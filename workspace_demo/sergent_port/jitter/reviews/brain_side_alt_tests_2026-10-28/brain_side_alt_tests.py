#!/usr/bin/env python3
"""The brain-side same-data comparison: the literature's own two-state tests on the matched comparison's synthetic EEG
sets (R052 job brief of 28 Oct 2026, Unimog prompts/2026-10-28_si_brain_side_alt_tests_job.txt). Every rule is declared
in RULES.md beside this file BEFORE the first run; the constants below restate them and are not changed after.

Stages (run in this order; the battery refuses to start until tie_check.json says PASS):
  python brain_side_alt_tests.py --tie      [--n-jobs 12]     member draws of every set; T1 regenerated and its inherited
                                                              per-window pipeline rerun against the saved lme; B4 and B5
                                                              restated from the saved rows -> tie_check.json, saved_restated.csv
  python brain_side_alt_tests.py --battery  [--n-jobs 12] [--limit N]   B1-B3 on every set (and the real 20, B6) -> sets.csv,
                                                              windows.csv, runtime.json
  python brain_side_alt_tests.py --summary                    per-setting counts with the one-sided bounds -> summary.csv,
                                                              table.md, totals.json
Data: s4.make_synthetic on the frozen validation seeds (DESIGN_jitter.md rev 7 §7.3, results/s4/run_config.json);
nothing is refitted; this script runs no model of the matched comparison.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
JIT = os.path.normpath(os.path.join(HERE, "..", ".."))            # sergent_port/jitter
PORT = os.path.dirname(JIT)                                        # sergent_port (fit_models.py, bms.py)
OUT = HERE
os.environ.setdefault("NPROC", "1")
os.environ["PYTHONPATH"] = f"{JIT}:{PORT}" + (":" + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")

# ---------------------------------------------------------------------------------------------- declared (RULES.md)
STAGE = "validation"
SETTINGS = {"W1": 100, "W2": 100, "W3": 100, "W4": 100, "O1": 100, "O2": 100, "O3": 100, "O4": 100, "O5": 100,
            "T1": 50, "T2": 50, "E1": 100}                        # T3 ABSENT (λ_T3 search failure, s4a.json)
UPPER_BOUND = ("W1", "W2", "W3", "W4", "O1", "O2", "O3", "O4", "O5")
LOWER_BOUND = ("T1", "T2", "E1")
INHERITED_RUN = ("W1", "W2", "W3", "W4", "O1", "O2", "O3", "O4", "O5", "T1")
TEST_LEVELS = (2, 3, 4)                   # mean A(k) of the 20 fitted B3 generators in [0.18, 0.82]: 0.313, 0.553, 0.774
ALL_LEVELS = (1, 2, 3, 4, 5)
ALPHA = 0.05
DIP_ALPHA_DECLARED = ALPHA / len(TEST_LEVELS)
DIP_ALPHA_ALL = ALPHA / len(ALL_LEVELS)
DBIC_STRONG = 10.0
GMM_N_INIT = 5
BURST_MARGIN = 0.10
RUN_LEN = 3
N_WINDOWS = 16
TIE_MAX_DISAGREE = 1                      # T1 sets whose regenerated inherited call may differ from the saved-lme call
EXPECTED_INHERITED = {"W1": 1, "W2": 0, "W3": 0, "W4": 0, "O1": 0, "O2": 0, "O3": 0, "O4": 0, "O5": 39, "T1": 7}
EXPECTED_PRIMARY = {"W1": (0, 0), "W2": (0, 0), "W3": (0, 0), "W4": (0, 4), "O1": (0, 0), "O2": (0, 0), "O3": (0, 0),
                    "O4": (0, 0), "O5": (12, 0), "T1": (49, 0), "T2": (0, 50), "E1": (99, 0)}   # (POSITIVE, UNAVAILABLE)
EXPECTED_E1_BOUNDED = 0

_MODS = {}


def mods():
    """The jitter modules, imported once per process (workers are fresh processes; the paths are set here)."""
    if _MODS:
        return _MODS
    for p in (PORT, JIT):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("NPROC", "1")
    import s4            # noqa
    import simulate as S  # noqa
    import data as D      # noqa
    import decide as X    # noqa
    _MODS.update(s4=s4, S=S, D=D, X=X, bases=s4.load_bases(), lam=lam_dict(s4))
    return _MODS


def lam_dict(s4) -> dict:
    a = s4.load_s4a()
    e1 = a["lambda"]["E1"]
    if e1.get("status") != "CERTIFIED":
        raise SystemExit(f"E1 λ is not CERTIFIED in s4a.json: {e1.get('status')}")
    return {"E1": float(e1["lam"])}


# ---------------------------------------------------------------------------------------------- data
def regenerate_set(setting: str, r: int) -> list:
    m_ = mods()
    s4, bases, lam = m_["s4"], m_["bases"], m_["lam"]
    members = s4.set_members(STAGE, setting, r)
    return [s4.make_synthetic(STAGE, setting, r, m, base, bases, lam) for m, base in enumerate(members)]


def real_participants() -> list:
    """B6: the 20 real participants' active session from the cached bases (W53 after the inherited preprocessing)."""
    m_ = mods()
    D, bases = m_["D"], m_["bases"]
    return [D.participant_from_windows(bases[s]["W53"], bases[s]["levels"], bases[s]["blocks"], s, "active", f"S{s}")
            for s in sorted(bases)]


def centred(p) -> tuple:
    """(Xc, Xs, k): the 16 primary-window distances centred on the participant's no-sound mean, the same divided by the
    no-sound SD, and the levels."""
    D = mods()["D"]
    Y = p.W53[:, D.PRIMARY_WINDOWS]
    catch = Y[p.levels == 0]
    mu0 = catch.mean(axis=0)
    sd0 = catch.std(axis=0, ddof=1)
    Xc = Y - mu0
    return Xc, Xc / sd0, p.levels


# ---------------------------------------------------------------------------------------------- tests
def gmm_seed(seed_set: int, w: int, k: int, variant: int) -> int:
    return int(np.random.default_rng([seed_set, w, k, variant]).integers(2**31))


def level_tests(x: np.ndarray, rs: int) -> dict:
    import diptest
    from sklearn.mixture import GaussianMixture
    dip, p = diptest.diptest(x)
    Xm = x.reshape(-1, 1)
    g1 = GaussianMixture(n_components=1, covariance_type="full", random_state=rs).fit(Xm)
    g2 = GaussianMixture(n_components=2, covariance_type="full", n_init=GMM_N_INIT, random_state=rs).fit(Xm)
    bic1, bic2 = float(g1.bic(Xm)), float(g2.bic(Xm))
    w = g2.weights_
    mu = g2.means_.ravel()
    o = np.argsort(mu)
    return dict(n=int(x.size), dip=float(dip), dip_p=float(p), bic1=bic1, bic2=bic2, dbic=bic1 - bic2,
                w_min=float(w.min()), mu_lo=float(mu[o[0]]), mu_hi=float(mu[o[1]]), gmm2_converged=int(g2.converged_))


def run_of(calls: np.ndarray, L: int = RUN_LEN) -> bool:
    c = np.asarray(calls, dtype=bool)
    return any(c[i:i + L].all() for i in range(c.size - L + 1))


def burst_calls(V: np.ndarray, margin: float) -> tuple:
    """V (16, 6). Burst at w: argmax over k strictly interior and V[w, k*] >= (1 + margin) max(V[w, 0], V[w, 5])."""
    kstar = V.argmax(axis=1)
    ends = np.maximum(V[:, 0], V[:, 5])
    interior = (kstar >= 1) & (kstar <= 4)
    call = interior & (V[np.arange(V.shape[0]), kstar] >= (1.0 + margin) * ends)
    return call, kstar


def set_tests(setting: str, r: int, parts: list, seed_set: int) -> tuple:
    """B1-B3 on one set of participants. Returns (set row, window rows)."""
    X = [centred(p) for p in parts]
    n_parts = len(parts)
    pooled = {}
    for var, idx in (("raw", 0), ("scaled", 1)):
        pooled[var] = {k: np.concatenate([xc[idx][xc[2] == k, :] for xc in X], axis=0) for k in range(6)}   # (n_k, 16)
    # variance profiles: within-participant variance per (w, k), mean over participants
    V = {}
    for var, idx in (("raw", 0), ("scaled", 1)):
        v = np.full((n_parts, N_WINDOWS, 6), np.nan)
        for i, xc in enumerate(X):
            for k in range(6):
                sel = xc[2] == k
                if sel.sum() >= 2:
                    v[i, :, k] = xc[idx][sel].var(axis=0, ddof=1)
        V[var] = np.nanmean(v, axis=0)
    win_rows = []
    stats = {var: {k: [] for k in ALL_LEVELS} for var in ("raw", "scaled")}
    for w in range(N_WINDOWS):
        for k in range(6):
            row = dict(setting=setting, r=r, window=w, level=k, n=int(pooled["raw"][k].shape[0]),
                       V_raw=float(V["raw"][w, k]), V_scaled=float(V["scaled"][w, k]))
            if k in ALL_LEVELS:
                for vi, var in enumerate(("raw", "scaled")):
                    t = level_tests(pooled[var][k][:, w], gmm_seed(seed_set, w, k, vi))
                    stats[var][k].append(t)
                    row.update({f"dip_{var}": t["dip"], f"dip_p_{var}": t["dip_p"], f"bic1_{var}": t["bic1"],
                                f"bic2_{var}": t["bic2"], f"dbic_{var}": t["dbic"], f"w_min_{var}": t["w_min"],
                                f"mu_lo_{var}": t["mu_lo"], f"mu_hi_{var}": t["mu_hi"],
                                f"gmm2_conv_{var}": t["gmm2_converged"]})
            win_rows.append(row)
    out = dict(setting=setting, r=r, seed_set=seed_set, n_participants=n_parts,
               n_trials=int(sum(p.n for p in parts)), data_ids=";".join(p.data_id for p in parts))
    for var in ("raw", "scaled"):
        sfx = "" if var == "raw" else "_s"
        P = np.array([[stats[var][k][w]["dip_p"] for k in ALL_LEVELS] for w in range(N_WINDOWS)])       # (16, 5)
        B = np.array([[stats[var][k][w]["dbic"] for k in ALL_LEVELS] for w in range(N_WINDOWS)])
        tl = [ALL_LEVELS.index(k) for k in TEST_LEVELS]
        dip_w = (P[:, tl] < DIP_ALPHA_DECLARED).any(axis=1)
        dip_all_w = (P < DIP_ALPHA_ALL).any(axis=1)
        bic10_w = B[:, tl].max(axis=1) > DBIC_STRONG
        bic0_w = B[:, tl].max(axis=1) > 0.0
        bic10_all_w = B.max(axis=1) > DBIC_STRONG
        bic0_all_w = B.max(axis=1) > 0.0
        burst_w, kstar = burst_calls(V[var], BURST_MARGIN)
        burst0_w, _ = burst_calls(V[var], 0.0)
        for name, c in (("dip", dip_w), ("dip_all", dip_all_w), ("bic10", bic10_w), ("bic0", bic0_w),
                        ("bic10_all", bic10_all_w), ("bic0_all", bic0_all_w), ("burst", burst_w), ("burst_m0", burst0_w)):
            out[f"{name}_run3{sfx}"] = int(run_of(c))
            out[f"{name}_any{sfx}"] = int(c.any())
            out[f"{name}_nwin{sfx}"] = int(c.sum())
        out[f"dip_min_p_declared{sfx}"] = float(P[:, tl].min())
        out[f"dip_min_p_all{sfx}"] = float(P.min())
        out[f"dbic_max_declared{sfx}"] = float(B[:, tl].max())
        out[f"dbic_max_all{sfx}"] = float(B.max())
        out[f"burst_kstar_mode{sfx}"] = int(np.bincount(kstar, minlength=6).argmax())
        out[f"burst_kstar_hist{sfx}"] = ";".join(str(int(c)) for c in np.bincount(kstar, minlength=6))
        out[f"V_level_mean{sfx}"] = ";".join(f"{v:.6g}" for v in V[var].mean(axis=0))      # profile averaged over windows
    return out, win_rows


def battery_task(setting: str, r: int) -> tuple:
    m_ = mods()
    S = m_["S"]
    t0 = time.time()
    if setting == "REAL":
        parts, seed_set = real_participants(), 0
    else:
        parts = regenerate_set(setting, r)
        seed_set = S.seed_for(STAGE, setting, r, 0, "set")
    t1 = time.time()
    out, win = set_tests(setting, r, parts, seed_set)
    out["seconds_regen"] = round(t1 - t0, 2)
    out["seconds_tests"] = round(time.time() - t1, 2)
    return out, win


# ---------------------------------------------------------------------------------------------- restatement of the saved record
def restate_task(setting: str, r: int) -> dict:
    """B4 (inherited per-window rule from the saved lme) and B5 (the saved verdict) of one set; no refit."""
    m_ = mods()
    s4, S, X = m_["s4"], m_["S"], m_["X"]
    s = s4.load_set(STAGE, setting, r)
    if s is None:
        return dict(setting=setting, r=r, missing=1)
    sc = s4.set_scores(s)
    prim = X.set_primary(sc)
    ros = X.roster(sc, ("G3", "B3"))
    d3 = {p: X.contrast(sc, p, "B3", "G3") for p in ros}
    iv = X.roster_interval(d3, ros)
    out = dict(setting=setting, r=r, missing=0, primary=prim, n_available=len(ros),
               delta3_mean=float(iv.mean) if np.isfinite(iv.mean) else float("nan"),
               delta3_lo=float(iv.lo) if np.isfinite(iv.lo) else float("nan"),
               delta3_hi=float(iv.hi) if np.isfinite(iv.hi) else float("nan"),
               bases=";".join(str(row["base"]) for row in s["rows"]),
               members_regen=";".join(str(b) for b in s4.set_members(STAGE, setting, r)),
               n_trials_saved=";".join(str(row["n_trials"]) for row in s["rows"]),
               data_ids_saved=";".join(row["data_id"] for row in s["rows"]))
    out["members_equal"] = int(out["bases"] == out["members_regen"])
    if setting == "E1":
        eps = s4.load_s4a()["epsilon"]
        out["bounded"] = int(np.isfinite(iv.hi) and iv.hi < eps) if iv.sign not in (X.UNAVAILABLE,) else -1
    if all("inherited_lme" in row for row in s["rows"]):
        summ = S.inherited_group_summary([np.asarray(row["inherited_lme"]) for row in s["rows"]])
        out.update(inherited_call=int(summ["call"]), inherited_first_run_ms=summ["first_run_start_ms"],
                   inherited_first_pxp095_ms=summ["first_window_pxp_above_095_ms"])
    else:
        out.update(inherited_call=-1, inherited_first_run_ms=None, inherited_first_pxp095_ms=None)
    return out


def tie_t1_task(r: int) -> dict:
    """Regenerate T1 set r on this machine, rerun the inherited per-window pipeline, compare with the saved lme and call."""
    m_ = mods()
    s4, S = m_["s4"], m_["S"]
    t0 = time.time()
    s = s4.load_set(STAGE, "T1", r)
    parts = regenerate_set("T1", r)
    lme_regen, diffs, idmatch, ntrials_eq = [], [], 0, 0
    for p, row in zip(parts, s["rows"]):
        lme = S.inherited_fits(p.W53, p.levels, p.blocks)
        lme_regen.append(lme)
        diffs.append(float(np.max(np.abs(lme - np.asarray(row["inherited_lme"])))))
        idmatch += int(p.data_id == row["data_id"])
        ntrials_eq += int(p.n == row["n_trials"])
    saved = S.inherited_group_summary([np.asarray(row["inherited_lme"]) for row in s["rows"]])
    regen = S.inherited_group_summary(lme_regen)
    return dict(r=r, n_trials_equal=ntrials_eq, data_id_matches=idmatch, lme_max_abs_diff=max(diffs),
                lme_max_abs_diff_per_row=diffs, call_saved=int(saved["call"]), call_regen=int(regen["call"]),
                first_run_saved_ms=saved["first_run_start_ms"], first_run_regen_ms=regen["first_run_start_ms"],
                pxp_m3_max_abs_diff=float(np.max(np.abs(saved["pxp"][:, 2] - regen["pxp"][:, 2]))),
                seconds=round(time.time() - t0, 1))


# ---------------------------------------------------------------------------------------------- bounds and summaries
def cp_upper(x: int, n: int, alpha: float = ALPHA) -> float:
    from scipy.stats import beta
    return 1.0 if x >= n else float(beta.ppf(1 - alpha, x + 1, n - x))


def cp_lower(x: int, n: int, alpha: float = ALPHA) -> float:
    from scipy.stats import beta
    return 0.0 if x <= 0 else float(beta.ppf(alpha, x, n - x + 1))


def runtime_versions() -> str:
    import platform
    import diptest
    import joblib
    import scipy
    import sklearn
    return (f"python {platform.python_version()} numpy {np.__version__} scipy {scipy.__version__} pandas {pd.__version__} "
            f"scikit-learn {sklearn.__version__} diptest {diptest.__version__} joblib {joblib.__version__} {platform.machine()}")


def run_tie(n_jobs: int):
    from joblib import Parallel, delayed
    mods()
    t0 = time.time()
    tasks = [(s, r) for s, R in SETTINGS.items() for r in range(R)]
    rest = Parallel(n_jobs=n_jobs, batch_size=4)(delayed(restate_task)(s, r) for s, r in tasks)
    t_rest = time.time() - t0
    df = pd.DataFrame(rest)
    df.to_csv(os.path.join(OUT, "saved_restated.csv"), index=False)
    checks = {}
    ok = True
    missing = int(df["missing"].sum())
    checks["missing_sets"] = missing
    ok &= missing == 0
    me = {s: int(df[df.setting == s]["members_equal"].sum()) for s in SETTINGS}
    checks["members_equal_per_setting"] = me
    ok &= all(me[s] == SETTINGS[s] for s in SETTINGS)
    inh = {s: int((df[df.setting == s]["inherited_call"] == 1).sum()) for s in INHERITED_RUN}
    checks["inherited_calls_restated"] = inh
    checks["inherited_calls_expected"] = EXPECTED_INHERITED
    ok &= inh == EXPECTED_INHERITED
    prim = {s: (int((df[df.setting == s]["primary"] == "POSITIVE").sum()), int((df[df.setting == s]["primary"] == "UNAVAILABLE").sum()))
            for s in SETTINGS}
    checks["primaries_restated_positive_unavailable"] = {s: list(v) for s, v in prim.items()}
    checks["primaries_expected"] = {s: list(v) for s, v in EXPECTED_PRIMARY.items()}
    ok &= prim == EXPECTED_PRIMARY
    e1b = int((df[df.setting == "E1"]["bounded"] == 1).sum())
    checks["E1_bounded_restated"] = e1b
    ok &= e1b == EXPECTED_E1_BOUNDED
    checks["restatement_pass"] = bool(ok)
    print(json.dumps(checks, indent=1), flush=True)
    # T1 regeneration and the inherited pipeline rerun
    t1 = time.time()
    tie = Parallel(n_jobs=n_jobs, batch_size=1)(delayed(tie_t1_task)(r) for r in range(SETTINGS["T1"]))
    t_t1 = time.time() - t1
    tie_df = pd.DataFrame([{k: v for k, v in t.items() if k != "lme_max_abs_diff_per_row"} for t in tie])
    tie_df.to_csv(os.path.join(OUT, "tie_T1_sets.csv"), index=False)
    disagree = [t["r"] for t in tie if t["call_saved"] != t["call_regen"]]
    t1c = dict(sets=len(tie), calls_saved=int(sum(t["call_saved"] for t in tie)), calls_regen=int(sum(t["call_regen"] for t in tie)),
               sets_called_saved=[t["r"] for t in tie if t["call_saved"]], sets_called_regen=[t["r"] for t in tie if t["call_regen"]],
               disagreeing_sets=disagree, n_trials_equal_rows=int(sum(t["n_trials_equal"] for t in tie)),
               data_id_matching_rows=int(sum(t["data_id_matches"] for t in tie)),
               lme_max_abs_diff_over_rows=max(t["lme_max_abs_diff"] for t in tie),
               lme_max_abs_diff_median_over_sets=float(np.median([t["lme_max_abs_diff"] for t in tie])),
               pxp_m3_max_abs_diff_over_sets=max(t["pxp_m3_max_abs_diff"] for t in tie),
               seconds_per_set_median=float(np.median([t["seconds"] for t in tie])))
    t1_ok = (t1c["calls_saved"] == EXPECTED_INHERITED["T1"] and t1c["n_trials_equal_rows"] == 20 * len(tie)
             and len(disagree) <= TIE_MAX_DISAGREE)
    t1c["pass"] = bool(t1_ok)
    print(json.dumps(t1c, indent=1), flush=True)
    rec = dict(pass_=bool(ok and t1_ok), restatement=checks, T1_regeneration=t1c, n_jobs=n_jobs,
               seconds_restatement=round(t_rest, 1), seconds_T1_regeneration=round(t_t1, 1),
               runtime=runtime_versions(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    rec["pass"] = rec.pop("pass_")
    with open(os.path.join(OUT, "tie_check.json"), "w") as fh:
        json.dump(rec, fh, indent=1, default=str)
    print("TIE", "PASS" if rec["pass"] else "FAIL", f"({t_rest + t_t1:.0f} s)", flush=True)


def tie_passed() -> bool:
    p = os.path.join(OUT, "tie_check.json")
    if not os.path.exists(p):
        return False
    with open(p) as fh:
        return bool(json.load(fh).get("pass"))


def run_battery(n_jobs: int, limit: int | None):
    from joblib import Parallel, delayed
    if not tie_passed():
        raise SystemExit("tie_check.json is missing or not PASS: run --tie first (RULES.md §5)")
    mods()
    tasks = [(s, r) for s, R in SETTINGS.items() for r in range(R if limit is None else min(R, limit))] + [("REAL", 0)]
    t0 = time.time()
    res = Parallel(n_jobs=n_jobs, batch_size=2)(delayed(battery_task)(s, r) for s, r in tasks)
    secs = time.time() - t0
    sets = pd.DataFrame([r[0] for r in res])
    wins = pd.DataFrame([x for r in res for x in r[1]])
    tag = f"_limit{limit}" if limit else ""
    sets.to_csv(os.path.join(OUT, f"sets{tag}.csv"), index=False, float_format="%.7g")
    wins.to_csv(os.path.join(OUT, f"windows{tag}.csv"), index=False, float_format="%.7g")
    meta = dict(n_sets=len(sets), n_jobs=n_jobs, seconds=round(secs, 1), seconds_per_set=round(secs / len(sets), 3),
                regen_seconds_median=float(sets["seconds_regen"].median()), tests_seconds_median=float(sets["seconds_tests"].median()),
                test_levels=TEST_LEVELS, dip_alpha_declared=DIP_ALPHA_DECLARED, dip_alpha_all=DIP_ALPHA_ALL,
                dbic_strong=DBIC_STRONG, gmm_n_init=GMM_N_INIT, burst_margin=BURST_MARGIN, run_len=RUN_LEN,
                runtime=runtime_versions(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    with open(os.path.join(OUT, f"runtime{tag}.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(f"battery: {len(sets)} sets in {secs / 60:.1f} min on {n_jobs} workers ({secs / len(sets):.2f} s per set)", flush=True)


READINGS = [  # (column in sets.csv, label)
    ("dip_run3", "dip, >=3 consecutive windows"), ("dip_any", "dip, any window"),
    ("bic10_run3", "BIC > 10, >=3 consecutive"), ("bic10_any", "BIC > 10, any window"),
    ("bic0_run3", "BIC > 0, >=3 consecutive"), ("bic0_any", "BIC > 0, any window"),
    ("burst_run3", "variance burst (margin 0.10), >=3 consecutive"), ("burst_any", "variance burst (margin 0.10), any window"),
    ("burst_m0_run3", "variance burst (margin 0), >=3 consecutive"), ("burst_m0_any", "variance burst (margin 0), any window"),
    ("dip_all_run3", "dip, all levels, >=3 consecutive"), ("bic10_all_run3", "BIC > 10, all levels, >=3 consecutive"),
    ("bic0_all_run3", "BIC > 0, all levels, >=3 consecutive"),
]


def run_summary():
    sets = pd.read_csv(os.path.join(OUT, "sets.csv"))
    rest = pd.read_csv(os.path.join(OUT, "saved_restated.csv"))
    rows = []
    for s, R in list(SETTINGS.items()) + [("REAL", 1)]:
        sub = sets[sets.setting == s]
        n = len(sub)
        cp = cp_upper if s in UPPER_BOUND else (cp_lower if s in LOWER_BOUND else None)
        r = dict(setting=s, n=n, bound_side=("upper" if s in UPPER_BOUND else "lower" if s in LOWER_BOUND else "none"))
        for col, _ in READINGS:
            for sfx in ("", "_s"):
                x = int(sub[col + sfx].sum())
                r[f"{col}{sfx}_calls"] = x
                r[f"{col}{sfx}_bound"] = cp(x, n) if cp else float("nan")
        if s != "REAL":
            rs = rest[rest.setting == s]
            r["inherited_calls"] = int((rs["inherited_call"] == 1).sum()) if s in INHERITED_RUN else -1
            r["inherited_bound"] = cp(r["inherited_calls"], n) if s in INHERITED_RUN else float("nan")
            r["matched_positive"] = int((rs["primary"] == "POSITIVE").sum())
            r["matched_negative"] = int((rs["primary"] == "NEGATIVE").sum())
            r["matched_unresolved"] = int((rs["primary"] == "UNRESOLVED").sum())
            r["matched_unavailable"] = int((rs["primary"] == "UNAVAILABLE").sum())
            r["matched_bound"] = cp(r["matched_positive"], n)
        rows.append(r)
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    # the table: setting x {dip, BIC > 10, BIC > 0, variance burst, per-window rule, matched comparison}, declared readings
    def cell(x, b):
        return f"{x} ({b:.3f})" if np.isfinite(b) else f"{x}"
    L = ["| Setting | sets | Dip test | Mixture BIC > 10 | Mixture BIC > 0 | Variance burst | Inherited per-window rule | Matched comparison (POSITIVE) |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in summ.iterrows():
        s = r["setting"]
        if s == "REAL":
            inh, mat = "—", "—"
        else:
            inh = cell(int(r["inherited_calls"]), r["inherited_bound"]) if r["inherited_calls"] >= 0 else "not run"
            mat = cell(int(r["matched_positive"]), r["matched_bound"]) + (f"; {int(r['matched_unavailable'])} UNAVAILABLE" if r["matched_unavailable"] else "")
        L.append(f"| {s} | {int(r['n'])} | {cell(int(r['dip_run3_calls']), r['dip_run3_bound'])} | {cell(int(r['bic10_run3_calls']), r['bic10_run3_bound'])} | "
                 f"{cell(int(r['bic0_run3_calls']), r['bic0_run3_bound'])} | {cell(int(r['burst_run3_calls']), r['burst_run3_bound'])} | {inh} | {mat} |")
    L += ["", "Any-window reading (beside the declared >=3-consecutive rule):", "",
          "| Setting | sets | Dip any | BIC > 10 any | BIC > 0 any | Burst (0.10) any | Burst (0) run3 | Burst (0) any |", "|---|---|---|---|---|---|---|---|"]
    for _, r in summ.iterrows():
        L.append(f"| {r['setting']} | {int(r['n'])} | {cell(int(r['dip_any_calls']), r['dip_any_bound'])} | {cell(int(r['bic10_any_calls']), r['bic10_any_bound'])} | "
                 f"{cell(int(r['bic0_any_calls']), r['bic0_any_bound'])} | {cell(int(r['burst_any_calls']), r['burst_any_bound'])} | "
                 f"{cell(int(r['burst_m0_run3_calls']), r['burst_m0_run3_bound'])} | {cell(int(r['burst_m0_any_calls']), r['burst_m0_any_bound'])} |")
    L += ["", "Sensitivity readings, >=3 consecutive windows: scaled by the no-sound SD (dip, BIC > 10, BIC > 0, burst 0.10) and all levels 1-5 (dip p < 0.05/5; BIC > 10; BIC > 0), unscaled:", "",
          "| Setting | sets | Dip scaled | BIC > 10 scaled | BIC > 0 scaled | Burst scaled | Dip all levels | BIC > 10 all levels | BIC > 0 all levels |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in summ.iterrows():
        L.append(f"| {r['setting']} | {int(r['n'])} | {cell(int(r['dip_run3_s_calls']), r['dip_run3_s_bound'])} | {cell(int(r['bic10_run3_s_calls']), r['bic10_run3_s_bound'])} | "
                 f"{cell(int(r['bic0_run3_s_calls']), r['bic0_run3_s_bound'])} | {cell(int(r['burst_run3_s_calls']), r['burst_run3_s_bound'])} | "
                 f"{cell(int(r['dip_all_run3_calls']), r['dip_all_run3_bound'])} | {cell(int(r['bic10_all_run3_calls']), r['bic10_all_run3_bound'])} | {cell(int(r['bic0_all_run3_calls']), r['bic0_all_run3_bound'])} |")
    with open(os.path.join(OUT, "table.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    # totals and descriptive profile facts
    tot = {}
    for s in list(SETTINGS) + ["REAL"]:
        sub = sets[sets.setting == s]
        tot[s] = dict(n=len(sub),
                      kstar_hist_raw=[int(v) for v in np.sum([[int(c) for c in h.split(";")] for h in sub["burst_kstar_hist"]], axis=0)],
                      V_level_mean_raw=[float(v) for v in np.mean([[float(c) for c in h.split(";")] for h in sub["V_level_mean"]], axis=0)],
                      V_level_mean_scaled=[float(v) for v in np.mean([[float(c) for c in h.split(";")] for h in sub["V_level_mean_s"]], axis=0)],
                      dip_min_p_declared_min=float(sub["dip_min_p_declared"].min()),
                      dbic_max_declared_median=float(sub["dbic_max_declared"].median()),
                      dbic_max_declared_max=float(sub["dbic_max_declared"].max()),
                      dip_nwin_median=float(sub["dip_nwin"].median()), bic10_nwin_median=float(sub["bic10_nwin"].median()),
                      burst_nwin_median=float(sub["burst_nwin"].median()))
    with open(os.path.join(OUT, "totals.json"), "w") as fh:
        json.dump(tot, fh, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tie", action="store_true")
    ap.add_argument("--battery", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--n-jobs", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None, help="sets per setting (smoke test; writes *_limitN files)")
    a = ap.parse_args()
    if a.tie:
        run_tie(a.n_jobs)
    elif a.battery:
        run_battery(a.n_jobs, a.limit)
    elif a.summary:
        run_summary()
    else:
        ap.error("--tie, --battery or --summary")

#!/usr/bin/env python3
"""The literature's own two-state tests, run on the paper's known-truth batteries (R052 job brief of 25 Oct 2026).

What this does. The article compares two procedures on the same known-truth data: the inherited two-model pair
(989 false mixture calls on the 12,000 graded datasets of run d4v12b) against the expanded families with selection
(0 false calls; 599 of 600 mixture datasets of run sens600 detected). This script extends that matrix with the tests
the literature uses for THIS indicator, each run as defined on exactly the same datasets:

  T1  Hartigan's dip test of unimodality (Hartigan & Hartigan 1985) on the per-trial readout pooled over concepts
      and carriers at each near-threshold dose level (the `diptest` package, interpolated p-value table).
  T2  A two-component against a one-component Gaussian mixture on the same per-level readouts, decided by BIC
      (sklearn GaussianMixture, covariance_type="full", n_init=5, seeded from the dataset seed).
  T3  The aggregate ignition index of Rahbar (arXiv 2608.05160 v1): the steepness beta of a four-parameter logistic
      fitted by nonlinear least squares (scipy curve_fit, Levenberg-Marquardt) to the MEAN readout against the dose
      level, with the paper's initialisation (midpoint = first level at or above the mid-range, steepness from the
      local slope scaled by the range) and the paper's cap at beta = 300. The paper's own axis is layer depth; this
      battery has one layer, so the form is applied along the dose axis. The paper defines NO verdict threshold
      ("high values indicate abrupt, ignition-like transitions, low values graded build-up"), so T3 reports the
      distribution of beta under each generator and makes no two-state call.
  T4  This paper's procedure: the saved verdict of every row (selection_decision; no refit).

Declared before running (and not changed after):
  TEST_LEVELS = (2, 3, 4): the near-threshold dose levels, those where the declared mixture base occupies the high
      state with probability A(k) = sigmoid(1.5 (k - 3)) between 0.18 and 0.82 (A = 0.047 at k = 1, 0.989 at k = 6).
  T1 call: a dataset is called two-state when any tested level has dip p < 0.05 / 3 (Bonferroni over the three levels).
      A sensitivity reading over all seven levels (p < 0.05 / 7) is written beside it.
  T2 call: a dataset is called two-state when the largest delta BIC = BIC(1) - BIC(2) over the three tested levels
      exceeds 10 (the "very strong" threshold of Kass & Raftery 1995); the delta BIC > 0 reading is written beside it.
      No multiplicity adjustment is defined for BIC; the any-level rule over the three declared levels is the rule.
  Rates: per setting, the two-state call count over datasets with the exact one-sided 95% Clopper-Pearson bound
      the article uses - the upper bound on graded settings, the lower bound on mixture settings.

Regeneration. Every dataset is regenerated deterministically with the HISTORICAL code of its run: the three code
files (models.py, analyze.py, simulate.py) are exported from the RSC commit whose config_hash, with the run's
settings (Config(n_starts_inner=4), D = 4, layer 41, seed 2026), equals the code_hash stored in every saved row -
52267ec -> b29215469af9 for d4v12b, a9f66bb -> 625798e9e7f4 for sens600. The script refuses to run if the hash does
not match. The regeneration was tied to the saved rows on ten rows first (tie_check.py beside this file): the outer
fits of M2B and M3 refitted on the regenerated data reproduce the saved per-concept held-out scores (see README).

The readout. ds.y[:, 0] - the per-trial response at the single layer, exactly the array analyze_dataset scored (it is
used untransformed; Trials.build only sorts and pads). The synthetic design has one readout per trial; the "lens
projection" second readout of the real-model pipeline has no synthetic counterpart here.

Usage (a venv with the run's pinned stack plus diptest and scikit-learn; see requirements_alt_tests.txt):
  NPROC=1 python alt_tests_battery.py --battery graded  --n-jobs 12
  NPROC=1 python alt_tests_battery.py --battery mixture --n-jobs 12
  python alt_tests_battery.py --summary          # combines both into summary_all.csv and table_alttests.tex
Writes under sim_results/alt_tests_2026-10-25/ (never under aws_ec2/runs/). The exported code goes under raw/ there,
which is .gitignored.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.normpath(os.path.join(HERE, "..", ".."))                     # workspace_demo/t1_access
RSC = os.path.normpath(os.path.join(T1, "..", ".."))                      # the repository root
OUT = os.path.join(T1, "sim_results", "alt_tests_2026-10-25")

BATTERIES = {
    "graded": dict(csv=os.path.join(T1, "sim_results", "d4v12b", "calibration_D4.csv"), commit="52267ec",
                   code_hash="b29215469af9", bound="upper", n_expected=12000),
    "mixture": dict(csv=os.path.join(T1, "sim_results", "sens600", "power_D4.csv"), commit="a9f66bb",
                    code_hash="625798e9e7f4", bound="lower", n_expected=600),
}
D, LAYERS, SEED = 4, (41,), 2026
LEVELS = (0, 1, 2, 3, 4, 6, 8)             # models.LEVELS of both code versions (checked at load)
TEST_LEVELS = (2, 3, 4)                     # declared
ALPHA = 0.05
DIP_ALPHA_DECLARED = ALPHA / len(TEST_LEVELS)
DIP_ALPHA_ALL = ALPHA / len(LEVELS)
DBIC_STRONG = 10.0
BETA_CAP = 300.0
GMM_N_INIT = 5


# ----------------------------------------------------------------------------------------------
# the historical code
# ----------------------------------------------------------------------------------------------
def export_code(commit: str) -> str:
    d = os.path.join(OUT, "raw", f"code_{commit}")
    os.makedirs(d, exist_ok=True)
    for f in ("models.py", "analyze.py", "simulate.py"):
        p = os.path.join(d, f)
        if not os.path.exists(p):
            blob = subprocess.run(["git", "-C", RSC, "show", f"{commit}:workspace_demo/t1_access/{f}"],
                                  capture_output=True, check=True).stdout
            with open(p, "wb") as fh:
                fh.write(blob)
    return d


_MODS = {}


def load(code_dir: str):
    """Import the historical analyze / models / simulate from code_dir (once per process)."""
    if code_dir in _MODS:
        return _MODS[code_dir]
    os.environ.setdefault("NPROC", "1")
    if sys.path[0] != code_dir:
        sys.path.insert(0, code_dir)
    for name in ("analyze", "models", "simulate"):
        sys.modules.pop(name, None)
    import analyze as A      # noqa
    import models as M       # noqa
    import simulate as S     # noqa
    if tuple(M.LEVELS) != LEVELS:
        raise SystemExit(f"models.LEVELS at {code_dir} is {M.LEVELS}, this script declared {LEVELS}")
    _MODS[code_dir] = (A, M, S)
    return A, M, S


def verify_hash(code_dir: str, want: str) -> str:
    A, M, S = load(code_dir)
    cfg = A.Config(n_starts_inner=4)
    got = S.config_hash(cfg, D, LAYERS, SEED)
    if got != want:
        raise SystemExit(f"{code_dir}: config_hash {got} != the saved rows' {want}; refusing to regenerate")
    return got


def ds_seed_for(S, M, name, kwargs, rep):
    if hasattr(S, "dataset_seed"):
        return int(S.dataset_seed(name, kwargs, rep, D, SEED))
    # 52267ec: the weighted tag inline in one_replicate (identical to dataset_seed for grids of at most one value)
    grid_tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in
                   enumerate(kwargs.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    return int(np.random.default_rng([SEED, M.ALL_MEMBERS.index(name), grid_tag % (2**31 - 1), rep, D]).integers(2**31))


# ----------------------------------------------------------------------------------------------
# the three tests
# ----------------------------------------------------------------------------------------------
def rahbar_index(levels, means):
    """Rahbar (2608.05160 v1) eq. 3 four-parameter logistic f(x) = ymin + (ymax - ymin) / (1 + exp(-beta (x - x0))),
    fitted by scipy curve_fit (Levenberg-Marquardt); Definition 1: the index is the fitted beta. Initial values after
    the paper's s6.4: x0 at the first level at or above the midpoint of max and min; beta from the local slope across
    that level scaled by the range (the logistic's slope at its midpoint is beta (ymax - ymin) / 4). Cap: beta = 300
    (the paper's C1), also applied when the fit does not converge (a step-like curve)."""
    from scipy.optimize import curve_fit
    x = np.asarray(levels, float)
    y = np.asarray(means, float)
    ymin0, ymax0 = float(y.min()), float(y.max())
    rng_ = ymax0 - ymin0
    mid = 0.5 * (ymin0 + ymax0)
    i0 = int(np.argmax(y >= mid))
    lo, hi = max(i0 - 1, 0), min(i0 + 1, x.size - 1)
    slope = (y[hi] - y[lo]) / (x[hi] - x[lo])
    beta0 = max(4.0 * slope / rng_, 1e-3) if rng_ > 0 else 1.0

    def f(x, ymin, ymax, x0, beta):
        return ymin + (ymax - ymin) / (1.0 + np.exp(-beta * (x - x0)))

    ok = True
    try:
        with np.errstate(over="ignore", invalid="ignore"):
            popt, _ = curve_fit(f, x, y, p0=[ymin0, ymax0, x[i0], beta0], method="lm", maxfev=20000)
        ymin_h, ymax_h, x0_h, beta_raw = (float(v) for v in popt)
        if not np.isfinite(beta_raw):
            ok = False
    except (RuntimeError, ValueError):
        ok = False
        ymin_h, ymax_h, x0_h, beta_raw = ymin0, ymax0, float(x[i0]), float("inf")
    beta_abs = abs(beta_raw) if np.isfinite(beta_raw) else float("inf")
    capped = (not ok) or beta_abs > BETA_CAP
    return dict(beta_hat=min(beta_abs, BETA_CAP), beta_raw=beta_raw, beta_capped=int(capped), fit_ok=int(ok),
                x0_hat=x0_h, ymin_hat=ymin_h, ymax_hat=ymax_h, beta0=beta0, x0_init=float(x[i0]))


def level_tests(x: np.ndarray, rs: int) -> dict:
    import diptest
    from sklearn.mixture import GaussianMixture
    dip, p = diptest.diptest(x)
    X = x.reshape(-1, 1)
    g1 = GaussianMixture(n_components=1, covariance_type="full", random_state=rs).fit(X)
    g2 = GaussianMixture(n_components=2, covariance_type="full", n_init=GMM_N_INIT, random_state=rs).fit(X)
    bic1, bic2 = float(g1.bic(X)), float(g2.bic(X))
    w = g2.weights_
    mu = g2.means_.ravel()
    sd = np.sqrt(g2.covariances_.ravel())
    o = np.argsort(mu)
    return dict(n=int(x.size), mean=float(x.mean()), sd=float(x.std(ddof=1)), dip=float(dip), dip_p=float(p),
                bic1=bic1, bic2=bic2, dbic=bic1 - bic2, w_min=float(w.min()),
                mu_lo=float(mu[o[0]]), mu_hi=float(mu[o[1]]), sd_lo=float(sd[o[0]]), sd_hi=float(sd[o[1]]),
                gmm2_converged=int(g2.converged_))


def one_dataset(row: dict, code_dir: str) -> tuple:
    A, M, S = load(code_dir)
    name, kwargs, rep = row["generator"], json.loads(row["grid"]), int(row["rep"])
    theta = S.generator_theta(name, **kwargs)
    ds_seed = ds_seed_for(S, M, name, kwargs, rep)
    ds = S.make_dataset(name, theta, n_per_family=8, D=D, layers=LAYERS, rho=S.RHO_LAYERS, seed=ds_seed)
    y, k = ds.y[:, 0], ds.k
    key = dict(generator=name, grid=row["grid"], rep=rep, ds_seed=ds_seed)
    levels_out, means = [], []
    for li, lev in enumerate(LEVELS):
        x = y[k == lev]
        r = level_tests(x, rs=int(np.random.default_rng([ds_seed, li]).integers(2**31)))
        r.update(key, level=lev)
        levels_out.append(r)
        means.append(r["mean"])
    by = {r["level"]: r for r in levels_out}
    tested = [by[l] for l in TEST_LEVELS]
    out = dict(key, saved_decision=row["selection_decision"], saved_code_hash=row["code_hash"],
               dip_min_p_declared=min(r["dip_p"] for r in tested),
               dip_call_declared=int(any(r["dip_p"] < DIP_ALPHA_DECLARED for r in tested)),
               dip_min_p_all=min(r["dip_p"] for r in levels_out),
               dip_call_all=int(any(r["dip_p"] < DIP_ALPHA_ALL for r in levels_out)),
               gmm_max_dbic_declared=max(r["dbic"] for r in tested),
               gmm_call_strong=int(max(r["dbic"] for r in tested) > DBIC_STRONG),
               gmm_call_positive=int(max(r["dbic"] for r in tested) > 0.0),
               gmm_max_dbic_all=max(r["dbic"] for r in levels_out),
               gmm_call_strong_all=int(max(r["dbic"] for r in levels_out) > DBIC_STRONG),
               n_trials=int(y.size))
    out.update(rahbar_index(LEVELS, means))
    return out, levels_out


# ----------------------------------------------------------------------------------------------
# summaries
# ----------------------------------------------------------------------------------------------
def cp_upper(x: int, n: int, alpha: float = ALPHA) -> float:
    from scipy.stats import beta
    return 1.0 if x >= n else float(beta.ppf(1 - alpha, x + 1, n - x))


def cp_lower(x: int, n: int, alpha: float = ALPHA) -> float:
    from scipy.stats import beta
    return 0.0 if x <= 0 else float(beta.ppf(alpha, x, n - x + 1))


def setting_label(generator: str, grid: str, target_gain=None, latex: bool = False) -> str:
    kw = json.loads(grid)
    if generator == "M2B":
        return "Base (M2B)"
    if generator == "M2H":
        return (r"Threshold effect, $\tau = %g$" if latex else "Threshold effect, tau = %g") % kw["tau"]
    if generator == "M2K":
        return (r"Skew, $\alpha = %g$" if latex else "Skew, alpha = %g") % kw["alpha"]
    if generator == "M2S":
        return (r"Concept scale, $\omega = %g$" if latex else "Concept scale, omega = %g") % kw["omega"]
    return f"{generator}, gain {target_gain:g}"


def summarize(battery: str, ds: pd.DataFrame, bound: str) -> pd.DataFrame:
    rows = []
    cp = cp_upper if bound == "upper" else cp_lower
    for (g, grid), sub in ds.groupby(["generator", "grid"], sort=False):
        n = len(sub)
        tg = float(sub["target_gain"].iloc[0]) if "target_gain" in sub and sub["target_gain"].notna().any() else None
        r = dict(battery=battery, generator=g, grid=grid, target_gain=tg, setting=setting_label(g, grid, tg), n=n)
        for col, short in (("dip_call_declared", "dip"), ("dip_call_all", "dip_all7"), ("gmm_call_strong", "bic10"),
                           ("gmm_call_positive", "bic0"), ("gmm_call_strong_all", "bic10_all7")):
            x = int(sub[col].sum())
            r[f"{short}_calls"] = x
            r[f"{short}_rate"] = x / n
            r[f"{short}_bound"] = cp(x, n)
        saved_mix = int((sub["saved_decision"] == "mixture").sum())
        r["saved_mixture_calls"] = saved_mix
        r["saved_mixture_rate"] = saved_mix / n
        r["saved_mixture_bound"] = cp(saved_mix, n)
        r["saved_graded_calls"] = int((sub["saved_decision"] == "graded").sum())
        r["saved_inconclusive_calls"] = int((sub["saved_decision"] == "inconclusive").sum())
        b = sub["beta_hat"]
        r["beta_median"] = float(b.median())
        r["beta_q25"] = float(b.quantile(0.25))
        r["beta_q75"] = float(b.quantile(0.75))
        r["beta_min"] = float(b.min())
        r["beta_max"] = float(b.max())
        r["beta_capped_share"] = float(sub["beta_capped"].mean())
        r["beta_fit_failures"] = int((sub["fit_ok"] == 0).sum())
        r["bound_side"] = bound
        rows.append(r)
    return pd.DataFrame(rows)


def write_table(summary: pd.DataFrame, path: str):
    """The LaTeX rows of tab:alttests (methods x settings; the number of datasets called two-state with the one-sided
    bound; the datasets per setting are constant within a block and stated in its heading)."""
    def cell(calls, n, bound):
        return f"{calls} ({bound:.3f})"
    lines = []
    for battery, head in (("graded", r"\multicolumn{6}{l}{\textit{Graded generators, run d4v12b, 1{,}000 datasets per setting, upper bounds}} \\"),
                          ("mixture", r"\multicolumn{6}{l}{\textit{Mixture generators, run sens600, 50 datasets per setting, lower bounds}} \\")):
        sub = summary[summary["battery"] == battery]
        lines.append(head)
        for _, r in sub.iterrows():
            lab = setting_label(r["generator"], r["grid"], r["target_gain"], latex=True)
            n = int(r["n"])
            beta = f"{r['beta_median']:.2f} ({r['beta_q25']:.2f}--{r['beta_q75']:.2f})"
            lines.append(f"{lab} & {cell(int(r['dip_calls']), n, r['dip_bound'])} & {cell(int(r['bic10_calls']), n, r['bic10_bound'])} & "
                         f"{cell(int(r['bic0_calls']), n, r['bic0_bound'])} & {beta} & {cell(int(r['saved_mixture_calls']), n, r['saved_mixture_bound'])} \\\\")
        if battery == "graded":
            lines.append(r"\midrule")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def runtime_versions() -> str:
    import platform
    import scipy, sklearn, diptest, joblib
    return (f"python {platform.python_version()} numpy {np.__version__} scipy {scipy.__version__} pandas {pd.__version__} "
            f"scikit-learn {sklearn.__version__} diptest {diptest.__version__} joblib {joblib.__version__} {platform.machine()}")


# ----------------------------------------------------------------------------------------------
def run_battery(battery: str, n_jobs: int, limit: int | None):
    from joblib import Parallel, delayed
    spec = BATTERIES[battery]
    os.makedirs(OUT, exist_ok=True)
    gi = os.path.join(OUT, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as fh:
            fh.write("raw/\n")
    code_dir = export_code(spec["commit"])
    got = verify_hash(code_dir, spec["code_hash"])
    print(f"{battery}: historical code {spec['commit']} -> config_hash {got} == saved {spec['code_hash']}", flush=True)
    usecols = ["generator", "grid", "rep", "code_hash", "selection_decision"] + (["target_gain"] if battery == "mixture" else [])
    df = pd.read_csv(spec["csv"], usecols=usecols)
    if len(df) != spec["n_expected"]:
        raise SystemExit(f"{spec['csv']}: {len(df)} rows, expected {spec['n_expected']}")
    if set(df["code_hash"]) != {spec["code_hash"]}:
        raise SystemExit(f"{spec['csv']}: code_hash values {set(df['code_hash'])}")
    if limit:
        df = df.groupby(["generator", "grid"], sort=False).head(limit)
    rows = df.to_dict("records")
    t0 = time.time()
    res = Parallel(n_jobs=n_jobs, batch_size=8)(delayed(one_dataset)(r, code_dir) for r in rows)
    secs = time.time() - t0
    ds = pd.DataFrame([r[0] for r in res])
    if battery == "mixture":
        tg = {(r["generator"], r["grid"], int(r["rep"])): float(r["target_gain"]) for r in rows}
        ds["target_gain"] = [tg[(g, gr, int(rp))] for g, gr, rp in zip(ds["generator"], ds["grid"], ds["rep"])]
    lv = pd.DataFrame([x for r in res for x in r[1]])
    tag = f"_limit{limit}" if limit else ""
    ds.to_csv(os.path.join(OUT, f"datasets_{battery}{tag}.csv"), index=False, float_format="%.7g")
    lv.to_csv(os.path.join(OUT, f"levels_{battery}{tag}.csv"), index=False, float_format="%.7g")
    summ = summarize(battery, ds, spec["bound"])
    summ.to_csv(os.path.join(OUT, f"summary_{battery}{tag}.csv"), index=False)
    meta = dict(battery=battery, csv=os.path.relpath(spec["csv"], RSC), n_datasets=len(ds), commit=spec["commit"],
                code_hash=got, n_jobs=n_jobs, seconds=round(secs, 1), per_dataset_seconds=round(secs / len(ds), 3),
                levels=LEVELS, test_levels=TEST_LEVELS, dip_alpha_declared=DIP_ALPHA_DECLARED, dip_alpha_all=DIP_ALPHA_ALL,
                dbic_strong=DBIC_STRONG, beta_cap=BETA_CAP, gmm_n_init=GMM_N_INIT, runtime=runtime_versions(),
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    with open(os.path.join(OUT, f"runtime_{battery}{tag}.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    pd.set_option("display.width", 250)
    print(summ[["setting", "n", "dip_calls", "dip_bound", "bic10_calls", "bic10_bound", "bic0_calls", "bic0_bound",
                "beta_median", "beta_q25", "beta_q75", "beta_capped_share", "saved_mixture_calls"]].to_string(index=False))
    print(f"{battery}: {len(ds)} datasets in {secs / 60:.1f} min on {n_jobs} workers ({secs / len(ds):.3f} s per dataset)")


def write_summary():
    parts = [pd.read_csv(os.path.join(OUT, f"summary_{b}.csv")) for b in ("graded", "mixture")]
    summary = pd.concat(parts, ignore_index=True)
    summary.to_csv(os.path.join(OUT, "summary_all.csv"), index=False)
    write_table(summary, os.path.join(OUT, "table_alttests.tex"))
    print(summary[["battery", "setting", "n", "dip_calls", "dip_bound", "bic10_calls", "bic10_bound", "bic0_calls", "bic0_bound",
                   "beta_median", "beta_q25", "beta_q75", "saved_mixture_calls", "saved_mixture_bound"]].to_string(index=False))
    # the totals the article's paragraph quotes (every quoted number traces to this print and to totals.json)
    totals = {}
    for battery, sub in summary.groupby("battery"):
        n = int(sub["n"].sum())
        t = dict(n_datasets=n)
        for short in ("dip", "dip_all7", "bic10", "bic0", "bic10_all7", "saved_mixture"):
            t[f"{short}_calls"] = int(sub[f"{short}_calls"].sum())
        t["bic10_settings_with_calls"] = [s for s, c in zip(sub["setting"], sub["bic10_calls"]) if c > 0]
        t["dip_settings_with_calls"] = [s for s, c in zip(sub["setting"], sub["dip_calls"]) if c > 0]
        t["beta_median_min"] = float(sub["beta_median"].min())
        t["beta_median_max"] = float(sub["beta_median"].max())
        t["beta_capped_total_share"] = float((sub["beta_capped_share"] * sub["n"]).sum() / n)
        totals[battery] = t
    with open(os.path.join(OUT, "totals.json"), "w") as fh:
        json.dump(totals, fh, indent=1)
    print(json.dumps(totals, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--battery", choices=list(BATTERIES))
    ap.add_argument("--n-jobs", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None, help="datasets per setting (smoke test)")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        write_summary()
    elif a.battery:
        run_battery(a.battery, a.n_jobs, a.limit)
    else:
        ap.error("--battery or --summary")

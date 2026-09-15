#!/usr/bin/env python3
"""Phase 1 analysis — DEVPLAN_v7.md rev 1 §2.4, on the archived outputs of devpanel_v7.py (read-only; no fit, no generated
recording, no EEG). Mechanism, not frequency: the panel is enriched for extreme graded losses (§2.1) and says nothing about
how often a mechanism occurs, typical fold behaviour or a group decision.

Unit: one recording x fold x window x model (panel: 40 recordings x 4 folds x 20 windows; idealized: 272 recordings x 4
folds x the pseudo-window). Declared definitions (development diagnostics, fixed here before the tables are read):
  loss_vs_null   (held-out log-likelihood of the model - that of null) / n_test on the fold, nat per trial;
  severe         loss_vs_null < -1 (the unit of the v6 stage C catastrophe diagnosis, at fold level);
  at bound       the kept start's normalized position (x - lo) / (hi - lo) <= 1e-9 or >= 1 - 1e-9 for a parameter
                 (L-BFGS-B projects onto the box, so an active bound is exact); near bound: within 1e-3;
  extrapolated   a test present trial whose scaled dose lies below or above the training block's present-dose range;
  loss share     of a unit's summed per-trial loss against null, the part on extrapolated trials, within-support present
                 trials and catch trials;
  near-tie start a converged start other than the kept one, within likelihood.BASIN_NAT (0.5 nat) of the best training
                 log-likelihood, whose normalized parameters differ from the kept start's by more than 1e-4 somewhere;
                 material when its held-out log-likelihood differs from the kept solution's by more than 0.1 nat per trial
                 (also reported at 1 nat) — held-out values describe the procedure here and choose nothing;
  graded SD      the effective conditional SD exp(s0 + r L) in units of the training S: its minimum over all doses
                 exp(s0 + min(0, r)), and its realized minimum on training, within-support and extrapolated test trials;
                 floor violation below 0.05 S, the floor the null and two-state SDs already have (Q4);
  shifts         graded a1 at 10 S or 0; two-state delta0 / delta1 at their bounds (e^d0 + e^d1 in [0.02 S, 20 S]) (Q5).
Integrity: each panel recording's per-window evidence is rebuilt from the logged folds (sum of held-out / 4) and must equal
the stored v6 evidence exactly.

Outputs in results/devpanel_v7/run-5d74bc1d6a11/analysis/: units_panel.csv, units_ideal.csv, recordings_ideal.csv,
summary.json. Usage: ../../.venv/bin/python devpanel_analyze.py
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import collections  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402

import numpy as np  # noqa: E402

import battery as BT  # noqa: E402
import decoder as DEC  # noqa: E402
import likelihood as LK  # noqa: E402
import devpanel_v7 as DP  # noqa: E402

RUN = os.path.join(DP.BASE, "run-5d74bc1d6a11")
OUT = os.path.join(RUN, "analysis")
SEVERE = -1.0
BOUND_TOL = 1e-9
NEAR_BOUND = 1e-3
DISTINCT = 1e-4
MATERIAL = (0.1, 1.0)
FLOOR = 0.05
MODELS = LK.PRIMARY


def _design(a: dict) -> dict:
    return dict(y=a["y"], x=a["x"], c=a["catch"], h=a["h"])


def _finite_min(v):
    v = np.asarray(v, float)
    return float(v.min()) if v.size else float("nan")


def units(output: dict, meta: dict) -> list:
    fits = {(tuple(f["tags"]), f["model"]): f for f in output["fits"]}
    rows = []
    for key, fr in sorted(output["folds"].items()):
        _, _, hi, fi, w = key
        base = dict(meta, half=hi, fold=fi, window=w, main=bool(w in DEC.MAIN), n_train=fr["n_train"], n_test=fr["n_test"])
        if fr["scaling"] is None:
            rows += [dict(base, model=m, available=False, reason=fr["unavailable_reason"]) for m in MODELS]
            continue
        S = fr["scaling"]["S"]
        ds = fr["dose_support"]
        lab = ds["test_label"]
        extrap = (lab == "below") | (lab == "above")
        within = lab == "within"
        catch = lab == "catch"
        dte = _design(fr["test"])
        null = fr["models"]["null"]
        for m in MODELS:
            mr = fr["models"][m]
            f = fits.get((key, m))
            row = dict(base, model=m, available=mr["available"], reason=mr["reason"], S=S, n_below=ds["n_below"],
                       n_above=ds["n_above"], any_extrap=bool(extrap.any()))
            if "theta" in mr and "theta" in null:
                dll = mr["test_ll"] - null["test_ll"]
                row.update(loss_vs_null=float(dll.sum() / fr["n_test"]), severe=bool(dll.sum() / fr["n_test"] < SEVERE),
                           dll_extrap=float(dll[extrap].sum()), dll_within=float(dll[within].sum()), dll_catch=float(dll[catch].sum()),
                           worst_trial=float(dll.min()), worst_trial_label=str(lab[int(np.argmin(dll))]))
            if f is not None and f["available"]:
                ks = f["starts"][f["kept_start"]]
                names = LK.PARAMS[m]
                nz = ks["normalized"]
                row.update(at_bound=";".join(n for j, n in enumerate(names) if nz[j] <= BOUND_TOL or nz[j] >= 1 - BOUND_TOL),
                           near_bound=";".join(n for j, n in enumerate(names) if nz[j] <= NEAR_BOUND or nz[j] >= 1 - NEAR_BOUND),
                           n_starts=f["n_starts"], n_converged=f["n_converged"], retry=f["retry"], n_at_best=f["n_at_best"])
                row["n_at_bound"] = len([x for x in row["at_bound"].split(";") if x])
                if "theta" in mr:
                    held = float(mr["test_ll"].sum())
                    ties = [s for s in f["starts"] if s["converged"] and s["order"] != ks["order"]
                            and s["loglik"] >= ks["loglik"] - LK.BASIN_NAT and np.max(np.abs(s["normalized"] - nz)) > DISTINCT]
                    hd, md = [], []
                    for s in ties:
                        ll = LK.loglik(m, s["theta"], dte)
                        hd.append(abs(float(ll.sum()) - held) / fr["n_test"] if np.all(np.isfinite(ll)) else float("inf"))
                        md.append(float(np.max(np.abs(DP.predict(m, s["theta"], dte)["mean"] - mr["test"]["mean"]))) / S)
                    row.update(n_near_tie=len(ties), near_tie_max_heldout_diff=max(hd) if hd else 0.0,
                               near_tie_max_mean_diff_S=max(md) if md else 0.0,
                               near_tie_train_gap_max=max((ks["loglik"] - s["loglik"] for s in ties), default=0.0))
            if m == "graded" and "theta" in mr:
                th = mr["theta"]
                s0, r = th[4], th[5]
                sd = mr["test"]["sd"] / S
                row.update(a1_S=th[1] / S, r=r, x0=th[2], k=math.exp(th[3]), eff_sd_min_S=math.exp(s0 + min(0.0, r)) / S,
                           eff_sd_max_S=math.exp(s0 + max(0.0, r)) / S, train_sd_min_S=_finite_min(mr["train"]["sd"] / S),
                           within_sd_min_S=_finite_min(sd[within]), extrap_sd_min_S=_finite_min(sd[extrap]),
                           catch_sd_S=_finite_min(sd[catch]))
                row.update(floor_violation=bool(row["eff_sd_min_S"] < FLOOR),
                           test_floor_violation=bool(min(_finite_min(sd), np.inf) < FLOOR))
                if f is not None and f["available"]:
                    nz = f["starts"][f["kept_start"]]["normalized"]
                    row.update(a1_at_upper=bool(nz[1] >= 1 - BOUND_TOL), a1_at_zero=bool(nz[1] <= BOUND_TOL),
                               r_at_lower=bool(nz[5] <= BOUND_TOL), r_at_upper=bool(nz[5] >= 1 - BOUND_TOL))
            if m == "twostate" and "theta" in mr:
                th = mr["theta"]
                row.update(shift_sum_S=(math.exp(th[2]) + math.exp(th[3])) / S, sigma_S=math.exp(th[1]) / S)
                if f is not None and f["available"]:
                    nz = f["starts"][f["kept_start"]]["normalized"]
                    row.update(d0_at_bound=bool(nz[2] <= BOUND_TOL or nz[2] >= 1 - BOUND_TOL),
                               d1_at_bound=bool(nz[3] <= BOUND_TOL or nz[3] >= 1 - BOUND_TOL))
            rows.append(row)
    return rows


def check_evidence(output: dict) -> None:
    """Rebuild the per-window evidence from the logged folds; it must equal the stored (v6-equal) summary exactly."""
    summ = output["summary"]
    windows, models = summ["windows"], summ["models"]
    held = np.zeros((len(windows), len(models)))
    avail = np.ones_like(held, dtype=bool)
    for (_, _, hi, fi, w), fr in sorted(output["folds"].items(), key=lambda kv: (kv[0][2], kv[0][3])):
        wi = windows.index(w)
        for mi, m in enumerate(models):
            if fr["models"][m]["available"]:
                held[wi, mi] += fr["models"][m]["heldout"]
            else:
                avail[wi, mi] = False
    rebuilt = np.where(avail, held / 4.0, np.nan)
    if not np.array_equal(rebuilt, np.asarray(summ["evidence"], float), equal_nan=True):
        raise SystemExit(f"{output['key']}: evidence rebuilt from the logged folds differs from the stored summary")


def rate(num, den):
    return dict(k=int(num), n=int(den), p=(float(num) / den if den else None))


def family_tables(rows: list) -> dict:
    out = {}
    for fam in ("graded", "twostate"):
        U = [u for u in rows if u["model"] == fam and "loss_vs_null" in u]
        sev = [u for u in U if u["severe"]]
        ok = [u for u in U if not u["severe"]]
        t = dict(units=len(U), unavailable=sum(1 for u in rows if u["model"] == fam and not u["available"]), severe=len(sev),
                 at_bound_given_severe=rate(sum(u.get("n_at_bound", 0) > 0 for u in sev), len(sev)),
                 at_bound_given_not=rate(sum(u.get("n_at_bound", 0) > 0 for u in ok), len(ok)),
                 extrap_given_severe=rate(sum(u["any_extrap"] for u in sev), len(sev)),
                 extrap_given_not=rate(sum(u["any_extrap"] for u in ok), len(ok)),
                 worst_trial_extrapolated_given_severe=rate(sum(u["worst_trial_label"] in ("below", "above") for u in sev), len(sev)),
                 bound_params_in_severe=dict(collections.Counter(p for u in sev for p in u.get("at_bound", "").split(";") if p)),
                 bound_params_in_not=dict(collections.Counter(p for u in ok for p in u.get("at_bound", "").split(";") if p)))
        tot = sum(u["dll_extrap"] + u["dll_within"] + u["dll_catch"] for u in sev)
        if sev and np.isfinite(tot) and tot != 0:
            t["severe_loss_share"] = dict(extrapolated=sum(u["dll_extrap"] for u in sev) / tot,
                                          within=sum(u["dll_within"] for u in sev) / tot, catch=sum(u["dll_catch"] for u in sev) / tot)
        T = [u for u in U if "n_near_tie" in u]
        t["near_ties"] = dict(fits=len(T), with_distinct_near_tie=sum(u["n_near_tie"] > 0 for u in T),
                              **{f"material_{m}nat": sum(u["near_tie_max_heldout_diff"] > m for u in T) for m in MATERIAL},
                              **{f"material_{m}nat_in_severe": sum(u["near_tie_max_heldout_diff"] > m for u in T if u["severe"]) for m in MATERIAL})
        if fam == "graded":
            G = [u for u in U if "eff_sd_min_S" in u]
            t["q3_sd"] = dict(
                severe_with_extrap=len([u for u in sev if u["any_extrap"]]),
                median_extrap_over_within_min_sd_severe=_median([u["extrap_sd_min_S"] / u["within_sd_min_S"] for u in sev
                                                                 if u["any_extrap"] and u["within_sd_min_S"] > 0]),
                median_extrap_over_within_min_sd_not=_median([u["extrap_sd_min_S"] / u["within_sd_min_S"] for u in ok
                                                              if u["any_extrap"] and u["within_sd_min_S"] > 0]),
                median_extrap_sd_min_S_severe=_median([u["extrap_sd_min_S"] for u in sev if u["any_extrap"]]),
                median_within_sd_min_S_severe=_median([u["within_sd_min_S"] for u in sev]))
            t["q4_floor"] = dict(floor_violation_given_severe=rate(sum(u["floor_violation"] for u in G if u["severe"]), len([u for u in G if u["severe"]])),
                                 floor_violation_given_not=rate(sum(u["floor_violation"] for u in G if not u["severe"]), len([u for u in G if not u["severe"]])),
                                 test_floor_violation_given_severe=rate(sum(u["test_floor_violation"] for u in G if u["severe"]), len([u for u in G if u["severe"]])),
                                 test_floor_violation_given_not=rate(sum(u["test_floor_violation"] for u in G if not u["severe"]), len([u for u in G if not u["severe"]])),
                                 eff_sd_min_S_quantiles=_quantiles([u["eff_sd_min_S"] for u in G]))
            B = [u for u in G if "a1_at_upper" in u]
            t["q5_shifts"] = dict(a1_at_upper_given_severe=rate(sum(u["a1_at_upper"] for u in B if u["severe"]), len([u for u in B if u["severe"]])),
                                  a1_at_upper_given_not=rate(sum(u["a1_at_upper"] for u in B if not u["severe"]), len([u for u in B if not u["severe"]])),
                                  a1_at_zero=rate(sum(u["a1_at_zero"] for u in B), len(B)),
                                  r_at_lower_given_severe=rate(sum(u["r_at_lower"] for u in B if u["severe"]), len([u for u in B if u["severe"]])),
                                  r_at_lower_given_not=rate(sum(u["r_at_lower"] for u in B if not u["severe"]), len([u for u in B if not u["severe"]])))
        else:
            B = [u for u in U if "d0_at_bound" in u]
            t["q5_shifts"] = dict(d0_or_d1_at_bound=rate(sum(u["d0_at_bound"] or u["d1_at_bound"] for u in B), len(B)),
                                  shift_sum_S_quantiles=_quantiles([u["shift_sum_S"] for u in B]))
        out[fam] = t
    return out


def _median(v):
    v = [x for x in v if np.isfinite(x)]
    return float(np.median(v)) if v else None


def _quantiles(v):
    v = np.asarray([x for x in v if np.isfinite(x)], float)
    return dict(zip(("min", "q05", "q25", "median", "q75", "q95", "max"), map(float, np.quantile(v, [0, .05, .25, .5, .75, .95, 1])))) if v.size else None


def write_csv(path, rows):
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    with open(os.path.join(RUN, "identity.json")) as fh:
        ident = BT.digest(json.load(fh))
    os.makedirs(OUT, exist_ok=True)
    panel_rows = []
    for i, e in enumerate(DP.load_panel()["panel"]):
        key = DP.panel_key(e)
        o = DP.load_output(os.path.join(RUN, "panel", key + ".npy"), key, ident)
        if not o["parity"]["equal"]:
            raise SystemExit(f"{key}: no parity; not analysed")
        check_evidence(o)
        panel_rows += units(o, dict(set="panel", role=e["role"], generator=e["generator"], strength=e["strength"],
                                    drift=e["drift_index"], replicate=e["replicate"], subject=e["subject"], g_rec=e["g_rec"],
                                    g_rec_window=e["g_rec_window"]))
    ideal_rows, ideal_recs = [], []
    subjects = BT.templates()
    for g, di, s in DP.ideal_jobs(subjects):
        key = DP.ideal_key(g, di, s)
        o = DP.load_output(os.path.join(RUN, "ideal", key + ".npy"), key, ident)
        ideal_rows += units(o, dict(set="ideal", generator=g, drift=di, subject=s))
        ev = np.asarray(o.get("evidence", [np.nan] * 3), float)
        n = o.get("n_trials", 0)
        ideal_recs.append(dict(generator=g, drift=di, subject=s, status=o["status"], evidence_null=ev[0], evidence_graded=ev[1],
                               evidence_twostate=ev[2], n_trials=n, delta=o.get("delta"),
                               graded_minus_null_per_trial=4 * (ev[1] - ev[0]) / n if n else np.nan,
                               preferred=MODELS[int(np.nanargmax(ev))] if np.isfinite(ev).any() else None))
    write_csv(os.path.join(OUT, "units_panel.csv"), panel_rows)
    write_csv(os.path.join(OUT, "units_ideal.csv"), ideal_rows)
    write_csv(os.path.join(OUT, "recordings_ideal.csv"), ideal_recs)

    summary = dict(run=os.path.basename(RUN), identity=ident, definitions=dict(severe=SEVERE, bound_tol=BOUND_TOL, near_bound=NEAR_BOUND,
                                                                               distinct=DISTINCT, material=MATERIAL, floor=FLOOR),
                   integrity="evidence rebuilt from logged folds equals the stored summary for all 40 panel recordings",
                   panel_main=family_tables([u for u in panel_rows if u["main"]]),
                   panel_early=family_tables([u for u in panel_rows if not u["main"]]),
                   panel_main_worst=family_tables([u for u in panel_rows if u["main"] and u["role"] == "worst"]),
                   panel_main_median=family_tables([u for u in panel_rows if u["main"] and u["role"] == "median"]),
                   ideal_all=family_tables(ideal_rows),
                   ideal_by_generator={g: family_tables([u for u in ideal_rows if u["generator"] == g]) for g in DP.IDEAL_GENERATORS},
                   ideal_recordings={f"{g}|d{di}": dict(
                       n=len(R), status_ok=sum(r["status"] == "ok" for r in R),
                       delta_median=_median([r["delta"] for r in R if r["delta"] is not None]),
                       delta_positive=sum(1 for r in R if r["delta"] is not None and np.isfinite(r["delta"]) and r["delta"] > 0),
                       graded_below_null_more_than_1nat=sum(1 for r in R if np.isfinite(r["graded_minus_null_per_trial"]) and r["graded_minus_null_per_trial"] < -1),
                       preferred=dict(collections.Counter(r["preferred"] for r in R)))
                       for g in DP.IDEAL_GENERATORS for di in range(2) for R in [[r for r in ideal_recs if r["generator"] == g and r["drift"] == di]]})
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(BT._jsonable(summary), fh, indent=1)
    print(json.dumps(BT._jsonable(summary), indent=1))


if __name__ == "__main__":
    main()

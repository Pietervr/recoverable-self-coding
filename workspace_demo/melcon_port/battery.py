#!/usr/bin/env python3
"""The synthetic development battery — PREREG_secondary_melcon.md §9, DRAFT v4 (Codex, continuation review 3, V3.5).
No EEG is read. Development checks of the implementation, not calibrated family-error control.

Stage A (continuous preprocessing and QC on artificial raw recordings): test_preprocess.py.
Stage B (the isolation property of §4): test_recording.py.
Stage C (this file): the complete pipeline of §4–§8 on synthetic epochs (synthetic.py).

Templates: the nocue recordings that pass §2 at the events-table level (TEMPLATES, 34 recordings: sub-35 nocue is not on
OpenNeuro and sub-36 nocue is excluded, README D14), so every replicate has the real sample's size and the §8 thresholds
apply unchanged. Cells: 5 generators × 2 decoder strengths (held-out AUC ≈ 0.6 and ≈ 0.8) × 2 drift conditions (none;
0.3 SD per block) × 3 replicates = 60 replicates × 34 recordings = 2,040 synthetic recordings. A recording's seed tags
are (1, generator index, strength index, drift index, replicate, subject).

Strength calibration (independent of every family outcome): for each generator and target AUC the amplitude is chosen
on a calibration draw (tags (2, generator, target, 0, subject)) of the first N_CAL templates without drift, as the
amplitude on the grid CAL_GRID whose calibration statistic is nearest the target, refined by linear interpolation of the
statistic between the two bracketing grid points; the statistic is the median over recordings of the recording's mean
held-out AUC over the two halves and the ten main-interval windows. The amplitude is accepted if a fresh check draw
(tags (2, generator, target, 1, subject)) lands within CAL_TOL of the target; otherwise the grid is refined once around
the interpolated amplitude (five points spanning ±25 %) and checked again on the check draw; a second miss is reported and
the cell runs at the last interpolated amplitude, flagged.

Pass criteria, evaluated on the main interval with group.decide:
  - G1, G2, G3, in every strength × drift cell: at least 2 of the 3 replicates end in a substantive outcome (two-state,
    graded, inconclusive/mixed) and at most 1 replicate ends 'two-state'. Technical failure, insufficient sensitivity and
    insufficient availability are not substantive: they count against the first requirement and never pass a cell.
  - X1 at AUC ≈ 0.8, both drift conditions: 'two-state' in at least 2 of 3 replicates.
  - X2: no pass criterion; reported diagnostics are the outcome counts, the median fitted component separation
    (e^delta0 / sigma of the two-state fits, main interval) and the median absolute error of the fitted occupancy at the
    recording's trials against the generating occupancy.
  - Stages A and B pass.
A failure leads to a registered revision of the protocol and a re-run; every result and revision is retained.

Cost: unbenchmarked until `--benchmark` has timed one recording of the complete pipeline on one worker (the Mac is
shared with the running refit probe); the full stage C is then staged around the probe and the PC audit.

CLI:  --benchmark | --calibrate [--n-jobs N] | --run [--n-jobs N] [--generators G1,X1] | --summarize
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import pandas as pd

import decoder as DEC
import group as G
import likelihood as LK
import recording as RC
import synthetic as SY

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results", "battery")
STRENGTHS = (0.6, 0.8)
DRIFTS = (False, True)
N_REP = 3
N_CAL = 8
CAL_GRID = (0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.2, 3.2)
CAL_TOL = 0.03


def templates() -> list:
    """Nocue recordings passing §2 at the events-table level, in subject order."""
    df = pd.read_csv(SY.TRIALS_CSV)
    out = []
    for s, t in df[df.task == "nocue"].groupby("subject"):
        if s == 36:                                                    # README D14: sorted, unrandomised trial order
            continue
        t = t[~(t.present & ~(t.contrast > 0))]
        pres, catch = t[t.present], t[t["catch"]]
        if len(pres) < 250 or len(catch) < 25:
            continue
        ok = True
        for b, tb in t.groupby("block"):
            if tb["catch"].sum() < LK.MIN_CATCH or min((tb.present & (tb.side == side)).sum() for side in ("left", "right")) < LK.MIN_SIDE:
                ok = False
        for half in DEC.HALVES:
            if t[t.block.isin(half)]["catch"].sum() < DEC.MIN_CATCH_HALF:
                ok = False
        if ok:
            out.append(int(s))
    return out


def summary(res: dict) -> dict:
    """What the group rule and the diagnostics need from one recording result (no epochs, no per-start records)."""
    keep = {k: res[k] for k in ("status", "subject", "task")}
    if res["status"] != "ok":
        return keep
    sep, occ_err = [], []
    halves = sorted(res["decoder"]["halves"])
    for (hi, fi, w), s in res["folds"].items():
        if w in DEC.MAIN and s["twostate"]["available"]:
            th, sc = s["twostate"]["theta"], s["twostate"]["scaling"]
            sep.append(float(np.exp(th[2]) / np.exp(th[1])))
            B = halves[hi]
            tr = res["decoder"]["halves"][B]["trials"]
            b_te = B[1] if fi == 0 else B[0]
            t = tr[(tr.block == b_te) & ~tr["catch"]]
            if "occupancy_true" in t:
                x = (np.log(t["contrast"].to_numpy(float)) - sc["m"]) / sc["s"]
                A = 1.0 / (1.0 + np.exp(-np.exp(th[5]) * (x - th[4])))
                occ_err.append(float(np.median(np.abs(A - t["occupancy_true"].to_numpy(float)))))
    keep.update(windows=res["windows"], models=res["models"], evidence=res["evidence"], available=res["available"],
                delta=res["delta"], n_trials=res["n_trials"], auc=res["auc"],
                twostate_separation_median=float(np.median(sep)) if sep else np.nan,
                occupancy_abs_error_median=float(np.median(occ_err)) if occ_err else np.nan)
    return keep


def main_positions(res_windows) -> list:
    return [res_windows.index(w) for w in DEC.MAIN]


def calibration_statistic(recs: list) -> float:
    vals = []
    for rec in recs:
        dec = DEC.split_half(rec)
        if dec["status"] != "ok":
            continue
        vals.append(float(np.nanmean([d["auc"][DEC.MAIN] for d in dec["halves"].values()])))
    return float(np.median(vals)) if vals else np.nan


def _draw(generator, amplitude, draw, target_i, subjects):
    gi = SY.GENERATORS.index(generator)
    return [SY.generate(SY.template(s, "nocue"), generator, amplitude, False, tags=(2, gi, target_i, draw, s)) for s in subjects]


def calibrate(generator: str, target_i: int, subjects: list, log=print) -> dict:
    target = STRENGTHS[target_i]
    cal = {a: calibration_statistic(_draw(generator, a, 0, target_i, subjects)) for a in CAL_GRID}
    log(f"{generator} target {target}: grid {json.dumps({str(a): round(v, 3) for a, v in cal.items()})}")

    def interpolate(table):
        a = np.array(sorted(table))
        v = np.array([table[x] for x in a])
        above = np.where(v >= target)[0]
        if above.size == 0:
            return float(a[-1])
        j = int(above[0])
        if j == 0:
            return float(a[0])
        return float(a[j - 1] + (target - v[j - 1]) * (a[j] - a[j - 1]) / (v[j] - v[j - 1]))
    amp = interpolate(cal)
    check = calibration_statistic(_draw(generator, amp, 1, target_i, subjects))
    refined = False
    if not abs(check - target) <= CAL_TOL:
        refined = True
        local = {a: calibration_statistic(_draw(generator, a, 0, target_i, subjects))
                 for a in np.round(amp * np.array([0.75, 0.875, 1.0, 1.125, 1.25]), 4)}
        amp = interpolate({**cal, **local})
        check = calibration_statistic(_draw(generator, amp, 1, target_i, subjects))
    entry = dict(generator=generator, target=target, amplitude=amp, check=check, refined=refined,
                 accepted=bool(abs(check - target) <= CAL_TOL), grid={str(k): v for k, v in cal.items()})
    log(f"  -> amplitude {amp:.4f}, check {check:.3f}, accepted {entry['accepted']}")
    return entry


def run_recording(generator, strength_i, drift_i, rep, subject, amplitude, path):
    if os.path.exists(path):
        return path
    gi = SY.GENERATORS.index(generator)
    rec = SY.generate(SY.template(subject, "nocue"), generator, amplitude, DRIFTS[drift_i],
                      tags=(1, gi, strength_i, drift_i, rep, subject))
    res = summary(RC.recording_scores(rec, subject, "nocue"))
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        np.save(fh, np.array([res], dtype=object), allow_pickle=True)
    os.replace(tmp, path)
    return path


def cell_path(generator, strength_i, drift_i, rep, subject):
    return os.path.join(OUT_DIR, "recordings", f"{generator}_s{strength_i}_d{drift_i}_r{rep}_sub-{subject:02d}.npy")


def load(path):
    return np.load(path, allow_pickle=True)[0]


def cell_verdicts(outcomes: dict) -> dict:
    """outcomes {(generator, strength_i, drift_i): [outcome per replicate]} -> the §9 verdicts."""
    substantive = {"two-state", "graded", "inconclusive/mixed"}
    out = {}
    for (g, si, di), reps in outcomes.items():
        if g in ("G1", "G2", "G3"):
            ok = sum(o in substantive for o in reps) >= 2 and sum(o == "two-state" for o in reps) <= 1
            out[(g, si, di)] = "pass" if ok else "fail"
        elif g == "X1" and STRENGTHS[si] == 0.8:
            out[(g, si, di)] = "pass" if sum(o == "two-state" for o in reps) >= 2 else "fail"
        else:
            out[(g, si, di)] = "reported"
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--generators", default=",".join(SY.GENERATORS))
    ap.add_argument("--n-jobs", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(os.path.join(OUT_DIR, "recordings"), exist_ok=True)
    subjects = templates()
    gens = a.generators.split(",")
    if a.benchmark:
        t0 = time.time()
        rec = SY.generate(SY.template(subjects[0], "nocue"), "X1", 1.0, False, tags=(3, 0))
        t1 = time.time()
        res = RC.recording_scores(rec, subjects[0], "nocue")
        t2 = time.time()
        per = t2 - t0
        n_rec = len(SY.GENERATORS) * len(STRENGTHS) * len(DRIFTS) * N_REP * len(subjects)
        n_cal = len(SY.GENERATORS) * len(STRENGTHS) * (len(CAL_GRID) + 1) * N_CAL
        info = dict(templates=len(subjects), status=res["status"], generate_s=t1 - t0, pipeline_s=t2 - t1,
                    recordings_stage_c=n_rec, projected_stage_c_core_hours=n_rec * per / 3600,
                    calibration_decoder_runs=n_cal, projected_calibration_core_hours=n_cal * (t1 - t0 + 11.0) / 3600,
                    note="one worker on a machine shared with the refit probe; decoder-only runs assumed at 11 s")
        print(json.dumps(info, indent=2))
        with open(os.path.join(OUT_DIR, "benchmark.json"), "w") as fh:
            json.dump(info, fh, indent=2)
    if a.calibrate:
        cal_path = os.path.join(OUT_DIR, "calibration.json")
        done = json.load(open(cal_path)) if os.path.exists(cal_path) else []
        have = {(e["generator"], e["target"]) for e in done}
        for g in gens:
            for ti in range(len(STRENGTHS)):
                if (g, STRENGTHS[ti]) in have:
                    continue
                done.append(calibrate(g, ti, subjects[:N_CAL]))
                with open(cal_path, "w") as fh:
                    json.dump(done, fh, indent=2)
    if a.run:
        cal = {(e["generator"], e["target"]): e["amplitude"] for e in json.load(open(os.path.join(OUT_DIR, "calibration.json")))}
        jobs = [(g, si, di, r, s, cal[(g, STRENGTHS[si])], cell_path(g, si, di, r, s))
                for g in gens for si in range(len(STRENGTHS)) for di in range(len(DRIFTS)) for r in range(N_REP)
                for s in subjects]
        if a.n_jobs > 1:
            from joblib import Parallel, delayed
            Parallel(n_jobs=a.n_jobs)(delayed(run_recording)(*j) for j in jobs)
        else:
            for j in jobs:
                run_recording(*j)
    if a.summarize:
        outcomes, rows = {}, []
        for g in gens:
            for si in range(len(STRENGTHS)):
                for di in range(len(DRIFTS)):
                    for r in range(N_REP):
                        paths = [cell_path(g, si, di, r, s) for s in subjects]
                        if not all(os.path.exists(p) for p in paths):
                            continue
                        res = [load(p) for p in paths]
                        ok = [x for x in res if x["status"] == "ok"]
                        pos = main_positions(ok[0]["windows"]) if ok else []
                        n_pass = sum(not x["status"].startswith("excluded") for x in res)
                        d = G.decide(res, pos, n_pass)
                        outcomes.setdefault((g, si, di), []).append(d["outcome"])
                        rows.append(dict(generator=g, strength=STRENGTHS[si], drift=DRIFTS[di], replicate=r, outcome=d["outcome"],
                                         n_windows_eligible=d.get("n_windows_eligible"),
                                         median_auc_main=float(np.nanmedian(d.get("median_auc", [np.nan]))),
                                         twostate_separation=float(np.nanmedian([x.get("twostate_separation_median", np.nan) for x in ok]))
                                         if ok else np.nan,
                                         occupancy_abs_error=float(np.nanmedian([x.get("occupancy_abs_error_median", np.nan) for x in ok]))
                                         if ok else np.nan))
        verdicts = cell_verdicts(outcomes)
        pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, "replicates.csv"), index=False)
        with open(os.path.join(OUT_DIR, "verdicts.json"), "w") as fh:
            json.dump({f"{g}|{STRENGTHS[si]}|{DRIFTS[di]}": dict(outcomes=outcomes[(g, si, di)], verdict=v)
                       for (g, si, di), v in verdicts.items()}, fh, indent=2)
        print(pd.DataFrame(rows).to_string())
        print(json.dumps({f"{k}": v for k, v in verdicts.items()}, indent=1))


if __name__ == "__main__":
    main()

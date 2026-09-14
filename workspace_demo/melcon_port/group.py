#!/usr/bin/env python3
"""Group comparison, the total outcome rule and the participant bootstrap — PREREG_secondary_melcon.md §7–§8, DRAFT v4
(Codex, continuation review 3, V3.4 and V3.6). Input: recording.recording_scores results (one per recording of one
task). Nothing here is run on ds006171 before the freeze.

Per window: a recording enters the window's group comparison when all three models are available on all four folds;
the window is ELIGIBLE when at least MIN_ELIGIBLE recordings enter it; the group comparison is spm_BMS
(sergent_port/bms.py) on the entering recordings' evidence, seeded per window. A RUN for a model is at least RUN_LENGTH
windows that are ADJACENT on the physical window grid, each eligible, each with that model's pxp >= PXP_THRESHOLD
(adjacency is never re-established by dropping ineligible windows).

The decision function, evaluated in this order (the first that applies is the outcome):
  1. technical failure — more than a quarter of the recordings that pass §2 end in a technical failure, or fewer than
     MIN_ELIGIBLE recordings pass §2;
  2. insufficient sensitivity — per recording and window the held-out AUC is the mean of its two halves (missing if
     either is not finite); per window the median over recordings with a finite value, missing if fewer than
     MIN_ELIGIBLE have one; the outcome applies when no window of W has a median >= AUC_THRESHOLD;
  3. insufficient availability — fewer than MIN_WINDOWS_ELIGIBLE of the windows of W are eligible;
  4. two-state — a two-state run and no graded run in W; 5. graded — a graded run and no two-state run;
  6. inconclusive/mixed — otherwise (neither family runs, or both do); a null run changes nothing and is reported.
Every per-window cohort (its recordings) is reported, and a common-cohort sensitivity repeats the comparison on the
recordings that enter every eligible window of W.

Bootstrap (V3.6): statistic = the equal-weight mean over participants of the per-recording held-out log-score
difference per trial, per window, pointwise (no simultaneous band is claimed); B = N_BOOT resamples of participants with
replacement, seed BOOT_SEED, a resampled participant carrying its whole time course and both tasks; the 95 % interval
is the 2.5th and 97.5th percentiles of the finite resampled statistics; within a resample a window's mean uses the
resampled participants with a finite value, and is missing if fewer than MIN_BOOT_N have one; the interval is reported
only if at least MIN_FINITE_FRACTION of the resamples are finite. Separate estimators: nocue, informative, and their
paired difference over participants with both tasks. The same resampling (seed + 1) gives the interval of the median
held-out AUC per half and window, and (seed + 2) the interval of the median catch occupancy of the 3'L sensitivity.
These intervals describe the summary over already-fitted recordings; they are not a refitting bootstrap of the decoder
and the likelihood fits.
"""
from __future__ import annotations

import importlib.util
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("sergent_bms", os.path.join(HERE, "..", "sergent_port", "bms.py"))
BMS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BMS)

MIN_ELIGIBLE = 20
RUN_LENGTH = 3
PXP_THRESHOLD = 0.95
AUC_THRESHOLD = 0.55
MIN_WINDOWS_ELIGIBLE = 8
TECH_FAILURE_FRACTION = 0.25
BMS_SEED = 20260913
BMS_NSAMP = 1_000_000
N_BOOT = 2000
BOOT_SEED = 20260913
MIN_BOOT_N = 10
MIN_FINITE_FRACTION = 0.95
OUTCOMES = ("technical failure", "insufficient sensitivity", "insufficient availability", "two-state", "graded",
            "inconclusive/mixed")

SPEC = dict(min_eligible=MIN_ELIGIBLE, run_length=RUN_LENGTH, pxp_threshold=PXP_THRESHOLD, auc_threshold=AUC_THRESHOLD,
            min_windows_eligible=MIN_WINDOWS_ELIGIBLE, tech_failure_fraction=TECH_FAILURE_FRACTION, bms_seed=BMS_SEED,
            bms_nsamp=BMS_NSAMP, n_boot=N_BOOT, boot_seed=BOOT_SEED, min_boot_n=MIN_BOOT_N,
            min_finite_fraction=MIN_FINITE_FRACTION, outcomes=OUTCOMES)


def runs(flags) -> bool:
    """True if at least RUN_LENGTH consecutive True entries on the physical grid."""
    count = 0
    for f in flags:
        count = count + 1 if f else 0
        if count >= RUN_LENGTH:
            return True
    return False


def window_comparison(results: list, window_positions: list, nsamp: int = BMS_NSAMP) -> list:
    """Per window position (index into each result's windows): cohort, eligibility and pxp of the three models."""
    ok = [r for r in results if r["status"] == "ok"]
    out = []
    for p in window_positions:
        cohort = [r for r in ok if bool(np.all(r["available"][p]))]
        row = dict(position=p, window=(ok[0]["windows"][p] if ok else None),
                   cohort=[(r["subject"], r["task"]) for r in cohort], n=len(cohort), eligible=len(cohort) >= MIN_ELIGIBLE)
        if row["eligible"]:
            lme = np.stack([r["evidence"][p] for r in cohort])
            b = BMS.spm_bms(lme, nsamp=nsamp, rng=np.random.default_rng([BMS_SEED, int(row["window"])]))
            row.update(pxp=b["pxp"], bor=float(b["bor"]), exp_r=b["exp_r"])
        else:
            row.update(pxp=np.full(3, np.nan), bor=np.nan, exp_r=np.full(3, np.nan))
        out.append(row)
    return out


def decide(results: list, window_positions: list, n_pass_section2: int, nsamp: int = BMS_NSAMP,
           models=("null", "graded", "twostate")) -> dict:
    """The total decision function on one interval W (positions in physical order)."""
    n_tech = sum(r["status"].startswith("technical failure") for r in results)
    report = dict(n_recordings=len(results), n_pass_section2=n_pass_section2, n_technical_failure=n_tech,
                  n_excluded=sum(r["status"].startswith("excluded") for r in results))
    if n_pass_section2 < MIN_ELIGIBLE or n_tech > TECH_FAILURE_FRACTION * n_pass_section2:
        return dict(report, outcome="technical failure")
    ok = [r for r in results if r["status"] == "ok"]
    med = []
    for p in window_positions:
        vals = [float(np.mean(r["auc"][p])) for r in ok if np.all(np.isfinite(r["auc"][p]))]
        med.append(float(np.median(vals)) if len(vals) >= MIN_ELIGIBLE else np.nan)
    report["median_auc"] = med
    if not any(np.isfinite(m) and m >= AUC_THRESHOLD for m in med):
        return dict(report, outcome="insufficient sensitivity")
    rows = window_comparison(results, window_positions, nsamp)
    report["windows"] = rows
    n_elig = sum(r["eligible"] for r in rows)
    report["n_windows_eligible"] = n_elig
    if n_elig < MIN_WINDOWS_ELIGIBLE:
        return dict(report, outcome="insufficient availability")
    idx = {m: i for i, m in enumerate(models)}
    run = {m: runs([r["eligible"] and r["pxp"][idx[m]] >= PXP_THRESHOLD for r in rows]) for m in models}
    report["runs"] = run
    if run["twostate"] and not run["graded"]:
        outcome = "two-state"
    elif run["graded"] and not run["twostate"]:
        outcome = "graded"
    else:
        outcome = "inconclusive/mixed"
    # common-cohort sensitivity: the recordings in every eligible window
    elig = [r for r in rows if r["eligible"]]
    common = set(elig[0]["cohort"]).intersection(*[set(r["cohort"]) for r in elig[1:]]) if elig else set()
    report["common_cohort"] = sorted(common)
    if len(common) >= MIN_ELIGIBLE:
        sub = [r for r in ok if (r["subject"], r["task"]) in common]
        crow = window_comparison(sub, window_positions, nsamp)
        crun = {m: runs([r["eligible"] and r["pxp"][idx[m]] >= PXP_THRESHOLD for r in crow]) for m in models}
        report["common_cohort_runs"] = crun
    return dict(report, outcome=outcome)


def _boot_indices(n: int, seed: int, n_boot: int = N_BOOT) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def _interval(stats: np.ndarray) -> dict:
    finite = np.isfinite(stats)
    frac = float(finite.mean()) if stats.size else 0.0
    if frac < MIN_FINITE_FRACTION:
        return dict(lo=np.nan, hi=np.nan, finite_fraction=frac)
    return dict(lo=float(np.percentile(stats[finite], 2.5)), hi=float(np.percentile(stats[finite], 97.5)), finite_fraction=frac)


def bootstrap_mean(values: np.ndarray, seed: int = BOOT_SEED) -> list:
    """values (n_participants, n_windows) with NaN where missing: pointwise equal-weight mean and 95 % interval."""
    v = np.asarray(values, dtype=float)
    n, nw = v.shape
    idx = _boot_indices(n, seed)
    out = []
    for w in range(nw):
        col = v[:, w]
        fin = np.isfinite(col)
        point = float(np.mean(col[fin])) if fin.sum() >= MIN_BOOT_N else np.nan
        res = col[idx]
        cnt = np.isfinite(res).sum(axis=1)
        stats = np.where(cnt >= MIN_BOOT_N, np.nansum(res, axis=1) / np.maximum(cnt, 1), np.nan)
        out.append(dict(point=point, n=int(fin.sum()), **_interval(stats)))
    return out


def bootstrap_median(values: np.ndarray, seed: int) -> list:
    v = np.asarray(values, dtype=float)
    n, nw = v.shape
    idx = _boot_indices(n, seed)
    out = []
    for w in range(nw):
        col = v[:, w]
        fin = np.isfinite(col)
        point = float(np.median(col[fin])) if fin.sum() >= MIN_BOOT_N else np.nan
        res = col[idx]
        stats = np.array([np.median(r[np.isfinite(r)]) if np.isfinite(r).sum() >= MIN_BOOT_N else np.nan for r in res])
        out.append(dict(point=point, n=int(fin.sum()), **_interval(stats)))
    return out


def participant_delta_matrix(results_by_task: dict, participants: list, window_positions: list) -> dict:
    """{task: (n_participants, n_windows)} of held-out log-score differences per trial, NaN where missing, rows in the
    order of `participants`, so that one row index = one participant across tasks (resampled together)."""
    out = {}
    for task, results in results_by_task.items():
        m = np.full((len(participants), len(window_positions)), np.nan)
        by = {r["subject"]: r for r in results if r["status"] == "ok"}
        for i, s in enumerate(participants):
            if s in by:
                m[i] = by[s]["delta"][window_positions]
        out[task] = m
    return out


def bootstrap_tasks(results_by_task: dict, window_positions: list, seed: int = BOOT_SEED) -> dict:
    """The three estimators: per task, and the paired informative - nocue difference over participants with both."""
    participants = sorted({r["subject"] for rs in results_by_task.values() for r in rs if r["status"] == "ok"})
    mats = participant_delta_matrix(results_by_task, participants, window_positions)
    out = {task: bootstrap_mean(m, seed) for task, m in mats.items()}
    if {"nocue", "informative"} <= set(mats):
        out["informative_minus_nocue"] = bootstrap_mean(mats["informative"] - mats["nocue"], seed)
    out["participants"] = participants
    return out

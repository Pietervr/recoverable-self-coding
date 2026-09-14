#!/usr/bin/env python3
"""Single-trial "projected activity" decoder — port of the section
"SINGLE TRIAL PREDICTIONS WITHOUT TEMPORAL GENERALIZATION (NO DECIMATION)" of
SoundConsciousEEG_MNE_GAT_SingleTrials.py (Sergent 2017), which produced the file
classif_SingleTrialPred_vowelpresence_train_maxSNR_test_allSNR_{active,passive}_20_subjects.mat
that the model-fitting script (SoundConscEEG_SingleTrialPred_ModelFitting_Twind30ms_batch.m) loads.

Original design (kept exactly unless stated in README.md):
  * per time sample (500 Hz, 1250 samples, -0.5 .. 1.998 s), no decimation
  * features: the first 63 of the 64 channels (coi = range(63))
  * classifier: make_pipeline(StandardScaler(), LogisticRegression())  [sklearn defaults of 2017:
    L2, C = 1, solver liblinear] wrapped in mne.decoding.SlidingEstimator
  * labels: snr == 1 (no sound) vs snr == max level (6 = -5 dB; 7 for passive S11-S20)
  * StratifiedKFold(n_splits=10) without shuffling, split separately on the training trials
    (stratified on snr) and on the intermediate-SNR trials (stratified on a constant)
  * for each fold: fit on 9/10 of the {1, max} trials; decision_function on the held-out
    {1, max} trials and on 1/10 of the intermediate-SNR trials -> every trial receives exactly one
    signed distance per time sample ("projected activity")

Output per subject: <DERIVED_DIR>/S{n}_{session}_preds.npz  (preds (n_trials, n_times), snr, fold,
trialinfo, time, ...) and <RESULTS_DIR>/trials_S{n}_{session}.csv with the trial metadata.
"""
from __future__ import annotations

import argparse
import os
import sys
import time as _time

import numpy as np
import pandas as pd
import sklearn
import mne
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from mne.decoding import SlidingEstimator

from common import (COL_AUDIB, COL_BLOCK, COL_EVAL, COL_RESPSIDE, COL_SNR, COL_VOWEL, DERIVED_DIR,
                    RESULTS_DIR, derived_path, load_subject)

mne.set_log_level("WARNING")


def make_clf(solver: str):
    # sklearn <= 0.21 defaults: penalty='l2', C=1.0, solver='liblinear', tol=1e-4, max_iter=100.
    # 'liblinear' is still available and reproduces that estimator (intercept regularised, as then).
    # (L2 is the default penalty in every sklearn version; naming it explicitly is deprecated in 1.8.)
    return make_pipeline(StandardScaler(), LogisticRegression(solver=solver, C=1.0))


def decode_subject(subject: int, session: str, n_jobs: int = 8, solver: str = "liblinear",
                   n_splits: int = 10, overwrite: bool = False, tag: str = "", max_level=None) -> str:
    out = derived_path(subject, session, tag)
    if os.path.exists(out) and not overwrite:
        print(f"S{subject} {session}: exists, skipping ({out})")
        return out
    t0 = _time.time()
    d = load_subject(subject, session)
    X, ti, times = d["X"], d["trialinfo"], d["time"]
    snr = ti[:, COL_SNR]
    # max level: 6, or 7 for passive S11-S20 (the original hard-codes 6 / 7 per subject list). With
    # --max-level 6 on a 7-level dataset, the level-7 trials are neither trained on nor scored (NaN),
    # which is what the literal 20-subject section of the original script does (it leaves them at 0).
    max_level = int(snr.max()) if max_level is None else int(max_level)
    n_trials, n_times = X.shape[0], X.shape[2]

    train_cond = np.where((snr == 1) | (snr == max_level))[0]
    gen_cond = np.where((snr > 1) & (snr < max_level))[0]
    excluded = np.where(snr > max_level)[0]

    # original: StratifiedKFold(n_splits=10, random_state=0) with the default shuffle=False, i.e. an
    # in-order split; modern sklearn refuses random_state without shuffle, so it is simply omitted.
    cv = StratifiedKFold(n_splits=n_splits)
    cv_train = cv.split(X[train_cond], snr[train_cond])
    cv_gen = cv.split(X[gen_cond], np.ones_like(snr[gen_cond]))
    trains, tests = zip(*[(train_cond[tr], train_cond[te]) for tr, te in cv_train])
    gens = [gen_cond[te] for _, te in cv_gen]

    sliding = SlidingEstimator(make_clf(solver), n_jobs=n_jobs)
    y_pred = np.zeros((n_trials, n_times))
    fold_of_trial = np.full(n_trials, -1, dtype=np.int64)
    for fold, (train, test, gen) in enumerate(zip(trains, tests, gens)):
        assert set(snr[train]) == {1, max_level}
        sliding.fit(X=X[train], y=snr[train])
        y_pred[test] = sliding.decision_function(X[test])
        y_pred[gen] = sliding.decision_function(X[gen])
        fold_of_trial[test] = fold
        fold_of_trial[gen] = fold
    y_pred[excluded] = np.nan
    assert (fold_of_trial[np.setdiff1d(np.arange(n_trials), excluded)] >= 0).all(), "every trial must be scored exactly once"

    os.makedirs(DERIVED_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    np.savez_compressed(out, preds=y_pred, time=times, snr=snr, fold=fold_of_trial, trialinfo=ti,
                        max_level=max_level, subject=subject, session=session, solver=solver,
                        n_splits=n_splits, sklearn_version=sklearn.__version__, mne_version=mne.__version__,
                        labels=np.array(d["labels"]))
    meta = pd.DataFrame({
        "trial": np.arange(n_trials),
        "block": ti[:, COL_BLOCK],
        "snr_level": snr,
        "vowel": ti[:, COL_VOWEL],
        ("eval" if session == "active" else "questtype"): ti[:, COL_EVAL],
        "respside": ti[:, COL_RESPSIDE],
        ("audibility" if session == "active" else "response"): ti[:, COL_AUDIB],
        "cv_fold": fold_of_trial,
        "role": np.where(np.isin(np.arange(n_trials), train_cond), "train_cond",
                         np.where(np.isin(np.arange(n_trials), excluded), "excluded", "gen_cond")),
    })
    meta.to_csv(os.path.join(RESULTS_DIR, f"trials_S{subject}_{session}{tag}.csv"), index=False)
    dt = _time.time() - t0
    print(f"S{subject} {session}: {n_trials} trials, max level {max_level}, {len(train_cond)} train-cond, "
          f"{len(gen_cond)} gen-cond, {dt/60:.1f} min -> {out}", flush=True)
    return out


def parse_subjects(s: str):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", default="active", choices=["active", "passive"])
    ap.add_argument("--subjects", default="1-20", help="e.g. 1-5 or 1,3,7")
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--solver", default="liblinear", choices=["liblinear", "lbfgs"])
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--tag", default="", help="output-name suffix for a sensitivity run (e.g. _lbfgs); '' = main run")
    ap.add_argument("--max-level", type=int, default=None,
                    help="force the 'sound present' training level (default: the dataset's highest level)")
    a = ap.parse_args()
    for s in parse_subjects(a.subjects):
        decode_subject(s, a.session, n_jobs=a.n_jobs, solver=a.solver, overwrite=a.overwrite, tag=a.tag,
                       max_level=a.max_level)

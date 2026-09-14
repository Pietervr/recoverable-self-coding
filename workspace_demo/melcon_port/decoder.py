#!/usr/bin/env python3
"""The split-half presence decoder — PREREG_secondary_melcon.md §4–§5, DRAFT v4. It reads only preprocessed epochs
(preprocess.py) or synthetic ones (synthetic.py); nothing here is run on ds006171 EEG before the freeze.

Per recording, the four blocks form two halves, H1 = {1, 2} and H2 = {3, 4}. For each half A as the decoder half, a
presence decoder is fitted per time sample on A's retained trials (StandardScaler -> LogisticRegression(liblinear,
C = 1, class_weight 'balanced', random_state SEED); features the 128 channels typed 'eeg'; labels catch = 0, present =
1, or in the top-quintile variant catch against the present trials at or above A's 80th contrast percentile) and applied
to every retained trial of the other half B. B's decision values are z-scored per sample with the mean and SD of A's
in-sample decision values at that sample (SD below SD_FLOOR makes the sample unavailable), low-passed at 10 Hz
(12th-order Butterworth, forward-backward over the whole epoch), and averaged in half-open 30 ms windows on time
edges from -300 to +900 ms. Held-out presence AUC per window is computed on B. A decoder half with fewer than
MIN_CATCH_HALF catch trials among its retained trials excludes the recording (PREREG §2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfilt, sosfiltfilt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SEED = 20260913
FS = 512.0
HALVES = ((1, 2), (3, 4))
SMOOTH_HZ, SMOOTH_ORDER = 10.0, 12
WIN_START, WIN_STEP, N_WIN = -0.3, 0.03, 40
SD_FLOOR = 1e-8
MIN_CATCH_HALF = 10
VARIANTS = ("all_present", "top_quintile")
SOS = butter(SMOOTH_ORDER, SMOOTH_HZ, btype="low", fs=FS, output="sos")

SPEC = dict(seed=SEED, halves=HALVES, smoother=(SMOOTH_ORDER, SMOOTH_HZ, "sosfiltfilt"), windows=(WIN_START, WIN_STEP, N_WIN),
            sd_floor=SD_FLOOR, min_catch_half=MIN_CATCH_HALF, classifier="StandardScaler + LogisticRegression(liblinear, "
            "C=1, class_weight='balanced')", variants=VARIANTS)


def window_edges() -> np.ndarray:
    return WIN_START + WIN_STEP * np.arange(N_WIN + 1)


def window_samples(time: np.ndarray) -> list:
    e = window_edges()
    t = np.asarray(time)
    return [np.where((t >= e[j] - 1e-9) & (t < e[j + 1] - 1e-9))[0] for j in range(N_WIN)]


def interval_windows(t0: float, t1: float) -> list:
    e = window_edges()
    return [j for j in range(N_WIN) if e[j] >= t0 - 1e-9 and e[j + 1] <= t1 + 1e-9]


MAIN = interval_windows(0.3, 0.6)
EARLY = interval_windows(0.0, 0.3)


def smooth(z: np.ndarray, causal: bool = False) -> np.ndarray:
    """The 10 Hz smoother along time: forward-backward (primary), or forward only from zero initial conditions at the
    epoch's first sample, -0.5 s (the causal-processing sensitivity; no delay compensation)."""
    return sosfilt(SOS, z, axis=1) if causal else sosfiltfilt(SOS, z, axis=1)


def _classifier():
    return LogisticRegression(solver="liblinear", C=1.0, class_weight="balanced", random_state=SEED)


def decision_values(Xa: np.ndarray, ya: np.ndarray, Xb: np.ndarray):
    """Per time sample: in-sample decision values on A (n_a, T) and held-out values on B (n_b, T)."""
    T = Xa.shape[2]
    da = np.empty((Xa.shape[0], T))
    db = np.empty((Xb.shape[0], T))
    for t in range(T):
        sc = StandardScaler().fit(Xa[:, :, t])
        clf = _classifier().fit(sc.transform(Xa[:, :, t]), ya)
        da[:, t] = clf.decision_function(sc.transform(Xa[:, :, t]))
        db[:, t] = clf.decision_function(sc.transform(Xb[:, :, t]))
    return da, db


def split_half(rec: dict, variant: str = "all_present", drop_edge: bool = False, causal: bool = False) -> dict:
    """{'status': 'ok' | 'excluded: ...', 'halves': {B: dict(decoder_half, trials, W (n_B, N_WIN), auc (N_WIN,))}}"""
    if variant not in VARIANTS:
        raise ValueError(variant)
    trials = rec["trials"]
    keep = trials["retained"].to_numpy(bool) & trials["has_epoch"].to_numpy(bool)
    if drop_edge:
        keep &= ~trials["edge_trial"].to_numpy(bool)
    rows = trials[keep]
    eeg_idx = [i for i, t in enumerate(rec["ch_types"]) if t == "eeg"]
    wins = window_samples(rec["time"])
    out = {}
    for A, B in ((HALVES[0], HALVES[1]), (HALVES[1], HALVES[0])):
        ra, rb = rows[rows.block.isin(A)], rows[rows.block.isin(B)]
        if int(ra["catch"].sum()) < MIN_CATCH_HALF:
            return dict(status=f"excluded: fewer than {MIN_CATCH_HALF} catch trials in decoder half {A}", halves={})
        if variant == "top_quintile":
            pres = ra[~ra["catch"]]
            thr = float(np.quantile(pres["contrast"], 0.8))
            ra = ra[ra["catch"] | (ra["contrast"] >= thr)]
        ya = (~ra["catch"].to_numpy(bool)).astype(int)
        Xa = rec["X"][ra["epoch_index"].to_numpy()][:, eeg_idx, :].astype(np.float64)
        Xb = rec["X"][rb["epoch_index"].to_numpy()][:, eeg_idx, :].astype(np.float64)
        da, db = decision_values(Xa, ya, Xb)
        mu, sd = da.mean(axis=0), da.std(axis=0, ddof=1)
        zb = (db - mu) / np.where(sd >= SD_FLOOR, sd, np.nan)
        zs = smooth(zb, causal)
        W = np.stack([zs[:, idx].mean(axis=1) for idx in wins], axis=1)
        present_b = ~rb["catch"].to_numpy(bool)
        auc = np.full(N_WIN, np.nan)
        if 0 < present_b.sum() < present_b.size:
            for j in range(N_WIN):
                if np.all(np.isfinite(W[:, j])):
                    auc[j] = roc_auc_score(present_b, W[:, j])
        out[B] = dict(decoder_half=A, trials=rb.reset_index(drop=True), W=W, auc=auc, z_mean=mu, z_sd=sd)
    return dict(status="ok", halves=out)

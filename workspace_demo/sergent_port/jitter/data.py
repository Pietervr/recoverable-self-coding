#!/usr/bin/env python3
"""jitter/data.py — the data layer of DESIGN_jitter.md rev 6 §3 (data, preprocessing, spans, folds, the shared
noise model). Stage S1 (provisional implementation). Everything inherited is imported from the port one level up
(`sergent_port/fit_models.py`, `common.py`) and is not re-implemented: the 10 Hz zero-phase low-pass, the 53
window means (16 samples each, centres −285 + 30 i ms), the five block folds (block 21 always in training).

Per participant and span this module supplies
  - the window-mean matrix Y (n_trials × W) on the span's windows, levels k = snr − 1 ∈ {0..5} (catch = 0), blocks;
  - the training-only shared construction of §4: μ0 = mean of training catch trials, Σ = Ledoit–Wolf shrinkage on
    the training catch deviations about μ0 (one matrix for every model in that participant and fold), its Cholesky
    whitening; test trials are whitened with the TRAINING fold's μ0 and Σ;
  - the data identity (sha256 of the window means, levels and blocks) that every fit log carries (§5).
Spans (§3): PRIMARY = the 16 windows with centres 255–705 ms (sample times 240–720 ms); WHOLE = all 53 windows.
The template support is the span's sample-time range extended by the ±150 ms latency truncation (§4).
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PORT_DIR = os.path.dirname(HERE)
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)

from common import COL_BLOCK, load_preds  # noqa: E402  (the inherited port)
from fit_models import TWOI, block_folds, lowpass_filtfilt, window_means  # noqa: E402

N_WINDOWS = 53
WINDOW_SAMPLES = 16
SAMPLE_MS = 2.0
FIRST_WINDOW_START_MS = -300.0
WINDOW_STEP_MS = 30.0
TAU_TRUNC_MS = 150.0           # latency truncation ±150 ms (§4)
N_LEVELS = 6                   # levels 0..5 after the −1 shift; catch = 0
PRIMARY_WINDOWS = np.arange(18, 34)      # centres 255 .. 705 ms
WHOLE_WINDOWS = np.arange(N_WINDOWS)
RESULTS_DIR = os.path.join(HERE, "results")


def window_centres_ms() -> np.ndarray:
    return FIRST_WINDOW_START_MS + 15.0 + WINDOW_STEP_MS * np.arange(N_WINDOWS)


def window_sample_times_ms() -> np.ndarray:
    """(53, 16): the sample times (ms) averaged by `fit_models.window_means` for each window
    (TWOI[i] .. TWOI[i+1] inclusive = 16 samples at 2 ms; consecutive windows share one sample)."""
    starts = FIRST_WINDOW_START_MS + WINDOW_STEP_MS * np.arange(N_WINDOWS)
    return starts[:, None] + SAMPLE_MS * np.arange(WINDOW_SAMPLES)[None, :]


@dataclass(frozen=True)
class Span:
    name: str
    windows: np.ndarray            # indices into the 53 windows
    sample_times_ms: np.ndarray    # (W, 16)
    support_ms: tuple              # template support = sample-time range ± TAU_TRUNC_MS

    @property
    def n_windows(self) -> int:
        return int(self.windows.size)

    @property
    def visible_range_ms(self) -> tuple:
        return float(self.sample_times_ms.min()), float(self.sample_times_ms.max())


def span(name: str) -> Span:
    if name == "primary":
        win = PRIMARY_WINDOWS
    elif name == "whole":
        win = WHOLE_WINDOWS
    else:
        raise KeyError(name)
    st = window_sample_times_ms()[win]
    return Span(name, win.copy(), st, (float(st.min() - TAU_TRUNC_MS), float(st.max() + TAU_TRUNC_MS)))


# ----------------------------------------------------------------------------------------------
# participants
# ----------------------------------------------------------------------------------------------
@dataclass
class Participant:
    subject: int
    session: str
    tag: str
    W53: np.ndarray        # (n, 53) window means of the filtered preds
    fpreds: np.ndarray     # (n, 1250) filtered preds (used only by the §5 template starts)
    time_ms: np.ndarray    # (1250,)
    levels: np.ndarray     # (n,) 0..5
    blocks: np.ndarray     # (n,) 1..21
    data_id: str

    @property
    def n(self) -> int:
        return int(self.levels.size)

    def level_counts(self) -> np.ndarray:
        return np.bincount(self.levels, minlength=N_LEVELS)


def data_identity(W53: np.ndarray, levels: np.ndarray, blocks: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(W53, dtype=np.float64).tobytes())
    h.update(np.ascontiguousarray(levels, dtype=np.int64).tobytes())
    h.update(np.ascontiguousarray(blocks, dtype=np.int64).tobytes())
    return h.hexdigest()[:16]


def participant_from_arrays(preds: np.ndarray, time_s: np.ndarray, snr: np.ndarray, blocks: np.ndarray,
                            subject: int = 0, session: str = "synthetic", tag: str = "") -> Participant:
    """The inherited preprocessing (`fit_models.fit_subject` steps 1–3) on raw preds: NaN trials dropped,
    10 Hz filtfilt, 53 window means, levels shifted by −1."""
    keep = ~np.isnan(preds).any(axis=1)
    fpreds = lowpass_filtfilt(preds[keep])
    W53 = window_means(fpreds)
    levels = (np.asarray(snr)[keep] - 1).astype(np.int64)
    blocks = np.asarray(blocks)[keep].astype(np.int64)
    return Participant(subject, session, tag, W53, fpreds, 1000.0 * np.asarray(time_s), levels, blocks,
                       data_identity(W53, levels, blocks))


def participant_from_windows(W53: np.ndarray, levels: np.ndarray, blocks: np.ndarray, subject: int = 0,
                             session: str = "synthetic", tag: str = "") -> Participant:
    """A participant whose 53-window matrix is given directly (synthetic data of §7.2 enter here: nothing is
    filtered or averaged again). `fpreds` is absent; template starts then use the window means (§5 fallback)."""
    W53 = np.asarray(W53, dtype=np.float64)
    levels = np.asarray(levels, dtype=np.int64)
    blocks = np.asarray(blocks, dtype=np.int64)
    time_ms = -500.0 + SAMPLE_MS * np.arange(1250)
    return Participant(subject, session, tag, W53, None, time_ms, levels, blocks, data_identity(W53, levels, blocks))


def load_participant(subject: int, session: str = "active", tag: str = "") -> Participant:
    z = load_preds(subject, session, tag)
    p = participant_from_arrays(z["preds"], z["time"], z["snr"].astype(np.int64),
                                z["trialinfo"][:, COL_BLOCK].astype(np.int64), subject, session, tag)
    if session == "passive" and subject == 6:  # the inherited faulty-trial rule applies before the NaN drop
        raise NotImplementedError("passive S6 trial removal: passive session deferred (§3)")
    return p


def folds(p: Participant):
    """The port's five block folds: list of (train_idx, test_idx); block 21 is never tested."""
    tr, te = block_folds(p.blocks, 5)
    return list(zip(tr, te))


# ----------------------------------------------------------------------------------------------
# the shared noise model (§4): μ0 and the Ledoit–Wolf Σ from training catch trials, Cholesky whitening
# ----------------------------------------------------------------------------------------------
def ledoit_wolf(X: np.ndarray):
    """Ledoit & Wolf (2004) shrinkage of the sample covariance of centred rows X (n × p) towards μI.
    S = XᵀX/n; μ = tr S / p; d² = ‖S − μI‖²_F/p; b̄² = Σ_k ‖x_k x_kᵀ − S‖²_F /(n² p); b² = min(b̄², d²);
    Σ* = (1 − b²/d²) S + (b²/d²) μ I.  Returns (Σ*, shrinkage b²/d²)."""
    X = np.asarray(X, dtype=np.float64)
    n, p = X.shape
    S = X.T @ X / n
    mu = np.trace(S) / p
    d2 = np.sum((S - mu * np.eye(p)) ** 2) / p
    if d2 <= 0:
        return mu * np.eye(p), 1.0
    sq = np.sum(X ** 2, axis=1)
    bbar2 = (np.sum(sq ** 2) - n * np.sum(S ** 2)) / (n ** 2 * p)
    b2 = min(max(bbar2, 0.0), d2)
    rho = b2 / d2
    return (1.0 - rho) * S + rho * mu * np.eye(p), float(rho)


@dataclass
class Whitening:
    mu0: np.ndarray        # (W,)
    Sigma: np.ndarray      # (W, W)
    L: np.ndarray          # Cholesky factor, Σ = L Lᵀ
    Linv: np.ndarray       # L⁻¹
    logdet: float          # log|Σ|
    shrinkage: float
    n_catch: int

    def whiten(self, Y: np.ndarray) -> np.ndarray:
        return (Y - self.mu0) @ self.Linv.T


def whitening(Y: np.ndarray, levels: np.ndarray) -> Whitening:
    catch = Y[levels == 0]
    if catch.shape[0] < 2:
        raise ValueError("fewer than two catch trials")
    mu0 = catch.mean(axis=0)
    Sigma, rho = ledoit_wolf(catch - mu0)
    L = np.linalg.cholesky(Sigma)
    Linv = np.linalg.inv(L)
    logdet = 2.0 * float(np.sum(np.log(np.diag(L))))
    return Whitening(mu0, Sigma, L, Linv, logdet, rho, int(catch.shape[0]))


@dataclass
class Dataset:
    """Trials on one span with one whitening. `U` = whitened deviations (n × W); `k` levels 0..5."""
    Y: np.ndarray
    k: np.ndarray
    span: Span
    wh: Whitening
    U: np.ndarray
    ident: str                 # data identity + span + role, for the fit logs and caches

    @property
    def n(self) -> int:
        return int(self.k.size)

    @property
    def W(self) -> int:
        return int(self.Y.shape[1])


def make_dataset(Y: np.ndarray, k: np.ndarray, sp: Span, wh: Whitening | None = None, ident: str = "") -> Dataset:
    Y = np.asarray(Y, dtype=np.float64)
    k = np.asarray(k, dtype=np.int64)
    wh = whitening(Y, k) if wh is None else wh
    return Dataset(Y, k, sp, wh, wh.whiten(Y), ident)


def fold_datasets(p: Participant, sp: Span, fold: int):
    """(train, test) Datasets of one block fold; μ0 and Σ from the TRAINING catch trials only."""
    tr, te = folds(p)[fold]
    Y = p.W53[:, sp.windows]
    train = make_dataset(Y[tr], p.levels[tr], sp, None, f"{p.data_id}/{sp.name}/fold{fold}/train")
    test = make_dataset(Y[te], p.levels[te], sp, train.wh, f"{p.data_id}/{sp.name}/fold{fold}/test")
    return train, test, tr, te


def full_dataset(p: Participant, sp: Span) -> Dataset:
    """All trials (block 21 included), μ0 and Σ from all catch trials (the §7.1 generator fits and the real
    full-data fits of §7.5)."""
    return make_dataset(p.W53[:, sp.windows], p.levels, sp, None, f"{p.data_id}/{sp.name}/full")


def n_scored(p: Participant) -> int:
    """Trials scored across the five folds (block 21 excluded) — the §5 score denominator."""
    return int(sum(te.size for _, te in folds(p)))

#!/usr/bin/env python3
"""Synthetic epoched recordings for the development battery — PREREG_secondary_melcon.md §9, DRAFT v6 (laws unchanged
since v4, Codex continuation review 3, V3.5; v6 corrects the G2 latent-ranking integration, Codex continuation review 5
§1). No EEG is read: a recording's structure (trial order, blocks, catch trials,
hemifields, contrasts) is taken from a real events table (results/trials_all.csv, behaviour only); every sample is
generated. The output has the shape and fields preprocess.preprocess_raw returns, so decoder.py and recording.py run
on it unchanged. The continuous preprocessing and QC are checked separately on artificial raw recordings
(test_preprocess.py, battery stage A).

The laws, exactly (x = the recording's present log contrast z-scored over its present trials, a generation-side
quantity; L = lg(DOSE_SLOPE x), 0 on catch trials; eps ~ N(0, 1) independent per trial):
  G1 graded homogeneous     z = 2 L + eps
  G2 graded skewed          z = 2 L + e,  e a skew-normal (shape 2) standardized to mean 0 and SD 1
  G3 graded heteroscedastic z = 2 L + (1 + L) eps          (SD 1 at zero dose, 2 at full dose)
  X1 separated mixture      z = 2 B + eps,   B ~ Bernoulli(L)   (component separation 2 SD)
  X2 overlapping mixture    z = 0.8 B + eps, B ~ Bernoulli(L)   (separation 0.8 SD)
Catch trials follow the dose-absent law (L = 0; B = 0). Present trials in the right hemifield add HEMI_SHIFT to z. With
drift, every trial of block b adds DRIFT_PER_BLOCK (b - 1) to z. The occupancy curve L puts half occupancy at the
recording's mean log contrast, near its median seen rate of about one half.

Sensors: X_eeg(i, ch, t) = amplitude * z_i * p_ch * env(t) + sum_s M(ch, s) a_s(i, t) + SENSOR_SD n(i, ch, t), with p a
fixed unit-norm spatial pattern over the 128 channels, env(t) = exp(-(t - ENV_CENTER)^2 / (2 ENV_SD^2)), M a fixed
128 x 16 mixing matrix (entries N(0, 1/16)) of 16 unit-variance AR(1) sources with coefficient AR_PHI per sample at
512 Hz, and white sensor noise; four EOG channels of white noise (EOG_SD), never decoder features. Samples on the
epoch grid -0.5 .. +1.0 s at 512 Hz (769); each trial and channel is baseline-corrected over -0.5 .. 0 s, as the
epochs of preprocess.py are. p and M are fixed by (SEED, 101); a recording's draws by the seed tags it is given.
"""
from __future__ import annotations

import functools
import os

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm, skewnorm

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS_CSV = os.path.join(HERE, "results", "trials_all.csv")
SEED = 20260913
FS = 512.0
TIME = -0.5 + np.arange(769) / FS
N_EEG, N_EOG = 128, 4
EOG_NAMES = ("VEOG1", "VEOG2", "HEOG1", "HEOG2")
GENERATORS = ("G1", "G2", "G3", "X1", "X2")
DOSE_SLOPE = 1.5
HEMI_SHIFT = 0.3
DRIFT_PER_BLOCK = 0.3
ENV_CENTER, ENV_SD = 0.45, 0.12
N_SOURCES, AR_PHI, SENSOR_SD, EOG_SD = 16, 0.9, 0.5, 1.0
SKEW_SHAPE = 2.0

G2_GRID_STEP, G2_GRID_SPAN = 0.002, 10.0

SPEC = dict(seed=SEED, generators=GENERATORS, dose_slope=DOSE_SLOPE, hemi_shift=HEMI_SHIFT, drift_per_block=DRIFT_PER_BLOCK,
            envelope=(ENV_CENTER, ENV_SD), n_sources=N_SOURCES, ar_phi=AR_PHI, sensor_sd=SENSOR_SD, eog_sd=EOG_SD,
            skew_shape=SKEW_SHAPE, fixed_pattern_seed=(SEED, 101),
            g2_latent_auc=dict(step=G2_GRID_STEP, span=G2_GRID_SPAN, cdf="cumulative trapezoid"))


def fixed_pattern_and_mixing():
    rng = np.random.default_rng(np.random.SeedSequence([SEED, 101]))
    p = rng.normal(size=N_EEG)
    p /= np.linalg.norm(p)
    M = rng.normal(size=(N_EEG, N_SOURCES)) / np.sqrt(N_SOURCES)
    return p, M


@functools.lru_cache(maxsize=1)
def events_table() -> pd.DataFrame:
    """results/trials_all.csv, read once per process (its SHA-256 is part of the battery identity, re-verified on disk)."""
    return pd.read_csv(TRIALS_CSV)


def template(subject: int, task: str) -> pd.DataFrame:
    """A recording's trial structure from its events table (behaviour only); present trials with a non-positive
    contrast are excluded as in PREREG §2."""
    df = events_table()
    t = df[(df.subject == subject) & (df.task == task)].sort_values("onset_pd").reset_index(drop=True)
    t = t[~(t.present & ~(t.contrast > 0))].reset_index(drop=True)
    return t[["subject", "task", "trial", "block", "catch", "present", "side", "contrast"]].copy()


def latent(generator: str, x: np.ndarray, catch: np.ndarray, rng: np.random.Generator):
    n = x.size
    L = np.where(catch, 0.0, expit(DOSE_SLOPE * np.where(catch, 0.0, x)))
    eps = rng.normal(size=n)
    high = np.zeros(n, dtype=bool)
    if generator == "G1":
        z = 2.0 * L + eps
    elif generator == "G2":
        a = SKEW_SHAPE
        dlt = a / np.sqrt(1 + a * a)
        mean, sd = dlt * np.sqrt(2 / np.pi), np.sqrt(1 - 2 * dlt * dlt / np.pi)
        e = (skewnorm.rvs(a, size=n, random_state=rng) - mean) / sd
        z = 2.0 * L + e
    elif generator == "G3":
        z = 2.0 * L + (1.0 + L) * eps
    elif generator in ("X1", "X2"):
        high = rng.random(n) < L
        z = (2.0 if generator == "X1" else 0.8) * high + eps
    else:
        raise ValueError(f"unknown generator {generator!r}")
    return z, L, high


def present_latent_auc(generator: str, L: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Per present trial with occupancy L and displayed-right flag: the population probability that its no-drift latent z
    exceeds that of an independent catch trial (catch follows the dose-absent law). This is the AUC of ranking by the
    noiseless latent, which the synthetic readout approaches as the amplitude grows (Codex, continuation review 4, §5).
    Exact for G1, G3, X1 and X2:
      G1  Phi((2L + 0.3h) / sqrt 2)          G3  Phi((2L + 0.3h) / sqrt(1 + (1 + L)^2))
      X   (1 - L) Phi(0.3h / sqrt 2) + L Phi((d + 0.3h) / sqrt 2),  d = 2 (X1), 0.8 (X2)
    G2 by the distribution of the difference of two independent standardized skew-normals: its density by convolution on a
    grid of step 0.002 SD over +-10 SD, its CDF by the cumulative trapezoid rule and linear interpolation (v6). v5 took a
    plain cumulative sum, which integrates a full last cell and overstated the first-eight-template limit by 0.000196
    (Codex, continuation review 5 §1); the trapezoid's agreement with adaptive quadrature is measured in test_battery.py."""
    L = np.asarray(L, dtype=float)
    shift = HEMI_SHIFT * np.asarray(right, dtype=float)
    if generator == "G1":
        return norm.cdf((2.0 * L + shift) / np.sqrt(2.0))
    if generator == "G3":
        return norm.cdf((2.0 * L + shift) / np.sqrt(1.0 + (1.0 + L) ** 2))
    if generator in ("X1", "X2"):
        d = 2.0 if generator == "X1" else 0.8
        return (1.0 - L) * norm.cdf(shift / np.sqrt(2.0)) + L * norm.cdf((d + shift) / np.sqrt(2.0))
    if generator == "G2":
        a = SKEW_SHAPE
        dlt = a / np.sqrt(1 + a * a)
        mean, sd = dlt * np.sqrt(2 / np.pi), np.sqrt(1 - 2 * dlt * dlt / np.pi)
        h = G2_GRID_STEP
        e = np.arange(-G2_GRID_SPAN, G2_GRID_SPAN + h / 2, h)
        f = sd * skewnorm.pdf(mean + sd * e, a)                       # density of the standardized noise
        pdf_d = np.convolve(f, f[::-1]) * h                           # D = e_catch - e_present
        grid_d = 2.0 * e[0] + h * np.arange(pdf_d.size)
        cdf_d = np.concatenate(([0.0], np.cumsum(0.5 * (pdf_d[1:] + pdf_d[:-1])) * h))
        return np.interp(2.0 * L + shift, grid_d, cdf_d)
    raise ValueError(f"unknown generator {generator!r}")


def generate(tmpl: pd.DataFrame, generator: str, amplitude: float, drift: bool, tags=()) -> dict:
    rng = np.random.default_rng(np.random.SeedSequence([SEED, *[int(t) for t in tags]]))
    trials = tmpl.reset_index(drop=True).copy()
    n = len(trials)
    catch = trials["catch"].to_numpy(bool)
    right = (trials["side"].to_numpy() == "right") & ~catch
    lc = np.log(np.where(catch, 1.0, trials["contrast"].to_numpy(float)))
    x = np.where(catch, 0.0, (lc - lc[~catch].mean()) / lc[~catch].std(ddof=1))
    z, L, high = latent(generator, x, catch, rng)
    z = z + HEMI_SHIFT * right
    if drift:
        z = z + DRIFT_PER_BLOCK * (trials["block"].to_numpy(float) - 1.0)
    p, M = fixed_pattern_and_mixing()
    env = np.exp(-((TIME - ENV_CENTER) ** 2) / (2 * ENV_SD ** 2))
    T = TIME.size
    src = np.empty((n, N_SOURCES, T), dtype=np.float32)
    src[:, :, 0] = rng.normal(size=(n, N_SOURCES))
    innov = np.sqrt(1 - AR_PHI ** 2)
    for t in range(1, T):
        src[:, :, t] = AR_PHI * src[:, :, t - 1] + innov * rng.normal(size=(n, N_SOURCES))
    X = np.empty((n, N_EEG + N_EOG, T), dtype=np.float32)
    X[:, :N_EEG, :] = np.einsum("cs,nst->nct", M.astype(np.float32), src, optimize=True)
    X[:, :N_EEG, :] += (SENSOR_SD * rng.normal(size=(n, N_EEG, T))).astype(np.float32)
    X[:, :N_EEG, :] += (amplitude * z[:, None, None] * p[None, :, None] * env[None, None, :]).astype(np.float32)
    X[:, N_EEG:, :] = (EOG_SD * rng.normal(size=(n, N_EOG, T))).astype(np.float32)
    X -= X[:, :, TIME < 0].mean(axis=2, keepdims=True)
    trials["has_epoch"] = True
    trials["epoch_index"] = np.arange(n)
    trials["retained"] = True
    trials["reject_reason"] = ""
    trials["edge_trial"] = False
    trials["z_true"] = z
    trials["occupancy_true"] = L
    trials["high_true"] = high
    labels = [f"EEG{i:03d}" for i in range(N_EEG)] + list(EOG_NAMES)
    return dict(X=X, trials=trials, time=TIME.copy(), labels=labels, ch_types=["eeg"] * N_EEG + ["eog"] * N_EOG,
                fsample=FS, generator=generator, amplitude=float(amplitude), drift=bool(drift), tags=tuple(tags))

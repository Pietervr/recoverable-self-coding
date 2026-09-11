#!/usr/bin/env python3
"""Model fitting on the single-trial projected activity — port of
SoundConscEEG_SingleTrialPred_ModelFitting_Twind30ms_batch.m plus the three likelihood files
LLH_fun_null.m, LLH_fun_logisticB.m, LLH_fun_logisbimodalfixedsigma.m (Claire Sergent, Jan 2020).

Pipeline per subject and session (all as in the MATLAB, see README.md for the deviations):
  1. preds (n_trials x 1250) from decode.py, low-pass filtered: 12th-order Butterworth IIR,
     half-power 10 Hz at 500 Hz, zero-phase (filtfilt).
  2. 53 contiguous windows of 16 samples: TWOI = 101:15:901 (1-based) = -300 .. +1300 ms; the
     window value of a trial is the mean of the filtered preds over TWOI(i)..TWOI(i+1) inclusive.
  3. 5-fold cross-validation by BLOCK: test fold k = blocks 4(k-1)+1 .. 4(k-1)+4, train = all the
     other trials (a 21st block, present for a few subjects, is therefore in every training set and
     never tested — as in the original).
  4. For each window, each model, each fold: Nelder-Mead (MATLAB fminsearch defaults) maximising the
     training log-likelihood from the original's starting point; the model's score is the
     log-likelihood of the held-out trials under the fitted parameters, averaged over the 5 folds.
  5. SNR levels are shifted by -1 inside the models (0 = no sound, 1 = lowest SNR, ...).

Models (parameter order as in the .m files):
  Model 0  (null)      : sigma, mu
  Model 2B (unimodal)  : x0, k, L, sigma_slope, sigma_intercept, mu_maxsnr
  Model 3  (bifurcation): x0, k, mu_low, step, L_high, k_high, sigma

Outputs (RESULTS_DIR): fits_<session>.csv (one row per subject x window x model x fold, with train
and test LLH, exit flag and fitted parameters) and llh_<session>.csv (subject x window x model,
mean test LLH — the "lme" matrix handed to the Bayesian model selection).
"""
from __future__ import annotations

import argparse
import os
import time as _time
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import minimize
from scipy.signal import butter, sosfiltfilt

from common import COL_BLOCK, RESULTS_DIR, SUBJECTS, load_preds

SQRT2PI = np.sqrt(2 * np.pi)
FS = 500.0
LOWPASS_HZ = 10.0
FILTER_ORDER = 12
TWOI = np.arange(100, 901, 15)  # 0-based version of MATLAB's 101:15:901 -> 54 edges, 53 windows
N_CROSSVAL = 5
MODELS = ("model0", "model2B", "model3")
PARAM_NAMES = {
    "model0": ["sigma", "mu"],
    "model2B": ["x0", "k", "L", "sigma_slope", "sigma_intercept", "mu_maxsnr"],
    "model3": ["x0", "k", "mu_low", "step", "L_high", "k_high", "sigma"],
}


# ----------------------------------------------------------------------------------------------
# The three likelihoods — line-for-line ports. Natural log. `snrs` are ALREADY shifted by -1.
# ----------------------------------------------------------------------------------------------
def llh_null(pars, preds):
    sigma, mu = pars[0], pars[1]
    n = len(preds)
    sigma = abs(sigma)  # see README: MATLAB's log of a negative sigma is complex; fminsearch compares real parts
    return n * np.log(1.0 / (sigma * SQRT2PI)) - 0.5 * np.sum((preds - mu) ** 2) / sigma ** 2


def llh_logisticB(pars, preds, snrs):
    x0, k, L, sigma_slope, sigma_intercept, mu_maxsnr = pars
    xmax = float(np.max(snrs))
    with np.errstate(over="ignore"):
        Mu = L / (1.0 + np.exp(-k * (snrs - x0))) - L / (1.0 + np.exp(-k * (xmax - x0))) + mu_maxsnr
    Sigma = sigma_slope * Mu + sigma_intercept
    Sigma = np.abs(Sigma)  # real part of the MATLAB expression (see README)
    if np.any(Sigma == 0):
        return -np.inf
    return np.sum(np.log(1.0 / (Sigma * SQRT2PI))) - 0.5 * np.sum((preds - Mu) ** 2 / Sigma ** 2)


def llh_logisbimodalfixedsigma(pars, datapreds, snrs, first_level_mask):
    x0, k, mu_low, step, L_high, k_high, sigma = pars
    sigma = abs(sigma)
    if sigma == 0:
        return -np.inf
    with np.errstate(over="ignore"):
        A = 1.0 / (1.0 + np.exp(-k * (snrs - x0)))
        A = np.where(first_level_mask, 0.0, A)  # snr -inf (no sound) must be at 0 % heard
        Mu_high = L_high / (1.0 + np.exp(-k_high * (snrs - x0))) + step
        Mu_high = np.where(first_level_mask, mu_low, Mu_high)
        g_low = np.exp(-0.5 * ((datapreds - mu_low) / sigma) ** 2) / (sigma * SQRT2PI)
        g_high = np.exp(-0.5 * ((datapreds - Mu_high) / sigma) ** 2) / (sigma * SQRT2PI)
    mixture = (1.0 - A) * g_low + A * g_high
    with np.errstate(divide="ignore"):
        return np.sum(np.log(mixture))


# ----------------------------------------------------------------------------------------------
# fminsearch equivalent: Nelder-Mead (Lagarias et al. 1998) with MATLAB's default options
#   TolX = TolFun = 1e-4, MaxFunEvals = MaxIter = 200 * n_params, 5 % / 0.00025 initial simplex.
# scipy's implementation uses the same coefficients (rho 1, chi 2, psi 0.5, sigma 0.5), the same
# initial simplex and the same two-part stopping rule.
# ----------------------------------------------------------------------------------------------
def fminsearch(negfun, x0):
    x0 = np.asarray(x0, dtype=np.float64)
    n = x0.size
    res = minimize(negfun, x0, method="Nelder-Mead",
                   options=dict(xatol=1e-4, fatol=1e-4, maxiter=200 * n, maxfev=200 * n,
                                adaptive=False, disp=False))
    exitflag = 1 if res.success else 0
    return res.x, res.fun, exitflag, res.nfev


# ----------------------------------------------------------------------------------------------
def lowpass_filtfilt(preds: np.ndarray) -> np.ndarray:
    sos = butter(FILTER_ORDER, LOWPASS_HZ, btype="low", fs=FS, output="sos")
    return sosfiltfilt(sos, preds, axis=1)


def block_folds(blocks: np.ndarray, ncv: int = N_CROSSVAL):
    trials = np.arange(len(blocks))
    test_sets, train_sets = [], []
    if ncv == 5:
        for icv in range(5):
            bl = 4 * icv + np.array([1, 2, 3, 4])
            test = np.where(np.isin(blocks, bl))[0]
            test_sets.append(test)
            train_sets.append(trials[~np.isin(trials, test)])
    elif ncv == 10:
        for icv in range(10):
            bl = 2 * icv + np.array([1, 2])
            test = np.where(np.isin(blocks, bl))[0]
            test_sets.append(test)
            train_sets.append(trials[~np.isin(trials, test)])
    else:
        raise ValueError("Number of cross-validations must be either 5 or 10")
    return train_sets, test_sets


def window_means(fpreds: np.ndarray) -> np.ndarray:
    """(n_trials, 53): mean of the filtered preds over TWOI[i]..TWOI[i+1] inclusive."""
    out = np.empty((fpreds.shape[0], len(TWOI) - 1))
    for i in range(len(TWOI) - 1):
        out[:, i] = fpreds[:, TWOI[i]:TWOI[i + 1] + 1].mean(axis=1)
    return out


def fit_subject(subject: int, session: str, ncv: int = N_CROSSVAL, models=MODELS, preds_tag: str = "") -> pd.DataFrame:
    t0 = _time.time()
    z = load_preds(subject, session, preds_tag)
    preds = z["preds"]
    time_s = z["time"]
    SNRs = z["snr"].astype(np.int64)
    Blocknum = z["trialinfo"][:, COL_BLOCK].astype(np.int64)

    # REMOVE FAULTY TRIAL FOR SUBJECT INDEX 6 (subject name 7) in the passive session (trial 3, 1-based)
    keep = np.ones(len(SNRs), dtype=bool)
    if session == "passive" and subject == 6:
        keep[2] = False
    keep &= ~np.isnan(preds).any(axis=1)  # trials the decoder did not score (only in --max-level runs)

    fpreds = lowpass_filtfilt(preds)
    fpreds, SNRs, Blocknum = fpreds[keep], SNRs[keep], Blocknum[keep]
    train_sets, test_sets = block_folds(Blocknum, ncv)
    W = window_means(fpreds)  # (n_trials, n_windows)
    n_win = W.shape[1]
    t_ms = 1000.0 * time_s[TWOI[:-1]] + 15.0  # window centre label, as in the PlotFig script

    snr0 = SNRs - 1  # CAREFUL ! SNRs -1
    SNR_list = np.unique(snr0).astype(float)
    rows = []

    def sel(level):
        return snr0 == level

    for it in range(n_win):
        tw = W[:, it]
        # ---- Model 0
        if "model0" in models:
            init0 = np.array([1.0, 0.0])
            for icv in range(ncv):
                tr, te = train_sets[icv], test_sets[icv]
                bp, mllh, ef, nfev = fminsearch(lambda p: -llh_null(p, tw[tr]), init0)
                rows.append(dict(subject=subject, session=session, window=it, t_ms=t_ms[it], model="model0",
                                 fold=icv, train_llh=-mllh, test_llh=llh_null(bp, tw[te]), exitflag=ef,
                                 nfev=nfev, n_train=len(tr), n_test=len(te),
                                 **{f"p{i}": v for i, v in enumerate(bp)}))
        # ---- Model 2B
        if "model2B" in models:
            m_max = tw[sel(SNR_list[-1])].mean()
            m_min = tw[sel(SNR_list[1])].mean()
            s_max = tw[sel(SNR_list[-1])].std(ddof=1)
            s_min = tw[sel(SNR_list[1])].std(ddof=1)
            initx0 = (SNR_list[-1] + SNR_list[1]) / 2.0
            initk = (m_max - m_min) / (SNR_list[-1] - SNR_list[1])
            initL = 2.0 * m_max
            initsigma_slope = (s_max - s_min) / (m_max - m_min)
            initsigma_intercept = s_max - initsigma_slope * m_max
            initpars = np.array([initx0, initk, initL, initsigma_slope, initsigma_intercept, m_max])
            for icv in range(ncv):
                tr, te = train_sets[icv], test_sets[icv]
                bp, mllh, ef, nfev = fminsearch(lambda p: -llh_logisticB(p, tw[tr], snr0[tr].astype(float)), initpars)
                rows.append(dict(subject=subject, session=session, window=it, t_ms=t_ms[it], model="model2B",
                                 fold=icv, train_llh=-mllh,
                                 test_llh=llh_logisticB(bp, tw[te], snr0[te].astype(float)), exitflag=ef,
                                 nfev=nfev, n_train=len(tr), n_test=len(te),
                                 **{f"p{i}": v for i, v in enumerate(bp)}))
        # ---- Model 3
        if "model3" in models:
            m_max = tw[sel(SNR_list[-1])].mean()
            m_min = tw[sel(SNR_list[1])].mean()
            m_noise = tw[sel(SNR_list[0])].mean()
            init_x0 = (SNR_list[-1] + SNR_list[1]) / 2.0
            init_k = (m_max - m_min) / (SNR_list[-1] - SNR_list[1])
            init_mu_low = m_noise
            init_step = m_min - m_noise
            init_L_high = m_max - m_min
            init_k_high = (m_max - m_min) / (SNR_list[-1] - SNR_list[1])
            init_sigma = tw[sel(SNR_list[0])].std(ddof=1)
            initpars = np.array([init_x0, init_k, init_mu_low, init_step, init_L_high, init_k_high, init_sigma])
            first_all = snr0 == SNR_list[0]
            for icv in range(ncv):
                tr, te = train_sets[icv], test_sets[icv]
                # snrlist(1) is the first level present in the (training / test) set handed to the function
                f_tr = snr0[tr] == np.min(snr0[tr])
                f_te = snr0[te] == np.min(snr0[te])
                bp, mllh, ef, nfev = fminsearch(
                    lambda p: -llh_logisbimodalfixedsigma(p, tw[tr], snr0[tr].astype(float), f_tr), initpars)
                rows.append(dict(subject=subject, session=session, window=it, t_ms=t_ms[it], model="model3",
                                 fold=icv, train_llh=-mllh,
                                 test_llh=llh_logisbimodalfixedsigma(bp, tw[te], snr0[te].astype(float), f_te),
                                 exitflag=ef, nfev=nfev, n_train=len(tr), n_test=len(te),
                                 **{f"p{i}": v for i, v in enumerate(bp)}))
    df = pd.DataFrame(rows)
    print(f"S{subject} {session}: {len(df)} fits, {(_time.time()-t0)/60:.1f} min", flush=True)
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", default="active", choices=["active", "passive"])
    ap.add_argument("--subjects", default="1-20")
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--ncv", type=int, default=N_CROSSVAL)
    ap.add_argument("--tag", default=None, help="suffix for the output files (default: same as --preds-tag)")
    ap.add_argument("--preds-tag", default="", help="read the preds of a tagged decode run (e.g. _lbfgs)")
    a = ap.parse_args()
    from decode import parse_subjects
    subs = parse_subjects(a.subjects)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    dfs = Parallel(n_jobs=a.n_jobs)(delayed(fit_subject)(s, a.session, a.ncv, MODELS, a.preds_tag) for s in subs)
    df = pd.concat(dfs, ignore_index=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    tag = a.preds_tag if a.tag is None else a.tag
    df.to_csv(os.path.join(RESULTS_DIR, f"fits_{a.session}{tag}.csv"), index=False, float_format="%.6g")
    llh = (df.groupby(["subject", "window", "t_ms", "model"])["test_llh"].mean()
             .unstack("model").reset_index())
    llh.to_csv(os.path.join(RESULTS_DIR, f"llh_{a.session}{tag}.csv"), index=False, float_format="%.6g")
    ex = df.groupby("model")["exitflag"].mean()
    print("fraction of fminsearch runs that converged (exitflag == 1):")
    print(ex.to_string())
    neg = df.groupby("model").apply(lambda g: np.mean(g[[c for c in g.columns if c.startswith('p')]].iloc[:, -1] < 0)
                                    if g.name != "model2B" else np.nan)
    print("fraction of fits with a negative final sigma (model0: p0, model3: p6):",
          np.mean(df[df.model == "model0"]["p0"] < 0), np.mean(df[df.model == "model3"]["p6"] < 0))


if __name__ == "__main__":
    main()

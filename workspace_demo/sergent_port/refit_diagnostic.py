#!/usr/bin/env python3
"""Optimiser-cap diagnostic (RESULTS_sergent.md C8): what happens to the group comparison when the
evaluation-capped Nelder-Mead fits are allowed to continue.

For the windows 255, 285, 315, 435, 465, 495 ms, Models 2B and 3, every subject and block-fold:
  base     = the committed procedure (fminsearch defaults: 200*n evaluations / iterations)
  extended = restart Nelder-Mead from the base end point with maxiter = maxfev = 14,000 and keep
             whichever of {base, extended} has the higher TRAINING log-likelihood
then the held-out log-likelihood of both, and the three-model spm_BMS per window with Model 0 taken
unchanged from results/llh_<variant>.csv. This is a diagnostic of the specification's optimiser cap,
not a replacement of the reproduction (the cap is the specification).

Writes results/refit_diagnostic.csv (all fits) and results/refit_diagnostic_summary.csv.
"""
from __future__ import annotations

import argparse
import os
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import minimize

from bms import spm_bms
from common import COL_BLOCK, RESULTS_DIR, SUBJECTS, load_preds
from fit_models import (block_folds, llh_logisbimodalfixedsigma, llh_logisticB, lowpass_filtfilt, window_means)

TIMES = [255, 285, 315, 435, 465, 495]
EXTRA = 14000


def nm(fun, x0, maxev):
    return minimize(fun, x0, method="Nelder-Mead",
                    options=dict(xatol=1e-4, fatol=1e-4, maxiter=maxev, maxfev=maxev, adaptive=False))


def refit_subject(variant: str, subject: int):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    session = "passive" if variant.startswith("passive") else "active"
    tag = variant[len(session):]
    z = load_preds(subject, session, tag)
    preds, snr, blocks = z["preds"], z["snr"].astype(int), z["trialinfo"][:, COL_BLOCK]
    keep = np.ones(len(snr), bool)
    if session == "passive" and subject == 6:
        keep[2] = False
    keep &= ~np.isnan(preds).any(axis=1)
    W = window_means(lowpass_filtfilt(preds)[keep])
    s0 = (snr[keep] - 1).astype(float)
    trains, tests = block_folds(blocks[keep])
    lv = np.unique(s0)
    rows = []
    for tm in TIMES:
        w = int(round((tm + 285) / 30))
        tw = W[:, w]
        m_max, m_min, m_noise = tw[s0 == lv[-1]].mean(), tw[s0 == lv[1]].mean(), tw[s0 == lv[0]].mean()
        s_max, s_min, s_noise = tw[s0 == lv[-1]].std(ddof=1), tw[s0 == lv[1]].std(ddof=1), tw[s0 == lv[0]].std(ddof=1)
        x0 = (lv[-1] + lv[1]) / 2
        k = (m_max - m_min) / (lv[-1] - lv[1])
        a = (s_max - s_min) / (m_max - m_min)
        inits = {"model2B": np.array([x0, k, 2 * m_max, a, s_max - a * m_max, m_max]),
                 "model3": np.array([x0, k, m_noise, m_min - m_noise, m_max - m_min, k, s_noise])}
        for model, p0 in inits.items():
            for fold, (tr, te) in enumerate(zip(trains, tests)):
                if model == "model2B":
                    def ll(p, ix):
                        return llh_logisticB(p, tw[ix], s0[ix])

                    def scale_negative(p):  # any training trial with sigma_slope*Mu + sigma_intercept < 0 ?
                        x0_, k_, L_, a_, b_, mmax_ = p
                        with np.errstate(over="ignore"):
                            Mu = L_ / (1 + np.exp(-k_ * (s0[tr] - x0_))) - L_ / (1 + np.exp(-k_ * (s0[tr].max() - x0_))) + mmax_
                        return bool(np.any(a_ * Mu + b_ < 0))
                else:
                    def ll(p, ix):
                        return llh_logisbimodalfixedsigma(p, tw[ix], s0[ix], s0[ix] == s0[ix].min())

                    def scale_negative(p):
                        return bool(p[6] < 0)
                # README D6: count the objective evaluations at which the MATLAB code would have taken the
                # log of a negative scale (the port uses |sigma| there) along the capped optimisation path
                count = {"calls": 0, "negative": 0}

                def obj(p):
                    count["calls"] += 1
                    count["negative"] += scale_negative(p)
                    return -ll(p, tr)
                base = nm(obj, p0, 200 * len(p0))
                base_calls, base_neg = count["calls"], count["negative"]
                ext = nm(obj, base.x, EXTRA)
                best = ext if ext.fun < base.fun else base
                rows.append(dict(variant=variant, subject=subject, t_ms=tm, model=model, fold=fold,
                                 base_train=-base.fun, base_test=ll(base.x, te), base_converged=int(base.success),
                                 base_nfev=base_calls, base_negative_scale_evals=base_neg,
                                 ext_train=-best.fun, ext_test=ll(best.x, te), ext_converged=int(ext.success),
                                 ext_nfev=int(ext.nfev), ext_negative_scale_evals=count["negative"] - base_neg,
                                 n_test=len(te)))
    print(f"refit {variant} S{subject} done", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="active,active_lbfgs,passive")
    ap.add_argument("--n-jobs", type=int, default=6)
    a = ap.parse_args()
    variants = a.variants.split(",")
    batches = Parallel(n_jobs=a.n_jobs)(delayed(refit_subject)(v, s) for v in variants for s in SUBJECTS)
    df = pd.DataFrame([r for b in batches for r in b])
    df.to_csv(os.path.join(RESULTS_DIR, "refit_diagnostic.csv"), index=False, float_format="%.8g")
    rows = []
    rng = np.random.default_rng(0)
    for v in variants:
        d = df[df.variant == v]
        conv = d.groupby("model")[["base_converged", "ext_converged"]].mean()
        llh0 = pd.read_csv(os.path.join(RESULTS_DIR, f"llh_{v}.csv"))
        for tm in TIMES:
            dd = d[d.t_ms == tm]
            m = dd.groupby(["subject", "model"])[["base_test", "ext_test"]].mean().unstack("model")
            ref = llh0[np.isclose(llh0.t_ms, tm)].set_index("subject").loc[m.index]
            row = dict(variant=v, t_ms=tm,
                       max_abs_base_minus_committed=float(np.abs(
                           m["base_test"][["model2B", "model3"]].to_numpy() - ref[["model2B", "model3"]].to_numpy()).max()))
            for which in ["base", "ext"]:
                L = np.column_stack([ref.model0.to_numpy(), m[f"{which}_test"]["model2B"].to_numpy(),
                                     m[f"{which}_test"]["model3"].to_numpy()])
                r = spm_bms(L, nsamp=300_000, rng=rng)
                delta = L[:, 2] - L[:, 1]
                row.update({f"{which}_pxp0": r["pxp"][0], f"{which}_pxp2B": r["pxp"][1], f"{which}_pxp3": r["pxp"][2],
                            f"{which}_delta_3_minus_2B": delta.mean(), f"{which}_delta_sem": delta.std(ddof=1) / np.sqrt(len(delta)),
                            f"{which}_model3_wins": int((delta > 0).sum())})
            for model in ["model2B", "model3"]:
                row[f"conv_base_{model}"] = conv.loc[model, "base_converged"]
                row[f"conv_ext_{model}"] = conv.loc[model, "ext_converged"]
                dm = d[d.model == model]
                row[f"neg_scale_evals_base_{model}"] = int(dm.base_negative_scale_evals.sum())
                row[f"neg_scale_evals_ext_{model}"] = int(dm.ext_negative_scale_evals.sum())
                row[f"evals_base_{model}"] = int(dm.base_nfev.sum())
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RESULTS_DIR, "refit_diagnostic_summary.csv"), index=False, float_format="%.5g")
    pd.set_option("display.width", 250)
    print("negative-scale objective evaluations (README D6), base / extended paths, per variant:")
    print(out.groupby("variant")[[c for c in out.columns if c.startswith("neg_scale") or c.startswith("evals_base")]].first().to_string())
    print(out[["variant", "t_ms", "base_pxp3", "ext_pxp3", "base_pxp2B", "ext_pxp2B", "base_delta_3_minus_2B",
               "ext_delta_3_minus_2B", "base_model3_wins", "ext_model3_wins", "conv_ext_model2B", "conv_ext_model3",
               "max_abs_base_minus_committed"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()

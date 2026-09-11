#!/usr/bin/env python3
"""Group-level Bayesian model comparison per 30 ms window — port of
SoundConsciousEEG_SingleTrialPredict_ModelComp_Twind_PlotFig.m (script by Florent Meyniel):
    lme = [Model0_LLH, Model2B_LLH, Model3_LLH]  (subjects x models, cross-validated test LLH)
    [_, freq, xp, pxp, bor] = spm_BMS(lme, [], 0, 0, 1)   per window
    Simes correction of (1 - pxp) across windows, per model, alpha 0.05
Reads RESULTS_DIR/llh_<session>.csv (from fit_models.py); writes RESULTS_DIR/bms_<session>.csv and
figures/fig_b_model_comparison_<session>.{png,csv}.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bms import simes_threshold, spm_bms
from common import FIG_DIR, RESULTS_DIR

MODEL_COLS = ["model0", "model2B", "model3"]
MODEL_LABELS = {"model0": "Null model", "model2B": "Unimodal non-linear (2B)", "model3": "Bifurcation (3)"}
MODEL_COLORS = {"model0": "k", "model2B": (129 / 214, 96 / 214, 214 / 214), "model3": (147 / 200, 35 / 200, 59 / 200)}


def run(session: str, tag: str = "", nsamp: int = 1_000_000, seed: int = 0, alpha: float = 0.05):
    llh = pd.read_csv(os.path.join(RESULTS_DIR, f"llh_{session}{tag}.csv"))
    windows = np.sort(llh.window.unique())
    subjects = np.sort(llh.subject.unique())
    rng = np.random.default_rng(seed)
    rows = []
    for w in windows:
        d = llh[llh.window == w].set_index("subject").loc[subjects]
        lme = d[MODEL_COLS].to_numpy()
        r = spm_bms(lme, nsamp=nsamp, rng=rng)
        winner = np.argmax(lme, axis=1)
        row = dict(window=w, t_ms=float(d.t_ms.iloc[0]), n_subjects=len(subjects), bor=r["bor"])
        for k, m in enumerate(MODEL_COLS):
            row[f"freq_{m}"] = r["exp_r"][k]
            row[f"xp_{m}"] = r["xp"][k]
            row[f"pxp_{m}"] = r["pxp"][k]
            row[f"nwin_{m}"] = int(np.sum(winner == k))
            row[f"meanllh_{m}"] = float(lme[:, k].mean())
        dd = lme[:, 2] - lme[:, 1]
        row["d_llh_3_minus_2B_mean"] = dd.mean()
        row["d_llh_3_minus_2B_sem"] = dd.std(ddof=1) / np.sqrt(len(dd))
        dd = lme[:, 1] - lme[:, 0]
        row["d_llh_2B_minus_0_mean"] = dd.mean()
        row["d_llh_2B_minus_0_sem"] = dd.std(ddof=1) / np.sqrt(len(dd))
        rows.append(row)
    out = pd.DataFrame(rows)
    for m in MODEL_COLS:
        thr, sig = simes_threshold(1.0 - out[f"pxp_{m}"].to_numpy(), alpha)
        out[f"simes_sig_{m}"] = sig
        out[f"simes_thr_{m}"] = thr
    os.makedirs(FIG_DIR, exist_ok=True)
    out.to_csv(os.path.join(RESULTS_DIR, f"bms_{session}{tag}.csv"), index=False, float_format="%.6g")
    out[["window", "t_ms"] + [f"pxp_{m}" for m in MODEL_COLS] + [f"simes_sig_{m}" for m in MODEL_COLS]
        + [f"freq_{m}" for m in MODEL_COLS] + ["bor"]].to_csv(
        os.path.join(FIG_DIR, f"fig_b_model_comparison_{session}{tag}.csv"), index=False, float_format="%.6g")

    # ---- figure (the PlotFig layout: pxp time courses, Simes-significant windows as dots at 1.1)
    fig, ax = plt.subplots(figsize=(8.5, 5))
    t = out.t_ms.to_numpy()
    for m in MODEL_COLS:
        ax.plot(t, out[f"pxp_{m}"], lw=3, color=MODEL_COLORS[m], label=MODEL_LABELS[m])
        sig = out[f"simes_sig_{m}"].to_numpy()
        if sig.any():
            ax.plot(t[sig], 1.1 * np.ones(sig.sum()), ".", color=MODEL_COLORS[m], ms=14)
    ax.axhline(1 / 3, color="k", ls=":")
    ax.axvline(0, color="k")
    ax.set_xlim(t[0], t[-1]); ax.set_ylim(-0.07, 1.17)
    ax.set_xlabel("Time in ms"); ax.set_ylabel("Protected exceedance probability")
    ax.set_title(f"Bayesian model comparison, {session} session, n = {len(subjects)} (port)")
    ax.legend(loc="center right", frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, f"fig_b_model_comparison_{session}{tag}.png"), dpi=150)
    plt.close(fig)

    # ---- console summary
    pd.set_option("display.width", 220)
    print(f"=== {session}{tag}: BMS per window (n = {len(subjects)})")
    print(out[["window", "t_ms", "pxp_model0", "pxp_model2B", "pxp_model3", "simes_sig_model3", "nwin_model0",
               "nwin_model2B", "nwin_model3", "bor"]].round(3).to_string(index=False))
    best = out[[f"pxp_{m}" for m in MODEL_COLS]].to_numpy().argmax(axis=1)
    names = np.array(["0", "2B", "3"])[best]
    print("winner (highest pxp) per window:", " ".join(f"{int(tt)}:{n}" for tt, n in zip(t, names)))
    m3 = out.pxp_model3.to_numpy()
    above = t[m3 > 0.95]
    print("windows with pxp(bifurcation) > 0.95 (window centres, ms):", above.astype(int).tolist())
    print("Simes-significant windows for the bifurcation model:", t[out.simes_sig_model3].astype(int).tolist())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="active", choices=["active", "passive"])
    ap.add_argument("--tag", default="")
    ap.add_argument("--nsamp", type=int, default=1_000_000)
    a = ap.parse_args()
    run(a.session, a.tag, a.nsamp)

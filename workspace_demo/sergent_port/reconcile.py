#!/usr/bin/env python3
"""Reconciliation of the port against the publisher's Source Data (RESULTS_sergent.md C4, C6, C7)
and the two family/plotting sensitivities computed on the SAME saved likelihoods (C6, README D7).

Outputs
  figures/fig_b_pxp_published_vs_port_active.{csv,png}  published (Fig. 3E Source Data) vs port pxp curves
  results/c4_crossings.csv        neural x behavioural SD-profile correlation t-tests, {published, port} x {published, port}
  results/published_passive_sd_anova.csv   rmANOVA on the published passive SD profiles (Suppl. Fig. 4 Source Data)
  results/bms_two_model_<session>.csv      2B-vs-3 spm_BMS per window on the saved cross-validated LLH
  results/decoder_fold_block_overlap.csv   physical blocks whose trials fall into > 1 decoder test fold
  results/evidence_size.csv                held-out trials per fold and the per-trial size of the 3-2B evidence
All statistics on the Source Data are OUR calculations from the published subject-level tables, with the
port's conventions (levels 2-6, BH over windows, one-way rmANOVA), not the authors' statistics.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bms import simes_threshold, spm_bms
from common import COL_BLOCK, FIG_DIR, RESULTS_DIR, SUBJECTS, load_preds
from make_figures import ARTICLE_WINDOWS, bh_fdr, rm_anova
from model_comparison import MODEL_COLORS, MODEL_LABELS
from source_data import (XLSX, published_behaviour_sd, published_neural_sd_active, published_passive_sd,
                         published_pxp)

MODELS = ["model0", "model2B", "model3"]
WIN_LABELS = [f"{a}-{b}" for a, b in zip(ARTICLE_WINDOWS[:-1], ARTICLE_WINDOWS[1:])]


def sustained_start(winner, target, t):
    """first window from which `target` stays the winner for >= 3 consecutive windows."""
    for i in range(len(winner) - 2):
        if all(w == target for w in winner[i:i + 3]):
            return t[i]
    return np.nan


def pxp_overlay():
    t, px = published_pxp()
    port = pd.read_csv(os.path.join(RESULTS_DIR, "bms_active.csv"))
    assert np.allclose(port.t_ms.to_numpy(), t)
    df = pd.DataFrame(dict(t_ms=t))
    for k, m in enumerate(MODELS):
        df[f"published_pxp_{m}"] = px[:, k]
        df[f"port_pxp_{m}"] = port[f"pxp_{m}"].to_numpy()
    df["published_winner"] = np.array(MODELS)[px.argmax(axis=1)]
    df["port_winner"] = np.array(MODELS)[port[[f"pxp_{m}" for m in MODELS]].to_numpy().argmax(axis=1)]
    df.to_csv(os.path.join(FIG_DIR, "fig_b_pxp_published_vs_port_active.csv"), index=False, float_format="%.6g")

    fig, ax = plt.subplots(figsize=(9, 5))
    for m in MODELS:
        ax.plot(t, df[f"published_pxp_{m}"], lw=2.5, color=MODEL_COLORS[m], label=f"{MODEL_LABELS[m]} — published")
        ax.plot(t, df[f"port_pxp_{m}"], lw=1.5, ls="--", color=MODEL_COLORS[m], label=f"{MODEL_LABELS[m]} — port")
    ax.axhline(0.95, color="0.5", ls=":", lw=1); ax.axhline(1 / 3, color="k", ls=":", lw=1); ax.axvline(0, color="k")
    ax.set_xlim(t[0], t[-1]); ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Time in ms (window centre, PlotFig convention)"); ax.set_ylabel("Protected exceedance probability")
    ax.set_title("Active session: Fig. 3E Source Data (solid) vs this port (dashed)")
    ax.legend(fontsize=8, frameon=False, ncol=2, loc="center right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "fig_b_pxp_published_vs_port_active.png"), dpi=150); plt.close(fig)

    p3, q3 = df.published_pxp_model3.to_numpy(), df.port_pxp_model3.to_numpy()
    print("=== C6: published vs port pxp(bifurcation), active")
    for tm in [225, 255, 285, 315, 345, 525, 555, 585, 615, 645, 675]:
        i = int(np.where(t == tm)[0][0])
        print(f"  {tm:5d} ms  published {p3[i]:.3f}  port {q3[i]:.3f}  winners {df.published_winner[i]} / {df.port_winner[i]}")
    print("  first window with pxp3 > 0.95: published", t[p3 > 0.95][0], " port", t[q3 > 0.95][0])
    print("  windows > 0.95: published", t[p3 > 0.95].astype(int).tolist(), "\n                  port     ", t[q3 > 0.95].astype(int).tolist())
    print("  sustained (>=3 windows) bifurcation-highest start: published", sustained_start(df.published_winner.tolist(), "model3", t),
          " port", sustained_start(df.port_winner.tolist(), "model3", t))
    after = (t >= 300) & (t <= 660)
    print("  first window back to unimodal after the bifurcation period: published",
          t[(t > 600) & (df.published_winner == "model2B")][0], " port", t[(t > 600) & (df.port_winner == "model2B")][0])
    print("  mean |published - port| pxp3 over 315-645 ms: %.3f ; correlation over all 53 windows: %.3f"
          % (np.abs(p3 - q3)[(t >= 315) & (t <= 645)].mean(), np.corrcoef(p3, q3)[0, 1]))
    return df


def c4_crossings():
    beh_pub = published_behaviour_sd()                       # (20, 5) levels 2..6, 0-10 scale
    neu_pub = published_neural_sd_active()                   # (20, 8, 5)
    beh_port = (pd.read_csv(os.path.join(RESULTS_DIR, "behaviour_active.csv"))
                .pivot(index="subject", columns="level", values="sd_audib").loc[SUBJECTS, 2:6].to_numpy())
    neu_port = np.empty((20, 8, 5))
    for si, s in enumerate(SUBJECTS):
        z = load_preds(s, "active"); tms = 1000 * z["time"]
        for i, (lo, hi) in enumerate(zip(ARTICLE_WINDOWS[:-1], ARTICLE_WINDOWS[1:])):
            v = z["preds"][:, (tms > lo) & (tms <= hi)].mean(1)
            neu_port[si, i] = [v[z["snr"] == lv].std(ddof=1) for lv in range(2, 7)]
    rows = []
    for nl, N in [("published", neu_pub), ("port", neu_port)]:
        for bl, B in [("published", beh_pub), ("port", beh_port)]:
            R = np.array([[stats.pearsonr(N[s, i], B[s])[0] for i in range(8)] for s in range(20)])
            tt, pp = stats.ttest_1samp(R, 0.0, axis=0)
            pf = bh_fdr(pp)
            for i in range(8):
                rows.append(dict(neural=nl, behaviour=bl, window=WIN_LABELS[i], t=tt[i], p=pp[i], p_fdr=pf[i],
                                 cohen_d=R[:, i].mean() / R[:, i].std(ddof=1), mean_r=R[:, i].mean()))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, "c4_crossings.csv"), index=False, float_format="%.5g")
    print("=== C4: SD-profile correlation t(19) per window, {neural} x {behaviour}")
    piv = df.pivot_table(index=["neural", "behaviour"], columns="window", values="t")[WIN_LABELS]
    print(piv.round(3).to_string())
    print("  BH p at 200-250:", df[df.window == "200-250"][["neural", "behaviour", "p_fdr"]].round(4).to_string(index=False))
    print("  mean |published - port| behavioural SD (0-10 scale): %.3f" % np.abs(beh_pub - beh_port).mean())
    return df


def published_passive_anova():
    P = published_passive_sd()  # (20, 6 windows, 6 levels: -13 .. -3 dB)
    rows = []
    for i in range(6):
        F, df1, df2, p, eps, pgg = rm_anova(P[:, i, :5])   # levels 2..6 (-13 .. -5 dB), all 20 subjects
        rows.append(dict(window_index=i, window_assumed=f"{100*i}-{100*(i+1)}", F=F, df1=df1, df2=df2, p=p,
                         gg_eps=eps, p_gg=pgg, mean_profile=" ".join(f"{v:.3f}" for v in np.nanmean(P[:, i, :], axis=0))))
    df = pd.DataFrame(rows)
    df["p_bh"] = bh_fdr(df.p.to_numpy())
    df["p_gg_bh"] = bh_fdr(df.p_gg.to_numpy())
    df.to_csv(os.path.join(RESULTS_DIR, "published_passive_sd_anova.csv"), index=False, float_format="%.5g")
    print("=== C7: rmANOVA on the PUBLISHED passive SD profiles (Suppl. Fig. 4 Source Data), levels 2-6, 6 windows")
    print(df[["window_assumed", "F", "df1", "df2", "p", "p_bh", "gg_eps", "p_gg", "p_gg_bh", "mean_profile"]].round(4).to_string(index=False))
    return df


def two_model_bms(session):
    llh = pd.read_csv(os.path.join(RESULTS_DIR, f"llh_{session}.csv"))
    rows = []
    for w in np.sort(llh.window.unique()):
        d = llh[llh.window == w].set_index("subject").loc[SUBJECTS]
        L = d[["model2B", "model3"]].to_numpy()
        r = spm_bms(L)
        rows.append(dict(window=w, t_ms=float(d.t_ms.iloc[0]), pxp_model2B=r["pxp"][0], pxp_model3=r["pxp"][1],
                         xp_model3=r["xp"][1], freq_model3=r["exp_r"][1], bor=r["bor"]))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, f"bms_two_model_{session}.csv"), index=False, float_format="%.6g")
    three = pd.read_csv(os.path.join(RESULTS_DIR, f"bms_{session}.csv"))
    print(f"=== C6/C7: two-model (2B vs 3) BMS on the saved LLH, {session}")
    for tm in [285, 315, 345, 435, 465, 495, 555, 615]:
        i = int(np.where(np.isclose(df.t_ms, tm))[0][0])
        print(f"  {tm} ms: three-model pxp3 {three.pxp_model3[i]:.3f} pxp2B {three.pxp_model2B[i]:.3f}"
              f" | two-model pxp3 {df.pxp_model3[i]:.3f} pxp2B {df.pxp_model2B[i]:.3f} (BOR {df.bor[i]:.3f})")
    return df


def evidence_size():
    rows = []
    for session in ["active", "passive"]:
        fits = pd.read_csv(os.path.join(RESULTS_DIR, f"fits_{session}.csv"))
        llh = pd.read_csv(os.path.join(RESULTS_DIR, f"llh_{session}.csv"))
        ntest = fits[fits.model == "model3"].groupby("subject").n_test.mean()
        for tm in [315, 435, 465, 495]:
            d = llh[np.isclose(llh.t_ms, tm)].set_index("subject").loc[SUBJECTS]
            delta = (d.model3 - d.model2B).to_numpy()
            rows.append(dict(session=session, t_ms=tm, mean_n_test_per_fold=ntest.loc[SUBJECTS].mean(),
                             delta_3_minus_2B_per_fold=delta.mean(), delta_per_trial=np.mean(delta / ntest.loc[SUBJECTS].to_numpy()),
                             delta_2B_minus_0_per_fold=(d.model2B - d.model0).mean()))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, "evidence_size.csv"), index=False, float_format="%.5g")
    print("=== C6: evidence size (LLH = mean over 5 folds of the held-out fold SUM)")
    print(df.round(5).to_string(index=False))
    return df


def fold_block_overlap():
    rows = []
    for session in ["active", "passive"]:
        for s in SUBJECTS:
            z = load_preds(s, session)
            f = pd.DataFrame({"block": z["trialinfo"][:, COL_BLOCK], "fold": z["fold"]})
            f = f[f.fold >= 0]
            n_multi = int((f.groupby("block").fold.nunique() > 1).sum())
            rows.append(dict(session=session, subject=s, n_blocks=int(f.block.nunique()), blocks_in_multiple_test_folds=n_multi))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RESULTS_DIR, "decoder_fold_block_overlap.csv"), index=False)
    print("=== README: physical blocks spanning > 1 decoder test fold per subject")
    for session in ["active", "passive"]:
        d = df[df.session == session]
        print(f"  {session}: min {d.blocks_in_multiple_test_folds.min()} max {d.blocks_in_multiple_test_folds.max()} "
              f"median {d.blocks_in_multiple_test_folds.median()} of {d.n_blocks.min()}-{d.n_blocks.max()} blocks")
    return df


def mcp_variants():
    print("=== README D7: Simes-significant windows, BH '<=' (port) vs Meyniel/PlotFig strict '<'")
    for session in ["active", "passive"]:
        b = pd.read_csv(os.path.join(RESULTS_DIR, f"bms_{session}.csv"))
        for m in MODELS:
            p = 1 - b[f"pxp_{m}"].to_numpy()
            thr, mask = simes_threshold(p)
            print(f"  {session} {m}: thr {thr if np.isnan(thr) else round(thr, 5)}  BH<= {b.t_ms[mask].astype(int).tolist()}"
                  f"  strict< {b.t_ms[p < thr].astype(int).tolist() if not np.isnan(thr) else []}")


if __name__ == "__main__":
    print("Source Data workbook:", XLSX)
    pxp_overlay()
    c4_crossings()
    published_passive_anova()
    for s in ["active", "passive"]:
        two_model_bms(s)
    evidence_size()
    fold_block_overlap()
    mcp_variants()

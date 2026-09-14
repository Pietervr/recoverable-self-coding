#!/usr/bin/env python3
"""Figures (a) and (c) of the port plus the summary statistics the paper reports on the projected
activity, computed from the diagonal single-trial preds of decode.py.

(a) mean +/- SD of the projected activity by SNR level: time courses (group; 10 Hz filtered, as the
    paper's time-sample-by-sample analysis) and Fig.-2C-style profiles for the article's eight
    windows [50-100, 100-150, 150-200, 200-250, 250-300, 300-400, 400-500, 500-600 ms] — group and
    one example subject. Deviation: the paper's Fig. 2C profiles average the decimated
    train x test generalisation square over the window; here only the diagonal (train = test)
    preds exist, averaged over the window without filtering (as the paper states for Fig. 2C).
(c) the across-trial variability ("variance burst at threshold"): SD by SNR over time,
    baseline (no-sound) SD subtracted as in the paper; also the raw SD and the variance.

Stats (results/stats_<session>.csv, results/stats_timecourse_<session>.csv):
  * one-way repeated-measures ANOVAs per window (uncorrected F, plus Greenhouse-Geisser p):
    on the mean profile, on its first difference (the paper's non-linearity test), on the
    baseline-subtracted SD profile and on its first difference (levels 2..max).
  * per-subject Pearson correlation between the neural SD profile (raw SD, levels 2..max) and the
    behavioural SD-of-audibility profile (levels 2..max), t-test across subjects, BH-FDR, Cohen's d
    (the MATLAB "TTEST ON CORR COEFF" block) — active session only; and the same for mean profiles
    (levels 1..max, mean audibility), per window and per time sample (Fig. 3D).
Behaviour comes from trialinfo column 6 (audibility 0-10 of the RETAINED trials; the OSF
behavioural .mat files are MATLAB tables scipy cannot read).
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import COL_AUDIB, COL_EVAL, FIG_DIR, RESULTS_DIR, SNR_DB_MAIN, SUBJECTS, load_preds
from fit_models import lowpass_filtfilt

ARTICLE_WINDOWS = [50, 100, 150, 200, 250, 300, 400, 500, 600]
LEVEL_COLORS = {1: "k", 2: (0, 0.25, 1), 3: (0, 0.94, 1), 4: (0, 0.91, 0.1), 5: (1, 0.6, 0), 6: (1, 0, 0), 7: (0.7, 0, 0)}
EXAMPLE_SUBJECT = 12  # dataset S12 = original recording 14 ("participant 14" of Fig. 3A, if the paper used original numbers)


def bh_fdr(p):
    p = np.asarray(p, dtype=float)
    m = p.size
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return out


def rm_anova(data):
    """One-way repeated-measures ANOVA, data (n_subjects, k). Returns F, df1, df2, p, GG-epsilon, p_GG."""
    n, k = data.shape
    grand = data.mean()
    ss_cond = n * ((data.mean(0) - grand) ** 2).sum()
    ss_subj = k * ((data.mean(1) - grand) ** 2).sum()
    ss_tot = ((data - grand) ** 2).sum()
    ss_err = ss_tot - ss_cond - ss_subj
    df1, df2 = k - 1, (k - 1) * (n - 1)
    F = (ss_cond / df1) / (ss_err / df2)
    p = stats.f.sf(F, df1, df2)
    # Greenhouse-Geisser epsilon
    S = np.cov(data, rowvar=False)
    mean_all = S.mean(); row_means = S.mean(axis=1); diag_mean = np.trace(S) / k
    num = (k * (diag_mean - mean_all)) ** 2
    den = (k - 1) * ((S ** 2).sum() - 2 * k * (row_means ** 2).sum() + k ** 2 * mean_all ** 2)
    eps = num / den if den > 0 else 1.0
    eps = float(np.clip(eps, 1.0 / (k - 1), 1.0))
    p_gg = stats.f.sf(F, df1 * eps, df2 * eps)
    return F, df1, df2, p, eps, p_gg


def load_session(session):
    data = {}
    for s in SUBJECTS:
        z = load_preds(s, session)
        data[s] = z
    return data


def per_subject_profiles(data, session):
    """Time courses per subject: mean and SD by level (filtered 10 Hz), and unfiltered window profiles."""
    tc_mean, tc_sd, win_mean, win_sd, win_trials = {}, {}, {}, {}, {}
    time_ms = None
    for s, z in data.items():
        preds, snr, t = z["preds"], z["snr"], z["time"]
        time_ms = 1000 * t
        fp = lowpass_filtfilt(preds)
        levels = np.unique(snr)
        tc_mean[s] = {lv: fp[snr == lv].mean(0) for lv in levels}
        tc_sd[s] = {lv: fp[snr == lv].std(0, ddof=1) for lv in levels}
        wm, wsd, wt = {}, {}, {}
        for i in range(len(ARTICLE_WINDOWS) - 1):
            sel = (time_ms > ARTICLE_WINDOWS[i]) & (time_ms <= ARTICLE_WINDOWS[i + 1])
            v = preds[:, sel].mean(1)  # unfiltered, per trial
            wm[i] = {lv: v[snr == lv].mean() for lv in levels}
            wsd[i] = {lv: v[snr == lv].std(ddof=1) for lv in levels}
            wt[i] = {lv: v[snr == lv] for lv in levels}
        win_mean[s], win_sd[s], win_trials[s] = wm, wsd, wt
    return time_ms, tc_mean, tc_sd, win_mean, win_sd, win_trials


def behaviour(data):
    """Per subject per level: mean/SD/median audibility and identification accuracy (retained trials)."""
    rows = []
    for s, z in data.items():
        ti, snr = z["trialinfo"], z["snr"]
        for lv in np.unique(snr):
            a = ti[snr == lv, COL_AUDIB]
            rows.append(dict(subject=s, level=int(lv), n=len(a), mean_audib=a.mean(), sd_audib=a.std(ddof=1),
                             median_audib=np.median(a), p_heard30=np.mean(a >= 3),
                             accuracy=ti[snr == lv, COL_EVAL].mean()))
    return pd.DataFrame(rows)


def main(session):
    os.makedirs(FIG_DIR, exist_ok=True)
    data = load_session(session)
    time_ms, tc_mean, tc_sd, win_mean, win_sd, win_trials = per_subject_profiles(data, session)
    subs = sorted(data)
    n = len(subs)
    max_levels = {s: int(data[s]["snr"].max()) for s in subs}
    levels_all = sorted(set().union(*[set(tc_mean[s]) for s in subs]))
    beh = behaviour(data)
    beh.to_csv(os.path.join(RESULTS_DIR, f"behaviour_{session}.csv"), index=False, float_format="%.5g")

    # ------------------------------------------------------------------ time courses (group)
    rows = []
    for lv in levels_all:
        have = [s for s in subs if lv in tc_mean[s]]
        M = np.array([tc_mean[s][lv] for s in have])
        S = np.array([tc_sd[s][lv] for s in have])
        Sb = np.array([tc_sd[s][lv] - tc_sd[s][1] for s in have])
        V = np.array([tc_sd[s][lv] ** 2 for s in have])
        for i, tt in enumerate(time_ms):
            rows.append(dict(t_ms=tt, level=lv, n=len(have), mean=M[:, i].mean(), mean_sem=M[:, i].std(ddof=1) / np.sqrt(len(have)),
                             sd=S[:, i].mean(), sd_sem=S[:, i].std(ddof=1) / np.sqrt(len(have)),
                             sd_base=Sb[:, i].mean(), sd_base_sem=Sb[:, i].std(ddof=1) / np.sqrt(len(have)),
                             var=V[:, i].mean()))
    tc = pd.DataFrame(rows)
    tc.to_csv(os.path.join(FIG_DIR, f"fig_a_timecourse_{session}.csv"), index=False, float_format="%.5g")

    # ------------------------------------------------------------------ window profiles (group + example)
    rows = []
    for i in range(len(ARTICLE_WINDOWS) - 1):
        for lv in levels_all:
            have = [s for s in subs if lv in win_mean[s][i]]
            m = np.array([win_mean[s][i][lv] for s in have])
            sd = np.array([win_sd[s][i][lv] for s in have])
            sdb = np.array([win_sd[s][i][lv] - win_sd[s][i][1] for s in have])
            rows.append(dict(window=f"{ARTICLE_WINDOWS[i]}-{ARTICLE_WINDOWS[i+1]}", level=lv, n=len(have),
                             mean=m.mean(), mean_sem=m.std(ddof=1) / np.sqrt(len(have)),
                             sd=sd.mean(), sd_sem=sd.std(ddof=1) / np.sqrt(len(have)),
                             sd_base=sdb.mean(), sd_base_sem=sdb.std(ddof=1) / np.sqrt(len(have)),
                             example_mean=win_mean[EXAMPLE_SUBJECT][i].get(lv, np.nan),
                             example_sd=win_sd[EXAMPLE_SUBJECT][i].get(lv, np.nan),
                             example_sd_base=win_sd[EXAMPLE_SUBJECT][i].get(lv, np.nan) - win_sd[EXAMPLE_SUBJECT][i][1]))
    wp = pd.DataFrame(rows)
    wp.to_csv(os.path.join(FIG_DIR, f"fig_a_window_profiles_{session}.csv"), index=False, float_format="%.5g")

    # ------------------------------------------------------------------ stats per window
    srows = []
    beh_p = beh.pivot(index="subject", columns="level", values="sd_audib")
    beh_m = beh.pivot(index="subject", columns="level", values="mean_audib")
    for i in range(len(ARTICLE_WINDOWS) - 1):
        lvls = [2, 3, 4, 5, 6]  # the MATLAB uses levels 2:6 for every subject (7 exists only in passive S11-20)
        M = np.array([[win_mean[s][i][lv] for lv in lvls] for s in subs])
        SDb = np.array([[win_sd[s][i][lv] - win_sd[s][i][1] for lv in lvls] for s in subs])
        SD = np.array([[win_sd[s][i][lv] for lv in lvls] for s in subs])
        row = dict(window=f"{ARTICLE_WINDOWS[i]}-{ARTICLE_WINDOWS[i+1]}")
        for name, D in [("mean", M), ("mean_diff", np.diff(M, axis=1)), ("sdbase", SDb), ("sdbase_diff", np.diff(SDb, axis=1))]:
            F, df1, df2, p, eps, pgg = rm_anova(D)
            row[f"anova_{name}_F"], row[f"anova_{name}_df1"], row[f"anova_{name}_df2"] = F, df1, df2
            row[f"anova_{name}_p"], row[f"anova_{name}_eps"], row[f"anova_{name}_pGG"] = p, eps, pgg
        # peak of the group SD_base profile
        row["sdbase_peak_level"] = lvls[int(np.argmax(SDb.mean(0)))]
        row["sdbase_peak_level_median_subjects"] = float(np.median([lvls[int(np.argmax(r))] for r in SDb]))
        if session == "active":
            X = beh_p.loc[subs, lvls].to_numpy()
            R = np.array([stats.pearsonr(X[j], SD[j])[0] for j in range(n)])
            t, p = stats.ttest_1samp(R, 0.0)
            row.update(corr_sd_t=t, corr_sd_p=p, corr_sd_mean_r=R.mean(), corr_sd_cohen_d=R.mean() / R.std(ddof=1))
            Xm = beh_m.loc[subs, [1] + lvls].to_numpy()
            Mm = np.array([[win_mean[s][i][lv] for lv in [1] + lvls] for s in subs])
            Rm = np.array([stats.pearsonr(Xm[j], Mm[j])[0] for j in range(n)])
            t, p = stats.ttest_1samp(Rm, 0.0)
            row.update(corr_mean_t=t, corr_mean_p=p, corr_mean_mean_r=Rm.mean(), corr_mean_cohen_d=Rm.mean() / Rm.std(ddof=1))
        srows.append(row)
    st = pd.DataFrame(srows)
    for c in [c for c in st.columns if c.endswith("_p") and not c.endswith("_pGG")]:
        st[c + "_fdr"] = bh_fdr(st[c].to_numpy())
    st.to_csv(os.path.join(RESULTS_DIR, f"stats_{session}.csv"), index=False, float_format="%.4g")

    # ------------------------------------------------------------------ continuous neuro-behavioural correlation (Fig. 3D)
    if session == "active":
        lvls = [2, 3, 4, 5, 6]
        X = beh_p.loc[subs, lvls].to_numpy(); Xm = beh_m.loc[subs, [1] + lvls].to_numpy()
        Rsd = np.zeros((n, len(time_ms))); Rm = np.zeros((n, len(time_ms)))
        for j, s in enumerate(subs):
            SDt = np.array([tc_sd[s][lv] for lv in lvls])          # (5, T) raw SD
            Mt = np.array([tc_mean[s][lv] for lv in [1] + lvls])   # (6, T)
            xs = (X[j] - X[j].mean()) / X[j].std(); xm = (Xm[j] - Xm[j].mean()) / Xm[j].std()
            Zs = (SDt - SDt.mean(0)) / SDt.std(0); Zm = (Mt - Mt.mean(0)) / Mt.std(0)
            Rsd[j] = (xs[:, None] * Zs).mean(0); Rm[j] = (xm[:, None] * Zm).mean(0)
        t_sd, p_sd = stats.ttest_1samp(Rsd, 0.0, alternative="greater")
        t_m, p_m = stats.ttest_1samp(Rm, 0.0, alternative="greater")
        ct = pd.DataFrame(dict(t_ms=time_ms, r_sd_mean=Rsd.mean(0), r_sd_sem=Rsd.std(0, ddof=1) / np.sqrt(n), t_sd=t_sd,
                               p_sd=p_sd, p_sd_fdr=bh_fdr(p_sd), r_mean_mean=Rm.mean(0), r_mean_sem=Rm.std(0, ddof=1) / np.sqrt(n),
                               t_mean=t_m, p_mean=p_m, p_mean_fdr=bh_fdr(p_m)))
        ct.to_csv(os.path.join(RESULTS_DIR, f"stats_timecourse_{session}.csv"), index=False, float_format="%.4g")
        fig, ax = plt.subplots(figsize=(9, 3.8))
        for col, lab, c in [("r_mean", "mean profile", "b"), ("r_sd", "variability profile", "r")]:
            ax.plot(time_ms, ct[f"{col}_mean"], color=c, label=lab)
            ax.fill_between(time_ms, ct[f"{col}_mean"] - ct[f"{col}_sem"], ct[f"{col}_mean"] + ct[f"{col}_sem"], color=c, alpha=0.2)
            sig = ct[f"p{col[1:]}_fdr"].to_numpy() < 0.05
            ax.plot(time_ms[sig], np.full(sig.sum(), -0.55 if col == "r_mean" else -0.62), "s", color=c, ms=3)
        ax.axhline(0, color="k", lw=0.8); ax.axvline(0, color="k", lw=0.8)
        ax.set_xlim(-300, 1500); ax.set_ylim(-0.7, 1.0)
        ax.set_xlabel("Time (ms)"); ax.set_ylabel("Correlation neural vs audibility profile")
        ax.set_title("Neuro-behavioural correlation, active (Fig. 3D style; squares = p-FDR < 0.05, one-sided)")
        ax.legend(frameon=False, loc="upper right")
        fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, f"fig_d_neurobehav_corr_{session}.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------------ figure (a): window profiles, group + example
    nw = len(ARTICLE_WINDOWS) - 1
    for who, tag in [("group", ""), ("example", f"_S{EXAMPLE_SUBJECT}")]:
        fig, axes = plt.subplots(2, nw, figsize=(2.3 * nw, 5.2), sharex=True)
        for i in range(nw):
            wlab = f"{ARTICLE_WINDOWS[i]}-{ARTICLE_WINDOWS[i+1]}"
            d = wp[wp.window == wlab].set_index("level")
            lv = [l for l in d.index if l >= 2]
            if who == "group":
                m, ms, sdb, sds = d.loc[lv, "mean"], d.loc[lv, "mean_sem"], d.loc[lv, "sd_base"], d.loc[lv, "sd_base_sem"]
                m0 = d.loc[1, "mean"]
            else:
                m, ms, sdb, sds = d.loc[lv, "example_mean"], 0 * d.loc[lv, "mean_sem"], d.loc[lv, "example_sd_base"], 0 * d.loc[lv, "sd_base_sem"]
                m0 = d.loc[1, "example_mean"]
            ax = axes[0, i]
            ax.errorbar(lv, m, yerr=ms, fmt="k.-", lw=2, ms=10)
            ax.axhline(0, color="k", lw=0.8); ax.axhline(m0, color="k", ls="--", lw=0.8)
            ax.set_title(f"{wlab} ms", fontsize=10)
            ax = axes[1, i]
            ax.errorbar(lv, sdb, yerr=sds, fmt="k.-", lw=2, ms=10)
            ax.axhline(0, color="k", ls="--", lw=0.8)
            ax.set_xticks(lv); ax.set_xticklabels([SNR_DB_MAIN[l] for l in lv], fontsize=8)
        axes[0, 0].set_ylabel("mean projected activity"); axes[1, 0].set_ylabel("SD across trials\n(minus no-sound SD)")
        fig.suptitle(f"Projected activity by SNR, {session} session, "
                     + (f"group mean ± SEM (n = {n})" if who == "group" else f"example dataset S{EXAMPLE_SUBJECT} (orig. no. 14)")
                     + " — diagonal decoder, window-averaged (Fig. 2C style)")
        fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, f"fig_a_window_profiles_{session}{tag}.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------------ figure (a)+(c): time courses
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for lv in levels_all:
        d = tc[tc.level == lv]
        c = LEVEL_COLORS[lv]
        lab = f"level {lv} ({SNR_DB_MAIN[lv]} dB)" if lv > 1 else "no sound"
        axes[0].plot(d.t_ms, d["mean"], color=c, label=lab)
        axes[0].fill_between(d.t_ms, d["mean"] - d.mean_sem, d["mean"] + d.mean_sem, color=c, alpha=0.15)
        axes[1].plot(d.t_ms, d["sd"], color=c, label=lab)
        if lv > 1:
            axes[2].plot(d.t_ms, d.sd_base, color=c, label=lab)
            axes[2].fill_between(d.t_ms, d.sd_base - d.sd_base_sem, d.sd_base + d.sd_base_sem, color=c, alpha=0.15)
    for ax in axes:
        ax.axvline(0, color="k", lw=0.8); ax.axhline(0, color="k", lw=0.5)
    axes[0].set_ylabel("mean projected activity"); axes[1].set_ylabel("SD across trials"); axes[2].set_ylabel("SD minus no-sound SD")
    axes[2].set_xlabel("Time from stimulus onset (ms)"); axes[0].legend(frameon=False, ncol=4, fontsize=8)
    axes[0].set_title(f"Group ({n} subjects) time courses of the projected activity by SNR, {session} (10 Hz low-pass)")
    axes[2].set_xlim(-300, 1500)
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, f"fig_a_timecourse_{session}.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------------ figure (c): variance burst heat map + peak level
    lv2 = [l for l in levels_all if l >= 2]
    H = np.array([tc[tc.level == lv].sd_base.to_numpy() for lv in lv2])
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
    im = axes[0].imshow(H, aspect="auto", origin="lower", extent=[time_ms[0], time_ms[-1], lv2[0] - 0.5, lv2[-1] + 0.5],
                        cmap="magma", vmin=0, vmax=np.nanpercentile(H, 99))
    axes[0].set_yticks(lv2); axes[0].set_yticklabels([f"{SNR_DB_MAIN[l]} dB" for l in lv2])
    axes[0].set_ylabel("SNR level"); axes[0].set_title(f"Across-trial variability of the projected activity (SD minus no-sound SD), group, {session}")
    plt.colorbar(im, ax=axes[0], label="SD - SD(no sound)")
    peak = np.array(lv2)[np.argmax(H, axis=0)]
    tot = H.max(axis=0)
    axes[1].plot(time_ms, peak, "k.", ms=3)
    axes[1].set_yticks(lv2); axes[1].set_yticklabels([SNR_DB_MAIN[l] for l in lv2]); axes[1].set_ylabel("level of max SD")
    axes[1].axvline(0, color="k", lw=0.8); axes[1].set_xlabel("Time from stimulus onset (ms)"); axes[1].set_xlim(-300, 1500)
    ax2 = axes[1].twinx(); ax2.plot(time_ms, tot, color="r", lw=1); ax2.set_ylabel("max SD_base", color="r")
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, f"fig_c_variance_burst_{session}.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------------ distributions, example subject, 400-500 ms (Fig. 3A style)
    i = ARTICLE_WINDOWS.index(400)
    trials = win_trials[EXAMPLE_SUBJECT][i]
    fig, axes = plt.subplots(1, len(trials), figsize=(2.4 * len(trials), 3), sharex=True, sharey=True)
    allv = np.concatenate(list(trials.values()))
    bins = np.linspace(np.percentile(allv, 0.5), np.percentile(allv, 99.5), 30)
    for ax, (lv, v) in zip(axes, sorted(trials.items())):
        ax.hist(v, bins=bins, color=LEVEL_COLORS[lv], alpha=0.8)
        ax.set_title("no sound" if lv == 1 else f"{SNR_DB_MAIN[lv]} dB", fontsize=9)
    axes[0].set_ylabel("trials"); fig.suptitle(f"Dataset S{EXAMPLE_SUBJECT}, 400-500 ms window-averaged projected activity by SNR ({session})", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, f"fig_dist_example_S{EXAMPLE_SUBJECT}_{session}.png"), dpi=150); plt.close(fig)
    pd.DataFrame({f"level{lv}": pd.Series(v) for lv, v in trials.items()}).to_csv(
        os.path.join(FIG_DIR, f"fig_dist_example_S{EXAMPLE_SUBJECT}_{session}.csv"), index=False, float_format="%.5g")

    # ------------------------------------------------------------------ behaviour figure (active): Fig. 1D style
    if session == "active":
        g = beh.groupby("level")
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
        for ax, col, lab in zip(axes, ["accuracy", "mean_audib", "sd_audib"], ["identification accuracy", "mean audibility (0-10)", "SD of audibility"]):
            for s in subs:
                d = beh[beh.subject == s].sort_values("level")
                ax.plot(d.level, d[col], color="0.7", lw=0.7)
            ax.errorbar(g[col].mean().index, g[col].mean(), yerr=g[col].std(ddof=1) / np.sqrt(n), fmt="k.-", lw=2, ms=8)
            ax.set_xticks(range(1, 7)); ax.set_xticklabels(["N", "-13", "-11", "-9", "-7", "-5"]); ax.set_title(lab, fontsize=10)
        fig.suptitle("Behaviour, active session (retained trials, from trialinfo)", fontsize=10)
        fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "fig_behaviour_active.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------------ console summary
    pd.set_option("display.width", 250)
    print(f"=== {session}: window profiles (group)")
    print(wp.pivot(index="window", columns="level", values="mean").round(3).loc[[f"{a}-{b}" for a, b in zip(ARTICLE_WINDOWS[:-1], ARTICLE_WINDOWS[1:])]])
    print("SD minus no-sound SD:")
    print(wp.pivot(index="window", columns="level", values="sd_base").round(3).loc[[f"{a}-{b}" for a, b in zip(ARTICLE_WINDOWS[:-1], ARTICLE_WINDOWS[1:])]])
    cols = ["window", "anova_mean_diff_F", "anova_mean_diff_p_fdr", "anova_mean_F", "anova_mean_p_fdr", "anova_sdbase_F",
            "anova_sdbase_p_fdr", "anova_sdbase_diff_F", "anova_sdbase_diff_p_fdr", "sdbase_peak_level"]
    if session == "active":
        cols += ["corr_sd_t", "corr_sd_p_fdr", "corr_sd_cohen_d", "corr_mean_t", "corr_mean_p_fdr"]
    print(st[cols].round(4).to_string(index=False))
    if session == "active":
        print("behaviour group means:")
        print(beh.groupby("level")[["accuracy", "mean_audib", "sd_audib", "median_audib", "p_heard30"]].mean().round(3))
        print("SD-of-audibility peak level per subject:", beh.pivot(index="subject", columns="level", values="sd_audib").loc[:, 2:6].idxmax(axis=1).tolist())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=None, help="active | passive | (default: both that exist)")
    a = ap.parse_args()
    sessions = [a.session] if a.session else ["active", "passive"]
    for s in sessions:
        try:
            main(s)
        except FileNotFoundError as e:
            print(f"{s}: skipped ({e})")

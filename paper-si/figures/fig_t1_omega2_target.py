"""T1 simulation audit, the hardest null (M2S, concept random scale omega = 2) -> t1_omega2_target.pdf.

Reads t1_omega2_bank_data.csv: the selection-predictor point estimate and 95 % concept-cluster interval of
(i) the 1,000 calibration datasets of run d4v12b at omega = 2 and (ii) the independent reference bank
ref_m2s_omega2_aac9f69 (1,000 datasets, same procedure and generator, seed 2028), both at D = 4, one layer.
Written by ~/Recoverable-Self-Coding/workspace_demo/t1_access/reviews/t1_omega2_bank_2026-09-15/omega2_target_check.py
from the saved rows (no fits). Three panels:
(a) the bank's 1,000 point estimates sorted by size, magnitude on a log axis (all are negative, i.e. toward
    graded), with the bank mean, the mean without its single most extreme dataset, and the median;
(b) the fraction of the d4v12b intervals that contain each candidate reference value, against the 0.90 floor;
(c) the bank mean with two standard errors after removing its k most extreme datasets.
Development evidence under the old eight-start procedure; it validates no interval.
Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python fig_t1_omega2_target.py
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "t1_omega2_bank_data.csv"), newline="")))
get = lambda src, key: np.array([float(r[key]) for r in rows if r["source"] == src])
bank = get("bank", "point")
d4_point, d4_lo, d4_hi = get("d4v12b", "point"), get("d4v12b", "lo"), get("d4v12b", "hi")
assert bank.size == 1000 and d4_point.size == 1000
assert np.all(bank < 0), "panel (a) plots magnitudes on a log axis and needs every estimate below zero"

srt = np.sort(bank)                                   # most negative first
mean_all, mean_loo, median = bank.mean(), srt[1:].mean(), np.median(bank)
targets = [("bank\nmedian", median), ("bank mean\nwithout 1", mean_loo), ("d4v12b\nmean", d4_point.mean()),
           ("bank\nmean", mean_all)]
cover = [np.mean((d4_lo <= v) & (v <= d4_hi)) for _, v in targets]
ks = [0, 1, 2, 5, 10, 20, 50]
km = [srt[k:].mean() for k in ks]
kse = [srt[k:].std(ddof=1) / np.sqrt(srt[k:].size) for k in ks]

INK, MUTED, DATA = "#222222", "#6b6b6b", "#4c72b0"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED})
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.6), constrained_layout=True)

ax = axes[0]
rank = np.arange(1, bank.size + 1)
ax.plot(rank, -srt, color=DATA, lw=1.6)
ax.set_xscale("log"); ax.set_yscale("log")
for val, style, text, dy in ((mean_all, "--", f"mean {mean_all:.2f}", 1.10), (mean_loo, "-.", f"without 1: {mean_loo:.2f}", 0.80),
                             (median, ":", f"median {median:.2f}", 0.80)):
    ax.axhline(-val, color=INK, lw=0.8, ls=style)
    ax.text(1.15, -val * dy, text, ha="left", va="bottom" if dy > 1 else "top", fontsize=6.3, color=INK)
ax.annotate(f"one dataset at {srt[0]:,.0f}", xy=(1, -srt[0]), xytext=(2.4, -srt[0] * 0.5), fontsize=6.3, color=INK,
            arrowprops=dict(arrowstyle="-", lw=0.6, color=MUTED))
ax.set_xlabel("rank (most negative first)")
ax.set_ylabel(r"$-\bar\Delta$ (nat per trial)")
ax.set_title("(a) Bank estimates, sorted", loc="left")
ax.grid(True, which="major", color="#e6e6e6", lw=0.5)

ax = axes[1]
x = np.arange(len(targets))
ax.bar(x, cover, color=DATA, width=0.62)
for xi, c in zip(x, cover):
    ax.text(xi, c + 0.02, f"{c:.2f}", ha="center", va="bottom", fontsize=6.5, color=INK)
# No 0.90 floor on this panel: it is the audit threshold for the interval's own estimand, the replicate mean, and
# drawing it across the median and the trimmed mean invites reading those as failed coverage of quantities the
# interval never targeted (Codex record c4abb4f, correcting 226024e).
ax.set_xticks(x, [t for t, _ in targets])
ax.set_ylim(0, 1.05)
ax.set_ylabel("d4v12b intervals containing it")
ax.set_title("(b) Inclusion by candidate reference", loc="left")
ax.grid(True, axis="y", color="#e6e6e6", lw=0.5)

ax = axes[2]
xk = np.arange(len(ks))
ax.errorbar(xk, km, yerr=2 * np.array(kse), fmt="o", color=DATA, ms=4, capsize=2, lw=1.2)
ax.axhline(median, color=INK, lw=0.8, ls=":")
ax.text(len(ks) - 1, median + 0.25, "median", ha="right", va="bottom", fontsize=6.3, color=INK)
ax.set_xticks(xk, [str(k) for k in ks])
ax.set_xlabel("extreme datasets removed, $k$")
ax.set_ylabel(r"bank mean $\pm$ 2 SE (nat per trial)")
ax.set_title("(c) Mean without the tail", loc="left")
ax.grid(True, axis="y", color="#e6e6e6", lw=0.5)

fig.savefig(os.path.join(HERE, "t1_omega2_target.pdf"))
print(dict(mean_all=round(mean_all, 3), mean_loo=round(mean_loo, 3), median=round(median, 3),
           coverage={t.replace(chr(10), " "): round(c, 3) for (t, _), c in zip(targets, cover)},
           leave_k=[(k, round(m, 3), round(s, 3)) for k, m, s in zip(ks, km, kse)], bank_max=round(bank.max(), 4)))

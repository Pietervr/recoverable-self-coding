"""What an unassessed substrate transfer costs -> t1_transfer.pdf.

The three panels are the measured consequence of carrying a competing-model comparison to a second
substrate without assessing its predictors, its sampling unit, its uncertainty target and its decision rule.
Every dataset behind them is GRADED BY CONSTRUCTION, so a mixture call is false with respect to the
generating family.

Data, both post hoc aggregations of the same saved rows of run d4v12b (12,000 datasets, D = 4, one layer;
calibration_D4.csv, SHA-256 7762f152...babb), no refitting:
  t1_transfer_data.csv         per-generator decisions of the carried-over predictor pair and of the
                               transfer-assessed procedure (RSC reviews/t1_historical_pair_2026-09-16)
  t1_calibration_D4_summary.csv  the inclusion rate of the nominal 95 % concept-cluster interval for the
                               procedure's own replicate mean, an estimated reference

Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python fig_t1_transfer.py
"""
import csv, json, os
import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "t1_transfer_data.csv"), newline="") as f:
    rows = list(csv.DictReader(f))
with open(os.path.join(HERE, "t1_calibration_D4_summary.csv"), newline="") as f:
    cal = list(csv.DictReader(f))

SYM = {"tau": r"$\tau$", "omega": r"$\omega$", "alpha": r"$\alpha$"}
def label(row):
    g = json.loads(row["grid"]) if row["grid"] else {}
    if not g:
        return "base"
    (k, v), = g.items()
    return f"{SYM[k]}={float(v):g}"

labels = [label(r) for r in rows]
col = lambda rs, name: np.array([float(r[name]) for r in rs])
n = col(rows, "n")
hist = {k: col(rows, f"historical_{k}") for k in ("graded", "inconclusive", "mixture")}
sel = {k: col(rows, f"selection_{k}") for k in ("graded", "inconclusive", "mixture")}
incl = col(cal, "coverage")

G, I, M = "#55a868", "#bfbfbf", "#c44e52"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 7, "legend.fontsize": 6.8})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), constrained_layout=True)

# (a) all 12,000 datasets, the two procedures side by side
ax = axes[0]
tot = {k: (hist[k].sum(), sel[k].sum()) for k in hist}
xs = [0, 1]
bot = np.zeros(2)
handles = []
for k, c, nm in (("graded", G, "Graded support"), ("inconclusive", I, "Inconclusive"), ("mixture", M, "Mixture support")):
    v = np.array(tot[k], dtype=float)
    h = ax.bar(xs, v, 0.55, bottom=bot, color=c, label=nm, edgecolor="white", linewidth=0.5)
    handles.append(h)
    bot += v
ax.set_xticks(xs)
ax.set_xticklabels(["Inherited\npair", "Expanded\nfamilies"], linespacing=1.3)
ax.set_ylabel("Datasets (of 12,000)")
ax.set_title("(a) Predictor decisions", loc="left")
ax.annotate(f"{int(tot['mixture'][0])} mixture\ncalls", xy=(0.3, 11500), xytext=(0.62, 12900),
            fontsize=6.8, ha="center", color=M,
            arrowprops=dict(arrowstyle="->", color=M, lw=0.8))
ax.annotate("0 mixture\ncalls", xy=(1, 12200), ha="center", fontsize=6.8, color=G)
ax.set_ylim(0, 14600)

# (b) where the false calls sit, for the carried-over pair
ax = axes[1]
x = np.arange(len(rows))
rate = hist["mixture"] / n
ax.bar(x, rate, 0.62, color=[M if r > 0 else "#dddddd" for r in rate])
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=60, ha="right")
ax.set_ylabel("Mixture-call frequency")
ax.set_title("(b) Inherited-pair calls", loc="left")
ax.set_ylim(0, 0.88)
for xi, r in zip(x, rate):
    if r > 0:
        ax.annotate(f"{r:.3f}", xy=(xi, r), xytext=(0, 2.5), textcoords="offset points",
                    ha="center", fontsize=6.3, color=M)
ax.annotate("heterogeneity omitted from\nboth carried-over predictors", xy=(4, 0.70), xytext=(8.4, 0.80),
            fontsize=6.0, ha="center", va="center", color="#444444",
            arrowprops=dict(arrowstyle="->", color="#888888", lw=0.7))

# (c) the interval, for the assessed procedure
ax = axes[2]
ax.bar(x, incl, 0.62, color=["#4c72b0" if c >= 0.90 else "#dd8452" for c in incl])
ax.axhline(0.95, color="#333333", lw=0.9, ls="--")
ax.axhline(0.90, color="#888888", lw=0.8, ls=":")
ax.annotate("nominal level 0.95", xy=(-0.45, 0.955), ha="left", va="bottom", fontsize=6.3)
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=60, ha="right")
ax.set_ylabel("Interval inclusion rate")
ax.set_title("(c) Reference inclusion", loc="left")
ax.set_ylim(0, 1.13)
ax.annotate(f"{incl.min():.3f}", xy=(int(np.argmin(incl)), incl.min()), xytext=(0, 3),
            textcoords="offset points", ha="center", fontsize=6.3, color="#dd8452")

fig.legend(handles=[h for h in handles], loc="outside lower center", ncol=3, frameon=False,
           title="Decisions in panel (a):", title_fontsize=6.8, alignment="center")

fig.savefig(os.path.join(HERE, "t1_transfer.pdf"))
print("wrote t1_transfer.pdf")
print(f"  carried over: {int(tot['graded'][0])} G / {int(tot['inconclusive'][0])} I / {int(tot['mixture'][0])} M")
print(f"  assessed:     {int(tot['graded'][1])} G / {int(tot['inconclusive'][1])} I / {int(tot['mixture'][1])} M")
print(f"  inclusion below the 0.90 floor: {int((incl < 0.90).sum())} of {len(incl)}, min {incl.min():.3f}")

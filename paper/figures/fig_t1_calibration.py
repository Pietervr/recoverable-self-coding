"""T1 simulation audit, calibration stage (run d4v12b, D = 4, 1,000 datasets per null) -> t1_calibration_D4.pdf.

Reads t1_calibration_D4_summary.csv, the per-generator summary written by simulate.summarize() on
~/Recoverable-Self-Coding/workspace_demo/t1_access/sim_results/d4v12b/calibration_D4.csv (12,000 rows; file
SHA-256 7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb; the run's stored analysis hash is
b29215469af9), plus the column rms_se = sqrt(mean(claimed SE^2)) per null added from the same rows. Three panels:
(a) the observed false-positive frequency of the decision rule under each graded null against the 0.064 ceiling
(0/1,000 everywhere; one-sided exact 95 % upper bound 0.003 per setting); (b) the coverage of the nominal 95 %
concept-cluster interval for the procedure-level target theta_g against the 0.90 floor; (c) the replicate SD of
the band-mean statistic beside the RMS and the mean of the claimed SEs — a description of the interval-width
distribution, not a diagnosis of the coverage failure's cause (Codex review 13 Sept, finding 5).
Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python fig_t1_calibration.py
"""
import csv, json, os
import numpy as np
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "t1_calibration_D4_summary.csv"), newline="") as f:
    rows = list(csv.DictReader(f))
SYM = {"tau": r"$\tau$", "omega": r"$\omega$", "alpha": r"$\alpha$"}

def label(row):
    g = json.loads(row["grid"]) if row["grid"] else {}
    if not g:
        return "base"
    (k, v), = g.items()
    return f"{SYM[k]}={float(v):g}"

labels = [label(r) for r in rows]
col = lambda name: np.array([float(r[name]) for r in rows])
n = col("n")
fpr = col("mixture")
cov = col("coverage")
sd_point, mean_se, rms_se = col("sd_point"), col("mean_se"), col("rms_se")
fpr_se = np.sqrt(fpr * (1 - fpr) / n)
cov_se = np.sqrt(cov * (1 - cov) / n)
x = np.arange(len(rows))
fam_col = ["#4c72b0" if r["generator"] == "M2B" else "#55a868" if r["generator"] == "M2H" else "#c44e52" if r["generator"] == "M2K" else "#8172b2" for r in rows]

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 6.5, "ytick.labelsize": 7})
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.55), constrained_layout=True)

ax = axes[0]
ax.bar(x, fpr, yerr=2 * fpr_se, color=fam_col, width=0.7, capsize=1.5)
ax.axhline(0.064, color="k", lw=0.8, ls="--")
ax.text(len(rows) - 0.4, 0.067, "ceiling 0.064", ha="right", va="bottom", fontsize=6.5)
ax.axhline(0.05, color="0.5", lw=0.6, ls=":")
ax.set_ylim(0, 0.10)
ax.set_ylabel("false-positive rate")
ax.set_title("(a) rule says “mixture” under a graded null")

ax = axes[1]
ax.bar(x, cov, yerr=2 * cov_se, color=fam_col, width=0.7, capsize=1.5)
ax.axhline(0.90, color="k", lw=0.8, ls="--")
ax.axhline(0.95, color="0.5", lw=0.6, ls=":")
ax.set_ylim(0, 1.0)
ax.set_ylabel(r"coverage of $\theta_g$ (nominal 0.95)")
ax.set_title("(b) concept-cluster interval")

ax = axes[2]
w = 0.27
ax.bar(x - w, sd_point, width=w, color="0.15", label="replicate SD of the statistic")
ax.bar(x, rms_se, width=w, color="0.55", label="RMS of the claimed SEs")
ax.bar(x + w, mean_se, width=w, color="0.85", edgecolor="0.4", lw=0.4, label="mean of the claimed SEs")
ax.set_yscale("log")
ax.set_ylabel("nat per trial")
ax.set_title("(c) replicate SD vs claimed SEs")
ax.legend(loc="upper left", fontsize=6, frameon=False, handlelength=1.0, borderaxespad=0.2)

from matplotlib.patches import Patch
axes[0].legend(handles=[Patch(color="#4c72b0", label="M2B base"), Patch(color="#55a868", label=r"M2H threshold effect $\tau$"),
                        Patch(color="#c44e52", label=r"M2K skew $\alpha$"), Patch(color="#8172b2", label=r"M2S scale effect $\omega$")],
               loc="upper left", fontsize=6, frameon=False, handlelength=1.0, borderaxespad=0.2)
for ax in axes:
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90)
    ax.tick_params(axis="x", length=0, pad=1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

out = os.path.join(HERE, "t1_calibration_D4.pdf")
fig.savefig(out)
print("wrote", out)
for l, f, c, s, r, m in zip(labels, fpr, cov, sd_point, rms_se, mean_se):
    print(f"{l:8s} FPR {f:.3f}  coverage {c:.3f}  SD {s:.5f}  RMS SE {r:.5f}  mean SE {m:.5f}  SD/RMS {s / r:.3f}  SD/mean {s / m:.2f}")

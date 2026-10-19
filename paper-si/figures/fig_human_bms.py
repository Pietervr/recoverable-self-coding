"""Human model comparison reproduced (Sergent et al. 2021, open EEG data of 20 participants) -> human_bms.pdf.

Reads the port's per-window group model-selection tables in
~/Recoverable-Self-Coding/workspace_demo/sergent_port/figures/ (run 11 Sept 2026; RESULTS_sergent.md C6-C7):
  fig_b_pxp_published_vs_port_active.csv  the port's and the published protected exceedance probabilities; the
                                          published values are the article's Source Data sheet "Figure 3 Panel E"
  fig_b_model_comparison_active.csv       the port's pxp per model and its Simes marks
  fig_b_model_comparison_passive.csv      the same for the passive session (an additional analysis)
simes_sig_matlab_* is the strict '<' step-up set, as the authors' PlotFig script marks windows (port README D7).
Window centre = -285 + 30 i ms (the archived PlotFig convention). Writes the columns used to human_bms_data.csv.
(a) active: null / graded (2B) / two-state (3), port solid, published two-state dashed, 0.95 dotted, the port's Simes
set for the two-state model as dots; (b) passive: the port's three curves (no window passes Simes for any model).
Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python fig_human_bms.py
"""
import csv
import os

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Recoverable-Self-Coding/workspace_demo/sergent_port/figures")
NULL, GRADED, TWO = "#8c8c8c", "#1f77b4", "#d95f02"


def read(name):
    with open(os.path.join(SRC, name), newline="") as fh:
        return list(csv.DictReader(fh))


def col(rows, key):
    return [float(r[key]) for r in rows]


pub = read("fig_b_pxp_published_vs_port_active.csv")
act = read("fig_b_model_comparison_active.csv")
pas = read("fig_b_model_comparison_passive.csv")
t = col(act, "t_ms")
assert len(t) == 53 and col(pub, "t_ms") == t and col(pas, "t_ms") == t
assert max(abs(a - b) for a, b in zip(col(pub, "port_pxp_model3"), col(act, "pxp_model3"))) < 1e-5, "overlay file != port table"
passive_simes = [r for r in pas if "True" in (r["simes_sig_matlab_model0"], r["simes_sig_matlab_model2B"], r["simes_sig_matlab_model3"])]
assert not passive_simes, "a passive window passes Simes: the caption would be wrong"

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
handles = None
for ax, rows, title in ((axes[0], act, "(a) Active session"), (axes[1], pas, "(b) Passive session (additional analysis)")):
    ax.axhline(0.95, color="k", lw=0.6, ls=":")
    h0, = ax.plot(t, col(rows, "pxp_model0"), color=NULL, lw=1.2, label="null")
    h1, = ax.plot(t, col(rows, "pxp_model2B"), color=GRADED, lw=1.2, label="graded")
    h2, = ax.plot(t, col(rows, "pxp_model3"), color=TWO, lw=1.5, label="two-state (port)")
    sig = [ti for ti, r in zip(t, rows) if r["simes_sig_matlab_model3"] == "True"]
    ax.plot(sig, [1.035] * len(sig), "o", color=TWO, ms=2.8, clip_on=False)
    ax.set_title(title, fontsize=8.5, loc="left")
    ax.set_xlim(-300, 1290)
    ax.set_ylim(0, 1.07)
    ax.set_xlabel("window centre (ms)", fontsize=8)
    ax.tick_params(labelsize=7)
    if handles is None:
        handles = [h0, h1, h2]
h3, = axes[0].plot(t, col(pub, "published_pxp_model3"), color="k", lw=1.0, ls="--", label="two-state (published)")
axes[0].set_ylabel("protected exceedance prob.", fontsize=8)
fig.legend(handles + [h3], [h.get_label() for h in handles + [h3]], loc="lower center", ncol=4, fontsize=7, frameon=False)
fig.subplots_adjust(left=0.085, right=0.99, bottom=0.30, top=0.90, wspace=0.07)   # tight_layout squeezed the axes apart
fig.savefig(os.path.join(HERE, "human_bms.pdf"))

with open(os.path.join(HERE, "human_bms_data.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["t_ms", "active_pxp_null", "active_pxp_graded", "active_pxp_two_state", "published_pxp_two_state",
                "active_simes_two_state", "passive_pxp_null", "passive_pxp_graded", "passive_pxp_two_state"])
    for i in range(len(t)):
        w.writerow([t[i], act[i]["pxp_model0"], act[i]["pxp_model2B"], act[i]["pxp_model3"], pub[i]["published_pxp_model3"],
                    act[i]["simes_sig_matlab_model3"], pas[i]["pxp_model0"], pas[i]["pxp_model2B"], pas[i]["pxp_model3"]])
print("wrote human_bms.pdf and human_bms_data.csv")

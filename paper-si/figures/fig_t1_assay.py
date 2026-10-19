"""The Cross-Substrate Access Assay end to end, with both instantiations -> t1_assay.pdf.

Hand-placed block diagram (no auto-layout): centre column is the procedure, left the human instantiation
as calibrated in Section 6.1, right the language-model instantiation as measured by the development pilot (Results 6.4). The five
declared components are tagged where they act. Every cell restates material from the paper; nothing is
computed here.

Run: /Users/pietervanrooyen/Unimog-Projects/papers/ai_dissipative/presentation/.venv/bin/python fig_t1_assay.py
"""
import os
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))

CORE = "#eef2f7"; CORE_E = "#2f4f6f"
HUM = "#eaf3ea"; HUM_E = "#4a7a4a"
MOD = "#fdf0e6"; MOD_E = "#b5713a"
TAG = "#c44e52"

STAGES = [
    ("Stimulus population\ndeclared, randomized dose $k$",
     "Vowel in noise\nsix signal-to-noise levels",
     "Natural-text packets\n0-8 informative clues"),
    ("System under test\n+ declared readout $\\rightarrow$ scalar $y$",
     "20 participants, EEG\ndecoder projection, 30 ms windows",
     "One fixed checkpoint\nfrozen dose decoder per layer"),
    ("1  PREDICTORS\nCompeting families of\nconditional densities",
     "null, graded, two-state\n(three fixed models)",
     "4 graded + 4 mixture members\none of each selected"),
    ("2  FITTING\nFit every member; select\ninside training folds",
     "Nelder-Mead, authors' settings\nfive block folds",
     "multi-start L-BFGS-B\nnested selection"),
    ("3  SAMPLING UNIT\nScore units held out\nof the fit",
     "unit: the participant\nheld-out log-likelihood",
     "unit: the concept\njoint held-out log score"),
    ("Statistic: difference of held-out\ncross-entropies, nats per trial",
     "0.0025-0.003 nat/trial\nat the plateau",
     "$\\Delta_c$, over folds,\nconcepts and layers"),
    ("4  TARGET   5  RULE\nInterval for a NAMED target,\nthen a verdict",
     "exceedance probability,\nno explicit estimand",
     "target $\\theta_g$ named\ninterval under validation"),
    ("Verdict",
     "first crossing 315 ms\nREPRODUCED",
     "GRADED  (pilot, 16 concepts)\nconfirmatory set not run"),
]

fig, ax = plt.subplots(figsize=(7.2, 8.0))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

COL_X = {"hum": 1.5, "core": 35.0, "mod": 68.0}
COL_W = {"hum": 31.5, "core": 31.5, "mod": 30.5}
TOP, H, GAP = 92.0, 8.4, 2.6

ax.text(COL_X["hum"] + COL_W["hum"] / 2, 96.2, "Human EEG", ha="center", fontsize=8.6,
        fontweight="bold", color=HUM_E)
ax.text(COL_X["core"] + COL_W["core"] / 2, 97.2, "THE ASSAY", ha="center", fontsize=9.5, fontweight="bold",
        color=CORE_E)
ax.text(COL_X["core"] + COL_W["core"] / 2, 95.2, "declared once, then carried to a new substrate", ha="center",
        fontsize=6.5, style="italic", color=CORE_E)
ax.text(COL_X["mod"] + COL_W["mod"] / 2, 96.2, "Language model", ha="center", fontsize=8.6,
        fontweight="bold", color=MOD_E)

def box(x, w, y, h, text, fc, ec, fs=6.4, lw=0.9, weight="normal", tc="#111111"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2",
                                linewidth=lw, facecolor=fc, edgecolor=ec))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            linespacing=1.4, fontweight=weight, color=tc)

for i, (core, hum, mod) in enumerate(STAGES):
    y = TOP - (i + 1) * H - i * GAP
    tagged = core[0].isdigit()
    last = i == len(STAGES) - 1
    box(COL_X["core"], COL_W["core"], y, H, core, CORE, CORE_E,
        fs=6.3 if tagged else 6.8, lw=1.5 if tagged else 0.9,
        weight="bold" if last else "normal", tc=CORE_E if last else "#111111")
    box(COL_X["hum"], COL_W["hum"], y, H, hum, HUM, HUM_E)
    box(COL_X["mod"], COL_W["mod"], y, H, mod, MOD, MOD_E)
    if i:
        ax.add_patch(FancyArrowPatch((COL_X["core"] + COL_W["core"] / 2, y + H + GAP - 0.3),
                                     (COL_X["core"] + COL_W["core"] / 2, y + H + 0.4),
                                     arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color=CORE_E))

y_last = TOP - len(STAGES) * H - (len(STAGES) - 1) * GAP
ax.text(50, y_last - 3.4,
        "The five numbered components are the points at which a procedure's verdict is produced. Boxes with a heavy "
        "border carry them.\nThe right-hand column is a development pilot, and the confirmatory set is untouched.",
        ha="center", va="top", fontsize=6.3, color="#444444", linespacing=1.45)

fig.savefig(os.path.join(HERE, "t1_assay.pdf"), bbox_inches="tight")
print("wrote t1_assay.pdf")

#!/usr/bin/env python3
"""Capacity-growth figure: the Section 2.6/2.7 dynamics read from a decade
of repository histories.

Panel (a): normalized annual closing capacity (each repo / its own age 0-1
capacity), cohort median + IQR by age — growth, then plateau.
Panel (b): per-repo capacity growth rate (slope of log C vs age) against
the share of load-bearing years spent infeasible (CR_y >= 1) — the stall
prediction, with the median-split medians marked.

Reads the committed aggregates from analyze_github_history.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BLUE, RED, GREY = "#1F4E79", "#C00000", "0.4"

gr = pd.read_csv(HERE / "github_history_growth.csv")
rep = pd.read_csv(HERE / "github_history_repos.csv")
s = json.loads((HERE / "github_history_summary.json").read_text())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.2))

# (a) growth curve
by_age = gr.groupby("age").C_norm
ages = [a for a in by_age.groups if by_age.get_group(a).count() >= 8
        and a <= 12]
ages = sorted(ages)
med = [by_age.get_group(a).median() for a in ages]
q25 = [by_age.get_group(a).quantile(.25) for a in ages]
q75 = [by_age.get_group(a).quantile(.75) for a in ages]
ax1.fill_between(ages, q25, q75, color=BLUE, alpha=0.18, label="IQR")
ax1.plot(ages, med, "o-", color=BLUE, lw=1.8, ms=4, label="cohort median")
ax1.axhline(1.0, color="k", lw=1.0, ls=":")
ax1.set_xlabel("repository age  [years]")
ax1.set_ylabel("closing capacity / own early capacity")
ax1.set_title("(a) capacity is built: growth, then plateau", fontsize=9.5,
              loc="left")
ax1.legend(fontsize=8, frameon=False)
ax1.grid(alpha=0.25)

# (b) stall scatter
ax2.scatter(rep.infeasible_share, rep.growth_slope, s=22, color=BLUE,
            alpha=0.7, lw=0)
ax2.axhline(0.0, color="k", lw=0.8, ls=":")
split = s["infeasible_share_split"]
ax2.axvline(split, color=GREY, lw=1.0, ls="--")
lo, hi = (s["growth_slope_median_low_infeas"],
          s["growth_slope_median_high_infeas"])
ax2.plot([rep.infeasible_share.min(), split], [lo, lo], color=RED, lw=2.2)
ax2.plot([split, rep.infeasible_share.max()], [hi, hi], color=RED, lw=2.2)
ax2.annotate(f"median {lo*100:.0f}%/yr", xy=(split - 0.02, lo),
             ha="right", va="bottom", fontsize=8, color=RED)
ax2.annotate(f"median {hi*100:.0f}%/yr", xy=(split + 0.02, hi),
             ha="left", va="bottom", fontsize=8, color=RED)
ax2.set_xlabel("share of load-bearing years with $\\mathrm{CR}_y \\geq 1$")
ax2.set_ylabel("capacity growth rate  [$\\Delta\\log C$/yr]")
ax2.set_title("(b) growth stalls with time spent infeasible",
              fontsize=9.5, loc="left")
ax2.grid(alpha=0.25)

fig.tight_layout()
out = HERE / "github_annealing.pdf"
fig.savefig(out, bbox_inches="tight")
print(f"wrote {out}")

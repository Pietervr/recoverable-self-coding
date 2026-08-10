#!/usr/bin/env python3
"""Existence-proof figure for the foundational paper's operational-systems
application: GitHub repositories as self-decoders.

Panel (a): distribution of per-repo CR = opened/yr / closed/yr against the
           feasibility boundary CR = 1.
Panel (b): observed open-issue backlog, expressed as drain time
           backlog / (C_self/12) months, against CR - the directly countable
           uncertified-commitment count growing as the boundary is approached
           and crossed.

Input:  github_cself.csv (from github_cself.py; aggregate metadata only)
Output: github_verification.pdf
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams.update({
    "font.size": 9, "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42,
})

HERE = Path(__file__).resolve().parent
BLUE, RED, GREY = "#2b6f9e", "#b0413e", "#666666"


def main() -> None:
    m = pd.read_csv(HERE / "github_cself.csv")
    s = json.loads((HERE / "github_cself_summary.json").read_text())
    n = len(m)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.7))

    # (a) CR distribution
    bins = np.linspace(0, max(2.0, float(m.CR.max()) + 0.05), 33)
    feas, infeas = m[m.CR < 1], m[m.CR >= 1]
    ax1.hist(feas.CR, bins=bins, color=BLUE, alpha=0.85,
             label=f"CR < 1  (n={len(feas)})")
    ax1.hist(infeas.CR, bins=bins, color=RED, alpha=0.85,
             label=f"CR $\\geq$ 1  (n={len(infeas)})")
    ax1.axvline(1.0, color="k", lw=1.0, ls="--")
    ax1.text(1.06, ax1.get_ylim()[1] * 0.97, "$\\Gamma$", va="top", fontsize=10,
             zorder=5, bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    ax1.set_xlabel("capacity ratio  CR (issues opened / closed, 1 yr)")
    ax1.set_ylabel("repositories")
    ax1.set_title(f"(a)  {n} top-starred repositories", fontsize=9, loc="left")
    ax1.legend(frameon=False, fontsize=8)

    # (b) backlog drain time vs CR
    ax2.scatter(feas.CR, feas.drain_months, s=12, color=BLUE, alpha=0.6, lw=0)
    ax2.scatter(infeas.CR, infeas.drain_months, s=12, color=RED, alpha=0.6, lw=0)
    ax2.axvline(1.0, color="k", lw=1.0, ls="--")
    ax2.set_yscale("log")
    ax2.set_xlabel("capacity ratio  CR")
    ax2.set_ylabel("backlog drain time  [months]")
    med_lo = s["drain_months_median_CR_lt_1"]
    med_hi = s.get("drain_months_median_CR_ge_1")
    title = f"(b)  open backlog: median drain {med_lo:.1f} mo (CR<1)"
    if med_hi is not None:
        title += f" vs {med_hi:.1f} mo (CR$\\geq$1)"
    ax2.set_title(title, fontsize=9, loc="left")

    fig.tight_layout()
    out = HERE / "github_verification.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()

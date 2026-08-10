#!/usr/bin/env python3
"""Figure for the foundational paper's verification section (CinC-2019).

Panel (a): CR distributions, sepsis vs non-sepsis, from the committed
aggregate histograms — the boundary CR=1 marked. Panel (b): median backlog
occupancy per CR bin (IQR band) against the stationary M/M/1 law CR/(1-CR):
agreement in the fast-relaxation regime, controlled shortfall near the
boundary where 2-day stays cannot reach stationarity (relaxation time
diverges).

Reads only committed aggregates (cinc2019_regime_hist.csv,
cinc2019_srcr_binned.csv). Writes cinc2019_verification.pdf here.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
hist = pd.read_csv(HERE / "cinc2019_regime_hist.csv")
srcr = pd.read_csv(HERE / "cinc2019_srcr_binned.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.4))

# ---- panel (a): CR distributions, sepsis split ----
for gname, color, label in (
        ("non_sepsis", "#1F4E79", "non-sepsis (n=34{,}459)"),
        ("sepsis", "#C00000", "sepsis (n=2{,}437)")):
    h = hist[(hist["quantity"] == "CR") & (hist["group"] == gname)]
    x, c = h["bin_center"].to_numpy(), h["count"].to_numpy(float)
    dens = c / max(c.sum(), 1)
    ax1.step(x, dens, where="mid", color=color, lw=1.8,
             label=label.replace("{,}", ","))
    ax1.fill_between(x, dens, step="mid", color=color, alpha=0.18)
ax1.axvline(1.0, color="0.25", lw=1.3, ls=":")
ax1.text(1.05, 0.128, "CR = 1", fontsize=9, color="0.25", ha="left", va="top")
ax1.set_xlabel(r"capacity ratio  $\mathrm{CR}=\hat R_{\mathrm{self}}/\hat C_{\mathrm{self}}$")
ax1.set_ylabel("fraction of stays")
ax1.set_xlim(0, 2.05)
ax1.set_title("(a) ICU stays against the feasibility boundary", fontsize=9.5)
ax1.legend(fontsize=8, loc="upper right")
ax1.grid(alpha=0.25)

# ---- panel (b): occupancy vs load ----
ax2.semilogy(srcr["CR_bin"], srcr["theory"], "-", color="#C00000", lw=1.8,
             label=r"stationary law $\mathrm{CR}/(1-\mathrm{CR})$")
ax2.semilogy(srcr["CR_bin"], srcr["SR_median"], "o", color="#1F4E79", ms=4,
             label="observed median occupancy")
ax2.fill_between(srcr["CR_bin"], srcr["SR_q25"], srcr["SR_q75"],
                 color="#1F4E79", alpha=0.18, label="IQR")
ax2.set_xlabel(r"capacity ratio $\mathrm{CR}$ (binned)")
ax2.set_ylabel("backlog occupancy")
ax2.set_title("(b) occupancy vs load: truncated relaxation near $\\Gamma$",
              fontsize=9.5)
ax2.legend(fontsize=8, loc="upper left")
ax2.grid(alpha=0.25, which="both")

fig.tight_layout()
out = HERE / "cinc2019_verification.pdf"
fig.savefig(out, bbox_inches="tight")
print(f"wrote {out}")

#!/usr/bin/env python3
"""Figure for the foundational paper's verification section (CinC-2019).

Panel (a): CR distributions, sepsis vs non-sepsis, from the committed
aggregate histograms — the boundary CR=1 marked. Panel (b): median backlog
occupancy per CR bin (IQR band) against the stationary M/M/1 law CR/(1-CR):
agreement in the fast-relaxation regime, controlled shortfall near the
boundary where 2-day stays cannot reach stationarity (relaxation time
diverges).

Panel (c): the personal-parameter panel — per-patient (R, C) density in
events/day against the boundary C = R, with the same-load band (middle R
quintile) marked: capacity there spans 2.2x and feasibility runs 13% -> 100%
across capacity quartiles.

Reads only committed aggregates (cinc2019_regime_hist.csv,
cinc2019_srcr_binned.csv, cinc2019_rc_hist2d.csv,
cinc2019_personal_summary.json). Writes cinc2019_verification.pdf here.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

HERE = Path(__file__).resolve().parent
hist = pd.read_csv(HERE / "cinc2019_regime_hist.csv")
srcr = pd.read_csv(HERE / "cinc2019_srcr_binned.csv")
rc = pd.read_csv(HERE / "cinc2019_rc_hist2d.csv")
psum = json.loads((HERE / "cinc2019_personal_summary.json").read_text())

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(11.8, 3.3))

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

# ---- panel (c): R and C are personal parameters ----
edges = np.linspace(0, 40, 81)
grid = np.zeros((80, 80))
ri = np.clip((rc.R_lo / 0.5).round().astype(int), 0, 79)
ci = np.clip((rc.C_lo / 0.5).round().astype(int), 0, 79)
grid[ci, ri] = rc["count"]
ax3.pcolormesh(edges, edges, grid, cmap="Blues",
               norm=LogNorm(vmin=1, vmax=max(grid.max(), 2)),
               rasterized=True)
ax3.plot([0, 38], [0, 38], ls=":", color="0.25", lw=1.3)
ax3.text(34.3, 30.6, r"$\Gamma$: $C=R$", fontsize=9, color="0.25",
         rotation=39, ha="center")
blo, bhi = psum["band_R_day"]
ax3.axvspan(blo, bhi, color="#C00000", alpha=0.10)
ax3.annotate(
    "same-load band:\ncapacity spans "
    f"{psum['band_C_spread_x']:.1f}$\\times$,\n"
    "feasible 13% $\\to$ 100%\nby capacity quartile",
    xy=((blo + bhi) / 2, 30), xytext=(1.2, 39.3), fontsize=8, va="top",
    arrowprops=dict(arrowstyle="-", color="0.4", lw=0.8))
ax3.set_xlim(0, 40)
ax3.set_ylim(0, 40)
ax3.set_xlabel(r"$\hat R_{\mathrm{self}}$  [events/day]")
ax3.set_ylabel(r"$\hat C_{\mathrm{self}}$  [events/day]")
ax3.set_title("(c) capacity is personal: spread at matched load",
              fontsize=9.5)

fig.tight_layout()
out = HERE / "cinc2019_verification.pdf"
fig.savefig(out, bbox_inches="tight")
print(f"wrote {out}")

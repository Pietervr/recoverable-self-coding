#!/usr/bin/env python3
"""Toy-model figure for the RSC proceedings: the stability ratio SR(CR) = CR/(1-CR)
(M/M/1 backlog scaling) diverging at the feasibility boundary CR -> 1.
Generates sr_divergence_toy.pdf."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CR = np.linspace(0.0, 0.97, 400)
SR = CR / (1.0 - CR)            # M/M/1 mean-backlog scaling, utilisation rho = CR
SRc = 3.0                       # illustrative admissibility threshold

fig, ax = plt.subplots(figsize=(5.0, 3.4))
# recoverable region: CR<1 and SR<=SRc
CRc = SRc / (1.0 + SRc)         # CR at which SR = SRc
ax.axvspan(0, CRc, ymin=0, ymax=SRc / 8.0, color="#2E7D32", alpha=0.10)
ax.plot(CR, SR, color="#1F4E79", lw=2.2, label=r"$\mathrm{SR}(\mathrm{CR})=\dfrac{\mathrm{CR}}{1-\mathrm{CR}}$")
ax.axvline(1.0, color="#C00000", ls="--", lw=1.6, label=r"feasibility boundary $\Gamma\ (\mathrm{CR}=1)$")
ax.axhline(SRc, color="#888888", ls=":", lw=1.4, label=r"admissibility threshold $\mathrm{SR}_c$")
ax.scatter([CRc], [SRc], color="#C00000", zorder=5, s=28)
ax.annotate("recoverable\nregime", xy=(0.18, 0.45), fontsize=9, color="#2E7D32", ha="center")
ax.annotate(r"$\mathrm{SR}\sim(1-\mathrm{CR})^{-1}$", xy=(0.86, 6.0), xytext=(0.55, 6.3),
            fontsize=9, color="#1F4E79",
            arrowprops=dict(arrowstyle="->", color="#1F4E79", lw=1.2))

ax.set_xlim(0, 1.08); ax.set_ylim(0, 8)
ax.set_xlabel(r"capacity ratio $\mathrm{CR}=R_{\mathrm{self}}/C_{\mathrm{self}}$", fontsize=10)
ax.set_ylabel(r"stability ratio $\mathrm{SR}=\dot S_i/\dot S_e$", fontsize=10)
ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("sr_divergence_toy.pdf", bbox_inches="tight")
print("wrote sr_divergence_toy.pdf")

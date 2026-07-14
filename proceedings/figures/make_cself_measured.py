#!/usr/bin/env python3
"""C_self measured from a longitudinal event stream (proceedings, after Sec. 2).

Demonstrates that C_self, R_self, and the margin M = C_self - R_self are
concrete measured quantities, not only formal ones. Physiological homeostasis is
the self-decoder: a monitored variable crossing outside a reference band is a
candidate commitment, its return within a horizon is certification, and the
restoration rate is C_self. Estimated over synthetic longitudinal health records
(Synthea); per-unit values in cself_measured_synthea.csv.

Reads cself_measured_synthea.csv (C_self, R_self, CR, SR per unit); writes
cself_measured.pdf. Deterministic (no randomness).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("cself_measured_synthea.csv")
C = df["C_self"].to_numpy()
R = df["R_self"].to_numpy()
feasible = R < C

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.2))

# (a) measured R_self and C_self distributions
ax1.hist(np.log10(R[R > 0]), bins=32, color="#1F4E79", alpha=0.6, label=r"$R_{\mathrm{self}}$ (induced flux)")
ax1.hist(np.log10(C[C > 0]), bins=32, color="#2E7D32", alpha=0.6, label=r"$C_{\mathrm{self}}$ (capacity)")
ax1.set_xlabel(r"measured rate  ($\log_{10}$, yr$^{-1}$)")
ax1.set_ylabel("units")
ax1.set_title(r"(a) $R_{\mathrm{self}}$ and $C_{\mathrm{self}}$ are measurable", fontsize=9)
ax1.legend(fontsize=8)
ax1.grid(alpha=0.25)

# (b) measured feasibility margin M = C_self - R_self
hi = float(max(C.max(), R.max())) * 1.02
ax2.fill_between([0, hi], [0, hi], 0, color="#2E7D32", alpha=0.07)   # feasible region R<C
ax2.scatter(C[feasible], R[feasible], s=6, alpha=0.30, color="#1F4E79",
            edgecolors="none", label=r"$R_{\mathrm{self}}<C_{\mathrm{self}}$ (feasible)")
ax2.scatter(C[~feasible], R[~feasible], s=6, alpha=0.35, color="#C00000",
            edgecolors="none", label=r"$R_{\mathrm{self}}\geq C_{\mathrm{self}}$")
ax2.plot([0, hi], [0, hi], "-", color="k", lw=1.2, label=r"$R_{\mathrm{self}}=C_{\mathrm{self}}$")
ax2.set_xlim(0, hi); ax2.set_ylim(0, hi)
ax2.set_xlabel(r"measured $C_{\mathrm{self}}$  (yr$^{-1}$)")
ax2.set_ylabel(r"measured $R_{\mathrm{self}}$  (yr$^{-1}$)")
ax2.set_title(r"(b) measured margin $\mathcal{M}=C_{\mathrm{self}}-R_{\mathrm{self}}$", fontsize=9)
ax2.legend(fontsize=7, loc="upper left", framealpha=0.9)
ax2.grid(alpha=0.25)

print(f"units: {len(df)}   feasible (R<C): {feasible.mean():.1%}")
fig.tight_layout()
fig.savefig("cself_measured.pdf", bbox_inches="tight")
print("wrote cself_measured.pdf")

#!/usr/bin/env python3
"""Regime map (paper figure): capacity and invertibility are independent axes.

In steady state SR = CR/(1-CR) is CR-slaved, so SR is the *capacity* observable,
not a second axis. Invertibility has its own order parameter zeta = tau_cert/tau_upd
(certification latency vs environmental drift). An M/M/1 certification queue coupled
to a telegraph environment shows: (a) at fixed CR, SR is flat while I(dE;Z) collapses
as zeta rises; (b) the recoverable region in (CR, zeta) has two independent boundaries
-- CR<1 (sharp capacity transition) and zeta<zeta_c (smooth invertibility crossover).
-> figures/si_invertibility.pdf
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MU, DT = 1.0, 4.0
BLUE = "#1F4E79"; RED = "#C00000"; GREEN = "#2E7D32"


def binary_mi(x, y):
    if len(x) < 2:
        return np.nan
    mi = 0.0
    for xv in (-1, 1):
        for yv in (-1, 1):
            pxy = np.mean((x == xv) & (y == yv)); px = np.mean(x == xv); py = np.mean(y == yv)
            if pxy > 0 and px > 0 and py > 0:
                mi += pxy * np.log2(pxy / (px * py))
    return mi


def simulate(CR, kappa, N=120000, seed=0):
    rng = np.random.default_rng(seed)
    ia = rng.exponential(1 / (CR * MU), N); S = rng.exponential(1 / MU, N)
    Wq = np.zeros(N)
    for i in range(1, N):
        w = Wq[i - 1] + S[i - 1] - ia[i]; Wq[i] = w if w > 0 else 0.0
    T = Wq + S; cert = T < DT
    dEa = rng.choice(np.array([-1, 1]), N)
    dEc = dEa * np.where(rng.random(N) < 0.5 * (1 - np.exp(-2 * kappa * T)), -1, 1)
    Z = np.where(cert, dEa, rng.choice(np.array([-1, 1]), N))
    return dict(SR=(~cert).sum() / max(1, cert.sum()), I=binary_mi(dEc, Z),
                recov=float(np.mean(cert & (dEc == dEa))))


CR_fix = 0.70
zetas = np.geomspace(0.02, 5.0, 9)
SRs = [simulate(CR_fix, z / (2 * DT), seed=1)["SR"] for z in zetas]
Is = [simulate(CR_fix, z / (2 * DT), seed=1)["I"] for z in zetas]

CRg = np.linspace(0.30, 0.95, 11); Zg = np.geomspace(0.02, 5.0, 11)
REC = np.array([[simulate(cr, z / (2 * DT), N=60000, seed=2)["recov"] for cr in CRg] for z in Zg])

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.0, 4.5))
a1b = a1.twinx()
a1.semilogx(zetas, SRs, "o-", color=BLUE, lw=2.2, ms=6, label="SR  (capacity observable)")
a1b.semilogx(zetas, Is, "s-", color=RED, lw=2.2, ms=6, label=r"$I(\delta E;Z)$  (invertibility)")
a1.set_xlabel(r"invertibility axis  $\zeta=\tau_{\rm cert}/\tau_{\rm upd}$   (fixed CR $=0.70$)")
a1.set_ylabel("SR", color=BLUE); a1.tick_params(axis="y", labelcolor=BLUE)
a1b.set_ylabel(r"$I(\delta E;Z)$  [bit]", color=RED); a1b.tick_params(axis="y", labelcolor=RED)
a1.set_ylim(0, max(SRs) * 1.7); a1b.set_ylim(0, 1.0)
a1.set_title(r"(a)  fixed CR: SR flat, invertibility collapses", fontsize=10.5, weight="bold")
h1, l1 = a1.get_legend_handles_labels(); h2, l2 = a1b.get_legend_handles_labels()
a1.legend(h1 + h2, l1 + l2, fontsize=8.5, loc="center left")

im = a2.pcolormesh(CRg, Zg, REC, shading="gouraud", cmap="RdYlGn", vmin=0, vmax=REC.max())
a2.set_yscale("log"); a2.set_xlabel("capacity axis  CR"); a2.set_ylabel(r"invertibility axis  $\zeta$")
a2.axvline(1.0, color="k", lw=1.4, ls="--")
a2.text(0.99, 0.03, "CR $=1$", rotation=90, fontsize=8, ha="right", va="bottom", transform=a2.get_xaxis_transform())
a2.set_title("(b)  recoverable region: two independent boundaries", fontsize=10.5, weight="bold")
fig.colorbar(im, ax=a2, label="recoverable fraction")
fig.tight_layout()
fig.savefig("si_invertibility.pdf", bbox_inches="tight")
fig.savefig("/tmp/si_invertibility.png", dpi=120, bbox_inches="tight")
print(f"SR flat: {min(SRs):.3f}..{max(SRs):.3f}   I collapses: {max(Is):.3f}..{min(Is):.3f}")
print("wrote figures/si_invertibility.pdf")

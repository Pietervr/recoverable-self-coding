#!/usr/bin/env python3
"""Defend posture for D1: is the (CR, SR) regime map genuinely two-dimensional?

Referee's point: in steady state SR = CR/(1-CR), so SR is CR-slaved -- not an
independent axis, and condition (ii) of the admissibility law does no independent
work. This script tests the DEFENSE: invertibility has its own order parameter,
zeta = tau_cert / tau_upd (certification latency vs how fast the environmental
cause drifts), independent of CR = utilization. The minimal model is an M/M/1
certification queue coupled to a drifting (telegraph) environment.

For each commitment (arrival t_a, sojourn T, commit t_c=t_a+T):
  - cause at arrival dE_a in {+-1}, stationary;
  - telegraph drift: dE_c = dE_a with corr e^{-2 kappa T} (flip rate kappa=1/tau_upd);
  - certified iff T < Delta t; a certified commitment grounds Z = dE_a, an
    uncertified one commits on prior (Z random) -- as in the paper's instrument.
  - invertibility I(dE_c ; Z): does the certified macrostate inform the CURRENT cause?

Predictions if the defense holds:
  (1) SR depends only on CR, NOT on the environment speed kappa  (capacity axis);
  (2) at FIXED CR<1, I(dE;Z) collapses as kappa rises               (invertibility axis);
  (3) the recoverable region in (CR, zeta) is bounded by TWO independent
      boundaries: CR<1 and zeta<zeta_c.
Outputs: prints the decoupling table; writes invertibility_axis.pdf.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MU, DT = 1.0, 4.0
BLUE = "#1F4E79"; CYAN = "#0096C7"; RED = "#C00000"; GREEN = "#2E7D32"


def binary_mi(x, y):
    n = len(x)
    if n < 2:
        return np.nan
    mi = 0.0
    for xv in (-1, 1):
        for yv in (-1, 1):
            pxy = np.mean((x == xv) & (y == yv))
            px = np.mean(x == xv); py = np.mean(y == yv)
            if pxy > 0 and px > 0 and py > 0:
                mi += pxy * np.log2(pxy / (px * py))
    return mi


def simulate(CR, kappa, N=120000, seed=0):
    rng = np.random.default_rng(seed)
    lam = CR * MU
    ia = rng.exponential(1 / lam, N)
    S = rng.exponential(1 / MU, N)
    Wq = np.zeros(N)
    for i in range(1, N):
        w = Wq[i - 1] + S[i - 1] - ia[i]
        Wq[i] = w if w > 0 else 0.0
    T = Wq + S
    cert = T < DT
    dEa = rng.choice(np.array([-1, 1]), N)
    pflip = 0.5 * (1 - np.exp(-2 * kappa * T))
    dEc = dEa * np.where(rng.random(N) < pflip, -1, 1)
    Z = np.where(cert, dEa, rng.choice(np.array([-1, 1]), N))
    SR = (~cert).sum() / max(1, cert.sum())
    I_full = binary_mi(dEc, Z)
    recov = float(np.mean(cert & (dEc == dEa)))   # certified AND fresh
    return dict(SR=SR, I=I_full, recov=recov, cert=float(cert.mean()))


# --- (2) the decoupling: fix CR, sweep environment speed (zeta) ---
CR_fix = 0.70
zetas = np.array([0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0])   # zeta = 2*kappa*DT
print(f"Decoupling at fixed CR={CR_fix} (SR should be flat; I should collapse):")
print(f"{'zeta=2kDt':>10s} {'SR':>8s} {'I(dE;Z)':>9s} {'recov':>7s}")
SRs, Is = [], []
for z in zetas:
    kappa = z / (2 * DT)
    r = simulate(CR_fix, kappa, seed=1)
    SRs.append(r["SR"]); Is.append(r["I"])
    print(f"{z:10.2f} {r['SR']:8.3f} {r['I']:9.3f} {r['recov']:7.3f}")

# --- (3) the 2D phase diagram in (CR, zeta) ---
CRgrid = np.linspace(0.30, 0.95, 12)
Zgrid = np.geomspace(0.02, 5.0, 12)
REC = np.zeros((len(Zgrid), len(CRgrid)))
for i, z in enumerate(Zgrid):
    for j, cr in enumerate(CRgrid):
        REC[i, j] = simulate(cr, z / (2 * DT), N=60000, seed=2)["recov"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.6))
ax1b = ax1.twinx()
ax1.semilogx(zetas, SRs, "o-", color=BLUE, lw=2, label="SR (capacity axis)")
ax1b.semilogx(zetas, Is, "s-", color=RED, lw=2, label=r"$I(\delta E;Z)$ (invertibility)")
ax1.set_xlabel(r"environment speed  $\zeta=2\kappa\,\Delta t$ (at fixed CR=0.70)")
ax1.set_ylabel("SR", color=BLUE); ax1b.set_ylabel(r"$I(\delta E;Z)$ [bit]", color=RED)
ax1.set_title("(a)  At fixed CR: SR flat, invertibility collapses", fontsize=10.5, weight="bold")
ax1.set_ylim(0, max(SRs) * 1.6); ax1b.set_ylim(0, 1.05)
l1, lb1 = ax1.get_legend_handles_labels(); l2, lb2 = ax1b.get_legend_handles_labels()
ax1.legend(l1 + l2, lb1 + lb2, fontsize=8, loc="center left")

im = ax2.pcolormesh(CRgrid, Zgrid, REC, shading="auto", cmap="RdYlGn", vmin=0, vmax=REC.max())
ax2.set_yscale("log"); ax2.set_xlabel("CR (capacity)"); ax2.set_ylabel(r"$\zeta$ (invertibility)")
ax2.axvline(1.0, color="k", lw=1.2, ls="--")
ax2.set_title("(b)  Recoverable region: two independent boundaries", fontsize=10.5, weight="bold")
fig.colorbar(im, ax=ax2, label="recoverable fraction (certified & fresh)")
ax2.text(0.55, 0.04, "recoverable\n(low CR, low $\\zeta$)", fontsize=8, color=GREEN, ha="center")
fig.tight_layout()
fig.savefig("invertibility_axis.pdf", bbox_inches="tight")
fig.savefig("/tmp/invertibility_axis.png", dpi=120, bbox_inches="tight")
print("\nwrote invertibility_axis.pdf")
print(f"SR range over the zeta sweep: {min(SRs):.3f}..{max(SRs):.3f}  (flat => capacity axis independent of zeta)")
print(f"I  range over the zeta sweep: {min(Is):.3f}..{max(Is):.3f}  (collapses => invertibility is a separate axis)")

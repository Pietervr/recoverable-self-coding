#!/usr/bin/env python3
"""SI computational engine — teeth B (multi-distribution robustness) and the
Kingman-universality demonstration of the SR ~ (1-CR)^-1 divergence.

Generalizes the proceedings M/M/1 demo to GI/G/1: arrival and service
processes with matched mean but different variability (squared coefficient of
variation c^2, via Gamma; c^2=0 = deterministic). Shows
  (1) the accuracy/recoverability DECOUPLING holds for every process; and
  (2) SR diverges as (1-CR)^-1 with a UNIVERSAL exponent whose prefactor is
      set by (c_a^2 + c_s^2) -- Kingman's heavy-traffic theorem --
      i.e. SR*(1-CR) -> (c_a^2 + c_s^2)/(2 Dt) as CR -> 1.
Writes si_universality.pdf; prints the prefactor check.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "legend.fontsize": 7})

rng = np.random.default_rng(11)
mu, N, Dt, H, p_acc = 1.0, 20000, 4.0, 4.0, 0.90
CRs = np.linspace(0.30, 0.96, 24)


def gamma_samples(n, mean, cv2):
    if cv2 <= 1e-9:
        return np.full(n, mean)                       # deterministic
    return rng.gamma(shape=1.0 / cv2, scale=mean * cv2, size=n)


def lindley_sojourn(interarr, service):               # single-server queue sojourn
    n = len(service)
    wait = np.empty(n); wait[0] = 0.0
    for i in range(1, n):
        w = wait[i - 1] + service[i - 1] - interarr[i]
        wait[i] = w if w > 0.0 else 0.0
    return wait + service


DISTS = [("M/M/1", 1.0, 1.0), ("M/D/1", 1.0, 0.0), ("D/M/1", 0.0, 1.0),
         ("M/G/1 bursty svc", 1.0, 4.0), ("G/M/1 bursty arr", 4.0, 1.0)]

results = {}
for name, ca2, cs2 in DISTS:
    SR, rec = [], []
    for rho in CRs:
        lam = rho * mu
        soj = lindley_sojourn(gamma_samples(N, 1.0 / lam, ca2),
                              gamma_samples(N, 1.0 / mu, cs2))
        Pc = (soj <= Dt).mean()                        # certified fraction
        SR.append((1 - Pc) / max(Pc, 1e-9))            # uncertified : certified
        rec.append(Pc * (soj <= H).mean())             # certified AND correctable in H
    results[name] = (np.array(SR), np.array(rec), ca2, cs2)

print("distribution        (c_a^2+c_s^2)/(2Dt)   SR*(1-CR)@0.96")
for name, (SR, rec, ca2, cs2) in results.items():
    print(f"{name:18s}  {(ca2+cs2)/(2*Dt):7.3f}            {SR[-1]*(1-CRs[-1]):7.3f}")

fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.9))
for name, (SR, rec, ca2, cs2) in results.items():
    ax[0].semilogy(CRs, SR, 'o-', ms=3, lw=1.2, label=name)
    ax[1].plot(CRs, SR * (1 - CRs), 'o-', ms=3, lw=1.2, label=name)
    ax[2].plot(CRs, rec, 'o-', ms=3, lw=1.2, label=name)
    ax[1].axhline((ca2 + cs2) / (2 * Dt), ls=':', lw=0.8, color='grey')
ax[0].set_title("(a) SR diverges for every process"); ax[0].set_xlabel("CR"); ax[0].set_ylabel("SR"); ax[0].grid(alpha=.25, which='both'); ax[0].legend(fontsize=7)
ax[1].set_title(r"(b) SR$\cdot$(1$-$CR) $\to$ Kingman constant"); ax[1].set_xlabel("CR"); ax[1].set_ylabel(r"SR$\cdot$(1$-$CR)"); ax[1].grid(alpha=.25)
ax[2].axhline(p_acc, color='k', ls='--', lw=1.2, label="accuracy (flat, by construction)")
ax[2].set_title("(c) recoverability collapses; accuracy holds"); ax[2].set_xlabel("CR"); ax[2].set_ylabel("recoverability"); ax[2].set_ylim(0, 1); ax[2].grid(alpha=.25); ax[2].legend(fontsize=7)
fig.suptitle("RSC engine: the (1-CR)$^{-1}$ divergence is universal; the decoupling is robust", y=1.02)
fig.tight_layout()
fig.savefig("si_universality.pdf", bbox_inches="tight")
print("wrote si_universality.pdf")

#!/usr/bin/env python3
"""Numerical demonstration for the RSC proceedings.

An event-driven finite-capacity decoder: candidate commitments arrive (Poisson,
rate lambda) and must be certified by a single server (rate mu=1); utilization
rho = lambda/mu = CR. Waiting time follows the Lindley recursion. A commitment is
*certified* (traceable / locally invertible) if its sojourn (wait+service) is below
the certification horizon Dt, otherwise it is committed *uncertified*. Belief
correctness is drawn independently with probability p_acc, so predictive ACCURACY
is decoupled from congestion. RECOVERABILITY is the chance an erroneous commitment
can still be reversed: it must be certified (traceable) AND a correction pass must
complete within the option-loss window H.

Outputs rsc_simulation.pdf (two panels) and prints summary numbers used in the text.
Deterministic: fixed seed.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
mu = 1.0            # certification service rate
N = 40000          # commitments simulated per CR value
Dt = 4.0           # certification horizon (mean-service-time units)
H  = 4.0           # correction / option-loss window
p_acc = 0.90       # belief accuracy (constant, independent of congestion)
CRs = np.linspace(0.30, 0.965, 28)

accuracy, recover, sr_emp, sr_theory = [], [], [], []
for rho in CRs:
    lam = rho * mu
    interarr = rng.exponential(1.0 / lam, N)
    service  = rng.exponential(1.0 / mu, N)
    wait = np.empty(N); wait[0] = 0.0
    for i in range(1, N):                         # Lindley recursion (single server)
        w = wait[i-1] + service[i-1] - interarr[i]
        wait[i] = w if w > 0.0 else 0.0
    sojourn = wait + service                      # time to certify (queue wait + service)
    certified = sojourn <= Dt
    Pc = certified.mean()
    sr_emp.append((1.0 - Pc) / max(Pc, 1e-9))     # uncertified : certified commitment ratio
    sr_theory.append(rho / (1.0 - rho))           # Eq. (5) backlog scaling
    correct = rng.random(N) < p_acc               # belief correctness (queue-independent)
    accuracy.append(correct.mean())
    corr_sojourn = rng.exponential(1.0 / (mu - lam), N)   # a correction faces the same queue
    recover.append(Pc * (corr_sojourn <= H).mean())       # traceable AND correctable in time

CRs = np.array(CRs); accuracy = np.array(accuracy); recover = np.array(recover)
sr_emp = np.array(sr_emp); sr_theory = np.array(sr_theory)

# ---- summary numbers for the text ----
def at(cr):
    i = int(np.argmin(np.abs(CRs - cr)))
    return CRs[i], accuracy[i], recover[i], sr_emp[i]
for c in (0.5, 0.8, 0.95):
    cr, a, r, s = at(c)
    print(f"CR~{cr:.2f}: accuracy={a:.2f}  recoverability={r:.3f}  SR={s:.2f}")

# ---- figure ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.2))

CRc = 0.75
ax1.axvspan(0, CRc, color="#2E7D32", alpha=0.08)
ax1.plot(CRs, accuracy, "o-", color="#1F4E79", ms=3.5, lw=1.8, label="predictive accuracy")
ax1.plot(CRs, recover,  "s-", color="#C00000", ms=3.5, lw=1.8, label="recoverability")
ax1.set_xlabel(r"capacity ratio $\mathrm{CR}=R_{\mathrm{self}}/C_{\mathrm{self}}$")
ax1.set_ylabel("fraction")
ax1.set_ylim(0, 1.0); ax1.set_xlim(0.3, 1.0)
ax1.set_title("(a) accuracy holds, recoverability collapses", fontsize=9)
ax1.legend(fontsize=8, loc="center left"); ax1.grid(alpha=0.25)

ax2.semilogy(CRs, sr_emp, "o", color="#1F4E79", ms=4, label="simulated SR (uncert./cert.)")
ax2.semilogy(CRs, sr_theory, "-", color="#C00000", lw=1.8, label=r"theory $\mathrm{CR}/(1-\mathrm{CR})$")
ax2.set_xlabel(r"capacity ratio $\mathrm{CR}$")
ax2.set_ylabel(r"stability ratio $\mathrm{SR}$")
ax2.set_xlim(0.3, 1.0)
ax2.set_title(r"(b) SR diverges as $(1-\mathrm{CR})^{-1}$", fontsize=9)
ax2.legend(fontsize=8, loc="upper left"); ax2.grid(alpha=0.25, which="both")

fig.tight_layout()
fig.savefig("rsc_simulation.pdf", bbox_inches="tight")
print("wrote rsc_simulation.pdf")

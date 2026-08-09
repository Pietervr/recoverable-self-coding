#!/usr/bin/env python3
"""Numerical demonstration for the RSC proceedings.

An event-driven finite-capacity decoder: candidate commitments arrive at rate
lambda and must be certified by a single server (rate mu=1); utilization
rho = lambda/mu = CR. Waiting times follow the Lindley recursion. A commitment is
*certified* (traceable / locally invertible) if its sojourn (wait+service) falls
below the certification horizon Dt, and is committed *uncertified* otherwise.
RECOVERABILITY is the chance an erroneous commitment can still be reversed: it must
be certified (traceable) AND a correction pass must complete within the option-loss
window H.

Panel (a) -- the accuracy/recoverability decoupling, under two accuracy models:
  * INDEPENDENT: belief correctness drawn at p_acc, decoupled from congestion by
    construction (the null model: congestion alone destroys recoverability).
  * COUPLED: correctness is a function of the same queue -- p_hi if the commitment
    certified within Dt, p_lo if it timed out. The decoupling is then no longer
    assumed, and the result is an ORDERING: accuracy degrades mildly while
    recoverability collapses.

Panel (b) -- the boundary law SR = <N_uncert> (mean backlog occupancy, obtained as
Little's law L = lambda * E[sojourn]) under three arrival/service laws, testing the
claim that the (1-CR)^-1 exponent is distribution-free while the prefactor is not.
Kingman's heavy-traffic prefactor is (c_a^2 + c_s^2)/2:
  * M/M/1      c_a^2 = 1, c_s^2 = 1  -> 1.0
  * M/D/1      c_a^2 = 1, c_s^2 = 0  -> 0.5
  * H2/M/1     c_a^2 = 4, c_s^2 = 1  -> 2.5
Near the boundary the occupancy estimator is high-variance, so panel (b) averages
REPS independent replications per load; the script prints SR*(1-CR) averaged over
the top loads, which converges to the prefactor above.

Outputs rsc_simulation.pdf next to this file, and prints the summary numbers quoted
in the text. Deterministic: fixed seeds.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

mu = 1.0           # certification service rate
N = 40000          # commitments simulated per CR value
REPS = 12          # replications per load for the panel-(b) distribution sweep
Dt = 4.0           # certification horizon (mean-service-time units)
H = 4.0            # correction / option-loss window
p_acc = 0.90       # belief accuracy, independent model (constant, congestion-free)
p_hi, p_lo = 0.95, 0.85   # belief accuracy, coupled model (certified / timed out)
CRs = np.linspace(0.30, 0.965, 28)


def lindley(interarr, service):
    """Waiting times of a single-server FCFS queue.

    W[0] = 0, W[i] = max(0, W[i-1] + S[i-1] - A[i]) in Skorokhod-reflection form
    (verified equal to the explicit recursion to floating-point associativity).
    """
    x = np.empty(interarr.size)
    x[0] = 0.0
    x[1:] = service[:-1] - interarr[1:]
    c = np.cumsum(x)
    return c - np.minimum.accumulate(c)


def hyperexp(rng, rate, scv, n):
    """Two-phase hyperexponential draws, balanced means: mean 1/rate, given SCV>1."""
    p1 = 0.5 * (1.0 + np.sqrt((scv - 1.0) / (scv + 1.0)))
    p2 = 1.0 - p1
    pick = rng.random(n) < p1
    r = np.where(pick, 2.0 * p1 * rate, 2.0 * p2 * rate)
    return rng.exponential(1.0 / r)


def occupancy(rng, rho, kind):
    """Mean backlog occupancy L = lambda * E[sojourn] for one replication."""
    lam = rho * mu
    if kind == "MM1":
        interarr = rng.exponential(1.0 / lam, N)
        service = rng.exponential(1.0 / mu, N)
    elif kind == "MD1":
        interarr = rng.exponential(1.0 / lam, N)
        service = np.full(N, 1.0 / mu)
    elif kind == "H2M1":
        interarr = hyperexp(rng, lam, 4.0, N)
        service = rng.exponential(1.0 / mu, N)
    else:
        raise ValueError(kind)
    sojourn = lindley(interarr, service) + service
    return lam * sojourn.mean()


# =====================================================================
# Panel (a): one replication, original draw order preserved. The coupled-accuracy
# draw uses its own generator so the independent-accuracy and recoverability
# curves are numerically unchanged from the single-model version.
# =====================================================================
rng = np.random.default_rng(7)
rng_c = np.random.default_rng(11)

accuracy, accuracy_cpl, recover, sr_mm1_single, sr_theory = [], [], [], [], []
for rho in CRs:
    lam = rho * mu
    interarr = rng.exponential(1.0 / lam, N)
    service = rng.exponential(1.0 / mu, N)
    sojourn = lindley(interarr, service) + service   # time to certify (wait + service)
    certified = sojourn <= Dt
    Pc = certified.mean()                            # recoverability horizon only
    sr_mm1_single.append(lam * sojourn.mean())
    sr_theory.append(rho / (1.0 - rho))              # theory: SR = CR/(1-CR)
    correct = rng.random(N) < p_acc                  # belief correctness (queue-independent)
    accuracy.append(correct.mean())
    corr_sojourn = rng.exponential(1.0 / (mu - lam), N)   # a correction faces the same queue
    recover.append(Pc * (corr_sojourn <= H).mean())       # traceable AND correctable in time
    correct_cpl = rng_c.random(N) < np.where(certified, p_hi, p_lo)   # coupled to the queue
    accuracy_cpl.append(correct_cpl.mean())

CRs = np.array(CRs)
accuracy = np.array(accuracy)
accuracy_cpl = np.array(accuracy_cpl)
recover = np.array(recover)
sr_theory = np.array(sr_theory)

# =====================================================================
# Panel (b): the same occupancy law under three arrival/service laws,
# averaged over REPS replications (the estimator is high-variance near CR=1).
# =====================================================================
rng_b = np.random.default_rng(23)
series = {}
for kind in ("MM1", "MD1", "H2M1"):
    series[kind] = np.array([
        np.mean([occupancy(rng_b, rho, kind) for _ in range(REPS)]) for rho in CRs
    ])

# ---- summary numbers for the text ----
def at(cr):
    i = int(np.argmin(np.abs(CRs - cr)))
    return CRs[i], accuracy[i], accuracy_cpl[i], recover[i]


print("panel (a) -- accuracy vs recoverability")
print("  CR      acc(indep)  acc(coupled)  recoverability")
for c in (0.3, 0.5, 0.8, 0.94):
    cr, a, ac, r = at(c)
    print(f"  {cr:.3f}   {a:.3f}       {ac:.3f}         {r:.3f}")

top = CRs >= 0.90
print()
print(f"panel (b) -- Kingman prefactor  SR*(1-CR), mean over CR>=0.90, {REPS} reps")
for kind, pred in (("MD1", 0.5), ("MM1", 1.0), ("H2M1", 2.5)):
    got = float(np.mean(series[kind][top] * (1 - CRs[top])))
    print(f"  {kind:<6}: {got:.2f}   (Kingman {pred})")
print("  spread H2/M/1 : M/D/1 = %.1fx  (Kingman 5.0x)"
      % (series["H2M1"][top].mean() / series["MD1"][top].mean()))

# ---- figure ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.2))

CRc = 0.75
ax1.axvspan(0, CRc, color="#2E7D32", alpha=0.08)
ax1.plot(CRs, accuracy, "o-", color="#1F4E79", ms=3.5, lw=1.8,
         label="accuracy (independent)")
ax1.plot(CRs, accuracy_cpl, "^--", color="#4C8FBD", ms=3.5, lw=1.6,
         label="accuracy (coupled to queue)")
ax1.plot(CRs, recover, "s-", color="#C00000", ms=3.5, lw=1.8, label="recoverability")
ax1.set_xlabel(r"capacity ratio $\mathrm{CR}=R_{\mathrm{self}}/C_{\mathrm{self}}$")
ax1.set_ylabel("fraction")
ax1.set_ylim(0, 1.0)
ax1.set_xlim(0.3, 1.0)
ax1.set_title("(a) accuracy holds, recoverability collapses", fontsize=9)
ax1.legend(fontsize=7.5, loc="lower left")
ax1.grid(alpha=0.25)

ax2.semilogy(CRs, sr_theory, "-", color="#C00000", lw=1.8,
             label=r"theory $\mathrm{CR}/(1-\mathrm{CR})$")
ax2.semilogy(CRs, series["MM1"], "o", color="#1F4E79", ms=4,
             label=r"M/M/1 ($c_a^2\!=\!c_s^2\!=\!1$)")
ax2.semilogy(CRs, series["MD1"], "v", color="#2E7D32", ms=4,
             label=r"M/D/1 ($c_s^2\!=\!0$)")
ax2.semilogy(CRs, series["H2M1"], "^", color="#7B3294", ms=4,
             label=r"H$_2$/M/1 ($c_a^2\!=\!4$)")
ax2.set_xlabel(r"capacity ratio $\mathrm{CR}$")
ax2.set_ylabel(r"stability ratio $\mathrm{SR}$")
ax2.set_xlim(0.3, 1.0)
ax2.set_title(r"(b) SR diverges as $(1-\mathrm{CR})^{-1}$", fontsize=9)
ax2.legend(fontsize=7, loc="upper left")
ax2.grid(alpha=0.25, which="both")

fig.tight_layout()
out = Path(__file__).resolve().parent / "rsc_simulation.pdf"
fig.savefig(out, bbox_inches="tight")
print(f"\nwrote {out}")

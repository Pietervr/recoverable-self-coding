#!/usr/bin/env python3
"""Numerical demonstration for the RSC proceedings (revision 1).

An event-driven finite-capacity decoder: candidate commitments arrive at rate
lambda and must be certified by a single server (rate mu=1); utilization
rho = lambda/mu = CR. Waiting times follow the Lindley recursion. A commitment is
*certified* (traceable) if its sojourn (wait+service) falls below the
certification horizon Dt, and is committed *uncertified* otherwise.
RECOVERABILITY is the availability of a correction opportunity: the commitment is
certified (traceable) AND a corrective pass completes within the option-loss
window H. It is scored independently of whether the commitment proves wrong -- a
correctness-agnostic, conservative capacity measure.

Revision-1 statistical protocol (referee request):
  * warm-up deletion: the first WARMUP commitments of every replication are
    discarded before any estimate (the queue starts empty; near CR=1 the
    relaxation is slow and retaining the transient biases occupancy downward);
  * REPS independent replications per load for BOTH panels, with 95%
    t-based confidence intervals over replications reported in the figure;
  * the coupled-accuracy parameters (p_hi, p_lo) are no longer two fixed
    numbers: panel (c) sweeps p_lo at fixed p_hi and at two loads, mapping
    when accuracy falls before/with/after recoverability. The structural
    finding: coupled accuracy is bounded below by p_lo by construction
    (accuracy -> Pc*p_hi + (1-Pc)*p_lo >= p_lo), while recoverability
    collapses toward 0 REGARDLESS of (p_hi, p_lo); the ordering is therefore
    not an artefact of the chosen probabilities.

Panel (a) -- the accuracy/recoverability decoupling (independent and coupled
models, the latter at the reference point p_hi=0.95, p_lo=0.85).
Panel (b) -- the boundary law SR (mean backlog occupancy via Little's law)
under three arrival/service laws: the (1-CR)^-1 exponent is distribution-free,
the Kingman prefactor (c_a^2+c_s^2)/2 is not.
Panel (c) -- the coupling sweep.

The shaded admissible region in panel (a) is DERIVED from the horizon law:
per-commitment recoverability Pc = 1-exp(-M*Dt) >= 1/2 iff
M >= ln2/Dt, i.e. CR <= 1 - ln2/(mu*Dt) (= 0.827 for mu=1, Dt=4).

Outputs rsc_simulation.pdf next to this file, and prints the summary numbers
quoted in the text. Deterministic: fixed seeds via SeedSequence spawning.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

mu = 1.0           # certification service rate
N = 40000          # commitments simulated per replication per CR value
WARMUP = 5000      # warm-up deletion (discarded from every estimate)
REPS = 12          # independent replications per load (both panels)
Dt = 4.0           # certification horizon (mean-service-time units)
H = 4.0            # correction / option-loss window
p_acc = 0.90       # belief accuracy, independent model
p_hi, p_lo = 0.95, 0.85   # coupled-model reference point (panels a)
CRs = np.linspace(0.30, 0.965, 28)
CR_SHADE = 1.0 - np.log(2.0) / (mu * Dt)   # derived admissibility boundary


def lindley(interarr, service):
    """Waiting times of a single-server FCFS queue (Skorokhod reflection)."""
    x = np.empty(interarr.size)
    x[0] = 0.0
    x[1:] = service[:-1] - interarr[1:]
    c = np.cumsum(x)
    return c - np.minimum.accumulate(c)


def hyperexp(rng, rate, scv, n):
    """Two-phase hyperexponential draws, balanced means: mean 1/rate, SCV>1."""
    p1 = 0.5 * (1.0 + np.sqrt((scv - 1.0) / (scv + 1.0)))
    p2 = 1.0 - p1
    pick = rng.random(n) < p1
    r = np.where(pick, 2.0 * p1 * rate, 2.0 * p2 * rate)
    return rng.exponential(1.0 / r)


def draw_queue(rng, rho, kind="MM1"):
    """One replication's post-warm-up sojourn times."""
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
    return sojourn[WARMUP:]


def point_stats(rng, rho, phi=p_hi, plo=p_lo):
    """One replication of panel-(a) quantities at load rho."""
    lam = rho * mu
    sojourn = draw_queue(rng, rho)
    n = sojourn.size
    certified = sojourn <= Dt
    Pc = certified.mean()
    sr = lam * sojourn.mean()                       # Little's law occupancy
    correct = rng.random(n) < p_acc                 # independent model
    corr_sojourn = rng.exponential(1.0 / (mu - lam), n)
    recov = Pc * (corr_sojourn <= H).mean()
    correct_cpl = rng.random(n) < np.where(certified, phi, plo)
    return correct.mean(), correct_cpl.mean(), recov, sr


def ci95(a, axis=0):
    # Small-sample interval: with REPS=12 replications the estimated-variance
    # 95% interval uses Student's t, t_{11,0.975}=2.201 (not the normal 1.96).
    a = np.asarray(a)
    n = a.shape[axis]
    tcrit = 2.201 if n == 12 else 1.96
    return tcrit * a.std(axis=axis, ddof=1) / np.sqrt(n)


# =====================================================================
# Panel (a): REPS replications per load, warm-up deleted, 95% CIs.
# =====================================================================
ss = np.random.SeedSequence(7)
acc_r, accc_r, rec_r, sr_r = [], [], [], []
for rho in CRs:
    rows = [point_stats(np.random.default_rng(s), rho)
            for s in ss.spawn(REPS)]
    rows = np.array(rows)
    acc_r.append(rows[:, 0]); accc_r.append(rows[:, 1])
    rec_r.append(rows[:, 2]); sr_r.append(rows[:, 3])
acc_r, accc_r = np.array(acc_r), np.array(accc_r)
rec_r, sr_r = np.array(rec_r), np.array(sr_r)

accuracy, accuracy_cpl = acc_r.mean(1), accc_r.mean(1)
recover = rec_r.mean(1)
acc_ci, accc_ci, rec_ci = ci95(acc_r, 1), ci95(accc_r, 1), ci95(rec_r, 1)
sr_theory = CRs / (1.0 - CRs)

# =====================================================================
# Panel (b): three arrival/service laws, REPS replications, warm-up, CIs.
# =====================================================================
ssb = np.random.SeedSequence(23)
series, series_ci = {}, {}
for kind in ("MM1", "MD1", "H2M1"):
    vals = []
    for rho in CRs:
        lam = rho * mu
        occ = [lam * draw_queue(np.random.default_rng(s), rho, kind).mean()
               for s in ssb.spawn(REPS)]
        vals.append(occ)
    vals = np.array(vals)
    series[kind] = vals.mean(1)
    series_ci[kind] = ci95(vals, 1)

# =====================================================================
# Panel (c): the coupling sweep. p_hi = 0.95 fixed; p_lo swept 0..0.9,
# at CR = 0.5 and CR = 0.94. REPS replications each.
# =====================================================================
PLOS = np.linspace(0.0, 0.9, 10)
ssc = np.random.SeedSequence(43)
sweep = {}
for rho in (0.5, 0.94):
    accs, recs, a_ci, r_ci = [], [], [], []
    for plo in PLOS:
        rows = np.array([point_stats(np.random.default_rng(s), rho, plo=plo)
                         for s in ssc.spawn(REPS)])
        accs.append(rows[:, 1].mean()); a_ci.append(ci95(rows[:, 1]))
        recs.append(rows[:, 2].mean()); r_ci.append(ci95(rows[:, 2]))
    sweep[rho] = (np.array(accs), np.array(a_ci),
                  np.array(recs), np.array(r_ci))

# ---- summary numbers for the text ----
def at(cr):
    i = int(np.argmin(np.abs(CRs - cr)))
    return (CRs[i], accuracy[i], acc_ci[i], accuracy_cpl[i], accc_ci[i],
            recover[i], rec_ci[i])


print(f"protocol: N={N}/rep, warm-up {WARMUP}, {REPS} replications, 95% CIs")
print("panel (a) -- accuracy vs recoverability (mean +- 95% CI)")
print("  CR      acc(indep)        acc(coupled)      recoverability")
for c in (0.3, 0.5, 0.8, 0.94):
    cr, a, aci, ac, acci, r, rci = at(c)
    print(f"  {cr:.3f}   {a:.3f}+-{aci:.3f}     {ac:.3f}+-{acci:.3f}"
          f"     {r:.3f}+-{rci:.3f}")

top = CRs >= 0.90
print()
print(f"panel (b) -- Kingman prefactor SR*(1-CR), mean over CR>=0.90")
for kind, pred in (("MD1", 0.5), ("MM1", 1.0), ("H2M1", 2.5)):
    got = float(np.mean(series[kind][top] * (1 - CRs[top])))
    print(f"  {kind:<6}: {got:.2f}   (Kingman {pred})")

print()
print("panel (c) -- coupling sweep at p_hi=0.95 (bounds vs collapse)")
for rho in (0.5, 0.94):
    a, aci, r, rci = sweep[rho]
    print(f"  CR={rho}: acc range [{a.min():.3f},{a.max():.3f}] over "
          f"p_lo in [0,0.9]; recoverability {r.mean():.3f}"
          f" (spread {r.max()-r.min():.3f}) -- load-set, coupling-free")

print()
print(f"derived shading boundary: CR <= 1 - ln2/(mu*Dt) = {CR_SHADE:.3f}")

# =====================================================================
# Robustness: horizon dependence (unchanged protocol, now with warm-up)
# =====================================================================
ssr = np.random.SeedSequence(31)
print()
print("robustness of the recoverability collapse to the horizon")
print("  Dt=H    recov(CR=0.5)   recov(CR=0.94)   collapse factor")
for horizon in (2.0, 4.0, 8.0):
    out = {}
    for rho in (0.5, 0.94):
        lam = rho * mu
        vals = []
        for s in ssr.spawn(REPS):
            rng = np.random.default_rng(s)
            sojourn = draw_queue(rng, rho)
            Pc = (sojourn <= horizon).mean()
            corr = rng.exponential(1.0 / (mu - lam), sojourn.size)
            vals.append(Pc * (corr <= horizon).mean())
        out[rho] = float(np.mean(vals))
    print(f"  {horizon:>4.0f}    {out[0.5]:.3f}           {out[0.94]:.3f}"
          f"            {out[0.5]/max(out[0.94],1e-9):.0f}x")

# ---- figure ----
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(11.6, 3.3))
LAB = 10        # axis-label font size (referee: enlarge)
TICK = 8.5

ax1.axvspan(0, CR_SHADE, color="#2E7D32", alpha=0.08)
ax1.axvline(CR_SHADE, color="#2E7D32", lw=0.9, ls=":")
ax1.text(CR_SHADE - 0.015, 0.30, r"$P_c\geq\frac{1}{2}$ at $\Delta t{=}4$",
         rotation=90, fontsize=8, color="#2E7D32", ha="right")
ax1.errorbar(CRs, accuracy, yerr=acc_ci, fmt="o-", color="#1F4E79", ms=3.5,
             lw=1.8, elinewidth=0.8, capsize=1.5,
             label="accuracy (independent)")
ax1.errorbar(CRs, accuracy_cpl, yerr=accc_ci, fmt="^--", color="#4C8FBD",
             ms=3.5, lw=1.6, elinewidth=0.8, capsize=1.5,
             label="accuracy (coupled)")
ax1.errorbar(CRs, recover, yerr=rec_ci, fmt="s-", color="#C00000", ms=3.5,
             lw=1.8, elinewidth=0.8, capsize=1.5, label="recoverability")
ax1.set_xlabel(r"capacity ratio $\mathrm{CR}$", fontsize=LAB)
ax1.set_ylabel("fraction", fontsize=LAB)
ax1.set_ylim(0, 1.0)
ax1.set_xlim(0.3, 1.0)
ax1.set_title("(a) accuracy holds, recoverability collapses", fontsize=9.5)
ax1.legend(fontsize=8, loc="lower left")
ax1.tick_params(labelsize=TICK)
ax1.grid(alpha=0.25)

ax2.semilogy(CRs, sr_theory, "-", color="#C00000", lw=1.8,
             label=r"M/M/1 exact $\mathrm{CR}/(1-\mathrm{CR})$")
for kind, mk, col, lab in (
        ("MM1", "o", "#1F4E79", r"M/M/1 ($c_a^2\!=\!c_s^2\!=\!1$)"),
        ("MD1", "v", "#2E7D32", r"M/D/1 ($c_s^2\!=\!0$)"),
        ("H2M1", "^", "#7B3294", r"H$_2$/M/1 ($c_a^2\!=\!4$)")):
    ax2.errorbar(CRs, series[kind], yerr=series_ci[kind], fmt=mk, color=col,
                 ms=4, elinewidth=0.8, capsize=1.5, ls="none", label=lab)
ax2.set_xlabel(r"capacity ratio $\mathrm{CR}$", fontsize=LAB)
ax2.set_ylabel(r"stability index $\mathrm{SR}$ (mean backlog)", fontsize=LAB)
ax2.set_xlim(0.3, 1.0)
ax2.set_title(r"(b) $(1-\mathrm{CR})^{-1}$ divergence", fontsize=9.5)
ax2.legend(fontsize=7.5, loc="upper left")
ax2.tick_params(labelsize=TICK)
ax2.grid(alpha=0.25, which="both")

for rho, col_a, col_r, mk in ((0.5, "#4C8FBD", "#E58C8A", "o"),
                              (0.94, "#1F4E79", "#C00000", "s")):
    a, aci, r, rci = sweep[rho]
    ax3.errorbar(PLOS, a, yerr=aci, fmt=mk + "--", color=col_a, ms=3.5,
                 lw=1.3, elinewidth=0.8, capsize=1.5,
                 label=rf"accuracy, $\mathrm{{CR}}={rho}$")
    ax3.errorbar(PLOS, r, yerr=rci, fmt=mk + "-", color=col_r, ms=3.5,
                 lw=1.6, elinewidth=0.8, capsize=1.5,
                 label=rf"recoverability, $\mathrm{{CR}}={rho}$")
ax3.plot(PLOS, PLOS, ":", color="#6B6B6B", lw=1.0)
ax3.text(0.55, 0.47, r"$p_{\mathrm{lo}}$ (accuracy floor)", fontsize=7.5,
         color="#6B6B6B", rotation=35)
ax3.set_xlabel(r"time-out accuracy $p_{\mathrm{lo}}$ "
               r"($p_{\mathrm{hi}}=0.95$)", fontsize=LAB)
ax3.set_ylabel("fraction", fontsize=LAB)
ax3.set_ylim(0, 1.0)
ax3.set_title("(c) the ordering is not the coupling", fontsize=9.5)
ax3.legend(fontsize=7.5, loc="upper left")
ax3.tick_params(labelsize=TICK)
ax3.grid(alpha=0.25)

fig.tight_layout()
out = Path(__file__).resolve().parent / "rsc_simulation.pdf"
fig.savefig(out, bbox_inches="tight")
print(f"\nwrote {out}")

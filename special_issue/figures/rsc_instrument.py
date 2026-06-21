#!/usr/bin/env python3
"""SI: the instrument validated and operationalized in simulation -- answers two
review points at once.
 (a) USE the effective-capacity machinery, don't just cite it: the decay exponent
     is estimable from the SAME observable counts as SR, theta_hat = -ln(P_uncert)/Dt,
     and matches the M/M/1 prediction mu(1-CR).
 (b) The closed form SR(theta*) = e^{-theta* Dt}/(1-e^{-theta* Dt}) with the
     THEORETICAL exponent mu(1-CR) reproduces the directly simulated SR across the
     whole CR range -- Eq. (srtheta) is exact, not a heavy-traffic approximation.
 (c) Operationalize the invertibility condition (Eq. invert): a binary environmental
     cause dE is certified into a macrostate Z only when the commitment clears within
     Dt; the mutual information I(dE;Z) of the committed stream collapses to 0 as
     CR->1, in lockstep with recoverability -- so the second condition of the
     Recoverability Constraint is a measurable quantity that fails at the boundary,
     not a definitional appendage.
Writes si_instrument.pdf.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(17)
mu, Dt, p_acc, N = 1.0, 4.0, 0.90, 400000
plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "legend.fontsize": 8})


def lindley_sojourn(inter, serv):
    n = len(serv); d = np.empty(n); d[0] = 0.0; d[1:] = serv[:-1] - inter[1:]
    P = np.cumsum(d); return (P - np.minimum.accumulate(P)) + serv


def mi_binary(a, b):
    I = 0.0
    for ea in (0, 1):
        for zb in (0, 1):
            pab = np.mean((a == ea) & (b == zb))
            if pab > 0:
                I += pab * np.log2(pab / (np.mean(a == ea) * np.mean(b == zb)))
    return float(I)


CRs = np.linspace(0.30, 0.96, 18)
th_meas, th_pred, sr_meas, sr_pred, mi, recov = [], [], [], [], [], []
for rho in CRs:
    soj = lindley_sojourn(rng.exponential(1 / (rho * mu), N), rng.exponential(1 / mu, N))[2000:]
    cert = soj <= Dt
    Pu = float((~cert).mean()); Pc = 1 - Pu
    th_meas.append(-np.log(max(Pu, 1e-12)) / Dt)
    th_pred.append(mu * (1 - rho))
    sr_meas.append(Pu / Pc)
    t = mu * (1 - rho); sr_pred.append(np.exp(-t * Dt) / (1 - np.exp(-t * Dt)))
    # invertibility: environmental cause dE certified into macrostate Z
    n = len(soj); dE = rng.integers(0, 2, n)
    Z = np.where(cert, np.where(rng.random(n) < p_acc, dE, 1 - dE), rng.integers(0, 2, n))
    mi.append(mi_binary(dE, Z)); recov.append(Pc)

fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.9))
ax[0].plot(CRs, th_pred, '-', color='0.5', lw=2, label=r"$\mu(1-\mathrm{CR})$ (theory)")
ax[0].plot(CRs, th_meas, 'o', color="#1f77b4", ms=5, label=r"$\hat\theta^\star=-\ln\hat P_{\mathrm{unc}}/\Delta t$ (counts)")
ax[0].set_xlabel("capacity ratio CR"); ax[0].set_ylabel(r"decay exponent $\theta^\star$")
ax[0].set_title("(a) decay exponent, estimated from counts"); ax[0].grid(alpha=.25); ax[0].legend()

ax[1].semilogy(CRs, sr_pred, '-', color='0.5', lw=2, label=r"closed form, $\theta^\star=\mu(1-\mathrm{CR})$")
ax[1].semilogy(CRs, sr_meas, 'o', color="#C00000", ms=5, label="simulated SR")
ax[1].set_xlabel("capacity ratio CR"); ax[1].set_ylabel("stability ratio SR")
ax[1].set_title("(b) SR follows the exact closed form"); ax[1].grid(alpha=.25, which='both'); ax[1].legend()

ax[2].plot(CRs, mi, 'o-', color="#6A0DAD", ms=4, lw=1.4, label=r"$I(\delta E;Z)$ (bits)")
ax[2].plot(CRs, recov, 's--', color="#2E7D32", ms=3, lw=1.2, label="recoverability")
ax[2].set_xlabel("capacity ratio CR"); ax[2].set_ylabel("invertibility / recoverability")
ax[2].set_title("(c) invertibility MI collapses at the boundary"); ax[2].set_ylim(0, 1.0); ax[2].grid(alpha=.25); ax[2].legend()

fig.suptitle("The instrument validated and operationalized: the decay exponent, the closed-form SR, and the invertibility MI", y=1.02)
fig.tight_layout()
fig.savefig("si_instrument.pdf", bbox_inches="tight")
print("CR    theta_meas theta_pred   SR_meas  SR_pred    I(dE;Z)  recov")
for i in range(0, len(CRs), 3):
    print(f"{CRs[i]:4.2f}   {th_meas[i]:7.4f}   {th_pred[i]:7.4f}   {sr_meas[i]:7.3f}  {sr_pred[i]:7.3f}   {mi[i]:6.3f}  {recov[i]:5.3f}")
print("wrote si_instrument.pdf")

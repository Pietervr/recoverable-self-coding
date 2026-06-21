#!/usr/bin/env python3
"""SI computational engine — teeth C: the instrument is estimable from
observable counts, with characterized sample complexity and detection power.

Observable: from a window of n commitments, SR_hat = N_uncertified / N_certified
(pure counts -- exactly what a system already emits), and CR_hat = SR_hat/(1+SR_hat)
(the M/M/1 inversion of SR = CR/(1-CR)). We show:
  (a) SR_hat is consistent; its relative standard error shrinks ~1/sqrt(n) but
      GROWS near the boundary (certified events become rare) -- the instrument is
      hardest to pin exactly where SR is largest;
  (b) sample complexity n*(rel-SE <= 10%) vs CR -- rising toward the boundary;
  (c) a detection ROC: flag 'danger' (true CR >= CR*=0.85) from n observed
      commitments -- early warning before the CR=1 crossing.
Writes si_estimators.pdf; prints n* and ROC AUCs.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(23)
mu, Dt, WARM = 1.0, 4.0, 2000


def lindley_vec(a, s):                         # vectorized single-server sojourn
    n = len(s); d = np.empty(n); d[0] = 0.0; d[1:] = s[:-1] - a[1:]
    P = np.cumsum(d)
    return (P - np.minimum.accumulate(P)) + s


# self-test against the scalar recursion
_a = rng.exponential(1.3, 500); _s = rng.exponential(1.0, 500)
_w = np.empty(500); _w[0] = 0.0
for i in range(1, 500):
    _w[i] = max(0.0, _w[i - 1] + _s[i - 1] - _a[i])
assert np.allclose(_w + _s, lindley_vec(_a, _s)), "vectorized Lindley mismatch"


def sr_hat(rho, n):                            # SR estimate from a window of n commitments
    m = WARM + n
    soj = lindley_vec(rng.exponential(1.0 / (rho * mu), m), rng.exponential(1.0 / mu, m))
    cert = (soj[WARM:] <= Dt)
    nc = int(cert.sum()); nu = n - nc
    return nu / max(nc, 1)


# ---- (a) consistency + (b) sample complexity ----
RHOS = [0.5, 0.7, 0.8, 0.9, 0.95]
NS = [100, 300, 1000, 3000, 10000]
R = 150
relse = {}                                     # relse[rho] = list over NS
for rho in RHOS:
    relse[rho] = []
    for n in NS:
        s = np.array([sr_hat(rho, n) for _ in range(R)])
        relse[rho].append(s.std() / max(s.mean(), 1e-9))
CRsweep = np.linspace(0.50, 0.95, 12)          # estimation difficulty vs CR at fixed n
relse_cr = []
for r in CRsweep:
    s = np.array([sr_hat(r, 2000) for _ in range(R)])
    relse_cr.append(s.std() / max(s.mean(), 1e-9))
print("CR     rel-SE of SR_hat at n=2000")
for r, e in zip(CRsweep, relse_cr):
    print(f"{r:.2f}   {e:.3f}")

# ---- (c) detection ROC: flag true CR >= 0.85 from n commitments ----
CRstar = 0.85
def roc(n, W=1500):
    rhos = rng.uniform(0.5, 0.97, W)
    obs = np.array([sr_hat(r, n) for r in rhos])
    danger = rhos >= CRstar
    d, s = obs[danger], obs[~danger]
    # AUC = Mann-Whitney (robust to SR_hat's heavy tail)
    ss = np.sort(s)
    lt = np.searchsorted(ss, d, 'left'); le = np.searchsorted(ss, d, 'right')
    auc = float((lt.sum() + 0.5 * (le - lt).sum()) / (len(d) * len(s)))
    # ROC curve: threshold at observed values
    thr = np.unique(obs)
    tpr = np.array([1.0] + [(d >= t).mean() for t in thr] + [0.0])
    fpr = np.array([1.0] + [(s >= t).mean() for t in thr] + [0.0])
    o = np.argsort(fpr)
    return fpr[o], tpr[o], auc


fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.9))
for rho in RHOS:
    ax[0].loglog(NS, relse[rho], 'o-', ms=4, lw=1.3, label=f"CR={rho}")
ax[0].axhline(0.10, color='k', ls='--', lw=1)
ax[0].set_xlabel("window size n (commitments)"); ax[0].set_ylabel(r"relative SE of $\widehat{SR}$")
ax[0].set_title("(a) consistent; harder near the boundary"); ax[0].grid(alpha=.25, which='both'); ax[0].legend(fontsize=7)

ax[1].plot(CRsweep, relse_cr, 'o-', color="#C00000", ms=5, lw=1.6)
ax[1].set_xlabel("capacity ratio CR"); ax[1].set_ylabel(r"rel-SE of $\widehat{SR}$ at n=2000")
ax[1].set_title("(b) estimation hardest near the boundary"); ax[1].grid(alpha=.25)

for n in [200, 1000, 5000]:
    f, t, auc = roc(n)
    ax[2].plot(f, t, lw=1.6, label=f"n={n}  (AUC {auc:.2f})")
    print(f"ROC n={n}: AUC={auc:.3f}")
ax[2].plot([0, 1], [0, 1], 'k:', lw=1)
ax[2].set_xlabel("false-positive rate"); ax[2].set_ylabel("true-positive rate")
ax[2].set_title(f"(c) early-warning ROC: flag CR≥{CRstar}"); ax[2].grid(alpha=.25); ax[2].legend(fontsize=8, loc='lower right')

fig.suptitle("RSC instrument is estimable from counts, with characterized sample complexity + detection power", y=1.02)
fig.tight_layout()
fig.savefig("si_estimators.pdf", bbox_inches="tight")
print("wrote si_estimators.pdf")

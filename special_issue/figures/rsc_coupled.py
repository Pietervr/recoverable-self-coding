#!/usr/bin/env python3
"""SI computational study -- the accuracy/recoverability decoupling is NOT an
artifact of drawing accuracy independently of load (referee concern). Here both
quantities are functionals of the SAME single-server sojourn:

  recoverability = fraction resolved within the certification deadline Dt
                   (traceable, hence undoable) -- a hard threshold;
  accuracy       = a_floor + (a_max - a_floor)(1 - e^{-p/tau0}),  where p is the
                   ACTIVE deliberation an item receives before the deadline,
                   p = clip(Dt - wait, 0, service). Un-deliberated commitments
                   fall back on a fast heuristic of quality a_floor > 1/2.

As CR->1 the sojourn diverges (Lindley): items miss the deadline, so
recoverability collapses; but they still commit on the heuristic, so accuracy
degrades only to a_floor. The decoupling is therefore DERIVED from the shared
queue, and its size equals the fast-heuristic quality a_floor. Writes
si_coupled.pdf; prints the CR=0.9 numbers.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
mu, Dt, WARM, N = 1.0, 4.0, 3000, 30000
plt.rcParams.update({"font.size": 10, "axes.titlesize": 10, "legend.fontsize": 8})


def lindley_wait(inter, serv):
    n = len(serv); d = np.empty(n); d[0] = 0.0; d[1:] = serv[:-1] - inter[1:]
    P = np.cumsum(d); return P - np.minimum.accumulate(P)


def simulate(rho, tau0=0.5, afloor=0.65, amax=1.0, n=N):
    m = WARM + n
    inter = rng.exponential(1 / (rho * mu), m); serv = rng.exponential(1 / mu, m)
    wait = lindley_wait(inter, serv)[WARM:]; serv = serv[WARM:]
    soj = wait + serv
    recover = float((soj <= Dt).mean())                       # resolved within the deadline
    p = np.clip(Dt - wait, 0.0, serv)                         # active deliberation before deadline
    acc = afloor + (amax - afloor) * (1 - np.exp(-p / tau0))
    return recover, float(acc.mean())


CRs = np.linspace(0.30, 0.97, 20)
rec = np.array([simulate(r)[0] for r in CRs])
acc = np.array([simulate(r)[1] for r in CRs])

r9, a9 = simulate(0.90)
print(f"CR=0.90: recoverability={r9:.3f}  accuracy={a9:.3f}  (accuracy floor a_floor=0.65)")
print(f"CR=0.30: recoverability={rec[0]:.3f}  accuracy={acc[0]:.3f}")

fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.3))

ax[0].plot(CRs, acc, 'o-', color="#1f77b4", ms=4, lw=1.6, label="accuracy (coupled to load)")
ax[0].plot(CRs, rec, 's-', color="#C00000", ms=4, lw=1.6, label="recoverability")
ax[0].axhline(0.65, ls=':', color="#1f77b4", lw=1, alpha=0.7)
ax[0].text(0.31, 0.665, "fast-heuristic floor", color="#1f77b4", fontsize=7.5)
ax[0].axhline(0.5, ls='--', color='0.5', lw=0.8); ax[0].text(0.31, 0.515, "chance", color='0.5', fontsize=7.5)
ax[0].set_xlabel("capacity ratio CR"); ax[0].set_ylabel("fraction"); ax[0].set_ylim(0, 1.02)
ax[0].set_title("(a) accuracy and recoverability: different functionals of one queue")
ax[0].legend(loc='center left'); ax[0].grid(alpha=.25)

cols = {0.50: "#9ecae1", 0.65: "#4292c6", 0.80: "#084594"}
for af in [0.50, 0.65, 0.80]:
    a = np.array([simulate(r, afloor=af)[1] for r in CRs])
    ax[1].plot(CRs, a, '-', color=cols[af], lw=1.7, label=f"accuracy ($a_{{\\mathrm{{floor}}}}$={af:.2f})")
ax[1].plot(CRs, rec, 's-', color="#C00000", ms=3, lw=1.6, label="recoverability")
ax[1].set_xlabel("capacity ratio CR"); ax[1].set_ylabel("fraction"); ax[1].set_ylim(0, 1.02)
ax[1].set_title("(b) decoupling is robust to fallback quality")
ax[1].legend(loc='center left'); ax[1].grid(alpha=.25)

fig.suptitle("The decoupling is derived from a shared mechanism, not assumed: "
             "recoverability collapses while accuracy degrades only to its heuristic floor", y=1.0)
fig.tight_layout()
fig.savefig("si_coupled.pdf", bbox_inches="tight")
print("wrote si_coupled.pdf")

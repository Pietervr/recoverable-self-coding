#!/usr/bin/env python3
"""EXPLORATORY (not a paper figure). Finding: the count-based SR signal is a strong
DETECTOR but a LAGGING controller -- a real-time policy driven by an SR-EMA trails
the capacity regime and underperforms a blind fixed-rate policy. So the 'alarm =
throughput gain' cannot be cleanly computed from the count-based instrument; the
paper scopes the capacity point to the qualitative measurement-based-admission
argument (Gibbens-Kelly) and defers the closed-loop quantification (open problems).
Kept as the record of that negative result.

Original intent (see below): show measuring the state beats flying blind.

Honest version: the gain must come from MEASUREMENT, not from a static buffer cap.
Setup: an M/M/1 certification queue whose service capacity mu(t) FLUCTUATES (a
telegraph between mu_hi and mu_lo -- reviewers come and go), unobserved directly.
Offered demand is constant. Two policies share the same actuator (admit/defer):
  - BLIND (open loop): admit each arrival with a fixed probability p, no state
    feedback. To survive the low-capacity regimes it must stay conservative.
  - INSTRUMENT (closed loop): estimate SR live from recent certified/uncertified
    counts (an EMA, exactly the Section-on-estimation observable) and defer when
    SR-hat exceeds a threshold. It runs hot when capacity is good and throttles
    when the count signal says the boundary is near.
Tracing the achievable frontier of certified throughput vs un-recoverable fraction,
the instrument frontier dominates: the gap is the margin a blind operator must hold
because it cannot see its state. This is the value of the *measurement* (the
ARQ/feedback gain; Wu-Negi effective capacity), NOT a Shannon-capacity increase,
and NOT merely a finite buffer. -> figures/si_effcapacity.pdf
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MU_HI, MU_LO, R_MU = 1.0, 0.40, 0.015   # capacity telegraph (mean regime ~ 1/R_MU)
LAM, DT, N, ALPHA = 0.70, 10.0, 220000, 0.02
BLUE = "#1F4E79"; GREEN = "#2E7D32"; RED = "#C00000"


def run(policy, param, seed=0):
    rng = np.random.default_rng(seed)
    arr = np.cumsum(rng.exponential(1 / LAM, N))
    u = rng.random(N); Sx = rng.exponential(1.0, N)   # Sx ~ Exp(1); /mu gives Exp(mu)
    sw_t = np.cumsum(rng.exponential(1 / R_MU, 4 * int(arr[-1] * R_MU + 50))); si = 0
    mu = MU_HI; server_free = 0.0; ema = 0.10
    fin = np.empty(N); lab = np.empty(N, bool); nf = 0; dep = 0   # admitted items' finish/cert (FIFO)
    n_admit = n_cert = 0
    for i in range(N):
        t = arr[i]
        while si < len(sw_t) and sw_t[si] < t:
            mu = MU_LO if mu == MU_HI else MU_HI; si += 1
        # commitments realized since the last arrival update the count-based EMA (even while throttling)
        while dep < nf and fin[dep] <= t:
            ema = (1 - ALPHA) * ema + ALPHA * (0.0 if lab[dep] else 1.0); dep += 1
        if policy == "blind":
            admit = u[i] < param
        else:
            sr_hat = ema / (1 - ema) if ema < 0.999 else 999.0
            admit = (sr_hat < param) or (u[i] < 0.05)   # 5% probe keeps the measurement alive
        if admit:
            start = t if server_free <= t else server_free
            f = start + Sx[i] / mu; server_free = f
            cert = (f - t) < DT
            fin[nf] = f; lab[nf] = cert; nf += 1
            n_admit += 1; n_cert += int(cert)
    return n_cert / arr[-1], (1 - n_cert / n_admit if n_admit else np.nan)


blind = [run("blind", p, seed=1) for p in np.linspace(0.28, 0.85, 11)]
inst = [run("inst", s, seed=2) for s in [0.35, 0.5, 0.7, 0.9, 1.2, 1.6, 2.2, 3.0, 4.5]]
b_thr = np.array([x[0] for x in blind]); b_eps = np.array([x[1] for x in blind])
i_thr = np.array([x[0] for x in inst]); i_eps = np.array([x[1] for x in inst])


def thr_at(e0, e, thr):
    o = np.argsort(e); return float(np.interp(e0, e[o], thr[o]))


for et in (0.05, 0.10, 0.20):
    gb, gi = thr_at(et, b_eps, b_thr), thr_at(et, i_eps, i_thr)
    print(f"eps={et:.2f}:  blind throughput={gb:.3f}  instrument={gi:.3f}  gain=+{100*(gi/gb-1):.0f}%")

fig, ax = plt.subplots(figsize=(7.2, 5.0))
ax.plot(b_eps, b_thr, "o-", color=BLUE, lw=2.2, ms=6, label="blind (open loop: fixed admission)")
ax.plot(i_eps, i_thr, "s-", color=GREEN, lw=2.2, ms=6, label="instrument (closed loop: throttle on $\\widehat{\\mathrm{SR}}$)")
et = 0.10; gb, gi = thr_at(et, b_eps, b_thr), thr_at(et, i_eps, i_thr)
ax.annotate("", xy=(et, gi), xytext=(et, gb), arrowprops=dict(arrowstyle="<->", color=RED, lw=2))
ax.text(et + 0.012, 0.5 * (gb + gi), f"reclaimed\n+{100*(gi/gb-1):.0f}%", color=RED, fontsize=10, weight="bold", va="center")
ax.axvline(et, color="grey", ls=":", lw=1)
ax.set_xlabel("un-recoverable fraction  (recoverability target $\\varepsilon$)")
ax.set_ylabel("certified throughput  [/ unit time]")
ax.set_title("Using the instrument is a capacity gain:\nunder fluctuating capacity, measuring the state beats flying blind",
             fontsize=11, weight="bold")
ax.legend(loc="lower right", fontsize=9); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("si_effcapacity.pdf", bbox_inches="tight")
fig.savefig("/tmp/si_effcapacity.png", dpi=120, bbox_inches="tight")
print("wrote figures/si_effcapacity.pdf")

#!/usr/bin/env python3
"""What happens to the collapse when expired work leaves the queue? (round 3, request 4)

Reviewer 1: "a commitment that misses Delta t remains in the queue until served. Such a
commitment is already irreversible, so certifying it later cannot restore recoverability. In
many review pipelines it would leave the queue or be approved without review. This assumption
drives the headline collapse. With deadline abandonment (the M/M/1+D queue), the backlog is
stationary at every load, including CR >= 1, and the in-time certification probability no
longer vanishes at CR = 1." Codex calls this a required scope challenge rather than one of
the four optional extensions.

The variant. Keep Poisson arrivals at rate lambda, exponential certification at rate mu, one
server, first come first served, and give every candidate commitment a deterministic patience
D equal to the certification horizon Delta t: a commitment that cannot BEGIN certification
within Delta t leaves the queue and is committed without review. Under FCFS the waiting time
of an arrival equals the workload it finds, so the decision can be taken on arrival; this is
Barrer's constant-deadline queue (Operations Research 5, 1957), and the stationary analysis of
the M/G/1 version is Baccelli, Boyer and Hebuterne (Adv. Appl. Prob. 16, 1984).

Closed form, by level crossing. Let M = mu - lambda (of either sign) and let V be the
stationary workload. Downcrossings of a level x balance upcrossings:

    f(x) = lambda * P0 * exp(-M x)                 for 0 < x <= D
    f(x) = f(D) * exp(-mu (x - D))                 for x > D
    P0 * [1 + lambda (1 - e^{-MD})/M + rho e^{-MD}] = 1

The density beyond D decays at rate mu whatever the load, because no arrival joins above D, so
a stationary workload exists at EVERY load, including lambda >= mu. An arrival joins if
V <= D, waits exactly V, and is certified in time if V + S <= Delta t. With D = Delta t,

    P_c = P0 * [1 + lambda (1 - e^{-M dt})/M - e^{-M dt}]

and recoverability is P_c^2 at Delta t = H, since the corrective pass faces the same queue.
Setting D = infinity recovers 1 - e^{-M dt}, the lossless M/M/1 value of the main text, which
is the first check below.

Everything is then verified against a direct event-driven simulation of the recursion
V_{n+1} = max(0, V_n + S_n 1{V_n <= D} - A_{n+1}).

Usage:
    python3 abandonment_variant.py [--reps 12] [--n 200000] [--out abandonment.json]
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

MU = 1.0
DT = 4.0          # certification horizon, and the patience D
H = 4.0           # option-loss window
LOADS = (0.30, 0.50, 0.70, 0.85, 0.94, 0.965, 1.00, 1.10, 1.20)


# ----------------------------------------------------------------- closed form
def _ratio(lam, m, x):
    """lambda (1 - e^{-m x}) / m, continuous at m = 0."""
    if abs(m) < 1e-12:
        return lam * x
    return lam * (1.0 - math.exp(-m * x)) / m


def stationary(lam, mu=MU, d=DT):
    """P0, the joining probability, and the moments of the stationary workload."""
    m = mu - lam
    rho = lam / mu
    p0 = 1.0 / (1.0 + _ratio(lam, m, d) + rho * math.exp(-m * d))
    p_join = p0 * (1.0 + _ratio(lam, m, d))
    # E[V 1{V<=D}] = int_0^D x lambda P0 e^{-m x} dx
    if abs(m) < 1e-12:
        ev_le_d = lam * p0 * d * d / 2.0
    else:
        ev_le_d = lam * p0 * ((1.0 - math.exp(-m * d) * (1.0 + m * d)) / (m * m))
    # E[V 1{V>D}] uses the exponential tail f(D) e^{-mu(x-D)}
    f_d = lam * p0 * math.exp(-m * d)
    ev_gt_d = f_d * (d / mu + 1.0 / mu ** 2)
    return dict(p0=p0, p_join=p_join, mean_wait_accepted=ev_le_d / p_join,
                mean_workload=ev_le_d + ev_gt_d, f_d=f_d)


def pc_abandon(lam, mu=MU, dt=DT, d=DT):
    """Probability that a typical candidate commitment is certified within dt.

    Requires dt <= d: beyond the patience the integral limit is d, not dt.
    """
    assert dt <= d + 1e-12
    m = mu - lam
    p0 = stationary(lam, mu, d)["p0"]
    return p0 * (1.0 + _ratio(lam, m, dt) - math.exp(-m * dt))


def pc_lossless(lam, mu=MU, dt=DT):
    return 1.0 - math.exp(-(mu - lam) * dt) if lam < mu else float("nan")


def sr_abandon(lam, mu=MU, d=DT):
    """Mean number in system, by Little's law on the accepted stream."""
    s = stationary(lam, mu, d)
    lam_eff = lam * s["p_join"]
    return lam_eff * (s["mean_wait_accepted"] + 1.0 / mu)


# ------------------------------------------------------------------ simulation
def simulate(rng, lam, mu=MU, d=DT, dt=DT, n=200_000, warmup=50_000):
    """V_{n+1} = max(0, V_n + S_n 1{V_n <= d} - A_{n+1}), with the outcome of each arrival."""
    interarr = rng.exponential(1.0 / lam, n)
    service = rng.exponential(1.0 / mu, n)
    v = 0.0
    joined = np.zeros(n, dtype=bool)
    certified = np.zeros(n, dtype=bool)
    wait = np.zeros(n)
    area = 0.0          # integral of the workload, for the time-average check
    elapsed = 0.0
    for i in range(n):
        if v <= d:
            joined[i] = True
            wait[i] = v
            certified[i] = (v + service[i]) <= dt
            v += service[i]
        a = interarr[i] if i + 1 < n else 0.0
        if i >= warmup:
            # workload decays at rate 1 until the next arrival, floored at 0
            drop = min(v, a)
            area += v * drop - 0.5 * drop * drop
            elapsed += a
        v = max(0.0, v - a)
    k = slice(warmup, n)
    return dict(p_join=float(joined[k].mean()), pc=float(certified[k].mean()),
                mean_wait_accepted=float(wait[k][joined[k]].mean()),
                mean_workload=float(area / elapsed) if elapsed > 0 else float("nan"))


def run(reps=12, n=200_000, seed=20261013):
    seeds = np.random.SeedSequence(seed).spawn(reps * len(LOADS))
    rows, k = [], 0
    for rho in LOADS:
        lam = rho * MU
        sims = []
        for _ in range(reps):
            sims.append(simulate(np.random.default_rng(seeds[k]), lam, n=n)); k += 1
        exact = dict(p_join=stationary(lam)["p_join"], pc=pc_abandon(lam),
                     mean_wait_accepted=stationary(lam)["mean_wait_accepted"],
                     mean_workload=stationary(lam)["mean_workload"])
        row = dict(load=rho, reps=reps, n=n, exact=exact,
                   pc_lossless=pc_lossless(lam),
                   prec_abandon=pc_abandon(lam) ** 2,
                   prec_lossless=pc_lossless(lam) ** 2 if lam < MU else float("nan"),
                   sr_abandon=sr_abandon(lam),
                   sr_lossless=rho / (1 - rho) if rho < 1 else float("inf"))
        for key in ("p_join", "pc", "mean_wait_accepted", "mean_workload"):
            v = np.array([s[key] for s in sims], float)
            half = 2.201 * float(v.std(ddof=1)) / math.sqrt(reps) if reps == 12 else \
                1.96 * float(v.std(ddof=1)) / math.sqrt(reps)
            row[key] = dict(sim=float(v.mean()), ci_half_width=half, exact=exact[key],
                            inside=bool(abs(v.mean() - exact[key]) <= half))
        rows.append(row)
    return rows


def simulate_discipline(rng, lam, discipline, mu=MU, dt=DT, n=200_000, warmup=50_000):
    """Lossless M/M/1 under FCFS or non-preemptive LCFS, from the same event stream.

    Nothing leaves the queue in either case, so the load, the arrival stream and the service
    times are identical; only the order of service differs.
    """
    interarr = rng.exponential(1.0 / lam, n)
    service = rng.exponential(1.0 / mu, n)
    arrival = np.cumsum(interarr)
    sojourn = np.empty(n)
    waiting = []                      # indices of arrivals not yet started
    free = 0.0                        # time the server next becomes free
    i = 0                             # next arrival to admit
    while i < n or waiting:
        if i < n and (not waiting or arrival[i] <= free):
            waiting.append(i)
            i += 1
            continue
        # the server is free at max(free, arrival of the earliest waiting item)
        if discipline == "FCFS":
            j = waiting.pop(0)
        else:
            j = waiting.pop()         # most recent arrival first
        start = free if free > arrival[j] else arrival[j]
        free = start + service[j]
        sojourn[j] = free - arrival[j]
    k = slice(warmup, n)
    window = float(arrival[n - 1] - arrival[warmup])
    return dict(pc=float((sojourn[k] <= dt).mean()),
                mean_sojourn=float(sojourn[k].mean()),
                l=float(sojourn[k].sum() / window))


def discipline_study(reps=12, n=200_000, loads=(0.50, 0.70, 0.85, 0.94), seed=20261016):
    seeds = np.random.SeedSequence(seed).spawn(reps * len(loads))
    rows, k = [], 0
    for rho in loads:
        f, l = [], []
        for _ in range(reps):
            ss = seeds[k]; k += 1
            f.append(simulate_discipline(np.random.default_rng(ss), rho * MU, "FCFS", n=n))
            l.append(simulate_discipline(np.random.default_rng(ss), rho * MU, "LCFS", n=n))
        rows.append(dict(
            load=rho, reps=reps, n=n,
            pc_fcfs=float(np.mean([x["pc"] for x in f])),
            pc_lcfs=float(np.mean([x["pc"] for x in l])),
            pc_fcfs_ci=float(2.201 * np.std([x["pc"] for x in f], ddof=1) / math.sqrt(reps)),
            pc_lcfs_ci=float(2.201 * np.std([x["pc"] for x in l], ddof=1) / math.sqrt(reps)),
            l_fcfs=float(np.mean([x["l"] for x in f])),
            l_lcfs=float(np.mean([x["l"] for x in l])),
            l_exact=rho / (1 - rho),
            t_fcfs=float(np.mean([x["mean_sojourn"] for x in f])),
            t_lcfs=float(np.mean([x["mean_sojourn"] for x in l])),
            pc_exact_fcfs=pc_lossless(rho * MU)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--n", type=int, default=200_000)
    ap.add_argument("--out", default="abandonment.json")
    a = ap.parse_args()

    # check 1: with no patience limit the closed form is the lossless M/M/1 value
    worst = max(abs(pc_abandon(rho * MU, d=1e6, dt=DT) - pc_lossless(rho * MU))
                for rho in (0.3, 0.5, 0.7, 0.85, 0.94))
    print(f"closed form with D -> infinity against 1 - exp(-M dt): largest gap {worst:.2e}")
    if worst > 1e-9:
        raise SystemExit("the abandonment closed form does not reduce to the lossless case")

    rows = run(reps=a.reps, n=a.n)

    print(f"\nM/M/1+D, deterministic patience D = Delta t = {DT:g}, mu = {MU:g}; "
          f"{a.reps} replications of {a.n:,} arrivals, warm-up 50,000")
    print(f"{'CR':>6} {'P_c exact':>10} {'P_c sim':>18} {'in CI':>6} "
          f"{'join exact':>11} {'join sim':>18} {'in CI':>6}")
    for r in rows:
        print(f"{r['load']:>6.3f} {r['exact']['pc']:>10.4f} "
              f"{r['pc']['sim']:>11.4f} +-{r['pc']['ci_half_width']:<6.4f} "
              f"{str(r['pc']['inside']):>6} {r['exact']['p_join']:>11.4f} "
              f"{r['p_join']['sim']:>11.4f} +-{r['p_join']['ci_half_width']:<6.4f} "
              f"{str(r['p_join']['inside']):>6}")

    print(f"\n{'CR':>6} {'E[V] exact':>11} {'E[V] sim':>18} {'in CI':>6}")
    for r in rows:
        print(f"{r['load']:>6.3f} {r['exact']['mean_workload']:>11.4f} "
              f"{r['mean_workload']['sim']:>11.4f} "
              f"+-{r['mean_workload']['ci_half_width']:<6.4f} "
              f"{str(r['mean_workload']['inside']):>6}")

    print(f"\n{'CR':>6} {'P_c lossless':>13} {'P_c abandon':>12} "
          f"{'recov lossless':>15} {'recov abandon':>14} {'uncertified':>12} "
          f"{'SR lossless':>12} {'SR abandon':>11}")
    for r in rows:
        print(f"{r['load']:>6.3f} {r['pc_lossless']:>13.4f} {r['exact']['pc']:>12.4f} "
              f"{r['prec_lossless']:>15.4f} {r['prec_abandon']:>14.4f} "
              f"{1 - r['exact']['p_join']:>12.4f} "
              f"{r['sr_lossless']:>12.3f} {r['sr_abandon']:>11.3f}")
    print("\n(uncertified = the share of candidate commitments that leave without any "
          "review at all; SR is the mean number in system.)")

    print("\n== service discipline, no abandonment: FCFS against non-preemptive LCFS ==")
    disc = discipline_study(reps=a.reps, n=a.n)
    res_disc = disc
    print(f"{'CR':>6} {'P_c FCFS':>10} {'P_c LCFS':>10} {'ratio':>7} "
          f"{'L FCFS':>9} {'L LCFS':>9} {'L exact':>9} {'E[T] FCFS':>10} {'E[T] LCFS':>10}")
    for d in disc:
        print(f"{d['load']:>6.2f} {d['pc_fcfs']:>10.4f} {d['pc_lcfs']:>10.4f} "
              f"{d['pc_lcfs'] / d['pc_fcfs']:>7.2f} {d['l_fcfs']:>9.3f} "
              f"{d['l_lcfs']:>9.3f} {d['l_exact']:>9.3f} {d['t_fcfs']:>10.3f} "
              f"{d['t_lcfs']:>10.3f}")
    with open(a.out, "w") as fh:
        json.dump({"abandonment": rows, "discipline": res_disc}, fh, indent=2)
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

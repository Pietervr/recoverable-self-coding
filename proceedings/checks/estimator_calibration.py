#!/usr/bin/env python3
"""Does the Figure 1 estimator recover the generating parameters from an event log?

Round 3, Reviewer 1 request 5(c): "apply the estimator of Figure 1 to the simulated event
logs of Section 7 and show that it recovers lambda, mu, SR and P_c." At present the
estimator is never applied to data that satisfy the model, so Section 3 (measurement) and
Section 6 (theory) are never connected.

This cannot be done with the Section 7 simulator as released. `draw_queue` returns only
post-warm-up SOJOURN times, and `point_stats` forms the occupancy as

    sr = lam * sojourn.mean()                      # the GENERATING lambda

so the reported backlog is Little's law applied with the true arrival rate, not a quantity
measured from a log. Feeding the generating rate into an estimate and comparing the result
with that same rate would be circular. This script therefore runs the same queue as an
event-driven simulation, writes a genuine event log (arrival, service start, completion
per commitment), and estimates every quantity from the log alone:

    lambda_hat = arrivals in the window / window length
    mu_hat     = completions in the window / SERVER-BUSY time in the window
    SR_hat     = (1/window) * integral of N(t) dt          [queue trajectory, not Little]
    P_c_hat    = fraction of commitments completing in the window with sojourn <= dt

These are the Figure 1 estimators: arrivals over elapsed time, completions over busy time.
Window-boundary work is handled explicitly — occupancy is integrated only over the window,
and busy exposure counts only the part of each service inside it — so that a commitment
straddling either edge is neither double-counted nor dropped.

The generating values are then revealed and compared. Both successes and failures are
reported; a calibration that only reports agreement is not a calibration.

Usage:
    python3 estimator_calibration.py [--reps 12] [--out calibration.json]
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

MU = 1.0          # service rate, as in Section 7
DT = 4.0          # certification horizon Delta t
LOADS = (0.50, 0.70, 0.85, 0.94)
N_ARRIVALS = 400_000
WARMUP = 50_000


def simulate_log(rng, rho, kind="MM1", n=N_ARRIVALS):
    """Event-driven single-server FCFS run. Returns the per-commitment event log."""
    lam = rho * MU
    if kind == "MM1":
        interarr = rng.exponential(1.0 / lam, n)
        service = rng.exponential(1.0 / MU, n)
    elif kind == "MD1":
        interarr = rng.exponential(1.0 / lam, n)
        service = np.full(n, 1.0 / MU)
    else:
        raise ValueError(kind)

    arrival = np.cumsum(interarr)
    start = np.empty(n)
    completion = np.empty(n)
    free = 0.0
    for i in range(n):
        s = arrival[i] if arrival[i] > free else free
        start[i] = s
        free = s + service[i]
        completion[i] = free
    return dict(arrival=arrival, start=start, completion=completion, service=service)


def _overlap(a, b, t0, t1):
    """Total length of the intersection of each [a_i, b_i] with [t0, t1]."""
    lo = np.maximum(a, t0)
    hi = np.minimum(b, t1)
    return np.maximum(hi - lo, 0.0)


def estimate_from_log(log, t0, t1, dt=DT):
    """The Figure 1 estimators, computed from the log alone over the window [t0, t1]."""
    arrival, start, completion = log["arrival"], log["start"], log["completion"]
    window = t1 - t0

    # arrivals seen in the window
    n_arrivals = int(np.sum((arrival >= t0) & (arrival < t1)))
    lam_hat = n_arrivals / window

    # completions seen in the window, over the server-busy exposure inside it
    in_win_completion = (completion >= t0) & (completion < t1)
    n_completions = int(np.sum(in_win_completion))
    busy = float(np.sum(_overlap(start, completion, t0, t1)))   # server occupied
    mu_hat = n_completions / busy if busy > 0 else float("nan")

    # time-average number in system, from the trajectory: each commitment is in the
    # system over [arrival, completion]; integrate that indicator across the window.
    occupancy = float(np.sum(_overlap(arrival, completion, t0, t1)))
    sr_hat = occupancy / window

    # deadline success among commitments that completed inside the window
    sojourn = completion[in_win_completion] - arrival[in_win_completion]
    pc_hat = float(np.mean(sojourn <= dt)) if sojourn.size else float("nan")

    return dict(lam_hat=lam_hat, mu_hat=mu_hat, sr_hat=sr_hat, pc_hat=pc_hat,
                n_arrivals=n_arrivals, n_completions=n_completions,
                busy_fraction=busy / window, window=window)


def exact_values(rho, kind="MM1", dt=DT):
    """What the log should recover, from Proposition 1."""
    lam = rho * MU
    if kind == "MM1":
        sr = rho / (1.0 - rho)
        pc = 1.0 - math.exp(-MU * (1.0 - rho) * dt)       # exponential sojourn
    elif kind == "MD1":
        sr = rho + rho ** 2 / (2.0 * (1.0 - rho))
        pc = float("nan")        # no elementary closed form for the M/D/1 sojourn cdf
    else:
        raise ValueError(kind)
    return dict(lam=lam, mu=MU, sr=sr, pc=pc)


def run(reps=12, kind="MM1", seed=20261012):
    seeds = np.random.SeedSequence(seed).spawn(reps * len(LOADS))
    out = []
    k = 0
    for rho in LOADS:
        ests = []
        for _ in range(reps):
            rng = np.random.default_rng(seeds[k]); k += 1
            log = simulate_log(rng, rho, kind)
            t0 = float(log["arrival"][WARMUP])
            t1 = float(log["arrival"][-1])
            ests.append(estimate_from_log(log, t0, t1))
        truth = exact_values(rho, kind)
        row = {"load": rho, "kind": kind, "reps": reps, "truth": truth}
        for key, true_key in (("lam_hat", "lam"), ("mu_hat", "mu"),
                              ("sr_hat", "sr"), ("pc_hat", "pc")):
            v = np.array([e[key] for e in ests], dtype=float)
            mean = float(v.mean())
            # Student-t 95% interval over replications, as in S2
            half = 2.201 * float(v.std(ddof=1)) / math.sqrt(reps) if reps > 1 else float("nan")
            t = truth[true_key]
            rel = (mean - t) / t if (t == t and t != 0) else float("nan")
            row[key] = {"mean": mean, "ci_half_width": half, "truth": t,
                        "relative_bias": rel,
                        "truth_in_ci": bool(abs(mean - t) <= half) if t == t else None}
        row["busy_fraction_mean"] = float(np.mean([e["busy_fraction"] for e in ests]))
        out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--kind", default="MM1", choices=["MM1", "MD1"])
    ap.add_argument("--out", default="calibration.json")
    a = ap.parse_args()

    res = run(reps=a.reps, kind=a.kind)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2)

    print(f"{'load':>6} {'quantity':>9} {'estimate':>12} {'truth':>12} "
          f"{'rel.bias':>10} {'truth in CI':>12}")
    for row in res:
        for key in ("lam_hat", "mu_hat", "sr_hat", "pc_hat"):
            d = row[key]
            if d["truth"] != d["truth"]:
                continue
            print(f"{row['load']:>6.2f} {key[:-4]:>9} {d['mean']:>12.5f} "
                  f"{d['truth']:>12.5f} {d['relative_bias']:>+10.4f} "
                  f"{str(d['truth_in_ci']):>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Is the short protocol long enough for the panels that still use it? (round 3, request 2)

Reviewer 1: "A run-length sensitivity check is still not reported. Panels (a) and (c) and the
horizon check keep runs of 4e4 commitments with a 5,000-commitment warm-up. Yet S2.1 and S2.3
now show that runs of this length are unreliable near the boundary (47 +- 8 against an exact
67.5 for H2/M/1 at CR = 0.965). With the relaxation time mu^-1 (1 - sqrt(CR))^-2 of Section
6.2, about 3,200 mean service times at CR = 0.965, the warm-up covers fewer than two
relaxation times at the highest loads of panel (a). The author should apply the longer
protocol to all panels, or report a run-length check."

This is that check. It compares the two protocols against the EXACT values, which the paper
now has for both kinds of quantity:

    deadline success   P_c = 1 - exp(-M dt)                 (Proposition 1(d))
    backlog            SR  = CR/(1-CR), PK, or CR/(1-sigma) (Proposition 1(c),(d))

and separates two quantities that behave differently under a short run:

    P_c  -- a bounded fraction, the quantity panels (a) and (c) report;
    SR   -- the divergent mean, the quantity panel (b) reports, estimated as the released
            code estimates it (lambda * mean sojourn, Little's law with the generating rate).

The expected answer is not symmetric, and the paper should say which panel needed what.

Usage:
    python3 run_length_check.py [--reps 48] [--out run_length.json]
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

MU = 1.0
DT = 4.0
LOADS = (0.50, 0.793, 0.94, 0.965)
SHORT = (40_000, 5_000)          # panels (a) and (c), and the horizon check
LONG = (400_000, 50_000)         # panel (b) since revision 2
SCV_A_H2 = 4.0


def lindley(interarr, service):
    """Waiting times of a single-server FCFS queue (as figures/rsc_simulation.py)."""
    x = np.empty(interarr.size)
    x[0] = 0.0
    x[1:] = service[:-1] - interarr[1:]
    c = np.cumsum(x)
    return c - np.minimum.accumulate(c)


def hyperexp(rng, rate, scv, n):
    p1 = 0.5 * (1.0 + math.sqrt((scv - 1.0) / (scv + 1.0)))
    p2 = 1.0 - p1
    pick = rng.random(n) < p1
    r = np.where(pick, 2.0 * p1 * rate, 2.0 * p2 * rate)
    return rng.exponential(1.0 / r)


def draw_queue(rng, rho, kind, n, warmup):
    lam = rho * MU
    if kind == "MM1":
        interarr, service = rng.exponential(1.0 / lam, n), rng.exponential(1.0 / MU, n)
    elif kind == "MD1":
        interarr, service = rng.exponential(1.0 / lam, n), np.full(n, 1.0 / MU)
    elif kind == "H2M1":
        interarr, service = hyperexp(rng, lam, SCV_A_H2, n), rng.exponential(1.0 / MU, n)
    else:
        raise ValueError(kind)
    return (lindley(interarr, service) + service)[warmup:]


def gim1_root(lam, scv=SCV_A_H2):
    b = 2.0 * (lam / MU) - 1.0
    c = -2.0 * (lam / MU) * (1.0 - lam / MU) / (scv + 1.0)
    return 1.0 - 0.5 * (-b + math.sqrt(b * b - 4.0 * c))


def exact_sr(rho, kind):
    if kind == "MM1":
        return rho / (1.0 - rho)
    if kind == "MD1":
        return rho + rho ** 2 / (2.0 * (1.0 - rho))
    if kind == "H2M1":
        return rho / (1.0 - gim1_root(rho * MU))
    raise ValueError(kind)


def exact_pc(rho, kind):
    if kind == "MM1":
        return 1.0 - math.exp(-MU * (1.0 - rho) * DT)
    if kind == "H2M1":
        return 1.0 - math.exp(-MU * (1.0 - gim1_root(rho * MU)) * DT)
    return float("nan")        # M/D/1 sojourn law has no elementary closed form


def relaxation(rho):
    """Mean service times to relax, mu^-1 (1 - sqrt(CR))^-2."""
    return 1.0 / (MU * (1.0 - math.sqrt(rho)) ** 2)


def study(kind, reps, seed=20261017):
    seeds = np.random.SeedSequence(seed).spawn(reps * len(LOADS) * 2)
    rows, k = [], 0
    for rho in LOADS:
        row = {"kind": kind, "load": rho, "reps": reps,
               "relaxation_service_times": relaxation(rho),
               "exact_sr": exact_sr(rho, kind), "exact_pc": exact_pc(rho, kind)}
        for label, (n, warm) in (("short", SHORT), ("long", LONG)):
            pcs, srs = [], []
            for _ in range(reps):
                rng = np.random.default_rng(seeds[k]); k += 1
                soj = draw_queue(rng, rho, kind, n, warm)
                pcs.append(float((soj <= DT).mean()))
                srs.append(float(rho * MU * soj.mean()))
            pc = np.array(pcs); sr = np.array(srs)
            tcrit = 2.201 if reps == 12 else 1.96
            row[label] = {
                "n": n, "warmup": warm,
                "warmup_relaxations": warm / (rho * relaxation(rho)),
                "pc_mean": float(pc.mean()),
                "pc_ci": float(tcrit * pc.std(ddof=1) / math.sqrt(reps)),
                "pc_rel_bias": float(pc.mean() / row["exact_pc"] - 1.0)
                if row["exact_pc"] == row["exact_pc"] else float("nan"),
                "sr_mean": float(sr.mean()),
                "sr_ci": float(tcrit * sr.std(ddof=1) / math.sqrt(reps)),
                "sr_rel_bias": float(sr.mean() / row["exact_sr"] - 1.0),
            }
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=48)
    ap.add_argument("--out", default="run_length.json")
    a = ap.parse_args()

    out = {}
    for kind in ("MM1", "MD1", "H2M1"):
        out[kind] = study(kind, a.reps)

    print(f"run-length check, {a.reps} replications per cell, mu = 1, Delta t = 4")
    print("short = 4e4 commitments, 5,000 warm-up (panels a and c); "
          "long = 4e5, 5e4 (panel b)")
    print(f"\n{'queue':>6} {'CR':>6} {'relax':>8} {'warm-up':>8} "
          f"{'P_c short':>20} {'P_c long':>20} {'exact':>8}")
    for kind, rows in out.items():
        for r in rows:
            if r["exact_pc"] != r["exact_pc"]:
                continue
            s, l = r["short"], r["long"]
            print(f"{kind:>6} {r['load']:>6.3f} "
                  f"{r['relaxation_service_times']:>8.0f} "
                  f"{s['warmup_relaxations']:>8.1f} "
                  f"{s['pc_mean']:>12.4f}+-{s['pc_ci']:<7.4f} "
                  f"{l['pc_mean']:>12.4f}+-{l['pc_ci']:<7.4f} {r['exact_pc']:>8.4f}")
    print(f"\n{'queue':>6} {'CR':>6} {'SR short':>22} {'SR long':>22} {'exact':>8} "
          f"{'bias short':>11} {'bias long':>10}")
    for kind, rows in out.items():
        for r in rows:
            s, l = r["short"], r["long"]
            print(f"{kind:>6} {r['load']:>6.3f} "
                  f"{s['sr_mean']:>14.3f}+-{s['sr_ci']:<7.3f} "
                  f"{l['sr_mean']:>14.3f}+-{l['sr_ci']:<7.3f} {r['exact_sr']:>8.3f} "
                  f"{s['sr_rel_bias']:>+11.2%} {l['sr_rel_bias']:>+10.2%}")

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

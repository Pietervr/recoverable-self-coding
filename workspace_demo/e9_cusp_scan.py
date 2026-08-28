"""E9 — the alpha x theta cusp map in the reduced model (CPU scan).

The mean-field cusp claim: bistability exists iff alpha (1 + theta) > 1,
closing on alpha* = 1/(1 + theta); theta = T_d / s_cong. Two scan
generations taught the honest formulation:

  gen 1 (3600 s wall, absolute drain criterion): wide wedges everywhere
      — but slow drains near rho -> 1 misread as pinning (time-limit
      artifact).
  gen 2 (10800 s adaptive): wedges collapse toward a ~0.04-0.05 floor
      that the alpha = 0 CONTROL also shows — the floor is the diverging
      relaxation time of the CONTINUOUS congestion transition, not
      bistability. And the wedge is horizon-dependent: metastable escape
      times deep in the wedge exceed any fixed protocol time, so
      rig-scale hysteresis (E4: total) coexists with a narrower
      long-horizon wedge. The map must be drawn AT THE RIG'S HORIZON.

This (gen 3) scan is the pre-registerable, rig-matched map:
  horizon 2100 s (the E6 phase wall), E6-style verdicts:
  UP branch   (ignition): pre-filled clean window, empty queue,
      continuous arrivals at rho; ignited iff queue ever >= 25.
  DOWN branch (drain): junked window (hist ones), backlog B0 = 40, same
      arrivals; verdict from the backlog slope: EXIT iff B_end <= 0.7
      B0, PINNED iff B_end >= B0 (AMBIG dropped from the tally).
  l_up / l_down = 50% crossings found by bisection (N_REP replicas per
  probe); wedge = max(0, l_up - l_down). The alpha = 0 row is the
  artifact floor; the feedback-attributable wedge is wedge - floor.

Prediction surface for the rig spot-checks + the cusp question: does
the artifact-subtracted wedge close near alpha* = 0.433 / 0.276 / 0.160
(T_d = 33 / 66 / 132), or does the content channel hold it open below
the mean-field boundary (the E6 lesson, now as a map)?

Run:  python3 e9_cusp_scan.py     Out: runs/e9_cusp_map.json
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

import e6_predict
from e6_predict import CTX_CAP, S_CONG

HERE = Path(__file__).parent

ALPHAS = [0.0, 0.15, 0.2, 0.3, 0.4, 0.55, 0.8, 1.2, 1.6]
T_DS = [33.0, 66.0, 132.0]
N_REP = 48
WALL = 2100.0         # the E6 phase horizon — what the rig measures
IGNITE_Q = 25
B0 = 40


def run_one(rng, rho, up: bool) -> str:
    """One replica at the rig horizon. Up branch: 'IGNITED' iff queue
    ever >= IGNITE_Q, else 'CALM'. Down branch: E6 slope verdict —
    'EXIT' iff B_end <= 0.7 B0, 'PINNED' iff B_end >= B0, else 'AMBIG'."""
    now, ctx = 0.0, float(CTX_CAP)
    hist = [0.0] * 15 if up else [1.0] * 15
    queue = [] if up else [(0.0, e6_predict.T_D, 0, -t) for t in range(B0)]
    kids = defaultdict(int)
    tid = 0
    lam = rho / S_CONG
    t_a = 0.0
    arrivals = []
    while t_a < WALL:
        t_a += rng.expovariate(lam)
        arrivals.append(t_a)
    while now < WALL:
        while arrivals and arrivals[0] <= now:
            arr = arrivals.pop(0)
            tid += 1
            queue.append((arr, arr + e6_predict.T_D, 0, tid))
        if not queue:
            if not arrivals:
                break
            now = arrivals[0]
            continue
        now, ctx, _ = e6_predict.serve_task(
            rng, 0.0, False, now, ctx, queue, hist, kids)
        if up and len(queue) >= IGNITE_Q:
            return "IGNITED"
    if up:
        return "CALM"
    b = len(queue)
    if b <= 0.7 * B0:
        return "EXIT"
    if b >= B0:
        return "PINNED"
    return "AMBIG"


def prob(rho, up: bool, base_seed: int) -> float:
    """P(IGNITED) up / P(PINNED among EXIT+PINNED) down, N_REP reps."""
    n_pos = n_val = 0
    for i in range(N_REP):
        v = run_one(random.Random(base_seed + int(rho * 1000) * 7 + i),
                    rho, up)
        if up:
            n_val += 1
            n_pos += v == "IGNITED"
        elif v in ("EXIT", "PINNED"):
            n_val += 1
            n_pos += v == "PINNED"
    return n_pos / n_val if n_val else 0.5


def bisect_crossing(up: bool, base_seed: int) -> float | None:
    """rho at which the branch probability crosses 50% (7 bisections).
    Returns None if no crossing inside (0.02, 1.10)."""
    lo, hi = 0.02, 1.10
    p_lo, p_hi = prob(lo, up, base_seed), prob(hi, up, base_seed)
    if (p_lo < 0.5) == (p_hi < 0.5):
        return None
    for _ in range(7):
        mid = (lo + hi) / 2
        p_m = prob(mid, up, base_seed)
        if (p_m < 0.5) == (p_lo < 0.5):
            lo, p_lo = mid, p_m
        else:
            hi, p_hi = mid, p_m
    return round((lo + hi) / 2, 3)


def main() -> int:
    saved_a, saved_t = e6_predict.ALPHA, e6_predict.T_D
    out = {}
    try:
        for td in T_DS:
            e6_predict.T_D = td
            theta = td / S_CONG
            astar = 1 / (1 + theta)
            floor = None
            for a in ALPHAS:
                e6_predict.ALPHA = a
                bs = 90000 + int(td) * 977 + int(a * 100) * 131
                l_up = bisect_crossing(True, bs)
                l_dn = bisect_crossing(False, bs + 50000)
                width = (round(max(0.0, l_up - l_dn), 3)
                         if l_up is not None and l_dn is not None else None)
                if a == 0.0:
                    floor = width
                net = (round(width - floor, 3)
                       if width is not None and floor is not None else None)
                out[f"td{int(td)}_a{a}"] = {
                    "T_d": td, "theta": round(theta, 3), "alpha": a,
                    "alpha_star": round(astar, 3),
                    "l_up": l_up, "l_down": l_dn, "wedge": width,
                    "wedge_net_of_floor": net,
                }
                print(f"T_d={td:5.0f} theta={theta:4.2f} a={a:4.2f} "
                      f"(a*={astar:.3f}): l_up={l_up} l_down={l_dn} "
                      f"wedge={width} net={net}")
    finally:
        e6_predict.ALPHA, e6_predict.T_D = saved_a, saved_t
    (HERE / "runs" / "e9_cusp_map.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

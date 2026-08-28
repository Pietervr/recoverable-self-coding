"""E9 rig spot-check predictions — committed BEFORE the overnight run.

Four phases picked from the committed rig-horizon cusp map
(runs/e9_cusp_map.json, commit 23e01ad) as sharp discriminating pairs:

  THETA pair (alpha = 0.8, rho = 0.65, clean pre-filled window, 2100 s):
    S1  T_d = 33   -> map l_up 0.564 < 0.65  -> predict IGNITED
    S2  T_d = 132  -> map l_up 0.767 > 0.65  -> predict CALM

  ALPHA pair (T_d = 66, rho = 0.55, from the COLLAPSED state, 2100 s):
    S3  alpha quenched 0.8 -> 0.2 after ignition -> map l_down(0.2) =
        0.75 > 0.55 -> predict EXIT (the loop self-heals once feedback
        is weak — the wedge boundary moved with alpha)
    S4  alpha kept 0.8 -> l_down(0.8) = 0.16 < 0.55 -> predict PINNED

S3's alpha-quench is a new protocol (the map's down branch assumed
constant alpha + a synthetic junk state), so this predictor simulates
all four phases with the RIG protocol verbatim: S3/S4 ignite via the
E4 burst ramp at alpha 0.8, then the measurement phase runs at the
quenched alpha with continuous arrivals; S1/S2 start clean-prefilled.
Verdicts: S1/S2 IGNITED iff queue ever >= 25; S3/S4 the E6 slope rule.

Run:  python3 e9_predict_spots.py   Out: runs/e9_spots_prediction.json
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

import e6_predict
from e6_predict import CTX_CAP, S_CONG, Sim

HERE = Path(__file__).parent

N_REP = 200
WALL = 2100.0
IGNITE_LS = [0.60, 0.75, 0.85, 0.95, 1.05, 1.05]
SPOTS = [
    ("S1_up_td33", "up", 33.0, 0.8, 0.65),
    ("S2_up_td132", "up", 132.0, 0.8, 0.65),
    ("S3_down_quench02", "down", 66.0, 0.2, 0.55),
    ("S4_down_a08", "down", 66.0, 0.8, 0.55),
]


def up_phase(rng, td, alpha, rho) -> str:
    saved_a, saved_t = e6_predict.ALPHA, e6_predict.T_D
    e6_predict.ALPHA, e6_predict.T_D = alpha, td
    try:
        now, ctx = 0.0, float(CTX_CAP)
        queue, hist = [], [0.0] * 15
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
                queue.append((arr, arr + td, 0, tid))
            if not queue:
                if not arrivals:
                    break
                now = arrivals[0]
                continue
            now, ctx, _ = e6_predict.serve_task(
                rng, 0.0, False, now, ctx, queue, hist, kids)
            if len(queue) >= 25:
                return "IGNITED"
        return "CALM"
    finally:
        e6_predict.ALPHA, e6_predict.T_D = saved_a, saved_t


def down_phase(rng, td, alpha_meas, rho) -> str | None:
    """Ignite at alpha 0.8 via the burst ramp, then measure at
    alpha_meas with continuous arrivals (the rig protocol)."""
    saved_a, saved_t = e6_predict.ALPHA, e6_predict.T_D
    saved_r, saved_w = e6_predict.RHO_GATED, e6_predict.GATE_WALL
    e6_predict.ALPHA, e6_predict.T_D = 0.8, td
    try:
        sim = Sim(rng)
        for l in IGNITE_LS:
            sim.burst_dwell(l)
            if len(sim.queue) >= 25:
                break
        if len(sim.queue) < 8:
            return None
        e6_predict.ALPHA = alpha_meas
        e6_predict.RHO_GATED = rho
        e6_predict.GATE_WALL = WALL
        b0, b1, v = sim.gate_phase(0.0)
        return v
    finally:
        e6_predict.ALPHA, e6_predict.T_D = saved_a, saved_t
        e6_predict.RHO_GATED, e6_predict.GATE_WALL = saved_r, saved_w


def main() -> int:
    out = {}
    for name, kind, td, alpha, rho in SPOTS:
        counts: dict[str, int] = {}
        for i in range(N_REP):
            rng = random.Random(95000 + i)
            v = (up_phase(rng, td, alpha, rho) if kind == "up"
                 else down_phase(rng, td, alpha, rho)) or "VOID"
            counts[v] = counts.get(v, 0) + 1
        out[name] = {"kind": kind, "T_d": td, "alpha": alpha,
                     "rho": rho, **counts}
        print(f"{name:18s}: {counts}")
    out["prediction"] = {
        "S1_up_td33": "IGNITED", "S2_up_td132": "CALM",
        "S3_down_quench02": "EXIT", "S4_down_a08": "PINNED",
    }
    (HERE / "runs" / "e9_spots_prediction.json").write_text(
        json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

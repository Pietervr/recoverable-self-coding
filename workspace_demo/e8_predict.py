"""E8 prediction — the separatrix (basin boundary) under graded shocks,
committed BEFORE the rig run.

The bistability claim implies a separatrix in the two-component state
(backlog B, window junk j): from the collapsed state, a shock of size f
that removes fraction f of the backlog AND cleans fraction f of the
window either crosses the boundary (relax to healthy) or falls back
(re-pin). E4 verified the endpoints qualitatively (full compound reset
cures; partial resets fail); E8 measures the boundary.

Protocol — SEQUENTIAL, state carried between arms exactly as on the
rig (the E6 lesson: predictor and rig must share the protocol):
  1. IGNITE once via the E4 burst ramp (alpha = 0.8, T_d = 66).
  2. Arms in ARM_SEQ order (ascending expected severity). Before each:
     re-ignite (two 1.05 bursts) if backlog < 8; then HOLD 480 s of
     continuous arrivals at rho_hold = 0.35 — deep in the wedge (gen-3
     map: l_down 0.16 << 0.35 << l_up 0.63; 0.55 was rejected in
     predictor design — too close to l_up, cures re-ignited 77% of the
     time, conflating the separatrix with spontaneous re-ignition).
  3. SHOCK: compound family f in {0, 0.25, 0.5, 0.75, 1.0} — remove
     each queued task with prob f; zero the newest ceil(15 f)
     junk-history entries (rig: replace the newest f fraction of the
     window with clean fill). Plus the two f = 1.0 single-axis shocks:
     backlog_only (queue cleared, window untouched) and window_only
     (window cleaned, queue kept) — two-component memory says both
     underperform the compound shock.
  4. VERDICT: continue at rho_hold for 1500 s; E6 slope rule on the
     post-shock backlog (EXIT <= 0.7 base; PINNED >= base), base =
     max(8, B_after_shock).

Prediction: P(EXIT | f) monotone with a 50% crossing f* (the measured
separatrix); ordering compound > backlog_only > window_only.
Falsifier: no monotone boundary, or axis shocks match the compound.

Run:  python3 e8_predict.py     Out: runs/e8_prediction.json
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import e6_predict
from e6_predict import Sim

HERE = Path(__file__).parent

RHO_HOLD = 0.35
HOLD_S = 480.0
VERDICT_S = 1500.0
# sequential arm order, ascending expected severity (fewer re-ignites);
# state carries between arms exactly as on the rig
ARM_SEQ = [("compound_0.00", 0.0, 0.0), ("compound_0.25", 0.25, 0.25),
           ("window_only", 0.0, 1.0), ("compound_0.50", 0.5, 0.5),
           ("compound_0.75", 0.75, 0.75), ("backlog_only", 1.0, 0.0),
           ("compound_1.00", 1.0, 1.0)]
IGNITE_LS = [0.60, 0.75, 0.85, 0.95, 1.05, 1.05]
REIGNITE_LS = [1.05, 1.05]
N_REP = 200


def shock(sim: Sim, rng, f_b: float, f_j: float) -> int:
    """Apply the shock in place; returns the post-shock backlog."""
    if f_b > 0:
        sim.queue = [t for t in sim.queue if rng.random() >= f_b]
    if f_j > 0:
        k = math.ceil(15 * f_j)
        n = len(sim.hist)
        for i in range(max(0, n - k), n):
            sim.hist[i] = 0
    return len(sim.queue)


def hold(sim: Sim, wall: float):
    """Ungated continuous arrivals at RHO_HOLD for wall seconds
    (gate_phase with q=0 is ungated; its slope verdict ignored here)."""
    saved_wall = e6_predict.GATE_WALL
    e6_predict.GATE_WALL = wall
    try:
        return sim.gate_phase(0.0)
    finally:
        e6_predict.GATE_WALL = saved_wall


def run_replica(rng) -> dict:
    """One SEQUENTIAL replica: ignite once, then the seven arms in
    ARM_SEQ order, re-igniting whenever the state is not collapsed at
    shock time — the rig protocol verbatim."""
    saved = e6_predict.RHO_GATED
    e6_predict.RHO_GATED = RHO_HOLD
    out = {}
    try:
        sim = Sim(rng)
        for l in IGNITE_LS:
            sim.burst_dwell(l)
            if len(sim.queue) >= 25:
                break
        for name, f_b, f_j in ARM_SEQ:
            if len(sim.queue) < 8:
                for l in REIGNITE_LS:
                    sim.burst_dwell(l)
            if len(sim.queue) < 8:
                out[name] = "VOID"
                continue
            hold(sim, HOLD_S)
            if len(sim.queue) < 8:
                out[name] = "VOID"
                continue
            b_shock = shock(sim, rng, f_b, f_j)
            _, b1, _ = hold(sim, VERDICT_S)
            base = max(8, b_shock)
            if b1 <= 0.7 * base:
                out[name] = "EXIT"
            elif b1 >= base:
                out[name] = "PINNED"
            else:
                out[name] = "AMBIG"
        return out
    finally:
        e6_predict.RHO_GATED = saved


def main() -> int:
    tallies = {name: {"EXIT": 0, "PINNED": 0, "AMBIG": 0, "VOID": 0}
               for name, _, _ in ARM_SEQ}
    for i in range(N_REP):
        res = run_replica(random.Random(80000 + i))
        for name, v in res.items():
            tallies[name][v] += 1
    out = {}
    for name, f_b, f_j in ARM_SEQ:
        t = tallies[name]
        valid = t["EXIT"] + t["PINNED"]
        p = t["EXIT"] / valid if valid else float("nan")
        out[name] = {"f_backlog": f_b, "f_window": f_j,
                     "p_exit": round(p, 3), **t}
        print(f"{name:14s} (f_b={f_b:.2f} f_j={f_j:.2f}): "
              f"P(EXIT)={p:.2f}  {t}")
    fstar = None
    for name, f, fj in ARM_SEQ:
        if f == fj and out[name]["p_exit"] >= 0.5:
            fstar = f
            break
    out["prediction"] = {
        "f_star_first_ge_50": fstar,
        "direction": ("P(EXIT|f) monotone; ordering compound > "
                      "backlog_only > window_only (two-component memory)"),
    }
    print(f"\nPREDICTED separatrix: first f with P(EXIT) >= 0.5 -> {fstar}")
    (HERE / "runs" / "e8_prediction.json").write_text(
        json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

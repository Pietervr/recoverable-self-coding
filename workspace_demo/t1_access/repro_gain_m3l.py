"""repro_gain_m3l.py — reproduce the d4v12b gain-calibration failure locally, with the bisection trace.

Run d4v12b's first job to reach its power stage failed at 17:49 UTC on 12 Sept 2026 with
  RuntimeError: gain calibration incomplete — M3L@0.01: bisection limit: 0.00806 vs target 0.01
This runs the same calibration (seed 2026, D = 4, layer 41, four inner starts) for M3L at every target
through the current simulate._one_gain and prints the trace of (scale, gain, se) per bisection step, so
the question "Monte-Carlo noise or saturation?" is answered from the trace rather than guessed.

  NPROC=1 ./.venv/bin/python repro_gain_m3l.py [--targets 0.01] [--live] > repro_gain_m3l.out

--live prints every expected_gain evaluation AS IT COMPLETES (one JSON line per call: scale, gain, se, the
selected graded reference G*, the gain against EVERY graded member, each member's training log-likelihood,
convergence and fitted theta), so the trace can be read while the bisection is still running and a jump in
gain between adjacent scales can be attributed — a switch of G* (Codex's candidate, 12 Sept), a jump of one
member's fit between local optima, or neither. The numbers are identical to the plain run (same seeds).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze as A
import models as M
import simulate as S


_expected_gain = S.expected_gain


def expected_gain_live(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=M.FAMILY_G, **kw):
    """simulate.expected_gain itself, with everything it returns except the per-concept arrays printed per call."""
    t0 = time.time()
    r = _expected_gain(name, theta, seed=seed, n_per_family=n_per_family, D=D, cfg=cfg, graded=graded, **kw)
    scale = float(np.exp(theta[2]))       # theta[2] = log(sep1 * scale), sep1 = 1
    show = {k: v for k, v in r.items()}
    show["theta"] = {g: [round(float(v), 5) for v in th] for g, th in r.get("theta", {}).items()}
    print("EVAL " + json.dumps(dict(scale=round(scale, 10), n_per_family=n_per_family, seed=seed,
                                    warm=bool(kw.get("warm")), seconds=round(time.time() - t0, 1), **show)), flush=True)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="0.01")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--live", action="store_true", help="print every expected_gain evaluation as it completes")
    a = ap.parse_args()
    if a.live:
        S.expected_gain = expected_gain_live      # calibrate_gain looks the name up in simulate's namespace
    cfg = A.Config(n_starts_inner=4)
    for t in (float(x) for x in a.targets.split(",")):
        t0 = time.time()
        e = S._one_gain("M3L", t, a.seed, cfg, a.D)
        print(f"M3L target {t}: scale {e.get('scale')} gain {e.get('gain')} check {e.get('gain_check')} "
              f"± {e.get('gain_check_se')} note={e.get('note')!r} calib_converged={e.get('calib_converged')} "
              f"check_converged={e.get('check_converged')}  ({(time.time() - t0) / 60:.1f} min)", flush=True)
        for i, step in enumerate(e.get("trace", [])):
            print(f"  step {i:2d}: " + json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in step.items()}), flush=True)


if __name__ == "__main__":
    main()

"""repro_gain_m3l.py — reproduce the d4v12b gain-calibration failure locally, with the bisection trace.

Run d4v12b's first job to reach its power stage failed at 17:49 UTC on 12 Sept 2026 with
  RuntimeError: gain calibration incomplete — M3L@0.01: bisection limit: 0.00806 vs target 0.01
This runs the same calibration (seed 2026, D = 4, layer 41, four inner starts) for M3L at every target
through the current simulate._one_gain and prints the trace of (scale, gain, se) per bisection step, so
the question "Monte-Carlo noise or saturation?" is answered from the trace rather than guessed.

  NPROC=1 ./.venv/bin/python repro_gain_m3l.py [--targets 0.01] [--n-per-family 32] > repro_gain_m3l.out
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze as A
import simulate as S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="0.01")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--D", type=int, default=4)
    a = ap.parse_args()
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

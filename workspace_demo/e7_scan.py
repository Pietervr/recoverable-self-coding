"""E7 design scan (model-only, pre-commit): pick rho for the NEAR arm.

Target: ignition >= 70% of replicas within the wall, censoring <= 30%,
median pre-onset n >= 70. Control arm = alpha 0 at the SAME rho (no
fold exists), so the arm comparison is presence-vs-absence of the
feedback mechanism at matched load. Pre-filled window both arms.
"""

from __future__ import annotations

import random
from collections import defaultdict

from e6_predict import CTX_CAP, S_CONG, T_D
import e6_predict
from e7_stats import arm_summary

WALL = 3600.0
N_REP = 120


def run_arm(rng, rho, wall, alpha):
    e6_predict_alpha = e6_predict.ALPHA
    now, ctx = 0.0, float(CTX_CAP)
    queue, hist = [], [0.0] * 15
    kids = defaultdict(int)
    tid = 0
    t_a = 0.0
    lam = rho / S_CONG
    arrivals = []
    while t_a < wall:
        t_a += rng.expovariate(lam)
        arrivals.append(t_a)
    queue_after = []
    e6_predict.ALPHA = alpha
    try:
        while now < wall:
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                tid += 1
                queue.append((arr, arr + T_D, 0, tid))
            if not queue:
                now = arrivals[0] if arrivals else wall
                continue
            now, ctx, _ = e6_predict.serve_task(
                rng, 0.0, False, now, ctx, queue, hist, kids)
            queue_after.append(len(queue))
    finally:
        e6_predict.ALPHA = e6_predict_alpha
    return arm_summary([float(x) for x in hist], queue_after)


def main() -> int:
    for rho in (0.45, 0.55, 0.65, 0.75):
        for alpha in (0.8, 0.0):
            ign = cens = 0
            ns, tq, ta = [], [], []
            for i in range(N_REP):
                s = run_arm(random.Random(71000 + i), rho, WALL, alpha)
                ign += s["ignited"]
                if s.get("censored"):
                    cens += 1
                    continue
                ns.append(s["n"])
                if s.get("tau_qvar") is not None:
                    tq.append(s["tau_qvar"])
                if s.get("tau_qac1") is not None:
                    ta.append(s["tau_qac1"])
            nm = sorted(ns)[len(ns) // 2] if ns else 0
            mtq = sum(tq) / len(tq) if tq else float("nan")
            mta = sum(ta) / len(ta) if ta else float("nan")
            print(f"rho={rho:.2f} a={alpha:.1f}: ign {ign}/{N_REP} "
                  f"cens {cens} n_med {nm} tau_qvar {mtq:+.3f} "
                  f"tau_qac1 {mta:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

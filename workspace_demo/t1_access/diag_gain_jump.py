"""diag_gain_jump.py — the two sides of the gain jump found by repro_gain_m3l.py (12 Sept 2026).

The bisection for M3L at 0.01 nat collapsed onto scale 0.684661 with the gain alternating between 0.00806 and
0.01097 on either side (steps 16–31 of the trace), the selected graded reference being M2K on both sides. This
fits the four graded members on the SAME calibration draw at the two bracket ends (seed 2026, 8 x 32 concepts,
D = 4) and prints, per member, the kept solution and — for the reference member — every start's training
log-likelihood, convergence and held-out gain, so the jump is attributed to what actually moves. Finding
(12 Sept): the kept M2K solution — the best-found one (loglik −44,543.6) is reached by one start of the batch,
the other seven end in a basin 155 nat worse whose held-out score is 0.003 nat per trial worse; whether that one
start lands flips between the exact scales of bisection steps 21 and 22 (1.6e-6 apart in scale, 2.4e-6 relative).
How often a batch of eight misses the best-found solution is NOT established by these runs (Codex, finding 4).

  NPROC=1 ./.venv/bin/python diag_gain_jump.py [--scales 0.684660,0.684662] [--member M2K]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze as A
import models as M
import simulate as S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scales", default="0.684660,0.684662")
    ap.add_argument("--steps", default="", help="instead of --scales: bisection steps of the 12 Sept trace at full precision, e.g. 21,22")
    ap.add_argument("--member", default="M2K")
    ap.add_argument("--only-member", action="store_true", help="fit only --member (the graded reference of the trace)")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--n-per-family", type=int, default=32)
    a = ap.parse_args()
    cfg = A.Config(n_starts_inner=4)
    name, kw = "M3L", S.GAIN_KWARGS["M3L"]
    graded = (a.member,) if a.only_member else M.FAMILY_G
    scales = [float(x) for x in a.scales.split(",")]
    if a.steps:
        # the exact mids of the 12 Sept trace: geometric bisection from [0.02, 3.0], each step's side from the trace
        below = [True, False, True, True, False, True, False, False, True, False, False, False, False, False, True, True,
                 True, True, True, True, False, True, False, False, False, False, False, False, False, True]   # steps 2..31
        lo, hi, mids = 0.02, 3.0, {}
        for i, b in enumerate(below):
            mid = float(np.sqrt(lo * hi)); mids[i + 2] = mid
            if b:
                lo = mid
            else:
                hi = mid
        scales = [mids[int(s)] for s in a.steps.split(",")]
        print("exact bisection scales: " + ", ".join(f"step {s}: {mids[int(s)]:.10f}" for s in a.steps.split(",")))
    for scale in scales:
        theta = S.generator_theta(name, scale=scale, **kw)
        tr = S.make_dataset(name, theta, a.n_per_family, a.D, layers=(41,), rho=0.0, seed=a.seed)
        te = S.make_dataset(name, theta, a.n_per_family, a.D, layers=(41,), rho=0.0, seed=a.seed + 1)
        train = M.Trials.build(tr.y[:, 0], tr.k, tr.concept, tr.n_concepts)
        test = M.Trials.build(te.y[:, 0], te.k, te.concept, te.n_concepts, floor_sd=train.floor_sd)
        truth = M.Trials.build(te.y[:, 0], te.k, te.concept, te.n_concepts, floor_sd=0.0)
        lq_true = M.concept_scores(name, theta, truth, cfg.n_gh)
        # the start seed follows the member's index in FAMILY_G, as in simulate.expected_gain, whichever members are fitted
        fits = {g: M.fit(g, train, cfg.n_gh, cfg.n_starts, np.random.default_rng([a.seed, 7, M.FAMILY_G.index(g)])) for g in graded}
        best = max(graded, key=lambda g: fits[g].loglik)
        print(f"\n=== scale {scale:.10f}: y range train [{tr.y.min():.4f}, {tr.y.max():.4f}] mean {tr.y.mean():.6f}; best = {best}")
        for g in graded:
            f = fits[g]
            gain = float((lq_true.sum() - M.concept_scores(g, f.theta, test, cfg.n_gh).sum()) / test.n)
            print(f"  {g:4s} kept loglik {f.loglik:14.4f} conv {f.n_converged}/{f.n_starts} rec {f.recovery} "
                  f"gain vs truth {gain:.6f} theta {json.dumps([round(float(v), 5) for v in f.theta])}")
        f = fits[a.member]
        print(f"  --- every start of {a.member} (kept = the converged run with the best training loglik) ---")
        for r in f.runs:
            th = np.asarray(r["theta"])
            gain = (float((lq_true.sum() - M.concept_scores(a.member, th, test, cfg.n_gh).sum()) / test.n)
                    if np.all(np.isfinite(th)) else float("nan"))
            print(f"    start {r['start']}: loglik {r['loglik']:14.4f} conv {str(r['converged']):5s} nit {r['nit']:4d} "
                  f"gain {gain:.6f} theta {json.dumps([round(float(v), 5) for v in th])} {r.get('message', '')!r}")


if __name__ == "__main__":
    main()

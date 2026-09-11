#!/usr/bin/env python3
"""t1_access/bench.py — the §14 benchmark: one fit per member at confirmation size, then one full
layer of the §8 pipeline, on one core (XLA single-threaded), so that the simulation counts and the
frozen layer grid can be set from measured numbers (recorded in the pre-registration v1.2).

Sizes: outer training fold = 51 concepts x 168 trials (D = 4; 336 at D = 8); inner training fold
~38 concepts; held-out ~13 concepts.
"""
from __future__ import annotations

import argparse
import time as _time

import numpy as np

import analyze as A
import models as M
import simulate as S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--n-gh", type=int, default=M.GH_NODES_DEFAULT)
    ap.add_argument("--layer", action="store_true", help="also time one full layer of the §8 pipeline")
    ap.add_argument("--n-starts-inner", type=int, default=M.N_STARTS)
    a = ap.parse_args()
    ds = S.make_dataset("M3H", S.generator_theta("M3H", tau=0.5, sep=2.0), n_per_family=8, D=a.D, layers=(41,), rho=0.9, seed=1)
    folds = A.stratified_folds(ds.family, 5, seed=1)
    train_c = np.setdiff1d(np.arange(ds.n_concepts), folds[0])
    train = A._subset(ds.y[:, 0], ds.k, ds.concept, train_c)
    test = A._subset(ds.y[:, 0], ds.k, ds.concept, folds[0], train.floor_sd)
    print(f"D={a.D}: training fold {train.n} trials / {train.n_concepts} concepts; GH nodes {a.n_gh}")
    print(f"{'member':6s} {'compile s':>9s} {'fit s':>7s} {'per start':>9s} {'conv':>5s} {'nfev':>6s} {'score ms':>8s}")
    total = 0.0
    for name in M.ALL_MEMBERS:
        t0 = _time.time()
        f = M.objective(name, train, a.n_gh)
        f(M.start_from_moments(name, M.moments(train)))
        M.concept_scores(name, M.start_from_moments(name, M.moments(train)), test, a.n_gh)
        compile_s = _time.time() - t0
        r = M.fit(name, train, a.n_gh, rng=np.random.default_rng(0), recovery=False)
        t1 = _time.time()
        for _ in range(5):
            M.concept_scores(name, r.theta, test, a.n_gh)
        score_ms = (_time.time() - t1) / 5 * 1000
        total += r.seconds
        print(f"{name:6s} {compile_s:9.2f} {r.seconds:7.2f} {r.seconds / r.n_starts:9.3f} {r.n_converged:2d}/{r.n_starts:<2d} {r.nfev:6d} {score_ms:8.1f}")
    print(f"sum of the nine refits at 8 starts: {total:.1f} s")
    if a.layer:
        cfg = A.Config(n_gh=a.n_gh, n_starts_inner=a.n_starts_inner)
        t0 = _time.time()
        res = A.layer_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, folds, cfg, seed=1, layer_tag=41)
        wall = _time.time() - t0
        print(f"one layer, 5 outer folds x 8 members x (4 inner @ {a.n_starts_inner} starts + refit @ 8): "
              f"{wall:.0f} s wall, {res['fit_seconds']:.0f} s in fits, convergence {res['converged'].mean():.3f}, "
              f"selected {res['selected']}")
        for p in A.PREDICTORS:
            print(f"  {p}: mean Delta {np.nanmean(res['delta'][p]):.5f}")


if __name__ == "__main__":
    main()

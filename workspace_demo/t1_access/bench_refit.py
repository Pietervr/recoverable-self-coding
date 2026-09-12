"""bench_refit.py — time the corrected §8.2 refitting bootstrap: one CONF-sized dataset (8 concepts per family,
D = 4, one layer) through refit_bootstrap at n_rep replicates on one core, so the cost of the 200-replicate
interval (per dataset, per layer) and of its validation on new seeds can be projected honestly.

  NPROC=1 ./.venv/bin/python bench_refit.py [--n-rep 2] [--generator M2S --omega 0.5]
"""
import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze as A
import simulate as S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rep", type=int, default=2)
    ap.add_argument("--generator", default="M2S")
    ap.add_argument("--omega", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    cfg = A.Config(n_starts_inner=4)
    kw = dict(omega=a.omega) if a.generator == "M2S" else {}
    ds = S.make_dataset(a.generator, S.generator_theta(a.generator, **kw), n_per_family=8, D=4, layers=(41,), rho=0.0, seed=a.seed)
    t0 = time.time()
    out = A.refit_bootstrap(ds, cfg, seed=a.seed, n_rep=a.n_rep, predictor="selection")
    wall = time.time() - t0
    print(f"{a.generator} {kw}: refit_bootstrap n_rep={a.n_rep} on one core: {wall / 60:.1f} min wall, "
          f"{out['fit_seconds'] / 60:.1f} fit-min, {wall / a.n_rep / 60:.1f} min per replicate; "
          f"usable {out['usable']} used {out['n_used']} failed {out['n_failed']}; ws [{out['ws']['lo']:.5f}, {out['ws']['hi']:.5f}] se {out['ws']['se']:.5f}")
    print(f"projection: 200 replicates = {200 * wall / a.n_rep / 3600:.1f} core-hours per dataset per layer", flush=True)


if __name__ == "__main__":
    main()

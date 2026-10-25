"""Regeneration tie check: regenerate a saved row's dataset with the HISTORICAL code (the export whose config_hash equals
the row's code_hash), then refit two members' OUTER fits on every fold with the identical seeds and compare the per-concept
held-out joint log scores with the row's saved logq_per_concept. A regenerated dataset that is not the saved row's gives
O(1) differences; the saved row's gives agreement to rounding / platform precision.

usage: python tie_check.py <code_dir> <csv> <out_json> <n_jobs> <key> [<key> ...]      key = generator|grid_json|rep
"""
import os, sys, json, time
os.environ["NPROC"] = "1"
code_dir, csv_path, out_json, n_jobs = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
keys = [tuple(k.split("|")) for k in sys.argv[5:]]
sys.path.insert(0, code_dir)
import numpy as np
import pandas as pd
import analyze as A
import models as M
import simulate as S

MEMBERS_TO_FIT = ("M2B", "M3")
LAYERS = (41,)
D = 4
SEED = 2026


def ds_seed_for(name, kwargs, rep):
    if hasattr(S, "dataset_seed"):
        return S.dataset_seed(name, kwargs, rep, D, SEED)
    grid_tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in enumerate(kwargs.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    return int(np.random.default_rng([SEED, M.ALL_MEMBERS.index(name), grid_tag % (2**31 - 1), rep, D]).integers(2**31))


def one(row):
    cfg = A.Config(n_starts_inner=4)
    name, kwargs, rep = row["generator"], json.loads(row["grid"]), int(row["rep"])
    theta = S.generator_theta(name, **kwargs)
    ds_seed = ds_seed_for(name, kwargs, rep)
    ds = S.make_dataset(name, theta, n_per_family=8, D=D, layers=LAYERS, rho=S.RHO_LAYERS, seed=ds_seed)
    saved = json.loads(row["logq_per_concept"])
    outer = A.stratified_folds(ds.family, cfg.n_outer, ds_seed)
    y, k, concept = ds.y[:, 0], ds.k, ds.concept
    C = ds.family.size
    members = cfg.members
    out = dict(generator=name, grid=row["grid"], rep=rep, ds_seed=int(ds_seed), code_hash_saved=row["code_hash"],
               config_hash_here=S.config_hash(cfg, D, LAYERS, SEED), n_trials=int(y.size),
               y_mean=float(y.mean()), y_sd=float(y.std(ddof=1)), members={})
    t0 = time.time()
    for m in MEMBERS_TO_FIT:
        j = members.index(m)
        regen = np.full(C, np.nan)
        for f, test_c in enumerate(outer):
            train_c = np.setdiff1d(np.arange(C), test_c)
            floor_sd = float(np.std(y[np.isin(concept, train_c)], ddof=1))
            train = A._subset(y, k, concept, train_c, floor_sd)
            test = A._subset(y, k, concept, test_c, floor_sd)
            r = M.fit(m, train, cfg.n_gh, cfg.n_starts, A._rng(ds_seed, LAYERS[0], f, 3, j))
            regen[test_c] = M.concept_scores(m, r.theta, test, cfg.n_gh)
        sv = np.asarray(saved[m][0], dtype=float)
        diff = regen - sv
        out["members"][m] = dict(max_abs_diff=float(np.nanmax(np.abs(diff))), mean_abs_saved=float(np.mean(np.abs(sv))),
                                 max_rel_diff=float(np.nanmax(np.abs(diff) / np.abs(sv))),
                                 first3_saved=sv[:3].tolist(), first3_regen=regen[:3].tolist())
    out["seconds"] = round(time.time() - t0, 1)
    return out


df = pd.read_csv(csv_path, usecols=["generator", "grid", "rep", "code_hash", "logq_per_concept", "selection_decision"])
rows = []
for g, grid, rep in keys:
    sub = df[(df["generator"] == g) & (df["grid"] == grid) & (df["rep"] == int(rep))]
    if len(sub) != 1:
        raise SystemExit(f"key {(g, grid, rep)} matched {len(sub)} rows")
    rows.append(sub.iloc[0].to_dict())
from joblib import Parallel, delayed
res = Parallel(n_jobs=n_jobs)(delayed(one)(r) for r in rows)
with open(out_json, "w") as fh:
    json.dump(res, fh, indent=1)
for r in res:
    print(r["generator"], r["grid"], "rep", r["rep"], "ds_seed", r["ds_seed"], "hash", r["code_hash_saved"], "==", r["config_hash_here"],
          "| " + "; ".join(f"{m}: max|diff| {v['max_abs_diff']:.2e} (rel {v['max_rel_diff']:.1e}, |saved| ~{v['mean_abs_saved']:.1f})" for m, v in r["members"].items()),
          f"| {r['seconds']} s")

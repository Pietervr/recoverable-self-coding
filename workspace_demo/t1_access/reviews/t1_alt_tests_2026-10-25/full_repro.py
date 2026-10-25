"""Full-procedure reproduction of ONE saved row with the historical code: regenerate the dataset, run analyze_dataset with the
row's seed, compare the saved verdict, interval endpoints, held-out scores per member and every per-concept score.
usage: python full_repro.py <code_dir> <csv> <out_json> <generator> <grid_json> <rep>"""
import os, sys, json, time
os.environ["NPROC"] = "1"
code_dir, csv_path, out_json, name, grid, rep = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6])
sys.path.insert(0, code_dir)
import numpy as np
import pandas as pd
import analyze as A
import models as M
import simulate as S

D, LAYERS, SEED = 4, (41,), 2026
df = pd.read_csv(csv_path)
sub = df[(df["generator"] == name) & (df["grid"] == grid) & (df["rep"] == rep)]
assert len(sub) == 1, len(sub)
row = sub.iloc[0].to_dict()
kwargs = json.loads(grid)
cfg = A.Config(n_starts_inner=4)
if hasattr(S, "dataset_seed"):
    ds_seed = S.dataset_seed(name, kwargs, rep, D, SEED)
else:
    grid_tag = sum((i + 1) * int(round(1000 * float(v))) for i, v in enumerate(kwargs.get(x, 0.0) for x in ("tau", "omega", "sep", "pi0", "alpha", "scale")))
    ds_seed = int(np.random.default_rng([SEED, M.ALL_MEMBERS.index(name), grid_tag % (2**31 - 1), rep, D]).integers(2**31))
t0 = time.time()
theta = S.generator_theta(name, **kwargs)
ds = S.make_dataset(name, theta, n_per_family=8, D=D, layers=LAYERS, rho=S.RHO_LAYERS, seed=ds_seed)
res = A.analyze_dataset(ds, cfg, seed=ds_seed)
secs = time.time() - t0
out = dict(generator=name, grid=grid, rep=rep, ds_seed=int(ds_seed), seconds=round(secs, 1),
           config_hash_here=S.config_hash(cfg, D, LAYERS, SEED), code_hash_saved=row["code_hash"])
for p in A.PREDICTORS:
    b = res["predictors"][p]
    out[p] = dict(decision_regen=b["decision"], decision_saved=row[f"{p}_decision"],
                  ws=dict(regen=[b["ws"][k] for k in ("point", "lo", "hi", "se")],
                          saved=[row[f"{p}_ws_{k}"] for k in ("point", "lo", "hi", "se")]))
out["heldout_regen"] = {m: round(v, 5) for m, v in res["heldout_logscore_per_trial"].items()}
out["heldout_saved"] = json.loads(row["heldout"])
saved_logq = json.loads(row["logq_per_concept"])
out["logq_max_abs_diff"] = {m: float(np.max(np.abs(res["logq"][0, i, :] - np.asarray(saved_logq[m][0])))) for i, m in enumerate(res["members"])}
out["selected_regen"] = res["selected_counts"]
out["selected_saved"] = json.loads(row["selected"])
out["failed"] = bool(res["failed"])
with open(out_json, "w") as fh:
    json.dump(out, fh, indent=1, default=float)
print(json.dumps(out, indent=1, default=float))

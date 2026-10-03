"""Dump a rep's generated response array (and k) to .npy for a cross-machine comparison. Run from workspace_demo/t1_access:
  python rep_dump_y.py <rep> <out_prefix>"""
import json, os, sys
sys.path.insert(0, os.getcwd())
import numpy as np
import analyze as A, simulate as S
man = json.load(open("chpc/row19_slice_manifest.json"))
st = man["setting"]
rep = int(sys.argv[1]); out = sys.argv[2]
kw = dict(st["grid"]); theta = S.generator_theta(st["generator"], **kw)
seed = S.dataset_seed(st["generator"], kw, rep, int(st["D"]), int(man["datasets"]["seed_base"]))
ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]), layers=np.array(st["layers"]), rho=float(st["rho"]), seed=seed)
np.save(out + "_y.npy", np.asarray(ds.y, dtype=np.float64))
np.save(out + "_k.npy", np.asarray(ds.k, dtype=np.float64))
print("saved", out, "rep", rep, "seed", seed, "y", np.asarray(ds.y).shape, "dtype", np.asarray(ds.y).dtype)

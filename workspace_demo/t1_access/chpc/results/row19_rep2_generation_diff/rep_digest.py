"""Per-rep dataset digests for the row 19 slice (no fit): the sha256 of each array's bytes, the folds, theta and the identity
computed with the binding's numerical snapshot (if a task binding path is given). Run from workspace_demo/t1_access on either machine:
  python rep_digest.py <rep> [task_json]"""
import hashlib, json, os, sys
sys.path.insert(0, os.getcwd())
import numpy as np
import analyze as A, simulate as S
man = json.load(open("chpc/row19_slice_manifest.json"))
st, c = man["setting"], man["cfg"]
cfg = A.Config(start_policy=c["start_policy"], interval=c["interval"], n_boot_refit=int(c["n_boot_refit"]), n_starts=int(c["n_starts"]),
               n_starts_inner=int(c["n_starts_inner"]), refit_min_usable=float(c["refit_min_usable"]), n_outer=int(c["n_outer"]), n_inner=int(c["n_inner"]))
rep = int(sys.argv[1])
kw = dict(st["grid"]); theta = S.generator_theta(st["generator"], **kw)
seed = S.dataset_seed(st["generator"], kw, rep, int(st["D"]), int(man["datasets"]["seed_base"]))
ds = S.make_dataset(st["generator"], theta, n_per_family=int(st["n_per_family"]), D=int(st["D"]), layers=np.array(st["layers"]), rho=float(st["rho"]), seed=seed)
ds.meta.update(generator=st["generator"], theta=[float(x) for x in theta], D=int(st["D"]), rho=float(st["rho"]), seed=seed)
folds = A.stratified_folds(ds.family, cfg.n_outer, seed)
print("rep", rep, "seed", seed, "theta", [repr(float(x)) for x in theta])
for name in ("y", "k", "concept", "family", "layers"):
    a = np.ascontiguousarray(np.asarray(getattr(ds, name), dtype=np.float64))
    print(f"  {name:8s} shape {a.shape} sha {hashlib.sha256(a.tobytes()).hexdigest()[:16]} sum {float(a.sum())!r}")
print("  group", None if ds.group is None else hashlib.sha256(np.ascontiguousarray(np.asarray(ds.group, dtype=np.int64)).tobytes()).hexdigest()[:16])
print("  folds sha", hashlib.sha256(json.dumps([[int(x) for x in f] for f in folds]).encode()).hexdigest()[:16], "sizes", [len(f) for f in folds])
print("  meta", json.dumps({k: ds.meta.get(k) for k in ("generator", "theta", "D", "rho", "seed")}, default=str)[:200])
snap = None
if len(sys.argv) > 2:
    d = json.load(open(sys.argv[2])); b = d.get("binding") or d
    snap = b.get("numerical")
    print("  binding ident", b["ident"][:16], "n_rep", b["n_rep"])
ident = A.dataset_identity(ds, cfg, seed, int(cfg.n_boot_refit), folds, numerical=snap)
print("  identity", ident[:16], "(with binding snapshot)" if snap else "(local snapshot)")
loc = A.numerical_snapshot()
print("  local snapshot runtime", loc.get("runtime"), "files", loc.get("files"))

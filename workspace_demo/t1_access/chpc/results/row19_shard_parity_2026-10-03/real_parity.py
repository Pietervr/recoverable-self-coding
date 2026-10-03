"""REAL-fit parity (no stub) on a tiny configuration: the shard worker's records against the sequential refit_bootstrap's records."""
import os, sys, json, time, tempfile
os.environ.setdefault("NPROC", "1")
T1 = "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access"
os.chdir(T1); sys.path.insert(0, T1); sys.path.insert(0, os.path.join(T1, "chpc"))
import numpy as np
import analyze as A
import row19_shard as SH
from test_row19_slice import _manifest
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
d = tempfile.mkdtemp(); man = _manifest(d, os.path.join(d, "campaign"), n_boot=8)
t = SH.task(man, 0)
print("dataset", t["ds"].y.shape, "concepts", t["ds"].n_concepts, "identity", t["ident"][:16], flush=True)
t0 = time.time()
ck = os.path.join(d, "seq.jsonl")
rb = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], t["n_rep"], outer_folds=t["folds"], checkpoint_path=ck, until=N, durable=True)
print(f"sequential: {rb['n_new']} resamples in {time.time()-t0:.1f} s", flush=True)
seq = {r["rep"]: r for r in (json.loads(l) for l in open(ck).read().splitlines() if l.strip())}
ok = True
for i in reversed(range(N)):                      # another order, each index on its own
    t1 = time.time(); r = SH.resample_record(t, i)
    same = all(r[k] == seq[i][k] for k in ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep"))
    ok = ok and same and A._record_ok(r, t["ident"], t["seed"], t["n_rep"], t["idx"], t["bands"])
    print(f"index {i}: shard {time.time()-t1:.1f} s, bitwise equal to the sequential record: {same}; failed={r['failed']}; stats {json.dumps(r['stats'])[:90]}", flush=True)
print("REAL PARITY:", "PASS" if ok else "FAIL")

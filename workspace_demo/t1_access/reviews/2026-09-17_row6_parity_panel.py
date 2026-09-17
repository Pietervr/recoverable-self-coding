"""Ledger row 6, cross-machine parity panel. Re-runs three AWS sens600 datasets on the Mac and
compares them against their stored rows. Prints only maximum deviations and a decision-agreement
boolean: never which decision a setting returned, so the blinded read stays sealed."""
import os
os.environ["NPROC"] = "1"                      # before jax is imported (jax-cpu-thread-pinning rule)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import sys, csv, json, time
sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access")
os.chdir("/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access")
import analyze as A, simulate as S
from joblib import Parallel, delayed

AWS_CSV = "/private/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/ced0f2b1-fb5f-48d8-b54c-3a1e91f50686/scratchpad/s600/power_D4.shard000of020.csv"
GAIN = "sim_results/gain_sens600/gain_calibration_D4.json"
SEED, D, LAYERS = 2026, 4, (41,)
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")
TOL = 1e-6

cfg = A.Config(n_starts_inner=4, interval="cluster")
code_hash = S.config_hash(cfg, D, LAYERS, SEED)
print(f"local code/config hash: {code_hash}", flush=True)

rows = list(csv.DictReader(open(AWS_CSV)))
panel = rows[:3]                                # declared by file position, never by outcome
for r in panel:
    assert r["code_hash"] == code_hash, f"code hash mismatch: row {r['code_hash']} vs local {code_hash}"

points, extras = S.power_points(GAIN)
ex = {}
for (name, kw) in points:
    ex[(name, json.dumps(kw, sort_keys=True))] = extras.get((name, json.dumps(kw, sort_keys=True)))

jobs = []
for r in panel:
    kw = json.loads(r["grid"])
    jobs.append((r["generator"], kw, int(r["rep"])))
print("panel:", [(n, json.dumps(k, sort_keys=True), rp) for n, k, rp in jobs], flush=True)

t0 = time.time()
out = Parallel(n_jobs=3)(
    delayed(S.one_replicate)(n, k, rp, D, LAYERS, None, cfg, SEED,
                             ex.get((n, json.dumps(k, sort_keys=True))), code_hash)
    for n, k, rp in jobs)
print(f"local re-run of three datasets: {(time.time() - t0)/60:.1f} min", flush=True)

worst = {q: 0.0 for q in NUM}
decisions_identical = True
failures = []
for r, m in zip(panel, out):
    for q in NUM:
        a, b = r.get(q, ""), m.get(q, "")
        if a == "" or b is None:
            failures.append(f"{q} missing (aws={a!r} mac={b!r})")
            continue
        d = abs(float(a) - float(b))
        worst[q] = max(worst[q], d)
    if str(r["selection_decision"]) != str(m.get("selection_decision")):
        decisions_identical = False
    if str(m.get("failed", "0")) not in ("0", "False", "false"):
        failures.append(f"local re-run reported failed={m.get('failed')} reason={m.get('failed_reason')}")

print("\nROW 6 PARITY PANEL - arm64 (Mac) against x86_64 (AWS), one code hash")
print(f"  datasets compared:      {len(panel)}")
for q in NUM:
    print(f"  max |delta| {q:<22} {worst[q]:.3e} nat/trial")
print(f"  decisions identical:    {decisions_identical}")
print(f"  technical failures:     {failures if failures else 'none'}")
ok = all(worst[q] <= TOL for q in NUM) and decisions_identical and not failures
print(f"\n  tolerance 1e-6 nat/trial on every quantity, decisions identical")
print(f"  VERDICT: {'PASS - Mac and AWS rows may be pooled for row 2' if ok else 'FAIL - rows from the two machines may NOT be pooled'}")
print("\n  (Which decision each setting returned is deliberately not printed: sens600 stays blinded.)")

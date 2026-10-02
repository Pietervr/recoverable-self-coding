"""Ledger row 6, the cross-machine parity panel extended to CHPC Lengau (owner's go, 2 October 2026).

Re-runs the three declared sens600 datasets - M3, scale 0.5465000938917843, reps 0, 20, 40, chosen on 17 September by
file position in the AWS shard and recorded by content in row 6 - on Lengau through `simulate.one_replicate` with
byte-identical arguments (code/config hash 625798e9e7f4 at f7e69b1, seed 2026, D = 4, layers (41,), rho default,
Config(n_starts_inner=4, interval="cluster"), B = 2000, the power_points extras of that point) and writes ONLY the
compared quantities per dataset to a CSV. The comparison against the stored AWS rows runs on the Mac
(`row6_lengau_compare.py`), which prints maximum deviations and a decision-agreement boolean and never which decision a
setting returned, so sens600 stays blinded. Nothing here reads the AWS rows."""
import os
os.environ["NPROC"] = "1"                      # before jax is imported
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import sys, csv, json, time, platform
# the PBS job cds into t1_access before running; the script is copied to the toolchain's jobs/ directory, so the
# code directory is the current working directory when it holds analyze.py, else the script's parent (local runs)
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.getcwd() if os.path.exists(os.path.join(os.getcwd(), "analyze.py")) else os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, T1)
os.chdir(T1)
import analyze as A, simulate as S

GAIN = "sim_results/gain_sens600/gain_calibration_D4.json"
SEED, D, LAYERS = 2026, 4, (41,)
EXPECTED_HASH = "625798e9e7f4"
PANEL = [("M3", {"scale": 0.5465000938917843}, 0),
         ("M3", {"scale": 0.5465000938917843}, 20),
         ("M3", {"scale": 0.5465000938917843}, 40)]
NUM = ("selection_ws_point", "selection_ws_lo", "selection_ws_hi", "selection_ws_se")
OUT = sys.argv[1] if len(sys.argv) > 1 else "row6_lengau_rows.csv"
# which declared reps this process runs: all three sequentially by default, or one (single-core jobs). The toolchain's
# joblib workers cannot spawn under the image loader (a child python finds the host libc), so no process parallelism.
REPS = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0, 20, 40]
PANEL = [(n, k, rp) for (n, k, rp) in PANEL if rp in REPS]
assert PANEL, "no declared rep selected"

cfg = A.Config(n_starts_inner=4, interval="cluster")
code_hash = S.config_hash(cfg, D, LAYERS, SEED)
print(f"code/config hash: {code_hash}  (expected {EXPECTED_HASH})", flush=True)
assert code_hash == EXPECTED_HASH, "code/config hash differs from the AWS panel: stop"

points, extras = S.power_points(GAIN)
ex = {}
for (name, kw) in points:
    ex[(name, json.dumps(kw, sort_keys=True))] = extras.get((name, json.dumps(kw, sort_keys=True)))
print("panel:", [(n, json.dumps(k, sort_keys=True), rp) for n, k, rp in PANEL], flush=True)

t0 = time.time()
out = [S.one_replicate(n, k, rp, D, LAYERS, None, cfg, SEED, ex.get((n, json.dumps(k, sort_keys=True))), code_hash)
       for n, k, rp in PANEL]                       # sequential, one process, one core
wall = (time.time() - t0) / 60
print(f"lengau re-run of {len(PANEL)} dataset(s) {REPS}: {wall:.1f} min wall", flush=True)

import numpy, scipy, joblib, jax, jaxlib
env = (f"python {sys.version.split()[0]} jax {jax.__version__} jaxlib {jaxlib.__version__} numpy {numpy.__version__} "
       f"scipy {scipy.__version__} joblib {joblib.__version__} {platform.machine()} {platform.node()}")
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["generator", "grid", "rep", "code_hash", *NUM, "selection_decision", "failed", "failed_reason",
                "fit_seconds", "env"])
    for (n, k, rp), m in zip(PANEL, out):
        w.writerow([n, json.dumps(k, sort_keys=True), rp, code_hash,
                    *[m.get(q) for q in NUM], m.get("selection_decision"), m.get("failed", 0),
                    m.get("failed_reason", ""), m.get("fit_seconds", ""), env])
print(f"wrote {OUT}: {len(PANEL)} row(s) (quantities only; the comparison runs on the Mac)", flush=True)
print("technical failures:", [m.get("failed_reason") for m in out if str(m.get("failed", "0")) not in ("0", "False", "false")] or "none")

"""JOB D seed manifest, the part Codex's check left open (record 2026-09-15_t1_pc_nested_start_policy_codex_record.md §4):
the omega-2 reference bank and the M2B refit control. Same method as 2026-09-15_job_d_seed_cost_checks.py: dataset_seed
isolated by AST, no project imports, no data generation or fits. Base seeds and rep ranges come from the SageMaker job
environments (read 15 Sept 2026 with the xtenure-read profile), passed on the command line.

usage: python 2026-09-15_job_d_seed_manifest_extension.py --bank-seed 2028 --bank-reps 1000 --control-seed 2027 \
           --control-reps 10 --control-B 50 --probe-seed 2027 --probe-reps 20 --probe-B 50
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import platform
from types import SimpleNamespace

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--bank-seed", type=int, required=True)
ap.add_argument("--bank-reps", type=int, required=True)
ap.add_argument("--control-seed", type=int, required=True)
ap.add_argument("--control-reps", type=int, required=True)
ap.add_argument("--control-B", type=int, required=True)
ap.add_argument("--probe-seed", type=int, required=True)
ap.add_argument("--probe-reps", type=int, required=True)
ap.add_argument("--probe-B", type=int, required=True)
a = ap.parse_args()

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "simulate.py").read_text()
constants = {}
for node in ast.parse((ROOT / "models.py").read_text()).body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("FAMILY_G", "FAMILY_X", "ALL_MEMBERS")
                                            for t in node.targets):
        exec(compile(ast.Module(body=[node], type_ignores=[]), "models-constants-only", "exec"), constants)
seed_node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "dataset_seed")
ns = {"np": np, "json": json, "hashlib": hashlib, "M": SimpleNamespace(ALL_MEMBERS=constants["ALL_MEMBERS"])}
exec(compile(ast.Module(body=[seed_node], type_ignores=[]), "dataset-seed-only", "exec"), ns)
seed_for = ns["dataset_seed"]

# the 24 JOB D seeds, recomputed and checked against Codex's table
points = [("M2S", {"omega": 2}), ("M2S", {"omega": 1}), ("M2B", {}), ("M3H", {"sep": 2, "tau": 0.5})]
jobd = [dict(member=m, kwargs=kw, rep=r, seed=seed_for(m, kw, r, 4, 20260915)) for m, kw in points for r in range(6)]
codex = json.loads((ROOT / "reviews/2026-09-15_job_d_seed_cost_checks.json").read_text())["seeds"]
assert [r["seed"] for r in jobd] == [r["seed"] for r in codex], "JOB D seeds differ from Codex's table"
jobd_seeds = {r["seed"] for r in jobd}
assert len(jobd_seeds) == 24

bank = {seed_for("M2S", {"omega": 2.0}, r, 4, a.bank_seed) for r in range(a.bank_reps)}
control = {seed_for("M2B", {}, r, 4, a.control_seed) for r in range(a.control_reps)}
probe = {seed_for("M2S", {"omega": float(w)}, r, 4, a.probe_seed) for w in (1, 2) for r in range(a.probe_reps)}
# analyze.refit_bootstrap fits resample `rep` through run_dataset(sub, cfg, seed + 1 + rep): every refit stream is rooted
# at an integer OFFSET of its dataset seed, which can land on another run's dataset seed
def refit_roots(seeds, B):
    return {s + 1 + r for s in seeds for r in range(B)}
comparisons = {}
for label, seeds in ((f"omega2_bank_M2S_omega2_reps0_{a.bank_reps - 1}_base{a.bank_seed}_datasets", bank),
                     (f"refit_control_M2B_reps0_{a.control_reps - 1}_base{a.control_seed}_datasets", control),
                     (f"refit_control_refit_roots_seed_plus_1_plus_rep_B{a.control_B}", refit_roots(control, a.control_B)),
                     (f"probe_M2S_omega1_2_reps0_{a.probe_reps - 1}_base{a.probe_seed}_refit_roots_B{a.probe_B}",
                      refit_roots(probe, a.probe_B))):
    comparisons[label] = dict(unique_seeds=len(seeds), overlap=sorted(seeds & jobd_seeds))
# the reverse direction: a JOB D dataset seed within B of a historical dataset seed is the same event as above; JOB D
# itself runs the cluster interval only, so it creates no offset roots of its own
nearest = {}
for label, seeds in (("bank", bank), ("control", control), ("probe", probe)):
    arr = np.array(sorted(seeds))
    nearest[label] = int(min(np.min(np.abs(arr - s)) for s in jobd_seeds))

result = dict(
    method="AST-isolated dataset_seed plus NumPy; base seeds and rep ranges from the SageMaker job environments",
    python=platform.python_version(), numpy=np.__version__,
    dataset_seed_source_sha256=hashlib.sha256(ast.get_source_segment(source, seed_node).encode()).hexdigest(),
    jobd_seeds_equal_codex_table=True, comparisons=comparisons,
    nearest_distance_jobd_to_historical_dataset_seed=nearest,
    also_checked=("us-west-2 smoke t1-calibration-d4-smoke-usw2-1789342209: SEED 2026, M2B, N_REP 1, INTERVAL cluster — its "
                  "dataset is d4v12b's M2B rep 0, inside Codex's d4v12b enumeration, and a cluster run makes no refit roots; "
                  "the failed first control attempt 1789319939 used the same SEED 2027, M2B, N_REP 10 and namespace"),
    stream_note=("Every stream of a dataset is rooted in its dataset seed: outer folds stratified_folds(family, n_outer, seed), "
                 "inner folds and fits _rng(seed, layer_tag, ...), the cluster bootstrap band_bootstrap(..., seed) and the "
                 "refitting bootstrap default_rng(seed), with seed = the dataset seed (simulate.one_replicate). Distinct dataset "
                 "seeds therefore give distinct stream roots. Derived 31-bit intermediate integers (the inner-fold seed) are not "
                 "enumerated."))
out = Path(__file__).with_suffix(".json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(comparisons, indent=2))

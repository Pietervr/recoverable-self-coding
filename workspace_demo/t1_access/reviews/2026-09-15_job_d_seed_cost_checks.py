"""JOB D review arithmetic only: no project imports, data generation or fits."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(sys.maxsize)
source = (ROOT / "simulate.py").read_text()
model_tree = ast.parse((ROOT / "models.py").read_text())
constants = {}
for node in model_tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in ("FAMILY_G", "FAMILY_X", "ALL_MEMBERS")
        for t in node.targets
    ):
        exec(compile(ast.Module(body=[node], type_ignores=[]), "models-constants-only", "exec"), constants)
seed_node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "dataset_seed")
namespace = {"np": np, "json": json, "hashlib": hashlib,
             "M": SimpleNamespace(ALL_MEMBERS=constants["ALL_MEMBERS"])}
exec(compile(ast.Module(body=[seed_node], type_ignores=[]), "dataset-seed-only", "exec"), namespace)
seed_for = namespace["dataset_seed"]
points = [("M2S", {"omega": 2}), ("M2S", {"omega": 1}),
          ("M2B", {}), ("M3H", {"sep": 2, "tau": 0.5})]
proposed = [dict(member=m, kwargs=kw, rep=r, D=4, base=20260915,
                 seed=seed_for(m, kw, r, 4, 20260915))
            for m, kw in points for r in range(6)]
proposed_seeds = {r["seed"] for r in proposed}
assert len(proposed_seeds) == 24
assert all(0 <= s < 2**31 for s in proposed_seeds)

# Compare only the historical datasets enumerated here; this is not a universal
# historical-stream or bootstrap-stream audit. Read CSV identity columns only.
historical_keys = set()
historical_files = []
for path in sorted((ROOT / "sim_results/d4v12b").glob("calibration_D4.shard*.csv")):
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode().splitlines()))
    historical_files.append(dict(path=str(path.relative_to(ROOT)), rows=len(rows),
                                 sha256=hashlib.sha256(raw).hexdigest()))
    for row in rows:
        historical_keys.add((row["generator"], json.dumps(json.loads(row["grid"]), sort_keys=True),
                             int(row["rep"]), int(row["D"])))
historical = {seed_for(m, json.loads(kw), r, d, 2026) for m, kw, r, d in historical_keys}
probe = {seed_for("M2S", {"omega": w}, r, 4, 2027) for w in (1, 2) for r in range(20)}
audit = {500000 + r for r in range(6)}
comparisons = {}
for label, seeds in (("d4v12b_local_shard_dataset_identities_base2026", historical),
                     ("probe_M2S_omega1_2_reps0_19_base2027", probe),
                     ("audit_500000_plus_reps0_5", audit)):
    comparisons[label] = dict(unique_seeds=len(seeds), overlap=sorted(seeds & proposed_seeds))
    assert not comparisons[label]["overlap"]

timing_path = ROOT / "reviews/2026-09-14_fitter_evidence_checks.json"
timings = json.loads(timing_path.read_text())["timing_extrapolations_not_new_benchmarks"]["full_96"]["table"]
added = dict(M3H=32, M2H=64, M2S=64, M2B=80, M3=80, M3V=80, M3L=80, M2K=80)
cost_rows = {}
for key, row in timings.items():
    member, size = key.split("/")
    multiplicity = 20 if size == "inner" else 5
    policy_seconds = row["cold_seconds"] + added[member] * row["added_seconds_per_start"]
    cost_rows[key] = dict(cold_seconds=row["cold_seconds"],
                         added_seconds_per_start=row["added_seconds_per_start"],
                         added_starts=added[member], policy_seconds=policy_seconds,
                         fits_per_dataset=multiplicity,
                         nested_cold_seconds=multiplicity * row["cold_seconds"],
                         nested_policy_seconds=multiplicity * policy_seconds)
cold = sum(r["nested_cold_seconds"] for r in cost_rows.values())
policy = sum(r["nested_policy_seconds"] for r in cost_rows.values())
assert abs(cold - 5766.015625) < 1e-9

def blob(path):
    return subprocess.check_output(["git", "-C", str(ROOT), "hash-object", str(path)], text=True).strip()

result = dict(
    method="AST-isolated dataset_seed plus NumPy; CSV identities and existing timing arithmetic only",
    python=platform.python_version(), numpy=np.__version__, bit_generator=type(np.random.default_rng(0).bit_generator).__name__,
    models_blob=blob(ROOT / "models.py"), analyze_blob=blob(ROOT / "analyze.py"),
    simulate_blob=blob(ROOT / "simulate.py"),
    dataset_seed_source_sha256=hashlib.sha256(ast.get_source_segment(source, seed_node).encode()).hexdigest(),
    member_order=list(constants["ALL_MEMBERS"]), seeds=proposed, unique_seeds=len(proposed_seeds),
    historical_comparisons=comparisons, d4v12b_unique_dataset_identities=len(historical_keys),
    d4v12b_sources=historical_files,
    exclusions="No omega-2 bank/control/bootstrap/reference stream enumeration; no dataset hashes generated",
    timing_source_sha256=hashlib.sha256(timing_path.read_bytes()).hexdigest(),
    linear_extrapolation_not_benchmark=dict(table=cost_rows, cold_seconds=cold, policy_seconds=policy,
        multiplier=policy/cold, summed_worker_elapsed_hours_per_dataset=policy/3600,
        summed_worker_elapsed_hours_24=24*policy/3600,
        summed_worker_elapsed_hours_20=20*policy/3600,
        ideal_24_wall_hours_at_same_seven_worker_rates=24*policy/3600/7,
        ideal_20_wall_hours_at_same_seven_worker_rates=20*policy/3600/7,
        caveat="Historical loaded worker elapsed rates; not CPU, not new wall benchmark; do not apply another contention discount"))
out = Path(__file__).with_suffix(".json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("unique_seeds", "historical_comparisons", "d4v12b_unique_dataset_identities")}, indent=2))
print(json.dumps({k: v for k, v in result["linear_extrapolation_not_benchmark"].items() if k != "table"}, indent=2))

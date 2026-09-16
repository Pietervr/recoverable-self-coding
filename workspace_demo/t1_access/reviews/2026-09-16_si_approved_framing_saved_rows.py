"""Verify reported decision counts from saved d4v12b rows; stdlib only.

No fitting, generation, resampling, simulation module import, or input mutation.
The containment statistic uses each setting's saved replicate mean, not a known
population target. It is a descriptive plug-in diagnostic, not validation.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(path):
    before = sha256(path)
    grouped = defaultdict(list)
    keys = set()
    hashes = Counter()
    predictors = ("selection", "ensemble", "historical")
    totals = {p: Counter() for p in predictors}
    failed = Counter()
    csv.field_size_limit(16 * 1024 * 1024)
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            grid = json.dumps(json.loads(row["grid"]), sort_keys=True)
            group = (row["generator"], grid)
            key = (*group, int(row["D"]), int(row["rep"]))
            assert key not in keys, ("duplicate dataset", key)
            keys.add(key)
            assert int(row["D"]) == 4 and int(row["n_layers"]) == 1, key
            assert row["family"] == "G", key
            hashes[row["code_hash"]] += 1
            failed[row["failed"]] += 1
            assert int(row["failed"]) == 0, ("recorded failure", key)
            compact = {"rep": int(row["rep"])}
            for predictor in predictors:
                values = {field: float(row[f"{predictor}_ws_{field}"])
                          for field in ("point", "lo", "hi", "se")}
                assert all(math.isfinite(value) for value in values.values()), key
                assert values["lo"] <= values["hi"] and values["se"] >= 0, key
                decision = ("mixture" if values["lo"] > 0 else
                            "graded" if values["hi"] < 0 else "inconclusive")
                assert decision == row[f"{predictor}_decision"], (key, predictor)
                totals[predictor][decision] += 1
                compact[predictor] = {**values, "decision": decision}
            grouped[group].append(compact)
    assert len(keys) == 12000 and len(grouped) == 12
    assert len(hashes) == 1, hashes
    table = []
    for (generator, grid), rows in sorted(grouped.items()):
        assert len(rows) == 1000 and {row["rep"] for row in rows} == set(range(1000))
        points = [row["selection"]["point"] for row in rows]
        reference = statistics.fmean(points)
        contains = sum(row["selection"]["lo"] <= reference <= row["selection"]["hi"]
                       for row in rows)
        table.append({
            "generator": generator, "grid": json.loads(grid), "n": len(rows),
            "counts": {p: dict(Counter(row[p]["decision"] for row in rows)) for p in predictors},
            "selection_replicate_mean": reference,
            "selection_replicate_mean_sample_se": statistics.stdev(points) / math.sqrt(len(rows)),
            "selection_intervals_containing_replicate_mean": contains,
            "selection_plugin_containment": contains / len(rows),
        })
    after = sha256(path)
    assert before == after, "Input changed during the read"
    return {
        "input": str(path), "input_bytes": path.stat().st_size, "input_sha256": before,
        "input_unchanged": True, "datasets": len(keys), "settings": len(table),
        "row_code_hashes": dict(hashes), "recorded_failed": dict(failed),
        "interval_signs_match_stored_decisions": True,
        "all_three_predictors_have_finite_point_interval_se": True,
        "totals": {p: dict(counts) for p, counts in totals.items()}, "per_setting": table,
        "zero_call_upper_95_per_setting": -math.expm1(math.log(0.05) / 1000),
        "scope": "Saved-row verification only; no fits, generation, bootstrap, or scientific runner. "
                 "Containment uses same-sample replicate means and is not independent coverage validation. "
                 "The historical predictor uses the T1 interval rule, not the human PXP pipeline.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path(__file__).resolve().parents[1] /
                        "sim_results/d4v12b/calibration_D4.csv")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert args.csv.resolve() != args.out.resolve()
    result = audit(args.csv)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("datasets", "settings", "input_sha256", "input_unchanged", "totals")}, indent=2))
    for row in result["per_setting"]:
        print(row["generator"], json.dumps(row["grid"], sort_keys=True),
              "historical", row["counts"]["historical"],
              "primary plug-in containment", row["selection_plugin_containment"])


if __name__ == "__main__":
    main()

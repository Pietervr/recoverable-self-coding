"""Read landed rows and calculate review diagnostics; no model fits or simulations.

Run with t1_access/.venv/bin/python. JSON is printed to stdout.
"""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta, binom


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sim_results/d4v12b/calibration_D4.csv"
csv.field_size_limit(10_000_000)
groups = defaultdict(list)
identities = Counter()
hashes = Counter()
state_before = SOURCE.stat()
with SOURCE.open(newline="") as handle:
    for row in csv.DictReader(handle):
        key = (row["generator"], row["grid"])
        groups[key].append({field: float(row[field]) for field in (
            "selection_ws_point", "selection_ws_lo", "selection_ws_hi",
            "selection_ws_se", "failed", "n_layers", "D")})
        identities[(key, row["rep"], row["D"], row["n_layers"])] += 1
        hashes[row["code_hash"]] += 1
state_after = SOURCE.stat()
out = dict(source=str(SOURCE), sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           n_rows=sum(identities.values()), duplicates=sum(n - 1 for n in identities.values()),
           hashes=dict(hashes), changed_while_reading=(state_before.st_size, state_before.st_mtime_ns)
           != (state_after.st_size, state_after.st_mtime_ns), groups=[])
for (name, grid), rows in sorted(groups.items()):
    good = [r for r in rows if r["failed"] == 0 and math.isfinite(r["selection_ws_point"])]
    pts = np.array([r["selection_ws_point"] for r in good])
    se = pts.std(ddof=1) / math.sqrt(len(pts))
    k = math.ceil(.95 * (len(pts) + 1))
    out["groups"].append(dict(generator=name, grid=json.loads(grid), n=len(rows),
        valid=len(good), n_layers=sorted({r["n_layers"] for r in rows}),
        D=sorted({r["D"] for r in rows}), mean=float(pts.mean()), reference_mcse=float(se),
        median=float(np.median(pts)), q95_linear=float(np.quantile(pts, .95)),
        rank=k, rank_critical=float(np.sort(pts)[k - 1]),
        min=float(pts.min()), max=float(pts.max()), positive=int((pts > 0).sum()),
        coverage_at_reference_offsets={str(offset):float(np.mean([
            r["selection_ws_lo"] <= pts.mean() + offset * se <= r["selection_ws_hi"] for r in good
        ])) for offset in (-2, 0, 2)}))
out["critical_max"] = max(r["rank_critical"] for r in out["groups"])
out["q95_linear_max"] = max(r["q95_linear"] for r in out["groups"])
out["positive_total"] = sum(r["positive"] for r in out["groups"])

# Exact binomial intervals (two-sided 95%) and one-sided lower limits, not Wald intervals.
out["coverage_count_examples"] = [dict(n=n, covered=x,
    two_sided_95=[float(beta.ppf(.025, x, n-x+1)) if x else 0.,
                  float(beta.ppf(.975, x+1, n-x)) if x < n else 1.],
    lower_one_sided_95=float(beta.ppf(.05, x, n-x+1)) if x else 0.)
    for n, x in ((20, 18), (20, 20), (50, 45), (50, 48), (50, 49), (50, 50))]
out["bootstrap_tail_resolution"] = [dict(B=b, expected_samples_per_tail=b*.025,
    probability_no_sample_in_a_given_2_5pct_tail=float(.975**b),
    probability_no_sample_in_at_least_one_tail=float(2*.975**b-.95**b),
    linear_lower_percentile_zero_based_index=(b-1)*.025) for b in (25, 50, 100, 200)]
out["order_statistic_tolerance"] = []
for m in (200, 1000):
    for confidence in (.95, 1-.05/12):
        # F(T_(k)) ~ Beta(k, m+1-k); make P(F(T_(k)) >= .95) >= confidence.
        k = next(k for k in range(1, m+1) if binom.cdf(k-1, m, .95) >= confidence)
        out["order_statistic_tolerance"].append(dict(m=m, confidence=confidence, rank=k,
            attained_confidence=float(binom.cdf(k-1, m, .95))))
out["nominal_rank_test_size_1000"] = 50/1001
out["costs_at_old_15_3min_rate"] = []
for stage, datasets, B in (("probe", 40, 50), ("interval_screen_three_settings", 150, 100),
                            ("power_all_refit", 12000, 200), ("power_reduced_refit", 2400, 50)):
    hours = datasets * (B+1) * 15.3/60
    out["costs_at_old_15_3min_rate"].append(dict(stage=stage, core_hours=hours,
        cloud_dollars_at_recorded_conversion=hours*.48, continuous_days_on_11_Mac_workers=hours/11/24))

# Reproduce dataset_seed's declared <=1-coordinate rule without importing the fitting stack.
all_members = ("M0", "M2B", "M2H", "M2S", "M2K", "M3", "M3H", "M3V", "M3L")
def dataset_seed(name, kwargs, rep, D, seed):
    grid_tag = sum((i+1)*int(round(1000*float(kwargs.get(x, 0))))
                   for i, x in enumerate(("tau", "omega", "sep", "pi0", "alpha", "scale")))
    return int(np.random.default_rng([seed, all_members.index(name), grid_tag % (2**31-1), rep, D]).integers(2**31))
old_seeds = [dataset_seed(name, json.loads(grid), rep, 4, 2026)
             for name, grid in groups for rep in range(1000)]
new_seeds = [dataset_seed("M2S", {"omega": omega}, rep, 4, 2027)
             for omega in (2., 1.) for rep in range(20)]
out["seed_overlap_check"] = dict(old_unique=len(set(old_seeds)), new_unique=len(set(new_seeds)),
    intersection=len(set(old_seeds) & set(new_seeds)), member_order=all_members)
print(json.dumps(out, indent=2))

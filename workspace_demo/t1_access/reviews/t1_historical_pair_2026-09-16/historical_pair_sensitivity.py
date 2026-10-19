"""The inherited predictor pair as a sensitivity analysis on the saved d4v12b calibration rows.

Read-only: it opens `sim_results/d4v12b/calibration_D4.csv` (12,000 datasets, twelve graded nulls, D = 4, one layer)
and counts, per null setting, the decision made by each of the three predictors saved with every dataset:

  selection   the primary predictor of the proposed transfer (the expanded comparison, held-out selection);
  ensemble    the equal-weight ensemble of the same family set;
  historical  the inherited pair carried over from the human study, M3 (mixture) against M2B (graded baseline).

No fit, no simulation and no new data: every column read was written when d4v12b ran. The point of the comparison is
what the *carried-over* pair does under generators the human study never faced - graded responses whose items differ
(M2H, concept random intercept tau), whose spread grows with the mean (M2S, concept random scale omega) and which are
skewed (M2K). It is a property of that pair of predictors under these generators, not a re-audit of the published study.

Writes beside itself:
  historical_pair_counts.csv   one row per null setting, the decision counts of all three predictors
  historical_pair_sensitivity.output.txt  the console table (saved by the caller with a redirect)

Run: python3 historical_pair_sensitivity.py
"""
import collections
import csv
import os

CAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sim_results", "d4v12b",
                   "calibration_D4.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historical_pair_counts.csv")
PREDICTORS = ("selection", "ensemble", "historical")

rows = list(csv.DictReader(open(os.path.normpath(CAL), newline="")))
header = list(rows[0])
assert len(rows) == 12000, f"expected the 12,000 d4v12b datasets, found {len(rows)}"
for p in PREDICTORS:
    assert f"{p}_decision" in header, f"{p}_decision missing from {CAL}"

# Every generator is graded by construction, so any "mixture" call here is a false call.
setting_cols = [c for c in ("generator", "grid") if c in header]
agg = collections.defaultdict(collections.Counter)
totals = collections.Counter()
for r in rows:
    key = tuple(r[c] for c in setting_cols)
    agg[key]["n"] += 1
    for p in PREDICTORS:
        d = r[f"{p}_decision"] or "(blank)"
        agg[key][f"{p}:{d}"] += 1
        totals[f"{p}:{d}"] += 1

decisions = sorted({k.split(":", 1)[1] for k in totals})
print(f"{len(rows):,} datasets, {len(agg)} null settings, decisions seen: {', '.join(decisions)}")
print()
head = f"{'generator':<10} {'grid':<26} {'n':>5}  " + "  ".join(f"{p:<34}" for p in PREDICTORS)
print(head)
for key in sorted(agg):
    c = agg[key]
    cells = []
    for p in PREDICTORS:
        counts = {d: c[f"{p}:{d}"] for d in decisions if c[f"{p}:{d}"]}
        cells.append(", ".join(f"{d} {v}" for d, v in sorted(counts.items())))
    print(f"{key[0]:<10} {key[1]:<26} {c['n']:>5}  " + "  ".join(f"{s:<34}" for s in cells))

print()
for p in PREDICTORS:
    counts = {d: totals[f"{p}:{d}"] for d in decisions if totals[f"{p}:{d}"]}
    print(f"all settings  {p:<11}" + ", ".join(f"{d} {v:,}" for d, v in sorted(counts.items())))

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(list(setting_cols) + ["n"] + [f"{p}_{d}" for p in PREDICTORS for d in decisions])
    for key in sorted(agg):
        c = agg[key]
        w.writerow(list(key) + [c["n"]] + [c[f"{p}:{d}"] for p in PREDICTORS for d in decisions])
print(f"\nwrote {OUT}")

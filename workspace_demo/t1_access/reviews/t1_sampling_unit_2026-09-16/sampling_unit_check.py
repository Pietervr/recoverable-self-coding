"""Is the concept a calibrated sampling unit? Post hoc aggregation of saved d4v12b rows; no refitting.

For each graded setting the band mean is the average of the 64 held-out per-concept scores saved in every row.
Treating the concept as the exchangeable unit gives SE_concept = sd(delta_c)/sqrt(64). The honest check on that
choice is whether it reproduces the spread the statistic ACTUALLY has across independent replicates of the same
generator: sd_rep = SD of the band point estimate over the 1,000 datasets. A unit that is doing its job gives
SE_concept ~ sd_rep; a unit that is too fine for the data gives SE_concept < sd_rep.

Reads: sim_results/d4v12b/calibration_D4.csv (12,000 rows, SHA-256 7762f152...babb).
Writes: sampling_unit.csv beside this script, and the same table to stdout.
"""
import csv, json, math, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "sim_results", "d4v12b", "calibration_D4.csv")

by = {}
with open(SRC, newline="") as f:
    for row in csv.DictReader(f):
        if row["failed"] not in ("", "False", "false", "0"):
            continue
        key = (row["generator"], row["grid"])
        d = json.loads(row["delta_per_concept"])["selection"]
        flat = [v for part in d for v in part]
        by.setdefault(key, []).append((float(row["selection_ws_point"]),
                                       float(row["selection_ws_se"]), flat))

SYM = {"tau": "tau", "omega": "omega", "alpha": "alpha"}
def label(gen, grid):
    g = json.loads(grid) if grid else {}
    if not g:
        return "base (M2B)"
    (k, v), = g.items()
    return f"{gen}, {SYM[k]}={float(v):g}"

out = []
for (gen, grid), rows in by.items():
    pts = [r[0] for r in rows]
    claimed = [r[1] for r in rows]
    recomputed = [st.stdev(r[2]) / math.sqrt(len(r[2])) for r in rows]
    n_concepts = st.mode([len(r[2]) for r in rows])
    sd_rep = st.stdev(pts)
    out.append(dict(setting=label(gen, grid), generator=gen, grid=grid, n=len(rows),
                    n_concepts=n_concepts, sd_rep=sd_rep,
                    median_se_claimed=st.median(claimed), mean_se_claimed=st.mean(claimed),
                    median_se_concept=st.median(recomputed),
                    ratio_median=sd_rep / st.median(claimed),
                    ratio_mean=sd_rep / st.mean(claimed)))

order = {"M2B": 0, "M2H": 1, "M2K": 2, "M2S": 3}
out.sort(key=lambda r: (order[r["generator"]], r["grid"]))

print(f"{'setting':<22}{'n':>6}{'sd_rep':>11}{'med SE':>11}{'recomp SE':>11}{'sd/medSE':>10}{'sd/meanSE':>11}")
for r in out:
    print(f"{r['setting']:<22}{r['n']:>6}{r['sd_rep']:>11.5f}{r['median_se_claimed']:>11.5f}"
          f"{r['median_se_concept']:>11.5f}{r['ratio_median']:>10.2f}{r['ratio_mean']:>11.2f}")

with open(os.path.join(HERE, "sampling_unit.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
print("\nwrote sampling_unit.csv")

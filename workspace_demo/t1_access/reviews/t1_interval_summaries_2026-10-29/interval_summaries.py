"""Producing output for three summaries of the Entropy SI article's Section 7.4 (R052, 29 Oct 2026; NUMBERS_LEDGER rows 8-9,
open since draft 4): (a) the largest upper endpoint of any concept-cluster interval in the calibration run d4v12b, (b) the
median interval's position below zero measured in its own width, setting by setting, and (c) the ratio of the interval's
claimed standard error to the concept-level quantity sd(Delta_c)/sqrt(64) recomputed from the saved per-concept scores,
per dataset, summarized per setting and across settings. Post hoc aggregation of saved rows; no refitting.

Reads: sim_results/d4v12b/calibration_D4.csv (12,000 rows). Writes: interval_summaries.output.txt beside this script.
"""
import csv, json, math, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "sim_results", "d4v12b", "calibration_D4.csv")
OUT = os.path.join(HERE, "interval_summaries.output.txt")

SYM = {"tau": "tau", "omega": "omega", "alpha": "alpha"}
def label(gen, grid):
    g = json.loads(grid) if grid else {}
    if not g:
        return "base (M2B)"
    (k, v), = g.items()
    return f"{gen}, {SYM[k]}={float(v):g}"

VARIANTS = ("selection", "ensemble", "historical")
by = {}
n_failed = 0
with open(SRC, newline="") as f:
    for row in csv.DictReader(f):
        if row["failed"] not in ("", "False", "false", "0"):
            n_failed += 1
            continue
        key = (row["generator"], row["grid"])
        d = json.loads(row["delta_per_concept"])["selection"]
        flat = [v for part in d for v in part]
        rec = {}
        for v in VARIANTS:
            rec[v] = (float(row[f"{v}_ws_point"]), float(row[f"{v}_ws_lo"]), float(row[f"{v}_ws_hi"]), float(row[f"{v}_ws_se"]))
        rec["flat"] = flat
        by.setdefault(key, []).append(rec)

order = {"M2B": 0, "M2H": 1, "M2K": 2, "M2S": 3}
keys = sorted(by, key=lambda k: (order[k[0]], k[1]))

lines = []
P = lines.append
P(f"rows read: {sum(len(v) for v in by.values())} (failed rows skipped: {n_failed})")
P("")
P("(a) Largest upper endpoint of the 95% concept-cluster interval, per setting and variant (nat per trial)")
P(f"{'setting':<22}{'n':>6}{'max hi sel':>12}{'max hi ens':>12}{'max hi hist':>13}")
overall = {v: -math.inf for v in VARIANTS}
for k in keys:
    rows = by[k]
    mx = {v: max(r[v][2] for r in rows) for v in VARIANTS}
    for v in VARIANTS:
        overall[v] = max(overall[v], mx[v])
    P(f"{label(*k):<22}{len(rows):>6}{mx['selection']:>12.4f}{mx['ensemble']:>12.4f}{mx['historical']:>13.4f}")
P(f"{'all 12 settings':<22}{'':>6}{overall['selection']:>12.4f}{overall['ensemble']:>12.4f}{overall['historical']:>13.4f}")
P("")
P("(b) The interval's position below zero in units of its own width (selection variant): per setting the median over datasets of")
P("    -hi/width (the upper end's distance below zero) and of -point/width (the point estimate's distance below zero)")
P(f"{'setting':<22}{'n':>6}{'med -hi/w':>11}{'med -pt/w':>11}{'med width':>11}")
a_vals, b_vals = [], []
for k in keys:
    rows = by[k]
    a = st.median([-r["selection"][2] / (r["selection"][2] - r["selection"][1]) for r in rows])
    b = st.median([-r["selection"][0] / (r["selection"][2] - r["selection"][1]) for r in rows])
    w = st.median([r["selection"][2] - r["selection"][1] for r in rows])
    a_vals.append(a); b_vals.append(b)
    P(f"{label(*k):<22}{len(rows):>6}{a:>11.2f}{b:>11.2f}{w:>11.5f}")
P(f"range across settings: -hi/w {min(a_vals):.2f} to {max(a_vals):.2f}; -pt/w {min(b_vals):.2f} to {max(b_vals):.2f}")
P("")
P("(c) Claimed SE of the concept-cluster interval over the recomputed concept-level SE sd(Delta_c)/sqrt(n_c), per dataset;")
P("    per setting the median of the per-dataset ratio, and (for comparison) the ratio of the two medians")
P(f"{'setting':<22}{'n':>6}{'med ratio':>11}{'p05':>8}{'p95':>8}{'med/med':>9}")
med_ratios, all_ratios = [], []
for k in keys:
    rows = by[k]
    ratios = []
    claimed, recomputed = [], []
    for r in rows:
        rc = st.stdev(r["flat"]) / math.sqrt(len(r["flat"]))
        ratios.append(r["selection"][3] / rc)
        claimed.append(r["selection"][3]); recomputed.append(rc)
    ratios.sort()
    all_ratios.extend(ratios)
    m = st.median(ratios)
    med_ratios.append(m)
    p05 = ratios[int(0.05 * (len(ratios) - 1))]
    p95 = ratios[int(0.95 * (len(ratios) - 1))]
    P(f"{label(*k):<22}{len(rows):>6}{m:>11.4f}{p05:>8.3f}{p95:>8.3f}{st.median(claimed) / st.median(recomputed):>9.4f}")
P(f"across settings: median of the per-setting medians {st.median(med_ratios):.4f}, range {min(med_ratios):.4f} to {max(med_ratios):.4f}")
P(f"over all datasets pooled: median ratio {st.median(all_ratios):.4f}")
P(f"sqrt(7/8) = {math.sqrt(7 / 8):.4f}")

text = "\n".join(lines) + "\n"
print(text, end="")
with open(OUT, "w") as f:
    f.write(text)
print(f"wrote {OUT}")

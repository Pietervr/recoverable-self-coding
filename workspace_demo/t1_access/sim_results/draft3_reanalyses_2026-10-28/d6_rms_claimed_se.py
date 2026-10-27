"""D6 (R052 SI draft 3, deep-read decision D6): replicate SD against the root mean square of the claimed SEs.

Morris, White & Crowther (2019, Stat Med, Table 6 and section 5.2) define the check of a model standard error in mean
square: the "average model SE" is sqrt(mean(SE_i^2)) over replicates, compared with the empirical SE (the SD of the
point estimates over replicates). The SI's Table tab:unit compared the replicate SD with the MEDIAN claimed SE
(ratios 1.04 ... 3.31 at omega = 1, 71.43 at omega = 2). This script adds the RMS comparison for all twelve graded
settings of the calibration run, from the same saved rows, with no refitting.

Reads: ../d4v12b/calibration_D4.csv (12,000 rows, SHA-256 7762f152...9211babb; checked below).
Writes: d6_rms_claimed_se.csv and d6_rms_claimed_se.txt (this table) beside this script.

Columns: sd_rep = SD over the 1,000 datasets of the band point estimate (selection_ws_point); median / mean / RMS of
the claimed SE (selection_ws_se); ratio_median = sd_rep / median SE (the published Table tab:unit ratio, reproduced
here as a tie to the earlier script); ratio_rms = sd_rep / RMS SE (Morris's comparison); also the 90th, 99th
percentile and maximum of the claimed SE and the share of the mean square contributed by the largest 1% of SEs, to
show how much of the RMS is tail.
"""
import csv, hashlib, json, math, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "d4v12b", "calibration_D4.csv")
EXPECT = "7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb"

h = hashlib.sha256()
with open(SRC, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
assert h.hexdigest() == EXPECT, h.hexdigest()

by = {}
with open(SRC, newline="") as f:
    for row in csv.DictReader(f):
        if row["failed"] not in ("", "False", "false", "0"):
            continue
        by.setdefault((row["generator"], row["grid"]), []).append(
            (float(row["selection_ws_point"]), float(row["selection_ws_se"])))


def label(gen, grid):
    g = json.loads(grid) if grid else {}
    if not g:
        return "base (M2B)"
    (k, v), = g.items()
    return f"{gen}, {k}={float(v):g}"


def pct(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


out = []
for (gen, grid), rows in by.items():
    pts = [r[0] for r in rows]
    se = [r[1] for r in rows]
    sd_rep = st.stdev(pts)
    rms = math.sqrt(sum(s * s for s in se) / len(se))
    sq = sorted((s * s for s in se), reverse=True)
    top = max(1, len(sq) // 100)
    out.append(dict(setting=label(gen, grid), generator=gen, grid=grid, n=len(rows), sd_rep=sd_rep,
                    median_se=st.median(se), mean_se=st.mean(se), rms_se=rms,
                    p90_se=pct(se, 0.90), p99_se=pct(se, 0.99), max_se=max(se),
                    top1pct_share_of_mean_square=sum(sq[:top]) / sum(sq),
                    ratio_median=sd_rep / st.median(se), ratio_mean=sd_rep / st.mean(se),
                    ratio_rms=sd_rep / rms))

order = {"M2B": 0, "M2H": 1, "M2K": 2, "M2S": 3}
out.sort(key=lambda r: (order[r["generator"]], r["grid"]))

lines = [f"source {os.path.relpath(SRC, HERE)} sha256 {EXPECT}", "",
         f"{'setting':<18}{'n':>6}{'sd_rep':>11}{'med SE':>10}{'mean SE':>10}{'RMS SE':>10}{'max SE':>10}"
         f"{'top1%MS':>9}{'sd/med':>8}{'sd/mean':>9}{'sd/RMS':>8}"]
for r in out:
    lines.append(f"{r['setting']:<18}{r['n']:>6}{r['sd_rep']:>11.5f}{r['median_se']:>10.5f}{r['mean_se']:>10.5f}"
                 f"{r['rms_se']:>10.5f}{r['max_se']:>10.4f}{r['top1pct_share_of_mean_square']:>9.3f}"
                 f"{r['ratio_median']:>8.2f}{r['ratio_mean']:>9.2f}{r['ratio_rms']:>8.2f}")
text = "\n".join(lines)
print(text)
with open(os.path.join(HERE, "d6_rms_claimed_se.txt"), "w") as f:
    f.write(text + "\n")
with open(os.path.join(HERE, "d6_rms_claimed_se.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

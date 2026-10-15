"""Two saved-row diagnostics of the d4v12b calibration rows (read-only; no fits). R052, 15 Oct 2026.

The SI defers both (Section 6.2; S4); Codex's SI review (s.15 item 5) asked for them or a reason to omit them.

1. Row bootstrap of the inclusion statistic (SI Section 6.2). Per graded setting: resample the 1,000 complete
   replicate rows with replacement, re-estimate the reference as the mean of the resampled point estimates, and
   recompute the share of resampled intervals [lo, hi] containing it. B = 10,000 resamples, seed per setting.
   Reports the observed rate, the bootstrap 95 % percentile interval, and the bootstrap share of resamples at or
   above the 0.90 floor. This approximates the uncertainty of the empirical inclusion statistic with its
   reference estimated from the same rows; it is not a bound on coverage of the unknown expectation.

2. Per-concept concentration (SI S4). Each dataset's point estimate is the mean of its 64 held-out per-concept
   score differences Delta_c (primary predictor; saved in delta_per_concept, five decimals). With S = sum_c Delta_c,
   the top-k share is the sum of the k most negative Delta_c (the graded direction) divided by S. A share near
   k/64 means the difference is spread evenly; near 1, that k concepts carry it. Reported per setting as the
   median and 90th percentile over datasets with S < 0, for k = 1 and 3, and for the 10 datasets with the most
   negative point estimate; plus the share of datasets where one concept carries more than half of S.

Input: sim_results/d4v12b/calibration_D4.csv (12,000 rows; SHA-256 7762f152...9211babb).
Run: python3 saved_row_diagnostics.py   (writes saved_row_diagnostics.output.txt beside it)
"""
import collections
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.normpath(os.path.join(HERE, "..", "..", "sim_results", "d4v12b", "calibration_D4.csv"))
B, SEED0, FLOOR = 10_000, 20261015, 0.90
csv.field_size_limit(sys.maxsize)


def name(gen, grid):
    g = json.loads(grid)
    return gen + (" " + " ".join(f"{k}={g[k]:g}" for k in g) if g else "")


def main():
    by = collections.defaultdict(lambda: {"p": [], "lo": [], "hi": [], "d": []})
    with open(CAL, newline="") as fh:
        for r in csv.DictReader(fh):
            s = by[(r["generator"], r["grid"])]
            s["p"].append(float(r["selection_ws_point"]))
            s["lo"].append(float(r["selection_ws_lo"]))
            s["hi"].append(float(r["selection_ws_hi"]))
            s["d"].append(np.asarray(json.loads(r["delta_per_concept"])["selection"], float).ravel())
    out = []
    say = out.append
    say("1. Row bootstrap of the inclusion rate, reference re-estimated in every resample "
        f"(B = {B:,}; seeds default_rng([{SEED0}, setting]))")
    say(f"{'setting':<16} {'n':>5} {'observed':>9} {'95% interval':>17} {'P(>=0.90)':>10}")
    for si, key in enumerate(sorted(by)):
        s = by[key]
        p, lo, hi = (np.asarray(s[k]) for k in ("p", "lo", "hi"))
        n = p.size
        obs = np.mean((lo <= p.mean()) & (p.mean() <= hi))
        rng = np.random.default_rng([SEED0, si])
        rates = np.empty(B)
        for b in range(B):
            i = rng.integers(0, n, n)
            ref = p[i].mean()
            rates[b] = np.mean((lo[i] <= ref) & (ref <= hi[i]))
        q = np.percentile(rates, [2.5, 97.5])
        say(f"{name(*key):<16} {n:>5} {obs:>9.3f}   [{q[0]:.3f}, {q[1]:.3f}] {np.mean(rates >= FLOOR):>10.3f}")
    say("")
    say("2. Per-concept concentration of the band-mean difference (primary predictor, 64 concepts)")
    say("   top-k share = (sum of the k most negative Delta_c) / (sum of all Delta_c), datasets with a negative sum")
    say(f"{'setting':<16} {'n<0':>5} {'top1 med':>9} {'top1 p90':>9} {'top3 med':>9} {'top3 p90':>9} "
        f"{'top1>0.5':>9} {'top1 med, 10 most negative':>28}")
    for key in sorted(by):
        s = by[key]
        D = np.vstack(s["d"])
        S = D.sum(axis=1)
        neg = S < 0
        srt = np.sort(D[neg], axis=1)
        t1 = srt[:, 0] / S[neg]
        t3 = srt[:, :3].sum(axis=1) / S[neg]
        ext = np.argsort(np.asarray(s["p"]))[:10]
        ext_t1 = np.sort(D[ext], axis=1)[:, 0] / S[ext]
        say(f"{name(*key):<16} {neg.sum():>5} {np.median(t1):>9.3f} {np.percentile(t1, 90):>9.3f} "
            f"{np.median(t3):>9.3f} {np.percentile(t3, 90):>9.3f} {np.mean(t1 > 0.5):>9.3f} {np.median(ext_t1):>28.3f}")
    say("   an even spread over 64 concepts gives top-1 share 1/64 = 0.016 and top-3 share 0.047")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(HERE, "saved_row_diagnostics.output.txt"), "w") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main()

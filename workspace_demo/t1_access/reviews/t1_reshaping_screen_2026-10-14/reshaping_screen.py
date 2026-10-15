"""Reshaping screen of the fixed-score concept-cluster bootstrap, on the saved d4v12b calibration rows. No fits.

Reproduces, as a tracked script, the screen first run on 13 Sept 2026 (PC, untracked; recorded in the design
ledger rsc_t1_simulation_design.md section 6): do other constructions of the SAME fixed-score bootstrap - basic,
bias-corrected and accelerated (BCa), studentized (bootstrap-t) and normal-theory - reach an inclusion rate of
0.90 at every graded setting? The percentile interval, the one the procedure used, is recomputed alongside as a
check against the saved interval endpoints.

Input: sim_results/d4v12b/calibration_D4.csv (12,000 rows; SHA-256 7762f152...9211babb). Each row stores the
64 per-concept band-mean score differences of the primary (selection) predictor in delta_per_concept, rounded
to five decimals by the writer. The resampling follows analyze.band_bootstrap: whole concepts with replacement
within each of the 8 family strata (8 concepts each, family = concept // 8), B = 2,000, 95 % two-sided. Seeds
are per row, numpy default_rng([20261014, setting index, rep]), so the output is deterministic; they differ from
the original run's seeds, so recomputed percentile endpoints match the saved ones only to Monte-Carlo error.

Reference per setting, as in reference_inclusion_check.py: the setting's own replicate mean of the saved point
estimate (a same-sample candidate reference, not a known population value). A mixture call is lo > 0.

Run: python3 reshaping_screen.py   (about one to two minutes; writes reshaping_screen.output.txt beside it)
"""
import collections
import csv
import json
import os
import sys

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.normpath(os.path.join(HERE, "..", "..", "sim_results", "d4v12b", "calibration_D4.csv"))
B, N_FAM, PER_FAM, SEED0 = 2000, 8, 8, 20261014
METHODS = ("percentile", "basic", "bca", "studentized", "normal")
csv.field_size_limit(sys.maxsize)

fam = np.repeat(np.arange(N_FAM), PER_FAM)
C = fam.size


def strat_se(x):
    """Standard error of the concept mean under within-family resampling, for each row of x (..., C)."""
    xs = x.reshape(*x.shape[:-1], N_FAM, PER_FAM)
    var_f = xs.var(axis=-1, ddof=0)                      # plug-in variance inside each stratum
    return np.sqrt((var_f / PER_FAM).sum(axis=-1)) / N_FAM


def intervals(v, rng):
    point = v.mean()
    idx = np.concatenate([np.where(fam == f)[0][rng.integers(0, PER_FAM, size=(B, PER_FAM))] for f in range(N_FAM)], axis=1)
    bv = v[idx]
    boot = bv.mean(axis=1)
    se_b = boot.std(ddof=1)
    out = {"percentile": (np.percentile(boot, 2.5), np.percentile(boot, 97.5))}
    out["basic"] = (2 * point - out["percentile"][1], 2 * point - out["percentile"][0])
    out["normal"] = (point - 1.959964 * se_b, point + 1.959964 * se_b)
    # studentized: t* = (boot - point) / se*, with the analytic stratified SE inside each resample
    se0, se_star = strat_se(v), strat_se(bv)
    ok = se_star > 0
    t = (boot[ok] - point) / se_star[ok]
    q_lo, q_hi = np.percentile(t, [2.5, 97.5])
    out["studentized"] = (point - q_hi * se0, point - q_lo * se0)
    # BCa: bias from the share of replicates below the point, acceleration from the delete-one-concept jackknife
    p = np.clip(np.mean(boot < point) + 0.5 * np.mean(boot == point), 1 / (B + 1), B / (B + 1))
    z0 = norm.ppf(p)
    jack = (v.sum() - v) / (C - 1)
    d = jack.mean() - jack
    den = 6 * (d ** 2).sum() ** 1.5
    a = (d ** 3).sum() / den if den > 0 else 0.0
    z = norm.ppf([0.025, 0.975])
    adj = norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))
    out["bca"] = tuple(np.percentile(boot, 100 * adj))
    return point, se_b, out


def main():
    by = collections.defaultdict(list)
    with open(CAL, newline="") as fh:
        for r in csv.DictReader(fh):
            v = np.asarray(json.loads(r["delta_per_concept"])["selection"], dtype=float).ravel()
            assert v.size == C, v.size
            by[(r["generator"], r["grid"])].append((int(r["rep"]), v, float(r["selection_ws_point"]),
                                                    float(r["selection_ws_lo"]), float(r["selection_ws_hi"])))
    assert sum(len(x) for x in by.values()) == 12000
    lines = []
    say = lines.append
    say(f"reshaping screen, B = {B}, stratified concept bootstrap, seeds default_rng([{SEED0}, setting, rep])")
    say(f"{'setting':<22} {'ref':>10} {'ratio':>6} {'saved':>6} " + " ".join(f"{m:>11}" for m in METHODS) + "   mixture calls")
    reached = collections.Counter()
    calls = collections.Counter()
    for si, key in enumerate(sorted(by)):
        rows = by[key]
        ref = np.mean([x[2] for x in rows])
        inc = collections.Counter()
        pts, half = [], []
        saved = 0
        for rep, v, p_saved, lo_s, hi_s in rows:
            point, se_b, iv = intervals(v, np.random.default_rng([SEED0, si, rep]))
            pts.append(point)
            half.append((iv["percentile"][1] - iv["percentile"][0]) / 2)
            saved += lo_s <= ref <= hi_s
            for m in METHODS:
                lo, hi = iv[m]
                inc[m] += lo <= ref <= hi
                calls[m] += lo > 0
        n = len(rows)
        rates = {m: inc[m] / n for m in METHODS}
        for m in METHODS:
            reached[m] += rates[m] >= 0.90
        ratio = np.std(pts, ddof=1) / np.mean(half)
        g = json.loads(key[1])
        name = key[0] + (" " + " ".join(f"{k}={g[k]:g}" for k in g) if g else "")
        say(f"{name:<22} {ref:>10.5f} {ratio:>6.2f} {saved / n:>6.3f} " + " ".join(f"{rates[m]:>11.3f}" for m in METHODS)
            + "   " + " ".join(f"{calls[m]}" for m in METHODS))
    say("")
    say("settings (of 12) at which the inclusion rate reaches 0.90:")
    for m in METHODS:
        say(f"  {m:<12} {reached[m]:>2}   mixture calls over all 12,000 datasets: {calls[m]}")
    say("ratio = between-replicate SD of the point estimate / mean percentile half-width (about 0.51 for a calibrated normal 95 % interval)")
    say("saved = inclusion of the run's own saved percentile intervals (reference_inclusion_check.py reproduces these)")
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(HERE, "reshaping_screen.output.txt"), "w") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main()

"""Candidate repairs, screened offline on the d4v12b saved rows (method development, NOT validation).

A. small-strata correction: claimed interval half-widths times sqrt(8/7) (stratified bootstrap with 8 per stratum
   understates variance by (n_h-1)/n_h).
B. A plus a fixed inflation c applied everywhere (what a fitting-variance allowance of size c would buy).
C. robust estimand: 10% trimmed mean of the 64 per-concept deltas, stratified bootstrap (8 strata of 8, B=1000,
   with the sqrt(8/7) correction), reference = replicate mean of that trimmed statistic.
D. same as C with the median of per-concept deltas.
Concept order in delta_per_concept is assumed to be family-blocked (8 consecutive per family).
"""
import csv, json, sys
import numpy as np
from scipy import stats

csv.field_size_limit(10**9)
rng = np.random.default_rng(20261027)
rows, order = {}, []
with open(sys.argv[1]) as f:
    for r in csv.DictReader(f):
        g = r["generator"] + (" " + r["grid"] if r["grid"] not in ("{}", "") else "")
        rows.setdefault(g, []).append(r)
        if g not in order:
            order.append(g)

B = 1000
idx = rng.integers(0, 8, size=(B, 8, 8))  # resample within each of 8 strata
corr = np.sqrt(8 / 7)

def boot_stat(d, fn):
    d8 = d.reshape(8, 8)
    res = np.take_along_axis(np.broadcast_to(d8, (B, 8, 8)), idx, axis=2).reshape(B, 64)
    return fn(res)

trim = lambda a: stats.trim_mean(a, 0.10, axis=-1)
medf = lambda a: np.median(a, axis=-1)

print("setting | A incl | A+c=1.10 | A+c=1.20 | C trimmed incl | C k | D median incl | D k")
for g in order:
    R = rows[g]
    pt = np.array([float(r["selection_ws_point"]) for r in R])
    lo = np.array([float(r["selection_ws_lo"]) for r in R])
    hi = np.array([float(r["selection_ws_hi"]) for r in R])
    th = pt.mean()
    def incl(f):
        return (((pt - f * (pt - lo)) <= th) & (th <= pt + f * (hi - pt))).mean()
    out = [incl(corr), incl(corr * 1.10), incl(corr * 1.20)]
    for fn in (trim, medf):
        P, L, H = [], [], []
        for r in R:
            d = np.array(json.loads(r["delta_per_concept"])["selection"][0])
            p = float(fn(d[None, :])[0])
            bs = boot_stat(d, fn)
            s = bs.std(ddof=1) * corr
            P.append(p); L.append(p - 1.96 * s); H.append(p + 1.96 * s)
        P, L, H = map(np.array, (P, L, H))
        t = P.mean()
        k = P.std(ddof=1) / np.median((H - L) / 3.92)
        out += [((L <= t) & (t <= H)).mean(), k]
    print(f"{g} | {out[0]:.3f} | {out[1]:.3f} | {out[2]:.3f} | {out[3]:.3f} | {out[4]:.2f} | {out[5]:.3f} | {out[6]:.2f}")

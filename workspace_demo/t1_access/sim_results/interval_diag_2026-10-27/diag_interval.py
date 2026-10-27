"""Why does the fixed-score concept-cluster interval miss its estimated reference? Post hoc on d4v12b saved rows.

Per graded setting: observed inclusion; where the misses fall (interval above or below the reference);
oracle-width inclusion (point +/- 1.96 * replicate SD: fixes width only); width-rescaled inclusion
(interval half-width times replicate SD / median claimed SE); inclusion of the replicate median;
skewness of the point estimates; concept dominance (share of |sum delta| from the single largest concept)
and its relation to misses; selected-member mix and its relation to misses.
"""
import csv, json, sys, math
import numpy as np

path = sys.argv[1]
csv.field_size_limit(10**9)
rows = {}
order = []
with open(path) as f:
    for r in csv.DictReader(f):
        g = r["generator"] + (" " + r["grid"] if r["grid"] not in ("{}", "") else "")
        if g not in rows:
            rows[g] = []
            order.append(g)
        rows[g].append(r)

def skew(x):
    x = np.asarray(x); m = x.mean(); s = x.std()
    return float(((x - m) ** 3).mean() / s ** 3) if s > 0 else float("nan")

print("setting | n | incl | miss: ref<lo / ref>hi | oracle-width incl | rescaled incl | incl(median) | k=SDrep/SE | skew(point) | dom: med, misses vs hits | sel-mix")
for g in order:
    R = rows[g]
    pt = np.array([float(r["selection_ws_point"]) for r in R])
    lo = np.array([float(r["selection_ws_lo"]) for r in R])
    hi = np.array([float(r["selection_ws_hi"]) for r in R])
    se = np.array([float(r["selection_ws_se"]) for r in R])
    th = pt.mean(); med = np.median(pt)
    inc = (lo <= th) & (th <= hi)
    below = (th < lo).mean(); above = (th > hi).mean()
    sd = pt.std(ddof=1); k = sd / np.median(se)
    orc = (np.abs(pt - th) <= 1.96 * sd).mean()
    half_lo = pt - lo; half_hi = hi - pt
    resc = ((pt - k * half_lo <= th) & (th <= pt + k * half_hi)).mean()
    incmed = ((lo <= med) & (med <= hi)).mean()
    dom = []
    sel = []
    for r in R:
        d = np.array(json.loads(r["delta_per_concept"])["selection"][0])
        dom.append(np.abs(d).max() / max(np.abs(d).sum(), 1e-300))
        s = json.loads(r["selected"])
        sel.append(tuple(sorted(s.items())))
    dom = np.array(dom)
    dm = np.median(dom[~inc]) if (~inc).any() else float("nan")
    dh = np.median(dom[inc])
    # selected graded members: which graded member(s) were chosen across folds
    gsel = []
    for r in R:
        s = json.loads(r["selected"])
        gm = [m for m in s if m.startswith("M2")]
        gsel.append("+".join(sorted(gm)))
    gsel = np.array(gsel)
    mix = {}
    for key in sorted(set(gsel)):
        m = gsel == key
        mix[key] = (int(m.sum()), round(float(inc[m].mean()), 3))
    top = sorted(mix.items(), key=lambda kv: -kv[1][0])[:3]
    print(f"{g} | {len(R)} | {inc.mean():.3f} | {below:.3f} / {above:.3f} | {orc:.3f} | {resc:.3f} | {incmed:.3f} | {k:.2f} | {skew(pt):+.2f} | {np.median(dom):.3f}, {dm:.3f} vs {dh:.3f} | {top}")

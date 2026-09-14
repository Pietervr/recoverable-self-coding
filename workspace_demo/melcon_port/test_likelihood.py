"""likelihood.py on synthetic numbers only (no EEG): analytic gradients against central differences for all four
models, recovery of the family that generated large synthetic blocks, finite densities at every corner of the bounds,
interior starts when the moment recipe falls on or outside a bound, the unavailable paths, determinism of the seeded
starts, the removed intercept alias, and the legacy sensitivity's repaired anchor and catch flag.

Run: ../../.venv/bin/python test_likelihood.py
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.special import expit

import likelihood as LK


def synth_block(rng, n, law, n_catch=None, sep=2.0):
    """A block of n trials: 10 % catch, hemifields balanced, log contrast from a staircase-like spread."""
    n_catch = n // 10 if n_catch is None else n_catch
    catch = np.zeros(n, dtype=bool)
    catch[:n_catch] = True
    rng.shuffle(catch)
    right = rng.random(n) < 0.5
    logc = np.where(catch, np.nan, rng.normal(-3.0, 0.3, n))
    x = np.where(catch, 0.0, (np.nan_to_num(logc, nan=-3.0) + 3.0) / 0.3)
    L = np.where(catch, 0.0, expit(1.5 * x))
    shift = 0.3 * (right & ~catch)
    if law == "graded":
        y = sep * L + shift + rng.normal(0, 1, n)
    elif law == "mixture":
        high = rng.random(n) < L
        y = np.where(high, sep, 0.0) + shift + rng.normal(0, 1, n)
    else:
        raise ValueError(law)
    return LK.Block(y, logc, catch, right)


def check_gradients():
    rng = np.random.default_rng(1)
    blk = synth_block(rng, 120, "mixture")
    sc = LK.scaling(blk)
    d = LK.design(blk, sc)
    worst = {}
    for model in LK.PARAMS:
        b = LK.bounds(model, sc)
        for rep in range(5):
            th = b[:, 0] + (b[:, 1] - b[:, 0]) * rng.uniform(0.2, 0.8, len(b))
            _, g = LK.loglik(model, th, d, grad=True)
            num = np.empty_like(g)
            for i in range(len(th)):
                e = 1e-6 * max(1.0, abs(th[i]))
                tp, tm = th.copy(), th.copy()
                tp[i] += e
                tm[i] -= e
                num[i] = (LK.loglik(model, tp, d).sum() - LK.loglik(model, tm, d).sum()) / (2 * e)
            rel = np.max(np.abs(g - num) / np.maximum(1.0, np.abs(num)))
            worst[model] = max(worst.get(model, 0.0), rel)
        assert worst[model] < 1e-5, (model, worst[model])
    return worst


def check_recovery():
    rng = np.random.default_rng(2)
    out = {}
    for law in ("graded", "mixture"):
        tr, te = synth_block(rng, 3000, law), synth_block(rng, 3000, law)
        s = LK.fold_scores(tr, te, tags=(7, 0))
        assert all(s[m]["available"] for m in LK.PRIMARY), {m: s[m]["reason"] for m in s}
        delta = (s["twostate"]["heldout"] - s["graded"]["heldout"]) / s["graded"]["n_test"]
        out[law] = delta
        assert s["graded"]["heldout"] > s["null"]["heldout"] + 100, law
    assert out["mixture"] > 0.01 and out["graded"] < 0.005, out
    return out


def check_bounds_finite():
    rng = np.random.default_rng(3)
    blk = synth_block(rng, 100, "graded")
    blk.y[:3] += 40.0                                   # far outliers
    sc = LK.scaling(blk)
    d = LK.design(blk, sc)
    n = 0
    for model in LK.PARAMS:
        b = LK.bounds(model, sc)
        for corner in itertools.product(*[(0, 1)] * len(b)):
            th = np.array([b[i, c] for i, c in enumerate(corner)])
            ll, g = LK.loglik(model, th, d, grad=True)
            assert np.all(np.isfinite(ll)) and np.all(np.isfinite(g)), (model, corner)
            n += 1
    return n


def check_starts_interior():
    rng = np.random.default_rng(4)
    blk = synth_block(rng, 100, "graded")
    blk.y[:] = rng.normal(0, 1, 100)                    # no dose effect: top minus bottom quintile can be <= 0
    order = np.argsort(np.nan_to_num(blk.logc, nan=-9))
    blk.y[order[-15:]] -= 3.0                           # force a negative top-minus-bottom difference
    sc = LK.scaling(blk)
    d = LK.design(blk, sc)
    for model in LK.PARAMS:
        b = LK.bounds(model, sc)
        p0 = LK.interior(LK.moment_start(model, d, sc), b)
        assert np.all(p0 > b[:, 0]) and np.all(p0 < b[:, 1]), model
        j = LK.jitter(p0, b, np.random.default_rng(0), LK.JITTER_SD)
        assert np.all(j > b[:, 0]) and np.all(j < b[:, 1]), model
    assert LK.moment_start("graded", d, sc)[1] < 0            # the raw recipe fell outside the a1 bound ...
    assert LK.interior(LK.moment_start("graded", d, sc), LK.bounds("graded", sc))[1] > 0   # ... and was moved inside


def check_unavailable():
    rng = np.random.default_rng(5)
    good = synth_block(rng, 100, "graded")
    reasons = {}
    few_catch = synth_block(rng, 100, "graded", n_catch=2)
    reasons["2 catch"] = LK.fold_scores(few_catch, good)["graded"]["reason"]
    one_side = LK.Block(good.y, good.logc, good.catch, np.zeros(100, dtype=bool))
    reasons["one hemifield"] = LK.fold_scores(one_side, good)["graded"]["reason"]
    flat = LK.Block(np.full(100, 0.7), good.logc, good.catch, good.right)
    reasons["flat projections"] = LK.fold_scores(flat, good)["graded"]["reason"]
    same_c = LK.Block(good.y, np.where(good.catch, np.nan, -3.0), good.catch, good.right)
    reasons["one contrast"] = LK.fold_scores(same_c, good)["graded"]["reason"]
    bad_test = LK.Block(np.r_[good.y[:-1], np.inf], good.logc, good.catch, good.right)
    reasons["non-finite test"] = LK.fold_scores(good, bad_test)["graded"]["reason"]
    for k, v in reasons.items():
        assert v, k
    return reasons


def check_determinism_and_alias():
    rng = np.random.default_rng(6)
    tr, te = synth_block(rng, 200, "mixture"), synth_block(rng, 200, "mixture")
    a = LK.fold_scores(tr, te, tags=(3, 1, 2))
    b = LK.fold_scores(tr, te, tags=(3, 1, 2))
    for m in LK.PRIMARY:
        assert np.array_equal(a[m]["theta"], b[m]["theta"]) and a[m]["heldout"] == b[m]["heldout"]
    # the removed block shift: with one training block a0 + gamma reproduces every graded density exactly
    sc = LK.scaling(tr)
    d = LK.design(tr, sc)
    th = a["graded"]["theta"].copy()
    gamma = 0.37
    base = LK.loglik("graded", th, d)
    shifted = dict(d, y=d["y"] + gamma)
    th2 = th.copy()
    th2[0] += gamma
    assert np.allclose(LK.loglik("graded", th2, shifted), base, atol=1e-12)


def check_legacy():
    rng = np.random.default_rng(8)
    tr = synth_block(rng, 100, "mixture")
    te = synth_block(rng, 100, "mixture")
    lev = LK.legacy_levels(tr, tr)
    assert set(np.unique(lev[tr.catch])) == {0.0} and set(np.unique(lev[~tr.catch])) <= {1.0, 2.0, 3.0, 4.0, 5.0}
    # a test subset without its top level: the anchor stays at the design maximum (the port re-anchored per call)
    pars = np.array([3.0, 1.0, 2.0, 0.1, 1.0, 0.5])
    low = LK.legacy_levels(tr, te)
    keep = low <= 3
    y_sub, lev_sub = te.y[keep], low[keep]
    fixed = LK.llh_logisticB(pars, y_sub, lev_sub)
    xmax_call = float(np.max(lev_sub))
    with np.errstate(over="ignore"):
        mu = pars[2] / (1 + np.exp(-pars[1] * (lev_sub - pars[0]))) - pars[2] / (1 + np.exp(-pars[1] * (xmax_call - pars[0]))) + pars[5]
    sd = np.abs(pars[3] * mu + pars[4])
    per_call = float(np.sum(np.log(1 / (sd * LK.SQRT2PI))) - 0.5 * np.sum((y_sub - mu) ** 2 / sd ** 2))
    assert xmax_call < LK.LEGACY_XMAX and not math.isclose(fixed, per_call)
    # catch by flag: a subset without catch trials does not force its lowest present level to A = 0
    p3 = np.array([2.5, 2.0, 0.0, 1.0, 1.0, 1.0, 1.0])
    pres = ~te.catch
    by_flag = LK.llh_bimodal(p3, te.y[pres], low[pres], te.catch[pres])
    lowest = low[pres] == np.min(low[pres])
    by_min = LK.llh_bimodal(p3, te.y[pres], low[pres], lowest)
    assert not math.isclose(by_flag, by_min)
    s = LK.legacy_fold_scores(tr, te)
    assert all(s[m]["available"] for m in s), {m: s[m]["reason"] for m in s}


def main():
    worst = check_gradients()
    print("gradients: max relative error per model", {k: f"{v:.1e}" for k, v in worst.items()})
    rec = check_recovery()
    print(f"recovery (3,000 + 3,000 trials): held-out twostate - graded per trial {rec['mixture']:+.4f} under a separated "
          f"mixture, {rec['graded']:+.4f} under a graded law")
    print(f"finite log-likelihood and gradient at all {check_bounds_finite()} corners of the four models' bounds")
    check_starts_interior()
    print("moment starts outside a bound are moved to the interior; jittered starts stay inside")
    print("unavailable:", check_unavailable())
    check_determinism_and_alias()
    print("seeded fits are identical on repeat; a single-block shift is exactly an intercept alias (why v3's gamma is gone)")
    check_legacy()
    print("legacy sensitivity: levels by training edges, anchor fixed at the design maximum, catch by flag; fits available")
    print("test_likelihood: ALL OK")


if __name__ == "__main__":
    main()

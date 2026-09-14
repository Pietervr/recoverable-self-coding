"""battery.py and synthetic.py (PREREG §9, DRAFT v4; Codex continuation review 3, V3.5), synthetic inputs only: the 34
templates; the generator laws against their declared means, SDs, skew and occupancy on large draws; seeded determinism
of a generated recording; the recording summary the group rule and the X2 diagnostics read, on one real pipeline result;
and the §9 verdicts, including the loophole Codex found (three technical failures used to pass 'at most one two-state').

Run: ../../.venv/bin/python test_battery.py   (about a minute: one synthetic recording through the full pipeline)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.special import expit
from scipy.stats import skew

import battery as BT
import decoder as DEC
import recording as RC
import synthetic as SY


def check_laws():
    rng = np.random.default_rng(0)
    n = 400_000
    x = rng.normal(size=n)
    catch = np.zeros(n, dtype=bool)
    L = expit(SY.DOSE_SLOPE * x)
    out = {}
    for g in SY.GENERATORS:
        z, Lg, high = SY.latent(g, x, catch, np.random.default_rng(1))
        assert np.allclose(Lg, L)
        top, bottom = L > 0.95, L < 0.05
        out[g] = dict(mean_top=float(z[top].mean()), mean_bottom=float(z[bottom].mean()), sd_top=float(z[top].std()),
                      sd_bottom=float(z[bottom].std()), skew_bottom=float(skew(z[bottom])))
    assert abs(out["G1"]["mean_top"] - 2 * np.mean(L[L > 0.95])) < 0.02 and abs(out["G1"]["sd_top"] - 1) < 0.02
    assert abs(out["G2"]["sd_bottom"] - 1) < 0.02 and out["G2"]["skew_bottom"] > 0.3
    assert abs(out["G3"]["sd_top"] - (1 + np.mean(L[L > 0.95]))) < 0.03 and abs(out["G3"]["sd_bottom"] - 1.02) < 0.05
    for g, sep in (("X1", 2.0), ("X2", 0.8)):
        zc, _, hc = SY.latent(g, x, catch, np.random.default_rng(2))
        assert abs(hc.mean() - L.mean()) < 0.01
        assert abs(zc[hc].mean() - zc[~hc].mean() - sep) < 0.02
    zc, Lc, hc = SY.latent("X1", np.zeros(1000), np.ones(1000, dtype=bool), np.random.default_rng(3))
    assert np.all(Lc == 0) and not hc.any()
    return out


def main():
    subs = BT.templates()
    assert len(subs) == 34 and 36 not in subs and 35 not in subs, subs
    print(f"templates: {len(subs)} nocue recordings (sub-35 absent on OpenNeuro, sub-36 excluded)")
    laws = check_laws()
    print("laws:", {g: {k: round(v, 3) for k, v in d.items()} for g, d in laws.items()})

    tmpl = SY.template(subs[0], "nocue")
    a = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 0, subs[0]))
    b = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 0, subs[0]))
    c = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 1, subs[0]))
    assert np.array_equal(a["X"], b["X"]) and not np.array_equal(a["X"], c["X"])
    nodrift = SY.generate(tmpl, "X1", 0.8, False, tags=(1, 3, 1, 1, 0, subs[0]))
    shift = (a["trials"].z_true - nodrift["trials"].z_true).to_numpy()
    assert np.allclose(shift, SY.DRIFT_PER_BLOCK * (a["trials"].block.to_numpy() - 1)), np.unique(np.round(shift, 6))
    print("seeded generation reproducible; with the same draws, drift adds exactly 0.3 (b - 1) to z in block b "
          "(block means of z also move with each block's staircase contrasts, so the shift is checked per trial)")

    res = RC.recording_scores(a, subs[0], "nocue")
    s = BT.summary(res)
    assert s["status"] == "ok" and s["evidence"].shape == (20, 3)
    assert np.isfinite(s["twostate_separation_median"]) and np.isfinite(s["occupancy_abs_error_median"])
    assert "folds" not in s and "decoder" not in s
    print(f"summary of one pipeline result: evidence {s['evidence'].shape}, median separation "
          f"{s['twostate_separation_median']:.2f} SD, median occupancy error {s['occupancy_abs_error_median']:.3f}, "
          f"main-window AUC {np.round(np.nanmean(s['auc'][[RC.WINDOWS.index(w) for w in DEC.MAIN]], axis=1), 2).tolist()}")

    v = BT.cell_verdicts({
        ("G1", 0, 0): ["graded", "inconclusive/mixed", "two-state"],
        ("G1", 0, 1): ["technical failure", "technical failure", "technical failure"],
        ("G2", 1, 0): ["two-state", "two-state", "graded"],
        ("G3", 1, 1): ["insufficient availability", "graded", "insufficient sensitivity"],
        ("X1", 1, 0): ["two-state", "inconclusive/mixed", "two-state"],
        ("X1", 0, 0): ["graded", "graded", "graded"],
        ("X2", 1, 0): ["graded", "graded", "graded"],
    })
    assert v[("G1", 0, 0)] == "pass"
    assert v[("G1", 0, 1)] == "fail", "three technical failures must not pass a graded cell"
    assert v[("G2", 1, 0)] == "fail" and v[("G3", 1, 1)] == "fail"
    assert v[("X1", 1, 0)] == "pass" and v[("X1", 0, 0)] == "reported" and v[("X2", 1, 0)] == "reported"
    print("verdicts: a graded cell of three technical failures fails; two non-substantive replicates fail; X1 at 0.8 needs "
          "two two-state replicates; X1 at 0.6 and X2 are reported")
    print("test_battery: ALL OK")


if __name__ == "__main__":
    main()

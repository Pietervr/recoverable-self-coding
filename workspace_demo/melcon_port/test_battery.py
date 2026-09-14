"""battery.py and synthetic.py (PREREG §9, DRAFT v5; Codex continuation review 4, §4–§5), synthetic inputs only.

Checks: the 34 templates; the generator laws against their declared means, SDs, skew and occupancy on large draws; the
exact latent ranking AUC per trial against Monte Carlo, and the calibration statistic's population limits against Codex's
independent stdlib calculation (X1 0.7438555564, X2 0.6475829769 on the first eight templates; 0.7425603803 and
0.6470629738 on all 34); strength targets inside every generator's limit; seeded determinism of a generated recording;
the recording summary on one real pipeline result (minimum and full component gap, readout separation); the §9 verdicts
(Codex's technical-failure loophole, completeness, unusable calibrations); calibration history (refinement points and
both checks saved); result provenance (an existing result with another identity, or unreadable, is refused; a matching one
is reused without generating); and the run dispatch carrying calibration usability into every manifest.

Run: ../../.venv/bin/python test_battery.py   (about a minute: one synthetic recording through the full pipeline)
"""
import json
import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.special import expit
from scipy.stats import skew

import battery as BT
import decoder as DEC
import recording as RC
import synthetic as SY

CODEX_LIMITS = {"X1": (0.7438555564, 0.7425603803), "X2": (0.6475829769, 0.6470629738)}


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


def check_latent_auc():
    """present_latent_auc against Monte Carlo at a few (L, h) for every generator."""
    rng = np.random.default_rng(7)
    n = 1_000_000
    worst = 0.0
    for g in SY.GENERATORS:
        for Lv, h in ((0.2, 0), (0.5, 1), (0.9, 0)):
            zp, _, _ = SY.latent(g, np.full(n, np.log(Lv / (1 - Lv)) / SY.DOSE_SLOPE), np.zeros(n, bool), rng)
            zp = zp + SY.HEMI_SHIFT * h
            zc, _, _ = SY.latent(g, np.zeros(n), np.ones(n, bool), rng)
            mc = float(np.mean(zp > zc))
            exact = float(SY.present_latent_auc(g, np.array([Lv]), np.array([h]))[0])
            worst = max(worst, abs(mc - exact))
            assert abs(mc - exact) < 0.003, (g, Lv, h, mc, exact)
    return worst


def check_limits(subs):
    lim = {}
    for g in SY.GENERATORS:
        first, allv = BT.population_calibration_auc(g, subs[:BT.N_CAL]), BT.population_calibration_auc(g, subs)
        lim[g] = (first, allv)
        assert 0.5 < first < 1.0
        for st in BT.STRENGTHS:
            _, target = BT.strength_target(g, st, subs[:BT.N_CAL])
            assert 0.5 < target < first
    for g, (f8, a34) in CODEX_LIMITS.items():
        assert abs(lim[g][0] - f8) < 1e-9 and abs(lim[g][1] - a34) < 1e-9, (g, lim[g], f8, a34)
    assert all(lim[g][0] < 0.77 for g in ("X1", "X2"))
    return lim


def check_verdicts():
    v = BT.cell_verdicts({
        ("G1", "weak", 0): ["graded", "inconclusive/mixed", "two-state"],
        ("G1", "weak", 1): ["technical failure", "technical failure", "technical failure"],
        ("G2", "strong", 0): ["two-state", "two-state", "graded"],
        ("G3", "strong", 1): ["insufficient availability", "graded", "insufficient sensitivity"],
        ("X1", "strong", 0): ["two-state", "inconclusive/mixed", "two-state"],
        ("X1", "weak", 0): ["graded", "graded", "graded"],
        ("X2", "strong", 0): ["graded", "graded", "graded"],
    })
    assert v[("G1", "weak", 0)] == "pass"
    assert v[("G1", "weak", 1)] == "fail", "three technical failures must not pass a graded cell"
    assert v[("G2", "strong", 0)] == "fail" and v[("G3", "strong", 1)] == "fail"
    assert v[("X1", "strong", 0)] == "pass" and v[("X1", "weak", 0)] == "reported" and v[("X2", "strong", 0)] == "reported"
    # completeness (Codex: two of three replicates could pass; entirely missing cells disappeared)
    part = BT.cell_verdicts({("G1", "weak", 0): ["graded", "graded"], ("X1", "strong", 0): ["two-state", "two-state", None]},
                            expected=[("G1", "weak", 0), ("X1", "strong", 0), ("G2", "weak", 1)])
    assert part == {("G1", "weak", 0): "incomplete", ("X1", "strong", 0): "incomplete", ("G2", "weak", 1): "incomplete"}, part
    # an unusable calibration is a diagnostic, never a pass or a fail
    diag = BT.cell_verdicts({("X1", "strong", 0): ["two-state"] * 3, ("G1", "weak", 0): ["two-state"] * 3},
                            calibration_usable={("X1", "strong"): False, ("G1", "weak"): True})
    assert diag[("X1", "strong", 0)] == "diagnostic: calibration not usable" and diag[("G1", "weak", 0)] == "fail"


def check_calibration_history():
    with patch.object(BT, "_draw", side_effect=lambda g, amp, d, si, subjects: amp), \
         patch.object(BT, "calibration_statistic", return_value=0.65), \
         patch.object(BT, "population_calibration_auc", return_value=0.9):
        cal = BT.calibrate("X1", "strong", [1], log=lambda _: None)
    assert cal["refined"] and not cal["accepted"] and abs(cal["target"] - 0.86) < 1e-12
    assert cal["first"]["amplitude"] == BT.CAL_GRID[-1] and cal["refinement"], cal
    assert set(cal["grid"]) == {str(float(a)) for a in BT.CAL_GRID} and not cal["grid_reaches_target"]
    assert all(k not in cal["grid"] for k in cal["refinement"])
    # the locked store: entries from separate processes accumulate; an existing entry is never replaced
    with tempfile.TemporaryDirectory(prefix="melcon-cal-store-") as td, patch.object(BT, "OUT_DIR", td):
        run_dir = BT.run_directory()
        BT.save_calibration(run_dir, dict(cal, generator="X1", strength="strong"))
        BT.save_calibration(run_dir, dict(cal, generator="G1", strength="weak"))
        assert set(BT.load_calibration(run_dir)) == {("X1", "strong"), ("G1", "weak")}
        try:
            BT.save_calibration(run_dir, dict(cal, generator="X1", strength="strong", amplitude=1.0))
            raise AssertionError("an existing calibration must not be replaced")
        except RuntimeError:
            pass
    return cal


def check_provenance(subs):
    with tempfile.TemporaryDirectory(prefix="melcon-battery-test-") as td:
        entry = dict(generator="X1", strength="strong", amplitude=0.7, accepted=True, target=0.72, check=0.73)
        m = BT.recording_manifest("abc", "X1", 1, 0, 0, subs[0], entry)
        path = os.path.join(td, "x.npy")
        with open(path, "wb") as fh:
            np.save(fh, np.array([dict(status="ok", manifest=m)], dtype=object), allow_pickle=True)
        with patch.object(SY, "generate", side_effect=AssertionError("must not generate")):
            assert BT.run_recording(m, path) == path
            other = dict(m, amplitude=999.0)
            try:
                BT.run_recording(other, path)
                raise AssertionError("a result with another identity must be refused")
            except RuntimeError:
                pass
            bad = os.path.join(td, "old.npy")
            with open(bad, "wb") as fh:
                fh.write(b"old result with no authenticated identity")
            try:
                BT.run_recording(m, bad)
                raise AssertionError("an unreadable result must be refused")
            except RuntimeError:
                pass
        # run dispatch from an unusable calibration: every manifest carries it
        with patch.object(BT, "OUT_DIR", td), patch.object(BT, "templates", return_value=[subs[0]]):
            run_dir = BT.run_directory()
            cal = [dict(generator="X1", strength=s, amplitude=0.7, check=0.6, target=0.72, accepted=False) for s in BT.STRENGTHS]
            with open(os.path.join(run_dir, "calibration.json"), "w") as fh:
                json.dump(cal, fh)
            calls = []
            with patch.object(BT, "run_recording", side_effect=lambda man, p: calls.append((man, p))), \
                 patch.object(sys, "argv", ["battery.py", "--run", "--generators", "X1"]):
                BT.main()
        assert len(calls) == 12 and all(not man["calibration_accepted"] for man, _ in calls)
        assert len({man["calibration"] for man, _ in calls}) == 2 and all(p.startswith(run_dir) for _, p in calls)
    return len(calls)


def main():
    subs = BT.templates()
    assert len(subs) == 34 and 36 not in subs and 35 not in subs, subs
    print(f"templates: {len(subs)} nocue recordings (sub-35 absent on OpenNeuro, sub-36 excluded)")
    laws = check_laws()
    print("laws:", {g: {k: round(v, 3) for k, v in d.items()} for g, d in laws.items()})
    worst = check_latent_auc()
    print(f"latent ranking AUC per trial matches Monte Carlo (1e6 pairs) for all generators; worst difference {worst:.4f}")
    lim = check_limits(subs)
    print("population limits of the calibration statistic (first eight / all 34): "
          + ", ".join(f"{g} {a:.4f}/{b:.4f}" for g, (a, b) in lim.items()) + "; X1 and X2 equal Codex's values to 1e-9")

    tmpl = SY.template(subs[0], "nocue")
    a = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 0, subs[0]))
    b = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 0, subs[0]))
    c = SY.generate(tmpl, "X1", 0.8, True, tags=(1, 3, 1, 1, 1, subs[0]))
    assert np.array_equal(a["X"], b["X"]) and not np.array_equal(a["X"], c["X"])
    nodrift = SY.generate(tmpl, "X1", 0.8, False, tags=(1, 3, 1, 1, 0, subs[0]))
    shift = (a["trials"].z_true - nodrift["trials"].z_true).to_numpy()
    assert np.allclose(shift, SY.DRIFT_PER_BLOCK * (a["trials"].block.to_numpy() - 1)), np.unique(np.round(shift, 6))
    print("seeded generation reproducible; with the same draws, drift adds exactly 0.3 (b - 1) to z in block b")

    res = RC.recording_scores(a, subs[0], "nocue")
    s = BT.summary(res)
    assert s["status"] == "ok" and s["evidence"].shape == (20, 3) and s["section2"]["passed"]
    for k in ("twostate_min_gap_median", "twostate_full_gap_median", "occupancy_abs_error_median",
              "readout_component_separation_median", "readout_latent_corr_median"):
        assert np.isfinite(s[k]), k
    assert s["twostate_full_gap_median"] >= s["twostate_min_gap_median"]
    assert "folds" not in s and "decoder" not in s
    print(f"summary of one pipeline result (X1, amplitude 0.8, drift): minimum gap {s['twostate_min_gap_median']:.3f} SD, "
          f"full gap at held-out doses {s['twostate_full_gap_median']:.3f} SD, readout component separation "
          f"{s['readout_component_separation_median']:.3f} SD, readout-latent correlation {s['readout_latent_corr_median']:.3f}, "
          f"occupancy error {s['occupancy_abs_error_median']:.3f}, main-window AUC "
          f"{np.round(np.nanmean(s['auc'][[RC.WINDOWS.index(w) for w in DEC.MAIN]], axis=1), 2).tolist()}")

    check_verdicts()
    print("verdicts: three technical failures fail a graded cell; incomplete and missing cells are 'incomplete'; an unusable "
          "calibration is a diagnostic; X1 strong needs two two-state replicates; X1 weak and X2 are reported")
    cal = check_calibration_history()
    print(f"calibration history: grid, first check {cal['first']}, refinement points {list(cal['refinement'])} and the second "
          "check are saved; a missed target is not accepted")
    n = check_provenance(subs)
    print(f"provenance: a matching result is reused without generating; another identity or an unreadable file is refused; "
          f"{n} jobs dispatched from an unusable calibration all carry calibration_accepted = False")
    print("test_battery: ALL OK")


if __name__ == "__main__":
    main()

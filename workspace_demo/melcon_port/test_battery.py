"""battery.py and synthetic.py (PREREG §9, DRAFT v6; Codex, v5 calibration revision record), synthetic inputs only.

Checks: the 34 templates; the generator laws against their declared means, SDs, skew and occupancy on large draws; the
exact latent ranking AUC per trial against Monte Carlo; G2's trapezoidal CDF against adaptive quadrature and against
Codex's fine-grid limit (0.7837336528 on the first eight templates; v5's cumulative sum gave 0.7839291588); X1 and X2
against Codex's stdlib values; seeded determinism; the recording summary on one real pipeline result and one real decoder
run through recording_aucs; the seed map (phases disjoint, v5's phase retired); the calibration statistic's completeness
(missing, failed, non-finite, out-of-range, wrong-shape, duplicated recordings); the interior bracket (lowest already
meets, reached only at the top, incomplete before and after the crossing, non-monotone, exact hit); reach (no headroom,
incomplete, an unusable reach draws nothing); the search (grid and refinement on the calibration seed, first check and a
NEW terminal check on separate seeds, refinement reuse and clipping, at most 15 statistics, a terminal miss stops, no
bracket draws no check); strength resolution (overlapping bands, reversal); the verdicts; the sealed stores (accumulate,
never replaced, damaged or unreadable refused); result provenance (reuse without generating; a tampered payload, a
missing sidecar, another identity and an incomplete schema are refused; verify_runtime refuses a module changed since
import and a manifest that differs); the run dispatch (cells without an amplitude are not run, unusable cells carry
calibration_accepted False); and v5's namespace preserved byte for byte.

Run: ../../.venv/bin/python test_battery.py   (about a minute: one synthetic recording through the full pipeline)
"""
import json
import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy import integrate
from scipy.special import expit
from scipy.stats import skew, skewnorm

import battery as BT
import decoder as DEC
import likelihood as LK
import recording as RC
import synthetic as SY

CODEX_LIMITS = {"X1": (0.7438555564, 0.7425603803), "X2": (0.6475829769, 0.6470629738)}
CODEX_G2_FINE_GRID_FIRST_EIGHT = 0.7837336527984881          # reviews/2026-09-14_melcon_v5_scoped_checks.json
V5_G2_CUMSUM_FIRST_EIGHT = 0.7839291588328964
V5_NAMESPACE = os.path.join(BT.OUT_DIR, "v5-7fcb46729408")
V5_SHA256 = {"calibration.json": "87c96314af0f590880e447f26d103c216f579181993c0404ff00c83ea6fbeba3",
             "manifest.json": "5ea038c7e7349e9cd9f8d5fcd133c960fff6bf357aa9074aee58057c245cfb2f"}
NAN = float("nan")


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


def check_g2_precision(subs):
    """The trapezoidal G2 CDF against adaptive quadrature of P(e_catch - e_present < m) = int f(v) F(v + m) dv, and the
    first-eight-template limit against Codex's fine-grid value."""
    a = SY.SKEW_SHAPE
    dlt = a / np.sqrt(1 + a * a)
    mean, sd = dlt * np.sqrt(2 / np.pi), np.sqrt(1 - 2 * dlt * dlt / np.pi)
    worst = 0.0
    for Lv in (0.0, 0.1, 0.35, 0.6, 0.9, 1.0):
        for h in (0, 1):
            m = 2.0 * Lv + SY.HEMI_SHIFT * h
            ref, _ = integrate.quad(lambda v: sd * skewnorm.pdf(mean + sd * v, a) * skewnorm.cdf(mean + sd * (v + m), a),
                                    -12.0, 12.0, epsabs=1e-13, epsrel=1e-12, limit=400)
            got = float(SY.present_latent_auc("G2", np.array([Lv]), np.array([h]))[0])
            worst = max(worst, abs(got - ref))
    assert worst < 1e-6, worst
    lim8 = BT.latent_ranking_reference("G2", subs[:8])
    assert abs(lim8 - CODEX_G2_FINE_GRID_FIRST_EIGHT) < 2e-6, lim8
    assert lim8 < V5_G2_CUMSUM_FIRST_EIGHT - 1.5e-4
    return worst, lim8


def check_limits(subs):
    lim = {}
    for g in SY.GENERATORS:
        first, allv = BT.latent_ranking_reference(g, subs[:8]), BT.latent_ranking_reference(g, subs)
        lim[g] = (first, allv)
        assert 0.5 < first < 1.0
    for g, (f8, a34) in CODEX_LIMITS.items():
        assert abs(lim[g][0] - f8) < 1e-9 and abs(lim[g][1] - a34) < 1e-9, (g, lim[g], f8, a34)
    for R in (0.52, 0.596293, 0.706, 0.77):
        assert 0.5 < BT.target_for(R, "weak") < BT.target_for(R, "strong") < R
    assert abs(BT.target_for(0.705078, "strong") - 0.6640624) < 1e-6          # Codex's illustrative X1 strong value
    return lim


def check_seed_map(subs):
    assert 2 not in BT.SEED_PHASES.values() and len(set(BT.SEED_PHASES.values())) == len(BT.SEED_PHASES)
    tags = [(BT.SEED_PHASES["benchmark"], 0)]
    for g in SY.GENERATORS:
        for s in subs:
            tags += [BT.seed_tags("reach", g, d, s) for d in BT.REACH_DRAWS]
            for si in range(len(BT.STRENGTHS)):
                tags += [BT.seed_tags(p, g, si, s) for p in ("calibration", "check", "terminal")]
                tags += [(BT.SEED_PHASES["stage_c"], SY.GENERATORS.index(g), si, di, r, s)
                         for di in range(len(BT.DRIFTS)) for r in range(BT.N_REP)]
    entropy = [tuple([SY.SEED, *t]) for t in tags]
    assert len(set(entropy)) == len(entropy)
    return len(entropy)


def rows(subjects, aucs):
    return [dict(status="ok", subject=int(s), auc=a) for s, a in zip(subjects, aucs)]


def check_statistic_completeness():
    S = [1, 2, 3]
    full = [np.full((2, 10), v).tolist() for v in (0.6, 0.7, 0.8)]
    st = BT.calibration_statistic(rows(S, full), S)
    assert st["complete"] and abs(st["value"] - 0.7) < 1e-12 and st["n_auc_finite"] == 60 == st["n_auc_expected"]
    bad = [np.array(a) for a in full]
    bad[1][0, 3] = np.nan
    st = BT.calibration_statistic(rows(S, [b.tolist() for b in bad]), S)
    assert not st["complete"] and np.isnan(st["value"]) and st["n_auc_finite"] == 59 and st["failures"][0][0] == 2
    cases = {
        "failed decoder": [dict(status="excluded: fewer than 10 catch trials", subject=1, auc=None)] + rows(S[1:], full[1:]),
        "missing recording": rows(S[:2], full[:2]),
        "out of range": rows(S, [full[0], np.full((2, 10), 1.2).tolist(), full[2]]),
        "wrong shape": rows(S, [full[0], np.full((1, 10), 0.7).tolist(), full[2]]),
        "duplicated recording": rows(S, full) + rows([1], full[:1]),
        "unexpected recording": rows(S, full) + rows([9], full[:1]),
    }
    for name, rr in cases.items():
        st = BT.calibration_statistic(rr, S)
        assert not st["complete"] and np.isnan(st["value"]) and st["failures"], name


def check_bracket():
    fb = BT.find_bracket
    assert not fb({0.2: 0.7, 0.4: 0.8, 6.4: 0.9}, 0.65)["usable"]                        # lowest already meets
    r = fb({0.2: 0.5, 0.4: 0.55, 3.2: 0.6, 6.4: 0.7}, 0.65)                               # reached only at the top
    assert not r["usable"] and "not reached" in r["reason"]
    assert not fb({0.2: 0.5, 0.4: NAN, 0.7: 0.7}, 0.6)["usable"]                         # incomplete before the crossing
    assert not fb({0.2: NAN, 0.4: 0.7}, 0.6)["usable"]
    r = fb({0.2: 0.5, 0.4: 0.7, 0.7: NAN, 6.4: 0.8}, 0.6)                                 # incomplete after it
    assert r["usable"] and (r["lo"], r["hi"]) == (0.2, 0.4) and abs(r["amplitude"] - 0.3) < 1e-12
    curve = {0.2: 0.5, 0.4: 0.62, 0.7: 0.55, 1.0: 0.7}                                    # non-monotone: first crossing
    r = fb(curve, 0.6)
    assert r["usable"] and r["hi"] == 0.4 and abs(r["amplitude"] - (0.2 + 0.1 / 0.12 * 0.2)) < 1e-12
    assert BT.nonmonotone_steps(curve) == [[0.4, 0.7, 0.62, 0.55]]
    assert fb({0.2: 0.5, 0.4: 0.6}, 0.6)["amplitude"] == 0.4                              # exact hit
    assert BT.refinement_points(0.25) == [0.2, 0.2188, 0.25, 0.2812, 0.3125]              # clipped at 0.2
    assert BT.refinement_points(6.0) == [4.5, 5.25, 6.0, 6.4]                             # clipped and merged at 6.4


class FakeWorker:
    """Replaces battery._cell_recording: the recording's AUC is curve(amplitude) + an offset per seed phase."""

    def __init__(self, curve, offsets=None, reach_values=None, nan_phase=None):
        self.curve, self.offsets, self.reach_values, self.nan_phase = curve, offsets or {}, reach_values, nan_phase
        self.calls = []

    def __call__(self, generator, amplitude, tags, subject, run_dir=None):
        phase = {v: k for k, v in BT.SEED_PHASES.items()}[tags[0]]
        self.calls.append((phase, round(amplitude, 6), tuple(tags)))
        v = self.reach_values[tags[2]] if phase == "reach" and self.reach_values else self.curve(amplitude)
        v += self.offsets.get(phase, 0.0)
        auc = np.full((2, 10), v)
        if phase == self.nan_phase:
            auc[0, 0] = np.nan
        return dict(status="ok", subject=int(subject), tags=list(tags), auc=auc.tolist(), generate_s=0.0, decoder_s=0.0,
                    worker_peak_rss_mb=0.0)


def smooth_curve(a):
    return 0.5 + 0.2 * (1.0 - np.exp(-a / 0.8))


def _reach(worker, subs, generator="X1"):
    with patch.object(BT, "_cell_recording", side_effect=worker):
        return BT.seal(BT.reach(generator, subs, log=lambda _: None))


def _calibrate(worker, reach_entry, subs, strength="strong", generator="X1"):
    with patch.object(BT, "_cell_recording", side_effect=worker):
        return BT.calibrate(generator, strength, reach_entry, subs, log=lambda _: None)


def check_reach_and_search(subs):
    S = subs[:2]
    w = FakeWorker(smooth_curve, reach_values={0: smooth_curve(6.4) + 0.005, 1: smooth_curve(6.4) - 0.005})
    r = _reach(w, S)
    assert r["usable"] and abs(r["reach"] - smooth_curve(6.4)) < 1e-12 and abs(r["disagreement"] - 0.01) < 1e-12
    assert [c[0] for c in w.calls] == ["reach"] * 4 and len({c[2] for c in w.calls}) == 4
    assert len(r["draws"]) == 2 and all(len(d["auc"]) == 2 for d in r["draws"]) and 0.5 < r["latent_ranking_reference"] < 1

    # A: accepted on the first independent check, no refinement
    w = FakeWorker(smooth_curve)
    e = _calibrate(w, r, S)
    assert e["accepted"] and e["refinement"] is None and e["terminal_check"] is None and e["statistics_drawn"] == 9
    grid_calls = [c for c in w.calls if c[0] == "calibration"]
    assert len(grid_calls) == 8 * 2 and 6.4 in {c[1] for c in grid_calls}                  # 6.4 on the calibration seed
    assert {c[2][:3] for c in grid_calls} == {(5, 3, 1)}                                  # common random numbers
    assert abs(e["target"] - BT.target_for(r["reach"], "strong")) < 1e-15 and e["first_bracket"]["hi"] == 1.5

    # B: first check misses -> one refinement on the calibration seed -> NEW terminal check decides
    w = FakeWorker(smooth_curve, offsets={"check": 0.05})
    e = _calibrate(w, r, S)
    phases = [c[0] for c in w.calls]
    assert e["accepted"] and e["first_check"]["within_tolerance"] is False and e["statistics_drawn"] == 15
    assert phases == ["calibration"] * 16 + ["check"] * 2 + ["calibration"] * 10 + ["terminal"] * 2
    check_tags = {c[2] for c in w.calls if c[0] == "check"}
    term_tags = {c[2] for c in w.calls if c[0] == "terminal"}
    cal_tags = {c[2] for c in w.calls if c[0] == "calibration"}
    assert not (check_tags & term_tags) and not (term_tags & cal_tags) and not (check_tags & cal_tags)
    assert e["amplitude"] == e["terminal_check"]["amplitude"] == e["refinement"]["bracket"]["amplitude"]
    assert e["check"] == e["terminal_check"]["statistic"]["value"]

    # C: terminal miss -> not usable, and the search stops
    w = FakeWorker(smooth_curve, offsets={"check": 0.05, "terminal": 0.05})
    e = _calibrate(w, r, S)
    assert not e["accepted"] and e["unusable_reason"].startswith("terminal check") and e["amplitude"] is not None
    assert len(w.calls) == 15 * 2 and w.calls[-1][0] == "terminal"

    # D: no bracket (target never reached below 6.4) -> no check is drawn
    w = FakeWorker(lambda a: 0.55 if a < 6.4 else 0.7)
    e = _calibrate(w, r, S)
    assert not e["accepted"] and e["amplitude"] is None and "no usable bracket" in e["unusable_reason"]
    assert {c[0] for c in w.calls} == {"calibration"} and e["statistics_drawn"] == 8

    # E: refinement reuses an identical grid point (0.2 after clipping) and draws only the new ones
    lin = lambda a: min(0.5 + 0.4 * a, 0.7)                                              # noqa: E731
    rlin = _reach(FakeWorker(lin), S)
    w = FakeWorker(lin, offsets={"check": 0.05})
    e = _calibrate(w, rlin, S, strength="weak")
    assert e["first_bracket"]["lo"] == 0.2 and e["refinement"]["reused"] == [0.2]
    assert len(e["refinement"]["statistics"]) == 4 and e["statistics_drawn"] == 8 + 1 + 4 + 1

    # F: an incomplete check counts as a miss; an incomplete terminal check is not usable
    w = FakeWorker(smooth_curve, nan_phase="terminal", offsets={"check": 0.05})
    e = _calibrate(w, r, S)
    assert not e["accepted"] and e["unusable_reason"] == "terminal check incomplete"

    # reach without headroom, or incomplete: not usable, and calibrate draws nothing
    for worker, text in ((FakeWorker(lambda a: 0.49), "no headroom"), (FakeWorker(smooth_curve, nan_phase="reach"), "incomplete")):
        rr = _reach(worker, S)
        assert not rr["usable"] and text in rr["unusable_reason"]
        w = FakeWorker(smooth_curve)
        e = _calibrate(w, rr, S)
        assert not e["accepted"] and not w.calls and e["unusable_reason"].startswith("reach not usable")


def check_strength_resolution():
    reach = {"X2": dict(reach=0.596293, usable=True, unusable_reason=None),
             "G1": dict(reach=0.75, usable=True, unusable_reason=None),
             "G3": dict(reach=0.80, usable=True, unusable_reason=None)}
    cal = {("X2", "weak"): dict(accepted=True, check=0.56), ("X2", "strong"): dict(accepted=True, check=0.575),
           ("G1", "weak"): dict(accepted=True, check=0.63), ("G1", "strong"): dict(accepted=True, check=0.62),
           ("G3", "weak"): dict(accepted=True, check=0.64), ("G3", "strong"): dict(accepted=True, check=0.74)}
    r = BT.strength_resolution(reach, cal)
    assert r["X2"]["bands_overlap"] and not r["X2"]["resolved"] and abs(r["X2"]["target_gap"] - 0.0288879) < 1e-7
    assert r["G1"]["reversal"] and not r["G1"]["bands_overlap"] and not r["G1"]["resolved"]
    assert r["G3"]["resolved"] and r["G2"]["status"] == "reach missing"
    return r


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
    part = BT.cell_verdicts({("G1", "weak", 0): ["graded", "graded"], ("X1", "strong", 0): ["two-state", "two-state", None]},
                            expected=[("G1", "weak", 0), ("X1", "strong", 0), ("G2", "weak", 1)])
    assert part == {("G1", "weak", 0): "incomplete", ("X1", "strong", 0): "incomplete", ("G2", "weak", 1): "incomplete"}, part
    diag = BT.cell_verdicts({("X1", "strong", 0): ["two-state"] * 3, ("G1", "weak", 0): ["two-state"] * 3,
                             ("X2", "weak", 0): [None] * 3},
                            calibration_usable={("X1", "strong"): False, ("G1", "weak"): True, ("X2", "weak"): False},
                            expected=[("X1", "strong", 0), ("G1", "weak", 0), ("X2", "weak", 0), ("G2", "weak", 0)])
    assert diag[("X1", "strong", 0)] == "diagnostic: calibration not usable" and diag[("G1", "weak", 0)] == "fail"
    assert diag[("X2", "weak", 0)] == "diagnostic: calibration not usable; incomplete"
    assert diag[("G2", "weak", 0)] == "incomplete"                                        # not calibrated is not a diagnostic


def fake_result(manifest, drop=None):
    nW, nM = len(RC.WINDOWS), len(LK.PRIMARY)
    res = dict(status="ok", subject=manifest["subject"], task="nocue", windows=list(RC.WINDOWS), models=list(LK.PRIMARY),
               evidence=np.zeros((nW, nM)), available=np.ones((nW, nM), bool), delta=np.zeros(nW),
               n_trials=np.zeros(nW, int), auc=np.full((nW, 2), 0.6), twostate_min_gap_median=0.1,
               twostate_full_gap_median=1.0, occupancy_abs_error_median=0.1,
               readout_highlow_contrast_unadjusted_median=1.0, readout_latent_corr_median=0.5, manifest=manifest)
    if drop:
        res.pop(drop)
    return res


def check_stores_and_provenance(subs):
    with tempfile.TemporaryDirectory(prefix="melcon-v6-test-") as td, patch.object(BT, "OUT_DIR", td):
        run_dir = BT.run_directory()
        assert os.path.basename(run_dir).startswith("v6-")
        ident = BT.verify_runtime(run_dir)
        assert ident == BT.digest(BT.config_identity())
        idn = BT.config_identity()
        assert idn["runtime"]["bms_sha256"] == BT._sha_file(BT.BMS_PATH) and len(idn["template_digests"]) == len(subs)
        assert idn["templates"] == subs and idn["seed_phases"] == BT.SEED_PHASES and "threadpools" in idn["runtime"]
        with patch.dict(BT.LOADED_CODE, {"battery.py": "0" * 64}):
            try:
                BT.verify_runtime(run_dir)
                raise AssertionError("a module changed since import must be refused")
            except RuntimeError as e:
                assert "changed on disk" in str(e)
        # sealed stores: accumulate, never replaced, damage refused
        e1 = BT.save_store(run_dir, "calibration", dict(generator="X1", strength="strong", amplitude=0.7, accepted=True,
                                                        target=0.66, check=0.67, unusable_reason=None))
        BT.save_store(run_dir, "calibration", dict(generator="G1", strength="weak", amplitude=0.6, accepted=True, target=0.62,
                                                   check=0.62, unusable_reason=None))
        assert set(BT.load_calibration(run_dir)) == {("X1", "strong"), ("G1", "weak")}
        assert BT.load_calibration(run_dir)[("X1", "strong")]["sha256"] == e1["sha256"]
        try:
            BT.save_store(run_dir, "calibration", dict(generator="X1", strength="strong", amplitude=1.0, accepted=True))
            raise AssertionError("an existing calibration must not be replaced")
        except RuntimeError:
            pass
        path = os.path.join(run_dir, "calibration.json")
        with open(path) as fh:
            good = fh.read()
        for damaged in (good.replace('"amplitude": 0.7', '"amplitude": 0.71'), good[:-5]):
            with open(path, "w") as fh:
                fh.write(damaged)
            try:
                BT.load_calibration(run_dir)
                raise AssertionError("a damaged store must be refused")
            except RuntimeError:
                pass
        with open(path, "w") as fh:
            fh.write(good)
        # a namespace manifest that differs is refused, by run_directory and by verify_runtime
        mpath = os.path.join(run_dir, "manifest.json")
        with open(mpath) as fh:
            man = json.load(fh)
        with open(mpath, "w") as fh:
            json.dump(dict(man, cal_tol=0.05), fh)
        for fn in (BT.run_directory, lambda: BT.verify_runtime(run_dir)):
            try:
                fn()
                raise AssertionError("a differing namespace manifest must be refused")
            except RuntimeError:
                pass
        with open(mpath, "w") as fh:
            json.dump(man, fh)

        # recording results: sidecar checksum, manifest and schema on reuse
        m = BT.recording_manifest(ident, "X1", 1, 0, 0, subs[0], e1)
        assert m["calibration"] == e1["sha256"] and m["tags"][0] == BT.SEED_PHASES["stage_c"]
        rpath = BT.cell_path(run_dir, "X1", 1, 0, 0, subs[0])
        BT.write_result(rpath, fake_result(m))
        with patch.object(SY, "generate", side_effect=AssertionError("must not generate")):
            assert BT.run_recording(m, rpath) == rpath

            def refused(fn, text):
                try:
                    fn()
                    raise AssertionError(f"must be refused: {text}")
                except RuntimeError as err:
                    assert text in str(err), (text, str(err))
            refused(lambda: BT.run_recording(dict(m, amplitude=999.0), rpath), "another identity")
            with open(rpath, "rb") as fh:
                data = bytearray(fh.read())
            data[-3] ^= 0xFF
            with open(rpath, "wb") as fh:
                fh.write(bytes(data))
            refused(lambda: BT.run_recording(m, rpath), "payload SHA-256")
            BT.write_result(rpath, fake_result(m))
            os.remove(rpath + ".sha256")
            refused(lambda: BT.run_recording(m, rpath), "cannot be read")
            BT.write_result(rpath, fake_result(m, drop="delta"))
            refused(lambda: BT.run_recording(m, rpath), "schema")
            os.remove(rpath)
            refused(lambda: BT.run_recording(m, rpath), "cannot be read")               # a sidecar without its payload

    # run dispatch: a cell without an amplitude is not run; an unusable one runs as a diagnostic
    with tempfile.TemporaryDirectory(prefix="melcon-v6-dispatch-") as td, patch.object(BT, "OUT_DIR", td), \
            patch.object(BT, "templates", return_value=[subs[0]]):
        run_dir = BT.run_directory()
        weak = BT.save_store(run_dir, "calibration", dict(generator="X1", strength="weak", amplitude=0.7, check=0.7, target=0.62,
                                                          accepted=False, unusable_reason="terminal check outside"))
        BT.save_store(run_dir, "calibration", dict(generator="X1", strength="strong", amplitude=None, check=None, target=0.66,
                                                   accepted=False, unusable_reason="no usable bracket: ..."))
        calls = []
        with patch.object(BT, "run_recording", side_effect=lambda man, p: calls.append((man, p))), \
             patch.object(sys, "argv", ["battery.py", "--run", "--generators", "X1"]):
            BT.main()
        assert len(calls) == 6 and all(man["strength"] == "weak" and not man["calibration_accepted"] for man, _ in calls)
        assert {man["calibration"] for man, _ in calls} == {weak["sha256"]} and all(p.startswith(run_dir) for _, p in calls)
    return len(calls)


def check_v5_preserved():
    ns = BT.namespace_path(BT.config_identity())
    assert os.path.basename(ns).startswith("v6-") and os.path.basename(ns) != os.path.basename(V5_NAMESPACE)
    if not os.path.isdir(V5_NAMESPACE):
        return "v5 namespace not on this machine (untracked results): hash check skipped"
    for f, h in V5_SHA256.items():
        assert BT._sha_file(os.path.join(V5_NAMESPACE, f)) == h, f
    return "v5 namespace calibration.json and manifest.json unchanged (SHA-256)"


def main():
    subs = BT.templates()
    assert len(subs) == 34 and 36 not in subs and 35 not in subs, subs
    print(f"templates: {len(subs)} nocue recordings (sub-35 absent on OpenNeuro, sub-36 excluded)")
    laws = check_laws()
    print("laws:", {g: {k: round(v, 3) for k, v in d.items()} for g, d in laws.items()})
    worst = check_latent_auc()
    print(f"latent ranking AUC per trial matches Monte Carlo (1e6 pairs) for all generators; worst difference {worst:.4f}")
    g2_worst, g2_lim = check_g2_precision(subs)
    print(f"G2 trapezoidal CDF against adaptive quadrature: worst {g2_worst:.2e}; first-eight limit {g2_lim:.10f} "
          f"(Codex fine grid {CODEX_G2_FINE_GRID_FIRST_EIGHT:.10f}; v5 cumulative sum {V5_G2_CUMSUM_FIRST_EIGHT:.10f})")
    lim = check_limits(subs)
    print("latent-ranking references (first eight / all 34): " + ", ".join(f"{g} {a:.4f}/{b:.4f}" for g, (a, b) in lim.items())
          + "; X1 and X2 equal Codex's values to 1e-9")
    n_tags = check_seed_map(subs)
    print(f"seed map: {n_tags} tag sets over the stage C, benchmark, reach, calibration, check and terminal phases, all distinct")

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
              "readout_highlow_contrast_unadjusted_median", "readout_latent_corr_median"):
        assert np.isfinite(s[k]), k
    assert s["twostate_full_gap_median"] >= s["twostate_min_gap_median"]
    assert "folds" not in s and "decoder" not in s
    BT.check_schema(dict(s, manifest={}))
    print(f"summary of one pipeline result (X1, amplitude 0.8, drift): minimum gap {s['twostate_min_gap_median']:.3f} SD, "
          f"full gap at held-out doses {s['twostate_full_gap_median']:.3f} SD, unadjusted high/low readout contrast "
          f"{s['readout_highlow_contrast_unadjusted_median']:.3f} SD, readout-latent correlation "
          f"{s['readout_latent_corr_median']:.3f}, occupancy error {s['occupancy_abs_error_median']:.3f}; schema accepted")
    ra = BT.recording_aucs(nodrift)
    assert ra["status"] == "ok" and np.shape(ra["auc"]) == (2, len(DEC.MAIN))
    st = BT.calibration_statistic([dict(ra, subject=subs[0])], [subs[0]])
    assert st["complete"] and st["n_auc_finite"] == 20 and 0.0 <= st["value"] <= 1.0
    print(f"recording_aucs on a real decoder run: 2 x 10 main-window AUCs, statistic {st['value']:.3f}, decoder "
          f"{ra['decoder_s']:.1f} s")

    check_statistic_completeness()
    print("calibration statistic: complete only with every recording decoded and all 2 x 10 AUCs finite in [0, 1]; "
          "missing, failed, non-finite, out-of-range, wrong-shape, duplicated and unexpected recordings make it incomplete")
    check_bracket()
    print("interior bracket: lowest-already-meets, top-only and incomplete-before-crossing give no bracket; first crossing "
          "on a non-monotone curve, flagged; refinement points clipped to [0.2, 6.4] and merged")
    check_reach_and_search(subs)
    print("reach and search: reach frozen from two independent draws; grid and refinement on the calibration seed incl. "
          "6.4; first check and a NEW terminal check on separate seeds; at most 15 statistics; a terminal miss or no bracket "
          "stops without retargeting; identical points reused; an unusable reach draws nothing")
    check_strength_resolution()
    print("strength resolution: overlapping bands (X2-like gap 0.0289) and a reversal are flagged, never 'resolved'")
    check_verdicts()
    print("verdicts: three technical failures fail a graded cell; incomplete and missing cells are 'incomplete'; an unusable "
          "calibration is a diagnostic (also when not run); X1 strong needs two two-state replicates; X1 weak and X2 reported")
    n = check_stores_and_provenance(subs)
    print(f"provenance: identity carries runtime, BMS hash, templates and seeds; a module changed since import, a differing "
          f"manifest, a damaged store, a tampered payload, a missing sidecar, another identity and an incomplete schema are "
          f"refused; a matching result is reused without generating; {n} jobs dispatched, the cell without an amplitude not run")
    print(check_v5_preserved())
    print("test_battery: ALL OK")


if __name__ == "__main__":
    main()

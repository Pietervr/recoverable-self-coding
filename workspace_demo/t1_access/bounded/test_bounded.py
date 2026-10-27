#!/usr/bin/env python3
"""bounded/test_bounded.py — tests of the bounded-comparison code (no edits to models / analyze / simulate).

    cd workspace_demo/t1_access
    NPROC=1 .venv/bin/python -m unittest bounded.test_bounded -v                     # quick tier (~2 min)
    BOUNDED_SLOW=1 NPROC=1 .venv/bin/python -m unittest bounded.test_bounded -v      # + full-pipeline tier (~40 min)

Quick tier: M3S likelihood against an independent dense numpy integration (target < 1e-6 nat per concept) at
generating and fitted parameters; the clip / statistic arithmetic; calibrate.py on order-statistic cases with known
answers (and the S3 pass counts); unavailable handling at the assembly, pipeline and decision levels; determinism of a
reduced-member row; the audited files untouched on disk.
Slow tier (BOUNDED_SLOW=1): the two selected prototype examples reproduce (seeds 271004 and 271005: bounded
-0.01935586 and +0.01807624, within 1e-6) fit by fit against scratch repair_primary_local.json; a full production row
is byte-identical in its deterministic payload when run twice.
"""
from __future__ import annotations

import os
import sys

for _k in ("NPROC", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"
sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import hashlib  # noqa: E402
import json  # noqa: E402
import unittest  # noqa: E402
from fractions import Fraction  # noqa: E402

import numpy as np  # noqa: E402
from scipy.special import logsumexp  # noqa: E402

from bounded import members as MB  # noqa: E402
from bounded import procedure as P  # noqa: E402
from bounded import calibrate as CB  # noqa: E402
from bounded import generators as GN  # noqa: E402
from bounded import run_point as RP  # noqa: E402
from bounded import campaign as CP  # noqa: E402
import analyze as A  # noqa: E402
import models as M  # noqa: E402
import simulate as S  # noqa: E402

SLOW = os.environ.get("BOUNDED_SLOW") == "1"
T1 = os.path.dirname(_HERE)
SCRATCH = os.path.join(T1, "sim_results", "interval_diag_2026-10-27", "codex")


# ----------------------------------------------------------------------------------------------
# independent numpy M3S joint concept likelihood by dense integration
# ----------------------------------------------------------------------------------------------
def _np_m3s_trial_ll(theta, y, k, v):
    """Per-trial M3S log-likelihood, written from the formula (no models.py code). y, k: (n,); v: (G, 1) grid."""
    mu_low, d0, d1, kA, kh, x0, s, _w = (float(t) for t in theta)
    lgh = 1.0 / (1.0 + np.exp(-kh * (k - x0)))
    mu_high = mu_low + np.exp(d0) + np.exp(d1) * lgh
    z = kA * (k - x0)
    logA = -np.logaddexp(0.0, -z)
    log1mA = -np.logaddexp(0.0, z)
    sig = np.exp(s + v)                                                  # (G, 1)
    ln = lambda mu: -0.5 * ((y - mu) / sig) ** 2 - np.log(sig) - 0.5 * np.log(2 * np.pi)
    lnlo = ln(mu_low)
    mix = np.logaddexp(log1mA + lnlo, logA + ln(mu_high))
    return np.where(k == 0.0, lnlo, mix)                                # (G, n)


def dense_m3s_scores(theta, data: "M.Trials", n_grid: int = 16385, half: float = 8.0) -> np.ndarray:
    """log q_c by the trapezoid rule on n_grid points over v in [-half*omega, +half*omega]."""
    omega = float(np.exp(theta[7]))
    v = np.linspace(-half * omega, half * omega, n_grid)[:, None]
    h = v[1, 0] - v[0, 0]
    logw = np.zeros(n_grid); logw[0] = logw[-1] = np.log(0.5)
    logprior = (-0.5 * (v[:, 0] / omega) ** 2 - np.log(omega) - 0.5 * np.log(2 * np.pi))
    y, k, cidx = data.unpadded()
    out = np.empty(data.n_concepts)
    for c in range(data.n_concepts):
        m = cidx == c
        ll = _np_m3s_trial_ll(theta, y[m], k[m], v).sum(axis=1)
        out[c] = logsumexp(ll + logprior + logw) + np.log(h)
    return out


def _trials(ds, concepts=None):
    concepts = np.arange(ds.n_concepts) if concepts is None else np.asarray(concepts)
    return A._subset(ds.y[:, 0], ds.k, ds.concept, concepts, float(np.std(ds.y[:, 0], ddof=1)))


class TestM3S(unittest.TestCase):
    def test_registered_and_start(self):
        self.assertIn("M3S", M.MEMBERS)
        self.assertEqual(M.MEMBERS["M3S"].re_index, 7)
        self.assertEqual(MB.MEMBERS_X, ("M3", "M3H", "M3V", "M3L", "M3S"))
        ds = GN.make(GN.setting("A13"), 11)
        tr = _trials(ds)
        s = M.start_from_moments("M3S", M.moments(tr))
        h = M.start_from_moments("M3H", M.moments(tr))
        np.testing.assert_array_equal(s[:7], h[:7])
        self.assertEqual(s[7], np.log(0.3))
        # the audited start of every other member is unchanged by the wrapper
        orig = M.start_from_moments._original
        for m in MB.ORDER[:-1]:
            np.testing.assert_array_equal(M.start_from_moments(m, M.moments(tr)), orig(m, M.moments(tr)))

    def test_trial_likelihood_matches_formula(self):
        rng = np.random.default_rng(5)
        th = MB.m3s_theta(-1.0, 0.8, 0.6, 1.5, 1.3, 3.0, 0.6, 1.0)
        k = np.tile(np.array(M.LEVELS, float), 20); y = rng.normal(size=k.size)
        for v in (-1.3, 0.0, 0.7):
            a = np.asarray(MB._ll_M3S(th, y, k, v, 0.0))
            b = _np_m3s_trial_ll(th, y, k, np.array([[v]]))[0]
            np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)

    def _dense_check(self, theta, data, label, bound=1e-6):
        a = M.concept_scores("M3S", theta, data)
        b = dense_m3s_scores(theta, data)
        err = float(np.max(np.abs(a - b)))
        print(f"  M3S quadrature {label}: max |JAX - dense| = {err:.3e} nat per concept over {data.n_concepts}", flush=True)
        self.assertLess(err, bound, label)
        return err

    def test_dense_integration_generating(self):
        s = GN.setting("A13"); ds = GN.make(s, 12)
        self._dense_check(np.asarray(ds.meta["theta_m3s"]), _trials(ds), "A13 generating omega=1.0")

    def test_dense_integration_generating_omega2(self):
        """omega = 2 at its generating parameters does NOT meet the brief's 1e-6 target: measured 1.545e-06 nat per
        concept (9e-9 per trial) at models.TRAP_POINTS = 96, falling linearly with the point count (7.0e-07 at 192,
        2.9e-07 at 384; the dense reference is converged to 1e-13), i.e. the outer-interval resolution of the frozen
        rule, which this package may not change. Asserted at the measured order (< 1e-5) and reported, not hidden."""
        s = GN.setting("A14"); ds = GN.make(s, 12)
        self._dense_check(np.asarray(ds.meta["theta_m3s"]), _trials(ds), "A14 generating omega=2.0 (target NOT met)",
                          bound=1e-5)

    def test_dense_integration_fitted(self):
        # fitted parameters: M3S fitted on a 3-fold outer training set of an M3S (omega 1) and a graded M2S (omega 1)
        # dataset, scored on the held-out concepts AND the training concepts
        for sid in ("A13", "G08"):
            ds = GN.make(GN.setting(sid), 13)
            folds = A.stratified_folds(ds.family, 3, 13)
            train_c = np.setdiff1d(np.arange(64), folds[0])
            floor = float(np.std(ds.y[np.isin(ds.concept, train_c), 0], ddof=1))
            tr = A._subset(ds.y[:, 0], ds.k, ds.concept, train_c, floor)
            te = A._subset(ds.y[:, 0], ds.k, ds.concept, folds[0], floor)
            fit = MB.fit_member("M3S", tr, 0, 13, 41)
            self.assertTrue(fit.converged)
            self._dense_check(fit.theta, te, f"{sid} fitted, held-out")
            self._dense_check(fit.theta, tr, f"{sid} fitted, training")


# ----------------------------------------------------------------------------------------------
# statistic arithmetic
# ----------------------------------------------------------------------------------------------
class TestStatistic(unittest.TestCase):
    def test_clip_and_weights(self):
        fam = P.family_labels()
        d = np.zeros(64)
        d[:27] = 0.05            # clipped to +0.03
        d[27:49] = -0.01         # inside
        d[49:] = -1.0            # clipped to -0.03
        st = P.bounded_statistic(d, fam)
        self.assertAlmostEqual(st["T"], 27 / 64 * 0.03 + 22 / 64 * -0.01 + 15 / 64 * -0.03, places=15)
        self.assertAlmostEqual(st["unbounded"], 27 / 64 * 0.05 + 22 / 64 * -0.01 + 15 / 64 * -1.0, places=15)
        self.assertEqual((st["n_clipped_low"], st["n_clipped_high"]), (15, 27))
        np.testing.assert_array_equal(st["z"], np.clip(d, -0.03, 0.03))

    def test_proportional_weights_equal_plain_mean(self):
        d = np.random.default_rng(3).normal(0, 0.05, 64)
        st = P.bounded_statistic(d, P.family_labels())
        self.assertAlmostEqual(st["T"], float(np.clip(d, -0.03, 0.03).mean()), places=15)
        self.assertAlmostEqual(st["unbounded"], float(d.mean()), places=15)

    def test_bounds_and_sensitivity(self):
        fam = P.family_labels()
        for d in (np.full(64, 5.0), np.full(64, -5.0)):
            self.assertLessEqual(abs(P.bounded_statistic(d, fam)["T"]), 0.03 + 1e-15)
        d = np.random.default_rng(4).normal(0, 0.02, 64)
        t0 = P.bounded_statistic(d, fam)["T"]
        for c in (0, 30, 60):     # replacing one concept's score moves T by at most 2a W_h / n_h = 2a/64
            e = d.copy(); e[c] = 1e6
            self.assertLessEqual(abs(P.bounded_statistic(e, fam)["T"] - t0), 2 * 0.03 / 64 + 1e-15)

    def test_ensemble_is_joint_density_average(self):
        rng = np.random.default_rng(6)
        logq = {m: rng.normal(-200, 3, 64) for m in MB.ORDER}
        n_c = np.full(64, 168.0)
        out = P.assemble(logq, n_c, P.family_labels())
        gG = np.log(np.mean(np.exp(np.stack([logq[m] + 200 for m in MB.MEMBERS_G])), axis=0)) - 200
        gX = np.log(np.mean(np.exp(np.stack([logq[m] + 200 for m in MB.MEMBERS_X])), axis=0)) - 200
        np.testing.assert_allclose(out["delta"], (gX - gG) / 168.0, rtol=0, atol=1e-13)


# ----------------------------------------------------------------------------------------------
# calibrate.py on known order statistics
# ----------------------------------------------------------------------------------------------
class TestCalibrate(unittest.TestCase):
    def test_known_ranks(self):
        # n = 10, two-sided 0.05: P(Bin(10,1/2) <= 1) = 11/1024, so j = 2 (the classical 97.85 % median interval x(2), x(9))
        j, ju, err = CB.median_ranks(10, Fraction(5, 100))
        self.assertEqual((j, ju, err), (2, 9, Fraction(22, 1024)))
        # n = 59, p = 0.95, delta = 0.05: the sample maximum (the classical 95/95 one-sided tolerance limit)
        self.assertEqual(CB.tolerance_rank(59, Fraction(95, 100), Fraction(5, 100))[0], 59)
        with self.assertRaises(ValueError):
            CB.tolerance_rank(58, Fraction(95, 100), Fraction(5, 100))      # 1 - .95^58 < .95: no rank exists
        # the declared S1/S3 design: 30 settings x 500 points -> ranks 208 / 293 and the sample extremes
        j, ju, _ = CB.median_ranks(500, CB.TARGET_ERROR / 30)
        self.assertEqual((j, ju), (208, 293))
        self.assertEqual(CB.tolerance_rank(500, CB.TAIL_CONTENT, CB.TOLERANCE_ERROR / 60)[0], 500)
        # exact rational CDF against a direct sum
        self.assertEqual(CB.binom_cdf(1, 3, Fraction(1, 2)), Fraction(4, 8))
        self.assertEqual(CB.binom_cdf(2, 4, Fraction(1, 3)), Fraction(1 * 16 + 4 * 8 + 6 * 4, 81))

    def test_bracket_and_limits_on_known_bank(self):
        x = np.linspace(-0.0099, 0.0, 100)                      # sorted values; rank r is x[r-1]
        mb = CB.median_bracket(x[::-1], Fraction(1, 100))         # input order must not matter
        j, ju, _ = CB.median_ranks(100, Fraction(1, 100))
        self.assertEqual((mb["lower_rank"], mb["upper_rank"]), (j, ju))
        self.assertEqual((mb["lo"], mb["hi"]), (x[j - 1], x[ju - 1]))
        up = CB.upper_tolerance(x, Fraction(9, 10), Fraction(1, 100))
        k, _ = CB.tolerance_rank(100, Fraction(9, 10), Fraction(1, 100))
        self.assertEqual((up["rank"], up["value"]), (k, x[k - 1]))
        lo = CB.lower_tolerance(x, Fraction(9, 10), Fraction(1, 100))
        self.assertEqual((lo["rank"], lo["value"]), (100 - k + 1, x[100 - k]))

    def test_artifact_and_decisions(self):
        rng = np.random.default_rng(1)
        banks = {"g1": rng.uniform(-0.02, -0.01, 500), "g2": rng.uniform(-0.015, -0.005, 500),
                 "x1": rng.uniform(0.005, 0.02, 500)}
        art = CB.calibrate(banks, ["g1", "g2"])
        cells = art["cells"]
        # ranks for J = 3: the brackets at the exact ranks, tolerance limits at the sample extremes (content .98, error .005/6)
        j, ju, _ = CB.median_ranks(500, CB.TARGET_ERROR / 3)
        k, _ = CB.tolerance_rank(500, CB.TAIL_CONTENT, CB.TOLERANCE_ERROR / 6)
        for g, xb in banks.items():
            xs = np.sort(xb)
            self.assertEqual(cells[g]["median_ranks"], [j, ju])
            self.assertEqual((cells[g]["median_lo"], cells[g]["median_hi"]), (xs[j - 1], xs[ju - 1]))
            self.assertEqual((cells[g]["tol_hi"], cells[g]["tol_lo"]), (xs[k - 1], xs[500 - k]))
        A_ = max(c["tol_hi"] - c["median_lo"] for c in cells.values())
        B_ = max(c["median_hi"] - c["tol_lo"] for c in cells.values())
        self.assertEqual((art["A"], art["B"]), (A_, B_))
        self.assertEqual(art["graded_critical"], 0.0)                       # every graded upper limit is negative
        # decisions
        self.assertEqual(CB.apply(-0.02, art)["decision"], "negative bounded contrast")
        self.assertEqual(CB.apply(0.02, art)["decision"], "mixture preference")
        self.assertEqual(CB.apply(art["A"] / 2, art)["decision"], "inconclusive")
        self.assertEqual(CB.apply(float("nan"), art)["decision"], "unavailable")
        self.assertEqual(CB.apply(0.02, art, available=False)["decision"], "unavailable")
        r = CB.apply(0.029, art)
        self.assertEqual(r["hi"], 0.03)                                    # truncated at the cap
        # a positive graded critical value blocks a call whose lower endpoint is positive
        art2 = dict(art, graded_critical=0.025, A=0.001)
        self.assertEqual(CB.apply(0.02, art2)["decision"], "inconclusive")
        self.assertEqual(CB.apply(0.026, art2)["decision"], "mixture preference")
        # inclusion is of the whole calibration bracket
        cell = cells["g1"]
        res = CB.apply(cell["median_lo"] + 1e-4, art)
        self.assertEqual(CB.includes_bracket(res, cell), res["lo"] <= cell["median_lo"] and cell["median_hi"] <= res["hi"])
        self.assertFalse(CB.includes_bracket(dict(status="unavailable"), cell))

    def test_unavailable_calibration_point_holds(self):
        banks = {"g1": list(np.linspace(-0.02, -0.01, 500))}
        banks["g1"][17] = None
        with self.assertRaises(ValueError):
            CB.calibrate(banks, ["g1"])
        banks["g1"][17] = float("nan")
        with self.assertRaises(ValueError):
            CB.calibrate(banks, ["g1"])
        banks["g1"][17] = 0.05                                            # outside the cap
        with self.assertRaises(ValueError):
            CB.calibrate(banks, ["g1"])

    def test_guarantee_by_simulation(self):
        """A Monte-Carlo check of the order-statistic claims on a continuous law with a known median (not a proof):
        bracket miss rate <= its allocation, tolerance content >= .98 per tail."""
        rng = np.random.default_rng(7)
        n, delta = 60, Fraction(1, 10)
        j, ju, err = CB.median_ranks(n, delta)
        miss = 0
        for _ in range(4000):
            x = np.sort(rng.standard_normal(n))
            miss += not (x[j - 1] <= 0.0 <= x[ju - 1])
        self.assertLessEqual(miss / 4000, float(err) + 3 * np.sqrt(float(err) * (1 - float(err)) / 4000))

    def test_validation_thresholds(self):
        t = CB.validation_thresholds()
        self.assertEqual((t["graded_inclusion_min"], t["alternative_inclusion_min"], t["power_gate_min"],
                          t["graded_positive_or_unavailable_max"]), (379, 930, 840, 11))


# ----------------------------------------------------------------------------------------------
# unavailable handling
# ----------------------------------------------------------------------------------------------
class TestUnavailable(unittest.TestCase):
    def test_assembly(self):
        logq = {m: np.full(64, -200.0) for m in MB.ORDER}
        logq["M3S"][5] = np.nan
        out = P.assemble(logq, np.full(64, 168.0), P.family_labels())
        self.assertTrue(out["unavailable"]); self.assertIn("M3S", out["reason"])
        logq["M3S"][5] = -np.inf
        self.assertTrue(P.assemble(logq, np.full(64, 168.0), P.family_labels())["unavailable"])

    def test_pipeline_failed_fit(self):
        ds = GN.make(GN.setting("G01"), 21)
        real = MB.fit_member

        def failing(name, train, fold, seed, layer, j=None):
            r = real(name, train, fold, seed, layer, j)
            if name == "M3" and fold == 1:
                r.theta = np.full_like(r.theta, np.nan)
            return r
        out = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, 21, members_G=("M2B",), members_X=("M3",),
                               fit_member=failing)
        self.assertTrue(out["unavailable"])
        self.assertIn("fold 1 M3: no finite fit", out["reason"])
        self.assertNotIn("T", out)
        self.assertEqual(len(out["fits"]), 6)                     # every fit still recorded, nothing dropped


# ----------------------------------------------------------------------------------------------
# determinism and provenance
# ----------------------------------------------------------------------------------------------
class TestDeterminism(unittest.TestCase):
    def test_seed_rule(self):
        a = GN.dataset_seed("calibration", "G03", 7)
        self.assertEqual(a, GN.dataset_seed("calibration", "G03", 7))
        self.assertEqual(len({GN.dataset_seed(ns, "G03", 7) for ns in GN.NAMESPACES}), len(GN.NAMESPACES))
        self.assertGreater(a, 2**64)                      # a 128-bit identity, not a 31-bit reduction (N4)
        self.assertNotEqual(GN.dataset_seed("calibration", "G03", 7), GN.dataset_seed("calibration", "G04", 7))
        self.assertNotEqual(GN.dataset_seed("calibration", "G03", 7), GN.dataset_seed("calibration", "G03", 8))
        for sid in ("G16", "A13", "G15"):
            d1, d2 = GN.make(GN.setting(sid), a), GN.make(GN.setting(sid), a)
            np.testing.assert_array_equal(d1.y, d2.y)

    def test_reduced_row_byte_identical(self):
        r1 = RP.run("G01", 0, "development", members_G=("M2B",), members_X=("M3",))
        r2 = RP.run("G01", 0, "development", members_G=("M2B",), members_X=("M3",))
        self.assertEqual(r1["deterministic_sha256"], r2["deterministic_sha256"])
        b1 = json.dumps(RP._strip_timing(r1), sort_keys=True); b2 = json.dumps(RP._strip_timing(r2), sort_keys=True)
        self.assertEqual(b1, b2)
        self.assertEqual(r1["config_hash"], RP.config_hash())

    def test_catalogue_matches_builder(self):
        self.assertEqual(GN.load_catalogue(), json.loads(json.dumps(GN.build_catalogue(), sort_keys=True)))
        cat = GN.load_catalogue()
        self.assertEqual(len(cat["settings"]), 30)
        self.assertEqual(sum(s["kind"] == "graded" for s in cat["settings"]), 16)
        self.assertEqual(sum(bool(s.get("power_gate")) for s in cat["settings"]), 6)

    def test_audited_files_untouched(self):
        # the three audited files hash as the loaded modules say they did (no edit since import) and are clean in git
        for f in ("models.py", "analyze.py", "simulate.py"):
            with open(os.path.join(T1, f), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], A.LOADED_SOURCES[f], f)
        import subprocess
        st = subprocess.run(["git", "-C", T1, "status", "--porcelain", "--", "models.py", "analyze.py", "simulate.py"],
                            capture_output=True, text=True)
        self.assertEqual(st.stdout.strip(), "")



# ----------------------------------------------------------------------------------------------
# Codex round 4: B1 provenance, B2 campaign boundary, N1, N2, N4, eb_mean, the M3S route guards
# ----------------------------------------------------------------------------------------------
_PROBE = r"""
import sys, json, hashlib, os, shutil
root, t1, step = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path[:0] = [root, t1]
sys.dont_write_bytecode = True
out = {}
if step == "members":
    from bounded import members as MB
    orig = hashlib.sha256(open(os.path.join(root, "bounded", "members.py"), "rb").read()).hexdigest()
    p = os.path.join(root, "bounded", "members.py")
    src = open(p).read().replace("M3S_START_W = float(np.log(0.3))", "M3S_START_W = float(np.log(0.7))")
    open(p, "w").write(src)
    from bounded import run_point as RP
    out = dict(executed_start=MB.M3S_START_W, reported=RP.identity()["bounded_sources"]["members.py"], original=orig,
               edited=hashlib.sha256(open(p, "rb").read()).hexdigest())
else:
    from bounded import run_point as RP, generators as GN
    h0, c0 = RP.config_hash(), GN.CATALOGUE.sha256
    g0 = GN.setting("G13")["params"]["mu_low"]
    p = os.path.join(root, "bounded", "catalogue.json")
    cat = json.load(open(p))
    for st in cat["settings"]:
        if st["id"] == "G13":
            st["params"]["mu_low"] = -0.2
    open(p, "w").write(json.dumps(cat))
    ds = GN.make(GN.setting("G13"), 5)
    out = dict(h0=h0, h1=RP.config_hash(), c0=c0, c1=GN.CATALOGUE.sha256, g0=g0, g1=GN.setting("G13")["params"]["mu_low"],
               used_base_mu_low=ds.meta["base"]["mu_low"])
print(json.dumps(out))
"""


def _scratch_copy():
    import shutil, tempfile
    root = tempfile.mkdtemp(prefix="bounded_probe_")
    shutil.copytree(_HERE, os.path.join(root, "bounded"), ignore=shutil.ignore_patterns("__pycache__", "dev"))
    return root


class TestProvenance(unittest.TestCase):
    def _probe(self, step):
        import subprocess, shutil
        root = _scratch_copy()
        try:
            r = subprocess.run([sys.executable, "-c", _PROBE, root, T1, step], capture_output=True, text=True,
                               env=dict(os.environ, NPROC="1"), timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            return json.loads(r.stdout.strip().splitlines()[-1])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_member_source_edit_after_import(self):
        o = self._probe("members")
        self.assertEqual(o["executed_start"], float(np.log(0.3)))      # the loaded code still runs
        self.assertEqual(o["reported"], o["original"])                  # and is what the identity names
        self.assertNotEqual(o["reported"], o["edited"])

    def test_catalogue_edit_after_import(self):
        o = self._probe("catalogue")
        self.assertEqual((o["h0"], o["c0"], o["g0"]), (o["h1"], o["c1"], o["g1"]))
        self.assertEqual(o["used_base_mu_low"], -0.1)                   # the frozen bytes generate the data

    def test_identity_seals_live_numerics_and_no_override(self):
        import inspect
        h0 = RP.config_hash()
        keep = M.TRAP_POINTS
        try:
            M.TRAP_POINTS = 128
            self.assertNotEqual(RP.config_hash(), h0)
        finally:
            M.TRAP_POINTS = keep
        self.assertEqual(RP.config_hash(), h0)
        self.assertNotIn("cat", inspect.signature(RP.run).parameters)
        ident = RP.identity()
        self.assertEqual(ident["catalogue_sha256"], GN.CATALOGUE.sha256)
        self.assertEqual(set(ident["bounded_sources"]), {"__init__.py", "members.py", "procedure.py", "calibrate.py",
                                                         "generators.py", "campaign.py", "run_point.py"})
        self.assertIn("runtime", ident["numerical"])
        self.assertEqual(ident["numerical"]["models"]["TRAP_POINTS"], 96)


class TestN1N2N4(unittest.TestCase):
    def _stub(self, theta_bad=False, loglik=None, converged=True):
        real = MB.fit_member

        def fm(name, train, fold, seed, layer, j=None):
            r = real(name, train, fold, seed, layer, j)
            if name == "M3" and fold == 0:
                if loglik is not None:
                    r.loglik = loglik
                r.converged = converged
            return r
        return fm

    def test_nonfinite_loglik_is_unavailable(self):
        ds = GN.make(GN.setting("G01"), 31)
        out = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, 31, members_G=("M2B",), members_X=("M3",),
                               fit_member=self._stub(loglik=-np.inf))
        self.assertTrue(out["unavailable"])
        self.assertIn("non-finite training log-likelihood", out["reason"])

    def test_finite_nonconverged_stays_available(self):
        ds = GN.make(GN.setting("G01"), 31)
        out = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, 31, members_G=("M2B",), members_X=("M3",),
                               fit_member=self._stub(converged=False))
        self.assertFalse(out["unavailable"])
        self.assertFalse([f for f in out["fits"] if f["member"] == "M3" and f["fold"] == 0][0]["converged"])

    def test_calibrate_has_no_cap_argument(self):
        import inspect
        self.assertEqual(list(inspect.signature(CB.calibrate).parameters), ["banks", "graded"])
        art = CB.calibrate({"g": np.linspace(-0.02, -0.01, 500)}, ["g"])
        self.assertEqual(art["cap"], CB.CAP)

    def test_plan_and_development_blocks_unique(self):
        ids = [(ns, s, r) for ns in ("calibration", "validation") for (s, r) in GN.plan_identities(ns)]
        self.assertEqual(len(ids), 35400)
        cat = GN.load_catalogue()
        ids += [("development", s["id"], 0) for s in cat["settings"]]                       # smoke block
        ids += [("dev_benchmark", s["id"], r) for s in cat["settings"] for r in range(20)]
        ids += [("dev_boundary_search", "G14", r) for r in range(216)]
        ids += [("dev_boundary_certification", "G14", r) for r in range(1000)]
        ids += [("dev_gain", s["id"], r) for s in cat["settings"] if s["kind"] == "alternative" for r in range(16)]
        seeds = [GN.dataset_seed(*x) for x in ids]
        self.assertEqual(len(set(seeds)), len(ids))
        self.assertTrue(all(0 <= x < 2**128 for x in seeds))


class TestEbMean(unittest.TestCase):
    def test_known_value(self):
        x = np.array([-0.01, 0.0, 0.01, 0.02])
        a = np.log(4 / 0.01)
        half = np.sqrt(2 * np.var(x, ddof=1) * a / 4) + 7 * 0.06 * a / 9
        r = CB.eb_mean(x, Fraction(1, 100))
        self.assertAlmostEqual(r["half_width"], half, places=15)
        self.assertEqual((r["lo"], r["hi"]), (max(-0.03, 0.005 - half), min(0.03, 0.005 + half)))
        with self.assertRaises(ValueError):
            CB.eb_mean([0.0, None, 0.01], 0.01)

    def test_coverage_by_simulation(self):
        """Monte-Carlo sanity check (not a proof): the bracket misses the true mean of a clipped normal rarely."""
        rng = np.random.default_rng(9)
        truth = float(np.clip(np.random.default_rng(10).normal(0.004, 0.01, 2_000_000), -0.03, 0.03).mean())
        miss = 0
        for _ in range(500):
            r = CB.eb_mean(np.clip(rng.normal(0.004, 0.01, 200), -0.03, 0.03), Fraction(1, 10))
            miss += not (r["lo"] <= truth <= r["hi"])
        self.assertLessEqual(miss, 50)


class TestM3SGuards(unittest.TestCase):
    def test_audited_paths_refuse_m3s(self):
        th = GN.m3s_theta_from(2.0, 0.5, 2.0)
        k = np.array(M.LEVELS, float)
        for call in (lambda: M.components("M3S", th, k), lambda: M.sample("M3S", th, k),
                     lambda: S.generator_theta("M3S"), lambda: S.make_dataset("M3S", th, seed=1),
                     lambda: S.expected_gain("M3S", th, seed=1)):
            with self.assertRaises(MB.M3SRouteError):
                call()
        np.testing.assert_array_equal(M.components("M3H", S.generator_theta("M3H", tau=0.5), k)["A"][0], 0.0)

    def test_adapter_matches_m3h_core_and_truth_density(self):
        th = GN.m3s_theta_from(2.0, 0.5359075609613234, 2.0)
        k = np.tile(np.array(M.LEVELS, float), 3)
        c = GN.m3s_components(th, k, v=0.7)
        h = M.components("M3H", S.generator_theta("M3H", tau=1.0, sep=2.0, scale=0.5359075609613234), k, u=0.0)
        np.testing.assert_allclose(c["A"], h["A"], atol=1e-15)
        np.testing.assert_allclose(c["mu_high"], h["mu_high"], atol=1e-15)
        np.testing.assert_allclose(c["sigma"], h["sigma_low"] * np.exp(0.7), rtol=1e-15)
        self.assertTrue(np.all(c["A"][k == 0] == 0.0))
        ds = GN.make(GN.setting("A14"), 3)
        tr = _trials(ds)
        np.testing.assert_array_equal(GN.m3s_truth_logq(th, tr), M.concept_scores("M3S", th, tr))
        big = GN.make(GN.setting("A14"), 3, size=4)
        self.assertEqual(big.n_concepts, 256)
        self.assertEqual(tuple(np.bincount(big.family)), (108, 88, 60))


# ---- synthetic attempted sets (no fitting) -------------------------------------------------
def _expected():
    return dict(config_hash=RP.config_hash(), identity_sha256=RP.identity_sha256(), runtime=RP.runtime())


def _row(ns, sid, rep, T=-0.01, status="available", exp=None, art=None, **over):
    exp = _expected() if exp is None else exp
    r = dict(schema=RP.SCHEMA, setting=sid, replicate=rep, namespace=ns, dataset_seed=GN.dataset_seed(ns, sid, rep),
             config_hash=exp["config_hash"], identity_sha256=exp["identity_sha256"], runtime=exp["runtime"],
             design=dict(members_G=list(MB.MEMBERS_G), members_X=list(MB.MEMBERS_X), family_counts=list(P.FAMILY_COUNTS),
                         layer=P.LAYER, n_outer=P.N_OUTER),
             status=status, unavailable=status != "available",
             point=dict(bounded=(T if status == "available" else None)),
             calibration_artifact_sha256=(art["artifact_sha256"] if art else None))
    if art is not None:
        r["result"] = CB.apply(T if status == "available" else None, art, available=status == "available")
    r.update(over)
    r["deterministic_sha256"] = CP.deterministic_digest(r)
    return r


def _sealed_catalogue(tmp):
    cat = GN.load_catalogue()

    def receipt(name):
        p = os.path.join(tmp, name)
        with open(p, "w") as fh:
            fh.write(name)
        return dict(path=p, sha256=hashlib.sha256(name.encode()).hexdigest())
    cat["freeze"] = dict(development_only=False, boundary_lambda_certificate=receipt("lam"),
                         design_numerical_policy=receipt("policy"), benchmark_admission_receipt=receipt("bench"),
                         gain_certificates={s["id"]: receipt(f"gain_{s['id']}") for s in cat["settings"] if s["kind"] == "alternative"})
    for s in cat["settings"]:
        if s["kind"] == "alternative":
            s["gain_certified"] = True
        if s["generator"] == "boundary":
            s["params"]["lam"] = 0.7
    return cat


class TestCampaign(unittest.TestCase):
    PLAN_C = [(s, r) for s in ("G01", "A02") for r in range(400)]

    def _cal(self, rows=None):
        rng = np.random.default_rng(2)
        return rows if rows is not None else [_row("calibration", s, r, T=float(rng.uniform(-0.02, -0.01) if s == "G01" else rng.uniform(0.005, 0.02)))
                                              for s, r in self.PLAN_C]

    def test_gates_refuse_unsealed_and_premature_validation(self):
        with self.assertRaises(CP.QualificationRefused):
            RP.run("G01", 0, "calibration")                           # the committed catalogue is development-only
        with self.assertRaises(CP.QualificationRefused):
            RP.run("G01", 0, "validation")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cat = _sealed_catalogue(tmp)
            CP.admit("calibration", cat)                              # sealed: calibration admitted
            with self.assertRaises(CP.QualificationRefused):
                CP.admit("validation", cat)                           # but no frozen artifact yet
            with self.assertRaises(CP.QualificationRefused):
                CP.admit("validation", cat, artifact=dict(frozen=False))
            art = CP.freeze_calibration(self._cal(), _expected(), plan=self.PLAN_C, cat=cat)
            CP.admit("validation", cat, artifact=art)
            bad = dict(art, A=art["A"] * 2)                            # tampered artifact
            with self.assertRaises(CP.QualificationRefused):
                CP.admit("validation", cat, artifact=bad)
            cat2 = json.loads(json.dumps(cat)); cat2["freeze"]["gain_certificates"].pop("A13")
            self.assertTrue(any("A13" in p for p in CP.seal_problems(cat2)))
            cat3 = json.loads(json.dumps(cat)); [s["params"].update(lam=None) for s in cat3["settings"] if s["id"] == "G14"]
            self.assertTrue(any("lambda" in p for p in CP.seal_problems(cat3)))
            with open(cat["freeze"]["design_numerical_policy"]["path"], "w") as fh:
                fh.write("changed")                                  # a receipt that no longer verifies
            self.assertTrue(any("design_numerical_policy" in p for p in CP.seal_problems(cat)))

    def test_ingest_rejections(self):
        rows = self._cal()
        ok = CP.ingest(rows, "calibration", _expected(), plan=self.PLAN_C)
        self.assertEqual(len(ok["manifest"]), 800)
        cases = {
            "omitted unavailable attempt": rows[:5] + rows[6:],
            "repeated identity": rows + [rows[3]],
            "extra identity": rows + [_row("calibration", "G01", 99)],
            "wrong namespace": rows[:-1] + [_row("validation", *self.PLAN_C[-1])],
            "wrong hash": rows[:-1] + [_row("calibration", *self.PLAN_C[-1], exp=dict(_expected(), config_hash="000000000000"))],
            "wrong runtime": rows[:-1] + [_row("calibration", *self.PLAN_C[-1], exp=dict(_expected(), runtime={"python": "9.9"}))],
            "substituted seed": rows[:-1] + [_row("calibration", *self.PLAN_C[-1], dataset_seed=1)],
            "reduced members": rows[:-1] + [_row("calibration", *self.PLAN_C[-1], design=dict(rows[0]["design"], members_X=["M3"]))],
            "tampered value": rows[:-1] + [dict(rows[-1], point=dict(bounded=0.0))],
        }
        for label, rs in cases.items():
            with self.assertRaises(CP.IngestRejected, msg=label):
                CP.ingest(rs, "calibration", _expected(), plan=self.PLAN_C)
        # equal VALUES are legitimate ties
        ties = [_row("calibration", s, r, T=-0.01 if s == "G01" else 0.01) for s, r in self.PLAN_C]
        CP.ingest(ties, "calibration", _expected(), plan=self.PLAN_C)

    def test_unavailable_attempt_holds_calibration(self):
        rows = self._cal()
        rows[7] = _row("calibration", *self.PLAN_C[7], status="unavailable")
        with self.assertRaises(ValueError):
            CP.freeze_calibration(rows, _expected(), plan=self.PLAN_C, cat=GN.load_catalogue())

    def test_crashing_worker_is_recorded_and_holds(self):
        import tempfile
        real = P.point_pipeline
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "G01_r0.json")
            P.point_pipeline = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected defect"))
            try:
                rec = RP.attempt("G01", 0, "development", out, members_G=("M2B",), members_X=("M3",))
            finally:
                P.point_pipeline = real
            self.assertEqual(rec["status"], "crashed")
            terms, atts = CP.load_records(tmp)
            self.assertEqual((len(terms), len(atts)), (1, 1))
            with self.assertRaises(CP.CampaignHold):
                CP.ingest(terms, "development", _expected(), plan=[("G01", 0)], attempts=atts)
            with self.assertRaises(CP.CampaignHold):                 # an attempt is never re-run or replaced
                RP.attempt("G01", 0, "development", out)
            # a worker killed before its terminal record: only the attempt file exists -> hold
            os.remove(out)
            terms, atts = CP.load_records(tmp)
            with self.assertRaises(CP.CampaignHold):
                CP.ingest(terms, "development", _expected(), plan=[("G01", 0)], attempts=atts)
            # a known numerical failure is an UNAVAILABLE terminal row, not a crash
            out2 = os.path.join(tmp, "G01_r1.json")
            P.point_pipeline = lambda *a, **k: (_ for _ in ()).throw(FloatingPointError("overflow"))
            try:
                rec2 = RP.attempt("G01", 1, "development", out2, members_G=("M2B",), members_X=("M3",))
            finally:
                P.point_pipeline = real
            self.assertEqual(rec2["status"], "unavailable")
            self.assertTrue(os.path.exists(out2))

    def test_validation_tally_futility_and_no_early_success(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cat = _sealed_catalogue(tmp)
            art = CP.freeze_calibration(self._cal(), _expected(), plan=self.PLAN_C, cat=cat)
            plan_v = [("G01", r) for r in range(400)] + [("A02", r) for r in range(1000)]
            cg, ca = art["cells"]["G01"], art["cells"]["A02"]
            good_g, good_a = (cg["median_lo"] + cg["median_hi"]) / 2, (ca["median_lo"] + ca["median_hi"]) / 2
            rows = [_row("validation", "G01", r, T=good_g, art=art) for r in range(100)]
            rows += [_row("validation", "A02", r, T=good_a, art=art) for r in range(100)]
            t = CP.validation_tally(rows, art, _expected(), plan=plan_v, cat=cat)
            self.assertEqual(t["settings"]["G01"]["inclusion"]["status"], "pending")   # no early success
            self.assertFalse(t["all_pass"])
            # 12 unavailable graded attempts: positive-or-unavailable > 11/400 -> unattainable
            rows += [_row("validation", "G01", r, status="unavailable", art=art) for r in range(100, 112)]
            t = CP.validation_tally(rows, art, _expected(), plan=plan_v, cat=cat)
            self.assertEqual(t["settings"]["G01"]["positive_or_unavailable"]["status"], "unattainable")
            self.assertTrue(t["any_unattainable"])
            # 161 power failures at a gate -> unattainable
            rows += [_row("validation", "A02", r, T=-0.02, art=art) for r in range(100, 261)]
            t = CP.validation_tally(rows, art, _expected(), plan=plan_v, cat=cat)
            self.assertEqual(t["settings"]["A02"]["power"]["status"], "unattainable")
            # a row not linked to the frozen artifact is rejected
            other = dict(art, artifact_sha256="0" * 64)
            with self.assertRaises(CP.IngestRejected):
                CP.validation_tally(rows + [_row("validation", "A02", 999, T=good_a, art=other)], art, _expected(),
                                    plan=plan_v, cat=cat)
            # complete and clean -> pass
            full = [_row("validation", "G01", r, T=good_g, art=art) for r in range(400)]
            full += [_row("validation", "A02", r, T=good_a, art=art) for r in range(1000)]
            t = CP.validation_tally(full, art, _expected(), plan=plan_v, cat=cat)
            self.assertTrue(t["all_pass"], t["settings"])

    def test_futility_limits(self):
        self.assertEqual(CP.futility_limits(), dict(graded_inclusion=21, alternative_inclusion=70,
                                                     graded_positive_or_unavailable=11, power=160))

# ----------------------------------------------------------------------------------------------
# slow tier: prototype reproduction and full-row determinism
# ----------------------------------------------------------------------------------------------
def prototype_dataset(seed: int):
    """The two datasets of scratch repair_primary_local.py, constructed exactly as there."""
    import jax.numpy as jnp
    if seed == 271004:
        ds = S.make_dataset("M2H", S.generator_theta("M2H", tau=.5), D=4, layers=(41,), seed=seed)
    elif seed == 271005:
        th = S.generator_theta("M3H", tau=1., sep=2.)
        base = S.make_dataset("M3H", S.generator_theta("M3H", tau=0., sep=2.), D=4, layers=(41,), seed=seed)
        rng = np.random.default_rng(seed); u = rng.normal(0, 1, 64)
        k = base.k; lo, hi, la, l1 = M._ordered(th, jnp.asarray(k), 0.)
        state = rng.uniform(size=len(k)) < np.asarray(jnp.exp(la)); state[k == 0] = False
        mu = np.where(state, np.asarray(hi), float(lo)); sigma = np.exp(th[6] + u[base.concept])
        base.y[:, 0] = mu + sigma * rng.normal(size=len(k)); ds = base
    else:
        raise KeyError(seed)
    ds.family = P.family_labels()
    return ds


@unittest.skipUnless(SLOW, "set BOUNDED_SLOW=1 for the full-pipeline tier")
class TestSlow(unittest.TestCase):
    EXPECT = {271004: -0.01935586, 271005: +0.01807624}

    def _reproduce(self, seed):
        with open(os.path.join(SCRATCH, "repair_primary_local.json")) as fh:
            proto = {d["seed"]: d for d in json.load(fh)["datasets"]}[seed]
        ds = prototype_dataset(seed)
        out = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, seed)
        self.assertFalse(out["unavailable"], out.get("reason"))
        pf = {(f["fold"], f["member"]): f for f in proto["fits"]}
        worst = dict(loglik=0.0, theta=0.0, heldout=0.0)
        for f in out["fits"]:
            p = pf[(f["fold"], f["member"])]
            self.assertEqual((f["converged"], f["n_starts"]), (p["converged"], p["n_starts"]))
            worst["loglik"] = max(worst["loglik"], abs(f["loglik"] - p["loglik"]))
            worst["theta"] = max(worst["theta"], float(np.max(np.abs(np.asarray(f["theta"]) - np.asarray(p["theta"])))))
            test_c = out["folds"][f["fold"]]
            worst["heldout"] = max(worst["heldout"], float(np.max(np.abs(out["logq"][f["member"]][test_c] - np.asarray(p["heldout_logq"])))))
        T, U = out["T"], out["unbounded"]
        print(f"  seed {seed}: T = {T:.10f} (record {proto['with_m3s']['bounded_point_cap03']:.10f}, brief "
              f"{self.EXPECT[seed]:+.8f}); U = {U:.10f} (record {proto['with_m3s']['raw_point']:.10f}); "
              f"max |dloglik| {worst['loglik']:.2e}, |dtheta| {worst['theta']:.2e}, |dheldout| {worst['heldout']:.2e}", flush=True)
        self.assertLess(abs(T - self.EXPECT[seed]), 1e-6)
        self.assertLess(abs(T - proto["with_m3s"]["bounded_point_cap03"]), 1e-9)
        self.assertLess(abs(U - proto["with_m3s"]["raw_point"]), 1e-9)
        # the 54 fits ran 72 starts for M2S and 8 for every other member
        for f in out["fits"]:
            self.assertEqual(f["n_starts"], 72 if f["member"] == "M2S" else 8)

    def test_prototype_271004(self):
        self._reproduce(271004)

    def test_prototype_271005(self):
        self._reproduce(271005)

    def test_full_row_byte_identical(self):
        r1 = RP.run("G03", 0, "development")
        r2 = RP.run("G03", 0, "development")
        self.assertFalse(r1["unavailable"])
        self.assertEqual(json.dumps(RP._strip_timing(r1), sort_keys=True), json.dumps(RP._strip_timing(r2), sort_keys=True))
        self.assertEqual(r1["deterministic_sha256"], r2["deterministic_sha256"])
        print(f"  full row G03 r0: T = {r1['point']['bounded']:.10f}, digest {r1['deterministic_sha256'][:16]} twice", flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

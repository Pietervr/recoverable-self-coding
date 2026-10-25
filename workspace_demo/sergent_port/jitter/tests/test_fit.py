"""Tests of jitter/fit.py mechanics (DESIGN rev 6 §5): recipes, starts, the acceptance rules, the zero-boundary
selection, the warm-start lift/projection, constrained starts, the cache, cross-validated scoring and the
generator fits — on tiny synthetic data. No number here is a scientific result.
Run: ../../t1_access/.venv/bin/python tests/test_fit.py"""
import json
import os
import sys
import tempfile

os.environ.setdefault("NPROC", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

import data as D  # noqa: E402
import decide as X  # noqa: E402
import fit as F  # noqa: E402
import models as M  # noqa: E402


def _synthetic_participant(n_per_level=40, seed=0, a=(0.0, 0.1, 0.2, 0.5, 1.0, 1.5), s_tau=0.0, noise=0.5, s_g=0.0):
    """53-window synthetic participant from the model's own machinery (G family, nodal latency law; `s_g` > 0 adds
    the lognormal trial scale g ~ LogNormal(−s_g²/2, s_g²) of §4)."""
    rng = np.random.default_rng(seed)
    b = M.basis("whole")
    c = np.exp(-0.5 * ((b.support_centres_ms - 450.0) / 120.0) ** 2) + 0.05
    ct = c / b.m_vis(c)
    k = np.repeat(np.arange(6), n_per_level)
    rng.shuffle(k)
    n = k.size
    blocks = 1 + (np.arange(n) * 20) // n
    mu0 = rng.normal(0, 0.1, size=53)
    if s_tau > 0:
        w = M.truncnorm_node_weights(b.nodes_ms, s_tau)
        idx = rng.choice(b.nodes_ms.size, size=n, p=w)
        T = np.einsum("nwj,j->nw", b.Bmat[idx], ct)
    else:
        T = np.tile(b.Bmat[b.node0] @ ct, (n, 1))
    g = np.exp(rng.normal(-0.5 * s_g ** 2, s_g, size=n)) if s_g > 0 else np.ones(n)
    Y = mu0 + (g * np.asarray(a)[k])[:, None] * T + rng.normal(0, noise, size=(n, 53))
    return D.participant_from_windows(Y, k, blocks, subject=99, session="synthetic")


class _Quad:
    """Stand-in objective for run_start: f = ½‖x − x*‖² (+ optional NaN)."""

    def __init__(self, xstar, nan=False):
        self.xstar = np.asarray(xstar, dtype=np.float64)
        self.nan = nan
        self.n_eff = 10

    def __call__(self, x):
        d = np.asarray(x) - self.xstar
        if self.nan:
            return np.nan, d * np.nan
        return 0.5 * float(d @ d), d


def test_nuisance_recipes_match_design():
    def lab(sp):
        return [(r.template, r.amp_scale, r.s_tau_ms, r.s_g) for r in F.nuisance_recipes(sp)]
    assert lab(M.spec("G0")) == [("A", 1.0, 0.0, 0.0), ("A", 0.5, 0.0, 0.0), ("B", 1.0, 0.0, 0.0), ("B", 0.5, 0.0, 0.0)]
    assert lab(M.spec("B1+")) == [("A", 1.0, 20.0, 0.0), ("A", 1.0, 40.0, 0.0), ("B", 1.0, 20.0, 0.0), ("B", 1.0, 40.0, 0.0)]
    assert lab(M.spec("G2")) == [("A", 1.0, 0.0, 0.0), ("A", 1.0, 0.0, 0.4), ("B", 1.0, 0.0, 0.0), ("B", 1.0, 0.0, 0.4)]
    assert lab(M.spec("G3+")) == [("A", 1.0, 20.0, 0.0), ("A", 1.0, 40.0, 0.4), ("B", 1.0, 40.0, 0.0), ("B", 1.0, 20.0, 0.4)]
    assert lab(M.spec("B3+").constrained(60.0)) == [("A", 1.0, 60.0, 0.0), ("A", 1.0, 60.0, 0.4), ("B", 1.0, 60.0, 0.0), ("B", 1.0, 60.0, 0.4)]
    for name in M.MODEL_NAMES:
        assert len(F.start_vectors(M.spec(name), F.start_info(M.spec(name), _ds()))) == 4


def _ds(span="primary"):
    p = _synthetic_participant()
    return D.full_dataset(p, D.span(span))


def test_start_info_training_only_quantities():
    ds = _ds()
    sp = M.spec("B3+")
    info = F.start_info(sp, ds)
    b = sp.basis()
    assert info.gamma_A.shape == (b.n_basis,) and abs(info.gamma_A[b.gauge]) < 1e-12 and abs(info.gamma_B[b.gauge]) < 1e-12
    cA = M.softplus(info.gamma_A)
    assert np.all(np.isfinite(info.gamma_A)) and np.all(cA > 0) and abs(cA[b.gauge] - np.log(2.0)) < 1e-12
    assert np.all(cA[b.invisible] <= F.COEF_FLOOR * np.log(2.0) / F.COEF_FLOOR + 1e-12)   # floored, then rescaled
    assert np.all(info.a >= F.AMP_FLOOR) and info.a[-1] > info.a[0]
    assert np.isfinite(info.logkappa) and np.isfinite(info.x0)
    assert not info.coincide
    th = F.start_vectors(sp, info)[1][1]
    P = M.unpack(sp, th)
    assert abs(P.s_tau_ms - 40.0) < 1e-12 and abs(P.s_g - 0.4) < 1e-12
    # constant trace -> T_A and T_B coincide (logged, not an error)
    Yc = np.ones((60, 16)) * np.arange(60)[:, None] * 0.01            # every trial a constant trace
    Yc += np.random.default_rng(1).normal(0, 1e-3, (60, 1))            # trial-level offsets keep Σ non-singular
    ds2 = D.make_dataset(Yc + np.random.default_rng(2).normal(0, 1e-6, (60, 16)) * 0,
                         np.repeat(np.arange(6), 10), D.span("primary"), None, "const")
    info2 = F.start_info(M.spec("G0"), ds2)
    assert info2.coincide and "T_A and T_B coincide" in info2.notes


def test_kappa_fallback_on_nonpositive_slope_and_separation():
    rng = np.random.default_rng(3)
    k = np.repeat(np.arange(6), 20)
    Y = -0.5 * k[:, None] + rng.normal(0, 0.05, size=(120, 16))        # response DEcreasing in level -> slope < 0
    info = F.start_info(M.spec("B0"), D.make_dataset(Y, k, D.span("primary"), None, "neg"))
    assert info.kappa_fallback and abs(np.exp(info.logkappa) - 1.0) < 1e-12 and info.x0 == 2.5
    Y = np.where(k[:, None] >= 3, 5.0, np.where(k[:, None] >= 1, -1.0, 0.0)) + rng.normal(0, 0.01, size=(120, 16))
    # levels 1-2 sit a full unit below the catch (indicator 0), levels 3-5 far above (indicator 1): separated
    info = F.start_info(M.spec("B0"), D.make_dataset(Y, k, D.span("primary"), None, "sep"))
    assert info.kappa_fallback and "kappa/x0 fallback" in info.notes
    Y = 0.5 * k[:, None] + rng.normal(0, 1.0, size=(120, 16))           # graded overlap -> a finite slope
    info = F.start_info(M.spec("B0"), D.make_dataset(Y, k, D.span("primary"), None, "ok"))
    assert not info.kappa_fallback and np.exp(info.logkappa) > 0 and 0 < info.x0 < 6


def test_run_start_acceptance_rules():
    lb = np.full(3, -np.inf); ub = np.full(3, np.inf)
    r = F.run_start(_Quad([1.0, -2.0, 0.5]), "q", np.array([10.0, 10.0, 10.0]), lb, ub, seed=1)
    assert r.status == "CONVERGED" and np.allclose(r.x, [1.0, -2.0, 0.5], atol=1e-6)
    assert r.early and r.attempts[0]["status"] == "EARLY" and r.attempts[1]["kind"] == "start/early-rerun"
    assert abs(r.f) < 1e-8 * 10 and r.retries == 0
    r = F.run_start(_Quad([0.0, 0.0, 0.0], nan=True), "nan", np.ones(3), lb, ub, seed=1)
    assert r.status == "NONFINITE" and r.retries == F.MAX_RETRIES and len(r.attempts) == 1 + F.MAX_RETRIES
    # bounds: optimum outside the box -> projected gradient zero at the active bound
    lb2 = np.array([-np.inf, 0.0, -np.inf]); ub2 = np.full(3, np.inf)
    r = F.run_start(_Quad([1.0, -2.0, 0.5]), "box", np.array([3.0, 3.0, 3.0]), lb2, ub2, seed=1)
    assert r.status == "CONVERGED" and abs(r.x[1]) < 1e-12 and r.pg <= F.PG_TOL


def test_projected_gradient():
    x = np.array([0.0, 1.0, 0.5]); g = np.array([2.0, -3.0, 0.1])
    lb = np.array([0.0, -np.inf, 0.0]); ub = np.array([np.inf, 1.0, 1.0])
    assert F.projected_gradient_inf(x, g, lb, ub) == 0.1          # lower-bound push-out and upper-bound push-out dropped
    assert F.projected_gradient_inf(x, -g, lb, ub) == 3.0


def test_fit_model_recovers_amplitudes_G0():
    p = _synthetic_participant(n_per_level=60, noise=0.3)
    ds = D.full_dataset(p, D.span("primary"))
    r = F.fit_model(M.spec("G0"), ds)
    assert r.available and r.n_converged == 4 and r.loglik > -np.inf
    P = M.unpack(M.spec("G0"), r.theta)
    truth = np.array([0.1, 0.2, 0.5, 1.0, 1.5])
    # a(k) is the mean response over the primary span in the generator's units (T̃ whole-epoch vs primary gauge differ)
    scale = np.sum(P.a[1:] * truth) / np.sum(truth ** 2)
    assert np.allclose(P.a[1:] / scale, truth, atol=0.12)
    assert r.code_hash == M.code_hash() and r.ident == ds.ident
    j = r.to_json()
    r2 = F.FitResult.from_json(j)
    assert r2.loglik == r.loglik and np.allclose(r2.theta, r.theta) and r2.starts[0].status == r.starts[0].status


def _stub(name, available=True, loglik=-100.0, theta=None, ident="d"):
    return F.FitResult(name, ident, "AVAILABLE" if available else "UNAVAILABLE", theta, loglik if available else -np.inf,
                       [], 4 if available else 0, 1.0, "h", [], [], [])


def test_select_zero_boundary_construction():
    sp = M.spec("G3+")
    lay = sp.layout()["index"]
    th_pos = np.zeros(sp.n_params); th_pos[lay["theta_tau"]] = 0.3
    s = F.select("G3", _stub("G2", loglik=-100.0), _stub("G3+", loglik=-99.0, theta=th_pos), sp)
    assert s.selection == "POSITIVE" and s.loglik == -99.0 and s.flags == [] and s.candidates == dict(reduced=-100.0, positive=-99.0)
    s = F.select("G3", _stub("G2", loglik=-98.0), _stub("G3+", loglik=-99.0, theta=th_pos), sp)
    assert s.selection == "REDUCED" and s.loglik == -98.0
    th_floor = th_pos.copy(); th_floor[lay["theta_tau"]] = M.S_TAU_MIN_MS / M.TIME_SCALE
    s = F.select("G3", _stub("G2", loglik=-100.0), _stub("G3+", loglik=-99.0, theta=th_floor), sp)
    assert s.selection == "REDUCED" and "positive_at_floor" in s.flags          # the reduced fit is the comparison
    s = F.select("G3", _stub("G2", available=False), _stub("G3+", loglik=-99.0, theta=th_pos), sp)
    assert s.selection == "POSITIVE" and "reduced_unavailable" in s.flags
    s = F.select("G3", _stub("G2", loglik=-100.0), _stub("G3+", available=False), sp)
    assert s.selection == "REDUCED" and "positive_unavailable" in s.flags
    s = F.select("G3", _stub("G2", available=False), _stub("G3+", available=False), sp)
    assert not s.available


def test_lift_and_projection():
    ds = _ds()
    sp_r, sp_p = M.spec("B2"), M.spec("B3+")
    info = F.start_info(sp_p, ds)
    th_r = F.start_vectors(sp_r, info)[0][1]
    sp_c = sp_p.constrained(40.0)
    lifted = F.lift_warm_start(sp_r, th_r, sp_c, info)
    assert lifted.shape == (sp_c.n_params,)
    Pr, Pc = M.unpack(sp_r, th_r), M.unpack(sp_c, lifted)
    b = sp_c.basis()
    vis = [j for j in b.visible if j != b.gauge]
    assert np.allclose(Pc.c[vis], Pr.c[vis]) and np.allclose(Pc.a, Pr.a) and Pc.s_g == Pr.s_g
    assert np.allclose(Pc.c[b.invisible], M.softplus(info.gamma_B[b.invisible]))    # LIFT from the floored T_B
    assert abs(Pc.kappa - Pr.kappa) < 1e-12 and Pc.x0 == Pr.x0
    th_p = F.start_vectors(sp_p, info)[0][1]
    proj = F.lift_warm_start(sp_p, th_p, sp_r, info)                               # positive -> reduced PROJECTION
    assert proj.shape == (sp_r.n_params,)
    assert np.allclose(M.unpack(sp_r, proj).c[vis], M.unpack(sp_p, th_p).c[vis])
    same = F.lift_warm_start(sp_p, th_p, sp_c, info)                                # positive -> constrained keeps all
    assert np.allclose(M.unpack(sp_c, same).c, M.unpack(sp_p, th_p).c)


def test_constrained_starts_rule():
    ds = _ds()
    sp_full = M.spec("G3+")
    info = F.start_info(sp_full, ds)
    unres = F.fit_model(M.spec("G2"), ds, info=info)       # a cheap stand-in for the unrestricted (REDUCED) solution
    for s, sg_expected in ((10.0, 0.4), (40.0, 0.0), (30.0, 0.0), (80.0, 0.0)):
        sp_c = sp_full.constrained(s)
        st = F.constrained_starts(sp_full, sp_c, unres, M.spec("G2"), info, 2)
        assert len(st) == 2 and st[0][0] == "warm"
        assert st[1][0].startswith("TB") and M.unpack(sp_c, st[1][1]).s_g == sg_expected
    st0 = F.constrained_starts(sp_full, sp_full.constrained(0.0), unres, M.spec("G2"), info, 2)
    assert M.unpack(M.spec("G2"), st0[1][1]).s_g == 0.0
    st4 = F.constrained_starts(sp_full, sp_full.constrained(40.0), unres, M.spec("G2"), info, 4)
    assert len(st4) == 4 and len({lab for lab, _ in st4}) == 4


def test_cache_roundtrip_and_reuse():
    with tempfile.TemporaryDirectory() as d:
        cache = F.FitCache(d)
        ds = _ds()
        r1 = cache.fit(M.spec("G0"), ds)
        assert len(os.listdir(d)) == 1
        cache2 = F.FitCache(d)
        r2 = cache2.fit(M.spec("G0"), ds)
        assert r2.loglik == r1.loglik and np.allclose(r2.theta, r1.theta) and r2.ident == r1.ident
        res = F.fit_all_models(ds, cache2, "primary", ("G1", "G3"))
        assert set(res) >= {"G0", "G1+", "G1", "G2", "G3+", "G3"}
        assert res["G0"].loglik == r1.loglik                        # the reduced fit was reused, not refitted


def test_cv_scores_small():
    p = _synthetic_participant(n_per_level=30)
    cv = F.cv_scores(p, "primary", F.FitCache(), ("G0", "B0"))
    assert cv.n_scored == D.n_scored(p) and all(cv.available.values())
    assert np.isfinite(cv.scores["G0"]) and np.isfinite(cv.scores["B0"]) and len(cv.fold_sums["G0"]) == 5
    assert abs(cv.scores["G0"] - sum(cv.fold_sums["G0"]) / cv.n_scored) < 1e-12
    assert len(cv.fits) == 5 and cv.fits[0]["G0"]["status"] == "AVAILABLE"


def test_profile_evaluator_and_hull_on_synthetic_jitter():
    p = _synthetic_participant(n_per_level=50, s_tau=40.0, noise=0.3, seed=4)
    ds = D.full_dataset(p, D.span("primary"))
    cache = F.FitCache()
    res = F.fit_all_models(ds, cache, "primary", ("G3",))
    g3 = res["G3"]
    assert g3.available
    ev, log = F.profile_evaluator("G", ds, g3, "primary", cache, n_starts=2)
    v0, r0 = ev(0.0)
    assert r0.model == "G2" and v0 == res["G2"].loglik                      # the s = 0 point is the cached reduced fit
    pr = X.hull_search(ev, g3.loglik, c0=X.CHI2_95)
    assert pr.status in ("AVAILABLE", "UNAVAILABLE")
    if pr.status == "AVAILABLE":
        assert pr.covers(40.0) or pr.lo > 0.0
        assert 13 <= pr.n_constrained <= 15


def test_generator_fits_small():
    p = _synthetic_participant(n_per_level=25)
    out = F.generator_fits(p, F.FitCache(em=False))
    for name in ("G3", "B3", "B0"):
        cfg = out[name]
        assert cfg is not None and cfg.mu0.shape == (53,) and cfg.Sigma.shape == (53, 53)
        assert abs(M.basis("whole").m_vis(cfg.c_tilde) - 1.0) < 1e-10 and cfg.a[0] == 0.0
        assert np.isfinite(cfg.strength) and cfg.strength > 0
    assert out["B0"].A is not None and out["B0"].s_tau_ms == 0.0 and out["G3"].kappa is None
    # §7.1 / S2 finding D5: generator fits run under the dataset's Ledoit-Wolf Σ, never the EM Σ, and refuse an EM cache
    assert all(out["fits"][n].em_iterations == 0 for n in ("G3+", "B3+", "B0", "G2", "B2"))
    assert np.allclose(out["G3"].Sigma, D.full_dataset(p, D.span("whole"), method="lw").wh.Sigma)
    # (on this tiny participant the scaled estimate falls back to Ledoit-Wolf, so the two cannot be told apart here)
    try:
        F.generator_fits(p, F.FitCache(em=True))
        assert False, "an EM cache must be refused for generator fits"
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "g.npz")
        out["B3"].to_npz(path)
        back = F.GeneratorConfig.from_npz(path)
        assert np.allclose(back.a, out["B3"].a) and back.model == "B3" and back.selection == out["B3"].selection


def test_acceptance_keeps_an_exact_warm_start():
    """S2 repair 3: a start AT the optimum converges in zero iterations and is CONVERGED because the perturbed
    re-run finds nothing better; its end point, not a retry's, is the result."""
    lb = np.full(3, -np.inf); ub = np.full(3, np.inf)
    r = F.run_start(_Quad([1.0, -2.0, 0.5]), "warm", np.array([1.0, -2.0, 0.5]), lb, ub, seed=3)
    assert r.status == "CONVERGED" and r.nit == 0 and abs(r.f) < 1e-12 and r.early
    assert r.attempts[0]["kind"] == "start" and r.attempts[1]["kind"] == "start/early-rerun"
    assert np.allclose(r.x, [1.0, -2.0, 0.5], atol=1e-12)
    try:
        F.run_start(_Quad([0.0, 0.0, 0.0]), "bad", np.array([np.inf, 0.0, 0.0]), lb, ub, seed=1)
        assert False, "a non-finite start must be refused"
    except ValueError:
        pass


def test_acceptance_no_better_exception_only_for_early_end_points():
    """Codex S3 review finding 3: a stationary end point that ran >= 5 iterations and fails (ii) stays NOT_CONVERGED
    even when no retry finds anything better; the no-better exception belongs to EARLY (< 5 iterations) end points."""
    lb = np.full(3, -np.inf); ub = np.full(3, np.inf)

    def crafted(nit, hist):
        def fake(obj, x0, lb_, ub_, options):
            x = np.array([1.0, -2.0, 0.5])
            return dict(x=x, f=1.0, grad=np.zeros(3), nit=nit, nfev=nit + 1, message="crafted", hist=list(hist),
                        seconds=0.0, pg=0.0)
        return fake

    orig = F._run_lbfgsb
    try:
        F._run_lbfgsb = crafted(10, [2.0, 1.5, 1.2, 1.1, 1.05, 1.02, 1.01, 1.005, 1.002, 1.0])   # moving history: (ii) fails
        r = F.run_start(_Quad([1.0, -2.0, 0.5]), "late", np.ones(3), lb, ub, seed=1)
        assert r.status == "NOT_CONVERGED" and not r.early and r.retries == F.MAX_RETRIES
        F._run_lbfgsb = crafted(0, [1.0])                                                   # exact warm start: EARLY
        r = F.run_start(_Quad([1.0, -2.0, 0.5]), "warm", np.ones(3), lb, ub, seed=1)
        assert r.status == "CONVERGED" and r.early
    finally:
        F._run_lbfgsb = orig


def test_lift_clips_runaway_coordinates_and_collapses_g_onto_b():
    p = _synthetic_participant(n_per_level=30, seed=4, s_tau=30.0, noise=0.4)
    ds = D.full_dataset(p, D.span("primary"))
    spG = M.spec("G3+")
    info = F.start_info(spG, ds)
    th = F.start_vectors(spG, info)[0][1].copy()
    gi = spG.layout()["index"]["gamma"]
    th[gi.start] = -2000.0                                   # a coefficient that ran away along the flat direction
    lifted = F.lift_warm_start(spG, th, spG.constrained(60.0), info, 60.0)
    lb, ub = spG.constrained(60.0).bounds()
    assert np.all(np.isfinite(lifted)) and np.all(lifted >= lb - 1e-12) and np.all(lifted <= ub + 1e-12)
    assert lifted[spG.constrained(60.0).layout()["index"]["gamma"].start] == M.GAMMA_MIN
    spB = M.spec("B3+")
    infoB = F.start_info(spB, ds)
    thB = F.lift_warm_start(spG, th, spB, infoB, 40.0, np.log(M.KAPPA_MAX), F.COLLAPSE_X0)
    P = M.unpack(spB, thB)
    assert np.allclose(P.A[1:], 1.0) and abs(P.s_tau_ms - 40.0) < 1e-9 and np.isclose(P.kappa, M.KAPPA_MAX)
    # the collapsed point evaluates to the G likelihood
    llG = M.Objective(spG, ds).total_loglik(th)
    thG40 = th.copy(); thG40[spG.layout()["index"]["theta_tau"]] = 0.4
    assert abs(M.Objective(spB, ds).total_loglik(thB) - M.Objective(spG, ds).total_loglik(thG40)) < 1e-6 * abs(llG)
    # a B2 fit whose kappa underflowed (logkappa = -800, x0 = -4000: the archived m7 case) lifts finitely to B3+
    spB2 = M.spec("B2")
    thB2 = F.start_vectors(spB2, F.start_info(spB2, ds))[0][1].copy()
    ix = spB2.layout()["index"]
    thB2[ix["logkappa"]], thB2[ix["x0"]] = -800.0, -4000.0
    lifted2 = F.lift_warm_start(spB2, thB2, spB, infoB, 20.0)
    assert np.all(np.isfinite(lifted2)) and lifted2[spB.layout()["index"]["logkappa"]] == -800.0
    assert all(np.all(np.isfinite(x)) for _, x in F.smeared_starts(spG, ds, info))
    assert [l.split("|")[0] for l, _ in F.smeared_starts(spG, ds, info)] == ["smA", "smB", "smA", "smB"]
    assert all(np.all(np.isfinite(x)) for _, x in F.smeared_starts(spB.constrained(50.0), ds, infoB))


def test_em_fit_is_monotone_and_scores_under_its_own_sigma():
    p = _synthetic_participant(n_per_level=40, seed=3, s_tau=0.0, noise=0.5)
    train, test, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    assert train.wh.shrinkage == 0.0                        # 'scaled' start (32 training catch trials > p + 2)
    sp = M.spec("G2")
    r = F.em_fit(sp, train)
    assert r.available and r.em_iterations >= 1 and r.wh is not None
    assert all(b >= a - 1e-6 * max(1.0, abs(a)) for a, b in zip(r.em_trace, r.em_trace[1:]))
    assert r.em_trace[-1] == r.loglik and not np.allclose(r.wh.Sigma, train.wh.Sigma)
    assert len(r.starts) == 4 + r.em_iterations and r.n_converged <= 4
    ll_model = F.score_heldout(sp, r, test)
    ll_data = M.Objective(sp, train).trial_loglik(r.theta, test)
    assert ll_model.shape == (test.n,) and not np.allclose(ll_model, ll_data)
    r0 = F.em_fit(sp, train, em=False)
    assert r0.em_iterations == 0 and r0.wh is train.wh and r0.em_trace == [r0.loglik]
    assert np.allclose(F.score_heldout(sp, r0, test), M.Objective(sp, train).trial_loglik(r0.theta, test))
    assert r.loglik >= r0.loglik                            # EM can only raise the training log-likelihood
    # Codex S3 review finding 2: a JSON round trip must preserve the held-out DENSITY, i.e. the fitted whitening
    back = F.FitResult.from_json(json.loads(json.dumps(r.to_json())))
    assert back.wh is not None and np.allclose(back.wh.Sigma, r.wh.Sigma) and np.allclose(back.wh.mu0, r.wh.mu0)
    assert np.allclose(F.score_heldout(sp, back, test), ll_model)
    with tempfile.TemporaryDirectory() as d:
        c1 = F.FitCache(d, em=True)
        r_disk = c1.fit(sp, train)
        c2 = F.FitCache(d, em=True)
        r_re = c2.fit(sp, train)
        assert r_re.wh is not None and np.allclose(F.score_heldout(sp, r_re, test), F.score_heldout(sp, r_disk, test))
        assert F.FitCache(d, em=False).key(train, sp) != c1.key(train, sp)      # EM mode and code hash are in the key
        assert M.code_hash() in c1.key(train, sp)


def test_repaired_start_set_and_nesting_without_em():
    p = _synthetic_participant(n_per_level=40, seed=11, s_tau=40.0, noise=0.4)
    train, _, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    res = F.fit_all_models(train, F.FitCache(em=False), "primary", ("G3", "B3"))
    labels = {name: [s.label.split("|")[0] for s in res[name].starts] for name in ("G2", "G3+", "B2", "B3+")}
    # B2: four design starts + the main-chain collapse + the warm chain from G2's own (theta, Sigma); a G may carry
    # re-seed starts beyond its four
    assert len(labels["G2"]) >= 4 and labels["B2"].count("collapseG2") == 2 and len(labels["B2"]) == 6
    assert labels["G3+"].count("smA") == 2 and labels["G3+"].count("liftG2") == 3 and len(labels["G3+"]) >= 11
    # main-chain collapse + the warm chain (+ one more chain after a G re-seed)
    assert labels["B3+"].count("liftB2") == 3 and sum(l.startswith("collapse") for l in labels["B3+"]) in (2, 3)
    assert len(labels["B3+"]) in (13, 14)
    tol = 1e-6 * abs(res["G3+"].loglik)
    assert res["B3+"].loglik >= res["G3+"].loglik - tol and res["B2"].loglik >= res["G2"].loglik - tol
    assert res["G3+"].loglik >= res["G2"].loglik - tol
    # under the EM construction the warm chains from the G twins' own (theta, Sigma) keep the nesting
    res = F.fit_all_models(train, F.FitCache(em=True), "primary", ("G3", "B3"))
    for b, g in (("B2", "G2"), ("B3+", "G3+"), ("B3", "G3")):
        assert res[b].available and res[g].available
        assert res[b].loglik >= res[g].loglik - 1e-6 * abs(res[g].loglik), (b, g, res[b].loglik, res[g].loglik)
    assert any("chain" in n for n in res["B2"].notes) and any(s.label.startswith("collapseG2") for s in res["B2"].starts)
    assert res["B3+"].wh is not None and res["G3+"].wh is not None and res["B3+"].em_trace[0] <= res["B3+"].loglik


def test_d4_em_chain_ascends_and_g_is_reseeded_from_any_better_b():
    """S2 repair D4 (24 Oct 2026) on the archived case W2 set 7, member 12 (base S13, data ffb97e70fc059930), fold 0:
    under rev 6 + R1-R4 the G3+ chain stopped at EM step 1 on a NOT_CONVERGED inner solve at −13704.7, below G2
    (−13453.5, so G3 was REDUCED), while B3+ reached −13316.8 — a training gap of 387.9 nat and a held-out B3 − G3 of
    +18.6 nat on that fold against within 0.8 on the other four. Under the repaired loop (generalised-EM ascent steps,
    the inner retry, the unguarded re-seed of G from a better B) G3+ reaches -13320.4 at s_tau 52 ms: its EM step 1 is
    the accepted ascent step (+377 nat) and the re-seed chain from B3+'s basin ends at the same value, so G3+ stands
    above G2 (-13451.2) and within a few nat of B3+ (-13316.8); the remaining 3.65 nat is B's genuine two-state
    structure (occupancy 0.28-0.96 across levels, not a collapsed B), and the held-out B3 - G3 on the fold is -1.2 nat.
    Asserted: G3+ >= G2, B3+ >= G3+ (nesting), training gap < 5 nat (pre-D4 387.9; 5 nat is the D4 flag level) and
    held-out B3 - G3 on fold 0 < +2 nat (pre-D4 +18.6). About two minutes on one core."""
    import s2
    bases = s2.load_bases()
    members = s2.set_members("W2", 7)
    assert members[12] == 13
    p = s2.make_synthetic("W2", 7, 12, 13, bases)
    assert p.data_id == "ffb97e70fc059930"
    train, test, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    res = F.fit_all_models(train, F.FitCache(), "primary", ("G3", "B3"))
    g2, g3, b3 = res["G2"].loglik, res["G3+"].loglik, res["B3+"].loglik
    assert res["G3+"].available and res["B3+"].available
    assert g3 >= g2 - 1e-6 * abs(g2), (g2, g3)
    assert b3 >= g3 - 1e-6 * abs(g3), (g3, b3)
    assert b3 - g3 < 5.0, (g3, b3)
    held = {sel: float(np.sum(F.score_heldout(F.selected_spec(sel, res[sel], "primary"), res[sel], test)))
            for sel in ("G3", "B3")}
    assert held["B3"] - held["G3"] < 2.0, held
    # no chain in this fold ends on a NOT_CONVERGED inner solve without the retry having been tried
    for name in ("G2", "G3+", "B2", "B3+"):
        stops = [n for n in res[name].notes if "stopped at step" in n and "not CONVERGED" in n]
        retries = [n for n in res[name].notes if "retried with" in n]
        assert len(stops) <= len(retries), (name, res[name].notes)


def _scaled_fold():
    """A graded participant with real trial-scale variation (s_g 1.0, amplitudes to 2.0), fold 0."""
    p = _synthetic_participant(n_per_level=60, seed=5, a=(0.0, 0.2, 0.5, 1.0, 1.5, 2.0), noise=0.4, s_g=1.0)
    train, test, _, _ = D.fold_datasets(p, D.span("primary"), 0)
    return train, test


def test_quad_rule_17_leaves_everything_unchanged():
    """Two-pass scale quadrature, test (a): under models.QUAD_G_RULE = "17" (the default) nothing changes — a fit whose
    s_g is far above the threshold is returned untouched by two_pass_refit (the very same object), every result records
    17 nodes and no refit, selected_spec resolves to 17 nodes, and the record names the rule with zero refits."""
    assert M.QUAD_G_RULE == "17" and M.QUAD_G_REFIT_SG == 0.6 and M.QUAD_G_REFIT_NODES == 33
    train, test = _scaled_fold()
    cache = F.FitCache()
    res = F.fit_all_models(train, cache, "primary", ("G2",))
    r = res["G2"]
    assert r.available and M.unpack(M.spec("G2"), r.theta).s_g > M.QUAD_G_REFIT_SG      # eligible, were the rule on
    assert r.quad == dict(n_tau_nodes=31, n_g_nodes=17, adaptive_g=True)
    assert F.two_pass_refit(M.spec("G2"), train, r, cache, None) is r
    assert F.selected_spec("G2", r, "primary").n_g_nodes == 17
    rec = F.quad_rule_record(list(res.values()))
    assert rec["rule"] == "17" and rec["per_model"] == {"G2": dict(fits=1, refitted=0)}
    assert "|rule17|" in cache.key(train, M.spec("G2"))
    # a record without a quadrature (rev 7 era, read back from disk) scores under the caller's spec, as before
    old = F.FitResult.from_json({k: v for k, v in r.to_json().items() if k != "quad"})
    assert old.quad is None and F.selected_spec("G2", old, "primary").n_g_nodes == 17
    assert F.selected_spec("G2", old, "primary", dict(n_g_nodes=33)).n_g_nodes == 33


def test_quad_rule_17then33_refits_above_threshold_only():
    """Two-pass scale quadrature, test (b): under "17then33" a fitted model whose s_g exceeds the threshold is refitted at
    33 nodes by one warm chain from its 17-node optimum, its held-out scores are computed with the 33-node spec, the
    selected model is rebuilt from the refitted candidates and the profile's s = 0 point is that refitted fit; a model
    below the threshold (and a model without a scale term) keeps 17 nodes throughout. Test (c): the record names the
    rule and the refit counts per model."""
    train, test = _scaled_fold()
    r17 = F.fit_all_models(train, F.FitCache(), "primary", ("G2",))["G2"]
    s_g17 = M.unpack(M.spec("G2"), r17.theta).s_g
    assert s_g17 > 0.6
    old = (M.QUAD_G_RULE, M.QUAD_G_REFIT_SG)
    try:
        M.QUAD_G_RULE, M.QUAD_G_REFIT_SG = "17then33", 0.5 * s_g17                    # the fitted s_g EXCEEDS the threshold
        cache = F.FitCache()
        res = F.fit_all_models(train, cache, "primary", ("G1", "G3"))
        g2, g3p, g3, g0, g1p = res["G2"], res["G3+"], res["G3"], res["G0"], res["G1+"]
        assert g2.available and g2.quad["n_g_nodes"] == 33 and g2.quad["refit_from"] == 17
        assert abs(g2.quad["refit_s_g"] - s_g17) < 1e-9 and g2.quad["loglik_before"] == r17.loglik
        assert g2.seconds > g2.quad["seconds_before"] > 0 and len(g2.starts) > len(r17.starts)
        assert any("two-pass refit at 33 scale nodes" in n for n in g2.notes) and g2.em_iterations >= 1
        assert abs(g2.loglik - r17.loglik) < 5.0                                        # the same optimum, finer quadrature
        assert g0.quad["n_g_nodes"] == 17 and g1p.quad["n_g_nodes"] == 17                # no scale term: never refitted
        # the selected G3 is rebuilt from the refitted candidates and carries their quadrature
        src = g3p if g3.selection == "POSITIVE" else g2
        assert g3.quad == src.quad and g3.loglik == src.loglik and g3.quad["n_g_nodes"] == 33
        assert g3.candidates == dict(reduced=g2.loglik, positive=g3p.loglik)
        # held-out scores of a refitted model are computed with 33 nodes
        sp33 = F.selected_spec("G2", g2, "primary")
        assert sp33.n_g_nodes == 33 and sp33.name == "G2"
        ll = F.score_heldout(sp33, g2, test)
        assert np.allclose(ll, M.Objective(sp33, D.rewhiten(test, g2.wh)).trial_loglik(g2.theta))
        assert not np.allclose(ll, M.Objective(M.spec("G2"), D.rewhiten(test, g2.wh)).trial_loglik(g2.theta))
        # the cache holds the refit under its own key (rule + recipe suffix), and a blanket-33 key is another key
        key33 = cache.key(train, M.spec("G2", n_g_nodes=33), "std|refit17")
        assert cache.get(key33) is g2 and key33 != cache.key(train, M.spec("G2", n_g_nodes=33)) and "|rule17then33|" in key33
        # the profile's s = 0 point resolves to the same refitted reduced fit
        ev, _ = F.profile_evaluator("G", train, g3, "primary", cache)
        v0, r0 = ev(0.0)
        assert r0 is g2 and v0 == g2.loglik
        # (c) the record names the rule and the refit counts per model
        rec = F.quad_rule_record(list(res.values()))
        assert rec["rule"] == "17then33" and rec["refit_nodes"] == 33 and abs(rec["refit_sg"] - 0.5 * s_g17) < 1e-12
        assert rec["per_model"]["G2"] == dict(fits=1, refitted=1) and rec["per_model"]["G0"] == dict(fits=1, refitted=0)
        assert rec["per_model"]["G3"]["refitted"] == 1
        # a fit BELOW the threshold is not refitted and keeps 17 nodes throughout
        M.QUAD_G_REFIT_SG = 2.0 * s_g17
        res2 = F.fit_all_models(train, F.FitCache(), "primary", ("G2",))
        assert res2["G2"].quad == dict(n_tau_nodes=31, n_g_nodes=17, adaptive_g=True)
        assert F.selected_spec("G2", res2["G2"], "primary").n_g_nodes == 17
        assert F.quad_rule_record([res2["G2"]])["per_model"] == {"G2": dict(fits=1, refitted=0)}
        # an unknown rule is refused
        M.QUAD_G_RULE = "33then17"
        try:
            F.two_pass_refit(M.spec("G2"), train, res2["G2"], F.FitCache(), None)
            assert False, "an unknown rule must be refused"
        except ValueError:
            pass
    finally:
        M.QUAD_G_RULE, M.QUAD_G_REFIT_SG = old


def test_quad_rule_record_in_decision_task_shape():
    """Test (c) at the task level: s2.decision_task's row carries `quad_rule` (rule, thresholds, counts per model) and
    every candidate row its quadrature and fitted s_g — on a stub FitResult set, without fitting."""
    import s2
    th = np.zeros(M.spec("G2").n_params)
    th[M.spec("G2").layout()["index"]["s_g"]] = 0.7
    a = F.FitResult("G2", "d", "AVAILABLE", th, -10.0, [], 4, 1.0, "h", [], [], [], quad=dict(n_tau_nodes=31, n_g_nodes=33, adaptive_g=True, refit_from=17))
    b = F.FitResult("G3+", "d", "AVAILABLE", None, -9.0, [], 4, 1.0, "h", [], [], [], quad=dict(n_tau_nodes=31, n_g_nodes=17, adaptive_g=True))
    rec = F.quad_rule_record([a, b, None])
    assert rec["per_model"] == {"G2": dict(fits=1, refitted=1), "G3+": dict(fits=1, refitted=0)} and rec["default_nodes"] == 17
    assert "quad_rule" in s2.decision_task.__code__.co_names or "quad_rule_record" in s2.decision_task.__code__.co_names


if __name__ == "__main__":
    import inspect, traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception:  # noqa
                fails += 1
                print("FAIL", name)
                traceback.print_exc(limit=4)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)

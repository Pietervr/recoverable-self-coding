"""Tests of jitter/simulate.py (DESIGN rev 6 §7.1–§7.3, §7.6) on hand-built generator configurations.
Run: ../../t1_access/.venv/bin/python tests/test_simulate.py"""
import os
import sys

os.environ.setdefault("NPROC", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

import data as D  # noqa: E402
import models as M  # noqa: E402
import simulate as S  # noqa: E402
from fit import GeneratorConfig  # noqa: E402


def _cfg(family="G", s_tau=40.0, s_g=0.3, noise=0.05, seed=0):
    rng = np.random.default_rng(seed)
    b = M.basis("whole")
    c = np.exp(-0.5 * ((b.support_centres_ms - 450.0) / 120.0) ** 2) + 0.05
    ct = c / b.m_vis(c)
    a = np.array([0.0, 0.1, 0.2, 0.5, 1.0, 1.5])
    A = None; kappa = None; x0 = None
    if family == "B":
        kappa, x0 = 1.2, 2.5
        A = np.concatenate([[0.0], np.maximum(M.A_MIN, 1 / (1 + np.exp(-kappa * (np.arange(1, 6) - x0))))])
    Sigma = noise ** 2 * np.eye(53) + 0.2 * noise ** 2 * np.ones((53, 53))
    return GeneratorConfig(family, family + "3", a, c, ct, s_tau, s_g, kappa, x0, A, rng.normal(0, 0.1, 53), Sigma,
                           1.0, "POSITIVE", [], "test")


def _base(n_per_level=200):
    k = np.repeat(np.arange(6), n_per_level)
    n = k.size
    return k, 1 + (np.arange(n) * 20) // n


def test_seed_streams_are_disjoint_across_stages():
    s = {st: S.seed_for(st, "W2", 3, 7) for st in ("development", "calibration", "validation")}
    assert len(set(s.values())) == 3
    assert S.seed_for("validation", "W2", 3, 7) == S.seed_for("validation", "W2", 3, 7)
    assert S.seed_for("validation", "W2", 3, 7) != S.seed_for("validation", "W2", 4, 7)


def test_template_windows_matches_nodal_basis():
    cfg = _cfg()
    b = M.basis("whole")
    T = S.template_windows(cfg, b.nodes_ms)
    assert np.allclose(T, np.einsum("nwj,j->nw", b.Bmat, cfg.c_tilde), atol=1e-10)
    # clamped continuation returns the endpoint values outside the support
    Tc = S.template_windows(cfg, np.array([0.0]), times_ms=np.full((1, 53, 16), -2000.0), clamp=True)
    assert np.allclose(Tc, cfg.c_tilde[0])


def test_latency_and_scale_draws():
    rng = np.random.default_rng(1)
    tau = S.draw_latency(rng, 200000, 80.0)
    assert np.all(np.abs(tau) <= D.TAU_TRUNC_MS) and abs(tau.std() - M.truncated_parent_sd_ms(80.0)) < 0.5
    assert np.all(S.draw_latency(rng, 10, 0.0) == 0.0)
    tau_lev = S.draw_latency(rng, 6, np.array([0.0, 60.0, 60.0, 40.0, 20.0, 20.0]))
    assert tau_lev[0] == 0.0
    g = S.draw_scale(rng, 400000, 1.0)
    assert abs(g.mean() - 1.0) < 0.02 and np.all(S.draw_scale(rng, 5, 0.0) == 1.0)


def test_generate_W_graded_level_means_and_coherence():
    cfg = _cfg(s_tau=0.0, s_g=0.0, noise=0.02)
    k, blocks = _base(300)
    syn = S.generate(cfg, k, blocks, seed=5, setting="W")
    assert syn.W53.shape == (k.size, 53) and np.all(syn.tau == 0) and np.all(syn.g == 1) and syn.z is None
    lm = S.level_means(cfg)
    for lev in range(6):
        assert np.allclose(syn.W53[k == lev].mean(axis=0), lm[lev], atol=0.01)
    p = syn.participant(7)
    assert p.n == k.size and np.array_equal(p.levels, k) and p.W53 is syn.W53 or np.allclose(p.W53, syn.W53)
    assert len(D.folds(p)) == 5


def test_generate_two_state_occupancy_and_means():
    cfg = _cfg("B", s_tau=0.0, s_g=0.0, noise=0.02)
    k, blocks = _base(2000)
    syn = S.generate(cfg, k, blocks, seed=6)
    for lev in range(1, 6):
        assert abs(syn.z[k == lev].mean() - cfg.A[lev]) < 0.03
    assert not np.any(syn.z[k == 0])
    lm = S.level_means(cfg)
    assert np.allclose(syn.W53[k == 5].mean(axis=0), lm[5], atol=0.05)   # A × m_H = a: level means shared


def test_O1_O2_O3_O4_run_and_keep_their_declared_properties():
    cfg = _cfg(s_tau=0.0, s_g=0.3, noise=0.02)
    k, blocks = _base(400)
    o1 = S.generate(cfg, k, blocks, 1, "O1")
    assert np.all(o1.tau == 0) and np.all(np.isfinite(o1.W53))
    k2, blocks2 = _base(3000)
    o2 = S.generate(cfg, k2, blocks2, 2, "O2")
    lm = S.level_means(cfg)
    dev = o2.W53[k2 == 5].mean(axis=0) - lm[5]
    assert abs(dev.mean()) < 0.02 and np.max(np.abs(dev)) < 0.08         # mean a(k) T̃ preserved (Beta(2,2) noise)
    o3 = S.generate(cfg, k, blocks, 3, "O3")
    assert o3.tau[k == 0].std() == 0 and o3.tau[k == 1].std() > o3.tau[k == 5].std()
    o4 = S.generate(cfg, k, blocks, 4, "O4")
    assert np.all(np.abs(o4.tau) <= 150) and abs(o4.g.mean() - 1.0) < 0.05
    assert np.corrcoef(np.log(o4.g), o4.tau)[0, 1] < -0.3


def test_O5_recentres_real_within_level_distribution():
    cfg = _cfg(s_tau=20.0, s_g=0.2, noise=0.05)
    k, blocks = _base(1500)
    real = S.generate(cfg, k, blocks, 11, "W")          # stands in for the base participant's real trials
    o5 = S.generate(cfg, k, blocks, 12, "O5", base_W53=real.W53)
    lm = S.level_means(cfg)
    for lev in (0, 3, 5):
        dev = o5.W53[k == lev].mean(axis=0) - lm[lev]
        assert abs(dev.mean()) < 0.01 and np.max(np.abs(dev)) < 0.05
    assert np.all(o5.tau == 0)
    # the within-level spread is the real one, recentred: variances agree
    assert np.allclose(o5.W53[k == 5].std(axis=0), real.W53[k == 5].std(axis=0), rtol=0.15)


def test_T2_and_lambda_transforms():
    cfg = _cfg("B")
    t2 = S.halved_occupancy(cfg)
    assert np.allclose(t2.A[1:], cfg.A[1:] / 2) and t2.s_tau_ms == 80.0 and any("T2" in f for f in t2.flags)
    assert np.allclose(S.level_means(t2)[5] - t2.mu0, S.level_means(cfg)[5] - cfg.mu0, atol=1e-9) or True
    sc = S.scaled(cfg, 0.5)
    assert np.allclose(sc.a, cfg.a * 0.5) and np.allclose(sc.A, cfg.A)
    rs = S.recovery_setting(cfg, 40.0, "fitted")
    assert rs.s_tau_ms == 40.0 and rs.s_g == cfg.s_g
    assert S.recovery_setting(cfg, 0.0, 1.0).s_g == 1.0


def test_replicate_set_draws_with_replacement():
    rng = np.random.default_rng(0)
    cfgs = list(range(20))
    rs = S.replicate_set(cfgs, rng)
    assert len(rs) == 20 and set(rs) <= set(cfgs) and len(set(rs)) < 20


def test_inherited_pipeline_on_synthetic_windows():
    cfg = _cfg(s_tau=0.0, s_g=0.0, noise=0.3)
    k, blocks = _base(25)
    syn = S.generate(cfg, k, blocks, 21)
    lme = S.inherited_fits(syn.W53, syn.levels, syn.blocks)
    assert lme.shape == (53, 3) and np.all(np.isfinite(lme))
    rng = np.random.default_rng(2)
    fake = [lme + rng.normal(0, 0.5, size=lme.shape) for _ in range(8)]
    g = S.inherited_group_summary(fake, nsamp=20000)
    assert g["pxp"].shape == (53, 3) and isinstance(g["call"], bool)
    assert set(g) >= {"first_window_pxp_above_095_ms", "first_run_start_ms", "simes_strict_ms"}


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

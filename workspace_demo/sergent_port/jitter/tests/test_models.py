"""Tests of jitter/data.py and jitter/models.py (DESIGN rev 6 §3–§5 'Correctness'). Run with the t1_access venv:

    ../../t1_access/.venv/bin/python tests/test_models.py        (from sergent_port/jitter)
or  ../../t1_access/.venv/bin/python -m pytest tests -q

No fit here is a scientific result; the datasets are tiny and synthetic.
"""
import os
import sys

os.environ.setdefault("NPROC", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402

import data as D  # noqa: E402
import models as M  # noqa: E402


def _synthetic_dataset(span_name="primary", n_per_level=12, seed=0, W=None):
    rng = np.random.default_rng(seed)
    sp = D.span(span_name)
    W = sp.n_windows
    k = np.repeat(np.arange(6), n_per_level)
    mu0 = rng.normal(0.0, 0.2, size=W)
    A = rng.normal(size=(W, W)) * 0.15
    Sigma = A @ A.T + 0.3 * np.eye(W)
    resp = np.sin(np.linspace(0, np.pi, W)) ** 2
    Y = mu0 + 0.4 * k[:, None] * resp[None, :] + rng.multivariate_normal(np.zeros(W), Sigma, size=k.size)
    rng.shuffle(k)  # levels no longer aligned to Y rows: harmless for a likelihood-identity test
    return D.make_dataset(Y, k, sp, None, "test")


def _theta(sp, seed=1):
    rng = np.random.default_rng(seed)
    b = sp.basis()
    alpha = rng.normal(0.0, 0.5, size=5)
    gamma = rng.normal(0.0, 0.7, size=b.n_basis)
    return M.pack(sp, alpha, gamma, logkappa=0.3, x0=2.0, s_tau_ms=35.0, s_g=0.6)


# ---- data layer ------------------------------------------------------------------------------
def test_windows_and_spans():
    c = D.window_centres_ms()
    assert c[0] == -285.0 and c[52] == 1275.0
    st = D.window_sample_times_ms()
    assert st[0, 0] == -300.0 and st[0, -1] == -270.0 and st[52, -1] == 1290.0
    assert np.allclose(st[1:, 0], st[:-1, -1])  # consecutive windows share one sample (TWOI inclusive)
    p = D.span("primary")
    assert p.n_windows == 16 and c[p.windows[0]] == 255.0 and c[p.windows[-1]] == 705.0
    assert p.visible_range_ms == (240.0, 720.0) and p.support_ms == (90.0, 870.0)
    w = D.span("whole")
    assert w.n_windows == 53 and w.support_ms == (-450.0, 1440.0)


def test_block_folds_inherited():
    blocks = np.repeat(np.arange(1, 22), 3)  # a block 21 present
    p = D.participant_from_windows(np.zeros((blocks.size, 53)), np.zeros(blocks.size, dtype=int), blocks)
    f = D.folds(p)
    assert len(f) == 5
    tested = np.concatenate([te for _, te in f])
    assert np.all(blocks[tested] <= 20) and tested.size == 60 and D.n_scored(p) == 60
    assert all(np.all(blocks[tr] != 0) and (tr.size + te.size == blocks.size) for tr, te in f)


def test_ledoit_wolf_against_sklearn_if_available():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(120, 16)) @ (rng.normal(size=(16, 16)) * 0.3)
    X -= X.mean(axis=0)
    S, rho = D.ledoit_wolf(X)
    assert 0.0 <= rho <= 1.0 and np.allclose(S, S.T)
    assert np.all(np.linalg.eigvalsh(S) > 0)
    try:
        from sklearn.covariance import ledoit_wolf
    except Exception:
        return
    S2, rho2 = ledoit_wolf(X, assume_centered=True)
    assert np.allclose(S, S2, atol=1e-12) and abs(rho - rho2) < 1e-12


def test_whitening_identity():
    ds = _synthetic_dataset()
    wh = ds.wh
    assert np.allclose(wh.L @ wh.L.T, wh.Sigma)
    assert np.allclose(wh.Linv @ wh.L, np.eye(ds.W))
    assert abs(wh.logdet - np.linalg.slogdet(wh.Sigma)[1]) < 1e-9
    assert wh.n_catch == int(np.sum(ds.k == 0))
    assert np.allclose(ds.U @ wh.L.T + wh.mu0, ds.Y)


# ---- template basis ---------------------------------------------------------------------------
def test_primary_basis_matches_design():
    b = M.basis("primary")
    assert b.n_basis == 16
    assert b.invisible.tolist() == [0, 1, 14, 15]
    assert b.gauge == 7 and abs(b.support_centres_ms[7] - 450.0) < 1e-9
    assert np.allclose(np.diff(b.knots[4:-4]), 60.0)
    assert b.free_indices(True).size == 15 and b.free_indices(False).size == 11
    assert b.Bmat.shape == (31, 16, 16)
    # partition of unity, window averaged
    assert np.allclose(b.Bmat.sum(axis=2), 1.0)
    # at zero shift the shift-only functions contribute exactly nothing
    assert np.all(b.Bmat[b.node0][:, b.invisible] == 0.0)
    # the shifted nodes see them
    assert b.Bmat[0][:, [14, 15]].sum() > 0 and b.Bmat[-1][:, [0, 1]].sum() > 0
    # the τ = 0 node of the reduced basis equals the positive basis' node0
    r = M.basis("primary", 1)
    assert r.Bmat.shape[0] == 1 and np.allclose(r.Bmat[0], b.Bmat[b.node0])


def test_whole_basis():
    b = M.basis("whole")
    assert b.knots[0] == -450.0 and b.knots[-1] == 1440.0
    assert b.invisible.size == 4 and b.Bmat.shape == (31, 53, b.n_basis)
    assert np.allclose(b.Bmat.sum(axis=2), 1.0)
    assert abs(b.support_centres_ms[b.gauge] - 450.0) <= 30.0


def test_window_template_consistent_with_Bmat():
    b = M.basis("primary")
    c = np.random.default_rng(3).uniform(0.1, 2.0, size=b.n_basis)
    for i in (0, 7, 15, 30):
        assert np.allclose(b.window_template(c, b.nodes_ms[i]), b.Bmat[i] @ c)
    assert abs(b.m_vis(c) - np.mean(b.Bmat[b.node0] @ c)) < 1e-12
    assert np.allclose(b.eval_template(c, np.array([90.0, 870.0])), [c[0], c[-1]])   # clamped ends
    assert np.allclose(b.eval_template(c, np.array([-10.0, 1000.0]), clamp=True), [c[0], c[-1]])


# ---- quadrature -------------------------------------------------------------------------------
def test_truncnorm_nodes_and_realised_sd():
    nodes = M.tau_nodes_ms()
    assert nodes.size == 31 and nodes[0] == -150.0 and np.allclose(np.diff(nodes), 10.0)
    w = M.truncnorm_node_weights(nodes, 80.0)
    assert abs(w.sum() - 1.0) < 1e-12
    assert abs(M.realised_sd_ms(80.0) - 69.3) < 0.1          # design §4: 31-node 69.3 ms
    assert abs(M.truncated_parent_sd_ms(80.0) - 68.1) < 0.1  # design §4: truncated 68.1 ms
    w2 = M.truncnorm_node_weights(nodes, 2.0)
    assert w2[15] > 1 - 1e-5                                  # at the 2 ms floor the weights sit on node 0


def test_gh_lognormal_mean_one():
    z, lw = M.gh_nodes(7)
    for s in (0.0, 0.4, 1.0, 1.5):
        g = np.exp(-0.5 * s ** 2 + s * z)
        assert abs(np.sum(np.exp(lw) * g) - 1.0) < 2e-3
    z15, lw15 = M.gh_nodes(15)
    g = np.exp(-0.5 * 1.5 ** 2 + 1.5 * z15)
    assert abs(np.sum(np.exp(lw15) * g) - 1.0) < 1e-6


# ---- specs and packing ------------------------------------------------------------------------
def test_specs_and_parameter_counts():
    counts = {"G0": 5 + 11, "G1+": 5 + 15 + 1, "G2": 5 + 11 + 1, "G3+": 5 + 15 + 2,
              "B0": 7 + 11, "B1+": 7 + 15 + 1, "B2": 7 + 11 + 1, "B3+": 7 + 15 + 2}
    for name, n in counts.items():
        sp = M.spec(name)
        assert sp.name == name and sp.n_params == n, (name, sp.n_params, n)
        assert len(sp.param_names()) == n
    assert M.spec("G3+").reduced().name == "G2" and M.spec("B1+").reduced().name == "B0"
    c = M.spec("G3+").constrained(40.0)
    assert c.name == "G3@40" and c.positive and not c.tau_free and c.n_params == 5 + 15 + 1
    assert M.spec("G3+").constrained(0.0).name == "G2"
    lb, ub = M.spec("B3+").bounds()
    lay = M.spec("B3+").layout()["index"]
    assert lb[lay["theta_tau"]] == 0.02 and ub[lay["theta_tau"]] == 1.5
    assert lb[lay["s_g"]] == 0.0 and ub[lay["s_g"]] == 1.5
    assert abs(ub[lay["logkappa"]] - np.log(50.0)) < 1e-12 and lb[lay["logkappa"]] == -np.inf   # κ ≤ 50 (S2 repair)
    assert np.all(np.isinf(M.spec("G3+").bounds()[1][:5]))
    # κ = 50 already a step at integer levels: the neighbour of the active level is within 1e-17 of 0 or 1
    assert 1.0 / (1.0 + np.exp(50.0 * 0.8)) < 1e-17


def test_pack_unpack_roundtrip():
    sp = M.spec("B3+")
    th = _theta(sp)
    P = M.unpack(sp, th)
    assert P.a[0] == 0.0 and np.all(P.a[1:] > 0)
    assert abs(sp.basis().m_vis(P.c_tilde) - 1.0) < 1e-12            # T̃ has unit span mean at τ = 0
    assert abs(P.c[sp.basis().gauge] - np.log(2.0)) < 1e-12           # gauge coefficient softplus(0)
    assert P.s_tau_ms == 35.0 and P.s_g == 0.6 and P.A[0] == 0.0 and np.all(P.A[1:] >= M.A_MIN)
    red = M.spec("B2")
    Pr = M.unpack(red, M.pack(red, th[:5], np.zeros(16) + 0.3, 0.1, 2.0, 0.0, 0.2))
    assert np.all(Pr.c[red.basis().invisible] == 0.0) and Pr.s_tau_ms == 0.0


# ---- likelihood against the dense reference ---------------------------------------------------
def test_whitened_matches_dense_all_models():
    ds = _synthetic_dataset(n_per_level=4)
    for name in M.MODEL_NAMES + ("G3@40", "B3@5"):
        sp = M.spec(name) if "@" not in name else M.spec(name[0] + "3+").constrained(float(name.split("@")[1]))
        th = _theta(sp)
        ob = M.Objective(sp, ds)
        ll = ob.trial_loglik(th)
        ref = M.dense_trial_loglik(sp, th, ds.Y, ds.k, ds.wh.mu0, ds.wh.Sigma)
        assert ll.shape == ref.shape
        rel = np.max(np.abs(ll - ref) / np.maximum(1.0, np.abs(ref)))
        assert rel < 1e-10, (name, rel)
        v, g = ob(th)
        assert abs(v * ob.n_eff + ll.sum()) < 1e-9 * max(1.0, abs(v * ob.n_eff))   # the optimiser sees the per-trial mean
        assert abs(ob.total_loglik(th) - ll.sum()) < 1e-9 * max(1.0, abs(ll.sum()))
        assert np.all(np.isfinite(g)) and g.shape == (sp.n_params,)


def test_catch_trials_follow_mu0_sigma_exactly():
    ds = _synthetic_dataset(n_per_level=4)
    from scipy.stats import multivariate_normal
    for name in ("G3+", "B3+", "B0"):
        sp = M.spec(name)
        ob = M.Objective(sp, ds)
        ll = ob.trial_loglik(_theta(sp))
        ref = multivariate_normal.logpdf(ds.Y[ds.k == 0], ds.wh.mu0, ds.wh.Sigma)
        assert np.allclose(ll[ds.k == 0], ref, rtol=0, atol=1e-9)


def test_gradient_against_finite_differences():
    ds = _synthetic_dataset(n_per_level=5, seed=5)
    for name in ("G3+", "B3+", "B2"):
        sp = M.spec(name)
        th = _theta(sp, seed=7)
        ob = M.Objective(sp, ds)
        v0, g = ob(th)
        h = 1e-6
        for j in range(sp.n_params):
            e = np.zeros_like(th); e[j] = h
            fd = (ob(th + e)[0] - ob(th - e)[0]) / (2 * h)
            assert abs(fd - g[j]) < 1e-5 * max(1.0, abs(g[j])), (name, j, fd, g[j])


def test_reduced_equals_positive_at_vanishing_spread_and_scale():
    """G2 at the same visible parameters equals G3+ with s_τ → floor and s_g equal, up to the node weights at
    2 ms (weight on node 0 is 1 − 1e-6), and the catch anchoring makes level 0 identical."""
    ds = _synthetic_dataset(n_per_level=4, seed=9)
    red, pos = M.spec("G2"), M.spec("G3+")
    th_r = _theta(red)
    Pr = M.unpack(red, th_r)
    gamma_full = np.where(np.isfinite(M.softplus_inv(Pr.c)), M.softplus_inv(Pr.c), -20.0)
    th_p = M.pack(pos, M.softplus_inv(Pr.a[1:]), gamma_full, s_tau_ms=2.0, s_g=Pr.s_g)
    llr = M.Objective(red, ds).trial_loglik(th_r)
    llp = M.Objective(pos, ds).trial_loglik(th_p)
    assert np.max(np.abs(llr - llp)) < 1e-4


def test_padding_is_neutral():
    ds = _synthetic_dataset(n_per_level=7, seed=11)   # 42 trials -> padded to 64
    sp = M.spec("B1+")
    th = _theta(sp)
    ob = M.Objective(sp, ds)
    v, _ = ob(th)
    assert ob.n_eff == 42 and abs(v * 42 + ob.trial_loglik(th).sum()) < 1e-9 * abs(v * 42)
    assert ob.trial_loglik(th).shape == (42,)


def test_code_hash_is_stable():
    assert M.code_hash() == M.code_hash() and len(M.code_hash()) == 12


if __name__ == "__main__":
    import inspect
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception as e:  # noqa
                fails += 1
                import traceback; print("FAIL", name); traceback.print_exc(limit=3)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)

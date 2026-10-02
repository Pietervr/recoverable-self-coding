"""Tests of the §7.4 start policy (ledger row 4, draft amendment of 24 Sept 2026) as implemented in models.py and
wired through analyze.Config (2 Oct 2026). No fit is a scientific result; the fits here are on tiny synthetic
datasets and exist to check the mechanics: the table, the keyed streams, the tie-break, the padding, the legacy path.

    .venv/bin/python -m pytest test_start_policy.py -q
"""
import os
os.environ.setdefault("NPROC", "1")
import importlib
import numpy as np
import models as M
import analyze as A
import simulate as S


def _tiny(name="M2B", seed=3, n_per_level=6, n_concepts=4):
    rng = np.random.default_rng(seed)
    levels = np.array([0, 1, 2, 3, 4, 6, 8], dtype=float)
    k = np.tile(np.repeat(levels, n_per_level), n_concepts)
    cidx = np.repeat(np.arange(n_concepts), levels.size * n_per_level)
    mu = -1.0 + 2.0 / (1.0 + np.exp(-1.5 * (k - 3.0)))
    y = mu + 0.3 * rng.normal(size=k.size)
    return M.Trials.build(y, k, cidx, n_concepts)


def test_policy_table_matches_the_amendment():
    assert M.START_POLICY["M3H"] == ((32, 0.50),)
    assert M.START_POLICY["M2H"] == ((64, 0.25),)
    assert M.START_POLICY["M3V"] == ((32, 0.25),)
    for m in ("M3", "M3L", "M2K", "M2B"):
        assert M.START_POLICY[m] == ((64, 0.25), (16, 0.50))
    assert M.START_POLICY["M2S"] == ((64, 0.25),) and "M2S" in M.POLICY_OPEN
    assert M.START_POLICY["M0"] == ()
    assert M.PAD_MULTIPLE == 64
    assert set(M.START_POLICY) == set(M.ALL_MEMBERS)


def test_added_streams_are_keyed_deterministic_and_disjoint():
    base = np.zeros(5)
    a, ra = M.added_starts("M2B", base, (M.SIZE_OUTER, 0, (2026, 41)))
    b, rb = M.added_starts("M2B", base, (M.SIZE_OUTER, 0, (2026, 41)))
    assert a.shape == (80, 5) and np.array_equal(a, b)                       # same key -> identical starts
    c, _ = M.added_starts("M2B", base, (M.SIZE_OUTER, 1, (2026, 41)))
    assert not np.array_equal(a[0], c[0])                                    # another fold -> another stream
    d, _ = M.added_starts("M2B", base, (M.SIZE_INNER, 0, (2026, 41)))
    assert not np.array_equal(a[0], d[0])                                    # another size -> another stream
    assert len({r["key"] for r in ra}) == 80                                 # one key per added start
    assert [r["batch"] for r in ra][:64] == ["added:0:64@0.25"] * 64 and ra[64]["batch"] == "added:1:16@0.5"
    # the first added start's jitter is not the cold stream's first jitter under any plausible cold seeding
    cold = np.random.default_rng([2026, 41, 0, 3, 0]).normal(0.0, 0.25, size=5)
    assert not np.allclose(a[0], cold)
    e, re_ = M.added_starts("M0", base, (M.SIZE_OUTER, 0, 0))
    assert e.shape == (0, 5) and re_ == []


def test_pick_breaks_ties_by_lowest_start_index():
    th = np.zeros(2)
    runs = [dict(start=3, theta=th, loglik=-1.0, converged=True),
            dict(start=1, theta=th, loglik=-1.0, converged=True),
            dict(start=2, theta=th, loglik=-1.0, converged=True),
            dict(start=0, theta=th, loglik=-5.0, converged=True)]
    best, n = M._pick(runs)
    assert best["start"] == 1 and n == 4
    runs2 = [dict(start=0, theta=th, loglik=-1.0, converged=False), dict(start=1, theta=th, loglik=-1.0, converged=False)]
    best, n = M._pick(runs2)
    assert best["start"] == 0 and n == 0                                     # no converged run: best finite, flagged later


def test_padding_is_numerically_inert():
    data = _tiny("M2B")
    th = M.start_from_moments("M2B", M.moments(data))
    f64 = M.objective("M2B", data, M.GH_NODES_DEFAULT)
    v64, g64 = f64(th)
    keep = M.PAD_MULTIPLE
    try:
        M.PAD_MULTIPLE = 512
        data512 = M.Trials.build(*data.unpadded(), data.n_concepts, floor_sd=data.floor_sd)
        assert data512.y.size % 512 == 0 and data512.y.size != data.y.size
        f512 = M.objective("M2B", data512, M.GH_NODES_DEFAULT)
        v512, g512 = f512(th)
    finally:
        M.PAD_MULTIPLE = keep
    assert abs(float(v64) - float(v512)) <= 1e-13 * max(1.0, abs(float(v64)))
    assert np.max(np.abs(np.asarray(g64) - np.asarray(g512))) <= 1e-13 * max(1.0, np.max(np.abs(np.asarray(g64))))


def test_fit_under_the_policy_runs_cold_plus_added_and_records_sources():
    data = _tiny("M2B")
    r = M.fit("M2B", data, n_starts=2, rng=np.random.default_rng(0), policy_key=(M.SIZE_INNER, 0, (2026, 41)))
    assert r.policy == M.POLICY_NAME and r.n_added == 80 and r.n_starts == 82
    assert [x["source"] for x in r.runs[:2]] == ["cold", "cold"]
    assert all(x["source"] == "added" for x in r.runs[2:]) and r.runs[2]["key"][0] == "M2B"
    assert [x["start"] for x in r.runs] == list(range(82))                   # indices run on across batches
    assert np.isfinite(r.loglik)
    # determinism: the same key reproduces the same kept solution
    r2 = M.fit("M2B", data, n_starts=2, rng=np.random.default_rng(0), policy_key=(M.SIZE_INNER, 0, (2026, 41)))
    assert np.array_equal(r.theta, r2.theta) and r.loglik == r2.loglik


def test_legacy_fit_is_unchanged_without_a_key():
    data = _tiny("M2B")
    r = M.fit("M2B", data, n_starts=3, rng=np.random.default_rng(0))
    assert r.policy == "" and r.n_added == 0 and r.n_starts == 3
    assert all(x["source"] == "cold" for x in r.runs)


def test_config_and_hashes_carry_the_policy():
    c0 = A.Config()
    c1 = A.Config(start_policy=M.POLICY_NAME)
    assert A._policy_key(c0, M.SIZE_OUTER, 0, 2026, 41) is None
    assert A._policy_key(c1, M.SIZE_OUTER, 0, 2026, 41) == (M.SIZE_OUTER, 0, (2026, 41))
    assert A._policy_key(c1, M.SIZE_INNER, 2, 2026, 41, 1) == (M.SIZE_INNER, 2, (2026, 41, 1))
    h0 = S.config_hash(c0, 4, (41,), 2026)
    h1 = S.config_hash(c1, 4, (41,), 2026)
    assert h0 != h1
    try:
        A._policy_key(A.Config(start_policy="other"), M.SIZE_OUTER, 0, 1, 1)
        assert False, "an unknown policy name must raise"
    except ValueError:
        pass

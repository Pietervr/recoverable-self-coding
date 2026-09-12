#!/usr/bin/env python3
"""t1_access/verify.py — checks on models.py before anything is fitted to data.

V1  The inherited members M0, M2B, M3 equal the numpy originals in ../sergent_port/fit_models.py
    (llh_null, llh_logisticB, llh_logisbimodalfixedsigma) at random parameters and data, to 1e-9.
V2  JAX gradients of every member's objective agree with central finite differences.
V3  The Gauss–Hermite concept integral of the hierarchical members agrees with a dense quadrature at
    the CONF cluster size (n_c = 168), and the §7.4 node rule's successive changes are printed.
V4  The skew-normal density integrates to 1; the samplers' first two moments match the components.
V5  Each member refits its own generator at 64 x 168 trials (parameter recovery, loose tolerance).
"""
from __future__ import annotations

import os
import sys

import numpy as np

import models as M
import simulate as S

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "sergent_port")))
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from fit_models import llh_logisbimodalfixedsigma, llh_logisticB, llh_null  # noqa: E402

ok_all = True


def check(name, cond, detail=""):
    global ok_all
    ok_all &= bool(cond)
    print(f"[{'ok' if cond else 'FAIL'}] {name} {detail}")


def synthetic(name, seed=0, n_per_family=2, D=4, **kw):
    ds = S.make_dataset(name, S.generator_theta(name, **kw), n_per_family=n_per_family, D=D, layers=(41,), rho=0.0, seed=seed)
    return M.Trials.build(ds.y[:, 0], ds.k, ds.concept, ds.n_concepts), ds


# V1 — inherited likelihoods against the numpy originals
rng = np.random.default_rng(3)
data, _ = synthetic("M3", seed=3, sep=2.0)
y, k, cidx = data.unpadded()
for trial in range(5):
    p0 = np.array([rng.uniform(0.3, 2.0), rng.normal()])
    a = llh_null(p0, y); b = M.total_loglik("M0", p0, data)
    check("V1 M0 == llh_null", abs(a - b) < 1e-9 * max(1, abs(a)), f"{a:.6f} vs {b:.6f}")
    p2 = np.array([rng.uniform(1, 6), rng.uniform(0.2, 3), rng.normal(0, 2), rng.normal(0, 0.3), rng.uniform(0.3, 1.5), rng.normal()])
    a = llh_logisticB(p2, y, k); b = M.total_loglik("M2B", p2, data)
    check("V1 M2B == llh_logisticB", abs(a - b) < 1e-9 * max(1, abs(a)), f"{a:.6f} vs {b:.6f}")
    p3 = np.array([rng.uniform(1, 6), rng.uniform(0.2, 3), rng.normal(), rng.normal(), rng.uniform(0, 3), rng.uniform(0.2, 3), rng.uniform(0.3, 1.5)])
    a = llh_logisbimodalfixedsigma(p3, y, k, k == k.min()); b = M.total_loglik("M3", p3, data)
    check("V1 M3 == llh_logisbimodalfixedsigma", abs(a - b) < 1e-9 * max(1, abs(a)), f"{a:.6f} vs {b:.6f}")

# V2 — gradients
for name in M.ALL_MEMBERS:
    gen = name if name != "M0" else "M2B"
    data, _ = synthetic(gen, seed=5, tau=0.5, omega=0.3, sep=2.0, pi0=0.05, alpha=1.0)
    f = M.objective(name, data, n_gh=20)
    th = M.starts_from_moments(name, data, 2, np.random.default_rng(1))[1]
    v, g = f(th)
    h = 1e-5
    num = np.array([(f(th + h * e)[0] - f(th - h * e)[0]) / (2 * h) for e in np.eye(th.size)])
    rel = np.max(np.abs(num - g) / np.maximum(1.0, np.abs(g)))
    check(f"V2 grad {name}", rel < 1e-5, f"max rel err {rel:.2e}")

# V3 — Gauss–Hermite vs dense quadrature on single concepts at n_c = 168
for name, kw in (("M2H", dict(tau=1.0)), ("M2S", dict(omega=0.5)), ("M3H", dict(tau=1.0, sep=2.0))):
    data, ds = synthetic(name, seed=9, n_per_family=1, **kw)      # 8 concepts of 168 trials
    th = S.generator_theta(name, **kw)
    m = M.MEMBERS[name]
    tau = float(np.exp(th[m.re_index]))
    u = np.linspace(-9 * tau, 9 * tau, 60001)
    du = u[1] - u[0]
    yy, kk, cc = jnp.asarray(data.y), jnp.asarray(data.k), jnp.asarray(data.cidx)
    fl = M.M3V_FLOOR_FRACTION * data.floor_sd
    ll_u = jax.vmap(lambda uj: jax.ops.segment_sum(m.loglik(jnp.asarray(th), yy, kk, uj, fl) * jnp.asarray(data.mask), cc,
                                                   num_segments=data.n_concepts))(jnp.asarray(u))   # (U, C)
    logphi = -0.5 * (u / tau) ** 2 - np.log(tau) - 0.5 * np.log(2 * np.pi)
    dense = np.array(jax.scipy.special.logsumexp(ll_u + jnp.asarray(logphi)[:, None] + np.log(du), axis=0))
    chk = M.gh_node_check(name, th, data, counts=(64, 96, 128))
    errs = {n: float(np.max(np.abs(chk["scores"][n] - dense))) for n in chk["scores"]}
    print(f"     V3 {name} tau/omega={tau}: max |two-scale trapezoid - dense| by fine points {', '.join(f'{n}: {e:.2e}' for n, e in errs.items())}; "
          f"successive max change {', '.join(f'{n}: {e:.2e}' for n, e in chk['max_change'].items())}")
    check(f"V3 quadrature converges {name}", errs[96] < 1e-4, f"96-point error {errs[96]:.2e}")
    # the plain prior-centred rule of v1.1, for the record
    xs_, lw_ = M.gh_nodes(80)
    plain = np.array(jax.scipy.special.logsumexp(
        jax.vmap(lambda uj: jax.ops.segment_sum(m.loglik(jnp.asarray(th), yy, kk, uj, fl) * jnp.asarray(data.mask), cc,
                                                num_segments=data.n_concepts))(jnp.sqrt(2.0) * tau * xs_) + lw_[:, None], axis=0))
    print(f"     V3 {name}: plain prior-centred GH at 80 nodes misses by {float(np.max(np.abs(plain - dense))):.2e}")

# V4 — skew-normal normalisation and sampler moments
th = S.generator_theta("M2K", alpha=3.0)
yg = np.linspace(-15, 15, 200001)
for kk in (0.0, 3.0, 8.0):
    dens = np.exp(np.asarray(M.MEMBERS["M2K"].loglik(jnp.asarray(th), jnp.asarray(yg), jnp.asarray(np.full_like(yg, kk)), 0.0, 0.0)))
    z = np.trapezoid(dens, yg)
    check(f"V4 SN integrates to 1 at k={kk:g}", abs(z - 1) < 1e-6, f"{z:.8f}")
rng = np.random.default_rng(11)
for name, kw in (("M2B", {}), ("M2K", dict(alpha=3.0)), ("M3V", dict(sep=2.0)), ("M3L", dict(sep=2.0, pi0=0.2))):
    th = S.generator_theta(name, **kw)
    for kk in (0.0, 3.0, 8.0):
        ks = np.full(400000, kk)
        ys = M.sample(name, th, ks, rng=rng)
        c = M.components(name, th, ks)
        if c["kind"] == "normal":
            mean, var = c["mu"][0], c["sigma"][0] ** 2
        elif c["kind"] == "skew":
            d = c["alpha"][0] / np.sqrt(1 + c["alpha"][0] ** 2)
            mean = c["xi"][0] + c["omega"][0] * d * np.sqrt(2 / np.pi)
            var = c["omega"][0] ** 2 * (1 - 2 * d ** 2 / np.pi)
        else:
            A_ = c["A"][0]
            mean = (1 - A_) * c["mu_low"][0] + A_ * c["mu_high"][0]
            var = (1 - A_) * (c["sigma_low"][0] ** 2 + c["mu_low"][0] ** 2) + A_ * (c["sigma_high"][0] ** 2 + c["mu_high"][0] ** 2) - mean ** 2
        check(f"V4 sampler {name} k={kk:g}", abs(ys.mean() - mean) < 0.01 and abs(ys.var() - var) < 0.02,
              f"mean {ys.mean():.4f}/{mean:.4f} var {ys.var():.4f}/{var:.4f}")

# V5 — each member refits its own generator (64 concepts x 168)
for name in M.ALL_MEMBERS:
    if name == "M0":
        continue
    kw = dict(tau=0.5, omega=0.3, sep=2.0, pi0=0.1, alpha=1.5)
    data, _ = synthetic(name, seed=21, n_per_family=8, **kw)
    th = S.generator_theta(name, **kw)
    r = M.fit(name, data, n_gh=40, rng=np.random.default_rng(2))
    ll_true = M.total_loglik(name, th, data, 40)
    nat_true, nat_fit = M.natural(name, th), M.natural(name, r.theta)
    keys = [p for p in ("mu_low", "sigma", "tau", "omega", "pi0", "sep0", "mu_max", "xi_max", "x0") if p in nat_true]
    diffs = {p: (round(nat_true[p], 3), round(nat_fit[p], 3)) for p in keys}
    check(f"V5 refit {name}", r.loglik >= ll_true - 1e-6 and r.n_converged > 0,
          f"ll fit {r.loglik:.2f} >= ll true {ll_true:.2f}; conv {r.n_converged}/{r.n_starts}; {diffs}")

print("ALL OK" if ok_all else "SOME CHECKS FAILED")
sys.exit(0 if ok_all else 1)

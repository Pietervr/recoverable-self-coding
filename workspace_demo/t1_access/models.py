#!/usr/bin/env python3
"""t1_access/models.py — the finite model family of PREREGISTRATION_T1_model.md §7 and its fitting (§7.4).

Nine members. The three inherited comparators (§7.1) are line-by-line ports of the likelihoods in
../sergent_port/fit_models.py (themselves ports of Claire Sergent's LLH_fun_*.m), on the same raw
parameter vectors and with the same |sigma| conventions; `verify.py` checks them against the numpy
originals to 1e-9. The four graded (G) and four mixture (X) members are the pre-registration's, in the
ordered parameterisation of §7.3.

    null   M0   (sigma, mu)
    G      M2B  (x0, kappa, L, a, b, mu_max)                  inherited unimodal, affine sigma = |a*mu + b|
           M2H  M2B + t          x0 + u_c, u_c ~ N(0, tau^2), tau = e^t
           M2S  M2B + w          sigma_c(k) = |a*mu(k)+b| e^{v_c}, v_c ~ N(0, omega^2), omega = e^w
           M2K  (x0, kappa, L, a, b, xi_max, alpha0, alpha1)   skew-normal SN(xi(k), omega(k), alpha(k))
    X      M3   (x0, kappa, mu_low, step, L_high, k_high, sigma)   inherited bifurcation, unordered
           M3H  (mu_low, d0, d1, kA, kh, x0, s, t)   ordered; u_c on the shared x0 of A and lg_h; sigma = e^s
           M3V  (mu_low, d0, d1, kA, kh, x0, s0, s1) ordered; sigma_low = floor + e^{s0}, sigma_high = floor + e^{s1}
           M3L  (mu_low, d0, d1, kA, kh, x0, s, th0)  ordered; A(0) = sigmoid(th0), mu_high(0) = mu_low + e^{d0}

Ordered mixtures (§7.3): mu_high(k) = mu_low + e^{d0} + e^{d1} lg_h(k), lg_h(k) = sigmoid(kh (k - x0)),
A(k) = sigmoid(kA (k - x0)); A(0) = 0 at the catch level for M3H and M3V. The M3V floor is
0.05 * SD_train(y) of the OUTER training fold, passed in with the data (Trials.floor_sd) — never a
CONF-wide SD. The floor enters as sigma = floor + e^{s}, a smooth reparameterisation of "floored at".

Joint concept likelihood (§8.1): q_{m,c} = ∫ ∏_i p_m(y_ci | k_ci, u) p_m(u) du, the integral absent for
non-hierarchical members. Numerically (§7.4 as amended in v1.2): per concept, the mode u_hat of the
log-posterior in u is found by a 9-point grid start over ±4 tau and NEWTON_STEPS safeguarded Newton
steps (all unrolled inside the JAX graph, so the gradient of the objective is exact), the Laplace SD
s_hat is taken there (floored at tau), and the integral is a TRAP_POINTS trapezoid rule on
[u_hat ± 6 s_hat] in log space. Why not Gauss–Hermite: prior-centred nodes do not converge at the CONF
cluster size (168 trials per concept: 80 nodes still miss by 0.06–0.3 nat), and mode-centred
(adaptive) nodes fail for the concepts whose shifted threshold leaves the level range — their
likelihood is flat in u and the posterior is a truncated Gaussian that no node count integrates
(errors of 1–5 nat at tau = 2). The trapezoid rule on the adaptive window converges exponentially
for the peaked posteriors and covers the prior's range for the flat ones (verify.py V3 and the grid
check of 2026-09-11: within 6e-7 nat of dense quadrature everywhere but the truncated M2H posteriors at
tau = 2, where 96 points leave 0.02 nat). The point count is set on CAL/PILOT by the §7.4 rule
(`gh_node_check`: 48 -> 96 -> 192 until every concept's log q changes by < 1e-3); TRAP_POINTS is
provisional until then. GH_NODES_DEFAULT and the xs/lw arguments remain only as a plumbing constant.

Fitting (§7.4 as amended in v1.2): 8 starts from the declared generator (`starts_from_moments`: data
moments of the TRAINING fold only, start 0 unjittered, starts 1..7 jittered by a seeded N(0, 0.25^2)
in the parameter units the optimiser works in — the raw vectors above), each run L-BFGS-B
(ftol=1e-10, gtol=1e-6, maxiter=2000) on the JAX analytic gradient; converged = L-BFGS-B success; the
kept solution is the converged run with the highest training log-likelihood, else the best run,
flagged. Recovery (§9): 16 further starts, then 16 at doubled jitter.

Environment: the t1_access venv (Python 3.12, jax CPU, x64). Each process is pinned to ONE XLA thread
so that dataset-level parallelism (joblib) owns the cores: the XLA CPU client sizes its Eigen
intra-op pool from the NPROC environment variable (checked 2026-09-11 with jax 0.11.1: without it a
fit burns three cores through the pool's work-stealing, and the XLA_FLAGS thread flags do nothing;
with NPROC=1 CPU time equals wall time). Set before jax is imported; a shell may override it.
"""
from __future__ import annotations

import hashlib
import os

# the digest of THIS source as loaded, bound at this module's own import — the provenance every checkpoint, row and gain
# file carries for the model code (Codex, 12 Sept 2026, review 7); never re-read from disk later
with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()[:16]

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("NPROC", "1")
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1")
# BLAS thread caps, all three explicitly: joblib's workers raise any that is UNSET to cores // n_jobs, and
# OpenBLAS (the Linux numpy wheels) spin-waits on its idle threads — 48 workers on a 192-vCPU instance
# showed 197 s of CPU per 56 s fit until OPENBLAS_NUM_THREADS was pinned (2026-09-11).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import functools
import time as _time
from dataclasses import dataclass, field

import jax
import jax.numpy as jnp
import numpy as np
from jax.nn import log_sigmoid, sigmoid
from jax.scipy.special import log_ndtr, logsumexp
from scipy.optimize import minimize

jax.config.update("jax_enable_x64", True)

LEVELS = (0, 1, 2, 3, 4, 6, 8)   # §3; the pilot may move one interior level
K_MAX = 8.0                      # the anchor of the inherited M2B (xmax = max level present)
K_CATCH = 0.0                    # the catch level (inherited "first level present"; always 0 here, §3)
LOG_SQRT_2PI = 0.5 * np.log(2.0 * np.pi)
JITTER_SD = 0.25                 # §7.4 "N(0, 0.25)": read as the SD (v1.2)
N_STARTS = 8
N_STARTS_RECOVERY = 16
LBFGSB_OPTIONS = dict(ftol=1e-10, gtol=1e-6, maxiter=2000)
GH_NODES_DEFAULT = 20            # adaptive GH; provisional until the §7.4 rule is run on CAL/PILOT (10 -> 20 -> 40)
NEWTON_STEPS = 4                 # safeguarded Newton steps from the grid start (unrolled, differentiable); 4 = 6 on the grid
NEWTON_MAX_STEP = 3.0            # in units of tau, per step
NEWTON_CANDIDATES = 8            # backtracking fractions 1, 1/2, ..., 1/128 of the Newton step
GRID_POINTS = 9                  # coarse grid start for the mode: 9 points over ±GRID_HALFWIDTH tau (spacing tau)
GRID_HALFWIDTH = 4.0
TRAP_POINTS = 96                 # fine trapezoid rule per concept on [u_hat ± TRAP_HALFWIDTH s_hat] (the peak; for a
                                 # flat concept s_hat = tau and this window is the whole prior range: 64 left 1.9e-3)
TRAP_HALFWIDTH = 6.0
OUTER_POINTS = 32                # trapezoid rule on each outer interval between the fine window and ±PRIOR_HALFWIDTH tau
PRIOR_HALFWIDTH = 6.0            # the prior's range covered (mass beyond 6 tau: 2e-9); s_hat is CAPPED at tau by the
                                 # curvature safeguard, so the fine window never exceeds ±6 tau and the outer intervals
                                 # carry flat tails and second modes (M2H's anchored mean returns to mu_max at both extremes)
M3V_FLOOR_FRACTION = 0.05
PAD_MULTIPLE = 512               # trial arrays are padded to a multiple of this so that jit caches are reused

FAMILY_G = ("M2B", "M2H", "M2S", "M2K")
FAMILY_X = ("M3", "M3H", "M3V", "M3L")
ALL_MEMBERS = ("M0",) + FAMILY_G + FAMILY_X


# ----------------------------------------------------------------------------------------------
# data container
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Trials:
    """One fitting or scoring set: trials sorted by concept, padded to a multiple of PAD_MULTIPLE.

    y, k, mask: (n_pad,); cidx: (n_pad,) concept index 0..n_concepts-1 (padded rows -> 0, mask 0);
    floor_sd: the SD_train(y) of the OUTER training fold (M3V floor = M3V_FLOOR_FRACTION * floor_sd).
    """
    y: np.ndarray
    k: np.ndarray
    cidx: np.ndarray
    mask: np.ndarray
    n_concepts: int
    floor_sd: float

    @staticmethod
    def build(y, k, cidx, n_concepts: int, floor_sd: float | None = None) -> "Trials":
        y = np.asarray(y, dtype=np.float64)
        k = np.asarray(k, dtype=np.float64)
        cidx = np.asarray(cidx, dtype=np.int64)
        order = np.argsort(cidx, kind="stable")
        y, k, cidx = y[order], k[order], cidx[order]
        n = y.size
        n_pad = int(np.ceil(n / PAD_MULTIPLE) * PAD_MULTIPLE)
        yp = np.zeros(n_pad); kp = np.zeros(n_pad); cp = np.zeros(n_pad, dtype=np.int64); mp = np.zeros(n_pad)
        yp[:n], kp[:n], cp[:n], mp[:n] = y, k, cidx, 1.0
        if floor_sd is None:
            floor_sd = float(np.std(y, ddof=1)) if n > 1 else 1.0
        return Trials(yp, kp, cp, mp, int(n_concepts), float(floor_sd))

    @property
    def n(self) -> int:
        return int(self.mask.sum())

    def n_per_concept(self) -> np.ndarray:
        return np.bincount(self.cidx, weights=self.mask, minlength=self.n_concepts)

    def unpadded(self):
        m = self.mask > 0
        return self.y[m], self.k[m], self.cidx[m]


# ----------------------------------------------------------------------------------------------
# the likelihoods (per trial, natural log). theta: raw parameter vector; u: random effect (0 if none).
# ----------------------------------------------------------------------------------------------
def _lg(k, kappa, x0):
    return sigmoid(kappa * (k - x0))


def _log_norm(y, mu, sigma):
    return -0.5 * ((y - mu) / sigma) ** 2 - jnp.log(sigma) - LOG_SQRT_2PI


def _ll_M0(theta, y, k, u, floor):
    sigma, mu = theta[0], theta[1]
    sigma = jnp.abs(sigma)                         # inherited |sigma| (sergent_port D6)
    return _log_norm(y, mu, sigma)


def _m2b_mu(theta, k, u):
    x0, kappa, L, a, b, mu_max = theta[0], theta[1], theta[2], theta[3], theta[4], theta[5]
    x = x0 + u
    return L * _lg(k, kappa, x) - L * _lg(K_MAX, kappa, x) + mu_max


def _m2b_sigma(theta, mu):
    return jnp.abs(theta[3] * mu + theta[4])       # inherited affine sigma, |.| as in the port


def _ll_M2B(theta, y, k, u, floor):
    mu = _m2b_mu(theta, k, 0.0)
    return _log_norm(y, mu, _m2b_sigma(theta, mu))


def _ll_M2H(theta, y, k, u, floor):               # u on x0
    mu = _m2b_mu(theta, k, u)
    return _log_norm(y, mu, _m2b_sigma(theta, mu))


def _ll_M2S(theta, y, k, u, floor):               # u = v_c on the log scale
    mu = _m2b_mu(theta, k, 0.0)
    return _log_norm(y, mu, _m2b_sigma(theta, mu) * jnp.exp(u))


def _ll_M2K(theta, y, k, u, floor):
    xi = _m2b_mu(theta, k, 0.0)
    omega = jnp.abs(theta[3] * xi + theta[4])
    alpha = theta[6] + theta[7] * xi
    z = (y - xi) / omega
    return jnp.log(2.0) - jnp.log(omega) - 0.5 * z ** 2 - LOG_SQRT_2PI + log_ndtr(alpha * z)


def _ll_M3(theta, y, k, u, floor):                # inherited, line by line (unordered)
    x0, kappa, mu_low, step, L_high, k_high, sigma = (theta[i] for i in range(7))
    sigma = jnp.abs(sigma)
    catch = k == K_CATCH
    z = kappa * (k - x0)
    mu_high = L_high * _lg(k, k_high, x0) + step
    ln_low = _log_norm(y, mu_low, sigma)
    ln_high = _log_norm(y, mu_high, sigma)
    mix = jnp.logaddexp(log_sigmoid(-z) + ln_low, log_sigmoid(z) + ln_high)
    # at the catch level A = 0 and mu_high = mu_low: the mixture is exactly the low component
    return jnp.where(catch, ln_low, mix)


def _ordered(theta, k, u):
    mu_low, d0, d1, kA, kh, x0 = (theta[i] for i in range(6))
    x = x0 + u
    mu_high = mu_low + jnp.exp(d0) + jnp.exp(d1) * _lg(k, kh, x)
    zA = kA * (k - x)
    return mu_low, mu_high, log_sigmoid(zA), log_sigmoid(-zA)


def _ll_M3H(theta, y, k, u, floor):               # u on the shared x0
    mu_low, mu_high, logA, log1mA = _ordered(theta, k, u)
    sigma = jnp.exp(theta[6])
    ln_low = _log_norm(y, mu_low, sigma)
    mix = jnp.logaddexp(log1mA + ln_low, logA + _log_norm(y, mu_high, sigma))
    return jnp.where(k == K_CATCH, ln_low, mix)


def _ll_M3V(theta, y, k, u, floor):
    mu_low, mu_high, logA, log1mA = _ordered(theta, k, 0.0)
    s_low = floor + jnp.exp(theta[6])
    s_high = floor + jnp.exp(theta[7])
    ln_low = _log_norm(y, mu_low, s_low)
    mix = jnp.logaddexp(log1mA + ln_low, logA + _log_norm(y, mu_high, s_high))
    return jnp.where(k == K_CATCH, ln_low, mix)


def _ll_M3L(theta, y, k, u, floor):
    mu_low, mu_high, logA, log1mA = _ordered(theta, k, 0.0)
    sigma = jnp.exp(theta[6])
    th0 = theta[7]
    ln_low = _log_norm(y, mu_low, sigma)
    mix = jnp.logaddexp(log1mA + ln_low, logA + _log_norm(y, mu_high, sigma))
    mu_high0 = mu_low + jnp.exp(theta[1])
    mix0 = jnp.logaddexp(log_sigmoid(-th0) + ln_low, log_sigmoid(th0) + _log_norm(y, mu_high0, sigma))
    return jnp.where(k == K_CATCH, mix0, mix)


@dataclass(frozen=True)
class Member:
    name: str
    family: str                  # "null", "G" or "X"
    params: tuple
    loglik: callable
    re_index: int | None = None  # index of the log-scale parameter of the concept random effect
    mixture: bool = False

    @property
    def hierarchical(self) -> bool:
        return self.re_index is not None

    @property
    def n_params(self) -> int:
        return len(self.params)


MEMBERS = {
    "M0": Member("M0", "null", ("sigma", "mu"), _ll_M0),
    "M2B": Member("M2B", "G", ("x0", "kappa", "L", "a", "b", "mu_max"), _ll_M2B),
    "M2H": Member("M2H", "G", ("x0", "kappa", "L", "a", "b", "mu_max", "t"), _ll_M2H, re_index=6),
    "M2S": Member("M2S", "G", ("x0", "kappa", "L", "a", "b", "mu_max", "w"), _ll_M2S, re_index=6),
    "M2K": Member("M2K", "G", ("x0", "kappa", "L", "a", "b", "xi_max", "alpha0", "alpha1"), _ll_M2K),
    "M3": Member("M3", "X", ("x0", "kappa", "mu_low", "step", "L_high", "k_high", "sigma"), _ll_M3, mixture=True),
    "M3H": Member("M3H", "X", ("mu_low", "d0", "d1", "kA", "kh", "x0", "s", "t"), _ll_M3H, re_index=7, mixture=True),
    "M3V": Member("M3V", "X", ("mu_low", "d0", "d1", "kA", "kh", "x0", "s0", "s1"), _ll_M3V, mixture=True),
    "M3L": Member("M3L", "X", ("mu_low", "d0", "d1", "kA", "kh", "x0", "s", "th0"), _ll_M3L, mixture=True),
}


# ----------------------------------------------------------------------------------------------
# joint concept log-likelihood (§8.1) — Gauss–Hermite in log space for the hierarchical members
# ----------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def gh_nodes(n: int):
    """Physicists' Gauss–Hermite: ∫ f(u) N(u; 0, tau^2) du ≈ Σ_j (w_j/√π) f(√2 tau x_j)."""
    x, w = np.polynomial.hermite.hermgauss(int(n))
    return jnp.asarray(x), jnp.asarray(np.log(w) - 0.5 * np.log(np.pi))


def _agh_centre(member: Member, theta, y, k, cidx, mask, floor, n_concepts: int):
    """Per-concept mode u_hat and Laplace scale s_hat of the log-posterior in the random effect.

    The log-likelihood in u is exponential-shaped for a scale effect and logistic-saturating for a
    threshold effect, so Newton from u = 0 crawls (a step of about one unit per iteration) when a
    concept's effect sits several tau out — at tau = 2 eight plain steps left errors of tens of nat.
    Hence: a coarse grid start (GRID_POINTS over ±GRID_HALFWIDTH tau, the argmax per concept), then
    NEWTON_STEPS safeguarded Newton steps, each taking the best of the full, half and quarter step and
    staying put if none improves the log-posterior. Everything is `where`-selected, so the gradient of
    the objective flows through the selected points exactly.
    """
    tau = jnp.exp(theta[member.re_index])
    prec = 1.0 / tau ** 2
    seg = lambda v: jax.ops.segment_sum(v, cidx, num_segments=n_concepts, indices_are_sorted=True)

    def f(u_trial):                                                # total masked log-lik, u per trial
        return jnp.sum(member.loglik(theta, y, k, u_trial, floor) * mask)
    grad_f = jax.grad(f)

    def logpost(u_c):                                              # per-concept log-posterior (unnormalised)
        return seg(member.loglik(theta, y, k, u_c[cidx], floor) * mask) - 0.5 * u_c ** 2 * prec

    def curv(u_c):
        u_trial = u_c[cidx]
        g, h = jax.jvp(grad_f, (u_trial,), (jnp.ones_like(u_trial),))   # h = diag of the (diagonal) Hessian
        G = seg(g) - u_c * prec
        H = jnp.minimum(seg(h) - prec, -prec)                            # never flatter than the prior
        return G, H

    grid = jnp.linspace(-GRID_HALFWIDTH, GRID_HALFWIDTH, GRID_POINTS) * tau                  # (G,)
    lp_grid = jax.vmap(lambda g: logpost(jnp.full((n_concepts,), g)))(grid)                    # (G, C)
    u0 = grid[jnp.argmax(lp_grid, axis=0)]
    idx = jnp.arange(n_concepts)

    def newton(carry, _):
        u_c, lp_c = carry
        G, H = curv(u_c)
        step = jnp.clip(-G / H, -NEWTON_MAX_STEP * tau, NEWTON_MAX_STEP * tau)
        # backtracking over a geometric range of step fractions: a peak far narrower than tau (a scale effect
        # with a large fitted omega) needs fractions well below 1/4, or every candidate overshoots and the
        # search sticks at its grid start (audit_quadrature.py, M2S omega = 2 at fitted parameters, 2026-09-11)
        fracs = 2.0 ** -jnp.arange(NEWTON_CANDIDATES)
        cands = u_c[None, :] + fracs[:, None] * step[None, :]                                    # (K, C)
        lps = jax.vmap(logpost)(cands)                                                           # (K, C)
        best = jnp.argmax(lps, axis=0)
        u_new = cands[best, idx]
        lp_new = lps[best, idx]
        improved = lp_new > lp_c
        return (jnp.where(improved, u_new, u_c), jnp.where(improved, lp_new, lp_c)), None
    (u_hat, _), _ = jax.lax.scan(newton, (u0, jnp.max(lp_grid, axis=0)), None, length=NEWTON_STEPS)
    _, H = curv(u_hat)
    s_hat = 1.0 / jnp.sqrt(-H)
    return u_hat, s_hat, tau


@functools.lru_cache(maxsize=None)
def gl_nodes(n: int):
    """Gauss–Legendre on [-1, 1]: nodes and log weights."""
    x, w = np.polynomial.legendre.leggauss(int(n))
    return x, np.log(w)          # numpy: constants baked into the jit (a cached jnp array would leak a tracer)


def _concept_loglik(member: Member, theta, y, k, cidx, mask, floor, xs, lw, n_concepts: int):
    if not member.hierarchical:
        ll = member.loglik(theta, y, k, 0.0, floor) * mask
        return jax.ops.segment_sum(ll, cidx, num_segments=n_concepts, indices_are_sorted=True)
    u_hat, s_hat, tau = _agh_centre(member, theta, y, k, cidx, mask, floor, n_concepts)

    def one_node(u_c):
        ll = member.loglik(theta, y, k, u_c[cidx], floor) * mask
        return jax.ops.segment_sum(ll, cidx, num_segments=n_concepts, indices_are_sorted=True)

    def log_prior(u):
        return -0.5 * (u / tau) ** 2 - jnp.log(tau) - LOG_SQRT_2PI

    # Two-scale trapezoid rule per concept (xs, lw unused). The fine rule covers the peak, [u_hat ± 6 s_hat];
    # two outer rules cover the rest of the prior's range, [-6 tau, lo] and [hi, 6 tau], each with exact
    # endpoints so nothing is counted twice and nothing straddles a boundary. Why: Gauss–Hermite is exact
    # only for Gaussian-like posteriors; a concept whose shifted threshold lies outside the level range has
    # a flat likelihood in u (a truncated-Gaussian posterior), and M2H's anchored mean returns to mu_max at
    # both extremes of the threshold, so such a concept's posterior can have mass at both ends. The trapezoid
    # rule on a smooth Gaussian-tailed integrand converges exponentially; the outer rules see a smooth
    # prior-times-plateau integrand at spacing <= 12 tau / (OUTER_POINTS - 1). The independent check against
    # dense quadrature at generating AND fitted parameters is audit_quadrature.py.
    def trap(a, b, n_pts):
        """log ∫_a^b exp(logpost) du by the trapezoid rule with n_pts points, per concept; -inf where b <= a."""
        t = jnp.linspace(0.0, 1.0, n_pts)
        u_t = a[None, :] + (b - a)[None, :] * t[:, None]                                            # (N, C)
        h = (b - a) / (n_pts - 1)
        logw = jnp.where((jnp.arange(n_pts) == 0) | (jnp.arange(n_pts) == n_pts - 1), jnp.log(0.5), 0.0)
        val = logsumexp(jax.vmap(one_node)(u_t) + log_prior(u_t) + logw[:, None], axis=0) + jnp.log(jnp.maximum(h, 1e-300))
        return jnp.where(b > a, val, -jnp.inf)

    lo = u_hat - TRAP_HALFWIDTH * s_hat
    hi = u_hat + TRAP_HALFWIDTH * s_hat
    edge = PRIOR_HALFWIDTH * tau
    lo_c = jnp.clip(lo, -edge, edge)
    hi_c = jnp.clip(hi, -edge, edge)
    parts = jnp.stack([trap(lo, hi, TRAP_POINTS),
                       trap(jnp.full_like(lo, -edge), lo_c, OUTER_POINTS),
                       trap(hi_c, jnp.full_like(hi, edge), OUTER_POINTS)])                          # (3, C)
    return logsumexp(parts, axis=0)


@functools.lru_cache(maxsize=None)
def _compiled_centre(name: str):
    member = MEMBERS[name]
    f = lambda theta, y, k, cidx, mask, floor, C: _agh_centre(member, theta, y, k, cidx, mask, floor, C)[:2]
    return jax.jit(f, static_argnums=(6,))


def posterior_mode(name: str, theta, data: Trials) -> tuple:
    """(u_hat, s_hat) per concept: the posterior mode of the concept random effect and its Laplace SD."""
    member = MEMBERS[name]
    if not member.hierarchical:
        return np.zeros(data.n_concepts), np.zeros(data.n_concepts)
    fl = M3V_FLOOR_FRACTION * data.floor_sd
    u, s = _compiled_centre(name)(jnp.asarray(theta, dtype=jnp.float64), jnp.asarray(data.y), jnp.asarray(data.k),
                                  jnp.asarray(data.cidx), jnp.asarray(data.mask), fl, data.n_concepts)
    return np.asarray(u), np.asarray(s)


@functools.lru_cache(maxsize=None)
def _compiled_scores(name: str):
    member = MEMBERS[name]
    f = lambda theta, y, k, cidx, mask, floor, xs, lw, C: _concept_loglik(member, theta, y, k, cidx, mask, floor, xs, lw, C)
    return jax.jit(f, static_argnums=(8,))


@functools.lru_cache(maxsize=None)
def _compiled_objective(name: str):
    member = MEMBERS[name]
    f = lambda theta, y, k, cidx, mask, floor, xs, lw, C: -jnp.sum(
        _concept_loglik(member, theta, y, k, cidx, mask, floor, xs, lw, C))
    return jax.jit(jax.value_and_grad(f), static_argnums=(8,))


def _args(member: Member, data: Trials, n_gh: int):
    if member.hierarchical:
        xs, lw = gh_nodes(n_gh)
    else:
        xs, lw = gh_nodes(1)
    floor = M3V_FLOOR_FRACTION * data.floor_sd
    return (jnp.asarray(data.y), jnp.asarray(data.k), jnp.asarray(data.cidx), jnp.asarray(data.mask),
            floor, xs, lw, data.n_concepts)


def concept_scores(name: str, theta, data: Trials, n_gh: int = GH_NODES_DEFAULT) -> np.ndarray:
    """log q_{m,c} for every concept of `data` (§8.1), shape (n_concepts,)."""
    member = MEMBERS[name]
    out = _compiled_scores(name)(jnp.asarray(theta, dtype=jnp.float64), *_args(member, data, n_gh))
    return np.asarray(out)


def total_loglik(name: str, theta, data: Trials, n_gh: int = GH_NODES_DEFAULT) -> float:
    return float(np.sum(concept_scores(name, theta, data, n_gh)))


def objective(name: str, data: Trials, n_gh: int = GH_NODES_DEFAULT):
    """Returns f(theta) -> (neg log-lik, gradient) as numpy float64, for scipy."""
    member = MEMBERS[name]
    fn = _compiled_objective(name)
    args = _args(member, data, n_gh)
    big = 1e30

    def f(theta):
        v, g = fn(jnp.asarray(theta, dtype=jnp.float64), *args)
        v = float(v)
        g = np.asarray(g, dtype=np.float64)
        if not np.isfinite(v) or not np.all(np.isfinite(g)):
            return big, np.zeros_like(g)
        return v, g
    return f


# ----------------------------------------------------------------------------------------------
# the declared start generator (§7.4): data moments of the TRAINING fold, then seeded jitter
# ----------------------------------------------------------------------------------------------
def moments(data: Trials) -> dict:
    y, k, _ = data.unpadded()
    lv = np.unique(k)
    means = {float(l): float(np.mean(y[k == l])) for l in lv}
    sds = {float(l): (float(np.std(y[k == l], ddof=1)) if np.sum(k == l) > 1 else float(np.std(y, ddof=1))) for l in lv}
    kmin, kmax = float(lv.min()), float(lv.max())
    k1 = float(lv[1]) if lv.size > 1 else kmax             # lowest non-catch level (inherited "SNR_list[1]")
    sd = float(np.std(y, ddof=1)) if y.size > 1 else 1.0
    m0, m1, m8 = means[kmin], means[k1], means[kmax]
    s0, s1, s8 = sds[kmin], sds[k1], sds[kmax]
    # x_mid: the level at which the piecewise-linear profile of level means crosses (m0 + m8)/2
    target = 0.5 * (m0 + m8)
    xs = [float(l) for l in lv]
    ms = [means[l] for l in xs]
    x_mid = 0.5 * (kmin + kmax)
    if m8 != m0:
        sign = 1.0 if m8 > m0 else -1.0
        for i in range(1, len(xs)):
            if sign * (ms[i] - target) >= 0:
                lo, hi = ms[i - 1], ms[i]
                frac = 0.0 if hi == lo else (target - lo) / (hi - lo)
                x_mid = xs[i - 1] + frac * (xs[i] - xs[i - 1])
                break
    x_mid = float(np.clip(x_mid, kmin + 0.5, kmax - 0.5))
    return dict(m0=m0, m1=m1, m8=m8, s0=s0, s1=s1, s8=s8, sd=sd, mean=float(np.mean(y)),
                kmin=kmin, k1=k1, kmax=kmax, x_mid=x_mid, floor=M3V_FLOOR_FRACTION * data.floor_sd)


def start_from_moments(name: str, mom: dict) -> np.ndarray:
    m0, m1, m8, s0, s1, s8, sd = (mom[x] for x in ("m0", "m1", "m8", "s0", "s1", "s8", "sd"))
    span = mom["kmax"] - mom["k1"]
    eps = 0.1 * sd if sd > 0 else 0.1
    if name == "M0":
        return np.array([sd, mom["mean"]])
    if name in ("M2B", "M2H", "M2S", "M2K"):
        # the inherited initialisation (fit_models.py), on the training fold
        x0 = 0.5 * (mom["kmax"] + mom["k1"])
        kappa = (m8 - m1) / span
        L = 2.0 * m8
        a = (s8 - s1) / (m8 - m1) if m8 != m1 else 0.0
        b = s8 - a * m8
        base = [x0, kappa, L, a, b, m8]
        if name == "M2B":
            return np.array(base)
        if name == "M2H":
            return np.array(base + [np.log(0.5)])
        if name == "M2S":
            return np.array(base + [np.log(0.3)])
        return np.array(base + [0.0, 0.0])
    if name == "M3":
        # the inherited initialisation
        x0 = 0.5 * (mom["kmax"] + mom["k1"])
        kappa = (m8 - m1) / span
        return np.array([x0, kappa, m0, m1 - m0, m8 - m1, kappa, s0])
    # ordered mixtures
    d0 = np.log(max(m1 - m0, eps))
    d1 = np.log(max(m8 - m1, eps))
    base = [m0, d0, d1, 1.0, 1.0, mom["x_mid"]]
    if name == "M3H":
        return np.array(base + [np.log(max(s0, eps)), np.log(0.5)])
    if name == "M3V":
        fl = mom["floor"]
        return np.array(base + [np.log(max(s0 - fl, eps)), np.log(max(s8 - fl, eps))])
    if name == "M3L":
        return np.array(base + [np.log(max(s0, eps)), np.log(0.05 / 0.95)])
    raise KeyError(name)


def starts_from_moments(name: str, data: Trials, n_starts: int, rng: np.random.Generator,
                        jitter_sd: float = JITTER_SD) -> np.ndarray:
    """(n_starts, p): start 0 = the moment start, the rest jittered by N(0, jitter_sd^2) per coordinate."""
    base = start_from_moments(name, moments(data))
    out = np.tile(base, (n_starts, 1))
    if n_starts > 1:
        out[1:] += rng.normal(0.0, jitter_sd, size=(n_starts - 1, base.size))
    return out


# ----------------------------------------------------------------------------------------------
# fitting (§7.4, v1.2) and recovery (§9)
# ----------------------------------------------------------------------------------------------
@dataclass
class FitResult:
    member: str
    theta: np.ndarray
    loglik: float               # training log-likelihood of the kept solution
    converged: bool             # the kept solution comes from a converged run
    n_converged: int
    n_starts: int
    recovery: int = 0           # 0 none, 1 = +16 starts, 2 = +16 at doubled jitter
    nfev: int = 0
    nit: int = 0
    seconds: float = 0.0
    runs: list = field(default_factory=list)

    @property
    def flagged(self) -> bool:
        return not self.converged


def _run_starts(name: str, data: Trials, starts: np.ndarray, n_gh: int, options: dict) -> list:
    f = objective(name, data, n_gh)
    runs = []
    for i, x0 in enumerate(starts):
        res = minimize(f, x0, jac=True, method="L-BFGS-B", options=options)
        ll = -float(res.fun) if np.isfinite(res.fun) and res.fun < 1e29 else -np.inf
        runs.append(dict(start=i, theta=np.asarray(res.x), loglik=ll, converged=bool(res.success),
                         nfev=int(res.nfev), nit=int(res.nit), message=str(res.message)))
    return runs


def _pick(runs: list):
    conv = [r for r in runs if r["converged"] and np.isfinite(r["loglik"])]
    pool = conv if conv else [r for r in runs if np.isfinite(r["loglik"])]
    if not pool:
        return None, len(conv)
    best = max(pool, key=lambda r: r["loglik"])
    return best, len(conv)


def fit(name: str, data: Trials, n_gh: int = GH_NODES_DEFAULT, n_starts: int = N_STARTS,
        rng: np.random.Generator | None = None, jitter_sd: float = JITTER_SD,
        options: dict | None = None, recovery: bool = True) -> FitResult:
    """Multi-start L-BFGS-B fit of member `name` on `data` (§7.4 v1.2), with the §9 recovery chain."""
    rng = np.random.default_rng(0) if rng is None else rng
    options = dict(LBFGSB_OPTIONS) if options is None else options
    t0 = _time.time()
    starts = starts_from_moments(name, data, n_starts, rng, jitter_sd)
    runs = _run_starts(name, data, starts, n_gh, options)
    best, n_conv = _pick(runs)
    level = 0
    if recovery and (best is None or n_conv == 0):
        level = 1
        more = starts_from_moments(name, data, N_STARTS_RECOVERY + 1, rng, jitter_sd)[1:]
        runs += _run_starts(name, data, more, n_gh, options)
        best, n_conv = _pick(runs)
        if best is None or n_conv == 0:
            level = 2
            more = starts_from_moments(name, data, N_STARTS_RECOVERY + 1, rng, 2.0 * jitter_sd)[1:]
            runs += _run_starts(name, data, more, n_gh, options)
            best, n_conv = _pick(runs)
    if best is None:
        p = MEMBERS[name].n_params
        return FitResult(name, np.full(p, np.nan), -np.inf, False, 0, len(runs), level,
                         sum(r["nfev"] for r in runs), 0, _time.time() - t0, runs)
    return FitResult(name, best["theta"], best["loglik"], bool(best["converged"]), n_conv, len(runs), level,
                     sum(r["nfev"] for r in runs), sum(r["nit"] for r in runs), _time.time() - t0, runs)


def gh_node_check(name: str, theta, data: Trials, counts=(64, 96, 128)) -> dict:
    """§7.4 quadrature rule: per-concept log q at each fine point count (TRAP_POINTS, with OUTER_POINTS at a
    third of it) and the max |change| between successive counts; frozen at the first whose change is < 1e-3."""
    global TRAP_POINTS, OUTER_POINTS
    keep = (TRAP_POINTS, OUTER_POINTS)
    scores = {}
    try:
        for n in counts:
            TRAP_POINTS, OUTER_POINTS = int(n), max(8, int(n) // 3)
            _compiled_scores.cache_clear()
            scores[n] = concept_scores(name, theta, data)
    finally:
        TRAP_POINTS, OUTER_POINTS = keep
        _compiled_scores.cache_clear()
    changes = {counts[i + 1]: float(np.max(np.abs(scores[counts[i + 1]] - scores[counts[i]])))
               for i in range(len(counts) - 1)}
    return dict(scores=scores, max_change=changes)


# ----------------------------------------------------------------------------------------------
# natural parameters, state posteriors and samplers (used by simulate.py and later h3.py)
# ----------------------------------------------------------------------------------------------
def natural(name: str, theta) -> dict:
    th = np.asarray(theta, dtype=float)
    m = MEMBERS[name]
    d = dict(zip(m.params, th))
    if name == "M0":
        d["sigma"] = abs(d["sigma"])
    if name == "M2H":
        d["tau"] = float(np.exp(d["t"]))
    if name == "M2S":
        d["omega"] = float(np.exp(d["w"]))
    if name == "M3":
        d["sigma"] = abs(d["sigma"])
    if name in ("M3H", "M3V", "M3L"):
        d["sep0"] = float(np.exp(d["d0"])); d["sep1"] = float(np.exp(d["d1"]))
    if name == "M3H":
        d["sigma"] = float(np.exp(d["s"])); d["tau"] = float(np.exp(d["t"]))
    if name == "M3L":
        d["sigma"] = float(np.exp(d["s"])); d["pi0"] = float(1.0 / (1.0 + np.exp(-d["th0"])))
    return d


def _np_sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def components(name: str, theta, k, u=0.0, floor: float = 0.0) -> dict:
    """numpy: the per-trial generating quantities of a member at levels k (and random effect u)."""
    th = np.asarray(theta, dtype=float)
    k = np.asarray(k, dtype=float)
    catch = k == K_CATCH
    if name == "M0":
        return dict(kind="normal", mu=np.full_like(k, th[1]), sigma=np.full_like(k, abs(th[0])))
    if name in ("M2B", "M2H", "M2S", "M2K"):
        x0, kappa, L, a, b, mu_max = th[:6]
        x = x0 + (u if name == "M2H" else 0.0)
        mu = L * _np_sigmoid(kappa * (k - x)) - L * _np_sigmoid(kappa * (K_MAX - x)) + mu_max
        sigma = np.abs(a * mu + b)
        if name == "M2S":
            sigma = sigma * np.exp(u)
        if name == "M2K":
            return dict(kind="skew", xi=mu, omega=sigma, alpha=th[6] + th[7] * mu)
        return dict(kind="normal", mu=mu, sigma=sigma)
    if name == "M3":
        x0, kappa, mu_low, step, L_high, k_high, sigma = th[:7]
        A = np.where(catch, 0.0, _np_sigmoid(kappa * (k - x0)))
        mu_high = np.where(catch, mu_low, L_high * _np_sigmoid(k_high * (k - x0)) + step)
        s = abs(sigma)
        return dict(kind="mixture", A=A, mu_low=np.full_like(k, mu_low), mu_high=mu_high,
                    sigma_low=np.full_like(k, s), sigma_high=np.full_like(k, s))
    mu_low, d0, d1, kA, kh, x0 = th[:6]
    x = x0 + (u if name == "M3H" else 0.0)
    mu_high = mu_low + np.exp(d0) + np.exp(d1) * _np_sigmoid(kh * (k - x))
    A = _np_sigmoid(kA * (k - x))
    if name == "M3H":
        s_low = s_high = np.exp(th[6]); A = np.where(catch, 0.0, A)
    elif name == "M3V":
        s_low, s_high = floor + np.exp(th[6]), floor + np.exp(th[7]); A = np.where(catch, 0.0, A)
    else:  # M3L
        s_low = s_high = np.exp(th[6])
        A = np.where(catch, _np_sigmoid(th[7]), A)
        mu_high = np.where(catch, mu_low + np.exp(d0), mu_high)
    return dict(kind="mixture", A=A, mu_low=np.full_like(k, mu_low), mu_high=mu_high,
                sigma_low=np.full_like(k, s_low), sigma_high=np.full_like(k, s_high))


def state_posterior(name: str, theta, y, k, u=0.0, floor: float = 0.0) -> np.ndarray:
    """P(high state | y, k) under a mixture member (§8.5(b), §11); numpy."""
    c = components(name, theta, k, u, floor)
    if c["kind"] != "mixture":
        raise ValueError(f"{name} is not a mixture member")
    y = np.asarray(y, dtype=float)
    def ln(mu, s):
        return -0.5 * ((y - mu) / s) ** 2 - np.log(s)
    with np.errstate(divide="ignore"):
        lo = np.log1p(-c["A"]) + ln(c["mu_low"], c["sigma_low"])
        hi = np.log(c["A"]) + ln(c["mu_high"], c["sigma_high"])
    return np.exp(hi - np.logaddexp(lo, hi))


def posterior_u(name: str, theta, data: Trials, n_gh: int = GH_NODES_DEFAULT) -> np.ndarray:
    """Plug-in value of the concept random effect for §11: the posterior mode per concept; numpy."""
    return posterior_mode(name, theta, data)[0]


def sample(name: str, theta, k, u=0.0, rng: np.random.Generator | None = None, noise: dict | None = None,
           floor: float = 0.0) -> np.ndarray:
    """Draw y for levels k under member `name`. `noise` may supply standard draws so that a caller can
    correlate them across layers: eps (N(0,1)), eps2 (N(0,1), skew-normal only), unif (U(0,1), mixtures)."""
    rng = np.random.default_rng() if rng is None else rng
    k = np.asarray(k, dtype=float)
    n = k.size
    noise = {} if noise is None else noise
    eps = noise.get("eps", rng.normal(size=n))
    c = components(name, theta, k, u, floor)
    if c["kind"] == "normal":
        return c["mu"] + c["sigma"] * eps
    if c["kind"] == "skew":
        eps2 = noise.get("eps2", rng.normal(size=n))
        delta = c["alpha"] / np.sqrt(1.0 + c["alpha"] ** 2)
        return c["xi"] + c["omega"] * (delta * np.abs(eps2) + np.sqrt(1.0 - delta ** 2) * eps)
    unif = noise.get("unif", rng.uniform(size=n))
    high = unif < c["A"]
    mu = np.where(high, c["mu_high"], c["mu_low"])
    s = np.where(high, c["sigma_high"], c["sigma_low"])
    return mu + s * eps


if __name__ == "__main__":
    # smoke: fit every member on a small synthetic dataset
    rng = np.random.default_rng(1)
    C, ncar, D = 16, 6, 4
    k = np.tile(np.repeat(np.array(LEVELS, float), ncar * D), C)
    cidx = np.repeat(np.arange(C), ncar * D * len(LEVELS))
    th = np.array([-1.0, np.log(0.6), np.log(1.0), 1.5, 1.5, 3.0, np.log(0.6), np.log(0.5)])
    y = sample("M3H", th, k, u=0.0, rng=rng)
    data = Trials.build(y, k, cidx, C)
    for name in ALL_MEMBERS:
        r = fit(name, data, rng=np.random.default_rng(0))
        print(f"{name:4s} ll={r.loglik:12.3f} conv={r.n_converged}/{r.n_starts} rec={r.recovery} {r.seconds:5.1f}s")

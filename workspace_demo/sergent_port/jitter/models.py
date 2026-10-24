#!/usr/bin/env python3
"""jitter/models.py — the two model families of DESIGN_jitter.md rev 6 §4 and the whitened-projection marginal
likelihood of §5. Stage S1 (provisional implementation; nothing here is frozen before S3).

Graded family   y_i | k_i, τ_i, g_i ~ N( μ0 + g_i a(k_i) T̃(· − τ_i), Σ )
Two-state family z_i ~ Bernoulli(A(k_i)); y | z=0 ~ N(μ0, Σ); y | z=1 ~ N( μ0 + g m_H(k) T̃(· − τ), Σ ), m_H = a/A
  a(k) = softplus(α_k), k = 1..5, a(0) = 0;  A(k) = max(A_MIN, logistic_{κ,x0}(k)), A(0) = 0, κ = exp(logκ)
  template T = Σ_j c_j B_j (cubic B-spline, open-clamped, interior knots every 60 ms on the support = span
  sample-time range ± 150 ms), c_j = softplus(γ_j), the gauge coefficient (visible basis function centred nearest
  450 ms, ties to the earlier) fixed at γ = 0, T̃ = T / m_vis(T) with m_vis = mean of T over the span's windows at
  τ = 0; a window's template value = mean of T̃ over its 16 sample times.
  τ ~ N(0, s_τ²) truncated to ±150 ms on 31 nodes (10 ms), truncated-normal weights normalised; s_τ ∈ [2, 150] ms in
  POSITIVE-SPREAD models; the exact s_τ = 0 model is REDUCED (one node, shift-only coefficients removed).
  g ~ LogNormal(−s_g²/2, s_g²); s_g ∈ [0, 1.5]. S2 numerical repair (24 Oct 2026): the scale integral uses an
  ADAPTIVE Gauss–Hermite rule in u = log g — per trial and latency node the nodes are centred on the mode of the
  log-integrand h(u) = −(u − μ_p)²/(2s_g²) + mP e^u − ½m²vv e^{2u} (8 safeguarded Newton steps from the
  precision-blended likelihood peak) and scaled by its curvature, with the e^{x²} correction (Liu & Pierce 1994),
  N_G_NODES = 17 (checked against 33). The design's prior-centred rule (7 nodes checked against 15) was found
  inadequate on the first development set: strong trials have scale likelihoods far sharper than the prior, the
  7-node rule mis-scored G3 by 2–3.5 nat per fold and the B3 − G3 contrast was still moving at 31 and 61 fixed
  nodes; the prior-centred rule stays available as `ModelSpec.adaptive_g = False` for the §4 node check. Models
  without a scale term (G0, G1, B0, B1) integrate nothing: g ≡ 1 exactly.

Models: G0 (s_τ = s_g = 0), G1 (s_τ free), G2 (s_g free), G3 (both); B0–B3 alike. In code the positive-spread
candidates are the specs "G1+", "G3+", "B1+", "B3+"; the reduced models "G0", "G2", "B0", "B2"; a constrained
profile fit is the positive-spread vector with s_τ FIXED at a grid value (`spec.tau_fixed_ms` > 0).

Likelihood (§5): Σ is Cholesky-whitened once per fold; u_i = L⁻¹(y_i − μ0), v_τ = L⁻¹ T̃_τ per node;
  log N(y_i | μ0 + g m T̃_τ, Σ) = −½W log 2π − ½ log|Σ| − ½‖u_i‖² + g m (u_i·v_τ) − ½ (g m)² ‖v_τ‖²;
all trial–template projections are one matrix product U Vᵀ; the (n × 31 × 7) logit tensor is reduced by
log-sum-exp over nodes; the two-state low branch is the m = 0 term and the branches combine by log-sum-exp with
the occupancy weights. No residual tensor over nodes is formed. `dense_trial_loglik` is the direct dense reference
implementation the tests compare against (1e-10 relative).

Parameter vector (optimiser units; §5 scaling: times in ms/100, amplitudes in decoder units, logits unit):
  [α_1..α_5, γ_free (11 reduced / 15 positive), (logκ, x0 | B), (θ_τ = s_τ/100 ms | tau free), (s_g | scale free)]

Environment: one XLA thread per process (NPROC=1 set before jax is imported; see t1_access/models.py), float64.
"""
from __future__ import annotations

import os

os.environ.setdefault("NPROC", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import hashlib  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from functools import lru_cache  # noqa: E402

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
from jax.scipy.special import logsumexp  # noqa: E402
from scipy.interpolate import BSpline  # noqa: E402
from scipy.stats import multivariate_normal  # noqa: E402

from data import N_LEVELS, TAU_TRUNC_MS, Span  # noqa: E402

jax.config.update("jax_enable_x64", True)

A_MIN = 0.02
KAPPA_MAX = 50.0              # S2 numerical repair (24 Oct 2026): box κ ≤ 50 per level unit. Beyond ≈ 50 the occupancy
#                               logistic is a step at the integer levels (neighbours within 1e-17 of 0 or 1), so no fit is
#                               lost; without the box, B3+ on graded data ran κ to 1e5–1e15 with x0 pinned at a level and
#                               three of four starts stalled on that ridge at a worse objective than the smooth optimum.
KNOT_SPACING_MS = 60.0
GAUGE_CENTRE_MS = 450.0
TAU_NODE_STEP_MS = 10.0
N_TAU_NODES = 31
N_G_NODES = 17                # adaptive Gauss–Hermite nodes in log g (checked against 33 in S2). Measured envelope
#                               against a fine trapezoid, worst case per (trial, node): 8e-6 nat for s_g ≤ 0.6 (2e-7 at
#                               33 nodes), 2e-4 at s_g = 1.0 (6e-6), 7e-3 at the s_g = 1.5 box edge (2e-4; such fits
#                               are flagged) — the mode-centred rule converges slowly when a wide scale prior meets a
#                               likelihood of comparable precision. Fitted s_g on the real participants: 0.14–0.77.
N_G_NODES_PRIOR = 7           # the design's prior-centred rule (kept for the node check)
NEWTON_STEPS = 4              # the blended start is within Newton's quadratic basin; 4 = 8 steps to 1e-12
S_G_EPS = 1e-12               # s_g² floor inside the adaptive rule (s_g = 0 sits on the box)
MODE_CLIP_SD = 12.0           # |û − μ_p| ≤ 12 s_g
S_TAU_MIN_MS = 2.0
S_TAU_MAX_MS = 150.0
S_G_MAX = 1.5
GAMMA_MIN = -30.0             # S2 repair 3 (24 Oct 2026): lower box on every template coordinate (c >= 1e-13). Without it
#                               L-BFGS-B ran coefficients that want to be zero off along the flat direction (archived W2
#                               set 1: median per-fit minimum gamma -75, 43 of 194 fits below -700, worst -1.9e6), softplus
#                               underflowed to c = 0 and every lifted warm start was packed with -inf (NONFINITE).
TIME_SCALE = 100.0            # θ_τ = s_τ / 100 ms
PAD_MULTIPLE = 64
LOG2PI = float(np.log(2.0 * np.pi))

FAMILIES = ("G", "B")
MODEL_NAMES = ("G0", "G1+", "G2", "G3+", "B0", "B1+", "B2", "B3+")
SELECTED_NAMES = {"G1": ("G0", "G1+"), "G3": ("G2", "G3+"), "B1": ("B0", "B1+"), "B3": ("B2", "B3+")}


# ----------------------------------------------------------------------------------------------
# template basis on a span
# ----------------------------------------------------------------------------------------------
def tau_nodes_ms(n_nodes: int = N_TAU_NODES) -> np.ndarray:
    """Equally spaced latency nodes on ±150 ms (31 → 10 ms); one node = the exact-zero REDUCED model."""
    if n_nodes == 1:
        return np.zeros(1)
    return np.linspace(-TAU_TRUNC_MS, TAU_TRUNC_MS, n_nodes)


def spline_knots(lo: float, hi: float, spacing: float = KNOT_SPACING_MS) -> np.ndarray:
    """Open-clamped cubic knot vector with interior knots at (as near as uniformly) `spacing` ms."""
    n_int = max(int(round((hi - lo) / spacing)), 1)
    step = (hi - lo) / n_int
    interior = lo + step * np.arange(1, n_int)
    return np.concatenate([[lo] * 4, interior, [hi] * 4])


def design_matrix(knots: np.ndarray, x: np.ndarray) -> np.ndarray:
    """(len(x), n_basis) cubic B-spline values; x inside [knots[0], knots[-1]] (the right end included)."""
    lo, hi = knots[0], knots[-1]
    x = np.asarray(x, dtype=np.float64)
    if np.any(x < lo - 1e-9) or np.any(x > hi + 1e-9):
        raise ValueError("evaluation point outside the support")
    xc = np.clip(x, lo, hi)
    xc = np.where(xc >= hi, np.nextafter(hi, lo), xc)   # scipy's base interval is half-open at the right
    return BSpline.design_matrix(xc, knots, 3).toarray()


@dataclass(frozen=True)
class Basis:
    """The template basis of one span: knots, visibility at τ = 0, gauge index and the node-shifted,
    window-averaged design tensor Bmat (n_nodes × W × J) with node index `node0` = the τ = 0 node."""
    span: Span
    knots: np.ndarray
    n_basis: int
    visible: np.ndarray          # indices visible at zero shift
    invisible: np.ndarray        # shift-only indices (removed in reduced models)
    gauge: int
    nodes_ms: np.ndarray
    node0: int
    Bmat: np.ndarray             # (n_nodes, W, J)

    @property
    def W(self) -> int:
        return self.span.n_windows

    @property
    def support_centres_ms(self) -> np.ndarray:
        return 0.5 * (self.knots[:self.n_basis] + self.knots[4:self.n_basis + 4])

    def free_indices(self, positive: bool) -> np.ndarray:
        """Template indices carried in the parameter vector: visible minus gauge (+ the shift-only ones in
        positive-spread / constrained-positive models)."""
        vis = [j for j in self.visible if j != self.gauge]
        return np.array(vis + (list(self.invisible) if positive else []), dtype=np.int64)

    def window_template(self, c: np.ndarray, tau_ms: float) -> np.ndarray:
        """(W,) window means of T(t − τ) at an arbitrary shift (used by the generators, §7.2)."""
        t = (self.span.sample_times_ms - tau_ms).ravel()
        vals = design_matrix(self.knots, t) @ c
        return vals.reshape(self.span.sample_times_ms.shape).mean(axis=1)

    def eval_template(self, c: np.ndarray, t_ms: np.ndarray, clamp: bool = False) -> np.ndarray:
        """T(t) at sample times; `clamp` continues the template beyond its support by the endpoint values
        (the O1 convention of §7.3)."""
        t = np.asarray(t_ms, dtype=np.float64)
        if clamp:
            t = np.clip(t, self.knots[0], self.knots[-1])
        return design_matrix(self.knots, t) @ c

    def m_vis(self, c: np.ndarray) -> float:
        return float(np.mean(self.Bmat[self.node0] @ c))


@lru_cache(maxsize=None)
def _basis_cached(span_name: str, n_nodes: int) -> Basis:
    from data import span as make_span
    sp = make_span(span_name)
    lo, hi = sp.support_ms
    knots = spline_knots(lo, hi)
    J = knots.size - 4
    vlo, vhi = sp.visible_range_ms
    starts, ends = knots[:J], knots[4:J + 4]
    visible = np.array([j for j in range(J) if starts[j] < vhi and ends[j] > vlo], dtype=np.int64)
    invisible = np.array([j for j in range(J) if j not in set(visible.tolist())], dtype=np.int64)
    centres = 0.5 * (starts + ends)
    cand = sorted(visible.tolist(), key=lambda j: (abs(centres[j] - GAUGE_CENTRE_MS), centres[j]))
    gauge = int(cand[0])
    nodes = tau_nodes_ms(n_nodes)
    node0 = int(np.argmin(np.abs(nodes)))
    assert abs(nodes[node0]) < 1e-12
    st = sp.sample_times_ms
    Bmat = np.empty((n_nodes, st.shape[0], J))
    for i, tau in enumerate(nodes):
        D = design_matrix(knots, (st - tau).ravel())
        Bmat[i] = D.reshape(st.shape[0], st.shape[1], J).mean(axis=1)
    return Basis(sp, knots, J, visible, invisible, gauge, nodes, node0, Bmat)


def basis(span_name: str, n_nodes: int = N_TAU_NODES) -> Basis:
    return _basis_cached(span_name, n_nodes)


# ----------------------------------------------------------------------------------------------
# quadrature
# ----------------------------------------------------------------------------------------------
def gh_nodes(n: int = N_G_NODES):
    """Gauss–Hermite nodes for a standard normal: z_m = √2 x_m, log weights log(w_m/√π)."""
    x, w = np.polynomial.hermite.hermgauss(n)
    return np.sqrt(2.0) * x, np.log(w / np.sqrt(np.pi))


def truncnorm_node_weights(nodes_ms: np.ndarray, s_tau_ms: float) -> np.ndarray:
    z = -0.5 * (nodes_ms / s_tau_ms) ** 2
    z -= z.max()
    w = np.exp(z)
    return w / w.sum()


def realised_sd_ms(s_tau_ms: float, n_nodes: int = N_TAU_NODES) -> float:
    nodes = tau_nodes_ms(n_nodes)
    w = truncnorm_node_weights(nodes, s_tau_ms)
    return float(np.sqrt(np.sum(w * nodes ** 2)))


def truncated_parent_sd_ms(s_tau_ms: float, trunc: float = TAU_TRUNC_MS) -> float:
    """SD of N(0, s²) truncated to ±trunc (the continuous 'realised' SD reported beside the parent, §4)."""
    from scipy.stats import truncnorm
    a = trunc / s_tau_ms
    return float(truncnorm.std(-a, a, loc=0.0, scale=s_tau_ms))


# ----------------------------------------------------------------------------------------------
# model specifications and parameter packing
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelSpec:
    family: str                 # "G" | "B"
    tau_free: bool              # θ_τ in the vector (positive-spread candidate)
    tau_fixed_ms: float         # when not free: 0 = REDUCED model; > 0 = constrained profile fit
    scale_free: bool
    span_name: str
    n_tau_nodes: int = N_TAU_NODES
    n_g_nodes: int = N_G_NODES
    adaptive_g: bool = True     # posterior-centred scale nodes (S2 repair); False = the prior-centred rule

    @property
    def positive(self) -> bool:
        """Carries the 31 τ nodes and the shift-only coefficients."""
        return self.tau_free or self.tau_fixed_ms > 0.0

    @property
    def name(self) -> str:
        if self.tau_free:
            base = "3+" if self.scale_free else "1+"
        elif self.tau_fixed_ms > 0.0:
            base = f"{'3' if self.scale_free else '1'}@{self.tau_fixed_ms:g}"
        else:
            base = "2" if self.scale_free else "0"
        return self.family + base

    def basis(self) -> Basis:
        return basis(self.span_name, self.n_tau_nodes if self.positive else 1)

    def layout(self) -> dict:
        b = self.basis()
        free = b.free_indices(self.positive)
        idx, pos = {}, 0
        idx["alpha"] = slice(pos, pos + N_LEVELS - 1); pos += N_LEVELS - 1
        idx["gamma"] = slice(pos, pos + free.size); pos += free.size
        if self.family == "B":
            idx["logkappa"] = pos; pos += 1
            idx["x0"] = pos; pos += 1
        if self.tau_free:
            idx["theta_tau"] = pos; pos += 1
        if self.scale_free:
            idx["s_g"] = pos; pos += 1
        return dict(index=idx, n_params=pos, gamma_indices=free)

    @property
    def n_params(self) -> int:
        return self.layout()["n_params"]

    def bounds(self):
        lay = self.layout()
        lb = np.full(lay["n_params"], -np.inf)
        ub = np.full(lay["n_params"], np.inf)
        lb[lay["index"]["gamma"]] = GAMMA_MIN
        if self.family == "B":
            ub[lay["index"]["logkappa"]] = np.log(KAPPA_MAX)
        if self.tau_free:
            lb[lay["index"]["theta_tau"]] = S_TAU_MIN_MS / TIME_SCALE
            ub[lay["index"]["theta_tau"]] = S_TAU_MAX_MS / TIME_SCALE
        if self.scale_free:
            lb[lay["index"]["s_g"]] = 0.0
            ub[lay["index"]["s_g"]] = S_G_MAX
        return lb, ub

    def param_names(self) -> list:
        lay = self.layout()
        names = [f"alpha{k}" for k in range(1, N_LEVELS)] + [f"gamma{j}" for j in lay["gamma_indices"]]
        if self.family == "B":
            names += ["logkappa", "x0"]
        if self.tau_free:
            names += ["theta_tau"]
        if self.scale_free:
            names += ["s_g"]
        return names

    def reduced(self) -> "ModelSpec":
        """The corresponding exact-zero model (G0 for G1+, G2 for G3+, …; itself if already reduced)."""
        return ModelSpec(self.family, False, 0.0, self.scale_free, self.span_name, self.n_tau_nodes, self.n_g_nodes,
                         self.adaptive_g)

    def constrained(self, s_tau_ms: float) -> "ModelSpec":
        """The profile model at a fixed spread (the reduced model at 0)."""
        if s_tau_ms <= 0.0:
            return self.reduced()
        return ModelSpec(self.family, False, float(s_tau_ms), self.scale_free, self.span_name,
                         self.n_tau_nodes, self.n_g_nodes, self.adaptive_g)


def spec(name: str, span_name: str = "primary", n_tau_nodes: int = N_TAU_NODES, n_g_nodes: int = N_G_NODES,
         adaptive_g: bool = True) -> ModelSpec:
    """ModelSpec from a model name: G0 G1+ G2 G3+ B0 B1+ B2 B3+ (the selected names G1/G3/B1/B3 are built from
    their two candidates by fit.py, not here)."""
    fam, rest = name[0], name[1:]
    if fam not in FAMILIES or rest not in ("0", "1+", "2", "3+"):
        raise KeyError(name)
    tau_free = rest.endswith("+")
    scale_free = rest[0] in ("2", "3")
    return ModelSpec(fam, tau_free, 0.0, scale_free, span_name, n_tau_nodes, n_g_nodes, adaptive_g)


@dataclass
class Params:
    """Unpacked natural parameters of one model at one parameter vector."""
    a: np.ndarray                # (6,) level amplitudes, a[0] = 0
    c: np.ndarray                # (J,) template coefficients (invisible = 0 in reduced models)
    c_tilde: np.ndarray          # c / m_vis
    s_tau_ms: float
    s_g: float
    kappa: float | None = None
    x0: float | None = None
    A: np.ndarray | None = None  # (6,) occupancy, A[0] = 0
    clipped: np.ndarray | None = None  # levels at the A_MIN floor
    extra: dict = field(default_factory=dict)


def softplus(x):
    return np.logaddexp(0.0, x)


def softplus_inv(y):
    y = np.asarray(y, dtype=np.float64)
    return np.where(y > 30.0, y, np.log(np.expm1(np.maximum(y, 1e-300))))


def unpack(sp: ModelSpec, theta: np.ndarray) -> Params:
    """numpy unpacking (reporting, generators, reference implementation)."""
    lay = sp.layout()
    idx = lay["index"]
    b = sp.basis()
    theta = np.asarray(theta, dtype=np.float64)
    a = np.concatenate([[0.0], softplus(theta[idx["alpha"]])])
    gamma = np.full(b.n_basis, -np.inf)
    gamma[lay["gamma_indices"]] = theta[idx["gamma"]]
    gamma[b.gauge] = 0.0
    c = np.where(np.isfinite(gamma), softplus(gamma), 0.0)
    mv = b.m_vis(c)
    s_tau = TIME_SCALE * float(theta[idx["theta_tau"]]) if sp.tau_free else sp.tau_fixed_ms
    s_g = float(theta[idx["s_g"]]) if sp.scale_free else 0.0
    P = Params(a, c, c / mv, s_tau, s_g)
    if sp.family == "B":
        P.kappa = float(np.exp(theta[idx["logkappa"]]))
        P.x0 = float(theta[idx["x0"]])
        k = np.arange(1, N_LEVELS, dtype=np.float64)
        lg = 1.0 / (1.0 + np.exp(-P.kappa * (k - P.x0)))
        P.A = np.concatenate([[0.0], np.maximum(A_MIN, lg)])
        P.clipped = np.where(lg < A_MIN)[0] + 1
    return P


def pack(sp: ModelSpec, alpha: np.ndarray, gamma_full: np.ndarray, logkappa: float = 0.0, x0: float = 2.5,
         s_tau_ms: float = 20.0, s_g: float = 0.0) -> np.ndarray:
    """Parameter vector from natural starting values; `gamma_full` (J,) is read at the free indices only."""
    lay = sp.layout()
    idx = lay["index"]
    th = np.zeros(lay["n_params"])
    th[idx["alpha"]] = alpha
    th[idx["gamma"]] = np.asarray(gamma_full)[lay["gamma_indices"]]
    if sp.family == "B":
        th[idx["logkappa"]] = logkappa
        th[idx["x0"]] = x0
    if sp.tau_free:
        th[idx["theta_tau"]] = s_tau_ms / TIME_SCALE
    if sp.scale_free:
        th[idx["s_g"]] = s_g
    return th


# ----------------------------------------------------------------------------------------------
# the JAX likelihood
# ----------------------------------------------------------------------------------------------
def _constants(sp: ModelSpec):
    b = sp.basis()
    lay = sp.layout()
    z, logw_g = gh_nodes(sp.n_g_nodes)
    x, w = np.polynomial.hermite.hermgauss(sp.n_g_nodes)
    gfree = lay["gamma_indices"]
    # gamma scatter: free -> their index, gauge -> 0, the rest (invisible in reduced models) -> c = 0
    return dict(
        Bmat=jnp.asarray(b.Bmat), node0=b.node0, nodes=jnp.asarray(b.nodes_ms), J=b.n_basis, gauge=b.gauge,
        gfree=jnp.asarray(gfree), has_invisible_zero=(not sp.positive),
        zero_mask=jnp.asarray(np.isin(np.arange(b.n_basis), np.concatenate([gfree, [b.gauge]]))),
        z=jnp.asarray(z), logw_g=jnp.asarray(logw_g), gh_x=jnp.asarray(x), gh_logw=jnp.asarray(np.log(w)),
        idx=lay["index"], W=b.W,
    )


def _adaptive_log_scale_integral(A, B, s_g, gh_x, gh_logw, xp=jnp, moments=False):
    """log ∫ LogNormal(g; −s²/2, s²) exp(A g − ½ B g²) dg by adaptive Gauss–Hermite in u = log g, elementwise over
    the arrays A = m P (n × N_tau) and B = m² vv (n × N_tau). Works with jnp (model) and np (dense reference).
    With `moments`, also the posterior moments E[g | ·], E[g² | ·] under the same nodes (the EM M-step of §5)."""
    s2 = s_g * s_g + S_G_EPS
    s = xp.sqrt(s2)
    mu_p = -0.5 * s_g * s_g
    tiny = 1e-30
    has_peak = (A > 0.0) & (B > tiny)
    Bsafe = xp.where(B > tiny, B, 1.0)                          # safe denominators: catch trials have A = B = 0
    gstar = xp.where(has_peak, A / Bsafe, 1.0)
    u_star = xp.log(gstar)
    prec_l = xp.where(has_peak, Bsafe * gstar * gstar, 0.0)      # likelihood curvature in u at its peak
    u = xp.where(has_peak, (mu_p / s2 + u_star * prec_l) / (1.0 / s2 + prec_l), mu_p)
    # the mode lies between the prior mean and the likelihood peak (A > 0), or below the prior mean (A ≤ 0)
    lo = xp.where(has_peak, xp.minimum(mu_p, u_star) - 0.5, mu_p - MODE_CLIP_SD * s - 0.5)
    hi = xp.where(has_peak, xp.maximum(mu_p, u_star) + 0.5, mu_p + 0.5)
    for _ in range(NEWTON_STEPS):
        e = xp.exp(u)
        h1 = -(u - mu_p) / s2 + A * e - B * e * e
        h2 = -1.0 / s2 + A * e - 2.0 * B * e * e
        h2 = xp.minimum(h2, -1.0 / s2)                            # safeguard: at least the prior curvature
        u = xp.clip(u - h1 / h2, lo, hi)
    e = xp.exp(u)
    curv = -(-1.0 / s2 + A * e - 2.0 * B * e * e)
    curv = xp.maximum(curv, 0.1 / s2)
    sigma_q = 1.0 / xp.sqrt(curv)
    um = u[..., None] + np.sqrt(2.0) * sigma_q[..., None] * gh_x
    em = xp.exp(um)
    h = -(um - mu_p) ** 2 / (2.0 * s2) + A[..., None] * em - 0.5 * B[..., None] * em * em
    terms = gh_logw + h + gh_x ** 2
    if xp is jnp:
        lse = logsumexp(terms, axis=-1)
    else:
        lse = np.logaddexp.reduce(terms, axis=-1)
    out = lse + xp.log(sigma_q / s) - 0.5 * np.log(np.pi)
    if not moments:
        return out
    w = xp.exp(terms - lse[..., None])
    return out, xp.sum(w * em, axis=-1), xp.sum(w * em * em, axis=-1)


def _core(theta, U, k, Linv, sp: ModelSpec, C: dict, moments: bool = False):
    """The computation shared by the per-trial log-likelihood and the EM E-step: the unwhitened window templates
    Tt (N_tau, W), the latency log-weights, the per-trial response amplitude m (n,), the per-(trial, node) scale
    integrals node_terms (n, N_tau), ‖u‖² and, for B, the occupancy log-weights per trial; with `moments` also the
    posterior scale moments Eg, Eg2 (n, N_tau) under the same quadrature (ones when g ≡ 1)."""
    idx = C["idx"]
    alpha = theta[idx["alpha"]]
    a = jnp.concatenate([jnp.zeros(1), jax.nn.softplus(alpha)])                  # (6,)
    gamma = jnp.zeros(C["J"]).at[C["gfree"]].set(theta[idx["gamma"]])
    c = jnp.where(C["zero_mask"], jax.nn.softplus(gamma), 0.0)                   # gauge: softplus(0) = ln 2
    Tw = jnp.einsum("nwj,j->nw", C["Bmat"], c)                                   # (N_tau, W)
    m_vis = jnp.mean(Tw[C["node0"]])
    Tt = Tw / m_vis
    V = Tt @ Linv.T                                                              # (N_tau, W) whitened templates
    P = U @ V.T                                                                  # (n, N_tau)
    vv = jnp.sum(V * V, axis=1)                                                  # (N_tau,)
    uu = jnp.sum(U * U, axis=1)                                                  # (n,)
    # latency weights
    if sp.tau_free:
        s_tau = theta[idx["theta_tau"]] * TIME_SCALE
    else:
        s_tau = sp.tau_fixed_ms
    if sp.positive:
        logw_tau = jax.nn.log_softmax(-0.5 * (C["nodes"] / s_tau) ** 2)
    else:
        logw_tau = jnp.zeros(1)
    out = dict(uu=uu, logw_tau=logw_tau, Tt=Tt)
    if sp.family == "G":
        m = a[k]                                                                 # (n,)
    else:
        kap = jnp.exp(theta[idx["logkappa"]])
        x0 = theta[idx["x0"]]
        lev = jnp.arange(1, N_LEVELS, dtype=jnp.float64)
        u = kap * (lev - x0)
        sig = jax.nn.sigmoid(u)
        floored = sig < A_MIN
        A = jnp.concatenate([jnp.zeros(1), jnp.where(floored, A_MIN, sig)])
        # log A and log(1 − A) in the saturation-safe softplus form (sigmoid(u) rounds to exactly 1 for u > 37,
        # where log1p(−A) is −inf and its gradient NaN); the floor branch is constant with zero derivative
        logA = jnp.concatenate([jnp.full(1, -np.inf), jnp.where(floored, jnp.log(A_MIN), -jax.nn.softplus(-u))])
        log1mA = jnp.concatenate([jnp.zeros(1), jnp.where(floored, jnp.log(1.0 - A_MIN), -jax.nn.softplus(u))])
        mH = jnp.concatenate([jnp.zeros(1), a[1:] / A[1:]])
        m = mH[k]
        out.update(logA_i=logA[k], log1mA_i=log1mA[k])
    out["m"] = m
    Am = m[:, None] * P
    Bm = (m * m)[:, None] * vv[None, :]
    # the scale integral per trial and latency node
    if not sp.scale_free:
        node_terms = Am - 0.5 * Bm                                               # g ≡ 1 exactly, (n, N_tau)
        if moments:
            out["Eg"] = jnp.ones_like(node_terms)
            out["Eg2"] = jnp.ones_like(node_terms)
    elif sp.adaptive_g:
        s_g = theta[idx["s_g"]]
        if moments:
            node_terms, out["Eg"], out["Eg2"] = _adaptive_log_scale_integral(Am, Bm, s_g, C["gh_x"], C["gh_logw"],
                                                                             moments=True)
        else:
            node_terms = _adaptive_log_scale_integral(Am, Bm, s_g, C["gh_x"], C["gh_logw"])
    else:
        s_g = theta[idx["s_g"]]
        g = jnp.exp(-0.5 * s_g ** 2 + s_g * C["z"])                              # prior-centred nodes (N_g,)
        gm = g[None, None, :] * m[:, None, None]
        logt = C["logw_g"][None, None, :] + gm * P[:, :, None] - 0.5 * gm ** 2 * vv[None, :, None]
        node_terms = logsumexp(logt, axis=2)
        if moments:
            w = jnp.exp(logt - node_terms[..., None])
            out["Eg"] = jnp.sum(w * g, axis=-1)
            out["Eg2"] = jnp.sum(w * g * g, axis=-1)
    out["node_terms"] = node_terms
    return out


def _trial_loglik_impl(theta, U, k, Linv, logdet, sp: ModelSpec, C: dict):
    o = _core(theta, U, k, Linv, sp, C)
    lse = logsumexp(o["logw_tau"][None, :] + o["node_terms"], axis=1)            # (n,)
    base = -0.5 * C["W"] * LOG2PI - 0.5 * logdet - 0.5 * o["uu"]
    if sp.family == "G":
        return base + lse
    catch = k == 0
    logA_safe = jnp.where(catch, jnp.log(0.5), o["logA_i"])
    log1mA_safe = jnp.where(catch, jnp.log(0.5), o["log1mA_i"])
    mix = jnp.logaddexp(log1mA_safe, logA_safe + lse)
    return base + jnp.where(catch, 0.0, mix)


def _posterior_impl(theta, U, k, Linv, sp: ModelSpec, C: dict):
    """EM E-step (S2 repair 1, 24 Oct 2026): R (n, N_tau) = posterior probability of a response AT latency node τ
    (rows sum to post_high), Eg and Eg2 (n, N_tau) = posterior scale moments at each node, post_high (n,) = posterior
    probability of a response (1 on stimulus trials of the graded family, 0 on catch trials), Tt (N_tau, W) the
    unwhitened window templates and m (n,) the response amplitude — everything the Σ M-step needs."""
    o = _core(theta, U, k, Linv, sp, C, moments=True)
    lt = o["logw_tau"][None, :] + o["node_terms"]
    lse = logsumexp(lt, axis=1)
    r = jnp.exp(lt - lse[:, None])
    catch = k == 0
    if sp.family == "G":
        post_high = jnp.where(catch, 0.0, 1.0)
    else:
        high = o["logA_i"] + lse
        low = o["log1mA_i"]
        post_high = jnp.where(catch, 0.0, jnp.exp(high - jnp.logaddexp(low, high)))
    return r * post_high[:, None], o["Eg"], o["Eg2"], post_high, o["Tt"], o["m"]


@lru_cache(maxsize=None)
def functions(sp: ModelSpec):
    """(value_and_grad of the negative training log-likelihood, per-trial log-likelihood, EM posterior), all jitted.
    Signatures: f(theta, U, k, mask, Linv, logdet), g(theta, U, k, Linv, logdet), p(theta, U, k, Linv)."""
    C = _constants(sp)

    def trial_loglik(theta, U, k, Linv, logdet):
        return _trial_loglik_impl(theta, U, k, Linv, logdet, sp, C)

    def objective(theta, U, k, mask, Linv, logdet):
        return -jnp.sum(mask * trial_loglik(theta, U, k, Linv, logdet))

    def posterior(theta, U, k, Linv):
        return _posterior_impl(theta, U, k, Linv, sp, C)

    return jax.jit(jax.value_and_grad(objective)), jax.jit(trial_loglik), jax.jit(posterior)


def m_step_sigma(sp: ModelSpec, theta: np.ndarray, ds) -> np.ndarray:
    """The Σ M-step of the within-model maximum-likelihood noise covariance (S2 repair 1): the posterior expectation
    of the residual outer product about μ0 (the training-catch anchor, not re-estimated), averaged over the trials:
      Σ_new = (1/n) Σ_i [ r_i r_iᵀ − Σ_τ R_iτ E[g]_iτ m_i (r_i T̃_τᵀ + T̃_τ r_iᵀ) + Σ_τ R_iτ E[g²]_iτ m_i² T̃_τ T̃_τᵀ ],
    r_i = y_i − μ0; the low branch (and every catch trial) contributes r_i r_iᵀ only. Symmetrised, with a ridge of
    1e-10 of the mean eigenvalue."""
    _, _, post = functions(sp)
    R, Eg, Eg2, ph, Tt, m = (np.asarray(v, dtype=np.float64) for v in
                             post(jnp.asarray(theta, dtype=jnp.float64), jnp.asarray(ds.U), jnp.asarray(ds.k),
                                  jnp.asarray(ds.wh.Linv)))
    r0 = np.asarray(ds.Y, dtype=np.float64) - ds.wh.mu0
    n, W = r0.shape
    S0 = r0.T @ r0
    Mx = R * Eg * m[:, None]
    C1 = r0.T @ (Mx @ Tt)
    wtau = np.sum(R * Eg2 * (m * m)[:, None], axis=0)
    Q = Tt.T @ (wtau[:, None] * Tt)
    Sigma = (S0 - C1 - C1.T + Q) / n
    Sigma = 0.5 * (Sigma + Sigma.T)
    return Sigma + 1e-10 * (np.trace(Sigma) / W) * np.eye(W)


def padded(U: np.ndarray, k: np.ndarray, multiple: int = PAD_MULTIPLE):
    """Pad trials to a multiple of `multiple` (cached compile shapes, §8) with zero-weight catch rows."""
    n = U.shape[0]
    n_pad = int(np.ceil(n / multiple) * multiple)
    Up = np.zeros((n_pad, U.shape[1]))
    Up[:n] = U
    kp = np.zeros(n_pad, dtype=np.int64)
    kp[:n] = k
    mask = np.zeros(n_pad)
    mask[:n] = 1.0
    return jnp.asarray(Up), jnp.asarray(kp), jnp.asarray(mask)


class Objective:
    """Callable for scipy: f(theta) -> (negative MEAN log-likelihood per training trial, gradient) as float64
    numpy, on one Dataset. The optimiser works on the per-trial mean (S1 choice, declared in fit.py: on the
    summed objective, ≈ 1.1e4 nat for 750 trials, the §5 gradient threshold 1e-5 lies at the float64 resolution
    floor and converged optima fail it); `n_eff` converts back to total nat (`total_loglik`)."""

    def __init__(self, sp: ModelSpec, ds):
        self.spec = sp
        self.vg, self.per_trial, self.posterior = functions(sp)
        self.U, self.k, self.mask = padded(ds.U, ds.k)
        self.n_eff = int(ds.k.size)
        self.Linv = jnp.asarray(ds.wh.Linv)
        self.logdet = float(ds.wh.logdet)
        self.n_calls = 0

    def __call__(self, theta):
        self.n_calls += 1
        v, g = self.vg(jnp.asarray(theta, dtype=jnp.float64), self.U, self.k, self.mask, self.Linv, self.logdet)
        return float(v) / self.n_eff, np.asarray(g, dtype=np.float64) / self.n_eff

    def total_loglik(self, theta) -> float:
        v, _ = self.vg(jnp.asarray(theta, dtype=jnp.float64), self.U, self.k, self.mask, self.Linv, self.logdet)
        return -float(v)

    def trial_loglik(self, theta, ds=None):
        """Per-trial log-likelihood on `ds` (default: the fitted dataset) — the held-out score of §5."""
        if ds is None:
            U, k = self.U[: int(self.mask.sum())], self.k[: int(self.mask.sum())]
            return np.asarray(self.per_trial(jnp.asarray(theta), U, k, self.Linv, self.logdet))
        return np.asarray(self.per_trial(jnp.asarray(theta), jnp.asarray(ds.U), jnp.asarray(ds.k),
                                         jnp.asarray(ds.wh.Linv), float(ds.wh.logdet)))


# ----------------------------------------------------------------------------------------------
# dense reference implementation (tests, §5 "Correctness")
# ----------------------------------------------------------------------------------------------
def log_scale_integral_dense(A: float, B: float, s_g: float, n_u: int = 40001, half_width_sd: float = 12.0) -> float:
    """Reference: log ∫ LogNormal(g; −s²/2, s²) exp(A g − ½ B g²) dg by a fine trapezoid in u = log g over a
    window that covers both the prior and the likelihood peak."""
    if s_g <= 0.0:
        return float(A - 0.5 * B)
    mu_p = -0.5 * s_g ** 2
    s_w = max(s_g, 1e-3)
    lo, hi = mu_p - half_width_sd * s_w, mu_p + half_width_sd * s_w
    if A > 0 and B > 0:
        u_star = np.log(A / B)
        lo, hi = min(lo, u_star - 12.0 * s_w - 1.0), max(hi, u_star + 12.0 * s_w + 1.0)
    u = np.linspace(lo, hi, n_u)
    h = -(u - mu_p) ** 2 / (2 * s_g ** 2) + A * np.exp(u) - 0.5 * B * np.exp(2 * u)
    du = u[1] - u[0]
    hm = h.max()
    return float(hm + np.log(np.trapezoid(np.exp(h - hm), dx=du)) - np.log(s_g * np.sqrt(2 * np.pi)))


def dense_trial_loglik(sp: ModelSpec, theta: np.ndarray, Y: np.ndarray, k: np.ndarray, mu0: np.ndarray,
                       Sigma: np.ndarray, exact_scale: bool = False) -> np.ndarray:
    """Direct mixture over the τ nodes with scipy's multivariate normal, no whitening. The scale integral uses
    the same rule as the model (adaptive nodes in numpy, or the prior-centred nodes), or, with
    `exact_scale`, the fine trapezoid reference (then the comparison tests the quadrature itself)."""
    P = unpack(sp, theta)
    b = sp.basis()
    nodes = b.nodes_ms if sp.positive else np.zeros(1)
    w_tau = truncnorm_node_weights(nodes, P.s_tau_ms) if sp.positive else np.ones(1)
    z, logw_g = gh_nodes(sp.n_g_nodes)
    x, w = np.polynomial.hermite.hermgauss(sp.n_g_nodes)
    g_prior = np.exp(-0.5 * P.s_g ** 2 + P.s_g * z)
    L = np.linalg.cholesky(Sigma)
    Linv = np.linalg.inv(L)
    out = np.empty(Y.shape[0])
    for i in range(Y.shape[0]):
        ki = int(k[i])
        if sp.family == "G":
            m = P.a[ki]
        else:
            m = 0.0 if ki == 0 else P.a[ki] / P.A[ki]
        comps = []
        for n_, wt in zip(range(nodes.size), w_tau):
            Tt = b.Bmat[n_] @ P.c_tilde
            if not sp.scale_free:
                comps.append(np.log(wt) + multivariate_normal.logpdf(Y[i], mu0 + m * Tt, Sigma))
                continue
            u_i = Linv @ (Y[i] - mu0)
            v = Linv @ Tt
            A_ = m * float(u_i @ v)
            B_ = m * m * float(v @ v)
            base_i = multivariate_normal.logpdf(Y[i], mu0, Sigma)       # −½W log 2π − ½ log|Σ| − ½‖u‖²
            if exact_scale:
                val = log_scale_integral_dense(A_, B_, P.s_g)
            elif sp.adaptive_g:
                val = float(_adaptive_log_scale_integral(np.array([[A_]]), np.array([[B_]]), P.s_g, x, np.log(w), xp=np)[0, 0])
            else:
                val = float(np.logaddexp.reduce(logw_g + g_prior * A_ - 0.5 * g_prior ** 2 * B_))
            comps.append(np.log(wt) + base_i + val)
        high = np.logaddexp.reduce(comps)
        if sp.family == "G":
            out[i] = high
        else:
            if ki == 0:
                out[i] = multivariate_normal.logpdf(Y[i], mu0, Sigma)
            else:
                low = np.log(1.0 - P.A[ki]) + multivariate_normal.logpdf(Y[i], mu0, Sigma)
                out[i] = np.logaddexp(low, np.log(P.A[ki]) + high)
    return out


def code_hash() -> str:
    """sha256 over this module and its siblings (logged with every fit, §5)."""
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("data.py", "models.py", "fit.py", "simulate.py", "decide.py"):
        p = os.path.join(here, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:12]

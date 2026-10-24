#!/usr/bin/env python3
"""jitter/fit.py — fitting of DESIGN_jitter.md rev 6 §5: starts, the L-BFGS-B driver with the acceptance rules,
the zero-boundary construction, caching of reduced fits, cross-validated scoring, the constrained (profile) fits
and the §7.1 generator fits. Stage S1 (provisional; frozen at S3).

Starts (§5), exactly four per fit, from the fold's TRAINING trials only, all at WINDOW level so that real and
synthetic data (53-window vectors, §7.2) are treated identically:
  T_A = non-negative least squares of the window-averaged visible basis (τ = 0) to the training level-5 mean
        response (level-5 window means − μ0) over the span; T_B = the same fit to that response smoothed by a
        90 ms moving average (three windows). Floor 1e-3, rescale so the gauge coefficient is softplus(0) = ln 2,
        γ = softplus⁻¹(c); coincidence of T_A and T_B is logged.
  a(k) = training level means of the span response, clipped below at 0.05; κ, x0 from a logistic regression of the
        indicator "span mean above the training catch 90th percentile" on level (k ≥ 1); separated or
        non-positive slope → κ = 1, x0 = 2.5.
  Nuisance starts: G0/B0 {T_A, T_B} × {a, a × 0.5}; G1/B1 positive {T_A, T_B} × s_τ {20, 40}; G2/B2 {T_A, T_B} ×
        s_g {0, 0.4}; G3/B3 positive T_A × {(20, 0), (40, 0.4)}, T_B × {(40, 0), (20, 0.4)}.
Acceptance (§5): CONVERGED = projected-gradient ∞-norm ≤ 1e-5 (scaled units) AND relative objective change over
the last 5 iterations ≤ 1e-9 AND finite; < 5 iterations = EARLY → one re-run from the start perturbed by
N(0, 0.1²), the pair CONVERGED only if both satisfy (i)+(iii) and agree to 1e-8 relative (better kept); iteration
cap 2,000; two retries from re-seeded perturbed starts on failure; no CONVERGED start → the model is UNAVAILABLE.
The best CONVERGED objective is selected; every start's end point and status is archived. L-BFGS-B is run with
gtol 1e-7 and ftol 1e-15 so that it polishes past the acceptance thresholds; the status is assessed from the end
point and the iteration history, never from scipy's flag. The optimiser objective is the negative MEAN
log-likelihood per training trial (S1 choice, 24 Oct 2026: on the summed objective, ≈ 1.1e4 nat on S10 fold 0, the
1e-5 gradient threshold lies at the float64 resolution floor — all four G3+/B3+ starts reached one optimum to
1e-8 relative yet three failed criterion (i) with pg 1e-5–4e-5); objectives and gradients in the acceptance rules
are per trial, archived and reported log-likelihoods are totals in nat.
Zero-boundary construction (§5): a model with s_τ free is the better of its cached REDUCED fit (G0 for G1, G2
for G3, B0 for B1, B2 for B3) and its POSITIVE-SPREAD candidate (s_τ ∈ [2, 150]); a positive fit at the 2 ms
floor is flagged and the reduced fit is the comparison.
Score (§5): out-of-fold log marginal density summed over the five folds / number of scored trials (block 21
excluded), nat per trial; the inherited fold-mean convention is reported beside it.
S1 choices to confirm at S3: window-level starts (above); the second constrained start takes the T_B nuisance
start nearest in s_τ, ties to the first listed, and s_g = 0 at the reduced (s = 0) point; a selected model with
exactly one AVAILABLE candidate is that candidate, flagged.
"""
from __future__ import annotations

import os

os.environ.setdefault("NPROC", "1")

import hashlib  # noqa: E402
import json  # noqa: E402
import time as _time  # noqa: E402
from dataclasses import asdict, dataclass, field  # noqa: E402

import numpy as np  # noqa: E402
from scipy.optimize import minimize, nnls  # noqa: E402

import data as D  # noqa: E402
import models as M  # noqa: E402

LBFGSB_OPTIONS = dict(maxiter=2000, maxcor=20, ftol=1e-15, gtol=1e-7, maxls=50)
PG_TOL = 1e-5
REL_TOL = 1e-9
HIST_ITERS = 5
EARLY_ITERS = 5
EARLY_AGREE = 1e-8
PERTURB_SD = 0.1
MAX_RETRIES = 2
AMP_FLOOR = 0.05
COEF_FLOOR = 1e-3
SMOOTH_WINDOWS = 3            # 90 ms moving average at the 30 ms window step
KAPPA_FALLBACK, X0_FALLBACK = 1.0, 2.5
FLOOR_EPS = 1e-9
FULL_MODELS = ("G0", "G1", "G2", "G3", "B0", "B1", "B2", "B3")
# S2 repairs (24 Oct 2026), declared for the S3 review:
SMEAR_SPREADS_MS = (20.0, 40.0, 80.0, 120.0)   # repair 2: template starts fitted through the basis SMEARED by the
SMEAR_S_G = 0.4                                #   start's own latency kernel (the level-5 mean is the jitter-broadened
LIFT_SPREADS_MS = (20.0, 40.0, 80.0)           #   template; a start fitted to it slides to s_tau = 0), the reduced fit
COLLAPSE_X0 = -5.0                             #   lifted at three spreads, and for B the selected G fit collapsed (A -> 1)
EM_MAX_ITER = 8                                # repair 1: Σ by maximum likelihood within each model (EM outer loop)
EM_TOL = 1e-6                                  #   relative gain in the total log-likelihood that ends the loop
RESEED_MIN_NAT = 0.05                          #   a collapsed B this far above G re-seeds G (another basin, not EM noise)


def _seed(*parts) -> int:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16)


# ----------------------------------------------------------------------------------------------
# starts
# ----------------------------------------------------------------------------------------------
@dataclass
class StartRecipe:
    template: str              # "A" | "B"
    amp_scale: float = 1.0
    s_tau_ms: float = 20.0
    s_g: float = 0.0

    @property
    def label(self) -> str:
        return f"T{self.template}|amp{self.amp_scale:g}|tau{self.s_tau_ms:g}|sg{self.s_g:g}"


def nuisance_recipes(sp: M.ModelSpec) -> list:
    """The four §5 starts of a model; constrained profile models use the G2/B2 recipe (s_τ is fixed)."""
    if sp.tau_free and sp.scale_free:
        return [StartRecipe("A", 1.0, 20.0, 0.0), StartRecipe("A", 1.0, 40.0, 0.4),
                StartRecipe("B", 1.0, 40.0, 0.0), StartRecipe("B", 1.0, 20.0, 0.4)]
    if sp.tau_free:
        return [StartRecipe("A", 1.0, 20.0, 0.0), StartRecipe("A", 1.0, 40.0, 0.0),
                StartRecipe("B", 1.0, 20.0, 0.0), StartRecipe("B", 1.0, 40.0, 0.0)]
    if sp.scale_free:
        return [StartRecipe("A", 1.0, sp.tau_fixed_ms, 0.0), StartRecipe("A", 1.0, sp.tau_fixed_ms, 0.4),
                StartRecipe("B", 1.0, sp.tau_fixed_ms, 0.0), StartRecipe("B", 1.0, sp.tau_fixed_ms, 0.4)]
    return [StartRecipe("A", 1.0, sp.tau_fixed_ms, 0.0), StartRecipe("A", 0.5, sp.tau_fixed_ms, 0.0),
            StartRecipe("B", 1.0, sp.tau_fixed_ms, 0.0), StartRecipe("B", 0.5, sp.tau_fixed_ms, 0.0)]


@dataclass
class StartInfo:
    gamma_A: np.ndarray
    gamma_B: np.ndarray
    a: np.ndarray                # (5,) clipped level amplitudes
    logkappa: float
    x0: float
    coincide: bool
    kappa_fallback: bool
    notes: list = field(default_factory=list)


def _template_gamma(b: M.Basis, response: np.ndarray, notes: list, tag: str) -> np.ndarray:
    B0 = b.Bmat[b.node0][:, b.visible]
    coef, _ = nnls(B0, np.asarray(response, dtype=np.float64))
    c = np.zeros(b.n_basis)
    c[b.visible] = coef
    c = np.maximum(c, COEF_FLOOR)
    if c[b.gauge] <= COEF_FLOOR + 1e-15:
        notes.append(f"{tag}: gauge coefficient at the floor before rescaling")
    c *= np.log(2.0) / c[b.gauge]
    return np.asarray(M.softplus_inv(c), dtype=np.float64)


def _logistic_fit(k: np.ndarray, y: np.ndarray):
    """IRLS logistic regression of y on (1, k). Returns (β0, β1, ok); ok is False under (quasi-)complete
    separation — for the ordinal level this is 'every indicator below some level is 0 and above it 1' (either
    direction), or one class empty — and when the iteration diverges."""
    y = np.asarray(y, dtype=np.float64)
    if y.sum() == 0 or y.sum() == y.size:
        return 0.0, 0.0, False
    if np.max(k[y == 0]) <= np.min(k[y == 1]) or np.min(k[y == 0]) >= np.max(k[y == 1]):
        return 0.0, 0.0, False
    X = np.column_stack([np.ones(k.size), k.astype(np.float64)])
    beta = np.zeros(2)
    for _ in range(60):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        w = p * (1.0 - p)
        if np.any(~np.isfinite(w)) or w.max() < 1e-12:
            return beta[0], beta[1], False
        H = X.T @ (X * w[:, None]) + 1e-12 * np.eye(2)
        step = np.linalg.solve(H, X.T @ (y - p))
        beta = beta + step
        if np.abs(beta).max() > 15.0:          # separation
            return beta[0], beta[1], False
        if np.abs(step).max() < 1e-8:
            return beta[0], beta[1], True
    return beta[0], beta[1], False


def start_info(sp: M.ModelSpec, ds: D.Dataset) -> StartInfo:
    """Training-only quantities for the §5 starts of model `sp` on dataset `ds`."""
    b = sp.basis()
    notes = []
    R = ds.Y - ds.wh.mu0                                             # (n, W) response about μ0
    lev5 = R[ds.k == 5].mean(axis=0) if np.any(ds.k == 5) else R[ds.k == ds.k.max()].mean(axis=0)
    gamma_A = _template_gamma(b, lev5, notes, "T_A")
    kern = np.ones(SMOOTH_WINDOWS) / SMOOTH_WINDOWS
    pad = SMOOTH_WINDOWS // 2
    sm = np.convolve(np.pad(lev5, pad, mode="edge"), kern, mode="valid")
    gamma_B = _template_gamma(b, sm, notes, "T_B")
    coincide = bool(np.allclose(gamma_A, gamma_B, atol=1e-12, rtol=0))
    if coincide:
        notes.append("T_A and T_B coincide")
    span_mean = R.mean(axis=1)
    a = np.array([max(span_mean[ds.k == k].mean() if np.any(ds.k == k) else AMP_FLOOR, AMP_FLOOR)
                  for k in range(1, D.N_LEVELS)])
    thr = np.percentile(span_mean[ds.k == 0], 90)
    sel = ds.k >= 1
    b0, b1, ok = _logistic_fit(ds.k[sel], (span_mean[sel] > thr).astype(np.float64))
    fallback = (not ok) or (not np.isfinite(b1)) or b1 <= 0.0
    if fallback:
        kappa, x0 = KAPPA_FALLBACK, X0_FALLBACK
        notes.append("kappa/x0 fallback")
    else:
        kappa, x0 = float(b1), float(-b0 / b1)
    return StartInfo(gamma_A, gamma_B, a, float(np.log(kappa)), x0, coincide, bool(fallback), notes)


def start_vectors(sp: M.ModelSpec, info: StartInfo, recipes: list | None = None):
    """[(label, θ0)] for the four §5 starts."""
    recipes = nuisance_recipes(sp) if recipes is None else recipes
    out = []
    for r in recipes:
        gamma = info.gamma_A if r.template == "A" else info.gamma_B
        alpha = M.softplus_inv(np.maximum(info.a * r.amp_scale, 1e-6))
        out.append((r.label, M.pack(sp, alpha, gamma, info.logkappa, info.x0, r.s_tau_ms, r.s_g)))
    return out


# ----------------------------------------------------------------------------------------------
# the optimiser driver
# ----------------------------------------------------------------------------------------------
def projected_gradient_inf(x, g, lb, ub, tol=1e-12):
    pg = np.array(g, dtype=np.float64)
    at_lb = x <= lb + tol
    at_ub = x >= ub - tol
    pg[at_lb & (pg > 0)] = 0.0
    pg[at_ub & (pg < 0)] = 0.0
    return float(np.max(np.abs(pg))) if pg.size else 0.0


def _run_lbfgsb(obj: M.Objective, x0: np.ndarray, lb: np.ndarray, ub: np.ndarray, options: dict) -> dict:
    hist = []

    def cb(intermediate_result):
        hist.append(float(intermediate_result.fun))

    t0 = _time.time()
    bounds = list(zip(np.where(np.isfinite(lb), lb, None), np.where(np.isfinite(ub), ub, None)))
    res = minimize(obj, np.asarray(x0, dtype=np.float64), jac=True, method="L-BFGS-B", bounds=bounds,
                   options=options, callback=cb)
    f, g = obj(res.x)
    return dict(x=np.asarray(res.x), f=float(f), grad=np.asarray(g), nit=int(res.nit), nfev=int(res.nfev),
                message=str(res.message), hist=hist, seconds=_time.time() - t0,
                pg=projected_gradient_inf(res.x, g, lb, ub))


def _assess(run: dict) -> str:
    if not (np.isfinite(run["f"]) and np.all(np.isfinite(run["x"])) and np.all(np.isfinite(run["grad"]))):
        return "NONFINITE"
    if run["nit"] < EARLY_ITERS:
        return "EARLY"
    hist = run["hist"]
    if len(hist) > HIST_ITERS:
        rel = abs(hist[-1] - hist[-1 - HIST_ITERS]) / max(1.0, abs(hist[-1]))
    else:
        rel = abs(hist[-1] - hist[0]) / max(1.0, abs(hist[-1])) if hist else np.inf
    if run["pg"] <= PG_TOL and rel <= REL_TOL:
        return "CONVERGED"
    return "NOT_CONVERGED"


def _ok_i_iii(run: dict) -> bool:
    return (np.isfinite(run["f"]) and np.all(np.isfinite(run["x"])) and np.all(np.isfinite(run["grad"]))
            and run["pg"] <= PG_TOL)


@dataclass
class StartResult:
    label: str
    status: str                  # CONVERGED | NOT_CONVERGED | NONFINITE | EARLY_PAIR_FAILED
    x: np.ndarray
    f: float                     # TOTAL negative log-likelihood (nat) at the end point of the kept attempt
    pg: float                    # projected-gradient ∞-norm of the per-trial objective, scaled units
    nit: int
    nfev: int
    seconds: float
    attempts: list               # per attempt: dict(kind, status, f, pg, nit, nfev, message)
    early: bool = False
    retries: int = 0

    @property
    def loglik(self) -> float:
        return -self.f


def run_start(obj: M.Objective, label: str, x0: np.ndarray, lb: np.ndarray, ub: np.ndarray, seed: int,
              options: dict | None = None) -> StartResult:
    """One §5 start under the acceptance rules as repaired in S2 (24 Oct 2026). Every attempt's end point is
    archived. The start's RESULT is the best end point among the attempts that satisfy (i) the projected-gradient
    threshold and (iii) finiteness; it is CONVERGED when that end point also satisfies (ii) the five-iteration
    relative-change rule, or when it was reached in fewer than five iterations (a warm start at an optimum) and the
    perturbed re-run and the retries found nothing better than it by 1e-8 relative. Retries (at most two, from the
    start perturbed by N(0, 0.1²) in scaled units) run while the start is not yet CONVERGED. The rev 6 code let a
    worse CONVERGED retry replace a better stationary end point and discarded an exact warm start whose perturbed
    re-run landed in another basin; the lifted profile warm starts were all lost that way."""
    options = dict(LBFGSB_OPTIONS) if options is None else options
    rng = np.random.default_rng(seed)
    attempts, runs = [], []
    t0 = _time.time()
    x0 = np.asarray(x0, dtype=np.float64)
    if not np.all(np.isfinite(x0)):
        raise ValueError(f"start {label} has non-finite coordinates")

    def one(x_start, kind):
        run = _run_lbfgsb(obj, x_start, lb, ub, options)
        run["status0"] = _assess(run)
        attempts.append(dict(kind=kind, status=run["status0"], f=run["f"], pg=run["pg"], nit=run["nit"],
                             nfev=run["nfev"], message=run["message"], seconds=run["seconds"]))
        runs.append(run)
        return run

    def perturbed(x):
        return np.clip(x + rng.normal(0.0, PERTURB_SD, size=x.shape), lb, ub)

    def best_stationary():
        s = [r for r in runs if _ok_i_iii(r)]
        return min(s, key=lambda r: r["f"]) if s else None

    def accepted(best):
        """CONVERGED: (ii) holds at the best stationary point, or nothing else found a better objective."""
        if best is None:
            return False
        if best["status0"] == "CONVERGED":
            return True
        others = [r for r in runs if r is not best]
        tol = EARLY_AGREE * max(1.0, abs(best["f"]))
        return bool(others) and all((not np.isfinite(r["f"])) or r["f"] >= best["f"] - tol for r in others)

    first = one(x0, "start")
    early = first["status0"] == "EARLY"
    if early:
        one(perturbed(x0), "start/early-rerun")
    retries = 0
    while not accepted(best_stationary()) and retries < MAX_RETRIES:
        retries += 1
        one(perturbed(x0), f"retry{retries}")
    best = best_stationary()
    if best is not None:
        status = "CONVERGED" if accepted(best) else "NOT_CONVERGED"
    else:
        finite = [r for r in runs if np.isfinite(r["f"]) and np.all(np.isfinite(r["x"]))]
        best = min(finite, key=lambda r: r["f"]) if finite else runs[0]
        status = "NOT_CONVERGED" if finite else "NONFINITE"
    n_eff = getattr(obj, "n_eff", 1)
    for a in attempts:
        a["f_total"] = a["f"] * n_eff
    return StartResult(label, status, best["x"], best["f"] * n_eff, best["pg"], best["nit"],
                       sum(a["nfev"] for a in attempts), _time.time() - t0, attempts, early, retries)


# ----------------------------------------------------------------------------------------------
# one model on one dataset
# ----------------------------------------------------------------------------------------------
@dataclass
class FitResult:
    model: str                   # spec name (G0, G3+, G3@40, …)
    ident: str
    status: str                  # AVAILABLE | UNAVAILABLE
    theta: np.ndarray
    loglik: float
    starts: list                 # StartResult
    n_converged: int
    seconds: float
    code_hash: str
    bounds_hit: list
    clipped: list
    notes: list
    selection: str = ""          # REDUCED | POSITIVE for selected models, "" for candidates
    flags: list = field(default_factory=list)
    candidates: dict = field(default_factory=dict)   # selected models: {"reduced": loglik, "positive": loglik}
    wh: object = None            # the model's own whitening (μ0, Σ) after the EM loop (S2 repair 1); None = the data's
    em_iterations: int = 0
    em_trace: list = field(default_factory=list)     # total log-likelihood after the multi-start fit and each EM step

    @property
    def available(self) -> bool:
        return self.status == "AVAILABLE"

    def to_json(self) -> dict:
        d = dict(model=self.model, ident=self.ident, status=self.status,
                 theta=None if self.theta is None else [float(v) for v in self.theta],
                 loglik=float(self.loglik), n_converged=self.n_converged, seconds=self.seconds,
                 code_hash=self.code_hash, bounds_hit=self.bounds_hit, clipped=self.clipped, notes=self.notes,
                 selection=self.selection, flags=self.flags, candidates=self.candidates,
                 em_iterations=self.em_iterations, em_trace=[float(v) for v in self.em_trace],
                 sigma_logdet=None if self.wh is None else float(self.wh.logdet),
                 starts=[dict(label=s.label, status=s.status, f=s.f, pg=s.pg, nit=s.nit, nfev=s.nfev,
                              seconds=s.seconds, early=s.early, retries=s.retries, attempts=s.attempts,
                              x=[float(v) for v in s.x]) for s in self.starts])
        return d

    @staticmethod
    def from_json(d: dict) -> "FitResult":
        """The whitening is not serialised: a result read back scores held-out data under the data's whitening."""
        starts = [StartResult(s["label"], s["status"], np.asarray(s["x"]), s["f"], s["pg"], s["nit"], s["nfev"],
                              s["seconds"], s["attempts"], s["early"], s["retries"]) for s in d["starts"]]
        return FitResult(d["model"], d["ident"], d["status"], None if d["theta"] is None else np.asarray(d["theta"]),
                         d["loglik"], starts, d["n_converged"], d["seconds"], d["code_hash"], d["bounds_hit"],
                         d["clipped"], d["notes"], d.get("selection", ""), d.get("flags", []), d.get("candidates", {}),
                         None, d.get("em_iterations", 0), d.get("em_trace", []))


def _bounds_hit(sp: M.ModelSpec, theta: np.ndarray) -> list:
    lb, ub = sp.bounds()
    names = sp.param_names()
    out = []
    for i, nm in enumerate(names):
        if np.isfinite(lb[i]) and theta[i] <= lb[i] + FLOOR_EPS:
            out.append(f"{nm}@lower")
        if np.isfinite(ub[i]) and theta[i] >= ub[i] - FLOOR_EPS:
            out.append(f"{nm}@upper")
    return out


def fit_model(sp: M.ModelSpec, ds: D.Dataset, starts: list | None = None, info: StartInfo | None = None,
              options: dict | None = None) -> FitResult:
    """Multi-start fit of one candidate model (§5). `starts` = [(label, θ0)] overrides the four recipes."""
    t0 = _time.time()
    info = start_info(sp, ds) if info is None else info
    starts = start_vectors(sp, info) if starts is None else starts
    obj = M.Objective(sp, ds)
    lb, ub = sp.bounds()
    results = []
    for i, (label, x0) in enumerate(starts):
        results.append(run_start(obj, label, x0, lb, ub, _seed(ds.ident, sp.name, label, i), options))
    conv = [r for r in results if r.status == "CONVERGED"]
    notes = list(info.notes)
    if conv:
        best = min(conv, key=lambda r: (r.f, r.label))
        P = M.unpack(sp, best.x)
        clipped = [] if P.clipped is None else [int(v) for v in P.clipped]
        return FitResult(sp.name, ds.ident, "AVAILABLE", best.x, -best.f, results, len(conv), _time.time() - t0,
                         M.code_hash(), _bounds_hit(sp, best.x), clipped, notes)
    return FitResult(sp.name, ds.ident, "UNAVAILABLE", None, -np.inf, results, 0, _time.time() - t0,
                     M.code_hash(), [], [], notes + ["no CONVERGED start"])


# ----------------------------------------------------------------------------------------------
# caching and the zero-boundary construction
# ----------------------------------------------------------------------------------------------
class FitCache:
    """Fits keyed by (dataset identity, model name, start recipe). Reduced fits are computed once per
    participant, fold and data identity and reused as models, boundary candidates, profile points and c₀
    components (§5). Optional on-disk JSON store. `em` = Σ by maximum likelihood within each model (the repaired
    default); False = Σ fixed at the dataset's whitening (the rev 6 construction, kept for the S2 comparisons)."""

    def __init__(self, directory: str | None = None, em: bool = True):
        self.mem = {}
        self.dir = directory
        self.em = em
        if directory:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def key(ds: D.Dataset, sp: M.ModelSpec, recipe: str = "std") -> str:
        quad = f"t{sp.n_tau_nodes}g{sp.n_g_nodes}{'a' if sp.adaptive_g else 'p'}"
        return f"{ds.ident}|{sp.name}|{quad}|{recipe}"

    def _path(self, key: str) -> str:
        return os.path.join(self.dir, hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")

    def get(self, key: str):
        if key in self.mem:
            return self.mem[key]
        if self.dir and os.path.exists(self._path(key)):
            with open(self._path(key)) as f:
                r = FitResult.from_json(json.load(f))
            self.mem[key] = r
            return r
        return None

    def put(self, key: str, r: FitResult):
        self.mem[key] = r
        if self.dir:
            with open(self._path(key), "w") as f:
                json.dump(r.to_json(), f)

    def fit(self, sp: M.ModelSpec, ds: D.Dataset, info: StartInfo | None = None, recipe: str = "std",
            starts: list | None = None, warm: list | None = None) -> FitResult:
        key = self.key(ds, sp, recipe)
        r = self.get(key)
        if r is None:
            r = em_fit(sp, ds, starts, info, em=self.em, warm=warm)
            self.put(key, r)
        return r


def select(name: str, reduced: FitResult, positive: FitResult, sp_pos: M.ModelSpec) -> FitResult:
    """The zero-boundary construction: the better of the REDUCED and the POSITIVE-SPREAD candidate."""
    flags = []
    at_floor = False
    if positive.available:
        lay = sp_pos.layout()["index"]
        at_floor = positive.theta[lay["theta_tau"]] <= M.S_TAU_MIN_MS / M.TIME_SCALE + FLOOR_EPS
        if at_floor:
            flags.append("positive_at_floor")
    cands = dict(reduced=float(reduced.loglik), positive=float(positive.loglik))
    if not reduced.available and not positive.available:
        return FitResult(name, reduced.ident, "UNAVAILABLE", None, -np.inf, [], 0, 0.0, M.code_hash(), [], [],
                         ["both candidates UNAVAILABLE"], "", flags, cands)
    if positive.available and (not at_floor or not reduced.available) and \
            (not reduced.available or positive.loglik > reduced.loglik):
        src, sel = positive, "POSITIVE"
        if not reduced.available:
            flags.append("reduced_unavailable")
    else:
        src, sel = reduced, "REDUCED"
        if not positive.available:
            flags.append("positive_unavailable")
    return FitResult(name, src.ident, "AVAILABLE", src.theta, src.loglik, src.starts, src.n_converged,
                     reduced.seconds + positive.seconds, M.code_hash(), src.bounds_hit, src.clipped, src.notes,
                     sel, flags, cands, src.wh, src.em_iterations, src.em_trace)


def fit_all_models(ds: D.Dataset, cache: FitCache | None = None, span_name: str | None = None,
                   models: tuple = FULL_MODELS, quad: dict | None = None) -> dict:
    """The eight models of §4 on one dataset: {name: FitResult}, selected models built from their candidates;
    also returns the candidates under their spec names. Reduced fits are cached and never refitted. `quad`
    overrides the node counts / rule (n_tau_nodes, n_g_nodes, adaptive_g) for the §4 node checks."""
    cache = FitCache() if cache is None else cache
    span_name = ds.span.name if span_name is None else span_name
    quad = {} if quad is None else quad
    out = {}
    infos = {}

    def info_for(sp):
        key = (sp.positive, sp.family)
        if key not in infos:
            infos[key] = start_info(sp, ds)
        return infos[key]

    def g_twin(b_name):
        """The G result that a B model collapses onto (B2 -> G2, B3 -> the selected G3, B0 -> G0, B3+ -> G3)."""
        return out.get("G" + b_name[1:].replace("+", "")) if b_name[0] == "B" else None

    def g_spec(g_result):
        return (M.spec(g_result.model, span_name, **quad) if g_result.model in M.MODEL_NAMES
                else selected_spec(g_result.model, g_result, span_name, quad))

    def warm_from_twin(sp_b, g_result, info_b):
        """The B candidate's warm EM chain from its G twin's own (θ collapsed, Σ)."""
        if g_result is None or not g_result.available or g_result.wh is None:
            return None
        (label, theta), = collapsed_start(sp_b, g_result, g_spec(g_result), info_b)
        return [(label + "|chain", theta, g_result.wh)]

    def reseed_g(sp_g, g_result, sp_b, b_result, info_g, b_name):
        """A collapsed B optimum materially above the G optimum (> RESEED_MIN_NAT, i.e. another basin, not EM
        noise) re-seeds G: projection onto G's coordinates, one EM chain under B's Σ; the better G is kept."""
        if not (b_result.available and g_result.available and b_result.wh is not None):
            return g_result
        PB = M.unpack(sp_b, b_result.theta)
        if b_result.loglik <= g_result.loglik + RESEED_MIN_NAT or np.any(PB.A[1:] < 0.99):
            return g_result
        theta = lift_warm_start(sp_b, b_result.theta, sp_g, info_g, PB.s_tau_ms if sp_g.positive else 20.0)
        r2 = em_fit(sp_g, ds, [], info_g, em=cache.em, warm=[(f"reseed{b_name}", theta, b_result.wh)])
        if r2.available and r2.loglik > g_result.loglik:
            r2.starts = list(g_result.starts) + list(r2.starts)
            r2.notes = list(g_result.notes) + list(r2.notes)
            cache.put(cache.key(ds, sp_g), r2)
            return r2
        return g_result

    def nest_b(sp_b, b_result, g_result, info_b):
        """After a G re-seed, one more B chain from the new G point so that l(B) >= l(G) holds again."""
        w = warm_from_twin(sp_b, g_result, info_b)
        if w is None:
            return b_result
        r2 = em_fit(sp_b, ds, [], info_b, em=cache.em, warm=w)
        if r2.available and (not b_result.available or r2.loglik > b_result.loglik):
            r2.starts = list(b_result.starts) + list(r2.starts)
            r2.notes = list(b_result.notes) + list(r2.notes)
            cache.put(cache.key(ds, sp_b), r2)
            return r2
        return b_result

    for name in models:
        if name in M.SELECTED_NAMES:
            red_name, pos_name = M.SELECTED_NAMES[name]
            sp_r, sp_p = M.spec(red_name, span_name, **quad), M.spec(pos_name, span_name, **quad)
            info_r, info_p = info_for(sp_r), info_for(sp_p)
            tw_r, tw_p = g_twin(red_name), g_twin(name)
            red = cache.fit(sp_r, ds, info_r, starts=reduced_starts(sp_r, info_r, tw_r, span_name, quad),
                            warm=warm_from_twin(sp_r, tw_r, info_r) if sp_r.family == "B" else None)
            starts = positive_starts(sp_p, ds, info_p, red, sp_r, tw_p, span_name, quad)
            pos = cache.fit(sp_p, ds, info_p, starts=starts,
                            warm=warm_from_twin(sp_p, tw_p, info_p) if sp_p.family == "B" else None)
            if sp_p.family == "B":
                g_red_name, g_pos_name = M.SELECTED_NAMES["G" + name[1:]]
                for gn, sp_bb, b_res, info_bb, bn in ((g_red_name, sp_r, red, info_r, red_name),
                                                      (g_pos_name, sp_p, pos, info_p, pos_name)):
                    if gn not in out:
                        continue
                    sp_gg = M.spec(gn, span_name, **quad)
                    g_new = reseed_g(sp_gg, out[gn], sp_bb, b_res, info_for(sp_gg), bn)
                    if g_new is not out[gn]:
                        out[gn] = g_new
                        b_res = nest_b(sp_bb, b_res, g_new, info_bb)
                        if bn == red_name:
                            red = b_res
                        else:
                            pos = b_res
                if g_red_name in out and g_pos_name in out:
                    out["G" + name[1:]] = select("G" + name[1:], out[g_red_name], out[g_pos_name],
                                                 M.spec(g_pos_name, span_name, **quad))
            out[red_name], out[pos_name] = red, pos
            out[name] = select(name, red, pos, sp_p)
        else:
            sp = M.spec(name, span_name, **quad)
            info_s = info_for(sp)
            tw = g_twin(name)
            out[name] = cache.fit(sp, ds, info_s, starts=reduced_starts(sp, info_s, tw, span_name, quad),
                                  warm=warm_from_twin(sp, tw, info_s) if sp.family == "B" else None)
            if sp.family == "B" and "G" + name[1:] in out:
                g_name = "G" + name[1:]
                sp_gg = M.spec(g_name, span_name, **quad)
                g_new = reseed_g(sp_gg, out[g_name], sp, out[name], info_for(sp_gg), name)
                if g_new is not out[g_name]:
                    out[g_name] = g_new
                    out[name] = nest_b(sp, out[name], g_new, info_s)
    return out


def reduced_starts(sp_r: M.ModelSpec, info: StartInfo, g_result: FitResult | None, span_name: str,
                   quad: dict | None = None) -> list:
    """A reduced (or any non-selected) model's starts: the four §5 design starts and, for B, its G twin collapsed."""
    starts = start_vectors(sp_r, info)
    if sp_r.family == "B" and g_result is not None and g_result.available:
        sp_g = (M.spec(g_result.model, span_name, **(quad or {})) if g_result.model in M.MODEL_NAMES
                else selected_spec(g_result.model, g_result, span_name, quad))
        starts += collapsed_start(sp_r, g_result, sp_g, info)
    return starts


def positive_starts(sp_p: M.ModelSpec, ds: D.Dataset, info: StartInfo, reduced: FitResult | None,
                    sp_r: M.ModelSpec, g_result: FitResult | None, span_name: str, quad: dict | None = None) -> list:
    """The repaired start set of a positive-spread candidate (S2 repair 2): the four §5 design starts, the four
    smeared-kernel template starts, the reduced fit lifted at three spreads and, for B, the selected G fit collapsed
    to A → 1 (κ = 50, x0 = −5). Each family is labelled so that the S2 basin report can say which were material."""
    starts = start_vectors(sp_p, info) + smeared_starts(sp_p, ds, info)
    if reduced is not None and reduced.available:
        starts += lifted_starts(sp_p, reduced, sp_r, info)
    if g_result is not None and g_result.available and sp_p.family == "B":
        sp_g = selected_spec("G" + sp_p.name[1:].replace("+", ""), g_result, span_name, quad)
        starts += collapsed_start(sp_p, g_result, sp_g, info)
    return starts


def _em_loop(sp: M.ModelSpec, ds: D.Dataset, r: FitResult, cur: D.Dataset, info: StartInfo | None, options,
             max_iter: int, tol: float, tag: str = "em") -> FitResult:
    """The generalised EM loop from an AVAILABLE fit `r` on `cur` (the same trials as `ds` under some whitening)."""
    archive, n_conv, notes = list(r.starts), r.n_converged, list(r.notes)
    for it in range(1, max_iter + 1):
        Sigma = M.m_step_sigma(sp, r.theta, cur)
        wh = D.whitening_from_sigma(cur.wh.mu0, Sigma, 0.0, cur.wh.n_catch)
        nxt = D.rewhiten(ds, wh, f"/{tag}{it}")
        r2 = fit_model(sp, nxt, [(f"{tag}{it}", r.theta)], info, options)
        if not r2.available or r2.loglik < r.loglik:
            # strictly monotone: a decrease, however small (the adaptive quadrature's nodes move with Σ, so the
            # E-step and the likelihood are not exactly consistent near convergence), ends the chain at `r`
            notes.append(f"{tag} stopped at step {it}: " + ("inner solve not CONVERGED" if not r2.available else
                                                             f"objective fell by {r.loglik - r2.loglik:.3g} nat"))
            break
        gain = r2.loglik - r.loglik
        trace = r.em_trace + [float(r2.loglik)]
        archive = archive + list(r2.starts)
        r = FitResult(sp.name, ds.ident, "AVAILABLE", r2.theta, r2.loglik, archive, n_conv, r.seconds + r2.seconds,
                      M.code_hash(), r2.bounds_hit, r2.clipped, notes, "", [], {}, wh, it, trace)
        cur = nxt
        if gain <= tol * max(1.0, abs(r.loglik)):
            break
    r.notes = notes
    return r


def em_fit(sp: M.ModelSpec, ds: D.Dataset, starts: list | None = None, info: StartInfo | None = None,
           options: dict | None = None, em: bool = True, max_iter: int = EM_MAX_ITER, tol: float = EM_TOL,
           warm: list | None = None) -> FitResult:
    """Σ by maximum likelihood within the model (S2 repair 1): the multi-start fit under the dataset's starting
    whitening (the scaled catch covariance), then a generalised EM loop — Σ M-step from the posterior over
    (branch, τ node, g) at the current θ (`models.m_step_sigma`), re-whitening of the same trials, one warm-started
    L-BFGS-B solve — until the total log-likelihood gains less than `tol` relative or `max_iter` steps. μ0 stays the
    training-catch anchor. `warm` = [(label, θ, Whitening)] further EM CHAINS, each started from a fitted point of
    another model under THAT model's Σ (a B candidate from its G twin collapsed, A → 1; a G candidate from a
    collapsed B that scored higher): the chain's first objective equals the other model's log-likelihood, so the
    nesting l(B) ≥ l(G) holds by construction in the joint (θ, Σ) space. The best final log-likelihood over the main
    chain and the warm chains is the result; every start of every chain is archived; `starts=[]` runs the warm
    chains only. The result carries the final whitening (`wh`) and the EM trace. The total log-likelihood never
    decreases along a chain (a decrease, impossible for a converged inner solve, ends it with a note). `em=False`
    is the rev 6 construction (no EM; warm chains then run as single fits under their whitening)."""
    chains = []
    if starts is None or len(starts) > 0:
        r = fit_model(sp, ds, starts, info, options)
        r.wh, r.em_iterations, r.em_trace = ds.wh, 0, [float(r.loglik)]
        if em and r.available:
            r = _em_loop(sp, ds, r, ds, info, options, max_iter, tol)
        chains.append(("main", r))
    for label, theta, wh in (warm or []):
        cur = D.rewhiten(ds, wh, f"/{label}")
        r = fit_model(sp, cur, [(label, np.asarray(theta, dtype=np.float64))], info, options)
        r.wh, r.em_iterations, r.em_trace = wh, 0, [float(r.loglik)]
        if em and r.available:
            r = _em_loop(sp, ds, r, cur, info, options, max_iter, tol, tag=label)
        chains.append((label, r))
    avail = [(lab, r) for lab, r in chains if r.available]
    if not avail:
        best_lab, best = chains[0]
    else:
        best_lab, best = max(avail, key=lambda t: t[1].loglik)
    if len(chains) > 1:
        best.starts = [s for _, r in chains for s in r.starts]
        best.notes = list(best.notes) + [f"chain {best_lab} selected of " +
                                         ", ".join(f"{lab} {r.loglik:.2f}" if r.available else f"{lab} UNAVAILABLE"
                                                   for lab, r in chains)]
        best.seconds = sum(r.seconds for _, r in chains)
    return best


def score_heldout(sp: M.ModelSpec, r: FitResult, test: D.Dataset) -> np.ndarray:
    """Per-trial log density of the test trials under the fitted model — whitened with the MODEL's own (μ0, Σ)
    when the fit carries one (EM), else with the test dataset's whitening (the training fold's starting Σ)."""
    ds = test if (r.wh is None or r.wh is test.wh) else D.rewhiten(test, r.wh, "/model")
    return M.Objective(sp, ds).trial_loglik(r.theta)


def spec_of(result_name: str, span_name: str) -> M.ModelSpec:
    """Spec that evaluates a result's θ: selected names resolve to the candidate that was selected."""
    if result_name in M.SELECTED_NAMES:
        raise ValueError("use selected_spec(result)")
    return M.spec(result_name, span_name)


def selected_spec(name: str, r: FitResult, span_name: str, quad: dict | None = None) -> M.ModelSpec:
    quad = {} if quad is None else quad
    if name in M.SELECTED_NAMES:
        red_name, pos_name = M.SELECTED_NAMES[name]
        return M.spec(red_name if r.selection == "REDUCED" else pos_name, span_name, **quad)
    return M.spec(name, span_name, **quad)


# ----------------------------------------------------------------------------------------------
# cross-validated scoring (§5 score, §6 contrasts)
# ----------------------------------------------------------------------------------------------
@dataclass
class CVResult:
    participant: str
    span: str
    n_scored: int
    scores: dict                 # name -> nat per trial (summed over folds / n_scored), nan if any fold UNAVAILABLE
    fold_sums: dict              # name -> [fold sums]  (inherited convention: mean of these)
    fold_mean: dict
    available: dict              # name -> bool (all five folds AVAILABLE)
    fits: list                   # per fold: {name: FitResult.to_json()}
    seconds: float


def cv_scores(p: D.Participant, span_name: str = "primary", cache: FitCache | None = None,
              models: tuple = FULL_MODELS) -> CVResult:
    t0 = _time.time()
    sp_ = D.span(span_name)
    cache = FitCache() if cache is None else cache
    sums = {m: [] for m in models}
    avail = {m: True for m in models}
    fits = []
    for fold in range(5):
        train, test, _, _ = D.fold_datasets(p, sp_, fold)
        res = fit_all_models(train, cache, span_name, models)
        fits.append({k: v.to_json() for k, v in res.items()})
        for m in models:
            r = res[m]
            if not r.available:
                avail[m] = False
                sums[m].append(np.nan)
                continue
            sp = selected_spec(m, r, span_name)
            ll = score_heldout(sp, r, test)
            sums[m].append(float(np.sum(ll)))
    n = D.n_scored(p)
    scores = {m: (float(np.sum(sums[m]) / n) if avail[m] else float("nan")) for m in models}
    fmean = {m: (float(np.mean(sums[m])) if avail[m] else float("nan")) for m in models}
    return CVResult(f"S{p.subject}_{p.session}{p.tag}", span_name, n, scores, sums, fmean, avail, fits,
                    _time.time() - t0)


# ----------------------------------------------------------------------------------------------
# constrained (profile) fits, §7.5 — the search itself is decide.hull_search
# ----------------------------------------------------------------------------------------------
def lift_warm_start(sp_from: M.ModelSpec, theta_from: np.ndarray, sp_to: M.ModelSpec, info: StartInfo,
                    s_tau_ms: float = 20.0, logkappa: float | None = None, x0: float | None = None) -> np.ndarray:
    """Map a fitted vector of `sp_from` onto `sp_to`'s coordinates: REDUCED → positive LIFT supplies the shift-only
    coefficients from the floored T_B initialisation; positive → reduced PROJECTS (shift-only coefficients dropped);
    θ_τ (when `sp_to` has it) is set to `s_tau_ms`; the two-state parameters are kept, taken from `logkappa`/`x0`
    when given (the G → B collapse), or the §5 fallbacks when `sp_from` has none. Every coordinate is clipped to
    the target box (S2 repair 3: a coefficient that had run below the softplus floor used to be packed as −inf)."""
    P = M.unpack(sp_from, theta_from)
    b_to = sp_to.basis()
    gamma = np.where(P.c > 0, M.softplus_inv(np.maximum(P.c, 1e-300)), M.GAMMA_MIN)
    gamma = np.maximum(np.where(np.isfinite(gamma), gamma, M.GAMMA_MIN), M.GAMMA_MIN)
    gamma_full = np.array(info.gamma_B, dtype=np.float64)
    vis = [j for j in b_to.visible if j != b_to.gauge]
    gamma_full[vis] = gamma[vis]
    if sp_to.positive and sp_from.positive:
        gamma_full[b_to.invisible] = gamma[b_to.invisible]
    alpha = M.softplus_inv(np.maximum(P.a[1:], 1e-6))
    if sp_from.family == "B":
        idx_from = sp_from.layout()["index"]                      # the coordinates themselves, not log(exp(·))
        lk_from, x0_from = float(theta_from[idx_from["logkappa"]]), float(theta_from[idx_from["x0"]])
    else:
        lk_from, x0_from = np.log(KAPPA_FALLBACK), X0_FALLBACK
    lk = lk_from if logkappa is None else logkappa
    xx = x0_from if x0 is None else x0
    th = M.pack(sp_to, alpha, gamma_full, lk, xx, s_tau_ms, P.s_g)
    lb, ub = sp_to.bounds()
    th = np.clip(th, lb, ub)
    if not np.all(np.isfinite(th)):
        bad = [sp_to.param_names()[i] for i in np.where(~np.isfinite(th))[0]]
        raise ValueError(f"lift produced non-finite coordinates {bad} from {sp_from.name} to {sp_to.name}")
    return th


def _level5_responses(ds: D.Dataset):
    """The training level-5 mean response about μ0 (raw = T_A's target, smoothed = T_B's)."""
    R = ds.Y - ds.wh.mu0
    lev5 = R[ds.k == 5].mean(axis=0) if np.any(ds.k == 5) else R[ds.k == ds.k.max()].mean(axis=0)
    kern = np.ones(SMOOTH_WINDOWS) / SMOOTH_WINDOWS
    sm = np.convolve(np.pad(lev5, SMOOTH_WINDOWS // 2, mode="edge"), kern, mode="valid")
    return lev5, sm


def smeared_template_gamma(b: M.Basis, response: np.ndarray, s_tau_ms: float) -> np.ndarray:
    """Template start for a positive-spread model at spread s (S2 repair 2): non-negative least squares of the
    basis SMEARED by the truncated-normal latency kernel at s — Σ_τ w_τ(s) Bmat[τ], all J columns, the shift-only
    ones included — to the level-5 mean response, so that the start's EXPECTED response matches the mean response
    rather than the template itself (the level-5 mean is the jitter-broadened template). Floor 1e-3, gauge rescale."""
    w = M.truncnorm_node_weights(b.nodes_ms, s_tau_ms)
    Bs = np.einsum("n,nwj->wj", w, b.Bmat)
    coef, _ = nnls(Bs, np.asarray(response, dtype=np.float64))
    c = np.maximum(coef, COEF_FLOOR)
    c *= np.log(2.0) / c[b.gauge]
    return np.maximum(np.asarray(M.softplus_inv(c), dtype=np.float64), M.GAMMA_MIN)


def smeared_starts(sp: M.ModelSpec, ds: D.Dataset, info: StartInfo, spreads=SMEAR_SPREADS_MS) -> list:
    """Four smeared-kernel starts for a positive-spread model: spreads 20/40/80/120 ms, the raw (T_A) and smoothed
    (T_B) level-5 response alternating, s_g = 0.4 when the model has a scale term."""
    if not sp.positive:
        return []
    b = sp.basis()
    raw, sm = _level5_responses(ds)
    alpha = M.softplus_inv(np.maximum(info.a, 1e-6))
    s_g = SMEAR_S_G if sp.scale_free else 0.0
    out = []
    for i, s in enumerate(spreads):
        resp, tag = (raw, "A") if i % 2 == 0 else (sm, "B")
        gamma = smeared_template_gamma(b, resp, s)
        s_eff = s if sp.tau_free else sp.tau_fixed_ms
        out.append((f"sm{tag}|tau{s:g}|sg{s_g:g}", M.pack(sp, alpha, gamma, info.logkappa, info.x0, s_eff, s_g)))
    return out


def lifted_starts(sp_p: M.ModelSpec, reduced: FitResult, sp_r: M.ModelSpec, info: StartInfo,
                  spreads=LIFT_SPREADS_MS) -> list:
    """The cached reduced fit (G2 for G3+, …) lifted onto the positive-spread coordinates at three spreads."""
    if not reduced.available:
        return []
    return [(f"lift{sp_r.name}|tau{s:g}", lift_warm_start(sp_r, reduced.theta, sp_p, info, s)) for s in spreads]


def collapsed_start(sp_b: M.ModelSpec, g_result: FitResult, sp_g: M.ModelSpec, info: StartInfo) -> list:
    """The selected G fit as a B start with A → 1 at every level (κ = 50, x0 = −5): the point of the B family at
    which it coincides with the G optimum, so that l(B+) ≥ l(G+) holds by construction when it is accepted."""
    if not g_result.available:
        return []
    PG = M.unpack(sp_g, g_result.theta)
    s = PG.s_tau_ms if (sp_g.positive and PG.s_tau_ms > 0) else LIFT_SPREADS_MS[0]
    return [(f"collapse{sp_g.name}", lift_warm_start(sp_g, g_result.theta, sp_b, info, s, np.log(M.KAPPA_MAX), COLLAPSE_X0))]


def constrained_starts(sp_full: M.ModelSpec, sp_c: M.ModelSpec, unrestricted: FitResult, sp_u: M.ModelSpec,
                       info: StartInfo, n_starts: int = 2) -> list:
    """TWO starts per constrained fit (§5): the warm start and the T_B start with the nearest nuisance start;
    `n_starts` = 4 adds the remaining §5 recipes (the S2 validation of the two-start exception)."""
    warm = lift_warm_start(sp_u, unrestricted.theta, sp_c, info)
    recipes = [r for r in nuisance_recipes(sp_full) if r.template == "B"]
    s = sp_c.tau_fixed_ms
    if s <= 0.0:
        rB = StartRecipe("B", 1.0, 0.0, 0.0)
    else:
        rB = min(recipes, key=lambda r: (abs(r.s_tau_ms - s), recipes.index(r)))
        rB = StartRecipe("B", 1.0, s, rB.s_g)
    starts = [("warm", warm)] + start_vectors(sp_c, info, [rB])
    if n_starts > 2:
        others = [StartRecipe(r.template, r.amp_scale, s, r.s_g) for r in nuisance_recipes(sp_full)
                  if not (r.template == "B" and r.s_g == rB.s_g)]
        starts += start_vectors(sp_c, info, others)[: n_starts - 2]
    return starts


def profile_evaluator(family: str, ds: D.Dataset, unrestricted: FitResult, span_name: str, cache: FitCache,
                      info: StartInfo | None = None, n_starts: int = 2):
    """Callable s ↦ (ℓ_prof(s) or None if UNAVAILABLE, FitResult) for decide.hull_search. The s = 0 point is the
    cached reduced fit (G2/B2)."""
    sp_full = M.spec(family + "3+", span_name)
    sp_u = selected_spec(family + "3", unrestricted, span_name)
    info = start_info(sp_full, ds) if info is None else info
    log = {}

    def evaluate(s_ms: float):
        sp_c = sp_full.constrained(s_ms)
        if s_ms <= 0.0:
            r = cache.fit(sp_c, ds, info)
        else:
            starts = constrained_starts(sp_full, sp_c, unrestricted, sp_u, info, n_starts)
            r = cache.fit(sp_c, ds, info, recipe=f"prof{n_starts}", starts=starts)
        log[float(s_ms)] = r
        return (r.loglik if r.available else None), r

    return evaluate, log


# ----------------------------------------------------------------------------------------------
# generator fits (§7.1)
# ----------------------------------------------------------------------------------------------
@dataclass
class GeneratorConfig:
    family: str                  # G | B
    model: str                   # G3 | B3 | B0
    a: np.ndarray                # (6,)
    c: np.ndarray                # (J,) whole-epoch template coefficients (unnormalised)
    c_tilde: np.ndarray
    s_tau_ms: float
    s_g: float
    kappa: float | None
    x0: float | None
    A: np.ndarray | None
    mu0: np.ndarray              # (53,)
    Sigma: np.ndarray            # (53, 53)
    strength: float
    selection: str
    flags: list
    base: str

    def to_npz(self, path: str):
        np.savez(path, family=self.family, model=self.model, a=self.a, c=self.c, c_tilde=self.c_tilde,
                 s_tau_ms=self.s_tau_ms, s_g=self.s_g, kappa=np.nan if self.kappa is None else self.kappa,
                 x0=np.nan if self.x0 is None else self.x0, A=np.full(6, np.nan) if self.A is None else self.A,
                 mu0=self.mu0, Sigma=self.Sigma, strength=self.strength, selection=self.selection,
                 flags=np.array(self.flags), base=self.base)

    @staticmethod
    def from_npz(path: str) -> "GeneratorConfig":
        z = np.load(path, allow_pickle=False)
        kappa = float(z["kappa"]); x0 = float(z["x0"])
        return GeneratorConfig(str(z["family"]), str(z["model"]), z["a"], z["c"], z["c_tilde"], float(z["s_tau_ms"]),
                               float(z["s_g"]), None if np.isnan(kappa) else kappa, None if np.isnan(x0) else x0,
                               None if np.all(np.isnan(z["A"])) else z["A"], z["mu0"], z["Sigma"],
                               float(z["strength"]), str(z["selection"]), [str(f) for f in z["flags"]], str(z["base"]))


def strength_of(b_whole: M.Basis, a: np.ndarray, c_tilde: np.ndarray) -> float:
    """a_gen(5) × mean of T̃_gen over the PRIMARY windows at τ = 0 (§7.1)."""
    Tw = b_whole.Bmat[b_whole.node0] @ c_tilde
    return float(a[5] * np.mean(Tw[D.PRIMARY_WINDOWS]))


def generator_fits(p: D.Participant, cache: FitCache | None = None) -> dict:
    """G3, B3 and B0 on full data, whole-epoch span and support (§7.1). Returns {model: GeneratorConfig} and
    the FitResults under 'fits'."""
    cache = FitCache() if cache is None else cache
    ds = D.full_dataset(p, D.span("whole"))
    res = fit_all_models(ds, cache, "whole", ("G3", "B3", "B0"))
    b = M.basis("whole")
    out = {"fits": {k: v for k, v in res.items()}}
    for name in ("G3", "B3", "B0"):
        r = res[name]
        if not r.available:
            out[name] = None
            continue
        sp = selected_spec(name, r, "whole")
        P = M.unpack(sp, r.theta)
        out[name] = GeneratorConfig(name[0], name, P.a, P.c, P.c_tilde, P.s_tau_ms, P.s_g, P.kappa, P.x0, P.A,
                                    ds.wh.mu0, ds.wh.Sigma, strength_of(b, P.a, P.c_tilde), r.selection, r.flags,
                                    f"S{p.subject}_{p.session}{p.tag}")
    return out


def summarize_fit(sp: M.ModelSpec, r: FitResult) -> dict:
    """Readable parameter summary for logs and tables."""
    if not r.available:
        return dict(model=r.model, status=r.status)
    P = M.unpack(sp, r.theta)
    d = dict(model=r.model, status=r.status, selection=r.selection, loglik=r.loglik, a=[float(v) for v in P.a[1:]],
             s_tau_ms=P.s_tau_ms, s_g=P.s_g, m_vis_check=sp.basis().m_vis(P.c_tilde),
             n_converged=r.n_converged, bounds_hit=r.bounds_hit, flags=r.flags, seconds=r.seconds)
    if P.kappa is not None:
        d.update(kappa=P.kappa, x0=P.x0, A=[float(v) for v in P.A[1:]], clipped=r.clipped)
    if P.s_tau_ms > 0:
        d.update(realised_sd_ms=M.realised_sd_ms(P.s_tau_ms), truncated_sd_ms=M.truncated_parent_sd_ms(P.s_tau_ms))
    return d

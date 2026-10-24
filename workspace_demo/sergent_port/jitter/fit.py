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
    options = dict(LBFGSB_OPTIONS) if options is None else options
    rng = np.random.default_rng(seed)
    attempts = []
    t0 = _time.time()

    def one(x_start, kind):
        run = _run_lbfgsb(obj, x_start, lb, ub, options)
        st = _assess(run)
        attempts.append(dict(kind=kind, status=st, f=run["f"], pg=run["pg"], nit=run["nit"], nfev=run["nfev"],
                             message=run["message"], seconds=run["seconds"]))
        return run, st

    def perturbed(x):
        return np.clip(x + rng.normal(0.0, PERTURB_SD, size=x.shape), lb, ub)

    def resolve(x_start, kind):
        """One attempt with the EARLY pairing rule. Returns (run, status, early_flag)."""
        run, st = one(x_start, kind)
        if st != "EARLY":
            return run, st, False
        run2, st2 = one(perturbed(x_start), kind + "/early-rerun")
        both = _ok_i_iii(run) and _ok_i_iii(run2)
        agree = abs(run["f"] - run2["f"]) <= EARLY_AGREE * max(1.0, abs(run["f"]))
        best = run if run["f"] <= run2["f"] else run2
        if both and agree:
            return best, "CONVERGED", True
        return best, "EARLY_PAIR_FAILED", True

    run, st, early = resolve(np.asarray(x0, dtype=np.float64), "start")
    retries = 0
    best_run, best_st = run, st
    while best_st != "CONVERGED" and retries < MAX_RETRIES:
        retries += 1
        run_r, st_r, early_r = resolve(perturbed(np.asarray(x0, dtype=np.float64)), f"retry{retries}")
        early = early or early_r
        if st_r == "CONVERGED" or (best_st != "CONVERGED" and np.isfinite(run_r["f"]) and run_r["f"] < best_run["f"]):
            best_run, best_st = run_r, st_r
    n_eff = getattr(obj, "n_eff", 1)
    for a in attempts:
        a["f_total"] = a["f"] * n_eff
    return StartResult(label, best_st, best_run["x"], best_run["f"] * n_eff, best_run["pg"], best_run["nit"],
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

    @property
    def available(self) -> bool:
        return self.status == "AVAILABLE"

    def to_json(self) -> dict:
        d = dict(model=self.model, ident=self.ident, status=self.status,
                 theta=None if self.theta is None else [float(v) for v in self.theta],
                 loglik=float(self.loglik), n_converged=self.n_converged, seconds=self.seconds,
                 code_hash=self.code_hash, bounds_hit=self.bounds_hit, clipped=self.clipped, notes=self.notes,
                 selection=self.selection, flags=self.flags, candidates=self.candidates,
                 starts=[dict(label=s.label, status=s.status, f=s.f, pg=s.pg, nit=s.nit, nfev=s.nfev,
                              seconds=s.seconds, early=s.early, retries=s.retries, attempts=s.attempts,
                              x=[float(v) for v in s.x]) for s in self.starts])
        return d

    @staticmethod
    def from_json(d: dict) -> "FitResult":
        starts = [StartResult(s["label"], s["status"], np.asarray(s["x"]), s["f"], s["pg"], s["nit"], s["nfev"],
                              s["seconds"], s["attempts"], s["early"], s["retries"]) for s in d["starts"]]
        return FitResult(d["model"], d["ident"], d["status"], None if d["theta"] is None else np.asarray(d["theta"]),
                         d["loglik"], starts, d["n_converged"], d["seconds"], d["code_hash"], d["bounds_hit"],
                         d["clipped"], d["notes"], d.get("selection", ""), d.get("flags", []), d.get("candidates", {}))


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
    components (§5). Optional on-disk JSON store."""

    def __init__(self, directory: str | None = None):
        self.mem = {}
        self.dir = directory
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
            starts: list | None = None) -> FitResult:
        key = self.key(ds, sp, recipe)
        r = self.get(key)
        if r is None:
            r = fit_model(sp, ds, starts, info)
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
                     sel, flags, cands)


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

    for name in models:
        if name in M.SELECTED_NAMES:
            red_name, pos_name = M.SELECTED_NAMES[name]
            sp_r, sp_p = M.spec(red_name, span_name, **quad), M.spec(pos_name, span_name, **quad)
            red = cache.fit(sp_r, ds, info_for(sp_r))
            pos = cache.fit(sp_p, ds, info_for(sp_p))
            out[red_name], out[pos_name] = red, pos
            out[name] = select(name, red, pos, sp_p)
        else:
            sp = M.spec(name, span_name, **quad)
            out[name] = cache.fit(sp, ds, info_for(sp))
    return out


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
            ll = M.Objective(sp, train).trial_loglik(r.theta, test)
            sums[m].append(float(np.sum(ll)))
    n = D.n_scored(p)
    scores = {m: (float(np.sum(sums[m]) / n) if avail[m] else float("nan")) for m in models}
    fmean = {m: (float(np.mean(sums[m])) if avail[m] else float("nan")) for m in models}
    return CVResult(f"S{p.subject}_{p.session}{p.tag}", span_name, n, scores, sums, fmean, avail, fits,
                    _time.time() - t0)


# ----------------------------------------------------------------------------------------------
# constrained (profile) fits, §7.5 — the search itself is decide.hull_search
# ----------------------------------------------------------------------------------------------
def lift_warm_start(sp_from: M.ModelSpec, theta_from: np.ndarray, sp_to: M.ModelSpec, info: StartInfo) -> np.ndarray:
    """Map an unrestricted solution onto a constrained model's coordinates: drop θ_τ; REDUCED → positive LIFT
    supplies the shift-only coefficients from the floored T_B initialisation; positive → reduced PROJECTS
    (shift-only coefficients dropped)."""
    P = M.unpack(sp_from, theta_from)
    b_to = sp_to.basis()
    gamma = np.where(P.c > 0, M.softplus_inv(np.maximum(P.c, 1e-300)), -np.inf)
    gamma_full = np.array(info.gamma_B, dtype=np.float64)
    vis = [j for j in b_to.visible if j != b_to.gauge]
    gamma_full[vis] = gamma[vis]
    if sp_to.positive and sp_from.positive:
        gamma_full[b_to.invisible] = gamma[b_to.invisible]
    alpha = M.softplus_inv(P.a[1:])
    logkappa = np.log(P.kappa) if P.kappa is not None else 0.0
    x0 = P.x0 if P.x0 is not None else X0_FALLBACK
    return M.pack(sp_to, alpha, gamma_full, logkappa, x0, 20.0, P.s_g)


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

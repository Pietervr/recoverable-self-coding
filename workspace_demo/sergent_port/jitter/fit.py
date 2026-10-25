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
from dataclasses import asdict, dataclass, field, replace  # noqa: E402

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
RESEED_MIN_NAT = 0.05                          #   a B this far above G re-seeds G (another basin, not EM noise)
EM_RETRY_MAXITER_FACTOR = 4                    # repair D4: an inner EM solve that ends NOT_CONVERGED without improving the
                                               #   chain point is retried once from that point with this many times the budget
NEST_TOL_REL = 1e-6                            # the nesting l(B) >= l(G) is checked to this relative tolerance (25 Oct 2026)
# The polish (25 Oct 2026, Codex latency/quadrature review finding 11; DESIGN §5): a start whose RETAINED end point is
# stationary — (i) projected gradient <= PG_TOL and (iii) finite — but NOT_CONVERGED, because (ii) the five-iteration
# objective-change rule failed or the EARLY exception was refused, and which would otherwise be LOST (it beats every
# CONVERGED start of the fit, or there is none), gets ONE restart from that end point through run_start again: the same
# options, the same iteration budget, the same acceptance rules and tolerances. It is accepted only when run_start accepts
# it. One that still fails while its end point is better than the selected start is a NUMERICAL FAILURE: recorded in the
# fit (`numerical_failure`, a note naming the lost objective) and carried by every record built from it, never hidden by
# the worse candidate that stands. The UNAVAILABLE semantics are unchanged. Found on the AWS 31-node reference of W2 set 0
# (m15 fold 3): the B3+ chain warm-started from the G3+ optimum reached -10944.0075 nat with pg 9.5e-8 after 12 iterations,
# was retained NOT_CONVERGED, never entered the EM loop, and the main chain 11.5 nat worse was selected (B3 then REDUCED).
#
# The NUMERICAL-FAILURE POLICY (25 Oct 2026, the session's decision on Codex S3 re-review finding 7; DESIGN §5):
#  (a) DETERMINISTIC RESCUE (em_fit): a fit that ends with numerical_failure — a stationary end point the acceptance rule
#      could not accept stands above the selected log-likelihood, or nothing was selected while one exists — is restarted
#      from that better end point (its θ, under the whitening (μ0, Σ) it was reached on, then the EM loop where EM
#      applies), through fit_model with the STANDARD options and the UNCHANGED acceptance rule, for at most RESCUE_ROUNDS
#      rounds. Seeds are the usual label hashes: no new randomness. An accepted rescue that beats the selected fit becomes
#      the selection and the failure is RESOLVED; `FitResult.rescue` records the rounds and the before/after values.
#  (b) An UNRESOLVED failure makes the fit UNAVAILABLE with unavailable_reason "numerical_failure" (finalize_failure, applied
#      at every exit of the fitter: fit_all_models, profile_evaluator, the task records), so every availability
#      denominator and gate counts it like any other UNAVAILABLE fit; its diagnostics (the standing and the lost
#      log-likelihoods, the lost end point's status) stay in `rescue`. No AVAILABLE result leaves the fitter flagged.
#  (c) The FINAL NESTING GUARD (fit_all_models, every call, whether or not the two-pass rule fired): every G/B candidate
#      pair and every selected G/B pair at the same quadrature with l(B) − l(G) < −NEST_TOL_REL·max(1, |l(G)|) first gets
#      the existing nest rescue (one B chain from G's point under G's Σ); a deficit that persists is recorded on B as
#      `nesting` with failure True — counted by every task record, never silently passed (and never an availability
#      change: a persistent deficit is a recorded nesting failure, not a numerical failure).
RESCUE_ROUNDS = 2
# Profiles (§5; 25 Oct 2026, Codex S3 re-review finding 8): the S2 validation of the two-start exception FAILED (G 425/1200,
# B 326/1200 grid points), so every production constrained fit uses FOUR starts. profile_evaluator and constrained_starts
# default to this constant and s4.rec_task / s5.full_task pass it explicitly; two-start calls remain only in the S2
# validation and benchmark code, which pass n_starts=2 themselves.
PROFILE_STARTS = 4


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
        """CONVERGED: (ii) holds at the best stationary point, or — ONLY when that point was reached in fewer than
        EARLY_ITERS iterations (a warm start already at an optimum, the declared EARLY exception) — no other attempt
        found a better objective. A stationary end point that ran five or more iterations and still fails (ii) is
        NOT_CONVERGED however the retries fared (Codex S3 review 24 Oct, finding 3)."""
        if best is None:
            return False
        if best["status0"] == "CONVERGED":
            return True
        if best["nit"] >= EARLY_ITERS:
            return False
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


def stationary_unaccepted(s: StartResult) -> bool:
    """A retained end point that is stationary by the declared criteria — (i) projected gradient <= PG_TOL and (iii)
    finite — yet NOT_CONVERGED: refused on (ii) the five-iteration objective-change rule, or the EARLY exception was
    refused because the perturbed re-run found a point better by more than 1e-8 relative. The polish restarts from
    exactly these points; nothing else is ever polished (a non-stationary end point is an optimiser failure, not a
    lost optimum)."""
    return bool(s.status == "NOT_CONVERGED" and np.isfinite(s.f) and np.all(np.isfinite(s.x)) and s.pg <= PG_TOL)


def _polish_record(calls: int = 0, accepted: int = 0, seconds: float = 0.0, unaccepted_loglik=None) -> dict:
    return dict(calls=int(calls), accepted=int(accepted), seconds=float(seconds),
                unaccepted_loglik=None if unaccepted_loglik is None else float(unaccepted_loglik))


def _sum_polish(records) -> dict:
    """The polish records of several fits (the chains of em_fit, the candidates of select) as one: counts and seconds
    summed, `unaccepted_loglik` the best stationary end point that no fit could accept (None when there was none)."""
    recs = [r for r in records if r]
    un = [r["unaccepted_loglik"] for r in recs if r.get("unaccepted_loglik") is not None]
    return _polish_record(sum(r.get("calls", 0) for r in recs), sum(r.get("accepted", 0) for r in recs),
                          sum(r.get("seconds", 0.0) for r in recs), max(un) if un else None)


def _failure_against(unaccepted_loglik, selected_loglik, available: bool) -> bool:
    """The numerical-failure rule: a stationary end point the acceptance rule could not accept stands ABOVE the selected
    log-likelihood by more than 1e-8 relative (or nothing was selected while such a point exists) — a worse candidate, or
    none, stands in for an optimum the optimiser reached."""
    if unaccepted_loglik is None:
        return False
    if not available:
        return True
    return bool(unaccepted_loglik > selected_loglik + EARLY_AGREE * max(1.0, abs(selected_loglik)))


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
    quad: dict | None = None     # the quadrature that produced θ (n_tau_nodes, n_g_nodes, adaptive_g); a two-pass refit
    #                              (models.QUAD_G_RULE "17then33") adds refit_from, refit_s_g, loglik_before, seconds_before.
    #                              None = a record from before 25 Oct 2026: the caller's spec applies.
    numerical_failure: bool = False                   # a stationary end point the rule could not accept stands above
    #                                                   the selected log-likelihood, or a required rescue chain failed
    #                                                   (25 Oct 2026; the set record carries it)
    polish: dict = field(default_factory=dict)        # calls, accepted, seconds, unaccepted_loglik (see _polish_record)
    unavailable_reason: str = ""                      # "" when AVAILABLE; "no_converged_start", "numerical_failure",
    #                                                   "both_candidates_unavailable" (25 Oct 2026)
    rescue: dict = field(default_factory=dict)        # the deterministic rescue of policy (a): rounds, the standing and
    #                                                   the lost log-likelihoods, the lost end point's status, resolved
    nesting: dict = field(default_factory=dict)       # B results: the final nesting guard's reading against the G twin
    #                                                   (deficit, tolerance, same quadrature, rescued, failure)
    lost: object = field(default=None, repr=False, compare=False)   # the best stationary end point no rule accepted, as
    #                                                   dict(theta, wh, loglik, status, label) — in memory only (the
    #                                                   rescue runs in the process that found it); never serialised

    @property
    def available(self) -> bool:
        return self.status == "AVAILABLE"

    def to_json(self) -> dict:
        d = dict(model=self.model, ident=self.ident, status=self.status,
                 theta=None if self.theta is None else [float(v) for v in self.theta],
                 loglik=float(self.loglik), n_converged=self.n_converged, seconds=self.seconds,
                 code_hash=self.code_hash, bounds_hit=self.bounds_hit, clipped=self.clipped, notes=self.notes,
                 selection=self.selection, flags=self.flags, candidates=self.candidates, quad=self.quad,
                 numerical_failure=bool(self.numerical_failure), polish=dict(self.polish),
                 unavailable_reason=self.unavailable_reason, rescue=_jsonable(self.rescue), nesting=_jsonable(self.nesting),
                 em_iterations=self.em_iterations, em_trace=[float(v) for v in self.em_trace],
                 sigma_logdet=None if self.wh is None else float(self.wh.logdet),
                 wh=None if self.wh is None else dict(mu0=[float(v) for v in self.wh.mu0],
                                                      Sigma=[[float(v) for v in row] for row in self.wh.Sigma],
                                                      shrinkage=float(self.wh.shrinkage), n_catch=int(self.wh.n_catch)),
                 starts=[dict(label=s.label, status=s.status, f=s.f, pg=s.pg, nit=s.nit, nfev=s.nfev,
                              seconds=s.seconds, early=s.early, retries=s.retries, attempts=s.attempts,
                              x=[float(v) for v in s.x]) for s in self.starts])
        return d

    @staticmethod
    def from_json(d: dict) -> "FitResult":
        """The fitted whitening (μ0, Σ) is serialised and rebuilt, so that a result read back scores held-out data
        under the MODEL's own Σ exactly as the fresh result did (Codex S3 review 24 Oct, finding 2: the earlier
        form dropped it and a disk-cache round trip changed the held-out density by several nat). A record without
        a whitening (rev 6 era) comes back with wh=None and scores under the data's whitening, as it was fitted."""
        starts = [StartResult(s["label"], s["status"], np.asarray(s["x"]), s["f"], s["pg"], s["nit"], s["nfev"],
                              s["seconds"], s["attempts"], s["early"], s["retries"]) for s in d["starts"]]
        wh = None
        if d.get("wh") is not None:
            w = d["wh"]
            wh = D.whitening_from_sigma(np.asarray(w["mu0"], dtype=np.float64), np.asarray(w["Sigma"], dtype=np.float64),
                                        float(w.get("shrinkage", 0.0)), int(w.get("n_catch", 0)))
        return FitResult(d["model"], d["ident"], d["status"], None if d["theta"] is None else np.asarray(d["theta"]),
                         d["loglik"], starts, d["n_converged"], d["seconds"], d["code_hash"], d["bounds_hit"],
                         d["clipped"], d["notes"], d.get("selection", ""), d.get("flags", []), d.get("candidates", {}),
                         wh, d.get("em_iterations", 0), d.get("em_trace", []), d.get("quad"),
                         bool(d.get("numerical_failure", False)), dict(d.get("polish") or {}),
                         d.get("unavailable_reason", "" if d["status"] == "AVAILABLE" else "no_converged_start"),
                         dict(d.get("rescue") or {}), dict(d.get("nesting") or {}))


def _jsonable(v):
    """Plain JSON values (floats, lists, dicts) from a diagnostics dict that may hold numpy scalars or infinities."""
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (np.floating, float)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _quad_of(sp: M.ModelSpec) -> dict:
    """The quadrature record a FitResult carries for the spec that produced it."""
    return dict(n_tau_nodes=int(sp.n_tau_nodes), n_g_nodes=int(sp.n_g_nodes), adaptive_g=bool(sp.adaptive_g))


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
              options: dict | None = None, polish: bool = True) -> FitResult:
    """Multi-start fit of one candidate model (§5). `starts` = [(label, θ0)] overrides the four recipes.
    `polish` (25 Oct 2026, see the module constants): every start whose retained end point is stationary but
    NOT_CONVERGED and better than the best CONVERGED start (or the only kind there is) is restarted ONCE from that end
    point through run_start — same options, budget and acceptance rules; the restart is archived as `<label>|polish` and
    joins the candidate set only if run_start accepts it. A stationary end point that still stands above the selected
    start afterwards is a numerical failure (flag + note); it never replaces the acceptance rule's verdict. The EM
    loop's inner solves pass polish=False: repair D4 governs those (a NOT_CONVERGED ascent step is accepted, retried
    with a larger budget when it does not improve), and the next step's warm start polishes them."""
    t0 = _time.time()
    info = start_info(sp, ds) if info is None else info
    starts = start_vectors(sp, info) if starts is None else starts
    obj = M.Objective(sp, ds)
    lb, ub = sp.bounds()
    results = []
    for i, (label, x0) in enumerate(starts):
        results.append(run_start(obj, label, x0, lb, ub, _seed(ds.ident, sp.name, label, i), options))
    notes = list(info.notes)
    pol = _polish_record()
    if polish:
        for i, s in enumerate(list(results)):
            if not stationary_unaccepted(s):
                continue
            best_conv = min((r.f for r in results if r.status == "CONVERGED"), default=np.inf)
            if np.isfinite(best_conv) and not s.f < best_conv - EARLY_AGREE * max(1.0, abs(best_conv)):
                continue                                  # a CONVERGED start is at least as good: nothing is lost
            p = run_start(obj, s.label + "|polish", s.x, lb, ub, _seed(ds.ident, sp.name, s.label, i, "polish"), options)
            results.append(p)
            pol["calls"] += 1
            pol["seconds"] += p.seconds
            if p.status == "CONVERGED":
                pol["accepted"] += 1
                notes.append(f"{s.label}: stationary NOT_CONVERGED end point ({-s.f:.3f} nat, pg {s.pg:.2e}, {s.nit} it) "
                             f"polished and accepted at {-p.f:.3f} nat")
            else:
                notes.append(f"{s.label}: stationary NOT_CONVERGED end point ({-s.f:.3f} nat, pg {s.pg:.2e}, {s.nit} it) "
                             f"not accepted after the polish ({p.status} at {-p.f:.3f} nat)")
    conv = [r for r in results if r.status == "CONVERGED"]
    lost = [r for r in results if stationary_unaccepted(r)]
    pol["unaccepted_loglik"] = max(-r.f for r in lost) if lost else None
    best_lost = None
    if lost:
        bl = min(lost, key=lambda r: (r.f, r.label))
        best_lost = dict(theta=np.asarray(bl.x, dtype=np.float64), wh=ds.wh, loglik=-float(bl.f), status=bl.status, label=bl.label)
    if conv:
        best = min(conv, key=lambda r: (r.f, r.label))
        P = M.unpack(sp, best.x)
        clipped = [] if P.clipped is None else [int(v) for v in P.clipped]
        failed = _failure_against(pol["unaccepted_loglik"], -best.f, True)
        if failed:
            notes.append(f"numerical failure: a stationary end point at {pol['unaccepted_loglik']:.3f} nat could not be "
                         f"accepted; the selected start stands at {-best.f:.3f} nat")
        return FitResult(sp.name, ds.ident, "AVAILABLE", best.x, -best.f, results, len(conv), _time.time() - t0,
                         M.code_hash(), _bounds_hit(sp, best.x), clipped, notes, quad=_quad_of(sp),
                         numerical_failure=failed, polish=pol, lost=best_lost)
    failed = _failure_against(pol["unaccepted_loglik"], -np.inf, False)
    if failed:
        notes.append(f"numerical failure: a stationary end point at {pol['unaccepted_loglik']:.3f} nat could not be "
                     f"accepted and no start is CONVERGED")
    return FitResult(sp.name, ds.ident, "UNAVAILABLE", None, -np.inf, results, 0, _time.time() - t0,
                     M.code_hash(), [], [], notes + ["no CONVERGED start"], quad=_quad_of(sp),
                     numerical_failure=failed, polish=pol, unavailable_reason="no_converged_start", lost=best_lost)


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

    def key(self, ds: D.Dataset, sp: M.ModelSpec, recipe: str = "std") -> str:
        """Cache identity: data identity, model, quadrature, start recipe, the scale-quadrature RULE in force
        (models.QUAD_G_RULE; a two-pass refit also carries its own recipe suffix), the EM mode of this cache and the
        code hash — so that a persistent cache written under another construction, rule or code version can never
        answer for this one (Codex S3 review 24 Oct, finding 2)."""
        quad = f"t{sp.n_tau_nodes}g{sp.n_g_nodes}{'a' if sp.adaptive_g else 'p'}"
        return f"{ds.ident}|{sp.name}|{quad}|{recipe}|rule{M.QUAD_G_RULE}|{'em' if self.em else 'fixed'}|{M.code_hash()}"

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
    # a numerical failure in an AVAILABLE candidate is one of the selected model (the REDUCED/POSITIVE comparison may be
    # wrong); a candidate already made UNAVAILABLE by policy (b) is treated like any other UNAVAILABLE candidate (the
    # one-candidate rule applies) and named in the flags (25 Oct 2026)
    nf = bool((reduced.numerical_failure and reduced.available) or (positive.numerical_failure and positive.available))
    for tag, c in (("reduced", reduced), ("positive", positive)):
        if not c.available and c.numerical_failure:
            flags.append(f"{tag}_numerical_failure")
    pol = _sum_polish([reduced.polish, positive.polish])
    if not reduced.available and not positive.available:
        return FitResult(name, reduced.ident, "UNAVAILABLE", None, -np.inf, [], 0, 0.0, M.code_hash(), [], [],
                         ["both candidates UNAVAILABLE"], "", flags, cands,
                         numerical_failure=bool(reduced.numerical_failure or positive.numerical_failure), polish=pol,
                         unavailable_reason="both_candidates_unavailable")
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
                     sel, flags, cands, src.wh, src.em_iterations, src.em_trace, src.quad, nf, pol,
                     rescue=dict(src.rescue or {}))


def two_pass_refit(sp: M.ModelSpec, ds: D.Dataset, r: FitResult, cache: FitCache, info: StartInfo | None = None,
                   recipe: str = "std") -> FitResult:
    """The two-pass scale quadrature (DESIGN §4, declared 25 Oct 2026 for the Codex S3 re-review; the rule is
    `models.QUAD_G_RULE`). Under "17then33" a fitted scale-free model whose fitted s_g EXCEEDS models.QUAD_G_REFIT_SG
    is refitted at models.QUAD_G_REFIT_NODES adaptive nodes by ONE EM chain warm-started from its optimum under its own
    Σ — the full start set is not repeated; the inner solve, the acceptance rule and the EM loop are those of em_fit —
    and the refit replaces it everywhere downstream (it carries quad.n_g_nodes = 33, so selected_spec scores its
    held-out trials at 33 nodes; its archive is the 17-node archive followed by the refit chain). "17then33" is the
    default since 25 Oct 2026 (the frozen S4 rule); under an explicit "17" (the S2 check runs) `r` is returned untouched.
    Models without a scale term, fits already at 33 or more nodes, the prior-centred rule and UNAVAILABLE fits are never
    refitted; a refit that ends UNAVAILABLE is a numerical failure of the standing 17-node result (the required chain was
    lost; nothing to restart from), which therefore leaves the fitter UNAVAILABLE by policy (b). The refit is cached under the 33-node spec with the recipe suffix
    "|refit<from>" so that a blanket 33-node fit and a two-pass refit can never answer for each other."""
    if M.QUAD_G_RULE == "17":
        return r
    if M.QUAD_G_RULE not in M.QUAD_G_RULES:
        raise ValueError(f"unknown models.QUAD_G_RULE {M.QUAD_G_RULE!r}; one of {M.QUAD_G_RULES}")
    if not (sp.scale_free and sp.adaptive_g and r.available and sp.n_g_nodes < M.QUAD_G_REFIT_NODES):
        return r
    s_g = float(M.unpack(sp, r.theta).s_g)
    if not s_g > M.QUAD_G_REFIT_SG:
        return r
    sp33 = replace(sp, n_g_nodes=M.QUAD_G_REFIT_NODES)
    key = cache.key(ds, sp33, f"{recipe}|refit{sp.n_g_nodes}")
    r33 = cache.get(key)
    if r33 is not None:
        return r33
    label = f"refit_g{M.QUAD_G_REFIT_NODES}"
    wh = r.wh if r.wh is not None else ds.wh
    r33 = em_fit(sp33, ds, [], info, em=cache.em, warm=[(label, np.asarray(r.theta, dtype=np.float64), wh)])
    if not r33.available:
        # a refit the rule REQUIRES that fails is a numerical failure of the standing result, not a silent fallback
        r.notes = list(r.notes) + [f"two-pass refit at {M.QUAD_G_REFIT_NODES} scale nodes (s_g {s_g:.3f} > "
                                   f"{M.QUAD_G_REFIT_SG:g}) ended UNAVAILABLE; the {sp.n_g_nodes}-node result stands "
                                   f"(numerical failure: the required refit chain was lost)"]
        _mark_required_chain_lost(r, f"two-pass refit at {M.QUAD_G_REFIT_NODES} scale nodes")
        r.polish = _sum_polish([r.polish, r33.polish])
        return r
    r33.starts = list(r.starts) + list(r33.starts)
    r33.notes = list(r.notes) + list(r33.notes) + [
        f"two-pass refit at {M.QUAD_G_REFIT_NODES} scale nodes from the {sp.n_g_nodes}-node optimum (s_g {s_g:.3f} > "
        f"{M.QUAD_G_REFIT_SG:g}): {r.loglik:.3f} -> {r33.loglik:.3f} nat"]
    r33.quad = dict(_quad_of(sp33), refit_from=int(sp.n_g_nodes), refit_s_g=s_g, loglik_before=float(r.loglik),
                    seconds_before=float(r.seconds))
    r33.seconds = float(r.seconds) + float(r33.seconds)
    r33.numerical_failure = bool(r.numerical_failure or r33.numerical_failure)
    r33.polish = _sum_polish([r.polish, r33.polish])
    cache.put(key, r33)
    return r33


def _inherit_refit(r_new: FitResult, r_old: FitResult) -> FitResult:
    """A rescue chain that replaces a two-pass REFIT keeps the refit's provenance (refit_from, refit_s_g, loglik_before,
    seconds_before) and its archive, so that quad_rule_record still counts it and its seconds split stays readable."""
    q_old = r_old.quad or {}
    if q_old.get("refit_from") is not None and (r_new.quad or {}).get("n_g_nodes") == q_old.get("n_g_nodes"):
        r_new.quad = dict(r_new.quad or {}, **{k: q_old[k] for k in ("refit_from", "refit_s_g", "loglik_before", "seconds_before")
                                                if k in q_old})
    return r_new


def _recipe_of(r: FitResult, recipe: str = "std") -> str:
    """The cache recipe under which a result lives: a two-pass refit carries the `|refit<from>` suffix."""
    q = r.quad or {}
    return f"{recipe}|refit{q['refit_from']}" if q.get("refit_from") is not None else recipe


def quad_rule_record(fits) -> dict:
    """What the scale-quadrature rule did on these FitResults — every result json carries it (DESIGN §4): the rule in
    force, its threshold and node counts, and per model name the fits seen and those refitted at QUAD_G_REFIT_NODES."""
    per = {}
    for r in fits:
        if r is None:
            continue
        c = per.setdefault(r.model, dict(fits=0, refitted=0))
        c["fits"] += 1
        c["refitted"] += int((r.quad or {}).get("refit_from") is not None)
    return dict(rule=M.QUAD_G_RULE, refit_sg=float(M.QUAD_G_REFIT_SG), refit_nodes=int(M.QUAD_G_REFIT_NODES),
                default_nodes=int(M.N_G_NODES), per_model=per)


def fit_all_models(ds: D.Dataset, cache: FitCache | None = None, span_name: str | None = None,
                   models: tuple = FULL_MODELS, quad: dict | None = None, extra_warm: dict | None = None) -> dict:
    """The eight models of §4 on one dataset: {name: FitResult}, selected models built from their candidates;
    also returns the candidates under their spec names. Reduced fits are cached and never refitted. `quad`
    overrides the node counts / rule (n_tau_nodes, n_g_nodes, adaptive_g) for the §4 node checks. After the whole
    cross-family procedure the two-pass scale quadrature (two_pass_refit; models.QUAD_G_RULE, default "17then33"; an
    explicit "17" = no second pass) refits the scale-free candidates whose fitted s_g exceeds the threshold, reapplies
    the cross-family rescues to the pairs touched, and rebuilds the selected models from the refitted candidates. At the
    exit, on EVERY call (25 Oct 2026, policies (b) and (c)): every result with a standing numerical failure becomes
    UNAVAILABLE (finalize_failure), every G/B candidate pair and every selected pair at the same quadrature is read by
    the final nesting guard (one nest rescue for a material deficit; a persistent one is recorded in B's `nesting`), and
    the selected models are rebuilt from the final candidates.
    `extra_warm` = {candidate name: [(label, θ, Whitening)]} further warm EM chains for the candidates (the §4 node
    recheck warm-started from a coarser grid's endpoints); they run beside the twin chains under the same rules."""
    cache = FitCache() if cache is None else cache
    span_name = ds.span.name if span_name is None else span_name
    quad = {} if quad is None else quad
    extra_warm = {} if extra_warm is None else extra_warm
    out = {}
    infos = {}

    def with_extra(name, warm):
        w = list(warm or []) + list(extra_warm.get(name, []))
        return w or None

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

    def reseed_g(sp_g, g_result, sp_b, b_result, info_g, b_name, recipe="std"):
        """A B optimum materially above the G optimum (> RESEED_MIN_NAT, i.e. another basin, not EM noise) re-seeds
        G: B's θ projected onto G's coordinates (the two-state parameters dropped), one EM chain under B's Σ; the
        better G is kept. S2 repair D4 (24 Oct 2026): the rule applies to EVERY such B, collapsed or not. The
        rev 6 + R1-R4 code required every fitted occupancy A(k) ≥ 0.99, which is exactly what never holds when B has
        found a basin that G's chain missed (W2 set 7 m12 fold 0: G3+ −13704.7 below G2 −13453.5 while B3+ reached
        −13316.8, and the rescue never fired); on two-state data the attempt costs one chain and changes nothing.
        A re-seed chain that is lost (UNAVAILABLE) is a numerical failure of the standing G (25 Oct 2026): the rule
        required it, and G may stand under-found. `recipe` = the cache recipe of the result being replaced."""
        if not (b_result.available and g_result.available and b_result.wh is not None):
            return g_result
        if b_result.loglik <= g_result.loglik + RESEED_MIN_NAT:
            return g_result
        PB = M.unpack(sp_b, b_result.theta)
        theta = lift_warm_start(sp_b, b_result.theta, sp_g, info_g, PB.s_tau_ms if sp_g.positive else 20.0)
        r2 = em_fit(sp_g, ds, [], info_g, em=cache.em, warm=[(f"reseed{b_name}", theta, b_result.wh)])
        if r2.available and r2.loglik > g_result.loglik:
            r2.starts = list(g_result.starts) + list(r2.starts)
            r2.notes = list(g_result.notes) + list(r2.notes)
            r2.polish = _sum_polish([g_result.polish, r2.polish])
            r2.numerical_failure = _failure_against(r2.polish["unaccepted_loglik"], r2.loglik, True)
            cache.put(cache.key(ds, sp_g, recipe), _inherit_refit(r2, g_result))
            return r2
        g_result.polish = _sum_polish([g_result.polish, r2.polish])
        if not r2.available:
            g_result.notes = list(g_result.notes) + [f"re-seed chain reseed{b_name} from {b_name} ({b_result.loglik:.3f} nat, "
                                                     f"above G {g_result.loglik:.3f}) ended UNAVAILABLE (numerical failure: "
                                                     f"the required rescue chain was lost)"]
            _mark_required_chain_lost(g_result, f"re-seed from {b_name}")
        return g_result

    def nest_b(sp_b, b_result, g_result, info_b, recipe="std"):
        """After a G re-seed (or a two-pass refit that left B below G), one more B chain from the G point so that
        l(B) >= l(G) holds again. A lost nest chain is a numerical failure of B (25 Oct 2026)."""
        w = warm_from_twin(sp_b, g_result, info_b)
        if w is None:
            return b_result
        r2 = em_fit(sp_b, ds, [], info_b, em=cache.em, warm=w)
        if r2.available and (not b_result.available or r2.loglik > b_result.loglik):
            r2.starts = list(b_result.starts) + list(r2.starts)
            r2.notes = list(b_result.notes) + list(r2.notes)
            r2.polish = _sum_polish([b_result.polish, r2.polish])
            r2.numerical_failure = _failure_against(r2.polish["unaccepted_loglik"], r2.loglik, True)
            cache.put(cache.key(ds, sp_b, recipe), _inherit_refit(r2, b_result))
            return r2
        b_result.polish = _sum_polish([b_result.polish, r2.polish])
        if not r2.available:
            b_result.notes = list(b_result.notes) + [f"nest chain {w[0][0]} from {g_result.model} ({g_result.loglik:.3f} nat) "
                                                     f"ended UNAVAILABLE (numerical failure: the required rescue chain was lost)"]
            _mark_required_chain_lost(b_result, f"nest from {g_result.model}")
        return b_result

    def rescue_pair(gn, bn):
        """The cross-family rescues and the nesting check on a (G, B) candidate pair AFTER the two-pass second pass
        (25 Oct 2026, Codex finding 11: the second pass followed the cross-family loop without rerunning them), each
        model at the quadrature its result records: B below G -> one B chain from G's point under G's Σ (nest_b); B
        above G by more than RESEED_MIN_NAT -> G re-seeded from B, then B nested again from the new G. A pair left with
        l(B) < l(G) at the SAME quadrature is a numerical failure of B; at mixed quadratures (one refitted at 33 nodes,
        the other at 17) the two log-likelihoods are not comparable to NEST_TOL_REL and the deficit is noted only.
        A deficit left at the same quadrature is no longer marked here: the final nesting guard (policy (c)) reads every
        pair at the end of fit_all_models and records it as a nesting failure (25 Oct 2026)."""
        g, b = out[gn], out[bn]
        sp_g, sp_b = selected_spec(gn, g, span_name, quad), selected_spec(bn, b, span_name, quad)
        info_g, info_b = info_for(sp_g), info_for(sp_b)
        rg, rb = _recipe_of(g), _recipe_of(b)

        def below(bb, gg):
            return gg.available and (not bb.available or bb.loglik < gg.loglik - NEST_TOL_REL * max(1.0, abs(gg.loglik)))

        if below(b, g):
            b = nest_b(sp_b, b, g, info_b, rb)
        g_new = reseed_g(sp_g, g, sp_b, b, info_g, bn, rg)
        if g_new is not g:
            g = g_new
            b = nest_b(sp_b, b, g, info_b, rb)
        same_quad = (g.quad or {}).get("n_g_nodes") == (b.quad or {}).get("n_g_nodes")
        if below(b, g):
            txt = (f"nesting after the two-pass rescues: l({bn}) {b.loglik:.3f} below l({gn}) {g.loglik:.3f}"
                   + ("" if same_quad else f" (mixed quadrature {(b.quad or {}).get('n_g_nodes')}/{(g.quad or {}).get('n_g_nodes')} "
                                           "scale nodes: not comparable)"))
            b.notes = list(b.notes) + [txt + (" (left to the final nesting guard)" if same_quad else "")]
        for r_ in (g, b):
            r_.notes = list(r_.notes) + [f"two-pass second pass: cross-family rescues and nesting check reapplied to ({gn}, {bn})"]
        out[gn], out[bn] = g, b

    for name in models:
        if name in M.SELECTED_NAMES:
            red_name, pos_name = M.SELECTED_NAMES[name]
            sp_r, sp_p = M.spec(red_name, span_name, **quad), M.spec(pos_name, span_name, **quad)
            info_r, info_p = info_for(sp_r), info_for(sp_p)
            tw_r, tw_p = g_twin(red_name), g_twin(name)
            red = cache.fit(sp_r, ds, info_r, starts=reduced_starts(sp_r, info_r, tw_r, span_name, quad),
                            warm=with_extra(red_name, warm_from_twin(sp_r, tw_r, info_r) if sp_r.family == "B" else None))
            starts = positive_starts(sp_p, ds, info_p, red, sp_r, tw_p, span_name, quad)
            pos = cache.fit(sp_p, ds, info_p, starts=starts,
                            warm=with_extra(pos_name, warm_from_twin(sp_p, tw_p, info_p) if sp_p.family == "B" else None))
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
                                  warm=with_extra(name, warm_from_twin(sp, tw, info_s) if sp.family == "B" else None))
            if sp.family == "B" and "G" + name[1:] in out:
                g_name = "G" + name[1:]
                sp_gg = M.spec(g_name, span_name, **quad)
                g_new = reseed_g(sp_gg, out[g_name], sp, out[name], info_for(sp_gg), name)
                if g_new is not out[g_name]:
                    out[g_name] = g_new
                    out[name] = nest_b(sp, out[name], g_new, info_s)
    if M.QUAD_G_RULE != "17":
        # the second pass of the two-pass scale quadrature: every scale-free candidate whose fitted s_g exceeds the
        # threshold is refitted at QUAD_G_REFIT_NODES from its own optimum; then (25 Oct 2026) the cross-family rescues
        # and the nesting check are reapplied to every (G, B) pair one of whose members was refitted; then the selected
        # models whose candidates changed are rebuilt (REDUCED/POSITIVE compared at the refitted log-likelihoods)
        changed = set()
        for name in [n for n in out if n in M.MODEL_NAMES]:
            sp = M.spec(name, span_name, **quad)
            if sp.scale_free:
                r2 = two_pass_refit(sp, ds, out[name], cache, info_for(sp))
                if r2 is not out[name]:
                    out[name], changed = r2, changed | {name}
        for bn in [n for n in out if n in M.MODEL_NAMES and n[0] == "B"]:
            gn = "G" + bn[1:]
            if gn in out and changed & {gn, bn}:
                before = (out[gn], out[bn])
                rescue_pair(gn, bn)
                changed |= {n for n, r_, r0 in ((gn, out[gn], before[0]), (bn, out[bn], before[1])) if r_ is not r0}
        for name in [n for n in out if n in M.SELECTED_NAMES]:
            red_name, pos_name = M.SELECTED_NAMES[name]
            if changed & {red_name, pos_name} and red_name in out and pos_name in out:
                out[name] = select(name, out[red_name], out[pos_name], selected_spec(pos_name, out[pos_name], span_name, quad))

    # ---- the exit of the fitter (25 Oct 2026; module constants, policies (b) and (c)) ----
    def rebuild_selected():
        for name in [n for n in out if n in M.SELECTED_NAMES]:
            red_name, pos_name = M.SELECTED_NAMES[name]
            if red_name in out and pos_name in out:
                out[name] = select(name, out[red_name], out[pos_name], selected_spec(pos_name, out[pos_name], span_name, quad))

    def reading(g, b):
        qg, qb = g.quad or {}, b.quad or {}
        same = (qg.get("n_g_nodes"), qg.get("n_tau_nodes")) == (qb.get("n_g_nodes"), qb.get("n_tau_nodes"))
        tol = NEST_TOL_REL * max(1.0, abs(g.loglik))
        d = float(b.loglik - g.loglik)
        return d, tol, same, bool(same and d < -tol)

    def guard(gn, bn, target):
        """One G/B pair: a material matched-quadrature deficit gets the nest rescue of `target` (bn itself, or for a selected
        pair the B candidate of the kind G selected) from G's point under G's Σ; the reading is recorded on out[bn]."""
        g, b = out[gn], out[bn]
        if not (g.available and b.available):
            return
        d, tol, same, material = reading(g, b)
        d0, rescued = d, False
        if material:
            sp_t = selected_spec(target, out[target], span_name, quad)
            nb = finalize_failure(nest_b(sp_t, out[target], g, info_for(sp_t), _recipe_of(out[target])))
            rescued = nb is not out[target] or nb.loglik != out[target].loglik
            out[target] = nb
            if target != bn:
                rebuild_selected()
            b = out[bn]
            if b.available:
                d, tol, same, material = reading(g, b)
        if not b.available:
            return
        b.nesting = dict(vs=gn, deficit=d, deficit_before_rescue=d0, tol=tol, same_quad=same, rescued=bool(rescued),
                         failure=bool(material), g_loglik=float(g.loglik), b_loglik=float(b.loglik))
        if material:
            b.notes = list(b.notes) + [f"NESTING FAILURE (final guard): l({bn}) {b.loglik:.3f} below l({gn}) {g.loglik:.3f} by "
                                       f"{-d:.3g} nat after the nest rescue (tolerance {tol:.3g})"]

    for name in [n for n in out if n in M.MODEL_NAMES]:
        out[name] = finalize_failure(out[name])
    for sfx in ("0", "1+", "2", "3+"):
        if "G" + sfx in out and "B" + sfx in out:
            guard("G" + sfx, "B" + sfx, "B" + sfx)
    rebuild_selected()
    for sfx in ("1", "3"):
        gn, bn = "G" + sfx, "B" + sfx
        if gn in out and bn in out and out[gn].available and out[bn].available:
            tgt = M.SELECTED_NAMES[bn][0 if out[gn].selection == "REDUCED" else 1]
            if tgt in out:
                guard(gn, bn, tgt)
    for name in list(out):
        out[name] = finalize_failure(out[name])
    return out


def nesting_failures(res: dict) -> list:
    """The pairs of a fit_all_models dictionary that the final guard left with a material nesting deficit."""
    return [f"{k}<{(v.nesting or {}).get('vs')}" for k, v in res.items() if v is not None and (v.nesting or {}).get("failure")]


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


def _inner_solve(sp: M.ModelSpec, nxt: D.Dataset, theta: np.ndarray, info: StartInfo | None, options, label: str):
    """One warm-started inner solve of the EM loop on the re-whitened dataset `nxt`. Returns (θ, total log-likelihood,
    starts, seconds, converged) of the start's end point: the CONVERGED optimum, or the best finite end point of a
    NOT_CONVERGED start (θ = None and −inf when nothing finite was reached)."""
    r2 = fit_model(sp, nxt, [(label, theta)], info, options, polish=False)
    if r2.available:
        return r2.theta, r2.loglik, r2.starts, r2.seconds, True
    s = r2.starts[0]
    if s.status == "NONFINITE" or not (np.isfinite(s.f) and np.all(np.isfinite(s.x))):
        return None, -np.inf, r2.starts, r2.seconds, False
    return np.asarray(s.x, dtype=np.float64), -float(s.f), r2.starts, r2.seconds, False


def _em_loop(sp: M.ModelSpec, ds: D.Dataset, r: FitResult, cur: D.Dataset, info: StartInfo | None, options,
             max_iter: int, tol: float, tag: str = "em") -> FitResult:
    """The generalised EM loop from an AVAILABLE fit `r` on `cur` (the same trials as `ds` under some whitening).
    S2 repair D4 (24 Oct 2026): an inner solve that ends NOT_CONVERGED no longer ends the chain outright. Its best
    finite end point is a legitimate generalised-EM step whenever it raises the total log-likelihood (the Σ M-step is
    exact; the θ-step need only not decrease the objective), so it is accepted, noted, and the chain continues —
    the next step's warm start then polishes it. When it does not improve, the solve is retried once from the chain
    point with EM_RETRY_MAXITER_FACTOR times the iteration budget, and only then does the chain stop. Under the
    rev 6 + R1-R4 code the chain broke at the first NOT_CONVERGED solve (W2 sets 0-8: G3+ 6x, G2 4x, B3+ 1x over
    900 folds), leaving G at its starting-Σ optimum while B's chains carried on — the D4 under-finding of G (W2 set 7
    m12 fold 0: G3+ stopped at step 1 at −13704.7, G2 reached −13453.5 in three steps). Every attempt is archived."""
    archive, n_conv, notes, seconds = list(r.starts), r.n_converged, list(r.notes), r.seconds
    for it in range(1, max_iter + 1):
        Sigma = M.m_step_sigma(sp, r.theta, cur)
        wh = D.whitening_from_sigma(cur.wh.mu0, Sigma, 0.0, cur.wh.n_catch)
        nxt = D.rewhiten(ds, wh, f"/{tag}{it}")
        theta2, ll2, st2, sec2, conv2 = _inner_solve(sp, nxt, r.theta, info, options, f"{tag}{it}")
        archive, seconds = archive + list(st2), seconds + sec2
        if not conv2 and not ll2 > r.loglik:
            opts = dict(LBFGSB_OPTIONS if options is None else options)
            opts["maxiter"] = EM_RETRY_MAXITER_FACTOR * int(opts.get("maxiter", LBFGSB_OPTIONS["maxiter"]))
            theta2, ll2, st2, sec2, conv2 = _inner_solve(sp, nxt, r.theta, info, opts, f"{tag}{it}|retry")
            archive, seconds = archive + list(st2), seconds + sec2
            notes.append(f"{tag} step {it}: inner solve not CONVERGED and not improving, retried with "
                         f"{opts['maxiter']} iterations")
        if theta2 is None or ll2 < r.loglik:
            # strictly monotone: a decrease, however small (the adaptive quadrature's nodes move with Σ, so the
            # E-step and the likelihood are not exactly consistent near convergence), ends the chain at `r`
            notes.append(f"{tag} stopped at step {it}: " + ("inner solve not finite" if theta2 is None else
                         f"{'inner solve not CONVERGED, ' if not conv2 else ''}objective fell by {r.loglik - ll2:.3g} nat"))
            break
        if not conv2:
            notes.append(f"{tag} step {it}: inner solve not CONVERGED, accepted as a generalised-EM ascent step "
                         f"(+{ll2 - r.loglik:.3g} nat)")
        gain = ll2 - r.loglik
        trace = r.em_trace + [float(ll2)]
        P = M.unpack(sp, theta2)
        clipped = [] if P.clipped is None else [int(v) for v in P.clipped]
        r = FitResult(sp.name, ds.ident, "AVAILABLE", theta2, ll2, archive, n_conv, seconds, M.code_hash(),
                      _bounds_hit(sp, theta2), clipped, notes, "", [], {}, wh, it, trace, _quad_of(sp),
                      r.numerical_failure, dict(r.polish), lost=r.lost)
        cur = nxt
        if gain <= tol * max(1.0, abs(r.loglik)):
            break
    r.notes, r.starts, r.seconds = notes, archive, seconds
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
    # the numerical-failure verdict is taken against the FINAL result over all chains: a stationary end point that no
    # chain could accept (after its polish) and that stands above the selected log-likelihood — the EM steps may have
    # carried the selected chain past a point lost inside one chain, in which case nothing was lost
    best.polish = _sum_polish([r.polish for _, r in chains])
    un = best.polish["unaccepted_loglik"]
    flagged_in_chain = any(r.numerical_failure for _, r in chains)
    best.numerical_failure = _failure_against(un, best.loglik, best.available)
    best.lost = _best_lost([r.lost for _, r in chains])
    if best.numerical_failure and len(chains) > 1:
        best.notes = list(best.notes) + [f"numerical failure: a stationary end point at {un:.3f} nat in one chain could not "
                                         f"be accepted; the selected chain stands at {best.loglik:.3f} nat"]
    elif flagged_in_chain and not best.numerical_failure:
        best.notes = list(best.notes) + [f"the EM steps carried the selected result ({best.loglik:.3f} nat) past the stationary "
                                         f"end point lost in a chain ({un:.3f} nat): no numerical failure stands"]
    if best.numerical_failure:
        best = _rescue(sp, ds, best, info, options, em, max_iter, tol)
    return best


def _best_lost(eps):
    eps = [e for e in eps if e is not None]
    return max(eps, key=lambda e: e["loglik"]) if eps else None


def _rescue(sp: M.ModelSpec, ds: D.Dataset, best: FitResult, info: StartInfo | None, options, em: bool, max_iter: int,
            tol: float) -> FitResult:
    """Policy (a), the deterministic rescue (25 Oct 2026; see the module constants). `best` ends with a numerical failure:
    a stationary end point (`best.lost`) above its selected log-likelihood that the acceptance rule refused. Each round
    restarts from the best such end point seen so far — its θ under the whitening it was reached on — through fit_model
    with the standard options (the unchanged acceptance rule; the polish included), then the EM loop where EM applies.
    A rescue that is accepted and beats the standing fit (or there was none) becomes the selection; the failure verdict
    is retaken against the combined record, and the loop stops when it is resolved or after RESCUE_ROUNDS rounds. Every
    rescue start is archived. Seeds are the label hashes of run_start: deterministic, no new randomness."""
    ep = best.lost
    rec = dict(kind="lost_end_point", rounds=0, standing_loglik_before=(float(best.loglik) if best.available else None),
               standing_status_before=best.status, lost_loglik=(None if ep is None else float(ep["loglik"])),
               lost_status=(None if ep is None else ep["status"]), lost_label=(None if ep is None else ep["label"]),
               attempts=[], resolved=False)
    cur_best = best
    while cur_best.numerical_failure and ep is not None and rec["rounds"] < RESCUE_ROUNDS:
        rec["rounds"] += 1
        label = f"rescue{rec['rounds']}"
        cur = D.rewhiten(ds, ep["wh"], f"/{label}")
        rr = fit_model(sp, cur, [(label, np.asarray(ep["theta"], dtype=np.float64))], info, options)
        rr.wh, rr.em_iterations, rr.em_trace = ep["wh"], 0, [float(rr.loglik)]
        if em and rr.available:
            rr = _em_loop(sp, ds, rr, cur, info, options, max_iter, tol, tag=label)
        rec["attempts"].append(dict(round=rec["rounds"], start_loglik=float(ep["loglik"]), status=rr.status,
                                    loglik=(float(rr.loglik) if rr.available else None), em_iterations=int(rr.em_iterations)))
        pol = _sum_polish([cur_best.polish, rr.polish])
        lost = _best_lost([cur_best.lost, rr.lost])
        if rr.available and (not cur_best.available or rr.loglik > cur_best.loglik):
            rr.starts = list(cur_best.starts) + list(rr.starts)
            rr.notes = list(cur_best.notes) + list(rr.notes) + [
                f"rescue round {rec['rounds']}: restarted from the lost end point ({ep['loglik']:.3f} nat, {ep['status']}); "
                f"accepted at {rr.loglik:.3f} nat and selected"]
            rr.seconds = float(cur_best.seconds) + float(rr.seconds)
            new = rr
        else:
            new = cur_best
            new.starts = list(new.starts) + list(rr.starts)
            new.seconds = float(new.seconds) + float(rr.seconds)
            new.notes = list(new.notes) + [f"rescue round {rec['rounds']}: restart from the lost end point ({ep['loglik']:.3f} nat) "
                                           f"ended {rr.status}" + (f" at {rr.loglik:.3f} nat, not above the standing fit"
                                                                   if rr.available else "")]
        new.polish = pol
        new.lost = lost
        new.numerical_failure = _failure_against(pol["unaccepted_loglik"], new.loglik, new.available)
        cur_best = new
        ep = lost
    rec["resolved"] = not cur_best.numerical_failure
    rec["loglik_after"] = float(cur_best.loglik) if cur_best.available else None
    cur_best.rescue = rec
    cur_best.notes = list(cur_best.notes) + [
        f"numerical failure {'RESOLVED' if rec['resolved'] else 'UNRESOLVED'} after {rec['rounds']} rescue round(s): standing "
        f"{rec['standing_loglik_before']} -> {rec['loglik_after']} nat (lost end point {rec['lost_loglik']})"]
    return cur_best


def _mark_required_chain_lost(r: FitResult, what: str) -> FitResult:
    """A rescue chain that a rule REQUIRED (two-pass refit, G re-seed, B nest) ended UNAVAILABLE: a numerical failure of the
    standing result with no end point to restart from — unresolved by construction (policy (b) then applies)."""
    r.numerical_failure = True
    if not r.rescue:
        r.rescue = dict(kind="required_chain_lost", chain=what, rounds=0, resolved=False,
                        standing_loglik_before=(float(r.loglik) if r.available else None))
    return r


def finalize_failure(r: FitResult | None) -> FitResult | None:
    """Policy (b): a result whose numerical failure stands after the rescue leaves the fitter UNAVAILABLE with reason
    "numerical_failure" (a copy; the diagnostics — the standing log-likelihood, the lost end point's log-likelihood and
    status — stay in `rescue`). Idempotent; results without a standing failure are returned unchanged (the same object)."""
    if r is None or not r.numerical_failure:
        return r
    if r.available:
        res = dict(r.rescue or {}, standing_loglik=float(r.loglik), standing_status="AVAILABLE")
        res.setdefault("kind", "lost_end_point")
        res.setdefault("resolved", False)
        return replace(r, status="UNAVAILABLE", theta=None, loglik=-np.inf, unavailable_reason="numerical_failure",
                       rescue=res, notes=list(r.notes) + [
                           f"UNAVAILABLE (numerical_failure, policy (b)): the standing fit at {r.loglik:.3f} nat is not used"])
    if r.unavailable_reason in ("", "no_converged_start"):
        return replace(r, unavailable_reason="numerical_failure")
    return r


def usable(r: FitResult | None) -> bool:
    """The only test a downstream reader may apply: AVAILABLE and no standing numerical failure."""
    return bool(r is not None and r.available and not r.numerical_failure)


def finalized(res: dict) -> dict:
    """finalize_failure over a fit_all_models dictionary (a boundary guard for records built from it). Selected models
    whose candidates were finalized are rebuilt only by fit_all_models itself; here a flagged selected result is made
    UNAVAILABLE like any other."""
    return {k: finalize_failure(v) for k, v in res.items()}


def score_heldout(sp: M.ModelSpec, r: FitResult, test: D.Dataset) -> np.ndarray:
    """Per-trial log density of the test trials under the fitted model — whitened with the MODEL's own (μ0, Σ)
    when the fit carries one (EM), else with the test dataset's whitening (the training fold's starting Σ). A fit that
    is not usable (UNAVAILABLE, or a standing numerical failure: policy (b)) is refused — no score may silently come
    from it (25 Oct 2026)."""
    if not usable(r):
        raise ValueError(f"score_heldout: {r.model} is not usable (status {r.status}, numerical_failure {r.numerical_failure})")
    ds = test if (r.wh is None or r.wh is test.wh) else D.rewhiten(test, r.wh, "/model")
    return M.Objective(sp, ds).trial_loglik(r.theta)


def spec_of(result_name: str, span_name: str) -> M.ModelSpec:
    """Spec that evaluates a result's θ: selected names resolve to the candidate that was selected."""
    if result_name in M.SELECTED_NAMES:
        raise ValueError("use selected_spec(result)")
    return M.spec(result_name, span_name)


def selected_spec(name: str, r: FitResult, span_name: str, quad: dict | None = None) -> M.ModelSpec:
    """Spec that evaluates a result's θ: selected names resolve to the candidate that was selected, and the quadrature
    is the one the result RECORDS (`FitResult.quad`: a two-pass refit carries 33 scale nodes, so its held-out trials
    are scored at 33 nodes), falling back to the caller's `quad` override for records without one."""
    quad = {} if quad is None else dict(quad)
    rq = getattr(r, "quad", None) if r is not None else None
    if rq:
        quad.update({k: rq[k] for k in ("n_tau_nodes", "n_g_nodes", "adaptive_g") if k in rq})
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
            if not usable(r):
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
                       info: StartInfo, n_starts: int = PROFILE_STARTS) -> list:
    """The constrained fit's starts (§5): the warm start and the T_B start with the nearest nuisance start, and with
    `n_starts` = 4 (PROFILE_STARTS, the production rule since 25 Oct 2026) the remaining §5 recipes; `n_starts` = 2 is
    the two-start exception, kept for the S2 validation that rejected it."""
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
                      info: StartInfo | None = None, n_starts: int = PROFILE_STARTS, quad: dict | None = None):
    """Callable s ↦ (ℓ_prof(s) or None if UNAVAILABLE, FitResult) for decide.hull_search. The s = 0 point is the
    cached reduced fit (G2/B2). Every constrained fit goes through the two-pass scale quadrature as well
    (two_pass_refit), so that under "17then33" (the default) the profile's constrained fits obey the same rule as the
    unrestricted fit they are compared with — the s = 0 point then resolves to the same refitted reduced fit that
    fit_all_models produced. The constrained spec's latency nodes and scale rule are the UNRESTRICTED fit's own (its
    recorded quadrature: n_tau_nodes, adaptive_g, and the pre-refit scale node count), else `quad`, else the module
    defaults — never a separately bound default (Codex S3 re-review finding 6). Production uses PROFILE_STARTS = 4
    starts. Every point leaves through finalize_failure (policy (b))."""
    q = {} if quad is None else dict(quad)
    uq = getattr(unrestricted, "quad", None) or {}
    for k in ("n_tau_nodes", "adaptive_g"):
        if k in uq:
            q[k] = uq[k]
    if "n_g_nodes" in uq:
        q["n_g_nodes"] = int(uq.get("refit_from") or uq["n_g_nodes"])
    sp_full = M.spec(family + "3+", span_name, **q)
    sp_u = selected_spec(family + "3", unrestricted, span_name, q)
    info = start_info(sp_full, ds) if info is None else info
    log = {}

    def evaluate(s_ms: float):
        sp_c = sp_full.constrained(s_ms)
        if s_ms <= 0.0:
            r = two_pass_refit(sp_c, ds, cache.fit(sp_c, ds, info), cache, info)
        else:
            starts = constrained_starts(sp_full, sp_c, unrestricted, sp_u, info, n_starts)
            r = cache.fit(sp_c, ds, info, recipe=f"prof{n_starts}", starts=starts)
            r = two_pass_refit(sp_c, ds, r, cache, info, recipe=f"prof{n_starts}")
        r = finalize_failure(r)
        log[float(s_ms)] = r
        return (r.loglik if usable(r) else None), r

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
    the FitResults under 'fits'. The generator fits use μ0 and the 53 × 53 LEDOIT-WOLF Σ from all catch trials, as
    §7.1 says — NOT the per-model EM Σ of the primary-span fits (S2 finding D5, 24 Oct 2026: under a free 53 × 53 Σ
    estimated from about 900 trials the S10 G3 generator fit returned s_τ 24.7 ms, s_g 0.00 against 82.2 ms, 0.56
    under Ledoit-Wolf — the full covariance absorbs the trial variability the generators exist to carry, and B3
    collapsed onto G3). An EM cache is refused so that this cannot recur silently."""
    cache = FitCache(em=False) if cache is None else cache
    if cache.em:
        raise ValueError("generator fits use the Ledoit-Wolf Σ (DESIGN §7.1); pass FitCache(em=False)")
    ds = D.full_dataset(p, D.span("whole"), method="lw")      # §7.1 explicitly; the default "scaled" is the EM start
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


# ----------------------------------------------------------------------------------------------
# the run record (25 Oct 2026, Codex S3 re-review finding 6): the numerical contract a production run executes
# ----------------------------------------------------------------------------------------------
RUN_CONFIG_NAME = "run_config.json"
RUNNER_FILES = ("s2.py", "s4.py", "s5.py")


def _cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def runner_hash() -> str:
    """sha256 over the stage runners (s2.py, s4.py, s5.py) beside this module — the part of the bundle that
    models.code_hash() (the five fitting modules) does not cover."""
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in RUNNER_FILES:
        p = os.path.join(here, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:12]


def run_config(gen_dir: str) -> dict:
    """The numerical contract of this process: the trial chunk actually in force (models.TRIAL_CHUNK, read from
    JITTER_TRIAL_CHUNK at import), latency and scale node counts, the scale rule with its threshold and refit nodes, the
    profile starts, the rescue rounds and nesting tolerance, the software versions (numpy, scipy, jax, jaxlib, joblib,
    pandas, python), the machine and CPU model
    (/proc/cpuinfo where present), the fitter's code hash and the sha256 of every generator asset in `gen_dir`. The
    `fingerprint` (config_fingerprint) covers exactly these keys; `runner_hash`, `host`, `utc` and the raw environment
    value are recorded beside it and are not part of it."""
    import platform
    import scipy
    import jax
    import jaxlib
    gens = {}
    if gen_dir and os.path.isdir(gen_dir):
        for fn in sorted(os.listdir(gen_dir)):
            p = os.path.join(gen_dir, fn)
            if fn.startswith(".") or ".tmp" in fn or not os.path.isfile(p):
                continue
            gens[fn] = _sha256_file(p)
    versions = dict(numpy=np.__version__, scipy=scipy.__version__, jax=jax.__version__, jaxlib=jaxlib.__version__,
                    python=platform.python_version())
    for mod in ("joblib", "pandas"):
        try:
            versions[mod] = __import__(mod).__version__
        except ImportError:
            versions[mod] = None
    return dict(trial_chunk=int(M.TRIAL_CHUNK), n_tau_nodes=int(M.N_TAU_NODES), n_g_nodes=int(M.N_G_NODES),
                quad_g_rule=str(M.QUAD_G_RULE), quad_g_refit_sg=float(M.QUAD_G_REFIT_SG),
                quad_g_refit_nodes=int(M.QUAD_G_REFIT_NODES), profile_starts=int(PROFILE_STARTS),
                rescue_rounds=int(RESCUE_ROUNDS), nest_tol_rel=float(NEST_TOL_REL),
                versions=versions, machine=platform.machine(), cpu_model=_cpu_model(), code_hash=M.code_hash(), generators=gens)


def config_fingerprint(cfg: dict) -> str:
    keys = ("trial_chunk", "n_tau_nodes", "n_g_nodes", "quad_g_rule", "quad_g_refit_sg", "quad_g_refit_nodes",
            "profile_starts", "rescue_rounds", "nest_tol_rel", "versions", "machine", "cpu_model", "code_hash", "generators")
    blob = json.dumps({k: cfg.get(k) for k in keys}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def run_record(gen_dir: str) -> dict:
    """run_config + its fingerprint + the unfingerprinted context (runner hash, host, utc, the raw environment value)."""
    import socket
    cfg = run_config(gen_dir)
    return dict(cfg, fingerprint=config_fingerprint(cfg), runner_hash=runner_hash(), host=socket.gethostname(),
                trial_chunk_env=os.environ.get("JITTER_TRIAL_CHUNK"), utc=_time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime()))


_FINGERPRINTS = {}


def run_fingerprint(gen_dir: str) -> str:
    """This process's fingerprint (computed once per process and generator directory; every task record carries it)."""
    if gen_dir not in _FINGERPRINTS:
        _FINGERPRINTS[gen_dir] = config_fingerprint(run_config(gen_dir))
    return _FINGERPRINTS[gen_dir]


class RunConfigMismatch(SystemExit):
    """A resumed or dependent run whose numerical contract differs from the recorded one."""


def config_differences(a: dict, b: dict) -> list:
    keys = ("trial_chunk", "n_tau_nodes", "n_g_nodes", "quad_g_rule", "quad_g_refit_sg", "quad_g_refit_nodes",
            "profile_starts", "rescue_rounds", "nest_tol_rel", "versions", "machine", "cpu_model", "code_hash")
    out = [f"{k}: recorded {a.get(k)!r}, this process {b.get(k)!r}" for k in keys if a.get(k) != b.get(k)]
    ga, gb = a.get("generators") or {}, b.get("generators") or {}
    for fn in sorted(set(ga) | set(gb)):
        if ga.get(fn) != gb.get(fn):
            out.append(f"generator asset {fn}: recorded {str(ga.get(fn))[:12]}, this process {str(gb.get(fn))[:12]}")
    return out


def ensure_run_record(directory: str, gen_dir: str, label: str, check_runner: bool = True) -> dict:
    """At the first start of a run: write <directory>/run_config.json. On a resume: refuse (RunConfigMismatch, a clear
    message naming every difference) unless this process's fingerprint — and, with `check_runner`, the runner hash —
    equals the recorded one. Returns the record in force."""
    path = os.path.join(directory, RUN_CONFIG_NAME)
    cur = run_record(gen_dir)
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)
        diffs = config_differences(old, cur) if old.get("fingerprint") != cur["fingerprint"] else []
        if old.get("fingerprint") != cur["fingerprint"] and not diffs:
            diffs = [f"fingerprint: recorded {old.get('fingerprint')}, this process {cur['fingerprint']}"]
        if check_runner and old.get("runner_hash") != cur["runner_hash"]:
            diffs.append(f"runner_hash (s2/s4/s5): recorded {old.get('runner_hash')}, this process {cur['runner_hash']}")
        if diffs:
            raise RunConfigMismatch(f"{label} refused: this process does not match the run record {path} "
                                    f"(written {old.get('utc')} on {old.get('host')}):\n  - " + "\n  - ".join(diffs) +
                                    "\nResume only with the recorded bundle and environment (e.g. export JITTER_TRIAL_CHUNK=64), "
                                    "or start a new run in a fresh directory.")
        return old
    os.makedirs(directory, exist_ok=True)
    tmp = path + f".tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(cur, f, indent=1)
    os.replace(tmp, path)
    return cur

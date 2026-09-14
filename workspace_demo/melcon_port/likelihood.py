#!/usr/bin/env python3
"""The likelihoods of the planned secondary analysis on Melcón et al. 2024 — PREREG_secondary_melcon.md §6, DRAFT v4
(Codex, continuation review 3, V3.3). Nothing here reads EEG: the inputs are one window's projections of a training
block and a test block (from decoder.py) with each trial's log contrast, catch flag and hemifield.

Densities (x = scaled log contrast, h = 1 for a Gabor in the right hemifield and 0 otherwise, lg = logistic):
  null      y ~ N(mu0 + beta h, sigma0^2)
  graded    y ~ N(a0 + a1 L + beta h, exp(s0 + r L)^2),   L = lg(k (x - x0));   catch: N(a0, exp(s0)^2)
  twostate  y ~ (1 - A) N(mu_l + beta h, sigma^2) + A N(mu_l + e^d0 + e^d1 H + beta h, sigma^2),
            A = lg(k_a (x - x0)), H = lg(k_h (x - x0));   catch: N(mu_l, sigma^2)
  twostate_catch (sensitivity 3'L): twostate, and on catch trials (1 - pi0) N(mu_l, sigma^2) + pi0 N(mu_l + e^d0, sigma^2),
            pi0 = lg(theta0)
Catch trials carry no hemifield term: no stimulus was displayed, and in the nocue task their side code is a virtual
side from the event mapping. The graded spread moves with the same logistic as the mean, its full-range change
bounded to a factor of ten (|r| <= ln 10), so every density is finite by construction (DRAFT v3's s1 (mu - a0) could
span e^-20 .. e^20). v3's per-block location shift gamma is removed: with one training block it is an alias of the
intercept (a0' = a0 + gamma reproduces every density), so it adjusted nothing.

Scaling, from the TRAINING block only: x = (log c - m) / s with m, s the mean and SD of the present trials' log
contrast; S and ybar the SD and mean of the training block's window values over all its retained trials (after the
decoder's training-only z-score, the 10 Hz smoother and the window mean). Floors: fewer than MIN_CATCH catch trials, or
fewer than MIN_SIDE present trials in either hemifield, or s < X_SD_FLOOR, or S < S_FLOOR, make the fold unavailable.

Fitting: L-BFGS-B on analytic gradients within box bounds (bounds()). Starts: one moment start (moment_start()) moved
to the interior (INTERIOR of each range from either bound), plus N_JITTER starts jittered by N(0, JITTER_SD) in the
logit coordinate of each bounded range, seeded from (SEED, tags, model). A start is converged when the training
log-likelihood and its gradient are finite and the optimizer reports success or the projected gradient's largest
component is <= PG_TOL. The kept solution is the converged start with the highest training log-likelihood; with none,
RETRY_STARTS more starts at RETRY_JITTER_SD from a second seed; with still none, the model is unavailable for that fold
and window. The held-out density of every test trial must be finite, else unavailable. The number of converged starts
within BASIN_NAT of the kept solution is recorded.

The legacy/quantile sensitivity (legacy_fold_scores) ports the three Sergent likelihoods with the two inherited traps
repaired and every choice frozen in LEGACY.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logit

SEED = 20260913
LOG2PI = math.log(2.0 * math.pi)
N_JITTER = 7
JITTER_SD = 0.25
RETRY_STARTS = 8
RETRY_JITTER_SD = 0.5
INTERIOR = 1e-3
LBFGSB_OPTIONS = dict(ftol=1e-10, gtol=1e-6, maxiter=2000)
PG_TOL = 1e-3
BASIN_NAT = 0.5
S_FLOOR = 1e-8
X_SD_FLOOR = 1e-6
MIN_CATCH = 3
MIN_SIDE = 20
PI0_START = 0.05

PARAMS = {
    "null": ("mu0", "log_sigma0", "beta"),
    "graded": ("a0", "a1", "x0", "log_k", "s0", "r", "beta"),
    "twostate": ("mu_l", "log_sigma", "delta0", "delta1", "x0", "log_k_a", "log_k_h", "beta"),
    "twostate_catch": ("mu_l", "log_sigma", "delta0", "delta1", "x0", "log_k_a", "log_k_h", "beta", "theta0"),
}
MODEL_INDEX = {"null": 0, "graded": 1, "twostate": 2, "twostate_catch": 3}
PRIMARY = ("null", "graded", "twostate")

SPEC = dict(seed=SEED, n_jitter=N_JITTER, jitter_sd=JITTER_SD, retry_starts=RETRY_STARTS, retry_jitter_sd=RETRY_JITTER_SD,
            interior=INTERIOR, lbfgsb=LBFGSB_OPTIONS, pg_tol=PG_TOL, basin_nat=BASIN_NAT, s_floor=S_FLOOR,
            x_sd_floor=X_SD_FLOOR, min_catch=MIN_CATCH, min_side=MIN_SIDE, pi0_start=PI0_START,
            bounds="loc in ybar +- 5S; log sigma in log(0.05S)..log(5S); beta in +-3S; a1 in 0..10S; x0 in +-4; log k in "
                   "log 0.05..log 20; r in +-ln 10; delta in log(0.01S)..log(10S); theta0 in -6..3",
            params=PARAMS)


class Block:
    """One block's trials in one window: projections y, log contrast (NaN on catch trials), catch flag, hemifield."""

    def __init__(self, y, logc, catch, right):
        self.y = np.asarray(y, dtype=float)
        self.logc = np.asarray(logc, dtype=float)
        self.catch = np.asarray(catch, dtype=bool)
        self.right = np.asarray(right, dtype=bool)
        n = self.y.size
        if not (self.logc.size == self.catch.size == self.right.size == n):
            raise ValueError("y, logc, catch and right must have one entry per trial")

    def __len__(self):
        return self.y.size


def scaling(train: Block):
    """The training block's scaling, or the reason the fold is unavailable (a str)."""
    pres = ~train.catch
    if int(train.catch.sum()) < MIN_CATCH:
        return f"fewer than {MIN_CATCH} catch trials in the training block"
    if int((pres & train.right).sum()) < MIN_SIDE or int((pres & ~train.right).sum()) < MIN_SIDE:
        return f"fewer than {MIN_SIDE} present trials in a hemifield of the training block"
    lc = train.logc[pres]
    if not np.all(np.isfinite(lc)):
        return "non-finite log contrast on a present training trial"
    s = float(np.std(lc, ddof=1))
    if not np.isfinite(s) or s < X_SD_FLOOR:
        return "training log contrast has no spread"
    if not np.all(np.isfinite(train.y)):
        return "non-finite training projection"
    S = float(np.std(train.y, ddof=1))
    if not np.isfinite(S) or S < S_FLOOR:
        return "training projections have no spread"
    return dict(m=float(np.mean(lc)), s=s, S=S, ybar=float(np.mean(train.y)))


def design(block: Block, sc: dict) -> dict:
    c = block.catch
    x = np.where(c, 0.0, (np.where(c, 0.0, block.logc) - sc["m"]) / sc["s"])
    h = (block.right & ~c).astype(float)
    return dict(y=block.y, x=x, c=c, h=h)


def bounds(model: str, sc: dict) -> np.ndarray:
    S, yb = sc["S"], sc["ybar"]
    loc = (yb - 5 * S, yb + 5 * S)
    lsig = (math.log(0.05 * S), math.log(5 * S))
    beta = (-3 * S, 3 * S)
    lk = (math.log(0.05), math.log(20.0))
    x0 = (-4.0, 4.0)
    dl = (math.log(0.01 * S), math.log(10 * S))
    b = {
        "null": [loc, lsig, beta],
        "graded": [loc, (0.0, 10 * S), x0, lk, lsig, (-math.log(10.0), math.log(10.0)), beta],
        "twostate": [loc, lsig, dl, dl, x0, lk, lk, beta],
        "twostate_catch": [loc, lsig, dl, dl, x0, lk, lk, beta, (-6.0, 3.0)],
    }[model]
    return np.array(b, dtype=float)


# --- densities with analytic gradients ---------------------------------------------------------------------------

def _gauss(y, mu, ls):
    z = (y - mu) * np.exp(-ls)
    return -0.5 * LOG2PI - ls - 0.5 * z * z, z * np.exp(-ls), z * z - 1.0     # log phi, d/dmu, d/dlog sigma


def loglik(model: str, theta, d: dict, grad: bool = False):
    """Per-trial log-likelihood (n,), and with grad=True the gradient of the SUM with respect to theta."""
    th = np.asarray(theta, dtype=float)
    y, x, c, h = d["y"], d["x"], d["c"], d["h"]
    if model == "null":
        mu0, ls, beta = th
        ll, gm, gs = _gauss(y, mu0 + beta * h, ls)
        if not grad:
            return ll
        return ll, np.array([gm.sum(), gs.sum(), (gm * h).sum()])
    if model == "graded":
        a0, a1, x0, lk, s0, r, beta = th
        k = math.exp(lk)
        u = k * (x - x0)
        L = np.where(c, 0.0, expit(u))
        ll, gm, gs = _gauss(y, a0 + a1 * L + beta * h, s0 + r * L)
        if not grad:
            return ll
        dL = np.where(c, 0.0, (gm * a1 + gs * r) * L * (1.0 - L))
        return ll, np.array([gm.sum(), (gm * L).sum(), (dL * -k).sum(), (dL * u).sum(), gs.sum(), (gs * L).sum(),
                             (gm * h).sum()])
    if model in ("twostate", "twostate_catch"):
        mu_l, ls, d0, d1, x0, lka, lkh, beta = th[:8]
        ka, kh, e0, e1 = math.exp(lka), math.exp(lkh), math.exp(d0), math.exp(d1)
        ua, uh = ka * (x - x0), kh * (x - x0)
        A, H = expit(ua), expit(uh)
        lpl, gl, sl = _gauss(y, mu_l + beta * h, ls)
        lph, gh, sh = _gauss(y, mu_l + e0 + e1 * H + beta * h, ls)
        la, l1a = log_expit(ua), log_expit(-ua)
        llp = np.logaddexp(l1a + lpl, la + lph)
        wh = np.exp(la + lph - llp)
        wl = 1.0 - wh
        if model == "twostate":
            ll = np.where(c, lpl, llp)
            wl_c, wh_c, glc, ghc, slc, shc, dth0 = 1.0, 0.0, gl, gl, sl, sl, None
        else:
            th0 = th[8]
            lpc, gc, sc_ = _gauss(y, mu_l + e0, ls)            # catch rows have h = 0, so mu_l + e0 is the catch high mean
            lpi, l1pi = log_expit(th0), log_expit(-th0)
            llc = np.logaddexp(l1pi + lpl, lpi + lpc)
            ll = np.where(c, llc, llp)
            wh_c = np.exp(lpi + lpc - llc)
            wl_c = 1.0 - wh_c
            glc, ghc, slc, shc = gl, gc, sl, sc_
            pi0 = expit(th0)
            dth0 = np.where(c, wh_c * (1.0 - pi0) - wl_c * pi0, 0.0).sum()
        if not grad:
            return ll
        p = ~c
        dmu = np.where(p, wl * gl + wh * gh, wl_c * glc + wh_c * ghc)
        dls = np.where(p, wl * sl + wh * sh, wl_c * slc + wh_c * shc)
        dd0 = np.where(p, wh * gh * e0, wh_c * ghc * e0)
        dd1 = np.where(p, wh * gh * e1 * H, 0.0)
        dua = np.where(p, wh * (1.0 - A) - wl * A, 0.0)
        duh = np.where(p, wh * gh * e1 * H * (1.0 - H), 0.0)
        g = [dmu.sum(), dls.sum(), dd0.sum(), dd1.sum(), (dua * -ka + duh * -kh).sum(), (dua * ua).sum(),
             (duh * uh).sum(), (dmu * h).sum()]
        if model == "twostate_catch":
            g.append(dth0)
        return ll, np.array(g)
    raise ValueError(f"unknown model {model!r}")


# --- starts and the fit ---------------------------------------------------------------------------------------------

def moment_start(model: str, d: dict, sc: dict) -> np.ndarray:
    """The declared moment start (before the move to the interior)."""
    y, x, c, h = d["y"], d["x"], d["c"], d["h"]
    S = sc["S"]
    pres = ~c
    mc = float(np.mean(y[c]))
    scatch = max(float(np.std(y[c], ddof=1)), 0.05 * S)
    q20, q80 = np.quantile(x[pres], [0.2, 0.8])
    dtop = float(np.mean(y[pres & (x >= q80)]) - np.mean(y[pres & (x <= q20)]))
    b = float(np.mean(y[pres & (h == 1)]) - np.mean(y[pres & (h == 0)]))
    if model == "null":
        return np.array([sc["ybar"], math.log(S), b])
    if model == "graded":
        return np.array([mc, dtop, 0.0, 0.0, math.log(scatch), 0.0, b])
    start = [mc, math.log(scatch), math.log(max(dtop, 0.01 * S)), math.log(max(0.5 * dtop, 0.01 * S)), 0.0, 0.0, 0.0, b]
    if model == "twostate_catch":
        start.append(float(logit(PI0_START)))
    return np.array(start)


def interior(p: np.ndarray, b: np.ndarray) -> np.ndarray:
    lo, hi = b[:, 0], b[:, 1]
    return np.clip(p, lo + INTERIOR * (hi - lo), hi - INTERIOR * (hi - lo))


def jitter(p: np.ndarray, b: np.ndarray, rng: np.random.Generator, sd: float) -> np.ndarray:
    lo, hi = b[:, 0], b[:, 1]
    u = logit((interior(p, b) - lo) / (hi - lo)) + rng.normal(0.0, sd, size=p.size)
    return lo + (hi - lo) * expit(u)


def _projected_gradient(g, x, b):
    lo, hi = b[:, 0], b[:, 1]
    pg = g.copy()
    at_lo = x <= lo + 1e-12 * np.maximum(1.0, np.abs(lo))
    at_hi = x >= hi - 1e-12 * np.maximum(1.0, np.abs(hi))
    pg[at_lo] = np.minimum(g[at_lo], 0.0)
    pg[at_hi] = np.maximum(g[at_hi], 0.0)
    return pg


def _run(model, d, b, x0):
    def f(th):
        ll, g = loglik(model, th, d, grad=True)
        s = float(ll.sum())
        if not np.isfinite(s) or not np.all(np.isfinite(g)):
            return 1e300, np.zeros_like(g)
        return -s, -g
    res = minimize(f, x0, jac=True, method="L-BFGS-B", bounds=[tuple(r) for r in b], options=dict(LBFGSB_OPTIONS))
    ll, g = loglik(model, res.x, d, grad=True)
    s = float(ll.sum())
    finite = bool(np.isfinite(s) and np.all(np.isfinite(g)))
    pg = _projected_gradient(-g, res.x, b) if finite else np.full_like(g, np.inf)
    converged = finite and (bool(res.success) or float(np.max(np.abs(pg))) <= PG_TOL)
    return dict(theta=np.asarray(res.x), loglik=s if finite else -np.inf, converged=converged, success=bool(res.success),
                pg=float(np.max(np.abs(pg))), nit=int(res.nit), start=np.asarray(x0))


def fit(model: str, d: dict, sc: dict, tags=()) -> dict:
    b = bounds(model, sc)
    p0 = interior(moment_start(model, d, sc), b)
    rng = np.random.default_rng(np.random.SeedSequence([SEED, *[int(t) for t in tags], MODEL_INDEX[model]]))
    starts = [p0] + [jitter(p0, b, rng, JITTER_SD) for _ in range(N_JITTER)]
    runs = [_run(model, d, b, s) for s in starts]
    retry = False
    if not any(r["converged"] for r in runs):
        retry = True
        rng2 = np.random.default_rng(np.random.SeedSequence([SEED, *[int(t) for t in tags], MODEL_INDEX[model], 1]))
        runs += [_run(model, d, b, jitter(p0, b, rng2, RETRY_JITTER_SD)) for _ in range(RETRY_STARTS)]
    conv = [r for r in runs if r["converged"]]
    out = dict(model=model, n_starts=len(runs), n_converged=len(conv), retry=retry)
    if not conv:
        return dict(out, available=False, reason="no converged start")
    best = max(conv, key=lambda r: r["loglik"])
    return dict(out, available=True, reason="", theta=best["theta"], loglik=best["loglik"],
                n_at_best=sum(r["loglik"] >= best["loglik"] - BASIN_NAT for r in conv))


def fold_scores(train: Block, test: Block, tags=(), models=PRIMARY) -> dict:
    """Fit each model on the training block and score the test block: {model: dict(available, reason, heldout, n_test,
    theta, loglik, n_starts, n_converged, n_at_best, retry)}."""
    sc = scaling(train)
    if isinstance(sc, str):
        return {m: dict(model=m, available=False, reason=sc) for m in models}
    if not np.all(np.isfinite(test.logc[~test.catch])) or not np.all(np.isfinite(test.y)):
        return {m: dict(model=m, available=False, reason="non-finite test input") for m in models}
    dtr, dte = design(train, sc), design(test, sc)
    out = {}
    for m in models:
        r = fit(m, dtr, sc, tags)
        if r["available"]:
            ll = loglik(m, r["theta"], dte)
            if not np.all(np.isfinite(ll)):
                r.update(available=False, reason="non-finite held-out density")
            else:
                r.update(heldout=float(ll.sum()), n_test=int(ll.size))
        r["scaling"] = sc
        out[m] = r
    return out


def pi0_report(fit_result: dict) -> dict:
    """The catch-occupancy sensitivity's point estimate with its separation in units of the component SD; a separation
    below 0.5 marks pi0 as weakly identified (reported, not interpreted)."""
    th = fit_result["theta"]
    sep = math.exp(th[2]) / math.exp(th[1])
    return dict(pi0=float(expit(th[8])), separation_sd=float(sep), weakly_identified=bool(sep < 0.5))


# --- the legacy/quantile sensitivity ---------------------------------------------------------------------------------

LEGACY = dict(
    levels="quintile edges (20/40/60/80 %) of the TRAINING block's present log contrast; level = 1 + the number of edges "
           "below the trial's log contrast, for training and test trials alike (outer bins open); catch = level 0 by flag",
    anchor="x_max = 5, the design maximum, in every call (the port used each call's own maximum level)",
    catch="A = 0 and mu_high = mu_low on catch trials by the catch flag (the port used each subset's minimum level)",
    starts="the inherited moment starts (fit_models.py) computed from the training block only",
    optimizer="Nelder-Mead from that single start, xatol = fatol = 1e-4, maxiter = maxfev = 200 x n_params, "
              "non-adaptive; a non-finite start or held-out score makes the model unavailable",
    hemifield="none, as in the inherited models",
    plots="descriptive quintile plots use recording-wide edges over all present trials and are never used for fitting",
)
LEGACY_XMAX = 5.0
SQRT2PI = math.sqrt(2.0 * math.pi)


def legacy_levels(train: Block, block: Block) -> np.ndarray:
    edges = np.quantile(train.logc[~train.catch], [0.2, 0.4, 0.6, 0.8])
    lev = 1.0 + np.searchsorted(edges, np.where(block.catch, -np.inf, block.logc), side="left")
    return np.where(block.catch, 0.0, lev)


def llh_null(pars, y):
    sigma, mu = abs(pars[0]), pars[1]
    if sigma == 0:
        return -np.inf
    return y.size * math.log(1.0 / (sigma * SQRT2PI)) - 0.5 * np.sum((y - mu) ** 2) / sigma ** 2


def llh_logisticB(pars, y, lev):
    x0, k, L, s_slope, s_int, mu_max = pars
    with np.errstate(over="ignore"):
        mu = L / (1.0 + np.exp(-k * (lev - x0))) - L / (1.0 + np.exp(-k * (LEGACY_XMAX - x0))) + mu_max
    sd = np.abs(s_slope * mu + s_int)
    if np.any(sd == 0):
        return -np.inf
    return float(np.sum(np.log(1.0 / (sd * SQRT2PI))) - 0.5 * np.sum((y - mu) ** 2 / sd ** 2))


def llh_bimodal(pars, y, lev, catch):
    x0, k, mu_low, step, L_high, k_high, sigma = pars
    sigma = abs(sigma)
    if sigma == 0:
        return -np.inf
    with np.errstate(over="ignore"):
        A = np.where(catch, 0.0, 1.0 / (1.0 + np.exp(-k * (lev - x0))))
        mu_high = np.where(catch, mu_low, L_high / (1.0 + np.exp(-k_high * (lev - x0))) + step)
        g_low = np.exp(-0.5 * ((y - mu_low) / sigma) ** 2) / (sigma * SQRT2PI)
        g_high = np.exp(-0.5 * ((y - mu_high) / sigma) ** 2) / (sigma * SQRT2PI)
    with np.errstate(divide="ignore"):
        return float(np.sum(np.log((1.0 - A) * g_low + A * g_high)))


def _nelder_mead(negf, x0):
    x0 = np.asarray(x0, dtype=float)
    n = x0.size
    res = minimize(negf, x0, method="Nelder-Mead",
                   options=dict(xatol=1e-4, fatol=1e-4, maxiter=200 * n, maxfev=200 * n, adaptive=False, disp=False))
    return res.x


def legacy_fold_scores(train: Block, test: Block) -> dict:
    lt, le = legacy_levels(train, train), legacy_levels(train, test)
    y, yt, ct, ce = train.y, test.y, train.catch, test.catch
    out = {}

    def mean_sd(mask):
        return float(np.mean(y[mask])), float(np.std(y[mask], ddof=1))
    try:
        m_max, s_max = mean_sd(lt == 5)
        m_min, s_min = mean_sd(lt == 1)
        m_noise, s_noise = mean_sd(ct)
    except Exception:                                  # an empty level leaves no start
        return {m: dict(available=False, reason="a legacy level is empty in the training block")
                for m in ("model0", "model2B", "model3")}
    starts = {
        "model0": np.array([1.0, 0.0]),
        "model2B": np.array([3.0, (m_max - m_min) / 4.0, 2.0 * m_max, (s_max - s_min) / (m_max - m_min),
                             s_max - (s_max - s_min) / (m_max - m_min) * m_max, m_max]),
        "model3": np.array([3.0, (m_max - m_min) / 4.0, m_noise, m_min - m_noise, m_max - m_min, (m_max - m_min) / 4.0,
                            s_noise]),
    }
    funcs = {
        "model0": (lambda p: llh_null(p, y), lambda p: llh_null(p, yt)),
        "model2B": (lambda p: llh_logisticB(p, y, lt), lambda p: llh_logisticB(p, yt, le)),
        "model3": (lambda p: llh_bimodal(p, y, lt, ct), lambda p: llh_bimodal(p, yt, le, ce)),
    }
    for m, (ftr, fte) in funcs.items():
        if not np.all(np.isfinite(starts[m])):
            out[m] = dict(available=False, reason="non-finite legacy start")
            continue
        p = _nelder_mead(lambda q: -ftr(q), starts[m])
        score = fte(p)
        out[m] = (dict(available=True, reason="", heldout=float(score), n_test=int(yt.size), theta=p)
                  if np.isfinite(score) else dict(available=False, reason="non-finite legacy held-out score"))
    return out

#!/usr/bin/env python3
"""How precisely can the margin be measured? (round 3, Reviewer 1 request 5(a),(b))

Reviewer 1: "No uncertainty is given for the estimated margin, although its early-warning
role depends on it. Near the boundary the margin is a small difference between two large,
noisy rates." He asks for (a) a precision analysis -- delta method or bootstrap for the
margin, the capacity ratio and the implied P_c -- and (b) the observation span needed for
a given relative precision. His worked example: with mu = 10 and lambda = 9.5 per week,
one year of counts gives a standard error of about 0.6 per week against a margin of 0.5
per week, and resolving the post-increase margin of 0.025 per week needs several centuries.

This script establishes five things, in order.

1. THE DELTA METHOD, with the joint covariance kept. The Figure 1 estimators are
   lambda_hat = arrivals / elapsed time and mu_hat = completions / server-busy time. Under
   the counting approximation,

       Var(lambda_hat) = c_a^2 * lambda / tau
       Var(mu_hat)     = c_s^2 * mu^2 / (lambda * tau)
       Var(margin)     = Var(lambda_hat) + Var(mu_hat) - 2 Cov(lambda_hat, mu_hat)
       Var(CR)         = [Var(lambda_hat) + CR^2 Var(mu_hat) - 2 CR Cov] / mu^2
       Var(P_c)        = (dt * exp(-margin * dt))^2 * Var(margin)

   At c_a^2 = c_s^2 = 1 the margin variance is the reviewer's (lambda + mu^2/lambda)/tau.
   The covariance term is carried through every formula instead of being assumed away, and
   is then measured: for THIS estimator pair the service-completion fluctuation is
   orthogonal to the arrival counts, so the correlation should vanish as the window grows.
   That is a property of the pair, not a licence to drop the term -- a mu_hat formed as
   throughput over elapsed time would be strongly correlated with lambda_hat.

2. VALIDATION against replicated event logs at the Section 7 loads, for M/M/1, M/D/1 and
   H2/M/1, so that the c_a^2 and c_s^2 dependence is exercised: the predicted standard
   errors are compared with the spread over independent replications.

3. BOOTSTRAP on a single log: an i.i.d. resample of the interarrival and service times,
   and a moving-block resample at several block lengths. The two agree for the two rates,
   which are i.i.d. by construction. They do not agree for the deadline-success fraction
   measured directly from sojourn times, because sojourn times are autocorrelated; the
   block length at which the bootstrap standard error stops rising measures how few
   independent observations a long log really contains.

4. THE OBSERVATION SPAN, with its criterion declared. "Resolve" is meaningless without
   one. For a standard error of eps * margin, tau >= (c_a^2 lambda + c_s^2 mu^2/lambda) /
   (eps * margin)^2; a 95% half-width of eps * margin needs 1.96^2 times that exposure.
   The spans are printed beside the queue's own relaxation time mu^-1 (1-sqrt(CR))^-2,
   because the stationary formula being estimated is only valid over a window in which the
   queue has settled, and both quantities diverge as margin^-2.

5. THE REVIEW BOARD of the Introduction, simulated. Over many independent years of the
   same board, how often does the estimated margin have the wrong sign, how often does its
   95% interval contain zero, and what does a naive pipeline report if it clips an invalid
   margin to a positive value before forming P_c? No invalid probability is clipped into
   evidence here; where the confidence set reaches lambda >= mu, the stationary P_c is
   reported as not identified on that part of the set.

Usage:
    python3 margin_precision.py [--reps 48] [--out margin_precision.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

MU = 1.0              # service rate, as in Section 7
DT = 4.0              # certification horizon Delta t
LOADS = (0.50, 0.70, 0.85, 0.94)
N_ARRIVALS = 200_000
WARMUP = 50_000
SCV_A_H2 = 4.0        # the H2 interarrival law of the paper's panel (b)

# squared coefficients of variation of the interarrival and service laws
SCV = {"MM1": (1.0, 1.0), "MD1": (1.0, 0.0), "H2M1": (SCV_A_H2, 1.0)}

WEEKS_PER_YEAR = 52.0   # the convention of the Introduction's weekly rates


# ------------------------------------------------- the margin-to-P_c mapping
def gim1_root(lam, mu, scv_a):
    """Root sigma in (0,1) of sigma = E[exp(-mu(1-sigma)A)] for the H2 arrival law.

    Same bisection as figures/rsc_simulation.py:gim1_root, with mu a parameter.
    """
    p1 = 0.5 * (1.0 + math.sqrt((scv_a - 1.0) / (scv_a + 1.0)))
    p2 = 1.0 - p1
    r1, r2 = 2.0 * p1 * lam, 2.0 * p2 * lam

    def f(z):
        s = mu * (1.0 - z)
        return p1 * r1 / (r1 + s) + p2 * r2 / (r2 + s) - z

    a, b = 1e-12, 1.0 - 1e-12
    for _ in range(200):
        m = 0.5 * (a + b)
        if f(m) > 0.0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def gim1_root_algebraic(cr, scv_a):
    """The same root from the quadratic of Supplementary S3.4, as an independent check:
    (1-sigma)^2 + (2 CR - 1)(1-sigma) - 2 CR (1-CR)/(c_a^2+1) = 0."""
    b = 2.0 * cr - 1.0
    c = -2.0 * cr * (1.0 - cr) / (scv_a + 1.0)
    x = 0.5 * (-b + math.sqrt(b * b - 4.0 * c))
    return 1.0 - x


def pc_from_rates(lam, mu, kind, dt=DT):
    """The deadline probability the model implies for a pair of estimated rates.

    M/M/1: exact, with the sojourn decay rate equal to the margin itself
    (Proposition 1(d) with sigma = CR). H2/M/1: exact, with the decay rate mu(1-sigma)
    of the GI/M/1 root, which is NOT the margin. M/D/1: the sojourn distribution has no
    elementary closed form, so no implied value is reported.
    """
    if lam <= 0 or mu <= lam:
        return float("nan")           # no stationary sojourn law above the boundary
    if kind == "MM1":
        return 1.0 - math.exp(-(mu - lam) * dt)
    if kind == "H2M1":
        return 1.0 - math.exp(-mu * (1.0 - gim1_root(lam, mu, SCV_A_H2)) * dt)
    return float("nan")


def pc_gradient(lam, mu, kind, dt=DT, h=1e-6):
    """(dP_c/dlambda, dP_c/dmu) by central differences on pc_from_rates."""
    if pc_from_rates(lam, mu, kind, dt) != pc_from_rates(lam, mu, kind, dt):
        return float("nan"), float("nan")
    gl = (pc_from_rates(lam + h, mu, kind, dt) -
          pc_from_rates(lam - h, mu, kind, dt)) / (2 * h)
    gm = (pc_from_rates(lam, mu + h, kind, dt) -
          pc_from_rates(lam, mu - h, kind, dt)) / (2 * h)
    return gl, gm


# ---------------------------------------------------------------- simulation
def hyperexp(rng, rate, scv, n):
    """Two-phase hyperexponential draws, balanced means (as rsc_simulation.py)."""
    p1 = 0.5 * (1.0 + math.sqrt((scv - 1.0) / (scv + 1.0)))
    p2 = 1.0 - p1
    pick = rng.random(n) < p1
    r = np.where(pick, 2.0 * p1 * rate, 2.0 * p2 * rate)
    return rng.exponential(1.0 / r)


def draw_times(rng, rho, kind, n, mu=MU):
    lam = rho * mu
    if kind == "MM1":
        return rng.exponential(1.0 / lam, n), rng.exponential(1.0 / mu, n)
    if kind == "MD1":
        return rng.exponential(1.0 / lam, n), np.full(n, 1.0 / mu)
    if kind == "H2M1":
        return hyperexp(rng, lam, SCV_A_H2, n), rng.exponential(1.0 / mu, n)
    raise ValueError(kind)


def build_log(interarr, service):
    """Event log of an FCFS single server, vectorized.

    The loop in estimator_calibration.simulate_log is completion_i =
    max(completion_{i-1}, arrival_i) + service_i. Writing P_i for the cumulative service
    time, that recursion solves as completion_i = P_i + max_{j<=i}(arrival_j - P_{j-1}),
    which is a running maximum. check_vectorization() below asserts the two agree.
    """
    arrival = np.cumsum(interarr)
    P = np.cumsum(service)
    P_prev = P - service
    completion = P + np.maximum.accumulate(arrival - P_prev)
    start = completion - service
    return dict(arrival=arrival, start=start, completion=completion,
                service=service, interarr=interarr)


def check_vectorization(n=5_000, seed=11):
    """The vectorized log must equal the released loop implementation."""
    from estimator_calibration import simulate_log
    rng = np.random.default_rng(seed)
    loop = simulate_log(rng, 0.85, "MM1", n=n)
    # the same interarrival and service draws, recovered from the loop's own log
    vec = build_log(np.diff(loop["arrival"], prepend=0.0), loop["service"])
    same_c = np.allclose(loop["completion"], vec["completion"], rtol=0, atol=1e-9)
    same_s = np.allclose(loop["start"], vec["start"], rtol=0, atol=1e-9)
    return bool(same_c and same_s)


def _overlap(a, b, t0, t1):
    return np.maximum(np.minimum(b, t1) - np.maximum(a, t0), 0.0)


def estimate(log, t0, t1, dt=DT):
    """The Figure 1 estimators over the window [t0, t1], from the log alone."""
    arrival, start, completion = log["arrival"], log["start"], log["completion"]
    window = t1 - t0
    n_arr = int(np.sum((arrival >= t0) & (arrival < t1)))
    lam_hat = n_arr / window

    done = (completion >= t0) & (completion < t1)
    n_comp = int(np.sum(done))
    busy = float(np.sum(_overlap(start, completion, t0, t1)))
    mu_hat = n_comp / busy if busy > 0 else float("nan")

    sojourn = completion[done] - arrival[done]
    pc_direct = float(np.mean(sojourn <= dt)) if sojourn.size else float("nan")

    margin = mu_hat - lam_hat
    cr = lam_hat / mu_hat
    return dict(lam_hat=lam_hat, mu_hat=mu_hat, margin=margin, cr=cr,
                pc_direct=pc_direct, pc_implied=1.0 - math.exp(-margin * dt),
                n_arrivals=n_arr, n_completions=n_comp, window=window,
                sojourn=sojourn)


# --------------------------------------------------------------- delta method
def analytic_var(lam, mu, tau, scv_a, scv_s, cov=0.0, kind="MM1"):
    """Counting-approximation variances, with the covariance carried through.

    The implied deadline probability uses the gradient of the queue's own mapping from
    the two rates to P_c, so that Var(P_c) = g_l^2 V_l + g_m^2 V_m + 2 g_l g_m Cov. For
    M/M/1 that reduces to (dt e^{-M dt})^2 Var(margin).
    """
    v_lam = scv_a * lam / tau
    v_mu = scv_s * mu ** 2 / (lam * tau)
    v_margin = v_lam + v_mu - 2.0 * cov
    cr = lam / mu
    v_cr = (v_lam + cr ** 2 * v_mu - 2.0 * cr * cov) / mu ** 2
    gl, gm = pc_gradient(lam, mu, kind)
    v_pc = (gl ** 2 * v_lam + gm ** 2 * v_mu + 2.0 * gl * gm * cov
            if gl == gl else float("nan"))
    return dict(v_lam=v_lam, v_mu=v_mu, cov=cov, v_margin=v_margin, v_cr=v_cr,
                v_pc=v_pc, pc_grad=[gl, gm], se_lam=math.sqrt(v_lam),
                se_mu=math.sqrt(v_mu), se_margin=math.sqrt(v_margin),
                se_cr=math.sqrt(v_cr),
                se_pc=math.sqrt(v_pc) if v_pc == v_pc and v_pc >= 0
                else float("nan"))


def relaxation_time(cr, mu=MU):
    """The M/M/1 relaxation time of Section 6.2: mu^-1 (1 - sqrt(CR))^-2."""
    return 1.0 / (mu * (1.0 - math.sqrt(cr)) ** 2)


def span_for(lam, mu, scv_a, scv_s, eps, z):
    """Observation span for a half-width of eps*margin at multiplier z."""
    margin = mu - lam
    num = scv_a * lam + scv_s * mu ** 2 / lam
    return z ** 2 * num / (eps * margin) ** 2


# ------------------------------------------------------- 2. replication study
def replication_study(kind, reps, n=N_ARRIVALS, warmup=WARMUP, seed=20261013):
    seeds = np.random.SeedSequence(seed).spawn(reps * len(LOADS))
    scv_a, scv_s = SCV[kind]
    rows, k = [], 0
    for rho in LOADS:
        est = []
        for _ in range(reps):
            rng = np.random.default_rng(seeds[k]); k += 1
            interarr, service = draw_times(rng, rho, kind, n)
            log = build_log(interarr, service)
            t0 = float(log["arrival"][warmup])
            t1 = float(log["arrival"][-1])
            e = estimate(log, t0, t1)
            e.pop("sojourn")
            e["pc_implied"] = pc_from_rates(e["lam_hat"], e["mu_hat"], kind)
            est.append(e)
        lam = rho * MU
        tau = float(np.mean([e["window"] for e in est]))
        emp = {}
        for key in ("lam_hat", "mu_hat", "margin", "cr", "pc_direct", "pc_implied"):
            v = np.array([e[key] for e in est], float)
            emp[key] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)))
        lv = np.array([e["lam_hat"] for e in est], float)
        mv = np.array([e["mu_hat"] for e in est], float)
        cov_emp = float(np.cov(lv, mv, ddof=1)[0, 1])
        corr = float(np.corrcoef(lv, mv)[0, 1]) if scv_s > 0 else float("nan")
        # Fisher-z 95% interval for the correlation
        if corr == corr and reps > 3 and abs(corr) < 1:
            zf = 0.5 * math.log((1 + corr) / (1 - corr))
            h = 1.96 / math.sqrt(reps - 3)
            corr_ci = [math.tanh(zf - h), math.tanh(zf + h)]
        else:
            corr_ci = [float("nan"), float("nan")]

        pred_zero = analytic_var(lam, MU, tau, scv_a, scv_s, cov=0.0, kind=kind)
        pred_emp = analytic_var(lam, MU, tau, scv_a, scv_s, cov=cov_emp, kind=kind)
        pc_true = pc_from_rates(lam, MU, kind)
        pc_obs = float(np.mean([e["pc_direct"] for e in est]))
        ref = pc_true if pc_true == pc_true else pc_obs
        binom_se = math.sqrt(ref * (1 - ref) /
                             float(np.mean([e["n_completions"] for e in est])))
        rows.append(dict(
            kind=kind, load=rho, reps=reps, window=tau, margin_true=MU - lam,
            cr_true=rho, pc_true=pc_true, empirical=emp,
            cov_empirical=cov_emp, corr=corr, corr_ci95=corr_ci,
            predicted=pred_zero, predicted_with_cov=pred_emp,
            n_completions=float(np.mean([e["n_completions"] for e in est])),
            pc_direct_binomial_se=binom_se,
            pc_direct_vif=(emp["pc_direct"]["sd"] / binom_se) ** 2,
        ))
    return rows


# ------------------------------------------------------------- 3. bootstrap
def block_bootstrap(interarr, service, sojourn, block, n_boot, rng, kind="MM1",
                    dt=DT):
    """Moving-block resample of the per-commitment triples.

    Block length 1 is the ordinary i.i.d. bootstrap. The block length must stay small
    against the series length: overlapping blocks that each cover an appreciable share of
    the series have block means too close to the global mean, and the resample then
    understates the spread. bootstrap_study() keeps block <= n/50 and prints the ratio.
    """
    n = interarr.size
    k = n // block
    starts_max = n - block
    lam_b = np.empty(n_boot); mu_b = np.empty(n_boot); pc_b = np.empty(n_boot)
    idx_block = np.arange(block)
    for b in range(n_boot):
        s = rng.integers(0, starts_max + 1, size=k)
        idx = (s[:, None] + idx_block[None, :]).ravel()
        lam_b[b] = 1.0 / interarr[idx].mean()
        mu_b[b] = 1.0 / service[idx].mean()
        pc_b[b] = (sojourn[idx] <= dt).mean()
    return lam_b, mu_b, pc_b


def bootstrap_study(kind, rho, n=600_000, warmup=WARMUP, n_boot=200,
                    blocks=(1, 100, 1_000, 10_000), seed=20261014):
    rng = np.random.default_rng(seed)
    interarr, service = draw_times(rng, rho, kind, n)
    log = build_log(interarr, service)
    t0 = float(log["arrival"][warmup]); t1 = float(log["arrival"][-1])
    est = estimate(log, t0, t1)
    sl = slice(warmup, n)
    ia, sv = interarr[sl], service[sl]
    soj = (log["completion"] - log["arrival"])[sl]

    out = {}
    usable = ia.size
    for block in blocks:
        if block * 50 > usable:
            continue
        lam_b, mu_b, pc_b = block_bootstrap(ia, sv, soj, block, n_boot, rng, kind)
        margin_b = mu_b - lam_b
        cr_b = lam_b / mu_b
        # the queue's own mapping from the two rates to P_c, not the M/M/1 one
        pc_implied_b = np.array([pc_from_rates(l, m, kind)
                                 for l, m in zip(lam_b, mu_b)])
        with np.errstate(invalid="ignore", divide="ignore"):
            corr_b = float(np.corrcoef(lam_b, mu_b)[0, 1])
        out[str(block)] = dict(
            block_over_n=block / usable,
            se_lam=float(lam_b.std(ddof=1)), se_mu=float(mu_b.std(ddof=1)),
            se_margin=float(margin_b.std(ddof=1)), se_cr=float(cr_b.std(ddof=1)),
            se_pc_implied=float(pc_implied_b.std(ddof=1)),
            se_pc_direct=float(pc_b.std(ddof=1)),
            margin_ci95=[float(np.quantile(margin_b, 0.025)),
                         float(np.quantile(margin_b, 0.975))],
            corr_lam_mu=corr_b,
        )
    # sojourn autocorrelation, for the dependence story
    x = soj - soj.mean()
    denom = float(np.dot(x, x))
    acf = [float(np.dot(x[:-l], x[l:]) / denom) for l in (1, 10, 100, 1_000, 10_000)]
    scv_a, scv_s = SCV[kind]
    pred = analytic_var(rho * MU, MU, est["window"], scv_a, scv_s, kind=kind)
    return dict(kind=kind, load=rho, n=n, n_usable=int(usable), n_boot=n_boot, point=
                {k: v for k, v in est.items() if k != "sojourn"},
                predicted=pred, by_block=out,
                sojourn_acf_lags=[1, 10, 100, 1000, 10000], sojourn_acf=acf)


# -------------------------------------------------------- 4. observation spans
def span_study(mu=10.0, dt_board=2.0):
    """The review board of the Introduction, with the criterion declared."""
    rows = []
    for lam, label in ((9.5, "as stated"), (9.975, "after a five-percent rise")):
        margin = mu - lam
        pc = 1.0 - math.exp(-margin * dt_board)
        se_year = math.sqrt((lam + mu ** 2 / lam) / WEEKS_PER_YEAR)
        crit = {}
        for name, eps, z in (("se_equals_margin", 1.0, 1.0),
                             ("ci95_excludes_zero", 1.0, 1.96),
                             ("ci95_half_width_10pct", 0.1, 1.96)):
            tau = span_for(lam, mu, 1.0, 1.0, eps, z)
            crit[name] = dict(weeks=tau, years=tau / WEEKS_PER_YEAR)
        # the same span if the capacity is known independently rather than estimated
        tau_known_mu = span_for(lam, mu, 1.0, 0.0, 1.0, 1.0)
        # and under deterministic service (c_s^2 = 0 in the second term only)
        rows.append(dict(
            lam=lam, mu=mu, label=label, margin=margin, cr=lam / mu, pc=pc,
            se_one_year=se_year, se_exceeds_margin=bool(se_year > margin),
            criteria=crit,
            se_one_year_known_mu=math.sqrt(lam / WEEKS_PER_YEAR),
            span_se_equals_margin_known_mu_weeks=tau_known_mu,
            relaxation_weeks=relaxation_time(lam / mu, mu),
            relaxation_years=relaxation_time(lam / mu, mu) / WEEKS_PER_YEAR,
        ))
    # the general relation between the two spans, checked numerically
    rel = []
    for cr in (0.9, 0.95, 0.99, 0.9975, 0.999):
        lam = cr * mu
        tq = relaxation_time(cr, mu)
        for eps, z, name in ((1.0, 1.0, "se_equals_margin"),
                             (1.0, 1.96, "ci95_excludes_zero"),
                             (0.1, 1.96, "ci95_half_width_10pct")):
            ts = span_for(lam, mu, 1.0, 1.0, eps, z)
            rel.append(dict(cr=cr, criterion=name, span_weeks=ts,
                            relaxation_weeks=tq, ratio=ts / tq))
    return dict(board=rows, span_over_relaxation=rel)


# ------------------------------------------------------------ 5. board study
def board_study(mu=10.0, dt_board=2.0, tau=WEEKS_PER_YEAR, reps=2000,
                seed=20261015):
    """Independent years of the same board: sign errors, intervals, clipping."""
    out = []
    for lam in (9.5, 9.975):
        margin_true = mu - lam
        pc_true = 1.0 - math.exp(-margin_true * dt_board)
        n_arr_expected = int(lam * tau * 1.4) + 400
        seeds = np.random.SeedSequence(seed).spawn(reps)
        m_hat, se_hat, lam_h, mu_h = [], [], [], []
        for s in seeds:
            rng = np.random.default_rng(s)
            interarr, service = draw_times(rng, lam / mu, "MM1",
                                           n_arr_expected, mu=mu)
            log = build_log(interarr, service)
            t0 = float(log["arrival"][200])          # start the window mid-stream
            e = estimate(log, t0, t0 + tau, dt=dt_board)
            m_hat.append(e["margin"]); lam_h.append(e["lam_hat"])
            mu_h.append(e["mu_hat"])
            # standard error from the counts of that window alone
            se_hat.append(math.sqrt(e["lam_hat"] / tau +
                                    e["mu_hat"] ** 2 / (e["lam_hat"] * tau)))
        m_hat = np.array(m_hat); se_hat = np.array(se_hat)
        lo = m_hat - 1.96 * se_hat
        hi = m_hat + 1.96 * se_hat
        # what a naive pipeline would report: clip the margin positive, then P_c
        clipped = np.maximum(m_hat, 1e-9)
        pc_clipped = 1.0 - np.exp(-clipped * dt_board)
        pc_unclipped = 1.0 - np.exp(-m_hat * dt_board)
        # share of each 95% confidence set that lies at lambda >= mu
        frac_super = 0.5 * (1.0 + np.vectorize(math.erf)(-m_hat /
                                                         (se_hat * math.sqrt(2))))
        out.append(dict(
            lam=lam, mu=mu, tau_weeks=tau, reps=reps,
            margin_true=margin_true, pc_true=pc_true,
            margin_mean=float(m_hat.mean()), margin_sd=float(m_hat.std(ddof=1)),
            se_mean=float(se_hat.mean()),
            se_analytic=math.sqrt((lam + mu ** 2 / lam) / tau),
            frac_wrong_sign=float(np.mean(m_hat <= 0)),
            frac_ci_contains_zero=float(np.mean((lo <= 0) & (hi >= 0))),
            frac_ci_entirely_positive=float(np.mean(lo > 0)),
            mean_supercritical_mass=float(frac_super.mean()),
            pc_clipped_mean=float(pc_clipped.mean()),
            pc_clipped_median=float(np.median(pc_clipped)),
            frac_pc_invalid=float(np.mean(pc_unclipped < 0)),
            lam_hat_mean=float(np.mean(lam_h)), mu_hat_mean=float(np.mean(mu_h)),
        ))
    return out


# ------------------------------------------------------------------- reporting
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=48)
    ap.add_argument("--boot", type=int, default=400)
    ap.add_argument("--out", default="margin_precision.json")
    a = ap.parse_args()

    ok = check_vectorization()
    print(f"vectorized log identical to estimator_calibration.simulate_log: {ok}")
    if not ok:
        raise SystemExit("vectorized event log does not match the released loop")
    root_gap = max(abs(gim1_root(cr, MU, SCV_A_H2) -
                       gim1_root_algebraic(cr, SCV_A_H2))
                   for cr in (0.3, 0.497, 0.5, 0.7, 0.85, 0.94, 0.965))
    print(f"GI/M/1 root: bisection against the S3.4 quadratic, largest gap "
          f"{root_gap:.2e}")
    if root_gap > 1e-9:
        raise SystemExit("the GI/M/1 root solvers disagree")

    res = {"vectorization_check": ok, "replications": {}, "bootstrap": [],
           "spans": span_study(), "board": board_study()}

    print("\n== 2. delta method against the replication spread "
          f"({a.reps} replications, {N_ARRIVALS - WARMUP} commitments each) ==")
    print(f"{'queue':>6} {'load':>5} {'quantity':>10} {'SE pred':>11} {'SD emp':>11} "
          f"{'pred/emp':>9} {'rel.SE':>8}")
    for kind in ("MM1", "MD1", "H2M1"):
        rows = replication_study(kind, a.reps)
        res["replications"][kind] = rows
        for r in rows:
            for key, pkey, truth in (("lam_hat", "se_lam", r["load"] * MU),
                                     ("mu_hat", "se_mu", MU),
                                     ("margin", "se_margin", r["margin_true"]),
                                     ("cr", "se_cr", r["cr_true"]),
                                     ("pc_implied", "se_pc", r["pc_true"])):
                pred = r["predicted"][pkey]
                emp = r["empirical"][key]["sd"]
                if pred != pred:          # no implied P_c for this queue
                    continue
                ratio = pred / emp if emp > 0 else float("nan")
                print(f"{kind:>6} {r['load']:>5.2f} {key:>10} {pred:>11.3e} "
                      f"{emp:>11.3e} {ratio:>9.2f} {pred / truth:>8.2%}")
            print(f"{kind:>6} {r['load']:>5.2f} {'corr(l,m)':>10} "
                  f"{r['corr']:>11.3f} {'':>11} "
                  f"[{r['corr_ci95'][0]:.2f},{r['corr_ci95'][1]:.2f}]")
            print(f"{kind:>6} {r['load']:>5.2f} {'pc_direct':>10} "
                  f"{r['pc_direct_binomial_se']:>11.3e} "
                  f"{r['empirical']['pc_direct']['sd']:>11.3e} "
                  f"  VIF {r['pc_direct_vif']:>7.0f}   implied/direct SD "
                  f"{r['empirical']['pc_implied']['sd'] / r['empirical']['pc_direct']['sd']:.2f}")

    print("\n   the margin alone does not fix P_c: the same margin under a different "
          "arrival law")
    print(f"   {'load':>6} {'margin':>8} {'P_c M/M/1':>10} {'P_c H2/M/1':>11} "
          f"{'ratio':>7}")
    for rho in LOADS:
        a_pc = pc_from_rates(rho * MU, MU, "MM1")
        b_pc = pc_from_rates(rho * MU, MU, "H2M1")
        print(f"   {rho:>6.2f} {MU - rho * MU:>8.3f} {a_pc:>10.4f} {b_pc:>11.4f} "
              f"{a_pc / b_pc:>7.2f}")
    res["pc_by_arrival_law"] = [
        dict(load=rho, margin=MU - rho * MU, pc_mm1=pc_from_rates(rho * MU, MU, "MM1"),
             pc_h2m1=pc_from_rates(rho * MU, MU, "H2M1")) for rho in LOADS]

    print("\n== 3. bootstrap on one log, by block length ==")
    for kind, rho in (("MM1", 0.70), ("MM1", 0.94), ("MD1", 0.94), ("H2M1", 0.94)):
        b = bootstrap_study(kind, rho, n_boot=a.boot)
        res["bootstrap"].append(b)
        print(f"  {kind} load {rho}: margin {b['point']['margin']:.5f} "
              f"(true {MU - rho * MU:.5f}); sojourn ACF at lags "
              f"{b['sojourn_acf_lags']} = "
              + ", ".join(f"{v:.3f}" for v in b["sojourn_acf"]))
        print(f"    delta method on the same window ({b['point']['window']:,.0f} time "
              f"units, {b['n_usable']:,} commitments): SE margin "
              f"{b['predicted']['se_margin']:.3e}, SE CR {b['predicted']['se_cr']:.3e}, "
              f"SE Pc(impl) {b['predicted']['se_pc']:.3e}")
        print(f"    {'block':>7} {'block/n':>8} {'SE margin':>11} {'SE CR':>11} "
              f"{'SE Pc(impl)':>12} {'SE Pc(direct)':>14} {'corr(l,m)':>10}")
        for blk, d in b["by_block"].items():
            print(f"    {blk:>7} {d['block_over_n']:>8.4f} {d['se_margin']:>11.3e} "
                  f"{d['se_cr']:>11.3e} {d['se_pc_implied']:>12.3e} "
                  f"{d['se_pc_direct']:>14.3e} {d['corr_lam_mu']:>10.3f}")

    print("\n== 4. the observation span, criterion declared "
          "(review board, mu = 10/week, Delta t = 2 weeks) ==")
    for r in res["spans"]["board"]:
        print(f"  lambda = {r['lam']}/wk ({r['label']}): margin {r['margin']:.3f}/wk, "
              f"CR {r['cr']:.4f}, P_c {r['pc']:.3f}")
        print(f"    one year of counts: SE = {r['se_one_year']:.3f}/wk "
              f"({'exceeds' if r['se_exceeds_margin'] else 'below'} the margin); "
              f"SE = {r['se_one_year_known_mu']:.3f}/wk if mu is known")
        for name, d in r["criteria"].items():
            print(f"    {name:>22}: {d['weeks']:>12,.0f} weeks = "
                  f"{d['years']:>10,.1f} years")
        print(f"    queue relaxation time: {r['relaxation_weeks']:,.0f} weeks = "
              f"{r['relaxation_years']:,.1f} years")
    print("    span / relaxation time, both diverging as margin^-2:")
    for d in res["spans"]["span_over_relaxation"]:
        print(f"      CR {d['cr']:<7} {d['criterion']:>22}: ratio {d['ratio']:.3f}")

    print("\n== 5. independent years of the same board ==")
    for r in res["board"]:
        print(f"  lambda = {r['lam']}/wk, margin {r['margin_true']:.3f}/wk, "
              f"{r['reps']} years of {r['tau_weeks']:.0f} weeks")
        print(f"    margin estimate: mean {r['margin_mean']:+.4f}, "
              f"SD {r['margin_sd']:.4f} (analytic SE {r['se_analytic']:.4f}, "
              f"mean estimated SE {r['se_mean']:.4f})")
        print(f"    wrong sign in {r['frac_wrong_sign']:.1%} of years; "
              f"95% interval contains zero in {r['frac_ci_contains_zero']:.1%}; "
              f"entirely positive in {r['frac_ci_entirely_positive']:.1%}")
        print(f"    mean mass of the confidence set at lambda >= mu: "
              f"{r['mean_supercritical_mass']:.1%}; "
              f"P_c invalid (negative) in {r['frac_pc_invalid']:.1%} of years")
        print(f"    clipping the margin positive would report P_c = "
              f"{r['pc_clipped_mean']:.3f} on average "
              f"(median {r['pc_clipped_median']:.3f}) against the true "
              f"{r['pc_true']:.3f}")

    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

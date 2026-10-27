"""bounded/calibrate.py — interval, graded critical value and decision rule of the bounded comparison (S1, S3).

Inputs are complete point-pipeline statistics T (bounded.procedure) from independent calibration banks, one bank per
catalogue setting. Construction (method-repair record S1, implemented after scratch repair_procedure.py, made exact):

 1. Median bracket per setting g: the exact binomial order-statistic interval [x_(j), x_(n-j+1)] for the LOWER median
    theta_g = inf{t : P_g(T <= t) >= 1/2}, with j the largest rank in 1..floor(n/2) such that
    2 * BinomCDF(j-1; n, 1/2) <= delta_med,  delta_med = 0.005 / J  (J = number of settings).
    Why it holds for any distribution, ties included: P(x_(j) > theta) = P(#{x_i <= theta} < j) <= BinomCDF(j-1; n, 1/2)
    because P(T <= theta) >= 1/2, and P(x_(n-j+1) < theta) = P(#{x_i < theta} >= n-j+1) <= BinomCDF(j-1; n, 1/2)
    because P(T < theta) <= 1/2. No bracket exists if even j = 1 fails; then the bracket is the whole range [-a, a].
 2. Tolerance limits per setting at content p = 0.98 per tail: u_g = x_(k) with k the SMALLEST rank such that
    BinomCDF(k-1; n, p) >= 1 - delta_tol, delta_tol = 0.005 / (2J); then P(P_g(T <= u_g) >= p) >= 1 - delta_tol, because
    x_(k) < q_p requires at least k of n values below q_p, an event of probability <= 1 - BinomCDF(k-1; n, p). The lower
    limit l_g is the same construction applied to -T. On both events P_g(l_g <= T <= u_g) >= 0.96.
 3. A = max_g max(u_g - m_g^-, 0), B = max_g max(m_g^+ - l_g, 0); I(T) = [max(-a, T - A), min(a, T + B)].
 4. c_G = max(0, max over graded g of u_g).

The calibration event (every bracket holds AND every tolerance limit holds) has probability >= 1 - 0.005 - 0.005 = 0.99
by the union bound. On it, for every catalogue setting: P_g(theta_g in I(T)) >= P_g(l_g <= T <= u_g) >= 0.96 (if
l_g <= T <= u_g then T - A <= m_g^- <= theta_g <= m_g^+ <= T + B; theta_g lies in [-a, a] so the truncation is harmless),
hence unconditional inclusion >= 0.99 * 0.96 = 0.9504; and for every graded setting P_g(T > c_G) <= P_g(T > u_g) <= 0.02,
hence an unconditional mixture-preference probability <= 0.99 * 0.02 + 0.01 = 0.0298. Assumptions: independent, finite
complete-pipeline statistics, an unchanged catalogue and algorithm. Nothing is certified outside the catalogue.

Decision (S1): mixture preference iff lower endpoint > 0 AND T > c_G; negative bounded contrast iff upper endpoint < 0;
otherwise inconclusive; a failed fit or unavailable score is UNAVAILABLE, never a scientific decision. An unavailable
calibration attempt HOLDS artifact construction (ValueError): it is never omitted or replaced.

"Exact": every binomial comparison is made in rational arithmetic (fractions.Fraction), so no rank can move with
floating-point rounding in a CDF; the order statistics themselves are the floating-point T values as computed.
`validation_thresholds` derives the S3 pass counts by the same exact arithmetic (one-sided exact binomial bounds at
alpha = 0.04/52 each).
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from functools import lru_cache
from math import comb

import numpy as np

with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()          # bound at this module's own import (B1)

CAP = 0.03
TARGET_ERROR = Fraction(5, 1000)          # total error across all median brackets
TOLERANCE_ERROR = Fraction(5, 1000)       # total error across both tails of all tolerance limits
TAIL_CONTENT = Fraction(98, 100)          # p per tail; central content 0.96
CENTRAL_CONTENT = 2 * TAIL_CONTENT - 1
VALIDATION_FAMILY_ALPHA = Fraction(4, 100)
VALIDATION_STATEMENTS = 52                # 30 inclusion + 16 graded safety + 6 power
DECISIONS = ("mixture preference", "negative bounded contrast", "inconclusive", "unavailable")
_TOL = 1e-12


def _q(p) -> Fraction:
    return p if isinstance(p, Fraction) else Fraction(str(p))


def binom_cdf(k: int, n: int, p) -> Fraction:
    """Exact P(Bin(n, p) <= k) as a Fraction (p a Fraction or a decimal-string-exact float)."""
    p = _q(p)
    if k < 0:
        return Fraction(0)
    if k >= n:
        return Fraction(1)
    q = 1 - p
    num, den = p.numerator, p.denominator
    qn = q.numerator                               # q = (den - num) / den
    total = sum(comb(n, i) * num ** i * qn ** (n - i) for i in range(0, k + 1))
    return Fraction(total, den ** n)


def _cdf_table(n: int, p) -> tuple:
    """(P(Bin(n,p) <= k) for k = 0..n), exact, computed once per (n, p)."""
    return _cdf_table_q(int(n), _q(p))


@lru_cache(maxsize=None)
def _cdf_table_q(n: int, p: Fraction) -> tuple:
    num, den = p.numerator, p.denominator
    qn = den - num
    acc, out = 0, []
    for i in range(n + 1):
        acc += comb(n, i) * num ** i * qn ** (n - i)
        out.append(Fraction(acc, den ** n))
    return tuple(out)


def median_ranks(n: int, delta) -> tuple:
    """(j, n - j + 1, exact two-sided error bound) for the median bracket, or (0, n + 1, 0) when none exists."""
    delta = _q(delta)
    cdf = _cdf_table(n, Fraction(1, 2))
    j = 0
    for cand in range(1, n // 2 + 1):
        if 2 * cdf[cand - 1] <= delta:
            j = cand
        else:
            break                                   # the CDF is increasing in its argument
    return (j, n - j + 1, (2 * cdf[j - 1]) if j else Fraction(0))


def tolerance_rank(n: int, p, delta) -> tuple:
    """(k, exact error bound 1 - BinomCDF(k-1; n, p)) with k the smallest rank such that BinomCDF(k-1; n, p) >= 1 - delta."""
    delta = _q(delta)
    cdf = _cdf_table(n, p)
    for k in range(1, n + 1):
        if cdf[k - 1] >= 1 - delta:
            return k, 1 - cdf[k - 1]
    raise ValueError(f"insufficient calibration rows for content {p} at error {delta} with n = {n}")


def _bank(raw) -> np.ndarray:
    x = np.asarray([np.nan if v is None else v for v in raw], dtype=float)
    if x.ndim != 1 or x.size < 2:
        raise ValueError("a calibration bank needs at least two statistics")
    if not np.all(np.isfinite(x)):
        raise ValueError("unavailable or invalid calibration point: artifact construction is HELD (never omitted)")
    if np.any(np.abs(x) > CAP + _TOL):
        raise ValueError("a calibration statistic lies outside [-cap, cap]")
    return np.sort(x)


def median_bracket(x, delta) -> dict:
    x = _bank(x); n = x.size
    j, ju, err = median_ranks(n, delta)
    if j == 0:
        return dict(lo=-CAP, hi=CAP, lower_rank=0, upper_rank=n + 1, error_bound=0.0)
    return dict(lo=float(x[j - 1]), hi=float(x[ju - 1]), lower_rank=j, upper_rank=ju, error_bound=float(err))


def upper_tolerance(x, p, delta) -> dict:
    x = _bank(x); n = x.size
    k, err = tolerance_rank(n, p, delta)
    return dict(value=float(x[k - 1]), rank=k, error_bound=float(err))


def lower_tolerance(x, p, delta) -> dict:
    """The upper construction applied to -T: value = x_(n-k+1) in ascending order."""
    x = _bank(x); n = x.size
    k, err = tolerance_rank(n, p, delta)
    return dict(value=float(x[n - k]), rank=n - k + 1, error_bound=float(err))


def eb_mean(x, delta) -> dict:
    """Two-sided empirical-Bernstein bracket for the MEAN of a statistic bounded in [-CAP, CAP] (Maurer & Pontil 2009,
    Theorem 4, each tail at delta/2), ported from sim_results/interval_diag_2026-10-27/codex/repair_procedure.py:eb_mean.
    On [0, 1] the one-sided bound is sqrt(2 V ln(2/d) / n) + 7 ln(2/d) / (3 (n - 1)) with V the unbiased sample
    variance; rescaled to the range R = 2 CAP it is sqrt(2 s^2 a / n) + 7 R a / (3 (n - 1)), a = ln(4 / delta) for the
    two-sided bracket. Used by the boundary certificate (S3: the bounded-mean bracket at error 0.01 inside +-0.003).
    Truncated to [-CAP, CAP]. Raises on an unavailable or out-of-range statistic, like the order-statistic helpers."""
    x = _bank(x)
    n = x.size
    a = float(np.log(4.0 / float(_q(delta))))
    half = float(np.sqrt(2.0 * np.var(x, ddof=1) * a / n) + 7.0 * (2.0 * CAP) * a / (3.0 * (n - 1)))
    m = float(np.mean(x))
    return dict(lo=max(-CAP, m - half), hi=min(CAP, m + half), mean=m, half_width=half, n=int(n), delta=str(_q(delta)))


def calibrate(banks: dict, graded) -> dict:
    """The frozen interval artifact from complete calibration banks {setting: [T, ...]} and the graded setting names.

    Raises ValueError if any bank holds an unavailable (None / non-finite) or out-of-range statistic. The cap is the
    module constant CAP (no argument: Codex round 4, N2). This is the mathematical core only: the attempted-set,
    identity and freeze contract is bounded.campaign.freeze_calibration."""
    graded = list(graded)
    J = len(banks)
    if J == 0 or not graded or not set(graded).issubset(banks):
        raise ValueError("bad catalogue: every graded setting needs a bank")
    d_med = TARGET_ERROR / J
    d_tol = TOLERANCE_ERROR / (2 * J)
    A = B = c_G = 0.0
    cells = {}
    for name in sorted(banks):
        x = _bank(banks[name])
        mb = median_bracket(x, d_med)
        up = upper_tolerance(x, TAIL_CONTENT, d_tol)
        lo = lower_tolerance(x, TAIL_CONTENT, d_tol)
        A = max(A, up["value"] - mb["lo"], 0.0)
        B = max(B, mb["hi"] - lo["value"], 0.0)
        if name in graded:
            c_G = max(c_G, up["value"], 0.0)
        cells[name] = dict(n=int(x.size), graded=name in graded, median_lo=mb["lo"], median_hi=mb["hi"],
                           median_ranks=[mb["lower_rank"], mb["upper_rank"]], median_error=mb["error_bound"],
                           tol_lo=lo["value"], tol_hi=up["value"], tol_lo_rank=lo["rank"], tol_hi_rank=up["rank"],
                           tol_error_per_tail=up["error_bound"], sample_median=float(np.median(x)))
    art = dict(cap=float(CAP), A=float(A), B=float(B), graded_critical=float(c_G), n_settings=J, graded=sorted(graded),
               allocation=dict(median_error_total=str(TARGET_ERROR), median_error_per_setting=str(d_med),
                               tolerance_error_total=str(TOLERANCE_ERROR), tolerance_error_per_tail_per_setting=str(d_tol),
                               tail_content=str(TAIL_CONTENT), central_content=str(CENTRAL_CONTENT)),
               guarantees=dict(calibration_event_probability=">= 0.99",
                               inclusion_on_event=">= 0.96", inclusion_unconditional=">= 0.9504",
                               graded_positive_call_on_event="<= 0.02", graded_positive_call_unconditional="<= 0.0298"),
               cells=cells)
    art["artifact_sha256"] = hashlib.sha256(json.dumps(art, sort_keys=True).encode()).hexdigest()
    return art


def interval(t: float, art: dict) -> tuple:
    a = art["cap"]
    return max(-a, t - art["A"]), min(a, t + art["B"])


def apply(t, art: dict, available: bool = True) -> dict:
    """The S1 decision for one study statistic T under a frozen artifact."""
    if not available or t is None or not np.isfinite(t):
        return dict(status="unavailable", decision="unavailable")
    for key in ("A", "B", "graded_critical"):
        if not np.isfinite(art[key]) or art[key] < 0:
            raise ValueError("invalid interval artifact")
    if abs(art["cap"] - CAP) > _TOL or abs(t) > CAP + _TOL:
        raise ValueError("statistic or artifact outside the declared cap")
    lo, hi = interval(float(t), art)
    if lo > 0 and t > art["graded_critical"]:
        dec = "mixture preference"
    elif hi < 0:
        dec = "negative bounded contrast"
    else:
        dec = "inconclusive"
    return dict(status="available", point=float(t), lo=float(lo), hi=float(hi), decision=dec)


def includes_bracket(result: dict, cell: dict) -> bool:
    """Validation's conservative inclusion: the interval contains the setting's ENTIRE calibration median bracket.
    An unavailable result is an inclusion failure."""
    if result.get("status") != "available":
        return False
    return result["lo"] <= cell["median_lo"] and cell["median_hi"] <= result["hi"]


def _upper_tail(n: int, k: int, p) -> Fraction:
    """P(Bin(n, p) >= k), exact."""
    return Fraction(1) if k <= 0 else 1 - _cdf_table(n, p)[k - 1]


def validation_thresholds(n_graded: int = 400, n_alt: int = 1000, alpha=None) -> dict:
    """S3's operational pass counts from one-sided exact binomial (Clopper-Pearson) bounds at alpha = 0.04/52 each.

    lower bound >= f  <=>  P(Bin(n, f) >= k) <= alpha;   upper bound <= f  <=>  P(Bin(n, f) <= k) <= alpha."""
    alpha = VALIDATION_FAMILY_ALPHA / VALIDATION_STATEMENTS if alpha is None else _q(alpha)

    def min_success(n, floor):
        return next(k for k in range(n + 1) if _upper_tail(n, k, floor) <= alpha)

    def max_fail(n, ceiling):
        cdf = _cdf_table(n, ceiling)
        return max(k for k in range(n + 1) if cdf[k] <= alpha)
    return dict(alpha=str(alpha),
                graded_inclusion_min=min_success(n_graded, Fraction(90, 100)), graded_n=n_graded,
                alternative_inclusion_min=min_success(n_alt, Fraction(90, 100)), alternative_n=n_alt,
                power_gate_min=min_success(n_alt, Fraction(80, 100)),
                graded_positive_or_unavailable_max=max_fail(n_graded, Fraction(64, 1000)))

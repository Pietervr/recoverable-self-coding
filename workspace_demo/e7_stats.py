"""E7 shared statistics — pre-registered, used identically on the
reduced-model prediction and on the rig data.

Confound discipline (the reason e4_precursors.py was inconclusive, plus
two artifacts caught during predictor design):

1. Mean drift. The junk indicator is Bernoulli: raw variance = p(1-p)
   rises with p trivially. Fixed with an EXACTLY unbiased excess
   variance: for iid Bernoulli at ANY p,
   E[ sum(x-m)^2/(w-1) - m(1-m) w/(w-1) ] = 0.
2. Degenerate-window artifact. All-same windows have undefined AC1; a
   0.0 placeholder plus the iid small-sample bias (-1/(w-1)) fabricates
   a negative trend as the mean leaves 0. Fixed: AC1 windows with
   0 < m < 1 only; placeholder windows are dropped, not zeroed.
3. Order parameter. Critical slowing down lives in the QUEUE relaxation
   time, so the primary series is queue_after (per served task), linearly
   detrended within each window before residual variance and AC1. The
   junk indicator is the secondary series.

Trend statistic: Kendall tau of each sliding series against index.
Overlapping windows are serially dependent, so tau is an EFFECT SIZE
compared between arms (near-fold vs far-fold), never a naked p-value.

Pre-onset segment: tasks served before the first task whose
queue_after >= 12 (identical rule in model and rig); arms that never
reach 12 contribute their full series. Arms with a pre-onset segment
shorter than 40 tasks are censored (reported, not analyzed).
"""

from __future__ import annotations

W = 25
ONSET_QUEUE = 12
MIN_TASKS = 40


def _detrend(win: list[float]) -> list[float]:
    """Residuals of an OLS line fit within the window."""
    n = len(win)
    xm = (n - 1) / 2
    ym = sum(win) / n
    sxx = sum((i - xm) ** 2 for i in range(n))
    sxy = sum((i - xm) * (win[i] - ym) for i in range(n))
    b = sxy / sxx if sxx else 0.0
    return [win[i] - (ym + b * (i - xm)) for i in range(n)]


def _ac1(res: list[float]) -> float | None:
    den = sum(r * r for r in res)
    if den < 1e-9:
        return None
    return sum(res[j] * res[j + 1] for j in range(len(res) - 1)) / den


def queue_series_stats(queue_after: list[int], w: int = W):
    """Sliding (var, ac1) of the linearly detrended queue-length series."""
    out = []
    for i in range(w, len(queue_after) + 1):
        res = _detrend([float(x) for x in queue_after[i - w:i]])
        var = sum(r * r for r in res) / (w - 2) if w > 2 else 0.0
        a = _ac1(res)
        out.append((var, a))
    return out


def junk_series_stats(series: list[float], w: int = W):
    """Sliding (excess_var, ac1) of the 0/1 junk series; exact-unbiased
    excess variance, AC1 only for non-degenerate windows (else None)."""
    out = []
    for i in range(w, len(series) + 1):
        win = series[i - w:i]
        m = sum(win) / w
        ss = sum((x - m) ** 2 for x in win)
        xvar = ss / (w - 1) - m * (1 - m) * w / (w - 1)
        a = _ac1([x - m for x in win]) if 0 < m < 1 else None
        out.append((xvar, a))
    return out


def kendall_tau(xs: list[float]) -> float | None:
    """Kendall tau of xs against its index (O(n^2), n is small)."""
    n = len(xs)
    if n < 8:
        return None
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = xs[j] - xs[i]
            if d > 0:
                conc += 1
            elif d < 0:
                disc += 1
    tot = n * (n - 1) / 2
    return (conc - disc) / tot if tot else 0.0


def pre_onset_len(queue_after: list[int]) -> int:
    for i, qa in enumerate(queue_after):
        if qa >= ONSET_QUEUE:
            return i
    return len(queue_after)


def arm_summary(junk: list[float], queue_after: list[int]) -> dict:
    """The pre-registered per-arm summary."""
    cut = pre_onset_len(queue_after)
    ignited = cut < len(queue_after)
    if cut < MIN_TASKS:
        return {"n": cut, "ignited": ignited, "censored": True}
    qa, jk = queue_after[:cut], junk[:cut]
    qst = queue_series_stats(qa)
    jst = junk_series_stats(jk)
    qvar = [s[0] for s in qst]
    qac1 = [s[1] for s in qst if s[1] is not None]
    jxv = [s[0] for s in jst]
    jac1 = [s[1] for s in jst if s[1] is not None]
    third = max(1, len(qst) // 3)

    def thirds(xs):
        if len(xs) < 6:
            return None
        t = max(1, len(xs) // 3)
        return round(sum(xs[-t:]) / t - sum(xs[:t]) / t, 4)

    return {
        "n": cut, "ignited": ignited, "censored": False,
        "n_windows": len(qst),
        "tau_qvar": kendall_tau(qvar),
        "tau_qac1": kendall_tau(qac1),
        "tau_jxvar": kendall_tau(jxv),
        "tau_jac1": kendall_tau(jac1),
        "d_qac1_thirds": thirds(qac1),
        "d_qvar_thirds": thirds(qvar),
        "d_jxvar_thirds": thirds(jxv),
        "third_size": third,
    }

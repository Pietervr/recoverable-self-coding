#!/usr/bin/env python3
"""Stage 3 of the RSC exemplar: estimation, static and dynamic.

Static: the unchanged excursion/restore estimator (proceedings
csself_estimator.py) over a whole segment.

Dynamic: a Gamma-Poisson conjugate filter with exponential forgetting over
the same two point processes, giving a posterior over CR(t) that updates per
event. Arrivals are band-exit onsets against discounted observation time;
services are restorations against discounted union busy time. With
forgetting rate lam = ln2 / half_life:

    n_R(t) = sum_i exp(-lam (t - o_i))          onsets o_i <= t
    E_R(t) = (1 - exp(-lam t)) / lam            discounted observation time
    n_C(t) = sum_j exp(-lam (t - r_j))          restorations r_j <= t
    E_C(t) = int busy(s) exp(-lam (t-s)) ds     discounted busy time

    R(t) ~ Gamma(a0 + n_R, b0 + E_R),  C(t) ~ Gamma(a0 + n_C, b0 + E_C)

CR(t) = R/C posterior summarized by Monte Carlo. Priors are weakly
informative (a0 = 0.5 events, b0 = 0.5 days) and stated wherever results
are shown. Left-censoring is inherited from the static estimator: an onset
requires a fresh in-range -> out-of-range crossing.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "proceedings" / "cself"))
from csself_estimator import _union_length, excursion_intervals  # noqa: E402

A0 = 0.5        # prior events
B0 = 0.5        # prior exposure, days
MC = 4000       # posterior draws for CR summaries
RNG = np.random.default_rng(20260810)


@dataclass
class UnitEvents:
    """Per-unit event material extracted once, reused by both estimators."""
    onsets: np.ndarray            # onset times, days
    restores: np.ndarray          # restoration times, days
    busy: list[tuple[float, float]]   # union of excursion intervals
    t_first: float
    t_last: float


def extract_unit(events: pd.DataFrame) -> UnitEvents:
    """events: harmonized rows for ONE unit (schema.py contract)."""
    onsets: list[float] = []
    restores: list[float] = []
    intervals: list[tuple[float, float]] = []
    t_first, t_last = np.inf, -np.inf
    for _, g in events.groupby("var", sort=False):
        g = g.sort_values("t_days")
        t = g["t_days"].to_numpy(float)
        v = g["value"].to_numpy(float)
        if len(t) == 0:
            continue
        t_first = min(t_first, float(t[0]))
        t_last = max(t_last, float(t[-1]))
        ivs, _n_restored = excursion_intervals(
            t, v, float(g["lo"].iloc[0]), float(g["hi"].iloc[0]))
        last_t = float(t[-1])
        for (o, r) in ivs:
            onsets.append(o)
            if r < last_t or (r == last_t and v[-1] >= g["lo"].iloc[0]
                              and v[-1] <= g["hi"].iloc[0]):
                restores.append(r)
        intervals.extend(ivs)
    # merge to the union busy set
    merged: list[tuple[float, float]] = []
    for s, e in sorted(intervals):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return UnitEvents(np.asarray(sorted(onsets)), np.asarray(sorted(restores)),
                      merged, float(t_first), float(t_last))


def static_estimate(u: UnitEvents) -> dict:
    span = max(u.t_last - u.t_first, 1e-9)
    busy = max(_union_length(u.busy), 1e-9)
    r = len(u.onsets) / span
    c = len(u.restores) / busy
    return dict(R_day=r, C_day=c,
                CR=(r / c if c > 0 else np.inf),
                n_onset=len(u.onsets), n_restore=len(u.restores),
                span_days=span, busy_days=busy)


def _discounted_busy(busy: list[tuple[float, float]], t: float,
                     lam: float) -> float:
    """int_0^t busy(s) exp(-lam (t - s)) ds for a union of intervals."""
    acc = 0.0
    for s, e in busy:
        if s >= t:
            break
        e = min(e, t)
        acc += (np.exp(-lam * (t - e)) - np.exp(-lam * (t - s))) / lam
    return acc


# posterior tail probabilities the gates consume: name -> (op, threshold)
GATE_PROBS: dict[str, tuple[str, float]] = {
    "p_escalate":   (">", 0.7),   # P(CR > 0.7)
    "p_infeasible": (">", 1.0),   # P(CR > 1)
    "p_recovered":  ("<", 0.8),   # P(CR < 0.8)
}


def filter_trajectory(u: UnitEvents, grid: np.ndarray,
                      half_life_days: float = 14.0,
                      probs: dict[str, tuple[str, float]] | None = None,
                      ) -> pd.DataFrame:
    """Posterior over (R, C, CR, M) on a time grid (days, unit clock)."""
    lam = np.log(2.0) / half_life_days
    probs = GATE_PROBS if probs is None else probs
    rows = []
    for t in grid:
        rel_o = u.onsets[u.onsets <= t]
        rel_r = u.restores[u.restores <= t]
        n_r = float(np.exp(-lam * (t - rel_o)).sum())
        n_c = float(np.exp(-lam * (t - rel_r)).sum())
        e_r = (1.0 - np.exp(-lam * max(t - u.t_first, 0.0))) / lam
        e_c = _discounted_busy(u.busy, t, lam)
        gr = RNG.gamma(A0 + n_r, 1.0 / (B0 + e_r), MC)
        gc = RNG.gamma(A0 + n_c, 1.0 / (B0 + e_c), MC)
        cr = gr / gc
        m = gc - gr
        row = dict(
            t=t,
            R_mean=(A0 + n_r) / (B0 + e_r),
            C_mean=(A0 + n_c) / (B0 + e_c),
            CR_med=float(np.median(cr)),
            CR_lo=float(np.quantile(cr, 0.1)),
            CR_hi=float(np.quantile(cr, 0.9)),
            M_med=float(np.median(m)),
            M_lo=float(np.quantile(m, 0.1)),
            M_hi=float(np.quantile(m, 0.9)),
        )
        for name, (op, theta) in probs.items():
            row[name] = float((cr > theta).mean() if op == ">"
                              else (cr < theta).mean())
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from schema import load_synthea_events, synthea_anchors

    ev = load_synthea_events()
    an = synthea_anchors()
    # smoke test: one COVID-inpatient unit with a dense record
    target = an[an.covid_admission.notna()].patient.iloc[0]
    unit = ev[ev.unit == f"synthea:{target}"]
    u = extract_unit(unit)
    print("static:", {k: round(v, 3) if isinstance(v, float) else v
                      for k, v in static_estimate(u).items()})
    grid = np.linspace(u.t_first, u.t_last, 60)
    traj = filter_trajectory(u, grid)
    print(traj[["t", "CR_med", "p_infeasible"]].tail(8).to_string(index=False))

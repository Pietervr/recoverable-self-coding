#!/usr/bin/env python3
"""Stage 5 of the RSC exemplar: C_self as a gate.

Three gates over a filtered trajectory (estimate.filter_trajectory output).
All parameters are illustrative *policy*, stated here and never fitted to
outcomes:

  G1 escalation  first t with P(CR > 0.7) >= 0.6
                 -> workup / screening (certification-capacity injection)
  G2 admission   first t with P(CR > 1) >= 0.5 on >= 2 consecutive grid
                 points -> ICU (exogenous capacity injection)
  G3 discharge   first t with P(CR < 0.8) >= 0.7 AND non-negative median-
                 margin drift over the trailing 3 grid points -> step down

Gates act on posterior tail probabilities, not point estimates: during
data-sparse stretches the posterior is wide and the tail probabilities stay
calibrated, so a quiet record does not fire gates by accident.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

G1_P, G1_MIN = "p_escalate", 0.6
G2_P, G2_MIN, G2_RUN = "p_infeasible", 0.5, 2
G3_P, G3_MIN, G3_DRIFT_PTS = "p_recovered", 0.7, 3


@dataclass
class GateEvents:
    g1_escalate: float | None
    g2_admit: float | None
    g3_discharge: float | None

    def as_dict(self) -> dict:
        return dict(g1_escalate=self.g1_escalate, g2_admit=self.g2_admit,
                    g3_discharge=self.g3_discharge)


def _first(traj: pd.DataFrame, mask: np.ndarray) -> float | None:
    idx = np.flatnonzero(mask)
    return float(traj["t"].iloc[idx[0]]) if len(idx) else None


def evaluate_gates(traj: pd.DataFrame,
                   g3_after: float | None = None) -> GateEvents:
    """traj: filter output, time-ordered. g3_after: earliest time G3 may
    fire (typically the ICU segment start)."""
    g1 = _first(traj, (traj[G1_P] >= G1_MIN).to_numpy())

    hit = (traj[G2_P] >= G2_MIN).to_numpy()
    run = np.zeros(len(hit), dtype=int)
    for i, h in enumerate(hit):
        run[i] = run[i - 1] + 1 if (h and i > 0) else int(h)
    g2 = _first(traj, run >= G2_RUN)

    m = traj["M_med"].to_numpy()
    drift = np.full(len(m), -np.inf)
    if len(m) >= G3_DRIFT_PTS:
        drift[G3_DRIFT_PTS - 1:] = (m[G3_DRIFT_PTS - 1:]
                                    - m[: len(m) - G3_DRIFT_PTS + 1])
    ok = (traj[G3_P] >= G3_MIN).to_numpy() & (drift >= 0.0)
    if g3_after is not None:
        ok &= traj["t"].to_numpy() >= g3_after
    g3 = _first(traj, ok)

    return GateEvents(g1, g2, g3)

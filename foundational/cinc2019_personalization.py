#!/usr/bin/env python3
"""Person-level dispersion aggregates for the CinC-2019 cohort.

R_self and C_self are personal parameters: capacity varies widely between
patients facing comparable load, and feasibility at matched load is decided
by the patient's own restoration rate. This script reduces the local
per-patient table (data/cinc2019/cinc2019_metrics.parquet, produced by
cinc2019_cself.py; gitignored) to two committed aggregates:

  cinc2019_rc_hist2d.csv    2-D histogram of (R_self, C_self) in events/day
  cinc2019_personal_band.csv  same-load band (middle R quintile) summary:
                              capacity quartiles x feasibility, band edges,
                              dispersion quantiles, sepsis capacity medians

No per-patient rows leave data/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DAYS = 365.25          # parquet rates are per-year; report per-day


def main() -> None:
    m = pd.read_parquet(HERE / "data/cinc2019/cinc2019_metrics.parquet")
    r_day = m.R_self / DAYS
    c_day = m.C_self / DAYS

    # --- committed aggregate 1: 2-D histogram, events/day ---
    edges = np.linspace(0, 40, 81)
    h, xe, ye = np.histogram2d(r_day, c_day, bins=[edges, edges])
    rows = []
    for i in range(len(xe) - 1):
        for j in range(len(ye) - 1):
            if h[i, j] > 0:
                rows.append(dict(
                    R_lo=round(xe[i], 2), R_hi=round(xe[i + 1], 2),
                    C_lo=round(ye[j], 2), C_hi=round(ye[j + 1], 2),
                    count=int(h[i, j])))
    pd.DataFrame(rows).to_csv(HERE / "cinc2019_rc_hist2d.csv", index=False)

    # --- committed aggregate 2: same-load band summary ---
    lo, hi = m.R_self.quantile([0.4, 0.6])
    band = m[(m.R_self >= lo) & (m.R_self <= hi)].copy()
    band["Cq"] = pd.qcut(band.C_self, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    tab = band.groupby("Cq", observed=True).agg(
        n=("CR", "size"),
        feasible_frac=("CR", lambda s: round(float((s < 1).mean()), 4)),
        CR_median=("CR", lambda s: round(float(s.median()), 4)),
        C_day_median=("C_self", lambda s: round(float(s.median()) / DAYS, 2)),
    ).reset_index()
    tab.to_csv(HERE / "cinc2019_personal_band.csv", index=False)

    qc = band.C_self.quantile([0.05, 0.95])
    summary = dict(
        n_cohort=len(m),
        R_day_p5_p95=[round(float(r_day.quantile(q)), 2) for q in (0.05, 0.95)],
        C_day_p5_p95=[round(float(c_day.quantile(q)), 2) for q in (0.05, 0.95)],
        pearson_RC=round(float(m.R_self.corr(m.C_self)), 3),
        band_R_day=[round(float(lo) / DAYS, 2), round(float(hi) / DAYS, 2)],
        band_n=len(band),
        band_C_day_p5_p95=[round(float(qc[0.05]) / DAYS, 2),
                           round(float(qc[0.95]) / DAYS, 2)],
        band_C_spread_x=round(float(qc[0.95] / qc[0.05]), 2),
        band_C_day_median_sepsis=round(
            float(band[band.sepsis == 1].C_self.median()) / DAYS, 2),
        band_C_day_median_non=round(
            float(band[band.sepsis == 0].C_self.median()) / DAYS, 2),
    )
    (HERE / "cinc2019_personal_summary.json").write_text(
        json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""eICU-CRD Demo v2.0.1 -> per-stay (C_self, R_self, CR, SR): the fourth
open verification cohort (real, multi-center, openly downloadable without
credentialing).

Same estimator, same band policy as the CinC-2019 driver (standard adult
clinical reference intervals; the database ships none usable per-assay in
the demo). Documented adaptations for this source:
  - lab times are labresultoffset minutes from unit admission
  - periodic vitals (5-min cadence) are resampled to hourly medians per
    stay, matching the CinC charting cadence
  - outcome label = unitdischargestatus (Alive / Expired)

Outputs aggregates only (eicu_demo_results.json); raw data stays in
exemplar/data/ (gitignored, re-pullable from PhysioNet).

Usage: python3 eicu_demo_cself.py [--data ../exemplar/data/...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "proceedings" / "cself"))
from csself_estimator import _union_length, excursion_intervals  # noqa: E402

from cinc2019_cself import rank_auc, wilson  # noqa: E402

YEAR = 365.25
SPAN_FLOOR_DAYS = 2.0 / 24.0
MIN_SERIES = 5

LAB_PANEL: dict[str, tuple[float, float]] = {
    "sodium": (135, 145), "potassium": (3.5, 5.0), "chloride": (96, 106),
    "calcium": (8.5, 10.5), "creatinine": (0.5, 1.2), "glucose": (70, 140),
    "BUN": (7, 20), "albumin": (3.5, 5.0), "ALT (SGPT)": (7, 56),
    "AST (SGOT)": (10, 40), "total bilirubin": (0.1, 1.2),
    "lactate": (0.5, 2.0), "magnesium": (1.7, 2.2),
    "phosphate": (2.5, 4.5), "WBC x 1000": (4, 12), "Hgb": (11.5, 17.5),
    "Hct": (36, 50), "platelets x 1000": (150, 400), "PTT": (25, 35),
    "fibrinogen": (200, 400), "pH": (7.35, 7.45), "paCO2": (35, 45),
    "paO2": (75, 100), "bicarbonate": (22, 28), "Base Excess": (-2, 2),
}
PERIODIC_PANEL: dict[str, tuple[float, float]] = {
    "heartrate": (60, 100), "respiration": (12, 20), "sao2": (95, 100),
    "temperature": (36.0, 38.0),
}
APERIODIC_PANEL: dict[str, tuple[float, float]] = {
    "noninvasivesystolic": (90, 140), "noninvasivediastolic": (60, 90),
    "noninvasivemean": (65, 105),
}


def _find_csv(root: Path, name: str) -> Path:
    hits = list(root.rglob(name))
    if not hits:
        raise SystemExit(f"missing {name} under {root}")
    return hits[0]


def load_series(data: Path) -> dict[int, list[tuple[np.ndarray, np.ndarray,
                                                    float, float]]]:
    """Per stay: list of (t_days, values, lo, hi) series."""
    series: dict[int, list] = {}

    lab = pd.read_csv(_find_csv(data, "lab.csv.gz"),
                      usecols=["patientunitstayid", "labresultoffset",
                               "labname", "labresult"])
    lab = lab[lab.labname.isin(LAB_PANEL)].dropna(subset=["labresult"])
    for (sid, name), g in lab.groupby(["patientunitstayid", "labname"]):
        g = g.sort_values("labresultoffset")
        lo, hi = LAB_PANEL[name]
        series.setdefault(int(sid), []).append(
            (g.labresultoffset.to_numpy(float) / (60 * 24),
             g.labresult.to_numpy(float), lo, hi))

    vp = pd.read_csv(_find_csv(data, "vitalPeriodic.csv.gz"),
                     usecols=["patientunitstayid", "observationoffset",
                              *PERIODIC_PANEL])
    vp["hour"] = vp.observationoffset // 60
    hourly = (vp.groupby(["patientunitstayid", "hour"])[list(PERIODIC_PANEL)]
              .median().reset_index())
    for name, (lo, hi) in PERIODIC_PANEL.items():
        sub = hourly.dropna(subset=[name])
        for sid, g in sub.groupby("patientunitstayid"):
            g = g.sort_values("hour")
            series.setdefault(int(sid), []).append(
                (g.hour.to_numpy(float) / 24.0,
                 g[name].to_numpy(float), lo, hi))

    va = pd.read_csv(_find_csv(data, "vitalAperiodic.csv.gz"),
                     usecols=["patientunitstayid", "observationoffset",
                              *APERIODIC_PANEL])
    for name, (lo, hi) in APERIODIC_PANEL.items():
        sub = va.dropna(subset=[name])
        for sid, g in sub.groupby("patientunitstayid"):
            g = g.sort_values("observationoffset")
            series.setdefault(int(sid), []).append(
                (g.observationoffset.to_numpy(float) / (60 * 24),
                 g[name].to_numpy(float), lo, hi))
    return series


def stay_metrics(slist: list) -> dict | None:
    intervals: list[tuple[float, float]] = []
    n_onset = n_restored = 0
    t_lo, t_hi = np.inf, -np.inf
    for t, v, lo, hi in slist:
        if len(t) < MIN_SERIES:
            continue
        t_lo, t_hi = min(t_lo, float(t[0])), max(t_hi, float(t[-1]))
        ivs, nres = excursion_intervals(t, v, lo, hi)
        intervals.extend(ivs)
        n_onset += len(ivs)
        n_restored += nres
    if n_onset < max(MIN_SERIES, 2) or n_restored == 0:
        return None
    span = max(t_hi - t_lo, SPAN_FLOOR_DAYS)
    busy = _union_length(intervals)
    if busy <= 0:
        return None
    r = n_onset / span * YEAR
    c = n_restored / busy * YEAR
    return dict(CR=r / c, SR=sum(e - o for o, e in intervals) / span,
                R_self=r, C_self=c, n_onset=n_onset, span_days=span)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).parent.parent
                                          / "exemplar" / "data"))
    a = ap.parse_args()
    data = Path(a.data)

    pat = pd.read_csv(_find_csv(data, "patient.csv.gz"),
                      usecols=["patientunitstayid", "unitdischargestatus"])
    status = pat.set_index("patientunitstayid").unitdischargestatus

    series = load_series(data)
    rows = []
    for sid, slist in series.items():
        m = stay_metrics(slist)
        if m is None:
            continue
        m["stay"] = sid
        m["expired"] = int(status.get(sid, "") == "Expired")
        rows.append(m)
    m = pd.DataFrame(rows)
    print(f"placeable stays: {len(m)} of {len(series)}")

    k = int((m.CR < 1).sum())
    p, lo, hi = wilson(k, len(m))
    ex, al = m[m.expired == 1], m[m.expired == 0]
    kx, ka = int((ex.CR < 1).sum()), int((al.CR < 1).sum())
    px, lox, hix = wilson(kx, len(ex))
    pa, loa, hia = wilson(ka, len(al))
    out = dict(
        n=len(m), feasible_frac=round(p, 4),
        feasible_ci=[round(lo, 4), round(hi, 4)],
        CR_median=round(float(m.CR.median()), 4),
        SR_median=round(float(m.SR.median()), 4),
        span_days_median=round(float(m.span_days.median()), 2),
        n_expired=len(ex), n_alive=len(al),
        CR_median_expired=round(float(ex.CR.median()), 4),
        CR_median_alive=round(float(al.CR.median()), 4),
        feasible_frac_expired=round(px, 4),
        feasible_ci_expired=[round(lox, 4), round(hix, 4)],
        feasible_frac_alive=round(pa, 4),
        feasible_ci_alive=[round(loa, 4), round(hia, 4)],
        auc_CR_expired=round(rank_auc(ex.CR.to_numpy(),
                                      al.CR.to_numpy()), 4),
        auc_SR_expired=round(rank_auc(ex.SR.to_numpy(),
                                      al.SR.to_numpy()), 4),
    )
    (Path(__file__).parent / "eicu_demo_results.json").write_text(
        json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

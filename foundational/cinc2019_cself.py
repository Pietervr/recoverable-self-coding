#!/usr/bin/env python3
"""C_self / R_self / CR / SR on the PhysioNet/CinC Challenge 2019 cohort.

Data: 40,336 ICU stays (training_setA = 20,336, BIDMC; training_setB = 20,000,
Emory), hourly rows, 8 vitals + 26 labs, CC-BY 4.0, fetched by
fetch_cinc2019.py. Same construct as the proceedings' estimator
(proceedings/cself/csself_estimator.py): homeostasis as a self-decoder — a
monitored variable crossing outside its reference band is a candidate
commitment (excursion), its return in-range is a certification (restore).

    R_self = excursion onsets / observation time      (arrival rate lambda)
    C_self = restorations / system-busy time          (service rate mu)
    CR     = R_self / C_self                          (load, FROM RATES)
    SR     = mean # variables out of range            (occupancy, FROM N(t))

Documented adaptations for the ICU-hourly setting (vs the ambulatory Synthea /
MIMIC-demo drivers):
  * Time base is hours (ICULOS), converted to days; the observation-span floor
    is 2 h (not 1 day — ICU stays are ~2 days; a 1-day floor would deflate
    short-stay rates).
  * CinC-2019 ships no reference ranges, so standard adult clinical reference
    intervals are hard-coded per variable below (the proceedings' MIMIC driver
    used MIMIC's own ref_range fields instead). FiO2 (a ventilator setting) and
    EtCO2 (sparse capnography) are excluded from the panel.
  * min_series_length = 5 points per variable: hourly vitals qualify for nearly
    all stays; sparse labs qualify only for longer stays (they add signal, not
    bias — excursion logic requires a fresh in-range->out-of-range crossing,
    so admission-deranged values are left-censored, not counted).

Outputs (aggregates only; no per-patient rows leave data/):
  cinc2019_results.json          cohort + per-set + sepsis-split summaries
  cinc2019_regime_hist.csv       CR and SR histograms (small cells suppressed)
  cinc2019_srcr_binned.csv       median SR per CR bin vs CR/(1-CR) (queue-law
                                 comparison; interpret with the stationarity
                                 caveat - ICU stays are short)

Usage: python3 cinc2019_cself.py [--data data/cinc2019] [--min-patients 100]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "proceedings" / "cself"))
from csself_estimator import _union_length, excursion_intervals  # noqa: E402

YEAR = 365.25
SPAN_FLOOR_DAYS = 2.0 / 24.0          # 2 hours
MIN_SERIES = 5

# Standard adult clinical reference intervals (documented adaptation: the
# dataset ships none). Vitals first (dense, hourly), then labs (sparse).
PANEL: dict[str, tuple[float, float]] = {
    "HR": (60, 100), "O2Sat": (95, 100), "Temp": (36.0, 38.0),
    "SBP": (90, 140), "MAP": (65, 105), "DBP": (60, 90), "Resp": (12, 20),
    "BaseExcess": (-2, 2), "HCO3": (22, 28), "pH": (7.35, 7.45),
    "PaCO2": (35, 45), "SaO2": (94, 100), "AST": (10, 40), "BUN": (7, 20),
    "Alkalinephos": (44, 147), "Calcium": (8.5, 10.5), "Chloride": (96, 106),
    "Creatinine": (0.5, 1.2), "Bilirubin_direct": (0.0, 0.3),
    "Glucose": (70, 140), "Lactate": (0.5, 2.0), "Magnesium": (1.7, 2.2),
    "Phosphate": (2.5, 4.5), "Potassium": (3.5, 5.0),
    "Bilirubin_total": (0.1, 1.2), "TroponinI": (0.0, 0.04),
    "Hct": (36, 50), "Hgb": (11.5, 17.5), "PTT": (25, 35), "WBC": (4, 12),
    "Fibrinogen": (200, 400), "Platelets": (150, 400),
}


def patient_metrics(psv: Path) -> dict | None:
    df = pd.read_csv(psv, sep="|", na_values="NaN")
    if "ICULOS" not in df.columns or len(df) < MIN_SERIES:
        return None
    t_days = df["ICULOS"].to_numpy(float) / 24.0
    intervals: list[tuple[float, float]] = []
    n_onset = n_restored = 0
    for code, (lo, hi) in PANEL.items():
        if code not in df.columns:
            continue
        v = df[code].to_numpy(float)
        mask = np.isfinite(v)
        if mask.sum() < MIN_SERIES:
            continue
        ivs, nres = excursion_intervals(t_days[mask], v[mask], lo, hi)
        intervals.extend(ivs)
        n_onset += len(ivs)
        n_restored += nres
    if n_onset < max(MIN_SERIES, 2) or n_restored == 0:
        return None
    span = max(t_days[-1] - t_days[0], SPAN_FLOOR_DAYS)
    busy = _union_length(intervals)
    if busy <= 0:
        return None
    occupancy_time = sum(r - o for (o, r) in intervals)
    r_self = n_onset / span * YEAR
    c_self = n_restored / busy * YEAR
    return dict(
        CR=r_self / c_self, SR=occupancy_time / span,
        R_self=r_self, C_self=c_self, n_onset=n_onset,
        censored=n_onset - n_restored,
        sepsis=int(df.get("SepsisLabel", pd.Series([0])).fillna(0).max() > 0),
        span_days=float(span),
    )


def wilson(k: int, n: int, z: float = 1.959963985) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def rank_auc(x: np.ndarray, y: np.ndarray) -> float:
    """P(X > Y) by ranks (Mann-Whitney AUC), numpy-only."""
    both = np.concatenate([x, y])
    ranks = pd.Series(both).rank().to_numpy()
    rx = ranks[: len(x)].sum()
    u = rx - len(x) * (len(x) + 1) / 2
    return float(u / (len(x) * len(y)))


def summarize(m: pd.DataFrame) -> dict:
    k = int((m["R_self"] < m["C_self"]).sum())
    n = len(m)
    p, lo, hi = wilson(k, n)
    return dict(
        n=n, feasible_k=k,
        feasible_frac=round(p, 4), feasible_ci=[round(lo, 4), round(hi, 4)],
        CR_median=round(float(m["CR"].median()), 4),
        SR_median=round(float(m["SR"].median()), 4),
        R_self_median_per_yr=round(float(m["R_self"].median()), 1),
        C_self_median_per_yr=round(float(m["C_self"].median()), 1),
        censored_frac=round(float(m["censored"].sum() / m["n_onset"].sum()), 4),
        span_days_median=round(float(m["span_days"].median()), 2),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).parent / "data" / "cinc2019"))
    ap.add_argument("--out", default=str(Path(__file__).parent))
    ap.add_argument("--min-patients", type=int, default=100)
    a = ap.parse_args()
    data, out = Path(a.data), Path(a.out)

    rows = []
    t0 = time.time()
    for set_name in ("training_setA", "training_setB"):
        files = sorted((data / set_name).glob("p*.psv"))
        print(f"[cinc] {set_name}: {len(files)} files", flush=True)
        for i, f in enumerate(files):
            r = patient_metrics(f)
            if r is not None:
                r["set"] = set_name[-1]
                rows.append(r)
            if (i + 1) % 5000 == 0:
                print(f"[cinc]  {set_name} {i+1}/{len(files)} "
                      f"({(i+1)/max(time.time()-t0,1):.0f}/s)", flush=True)
    m = pd.DataFrame(rows)
    if len(m) < a.min_patients:
        raise SystemExit(f"[cinc] only {len(m)} patients placed — data incomplete?")

    res = {
        "data_source": ("PhysioNet/CinC Challenge 2019 training data v1.0.0 "
                        "(CC-BY 4.0), 8 vitals + 26 labs, hourly"),
        "estimator": ("proceedings/cself/csself_estimator.py excursion/restore "
                      "logic; ICU adaptations per cinc2019_cself.py docstring"),
        "panel_size": len(PANEL),
        "cohort": summarize(m),
        "by_set": {s: summarize(m[m["set"] == s]) for s in ("A", "B")},
        "by_sepsis": {
            "sepsis": summarize(m[m["sepsis"] == 1]),
            "non_sepsis": summarize(m[m["sepsis"] == 0]),
        },
        "sepsis_discrimination": {
            "CR_auc_sepsis_gt_nonsepsis": round(rank_auc(
                m.loc[m.sepsis == 1, "CR"].to_numpy(),
                m.loc[m.sepsis == 0, "CR"].to_numpy()), 4),
            "SR_auc_sepsis_gt_nonsepsis": round(rank_auc(
                m.loc[m.sepsis == 1, "SR"].to_numpy(),
                m.loc[m.sepsis == 0, "SR"].to_numpy()), 4),
        },
    }
    (out / "cinc2019_results.json").write_text(json.dumps(res, indent=2))

    # per-patient table stays LOCAL (data/ is gitignored); aggregates only below
    m.to_parquet(data / "cinc2019_metrics.parquet")

    # aggregate histograms (small-cell suppression at 10), incl. sepsis split
    groups = {"cohort": m, "sepsis": m[m.sepsis == 1], "non_sepsis": m[m.sepsis == 0]}
    hists = []
    for col in ("CR", "SR", "R_self", "C_self"):
        rng = (float(m[col].quantile(0.001)), float(m[col].quantile(0.999)))
        for gname, gdf in groups.items():
            counts, edges = np.histogram(gdf[col], bins=60, range=rng)
            counts = np.where(counts < 10, 0, counts)
            hists.append(pd.DataFrame({
                "quantity": col, "group": gname,
                "bin_center": (edges[:-1] + edges[1:]) / 2, "count": counts}))
    pd.concat(hists).to_csv(out / "cinc2019_regime_hist.csv", index=False)

    # SR vs CR binned (queue-law comparison, sub-boundary bins only)
    sub = m[(m["CR"] > 0.05) & (m["CR"] < 0.98)]
    bins = np.linspace(0.05, 0.98, 25)
    idx = np.digitize(sub["CR"], bins)
    rows2 = []
    for b in range(1, len(bins)):
        grp = sub[idx == b]
        if len(grp) >= 30:
            cc = float(grp["CR"].median())
            rows2.append(dict(CR_bin=round(cc, 4),
                              SR_median=round(float(grp["SR"].median()), 4),
                              SR_q25=round(float(grp["SR"].quantile(.25)), 4),
                              SR_q75=round(float(grp["SR"].quantile(.75)), 4),
                              theory=round(cc / (1 - cc), 4), n=len(grp)))
    pd.DataFrame(rows2).to_csv(out / "cinc2019_srcr_binned.csv", index=False)

    print(json.dumps(res["cohort"], indent=2))
    print(json.dumps(res["by_sepsis"], indent=2))
    print(json.dumps(res["sepsis_discrimination"], indent=2))
    print(f"[cinc] wrote results to {out} in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()

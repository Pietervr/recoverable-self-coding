#!/usr/bin/env python3
"""The real-physiology estimates reported in Section 3 of the proceedings.

Runs the UNCHANGED v2 estimator (csself_estimator.py) — same 13-analyte panel as
the Synthea figure — on the MIMIC-IV Clinical Database Demo: 100 intensive-care
patients with real ICD-10 diagnoses and real laboratory series, read against the
database's OWN per-assay reference bands (labevents.ref_range_lower/upper, taken
as the median per itemid) rather than the textbook ranges used for Synthea.

Reproduces the numbers in the paper:
    units on the regime map .......... 78 / 100
    degenerate in either rate ........ 0
    below the feasibility boundary ... ~45%   (vs ~90% for ambulatory Synthea)
    median CR ........................ ~1.02  (the boundary itself)

Only aggregates are printed; no patient rows are emitted.

Data — openly licensed (Open Data Commons ODbL), NO credentialing and NO data
use agreement required:
    https://physionet.org/content/mimic-iv-demo/2.2/
    Johnson, A. et al. MIMIC-IV Clinical Database Demo (v2.2). PhysioNet, 2023.
    doi:10.13026/dp1f-ex47

    python3 mimic_demo_cself.py --download          # fetches the 3 tables it needs
    python3 mimic_demo_cself.py --data /path/to/hosp

NOTE: this is the openly licensed *demo*. The full MIMIC-IV database is
credentialed and carries a DUA; nothing in this script touches it.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import csself_estimator as est

BASE_URL = "https://physionet.org/files/mimic-iv-demo/2.2/hosp"
TABLES = ["labevents.csv.gz", "diagnoses_icd.csv.gz", "patients.csv.gz"]

DELTA_T_DAYS = 30    # clinical readout only (not used by CR or SR)
MIN_SERIES = 4

# MIMIC itemid -> analyte. Same 13-analyte panel as the Synthea figure.
CSELF_ITEMS = {
    50983: "SODIUM", 50971: "POTASSIUM", 50893: "CALCIUM", 50912: "CREATININE",
    50931: "GLUCOSE", 51006: "UREA_NITROGEN", 51222: "HEMOGLOBIN",
    51221: "HEMATOCRIT", 51301: "WBC", 51265: "PLATELETS", 50861: "ALT",
    50878: "AST", 50862: "ALBUMIN",
}


def download(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        out = dest / t
        if out.exists():
            print(f"  have {t}")
            continue
        print(f"  fetching {t} ...")
        urllib.request.urlretrieve(f"{BASE_URL}/{t}", out)


def read_labevents(data: Path) -> pd.DataFrame:
    le = pd.read_csv(data / "labevents.csv.gz",
                     usecols=["subject_id", "itemid", "charttime", "valuenum",
                              "ref_range_lower", "ref_range_upper"],
                     low_memory=False).dropna(subset=["valuenum"])
    le["_dt"] = pd.to_datetime(le["charttime"], errors="coerce")
    return le.dropna(subset=["_dt"])


def build_labs(le: pd.DataFrame):
    """`labs` contract, with MIMIC's own reference bands (median per assay)."""
    sub = le[le["itemid"].isin(CSELF_ITEMS)].copy()
    sub["code"] = sub["itemid"].map(CSELF_ITEMS)
    rng = sub.groupby("code")[["ref_range_lower", "ref_range_upper"]].median()
    t0 = sub["_dt"].min()
    sub["t"] = ((sub["_dt"] - t0).dt.total_seconds() / 86400.0).round().astype(int)
    labs = (sub.groupby(["subject_id", "code", "t"], as_index=False)["valuenum"].mean()
               .rename(columns={"subject_id": "pid", "valuenum": "value"}))
    labs["ref_low"] = labs["code"].map(rng["ref_range_lower"])
    labs["ref_high"] = labs["code"].map(rng["ref_range_upper"])
    labs = labs.dropna(subset=["ref_low", "ref_high"])
    return labs[["pid", "code", "t", "value", "ref_low", "ref_high"]], rng


def build_events(data: Path):
    dx = pd.read_csv(data / "diagnoses_icd.csv.gz", dtype={"icd_code": str})
    dx10 = dx[dx["icd_version"] == 10].copy()
    events = pd.DataFrame({
        "pid": dx10["subject_id"],
        "icd10": dx10["icd_code"],
        "t": 0,
        "chronic": True,
    })
    burden = (dx10.groupby("subject_id")["icd_code"].nunique()
                  .rename("n_icd10").reset_index())
    return events, burden


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=Path("mimic_demo/hosp"),
                    help="directory holding the MIMIC-IV demo `hosp` tables")
    ap.add_argument("--download", action="store_true",
                    help="fetch the three tables into --data first")
    a = ap.parse_args()

    if a.download:
        download(a.data)

    le = read_labevents(a.data)
    labs, rng = build_labs(le)
    events, burden = build_events(a.data)
    print(f"lab units in panel: {labs['pid'].nunique()}   analytes: {labs['code'].nunique()}")
    print(f"ICD-10: {len(events):,} rows, median {burden['n_icd10'].median():.0f} codes/unit")

    cfg = {
        "panel": [{"code": name,
                   "ref_low": float(rng.loc[name, "ref_range_lower"]),
                   "ref_high": float(rng.loc[name, "ref_range_upper"])}
                  for name in CSELF_ITEMS.values() if name in rng.index],
        "delta_t_days": DELTA_T_DAYS,
        "min_series_length": MIN_SERIES,
        "aggregation": {"suppress_cell_below": 5, "histogram_bins": 25},
    }

    m = est.per_patient_metrics(labs, events, cfg)
    m = m[np.isfinite(m["CR"]) & np.isfinite(m["C_self"]) & np.isfinite(m["R_self"])]
    margin = m["C_self"] - m["R_self"]

    print(f"\nunits on the regime map: {len(m)}")
    for col in ["R_self", "C_self", "CR"]:
        x = m[col].to_numpy()
        print(f"  {col:7s} median={np.median(x):9.3f}   "
              f"IQR=[{np.percentile(x, 25):.3f}, {np.percentile(x, 75):.3f}]")
    print(f"  below the feasibility boundary (M >= 0): "
          f"{(margin >= 0).mean():.1%}  ({int((margin >= 0).sum())}/{len(m)})")
    print(f"  degenerate (R_self == 0 or C_self == 0): "
          f"{int(((m['R_self'] == 0) | (m['C_self'] == 0)).sum())}")

    res = {
        "data_source": "MIMIC-IV Clinical Database Demo v2.2 (PhysioNet, ODbL, 100 ICU patients)",
        "reference_ranges": "MIMIC's own labevents ref_range fields (median per itemid)",
        "n_units_on_regime_map": int(len(m)),
        "n_degenerate": int(((m["R_self"] == 0) | (m["C_self"] == 0)).sum()),
        "feasible_fraction_R_lt_C": float((margin >= 0).mean()),
        "CR_median": float(m["CR"].median()),
        "R_self_median_per_yr": float(m["R_self"].median()),
        "C_self_median_per_yr": float(m["C_self"].median()),
        "icd10_median_codes_per_unit": float(burden["n_icd10"].median()),
        "note": ("Absolute rates are not comparable with the ambulatory Synthea cohort "
                 "(ICU series run over days, ambulatory ones over years); CR, being "
                 "dimensionless, is the compared quantity. A face-validity check on "
                 "measurability, not a validation."),
    }
    out = Path(__file__).resolve().parent / "mimic_demo_cself_results.json"
    out.write_text(json.dumps(res, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

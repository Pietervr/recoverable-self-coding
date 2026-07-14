#!/usr/bin/env python3
"""Synthea -> per-unit (C_self, R_self, CR, SR): the input behind Figure 1.

Reads the Synthea 10k COVID-19 synthetic cohort, keeps a fixed 13-analyte
metabolic / haematology / liver panel with standard adult reference ranges,
normalizes to the estimator's `labs` contract, and runs the unchanged v2
estimator (csself_estimator.py).

Writes cself_measured_synthea.csv (C_self, R_self, CR, SR per unit) — the file
proceedings/figures/make_cself_measured.py plots as Figure 1 — plus a
results.json of the aggregates.

Data (openly downloadable, no registration):
  https://synthetichealth.github.io/synthea-sample-data/downloads/10k_synthea_covid19_csv.zip
Unzip it and point --data at the resulting 10k_synthea_covid19_csv directory.

  python3 synthea_to_cself.py --data /path/to/10k_synthea_covid19_csv \
                              --out ../figures/cself_measured_synthea.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

import csself_estimator as est

# LOINC code -> (analyte, ref_low, ref_high); standard adult ranges
PANEL = {
    "2951-2":  ("SODIUM",       135.0, 145.0),
    "2823-3":  ("POTASSIUM",      3.5,   5.1),
    "17861-6": ("CALCIUM",        8.5,  10.5),
    "2160-0":  ("CREATININE",     0.6,   1.3),
    "2345-7":  ("GLUCOSE",       70.0, 140.0),
    "3094-0":  ("UREA_NITROGEN",  7.0,  20.0),
    "718-7":   ("HEMOGLOBIN",    12.0,  17.5),
    "4544-3":  ("HEMATOCRIT",    36.0,  50.0),
    "6690-2":  ("WBC",            4.5,  11.0),
    "777-3":   ("PLATELETS",    150.0, 400.0),
    "1742-6":  ("ALT",            7.0,  56.0),
    "1920-8":  ("AST",           10.0,  40.0),
    "1751-7":  ("ALBUMIN",        3.5,   5.0),
}

DELTA_T_DAYS = 30    # clinical readout only (not used by CR or SR)
MIN_SERIES = 4       # >= 4 readings of an analyte for a unit to count


def build_labs(data: Path) -> pd.DataFrame:
    obs = pd.read_csv(data / "observations.csv",
                      usecols=["DATE", "PATIENT", "CODE", "VALUE", "TYPE"],
                      dtype={"CODE": str, "TYPE": str}, low_memory=False)
    obs = obs[(obs["TYPE"] == "numeric") & (obs["CODE"].isin(PANEL))].copy()
    obs["value"] = pd.to_numeric(obs["VALUE"], errors="coerce")
    obs = obs.dropna(subset=["value"])
    obs["code"] = obs["CODE"].map(lambda c: PANEL[c][0])
    dt = pd.to_datetime(obs["DATE"], utc=True, errors="coerce")
    obs = obs.assign(_dt=dt).dropna(subset=["_dt"])
    t0 = obs["_dt"].min()
    obs["day"] = ((obs["_dt"] - t0).dt.total_seconds() / 86400.0).round().astype(int)
    labs = (obs.groupby(["PATIENT", "code", "day"], as_index=False)["value"].mean()
               .rename(columns={"PATIENT": "pid", "day": "t"}))
    rng = {name: (lo, hi) for (name, lo, hi) in PANEL.values()}
    labs["ref_low"] = labs["code"].map(lambda c: rng[c][0])
    labs["ref_high"] = labs["code"].map(lambda c: rng[c][1])
    return labs[["pid", "code", "t", "value", "ref_low", "ref_high"]]


def build_events(data: Path) -> pd.DataFrame:
    con = pd.read_csv(data / "conditions.csv",
                      usecols=["START", "STOP", "PATIENT", "CODE"],
                      dtype={"CODE": str}, low_memory=False)
    dt = pd.to_datetime(con["START"], utc=True, errors="coerce")
    t0 = dt.min()
    return pd.DataFrame({
        "pid": con["PATIENT"],
        "icd10": con["CODE"],
        "t": ((dt - t0).dt.total_seconds() / 86400.0).fillna(0).round().astype(int),
        "chronic": con["STOP"].isna(),   # still-ongoing condition = chronic
    })


def make_config() -> dict:
    return {
        "panel": [{"code": name, "ref_low": lo, "ref_high": hi}
                  for (name, lo, hi) in PANEL.values()],
        "delta_t_days": DELTA_T_DAYS,
        "min_series_length": MIN_SERIES,
        "aggregation": {"suppress_cell_below": 5, "histogram_bins": 25},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, type=Path,
                    help="unzipped 10k_synthea_covid19_csv directory")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parents[1] / "figures" / "cself_measured_synthea.csv")
    a = ap.parse_args()

    labs = build_labs(a.data)
    print(f"labs rows={len(labs):,}  units={labs['pid'].nunique():,}  "
          f"analytes={labs['code'].nunique()}")
    events = build_events(a.data)
    m = est.per_patient_metrics(labs, events, make_config())
    print(f"units placed on the regime map: {len(m):,}")

    feasible = (m["R_self"] < m["C_self"]).mean()
    m[["C_self", "R_self", "CR", "SR"]].to_csv(a.out, index=False)
    print(f"wrote {a.out}")

    res = {
        "data_source": "Synthea 10k COVID-19 synthetic cohort (CSV sample)",
        "n_units_on_regime_map": int(len(m)),
        "feasible_fraction_R_lt_C": float(feasible),
        "CR_median": float(m["CR"].median()),
        "SR_median": float(m["SR"].median()),
        "C_self_median_per_yr": float(m["C_self"].median()),
        "R_self_median_per_yr": float(m["R_self"].median()),
    }
    (a.out.parent / "cself_measured_synthea_results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

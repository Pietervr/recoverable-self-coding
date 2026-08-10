#!/usr/bin/env python3
"""Stage 1 of the RSC exemplar: harmonize every source to one event table.

Contract (all sources, all segments):

    unit     str     patient / stay identifier, prefixed by source
    t_days   float   time in days on the unit's own clock (source epoch noted)
    var      str     variable name (panel key)
    value    float   measured value
    lo, hi   float   reference band for this unit+var

Bands: per-assay where the source ships them; the standard adult clinical
reference intervals otherwise (same policy as the foundational paper's
CinC-2019 driver). This module implements the Synthea loader; CinC and eICU
loaders reuse the panels already defined in foundational/.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SYNTHEA_DIR = HERE / "data" / "10k_synthea_covid19_csv"

# LOINC -> (var, lo, hi). The proceedings 13-analyte core panel plus the
# acute-phase markers the Synthea COVID module charts daily during the
# deterioration arc. Bands are standard adult clinical reference intervals.
SYNTHEA_PANEL: dict[str, tuple[str, float, float]] = {
    # core metabolic / haematology / liver (proceedings panel, unchanged)
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
    # acute-phase markers charted by the COVID module
    "1988-5":  ("CRP",            0.0,  10.0),    # mg/L
    "48065-7": ("D_DIMER",        0.0,   0.5),    # ug/mL FEU
    "2276-4":  ("FERRITIN",      12.0, 300.0),    # ug/L
    "14804-9": ("LDH",          122.0, 222.0),    # U/L
    "731-0":   ("LYMPHOCYTES",    1.0,   4.8),    # 10^3/uL
    "751-8":   ("NEUTROPHILS",    1.8,   7.7),    # 10^3/uL
    "2703-7":  ("PAO2",          75.0, 100.0),    # mmHg (arterial)
    # bedside vitals (charted at encounters; sparse but in-contract)
    "8867-4":  ("HEART_RATE",    60.0, 100.0),
    "9279-1":  ("RESP_RATE",     12.0,  20.0),
    "8310-5":  ("TEMPERATURE",   36.1,  37.8),    # Celsius
    "2708-6":  ("SPO2",          94.0, 100.0),
}


def load_synthea_events(data: Path = SYNTHEA_DIR,
                        patients: list[str] | None = None) -> pd.DataFrame:
    """Synthea observations -> the harmonized event table.

    t_days epoch: each unit's first observation is t=0.
    """
    obs = pd.read_csv(data / "observations.csv",
                      usecols=["DATE", "PATIENT", "CODE", "VALUE", "TYPE"],
                      dtype={"CODE": str, "TYPE": str}, low_memory=False)
    obs = obs[(obs["TYPE"] == "numeric") & (obs["CODE"].isin(SYNTHEA_PANEL))]
    if patients is not None:
        obs = obs[obs["PATIENT"].isin(patients)]
    obs = obs.copy()
    obs["value"] = pd.to_numeric(obs["VALUE"], errors="coerce")
    obs = obs.dropna(subset=["value"])
    dt = pd.to_datetime(obs["DATE"], utc=True, errors="coerce")
    obs = obs.assign(_dt=dt).dropna(subset=["_dt"])

    obs["var"] = obs["CODE"].map(lambda c: SYNTHEA_PANEL[c][0])
    obs["lo"] = obs["CODE"].map(lambda c: SYNTHEA_PANEL[c][1])
    obs["hi"] = obs["CODE"].map(lambda c: SYNTHEA_PANEL[c][2])

    t0 = obs.groupby("PATIENT")["_dt"].transform("min")
    obs["t_days"] = (obs["_dt"] - t0).dt.total_seconds() / 86400.0
    obs["unit"] = "synthea:" + obs["PATIENT"]

    ev = (obs[["unit", "t_days", "var", "value", "lo", "hi"]]
          .sort_values(["unit", "var", "t_days"])
          .reset_index(drop=True))
    return ev


def synthea_anchors(data: Path = SYNTHEA_DIR) -> pd.DataFrame:
    """Per-patient journey anchors: first COVID inpatient admission, ICU
    admission if any, death if any — as absolute timestamps (UTC).
    Offsets onto the unit clock are resolved against the unit's own t=0."""
    enc = pd.read_csv(data / "encounters.csv",
                      usecols=["START", "PATIENT", "ENCOUNTERCLASS",
                               "DESCRIPTION", "REASONDESCRIPTION"])
    enc["_dt"] = pd.to_datetime(enc["START"], utc=True, errors="coerce")

    adm = (enc[(enc.ENCOUNTERCLASS == "inpatient")
               & enc.REASONDESCRIPTION.str.contains("COVID", na=False)]
           .groupby("PATIENT")["_dt"].min().rename("covid_admission"))
    icu = (enc[enc.DESCRIPTION.str.contains("intensive care", case=False,
                                            na=False)]
           .groupby("PATIENT")["_dt"].min().rename("icu_admission"))

    pat = pd.read_csv(data / "patients.csv", usecols=["Id", "DEATHDATE"])
    death = (pd.to_datetime(pat.set_index("Id")["DEATHDATE"], utc=True,
                            errors="coerce").rename("death"))

    out = pd.concat([adm, icu, death], axis=1)
    out.index.name = "patient"
    return out.reset_index()


if __name__ == "__main__":
    ev = load_synthea_events()
    an = synthea_anchors()
    n_units = ev["unit"].nunique()
    print(f"events: {len(ev):,}  units: {n_units:,}  vars: {ev['var'].nunique()}")
    print(ev.groupby("var").size().sort_values(ascending=False).to_string())
    print(f"\nanchors: covid_admission={an.covid_admission.notna().sum()}, "
          f"icu={an.icu_admission.notna().sum()}, "
          f"death={an.death.notna().sum()}")

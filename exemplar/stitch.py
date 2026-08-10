#!/usr/bin/env python3
"""Stage 6 of the RSC exemplar: the journey builder.

Stitches one continuous patient journey from sources with disjoint
strengths, on one clock, in the harmonized event schema:

  pre       Synthea ambulatory baseline + deterioration, up to the COVID
            admission anchor (+0.5 d so admission-day labs are included)
  icu       a real PhysioNet/CinC-2019 stay, spliced at the admission
            anchor, matched on (sepsis flag, whole-stay CR band)
  recovery  the survivor's own post-episode Synthea observations, shifted
            to resume after ICU discharge (the 14 d Synthea in-hospital
            window they replace is dropped)

The deceased journey ends at ICU discharge (death marker); the survivor
continues into the recovery tail. The stitch is placed at the *anchor*
(Synthea ground truth), never at a gate: gates are evaluated afterwards, so
gate-vs-anchor lead time is a readout, not a construction.

Per-segment filter half-lives reflect charting cadence (ambulatory 14 d,
ICU 0.5 d); the filter restarts at regime boundaries because absolute event
rates change with charting intensity by an order of magnitude — CR stays
comparable across segments (dimensionless), absolute rates do not.

A committed stitch index (stitch_index.json) records unit ids, stay files,
and offsets: journeys reproduce exactly from re-pulled raw data.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from estimate import extract_unit, filter_trajectory
from gates import evaluate_gates
from schema import SYNTHEA_DIR, load_synthea_events, synthea_anchors

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "foundational"))
from cinc2019_cself import PANEL as CINC_PANEL, patient_metrics  # noqa: E402

HERE = Path(__file__).resolve().parent
CINC_DIR = Path(__file__).resolve().parent.parent / "foundational" / "data" / "cinc2019"

SYNTHEA_HOSPITAL_WINDOW_DAYS = 14.0    # in-hospital Synthea labs replaced
HALF_LIFE = {"pre": 14.0, "icu": 0.5, "recovery": 14.0}
GRID_STEP = {"pre": 1.0, "icu": 1.0 / 12.0, "recovery": 1.0}
PRE_WINDOW_DAYS = 120.0                # how much baseline the figure shows


def cinc_events(psv: Path) -> pd.DataFrame:
    """One CinC stay -> harmonized events (t_days from ICU hour 0)."""
    df = pd.read_csv(psv, sep="|", na_values="NaN")
    t = df["ICULOS"].to_numpy(float) / 24.0
    rows = []
    for var, (lo, hi) in CINC_PANEL.items():
        if var not in df.columns:
            continue
        v = df[var].to_numpy(float)
        mask = np.isfinite(v)
        for tt, vv in zip(t[mask], v[mask]):
            rows.append((f"cinc:{psv.stem}", float(tt), var, float(vv),
                         float(lo), float(hi)))
    return pd.DataFrame(rows, columns=["unit", "t_days", "var", "value",
                                       "lo", "hi"])


def _end_window_cr(psv: Path, window_days: float = 1.0) -> float:
    """Static CR over the trailing window of a stay (is it ending cold?)."""
    from estimate import extract_unit, static_estimate
    ev = cinc_events(psv)
    t_last = float(ev.t_days.max())
    tail = ev[ev.t_days >= t_last - window_days]
    try:
        return float(static_estimate(extract_unit(tail))["CR"])
    except Exception:
        return float("inf")


def find_stay(sepsis: int, cr_lo: float, cr_hi: float,
              min_span_days: float = 3.0, scan_limit: int = 4000,
              end_cold_below: float | None = None) -> Path:
    """Deterministic scan for a stay matching (sepsis, CR band, span).
    end_cold_below: additionally require the trailing-24 h static CR under
    this value — a discharged-recovering stay, not a mid-course trim."""
    files = sorted((CINC_DIR / "training_setA").glob("p*.psv"))[:scan_limit]
    for f in files:
        m = patient_metrics(f)
        if m is None:
            continue
        if not (m["sepsis"] == sepsis and cr_lo <= m["CR"] <= cr_hi
                and m["span_days"] >= min_span_days):
            continue
        if (end_cold_below is not None
                and _end_window_cr(f) >= end_cold_below):
            continue
        return f
    raise RuntimeError(f"no stay found: sepsis={sepsis} CR in "
                       f"[{cr_lo},{cr_hi}] span>={min_span_days} "
                       f"end_cold<{end_cold_below}")


def _synthea_unit_events(ev: pd.DataFrame, patient: str) -> pd.DataFrame:
    return ev[ev.unit == f"synthea:{patient}"]


def _patient_t0() -> pd.Series:
    obs = pd.read_csv(SYNTHEA_DIR / "observations.csv",
                      usecols=["DATE", "PATIENT"], low_memory=False)
    dt = pd.to_datetime(obs.DATE, utc=True, errors="coerce")
    return obs.assign(_dt=dt).groupby("PATIENT")._dt.min()


def _admission_offset(patient: str, adm_ts: pd.Timestamp,
                      t0map: pd.Series) -> float:
    return (adm_ts - t0map[patient]).total_seconds() / 86400.0


def build_journey(kind: str, ev: pd.DataFrame, an: pd.DataFrame,
                  patient: str, stay: Path, t0map: pd.Series) -> dict:
    """kind: 'survivor' | 'deceased'. Returns segments, trajectories, gates,
    and the stitch record."""
    row = an[an.patient == patient].iloc[0]
    t_adm = _admission_offset(patient, row.covid_admission, t0map)
    unit_ev = _synthea_unit_events(ev, patient)

    icu_ev = cinc_events(stay)
    icu_span = float(icu_ev.t_days.max())

    segments: list[tuple[str, pd.DataFrame, float]] = []
    pre = unit_ev[unit_ev.t_days <= t_adm + 0.5]
    segments.append(("pre", pre, 0.0))
    segments.append(("icu", icu_ev, t_adm))
    if kind == "survivor":
        tail = unit_ev[unit_ev.t_days
                       > t_adm + SYNTHEA_HOSPITAL_WINDOW_DAYS].copy()
        if len(tail) >= 10:
            shift = (t_adm + icu_span + 1.0) - float(tail.t_days.min())
            tail["t_days"] = tail.t_days + shift
            segments.append(("recovery", tail, 0.0))

    trajs = []
    for name, seg_ev, offset in segments:
        u = extract_unit(seg_ev)
        lo = (max(u.t_first, u.t_last - PRE_WINDOW_DAYS) if name == "pre"
              else u.t_first)
        grid = np.arange(lo, u.t_last + GRID_STEP[name] / 2, GRID_STEP[name])
        traj = filter_trajectory(u, grid, half_life_days=HALF_LIFE[name])
        traj["t_journey"] = traj.t + offset
        traj["segment"] = name
        trajs.append(traj)
    traj_all = (pd.concat(trajs, ignore_index=True)
                .sort_values("t_journey").reset_index(drop=True))

    icu_start = t_adm
    gates = evaluate_gates(
        traj_all.rename(columns={"t_journey": "t", "t": "t_seg"}),
        g3_after=icu_start)

    return dict(
        kind=kind, patient=patient, stay=stay.name, t_adm=t_adm,
        icu_span=icu_span, traj=traj_all, gates=gates,
        anchors=dict(admission=t_adm,
                     death=(t_adm + icu_span if kind == "deceased" else None)),
    )


def main() -> None:
    ev = load_synthea_events()
    an = synthea_anchors()
    t0map = _patient_t0()
    counts = ev.groupby("unit").size()

    def best(mask: pd.Series) -> str:
        cands = [c for c in ("synthea:" + an[mask].patient)
                 if counts.get(c, 0) > 0]
        return max(cands, key=lambda c: counts[c]).split(":", 1)[1]

    def best_with_tail(mask: pd.Series) -> str:
        """Survivor with the longest post-episode record (so the recovery
        arc can complete), given a dense pre-admission record."""
        scored = []
        for pat in an[mask].patient:
            unit = f"synthea:{pat}"
            if counts.get(unit, 0) < 100:
                continue
            row = an[an.patient == pat].iloc[0]
            t_adm = _admission_offset(pat, row.covid_admission, t0map)
            sub = ev[ev.unit == unit]
            tail = sub[sub.t_days > t_adm + SYNTHEA_HOSPITAL_WINDOW_DAYS]
            n_pre = int((sub.t_days <= t_adm + 0.5).sum())
            if len(tail) >= 30 and n_pre >= 50:
                span = float(tail.t_days.max()
                             - (t_adm + SYNTHEA_HOSPITAL_WINDOW_DAYS))
                scored.append((span, pat))
        if not scored:
            return best(mask)
        return max(scored)[1]

    picks = {
        "survivor": best_with_tail(an.covid_admission.notna()
                                   & an.death.isna()),
        "deceased": best(an.covid_admission.notna()
                         & an.icu_admission.notna() & an.death.notna()),
    }
    # CinC property: non-septic records are trimmed to ~2 days by the
    # challenge, so the survivor's ICU stay is short by construction.
    stays = {
        "survivor": find_stay(sepsis=0, cr_lo=0.70, cr_hi=0.95,
                              min_span_days=1.5, end_cold_below=0.85),
        "deceased": find_stay(sepsis=1, cr_lo=1.02, cr_hi=1.15,
                              min_span_days=4.0),
    }

    index = {}
    for kind in ("deceased", "survivor"):
        j = build_journey(kind, ev, an, picks[kind], stays[kind], t0map)
        g = j["gates"].as_dict()
        print(f"[{kind}] synthea:{j['patient'][:8]}…  icu={j['stay']} "
              f"(span {j['icu_span']:.1f} d)  adm@{j['t_adm']:.1f} d")
        for k, v in g.items():
            lead = (None if v is None
                    else round(v - j['t_adm'], 2))
            print(f"    {k}: t={None if v is None else round(v, 2)} "
                  f"(vs admission {lead})")
        index[kind] = dict(patient=j["patient"], stay=j["stay"],
                           t_adm=round(j["t_adm"], 3),
                           icu_span=round(j["icu_span"], 3),
                           gates={k: (None if v is None else round(v, 3))
                                  for k, v in g.items()})
        j["traj"].to_parquet(HERE / f"journey_{kind}.parquet")

    (HERE / "stitch_index.json").write_text(json.dumps(index, indent=2))
    print("wrote stitch_index.json + journey_*.parquet")


if __name__ == "__main__":
    main()

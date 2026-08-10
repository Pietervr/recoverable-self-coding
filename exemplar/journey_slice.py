#!/usr/bin/env python3
"""Vertical slice of the exemplar: two real journeys through the filter.

Selects two Synthea COVID-inpatient units — one who died during the episode
(with an ICU admission) and one who survived — runs the Gamma-Poisson filter
on each, and renders margin + capacity-ratio trajectories with the journey
anchors (admission, ICU, death) marked. This is the seed of the full
stitched-journey figure (DESIGN.md stage 8).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from estimate import extract_unit, filter_trajectory, static_estimate
from schema import load_synthea_events, synthea_anchors

HERE = Path(__file__).resolve().parent
BLUE, RED, GREY = "#1F4E79", "#C00000", "0.35"


def pick_units(ev: pd.DataFrame, an: pd.DataFrame) -> dict[str, str]:
    counts = ev.groupby("unit").size()

    def best(mask: pd.Series) -> str:
        cands = ("synthea:" + an[mask].patient)
        cands = [c for c in cands if counts.get(c, 0) > 0]
        return max(cands, key=lambda c: counts[c])

    died = best(an.covid_admission.notna() & an.icu_admission.notna()
                & an.death.notna())
    lived = best(an.covid_admission.notna() & an.death.isna())
    return {"died": died, "survived": lived}


def unit_clock_offsets(ev_unit: pd.DataFrame, anchors_row: pd.Series,
                       data_dir: Path) -> dict[str, float]:
    """Anchor timestamps -> days on this unit's clock (t=0 at first obs)."""
    obs = pd.read_csv(data_dir / "observations.csv",
                      usecols=["DATE", "PATIENT"], low_memory=False)
    pid = ev_unit["unit"].iloc[0].split(":", 1)[1]
    t0 = pd.to_datetime(obs[obs.PATIENT == pid].DATE, utc=True,
                        errors="coerce").min()
    out = {}
    for key in ("covid_admission", "icu_admission", "death"):
        v = anchors_row[key]
        if pd.notna(v):
            out[key] = (v - t0).total_seconds() / 86400.0
    return out


def main() -> None:
    ev = load_synthea_events()
    an = synthea_anchors()
    picks = pick_units(ev, an)

    fig, axes = plt.subplots(2, 1, figsize=(8.6, 5.6), sharex=False)
    labels = {"died": ("deceased trajectory", RED),
              "survived": ("survivor trajectory", BLUE)}

    for ax, (kind, unit) in zip(axes, picks.items()):
        sub = ev[ev.unit == unit]
        u = extract_unit(sub)
        row = an[an.patient == unit.split(":", 1)[1]].iloc[0]
        anchors = unit_clock_offsets(sub, row,
                                     HERE / "data" / "10k_synthea_covid19_csv")

        # daily grid over the last 120 days of record (the episode window)
        lo = max(u.t_first, u.t_last - 120.0)
        grid = np.arange(lo, u.t_last + 0.5, 1.0)
        traj = filter_trajectory(u, grid, half_life_days=14.0)

        name, color = labels[kind]
        ax.fill_between(traj.t, traj.M_lo, traj.M_hi, color=color, alpha=0.18,
                        label="margin posterior (10-90%)")
        ax.plot(traj.t, traj.M_med, color=color, lw=1.8,
                label=r"$\mathcal{M}(t)$ median")
        ax.axhline(0.0, color="k", lw=1.0, ls=":")
        for key, style in (("covid_admission", "--"), ("icu_admission", "-."),
                           ("death", "-")):
            if key in anchors and lo <= anchors[key] <= u.t_last + 1:
                ax.axvline(anchors[key], color=GREY, lw=1.2, ls=style)
                ax.text(anchors[key], ax.get_ylim()[1],
                        key.replace("covid_", "").replace("_", " "),
                        rotation=90, va="top", ha="right", fontsize=7.5,
                        color=GREY)
        st = static_estimate(u)
        ax.set_title(f"({'ab'[list(picks).index(kind)]}) {name} — "
                     f"whole-record static CR = {st['CR']:.2f}",
                     fontsize=9.5, loc="left")
        ax.set_ylabel(r"$\mathcal{M}$  [events/day]")
        ax.legend(fontsize=8, loc="lower left")
        ax.grid(alpha=0.25)
    axes[-1].set_xlabel("days on unit clock (episode window)")

    fig.tight_layout()
    out = HERE / "journey_slice.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    for kind, unit in picks.items():
        print(kind, unit)


if __name__ == "__main__":
    main()

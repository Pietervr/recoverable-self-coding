#!/usr/bin/env python3
"""Stage 7 of the RSC exemplar: the personalization pair, from real data.

Two real CinC-2019 stays under the SAME load (arrival rate in the cohort's
middle quintile, the band of the foundational paper's Figure 2c) drawn from
opposite capacity quartiles — a thin-margin and a high-reserve unit. The
paper's Marli/Nduku contrast, selected from data rather than invented:
identical disturbance rate, different restoration rate, and therefore
opposite sides of the feasibility boundary.

Selection is deterministic: first stays in sorted set-A order whose static
metrics fall in the band with C in the bottom / top quartile ranges of the
committed cinc2019_personal_band.csv aggregate, span >= 2.5 d.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from estimate import extract_unit, filter_trajectory
from stitch import CINC_DIR, cinc_events

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "foundational"))
from cinc2019_cself import patient_metrics  # noqa: E402

HERE = Path(__file__).resolve().parent
YEAR = 365.25
BAND_R_DAY = (11.03, 13.26)     # middle-R quintile, per committed aggregate
Q1_C_MAX_DAY = 11.5             # bottom capacity quartile (median 11.08)
Q4_C_MIN_DAY = 17.5             # top capacity quartile (median 18.67)
MIN_SPAN = 2.5
BLUE, RED = "#1F4E79", "#C00000"


def find_pair() -> dict[str, Path]:
    picks: dict[str, Path] = {}
    files = sorted((CINC_DIR / "training_setA").glob("p*.psv"))
    for f in files:
        if len(picks) == 2:
            break
        m = patient_metrics(f)
        if m is None or m["span_days"] < MIN_SPAN:
            continue
        r_day, c_day = m["R_self"] / YEAR, m["C_self"] / YEAR
        if not (BAND_R_DAY[0] <= r_day <= BAND_R_DAY[1]):
            continue
        if "thin" not in picks and c_day <= Q1_C_MAX_DAY:
            picks["thin"] = f
        elif "reserve" not in picks and c_day >= Q4_C_MIN_DAY:
            picks["reserve"] = f
    if len(picks) < 2:
        raise RuntimeError(f"pair incomplete: {list(picks)}")
    return picks


def main() -> None:
    picks = find_pair()
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    styles = {
        "thin": (RED, "thin margin (bottom capacity quartile)"),
        "reserve": (BLUE, "high reserve (top capacity quartile)"),
    }
    info = {}
    for kind, psv in picks.items():
        ev = cinc_events(psv)
        u = extract_unit(ev)
        m = patient_metrics(psv)
        grid = np.arange(u.t_first + 0.5, u.t_last + 1 / 48, 1.0 / 24.0)
        traj = filter_trajectory(u, grid, half_life_days=1.0)
        color, label = styles[kind]
        ax.fill_between(traj.t, traj.CR_lo, traj.CR_hi, color=color,
                        alpha=0.15)
        ax.plot(traj.t, traj.CR_med, color=color, lw=1.7,
                label=f"{label}: $R$={m['R_self']/YEAR:.1f}, "
                      f"$C$={m['C_self']/YEAR:.1f}/day, "
                      f"CR={m['CR']:.2f}")
        info[kind] = dict(stay=psv.name,
                          R_day=round(m["R_self"] / YEAR, 2),
                          C_day=round(m["C_self"] / YEAR, 2),
                          CR=round(m["CR"], 3),
                          span_days=round(m["span_days"], 2))
    ax.axhline(1.0, color="k", lw=1.0, ls=":")
    ax.text(0.35, 1.04, "$\\Gamma$", fontsize=9, color="0.25")
    ax.set_xlabel("ICU time  [days]")
    ax.set_ylabel("$\\mathrm{CR}$ posterior")
    ax.set_ylim(0, 2.2)
    ax.set_title("Same load, different decoders: matched arrival rate, "
                 "opposite capacity quartiles", fontsize=9.5, loc="left")
    ax.legend(fontsize=7.8, loc="upper right", frameon=False)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    out = HERE / "phenotypes_figure.pdf"
    fig.savefig(out, bbox_inches="tight")
    (HERE / "phenotypes_index.json").write_text(json.dumps(info, indent=2))
    print(f"wrote {out}")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()

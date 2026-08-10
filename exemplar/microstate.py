#!/usr/bin/env python3
"""Stage 2 of the RSC exemplar: the microstate -> macrostate map, on data.

The paper defines a microstate as the fine-grained internal configuration
and the macrostate as its coarse-graining to rate--capacity coordinates.
On monitored physiology this is concrete and directly renderable:

    microstate omega(t): the panel state vector — for each variable,
        in-band / out-of-band / not yet observed, under the estimator's
        carry-forward convention (a variable stays "out" from its band-exit
        onset until the next in-range reading)
    backlog N(t): the number of variables simultaneously out of band —
        the column sum of the microstate raster, the directly countable
        uncertified-commitment occupancy
    macrostate Sigma(t) = (R_self, C_self, M): the filtered rate--capacity
        coordinates over the same events

The figure aligns all three on one clock for one real ICU stay: the raster
(top), the backlog (middle), and the filtered margin/CR (bottom) — the same
data at three levels of description.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd

from estimate import extract_unit, filter_trajectory
from stitch import cinc_events, CINC_DIR

HERE = Path(__file__).resolve().parent
GRID_STEP_DAYS = 1.0 / 24.0     # hourly, matching the charting cadence

UNOBS, INBAND, OUT = 0, 1, 2
CMAP = ListedColormap(["#FFFFFF", "#D7E3EE", "#C00000"])


def state_raster(events: pd.DataFrame,
                 grid: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Panel-variable state at each grid time, carry-forward convention."""
    variables = sorted(events["var"].unique())
    raster = np.full((len(variables), len(grid)), UNOBS, dtype=int)
    for i, var in enumerate(variables):
        g = events[events["var"] == var].sort_values("t_days")
        t = g["t_days"].to_numpy(float)
        v = g["value"].to_numpy(float)
        lo, hi = float(g["lo"].iloc[0]), float(g["hi"].iloc[0])
        state = (v >= lo) & (v <= hi)
        idx = np.searchsorted(t, grid, side="right") - 1
        seen = idx >= 0
        raster[i, seen] = np.where(state[idx[seen]], INBAND, OUT)
    return raster, variables


def main() -> None:
    idx = json.loads((HERE / "stitch_index.json").read_text())
    stay = CINC_DIR / "training_setA" / idx["deceased"]["stay"]
    ev = cinc_events(stay)
    u = extract_unit(ev)

    grid = np.arange(u.t_first, u.t_last + GRID_STEP_DAYS / 2,
                     GRID_STEP_DAYS)
    raster, variables = state_raster(ev, grid)
    backlog = (raster == OUT).sum(axis=0)
    traj = filter_trajectory(u, grid, half_life_days=0.5)

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(8.8, 6.8), sharex=True,
        gridspec_kw=dict(height_ratios=[3.2, 1.0, 1.4], hspace=0.38))

    # (a) microstate raster
    dt = GRID_STEP_DAYS
    edges = np.concatenate([grid - dt / 2, [grid[-1] + dt / 2]])
    ax1.pcolormesh(edges, np.arange(len(variables) + 1), raster, cmap=CMAP,
                   vmin=0, vmax=2, rasterized=True)
    ax1.set_yticks(np.arange(len(variables)) + 0.5)
    ax1.set_yticklabels(variables, fontsize=5.6)
    ax1.set_ylim(0, len(variables))
    ax1.set_title(
        "(a) microstate $\\omega(t)$: panel state vector "
        "(white = not yet observed, blue = in band, red = out of band)",
        fontsize=9, loc="left")

    # (b) backlog occupancy — the column sum of (a)
    ax2.fill_between(grid, backlog, step="mid", color="#C00000", alpha=0.35)
    ax2.step(grid, backlog, where="mid", color="#C00000", lw=1.2)
    ax2.set_ylabel("$N(t)$", fontsize=8.5)
    ax2.set_title("(b) backlog occupancy: variables simultaneously out of "
                  "band (the column sum of (a))", fontsize=9, loc="left")
    ax2.grid(alpha=0.25)

    # (c) macrostate — filtered CR with boundary (6 h burn-in omitted:
    # the restarted filter's capacity posterior is prior-dominated until
    # the first restorations arrive)
    tr = traj[traj.t >= u.t_first + 0.25]
    ax3.fill_between(tr.t, tr.CR_lo, tr.CR_hi, color="#1F4E79",
                     alpha=0.18)
    ax3.plot(tr.t, tr.CR_med, color="#1F4E79", lw=1.6)
    ax3.axhline(1.0, color="k", lw=1.0, ls=":")
    ax3.set_ylim(0, 2.5)
    ax3.text(float(grid[3]), 1.06, "$\\Gamma$", fontsize=8, color="0.25")
    ax3.set_ylabel("$\\mathrm{CR}$", fontsize=8.5)
    ax3.set_xlabel("ICU time  [days]")
    ax3.set_title(
        "(c) macrostate $\\Sigma(t)$: the same events coarse-grained to "
        "rate--capacity coordinates (filtered $\\mathrm{CR}$, 10--90% band)",
        fontsize=9, loc="left")
    ax3.grid(alpha=0.25)

    fig.align_ylabels()
    out = HERE / "microstate_figure.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}  (stay {stay.name}, {len(variables)} variables, "
          f"{len(grid)} hourly states, backlog max {backlog.max()})")


if __name__ == "__main__":
    main()

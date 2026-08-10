#!/usr/bin/env python3
"""Stage 8 of the RSC exemplar: the stitched-journey figure.

Two journeys (deceased, survivor), each rendered as broken-axis segments
(ambulatory pre | real ICU | recovery) with the filtered CR(t) posterior,
the feasibility boundary, the three gates, and segment provenance. CR is
dimensionless, so one y-axis serves segments whose absolute event rates
differ by an order of magnitude — the point of the gauge.

Reads journey_*.parquet + stitch_index.json (from stitch.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
BLUE, RED, GREEN, ORANGE = "#1F4E79", "#C00000", "#1E7B1E", "#C77400"
SEG_BG = {"pre": "#FFF9E8", "icu": "#EEF1F5", "recovery": "#FFF9E8"}
SEG_LABEL = {"pre": "ambulatory + deterioration\n(Synthea, synthetic)",
             "icu": "ICU\n(CinC-2019, real)",
             "recovery": "recovery\n(Synthea, synthetic)"}
PRE_SHOW_DAYS = 30.0
REC_SHOW_DAYS = 45.0
GATES = [("g1_escalate", "G1 escalate", ORANGE, "^"),
         ("g2_admit", "G2 admit", RED, "o"),
         ("g3_discharge", "G3 discharge", GREEN, "D")]


def render_journey(fig, gs_row, kind: str, idx: dict, color: str,
                   title: str) -> None:
    traj = (pd.read_parquet(HERE / f"journey_{kind}.parquet")
            .sort_values("t_journey"))
    segs = [s for s in ("pre", "icu", "recovery")
            if (traj.segment == s).any()]
    t_adm = idx["t_adm"]

    widths, views = [], {}
    for s in segs:
        st = traj[traj.segment == s]
        lo, hi = st.t_journey.min(), st.t_journey.max()
        if s == "pre":
            lo = max(lo, t_adm - PRE_SHOW_DAYS)
        if s == "recovery":
            hi = min(hi, st.t_journey.min() + REC_SHOW_DAYS)
        views[s] = (lo, hi)
        widths.append(max(hi - lo, 1.0) ** 0.5)

    sub = gs_row.subgridspec(1, len(segs), wspace=0.05,
                             width_ratios=widths)
    axes = [fig.add_subplot(sub[0, i]) for i in range(len(segs))]

    for ax, s in zip(axes, segs):
        st = traj[traj.segment == s]
        lo, hi = views[s]
        st = st[(st.t_journey >= lo) & (st.t_journey <= hi)]
        narrow = (hi - lo) < 5.0
        ax.set_facecolor(SEG_BG[s])
        ax.fill_between(st.t_journey, st.CR_lo, st.CR_hi, color=color,
                        alpha=0.18)
        ax.plot(st.t_journey, st.CR_med, color=color, lw=1.7)
        ax.axhline(1.0, color="k", lw=1.0, ls=":")
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, 2.6)
        if narrow and s == "icu":
            ax.text(0.5, 0.03, "ICU (real)", transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=6.5, color="0.35")
        else:
            ax.text(0.5, 0.985, SEG_LABEL[s], transform=ax.transAxes,
                    ha="center", va="top", fontsize=7.2, color="0.35")
        for key, label, gcol, marker in GATES:
            gt = idx["gates"].get(key)
            if gt is not None and lo <= gt <= hi:
                ax.axvline(gt, color=gcol, lw=1.3, ls="--", alpha=0.85)
                ax.plot([gt], [2.38], marker=marker, color=gcol, ms=6,
                        clip_on=False)
        if s == "icu":
            ax.axvline(t_adm, color="0.4", lw=1.0)
            if kind == "deceased":
                t_end = t_adm + idx["icu_span"]
                ax.axvline(t_end, color="k", lw=1.4)
                ax.text(t_end, 1.55, " death", rotation=90, fontsize=7.5,
                        va="bottom", ha="right", color="k")
            if not narrow:
                pre_c = traj[traj.segment == "pre"].C_mean.median()
                icu_c = traj[traj.segment == "icu"].C_mean.median()
                ax.text(0.5, 0.04, f"capacity injection:\n"
                        f"$C$ {pre_c:.1f} $\\to$ {icu_c:.0f} /day",
                        transform=ax.transAxes, ha="center", va="bottom",
                        fontsize=7.2, color="0.25")
        if ax is not axes[0]:
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=7.5)
        ax.grid(alpha=0.2)

    axes[0].set_ylabel(r"$\mathrm{CR}$ posterior")
    axes[0].text(0.012, 1.045, "$\\Gamma$ (CR = 1)",
                 transform=axes[0].get_yaxis_transform(), fontsize=7.5,
                 color="0.25", ha="left", va="bottom")
    axes[len(segs) // 2].set_xlabel("journey time  [days on unit clock]",
                                    fontsize=8.5)
    axes[0].set_title(title, fontsize=9.5, loc="left", pad=10)


def main() -> None:
    idx = json.loads((HERE / "stitch_index.json").read_text())
    fig = plt.figure(figsize=(9.0, 5.8))
    gs = fig.add_gridspec(2, 1, hspace=0.42)

    render_journey(
        fig, gs[0], "deceased", idx["deceased"], RED,
        "(a) deceased journey — G2 admits, G3 never fires; margin never "
        "recovers")
    render_journey(
        fig, gs[1], "survivor", idx["survivor"], BLUE,
        "(b) survivor journey — G2 admits, G3 discharges "
        f"{idx['survivor']['gates']['g3_discharge'] - idx['survivor']['t_adm']:.1f}"
        " d after admission")

    handles = [plt.Line2D([], [], color=c, ls="--", marker=m, ms=6,
                          label=lbl)
               for _, lbl, c, m in GATES]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, -0.02))

    out = HERE / "journey_figure.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

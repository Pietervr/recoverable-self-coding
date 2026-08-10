#!/usr/bin/env python3
"""Capacity growth and the growth-stall test on GitHub repo histories.

Input: github_cself_history.csv (repo, year, age, opened, closed).
Tests (Sections 2.6/2.7 of the foundational paper):

  GROWTH: capacity is built. Per repo, annual closing capacity C_y is
  normalized to the repo's own early capacity (median of ages 0-1); the
  cohort median of the normalized curve by age shows whether capacity grows
  as projects mature.

  STALL: sustained overload stalls growth. Per repo, the capacity growth
  rate = least-squares slope of log C_y against age (years with closed >=
  12), against the repo's share of infeasible years (CR_y >= 1 among years
  with opened >= 24). Prediction: negative association.

Outputs: github_history_summary.json + github_history_growth.csv
(aggregates; figure by make_annealing_figure.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MIN_CLOSED = 12
MIN_OPENED = 24
MIN_YEARS = 5


def rank_corr(x: np.ndarray, y: np.ndarray) -> float:
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    return float((rx * ry).mean())


def main() -> None:
    m = pd.read_csv(HERE / "github_cself_history.csv")
    m = m[m.closed > 0].copy()
    m["CR_y"] = m.opened / m.closed

    growth_rows, repo_rows = [], []
    for repo, g in m.groupby("repo"):
        g = g.sort_values("age")
        base = g[g.age <= 1].closed.median()
        if not np.isfinite(base) or base < MIN_CLOSED:
            base = g[g.closed >= MIN_CLOSED].closed.iloc[:2].median() \
                if (g.closed >= MIN_CLOSED).any() else np.nan
        if not np.isfinite(base):
            continue
        for r in g.itertuples():
            growth_rows.append(dict(repo=repo, age=r.age,
                                    C_norm=r.closed / base,
                                    CR_y=r.CR_y))
        fit = g[g.closed >= MIN_CLOSED]
        loaded = g[g.opened >= MIN_OPENED]
        if len(fit) >= MIN_YEARS and len(loaded) >= MIN_YEARS:
            slope = np.polyfit(fit.age, np.log(fit.closed), 1)[0]
            infeas = float((loaded.CR_y >= 1).mean())
            repo_rows.append(dict(repo=repo, n_years=len(fit),
                                  growth_slope=round(float(slope), 4),
                                  infeasible_share=round(infeas, 4)))

    gr = pd.DataFrame(growth_rows)
    rep = pd.DataFrame(repo_rows)
    gr.to_csv(HERE / "github_history_growth.csv", index=False)
    rep.to_csv(HERE / "github_history_repos.csv", index=False)

    curve = gr.groupby("age").C_norm.median()
    lo_group = rep[rep.infeasible_share <= rep.infeasible_share.median()]
    hi_group = rep[rep.infeasible_share > rep.infeasible_share.median()]
    summary = dict(
        n_repos=int(m.repo.nunique()), n_repo_years=len(m),
        n_repos_fit=len(rep),
        C_norm_median_age5=round(float(curve.get(5, np.nan)), 2),
        C_norm_median_age10=round(float(curve.get(10, np.nan)), 2),
        growth_slope_median=round(float(rep.growth_slope.median()), 4),
        rank_corr_slope_vs_infeasible=round(
            rank_corr(rep.growth_slope.to_numpy(),
                      rep.infeasible_share.to_numpy()), 3),
        growth_slope_median_low_infeas=round(
            float(lo_group.growth_slope.median()), 4),
        growth_slope_median_high_infeas=round(
            float(hi_group.growth_slope.median()), 4),
        infeasible_share_split=round(float(rep.infeasible_share.median()), 3),
    )
    (HERE / "github_history_summary.json").write_text(
        json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(rep.sort_values("infeasible_share").to_string(index=False))


if __name__ == "__main__":
    main()

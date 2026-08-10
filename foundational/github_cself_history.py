#!/usr/bin/env python3
"""Longitudinal R/C histories for GitHub repositories: the capacity-growth
and growth-stall test.

Section 2.6/2.7 of the foundational paper claim that capacity is grown
(exploration -> consolidation cycles) and that sustained overload stalls
that growth. Per repo, per calendar year since creation:

    opened_y = issues opened in year y      closed_y = issues closed in y
    C_y = closed_y (capacity, /yr)          CR_y = opened_y / closed_y

Predictions tested downstream:
  (a) growth: median C_y rises with repository age;
  (b) stall:  capacity growth is flatter for repos with a larger share of
      infeasible years (CR_y >= 1) — overload consumes the resources that
      would otherwise grow capacity.

Sample: from the committed github_cself.csv snapshot, the 25 lowest- and 25
highest-CR repos (balanced feasible/infeasible), full history. Aggregate
counts only, via the public search API (gh CLI auth; ~27 req/min).
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PAUSE = 2.2
N_EACH = 25


def gh_json(endpoint: str) -> dict:
    for attempt in range(4):
        r = subprocess.run(["gh", "api", endpoint], capture_output=True,
                           text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
        wait = 30.0 * (attempt + 1)
        print(f"[gh] retry in {wait:.0f}s: {r.stderr.strip()[:100]}",
              flush=True)
        time.sleep(wait)
    raise RuntimeError(f"gh api failed: {endpoint}")


def search_count(q: str) -> int:
    out = gh_json(f"search/issues?q={q}&per_page=1")
    time.sleep(PAUSE)
    return int(out["total_count"])


def main() -> None:
    snap = pd.read_csv(HERE / "github_cself.csv").sort_values("CR")
    repos = pd.concat([snap.head(N_EACH), snap.tail(N_EACH)])
    this_year = dt.date.today().year
    print(f"[ghh] {len(repos)} repos (25 lowest / 25 highest CR), "
          f"histories to {this_year - 1}", flush=True)

    rows = []
    for i, rec in enumerate(repos.itertuples()):
        full = rec.repo
        try:
            meta = gh_json(f"repos/{full}")
            time.sleep(PAUSE)
            created = int(meta["created_at"][:4])
        except RuntimeError as e:
            print(f"[ghh] skip {full}: {e}", flush=True)
            continue
        for y in range(created, this_year):        # full calendar years only
            span = f"{y}-01-01..{y}-12-31"
            try:
                opened = search_count(f"repo:{full}+type:issue+created:{span}")
                closed = search_count(f"repo:{full}+type:issue+closed:{span}")
            except RuntimeError as e:
                print(f"[ghh] skip {full} {y}: {e}", flush=True)
                continue
            rows.append(dict(repo=full, year=y, age=y - created,
                             opened=opened, closed=closed,
                             snapshot_CR=round(rec.CR, 4)))
        print(f"[ghh] {i + 1}/{len(repos)} {full} "
              f"({created}-{this_year - 1})", flush=True)
        pd.DataFrame(rows).to_csv(HERE / "github_cself_history.csv",
                                  index=False)

    m = pd.DataFrame(rows)
    m.to_csv(HERE / "github_cself_history.csv", index=False)
    print(f"[ghh] done: {len(m)} repo-years across {m.repo.nunique()} repos",
          flush=True)


if __name__ == "__main__":
    main()

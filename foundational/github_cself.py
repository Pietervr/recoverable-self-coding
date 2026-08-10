#!/usr/bin/env python3
"""R_self / C_self / CR / backlog for popular GitHub repositories.

The operational-systems existence proof for the foundational paper: a
repository is a self-decoder whose commitments are issues. Per repo, over a
365-day window ending today:

    R_self  = issues opened / year      (arrival rate)
    C_self  = issues closed / year      (service rate; completions in window)
    CR      = R_self / C_self
    backlog = currently open issues     (the uncertified-commitment count,
                                         observed directly - no proxy)
    drain_months = backlog / (C_self/12)  (months of work at current capacity)

Sample: top-starred repositories from the GitHub search API (public
metadata only; PRs excluded via type:issue throughout). Uses the gh CLI for
auth; respects the 30 req/min search limit. Aggregate CSV committed; no
scraping, no content.

Usage: python3 github_cself.py [--repos 180] [--window-days 365]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAUSE = 2.2          # seconds between search calls (~27/min < 30/min limit)


def gh_json(endpoint: str) -> dict:
    for attempt in range(4):
        r = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
        wait = 30.0 * (attempt + 1)
        print(f"[gh] retry in {wait:.0f}s: {r.stderr.strip()[:100]}", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"gh api failed: {endpoint}")


def search_count(q: str) -> int:
    out = gh_json(f"search/issues?q={q}&per_page=1")
    time.sleep(PAUSE)
    return int(out["total_count"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", type=int, default=180)
    ap.add_argument("--window-days", type=int, default=365)
    a = ap.parse_args()

    since = (dt.date.today() - dt.timedelta(days=a.window_days)).isoformat()
    years = a.window_days / 365.25

    repos: list[str] = []
    for page in range(1, (a.repos // 100) + 2):
        out = gh_json(
            f"search/repositories?q=stars:%3E15000&sort=stars&order=desc"
            f"&per_page=100&page={page}")
        repos += [it["full_name"] for it in out["items"]]
        time.sleep(PAUSE)
        if len(repos) >= a.repos:
            break
    repos = repos[: a.repos]
    print(f"[gh] sampling {len(repos)} repos, window since {since}", flush=True)

    rows = []
    for i, full in enumerate(repos):
        try:
            opened = search_count(f"repo:{full}+type:issue+created:%3E{since}")
            closed = search_count(f"repo:{full}+type:issue+closed:%3E{since}")
            opennow = search_count(f"repo:{full}+type:issue+state:open")
        except RuntimeError as e:
            print(f"[gh] skip {full}: {e}", flush=True)
            continue
        if opened < 24 or closed < 12:     # too quiet to place
            continue
        r_self = opened / years
        c_self = closed / years
        rows.append(dict(
            repo=full, opened_yr=round(r_self, 1), closed_yr=round(c_self, 1),
            CR=round(r_self / c_self, 4), backlog=opennow,
            drain_months=round(opennow / (c_self / 12.0), 2)))
        if (i + 1) % 20 == 0:
            print(f"[gh] {i+1}/{len(repos)} ({len(rows)} placed)", flush=True)

    import pandas as pd
    m = pd.DataFrame(rows)
    m.to_csv(HERE / "github_cself.csv", index=False)
    feasible = int((m["CR"] < 1).sum())
    summary = dict(
        n=len(m), window_days=a.window_days, since=since,
        feasible_k=feasible, feasible_frac=round(feasible / len(m), 4),
        CR_median=round(float(m["CR"].median()), 4),
        drain_months_median=round(float(m["drain_months"].median()), 2),
        drain_months_median_CR_lt_1=round(
            float(m.loc[m.CR < 1, "drain_months"].median()), 2),
        drain_months_median_CR_ge_1=round(
            float(m.loc[m.CR >= 1, "drain_months"].median()), 2)
        if (m.CR >= 1).any() else None,
    )
    (HERE / "github_cself_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

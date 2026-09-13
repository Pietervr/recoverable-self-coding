#!/usr/bin/env python3
"""dashboard.py — build the run monitor page for a simulation run from the shard files spotcheck.py has pulled.

  ./.venv/bin/python dashboard.py --run d4v12b --out /path/run_d4v12b.html \
      [--status-file <launch_t1 --status output>] [--starts-file <"sNNN count" lines>]

Reads sim_results/<run>/ (the per-shard CSVs and their .progress.json, the gain files), the fleet listing
and the job-start counts the monitor writes, appends one record to sim_results/<run>/dashboard_history.json,
and writes dashboard_template.html with the data embedded. Nothing is downloaded here; the statistics are
the ones spotcheck.py prints (simulate.summarize), the power stages are HELD under the same gate.
"""
from __future__ import annotations

import argparse
import calendar
import glob
import json
import os
import re
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# stage key, label, expected rows for the whole run, cost weight of one row relative to a single-layer replicate
STAGES = [
    ("calibration_D4", "Calibration · graded nulls", 12000, 1),
    ("power_D4", "Power · mixture alternatives", 12000, 1),
    ("recovery_D4", "Recovery · mixture grid", 7200, 1),
    ("calibration_D4_5layers", "Five-layer pilot · nulls", 800, 5),
    ("power_D4_5layers", "Five-layer pilot · alternatives", 800, 5),
]
N_SHARDS = 160
RULES = dict(fpr_max=0.064, coverage_min=0.90, power_min=0.8)
JOB_RE = re.compile(r"-s(\d{3})(?:-(\d{3}))?of(\d{3})-")          # job names: ...-s020of160-..., ...-s042-056of160-...
FILE_RE = re.compile(r"\.shard(\d{3})(?:-(\d{3}))?of(\d{3})\.csv")   # shard files: <stage>.shard020of160.csv


def job_kind(shard0: int, instance: str, spot_shards: range) -> str:
    if shard0 in spot_shards:
        return "spot"
    return "large" if "48xlarge" in instance else "small"


def read_status(path: str | None, run: str) -> list[dict]:
    jobs = []
    if not path or not os.path.exists(path):
        return jobs
    for line in open(path):
        parts = line.split()
        if len(parts) < 5 or run not in parts[0]:
            continue
        m = JOB_RE.search(parts[0])
        if not m:
            continue
        s0 = int(m.group(1))
        s1 = int(m.group(2)) if m.group(2) else s0
        try:
            train_h = float(parts[4])
        except ValueError:
            train_h = None
        jobs.append(dict(name=parts[0], status=parts[1], secondary=parts[2], instance=parts[3],
                         train_h=train_h, shard0=s0, shard1=s1))
    # a relaunched shard has two jobs with the same range: keep the newest (the launcher suffixes the name
    # with a timestamp), so a superseded Failed/Stopped job does not count against the fleet
    newest = {}
    for j in jobs:
        key = (j["shard0"], j["shard1"])
        stamp = j["name"].rsplit("-", 1)[-1]
        if key not in newest or stamp > newest[key]["name"].rsplit("-", 1)[-1]:
            newest[key] = j
    return sorted(newest.values(), key=lambda j: j["shard0"])


def read_starts(path: str | None) -> dict[int, int]:
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path):
        m = re.match(r"s(\d{3})(?:-(\d{3}))?\s+(\d+)", line.strip())
        if m:
            out[int(m.group(1))] = int(m.group(3))
    return out


def shard_file_stem(stage: str, s0: int, s1: int) -> str:
    return f"{stage}.shard{s0:03d}of{N_SHARDS:03d}" if s0 == s1 else f"{stage}.shard{s0:03d}-{s1:03d}of{N_SHARDS:03d}"


def gain_verdicts(out_dir: str) -> dict:
    import simulate as S
    from spotcheck import gain_file_for
    v = {}
    for D in (4, 8):
        p = gain_file_for(out_dir, D)
        if not p:
            v[D] = dict(present=False, ok=False, file=None, problems=[])
            continue
        with open(p) as fh:
            cal = json.load(fh)
        entries = cal["entries"] if isinstance(cal, dict) else cal
        problems = S.validate_gain_entries(entries)
        v[D] = dict(present=True, ok=not problems, file=os.path.basename(p), problems=problems)
    return v


def stage_summary(out_dir: str, stage: str, held: bool) -> tuple[dict | None, list[dict], list[dict]]:
    """Stage totals, the per-generator table rows, and the per-shard-file rows (with fit times)."""
    import simulate as S
    files = sorted(glob.glob(os.path.join(out_dir, f"{stage}.shard*of{N_SHARDS:03d}.csv")))
    if not files:
        return None, [], []
    frames, per_file = [], []
    for f in files:
        part = pd.read_csv(f)
        m = FILE_RE.search(os.path.basename(f))
        s0 = int(m.group(1)) if m else -1
        s1 = int(m.group(2)) if (m and m.group(2)) else s0
        part["_shard0"] = s0
        frames.append(part)
        prog = {}
        pj = f + ".progress.json"
        if os.path.exists(pj):
            with open(pj) as fh:
                prog = json.load(fh)
        per_file.append(dict(shard0=s0, shard1=s1, rows=len(part), done=prog.get("done", len(part)),
                             total=prog.get("total"), rate=prog.get("rate_per_hour"), eta_h=prog.get("eta_hours"),
                             updated=prog.get("updated"), fit_min=(part["fit_seconds"] / 60).round(1).tolist()))
    df = pd.concat(frames, ignore_index=True)
    n = len(df)
    st = dict(key=stage, rows=n, files=len(files), n_generators=int(df["generator"].nunique()),
              convergence=float(df["convergence"].mean()), inner_convergence=float(df["inner_convergence"].mean()) if "inner_convergence" in df else None,
              failures=float(df["failed"].mean()), held=held,
              rate=float(sum(p["rate"] or 0 for p in per_file)), eta_h=float(max((p["eta_h"] or 0) for p in per_file)))
    nulls = df[df["family"] == "G"]
    alts = df[df["family"] == "X"]
    if len(nulls):
        fpr = float((nulls["selection_decision"] == "mixture").mean())
        st.update(n_nulls=int(len(nulls)), fpr=fpr, fpr_se=float(np.sqrt(fpr * (1 - fpr) / len(nulls))))
    if len(alts):
        st.update(n_alts=int(len(alts)), mixture_rate=float((alts["selection_decision"] == "mixture").mean()))
    gens = []
    if not held:
        tmp = os.path.join(out_dir, f".{stage}.dashboard.csv")
        df.drop(columns=["_shard0"]).to_csv(tmp, index=False)
        summ = S.summarize(tmp)
        os.remove(tmp)
        for _, r in summ.iterrows():
            gens.append({k: (None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else v))
                         for k, v in r.items()})
            gens[-1]["stage"] = stage
    else:
        for (g, fam, grid), part in df.groupby(["generator", "family", "grid"], sort=False):
            gens.append(dict(stage=stage, generator=g, family=fam, grid=grid, n=int(len(part)), held=True,
                             convergence=float(part["convergence"].mean()), failure=float(part["failed"].mean()),
                             mean_fit_s=float(part["fit_seconds"].mean())))
    return st, gens, per_file


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="d4v12b")
    ap.add_argument("--out", required=True)
    ap.add_argument("--status-file", default=None)
    ap.add_argument("--starts-file", default=None)
    ap.add_argument("--launched", default="2026-09-12T00:38Z", help="launch time, UTC")
    ap.add_argument("--spot-shards", default="0-19")
    ap.add_argument("--code-hash", default="b29215469af9")
    ap.add_argument("--projected-hours", default="45–50")
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from aws_env import cache_dir          # the same per-bucket local mirror spotcheck pulls into (13 Sept 2026)
    out_dir = cache_dir(HERE, a.run)
    lo, hi = (int(x) for x in a.spot_shards.split("-"))
    spot = range(lo, hi + 1)
    now = time.gmtime()
    verdicts = gain_verdicts(out_dir)

    stages, generators, per_file_by_stage = [], [], {}
    for key, label, expected, weight in STAGES:
        D = 8 if "D8" in key else 4
        held = key.startswith("power") and not verdicts.get(D, {}).get("ok", False)
        st, gens, per_file = stage_summary(out_dir, key, held)
        if st is None:
            st = dict(key=key, rows=0, files=0, n_generators=0, held=held, rate=0.0, eta_h=0.0)
        st.update(label=label, expected=expected, weight=weight)
        stages.append(st)
        generators += gens
        per_file_by_stage[key] = {(p["shard0"], p["shard1"]): p for p in per_file}

    jobs = read_status(a.status_file, a.run)
    starts = read_starts(a.starts_file)
    job_rows = []
    for j in jobs:
        n_sh = j["shard1"] - j["shard0"] + 1
        work_done = work_total = 0.0
        stage_now, stage_done_rows, stage_total_rows = None, 0, 0
        per_stage = []
        for key, label, expected, weight in STAGES:
            per_shard = expected / N_SHARDS
            total_rows = per_shard * n_sh
            p = per_file_by_stage[key].get((j["shard0"], j["shard1"]))
            done = p["done"] if p else 0
            work_done += done * weight
            work_total += total_rows * weight
            per_stage.append(dict(stage=key, done=done, total=total_rows))
            if p:
                stage_now, stage_done_rows, stage_total_rows = key, done, (p["total"] or total_rows)
        job_rows.append(dict(name=j["name"], short=f"s{j['shard0']:03d}" + (f"–{j['shard1']:03d}" if n_sh > 1 else ""),
                             kind=job_kind(j["shard0"], j["instance"], spot), instance=j["instance"], status=j["status"],
                             secondary=j["secondary"], train_h=j["train_h"], shards=n_sh, starts=starts.get(j["shard0"], 1),
                             work_done=work_done, work_total=work_total, stage=stage_now,
                             stage_done=stage_done_rows, stage_total=stage_total_rows, per_stage=per_stage))
    fleet = {}
    for j in jobs:
        fleet[j["status"]] = fleet.get(j["status"], 0) + 1

    # fit-time histogram per instance kind, all stages, minutes
    edges = list(range(30, 245, 5))
    hist = {k: [0] * (len(edges) - 1) for k in ("spot", "small", "large")}
    for key, _, _, _ in STAGES:
        for (s0, s1), p in per_file_by_stage[key].items():
            kind = "spot" if s0 in spot else ("large" if s1 > s0 else "small")
            counts, _ = np.histogram(p["fit_min"], bins=edges)
            hist[kind] = [x + int(y) for x, y in zip(hist[kind], counts)]

    # history: one record per build when the rows changed
    hist_path = os.path.join(out_dir, "dashboard_history.json")
    history = []
    if os.path.exists(hist_path):
        with open(hist_path) as fh:
            history = json.load(fh)
    rows_now = {s["key"]: s["rows"] for s in stages}
    stamp = time.strftime("%Y-%m-%dT%H:%MZ", now)
    if not history or history[-1]["rows"] != rows_now:
        history.append(dict(t=stamp, rows=rows_now))
        with open(hist_path, "w") as fh:
            json.dump(history, fh, indent=1)

    launched = time.strptime(a.launched, "%Y-%m-%dT%H:%MZ")
    elapsed_h = (calendar.timegm(now) - calendar.timegm(launched)) / 3600
    data = dict(run=a.run, code_hash=a.code_hash, launched=a.launched, generated=stamp, elapsed_h=round(elapsed_h, 2),
                projected_hours=a.projected_hours, n_shards=N_SHARDS, rules=RULES, gain=verdicts,
                fleet=fleet, jobs=job_rows, stages=stages, generators=generators, history=history,
                fit_hist=dict(edges=edges, counts=hist),
                total_rows=sum(s["rows"] for s in stages), total_expected=sum(s["expected"] for s in stages))
    with open(os.path.join(HERE, "dashboard_template.html")) as fh:
        html = fh.read()
    html = html.replace("/*__DATA_JSON__*/null", json.dumps(data, default=float))
    with open(a.out, "w") as fh:
        fh.write(html)
    print(f"{a.out}: {data['total_rows']} rows, {len(job_rows)} jobs, {len(generators)} generator rows, history {len(history)}")


if __name__ == "__main__":
    main()

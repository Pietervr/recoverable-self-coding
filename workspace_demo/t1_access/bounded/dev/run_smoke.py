#!/usr/bin/env python3
"""bounded/dev/run_smoke.py — the Mac smoke run: one replicate (r = 0) of each of the 30 catalogue settings in the
DEVELOPMENT namespace (271100), each point in its own `python -m bounded.run_point` process with NPROC=1 set before
jax is imported, under a cumulative process-CPU budget of 6 h (21,600 s). Records per-setting CPU seconds in
bounded/dev/smoke.json (rewritten after every completed point) and the rows in bounded/dev/smoke_rows/.

    cd workspace_demo/t1_access
    .venv/bin/python bounded/dev/run_smoke.py --workers 3

Budget rule: a new point is launched only while (CPU spent by completed points) + (CPU still committed to running
points, at the largest per-point CPU seen so far, 900 s before the first completes) + (that same estimate for the new
point) stays within the budget. Points run in the stopping-rule order of S3 (the M3S alternatives and the hardest
graded settings first). The boundary setting G14 runs at the development placeholder lambda = 0.5 (not frozen).
This is the Mac cost basis for the Lengau benchmark, not a Lengau rate and not a calibration or validation result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

DEV = os.path.dirname(os.path.abspath(__file__))
BOUNDED = os.path.dirname(DEV)
T1 = os.path.dirname(BOUNDED)
ROWS = os.path.join(DEV, "smoke_rows")
OUT = os.path.join(DEV, "smoke.json")
PY = os.path.join(T1, ".venv", "bin", "python")
BUDGET = 6 * 3600.0
ORDER = ["A13", "A14", "G14", "G09", "G08", "G05", "G03", "G07", "G11", "G16", "G15", "G13",
         "A05", "A08", "A02", "A11", "A04", "A07", "A01", "A10", "A06", "A09", "A03", "A12",
         "G01", "G02", "G04", "G06", "G10", "G12"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--budget", type=float, default=BUDGET)
    a = ap.parse_args()
    os.makedirs(ROWS, exist_ok=True)
    env = dict(os.environ, NPROC="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               JAX_PLATFORMS="cpu", PYTHONDONTWRITEBYTECODE="1")
    with open(os.path.join(BOUNDED, "catalogue.json")) as fh:
        kinds = {s["id"]: s["kind"] for s in json.load(fh)["settings"]}
    assert sorted(ORDER) == sorted(kinds), "the smoke order must cover the catalogue exactly once"
    state = dict(about="R052 bounded-comparison Mac smoke run: development namespace 271100, replicate 0, one process per point, "
                       "NPROC=1; Mac cost basis only (not Lengau, not calibration, not validation)",
                 started=time.strftime("%Y-%m-%dT%H:%M:%S%z"), budget_cpu_seconds=a.budget, workers=a.workers,
                 driver_pid=os.getpid(), host=os.uname().nodename, machine=os.uname().machine,
                 boundary_lambda_placeholder=0.5, order=ORDER, settings={}, finished=None, stopped_by_budget=[])

    def save():
        done = [v for v in state["settings"].values() if v.get("status") == "done"]
        state["completed"] = len(done)
        state["cpu_seconds_completed"] = sum(v["process_cpu_seconds"] for v in done)
        tmp = OUT + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, OUT)

    queue = list(ORDER)
    running = {}
    spent, seen = 0.0, []
    save()
    while queue or running:
        while queue and len(running) < a.workers:
            worst = max(seen) if seen else 900.0
            if spent + worst * (len(running) + 1) > a.budget:
                state["stopped_by_budget"] = list(queue)
                queue = []
                break
            sid = queue.pop(0)
            row = os.path.join(ROWS, f"{sid}_r0.json")
            cmd = [PY, "-m", "bounded.run_point", "--setting", sid, "--replicate", "0", "--namespace", "development",
                   "--out", row] + (["--lam", "0.5"] if sid == "G14" else [])
            log = open(os.path.join(ROWS, f"{sid}_r0.log"), "w")
            p = subprocess.Popen(cmd, cwd=T1, env=env, stdout=log, stderr=subprocess.STDOUT)
            running[sid] = (p, row, log, time.monotonic(), os.getloadavg())
            state["settings"][sid] = dict(kind=kinds[sid], status="running", pid=p.pid, launched=time.strftime("%H:%M:%S"),
                                          loadavg_at_launch=list(os.getloadavg()))
            save()
        time.sleep(5)
        for sid in list(running):
            p, row, log, t0, la = running[sid]
            if p.poll() is None:
                continue
            log.close()
            del running[sid]
            rec = state["settings"][sid]
            rec.update(returncode=p.returncode, wall_seconds=time.monotonic() - t0)
            if p.returncode == 0 and os.path.exists(row):
                with open(row) as fh:
                    r = json.load(fh)
                with open(row, "rb") as fh:
                    rec["row_sha256"] = hashlib.sha256(fh.read()).hexdigest()
                tm = r["timing"]
                rec.update(status="done", process_cpu_seconds=tm["process_cpu_seconds_total"],
                           fit_cpu_seconds=tm["fit_cpu_seconds"], point_cpu_seconds=tm["point_cpu_seconds"],
                           overhead_cpu_seconds=tm["process_cpu_seconds_total"] - tm["fit_cpu_seconds"],
                           fit_cpu_by_member=tm["fit_cpu_by_member"], loadavg_at_end=tm["loadavg_at_end"],
                           bounded=r["point"]["bounded"], unbounded=r["point"]["unbounded"], unavailable=r["unavailable"],
                           unavailable_reason=r["unavailable_reason"], dataset_seed=r["dataset_seed"],
                           n_fits=r["fit_summary"]["n_fits"], n_converged=r["fit_summary"]["n_converged"],
                           n_recovery=r["fit_summary"]["n_recovery"], config_hash=r["config_hash"],
                           deterministic_sha256=r["deterministic_sha256"], row=os.path.relpath(row, T1))
                spent += rec["process_cpu_seconds"]
                seen.append(rec["process_cpu_seconds"])
            else:
                rec.update(status="failed")
            save()
    state["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    save()


if __name__ == "__main__":
    sys.exit(main())

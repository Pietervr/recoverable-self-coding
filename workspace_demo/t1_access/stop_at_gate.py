#!/usr/bin/env python3
"""stop_at_gate.py — stop every d4v12b job that has finished its calibration rows and entered the job-side gain
calibration, a stage known to fail the §10 gate (M3L at 0.01 nat; run d4v12b, 12 Sept 2026) and to cost ≈ 4.4 h
per ml.c8i.48xlarge job (13:25 → 17:49 UTC on the first job to reach it) before the job exits by itself.
A job's calibration rows are uploaded chunk by chunk and the last chunk lands before the "gain calibration at
D=4" line is logged, so stopping at that line loses nothing that has landed. Read-only otherwise.

  ./.venv/bin/python stop_at_gate.py [--dry-run] [--loop MINUTES]   # --loop: repeat until no d4v12b job is InProgress
"""
import argparse
import datetime
import time

import boto3

RUN = "t1-all-d4-d4v12b"
LOG_GROUP = "/aws/sagemaker/TrainingJobs"
MARK = '"gain calibration at D=4"'


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%H:%MZ")


def in_progress(sm):
    r = sm.list_training_jobs(NameContains=RUN, StatusEquals="InProgress", MaxResults=100)
    return sorted(j["TrainingJobName"] for j in r["TrainingJobSummaries"])


def at_gain_stage(logs, job) -> bool:
    r = logs.filter_log_events(logGroupName=LOG_GROUP, logStreamNamePrefix=job, filterPattern=MARK, limit=1)
    return bool(r.get("events"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--loop", type=float, default=0.0, help="minutes between passes; 0 = one pass")
    ap.add_argument("--profile", default="xtenure-read")
    a = ap.parse_args()
    sess = boto3.Session(profile_name=a.profile, region_name="eu-north-1")
    sm, logs = sess.client("sagemaker"), sess.client("logs")
    stopped = set()
    while True:
        jobs = in_progress(sm)
        if not jobs:
            print(f"[{stamp()}] no {RUN} job InProgress — done ({len(stopped)} stopped by this script)", flush=True)
            return
        n_gate = 0
        for job in jobs:
            try:
                gate = at_gain_stage(logs, job)
            except Exception as e:      # a log read that fails must not stop the pass
                print(f"[{stamp()}] {job}: log read failed ({e}); left running", flush=True)
                continue
            if not gate:
                continue
            n_gate += 1
            if a.dry_run:
                print(f"[{stamp()}] would stop {job} (at the gain stage)", flush=True)
                continue
            try:
                sm.stop_training_job(TrainingJobName=job)
                stopped.add(job)
                print(f"[{stamp()}] STOPPED {job} — calibration rows landed, gain stage cannot pass the gate", flush=True)
            except Exception as e:
                print(f"[{stamp()}] stop of {job} failed: {e}", flush=True)
        print(f"[{stamp()}] pass: {len(jobs)} InProgress, {n_gate} at the gain stage, {len(stopped)} stopped so far", flush=True)
        if a.loop <= 0:
            return
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    main()

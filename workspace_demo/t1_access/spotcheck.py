#!/usr/bin/env python3
"""spotcheck.py — pull what the cloud shards have written so far and summarise it, while the run is going.

  ./.venv/bin/python spotcheck.py --run full160            # download + summarise every stage
  ./.venv/bin/python spotcheck.py --run full160 --brief    # one line per stage (for a monitor)

Lists results/t1_access/<run>/, downloads every <stage>.shardXXX[-YYY]ofNNN.csv (and the progress
JSONs) that exists, concatenates them into sim_results/<run>/<stage>.csv, and prints per stage:
rows so far, convergence, assay failures, the decision rates per generator (simulate.summarize) and,
for the nulls, the pooled false-positive rate with its Monte-Carlo SE. What to look for as it goes:
convergence near 1, no assay failures, graded nulls giving "graded" or "inconclusive" (mixture at
about the nominal 5 % or below), mixture alternatives giving "mixture" more often as the gain rises,
and no generator whose rows stop growing while its job is InProgress.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import boto3
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BUCKET = "xtenure-cself-pvr"
PREFIX = "results/t1_access/"
STAGES = ("calibration_D4", "power_D4", "recovery_D4", "calibration_D4_5layers", "power_D4_5layers",
          "calibration_D8", "power_D8", "recovery_D8")


def pull(run: str, profile: str, out_dir: str) -> dict:
    """List results/t1_access/<run>/ (the job-written files, not the checkpoints/ or output/ copies), download
    every shard CSV and progress JSON, concatenate per stage."""
    s3 = boto3.Session(profile_name=profile, region_name="eu-north-1").client("s3")
    os.makedirs(out_dir, exist_ok=True)
    prefix = f"{PREFIX}{run}/"
    keys = []
    token = None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=prefix)
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in r.get("Contents", [])]
        token = r.get("NextContinuationToken")
        if not token:
            break
    keys = [k for k in keys if "/" not in k[len(prefix):]]          # top level only
    found = {}
    for stage in STAGES:
        frames, prog = [], []
        for k in keys:
            name = k[len(prefix):]
            if not (name.startswith(stage + ".shard") and name.endswith(".csv")):
                continue
            local = os.path.join(out_dir, name)
            s3.download_file(BUCKET, k, local)
            frames.append(pd.read_csv(local))
            if k + ".progress.json" in keys:
                s3.download_file(BUCKET, k + ".progress.json", local + ".progress.json")
                with open(local + ".progress.json") as fh:
                    prog.append(json.load(fh))
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df.to_csv(os.path.join(out_dir, f"{stage}.csv"), index=False)
            found[stage] = (df, prog)
    if prefix + "gain_calibration.json" in keys:
        s3.download_file(BUCKET, prefix + "gain_calibration.json", os.path.join(out_dir, "gain_calibration.json"))
    return found


def report(found: dict, brief: bool):
    import simulate as S
    if not found:
        print("nothing landed yet")
        return
    for stage, (df, prog) in found.items():
        n = len(df)
        conv = df["convergence"].mean()
        fail = df["failed"].mean()
        dec = df["selection_decision"].value_counts()
        line = f"{stage}: {n} rows from {df['generator'].nunique()} generators; convergence {conv:.3f}; failures {fail:.3%}; "
        nulls = df[df["family"] == "G"]
        if len(nulls):
            fpr = (nulls["selection_decision"] == "mixture").mean()
            line += f"nulls {len(nulls)}: FPR {fpr:.3f} ± {np.sqrt(fpr * (1 - fpr) / len(nulls)):.3f}; "
        alts = df[df["family"] == "X"]
        if len(alts):
            line += f"alternatives {len(alts)}: mixture rate {(alts['selection_decision'] == 'mixture').mean():.3f}; "
        if prog:
            rates = [p.get("rate_per_hour", 0) for p in prog]
            etas = [p.get("eta_hours", 0) for p in prog]
            line += f"{len(prog)} shard files reporting, {sum(rates):.0f} rows/h combined, longest eta {max(etas):.1f} h"
        print(line)
        if not brief:
            print(S.summarize(_tmp_csv(df)).to_string())
            print()


def _tmp_csv(df):
    p = os.path.join("/tmp", f"spotcheck_{os.getpid()}.csv")
    df.to_csv(p, index=False)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="full160")
    ap.add_argument("--profile", default="xtenure-read")
    ap.add_argument("--brief", action="store_true")
    a = ap.parse_args()
    out_dir = os.path.join(HERE, "sim_results", a.run)
    found = pull(a.run, a.profile, out_dir)
    report(found, a.brief)


if __name__ == "__main__":
    main()

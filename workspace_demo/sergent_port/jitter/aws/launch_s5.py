#!/usr/bin/env python3
"""jitter/aws/launch_s5.py — stage S5 on one c7a.24xlarge (DESIGN 8; Codex S3 re-review finding 6), template
aws/userdata_s5.sh.

    launch_s5.py inputs                         tar the 20 participants' S<s>_active_preds.npz (brain_data/sergent2021/
                                                derived), sha256, upload to <code_prefix>/s5_inputs/
    launch_s5.py upload-s4                      upload results/s4/summary.json, s4a.json (and run_config.json) to the
                                                results prefix (after `s4.py evaluate` on the Mac)
    launch_s5.py launch [--config C] [--market spot|on-demand] [--workers 96] [--lifetime-h 6] [--dry-run]

Never writes under t1_access/aws_ec2/runs/.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tarfile

import launch_s4 as L

HERE = os.path.dirname(os.path.abspath(__file__))
J = os.path.dirname(HERE)
DERIVED = os.path.normpath(os.path.join(J, "..", "..", "brain_data", "sergent2021", "derived"))
INPUTS = "s5_inputs_active_S1-S20.tar.gz"
SUBJECTS = range(1, 21)


def inputs(c: dict):
    out = os.path.join(HERE, "bundle", INPUTS)
    with tarfile.open(out, "w:gz") as tf:
        for s in SUBJECTS:
            fn = f"S{s}_active_preds.npz"
            tf.add(os.path.join(DERIVED, fn), arcname=fn)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    with open(out + ".sha256", "w") as f:
        f.write(f"{h}  {INPUTS}\n")
    for fn in (out, out + ".sha256"):
        L.s3(["cp", fn, f"s3://{c['bucket']}/{c['code_prefix']}/s5_inputs/{os.path.basename(fn)}"], c)
    print(f"[s5] inputs {INPUTS} sha256 {h} uploaded ({os.path.getsize(out) / 1e6:.0f} MB)")


def upload_s4(c: dict):
    for fn in ("summary.json", "s4a.json", "run_config.json"):
        p = os.path.join(J, "results", "s4", fn)
        if os.path.exists(p):
            L.s3(["cp", p, f"s3://{c['bucket']}/{c['results_prefix']}/results/s4/{fn}"], c)
            print(f"[s5] uploaded results/s4/{fn}")
        elif fn != "run_config.json":
            raise SystemExit(f"[s5] results/s4/{fn} missing: run `s4.py evaluate` first")


def launch(c: dict, market: str, workers: int, lifetime_h: float, dry: bool):
    with open(os.path.join(HERE, "userdata_s5.sh")) as f:
        txt = f.read().replace("__S5_INPUTS__", INPUTS)
    tmpl = "userdata_s5_filled.sh"
    with open(os.path.join(HERE, tmpl), "w") as f:
        f.write(txt)
    L.launch_one(c, "s5", "s5", workers, "all", lifetime_h, dry, None, part="all", template=tmpl, market=market)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inputs"); sub.add_parser("upload-s4")
    la = sub.add_parser("launch")
    la.add_argument("--market", default="spot", choices=["spot", "on-demand"])
    la.add_argument("--workers", type=int, default=96)
    la.add_argument("--lifetime-h", type=float, default=6.0)
    la.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    c = L.cfg(None if a.config is None else os.path.join(HERE, a.config))
    if a.cmd == "inputs":
        inputs(c)
    elif a.cmd == "upload-s4":
        upload_s4(c)
    else:
        launch(c, a.market, a.workers, a.lifetime_h, a.dry_run)


if __name__ == "__main__":
    main()

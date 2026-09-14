#!/usr/bin/env python3
"""Stage C launcher with a run receipt (PREREG_secondary_melcon.md §9, DRAFT v6; Codex, continuation review 5 §2 and the
v5 calibration revision record §4).

Before any stage C job: pin single-threaded numerics (set before numpy is imported, inherited by the joblib workers);
check the reviewed numerical environment and BMS port hash against EXPECTED; require the namespace to exist already
(never create an empty one) and verify this process's configuration identity against its manifest — v6 carries the BMS
hash, library versions and thread settings inside the identity, and every worker re-verifies it before each recording;
require every reach and calibration entry (content hashes checked on load); refuse uncommitted covered modules; write a
receipt (identity digest, runtime, repository HEAD, reach and calibration digests, usability, amplitudes, the cells not
run for want of an amplitude, the strength-resolution flags) in the namespace; only then run `battery.py --run` in this
verified interpreter. A mismatch stops before anything runs. This file is not one of battery.CODE_FILES.

Usage:  stage_c_launch.py [--n-jobs 2] [--generators G1,G2,G3,X1,X2] [--dry-run]
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import battery as BT  # noqa: E402
import synthetic as SY  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = dict(bms_sha256="6d48a893977e6c71380223f19e70d5fcd95f076eccfa0b8332aada1db1717611", python="3.14.6",
                numpy="2.5.3", scipy="1.18.1", sklearn="1.9.1")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-jobs", type=int, default=2)
    ap.add_argument("--generators", default=",".join(SY.GENERATORS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = BT.runtime()
    mismatch = {k: dict(expected=EXPECTED[k], actual=env[k]) for k in EXPECTED if env[k] != EXPECTED[k]}
    if mismatch:
        sys.exit(f"environment differs from the reviewed one; nothing launched: {json.dumps(mismatch)}")
    identity = BT.config_identity()
    run_dir = BT.namespace_path(identity)
    if not os.path.exists(os.path.join(run_dir, "manifest.json")):
        sys.exit(f"no calibrated namespace for this configuration ({run_dir}); nothing launched")
    ident = BT.verify_runtime(run_dir)
    gens = a.generators.split(",")
    reach, cal = BT.load_store(run_dir, "reach"), BT.load_calibration(run_dir)
    missing = [g for g in gens if g not in reach] + [(g, s) for g in gens for s in BT.STRENGTHS if (g, s) not in cal]
    if missing:
        sys.exit(f"reach or calibration incomplete; nothing launched: {missing}")
    head = subprocess.run(["git", "-C", HERE, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", *BT.CODE_FILES], capture_output=True,
                           text=True).stdout.strip()
    receipt = dict(created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), namespace=run_dir, identity_digest=ident,
                   runtime=env, expected_environment=EXPECTED, repository_head=head,
                   covered_modules_uncommitted=dirty.splitlines(), generators=gens, n_jobs=a.n_jobs, pid=os.getpid(),
                   dry_run=a.dry_run, reach={g: dict(sha256=reach[g]["sha256"], reach=reach[g]["reach"],
                                                     usable=reach[g]["usable"]) for g in gens},
                   calibration={f"{g}|{s}": dict(sha256=cal[(g, s)]["sha256"], accepted=bool(cal[(g, s)]["accepted"]),
                                                 amplitude=cal[(g, s)]["amplitude"], target=cal[(g, s)]["target"],
                                                 check=cal[(g, s)]["check"], unusable_reason=cal[(g, s)]["unusable_reason"])
                                for g in gens for s in BT.STRENGTHS},
                   not_run=[f"{g}|{s}" for g in gens for s in BT.STRENGTHS if cal[(g, s)]["amplitude"] is None],
                   strength_resolution=BT.strength_resolution(reach, cal))
    path = os.path.join(run_dir, f"stage_c_receipt_{receipt['created_utc'].replace(':', '')}.json")
    with open(path, "w") as fh:
        json.dump(receipt, fh, indent=2)
    print(f"receipt {path}")
    print(json.dumps({k: receipt[k] for k in ("identity_digest", "repository_head", "covered_modules_uncommitted", "generators",
                                              "n_jobs", "not_run")}, indent=2))
    if dirty:
        sys.exit("a covered module has uncommitted changes; nothing launched")
    if a.dry_run:
        return
    sys.argv = ["battery.py", "--run", "--n-jobs", str(a.n_jobs), "--generators", ",".join(gens)]
    BT.main()
    print(f"stage C --run finished at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stage C launcher with the run receipt required by Codex's continuation review 5 §2 (PREREG_secondary_melcon.md §9, DRAFT v5).

Before any stage C job: pin single-threaded numerics (set before numpy is imported, inherited by the joblib workers);
verify the imported BMS port's source SHA-256 and the numerical environment against the reviewed values; bind them, the
namespace identity digest, every calibration entry's digest and usability and the repository HEAD into a receipt written
in the namespace; only then run `battery.py --run` in this verified interpreter. A mismatch stops before anything runs.
This file is not one of battery.CODE_FILES, so it does not change the result namespace.

Usage:  stage_c_launch.py [--n-jobs 2] [--generators G1,G2,G3,X1,X2] [--dry-run]
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import scipy  # noqa: E402
import sklearn  # noqa: E402

import battery as BT  # noqa: E402
import synthetic as SY  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BMS_PATH = os.path.normpath(os.path.join(HERE, "..", "sergent_port", "bms.py"))
EXPECTED = dict(bms_sha256="6d48a893977e6c71380223f19e70d5fcd95f076eccfa0b8332aada1db1717611", python="3.14.6",
                numpy="2.5.3", scipy="1.18.1", sklearn="1.9.1")


def environment() -> dict:
    with open(BMS_PATH, "rb") as fh:
        bms = hashlib.sha256(fh.read()).hexdigest()
    return dict(bms_sha256=bms, python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                sklearn=sklearn.__version__)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-jobs", type=int, default=2)
    ap.add_argument("--generators", default=",".join(SY.GENERATORS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = environment()
    mismatch = {k: dict(expected=EXPECTED[k], actual=env[k]) for k in EXPECTED if env[k] != EXPECTED[k]}
    if mismatch:
        sys.exit(f"environment differs from the reviewed one; nothing launched: {json.dumps(mismatch)}")
    identity = BT.config_identity()
    ident = BT.digest(identity)
    run_dir = BT.run_directory(identity)
    gens = a.generators.split(",")
    cal = BT.load_calibration(run_dir)
    missing = [(g, s) for g in gens for s in BT.STRENGTHS if (g, s) not in cal]
    if missing:
        sys.exit(f"calibration incomplete; nothing launched: {missing}")
    head = subprocess.run(["git", "-C", HERE, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", *BT.CODE_FILES], capture_output=True,
                           text=True).stdout.strip()
    receipt = dict(created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), namespace=run_dir, identity_digest=ident,
                   environment=env, expected_environment=EXPECTED, thread_vars={v: os.environ[v] for v in THREAD_VARS},
                   bms_path=BMS_PATH, repository_head=head, covered_modules_uncommitted=dirty.splitlines(),
                   generators=gens, n_jobs=a.n_jobs, pid=os.getpid(), dry_run=a.dry_run,
                   calibration={f"{g}|{s}": dict(digest=BT.digest(cal[(g, s)]), accepted=bool(cal[(g, s)]["accepted"]),
                                                 amplitude=cal[(g, s)]["amplitude"], target=cal[(g, s)]["target"],
                                                 check=cal[(g, s)]["check"])
                                for g in gens for s in BT.STRENGTHS})
    path = os.path.join(run_dir, f"stage_c_receipt_{receipt['created_utc'].replace(':', '')}.json")
    with open(path, "w") as fh:
        json.dump(receipt, fh, indent=2)
    print(f"receipt {path}")
    print(json.dumps({k: receipt[k] for k in ("identity_digest", "environment", "repository_head", "covered_modules_uncommitted",
                                              "generators", "n_jobs")}, indent=2))
    if dirty:
        sys.exit("a covered module has uncommitted changes; nothing launched")
    if a.dry_run:
        return
    sys.argv = ["battery.py", "--run", "--n-jobs", str(a.n_jobs), "--generators", ",".join(gens)]
    BT.main()
    print(f"stage C --run finished at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")


if __name__ == "__main__":
    main()

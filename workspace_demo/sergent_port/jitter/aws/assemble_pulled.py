#!/usr/bin/env python3
"""jitter/aws/assemble_pulled.py — after `launch_s4.py pull --what s2`, build the per-set records (set_<r>.json) of the
S2 closure under results/s2_aws from the per-task files that the paired hosts of each setting left on S3 (each host
assembles only the sets of its own queue, and a host stopped early assembles none). Task files are kept. Then prints
the s2.summary over results/s2_aws. 24 Oct 2026.

    aws/assemble_pulled.py [results root, default results/s2_aws] [--settings W2,T1,O1] [--R 25]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = os.path.dirname(HERE)
sys.path.insert(0, J)
import s2  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=os.path.join(J, "results", "s2_aws"))
    ap.add_argument("--settings", default="W2,T1,O1")
    ap.add_argument("--R", type=int, default=25)
    a = ap.parse_args()
    s2.S2_DIR = a.root
    s2.DEC_DIR = os.path.join(a.root, "decision")
    s2.ARC_DIR = os.path.join(a.root, "archive")
    for S in a.settings.split(","):
        done, missing = [], {}
        for r in range(a.R):
            path = os.path.join(s2.DEC_DIR, S, f"set_{r}.json")
            if os.path.exists(path):
                done.append(r)
                continue
            absent = [m for m in range(20) if not os.path.exists(s2.task_paths(S, r, m)[0])]
            if absent:
                missing[r] = absent
                continue
            s2.assemble_set(S, r, remove_task_files=False)
            done.append(r)
        print(f"[assemble] {S}: {len(done)} sets present/assembled; incomplete sets {missing or 'none'}", flush=True)
    print(s2.summary_markdown(s2.summarize()))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""jitter/aws/launch_s2final.py — the S2 final evidence fleet (25 Oct 2026; Codex S3 re-review findings 3, 4, 9, closure
order 14): one CHECKS host (final-rule paired checks F/G/H on W2 set 0, then crosseval and final-summary) and K DEV hosts
(the three R = 25 development blocks W2, T1, O1 as disjoint hash shards i/K), all c7a.24xlarge spot under the latest
bundle (aws/userdata_s2final.sh). The spot quota is five c7a.24xlarge per region, so the hosts are spread over the four
configured regions in order (eu-north-1 first, the checks host there).

    launch_s2final.py [--dev-shards 19] [--only checks|dev] [--shards 3,7] [--dry-run]

Results: s3://<bucket>/<results_prefix>/s2final/{checks,dev,dev_archive}/; logs <results_prefix>/logs/s2final_*.log.
Never writes under t1_access/aws_ec2/runs/.
"""
from __future__ import annotations

import argparse
import os

import launch_s4 as L

HERE = os.path.dirname(os.path.abspath(__file__))
REGION_CONFIGS = [None, "s4_aws_euw1.json", "s4_aws_use1.json", "s4_aws_usw2.json"]
PER_REGION = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-shards", type=int, default=19)
    ap.add_argument("--only", choices=["checks", "dev"], default=None)
    ap.add_argument("--shards", default=None, help="comma list of dev shard indices to (re)launch, e.g. after a spot loss")
    ap.add_argument("--workers", type=int, default=96)
    ap.add_argument("--lifetime-h", type=float, default=6.0)
    ap.add_argument("--checks-lifetime-h", type=float, default=5.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfgs = [L.cfg(None if p is None else os.path.join(HERE, p)) for p in REGION_CONFIGS]
    for c in cfgs[1:]:
        assert (c["bucket"], c["code_prefix"], c["results_prefix"]) == (cfgs[0]["bucket"], cfgs[0]["code_prefix"], cfgs[0]["results_prefix"])
    slots = [(ci, j) for ci in range(len(cfgs)) for j in range(PER_REGION)]      # (region, slot) in launch order
    hosts = [("checks", "checks")] + [("dev", f"{i}/{a.dev_shards}") for i in range(a.dev_shards)]
    assert len(hosts) <= len(slots), f"{len(hosts)} hosts exceed the {len(slots)} spot slots"
    want = None if a.shards is None else {f"{int(i)}/{a.dev_shards}" for i in a.shards.split(",")}
    for (part, shard), (ci, j) in zip(hosts, slots):
        if a.only and part != a.only:
            continue
        if want is not None and shard not in want:
            continue
        c = cfgs[ci]
        az = c["subnet_order"][j % len(c["subnet_order"])]
        life = a.checks_lifetime_h if part == "checks" else a.lifetime_h
        print(f"[s2final] {part} {shard} -> {c['region']} {az}, lifetime {life} h")
        L.launch_one(c, "s2final", shard, a.workers, "all", life, a.dry_run, az, part=part,
                     template="userdata_s2final.sh", market="spot")


if __name__ == "__main__":
    main()

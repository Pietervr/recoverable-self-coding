"""aws_env.py — the one place that says which AWS region and bucket the T1 cloud tools talk to.

SageMaker requires a training job's input bucket to be in the job's region, so region and bucket
travel together. Set T1_AWS_REGION to pick the pair (T1_AWS_BUCKET overrides the bucket alone):

  eu-north-1  xtenure-cself-pvr        the original home (d4v12b, the 13 Sept 2026 control and omega-2 bank)
  us-west-2   xtenure-cself-pvr-usw2   from 13 Sept 2026: cheaper and calmer c8i spot pools (R052 log)

launch_t1.py, spotcheck.py and the monitors import from here; the job itself (t1_job.py) is region-blind
and takes its bucket from RESULTS_URI. Existing result prefixes were copied across so a --resume finds them.
"""
from __future__ import annotations

import os

ACCOUNT = "763348960464"
REGION_BUCKETS = {"eu-north-1": "xtenure-cself-pvr", "us-west-2": "xtenure-cself-pvr-usw2"}
REGION = os.environ.get("T1_AWS_REGION", "eu-north-1")
if REGION not in REGION_BUCKETS and not os.environ.get("T1_AWS_BUCKET"):
    raise SystemExit(f"T1_AWS_REGION={REGION}: no bucket known for it; set T1_AWS_BUCKET or add it to aws_env.REGION_BUCKETS")
BUCKET = os.environ.get("T1_AWS_BUCKET") or REGION_BUCKETS[REGION]


def cache_dir(here: str, run: str) -> str:
    """The local mirror of results/t1_access/<run>/ for the selected bucket: sim_results/<run> for the original
    Stockholm bucket (every existing path unchanged), sim_results/<run>@<bucket> for any other, so a local cache
    never crosses sources (Codex, continuation review 3, 13 Sept 2026)."""
    name = run if BUCKET == REGION_BUCKETS["eu-north-1"] else f"{run}@{BUCKET}"
    return os.path.join(here, "sim_results", name)

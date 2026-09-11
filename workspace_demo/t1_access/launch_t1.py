#!/usr/bin/env python3
"""launch_t1.py — launch one T1 simulation task (t1_job.py) as a SageMaker TRAINING job in the shared
xTenure account, following xTenure-MCED/phase1/launch_*.py: code channel from S3, the prebuilt CPU
training image, the job execution role, results uploaded by the job to RESULTS_URI, auto-terminating.

  ./.venv/bin/python launch_t1.py --task calibration --n-rep 1000 --D 4 --run full --spot --shards 20
  ./.venv/bin/python launch_t1.py --task calibration --n-rep 8 --generators M2B --run smoke --spot --max-hours 2
  ./.venv/bin/python launch_t1.py --status                                                  # our jobs' state
  ./.venv/bin/python launch_t1.py --stop <job-name>                                         # stop one (resumable)

Sharding: --shards N launches N jobs (SHARD=i, N_SHARDS=N); each takes every N-th (point, replicate)
task, writes its own CSV at RESULTS_URI and resumes from it. The account's spot quota (2026-09-11)
covers instance sizes up to 2xlarge (4xlarge for r6i), 20 instances across all spot jobs, so the
full runs go as 20 sharded spot jobs on ml.c8i.2xlarge (8 vCPU) rather than one on-demand 48xlarge.

Cost hygiene (shared account): training jobs terminate themselves; nothing persistent is created;
never touch anyone else's resources. The instance price is printed before launch.
"""
from __future__ import annotations

import argparse
import os
import time

import boto3

ACCOUNT, REGION = "763348960464", "eu-north-1"
EXEC_ROLE = f"arn:aws:iam::{ACCOUNT}:role/xtenure-job-execution-role"
IMAGE = f"763104351884.dkr.ecr.{REGION}.amazonaws.com/pytorch-training:2.8.0-cpu-py312-ubuntu22.04-sagemaker"
BUCKET = "xtenure-cself-pvr"
CODE_PREFIX = "code/t1_access/"
RESULTS_ROOT = f"s3://{BUCKET}/results/t1_access/"
CODE_FILES = ("models.py", "analyze.py", "simulate.py", "t1_job.py")
ENTRY = ("pip install -q 'jax==0.11.1' 'scipy>=1.14' pandas joblib boto3 >/dev/null 2>&1; "
         "python /opt/ml/input/data/code/t1_job.py")
PRICE_USD_H = {"ml.c7i.48xlarge": 11.01, "ml.c7i.24xlarge": 5.50, "ml.c7i.16xlarge": 3.67, "ml.c7i.2xlarge": 0.459,
               "ml.c8i.2xlarge": 0.50, "ml.r6i.4xlarge": 1.30}   # on-demand, eu-north-1 Training; c8i/r6i estimated
HERE = os.path.dirname(os.path.abspath(__file__))


def upload_code(s3):
    for f in CODE_FILES:
        s3.upload_file(os.path.join(HERE, f), BUCKET, CODE_PREFIX + f)
    print(f"code -> s3://{BUCKET}/{CODE_PREFIX} ({', '.join(CODE_FILES)})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["all", "calibration", "power", "recovery", "gain", "bench"])
    ap.add_argument("--n-rep", type=int, default=1000)
    ap.add_argument("--n-rep-recovery", type=int, default=200)
    ap.add_argument("--n-rep-5layers", type=int, default=200)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--layers", default="41")
    ap.add_argument("--generators", default="")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n-jobs", type=int, default=0, help="0 = every vCPU")
    ap.add_argument("--n-starts-inner", type=int, default=8, help="inner-selection starts (§14 allows 4)")
    ap.add_argument("--instance-type", default="ml.c8i.2xlarge")
    ap.add_argument("--max-hours", type=float, default=48.0)
    ap.add_argument("--spot", action="store_true", help="managed spot training (waits up to 2x max-hours for capacity)")
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--shard-start", type=int, default=0, help="launch shards shard-start..shards-1 (to relaunch a few)")
    ap.add_argument("--run", default="full", help="results subfolder under results/t1_access/")
    ap.add_argument("--profile", default="xtenure-read")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--stop", default=None, metavar="JOB", help="a job name, or a prefix ending in * to stop several")
    a = ap.parse_args()
    sess = boto3.Session(profile_name=a.profile, region_name=REGION)
    sm = sess.client("sagemaker")
    if a.status:
        r = sm.list_training_jobs(NameContains="t1-", SortBy="CreationTime", SortOrder="Descending", MaxResults=60)
        for j in r["TrainingJobSummaries"]:
            d = sm.describe_training_job(TrainingJobName=j["TrainingJobName"])
            secs = d.get("TrainingTimeInSeconds", 0) or 0
            bill = d.get("BillableTimeInSeconds", 0) or 0
            print(f"{j['TrainingJobName']:52s} {j['TrainingJobStatus']:10s} {d.get('SecondaryStatus',''):12s} "
                  f"{d['ResourceConfig']['InstanceType']:15s} {secs/3600:6.2f} h train {bill/3600:6.2f} h billed  "
                  f"{d.get('FailureReason','')[:60]}")
        return
    if a.stop and a.stop.endswith("*"):
        r = sm.list_training_jobs(NameContains=a.stop[:-1], StatusEquals="InProgress", MaxResults=60)
        for j in r["TrainingJobSummaries"]:
            sm.stop_training_job(TrainingJobName=j["TrainingJobName"])
            print(f"stop requested for {j['TrainingJobName']}")
        return
    if a.stop:
        sm.stop_training_job(TrainingJobName=a.stop)
        print(f"stop requested for {a.stop} (rows already uploaded stay at RESULTS_URI; relaunch resumes)")
        return
    if not a.task:
        ap.error("--task is required")
    results_uri = f"{RESULTS_ROOT}{a.run}/"
    env = {"TASK": a.task, "N_REP": str(a.n_rep), "N_REP_RECOVERY": str(a.n_rep_recovery),
           "N_REP_5LAYERS": str(a.n_rep_5layers), "D": str(a.D), "LAYERS": a.layers, "SEED": str(a.seed),
           "RESULTS_URI": results_uri, "NPROC": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
           "MKL_NUM_THREADS": "1", "N_STARTS_INNER": str(a.n_starts_inner)}
    if a.generators:
        env["GENERATORS"] = a.generators
    if a.n_jobs:
        env["N_JOBS"] = str(a.n_jobs)
    stamp = int(time.time())
    price = PRICE_USD_H.get(a.instance_type)
    stopping = {"MaxRuntimeInSeconds": int(a.max_hours * 3600)}
    if a.spot:
        stopping["MaxWaitTimeInSeconds"] = int(2 * a.max_hours * 3600)
    if not a.dry_run:
        upload_code(sess.client("s3"))
    for shard in range(a.shard_start, a.shards):
        env_s = dict(env)
        tag = ""
        if a.shards > 1:
            env_s["SHARD"] = str(shard); env_s["N_SHARDS"] = str(a.shards)
            tag = f"-s{shard:02d}of{a.shards:02d}"
        job = f"t1-{a.task}-d{a.D}-{a.run.replace('_', '-')[:12]}{tag}-{stamp}"
        spec = dict(
            TrainingJobName=job,
            AlgorithmSpecification={"TrainingImage": IMAGE, "TrainingInputMode": "File",
                                    "ContainerEntrypoint": ["bash", "-lc", ENTRY]},
            RoleArn=EXEC_ROLE,
            InputDataConfig=[{"ChannelName": "code", "DataSource": {"S3DataSource": {
                "S3DataType": "S3Prefix", "S3Uri": f"s3://{BUCKET}/{CODE_PREFIX}", "S3DataDistributionType": "FullyReplicated"}}}],
            OutputDataConfig={"S3OutputPath": f"{RESULTS_ROOT}{a.run}/output/"},
            ResourceConfig={"InstanceType": a.instance_type, "InstanceCount": 1, "VolumeSizeInGB": 30},
            StoppingCondition=stopping,
            Environment=env_s,
            EnableManagedSpotTraining=bool(a.spot),
        )
        if a.spot:
            spec["CheckpointConfig"] = {"S3Uri": f"{RESULTS_ROOT}{a.run}/checkpoints{tag}/", "LocalPath": "/opt/ml/checkpoints"}
        print(f"job {job}: {a.task} n_rep={a.n_rep} D={a.D} layers={a.layers} on {a.instance_type}"
              f"{' SPOT' if a.spot else ''} (max {a.max_hours} h{f', at most USD {price * a.max_hours:.0f} on demand' if price else ''})"
              f" -> {results_uri}")
        if a.dry_run:
            import json
            print(json.dumps(spec, indent=1))
            continue
        sm.create_training_job(**spec)
        print(f"launched {job}")


if __name__ == "__main__":
    main()

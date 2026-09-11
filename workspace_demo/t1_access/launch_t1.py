#!/usr/bin/env python3
"""launch_t1.py — launch one T1 simulation task (t1_job.py) as a SageMaker TRAINING job in the shared
xTenure account, following xTenure-MCED/phase1/launch_*.py: code channel from S3, the prebuilt CPU
training image, the job execution role, results uploaded by the job to RESULTS_URI, auto-terminating.

  ./.venv/bin/python launch_t1.py --task calibration --n-rep 1000 --D 4 --run full_2026-09-11
  ./.venv/bin/python launch_t1.py --task calibration --n-rep 16 --run smoke --max-hours 1   # the smoke run
  ./.venv/bin/python launch_t1.py --status                                                  # our jobs' state
  ./.venv/bin/python launch_t1.py --stop <job-name>                                         # stop one (resumable)

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
PRICE_USD_H = {"ml.c7i.48xlarge": 11.01, "ml.c7i.24xlarge": 5.50, "ml.c7i.16xlarge": 3.67, "ml.c7i.2xlarge": 0.46}
HERE = os.path.dirname(os.path.abspath(__file__))


def upload_code(s3):
    for f in CODE_FILES:
        s3.upload_file(os.path.join(HERE, f), BUCKET, CODE_PREFIX + f)
    print(f"code -> s3://{BUCKET}/{CODE_PREFIX} ({', '.join(CODE_FILES)})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["calibration", "power", "recovery", "gain"])
    ap.add_argument("--n-rep", type=int, default=1000)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--layers", default="41")
    ap.add_argument("--generators", default="")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n-jobs", type=int, default=0, help="0 = every vCPU")
    ap.add_argument("--instance-type", default="ml.c7i.48xlarge")
    ap.add_argument("--max-hours", type=float, default=36.0)
    ap.add_argument("--run", default="full_2026-09-11", help="results subfolder under results/t1_access/")
    ap.add_argument("--profile", default="xtenure-read")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--stop", default=None, metavar="JOB")
    a = ap.parse_args()
    sess = boto3.Session(profile_name=a.profile, region_name=REGION)
    sm = sess.client("sagemaker")
    if a.status:
        r = sm.list_training_jobs(NameContains="t1-", SortBy="CreationTime", SortOrder="Descending", MaxResults=20)
        for j in r["TrainingJobSummaries"]:
            d = sm.describe_training_job(TrainingJobName=j["TrainingJobName"])
            secs = d.get("TrainingTimeInSeconds", 0) or 0
            print(f"{j['TrainingJobName']:42s} {j['TrainingJobStatus']:10s} {d.get('SecondaryStatus',''):12s} "
                  f"{d['ResourceConfig']['InstanceType']:16s} {secs/3600:6.2f} h  {d.get('FailureReason','')[:80]}")
        return
    if a.stop:
        sm.stop_training_job(TrainingJobName=a.stop)
        print(f"stop requested for {a.stop} (rows already uploaded stay at RESULTS_URI; relaunch resumes)")
        return
    if not a.task:
        ap.error("--task is required")
    results_uri = f"{RESULTS_ROOT}{a.run}/"
    env = {"TASK": a.task, "N_REP": str(a.n_rep), "D": str(a.D), "LAYERS": a.layers, "SEED": str(a.seed),
           "RESULTS_URI": results_uri, "NPROC": "1"}
    if a.generators:
        env["GENERATORS"] = a.generators
    if a.n_jobs:
        env["N_JOBS"] = str(a.n_jobs)
    job = f"t1-{a.task}-d{a.D}-{a.run.replace('_', '-')[:16]}-{int(time.time())}"
    spec = dict(
        TrainingJobName=job,
        AlgorithmSpecification={"TrainingImage": IMAGE, "TrainingInputMode": "File",
                                "ContainerEntrypoint": ["bash", "-lc", ENTRY]},
        RoleArn=EXEC_ROLE,
        InputDataConfig=[{"ChannelName": "code", "DataSource": {"S3DataSource": {
            "S3DataType": "S3Prefix", "S3Uri": f"s3://{BUCKET}/{CODE_PREFIX}", "S3DataDistributionType": "FullyReplicated"}}}],
        OutputDataConfig={"S3OutputPath": f"{RESULTS_ROOT}{a.run}/output/"},
        ResourceConfig={"InstanceType": a.instance_type, "InstanceCount": 1, "VolumeSizeInGB": 50},
        StoppingCondition={"MaxRuntimeInSeconds": int(a.max_hours * 3600)},
        Environment=env,
    )
    price = PRICE_USD_H.get(a.instance_type)
    print(f"job {job}: {a.task} n_rep={a.n_rep} D={a.D} layers={a.layers} on {a.instance_type} "
          f"(max {a.max_hours} h{f', at most USD {price * a.max_hours:.0f}' if price else ''}) -> {results_uri}")
    if a.dry_run:
        import json
        print(json.dumps(spec, indent=1))
        return
    upload_code(sess.client("s3"))
    sm.create_training_job(**spec)
    print(f"launched {job}")


if __name__ == "__main__":
    main()

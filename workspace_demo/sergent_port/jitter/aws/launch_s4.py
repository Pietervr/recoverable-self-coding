#!/usr/bin/env python3
"""jitter/aws/launch_s4.py — launch, watch and stop the EC2 workers of the jitter S4 battery (DESIGN rev 7 §8;
owner 24 Oct 2026: "we need to do it on aws - go", within the standing USD 3,000 cap).

    launch_s4.py bundle                         build the code bundle (aws/make_bundle.sh) and upload it to S3
    launch_s4.py launch --mode s4a --workers 96 [--lifetime-h 10]          one instance, S4a synchronously
    launch_s4.py launch --mode s4b --shards 4 --workers 96 [--kind all]    K instances, shard i/K each
    launch_s4.py status                         instances of this job (tag Job=jitter-s4), uptime, estimated spend
    launch_s4.py pull                           s3 sync results/s4 down to the Mac
    launch_s4.py stop [--all | --instance ID]   terminate

Configuration in aws/s4_aws.json: profile, region, ami, instance_type, subnet_id, security_group_id,
iam_instance_profile, key_name, bucket, prefix, spot_max_price (None = on-demand), on_demand_fallback (bool).
Every instance: tags Job=jitter-s4 Mode=<mode> Shard=<i/K>, InstanceInitiatedShutdownBehavior=terminate (the
user-data ends with shutdown -h now), a hard lifetime timer inside the user-data, results synced to S3 every 5 min.
Spend is estimated from launch time × the price (spot price at launch or the on-demand list price in the config) and
written to aws/s4_spend.json at every `status`; the R052 log carries the figure.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = os.path.dirname(HERE)
CFG_PATH = os.path.join(HERE, "s4_aws.json")
STATE_PATH = os.path.join(HERE, "s4_instances.json")
SPEND_PATH = os.path.join(HERE, "s4_spend.json")
PINS = dict(NUMPY="2.5.3", SCIPY="1.18.1", JAX="0.11.1", JOBLIB="1.6.0", PANDAS="3.0.5")


def cfg() -> dict:
    with open(CFG_PATH) as f:
        return json.load(f)


def aws(args: list, c: dict, parse=True):
    cmd = ["aws", "--profile", c["profile"], "--region", c["region"], "--output", "json"] + args
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"aws {' '.join(args[:3])}: rc {out.returncode}: {out.stderr.strip()[:500]}")
    return json.loads(out.stdout) if parse and out.stdout.strip() else out.stdout


def state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return dict(instances=[])


def save_state(s: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(s, f, indent=1)


def bundle(c: dict) -> str:
    out = subprocess.run(["bash", os.path.join(HERE, "make_bundle.sh")], capture_output=True, text=True, cwd=J)
    print(out.stdout.strip())
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    names = sorted(f for f in os.listdir(os.path.join(HERE, "bundle")) if f.endswith(".tar.gz"))
    name = names[-1]
    for fn in (name, name + ".sha256"):
        aws(["s3", "cp", os.path.join(HERE, "bundle", fn), f"s3://{c['bucket']}/{c['prefix']}/bundle/{fn}"], c, parse=False)
    print(f"[launch] bundle {name} uploaded to s3://{c['bucket']}/{c['prefix']}/bundle/")
    return name


def latest_bundle() -> str:
    names = sorted(f for f in os.listdir(os.path.join(HERE, "bundle")) if f.endswith(".tar.gz"))
    if not names:
        raise RuntimeError("no bundle; run `launch_s4.py bundle` first")
    return names[-1]


def user_data(c: dict, mode: str, shard: str, workers: int, kind: str, lifetime_s: int) -> str:
    with open(os.path.join(HERE, "userdata_s4.sh")) as f:
        txt = f.read()
    rep = dict(BUCKET=c["bucket"], PREFIX=c["prefix"], BUNDLE=latest_bundle(), MODE=mode, SHARD=shard,
               SHARD_TAG=shard.replace("/", "of"), WORKERS=str(workers), KIND=kind, LIFETIME_S=str(lifetime_s), **PINS)
    for k, v in rep.items():
        txt = txt.replace(f"__{k}__", v)
    assert "__" not in txt.replace("___", ""), "unfilled placeholder in user-data"
    return txt


def launch_one(c: dict, mode: str, shard: str, workers: int, kind: str, lifetime_h: float, dry: bool) -> dict:
    ud = user_data(c, mode, shard, workers, kind, int(lifetime_h * 3600))
    spec = dict(
        ImageId=c["ami"], InstanceType=c["instance_type"], MinCount=1, MaxCount=1,
        KeyName=c.get("key_name"), SubnetId=c["subnet_id"], SecurityGroupIds=[c["security_group_id"]],
        IamInstanceProfile=dict(Name=c["iam_instance_profile"]) if c.get("iam_instance_profile") else None,
        InstanceInitiatedShutdownBehavior="terminate",
        BlockDeviceMappings=[dict(DeviceName=c.get("root_device", "/dev/xvda"), Ebs=dict(VolumeSize=int(c.get("root_gb", 30)), VolumeType="gp3", DeleteOnTermination=True))],
        TagSpecifications=[dict(ResourceType="instance", Tags=[dict(Key="Job", Value="jitter-s4"), dict(Key="Mode", Value=mode),
                                                               dict(Key="Shard", Value=shard), dict(Key="Name", Value=f"jitter-s4-{mode}-{shard.replace('/', 'of')}")]),
                           dict(ResourceType="volume", Tags=[dict(Key="Job", Value="jitter-s4")])],
        UserData=base64.b64encode(ud.encode()).decode(),
    )
    if c.get("spot_max_price") is not None:
        spec["InstanceMarketOptions"] = dict(MarketType="spot", SpotOptions=dict(MaxPrice=str(c["spot_max_price"]), SpotInstanceType="one-time",
                                                                                InstanceInterruptionBehavior="terminate"))
    spec = {k: v for k, v in spec.items() if v is not None}
    if dry:
        print(json.dumps({k: v for k, v in spec.items() if k != "UserData"}, indent=1))
        return dict(dry=True)
    cli = os.path.join(HERE, f"run_{mode}_{shard.replace('/', 'of')}.json")
    with open(cli, "w") as f:
        json.dump(spec, f)
    try:
        res = aws(["ec2", "run-instances", "--cli-input-json", f"file://{cli}"], c)
        market = "spot"
    except RuntimeError as e:
        if c.get("spot_max_price") is not None and c.get("on_demand_fallback") and ("InsufficientInstanceCapacity" in str(e) or "SpotMaxPriceTooLow" in str(e) or "MaxSpotInstanceCountExceeded" in str(e)):
            print(f"[launch] spot refused ({str(e)[:160]}); on-demand fallback")
            spec.pop("InstanceMarketOptions", None)
            with open(cli, "w") as f:
                json.dump(spec, f)
            res = aws(["ec2", "run-instances", "--cli-input-json", f"file://{cli}"], c)
            market = "on-demand"
        else:
            raise
    inst = res["Instances"][0]
    rec = dict(instance_id=inst["InstanceId"], mode=mode, shard=shard, kind=kind, workers=workers, market=market,
               launched_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(), lifetime_h=lifetime_h,
               instance_type=c["instance_type"], az=inst.get("Placement", {}).get("AvailabilityZone"))
    s = state(); s["instances"].append(rec); save_state(s)
    print(f"[launch] {rec}")
    return rec


def status(c: dict) -> dict:
    res = aws(["ec2", "describe-instances", "--filters", "Name=tag:Job,Values=jitter-s4"], c)
    rows = []
    now = _dt.datetime.now(_dt.timezone.utc)
    total = 0.0
    for r in res.get("Reservations", []):
        for i in r["Instances"]:
            tags = {t["Key"]: t["Value"] for t in i.get("Tags", [])}
            st = i["State"]["Name"]
            launch = _dt.datetime.fromisoformat(i["LaunchTime"].replace("Z", "+00:00"))
            hours = (now - launch).total_seconds() / 3600.0 if st in ("running", "pending", "shutting-down") else None
            price = c.get("spot_price_estimate_usd_h") if i.get("InstanceLifecycle") == "spot" else c.get("on_demand_usd_h")
            spend = (hours or 0.0) * (price or 0.0)
            total += spend
            rows.append(dict(id=i["InstanceId"], state=st, type=i["InstanceType"], lifecycle=i.get("InstanceLifecycle", "on-demand"),
                             mode=tags.get("Mode"), shard=tags.get("Shard"), launched=i["LaunchTime"], hours=hours, est_usd=round(spend, 2)))
    for row in rows:
        print(row)
    rec = dict(utc=now.isoformat(), instances=rows, est_running_usd=round(total, 2))
    prev = {}
    if os.path.exists(SPEND_PATH):
        with open(SPEND_PATH) as f:
            prev = json.load(f)
    rec["closed_usd"] = prev.get("closed_usd", 0.0)
    with open(SPEND_PATH, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"[status] running-instance spend so far about USD {total:.2f} (+ closed USD {rec['closed_usd']:.2f})")
    return rec


def pull(c: dict):
    dst = os.path.join(J, "results", "s4")
    os.makedirs(dst, exist_ok=True)
    out = subprocess.run(["aws", "--profile", c["profile"], "--region", c["region"], "s3", "sync",
                          f"s3://{c['bucket']}/{c['prefix']}/results/s4", dst, "--quiet"], capture_output=True, text=True)
    print("[pull] rc", out.returncode, out.stderr.strip()[:300])
    for mode in ("calibration", "validation", "c0", "rec"):
        d = os.path.join(dst, mode)
        n = sum(len(fs) for _, _, fs in os.walk(d)) if os.path.isdir(d) else 0
        print(f"[pull] {mode}: {n} files")


def stop(c: dict, instance: str | None, all_: bool):
    ids = []
    if instance:
        ids = [instance]
    elif all_:
        res = aws(["ec2", "describe-instances", "--filters", "Name=tag:Job,Values=jitter-s4", "Name=instance-state-name,Values=pending,running"], c)
        ids = [i["InstanceId"] for r in res.get("Reservations", []) for i in r["Instances"]]
    if not ids:
        print("[stop] nothing to stop"); return
    aws(["ec2", "terminate-instances", "--instance-ids"] + ids, c)
    print(f"[stop] terminated {ids}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bundle")
    la = sub.add_parser("launch")
    la.add_argument("--mode", required=True, choices=["s4a", "s4b"])
    la.add_argument("--shards", type=int, default=1)
    la.add_argument("--shard-start", type=int, default=0)
    la.add_argument("--workers", type=int, default=96)
    la.add_argument("--kind", default="all", choices=["cv", "rec", "all"])
    la.add_argument("--lifetime-h", type=float, default=12.0)
    la.add_argument("--dry-run", action="store_true")
    sub.add_parser("status"); sub.add_parser("pull")
    stp = sub.add_parser("stop"); stp.add_argument("--instance", default=None); stp.add_argument("--all", action="store_true")
    a = ap.parse_args()
    c = cfg()
    if a.cmd == "bundle":
        bundle(c)
    elif a.cmd == "launch":
        if a.mode == "s4a":
            launch_one(c, "s4a", "1/1", a.workers, a.kind, a.lifetime_h, a.dry_run)
        else:
            for i in range(a.shard_start, a.shards):
                launch_one(c, "s4b", f"{i}/{a.shards}", a.workers, a.kind, a.lifetime_h, a.dry_run)
    elif a.cmd == "status":
        status(c)
    elif a.cmd == "pull":
        pull(c)
    elif a.cmd == "stop":
        stop(c, a.instance, a.all)


if __name__ == "__main__":
    main()

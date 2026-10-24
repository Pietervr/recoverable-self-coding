#!/usr/bin/env python3
"""jitter/aws/launch_s4.py — launch, watch and stop the EC2 workers of the jitter study on AWS (DESIGN rev 7 §8; owner
24 Oct 2026: "we need to do it on aws - go", within the standing USD 3,000 cap).

    launch_s4.py bundle                                   build the code bundle (aws/make_bundle.sh) and upload it to S3
    launch_s4.py probe                                    1-byte Put/Get on the code prefix and Get on the results prefix
    launch_s4.py launch --mode s2closure --workers 96 --lifetime-h 6 [--dry-run]     one instance: the S2 closure
    launch_s4.py launch --mode s4a --workers 96 --lifetime-h 10                       one instance: S4a synchronously
    launch_s4.py launch --mode s4b --shards 4 --workers 96 --lifetime-h 24 [--kind all]   K instances, shard i/K each
    launch_s4.py status                                   instances of this job (tag Job=jitter-s4), uptime, estimated spend
    launch_s4.py pull [--what s4|s2]                      s3 sync results down to the Mac (into results/s4 or results/s2_aws)
    launch_s4.py stop [--all | --instance ID]             terminate

Configuration in aws/s4_aws.json (see the file). What the T1 tooling taught (aws_ec2/README.md, the 24 Oct inventory):
EC2 in eu-north-1, the bucket in us-west-2 (pinned for every s3 call); the instance role may GetObject under the CODE
prefix and Get/Put under the RESULTS prefix only; Terminate works only on resources tagged project=t1 (so every instance
and volume carries it); no key pairs exist; user-data goes as --user-data file://; a real EC2 DryRun answers
DryRunOperation; spot interruption is flushed by the instance and resumed by relaunch (per-dataset result files).
Spend is estimated from launch time × the configured price and written to aws/s4_spend.json at every `status`.
Never writes under t1_access/aws_ec2/runs/.
"""
from __future__ import annotations

import argparse
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
JOB_TAG = "jitter-s4"


def cfg(path: str | None = None) -> dict:
    with open(path or CFG_PATH) as f:
        return json.load(f)


def _run(cmd: list, parse=True):
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:6])}: rc {out.returncode}: {out.stderr.strip()[:600]}")
    return json.loads(out.stdout) if parse and out.stdout.strip() else out.stdout


def ec2(args: list, c: dict, parse=True):
    return _run(["aws", "--profile", c["profile"], "--region", c["region"], "--output", "json", "ec2"] + args, parse)


def s3(args: list, c: dict, parse=False):
    return _run(["aws", "--profile", c["profile"], "--region", c["s3_region"], "--output", "json", "s3"] + args, parse)


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
    name = latest_bundle()
    for fn in (name, name + ".sha256"):
        s3(["cp", os.path.join(HERE, "bundle", fn), f"s3://{c['bucket']}/{c['code_prefix']}/bundle/{fn}"], c)
    print(f"[launch] bundle {name} uploaded to s3://{c['bucket']}/{c['code_prefix']}/bundle/")
    return name


def latest_bundle() -> str:
    names = sorted((os.path.getmtime(os.path.join(HERE, "bundle", f)), f) for f in os.listdir(os.path.join(HERE, "bundle")) if f.endswith(".tar.gz"))
    if not names:
        raise RuntimeError("no bundle; run `launch_s4.py bundle` first")
    return names[-1][1]


def probe(c: dict):
    """The Mac's own rights: Put + Get on the code prefix (the bundle path), Get (list) on the results prefix."""
    p = os.path.join(HERE, "probe.txt")
    with open(p, "w") as f:
        f.write("1")
    s3(["cp", p, f"s3://{c['bucket']}/{c['code_prefix']}/probe.txt"], c)
    s3(["cp", f"s3://{c['bucket']}/{c['code_prefix']}/probe.txt", p + ".back"], c)
    print("[probe] code prefix: Put + Get ok")
    try:
        s3(["ls", f"s3://{c['bucket']}/{c['results_prefix']}/"], c)
        print("[probe] results prefix: list ok")
    except RuntimeError as e:
        print(f"[probe] results prefix list: {str(e)[:200]} (empty prefix lists return nothing; a denial would say AccessDenied)")
    for fn in (p, p + ".back"):
        if os.path.exists(fn):
            os.remove(fn)


def user_data(c: dict, mode: str, shard: str, workers: int, kind: str, lifetime_s: int, part: str = "all",
              template: str = "userdata_s4.sh", tag: str | None = None) -> str:
    with open(os.path.join(HERE, template)) as f:
        txt = f.read()
    rep = dict(BUCKET=c["bucket"], CODE_PREFIX=c["code_prefix"], RESULTS_PREFIX=c["results_prefix"], BUNDLE=latest_bundle(),
               MODE=mode, SHARD=shard, SHARD_TAG=shard.replace("/", "of"), WORKERS=str(workers), KIND=kind, PART=part,
               LIFETIME_S=str(lifetime_s), TAG=tag or shard.replace("/", "of"), **PINS)
    for k, v in rep.items():
        txt = txt.replace(f"__{k}__", v)
    import re
    left = re.findall(r"__[A-Z_]+__", txt)
    assert not left, f"unfilled placeholders in user-data: {left}"
    return txt


def launch_one(c: dict, mode: str, shard: str, workers: int, kind: str, lifetime_h: float, dry: bool, az: str | None,
               part: str = "all", instance_type: str | None = None, template: str = "userdata_s4.sh",
               market: str = "spot") -> dict:
    """One instance. For mode s2closure `part` selects the closure part (aws/s2_closure.sh: W2 | T1 | O1 | checks | all)
    and names the instance and its log (24 Oct 2026: the closure is spread over several instances, one part each).
    `market` = spot (the configured max price) or on-demand (the spot quota is 512 vCPU = five c7a.24xlarge; the
    on-demand quota another 520, so ten S4b shards run as five spot + five on-demand)."""
    tag = part if (mode == "s2closure" and part != "all") else shard.replace("/", "of")
    ud = user_data(c, mode, shard, workers, kind, int(lifetime_h * 3600), part, template, tag)
    ud_path = os.path.join(HERE, f"userdata_{mode}_{tag}.sh")
    with open(ud_path, "w") as f:
        f.write(ud)
    az = az or c["subnet_order"][0]
    tags = [dict(Key="project", Value="t1"), dict(Key="Job", Value=JOB_TAG), dict(Key="Mode", Value=mode),
            dict(Key="Shard", Value=shard), dict(Key="Part", Value=part), dict(Key="Name", Value=f"{JOB_TAG}-{mode}-{tag}")]
    spec = dict(
        ImageId=c["ami"], InstanceType=instance_type or c["instance_type"], MinCount=1, MaxCount=1,
        SubnetId=c["subnets"][az], SecurityGroupIds=[c["security_group_id"]],
        IamInstanceProfile=dict(Name=c["iam_instance_profile"]),
        InstanceInitiatedShutdownBehavior="terminate",
        MetadataOptions=dict(HttpTokens="required", HttpEndpoint="enabled"),
        BlockDeviceMappings=[dict(DeviceName=c.get("root_device", "/dev/xvda"), Ebs=dict(VolumeSize=int(c.get("root_gb", 30)), VolumeType="gp3", DeleteOnTermination=True))],
        TagSpecifications=[dict(ResourceType="instance", Tags=tags), dict(ResourceType="volume", Tags=tags)],
    )
    if c.get("key_name"):
        spec["KeyName"] = c["key_name"]
    if c.get("spot_max_price") is not None and market == "spot":
        spec["InstanceMarketOptions"] = dict(MarketType="spot", SpotOptions=dict(MaxPrice=str(c["spot_max_price"]), SpotInstanceType="one-time",
                                                                                InstanceInterruptionBehavior="terminate"))
    cli = os.path.join(HERE, f"run_{mode}_{tag}.json")
    with open(cli, "w") as f:
        json.dump(spec, f)
    base_args = ["run-instances", "--cli-input-json", f"file://{cli}", "--user-data", f"file://{ud_path}"]
    if dry:
        try:
            ec2(base_args + ["--dry-run"], c)
            print("[launch] dry run returned without the expected DryRunOperation error")
        except RuntimeError as e:
            ok = "DryRunOperation" in str(e)
            print(f"[launch] dry run {'OK (DryRunOperation: the request would succeed)' if ok else 'FAILED: ' + str(e)[:400]}")
        return dict(dry=True)
    try:
        res = ec2(base_args, c)
        market = "spot" if "InstanceMarketOptions" in spec else "on-demand"
    except RuntimeError as e:
        capacity = any(s in str(e) for s in ("InsufficientInstanceCapacity", "SpotMaxPriceTooLow", "MaxSpotInstanceCountExceeded", "Unsupported"))
        if "InstanceMarketOptions" in spec and c.get("on_demand_fallback") and capacity:
            print(f"[launch] spot refused ({str(e)[:160]}); on-demand fallback")
            spec.pop("InstanceMarketOptions", None)
            with open(cli, "w") as f:
                json.dump(spec, f)
            res = ec2(base_args, c)
            market = "on-demand"
        else:
            raise
    inst = res["Instances"][0]
    rec = dict(instance_id=inst["InstanceId"], mode=mode, shard=shard, part=part, kind=kind, workers=workers, market=market,
               launched_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(), lifetime_h=lifetime_h,
               instance_type=instance_type or c["instance_type"], region=c["region"],
               az=inst.get("Placement", {}).get("AvailabilityZone"), bundle=latest_bundle())
    s = state(); s["instances"].append(rec); save_state(s)
    print(f"[launch] {rec}")
    return rec


def status(c: dict) -> dict:
    res = ec2(["describe-instances", "--filters", f"Name=tag:Job,Values={JOB_TAG}"], c)
    rows, total = [], 0.0
    now = _dt.datetime.now(_dt.timezone.utc)
    for r in res.get("Reservations", []):
        for i in r["Instances"]:
            tags = {t["Key"]: t["Value"] for t in i.get("Tags", [])}
            st = i["State"]["Name"]
            launch = _dt.datetime.fromisoformat(i["LaunchTime"].replace("Z", "+00:00"))
            hours = (now - launch).total_seconds() / 3600.0 if st in ("running", "pending", "shutting-down") else None
            price = c.get("spot_price_estimate_usd_h") if i.get("InstanceLifecycle") == "spot" else c.get("on_demand_usd_h")
            if i["InstanceType"] != c["instance_type"]:                 # a probe on a small instance: scale by vCPU count
                price = (price or 0.0) * max(1, i.get("CpuOptions", {}).get("CoreCount", 1) * i.get("CpuOptions", {}).get("ThreadsPerCore", 1)) / 96.0
            spend = (hours or 0.0) * (price or 0.0)
            total += spend
            rows.append(dict(id=i["InstanceId"], state=st, type=i["InstanceType"], lifecycle=i.get("InstanceLifecycle", "on-demand"),
                             az=i.get("Placement", {}).get("AvailabilityZone"), mode=tags.get("Mode"), shard=tags.get("Shard"),
                             part=tags.get("Part"), launched=i["LaunchTime"], hours=None if hours is None else round(hours, 2),
                             est_usd=round(spend, 2)))
    for row in rows:
        print(row)
    prev = {}
    if os.path.exists(SPEND_PATH):
        with open(SPEND_PATH) as f:
            prev = json.load(f)
    rec = dict(utc=now.isoformat(), instances=rows, est_running_usd=round(total, 2), closed_usd=prev.get("closed_usd", 0.0),
               closed_log=prev.get("closed_log", []))
    with open(SPEND_PATH, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"[status] running-instance spend so far about USD {total:.2f} (+ closed USD {rec['closed_usd']:.2f})")
    return rec


def close_spend(c: dict, usd: float, note: str):
    """Record a finished instance's spend (hours × price, or the Cost Explorer figure when known)."""
    prev = {}
    if os.path.exists(SPEND_PATH):
        with open(SPEND_PATH) as f:
            prev = json.load(f)
    prev["closed_usd"] = round(prev.get("closed_usd", 0.0) + usd, 2)
    prev.setdefault("closed_log", []).append(dict(utc=_dt.datetime.now(_dt.timezone.utc).isoformat(), usd=usd, note=note))
    with open(SPEND_PATH, "w") as f:
        json.dump(prev, f, indent=1)
    print(f"[spend] closed total USD {prev['closed_usd']:.2f}")


def pull(c: dict, what: str):
    if what == "s4":
        dst = os.path.join(J, "results", "s4")
        src = f"s3://{c['bucket']}/{c['results_prefix']}/results/s4"
    else:
        dst = os.path.join(J, "results", "s2_aws")
        src = f"s3://{c['bucket']}/{c['results_prefix']}/results/s2"
    os.makedirs(dst, exist_ok=True)
    out = subprocess.run(["aws", "--profile", c["profile"], "--region", c["s3_region"], "s3", "sync", src, dst, "--quiet"],
                         capture_output=True, text=True)
    print("[pull] rc", out.returncode, out.stderr.strip()[:300])
    n = sum(len(fs) for _, _, fs in os.walk(dst))
    print(f"[pull] {dst}: {n} files")
    logs = f"s3://{c['bucket']}/{c['results_prefix']}/logs/"
    out = subprocess.run(["aws", "--profile", c["profile"], "--region", c["s3_region"], "s3", "ls", logs], capture_output=True, text=True)
    print("[pull] logs:", out.stdout.strip()[:800])


def stop(c: dict, instance: str | None, all_: bool):
    ids = []
    if instance:
        ids = [instance]
    elif all_:
        res = ec2(["describe-instances", "--filters", f"Name=tag:Job,Values={JOB_TAG}", "Name=instance-state-name,Values=pending,running"], c)
        ids = [i["InstanceId"] for r in res.get("Reservations", []) for i in r["Instances"]]
    if not ids:
        print("[stop] nothing to stop"); return
    ec2(["terminate-instances", "--instance-ids"] + ids, c)
    print(f"[stop] terminated {ids}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None, help="another region's config, e.g. aws/s4_aws_usw2.json (default aws/s4_aws.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bundle"); sub.add_parser("probe")
    la = sub.add_parser("launch")
    la.add_argument("--mode", required=True, choices=["s2closure", "s4a", "s4b"])
    la.add_argument("--shards", type=int, default=1)
    la.add_argument("--shard-start", type=int, default=0)
    la.add_argument("--shard-end", type=int, default=None, help="launch shards [shard-start, shard-end) of --shards (default: all)")
    la.add_argument("--market", default="spot", choices=["spot", "on-demand"])
    la.add_argument("--workers", type=int, default=96)
    la.add_argument("--kind", default="all", choices=["cv", "rec", "all"])
    la.add_argument("--lifetime-h", type=float, default=12.0)
    la.add_argument("--az", default=None)
    la.add_argument("--part", default="all", choices=["all", "W2", "T1", "O1", "W2-rev", "T1-rev", "O1-rev", "checks", "nodes", "validators", "profiles"],
                    help="s2closure only: which part of aws/s2_closure.sh this instance runs")
    la.add_argument("--dry-run", action="store_true")
    pc = sub.add_parser("probe-core", help="throughput probe on a small instance: thread count, one decision task alone, two in parallel")
    pc.add_argument("--instance-type", default="c7a.2xlarge")
    pc.add_argument("--lifetime-h", type=float, default=2.0)
    pc.add_argument("--az", default=None)
    pc.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    pl = sub.add_parser("pull"); pl.add_argument("--what", default="s4", choices=["s4", "s2"])
    cs = sub.add_parser("close-spend"); cs.add_argument("--usd", type=float, required=True); cs.add_argument("--note", required=True)
    stp = sub.add_parser("stop"); stp.add_argument("--instance", default=None); stp.add_argument("--all", action="store_true")
    a = ap.parse_args()
    c = cfg(a.config)
    if a.cmd == "bundle":
        bundle(c)
    elif a.cmd == "probe":
        probe(c)
    elif a.cmd == "launch":
        if a.mode == "s2closure" or (a.mode == "s4a" and a.shards == 1):
            launch_one(c, a.mode, "1/1", a.workers, a.kind, a.lifetime_h, a.dry_run, a.az, part=a.part, market=a.market)
        else:
            # s4b: disjoint hash shards of one queue. s4a with K > 1: the same deterministic path on K hosts, each
            # running its hash shard of every batch and waiting for the others at the barriers (s4.py s4a --shard)
            order = c["subnet_order"]
            for i in range(a.shard_start, a.shards if a.shard_end is None else a.shard_end):
                launch_one(c, a.mode, f"{i}/{a.shards}", a.workers, a.kind, a.lifetime_h, a.dry_run,
                           a.az or order[i % len(order)], market=a.market)
    elif a.cmd == "probe-core":
        tag = "probe" + _dt.datetime.now(_dt.timezone.utc).strftime("%H%M")
        launch_one(c, "probe", tag, 1, "all", a.lifetime_h, a.dry_run, a.az, part="all", instance_type=a.instance_type,
                   template="userdata_probe.sh")
    elif a.cmd == "status":
        status(c)
    elif a.cmd == "pull":
        pull(c, a.what)
    elif a.cmd == "close-spend":
        close_spend(c, a.usd, a.note)
    elif a.cmd == "stop":
        stop(c, a.instance, a.all)


if __name__ == "__main__":
    main()

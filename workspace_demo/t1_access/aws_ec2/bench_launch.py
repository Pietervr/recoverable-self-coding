"""Ledger row 23 (revision 2): launch ONE attempt of the EC2 benchmark (spot c7a.24xlarge, us-west-2) from the Mac.

    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2 --dry-run   # EC2 authorization only
    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2             # one attempt
    python3 bench_reaper.py --run b2      # MUST run beside every attempt: terminal proof, accounting, fallback terminate

COST CEILING, ENFORCED CUMULATIVELY (USD 28.00 for row 23, all attempts together). One attempt's worst case is
(lifetime + reaper grace) x (spot MaxPrice 1.20 + ancillaries 0.0094/h: 40 GB gp3 0.0044 + public IPv4 0.005) + 0.10 S3.
A reconciled attempt is charged its observed running hours (launch to first observed shutting-down/terminated, an
upper bound) at the same rates; an unreconciled one at its worst case. A new attempt gets the largest lifetime the
remaining ceiling admits (at most 77,400 s = 21.5 h -> USD 26.30 worst) and is refused when that lifetime cannot hold
setup + one 68,400 s fit + the upload reserve (72,300 s).

DUPLICATES. Refused while the run has an unreconciled attempt, a non-terminated instance tagged run=<run>, or objects
under the attempt's result prefix. The attempt (client token, intent) is written to runs/<run>/attempts.json BEFORE the
API call; RunInstances carries that client token, so a retried or ambiguous call cannot create a second instance, and
an ambiguous response is reconciled by describing instances with that token."""
import argparse, hashlib, json, os, subprocess, sys, time, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE, REGION, BUCKET = "xtenure-read", "us-west-2", "xtenure-cself-pvr-usw2"
ITYPE, MAXPRICE, ROLE = "c7a.24xlarge", 1.20, "xtenure-ec2-t1-worker"
ANC_H, S3_FIXED, GRACE_S, CEILING = 0.0094, 0.10, 600, 28.00
MAX_LIFE_S, MIN_LIFE_S = 77400, 72300
AMI_PARAM = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
FILES = {"manifest_A.json": "bench/manifest_A.json", "manifest_B.json": "bench/manifest_B.json", "plan.json": "bench/plan.json",
         "attest.py": "attest.py", "row6_lengau_panel.py": "../chpc/row6_lengau_panel.py"}
ROW6_SHA = "76e5670f348032193cd4425b188be09aef8037af69c5ac5b9af8198e6e2e3327"


def aws(*args, check=True):
    p = subprocess.run(["aws", "--profile", PROFILE, "--region", REGION, *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"aws {' '.join(args[:2])}: {p.stderr.strip()}")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def worst_usd(seconds):
    return (seconds / 3600) * (MAXPRICE + ANC_H) + S3_FIXED


def charged(a):
    if a.get("state") == "no instance":
        return 0.0
    if a.get("terminal", {}).get("billed_s") is not None:
        return worst_usd(a["terminal"]["billed_s"])
    return worst_usd(a["lifetime_s"] + GRACE_S)


def ledger_path(run):
    return os.path.join(HERE, "runs", run, "attempts.json")


def load(run):
    p = ledger_path(run)
    return json.load(open(p)) if os.path.exists(p) else {"run": run, "ceiling_usd": CEILING, "attempts": []}


def save(run, led):
    p = ledger_path(run); os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"; json.dump(led, open(tmp, "w"), indent=1); os.replace(tmp, p)


def find_instances(**filters):
    fl = [f"Name={k},Values={v}" for k, v in filters.items()]
    out = json.loads(aws("ec2", "describe-instances", "--filters", *fl, "--output", "json").stdout)
    return [i for r in out["Reservations"] for i in r["Instances"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarball", required=True); ap.add_argument("--run", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    led = load(a.run)
    for prev in led["attempts"]:
        if prev.get("state") not in ("no instance", "reconciled"):
            sys.exit(f"REFUSED: attempt {prev['attempt']} is {prev.get('state')} - run bench_reaper.py --run {a.run} first")
    live = [i for i in find_instances(**{"tag:run": a.run}) if i["State"]["Name"] != "terminated"]
    if live:
        sys.exit(f"REFUSED: instance(s) tagged run={a.run} not terminated: {[i['InstanceId'] for i in live]}")
    spent = sum(charged(x) for x in led["attempts"])
    life = min(MAX_LIFE_S, int(((CEILING - spent - S3_FIXED) / (MAXPRICE + ANC_H)) * 3600) - GRACE_S)
    if life < MIN_LIFE_S:
        sys.exit(f"REFUSED: USD {spent:.2f} charged to row 23 leaves a {life} s lifetime, below the {MIN_LIFE_S} s one attempt needs")
    n = len(led["attempts"]) + 1
    prefix = f"results/t1_access/aws_bench/{a.run}/attempt_{n}/"
    if aws("s3", "ls", f"s3://{BUCKET}/{prefix}", check=False).stdout.strip():
        sys.exit(f"REFUSED: s3://{BUCKET}/{prefix} is not empty")
    tgz = os.path.expanduser(a.tarball)
    paths = {"t1_toolchain_lengau.tgz": tgz, **{k: os.path.join(HERE, v) for k, v in FILES.items()}}
    sums = {k: sha256(p) for k, p in paths.items()}
    assert sums["row6_lengau_panel.py"] == ROW6_SHA, "row 6 panel script is not the one Lengau ran"
    sumtext = "\n".join(f"{v}  {k}" for k, v in sums.items())
    ud = (open(os.path.join(HERE, "bench_userdata.sh")).read().replace("__RUN__", a.run).replace("__ATTEMPT__", str(n))
          .replace("__LIFETIME_S__", str(life)).replace("__SUMS__", sumtext))
    assert not any(t in ud for t in ("__RUN__", "__ATTEMPT__", "__LIFETIME_S__", "__SUMS__")), "unfilled placeholder"
    udp = os.path.join(HERE, "runs", a.run, f"userdata_attempt{n}.sh"); os.makedirs(os.path.dirname(udp), exist_ok=True)
    open(udp, "w").write(ud)
    ami = json.loads(aws("ssm", "get-parameters", "--names", AMI_PARAM, "--output", "json").stdout)["Parameters"][0]["Value"]
    token = f"t1-{a.run}-{n}-{uuid.uuid4().hex[:12]}"
    tags = [{"ResourceType": rt, "Tags": [{"Key": "project", "Value": "t1"}, {"Key": "row", "Value": "23"}, {"Key": "run", "Value": a.run},
                                            {"Key": "attempt", "Value": str(n)}, {"Key": "Name", "Value": f"t1-bench-{a.run}-{n}"}]}
            for rt in ("instance", "volume")]
    args = ["ec2", "run-instances", "--image-id", ami, "--instance-type", ITYPE, "--count", "1", "--client-token", token,
            "--iam-instance-profile", f"Name={ROLE}",
            "--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
                "MaxPrice": f"{MAXPRICE:.2f}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}}),
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": 40, "VolumeType": "gp3", "DeleteOnTermination": True}}]),
            "--metadata-options", "HttpTokens=required",
            "--tag-specifications", json.dumps(tags), "--user-data", f"file://{udp}", "--output", "json"]
    print(f"attempt {n}: lifetime {life} s, worst USD {worst_usd(life + GRACE_S):.2f}, prior charged USD {spent:.2f}, AMI {ami}")
    if a.dry_run:
        p = aws(*args, "--dry-run", check=False)
        ok = "DryRunOperation" in p.stderr
        print("DRY RUN:", "EC2 authorization OK (S3 uploads not exercised)" if ok else p.stderr.strip())
        return 0 if ok else 1
    for k, p in paths.items():
        aws("s3", "cp", p, f"s3://{BUCKET}/code/t1_access/aws_bench/{a.run}/{k}", "--only-show-errors")
    att = dict(attempt=n, state="intent", client_token=token, lifetime_s=life, max_price=MAXPRICE, type=ITYPE, ami=ami,
               sha256=sums, results=f"s3://{BUCKET}/{prefix}", intent_at=time.time())
    led["attempts"].append(att); save(a.run, led)
    try:
        out = json.loads(aws(*args).stdout)
        inst = out["Instances"][0]
    except Exception as e:
        found = find_instances(**{"client-token": token})
        if not found:
            att.update(state="no instance", error=str(e)[:500]); save(a.run, led)
            sys.exit(f"launch failed, no instance under token {token}: {e}")
        inst = found[0]; att["ambiguous_response"] = str(e)[:500]
    att.update(state="launched", instance=inst["InstanceId"], launch_time=inst["LaunchTime"])
    save(a.run, led)
    print(json.dumps(att, indent=1))
    print(f"NOW RUN: python3 {os.path.join(HERE, 'bench_reaper.py')} --run {a.run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

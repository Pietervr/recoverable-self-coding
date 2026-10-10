"""Ledger row 23: launch the EC2 parity and timing benchmark (ONE spot c7a.24xlarge, us-west-2) from the Mac.

    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b1 --dry-run   # permissions only
    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b1             # uploads + launches

Uses the AWS CLI under the profile xtenure-read. Ceilings: spot one-time at MaxPrice USD 1.20/h (live price ~0.86),
instance-initiated shutdown = terminate, the user-data's own shutdown at 23.5 h -> at most ~USD 28 even at the cap.
Writes launch_<run>.json beside this file (instance id, AMI, price cap, tarball sha256)."""
import argparse, hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE, REGION = "xtenure-read", "us-west-2"
BUCKET = "xtenure-cself-pvr-usw2"
ITYPE, MAXPRICE = "c7a.24xlarge", "1.20"
ROLE = "xtenure-ec2-t1-worker"
AMI_PARAM = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"


def aws(*args, check=True):
    cmd = ["aws", "--profile", PROFILE, "--region", REGION, *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd[:6])} ...\n{p.stderr.strip()}")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarball", required=True); ap.add_argument("--run", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tgz = os.path.expanduser(a.tarball); tsha = sha256(tgz)
    print(f"tarball {tgz} {os.path.getsize(tgz)/2**20:.0f} MiB sha256 {tsha}")
    ud = open(os.path.join(HERE, "bench_userdata.sh")).read().replace("__RUN__", a.run).replace("__TGZ_SHA__", tsha)
    udp = os.path.join(HERE, f"userdata_{a.run}.sh"); open(udp, "w").write(ud)
    ami = json.loads(aws("ssm", "get-parameters", "--names", AMI_PARAM, "--output", "json").stdout)["Parameters"][0]["Value"]
    print(f"AMI {ami}")
    if not a.dry_run:
        aws("s3", "cp", tgz, f"s3://{BUCKET}/code/t1_access/aws_bench/{a.run}/t1_toolchain_lengau.tgz", "--only-show-errors")
        aws("s3", "cp", os.path.join(HERE, "..", "chpc", "row6_lengau_panel.py"),
            f"s3://{BUCKET}/code/t1_access/aws_bench/{a.run}/row6_lengau_panel.py", "--only-show-errors")
        print("tarball and row 6 panel script uploaded")
    tags = [{"ResourceType": rt, "Tags": [{"Key": "project", "Value": "t1"}, {"Key": "row", "Value": "23"},
                                            {"Key": "Name", "Value": f"t1-bench-{a.run}"}]} for rt in ("instance", "volume")]
    args = ["ec2", "run-instances", "--image-id", ami, "--instance-type", ITYPE, "--count", "1",
            "--iam-instance-profile", f"Name={ROLE}",
            "--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
                "MaxPrice": MAXPRICE, "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}}),
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": 40, "VolumeType": "gp3",
                                                                                      "DeleteOnTermination": True}}]),
            "--metadata-options", "HttpTokens=required",
            "--tag-specifications", json.dumps(tags), "--user-data", f"file://{udp}", "--output", "json"]
    if a.dry_run:
        p = aws(*args, "--dry-run", check=False)
        ok = "DryRunOperation" in p.stderr
        print("DRY RUN:", "permissions OK (DryRunOperation)" if ok else p.stderr.strip())
        return 0 if ok else 1
    out = json.loads(aws(*args).stdout)
    iid = out["Instances"][0]["InstanceId"]
    rec = dict(run=a.run, instance=iid, ami=ami, type=ITYPE, max_price=MAXPRICE, tarball_sha256=tsha,
               launched=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               results=f"s3://{BUCKET}/results/t1_access/aws_bench/{a.run}/")
    json.dump(rec, open(os.path.join(HERE, f"launch_{a.run}.json"), "w"), indent=1)
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

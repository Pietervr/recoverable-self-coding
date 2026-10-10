"""Row 19 screen on EC2, production stage 2: admit and dispatch ONE production instance of a partition epoch.

    python3 prod_launch.py --epoch 1 --partition ../chpc/row19_partition_e1.json --manifest prod/manifest_e1.json \
        --snapshot ../chpc/results/row19_screen --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz [--dry-run]
    python3 prod_launch.py --epoch 1 --recover      # re-issue an unresolved attempt's SAME request

Under the run lock (shared with the reaper's ledger writes): refuses while any attempt is 'intent' or 'ambiguous' (an
unresolved launch keeps its coordinates and its worst-case charge); requires a fresh whole-role refit receipt in the
snapshot (<= 2,700 s); validates the partition and the operational manifest; allocates up to 72 work coordinates from
the block (prod_authority.allocate) plus 4 sentinels; checks both envelopes with this attempt's worst case; writes the
immutable plan and request and the attempt (state intent, coordinates owned) BEFORE RunInstances; dispatches through
the reviewed launcher's issue/resolve (same token on replay, single-attempt first dispatch) and starts the reaper.
Several production instances may run at once; each one's coordinates are disjoint by construction."""
import argparse, glob, json, os, sys, time, uuid
import bench_launch as L
import prod_authority as PA

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(T1, "chpc"))
import row19_partition as RP

PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
RECEIPT_MAX_AGE_S = 2700


def snapshot_state(snapshot, part):
    """(completed coordinates, Lengau-completed coordinates outside the block, receipt) from the status tool's latest
    FRESH refit snapshot; raises when the newest whole-role receipt is older than the admission limit or alarmed."""
    recs = sorted(glob.glob(os.path.join(snapshot, "receipts", "watch_refit_*.json")))
    if not recs:
        raise ValueError("no refit receipt in the snapshot")
    w = json.load(open(recs[-1])); age = time.time() - float(w.get("time", 0))
    if age > RECEIPT_MAX_AGE_S or w.get("alarms") or not w.get("fresh", True):
        raise ValueError(f"the newest refit receipt {os.path.basename(recs[-1])} is {age:.0f} s old or not clean")
    root = os.path.join(snapshot, "live", "refit", "root")
    done = set()
    for p in glob.glob(os.path.join(root, "records", "rep*", "rec_*.json")):
        done.add((int(os.path.basename(os.path.dirname(p))[3:]), int(os.path.basename(p)[4:7])))
    lengau = {c for c in done if not RP.blocked(part, *c)}
    return done, lengau, os.path.basename(recs[-1])


def admit(a):
    run = PA.run_name(a.epoch); led = L.load(run)
    open_ = [x for x in led["attempts"] if x.get("state") in ("intent", "ambiguous")]
    if open_:
        sys.exit(f"REFUSED: attempt {open_[-1]['attempt']} is {open_[-1]['state']} - python3 prod_launch.py --epoch {a.epoch} --recover")
    man_prod = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))
    part = RP.load(a.partition, man_prod, PROD_SHA)
    if part["epoch"] != a.epoch:
        sys.exit(f"REFUSED: partition epoch {part['epoch']} is not --epoch {a.epoch}")
    opm = json.load(open(a.manifest))
    if (opm.get("ec2_production") or {}).get("epoch") != a.epoch or opm["ec2_production"]["derived_from_sha256"] != PROD_SHA:
        sys.exit("REFUSED: the operational manifest is not this epoch's derivation of 43b75f94")
    try:
        done, lengau, receipt = snapshot_state(a.snapshot, part)
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    n_work = PA.WORKERS_PER_INSTANCE - PA.SENTINELS_PER_ATTEMPT
    work = PA.allocate(part, led, done, n_work)
    if not work:
        sys.exit("REFUSED: the partition block has no free coordinate left")
    n = max([x["attempt"] for x in led["attempts"]], default=0) + 1
    token = f"t1-{run}-{n}-{uuid.uuid4().hex[:12]}"
    sent = PA.sentinels(lengau, token)
    life = int(opm["ec2_production"]["lifetime_s"]); worst = L.worst_usd(life + L.GRACE_S + L.RESERVE_S)
    why = PA.budget_problem(led, run, worst)
    if why:
        sys.exit(f"REFUSED: {why}")
    attempt_id = f"ec2-e{a.epoch}-a{n}"
    plan = {"job": n, "attempt_id": attempt_id, "epoch": a.epoch, "partition_sha256": RP.sha_file(a.partition),
            "slots": [dict(slot=k, rep=r, indices=[i], role="work") for k, (r, i) in enumerate(work)]
                     + [dict(slot=len(work) + k, rep=r, indices=[i], role="sentinel") for k, (r, i) in enumerate(sent)]}
    d = L.run_dir(run); planp = os.path.join(d, f"plan_attempt{n}.json")
    json.dump(plan, open(planp, "w"), indent=1)
    files = {"t1_toolchain_lengau.tgz": os.path.expanduser(a.tarball), "manifest_prod.json": a.manifest, "plan.json": planp,
             "attest.py": os.path.join(HERE, "attest.py")}
    sums = {k: L.sha256(p) for k, p in files.items()}
    if sums["t1_toolchain_lengau.tgz"] != L.PINS["t1_toolchain_lengau.tgz"]:
        sys.exit("REFUSED: the toolchain tarball is not the pinned bytes")
    ud = (open(os.path.join(HERE, "prod_userdata.sh")).read().replace("__RUN__", run).replace("__ATTEMPT__", str(n))
          .replace("__LIFETIME_S__", str(life)).replace("__ATTEMPT_ID__", attempt_id)
          .replace("__SUMS__", "\n".join(f"{v}  {k}" for k, v in sums.items())))
    if any(t in ud for t in ("__RUN__", "__ATTEMPT__", "__LIFETIME_S__", "__ATTEMPT_ID__", "__SUMS__")):
        sys.exit("REFUSED: unfilled user-data placeholder")
    udp = os.path.join(d, f"userdata_attempt{n}.sh"); open(udp, "w").write(ud)
    print(f"{attempt_id}: {len(work)} work coordinates (indices {work[0][1]}..{work[-1][1]}), {len(sent)} sentinels, lifetime {life} s, "
          f"worst USD {worst:.2f}; receipt {receipt}")
    ami = json.loads(L.aws("ssm", "get-parameters", "--names", L.AMI_PARAM, "--output", "json").stdout)["Parameters"][0]["Value"]
    tags = [{"ResourceType": rt, "Tags": [{"Key": "project", "Value": "t1"}, {"Key": "row", "Value": "19-ec2"}, {"Key": "run", "Value": run},
                                            {"Key": "attempt", "Value": str(n)}, {"Key": "Name", "Value": attempt_id}]} for rt in ("instance", "volume")]
    args = ["ec2", "run-instances", "--image-id", ami, "--instance-type", L.ITYPE, "--count", "1", "--client-token", token,
            "--placement", f"AvailabilityZone={L.AZ}", "--iam-instance-profile", f"Name={L.ROLE}",
            "--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
                "MaxPrice": f"{L.MAXPRICE:.2f}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}}),
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": 60, "VolumeType": "gp3", "DeleteOnTermination": True}}]),
            "--metadata-options", "HttpTokens=required", "--tag-specifications", json.dumps(tags), "--user-data", f"file://{udp}", "--output", "json"]
    if a.dry_run:
        try:
            L.aws(*args, "--dry-run")
        except L.AwsError as e:
            print("DRY RUN:", "EC2 authorization OK" if e.code == "DryRunOperation" else str(e)); return 0 if e.code == "DryRunOperation" else 1
        return 1
    for k, p in files.items():
        L.aws("s3", "cp", p, f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run}/attempt_{n}/{k}", "--only-show-errors", timeout=1800)
    reqp = os.path.join(d, f"request_attempt{n}.json")
    json.dump(dict(client_token=token, args=args, userdata_sha256=L.sha256(udp), sha256=sums), open(reqp, "w"), indent=1)
    att = dict(attempt=n, sequence=n, attempt_id=attempt_id, state="intent", client_token=token, request=reqp, lifetime_s=life,
               max_price=L.MAXPRICE, type=L.ITYPE, ami=ami, plan=planp, plan_sha256=L.sha256(planp),
               coordinates=[list(c) for c in work], sentinels=[list(c) for c in sent], ingestion="pending",
               results=f"s3://{L.BUCKET}/results/t1_access/aws_bench/{run}/attempt_{n}/", intent_at=time.time(), receipt=receipt)
    led["attempts"].append(att); L.save(run, led)
    return L.finish(run, led, att, fresh=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", type=int, required=True); ap.add_argument("--partition"); ap.add_argument("--manifest")
    ap.add_argument("--snapshot", default=os.path.join(T1, "chpc", "results", "row19_screen")); ap.add_argument("--tarball")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--recover", action="store_true")
    a = ap.parse_args(); run = PA.run_name(a.epoch)
    try:
        with L.run_lock(run):
            if a.recover:
                led = L.load(run)
                att = next((x for x in reversed(led["attempts"]) if x.get("state") in ("intent", "ambiguous")), None)
                if att is None:
                    sys.exit("nothing to recover")
                return L.finish(run, led, att, fresh=False)
            if not (a.partition and a.manifest and a.tarball):
                sys.exit("--partition, --manifest and --tarball are required to admit an instance")
            return admit(a)
    except BlockingIOError:
        sys.exit(f"REFUSED: another launcher or reaper holds runs/{run}/.lock")


if __name__ == "__main__":
    sys.exit(main())

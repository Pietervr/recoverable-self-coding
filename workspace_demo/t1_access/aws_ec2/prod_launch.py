"""Row 19 screen on EC2: admit and dispatch ONE instance of a production epoch or of a predeclared qualification part
(Codex RSC f3dd3d7; repaired for Codex RSC 0483db4 V10-1, V10-2, V10-6, V10-7, V10-8). Mac only.

    python3 prod_launch.py --contract Q1 --epoch 1 --partition ../chpc/row19_partition_e1.json --manifest prod/manifest_q1_e1.json \
        --snapshot ../chpc/results/row19_screen --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz [--dry-run]
    python3 prod_launch.py --contract production --epoch 1 ...      # only after the reviewed production release
    python3 prod_launch.py --contract production --epoch 1 --recover # re-issue an unresolved attempt's SAME request (STOP-checked)

Admission, under the GLOBAL authority lock and the run lock (shared with the reaper), refuses unless ALL hold:
  STOP     no STOP anywhere: the run's and the global local STOP (runs/STOP), the run's and the global S3 STOP (bounded
           30 s calls; an API failure is not proof of absence and refuses), the Lengau screen root STOP and ec2/HOLD in the
           pulled snapshot. Recovery checks the same before re-issuing.
  release  ec2_release_state.json: Q1/Q2 need row 23's declared success (pinned report) AND qualification permitted with
           the owner's acceptance of the per-part USD ceilings; production needs the reviewed release certificate (outcome
           RELEASE). Q2 also needs a reconciled Q1 attempt.
  inputs   the partition is the one the LATEST adopted controls (chpc/row19_screen_controls.json) pin, and the pulled root
           carries its serialized activation proof; the operational manifest is the exact derivation of 43b75f94 for this
           epoch and contract (row19_ec2_state.operational_problem).
  receipt  the newest whole-role refit receipt is a FRESH PRODUCTION one (explicit true flags, schema, role), alarm-free,
           finite, not in the future, <= 2,700 s old; it binds the snapshot's EC2 state (ec2.bound = row19_ec2_state.bound of
           the snapshot root) AND the authority inventory this Mac last sealed, at the CURRENT generation - so a newly
           journaled attempt refuses until the inventory is copied to Lengau and a new receipt taken. Completion comes from the
           receipt's own bound verifier document (record ok), not from file names.
  budget   prod_authority.budget_problem: global production envelope across all epochs/qualification/retries, the cumulative
           USD 3,000 cap over baseline + every run, the per-part qualification ceiling.
Then: global sequence reserved, the immutable plan (bound to partition, operational manifest, activation, sequence and the
contract) and request written, the attempt journaled 'intent' BEFORE RunInstances, the generation bumped and a new
inventory sealed; dispatch through the reviewed issue/resolve and the reaper.

Plans by contract (row19_ec2_state.CONTRACTS; QUALIFICATION_PLAN.md): production = up to 72 block coordinates in the fixed
order + 4 sentinels; Q1 = 48 block coordinates (index 199 and 198 of reps 3..26, owned) + 24 Lengau-completed
coordinates (index 1 and 2 of reps 3..14, duplicates) + 4 sentinels = 76; Q2 = the 24 coordinates index 199 of reps 3..26
recomputed on a c7a.12xlarge at cap 0.70 (duplicates; Q1 owns them).

REVISION 3 (Codex RSC 3dc0daf R1-1, R1-3, R1-5, R1-7). STOP absence is accepted ONLY when S3 answers that the object does
not exist (HeadObject 404 / NoSuchKey / NotFound); every other outcome - credentials, configuration, connection, timeout,
throttling, any unparsed failure - refuses admission and recovery. The activation proof must be canonical with its controls
lineage intact (row19_partition.activation_problem with the current controls). The snapshot root's registered EC2 artifacts
and installed inventory are rechecked now (row19_ec2_state.current_problems), not trusted from the receipt's metadata. An
admission refuses while a benchmark attempt is unresolved/running or an unresolved attempt was made in another region
(prod_authority.exclusion_problem); every attempt and request records its region and zone, and recovery refuses an attempt
of another region.

REVISION 4 (Codex RSC 299f4b7 R2-1, R2-2, R2-3). Controls are read only through row19_partition.adopted_controls (the
current adopted, tracked, unmodified bytes): a later unadopted candidate refuses here as on Lengau. STOP (every source) and
the receipt's freshness are checked AGAIN after the uploads, immediately before the attempt is journaled and RunInstances is
issued, and before every issue and re-issue of the saved request (dispatch_guard, passed to bench_launch.finish): a STOP
written during staging, or a receipt that aged past 2,700 s, dispatches nothing - a never-issued attempt is withdrawn
('rejected', no instance can exist), an issued one stays ambiguous and funded. After the dispatch outcome (launched /
rejected / ambiguous) the inventory is sealed again, so every lifecycle state is an installable generation."""
import argparse, glob, json, math, os, sys, time, uuid
import bench_launch as L
import prod_authority as PA

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(T1, "chpc"))
import row19_partition as RP
import row19_ec2_state as ES

PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
RECEIPT_MAX_AGE_S = 2700
WATCH_SCHEMA = "row19-screen-watch-1"
Q1_BLOCK = [(r, i) for i in (199, 198) for r in range(3, 27)]
Q1_LENGAU = [(r, i) for r in range(3, 15) for i in (1, 2)]
Q2_REPEAT = [(r, 199) for r in range(3, 27)]


def s3_stop_key(run=None):
    return f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run + '/' if run else ''}STOP"


ABSENT_CODES = ("404", "NoSuchKey", "NotFound")
MODE = "canonical"                                                        # tests alone set "sandbox"


def s3_stop_present(key):
    """True when the STOP object exists, False ONLY when S3 proves it absent (HeadObject 404/NoSuchKey/NotFound); raises
    L.AwsError for every other outcome (R1-5: no unproved absence)."""
    bucket, _, k = key[len("s3://"):].partition("/")
    try:
        L.aws("s3api", "head-object", "--bucket", bucket, "--key", k, timeout=30)
        return True
    except L.AwsError as e:
        if e.code in ABSENT_CODES:
            return False
        raise


def stop_problem(run, snapshot):
    """Every STOP source; anything but a proved absence on S3 refuses (fail closed)."""
    found = [p for p in (os.path.join(L.run_dir(run), "STOP"), os.path.join(PA.HERE, "runs", "STOP"),
                         os.path.join(snapshot, "live", "refit", "root", "STOP"),
                         os.path.join(snapshot, "live", "refit", "root", "ec2", "HOLD")) if os.path.exists(p)]
    for key in (s3_stop_key(run), s3_stop_key()):
        try:
            if s3_stop_present(key):
                found.append(key)
        except L.AwsError as e:
            return f"the S3 STOP check did not prove absence ({e.code or 'no service code'}: {str(e)[:160]})"
        except Exception as e:
            return f"the S3 STOP check failed ({type(e).__name__}: {e})"
    return f"STOP/HOLD in force ({found})" if found else ""


def snapshot_state(snapshot, part, now=None):
    """(Lengau-verified completed coordinates, receipt name, receipt) from the newest whole-role refit receipt, strictly."""
    now = time.time() if now is None else now
    recs = sorted(glob.glob(os.path.join(snapshot, "receipts", "watch_refit_*.json")))
    if not recs:
        raise ValueError("no refit receipt in the snapshot")
    w = json.load(open(recs[-1])); t = w.get("time")
    if w.get("schema") != WATCH_SCHEMA or w.get("role") != "refit" or w.get("fresh") is not True or w.get("production") is not True:
        raise ValueError(f"{os.path.basename(recs[-1])} is not a fresh production refit receipt")
    if w.get("alarms") != []:
        raise ValueError(f"{os.path.basename(recs[-1])} carries alarms or no alarm list")
    if not (isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t)) or t > now + 60 or now - t > RECEIPT_MAX_AGE_S:
        raise ValueError(f"{os.path.basename(recs[-1])}: time {t!r} not finite, in the future or older than {RECEIPT_MAX_AGE_S} s")
    b = w.get("bound") or {}
    vp = os.path.join(snapshot, "receipts", b.get("verify_file") or "-")
    if not os.path.exists(vp) or L.sha256(vp) != b.get("verify_file_sha256"):
        raise ValueError("the receipt's bound verifier document is missing or not its bytes")
    units = json.load(open(vp)).get("units") or {}
    done = {tuple(int(x) for x in k.split("/")) for k, v in units.items() if (v.get("record") or {}).get("ok")}
    root = os.path.join(snapshot, "live", "refit", "root")
    if (w.get("ec2") or {}).get("bound") != ES.bound(root):
        raise ValueError("the receipt's EC2 binding is not the snapshot root's")
    cur = ES.current_problems(root, json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json"))), require=True)
    if cur:                                                                  # R1-3: the artifacts as they are now
        raise ValueError(f"the snapshot's registered EC2 artifacts or installed inventory fail now: {cur[:3]}")
    return done, os.path.basename(recs[-1]), w


def inventory_bound_problem(w):
    """The receipt must bind the inventory this authority last sealed, at the current generation."""
    lp = os.path.join(PA.INV_DIR, "latest.json")
    if not os.path.exists(lp):
        return "no sealed inventory yet (python3 prod_authority.py inventory, then install it on Lengau: chpc/row19_ec2_root.py install)"
    inv = json.load(open(lp))
    if inv.get("generation") != PA.state()["generation"]:
        return "the sealed inventory is not the current generation; seal and copy it"
    if (w.get("ec2") or {}).get("bound", {}).get("inventory_sha256") != L.sha256(lp):
        return "the receipt does not bind the current authority inventory: install it on Lengau (chpc/row19_ec2_root.py install) and take a fresh receipt"
    return ""


def controls_doc():
    """The CURRENT adopted controls (R2-2); raises ValueError when the canonical file is not the adopted bytes."""
    ctl, why = RP.adopted_controls()
    if why:
        raise ValueError(why)
    return ctl


def controls_pin():
    return (controls_doc()["versions"][-1].get("partition") or {}).get("sha256")


def build(contract, part, leds, done, token):
    """(work, duplicates, sentinels) for the contract; raises when the predeclared panel cannot be built as declared."""
    lengau = {c for c in done if not RP.blocked(part, *c)}
    if contract == "production":
        work = PA.allocate(part, leds, done, ES.CONTRACTS["production"]["workers"] - PA.SENTINELS_PER_ATTEMPT)
        if not work:
            raise ValueError("the partition block has no free coordinate left")
        return work, [], PA.sentinels(lengau, token)
    if contract == "Q1":
        own = PA.owned(leds)
        bad = [c for c in Q1_BLOCK if not RP.blocked(part, *c) or c in done or c in own]
        if bad:
            raise ValueError(f"Q1's block coordinates are not all free block coordinates, e.g. {bad[:3]}")
        miss = [c for c in Q1_LENGAU if c not in lengau]
        if miss:
            raise ValueError(f"Q1's Lengau duplicates are not all Lengau-completed, e.g. {miss[:3]}")
        return list(Q1_BLOCK), list(Q1_LENGAU), PA.sentinels(lengau, token, exclude=Q1_LENGAU)
    q1 = [a for a in leds.get(PA.qual_run("Q1"), {"attempts": []})["attempts"] if a.get("state") == "reconciled"]
    if not q1:
        raise ValueError("Q2 compares with Q1: no reconciled Q1 attempt")
    return [], list(Q2_REPEAT), []


def receipt_age_problem(w, now=None):
    now = time.time() if now is None else now
    t = w.get("time")
    if not (isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t)) or t > now + 60 or now - t > RECEIPT_MAX_AGE_S:
        return f"the receipt's time {t!r} is no longer within {RECEIPT_MAX_AGE_S} s"
    return ""


def dispatch_guard(run, snapshot, w):
    """R2-3: called immediately before EVERY RunInstances issue/re-issue; '' lets the call go out."""
    def guard():
        return stop_problem(run, snapshot) or receipt_age_problem(w)
    return guard


def admit(a, now=None):
    run = PA.qual_run(a.contract) if a.contract in ("Q1", "Q2") else PA.run_name(a.epoch)
    try:
        controls_doc()
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    leds = PA.ledgers(); led = L.load(run)
    if any(x.get("state") in ("intent", "ambiguous") for x in led["attempts"]):
        sys.exit(f"REFUSED: an attempt of {run} is unresolved - python3 prod_launch.py --contract {a.contract} --epoch {a.epoch} --recover")
    why = stop_problem(run, a.snapshot)
    if why:
        sys.exit(f"REFUSED: {why} - no new EC2 dispatch")
    why = PA.exclusion_problem(leds, L.REGION)
    if why:
        sys.exit(f"REFUSED: {why}")
    rel = PA.release_state(leds)
    gate = rel["qualification"]["ok"] if a.contract in ("Q1", "Q2") else rel["production"]["ok"]
    if not gate:
        sys.exit(f"REFUSED: ec2_release_state.json does not permit {a.contract} (row 23 success / qualification permission and "
                 f"owner-accepted ceilings / reviewed production release certificate)")
    man_prod = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))
    part = RP.load(a.partition, man_prod, PROD_SHA); psha = RP.sha_file(a.partition)
    if part["epoch"] != a.epoch or controls_pin() != psha:
        sys.exit("REFUSED: the partition is not this epoch's or not the one the latest adopted controls pin")
    actp = os.path.join(a.snapshot, "live", "refit", "root", "ec2", f"activation_e{a.epoch}.json")
    try:
        why = RP.activation_problem(man_prod, PROD_SHA, part, psha, json.load(open(actp)), controls=controls_doc(), mode=MODE)
    except Exception as e:
        why = f"no activation proof in the snapshot ({type(e).__name__})"
    if why:
        sys.exit(f"REFUSED: {why}")
    opm = json.load(open(a.manifest))
    why = ES.operational_problem(opm, man_prod, PROD_SHA)
    if why or opm["ec2_production"]["epoch"] != a.epoch or opm["ec2_production"]["contract"] != a.contract:
        sys.exit(f"REFUSED: {why or 'the operational manifest is not this epoch and contract'}")
    try:
        done, receipt, w = snapshot_state(a.snapshot, part, now)
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    why = inventory_bound_problem(w)
    if why:
        sys.exit(f"REFUSED: {why}")
    c = ES.CONTRACTS[a.contract]
    life = PA.QUAL_LIFETIME_S if a.contract in ("Q1", "Q2") else int(opm["ec2_production"]["lifetime_s"])
    if a.contract in ("Q1", "Q2") and int(opm["ec2_production"]["lifetime_s"]) != life:
        sys.exit(f"REFUSED: the qualification lifetime is declared {life} s; the manifest says {opm['ec2_production']['lifetime_s']}")
    worst = PA.worst_usd(life, c["max_price"])
    why = PA.budget_problem(leds, run, worst, rel, now)
    if why:
        sys.exit(f"REFUSED: {why}")
    st = PA.state(); n = max([x["attempt"] for x in led["attempts"]], default=0) + 1
    token = f"t1-{run}-{n}-{uuid.uuid4().hex[:12]}"
    try:
        work, dup, sent = build(a.contract, part, leds, done, token)
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    st, seq = PA.bump(st, sequences=1)
    attempt_id = f"ec2-{run}-a{n}"
    roles = ([("work", x) for x in work] + [("qual_lengau" if a.contract == "Q1" else "qual_repeat", x) for x in dup]
             + [("sentinel", x) for x in sent])
    plan = {"job": n, "attempt_id": attempt_id, "sequence": seq, "epoch": a.epoch, "contract": a.contract, "partition_sha256": psha,
            "opmanifest_sha256": L.sha256(a.manifest), "activation_sha256": L.sha256(actp), "instance": dict(c, roles=dict(c["roles"])),
            "lifetime_s": life, "slots": [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate(roles)]}
    att_view = dict(attempt_id=attempt_id, sequence=seq, coordinates=[list(x) for x in work], sentinels=[list(x) for x in sent],
                    duplicates=[list(x) for x in dup])
    why = ES.plan_problem(plan, a.contract, att_view, psha, plan["opmanifest_sha256"], plan["activation_sha256"])
    if why:
        sys.exit(f"REFUSED: the built plan fails its own contract ({why})")
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
    print(f"{attempt_id} ({a.contract}, seq {seq}): {len(work)} owned, {len(dup)} duplicates, {len(sent)} sentinels on {c['itype']} "
          f"cap {c['max_price']:.2f}, lifetime {life} s, worst USD {worst:.2f}; receipt {receipt}")
    ami = json.loads(L.aws("ssm", "get-parameters", "--names", L.AMI_PARAM, "--output", "json").stdout)["Parameters"][0]["Value"]
    tags = [{"ResourceType": rt, "Tags": [{"Key": "project", "Value": "t1"}, {"Key": "row", "Value": "19-ec2"}, {"Key": "run", "Value": run},
                                            {"Key": "attempt", "Value": str(n)}, {"Key": "Name", "Value": attempt_id}]} for rt in ("instance", "volume")]
    args = ["ec2", "run-instances", "--image-id", ami, "--instance-type", c["itype"], "--count", "1", "--client-token", token,
            "--placement", f"AvailabilityZone={L.AZ}", "--iam-instance-profile", f"Name={L.ROLE}",
            "--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
                "MaxPrice": f"{c['max_price']:.2f}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}}),
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": c["volume_gb"], "VolumeType": "gp3", "DeleteOnTermination": True}}]),
            "--metadata-options", "HttpTokens=required", "--tag-specifications", json.dumps(tags), "--user-data", f"file://{udp}", "--output", "json"]
    if a.dry_run:
        try:
            L.aws(*args, "--dry-run")
        except L.AwsError as e:
            print("DRY RUN:", "EC2 authorization OK" if e.code == "DryRunOperation" else str(e)); return 0 if e.code == "DryRunOperation" else 1
        return 1
    for k, p in files.items():
        L.aws("s3", "cp", p, f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run}/attempt_{n}/{k}", "--only-show-errors", timeout=1800)
    guard = dispatch_guard(run, a.snapshot, w)
    why = guard()                                                            # R2-3: after staging, before journaling/issue
    if why:
        sys.exit(f"REFUSED after staging: {why} - nothing journaled, no RunInstances")
    reqp = os.path.join(d, f"request_attempt{n}.json")
    json.dump(dict(client_token=token, args=args, userdata_sha256=L.sha256(udp), sha256=sums, region=L.REGION, az=L.AZ), open(reqp, "w"), indent=1)
    att = dict(attempt=n, sequence=seq, attempt_id=attempt_id, contract=a.contract, state="intent", client_token=token, request=reqp,
               region=L.REGION, az=L.AZ,
               lifetime_s=life, max_price=c["max_price"], anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, type=c["itype"], ami=ami,
               plan=planp, plan_sha256=L.sha256(planp), coordinates=att_view["coordinates"], sentinels=att_view["sentinels"],
               duplicates=att_view["duplicates"], ingestion="pending",
               results=f"s3://{L.BUCKET}/results/t1_access/aws_bench/{run}/attempt_{n}/", intent_at=time.time(), receipt=receipt)
    led["attempts"].append(att); L.save(run, led)
    PA.write_inventory()                                                     # the intent: a new generation to install
    rc = L.finish(run, led, att, fresh=True, guard=guard)
    PA.write_inventory()                                                     # the dispatch outcome: another generation (R2-1)
    return rc


def recover(a):
    run = PA.qual_run(a.contract) if a.contract in ("Q1", "Q2") else PA.run_name(a.epoch)
    led = L.load(run)
    att = next((x for x in reversed(led["attempts"]) if x.get("state") in ("intent", "ambiguous")), None)
    if att is None:
        sys.exit("nothing to recover")
    if att.get("region", L.REGION) != L.REGION:                               # R1-7: the region is attempt identity
        sys.exit(f"REFUSED: the attempt was made in {att.get('region')}; this launcher is set to {L.REGION} - recover it there")
    why = stop_problem(run, a.snapshot)
    if why:                                                                  # V10-8: never re-issue a launch under STOP
        sys.exit(f"REFUSED: {why} - the unresolved attempt stays charged at its worst case; resolve it by "
                 f"describe-instances on token {att['client_token']} (the reaper) once STOP is lifted or by hand")
    rc = L.finish(run, led, att, fresh=False, guard=lambda: stop_problem(run, a.snapshot))   # R2-3: before every re-issue
    PA.write_inventory()
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", choices=sorted(ES.CONTRACTS), required=True); ap.add_argument("--epoch", type=int, required=True)
    ap.add_argument("--partition"); ap.add_argument("--manifest")
    ap.add_argument("--snapshot", default=os.path.join(T1, "chpc", "results", "row19_screen")); ap.add_argument("--tarball")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--recover", action="store_true")
    a = ap.parse_args()
    run = PA.qual_run(a.contract) if a.contract in ("Q1", "Q2") else PA.run_name(a.epoch)
    try:
        with PA.authority_lock(), L.run_lock(run):
            if a.recover:
                return recover(a)
            if not (a.partition and a.manifest and a.tarball):
                sys.exit("--partition, --manifest and --tarball are required to admit an instance")
            return admit(a)
    except BlockingIOError:
        sys.exit(f"REFUSED: another authority operation, launcher or reaper holds the lock")


if __name__ == "__main__":
    sys.exit(main())

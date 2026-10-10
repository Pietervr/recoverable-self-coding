"""Ledger row 23 (revision 3, after Codex RSC a2e92b2): admit, dispatch and recover ONE benchmark attempt (spot
c7a.24xlarge, us-west-2) from the Mac.

    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2 --dry-run   # EC2 authorization only
    python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2             # admit + dispatch
    python3 bench_launch.py --run b2 --recover        # re-issue an unresolved attempt's SAME request (same client token)

ADMISSION IS SERIALIZED. Everything from loading the ledger to the dispatch outcome runs under an exclusive, non-blocking
lock on runs/<run>/.lock, shared with bench_reaper.py's ledger writes; a second launcher refuses instead of racing.

ATTEMPT STATES. intent (request saved, token chosen, not yet answered) -> launched (instance id known) | rejected (EC2
returned a definitive client error: no instance exists) | ambiguous (anything else: timeout, 5xx, throttling, an unparsed
error). intent and ambiguous stay FUNDED at their worst case and block new attempts; they are resolved only by
re-issuing the identical saved request with the same client token (EC2 idempotency returns the original instance if one
was created, or creates exactly one), with bounded backoff, here or by --recover after a crash. An empty Describe is never
taken as proof of absence. launched -> reconciled only by bench_reaper.py on an attributable shutting-down/terminated
observation.

COST. Row 23 ceiling USD 28.00 cumulative. Worst case per attempt = (lifetime + 900 s reaper grace + 1,800 s reserve for
polling, API retries and volume cleanup) x (MaxPrice 1.20 + 0.0094/h: 40 GB gp3 0.0044 + public IPv4 0.005) + 0.10 S3
= USD 27.01 at 77,400 s. rejected = 0; reconciled = observed
compute hours (upper bound) at the same rates + any ancillary hours recorded by the reaper; every other state = worst
case. A new attempt gets only the lifetime the remainder admits and is refused below 72,300 s.

FALLBACK SUPERVISION. After a launch the launcher starts bench_reaper.py detached under caffeinate (no idle sleep) and
waits for its heartbeat; without one within 180 s it terminates the instance itself (retrying) and exits non-zero."""
import argparse, contextlib, fcntl, hashlib, json, os, re, subprocess, sys, time, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE, REGION, BUCKET = "xtenure-read", "us-west-2", "xtenure-cself-pvr-usw2"
ITYPE, MAXPRICE, ROLE = "c7a.24xlarge", 1.20, "xtenure-ec2-t1-worker"
ANC_H, S3_FIXED, GRACE_S, RESERVE_S, CEILING = 0.0094, 0.10, 900, 1800, 28.00
MAX_LIFE_S, MIN_LIFE_S = 77400, 72300
AMI_PARAM = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
FILES = {"manifest_A.json": "bench/manifest_A.json", "manifest_B.json": "bench/manifest_B.json", "plan.json": "bench/plan.json",
         "attest.py": "attest.py", "row6_lengau_panel.py": "../chpc/row6_lengau_panel.py"}
PINS = {"manifest_A.json": "824837ee54af3f5fe43d67427cfdd335afc99e2f6d846333eb030b0e559053fa",
        "manifest_B.json": "08e498c447341dee9f462f10a5570eda4ef58e3c5ad9e418dfc7bc8a4b061955",
        "plan.json": "a67e2e1ce9c9c98455ee7946ec8f141ab50a5a8a473178b89aeaa12957d456d5",
        "row6_lengau_panel.py": "76e5670f348032193cd4425b188be09aef8037af69c5ac5b9af8198e6e2e3327",
        "t1_toolchain_lengau.tgz": "ec799aafe4347c3e20aedcced23d255a85afb763d24352dfed62705ac5dd4da2"}
# EC2 client errors that mean the request was refused and no instance exists. IdempotentParameterMismatch is NOT here:
# it says a request under this token already exists, so it stays ambiguous.
DEFINITIVE = {"InvalidParameterValue", "InvalidParameter", "InvalidParameterCombination", "MissingParameter",
              "UnauthorizedOperation", "AuthFailure", "OptInRequired", "InsufficientInstanceCapacity", "SpotMaxPriceTooLow",
              "MaxSpotInstanceCountExceeded", "VcpuLimitExceeded", "InstanceLimitExceeded", "InvalidAMIID.NotFound",
              "InvalidAMIID.Malformed", "InvalidIAMInstanceProfile.NotFound", "InvalidUserData.Malformed",
              "InvalidBlockDeviceMapping", "UnsupportedOperation", "Unsupported"}
BACKOFF_S = (15, 30, 60, 120, 240)


class AwsError(RuntimeError):
    def __init__(self, msg, code=None):
        super().__init__(msg); self.code = code


def aws(*args, timeout=120):
    env = dict(os.environ)
    if "run-instances" in args:          # one HTTP attempt: a definitive error is then the answer to THIS dispatch,
        env.update(AWS_MAX_ATTEMPTS="1", AWS_RETRY_MODE="standard")   # not to a hidden CLI retry of an unanswered one
    try:
        p = subprocess.run(["aws", "--profile", PROFILE, "--region", REGION, *args], capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise AwsError(f"aws {' '.join(args[:2])}: client timeout after {timeout} s")
    if p.returncode != 0:
        m = re.search(r"An error occurred \(([^)]+)\)", p.stderr)
        raise AwsError(f"aws {' '.join(args[:2])}: {p.stderr.strip()[:400]}", m.group(1) if m else None)
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
    if a.get("state") == "rejected":
        return 0.0
    if a.get("state") == "reconciled":
        t = a["terminal"]
        return (t["compute_s"] / 3600) * MAXPRICE + (t["ancillary_s"] / 3600) * ANC_H + S3_FIXED
    return worst_usd(a["lifetime_s"] + GRACE_S + RESERVE_S)


def run_dir(run):
    d = os.path.join(HERE, "runs", run); os.makedirs(d, exist_ok=True); return d


@contextlib.contextmanager
def run_lock(run, blocking=False, wait_s=600):
    fh = open(os.path.join(run_dir(run), ".lock"), "a+")
    t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            break
        except BlockingIOError:
            if not blocking and time.time() - t0 > wait_s:
                raise
            if not blocking:
                raise
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def load(run):
    p = os.path.join(run_dir(run), "attempts.json")
    return json.load(open(p)) if os.path.exists(p) else {"run": run, "ceiling_usd": CEILING, "attempts": []}


def save(run, led):
    p = os.path.join(run_dir(run), "attempts.json"); tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(led, f, indent=1); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)


def find_instances(**filters):
    fl = [f"Name={k},Values={v}" for k, v in filters.items()]
    out = json.loads(aws("ec2", "describe-instances", "--filters", *fl, "--output", "json").stdout)
    return [i for r in out["Reservations"] for i in r["Instances"]]


def issue(req):
    """One RunInstances call of a saved request. Returns ('launched', instance) | ('rejected', code) | ('ambiguous', msg)."""
    try:
        out = json.loads(aws(*req["args"], timeout=180).stdout)
        return "launched", out["Instances"][0]
    except AwsError as e:
        if e.code in DEFINITIVE:
            return "rejected", f"{e.code}: {e}"
        return "ambiguous", str(e)
    except Exception as e:
        return "ambiguous", f"{type(e).__name__}: {e}"


def resolve(run, led, att, fresh):
    """Issue / re-issue the attempt's saved request (same token, same parameters, same user-data bytes) with bounded
    backoff. A definitive client error releases the attempt ('rejected', charged 0) ONLY when it answers the very first
    dispatch of a fresh admission (single HTTP attempt, no earlier unanswered call, no crash in between). After any
    unanswered dispatch, or for a recovered intent, a rejection proves nothing about the earlier call: the attempt stays
    'ambiguous' and funded. Changed user-data bytes refuse the replay and leave it funded."""
    req = json.load(open(att["request"]))
    assert req["client_token"] == att["client_token"]
    udp = req["args"][req["args"].index("--user-data") + 1].replace("file://", "", 1)
    for i, pause in enumerate((0,) + BACKOFF_S):
        time.sleep(pause)
        if not os.path.exists(udp) or sha256(udp) != req["userdata_sha256"]:
            att.setdefault("issues", []).append(dict(at=time.time(), result="refused", detail="user-data bytes changed or missing"))
            save(run, led)                                   # state unchanged: intent or ambiguous, funded either way
            print("REFUSED replay: the saved user-data bytes changed; the attempt stays funded"); return None
        state, x = issue(req)
        first = fresh and i == 0 and not any(z["result"] != "refused" for z in att.get("issues", []))
        att.setdefault("issues", []).append(dict(at=time.time(), result=state, detail=(x["InstanceId"] if state == "launched" else str(x)[:300])))
        if state == "launched":
            att.update(state="launched", instance=x["InstanceId"], launch_time=x["LaunchTime"]); save(run, led); return True
        if state == "rejected" and first:
            att.update(state="rejected", rejection=x); save(run, led); return False
        if state == "rejected":
            att["rejected_on_replay"] = x                # not proof that no earlier call created an instance
        att["state"] = "ambiguous"; save(run, led)
    return None


def start_reaper(run, att):
    hb = os.path.join(run_dir(run), f"reaper_attempt{att['attempt']}.heartbeat")
    log = open(os.path.join(run_dir(run), f"reaper_attempt{att['attempt']}.log"), "a")
    subprocess.Popen(["caffeinate", "-i", sys.executable, os.path.join(HERE, "bench_reaper.py"), "--run", run,
                      "--attempt", str(att["attempt"])], stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 180:
        if os.path.exists(hb) and os.path.getmtime(hb) > t0:
            return True
        time.sleep(5)
    return False


def emergency_terminate(iid):
    for pause in (0,) + BACKOFF_S:
        time.sleep(pause)
        try:
            aws("ec2", "terminate-instances", "--instance-ids", iid); return True
        except AwsError as e:
            print(f"terminate {iid} failed: {e}", flush=True)
    return False


def after_launch(run, att):
    print(json.dumps({k: att[k] for k in ("attempt", "instance", "launch_time", "lifetime_s", "client_token")}, indent=1))
    try:
        started = start_reaper(run, att)
    except Exception as e:
        print(f"reaper start failed ({type(e).__name__}: {e})", flush=True); started = False
    if started:
        print(f"reaper running (first heartbeat seen - startup proof only); log runs/{run}/reaper_attempt{att['attempt']}.log")
        return 0
    print("NO REAPER HEARTBEAT within 180 s: terminating the instance (fail closed)", flush=True)
    emergency_terminate(att["instance"])
    print(f"attempt stays 'launched' (funded) until: python3 bench_reaper.py --run {run} --attempt {att['attempt']}")
    return 2


def admit(a):
    led = load(a.run)
    open_ = [x for x in led["attempts"] if x.get("state") not in ("rejected", "reconciled")]
    if open_:
        x = open_[-1]
        sys.exit(f"REFUSED: attempt {x['attempt']} is {x['state']} - " +
                 ("python3 bench_launch.py --run %s --recover" % a.run if x["state"] in ("intent", "ambiguous")
                  else f"python3 bench_reaper.py --run {a.run} --attempt {x['attempt']}"))
    try:
        live = [i for i in find_instances(**{"tag:run": a.run}) if i["State"]["Name"] != "terminated"]
    except AwsError as e:
        sys.exit(f"REFUSED: cannot list instances tagged run={a.run}: {e}")
    if live:
        sys.exit(f"REFUSED: instance(s) tagged run={a.run} not terminated: {[i['InstanceId'] for i in live]}")
    spent = sum(charged(x) for x in led["attempts"])
    life = min(MAX_LIFE_S, int(((CEILING - spent - S3_FIXED) / (MAXPRICE + ANC_H)) * 3600) - GRACE_S - RESERVE_S)
    if life < MIN_LIFE_S:
        sys.exit(f"REFUSED: USD {spent:.2f} charged to row 23 leaves a {life} s lifetime, below the {MIN_LIFE_S} s one attempt needs")
    n = max([x["attempt"] for x in led["attempts"]], default=0) + 1
    prefix = f"results/t1_access/aws_bench/{a.run}/attempt_{n}/"
    try:
        listing = aws("s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", prefix, "--max-keys", "1", "--output", "json").stdout
    except AwsError as e:
        sys.exit(f"REFUSED: cannot check s3://{BUCKET}/{prefix}: {e}")
    if json.loads(listing or "{}").get("KeyCount", 0):
        sys.exit(f"REFUSED: s3://{BUCKET}/{prefix} is not empty")
    tgz = os.path.expanduser(a.tarball)
    paths = {"t1_toolchain_lengau.tgz": tgz, **{k: os.path.join(HERE, v) for k, v in FILES.items()}}
    sums = {k: sha256(p) for k, p in paths.items()}
    for k, want in PINS.items():
        if sums[k] != want:
            sys.exit(f"REFUSED: {k} is not the reviewed pin ({sums[k][:12]} != {want[:12]})")
    sumtext = "\n".join(f"{v}  {k}" for k, v in sums.items())
    ud = (open(os.path.join(HERE, "bench_userdata.sh")).read().replace("__RUN__", a.run).replace("__ATTEMPT__", str(n))
          .replace("__LIFETIME_S__", str(life)).replace("__SUMS__", sumtext))
    if any(t in ud for t in ("__RUN__", "__ATTEMPT__", "__LIFETIME_S__", "__SUMS__")):
        sys.exit("REFUSED: unfilled user-data placeholder")
    udp = os.path.join(run_dir(a.run), f"userdata_attempt{n}.sh"); open(udp, "w").write(ud)
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
    print(f"attempt {n}: lifetime {life} s, worst USD {worst_usd(life + GRACE_S + RESERVE_S):.2f}, prior charged USD {spent:.2f}, AMI {ami}")
    if a.dry_run:
        try:
            aws(*args, "--dry-run")
        except AwsError as e:
            ok = e.code == "DryRunOperation"
            print("DRY RUN:", "EC2 authorization OK (S3 uploads not exercised)" if ok else str(e))
            return 0 if ok else 1
        return 1
    for k, p in paths.items():
        aws("s3", "cp", p, f"s3://{BUCKET}/code/t1_access/aws_bench/{a.run}/{k}", "--only-show-errors", timeout=1800)
    reqp = os.path.join(run_dir(a.run), f"request_attempt{n}.json")
    json.dump(dict(client_token=token, args=args, userdata_sha256=sha256(udp), sha256=sums), open(reqp, "w"), indent=1)
    att = dict(attempt=n, state="intent", client_token=token, request=reqp, lifetime_s=life, max_price=MAXPRICE, type=ITYPE,
               ami=ami, results=f"s3://{BUCKET}/{prefix}", intent_at=time.time())
    led["attempts"].append(att); save(a.run, led)
    return finish(a.run, led, att, fresh=True)


def finish(run, led, att, fresh):
    r = resolve(run, led, att, fresh)
    if r is True:
        return after_launch(run, att)
    if r is False:
        print(f"attempt {att['attempt']} REJECTED by EC2 (no instance, charged 0): {att['rejection']}")
        return 1
    print(f"attempt {att['attempt']} still AMBIGUOUS after bounded retries (funded, blocks new attempts): "
          f"python3 bench_launch.py --run {run} --recover")
    return 3


def recover(a):
    led = load(a.run)
    att = next((x for x in reversed(led["attempts"]) if x.get("state") in ("intent", "ambiguous")), None)
    if att is None:
        sys.exit("nothing to recover (no intent/ambiguous attempt)")
    return finish(a.run, led, att, fresh=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--tarball")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--recover", action="store_true")
    a = ap.parse_args()
    try:
        with run_lock(a.run):
            if a.recover:
                return recover(a)
            if not a.tarball:
                sys.exit("--tarball is required to admit an attempt")
            return admit(a)
    except BlockingIOError:
        sys.exit(f"REFUSED: another launcher or reaper holds runs/{a.run}/.lock")


if __name__ == "__main__":
    sys.exit(main())

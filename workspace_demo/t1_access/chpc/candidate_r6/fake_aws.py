#!/usr/bin/env python3
"""R6' FAKE `aws` CLI (test_r6_fleet.py only). It answers the calls the launcher and the reaper make - STOP head-object,
the SSM AMI parameter, S3 code uploads, run-instances, describe-instances, describe-volumes, terminate-instances - from
one JSON state file ($R6_FAKE_STATE, serialised by its own flock) and logs every call. It never touches the network; any
call it does not model exits 97 so that a test fails loudly.

Behaviour the test steers through the state file:
  stop_keys          s3 keys whose head-object succeeds (a STOP); every other head-object is a 404
  run_modes          a queue consumed per run-instances call: ok | ambiguous | reject | hang (create, then never answer)
  instances          {id: {token, state, reason, run, attempt}}; run-instances is idempotent on the client token
  hold_s3cp          while <state dir>/hold_s3cp exists an `s3 cp` writes <state dir>/s3cp_waiting and waits (the
                     admission is then inside its authority and run locks)"""
import fcntl, json, os, sys, time

args = sys.argv[1:]
ST = os.environ["R6_FAKE_STATE"]; D = os.path.dirname(ST)


def logcall(extra=None):
    with open(os.path.join(D, "aws_calls.jsonl"), "a") as f:
        f.write(json.dumps(dict(at=time.time(), pid=os.getpid(), args=args, **(extra or {}))) + "\n")


class State:
    def __enter__(self):
        self.fh = open(ST + ".lock", "a+"); fcntl.flock(self.fh, fcntl.LOCK_EX)
        self.s = json.load(open(ST)) if os.path.exists(ST) else {}
        return self.s

    def __exit__(self, *a):
        tmp = ST + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.s, f, indent=1)
        os.replace(tmp, ST); fcntl.flock(self.fh, fcntl.LOCK_UN); self.fh.close()


def opt(name):
    return args[args.index(name) + 1] if name in args else None


a = [x for i, x in enumerate(args) if not (x in ("--profile", "--region") or (i and args[i - 1] in ("--profile", "--region")))]
logcall()
if a[:2] == ["s3api", "head-object"]:
    key = f"s3://{opt('--bucket')}/{opt('--key')}"
    with State() as s:
        stop = key in s.get("stop_keys", [])
    if stop:
        print("{}"); sys.exit(0)
    sys.stderr.write("An error occurred (404) when calling the HeadObject operation: Not Found"); sys.exit(254)
if a[:2] == ["ssm", "get-parameters"]:
    print(json.dumps({"Parameters": [{"Value": "ami-r6fake"}]})); sys.exit(0)
if a[:2] == ["s3", "cp"]:
    hold = os.path.join(D, "hold_s3cp")
    if os.path.exists(hold):
        open(os.path.join(D, "s3cp_waiting"), "w").write(str(os.getpid()))
        while os.path.exists(hold):
            time.sleep(0.2)
    sys.exit(0)
if a[:2] == ["ec2", "run-instances"]:
    if "--dry-run" in a:
        sys.stderr.write("An error occurred (DryRunOperation) when calling the RunInstances operation"); sys.exit(254)
    tok = opt("--client-token")
    tags = json.loads(opt("--tag-specifications"))[0]["Tags"]; tag = {t["Key"]: t["Value"] for t in tags}
    with State() as s:
        modes = s.setdefault("run_modes", []); mode = modes.pop(0) if modes else "ok"
        insts = s.setdefault("instances", {})
        iid = next((k for k, v in insts.items() if v["token"] == tok), None)
        if mode in ("ok", "hang") and iid is None:
            s["counter"] = s.get("counter", 0) + 1; iid = f"i-r6{s['counter']:04d}"
            insts[iid] = dict(token=tok, state="running", reason="", run=tag.get("run"), attempt=tag.get("attempt"),
                              launch=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()))
        launch = insts[iid]["launch"] if iid else None
    logcall(dict(result=mode, instance=iid))
    if mode == "hang":
        open(os.path.join(D, "run_instances_hanging"), "w").write(str(os.getpid()))
        time.sleep(3600); sys.exit(255)
    if mode == "ambiguous":
        sys.stderr.write("Read timeout on endpoint URL"); sys.exit(255)
    if mode == "reject":
        sys.stderr.write("An error occurred (InsufficientInstanceCapacity) when calling the RunInstances operation"); sys.exit(254)
    print(json.dumps({"Instances": [{"InstanceId": iid, "LaunchTime": launch, "State": {"Name": "pending"}}]})); sys.exit(0)
if a[:2] == ["ec2", "describe-instances"]:
    flt = [x for x in a if x.startswith("Name=instance-id,Values=")]
    with State() as s:
        insts = s.get("instances", {})
        ids = [f.split("Values=")[1] for f in flt]
        res = [{"Instances": [{"InstanceId": i, "State": {"Name": insts[i]["state"]}, "StateTransitionReason": insts[i]["reason"]}]}
               for i in ids if i in insts]
    print(json.dumps({"Reservations": res})); sys.exit(0)
if a[:2] == ["ec2", "describe-volumes"]:
    print(json.dumps({"Volumes": []})); sys.exit(0)
if a[:2] == ["ec2", "terminate-instances"]:
    with State() as s:
        for i in [x for x in a[2:] if x.startswith("i-")]:
            if i in s.get("instances", {}):
                s["instances"][i].update(state="terminated", reason="Client.UserInitiatedShutdown")
    print("{}"); sys.exit(0)
sys.stderr.write(f"fake aws: unmodelled call {a}"); sys.exit(97)

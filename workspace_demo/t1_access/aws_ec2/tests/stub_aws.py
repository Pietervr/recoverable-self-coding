#!/usr/bin/env python3
"""A stub `aws` for the launcher tests: behaviour from STUB_MODE, every call logged to STUB_LOG."""
import json, os, sys
args = sys.argv[1:]
log = os.environ["STUB_LOG"]; mode = os.environ.get("STUB_MODE", "ok")
calls = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
open(log, "a").write(json.dumps(args) + "\n")
a = [x for x in args if not x.startswith("--profile") and not x.startswith("--region")]
def tok():
    return args[args.index("--client-token") + 1] if "--client-token" in args else None
def inst(t):
    return {"InstanceId": "i-" + t[-8:], "LaunchTime": "2026-10-10T18:00:00+00:00", "State": {"Name": "pending"}}
if "run-instances" in args:
    if "--dry-run" in args:
        sys.stderr.write("An error occurred (DryRunOperation) when calling the RunInstances operation"); sys.exit(254)
    n = sum(1 for c in calls if "run-instances" in c)
    if mode == "reject":
        sys.stderr.write("An error occurred (InsufficientInstanceCapacity) when calling the RunInstances operation"); sys.exit(254)
    if mode == "ambiguous_then_reject":
        if n == 0:
            sys.stderr.write("Connect timeout on endpoint URL"); sys.exit(255)
        sys.stderr.write("An error occurred (UnauthorizedOperation) when calling the RunInstances operation"); sys.exit(254)
    if mode == "ambiguous_then_ok" and n == 0:
        sys.stderr.write("Connect timeout on endpoint URL"); sys.exit(255)
    if mode == "always_ambiguous":
        sys.stderr.write("Read timeout on endpoint URL"); sys.exit(255)
    print(json.dumps({"Instances": [inst(tok())]})); sys.exit(0)
if "describe-instances" in args:
    n = sum(1 for c in calls if "describe-instances" in c)
    if mode == "reaper" and "instance-id" in " ".join(args):
        iid = [x for x in args if x.startswith("Name=instance-id")][0].split("Values=")[1]
        if n < 2:
            print(json.dumps({"Reservations": []})); sys.exit(0)          # eventual consistency: empty, not terminal
        if n < 3:
            sys.stderr.write("Read timeout on endpoint URL"); sys.exit(255) # a transient error
        print(json.dumps({"Reservations": [{"Instances": [{"InstanceId": iid, "State": {"Name": "terminated"},
                                                            "StateTransitionReason": "Client.InstanceInitiatedShutdown"}]}]})); sys.exit(0)
    print(json.dumps({"Reservations": []})); sys.exit(0)
if "describe-volumes" in args:
    print(json.dumps({"Volumes": []})); sys.exit(0)
if "list-objects-v2" in args:
    print(json.dumps({"KeyCount": 0})); sys.exit(0)
if "get-parameters" in args:
    print(json.dumps({"Parameters": [{"Value": "ami-stub"}]})); sys.exit(0)
if "terminate-instances" in args:
    open(log + ".terminated", "a").write(json.dumps(args) + "\n")
print("{}"); sys.exit(0)

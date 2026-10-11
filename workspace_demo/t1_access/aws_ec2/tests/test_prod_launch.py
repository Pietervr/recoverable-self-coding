"""Admission tests of prod_launch (Codex 0483db4 V10-1/2/6/7/8) against a synthetic snapshot, a fake `aws` and a captured
dispatch: release gates, every STOP source (also on recovery), controls pin and activation, exact operational manifest,
strict receipt (fresh/production flags, finite non-future time, alarms, EC2 binding, current inventory), and the Q1/Q2
construction. No AWS, no instance; a temporary authority directory.    python3 tests/test_prod_launch.py"""
import argparse, copy, glob, json, os, shutil, sys, tempfile, time, types
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path[:0] = [PKG, os.path.join(PKG, "..", "chpc")]
import bench_launch as L, prod_authority as PA, prod_launch as PL, row19_partition as RP, row19_ec2_state as ES
TMP = tempfile.mkdtemp()
for f in ("budget_baseline.json", "ec2_release_state.json"):
    shutil.copy(os.path.join(PKG, f), os.path.join(TMP, f))
L.HERE = PA.HERE = TMP
PA.LOCK, PA.STATE = os.path.join(TMP, "runs", ".authority.lock"), os.path.join(TMP, "runs", ".authority_state.json")
PA.INV_DIR, PA.RELEASE_STATE = os.path.join(TMP, "runs", "inventory"), os.path.join(TMP, "ec2_release_state.json")
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))

# fake aws + dispatch
S3 = {"stop": set(), "fail": None}; DISPATCH = []
FAILS = {"timeout": L.AwsError("aws s3api head-object: client timeout after 30 s"),
         "credentials": L.AwsError("aws s3api head-object: Unable to locate credentials. You can configure credentials by running \"aws configure\"."),
         "connection": L.AwsError("aws s3api head-object: Could not connect to the endpoint URL: \"https://s3.us-west-2.amazonaws.com/\""),
         "forbidden": L.AwsError("aws s3api head-object: An error occurred (403) when calling the HeadObject operation: Forbidden", "403"),
         "throttled": L.AwsError("aws s3api head-object: An error occurred (SlowDown) when calling the HeadObject operation", "SlowDown")}
def fake_aws(*args, timeout=120):
    if args[:2] == ("s3api", "head-object"):
        if S3["fail"]:
            raise FAILS[S3["fail"]]
        key = f"s3://{args[args.index('--bucket') + 1]}/{args[args.index('--key') + 1]}"
        if key in S3["stop"]:
            return types.SimpleNamespace(stdout="{}")
        raise L.AwsError("aws s3api head-object: An error occurred (404) when calling the HeadObject operation: Not Found", "404")
    if args[0] == "ssm":
        return types.SimpleNamespace(stdout=json.dumps({"Parameters": [{"Value": "ami-test"}]}))
    return types.SimpleNamespace(stdout="{}")
L.aws = fake_aws
GUARDS = []
L.finish = lambda run, led, att, fresh, guard=None: GUARDS.append(guard) or DISPATCH.append((run, att, fresh)) or 0
CP_HOOK = {"f": None}
_fake = fake_aws
def fake_aws2(*args, timeout=120):
    if args[:2] == ("s3", "cp") and CP_HOOK["f"]:                     # a STOP / receipt expiry arriving during staging
        CP_HOOK["f"]()
    return _fake(*args, timeout=timeout)
L.aws = fake_aws2
tgz = os.path.join(TMP, "t.tgz"); open(tgz, "w").write("toolchain"); L.PINS = dict(L.PINS, **{"t1_toolchain_lengau.tgz": L.sha256(tgz)})

# partition, controls pin, operational manifests
prod_path = os.path.join(PKG, "..", "chpc", "row19_screen_manifest.json"); prod = json.load(open(prod_path))
part = RP.declare(prod, PL.PROD_SHA, 2, 1); pp = os.path.join(TMP, "e1.json"); json.dump(part, open(pp, "w"))
PL.controls_pin = lambda: RP.sha_file(pp)
CTL = {"versions": [{"version": 10, "partition": {"path": "chpc/row19_partition_e1.json", "sha256": RP.sha_file(pp)}}]}
ORIG_CONTROLS_DOC = PL.controls_doc
PL.controls_doc = lambda: CTL
RP.adopted_controls = lambda path=None: (CTL, "")                   # the canonical consumer's authenticated controls (R2-2)
ops = {}
for c in ("Q1", "Q2", "production"):
    ops[c] = os.path.join(TMP, f"op_{c}.json"); json.dump(ES.derive_operational(prod, PL.PROD_SHA, 1, 75300, c), open(ops[c], "w"), indent=1, sort_keys=True)

# snapshot: verify units (Lengau-done indices 0..2 of reps 3..40), activation, inventory, receipt
snap = os.path.join(TMP, "snap"); root = os.path.join(snap, "live", "refit", "root"); rec = os.path.join(snap, "receipts")
os.makedirs(os.path.join(root, "ec2", "authority")); os.makedirs(rec)
units = {f"{r}/{i}": {"record": {"ok": True}} for r in range(3, 41) for i in range(3)}
json.dump({"units": units}, open(os.path.join(rec, "verify_refit_x.json"), "w"))
m_for_act = dict(prod, storage={"root": root, "campaign": os.path.join(TMP, "camp")})
proof = dict(schema=ES.ACTIVATION_SCHEMA, mode="canonical", epoch=1, partition_sha256=RP.sha_file(pp), manifest_sha256=PL.PROD_SHA,
             transferred_indices=[], controls_version=10, controls_entry_sha256=RP.entry_sha(CTL["versions"][0]), adoption_sha256="a" * 64)
json.dump(proof, open(os.path.join(root, "ec2", "activation_e1.json"), "w"))

def receipt(**kw):
    with PA.authority_lock():
        PA.write_inventory()
    shutil.copy(os.path.join(PA.INV_DIR, "latest.json"), os.path.join(root, "ec2", "authority", "inventory.json"))
    w = dict(schema=PL.WATCH_SCHEMA, role="refit", time=time.time(), fresh=True, production=True, alarms=[],
             bound=dict(verify_file="verify_refit_x.json", verify_file_sha256=L.sha256(os.path.join(rec, "verify_refit_x.json"))),
             ec2=dict(bound=ES.bound(root)))
    w.update(kw)
    json.dump(w, open(os.path.join(rec, "watch_refit_20261011T000000Z.json"), "w"))

def release(q=False, owner=False, prod_ok=False):
    r = json.load(open(PA.RELEASE_STATE))
    open(os.path.join(TMP, "row23.json"), "w").write("{}"); r["row23"] = dict(declared_success=True, report_path="row23.json", report_sha256=L.sha256(os.path.join(TMP, "row23.json")))
    open(os.path.join(TMP, "qrec.md"), "w").write("record"); r["qualification"].update(permitted=q, owner_accepted_ceilings=owner, record_path="qrec.md", record_sha256=L.sha256(os.path.join(TMP, "qrec.md")))
    if prod_ok:
        json.dump(dict(outcome="RELEASE", problems=[]), open(os.path.join(TMP, "cert.json"), "w"))
        r["production"].update(released=True, certificate_path="cert.json", certificate_sha256=L.sha256(os.path.join(TMP, "cert.json")))
    json.dump(r, open(PA.RELEASE_STATE, "w"))
    fp = os.path.join(PA.HERE, "runs", "BENCH_FENCE.json")                 # the cutover fence (qual_permit.py) goes with permission
    if q:
        os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w").write("{}")
    elif os.path.exists(fp):
        os.remove(fp)

def ns(contract="Q1", **kw):
    return argparse.Namespace(**dict(dict(contract=contract, epoch=1, partition=pp, manifest=ops[contract], snapshot=snap, tarball=tgz, dry_run=False, recover=False), **kw))

def admit(n):
    try:
        return "OK", PL.admit(n)
    except SystemExit as e:
        return "REFUSED", str(e)

receipt()
r = admit(ns()); check("Q1 refused while qualification is not permitted (release gate)", r[0] == "REFUSED" and "does not permit" in r[1], r)
release(q=True, owner=False); receipt()
r = admit(ns()); check("Q1 refused while the owner has not accepted the ceilings", r[0] == "REFUSED" and "does not permit" in r[1], r)
release(q=True, owner=True); receipt()
for name, setup, undo in (
        ("the run's local STOP", lambda: open(os.path.join(L.run_dir("qual-Q1"), "STOP"), "w").write("x"), lambda: os.remove(os.path.join(L.run_dir("qual-Q1"), "STOP"))),
        ("the global local STOP", lambda: open(os.path.join(TMP, "runs", "STOP"), "w").write("x"), lambda: os.remove(os.path.join(TMP, "runs", "STOP"))),
        ("the Lengau root STOP in the snapshot", lambda: open(os.path.join(root, "STOP"), "w").write("x"), lambda: os.remove(os.path.join(root, "STOP"))),
        ("an ec2/HOLD in the snapshot", lambda: open(os.path.join(root, "ec2", "HOLD"), "w").write("x"), lambda: os.remove(os.path.join(root, "ec2", "HOLD"))),
        ("the run's S3 STOP", lambda: S3["stop"].add(PL.s3_stop_key("qual-Q1")), lambda: S3["stop"].clear()),
        ("the global S3 STOP", lambda: S3["stop"].add(PL.s3_stop_key()), lambda: S3["stop"].clear()),
        *[(f"an S3 STOP check that does not prove absence ({k}: fail closed, R1-5)", (lambda k=k: S3.update(fail=k)), lambda: S3.update(fail=None))
          for k in FAILS]):
    setup(); r = admit(ns()); undo()
    check(f"admission refused under {name}", r[0] == "REFUSED" and ("STOP" in r[1]), r)
# R1-1: a sandbox proof, or a proof whose controls version entry is not in the current controls, refuses
for name, edit in (("a sandbox activation proof", dict(mode="sandbox")), ("a proof of another controls version entry", dict(controls_entry_sha256="0" * 64))):
    json.dump(dict(proof, **edit), open(os.path.join(root, "ec2", "activation_e1.json"), "w")); receipt()
    r = admit(ns()); check(f"R1-1 refused for {name}", r[0] == "REFUSED" and "activation" in r[1], r)
json.dump(proof, open(os.path.join(root, "ec2", "activation_e1.json"), "w")); receipt()
# R1-3: registered EC2 artifacts in the snapshot are rechecked now; R1-2: an installed inventory is required
regp = os.path.join(root, "ec2", "register.json"); tp = os.path.join(root, "timing", "rep3", "t_150.json"); os.makedirs(os.path.dirname(tp))
json.dump({"t": 1}, open(tp, "w"))
json.dump(dict(schema=ES.REGISTER_SCHEMA, authority_generation=1, fence={}, attempts={"x": dict(attempt_id="x", key="prod-e1/9", sequence=9, state="ingested",
          coordinates={"3/150": dict(slot=0, preexisting=False, failed=False, record_sha256="r", timing_sha256=L.sha256(tp), status_sha256="s")})}), open(regp, "w"))
receipt(); r = admit(ns()); check("R1-3 refused when a registered canonical artifact in the snapshot is not its registered bytes", r[0] == "REFUSED" and "registered" in r[1], r)
os.remove(regp); os.remove(tp); receipt()
os.remove(os.path.join(root, "ec2", "authority", "inventory.json")); w = json.load(open(os.path.join(rec, "watch_refit_20261011T000000Z.json")))
w["ec2"]["bound"] = ES.bound(root); json.dump(w, open(os.path.join(rec, "watch_refit_20261011T000000Z.json"), "w"))
r = admit(ns()); check("R1-2 refused when the snapshot root has no installed inventory", r[0] == "REFUSED" and "inventory" in r[1], r)
receipt()
# R1-7: a live benchmark attempt (its launcher is outside the global lock) and an unresolved attempt in another region refuse
L.save("b9", {"run": "b9", "attempts": [dict(attempt=1, state="launched", lifetime_s=100, max_price=1.2)]})
r = admit(ns()); check("R1-7 refused while a benchmark attempt is running (exclusion)", r[0] == "REFUSED" and "benchmark" in r[1], r)
shutil.rmtree(L.run_dir("b9"))
L.save("prod-e7", {"run": "prod-e7", "attempts": [dict(attempt=1, sequence=99, attempt_id="z", state="ambiguous", region="us-west-2", contract="production",
                                                       plan_sha256="p", coordinates=[], lifetime_s=100, max_price=1.2, anc_h=0.014, s3_fixed=0.3)]})
r = admit(ns()); check("R1-7 refused while an unresolved attempt was made in another region", r[0] == "REFUSED" and "region" in r[1], r)
try:
    PL.recover(ns("production", epoch=7, recover=True)); check("R1-7 recovery refuses an attempt of another region", False)
except SystemExit as e:
    check("R1-7 recovery refuses an attempt of another region", "us-west-2" in str(e), str(e))
shutil.rmtree(L.run_dir("prod-e7")); receipt()
PL.controls_pin = lambda: None
r = admit(ns()); check("refused when the latest controls do not pin the partition", r[0] == "REFUSED" and "pin" in r[1], r)
PL.controls_pin = lambda: RP.sha_file(pp)
os.rename(os.path.join(root, "ec2", "activation_e1.json"), os.path.join(TMP, "act")); receipt()
r = admit(ns()); check("refused without the activation proof in the snapshot", r[0] == "REFUSED" and "activation" in r[1], r)
os.rename(os.path.join(TMP, "act"), os.path.join(root, "ec2", "activation_e1.json")); receipt()
bad = json.load(open(ops["Q1"])); bad["datasets"]["seed_base"] += 1; bp = os.path.join(TMP, "bad_op.json"); json.dump(bad, open(bp, "w"))
r = admit(ns(manifest=bp)); check("refused for an operational manifest that changes science", r[0] == "REFUSED" and "derivation" in r[1], r)
r = admit(ns(manifest=ops["Q2"])); check("refused for another contract's operational manifest", r[0] == "REFUSED", r)
for name, kw in (("fresh missing", dict(fresh=None)), ("production false", dict(production=False)), ("alarms", dict(alarms=["x"])),
                 ("a future time", dict(time=time.time() + 3600)), ("a NaN time", dict(time=float("nan"))), ("an old time", dict(time=time.time() - 2800)),
                 ("another role", dict(role="bank")), ("no EC2 binding", dict(ec2={}))):
    receipt(**kw); r = admit(ns())
    check(f"refused for a receipt with {name}", r[0] == "REFUSED", r)
# R2-2: a later candidate at the canonical path without its own adoption refuses (Mac = Lengau)
RP.adopted_controls = lambda path=None: (None, "the current controls are not the adopted bytes (the controls file is not the adopted bytes)")
receipt(); r = admit(ns()); check("R2-2 refused while the canonical controls are not the adopted bytes (activation lineage)", r[0] == "REFUSED" and "adopted" in r[1], r)
try:
    ORIG_CONTROLS_DOC(); check("R2-2 the launcher's controls_doc refuses unadopted controls", False)
except ValueError as e:
    check("R2-2 the launcher's controls_doc refuses unadopted controls", "adopted" in str(e))
RP.adopted_controls = lambda path=None: (CTL, "")
# R2-3: STOP written during staging, or a receipt that ages out during staging, dispatches nothing
for name, arm, disarm in (("a run STOP written during the uploads", lambda: open(os.path.join(L.run_dir("qual-Q1"), "STOP"), "w").write("x"),
                           lambda: os.path.exists(os.path.join(L.run_dir("qual-Q1"), "STOP")) and os.remove(os.path.join(L.run_dir("qual-Q1"), "STOP"))),
                          ("a global S3 STOP written during the uploads", lambda: S3["stop"].add(PL.s3_stop_key()), lambda: S3["stop"].clear()),
                          ("a receipt that aged past 2,700 s during the uploads", lambda: setattr(PL, "RECEIPT_MAX_AGE_S", -1), lambda: setattr(PL, "RECEIPT_MAX_AGE_S", 2700))):
    receipt(); DISPATCH.clear(); n_before = len(L.load("qual-Q1")["attempts"])
    CP_HOOK["f"] = arm
    r = admit(ns()); CP_HOOK["f"] = None; disarm()
    check(f"R2-3 zero dispatch and nothing journaled for {name}", r[0] == "REFUSED" and "after staging" in r[1] and not DISPATCH
          and len(L.load("qual-Q1")["attempts"]) == n_before, r)
receipt()
with PA.authority_lock():
    PA.bump(PA.state())                                       # a journal change after the receipt
r = admit(ns()); check("refused when the receipt does not bind the CURRENT inventory generation", r[0] == "REFUSED" and "inventory" in r[1], r)
receipt()
DISPATCH.clear(); r = admit(ns())
run, att, fresh = DISPATCH[-1] if DISPATCH else (None, {}, None)
plan = json.load(open(att["plan"])) if att else {}
roles = {k: sum(1 for s in plan.get("slots", []) if s["role"] == k) for k in ("work", "qual_lengau", "sentinel")}
check("Q1 admitted: 76 slots = 48 owned block + 24 Lengau duplicates + 4 sentinels, journaled intent with a global sequence",
      r == ("OK", 0) and run == "qual-Q1" and roles == dict(work=48, qual_lengau=24, sentinel=4) and att["state"] == "intent" and att["sequence"] >= 1, (r, roles))
check("Q1 sentinels are Lengau-completed and never among its duplicates", att and not ({tuple(x) for x in att["sentinels"]} & set(PL.Q1_LENGAU)))
req = json.load(open(att["request"])) if att else {"args": []}
check("Q1 request: c7a.24xlarge at cap 1.20, 60 GB", "c7a.24xlarge" in req["args"] and '"MaxPrice": "1.20"' in " ".join(req["args"]) and '"VolumeSize": 60' in " ".join(req["args"]))
check("R1-7 the attempt and its request record the region and zone", att.get("region") == L.REGION and req.get("region") == L.REGION and att.get("az") == L.AZ)
check("Q1 plan passes its own contract check", ES.plan_problem(plan, "Q1", att, plan["partition_sha256"], plan["opmanifest_sha256"], plan["activation_sha256"]) == "")
inv = json.load(open(os.path.join(PA.INV_DIR, "latest.json")))
check("the journal bumped the generation and sealed a new inventory naming Q1 as owner", inv["generation"] == PA.state()["generation"] and inv["owners"].get("3/199", [None])[0] == "qual-Q1/1")
g = GUARDS[-1] if GUARDS else None
check("R2-3 the dispatch carries a pre-issue guard that passes now", callable(g) and g() == "")
open(os.path.join(root, "STOP"), "w").write("x")
check("R2-3 ... and refuses every (re-)issue once STOP appears", callable(g) and "STOP" in g()); os.remove(os.path.join(root, "STOP"))
gens = sorted(int(os.path.basename(x)[11:-5]) for x in glob.glob(os.path.join(PA.INV_DIR, "inventory_g*.json")))
check("R2-1 intent and dispatch outcome are two sealed generations", len(gens) >= 2 and gens[-1] == PA.state()["generation"])
receipt(); r = admit(ns()); check("a second Q1 while the first is unresolved is refused", r[0] == "REFUSED" and "unresolved" in r[1], r)
led = L.load("qual-Q1"); led["attempts"][0].update(state="reconciled", terminal=dict(compute_s=3600, ancillary_s=3600)); L.save("qual-Q1", led)
receipt(); r = admit(ns()); check("a Q1 retry is refused by the per-part ceiling (retries count; owner decision)", r[0] == "REFUSED" and "Q1 ceiling" in r[1], r)
try:
    PL.build("Q1", part, PA.ledgers(), {tuple(int(x) for x in k.split("/")) for k in units}, "tok"); check("Q1's block coordinates cannot be re-owned while pending", False)
except ValueError as e:
    check("Q1's block coordinates cannot be re-owned while pending", "not all free" in str(e))
DISPATCH.clear(); r = admit(ns("Q2"))
run, att2, _ = DISPATCH[-1] if DISPATCH else (None, {}, None)
req2 = json.load(open(att2["request"])) if att2 else {"args": []}
check("Q2 admitted after a reconciled Q1: 24 repeats of index 199, c7a.12xlarge, cap 0.70, owns nothing",
      r == ("OK", 0) and run == "qual-Q2" and len(att2["duplicates"]) == 24 and att2["coordinates"] == [] and "c7a.12xlarge" in req2["args"]
      and '"MaxPrice": "0.70"' in " ".join(req2["args"]), r)
receipt(); r = admit(ns("production")); check("production refused until the reviewed release certificate exists", r[0] == "REFUSED" and "does not permit" in r[1], r)
# recovery under STOP
led = L.load("qual-Q2"); led["attempts"][0]["state"] = "ambiguous"; L.save("qual-Q2", led)
open(os.path.join(root, "STOP"), "w").write("x")
try:
    PL.recover(ns("Q2", recover=True)); check("recovery refuses to re-issue under STOP", False)
except SystemExit as e:
    check("recovery refuses to re-issue under STOP", "STOP" in str(e))
os.remove(os.path.join(root, "STOP")); DISPATCH.clear()
check("recovery re-issues the SAME attempt once STOP is lifted", PL.recover(ns("Q2", recover=True)) == 0 and DISPATCH[-1][2] is False)
# D-1 (Codex cf07869): every recovery re-issue needs a correctly bound CURRENT receipt; otherwise zero RunInstances, still funded
led = L.load("qual-Q2"); led["attempts"][0]["state"] = "ambiguous"; L.save("qual-Q2", led)
def recover_refused(name, why_part):
    DISPATCH.clear()
    try:
        PL.recover(ns("Q2", recover=True)); refused, msg = False, ""
    except SystemExit as e:
        refused, msg = True, str(e)
    a2 = L.load("qual-Q2")["attempts"][0]
    check(name, refused and why_part in msg and not DISPATCH and a2["state"] == "ambiguous" and L.charged(a2) > 0, msg)
receipt(time=time.time() - PL.RECEIPT_MAX_AGE_S - 120)
recover_refused("D-1 a stale receipt: recovery refuses, zero RunInstances, attempt stays ambiguous and funded", "receipt")
for f in glob.glob(os.path.join(rec, "watch_refit_*.json")):
    os.remove(f)
recover_refused("D-1 a missing receipt: recovery refuses, zero RunInstances", "no refit receipt")
receipt(ec2=dict(bound=dict(ES.bound(root), inventory_sha256="0" * 64)))
recover_refused("D-1 a fresh receipt bound to another EC2 state (unrelated): recovery refuses, zero RunInstances", "receipt")
receipt()
with PA.authority_lock():
    PA.write_inventory()                                                 # a newer generation the receipt does not bind
recover_refused("D-1 a fresh receipt of an older inventory generation: recovery refuses, zero RunInstances", "current")
real_bump = PL.attempt_in_inventory_problem
receipt(); PL.attempt_in_inventory_problem = lambda run, att: "the current sealed inventory does not carry this unresolved attempt (test)"
recover_refused("D-1 a fresh receipt whose inventory does not carry this attempt: recovery refuses, zero RunInstances", "does not carry")
PL.attempt_in_inventory_problem = real_bump
receipt(); DISPATCH.clear(); seen = []
stub = L.finish; L.finish = lambda run, led, att, fresh, guard=None: seen.append((guard, guard())) or DISPATCH.append((run, att, fresh)) or 0
rc = PL.recover(ns("Q2", recover=True)); L.finish = stub
check("D-1 a correctly bound current receipt: the SAME attempt is re-issued, and its per-issue guard passes at the issue",
      rc == 0 and len(DISPATCH) == 1 and DISPATCH[-1][2] is False and DISPATCH[-1][1]["client_token"] == L.load("qual-Q2")["attempts"][0]["client_token"]
      and seen and seen[-1][1] == "", (rc, len(DISPATCH), seen[-1][1] if seen else None))
import types
realtime = PL.time; PL.time = types.SimpleNamespace(time=lambda: realtime.time() + PL.RECEIPT_MAX_AGE_S + 200, sleep=realtime.sleep)
aged = seen[-1][0](); PL.time = realtime
check("D-1 ... and the same guard refuses a later re-issue once the bound receipt has aged out", "no longer within" in aged, aged)
DISPATCH.clear()
try:
    PL.recover(ns("Q2", recover=True, partition=None)); rq = False
except SystemExit as e:
    rq = "--partition" in str(e)
check("D-1 recovery without --partition refuses (the receipt is validated against it), zero RunInstances", rq and not DISPATCH)
print("ALL PASS" if ok else "SOME FAILED"); shutil.rmtree(TMP); sys.exit(0 if ok else 1)

"""Tests for the provider partition (chpc/row19_partition.py) and the v10 candidate planner guard. No fits, no Lengau.
    .venv/bin/python test_row19_partition.py"""
import os, sys, json, tempfile, importlib.util, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_partition as RP
man_path = os.path.join(HERE, "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path)); ms = RP.sha_file(man_path)
ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))

p = RP.declare(man, ms, 50, 1)
check("block is the top k indices", p["indices"] == list(range(150, 200)) and p["reps"] == list(range(3, 103)))
check("blocked() exact", RP.blocked(p, 3, 150) and RP.blocked(p, 102, 199) and not RP.blocked(p, 3, 149) and not RP.blocked(p, 2, 150))
d = tempfile.mkdtemp(); f = os.path.join(d, "p.json"); json.dump(p, open(f, "w"))
check("load accepts its own declaration", RP.load(f, man, ms)["k"] == 50)
q = dict(p, indices=p["indices"] + [10]); json.dump(q, open(f, "w"))
try:
    RP.load(f, man, ms); check("tampered indices refused", False)
except ValueError:
    check("tampered indices refused", True)
try:
    RP.load(os.path.join(d, "p.json"), man, "0" * 64); check("other manifest refused", False)
except ValueError:
    check("other manifest refused", True)
for bad in (0, 200, 1.5):
    try:
        RP.declare(man, ms, bad, 1); check(f"k={bad} refused", False)
    except ValueError:
        check(f"k={bad} refused", True)

# cutover against a synthetic root/campaign
root, camp = os.path.join(d, "root"), os.path.join(d, "camp")
os.makedirs(os.path.join(root, "records", "rep3")); os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
open(os.path.join(root, "records", "rep3", "rec_000.json"), "w").write("{}")
json.dump({"job": 1, "slots": [{"slot": 0, "rep": 4, "indices": [1]}]}, open(os.path.join(root, "plans", "job_1.json"), "w"))
json.dump({"entries": {"a": {"kind": "shard", "rep": 1, "state": "settled", "job_id": "x"}}}, open(os.path.join(camp, "budget.json"), "w"))
m2 = dict(man, storage={"root": root, "campaign": camp})
probs, facts = RP.cutover_problems(m2, p)
check("cutover passes when Lengau holds only low indices", probs == [] and facts["lengau_max_index"] == 1)
json.dump({"job": 2, "slots": [{"slot": 0, "rep": 5, "indices": [160]}]}, open(os.path.join(root, "plans", "job_2.json"), "w"))
probs, _ = RP.cutover_problems(m2, p)
check("cutover refuses a planned block coordinate (plan without ledger entry too)", any("planned" in x for x in probs))
os.makedirs(os.path.join(root, "records", "rep6")); open(os.path.join(root, "records", "rep6", "rec_170.json"), "w").write("{}")
probs, _ = RP.cutover_problems(m2, p)
check("cutover refuses a completed block coordinate", any("completed" in x for x in probs))
json.dump({"entries": {"a": {"kind": "shard", "rep": 9, "state": "live", "job_id": "y"}}}, open(os.path.join(camp, "budget.json"), "w"))
probs, _ = RP.cutover_problems(m2, p)
check("a ledger entry without its plan is an unknown claim -> refused", any("no plan" in x for x in probs))

# R1-1: a plan file that is not a well-formed slot list is an unknown claim, never "no claims"
for name, doc in (("an empty plan object", {}), ("a slot without indices", {"slots": [{"slot": 0, "rep": 3}]}), ("unreadable JSON", None)):
    pp_ = os.path.join(root, "plans", "job_7.json")
    open(pp_, "w").write("{not json" if doc is None else json.dumps(doc))
    probs, _ = RP.cutover_problems(m2, p)
    check(f"R1-1 cutover refuses a malformed plan ({name})", any("claims are unknown" in x for x in probs), probs)
os.remove(os.path.join(root, "plans", "job_7.json"))

# the v11 candidate (candidate_v10r2) planner never plans the block
spec = importlib.util.spec_from_file_location("sa11", os.path.join(HERE, "chpc", "candidate_v10r2", "row19_screen_admit.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA); SA.ACTIVATION_MODE = "sandbox"
small = json.loads(json.dumps(man)); small["cfg"]["n_boot_refit"] = 200
done = {(r, i) for r in small["datasets"]["reps"] for i in range(150)}           # everything below the block done
jobs, left = SA.plan_jobs(small, "refit", 5, done, set(), {1}, p)
check("planner with the partition plans nothing when only the block is left", jobs == [] and left == 0)
jobs, left = SA.plan_jobs(small, "refit", 5, done, set(), {1}, None)
check("without a partition the same state plans the block (default unchanged)", len(jobs) == 5)
check("partition_problem flags a supplied plan inside the block", SA.partition_problem(jobs, p) != "" and SA.partition_problem([], p) == "")

# epochs: predecessor, handback, activation (Codex 0483db4 V10-1)
import time, row19_ec2_state as ES
for bad in (None, dict(epoch=1, sha256="a" * 64)):
    try:
        RP.declare(man, ms, 40, 2, bad); check(f"epoch 2 with predecessor {bad and 'missing indices'} refused", False)
    except ValueError:
        check(f"epoch 2 with predecessor {'None' if bad is None else 'missing indices'} refused", True)
try:
    RP.declare(man, ms, 50, 1, dict(epoch=0, sha256="a" * 64, indices=[])); check("epoch 1 with a predecessor refused", False)
except ValueError:
    check("epoch 1 with a predecessor refused", True)
p2 = RP.declare(man, ms, 40, 2, dict(epoch=1, sha256=RP.sha_file(f) if False else "b" * 64, indices=p["indices"]))
check("a smaller later block hands back exactly the uncovered indices", p2["transferred_indices"] == list(range(150, 160)) and p2["indices"][0] == 160)
d2 = tempfile.mkdtemp(); root2 = os.path.join(d2, "root"); os.makedirs(os.path.join(root2, "plans")); os.makedirs(os.path.join(root2, "ec2"))
m3 = dict(man, storage={"root": root2, "campaign": os.path.join(d2, "camp")})
mp3 = os.path.join(d2, "m.json"); json.dump(m3, open(mp3, "w")); ms3 = RP.sha_file(mp3)
e1 = RP.declare(m3, ms3, 50, 1); f1 = os.path.join(d2, "e1.json"); json.dump(e1, open(f1, "w"))
ctl = os.path.join(d2, "ctl.json"); json.dump({"versions": [{"version": 10, "partition": {"sha256": RP.sha_file(f1)}}]}, open(ctl, "w"))
_, probs = RP.activate(m3, mp3, f1, ctl)
check("R1-1 a canonical activation refuses any controls file but the adopted canonical one", any("canonical controls" in x for x in probs), probs)
proof, probs = RP.activate(m3, mp3, f1, ctl, mode="sandbox")
C1 = json.load(open(ctl))
check("epoch 1 activates on a clean root with the guard live", probs == [] and RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof, C1, "sandbox") == "")
check("activation_problem refuses a proof of another partition", RP.activation_problem(m3, ms3, e1, "c" * 64, proof, C1, "sandbox") != "")
check("R1-1 a canonical consumer refuses a sandbox proof", "sandbox" in RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof, C1, "canonical"))
check("R1-1 a consumer with no controls document refuses", RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof, None, "sandbox") != "")
C2 = {"versions": C1["versions"] + [{"version": 11, "partition": None}]}
check("R1-1 a later controls version that drops the pin makes the proof historical", "historical" in RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof, C2, "sandbox"))
C3 = {"versions": [dict(C1["versions"][0], reviewed="edited")]}
check("R1-1 a proof whose controls version entry changed refuses", "byte-identical" in RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof, C3, "sandbox"))
# R2-2: a canonical consumer authenticates the CURRENT adopted controls before the proof's lineage
cproof = dict(proof, mode="canonical", adoption_sha256="a" * 64)
saved_ad = RP.adopted_controls
RP.adopted_controls = lambda path=None: (None, "the current controls are not the adopted bytes (the controls file is not the adopted bytes)")
check("R2-2 a canonical consumer refuses while the canonical controls are not the adopted bytes (a later unadopted candidate)",
      "adopted" in RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), cproof, C1, "canonical"))
RP.adopted_controls = lambda path=None: (C1, "")
check("R2-2 ... refuses a supplied controls document that is not the current adopted one",
      "current adopted" in RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), cproof, C2, "canonical"))
C4 = {"versions": C1["versions"] + [{"version": 11, "partition": C1["versions"][0]["partition"]}]}
RP.adopted_controls = lambda path=None: (C4, "")
check("R2-2 a proof made under adopted version 10 stays valid under a later ADOPTED version pinning the same partition",
      RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), cproof, None, "canonical") == "")
RP.adopted_controls = saved_ad
check("R2-2 adopted_controls reads only the canonical controls file", RP.adopted_controls(ctl)[0] is None and "canonical" in RP.adopted_controls(ctl)[1])
json.dump(proof, open(RP.activation_path(m3, 1), "w"))
e2 = RP.declare(m3, ms3, 40, 2, dict(epoch=1, sha256=RP.sha_file(f1), indices=e1["indices"])); f2 = os.path.join(d2, "e2.json"); json.dump(e2, open(f2, "w"))
json.dump({"versions": [{"version": 11, "partition": {"sha256": RP.sha_file(f2)}}]}, open(ctl, "w"))
_, probs = RP.activate(m3, mp3, f2, ctl, mode="sandbox")
check("a handback without a fresh authority inventory is refused", any("handback" in x for x in probs))
def inv(owners):
    att = {"prod-e1/1": dict(key="prod-e1/1", run="prod-e1", attempt=1, attempt_id="a1", sequence=1, state="launched", ingestion="pending",
                             contract="production", plan_sha256="x", coordinates=[[3, 155]], sentinels=[], duplicates=[], charged_usd=1.0, **{"class": "production"})}
    if not owners:
        att["prod-e1/1"]["ingestion"] = "dispositioned"
    return ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=2, at=time.time(), attempts=att,
                        owners={"3/155": ["prod-e1/1", 1]} if owners else {}, fence={"3/155": 1}, release={}, usd={}))
os.makedirs(os.path.dirname(ES.paths(root2)["inventory"]), exist_ok=True)
json.dump(inv(True), open(ES.paths(root2)["inventory"], "w"))
_, probs = RP.activate(m3, mp3, f2, ctl, mode="sandbox")
check("a handed-back coordinate still owned by a live EC2 attempt refuses activation", any("still owned" in x for x in probs), probs)
json.dump(inv(False), open(ES.paths(root2)["inventory"], "w"))
_, probs = RP.activate(m3, mp3, f2, ctl, mode="sandbox")
check("the handback activates once the owning attempt is terminal/fenced", probs == [], probs)

# v10 r1 admission: activation gate and EC2 receipt binding
SA.controls = lambda: {"versions": [{"version": 11, "partition": {"sha256": RP.sha_file(f2)}}]}
check("Lengau refit admission HOLDS while the pinned partition is not activated", "not activated" in SA.activation_problem_v10(m3, mp3, e2))
json.dump(RP.activate(m3, mp3, f2, ctl, mode="sandbox")[0], open(RP.activation_path(m3, 2), "w"))
check("... and proceeds once it is", SA.activation_problem_v10(m3, mp3, e2) == "")
check("no partition: no activation requirement (null partition unchanged)", SA.activation_problem_v10(m3, mp3, None) == "")
r = dict(ec2=dict(bound=ES.bound(root2), problems=[]))
check("a receipt binding the root's EC2 state passes", SA.ec2_receipt_problem(m3, r) == "")
json.dump(inv(False) | {"generation": 3}, open(ES.paths(root2)["inventory"], "w"))
check("a newly journaled inventory refuses the older receipt", "recollect" in SA.ec2_receipt_problem(m3, r))
open(ES.paths(root2)["hold"], "w").write("{}")
check("an ec2/HOLD refuses even a matching receipt", "HOLD" in SA.ec2_receipt_problem(m3, dict(ec2=dict(bound=ES.bound(root2), problems=[]))))
check("a receipt with no ec2 section refuses", SA.ec2_receipt_problem(m3, {}) != "")

# R1-1 provider-aware history: EC2-published records are not Lengau completions; each must lie in its own epoch's block
os.remove(ES.paths(root2)["hold"])
reg_ = dict(schema=ES.REGISTER_SCHEMA, authority_generation=2, fence={"3/155": 1}, attempts={"a1": dict(
    attempt_id="a1", key="prod-e1/1", sequence=1, state="ingested", partition_sha256=RP.sha_file(f1), epoch=1,
    coordinates={"3/155": dict(slot=0, preexisting=False, record_sha256="x", timing_sha256="y", status_sha256="z", failed=False)})})
json.dump(reg_, open(ES.paths(root2)["register"], "w"))
os.makedirs(os.path.join(root2, "records", "rep3"), exist_ok=True); open(os.path.join(root2, "records", "rep3", "rec_155.json"), "w").write("{}")
d_, p_, pr_ = RP.lengau_claims(m3)
check("R1-1 an EC2-published record is not counted as a Lengau completion", (3, 155) not in d_ and pr_ == [], pr_)
hist = {RP.sha_file(f1): e1}
check("R1-1 an EC2 coordinate inside its own epoch's block passes the history check", RP.history_problems(m3, ms3, {"versions": []}, hist) == [])
reg_["attempts"]["a1"]["coordinates"]["3/10"] = reg_["attempts"]["a1"]["coordinates"].pop("3/155"); json.dump(reg_, open(ES.paths(root2)["register"], "w"))
check("R1-1 an EC2 coordinate outside its own epoch's block is refused", any("outside the block" in x for x in RP.history_problems(m3, ms3, {"versions": []}, hist)))
check("R1-1 an EC2 entry naming a partition no controls version pins is refused", any("not one any controls" in x for x in RP.history_problems(m3, ms3, {"versions": []}, {})))
os.remove(ES.paths(root2)["register"])

# R1-3 Lengau admission rechecks the registered canonical artifacts after a clean watch (post-watch tamper)
idents = man["shard"]["identities"]
import hashlib as _h
def put(rel, obj):
    p_ = os.path.join(root2, rel); os.makedirs(os.path.dirname(p_), exist_ok=True); json.dump(obj, open(p_, "w")); return RP.sha_file(p_)
stt = dict(job="a1", slot=0, rep=3, ident=idents["3"], indices=[160], new=[160], resumed=[], left=[], exit=0, reason="", wall_s=7e4, cpu_s=7e4,
           started=1.0, ended=2.0, maxrss=2_400_000_000)
hs = dict(record_sha256=put("records/rep3/rec_160.json", {"r": 1}), timing_sha256=put("timing/rep3/t_160.json", {"t": 1}),
          status_sha256=put("ec2/status/a1.slot0.json", stt))
json.dump(dict(schema=ES.REGISTER_SCHEMA, authority_generation=2, fence={}, attempts={"a1": dict(attempt_id="a1", key="prod-e1/1", sequence=1,
          state="ingested", partition_sha256=RP.sha_file(f2), epoch=2, coordinates={"3/160": dict(slot=0, preexisting=False, failed=False, **hs)})}),
          open(ES.paths(root2)["register"], "w"))
json.dump(inv(False), open(ES.paths(root2)["inventory"], "w"))
r = dict(ec2=dict(bound=ES.bound(root2), problems=[]))
check("R1-3 a clean root after the watch admits", SA.ec2_receipt_problem(m3, r) == "", SA.ec2_receipt_problem(m3, r))
put("timing/rep3/t_160.json", {"t": 2})
check("R1-3 a canonical timing altered after a clean watch refuses admission (metadata binding unchanged)", "registered" in SA.ec2_receipt_problem(m3, r))
put("timing/rep3/t_160.json", {"t": 1}); os.remove(os.path.join(root2, "ec2", "status", "a1.slot0.json"))
check("R1-3 a copied status removed after a clean watch refuses admission", "registered" in SA.ec2_receipt_problem(m3, r))
put("ec2/status/a1.slot0.json", stt); os.remove(ES.paths(root2)["inventory"]); r = dict(ec2=dict(bound=ES.bound(root2), problems=[]))
check("R1-2 a missing installed inventory refuses admission whenever EC2 evidence exists", "inventory" in SA.ec2_receipt_problem(m3, r))

# S: the combined refit+S sub-envelope (two 60,000 ledgers would not aggregate)
cr, cs = os.path.join(d2, "c_refit"), os.path.join(d2, "c_S"); os.makedirs(cr); os.makedirs(cs)
json.dump(dict(cap_core_h=60000.0, entries={"a": dict(state="settled", settled_core_h=58000.0, reserved_core_h=1152.0)}), open(os.path.join(cr, "budget.json"), "w"))
json.dump(dict(cap_core_h=2304.0, entries={"b": dict(state="reserved", reserved_core_h=1152.0)}), open(os.path.join(cs, "budget.json"), "w"))
envs = {"versions": [{"version": 11, "sub_envelopes": [dict(name="refit+S", campaigns=[cr, cs], cap_core_h=60000.0)]}]}
check("S the combined sub-envelope refuses an S job that fits its own 2,304 cap but not the shared 60,000", "sub-envelope" in SA.sub_envelope_problem(cs, 1152.0, envs))
check("... and refuses a refit job on the same count (both directions share it)", "sub-envelope" in SA.sub_envelope_problem(cr, 1152.0, envs))
check("... and passes while the shared total fits", SA.sub_envelope_problem(cs, 100.0, envs) == "")
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

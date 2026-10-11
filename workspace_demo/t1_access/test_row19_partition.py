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

# the v10 r1 candidate planner never plans the block
spec = importlib.util.spec_from_file_location("sa10", os.path.join(HERE, "chpc", "candidate_v10r1", "row19_screen_admit.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA)
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
proof, probs = RP.activate(m3, mp3, f1, ctl)
check("epoch 1 activates on a clean root with the guard live", probs == [] and RP.activation_problem(m3, ms3, e1, RP.sha_file(f1), proof) == "")
check("activation_problem refuses a proof of another partition", RP.activation_problem(m3, ms3, e1, "c" * 64, proof) != "")
json.dump(proof, open(RP.activation_path(m3, 1), "w"))
e2 = RP.declare(m3, ms3, 40, 2, dict(epoch=1, sha256=RP.sha_file(f1), indices=e1["indices"])); f2 = os.path.join(d2, "e2.json"); json.dump(e2, open(f2, "w"))
json.dump({"versions": [{"version": 11, "partition": {"sha256": RP.sha_file(f2)}}]}, open(ctl, "w"))
_, probs = RP.activate(m3, mp3, f2, ctl)
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
_, probs = RP.activate(m3, mp3, f2, ctl)
check("a handed-back coordinate still owned by a live EC2 attempt refuses activation", any("still owned" in x for x in probs), probs)
json.dump(inv(False), open(ES.paths(root2)["inventory"], "w"))
_, probs = RP.activate(m3, mp3, f2, ctl)
check("the handback activates once the owning attempt is terminal/fenced", probs == [], probs)

# v10 r1 admission: activation gate and EC2 receipt binding
SA.controls = lambda: {"versions": [{"version": 11, "partition": {"sha256": RP.sha_file(f2)}}]}
check("Lengau refit admission HOLDS while the pinned partition is not activated", "not activated" in SA.activation_problem_v10(m3, mp3, e2))
json.dump(RP.activate(m3, mp3, f2, ctl)[0], open(RP.activation_path(m3, 2), "w"))
check("... and proceeds once it is", SA.activation_problem_v10(m3, mp3, e2) == "")
check("no partition: no activation requirement (null partition unchanged)", SA.activation_problem_v10(m3, mp3, None) == "")
r = dict(ec2=dict(bound=ES.bound(root2), problems=[]))
check("a receipt binding the root's EC2 state passes", SA.ec2_receipt_problem(m3, r) == "")
json.dump(inv(False) | {"generation": 3}, open(ES.paths(root2)["inventory"], "w"))
check("a newly journaled inventory refuses the older receipt", "recollect" in SA.ec2_receipt_problem(m3, r))
open(ES.paths(root2)["hold"], "w").write("{}")
check("an ec2/HOLD refuses even a matching receipt", "HOLD" in SA.ec2_receipt_problem(m3, dict(ec2=dict(bound=ES.bound(root2), problems=[]))))
check("a receipt with no ec2 section refuses", SA.ec2_receipt_problem(m3, {}) != "")
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

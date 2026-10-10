"""Tests for the provider partition (chpc/row19_partition.py) and the v10 candidate planner guard. No fits, no Lengau.
    .venv/bin/python test_row19_partition.py"""
import os, sys, json, tempfile, importlib.util, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_partition as RP
man_path = os.path.join(HERE, "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path)); ms = RP.sha_file(man_path)
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)

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

# the v10 candidate planner never plans the block
spec = importlib.util.spec_from_file_location("sa10", os.path.join(HERE, "chpc", "candidate_v10", "row19_screen_admit.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA)
small = json.loads(json.dumps(man)); small["cfg"]["n_boot_refit"] = 200
done = {(r, i) for r in small["datasets"]["reps"] for i in range(150)}           # everything below the block done
jobs, left = SA.plan_jobs(small, "refit", 5, done, set(), {1}, p)
check("planner with the partition plans nothing when only the block is left", jobs == [] and left == 0)
jobs, left = SA.plan_jobs(small, "refit", 5, done, set(), {1}, None)
check("without a partition the same state plans the block (default unchanged)", len(jobs) == 5)
check("partition_problem flags a supplied plan inside the block", SA.partition_problem(jobs, p) != "" and SA.partition_problem([], p) == "")
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

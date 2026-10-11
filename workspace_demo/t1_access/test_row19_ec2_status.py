"""Tests for the v10 r1 candidate status adapter (ec2_reconcile) on synthetic roots with REAL-SHAPED evidence: canonical
record/timing files hashed into a schema-2 register, complete terminal worker statuses, a sealed authority inventory of every
attempt state. No fits, no Lengau.    .venv/bin/python test_row19_ec2_status.py"""
import os, sys, json, tempfile, importlib.util, types, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_partition as RP, row19_ec2_state as ES
spec = importlib.util.spec_from_file_location("sv10r1", os.path.join(HERE, "chpc", "candidate_v10r1", "row19_screen_status.py"))
SV = importlib.util.module_from_spec(spec); spec.loader.exec_module(SV)
man_path = os.path.join(HERE, "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path))
part = RP.declare(man, RP.sha_file(man_path), 50, 1)
fake = types.ModuleType("row19_screen_admit"); fake.partition = lambda m, p: part; sys.modules["row19_screen_admit"] = fake
SV.MANIFEST_PATH = man_path
ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
AID, KEY = "ec2-prod-e1-a1", "prod-e1/1"
ID = man["shard"]["identities"]


def attempt(state="reconciled", ingestion="pending", seq=1, key=KEY, aid=AID, coords=((3, 199), (4, 199))):
    return dict(key=key, run=key.split("/")[0], attempt=int(key.split("/")[1]), attempt_id=aid, sequence=seq, state=state, ingestion=ingestion,
                contract="production", plan_sha256="p" * 64, coordinates=[list(c) for c in coords], sentinels=[[3, 0]], duplicates=[],
                charged_usd=12.5, **{"class": "production"})


def inventory(atts, at=None):
    own = {f"{c[0]}/{c[1]}": [k, a["sequence"]] for k, a in atts.items() if ES.owns(a) for c in a["coordinates"]}
    fence = {f"{c[0]}/{c[1]}": a["sequence"] for a in atts.values() for c in a["coordinates"]}
    return ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=4, at=time.time() if at is None else at, attempts=atts,
                        owners=dict(sorted(own.items())), fence=fence, release={}, usd={}))


def setup(state="ingested", inv=None, status_edit=None, drop_status=(), coords=((3, 199), (4, 199))):
    root = tempfile.mkdtemp(); os.makedirs(os.path.join(root, "ec2", "status")); os.makedirs(os.path.join(root, "ec2", "authority"))
    entry = dict(attempt_id=AID, key=KEY, sequence=1, state=state, epoch=1, coordinates={})
    units = {}
    for k, (r, i) in enumerate(coords):
        rp = os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"); tp = os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json")
        for p, obj in ((rp, dict(rep=i, x=r)), (tp, dict(job=AID, slot=k))):
            os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, "w"))
        st = dict(job=AID, slot=k, rep=r, ident=ID[str(r)], indices=[i], new=[i], resumed=[], left=[], exit=0, reason="",
                  wall_s=70000.0, cpu_s=69000.0, started=1.0, ended=70001.0, maxrss=2_400_000_000, host="ip-10-0-0-1")
        if status_edit and k == 0:
            status_edit(st)
        sp = os.path.join(root, "ec2", "status", f"{AID}.slot{k}.json")
        json.dump(st, open(sp, "w"))
        entry["coordinates"][f"{r}/{i}"] = dict(slot=k, preexisting=False, failed=False, record_sha256=sha(rp), timing_sha256=sha(tp), status_sha256=sha(sp))
        if k in drop_status:
            os.remove(sp)
        units[f"{r}/{i}"] = dict(record=dict(ok=True), timing=dict(ok=True, job=AID, slot=k))
    json.dump(dict(schema=ES.REGISTER_SCHEMA, authority_generation=4, fence={}, attempts={AID: entry}), open(os.path.join(root, "ec2", "register.json"), "w"))
    json.dump(inv if inv is not None else inventory({KEY: attempt(ingestion="ingested" if state == "ingested" else "pending")}),
              open(os.path.join(root, "ec2", "authority", "inventory.json"), "w"))
    return root, units


def run(root, units, assigned=None):
    al = []; out = SV.ec2_reconcile(man, "refit", units, root, set() if assigned is None else assigned, al)
    return al, out


root, units = setup(); assigned = set()
al, out = run(root, units, assigned)
check("ingested attempt with complete evidence: no alarm, units assigned, bound = ES.bound(root)",
      al == [] and assigned == {"3/199", "4/199"} and out["bound"] == ES.bound(root) and out["attempts"][KEY]["ingested_coordinates"] == 2, al)
check("receipt carries USD only (no core-hours)", out["usd"]["charged"] == 12.5 and "core_h" not in json.dumps(out["usd"]))
bad = json.loads(json.dumps(units)); bad["4/199"]["timing"]["job"] = "7531115.sched01"
check("timing naming another producer -> alarm", any("timing names" in a for a in run(root, bad)[0]))
root2, u2 = setup(drop_status=(0,)); check("missing copied status -> alarm", any("no worker status" in a for a in run(root2, u2)[0]))
root3, u3 = setup(status_edit=lambda s: s.update(left=[199], new=[], exit=75))
check("a status that is not a completed terminal status -> alarm", any("status" in a and ("left" in a or "exit" in a or "bytes" in a) for a in run(root3, u3)[0]), run(root3, u3)[0])
root4, u4 = setup(); open(os.path.join(root4, "records", "rep3", "rec_199.json"), "w").write("{}")
check("a canonical record that is not the register's bytes -> alarm", any("canonical record" in a for a in run(root4, u4)[0]))
root5, u5 = setup(); json.dump(dict(job=AID, slot=0, edited=True), open(os.path.join(root5, "ec2", "status", f"{AID}.slot0.json"), "w"))
check("a copied status that is not the register's bytes -> alarm", any("copied status" in a for a in run(root5, u5)[0]))
root6, u6 = setup(inv=inventory({KEY: attempt(ingestion="ingested", seq=9)}))
check("a register attempt the inventory carries with another sequence -> alarm", any("not in the authority inventory" in a for a in run(root6, u6)[0]))
live = inventory({KEY: attempt(ingestion="ingested"), "prod-e1/2": attempt(state="launched", seq=2, key="prod-e1/2", aid="ec2-prod-e1-a2", coords=((5, 199),)),
                  "prod-e1/3": attempt(state="reconciled", seq=3, key="prod-e1/3", aid="ec2-prod-e1-a3", coords=((6, 199),)),
                  "prod-e1/4": attempt(state="rejected", seq=4, key="prod-e1/4", aid="ec2-prod-e1-a4", coords=((7, 199),))})
root7, u7 = setup(inv=live); al, out = run(root7, u7)
check("the inventory reports EVERY attempt state (launched, reconciled-uningested, rejected) with USD", al == [] and
      {k: v["state"] for k, v in out["attempts"].items()} == {KEY: "reconciled", "prod-e1/2": "launched", "prod-e1/3": "reconciled", "prod-e1/4": "rejected"}, al)
check("an EC2-owned coordinate also in a Lengau plan -> alarm", any("also in a Lengau plan" in a for a in run(root7, u7, {"5/199"})[0]))
stale = inventory({"prod-e1/2": attempt(state="launched", seq=2, key="prod-e1/2", aid="ec2-prod-e1-a2", coords=((5, 199),))}, at=time.time() - 7 * 3600)
root8, u8 = setup(inv=stale)
check("a stale inventory while an attempt is live -> alarm", any("authority inventory is" in a for a in run(root8, u8)[0]))
tam = inventory({KEY: attempt(ingestion="ingested")}); tam["generation"] = 99
root9, u9 = setup(inv=tam); check("an inventory whose seal does not match -> alarm", any("seal" in a for a in run(root9, u9)[0]))
two = setup()[0]; r = json.load(open(os.path.join(two, "ec2", "register.json")))
r["attempts"]["ec2-prod-e1-a2"] = dict(r["attempts"][AID], attempt_id="ec2-prod-e1-a2", key="prod-e1/2", sequence=2)
json.dump(r, open(os.path.join(two, "ec2", "register.json"), "w"))
check("coordinate claimed by two attempts -> alarm", any("claimed by attempts" in a for a in run(two, units)[0]))
rootp, up = setup(coords=((3, 199), (5, 10)))
check("coordinate outside the partition -> alarm", any("outside the provider partition" in a for a in run(rootp, up)[0]))
rooti, ui = setup(state="ingesting"); check("an 'ingesting' attempt without records yet raises no record alarm", run(rooti, {})[0] == [], run(rooti, {})[0])
rootw, uw = setup(state="weird"); check("unknown register state -> alarm", any("unknown register state" in a for a in run(rootw, uw)[0]))
rootv = tempfile.mkdtemp(); os.makedirs(os.path.join(rootv, "ec2")); json.dump({"schema": "row19-ec2-register-1", "attempts": {}}, open(os.path.join(rootv, "ec2", "register.json"), "w"))
check("a schema-1 register -> alarm", any("schema" in a for a in run(rootv, {})[0]))
fake.partition = lambda m, p: None
rootn, un = setup(); check("EC2 evidence with no partition in force -> alarm", any("no provider partition" in a for a in run(rootn, un)[0]))
fake.partition = lambda m, p: part
empty = tempfile.mkdtemp(); al, out = run(empty, {})
check("no EC2 evidence: no alarm, empty attempts, bound of an empty root", al == [] and out["attempts"] == {} and out["bound"] == ES.bound(empty))
# STOP propagation (V10-8): the Lengau root STOP reaches every live EC2 run through prod_stop.propagate
calls = []
PS = types.ModuleType("prod_stop"); PS.propagate = lambda runs, reason: calls.append(runs) or runs; sys.modules["prod_stop"] = PS
open(os.path.join(root7, "STOP"), "w").write("x"); al, out = run(root7, u7)
check("a root STOP with live EC2 runs is propagated to exactly those runs", calls == [["prod-e1"]] and out.get("stop_propagated") == ["prod-e1"], (calls, al))
def boom(runs, reason): raise RuntimeError("S3 unreachable")
PS.propagate = boom; al, _ = run(root7, u7)
check("a failed propagation is an alarm (no admission proceeds on it)", any("could not be propagated" in a for a in al))
calls.clear(); PS.propagate = lambda runs, reason: calls.append(runs) or runs
open(os.path.join(root, "STOP"), "w").write("x"); run(root, units)
check("a root STOP with no live EC2 attempt propagates nothing", calls == [])
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

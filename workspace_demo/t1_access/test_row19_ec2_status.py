"""Tests for the v10 candidate status adapter (ec2_reconcile) on synthetic registers; no fits, no Lengau.
    .venv/bin/python test_row19_ec2_status.py"""
import os, sys, json, tempfile, importlib.util, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_partition as RP
spec = importlib.util.spec_from_file_location("sv10", os.path.join(HERE, "chpc", "candidate_v10", "row19_screen_status.py"))
SV = importlib.util.module_from_spec(spec); spec.loader.exec_module(SV)
man_path = os.path.join(HERE, "chpc", "row19_screen_manifest.json"); man = json.load(open(man_path))
part = RP.declare(man, RP.sha_file(man_path), 50, 1)
fake = types.ModuleType("row19_screen_admit"); fake.partition = lambda m, p: part; sys.modules["row19_screen_admit"] = fake
ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

def setup(entries, status_slots=(0, 1)):
    root = tempfile.mkdtemp(); os.makedirs(os.path.join(root, "ec2", "status"))
    json.dump({"schema": "row19-ec2-register-1", "attempts": entries}, open(os.path.join(root, "ec2", "register.json"), "w"))
    for aid in entries:
        for k in status_slots:
            open(os.path.join(root, "ec2", "status", f"{aid}.slot{k}.json"), "w").write("{}")
    return root

good_units = {"3/199": dict(record=dict(ok=True), timing=dict(ok=True, job="ec2-e1-a1", slot=0)),
              "4/199": dict(record=dict(ok=True), timing=dict(ok=True, job="ec2-e1-a1", slot=1))}
E = lambda st="ingested", **kw: {"ec2-e1-a1": dict(state=st, epoch=1, coordinates={"3/199": dict(slot=0, preexisting=False, failed=False),
                                                                                   "4/199": dict(slot=1, preexisting=False, failed=False)}, **kw)}
SV.MANIFEST_PATH = man_path
al, assigned = [], set(); root = setup(E())
out = SV.ec2_reconcile(man, "refit", good_units, root, assigned, al)
check("ingested attempt with valid evidence: no alarm, units assigned", al == [] and assigned == {"3/199", "4/199"} and out["ec2-e1-a1"]["coordinates"] == 2, al)
bad = json.loads(json.dumps(good_units)); bad["4/199"]["timing"]["job"] = "7531115.sched01"
al = []; SV.ec2_reconcile(man, "refit", bad, root, set(), al)
check("timing naming another producer -> alarm", any("timing names" in a for a in al), al)
al = []; root2 = setup(E(), status_slots=(0,)); SV.ec2_reconcile(man, "refit", good_units, root2, set(), al)
check("missing copied status -> alarm", any("no worker status" in a for a in al), al)
two = E(); two["ec2-e1-a2"] = dict(state="ingested", epoch=1, coordinates={"3/199": dict(slot=0, preexisting=False)})
al = []; SV.ec2_reconcile(man, "refit", good_units, setup(two), set(), al)
check("coordinate claimed by two attempts -> alarm", any("claimed by attempts" in a for a in al), al)
out_part = E(); out_part["ec2-e1-a1"]["coordinates"]["5/10"] = dict(slot=2, preexisting=False)
al = []; SV.ec2_reconcile(man, "refit", dict(good_units, **{"5/10": dict(record=dict(ok=True), timing=dict(ok=True, job="ec2-e1-a1", slot=2))}), setup(out_part, (0, 1, 2)), set(), al)
check("coordinate outside the partition -> alarm", any("outside the provider partition" in a for a in al), al)
al = []; SV.ec2_reconcile(man, "refit", {}, setup(E("ingesting")), set(), al)
check("an 'ingesting' attempt without records yet raises no record alarm", al == [], al)
al = []; SV.ec2_reconcile(man, "refit", good_units, setup(E("weird")), set(), al)
check("unknown register state -> alarm", any("unknown register state" in a for a in al), al)
fake.partition = lambda m, p: None
al = []; SV.ec2_reconcile(man, "refit", good_units, setup(E()), set(), al)
check("EC2 register with no partition in force -> alarm", any("no provider partition" in a for a in al), al)
check("no register -> nothing, no alarm", SV.ec2_reconcile(man, "refit", {}, tempfile.mkdtemp(), set(), []) == {})
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

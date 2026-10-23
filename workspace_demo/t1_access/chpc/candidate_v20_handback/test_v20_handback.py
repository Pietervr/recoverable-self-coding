"""Controls v20 CANDIDATE (NOT adopted): tests of the EC2 CLOSE - the epoch-2 block handed back to Lengau (route A, owner
decision 23 Oct 2026; chpc/candidate_v20_handback/DESIGN_v20.md). Mac, pure python; private temporary worlds only.

  A  the closing declaration e3 (row19_partition REVISION 7): regeneration, the split, tamper refusals, terminality
  B  the close activation (close_problems) in a sandbox root seeded from the local Lengau copy: accepted only with every
     precondition; refused with a live claim, an undispositioned attempt, an EC2-completed coordinate in the hand-back, a
     stale inventory, no predecessor activation; the e2 proof is historical under v20
  C  the planner (row19_screen_admit REVISION 20) on the REAL local snapshot: v19 order reproduced (the receipt's 179),
     the v20 order restricted to the old scope is the v19 order exactly, the hand-back extends it, the view arithmetic
  D  prod_authority REVISION 10: terminal close (every gate refuses), unchanged while open, close-check preconditions
  E  controls v20: the build, the pins, programme/sub-envelopes unchanged, Python 3.7 grammar, the live tree untouched

    python3 chpc/candidate_v20_handback/test_v20_handback.py          (from workspace_demo/t1_access)"""
import ast, copy, glob, hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile, time

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
for p in (os.path.join(T1, "aws_ec2"), T1, CHPC, CAND):     # the candidate modules must be what `import ...` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


LIVE_BEFORE = {r: sha(os.path.join(T1, r)) for r in ("chpc/row19_partition.py", "chpc/row19_screen_admit.py", "chpc/row19_screen_controls.json",
                                                     "chpc/row19_screen_controls_adoption.json", "chpc/row19_partition_e2.json",
                                                     "aws_ec2/prod_authority.py", "aws_ec2/ec2_release_state.json")}
RP = load("row19_partition", os.path.join(CAND, "row19_partition.py"))
SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))
SA19 = load("row19_screen_admit_v19", os.path.join(CHPC, "row19_screen_admit.py"))       # the live v19 admission (comparison)
RP19 = load("row19_partition_v19", os.path.join(CHPC, "row19_partition.py"))             # the live v19 partition module
import row19_ec2_state as ES                                                             # live, unchanged
PA = load("prod_authority", os.path.join(CAND, "aws_ec2", "prod_authority.py"))
PA19 = load("prod_authority_v19", os.path.join(T1, "aws_ec2", "prod_authority.py"))

fails = []; npass = [0]


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name, flush=True)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


def raises(f, *a, **k):
    try:
        f(*a, **k)
    except (ValueError, KeyError, TypeError) as e:
        return str(e) or type(e).__name__
    return ""


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json")
MAN = json.load(open(MAN_PATH)); MSHA = sha(MAN_PATH)
DESIG_PATH = os.path.join(CHPC, "row19_screen_designated.json")
DESIG = json.load(open(DESIG_PATH))
E2_PATH = os.path.join(CHPC, "row19_partition_e2.json"); E2SHA = sha(E2_PATH)
E2 = RP.load(E2_PATH, MAN, MSHA)
E3_PATH = os.path.join(CAND, "row19_partition_e3.json"); E3SHA = sha(E3_PATH)
LOCAL = os.path.join(CHPC, "results", "row19_screen", "live", "refit")
LROOT, LCAMP = os.path.join(LOCAL, "root"), os.path.join(LOCAL, "campaign")
REG_PATH = os.path.join(LROOT, "ec2", "register.json")
CTL20_PATH = os.path.join(CAND, "row19_screen_controls.json"); CTL20 = json.load(open(CTL20_PATH))
TMP = tempfile.mkdtemp(prefix="v20_handback_test_")

# ---- A. the closing declaration -------------------------------------------------------------------------------------------
print("# A. the closing declaration e3")
E3 = RP.load(E3_PATH, MAN, MSHA)
check("A1 e3 loads from its candidate path; schema 3, epoch 3, predecessor e2 48cea639 at chpc/row19_partition_e2.json",
      E3["schema"] == RP.SCHEMA3 and E3["epoch"] == 3 and E3["predecessor"]["sha256"] == E2SHA
      and E3["predecessor"]["path"] == "chpc/row19_partition_e2.json" and E2SHA.startswith("48cea639"))
check("A2 verify3: e3 is the deterministic declaration from e2 + designated + the register (Mac copy)",
      not raises(RP.load, E3_PATH, MAN, MSHA, predecessor_path=E2_PATH, register_path=REG_PATH))
own2 = set(RP.owned_set(E2)); back = set(RP.handed_back(E3))
check(f"A3 the hand-back is exactly e2's owned set ({len(own2)}), retained EC2-completed 0, EC2 owns nothing",
      back == own2 and len(back) == 3274 and E3["retained_ec2_completed"]["count"] == 0 and RP.owned_set(E3) == frozenset()
      and E3["owned_count"] == 0 and E3["cover"] == {"designated": 4800, "predecessor_owned": 3274, "handed_back": 3274,
                                                      "retained_ec2_completed": 0, "ec2_owned": 0})
check("A4 blocked() is False on every designated coordinate; transferred_of binds the hand-back digest; is_closed",
      not any(RP.blocked(E3, r, i) for r in DESIG["reps"] for i in range(80)) and RP.transferred_of(E3) ==
      {"count": 3274, "sha256": E3["handed_back"]["sha256"]} and RP.is_closed(E3) and not RP.is_closed(E2))
check("A5 the hand-back lies on the 47 EC2-designated replicates x 0..79 and is the 47 LARGEST replicate IDs of S",
      {r for r, _ in back} <= set(DESIG["providers"]["ec2_reps"]) and all(0 <= i < 80 for _, i in back)
      and min(r for r, _ in back) > max(DESIG["providers"]["lengau_reps"]))
q3 = json.load(open(os.path.join(T1, "aws_ec2", "runs", "qual-E2Q3", "attempts.json")))["attempts"][0]
check("A6 every coordinate the E2Q3 claim touched as owned work (52, rep 24) is inside the hand-back; its duplicates and "
      "sentinels are Lengau-completed coordinates (never owned)", len(q3["coordinates"]) == 52 and all(tuple(c) in back for c in q3["coordinates"])
      and not any(tuple(c) in back for c in (q3.get("duplicates") or []) + (q3.get("sentinels") or [])))


def tampered(mut, name):
    d = json.load(open(E3_PATH)); mut(d)
    p = os.path.join(TMP, f"e3_{name}.json"); json.dump(d, open(p, "w"), indent=1, sort_keys=True)
    return raises(RP.load, p, MAN, MSHA)


def _move_to_retained(d):
    c = d["handed_back"]["coordinates"]; r = "24"; i = c[r].pop(0)
    hb = {(int(a), b) for a, ix in c.items() for b in ix}
    d["handed_back"].update(count=len(hb), sha256=RP.coords_sha(hb))
    d["retained_ec2_completed"] = dict(count=1, sha256=RP.coords_sha([(24, i)]), coordinates={"24": [i]})
    d["cover"].update(handed_back=len(hb), retained_ec2_completed=1)


def _dup_in_both(d):
    d["retained_ec2_completed"] = dict(count=1, sha256=RP.coords_sha([(24, 11)]), coordinates={"24": [11]})
    d["cover"]["retained_ec2_completed"] = 1


def _drop_one(d):
    c = d["handed_back"]["coordinates"]; c["24"].pop(0)
    hb = {(int(a), b) for a, ix in c.items() for b in ix}
    d["handed_back"].update(count=len(hb), sha256=RP.coords_sha(hb)); d["cover"]["handed_back"] = len(hb)


def _add_lengau_rep(d):
    c = d["handed_back"]["coordinates"]; c["3"] = [0]
    hb = {(int(a), b) for a, ix in c.items() for b in ix}
    d["handed_back"].update(count=len(hb), sha256=RP.coords_sha(hb), coordinates=RP.as_map(hb)); d["cover"]["handed_back"] = len(hb)


TAMPER = {
    "owned_nonempty": lambda d: d.update(owned={"24": [11]}, owned_count=1, owned_sha256=RP.coords_sha([(24, 11)])),
    "both_handed_back_and_completed": _dup_in_both,
    "completed_moved_without_register": None,            # structurally valid; refused at verify3/activation (B)
    "drop_one": _drop_one,
    "lengau_replicate": _add_lengau_rep,
    "not_terminal": lambda d: d["closed"].update(terminal=False),
    "predecessor_sha": lambda d: d["predecessor"].update(sha256="0" * 64),
    "predecessor_schema1": lambda d: d["predecessor"].update(schema=RP.SCHEMA),
    "epoch2": lambda d: d.update(epoch=2),
    "extra_field": lambda d: d.update(transferred=[]),
    "cover": lambda d: d["cover"].update(ec2_owned=1),
    "count": lambda d: d["handed_back"].update(count=3273),
    "manifest": lambda d: d.update(manifest_sha256="0" * 64),
}
for name, mut in TAMPER.items():
    if mut is None:
        continue
    why = tampered(mut, name)
    check(f"A7 a tampered e3 refuses at load: {name} ({why[:70]})", bool(why))
d_moved = json.load(open(E3_PATH)); _move_to_retained(d_moved)
p_moved = os.path.join(TMP, "e3_moved.json"); json.dump(d_moved, open(p_moved, "w"), indent=1, sort_keys=True)
check("A8 a hand-back coordinate declared EC2-completed loads structurally but verify3 against the real register refuses",
      not raises(RP.load, p_moved, MAN, MSHA) and "regenerated" in raises(RP.load, p_moved, MAN, MSHA, predecessor_path=E2_PATH,
                                                                       register_path=REG_PATH))
reg_c = json.load(open(REG_PATH))
reg_c["attempts"]["ec2-prod-e2-a1"] = dict(attempt_id="ec2-prod-e2-a1", key="prod-e2/1", sequence=99, state="ingested",
                                           coordinates={"24/11": {"slot": 0}, "24/12": {"slot": 1, "preexisting": True}})
d3c = RP.declare3(MAN, MSHA, DESIG, sha(DESIG_PATH), E2, E2SHA, reg_c)
check("A9 an EC2-completed coordinate stays completed: declare3 retains 24/11 (and not a preexisting 24/12), hands back 3,273",
      d3c["retained_ec2_completed"]["coordinates"] == {"24": [11]} and d3c["handed_back"]["count"] == 3273
      and (24, 11) not in RP.handed_back(d3c) and (24, 12) in RP.handed_back(d3c))
check("A10 terminal: declare3 refuses a schema-3 predecessor; declare2 refuses a schema-3 predecessor; declare3 refuses a schema-1 one",
      bool(raises(RP.declare3, MAN, MSHA, DESIG, sha(DESIG_PATH), E3, E3SHA, None, 4))
      and bool(raises(RP.declare2, MAN, MSHA, DESIG, sha(DESIG_PATH), json.load(open(os.path.join(CHPC, "claims_snapshot_e2.json"))),
                      "0" * 64, E3, E3SHA, 4))
      and bool(raises(RP.declare3, MAN, MSHA, DESIG, sha(DESIG_PATH), RP.load(os.path.join(CHPC, "row19_partition_e1.json"), MAN, MSHA),
                      sha(os.path.join(CHPC, "row19_partition_e1.json")), None, 2)))
check("A11 e1 and e2 still load unchanged under REVISION 7 (blocked/owned_set identical to the v19 module on e2)",
      RP.owned_set(E2) == RP19.owned_set(RP19.load(E2_PATH, MAN, MSHA))
      and all(RP.blocked(E2, r, i) == RP19.blocked(E2, r, i) for r in DESIG["reps"] for i in range(0, 80, 7)))

# ---- B. the close activation -------------------------------------------------------------------------------------------
print("# B. the close activation (sandbox roots seeded from the local Lengau copy; record NAMES only, never contents)")
NOW = time.time()
LATEST = json.load(open(os.path.join(T1, "aws_ec2", "runs", "inventory", "latest.json")))


def inventory(mut=None, at=None, gen=None):
    inv = copy.deepcopy(LATEST)
    inv.pop("sha256", None)
    for k in ("qual-E2Q3/1", "qual-Q2/1"):
        inv["attempts"][k]["ingestion"] = "dispositioned"; inv["attempts"][k]["disposition_requested"] = False
    inv["owners"] = {}
    inv["at"] = NOW - 60 if at is None else at
    inv["generation"] = (LATEST["generation"] + 3) if gen is None else gen
    if mut:
        mut(inv)
    return ES.seal(inv)


def world(name, inv=None, register=None, act_e2=True):
    w = os.path.join(TMP, name); root = os.path.join(w, "root"); camp = os.path.join(w, "campaign")
    os.makedirs(os.path.join(root, "plans")); os.makedirs(os.path.join(root, "ec2", "authority")); os.makedirs(camp)
    for p in glob.glob(os.path.join(LROOT, "plans", "job_*.json")):
        shutil.copyfile(p, os.path.join(root, "plans", os.path.basename(p)))
    for p in glob.glob(os.path.join(LROOT, "records", "rep*", "rec_*.json")):       # names only: empty placeholders
        d = os.path.join(root, "records", os.path.basename(os.path.dirname(p))); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, os.path.basename(p)), "w").close()
    shutil.copyfile(os.path.join(LCAMP, "budget.json"), os.path.join(camp, "budget.json"))
    json.dump(register if register is not None else json.load(open(REG_PATH)), open(os.path.join(root, "ec2", "register.json"), "w"))
    if act_e2:
        shutil.copyfile(os.path.join(LROOT, "ec2", "activation_e2.json"), os.path.join(root, "ec2", "activation_e2.json"))
    shutil.copyfile(os.path.join(LROOT, "ec2", "activation_e1.json"), os.path.join(root, "ec2", "activation_e1.json"))
    json.dump(inv if inv is not None else inventory(), open(os.path.join(root, "ec2", "authority", "inventory.json"), "w"), indent=1, sort_keys=True)
    man = copy.deepcopy(MAN); man["storage"] = dict(MAN["storage"], root=root, campaign=camp)
    return man


def act(man, part_path=E3_PATH, ctl=CTL20_PATH, now=None):
    return RP.activate(man, MAN_PATH, part_path, controls_path=ctl, now=NOW if now is None else now, mode="sandbox")


man_ok = world("ok")
proof, probs = act(man_ok)
check(f"B1 every precondition holds -> the close activates (sandbox proof, no problem) {probs[:2]}", probs == [])
check("B2 the proof binds e3, the hand-back digest, owned = empty, closed, the predecessor e2 and the v20 entry",
      proof["epoch"] == 3 and proof["partition_sha256"] == E3SHA and proof["handed_back_sha256"] == E3["handed_back"]["sha256"]
      and proof["owned_sha256"] == RP.coords_sha([]) and proof["closed"] is True and proof["predecessor"]["sha256"] == E2SHA
      and proof["controls_version"] == 20 and proof["facts"]["lengau_claims_on_owned"] == 0)
check("B3 activation_problem accepts that proof under the v20 controls (sandbox lineage)",
      RP.activation_problem(man_ok, MSHA, E3, E3SHA, proof, controls=CTL20, mode="sandbox") == "")
e2proof = dict(json.load(open(os.path.join(LROOT, "ec2", "activation_e2.json"))), mode="sandbox")
check("B4 under v20 the e2 activation is HISTORICAL: every e2 consumer (EC2 launcher, ingestion, qualifier) refuses",
      "historical" in RP.activation_problem(man_ok, MSHA, E2, E2SHA, e2proof, controls=CTL20, mode="sandbox"))


def refused(name, needle, **kw):
    m = world(name, **{k: v for k, v in kw.items() if k in ("inv", "register", "act_e2")})
    _, pr = act(m, **{k: v for k, v in kw.items() if k in ("now",)})
    hit = [x for x in pr if needle in x]
    check(f"B5 refused: {name} ({(hit or pr or ['NOT REFUSED'])[0][:90]})", bool(hit))


inv_owned = ES.seal(dict({k: v for k, v in LATEST.items() if k != "sha256"}, at=NOW - 60))      # E2Q3 pending, owning 52
refused("live_claim_E2Q3_pending", "still owned", inv=inv_owned)


def _q2_pending(inv):
    inv["attempts"]["qual-Q2/1"]["ingestion"] = "pending"


refused("undispositioned_Q2_pending", "live or owning", inv=inventory(_q2_pending))


def _launched(inv):
    inv["attempts"]["qual-E2Q3/1"]["state"] = "launched"; inv["attempts"]["qual-E2Q3/1"]["ingestion"] = "pending"
    inv["owners"] = {f"{c[0]}/{c[1]}": ["qual-E2Q3/1", inv["attempts"]["qual-E2Q3/1"]["sequence"]] for c in inv["attempts"]["qual-E2Q3/1"]["coordinates"]}


refused("live_lease_E2Q3_launched", "live or owning", inv=inventory(_launched))
refused("stale_inventory_7h", "fresh installed authority inventory", inv=inventory(at=NOW - 7 * 3600))
reg_bad = json.load(open(REG_PATH))
reg_bad["attempts"]["ec2-prod-e2-a1"] = dict(attempt_id="ec2-prod-e2-a1", key="prod-e2/1", sequence=99, state="ingested",
                                             partition_sha256=E2SHA, coordinates={"24/11": {"slot": 0}})
refused("ec2_completed_in_handback", "EC2-completed", register=reg_bad)
refused("no_predecessor_activation", "never activated", act_e2=False)
man_v19 = world("v19ctl")
_, pr19 = RP.activate(man_v19, MAN_PATH, E3_PATH, controls_path=os.path.join(CHPC, "row19_screen_controls.json"), now=NOW, mode="sandbox")
check("B6 refused while the latest controls (v19) do not pin e3 (the Lengau guard is not live)", any("does not pin this partition" in x for x in pr19))
check("B7 the close does not touch the live root copy (no activation_e3 written by activate; activation is the CLI's job)",
      not os.path.exists(os.path.join(LROOT, "ec2", "activation_e3.json")))

# ---- C. the planner on the REAL local snapshot ---------------------------------------------------------------------------
print("# C. the planner on the local snapshot (receipt watch_refit_20261023T050233Z)")
rcp = sorted(glob.glob(os.path.join(CHPC, "results", "row19_screen", "receipts", "watch_refit_*.json")))[-1]
RCP = json.load(open(rcp)); RD = RCP["designated"]
done, planned, cprob = RP.lengau_claims(dict(MAN, storage=dict(root=LROOT, campaign=LCAMP)))
led = json.load(open(os.path.join(LCAMP, "budget.json")))
flight = set()
for e in led["entries"].values():
    pp = os.path.join(LROOT, "plans", f"job_{int(e['rep'])}.json")
    if e.get("kind") == "shard" and e.get("state") in SA.LIVE and e.get("runner_exit") is None and os.path.exists(pp):
        flight |= RP.plan_claims(pp, [])
excluded = {tuple(int(x) for x in c["coordinate"].split("/")): [1, 2] for c in RD["rescue_pending"]}
excluded.update({tuple(int(x) for x in c.split("/")): [1, 2] for c in RD["crash_excluded_outside_set"]})
desig = dict(DESIG, _sha256=sha(DESIG_PATH))
o19 = SA19.designated_order(desig, done, flight, done | planned, excluded, E2)
o20 = SA.designated_order(desig, done, flight, done | planned, excluded, E3)
o20_e2 = SA.designated_order(desig, done, flight, done | planned, excluded, E2)
o20_none = SA.designated_order(desig, done, flight, done | planned, excluded, None)
D = SA.designated_coordinates(desig)
print(f"   local snapshot: {os.path.basename(rcp)}; done (record names) in D {len(D & done)}, in flight {len(D & flight)}; v19 order {len(o19)}, v20 order {len(o20)}")
check(f"C1 the v19 order rebuilt from the local snapshot is the receipt's: plannable {RD['lengau_plannable']}, first 24 = its next_coordinates; "
      f"done + in flight {len(D & done)} + {len(D & (flight - done))} = the receipt's {RD['done']} + {RD['in_flight']} (the local root copy "
      "is a few hours older than the receipt: records the running jobs published since are 'in flight' here)",
      not cprob and len(o19) == RD["lengau_plannable"] and [f"{r}/{ix[0]}" for r, ix in o19[:24]] == RD["next_coordinates"]
      and len(D & done) + len(D & (flight - done)) == RD["done"] + RD["in_flight"])
check("C2 REVISION 20 with e2 pinned (or no partition) plans EXACTLY the v19 order (no behaviour change before the close)",
      o20_e2 == o19 and SA19.designated_order(desig, done, flight, done | planned, excluded, None) == o20_none)
old = set(c for c in SA19.lengau_scope(desig, done | planned))
restr = [x for x in o20 if (x[0], x[1][0]) in old]
check("C3 the v20 order RESTRICTED to the v19 scope is the v19 order exactly (same coordinates, same sequence)", restr == o19)
new = [(r, ix[0]) for r, ix in o20 if (r, ix[0]) not in old]
check(f"C4 the v20 order extends it by exactly the hand-back less done/in flight/excluded ({len(new)} = 3,274) and stays ascending (rep, index)",
      set(new) == back - done - flight - set(excluded) and len(new) == 3274 and [(r, ix[0]) for r, ix in o20] == sorted((r, ix[0]) for r, ix in o20))
first_new = next(k for k, (r, ix) in enumerate(o20) if (r, ix[0]) in back)
after = [(r, ix[0]) for r, ix in o20[first_new:] if (r, ix[0]) in old]
print(f"   order shape: the first {first_new} v20 positions are the v19 order's head (the 13 Lengau replicates); then the block's "
      f"replicates in ascending ID, with {len(after)} old-scope coordinate(s) of the 47 interleaved by (rep, index): {after[:6]}")
check("C5 the old-scope coordinates on the 13 Lengau replicates all precede the hand-back (the block = the 47 largest IDs)",
      all((r, ix[0]) not in back for r, ix in o20[:first_new]) and all(r in DESIG["providers"]["ec2_reps"] for r, _ in after))
v20view = SA.designated_view(desig, done, flight, done | planned, {}, None, E3)
v19view = SA19.designated_view(desig, done, flight, done | planned, {}, None, E2)
check(f"C6 the status/dry-run view after the close: EC2-designated unclaimed 0 (was {v19view['ec2_waiting_unclaimed']}), Lengau plannable "
      f"{v20view['lengau_plannable']} = {v19view['lengau_plannable']} + 3,274", v20view["ec2_waiting_unclaimed"] == 0 and v19view["ec2_waiting_unclaimed"] == 3274
      and v20view["lengau_plannable"] == v19view["lengau_plannable"] + 3274)
pend = {tuple(int(x) for x in c["coordinate"].split("/")) for c in RD["rescue_pending"]}
check("C7 receipt arithmetic: designated 4,800 = done 1,144 + in flight 198 + Lengau plannable (179 -> 3,453) + EC2 waiting (3,274 -> 0) + rescue-pending 5",
      RD["done"] + RD["in_flight"] + RD["lengau_plannable"] + RD["ec2_waiting_unclaimed"] + len(pend & D) == 4800
      and RD["done"] + RD["in_flight"] + len(o20) + 0 + len(pend & D) == 4800 and len(o20) == 3453)
jobs20, _left = SA.plan_jobs(MAN, "refit", 10, done, flight, [1], E3, order=o20)
c20 = [(int(s["rep"]), int(s["indices"][0])) for j in jobs20 for s in j["slots"]]
mv = [(r, ix[0]) for r, ix in o19 if r in DESIG["providers"]["ec2_reps"]]
pos = {c: k for k, c in enumerate((r, ix[0]) for r, ix in o20)}
check(f"C8 the next 10-job round under v20 = the first 240 of the v20 order: the {first_new} old coordinates on the Lengau replicates, then "
      f"{240 - first_new} of the block (rep {sorted({r for r, i in c20 if (r, i) in back})}); the old-scope coordinate(s) on the 47 {mv} move "
      f"from v19 position(s) {[[(r, ix[0]) for r, ix in o19].index(c) for c in mv]} to v20 position(s) {[pos[c] for c in mv]} (replicate-complete rule)",
      c20 == [(r, ix[0]) for r, ix in o20[:240]] and c20[:first_new] == [(r, ix[0]) for r, ix in o19[:first_new]]
      and all(c in back for c in c20[first_new:]) and len(c20) == 240 and first_new + len(mv) == len(o19))
check("C9 admission checks: designated_problem/partition_problem accept those jobs under e3; under e2 they refuse (blocked/out of scope)",
      SA.designated_problem(jobs20, desig, done, flight, done | planned, excluded, E3) == "" and SA.partition_problem(jobs20, E3) == ""
      and SA.designated_problem(jobs20, desig, done, flight, done | planned, excluded, E2) != "" and SA.partition_problem(jobs20, E2) != "")
check("C10 the crash rule is unchanged: a rescue-pending coordinate is never planned, also under e3",
      not any((r, ix[0]) in pend for r, ix in o20) and SA.crash_excluded.__code__.co_code == SA19.crash_excluded.__code__.co_code
      and SA.crash_history.__code__.co_code == SA19.crash_history.__code__.co_code)

# ---- D. prod_authority REVISION 10 -------------------------------------------------------------------------------------------
print("# D. prod_authority REVISION 10 (terminal close)")
leds = PA.ledgers()
check("D1 open today (live controls v19): closed_problem '' and the gates answer exactly as the live v19 authority",
      PA.closed_problem() == "" and PA.exclusion_problem(leds, "eu-north-1") == PA19.exclusion_problem(leds, "eu-north-1")
      and all(PA.e2q_admission_problem(c, PA19.release_state(leds), leds) == PA19.e2q_admission_problem(c, PA19.release_state(leds), leds)
              for c in ("E2Q1", "E2Q2", "E2Q3")))
ct = os.path.join(TMP, "t1_closed"); os.makedirs(os.path.join(ct, "chpc"))
shutil.copyfile(CTL20_PATH, os.path.join(ct, "chpc", "row19_screen_controls.json"))
shutil.copyfile(E3_PATH, os.path.join(ct, "chpc", "row19_partition_e3.json"))
REAL_T1 = PA.T1; PA.T1 = ct
try:
    cp = PA.closed_problem()
    rel = PA.release_state(leds)
    check(f"D2 v20 pins e3 -> CLOSED ({cp[:60]})", "CLOSED" in cp)
    check("D3 every admission refuses first: exclusion_problem (prod_launch's first gate)", "CLOSED" in PA.exclusion_problem(leds, "eu-north-1"))
    check("D4 E2Q1 / E2Q2 / E2Q3 qualification admissions refuse", all("CLOSED" in PA.e2q_admission_problem(c, rel, leds) for c in ("E2Q1", "E2Q2", "E2Q3")))
    check("D5 production (epoch 2 and any epoch) refuses", all("CLOSED" in PA.production_release_problem(rel, e, None) for e in (1, 2, 3)))
    check("D6 release_problem (release-adopt) refuses", "CLOSED" in PA.release_problem(os.path.join(TMP, "none.json"), os.path.join(TMP, "none.md"))[1])
    check("D7 allocate refuses on e3 and on e2", bool(raises(PA.allocate, E3, leds, set(), 72)) and bool(raises(PA.allocate, E2, leds, set(), 72)))
    check("D8 release_state: qualification, qualification_e2 (E2Q2/E2Q3) and production all NOT ok, with the close as the reason",
          not rel["qualification"]["ok"] and not rel["qualification_e2"]["ok"] and not rel["qualification_e2"]["e2q2_ok"]
          and not rel["qualification_e2"]["e2q3_ok"] and not rel["production"]["ok"] and "CLOSED" in rel["production"]["why"] and "CLOSED" in rel["closed"])
    v21 = copy.deepcopy(CTL20); v21["versions"].append(dict(copy.deepcopy(CTL20["versions"][-1]), version=21, partition=CTL20["versions"][-2]["partition"]))
    check("D9 terminal: a later controls version that pins e2 again does not re-open EC2 (any version pinning e3 closes)",
          PA.ec2_closed(v21)[0] is True)
finally:
    PA.T1 = REAL_T1
check("D10 bookkeeping stays: ack/disposition/disposition-confirm/inventory/budget never consult the close (source)",
      all("closed_problem" not in __import__("inspect").getsource(getattr(PA, f)) for f in ("ack", "disposition", "disposition_confirm", "inventory", "budget")))
inv_now = json.load(open(os.path.join(PA.INV_DIR, "latest.json")))
pr_real = PA.close_precondition_problems(leds, inv_now, PA.state()["generation"])
check(f"D11 close-check on the REAL Mac ledgers: NOT MET - E2Q3/1 and qual-Q2/1 pending, 52 owned ({len(pr_real)} problems)",
      any("qual-E2Q3/1" in x for x in pr_real) and any("qual-Q2/1" in x for x in pr_real) and any("owned" in x for x in pr_real))
leds_d = copy.deepcopy(leds)
for run, n in (("qual-E2Q3", 1), ("qual-Q2", 1)):
    a = next(x for x in leds_d[run]["attempts"] if x["attempt"] == n); a["ingestion"] = "dispositioned"
inv_d = inventory(gen=PA.state()["generation"], at=NOW - 60)
check("D12 close-check MET once E2Q3/1 and qual-Q2/1 are dispositioned and a fresh current-generation inventory is sealed",
      PA.close_precondition_problems(leds_d, inv_d, PA.state()["generation"], NOW) == [])
check("D13 close-check refuses a stale (7 h) or a non-current-generation inventory",
      PA.close_precondition_problems(leds_d, inventory(gen=PA.state()["generation"], at=NOW - 7 * 3600), PA.state()["generation"], NOW) != []
      and PA.close_precondition_problems(leds_d, inv_d, PA.state()["generation"] + 1, NOW) != [])
src_pl = open(os.path.join(T1, "aws_ec2", "prod_launch.py")).read()
i_ex, i_gate, i_alloc = src_pl.find("why = PA.exclusion_problem(leds"), src_pl.find("why = gate_problem("), src_pl.find("PA.allocate(")
check("D14 prod_launch (unchanged) calls PA.exclusion_problem before the release gate and before any plan, so every launch refuses at once",
      0 < i_ex < src_pl.find("rel = PA.release_state(leds)") < i_gate and i_alloc > 0)

# ---- E. controls v20 ---------------------------------------------------------------------------------------------------------
print("# E. controls v20")
BASE = json.load(open(os.path.join(CHPC, "row19_screen_controls.json")))
v20, v19 = CTL20["versions"][-1], CTL20["versions"][-2]
check("E1 versions 1-19 and every top-level key (programme, deployment, history) equal the adopted v19 controls",
      CTL20["versions"][:-1] == BASE["versions"] and {k: v for k, v in CTL20.items() if k != "versions"} == {k: v for k, v in BASE.items() if k != "versions"})
check("E2 v20 changes exactly two pins (partition module, admission) to this folder's bytes and the partition to e3",
      v20["version"] == 20 and sorted(f for f in v20["files"] if v20["files"][f] != v19["files"].get(f)) == ["chpc/row19_partition.py", "chpc/row19_screen_admit.py"]
      and v20["files"]["chpc/row19_partition.py"] == sha(os.path.join(CAND, "row19_partition.py"))
      and v20["files"]["chpc/row19_screen_admit.py"] == sha(os.path.join(CAND, "row19_screen_admit.py"))
      and v20["partition"] == {"path": "chpc/row19_partition_e3.json", "sha256": E3SHA})
check("E3 the status view, the EC2 state/ingestion/qualifier/E2Q module and every other pin are unchanged; sub_envelopes refit+S 81,000 and qualification_S equal v19",
      all(v20["files"][f] == v19["files"][f] for f in v19["files"] if f not in ("chpc/row19_partition.py", "chpc/row19_screen_admit.py"))
      and v20["sub_envelopes"] == v19["sub_envelopes"] and v20["sub_envelopes"][0]["cap_core_h"] == 81000.0 and v20["qualification_S"] == v19["qualification_S"])
check("E4 funding: the CSCI1913 allocation is ONE declared value (manifest funding.allocation_core_h 100,000; the controls programme block, "
      "which programme_gate.programme_funding lets override it, carries no allocation_core_h) - unchanged by v20",
      MAN["funding"]["allocation_core_h"] == 100000.0 and "allocation_core_h" not in CTL20["programme"]
      and "f.update(ctl[\"programme\"])" in open(os.path.join(CHPC, "programme_gate.py")).read())
check("E5 build_v20 --check: the controls and promotion map are the deterministic build from the authenticated v19 base",
      subprocess.run([sys.executable, os.path.join(CAND, "build_v20.py"), "--check"], capture_output=True).returncode == 0)
check("E6 Python 3.7 grammar for every candidate Python file",
      all(ast.parse(open(p).read(), feature_version=(3, 7)) for p in glob.glob(os.path.join(CAND, "*.py")) + glob.glob(os.path.join(CAND, "aws_ec2", "*.py"))))
check("E7 fit code, estimand, seeds, folds, pass conditions untouched: the manifest (43b75f94) and its code pins are not in the change set",
      MSHA.startswith("43b75f94") and not any(f.startswith(("analyze", "models", "chpc/row19_shard", "chpc/row19_screen_verify")) for f in
                                             ("chpc/row19_partition.py", "chpc/row19_screen_admit.py")))
after = {r: sha(os.path.join(T1, r)) for r in LIVE_BEFORE}
check("E8 the live tree is untouched (partition module, admission, controls, adoption, e2, Mac authority, release state)", after == LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{npass[0]} passed, {len(fails)} failed")
for f in fails:
    print("FAILED:", f)
sys.exit(1 if fails else 0)

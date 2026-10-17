"""REVISION 16 CANDIDATE (controls v16, the resized row-19 screen; NOT adopted): tests of chpc/candidate_v16 on the Mac, pure python.
Design reviews/2026-10-17_row19_resize_codex.md (RSC 08ce9e3) s.2-4, s.6 item 4; owner adoption 17 Oct 2026.

  1. the pinned declaration recomputes from the manifest (S, 0..79, 13/47, threshold 2, rescue disabled); every edit refuses;
  2. selection = S x 0..79 only, within Lengau's scope (13 replicates + its existing claims on the 47);
  3. replicate-complete order (ascending rep, then index), not index-major, not by speed or success;
  4. done, live/planned (in flight) and partition-blocked coordinates skipped; the admission check refuses each kind;
  5. the crash rule: two same-envelope slot dispositions exclude a coordinate (rescue-pending), counts from dispositions only;
  6. old history outside the set untouched (byte-identical root, still evidence, still claims);
  7. the CLI wiring (dry run): receipt-derived crash history, HELD accounting, first new-order job alone, receipt swap,
     rescue route refused, plans marked;
  8. replay on the REAL local receipt of 17 Oct 17:00Z and the live snapshot (skipped when absent): 83/2 4 crashes, 43/4 2.

    python3 chpc/candidate_v16/test_designated_r16.py          (from workspace_demo/t1_access)"""
import contextlib, copy, glob, hashlib, importlib.util, io, json, os, shutil, sys, tempfile

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
for p in (os.path.dirname(CHPC), CHPC, CAND):                 # the candidate admission must be what `import row19_screen_admit` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))
R = load("r19_status_v16", os.path.join(CAND, "row19_screen_status.py"))
import row19_partition as RP
fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json")
MAN = json.load(open(MAN_PATH)); MAN_SHA = sha(MAN_PATH)
DECL_PATH = os.path.join(CAND, "row19_screen_designated.json")
DECL = json.load(open(DECL_PATH))
S = [r for r in range(3, 103) if (r - 3) % 5 in (0, 1, 2)]
L13, E47 = S[:13], S[13:]

# ---- 1. the declaration -------------------------------------------------------------------------------------------------------
check("S by the rule: 60 reps, rep 83 in, 13 smallest = 3..23, EC2 from 24 to 100",
      len(S) == 60 and 83 in S and L13 == [3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20, 23] and E47[0] == 24 and E47[-1] == 100 and len(E47) == 47)
check("the candidate declaration recomputes from the real manifest", SA.designated_shape_problem(DECL, MAN, MAN_SHA) == "")


def edited(f):
    d = copy.deepcopy(DECL); f(d); return SA.designated_shape_problem(d, MAN, MAN_SHA)


NEG = [("rep 83 dropped", lambda d: d["reps"].remove(83)),
       ("a rep outside S added (rep 6)", lambda d: d.__setitem__("reps", sorted(d["reps"] + [6]))),
       ("indices stop 81", lambda d: d["indices"].__setitem__("stop", 81)),
       ("indices stop 200 (the old B)", lambda d: d["indices"].__setitem__("stop", 200)),
       ("indices start 1", lambda d: d["indices"].__setitem__("start", 1)),
       ("indices stop as a float", lambda d: d["indices"].__setitem__("stop", 80.0)),
       ("indices with an extra key", lambda d: d["indices"].__setitem__("step", 1)),
       ("split 14 / 46", lambda d: d["providers"].update(lengau_reps=S[:14], ec2_reps=S[14:])),
       ("split by success (Lengau = the 13 largest)", lambda d: d["providers"].update(lengau_reps=S[-13:], ec2_reps=S[:-13])),
       ("an EC2 coordinate-set epoch smuggled in", lambda d: d["providers"].__setitem__("ec2_epoch", {"epoch": 2})),
       ("crash threshold 3", lambda d: d["crash_rule"].__setitem__("max_same_envelope_crashes", 3)),
       ("crash threshold True", lambda d: d["crash_rule"].__setitem__("max_same_envelope_crashes", True)),
       ("rescue enabled", lambda d: d["rescue"].__setitem__("enabled", True)),
       ("rescue resources chosen", lambda d: d["rescue"].__setitem__("resources", {"cores": 12})),
       ("first job not alone", lambda d: d.__setitem__("first_job_alone", False)),
       ("another manifest", lambda d: d.__setitem__("manifest_sha256", "0" * 64)),
       ("another schema", lambda d: d.__setitem__("schema", "row19-screen-designated-2"))]
for label, f in NEG:
    check(f"declaration edit refuses: {label}", edited(f) != "")

# the lineage pin (designated): a temporary t1_access with the declaration under chpc/ and a controls stub
T = tempfile.mkdtemp(); os.makedirs(os.path.join(T, "chpc"))
shutil.copy(DECL_PATH, os.path.join(T, "chpc", "row19_screen_designated.json"))
for n in ("row19_screen_resources.json", "row19_partition_e1.json"):
    shutil.copy(os.path.join(CHPC, n), os.path.join(T, "chpc", n))
CTL16 = json.load(open(os.path.join(CAND, "row19_screen_controls.json")))
REAL_CONTROLS = SA.controls
SA.T1 = T; SA.controls = lambda: CTL16
doc, why = SA.designated(MAN, MAN_PATH)
check("designated(): pinned bytes in the v16 lineage -> the declaration, with its SHA-256", why == "" and doc["_sha256"] == sha(DECL_PATH))
open(os.path.join(T, "chpc", "row19_screen_designated.json"), "a").write(" ")
check("designated(): one byte changed -> HOLD", "not the lineage's pinned bytes" in SA.designated(MAN, MAN_PATH)[1])
shutil.copy(DECL_PATH, os.path.join(T, "chpc", "row19_screen_designated.json"))
c2 = copy.deepcopy(CTL16); del c2["versions"][-1]["files"]["chpc/row19_screen_designated.json"]; SA.controls = lambda: c2
check("designated(): a lineage that does not pin it -> HOLD", "does not pin" in SA.designated(MAN, MAN_PATH)[1])
SA.controls = lambda: CTL16
check("controls v16: versions 1-15 byte-identical to the adopted controls", CTL16["versions"][:-1] == json.load(open(os.path.join(CHPC, "row19_screen_controls.json")))["versions"])
v16, v15 = CTL16["versions"][-1], CTL16["versions"][-2]
check("controls v16: only admit, status and the new declaration differ from v15; partition e1 and qualification_S unchanged",
      v16["version"] == 16 and sorted(f for f in v16["files"] if v16["files"][f] != v15["files"].get(f)) ==
      ["chpc/row19_screen_admit.py", "chpc/row19_screen_designated.json", "chpc/row19_screen_status.py"]
      and v16["partition"] == v15["partition"] and v16["qualification_S"] == v15["qualification_S"])
check("controls v16: the pins are the candidate bytes", all(v16["files"][f"chpc/{n}"] == sha(os.path.join(CAND, n))
      for n in ("row19_screen_admit.py", "row19_screen_status.py", "row19_screen_designated.json")))
check("controls v16: refit+S sub-envelope declared 81,000 (v15: 60,000)",
      v16["sub_envelopes"][0]["cap_core_h"] == 81000.0 and v15["sub_envelopes"][0]["cap_core_h"] == 60000.0
      and v16["sub_envelopes"][0]["campaigns"] == v15["sub_envelopes"][0]["campaigns"])
doc = dict(DECL, _sha256=sha(DECL_PATH))

# ---- 2. selection = S x 0..79 only -------------------------------------------------------------------------------------------
ALL = {(r, i) for r in MAN["datasets"]["reps"] for i in range(200)}
order0 = SA.designated_order(doc, set(), set(), set(), {})
check("no claims: Lengau plans exactly its 13 replicates x 0..79 (1,040), nothing of the 47",
      {(r, i[0]) for r, i in order0} == {(r, i) for r in L13 for i in range(80)} and len(order0) == 1040)
orderA = SA.designated_order(doc, set(), set(), ALL, {})
got = {(r, i[0]) for r, i in orderA}
check("every coordinate of all 100 reps x 0..199 claimed: the order is exactly S x 0..79 (4,800) - no rep outside S, no index >= 80",
      got == {(r, i) for r in S for i in range(80)} and all(r in S and i < 80 for r, i in got))
claims = {(24, 0), (24, 81), (6, 0), (100, 79), (101, 3), (50, 150)}
orderC = {(r, i[0]) for r, i in SA.designated_order(doc, set(), set(), claims, {})}
check("Lengau's claims on the 47 count only inside 0..79 and only on S reps (24/0 and 100/79 yes; 24/81, 6/0, 101/3, 50/150 no)",
      (24, 0) in orderC and (100, 79) in orderC and not ({(24, 81), (6, 0), (101, 3), (50, 150)} & orderC) and len(orderC) == 1042)
check("an unclaimed coordinate of an EC2-designated replicate is never Lengau's (25/0 waits for the EC2 epoch)", (25, 0) not in orderC)
part = RP.load(os.path.join(CHPC, "row19_partition_e1.json"), MAN, MAN_SHA)
check("the epoch-1 partition stays enforced: no planned coordinate in 160..199 even when claimed",
      all(i < 160 for _, (i,) in SA.designated_order(doc, set(), set(), ALL, {}, part)))

# ---- 3. replicate-complete order ---------------------------------------------------------------------------------------------
manp = dict(MAN, pbs=dict(MAN["pbs"]))
done3 = {(3, i) for i in range(70)}                                       # rep 3 has 70 done (synthetic)
jobs, left = SA.plan_jobs(manp, "refit", 2, done3, set(), {1, 2}, None, order=SA.designated_order(doc, done3, set(), set(), {}))
j1 = [(s["rep"], s["indices"][0]) for s in jobs[0]["slots"]]
check("job 1 = rep 3's 10 remaining indices (70..79) then rep 4's first 14 - replicate-complete, not index-major",
      j1 == [(3, i) for i in range(70, 80)] + [(4, i) for i in range(14)] and jobs[0]["job"] == 3)
j2 = [(s["rep"], s["indices"][0]) for s in jobs[1]["slots"]]
check("job 2 continues rep 4 (14..37); one index per slot, slots 0..23", j2 == [(4, i) for i in range(14, 38)]
      and [s["slot"] for s in jobs[1]["slots"]] == list(range(24)) and all(len(s["indices"]) == 1 for j in jobs for s in j["slots"]))
check("left = everything not in this call (1,040 - 70 - 48)", left == 1040 - 70 - 48)
fast = {(r, i) for r in (20, 23) for i in range(80)}                      # 'fast' replicates already complete change nothing about order
o_f = SA.designated_order(doc, fast, set(), set(), {})
check("completed later replicates are skipped, the earliest unfinished stays first (no selection by speed)", o_f[0] == (3, [0]) and all(r not in (20, 23) for r, _ in o_f))
try:
    SA.plan_jobs(manp, "refit", 1, set(), set(), set(), None)
    check("the refit planner refuses without the designated order", False)
except ValueError:
    check("the refit planner refuses without the designated order", True)

# ---- 4. skipped coordinates and the admission check --------------------------------------------------------------------------
flight4 = {(3, 0), (3, 1), (24, 5)}; done4 = {(3, 2), (24, 6)}; claimed4 = {(24, 5), (24, 6), (24, 7)}
o4 = [(r, i[0]) for r, i in SA.designated_order(doc, done4, flight4, claimed4, {})]
check("done and in-flight skipped; the first job starts at 3/3; the claimed-but-free 24/7 is plannable, 24/5 (live) and 24/6 (done) not",
      o4[0] == (3, 3) and (3, 0) not in o4 and (3, 2) not in o4 and (24, 7) in o4 and (24, 5) not in o4 and (24, 6) not in o4)


def job(*coords):
    return [{"job": 50, "slots": [{"slot": k, "rep": r, "indices": [i]} for k, (r, i) in enumerate(coords)]}]


dp = lambda jobs, exc={}: SA.designated_problem(jobs, doc, done4, flight4, claimed4, exc, part)
check("admission check: a plan of free designated coordinates passes", dp(job((3, 3), (3, 4), (24, 7))) == "")
for label, c in (("a done coordinate", (3, 2)), ("an in-flight coordinate", (3, 0)), ("index 80", (3, 80)), ("index 199", (3, 199)),
                 ("a rep outside S (rep 6)", (6, 0)), ("an unclaimed EC2-designated coordinate", (25, 0)),
                 ("a crash-excluded coordinate", (4, 9))):
    check(f"admission check refuses {label}", dp(job((3, 3), c), {(4, 9): [{}]}) != "")
check("admission check refuses two indices in one slot", SA.designated_problem([{"job": 50, "slots": [{"slot": 0, "rep": 3, "indices": [3, 4]}]}],
                                                                                doc, set(), set(), set(), {}) != "")

# ---- 5. the crash rule -------------------------------------------------------------------------------------------------------
E48 = dict(queue="serial", cores=24, walltime_s=172800.0, mem_gb=120, nodetype="haswell_reg", deadline_reserve_s=1800)
E30 = dict(E48, walltime_s=108000.0)


def sdisp(jid, crashed):
    return {"slot_disposition": {"kind": SA.CRASH_KIND, "job_id": jid,
                                  "slots": [dict(slot=k, rep=r, indices=[i], signal="Segmentation fault") for k, (r, i) in enumerate(crashed)]}}


REAL_PATTERN = {"13": [(83, 2)], "14": [(83, 2)], "17": [(83, 2)], "20": [(43, 4)], "28": [(25, 6)], "30": [(83, 2), (43, 4), (81, 6)], "33": [(55, 7)]}
rcpt = {"jobs": {n: dict(sdisp(f"75{n}.sched01", c), state="F") for n, c in REAL_PATTERN.items()}}
rcpt["jobs"]["12"] = dict(state="F", exit=0)                              # an ordinary job carries no crash
hist = SA.crash_history(rcpt, lambda n: E48)
check("crash history from the dispositions: 83/2 x4 (jobs 13,14,17,30), 43/4 x2 (20,30), 25/6, 81/6, 55/7 x1",
      {k: [x["job"] for x in v] for k, v in hist.items()} == {(83, 2): [13, 14, 17, 30], (43, 4): [20, 30], (25, 6): [28], (81, 6): [30], (55, 7): [33]})
exc = SA.crash_excluded(hist, E48)
check("two same-envelope crashes exclude: exactly 83/2 and 43/4", sorted(exc) == [(43, 4), (83, 2)])
claimed5 = {(83, 2), (43, 4), (25, 6), (55, 7), (81, 6)}
o5 = {(r, i[0]) for r, i in SA.designated_order(doc, set(), set(), claimed5, exc)}
check("the ordinary planner never issues 83/2 or 43/4 again; single-crash 25/6 and 55/7 stay plannable (Lengau claims)",
      (83, 2) not in o5 and (43, 4) not in o5 and (25, 6) in o5 and (55, 7) in o5 and (81, 6) not in o5)
view = SA.designated_view(doc, set(), {(83, 2)}, claimed5, hist, E48)
check("view: rescue-pending lists 43/4 (2) and 83/2 (4, its current attempt running), never 81/6 (outside S, listed apart)",
      [(x["coordinate"], x["crashes"], x["attempt_running"]) for x in view["rescue_pending"]] == [("43/4", 2, False), ("83/2", 4, True)]
      and view["crash_excluded_outside_set"] == [] and "DISABLED" in view["rescue_route"])
hist30 = SA.crash_history(rcpt, lambda n: E30 if int(n) < 17 else E48)  # 83/2's jobs 13, 14 at another envelope
check("same-envelope only: 83/2 with two crashes at 30 h and two at 48 h is excluded for 48 h; 43/4 too; a 30 h-only pair would not be",
      sorted(SA.crash_excluded(hist30, E48)) == [(43, 4), (83, 2)]
      and sorted(SA.crash_excluded(SA.crash_history({"jobs": {"13": rcpt["jobs"]["13"], "14": rcpt["jobs"]["14"]}}, lambda n: E30), E48)) == [])
check("an attempt of unknown envelope counts (fail closed)", sorted(SA.crash_excluded(SA.crash_history(rcpt, lambda n: None), E48)) == [(43, 4), (83, 2)])
check("one crash is not enough", SA.crash_excluded({(3, 1): [dict(job=1, envelope=list(SA.env_key(E48)))]}, E48) == {})
check("a held/ordinary job without a disposition never adds a crash (counts only from dispositions)",
      SA.crash_history({"jobs": {"9": dict(state="F", exit=4, runner_exit=4)}}, lambda n: E48) == {})
check("the rescue route is declared and refuses while disabled", "DISABLED" in SA.rescue_route_problem(doc))
check("the rescue route refuses even if a declaration said enabled (no v16 implementation)",
      SA.rescue_route_problem(dict(doc, rescue=dict(enabled=True, resources={"cores": 12}))) != "")

# ---- 6. old history untouched ------------------------------------------------------------------------------------------------
def tree_digest(root):
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True)):
        if os.path.isfile(p):
            h.update(os.path.relpath(p, root).encode()); h.update(open(p, "rb").read())
    return h.hexdigest()


import types
if "row19_shard" not in sys.modules:                                       # evidence() imports the worker (jax) even with validate=False;
    try:                                                                   # its validation is not under test here, so a stub stands in on the Mac
        import row19_shard  # noqa: F401
    except ImportError:
        sys.modules["row19_shard"] = types.ModuleType("row19_shard")
D6 = tempfile.mkdtemp(); root6 = os.path.join(D6, "root"); camp6 = os.path.join(D6, "campaign")
for sub in ("plans", "records", "status", "gate", "timing"):
    os.makedirs(os.path.join(root6, sub))
os.makedirs(camp6)
OLD = [dict(job=1, token="t1", slots=[dict(slot=0, rep=6, indices=[0]), dict(slot=1, rep=3, indices=[150]), dict(slot=2, rep=25, indices=[1])]),
       dict(job=2, token="t2", slots=[dict(slot=0, rep=7, indices=[1]), dict(slot=1, rep=3, indices=[0])])]
for p in OLD:
    json.dump(p, open(os.path.join(root6, "plans", f"job_{p['job']}.json"), "w"))
for r, i in ((6, 0), (3, 150), (25, 1)):
    os.makedirs(os.path.join(root6, "records", f"rep{r}"), exist_ok=True)
    json.dump(dict(x=1), open(os.path.join(root6, "records", f"rep{r}", f"rec_{i:03d}.json"), "w"))
json.dump({"cap_core_h": 60000.0, "entries": {
    "a": dict(kind="shard", rep=1, job_id="1.s", token="t1", state="settled", settled_core_h=500.0, runner_exit=0),
    "b": dict(kind="shard", rep=2, job_id="2.s", token="t2", state="live", reserved_core_h=1152.0)}}, open(os.path.join(camp6, "budget.json"), "w"))
man6 = dict(MAN, storage=dict(root=root6, campaign=camp6))
before = tree_digest(D6)
done6, flight6, used6, probs6 = SA.evidence(man6, "refit", validate=False)
_d, claimed6, cp6 = RP.lengau_claims(man6)
o6 = SA.designated_order(doc, done6, flight6, claimed6, {})
jobs6, _ = SA.plan_jobs(man6, "refit", 3, done6, flight6, used6, None, order=o6)
view6 = SA.designated_view(doc, done6, flight6, claimed6, {}, E48)
check("history outside the set is still evidence (done 6/0, 3/150; in flight 7/1) and still a claim (6/0, 3/150, 7/1)",
      {(6, 0), (3, 150)} <= done6 and (7, 1) in flight6 and {(6, 0), (3, 150), (7, 1)} <= claimed6 and not probs6 and not cp6)
check("history outside the set is never planned; 25/1 (done, claimed, EC2 rep) neither; 3/0 (live) neither; new jobs number from 3",
      all((s["rep"], s["indices"][0]) not in {(6, 0), (3, 150), (7, 1), (25, 1), (3, 0)} for j in jobs6 for s in j["slots"]) and jobs6[0]["job"] == 3)
check("the view keeps outside-set history visible (done 2, in flight 1) without crediting it to S x 0..79",
      view6["outside_set_history"] == dict(done=2, in_flight=1) and view6["done"] == 1 and view6["in_flight"] == 1)
check("planning and the view leave the root and the ledger byte-identical (no deletion, no relabel)", tree_digest(D6) == before)

# ---- 7. the CLI wiring (dry run) -------------------------------------------------------------------------------------------
def cli_fixture():
    d = tempfile.mkdtemp(); root = os.path.join(d, "root"); camp = os.path.join(d, "campaign")
    for sub in ("plans", "records", "status", "gate", "timing"):
        os.makedirs(os.path.join(root, sub))
    os.makedirs(camp)
    ents = {}
    for n in range(1, 4):                                                  # three old index-major jobs, the third crashed 3/1
        pl = dict(job=n, token=f"t{n}", slots=[dict(slot=k, rep=S[k], indices=[n - 1]) for k in range(24)])
        json.dump(pl, open(os.path.join(root, "plans", f"job_{n}.json"), "w"))
        ents[str(n)] = dict(kind="shard", rep=n, job_id=f"{n}.s", token=f"t{n}", state="settled", settled_core_h=500.0, runner_exit=0)
    ents["3"]["runner_exit"] = 4
    json.dump({"cap_core_h": 60000.0, "entries": ents}, open(os.path.join(camp, "budget.json"), "w"))
    man = dict(MAN, storage=dict(root=root, campaign=camp), shard=dict(MAN["shard"], toolchain=os.path.join(d, "tc"), clone=os.path.join(d, "clone")))
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w"))
    return d, root, camp, man, mp


def receipt(root, jobs, stamp="20261020T000000Z"):
    p = os.path.join(root, "gate", f"watch_refit_{stamp}.json"); json.dump(dict(schema="row19-screen-watch-1", jobs=jobs), open(p, "w")); return p


def run(argv, mp, gate=""):
    SA.PG.programme_lock = lambda f: contextlib.nullcontext(); SA.PG.programme_funding = lambda man: {}
    SA.partition = lambda man, mpath: None; SA.activation_problem_v10 = lambda *a: ""
    SA.gate_problem = lambda *a, **k: gate; SA.pin_problems = lambda *a: []
    SA.designated = lambda man, mpath: (doc, "")
    SA.resolve_envelope = lambda man, mpath, role, n: (dict(E48, source="policy"), "")
    SA.evidence = lambda man, role, validate=True: REAL_EVIDENCE(man, role, validate=False)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = SA.main(["--manifest", mp, "--role", "refit"] + argv)
    return rc, out.getvalue()


REAL_EVIDENCE = SA.evidence; REAL = dict(designated=SA.designated, resolve_envelope=SA.resolve_envelope, gate_problem=SA.gate_problem)
d, root, camp, man, mp = cli_fixture()
receipt(root, {"1": {}, "2": {}, "3": sdisp("3.s", [(3, 1)])})
rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("dry run: one job, the gate would admit (one crash of 3/1 is not enough to exclude it)", rc == 0 and "would admit" in out)
plan_line = [l for l in out.splitlines() if l.strip().startswith("job 4:")]
check("dry run: job 4 starts at rep 3 (replicate-complete), slot 0 rep 3 [0]", plan_line and "slot 0 rep 3 [0]" in plan_line[0] and "slot 1 rep 3 [1]" in plan_line[0])
check("dry run: the designated summary line names 4,800 coordinates and the receipt it read the crash history from",
      "designated S x 0..79" in out and "4800 coordinates" in out and "watch_refit_20261020T000000Z.json" in out)
receipt(root, {"1": {}, "2": {}, "3": sdisp("3.s", [(3, 1)])}, stamp="20261020T000001Z")
receipt(root, {"1": {}, "2": sdisp("2.s", [(3, 1)]), "3": sdisp("3.s", [(3, 1)])}, stamp="20261020T000002Z")
rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("dry run: two same-envelope crashes of 3/1 -> RESCUE-PENDING printed, 3/1 not planned",
      "RESCUE-PENDING 3/1: 2 same-envelope crash(es) in jobs [2, 3]" in out and "rep 3 [1]" not in [l for l in out.splitlines() if "job 4:" in l][0])
rc, out = run(["--jobs", "2", "--dry-run"], mp)
check("first new-order job alone: --jobs 2 -> the gate would REFUSE ('ALONE')", rc == 0 and "would REFUSE" in out and "ALONE" in out)
os.remove(os.path.join(root, "gate", "watch_refit_20261020T000002Z.json"))
receipt(root, {"1": {}, "2": {}, "3": {}}, stamp="20261020T000003Z")       # the HELD job 3 without its disposition
rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("HELD accounting: a runner-exit-4 job without a disposition in the planning receipt -> HELD", rc == 2 and "HELD" in out and "crash history unknown" in out)
for p in glob.glob(os.path.join(root, "gate", "watch_*.json")):
    os.remove(p)
rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("no receipt -> HELD (crash history not establishable)", rc == 2 and "no readable gate receipt" in out)
receipt(root, {"1": {}, "2": {}, "3": sdisp("3.s", [(3, 1)])}, stamp="20261020T000004Z")


def swap_gate(*a, **k):                                                    # a newer receipt lands while the gate runs
    receipt(root, {"1": {}, "2": {}, "3": sdisp("3.s", [(3, 1)])}, stamp="20261020T000005Z"); return ""


rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("the same receipt for planning and the gate -> would admit", "would admit" in out)
SA.gate_problem = swap_gate
out2 = io.StringIO()
with contextlib.redirect_stdout(out2):
    rc2 = SA.main(["--manifest", mp, "--role", "refit", "--jobs", "1", "--dry-run"])
check("a newer receipt between planning and the gate -> would REFUSE (one receipt for both)", "newer receipt arrived" in out2.getvalue())
rc, out = run(["--rescue"], mp)
check("--rescue -> REFUSED, the route is declared but DISABLED", rc == 2 and "DISABLED" in out)
json.dump(dict(job=4, token="t4", order=SA.ORDER_MARK, designated_sha256=doc["_sha256"], slots=[dict(slot=0, rep=3, indices=[0])]),
          open(os.path.join(root, "plans", "job_4.json"), "w"))
for p in glob.glob(os.path.join(root, "gate", "watch_*.json")):
    os.remove(p)
receipt(root, {"1": {}, "2": {}, "3": sdisp("3.s", [(3, 1)]), "4": {}}, stamp="20261020T000006Z")
led = json.load(open(os.path.join(camp, "budget.json")))
led["entries"]["4"] = dict(kind="shard", rep=4, job_id="4.s", token="t4", state="live", reserved_core_h=1152.0)
json.dump(led, open(os.path.join(camp, "budget.json"), "w"))
rc, out = run(["--jobs", "1", "--dry-run"], mp)
check("a new-order job exists and no scale-up is adopted -> would REFUSE (scale-up held)", "would REFUSE" in out and "scale-up is held" in out)
check("the existing new-order job's coordinate (3/0, in flight) is not re-planned", "slot 0 rep 3 [0]" not in out)
os.makedirs(os.path.join(T, "reviews"), exist_ok=True)
check("--adopt-scaleup refuses while the first new-order job is not SETTLED",
      "not SETTLED" in SA.adopt_scaleup(man, mp, "reviews/none.md") or "not tracked" in SA.adopt_scaleup(man, mp, "reviews/none.md"))
g = dict(schema=SA.SCALEUP_SCHEMA, designated_sha256=doc["_sha256"], first_job=4, job_id="4.s", plan_sha256="0" * 64,
         record_path="reviews/x.md", record_sha256="0" * 64)
json.dump(g, open(os.path.join(root, "gate", "scaleup_refit_v16.json"), "w"))
check("a scale-up gate file whose record is not tracked/unmodified refuses", "not tracked" in SA.scaleup_problem(man, doc, 3))
SA.designated, SA.resolve_envelope, SA.gate_problem = REAL["designated"], REAL["resolve_envelope"], REAL["gate_problem"]

# ---- 8. replay on the REAL local receipt and live snapshot (skipped when absent) --------------------------------------------
RC = os.path.join(CHPC, "results", "row19_screen", "receipts", "watch_refit_20261017T170047Z.json")
VF = os.path.join(CHPC, "results", "row19_screen", "receipts", "verify_refit_20261017T170047Z.json")
LV = os.path.join(CHPC, "results", "row19_screen", "live", "refit")
if all(os.path.exists(p) for p in (RC, VF, LV)):
    rc_ = json.load(open(RC)); vf = json.load(open(VF)); ledger = json.load(open(os.path.join(LV, "campaign", "budget.json")))
    hist_r = SA.crash_history(rc_, lambda n: SA.resolve_envelope(MAN, MAN_PATH, "refit", n)[0])
    counts = {f"{r}/{i}": len(a) for (r, i), a in hist_r.items()}
    print("   real crash history:", counts)
    check("REAL 17 Oct receipt: 83/2 crashed 4 times (jobs 13, 14, 17, 30), 43/4 twice (20, 30), from the dispositions",
          [x["job"] for x in hist_r[(83, 2)]] == [13, 14, 17, 30] and [x["job"] for x in hist_r[(43, 4)]] == [20, 30])
    env_next = SA.resolve_envelope(MAN, MAN_PATH, "refit", 46)[0]
    check("REAL: the next ordinary envelope is 24 x 48 h and every crash ran in it", SA.env_key(env_next) == ("serial", 24, 172800.0, 120, "haswell_reg", 1800)
          and all(x["envelope"] == list(SA.env_key(env_next)) for a in hist_r.values() for x in a))
    check("REAL: crash-excluded = exactly 43/4 and 83/2", sorted(SA.crash_excluded(hist_r, env_next)) == [(43, 4), (83, 2)])
    R.MANIFEST_PATH = MAN_PATH
    view_r, why_r = R.designated_report(MAN, vf, ledger, LV, rc_["jobs"], MAN_PATH)
    print("   real designated view:", {k: view_r[k] for k in ("designated", "done", "in_flight", "lengau_plannable", "ec2_waiting_unclaimed",
                                                             "outside_set_history", "rescue_pending")} if view_r else why_r)
    check("REAL status view: rescue-pending 43/4 (2) and 83/2 (4), both with their job-37 attempt running",
          why_r == "" and [(x["coordinate"], x["crashes"], x["attempt_running"]) for x in view_r["rescue_pending"]] == [("43/4", 2, True), ("83/2", 4, True)])
    check("REAL: done + in flight (not done) + Lengau plannable + EC2 unclaimed + idle rescue-pending = 4,800 (each coordinate once)",
          view_r["done"] + view_r["in_flight"] + view_r["lengau_plannable"] + view_r["ec2_waiting_unclaimed"]
          + len([x for x in view_r["rescue_pending"] if not x["attempt_running"]]) == 4800)
    check("REAL: the first 24 planned coordinates are rep 3's lowest free indices (replicate-complete)",
          view_r["next_coordinates"][0].startswith("3/") and all(c.split("/")[0] in ("3", "4") for c in view_r["next_coordinates"]))
else:
    print("skip REAL replay (needs chpc/results/row19_screen receipts of 20261017T170047Z and the live snapshot)")

SA.controls = REAL_CONTROLS
print(f"\n{'ALL OK' if not fails else f'{len(fails)} FAILED'}")
sys.exit(1 if fails else 0)

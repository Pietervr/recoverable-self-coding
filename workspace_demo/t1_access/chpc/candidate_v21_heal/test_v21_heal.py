"""Controls v21 CANDIDATE (NOT adopted): tests of the FUNDING ROUTE - CSCI1913 first, then HEAL1922, per admission, side by side
(owner ruling 26 Oct 2026; chpc/candidate_v21_heal/DESIGN_v21.md). Mac, pure python; private temporary worlds only; nothing live
is touched (checked at the end).

  A  programme_gate REVISION 5: the route (validation), entry_programme (the no-field rule)
  B  per-programme accounting: old entries are CSCI1913; HEAL1922 never counted against CSCI1913 and vice versa; the REAL local
     ledger copy counts exactly as REVISION 4 did; settlement credits the entry's own programme through every ledger step
  C  route_choice: CSCI1913 while it fits, HEAL1922 when CSCI1913 committed + proposal > 100,000 (the boundary), refusal when
     neither fits, per-job assignment inside one admission, a MIXED set of live entries, back to CSCI1913 when a settlement frees it
  D  the admission end to end (row19_screen_admit REVISION 21 main(), its science/receipt gates stubbed, the funding, ledger,
     cap, sub-envelope, plan, PBS script and a fake qsub REAL): the PBS script carries the chosen -P, the entry and the plan carry
     it, refusal reserves nothing, a failed charge holds before qsub, the dry run reserves nothing
  E  the programme lock still serialises: an admission and a settlement wait for a held lock; the settle wrapper logs both
     programmes before and after
  F  controls v21: the build, exactly two pins + sub-envelope + funding_route change, versions 1-20 byte-equal, the route resolves
     against the REAL manifest funding, Python 3.7 grammar, the live tree untouched

    python3 chpc/candidate_v21_heal/test_v21_heal.py          (from workspace_demo/t1_access)"""
import ast, copy, fcntl, hashlib, importlib.util, io, json, os, shutil, subprocess, sys, tempfile, time, contextlib

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):                 # the candidate modules must be what `import ...` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


LIVE = ("chpc/programme_gate.py", "chpc/row19_screen_admit.py", "chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json",
        "chpc/row19_screen_budget.json", "chpc/row19_ledger.py", "chpc/row19_screen_manifest.json")
LIVE_BEFORE = {r: sha(os.path.join(T1, r)) for r in LIVE}
PG = load("programme_gate", os.path.join(CAND, "programme_gate.py"))
PG20 = load("programme_gate_v20", os.path.join(CHPC, "programme_gate.py"))
import row19_ledger as LG                                                  # live, pinned by the manifest, unchanged
import row19_partition as RP                                               # live (stubbed in D only)
SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))

fails = []; npass = [0]


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name, flush=True)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json")
MAN = json.load(open(MAN_PATH))
CTL21_PATH = os.path.join(CAND, "row19_screen_controls.json"); CTL21 = json.load(open(CTL21_PATH))
ROUTE = CTL21["versions"][-1]["funding_route"]
TMP = tempfile.mkdtemp(prefix="v21_heal_test_")
CORE_H = 24 * 30.0                       # a 24-core x 30 h job (the manifest envelope); the live policy reserves 1,152 (48 h), see C11


def raises(f, *a):
    try:
        f(*a)
    except RuntimeError as e:
        return str(e) or "RuntimeError"
    return ""


def ledger(dirname, entries, cap=181000.0):
    d = os.path.join(TMP, dirname); os.makedirs(d, exist_ok=True)
    st = dict(cap_core_h=cap, entries={})
    for k, e in enumerate(entries):
        tok = "%s%04d" % (dirname[:4], k)
        x = dict(token=tok, kind="shard", rep=k + 1, root="/r", cores=24, walltime_s=108000.0, reserved_core_h=CORE_H, attempt=1,
                 state=e.get("state", "settled"), job_id=None if e.get("state") == "reserved" else "%s%d.sched01" % (dirname[:4], k), created=time.time() + k, note="")
        if x["state"] == "settled":
            x["settled_core_h"] = e.get("charge", 600.0)
        if "programme" in e:
            x["programme"] = e["programme"]
        st["entries"][tok] = x
    json.dump(st, open(os.path.join(d, "budget.json"), "w"), indent=1, sort_keys=True)
    return d


def funding(camps, route=ROUTE, other=6.0, alloc=100000.0):
    f = dict(programme="CSCI1913", allocation_core_h=alloc, other_settled_core_h=other, campaigns=list(camps),
             lock=os.path.join(TMP, "programme_admission.lock"))
    if route is not None:
        f["route"] = copy.deepcopy(route)
    return f


# ---- A. the route ----------------------------------------------------------------------------------------------------------
print("# A. programme_gate REVISION 5: the route")
f0 = funding([], route=None)
check("A1 no declared route -> the funding block's one programme (every earlier version's behaviour)",
      PG.route_of(f0) == [dict(programme="CSCI1913", allocation_core_h=100000.0, other_settled_core_h=6.0)])
r = PG.route_of(funding([]))
check("A2 the v21 route resolves to CSCI1913 100,000 (other 6) then HEAL1922 100,000 (other 0.01)",
      [(x["programme"], x["allocation_core_h"], x["other_settled_core_h"]) for x in r] == [("CSCI1913", 100000.0, 6.0), ("HEAL1922", 100000.0, 0.01)])
bad = copy.deepcopy(ROUTE); bad[0]["allocation_core_h"] = 120000.0
check("A3 refused: the route's first programme disagrees with the funding block's allocation (one source per number)",
      "first programme" in raises(PG.route_of, funding([], route=bad)))
bad = copy.deepcopy(ROUTE); bad.reverse()
check("A4 refused: a route that does not start with the manifest's programme", "first programme" in raises(PG.route_of, funding([], route=bad)))
bad = copy.deepcopy(ROUTE) + [copy.deepcopy(ROUTE[1])]
check("A5 refused: a programme listed twice", "twice" in raises(PG.route_of, funding([], route=bad)))
for k, v in (("allocation_core_h", float("inf")), ("allocation_core_h", 0.0), ("allocation_core_h", True), ("other_settled_core_h", -1.0)):
    bad = copy.deepcopy(ROUTE); bad[1][k] = v
    check(f"A6 refused: HEAL1922 {k} = {v!r}", "finite" in raises(PG.route_of, funding([], route=bad)))
bad = copy.deepcopy(ROUTE); bad[1]["programme"] = "heal 1922"
check("A7 refused: a malformed programme code", "programme code" in raises(PG.route_of, funding([], route=bad)))
check("A8 refused: an empty route", "non-empty" in raises(PG.route_of, funding([], route=[])))
check("A9 entry_programme: no field -> CSCI1913 by definition; HEAL1922 field -> HEAL1922",
      PG.entry_programme({}, r) == "CSCI1913" and PG.entry_programme({"programme": "HEAL1922"}, r) == "HEAL1922")
check("A10 entry_programme refuses a code outside the route, a non-string and None",
      all(raises(PG.entry_programme, {"programme": v}, r) for v in ("LHM001", 1922, None, "")))

# ---- B. per-programme accounting -------------------------------------------------------------------------------------------
print("# B. per-programme accounting")
old = ledger("old", [{"charge": 575.9}, {"charge": 641.4}, {"state": "live"}])
f = funding([old])
tot, det = PG.committed_by_programme(f)
check("B1 old entries (no field) are CSCI1913: 575.9 + 641.4 + 720 live + other 6; HEAL1922 0.01 (its other use only)",
      abs(tot["CSCI1913"] - (575.9 + 641.4 + 720 + 6)) < 1e-9 and abs(tot["HEAL1922"] - 0.01) < 1e-12)
check("B2 committed_core_h (the first programme) equals REVISION 4's count on a ledger without the field",
      abs(PG.committed_core_h(f)[0] - PG._committed_core_h_r4(f)[0]) < 1e-9 and abs(PG.committed_core_h(f)[0] - PG20.committed_core_h(f)[0]) < 1e-9)
real = os.path.join(CHPC, "results", "row19_screen", "live", "refit", "campaign")
if os.path.exists(os.path.join(real, "budget.json")):
    fr = funding([real])
    a, b = PG.committed_core_h(fr)[0], PG20.committed_core_h(fr)[0]
    check(f"B3 the REAL local refit ledger copy ({len(json.load(open(os.path.join(real, 'budget.json')))['entries'])} entries) counts exactly as v20: {a:.2f} = {b:.2f}, HEAL1922 none",
          abs(a - b) < 1e-9 and PG.committed_by_programme(fr)[0]["HEAL1922"] == 0.01)
else:
    check("B3 the REAL local refit ledger copy exists (chpc/results/row19_screen/live/refit/campaign)", False)
mixed = ledger("mixed", [{"charge": 600.0}, {"state": "live"}, {"state": "live", "programme": "HEAL1922"},
                         {"charge": 650.0, "programme": "HEAL1922"}, {"state": "bound", "programme": "CSCI1913"}])
tot, det = PG.committed_by_programme(funding([mixed]))
check("B4 a HEAL1922 entry is never counted against CSCI1913: CSCI1913 = 600 + 720 + 720 + 6", abs(tot["CSCI1913"] - 2046.0) < 1e-9)
check("B5 a CSCI1913 entry (field or none) is never counted against HEAL1922: HEAL1922 = 720 + 650 + 0.01", abs(tot["HEAL1922"] - 1370.01) < 1e-9)
check("B6 the per-campaign detail splits by programme", det["mixed"] == {"CSCI1913": 2040.0, "HEAL1922": 1370.0})
check("B7 committed_core_h / funding_problem keep the FIRST programme's meaning (the wrapper for bank/shard/slice charges CSCI1913)",
      abs(PG.committed_core_h(funding([mixed]))[0] - 2046.0) < 1e-9 and PG.funding_problem(funding([mixed]), 97954.0) == ""
      and "> the CSCI1913 allocation" in PG.funding_problem(funding([mixed]), 97955.0))
bad = ledger("badprog", [{"charge": 1.0, "programme": "LHM001"}])
check("B8 an entry naming a programme outside the route cannot be counted: refused", "LHM001" in raises(PG.committed_by_programme, funding([bad])))
bad2 = ledger("badtype", [{"charge": 1.0}]); st = json.load(open(os.path.join(bad2, "budget.json")))
list(st["entries"].values())[0]["programme"] = None; json.dump(st, open(os.path.join(bad2, "budget.json"), "w"))
check("B9 a null programme field refuses (only ABSENT means CSCI1913)", raises(PG.committed_by_programme, funding([bad2])) != "")
# settlement through every real ledger step credits the entry's own programme
sc = os.path.join(TMP, "settle_camp"); L = LG.CampaignLedger(sc, 181000.0)
tok_c, _ = L.reserve("shard", 1, 24, 108000.0, "/r", "csci job")
tok_h, _ = L.reserve("shard", 2, 24, 108000.0, "/r", "heal job")
SA.charge_programme(L, tok_c, "CSCI1913"); SA.charge_programme(L, tok_h, "HEAL1922")
fs = funding([sc])
b0 = PG.committed_by_programme(fs)[0]
L.bind(tok_h, "9001.sched01"); L.runner_start(tok_h, "9001.sched01", "shard", 2, "/r", 24, 108000.0); L.runner_end(tok_h, 86400.0, 0)
mid = PG.committed_by_programme(fs)[0]
L.settle("9001.sched01", 90000.0, 24, "test settle: qstat -xf walltime 25:00:00")
b1 = PG.committed_by_programme(fs)[0]
e_h = json.load(open(os.path.join(sc, "budget.json")))["entries"][tok_h]
check("B10 the programme field survives bind, runner start, runner end and settlement (row19_ledger unchanged)",
      e_h.get("programme") == "HEAL1922" and e_h["state"] == "settled")
check("B11 settlement credits the entry's OWN programme: HEAL1922 720 -> 600 settled; CSCI1913 unchanged at 720 + 6",
      abs(b0["HEAL1922"] - 720.01) < 1e-9 and abs(mid["HEAL1922"] - 720.01) < 1e-9 and abs(b1["HEAL1922"] - 600.01) < 1e-9
      and abs(b0["CSCI1913"] - 726.0) < 1e-9 and abs(b1["CSCI1913"] - 726.0) < 1e-9)
check("B12 charge_programme refuses a bound entry and a second, different programme",
      raises(SA.charge_programme, L, tok_h, "HEAL1922") != "" and raises(SA.charge_programme, L, tok_c, "HEAL1922") != "")
check("B13 charge_programme is idempotent for the same programme on the fresh reservation", SA.charge_programme(L, tok_c, "CSCI1913") == "CSCI1913")

# ---- C. route_choice ---------------------------------------------------------------------------------------------------------
print("# C. route_choice")


def world_at(csci_settled, heal_settled=0.0, csci_live=0, heal_live=0, name=None):
    ents = []
    if csci_settled:
        ents.append({"charge": csci_settled})
    if heal_settled:
        ents.append({"charge": heal_settled, "programme": "HEAL1922"})
    ents += [{"state": "live"}] * csci_live + [{"state": "live", "programme": "HEAL1922"}] * heal_live
    return funding([ledger(name or "w%d" % int(time.time() * 1e6 % 1e9), ents)])


fw = world_at(80856.2 - 6.0)
check("C1 CSCI1913 is chosen while it fits (today: 80,856.2 committed + 720)", PG.route_choice(fw, [CORE_H]) == (["CSCI1913"], ""))
fw = world_at(100000.0 - 6.0 - 720.0)
check("C2 the boundary: CSCI1913 committed + proposal = 100,000 exactly still goes to CSCI1913", PG.route_choice(fw, [CORE_H])[0] == ["CSCI1913"])
fw = world_at(100000.0 - 6.0 - 719.0)
check("C3 HEAL1922 is chosen when CSCI1913 committed + proposal > 100,000 (by 1 core-hour)", PG.route_choice(fw, [CORE_H]) == (["HEAL1922"], ""))
fw = world_at(100000.0 - 6.0 - 100.0, heal_settled=100000.0 - 0.01 - 100.0)
pr, why = PG.route_choice(fw, [CORE_H])
check("C4 refusal when neither fits (both within 100 core-h of their allocation); the reason names both programmes",
      pr == [] and "no programme of the route fits" in why and "CSCI1913" in why and "HEAL1922" in why)
fw = world_at(100000.0 - 6.0 - 1000.0)
check("C5 per-job inside one admission: 3 jobs with room for 1 on CSCI1913 -> CSCI1913, HEAL1922, HEAL1922",
      PG.route_choice(fw, [CORE_H] * 3)[0] == ["CSCI1913", "HEAL1922", "HEAL1922"])
fw = world_at(100000.0 - 6.0 - 1000.0, heal_settled=100000.0 - 0.01 - 1000.0)
pr, why = PG.route_choice(fw, [CORE_H] * 3)
check("C6 refusal names the job that fits nowhere (job 3: one on each programme, then none)", pr == [] and "job 3" in why)
# (d) the owner's requirement: a MIXED set of live entries admitting the next job correctly
fw = world_at(100000.0 - 6.0 - 720.0 * 10 - 100.0, csci_live=10, heal_live=3, name="mixed_live")
tot, _ = PG.committed_by_programme(fw)
check("C7 mixed live (10 CSCI1913 live + 3 HEAL1922 live): CSCI1913 is 100 core-h short of a job -> the next job goes to HEAL1922",
      PG.route_choice(fw, [CORE_H])[0] == ["HEAL1922"] and abs(tot["HEAL1922"] - (3 * 720 + 0.01)) < 1e-9)
# one CSCI1913 live job settles below its reservation (720 -> 575): CSCI1913 now has 245 + 100 free -> still not a job; after
# four such settlements it has 680 free... after the fifth, 825 >= 720: the next job goes BACK to CSCI1913 (first that fits)
led_p = os.path.join(TMP, "mixed_live", "budget.json"); st = json.load(open(led_p))
cs = [e for e in st["entries"].values() if e["state"] == "live" and "programme" not in e]
seq = []
for k in range(5):
    cs[k]["state"] = "settled"; cs[k]["settled_core_h"] = 575.0; json.dump(st, open(led_p, "w"))
    seq.append(PG.route_choice(fw, [CORE_H])[0][0])
check("C8 settlements below the reservation free CSCI1913 again: the next job goes back to CSCI1913 once it fits "
      f"({' '.join(s[:4] for s in seq)})", seq == ["HEAL1922"] * 4 + ["CSCI1913"])
check("C9 malformed proposals are refused", PG.route_choice(fw, [])[1] != "" and PG.route_choice(fw, [float("nan")])[1] != ""
      and PG.route_choice(fw, [0.0])[1] != "" and PG.route_choice(fw, [True])[1] != "")
fw = world_at(80856.2 - 6.0, name="real_today")
pr, why = PG.route_choice(fw, [1152.0] * 20)
check("C11 today's numbers (CSCI1913 80,856.2 committed, the live 24 x 48 h = 1,152 core-h reservation): 16 jobs fit CSCI1913, "
      f"jobs 17-20 go to HEAL1922 ({pr.count('CSCI1913')} + {pr.count('HEAL1922')})", pr == ["CSCI1913"] * 16 + ["HEAL1922"] * 4 and why == "")
check("C10 an uncountable ledger refuses the route (never a guess)",
      "funding cannot be established" in PG.route_choice(funding([bad]), [CORE_H])[1])

# ---- D. the admission end to end ------------------------------------------------------------------------------------------
print("# D. the admission end to end (row19_screen_admit REVISION 21 main)")
ENV = dict(queue="serial", cores=24, walltime_s=108000.0, mem_gb=120, nodetype="haswell_reg", deadline_reserve_s=1800, source="manifest")
W = os.path.join(TMP, "world"); TC = os.path.join(W, "tc"); CLONE = os.path.join(TC, "rsc_screen"); ROOT = os.path.join(W, "root")
CAMP = os.path.join(W, "campaign"); OTHER = os.path.join(W, "other_campaign")
for d in (os.path.join(CLONE, "workspace_demo", "t1_access", "chpc"), ROOT, os.path.join(W, "bin")):
    os.makedirs(d, exist_ok=True)
PHASES = os.path.join(W, "budget_phases.json")
json.dump({"phases": [{"cap_core_h": 81000.0, "note": "initial", "t": 1.0},
                      {"cap_core_h": 181000.0, "note": "test raise", "t": 2.0, "campaign": CAMP, "pending": False}]}, open(PHASES, "w"))
QSUB_LOG = os.path.join(W, "qsub.log")
open(os.path.join(W, "bin", "qsub"), "w").write('#!/bin/bash\nn=$(( $(cat "%s" 2>/dev/null | wc -l) + 1 ))\ncp "$1" "%s/submitted_$n.pbs"\necho "$1" >> "%s"\necho "77${n}00.sched01"\n'
                                                % (QSUB_LOG, W, QSUB_LOG))
os.chmod(os.path.join(W, "bin", "qsub"), 0o755)
os.environ["PATH"] = os.path.join(W, "bin") + os.pathsep + os.environ["PATH"]
DMAN = copy.deepcopy(MAN)
DMAN["storage"]["root"] = ROOT; DMAN["storage"]["campaign"] = CAMP
DMAN["shard"]["toolchain"] = TC; DMAN["shard"]["clone"] = CLONE
DMAN["budget"]["admission"] = PHASES
DMAN_PATH = os.path.join(CLONE, "workspace_demo", "t1_access", "chpc", "row19_screen_manifest.json")
json.dump(DMAN, open(DMAN_PATH, "w"), indent=1)
LOCK = os.path.join(W, "programme_admission.lock"); open(LOCK, "a").close()


def dfund():
    return dict(programme="CSCI1913", allocation_core_h=100000.0, other_settled_core_h=6.0, campaigns=[OTHER, CAMP], lock=LOCK,
                route=copy.deepcopy(ROUTE))


CTL_D = copy.deepcopy(CTL21); CTL_D["versions"][-1]["sub_envelopes"][0]["campaigns"] = [CAMP]
NEXT = [101]
stubs = dict(evidence=lambda man, role: (set(), set(), {1}, []), partition=lambda man, mp: None,
             activation_problem_v10=lambda man, mp, part: "", designated=lambda man, mp: ({"_sha256": "d" * 64}, ""),
             newest_receipt=lambda man, role: ("watch.json", "s" * 64, {}), held_accounting_problem=lambda *a: "",
             resolve_envelope=lambda man, mp, role, n: (dict(ENV), ""), crash_history=lambda rdoc, f: {}, crash_excluded=lambda h, env: {},
             designated_order=lambda *a: [], designated_view=lambda *a: dict(designated=1, done=0, in_flight=0, lengau_plannable=1,
                                                                            ec2_waiting_unclaimed=0, rescue_pending=[]),
             partition_problem=lambda jobs, part: "", designated_problem=lambda *a: "", scaleup_problem=lambda *a: "",
             controls_problem=lambda: "", seed_domain_problem=lambda man: "", identity_problem=lambda man, reps: "",
             review_problem=lambda *a: "", pin_problems=lambda man, clone: [], controls=lambda: CTL_D)


def plan_jobs(man, role, n_jobs, done, flight, used, part=None, order=None):
    out = []
    for _ in range(n_jobs):
        n = NEXT[0]; NEXT[0] += 1
        out.append({"job": n, "slots": [{"slot": s, "rep": 3 + s, "indices": [n % 80]} for s in range(24)]})
    return out, 0


stubs["plan_jobs"] = plan_jobs
for k, v in stubs.items():
    setattr(SA, k, v)
RP.lengau_claims = lambda man: (None, set(), [])
PG.programme_funding = lambda man: dfund()


def admit(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = SA.main(["--manifest", DMAN_PATH, "--role", "refit"] + list(args))
    return rc, buf.getvalue()


def entries(camp=CAMP):
    p = os.path.join(camp, "budget.json")
    return json.load(open(p))["entries"] if os.path.exists(p) else {}


def nq():
    return len(open(QUAL).read().splitlines()) if os.path.exists(QUAL) else 0


QUAL = QSUB_LOG
# the other CSCI1913 ledgers (bank, shard, slice, orig, S in production): 79,000 settled, no field
ledger("other_campaign", [{"charge": 79000.0 - 6.0}]); shutil.rmtree(OTHER, ignore_errors=True)
shutil.move(os.path.join(TMP, "other_campaign"), OTHER)
LG.CampaignLedger(CAMP, 81000.0)                                         # created at the first phase ...
st = json.load(open(os.path.join(CAMP, "budget.json"))) if os.path.exists(os.path.join(CAMP, "budget.json")) else None
L = LG.CampaignLedger(CAMP, 81000.0)
with L.locked() as s_:
    pass
L.raise_cap(181000.0, "test: the v21 two-phase raise")                   # ... and raised as the migration does
rc, out = admit("--jobs", "1")
e = list(entries().values())
sub = open(os.path.join(W, "submitted_1.pbs")).read() if os.path.exists(os.path.join(W, "submitted_1.pbs")) else ""
plan = json.load(open(os.path.join(ROOT, "plans", "job_101.json"))) if os.path.exists(os.path.join(ROOT, "plans", "job_101.json")) else {}
check("D1 CSCI1913 fits (79,000 committed): job 101 submitted, `#PBS -P CSCI1913`, the entry and the plan carry CSCI1913",
      rc == 0 and len(e) == 1 and e[0].get("programme") == "CSCI1913" and e[0].get("job_id") == "77100.sched01"
      and "#PBS -P CSCI1913\n" in sub and sub.count("#PBS -P") == 1 and plan.get("programme") == "CSCI1913" and "charged to CSCI1913" in out)
if rc != 0:
    print(out[-1500:])
# fill CSCI1913 with nine more live CSCI1913 jobs' worth: 79,000 + 10 x 720 = 86,200; then make it short by settling 'other' high
rc2, out2 = admit("--jobs", "9")
st = json.load(open(os.path.join(OTHER, "budget.json"))); list(st["entries"].values())[0]["settled_core_h"] = 100000.0 - 6.0 - 7200.0 - 500.0
json.dump(st, open(os.path.join(OTHER, "budget.json"), "w"))
rc3, out3 = admit("--jobs", "1")
e = entries()
heal = [x for x in e.values() if x.get("programme") == "HEAL1922"]
csci_live = [x for x in e.values() if x.get("programme") == "CSCI1913" and x["state"] != "settled"]
sub11 = open(os.path.join(W, "submitted_11.pbs")).read() if os.path.exists(os.path.join(W, "submitted_11.pbs")) else ""
check("D2 with 10 CSCI1913 jobs live and CSCI1913 500 core-h short of a job, job 111 is admitted at once on HEAL1922 "
      "(`#PBS -P HEAL1922`); the 10 CSCI1913 entries are untouched",
      rc2 == 0 and rc3 == 0 and len(heal) == 1 and heal[0]["rep"] == 111 and "#PBS -P HEAL1922\n" in sub11 and len(csci_live) == 10
      and all(x["state"] == "bound" for x in csci_live) and "charged to HEAL1922" in out3)
pl = json.load(open(os.path.join(ROOT, "plans", "job_111.json")))
check("D3 the HEAL1922 plan carries programme HEAL1922 and its token", pl.get("programme") == "HEAL1922" and pl.get("token") == heal[0]["token"])
fb = PG.committed_by_programme(dfund())[0]
check(f"D4 per-programme committed after D2: CSCI1913 {fb['CSCI1913']:.0f} (unchanged by the HEAL1922 job), HEAL1922 {fb['HEAL1922']:.2f}",
      abs(fb["CSCI1913"] - (100000.0 - 500.0)) < 1e-6 and abs(fb["HEAL1922"] - 720.01) < 1e-9)
# straddling admission: settle the other ledger lower so CSCI1913 has room for exactly one job, then --jobs 3
st = json.load(open(os.path.join(OTHER, "budget.json"))); list(st["entries"].values())[0]["settled_core_h"] = 100000.0 - 6.0 - 7200.0 - 1000.0
json.dump(st, open(os.path.join(OTHER, "budget.json"), "w"))
rc4, out4 = admit("--jobs", "3")
progs = [json.load(open(os.path.join(ROOT, "plans", f"job_{n}.json"))).get("programme") for n in (112, 113, 114)]
pbs = [open(os.path.join(W, f"submitted_{k}.pbs")).read() for k in (12, 13, 14)]
check("D5 one admission of 3 jobs with room for one on CSCI1913: 112 CSCI1913, 113 and 114 HEAL1922, each script's -P matches",
      rc4 == 0 and progs == ["CSCI1913", "HEAL1922", "HEAL1922"] and all(f"#PBS -P {p}\n" in s for p, s in zip(progs, pbs)))
# neither fits: push HEAL1922 near its allocation through its own settled entry (field) in the other ledger
st = json.load(open(os.path.join(OTHER, "budget.json")))
st["entries"]["heal_big"] = dict(token="heal_big", kind="shard", rep=999, root="/r", cores=24, walltime_s=108000.0, reserved_core_h=720.0,
                                 attempt=1, state="settled", job_id="99.sched01", created=1.0, note="", settled_core_h=100000.0 - 0.01 - 3 * 720.0 - 100.0,
                                 programme="HEAL1922")
json.dump(st, open(os.path.join(OTHER, "budget.json"), "w"))
n_before, q_before = len(entries()), nq()
rc5, out5 = admit("--jobs", "1")
check("D6 neither programme fits: REFUSED by the screen gate, nothing reserved, no qsub",
      rc5 == 2 and "no programme of the route fits" in out5 and len(entries()) == n_before and nq() == q_before)
rc6, out6 = admit("--jobs", "1", "--dry-run")
check("D7 the dry run reports the same refusal and reserves nothing", rc6 == 0 and "would REFUSE" in out6 and len(entries()) == n_before)
del st["entries"]["heal_big"]; json.dump(st, open(os.path.join(OTHER, "budget.json"), "w"))
rc7, out7 = admit("--jobs", "1", "--dry-run")
check("D8 the dry run prints the chosen programme (funding: #PBS -P HEAL1922) and reserves nothing",
      rc7 == 0 and "funding: #PBS -P HEAL1922" in out7 and "would admit" in out7 and len(entries()) == n_before)
real_charge = SA.charge_programme


def boom(*a):
    raise RuntimeError("simulated interruption")


SA.charge_programme = boom
rc8, out8 = admit("--jobs", "1")
SA.charge_programme = real_charge
stuck = [x for x in entries().values() if x["state"] == "reserved"]
check("D9 a failed programme write HOLDS before the plan and qsub; the reservation stays reserved, unbound, WITHOUT a field "
      "(counted against CSCI1913, the conservative default)",
      rc8 == 1 and "HELD before the plan" in out8 and nq() == q_before and len(stuck) == 1 and "programme" not in stuck[0]
      and not os.path.exists(os.path.join(ROOT, "plans", "job_%d.json" % stuck[0]["rep"])))
SA_pp = SA.programme_problem
check("D10 programme_problem: a script charging another project, two -P lines, an entry or plan without the code all refuse",
      SA_pp("#PBS -P CSCI1913\n", {"programme": "HEAL1922"}, {"programme": "HEAL1922"}, "HEAL1922") != ""
      and SA_pp("#PBS -P HEAL1922\n#PBS -P HEAL1922\n", {"programme": "HEAL1922"}, {"programme": "HEAL1922"}, "HEAL1922") != ""
      and SA_pp("#PBS -P HEAL1922\n", {}, {"programme": "HEAL1922"}, "HEAL1922") != ""
      and SA_pp("#PBS -P HEAL1922\n", {"programme": "HEAL1922"}, {}, "HEAL1922") != ""
      and SA_pp("#PBS -P HEAL1922\n", {"programme": "HEAL1922"}, {"programme": "HEAL1922"}, "HEAL1922") == "")
check("D11 a plan without `programme` (every pre-v21 plan) still builds `#PBS -P CSCI1913` from the manifest",
      "#PBS -P CSCI1913\n" in SA.refit_pbs_script(DMAN, {"job": 5, "slots": [{"slot": 0, "rep": 3, "indices": [0]}]}, "T", 108000.0, "serial", TC, CLONE, "m.json"))
# the ledger cap still counts BOTH programmes: with the cap at 81,000 (no raise) a HEAL1922 job is refused by the cap
L2 = LG.CampaignLedger(os.path.join(W, "capcamp"), 81000.0)
with L2.locked() as s_:
    for k in range(112):
        s_["entries"]["t%d" % k] = dict(token="t%d" % k, kind="shard", rep=k + 1, root="/r", cores=24, walltime_s=108000.0, reserved_core_h=720.0,
                                         attempt=1, state="settled", job_id="c%d" % k, created=1.0, note="", settled_core_h=720.0)
DMAN2 = copy.deepcopy(DMAN); DMAN2["storage"]["campaign"] = os.path.join(W, "capcamp")
json.dump({"phases": [{"cap_core_h": 81000.0, "note": "initial", "t": 1.0}]}, open(os.path.join(W, "phases81.json"), "w"))
DMAN2["budget"]["admission"] = os.path.join(W, "phases81.json")
check("D12 the campaign cap counts every entry of either programme: at 81,000 with 80,640 spent a HEAL1922-bound job is refused by the cap",
      "the campaign cap" in SA.campaign_cap_problem(DMAN2, 720.0))
# ---- E. the lock -------------------------------------------------------------------------------------------------------------
print("# E. the programme lock still serialises every admission and settlement")
child = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time\nfh = open(sys.argv[1], 'a+'); fcntl.flock(fh.fileno(), fcntl.LOCK_EX)\n"
                          "print('held', flush=True); time.sleep(4)", LOCK], stdout=subprocess.PIPE, text=True)
child.stdout.readline()
t0 = time.time(); rc9, out9 = admit("--jobs", "1"); dt = time.time() - t0
child.wait()
check(f"E1 an admission waits for the held programme lock ({dt:.1f} s) and then admits", rc9 == 0 and dt >= 2.5)
src = open(os.path.join(CAND, "row19_screen_admit.py")).read()
body = src[src.index("    with PG.programme_lock(PG.programme_funding(man)), open(os.path.join(root, \"plans\", \".submit.lock\")"):]
check("E2 the admission's planning, route, reservation, charge, plan and qsub all run inside ONE `with PG.programme_lock(...)`",
      all(body.index(k) > 0 for k in ("funding_assignment(man, per_job)", "L.reserve(", "charge_programme(L, token, prog)", 'subprocess.run(["qsub"')))
# the settle wrapper: real PG.main settle (lineage stubbed: the candidate is not adopted), real ledger CLI, the lock held 3 s
hj = [x for x in entries().values() if x.get("programme") == "HEAL1922" and x["state"] == "bound"][0]
PG.lineage_problem = lambda: ""
child = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time\nfh = open(sys.argv[1], 'a+'); fcntl.flock(fh.fileno(), fcntl.LOCK_EX)\n"
                          "print('held', flush=True); time.sleep(3)", LOCK], stdout=subprocess.PIPE, text=True)
child.stdout.readline()
t0 = time.time()
rc10 = PG.main(["settle", "--manifest", DMAN_PATH, "--", sys.executable, os.path.join(CHPC, "row19_ledger.py"), "--campaign", CAMP, "settle",
                "--job-id", hj["job_id"], "--walltime-s", "86400", "--cores", "24", "--note", "test: qstat -xf walltime 24:00:00 F"])
dt = time.time() - t0; child.wait()
log = [json.loads(l) for l in open(os.path.join(W, "programme_admissions.jsonl")).read().splitlines()]
s_ = [x for x in log if x["kind"] == "settle"][-1]
check(f"E3 a settlement through the wrapper waits for the held lock ({dt:.1f} s), settles the HEAL1922 entry and logs both programmes "
      f"(HEAL1922 {s_['by_programme_before']['HEAL1922']:.0f} -> {s_['by_programme_after']['HEAL1922']:.0f}; CSCI1913 unchanged)",
      rc10 == 0 and dt >= 2.0 and abs(s_["by_programme_before"]["HEAL1922"] - s_["by_programme_after"]["HEAL1922"] - 144.0) < 1e-6
      and abs(s_["by_programme_before"]["CSCI1913"] - s_["by_programme_after"]["CSCI1913"]) < 1e-9
      and entries()[hj["token"]]["programme"] == "HEAL1922" and entries()[hj["token"]]["state"] == "settled")

# ---- F. controls v21 -----------------------------------------------------------------------------------------------------------
print("# F. controls v21")
B = load("build_v21", os.path.join(CAND, "build_v21.py"))
base, why = B.resolve_base()
cb, pmb = B.build(base) if not why else (b"", b"")
check("F1 the candidate controls and map are build_v21's deterministic bytes from the authenticated v20 base",
      not why and open(CTL21_PATH, "rb").read() == cb and open(os.path.join(CAND, "v21_promotion_map.json"), "rb").read() == pmb)
c20 = json.loads(base["controls"])
check("F2 versions 1-20 and every top-level key equal the adopted v20 (programme block unchanged)",
      CTL21["versions"][:-1] == c20["versions"] and {k: v for k, v in CTL21.items() if k != "versions"} == {k: v for k, v in c20.items() if k != "versions"})
v20e, v21e = c20["versions"][-1], CTL21["versions"][-1]
diff = sorted(f for f in v21e["files"] if v21e["files"][f] != v20e["files"].get(f))
check("F3 exactly two pins change (programme_gate, admission), to this folder's bytes", diff == ["chpc/programme_gate.py", "chpc/row19_screen_admit.py"]
      and v21e["files"]["chpc/programme_gate.py"] == sha(os.path.join(CAND, "programme_gate.py"))
      and v21e["files"]["chpc/row19_screen_admit.py"] == sha(os.path.join(CAND, "row19_screen_admit.py")) and sorted(v21e["files"]) == sorted(v20e["files"]))
keys = sorted(k for k in set(v21e) | set(v20e) if v21e.get(k) != v20e.get(k))
check(f"F4 the v21 entry differs from v20 only in {keys}", keys == ["files", "funding_route", "reviewed", "sub_envelopes", "version"])
check("F5 the sub-envelope refit+S: 81,000 -> 181,000, the same campaigns", v21e["sub_envelopes"][0]["cap_core_h"] == 181000.0
      and v21e["sub_envelopes"][0]["campaigns"] == v20e["sub_envelopes"][0]["campaigns"] and v20e["sub_envelopes"][0]["cap_core_h"] == 81000.0)
fr = dict(MAN["funding"]); fr.update(CTL21["programme"]); fr["route"] = v21e["funding_route"]
check("F6 the route resolves against the REAL manifest funding + the controls programme block (CSCI1913 100,000 other 6 first)",
      [x["programme"] for x in PG.route_of(fr)] == ["CSCI1913", "HEAL1922"])
check("F7 the manifest's pbs.project is CSCI1913 = the route's first programme (old plans' -P unchanged)", MAN["pbs"]["project"] == "CSCI1913")
gram = []
for f in ("programme_gate.py", "row19_screen_admit.py", "build_v21.py"):
    try:
        ast.parse(open(os.path.join(CAND, f)).read(), feature_version=(3, 7))
    except SyntaxError as e:
        gram.append(f"{f}: {e}")
check("F8 Python 3.7 grammar (the Lengau t1py is 3.12; the rule of every earlier version)", not gram)
# the e3 activation proof (made under v20) must stay THE canonical activation under v21 (v21 pins the same e3): the REAL proof copy
RPm = load("row19_partition_f10", os.path.join(CHPC, "row19_partition.py"))
e3p = os.path.join(CHPC, "row19_partition_e3.json"); prf = os.path.join(CHPC, "results", "row19_screen", "live", "refit", "root", "ec2", "activation_e3.json")
part3 = RPm.load(e3p, MAN, sha(MAN_PATH)); proof3 = json.load(open(prf))
RPm.adopted_controls = lambda: (CTL21, "")
w21 = RPm.activation_problem(MAN, sha(MAN_PATH), part3, sha(e3p), proof3, mode="canonical")
RPm.adopted_controls = lambda: (json.loads(base["controls"]), "")
w20 = RPm.activation_problem(MAN, sha(MAN_PATH), part3, sha(e3p), proof3, mode="canonical")
check(f"F10 the REAL e3 activation proof (fb3304d3, made under v20) stays canonical under v21 ({w21!r}) as under v20 ({w20!r})",
      sha(prf).startswith("fb3304d3") and w21 == "" and w20 == "")
check("F9 the live tree is untouched by this suite", {r: sha(os.path.join(T1, r)) for r in LIVE} == LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{npass[0]} passed, {len(fails)} failed")
for f_ in fails:
    print("  FAILED:", f_)
sys.exit(1 if fails else 0)

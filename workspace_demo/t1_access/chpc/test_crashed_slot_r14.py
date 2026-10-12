"""REVISION 14 CANDIDATE (R052 12 Oct): the crashed-worker slot disposition of chpc/candidate_v15 (status + admission).
Refit job 13 (7531397.sched01) ended HELD 4 because slot 16 (rep 83 index 2) died of SIGSEGV after an LLVM "Cannot allocate
memory" during XLA compilation; 23 of 24 workers ended 0. The shared rule row19_screen_admit.crashed_slot_evidence is tested on
synthetic roots (one positive, every negative), then through the status view's reconcile and the admission's recompute, then
replayed on the REAL refit 13 PBS output/error bytes and the local live snapshot when present.

    python3 chpc/test_crashed_slot_r14.py          (from workspace_demo/t1_access)"""
import copy, hashlib, importlib.util, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "candidate_v15")
for p in (HERE, CAND):                                   # the candidate admission must be what `import row19_screen_admit` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))
R = load("r19_status_v15", os.path.join(CAND, "row19_screen_status.py"))
fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


JID = "7531397.sched01"; N = 13; TOKEN = "b15bb996a3dd"
SLOTS = [dict(slot=0, rep=67, indices=[2]), dict(slot=1, rep=83, indices=[2]), dict(slot=2, rep=84, indices=[2])]
OUT = ("host cnode0892\ncode aac02ca  start 2026-10-11T02:55:25Z  job 7531397.sched01  screen refit job 13\n"
       "job 13 admitted: 3 slots, 3 indices, start 2026-10-11T02:57:55Z\n"
       "job 13 ended: exit 4; workers exit codes [0, None, 0]; wall 85567 s\nexit 4 job 7531397.sched01 end 2026-10-12T02:41:32Z\n")


def crash(slot=1, rep=83, idx="2", sig="Segmentation fault", jid=JID):
    return (f"/var/spool/PBS/mom_priv/jobs/{jid}.SC: line 53: 55789 {sig}      $T/t1py chpc/row19_shard.py worker --manifest "
            f"../../../rsc_screen_ctl/workspace_demo/t1_access/chpc/row19_screen_manifest.json --rep {rep} --indices {idx} --slot {slot} "
            f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {{ROOT}}/logs/job$PBS_JOBID.slot{slot}.log 2>&1\n")


ERR = crash()


def entry(**kw):
    e = dict(kind="shard", rep=N, job_id=JID, token=TOKEN, state="settled", settled_core_h=570.45, settled_at=1791770000.0,
             settle_note="job 13: qstat -xf Exit_status 4, resources_used.walltime 23:46:07, job_state F", runner_exit=4,
             runner_ended=1791770000.0, runner_wall_s=85567.0)
    e.update(kw); return e


def fixture(statuses=None, extra_files=()):
    d = tempfile.mkdtemp(); root = os.path.join(d, "root")
    for sub in ("plans", "status", "records", "timing", "gate"):
        os.makedirs(os.path.join(root, sub))
    json.dump(dict(job=N, token=TOKEN, slots=SLOTS), open(os.path.join(root, "plans", f"job_{N}.json"), "w"))
    units = {}
    for sl in SLOTS:
        if sl["slot"] == 1:
            continue
        ex = (statuses or {}).get(sl["slot"], 0)
        json.dump(dict(job=JID, slot=sl["slot"], rep=sl["rep"], indices=sl["indices"], exit=ex, new=[2], resumed=[], left=[], maxrss=1, wall_s=1),
                  open(os.path.join(root, "status", f"job{JID}.slot{sl['slot']}.json"), "w"))
        os.makedirs(os.path.join(root, "timing", f"rep{sl['rep']}")); os.makedirs(os.path.join(root, "records", f"rep{sl['rep']}"))
        json.dump(dict(rep=sl["rep"], index=2, job=JID, slot=sl["slot"], wall_s=1, fit_seconds=1, maxrss=1, t=1),
                  open(os.path.join(root, "timing", f"rep{sl['rep']}", "t_002.json"), "w"))
        json.dump(dict(rep=2, sha="x"), open(os.path.join(root, "records", f"rep{sl['rep']}", "rec_002.json"), "w"))
        units[f"{sl['rep']}/2"] = dict(record=dict(ok=True), timing=dict(ok=True, job=JID, slot=sl["slot"]))
    for rel, body in extra_files:
        p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
    man = dict(storage=dict(root=root, campaign=os.path.join(d, "campaign")), shard=dict(toolchain=os.path.join(d, "tc")),
               datasets=dict(identities={}, reps=[67, 83, 84]))
    return d, root, man, units


def ev(man, units, e=None, obs=None, out=OUT, err=ERR, plan=None, jid=JID):
    plan = plan or json.load(open(os.path.join(man["storage"]["root"], "plans", f"job_{N}.json")))
    e = e or entry(); err = err.replace("{ROOT}", man["storage"]["root"])
    return SA.crashed_slot_evidence(man, "refit", N, e, plan, jid, obs or dict(state="F", exit=4), out.encode(), err.encode(), units, [e])


# ---- the shared rule, synthetic -------------------------------------------------------------------------------------------
d, root, man, units = fixture()
got, why = ev(man, units)
check("positive: one SIGSEGV worker, others 0 -> disposition", why == "" and got["kind"] == SA.CRASH_KIND
      and [c["slot"] for c in got["slots"]] == [1] and got["uncompleted"] == ["83/2"] and got["slots"][0]["signal"] == "Segmentation fault"
      and got["output_sha256"] == hashlib.sha256(OUT.encode()).hexdigest() and got["error_sha256"] == hashlib.sha256(ERR.replace("{ROOT}", root).encode()).hexdigest())
check("orig role never", ev.__call__ and SA.crashed_slot_evidence(man, "orig", N, entry(), {}, JID, dict(state="F", exit=4), b"", b"", {}, [])[0] is None)
check("scheduler exit 271 (walltime kill) -> no", ev(man, units, obs=dict(state="F", exit=271))[0] is None)
check("scheduler state E -> no", ev(man, units, obs=dict(state="E", exit=4))[0] is None)
check("ledger not settled -> no", ev(man, units, e=entry(state="running"))[0] is None)
check("runner exit 0 -> no", ev(man, units, e=entry(runner_exit=0))[0] is None)
check("runner exit True (bool) -> no", ev(man, units, e=entry(runner_exit=True))[0] is None)
check("settlement note missing -> no", ev(man, units, e=entry(settle_note=""))[0] is None)
check("plan of another token -> no", ev(man, units, plan=dict(job=N, token="other", slots=SLOTS))[0] is None)
check("error line names another slot -> no", ev(man, units, err=crash(slot=2, rep=84))[0] is None)
check("error line names another rep -> no", ev(man, units, err=crash(rep=82))[0] is None)
check("error line names another PBS id -> no", ev(man, units, err=crash(jid="7531398.sched01"))[0] is None)
check("Killed (external kill) -> no", ev(man, units, err=crash(sig="Killed"))[0] is None)
check("Bus error -> yes", ev(man, units, err=crash(sig="Bus error"))[1] == "")
check("core dumped suffix -> yes", ev(man, units, err=crash(sig="Segmentation fault (core dumped)").replace("(core dumped)      ", "(core dumped) "))[1] == ""
      or ev(man, units, err=crash(sig="Segmentation fault (core dumped)"))[1] == "")
check("duplicate crash line -> no", ev(man, units, err=ERR + ERR)[0] is None)
check("an extra death of a surviving worker -> no", ev(man, units, err=ERR + crash(slot=2, rep=84, sig="Killed"))[0] is None)
check("empty error stream -> no", ev(man, units, err="")[0] is None)
check("job-end codes None at another slot -> no", ev(man, units, out=OUT.replace("[0, None, 0]", "[None, 0, 0]"))[0] is None)
check("job-end codes with a 75 the status does not show -> no", ev(man, units, out=OUT.replace("[0, None, 0]", "[75, None, 0]"))[0] is None)
check("job-end exit 0 line -> no", ev(man, units, out=OUT.replace("ended: exit 4", "ended: exit 0"))[0] is None)
check("two job-end lines -> no", ev(man, units, out=OUT + "job 13 ended: exit 4; workers exit codes [0, None, 0]; wall 1 s\n")[0] is None)
check("ADMISSION FAILED -> no", ev(man, units, out=OUT + "(ADMISSION FAILED)\n")[0] is None)
check("output not naming the PBS id -> no", ev(man, units, out=OUT.replace("job 7531397.sched01", "job 1.sched01"))[0] is None)
d2, root2, man2, units2 = fixture(statuses={2: 4})
check("a surviving worker HELD (exit 4 status) -> no", ev(man2, units2, out=OUT.replace("[0, None, 0]", "[0, None, 4]"))[0] is None)
d3, root3, man3, units3 = fixture(extra_files=[(f"status/job{JID}.slot1.json.tmp.99", "{}")])
check("a status scoped to the PBS id at the crashed slot (temp name) -> no", ev(man3, units3)[0] is None)
d4, root4, man4, units4 = fixture(extra_files=[("timing/rep83/t_002.json", json.dumps(dict(rep=83, index=2, job=JID, slot=1)))])
check("a timing naming the job at the crashed coordinate -> no", ev(man4, units4)[0] is None)
d5, root5, man5, units5 = fixture(extra_files=[("records/rep83/rec_002.json", json.dumps(dict(rep=2, sha="y")))])
check("a record at the crashed coordinate with no later producer -> no", ev(man5, units5)[0] is None)
d6, root6, man6, units6 = fixture(extra_files=[("records/rep83/rec_002.json.tmp.5", "x")])
check("a temporary file at the crashed coordinate -> no", ev(man6, units6)[0] is None)
d7, root7, man7, units7 = fixture(extra_files=[("timing/rep99/t_000.json.tmp", "x")])
check("a timing file of unknown attribution anywhere -> no", ev(man7, units7)[0] is None)
u8 = copy.deepcopy(units); u8["83/2"] = dict(record=None, timing=dict(ok=True, job=JID, slot=1))
check("a verifier unit at the crashed coordinate naming the job -> no", ev(man, u8)[0] is None)
# a LATER bound job (14) that planned 83/2 in its slot 5 and completed it: allowed (the R1 later-completion rule)
d9, root9, man9, units9 = fixture(extra_files=[
    ("records/rep83/rec_002.json", json.dumps(dict(rep=2, sha="z", ident="I83"))),
    ("timing/rep83/t_002.json", json.dumps(dict(rep=83, index=2, ident="I83", job="7532000.sched01", slot=5, wall_s=1, fit_seconds=1, maxrss=1, t=1))),
    ("plans/job_14.json", json.dumps(dict(job=14, token="t14", slots=[dict(slot=5, rep=83, indices=[2])])))])
man9["datasets"]["identities"] = {"83": "I83"}
units9["83/2"] = dict(record=dict(ok=True, sha="z"), timing=dict(ok=True, job="7532000.sched01", slot=5))
e14 = dict(kind="shard", rep=14, job_id="7532000.sched01", token="t14", state="settled")
got9, why9 = SA.crashed_slot_evidence(man9, "refit", N, entry(), json.load(open(os.path.join(root9, "plans", f"job_{N}.json"))), JID,
                                      dict(state="F", exit=4), OUT.encode(), ERR.replace("{ROOT}", root9).encode(), units9, [entry(), e14])
check("a later bound job's verified completion at the crashed coordinate -> allowed", why9 == "" and got9["uncompleted"] == ["83/2"])

# V15-1 (Codex 5ca7fbd): EVERY timing naming the crashed job must be a surviving worker's planned coordinate in its slot
def tim(rep_, idx, slot, **kw):
    d = dict(rep=rep_, index=idx, job=JID, slot=slot, wall_s=1, fit_seconds=1, maxrss=1, t=1); d.update(kw); return json.dumps(d)


V151 = [("orphan timing-only outside the plan (Codex's trace rep999/777 slot 0)", "timing/rep999/t_777.json", tim(999, 777, 0)),
        ("timing at a surviving coordinate in the WRONG slot", "timing/rep67/t_002.json", tim(67, 2, 2)),
        ("timing at a planned coordinate of another index (not planned)", "timing/rep67/t_003.json", tim(67, 3, 0)),
        ("timing with no slot field", "timing/rep67/t_002.json", json.dumps(dict(rep=67, index=2, job=JID))),
        ("timing with a boolean slot", "timing/rep84/t_002.json", tim(84, 2, True)),
        ("timing with a string index", "timing/rep84/t_002.json", tim(84, "2", 2)),
        ("path alias: rep67/t_002 content claims 84/2", "timing/rep67/t_002.json", tim(84, 2, 2)),
        ("non-canonical path (subdirectory)", "timing/rep67/old/t_002.json", tim(67, 2, 0)),
        ("non-canonical name (t_2.json)", "timing/rep67/t_2.json", tim(67, 2, 0)),
        ("leading-zero rep alias rep067/t_002 beside the canonical survivor, contradictory provenance (Codex 485fe70)",
         "timing/rep067/t_002.json", tim(67, 2, 0, wall_s=999999, host="elsewhere", ident="not-the-declared-one")),
        ("leading-zero index alias t_0002", "timing/rep67/t_0002.json", tim(67, 2, 0))]
for label, rel, body in V151:
    dv, rootv, manv, unitsv = fixture(extra_files=[(rel, body)])
    got_v, why_v = ev(manv, unitsv)
    check(f"V15-1 shared rule: {label} -> no ({why_v[:70]})", got_v is None and why_v != "")
dv, rootv, manv, unitsv = fixture(extra_files=[("timing/rep999/t_777.json", tim(999, 777, 0, job="7000000.sched01"))])
check("V15-1 shared rule: an out-of-plan timing naming ANOTHER job is not this job's evidence -> still yes", ev(manv, unitsv)[1] == "")
check("tightened regex: a log path outside the campaign root -> no",
      ev(man, units, err=ERR.replace("{ROOT}/logs", "/elsewhere/logs"))[0] is None)
check("tightened regex: another manifest -> no", ev(man, units, err=ERR.replace("chpc/row19_screen_manifest.json", "chpc/other_manifest.json"))[0] is None)
check("tightened regex: a script outside the PBS spool -> no", ev(man, units, err=ERR.replace("/var/spool/PBS/mom_priv/jobs/", "/tmp/"))[0] is None)


# ---- the status view: reconcile with the fetched files ----------------------------------------------------------------------
def live_fixture(with_err=True, err=ERR, extra_files=()):
    d, root, man, units = fixture(extra_files=extra_files)
    err = err.replace("{ROOT}", man["storage"]["root"])
    live = os.path.join(d, "live"); shutil.copytree(root, os.path.join(live, "root"))
    os.makedirs(os.path.join(live, "jobs")); os.makedirs(os.path.join(live, "campaign"))
    fetch = {}
    for key, name, body in ((str(N), f"row19_screen_refit_{N}.out", OUT), (f"{N}.err", f"row19_screen_refit_{N}.err", err)):
        if key.endswith(".err") and not with_err:
            fetch[key] = dict(file=name, rc=1, ok=False, sha256=None); continue
        open(os.path.join(live, "jobs", name), "w").write(body)
        fetch[key] = dict(file=name, rc=0, ok=True, sha256=hashlib.sha256(body.encode()).hexdigest())
    json.dump(fetch, open(os.path.join(live, "jobs", "_fetch.json"), "w"))
    ledger = {"entries": {"13": entry()}}
    man.update(pbs=dict(mem_gb=120, mem_stop_gib=4.5), datasets=dict(identities={"67": None, "84": None}, reps=[67, 83, 84]))
    verify = dict(units=units, bindings={"67": dict(ok=True, declared_ident_equal=True), "83": dict(ok=True, declared_ident_equal=True),
                                         "84": dict(ok=True, declared_ident_equal=True)})
    obs = {JID: dict(state="F", exit=4, mem_kb=46155404, walltime_req_s=None)}
    return man, verify, obs, ledger, live


R.ec2_reconcile = lambda *a, **k: {}
THREE = ("terminal as state F, scheduler exit 4", "runner exit 4", "slot 1: no worker status")
man_, verify_, obs_, ledger_, live_ = live_fixture()
al, summ, jobs, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
s13 = summ[str(N)]
check("status: the three crash alarms are not raised and nothing else is", al == [])
check("status: summary carries the slot disposition, keeps the actual exits, 2 of 3 ended",
      s13.get("slot_disposition", {}).get("kind") == SA.CRASH_KIND and s13["exit"] == 4 and s13["runner_exit"] == 4 and s13["ended"] == 2)
check("status: crashed coordinate uncompleted with origin crashed-slot",
      s13["partition"].get("uncompleted") == ["83/2"] and s13["partition"].get("uncompleted_origin") == "crashed-slot")
man_, verify_, obs_, ledger_, live_ = live_fixture(with_err=False)
al, summ, _, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
check("status: error stream not retrieved -> all three alarms stand, reason kept",
      all(any(t in a for a in al) for t in THREE) and "not retrieved" in summ[str(N)].get("slot_disposition_held", ""))
man_, verify_, obs_, ledger_, live_ = live_fixture(err=crash(sig="Killed"))
al, summ, _, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
check("status: Killed -> all three alarms stand", all(any(t in a for a in al) for t in THREE) and "slot_disposition" not in summ[str(N)])
man_, verify_, obs_, ledger_, live_ = live_fixture()
ledger_["entries"]["13"]["runner_exit"] = 0
al, summ, _, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
check("status: runner exit 0 with a missing status -> not examined, alarms stand",
      any("scheduler exit 4" in a for a in al) and any("slot 1: no worker status" in a for a in al) and "slot_disposition_held" not in summ[str(N)])

# ---- the admission: recompute from the campaign's files ----------------------------------------------------------------------
def admit_fixture():
    man_, verify_, obs_, ledger_, live_ = live_fixture()
    al, summ, jobs, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
    root = man_["storage"]["root"]; os.makedirs(man_["storage"]["campaign"]); os.makedirs(os.path.join(man_["shard"]["toolchain"], "jobs"))
    json.dump(ledger_, open(os.path.join(man_["storage"]["campaign"], "budget.json"), "w"))
    for name, body in ((f"row19_screen_refit_{N}.out", OUT), (f"row19_screen_refit_{N}.err", ERR.replace("{ROOT}", root))):
        open(os.path.join(man_["shard"]["toolchain"], "jobs", name), "w").write(body)
    json.dump(verify_, open(os.path.join(root, "gate", "verify_refit_x.json"), "w"))
    d = summ[str(N)]["slot_disposition"]
    bound = dict(jobs=jobs, verify_file="verify_refit_x.json",
                 slot_outputs={str(N): dict(out=dict(file=d["output_file"], sha256=d["output_sha256"]), err=dict(file=d["error_file"], sha256=d["error_sha256"]))})
    return man_, summ[str(N)], bound, ledger_


man_, sj, bound, ledger_ = admit_fixture()
check("admission: the receipt's slot disposition recomputes exactly", SA.slot_disposition_problem(man_, None, "refit", N, sj, bound) == "")
check("admission: the summary passes job_summary_problem", SA.job_summary_problem(man_, str(N), sj) == "")
check("admission: never a pilot", "never qualifies" in SA.job_summary_problem(man_, str(N), sj, pilot=True))
check("admission: units reconcile against the plan minus the crashed coordinate",
      SA.units_problem(man_, dict(units=json.load(open(os.path.join(man_["storage"]["root"], "gate", "verify_refit_x.json")))["units"]),
                       dict(jobs={str(N): sj})) == "")
check("admission: transition check passes on the same certificate", SA.transition_problem(man_, "refit", dict(jobs={str(N): sj})) == "")
open(os.path.join(man_["shard"]["toolchain"], "jobs", f"row19_screen_refit_{N}.err"), "a").write("\n")
check("admission: changed error bytes on disk -> refused", "not the bytes the receipt bound" in SA.slot_disposition_problem(man_, None, "refit", N, sj, bound))
man_, sj, bound, ledger_ = admit_fixture()
sj2 = copy.deepcopy(sj); sj2["slot_disposition"]["uncompleted"] = ["67/2"]
check("admission: an edited disposition -> refused", SA.slot_disposition_problem(man_, None, "refit", N, sj2, bound) != "")
sj3 = copy.deepcopy(sj); sj3["partition"]["uncompleted_origin"] = "plan"
check("admission: wrong uncompleted origin -> refused", "crashed-slot" in SA.slot_disposition_problem(man_, None, "refit", N, sj3, bound))
b2 = copy.deepcopy(bound); b2["slot_outputs"] = {}
check("admission: receipt binds no error bytes -> refused", "does not bind" in SA.slot_disposition_problem(man_, None, "refit", N, sj, b2))
led = json.load(open(os.path.join(man_["storage"]["campaign"], "budget.json"))); led["entries"]["13"]["settled_core_h"] = 1.0
json.dump(led, open(os.path.join(man_["storage"]["campaign"], "budget.json"), "w"))
check("admission: a changed settlement certificate -> refused", "certificate" in SA.slot_disposition_problem(man_, None, "refit", N, sj, bound)
      and "certificate" in SA.transition_problem(man_, "refit", dict(jobs={str(N): sj})))
man_, sj, bound, ledger_ = admit_fixture()
sj4 = copy.deepcopy(sj); sj4["disposition"] = dict(kind="closed-no-record")
check("admission: both dispositions at once -> refused", "both" in SA.slot_disposition_problem(man_, None, "refit", N, sj4, bound))
sj5 = copy.deepcopy(sj); sj5["ended"] = 3
check("admission: summary claiming every worker ended -> refused", SA.job_summary_problem(man_, str(N), sj5) != "")

# V15-1 through the consumers: the status view keeps all three alarms; the admission refuses a receipt disposition
man_, verify_, obs_, ledger_, live_ = live_fixture(extra_files=[("timing/rep067/t_002.json", tim(67, 2, 0, wall_s=999999))])
al, summ, _, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
check("V15-1 status: rep067 alias beside the canonical survivor -> all three alarms stand",
      all(any(t in a for a in al) for t in THREE) and "rep067" in summ[str(N)].get("slot_disposition_held", ""))
man_, verify_, obs_, ledger_, live_ = live_fixture(extra_files=[("timing/rep999/t_777.json", tim(999, 777, 0))])
al, summ, _, _ = R.reconcile(man_, "refit", verify_, obs_, ledger_, live_)
check("V15-1 status: orphan same-job timing -> all three alarms stand, reason kept",
      all(any(t in a for a in al) for t in THREE) and "slot_disposition" not in summ[str(N)] and "rep999" in summ[str(N)].get("slot_disposition_held", ""))
man_, sj, bound, ledger_ = admit_fixture()
p_orphan = os.path.join(man_["storage"]["root"], "timing", "rep999"); os.makedirs(p_orphan)
open(os.path.join(p_orphan, "t_777.json"), "w").write(tim(999, 777, 0))
why_o = SA.slot_disposition_problem(man_, None, "refit", N, sj, bound)
check(f"V15-1 admission: an orphan written after the receipt -> refused ({why_o[:60]})", "not a crashed-worker slot disposition" in why_o and "rep999" in why_o)
os.remove(os.path.join(p_orphan, "t_777.json"))
open(os.path.join(man_["storage"]["root"], "timing", "rep67", "t_002.json"), "w").write(tim(67, 2, 2))
check("V15-1 admission: a survivor's timing rewritten to the wrong slot -> refused",
      "not a crashed-worker slot disposition" in SA.slot_disposition_problem(man_, None, "refit", N, sj, bound))
man_, sj, bound, ledger_ = admit_fixture()
p_alias = os.path.join(man_["storage"]["root"], "timing", "rep067"); os.makedirs(p_alias)
open(os.path.join(p_alias, "t_002.json"), "w").write(tim(67, 2, 0, wall_s=999999))
why_a = SA.slot_disposition_problem(man_, None, "refit", N, sj, bound)
check(f"V15-1 admission: rep067 alias written after the receipt -> refused ({why_a[:50]})", "not a crashed-worker slot disposition" in why_a and "rep067" in why_a)


# ---- replay on the REAL refit 13 bytes and the local snapshot (skipped when absent) ------------------------------------------
REAL = os.environ.get("R13_FIXTURE", os.path.join(CAND, "fixture_refit13"))   # row19_screen_refit_13.out/.err as retrieved from Lengau
LIVE = os.path.join(HERE, "results", "row19_screen", "live", "refit")
RCPT = os.path.join(HERE, "results", "row19_screen", "receipts", "watch_refit_20261012T033531Z.json")
VFY = os.path.join(HERE, "results", "row19_screen", "receipts", "verify_refit_20261012T033531Z.json")
if REAL and os.path.isdir(REAL) and all(os.path.exists(p) for p in (LIVE, RCPT, VFY)):
    rc = json.load(open(RCPT)); man = json.load(open(os.path.join(HERE, "row19_screen_manifest.json")))
    d = tempfile.mkdtemp(); live = os.path.join(d, "refit"); shutil.copytree(LIVE, live)
    fetch = json.load(open(os.path.join(live, "jobs", "_fetch.json")))       # keep job 3's closed-no-record retrieval
    for key, name in (("13", "row19_screen_refit_13.out"), ("13.err", "row19_screen_refit_13.err")):
        src = os.path.join(REAL, name); src = src if os.path.exists(src) else src + ".txt"     # committed copies carry .txt (.out is gitignored)
        shutil.copy(src, os.path.join(live, "jobs", name))
        fetch[key] = dict(file=name, rc=0, ok=True, sha256=R.sha_file(os.path.join(live, "jobs", name)))
    json.dump(fetch, open(os.path.join(live, "jobs", "_fetch.json"), "w"))
    obs = {s["job_id"]: dict(state=s["state"], exit=s["exit"], mem_kb=s["mem_kb"], walltime_req_s=s.get("requested_walltime_s"))
           for s in rc["jobs"].values() if s.get("job_id")}
    ledger = json.load(open(os.path.join(live, "campaign", "budget.json")))
    R.MANIFEST_PATH = os.path.join(HERE, "row19_screen_manifest.json")
    al, summ, _, _ = R.reconcile(man, "refit", json.load(open(VFY)), obs, ledger, live)
    s = summ["13"]
    print("   replay alarms:", al, "| held:", s.get("slot_disposition_held"))
    check("REAL refit 13: slot 16 (rep 83 index 2) dispositioned as a Segmentation fault, the receipt's three alarms gone",
          al == [] and [(c["slot"], c["rep"], c["indices"], c["signal"]) for c in s["slot_disposition"]["slots"]] == [(16, 83, [2], "Segmentation fault")]
          and s["partition"]["uncompleted"] == ["83/2"] and s["ended"] == 23)
else:
    print("skip REAL refit 13 replay (set R13_FIXTURE to the directory with the retrieved .out/.err; needs the local live snapshot)")

print(f"\n{'ALL OK' if not fails else f'{len(fails)} FAILED'}")
sys.exit(1 if fails else 0)

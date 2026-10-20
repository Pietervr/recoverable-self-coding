"""Controls v18 CANDIDATE (NOT adopted): tests of the NODE-FAILURE disposition (chpc/candidate_v18_nodefail), Mac, pure python.

The positive case is modelled on refit job 54 (PBS 7551259.sched01, 20 Oct 2026): its REAL plan, ledger entry and the two REAL
completed statuses (slots 19 and 20) from the local live snapshot when present (else the same values written here), Exit_status
265, exec_host cnode0240/0*24, walltime 17:21:10 of 48:00:00, mem 41,763,220 kb, mtime and pbsnodes last_state_change_time both
20 Oct 20:00:36. ASSUMED, not observed (the brief gives neither): Lengau prints local SAST (UTC+2) times, and stime 02:19:20
local (21 s before the ledger's runner_started). The capture writes the true values; nothing here is evidence.

    python3 chpc/candidate_v18_nodefail/test_v18_nodefail.py          (from workspace_demo/t1_access)"""
import ast, copy, hashlib, importlib.util, io, json, os, shutil, subprocess, sys, tempfile, contextlib

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):                       # the candidate admission and rule must be what `import ...` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))
NF = load("row19_screen_nodefail", os.path.join(CAND, "row19_screen_nodefail.py"))
R = load("r19_status_v18", os.path.join(CAND, "row19_screen_status.py"))
CAP = load("r19_nodefail_capture", os.path.join(CAND, "row19_nodefail_capture.py"))
PIN = hashlib.sha256(open(os.path.join(CAND, "row19_nodefail_capture.py"), "rb").read()).hexdigest()
fails = []; npass = [0]


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


# ---- job 54, from the local snapshot when present ---------------------------------------------------------------------------
LIVE = os.path.join(CHPC, "results", "row19_screen", "live", "refit")
JID, N, TOKEN = "7551259.sched01", 54, "dd8d1b891252"
REAL = os.path.exists(os.path.join(LIVE, "root", "plans", "job_54.json"))
if REAL:
    PLAN = json.load(open(os.path.join(LIVE, "root", "plans", "job_54.json")))
    ENTRY = [e for e in json.load(open(os.path.join(LIVE, "campaign", "budget.json")))["entries"].values() if e.get("kind") == "shard" and e.get("rep") == 54][0]
    STAT = {s: json.load(open(os.path.join(LIVE, "root", "status", f"job{JID}.slot{s}.json"))) for s in (19, 20)}
else:
    PLAN = dict(job=54, slots=[dict(slot=s, rep=5, indices=[65 + s]) for s in range(15)] + [dict(slot=15 + k, rep=8, indices=[11 + k]) for k in range(9)],
                queue="serial", walltime_s=172800.0, token=TOKEN, created=1792440705.86,
                envelope=dict(queue="serial", cores=24, walltime_s=172800.0, mem_gb=120, nodetype="haswell_reg", deadline_reserve_s=1800,
                              source="chpc/row19_screen_resources.json first_job=10"))
    ENTRY = dict(attempt=1, bound_at=1792440705.96, cores=24, created=1792440705.79, job_id=JID, kind="shard", rep=54, reserved_core_h=1152.0,
                 root="/x", runner_started=1792455581.6020372, settle_note="refit job 54: qstat -xf Exit_status 265, resources_used.walltime 17:21:10, job_state F",
                 settled_at=1792527561.3968687, settled_core_h=416.46666666666664, state="settled", token=TOKEN, walltime_s=172800.0)
    STAT = {19: dict(cpu_s=47145.4, ended=1792503088.73, exit=0, host="cnode0240", ident="I8", indices=[15], job=JID, left=[], maxrss=2255351808,
                     new=[15], reason="", rep=8, resumed=[], slot=19, started=1792455587.76, wall_s=47500.98),
            20: dict(cpu_s=61341.96, ended=1792517192.11, exit=0, host="cnode0240", ident="I8", indices=[16], job=JID, left=[], maxrss=2582990848,
                     new=[16], reason="", rep=8, resumed=[], slot=20, started=1792455587.84, wall_s=61604.27)}
print("job 54 inputs:", "REAL local snapshot" if REAL else "built-in copy of the snapshot values")
IDENT8 = STAT[19]["ident"]
SURV = {19: "8/15", 20: "8/16"}
NOSTAT = [s for s in range(24) if s not in SURV]


def evidence_doc(**kw):
    q = dict(job_state="F", Exit_status=265, exec_host="cnode0240/0*24", stime="Tue Oct 20 02:19:20 2026", stime_epoch=1792455560,
             mtime="Tue Oct 20 20:00:36 2026", mtime_epoch=1792519236, resources_used_walltime="17:21:10", resources_used_walltime_s=62470,
             resources_used_mem_kb=41763220, Resource_List_walltime="48:00:00", Resource_List_walltime_s=172800)
    nd = dict(name="cnode0240", state="down", comment="node down: communication closed", last_state_change_time="Tue Oct 20 20:00:36 2026",
              last_state_change_epoch=1792519236)
    d = dict(schema=NF.SCHEMA, role="refit", job=N, job_id=JID, captured_at=1792530000.0, captured_by="row19_nodefail_capture.py", capture_sha256=PIN,
             utc_offset_s=7200, qstat=q, node=nd, pbs_output_present=dict(out=False, err=False),
             source_sha256=dict(qstat_xf="a" * 64, pbsnodes="b" * 64))
    for k, v in kw.items():
        if k in q:
            q[k] = v
        elif k.startswith("node_"):
            nd[k[5:]] = v
        else:
            d[k] = v
    return d


def ev_bytes(d):
    return (json.dumps(d, indent=1, sort_keys=True) + "\n").encode()


def fixture(statuses=None, extra_files=(), logs_exit=()):
    """A root holding job 54's plan, the two completed statuses (or `statuses` {slot: status | None}) with their records and
    timings, and a header-only log per no-status slot."""
    d = tempfile.mkdtemp(); root = os.path.join(d, "root")
    for sub in ("plans", "status", "records", "timing", "gate", "logs"):
        os.makedirs(os.path.join(root, sub))
    json.dump(PLAN, open(os.path.join(root, "plans", f"job_{N}.json"), "w"), indent=1)
    sts = {s: copy.deepcopy(STAT[s]) for s in SURV}
    if statuses:
        sts.update(statuses)
    units = {}
    for s, st in sorted(sts.items()):
        if st is None:
            continue
        json.dump(st, open(os.path.join(root, "status", f"job{JID}.slot{s}.json"), "w"), indent=1)
        sl = PLAN["slots"][s]; r, i = sl["rep"], sl["indices"][0]
        os.makedirs(os.path.join(root, "timing", f"rep{r}"), exist_ok=True); os.makedirs(os.path.join(root, "records", f"rep{r}"), exist_ok=True)
        json.dump(dict(rep=r, index=i, ident=IDENT8, job=JID, slot=s, wall_s=1, fit_seconds=1, maxrss=1, t=1),
                  open(os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json"), "w"))
        json.dump(dict(rep=i, sha=f"s{i}", ident=IDENT8), open(os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"), "w"))
        units[f"{r}/{i}"] = dict(record=dict(ok=True, sha=f"s{i}"), timing=dict(ok=True, job=JID, slot=s))
    for s in range(24):
        sl = PLAN["slots"][s]
        body = f"worker job {JID} slot {s}: rep {sl['rep']} identity x indices {sl['indices']}\n"
        if (sts.get(s) is not None) or s in logs_exit:
            body += f"worker job {JID} slot {s}: exit 0 new {sl['indices']} resumed [] left [] \n"
        open(os.path.join(root, "logs", f"job{JID}.slot{s}.log"), "w").write(body)
    for rel, body in extra_files:
        p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
    man = dict(storage=dict(root=root, campaign=os.path.join(d, "campaign")), shard=dict(toolchain=os.path.join(d, "tc")),
               datasets=dict(identities={"5": "I5", "8": IDENT8}, reps=[5, 8]), pbs=dict(mem_gb=120, mem_stop_gib=4.5, deadline_reserve_s=1800))
    return d, root, man, units


def ev(man, units, e=None, obs=None, doc=None, b=None, plan=None, pin=PIN, entries=None):
    plan = plan or json.load(open(os.path.join(man["storage"]["root"], "plans", f"job_{N}.json")))
    e = e if e is not None else copy.deepcopy(ENTRY)
    b = b if b is not None else ev_bytes(doc or evidence_doc())
    return NF.node_failure_evidence(man, "refit", N, e, plan, JID, obs or dict(state="F", exit=265), b, units, entries or [e], pin=pin)


def no(label, got):
    check(f"{label} -> refused ({got[1][:90]})", got[0] is None and got[1] != "")


# ---- 1. the shared rule ------------------------------------------------------------------------------------------------------
d, root, man, units = fixture()
got, why = ev(man, units)
check("POSITIVE job 54: node-failure disposition (cnode0240 down at the job's end, slots 19/20 kept, 22 coordinates uncompleted)",
      why == "" and got["kind"] == "node-failure" and got["node"] == "cnode0240" and got["scheduler_exit"] == 265 and got["runner_exit"] is None
      and got["completed_slots"] == [19, 20] and got["no_status_slots"] == NOSTAT and got["completed"] == ["8/15", "8/16"]
      and len(got["uncompleted"]) == 22 and "8/15" not in got["uncompleted"] and got["counts_as_crash"] is False
      and got["node_change_minus_mtime_s"] == 0 and got["evidence_file"] == "row19_screen_refit_54.nodefail.json")
print("   ", why or {k: got[k] for k in ("node", "node_state", "node_comment", "completed_slots", "settled_core_h")})
check("the uncompleted coordinates are exactly the 22 no-status slots' (5/65..5/79, 8/11..8/14, 8/17..8/19)",
      got and sorted(got["uncompleted"]) == sorted([f"5/{i}" for i in range(65, 80)] + [f"8/{i}" for i in (11, 12, 13, 14, 17, 18, 19)]))
check("deterministic: the same evidence gives the identical disposition", ev(man, units)[0] == got)

gU, wU = ev(man, units, doc=evidence_doc(utc_offset_s=0, stime="Tue Oct 20 00:19:20 2026", stime_epoch=1792455560, mtime_epoch=1792526436,
                                         node_last_state_change_epoch=1792526436))
check("the same printed times from a UTC-printing host (the R052 log's reading '20:00:36Z') -> also yes; the capture records which",
      wU == "" and gU["job_mtime_epoch"] == 1792526436)
no("node not down (state free)", ev(man, units, doc=evidence_doc(node_state="free")))
no("node offline but not down", ev(man, units, doc=evidence_doc(node_state="offline")))
check("node 'down,offline' -> yes", ev(man, units, doc=evidence_doc(node_state="down,offline"))[1] == "")
no("time mismatch: node changed 600 s after the job's mtime", ev(man, units, doc=evidence_doc(node_last_state_change_time="Tue Oct 20 20:10:36 2026",
                                                                                              node_last_state_change_epoch=1792519836)))
no("time mismatch: node changed 1 h before the job's mtime", ev(man, units, doc=evidence_doc(node_last_state_change_time="Tue Oct 20 19:00:36 2026",
                                                                                               node_last_state_change_epoch=1792515636)))
check("node change 100 s after mtime (within the 120 s tolerance) -> yes",
      ev(man, units, doc=evidence_doc(node_last_state_change_time="Tue Oct 20 20:02:16 2026", node_last_state_change_epoch=1792519336))[1] == "")
e4 = dict(ENTRY, settle_note="refit job 54: qstat -xf Exit_status 4, resources_used.walltime 17:21:10, job_state F")
no("exit 4 (HELD: the crashed-slot class, not node failure)", ev(man, units, e=e4, obs=dict(state="F", exit=4), doc=evidence_doc(Exit_status=4)))
e271 = dict(ENTRY, settle_note="refit job 54: qstat -xf Exit_status 271, resources_used.walltime 17:21:10, job_state F")
no("exit 271 (SIGTERM, the walltime-kill signature) even with the node down", ev(man, units, e=e271, obs=dict(state="F", exit=271), doc=evidence_doc(Exit_status=271)))
no("exit True (boolean)", ev(man, units, obs=dict(state="F", exit=True)))
no("scheduler state E", ev(man, units, obs=dict(state="E", exit=265)))
no("captured scheduler record says exit 0", ev(man, units, doc=evidence_doc(Exit_status=0)))
no("settlement note's Exit_status is another exit", ev(man, units, e=e4))
no("unsettled ledger (state running)", ev(man, units, e=dict(ENTRY, state="running")))
no("ledger settled without a note", ev(man, units, e=dict(ENTRY, settle_note="")))
no("ledger records a runner end (job-end ran)", ev(man, units, e=dict(ENTRY, runner_exit=4, runner_ended=1.0, runner_wall_s=1.0)))
no("ledger records no runner start (an admission failure is not excluded)", ev(man, units, e={k: v for k, v in ENTRY.items() if k != "runner_started"}))
no("plan of another token", ev(man, units, plan=dict(PLAN, token="other")))
no("evidence of another PBS id", ev(man, units, doc=evidence_doc(job_id="7551260.sched01")))
no("evidence of another job number", ev(man, units, doc=evidence_doc(job=55)))
no("evidence written by another capture script (sha not the pin)", ev(man, units, doc=evidence_doc(capture_sha256="c" * 64)))
no("no capture pin (controls v17 pins no capture script)", ev(man, units, pin=None))
no("the job ran on two nodes", ev(man, units, doc=evidence_doc(exec_host="cnode0240/0*12+cnode0241/0*12")))
no("exec_host names another node than the captured one", ev(man, units, doc=evidence_doc(exec_host="cnode0241/0*24")))
no("PBS .out present at capture", ev(man, units, doc=evidence_doc(pbs_output_present=dict(out=True, err=False))))
no("walltime used reached the request less the reserve (a walltime kill)",
   ev(man, units, doc=evidence_doc(resources_used_walltime="47:40:00", resources_used_walltime_s=171600, stime="Sun Oct 18 20:00:00 2026", stime_epoch=1792346400)))
no("the captured request is not the plan's 48 h", ev(man, units, doc=evidence_doc(Resource_List_walltime="30:00:00", Resource_List_walltime_s=108000)))
no("capture taken before the job ended", ev(man, units, doc=evidence_doc(captured_at=1792500000.0)))
no("stime after the ledger's runner start", ev(man, units, doc=evidence_doc(stime="Tue Oct 20 03:19:20 2026", stime_epoch=1792459160)))
no("a printed time that does not recompute to its epoch (tampered mtime_epoch)", ev(man, units, doc=evidence_doc(mtime_epoch=1792519836)))
no("the UTC offset changed after the fact (SAST read as UTC)", ev(man, units, doc=evidence_doc(utc_offset_s=0)))
# raw capture attempts
dr = evidence_doc(); dr["raw"] = "Job Id: 7551259.sched01\n    job_state = F\n"
no("RAW CAPTURE: an extra key holding qstat -xf text", ev(man, units, doc=dr))
no("RAW CAPTURE: the qstat output pasted into a field", ev(man, units, doc=evidence_doc(exec_host="Job Id: 7551259.sched01\n    exec_host = cnode0240/0*24")))
no("RAW CAPTURE: a 'key = value' line in the node comment", ev(man, units, doc=evidence_doc(node_comment="state = down")))
no("RAW CAPTURE: a file over 4 KB", ev(man, units, b=ev_bytes(evidence_doc()) + b" " * 5000))
no("RAW CAPTURE: the raw qstat -xf text instead of JSON", ev(man, units, b=b"Job Id: 7551259.sched01\n    job_state = F\n    Exit_status = 265\n"))
no("a non-finite number in the evidence", ev(man, units, b=ev_bytes(evidence_doc()).replace(b'"captured_at": 1792530000.0', b'"captured_at": NaN')))
no("a missing key (no source digests)", ev(man, units, doc={k: v for k, v in evidence_doc().items() if k != "source_sha256"}))
# slots
st75 = dict(STAT[19], slot=0, rep=5, indices=[65], new=[], left=[65], exit=75)
d2, root2, man2, units2 = fixture(statuses={0: st75})
no("a PARTIAL status (slot 0 exit 75 with work left)", ev(man2, units2))
st4 = dict(STAT[19], slot=0, rep=5, indices=[65], new=[], left=[65], exit=4)
d2, root2, man2, units2 = fixture(statuses={0: st4})
no("a HELD status (slot 0 exit 4)", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[(f"status/job{JID}.slot0.json", "{not json")])
no("an unreadable status at a planned slot", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[(f"status/job{JID}.slot30.json", json.dumps(dict(job=JID, slot=30, exit=0)))])
no("a status of this job at an unplanned slot", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[(f"status/job{JID}.slot3.json.tmp.77", "{}")])
no("a temporary status file scoped to the job", ev(man2, units2))
d2, root2, man2, units2 = fixture(statuses={19: dict(STAT[19], host="cnode0241")})
no("a completed status on another host than the down node", ev(man2, units2))
d2, root2, man2, units2 = fixture(statuses={20: dict(STAT[20], ended=1792519236 + 3600)})
no("a completed status that ended after the job's captured end", ev(man2, units2))
d2, root2, man2, units2 = fixture(statuses={19: dict(STAT[19], indices=[14])})
no("a completed status whose assignment is not the plan's", ev(man2, units2))
u3 = copy.deepcopy(units); u3["8/15"]["record"] = dict(ok=False, reason="bad checksum")
no("a completed slot whose record is invalid", ev(man, u3))
u3 = copy.deepcopy(units); u3["8/16"]["timing"]["slot"] = 7
no("a completed slot's new timing naming another slot", ev(man, u3))
d2, root2, man2, units2 = fixture(extra_files=[("records/rep5/rec_065.json", json.dumps(dict(rep=65, sha="q", ident="I5")))])
no("a record at a no-status coordinate with no later producer", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[("timing/rep5/t_066.json", json.dumps(dict(rep=5, index=66, job=JID, slot=1, wall_s=1, fit_seconds=1, maxrss=1, t=1)))])
no("a timing naming the job at a no-status coordinate (a worker that published but wrote no status)", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[("records/rep5/rec_067.json.tmp.9", "x")])
no("a temporary file at a no-status coordinate", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[("timing/rep999/t_777.json", json.dumps(dict(rep=999, index=777, job=JID, slot=19)))])
no("an orphan same-job timing outside the plan (the V15-1 rule)", ev(man2, units2))
d2, root2, man2, units2 = fixture(extra_files=[("timing/rep008/t_015.json", json.dumps(dict(rep=8, index=15, job=JID, slot=19)))])
no("a leading-zero path alias of a survivor's timing", ev(man2, units2))
d2, root2, man2, units2 = fixture(logs_exit=(3,))
no("a no-status slot whose log reports an exit", ev(man2, units2))
u4 = copy.deepcopy(units); u4["5/70"] = dict(record=None, timing=dict(ok=True, job=JID, slot=5))
no("a verifier unit at a no-status coordinate naming the job", ev(man, u4))
no("role orig", NF.node_failure_evidence(man, "orig", N, ENTRY, PLAN, JID, dict(state="F", exit=265), ev_bytes(evidence_doc()), units, [ENTRY], pin=PIN))
# later completion of a no-status coordinate by a later bound job: allowed (the R1 rule)
d9, root9, man9, units9 = fixture(extra_files=[
    ("records/rep5/rec_065.json", json.dumps(dict(rep=65, sha="z", ident="I5"))),
    ("timing/rep5/t_065.json", json.dumps(dict(rep=5, index=65, ident="I5", job="7560000.sched01", slot=2, wall_s=1, fit_seconds=1, maxrss=1, t=1))),
    ("plans/job_60.json", json.dumps(dict(job=60, token="t60", slots=[dict(slot=2, rep=5, indices=[65])])))])
units9["5/65"] = dict(record=dict(ok=True, sha="z"), timing=dict(ok=True, job="7560000.sched01", slot=2))
e60 = dict(kind="shard", rep=60, job_id="7560000.sched01", token="t60", state="settled")
g9, w9 = ev(man9, units9, entries=[ENTRY, e60])
check("a LATER bound job's verified completion at a no-status coordinate -> allowed, still uncompleted for job 54", w9 == "" and "5/65" in g9["uncompleted"])
d0, root0, man0, units0 = fixture(statuses={19: None, 20: None})
for rel in ("timing/rep8/t_015.json", "timing/rep8/t_016.json", "records/rep8/rec_015.json", "records/rep8/rec_016.json"):
    if os.path.exists(os.path.join(root0, rel)):
        os.remove(os.path.join(root0, rel))
g0, w0 = ev(man0, {})
check("no slot completed at all (every worker lost with the node) -> yes, 24 uncompleted", w0 == "" and len(g0["uncompleted"]) == 24 and g0["completed_slots"] == [])

# ---- 2. the status view ------------------------------------------------------------------------------------------------------
def live_fixture(doc=None, fetch_ok=True, statuses=None, extra_files=()):
    d, root, man, units = fixture(statuses=statuses, extra_files=extra_files)
    live = os.path.join(d, "live"); shutil.copytree(root, os.path.join(live, "root"))
    os.makedirs(os.path.join(live, "jobs")); os.makedirs(os.path.join(live, "campaign"))
    b = ev_bytes(doc or evidence_doc()); name = NF.evidence_name("refit", N)
    fetch = {str(N): dict(file=f"row19_screen_refit_{N}.out", rc=1, ok=False, sha256=None, err="No such file or directory")}
    if fetch_ok:
        open(os.path.join(live, "jobs", name), "wb").write(b)
        fetch[f"{N}.nodefail"] = dict(file=name, rc=0, ok=True, sha256=hashlib.sha256(b).hexdigest())
    else:
        fetch[f"{N}.nodefail"] = dict(file=name, rc=1, ok=False, sha256=None)
    json.dump(fetch, open(os.path.join(live, "jobs", "_fetch.json"), "w"))
    ledger = {"entries": {"54": copy.deepcopy(ENTRY)}}
    verify = dict(units=units, bindings={"5": dict(ok=True, declared_ident_equal=True), "8": dict(ok=True, declared_ident_equal=True)})
    obs = {JID: dict(state="F", exit=265, mem_kb=41763220, walltime_req_s=172800.0)}
    return man, verify, obs, ledger, live, b


R.ec2_reconcile = lambda *a, **k: {}
NF.capture_pin = lambda: PIN                     # the candidate v18 controls pin exactly these bytes (checked in part 4)
WANT_ALARMS = ("terminal as state F, scheduler exit 265", "terminal but no runner end", "no worker status after the job ended")
m_, v_, o_, l_, lv_, b_ = live_fixture()
al, summ, jobs, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
s54 = summ[str(N)]
check("status: the 24 job-54 alarms (exit 265, no runner end, 22 missing statuses) are gone and NOTHING else is raised", al == [])
check("status: summary carries node_disposition; exit 265 kept, runner exit None, 2 of 24 ended 0, new 2",
      s54.get("node_disposition", {}).get("kind") == "node-failure" and s54["exit"] == 265 and s54["runner_exit"] is None
      and s54["ended"] == 2 and s54["exits"] == {"0": 2} and s54["new"] == 2 and "disposition" not in s54 and "slot_disposition" not in s54)
check("status: 22 coordinates uncompleted with origin node-failure; partition new = 8/15, 8/16",
      s54["partition"].get("uncompleted_origin") == "node-failure" and len(s54["partition"]["uncompleted"]) == 22
      and s54["partition"]["new"] == ["8/15", "8/16"])
check("status: closed-no-record is still examined and held (statuses exist)", "status evidence scoped" in s54.get("disposition_held", ""))
m_, v_, o_, l_, lv_, b_ = live_fixture(fetch_ok=False)
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: evidence not retrieved -> every alarm stands (24), reason kept",
      len(al) == 24 and all(any(t in a for a in al) for t in WANT_ALARMS) and "not retrieved" in summ[str(N)].get("node_disposition_held", ""))
m_, v_, o_, l_, lv_, b_ = live_fixture(doc=evidence_doc(node_state="free"))
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: node not down -> every alarm stands", len(al) == 24 and "not down" in summ[str(N)].get("node_disposition_held", ""))
m_, v_, o_, l_, lv_, b_ = live_fixture(statuses={0: st75})
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: a partial status -> the exit/runner/missing alarms stand (plus the partial slot's own)",
      any("scheduler exit 265" in a for a in al) and any("no runner end" in a for a in al) and "node_disposition" not in summ[str(N)])
m_, v_, o_, l_, lv_, b_ = live_fixture()
l_["entries"]["54"]["state"] = "running"
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: unsettled ledger -> alarms stand", any("scheduler exit 265" in a for a in al) and "SETTLED" in summ[str(N)].get("node_disposition_held", ""))
m_, v_, o_, l_, lv_, b_ = live_fixture()
o_[JID]["exit"] = 4
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: scheduler exit 4 -> not node failure; alarms stand", any("scheduler exit 4" in a for a in al) and "kill set" in summ[str(N)].get("node_disposition_held", ""))
m_, v_, o_, l_, lv_, b_ = live_fixture()
o_[JID]["mem_kb"] = 0.95 * 120 * 1024 ** 2
al, summ, _, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
check("status: other alarms of a node-dispositioned job are kept (scheduler memory above 90 %)",
      al == ["refit job 54: scheduler memory above 90 % of the request"] and "node_disposition" in summ[str(N)])
# the fetch: only settled no-runner-end refit entries whose settlement exit is in the kill set ask for the evidence file
calls = []
R.sh = lambda cmd, timeout=900: (calls.append(cmd[-2]) or (1, "", "No such file"))
stg = tempfile.mkdtemp(); os.makedirs(os.path.join(stg, "campaign"))
json.dump({"entries": {"54": ENTRY, "3": dict(kind="shard", rep=3, state="settled", settle_note="job 3: qstat -xf Exit_status 271, x"),
                       "13": dict(kind="shard", rep=13, state="settled", runner_exit=4, settle_note="Exit_status 4 ....")}},
          open(os.path.join(stg, "campaign", "budget.json"), "w"))
res = R.fetch_job_outputs(dict(shard=dict(toolchain="/tc")), "refit", stg)
check("fetch: job 54 (settled, no runner end, Exit_status 265) asks for its .out AND its node evidence; job 3 (271) and job 13 (4) do not",
      "54.nodefail" in res and "3.nodefail" not in res and "13.nodefail" not in res and any(c.endswith("row19_screen_refit_54.nodefail.json") for c in calls))

# ---- 3. the admission ---------------------------------------------------------------------------------------------------------
def admit_fixture(doc=None):
    m_, v_, o_, l_, lv_, b_ = live_fixture(doc=doc)
    al, summ, jobs, _ = R.reconcile(m_, "refit", v_, o_, l_, lv_)
    root = m_["storage"]["root"]; os.makedirs(m_["storage"]["campaign"]); os.makedirs(os.path.join(m_["shard"]["toolchain"], "jobs"))
    json.dump(l_, open(os.path.join(m_["storage"]["campaign"], "budget.json"), "w"))
    open(NF.evidence_path(m_, "refit", N), "wb").write(b_)
    json.dump(v_, open(os.path.join(root, "gate", "verify_refit_x.json"), "w"))
    d = summ[str(N)]["node_disposition"]
    bound = dict(jobs=jobs, verify_file="verify_refit_x.json", node_evidence={str(N): dict(file=d["evidence_file"], sha256=d["evidence_sha256"])})
    return m_, summ[str(N)], bound


m_, sj, bound = admit_fixture()
check("admission: the receipt's node disposition recomputes exactly", SA.node_disposition_problem(m_, None, "refit", N, sj, bound) == "")
check("admission: the summary passes job_summary_problem", SA.job_summary_problem(m_, str(N), sj) == "")
check("admission: NEVER a pilot", "never qualifies a pilot" in SA.job_summary_problem(m_, str(N), sj, pilot=True))
VU = json.load(open(os.path.join(m_["storage"]["root"], "gate", "verify_refit_x.json")))
check("admission: units reconcile against the plan minus the 22 node-failure coordinates", SA.units_problem(m_, VU, dict(jobs={str(N): sj})) == "")
check("admission: the transition check passes on the same settled certificate", SA.transition_problem(m_, "refit", dict(jobs={str(N): sj})) == "")
hist = SA.crash_history(dict(jobs={str(N): sj}), lambda m: None)
check("admission: crash_history counts NOTHING for a node failure (the two-crash rule is untouched)", hist == {} and SA.crash_excluded(hist, None) == {})
check("admission: held_accounting does not ask for a slot disposition (no runner exit 4)", SA.held_accounting_problem(m_, "refit", dict(jobs={str(N): sj})) == "")
open(NF.evidence_path(m_, "refit", N), "ab").write(b"\n")
check("admission: changed evidence bytes on disk -> refused", "not the bytes the receipt bound" in SA.node_disposition_problem(m_, None, "refit", N, sj, bound))
m_, sj, bound = admit_fixture()
open(SA.job_output_path(m_, "refit", N), "w").write(f"exit 265 job {JID}\n")
check("admission: a PBS .out that appeared after the receipt -> refused", "exists now" in SA.node_disposition_problem(m_, None, "refit", N, sj, bound))
m_, sj, bound = admit_fixture()
sj2 = copy.deepcopy(sj); sj2["node_disposition"]["uncompleted"] = sj2["node_disposition"]["uncompleted"][:-1]
check("admission: an edited disposition (one coordinate dropped) -> refused", SA.node_disposition_problem(m_, None, "refit", N, sj2, bound) != "")
sj3 = copy.deepcopy(sj); sj3["partition"]["uncompleted_origin"] = "crashed-slot"
check("admission: wrong uncompleted origin -> refused", "node-failure" in SA.node_disposition_problem(m_, None, "refit", N, sj3, bound))
b2 = copy.deepcopy(bound); b2["node_evidence"] = {}
check("admission: the receipt binds no node evidence -> refused", "does not bind" in SA.node_disposition_problem(m_, None, "refit", N, sj, b2))
sj4 = copy.deepcopy(sj); sj4["slot_disposition"] = dict(kind=SA.CRASH_KIND)
check("admission: two dispositions on one job -> refused", "one disposition" in SA.node_disposition_problem(m_, None, "refit", N, sj4, bound))
sj5 = copy.deepcopy(sj); sj5["ended"] = 24
check("admission: a summary claiming every worker ended -> refused", SA.job_summary_problem(m_, str(N), sj5) != "")
sj6 = copy.deepcopy(sj); sj6["exit"] = 271
check("admission: a node-dispositioned summary with exit 271 -> refused", SA.job_summary_problem(m_, str(N), sj6) != "")
led = json.load(open(os.path.join(m_["storage"]["campaign"], "budget.json"))); led["entries"]["54"]["settled_core_h"] = 1.0
json.dump(led, open(os.path.join(m_["storage"]["campaign"], "budget.json"), "w"))
check("admission: a changed settlement certificate -> refused (disposition and transition)",
      "certificate" in SA.node_disposition_problem(m_, None, "refit", N, sj, bound) and "certificate" in SA.transition_problem(m_, "refit", dict(jobs={str(N): sj})))
m_, sj, bound = admit_fixture()
led = json.load(open(os.path.join(m_["storage"]["campaign"], "budget.json"))); led["entries"]["54"]["runner_exit"] = 0
json.dump(led, open(os.path.join(m_["storage"]["campaign"], "budget.json"), "w"))
check("admission: a runner end recorded after the receipt -> transition refused", "no runner end" in SA.transition_problem(m_, "refit", dict(jobs={str(N): sj})))
m_, sj, bound = admit_fixture()
p_o = os.path.join(m_["storage"]["root"], "timing", "rep999"); os.makedirs(p_o)
open(os.path.join(p_o, "t_777.json"), "w").write(json.dumps(dict(rep=999, index=777, job=JID, slot=19)))
check("admission: an orphan same-job timing written after the receipt -> refused", "not a node-failure disposition" in SA.node_disposition_problem(m_, None, "refit", N, sj, bound))
m_, sj, bound = admit_fixture()
NF.capture_pin = lambda: None
check("admission: under controls that pin no capture script (v17) -> refused", "pinned capture script" in SA.node_disposition_problem(m_, None, "refit", N, sj, bound))
NF.capture_pin = lambda: PIN
uo = SA.units_problem(m_, VU, dict(jobs={str(N): dict(sj, node_disposition=dict(sj["node_disposition"], uncompleted=["9/9"]))}))
check("admission: units_problem refuses node-failure coordinates the job did not plan", "not planned" in uo)

# ---- 4. the capture script and the candidate controls ---------------------------------------------------------------------
QX = (f"Job Id: {JID}\n    Job_Name = t1_screen_54\n    job_state = F\n    exec_host = cnode0240/0*24\n    Exit_status = 265\n"
      "    resources_used.mem = 41763220kb\n    resources_used.walltime = 17:21:10\n    Resource_List.walltime = 48:00:00\n"
      "    stime = Tue Oct 20 02:19:20 2026\n    mtime = Tue Oct 20 20:00:36 2026\n    Variable_List = PBS_O_HOME=/home/x,PBS_O_LANG=en_US.U\n"
      "\tTF-8,PBS_O_LOGNAME=x\n")
PX = ("cnode0240\n     Mom = cnode0240\n     state = down\n     comment = node down: communication closed\n"
      "     last_state_change_time = Tue Oct 20 20:00:36 2026\n")


def run_capture(qx=QX, px=PX, extra=(), tz="Africa/Johannesburg"):
    d, root, man, units = fixture()
    os.makedirs(os.path.join(man["shard"]["toolchain"], "jobs")); os.makedirs(man["storage"]["campaign"])
    json.dump({"entries": {"54": ENTRY}}, open(os.path.join(man["storage"]["campaign"], "budget.json"), "w"))
    mp = os.path.join(d, "man.json"); json.dump(dict(man, role="refit"), open(mp, "w"))
    for rel, body in extra:
        open(os.path.join(man["shard"]["toolchain"], "jobs", rel), "w").write(body)
    CAP.run = lambda cmd: (0, qx, "") if cmd[0] == "qstat" else (0, px, "")
    old = os.environ.get("TZ"); os.environ["TZ"] = tz; __import__("time").tzset()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = CAP.main(["--manifest", mp, "--role", "refit", "--job", "54"])
    finally:
        if old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old
        __import__("time").tzset()
    p = NF.evidence_path(man, "refit", N)
    return rc, (open(p, "rb").read() if os.path.exists(p) else None), buf.getvalue(), man, units


rc, b, out, mc, uc = run_capture()
dc = json.loads(b) if b else {}
check("capture: writes ONE strict evidence file of job 54 (SAST host), no raw text, sha of the script, every field as printed",
      rc == 0 and b is not None and len(b) <= NF.MAX_BYTES and dc["capture_sha256"] == PIN and dc["utc_offset_s"] == 7200
      and dc["qstat"]["mtime_epoch"] == 1792519236 and dc["node"]["last_state_change_epoch"] == 1792519236 and dc["qstat"]["Exit_status"] == 265
      and dc["pbs_output_present"] == dict(out=False, err=False) and "Variable_List" not in b.decode() and "Job Id" not in b.decode())
check("capture: its own output is accepted by the shared rule (the job-54 positive, end to end)",
      b is not None and NF.node_failure_evidence(mc, "refit", N, copy.deepcopy(ENTRY), PLAN, JID, dict(state="F", exit=265), b, uc, [ENTRY], pin=PIN)[1] == "")
rc, b, out, _, _ = run_capture(px=PX.replace("state = down", "state = free"))
check("capture: node no longer down -> refused, nothing written", rc == 3 and b is None and "not down" in out)
rc, b, out, _, _ = run_capture(qx=QX.replace("job_state = F", "job_state = R"))
check("capture: job not F -> refused, nothing written", rc == 3 and b is None)
rc, b, out, _, _ = run_capture(qx=QX.replace("cnode0240/0*24", "cnode0240/0*12+cnode0241/0*12"))
check("capture: two exec nodes -> refused", rc == 3 and b is None)
rc, b, out, _, _ = run_capture(extra=[("row19_screen_refit_54.nodefail.json", "{}")])
check("capture: an existing evidence file is never overwritten", rc == 3 and "already exists" in out)
CAP.run = None
d_, r_, m_c, u_ = fixture(); os.makedirs(m_c["storage"]["campaign"])
json.dump({"entries": {"54": dict(ENTRY, runner_exit=0)}}, open(os.path.join(m_c["storage"]["campaign"], "budget.json"), "w"))
mp = os.path.join(d_, "man.json"); json.dump(dict(m_c, role="refit"), open(mp, "w"))
with contextlib.redirect_stdout(io.StringIO()) as bf:
    rcx = CAP.main(["--manifest", mp, "--role", "refit", "--job", "54"])
check("capture: a job with a runner end is refused before any scheduler query", rcx == 3 and "runner end" in bf.getvalue())
rc, b, out, _, _ = run_capture(extra=[("row19_screen_refit_54.out", "x")])
check("capture: a present PBS .out is recorded (and the rule then refuses it)", rc == 0 and json.loads(b)["pbs_output_present"]["out"] is True)

CTL = json.load(open(os.path.join(CAND, "row19_screen_controls.json")))
LIVE_CTL = json.load(open(os.path.join(CHPC, "row19_screen_controls.json")))
v17, v18 = CTL["versions"][-2], CTL["versions"][-1]
check("controls v18: versions 1-17 byte-equal to the adopted v17 controls", CTL["versions"][:-1] == LIVE_CTL["versions"]
      and json.dumps(CTL["versions"][:-1], indent=1) == json.dumps(LIVE_CTL["versions"], indent=1))
changed = sorted(k for k in set(v17["files"]) | set(v18["files"]) if v17["files"].get(k) != v18["files"].get(k))
check("controls v18: exactly four pins differ (admission, status, NEW nodefail rule, NEW capture script)",
      changed == ["chpc/row19_nodefail_capture.py", "chpc/row19_screen_admit.py", "chpc/row19_screen_nodefail.py", "chpc/row19_screen_status.py"])
check("controls v18: each pin is this folder's bytes", all(v18["files"][f"chpc/{n}"] == hashlib.sha256(open(os.path.join(CAND, n), "rb").read()).hexdigest()
                                                         for n in ("row19_screen_admit.py", "row19_screen_status.py", "row19_screen_nodefail.py", "row19_nodefail_capture.py")))
check("controls v18: every other key (partition e2, sub_envelopes, qualification_S) equals v17",
      {k: v for k, v in v18.items() if k not in ("version", "commit", "reviewed", "files")} == {k: v for k, v in v17.items() if k not in ("version", "commit", "reviewed", "files")})
check("controls v18: the candidate admission reads these controls, so capture_pin() is the capture script's bytes",
      load("r19_nf_pin", os.path.join(CAND, "row19_screen_nodefail.py")).capture_pin() == PIN)
check("build_v18 --check: deterministic", subprocess.run([sys.executable, os.path.join(CAND, "build_v18.py"), "--check"], capture_output=True).returncode == 0)
check("Python 3.7 grammar for every candidate file", all(ast.parse(open(os.path.join(CAND, f)).read(), feature_version=(3, 7)) for f in
                                                          ("row19_screen_nodefail.py", "row19_nodefail_capture.py", "row19_screen_status.py", "row19_screen_admit.py", "build_v18.py")))
LIVE_PINS = {f: hashlib.sha256(open(os.path.join(T1, f), "rb").read()).hexdigest() for f in ("chpc/row19_screen_admit.py", "chpc/row19_screen_status.py", "chpc/row19_screen_controls.json")}
check("the live tree is untouched (admission c3960464, status a9f9180b, controls 9ea4e727)",
      LIVE_PINS == {"chpc/row19_screen_admit.py": "c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed",
                    "chpc/row19_screen_status.py": "a9f9180b73438221788d745567603fd267befca8fbc60528e3e7de47421ff64a",
                    "chpc/row19_screen_controls.json": "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"}
      and not os.path.exists(os.path.join(CHPC, "row19_screen_nodefail.py")) and not os.path.exists(os.path.join(CHPC, "row19_nodefail_capture.py")))

# ---- 5. replay on the REAL 20 Oct 20:19Z refit snapshot (skipped when absent) ----------------------------------------------
RC_P = os.path.join(CHPC, "results", "row19_screen", "receipts", "watch_refit_20261020T201925Z.json")
VF_P = os.path.join(CHPC, "results", "row19_screen", "receipts", "verify_refit_20261020T201925Z.json")
if REAL and os.path.exists(RC_P) and os.path.exists(VF_P):
    rc0 = json.load(open(RC_P)); man0 = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))
    dd = tempfile.mkdtemp(); live = os.path.join(dd, "refit"); shutil.copytree(LIVE, live)
    fetch = json.load(open(os.path.join(live, "jobs", "_fetch.json")))
    b = ev_bytes(evidence_doc()); name = NF.evidence_name("refit", N)
    open(os.path.join(live, "jobs", name), "wb").write(b)
    fetch[f"{N}.nodefail"] = dict(file=name, rc=0, ok=True, sha256=hashlib.sha256(b).hexdigest())
    json.dump(fetch, open(os.path.join(live, "jobs", "_fetch.json"), "w"))
    obs = {s["job_id"]: dict(state=s["state"], exit=s["exit"], mem_kb=s["mem_kb"], walltime_req_s=s.get("requested_walltime_s"))
           for s in rc0["jobs"].values() if s.get("job_id")}
    ledger = json.load(open(os.path.join(live, "campaign", "budget.json")))
    R.MANIFEST_PATH = os.path.join(CHPC, "row19_screen_manifest.json")
    al, summ, _, _ = R.reconcile(man0, "refit", json.load(open(VF_P)), obs, ledger, live)
    print("   replay alarms:", al[:5], "| job 54 held:", summ["54"].get("node_disposition_held"))
    check(f"REAL 20 Oct 20:19Z snapshot (receipt alarms: {len(rc0['alarms'])}, all job 54's): with job 54's modelled node evidence the "
          "reconciliation raises ZERO alarms", len(rc0["alarms"]) == 24 and al == [] and summ["54"]["node_disposition"]["no_status_slots"] == NOSTAT)
    keys = ("ended", "exits", "new", "resumed", "left", "partition", "disposition", "slot_disposition", "failed_units")
    diff = [n for n, s in rc0["jobs"].items() if n != "54" and any(s.get(k) != summ[n].get(k) for k in keys)]
    check(f"REAL replay: every other job's reconciled outcome equals the v17 receipt's ({len(rc0['jobs']) - 1} jobs)", diff == [])
    check("REAL replay: closed-no-record job 3 and the slot-dispositioned jobs keep their dispositions",
          summ["3"].get("disposition", {}).get("kind") == "closed-no-record" and summ["13"].get("slot_disposition", {}).get("kind") == SA.CRASH_KIND)
else:
    print("skip REAL replay (needs the local live snapshot and the 20 Oct 20:19Z receipt + verifier)")

print(f"\n{npass[0]} passed, {len(fails)} failed")
print("ALL OK" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)

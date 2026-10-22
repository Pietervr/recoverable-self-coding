"""Controls v19 CANDIDATE (NOT adopted): tests of the OPERATIONAL-LOSS disposition (chpc/candidate_v19_oploss), Mac, pure python.

Synthetic fixtures (a 6-slot refit job 70, PBS 7600001.sched01) for: a node loss WITHOUT evidence, a walltime kill (exit 271)
with a salvaged record, a scheduler kill (negative JOB_EXEC code, no status at all), a crashed worker (status exit 4, HELD job),
an UNSETTLED terminal job (still blocks), integrity alarms (still block or refuse). Then the admission's exact recompute and
its refusals, the precedence of the existing dispositions, the REAL replay of the newest local generation-18 receipt (zero
alarms, job 54 still node-dispositioned, every job summary byte-equal) when the local snapshot is present, and the controls.

    python3 chpc/candidate_v19_oploss/test_v19_oploss.py          (from workspace_demo/t1_access)"""
import ast, copy, glob, hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):                       # the candidate admission must be what `import row19_screen_admit` finds
    sys.path.insert(0, p)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m)
    return m


SA = load("row19_screen_admit", os.path.join(CAND, "row19_screen_admit.py"))
NF = load("row19_screen_nodefail", os.path.join(CHPC, "row19_screen_nodefail.py"))       # unchanged v18 bytes
R = load("r19_status_v19", os.path.join(CAND, "row19_screen_status.py"))
R.ec2_reconcile = lambda *a, **k: {}
fails = []; npass = [0]


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


JID, N, TOKEN = "7600001.sched01", 70, "tok70abcdef01"
PLAN = dict(job=N, slots=[dict(slot=s, rep=5, indices=[10 + s]) for s in range(3)] + [dict(slot=s, rep=8, indices=[20 + s - 3]) for s in range(3, 6)],
            queue="serial", walltime_s=172800.0, token=TOKEN, created=1792600000.0)
IDS = {"5": "I5", "8": "I8"}
KEY = {sl["slot"]: f"{sl['rep']}/{sl['indices'][0]}" for sl in PLAN["slots"]}


def stat(s, exit=0, new=None, left=None, ident=None):
    sl = PLAN["slots"][s]; idx = sl["indices"]
    new = idx if new is None and not left else (new or [])
    left = left if left is not None else [i for i in idx if i not in new]
    return dict(job=JID, slot=s, rep=sl["rep"], ident=ident or IDS[str(sl["rep"])], indices=idx, new=new, resumed=[], left=left, exit=exit,
                reason="" if exit in (0, 75) else "exception: x", host="cnode0300", started=1792600100.0, ended=1792610000.0,
                wall_s=9900.0, maxrss=2 ** 31, cpu_s=9000.0)


def entry(ex, settled=True, runner_exit=None, note=None):
    e = dict(kind="shard", rep=N, job_id=JID, token=TOKEN, state="settled" if settled else "running", cores=24, walltime_s=172800.0,
             runner_started=1792600090.0, settled_core_h=100.0, settled_at=1792620000.0,
             settle_note=note or f"refit job {N}: qstat -xf Exit_status {ex}, resources_used.walltime 04:10:00, job_state F")
    if not settled:
        for k in ("settled_core_h", "settled_at", "settle_note"):
            e.pop(k)
    if runner_exit is not None:
        e.update(runner_exit=runner_exit, runner_ended=1792619000.0, runner_wall_s=15000.0)
    return e


def write_unit(root, units, s, k, slot=None, job=JID):
    r, i = (int(x) for x in k.split("/"))
    os.makedirs(os.path.join(root, "timing", f"rep{r}"), exist_ok=True); os.makedirs(os.path.join(root, "records", f"rep{r}"), exist_ok=True)
    json.dump(dict(rep=r, index=i, ident=IDS[str(r)], job=job, slot=s if slot is None else slot, wall_s=1, fit_seconds=1, maxrss=1, t=1),
              open(os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json"), "w"))
    json.dump(dict(rep=i, sha=f"s{r}_{i}", ident=IDS[str(r)]), open(os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"), "w"))
    units[k] = dict(record=dict(ok=True, sha=f"s{r}_{i}"), timing=dict(ok=True, job=job, slot=s if slot is None else slot))


def world(statuses, salvage=(), extra_files=(), logs_exit=(), ex=265, runner_exit=None, settled=True, note=None, mem_kb=1000):
    """(man, verify, obs, ledger, live): a root holding job 70's plan, the given statuses {slot: status} (absent = no status) with
    a record + timing for every status's new coordinate, salvaged no-status coordinates' record + timing, a header log per slot."""
    d = tempfile.mkdtemp(); root = os.path.join(d, "live", "root")
    for sub in ("plans", "status", "records", "timing", "gate", "logs"):
        os.makedirs(os.path.join(root, sub))
    json.dump(PLAN, open(os.path.join(root, "plans", f"job_{N}.json"), "w"), indent=1)
    units = {}
    for s, st in sorted(statuses.items()):
        json.dump(st, open(os.path.join(root, "status", f"job{JID}.slot{s}.json"), "w"), indent=1)
        for i in st["new"]:
            write_unit(root, units, s, f"{st['rep']}/{i}")
    for s in salvage:
        write_unit(root, units, s, KEY[s])
    for s in range(6):
        sl = PLAN["slots"][s]
        body = f"worker job {JID} slot {s}: rep {sl['rep']} identity x indices {sl['indices']}\n"
        if s in statuses or s in logs_exit:
            body += f"worker job {JID} slot {s}: exit 0 new {sl['indices']} resumed [] left [] \n"
        open(os.path.join(root, "logs", f"job{JID}.slot{s}.log"), "w").write(body)
    for rel, body in extra_files:
        p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
    live = os.path.join(d, "live"); os.makedirs(os.path.join(live, "jobs")); os.makedirs(os.path.join(d, "campaign"))
    json.dump({str(N): dict(file=f"row19_screen_refit_{N}.out", rc=1, ok=False, sha256=None, err="No such file or directory")},
              open(os.path.join(live, "jobs", "_fetch.json"), "w"))
    man = dict(storage=dict(root=root, campaign=os.path.join(d, "campaign")), shard=dict(toolchain=os.path.join(d, "tc")),
               datasets=dict(identities=IDS, reps=[5, 8]), pbs=dict(mem_gb=120, mem_stop_gib=4.5, deadline_reserve_s=1800))
    ledger = {"entries": {str(N): entry(ex, settled, runner_exit, note)}}
    verify = dict(units=units, bindings={"5": dict(ok=True, declared_ident_equal=True), "8": dict(ok=True, declared_ident_equal=True)})
    obs = {JID: dict(state="F", exit=ex, mem_kb=mem_kb, walltime_req_s=172800.0)}
    return man, verify, obs, ledger, live


def run(w):
    man, verify, obs, ledger, live = w
    al, summ, jobs, _ = R.reconcile(man, "refit", verify, obs, ledger, live)
    return al, summ[str(N)], jobs


def admit_ready(w):
    """Write the world as the admission sees it (ledger, retained verifier); return (man, summary, bound)."""
    man, verify, obs, ledger, live = w
    al, s, jobs = run(w)
    json.dump(ledger, open(os.path.join(man["storage"]["campaign"], "budget.json"), "w"))
    json.dump(verify, open(os.path.join(man["storage"]["root"], "gate", "verify_refit_x.json"), "w"))
    return man, s, dict(jobs=jobs, verify_file="verify_refit_x.json"), al


def admit_ok(label, w):
    man, s, bound, al = admit_ready(w)
    vu = json.load(open(os.path.join(man["storage"]["root"], "gate", "verify_refit_x.json")))
    rec = dict(jobs={str(N): s})
    got = (SA.oploss_disposition_problem(man, None, "refit", N, s, bound), SA.job_summary_problem(man, str(N), s), SA.units_problem(man, vu, rec),
           SA.transition_problem(man, "refit", rec), SA.held_accounting_problem(man, "refit", rec))
    check(f"{label}: admission recomputes exactly; summary, units, transition and HELD accounting pass {got if any(got) else ''}", got == ("",) * 5)
    check(f"{label}: NEVER a pilot", "never qualifies a pilot" in SA.job_summary_problem(man, str(N), s, pilot=True))
    hist = SA.crash_history(rec, lambda m: None)
    check(f"{label}: crash_history counts nothing (the two-crash rule untouched)", hist == {} and SA.crash_excluded(hist, None) == {})
    return man, s, bound


ALL = {s: stat(s) for s in range(6)}

# ---- 1. node loss WITHOUT evidence (exit 265, no runner end, slots 0-1 completed, 2-5 no status, no node document) -------------
w = world({0: stat(0), 1: stat(1)}, ex=265)
al, s, _ = run(w)
d = s.get("operational_loss") or {}
check("node loss without evidence: ZERO alarms", al == [])
check("node loss without evidence: node-failure held (evidence not retrieved), operational-loss granted",
      "not retrieved" in s.get("node_disposition_held", "") and d.get("kind") == "operational-loss" and "node_disposition" not in s)
check("node loss without evidence: 4 no-status slots, their 4 coordinates uncompleted (origin operational-loss), records 5/10, 5/11 kept",
      d.get("no_status_slots") == [2, 3, 4, 5] and s["partition"]["uncompleted"] == sorted(KEY[x] for x in (2, 3, 4, 5))
      and s["partition"]["uncompleted_origin"] == "operational-loss" and s["partition"]["new"] == ["5/10", "5/11"] and s["new"] == 2)
check("node loss without evidence: the scheduler-exit, no-runner-end and 4 missing-status alarms are informational lines (6)",
      len(s.get("informational", [])) == 6 and any("scheduler exit 265" in x for x in s["informational"])
      and any("no runner end" in x for x in s["informational"]) and sum("no worker status" in x for x in s["informational"]) == 4)
check("node loss without evidence: exit 265 and runner exit None kept, charge kept, not a crash",
      s["exit"] == 265 and s["runner_exit"] is None and d["settled_core_h"] == 100.0 and d["counts_as_crash"] is False and d["runner_end"] is False)
admit_ok("node loss without evidence", w)

# ---- 2. walltime kill (exit 271), slot 4 died after publishing its record (salvaged), slot 5 nothing ---------------------------
w = world({0: stat(0), 1: stat(1), 2: stat(2), 3: stat(3)}, salvage=(4,), ex=271)
al, s, _ = run(w)
d = s.get("operational_loss") or {}
check("walltime kill 271: ZERO alarms; operational-loss granted", al == [] and d.get("kind") == "operational-loss")
check("walltime kill 271: slot 4's verified record of THIS job is salvaged (counted new), only slot 5's coordinate uncompleted",
      d.get("salvaged") == [KEY[4]] and d.get("uncompleted") == [KEY[5]] and KEY[4] in s["partition"]["new"] and s["new"] == 5)
check("walltime kill 271: node-failure never examined as granted (271 not in the kill set)", "node_disposition" not in s)
admit_ok("walltime kill 271", w)

# ---- 3. scheduler kill: negative JOB_EXEC code, no worker ever wrote a status ------------------------------------------------
w = world({}, ex=-11)
al, s, _ = run(w)
d = s.get("operational_loss") or {}
check("scheduler kill (-11, no status): ZERO alarms; all 6 coordinates uncompleted", al == [] and d.get("uncompleted") == sorted(KEY.values())
      and s["ended"] == 0 and s["exits"] == {})
admit_ok("scheduler kill -11", w)
w = world({0: stat(0)}, ex=-11, mem_kb=None)
al, s, _ = run(w)
check("scheduler kill with no observed scheduler memory: the memory alarm is informational too",
      al == [] and any("no finite observed scheduler memory" in x for x in s.get("informational", [])))
admit_ok("scheduler kill, memory unobserved", w)

# ---- 4. crashed worker: status exit 4 (HELD job, scheduler and runner exit 4), crash evidence (.out/.err) not retrieved ----------
st2 = stat(2, exit=4, new=[], left=[12])
w = world({0: stat(0), 1: stat(1), 2: st2, 3: stat(3), 4: stat(4), 5: stat(5)}, ex=4, runner_exit=4)
al, s, _ = run(w)
d = s.get("operational_loss") or {}
check("crashed worker exit 4: ZERO alarms; crashed-slot held (no .out/.err), operational-loss granted",
      al == [] and "slot_disposition_held" in s and d.get("crashed_slots") == [dict(slot=2, exit=4, left=["5/12"])])
check("crashed worker exit 4: the scheduler-exit, runner-exit and worker-exit alarms are informational",
      any("scheduler exit 4" in x for x in s.get("informational", [])) and any("runner exit 4" in x for x in s["informational"])
      and any("slot 2: worker exit 4" in x for x in s["informational"]))
check("crashed worker exit 4: its coordinate stays `left` (returned to the planner), nothing uncompleted, 5 records kept",
      s["partition"]["left"] == ["5/12"] and d["uncompleted"] == [] and s["new"] == 5 and s["exits"] == {"0": 5, "4": 1})
admit_ok("crashed worker exit 4", w)
st2b = stat(2, exit=4, new=[], left=[12], ident="WRONG")
al, s, _ = run(world({0: stat(0), 1: stat(1), 2: st2b, 3: stat(3), 4: stat(4), 5: stat(5)}, ex=4, runner_exit=4))
check("crashed worker with a wrong identity: granted, but the identity alarm (integrity) still stands",
      "operational_loss" in s and al == ["refit job 70 slot 2: the status names another identity than the declared one"])

# ---- 5. an UNSETTLED terminal job still blocks --------------------------------------------------------------------------------
al, s, _ = run(world({0: stat(0), 1: stat(1)}, ex=265, settled=False))
check("unsettled terminal job: NOT dispositioned, every alarm stands (exit, runner end, 4 missing statuses), reason names settling",
      "operational_loss" not in s and len(al) == 6 and "operator's step" in s.get("operational_loss_held", ""))

# ---- 6. integrity alarms still block -----------------------------------------------------------------------------------------
al, s, _ = run(world({0: stat(0), 1: stat(1)}, ex=265, note=f"refit job {N}: qstat -xf Exit_status 271, job_state F"))
check("ledger inconsistency (settlement Exit_status 271, observed 265): refused, alarms stand",
      "operational_loss" not in s and len(al) == 6 and "ledger inconsistency" in s.get("operational_loss_held", ""))
al, s, _ = run(world({0: stat(0), 1: stat(1), 2: stat(2), 3: stat(3), 4: stat(4)}, ex=4, runner_exit=0))
check("ledger inconsistency (runner exit 0 recorded while a slot has no status): refused, alarms stand",
      "operational_loss" not in s and "job-end code" in s.get("operational_loss_held", "") and any("no worker status" in a for a in al))
w = world({0: stat(0), 1: stat(1)}, ex=265)
open(os.path.join(w[4], "root", "status", f"job{JID}.slot2.json"), "w").write("{corrupt")
al, s, _ = run(w)
check("corrupt status: refused, the unreadable-status alarm and the job's alarms stand",
      "operational_loss" not in s and "unreadable" in s.get("operational_loss_held", "") and any("unreadable" in a for a in al))
w = world({0: stat(0), 1: stat(1)}, ex=265)
json.dump(stat(1), open(os.path.join(w[4], "root", "status", f"job{JID}.slot9.json"), "w"))
al, s, _ = run(w)
check("an unplanned (duplicate) status scoped to the job: refused, the foreign-status alarm stands",
      "operational_loss" not in s and any("no planned job and slot assigns" in a for a in al))
w = world({0: stat(0), 1: stat(1)}, ex=265)
w[1]["units"][KEY[3]] = dict(record=dict(ok=False, reason="corrupt"), timing=dict(ok=True, job=JID, slot=3))
al, s, _ = run(w)
check("a corrupt record of this job at a no-status coordinate: refused (unverifiable), alarms stand",
      "operational_loss" not in s and len([a for a in al if "invalid record" in a or "no worker status" in a]) >= 4)
al, s, _ = run(world({0: stat(0), 1: stat(1)}, ex=265, extra_files=[("records/rep8/rec_020.json.tmp.123", "x")]))
check("a temporary file at a no-status coordinate: refused, alarms stand", "operational_loss" not in s and "temporary" in s.get("operational_loss_held", ""))
al, s, _ = run(world({0: stat(0), 1: stat(1)}, ex=265, logs_exit=(3,)))
check("a no-status slot whose log reports an exit: refused, alarms stand", "operational_loss" not in s and "log reports an exit" in s.get("operational_loss_held", ""))
al, s, _ = run(world({0: stat(0), 1: stat(1)}, ex=265, extra_files=[("timing/rep9/t_001.json", json.dumps(dict(rep=9, index=1, job=JID, slot=0)))]))
check("an orphan same-job timing outside the plan: refused (V15-1), alarms stand", "operational_loss" not in s and "timing" in s.get("operational_loss_held", ""))
w = world({0: stat(0), 1: stat(1)}, ex=265)
w[1]["units"]["5/10"]["record"] = dict(ok=False, reason="bad")
al, s, _ = run(w)
check("an invalid record of a completed slot: granted, but its no-valid-record alarm and the invalid-record alarm still stand",
      "operational_loss" in s and al and all("5/10" in a for a in al))
w = world({0: stat(0), 1: stat(1)}, ex=265)
w[2][JID]["walltime_req_s"] = 3600.0
al, s, _ = run(w)
check("a walltime request that is not the plan's: the alarm stands beside the disposition", "operational_loss" in s and len(al) == 1 and "walltime request" in al[0])
w = world({0: stat(0), 1: stat(1)}, ex=265, mem_kb=0.95 * 120 * 1024 ** 2)
al, s, _ = run(w)
check("scheduler memory above 90 %: the alarm stands beside the disposition", "operational_loss" in s and al == ["refit job 70: scheduler memory above 90 % of the request"])
check("anchor and producer-verifier alarms are untouched code paths (anchor_alarms still alarms a difference)",
      R.anchor_alarms(dict(anchors=dict(problem="anchor 3 differs"))) != [])

# ---- 7. a clean job is never examined; an existing disposition takes precedence ---------------------------------------------
al, s, _ = run(world(ALL, ex=0, runner_exit=0))
check("a clean job (0/0, every slot 0): no alarm, no operational-loss key of any kind", al == [] and not any(k.startswith("operational_loss") for k in s))
w = world({0: stat(0), 1: stat(1)}, ex=265)
check("status --qualify refuses an operational-loss job (code path present)", "it never qualifies" in open(os.path.join(CAND, "row19_screen_status.py")).read())

# ---- 8. admission refusals ---------------------------------------------------------------------------------------------------
man, s, bound = admit_ok("refusals base (node loss)", world({0: stat(0), 1: stat(1)}, ex=265))
s2 = copy.deepcopy(s); s2["operational_loss"]["uncompleted"] = s2["operational_loss"]["uncompleted"][:-1]
check("admission: an edited disposition (one coordinate dropped) -> refused", SA.oploss_disposition_problem(man, None, "refit", N, s2, bound) != "")
s3 = copy.deepcopy(s); s3["partition"]["uncompleted_origin"] = "node-failure"
check("admission: wrong uncompleted origin -> refused", "operational-loss" in SA.oploss_disposition_problem(man, None, "refit", N, s3, bound))
s4 = copy.deepcopy(s); s4["node_disposition"] = dict(kind="node-failure")
check("admission: two dispositions on one job -> refused", "one disposition" in SA.oploss_disposition_problem(man, None, "refit", N, s4, bound))
s5 = copy.deepcopy(s); s5["ended"] = 6
check("admission: a summary claiming every worker ended -> refused", SA.job_summary_problem(man, str(N), s5) != "")
s6 = copy.deepcopy(s); s6["runner_exit"] = 0
check("admission: a summary with another runner exit -> refused", SA.job_summary_problem(man, str(N), s6) != "")
led = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json"))); led["entries"][str(N)]["settled_core_h"] = 1.0
json.dump(led, open(os.path.join(man["storage"]["campaign"], "budget.json"), "w"))
check("admission: a changed settlement certificate -> refused (disposition and transition)",
      "certificate" in SA.oploss_disposition_problem(man, None, "refit", N, s, bound) and "certificate" in SA.transition_problem(man, "refit", dict(jobs={str(N): s})))
man, s, bound = admit_ok("refusals base 2", world({0: stat(0), 1: stat(1)}, ex=265))
led = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json"))); led["entries"][str(N)].update(runner_exit=0, runner_ended=1.0, runner_wall_s=1.0)
json.dump(led, open(os.path.join(man["storage"]["campaign"], "budget.json"), "w"))
check("admission: a runner end recorded after the receipt -> transition refused", "same runner end" in SA.transition_problem(man, "refit", dict(jobs={str(N): s})))
man, s, bound = admit_ok("refusals base 3", world({0: stat(0), 1: stat(1)}, ex=265))
p_o = os.path.join(man["storage"]["root"], "timing", "rep999"); os.makedirs(p_o)
open(os.path.join(p_o, "t_777.json"), "w").write(json.dumps(dict(rep=999, index=777, job=JID, slot=0)))
check("admission: an orphan same-job timing written after the receipt -> refused", "not an operational-loss" in SA.oploss_disposition_problem(man, None, "refit", N, s, bound))
uo = SA.units_problem(man, json.load(open(os.path.join(man["storage"]["root"], "gate", "verify_refit_x.json"))),
                      dict(jobs={str(N): dict(s, operational_loss=dict(s["operational_loss"], uncompleted=["9/9"]))}))
check("admission: units_problem refuses operational-loss coordinates the job did not plan", "not planned" in uo)
check("admission: receipt_problem names the operational-loss branch and the four-key one-disposition rule",
      '"operational_loss" in sj' in open(os.path.join(CAND, "row19_screen_admit.py")).read()
      and '("disposition", "slot_disposition", "node_disposition", "operational_loss")' in open(os.path.join(CAND, "row19_screen_admit.py")).read())
ENV = dict(queue="serial", cores=24, walltime_s=172800.0, mem_gb=120, nodetype="haswell_reg", deadline_reserve_s=1800, source="resources first_job=10")
_re = SA.resolve_envelope; SA.resolve_envelope = lambda *a, **k: (ENV, "")
pl = dict(PLAN, envelope=ENV); en = dict(entry(265), reserved_core_h=24 * 172800.0 / 3600.0)
sjo = dict(plan_walltime_s=172800.0, requested_walltime_s=None, operational_loss=dict(kind="operational-loss"))
check("admission: an operational-loss job whose walltime request PBS no longer reports passes the envelope check; any other job still refuses",
      SA.envelope_problem(man, None, "refit", N, pl, en, sjo) == ""
      and "walltime request" in SA.envelope_problem(man, None, "refit", N, pl, en, {k: v for k, v in sjo.items() if k != "operational_loss"})
      and "walltime request" in SA.envelope_problem(man, None, "refit", N, pl, en, dict(sjo, requested_walltime_s=3600.0)))
SA.resolve_envelope = _re
mh, sh_, bh, _ = admit_ready(world({0: stat(0), 1: stat(1), 2: st2, 3: stat(3), 4: stat(4), 5: stat(5)}, ex=4, runner_exit=4))
check("admission: HELD accounting refuses the same HELD entry when the receipt carries no disposition for it",
      "crash history unknown" in SA.held_accounting_problem(mh, "refit", dict(jobs={str(N): {k: v for k, v in sh_.items() if k != "operational_loss"}})))

# ---- 9. REAL replay: the newest local generation-18 receipt and the live snapshot (skipped when absent) ----------------------
LIVE = os.path.join(CHPC, "results", "row19_screen", "live", "refit")
RCD = os.path.join(CHPC, "results", "row19_screen", "receipts")
rcs = sorted(glob.glob(os.path.join(RCD, "watch_refit_*.json")))
if rcs and os.path.isdir(LIVE):
    RC_P = rcs[-1]; rc0 = json.load(open(RC_P)); VF_P = os.path.join(RCD, rc0["bound"]["verify_file"])
    man0 = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))
    dd = tempfile.mkdtemp(); live = os.path.join(dd, "refit"); shutil.copytree(LIVE, live)
    obs = {s_["job_id"]: dict(state=s_["state"], exit=s_["exit"], mem_kb=s_["mem_kb"], walltime_req_s=s_.get("requested_walltime_s"))
           for s_ in rc0["jobs"].values() if s_.get("job_id")}
    for s_ in rc0["jobs"].values():                                  # the ledger-settlement provenance fields, as observed
        if s_.get("observation") == "ledger-settlement":
            obs[s_["job_id"]].update(source="ledger-settlement", settle_note_sha256=s_["settle_note_sha256"], prior_receipt=s_.get("prior_receipt"),
                                     memory_evidence=s_.get("memory_evidence"), qstat_mem_kb=s_.get("qstat_mem_kb"),
                                     qstat_walltime_req_s=s_.get("qstat_walltime_req_s"), memory_breach=s_.get("memory_breach"))
    ledger = json.load(open(os.path.join(live, "campaign", "budget.json")))
    R.MANIFEST_PATH = os.path.join(CHPC, "row19_screen_manifest.json")
    al, summ, _, _ = R.reconcile(man0, "refit", json.load(open(VF_P)), obs, ledger, live)
    print(f"   replay of {os.path.basename(RC_P)} ({len(rc0['jobs'])} jobs, receipt alarms {len(rc0['alarms'])}):", al[:3])
    check(f"REAL replay {os.path.basename(RC_P)}: the v19 status view raises ZERO alarms (receipt: {len(rc0['alarms'])})", rc0["alarms"] == [] and al == [])
    check("REAL replay: job 54 is still node-dispositioned on the captured 730ea262, not operational-loss",
          summ["54"].get("node_disposition", {}).get("evidence_sha256", "").startswith("730ea262") and "operational_loss" not in summ["54"])
    rt = json.loads(json.dumps(summ))
    diff = [n for n in rc0["jobs"] if json.dumps(rc0["jobs"][n], sort_keys=True) != json.dumps(rt.get(n), sort_keys=True)]
    check(f"REAL replay: every one of the {len(rc0['jobs'])} job summaries is byte-equal to the v18 receipt's (closed-no-record, crashed-slot, "
          f"node-failure byte-stable) {diff[:5]}", diff == [] and len(rt) == len(rc0["jobs"]))
    check("REAL replay: closed-no-record job 3 and crashed-slot job 13 keep their dispositions, no job is operational-loss",
          summ["3"].get("disposition", {}).get("kind") == "closed-no-record" and summ["13"].get("slot_disposition", {}).get("kind") == SA.CRASH_KIND
          and not any("operational_loss" in v for v in summ.values()))
    shutil.rmtree(dd, ignore_errors=True)
else:
    print("skip REAL replay (needs the local live snapshot and a local refit receipt)")

# ---- 10. the candidate controls ---------------------------------------------------------------------------------------------
CTL = json.load(open(os.path.join(CAND, "row19_screen_controls.json")))
LIVE_CTL_B = open(os.path.join(CHPC, "row19_screen_controls.json"), "rb").read(); LIVE_CTL = json.loads(LIVE_CTL_B)
V18_SHA = "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b"
v18, v19 = CTL["versions"][-2], CTL["versions"][-1]
check("controls v19: versions 1-18 byte-equal to the adopted v18 controls (452b82df)", hashlib.sha256(LIVE_CTL_B).hexdigest() == V18_SHA
      and json.dumps(CTL["versions"][:-1], indent=1) == json.dumps(LIVE_CTL["versions"], indent=1) and v19["version"] == 19)
changed = sorted(k for k in set(v18["files"]) | set(v19["files"]) if v18["files"].get(k) != v19["files"].get(k))
V19_PINNED = ("row19_screen_admit.py", "row19_screen_status.py", "row19_ec2_state.py", "row19_ec2_e2qual.py", "row19_ec2_ingest.py")
check("controls v19: exactly five pins differ (admission, status; EC2 state, E2Q module, ingestion for E2Q3)",
      changed == sorted(f"chpc/{n}" for n in V19_PINNED) and sorted(v19["files"]) == sorted(v18["files"]))
check("controls v19: each pin is this folder's bytes", all(v19["files"][f"chpc/{n}"] == hashlib.sha256(open(os.path.join(CAND, n), "rb").read()).hexdigest()
                                                         for n in V19_PINNED))
check("controls v19: partition e2 48cea639, sub_envelopes, qualification_S and every other key equal v18",
      {k: v for k, v in v19.items() if k not in ("version", "commit", "reviewed", "files")} == {k: v for k, v in v18.items() if k not in ("version", "commit", "reviewed", "files")}
      and v19["partition"]["sha256"].startswith("48cea639"))
check("build_v19 --check: deterministic", subprocess.run([sys.executable, os.path.join(CAND, "build_v19.py"), "--check"], capture_output=True).returncode == 0)
check("Python 3.7 grammar for every candidate file", all(ast.parse(open(os.path.join(CAND, f)).read(), feature_version=(3, 7)) for f in
                                                          ("row19_screen_status.py", "row19_screen_admit.py", "build_v19.py", "promote_v19.py",
                                                           "row19_ec2_state.py", "row19_ec2_e2qual.py", "row19_ec2_ingest.py")))
LIVE_PINS = {f: hashlib.sha256(open(os.path.join(T1, f), "rb").read()).hexdigest() for f in
             ("chpc/row19_screen_admit.py", "chpc/row19_screen_status.py", "chpc/row19_screen_controls.json", "chpc/row19_ec2_state.py",
              "chpc/row19_ec2_e2qual.py", "chpc/row19_ec2_ingest.py")}
check("the live tree is untouched (admission e2260765, status 4710544a, controls 452b82df, EC2 state 7bdedafc, E2Q 5ceba551, ingestion 277c51b0)",
      LIVE_PINS == {"chpc/row19_screen_admit.py": "e22607650058ae2cbb8f19fe3e225d886bd2cc733adf02bb93dbc01d65f719af",
                    "chpc/row19_screen_status.py": "4710544a3861b688b0f2c89e67a8ba56cf65261a8900d4147658fee576f58232",
                    "chpc/row19_screen_controls.json": V18_SHA,
                    "chpc/row19_ec2_state.py": "7bdedafc7c90ec065217d9a7bbf53b88e1bf31e0c094dc34df730b4028bd038e",
                    "chpc/row19_ec2_e2qual.py": "5ceba55189dd351b2cc5a997b115cdbfd0d84f17397402fa7deb2b3e937025fa",
                    "chpc/row19_ec2_ingest.py": "277c51b0a24fee6b151180e99584a831c091ca4b30b6bd999a1221ff364bf54f"}
      and not os.path.exists(os.path.join(T1, "aws_ec2", "prod", "manifest_e2q3_e2.json")))

print(f"\n{npass[0]} passed, {len(fails)} failed")
print("ALL OK" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)

"""Bank REVISION B1 candidate: closed-no-record disposition tests (synthetic roots; the PBS output is bank job 11's real bytes).

    python3 chpc/candidate_bank_r1/test_bank_closed_no_record.py
Covers: the fully evidenced settled no-record job is dispositioned (alarms suppressed, loss kept, reps uncompleted); an
unsettled kill holds; a runner end holds; any status scoped to the job (planned, unplanned, parsed), an unreadable status
with no job named, a timing naming the job, an unreadable or temporary timing, a record at a planned rep without a later
bound completion, a missing/failed/changed PBS output retrieval, ADMISSION FAILED, an output not naming the job, and a note
exit differing from the observed exit all hold; a later bound retry (job 18) completes the reps without lifting the
disposition and is credited to job 18 only; the memory alarm survives a disposition; an ordinary exit-0 job is unchanged;
the admission recomputes and refuses a forged charge, a changed output, a missing
output binding, a stray binding, a bad exit without a disposition, and a status appearing after the receipt.
REPAIR R1 (Codex RSC 4295ed6) negatives: B1-1 a malformed records/b0240.json beside a valid canonical rep 24, an undeclared
rep and a directory hold; B1-2 after a clean receipt with a verified job-18 completion, a disk-only timing change (wall_s -1,
another seed), changed record bytes or a missing bound verification refuse, and the unchanged verified completion passes;
R2 (Codex RSC 82b7253): an extra records/ or timing/ b024.json followed by a newline beside the valid canonical rep 24 (job 11's
planned reps empty) holds the status view and refuses the admission; a non-ASCII-digit name holds; the clean inventory passes.
B1-3 a receipt missing job 11's summary AND output binding refuses; B1-4 missing, falsy or non-list alarms, a non-finite or
boolean time, and a qualification whose embedded receipt has no alarm list, refuse."""
import os, sys, json, shutil, tempfile, hashlib, copy

HERE = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(HERE)
sys.path[:0] = [HERE, CHPC]
import row22_bank_dispo as DP
import row22_bank_status as ST
import row22_bank_submit as SU
SU.task_seed = lambda man, r: 1                 # the synthetic timings carry seed 1 (the real one imports the pinned task)

OUT = open(os.path.join(HERE, "fixture_bank11", "row22_bank_11.out.txt"), "rb").read()
J11, J1, J18 = "7531003.sched01", "7523732.sched01", "7539999.sched01"
REPS11 = list(range(240, 264))
NOTE11 = "qstat -xf at settlement: job_state F Exit_status 271 resources_used.walltime 36:01:54 resources_used.mem 30722048kb"
NOTE1 = "qstat -xf at settlement: job_state F Exit_status 0 resources_used.walltime 24:46:28 resources_used.mem 20000000kb"
FAILS = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


class World:
    """A synthetic live snapshot (root, campaign, jobs) + toolchain, with job 1 done and job 11 wall-killed and settled."""
    def __init__(self, settled=True):
        self.d = tempfile.mkdtemp(prefix="bankB1_")
        self.live = os.path.join(self.d, "live"); self.root = os.path.join(self.live, "root")
        self.camp = os.path.join(self.live, "campaign"); self.tc = os.path.join(self.d, "toolchain")
        for sub in ("plans", "status", "timing", "records", "gate"):
            os.makedirs(os.path.join(self.root, sub))
        os.makedirs(self.camp); os.makedirs(os.path.join(self.live, "jobs")); os.makedirs(os.path.join(self.tc, "jobs"))
        self.man = dict(storage=dict(root=self.root, campaign=self.camp), bank=dict(toolchain=self.tc),
                        pbs=dict(mem_gb=120, mem_stop_gib=4.5), datasets=dict(reps=list(range(408))))
        self.plan(1, "tok1", list(range(0, 24))); self.plan(11, "dcb830e255e2", REPS11)
        e1 = dict(kind="bank", rep=1, token="tok1", job_id=J1, state="settled", settled_core_h=594.59, settled_at=1.0e9,
                  settle_note=NOTE1, runner_exit=0, runner_ended=1.0e9, runner_wall_s=89188.0)
        e11 = dict(kind="bank", rep=11, token="dcb830e255e2", job_id=J11, state="live", reserved_core_h=864.0, walltime_s=129600.0)
        if settled:
            e11.update(state="settled", settled_core_h=864.76, settled_at=1.79e9, settle_note=NOTE11)
        self.led = dict(cap_core_h=15000.0, entries={"tok1": e1, "dcb830e255e2": e11})
        self.save()
        for s in range(24):
            r = s
            self.status(J1, s, dict(job=J1, slot=s, reps=[r], new=[r], resumed=[], left=[], exit=0, wall_s=1.0, cpu_s=1.0, maxrss=1.0e9))
            self.output(r, J1, s)
        self.put_out(OUT)

    def plan(self, n, tok, reps):
        json.dump(dict(job=n, token=tok, slots=[dict(slot=i, reps=[r]) for i, r in enumerate(reps)]),
                  open(os.path.join(self.root, "plans", f"job_{n}.json"), "w"))

    def save(self):
        json.dump(self.led, open(os.path.join(self.camp, "budget.json"), "w"))

    def status(self, j, s, d):
        json.dump(d, open(os.path.join(self.root, "status", f"job{j}.slot{s}.json"), "w"))

    def output(self, r, j, s):
        json.dump(dict(bank_rep=r, seed=1, job=j, slot=s, wall_s=1.0, fit_seconds=1.0, maxrss=1.0, t=1.0),
                  open(os.path.join(self.root, "timing", f"b{r:03d}.json"), "w"))
        json.dump(dict(rep=r), open(os.path.join(self.root, "records", f"b{r:03d}.json"), "w"))

    def put_out(self, b, fetch_ok=True):
        name = "row22_bank_11.out"
        open(os.path.join(self.live, "jobs", name), "wb").write(b)
        open(os.path.join(self.tc, "jobs", name), "wb").write(b)
        json.dump({"11": dict(file=name, rc=0 if fetch_ok else 1, ok=fetch_ok, sha256=hashlib.sha256(b).hexdigest() if fetch_ok else None)},
                  open(os.path.join(self.live, "jobs", "_fetch.json"), "w"))

    def verify(self):
        reps = {}
        for p in sorted(os.listdir(os.path.join(self.root, "timing"))):
            if DP.canonical_name(p) is None:
                continue
            r = int(p[1:4])
            try:
                t = json.load(open(os.path.join(self.root, "timing", p)))
            except ValueError:                                   # as row22_bank_verify.timing_check: ok False
                reps[str(r)] = dict(record=None, timing=dict(ok=False, reason="not JSON")); continue
            rp = os.path.join(self.root, "records", f"b{r:03d}.json")
            reps[str(r)] = dict(record=dict(ok=True, file_sha256=DP.sha_file(rp)) if os.path.exists(rp) else None,
                                timing=dict(ok=True, job=t["job"], slot=t["slot"]))
        return dict(reps=reps)

    def obs(self, exit11=271, src11="qstat"):
        return {J1: dict(state="F", exit=0, source="ledger-settlement", mem_kb=20000000, memory_evidence=dict(kind="qstat")),
                J11: dict(state="F", exit=exit11, source=src11, mem_kb=30722048, memory_evidence=dict(kind="qstat"))}

    def run(self, **kw):
        return ST.reconcile(self.man, self.verify(), self.obs(**kw), self.led, live=self.live)

    def receipt(self):
        al, _, summary, jobs, outputs = self.run()
        line = json.dumps(dict(schema="row22-bank-verify-1", reps=self.verify()["reps"]), sort_keys=True)
        open(os.path.join(self.root, "gate", "verify_20261012T000000Z.json"), "w").write(line)
        bound = dict(jobs=jobs, job_outputs=outputs, verify_sha256=hashlib.sha256(line.encode()).hexdigest())
        return al, dict(jobs=summary, bound=bound)

    def close(self):
        shutil.rmtree(self.d, ignore_errors=True)


def j11_alarms(al):
    return [a for a in al if "job 11" in a]


# 1. the fully evidenced settled no-record job
w = World()
al, _, s, jobs, outs = w.run()
d = s["11"].get("disposition")
check("settled no-record job 11 is dispositioned", d is not None and d["kind"] == DP.DISPO_KIND)
check("its exit/runner-end/no-status alarms are suppressed (no alarm at all)", al == [])
check("the loss is kept: exit 271, charge 864.76, zero ended/new/resumed/left",
      d and d["scheduler_exit"] == 271 and d["settled_core_h"] == 864.76 and s["11"]["ended"] == 0 and s["11"]["new"] == 0 and s["11"]["exit"] == 271)
check("its 24 reps are uncompleted with origin plan", s["11"]["partition"] == dict(new=[], resumed=[], left=[], uncompleted=REPS11, uncompleted_origin="plan"))
check("the receipt binds the PBS output", outs == {"11": dict(file="row22_bank_11.out", sha256=hashlib.sha256(OUT).hexdigest())})
check("the ordinary exit-0 job 1 carries no disposition", "disposition" not in s["1"] and "disposition_held" not in s["1"])
check("a ledger-settlement observation also dispositions", ST.reconcile(w.man, w.verify(), w.obs(src11="ledger-settlement"), w.led, live=w.live)[2]["11"].get("disposition") is not None)
w.close()

# 2. holds
def held(label, mutate, **kw):
    w = World(settled=kw.pop("settled", True)); mutate(w)
    al, _, s, _, outs = w.run(**kw)
    check(f"HOLDS: {label}", s["11"].get("disposition") is None and len(j11_alarms(al)) >= 1 and "11" not in outs)
    w.close()

held("an unsettled kill", lambda w: None, settled=False)
held("a runner end in the ledger", lambda w: w.led["entries"]["dcb830e255e2"].update(runner_exit=4) or w.save())
held("a status of the job in a planned slot", lambda w: w.status(J11, 3, dict(job=J11, slot=3, reps=[243], new=[], resumed=[], left=[243], exit=75)))
held("a status of the job in an unplanned slot", lambda w: w.status(J11, 40, dict(job=J11)))
held("a status under another name naming the job", lambda w: json.dump(dict(job=J11), open(os.path.join(w.root, "status", "jobX.slot0.json"), "w")))
held("an unreadable status with no job named", lambda w: open(os.path.join(w.root, "status", "garbage.json"), "w").write("{"))
held("a timing naming the job (no record)", lambda w: json.dump(dict(bank_rep=250, job=J11, slot=10), open(os.path.join(w.root, "timing", "b250.json"), "w")))
held("an unreadable timing anywhere", lambda w: open(os.path.join(w.root, "timing", "b100.json"), "w").write("{"))
held("a temporary timing file", lambda w: open(os.path.join(w.root, "timing", "b251.json.tmp.123"), "w").write("{}"))
held("a temporary record file at a planned rep", lambda w: open(os.path.join(w.root, "records", "b252.json.tmp"), "w").write("{}"))
held("a record at a planned rep without a later bound completion", lambda w: w.output(253, J1, 0))
held("the PBS output not retrieved", lambda w: w.put_out(OUT, fetch_ok=False))
held("the PBS output changed after retrieval", lambda w: open(os.path.join(w.live, "jobs", "row22_bank_11.out"), "ab").write(b"x"))
held("ADMISSION FAILED in the output", lambda w: w.put_out(OUT + b"exit 4 job 7531003.sched01 end (ADMISSION FAILED)\n"))
held("an output not naming the job", lambda w: w.put_out(OUT.replace(J11.encode(), b"7000000.sched01")))
held("a note exit that is not the observed exit", lambda w: w.led["entries"]["dcb830e255e2"].update(settle_note=NOTE11.replace("271", "0")) or w.save())

# 3. the later bound retry, job 18
w = World()
w.plan(18, "tok18", REPS11)
w.led["entries"]["tok18"] = dict(kind="bank", rep=18, token="tok18", job_id=J18, state="live", reserved_core_h=1152.0, walltime_s=172800.0)
w.save()
for i, r in enumerate(REPS11):
    w.output(r, J18, i)
al, _, s, _, _ = w.run()
check("a later bound retry (job 18) completes the reps without lifting job 11's disposition", s["11"].get("disposition") is not None and not j11_alarms(al))
w.led["entries"]["tok18"]["job_id"] = None; w.save()
al, _, s, _, _ = w.run()
check("HOLDS: the same records under an UNBOUND later entry", s["11"].get("disposition") is None)
w.close()
w = World(); w.plan(18, "tok18", list(reversed(REPS11)))
w.led["entries"]["tok18"] = dict(kind="bank", rep=18, token="tok18", job_id=J18, state="live"); w.save()
for i, r in enumerate(REPS11):
    w.output(r, J18, i)
check("HOLDS: a later job's timing in a slot its plan did not assign", w.run()[2]["11"].get("disposition") is None)
w.close()

# 4. memory survives; qualification
w = World()
o = w.obs(); o[J11]["mem_kb"] = 0.95 * 120 * 1024 ** 2
al, _, s, _, _ = ST.reconcile(w.man, w.verify(), o, w.led, live=w.live)
check("the scheduler-memory alarm survives a disposition", s["11"].get("disposition") is not None and any("job 11: scheduler memory" in a for a in al))
w.close()

# 5. admission (recomputed on the current evidence)
w = World()
al, r = w.receipt()
w.man["storage"]["root"] = w.root
check("admission accepts the exact recomputed disposition", SU.dispositions_problem(w.man, r) == "")
r2 = copy.deepcopy(r); r2["jobs"]["11"]["disposition"]["settled_core_h"] = 0.0
check("admission refuses a forged charge", "differs" in SU.dispositions_problem(w.man, r2))
r2 = copy.deepcopy(r); del r2["bound"]["job_outputs"]["11"]
check("admission refuses a missing output binding", "does not bind" in SU.dispositions_problem(w.man, r2))
r2 = copy.deepcopy(r); r2["bound"]["job_outputs"]["1"] = dict(file="x", sha256="0" * 64)
check("admission refuses a stray output binding", "carry no disposition" in SU.dispositions_problem(w.man, r2))
r2 = copy.deepcopy(r); del r2["jobs"]["11"]["disposition"]
check("admission refuses a bad exit without a disposition", "carries no disposition" in SU.dispositions_problem(w.man, r2))
r2 = copy.deepcopy(r); r2["jobs"]["11"]["partition"]["uncompleted"] = REPS11[:-1]
check("admission refuses a partition that is not the plan's reps", SU.dispositions_problem(w.man, r2) != "")
open(os.path.join(w.tc, "jobs", "row22_bank_11.out"), "ab").write(b"later\n")
check("admission refuses an output changed since the receipt", "differs" in SU.dispositions_problem(w.man, r))
w.put_out(OUT)
w.status(J11, 5, dict(job=J11))
check("admission refuses a status naming the job that appeared after the receipt", "not closed-no-record" in SU.dispositions_problem(w.man, r))
w.close()
w = World(); al, r = w.receipt()
w.led["entries"]["dcb830e255e2"]["settle_note"] = NOTE11 + " resettled"; w.save()
check("admission refuses a replaced settlement certificate", "differs" in SU.dispositions_problem(w.man, r))
w.close()

# 7. REPAIR R1
held("B1-1 a malformed records/b0240.json beside a valid canonical rep 24",
     lambda w: (w.output(24, J1, 0), open(os.path.join(w.root, "records", "b0240.json"), "w").write("{")))
held("B1-1 an undeclared rep's record", lambda w: open(os.path.join(w.root, "records", "b999.json"), "w").write("{}"))
held("B1-1 a directory under records/", lambda w: os.makedirs(os.path.join(w.root, "records", "b240.json")))

def nl_world(sub, name="b024.json\n"):
    w = World(); w.output(24, J1, 0)
    open(os.path.join(w.root, sub, name), "w").write("{}")
    return w

for sub in ("records", "timing"):
    w = nl_world(sub)
    al, r = w.receipt(); s = w.run()[2]
    check(f"R2 HOLDS: an extra {sub}/'b024.json\\n' beside valid rep 24", s["11"].get("disposition") is None and j11_alarms(al))
    w2 = World(); w2.output(24, J1, 0); _, rc = w2.receipt()
    open(os.path.join(w2.root, sub, "b024.json\n"), "w").write("{}")
    check(f"R2 admission refuses after an extra {sub}/'b024.json\\n' appears", "not closed-no-record" in SU.dispositions_problem(w2.man, rc))
    w.close(); w2.close()
held("R2 a non-ASCII-digit name b\u0662\u0664\u0660.json", lambda w: open(os.path.join(w.root, "records", "b\u0662\u0664\u0660.json"), "w").write("{}"))
w = World(); w.output(24, J1, 0)
check("R2 a valid canonical inventory (rep 24 beside job 11) still dispositions", w.run()[2]["11"].get("disposition") is not None)
check("R2 canonical_name is exact", DP.canonical_name("b024.json") == 24 and DP.canonical_name("b024.json\n") is None
      and DP.canonical_name("b0240.json") is None and DP.canonical_name("b\u0662\u0664\u0660.json") is None)
w.close()

def retry_world():
    w = World(); w.plan(18, "tok18", REPS11)
    w.led["entries"]["tok18"] = dict(kind="bank", rep=18, token="tok18", job_id=J18, state="live", reserved_core_h=1152.0, walltime_s=172800.0)
    w.save()
    for i, r in enumerate(REPS11):
        w.output(r, J18, i)
    return w

def tamper_timing(w, **kv):
    tp = os.path.join(w.root, "timing", "b245.json"); t = json.load(open(tp)); t.update(kv); json.dump(t, open(tp, "w"))

w = retry_world(); al, r = w.receipt()
check("B1-2 the unchanged verified later completion passes the admission", not j11_alarms(al) and SU.dispositions_problem(w.man, r) == "")
tamper_timing(w, wall_s=-1)
check("B1-2 a disk-only timing wall_s -1 after the receipt refuses", "not closed-no-record" in SU.dispositions_problem(w.man, r))
w.close()
w = retry_world(); al, r = w.receipt(); tamper_timing(w, seed=2)
check("B1-2 a disk-only timing seed change after the receipt refuses", "not closed-no-record" in SU.dispositions_problem(w.man, r))
w.close()
w = retry_world(); al, r = w.receipt()
json.dump(dict(rep=245, replaced=True), open(os.path.join(w.root, "records", "b245.json"), "w"))
check("B1-2 changed record bytes after the receipt refuse", "not closed-no-record" in SU.dispositions_problem(w.man, r))
w.close()
w = retry_world(); al, r = w.receipt()
for p in os.listdir(os.path.join(w.root, "gate")):
    os.remove(os.path.join(w.root, "gate", p))
check("B1-2 a receipt whose bound verification is not in the gate refuses", "not in the gate" in SU.dispositions_problem(w.man, r))
w.close()
w = retry_world()
al, _, s, _, _ = ST.reconcile(w.man, None or dict(reps={}), w.obs(), w.led, live=w.live)
check("B1-2 the status view without a verification of the later completion holds", s["11"].get("disposition") is None)
w.close()

w = World(); al, r = w.receipt()
r2 = copy.deepcopy(r); del r2["jobs"]["11"]; del r2["bound"]["job_outputs"]["11"]
check("B1-3 a receipt missing job 11's summary and output binding refuses", "not one set" in SU.dispositions_problem(w.man, r2))
r2 = copy.deepcopy(r); r2["jobs"] = list(r2["jobs"].values())
check("B1-3 summaries that are not a mapping refuse", "not mappings" in SU.dispositions_problem(w.man, r2))
w.close()

good = dict(schema=SU.WATCH_SCHEMA, production=True, fresh=True, alarms=[], time=1000.0)
check("B1-4 a clean receipt passes the field check", SU.clean_receipt_fields(good, now=1100.0) == "")
for label, bad in (("missing alarms", {k: v for k, v in good.items() if k != "alarms"}), ("alarms None", dict(good, alarms=None)),
                   ("alarms ''", dict(good, alarms="")), ("alarms {}", dict(good, alarms={})), ("time NaN", dict(good, time=float("nan"))),
                   ("time True", dict(good, time=True)), ("time missing", {k: v for k, v in good.items() if k != "time"}),
                   ("fresh 1", dict(good, fresh=1)), ("stale", good)):
    check(f"B1-4 refuses: {label}", SU.clean_receipt_fields(bad, now=(1100.0 if label != "stale" else 1000.0 + SU.CEILING_S + 1)) != "")
w = World()
json.dump(dict(schema=SU.QUAL_SCHEMA, qualified_job=1, production=True, time=1.0, receipt={k: v for k, v in good.items() if k != "alarms"}),
          open(os.path.join(w.root, "gate", "qualified_bank_job1.json"), "w"))
check("B1-4 a qualification whose embedded receipt has no alarm list refuses", "embedded receipt" in SU.qualification_problem(w.man, None)[0])
w.close()

# 6. the planner: settled job 11 is not in flight; its reps are MISSING and planned first into the next number
w = World()
for r in range(24, 240):
    open(os.path.join(w.root, "records", f"b{r:03d}.json"), "w").write("{}")
done = {int(p[1:4]) for p in os.listdir(os.path.join(w.root, "records"))}
jobs, left = SU.plan_jobs(dict(w.man, pbs=dict(cores=24)), 1, 1, done - set(REPS11), set(range(264, 408)), set(range(1, 18)))
check("the planner puts reps 240-263 into job 18, one per slot", jobs and jobs[0]["job"] == 18 and [s["reps"][0] for s in jobs[0]["slots"]] == REPS11)
w.close()

print(f"\n{'ALL OK' if not FAILS else str(len(FAILS)) + ' FAILED'}")
sys.exit(1 if FAILS else 0)

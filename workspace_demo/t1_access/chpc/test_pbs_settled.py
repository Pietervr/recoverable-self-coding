"""REVISION 11 (R052 11 Oct, PBS history expiry): pbs_observe of the bank status and the v13 refit status candidate.
Settled ledger entries are observed from their settlement (never asked of qstat); unsettled ones stay fail-closed.

    python3 chpc/test_pbs_settled.py          (from workspace_demo/t1_access)"""
import importlib.util, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


BANK = load("bank_status_t", os.path.join(HERE, "row22_bank_status.py"))
R19 = load("r19_status_t", os.path.join(HERE, "candidate_v10r4", "row19_screen_status.py"))
NOTE = "job 9: qstat -xf Exit_status 0, resources_used.walltime 23:54:08, job_state F"
QSTAT_R = "Job Id: 2.sched01\n    job_state = R\n    resources_used.mem = 100kb\n    Resource_List.walltime = 30:00:00\n"
calls, fails = [], []


def stub(rc, out, err=""):
    def sh(cmd, timeout=None):
        calls.append(cmd[-1]); return rc, out, err
    return sh


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def settled(j, note=NOTE):
    return {j: dict(state="settled", job_id=j, settle_note=note, settled_at=1.0)}


for M, label in ((BANK, "bank"), (R19, "refit")):
    kw = dict(role="refit", receipts_dir=tempfile.mkdtemp()) if M is R19 else dict(receipts_dir=tempfile.mkdtemp())
    settled_q = ["qstat -xf 1.sched01"] if M is BANK else []          # bank: one tolerant memory-only query of the settled ids
    calls.clear(); M.sh = stub(153, "", "qstat: Unknown Job Id 1.sched01")
    obs, why = M.pbs_observe(["1.sched01"], None, settled("1.sched01"), **kw)
    check(f"{label}: settled + expired -> no failed observation, no state query", why == "" and calls == settled_q and obs["1.sched01"]["state"] == "F"
          and obs["1.sched01"]["exit"] == 0 and obs["1.sched01"]["source"] == "ledger-settlement")
    calls.clear(); M.sh = stub(0, QSTAT_R)
    obs, why = M.pbs_observe(["1.sched01", "2.sched01"], None, settled("1.sched01"), **kw)
    check(f"{label}: the state query asks only the unsettled id", why == "" and calls == settled_q + ["qstat -xf 2.sched01"]
          and obs["2.sched01"]["state"] == "R" and obs["1.sched01"]["state"] == "F")
    M.sh = stub(153, "", "qstat: Unknown Job Id 2.sched01")
    obs, why = M.pbs_observe(["1.sched01", "2.sched01"], None, settled("1.sched01"), **kw)
    check(f"{label}: unsettled + unknown -> alarm", obs is None and "qstat failed (rc 153)" in why)
    M.sh = stub(0, "")
    obs, why = M.pbs_observe(["2.sched01"], None, {}, **kw)
    check(f"{label}: unsettled + not described -> alarm", obs is None and "did not describe" in why)
    obs, why = M.pbs_observe(["1.sched01"], None, settled("1.sched01", "settled by hand, no scheduler evidence"), **kw)
    check(f"{label}: settled note without Exit_status -> alarm", obs is None and "no Exit_status" in why)
    obs, why = M.pbs_observe(["3.sched01"], None, settled("3.sched01", "walltime kill: qstat -xf Exit_status 271, job_state F"), **kw)
    check(f"{label}: non-zero settled exit kept", why == "" and obs["3.sched01"]["exit"] == 271)

# refit: scheduler facts carried from the newest fresh, production, alarm-free receipt that saw the same id F with the same exit
d = tempfile.mkdtemp()


def receipt(stamp, alarms=(), fresh=True, exit_=0, mem=47179688, obs=None, jid="1.sched01"):
    sj = dict(job_id=jid, state="F", exit=exit_, mem_kb=mem, requested_walltime_s=108000.0)
    if obs:
        sj["observation"] = obs
    json.dump(dict(schema=R19.WATCH_SCHEMA, role="refit", fresh=fresh, production=True, alarms=list(alarms), jobs={"1": sj}),
              open(os.path.join(d, f"watch_refit_{stamp}.json"), "w"))


receipt("20261010T100000Z", mem=111)
receipt("20261010T224529Z", mem=47179688)
receipt("20261011T041817Z", alarms=["qstat failed (rc 153)"], mem=999)             # newest, but alarmed: never a source
receipt("20261011T050000Z", obs="ledger-settlement", mem=555)                       # carried, not a scheduler observation
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=d)
o = obs["1.sched01"]
check("refit: memory and walltime request carried from the newest clean qstat receipt", why == "" and o["mem_kb"] == 47179688
      and o["walltime_req_s"] == 108000.0 and o["prior_receipt"]["file"] == "watch_refit_20261010T224529Z.json")
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01", "x: qstat -xf Exit_status 75, job_state F"), role="refit", receipts_dir=d)
check("refit: a different exit is not carried (no memory -> the no-finite-memory alarm stays)", why == "" and "mem_kb" not in obs["1.sched01"])
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=tempfile.mkdtemp())
check("refit: no prior receipt -> no carried memory", why == "" and "mem_kb" not in obs["1.sched01"] and "prior_receipt" not in obs["1.sched01"])
# bank memory (Codex RSC 5bab1a9 (a)): the aggregate >90 % alarm survives settlement; absence is never a pass
F95 = "Job Id: 1.sched01\n    job_state = F\n    resources_used.mem = 119537664kb\n"   # 95 % of 120 GiB
BANK.sh = stub(0, F95)
obs, why = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=tempfile.mkdtemp())
check("bank: settled job PBS still knows -> its memory is observed", why == "" and obs["1.sched01"]["mem_kb"] == 119537664
      and obs["1.sched01"]["memory_evidence"]["kind"] == "qstat")
BANK.sh = stub(153, "", "qstat: Unknown Job Id 1.sched01")
obs, why = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=tempfile.mkdtemp())
check("bank: settled + expired + no receipt -> no memory evidence", why == "" and obs["1.sched01"]["memory_evidence"] is None)
BANK.sh = stub(255, "", "ssh: connect to host lengau: timed out")
obs, why = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=tempfile.mkdtemp())
check("bank: a failed memory query is never read as a pass", why == "" and obs["1.sched01"]["memory_evidence"] is None)
bd = tempfile.mkdtemp()


def bank_receipt(stamp, sj, alarms=()):
    json.dump(dict(schema=BANK.WATCH_SCHEMA, fresh=True, production=True, alarms=list(alarms), jobs={"1": sj}),
              open(os.path.join(bd, f"bank_watch_{stamp}.json"), "w"))


bank_receipt("20261010T200604Z", dict(job_id="1.sched01", state="F", exit=0))
BANK.sh = stub(153, "", "qstat: Unknown Job Id 1.sched01")
obs, _ = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=bd)
check("bank: clean receipt that saw F -> documented check, no value", obs["1.sched01"]["mem_kb"] is None
      and obs["1.sched01"]["memory_evidence"]["kind"] == "prior-clean-receipt-check")
bank_receipt("20261011T060000Z", dict(job_id="1.sched01", state="F", exit=0, mem_kb=119537664))
bank_receipt("20261011T070000Z", dict(job_id="1.sched01", state="F", exit=0, mem_kb=1), alarms=["x"])   # alarmed, smaller value: the largest value wins
obs, _ = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=bd)
check("bank: a recorded value is carried and checked", obs["1.sched01"]["mem_kb"] == 119537664
      and obs["1.sched01"]["memory_evidence"]["kind"] == "prior-receipt-value")
obs, _ = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01", "x: qstat -xf Exit_status 271, job_state F"), receipts_dir=bd)
check("bank: another exit is never carried", obs["1.sched01"]["memory_evidence"] is None)

# reconcile: settled 95 % alarms; settled without evidence alarms
live = tempfile.mkdtemp(); os.makedirs(os.path.join(live, "root", "plans")); os.makedirs(os.path.join(live, "root", "status"))
json.dump(dict(job=1, slots=[dict(slot=0, reps=[5])]), open(os.path.join(live, "root", "plans", "job_1.json"), "w"))
json.dump(dict(job="1.sched01", slot=0, reps=[5], new=[5], resumed=[], left=[], exit=0, wall_s=1.0, cpu_s=1.0, maxrss=1.0),
          open(os.path.join(live, "root", "status", "job1.sched01.slot0.json"), "w"))
BANK.LIVE_DIR = live
man = dict(pbs=dict(mem_gb=120, mem_stop_gib=0))
ver = dict(reps={"5": dict(record=dict(ok=True), timing=dict(ok=True, job="1.sched01", slot=0))})
led = dict(entries={"a": dict(kind="bank", rep=1, job_id="1.sched01", token="t", state="settled", runner_exit=0, settle_note=NOTE)})
for mem, ev, want, name in ((119537664, dict(kind="qstat"), True, "settled at 95 % of the request -> memory alarm"),
                            (29388268, dict(kind="qstat"), False, "settled at 24 % -> no memory alarm"),
                            (None, None, True, "settled with no memory evidence -> alarm")):
    o = dict(state="F", exit=0, source="ledger-settlement", settle_note_sha256="x", mem_kb=mem, memory_evidence=ev)
    al, _, _, _ = BANK.reconcile(man, ver, {"1.sched01": o}, led)
    check(f"bank reconcile: {name}", any("memory" in x for x in al) == want)
# Codex RSC c38779c: a newer same-job breach (95 % + its memory alarm) is never displaced by an older clean receipt
MEM_ALARM = "bank job 1: scheduler memory 114.0 GiB above 90 % of the request"
for older, oname in ((dict(job_id="1.sched01", state="F", exit=0, mem_kb=29388268), "older clean 24 %"),
                     (dict(job_id="1.sched01", state="F", exit=0), "older clean legacy (no value)")):
    bd2 = tempfile.mkdtemp()
    json.dump(dict(schema=BANK.WATCH_SCHEMA, fresh=True, production=True, alarms=[], jobs={"1": older}),
              open(os.path.join(bd2, "bank_watch_20261010T200000Z.json"), "w"))
    json.dump(dict(schema=BANK.WATCH_SCHEMA, fresh=True, production=True, alarms=[MEM_ALARM],
                   jobs={"1": dict(job_id="1.sched01", state="F", exit=0, mem_kb=119537664)}),
              open(os.path.join(bd2, "bank_watch_20261011T030000Z.json"), "w"))
    BANK.sh = stub(153, "", "qstat: Unknown Job Id 1.sched01")                   # PBS history expired
    obs, why = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=bd2)
    o = obs["1.sched01"]
    check(f"bank: newer 95 % + alarm vs {oname}, expired -> the 95 % value and the breach are kept",
          why == "" and o["mem_kb"] == 119537664 and o["memory_breach"]["file"] == "bank_watch_20261011T030000Z.json")
    al, _, _, _ = BANK.reconcile(man, ver, obs, led)
    check(f"bank reconcile: newer breach vs {oname} -> memory alarms fire",
          any("above 90 %" in x for x in al) and any("recorded a scheduler-memory alarm" in x for x in al))
    json.dump(dict(schema=BANK.WATCH_SCHEMA, fresh=True, production=True, alarms=[MEM_ALARM],
                   jobs={"1": dict(job_id="1.sched01", state="F", exit=0)}),
              open(os.path.join(bd2, "bank_watch_20261011T030000Z.json"), "w"))   # breach recorded only as an alarm
    obs, _ = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=bd2)
    al, _, _, _ = BANK.reconcile(man, ver, obs, led)
    check(f"bank reconcile: alarm-only breach vs {oname} -> the breach alarm fires", any("recorded a scheduler-memory alarm" in x for x in al))
bd3 = tempfile.mkdtemp()
json.dump(dict(schema=BANK.WATCH_SCHEMA, fresh=True, production=True, alarms=["bank job 2: something unrelated"],
               jobs={"1": dict(job_id="1.sched01", state="F", exit=0)}), open(os.path.join(bd3, "bank_watch_20261011T030000Z.json"), "w"))
obs, _ = BANK.pbs_observe(["1.sched01"], None, settled("1.sched01"), receipts_dir=bd3)
check("bank: an unrelated alarm is neither a breach nor a clean check", obs["1.sched01"]["memory_breach"] is None
      and obs["1.sched01"]["memory_evidence"] is None)
print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)

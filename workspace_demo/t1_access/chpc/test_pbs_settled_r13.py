"""REVISION 11 + 12 + 13 (R052 11-12 Oct): pbs_observe of the bank status and the v14 refit status candidate (REVISION 12 and 13
cases at the end; REVISION 13 = Codex RSC 7523370 (a): breach preservation, durable direct carry, no recursive carry).
Settled ledger entries are observed from their settlement (never asked of qstat); unsettled ones stay fail-closed.

    python3 chpc/test_pbs_settled_r13.py          (from workspace_demo/t1_access)"""
import importlib.util, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


BANK = load("bank_status_t", os.path.join(HERE, "row22_bank_status.py"))
R19 = load("r19_status_t", os.path.join(HERE, "candidate_v14", "row19_screen_status.py"))
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
    settled_q = ["qstat -xf 1.sched01"]                                 # bank and (REVISION 12) refit: one tolerant query of the settled ids
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
# REVISION 12 (refit): a settled job PBS still reports contributes its live scheduler facts; expiry and failures fail closed
FJ = lambda j, mem: f"Job Id: {j}\n    job_state = F\n    resources_used.mem = {mem}kb\n    Resource_List.walltime = 48:00:00\n"
R19.sh = stub(0, FJ("1.sched01", 48345148))
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=tempfile.mkdtemp())
o = obs["1.sched01"]
check("r12: settled before any clean receipt, PBS still knows it -> live memory and walltime request",
      why == "" and o["mem_kb"] == 48345148 and o["walltime_req_s"] == 172800.0 and o["memory_evidence"] == [dict(kind="qstat")]
      and o["state"] == "F" and o["exit"] == 0 and o["source"] == "ledger-settlement")
R19.sh = stub(0, FJ("1.sched01", 100))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=d)
o = obs["1.sched01"]
check("r12: carried value larger than live -> the larger (carried) is checked, both sources named (r13 kinds)",
      o["mem_kb"] == 47179688 and [e["kind"] for e in o["memory_evidence"]] == ["qstat", "prior-receipt-qstat"]
      and o["walltime_req_s"] == 108000.0)
R19.sh = stub(0, FJ("1.sched01", 119537664))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=d)
check("r12: live value larger than carried -> the live value is checked", obs["1.sched01"]["mem_kb"] == 119537664)
R19.sh = stub(0, "Job Id: 1.sched01\n    job_state = R\n    resources_used.mem = 5kb\n")
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=tempfile.mkdtemp())
check("r12: the scheduler does not report F -> no value (alarm stays)", "mem_kb" not in obs["1.sched01"])
R19.sh = stub(255, "", "ssh: connect to host lengau: timed out")
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=tempfile.mkdtemp())
check("r12: a failed query is never read as a value", why == "" and "mem_kb" not in obs["1.sched01"]
      and obs["1.sched01"]["memory_evidence"] == [])
R19.sh = stub(153, FJ("2.sched01", 7), "qstat: Unknown Job Id 1.sched01")
obs, why = R19.pbs_observe(["1.sched01", "2.sched01"], None, {**settled("1.sched01"), **settled("2.sched01")}, role="refit",
                           receipts_dir=tempfile.mkdtemp())
check("r12: one settled id expired, the other still known -> value only for the known one",
      why == "" and "mem_kb" not in obs["1.sched01"] and obs["2.sched01"]["mem_kb"] == 7)
R19.sh = stub(153, "", "qstat: Unknown Job Id 9.sched01")
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=tempfile.mkdtemp())
check("r12: an Unknown Job Id for an id not asked is not tolerated", "mem_kb" not in obs["1.sched01"])
# REVISION 13 (Codex RSC 7523370 (a)): publication -> PBS expiry -> reconciliation; breaches are never displaced, carry is
# durable for a job first observed after settlement, and only DIRECT observations are consumed (no recursive carry).
R19.ec2_reconcile = lambda *a, **k: {}
REQ = 120 * 1024 ** 2                                                    # mem_gb 120 in kB
P95, P24 = int(0.95 * REQ), int(0.24 * REQ)
MEMA = "refit job 1: scheduler memory above 90 % of the request"
rlive = tempfile.mkdtemp(); os.makedirs(os.path.join(rlive, "root", "plans")); os.makedirs(os.path.join(rlive, "root", "status"))
json.dump(dict(job=1, walltime_s=172800.0, slots=[dict(slot=0, rep=5, indices=[0])]), open(os.path.join(rlive, "root", "plans", "job_1.json"), "w"))
json.dump(dict(job="1.sched01", slot=0, rep=5, indices=[0], ident="id5", new=[0], resumed=[], left=[], exit=0, wall_s=1.0, maxrss=1.0),
          open(os.path.join(rlive, "root", "status", "job1.sched01.slot0.json"), "w"))
rman = dict(pbs=dict(mem_gb=120, mem_stop_gib=0), datasets=dict(identities={"5": "id5"}))
rver = dict(units={"5/0": dict(record=dict(ok=True), timing=dict(ok=True, job="1.sched01", slot=0))},
            bindings={"5": dict(ok=True, declared_ident_equal=True)})
rled = dict(entries={"a": dict(kind="shard", rep=1, job_id="1.sched01", token="t", state="settled", runner_exit=0, settle_note=NOTE)})


def rreceipt(dd, stamp, sj, alarms=()):
    json.dump(dict(schema=R19.WATCH_SCHEMA, role="refit", fresh=True, production=True, alarms=list(alarms), jobs={"1": sj}),
              open(os.path.join(dd, f"watch_refit_{stamp}.json"), "w"))


def mem_alarms(al):
    return [x for x in al if "memory" in x]


def publish(dd, stamp, obs):
    """What a REVISION 13 receipt records for job 1: reconcile's own summary and alarms."""
    al, summ, _, _ = R19.reconcile(rman, "refit", rver, obs, rled, rlive)
    rreceipt(dd, stamp, summ["1"], al)
    return al, summ["1"]


EXPIRED = stub(153, "", "qstat: Unknown Job Id 1.sched01")
CLEAN24 = dict(job_id="1.sched01", state="F", exit=0, mem_kb=P24, requested_walltime_s=172800.0)       # old direct-qstat receipt
# Codex's sequence: older clean direct 24 %; R13 sees the settled id live at 95 %, alarms and publishes; PBS expires
dd = tempfile.mkdtemp(); rreceipt(dd, "20261010T100000Z", CLEAN24)
R19.sh = stub(0, FJ("1.sched01", P95))
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
o = obs["1.sched01"]
check("r13: live 95 % beside an older clean 24 % -> 95 % checked, recorded as qstat_mem_kb", why == "" and o["mem_kb"] == P95
      and o["qstat_mem_kb"] == P95 and o["memory_evidence"][0] == dict(kind="qstat") and o["memory_breach"] is None)
al, summ = publish(dd, "20261012T030000Z", obs)
check("r13: publication carries the 95 % alarm and the direct value", MEMA in al and summ["qstat_mem_kb"] == P95
      and summ["observation"] == "ledger-settlement")
R19.sh = EXPIRED
obs, why = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
o = obs["1.sched01"]
check("r13: after expiry the alarmed settlement receipt's direct 95 % beats the older clean 24 %", why == "" and o["mem_kb"] == P95
      and o["prior_receipt"]["file"] == "watch_refit_20261012T030000Z.json" and o["memory_evidence"][0]["kind"] == "prior-receipt-settled-qstat"
      and o["memory_breach"]["file"] == "watch_refit_20261012T030000Z.json")
al, summ = publish(dd, "20261012T040000Z", obs)
check("r13: reconciliation after expiry still alarms (>90 % and the recorded breach)", MEMA in al
      and any("recorded a scheduler-memory alarm" in x for x in al))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
check("r13: the breach persists through further receipts (the value check re-fires; 95 % still checked)",
      obs["1.sched01"]["memory_breach"] is not None and obs["1.sched01"]["mem_kb"] == P95)
# alarm-only breach (no recorded value) beside an older clean 24 %: the value is 24 %, but the breach alarm fires
dd = tempfile.mkdtemp(); rreceipt(dd, "20261010T100000Z", CLEAN24)
rreceipt(dd, "20261011T100000Z", dict(job_id="1.sched01", state="F", exit=0, observation="ledger-settlement"), alarms=[MEMA])
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
al, _, _, _ = R19.reconcile(rman, "refit", rver, obs, rled, rlive)
check("r13: alarm-only breach vs older clean 24 % -> 24 % checked, the breach alarm fires", obs["1.sched01"]["mem_kb"] == P24
      and any("recorded a scheduler-memory alarm" in x for x in al) and MEMA not in al)
# durable carry for a job first observed by R13 (no older eligible receipt): clean live -> receipt -> expiry -> value kept
dd = tempfile.mkdtemp()
R19.sh = stub(0, FJ("1.sched01", 48345148))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
al, summ = publish(dd, "20261012T030000Z", obs)
check("r13: first observation after settlement, clean -> no memory alarm", mem_alarms(al) == [] and summ["qstat_mem_kb"] == 48345148)
R19.sh = EXPIRED
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
al, summ = publish(dd, "20261012T040000Z", obs)
check("r13: after expiry the value carries from the settlement receipt's qstat_mem_kb (durable), no memory alarm",
      obs["1.sched01"]["mem_kb"] == 48345148 and obs["1.sched01"]["walltime_req_s"] == 172800.0 and mem_alarms(al) == []
      and summ["qstat_mem_kb"] is None and summ["mem_kb"] == 48345148)
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
check("r13: a later receipt that only CARRIED the value is not a source; the direct one stays the source",
      obs["1.sched01"]["prior_receipt"]["file"] == "watch_refit_20261012T030000Z.json")
os.remove(os.path.join(dd, "watch_refit_20261012T030000Z.json"))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
al, _, _, _ = R19.reconcile(rman, "refit", rver, obs, rled, rlive)
check("r13: no recursive carry - with the direct receipt gone, a carried-only receipt gives no value (alarm)",
      "mem_kb" not in obs["1.sched01"] and any("no finite observed scheduler memory" in x for x in al))
# exits, foreign and unrelated alarms
dd = tempfile.mkdtemp()
rreceipt(dd, "20261011T100000Z", dict(job_id="1.sched01", state="F", exit=75, mem_kb=P95), alarms=[MEMA])
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
check("r13: another exit's value and breach are never consumed", "mem_kb" not in obs["1.sched01"] and obs["1.sched01"]["memory_breach"] is None)
dd = tempfile.mkdtemp()
rreceipt(dd, "20261011T100000Z", dict(CLEAN24), alarms=["refit job 2: scheduler memory above 90 % of the request",
                                                          "refit job 1 (1.sched01): runner exit 4"])
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
check("r13: another job's breach and unrelated alarms are not carried; the direct value is still used",
      obs["1.sched01"]["memory_breach"] is None and obs["1.sched01"]["mem_kb"] == P24)
dd = tempfile.mkdtemp()
json.dump(dict(schema=R19.WATCH_SCHEMA, role="refit", fresh=False, production=True, alarms=[MEMA],
               jobs={"1": dict(CLEAN24, mem_kb=P95)}), open(os.path.join(dd, "watch_refit_20261011T100000Z.json"), "w"))
obs, _ = R19.pbs_observe(["1.sched01"], None, settled("1.sched01"), role="refit", receipts_dir=dd)
check("r13: a non-fresh receipt is never a source", "mem_kb" not in obs["1.sched01"] and obs["1.sched01"]["memory_breach"] is None)
print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)

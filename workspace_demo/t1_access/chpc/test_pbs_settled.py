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
    kw = dict(role="refit", receipts_dir=tempfile.mkdtemp()) if M is R19 else {}
    calls.clear(); M.sh = stub(153, "", "qstat: Unknown Job Id 1.sched01")
    obs, why = M.pbs_observe(["1.sched01"], None, settled("1.sched01"), **kw)
    check(f"{label}: settled + expired -> no alarm, no qstat call", why == "" and calls == [] and obs["1.sched01"]["state"] == "F"
          and obs["1.sched01"]["exit"] == 0 and obs["1.sched01"]["source"] == "ledger-settlement")
    calls.clear(); M.sh = stub(0, QSTAT_R)
    obs, why = M.pbs_observe(["1.sched01", "2.sched01"], None, settled("1.sched01"), **kw)
    check(f"{label}: qstat asked only of the unsettled id", why == "" and calls == ["qstat -xf 2.sched01"] and obs["2.sched01"]["state"] == "R"
          and obs["1.sched01"]["state"] == "F")
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
print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)

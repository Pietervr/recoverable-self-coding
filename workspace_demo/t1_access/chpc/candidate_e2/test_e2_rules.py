"""EC2 provider epoch 2 CANDIDATE (NOT adopted): tests of the shared rules module (chpc/candidate_e2/row19_ec2_e2rules.py)
and of the snapshot plan lock (row19_partition REVISION 6) - Codex review reviews/2026-10-17_e2_p80r_codex_review.md A1, A2,
A3, rulings 1 and 7. Pure python, a temporary sandbox root; no fits, no Lengau, no AWS.

    python3 chpc/candidate_e2/test_e2_rules.py                (from workspace_demo/t1_access)"""
import copy, fcntl, hashlib, importlib.util, json, os, shutil, sys, tempfile

CAND = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(CAND); T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):
    sys.path.insert(0, p)
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


R = load_mod("row19_ec2_e2rules", os.path.join(CAND, "row19_ec2_e2rules.py"))
RP = load_mod("row19_partition", os.path.join(CAND, "row19_partition.py"))
SRC = open(R.__file__).read()

# ---- A2: one classification ---------------------------------------------------------------------------------------------
check("A2: the fatal-signal class is exactly 129..159 and every member counts toward the crash rule",
      R.FATAL_SIGNAL_EXITS == frozenset(range(129, 160)) and all(R.kind(x) == "fatal_signal" and R.counts_toward_crash_rule(x) for x in range(129, 160)))
check("A2: 128, 160, 0, 1, 4, 75, the censor marker, True and 139.0 are not fatal signals",
      not any(R.counts_toward_crash_rule(x) for x in (128, 160, 0, 1, 4, 75, R.CENSORED, True, 139.0)))
check("kinds: 75 resume, the marker censored, exit 4 / exit 1 / an unknown string none",
      R.kind(75) == "resume" and R.kind(R.CENSORED) == "censored" and R.kind(4) is None and R.kind(1) is None and R.kind("killed") is None)
check("no OOM claim for exit 137 in the shared module (SIGKILL only)", "OOM killer" not in SRC.replace("never described as the OOM killer", ""))
check("the module is pure: no I/O, no scientific import", all(t not in SRC for t in ("open(", "import jax", "import numpy", "import os")))

# ---- A1: the orderly LEFT status -----------------------------------------------------------------------------------------
GOOD = dict(job="a1", slot=3, rep=24, ident="id24", indices=[5], left=[5], new=[], resumed=[], exit=75,
            reason="deadline: 12 s left, 900 s needed for the next resample", wall_s=10.0, cpu_s=9.0, started=1.0, ended=11.0, maxrss=2_000_000_000)
STOP = 4.5 * 2 ** 30
ok = lambda st: R.left_status_problem(st, "a1", 3, 24, 5, "id24", STOP)
check("A1: the worker's own deadline status passes; the STOP reason passes", ok(GOOD) == "" and ok(dict(GOOD, reason=R.STOP_REASON)) == "")
for name, edit in (("exit 4", dict(exit=4)), ("a memory reason", dict(reason="memory: maxrss 5.10 GiB above the 4.50 GiB stop, before index 5")),
                   ("an exception reason", dict(reason="exception: MemoryError: ")), ("an empty reason", dict(reason="")),
                   ("another attempt", dict(job="a2")), ("another slot", dict(slot=4)), ("another rep", dict(rep=25)),
                   ("a wrong identity", dict(ident="id25")), ("left []", dict(left=[])), ("new [5]", dict(new=[5])),
                   ("resumed [5]", dict(resumed=[5])), ("two indices", dict(indices=[5, 6], left=[5, 6])), ("maxrss 1e12", dict(maxrss=10 ** 12)),
                   ("maxrss 0", dict(maxrss=0)), ("a NaN wall", dict(wall_s=float("nan"))), ("no cpu", dict(cpu_s=None)),
                   ("exit True", dict(exit=True)), ("slot as string", dict(slot="3"))):
    check(f"A1: a status with {name} is not an orderly LEFT status", ok(dict(GOOD, **edit)) != "")
check("A1: a status that is not an object fails", ok(None) != "" and ok([1]) != "")

# ---- A3: concentration -------------------------------------------------------------------------------------------------
slots = lambda d: [dict(rep=r) for r, n in d.items() for _ in range(n)]
check("A3: the declared E2Q1 shape (52 work + 9 duplicates on rep 24, 11 duplicates on reps 25/28, 4 sentinels) is 61 on one replicate",
      max(R.rep_concentration(slots({24: 61, 25: 8, 28: 3, 3: 1, 7: 1, 9: 1, 11: 1})).values()) == R.QUALIFIED_REP_SLOTS == 61)
check("A3: 61 on one replicate is inside the shape, 62 outside", R.concentration_problem(slots({24: 61, 25: 15})) == ""
      and "above the qualified 61" in R.concentration_problem(slots({24: 62, 25: 14})))
check("A3: the unconstrained production shapes Codex found (69 on rep 24; 70 on reps 69/70) are outside",
      R.concentration_problem(slots({24: 69, 25: 3, 1: 4})) != "" and R.concentration_problem(slots({69: 70, 70: 2, 5: 4})) != "")

# ---- ruling 7: R4' at most 3 non-completions of ALL roles --------------------------------------------------------------
plan = [dict(slot=k, rep=24, role="work" if k < 52 else "qual_lengau" if k < 72 else "sentinel") for k in range(76)]
oc = lambda d: {f"w_slot{k}": d.get(k, 0) for k in range(76)}
check("R4': three non-completions (a work crash, a duplicate censored, a sentinel RESUME) pass",
      R.qualification_unproduced_problem(plan, oc({0: 139, 60: R.CENSORED, 74: 75})) == "")
check("R4': a fourth non-completion of ANY role fails (here a sentinel)", "> 3" in R.qualification_unproduced_problem(plan, oc({0: 139, 1: 139, 60: 139, 75: 134})))
check("R4': a non-completion of no qualifying kind fails even alone", "no qualifying kind" in R.qualification_unproduced_problem(plan, oc({5: 4})))
check("R4': the qualification bound (3 of 76) is stricter than production's MAX_UNPRODUCED_WORK (7)", R.QUAL_MAX_UNPRODUCED == 3)

# ---- ruling 1: the canonical snapshot takes the plan lock ---------------------------------------------------------------
tmp = tempfile.mkdtemp()
root, camp = os.path.join(tmp, "root"), os.path.join(tmp, "camp")
os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
json.dump({"entries": {}}, open(os.path.join(camp, "budget.json"), "w"))
man = copy.deepcopy(json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))); man["storage"] = {"root": root, "campaign": camp}
mp = os.path.join(tmp, "manifest.json"); json.dump(man, open(mp, "w"))
lk = open(os.path.join(root, "plans", ".submit.lock"), "a+"); fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
out1 = os.path.join(tmp, "snap1.json")
rc = RP.main(["snapshot", "--manifest", mp, "--out", out1])
check("ruling 1: a canonical snapshot while the plan lock is held refuses (exit 3) and writes nothing", rc == 3 and not os.path.exists(out1))
fcntl.flock(lk.fileno(), fcntl.LOCK_UN); lk.close()
rc = RP.main(["snapshot", "--manifest", mp, "--out", out1])
check("ruling 1: with the lock free the canonical snapshot is taken under it and says so", rc == 0 and json.load(open(out1))["source"]["plan_lock"] == "held")
out2 = os.path.join(tmp, "snap2.json")
lk = open(os.path.join(root, "plans", ".submit.lock"), "a+"); fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
rc = RP.main(["snapshot", "--manifest", mp, "--root", root, "--campaign", camp, "--out", out2])
fcntl.flock(lk.fileno(), fcntl.LOCK_UN); lk.close()
check("ruling 1: a snapshot of a pulled copy takes no live lock and records it as candidate input",
      rc == 0 and json.load(open(out2))["source"]["plan_lock"] == "not taken (copy)" and json.load(open(out2))["source"]["copy"] is True)
shutil.rmtree(tmp)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)

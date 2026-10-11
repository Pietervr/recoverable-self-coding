"""Local tests of bench_launch.py's admission/recovery logic against a stub `aws` (no AWS, no instance, no cost).
    python3 tests/test_bench_launch.py"""
import json, os, shutil, subprocess, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import bench_launch as L

tmp = tempfile.mkdtemp(); bindir = os.path.join(tmp, "bin"); os.makedirs(bindir)
os.symlink(os.path.join(HERE, "stub_aws.py"), os.path.join(bindir, "aws")); os.chmod(os.path.join(HERE, "stub_aws.py"), 0o755)
os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]
L.BACKOFF_S = (0, 0, 0, 0, 0)
fake_tgz = os.path.join(tmp, "t.tgz"); open(fake_tgz, "wb").write(b"x")
L.PINS["t1_toolchain_lengau.tgz"] = L.sha256(fake_tgz)          # the real tarball is not needed for these tests
L.start_reaper = lambda run, att: True                          # supervision is exercised separately
class A: pass
def args(run, **kw):
    a = A(); a.run = run; a.tarball = fake_tgz; a.dry_run = False; a.recover = False; a.__dict__.update(kw); return a
def fresh(run, mode):
    os.environ["STUB_MODE"] = mode; os.environ["STUB_LOG"] = os.path.join(tmp, f"{run}.log")
    shutil.rmtree(os.path.join(PKG, "runs", run), ignore_errors=True)
def runs_calls_safe(run):
    p = os.path.join(tmp, f"{run}.log")
    return [l for l in open(p) if "run-instances" in l] if os.path.exists(p) else []
def runs_calls(run):
    return [json.loads(l) for l in open(os.path.join(tmp, f"{run}.log")) if "run-instances" in l]
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)

# 1 ambiguous then success: the SAME token is re-issued, one instance, state launched
fresh("t_amb", "ambiguous_then_ok")
with L.run_lock("t_amb"):
    rc = L.admit(args("t_amb"))
c = runs_calls("t_amb"); toks = {x[x.index("--client-token") + 1] for x in c}
att = L.load("t_amb")["attempts"][-1]
check("ambiguous then launched on the same token", rc == 0 and len(c) == 2 and len(toks) == 1 and att["state"] == "launched")

# 2 definitive rejection: state rejected, charged 0, next admission allowed (attempt 2)
fresh("t_rej", "reject")
with L.run_lock("t_rej"):
    rc = L.admit(args("t_rej"))
led = L.load("t_rej")
check("definitive rejection -> rejected, charged 0", rc == 1 and led["attempts"][-1]["state"] == "rejected" and L.charged(led["attempts"][-1]) == 0)

# 3 always ambiguous: stays ambiguous and funded; a new admission is refused; --recover re-issues the same token
fresh("t_amb2", "always_ambiguous")
with L.run_lock("t_amb2"):
    rc = L.admit(args("t_amb2"))
att = L.load("t_amb2")["attempts"][-1]
check("persistent ambiguity stays funded", rc == 3 and att["state"] == "ambiguous" and L.charged(att) > 26.9)
try:
    with L.run_lock("t_amb2"):
        L.admit(args("t_amb2")); refused = False
except SystemExit as e:
    refused = "REFUSED" in str(e)
check("new attempt refused while ambiguous", refused)
os.environ["STUB_MODE"] = "ok"
with L.run_lock("t_amb2"):
    rc = L.recover(args("t_amb2", recover=True))
c = runs_calls("t_amb2"); toks = {x[x.index("--client-token") + 1] for x in c}
check("--recover resolves with the same token", rc == 0 and len(toks) == 1 and L.load("t_amb2")["attempts"][-1]["state"] == "launched")

# 4 crash after intent (state intent, no API answer): new admission refused, --recover issues that token
fresh("t_crash", "ok")
with L.run_lock("t_crash"):
    real = L.finish; L.finish = lambda run, led, att, fresh: 99
    L.admit(args("t_crash")); L.finish = real
att = L.load("t_crash")["attempts"][-1]
check("crash leaves intent recorded", att["state"] == "intent")
with L.run_lock("t_crash"):
    rc = L.recover(args("t_crash", recover=True))
c = runs_calls("t_crash")
check("intent recovered on its own token", rc == 0 and len(c) == 1 and c[0][c[0].index("--client-token") + 1] == att["client_token"])

# 5 concurrency: a second launcher cannot take the lock while the first holds it
fresh("t_conc", "ok")
got = {}
with L.run_lock("t_conc"):
    def second():
        try:
            with L.run_lock("t_conc"):
                got["second"] = "acquired"
        except BlockingIOError:
            got["second"] = "refused"
    th = threading.Thread(target=second); th.start(); th.join()
check("concurrent launcher refused by the run lock", got.get("second") == "refused")


# 6 ambiguous first dispatch, then a definitive rejection on replay: NOT released (stays ambiguous, funded)
fresh("t_ar", "ambiguous_then_reject")
with L.run_lock("t_ar"):
    rc = L.admit(args("t_ar"))
att = L.load("t_ar")["attempts"][-1]
check("rejection after an unanswered dispatch stays funded", att["state"] == "ambiguous" and "rejected_on_replay" in att and L.charged(att) > 26.9)
try:
    with L.run_lock("t_ar"):
        L.admit(args("t_ar")); refused = False
except SystemExit as e:
    refused = "REFUSED" in str(e)
check("no new attempt after a replay rejection", refused)

# 7 crash-left intent, then a rejection on --recover: NOT released
fresh("t_cr", "reject")
with L.run_lock("t_cr"):
    real = L.finish; L.finish = lambda run, led, att, fresh: 99
    L.admit(args("t_cr")); L.finish = real
with L.run_lock("t_cr"):
    L.recover(args("t_cr", recover=True))
att = L.load("t_cr")["attempts"][-1]
check("rejection on a recovered intent stays funded", att["state"] == "ambiguous" and L.charged(att) > 26.9)

# 8 changed user-data bytes: replay refused, attempt stays funded, no RunInstances call
fresh("t_ud", "ok")
with L.run_lock("t_ud"):
    real = L.finish; L.finish = lambda run, led, att, fresh: 99
    L.admit(args("t_ud")); L.finish = real
att = L.load("t_ud")["attempts"][-1]
udp = json.load(open(att["request"]))["args"]; udp = udp[udp.index("--user-data") + 1].replace("file://", "")
open(udp, "a").write("\n# tampered\n")
with L.run_lock("t_ud"):
    rc = L.recover(args("t_ud", recover=True))
att = L.load("t_ud")["attempts"][-1]
check("changed user-data refuses the replay, funded", rc == 3 and att["state"] in ("intent", "ambiguous") and not runs_calls_safe("t_ud"))

# 9 supervisor start raises: the launcher terminates the instance itself and keeps it launched/funded
fresh("t_sup", "ok")
def boom(run, att): raise OSError("caffeinate missing")
L.start_reaper = boom
with L.run_lock("t_sup"):
    rc = L.admit(args("t_sup"))
term = os.path.exists(os.path.join(tmp, "t_sup.log.terminated"))
att = L.load("t_sup")["attempts"][-1]
check("supervisor failure -> emergency terminate, attempt stays launched", rc == 2 and term and att["state"] == "launched")

# 10 R2-3 pre-issue guard: withheld before the first call -> withdrawn (rejected, no call); after an unanswered call -> ambiguous
L.start_reaper = lambda run, att: True
fresh("t_g1", "ok")
with L.run_lock("t_g1"):
    real = L.finish; L.finish = lambda run, led, att, fresh: 99
    L.admit(args("t_g1")); L.finish = real
led = L.load("t_g1"); att = led["attempts"][-1]
rc = L.finish("t_g1", led, att, True, guard=lambda: "STOP in force (test)")
att = L.load("t_g1")["attempts"][-1]
check("R2-3 a guard refusal before any call withdraws the fresh attempt: rejected, zero RunInstances", rc == 1 and att["state"] == "rejected"
      and "withdrawn" in att["rejection"] and not runs_calls_safe("t_g1"))
fresh("t_g2", "always_ambiguous")
with L.run_lock("t_g2"):
    real = L.finish; L.finish = lambda run, led, att, fresh: 99
    L.admit(args("t_g2")); L.finish = real
led = L.load("t_g2"); att = led["attempts"][-1]; n = {"k": 0}
def g():
    n["k"] += 1; return "" if n["k"] == 1 else "STOP in force (test)"
rc = L.finish("t_g2", led, att, True, guard=g)
att = L.load("t_g2")["attempts"][-1]
check("R2-3 a guard refusal before a RE-issue stays ambiguous and funded after exactly one call", rc == 3 and att["state"] == "ambiguous"
      and len(runs_calls("t_g2")) == 1 and L.charged(att) > 26.9)
# 11 freeze: once EC2 qualification/production exists, benchmark admissions AND recoveries refuse
check("freeze: none today (no qualification permitted, no qual-/prod- ledger)", L.freeze_problem() == "")
fz = tempfile.mkdtemp(); realHERE = L.HERE; L.HERE = fz
json.dump({"qualification": {"permitted": True}}, open(os.path.join(fz, "ec2_release_state.json"), "w"))
check("freeze: a release state permitting qualification freezes benchmarks", "frozen" in L.freeze_problem())
json.dump({"qualification": {"permitted": False}}, open(os.path.join(fz, "ec2_release_state.json"), "w"))
os.makedirs(os.path.join(fz, "runs", "qual-Q1")); json.dump({"attempts": [{"attempt": 1}]}, open(os.path.join(fz, "runs", "qual-Q1", "attempts.json"), "w"))
check("freeze: any qualification/production attempt freezes benchmarks", "frozen" in L.freeze_problem())
os.remove(os.path.join(fz, "ec2_release_state.json"))
check("freeze: an unreadable release state freezes (fail closed)", "frozen" in L.freeze_problem())
L.HERE = realHERE; shutil.rmtree(fz)
env = dict(os.environ); sp = subprocess.run([sys.executable, os.path.join(PKG, "bench_launch.py"), "--run", "t_fz", "--recover"],
                                            capture_output=True, text=True, env=env, cwd=PKG)
check("freeze is checked in main before admission and recovery (today: passes to the recovery path)", "frozen" not in sp.stdout + sp.stderr)

for r in ("t_amb", "t_rej", "t_amb2", "t_crash", "t_conc", "t_ar", "t_cr", "t_ud", "t_sup", "t_g1", "t_g2", "t_fz"):
    shutil.rmtree(os.path.join(PKG, "runs", r), ignore_errors=True)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

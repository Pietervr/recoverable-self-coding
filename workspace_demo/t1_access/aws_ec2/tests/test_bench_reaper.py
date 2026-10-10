"""Local test of bench_reaper.py against the stub `aws`: an empty Describe and a transient error do not reconcile; an
attributable terminated observation does, with compute and ancillary hours. No AWS, no cost.
    python3 tests/test_bench_reaper.py"""
import json, os, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import bench_launch as L
tmp = tempfile.mkdtemp(); bindir = os.path.join(tmp, "bin"); os.makedirs(bindir)
os.symlink(os.path.join(HERE, "stub_aws.py"), os.path.join(bindir, "aws"))
env = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"], STUB_MODE="reaper", STUB_LOG=os.path.join(tmp, "r.log"))
run = "t_reap"; shutil.rmtree(os.path.join(PKG, "runs", run), ignore_errors=True)
launch = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() - 3600))
L.save(run, {"run": run, "ceiling_usd": 28.0, "attempts": [dict(attempt=1, state="launched", instance="i-stub0001", launch_time=launch,
                                                              lifetime_s=77400, client_token="tok")]})
p = subprocess.run([sys.executable, os.path.join(PKG, "bench_reaper.py"), "--run", run, "--attempt", "1", "--poll-s", "1"],
                   env=env, capture_output=True, text=True, timeout=120)
att = L.load(run)["attempts"][0]
log = p.stdout
ok = ("no attributable instance" in log and "describe error" in log and att["state"] == "reconciled"
      and att["terminal"]["observed_state"] == "terminated" and 3500 < att["terminal"]["compute_s"] < 3700
      and att["terminal"]["ancillary_s"] >= att["terminal"]["compute_s"] and len(att["terminal"]["errors"]) == 1
      and os.path.exists(os.path.join(PKG, "runs", run, "reaper_attempt1.heartbeat")))
print(log.strip().splitlines()[-1]); print("PASS reaper: empty and error polls held, terminated reconciled" if ok else "FAIL\n" + log + p.stderr)
shutil.rmtree(os.path.join(PKG, "runs", run), ignore_errors=True); sys.exit(0 if ok else 1)

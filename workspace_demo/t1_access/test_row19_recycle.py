"""Row 19 process recycling (5 Oct 2026): the unchanged runner, called repeatedly under ONE job id and ONE reservation with
--segment 1 (as chpc/row19_slice_rep.pbs.template now does), adds exactly one record per call, never HOLDs, resumes its
checkpoint and cached original every call, and its records equal a single uninterrupted chain's bit for bit. The template's
bash loop is exercised with a fake runner: it recycles while a call returns 75 with a new record, and stops on a call with no
new record, on any other exit, and when too little walltime is left."""
import os
os.environ.setdefault("NPROC", "1")
import json, subprocess, tempfile, shutil, io, contextlib
from test_row19_slice import _manifest, _run, _dirs, _Patched, R19, T1
from row19_ledger import CampaignLedger

SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")


def _records(root):
    ck = os.path.join(root, "ckpt"); f = [x for x in os.listdir(ck) if x.endswith(".jsonl")][0]
    return {r["rep"]: r for r in (json.loads(l) for l in open(os.path.join(ck, f)) if l.strip())}


def test_repeated_single_resample_calls_under_one_job_match_one_chain():
    with _Patched():
        d1, c1 = _dirs()
        man1 = _manifest(d1, c1, n_boot=6)
        assert _run(d1, man1, "--job-id", "ref") in (R19.DONE, R19.RESUME)              # the uninterrupted reference chain
        ref = _records(d1)
        d2, c2 = _dirs()
        man2 = _manifest(d2, c2, n_boot=6)
        L = CampaignLedger(c2, 1500.0); tok, _ = L.reserve("main", 0, 1, 3600.0, d2)
        mp = os.path.join(d2, "manifest.json"); json.dump(man2, open(mp, "w"))
        argv = ["--manifest", mp, "--root", d2, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                "--reservation-token", tok, "--job-id", "J1", "--segment", "1"]
        codes = []
        for k in range(8):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                codes.append(R19.main(argv))
            n = len(_records(d2))
            if codes[-1] == R19.DONE:
                break
            assert codes[-1] == R19.RESUME and n == k + 1, (k, codes, n, buf.getvalue()[-400:])
            assert "(cached)" in buf.getvalue() or k == 0                               # the original fit is reused after call 1
        assert codes[-1] == R19.DONE and R19.HELD not in codes
        got = _records(d2)
        assert sorted(got) == sorted(ref) == list(range(6))
        for i in ref:
            assert all(json.dumps(got[i][k], sort_keys=True) == json.dumps(ref[i][k], sort_keys=True) for k in SCI), i


def _loop_harness(tmp, script_lines, safe_s=86400, job_s=518400):
    """Run the template's loop with the runner replaced by a fake that replays one scripted (exit, new) per call."""
    tpl = open(os.path.join(T1, "chpc", "row19_slice_rep.pbs.template")).read()
    body = tpl[tpl.index("JOB_START="):]
    body = body.replace("__REP__", "0").replace("__TOKEN__", "tok")
    body = body.replace("518400", str(job_s)).replace("RECYCLE_SAFE_S=86400", f"RECYCLE_SAFE_S={safe_s}")
    script = os.path.join(tmp, "script.txt"); open(script, "w").write("\n".join(script_lines) + "\n")
    fake = os.path.join(tmp, "t1py")
    open(fake, "w").write("#!/bin/bash\nn=$(cat $FAKE_STATE 2>/dev/null || echo 0); n=$((n+1)); echo $n > $FAKE_STATE\n"
                          "line=$(sed -n \"${n}p\" $FAKE_SCRIPT); rc=${line%% *}; new=${line##* }\n"
                          "echo \"rep 0: PARTIAL (resume): done $n/200, new $new, resumed 0, wall 1.0 min\"\nexit $rc\n")
    os.chmod(fake, 0o755)
    os.makedirs(os.path.join(tmp, "row19_slice"), exist_ok=True)
    sh = os.path.join(tmp, "job.sh")
    open(sh, "w").write("#!/bin/bash\nT=%s\nPBS_JOBID=J1\n%s" % (tmp, body))
    env = dict(os.environ, FAKE_STATE=os.path.join(tmp, "state"), FAKE_SCRIPT=script)
    r = subprocess.run(["bash", sh], capture_output=True, text=True, env=env, timeout=60)
    calls = int(open(os.path.join(tmp, "state")).read()) if os.path.exists(os.path.join(tmp, "state")) else 0
    return r.returncode, calls, r.stdout


def test_the_template_loop_recycles_and_stops_where_declared():
    tmp = tempfile.mkdtemp()
    try:
        rc, calls, out = _loop_harness(tmp, ["75 1", "75 1", "75 1", "0 0"])           # three resamples then COMPLETE
        assert rc == 0 and calls == 4 and "calls 4" in out
        shutil.rmtree(tmp); tmp = tempfile.mkdtemp()
        rc, calls, out = _loop_harness(tmp, ["75 1", "75 0", "75 1"])                   # a call with no new record ends the job
        assert rc == 75 and calls == 2 and "added no record" in out
        shutil.rmtree(tmp); tmp = tempfile.mkdtemp()
        rc, calls, out = _loop_harness(tmp, ["75 1", "4 0"])                            # HELD ends the job with 4
        assert rc == 4 and calls == 2
        shutil.rmtree(tmp); tmp = tempfile.mkdtemp()
        rc, calls, out = _loop_harness(tmp, ["75 1"] * 5, safe_s=100, job_s=50)        # too little walltime: no call at all
        assert rc == 75 and calls == 0 and "below 100 s" in out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

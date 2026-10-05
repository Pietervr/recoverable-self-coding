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


# --- Codex RSC 0be5547 repairs: the job-versus-process lifecycle in the watch, and sticky logger failures in the template ---

_FAIL_TEE = r'''
tee() {
  command tee "$@"; local rc=$?
  local n; n=$(cat $FAKE_STATE 2>/dev/null || echo 0)
  if [ "$1" = "-a" ] && [ -n "$FAIL_LIVE_AT" ] && [ "$n" = "$FAIL_LIVE_AT" ] && [ ! -e $T/live_failed ]; then touch $T/live_failed; return 1; fi
  if [ "$1" != "-a" ] && [ -n "$FAIL_CAP_AT" ] && [ "$n" = "$FAIL_CAP_AT" ] && [ ! -e $T/cap_failed ]; then touch $T/cap_failed; return 2; fi
  if [ "$1" = "-a" ] && [ -n "$FAIL_MARK_AT" ] && [ ! -e $T/mark_failed ] && tail -1 "$2" | grep -q "call $FAIL_MARK_AT start"; then touch $T/mark_failed; return 3; fi
  return $rc
}
'''


def _loop_with_tee_failure(tmp, script_lines, **fail):
    """The template loop with `tee` wrapped: it fails ONCE, on the named call's live-log tee or capture tee, after passing its
    input through (so the runner's summary still reaches the loop - the worst case: progress parsed, stream incomplete)."""
    tpl = open(os.path.join(T1, "chpc", "row19_slice_rep.pbs.template")).read()
    body = tpl[tpl.index("JOB_START="):].replace("__REP__", "0").replace("__TOKEN__", "tok")
    script = os.path.join(tmp, "script.txt"); open(script, "w").write("\n".join(script_lines) + "\n")
    fake = os.path.join(tmp, "t1py")
    open(fake, "w").write("#!/bin/bash\nn=$(cat $FAKE_STATE 2>/dev/null || echo 0); n=$((n+1)); echo $n > $FAKE_STATE\n"
                          "line=$(sed -n \"${n}p\" $FAKE_SCRIPT); rc=${line%% *}; new=${line##* }\n"
                          "echo \"rep 0: PARTIAL (resume): done $n/200, new $new, resumed 0, wall 1.0 min\"\nexit $rc\n")
    os.chmod(fake, 0o755)
    os.makedirs(os.path.join(tmp, "row19_slice"), exist_ok=True)
    sh = os.path.join(tmp, "job.sh")
    open(sh, "w").write("#!/bin/bash\nT=%s\nPBS_JOBID=J1\n%s\n%s" % (tmp, _FAIL_TEE, body))
    env = dict(os.environ, FAKE_STATE=os.path.join(tmp, "state"), FAKE_SCRIPT=script,
               FAIL_LIVE_AT=str(fail.get("live", "")), FAIL_CAP_AT=str(fail.get("cap", "")), FAIL_MARK_AT=str(fail.get("mark", "")))
    r = subprocess.run(["bash", sh], capture_output=True, text=True, env=env, timeout=60)
    calls = int(open(os.path.join(tmp, "state")).read()) if os.path.exists(os.path.join(tmp, "state")) else 0
    return r.returncode, calls, open(os.path.join(tmp, "row19_slice", "live_rep0.log")).read()


def test_a_logger_or_capture_failure_stops_the_loop_and_survives_into_the_job_final_line():
    from test_row19_watch import W
    tmp = tempfile.mkdtemp()
    try:
        # the clean path: the job-final line keeps the ORIGINAL grammar the watch parses; the call count is on its own line
        rc, calls, log = _loop_with_tee_failure(tmp, ["75 1", "75 1", "0 0"])
        assert rc == 0 and calls == 3 and "recycle: job J1 calls 3" in log
        found, trc, tee = W.terminal_evidence(os.path.join(tmp, "row19_slice", "live_rep0.log"), "J1")
        assert found and trc == "0" and tee == "0"
        assert [n for n, _ in W.call_starts(os.path.join(tmp, "row19_slice", "live_rep0.log"), "J1")] == [1, 2, 3]
        # the live-log tee fails on call 1 while the summary still parses as progress: the loop STOPS (no call 2 could
        # replace the status with a clean one) and the job-final line carries the failure
        for fail, code in ((dict(live=1), "1"), (dict(cap=1), "2"), (dict(live=2), "1")):
            shutil.rmtree(tmp); tmp = tempfile.mkdtemp()
            rc, calls, log = _loop_with_tee_failure(tmp, ["75 1", "75 1", "75 1", "0 0"], **fail)
            stop_call = fail.get("live") or fail.get("cap")
            assert calls == stop_call and "LOGGER FAILURE" in log, (fail, calls, log[-300:])
            found, trc, tee = W.terminal_evidence(os.path.join(tmp, "row19_slice", "live_rep0.log"), "J1")
            assert found and tee == code, (fail, tee)                                   # the watch's logger check alarms on it
        # the call-start MARKER fails (Codex 71dee38): nothing is dispatched for that call, and the failure is the final tee
        for at in (1, 2):
            shutil.rmtree(tmp); tmp = tempfile.mkdtemp()
            rc, calls, log = _loop_with_tee_failure(tmp, ["75 1", "75 1", "75 1", "0 0"], mark=at)
            assert calls == at - 1, (at, calls, log[-300:])                             # the runner was not started for call `at`
            found, trc, tee = W.terminal_evidence(os.path.join(tmp, "row19_slice", "live_rep0.log"), "J1")
            assert found and tee == "3" and f"recycle: job J1 calls {at - 1}" in log, (at, tee, log[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_watch_separates_a_recycled_process_end_from_the_job_end():
    import time as _t
    from test_row19_watch import W, _snapshot, _watch, _set_entry
    iso = lambda t: _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(t))
    keep_q = W.qstat_states
    try:
        with _Patched():
            d, c = _dirs()
            man = _manifest(d, c, n_boot=6)
            L = CampaignLedger(c, 1500.0); tok, _ = L.reserve("main", 0, 1, 3600.0, d)
            mp0 = os.path.join(d, "manifest.json"); json.dump(man, open(mp0, "w"))
            argv = ["--manifest", mp0, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                    "--reservation-token", tok, "--job-id", "J1", "--segment", "1"]
            t_call1 = _t.time() - 120
            with contextlib.redirect_stdout(io.StringIO()):
                assert R19.main(argv) == R19.RESUME                                     # call 1: one record, process ends 75
        mp, lr = _snapshot(d, c, man)
        log = os.path.join(lr, "live_rep0.log")
        open(log, "w").write(f"recycle: job J1 call 1 start {iso(t_call1)}\nrep 0: PARTIAL (resume): done 1/6, new 1,\n")

        # 1. the normal gap between calls: process ended 75, no job-final line, job alive -> NOT an ended job
        _set_entry("J1", runner_started=t_call1 + 5, runner_ended=_t.time() - 30)
        rc, out = _watch(mp)
        assert rc == 0 and "between calls" in out and "no terminal line" not in out, out[-800:]
        W.qstat_states = lambda ids: {j: "R" for j in ids}
        _set_entry("J1", runner_started=_t.time() - 4 * 3600, runner_ended=_t.time() - 3 * 3600)                            # PBS says R: still between calls
        rc, out = _watch(mp, "--qstat")
        assert rc == 0 and "between calls" in out, out[-800:]
        # an unobserved gap past the allowance is an alarm, never silently green
        rc, out = _watch(mp, "--startup-allowance-s", "900")
        assert rc == 1 and "no new call and no job-final line" in out, out[-800:]

        # 2. the next call is active: the ledger still carries call 1's exit 75, but its start is newer -> running, and the
        #    live health checks (stall, stop acknowledgment) apply again
        _set_entry("J1", runner_ended=_t.time() - 90, runner_started=_t.time() - 60)
        open(log, "a").write(f"recycle: job J1 call 2 start {iso(_t.time() - 60)}\n")
        rc, out = _watch(mp)
        assert rc == 0 and "running call 2" in out and "no terminal line" not in out, out[-800:]
        rc, out = _watch(mp, "--stall-h", "0")
        assert rc == 1 and "no new record for" in out                                     # the stall check runs during call 2
        json.dump(dict(id="s1", requested=_t.time() - 7200, scope="rep0"), open(os.path.join(W.LIVE_DIR, "campaign", "STOP_rep0"), "w"))
        rc, out = _watch(mp, "--stall-h", "100")
        assert rc == 1 and "not acknowledged" in out                                      # and the stop-ack check
        os.remove(os.path.join(W.LIVE_DIR, "campaign", "STOP_rep0"))

        # 3. a native crash in call 2: PBS says F, the latest process never ended, the stale 75 is not taken as its exit
        W.qstat_states = lambda ids: {j: "F" for j in ids}
        open(log, "a").write(f"exit 139 tee 0 job J1 end {iso(_t.time())}\n")
        rc, out = _watch(mp, "--qstat")
        assert rc == 1 and "latest process never ended" in out and "belongs to an earlier call" in out and "differs" in out, out[-900:]

        # 4. the actual job end: call 2 completed (exit 0), the job-final line names this job, PBS says F -> ended, clean
        _set_entry("J1", runner_ended=_t.time() - 5, runner_exit=0)
        open(log, "w").write(f"recycle: job J1 call 1 start {iso(t_call1)}\nrecycle: job J1 call 2 start {iso(_t.time() - 60)}\n"
                             f"recycle: job J1 calls 2\nexit 0 tee 0 job J1 end {iso(_t.time())}\n")
        rc, out = _watch(mp, "--qstat")
        assert rc == 0 and " ended " in out.replace("  ", " "), out[-800:]
        # ... and a known logger failure in the job-final line is still an alarm
        open(log, "a").write(f"exit 0 tee 1 job J1 end {iso(_t.time())}\n")
        rc, out = _watch(mp, "--qstat")
        assert rc == 1 and "logger status '1'" in out
    finally:
        W.qstat_states = keep_q


def test_the_jobs_own_final_line_ends_it_whatever_pbs_shows():
    """Codex RSC 71dee38, finding 1: a native failure leaves the newer start and the stale exit 75 (or no runner fields at
    all), and the wrapper writes its own job-final line; with PBS unobserved or still R the watch must still treat the job as
    ended, alarm the unfinished process, and apply the terminal exit and logger checks. Clean active and gap cases stay clean."""
    import time as _t
    from test_row19_watch import W, _snapshot, _watch, _set_entry
    iso = lambda t: _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(t))
    keep_q = W.qstat_states
    try:
        with _Patched():
            d, c = _dirs()
            man = _manifest(d, c, n_boot=6)
            L = CampaignLedger(c, 1500.0); tok, _ = L.reserve("main", 0, 1, 3600.0, d)
            mp0 = os.path.join(d, "manifest.json"); json.dump(man, open(mp0, "w"))
            argv = ["--manifest", mp0, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                    "--reservation-token", tok, "--job-id", "J1", "--segment", "1"]
            t1 = _t.time() - 1
            with contextlib.redirect_stdout(io.StringIO()):
                assert R19.main(argv) == R19.RESUME                                     # call 1 ends 75
            L.runner_start(tok, "J1", "main", 0, d, 1, 3600.0)                           # call 2 starts: newer start, stale exit 75
            tok2, _ = L.reserve("main", 1, 1, 3600.0, d); L.bind(tok2, "J2")            # a job that never reached runner start
        mp, lr = _snapshot(d, c, man)
        log0 = os.path.join(lr, "live_rep0.log")
        base = f"recycle: job J1 call 1 start {iso(t1)}\nrecycle: job J1 call 2 start {iso(_t.time())}\n"
        open(log0, "w").write(base)
        # call 2 active, no final line: clean, under both observations
        for q, args in (("-", ()), ("R", ("--qstat",))):
            W.qstat_states = lambda ids, q=q: {j: q for j in ids}
            rc, out = _watch(mp, *args)
            assert "running call 2" in out and "J1: its job-final line" not in out, (q, out[-900:])
        # call 2 died natively; the wrapper's own final line is present
        open(log0, "w").write(base + f"recycle: job J1 calls 2\nexit 139 tee 0 job J1 end {iso(_t.time())}\n")
        for q, args in (("-", ()), ("R", ("--qstat",))):
            W.qstat_states = lambda ids, q=q: {j: q for j in ids}
            rc, out = _watch(mp, *args)
            assert rc == 1 and "J1: its job-final line exit 139" in out and "belongs to an earlier call" in out and "differs" in out, (q, out[-900:])
        # the first call died before the runner started (no runner fields): the final line still ends the job and alarms
        log1 = os.path.join(lr, "live_rep1.log")
        open(log1, "w").write(f"recycle: job J2 call 1 start {iso(_t.time())}\nrecycle: job J2 calls 1\nexit 139 tee 0 job J2 end {iso(_t.time())}\n")
        W.qstat_states = lambda ids: {j: "R" for j in ids}
        rc, out = _watch(mp, "--qstat")
        assert rc == 1 and "J2: its job-final line exit 139" in out, out[-900:]
        os.remove(log1)
        # a completed job whose final line carries a logger failure, PBS unobserved: the logger alarm still fires
        _set_entry("J1", runner_ended=_t.time(), runner_exit=0)
        open(log0, "w").write(base + f"recycle: job J1 calls 2\nexit 0 tee 3 job J1 end {iso(_t.time())}\n")
        rc, out = _watch(mp)
        assert rc == 1 and "logger status '3'" in out and "never recorded" not in out, out[-900:]
    finally:
        W.qstat_states = keep_q

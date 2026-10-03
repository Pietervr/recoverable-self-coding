"""The live watch (chpc/row19_watch.py), Codex 523249d G, e44f804 R4/R5, 6d8a597 R4, on a constructed local snapshot
(--no-pull): expected jobs come from the ledger (a live job without its task binding past the start-up allowance, and a
runner that ended without a binding, are alarms); progress and failures come from records passing the COMPLETE contract
(a failed record, a record with a missing band or a foreign draw, a lost record against the watermark, a timing row
naming an unaccepted index); a running job's clock starts at ITS start, so a restored record with no timing row still
yields a first-record alarm after the allowance; every ended job must show its own attributed terminal evidence (an
absent log, an old attempt's line, a non-zero logger status are alarms; the C2 entry is exempt); HELD exits, a missing
ledger, an unordered range, and a stop request acknowledged under another id are alarms; the local cache is never
called fresh evidence."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, shutil

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_watch", os.path.join(T1, "chpc", "row19_watch.py"))
W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
# The fixtures build their snapshots in a private live directory: the production cache (chpc/results/row19_slice/live) is
# the slice's actual evidence once the campaign runs and must never be overwritten by a test (3 Oct 2026).
_TEST_LIVE = tempfile.mkdtemp(prefix="row19_watch_test_")
W.LIVE_DIR = os.path.join(_TEST_LIVE, "live"); W.ARCHIVE_DIR = os.path.join(_TEST_LIVE, "archive")
spec2 = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(R19)
from test_row19_slice import _manifest, _run, _dirs, _Patched
from row19_ledger import CampaignLedger
from row19_control_compare import record_sha


def _snapshot(root, campaign, man):
    shutil.rmtree(W.LIVE_DIR, ignore_errors=True)
    os.makedirs(W.LIVE_DIR)
    shutil.copytree(campaign, os.path.join(W.LIVE_DIR, "campaign"))
    shutil.copytree(root, os.path.join(W.LIVE_DIR, os.path.basename(root.rstrip("/"))))
    mp = os.path.join(W.LIVE_DIR, "manifest.json")
    man = dict(man); man["storage"] = dict(man["storage"], root=root, campaign=campaign)
    json.dump(man, open(mp, "w"))
    return mp, os.path.join(W.LIVE_DIR, os.path.basename(root.rstrip("/")))


def _watch(mp, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = W.main(["--manifest", mp, "--no-pull", *args])
    return rc, buf.getvalue()


def _ledger_local():
    return os.path.join(W.LIVE_DIR, "campaign", "budget.json")


def _set_entry(job, **kw):
    st = json.load(open(_ledger_local()))
    for e in st["entries"].values():
        if e.get("job_id") == job:
            e.update(kw)
    json.dump(st, open(_ledger_local(), "w"))


def test_progress_from_the_complete_contract_and_the_cache_is_never_fresh():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "4") == R19.RESUME
    mp, lr = _snapshot(d, c, man)
    _set_entry("j1", runner_exit=None, runner_ended=None)                 # treat it as still running for these checks
    rc, out = _watch(mp)
    assert "accepted 4/10 from strict checkpoint records" in out and "LOCAL CACHE" in out and "no alarms (fresh evidence)" not in out and rc == 0
    ck = os.path.join(lr, "ckpt", [f for f in os.listdir(os.path.join(lr, "ckpt")) if f.endswith(".jsonl")][0])
    lines = open(ck).read().splitlines()
    rec = json.loads(lines[-1]); rec["failed"] = True; rec["failed_reason"] = "x"; rec["sha"] = record_sha(rec)
    open(ck, "w").write("\n".join(lines[:-1] + [json.dumps(rec)]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "failed resample(s) in the checkpoint" in out
    rec = json.loads(lines[-1]); del rec["stats"]["selection"]["ws"]; rec["sha"] = record_sha(rec)     # a missing band, re-hashed
    open(ck, "w").write("\n".join(lines[:-1] + [json.dumps(rec)]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "rejected" in out and "does not hold exactly the bands" in out
    open(ck, "w").write("\n".join(lines[:2]) + "\n")                                                   # a lost record
    rc, out = _watch(mp)
    assert rc == 1 and "watermark" in out and "no accepted record" in out                              # the timing rows name unaccepted indices too
    rec = json.loads(lines[0]); rec["chosen"] = [-1]; rec["sha"] = record_sha(rec)
    open(ck, "w").write("\n".join([json.dumps(rec)] + lines[1:]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "rejected" in out


def test_restored_record_without_timing_still_alarms_on_a_stalled_new_job():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.runner_start(tok, "j2", "main", 0, d, 1, 3600.0)                                           # a new job, resumed, no record of its own
    mp, lr = _snapshot(d, c, man)
    _set_entry("j2", runner_started=time.time() - 5 * 3600)
    os.remove(os.path.join(lr, "timing_0.jsonl"))                                                     # the restored records carry no timing row
    rc, out = _watch(mp, "--expect-original-s", "3600", "--expect-fit-s", "100", "1000")
    assert rc == 1 and "no record from this job" in out and "restored record(s) do not count" in out


def test_terminal_evidence_is_attributed_and_c2_is_exempt():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
    mp, lr = _snapshot(d, c, man)
    rc, out = _watch(mp)
    assert rc == 1 and "live log live_rep0.log is absent" in out                                       # ended job, no log
    open(os.path.join(lr, "live_rep0.log"), "w").write("rep 0: PARTIAL (resume)\nexit 75 tee 0 job jOLD end 2026-10-02T22:00:00Z\n")
    rc, out = _watch(mp)
    assert rc == 1 and "no terminal line names this job" in out                                        # an old attempt's line
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 75 tee 1 job j1 end 2026-10-02T22:01:00Z\n")
    rc, out = _watch(mp)
    assert rc == 1 and "logger status '1'" in out                                                      # tee failed
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 4 tee 0 job j1 end 2026-10-02T22:02:00Z\n")
    rc, out = _watch(mp)
    assert rc == 1 and "differs from the ledger's runner exit" in out                                  # a mismatched exit
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 75 tee 0 job j1 end 2026-10-02T22:03:00Z\n")
    rc, out = _watch(mp)
    assert rc == 0
    # a C2 entry that never ended (killed by PBS) raises no terminal alarm and is noted as judged by its interruption record
    with _Patched():
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("c2", 0, 1, 1800.0, d + "_ctl")
        L.runner_start(tok, "c2.sched", "c2", 0, d + "_ctl", 1, 1800.0)
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 9 * 3600; json.dump(st, open(L.path, "w"))
    os.makedirs(d + "_ctl", exist_ok=True)
    good_kill = dict(job_id="c2.sched", exit_status=271, walltime_requested_s=1800.0, walltime_used_s=1803.0, pbs_killed=True,
                     accepted_records_before=7, original_cache_reused=True, tail_fragment_present=False)
    json.dump(good_kill, open(os.path.join(d + "_ctl", "c2_interruption.json"), "w"))
    mp, lr = _snapshot(d, c, man)
    shutil.copytree(d + "_ctl", os.path.join(W.LIVE_DIR, os.path.basename(d + "_ctl")))
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 75 tee 0 job j1 end 2026-10-02T22:03:00Z\n")
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert "externally killed by design" in out and "c2" not in " ".join(l for l in out.splitlines() if l.strip().startswith("-")) and rc == 0
    # an incomplete, false or mistyped kill receipt is NOT a known kill: alarmed, and the aged C2 trips its start-up obligation
    itp = os.path.join(W.LIVE_DIR, os.path.basename(d + "_ctl"), "c2_interruption.json")
    for mut in (dict(job_id="c2.sched"), dict(good_kill, pbs_killed="yes"), dict(good_kill, exit_status=0), dict(good_kill, walltime_requested_s=3600.0),
                dict(good_kill, walltime_used_s=100.0), dict(good_kill, exit_status=True)):
        json.dump(mut, open(itp, "w"))
        rc, out = _watch(mp, "--startup-allowance-s", "60")
        assert rc == 1 and "incomplete or contradictory" in out and "without a task binding" in out, mut
    json.dump(good_kill, open(itp, "w"))
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 0
    # a control's live log is named by kind; a torn witness and a non-finite timing field are alarms
    with _Patched():
        L = CampaignLedger(c, 1500.0)
        tok1, _ = L.reserve("c1", 0, 1, 3600.0, d + "_c1")
        L.runner_start(tok1, "c1.sched", "c1", 0, d + "_c1", 1, 3600.0); L.runner_end(tok1, 5.0, 75)
    os.makedirs(d + "_c1", exist_ok=True)
    for f in ("task_0.json", "task_index.json"):                                      # the control root's own binding
        shutil.copy(os.path.join(d, f), os.path.join(d + "_c1", f))
    t = json.load(open(os.path.join(d + "_c1", "task_0.json"))); t["expected_accepted"] = 0; t["runs"] = []
    json.dump(t, open(os.path.join(d + "_c1", "task_0.json"), "w"))
    mp, lr = _snapshot(d, c, man)
    shutil.copytree(d + "_ctl", os.path.join(W.LIVE_DIR, os.path.basename(d + "_ctl")))
    shutil.copytree(d + "_c1", os.path.join(W.LIVE_DIR, os.path.basename(d + "_c1")))
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 75 tee 0 job j1 end 2026-10-02T22:03:00Z\n")
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 1 and "live log live_ctl_c1.log is absent" in out
    lc1 = os.path.join(W.LIVE_DIR, os.path.basename(d + "_c1"), "live_ctl_c1.log")
    open(lc1, "w").write("exit 75 tee 0 job c1.sched end \n")                       # a torn witness
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 1 and "no terminal line names this job" in out
    open(lc1, "w").write("exit 75 tee 0 job c1.sched end 2026-10-02T22:10:00Z\n")
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 0, out[-900:]
    tp = os.path.join(lr, "timing_0.jsonl")
    rows = open(tp).read().splitlines()
    open(tp, "w").write("\n".join(rows[:-1] + [rows[-1].replace('"t": ', '"t": Infinity, "was": ')]) + "\n")
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 1 and "non-finite or mistyped" in out
    open(tp, "w").write("\n".join(rows) + "\n")
    # a SETTLED entry without the operator's note keeps its terminal obligations
    st = json.load(open(_ledger_local()))
    for e in st["entries"].values():
        if e.get("job_id") == "j1":
            e.update(state="settled", settled_core_h=0.5, settle_note="")
    json.dump(st, open(_ledger_local(), "w"))
    os.remove(os.path.join(lr, "live_rep0.log"))
    rc, out = _watch(mp, "--startup-allowance-s", "60")
    assert rc == 1 and "live log live_rep0.log is absent" in out


def test_expected_jobs_held_exits_and_stop_ack():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 1, 1, 3600.0, d)
        L.runner_start(tok, "j9", "main", 1, d, 1, 3600.0)
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 3 * 3600; json.dump(st, open(L.path, "w"))
    mp, lr = _snapshot(d, c, man)
    open(os.path.join(lr, "live_rep0.log"), "w").write("exit 75 tee 0 job j1 end 2026-10-02T22:03:00Z\n")
    rc, out = _watch(mp)
    assert rc == 1 and "without a task binding" in out
    _set_entry("j9", runner_exit=4, runner_ended=time.time())
    rc, out = _watch(mp)
    assert rc == 1 and "HELD (exit 4)" in out and "ended (exit 4) without a task binding" in out
    _set_entry("j1", runner_exit=None, runner_ended=None, runner_started=time.time() - 7200)
    json.dump(dict(id="new1", requested=time.time() - 7000, scope="rep0"), open(os.path.join(W.LIVE_DIR, "campaign", "STOP_rep0"), "w"))
    json.dump(dict(request_id="old0", boundary="x", job="j1"), open(os.path.join(lr, "STOP_ACK_rep0.json"), "w"))
    rc, out = _watch(mp, "--stall-h", "0.5")
    assert rc == 1 and "not acknowledged" in out
    json.dump(dict(request_id="new1", boundary="after the last durable record", job="j1"), open(os.path.join(lr, "STOP_ACK_rep0.json"), "w"))
    rc, out = _watch(mp, "--stall-h", "0.5")
    assert "acknowledged at boundary" in out


def test_missing_ledger_first_record_timeout_and_unordered_range():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.runner_start(tok, "j9", "main", 0, d, 1, 3600.0)
        assert _run(d, man, "--job-id", "jq", reserve=False, walltime_s=1e-6) == R19.RESUME
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 5 * 3600; json.dump(st, open(L.path, "w"))
    mp, lr = _snapshot(d, c, man)
    if os.path.exists(os.path.join(lr, "status_0.json")):
        os.remove(os.path.join(lr, "status_0.json"))
    rc, out = _watch(mp, "--expect-original-s", "3600", "--expect-fit-s", "100", "1000")
    assert rc == 1 and "no record from this job" in out
    os.remove(_ledger_local())
    rc, out = _watch(mp)
    assert rc == 1 and "ledger absent" in out
    rc, out = _watch(mp, "--expect-fit-s", "10", "5")
    assert rc == 1 and "ordered" in out

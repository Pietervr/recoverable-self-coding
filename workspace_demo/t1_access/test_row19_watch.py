"""The live watch (chpc/row19_watch.py), Codex 523249d G and e44f804 R4/R5, on a constructed local snapshot (--no-pull):
expected jobs come from the ledger (a live job without its task binding past the start-up allowance is an alarm; a job
whose runner ended without a binding is an alarm); progress and failures come from strict checkpoint records (a failed
record with NO timing row is still an alarm); HELD exits, a missing ledger, an unordered range, a stop request whose
acknowledgment names another request, and an ended job whose live log lacks its terminal line are alarms; and the
local cache is never called fresh evidence."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, shutil

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_watch", os.path.join(T1, "chpc", "row19_watch.py"))
W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
spec2 = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(R19)
from test_row19_slice import _manifest, _run, _dirs, _Patched
from row19_ledger import CampaignLedger


def _snapshot(root, campaign, man):
    """Lay the campaign and the root out under the watch's live directory the way a fresh pull would."""
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


def test_progress_from_strict_records_and_the_cache_is_never_fresh():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "4") == R19.RESUME
    mp, lr = _snapshot(d, c, man)
    rc, out = _watch(mp)
    assert "accepted 4/10 from strict checkpoint records" in out and "LOCAL CACHE" in out and "no alarms (fresh evidence)" not in out
    assert rc == 0
    # a failed record committed WITHOUT a timing row is an alarm (checkpoint-derived)
    ck = os.path.join(lr, "ckpt", [f for f in os.listdir(os.path.join(lr, "ckpt")) if f.endswith(".jsonl")][0])
    lines = open(ck).read().splitlines()
    rec = json.loads(lines[-1]); rec["failed"] = True; rec["failed_reason"] = "x"; rec["sha"] = W.record_sha(rec)
    open(ck, "w").write("\n".join(lines[:-1] + [json.dumps(rec)]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "failed resample(s) in the checkpoint" in out
    # a lost record against the per-record watermark
    open(ck, "w").write("\n".join(lines[:2]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "watermark" in out
    # a rejected (foreign-draw) record
    rec = json.loads(lines[0]); rec["chosen"] = [-1]; rec["sha"] = W.record_sha(rec)
    open(ck, "w").write("\n".join([json.dumps(rec)] + lines[1:]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "rejected" in out


def test_expected_jobs_held_exits_stop_ack_and_terminal_witness():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        L = CampaignLedger(c, 1500.0)
        # a live job on rep 1 that never published a binding, started long ago
        tok, _ = L.reserve("main", 1, 1, 3600.0, d)
        L.runner_start(tok, "j9", "main", 1, d, 1, 3600.0)
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 3 * 3600; json.dump(st, open(L.path, "w"))
    mp, lr = _snapshot(d, c, man)
    rc, out = _watch(mp)
    assert rc == 1 and "without a task binding" in out
    # that job ended HELD: an alarm; and a runner that ended without a binding
    st = json.load(open(os.path.join(W.LIVE_DIR, "campaign", "budget.json")))
    st["entries"][tok].update(runner_exit=4, runner_ended=time.time()); json.dump(st, open(os.path.join(W.LIVE_DIR, "campaign", "budget.json"), "w"))
    rc, out = _watch(mp)
    assert rc == 1 and "HELD (exit 4)" in out and "ended (exit 4) without a task binding" in out
    # an ended job whose live log lacks the terminal line
    e0 = [e for e in st["entries"].values() if e.get("rep") == 0][0]
    e0.update(runner_exit=75, runner_ended=time.time()); json.dump(st, open(os.path.join(W.LIVE_DIR, "campaign", "budget.json"), "w"))
    open(os.path.join(lr, "live_rep0.log"), "w").write("rep 0: PARTIAL (resume)\n")
    rc, out = _watch(mp)
    assert rc == 1 and "no terminal 'exit' line" in out
    open(os.path.join(lr, "live_rep0.log"), "a").write("exit 75 tee 0  end 2026-10-02T22:00:00Z\n")
    # a stop request acknowledged under ANOTHER id is not an acknowledgment
    e0.update(runner_exit=None, runner_ended=None, runner_started=time.time() - 7200); json.dump(st, open(os.path.join(W.LIVE_DIR, "campaign", "budget.json"), "w"))
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
        mp0 = os.path.join(d, "manifest.json"); json.dump(man, open(mp0, "w"))
        # the runner's own task binding without any record (produced: the binding is written before the original fit)
        import fcntl
        assert _run(d, man, "--job-id", "jq", reserve=False, walltime_s=1e-6) == R19.RESUME     # deadline 0: binding + no work
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 5 * 3600; json.dump(st, open(L.path, "w"))
    mp, lr = _snapshot(d, c, man)
    for f in ("status_0.json",):
        if os.path.exists(os.path.join(lr, f)):
            os.remove(os.path.join(lr, f))
    rc, out = _watch(mp, "--expect-original-s", "3600", "--expect-fit-s", "100", "1000")
    assert rc == 1 and "no accepted record" in out
    os.remove(os.path.join(W.LIVE_DIR, "campaign", "budget.json"))
    rc, out = _watch(mp)
    assert rc == 1 and "ledger absent" in out
    rc, out = _watch(mp, "--expect-fit-s", "10", "5")
    assert rc == 1 and "ordered" in out

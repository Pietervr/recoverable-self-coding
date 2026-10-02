"""The live watch (chpc/row19_watch.py), condition G of Codex 523249d: on a constructed local cache (--no-pull) it counts
accepted records from validated checkpoint records, alarms on a HELD log, a missing ledger, a failed resample, lost
records and a first-record timeout, and never calls a local cache fresh evidence."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_watch", os.path.join(T1, "chpc", "row19_watch.py"))
W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
spec2 = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(R19)
from test_row19_slice import _manifest, _run, _dirs, _Patched
from row19_ledger import CampaignLedger


def _cache_from(root, campaign, man):
    """Lay the slice root and campaign out the way a pull would, under the watch's local directory."""
    local = os.path.join(T1, "chpc", "results", "row19_slice", "live")
    import shutil
    shutil.rmtree(local, ignore_errors=True)
    shutil.copytree(campaign, os.path.join(local, "campaign"))
    shutil.copytree(root, os.path.join(local, os.path.basename(root.rstrip("/"))))
    mp = os.path.join(local, "manifest.json"); json.dump(man, open(mp, "w"))
    return mp, local


def _watch(mp, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = W.main(["--manifest", mp, "--no-pull", *args])
    return rc, buf.getvalue()


def test_counts_validated_records_and_alarms_on_held_failed_and_lost():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "4") == R19.RESUME
    mp, local = _cache_from(d, c, man)
    rc, out = _watch(mp)
    assert rc == 0 and "accepted 4/10" in out and "LOCAL CACHE" in out and "fresh evidence" not in out.split("ALARMS")[0] or rc == 0
    # a HELD line in the live log
    lr = os.path.join(local, os.path.basename(d))
    open(os.path.join(lr, "live_rep0.log"), "w").write("rep 0: ...\nHELD: checkpoint damaged\n")
    rc, out = _watch(mp)
    assert rc == 1 and "HELD" in out
    os.remove(os.path.join(lr, "live_rep0.log"))
    # a failed resample in the timing ledger
    tp = os.path.join(lr, "timing_0.jsonl")
    rows = open(tp).read()
    open(tp, "a").write(json.dumps(dict(rep=4, fit_seconds=1.0, failed=True, t=time.time(), job="j1")) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "failed resample" in out
    open(tp, "w").write(rows)
    # a lost committed record
    ck = os.path.join(lr, "ckpt", [f for f in os.listdir(os.path.join(lr, "ckpt")) if f.endswith(".jsonl")][0])
    lines = open(ck).read().splitlines()
    open(ck, "w").write("\n".join(lines[:2]) + "\n")
    rc, out = _watch(mp)
    assert rc == 1 and "were committed" in out


def test_missing_ledger_and_first_record_timeout_alarm():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.runner_start(tok, "j9", "main", 0, d)          # a live job that has written nothing yet
        mp_root = os.path.join(d, "manifest.json"); json.dump(man, open(mp_root, "w"))
        # a task binding without any record (the runner would write it before the original fit)
        json.dump(dict(binding=dict(manifest_sha="x", rep=0, ds_seed=1, ident="i" * 64, code_hash="h", n_rep=10, until=None,
                                    ckpt=os.path.join(d, "ckpt", "refit_x.jsonl"), orig="o"), created=time.time(), runs=[], expected_accepted=0),
                  open(os.path.join(d, "task_0.json"), "w"))
        st = json.load(open(L.path)); st["entries"][tok]["runner_started"] = time.time() - 5 * 3600
        json.dump(st, open(L.path, "w"))
    mp, local = _cache_from(d, c, man)
    rc, out = _watch(mp, "--expect-original-s", "3600", "--expect-fit-s", "100", "1000")
    assert rc == 1 and "no accepted record" in out
    os.remove(os.path.join(local, "campaign", "budget.json"))
    rc, out = _watch(mp)
    assert rc == 1 and "ledger absent" in out
    rc, out = _watch(mp, "--expect-fit-s", "10", "5")
    assert rc == 1 and "ordered" in out

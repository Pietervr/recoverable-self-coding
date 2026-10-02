"""The recovery-control comparison (chpc/row19_control_compare.py), Codex 523249d F and e44f804 R3: a produced C1/C3 pair
on the stub pipeline agrees and is QUALIFIED only against the frozen task rebuilt from the manifest (draws per index,
bands, identity, seed, B), typed statuses bound to the task, and a typed interruption record whose job id is the C2 job
bound in the campaign ledger. Negatives: an edited statistic (stale checksum, then re-hashed), empty, incomplete,
missing field, a foreign draw (chosen=[-1] re-hashed), a string statistic, a foreign complete task target, cooperative
end, killed in the original, not a walltime kill, a string pbs_killed, exit status 0, a job id not bound in the ledger,
a C1 that resumed, and both chains FAILED identically (parity yes, qualification no).

NOTE on the interruption record: the stub cannot be killed by PBS, so the fixture WRITES a stand-in record naming the
job id the ledger binds; this is desk evidence of the comparator's checks, not an observed kill - the real kill is a
slice output."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_control_compare", os.path.join(T1, "chpc", "row19_control_compare.py"))
CC = importlib.util.module_from_spec(spec); spec.loader.exec_module(CC)
spec2 = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(R19)
from test_row19_slice import _stub_run_dataset, _manifest, _run, _dirs, _Patched, CALLS
from row19_ledger import CampaignLedger


def _produce(n_boot=30, segment_c2=7, fail_all=False, target=20):
    """C1 fresh to 0..target-1 in its root; C2 'interrupted' after `segment_c2` and C3 resumed to the target in another root;
    the interruption record is a stand-in that names the ledger-bound C2 job id."""
    d1, c = _dirs(); d2 = tempfile.mkdtemp()
    L = CampaignLedger(c, 1500.0)
    with _Patched():
        CALLS["fail_all"] = fail_all
        try:
            assert _run(d1, _manifest(d1, c, n_boot=n_boot, target=target), "--job-id", "c1.sched", "--until", str(target), kind="c1") == R19.RESUME
            assert _run(d2, _manifest(d2, c, n_boot=n_boot, target=target), "--job-id", "c2.sched", "--until", str(target), "--segment", str(segment_c2), "--pbs-kill-control", kind="c2") == R19.RESUME
            assert _run(d2, _manifest(d2, c, n_boot=n_boot, target=target), "--job-id", "c3.sched", "--until", str(target), kind="c3") == R19.RESUME
        finally:
            CALLS["fail_all"] = False
    ck1 = os.path.join(d1, "ckpt", [f for f in os.listdir(os.path.join(d1, "ckpt")) if f.endswith(".jsonl")][0])
    ck3 = os.path.join(d2, "ckpt", [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0])
    it = os.path.join(d2, "c2_interruption.json")
    json.dump(dict(job_id="c2.sched", exit_status=271, walltime_requested_s=1800.0, walltime_used_s=1803.0, pbs_killed=True,
                   accepted_records_before=segment_c2, original_cache_reused=True, tail_fragment_present=False), open(it, "w"))
    args = ["--manifest", os.path.join(d1, "manifest.json"), "--task", os.path.join(d1, "task_0.json"), "--c1", ck1, "--c3", ck3,
            "--status-c1", os.path.join(d1, "status_0.json"), "--status-c3", os.path.join(d2, "status_0.json"),
            "--interruption", it, "--ledger", L.path, "--target", str(target)]
    return args, ck1, ck3, it, d1, d2, L


def _rewrite(ck, lines):
    open(ck, "w").write("\n".join(lines) + ("\n" if lines else ""))


def test_produced_control_agrees_and_qualifies():
    args, *_ = _produce()
    assert CC.main(args) == 0


def test_edited_statistic_is_a_checksum_failure_then_a_parity_difference():
    args, ck1, ck3, it, d1, d2, L = _produce()
    lines = open(ck3).read().splitlines()
    rec = json.loads(lines[3]); rec["stats"]["selection"]["ws"] += 1e-9
    _rewrite(ck3, lines[:3] + [json.dumps(rec)] + lines[4:])
    assert CC.main(args) == 3
    rec["sha"] = CC.record_sha(rec)
    _rewrite(ck3, lines[:3] + [json.dumps(rec)] + lines[4:])
    assert CC.main(args) == 1


def test_record_negatives_are_refused():
    args, ck1, ck3, it, d1, d2, L = _produce()
    keep = open(ck3).read().splitlines()
    _rewrite(ck3, []); assert CC.main(args) in (2, 3)                                   # empty
    _rewrite(ck3, keep[:19]); assert CC.main(args) in (2, 3)                             # incomplete
    rec = json.loads(keep[0]); del rec["chosen"]; _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["chosen"] = [-1]; rec["sha"] = CC.record_sha(rec)       # a foreign draw, coherently re-hashed
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["stats"]["selection"]["ws"] = "0.1"; rec["sha"] = CC.record_sha(rec)   # a string statistic
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["fit_seconds"] = float("nan"); rec["sha"] = CC.record_sha(rec)
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    _rewrite(ck3, keep); assert CC.main(args) == 0


def test_foreign_complete_target_and_status_binding_are_refused():
    args, ck1, ck3, it, d1, d2, L = _produce(target=21)                                  # a complete 0..20 control
    assert CC.main(args) == 0
    assert CC.main(args[:-1] + ["20"]) in (2, 3)                                         # compared against the declared 20: foreign target
    s1 = json.load(open(os.path.join(d1, "status_0.json"))); s1["policy"] = "other"
    json.dump(s1, open(os.path.join(d1, "status_0.json"), "w"))
    assert CC.main(args) == 2                                                            # status not bound to the frozen task


def test_interruption_negatives_are_non_qualification():
    args, ck1, ck3, it, d1, d2, L = _produce()
    good = json.load(open(it))
    for mut in (dict(pbs_killed=False), dict(pbs_killed="yes"), dict(accepted_records_before=0), dict(accepted_records_before=20),
                dict(walltime_used_s=100.0), dict(exit_status=0), dict(exit_status="271"), dict(job_id="c9.sched"),
                dict(original_cache_reused=False), dict(tail_fragment_present="no"), dict(walltime_used_s=float("nan"))):
        bad = dict(good); bad.update(mut); json.dump(bad, open(it, "w"))
        assert CC.main(args) == 2, mut
    json.dump(good, open(it, "w"))
    assert CC.main(args) == 0


def test_c1_that_resumed_is_not_qualified():
    args, ck1, ck3, it, d1, d2, L = _produce()
    s1 = json.load(open(os.path.join(d1, "status_0.json"))); s1["n_resumed"] = 3
    json.dump(s1, open(os.path.join(d1, "status_0.json"), "w"))
    assert CC.main(args) == 2


def test_identically_failed_chains_agree_but_do_not_qualify():
    args, *_ = _produce(fail_all=True)
    rc = CC.main(args)
    assert rc == 2

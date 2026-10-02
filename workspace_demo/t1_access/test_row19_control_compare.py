"""The recovery-control comparison (chpc/row19_control_compare.py), Codex 523249d F, e44f804 R3, 6d8a597 R3: a produced
C1/C3 pair on the stub pipeline agrees and is QUALIFIED only against the frozen task rebuilt from the manifest, typed
TERMINAL statuses (phase final, exit 75, no breach) whose jobs are the C1/C3 jobs bound in the campaign ledger, and a
typed interruption record naming the ledger's C2 job and requesting exactly C2's reserved walltime. Negatives: an
edited statistic (stale checksum, then re-hashed), empty, incomplete, missing field, a foreign draw, a string
statistic, NaN fit seconds, a foreign complete target, a status not bound to the task, a non-terminal (chain_done)
status, a HELD exit, a memory breach, a job not bound in the ledger, a requested walltime differing from the
reservation, cooperative end, killed in the original, not a walltime kill, a string pbs_killed, exit status 0, a C1
that resumed, and FAILED resamples (parity holds, qualification refused).

NOTE on the interruption record: the stub cannot be killed by PBS, so the fixture WRITES a stand-in record that names
the job id the ledger binds and the walltime it reserved; this is desk evidence of the comparator's checks, not an
observed kill - the real kill is a slice output."""
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
from test_row19_slice import _stub_run_dataset, _manifest, _dirs, _Patched, CALLS
from row19_ledger import CampaignLedger

W_INT = 1800.0


def _run_ctl(root, man, kind, job, *args, walltime_s=3600.0):
    mp = os.path.join(root, "manifest.json"); json.dump(man, open(mp, "w"))
    tok, _ = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).reserve(kind, 0, 1, walltime_s, root)
    return R19.main(["--manifest", mp, "--root", root, "--rep", "0", "--kind", kind, "--walltime-s", str(walltime_s),
                     "--skip-environment-check", "--reservation-token", tok, "--job-id", job, *args])


def _produce(n_boot=30, segment_c2=7, fail_all=False, target=20):
    """C1 fresh to 0..target-1 in its root; C2 'interrupted' after `segment_c2` under a W_INT reservation and C3 resumed
    to the target in another root; the interruption record is a stand-in that names the ledger-bound C2 job and W_INT."""
    d1, c = _dirs(); d2 = tempfile.mkdtemp()
    L = CampaignLedger(c, 1500.0)
    with _Patched():
        CALLS["fail_all"] = fail_all
        try:
            man = _manifest(d1, c, n_boot=n_boot, target=target)                 # ONE manifest for every root, as in production
            assert _run_ctl(d1, man, "c1", "c1.sched", "--until", str(target)) == R19.RESUME
            assert _run_ctl(d2, man, "c2", "c2.sched", "--until", str(target), "--segment", str(segment_c2),
                            "--pbs-kill-control", walltime_s=W_INT) == R19.RESUME
            assert _run_ctl(d2, man, "c3", "c3.sched", "--until", str(target)) == R19.RESUME
        finally:
            CALLS["fail_all"] = False
    ck1 = os.path.join(d1, "ckpt", [f for f in os.listdir(os.path.join(d1, "ckpt")) if f.endswith(".jsonl")][0])
    ck3 = os.path.join(d2, "ckpt", [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0])
    it = os.path.join(d2, "c2_interruption.json")
    json.dump(dict(job_id="c2.sched", exit_status=271, walltime_requested_s=W_INT, walltime_used_s=W_INT + 3.0, pbs_killed=True,
                   accepted_records_before=segment_c2, original_cache_reused=True, tail_fragment_present=False), open(it, "w"))
    args = ["--manifest", os.path.join(d1, "manifest.json"), "--task", os.path.join(d1, "task_0.json"), "--c1", ck1, "--c3", ck3,
            "--status-c1", os.path.join(d1, "status_0.json"), "--status-c3", os.path.join(d2, "status_0.json"),
            "--interruption", it, "--ledger", L.path, "--target", str(target)]
    return args, ck1, ck3, it, d1, d2, L


def _rewrite(ck, lines):
    open(ck, "w").write("\n".join(lines) + ("\n" if lines else ""))


def _mutate_status(path, **kw):
    s = json.load(open(path)); s.update(kw); json.dump(s, open(path, "w"))


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
    _rewrite(ck3, []); assert CC.main(args) in (2, 3)
    _rewrite(ck3, keep[:19]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); del rec["chosen"]; _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["chosen"] = [-1]; rec["sha"] = CC.record_sha(rec)
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["stats"]["selection"]["ws"] = "0.1"; rec["sha"] = CC.record_sha(rec)
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); del rec["stats"]["selection"]["ws"]; rec["sha"] = CC.record_sha(rec)       # a missing band
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    rec = json.loads(keep[0]); rec["fit_seconds"] = float("nan"); rec["sha"] = CC.record_sha(rec)
    _rewrite(ck3, [json.dumps(rec)] + keep[1:]); assert CC.main(args) in (2, 3)
    _rewrite(ck3, keep); assert CC.main(args) == 0


def test_foreign_complete_target_and_status_binding_are_refused():
    args, ck1, ck3, it, d1, d2, L = _produce(target=21)
    assert CC.main(args) == 0
    assert CC.main(args[:-1] + ["20"]) in (2, 3)
    _mutate_status(os.path.join(d1, "status_0.json"), policy="other")
    assert CC.main(args) == 2


def test_nonterminal_held_breached_or_unbound_statuses_are_not_qualified():
    args, ck1, ck3, it, d1, d2, L = _produce()
    s3 = os.path.join(d2, "status_0.json"); keep = json.load(open(s3))
    for mut in (dict(phase="chain_done"), dict(exit=4), dict(exit=0), dict(memory_breach=True), dict(job="c9.sched"), dict(kind="c1")):
        json.dump(dict(keep, **mut), open(s3, "w"))
        assert CC.main(args) == 2, mut
    json.dump(keep, open(s3, "w"))
    assert CC.main(args) == 0


def test_interruption_negatives_are_non_qualification():
    args, ck1, ck3, it, d1, d2, L = _produce()
    good = json.load(open(it))
    for mut in (dict(pbs_killed=False), dict(pbs_killed="yes"), dict(accepted_records_before=0), dict(accepted_records_before=20),
                dict(walltime_used_s=100.0), dict(exit_status=0), dict(exit_status="271"), dict(job_id="c9.sched"),
                dict(original_cache_reused=False), dict(tail_fragment_present="no"), dict(walltime_used_s=float("nan")),
                dict(walltime_requested_s=3600.0, walltime_used_s=3603.0)):                        # not the reserved walltime
        bad = dict(good); bad.update(mut); json.dump(bad, open(it, "w"))
        assert CC.main(args) == 2, mut
    json.dump(good, open(it, "w"))
    assert CC.main(args) == 0


def test_root_token_and_checkpoint_bindings_are_required():
    args, ck1, ck3, it, d1, d2, L = _produce()
    s3 = os.path.join(d2, "status_0.json"); keep = json.load(open(s3))
    for mut in (dict(reservation="000000000000"), dict(checkpoint=os.path.join(d2, "ckpt", "refit_foreign.jsonl")),
                dict(checkpoint=os.path.join(d1, "ckpt", os.path.basename(keep["checkpoint"]))), dict(manifest_sha="0" * 64)):
        json.dump(dict(keep, **mut), open(s3, "w"))
        assert CC.main(args) == 2, mut
    json.dump(keep, open(s3, "w"))
    led = json.load(open(L.path))                                       # C3 reserved in a root other than C2's
    for e in led["entries"].values():
        if e["kind"] == "c3":
            e["root"] = d1
    json.dump(led, open(L.path, "w"))
    assert CC.main(args) == 2


def test_c1_that_resumed_is_not_qualified():
    args, ck1, ck3, it, d1, d2, L = _produce()
    _mutate_status(os.path.join(d1, "status_0.json"), n_resumed=3)
    assert CC.main(args) == 2


def test_identically_failed_chains_agree_but_do_not_qualify():
    args, *_ = _produce(fail_all=True)
    assert CC.main(args) == 2

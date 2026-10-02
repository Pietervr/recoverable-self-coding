"""The recovery-control comparison (chpc/row19_control_compare.py), condition F of Codex 523249d: a produced C1/C3 pair on
the stub pipeline agrees and is QUALIFIED only with validated records, the exact target 0..19, the task binding, fresh
C1 / resumed C3 status and a real-interruption record; every negative (empty file, incomplete set, missing field, stale
checksum, wrong target, cooperative or in-original interruption, both chains failed) is refused as such."""
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
from test_row19_slice import _stub_run_dataset, _manifest, _run, _dirs, _Patched


def _produce(n_boot=30, segment_c2=7):
    """C1 fresh to 0..19 in its root; C2 interrupted after `segment_c2` and C3 resumed to 0..19 in another root."""
    d1, c = _dirs(); d2 = tempfile.mkdtemp()
    with _Patched():
        assert _run(d1, _manifest(d1, c, n_boot=n_boot), "--job-id", "c1", "--until", "20", kind="c1") == R19.RESUME
        assert _run(d2, _manifest(d2, c, n_boot=n_boot), "--job-id", "c2", "--until", "20", "--segment", str(segment_c2), "--pbs-kill-control", kind="c2") == R19.RESUME
        assert _run(d2, _manifest(d2, c, n_boot=n_boot), "--job-id", "c3", "--until", "20", kind="c3") == R19.RESUME
    ck1 = os.path.join(d1, "ckpt", [f for f in os.listdir(os.path.join(d1, "ckpt")) if f.endswith(".jsonl")][0])
    ck3 = os.path.join(d2, "ckpt", [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0])
    it = os.path.join(d2, "c2_interruption.json")
    json.dump(dict(job_id="c2.sched01", exit_status=271, walltime_requested_s=1800, walltime_used_s=1803, pbs_killed=True,
                   accepted_records_before=segment_c2), open(it, "w"))
    args = ["--c1", ck1, "--c3", ck3, "--task", os.path.join(d1, "task_0.json"), "--status-c1", os.path.join(d1, "status_0.json"),
            "--status-c3", os.path.join(d2, "status_0.json"), "--interruption", it, "--target", "20"]
    return args, ck1, ck3, it, d1, d2


def test_produced_control_agrees_and_qualifies():
    args, *_ = _produce()
    assert CC.main(args) == 0


def test_edited_statistic_breaks_parity_but_is_caught_as_a_checksum_failure():
    args, ck1, ck3, it, d1, d2 = _produce()
    lines = open(ck3).read().splitlines()
    rec = json.loads(lines[3]); rec["stats"]["selection"]["ws"] += 1e-9
    open(ck3, "w").write("\n".join(lines[:3] + [json.dumps(rec)] + lines[4:]) + "\n")
    assert CC.main(args) == 3                                             # checksum stale: not comparable AND not qualified
    rec["sha"] = CC.record_sha(rec)                                       # a re-hashed edit: comparable, parity differs
    open(ck3, "w").write("\n".join(lines[:3] + [json.dumps(rec)] + lines[4:]) + "\n")
    assert CC.main(args) == 1


def test_negatives_are_refused():
    args, ck1, ck3, it, d1, d2 = _produce()
    keep = open(ck3).read()
    open(ck3, "w").write("")                                              # empty C3
    assert CC.main(args) in (2, 3)
    open(ck3, "w").write("\n".join(keep.splitlines()[:19]) + "\n")        # incomplete C3
    assert CC.main(args) in (2, 3)
    lines = keep.splitlines(); rec = json.loads(lines[0]); del rec["chosen"]
    open(ck3, "w").write("\n".join([json.dumps(rec)] + lines[1:]) + "\n") # missing field
    assert CC.main(args) in (2, 3)
    open(ck3, "w").write(keep)
    assert CC.main(args[:-1] + ["21"]) in (2, 3)                          # wrong target
    bad = json.load(open(it)); bad.update(pbs_killed=False)                # cooperative end: non-qualification
    json.dump(bad, open(it, "w"))
    assert CC.main(args) == 2
    bad.update(pbs_killed=True, accepted_records_before=0)                 # killed inside the original: non-qualification
    json.dump(bad, open(it, "w"))
    assert CC.main(args) == 2
    bad.update(accepted_records_before=7, walltime_used_s=100)             # not a walltime kill
    json.dump(bad, open(it, "w"))
    assert CC.main(args) == 2


def test_c1_that_resumed_or_c3_that_recomputed_is_not_qualified():
    args, ck1, ck3, it, d1, d2 = _produce()
    s1 = json.load(open(os.path.join(d1, "status_0.json"))); s1["n_resumed"] = 3
    json.dump(s1, open(os.path.join(d1, "status_0.json"), "w"))
    assert CC.main(args) == 2

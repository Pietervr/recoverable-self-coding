"""Plumbing test of jitter/s2.run_decision's cross-set queue (24 Oct 2026): every pending set's participant-datasets go
through ONE Parallel call, each task writes its own file first (resume unit), the per-set records are assembled with
the same fields as before (members, primary, delta3, participants, archive npz), finished sets are skipped, and a
half-finished set resumes from its task files. decision_task is replaced by a fast fake; no fit runs.
Run: ../../t1_access/.venv/bin/python tests/test_s2_queue.py"""
import json
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import s2  # noqa: E402

CALLS = []


def _fake_task(setting, r, m, base_subject, bases, span_name="primary", quad=None):
    CALLS.append((setting, r, m))
    g3, b3 = -15.0 + 0.001 * m, -15.0 + 0.001 * m - 0.002       # every participant: B3 below G3 -> NEGATIVE set
    return dict(setting=setting, r=r, m=m, base=base_subject, data_id=f"fake{r}_{m}", n_trials=900, n_scored=850,
                scores={"G3": g3, "B3": b3}, fold_sums={"G3": [g3] * 5, "B3": [b3] * 5}, folds=[], seconds=1.5,
                code_hash="fake", quad={}, _xs={"f0_G3_theta": np.zeros(3, dtype=np.float32)})


def _redirect():
    tmp = tempfile.mkdtemp()
    s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR = tmp, os.path.join(tmp, "decision"), os.path.join(tmp, "archive")
    return tmp


def test_queue_assembles_sets_skips_finished_and_resumes():
    old = (s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR)
    s2.decision_task = _fake_task
    s2.PARALLEL_BACKEND = "threading"
    tmp = _redirect()
    try:
        CALLS.clear()
        s2.run_decision("W2", 3, 4, sets=[0, 1, 2])
        assert len(CALLS) == 60 and len({(r, m) for _, r, m in CALLS}) == 60       # 3 sets × 20, each once, one queue
        for r in range(3):
            p = os.path.join(s2.DEC_DIR, "W2", f"set_{r}.json")
            assert os.path.exists(p)
            with open(p) as f:
                rec = json.load(f)
            assert rec["primary"] == "NEGATIVE" and len(rec["participants"]) == 20 and len(rec["delta3"]) == 20
            assert rec["members"] == s2.set_members("W2", r) and rec["wall_s"] == 30.0 and "queue_wall_s" in rec
            assert [row["m"] for row in rec["participants"]] == list(range(20))
            with np.load(os.path.join(s2.ARC_DIR, "W2", f"set_{r}.npz")) as z:
                assert len(z.files) == 20
        assert not os.path.exists(os.path.join(s2.DEC_DIR, "W2", "tasks")) or not os.listdir(os.path.join(s2.DEC_DIR, "W2", "tasks"))
        # finished sets are skipped; a half-finished set resumes from its task files
        CALLS.clear()
        for m in range(7):
            jp, npz = s2.task_paths("W2", 3, m)
            s2.decision_task_to_file("W2", 3, m, 10, {}, "primary", jp, npz)
        CALLS.clear()
        s2.run_decision("W2", 4, 4)
        assert sorted(CALLS) == [("W2", 3, m) for m in range(7, 20)]                 # sets 0-2 skipped, set 3 resumed
        with open(os.path.join(s2.DEC_DIR, "W2", "set_3.json")) as f:
            assert len(json.load(f)["participants"]) == 20
    finally:
        s2.decision_task, s2.PARALLEL_BACKEND, s2.S2_DIR, s2.DEC_DIR, s2.ARC_DIR = old


if __name__ == "__main__":
    import inspect
    import traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception:  # noqa
                fails += 1
                print("FAIL", name)
                traceback.print_exc(limit=3)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)

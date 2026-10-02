"""Tests of the refitting bootstrap's slice hooks (ledger row 19, 2 Oct 2026): the exact-index segment, the wall-clock
deadline, the strict fail-closed restore and the single-writer durable checkpoint. run_dataset is replaced by a fast
stub, so no fit runs; the tests exercise the mechanics, not the statistics.

    NPROC=1 .venv/bin/python <runner> test_refit_slice
"""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, time
import numpy as np
import analyze as A
import simulate as S


def _ds():
    return S.make_dataset("M2B", S.generator_theta("M2B"), n_per_family=4, D=2, layers=np.array([41]), rho=0.0, seed=5)


def _stub_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    """A deterministic fake pipeline: band deltas from the seed, never a fit."""
    rng = np.random.default_rng(seed)
    L = sub.layers.size
    delta = {p: rng.normal(size=(L, sub.n_concepts)) for p in A.PREDICTORS}
    return dict(failed=False, failed_reason="", fit_seconds=0.01, delta=delta)


class _Patched:
    def __enter__(self):
        self.keep = A.run_dataset
        A.run_dataset = _stub_run_dataset
        return self
    def __exit__(self, *a):
        A.run_dataset = self.keep


def _cfg():
    return A.Config(interval="refit", n_boot_refit=12, bands={"ws": (23, 57), "early": (0, 22)})


def test_segment_runs_exactly_k_then_resumes_from_k():
    ds, cfg = _ds(), _cfg()
    with tempfile.TemporaryDirectory() as d, _Patched():
        path = os.path.join(d, "ck.jsonl")
        r1 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=5, durable=True)
        assert r1["partial"] is True and r1["n_new"] == 5 and r1["n_done"] == 5 and r1["segment"] == 5
        assert all(not r1["predictors"][p]["usable"] for p in A.PREDICTORS)     # a partial chain yields no interval
        reps = [json.loads(l)["rep"] for l in open(path) if l.strip()]
        assert reps == [0, 1, 2, 3, 4]
        r2 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=4, durable=True, strict_restore=True)
        assert r2["n_resumed"] == 5 and r2["n_new"] == 4 and r2["n_done"] == 9 and r2["partial"] is True
        reps = [json.loads(l)["rep"] for l in open(path) if l.strip()]
        assert reps == list(range(9))                                           # continues from the next index, in order
        r3 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, durable=True, strict_restore=True)
        assert r3["partial"] is False and r3["n_resumed"] == 9 and r3["n_new"] == 3 and r3["n_done"] == 12
        assert r3["predictors"]["selection"]["usable"] is True
        # the complete chain equals an uninterrupted one on every resample's statistics (same identity, same draws)
        with tempfile.TemporaryDirectory() as d2:
            r_full = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=os.path.join(d2, "ck.jsonl"))
        for s, t in zip(r3["replicates"], r_full["replicates"]):
            assert s["rep"] == t["rep"] and s["stats"] == t["stats"]


def test_deadline_stops_dispatch_and_flags_it():
    ds, cfg = _ds(), _cfg()
    with tempfile.TemporaryDirectory() as d, _Patched():
        path = os.path.join(d, "ck.jsonl")
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, deadline=time.time() - 1.0)
        assert r["stopped_at_deadline"] is True and r["n_new"] == 0 and r["partial"] is True
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, deadline=time.time() + 3600)
        assert r["stopped_at_deadline"] is False and r["partial"] is False and r["n_done"] == 12


def test_strict_restore_holds_on_damage_but_repairs_a_tail_fragment():
    ds, cfg = _ds(), _cfg()
    with tempfile.TemporaryDirectory() as d, _Patched():
        path = os.path.join(d, "ck.jsonl")
        A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=4)
        lines = [l for l in open(path) if l.strip()]
        # (a) a trailing partial line = an interrupted write: repaired, counted, the run continues
        with open(path, "a") as fh:
            fh.write('{"rep": 4, "truncated"')
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=1, strict_restore=True)
        assert r["n_tail_repaired"] == 1 and r["n_resumed"] == 4 and r["n_new"] == 1 and r["n_damaged"] == 0
        # (b) damage inside the file (an edited payload with a stale checksum) holds the run under strict restore
        rec = json.loads(lines[1]); rec["stats"]["selection"]["ws"] += 1.0
        with open(path, "w") as fh:
            fh.write(lines[0]); fh.write(json.dumps(rec) + "\n"); fh.write("".join(lines[2:]))
        try:
            A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=1, strict_restore=True)
            assert False, "strict restore must hold on an unacceptable record"
        except A.CheckpointDamaged:
            pass
        # the same file without strict restore is recomputed (the pre-existing behaviour), counted as damaged
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=1)
        assert r["n_damaged"] == 1


def test_durable_lock_refuses_a_second_writer():
    ds, cfg = _ds(), _cfg()
    with tempfile.TemporaryDirectory() as d, _Patched():
        path = os.path.join(d, "ck.jsonl")
        import fcntl
        os.makedirs(d, exist_ok=True)
        holder = open(path + ".lock", "a+")
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=1, durable=True)
            assert False, "a second writer must be refused"
        except A.CheckpointDamaged:
            pass
        finally:
            fcntl.flock(holder.fileno(), fcntl.LOCK_UN); holder.close()
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=1, durable=True)
        assert r["n_new"] == 1


def test_on_record_sees_every_durable_write():
    ds, cfg = _ds(), _cfg()
    seen = []
    with tempfile.TemporaryDirectory() as d, _Patched():
        path = os.path.join(d, "ck.jsonl")
        A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=path, segment=3, durable=True, on_record=seen.append)
    assert [r["rep"] for r in seen] == [0, 1, 2] and all("sha" in r and "fit_seconds" in r for r in seen)


def test_defaults_leave_the_existing_path_unchanged():
    ds, cfg = _ds(), _cfg()
    with tempfile.TemporaryDirectory() as d, _Patched():
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=os.path.join(d, "ck.jsonl"))
        assert r["partial"] is False and r["segment"] is None and r["stopped_at_deadline"] is False
        assert r["n_tail_repaired"] == 0 and r["predictors"]["selection"]["usable"] is True

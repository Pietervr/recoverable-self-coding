"""The refitting bootstrap's `until` target, `should_stop` boundary and `checkpoint_state` preflight (Codex 523249d,
conditions D, E and G), on the stub pipeline of test_refit_slice; and analyze_dataset(interval_result=) refusing anything
but a completed chain of the same identity (condition B)."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile
import numpy as np
import analyze as A
from test_refit_slice import _ds, _cfg, _Patched


def test_until_is_cumulative_and_segment_is_new_work():
    with _Patched(), tempfile.TemporaryDirectory() as d:
        ds, cfg = _ds(), _cfg()
        p = os.path.join(d, "c.jsonl")
        r1 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=p, until=8, segment=3, durable=True)
        assert r1["n_new"] == 3 and r1["partial"] and not r1["target_complete"] and r1["until"] == 8
        r2 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=p, until=8, durable=True, strict_restore=True)
        assert r2["n_resumed"] == 3 and r2["n_new"] == 5 and r2["target_complete"] and r2["partial"]
        reps = [json.loads(l)["rep"] for l in open(p) if l.strip()]
        assert reps == list(range(8))
        r3 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=p, until=8, durable=True, strict_restore=True)
        assert r3["n_new"] == 0 and r3["target_complete"]                            # nothing beyond the target, ever
        r4 = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=p, durable=True, strict_restore=True)
        assert r4["n_resumed"] == 8 and r4["n_new"] == 4 and not r4["partial"] and r4["usable"]


def test_should_stop_lands_at_a_record_boundary():
    with _Patched(), tempfile.TemporaryDirectory() as d:
        ds, cfg = _ds(), _cfg()
        p = os.path.join(d, "c.jsonl")
        n = {"calls": 0}
        def stop():
            n["calls"] += 1
            return n["calls"] > 4                                                      # allow four dispatches
        r = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, checkpoint_path=p, durable=True, should_stop=stop)
        assert r["stopped_by_request"] and r["n_new"] == 4 and r["partial"]
        assert len([l for l in open(p) if l.strip()]) == 4                              # every dispatched record committed


def test_checkpoint_state_inspects_without_fitting():
    with _Patched(), tempfile.TemporaryDirectory() as d:
        ds, cfg = _ds(), _cfg()
        p = os.path.join(d, "c.jsonl")
        folds = A.stratified_folds(ds.family, cfg.n_outer, 7)
        cs = A.checkpoint_state(ds, cfg, 7, 12, folds, p)
        assert not cs["exists"] and cs["accepted"] == []
        A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, outer_folds=folds, checkpoint_path=p, segment=5, durable=True)
        cs = A.checkpoint_state(ds, cfg, 7, 12, folds, p)
        assert cs["accepted"] == [0, 1, 2, 3, 4] and cs["rejected"] == 0 and not cs["tail_fragment"]
        lines = open(p).read().splitlines()
        rec = json.loads(lines[2]); rec["fit_seconds"] = 5.0
        open(p, "w").write("\n".join(lines[:2] + [json.dumps(rec)] + lines[3:]) + "\n{\"rep\": 9, \"trunc")
        cs = A.checkpoint_state(ds, cfg, 7, 12, folds, p)
        assert cs["rejected"] == 1 and cs["tail_fragment"] and cs["accepted"] == [0, 1, 3, 4]
        cs2 = A.checkpoint_state(ds, cfg, 8, 12, folds, p)                              # another seed: nothing accepted
        assert cs2["accepted"] == [] and cs2["rejected"] >= 4


def test_analyze_dataset_refuses_a_foreign_or_partial_interval_result():
    from test_row19_slice import _stub_run_dataset as real_shaped      # run_dataset's full output structure
    keep0 = A.run_dataset; A.run_dataset = real_shaped
    try:
        _body_analyze_dataset()
    finally:
        A.run_dataset = keep0


def _body_analyze_dataset():
    with tempfile.TemporaryDirectory() as d:
        ds, cfg = _ds(), _cfg()
        folds = A.stratified_folds(ds.family, cfg.n_outer, 7)
        run = A.run_dataset(ds, cfg, 7, outer_folds=folds)
        p = os.path.join(d, "c.jsonl")
        part = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, outer_folds=folds, checkpoint_path=p, segment=5)
        try:
            A.analyze_dataset(ds, cfg, 7, outer_folds=folds, run=run, interval_result=part); raise AssertionError("partial accepted")
        except ValueError:
            pass
        full = A.refit_bootstrap(ds, cfg, seed=7, n_rep=12, outer_folds=folds, checkpoint_path=p)
        n = {"fits": 0}
        keep = A.run_dataset
        def counting(*a, **k):
            n["fits"] += 1; return keep(*a, **k)
        A.run_dataset = counting
        try:
            res = A.analyze_dataset(ds, cfg, 7, outer_folds=folds, run=run, interval_result=full)
        finally:
            A.run_dataset = keep
        assert n["fits"] == 0 and res["interval"]["n_used"] == 12 and "cluster" in res["predictors"]["selection"]
        other = dict(full, seed=8)
        try:
            A.analyze_dataset(ds, cfg, 7, outer_folds=folds, run=run, interval_result=other); raise AssertionError("foreign accepted")
        except ValueError:
            pass

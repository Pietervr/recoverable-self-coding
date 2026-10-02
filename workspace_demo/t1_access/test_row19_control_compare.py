"""The recovery-control comparison (chpc/row19_control_compare.py): an interrupted-then-resumed subchain built on the
stub pipeline must agree field by field with an uninterrupted one, and an edited statistic must be caught."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util
import numpy as np
import analyze as A
import simulate as S

T1 = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("row19_control_compare", os.path.join(T1, "chpc", "row19_control_compare.py"))
CC = importlib.util.module_from_spec(spec); spec.loader.exec_module(CC)


def _stub(sub, cfg, seed, outer_folds=None, n_jobs=1):
    rng = np.random.default_rng(seed)
    return dict(failed=False, failed_reason="", fit_seconds=0.01,
                delta={p: rng.normal(size=(sub.layers.size, sub.n_concepts)) for p in A.PREDICTORS})


def test_resumed_subchain_equals_uninterrupted_and_edits_are_caught():
    keep = A.run_dataset; A.run_dataset = _stub
    try:
        ds = S.make_dataset("M2B", S.generator_theta("M2B"), n_per_family=4, D=2, layers=np.array([41]), rho=0.0, seed=5)
        cfg = A.Config(interval="refit", n_boot_refit=30, bands={"ws": (23, 57), "early": (0, 22)})
        with tempfile.TemporaryDirectory() as d:
            c1 = os.path.join(d, "c1.jsonl"); c3 = os.path.join(d, "c3.jsonl")
            A.refit_bootstrap(ds, cfg, seed=7, n_rep=30, checkpoint_path=c1, segment=20, durable=True)
            A.refit_bootstrap(ds, cfg, seed=7, n_rep=30, checkpoint_path=c3, segment=7, durable=True)       # "interrupted" after 7
            A.refit_bootstrap(ds, cfg, seed=7, n_rep=30, checkpoint_path=c3, segment=13, durable=True, strict_restore=True)
            assert CC.main([c1, c3]) == 0
            lines = open(c3).read().splitlines()
            rec = json.loads(lines[3]); rec["stats"]["selection"]["ws"] += 1e-9
            open(c3, "w").write("\n".join(lines[:3] + [json.dumps(rec)] + lines[4:]) + "\n")
            assert CC.main([c1, c3]) == 1
    finally:
        A.run_dataset = keep

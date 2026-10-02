"""Tests of the row-19 slice runner's mechanics (chpc/row19_slice.py) on a stub pipeline: the environment and code
gates, the budget ledger, the original-run cache across sessions, segment and deadline exits, strict restore, the
status and timing ledgers. No real fit runs.

    NPROC=1 .venv/bin/python <runner> test_row19_slice
"""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R19)

CALLS = {"run_dataset": 0}


def _stub_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    CALLS["run_dataset"] += 1
    rng = np.random.default_rng(seed)
    L = sub.layers.size
    delta = {p: rng.normal(size=(L, sub.n_concepts)) for p in A.PREDICTORS}
    return dict(failed=False, failed_reason="", fit_seconds=0.01, delta=delta, layers=sub.layers,
                converged=np.ones((cfg.n_outer, 8)), inner_conv=np.ones((cfg.n_outer, 8)), inner_nonfinite=np.zeros((cfg.n_outer, 8), bool),
                recovery=np.zeros((cfg.n_outer, 8)), logq=np.zeros((L, 8, sub.n_concepts)), members=list(cfg.members), selected=[])


def _manifest(root, n_boot=10, cap=1500.0, walltime_h=1.0):
    return {"setting": {"generator": "M2S", "grid": {"omega": 1.0}, "D": 2, "layers": [41], "rho": 0.0, "n_per_family": 4},
            "datasets": {"seed_base": 20261003, "reps": [0, 1, 2]},
            "cfg": {"start_policy": "", "interval": "refit", "n_boot_refit": n_boot, "n_starts": 2, "n_starts_inner": 2,
                    "refit_min_usable": 1.0, "n_outer": 3, "n_inner": 2},
            "code": {"files": {"analyze.py": None}},
            "environment": {"python": "x", "jax": "x", "jaxlib": "x", "numpy": "x", "scipy": "x", "joblib": "x", "machine": "x"},
            "pbs": {"cores": 1, "walltime_h": walltime_h, "deadline_reserve_s": 0.0},
            "storage": {"root": root}, "budget": {"core_hours_cap": cap}}


class _Patched:
    def __enter__(self):
        self.keep = (A.run_dataset, A.analyze_dataset)
        A.run_dataset = _stub_run_dataset
        A.analyze_dataset = lambda ds, cfg, seed, outer_folds=None, n_jobs=1, run=None: dict(
            predictors={p: dict(decision="inconclusive", ws=dict(point=0.0, lo=-1.0, hi=1.0)) for p in A.PREDICTORS}, interval={})
        return self
    def __exit__(self, *a):
        A.run_dataset, A.analyze_dataset = self.keep


def _run(root, man, *args):
    mp = os.path.join(root, "manifest.json")
    json.dump(man, open(mp, "w"))
    return R19.main(["--manifest", mp, "--root", root, *args])


def test_environment_gate_holds_before_anything():
    with tempfile.TemporaryDirectory() as d, _Patched():
        code = _run(d, _manifest(d), "--rep", "0", "--job-id", "j1")
        assert code == R19.HELD and not os.path.exists(os.path.join(d, "status_0.json"))


def test_code_pin_mismatch_holds():
    with tempfile.TemporaryDirectory() as d, _Patched():
        man = _manifest(d); man["code"]["files"]["analyze.py"] = "0" * 64
        code = _run(d, man, "--rep", "0", "--job-id", "j1", "--skip-environment-check")
        assert code == R19.HELD


def test_segment_then_resume_with_cached_original_and_budget_ledger():
    CALLS["run_dataset"] = 0
    with tempfile.TemporaryDirectory() as d, _Patched():
        man = _manifest(d, n_boot=10)
        code = _run(d, man, "--rep", "0", "--job-id", "j1", "--segment", "4", "--skip-environment-check")
        assert code == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["partial"] and st["n_new"] == 4 and st["n_done"] == 4 and st["original_cached"] is False
        assert CALLS["run_dataset"] == 1 + 4                         # the original + four resamples (the stub counts both)
        timing = [json.loads(l) for l in open(os.path.join(d, "timing_0.jsonl"))]
        assert [t["rep"] for t in timing] == [0, 1, 2, 3] and all(t["job"] == "j1" for t in timing)
        b = json.load(open(os.path.join(d, "budget.json")))
        assert b["jobs"]["j1"]["state"] == "ended" and b["jobs"]["j1"]["spent_core_h"] >= 0
        code = _run(d, man, "--rep", "0", "--job-id", "j2", "--skip-environment-check")
        assert code == R19.DONE
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["original_cached"] is True and st["n_resumed"] == 4 and st["n_new"] == 6 and st["n_done"] == 10 and not st["partial"]
        assert "result" in st and set(st["result"]) == set(A.PREDICTORS)
        assert CALLS["run_dataset"] == 1 + 4 + 6                     # the original was NOT recomputed on resume


def test_budget_cap_refuses_before_any_fit():
    CALLS["run_dataset"] = 0
    with tempfile.TemporaryDirectory() as d, _Patched():
        man = _manifest(d, cap=0.5, walltime_h=1.0)                   # one core-hour requested against a half-hour cap
        code = _run(d, man, "--rep", "0", "--job-id", "j1", "--skip-environment-check")
        assert code == R19.HELD and CALLS["run_dataset"] == 0
        b = json.load(open(os.path.join(d, "budget.json"))) if os.path.exists(os.path.join(d, "budget.json")) else {"jobs": {}}
        assert "j1" not in b["jobs"]


def test_deadline_exit_is_resumable():
    with tempfile.TemporaryDirectory() as d, _Patched():
        man = _manifest(d, n_boot=6)
        code = _run(d, man, "--rep", "1", "--job-id", "j1", "--walltime-s", "0", "--skip-environment-check")
        assert code == R19.RESUME
        st = json.load(open(os.path.join(d, "status_1.json")))
        assert st["stopped_at_deadline"] and st["n_new"] == 0
        code = _run(d, man, "--rep", "1", "--job-id", "j2", "--skip-environment-check")
        assert code == R19.DONE


def test_strict_restore_damage_holds():
    with tempfile.TemporaryDirectory() as d, _Patched():
        man = _manifest(d, n_boot=6)
        assert _run(d, man, "--rep", "2", "--job-id", "j1", "--segment", "3", "--skip-environment-check") == R19.RESUME
        ck = [f for f in os.listdir(os.path.join(d, "ckpt")) if f.endswith(".jsonl")]
        assert len(ck) == 1
        path = os.path.join(d, "ckpt", ck[0])
        lines = open(path).read().splitlines()
        rec = json.loads(lines[0]); rec["fit_seconds"] = 99.0            # an edited payload with a stale checksum
        open(path, "w").write("\n".join([json.dumps(rec)] + lines[1:]) + "\n")
        assert _run(d, man, "--rep", "2", "--job-id", "j2", "--skip-environment-check") == R19.HELD

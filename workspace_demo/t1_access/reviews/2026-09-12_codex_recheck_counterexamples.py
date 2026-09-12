"""Review fixtures for 44b6d74: no optimization, generated responses, or AWS calls.

These assertions describe defects at the reviewed commit. A later repair should
change their outcome; they are evidence, not desired-behavior regression tests.
Run with t1_access/.venv/bin/python. Numerical fitting and data generation are
mocked; launcher/job functions are extracted without importing their side effects.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import analyze as A
import models as M
import simulate as S
import spotcheck as C


def extract_function(filename, name, namespace):
    tree = ast.parse((HERE / filename).read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), filename, "exec"), namespace)
    return namespace[name]


def endpoint_gate():
    """Resolving at the lower endpoint borrows the upper endpoint's passed diagnostics."""
    visits = {}
    evaluations = []

    def fake_gain(name, theta, seed=0, **kwargs):
        scale = round(float(np.exp(theta[2])), 8)
        visits[(scale, seed)] = visits.get((scale, seed), 0) + 1
        lower_selected = seed == 10 and scale == 2.0 and visits[(scale, seed)] == 2
        value = 0.01 if seed == 1010 or lower_selected else {1.0: 0.002, 2.0: 0.008, 4.0: 0.02}[scale]
        reproduced = not lower_selected
        result = dict(gain=value, se=0.0001, best="M2K", converged={g: True for g in M.FAMILY_G},
                      ref_reproduced=reproduced, starts_at_best={g: 2 if reproduced else 1 for g in M.FAMILY_G},
                      warm_at_best={g: 0 for g in M.FAMILY_G}, theta={g: [scale] for g in M.FAMILY_G},
                      runs={g: [dict(source="cold", scale=scale, reproduced=reproduced)] for g in M.FAMILY_G})
        evaluations.append((scale, seed, copy.deepcopy(result)))
        return result

    with patch.object(S, "expected_gain", fake_gain):
        result = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, lo=1.0, hi=4.0,
                                  min_width=10.0, seed=10, max_iter=3)
    selected = next(r for scale, seed, r in evaluations if scale == 2.0 and seed == 10 and r["gain"] == 0.01)
    assert result["scale"] == 2.0 and not selected["ref_reproduced"]
    assert result["trace"][-1]["scale"] == 4.0
    assert result["calib_ref_reproduced"] and result["note"] == ""
    return dict(selected_scale=result["scale"], selected_reproduced=False,
                archived_calibration_scale=result["trace"][-1]["scale"], gate=result["note"] or "PASS")


def fixed_dataset(layers=(10, 41, 60)):
    n = 64
    return A.Dataset(np.zeros((n, len(layers))), np.zeros(n), np.arange(n),
                     np.repeat(np.arange(8), 8), np.asarray(layers))


def failure_and_row():
    """One failed refit is an assay failure in the decision, but remains usable downstream."""
    ds = fixed_dataset()
    members = M.FAMILY_G + M.FAMILY_X

    def fake_run(sub, cfg, seed, outer_folds=None, n_jobs=1):
        folds = A.stratified_folds(sub.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
        shape = (sub.n_layers, len(folds), len(members))
        failed = sub.group is not None and seed == 6
        base = np.broadcast_to(np.array([0.0, 0.02, 0.01])[:, None], (sub.n_layers, sub.n_concepts)).copy()
        return dict(layers=sub.layers, folds=folds, members=members,
                    delta={p: base.copy() for p in A.PREDICTORS},
                    logq=np.zeros((sub.n_layers, len(members), sub.n_concepts)),
                    n_c=np.ones(sub.n_concepts),
                    selected=[[("M2B", "M3")] * len(folds) for _ in sub.layers],
                    converged=np.ones(shape, bool), inner_conv=np.ones(shape),
                    inner_nonfinite=np.zeros(shape, bool), recovery=np.zeros(shape, int),
                    failed=failed, failed_reason="mock failed refit" if failed else "", fit_seconds=0.0)

    cfg = A.Config(interval="refit", n_boot_refit=4, n_boot=20)
    with patch.object(A, "run_dataset", fake_run):
        out = A.analyze_dataset(ds, cfg, seed=5)
        row = S._row("M3L", {}, 0, 4, ds.layers, out, 0.0)
        with patch.object(S, "make_dataset", return_value=ds):
            runner_row = S.one_replicate("M3L", {}, 0, 4, ds.layers, 0.9, cfg, seed=2026)
    assert row["selection_decision"] == "assay failure" and row["interval_usable"] == 0
    assert row["failed"] == 0 and row["failed_reason"] == ""
    assert "ws_minus_early" in out["predictors"]["selection"]
    assert not any("minus_early" in key for key in row)
    assert "outer_folds" not in out["interval"]
    assert "replicates" in out["interval"] and not any("replicate" in key for key in runner_row)
    frame = pd.DataFrame([row])
    with tempfile.TemporaryDirectory() as directory:
        filename = Path(directory) / "fixture.csv"
        frame.to_csv(filename, index=False)
        summary = S.summarize(str(filename)).iloc[0]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        C.report({"calibration_D4": (frame, [])}, brief=True)
    assert summary["n_usable"] == 1 and summary["coverage"] == 0.0
    assert "failures 0.000%" in buf.getvalue()
    return dict(decision=row["selection_decision"], row_failed=row["failed"], interval_usable=row["interval_usable"],
                summary_n_usable=int(summary["n_usable"]), summary_coverage=float(summary["coverage"]),
                monitor=buf.getvalue().strip(), H2_saved=False, replicate_stats_saved=False, outer_folds_returned=False)


def no_challenge():
    """Cold reproduction alone suppresses any extra training search at a frozen-scale evaluation."""
    levels = np.asarray(M.LEVELS)
    fixed = SimpleNamespace(y=np.tile(np.linspace(-1, 1, levels.size), 8)[:, None],
                            k=np.tile(levels, 8), concept=np.repeat(np.arange(8), levels.size), n_concepts=8)
    batches = []

    def fake_fit(name, data, n_gh, n_starts, rng):
        starts = M.starts_from_moments(name, data, n_starts, rng)
        batches.append(starts)
        runs = [dict(theta=np.zeros(M.MEMBERS[name].n_params), loglik=0.0, converged=True,
                     nfev=1, nit=1) for _ in starts]
        return M.FitResult(name, runs[0]["theta"], 0.0, True, len(runs), len(runs), runs=runs)

    with patch.object(S, "make_dataset", return_value=fixed), patch.object(M, "fit", fake_fit), \
            patch.object(M, "concept_scores", side_effect=lambda name, theta, data, n_gh: np.zeros(data.n_concepts)), \
            patch.object(M, "_run_starts", side_effect=AssertionError("Unexpected challenge search")):
        out = S.expected_gain("M3L", np.zeros(8), seed=2026, graded=("M2K",))
    assert len(batches) == 1 and out["ref_reproduced"] and out["extra_starts"]["M2K"] == 0
    assert len(np.unique(batches[0], axis=0)) == 32
    return dict(distinct_cold_starts=32, extra_starts=0, reproduced=True,
                archived_run_keys=sorted(out["runs"]["M2K"][0]))


def launcher_environment():
    """Exercise the real launcher's dry-run branch with the AWS module replaced in memory."""
    import argparse
    import time

    tree = ast.parse((HERE / "launch_t1.py").read_text())
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)]
    fake_session = SimpleNamespace(client=lambda *args, **kwargs: SimpleNamespace())
    namespace = dict(argparse=argparse, os=os, time=time, __file__=str(HERE / "launch_t1.py"),
                     boto3=SimpleNamespace(Session=lambda **kwargs: fake_session))
    exec(compile(ast.Module(body=assignments, type_ignores=[]), "launcher_constants", "exec"), namespace)
    main = extract_function("launch_t1.py", "main", namespace)
    buf = io.StringIO()
    with patch.dict(os.environ, {"INTERVAL": "refit", "N_BOOT_REFIT": "7"}), \
            patch.object(sys, "argv", ["launch_t1.py", "--task", "calibration", "--run", "review-fixture", "--dry-run"]), \
            contextlib.redirect_stdout(buf):
        main()
    spec = json.loads(buf.getvalue()[buf.getvalue().index("{"):])
    env = spec["Environment"]
    assert "INTERVAL" not in env and "N_BOOT_REFIT" not in env
    return dict(host_interval="refit", request_interval=env.get("INTERVAL"),
                request_n_boot_refit=env.get("N_BOOT_REFIT"), job_default="cluster")


def artifact_selection():
    """The job reads the raw file even when a failed revalidated file is present beside it."""
    entries = [dict(generator=g, kwargs=S.GAIN_KWARGS[g], target=t, D=4, scale=0.5, gain=t,
                    gain_check=t, gain_check_se=t / 10, calib_converged=True, check_converged=True,
                    calib_ref_reproduced=True, check_ref_reproduced=True, note="")
               for g in M.FAMILY_X for t in S.GAINS]
    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "gain_calibration_D4.json"
        raw.write_text(json.dumps(dict(code_hash="fixture-hash", D=4, entries=entries)))
        checked = Path(directory) / "gain_calibration_D4.revalidated.json"
        checked.write_text(json.dumps(dict(entries=[dict(e, gain_check_se=e["target"]) for e in entries])))
        namespace = dict(os=os, json=json, D=4, SEED=2026, WORK=directory, TASK="power",
                         RESULTS_URI="s3://review-fixture/", log=lambda text: None,
                         s3_download=lambda *args: (_ for _ in ()).throw(AssertionError("Unexpected download")))
        gain_file = extract_function("t1_job.py", "gain_file", namespace)
        path = gain_file(A.Config(), SimpleNamespace(config_hash=lambda *args: "fixture-hash"), (41,))
        points, _ = S.power_points(path)
        assert path == str(raw) and len(points) == 12
        with contextlib.redirect_stdout(io.StringIO()):
            problems = C.check_gain_file(C.gain_file_for(directory, 4))
        assert problems
    return dict(job_file="raw", accepted_pairs=12, monitor_file="revalidated", monitor_verdict="FAIL")


def revalidation_archive():
    entry = dict(generator="M3L", kwargs={"pi0": 0.05}, target=0.01, D=4, scale=0.5,
                 gain=0.01, gain_check=0.01, gain_check_se=0.001, calib_converged=True,
                 check_converged=True, calib_ref_reproduced=True, check_ref_reproduced=True,
                 check_runs={"M2K": ["old runs"]}, check_theta={"M2K": [1.0]}, check_loglik={"M2K": 1.0})
    result = dict(gain=0.011, se=0.001, best="M2K", converged={"M2K": True},
                  ref_reproduced=True, starts_at_best={"M2K": 2}, warm_at_best={"M2K": 1},
                  theta={"M2K": [2.0]}, loglik={"M2K": 2.0}, runs={"M2K": ["fresh runs"]})
    with patch.object(S, "expected_gain", return_value=result):
        new = S.revalidate_gain_entries([entry], seed=2026, cfg=A.Config())[0]
    assert new["gain_check"] == 0.011 and new["check_theta"] == {"M2K": [1.0]}
    return dict(new_gain=new["gain_check"], saved_theta=new["check_theta"], actual_theta=result["theta"],
                saved_runs=new["check_runs"], actual_runs=result["runs"])


if __name__ == "__main__":
    for name, fn in [("endpoint_gate", endpoint_gate), ("failure_and_row", failure_and_row),
                     ("no_challenge", no_challenge), ("launcher_environment", launcher_environment),
                     ("artifact_selection", artifact_selection), ("revalidation_archive", revalidation_archive)]:
        print(name + ": " + json.dumps(fn(), sort_keys=True))

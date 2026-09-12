"""Full review 4 fixtures for 8972ba4 (production code unchanged at d1ab54f).

These assertions document defects, not the desired repaired behavior. Response
generation, numerical optimization and AWS are replaced with mocks. The real
runner, checkpoint reader/writer and revalidation file writer are exercised;
the job function is extracted to avoid its top-level cloud/filesystem effects.
Run with t1_access/.venv/bin/python.
"""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

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


def checkpoint_layers():
    """One- and five-layer stages share ds_seed and silently share bootstrap statistics."""
    calls = []

    def fixed_dataset(name, theta, n_per_family, D, layers, rho, seed):
        marker = float(np.exp(theta[-1])) if name == "M3H" else float(len(layers))
        return A.Dataset(np.full((64, len(layers)), marker), np.zeros(64), np.arange(64),
                         np.repeat(np.arange(8), 8), np.asarray(layers))

    def fake_run(sub, cfg, seed, outer_folds=None, n_jobs=1):
        folds = A.stratified_folds(sub.family, cfg.n_outer, seed) if outer_folds is None else outer_folds
        shape = (sub.n_layers, len(folds), len(cfg.members))
        if sub.group is not None:
            calls.append(sub.n_layers)
        return dict(layers=sub.layers, folds=folds, members=cfg.members,
                    delta={p: np.full((sub.n_layers, sub.n_concepts), float(sub.y[0, 0])) for p in A.PREDICTORS},
                    logq=np.zeros((sub.n_layers, len(cfg.members), sub.n_concepts)),
                    n_c=np.ones(sub.n_concepts), selected=[[("M2B", "M3")] * len(folds) for _ in sub.layers],
                    converged=np.ones(shape, bool), inner_conv=np.ones(shape),
                    inner_nonfinite=np.zeros(shape, bool), recovery=np.zeros(shape, int),
                    failed=False, failed_reason="", fit_seconds=0.0)

    with tempfile.TemporaryDirectory() as directory, patch.object(S, "make_dataset", fixed_dataset), \
            patch.object(A, "run_dataset", fake_run):
        cfg = A.Config(interval="refit", n_boot_refit=4, n_boot=20, refit_checkpoint_dir=directory)
        one = S.one_replicate("M2B", {}, 0, 4, (41,), 0.9, cfg, seed=2026,
                              code_hash=S.config_hash(cfg, 4, (41,), 2026))
        assert calls == [1] * 4
        calls.clear()
        five = S.one_replicate("M2B", {}, 0, 4, (25, 33, 41, 49, 57), 0.9, cfg, seed=2026,
                               code_hash=S.config_hash(cfg, 4, (25, 33, 41, 49, 57), 2026))
        assert not calls, "The five-layer stage performed new bootstrap refits"
        assert one["interval_seed"] == five["interval_seed"] and one["code_hash"] != five["code_hash"]
        assert five["selection_ws_point"] == 5.0 and five["selection_ws_lo"] == five["selection_ws_hi"] == 1.0
        assert five["primary_available"] == 1 and five["selection_interval_n_used"] == 4
        cfg.refit_checkpoint_dir = str(Path(directory) / "fresh-five")
        fresh = S.one_replicate("M2B", {}, 0, 4, (25, 33, 41, 49, 57), 0.9, cfg, seed=2026)
        assert calls == [5] * 4 and fresh["selection_ws_lo"] == fresh["selection_ws_hi"] == 5.0
        # Distinct points in the actual recovery grid also have the same weighted grid_tag:
        # tau + 3*sep = 3.5 for (tau=.5, sep=1) and (tau=2, sep=.5).
        cfg.refit_checkpoint_dir = str(Path(directory) / "grid-collision")
        left, right = dict(tau=0.5, sep=1.0), dict(tau=2.0, sep=0.5)
        assert ("M3H", left) in S.recovery_points() and ("M3H", right) in S.recovery_points()
        g1 = S.one_replicate("M3H", left, 0, 4, (41,), 0.9, cfg, seed=2026)
        calls.clear()
        g2 = S.one_replicate("M3H", right, 0, 4, (41,), 0.9, cfg, seed=2026)
        assert g1["interval_seed"] == g2["interval_seed"] and not calls
        assert g2["selection_ws_point"] == 2.0 and g2["selection_ws_lo"] == g2["selection_ws_hi"] == 0.5
    return dict(shared_seed=one["interval_seed"], different_row_hashes=True,
                five_layer_point=five["selection_ws_point"], resumed_interval=[1.0, 1.0],
                fresh_interval=[5.0, 5.0], five_layer_resumed_interval_marked_usable=True,
                five_layer_refits_on_resume=0, recovery_grid_shared_seed=g1["interval_seed"],
                second_grid_point=g2["selection_ws_point"], second_grid_interval=[0.5, 0.5])


def revalidated_writer_reader():
    """The monitor's real revalidation writer makes a file the job rejects, falling back to raw."""
    cfg = A.Config(n_starts_inner=4)
    code_hash = S.config_hash(cfg, 4, (41,), 2026)
    entries = [dict(generator=g, kwargs=S.GAIN_KWARGS[g], target=t, D=4, scale=0.5, gain=t,
                    gain_check=t, gain_check_se=t / 10, calib_converged=True, check_converged=True,
                    calib_ref_reproduced=True, check_ref_reproduced=True, note="")
               for g in M.FAMILY_X for t in S.GAINS]
    uploads = []
    fake_s3 = SimpleNamespace(upload_file=lambda *args: uploads.append(args))
    fake_session = SimpleNamespace(client=lambda service: fake_s3 if service == "s3" else None)
    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "gain_calibration_D4.json"
        raw.write_text(json.dumps(dict(code_hash=code_hash, D=4, seed=2026, entries=entries)))
        with patch.object(S, "revalidate_gain_entries", return_value=[dict(e, gain_check_se=e["target"]) for e in entries]), \
                patch.object(C.boto3, "Session", return_value=fake_session), contextlib.redirect_stdout(io.StringIO()):
            checked = C.revalidate("review-fixture", 4, directory, "unused", seed=2026, n_jobs=1)
        saved = json.loads(Path(checked).read_text())
        assert saved["revalidated_with"] == saved["source_code_hash"] == code_hash
        assert "code_hash" not in saved and "D" not in saved and saved["problems"]
        assert len(uploads) == 1 and uploads[0][0] == checked
        namespace = dict(os=os, json=json, D=4, SEED=2026, WORK=directory, TASK="power",
                         RESULTS_URI="s3://review-fixture/", log=lambda text: None,
                         s3_download=lambda *args: (_ for _ in ()).throw(AssertionError("Unexpected download")))
        gain_file = extract_function("t1_job.py", "gain_file", namespace)
        job_path = gain_file(cfg, S, (41,))
        points, _ = S.power_points(job_path)
        monitor_path = C.gain_file_for(directory, 4)
        with contextlib.redirect_stdout(io.StringIO()):
            problems = C.check_gain_file(monitor_path)
        assert job_path == str(raw) and len(points) == 12 and monitor_path == checked and problems
    return dict(writer_has_code_hash=False, writer_has_D=False, reference_hash_matches_job=True,
                job_file="raw", job_accepted_pairs=12, monitor_file="revalidated", monitor_verdict="FAIL")


def recovered_start_provenance():
    """M.fit's real recovery chain causes all its initial-vector records to be discarded."""
    levels = np.asarray(M.LEVELS)
    fixed = SimpleNamespace(y=np.tile(np.linspace(-1, 1, levels.size), 8)[:, None],
                            k=np.tile(levels, 8), concept=np.repeat(np.arange(8), levels.size), n_concepts=8)
    batches = []

    def fake_optimizer(name, data, starts, n_gh, options):
        batch = len(batches)
        batches.append(np.array(starts, copy=True))
        ll = (-2.0, 0.0, -1.0)[batch]  # initial cold batch fails; recovery finds the best; challenge is worse
        return [dict(start=j, theta=np.asarray(s), loglik=ll, converged=batch != 0, nfev=1, nit=1)
                for j, s in enumerate(starts)]

    with patch.object(S, "make_dataset", return_value=fixed), patch.object(M, "_run_starts", fake_optimizer), \
            patch.object(M, "concept_scores", side_effect=lambda name, theta, data, n_gh: np.zeros(data.n_concepts)):
        result = S.expected_gain("M3L", np.zeros(8), seed=2026, graded=("M2K",), challenge=True)
    assert [len(b) for b in batches] == [S.REF_STARTS, M.N_STARTS_RECOVERY, S.REF_CHALLENGE_STARTS]
    cold = [r for r in result["runs"]["M2K"] if r["source"] == "cold"]
    assert len(cold) == S.REF_STARTS + M.N_STARTS_RECOVERY and all(r["x0"] is None for r in cold)
    assert result["ref_reproduced"] and result["starts_at_best"]["M2K"] == M.N_STARTS_RECOVERY
    return dict(cold_and_recovery_runs=len(cold), missing_initial_vectors=len(cold),
                recorded_batch_ids=sorted({r["batch"] for r in cold}),
                reproduction_count_without_initial_vectors=result["starts_at_best"]["M2K"],
                reference_marked_reproduced=result["ref_reproduced"])


def refreshed_check_provenance():
    """Positive control: every old check_* field is replaced or removed together."""
    entry = dict(generator="M3L", kwargs={"pi0": 0.05}, target=0.01, D=4, scale=0.5,
                 gain=0.01, gain_check=0.01, gain_check_se=0.001, calib_converged=True,
                 check_converged=True, calib_ref_reproduced=True, check_ref_reproduced=True,
                 check_runs={"M2K": ["old"]}, check_theta={"M2K": [1.0]}, check_loglik={"M2K": 1.0},
                 check_obsolete="old field")
    result = dict(gain=0.011, se=0.001, best="M2K", converged={"M2K": True},
                  ref_reproduced=True, starts_at_best={"M2K": 2}, warm_at_best={"M2K": 1},
                  theta={"M2K": [2.0]}, loglik={"M2K": 2.0}, runs={"M2K": ["fresh"]},
                  challenge_improved={"M2K": 1.0})
    with patch.object(S, "expected_gain", return_value=result) as gain:
        updated = S.revalidate_gain_entries([entry], seed=2026, cfg=A.Config())[0]
    assert updated["check_theta"] == result["theta"] and updated["check_runs"] == result["runs"]
    assert updated["check_loglik"] == result["loglik"] and "check_obsolete" not in updated
    assert updated["gain_check"] == result["gain"] and gain.call_args.kwargs["challenge"]
    return dict(fresh_gain_and_provenance_together=True, obsolete_check_field_removed=True)


if __name__ == "__main__":
    with patch.object(M, "minimize", side_effect=AssertionError("Unexpected numerical optimizer")), \
            patch.object(M, "sample", side_effect=AssertionError("Unexpected response simulation")):
        for fn in (checkpoint_layers, revalidated_writer_reader, recovered_start_provenance, refreshed_check_provenance):
            print(fn.__name__ + ": " + json.dumps(fn(), sort_keys=True))

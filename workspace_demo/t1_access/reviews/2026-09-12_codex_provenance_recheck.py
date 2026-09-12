"""Full review 7 fixtures for 71c46fb: provenance repairs and remaining paths.

Edit only temporary copies. Every analysis/calibration result is mocked; do not
run a numerical optimizer, generate response data, or perform an AWS operation.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from botocore.exceptions import ClientError

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import analyze as A
import models as M
import simulate as S

spec = importlib.util.spec_from_file_location(
    "codex_review6_helpers", Path(__file__).with_name("2026-09-12_codex_snapshot_recheck.py"))
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

PIPELINE = """
def run_dataset(ds, cfg, seed, outer_folds=None, n_jobs=1):
    return dict(delta={p: np.full((ds.n_layers, ds.n_concepts), SCORE_VALUE) for p in PREDICTORS},
                failed=False, failed_reason='', fit_seconds=0.0)
"""


def fixed_data(module):
    return module.Dataset(np.zeros((64, 1)), np.zeros(64), np.arange(64),
                          np.repeat(np.arange(8), 8), np.asarray([41]))


def analysis_edit_is_fixed():
    names = ("review7_analysis_old", "review7_analysis_new")
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "analyze.py"
            base = (HERE / "analyze.py").read_text()
            path.write_text(base + PIPELINE.replace("SCORE_VALUE", "1.0"))
            old = F.load_copy(path, names[0])
            snapshot = old.numerical_snapshot()
            ds, cfg = fixed_data(old), old.Config()
            first = old.refit_bootstrap(ds, cfg, 5, n_rep=4, checkpoint_dir=str(root / "ckpt"))
            path.write_text(base + PIPELINE.replace("SCORE_VALUE", "2.0"))
            new = F.load_copy(path, names[1])
            assert old.numerical_snapshot() == snapshot
            assert new.numerical_snapshot() != snapshot
            second = new.refit_bootstrap(ds, cfg, 5, n_rep=4, checkpoint_dir=str(root / "ckpt"))
            assert first["ident"] != second["ident"] and second["n_resumed"] == 0
            assert first["ws"]["lo"] == 1.0 and second["ws"]["lo"] == 2.0
        return dict(old_identity_retained=True, new_identity_separate=True, new_n_resumed=0)
    finally:
        for name in names:
            sys.modules.pop(name, None)


def missing_source_is_fixed():
    with tempfile.TemporaryDirectory() as directory:
        cfg, raw, rev = F.gain_files(directory)
        raw.unlink()
        def absent(bucket, key, local):
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "mock absence"}}, "GetObject")
        job, _, logs = F.job_functions(directory, absent)
        try:
            job(cfg, S, (41,))
        except RuntimeError as error:
            assert "no job-written file" in str(error) and "HELD" in str(error)
        else:
            raise AssertionError("The job accepted a revalidation without its source")
        with contextlib.redirect_stdout(io.StringIO()):
            assert F.C.gain_file_for(directory, 4) is None
    return dict(source="verified absent", job="HELD", monitor="HELD")


def delayed_models_import():
    """models is already loaded when analyze later hashes the model file."""
    names = ("review7_models_old", "review7_models_new", "review7_late_analysis_old", "review7_late_analysis_new")
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path, analysis_path = root / "models.py", root / "analyze.py"
            model_source = (HERE / "models.py").read_text()
            analysis_path.write_text((HERE / "analyze.py").read_text() +
                                     PIPELINE.replace("SCORE_VALUE", "M.review_statistic()"))
            model_path.write_text(model_source + "\ndef review_statistic():\n    return 1.0\n")
            loaded_digest = hashlib.sha256(model_path.read_bytes()).hexdigest()[:16]
            old_model = F.load_copy(model_path, names[0])
            # A preloaded models module remains in Python's import cache while its file changes.
            model_path.write_text(model_source + "\ndef review_statistic():\n    return 2.0\n")
            with patch.dict(sys.modules, {"models": old_model}):
                old_analysis = F.load_copy(analysis_path, names[2])
            new_model = F.load_copy(model_path, names[1])
            with patch.dict(sys.modules, {"models": new_model}):
                new_analysis = F.load_copy(analysis_path, names[3])
            assert old_model.review_statistic() == 1.0 and new_model.review_statistic() == 2.0
            assert old_analysis.numerical_snapshot() == new_analysis.numerical_snapshot()
            assert old_analysis.LOADED_SOURCES["models.py"] != loaded_digest
            ds, cfg = fixed_data(old_analysis), old_analysis.Config()
            checkpoint = str(root / "ckpt")
            stale = old_analysis.refit_bootstrap(ds, cfg, 5, n_rep=4, checkpoint_dir=checkpoint)
            reused = new_analysis.refit_bootstrap(ds, cfg, 5, n_rep=4, checkpoint_dir=checkpoint)
            fresh = new_analysis.refit_bootstrap(ds, cfg, 5, n_rep=4)
            assert stale["ident"] == reused["ident"] and reused["n_resumed"] == 4
            assert reused["ws"]["lo"] == reused["ws"]["hi"] == 1.0
            assert fresh["ws"]["lo"] == fresh["ws"]["hi"] == 2.0
        return dict(preloaded_models_mislabelled=True, different_loaded_code_same_identity=True,
                    n_resumed=4, reused_interval=[1, 1], fresh_interval=[2, 2])
    finally:
        for name in names:
            sys.modules.pop(name, None)


def gain_file_hash_still_reads_disk():
    """The real calibrate_all_gains stamps old generated entries with newly edited code."""
    fake_gain = """
def _one_gain(name, target, seed, cfg, D):
    return dict(generator=name, kwargs=GAIN_KWARGS[name], target=target, D=D,
                scale=SCALE_VALUE, gain=target, gain_check=target, gain_check_se=target/10,
                calib_converged=True, check_converged=True,
                calib_ref_reproduced=True, check_ref_reproduced=True, note='')
"""
    names = ("review7_sim_old", "review7_sim_new")
    registry = dict(A.LOADED_SOURCES)
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("models.py", "analyze.py"):
                (root / filename).write_bytes((HERE / filename).read_bytes())
            path = root / "simulate.py"
            base = (HERE / "simulate.py").read_text()
            path.write_text(base + fake_gain.replace("SCALE_VALUE", "0.5"))
            old = F.load_copy(path, names[0])
            cfg = A.Config(n_starts_inner=4)
            original_hash = old.config_hash(cfg, 4, (41,), 2026)
            path.write_text(base + fake_gain.replace("SCALE_VALUE", "0.75"))
            new = F.load_copy(path, names[1])
            # All twelve calls still use the old loaded procedure, then the real wrapper hashes disk.
            old_result = old.calibrate_all_gains(2026, cfg)
            new_result = new.calibrate_all_gains(2026, cfg)
            assert original_hash != old_result["code_hash"] == new_result["code_hash"]
            assert {e["scale"] for e in old_result["entries"]} == {0.5}
            assert {e["scale"] for e in new_result["entries"]} == {0.75}
            raw = root / "gain_calibration_D4.json"
            raw.write_text(json.dumps(old_result))
            def absent(bucket, key, local):
                raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "mock absence"}}, "GetObject")
            job, _, _ = F.job_functions(directory, absent)
            accepted = job(cfg, new, (41,))
            points, _ = new.power_points(accepted)
            assert accepted == str(raw) and len(points) == 12
        return dict(hash_changed_without_reloading=True, old_and_new_results_share_code_hash=True,
                    old_scales=[0.5], new_scales=[0.75], new_job_accepted_old_pairs=12)
    finally:
        A.LOADED_SOURCES.clear()
        A.LOADED_SOURCES.update(registry)
        for name in names:
            sys.modules.pop(name, None)


if __name__ == "__main__":
    with patch.object(M, "minimize", side_effect=AssertionError("Unexpected optimizer")), \
            patch.object(M, "sample", side_effect=AssertionError("Unexpected response simulation")):
        for fn in (analysis_edit_is_fixed, missing_source_is_fixed, delayed_models_import, gain_file_hash_still_reads_disk):
            print(fn.__name__ + ": " + json.dumps(fn(), sort_keys=True))

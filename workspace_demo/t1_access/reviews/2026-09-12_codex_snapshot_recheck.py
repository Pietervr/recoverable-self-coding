"""Full review 6 fixtures for 2d9d3c0: two remaining gaps and two positive integration checks.

Only temporary copies of source files are edited. Pipeline statistics are mocked;
response simulation, numerical optimization and AWS operations are prohibited.
Job functions are extracted without importing their /opt/ml side effects.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np
from botocore.exceptions import ClientError

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import analyze as A
import models as M
import simulate as S
import spotcheck as C


def extract(name, namespace):
    tree = ast.parse((HERE / "t1_job.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "t1_job.py", "exec"), namespace)
    return namespace[name]


def load_copy(path, module_name):
    module = ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module  # dataclass resolves the defining module here
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module


def loaded_code_snapshot():
    """A running old module hashes newly edited disk files and stamps old statistics as new code."""
    source = (HERE / "analyze.py").read_text()
    fake_pipeline = """
def run_dataset(ds, cfg, seed, outer_folds=None, n_jobs=1):
    return dict(delta={p: np.full((ds.n_layers, ds.n_concepts), SCORE_VALUE) for p in PREDICTORS},
                failed=False, failed_reason='', fit_seconds=0.0)
"""
    names = ("codex_review_loaded_old", "codex_review_loaded_new")
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("models.py", "simulate.py"):
                (root / filename).write_bytes((HERE / filename).read_bytes())
            path = root / "analyze.py"
            path.write_text(source + fake_pipeline.replace("SCORE_VALUE", "1.0"))
            loaded_digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
            old = load_copy(path, names[0])
            # Another session edits the files while the old module remains loaded.
            path.write_text(source + fake_pipeline.replace("SCORE_VALUE", "2.0"))
            fresh_module = load_copy(path, names[1])
            assert old.run_dataset.__code__.co_consts != fresh_module.run_dataset.__code__.co_consts
            old_snapshot = old.numerical_snapshot()
            assert old_snapshot == fresh_module.numerical_snapshot()
            assert old_snapshot["files"]["analyze.py"] != loaded_digest
            ds = old.Dataset(np.zeros((64, 1)), np.zeros(64), np.arange(64),
                             np.repeat(np.arange(8), 8), np.asarray([41]))
            cfg = old.Config()
            ckpt = str(root / "checkpoints")
            stale = old.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=ckpt)
            reused = fresh_module.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=ckpt)
            fresh = fresh_module.refit_bootstrap(ds, cfg, seed=5, n_rep=4)
            assert stale["ident"] == reused["ident"] and reused["n_resumed"] == 4
            assert reused["ws"]["lo"] == reused["ws"]["hi"] == 1.0 and fresh["ws"]["lo"] == fresh["ws"]["hi"] == 2.0
        return dict(old_loaded_code_reports_new_disk_digest=True, different_loaded_procedures_share_identity=True,
                    resumed=4, reused_interval=[1.0, 1.0], fresh_interval=[2.0, 2.0])
    finally:
        for name in names:
            sys.modules.pop(name, None)


def gain_files(directory):
    cfg = A.Config(n_starts_inner=4)
    expected = S.config_hash(cfg, 4, (41,), 2026)
    entries = [dict(generator=g, kwargs=S.GAIN_KWARGS[g], target=t, D=4, scale=0.5, gain=t,
                    gain_check=t, gain_check_se=t / 10, calib_converged=True, check_converged=True,
                    calib_ref_reproduced=True, check_ref_reproduced=True, note="")
               for g in M.FAMILY_X for t in S.GAINS]
    raw = Path(directory) / "gain_calibration_D4.json"
    raw.write_text(json.dumps(dict(code_hash=expected, D=4, seed=2026, entries=entries)))
    fake_client = SimpleNamespace(upload_file=lambda *args: None)
    fake_session = SimpleNamespace(client=lambda *args: fake_client)
    with patch.object(S, "revalidate_gain_entries", return_value=entries), \
            patch.object(C.boto3, "Session", return_value=fake_session), contextlib.redirect_stdout(io.StringIO()):
        rev = Path(C.revalidate("review-fixture", 4, directory, "unused", seed=2026, n_jobs=1))
    return cfg, raw, rev


def job_functions(directory, download):
    logs = []
    namespace = dict(os=os, D=4, SEED=2026, WORK=directory, TASK="power", RESULTS_URI="s3://fixture/run/",
                     log=logs.append, s3=SimpleNamespace(download_file=download), _bucket="fixture", _prefix="run/")
    extract("s3_fetch", namespace)
    return extract("gain_file", namespace), namespace, logs


def orphan_revalidation():
    """The declared orphan-file exception permits execution while the monitor holds it."""
    with tempfile.TemporaryDirectory() as directory:
        cfg, raw, rev = gain_files(directory)
        raw.unlink()
        def absent(bucket, key, local):
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "mock absence"}}, "GetObject")
        job, namespace, logs = job_functions(directory, absent)
        accepted = job(cfg, S, (41,))
        assert accepted == str(rev) and len(S.power_points(accepted)[0]) == 12
        assert any("source verified False" in line for line in logs)
        with contextlib.redirect_stdout(io.StringIO()):
            monitored = C.gain_file_for(directory, 4)
        assert monitored is None
    return dict(source_file="verified absent", job_accepted_pairs=12, source_verified=False, monitor="HELD")


def real_download_contract():
    """Positive: actual s3_fetch + gain_file distinguish absence from auth/transport failure."""
    results = {}
    for outcome in ("AccessDenied", "transport", "NoSuchKey"):
        with tempfile.TemporaryDirectory() as directory:
            cfg, raw, rev = gain_files(directory)
            rev.unlink()
            def download(bucket, key, local):
                if outcome == "transport":
                    raise OSError("mock transport failure")
                raise ClientError({"Error": {"Code": outcome, "Message": "mock"}}, "GetObject")
            job, namespace, logs = job_functions(directory, download)
            if outcome == "NoSuchKey":
                assert job(cfg, S, (41,)) == str(raw)
                results[outcome] = "raw fallback after verified absence"
            else:
                try:
                    job(cfg, S, (41,))
                except RuntimeError as error:
                    assert "HELD" in str(error)
                    results[outcome] = "HELD"
                else:
                    raise AssertionError("A download error did not hold the job")
    return results


def shard_mirror_contract():
    """Positive: actual shard mirror restores only its prefix and retries failed uploads."""
    prefix_a, prefix_b = "run/refit_ckpt/s000of002/", "run/refit_ckpt/s001of002/"
    remote = {prefix_a + "a.jsonl": b'{"rep":0}\n', prefix_b + "b.jsonl": b'{"rep":0}\n'}
    fail = {"once": False}
    def upload(local, bucket, key):
        if fail["once"]:
            fail["once"] = False
            raise OSError("mock upload failure")
        remote[key] = Path(local).read_bytes()
    pager = SimpleNamespace(paginate=lambda **kwargs: [{"Contents": [{"Key": k} for k in remote if k.startswith(kwargs["Prefix"])]}])
    client = SimpleNamespace(get_paginator=lambda name: pager, upload_file=upload,
                             download_file=lambda bucket, key, local: Path(local).write_bytes(remote[key]))
    with tempfile.TemporaryDirectory() as directory:
        namespace = dict(os=os, CKPT_DIR=directory, CKPT_S3=prefix_a, _ckpt_uploaded={},
                         s3=client, _bucket="fixture", log=lambda text: None)
        down, up = extract("ckpt_sync_down", namespace), extract("ckpt_sync_up", namespace)
        assert down() == 1 and sorted(p.name for p in Path(directory).iterdir()) == ["a.jsonl"]
        remote[prefix_b + "b.jsonl"] += b'{"rep":1}\n'
        other = remote[prefix_b + "b.jsonl"]
        assert up() == 0  # unchanged restored files are not uploaded
        own = Path(directory) / "a.jsonl"
        own.write_bytes(own.read_bytes() + b'{"rep":1}\n')
        fail["once"] = True
        assert up() == 0 and "a.jsonl" not in namespace["_ckpt_uploaded"]
        assert up() == 1 and up() == 0
        assert remote[prefix_a + "a.jsonl"] == own.read_bytes() and remote[prefix_b + "b.jsonl"] == other
    return dict(only_own_prefix_restored=True, foreign_progress_preserved=True,
                failed_upload_retried=True, unchanged_uploads_skipped=True)


if __name__ == "__main__":
    with patch.object(M, "minimize", side_effect=AssertionError("Unexpected optimizer")), \
            patch.object(M, "sample", side_effect=AssertionError("Unexpected response simulation")):
        for fn in (loaded_code_snapshot, orphan_revalidation, real_download_contract, shard_mirror_contract):
            print(fn.__name__ + ": " + json.dumps(fn(), sort_keys=True))

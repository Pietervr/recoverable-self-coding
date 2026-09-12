"""Full review 5 fixtures for ce0c034. Assertions document gaps at that commit.

No numerical optimization, response simulation or AWS operation. Real bootstrap
checkpoint code, the real revalidation writer and extracted job functions are
exercised with fixed arrays, mocked pipeline statistics and an in-memory S3 store.
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


def fixed_dataset():
    return A.Dataset(np.zeros((64, 1)), np.zeros(64), np.arange(64),
                     np.repeat(np.arange(8), 8), np.asarray([41]))


def pipeline(calls, value):
    def run(ds, cfg, seed, outer_folds=None, n_jobs=1):
        calls.append(seed)
        return dict(delta={p: np.full((ds.n_layers, ds.n_concepts), value()) for p in A.PREDICTORS},
                    failed=False, failed_reason="", fit_seconds=0.0)
    return run


def checkpoint_numerics():
    ds, cfg, calls = fixed_dataset(), A.Config(), []
    trap = M.TRAP_POINTS
    fake = pipeline(calls, lambda: 1.0 if M.TRAP_POINTS == trap else 2.0)
    with tempfile.TemporaryDirectory() as directory, patch.object(A, "run_dataset", fake):
        before_hash = S.config_hash(cfg, 4, (41,), 2026)
        before = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        calls.clear()
        with patch.object(M, "TRAP_POINTS", trap + 1):
            after_hash = S.config_hash(cfg, 4, (41,), 2026)
            after = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
            assert before_hash != after_hash and before["ident"] == after["ident"]
            assert after["n_resumed"] == 4 and not calls and after["usable"]
            fresh = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4)
            assert after["ws"]["lo"] == 1.0 and fresh["ws"]["lo"] == 2.0
    return dict(numerical_run_hash_changed=True, checkpoint_identity_unchanged=True,
                resumed=after["n_resumed"], cached_interval=[1.0, 1.0], fresh_interval=[2.0, 2.0])


def checkpoint_payload_and_tail():
    ds, cfg, calls = fixed_dataset(), A.Config(), []
    fake = pipeline(calls, lambda: 1.0)
    with tempfile.TemporaryDirectory() as directory, patch.object(A, "run_dataset", fake):
        initial = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        path = Path(initial["checkpoint"])
        lines = path.read_text().splitlines()
        records = [json.loads(line) for line in lines]
        for record in records:
            record["stats"]["selection"]["ws"] = 99.0
        path.write_text("".join(json.dumps(record) + "\n" for record in records))
        calls.clear()
        changed = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        assert changed["n_resumed"] == 4 and changed["n_damaged"] == 0 and not calls
        assert changed["usable"] and changed["ws"]["lo"] == changed["ws"]["hi"] == 99.0
        # A structurally broken nested payload passes the reader and crashes the summarizer.
        missing = json.loads(lines[0])
        missing["stats"]["selection"] = {}
        path.write_text("\n".join([json.dumps(missing)] + lines[1:]) + "\n")
        try:
            A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        except KeyError as error:
            missing_error = str(error)
        else:
            raise AssertionError("The incomplete nested payload was handled")
        assert missing_error == "'ws'"
        # An actual interrupted final write has no newline; appending glues the first repair to that fragment.
        path.write_text("\n".join(lines[:3]) + "\n" + lines[3][:40])
        calls.clear()
        first = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        assert len(calls) == 1 and first["n_resumed"] == 3
        calls.clear()
        second = A.refit_bootstrap(ds, cfg, seed=5, n_rep=4, checkpoint_dir=directory)
        assert len(calls) == 1 and second["n_resumed"] == 3
    return dict(changed_statistics_interval=[99.0, 99.0], changed_statistics_damaged_count=0,
                missing_band_crashes_with=missing_error, first_restart_refits=1,
                second_restart_repeats_repaired_refit=1)


def gain_authentication():
    cfg = A.Config(n_starts_inner=4)
    expected = S.config_hash(cfg, 4, (41,), 2026)
    entries = [dict(generator=g, kwargs=S.GAIN_KWARGS[g], target=t, D=4, scale=0.5, gain=t,
                    gain_check=t, gain_check_se=t / 10, calib_converged=True, check_converged=True,
                    calib_ref_reproduced=True, check_ref_reproduced=True, note="")
               for g in M.FAMILY_X for t in S.GAINS]
    fake_client = SimpleNamespace(upload_file=lambda *args: None)
    fake_session = SimpleNamespace(client=lambda *args: fake_client)
    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "gain_calibration_D4.json"
        raw.write_text(json.dumps(dict(code_hash=expected, D=4, seed=2026, entries=entries)))
        with patch.object(S, "revalidate_gain_entries", return_value=entries), \
                patch.object(C.boto3, "Session", return_value=fake_session), contextlib.redirect_stdout(io.StringIO()):
            rev = Path(C.revalidate("review-fixture", 4, directory, "unused", seed=2026, n_jobs=1))
        valid = json.loads(rev.read_text())
        namespace = dict(os=os, D=4, SEED=2026, WORK=directory, TASK="power", RESULTS_URI="s3://fixture/",
                         log=lambda text: None, s3_download=lambda *args: False)
        job_gain_file = extract("gain_file", namespace)
        assert job_gain_file(cfg, S, (41,)) == str(rev) and C.gain_file_for(directory, 4) == str(rev)
        # Required source digest is only compared if present; deleting it bypasses that check.
        missing = copy.deepcopy(valid)
        del missing["source_digest"]
        rev.write_text(json.dumps(missing))
        assert job_gain_file(cfg, S, (41,)) == str(rev) and C.gain_file_for(directory, 4) == str(rev)
        assert len(S.power_points(str(rev))[0]) == 12
        # The monitor supplies want=None, so a foreign hash inconsistent with the raw file is accepted.
        foreign = copy.deepcopy(valid)
        foreign["code_hash"] = foreign["source_code_hash"] = "ffffffffffff"
        rev.write_text(json.dumps(foreign))
        try:
            job_gain_file(cfg, S, (41,))
        except RuntimeError as error:
            assert "HELD" in str(error)
        else:
            raise AssertionError("The job accepted the foreign hash")
        assert C.gain_file_for(directory, 4) == str(rev)
        with contextlib.redirect_stdout(io.StringIO()):
            assert not C.check_gain_file(str(rev))
        # Real download helper treats an I/O/authorization error exactly like absence.
        rev.unlink()
        def inaccessible(bucket, key, local):
            raise PermissionError("mock S3 AccessDenied while retrieving a present revalidation")
        namespace.update(s3=SimpleNamespace(download_file=inaccessible), _bucket="fixture", _prefix="run/")
        extract("s3_download", namespace)
        accepted = job_gain_file(cfg, S, (41,))
        assert accepted == str(raw) and len(S.power_points(accepted)[0]) == 12
    return dict(missing_source_digest_accepted_by_both=True, foreign_hash_job="HELD",
                foreign_hash_monitor="PASS", revalidation_download_error_job="raw accepted")


def stale_checkpoint_upload():
    key = "run/refit_ckpt/refit_other_job.jsonl"
    remote = {key: b'{"rep":0}\n'}
    pager = SimpleNamespace(paginate=lambda **kwargs: [{"Contents": [{"Key": k} for k in remote]}])
    client = SimpleNamespace(
        get_paginator=lambda name: pager,
        download_file=lambda bucket, name, local: Path(local).write_bytes(remote[name]),
        upload_file=lambda local, bucket, name: remote.__setitem__(name, Path(local).read_bytes()))
    with tempfile.TemporaryDirectory() as directory:
        namespace = dict(os=os, CKPT_DIR=directory, s3=client, _bucket="fixture", _prefix="run/", log=lambda text: None)
        down, up = extract("ckpt_sync_down", namespace), extract("ckpt_sync_up", namespace)
        assert down() == 1
        # The file's owning job finishes another replicate after this job fetched its copy.
        remote[key] += b'{"rep":1}\n'
        assert len(remote[key].splitlines()) == 2
        assert up() == 1
        assert remote[key] == b'{"rep":0}\n'
    return dict(remote_completed_records_before_upload=2, remote_completed_records_after_upload=1,
                stale_foreign_checkpoint_overwritten=True)


if __name__ == "__main__":
    with patch.object(M, "minimize", side_effect=AssertionError("Unexpected optimizer")), \
            patch.object(M, "sample", side_effect=AssertionError("Unexpected response simulation")):
        for fn in (checkpoint_numerics, checkpoint_payload_and_tail, gain_authentication, stale_checkpoint_upload):
            print(fn.__name__ + ": " + json.dumps(fn(), sort_keys=True))

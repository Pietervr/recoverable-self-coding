"""Offline runner review: real launch/run_stage/run_points, mocked fits and S3.

Run with t1_access/.venv/bin/python. No numerical fit, cloud request, or EEG read.
Exercises packing, the actual POINTS wiring, identity preservation and resumption.
"""
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

T1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T1))
os.environ.setdefault('NPROC', '1')
import analyze as A
import launch_t1 as L
import pandas as pd
import simulate as S


def dry_specs(args):
    out = io.StringIO()
    # --dry-run instantiates a client but must never call it or upload anything.
    class NoCalls:
        def __getattr__(self, name):
            raise AssertionError('unexpected AWS call: ' + name)
    with patch.object(L.boto3, 'Session') as session, patch.object(sys, 'argv', ['launch_t1.py', '--dry-run'] + args):
        session.return_value.client.return_value = NoCalls()
        with contextlib.redirect_stdout(out):
            L.main()
    text = out.getvalue()
    specs = []
    decoder = json.JSONDecoder()
    for chunk in text.split('\n{')[1:]:
        specs.append(decoder.raw_decode('{' + chunk)[0])
    return specs


control_args = ['--task', 'calibration', '--generators', 'M2B', '--n-rep', '10', '--seed', '2027',
    '--n-starts-inner', '4', '--interval', 'refit', '--n-boot-refit', '50', '--layers', '41',
    '--shards', '2', '--n-jobs', '5', '--max-hours', '110', '--run', 'review_control']
reference_args = ['--task', 'calibration', '--generators', 'M2S', '--points', 'M2S:omega=2.0',
    '--n-rep', '1000', '--seed', '2028', '--n-starts-inner', '4', '--interval', 'cluster',
    '--layers', '41', '--shards', '10', '--spot', '--max-hours', '60', '--run', 'review_reference']
control, reference = dry_specs(control_args), dry_specs(reference_args)
assert len(control) == 2 and len(reference) == 10
assert 'points_filter.py' in L.CODE_FILES
for i, spec in enumerate(control):
    env = spec['Environment']
    assert (env['SHARD'], env['N_SHARDS'], env['N_JOBS']) == (str(i), '2', '5')
    assert (env['INTERVAL'], env['N_BOOT_REFIT'], env['SEED']) == ('refit', '50', '2027')
    assert spec['StoppingCondition'] == {'MaxRuntimeInSeconds': 396000}
    assert spec['EnableManagedSpotTraining'] is False
for i, spec in enumerate(reference):
    env = spec['Environment']
    assert (env['SHARD'], env['N_SHARDS'], env['POINTS']) == (str(i), '10', 'M2S:omega=2.0')
    assert (env['SEED'], env['INTERVAL']) == ('2028', 'cluster')
    assert spec['StoppingCondition'] == {'MaxRuntimeInSeconds': 216000, 'MaxWaitTimeInSeconds': 432000}
    assert spec['EnableManagedSpotTraining'] is True

# Import the entry file without its cloud/filesystem initialization doing anything.
module_spec = importlib.util.spec_from_file_location('review_t1_job', T1 / 't1_job.py')
J = importlib.util.module_from_spec(module_spec)
with patch.dict(os.environ, TASK='calibration', RESULTS_URI='s3://offline/review/'), \
     patch('os.makedirs'), patch('boto3.client'):
    module_spec.loader.exec_module(J)


class SerialParallel:
    """Evaluate joblib delayed tuples locally, retaining the requested dataset count."""
    def __init__(self, n_jobs): self.n_jobs = n_jobs
    def __call__(self, tasks): return [f(*a, **k) for f, a, k in tasks]


def run_fixture(specs, n_rep, generators, points, seed, interval, jobs):
    calls, saved_progress, datasets = [], [], []
    def fake_fit(name, kw, rep, D, layers, rho, cfg, dataset_bank_seed, extra, code_hash):
        ds_seed = S.dataset_seed(name, kw, rep, D, dataset_bank_seed)
        calls.append((name, json.dumps(kw, sort_keys=True), rep, ds_seed))
        return dict(generator=name, grid=json.dumps(kw, sort_keys=True), rep=rep, D=D,
                    code_hash=code_hash, dataset_seed=ds_seed)
    def fake_summary(path): return pd.DataFrame([{'n':len(pd.read_csv(path))}])
    with tempfile.TemporaryDirectory(prefix='r052-runner-') as td, \
         patch.object(S, 'one_replicate', fake_fit), patch.object(S, 'summarize', fake_summary), \
         patch('joblib.Parallel', SerialParallel), patch.object(J, 'gain_file', side_effect=AssertionError('gain called')):
        cfg = A.Config(n_starts_inner=4, interval=interval, n_boot_refit=50 if interval == 'refit' else 200)
        for spec in specs:
            shard = int(spec['Environment']['SHARD'])
            folder = Path(td) / str(shard); folder.mkdir()
            out = folder / 'output'; out.mkdir()
            J.WORK, J.OUT_DIR = str(folder), str(out)
            J.POINTS, J.SEED, J.N_JOBS, J.INTERVAL = points, seed, jobs, interval
            J.SHARDS, J.SHARD, J.N_SHARDS = [shard], shard, len(specs)
            J.ckpt_sync_down = lambda: 0
            J.ckpt_sync_up = lambda: 0
            J.s3_download = lambda *a: False
            interrupted = False
            def upload(local, key):
                nonlocal interrupted
                if key.endswith('.progress.json'):
                    saved_progress.append(json.loads(Path(local).read_text()))
                    # One synthetic reference interruption after a complete uploaded chunk.
                    if interval == 'cluster' and shard == 0 and not interrupted:
                        interrupted = True
                        raise RuntimeError('review interruption after a saved chunk')
            J.s3_upload = upload
            with contextlib.redirect_stdout(io.StringIO()):
                try: J.run_stage('calibration', n_rep, (41,), generators, cfg, A, S)
                except RuntimeError as e:
                    assert str(e) == 'review interruption after a saved chunk'
                    J.run_stage('calibration', n_rep, (41,), generators, cfg, A, S)
                n_before = len(calls)
                J.run_stage('calibration', n_rep, (41,), generators, cfg, A, S)
                assert len(calls) == n_before, 'a complete shard refitted on resume'
            rows = list(csv.DictReader((folder / J.shard_name('calibration_D4.csv')).open()))
            assert len(rows) == n_rep // len(specs)
            datasets.extend(rows)
        assert len(calls) == n_rep and len(set(calls)) == n_rep
        assert len({r['dataset_seed'] for r in datasets}) == n_rep
        desired = [('M2B', {})] if interval == 'refit' else [('M2S', {'omega':2.0})]
        for row in datasets:
            key = (row['generator'], json.loads(row['grid']))
            assert key in desired
            assert int(row['dataset_seed']) == S.dataset_seed(*key, int(row['rep']), 4, seed)
        assert all(p['points'] == [[n, k] for n, k in desired] for p in saved_progress)
    return dict(shards=len(specs), rows=n_rep, rows_per_shard=n_rep // len(specs),
                requested_dataset_workers=jobs, duplicate_fits=0, resumed_without_refitting=True,
                dataset_seeds_preserved=True, no_gain_calls=True)


result = dict(control=run_fixture(control, 10, 'M2B', None, 2027, 'refit', 5),
              reference=run_fixture(reference, 1000, 'M2S', 'M2S:omega=2.0', 2028, 'cluster', 8),
              ceiling_estimate_at_050_usd_per_hour=dict(control=110, reference=300, combined=410),
              note='Mocked fits verify dispatch and resume only; no throughput or statistical validation.')
Path(__file__).with_suffix('.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))

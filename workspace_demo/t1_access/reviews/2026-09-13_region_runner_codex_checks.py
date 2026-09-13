"""Offline review of 0fe3ac1's region migration, with real launcher/monitor code.

Run with t1_access/.venv/bin/python. Every AWS client is fake; no network,
launch, upload, numerical fit or production output is touched. Writes its JSON
companion. Missing-snapshot and stale-cache cases deliberately expose current
behavior, not passing safety guarantees.
"""
import contextlib
import hashlib
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


def load_module(filename, name):
    spec = importlib.util.spec_from_file_location(name, T1/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NoCalls:
    def __getattr__(self, name):
        raise AssertionError('unexpected AWS method: '+name)


def dry_run(region):
    env = {k: v for k, v in os.environ.items() if k not in ('T1_AWS_REGION', 'T1_AWS_BUCKET')}
    if region is not None:
        env['T1_AWS_REGION'] = region
    with patch.dict(os.environ, env, clear=True):
        sys.modules.pop('aws_env', None)
        launcher = load_module('launch_t1.py', 'review_launcher_'+str(region))
        out = io.StringIO()
        args = ['launch_t1.py', '--dry-run', '--task', 'calibration', '--run', 'region_review',
                '--generators', 'M2B', '--n-rep', '10', '--seed', '2027', '--n-starts-inner', '4',
                '--interval', 'refit', '--n-boot-refit', '50', '--shards', '2', '--n-jobs', '5',
                '--instance-type', 'ml.r7i.2xlarge', '--max-hours', '110']
        with patch.object(launcher.boto3, 'Session') as session, \
             patch.object(sys, 'argv', args), contextlib.redirect_stdout(out):
            session.return_value.client.return_value = NoCalls()
            launcher.main()
        specs = [json.JSONDecoder().raw_decode('{'+x)[0] for x in out.getvalue().split('\n{')[1:]]
    expected_region = region or 'eu-north-1'
    expected_bucket = {'eu-north-1': 'xtenure-cself-pvr',
                       'us-west-2': 'xtenure-cself-pvr-usw2'}[expected_region]
    assert len(specs) == 2
    for request in specs:
        assert f'.ecr.{expected_region}.' in request['AlgorithmSpecification']['TrainingImage']
        uris = [request['Environment']['RESULTS_URI'], request['CheckpointConfig']['S3Uri'],
                request['OutputDataConfig']['S3OutputPath'],
                request['InputDataConfig'][0]['DataSource']['S3DataSource']['S3Uri']]
        assert all(uri.startswith('s3://'+expected_bucket+'/') for uri in uris)
        assert request['Environment']['N_JOBS'] == '5'
        assert request['Environment']['N_BOOT_REFIT'] == '50'
    return launcher, specs


class EmptyS3:
    def __init__(self):
        self.list_calls, self.uploads = [], []
    def list_objects_v2(self, **kw):
        self.list_calls.append(kw)
        return {'Contents': []}
    def upload_file(self, local, bucket, key):
        self.uploads.append(dict(local=local, bucket=bucket, key=key))


def missing_snapshot(launcher):
    s3 = EmptyS3()
    with contextlib.redirect_stdout(io.StringIO()):
        prefix = launcher.upload_code(s3, 'existing_run', resume=True, from_snapshot=True)
    assert len(s3.uploads) == 5
    return dict(requested_resume_from_snapshot=True, remote_snapshot_absent=True,
        current_behavior='uploads current local source instead of refusing',
        returned_prefix=prefix, simulated_uploads=s3.uploads)


def stale_monitor_cache():
    # The same local out_dir survives selection of a different bucket.
    sys.modules.pop('aws_env', None)
    with patch.dict(os.environ, T1_AWS_REGION='us-west-2', T1_AWS_BUCKET='xtenure-cself-pvr-usw2'):
        monitor = load_module('spotcheck.py', 'review_spotcheck_region')
    s3 = EmptyS3()
    import simulate as S
    class StopBeforeAnyFit(RuntimeError):
        pass
    source_seen = []
    def inspect_only(entries, **kwargs):
        source_seen.extend(entries)
        raise StopBeforeAnyFit()
    with tempfile.TemporaryDirectory(prefix='r052-region-cache-') as td:
        old = Path(td)/'gain_calibration_D4.json'
        old.write_text(json.dumps(dict(entries=[{'origin': 'prior Stockholm cache'}], code_hash='a'*12)))
        with patch.object(monitor.boto3, 'Session') as session:
            session.return_value.client.return_value = s3
            found = monitor.pull('existing_run', 'unused', td)
        assert found == {} and old.exists()
        with patch.object(S, 'revalidate_gain_entries', side_effect=inspect_only):
            try:
                monitor.revalidate('existing_run', 4, td, 'unused', 2026, 1)
            except StopBeforeAnyFit:
                pass
        assert source_seen == [{'origin': 'prior Stockholm cache'}]
    return dict(selected_region=monitor.REGION, selected_bucket=monitor.BUCKET,
        destination_has_no_remote_files=True, previous_bucket_gain_file_retained=True,
        revalidation_attempts_previous_cached_source=True,
        source_entries_seen=source_seen, no_fitting_or_upload_performed=True)


def main():
    original, stockholm = dry_run(None)
    oregon_launcher, oregon = dry_run('us-west-2')
    assert original.REGION == 'eu-north-1'
    out = dict(scope=__doc__, source_sha256={name: hashlib.sha256((T1/name).read_bytes()).hexdigest()
        for name in ('aws_env.py', 'launch_t1.py', 'spotcheck.py', 't1_job.py', 'points_filter.py')},
        default_region=original.REGION,
        default_and_oregon_requests_have_consistent_image_code_output_and_checkpoint_regions=True,
        dry_specs={'stockholm': stockholm, 'oregon': oregon},
        absent_migration_snapshot=missing_snapshot(oregon_launcher),
        cross_region_local_cache=stale_monitor_cache())
    destination = Path(__file__).with_suffix('.json')
    destination.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({key: value for key, value in out.items() if key != 'dry_specs'}, indent=2))


if __name__ == '__main__':
    main()

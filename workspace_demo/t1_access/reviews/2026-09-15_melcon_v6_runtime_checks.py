"""Bounded v6 review checks: mocked unit paths and actual parent/two-worker identity.

Uses the RSC venv. No generator, decoder fit, family fit, benchmark or stage C.
Only temporary stores and the adjacent review JSON are written.
"""
import os

THREAD_VARS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
               'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')
for variable in THREAD_VARS:
    os.environ[variable] = '1'

from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PORT = ROOT / 'workspace_demo/melcon_port'
RUN = PORT / 'results/battery/v6-ebaddf98807b'
V5 = PORT / 'results/battery/v5-7fcb46729408'
IDENTITY = 'ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021'
sys.path.insert(0, str(PORT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_files():
    return {str(p.relative_to(PORT)): sha(p) for root in (RUN, V5)
            for p in sorted(root.rglob('*')) if p.is_file()}


def command(args):
    return subprocess.check_output(args, text=True).strip()


def machine_snapshot():
    table = command(['ps', '-axo', 'pid=,ppid=,ni=,%cpu=,rss=,etime=,command='])
    parsed = [line.split(None, 6) for line in table.splitlines()]
    probe = [row for row in parsed if row[0] == '11036' or row[1] == '11036']
    related = [row for row in parsed if row[0] in ('24001', '26380', '6330')
               or 'stage_c_launch.py' in row[6]
               or ('battery.py' in row[6] and 'python' in row[6].lower())]
    return dict(utc=datetime.now(timezone.utc).isoformat(),
                cores_memory_load=command(['sysctl', 'hw.ncpu', 'hw.memsize', 'hw.perflevel0.physicalcpu',
                                          'hw.perflevel1.physicalcpu', 'vm.loadavg', 'vm.swapusage']),
                power=command(['pmset', '-g', 'batt']),
                disk=command(['df', '-h', str(ROOT)]),
                process_columns=['pid', 'ppid', 'nice', 'cpu_percent', 'rss_kib', 'elapsed', 'command'],
                probe_processes=probe, calibration_or_stage_c_processes=related)


def worker_identity(run_dir, rendezvous):
    # Same joblib process backend as stage C; inherit all five variables before importing numerics.
    import battery as worker_bt
    from pathlib import Path as WorkerPath
    import os as worker_os
    import time as worker_time
    assert all(worker_os.environ.get(v) == '1' for v in worker_bt.THREAD_VARS)
    identity = worker_bt.verify_runtime(run_dir)
    pid = worker_os.getpid()
    marker = WorkerPath(rendezvous) / f'{pid}.ready'
    marker.write_text(str(pid))
    deadline = worker_time.monotonic() + 30
    while len(list(WorkerPath(rendezvous).glob('*.ready'))) < 2:
        if worker_time.monotonic() > deadline:
            raise RuntimeError('two distinct runtime workers did not rendezvous within 30 seconds')
        worker_time.sleep(0.02)
    return dict(pid=pid, executable=sys.executable, identity_digest=identity, runtime=worker_bt.runtime())


def main():
    import battery as BT
    import test_battery as tests
    from joblib import Parallel, delayed

    baseline = json.loads((HERE / '2026-09-15_melcon_v6_calibration_checks.json').read_text())
    assert sys.prefix == str(ROOT / '.venv'), sys.prefix
    assert all(os.environ.get(v) == '1' for v in THREAD_VARS)
    before = run_files()
    assert not list((RUN / 'recordings').iterdir()), 'stage C directory is not empty'
    for name, expected in baseline['input_sha256'].items():
        assert sha(RUN / name) == expected, name
    files = [PORT / f for f in BT.CODE_FILES]
    files += [PORT / f for f in ('stage_c_launch.py', 'test_battery.py', 'PREREG_secondary_melcon.md', 'README.md')]
    files += [Path(BT.BMS_PATH), Path(BT.SY.TRIALS_CSV)]
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    snapshot = machine_snapshot()
    parent_identity = BT.verify_runtime(str(RUN))
    assert parent_identity == IDENTITY
    parent_runtime = BT.runtime()
    assert parent_runtime == baseline['runtime']
    subs = BT.templates()
    assert subs == list(range(1, 35))
    checks = [
        ('check_seed_map', (subs,)),
        ('check_statistic_completeness', ()),
        ('check_bracket', ()),
        ('check_reach_and_search', (subs,)),
        ('check_strength_resolution', ()),
        ('check_verdicts', ()),
        ('check_stores_and_provenance', (subs,)),
        ('check_v5_preserved', ()),
    ]
    passed = []
    stdout = io.StringIO()
    # Fail if a selected test reaches a real generator, decoder or recording pipeline.
    guards = []
    with ExitStack() as stack, redirect_stdout(stdout):
        for module, function in ((BT.SY, 'generate'), (BT, 'recording_aucs'), (BT.RC, 'recording_scores')):
            guards.append(stack.enter_context(patch.object(module, function,
                side_effect=AssertionError('real generation/decoding/fitting is outside this review'))))
        for name, args in checks:
            started = time.monotonic()
            result = getattr(tests, name)(*args)
            passed.append(dict(name=name, passed=True, wall_seconds=time.monotonic()-started, result=result))
        assert all(guard.call_count == 0 for guard in guards)

    # Actual namespace verification, not a patched or temporary configuration.
    assert BT.verify_runtime(str(RUN)) == IDENTITY
    with tempfile.TemporaryDirectory(prefix='melcon-v6-runtime-review-') as rendezvous:
        workers = Parallel(n_jobs=2, backend='loky', batch_size=1)(
            delayed(worker_identity)(str(RUN), rendezvous) for _ in range(2))
    assert len({worker['pid'] for worker in workers}) == 2
    assert all(worker['pid'] != os.getpid() and worker['identity_digest'] == IDENTITY
               and worker['runtime'] == parent_runtime for worker in workers)
    assert run_files() == before, 'a calibration/run file changed during the bounded audit'
    assert {str(p.relative_to(ROOT)): sha(p) for p in files} == source_hashes
    assert not list((RUN / 'recordings').iterdir())
    output = dict(utc=datetime.now(timezone.utc).isoformat(),
                  repository_head=command(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
                  review_driver_sha256=sha(Path(__file__)), source_sha256=source_hashes,
                  calibration_evidence_sha256=sha(HERE / '2026-09-15_melcon_v6_calibration_checks.json'),
                  checks=passed, mocked_test_stdout=stdout.getvalue(),
                  real_generation_decoder_pipeline_guard_calls=[guard.call_count for guard in guards],
                  parent=dict(pid=os.getpid(), executable=sys.executable, identity_digest=parent_identity,
                              runtime=parent_runtime),
                  workers=workers, input_and_source_bytes_unchanged=True, stage_c_files=0,
                  run_files_sha256=before, machine_snapshot=snapshot,
                  limitations='Bounded mocked tests and runtime identity only; no new simulated recording, decoder fit, '
                              'family fit, benchmark, EEG, stage C, launch, schedule or monitor change. '
                              'Machine load is a single snapshot, not measured spare throughput.')
    target = HERE / '2026-09-15_melcon_v6_runtime_checks.json'
    target.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(dict(evidence=str(target), passed=[row['name'] for row in passed],
                         parent_pid=os.getpid(), worker_pids=[worker['pid'] for worker in workers],
                         identity_digest=parent_identity, input_and_source_bytes_unchanged=True,
                         stage_c_files=0), indent=2))


if __name__ == '__main__':
    main()

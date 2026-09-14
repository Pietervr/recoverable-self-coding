#!/usr/bin/env python3
"""Run the six read-and-reviewed Melcon artificial/synthetic suites serially.
No stage C. One process at a time, numerical thread counts bounded to one.
The battery unit test's single recording also supplies review diagnostics.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[1] / 'melcon_port'
SUITES = ('test_preprocess.py', 'test_causal.py', 'test_likelihood.py', 'test_recording.py', 'test_group.py', 'test_battery.py')
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'NPROC')
os.environ.update({k: '1' for k in THREADS})


def child(suite):
    def no_eeg(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)) and os.fsdecode(args[0]).lower().endswith('.bdf'):
            raise RuntimeError('Review refuses BDF access')
    sys.addaudithook(no_eeg)
    sys.path.insert(0, str(PORT))
    if suite == 'test_battery.py':
        import recording as RC
        diag = runpy.run_path(str(HERE / '2026-09-14_melcon_v4_diagnostics.py'))
        original = RC.recording_scores
        def capture(rec, *args, **kwargs):
            result = original(rec, *args, **kwargs)
            details = diag['recording_diagnostics'](rec, result)
            (HERE / '2026-09-14_melcon_v4_diagnostics.json').write_text(json.dumps(details, indent=2) + '\n')
            print('REVIEW_DIAGNOSTICS:', json.dumps(details['summary']), flush=True)
            return result
        RC.recording_scores = capture
    runpy.run_path(str(PORT / suite), run_name='__main__')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--suite', choices=SUITES)
    args = ap.parse_args()
    if args.suite:
        child(args.suite)
    else:
        report = {'thread_environment': {k: os.environ[k] for k in THREADS}, 'python': sys.version, 'suites': [],
                  'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PORT.glob('*.py'))}}
        out = HERE / '2026-09-14_melcon_v4_test_results.json'
        for suite in SUITES:
            t0 = time.monotonic()
            p = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--suite', suite], capture_output=True, text=True, timeout=300, cwd=str(PORT))
            row = {'suite': suite, 'returncode': p.returncode, 'elapsed_seconds': time.monotonic()-t0, 'stdout': p.stdout, 'stderr': p.stderr}
            report['suites'].append(row)
            out.write_text(json.dumps(report, indent=2) + '\n')
            print(f'{suite}: exit {p.returncode}, {row["elapsed_seconds"]:.1f} s', flush=True)
            if p.returncode:
                print(p.stdout + p.stderr, flush=True)
                sys.exit(p.returncode)
        print('Six suites passed; detailed receipt:', out, flush=True)

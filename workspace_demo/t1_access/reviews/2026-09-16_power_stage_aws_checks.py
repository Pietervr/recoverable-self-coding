"""Bounded Q4 static checks and illustrative scheduling arithmetic; no numerical imports or AWS calls."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
gain = ROOT / 'sim_results/gain_local_9b277df/gain_calibration_D4.json'
cal = json.loads(gain.read_text())
points = [(e['generator'], dict(e['kwargs'], scale=e['scale'])) for e in cal['entries']]
selected_entries = [e for e in cal['entries'] if float(e['target']) == 0.01]
spec = ','.join(e['generator'] + ':' + ';'.join(f'{k}={v!r}' for k, v in dict(e['kwargs'], scale=e['scale']).items()) for e in selected_entries)
selected = runpy.run_path(str(ROOT / 'points_filter.py'))['select_points'](points, spec)
assert len(points) == 12 and len(selected) == 4
assert [p[0] for p in selected] == ['M3', 'M3H', 'M3V', 'M3L']
scenarios = []
for n_points in (4, 12):
    counts = [0] * 20
    for i in range(n_points * 50):
        counts[i % 20] += 1
    # Assumption only: each full dataset costs the brief's 6,188 fitter seconds.
    # This is NOT a measured mixture-dataset runtime at 8-way concurrency.
    hours_per_dataset = 6188 / 3600
    rounds = max(math.ceil(n / 8) for n in counts)
    fleet_hours = rounds * hours_per_dataset
    scenarios.append({'points': n_points, 'R': 50, 'datasets': n_points * 50, 'per_job_counts': counts,
                      'jobs': 20, 'workers_per_job': 8, 'rounds_equal_time_assumption': rounds,
                      'summed_fitter_hours': n_points * 50 * hours_per_dataset,
                      'ideal_fully_utilized_hours': n_points * 50 * hours_per_dataset / 160,
                      'chunked_equal_time_hours': fleet_hours,
                      'usd_at_unverified_050': 20 * fleet_hours * 0.5,
                      'usd_at_listed_oregon_c7i_04284': 20 * fleet_hours * 0.4284})
files = ['launch_t1.py', 't1_job.py', 'aws_env.py', 'points_filter.py', 'simulate.py', 'analyze.py', 'models.py']
record = {'scope': 'No fitting, gate rerun, response simulation, benchmark, launcher import or AWS operation. Only stored JSON, pure point selection and arithmetic.',
          'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
          'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
          'gain_sha256': hashlib.sha256(gain.read_bytes()).hexdigest(), 'gain_code_hash': cal.get('code_hash'),
          'gain_D': cal.get('D'), 'gain_seed': cal.get('seed'),
          'points_filter_spec_for_stored_artifact': spec, 'selected_points': selected,
          'bare_power_n_rep_2_datasets': len(points) * 2, 'filtered_power_n_rep_2_datasets': len(selected) * 2,
          'arithmetic_assumptions': 'Illustrations only: 20 simultaneous jobs, 8 workers each, equal 6,188 seconds per complete dataset, chunk=N_JOBS, no startup/straggler/retry/spot delay. Fitter time is not measured complete-dataset time.',
          'scenarios': scenarios}
out = Path(__file__).with_suffix('.json')
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))

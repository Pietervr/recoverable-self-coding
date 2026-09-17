"""Bounded row-17 review evidence. No fits, cloud clients, job signals or outcome reads.

Inspects only identity/runtime columns of the Mac probe CSV. The queue experiment
executes the actual run_points definition with fake workers in a temporary folder.
"""
import ast
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
UNIMOG = Path.home() / 'Unimog-Projects'
digest = lambda data: hashlib.sha256(data).hexdigest()
git = lambda repo, *args: subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()
brief = ROOT / 'reviews/2026-09-17_refit_aws_codex_brief.md'
raw_brief = brief.read_bytes()
assert digest(raw_brief) == '351439ccb947dbeac62e3d3683ef6d4ddd4a020cb82c493ac9860dffc42c2b82'
assert raw_brief == subprocess.check_output(['git', '-C', str(REPO), 'show', 'c900d04:workspace_demo/t1_access/reviews/2026-09-17_refit_aws_codex_brief.md'])

sources = {name: digest((ROOT / name).read_bytes()) for name in
           ('models.py', 'analyze.py', 'simulate.py', 'probe_refit.py', 't1_job.py', 'launch_t1.py', 'requirements.txt')}
csv_path = ROOT / 'sim_results/refit_probe_3ca9304/refit_probe_D4.csv'
csv_bytes = csv_path.read_bytes()
rows = list(csv.DictReader(io.StringIO(csv_bytes.decode())))
identities = [{k: r[k] for k in ('generator', 'grid', 'rep', 'D', 'code_hash', 'runtime', 'settings')}
              for r in rows]
counts = {}
for r in identities:
    key = r['generator'] + ' ' + r['grid']
    counts[key] = counts.get(key, 0) + 1
checkpoints = []
for path in sorted((csv_path.parent / 'ckpt').glob('refit_*.jsonl')):
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    checkpoints.append(dict(file=path.name, unique_completed_indices=len({r['rep'] for r in records}),
                            declared_n_rep=sorted({r['n_rep'] for r in records}),
                            seeds=sorted({r['seed'] for r in records})))

# Exercise the real function with a deterministic fake worker. A second writer
# supplies rep 2 after the first batch. The existing process still schedules it.
tree = ast.parse((ROOT / 'simulate.py').read_text())
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_points')
module = ast.Module(body=[fn], type_ignores=[])
joblib = types.ModuleType('joblib')
joblib.delayed = lambda f: lambda *a, **kw: lambda: f(*a, **kw)
class Parallel:
    def __init__(self, n_jobs):
        self.n_jobs = n_jobs
    def __call__(self, calls):
        return [call() for call in calls]
joblib.Parallel = Parallel
saved_joblib = sys.modules.get('joblib')
sys.modules['joblib'] = joblib
scheduled = []
def fake_row(name, kwargs, rep, D, layers, rho, cfg, seed, extra, code_hash):
    scheduled.append(rep)
    return dict(generator=name, grid=json.dumps(kwargs, sort_keys=True), rep=rep, D=D, code_hash=code_hash)
namespace = dict(A=types.SimpleNamespace(Config=object), config_hash=lambda *a: 'fixed',
                 one_replicate=fake_row, csv=csv, json=json, os=os, _time=time)
exec(compile(module, str(ROOT / 'simulate.py'), 'exec'), namespace)
with tempfile.TemporaryDirectory(prefix='r052-queue-fixture-') as folder:
    target = Path(folder) / 'rows.csv'
    inserted = []
    def on_chunk(path, n_done, n_total, elapsed):
        if not inserted:
            with open(path, 'a', newline='') as fh:
                writer = csv.DictWriter(fh, fieldnames=['generator', 'grid', 'rep', 'D', 'code_hash'])
                writer.writerow(dict(generator='M2S', grid='{"omega": 1.0}', rep=2, D=4, code_hash='fixed'))
            inserted.append(2)
    with contextlib.redirect_stdout(io.StringIO()):
        namespace['run_points']([('M2S', {'omega': 1.0})], 4, 4, (41,), .9, object(), 2027, 2,
                                str(target), chunk=2, on_chunk=on_chunk)
    fixture_rows = list(csv.DictReader(target.open()))
    rep2_count = sum(int(r['rep']) == 2 for r in fixture_rows)
assert scheduled == [0, 1, 2, 3] and rep2_count == 2
if saved_joblib is None:
    del sys.modules['joblib']
else:
    sys.modules['joblib'] = saved_joblib

pipeline_h = 4730 / 3600
rate = .467  # local launcher's estimated us-west-2 rate, NOT a verified tariff
result = dict(
    generated_utc=datetime.now(timezone.utc).isoformat(),
    scope='Read-only provenance/arithmetic plus isolated queue fixture; no numerical fits or AWS account calls.',
    rsc_head=git(REPO, 'rev-parse', 'HEAD'), unimog_head=git(UNIMOG, 'rev-parse', 'HEAD'),
    brief_sha256=digest(raw_brief), brief_bytes=len(raw_brief), brief_lines=len(raw_brief.splitlines()),
    source_sha256=sources,
    probe_csv=dict(path=str(csv_path), sha256=digest(csv_bytes), completed=len(rows), counts_by_setting=counts,
                   identities=identities, outcome_columns_inspected=False, checkpoints=checkpoints),
    fixed_queue_fixture=dict(scheduled=scheduled, external_row_inserted=inserted, rep2_rows=rep2_count,
                             proves='run_points does not refresh its pending task list between batches'),
    arithmetic=dict(pipeline_seconds=4730, refit_resamples=50, pipeline_hours=pipeline_h,
                    original_plus_50_refits_hours=51*pipeline_h,
                    instance_hours_18=18*51*pipeline_h,
                    estimated_rate_basis_usd_h=rate, rate_is_current_verified_tariff=False,
                    forecast_at_stated_quarter_rate=18*51*pipeline_h*rate/4,
                    forecast_at_stated_full_rate=18*51*pipeline_h*rate,
                    max_18x72_at_quarter_rate=18*72*rate/4,
                    max_18x72_at_full_rate=18*72*rate,
                    row_cap_usd=250, max_effective_rate_to_fit_18x72=250/(18*72),
                    expected_count_per_setting=20, max_binomial_mcse_per_setting=(.25/20)**.5,
                    binomial_mcse_at_coverage_09=(.9*.1/20)**.5))
out = ROOT / 'reviews/2026-09-17_refit_aws_codex_checks.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('probe_csv', 'source_sha256')}, indent=2))
print(json.dumps({'probe_completed': len(rows), 'counts_by_setting': counts,
                  'checkpoint_files': len(checkpoints),
                  'complete_50_resample_files': sum(c['unique_completed_indices'] == 50 for c in checkpoints),
                  'incomplete_checkpoint_counts': [c['unique_completed_indices'] for c in checkpoints if c['unique_completed_indices'] < 50],
                  'runtime': sorted({r['runtime'] for r in identities}),
                  'code_hash': sorted({r['code_hash'] for r in identities}),
                  'evidence_file': str(out)}, indent=2))

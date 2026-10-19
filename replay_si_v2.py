"""Re-run the saved-row analyses and figure scripts of research snapshot 2.0.0 without fitting, and report.

The replay script reruns the saved-row analyses and figure scripts without fitting. Its report identifies the
archived outputs reproduced at the stated comparison precision, the disclosed omega-2 input-file-list exception,
and outputs generated without an archived comparison.

Every task reads only files inside this snapshot. Nothing is fitted or simulated, but the scripts do arithmetic
on saved rows: bootstraps and seeded latent-draw regeneration. The snapshot is copied to a temporary directory
first, so the archived files are never written. Four archived scripts name the author's machine directories; in
the temporary copy only, that one constant is replaced by the snapshot path. Printed output that contains an
absolute path is compared after mapping the temporary root back to the author's repository root, which is how
the archived text was recorded.

COMPARISON PRECISION, per check (recorded in the report):
  file-bytes        the regenerated file is byte-identical to the archived file. For a text table this means
                    every value is equal at the precision written to the file.
  stdout-text       the printed output, after the path mapping above, is byte-identical to the archived output
                    text: equality at the printed precision.
  json-except-keys  the regenerated JSON equals the archived JSON after removing the named keys. Used once, for
                    omega2_target_check.json, whose 'd4v12b_files' lists the row files read: the run read 160
                    shard files, the snapshot holds the same rows merged. This is not raw byte identity.
Outputs generated WITHOUT an archived comparison are listed per task under 'generated_not_compared' (every figure
PDF, the sensitivity-interval script's printed intervals, the refit-probe script's printed diagnostics, and the
refit-control script's two plots, which are not archived). A figure PDF is required to exist and to be a PDF; that shows it was generated,
not that it equals the archived figure.

THIS IS A GATE. The exit status is 0 only when every task in REQUIRED ran with return code 0, every compared
output exists and matches, and every required figure PDF was regenerated. A missing module, a missing output, a
zero-task or unknown --only selection all fail. --only runs a diagnostic subset: its report says verified=false
and it exits 3 even when the subset passes.

Usage (from the snapshot root):
    python replay_si_v2.py --out replay-report [--plot-python /path/to/python]
--plot-python is the interpreter for the tasks that need matplotlib (the refit-control analysis and the five
figures); the default is the interpreter running this script. The other tasks need numpy, scipy and pandas, and
concept_scale_link.py needs jax 0.11 (workspace_demo/t1_access/requirements.txt).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
ORIGINAL_ROOT = '/Users/pietervanrooyen/Recoverable-Self-Coding'
T1 = 'workspace_demo/t1_access'
BANK_DIR = f'{T1}/sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15'
BANK_CSV = f'{T1}/reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv'
# The human figure script reads the port's figure tables from the author's checkout (as in replay_figures.py).
HUMAN_INPUT = 'os.path.expanduser("~/Recoverable-Self-Coding/workspace_demo/sergent_port/figures")'
D4_SHARDS = '"sim_results/d4v12b/calibration_D4.shard*.csv"'
OMEGA2_JSON = f'{T1}/reviews/t1_omega2_bank_2026-09-15/omega2_target_check.json'

# name, script, {constant line prefix: replacement}, compared files, archived stdout file or None,
# needs the plotting interpreter, outputs generated without an archived comparison
TASKS = [
    ('reference bank summary', f'{T1}/reviews/t1_omega2_bank_2026-09-15/bank_omega2.py',
     {'D = ': BANK_DIR}, [], f'{T1}/reviews/t1_omega2_bank_2026-09-15/bank_omega2.output.txt', False, []),
    ('reference bank tail', f'{T1}/reviews/t1_omega2_bank_2026-09-15/bank_tail.py',
     {'D = ': BANK_DIR}, [], f'{T1}/reviews/t1_omega2_bank_2026-09-15/bank_tail.output.txt', False, []),
    ('omega-2 target check and figure data', f'{T1}/reviews/t1_omega2_bank_2026-09-15/omega2_target_check.py',
     # It globbed the run's 160 shard files; the snapshot holds the same rows merged (calibration_D4.csv).
     {D4_SHARDS: f'{T1}/sim_results/d4v12b/calibration_D4.csv'}, [OMEGA2_JSON, BANK_CSV], None, False, []),
    ('inherited-pair sensitivity', f'{T1}/reviews/t1_historical_pair_2026-09-16/historical_pair_sensitivity.py',
     {}, [f'{T1}/reviews/t1_historical_pair_2026-09-16/historical_pair_counts.csv'],
     f'{T1}/reviews/t1_historical_pair_2026-09-16/historical_pair_sensitivity.output.txt', False, []),
    ('reference-inclusion rates', f'{T1}/reviews/t1_historical_pair_2026-09-16/reference_inclusion_check.py',
     {'BANK = ': BANK_CSV}, [], f'{T1}/reviews/t1_historical_pair_2026-09-16/reference_inclusion_check.output.txt',
     False, []),
    ('saved-row diagnostics', f'{T1}/reviews/t1_saved_row_diagnostics_2026-10-15/saved_row_diagnostics.py',
     {}, [f'{T1}/reviews/t1_saved_row_diagnostics_2026-10-15/saved_row_diagnostics.output.txt'], None, False, []),
    ('concept-scale link', f'{T1}/reviews/t1_saved_row_diagnostics_2026-10-15/concept_scale_link.py',
     {}, [f'{T1}/reviews/t1_saved_row_diagnostics_2026-10-15/concept_scale_link.output.txt'], None, False, []),
    ('reshaping screen', f'{T1}/reviews/t1_reshaping_screen_2026-10-14/reshaping_screen.py',
     {}, [f'{T1}/reviews/t1_reshaping_screen_2026-10-14/reshaping_screen.output.txt'], None, False, []),
    ('refitting-resample timing', f'{T1}/reviews/t1_refit_timing_2026-10-14/refit_timing.py',
     {}, [f'{T1}/reviews/t1_refit_timing_2026-10-14/refit_timing.output.txt'], None, False, []),
    ('refit control analysis', f'{T1}/reviews/2026-09-16_refit_control_analysis.py',
     {'SIM = ': f'{T1}/sim_results'},
     [f'{T1}/sim_results/refit_control_aac9f69/refit_control_summary.json',
      f'{T1}/sim_results/refit_control_aac9f69/refit_control_paired.csv'], None, True,
     [f'{T1}/sim_results/refit_control_aac9f69/refit_control_intervals.pdf and .png (plots; not archived)',
      'printed summary (not compared; the summary JSON file is)']),
    ('refit probe analysis', f'{T1}/reviews/2026-09-19_refit_probe_analysis.py',
     {}, [f'{T1}/reviews/2026-09-19_refit_probe_figure_data.csv'], None, False,
     ['printed coverage, interval and width diagnostics']),
    ('sensitivity-study intervals', f'{T1}/reviews/2026-09-17_sens600_blinded_intervals.py', {}, [], None, False,
     ['printed blinded intervals (no archived output file of this script)']),
    ('figure human_bms', 'paper-si/figures/fig_human_bms.py',
     {HUMAN_INPUT: 'workspace_demo/sergent_port/figures'}, ['paper-si/figures/human_bms_data.csv'], None, True, []),
] + [(f'figure {n}', f'paper-si/figures/fig_{n}.py', {}, [], None, True, []) for n in
     ['t1_calibration', 't1_omega2_target', 't1_assay', 't1_transfer']]
REQUIRED = [t[0] for t in TASKS]
# Keys that record which input files were read, compared separately: the snapshot holds merged rows.
JSON_INPUT_LISTS = {OMEGA2_JSON: ['d4v12b_files']}
FIGURE_PDFS = {'fig_human_bms.py': 'human_bms.pdf', 'fig_t1_calibration.py': 't1_calibration_D4.pdf',
               'fig_t1_omega2_target.py': 't1_omega2_target.pdf', 'fig_t1_assay.py': 't1_assay.pdf',
               'fig_t1_transfer.py': 't1_transfer.pdf'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch(script, constants, work):
    """Point each machine-specific input at the snapshot copy: a constant line or one exact expression."""
    for key, rel in constants.items():
        text = script.read_text()
        if key.endswith(' = '):
            lines = text.splitlines(keepends=True)
            hits = [i for i, line in enumerate(lines) if line.startswith(key)]
            assert len(hits) == 1, (script, key, hits)
            lines[hits[0]] = f'{key}{json.dumps(str(work / rel))}\n'
            text = ''.join(lines)
        else:
            assert text.count(key) == 1, (script, key)
            text = text.replace(key, json.dumps(str(work / rel)))
        script.write_text(text)


def compare_file(o, work):
    """Return a check record for one compared output file."""
    path = work / o
    if not path.exists():
        return dict(output=o, precision='file-bytes', match=False, reason='not regenerated')
    new, old = path.read_bytes(), (ROOT / o).read_bytes()
    if new == old:
        return dict(output=o, precision='file-bytes', match=True, sha256=digest(new))
    if o in JSON_INPUT_LISTS:
        a, b = json.loads(new), json.loads(old)
        removed = JSON_INPUT_LISTS[o]
        for key in removed:
            a.pop(key, None), b.pop(key, None)
        return dict(output=o, precision='json-except-keys', excluded_keys=removed, match=a == b,
                    exception=('omega-2 input-file-list exception: identical except the list of row files read '
                               '(the run read 160 shard files; the snapshot holds the same rows merged)'))
    return dict(output=o, precision='file-bytes', match=False, reason='bytes differ')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--only', nargs='*', help='diagnostic subset of task names; never a verification')
    parser.add_argument('--plot-python', default=sys.executable)
    args = parser.parse_args()
    if args.only is not None:
        unknown = sorted(set(args.only) - set(REQUIRED))
        if unknown or not args.only:
            print(f'FAIL: --only selects no task or names unknown tasks {unknown}; tasks are {REQUIRED}')
            sys.exit(2)
    selected = [t for t in TASKS if args.only is None or t[0] in args.only]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp).resolve() / 'snapshot'
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns('__pycache__'))
        for name, rel, constants, outputs, stdout_file, plot, not_compared in selected:
            script = work / rel
            original_script = script.read_bytes()
            patch(script, constants, work)
            pdf = FIGURE_PDFS.get(script.name)
            pdf_rel = str(Path(rel).parent / pdf) if pdf else None
            regenerated_files = list(outputs) + ([pdf_rel] if pdf else [])
            for o in regenerated_files:
                (work / o).unlink()
            python = args.plot_python if plot else sys.executable
            env = dict(os.environ, NPROC='1', MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1')
            proc = subprocess.run([python, script.name], cwd=script.parent, env=env, capture_output=True,
                                  timeout=3600)
            err = proc.stderr.decode(errors='replace')
            entry = dict(task=name, script=rel, interpreter=python, returncode=proc.returncode, checks=[],
                         generated_not_compared=list(not_compared))
            problems = []
            if proc.returncode != 0:
                problems.append('interpreter lacks a module' if 'ModuleNotFoundError' in err else 'script failed')
                entry['stderr_tail'] = err[-600:]
            else:
                for o in outputs:
                    entry['checks'].append(compare_file(o, work))
                if stdout_file:
                    text = proc.stdout.decode()
                    for form in sorted({str(work), str(work).replace('/private/', '/', 1)}, key=len, reverse=True):
                        text = text.replace(form, ORIGINAL_ROOT)
                    entry['checks'].append(dict(output=stdout_file, precision='stdout-text',
                                                match=text.encode() == (ROOT / stdout_file).read_bytes()))
                problems += [f"{c['output']}: {c.get('reason', 'differs')}" for c in entry['checks'] if not c['match']]
                if pdf:
                    regenerated = work / pdf_rel
                    ok = regenerated.exists() and regenerated.read_bytes()[:5] == b'%PDF-'
                    entry['figure'] = dict(pdf=pdf_rel, regenerated=ok, compared=False)
                    entry['generated_not_compared'].append(f'{pdf_rel} (figure PDF; regenerated, not compared)')
                    if ok:
                        shutil.copyfile(regenerated, out / pdf)
                    else:
                        problems.append(f'{pdf_rel} not regenerated')
                (out / (Path(rel).stem + '.stdout.txt')).write_bytes(proc.stdout)
            if problems:
                entry['status'] = 'FAILED'
                entry['problems'] = problems
            elif entry['checks']:
                entry['status'] = 'reproduced'
            else:
                entry['status'] = 'generated, no archived comparison'
            results.append(entry)
            # Restore the archived bytes, so that every later task reads the snapshot exactly as published.
            script.write_bytes(original_script)
            for o in regenerated_files:
                shutil.copyfile(ROOT / o, work / o)
    ran = [r['task'] for r in results]
    failed = [r['task'] for r in results if r['status'] == 'FAILED']
    complete = ran == REQUIRED
    summary = dict(
        required_tasks=len(REQUIRED), tasks_run=len(ran), complete=complete, failed=failed,
        verified=complete and not failed,
        reproduced=[dict(task=r['task'], output=c['output'], precision=c['precision'])
                    for r in results for c in r['checks'] if c['match']],
        exceptions=[dict(task=r['task'], output=c['output'], note=c['exception'])
                    for r in results for c in r['checks'] if c.get('exception') and c['match']],
        generated_not_compared=[dict(task=r['task'], output=g) for r in results for g in r['generated_not_compared']])
    report = dict(python=sys.version.split()[0], executable=sys.executable, plot_python=args.plot_python,
                  summary=summary, results=results)
    (out / 'replay_report.json').write_text(json.dumps(report, indent=2) + '\n')
    for r in results:
        print(f"{r['status']:<36} {r['task']}")
    print(f"tasks {len(ran)}/{len(REQUIRED)}; reproduced outputs {len(summary['reproduced'])}; "
          f"exceptions {len(summary['exceptions'])}; generated without comparison {len(summary['generated_not_compared'])}")
    if failed:
        print(f'FAIL: {failed}')
        sys.exit(1)
    if not complete:
        print('PARTIAL: a diagnostic subset ran; this is not a verification of the snapshot')
        sys.exit(3)
    print('VERIFIED: every required task ran and every compared output matched at its stated precision')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Scoped review of v5: arithmetic and temporary contract fixtures, no stage C.

Runs the new inclusion suite (its decoder/fitter are stubbed), and the battery's
contract checks only. Independently integrates the G2 latent-ranking probability,
checks the complete CLI summary with constructed results, and exposes the exact
scope of the readout diagnostic and namespace dependency checks. No production
edits, real EEG, decoder fit, density fit, cloud call or live-result write.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'NPROC')
os.environ.update({k: '1' for k in THREADS})
HERE = Path(__file__).resolve().parent
PORT = HERE.parents[1] / 'melcon_port'
sys.path.insert(0, str(PORT))


def no_eeg(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)) and os.fsdecode(args[0]).lower().endswith('.bdf'):
        raise RuntimeError('Review refuses BDF access')


sys.addaudithook(no_eeg)
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import cumulative_trapezoid, quad
from scipy.signal import fftconvolve
from scipy.special import expit, ndtr
from scipy.stats import skewnorm
import sklearn
import battery as BT
import decoder as DEC
import likelihood as LK
import synthetic as SY
import test_battery as TB
import test_inclusion as TI


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probability_checks():
    # Raw skew-normal means cancel in the independent difference. Only its SD
    # rescales the desired difference threshold in standardized-noise units.
    shape = SY.SKEW_SHAPE
    delta = shape / np.sqrt(1 + shape * shape)
    mean = delta * np.sqrt(2 / np.pi)
    sd = np.sqrt(1 - 2 * delta * delta / np.pi)
    shifts = np.array([0., .1, .3, .4, 1., 1.3, 1.8, 2.3])
    actual = SY.present_latent_auc('G2', shifts / 2, np.zeros(len(shifts)))
    truth, errs = [], []
    for shift in shifts:
        val, err = quad(lambda u: 2 * np.exp(-u*u/2) / np.sqrt(2*np.pi) * ndtr(shape*u)
                        * skewnorm.cdf(u + sd * shift, shape), -12, 12, epsabs=1e-12, epsrel=1e-12)
        truth.append(val)
        errs.append(err)
    assert abs(truth[0] - .5) < 1e-12
    assert actual[0] - .5 > 1e-4

    # Separate fine-grid trapezoid reference, checked against adaptive quadrature.
    step = .0005
    e = np.arange(-10., 10. + step/2, step)
    f = sd * skewnorm.pdf(mean + sd*e, shape)
    pdf = fftconvolve(f, f[::-1]) * step
    grid = 2 * e[0] + step * np.arange(len(pdf))
    cdf = cumulative_trapezoid(pdf, dx=step, initial=0.)
    fine = np.interp(shifts, grid, cdf)
    assert np.max(np.abs(fine - truth)) < 1e-7

    subjects = BT.templates()[:BT.N_CAL]
    limits = {}
    for g in SY.GENERATORS:
        limit = BT.population_calibration_auc(g, subjects)
        limits[g] = dict(production_limit=limit,
                         targets={st: .5 + q*(limit - .5) for st, q in BT.HEADROOM.items()})
    for g, value in {'X1': .7438555563939797, 'X2': .6475829768892323}.items():
        assert abs(limits[g]['production_limit'] - value) < 1e-12
    per = []
    for subject in subjects:
        t = SY.template(subject, 'nocue')
        t = t[~t['catch']]
        logc = np.log(t.contrast.to_numpy(float))
        L = expit(SY.DOSE_SLOPE * (logc - logc.mean()) / logc.std(ddof=1))
        shift = 2*L + SY.HEMI_SHIFT*(t.side.to_numpy() == 'right')
        auc = np.interp(shift, grid, cdf)
        per.append(np.mean([auc[t.block.isin(h)].mean() for h in DEC.HALVES]))
    corrected = float(np.median(per))
    limits['G2']['fine_grid_limit'] = corrected
    limits['G2']['fine_grid_targets'] = {st: .5 + q*(corrected - .5) for st, q in BT.HEADROOM.items()}
    return dict(shifts=shifts.tolist(), production=actual.tolist(), adaptive_quadrature=truth,
                quadrature_error_estimates=errs, production_minus_reference=(actual-truth).tolist(),
                fine_grid_max_error_on_reference_nodes=float(np.max(np.abs(fine-truth))), limits=limits)


def summary_diagnostic():
    # Two blocks per half; high-state labels differ in prevalence by block.
    # Within each block both label groups have identical balanced noise, and y
    # contains only the block shift, with NO state effect. This is a summary
    # fixture, not fitted data from an X1 pipeline run.
    halves = {}
    folds = {}
    th = np.zeros(len(LK.PARAMS['twostate']))
    idx = {name: i for i, name in enumerate(LK.PARAMS['twostate'])}
    th[idx['delta0']], th[idx['delta1']] = np.log(.1), np.log(1.8)
    for hi, half in enumerate(DEC.HALVES):
        block = np.repeat(half, 32)
        high = np.concatenate((np.arange(32) < 8, np.arange(32) < 24))
        noise = np.tile([-1., 1.], 32)
        y = SY.DRIFT_PER_BLOCK*(block - block.min()) + noise
        t = pd.DataFrame(dict(block=block, catch=False, contrast=1., side='left', high_true=high, z_true=y))
        halves[half] = dict(trials=t, W=np.tile(y[:, None], (1, 40)))
        for fi in range(2):
            folds[(hi, fi, 25)] = {'twostate': dict(available=True, theta=th, scaling=dict(m=0., s=1.))}
    res = dict(status='ok', subject=1, task='nocue', windows=list(range(40)), models=list(LK.PRIMARY),
               evidence=np.zeros((40, 3)), available=np.ones((40, 3), bool), delta=np.zeros(40),
               n_trials=np.full(40, 128), auc=np.full((40, 2), .7), folds=folds, decoder={'halves': halves})
    got = BT.summary(res)
    assert abs(got['twostate_min_gap_median'] - .1) < 1e-12
    assert abs(got['twostate_full_gap_median'] - 1.) < 1e-12
    assert got['readout_component_separation_median'] > .1
    return dict(fitted_minimum_gap=got['twostate_min_gap_median'], fitted_full_gap=got['twostate_full_gap_median'],
                constructed_conditional_state_effect=0., unadjusted_readout_separation=got['readout_component_separation_median'],
                note='Constructed input: high/low prevalence differs by block; within-block state effect is zero.')


def cli_summary_fixture():
    key = 'X1|strong|False'
    with tempfile.TemporaryDirectory(prefix='codex-melcon-v5-summary-') as td, \
         patch.object(BT, 'OUT_DIR', td), patch.object(BT, 'templates', return_value=[1]):
        identity = BT.config_identity()
        ident = BT.digest(identity)
        run_dir = BT.run_directory(identity)
        entry = dict(generator='X1', strength='strong', amplitude=.8, target=.719,
                     check=.719, accepted=True)
        BT.save_calibration(run_dir, entry)

        def save_result(rep):
            path = BT.cell_path(run_dir, 'X1', 1, 0, rep, 1)
            manifest = BT.recording_manifest(ident, 'X1', 1, 0, rep, 1, entry)
            with open(path, 'wb') as f:
                np.save(f, np.array([dict(status='ok', subject=1, task='nocue', windows=list(range(40)),
                                         manifest=manifest)], dtype=object), allow_pickle=True)

        def summarize():
            with patch.object(BT.G, 'decide', return_value=dict(outcome='two-state')), \
                 patch.object(sys, 'argv', ['battery.py', '--summarize', '--generators', 'X1']), \
                 contextlib.redirect_stdout(io.StringIO()):
                BT.main()
            return json.loads((Path(run_dir) / 'verdicts.json').read_text())

        save_result(0)
        save_result(1)
        partial = summarize()
        assert partial[key]['verdict'] == 'incomplete'
        save_result(2)
        complete = summarize()
        assert complete[key]['verdict'] == 'pass'
        assert len(complete) == 4
        assert all(v['verdict'] == 'incomplete' for k, v in complete.items() if k != key)
    unusable = {('X1', 'strong'): False}
    precedence = BT.cell_verdicts({('X1', 'strong', 0): ['two-state']*2,
                                  ('X1', 'strong', 1): ['two-state']*3}, unusable)
    assert precedence[('X1', 'strong', 0)] == 'incomplete'
    assert precedence[('X1', 'strong', 1)] == 'diagnostic: calibration not usable'
    return dict(partial=partial, complete=complete, precedence={str(k): v for k, v in precedence.items()})


def provenance_checks():
    identity = BT.config_identity()
    bms_path = Path(BT.G.BMS.__file__).resolve()
    original = BT._sha_file
    with patch.object(BT, '_sha_file', side_effect=lambda p: '0'*64 if Path(p).resolve() == bms_path else original(p)):
        altered_dependency = BT.config_identity()
    assert BT.digest(identity) == BT.digest(altered_dependency)
    manifest_path = PORT / 'results/battery/v5-7fcb46729408/manifest.json'
    live_matches = json.loads(manifest_path.read_text()) == json.loads(json.dumps(identity, default=str))
    with tempfile.TemporaryDirectory(prefix='codex-melcon-v5-payload-') as td:
        p = Path(td) / 'recording.npy'
        manifest = {'fixture': True}
        # The manifest comparison accepts a modified readable payload; it is
        # identity checking, not content authentication or a schema check.
        result = dict(manifest=manifest, status='ok', arbitrary_payload=999)
        with p.open('wb') as f:
            np.save(f, np.array([result], dtype=object), allow_pickle=True)
        accepted = BT.load_verified(str(p), manifest)
    return dict(namespace='v5-' + BT.digest(identity)[:12], live_manifest_matches=live_matches,
                bms_path=str(bms_path), bms_sha256=sha(bms_path),
                bms_hash_change_changes_identity=BT.digest(identity) != BT.digest(altered_dependency),
                manifest_matching_payload_is_not_schema_or_checksum_checked=accepted == result,
                runtime_versions=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__),
                numerical_versions_present_in_identity=any(k in identity for k in ('environment', 'versions', 'runtime')))


def main():
    result = dict(scope='Scoped v5 arithmetic and temporary contract fixtures; no model fits or stage C.',
                  thread_environment={k: os.environ[k] for k in THREADS},
                  source_sha256={f: sha(PORT / f) for f in (*BT.CODE_FILES, 'test_battery.py', 'test_inclusion.py',
                                                        'PREREG_secondary_melcon.md', 'results/trials_all.csv')})
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        TI.main()
        TB.check_verdicts()
        TB.check_calibration_history()
        TB.check_provenance([1])
    result['existing_scoped_tests'] = dict(passed=True, stdout=stdout.getvalue(),
                                         tests=['test_inclusion.main', 'test_battery.check_verdicts',
                                                'test_battery.check_calibration_history', 'test_battery.check_provenance'])
    result['probabilities'] = probability_checks()
    result['summary_diagnostic'] = summary_diagnostic()
    result['cli_summary'] = cli_summary_fixture()
    result['provenance'] = provenance_checks()
    out = HERE / '2026-09-14_melcon_v5_scoped_checks.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_sha256', 'existing_scoped_tests')}, indent=2))
    print('Saved:', out)


def concurrent_store_check():
    import fcntl
    with tempfile.TemporaryDirectory(prefix='codex-v5-lock-') as td:
        lock_path = Path(td) / 'calibration.json.lock'
        with lock_path.open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            children = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--save-fixture', td, g],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        for g in ('G1', 'X1')]
            for child in children:
                assert child.stdout.readline().strip() == 'READY'
            fcntl.flock(lock, fcntl.LOCK_UN)
            for child in children:
                stdout, stderr = child.communicate(timeout=30)
                assert child.returncode == 0, (stdout, stderr)
        entries = BT.load_calibration(td)
        assert set(entries) == {('G1', 'weak'), ('X1', 'weak')}
    out = HERE / '2026-09-14_melcon_v5_scoped_checks.json'
    result = json.loads(out.read_text())
    result['concurrent_calibration_store'] = dict(two_waiting_writers=True, both_entries_retained=True,
                                                duplicate_replacement_refused_by_existing_scoped_test=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['concurrent_calibration_store']))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--save-fixture':
        print('READY', flush=True)
        BT.save_calibration(sys.argv[2], dict(generator=sys.argv[3], strength='weak', amplitude=.8, accepted=True))
    elif len(sys.argv) > 1 and sys.argv[1] == '--lock-check':
        concurrent_store_check()
    else:
        main()

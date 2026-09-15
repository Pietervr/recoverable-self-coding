#!/usr/bin/env python3
"""Read-only audit of SAVED Phase 1 evidence; no generation, decoder, fit or C2 test score.

Only likelihood's algebraic loglik/bounds functions are called. All production inputs
are hashed before/after. Writes only the adjacent review JSON. Run with RSC .venv.
"""
import os

for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import collections
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MP = ROOT / 'workspace_demo/melcon_port'
sys.path.insert(0, str(MP))
import likelihood as LK


def forbidden(*args, **kwargs):
    raise AssertionError('Generation, fitting and production writes are outside this audit')


LK._run = LK.fit = LK.fold_scores = LK.minimize = forbidden
RUN = MP / 'results/devpanel_v7/run-5d74bc1d6a11'
HASHES = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    data = path.read_bytes()
    HASHES[str(path)] = sha(data)
    return data


def read_json(path):
    return json.loads(read(path))


def digest(obj):
    return sha(json.dumps(obj, sort_keys=True, default=str).encode())


def same(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape:
        return False
    if a.dtype.kind in 'fc' and b.dtype.kind in 'fc':
        return np.array_equal(a, b, equal_nan=True)
    return np.array_equal(a, b)


def load(path, key, ident, parent=None):
    data = read(path)
    side = read_json(Path(str(path) + '.sha256'))
    assert sha(data) == side['sha256'], path
    if parent is None:
        assert (side['key'], side['identity'], side['schema']) == (key, ident, 'melcon-devpanel-v7-phase1-r1')
    else:
        assert side['manifest'] == digest(parent)
        assert side['schema'] == 'melcon-battery-result-v6'
    out = np.load(io.BytesIO(data), allow_pickle=True)[0]
    if parent is None:
        assert (out['key'], out['identity']) == (key, ident)
    else:
        assert out['manifest'] == parent
    return out


def design(a):
    return dict(y=a['y'], x=a['x'], c=a['catch'], h=a['h'])


def inspect(out, bucket, counts, g1_truth):
    assert out['status'] == 'ok'
    summ = out['summary'] if bucket == 'panel' else out
    windows = list(summ['windows']) if bucket == 'panel' else [99]
    models = list(LK.PRIMARY)
    assert summ['models'] == models
    held = np.zeros((len(windows), 3))
    n = np.zeros(len(windows), dtype=int)
    fits = {(tuple(f['tags']), f['model']): f for f in out['fits']}
    assert len(fits) == len(out['fits']) == len(windows) * 12
    assert len(out['folds']) == len(windows) * 4
    for key, fr in sorted(out['folds'].items(), key=lambda kv: (kv[0][2], kv[0][3])):
        wi = windows.index(key[-1])
        sc = fr['scaling']
        dtr, dte = design(fr['train']), design(fr['test'])
        xp = dtr['x'][~dtr['c']]
        lo, hi = float(xp.min()), float(xp.max())
        assert (lo, hi) == (fr['dose_support']['train_present_min'], fr['dose_support']['train_present_max'])
        # Identity of the clamp on TRAINING ONLY. No candidate held-out evaluation.
        clipped = dict(dtr, x=np.where(dtr['c'], dtr['x'], np.clip(dtr['x'], lo, hi)))
        assert same(clipped['x'], dtr['x'])
        labels = np.where(dte['c'], 'catch', np.where(dte['x'] < lo, 'below', np.where(dte['x'] > hi, 'above', 'within')))
        assert same(labels, fr['dose_support']['test_label'])
        n[wi] += fr['n_test']
        for mi, m in enumerate(models):
            mr, f = fr['models'][m], fits[(key, m)]
            assert mr['available'] and f['available'] and mr['fit_logged']
            assert f['seed'] == [LK.SEED, *key, LK.MODEL_INDEX[m]]
            assert f['retry_seed'] == f['seed'] + [1]
            starts = f['starts']
            assert [s['order'] for s in starts] == list(range(len(starts)))
            assert len(starts) == f['n_starts'] == (16 if f['retry'] else 8)
            conv = [s for s in starts if s['converged']]
            assert len(conv) == f['n_converged']
            kept = max(conv, key=lambda s: s['loglik'])
            assert kept['order'] == f['kept_start']
            assert same(kept['theta'], mr['theta']) and kept['loglik'] == mr['loglik_train']
            assert f['n_at_best'] == sum(s['loglik'] >= kept['loglik'] - LK.BASIN_NAT for s in conv)
            assert f['n_exact_ties_at_best'] == sum(s['loglik'] == kept['loglik'] for s in conv)
            train_ll, grad = LK.loglik(m, mr['theta'], dtr, grad=True)
            clipped_ll, clipped_grad = LK.loglik(m, mr['theta'], clipped, grad=True)
            test_ll = LK.loglik(m, mr['theta'], dte)
            assert same(train_ll, mr['train_ll']) and float(train_ll.sum()) == mr['loglik_train']
            assert same(train_ll, clipped_ll) and same(grad, clipped_grad)
            assert same(test_ll, mr['test_ll']) and float(test_ll.sum()) == mr['heldout']
            assert np.all(np.isfinite(train_ll)) and np.all(np.isfinite(test_ll))
            held[wi, mi] += mr['heldout']
            counts['fits_replayed'] += 1
            counts['starts_selection_checked'] += len(starts)
            if m == 'null':
                continue
            group = 'ideal' if bucket == 'ideal' else ('panel_main' if 20 <= key[-1] <= 29 else 'panel_early')
            row = counts['families'][group][m]
            dll = test_ll - fr['models']['null']['test_ll']
            severe = float(dll.sum()) / fr['n_test'] < -1
            row['units'] += 1
            row['severe'] += int(severe)
            if severe:
                ext = (labels == 'below') | (labels == 'above')
                row['severe_extrapolated_loss'] += float(dll[ext].sum())
                row['severe_total_loss'] += float(dll.sum())
                row['severe_extrapolated_trials'] += int(ext.sum())
                row['severe_trials'] += len(dll)
            if m == 'graded':
                s0, r = map(float, mr['theta'][4:6])
                minimum, maximum = math.exp(s0 + min(0, r)) / sc['S'], math.exp(s0 + max(0, r)) / sc['S']
                row['min_sd_S'] = min(row['min_sd_S'], minimum)
                row['max_sd_S'] = max(row['max_sd_S'], maximum)
                row['below_floor'] += int(minimum < .05)
                row['above_ceiling'] += int(maximum > 5)
                row['above_ceiling_severe'] += int(maximum > 5 and severe)
                row['above_ceiling_nonpositive_r'] += int(maximum > 5 and r <= 0)
                row['r_lower_severe' if severe else 'r_lower_other'] += int(kept['normalized'][5] <= 1e-9)
        if bucket == 'ideal' and out['generator'] == 'G1' and out['drift_index'] == 0:
            truth = out['truth']
            pres = ~truth['catch'].to_numpy(bool)
            logc = np.log(truth['contrast'].to_numpy(float)[pres])
            m_all, s_all = float(logc.mean()), float(logc.std(ddof=1))
            th = np.array([0., 2., (m_all-sc['m'])/sc['s'], math.log(1.5*sc['s']/s_all), 0., 0., .3])
            b = LK.bounds('graded', sc)
            outside = [LK.PARAMS['graded'][i] for i in range(7) if not b[i, 0] <= th[i] <= b[i, 1]]
            g1_truth.append(dict(key=out['key'], tags=list(key), theta=th.tolist(), outside_bounds=outside,
                                 n_trials=len(truth), n_training=fr['n_train']))
    actual = held / 4
    assert same(actual if bucket == 'panel' else actual[0], summ['evidence'])
    assert same(n if bucket == 'panel' else n[0], summ['n_trials'])
    assert np.asarray(summ['available']).all()
    delta = (held[:, 2] - held[:, 1]) / n
    assert same(delta if bucket == 'panel' else delta[0], summ['delta'])


def main():
    began = time.monotonic()
    ident = read_json(RUN / 'identity.json')
    identity = digest(ident)
    assert identity == '5d74bc1d6a1147eec97694c31eee4bf0c891af18908955fc7beb2c2170a7d5bb'
    for f, expected in ident['modules'].items():
        assert sha(read(MP / f)) == expected
    assert sha(read(MP.parent / 'sergent_port/bms.py')) == ident['runtime']['bms_sha256']
    pm_path = MP / 'results/devpanel_v7/panel_manifest.json'
    pm = read_json(pm_path)
    assert sha(read(pm_path)) == ident['panel_manifest_sha256']
    parent = MP / 'results/battery' / pm['parent_namespace']
    parent_manifest = read_json(parent / 'manifest.json')
    assert digest(parent_manifest) == ident['parent_identity'] == pm['parent_identity']
    assert sha(read(parent / 'manifest.json')) == pm['parent_manifest_sha256']
    assert sha(read(parent / 'calibration.json')) == pm['parent_calibration_sha256']
    assert sha(read(MP / 'results/trials_all.csv')) == parent_manifest['events_table']
    summary = read_json(RUN / 'analysis/summary.json')
    read(MP / 'devpanel_analyze.py')
    read(MP / 'DEVPLAN_v7.md')
    read_json(RUN / 'benchmark.json')
    parity_report = read_json(RUN / 'parity_report.json')
    families = {}
    for group in ('panel_main', 'panel_early', 'ideal'):
        families[group] = {}
        for m in ('graded', 'twostate'):
            families[group][m] = dict(units=0, severe=0, severe_extrapolated_loss=0., severe_total_loss=0.,
                                      severe_extrapolated_trials=0, severe_trials=0)
        families[group]['graded'].update(min_sd_S=math.inf, max_sd_S=0., below_floor=0, above_ceiling=0,
                                         above_ceiling_severe=0, above_ceiling_nonpositive_r=0,
                                         r_lower_severe=0, r_lower_other=0)
    counts = dict(panel=0, ideal=0, fits_replayed=0, starts_selection_checked=0, families=families)
    g1_truth = []
    parity_keys = ('status', 'windows', 'models', 'evidence', 'available', 'delta', 'n_trials', 'auc',
                   'twostate_min_gap_median', 'twostate_full_gap_median', 'occupancy_abs_error_median',
                   'readout_highlow_contrast_unadjusted_median', 'readout_latent_corr_median')
    for entry in pm['panel']:
        key = f"{entry['generator']}_{entry['strength']}_d{entry['drift_index']}_r{entry['replicate']}_sub-{entry['subject']:02d}"
        o = load(RUN / 'panel' / (key + '.npy'), key, identity)
        path = MP / entry['path']
        p = load(path, None, None, parent=entry['parent_recording_manifest'])
        assert sha(read(Path(str(path) + '.sha256'))) == entry['parent_sidecar_file_sha256']
        assert o['entry'] == entry
        for k in parity_keys:
            assert k in p and k in o['summary'] and same(p[k], o['summary'][k]), (key, k)
        assert o['parity']['equal'] and not o['parity']['differing']
        inspect(o, 'panel', counts, g1_truth)
        counts['panel'] += 1
    preferred = collections.defaultdict(collections.Counter)
    for gi, g in enumerate(('G1', 'G2', 'G3', 'X1')):
        for drift in range(2):
            for subject in pm['templates']:
                key = f'{g}_d{drift}_sub-{subject:02d}'
                o = load(RUN / 'ideal' / (key + '.npy'), key, identity)
                assert o['data_tags'] == [9, gi, 0, drift, 0, subject]
                inspect(o, 'ideal', counts, g1_truth)
                preferred[f'{g}|d{drift}'][LK.PRIMARY[int(np.argmax(o['evidence']))]] += 1
                counts['ideal'] += 1
    assert counts['panel'] == parity_report['panel_parity_equal'] == 40
    assert counts['ideal'] == parity_report['ideal_present'] == 272
    for group, rows in families.items():
        saved = summary['ideal_all' if group == 'ideal' else group]
        for m, row in rows.items():
            assert row['units'] == saved[m]['units'] and row['severe'] == saved[m]['severe']
            row['extrapolated_loss_share'] = row['severe_extrapolated_loss'] / row['severe_total_loss']
            assert math.isclose(row['extrapolated_loss_share'], saved[m]['severe_loss_share']['extrapolated'], rel_tol=1e-12)
            if m == 'graded':
                assert row['r_lower_severe'] == saved[m]['q5_shifts']['r_at_lower_given_severe']['k']
                assert row['r_lower_other'] == saved[m]['q5_shifts']['r_at_lower_given_not']['k']
    for group, winners in preferred.items():
        assert dict(winners) == summary['ideal_recordings'][group]['preferred']
    for p, expected in HASHES.items():
        assert sha(Path(p).read_bytes()) == expected, ('input changed', p)
    outside = [r for r in g1_truth if r['outside_bounds']]
    report = dict(status='PASS', scope='saved Phase 1 audit; no fits, generated recordings, C2 held-out scores or group reruns',
                  source_head=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                  identity=identity, counts=counts, ideal_winners=dict(preferred),
                  g1_no_drift_true_parameters=dict(n_folds=len(g1_truth), outside_bounds=outside,
                      x0_range=[min(r['theta'][2] for r in g1_truth), max(r['theta'][2] for r in g1_truth)],
                      k_range=[min(math.exp(r['theta'][3]) for r in g1_truth), max(math.exp(r['theta'][3]) for r in g1_truth)]),
                  python=platform.python_version(), versions={k: importlib.metadata.version(k) for k in ('numpy', 'scipy', 'pandas')},
                  input_files_unchanged=len(HASHES), input_hashes=HASHES, audit_sha256=sha(Path(__file__).read_bytes()),
                  elapsed_s=time.monotonic()-began)
    path = Path(__file__).with_suffix('.json')
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'input_hashes'}, indent=2))


if __name__ == '__main__':
    main()

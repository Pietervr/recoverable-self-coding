#!/usr/bin/env python3
"""Deterministic review counterexamples. No EEG, production edits, or stage C.
Classifier/fitter calls in inclusion tests are stubs so only dispatch is tested.
"""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'NPROC'):
    os.environ[key] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[1] / 'melcon_port'
sys.path.insert(0, str(PORT))
import numpy as np
import pandas as pd
import battery as BT
import decoder as DEC
import group as G
import likelihood as LK
import synthetic as SY
import recording as RC
import mne
import preprocess as PP


def inclusion_cases():
    t = SY.template(1, 'nocue')
    t['retained'] = True
    t['has_epoch'] = True
    t['edge_trial'] = False
    t['epoch_index'] = np.arange(len(t))
    cases = {}
    t240 = t.copy()
    for b, rows in t240[t240.present].groupby('block'):
        t240.loc[rows.index[60:], 'retained'] = False
    cases['240_present'] = dict(trials=t240)
    t24 = t.copy()
    for b, rows in t24[t24['catch']].groupby('block'):
        t24.loc[rows.index[6:], 'retained'] = False
    cases['24_catch'] = dict(trials=t24)
    tb = t.copy()
    tb.loc[tb.index[(tb.block == 1) & tb['catch']][2:], 'retained'] = False
    cases['2_catch_block1'] = dict(trials=tb)
    tn = t.copy()
    tn.loc[tn.index[tn.present][0], 'contrast'] = -1
    cases['negative_contrast_present'] = dict(trials=tn)
    cases['preprocessor_excluded'] = dict(trials=t.copy(), excluded=True, exclude_reason='13 bad channels')
    calls = []
    def decoder(rec, **kwargs):
        rows = rec['trials'][rec['trials'].retained & rec['trials'].has_epoch]
        calls.append({'n_present': int(rows.present.sum()), 'n_catch': int(rows['catch'].sum()),
                      'n_nonpositive_present': int((rows.present & ~(rows.contrast > 0)).sum())})
        return dict(status='ok', halves={B: dict(trials=rows[rows.block.isin(B)].reset_index(drop=True),
                      W=np.zeros((int(rows.block.isin(B).sum()), 40)), auc=np.full(40, .7)) for B in DEC.HALVES})
    def fits(train, test, tags=(), models=LK.PRIMARY):
        return {m: dict(available=True, heldout=-float(len(test)), reason='') for m in models}
    out = {}
    with patch.object(DEC, 'split_half', side_effect=decoder), patch.object(LK, 'fold_scores', side_effect=fits):
        for name, rec in cases.items():
            result = RC.recording_scores(rec, 1, 'nocue', windows=(25,))
            assert result['status'] == 'ok'
            out[name] = {'status_with_stubbed_numerics': result['status'], 'decoder_received': calls[-1],
                         'n_test_trials': int(result['n_trials'][0])}
    return out


def battery_contracts():
    partial = BT.cell_verdicts({('G1', 0, 0): ['graded', 'graded'], ('X1', 1, 0): ['two-state', 'two-state']})
    assert all(v == 'pass' for v in partial.values())
    with tempfile.TemporaryDirectory(prefix='melcon-v4-review-') as td:
        path = Path(td)/'old.npy'
        path.write_bytes(b'old result with no authenticated identity')
        with patch.object(SY, 'generate', side_effect=AssertionError('must not generate')):
            returned = BT.run_recording('X1', 1, 0, 0, 1, 999., str(path))
        assert returned == str(path)
        cal = [dict(generator='X1', target=s, amplitude=.7, check=.65, accepted=False) for s in BT.STRENGTHS]
        (Path(td)/'calibration.json').write_text(json.dumps(cal))
        calls = []
        with patch.object(BT, 'OUT_DIR', td), patch.object(BT, 'templates', return_value=[1]), \
             patch.object(BT, 'run_recording', side_effect=lambda *a: calls.append(a)), \
             patch.object(sys, 'argv', ['battery.py', '--run', '--generators', 'X1']):
            BT.main()
        assert len(calls) == 12
    # A fully deterministic calibration miss: no epochs. Local refinement is used
    # but omitted from the returned grid, which prevents reproducing interpolation.
    def draw(g, amp, draw_i, ti, subjects):
        return amp
    with patch.object(BT, '_draw', side_effect=draw), patch.object(BT, 'calibration_statistic', return_value=.65):
        cal = BT.calibrate('X1', 1, [1], log=lambda _: None)
    assert cal['refined'] and not cal['accepted'] and cal['amplitude'] == 4.
    assert '4.0' not in cal['grid']
    return {'partial_two_replicates_can_pass': {str(k): v for k, v in partial.items()},
            'existing_recording_reused_with_amplitude_999': True, 'jobs_dispatched_from_rejected_calibration': len(calls),
            'refinement_not_saved_in_returned_grid': cal}


def summary_diagnostic():
    # Valid model parameters: minimum separation .1, full separation near 2 at x=0.
    th = np.array([0., 0., np.log(.1), np.log(3.8), 0., 0., 0., 0.])
    tr = pd.DataFrame(dict(block=[2], contrast=[1.], catch=[False], occupancy_true=[.5]))
    res = dict(status='ok', subject=1, task='nocue', decoder={'halves': {(1, 2): {'trials': tr}}},
               folds={(0, 0, 25): {'twostate': dict(available=True, theta=th, scaling=dict(m=0., s=1.))}})
    for k in ('windows', 'models', 'evidence', 'available', 'delta', 'n_trials', 'auc'):
        res[k] = []
    reported = BT.summary(res)['twostate_separation_median']
    total = (np.exp(th[2]) + .5*np.exp(th[3]))/np.exp(th[1])
    assert np.isclose(reported, .1) and np.isclose(total, 2.)
    d = dict(y=np.array([0., 0., 0.]), x=np.array([-2., 0., 2.]), c=np.zeros(3, bool), h=np.zeros(3))
    theta = [0., 0., 0., 0., 0., np.log(2.), 0.]
    ll = LK.loglik('graded', theta, d)
    assert len(np.unique(ll)) == 3  # a1=0, spread alone varies
    return {'reported_minimum_separation': reported, 'actual_separation_at_x0': total,
            'graded_zero_mean_range_spread_only_log_densities': ll.tolist(),
            'graded_global_sd_envelope_in_S_units': [.005, 50.]}


def task_counts():
    t = pd.read_csv(SY.TRIALS_CSV)
    nocue = set(BT.templates())
    informative = set(int(s) for s in t[t.task == 'informative'].subject.unique())
    assert len(nocue) == 34 and len(informative) == 35 and len(nocue & informative) == 33
    return {'nocue': len(nocue), 'informative': len(informative), 'paired_after_sub36_nocue_exclusion': len(nocue & informative)}


def temporal_edges():
    fs = 1024.
    output = {}
    for name, cfg, at in (('minimum_phase_near_segment_start', PP.CONFIG_CAUSAL, 2.),
                          ('zero_phase_composite_support', PP.CONFIG, 20.)):
        data = np.zeros((1, int(40*fs)))
        s = int(at*fs)
        data[0, s] = 1.
        raw = mne.io.RawArray(data, mne.create_info(['test'], fs, 'eeg'), verbose=False)
        PP.apply_filters(raw, cfg)
        y = raw.get_data()[0]
        far = np.abs(np.arange(len(y))-s) > PP.CONFIG['edge_s']*fs
        output[name] = {'impulse_time_s': at, 'max_output_before_impulse_fraction': float(np.max(np.abs(y[:s]))),
                        'max_output_beyond_4_125s_fraction': float(np.max(np.abs(y[far])))}
    assert output['minimum_phase_near_segment_start']['max_output_before_impulse_fraction'] > 1e-8
    assert output['zero_phase_composite_support']['max_output_beyond_4_125s_fraction'] > 1e-8
    return output


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = {'scope': 'deterministic contracts; decoder/fitter stubs explicitly identified; no epochs or fits',
              'inclusion': inclusion_cases(), 'battery': battery_contracts(), 'separation_and_graded': summary_diagnostic(),
              'task_counts': task_counts(), 'temporal_edge_counterexamples': temporal_edges(),
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PORT.glob('*.py'))}}
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_sha256'}, indent=2))

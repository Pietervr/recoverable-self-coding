"""Bounded review evidence for draft v3; no EEG, decoder or likelihood fits.

Uses MNE filter coefficients, the real cache writer fed artificial epochs,
public channel/event metadata, and explicit algebraic contract examples.
Run with the repo-root .venv/bin/python. Writes only its JSON companion;
the artificial cache is written in a temporary directory and removed.
This is not the proposed full-pipeline synthetic recovery battery.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import mne
import numpy as np
import pandas as pd
from scipy.special import expit, ndtr

MELCON = Path(__file__).resolve().parents[2] / 'melcon_port'
sys.path.insert(0, str(MELCON))
import common as C

spec = importlib.util.spec_from_file_location('review_melcon_v3_load', MELCON / 'load.py')
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)


def cache_contract():
    trials = pd.DataFrame(dict(trial=[1, 2, 3], code=[11, 31, 12],
        contrast=[.1, np.nan, .2], seen=[1., 0., 1.], present=[True, False, True],
        block=[1, 1, 1]))
    labels = ['A1', 'A2', 'VEOG1', 'VEOG2', 'HEOG1', 'HEOG2']
    fake = dict(X=np.zeros((3, 6, 769)), time=np.arange(769)/512-.5,
        labels=labels, fsample=512., trials=trials, n_dropped_edge=0,
        dropped_trials=[], drop_reasons=[], recording_s=30., status_check={},
        params=dict(lowpass=200., highpass=.4, notch=50.,
                    ch_types=['eeg', 'eeg', 'eog', 'eog', 'eog', 'eog']))
    with tempfile.TemporaryDirectory(prefix='r052-v3-cache-') as td, \
         patch.object(L, 'DERIVED_DIR', td), \
         patch.object(L, 'available', return_value=[(1, 'nocue')]), \
         patch.object(L, 'load_subject', return_value=fake), \
         patch.object(L, 'trial_table', return_value=trials), \
         patch.object(sys, 'argv', ['load.py', '--subjects', '1', '--tasks', 'nocue', '--cache']), \
         contextlib.redirect_stdout(io.StringIO()):
        L.main()
        with np.load(L.cache_path(1, 'nocue'), allow_pickle=False) as cache:
            keys = sorted(cache.files)
    assert not {'params', 'lowpass', 'ch_types'} & set(keys)
    return dict(actual_npz_keys=keys, input_had_filter_and_channel_metadata=True,
                cache_retains_that_metadata=False)


def filters_and_montage():
    filters = []
    for fs in (1024., 2048.):
        taps = mne.filter.create_filter(None, fs, .4, None, verbose=False)
        lag = (np.arange(len(taps)) - (len(taps)-1)/2)/fs
        tail = np.abs(taps[np.abs(lag) > 1])
        assert len(taps)/fs > 8 and tail.max() > 0
        filters.append(dict(native_hz=fs, taps=len(taps),
            first_to_last_tap_seconds=(len(taps)-1)/fs,
            one_sided_support_seconds=float(abs(lag).max()),
            absolute_tap_sum_beyond_one_second=float(tail.sum())))
    labels = C.read_channels(1, 'nocue').name.tolist()[:128]
    montage = mne.channels.make_standard_montage('biosemi128')
    missing = sorted(set(labels) - set(montage.ch_names))
    original_names = L.BDF_NAMES_144[:128]
    assert set(original_names) == set(montage.ch_names)
    assert missing
    # The position-preserving rename is available, unlike literal name matching.
    renamed = montage.copy()
    renamed.rename_channels(dict(zip(original_names, labels)))
    assert set(renamed.ch_names) == set(labels)
    gaps = []
    for subject, task in C.available('events'):
        if task not in ('nocue', 'informative'):
            continue
        table = C.trial_table(subject, task)
        for i in range(1, len(table)):
            if table.block.iloc[i] != table.block.iloc[i-1]:
                gaps.append(dict(subject=subject, task=task,
                    next_block=int(table.block.iloc[i]),
                    onset_gap_s=float(table.onset_pd.iloc[i]-table.onset_pd.iloc[i-1])))
    gaps.sort(key=lambda item: item['onset_gap_s'])
    taps = mne.filter.create_filter(None, 1024., .4, None, verbose=False)
    lag_samples = round(gaps[0]['onset_gap_s']*1024)
    coefficient = float(taps[len(taps)//2+lag_samples])
    assert coefficient != 0
    return dict(highpass=filters, channel_names_missing_from_literal_biosemi_montage=missing,
        original_bdf_name_to_tsv_rename_covers_all_128=True,
        boundary_gap_count=len(gaps), smallest_onset_gaps=gaps[:5],
        median_onset_gap_s=float(np.median([g['onset_gap_s'] for g in gaps])),
        highpass_coefficient_at_shortest_boundary_onset_gap=coefficient,
        boundary_note='Onset-to-onset gaps from metadata, not measured filter leakage or pause duration.')


def density_contract():
    x = np.linspace(-2, 2, 31)
    a0, gamma, a1, s0, s1 = -.4, .7, 1.2, -.2, .1
    main_mu = (a0+gamma) + a1*expit(x)
    sensitivity_mu = a0 + a1*expit(x) + gamma
    main_sd = np.exp(s0+s1*(main_mu-(a0+gamma)))
    sensitivity_sd = np.exp(s0+s1*(sensitivity_mu-gamma-a0))
    assert np.allclose(main_mu, sensitivity_mu, rtol=0, atol=1e-15)
    assert np.allclose(main_sd, sensitivity_sd, rtol=0, atol=1e-15)
    # With one training block, its gamma and the intercept occur only as their sum.
    # The held-out gamma is defined as that same single training gamma.
    mu_l, delta = -.8, .9
    assert np.allclose((mu_l+gamma)+delta*expit(x), mu_l+delta*expit(x)+gamma)
    # Draft v3 fixes exact catch cancellation, but its allowed separation can be tiny.
    min_sep, sigma = np.exp(-5.), 5.
    tv = abs(.8-.1)*(2*ndtr(min_sep/(2*sigma))-1)
    assert 0 < tv < .001
    catch_per_block = [10, 0, 10, 10]
    assert sum(catch_per_block) >= 25
    assert min(sum(catch_per_block[:2]), sum(catch_per_block[2:])) >= 10
    return dict(single_training_block_gamma_is_intercept_alias=True,
        equivalent_graded_max_mean_error=float(np.max(abs(main_mu-sensitivity_mu))),
        equivalent_graded_max_sd_error=float(np.max(abs(main_sd-sensitivity_sd))),
        catch_sensitivity=dict(S=1., separation=min_sep, sigma=sigma,
            pi_values=[.1, .8], total_variation_distance=float(tv),
            interpretation='Structurally distinct densities; practical information is not guaranteed.'),
        accepted_recording_with_empty_likelihood_catch=dict(catches_by_block=catch_per_block,
            present_trials=360, all_recording_and_half_class_floors_pass=True,
            likelihood_training_block_without_catch=2),
        invalid_moment_start_example=dict(top_quintile_mean=1., bottom_quintile_mean=2.,
            proposed_a1_or_exp_delta0=-1., needs_declared_clipping_or_fallback=True))


def run_flag(values, eligible):
    hits = (np.asarray(values) >= .95) & np.asarray(eligible)
    return bool(np.any(np.convolve(hits, np.ones(3, dtype=int), mode='valid') == 3))


def written_rule(eligible, mix, graded, median_auc, passed=35, hard_failures=0):
    if passed < 20 or hard_failures > passed/4:
        return 'technical failure'
    if np.all(np.asarray(median_auc) < .55):
        return 'insufficient sensitivity'
    rm, rg = run_flag(mix, eligible), run_flag(graded, eligible)
    return 'inconclusive/mixed' if rm == rg else ('two-state' if rm else 'graded')


def outcomes_and_battery():
    eligible = [True]*10
    mix, graded = [.96]*3+[.02]*7, [.02]*3+[.96]+[.02]*6
    fixed = written_rule(eligible, mix, graded, [.8]*10)
    assert fixed == 'two-state'
    missing = written_rule([False]*10, [np.nan]*10, [np.nan]*10, [.8]*10)
    assert missing == 'inconclusive/mixed'
    # Under §9's literal null criterion, unavailable/failed outputs are not two-state.
    failures = ['technical failure']*3
    literal_null_pass = sum(x == 'two-state' for x in failures) <= 1
    assert literal_null_pass
    return dict(opposing_isolated_window_now_classified=fixed,
        no_eligible_windows_despite_35_recordings_and_good_auc=missing,
        note='Exact prose translation, not an implemented outcome classifier.',
        battery_null_failure_counterexample=dict(outcomes=failures,
            literal_at_most_one_two_state_rule_passes=literal_null_pass),
        planned_battery_counts=dict(generators=5, signal_levels=2, drift_levels=2,
            replicates=3, recordings_per_replicate=20, total_recordings=1200,
            primary_samplewise_decoder_fits_at_769_samples=1200*2*769,
            primary_density_starts_at_40_windows=1200*4*40*3*8))


def main():
    out = dict(scope=__doc__, versions=dict(mne=mne.__version__, numpy=np.__version__),
        source_sha256={name: hashlib.sha256((MELCON/name).read_bytes()).hexdigest()
                       for name in ('PREREG_secondary_melcon.md', 'load.py', 'common.py')},
        cache=cache_contract(), preprocessing=filters_and_montage(),
        densities=density_contract(), outcomes=outcomes_and_battery())
    destination = Path(__file__).with_suffix('.json')
    destination.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()

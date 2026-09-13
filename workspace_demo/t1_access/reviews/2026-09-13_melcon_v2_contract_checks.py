"""Synthetic-only checks of Melcon v2. Run with the repo-root .venv/bin/python.

No BDF or neural observation is read, and no classifier or likelihood is fitted.
The real loader filtering/epoch path receives artificial RawArray data instead.
"""
import importlib.util
import json
import math
from pathlib import Path
import sys
import warnings
from unittest.mock import patch

import mne
import numpy as np
import pandas as pd
from scipy.signal import freqz

MELCON = Path(__file__).resolve().parents[2] / 'melcon_port'
sys.path.insert(0, str(MELCON))
spec = importlib.util.spec_from_file_location('review_melcon_load', MELCON / 'load.py')
L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)


def artificial_raw(sfreq):
    t = np.arange(0, 30, 1/sfreq)
    # A known signal with an out-of-target-band component; no EEG observations.
    signal = 1e-5*np.sin(2*np.pi*23*t) + 1e-4*np.sin(2*np.pi*300*t)
    data = np.stack([signal, -signal, signal, -signal, signal, -signal])
    raw = mne.io.RawArray(data, mne.create_info(
        ['A1','A2','VEOG1','VEOG2','HEOG1','HEOG2'], sfreq,
        ['eeg','eeg','eog','eog','eog','eog']), verbose=False)
    raw.info['temp'] = {'n_bdf_channels':6}
    return raw


def loader_check(sfreq):
    raw = artificial_raw(sfreq)
    table = pd.DataFrame({'onset_pd':[10.,15.,20.], 'code':[11,31,12], 'trial':[1,2,3]})
    with patch.object(L, 'raw_bdf', return_value=raw), \
         patch.object(L, 'compare_status_with_events_tsv', return_value={}), \
         patch.object(L, 'trial_table', return_value=table), \
         patch.object(L, 'snap_to_status', return_value=(np.array([10,15,20])*int(sfreq),np.zeros(3))), \
         warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        d = L.load_subject(1, 'nocue', verbose=False)
    taps = mne.filter.create_filter(None, sfreq, l_freq=None, h_freq=200., verbose=False)
    _, response = freqz(taps, worN=np.array([23.,250.,256.,300.]), fs=sfreq)
    assert d['X'].shape == (3,6,769) and d['fsample'] == 512
    assert d['params']['ch_types'] == ['eeg','eeg','eog','eog','eog','eog']
    return dict(raw_sfreq=sfreq, output_shape=list(d['X'].shape), output_fs=d['fsample'],
                ch_types=d['params']['ch_types'],
                runtime_warnings=[str(w.message) for w in caught if issubclass(w.category,RuntimeWarning)],
                response_db_at_23_250_256_300_hz=(20*np.log10(np.maximum(np.abs(response),1e-30))).tolist())


def normpdf(x, mu=0., sigma=1.):
    return math.exp(-0.5*((x-mu)/sigma)**2)/(sigma*math.sqrt(2*math.pi))


# Literal catch definition in v2: mu_high == mu_low and common sigma.
catch_densities = [(1-p)*normpdf(.7)+p*normpdf(.7) for p in (0.,.2,.8,1.)]
assert max(catch_densities)-min(catch_densities) < 1e-15

# Common pooled affine normalization cannot align three different decoder offsets.
inner_offsets = np.array([-2.,0.,2.])
pooled_sd = math.sqrt(1+np.var(inner_offsets))
normalized_group_means = inner_offsets/pooled_sd
normalized_group_sds = np.ones(3)/pooled_sd
assert np.ptp(normalized_group_means) > 2

# The written outcome table has a gap if an opposing isolated .95 window counts
# against a three-window win but does not itself meet the persistence rule.
mixture_pxp=np.array([.96,.96,.96,.02,.2,.2,.2,.2,.2,.2])
graded_pxp=np.array([.02,.02,.02,.96,.2,.2,.2,.2,.2,.2])
def persistent(x): return bool(np.any(np.convolve(x>=.95,np.ones(3,dtype=int),mode='valid')==3))
mix_run, graded_run = persistent(mixture_pxp), persistent(graded_pxp)
assert mix_run and not graded_run and np.any(graded_pxp>=.95)

result=dict(mne_version=mne.__version__, loader=[loader_check(1024.),loader_check(2048.)],
    catch_density_for_pi_0_02_08_1=catch_densities,
    pooled_zscore_counterexample=dict(inner_decoder_offsets=inner_offsets.tolist(),
        transformed_group_means=normalized_group_means.tolist(),
        transformed_group_sds=normalized_group_sds.tolist(), outer_decoder_mean=0.,
        explanation='Same pooled z score leaves between-decoder offsets; illustrative, not measured in EEG.'),
    outcome_counterexample=dict(mixture_three_window_run=mix_run,graded_three_window_run=graded_run,
        isolated_graded_threshold_window=True,
        explanation='Clarify whether any opposing window or a full opposing run blocks a family outcome.'),
    scope='Artificial signals and algebra only; not pipeline recovery or EEG outcome analysis.')
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

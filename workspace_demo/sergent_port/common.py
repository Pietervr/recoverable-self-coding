"""Shared constants, paths and loaders for the Sergent et al. 2021 port.

Sergent C. et al. (2021) "Bifurcation in brain dynamics reveals a signature of conscious
processing independent of report", Nat Commun 12:1149. Data + scripts: OSF aw3t5 (CC0).

The OSF datasets are numbered S1..S20; the OSF scripts name subjects by ORIGINAL recording
number (subjects_list = 01 02 03 05 06 07 08 09 11 12 13 14 15 17 19 20 22 23 24 25).
ORIG_NUMBER[i] gives the original number of dataset S(i+1).
"""
from __future__ import annotations

import os
import numpy as np
from scipy.io import loadmat

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.normpath(os.path.join(HERE, "..", "brain_data", "sergent2021"))
PREPROC_DIR = os.path.join(DATA_ROOT, "Bifurcation_OSF_PreprocessedData")
BEHAV_DIR = os.path.join(DATA_ROOT, "Bifurcation_OSF_BehaviouralData_ActiveSessions")
# derived outputs (npz per subject) live beside the data, which is gitignored (workspace_demo/brain_data/)
DERIVED_DIR = os.path.join(DATA_ROOT, "derived")
RESULTS_DIR = os.path.join(HERE, "results")
FIG_DIR = os.path.join(HERE, "figures")

SUBJECTS = list(range(1, 21))
ORIG_NUMBER = ["01", "02", "03", "05", "06", "07", "08", "09", "11", "12",
               "13", "14", "15", "17", "19", "20", "22", "23", "24", "25"]

FS = 500.0
N_TIMES = 1250
# trialinfo columns (SoundConsciousEEG_Params.m); 0-based here
COL_BLOCK, COL_SNR, COL_VOWEL, COL_EVAL, COL_RESPSIDE, COL_AUDIB = 0, 1, 2, 3, 4, 5
# original decoder keeps the first 63 of 64 channels (coi = range(63)); channel 64 is FT10 (the recording reference)
N_CHANNELS_USED = 63

# SNR level -> dB label. Levels are what the analysis uses; the dB label is only for plots.
# Per the data Readme, level 2.. = -13,-11,-9,-7,-5(,-3) dB for original subjects < 21, and the
# range is shifted (-11 ... -1 dB) for original subjects 22-25 (= datasets S17-S20) — the Readme
# itself says "not sure about 2". The paper describes -13..-5 dB for the active session.
SNR_DB_MAIN = {1: "noise", 2: "-13", 3: "-11", 4: "-9", 5: "-7", 6: "-5", 7: "-3"}


def mat_path(subject: int, session: str) -> str:
    sess = {"active": "Active", "passive": "Passive"}[session.lower()]
    return os.path.join(PREPROC_DIR, f"S{subject}_{sess}_data_ref.mat")


def load_subject(subject: int, session: str, channels: int | None = N_CHANNELS_USED):
    """Load one FieldTrip data_ref struct.

    Returns dict with X (n_trials, n_chan, n_times) float64, trialinfo (n_trials, 12) int,
    time (n_times,) s, labels (list of str), fsample.
    """
    m = loadmat(mat_path(subject, session), squeeze_me=True, struct_as_record=False)
    d = m["data_ref"]
    n_trial = len(d.trial)
    n_chan, n_time = d.trial[0].shape
    X = np.empty((n_trial, n_chan, n_time), dtype=np.float64)
    for i in range(n_trial):
        X[i] = d.trial[i]
    if channels is not None:
        X = X[:, :channels, :]
    trialinfo = np.asarray(d.trialinfo).astype(np.int64)
    t = d.time
    time = np.asarray(t[0] if (isinstance(t, np.ndarray) and t.dtype == object) else t, dtype=np.float64)
    labels = [str(x) for x in d.label]
    return dict(X=X, trialinfo=trialinfo, time=time, labels=labels[: X.shape[1]], fsample=float(d.fsample))


def derived_path(subject: int, session: str, tag: str = "") -> str:
    """tag: '' for the main run; e.g. '_lbfgs' for a sensitivity run of the decoder."""
    return os.path.join(DERIVED_DIR, f"S{subject}_{session.lower()}{tag}_preds.npz")


def load_preds(subject: int, session: str, tag: str = ""):
    z = np.load(derived_path(subject, session, tag), allow_pickle=False)
    return {k: z[k] for k in z.files}

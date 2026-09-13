#!/usr/bin/env python3
"""Load one subject × task of ds006171 (Melcón et al. 2024) into epochs of the shape the
sergent_port decoder consumes — X (n_trials, n_channels, n_times) float64 + a per-trial table —
with the photodiode timing correction of common.trial_table applied. NO decoding happens here.

Processing (each step is a D-list entry in README.md; defaults mirror the Sergent 2021 OSF
preprocessing, SoundConsciousEEG_PreProcessing.m, where the two paradigms allow it):
  1. read the BDF (BioSemi ActiveTwo, 144 channels, 1024 Hz), rename the channels by position from
     channels.tsv (A1..D32 -> 10-20 names, EXG1..4 -> VEOG1/2 HEOG1/2), keep the 128 scalp channels;
  2. high-pass 0.4 Hz (Sergent: FieldTrip hpfreq .4) — needed on BioSemi data, which has no hardware
     high-pass — and a 50 Hz notch (Sergent: dftfilter);
  3. an anti-alias low-pass at LOWPASS_HZ (200 Hz, zero-phase FIR, MNE defaults: transition band 50 Hz, so the
     stop band starts at 250 Hz, below the 256 Hz Nyquist of the 512 Hz target) applied to EVERY recording
     before decimation (13 Sept 2026, Codex: the four 2048 Hz files carry a 417 Hz acquisition corner, so
     decimating them by 4 without a digital low-pass aliased the 256–417 Hz band; the 1024 Hz files' 208 Hz
     corner was adequate, and the same digital filter is now applied to all so that every recording is
     processed identically). The recording's lowpass must be <= target Nyquist before decimation or the
     loader raises; no warning is suppressed;
  4. common average reference over the 128 scalp channels (Sergent: refchannel 'all'; the paper: CAR);
  5. epochs around the PHOTODIODE-corrected Gabor / catch onset, -0.5 .. +1.0 s, baseline -0.5 .. 0
     (Sergent: -0.5 .. 2 s, baseline -0.5 .. 0; the Melcón trial ends with the question display at
     +0.30 .. +0.40 s and the response at ~+0.8 s, so +1.0 s covers the whole trial); the photodiode
     snap happens on the raw at its native rate, before any decimation;
  6. decimate to 512 Hz (the paper's own rate; Sergent's data were 500 Hz): by 2 for the 1024 Hz
     files, by 4 for the four 2048 Hz files of sub-35 / sub-36 (README D13).
  The EOG channels (EXG1..4 -> VEOG1/2, HEOG1/2) are kept in X by default since 13 Sept 2026 so that the
  pre-registered artefact rule can use them; they receive the same filters and are NEVER decoder features
  (the decoder picks channel type 'eeg'). No ICA, no channel repair, no trial rejection here — those are
  pre-registration decisions.

CLI:
  python load.py --subjects 1-3 --verify        # per subject × task: epoch count == events-table trial
                                                # count, Status-channel events == events.tsv, writes
                                                # results/load_verification.csv  (no decoding)
  python load.py --subjects 1 --tasks nocue --cache   # write DERIVED_DIR/sub-01_task-nocue_epochs.npz
"""
from __future__ import annotations

import argparse
import os
import time as _time
import warnings

import numpy as np
import pandas as pd
import mne

from common import (DERIVED_DIR, EOG_NAMES, FS_RAW, N_EEG, PHOTODIODE, RESULTS_DIR, TASKS, available,
                    bids_path, parse_subjects, read_channels, read_events, sub_id, trial_table)

mne.set_log_level("WARNING")

TMIN, TMAX = -0.5, 1.0
BASELINE = (-0.5, 0.0)
HIGHPASS_HZ = 0.4
NOTCH_HZ = 50.0
LOWPASS_HZ = 200.0             # anti-alias low-pass before decimation, every recording (13 Sept 2026, see the docstring)
TARGET_FS = 512.0              # decimation factor = round(raw sfreq / 512): 2 for the 1024 Hz files, 4 for the
                               # 2048 Hz files of sub-35 and sub-36 (README D13; eeg.json says 1024 Hz for all)
SNAP_MS = 8.0                  # snap the tsv onset to the Status-channel 128 within this (tsv onsets: <= 5 ms rounding)
STATUS_TOL_MS = 6.0            # events.tsv row <-> Status event match tolerance


BDF_NAMES_144 = ([f"{g}{i}" for g in "ABCD" for i in range(1, 33)] + [f"EXG{i}" for i in range(1, 9)]
                 + ["GSR1", "GSR2", "Erg1", "Erg2", "Resp", "Plet", "Temp", "Status"])


def raw_bdf(subject: int, task: str, preload: bool = True) -> mne.io.BaseRaw:
    """The BDF with channels renamed from channels.tsv and typed (eeg / eog / misc / stim).

    channels.tsv (144 rows, identical in every file) lists the channels in the order of a 144-channel
    BioSemi BDF: A1..D32 (the 128 scalp electrodes, 10-20 names), EXG1..8, GSR1/2, Erg1/2, Resp, Plet,
    Temp, Status. Some recordings were saved in the 256-channel configuration (272 channels, A1..H32
    + the same 16 extras; E..H are all-zero, README D12): the mapping is therefore by BioSemi NAME,
    and channels outside the 144-name list are dropped.
    """
    raw = mne.io.read_raw_bdf(bids_path(subject, task, "eeg.bdf"), preload=preload, verbose=False)
    ch = read_channels(subject, task)
    if len(ch) != len(BDF_NAMES_144):
        raise RuntimeError(f"{sub_id(subject)} {task}: channels.tsv has {len(ch)} rows, expected 144")
    raw.info["temp"] = dict(n_bdf_channels=len(raw.ch_names))
    missing = [n for n in BDF_NAMES_144 if n not in raw.ch_names]
    if missing:
        raise RuntimeError(f"{sub_id(subject)} {task}: BDF lacks channels {missing}")
    extra = [n for n in raw.ch_names if n not in BDF_NAMES_144]
    if extra:
        raw.drop_channels(extra)
    raw.reorder_channels(BDF_NAMES_144)
    raw.rename_channels(dict(zip(BDF_NAMES_144, ch.name.tolist())))
    types = {}
    for i, name in enumerate(ch.name):
        if i < N_EEG:
            types[name] = "eeg"
        elif name in EOG_NAMES:
            types[name] = "eog"
        elif name == "Status":
            types[name] = "stim"
        else:
            types[name] = "misc"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # unit-change notices for the misc/stim channels
        raw.set_channel_types(types, verbose=False)
    return raw


def status_events(raw: mne.io.BaseRaw) -> np.ndarray:
    """All trigger events of the Status channel (sample, 0, code), codes masked to 8 bits."""
    return mne.find_events(raw, stim_channel="Status", mask=0xFF, mask_type="and", consecutive=True,
                           min_duration=0, shortest_event=1, verbose=False)


def snap_to_status(onsets_s: np.ndarray, raw: mne.io.BaseRaw, max_ms: float = SNAP_MS):
    """Absolute sample of the Status-channel 128 nearest to each onset (within max_ms);
    where none is that close (a trial without its photodiode, README D1) the rounded onset is used.
    Returns (samples, snap_distance in samples) with snap_distance NaN for the unsnapped."""
    ev = status_events(raw)
    pd_samples = np.sort(ev[ev[:, 2] == PHOTODIODE, 0])
    max_dist = int(np.ceil(max_ms * raw.info["sfreq"] / 1000.0))
    target = raw.first_samp + np.round(onsets_s * raw.info["sfreq"]).astype(int)
    j = np.searchsorted(pd_samples, target)
    j0 = np.clip(j - 1, 0, len(pd_samples) - 1)
    j1 = np.clip(j, 0, len(pd_samples) - 1)
    cand = np.where(np.abs(pd_samples[j0] - target) <= np.abs(pd_samples[j1] - target), pd_samples[j0], pd_samples[j1])
    dist = cand - target
    okk = np.abs(dist) <= max_dist
    out = np.where(okk, cand, target)
    return out.astype(int), np.where(okk, dist, np.nan)


def compare_status_with_events_tsv(subject: int, task: str, raw: mne.io.BaseRaw, tol_ms: float = STATUS_TOL_MS) -> dict:
    """Does the BDF Status channel reproduce events.tsv? Each tsv row is matched to the nearest Status
    event within `tol_ms` (the tsv onsets carry six significant figures, README D3); reports the
    unmatched tsv rows, the code mismatches among matched rows, and the Status events the tsv omits
    (stray single triggers such as 84 / 16 / 8 / 64 occur in some recordings)."""
    ev = status_events(raw)
    tsv = read_events(subject, task)
    tol = int(np.ceil(tol_ms * raw.info["sfreq"] / 1000.0))
    s_tsv = np.round(tsv.onset.values * raw.info["sfreq"]).astype(int)
    s_raw = ev[:, 0] - raw.first_samp
    j = np.searchsorted(s_raw, s_tsv)
    j0 = np.clip(j - 1, 0, len(s_raw) - 1)
    j1 = np.clip(j, 0, len(s_raw) - 1)
    near = np.where(np.abs(s_raw[j0] - s_tsv) <= np.abs(s_raw[j1] - s_tsv), j0, j1)
    ok = np.abs(s_raw[near] - s_tsv) <= tol
    extra = sorted(set(range(len(s_raw))) - set(near[ok].tolist()))
    return dict(n_status=len(ev), n_tsv=len(tsv),
                n_tsv_unmatched=int((~ok).sum()),
                n_code_mismatch=int((ev[near[ok], 2] != tsv.trial_type.values[ok]).sum()),
                max_sample_diff=int(np.abs(s_raw[near[ok]] - s_tsv[ok]).max()) if ok.any() else -1,
                n_status_extra=len(extra),
                status_extra_codes=";".join(str(int(c)) for c in ev[extra, 2]) if extra else "",
                n_128_status=int((ev[:, 2] == PHOTODIODE).sum()))


def load_subject(subject: int, task: str, tmin: float = TMIN, tmax: float = TMAX, baseline=BASELINE,
                 highpass: float = HIGHPASS_HZ, notch: float = NOTCH_HZ, lowpass: float = LOWPASS_HZ,
                 target_fs: float = TARGET_FS, reref: str = "average", keep_eog: bool = True,
                 verbose: bool = True) -> dict:
    """Returns dict(X (n_trials, n_chan, n_times) float64 in volts, trials (DataFrame, one row per
    epoch in X order = events-table trial order), time (s), labels, fsample, status_check)."""
    t0 = _time.time()
    raw = raw_bdf(subject, task, preload=True)
    status_check = compare_status_with_events_tsv(subject, task, raw)
    status_check["n_bdf_channels"] = raw.info["temp"]["n_bdf_channels"]
    status_check["raw_sfreq"] = float(raw.info["sfreq"])
    decim = int(round(raw.info["sfreq"] / target_fs))
    if abs(raw.info["sfreq"] / decim - target_fs) > 1e-6:
        raise RuntimeError(f"{sub_id(subject)} {task}: sfreq {raw.info['sfreq']} is not an integer multiple of {target_fs}")
    trials = trial_table(subject, task)
    # events at the photodiode-corrected onsets, one per trial row: the events.tsv onsets carry only
    # six significant figures (10 ms past 100 s), so each is snapped to the nearest 128 of the Status
    # channel (exact sample) before the Status channel is dropped
    samples, snap = snap_to_status(trials.onset_pd.values, raw)
    status_check["max_snap_samples"] = int(np.nanmax(np.abs(snap))) if np.isfinite(snap).any() else 0
    status_check["n_unsnapped"] = int(np.isnan(snap).sum())
    picks = mne.pick_types(raw.info, eeg=True, eog=keep_eog)
    raw.pick(picks)
    filt_picks = ["eeg", "eog"] if keep_eog else "eeg"
    if highpass:
        raw.filter(l_freq=highpass, h_freq=None, picks=filt_picks, verbose=False)
    if notch:
        raw.notch_filter(freqs=[notch], picks=filt_picks, verbose=False)
    if lowpass:
        # the anti-alias low-pass, every recording, before decimation (13 Sept 2026; docstring step 3)
        raw.filter(l_freq=None, h_freq=lowpass, picks=filt_picks, verbose=False)
    if raw.info["lowpass"] > target_fs / 2 + 1e-6:
        raise RuntimeError(f"{sub_id(subject)} {task}: lowpass {raw.info['lowpass']} Hz exceeds the target Nyquist "
                           f"{target_fs / 2} Hz; decimation would alias (set lowpass)")
    if reref == "average":
        raw.set_eeg_reference("average", projection=False, verbose=False)
    elif reref is not None:
        raw.set_eeg_reference(reref, projection=False, verbose=False)
    events = np.column_stack([samples, np.zeros(len(samples), dtype=int), trials.code.values.astype(int)])
    # no warning is suppressed here: an aliasing RuntimeWarning from Epochs(decim=) would be a real defect
    epochs = mne.Epochs(raw, events, event_id=None, tmin=tmin, tmax=tmax, baseline=baseline, decim=decim,
                        preload=True, reject=None, flat=None, reject_by_annotation=False, verbose=False)
    n_table = len(trials)
    dropped_trials, drop_reasons = [], []
    if len(epochs) != n_table:
        # MNE drops epochs that run past the recording's edges (no rejection thresholds are set): report which
        kept = epochs.selection
        dropped = sorted(set(range(n_table)) - set(kept))
        dropped_trials = [int(trials.trial.iloc[i]) for i in dropped]
        drop_reasons = [";".join(str(r) for r in epochs.drop_log[i]) for i in dropped]
        trials = trials.iloc[kept].reset_index(drop=True)
        if verbose:
            print(f"{sub_id(subject)} {task}: {len(dropped)} epoch(s) dropped: trials {dropped_trials}, reasons {drop_reasons}, "
                  f"recording {raw.times[-1]:.1f} s, onsets {[round(float(x), 1) for x in trial_table(subject, task).onset_pd.iloc[dropped]]}")
    X = epochs.get_data(copy=False)
    out = dict(X=X, trials=trials, time=epochs.times, labels=epochs.ch_names, fsample=float(epochs.info["sfreq"]),
               status_check=status_check, n_dropped_edge=n_table - len(trials), dropped_trials=dropped_trials,
               drop_reasons=drop_reasons, recording_s=float(raw.times[-1]),
               params=dict(tmin=tmin, tmax=tmax, baseline=baseline, highpass=highpass, notch=notch, lowpass=lowpass,
                           info_lowpass=float(raw.info["lowpass"]), decim=decim, target_fs=target_fs, reref=reref,
                           keep_eog=keep_eog, ch_types=[mne.channel_type(raw.info, i) for i in range(len(raw.ch_names))]))
    if verbose:
        print(f"{sub_id(subject)} {task}: X {X.shape} at {out['fsample']:.0f} Hz, {len(trials)} trials in table, "
              f"status {status_check}, {(_time.time() - t0) / 60:.1f} min", flush=True)
    return out


def cache_path(subject: int, task: str) -> str:
    return os.path.join(DERIVED_DIR, f"{sub_id(subject)}_task-{task}_epochs.npz")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subjects", default="1-36")
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--verify", action="store_true", help="load and compare epoch counts with the events tables; write results/load_verification.csv")
    ap.add_argument("--cache", action="store_true", help="write the epochs to DERIVED_DIR as npz")
    a = ap.parse_args()
    subs = parse_subjects(a.subjects)
    tasks = a.tasks.split(",")
    on_disk = set(available("bdf"))
    rows = []
    for s in subs:
        for t in tasks:
            if (s, t) not in on_disk:
                print(f"{sub_id(s)} {t}: no BDF on disk, skipped")
                continue
            d = load_subject(s, t)
            n_table = len(trial_table(s, t))
            rows.append(dict(subject=s, task=t, n_trials_table=n_table, n_epochs=d["X"].shape[0], n_dropped_edge=d["n_dropped_edge"],
                             dropped_trials=";".join(map(str, d["dropped_trials"])), drop_reasons=";".join(d["drop_reasons"]),
                             recording_s=round(d["recording_s"], 1),
                             match=(d["X"].shape[0] == n_table), n_chan=d["X"].shape[1], n_times=d["X"].shape[2], fsample=d["fsample"],
                             **{f"status_{k}": v for k, v in d["status_check"].items()}))
            if a.cache:
                os.makedirs(DERIVED_DIR, exist_ok=True)
                np.savez_compressed(cache_path(s, t), X=d["X"].astype(np.float32), time=d["time"], labels=np.array(d["labels"]),
                                    fsample=d["fsample"], trial=d["trials"].trial.values, code=d["trials"].code.values,
                                    contrast=d["trials"].contrast.values, seen=d["trials"].seen.values.astype(float),
                                    present=d["trials"].present.values, block=d["trials"].block.values, subject=s, task=t)
                d["trials"].to_csv(os.path.join(DERIVED_DIR, f"{sub_id(s)}_task-{t}_trials.csv"), index=False)
            del d
    if a.verify and rows:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        df = pd.DataFrame(rows)
        out = os.path.join(RESULTS_DIR, "load_verification.csv")
        if os.path.exists(out):
            old = pd.read_csv(out)
            old = old[~old.set_index(["subject", "task"]).index.isin(df.set_index(["subject", "task"]).index)]
            df = pd.concat([old, df], ignore_index=True).sort_values(["subject", "task"])
        df.to_csv(out, index=False)
        print(df.to_string())
        print(f"epoch count == events-table trial count in {int(df.match.sum())} of {len(df)} recordings")


if __name__ == "__main__":
    main()

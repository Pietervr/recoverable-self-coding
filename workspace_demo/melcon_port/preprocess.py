#!/usr/bin/env python3
"""Continuous-stage preprocessing of one ds006171 recording (Melcón et al. 2024) — PREREG_secondary_melcon.md §3,
DRAFT v4. NO decoding happens here: channel QC, interpolation, reference, epochs and trial rejection use no label,
no report and no contrast; the output is the epochs, the per-trial retention flags and a per-block QC report.

Order (the constants are CONFIG below; every step is fixed before any EEG is examined):
  0. channels by BioSemi name, positions from MNE's biosemi128 montage attached to the ORIGINAL names A1..D32 and
     kept through the position-preserving rename to channels.tsv's names (load.prepare_channels); 128 scalp 'eeg'
     and 4 'eog' channels are processed, nothing else.
  1. BLOCK-LOCAL SEGMENTS. The continuous recording is cut into one segment per block. The cut between blocks b and
     b+1 is the sample midway between the end of block b's last epoch (onset + TMAX) and the start of block b+1's
     first epoch (onset + TMIN); the first segment starts at the recording's first sample, the last ends at its
     last. Every later step runs on one segment and nothing crosses a cut, so a block's output samples, its QC
     decisions and its retained trials depend only on its own raw segment and the constants. Why: the 0.4 Hz
     high-pass has 8.25 s of support (4.125 s each side; the 50 Hz notch 6.6 s), so a recording-wide filter lets one
     block's samples reach another block's epochs where blocks follow closely — the shortest boundary onset gap in
     the included tasks is 2.643 s (sub-01 nocue, blocks 2 -> 3) and 15 of the 210 gaps are below 9.75 s (Codex,
     continuation review 3, V3.1).
  2. per segment: high-pass 0.4 Hz, notch 50 Hz, anti-alias low-pass 200 Hz on the scalp and EOG channels (FIR,
     firwin, Hamming, zero phase, automatic lengths, reflect_limited padding at the segment edges — MNE 1.13's
     defaults, named explicitly). A trial whose epoch lies within EDGE_S (the high-pass's one-sided support) of a
     segment edge is flagged edge_trial; a sensitivity drops those trials.
  3. channel QC on the filtered segment: FLAT = scalp peak-to-peak over the whole segment below 0.5 µV; NOISY =
     scalp peak-to-peak above 150 µV within -0.2 .. +0.6 s in more than 20 % of the block's trials (denominator: every
     trial of the block in the events table), measured after subtracting the per-sample median of the 128 scalp
     channels inside each window — a detection reference only, because BioSemi data are recorded against CMS/DRL and
     carry common-mode activity until re-referenced. EOG channels are never marked bad.
  4. the block's bad scalp channels are interpolated by spherical splines (mode 'accurate', origin 'auto').
  5. common average reference over the 128 scalp channels (after interpolation).
  6. epochs -0.5 .. +1.0 s around the photodiode-corrected onset, baseline -0.5 .. 0 s, decimation to 512 Hz.
  7. trial rejection on the epochs: any scalp channel above 150 µV peak-to-peak, or the bipolar VEOG = VEOG1 - VEOG2
     or HEOG = HEOG1 - HEOG2 above 100 µV peak-to-peak, within -0.2 .. +0.6 s. The sequence ends here. (DRAFT v3's
     second channel pass on the retained trials is removed: a retained trial has no scalp channel above the same
     150 µV threshold, so that pass could flag a channel only through the small difference between the median
     detection reference and the average reference — it was empty by construction, not a safeguard.)
  A recording is EXCLUDED when any block's bad set exceeds MAX_BAD (12) channels: a label-free, recording-level
  inclusion decision; the transformations above remain block-local.

CLI (writes the authenticated cache; no decoding):
  python preprocess.py --subjects 1 --tasks nocue --cache    # DERIVED_DIR/sub-01_task-nocue_preproc.npz
read_cache refuses a file whose stored configuration — every constant below, the library versions and the digests
of preprocess.py / load.py / common.py as loaded — differs from the running one, whose payload checksum fails, or
whose channel types are not the 128 'eeg' channels followed by the four EOG channels in their stored order.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _file_digests(names) -> dict:
    out = {}
    for name in names:
        with open(os.path.join(HERE, name), "rb") as fh:
            out[name] = hashlib.sha256(fh.read()).hexdigest()
    return out


# bound at import: a later disk edit does not change the identity of the code that is running
LOADED_SOURCES = _file_digests(("preprocess.py", "load.py", "common.py"))

import mne
import numpy as np
import pandas as pd
import scipy

import load as L
from common import DERIVED_DIR, EOG_NAMES, N_EEG, TASKS, available, parse_subjects, sub_id, trial_table

UV = 1e-6
PREPROC_VERSION = "melcon-preprocess 1 (2026-09-13, PREREG DRAFT v4 §3)"

CONFIG = dict(
    version=PREPROC_VERSION,
    tmin=L.TMIN, tmax=L.TMAX, baseline=list(L.BASELINE), target_fs=L.TARGET_FS,
    highpass_hz=L.HIGHPASS_HZ, notch_hz=L.NOTCH_HZ, lowpass_hz=L.LOWPASS_HZ,
    filter=dict(method="fir", fir_design="firwin", fir_window="hamming", phase="zero", filter_length="auto",
                l_trans_bandwidth="auto", h_trans_bandwidth="auto", notch_trans_bandwidth=1.0,
                pad="reflect_limited"),
    segments="block-local; cut midway between the last epoch of one block and the first epoch of the next",
    edge_s=4.125,
    montage="biosemi128 attached to the original BDF names A1..D32, then renamed by position to channels.tsv",
    flat_p2p_uv=0.5, noisy_p2p_uv=150.0, noisy_window=[-0.2, 0.6], noisy_frac=0.20,
    detection_reference="per-sample median of the 128 scalp channels inside each trial window (detection only)",
    interpolation=dict(method="spherical spline", mode="accurate", origin="auto"),
    reference="average of the 128 scalp channels after interpolation",
    reject_scalp_p2p_uv=150.0, reject_eog_p2p_uv=100.0, reject_window=[-0.2, 0.6],
    eog_bipolar=[["VEOG1", "VEOG2"], ["HEOG1", "HEOG2"]],
    channel_passes=1, max_bad=12,
    cache_dtype="float32",
    code=LOADED_SOURCES,
    versions=dict(mne=mne.__version__, numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__),
)


class StaleCacheError(RuntimeError):
    """A cache that does not authenticate against the running configuration."""


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def block_segments(onsets_rel: np.ndarray, blocks: np.ndarray, n_times: int, sfreq: float,
                   tmin: float, tmax: float) -> list[tuple[int, int, int]]:
    """(block, start, stop) in samples from the recording's first sample, stop exclusive, one per block in order."""
    onsets_rel = np.asarray(onsets_rel, dtype=np.int64)
    blocks = np.asarray(blocks)
    pre, post = int(round(tmin * sfreq)), int(round(tmax * sfreq))
    ub = sorted({int(b) for b in blocks})
    first = {b: int(onsets_rel[blocks == b].min()) for b in ub}
    last = {b: int(onsets_rel[blocks == b].max()) for b in ub}
    for b0, b1 in zip(ub[:-1], ub[1:]):
        if last[b0] >= first[b1]:
            raise RuntimeError(f"block {b1} begins before block {b0} ends; blocks are not temporally ordered")
        if last[b0] + post + 1 > first[b1] + pre:
            raise RuntimeError(f"blocks {b0} and {b1}: their epochs overlap, so no block-local cut exists")
    segments, start = [], 0
    for i, b in enumerate(ub):
        stop = (last[b] + post + 1 + first[ub[i + 1]] + pre) // 2 if i + 1 < len(ub) else int(n_times)
        segments.append((b, start, stop))
        start = stop
    return segments


def filter_kwargs(cfg: dict) -> dict:
    f = cfg["filter"]
    return dict(method=f["method"], fir_design=f["fir_design"], fir_window=f["fir_window"], phase=f["phase"],
                filter_length=f["filter_length"], pad=f["pad"])


def filter_support(sfreq: float, cfg: dict = CONFIG) -> dict:
    """Realised FIR lengths at this native rate; the edge flag must cover the high-pass's one-sided support."""
    f = cfg["filter"]
    design = dict(method=f["method"], fir_design=f["fir_design"], fir_window=f["fir_window"], phase=f["phase"],
                  filter_length=f["filter_length"], verbose=False)
    hp = mne.filter.create_filter(None, sfreq, cfg["highpass_hz"], None, l_trans_bandwidth=f["l_trans_bandwidth"], **design)
    lp = mne.filter.create_filter(None, sfreq, None, cfg["lowpass_hz"], h_trans_bandwidth=f["h_trans_bandwidth"], **design)
    out = dict(highpass_taps=len(hp), highpass_one_sided_s=(len(hp) - 1) / sfreq / 2,
               lowpass_taps=len(lp), lowpass_one_sided_s=(len(lp) - 1) / sfreq / 2)
    if out["highpass_one_sided_s"] > cfg["edge_s"] + 1e-9:
        raise RuntimeError(f"high-pass one-sided support {out['highpass_one_sided_s']:.3f} s exceeds edge_s {cfg['edge_s']}")
    return out


def apply_filters(raw: mne.io.BaseRaw, cfg: dict = CONFIG) -> mne.io.BaseRaw:
    """Step 2 on one segment (in place): high-pass, notch, low-pass on the scalp and EOG channels."""
    kw = dict(picks=["eeg", "eog"], verbose=False, **filter_kwargs(cfg))
    f = cfg["filter"]
    raw.filter(l_freq=cfg["highpass_hz"], h_freq=None, l_trans_bandwidth=f["l_trans_bandwidth"], **kw)
    raw.notch_filter(freqs=[cfg["notch_hz"]], trans_bandwidth=f["notch_trans_bandwidth"], **kw)
    raw.filter(l_freq=None, h_freq=cfg["lowpass_hz"], h_trans_bandwidth=f["h_trans_bandwidth"], **kw)
    return raw


def _segment(raw: mne.io.BaseRaw, start: int, stop: int) -> mne.io.RawArray:
    """An independent copy of samples [start, stop) with the recording's info and absolute sample numbering."""
    return mne.io.RawArray(raw.get_data(start=start, stop=stop), raw.info.copy(),
                           first_samp=raw.first_samp + start, verbose=False)


def detect_channels(seg: mne.io.BaseRaw, onsets: np.ndarray, cfg: dict = CONFIG) -> dict:
    """Step 3 on one filtered segment; onsets in samples from the segment's first sample."""
    eeg = mne.pick_types(seg.info, eeg=True, eog=False)
    names = [seg.ch_names[i] for i in eeg]
    d = seg.get_data(picks=eeg)
    flat = [names[i] for i in np.where(np.ptp(d, axis=1) < cfg["flat_p2p_uv"] * UV)[0]]
    sfreq = seg.info["sfreq"]
    a0 = int(round(cfg["noisy_window"][0] * sfreq))
    a1 = int(round(cfg["noisy_window"][1] * sfreq)) + 1
    over = np.zeros(len(eeg))
    for o in onsets:
        lo, hi = max(int(o) + a0, 0), min(int(o) + a1, d.shape[1])
        if hi <= lo:
            continue
        win = d[:, lo:hi]
        win = win - np.median(win, axis=0, keepdims=True)
        over += np.ptp(win, axis=1) > cfg["noisy_p2p_uv"] * UV
    n = len(onsets)
    frac = over / n if n else np.zeros(len(eeg))
    noisy = [names[i] for i in np.where(frac > cfg["noisy_frac"])[0]]
    return dict(flat=flat, noisy=noisy, noisy_frac=[round(float(x), 6) for x in frac], n_denominator=int(n))


def clean_segment(seg_filtered: mne.io.BaseRaw, bads: list[str], onsets: np.ndarray, codes: np.ndarray,
                  cfg: dict, decim: int):
    """Steps 4-7 on a copy of one filtered segment. Returns (X of the trials that have an epoch, has_epoch mask,
    reject reason per trial: '' retained, 'scalp', 'eog', 'scalp+eog', 'no_epoch')."""
    s = seg_filtered.copy()
    if bads:
        s.info["bads"] = list(bads)
        s.interpolate_bads(reset_bads=True, mode=cfg["interpolation"]["mode"], origin=cfg["interpolation"]["origin"],
                           verbose=False)
    s.set_eeg_reference("average", projection=False, ch_type="eeg", verbose=False)
    events = np.column_stack([np.asarray(onsets, dtype=np.int64) + s.first_samp, np.zeros(len(onsets), dtype=np.int64),
                              np.asarray(codes, dtype=np.int64)])
    # No warning is suppressed (MNE's decimation guard fires at 512 < 3 x 200 Hz; see load.py)
    ep = mne.Epochs(s, events, event_id=None, tmin=cfg["tmin"], tmax=cfg["tmax"], baseline=tuple(cfg["baseline"]),
                    decim=decim, preload=True, reject=None, flat=None, reject_by_annotation=False, verbose=False)
    X = ep.get_data(copy=True)
    has = np.zeros(len(onsets), dtype=bool)
    has[ep.selection] = True
    t = ep.times
    w = (t >= cfg["reject_window"][0] - 1e-9) & (t <= cfg["reject_window"][1] + 1e-9)
    types = ep.get_channel_types()
    eeg_i = [i for i, tp in enumerate(types) if tp == "eeg"]
    scalp = np.ptp(X[:, eeg_i][:, :, w], axis=2).max(axis=1) > cfg["reject_scalp_p2p_uv"] * UV
    eog = np.zeros(len(X), dtype=bool)
    for a, b in cfg["eog_bipolar"]:
        bip = X[:, ep.ch_names.index(a), :][:, w] - X[:, ep.ch_names.index(b), :][:, w]
        eog |= np.ptp(bip, axis=1) > cfg["reject_eog_p2p_uv"] * UV
    reason = np.array(["no_epoch"] * len(onsets), dtype=object)
    sub = np.where(scalp & eog, "scalp+eog", np.where(scalp, "scalp", np.where(eog, "eog", "")))
    reason[has] = sub
    return X, has, reason


def preprocess_raw(raw: mne.io.BaseRaw, trials: pd.DataFrame, onset_samples: np.ndarray, config: dict = CONFIG) -> dict:
    """Steps 1-7 on a prepared recording (load.prepare_channels). `onset_samples` are absolute sample numbers
    (including raw.first_samp), one per row of `trials`, which must carry `block` and `code`.

    Returns dict(X (n_epochs, 132, n_times) float64 volts — every trial that has an epoch, retained or not, in time
    order; trials (the input rows, same order, plus has_epoch, epoch_index, retained, reject_reason, edge_trial);
    time, labels, ch_types, fsample, qc (one dict per block), excluded, exclude_reason, filter_support, config)."""
    cfg = config
    sfreq = float(raw.info["sfreq"])
    decim = int(round(sfreq / cfg["target_fs"]))
    if decim < 1 or abs(sfreq / decim - cfg["target_fs"]) > 1e-6:
        raise RuntimeError(f"sfreq {sfreq} is not an integer multiple of {cfg['target_fs']}")
    support = filter_support(sfreq, cfg)
    raw = raw.copy().pick(["eeg", "eog"])
    types = raw.get_channel_types()
    eeg_names = [n for n, t in zip(raw.ch_names, types) if t == "eeg"]
    eog_names = [n for n, t in zip(raw.ch_names, types) if t == "eog"]
    if len(eeg_names) != N_EEG or tuple(eog_names) != tuple(EOG_NAMES) or raw.ch_names != eeg_names + eog_names:
        raise RuntimeError(f"expected {N_EEG} scalp channels then {EOG_NAMES}; got {len(eeg_names)} eeg, eog {eog_names}")
    locs = np.array([raw.info["chs"][raw.ch_names.index(n)]["loc"][:3] for n in eeg_names])
    if not (np.all(np.isfinite(locs)) and np.all(np.linalg.norm(locs, axis=1) > 0)):
        raise RuntimeError("scalp channels without montage positions: use load.prepare_channels")

    trials = trials.reset_index(drop=True).copy()
    rel = np.asarray(onset_samples, dtype=np.int64) - raw.first_samp
    if len(rel) != len(trials):
        raise RuntimeError("one onset sample per trial row is required")
    blocks = trials["block"].to_numpy()
    codes = trials["code"].to_numpy()
    segments = block_segments(rel, blocks, raw.n_times, sfreq, cfg["tmin"], cfg["tmax"])
    pre, post = int(round(cfg["tmin"] * sfreq)), int(round(cfg["tmax"] * sfreq))
    edge = int(round(cfg["edge_s"] * sfreq))

    trials["has_epoch"] = False
    trials["epoch_index"] = -1
    trials["retained"] = False
    trials["reject_reason"] = ""
    trials["edge_trial"] = False
    X_parts, qc, n_ep, time = [], [], 0, None
    for b, start, stop in segments:
        idx = np.where(blocks == b)[0]
        idx = idx[np.argsort(rel[idx], kind="stable")]
        seg = _segment(raw, start, stop)
        apply_filters(seg, cfg)
        onsets = rel[idx] - start
        det = detect_channels(seg, onsets, cfg)
        bads = [n for n in eeg_names if n in set(det["flat"]) | set(det["noisy"])]
        X, has, reason = clean_segment(seg, bads, onsets, codes[idx], cfg, decim)
        del seg
        if time is None and len(X):
            time = np.arange(X.shape[2]) / cfg["target_fs"] + cfg["tmin"]
        dist = np.minimum(onsets + pre, (stop - start) - (onsets + post + 1))
        trials.loc[idx, "edge_trial"] = dist < edge
        trials.loc[idx, "has_epoch"] = has
        trials.loc[idx[has], "epoch_index"] = np.arange(n_ep, n_ep + int(has.sum()))
        trials.loc[idx, "reject_reason"] = reason
        trials.loc[idx, "retained"] = reason == ""
        n_ep += int(has.sum())
        X_parts.append(X)
        qc.append(dict(block=int(b), start=int(start), stop=int(stop), n_trials=int(len(idx)),
                       n_denominator=det["n_denominator"], flat=det["flat"], noisy=det["noisy"], bad=bads,
                       n_bad=len(bads), noisy_frac_max=max(det["noisy_frac"]) if det["noisy_frac"] else 0.0,
                       n_epochs=int(has.sum()), n_no_epoch=int((reason == "no_epoch").sum()),
                       n_reject_scalp=int(np.isin(reason, ["scalp", "scalp+eog"]).sum()),
                       n_reject_eog=int(np.isin(reason, ["eog", "scalp+eog"]).sum()),
                       n_retained=int((reason == "").sum()), n_edge=int((dist < edge).sum())))
    over = [q["block"] for q in qc if q["n_bad"] > cfg["max_bad"]]
    X = np.concatenate(X_parts, axis=0) if X_parts else np.zeros((0, len(raw.ch_names), 0))
    return dict(X=X, trials=trials, time=time, labels=list(raw.ch_names), ch_types=list(types), fsample=cfg["target_fs"],
                qc=qc, excluded=bool(over),
                exclude_reason=(f"more than {cfg['max_bad']} bad channels in block(s) {over}" if over else ""),
                filter_support=support, config=cfg)


def preprocess_subject(subject: int, task: str, config: dict = CONFIG) -> dict:
    raw = L.raw_bdf(subject, task, preload=True)
    trials = trial_table(subject, task)
    samples, snap = L.snap_to_status(trials.onset_pd.values, raw)
    out = preprocess_raw(raw, trials, samples, config)
    out.update(subject=subject, task=task, n_unsnapped=int(np.isnan(snap).sum()))
    return out


# --- the authenticated cache ---------------------------------------------------------------------------------------

CACHE_KEYS = ("X", "time", "labels", "ch_types", "fsample", "trials_json", "qc_json", "config_json", "payload_sha256")


def cache_path(subject: int, task: str) -> str:
    return os.path.join(DERIVED_DIR, f"{sub_id(subject)}_task-{task}_preproc.npz")


def payload_digest(arrays: dict) -> str:
    """SHA-256 over every stored field except the digest itself, in a fixed order."""
    h = hashlib.sha256()
    for k in CACHE_KEYS[:-1]:
        a = np.asarray(arrays[k])
        h.update(k.encode())
        h.update(str(a.dtype).encode())
        h.update(repr(a.shape).encode())
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def write_cache(path: str, out: dict) -> str:
    if out["excluded"]:
        raise ValueError(f"excluded recording ({out['exclude_reason']}) is not cached")
    arrays = dict(X=out["X"].astype(np.float32), time=np.asarray(out["time"], dtype=np.float64),
                  labels=np.array(out["labels"]), ch_types=np.array(out["ch_types"]),
                  fsample=np.float64(out["fsample"]),
                  trials_json=np.array(out["trials"].to_json(orient="split", index=False)),
                  qc_json=np.array(canonical(out["qc"])), config_json=np.array(canonical(out["config"])))
    arrays["payload_sha256"] = np.array(payload_digest(arrays))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    np.savez_compressed(path, **arrays)
    return path


def read_cache(path: str, config: dict = CONFIG) -> dict:
    """The cached epochs, only if they authenticate against `config`; StaleCacheError otherwise."""
    with np.load(path, allow_pickle=False) as z:
        missing = [k for k in CACHE_KEYS if k not in z.files]
        if missing:
            raise StaleCacheError(f"{path}: not an authenticated preprocessing cache (missing {missing})")
        arrays = {k: z[k] for k in CACHE_KEYS}
    stored = json.loads(str(arrays["config_json"]))
    if canonical(stored) != canonical(config):
        diff = sorted(k for k in set(stored) | set(config) if canonical(stored.get(k)) != canonical(config.get(k)))
        raise StaleCacheError(f"{path}: configuration differs from the running one in {diff}")
    if payload_digest(arrays) != str(arrays["payload_sha256"]):
        raise StaleCacheError(f"{path}: payload checksum fails")
    labels, types = arrays["labels"].tolist(), arrays["ch_types"].tolist()
    eeg_idx = [i for i, t in enumerate(types) if t == "eeg"]
    eog_idx = [i for i, t in enumerate(types) if t == "eog"]
    if (eeg_idx != list(range(N_EEG)) or eog_idx != list(range(N_EEG, N_EEG + len(EOG_NAMES)))
            or tuple(labels[i] for i in eog_idx) != tuple(EOG_NAMES) or len(types) != N_EEG + len(EOG_NAMES)):
        raise StaleCacheError(f"{path}: channel types are not {N_EEG} 'eeg' followed by {EOG_NAMES}")
    trials = pd.read_json(io.StringIO(str(arrays["trials_json"])), orient="split")
    return dict(X=arrays["X"], time=arrays["time"], labels=labels, ch_types=types, eeg_idx=eeg_idx, eog_idx=eog_idx,
                fsample=float(arrays["fsample"]), trials=trials, qc=json.loads(str(arrays["qc_json"])), config=stored)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subjects", default="1-36")
    ap.add_argument("--tasks", default="nocue,informative")
    ap.add_argument("--cache", action="store_true", help="write the authenticated cache to DERIVED_DIR")
    a = ap.parse_args()
    on_disk = set(available("bdf"))
    for s in parse_subjects(a.subjects):
        for t in a.tasks.split(","):
            if t not in TASKS or (s, t) not in on_disk:
                print(f"{sub_id(s)} {t}: no BDF on disk, skipped")
                continue
            out = preprocess_subject(s, t)
            print(f"{sub_id(s)} {t}: X {out['X'].shape}, excluded {out['excluded']} {out['exclude_reason']}, "
                  f"per block bad/retained {[(q['n_bad'], q['n_retained']) for q in out['qc']]}", flush=True)
            if a.cache and not out["excluded"]:
                print("  ->", write_cache(cache_path(s, t), out))
            del out


if __name__ == "__main__":
    main()

"""preprocess.py on artificial continuous recordings (PREREG_secondary_melcon.md §3, DRAFT v4; Codex continuation
review 3, V3.1 and V3.2). No EEG of ds006171 is read: every recording here is a synthetic RawArray; the only file of
the dataset read is channels.tsv (a sidecar) for the channel names.

Checks: (1) positions attached to the original BioSemi names survive the rename to channels.tsv; (2) block-local
isolation — perturbing one block's raw samples (a step, a sine and a noisy channel) leaves the other blocks' epochs,
QC and retention bit-for-bit unchanged, while a recording-wide high-pass carries the same step into the previous
block's last epoch at the dataset's shortest boundary gap (2.643 s); (3) a flat channel, a noisy channel (> 20 % of
trials) and an occasional burst (10 %) in their blocks; EOG-only blinks reject trials without marking a scalp channel;
common-mode activity does not mark channels (the median detection reference); (4) edge flags; (5) more than twelve
bad channels in one block excludes the recording, twelve does not; (6) the cache authenticates its configuration,
payload and channel-type boundary and refuses legacy, altered or excluded inputs.

Run: ../../.venv/bin/python test_preprocess.py   (about a minute)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mne
import numpy as np
import pandas as pd

import common as C
import load as L
import preprocess as P

mne.set_log_level("ERROR")
FS = 1024.0
UV = 1e-6
PER_BLOCK = 10
SPACING_S = 1.8                    # the dataset's shortest within-block onset interval is 1.62 s
GAPS_S = (12.0, 2.643, 20.0)       # onset gaps 1->2, 2->3 (the dataset's shortest, sub-01 nocue), 3->4
LEAD_S = 5.0


def design():
    onsets, blocks, t = [], [], LEAD_S
    for b in range(4):
        for k in range(PER_BLOCK):
            onsets.append(t)
            blocks.append(b + 1)
            if k < PER_BLOCK - 1:
                t += SPACING_S
        if b < 3:
            t += GAPS_S[b]
    trials = pd.DataFrame(dict(trial=np.arange(1, len(onsets) + 1), block=blocks, onset_pd=onsets,
                               code=np.where(np.arange(len(onsets)) % PER_BLOCK == PER_BLOCK - 1, 31, 11)))
    return trials, onsets[-1] + LEAD_S


def base_data(n, seed=20260913):
    rng = np.random.default_rng(seed)
    d = rng.normal(0.0, 4 * UV, (144, n))
    d[:132] += rng.normal(0.0, 1e-3, (132, 1))                                   # electrode offsets (removed by the high-pass)
    d[:132] += 100 * UV * np.sin(2 * np.pi * 3.0 * np.arange(n) / FS)[None, :]   # common mode, 200 µV peak-to-peak
    d[143] = 0.0                                                                  # Status
    return d


def make_raw(data):
    raw = mne.io.RawArray(data, mne.create_info(L.BDF_NAMES_144, FS, ch_types="eeg"), verbose=False)
    return L.prepare_channels(raw, C.read_channels(1, "nocue"))


def rows(out, block):
    tr = out["trials"]
    return tr[tr.block == block]


def block_view(out, block):
    r = rows(out, block)
    idx = r.epoch_index[r.has_epoch].to_numpy()
    return out["X"][idx], r[["has_epoch", "retained", "reject_reason", "edge_trial"]].reset_index(drop=True)


def main():
    trials, dur = design()
    n = int(round(dur * FS))
    rel = np.round(trials.onset_pd.to_numpy() * FS).astype(np.int64)
    blocks = trials.block.to_numpy()
    segs = {b: (s, e) for b, s, e in P.block_segments(rel, blocks, n, FS, L.TMIN, L.TMAX)}
    tsv = C.read_channels(1, "nocue").name.tolist()
    scalp, eog_names = tsv[:128], tsv[128:132]
    assert tuple(eog_names) == tuple(C.EOG_NAMES), eog_names
    base = base_data(n)

    # (1) montage plumbing ------------------------------------------------------------------------------------------
    raw0 = make_raw(base.copy())
    montage = mne.channels.make_standard_montage("biosemi128")
    assert len(set(scalp) - set(montage.ch_names)) >= 100, "literal matching should miss most renamed labels"
    ref = mne.io.RawArray(np.zeros((128, 10)), mne.create_info(L.BDF_NAMES_144[:128], FS, "eeg"), verbose=False)
    ref.set_montage(montage)
    locs_ref = np.array([c["loc"][:3] for c in ref.info["chs"]])
    locs = np.array([raw0.info["chs"][raw0.ch_names.index(nm)]["loc"][:3] for nm in scalp])
    assert np.all(np.isfinite(locs)) and np.all(np.linalg.norm(locs, axis=1) > 0)
    assert np.array_equal(locs, locs_ref), "a renamed channel lost its original BioSemi position"
    print("(1) positions attached to A1..D32 survive the rename to channels.tsv for all 128 scalp channels")

    # the unperturbed recording ------------------------------------------------------------------------------------
    A = P.preprocess_raw(raw0, trials, rel + raw0.first_samp)
    assert A["X"].shape == (40, 132, 769), A["X"].shape
    assert A["labels"][:128] == scalp and A["labels"][128:] == eog_names
    assert not A["excluded"] and all(q["n_bad"] == 0 for q in A["qc"]), A["qc"]
    assert A["trials"].retained.all(), A["trials"].reject_reason.value_counts()
    fs_info = A["filter_support"]
    assert fs_info["highpass_taps"] == 8449 and abs(fs_info["highpass_one_sided_s"] - 4.125) < 1e-9, fs_info
    print("    common mode of 200 µV peak-to-peak marks no channel and rejects no trial; high-pass one-sided support "
          f"{fs_info['highpass_one_sided_s']:.3f} s = edge_s")

    # (4) edge flags on the unperturbed run ----------------------------------------------------------------------------
    b2, b3 = rows(A, 2), rows(A, 3)
    assert bool(b2.edge_trial.iloc[-1]) and bool(b3.edge_trial.iloc[0]), "the trials beside the 2.643 s gap are edge trials"
    assert not rows(A, 1).edge_trial.iloc[1:-1].any() and not rows(A, 4).edge_trial.iloc[1:-1].any()
    print(f"(4) edge trials: {int(A['trials'].edge_trial.sum())} of 40 (both sides of the short gap flagged)")

    # (2) block-local isolation --------------------------------------------------------------------------------------
    s3, e3 = segs[3]
    pert = base.copy()
    tt = np.arange(e3 - s3) / FS
    pert[0:64, s3:e3] += 30 * UV + 40 * UV * np.sin(2 * np.pi * 1.0 * tt)      # a step at the cut plus a sine, half the cap
    noisy_ch = 5
    for o in rel[blocks == 3]:
        pert[noisy_ch, o + 102:o + 204] += 400 * UV * np.hanning(102)             # a burst in every block-3 trial
    assert np.array_equal(pert[:, :s3], base[:, :s3]) and np.array_equal(pert[:, e3:], base[:, e3:])
    B = P.preprocess_raw(make_raw(pert), trials, rel)
    for b in (1, 2, 4):
        xa, ta = block_view(A, b)
        xb, tb = block_view(B, b)
        assert np.array_equal(xa, xb), f"block {b}: epochs changed by a perturbation confined to block 3"
        assert ta.equals(tb), f"block {b}: retention changed"
        assert P.canonical(A["qc"][b - 1]) == P.canonical(B["qc"][b - 1]), f"block {b}: QC changed"
    assert scalp[noisy_ch] in B["qc"][2]["noisy"] and B["qc"][2]["bad"] == [scalp[noisy_ch]], B["qc"][2]
    assert not np.array_equal(block_view(A, 3)[0], block_view(B, 3)[0])
    # the counterexample the block-local design removes: a recording-wide high-pass
    wide = []
    for data in (base, pert):
        r = make_raw(data.copy()).pick(["eeg", "eog"])
        P.apply_filters(r, P.CONFIG)
        o = int(rel[blocks == 2].max())
        wide.append(r.get_data(picks=[0], start=o + int(L.TMIN * FS), stop=o + int(L.TMAX * FS) + 1)[0])
    leak = float(np.max(np.abs(wide[1] - wide[0])))
    assert leak > 0.5 * UV, leak
    print(f"(2) isolation: blocks 1, 2, 4 bit-identical (epochs, QC, retention) with block 3 perturbed; a recording-wide "
          f"high-pass moves block 2's last epoch by up to {leak / UV:.2f} µV")
    del pert, B, wide

    # (3) flat, noisy, occasional burst, EOG-only ---------------------------------------------------------------------
    c = base.copy()
    s1, e1 = segs[1]
    flat_ch, noisy2, burst_ch = 10, 30, 20
    c[flat_ch, s1:e1] = 1e-3                                                     # a flat electrode in block 1 only
    i2, i4 = np.where(blocks == 2)[0], np.where(blocks == 4)[0]
    for k in (0, 3, 8):                                                          # 3 of 10 block-2 trials: noisy
        o = rel[i2[k]]
        c[noisy2, o + 300:o + 400] += 300 * UV * np.hanning(100)
    o = rel[i2[6]]
    c[burst_ch, o + 300:o + 400] += 300 * UV * np.hanning(100)                   # 1 of 10: the trial goes
    veog1 = 128                                                                  # EXG1 -> VEOG1
    for k in (1, 3):
        o = rel[i4[k]]
        c[veog1, o + 256:o + 512] += 250 * UV * np.hanning(256)                  # blinks at +0.25 .. +0.5 s
    D = P.preprocess_raw(make_raw(c), trials, rel)
    q = D["qc"]
    assert q[0]["flat"] == [scalp[flat_ch]] and q[0]["bad"] == [scalp[flat_ch]], q[0]
    assert q[1]["noisy"] == [scalp[noisy2]] and q[1]["bad"] == [scalp[noisy2]], q[1]
    assert q[2]["bad"] == [] and q[3]["bad"] == [], (q[2], q[3])
    assert not any(e in qq["bad"] for qq in q for e in eog_names)
    x1, _ = block_view(D, 1)
    ch = D["labels"].index(scalp[flat_ch])
    assert np.all(np.isfinite(x1)) and np.all(np.ptp(x1[:, ch, :], axis=1) > 0), "flat channel not interpolated"
    r2, r4 = rows(D, 2), rows(D, 4)
    assert r2.reject_reason.iloc[6] == "scalp" and r2.retained.drop(r2.index[6]).all(), r2.reject_reason.tolist()
    assert list(r4.reject_reason.iloc[[1, 3]]) == ["eog", "eog"] and r4.retained.drop(r4.index[[1, 3]]).all()
    print(f"(3) flat {scalp[flat_ch]} (block 1) and noisy {scalp[noisy2]} (block 2, 3 of 10 trials) interpolated in "
          f"their blocks only; a 1-in-10 burst rejects its trial; EOG-only blinks reject 2 trials and mark no channel")
    del c, D

    # (5) exclusion ------------------------------------------------------------------------------------------------------
    x = base.copy()
    s2, e2 = segs[2]
    x[40:52, s1:e1] = 1e-3                                                       # 12 flat in block 1: allowed
    x[60:73, s2:e2] = 1e-3                                                       # 13 flat in block 2: excludes
    E = P.preprocess_raw(make_raw(x), trials, rel)
    assert E["qc"][0]["n_bad"] == 12 and E["qc"][1]["n_bad"] == 13 and E["excluded"], (E["qc"][0], E["qc"][1])
    assert "[2]" in E["exclude_reason"], E["exclude_reason"]
    print(f"(5) exclusion: {E['exclude_reason']} (12 in block 1 allowed)")
    del x

    # (6) the authenticated cache ------------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory(prefix="melcon-preproc-") as td:
        path = P.write_cache(os.path.join(td, "sub-99_task-nocue_preproc.npz"), A)
        R = P.read_cache(path)
        assert np.array_equal(R["X"], A["X"].astype(np.float32))
        assert R["eeg_idx"] == list(range(128)) and [R["labels"][i] for i in R["eog_idx"]] == eog_names
        assert R["trials"][["trial", "block", "retained", "edge_trial", "epoch_index"]].equals(
            A["trials"][["trial", "block", "retained", "edge_trial", "epoch_index"]])
        refused = []

        def expect_refusal(label, fn):
            try:
                fn()
            except P.StaleCacheError as err:
                refused.append(label)
                return str(err)
            raise AssertionError(f"accepted: {label}")

        expect_refusal("changed configuration", lambda: P.read_cache(path, config=dict(P.CONFIG, noisy_frac=0.25)))
        expect_refusal("changed code digest", lambda: P.read_cache(
            path, config=dict(P.CONFIG, code=dict(P.CONFIG["code"], **{"preprocess.py": "0" * 64}))))
        legacy = os.path.join(td, "legacy.npz")
        np.savez_compressed(legacy, X=A["X"].astype(np.float32), time=A["time"], labels=np.array(A["labels"]))
        expect_refusal("legacy cache without configuration", lambda: P.read_cache(legacy))
        with np.load(path, allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
        altered = dict(arrays, X=arrays["X"] + np.float32(1e-6))
        np.savez_compressed(os.path.join(td, "altered.npz"), **altered)
        expect_refusal("altered epochs", lambda: P.read_cache(os.path.join(td, "altered.npz")))
        types = arrays["ch_types"].copy()
        types[128:] = "eeg"
        retyped = dict(arrays, ch_types=types)
        retyped["payload_sha256"] = np.array(P.payload_digest(retyped))
        np.savez_compressed(os.path.join(td, "retyped.npz"), **retyped)
        expect_refusal("EOG typed as EEG (checksum recomputed)", lambda: P.read_cache(os.path.join(td, "retyped.npz")))
        try:
            P.write_cache(os.path.join(td, "excluded.npz"), E)
            raise AssertionError("an excluded recording was cached")
        except ValueError:
            refused.append("excluded recording not written")
    assert set(P.CONFIG["code"]) == {"preprocess.py", "load.py", "common.py"}
    print(f"(6) cache: round trip exact, EEG/EOG boundary kept; refused: {'; '.join(refused)}")
    print("test_preprocess: ALL OK")


if __name__ == "__main__":
    main()

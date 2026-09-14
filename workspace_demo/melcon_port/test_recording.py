"""decoder.py and recording.py on synthetic epochs (synthetic.py; the trial structure of one real events table, no
EEG). Checks: the window grid (40 half-open 30 ms windows, 15 or 16 samples; main = 300-600 ms, early = 0-300 ms); the
held-out z-score uses only the decoder half; the §4 isolation property exactly — changing the EEG and the labels of one
held-out block changes neither the decoder that scores it (the other half's projections of it are recomputed, the
decoder's are not), nor the likelihood parameters that predict it, nor the other block of its half; the recording
result's structure and availability; the excluded and technical-failure statuses. Prints the single-worker timing
of one recording (decoder, fits) for the battery's cost estimate.

Run: ../../.venv/bin/python test_recording.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

import decoder as DEC
import likelihood as LK
import recording as RC
import synthetic as SY


def check_windows():
    wins = DEC.window_samples(SY.TIME)
    counts = {len(w) for w in wins}
    assert len(wins) == 40 and counts <= {15, 16}, counts
    assert DEC.MAIN == list(range(20, 30)) and DEC.EARLY == list(range(10, 20))
    return counts


def main():
    counts = check_windows()
    print(f"windows: 40 half-open 30 ms windows of {sorted(counts)} samples; main 300-600 ms = {DEC.MAIN[0]}..{DEC.MAIN[-1]}")
    tmpl = SY.template(1, "nocue")
    rec = SY.generate(tmpl, "X1", amplitude=0.6, drift=False, tags=(1, 0, 0))

    t0 = time.time()
    dec = DEC.split_half(rec)
    t_dec = time.time() - t0
    assert dec["status"] == "ok"
    h2 = dec["halves"][(3, 4)]
    # the z-score of B uses A's in-sample statistics only: recompute from A's decision values
    tr = rec["trials"]
    ra, rb = tr[tr.block.isin((1, 2))], tr[tr.block.isin((3, 4))]
    da, db = DEC.decision_values(rec["X"][ra.epoch_index][:, :128, 300:302].astype(float),
                                 (~ra["catch"].to_numpy(bool)).astype(int),
                                 rec["X"][rb.epoch_index][:, :128, 300:302].astype(float))
    assert np.allclose(da.mean(0), h2["z_mean"][300:302]) and np.allclose(da.std(0, ddof=1), h2["z_sd"][300:302])
    print(f"z-score of the held-out half from the decoder half's in-sample decision values: confirmed; decoder {t_dec:.1f} s")

    # isolation: perturb the EEG and the labels of block 4 (held out when H1 is the decoder half)
    wins = (DEC.MAIN[3], DEC.EARLY[5])
    t0 = time.time()
    base = RC.recording_scores(rec, 1, "nocue", windows=wins)
    t_fit = time.time() - t0
    assert base["status"] == "ok", base["status"]
    pert = {k: v for k, v in rec.items()}
    pert["X"] = rec["X"].copy()
    b4 = tr.index[tr.block == 4].to_numpy()
    rng = np.random.default_rng(0)
    pert["X"][b4, :128, :] += (3.0 * rng.normal(size=(b4.size, 128, rec["X"].shape[2]))).astype(np.float32)
    pert["trials"] = tr.copy()
    pres4 = b4[~tr.loc[b4, "catch"].to_numpy(bool)]
    pert["trials"].loc[pres4, "contrast"] *= 1.7
    flip = pres4[:5]
    pert["trials"].loc[flip, "side"] = np.where(tr.loc[flip, "side"] == "left", "right", "left")
    new = RC.recording_scores(pert, 1, "nocue", windows=wins)
    hb, hn = base["decoder"]["halves"][(3, 4)], new["decoder"]["halves"][(3, 4)]
    m3 = hb["trials"].block.to_numpy() == 3
    assert np.array_equal(hb["z_mean"], hn["z_mean"]) and np.array_equal(hb["z_sd"], hn["z_sd"]), "decoder of block 4 changed"
    assert np.array_equal(hb["W"][m3], hn["W"][m3]), "block 3's projections changed"
    half = sorted(base["decoder"]["halves"]).index((3, 4))
    for w in wins:
        fold_predicting_b4 = (half, 0, w)                    # train block 3 -> test block 4
        for m in LK.PRIMARY:
            a, b = base["folds"][fold_predicting_b4][m], new["folds"][fold_predicting_b4][m]
            assert a["available"] and b["available"]
            assert np.array_equal(a["theta"], b["theta"]), f"parameters predicting block 4 changed ({m}, window {w})"
    changed = not np.array_equal(base["decoder"]["halves"][(1, 2)]["W"], new["decoder"]["halves"][(1, 2)]["W"])
    assert changed, "block 4 is decoder training data for H1's projections, which should change"
    print("isolation: with block 4's EEG and labels changed, its decoder (fitted on blocks 1-2), block 3's projections and "
          "the parameters predicting block 4 are bit-identical; the H1 projections (decoder trained on blocks 3-4) change")

    assert base["evidence"].shape == (2, 3) and base["available"].all() and np.all(np.isfinite(base["delta"]))
    assert base["n_trials"].tolist() == [int(len(tr))] * 2
    print(f"recording result: evidence {base['evidence'].shape}, all available, delta {np.round(base['delta'], 4).tolist()}, "
          f"AUC by half {np.round(base['auc'], 3).tolist()}")

    few = {k: v for k, v in rec.items()}
    few["trials"] = tr.copy()
    few["trials"].loc[tr.index[(tr.block <= 2) & tr["catch"]][5:], "retained"] = False
    st = RC.recording_scores(few, 1, "nocue", windows=wins)["status"]
    assert st.startswith("excluded"), st
    broken = {k: v for k, v in rec.items()}
    broken["X"] = rec["X"][:, :, :100]
    st2 = RC.recording_scores(broken, 1, "nocue", windows=wins)["status"]
    assert st2.startswith("technical failure"), st2
    print(f"statuses: '{st}'; '{st2[:60]}…'")

    per_window = t_fit / len(wins)
    print(f"timing (one worker, machine under load): decoder {t_dec:.1f} s per recording; decoder + fits {t_fit:.1f} s for "
          f"{len(wins)} windows; projected recording ≈ {t_dec + (t_fit - t_dec) / len(wins) * 20:.0f} s at 20 windows")
    print("test_recording: ALL OK")


if __name__ == "__main__":
    main()

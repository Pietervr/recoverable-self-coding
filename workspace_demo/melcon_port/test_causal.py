"""The causal-processing sensitivity (PREREG §5, DRAFT v4; Codex continuation review 3, V3.1's last point) on artificial
inputs only: with CONFIG_CAUSAL the three FIR filters are minimum-phase, so an impulse at sample s leaves every earlier
output sample exactly zero, while the primary zero-phase filters spread it backwards; the decoder's causal smoother
likewise; the causal variant runs through preprocess_raw, differs from the primary output, and its cache authenticates
only under its own configuration. No EEG of ds006171 is read.

Run: ../../.venv/bin/python test_causal.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mne
import numpy as np

import decoder as DEC
import preprocess as P
import test_preprocess as TP

mne.set_log_level("ERROR")


def impulse_response(config, n=int(40 * TP.FS), s=int(20 * TP.FS)):
    d = np.zeros((144, n))
    d[0, s] = 1e-6
    r = TP.make_raw(d).pick(["eeg", "eog"])
    P.apply_filters(r, config)
    y = r.get_data(picks=[0])[0]
    return y, s


def main():
    y, s = impulse_response(P.CONFIG_CAUSAL)
    pre = np.max(np.abs(y[:s]))
    assert pre <= 1e-12 * 1e-6 and np.max(np.abs(y[s:])) > 0, pre          # FFT convolution leaves ~1e-17 of the impulse
    y0, _ = impulse_response(P.CONFIG)
    back = np.max(np.abs(y0[:s]))
    assert back > 1e6 * max(pre, 1e-30)
    lag_ms = 1000.0 * (int(np.argmax(np.abs(y[s:]))) / TP.FS)
    print(f"filters: causal output before the impulse at most {pre / 1e-6:.1e} of the impulse (floating-point residue); "
          f"zero-phase spreads it backwards up to {back / 1e-6:.3g} of the impulse; causal peak at +{lag_ms:.1f} ms")
    sup = P.filter_support(TP.FS, P.CONFIG_CAUSAL)
    print(f"causal FIR lengths at 1024 Hz: high-pass {sup['highpass_taps']} taps, low-pass {sup['lowpass_taps']} taps")

    z = np.zeros((1, 769))
    z[0, 400] = 1.0
    zc = DEC.smooth(z, causal=True)
    zz = DEC.smooth(z, causal=False)
    assert np.max(np.abs(zc[0, :400])) == 0.0 and np.max(np.abs(zz[0, :400])) > 0
    peak = (int(np.argmax(zc[0, 400:])) / DEC.FS) * 1000.0
    print(f"smoother: forward-only output is zero before the impulse (peak at +{peak:.1f} ms); forward-backward is not")

    trials, dur = TP.design()
    n = int(round(dur * TP.FS))
    rel = np.round(trials.onset_pd.to_numpy() * TP.FS).astype(np.int64)
    base = TP.base_data(n)
    A = P.preprocess_raw(TP.make_raw(base.copy()), trials, rel)
    Cz = P.preprocess_raw(TP.make_raw(base.copy()), trials, rel, config=P.CONFIG_CAUSAL)
    assert A["X"].shape == Cz["X"].shape and not np.array_equal(A["X"], Cz["X"])
    assert not Cz["excluded"] and Cz["trials"].retained.all()
    with tempfile.TemporaryDirectory(prefix="melcon-causal-") as td:
        path = P.write_cache(os.path.join(td, "sub-99_task-nocue_preproc_causal.npz"), Cz)
        P.read_cache(path, config=P.CONFIG_CAUSAL)
        try:
            P.read_cache(path)
            raise AssertionError("a causal cache authenticated under the primary configuration")
        except P.StaleCacheError:
            pass
    print("preprocess_raw with CONFIG_CAUSAL: runs, retains every artificial trial, differs from the primary output; its "
          "cache is refused under the primary configuration")
    print("test_causal: ALL OK")


if __name__ == "__main__":
    main()

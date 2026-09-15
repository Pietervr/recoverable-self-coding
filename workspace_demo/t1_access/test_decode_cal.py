"""Synthetic tests for decode_cal.py (no captures): folds, selection rule, refit, z-scaling, determinism.

    workspace_demo/t1_access/.venv-decode/bin/python -m pytest workspace_demo/t1_access/test_decode_cal.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import decode_cal as dc  # noqa: E402

FAMILIES = ["animals", "countries", "tools", "foods", "vehicles", "instruments", "body parts", "materials"]
CONCEPTS = [f"{f}/c{i}" for f in FAMILIES for i in range(2)]


def synthetic(d=40, per=48, signal=1.0, seed=0):
    rng = np.random.default_rng(seed)
    direction = rng.normal(size=d)
    X, y, g = [], [], []
    for c in CONCEPTS:
        offset = rng.normal(scale=0.5, size=d)
        for k in (0, 8):
            for _ in range(per // 2):
                X.append(offset + rng.normal(size=d) + (signal * direction if k == 8 else 0))
                y.append(int(k == 8))
                g.append(c)
    return np.array(X, dtype=np.float32), np.array(y), np.array(g)


def test_parse_trial_id():
    m = dc.parse_trial_id("CAL|primary|active|body parts/knee|c3|d1|k8")
    assert m == {"split": "CAL", "set": "primary", "condition": "active", "concept": "body parts/knee",
                 "carrier": 3, "draw": 1, "k": 8, "family": "body parts"}


def test_folds_are_concept_disjoint_balanced_and_seeded():
    folds = dc.concept_folds(CONCEPTS)
    sizes = sorted(np.bincount(list(folds.values())).tolist())
    assert sizes == [3, 3, 3, 3, 4]
    for f in FAMILIES:
        assert folds[f"{f}/c0"] != folds[f"{f}/c1"]
    assert dc.concept_folds(list(reversed(CONCEPTS))) == folds


def test_fit_layer_separates_and_is_deterministic():
    X, y, g = synthetic()
    folds = dc.concept_folds(CONCEPTS)
    a = dc.fit_layer(X, y, g, folds)
    b = dc.fit_layer(X, y, g, folds)
    assert a["C"] == b["C"] and np.array_equal(a["coef"], b["coef"])
    assert max(a["cv"]["accuracy"]) > 0.9 and a["refit_converged"]
    assert len(a["cv"]["log_loss"]) == 9
    assert a["C_index"] == int(np.argmin(a["cv"]["log_loss"]))
    from sklearn.linear_model import LogisticRegression  # z-scaling reproduces from the stored parameters
    z = ((X - a["scaler_mean"]) / a["scaler_scale"]) @ a["coef"] + a["intercept"]
    assert abs(np.mean(z) - a["z_mean"]) < 1e-6 and abs(np.std(z) - a["z_sd"]) < 1e-6
    assert LogisticRegression  # imported for the environment check


def test_ties_go_to_smaller_C(monkeypatch):
    X, y, g = synthetic(signal=0.0)
    calls = []

    def flat_log_loss(y_true, p, labels=None):
        calls.append(1)
        return 0.5

    import sklearn.metrics
    monkeypatch.setattr(sklearn.metrics, "log_loss", flat_log_loss)
    res = dc.fit_layer(X, y, g, dc.concept_folds(CONCEPTS))
    assert calls and res["C_index"] == 0 and res["C"] == dc.C_GRID[0]

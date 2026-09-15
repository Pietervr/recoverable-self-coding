"""Synthetic tests of h3.py (no captures).

    workspace_demo/t1_access/.venv/bin/python -m pytest workspace_demo/t1_access/test_h3.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import h3  # noqa: E402

BANK = json.loads((HERE / "stimuli" / "concepts.json").read_text())


def test_offtarget_pairs_rules():
    pairs = h3.offtarget_pairs(BANK)
    role = {c["id"]: c["role"] for c in BANK["concepts"]}
    assert len(pairs) == 8 * 7
    for key, (u1, u2) in pairs.items():
        ft, ff = key.split("|")
        f1, f2 = u1.split("/")[0], u2.split("/")[0]
        assert role[u1] == role[u2] == "BACKGROUND" and f1 != f2 and not {f1, f2} & {ft, ff}
    assert h3.offtarget_pairs(BANK) == pairs


def test_match_within_cells_and_cap():
    rng = np.random.default_rng(0)
    n = 3000
    k = rng.choice([2, 3, 4], n)
    carrier = rng.integers(0, 6, n)
    family = rng.choice(["animals", "tools"], n)
    labels = rng.choice(np.array(["high", "low", ""], dtype=object), n)
    m = h3.match(labels, k, carrier, family, n_max=200)
    assert m["n_pairs"] == 200 and len(set(m["high"])) == 200 and len(set(m["low"])) == 200
    for h, l in zip(m["high"], m["low"]):
        assert labels[h] == "high" and labels[l] == "low"
        assert (k[h], carrier[h], family[h]) == (k[l], carrier[l], family[l])
    small = h3.match(labels[:60], k[:60], carrier[:60], family[:60], n_max=200)
    assert small["n_pairs"] == small["n_eligible_pairs"] < 200
    assert h3.match(labels, k, carrier, family, n_max=200) == m


def test_state_labels_levels_only():
    p = np.array([0.95, 0.05, 0.5, 0.95, 0.02])
    k = np.array([2, 3, 4, 8, 0])
    assert h3.state_labels(p, k).tolist() == ["high", "low", "", "", ""]


def test_edit_lists_counts_and_fields():
    layers, pos = [30, 41, 52], [120, 121, 122]
    e = h3.edit_lists(layers, pos, 5388, 13846, amplitudes={30: 2.0, 41: 3.0, 52: 4.0}, off_ids=(1, 2),
                      swap_written={l: [1.0, 1.1, 1.2] for l in layers}, patch_rows={l: "AA==" for l in layers})
    assert len(e) == 1 + 6 + 9
    assert e["baseline"] == [] and all(x["alpha"] == 0.0 for x in e["sham"])
    assert [x["layer"] for x in e["swap"]] == layers and e["swap"][0]["positions"] == pos
    assert e["rescue"][1]["target_norms"] == [3.0] * 3
    assert e["offtarget"][2]["target_norms"] == [1.0, 1.1, 1.2]
    assert e["ablate@41"][0]["ablate_token_ids"] == [5388]


def test_amplitudes_median():
    logs = [[{"layer": 30, "written_delta_norm": [1.0, 3.0]}], [{"layer": 30, "written_delta_norm": [2.0]}]]
    assert h3.amplitudes(logs, [30]) == {30: 2.0}


def _concepts(n_per=20):
    names = [f"{f}/c{i}" for f in ["animals", "tools", "foods", "vehicles"] for i in range(4)]
    return np.repeat(np.array(names), n_per)


def test_interaction_detects_and_rejects():
    rng = np.random.default_rng(1)
    concepts = _concepts()
    labels = np.where(np.arange(concepts.size) % 2 == 0, "high", "low").astype(object)
    e_yes = np.where(labels == "high", 1.5, 0.2) + rng.normal(0, 0.3, concepts.size)
    r = h3.interaction(e_yes, labels, concepts, n_boot=300)
    assert r["supported"] and r["strong"] and 1.1 < r["estimate"] < 1.5
    e_no = rng.normal(0.5, 0.3, concepts.size)
    assert not h3.interaction(e_no, labels, concepts, n_boot=300)["supported"]


def test_equivalence_and_positive_control():
    rng = np.random.default_rng(2)
    concepts = _concepts()
    assert h3.equivalence(rng.normal(0, 0.05, concepts.size), concepts, n_boot=300)["equivalent"]
    assert not h3.equivalence(rng.normal(0.4, 0.05, concepts.size), concepts, n_boot=300)["equivalent"]
    assert h3.positive_control(rng.normal(1.0, 0.2, concepts.size), concepts, n_boot=300)["h3"] == "testable"
    assert h3.positive_control(rng.normal(0.0, 0.2, concepts.size), concepts, n_boot=300)["h3"] == "not testable"


def test_flips_and_effect_sign():
    before = np.array([True, True, False, False])
    after = np.array([False, True, True, False])
    assert h3.flips(before, after) == {"denominator": 2, "flips": 1}
    assert h3.flips(before, after, rescue=True) == {"denominator": 4, "flips": 1}
    assert h3.effect(np.array([3.0]), np.array([1.0]))[0] == 2.0
    assert h3.effect(np.array([1.0]), np.array([3.0]), rescue=True)[0] == 2.0


def test_binary_vs_smooth_prefers_the_generating_account():
    rng = np.random.default_rng(3)
    concepts = _concepts(40)
    z = rng.normal(0, 1, concepts.size)
    labels = np.where(z > 0, "high", "low").astype(object)
    e_smooth = 0.8 * z + rng.normal(0, 0.2, concepts.size)
    assert not h3.binary_vs_smooth(e_smooth, labels, z, concepts)["two_state_may_be_written"]
    e_binary = np.where(labels == "high", 1.0, 0.0) + rng.normal(0, 0.05, concepts.size)
    z_noisy = np.where(labels == "high", 1.0, -1.0) * np.abs(rng.normal(0, 1, concepts.size))
    assert h3.binary_vs_smooth(e_binary, labels, z_noisy, concepts)["two_state_may_be_written"]

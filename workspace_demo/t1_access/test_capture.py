"""Offline tests for the T1 capture path (no model load): packet ids, bf16 decoding,
request validation and the edit arithmetic of jlens_qwen/capture_endpoint.py.

Run with the upstream environment (mlx, fastapi and the tokenizer live there):
    workspace_demo/upstream/jlens-qwen36/.venv/bin/python -m pytest workspace_demo/t1_access/test_capture.py -q
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import mlx.core as mx
import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "upstream" / "jlens-qwen36"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(UPSTREAM))

from capture import bf16_to_float32  # noqa: E402
from stimuli.packet import (ANSWER_SUFFIX, INSTRUCTION_A, MarkerError, SuffixError,  # noqa: E402
                            build_ids, packet_text)

SNAP = Path.home() / ".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots"


@pytest.fixture(scope="module")
def tok():
    from transformers import AutoTokenizer

    snaps = sorted(SNAP.glob("*"))
    if not snaps:
        pytest.skip("model snapshot not in the HF cache")
    return AutoTokenizer.from_pretrained(str(snaps[-1]))


SLOTS = ["has four legs and a flat seat for one person"] * 4 + ["gives light from a bulb under a shade"] * 4


def test_bf16_to_float32_is_exact():
    rng = np.random.default_rng(0)
    vals = np.concatenate([rng.normal(0, 1, 2000) * 10.0 ** rng.integers(-40, 38, 2000),
                           [0.0, -0.0, np.inf, -np.inf, np.nan, 1e-40, -1e-45]]).astype(np.float32)
    x = mx.array(vals).astype(mx.bfloat16)
    u16 = np.array(mx.view(x, mx.uint16))
    want = np.array(mx.view(x.astype(mx.float32), mx.uint32))
    got = bf16_to_float32(u16).view(np.uint32)
    assert np.array_equal(got, want)


def test_build_ids_marker_and_suffix(tok):
    prefix = packet_text(INSTRUCTION_A, "Here are some notes:", SLOTS, "That is all.")
    b = build_ids(tok, prefix, ANSWER_SUFFIX)
    ids = b["ids"]
    assert b["n_prefix"] + b["n_suffix"] == len(ids)
    assert [tok.decode([ids[i]]) for i in b["marker_positions"]] == ["[", "END", "]"]
    assert b["readout_position"] == b["n_prefix"] - 1
    assert tok.decode(ids[b["n_prefix"]:]) == ANSWER_SUFFIX
    assert ids == tok.encode(prefix + ANSWER_SUFFIX, add_special_tokens=False)
    nb = build_ids(tok, prefix, None)
    assert nb["ids"] == ids[: b["n_prefix"]] and nb["marker_positions"] == b["marker_positions"]


def test_suffix_merge_is_rejected(tok):
    assert tok.encode("###", add_special_tokens=False) == [13962]  # "#" + "##" merges
    with pytest.raises(SuffixError):
        build_ids(tok, "notes\n#", "##", marker="#")


def test_marker_not_token_aligned_is_rejected(tok):
    with pytest.raises(MarkerError):
        build_ids(tok, "notes\n[END]", None, marker="ND]")


def test_packet_needs_eight_slots():
    with pytest.raises(ValueError):
        packet_text(INSTRUCTION_A, "open", SLOTS[:7], "close")


# -- endpoint validation and edit arithmetic (imports the module, not the server) ----------

@pytest.fixture(scope="module")
def ep():
    from jlens_qwen import capture_endpoint

    return capture_endpoint


DIMS = dict(n_layers=64, d_model=8, vocab_rows=100, fitted=set(range(63)))


def _req(ep, **kw):
    base = dict(input_ids=[1, 2, 3, 4, 5], readout_positions=[4])
    base.update(kw)
    return ep.CaptureRequest(**base)


def _status(ep, req):
    from fastapi import HTTPException

    try:
        ep.validate(req, **DIMS)
    except HTTPException as e:
        return e.status_code
    return 200


def test_validate(ep):
    assert _status(ep, _req(ep)) == 200
    assert _status(ep, _req(ep, input_ids=[1] * (ep.MAX_CAPTURE_TOKENS + 1), readout_positions=[0])) == 413
    assert _status(ep, _req(ep, input_ids=[1, 100])) == 400
    assert _status(ep, _req(ep, readout_positions=[5])) == 400
    assert _status(ep, _req(ep, readout_positions=[3, 2])) == 400
    assert _status(ep, _req(ep, capture_layers=[64])) == 400
    steer = dict(mode="steer", layer=41, positions=[3, 4], alpha=0.0, token_id=7)
    assert _status(ep, _req(ep, edits=[steer])) == 200
    assert _status(ep, _req(ep, edits=[{**steer, "token_id": None}])) == 400
    assert _status(ep, _req(ep, edits=[{**steer, "positions": [4, 3]}])) == 400
    assert _status(ep, _req(ep, edits=[{**steer, "layer": 63}])) == 200
    swap = dict(mode="swap_delta", layer=41, positions=[4], token_id=7, target_id=7)
    assert _status(ep, _req(ep, edits=[swap])) == 400
    ablate = dict(mode="ablate", layer=41, positions=[4], ablate_token_ids=[7], target_norms=[1.0])
    assert _status(ep, _req(ep, edits=[ablate])) == 400
    rows = base64.b64encode(np.zeros((2, 8), np.uint16).tobytes()).decode()
    patch = dict(mode="patch", layer=41, positions=[3, 4], vectors_b64=rows, vectors_dtype="bfloat16")
    assert _status(ep, _req(ep, edits=[patch])) == 200
    assert _status(ep, _req(ep, edits=[{**patch, "positions": [4]}])) == 400


def _h(n=3, d=8, seed=1):
    return mx.array(np.random.default_rng(seed).normal(0, 3, (n, d)).astype(np.float32))


def _fn(ep, payload, **kw):
    e = ep.CaptureEdit(layer=41, positions=list(range(3)), **kw)
    rec: dict = {}
    return ep._edit_fn(e, payload, rec, mx.bfloat16), rec


def test_edit_math_matches_upstream_forms(ep):
    from jlens_qwen.interventions import ablate_rows, gram_inv, make_swap_basis, patch_swap_rows

    h = _h()
    v = _h(1, seed=2)[0]
    fn, _ = _fn(ep, v, mode="steer", alpha=0.5, token_id=1)
    assert mx.array_equal(fn(h), h + 0.5 * v).item()

    V = _h(2, seed=3)
    G = gram_inv(V)
    fn, _ = _fn(ep, (V, G), mode="ablate", alpha=1.0, ablate_token_ids=[1, 2])
    assert mx.array_equal(fn(h), ablate_rows(h, V, G, 1.0)).item()

    Vs, inv = make_swap_basis(V[0], V[1])
    fn, rec = _fn(ep, (Vs, inv), mode="swap_delta", alpha=0.25, token_id=1, target_id=2)
    delta = patch_swap_rows(h, Vs, inv, 1.0) - h
    assert mx.array_equal(fn(h), h + 0.25 * delta).item()
    assert rec["_calls"] == 1


def test_lambda_zero_is_identity_and_norms_match(ep):
    from jlens_qwen.interventions import make_swap_basis

    h = _h()
    V = _h(2, seed=3)
    for mode, payload, kw in [("steer", V[0], {"token_id": 1}),
                              ("swap_delta", make_swap_basis(V[0], V[1]), {"token_id": 1, "target_id": 2})]:
        fn, _ = _fn(ep, payload, mode=mode, alpha=0.0, **kw)
        assert mx.array_equal(fn(h), h).item()
        fn, rec = _fn(ep, payload, mode=mode, target_norms=[2.0, 0.5, 1.0], **kw)
        out = fn(h)
        got = np.array(mx.linalg.norm(out - h, axis=-1))
        assert np.allclose(got, [2.0, 0.5, 1.0], rtol=1e-5)
        assert np.array(rec["_ok"]).all()  # every position defined


def test_norm_floor_leaves_position_unedited(ep):
    h = _h()
    v = mx.array(np.full(8, 1e-6, np.float32))
    fn, rec = _fn(ep, v, mode="steer", token_id=1, target_norms=[1.0, 1.0, 1.0])
    out = fn(h)
    assert mx.array_equal(out, h).item()
    assert not np.array(rec["_ok"]).any()


def test_negative_zero_is_counted(ep):
    h = mx.array(np.array([[-0.0] + [1.0] * 7] * 3, np.float32))
    fn, rec = _fn(ep, mx.zeros((8,)), mode="steer", alpha=0.0, token_id=1)
    fn(h)
    assert int(rec["_neg_zero"].item()) == 3


def test_native_bytes_roundtrip(ep):
    x = (_h(4, 16) * 100).astype(mx.bfloat16)
    y = ep.from_bytes(ep.to_bytes(x), "bfloat16", (4, 16))
    assert mx.array_equal(mx.view(x, mx.uint16), mx.view(y, mx.uint16)).item()


# -- revision 2 (Codex record 2026-09-15, findings 1-4, 7, 8) -------------------------------

def test_ranks_below_top_k_and_ties_by_id(ep):
    logits = np.zeros(5000, np.float32)
    logits[7] = 3.0
    logits[42] = 3.0   # tie with 7: id 7 ranks first
    logits[4000] = -1.0
    order, ranks = ep.ranks_of(logits, [7, 42, 4000, 1])
    assert ranks[:2] == [1, 2] and ranks[2] == 5000 and ranks[3] == 4  # zeros follow in id order: 0 is 3rd, 1 is 4th
    assert order[:3].tolist() == [7, 42, 0]


def _hidden_with_negative_zero():
    base = np.random.default_rng(4).normal(0, 2, (1, 4, 8)).astype(np.float32)
    base[0, 1, 0] = -0.0
    base[0, 2, 3] = -0.0
    return mx.array(base).astype(mx.bfloat16)


def test_zero_dose_preserves_native_bits_through_scatter(ep):
    from jlens_qwen.model import LayerEdit, _apply_edits

    for mode, kw in [("steer", {"token_id": 1}), ("swap_delta", {"token_id": 1, "target_id": 2}),
                     ("ablate", {"ablate_token_ids": [1]})]:
        hidden = _hidden_with_negative_zero()
        before = np.array(mx.view(hidden, mx.uint16))
        e = ep.CaptureEdit(layer=41, positions=[1, 2], alpha=0.0, mode=mode, **kw)
        rec: dict = {}
        out = _apply_edits(hidden, [LayerEdit(layer=41, fn=ep._edit_fn(e, None, rec, mx.bfloat16), positions=(1, 2))], 0)
        mx.eval(out, rec["_written"], rec["_neg_zero"])
        assert np.array_equal(np.array(mx.view(out, mx.uint16)), before), mode
        assert np.array(rec["_written"]).tolist() == [0.0, 0.0] and int(rec["_neg_zero"].item()) == 2
        assert "_raw" not in rec


def test_skipped_norm_position_preserves_native_bits(ep):
    from jlens_qwen.model import LayerEdit, _apply_edits

    hidden = _hidden_with_negative_zero()
    before = np.array(mx.view(hidden, mx.uint16))
    tiny = mx.array(np.full(8, 1e-9, np.float32))
    e = ep.CaptureEdit(layer=41, positions=[1, 2], mode="steer", token_id=1, target_norms=[1.0, 1.0])
    rec: dict = {}
    out = _apply_edits(hidden, [LayerEdit(layer=41, fn=ep._edit_fn(e, tiny, rec, mx.bfloat16), positions=(1, 2))], 0)
    mx.eval(out)
    assert np.array_equal(np.array(mx.view(out, mx.uint16)), before)
    assert not np.array(rec["_ok"]).any()


def test_validate_rejects_dose_conflicts(ep):
    steer = dict(mode="steer", layer=41, positions=[4], token_id=7)
    assert _status(ep, _req(ep, edits=[{**steer, "alpha": 0.0, "target_norms": [1.0]}])) == 400
    assert _status(ep, _req(ep, edits=[{**steer, "target_norms": [1.0]}])) == 200
    rows = base64.b64encode(np.zeros((1, 8), np.uint16).tobytes()).decode()
    patch = dict(mode="patch", layer=41, positions=[4], vectors_b64=rows, vectors_dtype="bfloat16")
    assert _status(ep, _req(ep, edits=[{**patch, "alpha": 0.5}])) == 400
    assert ep.is_zero_dose(ep.CaptureEdit(**{**steer, "alpha": 0.0}))
    assert not ep.is_zero_dose(ep.CaptureEdit(**{**patch, "alpha": 0.0}))


def test_basis_condition(ep):
    assert ep.basis_condition(np.array([[1.0, 0.0], [2.0, 0.0]])) == float("inf")
    assert ep.basis_condition(np.array([[1.0, 0.0], [0.0, 1.0]])) == 1.0
    assert ep.basis_condition(np.array([[np.nan, 0.0], [0.0, 1.0]])) == float("inf")


def _write_gate(logs, n_prompts, identity="id-A", client=None, qualifying=True, tamper=False):
    import capture as cap_mod

    client = client or {"t1_access/capture.py": "c1"}
    stamp = f"20260915T00{n_prompts:04d}"
    ev = logs / f"parity_{stamp}.jsonl"
    lines = [{"header": "parity", "startup_identity_sha256": identity,
              "prompts": [{"index": i} for i in range(n_prompts)]}]
    for i in range(n_prompts):
        for gate, need in cap_mod.REQUIRED_PER_PROMPT.items():
            for _ in range(need):
                lines.append({"gate": gate, "prompt": i, "required": True, "pass": True})
    ev.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    rep = {"verdict": "PASS", "qualifying": qualifying, "startup_identity_sha256": identity, "client_sha256": client,
           "rsc_dirty_paths": "", "evidence": ev.name, "evidence_sha256": cap_mod.sha256_file(ev)}
    if tamper:
        ev.write_text(ev.read_text().replace('"pass": true', '"pass": false', 1))
    (logs / f"parity_{stamp}.json").write_text(json.dumps(rep))


def test_gate_admission_rule(tmp_path):
    import capture as cap_mod

    prov = {"startup_identity_sha256": "id-A", "client_sha256": {"t1_access/capture.py": "c1"}}
    _write_gate(tmp_path, 1)
    name, why = cap_mod.matching_parity(prov, tmp_path)
    assert name is None and "re-count" in " ".join(why)
    _write_gate(tmp_path, 20)
    name, _ = cap_mod.matching_parity(prov, tmp_path)
    assert name == "parity_20260915T000020.json"
    assert cap_mod.matching_parity({**prov, "startup_identity_sha256": "id-B"}, tmp_path)[0] is None
    assert cap_mod.matching_parity({**prov, "client_sha256": {"t1_access/capture.py": "c2"}}, tmp_path)[0] is None


def test_gate_admission_rejects_altered_evidence(tmp_path):
    import capture as cap_mod

    _write_gate(tmp_path, 20, tamper=True)
    prov = {"startup_identity_sha256": "id-A", "client_sha256": {"t1_access/capture.py": "c1"}}
    name, why = cap_mod.matching_parity(prov, tmp_path)
    assert name is None and "altered" in " ".join(why)


def test_observables_sha_covers_every_array():
    import capture as cap_mod

    rows = {name: np.arange(6, dtype=np.int32) for name in cap_mod.OBSERVABLES}
    base = cap_mod.observables_sha(rows, 1.5)
    for name in cap_mod.OBSERVABLES:
        changed = dict(rows)
        changed[name] = rows[name].copy()
        changed[name][0] += 1
        assert cap_mod.observables_sha(changed, 1.5) != base
    assert cap_mod.observables_sha(rows, 1.25) != base

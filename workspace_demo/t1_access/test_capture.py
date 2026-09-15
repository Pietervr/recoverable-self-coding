"""Offline tests for the T1 capture path (no model load): packet ids, bf16 decoding,
request validation and the edit arithmetic of jlens_qwen/capture_endpoint.py.

Run with the upstream environment (mlx, fastapi and the tokenizer live there):
    workspace_demo/upstream/jlens-qwen36/.venv/bin/python -m pytest workspace_demo/t1_access/test_capture.py -q
"""

from __future__ import annotations

import base64
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

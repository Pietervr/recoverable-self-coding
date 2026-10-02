"""Photograph arm, desk gate ask 3: the image adapter (framework §3, §8.4).

DESIGN (an engineering call, reported): the instrumented image path IS the text arm's capture path. The text arm's
single-pass capture (`jlens_qwen.capture_endpoint._run` + `validate`, patch t1-capture-2: a new StreamSession per
request, ONE `extend` over all ids, edits inside the pass, residuals at the readout positions, closed-set logits and
ranks at the final position) runs in-process and unmodified. Two things are added and nothing else changes:

  1. an embedding injector on the mlx_lm text model's `embed_tokens`: for a registered image sequence it returns the
     token embeddings with the image-pad rows replaced by mlx-vlm 0.6.3's qwen3_5 vision tower output, merged by
     mlx-vlm's own `merge_input_ids_with_image_features` (the native merge);
  2. the 16 full-attention layers' 1-D `nn.RoPE` replaced by mlx-vlm's interleaved M-RoPE, fed the multimodal
     (t, h, w) positions from mlx-vlm's own `get_rope_index` for the registered sequence, and 1-D positions tiled
     over (t, h, w) otherwise.

Measured before the build (runtime_agreement.py / runtime_agreement.json, text only, no image, no pool concept):
mlx-vlm's separate qwen3_5 language stack and the jlens/mlx_lm StreamSession agree BITWISE on all 64 layers and the
logits; the M-RoPE swap is bitwise equal to nn.RoPE on 1-D positions, live on unequal (t, h, w) positions, and
bitwise equal to mlx-vlm there. So the image arm runs the text arm's runtime; the vision tower, merge and positions
are mlx-vlm's. The native reference (`native_forward`) is mlx-vlm's own prefill as `generate_step` runs it for an
unchunked prompt: `get_input_embeddings` then `language_model(ids, inputs_embeds, cache)`, in its own process.

TEMPLATE (proposed by R084 for the row-20 review; the image analogue of stimuli/packet.py): raw ids, no chat
template, no thinking block - matched to the text arm (PREREGISTRATION_T1_model.md §4: "no chat template");

    <instruction>
    <carrier open>
    <|vision_start|><|image_pad|> x 144<|vision_end|>
    <carrier close>
    [END]
  + "\\nAnswer:" (tokenized separately under the join assertion of packet.build_ids)

The marker, suffix and join rules are packet.build_ids' own, applied to the unexpanded prefix; the single image pad
is then expanded to the merged-token count of the image grid and every later index shifted. The expansion is checked
against mlx-vlm's processor (`check_against_processor`).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
T1 = HERE.parents[1]
UPSTREAM = T1.parent / "upstream" / "jlens-qwen36"
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
LENS = UPSTREAM / "data" / "lens" / "qwen36_27b_neuronpedia_n1000.npz"
if str(T1) not in sys.path:
    sys.path.insert(0, str(T1))

from stimuli.packet import ANSWER_SUFFIX, MARKER, build_ids  # noqa: E402

INSTRUCTION = "Look at the picture below; afterwards, name in one word what is shown."
CARRIERS = [("Here is a photograph someone took:", "That was the whole photograph."),
            ("A camera captured the following picture:", "Nothing else was in the picture.")]
VISION_START, IMAGE_PAD, VISION_END = "<|vision_start|>", "<|image_pad|>", "<|vision_end|>"
IMAGE_SPAN = VISION_START + IMAGE_PAD + VISION_END
FA_LAYERS = [i for i in range(64) if (i + 1) % 4 == 0]
TEMPLATE = {"instruction": INSTRUCTION, "carriers": CARRIERS, "image_span": IMAGE_SPAN, "marker": MARKER,
            "suffix": ANSWER_SUFFIX, "chat_template": None, "thinking": "none (raw ids, no chat template)",
            "layout": "instruction / carrier open / image span / carrier close / [END], newline-joined"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def template_sha256() -> str:
    return sha256_bytes(json.dumps(TEMPLATE, sort_keys=True).encode())


def positions_sha256(pos) -> str:
    """Positions hashed as int64 [3, 1, L] whatever dtype the producer used, so both paths compare."""
    return sha256_bytes(np.ascontiguousarray(np.asarray(np.array(pos)).astype(np.int64)).tobytes())


def prefix_text(carrier: int) -> str:
    o, c = CARRIERS[carrier]
    return "\n".join([INSTRUCTION, o, IMAGE_SPAN, c, MARKER])


def build_sequence(tok, carrier: int, grid_thw: list[int], merge: int = 2, suffix: bool = True) -> dict:
    """The complete id sequence for one image trial and every index derived from it."""
    built = build_ids(tok, prefix_text(carrier), ANSWER_SUFFIX if suffix else None)
    ids = built["ids"]
    pad_id, vs_id, ve_id = (tok.convert_tokens_to_ids(t) for t in (IMAGE_PAD, VISION_START, VISION_END))
    if ids.count(pad_id) != 1 or ids.count(vs_id) != 1 or ids.count(ve_id) != 1:
        raise ValueError("the unexpanded prefix must hold exactly one image span")
    p = ids.index(pad_id)
    if ids[p - 1] != vs_id or ids[p + 1] != ve_id:
        raise ValueError("the image pad is not between vision_start and vision_end")
    t, h, w = grid_thw
    n_img = t * h * w // (merge * merge)
    shift = n_img - 1
    full = ids[:p] + [pad_id] * n_img + ids[p + 1:]
    marker = [m + shift for m in built["marker_positions"]]
    out = {"ids": full, "n": len(full), "carrier": carrier, "grid_thw": list(grid_thw), "n_image_tokens": n_img,
           "image_span": [p, p + n_img], "vision_start": p - 1, "vision_end": p + n_img,
           "marker_positions": marker, "readout_position": marker[-1],
           "suffix_positions": list(range(built["n_prefix"] + shift, len(full))) if suffix else [],
           "final_position": len(full) - 1, "n_prefix": built["n_prefix"] + shift, "n_suffix": built["n_suffix"]}
    if full[marker[0]:marker[-1] + 1] != ids[built["marker_positions"][0]:built["marker_positions"][-1] + 1]:
        raise ValueError("marker ids moved under expansion")
    out["ids_sha256"] = sha256_bytes(np.asarray(full, dtype=np.int64).tobytes())
    return out


def check_against_processor(processor, seq: dict, image, suffix: bool = True) -> dict:
    """mlx-vlm's processor on the same text and image must give the same expanded ids and grid."""
    text = prefix_text(seq["carrier"]) + (ANSWER_SUFFIX if suffix else "")
    out = processor(text=[text], images=[image], return_tensors="np", padding=False)
    pids = np.asarray(out["input_ids"])[0].tolist()
    grid = np.asarray(out["image_grid_thw"]).tolist()[0]
    return {"ids_equal": pids == seq["ids"], "grid_equal": list(grid) == seq["grid_thw"],
            "processor_n": len(pids), "pixel_values_sha256": sha256_bytes(
                np.ascontiguousarray(np.asarray(out["pixel_values"], dtype=np.float32)).tobytes())}


class MRope:
    """Stands in for nn.RoPE inside an mlx_lm full-attention layer: rope(x, offset). With `holder['position_ids']`
    set it applies mlx-vlm's interleaved M-RoPE at those (3, 1, L) positions sliced at the offset; with it None it
    uses 1-D positions tiled over (t, h, w), measured bitwise equal to nn.RoPE."""

    def __init__(self, rotary_emb, holder: dict):
        self.rotary_emb, self.holder = rotary_emb, holder

    def __call__(self, x, offset=0):
        import mlx.core as mx
        L = x.shape[2]
        pos = self.holder.get("position_ids")
        if pos is None:
            pos = mx.tile(mx.arange(offset, offset + L)[None, None, :], (3, 1, 1))
        else:
            if pos.shape[-1] < offset + L:
                raise ValueError("registered positions shorter than the sequence")
            pos = pos[:, :, offset:offset + L]
            calls = self.holder.setdefault("calls", [])  # the effective positions, one record per rope call
            calls.append((int(offset), int(L)))
            if len(calls) == 1:
                self.holder["effective"] = pos
        out, _ = self.rotary_emb.apply_rotary(x, x, pos, unsqueeze_dim=1)
        return out


class EmbedInjector:
    """Wraps the text model's embed_tokens. With a registered image sequence, the next call on exactly those ids
    returns the native merge of the token embeddings and the vision features; any other call is the plain
    embedding. Counts every injection; a registration is consumed once."""

    def __init__(self, embed, merge_fn, image_token_id: int, video_token_id: int):
        self.embed, self.merge_fn = embed, merge_fn
        self.image_token_id, self.video_token_id = image_token_id, video_token_id
        self.pending = None
        self.injections = 0
        self.calls = 0                      # every embed call, registered or not: one per decoder prefill
        self.last_merge: dict | None = None

    def __call__(self, ids):
        import mlx.core as mx
        self.calls += 1
        h = self.embed(ids)
        if self.pending is None:
            return h
        want, feats = self.pending
        got = np.array(ids).reshape(-1).tolist()
        if got != want:
            raise RuntimeError("embed call on ids other than the registered image sequence")
        fh = feats.astype(h.dtype)
        merged, _ = self.merge_fn(fh, h, ids, self.image_token_id, self.video_token_id)
        # The merge, verified bitwise: image-pad rows are the features in order, every other row the token embedding.
        span = [i for i, t in enumerate(got) if t == self.image_token_id]
        other = [i for i, t in enumerate(got) if t != self.image_token_id]
        u16 = lambda a: mx.view(a, mx.uint16) if a.dtype == mx.bfloat16 else a
        img_ok = mx.array_equal(u16(merged[0, mx.array(span)]), u16(fh))
        txt_ok = mx.array_equal(u16(merged[0, mx.array(other)]), u16(h[0, mx.array(other)]))
        mx.eval(img_ok, txt_ok, merged)
        self.last_merge = {"image_rows_equal_features": bool(img_ok.item()),
                           "text_rows_equal_embeddings": bool(txt_ok.item()), "n_image_rows": len(span),
                           "image_rows_contiguous": span == list(range(span[0], span[0] + len(span))) if span else False,
                           "merged_sha256": sha256_bytes(np.ascontiguousarray(np.array(u16(merged))).tobytes()),
                           "dtype": str(merged.dtype)}
        self.pending = None
        self.injections += 1
        return merged


class ImageInstrument:
    """The instrumented image path: the jlens/mlx_lm model with the text arm's capture code, the mlx-vlm vision
    tower, the native merge and M-RoPE. One `capture` is one model pass (vision tower + one extend)."""

    def __init__(self, snapshot: Path = SNAPSHOT, lens_path: Path = LENS):
        import mlx.core as mx
        from mlx_vlm import load as vload
        from mlx_vlm.models.qwen3_5.language import Qwen3_5RotaryEmbedding
        from mlx_vlm.models.qwen3_5.qwen3_5 import Model as VModel

        from jlens_qwen import capture_endpoint as ce
        from jlens_qwen.lens import JacobianLens
        from jlens_qwen.model import load as lload

        self.mx, self.ce = mx, ce
        vmodel, self.processor = vload(str(snapshot), lazy=True)
        self.vision = vmodel.vision_tower
        mx.eval(self.vision.parameters())
        self._rope_lm = vmodel.language_model                 # get_rope_index needs only its config
        self._rope_lm.model.layers = []                       # the language weights come from mlx_lm, never twice
        self._rope_lm.model.embed_tokens = None
        if hasattr(self._rope_lm, "lm_head"):
            self._rope_lm.lm_head = None
        self.vconfig = vmodel.config
        del vmodel

        self.model = lload(str(snapshot))
        self.lens = JacobianLens.load(str(lens_path))
        self.lens.warm()
        self.S = SimpleNamespace(_model=self.model, _lens=self.lens)
        cfg = json.loads((snapshot / "config.json").read_text())
        tc, rp = cfg["text_config"], cfg["text_config"]["rope_parameters"]
        self.holder: dict = {"position_ids": None}
        for i in FA_LAYERS:
            rot = Qwen3_5RotaryEmbedding(int(tc["head_dim"] * rp["partial_rotary_factor"]),
                                         max_position_embeddings=tc["max_position_embeddings"],
                                         base=rp["rope_theta"], mrope_section=rp["mrope_section"])
            self.model.layers[i].self_attn.rope = MRope(rot, self.holder)
        text = self.model._text_module
        self.injector = EmbedInjector(text.embed_tokens, VModel.merge_input_ids_with_image_features,
                                      cfg["image_token_id"], cfg["video_token_id"])
        ce._get_hidden_dtype(self.S)        # _run's one-off dtype probe (embed of [[0]]), resolved before any
        text.embed_tokens = self.injector   # registration so the injector only ever sees trial sequences
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(str(snapshot))   # the text arm's tokenizer (capture.py)
        self.passes = 0

    def vision_features(self, pixel_values: np.ndarray, grid_thw: list[int]):
        mx = self.mx
        dtype = self.vision.patch_embed.proj.weight.dtype
        feats, _ = self.vision(mx.array(pixel_values).astype(dtype), mx.array([grid_thw]))
        mx.eval(feats)
        return feats

    def positions(self, ids: list[int], grid_thw: list[int]):
        mx = self.mx
        pos, deltas = self._rope_lm.get_rope_index(mx.array([ids]), mx.array([grid_thw]))
        mx.eval(pos)
        return pos, deltas

    def capture(self, seq: dict, pixel_values: np.ndarray, *, capture_layers=None, request_token_ids=(),
                top_k: int = 1000, edits=None, readout_positions=None) -> dict:
        """One instrumented pass through the text arm's `_run`. Returns its result plus the image identity and the
        projected visual-token boundary (FP32 mean over the merged tokens, and its hash)."""
        mx, ce = self.mx, self.ce
        feats = self.vision_features(pixel_values, seq["grid_thw"])
        if feats.shape[0] != seq["n_image_tokens"]:
            raise RuntimeError(f"vision features {feats.shape[0]} != image tokens {seq['n_image_tokens']}")
        pos, _ = self.positions(seq["ids"], seq["grid_thw"])
        req = ce.CaptureRequest(input_ids=seq["ids"], readout_positions=readout_positions or seq["marker_positions"],
                                capture_layers=capture_layers, request_token_ids=list(request_token_ids),
                                top_k=top_k, edits=edits)
        fitted = set(self.lens.source_layers)
        ce.validate(req, n_layers=self.model.n_layers, d_model=self.model.d_model,
                    vocab_rows=int(self.model._lm_head.weight.shape[0]), fitted=fitted)
        before, calls_before = self.injector.injections, self.injector.calls
        self.holder.update(position_ids=pos, calls=[], effective=None)
        self.injector.pending = (seq["ids"], feats)
        self.injector.last_merge = None
        try:
            out = ce._run(self.S, req)
        finally:
            self.holder["position_ids"] = None
            self.injector.pending = None
        self.passes += 1
        if self.injector.injections != before + 1:
            raise RuntimeError("the image embedding was not injected exactly once")
        rope_calls = list(self.holder.get("calls") or [])
        eff = self.holder.get("effective")
        f32 = feats.astype(mx.float32)
        finite = mx.all(mx.isfinite(f32))
        boundary = mx.mean(f32, axis=0)
        mx.eval(boundary, finite)
        b = np.array(boundary)
        out["image"] = {"pixel_values_sha256": sha256_bytes(np.ascontiguousarray(
                            np.asarray(pixel_values, dtype=np.float32)).tobytes()),
                        "grid_thw": seq["grid_thw"], "n_image_tokens": int(feats.shape[0]),
                        "features_shape": list(feats.shape), "features_dtype": str(feats.dtype),
                        "features_all_finite": bool(finite.item()),
                        "positions_sha256": positions_sha256(pos),
                        "effective_positions_sha256": positions_sha256(eff) if eff is not None else None,
                        "rope_calls": rope_calls,
                        "embed_calls_this_pass": self.injector.calls - calls_before,
                        "merge": self.injector.last_merge,
                        "features_sha256": sha256_bytes(np.ascontiguousarray(np.array(f32)).tobytes()),
                        "boundary_label": "FP32 mean over the 144 projected visual tokens + full-token sha256",
                        "boundary_mean_fp32_b64": __import__("base64").b64encode(b.tobytes()).decode("ascii"),
                        "boundary_mean_sha256": sha256_bytes(b.tobytes()),
                        "boundary_mean_all_finite": bool(np.all(np.isfinite(b)))}
        out["positions_array"] = np.asarray(np.array(pos)).astype(np.int64)
        return out


def native_forward(vmodel, seq: dict, pixel_values: np.ndarray, capture_layers, positions) -> dict:
    """mlx-vlm's own prefill for an unchunked prompt, as generate_step runs it: get_input_embeddings, then
    language_model(ids, inputs_embeds, cache) - no capture_layer_ids (that switches mlx-vlm to its speculative
    verify kernels). Residuals are read by transparent proxies around the decoder layers, which only record the
    output of each call. Returns FP32 residuals [L, P, D] at `positions` and the final-position logits."""
    import mlx.core as mx
    inner = vmodel.language_model.model
    rec: dict = {}

    class _Proxy:
        def __init__(self, layer, i):
            self.__dict__["_layer"], self.__dict__["_i"] = layer, i

        def __getattr__(self, k):
            return getattr(self._layer, k)

        def __call__(self, *a, **kw):
            calls[self._i] = calls.get(self._i, 0) + 1
            if self._i in FA_LAYERS and "position_ids" not in seen:
                seen["position_ids"] = kw.get("position_ids")
            h = self._layer(*a, **kw)
            if self._i in capture_layers:
                rec[self._i] = h
            return h

    calls: dict = {}
    seen: dict = {}
    originals = list(inner.layers)
    inner.layers = [_Proxy(l, i) for i, l in enumerate(originals)]
    try:
        ids = mx.array([seq["ids"]])
        grid = mx.array([seq["grid_thw"]])
        emb = vmodel.get_input_embeddings(ids, mx.array(pixel_values), mask=None, image_grid_thw=grid)
        out = vmodel.language_model(ids, inputs_embeds=emb.inputs_embeds, cache=vmodel.language_model.make_cache(),
                                    image_grid_thw=grid)
        logits = out.logits[0, -1]
        pos = mx.array(positions)
        stack = mx.stack([rec[l][0, pos] for l in capture_layers]).astype(mx.float32)
        e = emb.inputs_embeds
        mx.eval(logits, stack, e)
    finally:
        inner.layers = originals
    u16 = mx.view(e, mx.uint16) if e.dtype == mx.bfloat16 else e
    eff = seen.get("position_ids")
    return {"residuals": np.array(stack), "logits": np.array(logits.astype(mx.float32)),
            "decoder_calls": {"min": min(calls.values()), "max": max(calls.values()), "layers": len(calls)},
            "effective_positions_sha256": positions_sha256(eff) if eff is not None else None,
            "inputs_embeds_sha256": sha256_bytes(np.ascontiguousarray(np.array(u16)).tobytes()),
            "inputs_embeds_dtype": str(e.dtype)}

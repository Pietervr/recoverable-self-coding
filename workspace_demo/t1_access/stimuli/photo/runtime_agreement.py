"""Photograph arm, ask 3 engineering diagnostic: do the two qwen3_5 language implementations agree on TEXT?

The text arm's instrumented path is jlens_qwen's StreamSession over the mlx_lm Qwen3.5 model (one cached `extend`
over raw input ids, GDN stock kernel in inference mode, 1-D RoPE via nn.RoPE). mlx-vlm 0.6.3 carries a separate
qwen3_5 language implementation with interleaved M-RoPE. Before choosing how the image adapter is built (framework
§8.4: "any text-template or runtime change is reported as another factor"), this measures, on ONE short text prompt
that names no pool concept and holds no image:

  lm        the jlens StreamSession path, all 64 post-layer residuals and the final-position logits;
  lm_mrope  the same path with the 16 full-attention layers' nn.RoPE replaced by mlx-vlm's interleaved M-RoPE
            (Option B's only language-side change), fed 1-D positions tiled over (t, h, w) - should equal `lm`;
  vlm       mlx-vlm's own Qwen3_5Model over the same ids with its own cache, all 64 layers and the logits.

Each mode runs in its own process (`python runtime_agreement.py lm|vlm`, then `compare`) and saves FP32 arrays to
the scratch directory given by T1_PHOTO_ENG_DIR. Every model pass is logged through enforce.Budget in a SEPARATE
engineering state file (engineering_state.json, never row 20's): this establishes nothing about Stage A.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("T1_PHOTO_ENG_DIR", HERE / "engineering"))
SNAPSHOT = Path.home() / (".cache/huggingface/hub/models--mlx-community--Qwen3.6-27B-4bit/snapshots/"
                          "c000ac2c2057d94be3fa931000c31723aac53282")
PROMPT = "The river runs slowly past the old stone bridge, and the evening light settles on the water."
FA_LAYERS = [i for i in range(64) if (i + 1) % 4 == 0]


def _ctl_positions(n: int):
    """A CONTROL position grid with t, h, w unequal (t = i, h = i // 3, w = i % 3), as image tokens will have. Run
    through both implementations it must (a) differ from the 1-D result, proving the swap is live, and (b) agree
    between them, proving the two M-RoPE paths match on non-trivial multimodal positions."""
    import mlx.core as mx
    i = mx.arange(n)
    return mx.stack([i, i // 3, i % 3])[:, None, :]


def _budget(identity: str):
    sys.path.insert(0, str(HERE))
    from enforce import Budget
    return Budget(OUT / "engineering_state.json", "row20", identity, [OUT])


def _ids() -> list[int]:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(SNAPSHOT)
    return tok.encode(PROMPT, add_special_tokens=False)


def _save(name: str, acts: dict, logits, ids, extra: dict) -> None:
    import mlx.core as mx
    H = np.stack([np.array(acts[i][0].astype(mx.float32)) for i in range(64)])      # [64, L, D]
    np.savez(OUT / f"{name}.npz", H=H, logits=np.array(logits.astype(mx.float32)), ids=np.array(ids))
    (OUT / f"{name}.json").write_text(json.dumps(extra, indent=1))


class _MRope:
    """Stands in for nn.RoPE inside an mlx_lm attention layer: rope(x, offset) -> x rotated at explicit (3, B, L)
    multimodal positions held by `holder`, sliced at the cache offset."""

    def __init__(self, rotary_emb, holder: dict):
        self.rotary_emb, self.holder = rotary_emb, holder

    def __call__(self, x, offset=0):
        L = x.shape[2]
        pos = self.holder["position_ids"][:, :, offset:offset + L]
        out, _ = self.rotary_emb.apply_rotary(x, x, pos, unsqueeze_dim=1)
        return out


def run_lm() -> None:
    import mlx.core as mx
    from jlens_qwen.model import load
    ids = _ids()
    m = load(str(SNAPSHOT))
    budget = _budget("eng-runtime-agreement")
    with budget.attempt(f"lm-{time.time():.0f}", "diagnostic", passes=1):
        logits, acts = m.make_stream(capture_layers=range(64)).extend(ids)
    _save("lm", acts, logits, ids, {"mode": "lm", "n_ids": len(ids)})

    from mlx_vlm.models.qwen3_5.language import Qwen3_5RotaryEmbedding
    cfg = json.loads((SNAPSHOT / "config.json").read_text())["text_config"]
    rp = cfg["rope_parameters"]
    holder = {"position_ids": mx.tile(mx.arange(len(ids))[None, None, :], (3, 1, 1))}
    swapped = []
    for i in FA_LAYERS:
        attn = m.layers[i].self_attn
        rot = Qwen3_5RotaryEmbedding(int(cfg["head_dim"] * rp["partial_rotary_factor"]),
                                     max_position_embeddings=cfg["max_position_embeddings"],
                                     base=rp["rope_theta"], mrope_section=rp["mrope_section"])
        swapped.append({"layer": i, "nn_rope": repr(attn.rope)})
        attn.rope = _MRope(rot, holder)
    with budget.attempt(f"lm_mrope-{time.time():.0f}", "diagnostic", passes=1):
        logits, acts = m.make_stream(capture_layers=range(64)).extend(ids)
    _save("lm_mrope", acts, logits, ids, {"mode": "lm_mrope", "swapped": swapped,
                                          "mrope_section": rp["mrope_section"]})
    holder["position_ids"] = _ctl_positions(len(ids))
    with budget.attempt(f"lm_mrope_ctl-{time.time():.0f}", "diagnostic", passes=1):
        logits, acts = m.make_stream(capture_layers=range(64)).extend(ids)
    _save("lm_mrope_ctl", acts, logits, ids, {"mode": "lm_mrope_ctl", "positions": "t=i, h=i//3, w=i%3",
                                              "text_model_class": type(m._text_module).__module__})
    print(json.dumps(budget.state["counters"]["row20"]))


def run_vlm() -> None:
    import mlx.core as mx
    from mlx_vlm import load
    ids = _ids()
    model, _ = load(str(SNAPSHOT))
    lm = model.language_model
    inner = lm.model
    sec = [inner.layers[i].self_attn.rotary_emb.mrope_section for i in FA_LAYERS]
    budget = _budget("eng-runtime-agreement")
    sink: list = []
    with budget.attempt(f"vlm-{time.time():.0f}", "diagnostic", passes=1):
        normed = inner(mx.array([ids]), cache=lm.make_cache(), capture_layer_ids=list(range(64)), hidden_sink=sink)
        head = lm.lm_head if hasattr(lm, "lm_head") and lm.lm_head is not None else None
        logits = (head(normed[:, -1, :]) if head is not None else inner.embed_tokens.as_linear(normed[:, -1, :]))[0]
        mx.eval(logits, *sink)
    _save("vlm", dict(enumerate(sink)), logits, ids,
          {"mode": "vlm", "mrope_section_used": sec[0], "all_fa_same": all(s == sec[0] for s in sec),
           "lm_head": head is not None, "text_model_class": type(inner).__module__})
    sink = []
    with budget.attempt(f"vlm_ctl-{time.time():.0f}", "diagnostic", passes=1):
        normed = inner(mx.array([ids]), cache=lm.make_cache(), position_ids=_ctl_positions(len(ids)),
                       capture_layer_ids=list(range(64)), hidden_sink=sink)
        logits = (head(normed[:, -1, :]) if head is not None else inner.embed_tokens.as_linear(normed[:, -1, :]))[0]
        mx.eval(logits, *sink)
    _save("vlm_ctl", dict(enumerate(sink)), logits, ids, {"mode": "vlm_ctl", "positions": "t=i, h=i//3, w=i%3"})
    print(json.dumps(budget.state["counters"]["row20"]))


def compare() -> None:
    res = {}
    for ref, other in (("lm", "lm_mrope"), ("lm", "vlm"), ("lm", "lm_mrope_ctl"), ("lm_mrope_ctl", "vlm_ctl")):
        base, o = np.load(OUT / f"{ref}.npz"), np.load(OUT / f"{other}.npz")
        assert (o["ids"] == base["ids"]).all()
        a, b = base["H"].astype(np.float64), o["H"].astype(np.float64)
        rel_last = np.linalg.norm(a[:, -1] - b[:, -1], axis=-1) / np.linalg.norm(a[:, -1], axis=-1)
        rel_all = np.linalg.norm((a - b).reshape(64, -1), axis=-1) / np.linalg.norm(a.reshape(64, -1), axis=-1)
        la, lb = base["logits"], o["logits"]
        res[f"{other}_vs_{ref}"] = {"bitwise_equal_layers": int(sum(np.array_equal(base["H"][i], o["H"][i]) for i in range(64))),
                      "rel_l2_last_max": float(rel_last.max()), "rel_l2_last_argmax_layer": int(rel_last.argmax()),
                      "rel_l2_all_max": float(rel_all.max()),
                      "rel_l2_last_by_layer": [round(float(x), 6) for x in rel_last],
                      "logit_max_abs": float(np.abs(la - lb).max()),
                      "argmax_equal": bool(la.argmax() == lb.argmax()), "argmax": [int(la.argmax()), int(lb.argmax())]}
    res["n_ids"] = int(len(base["ids"]))
    res["text_model_class"] = {n: json.loads((OUT / f"{n}.json").read_text()).get("text_model_class")
                               for n in ("lm_mrope_ctl", "vlm")}
    res["prompt"] = PROMPT
    res["inputs_sha256"] = {n: hashlib.sha256((OUT / f"{n}.npz").read_bytes()).hexdigest()
                            for n in ("lm", "lm_mrope", "vlm", "lm_mrope_ctl", "vlm_ctl")}
    (OUT / "runtime_agreement.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "rel_l2_last_by_layer"}
                      if isinstance(v, dict) else v for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    {"lm": run_lm, "vlm": run_vlm, "compare": compare}[sys.argv[1]]()

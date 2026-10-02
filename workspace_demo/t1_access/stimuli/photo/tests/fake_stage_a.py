"""A fake instrument for the Stage A runner's tests: no model is imported, loaded or run.

It returns capture results with the real runner's structure, built deterministically from the ids, so the runner's
gates, transaction, recovery and report can be exercised end to end. The residual width is shrunk (D_MODEL = 16)
to keep the test outputs small. Faults are injected by the `faults` dict.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

PHOTO = Path(__file__).resolve().parents[1]
T1 = PHOTO.parents[1]
for p in (str(PHOTO), str(T1)):
    if p not in sys.path:
        sys.path.insert(0, p)

import stage_a  # noqa: E402

D = 16
VOCAB = 1000


def _h(*parts) -> bytes:
    return hashlib.sha256("|".join(map(str, parts)).encode()).digest()


class FakeEdit:
    def __init__(self, **kw):
        self.alpha = 1.0                                    # CaptureEdit's default
        self.__dict__.update(kw)


class FakeCE:
    CaptureEdit = FakeEdit


class FakeImageProcessor:
    pass


class FakeProcessor:
    image_processor = FakeImageProcessor()


class FakeInstrument:
    def __init__(self, plan: dict, faults: dict):
        from transformers import AutoTokenizer
        from image_adapter import SNAPSHOT
        self.ce, self.processor, self.plan, self.faults = FakeCE(), FakeProcessor(), plan, faults
        self.tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
        self.calls = 0
        self.by_ids = {}

    def capture(self, seq, pv, *, capture_layers, request_token_ids, top_k, edits):
        self.calls += 1
        if self.faults.get("exit_at_call") == self.calls:
            os._exit(9)                                     # a crash mid-attempt
        if self.faults.get("sleep_at_call") == self.calls:
            t = time.monotonic()
            while time.monotonic() - t < 30:               # busy, interruptible work
                time.sleep(0.05)
        n = seq["n"]
        m = seq["marker_positions"]
        prefix = seq["ids"][: m[-1] + 1]
        mode = None
        alpha = 0.0
        if edits:
            mode, alpha = edits[0].mode, float(getattr(edits[0], "alpha", 1.0))
        moved = bool(edits) and mode != "patch" and alpha != 0.0
        eff = mode if moved else None
        idx = int(np.asarray(pv).reshape(-1)[0])
        fault = tuple(self.faults.get("differ") or ()) == (idx, self.case_of(edits, seq))
        res = np.frombuffer(_h("res", prefix, eff, fault) * (64 * 3 * D * 2 // 32), dtype=np.uint16)
        res = res.reshape(64, 3, D) & 0x3FFF                 # finite bf16 patterns
        rb = res.tobytes()
        logits = np.frombuffer(_h("logit", seq["ids"], eff, fault) * (VOCAB * 4 // 32),
                               dtype=np.uint32).astype(np.float64) / 2**32
        pos_sha = self.plan["inputs"][idx]["expected"]["positions_sha256"]
        x = self.plan["inputs"][idx]
        return {"n_tokens": n, "input_ids_sha256": seq["ids_sha256"], "readout_positions": list(m),
                "capture_layers": list(capture_layers), "gdn_inference_kernel": True,
                "edits_installed": edits is not None, "edit_log": [{"mode": mode}] * len(edits or []),
                "residuals": {"dtype": "bfloat16", "shape": [64, 3, D], "b64": base64.b64encode(rb).decode(),
                              "sha256": hashlib.sha256(rb).hexdigest()},
                "final_logits": {"dtype": "bfloat16", "n": VOCAB, "sha256": hashlib.sha256(logits.tobytes()).hexdigest()},
                "logsumexp": 1.0, "requested": [{"id": t, "logit": float(logits[t % VOCAB]), "rank": 1}
                                                for t in request_token_ids],
                "top_ids": [0], "top_logits": [0.0], "timing_s": {"total": 0.0},
                "image": {"pixel_values_sha256": x["pixel_values_sha256"], "grid_thw": x["grid_thw"],
                          "n_image_tokens": 144, "features_shape": [144, D], "features_dtype": "bfloat16",
                          "features_all_finite": True, "positions_sha256": pos_sha,
                          "effective_positions_sha256": pos_sha, "rope_calls": [(0, n)] * 32,
                          "embed_calls_this_pass": 1,
                          "merge": {"image_rows_equal_features": True, "text_rows_equal_embeddings": True,
                                    "n_image_rows": 144, "image_rows_contiguous": True,
                                    "merged_sha256": hashlib.sha256(_h("emb", idx)).hexdigest()},
                          "features_sha256": hashlib.sha256(_h("feat", x["pixel_values_sha256"])).hexdigest(),
                          "boundary_mean_all_finite": True}}

    def case_of(self, edits, seq):
        if edits is None:
            return "plain-like"
        if not edits:
            return "empty"
        e = edits[0]
        return {"steer": "zero_steer", "ablate": "zero_ablate" if e.alpha == 0 else "ablate1",
                "swap_delta": "zero_swap" if e.alpha == 0 else "swap1", "patch": "self_patch"}[e.mode]


def fake_pixels(x, image_processor):
    """The frozen hashes, and a tiny tensor carrying the input index (the fake instrument reads it)."""
    return {"pv": np.full((4, 4), x["index"], dtype=np.float32), "grid": x["grid_thw"], "png_sha256": x["png_sha256"],
            "pixel_values_sha256": x["pixel_values_sha256"], "image": x["index"]}


def make_ctx(out: Path, faults: dict | None = None, **budget_kwargs) -> stage_a.Ctx:
    import image_adapter
    faults = faults or {}
    plan = json.loads(stage_a.PLAN.read_text())
    stage_a.D_MODEL = D
    by_path = {str(stage_a.original_path(x)): x["original_sha256"] for x in plan["inputs"] if x["original_sha256"]}
    image_adapter.check_against_processor = lambda proc, seq, image, suffix=True: {
        "ids_equal": True, "grid_equal": True, "pixel_values_sha256": plan["inputs"][image]["pixel_values_sha256"]}
    ident = {"identity_sha256": "f" * 64}
    out.mkdir(parents=True, exist_ok=True)
    (out.parent / "identity.json").write_text(json.dumps(ident))

    def inst_factory():
        return FakeInstrument(plan, faults)

    def native_factory():
        from transformers import AutoTokenizer
        from image_adapter import SNAPSHOT
        tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))

        def forward(vmodel, seq, pv, layers, positions):
            x = plan["inputs"][int(np.asarray(pv).reshape(-1)[0])]
            rec = json.loads((out / f"passes/{x['index']:02d}-plain.json").read_text())
            res = np.load(out / f"passes/{x['index']:02d}-plain.residuals.npy")
            f32 = stage_a.bf16_to_f32(res)
            if faults.get("native_off") == x["index"]:
                f32 = f32 * 1.5
            logits = np.zeros(VOCAB + max(plan["request_token_ids"]) + 1, dtype=np.float32)
            for q in rec["requested"]:
                logits[q["id"]] = q["logit"]
            return {"residuals": f32, "logits": logits, "decoder_calls": {"min": 1, "max": 1, "layers": 64},
                    "effective_positions_sha256": x["expected"]["positions_sha256"],
                    "inputs_embeds_sha256": rec["image"]["merge"]["merged_sha256"]}
        return None, FakeProcessor(), tok, forward

    return stage_a.Ctx(out=out, identity_path=out.parent / "identity.json", verify_controller=False,
                       origins_check=lambda: None,
                       instrument_factory=inst_factory, native_factory=native_factory,
                       compute_identity=lambda: ident, check_go=lambda c: {}, pixels_fn=fake_pixels,
                       original_sha_fn=lambda p: by_path[str(p)], post_load=lambda inst: {"vocab_rows": VOCAB},
                       budget_kwargs=budget_kwargs)


if __name__ == "__main__":     # subprocess entry: python fake_stage_a.py <out> <faults json> [phase]
    import os
    out, faults = Path(sys.argv[1]), json.loads(sys.argv[2])
    phase = sys.argv[3] if len(sys.argv) > 3 else "instrumented"
    os.environ.setdefault("STAGE_A_SESSION", faults.get("session", "sub"))
    {"instrumented": stage_a.run_instrumented, "native": stage_a.run_native}[phase](make_ctx(out, faults))

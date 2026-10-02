"""Engineering forwards for the image adapter on ONE image outside the 32-concept pool (framework §8.1 item 2,
R052's reading): THINGSplus `chair.jpg` (furniture; outside all four families and the 121-concept qualified pool).
Every model pass is counted through enforce.Budget in a SEPARATE engineering state file, never row 20's. These
forwards establish nothing about Stage A; they test that the adapter runs and that its mechanics hold.

  inst    (one process: the instrumented path)
          builder check against mlx-vlm's processor (no model pass);
          six instrumented passes on the clean chair canvas, carrier 0, all 64 layers at the three marker positions:
            plain | empty edit list | zero-dose swap_delta at layer 41 | self-patch of layer 41's marker rows with
            the plain pass's own rows | swap_delta lambda = 1 at layer 41 (mechanics only) | delayed repeat of plain;
          plain, empty, zero, self-patch and repeat must be bitwise equal (residual and logit hashes).
  native  (a second process: mlx-vlm's own prefill, one pass) and the parity against `plain` at the §8.4 tolerances
          (relative L2 <= 0.01 per marker layer in FP32, max |logit diff| <= 0.10 on the requested ids, same argmax).
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dose  # noqa: E402
from enforce import Budget  # noqa: E402

OUT = Path(os.environ.get("T1_PHOTO_ENG_DIR", HERE / "engineering"))
IMAGE = Path.home() / "things-plus/cc0/object_images_CC0/chair.jpg"
IDENTITY = "eng-image-adapter-1"
LAYERS = list(range(64))
EDIT_LAYER = 41


def budget() -> Budget:
    return Budget(OUT / "engineering_state.json", "row20", IDENTITY, [OUT])


def stimulus():
    from PIL import Image
    canvas, geom = dose.load_canvas(IMAGE)
    S = dose.signal(dose.luma(canvas))
    rgb8, clip = dose.quantise(dose.mix(S, np.zeros_like(S), 1.0))        # clean: a = 1, the noise term is zero
    png = dose.to_png(rgb8)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    return img, png, geom, clip


def request_ids(tok) -> tuple[list[int], dict]:
    roles = json.loads((HERE / "dev_pool.json").read_text())["roles"]
    ids = [r["e1_token_id"] for r in roles]
    extra = {w: tok.encode(" " + w, add_special_tokens=False) for w in ("chair", "table")}
    return ids + [t[0] for t in extra.values() if len(t) == 1], extra


def run_inst() -> None:
    sys.path.insert(0, str(HERE.parents[1]))
    from image_adapter import ImageInstrument, build_sequence, check_against_processor, template_sha256
    t0 = time.time()
    inst = ImageInstrument()
    load_s = time.time() - t0
    img, png, geom, clip = stimulus()
    proc = inst.processor.image_processor
    po = proc(images=[img], return_tensors="np")
    pv = np.asarray(po["pixel_values"])
    grid = np.asarray(po["image_grid_thw"]).tolist()[0]
    seq = build_sequence(inst.tok, 0, grid)
    check = check_against_processor(inst.processor, seq, img)
    req_ids, extra = request_ids(inst.tok)
    chair, table = extra["chair"], extra["table"]
    b = budget()
    ce = inst.ce
    results = {}

    def one(name, edits=None):
        with b.attempt(f"{name}-{time.time():.0f}", "diagnostic", passes=1):
            r = inst.capture(seq, pv, capture_layers=LAYERS, request_token_ids=req_ids, top_k=20, edits=edits)
        results[name] = r
        return r

    mp = seq["marker_positions"]
    plain = one("plain")
    one("empty", [])
    one("zero", [ce.CaptureEdit(mode="swap_delta", layer=EDIT_LAYER, positions=mp, alpha=0.0,
                                token_id=chair[0], target_id=table[0])])
    res = np.frombuffer(base64.b64decode(plain["residuals"]["b64"]), dtype=np.uint16).reshape(len(LAYERS), len(mp), -1)
    rows41 = np.ascontiguousarray(res[LAYERS.index(EDIT_LAYER)])
    one("self_patch", [ce.CaptureEdit(mode="patch", layer=EDIT_LAYER, positions=mp,
                                      vectors_b64=base64.b64encode(rows41.tobytes()).decode("ascii"),
                                      vectors_dtype="bfloat16")])
    one("swap", [ce.CaptureEdit(mode="swap_delta", layer=EDIT_LAYER, positions=mp, alpha=1.0,
                                token_id=chair[0], target_id=table[0])])
    one("repeat")

    def key(r):
        return (r["residuals"]["sha256"], r["final_logits"]["sha256"], r["image"]["features_sha256"])

    bitwise = {n: key(results[n]) == key(plain) for n in ("empty", "zero", "self_patch", "repeat")}
    swap_moved = key(results["swap"]) != key(plain)
    summary = {
        "image": str(IMAGE.name), "png_sha256": dose.hashlib.sha256(png).hexdigest(), "geometry": geom, "clip": clip,
        "template_sha256": template_sha256(), "sequence": {k: v for k, v in seq.items() if k != "ids"},
        "processor_check": check, "load_seconds": round(load_s, 1),
        "bitwise_equal_to_plain": bitwise, "swap_changed_output": swap_moved,
        "swap_edit_log": results["swap"]["edit_log"], "zero_edit_log": results["zero"]["edit_log"],
        "plain": {k: plain[k] for k in ("n_tokens", "input_ids_sha256", "gdn_inference_kernel", "requested",
                                        "top_ids", "top_logits", "timing_s")},
        "plain_image": {k: v for k, v in plain["image"].items() if k != "boundary_mean_fp32_b64"},
        "timing_s": {n: r["timing_s"] for n, r in results.items()},
        "injections": inst.injector.injections, "instrument_passes": inst.passes,
        "counters": b.state["counters"]["row20"], "memory": dose_mem(),
        "decoded_top": [inst.tok.decode([t]) for t in plain["top_ids"][:10]],
    }
    np.savez(OUT / "inst_plain.npz", residuals=res, pixel_values=pv, ids=np.array(seq["ids"]), grid=np.array(grid),
             marker=np.array(mp), req_ids=np.array(req_ids),
             logits_requested=np.array([q["logit"] for q in plain["requested"]], dtype=np.float32),
             top_ids=np.array(plain["top_ids"]))
    (OUT / "seq.json").write_text(json.dumps(seq))
    (OUT / "adapter_engineering_inst.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("processor_check", "bitwise_equal_to_plain", "swap_changed_output",
                                              "injections", "instrument_passes", "counters", "decoded_top",
                                              "load_seconds", "memory")}, indent=1))


def dose_mem() -> dict:
    from enforce import GiB, memory_reading
    return {k: (round(v / GiB, 2) if isinstance(v, int) and k != "pressure_level" else v)
            for k, v in memory_reading().items()}


def run_native() -> None:
    import mlx.core as mx
    from mlx_vlm import load as vload
    sys.path.insert(0, str(HERE.parents[1]))
    from image_adapter import SNAPSHOT, native_forward
    z = np.load(OUT / "inst_plain.npz")
    seq = json.loads((OUT / "seq.json").read_text())
    vmodel, _ = vload(str(SNAPSHOT))
    b = budget()
    with b.attempt(f"native-{time.time():.0f}", "native_reference", passes=1):
        nat = native_forward(vmodel, seq, z["pixel_values"], LAYERS, seq["marker_positions"])
    inst = z["residuals"].view(np.uint16).astype(np.uint32) << 16
    inst = inst.view(np.float32).astype(np.float64)
    natr = nat["residuals"].astype(np.float64)
    rel = np.linalg.norm((inst - natr).reshape(64, -1), axis=-1) / np.linalg.norm(inst.reshape(64, -1), axis=-1)
    req = z["req_ids"].tolist()
    li = z["logits_requested"].astype(np.float64)
    ln = nat["logits"][req].astype(np.float64)
    out = {"rel_l2_max": float(rel.max()), "rel_l2_argmax_layer": int(rel.argmax()),
           "rel_l2_by_layer": [float(x) for x in rel], "numeric_equal_layers": int((rel == 0).sum()),  # rel == 0 after FP64 conversion: numeric equality, not a byte compare (signed zeros not distinguished; Codex f9d2ef3); the committed JSON of 1 Oct calls this "bitwise_layers"
          
           "requested_logit_max_abs": float(np.abs(li - ln).max()),
           "argmax_open_vocab": [int(z["top_ids"][0]), int(nat["logits"].argmax())],
           "argmax_requested": [int(req[int(li.argmax())]), int(req[int(ln.argmax())])],
           "tolerances": {"rel_l2": 0.01, "logit": 0.10},
           "pass": bool(rel.max() <= 0.01 and np.abs(li - ln).max() <= 0.10
                        and z["top_ids"][0] == nat["logits"].argmax() and li.argmax() == ln.argmax()),
           "counters": b.state["counters"]["row20"], "memory": dose_mem()}
    (OUT / "adapter_engineering_native.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rel_l2_by_layer"}, indent=1))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    {"inst": run_inst, "native": run_native}[sys.argv[1]]()

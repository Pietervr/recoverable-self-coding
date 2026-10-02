"""Photograph arm, Stage A (ledger row 20, framework §8.4): native fidelity and profiling - the runner.

NOT RUN. `plan` is pixels only (no model). `instrumented` and `native` refuse to start unless ROW20_GO.json exists
beside this file recording the owner's go and Codex's row review (it does not exist at the desk gate).

INPUTS (20, framework §8.4): the eight Stage A primary views of dev_pool.json (two DEV-CAL per family, each with an
eligible per-image check) -> 8 clean; per family the two views, sorted by name, are dealt one to -12 dB and one to 0 dB
by the plan seed -> 4 + 4 intermediate; 4 noise-only inputs built on dose.zero's own path (no photograph opened).
Carriers: the 20 inputs are shuffled by the plan seed, the first 10 take carrier 0, the rest carrier 1. Every noise
draw has an opaque nonce sha256("stageA|<seed>|<input index>"), independent of the concept and the pixels.

CASES per input, all through image_adapter.ImageInstrument (one pass each), 64 layers at the three [END] positions,
closed-set logits over the 32 frozen E1 ids at the final suffix position:
  plain        no edit list
  empty        edits = []                                       must equal plain bitwise
  zero         swap_delta target->foil at layer 41, alpha 0      must equal plain bitwise (the sham)
  self_patch   patch layer 41's marker rows with plain's rows    must equal plain bitwise
  swap         swap_delta target->foil at layer 41, alpha 1      H3's primary operation, mechanics only
  ablate       ablate target at layer 41, alpha 1                H3's secondary operation, mechanics only
  repeat       plain again, after every input's other cases      must equal plain bitwise (delayed repeat)
  (target = the view's E1; foil = the other Stage A view of its family; a noise-only input uses its assigned
  family's pair in name order.) 7 x 20 = 140 instrumented passes.
NATIVE: mlx-vlm's own prefill (image_adapter.native_forward), one pass per input, in a SEPARATE process = 20.
Total 160 mandatory; the 40 spare are not spent by this runner.

TOLERANCES (fixed here, never adjusted after a failure): relative L2 <= 0.01 per marker layer in FP32 (over the three
marker rows), max |logit diff| <= 0.10 over the 32 E1 ids, identical closed-set argmax; within-path checks bitwise.
STOPS: the first bitwise or parity failure, an identity mismatch, or any enforce.Budget stop (row 20 caps, memory,
swap, pressure). Counters persist atomically in stage_a_state.json (enforce.py); a restart refuses a changed
identity and never replays a completed attempt.

    .venv-image/bin/python stimuli/photo/stage_a.py plan
    .venv-image/bin/python stimuli/photo/stage_a.py instrumented     # after the go
    .venv-image/bin/python stimuli/photo/stage_a.py native           # then, in a fresh process
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
T1 = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dose  # noqa: E402

SEED = 20261006
EDIT_LAYER = 41
LAYERS = list(range(64))
CASES = ["plain", "empty", "zero", "self_patch", "swap", "ablate"]     # 'repeat' runs after all inputs
TOL = {"rel_l2": 0.01, "logit": 0.10}
OUT = T1 / "captures" / "photo_stage_a"
STATE = OUT / "stage_a_state.json"
GO = HERE / "ROW20_GO.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def plan() -> dict:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    checks = {c["concept"]: c for c in json.loads((HERE / "provenance_checks.json").read_text())["checks"]}
    views = sorted((r for r in pool["roles"] if r["stage_a_primary_view"]), key=lambda r: (r["family"], r["concept"]))
    assert len(views) == 8 and all(checks[v["concept"]]["status"] == "eligible" for v in views), "gate: checks"
    assert all(v["role"] == "DEV-CAL" for v in views)
    rng = random.Random(SEED)
    grid = dose.a_grid()
    fams = sorted({v["family"] for v in views})
    pair = {f: [v for v in views if v["family"] == f] for f in fams}
    inputs = [{"kind": "clean", "concept": v["concept"], "level": "clean"} for v in views]
    for f in fams:
        a, b = pair[f]
        lo, hi = (a, b) if rng.random() < 0.5 else (b, a)
        inputs += [{"kind": "intermediate", "concept": lo["concept"], "level": "-12dB"},
                   {"kind": "intermediate", "concept": hi["concept"], "level": "+0dB"}]
    inputs += [{"kind": "noise_only", "concept": None, "family_for_edits": f, "level": "noise_only"} for f in fams]
    rng.shuffle(inputs)
    by_name = {v["concept"]: v for v in views}
    e1 = [r["e1_token_id"] for r in sorted(pool["roles"], key=lambda r: r["concept"])]
    for i, x in enumerate(inputs):
        x["index"] = i
        x["carrier"] = 0 if i < 10 else 1
        x["nonce"] = sha(f"stageA|{SEED}|{i}".encode())
        x["a"] = grid["a"][x["level"]]
        fam = by_name[x["concept"]]["family"] if x["concept"] else x["family_for_edits"]
        p = pair[fam]
        if x["concept"]:
            tgt = by_name[x["concept"]]
            foil = p[1] if p[0]["concept"] == x["concept"] else p[0]
        else:
            tgt, foil = p[0], p[1]
        x["target"], x["foil"] = tgt["concept"], foil["concept"]
        x["target_id"], x["foil_id"] = tgt["e1_token_id"], foil["e1_token_id"]
    return {"seed": SEED, "a_grid_sha256": grid["sha256"], "inputs": inputs, "request_token_ids": e1,
            "cases": CASES + ["repeat"], "native": 1, "edit_layer": EDIT_LAYER, "tolerances": TOL,
            "dev_pool_sha256": sha((HERE / "dev_pool.json").read_bytes()),
            "provenance_checks_sha256": sha((HERE / "provenance_checks.json").read_bytes()),
            "planned_passes": {"instrumented": 7 * len(inputs), "native": len(inputs), "total": 8 * len(inputs)}}


def stimulus(x: dict) -> np.ndarray:
    """The input's 8-bit RGB array. Noise-only never opens a photograph (dose.zero's own path)."""
    if x["kind"] == "noise_only":
        I = dose.zero(x["nonce"])
    else:
        canvas, _ = dose.load_canvas(Path.home() / "things-plus/cc0/object_images_CC0" / f"{x['concept']}.jpg")
        S = dose.signal(dose.luma(canvas))
        N = dose.noise(x["nonce"]) if x["a"] < 1.0 else np.zeros_like(S)
        I = dose.mix(S, N, x["a"])
    rgb8, _ = dose.quantise(I)
    return rgb8


def pixels(x: dict, image_processor):
    from PIL import Image
    png = dose.to_png(stimulus(x))
    out = image_processor(images=[Image.open(io.BytesIO(png)).convert("RGB")], return_tensors="np")
    pv = np.asarray(out["pixel_values"])
    return pv, np.asarray(out["image_grid_thw"]).tolist()[0], sha(png), sha(np.ascontiguousarray(
        pv.astype(np.float32)).tobytes())


def identity(extra: dict) -> str:
    import mlx.core as mx
    import mlx_lm
    import mlx_vlm
    import image_adapter
    files = [HERE / n for n in ("stage_a.py", "image_adapter.py", "dose.py", "enforce.py")]
    files.append(image_adapter.UPSTREAM / "jlens_qwen" / "capture_endpoint.py")
    ident = {"code": {f.name: sha(f.read_bytes()) for f in files}, "template": image_adapter.template_sha256(),
             "mlx": mx.__version__, "mlx_lm": mlx_lm.__version__, "mlx_vlm": mlx_vlm.__version__,
             "snapshot": image_adapter.SNAPSHOT.name, **extra}
    return sha(json.dumps(ident, sort_keys=True).encode())


def require_go() -> dict:
    if not GO.exists():
        raise SystemExit(f"refused: {GO.name} absent - row 20 has no owner go and no Codex row review")
    go = json.loads(GO.read_text())
    for k in ("owner_go", "codex_row_review"):
        if not go.get(k):
            raise SystemExit(f"refused: {GO.name} lacks {k}")
    return go


def run_instrumented() -> None:
    require_go()
    from enforce import Budget, StopRun
    from image_adapter import ImageInstrument, build_sequence
    p = plan()
    OUT.mkdir(parents=True, exist_ok=True)
    inst = ImageInstrument()
    ident = identity({"phase": "stage_a", "plan_sha256": sha(json.dumps(p, sort_keys=True).encode())})
    budget = Budget(STATE, "row20", ident, [OUT])
    ce, proc = inst.ce, inst.processor.image_processor
    plains = {}

    def edits(case, x, seq, plain):
        mp = seq["marker_positions"]
        if case == "plain":
            return None
        if case == "empty":
            return []
        if case in ("zero", "swap"):
            return [ce.CaptureEdit(mode="swap_delta", layer=EDIT_LAYER, positions=mp, alpha=0.0 if case == "zero"
                                   else 1.0, token_id=x["target_id"], target_id=x["foil_id"])]
        if case == "ablate":
            return [ce.CaptureEdit(mode="ablate", layer=EDIT_LAYER, positions=mp, alpha=1.0,
                                   ablate_token_ids=[x["target_id"]])]
        res = np.frombuffer(base64.b64decode(plain["residuals"]["b64"]), dtype=np.uint16).reshape(64, len(mp), -1)
        return [ce.CaptureEdit(mode="patch", layer=EDIT_LAYER, positions=mp, vectors_dtype="bfloat16",
                               vectors_b64=base64.b64encode(np.ascontiguousarray(res[EDIT_LAYER]).tobytes()).decode())]

    def key(r):
        return (r["residuals"]["sha256"], r["final_logits"]["sha256"], r["image"]["features_sha256"])

    def one(x, case, seq, pv):
        with budget.attempt(f"{x['index']}-{case}", "instrumented", passes=1):
            r = inst.capture(seq, pv, capture_layers=LAYERS, request_token_ids=p["request_token_ids"], top_k=50,
                             edits=edits(case, x, seq, plains.get(x["index"])))
        rec = {k: r[k] for k in ("input_ids_sha256", "requested", "top_ids", "top_logits", "edit_log",
                                 "logsumexp", "timing_s", "image")}
        rec.update(case=case, index=x["index"], residuals_sha256=r["residuals"]["sha256"],
                   logits_sha256=r["final_logits"]["sha256"])
        np.save(OUT / f"res_{x['index']:02d}_{case}.npy",
                np.frombuffer(base64.b64decode(r["residuals"]["b64"]), dtype=np.uint16))
        with open(OUT / "instrumented.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        return r

    seqs = {}
    try:
        for x in p["inputs"]:
            pv, grid, png_sha, pv_sha = pixels(x, proc)
            seq = build_sequence(inst.tok, x["carrier"], grid)
            seqs[x["index"]] = (seq, pv)
            for case in CASES:
                r = one(x, case, seq, pv)
                if case == "plain":
                    plains[x["index"]] = r
                elif case in ("empty", "zero", "self_patch") and key(r) != key(plains[x["index"]]):
                    raise StopRun(f"input {x['index']}: {case} differs from plain - bitwise parity failure")
        for x in p["inputs"]:
            seq, pv = seqs[x["index"]]
            if key(one(x, "repeat", seq, pv)) != key(plains[x["index"]]):
                raise StopRun(f"input {x['index']}: delayed repeat differs from plain")
    except StopRun as e:
        (OUT / "STOP_instrumented.txt").write_text(str(e))
        raise
    print(json.dumps(budget.state["counters"]["row20"]))


def run_native() -> None:
    require_go()
    from mlx_vlm import load as vload
    from enforce import Budget, StopRun
    from image_adapter import SNAPSHOT, native_forward
    p = plan()
    vmodel, processor = vload(str(SNAPSHOT))
    ident = identity({"phase": "stage_a", "plan_sha256": sha(json.dumps(p, sort_keys=True).encode())})
    budget = Budget(STATE, "row20", ident, [OUT])
    plain = {json.loads(l)["index"]: json.loads(l) for l in (OUT / "instrumented.jsonl").read_text().splitlines()
             if json.loads(l)["case"] == "plain"}
    from image_adapter import build_sequence
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    req = p["request_token_ids"]
    report = []
    try:
        for x in p["inputs"]:
            pv, grid, _, pv_sha = pixels(x, processor.image_processor)
            if pv_sha != plain[x["index"]]["image"]["pixel_values_sha256"]:
                raise StopRun(f"input {x['index']}: pixel tensor differs from the instrumented pass")
            seq = build_sequence(tok, x["carrier"], grid)
            with budget.attempt(f"{x['index']}-native", "native_reference", passes=1):
                nat = native_forward(vmodel, seq, pv, LAYERS, seq["marker_positions"])
            inst = (np.load(OUT / f"res_{x['index']:02d}_plain.npy").astype(np.uint32) << 16).view(np.float32)
            inst = inst.reshape(64, -1).astype(np.float64)
            natr = nat["residuals"].reshape(64, -1).astype(np.float64)
            rel = np.linalg.norm(inst - natr, axis=1) / np.linalg.norm(inst, axis=1)
            li = np.array([q["logit"] for q in plain[x["index"]]["requested"]], dtype=np.float64)
            ln = nat["logits"][req].astype(np.float64)
            row = {"index": x["index"], "rel_l2_max": float(rel.max()), "rel_l2_by_layer": rel.tolist(),
                   "logit_max_abs": float(np.abs(li - ln).max()), "argmax_equal": bool(li.argmax() == ln.argmax())}
            row["pass"] = row["rel_l2_max"] <= TOL["rel_l2"] and row["logit_max_abs"] <= TOL["logit"] and \
                row["argmax_equal"]
            report.append(row)
            (OUT / "native_parity.json").write_text(json.dumps(report, indent=1))
            if not row["pass"]:
                raise StopRun(f"input {x['index']}: native parity failed {row}")
    except StopRun as e:
        (OUT / "STOP_native.txt").write_text(str(e))
        raise
    print(json.dumps(budget.state["counters"]["row20"]))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        from dose_report import processor
        p = plan()
        proc = processor()
        for x in p["inputs"]:
            _, grid, png_sha, pv_sha = pixels(x, proc)
            x.update(png_sha256=png_sha, pixel_values_sha256=pv_sha, grid_thw=grid)
        (HERE / "stage_a_plan.json").write_text(json.dumps(p, indent=1) + "\n")
        kinds = {k: sum(x["kind"] == k for x in p["inputs"]) for k in ("clean", "intermediate", "noise_only")}
        print(kinds, "carriers", [sum(x["carrier"] == c for x in p["inputs"]) for c in (0, 1)],
              "passes", p["planned_passes"])
        return 0
    {"instrumented": run_instrumented, "native": run_native}[cmd]()
    return 0


if __name__ == "__main__":
    sys.exit(main())

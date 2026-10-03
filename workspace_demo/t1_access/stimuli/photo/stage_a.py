"""Photograph arm, Stage A (ledger row 20, framework §8.4): native fidelity and profiling - the runner, revision 5.

Revision 5 answers Codex's record RSC 1bf9890 (not favourable to revision 4 at d7a486a) through R052's handoff
8c9dac2b; the condition-by-condition map is STAGE_A_CRITERIA.md §1; revisions 6-14 in its §0-§R14. Revision 13: the
native logit criterion in bfloat16 steps at and above 16 (`compare`) and the chained transition (`PREDECESSORS`);
revision 14: the prepared-link reconciliation in `identity_transition` (Codex c4bbcb5 R1); revision 15: macOS
27.0 -> 27.0.1 as the one declared environment difference of the revision-12 link (`environment_differences`);
revision 16: the row-20 OS-bridge supplement (Codex b0db0f9; STAGE_A_SUPPLEMENT_CRITERIA.md) - input 00, two new
forwards on macOS 27.0.1 in its own tree, two direct comparisons, `supplement_receipt_ok` for row 21. Stage A's own
paths are unchanged.
EXPOSURE: two runs - 2 October (revision 10: gates and 158 instrumented forwards, terminal) and 3 October (revision 12:
16 native forwards, terminal at 15-native) - reviews/2026-10-02_stage_a_run.md, reviews/2026-10-03_stage_a_resume_run.md.

    .venv-image/bin/python stimuli/photo/stage_a.py plan          # desk: freeze stage_a_plan.json (no model forward)
    .venv-image/bin/python stimuli/photo/stage_a.py identity      # desk: write stage_a_identity.json (no model load)
    .venv-image/bin/python stimuli/photo/stage_a.py package       # desk: print the hashes ROW20_GO.json must bind
    .venv-image/bin/python stimuli/photo/stage_a_controller.py run    # after the go: gates -> phases -> report
    (`stage_a.py worker <gates|instrumented|native|report>` is the controller's worker entry, never run by hand)
    .venv-image/bin/python stimuli/photo/stage_a.py supplement-plan      # rev 16 desk: stage_a_supplement_plan.json
    .venv-image/bin/python stimuli/photo/stage_a.py supplement-identity  # rev 16 desk: stage_a_supplement_identity.json
    .venv-image/bin/python stimuli/photo/stage_a.py supplement-package   # rev 16 desk: what ROW20S_GO.json binds
    .venv-image/bin/python stimuli/photo/stage_a_controller.py supplement   # after Codex + the owner's go only
    .venv-image/bin/python stimuli/photo/stage_a.py supplement-verify    # desk: row 21's verifier, current execution

WORKERS. GATES: frozen plan and manifest (and the current dev pool and provenance records equal to the plan's
reviewed pins - A8), positions receipt (present, passing, for this plan), the go under the strict shared guard with the
reviewed package re-derived from the reviewed commit's blobs, a fresh execution identity, the gates' OWN import map
consumed and checked (check_imported_origins - A1), then crash reconciliation of an open attempt and the recovery
files, and the identity rechecked before GATES.json is committed - a missing recovery file is an authorisation Hold
(exit 4), distinct from a refusal. INSTRUMENTED, NATIVE: each recomputes the execution identity itself (equal to the
frozen one and to the gates' admitted one), consumes the import map it wrote, and re-checks local code, packet, plan,
manifest and receipt before writing its phase record; a committed record reloaded on resumption passes the phase's full
independent predicates before use, and NATIVE runs the complete instrumented validator (stage_a_report.validate,
phases=("instrumented",)) before any native model is constructed (A6). REPORT: reads the ledger without converting,
granting or consuming anything, recomputes the identity, consumes and checks its own map, and rechecks the identity
before it writes its receipt (A1); it is admissible only with this session's passed gates and an equal identity. Every
write reserves storage (enforce.configure_storage).

INPUTS (20): unchanged from revision 1 (same seed, same draws): 8 clean, 4 at -12 dB, 4 at 0 dB, 4 noise-only; carriers
10/10. The plan now also freezes every input's original-file sha256 (equal to manifest_dev.json's), the expected
expanded ids hash, image span, marker and suffix indices, and the expected multimodal positions hash per carrier.

CASES (framework §8.4, R052 2 Oct): plain, empty, zero_steer, zero_ablate, zero_swap, self_patch, repeat. All but
plain must equal plain bitwise (residual, logit and feature hashes). `repeat` is an explicit no-edit pass run after
every input's other cases. An unknown case raises. 7 x 20 = 140 instrumented + 20 native = 160 mandatory.
DIAGNOSTICS (labelled, no favourable-output criterion except where stated): lambda = 1 swap and ablate at layer 41 on
the eight clean inputs (16); future-suffix isolation, one per carrier on a declared clean plain input, the suffix ids
replaced by declared tokens - marker residuals must equal plain's bitwise (2). Encoder sensitivity on a declared pair
of clean plain inputs - changed pixel and feature hashes - costs no forward. ENVELOPE: 16 engineering attempts
carried in + 140 + 18 + 20 = 194 of 200; no attempt id outside the plan is ever run.

GATES before any load: the exclusive task lock, the terminal gate, the go bound to this exact package, an authorised
recovery for any interrupted attempt, and (native) the complete validated instrumented phase.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

HERE = Path(__file__).resolve().parent
T1 = HERE.parents[1]
sys.path.insert(0, str(HERE))
import dose  # noqa: E402

SEED = 20261006
EDIT_LAYER = 41
LAYERS = list(range(64))
N_LAYERS, D_MODEL, N_MARKER, N_IMAGE_TOKENS = 64, 5120, 3, 144
CASES = ["plain", "empty", "zero_steer", "zero_ablate", "zero_swap", "self_patch", "repeat"]
BITWISE = ["empty", "zero_steer", "zero_ablate", "zero_swap", "self_patch", "repeat"]
MECHANICS = ["swap1", "ablate1"]
TOL = {"rel_l2": 0.01, "logit": 0.10}
# Revision 13 (R052 handoff 8508993b): the native logit criterion is per requested logit, |native - instrumented| <=
# max(TOL["logit"], one bfloat16 step at m = max(|native|, |instrumented|)) - the frozen 0.10 wherever it is coarser
# than a step (every |logit| < 16), one bf16 step at and above 16 (0.125 for 16-32, 0.25 for 32-64, ...). The native
# path emits bfloat16 logits: below one representable step a tolerance demands that two roundings coincide.


def bf16_step(m: float) -> float:
    """The bfloat16 spacing of the binade holding m: 2^(floor(log2 m) - 7) for m > 0 (8 significand bits); 0 for
    m = 0. compare passes m = the LARGER magnitude, so at a binade boundary the step is coarser than the gap just below
    (16.0 and 15.9375 are adjacent, 0.0625 apart, while step(16) = 0.125). frexp keeps the binade exact (m = f * 2^e,
    0.5 <= f < 1, so floor(log2 m) = e - 1)."""
    m = abs(float(m))
    if m == 0.0:
        return 0.0
    _, e = math.frexp(m)
    return math.ldexp(1.0, e - 1 - 7)


def logit_tolerance(m: float) -> float:
    return max(TOL["logit"], bf16_step(m))
TOP_K = 50
INST_SCHEMA, NAT_SCHEMA = "stage_a.instrumented.v4", "stage_a.native.v4"
INST_CAPTURE_KEYS = ("input_ids_sha256", "n_tokens", "readout_positions", "capture_layers", "requested", "top_ids",
                     "top_logits", "edit_log", "edits_installed", "logsumexp", "timing_s", "image",
                     "gdn_inference_kernel")
SUFFIX_PIECES = ["\t", "Reply", ";"]
ENGINEERING_CARRY = {
    "started": 16, "completed": 15, "failed": 1, "passes": 16,
    "measured_seconds": 8.73, "allowance_seconds": 1800.0, "seconds": 1808.73,
    "basis": "engineering/README.md: eng-runtime-agreement 8 attempts (1.72 s of attempts) and eng-image-adapter-1 "
             "8 attempts, 7 completed, 1 failed before any model pass (7.01 s); the manual identity relabel "
             "disclosed there. Startup, model and lens loads, preprocessing and writes were not timed: a recorded "
             "allowance of 1,800 s (30 min) is charged for them - conservative against the 5 s loads and ~1 s passes "
             "measured. Carried into row 20, not reset (framework §8.4; Codex f9d2ef3)."}
OUT = T1 / "captures" / "photo_stage_a"
RECEIPT = HERE / "stage_a_positions_receipt.json"
IDENTITY_FILES = HERE / "stage_a_identity_files.json"
PLAN = HERE / "stage_a_plan.json"
MANIFEST = HERE / "manifest_dev.json"
IDENTITY = HERE / "stage_a_identity.json"
CRITERIA = HERE / "STAGE_A_CRITERIA.md"
GO = HERE / "ROW20_GO.json"
THINGSPLUS = Path.home() / "things-plus/cc0/object_images_CC0"
RSC_ROOT = T1.parents[1]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


# ================================================================================================================
# The plan (desk; no model forward)
# ================================================================================================================
def draw_inputs() -> tuple[list[dict], dict, list[int]]:
    """Revision 1's draw, unchanged: the same seed gives the same 20 inputs, carriers, nonces, targets and foils."""
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
    roles = sorted(pool["roles"], key=lambda r: r["concept"])
    request = [{"concept": r["concept"], "id": r["e1_token_id"]} for r in roles]
    return inputs, grid, request


def original_path(x: dict) -> Path | None:
    return None if x["kind"] == "noise_only" else THINGSPLUS / f"{x['concept']}.jpg"


def stimulus(x: dict) -> np.ndarray:
    """The input's 8-bit RGB array. Noise-only never opens a photograph (dose.zero's own path)."""
    if x["kind"] == "noise_only":
        I = dose.zero(x["nonce"])
    else:
        canvas, _ = dose.load_canvas(original_path(x))
        S = dose.signal(dose.luma(canvas))
        N = dose.noise(x["nonce"]) if x["a"] < 1.0 else np.zeros_like(S)
        I = dose.mix(S, N, x["a"])
    rgb8, _ = dose.quantise(I)
    return rgb8


def pixels(x: dict, image_processor) -> dict:
    from PIL import Image
    png = dose.to_png(stimulus(x))
    image = Image.open(io.BytesIO(png)).convert("RGB")
    out = image_processor(images=[image], return_tensors="np")
    pv = np.asarray(out["pixel_values"])
    return {"pv": pv, "grid": np.asarray(out["image_grid_thw"]).tolist()[0], "png_sha256": sha(png), "image": image,
            "pixel_values_sha256": sha(np.ascontiguousarray(pv.astype(np.float32)).tobytes())}


def suffix_replacement(tok, seq: dict) -> dict:
    """The declared future-suffix perturbation: every suffix id ("\\n", "Answer", ":") replaced, position by
    position, by a declared single-token piece ("\\t", "Reply", ";"); each piece must be one token and differ from
    the id it replaces, so the length and every position are unchanged."""
    from stimuli.packet import encode

    old = [seq["ids"][i] for i in seq["suffix_positions"]]
    new = []
    for piece in SUFFIX_PIECES:
        ids = encode(tok, piece)
        if len(ids) != 1:
            raise ValueError(f"declared suffix piece {piece!r} is not one token")
        new += ids
    if len(new) != len(old) or any(a == b for a, b in zip(old, new)):
        raise ValueError("the declared suffix replacement does not change every suffix id at equal length")
    return {"pieces": SUFFIX_PIECES, "ids": new, "replaces": old}


def apply_suffix(seq: dict, rep: dict) -> dict:
    s = dict(seq)
    ids = list(seq["ids"])
    for i, t in zip(seq["suffix_positions"], rep["ids"]):
        ids[i] = t
    s["ids"] = ids
    s["ids_sha256"] = sha(np.asarray(ids, dtype=np.int64).tobytes())
    return s


def expected_positions(seq: dict, merge: int = 2) -> np.ndarray:
    """Interleaved M-RoPE positions as Qwen-VL defines them for one image: text 1-D before the image; the image's
    merged (t, h, w) grid offset by its start; text after the image resumes at max(image) + 1, all three equal."""
    n, (s0, s1) = seq["n"], seq["image_span"]
    t, h, w = seq["grid_thw"]
    gh, gw = h // merge, w // merge
    pos = np.zeros((3, 1, n), dtype=np.int64)
    pos[:, 0, :s0] = np.arange(s0)
    k = 0
    for ti in range(t):
        for hi in range(gh):
            for wi in range(gw):
                pos[:, 0, s0 + k] = (s0 + ti, s0 + hi, s0 + wi)
                k += 1
    assert s0 + k == s1
    start = int(pos[:, 0, s0:s1].max()) + 1
    pos[:, 0, s1:] = start + np.arange(n - s1)
    return pos


def check_sequence_structure(seq: dict) -> None:
    """Framework §8.4 (e), structure: one contiguous pad span ending before every marker; markers before the suffix;
    indices valid and distinct."""
    from image_adapter import IMAGE_PAD  # noqa: F401  (the convention's own names)
    s0, s1 = seq["image_span"]
    if s1 - s0 != N_IMAGE_TOKENS or seq["n_image_tokens"] != N_IMAGE_TOKENS:
        raise StopCheck(f"image span holds {s1 - s0} tokens, not {N_IMAGE_TOKENS}")
    m, sfx = seq["marker_positions"], seq["suffix_positions"]
    if len(m) != N_MARKER or len(set(m)) != N_MARKER or m != sorted(m) or m[0] <= s1 - 1:
        raise StopCheck(f"marker positions {m} invalid or not after the image span ending {s1 - 1}")
    if not sfx or sfx[0] <= m[-1] or sfx != list(range(sfx[0], seq["n"])):
        raise StopCheck("suffix positions do not follow the markers to the end of the sequence")
    if seq["vision_start"] != s0 - 1 or seq["vision_end"] != s1:
        raise StopCheck("vision_start / vision_end do not bracket the pad span")


class StopCheck(RuntimeError):
    """An integrity or parity failure (always terminal)."""


def envelope() -> dict:
    from enforce import CAPS, MEMORY_CAP
    import stage_a_controller as C
    return {"mandatory": {"instrumented": 140, "native": 20}, "diagnostics": {"mechanics_lambda1": 16,
            "suffix_isolation": 2, "encoder_sensitivity": 0}, "engineering_carried": ENGINEERING_CARRY,
            "total_attempts": 194, "cap_attempts": 200, "in_hand": 6, "caps": CAPS, "memory_cap": MEMORY_CAP,
            "controller": {"heartbeat_s": C.HEARTBEAT_S, "memory_sample_s": C.MEM_SAMPLE_S,
                           "system_sample_s": C.SYS_SAMPLE_S, "sample_limit_s": C.SAMPLE_LIMIT_S,
                           "watchdog_tick_stale_s": C.TICK_STALE_S,
                           "tail_reserve_s": C.TAIL_RESERVE_S, "stop_reserve_s": C.STOP_RESERVE_S,
                           "report_reserve_s": C.REPORT_RESERVE_S, "final_allowance_s": C.FINAL_ALLOWANCE_S,
                           "revoke_timeout_s": C.REVOKE_TIMEOUT_S, "exit_margin_s": C.EXIT_MARGIN_S,
                           "close_charge_s": C.CLOSE_CHARGE_S, "guardian_setup_deadline_s": C.SETUP_DEADLINE_S,
                           "stop_signal": "SIGKILL at once (no grace)",
                           "watchdog_stale_s": C.STALE_S, "watchdog_hard_margin_s": C.HARD_MARGIN_S,
                           "group_gone_s": C.GROUP_GONE_S, "watchdog_arm_timeout_s": C.ARM_TIMEOUT_S,
                           "memory_stop_bytes": C.MEM_STOP, "memory_measure": "per-identity lifetime maxima summed "
                           "over the watchdog, the worker and its group/descendants (exit peaks folded in), plus the "
                           "controller's final lifetime maximum",
                           "final_reserve_bytes": C.FINAL_RESERVE_BYTES},
            "rule": "no attempt id outside the plan; no retry; the six in hand are spent only by an owner-authorised "
                    "recovery of one named interrupted try"}


def budget_sha256(env: dict) -> str:
    return sha(json.dumps(env, sort_keys=True).encode())


def make_plan() -> dict:
    from transformers import AutoTokenizer
    from dose_report import processor
    from image_adapter import SNAPSHOT, build_sequence, template_sha256
    from stimuli.packet import encode
    inputs, grid, request = draw_inputs()
    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    proc = processor()
    manifest = {r["concept"]: r for r in json.loads(MANIFEST.read_text())["records"]}
    for r in request:
        if encode(tok, " " + r["concept"]) != [r["id"]]:
            raise SystemExit(f"E1 id of {r['concept']} is not the pinned tokenizer's single token")
    seqs = {}
    for x in inputs:
        px = pixels(x, proc)
        x.update(png_sha256=px["png_sha256"], pixel_values_sha256=px["pixel_values_sha256"], grid_thw=px["grid"])
        op = original_path(x)
        x["original_sha256"] = sha_file(op) if op else None
        if op and x["original_sha256"] != manifest[x["concept"]]["original_sha256"]:
            raise SystemExit(f"{x['concept']}: original bytes differ from manifest_dev.json")
        if x["kind"] == "clean" and x["png_sha256"] != manifest[x["concept"]]["clean_canvas"]["png_sha256"]:
            raise SystemExit(f"{x['concept']}: clean PNG differs from manifest_dev.json")
        seq = build_sequence(tok, x["carrier"], px["grid"])
        check_sequence_structure(seq)
        seqs[x["index"]] = seq
        x["expected"] = {k: seq[k] for k in ("ids_sha256", "n", "image_span", "vision_start", "vision_end",
                                             "marker_positions", "suffix_positions", "n_image_tokens")}
        x["expected"]["positions_sha256"] = sha(np.ascontiguousarray(expected_positions(seq)).tobytes())
    clean = [x for x in inputs if x["kind"] == "clean"]
    mech = sorted(x["index"] for x in clean)
    sfx_base = [min(x["index"] for x in clean if x["carrier"] == c) for c in (0, 1)]
    suffix = []
    for b in sfx_base:
        rep = suffix_replacement(tok, seqs[b])
        mod = apply_suffix(seqs[b], rep)
        suffix.append({"base_index": b, "carrier": inputs[b]["carrier"], "replacement": rep,
                       "ids_sha256": mod["ids_sha256"], "criterion": "marker residual sha256 == base plain's"})
    enc_pair = [sfx_base[0], next(x["index"] for x in clean if x["carrier"] == 0 and x["index"] != sfx_base[0])]
    attempts = []
    for x in inputs:
        attempts += [{"id": f"{x['index']:02d}-{c}", "phase": "instrumented", "kind": "mandatory",
                      "index": x["index"], "case": c} for c in CASES if c != "repeat"]
    attempts += [{"id": f"{x['index']:02d}-repeat", "phase": "instrumented", "kind": "mandatory",
                  "index": x["index"], "case": "repeat"} for x in inputs]
    attempts += [{"id": f"{i:02d}-{c}", "phase": "instrumented", "kind": "diagnostic_mechanics", "index": i,
                  "case": c} for i in mech for c in MECHANICS]
    attempts += [{"id": f"{s['base_index']:02d}-suffix_isolation", "phase": "instrumented",
                  "kind": "diagnostic_suffix_isolation", "index": s["base_index"], "case": "suffix_isolation"}
                 for s in suffix]
    attempts += [{"id": f"{x['index']:02d}-native", "phase": "native", "kind": "mandatory_native",
                  "index": x["index"], "case": "native"} for x in inputs]
    env = envelope()
    assert len(attempts) + ENGINEERING_CARRY["passes"] == env["total_attempts"] == 194
    return {"revision": 7, "seed": SEED, "a_grid_sha256": grid["sha256"], "inputs": inputs,
            "request_tokens": request, "request_token_ids": [r["id"] for r in request],
            "cases": CASES, "bitwise_cases": BITWISE, "edit_layer": EDIT_LAYER, "capture_layers": LAYERS,
            "top_k": TOP_K, "tolerances": TOL, "template_sha256": template_sha256(),
            "diagnostics": {"mechanics": {"cases": MECHANICS, "inputs": mech, "alpha": 1.0, "layer": EDIT_LAYER,
                                          "criterion": "none (labelled mechanics diagnostic); output archived"},
                            "suffix_isolation": suffix,
                            "encoder_sensitivity": {"pair": enc_pair, "criterion": "pixel_values and features "
                                                    "sha256 differ, grids equal; from the plain passes, no forward"}},
            "attempts": attempts, "envelope": env, "budget_sha256": budget_sha256(env),
            "dev_pool_sha256": sha_file(HERE / "dev_pool.json"),
            "provenance_checks_sha256": sha_file(HERE / "provenance_checks.json"),
            "manifest_records_sha256": {k: sha(json.dumps(v, sort_keys=True).encode())
                                        for k, v in sorted(manifest.items())
                                        if k in {x["concept"] for x in inputs if x["concept"]}}}


def verify_positions_rule(plan: dict) -> dict:
    """Desk check of expected_positions against mlx-vlm's own get_rope_index (index arithmetic on the config; the
    weights are opened lazily and never evaluated - no model forward)."""
    import mlx.core as mx
    from mlx_vlm import load as vload
    from transformers import AutoTokenizer
    from image_adapter import SNAPSHOT, build_sequence
    vmodel, _ = vload(str(SNAPSHOT), lazy=True)
    lm = vmodel.language_model
    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    out = {}
    for c in (0, 1):
        x = next(x for x in plan["inputs"] if x["carrier"] == c)
        seq = build_sequence(tok, c, x["grid_thw"])
        pos, _ = lm.get_rope_index(mx.array([seq["ids"]]), mx.array([seq["grid_thw"]]))
        got = np.asarray(np.array(pos)).astype(np.int64)
        out[c] = bool(np.array_equal(got, expected_positions(seq)))
    return out


# ================================================================================================================
# Running context (paths and factories, replaceable by the tests' fake instrument)
# ================================================================================================================
@dataclass
class Ctx:
    out: Path = OUT
    plan_path: Path = PLAN
    manifest_path: Path = MANIFEST
    identity_path: Path = IDENTITY
    criteria_path: Path = CRITERIA
    go_path: Path = GO
    receipt_path: Path = RECEIPT
    identity_files: Path = IDENTITY_FILES
    instrument_factory: Callable | None = None         # () -> ImageInstrument-like
    native_factory: Callable | None = None             # () -> (vmodel, processor, tokenizer, forward_fn)
    compute_identity: Callable | None = None           # () -> identity dict
    check_go: Callable | None = None                   # (ctx) -> go dict
    post_load: Callable | None = None                  # (instrument) -> {vocab_rows}
    pixels_fn: Callable = pixels
    original_sha_fn: Callable = sha_file
    budget_kwargs: dict = field(default_factory=dict)
    origins_check: Callable | None = None              # () -> None; default: guard.check_imported_origins
    verify_controller: bool = True
    supp_plan_path: Path | None = None                 # revision 16: the supplement's plan (supplement_ctx)
    stage_a_out: Path = OUT                            # revision 16: the frozen, accepted Stage A tree (read only)
    os_build_fn: Callable | None = None                # revision 16: () -> the OS build string; default os_build


def package_hashes(ctx: Ctx) -> dict:
    plan = json.loads(ctx.plan_path.read_text())
    return {"criteria_sha256": sha_file(ctx.criteria_path), "identity_sha256": sha_file(ctx.identity_path),
            "plan_sha256": sha_file(ctx.plan_path), "manifest_sha256": sha_file(ctx.manifest_path),
            "budget_sha256": budget_sha256(plan["envelope"])}


def load_frozen(ctx: Ctx) -> tuple[dict, dict]:
    plan = json.loads(ctx.plan_path.read_text())
    if plan.get("revision") != 7:
        raise SystemExit("refused: stage_a_plan.json is not revision 7")
    if budget_sha256(envelope()) != plan["budget_sha256"]:
        raise SystemExit("refused: the code's envelope differs from the frozen plan's")
    for k, name in (("dev_pool_sha256", "dev_pool.json"), ("provenance_checks_sha256", "provenance_checks.json")):
        if sha_file(HERE / name) != plan[k]:            # current source records must equal the reviewed pins (A8)
            raise SystemExit(f"refused: {name} differs from the plan's reviewed pin {k}")
    ids = [a["id"] for a in plan["attempts"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("refused: duplicate attempt ids in the plan")
    manifest = {r["concept"]: r for r in json.loads(ctx.manifest_path.read_text())["records"]}
    for k, h in plan["manifest_records_sha256"].items():
        if sha(json.dumps(manifest[k], sort_keys=True).encode()) != h:
            raise SystemExit(f"refused: manifest record {k} differs from the frozen plan's")
    return plan, manifest


class Hold(SystemExit):
    """An AUTHORISATION HOLD: an interrupted try lacks the owner's recovery file. Not an integrity failure; nothing
    ran; the run resumes once the file exists."""


def desk_gates(ctx: Ctx) -> dict:
    """The GATES worker's checks, before anything else is spawned (closure group 1): the frozen plan and manifest,
    the positions receipt (present, passing, for this plan), the go bound to an attestation of this exact package
    (re-derived at the reviewed commit, the identity's blobs included), a fresh execution identity equal to the
    frozen one, then crash reconciliation (an open attempt becomes an interrupted try, durably) and a recovery file
    for every interrupted try - its absence is a Hold, distinct from a refusal."""
    from enforce import reconcile_open_attempt
    from stage_a_guard import execution_identity, recovery_files, require_go
    plan, _ = load_frozen(ctx)
    check_receipt(ctx)
    pkg = package_hashes(ctx)
    (ctx.check_go or (lambda c: require_go(c.go_path, pkg, verify_at_commit=package_at_commit)))(ctx)
    frozen = json.loads(ctx.identity_path.read_text())
    ctx.out.mkdir(parents=True, exist_ok=True)
    tmp = ctx.out / "identity_files.gates.json"
    now = (ctx.compute_identity or (lambda: execution_identity(ctx.plan_path, ctx.manifest_path, ctx.receipt_path,
                                                               tmp)))()
    if now["identity_sha256"] != frozen["identity_sha256"]:
        raise SystemExit(f"refused: execution identity now {now['identity_sha256']} differs from the frozen "
                         f"{frozen['identity_sha256']}")
    from stage_a_guard import check_imported_origins          # the gates consume and check their own map (A1)
    (ctx.origins_check or (lambda: check_imported_origins(tmp, now["package_file_maps_sha256"])))()
    st = ctx.out / "stage_a_state.json"
    reconciled = reconcile_open_attempt(st)
    pending = json.loads(st.read_text())["interrupted"] if st.exists() else []
    files = {(f["attempt_id"], f["session"], f["try"]) for f in recovery_files(ctx.out)}
    missing = [i for i in pending if (i["id"], i["session"], i["try"]) not in files]
    out = {"package": pkg, "identity": now["identity_sha256"], "reconciled": reconciled, "missing_recovery": missing}
    recheck_identity(ctx, now)                                 # before GATES.json is committed (A1)
    if missing:
        raise Hold(json.dumps({**out, "hold_reason": "interrupted tries need an owner's recovery file each: " +
                               ", ".join(f"RECOVERY_{i['id']}__{i['session']}__{i['try']}.json" for i in missing)}))
    return out


def check_receipt(ctx: Ctx) -> dict:
    """The positions receipt must exist, pass, and be bound to this plan's bytes (absence, failure and staleness
    are three refusals)."""
    if not ctx.receipt_path.exists():
        raise SystemExit("refused: the positions receipt is absent")
    rc = json.loads(ctx.receipt_path.read_text())
    if rc.get("all_equal") is not True:
        raise SystemExit("refused: the positions receipt does not show the declared rule equal for both carriers")
    if rc.get("plan_sha256") != sha_file(ctx.plan_path):
        raise SystemExit("refused: the positions receipt is stale (bound to another plan)")
    return rc


def run_gates(ctx: Ctx | None = None) -> int:
    """The GATES worker: writes GATES.json (a finalisation-class write) for the controller; exit 0 = passed,
    4 = an authorisation hold; any refusal exits nonzero with nothing written as passed."""
    from enforce import configure_storage, write_json_atomic
    ctx = ctx or Ctx()
    _worker_storage(ctx)
    session = os.environ.get("STAGE_A_SESSION", "test")
    try:
        g = desk_gates(ctx)
    except Hold as h:
        d = json.loads(str(h.code))
        write_json_atomic(ctx.out / "GATES.json", {**d, "session": session, "passed": False, "hold": True},
                          final=True)
        return 4
    write_json_atomic(ctx.out / "GATES.json", {**g, "session": session, "passed": True, "hold": False}, final=True)
    return 0


def _worker_storage(ctx: Ctx) -> None:
    from enforce import CAPS, configure_storage
    cap = int(os.environ.get("STAGE_A_STORAGE_CAP", 0)) or CAPS["row20"]["bytes"]
    configure_storage([ctx.out], cap, int(os.environ.get("STAGE_A_STORAGE_LIMIT", 0)) or cap)


IDENTITY_BLOBS = {"plan_sha256": "stage_a_plan.json", "manifest_sha256": "manifest_dev.json",
                  "positions_receipt_sha256": "stage_a_positions_receipt.json",
                  "package_file_maps_sha256": "stage_a_identity_files.json"}


def _blob_reader(commit: str, repo: Path) -> Callable[[str], bytes]:
    def blob(rel: str) -> bytes:
        g = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"], capture_output=True)
        if g.returncode != 0:
            raise SystemExit(f"refused: {rel} absent at the reviewed commit {commit}")
        return g.stdout
    return blob


def _identity_describes_commit(ident: dict, blob: Callable[[str], bytes], photo: str, blobs: dict) -> None:
    """The identity committed at a reviewed commit hashes to its own identity_sha256, and every local-source digest,
    the packet source, the import map, the positions receipt, the plan and the manifest hash to their blobs at that
    commit (closure group 1). Revision 16 factors this out of package_at_commit (unchanged checks and messages) so the
    supplement's package re-derivation applies it to its own identity and import-map file."""
    body = {k: v for k, v in ident.items() if k != "identity_sha256"}
    if sha(json.dumps(body, sort_keys=True).encode()) != ident.get("identity_sha256"):
        raise SystemExit("refused: the identity at the reviewed commit does not hash to its own identity_sha256")
    bad = [f"{k} ({n})" for k, n in blobs.items() if sha(blob(f"{photo}/{n}")) != ident.get(k)]
    bad += [f"local_code_sha256[{n}]" for n, h in ident.get("local_code_sha256", {}).items()
            if sha(blob(f"{photo}/{n}")) != h]
    t1 = str(Path(photo).parents[1])
    if sha(blob(f"{t1}/stimuli/packet.py")) != ident.get("packet_py_sha256"):
        bad.append("packet_py_sha256")
    from stage_a_guard import LOCAL_CODE
    if sorted(ident.get("local_code_sha256", {})) != sorted(LOCAL_CODE):
        bad.append("local_code_sha256 does not cover exactly the declared local code")
    if bad:
        raise SystemExit(f"refused: the identity at the reviewed commit does not describe that commit's blobs: {bad}")


def package_at_commit(commit: str, repo: Path = RSC_ROOT, photo: str | None = None) -> dict:
    """The five package hashes as they were at the reviewed commit, AND proof that the identity committed there
    describes that commit's own blobs: its identity_sha256 recomputes; every local-source digest, the packet source,
    the import map, the positions receipt, the plan and the manifest hash to their blobs at the commit (closure
    group 1). Any disagreement refuses."""
    photo = photo or str(HERE.relative_to(RSC_ROOT))
    blob = _blob_reader(commit, repo)
    b = {k: blob(f"{photo}/{n}") for k, n in (("criteria", "STAGE_A_CRITERIA.md"), ("identity", "stage_a_identity.json"),
                                               ("plan", "stage_a_plan.json"), ("manifest", "manifest_dev.json"))}
    _identity_describes_commit(json.loads(b["identity"]), blob, photo, IDENTITY_BLOBS)
    plan = json.loads(b["plan"])
    return {"criteria_sha256": sha(b["criteria"]), "identity_sha256": sha(b["identity"]),
            "plan_sha256": sha(b["plan"]), "manifest_sha256": sha(b["manifest"]),
            "budget_sha256": budget_sha256(plan["envelope"])}


def worker_identity(ctx: Ctx, phase: str) -> tuple[dict, Path]:
    """Every worker recomputes the execution identity itself (closure group 1): it must equal the frozen identity
    and the identity the controller's gates admitted in this session. The per-file import map it writes is the map
    it consumes (check_imported_origins verifies its bytes against the identity's package_file_maps_sha256)."""
    from stage_a_guard import execution_identity
    files = ctx.out / f"identity_files.{phase}.json"
    ident = (ctx.compute_identity or (lambda: execution_identity(ctx.plan_path, ctx.manifest_path, ctx.receipt_path,
                                                                 files)))()
    frozen = json.loads(ctx.identity_path.read_text())["identity_sha256"]
    if ident["identity_sha256"] != frozen:
        raise SystemExit(f"refused: {phase}: execution identity {ident['identity_sha256']} differs from the frozen "
                         f"{frozen}")
    if ctx.verify_controller:
        g = json.loads(os.environ.get("STAGE_A_GATES") or "{}")
        if g.get("identity") != frozen:
            raise SystemExit(f"refused: {phase}: the identity differs from the one this session's gates admitted")
    return ident, files


def recheck_identity(ctx: Ctx, ident: dict) -> None:
    """Before a phase record is written: the local code, the packet, the plan, the manifest and the positions
    receipt still hash to the identity (code changed during a phase refuses)."""
    from stage_a_guard import LOCAL_CODE
    if ctx.compute_identity is not None:
        return
    bad = [n for n in LOCAL_CODE if sha_file(HERE / n) != ident["local_code_sha256"][n]]
    for k, pth in (("packet_py_sha256", T1 / "stimuli" / "packet.py"), ("plan_sha256", ctx.plan_path),
                   ("manifest_sha256", ctx.manifest_path), ("positions_receipt_sha256", ctx.receipt_path)):
        if sha_file(pth) != ident[k]:
            bad.append(k)
    if bad:
        raise StopCheck(f"identity changed during the phase: {bad}")


# ================================================================================================================
# Revision 12 (Codex 5eb51a8 A1): the REVIEWED COMPATIBILITY TRANSITION from a predecessor package's completed phases
# ================================================================================================================
# The one declared predecessor: Stage A revision 10 (RSC fbfb7db, favourable at RSC 3390183), whose run of 2 October
# completed the instrumented phase (158 attempts) and then stopped terminally. Its identity body is embedded here
# verbatim and must hash to its identity_sha256 (checked at use). A transition from it is admissible only when (1) the
# owner's TERMINAL_RELEASE.json names the run's terminal record (stage_a_guard.terminal_release), (2) every FROZEN
# component - plan, manifest, positions receipt, packet, the package file maps, the jlens/lens/dispatch/weights and
# machine fields - is byte-identical to the current identity's, and (3) the ledger holds no open or interrupted
# attempt. It then writes IDENTITY_TRANSITION.json (from, to, the predecessor's review, the release's sha256, the
# differing local code files with both hashes, the completed attempt ids and the counters at the transition) BEFORE
# the ledger's current-identity slot moves to the current package. Nothing else changes: the completed records stay
# bound to the predecessor (INSTRUMENTED_DONE.json keeps its identity), no counter is reset, no output relabelled, no
# attempt recomputed; pre-native admission and the final validator accept a phase record whose identity is the
# recorded transition's predecessor, with every other predicate unchanged.
PREDECESSOR_ID = "e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38"
PREDECESSOR = {"package": "Stage A revision 10, RSC fbfb7db", "review": "Codex RSC 3390183 (favourable)",
               "phases": ["instrumented"],
               "identity_body": json.loads(r'''{
 "dispatch": {
  "hidden_dtype": "bfloat16",
  "instrumented": {
   "GDN inference kernel per pass": true,
   "capture": "jlens_qwen.capture_endpoint._run, one StreamSession.extend per pass",
   "custom GDN VJP": "recorded (training-only path, unused in a prefill)",
   "jlens patch_gdn applied": true
  },
  "native": {
   "capture_layer_ids": null,
   "jlens_qwen imported": false,
   "prefill": "mlx-vlm get_input_embeddings + language_model(ids, inputs_embeds, fresh cache)"
  },
  "vision": "mlx-vlm qwen3_5 vision tower in its weight dtype; features cast to the hidden dtype at merge",
  "weights": "4-bit affine (snapshot quantization config)"
 },
 "jlens": {
  "head": "745a3a894be7043ae5eb7dbbdcec44b68b819411",
  "sitecustomize_sha256": "8b0b2acbe668ef4d994cad710557d57683d98a52c588e9bfe3e6dd1caa43afc9",
  "tracked_diff_sha256": "c5f7fac8b421a3c398bb2a36f4193d909f504573cdb323d5178342e3868926b9"
 },
 "lens": {
  "name": "qwen36_27b_neuronpedia_n1000.npz",
  "sha256": "1177e8fb529d9d81e8f379c9a5d02b4d11e05b3056f677bb223b7e6e23ce0aed"
 },
 "local_code_sha256": {
  "dose.py": "05d61ea6d199903eb066534e8cc2e7bb73e102b9cfa284f5692f8d75e9bb4302",
  "dose_report.py": "aff4afc3ac18455d0876da042d4202deaf428820ffaf09fde4603e32e14a825a",
  "enforce.py": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
  "image_adapter.py": "2c1c3cedc9559fe8b2f7fd31c82984255ac7072a1f6442fc5a3e098f56f901aa",
  "memprobe.py": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
  "stage_a.py": "1024c7eefc26c31ff8108b4a54d21bfd79d08337d8005b21e270737e82699267",
  "stage_a_controller.py": "922bea2245ccc381cc7c57e9880aba1b5ca34ed8f9a778936b58714186d28d2a",
  "stage_a_guard.py": "71031f606240c0ca93e41f22ceddcf9a78d1968a356803d00fff18b36749db70",
  "stage_a_report.py": "62839613895924afcb126dfbf7e970113fc5a4149f4b52572e5ae71bf9845b66",
  "stage_a_watchdog.py": "7a686c76fea6f9be8f21724d3690847c752a95b78f6389bc2792a9016a15736d"
 },
 "machine": "arm64",
 "macos": "27.0",
 "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
 "package_file_maps_sha256": "1cff193d3a630b6755ca095e93a2dc8445f37ebb8a48eacd0ff8f6fcb39c8ab8",
 "package_versions": {
  "PIL": "12.3.0",
  "huggingface_hub": "1.22.0",
  "mlx": "0.31.2",
  "mlx-metal": "0.31.2",
  "mlx_lm": "0.31.3",
  "mlx_vlm": "0.6.3",
  "numpy": "2.5.1",
  "pydantic": "2.13.5",
  "safetensors": "0.8.0",
  "tokenizers": "0.22.2",
  "transformers": "5.13.0"
 },
 "packet_py_sha256": "e4e0b6f8506b3af9f44b610e700ae12ba81cccb97d2982bd231611b2888c2eef",
 "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
 "positions_receipt_sha256": "db66fe563bc52f67d129d95d72d30d784de29858cf58d1f8db68eff847f1d334",
 "python": "3.12.14",
 "row": "20",
 "snapshot": {
  "files_sha256": {
   "chat_template.jinja": "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259",
   "config.json": "ede24666ac51e6d5ab948a8a1e6c72fc6effd941ba3aabb6dd942eb517c78043",
   "configuration.json": "2d4464e2ead06bc9bc718c781309ad1e7baded626d66e8dcdc8b469ba185faf0",
   "generation_config.json": "e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e",
   "model-00001-of-00003.safetensors": "2689680915661f040c50c35244d08b336def279e509e1ca11873f8dd1b0e7ce0",
   "model-00002-of-00003.safetensors": "a46183727b2c5cd16613fd8395f5e9e7cc4ad679644558cc87c9406fe334463d",
   "model-00003-of-00003.safetensors": "ac23bf70b1f239a040921d6f93770d74176fd435dbf44e42317053d06c68d702",
   "model.safetensors.index.json": "13b840162b4cb35c66fef7df072f7dbb4717908204364f5e5d9f9655a2758fa8",
   "preprocessor_config.json": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
   "processor_config.json": "51c5f33646392e0bf1ed3e96be02504da47406c21c6cb86925d8908d1a6c4da7",
   "tokenizer.json": "87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4",
   "tokenizer_config.json": "e98f1901ac6f0adff67b1d540bfa0c36ac1a0cf59eb72ed78146ef89aafa1182",
   "video_preprocessor_config.json": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
   "vocab.json": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003"
  },
  "id": "c000ac2c2057d94be3fa931000c31723aac53282"
 },
 "stage": "A"
}''')}
# Revision 13 (R052 handoff 8508993b, D): the SECOND declared predecessor - Stage A revision 12 (RSC 620f768,
# favourable at Codex RSC e7b31f0), whose resume of 3 October admitted the revision-10 instrumented phase through the
# first transition and then committed 16 native records (00- to 15-native) before its frozen logit criterion stopped it
# terminally at 15-native. Its identity body (stage_a_identity.json at 620f768 without identity_sha256) is embedded
# verbatim and must hash to its identity at use. The same rule as revision 12's A1 applies to it.
PREDECESSOR_12_ID = "c0fb2ea0f6c5ef83cdabd414cb7d761ec3aabd9de13ed6022a852a7b590da001"
PREDECESSOR_12 = {"package": "Stage A revision 12, RSC 620f768", "review": "Codex RSC e7b31f0 (favourable)",
                  "phases": ["native"],
                  # revision 15 (R052 handoff 6dc8029e): the ONE declared environment difference of this link - the
                  # machine took macOS 27.0 -> 27.0.1 (build 26A434) in the unplanned restart of 3 October; exactly
                  # this pair is admitted, nothing else
                  "environment_differences": {"macos": ["27.0", "27.0.1"]},
                  "identity_body": json.loads(r'''{
 "dispatch": {
  "hidden_dtype": "bfloat16",
  "instrumented": {
   "GDN inference kernel per pass": true,
   "capture": "jlens_qwen.capture_endpoint._run, one StreamSession.extend per pass",
   "custom GDN VJP": "recorded (training-only path, unused in a prefill)",
   "jlens patch_gdn applied": true
  },
  "native": {
   "capture_layer_ids": null,
   "jlens_qwen imported": false,
   "prefill": "mlx-vlm get_input_embeddings + language_model(ids, inputs_embeds, fresh cache)"
  },
  "vision": "mlx-vlm qwen3_5 vision tower in its weight dtype; features cast to the hidden dtype at merge",
  "weights": "4-bit affine (snapshot quantization config)"
 },
 "jlens": {
  "head": "745a3a894be7043ae5eb7dbbdcec44b68b819411",
  "sitecustomize_sha256": "8b0b2acbe668ef4d994cad710557d57683d98a52c588e9bfe3e6dd1caa43afc9",
  "tracked_diff_sha256": "c5f7fac8b421a3c398bb2a36f4193d909f504573cdb323d5178342e3868926b9"
 },
 "lens": {
  "name": "qwen36_27b_neuronpedia_n1000.npz",
  "sha256": "1177e8fb529d9d81e8f379c9a5d02b4d11e05b3056f677bb223b7e6e23ce0aed"
 },
 "local_code_sha256": {
  "dose.py": "05d61ea6d199903eb066534e8cc2e7bb73e102b9cfa284f5692f8d75e9bb4302",
  "dose_report.py": "aff4afc3ac18455d0876da042d4202deaf428820ffaf09fde4603e32e14a825a",
  "enforce.py": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
  "image_adapter.py": "2c1c3cedc9559fe8b2f7fd31c82984255ac7072a1f6442fc5a3e098f56f901aa",
  "memprobe.py": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
  "stage_a.py": "cbb27ef8c280d2c7bc70e9c7b657cb3973df251cfe03ad0b0d72398cc6f59953",
  "stage_a_controller.py": "3a47736dd5cb1f85c3b0b6bc2f2f189b7d5de359170a428760aefdc4153ae9c5",
  "stage_a_guard.py": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
  "stage_a_report.py": "42c134f35d682ca51aa67a936db47850c892a5e2c369c811dd602de646e7a511",
  "stage_a_watchdog.py": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed"
 },
 "machine": "arm64",
 "macos": "27.0",
 "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
 "package_file_maps_sha256": "1cff193d3a630b6755ca095e93a2dc8445f37ebb8a48eacd0ff8f6fcb39c8ab8",
 "package_versions": {
  "PIL": "12.3.0",
  "huggingface_hub": "1.22.0",
  "mlx": "0.31.2",
  "mlx-metal": "0.31.2",
  "mlx_lm": "0.31.3",
  "mlx_vlm": "0.6.3",
  "numpy": "2.5.1",
  "pydantic": "2.13.5",
  "safetensors": "0.8.0",
  "tokenizers": "0.22.2",
  "transformers": "5.13.0"
 },
 "packet_py_sha256": "e4e0b6f8506b3af9f44b610e700ae12ba81cccb97d2982bd231611b2888c2eef",
 "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
 "positions_receipt_sha256": "db66fe563bc52f67d129d95d72d30d784de29858cf58d1f8db68eff847f1d334",
 "python": "3.12.14",
 "row": "20",
 "snapshot": {
  "files_sha256": {
   "chat_template.jinja": "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259",
   "config.json": "ede24666ac51e6d5ab948a8a1e6c72fc6effd941ba3aabb6dd942eb517c78043",
   "configuration.json": "2d4464e2ead06bc9bc718c781309ad1e7baded626d66e8dcdc8b469ba185faf0",
   "generation_config.json": "e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e",
   "model-00001-of-00003.safetensors": "2689680915661f040c50c35244d08b336def279e509e1ca11873f8dd1b0e7ce0",
   "model-00002-of-00003.safetensors": "a46183727b2c5cd16613fd8395f5e9e7cc4ad679644558cc87c9406fe334463d",
   "model-00003-of-00003.safetensors": "ac23bf70b1f239a040921d6f93770d74176fd435dbf44e42317053d06c68d702",
   "model.safetensors.index.json": "13b840162b4cb35c66fef7df072f7dbb4717908204364f5e5d9f9655a2758fa8",
   "preprocessor_config.json": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
   "processor_config.json": "51c5f33646392e0bf1ed3e96be02504da47406c21c6cb86925d8908d1a6c4da7",
   "tokenizer.json": "87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4",
   "tokenizer_config.json": "e98f1901ac6f0adff67b1d540bfa0c36ac1a0cf59eb72ed78146ef89aafa1182",
   "video_preprocessor_config.json": "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
   "vocab.json": "ce99b4cb2983d118806ce0a8b777a35b093e2000a503ebde25853284c9dfa003"
  },
  "id": "c000ac2c2057d94be3fa931000c31723aac53282"
 },
 "stage": "A"
}''')}
PREDECESSORS = {PREDECESSOR_ID: PREDECESSOR, PREDECESSOR_12_ID: PREDECESSOR_12}
TRANSITION = "IDENTITY_TRANSITION.json"          # the first recorded transition; later ones IDENTITY_TRANSITION.<n>.json
FROZEN_KEYS = ("plan_sha256", "manifest_sha256", "positions_receipt_sha256", "packet_py_sha256",
               "package_file_maps_sha256", "jlens", "lens", "dispatch", "machine")
# Revision 15: `macos` left FROZEN_KEYS and is checked here instead - equal, or exactly a pair the predecessor DECLARES
# in its environment_differences (only revision 12's 27.0 -> 27.0.1); any other value on either side refuses.
ENVIRONMENT_KEYS = ("macos",)


def os_build() -> str | None:
    try:
        return subprocess.run(["/usr/bin/sw_vers", "-buildVersion"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except Exception:                                  # noqa: BLE001 - recorded as unknown, never guessed
        return None


def environment_differences(pred: dict, body: dict, current_ident: dict) -> list[dict]:
    """The declared environment differences of a transition (revision 15); refuses any undeclared one."""
    out = []
    for k in ENVIRONMENT_KEYS:
        a, b = body.get(k), current_ident.get(k)
        if a == b:
            continue
        if list(pred.get("environment_differences", {}).get(k) or []) != [a, b]:
            raise SystemExit(f"refused: the environment field {k} differs from the predecessor's ({a!r} -> {b!r}) "
                             f"and that pair is not declared for this predecessor; its outputs cannot be admitted")
        out.append({"field": k, "from": a, "to": b, **({"to_build": os_build()} if k == "macos" else {})})
    return out


def transition_record(out: Path) -> dict | None:
    """The FIRST recorded transition (revision 12's file name)."""
    p = out / TRANSITION
    return json.loads(p.read_text()) if p.exists() else None


def transition_records(out: Path) -> list[dict]:
    """Every recorded transition in order: IDENTITY_TRANSITION.json, then IDENTITY_TRANSITION.2.json, .3, ..."""
    first = transition_record(out)
    if first is None:
        return []
    recs, n = [first], 2
    while (out / f"IDENTITY_TRANSITION.{n}.json").exists():
        recs.append(json.loads((out / f"IDENTITY_TRANSITION.{n}.json").read_text()))
        n += 1
    return recs


def admitted_phase_identity(out: Path, phase_identity: str, current: str) -> bool:
    """A completed phase's producer identity is admitted under the current one when they are equal, or when the
    recorded transitions form an unbroken chain of DECLARED predecessors from exactly that identity to exactly the
    current one (revision 12: one link; revision 13: rev 10 -> rev 12 -> rev 13)."""
    if phase_identity == current:
        return True
    chain, at, started = transition_records(out), phase_identity, False
    for i, t in enumerate(chain):
        if i and t.get("from") != chain[i - 1].get("to"):
            return False                               # a broken chain admits nothing
        if t.get("from") == at and at in PREDECESSORS:
            at, started = t.get("to"), True
        elif started:
            return False
    return started and at == current


def attempt_environment(out: Path, aid: str, current: str | None, field: str = "macos") -> str | None:
    """Revision 15: the environment (macOS) an attempt's committed record was produced on, read from the recorded
    transitions: the 'from' value of the FIRST link that declares a difference in `field` and lists the attempt among
    its completed ids; otherwise (completed after every such link, or no such link) the current value."""
    for t in transition_records(out):
        for d in t.get("environment_differences") or []:
            if d.get("field") == field and aid in (t.get("completed_attempts") or []):
                return d.get("from")
    return current


def identity_transition(ctx, current_ident: dict) -> None:
    """Called by worker_open before the ledger opens: a no-op unless the ledger is bound to a DECLARED predecessor
    and the current package differs from it.

    TWO WRITES, IN THIS ORDER (revision 14, Codex c4bbcb5 R1): (1) the next transition link (IDENTITY_TRANSITION.json,
    then IDENTITY_TRANSITION.<n>.json), durable; (2) the ledger's identity slot (stage_a_state.json). A death or a failed
    write between them leaves a PREPARED TAIL: the last link runs from the ledger's identity to the current one while
    the ledger still holds its predecessor. ENVIRONMENT (revision 15): `macos` is not frozen; it must be equal or
    exactly a pair the predecessor declares (revision 12: 27.0 -> 27.0.1), recorded in the link's
    environment_differences with the build string. A later start RECONCILES a prepared tail idempotently - it
    completes ONLY write (2) - when every condition holds: the tail's from/to equal the ledger's identity and the current package identity; the chain
    before it is unbroken and ends at the ledger's identity; the current TERMINAL_RELEASE.json is valid for the current
    TERMINAL bytes (a release the controller's later failure invalidated cannot be reused - that failure needs its own
    release) and was consumed by no EARLIER link; the frozen inputs equal the predecessor's; no open or interrupted
    attempt; and the tail's recorded predecessor, frozen list, differing code files, completed attempt ids, counters
    and carry equal the ledger's and the package's now. Otherwise it refuses. A repeat finds the slot already moved and
    writes nothing; a reconciliation never appends a link, resets a counter or recomputes a record."""
    from stage_a_guard import terminal_release
    sp = ctx.out / "stage_a_state.json"
    if not sp.exists():
        return
    st = json.loads(sp.read_text())
    have, cur = (st.get("identities") or {}).get("row20"), current_ident["identity_sha256"]
    if have in (None, cur):
        return
    if have not in PREDECESSORS:
        return                                         # the ledger refuses the mismatch itself (enforce.Budget)
    pred = PREDECESSORS[have]
    body = pred["identity_body"]
    if sha(json.dumps(body, sort_keys=True).encode()) != have:
        raise SystemExit("refused: the declared predecessor's identity body does not hash to its identity")
    chain = transition_records(ctx.out)
    prepared = bool(chain) and chain[-1].get("from") == have and chain[-1].get("to") == cur and \
        (len(chain) == 1 or chain[-2].get("to") == have)
    before = chain[:-1] if prepared else chain
    if before and before[-1].get("to") != have:
        raise SystemExit("refused: the ledger's identity is not where the recorded transitions end")
    rel = terminal_release(ctx.out)
    if rel is None:
        raise SystemExit("refused: a predecessor's completed phases are admitted only under the owner's terminal "
                         "release (TERMINAL_RELEASE.json naming this run's terminal record)")
    if any(t.get("release_sha256") == rel["file_sha256"] for t in before):
        raise SystemExit("refused: this terminal release was already consumed by an earlier transition")
    differ = [k for k in FROZEN_KEYS if body.get(k) != current_ident.get(k)]
    if differ:
        raise SystemExit(f"refused: the frozen inputs differ from the predecessor's ({differ}); its outputs cannot be "
                         f"admitted")
    env = environment_differences(pred, body, current_ident)          # revision 15
    if st.get("open_attempt") or st.get("interrupted"):
        raise SystemExit("refused: an open or interrupted attempt in the predecessor's ledger; no transition")
    code_old, code_new = body.get("local_code_sha256", {}), current_ident.get("local_code_sha256", {})
    expect = {"from": have, "to": cur, "predecessor": {k: pred[k] for k in ("package", "review", "phases")},
              "local_code_differs": {n: {"from": code_old.get(n), "to": code_new.get(n)}
                                     for n in sorted(set(code_old) | set(code_new))
                                     if code_old.get(n) != code_new.get(n)},
              "frozen_identical": list(FROZEN_KEYS), "environment_differences": env,
              "completed_attempts": sorted(st.get("completed", {})),
              "counters": st.get("counters"), "carry_in": st.get("carry_in")}
    from enforce import write_json_atomic
    if prepared:                                       # revision 14 (R1): complete only the slot commit
        tail = chain[-1]
        bad = sorted(k for k, v in expect.items() if tail.get(k) != v)
        if bad:
            raise SystemExit(f"refused: the prepared transition record does not match the ledger and package ({bad})")
        st["identities"]["row20"] = cur
        write_json_atomic(sp, st, final=True)
        return
    rec = {**expect, "release_sha256": rel["file_sha256"], "wall": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    name = TRANSITION if not chain else f"IDENTITY_TRANSITION.{len(chain) + 1}.json"
    write_json_atomic(ctx.out / name, rec, final=True)           # write (1): durable BEFORE the ledger's slot moves
    st["identities"]["row20"] = cur
    write_json_atomic(sp, st, final=True)                        # write (2)


def worker_open(ctx: Ctx, phase: str, *, terminal_gate: bool = True):
    """A WORK worker's start: launched by the controller that holds the lock (closure group 3); the terminal gate;
    the frozen inputs; the attempt ledger; consumption of any recovery file that names one of its interrupted tries
    (closure group 2)."""
    from enforce import Budget
    from stage_a_guard import check_terminal, recovery_files
    _check_controller(ctx)
    _worker_storage(ctx)
    if terminal_gate:
        check_terminal(ctx.out)
    plan, manifest = load_frozen(ctx)
    cur_ident = json.loads(ctx.identity_path.read_text())
    identity_transition(ctx, cur_ident)                    # revisions 12-13: reviewed predecessors' phases (A1, D)
    ident = cur_ident["identity_sha256"]
    budget = Budget(ctx.out / "stage_a_state.json", "row20", ident, [ctx.out],
                    os.environ.get("STAGE_A_SESSION", "test"), carry_in=ENGINEERING_CARRY,
                    storage_limit=int(os.environ.get("STAGE_A_STORAGE_LIMIT", 0)) or None, **ctx.budget_kwargs)
    for f in recovery_files(ctx.out):
        key = (f["attempt_id"], f["session"], f["try"])
        if any((i["id"], i["session"], i["try"]) == key for i in budget.state["interrupted"]):
            budget.authorise_recovery(f)
    if budget.state["interrupted"]:
        raise Hold(f"refused: interrupted tries without a recovery file: {budget.state['interrupted']}")
    return budget, plan, manifest


def _check_controller(ctx: Ctx) -> None:
    if ctx.verify_controller:
        cpid = os.environ.get("STAGE_A_CONTROLLER_PID")
        lock = json.loads((ctx.out / "LOCK").read_text() or "{}") if (ctx.out / "LOCK").exists() else {}
        if not cpid or int(cpid) != os.getppid() or lock.get("pid") != int(cpid):
            raise SystemExit("refused: a worker runs only under the controller that holds the task lock")


# ================================================================================================================
# Admission of one input (frozen hashes, structure, processor) - both phases
# ================================================================================================================
def admit_input(ctx: Ctx, x: dict, manifest: dict, image_processor, full_processor, tok) -> tuple[dict, dict]:
    from image_adapter import build_sequence, check_against_processor
    op = original_path(x)
    if op is not None:
        got = ctx.original_sha_fn(op)
        if got != x["original_sha256"] or got != manifest[x["concept"]]["original_sha256"]:
            raise StopCheck(f"input {x['index']}: original bytes {got} differ from the frozen plan/manifest")
    elif x["original_sha256"] is not None:
        raise StopCheck(f"input {x['index']}: noise-only input carries an original")
    px = ctx.pixels_fn(x, image_processor)
    if px["png_sha256"] != x["png_sha256"]:
        raise StopCheck(f"input {x['index']}: PNG {px['png_sha256']} differs from the frozen {x['png_sha256']}")
    if px["pixel_values_sha256"] != x["pixel_values_sha256"]:
        raise StopCheck(f"input {x['index']}: delivered tensor differs from the frozen hash")
    if list(px["grid"]) != list(x["grid_thw"]):
        raise StopCheck(f"input {x['index']}: grid {px['grid']} differs from the frozen {x['grid_thw']}")
    if not np.all(np.isfinite(px["pv"])):
        raise StopCheck(f"input {x['index']}: nonfinite pixel values")
    seq = build_sequence(tok, x["carrier"], px["grid"])
    check_sequence_structure(seq)
    for k, v in x["expected"].items():
        if k != "positions_sha256" and seq[k] != v:
            raise StopCheck(f"input {x['index']}: {k} {seq[k]} differs from the frozen {v}")
    chk = check_against_processor(full_processor, seq, px["image"])
    if not (chk["ids_equal"] and chk["grid_equal"] and chk["pixel_values_sha256"] == x["pixel_values_sha256"]):
        raise StopCheck(f"input {x['index']}: processor check failed {chk}")
    return px, seq


def check_tokenizer(plan: dict, tok) -> None:
    from stimuli.packet import encode
    for r in plan["request_tokens"]:
        if encode(tok, " " + r["concept"]) != [r["id"]]:
            raise StopCheck(f"E1 id of {r['concept']} differs under the loaded tokenizer")


# ================================================================================================================
# The instrumented phase
# ================================================================================================================
def edits_for(ce, case: str, x: dict, seq: dict, plain_res: np.ndarray | None):
    mp = seq["marker_positions"]
    E = lambda **k: ce.CaptureEdit(layer=EDIT_LAYER, positions=mp, **k)
    table = {
        "plain": lambda: None,
        "repeat": lambda: None,                                    # explicit no-edit delayed repeat
        "suffix_isolation": lambda: None,
        "empty": lambda: [],
        "zero_steer": lambda: [E(mode="steer", alpha=0.0, token_id=x["target_id"])],
        "zero_ablate": lambda: [E(mode="ablate", alpha=0.0, ablate_token_ids=[x["target_id"]])],
        "zero_swap": lambda: [E(mode="swap_delta", alpha=0.0, token_id=x["target_id"], target_id=x["foil_id"])],
        "swap1": lambda: [E(mode="swap_delta", alpha=1.0, token_id=x["target_id"], target_id=x["foil_id"])],
        "ablate1": lambda: [E(mode="ablate", alpha=1.0, ablate_token_ids=[x["target_id"]])],
        "self_patch": lambda: [E(mode="patch", vectors_dtype="bfloat16", vectors_b64=base64.b64encode(
            np.ascontiguousarray(plain_res[EDIT_LAYER]).tobytes()).decode())],
    }
    if case not in table:
        raise ValueError(f"unknown case {case!r}")
    return table[case]()


def validate_pass(r: dict, x: dict, seq: dict, case: str, plan: dict, ctx_expect: dict) -> None:
    """Every per-pass identity and finiteness check of framework §8.4 (d), (e) on the instrumented path."""
    n = seq["n"]
    img = r["image"]
    want_edits = {"plain": None, "repeat": None, "suffix_isolation": None, "empty": 0}.get(case, 1)
    checks = {
        "n_tokens": r["n_tokens"] == n,
        "input_ids": r["input_ids_sha256"] == seq["ids_sha256"],
        "readout": r["readout_positions"] == seq["marker_positions"],
        "layers": r["capture_layers"] == LAYERS,
        "residual dtype/shape": r["residuals"]["dtype"] == "bfloat16" and
                                r["residuals"]["shape"] == [N_LAYERS, N_MARKER, D_MODEL],
        "logits n": r["final_logits"]["n"] == ctx_expect["vocab_rows"],
        "requested order": [q["id"] for q in r["requested"]] == plan["request_token_ids"],
        "requested finite": all(np.isfinite(q["logit"]) for q in r["requested"]),
        "gdn kernel": r.get("gdn_inference_kernel") is True,
        "edits": (not r["edits_installed"]) if want_edits is None else
                 (r["edits_installed"] and len(r["edit_log"]) == want_edits),
        "pixels": img["pixel_values_sha256"] == x["pixel_values_sha256"],
        "grid": img["grid_thw"] == x["grid_thw"],
        "144 tokens": img["n_image_tokens"] == N_IMAGE_TOKENS and img["features_shape"] == [N_IMAGE_TOKENS, D_MODEL],
        "features finite": img["features_all_finite"] is True,
        "boundary finite": img["boundary_mean_all_finite"] is True,
        "positions frozen": img["positions_sha256"] == x["expected"]["positions_sha256"],
        "positions effective == injected": img["effective_positions_sha256"] == img["positions_sha256"],
        "rope calls (one prefill)": [tuple(c) for c in img["rope_calls"]] == [(0, n)] * 32,
        "one embed call (one prefill)": img["embed_calls_this_pass"] == 1,
        "merge image rows": bool(img["merge"]) and img["merge"]["image_rows_equal_features"] is True,
        "merge text rows": bool(img["merge"]) and img["merge"]["text_rows_equal_embeddings"] is True,
        "merge one contiguous span": bool(img["merge"]) and img["merge"]["image_rows_contiguous"] is True and
                                     img["merge"]["n_image_rows"] == N_IMAGE_TOKENS,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad:
        raise StopCheck(f"{x['index']:02d}-{case}: per-pass checks failed: {bad}")


def residual_array(r: dict) -> np.ndarray:
    a = np.frombuffer(base64.b64decode(r["residuals"]["b64"]), dtype=np.uint16)
    return a.reshape(N_LAYERS, N_MARKER, D_MODEL)


def save_outputs(budget, out: Path, aid: str, arrays: dict[str, np.ndarray], record: dict) -> dict[str, str]:
    """Write each array and the record durably, re-read and checksum them; return {relative path: sha256}."""
    from enforce import write_atomic, write_json_atomic
    outputs = {}
    budget.reserve(sum(a.nbytes for a in arrays.values()) + 65536)
    for name, a in arrays.items():
        rel = f"passes/{aid}.{name}.npy"
        buf = io.BytesIO()
        np.save(buf, np.ascontiguousarray(a), allow_pickle=False)
        (out / "passes").mkdir(parents=True, exist_ok=True)
        write_atomic(out / rel, buf.getvalue())
        outputs[rel] = sha((out / rel).read_bytes())
        if outputs[rel] != sha(buf.getvalue()):
            raise StopCheck(f"{rel}: re-read checksum differs from the bytes written")
    rel = f"passes/{aid}.json"
    write_json_atomic(out / rel, {**record, "arrays": {k: v for k, v in outputs.items()}})
    outputs[rel] = sha((out / rel).read_bytes())
    return outputs


def load_outputs(out: Path, aid: str, outputs: dict[str, str]) -> tuple[dict, dict[str, np.ndarray]]:
    """Reload a committed attempt WITHOUT a forward; a missing or corrupt output holds for diagnosis."""
    arrays, record = {}, None
    for rel, h in outputs.items():
        p = out / rel
        if not p.exists():
            raise StopCheck(f"{aid}: committed output {rel} is missing - hold for diagnosis")
        if sha(p.read_bytes()) != h:
            raise StopCheck(f"{aid}: committed output {rel} fails its checksum - hold for diagnosis")
        if rel.endswith(".npy"):
            arrays[rel.split(".")[-2]] = np.load(p, allow_pickle=False)
        else:
            record = json.loads(p.read_text())
    if record is None:
        raise StopCheck(f"{aid}: committed record missing - hold for diagnosis")
    return record, arrays


def bitwise_key(rec: dict) -> tuple:
    return rec["residuals_sha256"], rec["logits_sha256"], rec["image"]["features_sha256"]


def run_instrumented(ctx: Ctx | None = None) -> dict:
    ctx = ctx or Ctx()
    from stage_a_guard import set_terminal
    budget, plan, manifest = worker_open(ctx, "instrumented")
    try:
        ident, files = worker_identity(ctx, "instrumented")
        inst = (ctx.instrument_factory or default_instrument)()
        expect = (ctx.post_load or post_load_instrumented)(inst)
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(
            files, ident["package_file_maps_sha256"])))()
        check_tokenizer(plan, inst.tok)
        ce, image_proc, full_proc = inst.ce, inst.processor.image_processor, inst.processor
        inputs = {x["index"]: x for x in plan["inputs"]}
        prepared: dict[int, tuple] = {}
        recs: dict[str, dict] = {}
        plain_res: dict[int, np.ndarray] = {}
        suffix = {s["base_index"]: s for s in plan["diagnostics"]["suffix_isolation"]}
        for a in (a for a in plan["attempts"] if a["phase"] == "instrumented"):
            x, aid, case = inputs[a["index"]], a["id"], a["case"]
            if x["index"] not in prepared:
                prepared[x["index"]] = admit_input(ctx, x, manifest, image_proc, full_proc, inst.tok)
            px, seq = prepared[x["index"]]
            if case == "suffix_isolation":
                seq = apply_suffix(seq, suffix[x["index"]]["replacement"])
                if seq["ids_sha256"] != suffix[x["index"]]["ids_sha256"]:
                    raise StopCheck(f"{aid}: perturbed ids differ from the declared diagnostic")
            done = budget.completed(aid)
            if done is not None:
                rec, arrays = load_outputs(ctx.out, aid, done)
                _admit_resumed(rec, arrays, a, x, plan, suffix, aid)
            else:
                ed = edits_for(ce, case, x, seq, plain_res.get(x["index"]))
                with budget.attempt(aid, a["kind"], passes=1) as att:
                    r = inst.capture(seq, px["pv"], capture_layers=LAYERS, request_token_ids=plan["request_token_ids"],
                                     top_k=TOP_K, edits=ed)
                    validate_pass(r, x, seq, case, plan, expect)
                    res = residual_array(r)
                    if sha(res.tobytes()) != r["residuals"]["sha256"]:
                        raise StopCheck(f"{aid}: residual bytes differ from the capture's own hash")
                    rec = {k: r[k] for k in INST_CAPTURE_KEYS}
                    rec.update(record_schema=INST_SCHEMA, id=aid, case=case, index=x["index"], kind=a["kind"],
                               residuals_meta={k: r["residuals"][k] for k in ("dtype", "shape", "sha256")},
                               final_logits={k: r["final_logits"][k] for k in ("dtype", "n", "sha256")},
                               residuals_sha256=r["residuals"]["sha256"], logits_sha256=r["final_logits"]["sha256"])
                    att.commit(save_outputs(budget, ctx.out, aid, {"residuals": res}, rec))
                arrays = {"residuals": res}
            if rec["case"] != case or rec["index"] != x["index"] or rec["id"] != aid:
                raise StopCheck(f"{aid}: reloaded record names another attempt")
            if sha(np.ascontiguousarray(arrays["residuals"]).tobytes()) != rec["residuals_sha256"] or \
                    arrays["residuals"].shape != (N_LAYERS, N_MARKER, D_MODEL):
                raise StopCheck(f"{aid}: residual array fails its hash or shape")
            recs[aid] = rec
            if case == "plain":
                plain_res[x["index"]] = arrays["residuals"]
            elif case in BITWISE and bitwise_key(rec) != bitwise_key(recs[f"{x['index']:02d}-plain"]):
                raise StopCheck(f"{aid}: differs from plain - bitwise parity failure")
            elif case == "suffix_isolation" and rec["residuals_sha256"] != recs[f"{x['index']:02d}-plain"][
                    "residuals_sha256"]:
                raise StopCheck(f"{aid}: marker residuals changed when only later suffix ids changed - "
                                f"future-suffix isolation failure")
        enc = plan["diagnostics"]["encoder_sensitivity"]["pair"]
        r0, r1 = (recs[f"{i:02d}-plain"]["image"] for i in enc)
        enc_ok = (r0["pixel_values_sha256"] != r1["pixel_values_sha256"] and r0["grid_thw"] == r1["grid_thw"]
                  and r0["features_sha256"] != r1["features_sha256"])
        if not enc_ok:
            raise StopCheck(f"encoder sensitivity failed on the declared pair {enc}")
        summary = finish_instrumented(ctx, budget, plan, recs, enc, ident)
        return summary
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            set_terminal(ctx.out, "instrumented", f"{type(exc).__name__}: {exc}")
        raise


def _admit_resumed(rec: dict, arrays: dict, a: dict, x: dict, plan: dict, suffix: dict, aid: str,
                   plain: dict | None = None) -> None:
    """A committed record reloaded on resumption passes the phase's full independent predicates before any use (A6)."""
    import stage_a_report as R
    v = R.V()
    v.need((rec.get("id"), rec.get("index"), rec.get("case"), rec.get("kind")) ==
           (aid, a["index"], a["case"], a["kind"]), "RECORD_ID", aid)
    if a["phase"] == "instrumented":
        R._inst(rec, arrays, a, x, plan, suffix, D_MODEL, v, aid)
    else:
        R._nat(rec, arrays, x, plan, plain, D_MODEL, v, aid)
    if v.failures:
        raise StopCheck(f"{aid}: the resumed record fails admission: {[f['code'] for f in v.failures][:6]}")


def finish_instrumented(ctx: Ctx, budget, plan: dict, recs: dict, enc: list, ident: dict) -> dict:
    from enforce import write_json_atomic
    ids = [a["id"] for a in plan["attempts"] if a["phase"] == "instrumented"]
    if sorted(recs) != sorted(ids) or len(set((r["index"], r["case"]) for r in recs.values())) != len(ids):
        raise StopCheck("instrumented phase incomplete or ids not unique")
    recheck_identity(ctx, ident)
    budget.final_size()
    done = {"phase": "instrumented", "attempts": {i: budget.completed(i) for i in ids},
            "encoder_sensitivity": {"pair": enc, "passed": True}, "identity": budget.identity}
    write_json_atomic(ctx.out / "INSTRUMENTED_DONE.json", done, final=True)
    return {"instrumented": len(ids), "counters": budget.state["counters"]["row20"]}


def default_instrument():
    from image_adapter import ImageInstrument
    return ImageInstrument()


def post_load_instrumented(inst) -> dict:
    from jlens_qwen import patch_gdn
    from jlens_qwen.capture_endpoint import _get_hidden_dtype, dtype_name
    if not (inst.model.n_layers == N_LAYERS and inst.model.d_model == D_MODEL):
        raise StopCheck("loaded model dimensions differ from the declared 64 x 5120")
    if dtype_name(_get_hidden_dtype(inst.S)) != "bfloat16":
        raise StopCheck("hidden dtype is not the declared bfloat16")
    if not patch_gdn._PATCHED:
        raise StopCheck("jlens patch_gdn not applied")
    return {"vocab_rows": int(inst.model._lm_head.weight.shape[0])}


# ================================================================================================================
# The native phase
# ================================================================================================================
def admit_native(ctx: Ctx, plan: dict, budget) -> dict:
    """§8.4 (l): all 140 mandatory instrumented cases (and the 18 diagnostics) committed, unique, re-verified."""
    p = ctx.out / "INSTRUMENTED_DONE.json"
    if not p.exists():
        raise SystemExit("refused: the instrumented phase has not completed")
    done = json.loads(p.read_text())
    ids = [a["id"] for a in plan["attempts"] if a["phase"] == "instrumented"]
    if sorted(done["attempts"]) != sorted(ids) or \
            not admitted_phase_identity(ctx.out, done["identity"], budget.identity):      # revision 12 (A1)
        raise StopCheck("INSTRUMENTED_DONE.json does not cover the planned instrumented attempts")
    plains, seen = {}, set()
    for aid in ids:
        outs = budget.completed(aid)
        if outs is None or outs != done["attempts"][aid]:
            raise StopCheck(f"{aid}: not committed in the state file, or its outputs differ from the phase record")
        rec, arrays = load_outputs(ctx.out, aid, outs)
        key = (rec["index"], rec["case"])
        if key in seen or rec["id"] != aid:
            raise StopCheck(f"{aid}: duplicate or misnamed record")
        seen.add(key)
        r = arrays["residuals"]
        if r.shape != (N_LAYERS, N_MARKER, D_MODEL) or r.dtype != np.uint16 or \
                sha(np.ascontiguousarray(r).tobytes()) != rec["residuals_sha256"]:
            raise StopCheck(f"{aid}: residual array fails shape, dtype or hash")
        if rec["case"] == "plain":
            plains[rec["index"]] = (rec, r)
    if len(plains) != len(plan["inputs"]):
        raise StopCheck("plain records missing")
    import stage_a_report as R                                 # the full instrumented validator BEFORE native (A6)
    val = R.validate(ctx.out, plan, budget.state, identity=budget.identity, phases=("instrumented",))
    if not val["pass"]:
        raise StopCheck(f"pre-native admission failed: {[(f['code'], f['where']) for f in val['failures']][:6]}")
    return plains


def default_native():
    from mlx_vlm import load as vload
    from transformers import AutoTokenizer
    from image_adapter import SNAPSHOT, native_forward
    vmodel, processor = vload(str(SNAPSHOT))
    return vmodel, processor, AutoTokenizer.from_pretrained(str(SNAPSHOT)), native_forward


def bf16_to_f32(u16: np.ndarray) -> np.ndarray:
    return (u16.astype(np.uint32) << 16).view(np.float32)


def compare(inst_u16: np.ndarray, nat: np.ndarray, li: np.ndarray, ln: np.ndarray) -> dict:
    """Relative L2 per layer = ||inst - nat|| / ||inst|| over the three marker rows x 5,120, with the FP32 residuals
    accumulated in FP64; the instrumented norm is the denominator and must be finite and non-zero."""
    inst = bf16_to_f32(inst_u16).reshape(N_LAYERS, -1).astype(np.float64)
    natr = nat.reshape(N_LAYERS, -1).astype(np.float64)
    den = np.linalg.norm(inst, axis=1)
    if not (np.all(np.isfinite(den)) and np.all(den > 0)):
        raise StopCheck("an instrumented reference norm is zero or nonfinite")
    rel = np.linalg.norm(inst - natr, axis=1) / den
    d = np.abs(li - ln)
    row = {"rel_l2_by_layer": rel.tolist(), "rel_l2_max": float(rel.max()), "rel_l2_argmax_layer": int(rel.argmax()),
           "ref_norm_min": float(den.min()), "logit_abs_diff": d.tolist(), "logit_max_abs": float(d.max()),
           "argmax_inst": int(li.argmax()), "argmax_native": int(ln.argmax())}
    stats = [row["rel_l2_max"], row["logit_max_abs"], row["ref_norm_min"], *row["rel_l2_by_layer"]]
    if not all(np.isfinite(stats)) or not (np.all(np.isfinite(li)) and np.all(np.isfinite(ln))):
        raise StopCheck("a comparison statistic is nonfinite")
    # revision 13: the per-logit tolerance; the row reports the largest difference with the magnitude, tolerance and
    # bf16 steps at it, and the worst logit (largest difference / tolerance), which decides the logit criterion
    mag = np.maximum(np.abs(li), np.abs(ln))
    tol = np.array([logit_tolerance(m) for m in mag])
    step = np.array([bf16_step(m) for m in mag])
    k, w = int(d.argmax()), int((d / tol).argmax())
    row.update({"logit_max_abs_magnitude": float(mag[k]), "logit_max_abs_tolerance": float(tol[k]),
                "logit_max_abs_bf16_steps": float(d[k] / step[k]) if step[k] > 0 else None,
                "logit_worst_index": w, "logit_worst_abs": float(d[w]), "logit_worst_magnitude": float(mag[w]),
                "logit_worst_tolerance": float(tol[w]),
                "logit_worst_bf16_steps": float(d[w] / step[w]) if step[w] > 0 else None,
                "logit_within_tolerance": bool(np.all(d <= tol))})
    row["argmax_equal"] = row["argmax_inst"] == row["argmax_native"]
    row["pass"] = row["rel_l2_max"] <= TOL["rel_l2"] and row["logit_within_tolerance"] and row["argmax_equal"]
    return row


def parity_failure(aid: str, row: dict) -> str:
    """The StopCheck text for a failing parity row (revision 13: the worst logit's magnitude, tolerance and steps)."""
    return (f"{aid}: native parity failed (rel_l2_max {row['rel_l2_max']:.3g}, argmax_equal {row['argmax_equal']}, "
            f"logit max abs {row['logit_max_abs']:.3g}; worst logit: difference {row['logit_worst_abs']:.4g} at "
            f"magnitude {row['logit_worst_magnitude']:.4g}, tolerance {row['logit_worst_tolerance']:.4g}, "
            f"{row['logit_worst_bf16_steps']} bf16 steps)")


def run_native(ctx: Ctx | None = None) -> dict:
    ctx = ctx or Ctx()
    from stage_a_guard import set_terminal
    budget, plan, manifest = worker_open(ctx, "native")
    try:
        ident, files = worker_identity(ctx, "native")
        plains = admit_native(ctx, plan, budget)
        vmodel, processor, tok, forward = (ctx.native_factory or default_native)()
        if any(m == "jlens_qwen" or m.startswith("jlens_qwen.") for m in sys.modules):
            raise StopCheck("jlens_qwen is imported in the native process: the dispatch is not mlx-vlm's own")
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(
            files, ident["package_file_maps_sha256"])))()
        check_tokenizer(plan, tok)
        inputs = {x["index"]: x for x in plan["inputs"]}
        req = plan["request_token_ids"]
        rows = []
        for a in (a for a in plan["attempts"] if a["phase"] == "native"):
            x, aid = inputs[a["index"]], a["id"]
            px, seq = admit_input(ctx, x, manifest, processor.image_processor, processor, tok)
            done = budget.completed(aid)
            if done is not None:
                rec, arrays = load_outputs(ctx.out, aid, done)
                _admit_resumed(rec, arrays, a, x, plan, {}, aid, plain=plains[x["index"]][0])
            else:
                with budget.attempt(aid, a["kind"], passes=1) as att:
                    nat = forward(vmodel, seq, px["pv"], LAYERS, seq["marker_positions"])
                    res, logits = np.asarray(nat["residuals"], dtype=np.float32), np.asarray(nat["logits"])
                    checks = {"shape": res.shape == (N_LAYERS, N_MARKER, D_MODEL),
                              "residuals finite": bool(np.all(np.isfinite(res))),
                              "logits finite": bool(np.all(np.isfinite(logits))),
                              "one prefill": nat["decoder_calls"] == {"min": 1, "max": 1, "layers": N_LAYERS},
                              "positions": nat["effective_positions_sha256"] == x["expected"]["positions_sha256"],
                              "merged embeddings == the instrumented merge (bitwise)":
                                  nat["inputs_embeds_sha256"] == plains[x["index"]][0]["image"]["merge"]["merged_sha256"]}
                    bad = [k for k, ok in checks.items() if not ok]
                    if bad:
                        raise StopCheck(f"{aid}: native checks failed: {bad}")
                    rec = {"record_schema": NAT_SCHEMA, "id": aid, "index": x["index"], "case": "native",
                           "kind": a["kind"], "inputs_embeds_dtype": nat.get("inputs_embeds_dtype"),
                           "requested_logits": logits[req].astype(np.float64).tolist(),
                           "logits_sha256": sha(np.ascontiguousarray(logits).tobytes()), "logits_n": int(logits.size),
                           "residuals_sha256": sha(np.ascontiguousarray(res).tobytes()),
                           "decoder_calls": nat["decoder_calls"],
                           "effective_positions_sha256": nat["effective_positions_sha256"],
                           "inputs_embeds_sha256": nat["inputs_embeds_sha256"],
                           "inputs_embeds_equal_instrumented_merge": nat["inputs_embeds_sha256"] ==
                           plains[x["index"]][0]["image"]["merge"]["merged_sha256"]}
                    att.commit(save_outputs(budget, ctx.out, aid, {"residuals": res}, rec))
                arrays = {"residuals": res}
            nres = arrays["residuals"]
            if nres.shape != (N_LAYERS, N_MARKER, D_MODEL) or sha(np.ascontiguousarray(nres).tobytes()) != \
                    rec["residuals_sha256"] or not np.all(np.isfinite(nres)):
                raise StopCheck(f"{aid}: native residuals fail shape, hash or finiteness")
            if rec["inputs_embeds_sha256"] != plains[x["index"]][0]["image"]["merge"]["merged_sha256"] or \
                    rec["decoder_calls"] != {"min": 1, "max": 1, "layers": N_LAYERS} or \
                    rec["effective_positions_sha256"] != x["expected"]["positions_sha256"]:
                raise StopCheck(f"{aid}: native embedding digest, decoder calls or positions differ (also checked "
                                f"on reloaded outputs)")
            prec, pres = plains[x["index"]]
            li = np.array([q["logit"] for q in prec["requested"]], dtype=np.float64)
            ln = np.asarray(rec["requested_logits"], dtype=np.float64)
            row = {"index": x["index"], "id": aid, **compare(pres, nres, li, ln),
                   "inputs_embeds_equal_instrumented_merge": rec["inputs_embeds_equal_instrumented_merge"]}
            rows.append(row)
            if not row["pass"]:
                raise StopCheck(parity_failure(aid, row))
        finish_native(ctx, budget, plan, rows, ident)
        return {"native": len(rows), "counters": budget.state["counters"]["row20"]}
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            set_terminal(ctx.out, "native", f"{type(exc).__name__}: {exc}")
        raise


def finish_native(ctx: Ctx, budget, plan: dict, rows: list, ident: dict) -> None:
    from enforce import write_json_atomic
    ids = [a["id"] for a in plan["attempts"] if a["phase"] == "native"]
    for aid in ids:                                        # all 20 re-validated from disk before any pass report
        load_outputs(ctx.out, aid, budget.completed(aid) or {})
    if [r["id"] for r in rows] != ids or not all(r["pass"] for r in rows):
        raise StopCheck("native results incomplete or failing")
    recheck_identity(ctx, ident)
    budget.final_size()
    write_json_atomic(ctx.out / "native_parity.json", rows, final=True)
    write_json_atomic(ctx.out / "NATIVE_DONE.json", {"phase": "native", "attempts": {i: budget.completed(i)
                                                                                      for i in ids}}, final=True)


# ================================================================================================================
# The report phase (inside A's clock; runs after a pass or after a stop)
# ================================================================================================================
def run_report(ctx: Ctx | None = None) -> dict:
    """The report WORKER: runs after a pass or a stop (no terminal gate), inside the controller's report reserve. It
    READS the ledger (enforce.read_ledger) - an open or interrupted attempt is described, never converted, granted or
    consumed - and recomputes the execution identity itself. It is ADMISSIBLE only when this session's gates passed
    (STAGE_A_GATES) and its own fresh identity equals the frozen one; otherwise it is labelled a diagnostic STOPPED
    report that confers nothing."""
    import stage_a_report
    from enforce import read_ledger
    ctx = ctx or Ctx()
    _check_controller(ctx)
    _worker_storage(ctx)
    plan, _ = load_frozen(ctx)
    gates = json.loads(os.environ.get("STAGE_A_GATES") or "{}")
    session = os.environ.get("STAGE_A_SESSION", "test")
    try:
        ident, files = worker_identity(ctx, "report")
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(     # its own map (A1)
            files, ident["package_file_maps_sha256"])))()
        ident_ok, why = True, ""
    except SystemExit as exc:
        ident_ok, why = False, str(exc)
    admissible = bool(gates.get("passed") is True and gates.get("session") == session and ident_ok)
    frozen = json.loads(ctx.identity_path.read_text())["identity_sha256"]
    return stage_a_report.build(ctx.out, plan, read_ledger(ctx.out / "stage_a_state.json"), admissible=admissible,
                                session=session, gates=gates, identity=frozen, identity_problem=why,
                                before_receipt=(lambda: recheck_identity(ctx, ident)) if ident_ok else None)


# ================================================================================================================
# Revision 16: the ROW-20 OS-BRIDGE SUPPLEMENT (Codex b0db0f9 §"Prospective row21 OS bridge"; R052 handoff 8266e5ae
# item 2; STAGE_A_SUPPLEMENT_CRITERIA.md). Built and tested only: no forward before Codex's record on this package
# and the owner's go (ROW20S_GO.json, stage "A-supplement").
# ================================================================================================================
# The accepted Stage A tree (captures/photo_stage_a) is FROZEN and only read: its ledger, controller record, final,
# marker, acceptance, transitions and every record stay byte-identical (pinned in the supplement plan, re-checked by
# every supplement worker). The supplement writes only its own tree (captures/photo_stage_a_supplement): its own
# ledger, which CARRIES Stage A's row-20 counters (194/193/1/194) so that its two starts are row 20's 195th and
# 196th of 200; its own controller record, which carries Stage A's row-20 seconds; its own storage cap, row 20's
# 1 GiB less the frozen tree's bytes. Input 00 (the original DEV-CAL input) only, fixed by id and hashes.
#   00-plain-os2701   one plain INSTRUMENTED forward on macOS 27.0.1 - comparison (a) against input 00's retained
#                     27.0 instrumented record 00-plain (the reference = the denominator);
#   00-native-os2701  one NATIVE forward, same input, same environment - comparison (b) against 00-plain-os2701.
# Each comparison is the accepted comparator (`compare`, unchanged) plus the bound-identity checks; both receipts are
# retained. No retry: a failure, an interruption or a refusal after a start STOPS this version (SUPPLEMENT_TERMINAL),
# preserving counters and results; nothing reopens 00-plain / 00-native or changes the 178-id plan and manifest.
SUPP_OUT = T1 / "captures" / "photo_stage_a_supplement"
SUPP_PLAN = HERE / "stage_a_supplement_plan.json"
SUPP_IDENTITY = HERE / "stage_a_supplement_identity.json"
SUPP_IDENTITY_FILES = HERE / "stage_a_supplement_identity_files.json"
SUPP_CRITERIA = HERE / "STAGE_A_SUPPLEMENT_CRITERIA.md"
SUPP_GO = HERE / "ROW20S_GO.json"
SUPP_STAGE = "A-supplement"
SUPP_INPUT = 0
SUPP_REFERENCE = "00-plain"
SUPP_INST, SUPP_NAT = "00-plain-os2701", "00-native-os2701"
SUPP_ATTEMPTS = [
    {"id": SUPP_INST, "phase": "supplement_instrumented", "kind": "supplement_instrumented", "index": SUPP_INPUT,
     "case": "plain", "compare_with": SUPP_REFERENCE},
    {"id": SUPP_NAT, "phase": "supplement_native", "kind": "supplement_native", "index": SUPP_INPUT,
     "case": "native", "compare_with": SUPP_INST}]
SUPP_ENVIRONMENT = {"macos": "27.0.1", "build": "26A434", "machine": "arm64"}
SUPP_COMPARISON_SCHEMA = "stage_a.supplement_comparison.v1"
SUPP_FROZEN = ("stage_a_state.json", "controller.json", "STAGE_A_FINAL.json", "STAGE_A_FINAL.ADMITTED.json",
               "report/ACCEPTANCE.json", "report/REPORT_RECEIPT.json", "INSTRUMENTED_DONE.json", "NATIVE_DONE.json")
SUPP_IDENTITY_BLOBS = {**IDENTITY_BLOBS, "package_file_maps_sha256": "stage_a_supplement_identity_files.json"}
PROCESSOR_CODE = ("image_adapter.py", "dose.py", "dose_report.py")
COMPAT_KEYS = ("macos", "build", "machine", "python", "package_versions", "package_file_maps_sha256",
               "snapshot_sha256", "lens_sha256", "jlens", "dispatch_sha256", "packet_py_sha256",
               "processor_code_sha256")


def supplement_ctx(**kw) -> Ctx:
    base = dict(out=SUPP_OUT, identity_path=SUPP_IDENTITY, criteria_path=SUPP_CRITERIA, go_path=SUPP_GO,
                identity_files=SUPP_IDENTITY_FILES, supp_plan_path=SUPP_PLAN)
    return Ctx(**{**base, **kw})


def _dumps_sha(obj) -> str:
    return sha(json.dumps(obj, sort_keys=True).encode())


def stage_a_pins(o: Path) -> dict:
    """The frozen Stage A tree as the supplement binds it: the files' sha256, the whole tree's bytes, the admitted
    final, the ledger's identity slot and row-20 counters, the controller's row-20 seconds, and input 00's reference
    record with its producer identity and environment (from the recorded transitions)."""
    import stage_a_controller as C
    from enforce import dir_bytes
    for rel in ("stage_a_state.json", "controller.json", "STAGE_A_FINAL.json", "STAGE_A_FINAL.ADMITTED.json",
                "report/ACCEPTANCE.json", "INSTRUMENTED_DONE.json"):
        if not (o / rel).exists():
            raise SystemExit(f"refused: the accepted Stage A tree lacks {rel}")
    fin = C.final_admitted(o)
    if not fin or fin.get("outcome") != "PASS":
        raise SystemExit("refused: the Stage A final record is not an admitted PASS")
    st = json.loads((o / "stage_a_state.json").read_text())
    if st.get("open_attempt") or st.get("interrupted"):
        raise SystemExit("refused: the Stage A ledger holds an open or interrupted attempt")
    ref = st["completed"].get(SUPP_REFERENCE)
    if not ref or (st["attempts"].get(SUPP_REFERENCE) or {}).get("status") != "completed":
        raise SystemExit(f"refused: the reference {SUPP_REFERENCE} is not a completed Stage A attempt")
    return {"files_sha256": {rel: sha_file(o / rel) for rel in SUPP_FROZEN if (o / rel).exists()},
            "tree_bytes": dir_bytes([o]), "final_session": fin["session"], "final_outcome": fin["outcome"],
            "ledger_identity": st["identities"]["row20"], "counters_row20": st["counters"]["row20"],
            "seconds_total": json.loads((o / "controller.json").read_text())["seconds_total"],
            "reference": {"attempt": SUPP_REFERENCE, "outputs": ref["outputs"],
                          "producer_identity": json.loads((o / "INSTRUMENTED_DONE.json").read_text())["identity"],
                          "environment": attempt_environment(o, SUPP_REFERENCE, None)}}


def supplement_envelope(stage: dict) -> dict:
    """Row 20's carried envelope (not row 21's): the two starts and every second, byte and memory sample of the
    supplement charged to row 20."""
    from enforce import CAPS, COUNTER_KEYS, MEMORY_CAP
    c = stage["counters_row20"]
    env = envelope()
    after = c["started"] + len(SUPP_ATTEMPTS)
    if after > CAPS["row20"]["attempts"]:
        raise SystemExit("refused: the supplement's starts exceed row 20's attempt cap")
    return {"row": "20", "attempts": [a["id"] for a in SUPP_ATTEMPTS], "starts_before": c["started"],
            "starts_after": after, "cap_attempts": CAPS["row20"]["attempts"],
            "in_hand_after": CAPS["row20"]["attempts"] - after,
            "in_hand_rule": "not a retry budget: a supplement failure stops this version; no retry, no other input, "
                            "no tolerance revision follows automatically",
            "carry_in": {**{k: c[k] for k in sorted(COUNTER_KEYS)},
                         "basis": "the accepted Stage A ledger's row-20 counters (captures/photo_stage_a/"
                                  "stage_a_state.json, pinned), carried, never reset"},
            "seconds_carry": stage["seconds_total"], "cap_seconds": CAPS["row20"]["seconds"],
            "storage_carry_bytes": stage["tree_bytes"], "cap_bytes": CAPS["row20"]["bytes"],
            "memory_cap": MEMORY_CAP, "controller": env["controller"],
            "rule": "no attempt id outside the supplement plan; one try each; every warm-up, internal or failed "
                    "forward is a start; setup, comparison, receipt and closure time, memory and files are row 20's"}


def make_supplement_plan(ctx: Ctx) -> dict:
    """Desk (no model): input 00 fixed by id and every frozen hash, copied from the 178-id plan unchanged."""
    plan, _ = load_frozen(ctx)
    x = plan["inputs"][SUPP_INPUT]
    if x["index"] != SUPP_INPUT:
        raise SystemExit("refused: plan input 0 is not index 0")
    stage = stage_a_pins(ctx.stage_a_out)
    if ctx.stage_a_out == OUT and {k: stage["counters_row20"][k] for k in ("started", "completed", "failed",
                                                                           "passes")} != \
            {"started": 194, "completed": 193, "failed": 1, "passes": 194}:
        raise SystemExit("refused: the accepted Stage A ledger is not at 194/193/1/194")
    env = supplement_envelope(stage)
    return {"kind": "stage_a_supplement", "revision": 1, "row": "20", "stage": SUPP_STAGE,
            "base_plan_sha256": sha_file(ctx.plan_path), "manifest_sha256": sha_file(ctx.manifest_path),
            "input_id": f"{SUPP_INPUT:02d}", "input": x, "input_sha256": _dumps_sha(x),
            "manifest_record_sha256": plan["manifest_records_sha256"].get(x["concept"]),
            "request_tokens": plan["request_tokens"], "request_token_ids": plan["request_token_ids"],
            "template_sha256": plan["template_sha256"], "capture_layers": LAYERS, "top_k": TOP_K,
            "comparator": {"rel_l2_max": TOL["rel_l2"], "rel_l2": "per recorded layer ||ref - cand|| / ||ref|| over the "
                           "three marker rows x 5,120, FP64; the reference norm finite and non-zero",
                           "logit": "each requested logit |ref - cand| <= max(0.10, one bfloat16 step at the larger "
                                    "magnitude) (logit_tolerance)",
                           "argmax": "identical requested-token argmax", "complete": "finite residuals and requested "
                           "logits, complete records", "bound": "input ids, readout positions, pixels, grid and "
                           "multimodal positions equal the frozen input; (b) the native merged embeddings equal the "
                           "new instrumented merge bitwise and one prefill"},
            "reference": stage["reference"], "attempts": SUPP_ATTEMPTS,
            "comparisons": [{"pair": "a", "reference": SUPP_REFERENCE, "candidate": SUPP_INST,
                             "what": "same path across environments (27.0 record -> 27.0.1)"},
                            {"pair": "b", "reference": SUPP_INST, "candidate": SUPP_NAT,
                             "what": "path fidelity in the current environment (new instrumented -> new native)"}],
            "environment": SUPP_ENVIRONMENT, "stage_a": stage, "envelope": env, "budget_sha256": budget_sha256(env),
            "scope": "one exposed development input; it does not isolate OS causality, re-qualify every image or edit, "
                     "reproduce the 120 shams on the new OS, or admit PILOT; no Stage B forward is approved by it"}


def check_stage_a_frozen(ctx: Ctx, supp: dict) -> None:
    """The accepted Stage A tree is unchanged since the supplement plan pinned it (every supplement worker)."""
    from stage_a_guard import terminal_active
    if terminal_active(ctx.stage_a_out):
        raise SystemExit("refused: Stage A is terminal (its release no longer matches TERMINAL.json)")
    now = stage_a_pins(ctx.stage_a_out)
    bad = sorted(k for k in now if now[k] != supp["stage_a"].get(k))
    if bad:
        raise SystemExit(f"refused: the accepted Stage A tree changed since the supplement plan pinned it: {bad}")


def load_supplement(ctx: Ctx) -> tuple[dict, dict, dict]:
    plan, manifest = load_frozen(ctx)
    supp = json.loads(ctx.supp_plan_path.read_text())
    checks = {"kind/revision": supp.get("kind") == "stage_a_supplement" and supp.get("revision") == 1,
              "base plan": supp.get("base_plan_sha256") == sha_file(ctx.plan_path),
              "manifest": supp.get("manifest_sha256") == sha_file(ctx.manifest_path),
              "input 00": supp.get("input") == plan["inputs"][SUPP_INPUT] and
                          supp.get("input_sha256") == _dumps_sha(plan["inputs"][SUPP_INPUT]),
              "requested tokens": supp.get("request_token_ids") == plan["request_token_ids"] and
                                  supp.get("request_tokens") == plan["request_tokens"],
              "attempts": supp.get("attempts") == SUPP_ATTEMPTS,
              "environment": supp.get("environment") == SUPP_ENVIRONMENT,
              "envelope": supp.get("envelope") == supplement_envelope(supp.get("stage_a") or {"counters_row20": {}})
                          if supp.get("stage_a") else False,
              "budget": supp.get("budget_sha256") == budget_sha256(supp.get("envelope") or {})}
    bad = [k for k, ok in checks.items() if not ok]
    if bad:
        raise SystemExit(f"refused: the supplement plan does not match the frozen plan or the code: {bad}")
    check_stage_a_frozen(ctx, supp)
    return plan, supp, manifest


def supplement_package_hashes(ctx: Ctx) -> dict:
    supp = json.loads(ctx.supp_plan_path.read_text())
    return {"supplement_criteria_sha256": sha_file(ctx.criteria_path),
            "supplement_identity_sha256": sha_file(ctx.identity_path),
            "supplement_plan_sha256": sha_file(ctx.supp_plan_path), "plan_sha256": sha_file(ctx.plan_path),
            "manifest_sha256": sha_file(ctx.manifest_path), "budget_sha256": budget_sha256(supp["envelope"])}


def supplement_package_at_commit(commit: str, repo: Path = RSC_ROOT, photo: str | None = None) -> dict:
    """The supplement's six package hashes as they were at the reviewed commit, with its identity proven to describe
    that commit's blobs (the same checks as package_at_commit, its own import-map file)."""
    photo = photo or str(HERE.relative_to(RSC_ROOT))
    blob = _blob_reader(commit, repo)
    b = {k: blob(f"{photo}/{n}") for k, n in (("criteria", SUPP_CRITERIA.name), ("identity", SUPP_IDENTITY.name),
                                               ("supp", SUPP_PLAN.name), ("plan", "stage_a_plan.json"),
                                               ("manifest", "manifest_dev.json"))}
    _identity_describes_commit(json.loads(b["identity"]), blob, photo, SUPP_IDENTITY_BLOBS)
    return {"supplement_criteria_sha256": sha(b["criteria"]), "supplement_identity_sha256": sha(b["identity"]),
            "supplement_plan_sha256": sha(b["supp"]), "plan_sha256": sha(b["plan"]),
            "manifest_sha256": sha(b["manifest"]), "budget_sha256": budget_sha256(json.loads(b["supp"])["envelope"])}


def _supp_terminal(ctx: Ctx, phase: str, exc: BaseException) -> None:
    import stage_a_controller as C
    C.supplement_set_terminal(ctx.out, phase, f"{type(exc).__name__}: {exc}")


def run_supplement_gates(ctx: Ctx | None = None) -> int:
    """The supplement's GATES worker: its terminal record absent; the 178-id plan, manifest and source pins; the
    supplement plan against them, the code and the frozen Stage A tree; the positions receipt; the go (row 20, stage
    A-supplement) bound to this exact package re-derived at the reviewed commit; a fresh execution identity equal to
    the frozen supplement identity; the DECLARED environment (macOS product version AND build, machine) - a product
    version string alone is not accepted; the gates' own import map; then the supplement ledger's crash
    reconciliation - an interrupted try STOPS the supplement (no recovery path); the identity rechecked before
    SUPPLEMENT_GATES.json is committed."""
    import stage_a_controller as C
    from enforce import reconcile_open_attempt, write_json_atomic
    from stage_a_guard import check_imported_origins, execution_identity, require_go
    ctx = ctx or supplement_ctx()
    _worker_storage(ctx)
    session = os.environ.get("STAGE_A_SESSION", "test")
    if C.supplement_terminal_active(ctx.out):
        raise SystemExit("refused: the supplement stopped terminally; this version never runs again")
    plan, supp, _ = load_supplement(ctx)
    check_receipt(ctx)
    pkg = supplement_package_hashes(ctx)
    (ctx.check_go or (lambda c: require_go(c.go_path, pkg, row="20", stage=SUPP_STAGE,
                                           verify_at_commit=supplement_package_at_commit)))(ctx)
    frozen = json.loads(ctx.identity_path.read_text())
    ctx.out.mkdir(parents=True, exist_ok=True)
    tmp = ctx.out / "identity_files.supplement_gates.json"
    now = (ctx.compute_identity or (lambda: execution_identity(ctx.plan_path, ctx.manifest_path, ctx.receipt_path,
                                                               tmp)))()
    if now["identity_sha256"] != frozen["identity_sha256"]:
        raise SystemExit(f"refused: execution identity now {now['identity_sha256']} differs from the frozen "
                         f"supplement identity {frozen['identity_sha256']}")
    build = (ctx.os_build_fn or os_build)()
    envd = {"macos": now.get("macos"), "build": build, "machine": now.get("machine")}
    if envd != supp["environment"]:
        raise SystemExit(f"refused: the execution environment {envd} is not the declared {supp['environment']}")
    (ctx.origins_check or (lambda: check_imported_origins(tmp, now["package_file_maps_sha256"])))()
    st = ctx.out / "stage_a_state.json"
    reconciled = reconcile_open_attempt(st)
    if st.exists() and json.loads(st.read_text())["interrupted"]:
        C.supplement_set_terminal(ctx.out, "supplement_gates", "an interrupted supplement try: this version stops "
                                  "(no recovery, no retry); counters and results preserved")
        raise SystemExit("refused: an interrupted supplement try - the supplement stopped terminally")
    recheck_identity(ctx, now)
    if sha_file(ctx.supp_plan_path) != pkg["supplement_plan_sha256"]:
        raise StopCheck("the supplement plan changed during the gates")
    write_json_atomic(ctx.out / C.SUPPLEMENT_NAMES["gates"],
                      {"package": pkg, "identity": now["identity_sha256"], "environment": envd,
                       "reconciled": reconciled, "session": session, "passed": True, "hold": False}, final=True)
    return 0


def supplement_open(ctx: Ctx, phase: str):
    """A supplement WORK worker's start: under the controller holding the lock; its storage; no supplement terminal;
    Stage A's own gate (released); the frozen plans, code and Stage A tree; the supplement ledger, created with Stage
    A's row-20 counters as its carry (so the two starts are 195 and 196 of 200) and refusing any foreign id or an
    interrupted try (which stops the version)."""
    import stage_a_controller as C
    from enforce import Budget
    from stage_a_guard import check_terminal
    _check_controller(ctx)
    _worker_storage(ctx)
    if C.supplement_terminal_active(ctx.out):
        raise SystemExit("refused: the supplement stopped terminally; this version never runs again")
    check_terminal(ctx.stage_a_out)
    plan, supp, manifest = load_supplement(ctx)
    ident = json.loads(ctx.identity_path.read_text())["identity_sha256"]
    carry = supp["envelope"]["carry_in"]
    budget = Budget(ctx.out / "stage_a_state.json", "row20", ident, [ctx.out],
                    os.environ.get("STAGE_A_SESSION", "test"), carry_in=carry,
                    storage_limit=int(os.environ.get("STAGE_A_STORAGE_LIMIT", 0)) or None, **ctx.budget_kwargs)
    if budget.state["carry_in"].get("row20") != carry:
        raise SystemExit("refused: the supplement ledger's carry is not the pinned Stage A row-20 counters")
    foreign = sorted(set(budget.state["attempts"]) - {a["id"] for a in SUPP_ATTEMPTS})
    if foreign:
        raise SystemExit(f"refused: the supplement ledger holds ids outside the supplement plan: {foreign}")
    if budget.state["interrupted"]:
        raise StopCheck(f"{phase}: an interrupted supplement try {budget.state['interrupted']} - the supplement stops "
                        f"(no recovery, no retry)")
    return budget, plan, supp, manifest


def _supp_recheck(ctx: Ctx, ident: dict, supp_sha: str) -> None:
    recheck_identity(ctx, ident)
    if sha_file(ctx.supp_plan_path) != supp_sha:
        raise StopCheck("the supplement plan changed during the phase")


def _validate_record(rec: dict, arrays: dict, a: dict, x: dict, plan: dict, plain: dict | None = None) -> None:
    """The phase's full independent predicates (stage_a_report._inst / _nat, unchanged) on a supplement or reference
    record; the supplement records carry Stage A's own record schemas."""
    import stage_a_report as R
    v = R.V()
    v.need((rec.get("id"), rec.get("index"), rec.get("case"), rec.get("kind")) ==
           (a["id"], a["index"], a["case"], a["kind"]), "RECORD_ID", a["id"])
    suffix = {s["base_index"]: s for s in plan["diagnostics"]["suffix_isolation"]}
    if a["case"] == "native":
        R._nat(rec, arrays, x, plan, plain, D_MODEL, v, a["id"])
    else:
        R._inst(rec, arrays, a, x, plan, suffix, D_MODEL, v, a["id"])
    if v.failures:
        raise StopCheck(f"{a['id']}: record fails admission: {[f['code'] for f in v.failures][:6]}")


def admit_reference(ctx: Ctx, plan: dict, supp: dict) -> tuple[dict, np.ndarray]:
    """Input 00's retained 27.0 instrumented record, read from the frozen Stage A tree: its outputs equal the pinned
    ones and the ledger's, every checksum holds, and it passes the instrumented predicates."""
    st = json.loads((ctx.stage_a_out / "stage_a_state.json").read_text())
    outs = (st["completed"].get(SUPP_REFERENCE) or {}).get("outputs")
    if outs is None or outs != supp["reference"]["outputs"]:
        raise StopCheck(f"{SUPP_REFERENCE}: the reference outputs differ from the supplement plan's pins")
    rec, arrays = load_outputs(ctx.stage_a_out, SUPP_REFERENCE, outs)
    a = next(a for a in plan["attempts"] if a["id"] == SUPP_REFERENCE)
    _validate_record(rec, arrays, a, plan["inputs"][SUPP_INPUT], plan)
    return rec, arrays["residuals"]


def _bound_checks(x: dict, *recs: dict) -> dict:
    exp = x["expected"]
    out = {}
    for r in recs:
        img, tag = r["image"], r["id"]
        out.update({f"{tag}: input ids": r["input_ids_sha256"] == exp["ids_sha256"],
                    f"{tag}: readout positions": r["readout_positions"] == exp["marker_positions"],
                    f"{tag}: pixels": img["pixel_values_sha256"] == x["pixel_values_sha256"],
                    f"{tag}: grid": img["grid_thw"] == x["grid_thw"],
                    f"{tag}: positions": img["positions_sha256"] == exp["positions_sha256"] ==
                                         img["effective_positions_sha256"]})
    return out


def compare_pair(pair: str, ref: dict, ref_u16: np.ndarray, cand: dict, cand_f32: np.ndarray, li: np.ndarray,
                 ln: np.ndarray, bound: dict, diagnostic: dict) -> dict:
    """One direct comparison receipt: the accepted comparator (`compare`, unchanged: reference = denominator) plus the
    bound-identity checks. PASS needs both."""
    row = compare(ref_u16, cand_f32, li, ln)
    comp_pass = row.pop("pass")
    bad = [k for k, ok in bound.items() if not ok]
    return {"record_schema": SUPP_COMPARISON_SCHEMA, "pair": pair, "reference": ref["id"], "candidate": cand["id"],
            "input_id": f"{SUPP_INPUT:02d}", **row, "comparator_pass": comp_pass, "bound": bound,
            "bound_failures": bad, "diagnostic": diagnostic, "pass": bool(comp_pass and not bad)}


def comparison_a(ref: dict, ref_u16: np.ndarray, rec: dict, rec_u16: np.ndarray, x: dict, supp: dict) -> dict:
    """Comparison (a), built the same way by the worker and by row 21's verifier (revision 2: the verifier re-derives
    the COMPLETE receipt)."""
    li = np.array([q["logit"] for q in ref["requested"]], dtype=np.float64)
    ln = np.array([q["logit"] for q in rec["requested"]], dtype=np.float64)
    diag = {"residuals_bitwise_equal": rec["residuals_sha256"] == ref["residuals_sha256"],
            "logits_bitwise_equal": rec["logits_sha256"] == ref["logits_sha256"],
            "features_bitwise_equal": rec["image"]["features_sha256"] == ref["image"]["features_sha256"],
            "merge_bitwise_equal": rec["image"]["merge"]["merged_sha256"] == ref["image"]["merge"]["merged_sha256"],
            "reference_environment": supp["reference"]["environment"], "candidate_environment": supp["environment"]}
    return compare_pair("a", ref, ref_u16, rec, bf16_to_f32(rec_u16), li, ln, _bound_checks(x, ref, rec), diag)


def comparison_b(inst: dict, inst_u16: np.ndarray, rec: dict, rec_f32: np.ndarray, x: dict, supp: dict) -> dict:
    """Comparison (b), built the same way by the worker and by row 21's verifier."""
    li = np.array([q["logit"] for q in inst["requested"]], dtype=np.float64)
    ln = np.asarray(rec["requested_logits"], dtype=np.float64)
    merged = inst["image"]["merge"]["merged_sha256"]
    bound = {**_bound_checks(x, inst),
             f"{rec['id']}: positions": rec["effective_positions_sha256"] == x["expected"]["positions_sha256"],
             f"{rec['id']}: one prefill": rec["decoder_calls"] == {"min": 1, "max": 1, "layers": N_LAYERS},
             f"{rec['id']}: merged embeddings == {inst['id']} merge": rec["inputs_embeds_sha256"] == merged}
    return compare_pair("b", inst, inst_u16, rec, rec_f32, li, ln, bound, {"environment": supp["environment"]})


def _write_comparison(ctx: Ctx, row: dict) -> dict:
    from enforce import write_json_atomic
    rel = f"supplement/comparison_{row['pair']}.json"
    (ctx.out / "supplement").mkdir(parents=True, exist_ok=True)
    write_json_atomic(ctx.out / rel, row, final=True)
    return {"path": rel, "sha256": sha_file(ctx.out / rel)}


def run_supplement_instrumented(ctx: Ctx | None = None) -> dict:
    ctx = ctx or supplement_ctx()
    from enforce import write_json_atomic
    budget, plan, supp, manifest = supplement_open(ctx, "supplement_instrumented")
    try:
        supp_sha = sha_file(ctx.supp_plan_path)
        ident, files = worker_identity(ctx, "supplement_instrumented")
        ref, ref_res = admit_reference(ctx, plan, supp)
        inst = (ctx.instrument_factory or default_instrument)()
        expect = (ctx.post_load or post_load_instrumented)(inst)
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(
            files, ident["package_file_maps_sha256"])))()
        check_tokenizer(plan, inst.tok)
        x = plan["inputs"][SUPP_INPUT]
        px, seq = admit_input(ctx, x, manifest, inst.processor.image_processor, inst.processor, inst.tok)
        a = SUPP_ATTEMPTS[0]
        _never_resumed(budget, a)                                     # revision 2: no post-start resumption
        with budget.attempt(a["id"], a["kind"], passes=1) as att:
            r = inst.capture(seq, px["pv"], capture_layers=LAYERS, request_token_ids=plan["request_token_ids"],
                             top_k=TOP_K, edits=edits_for(inst.ce, "plain", x, seq, None))
            validate_pass(r, x, seq, "plain", plan, expect)
            res = residual_array(r)
            if sha(res.tobytes()) != r["residuals"]["sha256"]:
                raise StopCheck(f"{a['id']}: residual bytes differ from the capture's own hash")
            rec = {k: r[k] for k in INST_CAPTURE_KEYS}
            rec.update(record_schema=INST_SCHEMA, id=a["id"], case="plain", index=x["index"], kind=a["kind"],
                       residuals_meta={k: r["residuals"][k] for k in ("dtype", "shape", "sha256")},
                       final_logits={k: r["final_logits"][k] for k in ("dtype", "n", "sha256")},
                       residuals_sha256=r["residuals"]["sha256"], logits_sha256=r["final_logits"]["sha256"])
            outs = save_outputs(budget, ctx.out, a["id"], {"residuals": res}, rec)
            rec, arrays = load_outputs(ctx.out, a["id"], outs)      # validated from disk before the commit
            _validate_record(rec, arrays, a, x, plan)
            att.commit(outs)
        _validate_record(rec, arrays, a, x, plan)
        if rec["final_logits"]["n"] != expect["vocab_rows"]:
            raise StopCheck(f"{a['id']}: logits length differs from the loaded vocabulary")
        row = comparison_a(ref, ref_res, rec, arrays["residuals"], x, supp)
        written = _write_comparison(ctx, row)
        if not row["pass"]:
            raise StopCheck(f"{a['id']}: comparison (a) with {SUPP_REFERENCE} failed: " + (
                parity_failure(a["id"], row) if not row["comparator_pass"] else f"bound {row['bound_failures']}"))
        _supp_recheck(ctx, ident, supp_sha)
        budget.final_size()
        write_json_atomic(ctx.out / "SUPPLEMENT_INSTRUMENTED_DONE.json",
                          {"phase": "supplement_instrumented", "attempts": {a["id"]: budget.completed(a["id"])},
                           "comparison": written, "identity": budget.identity}, final=True)
        return {"supplement_instrumented": a["id"], "comparison_a": row["pass"],
                "counters": budget.state["counters"]["row20"]}
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            _supp_terminal(ctx, "supplement_instrumented", exc)
        raise


def _never_resumed(budget, a: dict) -> None:
    """Revision 2 (Codex 478196f P1): an endpoint already started - in any status, in any session - is never reloaded,
    replayed or continued: the supplement is one session from its first start (the controller's restart rule makes
    the same decision before any worker is spawned; this is the worker's own refusal)."""
    if a["id"] in budget.state["attempts"]:
        raise StopCheck(f"{a['id']} was already started ({budget.state['attempts'][a['id']]['status']}): the supplement "
                        f"never resumes after a start; this version stops")


def admit_supplement_instrumented(ctx: Ctx, plan: dict, budget) -> tuple[dict, dict]:
    """Before any native model: the supplement instrumented phase complete - its record committed in the ledger and
    equal to the phase record, comparison (a) retained and passing, the record passing the instrumented predicates."""
    p = ctx.out / "SUPPLEMENT_INSTRUMENTED_DONE.json"
    if not p.exists():
        raise SystemExit("refused: the supplement instrumented phase has not completed")
    done = json.loads(p.read_text())
    a = SUPP_ATTEMPTS[0]
    outs = budget.completed(a["id"])
    if outs is None or done.get("attempts") != {a["id"]: outs} or done.get("identity") != budget.identity:
        raise StopCheck("SUPPLEMENT_INSTRUMENTED_DONE.json does not match the supplement ledger or identity")
    if budget.state["completed"][a["id"]].get("session") != budget.session:     # revision 2: the same session only
        raise StopCheck(f"{a['id']} was committed in another session: native is never dispatched after an interruption")
    cp = ctx.out / done["comparison"]["path"]
    if not cp.exists() or sha_file(cp) != done["comparison"]["sha256"] or json.loads(cp.read_text()).get("pass") \
            is not True:
        raise StopCheck("comparison (a) is missing, changed or not passing")
    rec, arrays = load_outputs(ctx.out, a["id"], outs)
    _validate_record(rec, arrays, a, plan["inputs"][SUPP_INPUT], plan)
    return rec, arrays


def run_supplement_native(ctx: Ctx | None = None) -> dict:
    ctx = ctx or supplement_ctx()
    from enforce import write_json_atomic
    budget, plan, supp, manifest = supplement_open(ctx, "supplement_native")
    try:
        supp_sha = sha_file(ctx.supp_plan_path)
        ident, files = worker_identity(ctx, "supplement_native")
        inst, inst_arr = admit_supplement_instrumented(ctx, plan, budget)
        vmodel, processor, tok, forward = (ctx.native_factory or default_native)()
        if any(m == "jlens_qwen" or m.startswith("jlens_qwen.") for m in sys.modules):
            raise StopCheck("jlens_qwen is imported in the native process: the dispatch is not mlx-vlm's own")
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(
            files, ident["package_file_maps_sha256"])))()
        check_tokenizer(plan, tok)
        x = plan["inputs"][SUPP_INPUT]
        px, seq = admit_input(ctx, x, manifest, processor.image_processor, processor, tok)
        a = SUPP_ATTEMPTS[1]
        merged = inst["image"]["merge"]["merged_sha256"]
        req = plan["request_token_ids"]
        _never_resumed(budget, a)                                     # revision 2: no post-start resumption
        with budget.attempt(a["id"], a["kind"], passes=1) as att:
            nat = forward(vmodel, seq, px["pv"], LAYERS, seq["marker_positions"])
            res, logits = np.asarray(nat["residuals"], dtype=np.float32), np.asarray(nat["logits"])
            checks = {"shape": res.shape == (N_LAYERS, N_MARKER, D_MODEL),
                      "residuals finite": bool(np.all(np.isfinite(res))),
                      "logits finite": bool(np.all(np.isfinite(logits))),
                      "logits length == the instrumented vocabulary": int(logits.size) == inst["final_logits"]["n"],
                      "one prefill": nat["decoder_calls"] == {"min": 1, "max": 1, "layers": N_LAYERS},
                      "positions": nat["effective_positions_sha256"] == x["expected"]["positions_sha256"],
                      "merged embeddings == the new instrumented merge (bitwise)":
                          nat["inputs_embeds_sha256"] == merged}
            bad = [k for k, ok in checks.items() if not ok]
            if bad:
                raise StopCheck(f"{a['id']}: native checks failed: {bad}")
            rec = {"record_schema": NAT_SCHEMA, "id": a["id"], "index": x["index"], "case": "native",
                   "kind": a["kind"], "inputs_embeds_dtype": nat.get("inputs_embeds_dtype"),
                   "requested_logits": logits[req].astype(np.float64).tolist(),
                   "logits_sha256": sha(np.ascontiguousarray(logits).tobytes()), "logits_n": int(logits.size),
                   "residuals_sha256": sha(np.ascontiguousarray(res).tobytes()),
                   "decoder_calls": nat["decoder_calls"],
                   "effective_positions_sha256": nat["effective_positions_sha256"],
                   "inputs_embeds_sha256": nat["inputs_embeds_sha256"],
                   "inputs_embeds_equal_instrumented_merge": nat["inputs_embeds_sha256"] == merged}
            outs = save_outputs(budget, ctx.out, a["id"], {"residuals": res}, rec)
            rec, arrays = load_outputs(ctx.out, a["id"], outs)
            _validate_record(rec, arrays, a, x, plan, plain=inst)
            att.commit(outs)
        _validate_record(rec, arrays, a, x, plan, plain=inst)
        if rec["logits_n"] != inst["final_logits"]["n"]:
            raise StopCheck(f"{a['id']}: native logits length differs from the instrumented vocabulary")
        row = comparison_b(inst, inst_arr["residuals"], rec, arrays["residuals"], x, supp)
        written = _write_comparison(ctx, row)
        if not row["pass"]:
            raise StopCheck(f"{a['id']}: comparison (b) with {inst['id']} failed: " + (
                parity_failure(a["id"], row) if not row["comparator_pass"] else f"bound {row['bound_failures']}"))
        _supp_recheck(ctx, ident, supp_sha)
        budget.final_size()
        write_json_atomic(ctx.out / "SUPPLEMENT_NATIVE_DONE.json",
                          {"phase": "supplement_native", "attempts": {a["id"]: budget.completed(a["id"])},
                           "comparison": written, "identity": budget.identity}, final=True)
        return {"supplement_native": a["id"], "comparison_b": row["pass"],
                "counters": budget.state["counters"]["row20"]}
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            _supp_terminal(ctx, "supplement_native", exc)
        raise


def supplement_compatibility(ident: dict, build: str | None) -> dict:
    """What a later package (row 21) must share with the supplement's execution for its PASS to carry: the OS product
    version AND build, machine, Python, every watched package's version and per-file map, the snapshot files, the
    lens, the jlens tree, the declared dispatch, the packet and the processor code. Not a product-version string."""
    return {"identity_sha256": ident["identity_sha256"], "macos": ident["macos"], "build": build,
            "machine": ident["machine"], "python": ident["python"], "package_versions": ident["package_versions"],
            "package_file_maps_sha256": ident["package_file_maps_sha256"],
            "snapshot_sha256": _dumps_sha(ident["snapshot"]), "lens_sha256": ident["lens"]["sha256"],
            "jlens": ident["jlens"], "dispatch_sha256": _dumps_sha(ident["dispatch"]),
            "packet_py_sha256": ident["packet_py_sha256"],
            "processor_code_sha256": {n: ident["local_code_sha256"][n] for n in PROCESSOR_CODE}}


def _supp_expected_counters(supp: dict) -> dict:
    c = supp["envelope"]["carry_in"]
    n = len(SUPP_ATTEMPTS)
    return {"started": c["started"] + n, "completed": c["completed"] + n, "failed": c["failed"],
            "passes": c["passes"] + n}


def run_supplement_receipt(ctx: Ctx | None = None) -> dict:
    """The supplement's RECEIPT worker: always runs after the gates passed (also after a stop), inside the report
    reserve. Reads its ledger without converting, granting or consuming anything; recomputes the identity and checks
    its own import map; admissible only with this session's passed gates and an equal identity. outcome PASS needs:
    admissible; no supplement terminal record; the supplement plan and the frozen Stage A tree unchanged; both ids
    completed in one try each, no open or interrupted try, the ledger legal and its row-20 counters exactly 196/195/1/
    196 (= the carry + 2); both phase records present and equal to the ledger; both comparison receipts retained,
    unchanged and passing. The receipt binds every output by sha256 and is written LAST."""
    import stage_a_controller as C
    from enforce import check_ledger, read_ledger, write_json_atomic
    ctx = ctx or supplement_ctx()
    _check_controller(ctx)
    _worker_storage(ctx)
    gates = json.loads(os.environ.get("STAGE_A_GATES") or "{}")
    session = os.environ.get("STAGE_A_SESSION", "test")
    reasons, supp, ident, ident_ok = [], None, None, False
    try:
        _, supp, _ = load_supplement(ctx)
    except SystemExit as exc:
        reasons.append(str(exc))
        supp = json.loads(ctx.supp_plan_path.read_text())
    try:
        ident, files = worker_identity(ctx, "supplement_receipt")
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(
            files, ident["package_file_maps_sha256"])))()
        ident_ok = True
    except SystemExit as exc:
        reasons.append(f"identity: {exc}")
    admissible = bool(gates.get("passed") is True and gates.get("session") == session and ident_ok)
    if not admissible:
        reasons.append("not admissible (this session's gates and an equal identity are both required)")
    if C.supplement_terminal_active(ctx.out):
        t = json.loads((ctx.out / C.SUPPLEMENT_TERMINAL).read_text())
        reasons.append(f"terminal: {t['first']['phase']}: {t['first']['reason']}")
    st = read_ledger(ctx.out / "stage_a_state.json")["state"] or {}
    outputs, attempts = {}, {}
    for a in SUPP_ATTEMPTS:
        e, c = (st.get("attempts") or {}).get(a["id"]), (st.get("completed") or {}).get(a["id"])
        attempts[a["id"]] = {"status": (e or {}).get("status"), "tries": (e or {}).get("tries"),
                             "outputs": (c or {}).get("outputs")}
        if not (e and e.get("status") == "completed" and e.get("tries") == 1 and c):
            reasons.append(f"{a['id']}: not completed in exactly one try")
        for rel, h in ((c or {}).get("outputs") or {}).items():
            if not (ctx.out / rel).exists() or sha_file(ctx.out / rel) != h:
                reasons.append(f"{a['id']}: output {rel} missing or changed")
            outputs[rel] = h
    counters = (st.get("counters") or {}).get("row20")
    if st:
        probs = check_ledger(st, witness_dir=ctx.out)
        if probs:
            reasons.append(f"ledger: {probs[:3]}")
        if st.get("open_attempt") or st.get("interrupted"):
            reasons.append("an open or interrupted supplement try")
        if counters != _supp_expected_counters(supp):
            reasons.append(f"row-20 counters {counters} are not {_supp_expected_counters(supp)}")
    else:
        reasons.append("no supplement ledger")
    comparisons = {}
    for pair, done_name, a in (("a", "SUPPLEMENT_INSTRUMENTED_DONE.json", SUPP_ATTEMPTS[0]),
                               ("b", "SUPPLEMENT_NATIVE_DONE.json", SUPP_ATTEMPTS[1])):
        dp, cp = ctx.out / done_name, ctx.out / f"supplement/comparison_{pair}.json"
        row = json.loads(cp.read_text()) if cp.exists() else None
        if row is not None:
            outputs[f"supplement/comparison_{pair}.json"] = sha_file(cp)
            comparisons[pair] = {k: row.get(k) for k in ("reference", "candidate", "rel_l2_max", "rel_l2_argmax_layer",
                                                         "logit_max_abs", "logit_worst_abs", "logit_worst_tolerance",
                                                         "logit_within_tolerance", "argmax_equal", "comparator_pass",
                                                         "bound_failures", "pass")}
        if not (row and row.get("pass") is True and row.get("reference") == a["compare_with"] and
                row.get("candidate") == a["id"]):
            reasons.append(f"comparison ({pair}) absent or not passing")
        if dp.exists():
            outputs[done_name] = sha_file(dp)
            d = json.loads(dp.read_text())
            if d.get("attempts") != {a["id"]: attempts[a["id"]]["outputs"]} or \
                    (row is not None and d.get("comparison", {}).get("sha256") != outputs.get(
                        f"supplement/comparison_{pair}.json")):
                reasons.append(f"{done_name} differs from the ledger or its comparison")
        else:
            reasons.append(f"{done_name} absent")
    for rel in ("stage_a_state.json", C.SUPPLEMENT_NAMES["gates"], C.SUPPLEMENT_TERMINAL):
        if (ctx.out / rel).exists():
            outputs[rel] = sha_file(ctx.out / rel)
    x = supp["input"]
    rc = {"session": session, "package": gates.get("package"), "identity": gates.get("identity"),
          "date": time.strftime("%Y-%m-%d"), "outcome": "PASS" if not reasons else "STOPPED",
          "admissible": admissible, "reasons": reasons,
          "input": {"id": supp["input_id"], "input_sha256": supp["input_sha256"], "original_sha256":
                    x["original_sha256"], "png_sha256": x["png_sha256"], "pixel_values_sha256":
                    x["pixel_values_sha256"], "grid_thw": x["grid_thw"], "carrier": x["carrier"], "level": x["level"],
                    "ids_sha256": x["expected"]["ids_sha256"], "positions_sha256": x["expected"]["positions_sha256"],
                    "request_token_ids_sha256": _dumps_sha(supp["request_token_ids"]),
                    "template_sha256": supp["template_sha256"]},
          "attempts": attempts, "comparisons": comparisons, "counters": counters,
          "compatibility": supplement_compatibility(json.loads(ctx.identity_path.read_text()),
                                                    (ctx.os_build_fn or os_build)()),
          "outputs": outputs}
    if ident_ok:
        _supp_recheck(ctx, ident, sha_file(ctx.supp_plan_path))      # before the receipt (A1)
    (ctx.out / "supplement").mkdir(parents=True, exist_ok=True)
    write_json_atomic(ctx.out / C.SUPPLEMENT_NAMES["receipt"], rc, final=True)
    return {"outcome": rc["outcome"], "admissible": admissible, "reasons": reasons}


def supplement_receipt_ok(current_identity: dict, *, out: Path = SUPP_OUT, supp_plan_path: Path = SUPP_PLAN,
                          plan_path: Path = PLAN, stage_a_out: Path = OUT, build: str | None = None) -> dict:
    """ROW 21'S VERIFIER, before its FIRST CAL forward (Codex b0db0f9): ok only if the supplement's final record is an
    ADMITTED PASS (marker present, no abort), no supplement terminal record, the receipt is the one the final binds,
    names its session, says PASS and admissible and binds outputs that are all on disk unchanged; both comparisons
    RE-DERIVED here from the retained arrays and records (the reference from the frozen Stage A tree) pass the
    accepted comparator and agree with the retained receipts; the ledger holds exactly the two ids in one try each,
    no open or interrupted try, counters carry + 2; the input is exactly input 00 of the 178-id plan; and the CURRENT
    execution (current_identity, the OS build now) is compatible on every COMPAT_KEYS field - runtime, processor and
    code, not a product-version string. Anything else holds (ok False, the reasons listed)."""
    import stage_a_controller as C
    from enforce import check_ledger
    why: list[str] = []
    res = {"ok": False, "hold": True, "why": why}
    fin = C.final_admitted(out, C.SUPPLEMENT_NAMES)
    if fin is None:
        why.append("no admitted supplement final record (absent, unadmitted, aborted or interrupted)")
        return res
    if fin.get("outcome") != "PASS":
        why.append(f"the supplement final record is {fin.get('outcome')}")
    if C.supplement_terminal_active(out):
        why.append("the supplement stopped terminally")
    rp = out / C.SUPPLEMENT_NAMES["receipt"]
    if not rp.exists():
        why.append("no supplement receipt")
        return res
    rc = json.loads(rp.read_text())
    if sha_file(rp) != fin.get("receipt_sha256") or rc.get("session") != fin.get("session"):
        why.append("the receipt is not the one the admitted final binds")
    if set(rc) != C.SUPPLEMENT_RECEIPT_KEYS or rc.get("outcome") != "PASS" or rc.get("admissible") is not True:
        why.append("the receipt is not an admissible PASS with the exact schema")
    for rel, h in (rc.get("outputs") or {}).items():
        if not (out / rel).exists() or sha_file(out / rel) != h:
            why.append(f"bound output {rel} missing or changed")
    try:
        supp = json.loads(supp_plan_path.read_text())
        plan = json.loads(plan_path.read_text())
        x = plan["inputs"][SUPP_INPUT]
        if supp.get("input") != x or supp.get("input_sha256") != _dumps_sha(x) or \
                (rc.get("input") or {}).get("input_sha256") != supp["input_sha256"] or \
                supp.get("base_plan_sha256") != sha_file(plan_path):
            why.append("the input is not exactly input 00 of the 178-id plan")
        if (rc.get("package") or {}).get("supplement_plan_sha256") != sha_file(supp_plan_path):
            why.append("the receipt's package does not bind this supplement plan")
        st = json.loads((out / "stage_a_state.json").read_text())
        ids = {a["id"] for a in SUPP_ATTEMPTS}
        if set(st["attempts"]) != ids or any(st["attempts"][i] != {"kind": next(a["kind"] for a in SUPP_ATTEMPTS
                                                                                if a["id"] == i), "passes": 1,
                                                                   "status": "completed", "tries": 1} for i in ids) \
                or st.get("open_attempt") or st.get("interrupted") or check_ledger(st, witness_dir=out) or \
                st["counters"]["row20"] != _supp_expected_counters(supp):
            why.append("the supplement ledger is not exactly two completed single tries at carry + 2")
        rref = json.loads((stage_a_out / "stage_a_state.json").read_text())["completed"][SUPP_REFERENCE]["outputs"]
        if rref != supp["reference"]["outputs"]:
            why.append("the Stage A reference outputs differ from the supplement plan's pins")
        ref, ra = load_outputs(stage_a_out, SUPP_REFERENCE, rref)
        inst, ia = load_outputs(out, SUPP_INST, st["completed"][SUPP_INST]["outputs"])
        nat, na = load_outputs(out, SUPP_NAT, st["completed"][SUPP_NAT]["outputs"])
        check_stage_a_frozen(Ctx(stage_a_out=stage_a_out, plan_path=plan_path), supp)   # the parent tree (rev 2)
        a_ref = next(a for a in plan["attempts"] if a["id"] == SUPP_REFERENCE)
        _validate_record(ref, ra, a_ref, x, plan)                   # revision 2: every record's full predicates
        _validate_record(inst, ia, SUPP_ATTEMPTS[0], x, plan)
        _validate_record(nat, na, SUPP_ATTEMPTS[1], x, plan, plain=inst)
        for pair, row in (("a", comparison_a(ref, ra["residuals"], inst, ia["residuals"], x, supp)),
                          ("b", comparison_b(inst, ia["residuals"], nat, na["residuals"], x, supp))):
            kept = json.loads((out / f"supplement/comparison_{pair}.json").read_text())
            if not row["pass"] or json.loads(json.dumps(row)) != kept:      # the COMPLETE receipt (revision 2)
                why.append(f"comparison ({pair}) does not re-derive to a PASS equal to its complete retained receipt")
        if nat["inputs_embeds_sha256"] != inst["image"]["merge"]["merged_sha256"]:
            why.append("the native merged embeddings differ from the new instrumented merge")
    except (OSError, KeyError, ValueError, TypeError, StopCheck, SystemExit) as exc:
        why.append(f"the supplement records cannot be re-derived: {type(exc).__name__}: {exc}")
    try:
        cur = supplement_compatibility(current_identity, build if build is not None else os_build())
        kept = rc.get("compatibility") or {}
        diff = [k for k in COMPAT_KEYS if cur.get(k) != kept.get(k) or kept.get(k) is None]
        if diff:
            why.append(f"the current execution is not compatible with the supplement's: {diff}")
    except (KeyError, TypeError) as exc:
        why.append(f"the current identity lacks a compatibility field: {exc}")
    res.update(ok=not why, hold=bool(why), final_sha256=sha_file(out / C.SUPPLEMENT_NAMES["final"]),
               receipt_sha256=sha_file(rp))
    return res


# ================================================================================================================
def main() -> int:
    from enforce import write_json_atomic
    cmd = sys.argv[1] if len(sys.argv) > 1 else "package"
    if cmd == "plan":
        p = make_plan()
        eq = verify_positions_rule(p)
        if not all(eq.values()):
            raise SystemExit(f"refused: the declared positions rule differs from mlx-vlm's get_rope_index: {eq}")
        PLAN.write_text(json.dumps(p, indent=1) + "\n")
        write_json_atomic(RECEIPT, {"all_equal": True, "by_carrier": eq, "plan_sha256": sha_file(PLAN),
                                    "method": "mlx-vlm 0.6.3 LanguageModel.get_rope_index on lazily opened weights, "
                                              "index arithmetic only, compared with expected_positions"})
        print("positions rule equals mlx-vlm get_rope_index:", eq)
        kinds = {k: sum(x["kind"] == k for x in p["inputs"]) for k in ("clean", "intermediate", "noise_only")}
        print(kinds, "carriers", [sum(x["carrier"] == c for x in p["inputs"]) for c in (0, 1)],
              "attempts", len(p["attempts"]), "+ carried", ENGINEERING_CARRY["passes"])
        return 0
    if cmd == "identity":
        from stage_a_guard import execution_identity
        ident = execution_identity(PLAN, MANIFEST, RECEIPT, IDENTITY_FILES)
        IDENTITY.write_text(json.dumps(ident, indent=1, sort_keys=True) + "\n")
        print(ident["identity_sha256"])
        return 0
    if cmd == "package":
        print(json.dumps(package_hashes(Ctx()), indent=1))
        return 0
    if cmd == "supplement-plan":                         # revision 16, desk: no model forward
        p = make_supplement_plan(supplement_ctx())
        SUPP_PLAN.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")
        print(SUPP_PLAN.name, sha_file(SUPP_PLAN))
        return 0
    if cmd == "supplement-identity":                     # desk: no model load
        from stage_a_guard import execution_identity
        ident = execution_identity(PLAN, MANIFEST, RECEIPT, SUPP_IDENTITY_FILES)
        SUPP_IDENTITY.write_text(json.dumps(ident, indent=1, sort_keys=True) + "\n")
        print(ident["identity_sha256"])
        return 0
    if cmd == "supplement-package":
        print(json.dumps(supplement_package_hashes(supplement_ctx()), indent=1))
        return 0
    if cmd == "supplement-verify":                       # desk: the row-21 verifier on the current execution
        from stage_a_guard import execution_identity
        ident = execution_identity(PLAN, MANIFEST, RECEIPT, None)
        print(json.dumps(supplement_receipt_ok(ident), indent=1, default=str))
        return 0
    if cmd == "worker":
        phase = sys.argv[2]
        if phase == "gates":
            return run_gates()
        if phase == "supplement_gates":
            return run_supplement_gates()
        try:
            out = {"instrumented": run_instrumented, "native": run_native, "report": run_report,
                   "supplement_instrumented": run_supplement_instrumented,
                   "supplement_native": run_supplement_native, "supplement_receipt": run_supplement_receipt}[phase]()
        except Hold as h:
            print(str(h.code), file=sys.stderr)
            return 4
        except SystemExit:
            raise
        except BaseException as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(out, default=str))
        return 0
    raise SystemExit(f"unknown command {cmd!r}: plan | identity | package | supplement-plan | supplement-identity | "
                     f"supplement-package | supplement-verify | worker <phase>")
    out = None
    print(json.dumps(out, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

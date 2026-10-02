"""Photograph arm, Stage A (ledger row 20, framework §8.4): native fidelity and profiling - the runner, revision 2.

Revision 2 answers Codex's NOT ON BOARD record (RSC f9d2ef3) through R052's repair brief of 2 October 2026; the
repair-by-repair map is in STAGE_A_CRITERIA.md §0. NOT RUN: no forward has run on any development image.

    .venv-image/bin/python stimuli/photo/stage_a.py plan          # desk: freeze stage_a_plan.json (no model forward)
    .venv-image/bin/python stimuli/photo/stage_a.py identity      # desk: write stage_a_identity.json (no model load)
    .venv-image/bin/python stimuli/photo/stage_a.py package       # desk: print the hashes ROW20_GO.json must bind
    .venv-image/bin/python stimuli/photo/stage_a.py instrumented  # after the go; one process
    .venv-image/bin/python stimuli/photo/stage_a.py native        # then, in a fresh process
    .venv-image/bin/python stimuli/photo/stage_a.py report        # then; also after a stop

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
import os
import random
import subprocess
import sys
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
TOP_K = 50
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
                           "system_sample_s": C.SYS_SAMPLE_S, "tail_reserve_s": C.TAIL_RESERVE_S,
                           "stop_reserve_s": C.STOP_RESERVE_S, "report_reserve_s": C.REPORT_RESERVE_S,
                           "term_grace_s": C.TERM_GRACE_S, "memory_stop_bytes": C.MEM_STOP,
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
    return {"revision": 3, "seed": SEED, "a_grid_sha256": grid["sha256"], "inputs": inputs,
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


def package_hashes(ctx: Ctx) -> dict:
    plan = json.loads(ctx.plan_path.read_text())
    return {"criteria_sha256": sha_file(ctx.criteria_path), "identity_sha256": sha_file(ctx.identity_path),
            "plan_sha256": sha_file(ctx.plan_path), "manifest_sha256": sha_file(ctx.manifest_path),
            "budget_sha256": budget_sha256(plan["envelope"])}


def load_frozen(ctx: Ctx) -> tuple[dict, dict]:
    plan = json.loads(ctx.plan_path.read_text())
    if plan.get("revision") != 3:
        raise SystemExit("refused: stage_a_plan.json is not revision 3")
    if budget_sha256(envelope()) != plan["budget_sha256"]:
        raise SystemExit("refused: the code's envelope differs from the frozen plan's")
    ids = [a["id"] for a in plan["attempts"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("refused: duplicate attempt ids in the plan")
    manifest = {r["concept"]: r for r in json.loads(ctx.manifest_path.read_text())["records"]}
    for k, h in plan["manifest_records_sha256"].items():
        if sha(json.dumps(manifest[k], sort_keys=True).encode()) != h:
            raise SystemExit(f"refused: manifest record {k} differs from the frozen plan's")
    return plan, manifest


def desk_gates(ctx: Ctx) -> dict:
    """Run by the CONTROLLER before it spawns anything (closure group 1): the frozen plan and manifest, the
    positions receipt, the go bound to an attestation of this exact package (re-derived at the reviewed commit), a
    fresh execution identity equal to the frozen one, and a recovery file for every interrupted try. Any failure
    holds; nothing has run."""
    from stage_a_guard import execution_identity, recovery_files, require_go
    plan, _ = load_frozen(ctx)
    rc = json.loads(ctx.receipt_path.read_text()) if ctx.receipt_path.exists() else {}
    if not (rc.get("all_equal") is True and rc.get("plan_sha256") == sha_file(ctx.plan_path)):
        raise SystemExit("refused: the positions receipt is absent, failing or for another plan")
    pkg = package_hashes(ctx)
    (ctx.check_go or (lambda c: require_go(c.go_path, pkg, verify_at_commit=package_at_commit)))(ctx)
    frozen = json.loads(ctx.identity_path.read_text())
    tmp = ctx.out / "identity_files.now.json"
    ctx.out.mkdir(parents=True, exist_ok=True)
    now = (ctx.compute_identity or (lambda: execution_identity(ctx.plan_path, ctx.manifest_path, ctx.receipt_path,
                                                               tmp)))()
    if now["identity_sha256"] != frozen["identity_sha256"]:
        raise SystemExit(f"refused: execution identity now {now['identity_sha256']} differs from the frozen "
                         f"{frozen['identity_sha256']}")
    st = ctx.out / "stage_a_state.json"
    pending = json.loads(st.read_text())["interrupted"] if st.exists() else []
    files = {(f["attempt_id"], f["session"], f["try"]) for f in recovery_files(ctx.out)}
    missing = [i for i in pending if (i["id"], i["session"], i["try"]) not in files]
    if missing:
        raise SystemExit(f"refused: interrupted tries need an owner's recovery file each: "
                         + ", ".join(f"RECOVERY_{i['id']}__{i['session']}__{i['try']}.json" for i in missing))
    return {"package": pkg, "identity": now["identity_sha256"]}


def package_at_commit(commit: str) -> dict:
    """The five package hashes as they were at the reviewed commit (closure group 1)."""
    rel = {k: str(v.relative_to(RSC_ROOT)) for k, v in (("criteria", CRITERIA), ("identity", IDENTITY), ("plan", PLAN),
                                                          ("manifest", MANIFEST))}
    blob = {}
    for k, r in rel.items():
        g = subprocess.run(["git", "-C", str(RSC_ROOT), "show", f"{commit}:{r}"], capture_output=True)
        if g.returncode != 0:
            raise SystemExit(f"refused: {r} absent at the reviewed commit {commit}")
        blob[k] = g.stdout
    plan = json.loads(blob["plan"])
    return {"criteria_sha256": sha(blob["criteria"]), "identity_sha256": sha(blob["identity"]),
            "plan_sha256": sha(blob["plan"]), "manifest_sha256": sha(blob["manifest"]),
            "budget_sha256": budget_sha256(plan["envelope"])}


def worker_open(ctx: Ctx, phase: str, *, terminal_gate: bool = True):
    """A WORKER's start: it must have been launched by the controller that holds the lock (closure group 3); then
    the terminal gate, the frozen inputs, the attempt ledger and the consumption of any recovery file that names
    one of its interrupted tries (closure group 2)."""
    from enforce import Budget
    from stage_a_guard import check_terminal, recovery_files
    if ctx.verify_controller:
        cpid = os.environ.get("STAGE_A_CONTROLLER_PID")
        lock = json.loads((ctx.out / "LOCK").read_text() or "{}") if (ctx.out / "LOCK").exists() else {}
        if not cpid or int(cpid) != os.getppid() or lock.get("pid") != int(cpid):
            raise SystemExit("refused: a worker runs only under the controller that holds the task lock")
    if terminal_gate:
        check_terminal(ctx.out)
    plan, manifest = load_frozen(ctx)
    ident = json.loads(ctx.identity_path.read_text())["identity_sha256"]
    budget = Budget(ctx.out / "stage_a_state.json", "row20", ident, [ctx.out],
                    os.environ.get("STAGE_A_SESSION", "test"), carry_in=ENGINEERING_CARRY,
                    storage_limit=int(os.environ.get("STAGE_A_STORAGE_LIMIT", 0)) or None, **ctx.budget_kwargs)
    for f in recovery_files(ctx.out):
        key = (f["attempt_id"], f["session"], f["try"])
        if any((i["id"], i["session"], i["try"]) == key for i in budget.state["interrupted"]):
            budget.authorise_recovery(f)
    if budget.state["interrupted"]:
        raise SystemExit(f"refused: interrupted tries without a recovery file: {budget.state['interrupted']}")
    return budget, plan, manifest


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
        inst = (ctx.instrument_factory or default_instrument)()
        expect = (ctx.post_load or post_load_instrumented)(inst)
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(ctx.identity_files)))()
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
            else:
                ed = edits_for(ce, case, x, seq, plain_res.get(x["index"]))
                with budget.attempt(aid, a["kind"], passes=1) as att:
                    r = inst.capture(seq, px["pv"], capture_layers=LAYERS, request_token_ids=plan["request_token_ids"],
                                     top_k=TOP_K, edits=ed)
                    validate_pass(r, x, seq, case, plan, expect)
                    res = residual_array(r)
                    if sha(res.tobytes()) != r["residuals"]["sha256"]:
                        raise StopCheck(f"{aid}: residual bytes differ from the capture's own hash")
                    rec = {k: r[k] for k in ("input_ids_sha256", "requested", "top_ids", "top_logits", "edit_log",
                                             "logsumexp", "timing_s", "image", "gdn_inference_kernel", "n_tokens")}
                    rec.update(id=aid, case=case, index=x["index"], kind=a["kind"],
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
        summary = finish_instrumented(ctx, budget, plan, recs, enc)
        return summary
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            set_terminal(ctx.out, "instrumented", f"{type(exc).__name__}: {exc}")
        raise


def finish_instrumented(ctx: Ctx, budget, plan: dict, recs: dict, enc: list) -> dict:
    from enforce import write_json_atomic
    ids = [a["id"] for a in plan["attempts"] if a["phase"] == "instrumented"]
    if sorted(recs) != sorted(ids) or len(set((r["index"], r["case"]) for r in recs.values())) != len(ids):
        raise StopCheck("instrumented phase incomplete or ids not unique")
    budget.final_size()
    done = {"phase": "instrumented", "attempts": {i: budget.completed(i) for i in ids},
            "encoder_sensitivity": {"pair": enc, "passed": True}, "identity": budget.identity}
    write_json_atomic(ctx.out / "INSTRUMENTED_DONE.json", done)
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
    if sorted(done["attempts"]) != sorted(ids) or done["identity"] != budget.identity:
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
    if not all(np.isfinite(stats)):
        raise StopCheck("a comparison statistic is nonfinite")
    row["argmax_equal"] = row["argmax_inst"] == row["argmax_native"]
    row["pass"] = row["rel_l2_max"] <= TOL["rel_l2"] and row["logit_max_abs"] <= TOL["logit"] and row["argmax_equal"]
    return row


def run_native(ctx: Ctx | None = None) -> dict:
    ctx = ctx or Ctx()
    from stage_a_guard import set_terminal
    budget, plan, manifest = worker_open(ctx, "native")
    try:
        plains = admit_native(ctx, plan, budget)
        vmodel, processor, tok, forward = (ctx.native_factory or default_native)()
        if any(m == "jlens_qwen" or m.startswith("jlens_qwen.") for m in sys.modules):
            raise StopCheck("jlens_qwen is imported in the native process: the dispatch is not mlx-vlm's own")
        (ctx.origins_check or (lambda: __import__("stage_a_guard").check_imported_origins(ctx.identity_files)))()
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
                    rec = {"id": aid, "index": x["index"], "case": "native", "kind": a["kind"],
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
            prec, pres = plains[x["index"]]
            li = np.array([q["logit"] for q in prec["requested"]], dtype=np.float64)
            ln = np.asarray(rec["requested_logits"], dtype=np.float64)
            row = {"index": x["index"], "id": aid, **compare(pres, nres, li, ln),
                   "inputs_embeds_equal_instrumented_merge": rec["inputs_embeds_equal_instrumented_merge"]}
            rows.append(row)
            if not row["pass"]:
                raise StopCheck(f"{aid}: native parity failed (rel_l2_max {row['rel_l2_max']:.3g}, logit "
                                f"{row['logit_max_abs']:.3g}, argmax_equal {row['argmax_equal']})")
        finish_native(ctx, budget, plan, rows)
        return {"native": len(rows), "counters": budget.state["counters"]["row20"]}
    except BaseException as exc:
        if not isinstance(exc, SystemExit):
            set_terminal(ctx.out, "native", f"{type(exc).__name__}: {exc}")
        raise


def finish_native(ctx: Ctx, budget, plan: dict, rows: list) -> None:
    from enforce import write_json_atomic
    ids = [a["id"] for a in plan["attempts"] if a["phase"] == "native"]
    for aid in ids:                                        # all 20 re-validated from disk before any pass report
        load_outputs(ctx.out, aid, budget.completed(aid) or {})
    if [r["id"] for r in rows] != ids or not all(r["pass"] for r in rows):
        raise StopCheck("native results incomplete or failing")
    budget.final_size()
    write_json_atomic(ctx.out / "native_parity.json", rows)
    write_json_atomic(ctx.out / "NATIVE_DONE.json", {"phase": "native", "attempts": {i: budget.completed(i)
                                                                                      for i in ids}})


# ================================================================================================================
# The report phase (inside A's clock; runs after a pass or after a stop)
# ================================================================================================================
def run_report(ctx: Ctx | None = None) -> dict:
    """The report WORKER: runs after a pass or a stop (no terminal gate), inside the controller's report reserve. It
    is ADMISSIBLE only when the controller passed the desk gates for this exact package in this run
    (STAGE_A_GATES_OK=1); otherwise it is labelled a diagnostic STOPPED report that confers nothing."""
    import stage_a_report
    budget, plan, _ = worker_open(ctx or Ctx(), "report", terminal_gate=False)
    ctx = ctx or Ctx()
    return stage_a_report.build(ctx.out, plan, budget.state, admissible=os.environ.get("STAGE_A_GATES_OK") == "1")


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
    if cmd == "worker":
        phase = sys.argv[2]
        try:
            out = {"instrumented": run_instrumented, "native": run_native, "report": run_report}[phase]()
        except SystemExit:
            raise
        except BaseException as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(out, default=str))
        return 0
    raise SystemExit(f"unknown command {cmd!r}: plan | identity | package | worker <phase>")
    out = None
    print(json.dumps(out, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

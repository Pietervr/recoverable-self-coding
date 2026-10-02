"""Photograph arm, Stage A (row 20): the INDEPENDENT VALIDATOR and the report - revision 5 (Codex RSC 1bf9890 A6 and
A7; revision 4 answered RSC 081f17b groups 5 and 6). Revision 5: the ledger's legal domains (enforce.check_ledger -
exact integer types, positive tries, the declared passes per try, non-negative counters, completed <= started, coherent
open/interrupted/recovery state) before its equations; requested ranks integers in [1, vocabulary] (never bool) that
agree with the top-k and with the order of their logits; top-k ids distinct integers in [0, vocabulary) with finite,
non-increasing logits; the final-logit dtype one of the capture's names and the same on every record; validation
restricted to the instrumented phase is the PRE-NATIVE ADMISSION; both figures are always written; the receipt is
written only after the caller's identity recheck. Runs as the controller's report worker, after a pass or a stop; never a forward; never converts,
grants or consumes ledger authority (it reads `enforce.read_ledger`).

VALIDATOR (group 5). Trusts no summary and no boolean that it can recompute. For every one of the 178 planned ids it
requires a commit in the ledger, re-reads every committed output and its sha256, and checks the record's EXACT key set
and schema tag, its planned id, index, case and kind, and then, from the archived data:
  instrumented  expanded-ids hash (plan's frozen hash; the suffix diagnostic's declared hash) and token count; readout
                positions and capture layers; the residual metadata (bfloat16, [64, 3, D], hash = the array's) and the
                array's shape, dtype, finiteness and hash; final-logit metadata (dtype, the same vocabulary size on
                every record, hash = logits_sha256); requested ids in order with finite logits and integer ranks;
                top_k ids and finite logits; edit/dispatch: edits installed exactly for edited cases, one edit-log
                entry with the case's mode, layer 41, the marker positions and the declared alpha; the GDN kernel;
                the image: exact keys, frozen pixel hash and grid, 144 tokens, features [144, D] in one declared
                dtype, frozen and effective positions, 32 rotary calls (0, n), one embed call, the merge (exact keys,
                image/text equality flags, 144 contiguous rows, a merged digest equal on every case of the input that
                shares its ids), the feature digest equal across all cases of the input, and the BOUNDARY: its FP32
                bytes decoded, D values, sha256 recomputed, finiteness recomputed and equal to the flag.
  native        exact keys and tag; decoder calls exactly one per layer (64); effective positions; the merged
                input-embedding digest EQUAL to the paired plain record's merge digest, compared from the archive
                (the stored boolean must agree with that comparison); finite requested logits; the residual array.
The LEDGER: identity = the frozen identity, caps = the declared caps, carry = the engineering carry; attempted and
completed ids planned (no unknown or extra id), completed kinds and output maps exact; counters recomputed from the
attempts (started, completed, failed, passes; aggregate = rows). OUTPUT MEMBERSHIP: every file under passes/ is a
committed output. Both phase records equal the ledger's committed output maps (INSTRUMENTED_DONE also the identity).
It then RECOMPUTES every criterion: the 120 bitwise cases, the two suffix-isolation diagnostics, the encoder pair, the
native embedding equality and all 20 native comparisons with stage_a.compare at the fixed tolerances;
native_parity.json is only compared with the recomputation.

WHAT IS LIVE-BOUND, NOT RECOMPUTED. The full final logits and the 144 x D projected features are not archived (about
1 MB and 3 MB per pass); their digests (logits_sha256, features_sha256) and the merge equality flags were computed
in the pass and are compared here as recorded digests. The bitwise criterion therefore compares recorded residual
(recomputed from the archive), logit and feature digests (recorded).

REPORT (group 6). Writes, in order: the two SVG figures, report/STAGE_A_REPORT.md, report/stage_a_report.json, and
LAST report/REPORT_RECEIPT.json naming the session, the gates' package and identity and the sha256 of every output -
a failure at any step leaves no receipt for this session, and the controller's FINAL cannot say PASS without it.
The B prediction here is preliminary; STAGE_A_FINAL.json carries the completed one. B ADMISSION is validated, not
asserted: report/INTERPRETATION.md must name its author ("Author: "), a date ("Date: YYYY-MM-DD") on or after the
report, and the sha256 of BOTH figures as they are on disk (`interpretation_status`).
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
import time
from pathlib import Path

import numpy as np

B_PLANNED_ATTEMPTS, B_RESERVE = 1856, 1.25
FEATURE_DTYPES = {"mlx.core.bfloat16", "mlx.core.float16", "mlx.core.float32"}
LOGIT_DTYPES = {"bfloat16", "float16", "float32"}           # jlens capture_endpoint.dtype_name; one on every record
INST_KEYS = {"record_schema", "id", "case", "index", "kind", "residuals_meta", "final_logits", "residuals_sha256",
             "logits_sha256", "arrays", "input_ids_sha256", "n_tokens", "readout_positions", "capture_layers",
             "requested", "top_ids", "top_logits", "edit_log", "edits_installed", "logsumexp", "timing_s", "image",
             "gdn_inference_kernel"}
NAT_KEYS = {"record_schema", "id", "index", "case", "kind", "inputs_embeds_dtype", "requested_logits", "logits_sha256",
            "logits_n", "residuals_sha256", "decoder_calls", "effective_positions_sha256", "inputs_embeds_sha256",
            "inputs_embeds_equal_instrumented_merge", "arrays"}
IMG_KEYS = {"pixel_values_sha256", "grid_thw", "n_image_tokens", "features_shape", "features_dtype",
            "features_all_finite", "positions_sha256", "effective_positions_sha256", "rope_calls",
            "embed_calls_this_pass", "merge", "features_sha256", "boundary_label", "boundary_mean_fp32_b64",
            "boundary_mean_sha256", "boundary_mean_all_finite"}
MERGE_KEYS = {"image_rows_equal_features", "text_rows_equal_embeddings", "n_image_rows", "image_rows_contiguous",
              "merged_sha256", "dtype"}
EDIT_MODE = {"zero_steer": ("steer", 0.0), "zero_ablate": ("ablate", 0.0), "zero_swap": ("swap_delta", 0.0),
             "swap1": ("swap_delta", 1.0), "ablate1": ("ablate", 1.0), "self_patch": ("patch", None)}
HEX64 = re.compile(r"[0-9a-f]{64}")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _finite(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _int(v, lo: int = 0) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= lo


class V:
    def __init__(self):
        self.failures: list[dict] = []

    def need(self, ok, code: str, where: str, detail="") -> bool:
        if not ok:
            self.failures.append({"code": code, "where": where, "detail": str(detail)[:300]})
        return bool(ok)


def _load(out: Path, aid: str, outputs: dict, v: V):
    rec, arrays = None, {}
    want = {f"passes/{aid}.json", f"passes/{aid}.residuals.npy"}
    if not v.need(set(outputs) == want, "OUTPUT_MAP", aid, sorted(outputs)):
        return None, {}
    for rel, h in outputs.items():
        p = out / rel
        if not v.need(p.exists(), "OUTPUT_MISSING", aid, rel) or not v.need(_sha(p.read_bytes()) == h,
                                                                             "OUTPUT_HASH", aid, rel):
            return None, {}
        if rel.endswith(".npy"):
            arrays[rel.split(".")[-2]] = np.load(p, allow_pickle=False)
        else:
            rec = json.loads(p.read_text())
    v.need(isinstance(rec, dict), "RECORD_MISSING", aid)
    if isinstance(rec, dict):
        v.need(rec.get("arrays") == {f"passes/{aid}.residuals.npy": outputs[f"passes/{aid}.residuals.npy"]},
               "RECORD_ARRAYS", aid)
    return (rec if isinstance(rec, dict) else None), arrays


def _boundary(img: dict, D: int, v: V, aid: str) -> None:
    try:
        b = base64.b64decode(img["boundary_mean_fp32_b64"], validate=True)
    except Exception as exc:
        v.need(False, "BOUNDARY_BYTES", aid, exc)
        return
    ok = v.need(len(b) == 4 * D, "BOUNDARY_BYTES", aid, len(b))
    v.need(_sha(b) == img.get("boundary_mean_sha256"), "BOUNDARY_HASH", aid)
    if ok:
        fin = bool(np.all(np.isfinite(np.frombuffer(b, dtype=np.float32))))
        v.need(fin and img.get("boundary_mean_all_finite") is True, "BOUNDARY_FINITE", aid)


def _inst(rec: dict, arr: dict, a: dict, x: dict, plan: dict, suffix: dict, D: int, v: V, aid: str) -> None:
    case = a["case"]
    v.need(rec.get("record_schema") == "stage_a.instrumented.v4" and set(rec) == INST_KEYS, "RECORD_SCHEMA", aid,
           sorted(set(rec) ^ INST_KEYS))
    if set(rec) != INST_KEYS:
        return
    exp = x["expected"]
    ids = suffix[x["index"]]["ids_sha256"] if case == "suffix_isolation" else exp["ids_sha256"]
    v.need(rec["input_ids_sha256"] == ids, "INPUT_IDS", aid)
    v.need(rec["n_tokens"] == exp["n"], "TOKEN_COUNT", aid, rec["n_tokens"])
    v.need(rec["readout_positions"] == exp["marker_positions"], "READOUT", aid)
    v.need(rec["capture_layers"] == plan["capture_layers"], "CAPTURE_LAYERS", aid)
    r = arr.get("residuals")
    rm = rec["residuals_meta"]
    v.need(rm == {"dtype": "bfloat16", "shape": [64, 3, D], "sha256": rec["residuals_sha256"]}, "RESIDUAL_META", aid)
    if v.need(r is not None and r.shape == (64, 3, D) and r.dtype == np.uint16, "SHAPE_DTYPE", aid,
              None if r is None else (r.shape, r.dtype)):
        import stage_a as A
        v.need(bool(np.all(np.isfinite(A.bf16_to_f32(r)))), "NONFINITE", aid, "residuals")
        v.need(_sha(np.ascontiguousarray(r).tobytes()) == rec["residuals_sha256"], "ARRAY_HASH", aid)
    fl = rec["final_logits"]
    n = fl.get("n") if isinstance(fl, dict) else None
    v.need(isinstance(fl, dict) and set(fl) == {"dtype", "n", "sha256"} and _int(n, 1) and
           fl.get("sha256") == rec["logits_sha256"] and fl.get("dtype") in LOGIT_DTYPES and
           isinstance(rec["logits_sha256"], str) and bool(HEX64.fullmatch(rec["logits_sha256"])), "LOGITS_META", aid)
    n = n if _int(n, 1) else 0
    req = rec["requested"]
    v.need(isinstance(req, list) and all(isinstance(q, dict) and set(q) == {"id", "logit", "rank"} for q in req) and
           [q.get("id") for q in req] == plan["request_token_ids"], "REQUEST_ORDER", aid)
    v.need(isinstance(req, list) and all(isinstance(q, dict) and _finite(q.get("logit")) for q in req), "NONFINITE",
           aid, "requested logits")
    v.need(isinstance(req, list) and all(isinstance(q, dict) and _int(q.get("rank"), 1) and q["rank"] <= n
                                         for q in req), "RANKS", aid, "rank not an int in [1, vocabulary]")
    top, tl = rec["top_ids"], rec["top_logits"]
    top_ok = (isinstance(top, list) and isinstance(tl, list) and len(top) == plan["top_k"] == len(tl) and
              all(_int(t) and t < n for t in top) and len(set(top)) == len(top) and all(_finite(x) for x in tl) and
              all(a >= b for a, b in zip(tl, tl[1:])))
    v.need(top_ok, "TOP_K", aid, "top-k ids not distinct ints in [0, vocabulary) with finite non-increasing logits")
    if top_ok and isinstance(req, list) and all(isinstance(q, dict) and _int(q.get("rank"), 1) for q in req):
        pos = {t: k + 1 for k, t in enumerate(top)}
        v.need(all(q["rank"] == pos[q["id"]] for q in req if q["id"] in pos) and
               all(q["rank"] > len(top) for q in req if q["id"] not in pos), "RANKS", aid,
               "a requested id's rank disagrees with its place in the top-k")
        if all(isinstance(q, dict) and _finite(q.get("logit")) and _int(q.get("id")) for q in req):
            ordered = sorted(req, key=lambda q: (-q["logit"], q["id"]))     # the capture's order: ties by ascending id
            v.need(all(a["rank"] < b["rank"] for a, b in zip(ordered, ordered[1:])), "RANKS", aid,
                   "requested ranks disagree with the order of their logits")
    v.need(_finite(rec["logsumexp"]) and rec["gdn_inference_kernel"] is True, "PASS_META", aid)
    el = rec["edit_log"]
    if case in ("plain", "repeat", "suffix_isolation"):
        v.need(rec["edits_installed"] is False and el == [], "EDITS", aid)
    elif case == "empty":
        v.need(rec["edits_installed"] is True and el == [], "EDITS", aid)
    else:
        mode, alpha = EDIT_MODE[case]
        e = el[0] if isinstance(el, list) and len(el) == 1 and isinstance(el[0], dict) else {}
        v.need(rec["edits_installed"] is True and bool(e) and e.get("mode") == mode and
               e.get("layer") == plan["edit_layer"] and e.get("positions") == exp["marker_positions"] and
               (alpha is None or e.get("alpha") == alpha), "EDITS", aid, e)
    img = rec["image"]
    if not v.need(isinstance(img, dict) and set(img) == IMG_KEYS, "IMAGE_SCHEMA", aid,
                  sorted(set(img) ^ IMG_KEYS) if isinstance(img, dict) else img):
        return
    m = img["merge"]
    for code, cond in (("PIXELS", img["pixel_values_sha256"] == x["pixel_values_sha256"]),
                       ("GRID", img["grid_thw"] == x["grid_thw"]),
                       ("TOKENS", img["n_image_tokens"] == 144 and img["features_shape"] == [144, D]),
                       ("FEATURE_DTYPE", img["features_dtype"] in FEATURE_DTYPES),
                       ("POSITIONS", img["positions_sha256"] == exp["positions_sha256"]),
                       ("POSITIONS_EFFECTIVE", img["effective_positions_sha256"] == exp["positions_sha256"]),
                       ("FEATURES_FINITE", img["features_all_finite"] is True),
                       ("FEATURE_DIGEST", isinstance(img["features_sha256"], str) and
                        bool(HEX64.fullmatch(img["features_sha256"]))),
                       ("ROTARY", [list(c) for c in img["rope_calls"]] == [[0, exp["n"]]] * 32),
                       ("ONE_PREFILL", img["embed_calls_this_pass"] == 1),
                       ("MERGE", isinstance(m, dict) and set(m) == MERGE_KEYS and
                        m["image_rows_equal_features"] is True and m["text_rows_equal_embeddings"] is True and
                        m["image_rows_contiguous"] is True and m["n_image_rows"] == 144 and
                        isinstance(m["merged_sha256"], str) and bool(HEX64.fullmatch(m["merged_sha256"])))):
        v.need(cond, code, aid)
    _boundary(img, D, v, aid)


def _nat(rec: dict, arr: dict, x: dict, plan: dict, plain: dict | None, D: int, v: V, aid: str) -> None:
    v.need(rec.get("record_schema") == "stage_a.native.v4" and set(rec) == NAT_KEYS, "RECORD_SCHEMA", aid,
           sorted(set(rec) ^ NAT_KEYS))
    if set(rec) != NAT_KEYS:
        return
    r = arr.get("residuals")
    if v.need(r is not None and r.shape == (64, 3, D) and r.dtype == np.float32, "SHAPE_DTYPE", aid,
              None if r is None else (r.shape, r.dtype)):
        v.need(bool(np.all(np.isfinite(r))), "NONFINITE", aid, "native residuals")
        v.need(_sha(np.ascontiguousarray(r).tobytes()) == rec["residuals_sha256"], "ARRAY_HASH", aid)
    rl = rec["requested_logits"]
    v.need(isinstance(rl, list) and len(rl) == len(plan["request_token_ids"]) and all(_finite(q) for q in rl),
           "NATIVE_LOGITS", aid)
    v.need(isinstance(rec["logits_n"], int) and rec["logits_n"] > 0 and isinstance(rec["logits_sha256"], str) and
           bool(HEX64.fullmatch(rec["logits_sha256"])), "LOGITS_META", aid)
    v.need(rec["decoder_calls"] == {"min": 1, "max": 1, "layers": 64}, "DECODER_CALLS", aid, rec["decoder_calls"])
    v.need(rec["effective_positions_sha256"] == x["expected"]["positions_sha256"], "POSITIONS_EFFECTIVE", aid)
    merged = ((plain or {}).get("image") or {}).get("merge", {}).get("merged_sha256") if plain else None
    eq = merged is not None and rec["inputs_embeds_sha256"] == merged
    v.need(eq, "EMBEDDINGS", aid, "native inputs_embeds_sha256 != the paired plain merge digest")
    v.need(rec["inputs_embeds_equal_instrumented_merge"] is eq, "EMBEDDINGS_FLAG", aid)
    v.need(isinstance(rec["inputs_embeds_dtype"], str), "PASS_META", aid)


def _ledger(state: dict, plan: dict, identity: str | None, v: V, witness=None) -> None:
    import stage_a as A
    from enforce import CAPS, check_ledger
    planned = {a["id"]: a for a in plan["attempts"]}
    for prob in check_ledger(state, witness_dir=witness):   # legal domains + bound owner authority (A6; rev 7 D)
        v.need(False, "LEDGER_DOMAIN", "state", prob)
    if not isinstance(state, dict) or not isinstance(state.get("attempts"), dict) or \
            not isinstance(state.get("completed"), dict):
        return
    v.need(identity is None or state.get("identities", {}).get("row20") == identity, "LEDGER_IDENTITY", "state")
    v.need(state.get("caps") == json.loads(json.dumps(CAPS)), "LEDGER_CAPS", "state")
    carry = A.ENGINEERING_CARRY
    v.need(state.get("carry_in", {}).get("row20") == carry, "LEDGER_CARRY", "state")
    att, comp = state.get("attempts", {}), state.get("completed", {})
    v.need(set(att) <= set(planned), "LEDGER_UNKNOWN_ID", "attempts", sorted(set(att) - set(planned))[:5])
    v.need(set(comp) <= set(planned), "LEDGER_UNKNOWN_ID", "completed", sorted(set(comp) - set(planned))[:5])
    for i, c in comp.items():
        a = att.get(i, {})
        v.need(a.get("status") == "completed" and c.get("kind") == planned.get(i, {}).get("kind") and
               a.get("kind") == c.get("kind"), "LEDGER_COMPLETED", i)
    tries = sum(a.get("tries", 0) for a in att.values() if isinstance(a, dict) and _int(a.get("tries", 0)))
    passes = sum(a["tries"] * a["passes"] for a in att.values() if isinstance(a, dict) and _int(a.get("tries"))
                 and _int(a.get("passes")))
    openp = 1 if state.get("open_attempt") else 0
    want = {"started": carry["started"] + tries, "passes": carry["passes"] + passes,
            "completed": carry["completed"] + len(comp), "failed": carry["failed"] + tries - len(comp) - openp}
    got = state.get("counters", {}).get("row20", {})
    v.need({k: got.get(k) for k in want} == want, "LEDGER_COUNTERS", "row20", (got, want))
    agg = state.get("counters", {}).get("aggregate", {})
    r21 = state.get("counters", {}).get("row21", {})
    v.need({k: agg.get(k) for k in want} == {k: got.get(k, 0) + r21.get(k, 0) for k in want}, "LEDGER_COUNTERS",
           "aggregate")
    v.need(got.get("passes", 0) <= CAPS["row20"]["attempts"] and agg.get("passes", 0) <= CAPS["aggregate"]["attempts"],
           "LEDGER_CAP", "counters", got.get("passes"))
    for it in state.get("interrupted", []):
        v.need(isinstance(it, dict) and att.get(it.get("id"), {}).get("status") == "interrupted",
               "LEDGER_INTERRUPTED", str(it.get("id") if isinstance(it, dict) else it))
    for i, a in att.items():
        v.need(isinstance(a, dict) and a.get("kind") == planned.get(i, {}).get("kind") and
               a.get("passes") == 1, "LEDGER_KIND", i)


def validate(out: Path, plan: dict, state: dict | None, *, identity: str | None = None,
             phases: tuple = ("instrumented", "native")) -> dict:
    """phases=("instrumented",) is the PRE-NATIVE ADMISSION (A6): the ledger's domains, every instrumented record and
    array under the full instrumented predicates, the cross-case, bitwise, suffix and encoder criteria and
    INSTRUMENTED_DONE - nothing native is required."""
    import stage_a as A
    v = V()
    if state is None:
        v.need(False, "NO_LEDGER", "stage_a_state.json")
        return {"pass": False, "failures": v.failures, "bitwise": {}, "suffix": {}, "encoder_pair_differs": False,
                "parity": []}
    D = A.D_MODEL
    inputs = {x["index"]: x for x in plan["inputs"]}
    suffix = {s["base_index"]: s for s in plan["diagnostics"]["suffix_isolation"]}
    _ledger(state, plan, identity, v, witness=out)
    recs, arrs = {}, {}
    for a in plan["attempts"]:
        if a["phase"] not in phases:
            continue
        aid = a["id"]
        c = state["completed"].get(aid) if isinstance(state.get("completed"), dict) else None
        if not v.need(c is not None, "NOT_COMMITTED", aid):
            continue
        rec, arr = _load(out, aid, c.get("outputs") or {}, v)
        if rec is None:
            continue
        x = inputs[a["index"]]
        v.need((rec.get("id"), rec.get("index"), rec.get("case"), rec.get("kind")) ==
               (aid, a["index"], a["case"], a["kind"]), "RECORD_ID", aid,
               (rec.get("id"), rec.get("index"), rec.get("case"), rec.get("kind")))
        if a["phase"] == "instrumented":
            _inst(rec, arr, a, x, plan, suffix, D, v, aid)
        recs[aid], arrs[aid] = rec, arr
    plain = {i: recs.get(f"{i:02d}-plain") for i in inputs}
    for aid, r in recs.items():
        a = next(p for p in plan["attempts"] if p["id"] == aid)
        if a["phase"] == "native":
            _nat(r, arrs[aid], inputs[a["index"]], plan, plain.get(a["index"]), D, v, aid)
    ns = {r.get("final_logits", {}).get("n") for r in recs.values() if r.get("record_schema") ==
          "stage_a.instrumented.v4"} | {r.get("logits_n") for r in recs.values() if r.get("record_schema") ==
                                        "stage_a.native.v4"}
    v.need(len(ns) <= 1, "VOCAB_SIZE", "all", sorted(map(str, ns)))
    fdt = {(r.get("image") or {}).get("features_dtype") for r in recs.values() if r.get("record_schema") ==
           "stage_a.instrumented.v4"}
    v.need(len(fdt) <= 1, "FEATURE_DTYPE", "all", sorted(map(str, fdt)))
    ldt = {(r.get("final_logits") or {}).get("dtype") for r in recs.values() if r.get("record_schema") ==
           "stage_a.instrumented.v4"}
    v.need(len(ldt) <= 1, "LOGITS_META", "all", sorted(map(str, ldt)))
    for i, p0 in plain.items():                       # one input, one image: features and merge agree across cases
        if not p0 or "image" not in p0:
            continue
        for aid, r in recs.items():
            if r.get("index") != i or r.get("record_schema") != "stage_a.instrumented.v4" or "image" not in r:
                continue
            v.need(r["image"]["features_sha256"] == p0["image"]["features_sha256"], "FEATURES_ACROSS_CASES", aid)
            if r.get("case") != "suffix_isolation":
                v.need(r["image"]["merge"].get("merged_sha256") == p0["image"]["merge"].get("merged_sha256"),
                       "MERGE_ACROSS_CASES", aid)
    committed = {rel for c in (state.get("completed") or {}).values() if isinstance(c, dict)
                 for rel in (c.get("outputs") or {})}
    present = {str(p.relative_to(out)) for p in (out / "passes").glob("*")} if (out / "passes").exists() else set()
    v.need(present <= committed, "OUTPUT_MEMBERSHIP", "passes/", sorted(present - committed)[:5])
    for name, ph, keys in (("INSTRUMENTED_DONE.json", "instrumented", {"phase", "attempts", "encoder_sensitivity",
                                                                       "identity"}),
                           ("NATIVE_DONE.json", "native", {"phase", "attempts"})):
        if ph not in phases:
            continue
        p = out / name
        ids = [a["id"] for a in plan["attempts"] if a["phase"] == ph]
        if v.need(p.exists(), "PHASE_RECORD_MISSING", name):
            d = json.loads(p.read_text())
            v.need(set(d) == keys and d.get("phase") == ph, "PHASE_RECORD_SCHEMA", name)
            v.need(d.get("attempts") == {i: (state["completed"].get(i) or {}).get("outputs") for i in ids},
                   "PHASE_RECORD_MISMATCH", name)
            if ph == "instrumented":
                v.need(identity is None or d.get("identity") == identity, "PHASE_RECORD_IDENTITY", name)
    key = lambda r: (r["residuals_sha256"], r["logits_sha256"], r["image"]["features_sha256"])
    bitwise = {}
    for aid, r in recs.items():
        if r.get("case") in plan["bitwise_cases"] and "image" in r:
            p0 = plain.get(r["index"])
            bitwise[aid] = bool(p0) and "image" in p0 and key(r) == key(p0)
            v.need(bitwise[aid], "BITWISE", aid)
    sfx = {}
    for s_ in plan["diagnostics"]["suffix_isolation"]:
        aid = f"{s_['base_index']:02d}-suffix_isolation"
        r, p0 = recs.get(aid), plain.get(s_["base_index"])
        sfx[aid] = bool(r and p0) and r.get("residuals_sha256") == p0.get("residuals_sha256") and \
            r.get("input_ids_sha256") == s_["ids_sha256"]
        v.need(sfx[aid], "SUFFIX_ISOLATION", aid)
    e0, e1 = plan["diagnostics"]["encoder_sensitivity"]["pair"]
    enc = bool(plain.get(e0) and plain.get(e1) and "image" in plain[e0] and "image" in plain[e1])
    if enc:
        i0, i1 = plain[e0]["image"], plain[e1]["image"]
        enc = (i0["pixel_values_sha256"] != i1["pixel_values_sha256"] and i0["features_sha256"] != i1["features_sha256"]
               and i0["grid_thw"] == i1["grid_thw"])
    v.need(enc, "ENCODER_SENSITIVITY", str([e0, e1]))
    parity = []
    if "native" not in phases:
        v.need(len(bitwise) == 120, "BITWISE_COUNT", str(len(bitwise)))
        return {"pass": not v.failures, "failures": v.failures, "bitwise": bitwise, "suffix": sfx,
                "encoder_pair_differs": enc, "parity": [], "records": recs, "arrays": arrs}
    for x in plan["inputs"]:
        aid = f"{x['index']:02d}-native"
        p0, n0 = plain.get(x["index"]), recs.get(aid)
        if not (p0 and n0 and "residuals" in arrs.get(aid, {}) and "residuals" in arrs.get(f"{x['index']:02d}-plain",
                                                                                          {})):
            v.need(False, "PARITY_INPUTS_MISSING", aid)
            continue
        try:
            row = A.compare(arrs[f"{x['index']:02d}-plain"]["residuals"], arrs[aid]["residuals"],
                            np.array([q["logit"] for q in p0["requested"]], dtype=np.float64),
                            np.asarray(n0["requested_logits"], dtype=np.float64))
        except Exception as exc:                      # zero/nonfinite reference norm or statistic, malformed input
            v.need(False, "PARITY_STATISTIC", aid, exc)
            continue
        parity.append({"index": x["index"], "id": aid, **row})
        v.need(row["pass"], "PARITY", aid, (row["rel_l2_max"], row["logit_max_abs"], row["argmax_equal"]))
    stored = out / "native_parity.json"
    if stored.exists():
        s_rows = json.loads(stored.read_text())
        same = [(r.get("id"), r.get("pass"), r.get("rel_l2_max"), r.get("logit_max_abs")) for r in s_rows] == \
               [(r["id"], r["pass"], r["rel_l2_max"], r["logit_max_abs"]) for r in parity]
        v.need(same, "PARITY_SUMMARY_MISMATCH", "native_parity.json")
    v.need(len(parity) == 20 and len({r["id"] for r in parity}) == 20, "PARITY_COUNT", str(len(parity)))
    v.need(len(bitwise) == 120, "BITWISE_COUNT", str(len(bitwise)))
    return {"pass": not v.failures, "failures": v.failures, "bitwise": bitwise, "suffix": sfx,
            "encoder_pair_differs": enc, "parity": parity}


def interpretation_status(out: Path) -> dict:
    """B admission's interpretation item: report/INTERPRETATION.md names its author, a date on or after the report and
    the sha256 of BOTH figures exactly as they are on disk."""
    rep = out / "report"
    p = rep / "INTERPRETATION.md"
    if not p.exists():
        return {"valid": False, "problems": ["absent"]}
    t = p.read_text()
    probs = []
    au = re.search(r"(?m)^Author: (\S.*)$", t)
    dt = re.search(r"(?m)^Date: (\d{4}-\d{2}-\d{2})$", t)
    if not au:
        probs.append("no author")
    if not dt:
        probs.append("no date")
    else:
        try:
            time.strptime(dt.group(1), "%Y-%m-%d")
        except ValueError:
            probs.append("invalid date")
    rc = json.loads((rep / "REPORT_RECEIPT.json").read_text()) if (rep / "REPORT_RECEIPT.json").exists() else {}
    if dt and rc.get("date") and dt.group(1) < rc["date"]:
        probs.append("interpretation dated before the report")
    for fig in ("rel_l2_by_layer.svg", "logit_max_abs.svg"):
        m = re.search(rf"(?m)^{re.escape(fig)} sha256: ([0-9a-f]{{64}})$", t)
        f = rep / fig
        if not f.exists():
            probs.append(f"{fig} absent")
        elif not m:
            probs.append(f"{fig} hash not named")
        elif m.group(1) != _sha(f.read_bytes()):
            probs.append(f"{fig} hash differs from the figure on disk")
    return {"valid": not probs, "problems": probs}


def _svg_lines(series, title, tol):
    W, H, L, R, T, B = 760, 380, 60, 20, 30, 40
    vals = [x for s in series.values() for x in s if np.isfinite(x)] + [tol]
    ymax = max(vals) * 1.1 or 1.0
    n = max((len(s) for s in series.values()), default=1)
    X = lambda i: L + (W - L - R) * i / max(n - 1, 1)
    Y = lambda y: T + (H - T - B) * (1 - y / ymax)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">'
             f'<rect width="{W}" height="{H}" fill="white"/><text x="{L}" y="18" font-size="13">{title}</text>',
             f'<line x1="{L}" y1="{Y(tol):.1f}" x2="{W - R}" y2="{Y(tol):.1f}" stroke="red" stroke-dasharray="4,3"/>']
    for k, s in series.items():
        parts.append(f'<polyline fill="none" stroke="#3366aa" stroke-opacity="0.6" points="'
                     + " ".join(f"{X(i):.1f},{Y(y):.1f}" for i, y in enumerate(s)) + f'"><title>{k}</title></polyline>')
    return "\n".join(parts + ["</svg>"])


def build(out: Path, plan: dict, ledger: dict, *, admissible: bool, session: str = "test", gates: dict | None = None,
          identity: str | None = None, identity_problem: str = "", writer=None, before_receipt=None) -> dict:
    from enforce import write_atomic, write_json_atomic
    W = writer or (lambda p, b: write_atomic(p, b, final=True))
    gates = gates or {}
    rep = out / "report"
    rep.mkdir(parents=True, exist_ok=True)
    state = ledger.get("state")
    ident = identity or gates.get("identity")
    val = validate(out, plan, state, identity=ident)
    terminal = json.loads((out / "TERMINAL.json").read_text()) if (out / "TERMINAL.json").exists() else None
    ctrl = json.loads((out / "controller.json").read_text()) if (out / "controller.json").exists() else {}
    planned = [a["id"] for a in plan["attempts"]]
    st = state or {"attempts": {}, "counters": {"row20": {}}, "carry_in": {}}
    tries = sum(st["attempts"].get(i, {}).get("tries", 0) for i in planned)
    a_seconds = ctrl.get("seconds_total_live", ctrl.get("seconds_total", 0.0)) - ctrl.get("carry_s", 0.0)
    unique_started = sum(1 for i in planned if i in st["attempts"])
    used = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    b = None
    if unique_started:
        caps = (state or {}).get("caps", {}).get("row21") or {"seconds": 4 * 3600, "bytes": 8 << 30}
        ps, pb = a_seconds / unique_started * B_PLANNED_ATTEMPTS, used / unique_started * B_PLANNED_ATTEMPTS
        b = {"seconds_per_unique_attempt_whole_stage": a_seconds / unique_started,
             "bytes_per_unique_attempt": used / unique_started, "predicted_seconds": ps, "predicted_bytes": pb,
             "limit_seconds": caps["seconds"] / B_RESERVE, "limit_bytes": caps["bytes"] / B_RESERVE,
             "note": "PRELIMINARY (as of this report); the completed prediction is in STAGE_A_FINAL.json"}
    interp = interpretation_status(out)
    admission = {"STAGE_A_FINAL_PASS": False, "inspected_figures_and_interpretation": interp["valid"],
                 "interpretation_problems": interp["problems"], "codex_review_of_report": False,
                 "owner_row21_go": False, "b_first_cal_slice": "row 21's own gate", "admitted": False}
    record = {"admissible": admissible, "label": "ADMISSIBLE" if admissible else
              "DIAGNOSTIC - identity/package not verified in this session; confers nothing",
              "identity_problem": identity_problem, "session": session,
              "validator_pass": bool(val["pass"] and admissible and terminal is None),
              "validator": val, "terminal": terminal, "unique_planned_ids": len(planned),
              "unique_ids_started": unique_started, "actual_tries": tries,
              "unreconciled_open_attempt": ledger.get("unreconciled_open_attempt"),
              "interrupted": st.get("interrupted", []),
              "counters_row20": st["counters"].get("row20"), "carry": st.get("carry_in", {}).get("row20"),
              "controller_as_of_report": {k: ctrl.get(k) for k in ("seconds_total_live", "carry_s", "peaks", "stops")},
              "storage_as_of_report": used, "stage_b_prediction": b, "stage_b_admission": admission}
    outputs = {}
    if True:                                          # both figures always (an empty plot after a stop; A7)
        for name, svg in (("rel_l2_by_layer.svg", _svg_lines({f"input {r['index']}": r["rel_l2_by_layer"]
                                                              for r in val["parity"]},
                                                             "Relative L2 by layer (tolerance 0.01)", 0.01)),
                          ("logit_max_abs.svg", _svg_lines({"max |logit diff|": [r["logit_max_abs"] for r in
                                                                                 val["parity"]]},
                                                           "Max |E1 logit difference| by input (tolerance 0.10)",
                                                           0.10))):
            W(rep / name, svg.encode())
            outputs[f"report/{name}"] = _sha(svg.encode())
    md = [f"# Stage A (row 20) report - {record['label']}", "",
          f"Validator: {'PASS' if record['validator_pass'] else 'FAIL'} ({len(val['failures'])} failures). "
          "Only STAGE_A_FINAL.json, written by the controller after this report, can state PASS.", "",
          f"Unique planned ids {len(planned)}; started {unique_started}; actual tries {tries}.", ""]
    if record["unreconciled_open_attempt"] or record["interrupted"]:
        md += ["Interrupted state (described, no authority granted or consumed): open attempt "
               f"{record['unreconciled_open_attempt']}; interrupted tries {record['interrupted']}.", ""]
    md += ["## Failures", ""] + [f"- {f['code']} at {f['where']}: {f['detail']}" for f in val["failures"][:200]] + \
          ["", "## Native parity (recomputed from the committed arrays)", "",
           "| input | rel L2 max | logit max abs | argmax equal | pass |", "|---|---|---|---|---|"] + \
          [f"| {r['index']} | {r['rel_l2_max']:.3g} | {r['logit_max_abs']:.3g} | {r['argmax_equal']} | {r['pass']} |"
           for r in val["parity"]] + \
          ["", "## Stage B", "", "```", json.dumps({"prediction": b, "admission": admission}, indent=1), "```", "",
           "## Interpretation", "", "Not written here: the author inspects the figures and archives "
           "report/INTERPRETATION.md ('Author: ', 'Date: YYYY-MM-DD', and '<figure> sha256: <hex>' for both figures) "
           "before any B admission.", ""]
    mdb = "\n".join(md).encode()
    W(rep / "STAGE_A_REPORT.md", mdb)
    outputs["report/STAGE_A_REPORT.md"] = _sha(mdb)
    jb = json.dumps(record, indent=1, sort_keys=True).encode()
    W(rep / "stage_a_report.json", jb)
    outputs["report/stage_a_report.json"] = _sha(jb)
    if before_receipt is not None:                    # the completion-time identity recheck (A1): no receipt else
        before_receipt()
    receipt = {"session": session, "package": gates.get("package"), "identity": gates.get("identity"),
               "date": time.strftime("%Y-%m-%d"), "outputs": outputs, "admissible": admissible,
               "validator_pass": record["validator_pass"]}
    W(rep / "REPORT_RECEIPT.json", json.dumps(receipt, indent=1, sort_keys=True).encode())
    return {"validator_pass": record["validator_pass"], "failures": len(val["failures"])}

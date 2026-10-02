"""Photograph arm, Stage A (row 20): the INDEPENDENT VALIDATOR and the report - revision 3 (Codex RSC 69539bb closure
groups 5, 6, 7). Runs as the controller's report worker, after a pass or a stop; never a forward.

VALIDATOR (group 5). Trusts no summary. For every one of the 178 planned ids it requires a commit in the state file,
re-reads every committed output and re-checks its sha256, then checks the record's exact planned id, index, case
and kind, its schema, the array's shape, dtype, finiteness and hash, the requested-E1 order and finiteness, and the
frozen pixel, grid, 144-token, position (frozen and effective), merge and boundary fields. Both phase records
(INSTRUMENTED_DONE.json, NATIVE_DONE.json) must equal the state's committed output maps. It then RECOMPUTES every
criterion from the committed arrays and records: the 120 bitwise cases, the two suffix-isolation diagnostics, the
encoder pair (pixel AND feature hashes must differ, grids equal), the native merged-embedding equality, and all 20
native comparisons with stage_a.compare at the fixed tolerances (0.01, 0.10, identical argmax).
native_parity.json is only compared with the recomputation; a mismatch is a failure.

REPORT. report/stage_a_report.json (machine record: validator verdict and every failure with its code), report/
STAGE_A_REPORT.md, and two SVG figures. Cost, peaks and final bytes are as of the report's generation; the complete
figures, including this report's own writes and closure, are in STAGE_A_FINAL.json, which the controller writes
after this worker has exited and which alone can say PASS (it re-checks the terminal record and every cap on the
final figures). Unique planned ids and actual tries are counted separately.

STAGE B (groups 6, 7). The prediction uses whole-stage rates - Stage A's controller seconds and stored bytes per
unique attempt - and requires predicted B total <= 0.8 x row 21's cap (x 1.25): at most 11,520 s and 6.4 GiB. B is
NOT admitted by this report: admission additionally needs STAGE_A_FINAL.json = PASS, the inspected figures with an
archived author interpretation (report/INTERPRETATION.md naming the author, the date and the sha256 of both
figures), a favourable Codex review of the report, and the owner's row-21 go; B's own first-CAL-slice qualification
(decoder, CV, probe and analysis cost) stays with row 21. A diagnostic report (STAGE_A_GATES_OK not set) is labelled
so and confers nothing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

B_PLANNED_ATTEMPTS, B_RESERVE = 1856, 1.25
SHAPE_INST = (64, 3, 5120)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class V:
    def __init__(self):
        self.failures: list[dict] = []

    def need(self, ok, code: str, where: str, detail="") -> bool:
        if not ok:
            self.failures.append({"code": code, "where": where, "detail": str(detail)[:300]})
        return bool(ok)


def _load(out: Path, aid: str, outputs: dict, v: V):
    rec, arrays = None, {}
    for rel, h in outputs.items():
        p = out / rel
        if not v.need(p.exists(), "OUTPUT_MISSING", aid, rel) or not v.need(_sha(p.read_bytes()) == h,
                                                                             "OUTPUT_HASH", aid, rel):
            return None, {}
        if rel.endswith(".npy"):
            arrays[rel.split(".")[-2]] = np.load(p, allow_pickle=False)
        else:
            rec = json.loads(p.read_text())
    v.need(rec is not None, "RECORD_MISSING", aid)
    return rec, arrays


def validate(out: Path, plan: dict, state: dict) -> dict:
    import stage_a as A
    v = V()
    inputs = {x["index"]: x for x in plan["inputs"]}
    recs, arrs = {}, {}
    for a in plan["attempts"]:
        aid = a["id"]
        c = state["completed"].get(aid)
        if not v.need(c is not None, "NOT_COMMITTED", aid):
            continue
        rec, arr = _load(out, aid, c["outputs"], v)
        if rec is None:
            continue
        x = inputs[a["index"]]
        v.need((rec.get("id"), rec.get("index"), rec.get("case")) == (aid, a["index"], a["case"]), "RECORD_ID", aid,
               (rec.get("id"), rec.get("index"), rec.get("case")))
        r = arr.get("residuals")
        if a["phase"] == "instrumented":
            ok = v.need(r is not None and r.shape == SHAPE_INST[:2] + (A.D_MODEL,) and r.dtype == np.uint16,
                        "SHAPE_DTYPE", aid, None if r is None else (r.shape, r.dtype))
            if ok:
                v.need(np.all(np.isfinite(A.bf16_to_f32(r))), "NONFINITE", aid, "residuals")
                v.need(_sha(np.ascontiguousarray(r).tobytes()) == rec.get("residuals_sha256"), "ARRAY_HASH", aid)
            req = rec.get("requested") or []
            v.need([q.get("id") for q in req] == plan["request_token_ids"], "REQUEST_ORDER", aid)
            v.need(all(np.isfinite(q.get("logit", np.nan)) for q in req), "NONFINITE", aid, "requested logits")
            img = rec.get("image") or {}
            m = img.get("merge") or {}
            for code, cond in (("PIXELS", img.get("pixel_values_sha256") == x["pixel_values_sha256"]),
                               ("GRID", img.get("grid_thw") == x["grid_thw"]),
                               ("TOKENS", img.get("n_image_tokens") == 144),
                               ("POSITIONS", img.get("positions_sha256") == x["expected"]["positions_sha256"]),
                               ("POSITIONS_EFFECTIVE", img.get("effective_positions_sha256") ==
                                x["expected"]["positions_sha256"]),
                               ("FEATURES_FINITE", img.get("features_all_finite") is True),
                               ("BOUNDARY_FINITE", img.get("boundary_mean_all_finite") is True),
                               ("MERGE", m.get("image_rows_equal_features") is True and
                                m.get("text_rows_equal_embeddings") is True and m.get("image_rows_contiguous") is True),
                               ("ONE_PREFILL", img.get("embed_calls_this_pass") == 1)):
                v.need(cond, code, aid)
        else:
            ok = v.need(r is not None and r.shape == SHAPE_INST[:2] + (A.D_MODEL,) and r.dtype == np.float32,
                        "SHAPE_DTYPE", aid, None if r is None else (r.shape, r.dtype))
            if ok:
                v.need(np.all(np.isfinite(r)), "NONFINITE", aid, "native residuals")
                v.need(_sha(np.ascontiguousarray(r).tobytes()) == rec.get("residuals_sha256"), "ARRAY_HASH", aid)
            rl = rec.get("requested_logits") or []
            v.need(len(rl) == len(plan["request_token_ids"]) and all(np.isfinite(rl)), "NATIVE_LOGITS", aid)
            v.need(rec.get("effective_positions_sha256") == x["expected"]["positions_sha256"], "POSITIONS_EFFECTIVE",
                   aid)
            v.need(rec.get("inputs_embeds_equal_instrumented_merge") is True, "EMBEDDINGS", aid)
        recs[aid], arrs[aid] = rec, arr
    for name, ph in (("INSTRUMENTED_DONE.json", "instrumented"), ("NATIVE_DONE.json", "native")):
        p = out / name
        ids = [a["id"] for a in plan["attempts"] if a["phase"] == ph]
        if v.need(p.exists(), "PHASE_RECORD_MISSING", name):
            d = json.loads(p.read_text())
            v.need(d.get("attempts") == {i: (state["completed"].get(i) or {}).get("outputs") for i in ids},
                   "PHASE_RECORD_MISMATCH", name)
    # recompute every criterion
    plain = {i: recs.get(f"{i:02d}-plain") for i in inputs}
    key = lambda r: (r["residuals_sha256"], r["logits_sha256"], r["image"]["features_sha256"])
    bitwise = {}
    for aid, r in recs.items():
        if r.get("case") in plan["bitwise_cases"]:
            p0 = plain.get(r["index"])
            bitwise[aid] = bool(p0) and key(r) == key(p0)
            v.need(bitwise[aid], "BITWISE", aid)
    suffix = {}
    for s_ in plan["diagnostics"]["suffix_isolation"]:
        aid = f"{s_['base_index']:02d}-suffix_isolation"
        r, p0 = recs.get(aid), plain.get(s_["base_index"])
        suffix[aid] = bool(r and p0) and r["residuals_sha256"] == p0["residuals_sha256"] and \
            r.get("input_ids_sha256") == s_["ids_sha256"]
        v.need(suffix[aid], "SUFFIX_ISOLATION", aid)
    e0, e1 = plan["diagnostics"]["encoder_sensitivity"]["pair"]
    enc = bool(plain.get(e0) and plain.get(e1))
    if enc:
        i0, i1 = plain[e0]["image"], plain[e1]["image"]
        enc = (i0["pixel_values_sha256"] != i1["pixel_values_sha256"] and i0["features_sha256"] != i1["features_sha256"]
               and i0["grid_thw"] == i1["grid_thw"])
    v.need(enc, "ENCODER_SENSITIVITY", str([e0, e1]))
    parity = []
    for x in plan["inputs"]:
        aid = f"{x['index']:02d}-native"
        p0, n0 = plain.get(x["index"]), recs.get(aid)
        if not (p0 and n0 and "residuals" in arrs.get(aid, {}) and "residuals" in arrs.get(f"{x['index']:02d}-plain", {})):
            v.need(False, "PARITY_INPUTS_MISSING", aid)
            continue
        try:
            row = A.compare(arrs[f"{x['index']:02d}-plain"]["residuals"], arrs[aid]["residuals"],
                            np.array([q["logit"] for q in p0["requested"]], dtype=np.float64),
                            np.asarray(n0["requested_logits"], dtype=np.float64))
        except Exception as exc:                      # zero/nonfinite reference norm or statistic
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
    return {"pass": not v.failures, "failures": v.failures, "bitwise": bitwise, "suffix": suffix,
            "encoder_pair_differs": enc, "parity": parity}


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


def build(out: Path, plan: dict, state: dict, *, admissible: bool) -> dict:
    from enforce import write_atomic, write_json_atomic
    rep = out / "report"
    rep.mkdir(parents=True, exist_ok=True)
    val = validate(out, plan, state)
    terminal = json.loads((out / "TERMINAL.json").read_text()) if (out / "TERMINAL.json").exists() else None
    ctrl = json.loads((out / "controller.json").read_text()) if (out / "controller.json").exists() else {}
    planned = [a["id"] for a in plan["attempts"]]
    tries = sum(state["attempts"].get(i, {}).get("tries", 0) for i in planned)
    a_seconds = ctrl.get("seconds_total_live", ctrl.get("seconds_total", 0.0)) - ctrl.get("carry_s", 0.0)
    unique_started = sum(1 for i in planned if i in state["attempts"])
    used = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    b = None
    if unique_started:
        caps = state["caps"]["row21"]
        ps, pb = a_seconds / unique_started * B_PLANNED_ATTEMPTS, used / unique_started * B_PLANNED_ATTEMPTS
        b = {"seconds_per_unique_attempt_whole_stage": a_seconds / unique_started,
             "bytes_per_unique_attempt": used / unique_started, "predicted_seconds": ps, "predicted_bytes": pb,
             "limit_seconds": caps["seconds"] / B_RESERVE, "limit_bytes": caps["bytes"] / B_RESERVE,
             "time_ok": ps <= caps["seconds"] / B_RESERVE, "storage_ok": pb <= caps["bytes"] / B_RESERVE,
             "note": "preliminary: the complete figures are in STAGE_A_FINAL.json"}
    admission = {"STAGE_A_FINAL_PASS": False, "inspected_figures_and_interpretation": (rep / "INTERPRETATION.md").exists(),
                 "codex_review_of_report": False, "owner_row21_go": False, "b_first_cal_slice": "row 21's own gate",
                 "admitted": False}
    record = {"admissible": admissible, "label": "ADMISSIBLE" if admissible else
              "DIAGNOSTIC - identity/package not verified in this run; confers nothing",
              "validator_pass": bool(val["pass"] and admissible and terminal is None),
              "validator": val, "terminal": terminal, "unique_planned_ids": len(planned),
              "unique_ids_started": unique_started, "actual_tries": tries,
              "counters_row20": state["counters"]["row20"], "carry": state.get("carry_in", {}).get("row20"),
              "controller_as_of_report": {k: ctrl.get(k) for k in ("seconds_total_live", "carry_s", "peaks", "stops")},
              "storage_as_of_report": used, "stage_b_prediction": b, "stage_b_admission": admission}
    if val["parity"]:
        write_atomic(rep / "rel_l2_by_layer.svg", _svg_lines({f"input {r['index']}": r["rel_l2_by_layer"]
                                                             for r in val["parity"]},
                                                            "Relative L2 by layer (tolerance 0.01)", 0.01).encode())
        write_atomic(rep / "logit_max_abs.svg", _svg_lines({"max |logit diff|": [r["logit_max_abs"] for r in
                                                                                 val["parity"]]},
                                                           "Max |E1 logit difference| by input (tolerance 0.10)",
                                                           0.10).encode())
    write_json_atomic(rep / "stage_a_report.json", record)
    md = [f"# Stage A (row 20) report - {record['label']}", "",
          f"Validator: {'PASS' if record['validator_pass'] else 'FAIL'} ({len(val['failures'])} failures). "
          "Only STAGE_A_FINAL.json, written by the controller after this report, can state PASS.", "",
          f"Unique planned ids {len(planned)}; started {unique_started}; actual tries {tries}.", "",
          "## Failures", ""] + [f"- {f['code']} at {f['where']}: {f['detail']}" for f in val["failures"][:200]] + \
         ["", "## Native parity (recomputed from the committed arrays)", "",
          "| input | rel L2 max | logit max abs | argmax equal | pass |", "|---|---|---|---|---|"] + \
         [f"| {r['index']} | {r['rel_l2_max']:.3g} | {r['logit_max_abs']:.3g} | {r['argmax_equal']} | {r['pass']} |"
          for r in val["parity"]] + \
         ["", "## Stage B", "", "```", json.dumps({"prediction": b, "admission": admission}, indent=1), "```", "",
          "## Interpretation", "", "Not written here: the author inspects the figures and archives "
          "report/INTERPRETATION.md (author, date, sha256 of both figures) before any B admission.", ""]
    write_atomic(rep / "STAGE_A_REPORT.md", "\n".join(md).encode())
    return {"validator_pass": record["validator_pass"], "failures": len(val["failures"])}

"""T1 capture client — single-pass captures through POST /api/capture (PREREGISTRATION_T1_model.md §4).

Run with the upstream environment, which has the model tokenizer:

    PY=workspace_demo/upstream/jlens-qwen36/.venv/bin/python
    $PY workspace_demo/t1_access/capture.py info
    $PY workspace_demo/t1_access/capture.py parity --n 20 --qualifying
    $PY workspace_demo/t1_access/capture.py run --build <dir> --run-name <name> --split CAL --ledger-row A3
    $PY workspace_demo/t1_access/capture.py verify --run-name <name>

The server must carry patches/serve_tail_readout.patch and patches/serve_capture.patch (patch t1-capture-2).
Bulky outputs go to captures/ (gitignored); the reports the §15 manifest cites go to capture_logs/ (committed).
Revision 2 answers the Codex record reviews/2026-09-15_r084_capture_endpoint_codex_record.md (findings 1-5, 8).

Parity gate (§4, bit for bit, on N prompts in the packet layout of stimuli/packet.py):
  G1 empty edit list      edits: [] equals the plain capture (edits absent)
  G2 zero dose            steer, ablate and swap_delta at alpha 0 jointly at three layers (the exact identity path),
                          and steer alpha 0 at single layers 0, 62, 63 on the first five prompts
  G3 patch with own rows  patching the plain capture's own residuals equals the plain capture
  G4 repeat               the plain capture repeated after every other prompt equals itself
"Equal": identical residual bytes at every captured layer and readout position, identical full-logit bytes,
logsumexp, top-k ids and logits, requested logits and ranks. A QUALIFYING gate (--qualifying) needs at least 20
distinct prompts, every declared comparison per prompt (G1 1, G2 3, G3 1, G4 1) passing, committed client code, and
it binds the server's startup identity, the client file hashes and the sha256 of its evidence file. `run` admits
only a qualifying report whose evidence re-counts and whose identity matches the running server. Diagnostics
(reported, not gates): causality of a nonzero edit, dose linearity, norm matching, negative zeros at edit inputs.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
LOGS = HERE / "capture_logs"
CAPTURES = HERE / "captures"
PATCHES = DEMO / "patches"
UPSTREAM = DEMO / "upstream" / "jlens-qwen36"
sys.path.insert(0, str(HERE))

from stimuli.packet import ANSWER_SUFFIX, INSTRUCTION_A, build_ids, packet_text  # noqa: E402

JOINT_LAYERS = [23, 41, 57]
SINGLE_LAYERS = [0, 62, 63]
MIN_PROMPTS = 20
REQUIRED_PER_PROMPT = {"G1_empty": 1, "G2_lambda0": 3, "G3_patch_self": 1, "G4_repeat": 1}
CLIENT_FILES = ["t1_access/capture.py", "t1_access/stimuli/packet.py", "patches/serve_tail_readout.patch",
                "patches/serve_capture.patch", "patches/make_serve_capture_patch.py"]
SHARD = 1000
TOP_K = 1000


# -- server --------------------------------------------------------------------------------

class Server:
    def __init__(self, port: int = 8765, timeout: int = 900):
        self.base = f"http://127.0.0.1:{port}"
        self.timeout = timeout

    def _call(self, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{path}: HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from None

    def info(self) -> dict:
        return self._call("/api/capture/info")

    def capture(self, payload: dict) -> dict:
        return self._call("/api/capture", payload)

    def lens_vectors(self, layers: list[int], token_ids: list[int]) -> np.ndarray:
        r = self._call("/api/capture/lens_vectors", {"layers": layers, "token_ids": token_ids})
        buf = base64.b64decode(r["b64"])
        if hashlib.sha256(buf).hexdigest() != r["sha256"]:
            raise RuntimeError("lens_vectors: payload checksum mismatch")
        return np.frombuffer(buf, dtype=np.float32).reshape(r["shape"])


# -- decoding ------------------------------------------------------------------------------

def bf16_to_float32(u16: np.ndarray) -> np.ndarray:
    """Exact float32 values of bfloat16 bit patterns: a bfloat16 is the top 16 bits of the float32 of the same value
    (1 sign, 8 exponent bits with the same bias, 7 mantissa bits)."""
    return (u16.astype(np.uint32) << np.uint32(16)).view(np.float32)


def residuals_native(resp: dict) -> np.ndarray:
    """[L, P, D] residuals as returned: uint16 bit patterns for bfloat16, else the float dtype."""
    r = resp["residuals"]
    buf = base64.b64decode(r["b64"])
    if hashlib.sha256(buf).hexdigest() != r["sha256"]:
        raise RuntimeError("residuals: payload checksum mismatch")
    dt = {"bfloat16": np.uint16, "float16": np.float16, "float32": np.float32}[r["dtype"]]
    return np.frombuffer(buf, dtype=dt).reshape(r["shape"])


def residuals_float32(resp: dict) -> np.ndarray:
    a = residuals_native(resp)
    return bf16_to_float32(a) if resp["residuals"]["dtype"] == "bfloat16" else a.astype(np.float32)


def canonical_sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def digests(resp: dict) -> dict:
    """Everything a parity comparison compares, as hashes and exact values."""
    return {"residuals_sha256": resp["residuals"]["sha256"], "final_logits_sha256": resp["final_logits"]["sha256"],
            "logsumexp": resp["logsumexp"], "top_sha256": canonical_sha([resp["top_ids"], resp["top_logits"]]),
            "requested_sha256": canonical_sha(resp["requested"]),
            "startup_identity_sha256": resp["startup_identity_sha256"]}


# -- provenance ----------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str, repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def provenance(server: Server) -> dict:
    """The server's startup manifest (content hashes of what it loaded) plus the client's own files and git state."""
    info = server.info()
    repo = DEMO.parent
    return {
        "server": info,
        "startup_identity_sha256": info["identity_sha256"],
        "client_sha256": {rel: (sha256_file(DEMO / rel) if (DEMO / rel).exists() else "missing") for rel in CLIENT_FILES},
        "rsc_head": git("rev-parse", "HEAD", repo=repo),
        "rsc_dirty_paths": git("status", "--porcelain", "--", *[f"workspace_demo/{p}" for p in CLIENT_FILES],
                               "workspace_demo/t1_access/stimuli", repo=repo),
        "client_python": sys.version.split()[0],
        "client_numpy": np.__version__,
    }


def load_tokenizer(info: dict):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(info["model_snapshot"])


# -- development prompts for the parity gate (no stimulus-bank concept) -------------------

DEV_CLAUSES = {
    "chair": ["has four legs and a flat seat for one person",
              "usually stands at a desk or around a dining table",
              "often has a straight back to lean against while sitting",
              "can be folded, stacked or fitted with small wheels"],
    "shirt": ["is worn on the upper body and has buttons down the front",
              "comes with short or long sleeves and a collar",
              "is ironed before an office day or a formal dinner",
              "gets tucked into trousers or left hanging loose"],
    "lamp": ["gives light from a bulb under a fabric shade",
             "sits on a bedside table and is switched on at night",
             "plugs into a wall socket with a thin cord",
             "can be dimmed or angled toward a book"],
    "clock": ["has two hands that move around a round numbered face",
              "hangs on a kitchen wall and ticks quietly all day",
              "is wound up or runs on a small battery",
              "tells people when it is time to leave for work"],
    "umbrella": ["opens into a dome of fabric on thin metal ribs",
                 "is carried on rainy days and folded when dry",
                 "has a curved handle at the bottom of its shaft",
                 "keeps a person's head dry while walking outside"],
}
DEV_CARRIERS = [("Here are some notes a visitor wrote:", "Those were all the notes."),
                ("A friend described something in a few short lines:", "That is the whole description.")]


def dev_prompts(tok, n: int, seed: int = 20260915) -> list[dict]:
    rng = random.Random(seed)
    pool = [(c, s) for c, clauses in DEV_CLAUSES.items() for s in clauses]
    out = []
    for i in range(n):
        slots = [s for _, s in rng.sample(pool, 8)]
        carrier = DEV_CARRIERS[i % len(DEV_CARRIERS)]
        prefix = packet_text(INSTRUCTION_A, carrier[0], slots, carrier[1])
        suffix = None if i % 5 == 4 else ANSWER_SUFFIX
        built = build_ids(tok, prefix, suffix)
        built["index"] = i
        built["has_suffix"] = suffix is not None
        out.append(built)
    return out


def single_token(tok, text: str) -> int:
    ids = tok.encode(text, add_special_tokens=False)
    if len(ids) != 1:
        raise RuntimeError(f"{text!r} is not a single token: {ids}")
    return ids[0]


# -- parity --------------------------------------------------------------------------------

def compare(a: dict, b: dict) -> dict:
    da, db = digests(a), digests(b)
    return {k: da[k] == db[k] for k in ("residuals_sha256", "final_logits_sha256", "logsumexp", "top_sha256",
                                        "requested_sha256")}


def first_mismatch(a: dict, b: dict) -> dict | None:
    x, y = residuals_native(a), residuals_native(b)
    diff = np.any(x != y, axis=-1)
    if not diff.any():
        return None
    li, pi = map(int, np.argwhere(diff)[0])
    return {"layer": a["capture_layers"][li], "position": a["readout_positions"][pi],
            "n_entries": int(np.sum(x != y))}


def sanitize_edits(edits):
    if edits is None:
        return None
    out = []
    for e in edits:
        e = dict(e)
        if "vectors_b64" in e:
            e["vectors_sha256"] = hashlib.sha256(base64.b64decode(e.pop("vectors_b64"))).hexdigest()
        out.append(e)
    return out


def recount_evidence(evidence: Path) -> dict:
    """Re-derive a gate's verdict from its evidence file alone."""
    lines = [json.loads(x) for x in evidence.read_text().splitlines() if x.strip()]
    header = lines[0] if lines and "header" in lines[0] else {}
    rows = [x for x in lines if "gate" in x]
    prompts = sorted({r["prompt"] for r in rows})
    per_prompt_ok = True
    for p in prompts:
        for gate, need in REQUIRED_PER_PROMPT.items():
            got = [r for r in rows if r["prompt"] == p and r["gate"] == gate and r.get("required")]
            if len(got) < need or not all(r["pass"] for r in got):
                per_prompt_ok = False
    manifest_prompts = sorted(x["index"] for x in header.get("prompts", []))
    return {"n_prompts": len(prompts), "n_rows": len(rows), "all_pass": bool(rows) and all(r["pass"] for r in rows),
            "per_prompt_complete": per_prompt_ok, "prompt_manifest_matches": manifest_prompts == prompts,
            "startup_identity_sha256": header.get("startup_identity_sha256")}


def matching_parity(prov: dict, logs: Path = LOGS) -> tuple[str | None, list[str]]:
    """A qualifying PASS report bound to this server identity and client code whose evidence re-counts; else reasons."""
    reasons = []
    for path in sorted(logs.glob("parity_*.json"), reverse=True):
        rep = json.loads(path.read_text())
        why = []
        if rep.get("verdict") != "PASS" or not rep.get("qualifying"):
            why.append("not a qualifying PASS")
        if rep.get("startup_identity_sha256") != prov["startup_identity_sha256"]:
            why.append("server startup identity differs")
        if rep.get("client_sha256") != prov["client_sha256"]:
            why.append("client files differ")
        if rep.get("rsc_dirty_paths"):
            why.append("the gate ran with uncommitted client code")
        evidence = logs / str(rep.get("evidence", ""))
        if not evidence.is_file() or sha256_file(evidence) != rep.get("evidence_sha256"):
            why.append("evidence file missing or altered")
        else:
            rc = recount_evidence(evidence)
            if not (rc["n_prompts"] >= MIN_PROMPTS and rc["all_pass"] and rc["per_prompt_complete"]
                    and rc["prompt_manifest_matches"]
                    and rc["startup_identity_sha256"] == prov["startup_identity_sha256"]):
                why.append(f"evidence does not re-count to a qualifying gate: {rc}")
        if not why:
            return path.name, []
        reasons.append(f"{path.name}: {'; '.join(why)}")
    return None, reasons or ["no parity report"]


def parity(args) -> int:
    server = Server(args.port)
    prov = provenance(server)
    if args.qualifying and (args.n < MIN_PROMPTS or prov["rsc_dirty_paths"]):
        print(f"REFUSED: a qualifying gate needs --n >= {MIN_PROMPTS} and committed client code "
              f"(dirty: {prov['rsc_dirty_paths']!r})")
        return 2
    tok = load_tokenizer(prov["server"])
    prompts = dev_prompts(tok, args.n)
    t_src, t_tgt = single_token(tok, " chair"), single_token(tok, " lamp")
    ablate_ids = [t_src, single_token(tok, " shirt")]
    requested = [t_src, t_tgt]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    LOGS.mkdir(exist_ok=True)
    log_path = LOGS / f"parity_{stamp}.jsonl"
    gates = {g: [] for g in REQUIRED_PER_PROMPT}
    diag: list[dict] = []
    plain_by_prompt: dict[int, dict] = {}
    n_captures = 0
    t_start = time.time()
    for p in prompts:
        final = [len(p["ids"]) - 1] if p["has_suffix"] else []
        p["readout_positions"] = sorted(set([5, p["n_prefix"] // 2] + p["marker_positions"] + final))

    def cap(p: dict, edits) -> tuple[dict, dict]:
        nonlocal n_captures
        payload = {"input_ids": p["ids"], "readout_positions": p["readout_positions"],
                   "request_token_ids": requested, "top_k": TOP_K}
        if edits is not None:
            payload["edits"] = edits
        n_captures += 1
        resp = server.capture(payload)
        if resp["startup_identity_sha256"] != prov["startup_identity_sha256"]:
            raise RuntimeError("the server's startup identity changed during the gate")
        return resp, {k: v for k, v in payload.items() if k != "input_ids"} | {"edits": sanitize_edits(edits)}

    def record(gate: str, p: dict, label: str, ref: dict, got_req: tuple[dict, dict], required: bool = True) -> None:
        got, request = got_req
        c = compare(ref, got)
        ok = all(c.values())
        row = {"gate": gate, "prompt": p["index"], "label": label, "required": required, "pass": ok, "checks": c,
               "request": request, "ref": digests(ref), "got": digests(got), "edit_log": got["edit_log"],
               "mismatch": None if ok else first_mismatch(ref, got),
               "neg_zero_inputs": sum(e["neg_zero_inputs"] for e in got["edit_log"])}
        gates[gate].append(row)
        with open(log_path, "a") as f:
            f.write(json.dumps(row) + "\n")
        print(f"  {gate:<14} prompt {p['index']:>2} {label:<34} {'PASS' if ok else 'FAIL ' + json.dumps(row['mismatch'])}")

    with open(log_path, "w") as f:
        f.write(json.dumps({"header": "parity", "stamp": stamp, "n_prompts": args.n, "qualifying_requested": args.qualifying,
                            "startup_identity_sha256": prov["startup_identity_sha256"], "provenance": prov,
                            "joint_layers": JOINT_LAYERS, "single_layers": SINGLE_LAYERS,
                            "requested_ids": requested, "required_per_prompt": REQUIRED_PER_PROMPT,
                            "prompts": [{"index": p["index"], "ids": p["ids"], "marker_positions": p["marker_positions"],
                                         "readout_positions": p["readout_positions"], "has_suffix": p["has_suffix"]}
                                        for p in prompts]}) + "\n")

    for p in prompts:
        mpos = p["marker_positions"]
        plain, _ = cap(p, None)
        plain_by_prompt[p["index"]] = plain
        print(f"prompt {p['index']:>2}: {len(p['ids'])} tokens, marker {mpos}, "
              f"extend {plain['timing_s']['extend']:.2f} s, top1 {tok.decode([plain['top_ids'][0]])!r}")
        record("G1_empty", p, "edits=[]", plain, cap(p, []))
        for mode, extra_fields in [("steer", {"token_id": t_tgt}),
                                   ("ablate", {"ablate_token_ids": ablate_ids}),
                                   ("swap_delta", {"token_id": t_src, "target_id": t_tgt})]:
            edits = [{"mode": mode, "layer": l, "positions": mpos, "alpha": 0.0, **extra_fields} for l in JOINT_LAYERS]
            record("G2_lambda0", p, f"{mode} zero dose joint {JOINT_LAYERS}", plain, cap(p, edits))
        if p["index"] < 5:
            for l in SINGLE_LAYERS:
                edits = [{"mode": "steer", "layer": l, "positions": mpos, "alpha": 0.0, "token_id": t_tgt}]
                record("G2_lambda0", p, f"steer zero dose layer {l}", plain, cap(p, edits), required=False)
        native = residuals_native(plain)
        rp = plain["readout_positions"]
        edits = []
        for l in JOINT_LAYERS:
            rows = native[l, [rp.index(q) for q in mpos], :]
            edits.append({"mode": "patch", "layer": l, "positions": mpos,
                          "vectors_b64": base64.b64encode(np.ascontiguousarray(rows).tobytes()).decode(),
                          "vectors_dtype": plain["residuals"]["dtype"]})
        record("G3_patch_self", p, f"patch own rows {JOINT_LAYERS}", plain, cap(p, edits))
        if p["index"] < 5:
            diag.append(diagnostics(p, plain, lambda pp, ee: cap(pp, ee)[0], t_src, t_tgt))

    for p in prompts:
        record("G4_repeat", p, "plain again after all prompts", plain_by_prompt[p["index"]], cap(p, None))

    summary = {g: {"n": len(rows), "pass": sum(r["pass"] for r in rows)} for g, rows in gates.items()}
    ok = all(s["n"] > 0 and s["n"] == s["pass"] for s in summary.values())
    rc = recount_evidence(log_path)
    qualifying = bool(args.qualifying and ok and rc["n_prompts"] >= MIN_PROMPTS and rc["per_prompt_complete"]
                      and rc["prompt_manifest_matches"] and not prov["rsc_dirty_paths"])
    report = {"stamp": stamp, "verdict": "PASS" if ok else "FAIL", "qualifying": qualifying, "recount": rc,
              "min_prompts": MIN_PROMPTS, "required_per_prompt": REQUIRED_PER_PROMPT, "summary": summary,
              "n_prompts": args.n, "n_captures": n_captures, "wall_s": round(time.time() - t_start, 1),
              "neg_zero_inputs_total": sum(r["neg_zero_inputs"] for rows in gates.values() for r in rows),
              "startup_identity_sha256": prov["startup_identity_sha256"], "client_sha256": prov["client_sha256"],
              "rsc_head": prov["rsc_head"], "rsc_dirty_paths": prov["rsc_dirty_paths"],
              "evidence": log_path.name, "evidence_sha256": sha256_file(log_path),
              "diagnostics": diag, "provenance": prov}
    out = LOGS / f"parity_{stamp}.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("verdict", "qualifying", "summary", "n_captures", "wall_s",
                                             "neg_zero_inputs_total")}, indent=1))
    print(f"report: {out}")
    return 0 if ok else 1


def diagnostics(p: dict, plain: dict, cap, t_src: int, t_tgt: int) -> dict:
    """Reported, not gated: causality, dose linearity and norm matching of real edits."""
    mpos, layer = p["marker_positions"], 41
    rp, layers = plain["readout_positions"], plain["capture_layers"]
    base = residuals_native(plain)
    steer = cap(p, [{"mode": "steer", "layer": layer, "positions": mpos, "alpha": 8.0, "token_id": t_tgt}])
    s = residuals_native(steer)
    before = [i for i, q in enumerate(rp) if q < mpos[0]]
    li = layers.index(layer)
    out = {
        "prompt": p["index"],
        "steer_layers_below_unchanged": bool(np.array_equal(base[:li], s[:li])),
        "steer_earlier_positions_unchanged": bool(np.array_equal(base[:, before], s[:, before])),
        "steer_edit_layer_changed": bool(not np.array_equal(base[li], s[li])),
        "steer_v_norm": steer["edit_log"][0]["v_norm"],
        "steer_written_norm": steer["edit_log"][0]["written_delta_norm"],
    }
    full = cap(p, [{"mode": "swap_delta", "layer": layer, "positions": mpos, "alpha": 1.0,
                    "token_id": t_src, "target_id": t_tgt}])
    half = cap(p, [{"mode": "swap_delta", "layer": layer, "positions": mpos, "alpha": 0.5,
                    "token_id": t_src, "target_id": t_tgt}])
    wf = np.array(full["edit_log"][0]["written_delta_norm"])
    wh = np.array(half["edit_log"][0]["written_delta_norm"])
    out["swap_basis_condition"] = full["edit_log"][0]["basis_condition"]
    out["swap_written_norm_lambda1"] = wf.tolist()
    out["swap_half_over_full"] = (wh / np.where(wf > 0, wf, np.nan)).tolist()
    matched = cap(p, [{"mode": "swap_delta", "layer": layer, "positions": mpos, "token_id": t_src,
                       "target_id": t_tgt, "target_norms": [1.0] * len(mpos)}])
    out["norm_matched_requested"] = matched["edit_log"][0]["requested_norm"]
    out["norm_matched_written"] = matched["edit_log"][0]["written_delta_norm"]
    out["norm_matched_undefined"] = matched["edit_log"][0]["undefined"]
    return out


# -- runs ----------------------------------------------------------------------------------

def trial_prefix(row: dict, clues: dict, carriers: list, instr: dict) -> str:
    slots = [clues[c][int(i)] for c, i in (s.rsplit("#", 1) for s in row["slots"].split(";"))]
    opening, closing = carriers[int(row["carrier"])]
    return packet_text(instr["A"] if row["condition"] == "active" else instr["B"], opening, slots, closing)


def selected_rows(build: Path, args_like: dict) -> list[dict]:
    splits, sets, conds = (set(args_like[k].split(",")) for k in ("split", "set", "condition"))
    max_draw = args_like.get("max_draw")
    return [r for r in csv.DictReader(open(build / "manifest.csv"))
            if r["split"] in splits and r["set"] in sets and r["condition"] in conds
            and (max_draw is None or int(r["draw"]) < max_draw)]


OBSERVABLES = ("res", "top_ids", "top_logits", "answer_logits", "variant_logits", "answer_ranks", "variant_ranks")


def observables_sha(rows: dict, logsumexp: float) -> str:
    h = hashlib.sha256()
    for name in OBSERVABLES:
        h.update(np.ascontiguousarray(rows[name]).tobytes())
    h.update(np.float64(logsumexp).tobytes())
    return h.hexdigest()


def run(args) -> int:
    from stimuli.build_bank import load_clues

    build = Path(args.build).resolve()
    blog = json.loads((build / "build_log.json").read_text())
    draft = blog["status"].startswith("DRAFT")
    splits = set(args.split.split(","))
    stop = []
    if draft and not args.dev:
        stop.append("the build is DRAFT (clues not audited): only --dev runs may use it")
    if "CONF" in splits:
        if args.dev:
            stop.append("CONF is never captured in a development run")
        elif not args.freeze_v2:
            stop.append("CONF needs --freeze-v2 <commit> of the frozen pre-registration")
        else:
            head = git("show", f"{args.freeze_v2}:workspace_demo/t1_access/PREREGISTRATION_T1_model.md",
                       repo=DEMO.parent).splitlines()[:1]
            if not head or "DRAFT" in head[0]:
                stop.append(f"the pre-registration at {args.freeze_v2} is not frozen")
    if not args.ledger_row:
        stop.append("--ledger-row is required (rsc_t1_simulation_design.md §12: no row, no run)")
    server = Server(args.port)
    prov = provenance(server)
    parity_name, parity_reasons = matching_parity(prov)
    if parity_name is None and not args.dev:
        stop.append(f"no qualifying parity gate for this server and client: {parity_reasons[:3]}")
    if prov["rsc_dirty_paths"] and not args.dev:
        stop.append(f"uncommitted capture code or stimuli: {prov['rsc_dirty_paths']}")
    if not prov["server"]["ready"]:
        stop.append(f"server refuses captures: {prov['server']['refusal']}")
    if stop:
        for s in stop:
            print("REFUSED:", s)
        return 2

    stimuli = HERE / "stimuli"
    bank = json.loads((stimuli / "concepts.json").read_text())
    clues, _ = load_clues(Path(blog["clues_source"]))
    carriers = json.loads((stimuli / "carriers.json").read_text())["carriers"]
    instr = json.loads((stimuli / "instructions.json").read_text())
    tok = load_tokenizer(prov["server"])
    tok_sha = prov["server"]["identity"]["model_files_sha256"].get("tokenizer.json")
    if tok_sha != blog["inputs_sha256"]["tokenizer.json"]:
        print("REFUSED: the server's tokenizer differs from the one the bank was built with")
        return 2
    # §6.3 (draft amendment 15 Sept): the answer set is the 128 frozen ids (chance 1/128); the logits and
    # open-vocabulary ranks of every concept's other single-token variants are stored for descriptive readings.
    answer_ids = sorted(c["token_id"] for c in bank["concepts"])
    variant_ids = sorted({v["ids"][0] for c in bank["concepts"] for v in c["variants"].values()
                          if v["single_token"]} - set(answer_ids))
    selection = {"split": args.split, "set": args.set, "condition": args.condition, "max_draw": args.max_draw}
    rows = selected_rows(build, selection)

    out = CAPTURES / args.run_name
    out.mkdir(parents=True, exist_ok=True)
    identity = {"startup_identity_sha256": prov["startup_identity_sha256"], "client_sha256": prov["client_sha256"],
                "manifest_sha256": sha256_file(build / "manifest.csv"), "selection": selection,
                "answer_ids": answer_ids, "variant_ids": variant_ids, "chance": 1 / len(answer_ids), "top_k": TOP_K,
                "shard": SHARD, "observables": list(OBSERVABLES)}
    header_path = out / "run_header.json"
    if header_path.exists():
        old = json.loads(header_path.read_text())
        if old["identity"] != identity:
            print("REFUSED: this run directory was captured under a different identity; use a new --run-name")
            return 2
    else:
        header_path.write_text(json.dumps({"identity": identity, "provenance": prov, "args": vars(args),
                                           "build": str(build), "build_log": blog, "parity_report": parity_name,
                                           "dev": args.dev, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    trials_path = out / "trials.jsonl"
    done_records = [json.loads(x) for x in trials_path.read_text().splitlines() if x.strip()] if trials_path.exists() else []
    done = {r["trial_id"] for r in done_records}
    todo = [r for r in rows if r["trial_id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(rows)} trials selected, {len(done)} already captured, {len(todo)} to capture -> {out}")

    L, D, A, V = prov["server"]["n_layers"], prov["server"]["d_model"], len(answer_ids), len(variant_ids)
    specs = {"res": (np.uint16, (SHARD, L, D)), "top_ids": (np.int32, (SHARD, TOP_K)),
             "top_logits": (np.float32, (SHARD, TOP_K)), "answer_logits": (np.float32, (SHARD, A)),
             "variant_logits": (np.float32, (SHARD, V)), "answer_ranks": (np.int32, (SHARD, A)),
             "variant_ranks": (np.int32, (SHARD, V))}
    maps: dict[int, dict] = {}

    def shard(s: int) -> dict:
        if s not in maps:
            maps[s] = {}
            for name, (dt, shape) in specs.items():
                p = out / f"{name}_{s:05d}.npy"
                maps[s][name] = (np.load(p, mmap_mode="r+") if p.exists()
                                 else np.lib.format.open_memmap(p, mode="w+", dtype=dt, shape=shape))
        return maps[s]

    n_done, times = len(done_records), []
    with open(trials_path, "a") as tf:
        for row in todo:
            suffix = ANSWER_SUFFIX if row["condition"] == "active" else None
            built = build_ids(tok, trial_prefix(row, clues, carriers, instr), suffix)
            if (hashlib.sha256(json.dumps(built["ids"]).encode()).hexdigest() != row["ids_sha256"]
                    or built["readout_position"] != int(row["readout_position"])):
                print(f"STOP: ids of {row['trial_id']} differ from the manifest")
                return 1
            try:
                resp = server.capture({"input_ids": built["ids"], "readout_positions": [built["readout_position"]],
                                       "request_token_ids": answer_ids + variant_ids, "top_k": TOP_K})
            except RuntimeError as exc:
                with open(out / "failures.jsonl", "a") as ff:
                    ff.write(json.dumps({"trial_id": row["trial_id"], "error": str(exc),
                                         "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
                print(f"STOP: capture of {row['trial_id']} failed: {exc}")
                return 1
            if resp["startup_identity_sha256"] != prov["startup_identity_sha256"]:
                print("STOP: the server's startup identity changed during the run")
                return 1
            res = residuals_native(resp)
            if resp["residuals"]["dtype"] != "bfloat16" or res.shape != (L, 1, D):
                print(f"STOP: unexpected residual format {resp['residuals']['dtype']} {res.shape}")
                return 1
            s, i = divmod(n_done, SHARD)
            m = shard(s)
            logits = [x["logit"] for x in resp["requested"]]
            ranks = [x["rank"] for x in resp["requested"]]
            m["res"][i] = res[:, 0, :]
            m["top_ids"][i] = resp["top_ids"]
            m["top_logits"][i] = resp["top_logits"]
            m["answer_logits"][i], m["variant_logits"][i] = logits[:A], logits[A:]
            m["answer_ranks"][i], m["variant_ranks"][i] = ranks[:A], ranks[A:]
            for arr in m.values():
                arr.flush()
            stored = {name: np.asarray(m[name][i]) for name in OBSERVABLES}
            tf.write(json.dumps({
                "trial_id": row["trial_id"], "shard": s, "index": i, "ids": built["ids"],
                "readout_position": built["readout_position"], "logsumexp": resp["logsumexp"],
                "final_logits_sha256": resp["final_logits"]["sha256"],
                "residuals_sha256": hashlib.sha256(np.ascontiguousarray(stored["res"]).tobytes()).hexdigest(),
                "observables_sha256": observables_sha(stored, resp["logsumexp"]),
                "extend_s": resp["timing_s"]["extend"], "total_s": resp["timing_s"]["total"],
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            tf.flush()
            n_done += 1
            times.append(resp["timing_s"]["total"])
            if len(times) % 50 == 0 or len(times) == len(todo):
                med = statistics.median(times)
                left = len(rows) - n_done
                print(f"  {n_done}/{len(rows)} captured; median {med:.2f} s/capture server-side; "
                      f"~{left * med / 3600:.1f} h left for this selection", flush=True)
    return 0


def verify(args) -> int:
    """Re-hash every stored observable, check ids, locations, finiteness and coverage of the declared selection."""
    out = CAPTURES / args.run_name
    header = json.loads((out / "run_header.json").read_text())
    ident = header["identity"]
    expected = {r["trial_id"] for r in selected_rows(Path(header["build"]), ident["selection"])}
    vocab = header["provenance"]["server"]["vocab_rows"]
    problems, seen, locs = [], set(), set()
    cache: dict[int, dict] = {}
    records = [json.loads(x) for x in (out / "trials.jsonl").read_text().splitlines() if x.strip()]
    for n, t in enumerate(records):
        if t["trial_id"] in seen:
            problems.append(f"duplicate trial {t['trial_id']}")
        seen.add(t["trial_id"])
        loc = (t["shard"], t["index"])
        if loc in locs or loc != divmod(n, ident["shard"]):
            problems.append(f"storage location {loc} of {t['trial_id']} is duplicated or out of sequence")
        locs.add(loc)
        if t["shard"] not in cache:
            cache[t["shard"]] = {name: np.load(out / f"{name}_{t['shard']:05d}.npy", mmap_mode="r") for name in OBSERVABLES}
        rows = {name: np.asarray(cache[t["shard"]][name][t["index"]]) for name in OBSERVABLES}
        if observables_sha(rows, t["logsumexp"]) != t.get("observables_sha256"):
            problems.append(f"observables of {t['trial_id']} do not match their record")
        floats = [rows["top_logits"], rows["answer_logits"], rows["variant_logits"]]
        ranks = np.concatenate([rows["answer_ranks"], rows["variant_ranks"]])
        if not all(np.all(np.isfinite(x)) for x in floats) or not np.isfinite(t["logsumexp"]):
            problems.append(f"nonfinite logits in {t['trial_id']}")
        if ranks.size and (ranks.min() < 1 or ranks.max() > vocab):
            problems.append(f"ranks out of range in {t['trial_id']}")
    missing, extra = sorted(expected - seen), sorted(seen - expected)
    if extra:
        problems.append(f"{len(extra)} records outside the declared selection, e.g. {extra[:3]}")
    report = {"run": args.run_name, "n_records": len(records), "n_expected": len(expected), "n_missing": len(missing),
              "complete": not missing and not extra, "problems": problems[:50], "n_problems": len(problems),
              "verdict": "PASS" if not problems else "FAIL"}
    print(json.dumps(report, indent=1))
    return 0 if not problems else 1


def info(args) -> int:
    prov = provenance(Server(args.port))
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"server_info_{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps(prov, indent=1))
    print(json.dumps({k: prov[k] for k in ("startup_identity_sha256", "client_sha256", "rsc_head", "rsc_dirty_paths")},
                     indent=1))
    print(f"written: {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    pp = sub.add_parser("parity")
    pp.add_argument("--n", type=int, default=MIN_PROMPTS)
    pp.add_argument("--qualifying", action="store_true", help="a gate that `run` may admit (needs >= 20 prompts, committed code)")
    rp = sub.add_parser("run", help="capture trials from a built bank's manifest")
    rp.add_argument("--build", required=True, help="directory with manifest.csv and build_log.json")
    rp.add_argument("--run-name", required=True)
    rp.add_argument("--split", required=True, help="comma list of CAL, PILOT, CONF")
    rp.add_argument("--set", default="primary", help="comma list of primary, C1, C2, single")
    rp.add_argument("--condition", default="active,noreport")
    rp.add_argument("--max-draw", type=int, default=None, help="only draws below this index (CONF D = 4: 4)")
    rp.add_argument("--limit", type=int, default=None, help="benchmark slice: capture at most this many")
    rp.add_argument("--ledger-row", default=None, help="the §12 ledger row this run belongs to, e.g. A3")
    rp.add_argument("--freeze-v2", default=None, help="commit of the frozen pre-registration (CONF only)")
    rp.add_argument("--dev", action="store_true", help="development run: DRAFT builds allowed, CONF refused")
    vp = sub.add_parser("verify", help="verify a run's stored observables and completeness")
    vp.add_argument("--run-name", required=True)
    args = ap.parse_args()
    return {"info": info, "parity": parity, "run": run, "verify": verify}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())

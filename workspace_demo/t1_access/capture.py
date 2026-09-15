"""T1 capture client — single-pass captures through POST /api/capture (PREREGISTRATION_T1_model.md §4).

Run with the upstream environment, which has the model tokenizer:

    PY=workspace_demo/upstream/jlens-qwen36/.venv/bin/python
    $PY workspace_demo/t1_access/capture.py info
    $PY workspace_demo/t1_access/capture.py parity --n 20

The server must carry patches/serve_tail_readout.patch and patches/serve_capture.patch.
Bulky outputs go to captures/ (gitignored); the reports the §15 manifest cites go to
capture_logs/ (committed).

Parity gate (§4, all bit for bit, on N prompts in the packet layout of stimuli/packet.py):
  G1 empty edit list      edits: [] equals the plain capture (edits absent)
  G2 λ = 0                steer, ablate and swap_delta at three layers jointly, and steer
                          at single layers 0, 62, 63, each equal the plain capture
  G3 patch with own rows  patching the plain capture's own residuals equals the plain capture
  G4 repeat               the plain capture repeated after every other prompt equals itself
"Equal" means identical residual bytes at every captured layer and readout position,
identical final-logit bytes, logsumexp, top-k ids and logits, and requested logits.
Diagnostics (reported, not gates): causality of a λ ≠ 0 edit (earlier layers and positions
unchanged), linearity of the swap_delta dose, norm matching, exact negative zeros at edit
positions (h + 0·Δ turns -0.0 into +0.0).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
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
    """Exact float32 values of bfloat16 bit patterns: a bfloat16 is the top 16 bits of the
    float32 of the same value (1 sign, 8 exponent bits with the same bias, 7 mantissa bits)."""
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


# -- provenance ----------------------------------------------------------------------------

def sha256_file(path: Path, cache: dict) -> str:
    st = path.stat()
    key = f"{path.resolve()}|{st.st_size}|{st.st_mtime_ns}"
    if key not in cache:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 24), b""):
                h.update(chunk)
        cache[key] = h.hexdigest()
    return cache[key]


def git(*args: str, repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def provenance(server: Server) -> dict:
    """Server identity plus sha256 of the model files, lens, tokenizer, patches and client code."""
    info = server.info()
    cache_path = CAPTURES / "sha256_cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    snap = Path(info["model_snapshot"])
    files = sorted(snap.glob("*.safetensors")) + [snap / "tokenizer.json", snap / "tokenizer_config.json",
                                                  snap / "config.json"]
    hashes = {p.name: sha256_file(p, cache) for p in files}
    if info.get("lens_path"):
        lens = Path(info["lens_path"])
        hashes["lens:" + lens.name] = sha256_file(lens, cache)
    for p in [PATCHES / "serve_tail_readout.patch", PATCHES / "serve_capture.patch",
              HERE / "capture.py", HERE / "stimuli" / "packet.py"]:
        hashes[str(p.relative_to(DEMO))] = sha256_file(p, cache) if p.exists() else "missing"
    CAPTURES.mkdir(exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=1))
    repo = DEMO.parent
    return {
        "server": info,
        "sha256": hashes,
        "rsc_head": git("rev-parse", "HEAD", repo=repo),
        "rsc_dirty_paths": git("status", "--porcelain", "--", "workspace_demo/t1_access/capture.py",
                               "workspace_demo/t1_access/stimuli", "workspace_demo/patches", repo=repo),
        "upstream_head": git("rev-parse", "HEAD", repo=UPSTREAM),
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
    return {
        "residuals": a["residuals"]["sha256"] == b["residuals"]["sha256"],
        "final_logits": a["final_logits"]["sha256"] == b["final_logits"]["sha256"],
        "logsumexp": a["logsumexp"] == b["logsumexp"],
        "top_k": a["top_ids"] == b["top_ids"] and a["top_logits"] == b["top_logits"],
        "requested": a["requested"] == b["requested"],
    }


def first_mismatch(a: dict, b: dict) -> dict | None:
    """Where two residual stacks first differ: (layer, position) and the count of differing entries."""
    x, y = residuals_native(a), residuals_native(b)
    diff = np.any(x != y, axis=-1)
    if not diff.any():
        return None
    li, pi = map(int, np.argwhere(diff)[0])
    return {"layer": a["capture_layers"][li], "position": a["readout_positions"][pi],
            "n_entries": int(np.sum(x != y))}


def parity(args) -> int:
    server = Server(args.port)
    prov = provenance(server)
    tok = load_tokenizer(prov["server"])
    prompts = dev_prompts(tok, args.n)
    t_src, t_tgt = single_token(tok, " chair"), single_token(tok, " lamp")
    ablate_ids = [t_src, single_token(tok, " shirt")]
    requested = [t_src, t_tgt]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    LOGS.mkdir(exist_ok=True)
    log_path = LOGS / f"parity_{stamp}.jsonl"
    gates = {"G1_empty": [], "G2_lambda0": [], "G3_patch_self": [], "G4_repeat": []}
    diag: list[dict] = []
    plain_by_prompt: dict[int, dict] = {}
    n_captures = 0
    t_start = time.time()

    def cap(p: dict, edits) -> dict:
        nonlocal n_captures
        payload = {"input_ids": p["ids"], "readout_positions": p["readout_positions"],
                   "request_token_ids": requested, "top_k": 1000}
        if edits is not None:
            payload["edits"] = edits
        n_captures += 1
        return server.capture(payload)

    def record(gate: str, p: dict, label: str, ref: dict, got: dict) -> None:
        c = compare(ref, got)
        ok = all(c.values())
        row = {"gate": gate, "prompt": p["index"], "label": label, "pass": ok, "checks": c,
               "mismatch": None if ok else first_mismatch(ref, got),
               "neg_zero_inputs": sum(e["neg_zero_inputs"] for e in got["edit_log"])}
        gates[gate].append(row)
        with open(log_path, "a") as f:
            f.write(json.dumps(row) + "\n")
        print(f"  {gate:<14} prompt {p['index']:>2} {label:<34} {'PASS' if ok else 'FAIL ' + json.dumps(row['mismatch'])}")

    with open(log_path, "w") as f:
        f.write(json.dumps({"header": "parity", "stamp": stamp, "n_prompts": args.n, "provenance": prov,
                            "joint_layers": JOINT_LAYERS, "single_layers": SINGLE_LAYERS}) + "\n")

    for p in prompts:
        extra = [5, p["n_prefix"] // 2]
        final = [len(p["ids"]) - 1] if p["has_suffix"] else []
        p["readout_positions"] = sorted(set(extra + p["marker_positions"] + final))
        mpos = p["marker_positions"]
        plain = cap(p, None)
        plain_by_prompt[p["index"]] = plain
        print(f"prompt {p['index']:>2}: {len(p['ids'])} tokens, marker {mpos}, "
              f"extend {plain['timing_s']['extend']:.2f} s, top1 {tok.decode([plain['top_ids'][0]])!r}")

        record("G1_empty", p, "edits=[]", plain, cap(p, []))

        for mode, extra_fields in [("steer", {"token_id": t_tgt}),
                                   ("ablate", {"ablate_token_ids": ablate_ids}),
                                   ("swap_delta", {"token_id": t_src, "target_id": t_tgt})]:
            edits = [{"mode": mode, "layer": l, "positions": mpos, "alpha": 0.0, **extra_fields}
                     for l in JOINT_LAYERS]
            record("G2_lambda0", p, f"{mode} λ=0 joint {JOINT_LAYERS}", plain, cap(p, edits))
        if p["index"] < 5:
            for l in SINGLE_LAYERS:
                edits = [{"mode": "steer", "layer": l, "positions": mpos, "alpha": 0.0, "token_id": t_tgt}]
                record("G2_lambda0", p, f"steer λ=0 layer {l}", plain, cap(p, edits))

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
            diag.append(diagnostics(p, plain, cap, t_src, t_tgt))

    for p in prompts:
        record("G4_repeat", p, "plain again after all prompts", plain_by_prompt[p["index"]], cap(p, None))

    summary = {g: {"n": len(rows), "pass": sum(r["pass"] for r in rows)} for g, rows in gates.items()}
    ok = all(s["n"] > 0 and s["n"] == s["pass"] for s in summary.values())
    report = {"stamp": stamp, "verdict": "PASS" if ok else "FAIL", "summary": summary,
              "n_prompts": args.n, "n_captures": n_captures, "wall_s": round(time.time() - t_start, 1),
              "neg_zero_inputs_total": sum(r["neg_zero_inputs"] for rows in gates.values() for r in rows),
              "diagnostics": diag, "log": log_path.name, "provenance": prov}
    out = LOGS / f"parity_{stamp}.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("verdict", "summary", "n_captures", "wall_s",
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
    out["swap_written_norm_lambda1"] = wf.tolist()
    out["swap_half_over_full"] = (wh / np.where(wf > 0, wf, np.nan)).tolist()
    matched = cap(p, [{"mode": "swap_delta", "layer": layer, "positions": mpos, "token_id": t_src,
                       "target_id": t_tgt, "target_norms": [1.0] * len(mpos)}])
    out["norm_matched_written"] = matched["edit_log"][0]["written_delta_norm"]
    out["norm_matched_undefined"] = matched["edit_log"][0]["undefined"]
    return out


# -- runs ----------------------------------------------------------------------------------

SHARD = 1000
TOP_K = 1000
PARITY_KEYS_SERVER = ["capture_endpoint_sha256", "serve_sha256", "model_snapshot", "lens_path", "hw_model",
                      "mlx", "mlx_lm", "hidden_dtype"]


def matching_parity(prov: dict, require_clean: bool) -> str | None:
    """Name of a PASS parity report with the same server, weights, patches and client code, else None."""
    for path in sorted(LOGS.glob("parity_*.json"), reverse=True):
        rep = json.loads(path.read_text())
        p = rep.get("provenance", {})
        if rep.get("verdict") != "PASS":
            continue
        if any(p.get("server", {}).get(k) != prov["server"].get(k) for k in PARITY_KEYS_SERVER):
            continue
        if p.get("sha256") != prov["sha256"]:
            continue
        if require_clean and p.get("rsc_dirty_paths"):
            continue
        return path.name
    return None


def trial_prefix(row: dict, clues: dict, carriers: list, instr: dict) -> str:
    slots = [clues[c][int(i)] for c, i in (s.rsplit("#", 1) for s in row["slots"].split(";"))]
    opening, closing = carriers[int(row["carrier"])]
    return packet_text(instr["A"] if row["condition"] == "active" else instr["B"], opening, slots, closing)


def run(args) -> int:
    import csv

    from stimuli.build_bank import load_clues

    build = Path(args.build).resolve()
    blog = json.loads((build / "build_log.json").read_text())
    draft = blog["status"].startswith("DRAFT")
    splits, sets, conds = (set(x.split(",")) for x in (args.split, args.set, args.condition))
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
    parity = matching_parity(prov, require_clean=not args.dev)
    if parity is None and not args.dev:
        stop.append("no PASS parity report matches this server, weights, patches and committed client code")
    if prov["rsc_dirty_paths"] and not args.dev:
        stop.append(f"uncommitted capture code or stimuli: {prov['rsc_dirty_paths']}")
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
    tok_sha = hashlib.sha256((Path(prov["server"]["model_snapshot"]) / "tokenizer.json").read_bytes()).hexdigest()
    if tok_sha != blog["inputs_sha256"]["tokenizer.json"]:
        print("REFUSED: the server's tokenizer differs from the one the bank was built with")
        return 2
    # §6.3 (draft amendment 15 Sept): the answer set is the 128 frozen ids (chance 1/128); the logits of every
    # concept's other single-token variants are also stored, for a descriptive variant-maximum reading only.
    answer_ids = sorted(c["token_id"] for c in bank["concepts"])
    variant_ids = sorted({v["ids"][0] for c in bank["concepts"] for v in c["variants"].values()
                          if v["single_token"]} - set(answer_ids))
    rows = [r for r in csv.DictReader(open(build / "manifest.csv"))
            if r["split"] in splits and r["set"] in sets and r["condition"] in conds
            and (args.max_draw is None or int(r["draw"]) < args.max_draw)]

    out = CAPTURES / args.run_name
    out.mkdir(parents=True, exist_ok=True)
    identity = {"server": {k: prov["server"][k] for k in PARITY_KEYS_SERVER}, "sha256": prov["sha256"],
                "manifest_sha256": hashlib.sha256((build / "manifest.csv").read_bytes()).hexdigest(),
                "answer_ids": answer_ids, "variant_ids": variant_ids, "chance": 1 / len(answer_ids),
                "top_k": TOP_K}
    header_path = out / "run_header.json"
    if header_path.exists():
        old = json.loads(header_path.read_text())
        if old["identity"] != identity:
            print("REFUSED: this run directory was captured under a different identity; use a new --run-name")
            return 2
    else:
        header_path.write_text(json.dumps({"identity": identity, "provenance": prov, "args": vars(args),
                                           "build": str(build), "build_log": blog, "parity_report": parity,
                                           "started": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    trials_path = out / "trials.jsonl"
    done = set()
    if trials_path.exists():
        done = {json.loads(line)["trial_id"] for line in trials_path.read_text().splitlines() if line.strip()}
    todo = [r for r in rows if r["trial_id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(rows)} trials selected, {len(done)} already captured, {len(todo)} to capture -> {out}")

    L, D, A, V = prov["server"]["n_layers"], prov["server"]["d_model"], len(answer_ids), len(variant_ids)
    maps: dict[int, dict] = {}

    def shard(s: int) -> dict:
        if s not in maps:
            specs = {"res": (np.uint16, (SHARD, L, D)), "top_ids": (np.int32, (SHARD, TOP_K)),
                     "top_logits": (np.float32, (SHARD, TOP_K)), "answer_logits": (np.float32, (SHARD, A)),
                     "variant_logits": (np.float32, (SHARD, V))}
            maps[s] = {}
            for name, (dt, shape) in specs.items():
                p = out / f"{name}_{s:05d}.npy"
                maps[s][name] = (np.load(p, mmap_mode="r+") if p.exists()
                                 else np.lib.format.open_memmap(p, mode="w+", dtype=dt, shape=shape))
        return maps[s]

    n_done, times = len(done), []
    with open(trials_path, "a") as tf:
        for row in todo:
            suffix = ANSWER_SUFFIX if row["condition"] == "active" else None
            built = build_ids(tok, trial_prefix(row, clues, carriers, instr), suffix)
            if (hashlib.sha256(json.dumps(built["ids"]).encode()).hexdigest() != row["ids_sha256"]
                    or built["readout_position"] != int(row["readout_position"])):
                print(f"STOP: ids of {row['trial_id']} differ from the manifest")
                return 1
            resp = server.capture({"input_ids": built["ids"], "readout_positions": [built["readout_position"]],
                                   "request_token_ids": answer_ids + variant_ids, "top_k": TOP_K})
            res = residuals_native(resp)
            if resp["residuals"]["dtype"] != "bfloat16" or res.shape != (L, 1, D):
                print(f"STOP: unexpected residual format {resp['residuals']['dtype']} {res.shape}")
                return 1
            s, i = divmod(n_done, SHARD)
            m = shard(s)
            m["res"][i] = res[:, 0, :]
            m["top_ids"][i] = resp["top_ids"]
            m["top_logits"][i] = resp["top_logits"]
            logits = [x["logit"] for x in resp["requested"]]
            m["answer_logits"][i] = logits[:A]
            m["variant_logits"][i] = logits[A:]
            for arr in m.values():
                arr.flush()
            tf.write(json.dumps({
                "trial_id": row["trial_id"], "shard": s, "index": i, "ids": built["ids"],
                "readout_position": built["readout_position"], "logsumexp": resp["logsumexp"],
                "final_logits_sha256": resp["final_logits"]["sha256"],
                "residuals_sha256": hashlib.sha256(np.ascontiguousarray(res[:, 0, :]).tobytes()).hexdigest(),
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
    """Re-hash every stored residual row against its trial record."""
    out = CAPTURES / args.run_name
    bad = n = 0
    cache: dict[int, np.ndarray] = {}
    for line in (out / "trials.jsonl").read_text().splitlines():
        t = json.loads(line)
        if t["shard"] not in cache:
            cache[t["shard"]] = np.load(out / f"res_{t['shard']:05d}.npy", mmap_mode="r")
        row = np.ascontiguousarray(cache[t["shard"]][t["index"]])
        n += 1
        if hashlib.sha256(row.tobytes()).hexdigest() != t["residuals_sha256"]:
            bad += 1
            print("MISMATCH", t["trial_id"])
    print(f"{'PASS' if not bad else 'FAIL'}: {n - bad}/{n} residual rows match their records")
    return 0 if not bad else 1


def info(args) -> int:
    prov = provenance(Server(args.port))
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"server_info_{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps(prov, indent=1))
    print(json.dumps(prov, indent=1))
    print(f"written: {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    pp = sub.add_parser("parity")
    pp.add_argument("--n", type=int, default=20)
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
    vp = sub.add_parser("verify", help="re-hash a run's stored residuals")
    vp.add_argument("--run-name", required=True)
    args = ap.parse_args()
    return {"info": info, "parity": parity, "run": run, "verify": verify}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())

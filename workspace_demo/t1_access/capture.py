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
    args = ap.parse_args()
    return {"info": info, "parity": parity}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())

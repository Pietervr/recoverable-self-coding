"""Synthetic fixture for the AI-reader mechanism tests: a small labelled-synthetic set (N_ITEMS items x 2 views), tiny
generated images, a delivery receipt, a key and a fake-codex plan. No model, no development or qualification image.

As a script (the hard-kill driver): airq_fixture.py <root>   -> runs the executor once in fixture mode and prints
the result; AIRQ_CRASH=<point>:<n> in its environment makes it os._exit(77) at that point.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PHOTO = TESTS.parent
sys.path.insert(0, str(PHOTO))
import ai_reader_exec as X  # noqa: E402
import ai_reader_runtime as R  # noqa: E402

N_ITEMS = 3
READER = {"model": "gpt-6.1-sol", "reasoning_effort": "medium", "cli_version": "codex-cli 0.159.3"}
PROMPT = "fixture prompt"
DIGEST = "f" * 64


def png(v: int) -> bytes:
    raw = b"".join(b"\x00" + bytes([v]) * 8 for _ in range(8))

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 0, 0, 0, 0)) + \
        ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


def build(root: Path, plan: dict | None = None, n_items: int = N_ITEMS) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir(exist_ok=True)
    (root / "attempts").mkdir(exist_ok=True)
    requests, items = [], {}
    for i in range(n_items):
        item = f"it{i}"
        items[item] = {"concept": f"thing{i}", "sense": "a synthetic thing", "synset": "", "aliases": ["thing"],
                       "human": {"recognizability": 0.9, "n_ratings": 10}, "stratum": i % 3, "easy": True}
        for j, view in enumerate(("colour", "gray")):
            rq = f"rq{i}{view[0]}"
            data = png(16 * i + j + 1)
            (root / "images" / f"{rq}.png").write_bytes(data)
            requests.append({"request": rq, "item": item, "view": view, "file": f"{rq}.png",
                             "sha256": hashlib.sha256(data).hexdigest()})
    order = [r["request"] for r in requests if r["view"] == "colour"] + \
            [r["request"] for r in requests if r["view"] == "gray"]
    sset = {"requests": requests, "delivery_order": order, "reader": READER, "prompt": PROMPT,
            "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest()}
    codex = [sys.executable, str(TESTS / "fake_codex.py")]
    adir = root / "attempts" / "probe" / "a"
    img = R.prepare(adir, (root / "images" / requests[0]["file"]).read_bytes(), requests[0]["file"])
    rc = R.prompt_input(codex, READER, adir, img, PROMPT, sandbox=False)
    delivery = {"instructions_sha256": rc["instructions_sha256"],
                "requests": {r["request"]: {"image_sha256": r["sha256"]} for r in requests}}
    (root / "fake_plan.json").write_text(json.dumps(plan or {}))
    fx = {"codex": codex, "images": root / "images", "job": root / "job", "raw": root / "raw.jsonl",
          "attempts": root / "attempts", "sset": sset, "delivery": delivery, "package": {"package_digest": DIGEST}}
    (root / "fixture.json").write_text(json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in fx.items()}))
    return {"fixture": fx, "key": {"items": items}, "sset": sset}


def load(root: Path) -> dict:
    d = json.loads((root / "fixture.json").read_text())
    for k in ("images", "job", "raw", "attempts"):
        d[k] = Path(d[k])
    return d


def dispatches(root: Path) -> list[dict]:
    p = root / "dispatch_log.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


if __name__ == "__main__":
    print(json.dumps(X.run(fixture=load(Path(sys.argv[1]))), default=str))

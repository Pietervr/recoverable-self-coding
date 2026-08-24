"""P0 exit test — first light through the J-lens on local hardware.

Against a running jlens-qwen36 server (default port 8765):
  1. verify the lens is the Neuronpedia n=1000 fit (the port's CLAUDE.md gate);
  2. run a two-hop prompt whose unspoken intermediate is known
     (the paper's spider example) through /api/slice;
  3. report where the intermediate appears in the readout
     (rank within top-n, per layer x position) and the greedy answer
     via /api/generate.

/api/slice response schema (serve.py):
  {"layers": [..], "seq_len": N, "token_strs": [..], "top_n": k,
   "cells": {layer: {"top_ids": [[id]*k]*N, "top_tokens": [[str]*k]*N,
                     "top_scores": [[f]*k]*N}}}

Pass criterion: the intermediate reaches the top-n readout at intermediate
layers at some prompt position, and the greedy answer is correct.

Run:  python3 p0_first_light.py [--port 8765] [--top-n 10]
"""

import argparse
import json
import urllib.request

PROMPT = "Fact: The number of legs on the animal that spins webs is"
INTERMEDIATE = "spider"
EXPECT_ANSWER = "8"


def post(port: int, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)


def get(port: int, path: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=60) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--top-n", type=int, default=10)
    args = ap.parse_args()

    # 1. lens gate (the port's CLAUDE.md: refuse a smaller lens silently)
    lens = get(args.port, "/api/lens")
    n = lens.get("n_prompts")
    print("lens info:", json.dumps(lens)[:300])
    if n != 1000:
        print("FAIL: not the n=1000 Neuronpedia lens — refusing to interpret readouts")
        return 1

    # 2. readout
    sl = post(args.port, "/api/slice", {"prompt": PROMPT, "top_n": args.top_n})
    layers = sl["layers"]
    toks = sl["token_strs"]
    cells = sl["cells"]
    print(f"seq_len={sl['seq_len']} layers={len(layers)} ({layers[0]}..{layers[-1]})")

    hits = []  # (layer, pos, rank)
    for layer in layers:
        cell = cells[str(layer)] if str(layer) in cells else cells[layer]
        for pos, top in enumerate(cell["top_tokens"]):
            for rank, t in enumerate(top):
                if t.strip().lower() == INTERMEDIATE:
                    hits.append((int(layer), pos, rank + 1))

    print(f"'{INTERMEDIATE}' hits in top-{args.top_n}: {len(hits)}")
    for layer, pos, rank in hits[:15]:
        print(f"   L{layer:>2}  pos {pos:>2} ({toks[pos]!r})  rank {rank}")

    # 3. answer
    gen = post(args.port, "/api/generate", {"prompt": PROMPT, "max_tokens": 4, "temp": 0.0})
    text = gen.get("text", "")
    print(f"greedy continuation: {text!r}")

    ok = bool(hits) and EXPECT_ANSWER in text
    print("P0 FIRST LIGHT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

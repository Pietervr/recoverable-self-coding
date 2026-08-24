"""E1 v2 — occupancy/margin statics with position discipline.

Fixes over v1 (whose occupancy was echo-contaminated and whose load never
stressed the workspace):

  * The readout is scored ONLY over the QUESTION SPAN — the tokens of the
    two-hop question itself, located as the last "Fact" token onward. Held
    words hitting at their own mention in the load instruction no longer
    count; what counts is what PERSISTS into the question region.
  * Load levels up to K=48 unrelated single-token nouns (pool of 96).

Metrics per (item, level):
  cert     — intermediate in band top-k within the question span (pre-action)
  occ      — held words present in band top-k within the question span
  correct  — greedy answer matches

Run:  python3 e1v2_statics.py [--levels 0,4,8,16,32,48] [--items 45]
Logs: runs/e1v2_statics.jsonl (resumable) + runs/e1v2_summary.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from harness.battery import (
    filter_single_token,
    graded,
    held_words,
    load_probe_swap,
    ramped_prompt,
)
from harness.certify import band_layers, occupancy_of
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent


def question_span(slice_resp: dict) -> tuple[int, int]:
    """(start, end) positions of the question segment: from the LAST token
    whose text contains 'Fact' to the end of the prompt."""
    toks = slice_resp["token_strs"]
    start = 0
    for i, t in enumerate(toks):
        if "Fact" in t:
            start = i
    return start, len(toks)


def span_view(slice_resp: dict, start: int, end: int) -> dict:
    """A shallow copy of the slice response with cells restricted to
    positions [start, end) so certify/occupancy score only that span."""
    cells = {}
    for layer, cell in slice_resp["cells"].items():
        cells[layer] = {"top_tokens": cell["top_tokens"][start:end]}
    return {"cells": cells}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--levels", default="0,4,8,16,32,48")
    ap.add_argument("--items", type=int, default=45)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default=str(HERE / "runs" / "e1v2_statics.jsonl"))
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",")]

    c = JLensClient(port=args.port)
    c.require_n1000()

    items = load_probe_swap()
    kept, _ = filter_single_token(c, items)
    rng = random.Random(args.seed)
    rng.shuffle(kept)
    kept = kept[: args.items]
    print(f"E1v2: {len(kept)} items x {levels}")

    log = RunLog(args.out)
    done = log.done_keys("item", "level")
    band: list[int] | None = None

    cells = [(it, lv) for lv in levels for it in kept]
    rng.shuffle(cells)
    from harness.certify import certified  # local import keeps top tidy

    for i, (it, lv) in enumerate(cells):
        if (it["name"], lv) in done:
            continue
        words = held_words(c, lv, seed=hash((it["name"], lv)) & 0xFFFF)
        prompt = ramped_prompt(it, words)
        sl = c.slice(prompt, top_n=args.top_k, max_seq_len=1024)
        if band is None:
            band = band_layers(sl["layers"])
            print(f"band: {band[0]}..{band[-1]}")
        qs, qe = question_span(sl)
        view = span_view(sl, qs, qe)
        cert = certified(view, [it["intermediate"]], band, args.top_k)
        occ = occupancy_of(view, words, band, args.top_k) if words else 0
        text = c.generate(prompt, max_tokens=8)
        ok = graded(it, text)
        log.write(
            {
                "item": it["name"],
                "level": lv,
                "n_words": len(words),
                "q_span": [qs, qe],
                "certified": cert["certified"],
                "best_rank": cert["best_rank"],
                "occupancy": occ,
                "correct": ok,
                "text": text[:48],
            }
        )
        if i % 10 == 0:
            print(f"[{i}/{len(cells)}] {it['name']} K={lv} span={qs}:{qe} "
                  f"cert={int(cert['certified'])} occ={occ} ok={int(ok)}")

    by_level: dict[int, list[dict]] = defaultdict(list)
    for r in log.records():
        if "level" in r:
            by_level[r["level"]].append(r)
    summary = {}
    for lv in sorted(by_level):
        rs = by_level[lv]
        n = len(rs)
        nc = sum(r["certified"] for r in rs)
        summary[lv] = {
            "n": n,
            "cert_rate": round(nc / n, 3),
            "accuracy": round(sum(r["correct"] for r in rs) / n, 3),
            "mean_occupancy": round(sum(r["occupancy"] for r in rs) / n, 2),
            "occ_frac_of_K": round(
                sum(r["occupancy"] for r in rs) / max(1, sum(r["n_words"] for r in rs)), 3
            ),
            "sr_proxy": round((n - nc) / max(1, nc), 3),
        }
    print("E1v2 SUMMARY:")
    print(json.dumps(summary, indent=1))
    (HERE / "runs" / "e1v2_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

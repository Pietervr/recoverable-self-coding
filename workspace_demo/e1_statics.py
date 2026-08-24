"""E1 — occupancy saturation and the margin (statics), design doc §4.

For each load level K (held-in-mind unrelated words) x battery item:
  slice(ramped prompt) -> certification of the two-hop intermediate +
  occupancy (how many held words sit in the band top-k);
  generate -> graded answer.

Predictions under test: occupancy plateaus (capacity C); certification rate
falls (SR rises) BEFORE accuracy falls as K grows.

Run:  python3 e1_statics.py [--levels 0,2,4,8,16] [--items 60] [--top-k 10]
Logs: runs/e1_statics.jsonl (resumable; summary printed + saved)
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
from harness.certify import band_layers, certified, occupancy_of
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--levels", default="0,2,4,8,16")
    ap.add_argument("--items", type=int, default=60)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=str(HERE / "runs" / "e1_statics.jsonl"))
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",")]

    c = JLensClient(port=args.port)
    c.require_n1000()

    items = load_probe_swap()
    kept, dropped = filter_single_token(c, items)
    rng = random.Random(args.seed)
    rng.shuffle(kept)
    kept = kept[: args.items]
    print(f"E1: {len(kept)} items x levels {levels}; dropped {len(dropped)}")

    log = RunLog(args.out)
    done = log.done_keys("item", "level")

    band: list[int] | None = None
    cells = [(it, lv) for lv in levels for it in kept]
    rng.shuffle(cells)  # interleave levels so partial runs cover all levels

    for i, (it, lv) in enumerate(cells):
        if (it["name"], lv) in done:
            continue
        words = held_words(c, lv, seed=hash((it["name"], lv)) & 0xFFFF)
        prompt = ramped_prompt(it, words)
        sl = c.slice(prompt, top_n=args.top_k, max_seq_len=768)
        if band is None:
            band = band_layers(sl["layers"])
            print(f"band: {band[0]}..{band[-1]}")
        cert = certified(sl, [it["intermediate"]], band, args.top_k)
        occ = occupancy_of(sl, words, band, args.top_k) if words else 0
        text = c.generate(prompt, max_tokens=8)
        ok = graded(it, text)
        log.write(
            {
                "item": it["name"],
                "level": lv,
                "n_words": len(words),
                "certified": cert["certified"],
                "best_rank": cert["best_rank"],
                "occupancy": occ,
                "correct": ok,
                "text": text[:48],
            }
        )
        if i % 10 == 0:
            print(f"[{i}/{len(cells)}] {it['name']} K={lv} "
                  f"cert={int(cert['certified'])} occ={occ} ok={int(ok)}")

    # summary
    by_level: dict[int, list[dict]] = defaultdict(list)
    for r in log.records():
        if "level" in r:
            by_level[r["level"]].append(r)
    summary = {}
    for lv in sorted(by_level):
        rs = by_level[lv]
        n = len(rs)
        summary[lv] = {
            "n": n,
            "cert_rate": round(sum(r["certified"] for r in rs) / n, 3),
            "accuracy": round(sum(r["correct"] for r in rs) / n, 3),
            "mean_occupancy": round(sum(r["occupancy"] for r in rs) / n, 2),
            "sr_proxy": round(
                sum(not r["certified"] for r in rs) / max(1, sum(r["certified"] for r in rs)), 3
            ),
        }
    print("E1 SUMMARY (by load level):")
    print(json.dumps(summary, indent=1))
    (HERE / "runs" / "e1_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

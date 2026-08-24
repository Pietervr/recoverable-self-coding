"""E2c — in-pass parallel demand: the collapse boundary moved inside one pass.

E1/E2/E2b synthesis: sequential drives load the context STORE, and the store
cannot saturate the per-pass STAGE — routing is protected, summoning is
on-demand, certification never leaves its ceiling. If a capacity collapse
boundary exists it must be induced IN-PASS: M independent two-hop inferences
posed simultaneously in ONE prompt, answered in one ordered continuation.
Certification of each chain's intermediate is read from the PROMPT span
(pre-generation), so it measures simultaneous staging, not emission.

Drive: M ∈ {1,2,3,4,5,6} chains per trial, 20 trials per M, compositions
sampled category-diverse (chunking guard, design doc §6) from the probe-swap
items whose prompt ends in "is" (clause-embeddable subset). Readout top-25:
certified = best rank ≤ 10 (unchanged); ranks 11–25 = crowding.

Pre-registered predictions (P) and falsifiers (F):
  P1c per-chain certification declines with M (staging contention; the E1
      capacity ~3 finally binding).
      F1c: flat at ceiling to M=6 → the stage parallelizes beyond 2×
      capacity; the boundary is out of reach even in-pass.
  P2c per-slot accuracy declines with M, AND at fixed M an uncertified
      chain's slot errs more than certified chains' slots — determinant
      absence predicts WHICH slot fails (the E3 signature, cleanest form).
      F2c: slot errors uncorrelated with per-chain certification.
  P3c mean best-rank degrades with M BEFORE binary cert rate falls
      (the leading-indicator ordering, in-pass form).

Format gate: parse success (numbered-slot markers recovered) must be ≥0.8
at M≤2, else abort — a format failure is not a workspace result.

COMMITMENT-POSITION refinement (added after the span-aggregated v1 run
fired F1c at cert=1.000 for all M — pre-registered before the v2 run):
span-aggregated certification permits POSITION-PARALLEL staging (each
chain staged at its own clause's positions), so it cannot see a
bottleneck. v2 additionally reads each chain's best rank over the FINAL 3
prompt positions (`rank_commit`) — the moment the first answer must be
ready. Predictions:
  P4c commitment-position staging declines with M (the E1 capacity ~3
      binds at the bottleneck position) even though span staging does not.
  P5c chains unstaged at commitment are NOT less accurate — autoregressive
      emission re-summons each chain at its own answer token (the
      serialization defense, demonstrated end-to-end). A P5c REVERSAL
      (unstaged chains err more) would instead be the E3
      determinant-absence signature at the commitment bottleneck.

Run:  python3 e2c_parallel.py [--trials 20] [--mmax 6]
Logs: runs/e2c_parallel.jsonl + runs/e2c_summary.json  (v1, span-only)
      runs/e2c_parallel_v2.jsonl + runs/e2c_v2_summary.json  (with commit)
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from harness.battery import filter_single_token, load_probe_swap
from harness.certify import band_layers, certified
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent


def clause_items(items: list[dict]) -> list[dict]:
    """Items whose prompt can embed as a clause: 'Fact: The X of Y is' ->
    'the X of Y'."""
    out = []
    for it in items:
        p = it["prompt"].strip()
        if not p.lower().startswith("fact:") or not p.endswith("is"):
            continue
        clause = p[5:].strip()[:-2].strip()
        clause = clause[0].lower() + clause[1:]
        out.append({**it, "clause": clause})
    return out


def composite_prompt(chosen: list[dict]) -> str:
    parts = "; ".join(
        f"({i + 1}) {it['clause']}" for i, it in enumerate(chosen)
    )
    return (
        "Fact: Answering all at once, in order: "
        + parts
        + ". The answers are: (1)"
    )


def parse_slots(text: str, m: int) -> tuple[list[str], bool]:
    """Continuation starts after '(1)'. Split on (i) / i. markers. Returns
    (segments 1..m, parsed_ok)."""
    body = "(1)" + text
    marks: list[tuple[int, int]] = []
    for mt in re.finditer(r"\((\d)\)|(?<![\d.])(\d)\.\s", body):
        num = mt.group(1) or mt.group(2)
        marks.append((mt.start(), int(num)))
    segs: dict[int, str] = {}
    for j, (pos, num) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else len(body)
        if 1 <= num <= m and num not in segs:
            segs[num] = body[pos:end]
    ok = all(i in segs for i in range(1, m + 1))
    if ok:
        return [segs[i] for i in range(1, m + 1)], True
    # fallback: ordered containment over the whole text
    return [text] * m, False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--mmax", type=int, default=6)
    ap.add_argument("--out", default=str(HERE / "runs" / "e2c_parallel_v2.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    print(f"band: {band[0]}..{band[-1]}")

    kept, _ = filter_single_token(c, load_probe_swap())
    pool = clause_items(kept)
    print(f"clause-embeddable battery: {len(pool)} items")

    log = RunLog(args.out)
    done = {(r.get("m"), r.get("trial")) for r in log.records()}

    for m in range(1, args.mmax + 1):
        for trial in range(args.trials):
            if (m, trial) in done:
                continue
            rng = random.Random(9000 + 100 * m + trial)
            shuffled = pool[:]
            rng.shuffle(shuffled)
            chosen: list[dict] = []
            cats: set[str] = set()
            for it in shuffled:
                if len(chosen) >= m:
                    break
                if it["category"] in cats:
                    continue
                chosen.append(it)
                cats.add(it["category"])
            if len(chosen) < m:  # category diversity exhausted; fill
                for it in shuffled:
                    if len(chosen) >= m:
                        break
                    if it not in chosen:
                        chosen.append(it)

            prompt = composite_prompt(chosen)
            sl = c.slice(prompt, top_n=25, max_seq_len=1024, tail=300)
            view = {
                "cells": {
                    layer: {"top_tokens": cell["top_tokens"]}
                    for layer, cell in sl["cells"].items()
                }
            }
            # commitment view: the final 3 prompt positions only
            n_pos = len(next(iter(sl["cells"].values()))["top_tokens"])
            view_end = {
                "cells": {
                    layer: {"top_tokens": cell["top_tokens"][max(0, n_pos - 3):]}
                    for layer, cell in sl["cells"].items()
                }
            }
            text = c.generate(prompt, max_tokens=6 * m + 6)
            segs, parsed = parse_slots(text, m)

            n_ok = 0
            n_commit = 0
            for slot, it in enumerate(chosen):
                r = certified(view, [it["intermediate"]], band, 25)
                r_end = certified(view_end, [it["intermediate"]], band, 25)
                rank = r["best_rank"]
                rc = r_end["best_rank"]
                ok = it["answer"].strip().lower() in segs[slot].lower()
                n_ok += ok
                n_commit += rc is not None and rc <= 10
                log.write(
                    {
                        "exp": "e2c", "m": m, "trial": trial, "slot": slot + 1,
                        "item": it["name"], "rank": rank,
                        "certified": rank is not None and rank <= 10,
                        "rank_commit": rc,
                        "commit_staged": rc is not None and rc <= 10,
                        "correct": ok, "parsed": parsed,
                        "ctx_tokens": sl["seq_len"],
                    }
                )
            print(
                f"m={m} trial={trial:>2} parsed={int(parsed)} ok={n_ok}/{m} "
                f"commit_staged={n_commit}/{m} {text[:30]!r}"
            )
        # format gate after each of the first two levels
        if m <= 2:
            rs = [r for r in log.records() if r.get("m") == m]
            pr = sum(r["parsed"] for r in rs) / len(rs)
            if pr < 0.8:
                raise RuntimeError(f"format gate FAILED at m={m}: parse={pr:.2f}")

    # summary + the pre-registered tests
    recs = [r for r in log.records() if r.get("exp") == "e2c"]
    latest: dict[tuple, dict] = {}
    for r in recs:
        latest[(r["m"], r["trial"], r["slot"])] = r
    recs = list(latest.values())
    summary: dict = {}
    print("\nP1c/P3c — per-chain certification, rank, accuracy vs M:")
    for m in sorted({r["m"] for r in recs}):
        rs = [r for r in recs if r["m"] == m]
        cert = sum(r["certified"] for r in rs) / len(rs)
        acc = sum(r["correct"] for r in rs) / len(rs)
        ranks = [r["rank"] for r in rs if r["rank"] is not None]
        mr = sum(ranks) / len(ranks)
        parsed = sum(r["parsed"] for r in rs) / len(rs)
        summary[str(m)] = {
            "n": len(rs), "cert_rate": round(cert, 3),
            "accuracy": round(acc, 3), "mean_rank": round(mr, 2),
            "absent": sum(1 for r in rs if r["rank"] is None),
            "parse_rate": round(parsed, 2),
        }
        print(
            f"  M={m}: cert={cert:.3f} mean_rank={mr:.2f} acc={acc:.3f} "
            f"absent={summary[str(m)]['absent']} parse={parsed:.2f} n={len(rs)}"
        )
    print("\nP2c — slot error conditional on that chain's certification (M>=3):")
    hi = [r for r in recs if r["m"] >= 3]
    for label, rs in (
        ("certified", [r for r in hi if r["certified"]]),
        ("uncertified", [r for r in hi if not r["certified"]]),
    ):
        if rs:
            err = 1 - sum(r["correct"] for r in rs) / len(rs)
            print(f"  err|{label} = {err:.3f} (n={len(rs)})")
        else:
            print(f"  err|{label} : n=0")

    print("\nP4c — commitment-position staging vs M (final 3 positions):")
    for m in sorted({r["m"] for r in recs}):
        rs = [r for r in recs if r["m"] == m]
        cs = sum(r["commit_staged"] for r in rs) / len(rs)
        rcs = [r["rank_commit"] for r in rs if r["rank_commit"] is not None]
        mr = sum(rcs) / len(rcs) if rcs else float("nan")
        per_trial = defaultdict(int)
        for r in rs:
            per_trial[r["trial"]] += r["commit_staged"]
        mean_staged = sum(per_trial.values()) / len(per_trial)
        summary[str(m)]["commit_staged_rate"] = round(cs, 3)
        summary[str(m)]["mean_staged_per_trial"] = round(mean_staged, 2)
        print(
            f"  M={m}: staged_rate={cs:.3f} mean_rank_commit={mr:.2f} "
            f"staged/trial={mean_staged:.2f} "
            f"absent_at_commit={sum(1 for r in rs if r['rank_commit'] is None)}"
        )
    print("\nP5c — slot error conditional on commitment staging (M>=3):")
    for label, rs in (
        ("commit_staged", [r for r in hi if r["commit_staged"]]),
        ("not_staged", [r for r in hi if not r["commit_staged"]]),
    ):
        if rs:
            err = 1 - sum(r["correct"] for r in rs) / len(rs)
            print(f"  err|{label} = {err:.3f} (n={len(rs)})")
        else:
            print(f"  err|{label} : n=0")
    (HERE / "runs" / "e2c_v2_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Paired analysis of the E2 hysteresis log (design doc §4/§8 predictions).

The two arms are item-matched by construction (same rng seed per session,
same held-word seeds per step), so every (session, step) is a matched pair
differing only in re-entrant content (alpha) — length-matched via padding.

Reads runs/e2_hysteresis.jsonl (last record per (alpha, session, step) wins),
prints:
  1. overall accuracy per arm + McNemar discordant counts (paired)
  2. up vs down accuracy at matched k, per arm (the hysteresis test)
  3. probe (loaded ctx) vs reset_probe (cleared ctx), per arm
  4. certification failures + best_rank distribution per branch
  5. occupancy: loaded vs post-reset
  6. context-length audit (alpha=0 must be >= alpha=1 at each pair)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "runs" / "e2_hysteresis.jsonl"


def main() -> int:
    latest: dict[tuple, dict] = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("exp") == "e2":
            latest[(r["alpha"], r["session"], r["step"])] = r
    recs = list(latest.values())
    sessions = sorted({r["session"] for r in recs})
    print(f"records: {len(recs)}  sessions: {sessions}")

    # 1. overall + McNemar pairs
    by_key = {(r["alpha"], r["session"], r["step"]): r for r in recs}
    pairs = []
    for (a, s, t), r in by_key.items():
        if a == 1 and (0, s, t) in by_key:
            pairs.append((r, by_key[(0, s, t)]))
    n01 = sum(1 for r1, r0 in pairs if not r1["correct"] and r0["correct"])
    n10 = sum(1 for r1, r0 in pairs if r1["correct"] and not r0["correct"])
    for a in (1, 0):
        rs = [r for r in recs if r["alpha"] == a]
        acc = sum(r["correct"] for r in rs) / len(rs)
        print(f"alpha={a}: n={len(rs)} accuracy={acc:.3f}")
    print(f"paired steps: {len(pairs)}  discordant a0-only-correct={n01} "
          f"a1-only-correct={n10}  (a1 worse if first >> second)")

    # 2. hysteresis: up vs down at matched k, per arm
    print("\nup vs down accuracy at matched k (n per cell):")
    for a in (1, 0):
        cells: dict[tuple, list] = defaultdict(list)
        for r in recs:
            if r["alpha"] == a and r["branch"] in ("up", "down"):
                cells[(r["branch"], r["k"])].append(r["correct"])
        ks = sorted({k for (_, k) in cells if ("down", k) in cells})
        row = []
        for k in ks:
            u = cells[("up", k)]
            d = cells[("down", k)]
            row.append(f"k={k}: {sum(u)/len(u):.2f}->{sum(d)/len(d):.2f}")
        print(f"  alpha={a}: " + "  ".join(row))
        um = [c for k in ks for c in cells[("up", k)]]
        dm = [c for k in ks for c in cells[("down", k)]]
        print(f"           mean up={sum(um)/len(um):.3f} "
              f"down={sum(dm)/len(dm):.3f}  (hysteresis => down < up)")

    # 3. probe vs reset_probe
    print("\nprobe (loaded ctx) vs reset_probe (cleared ctx):")
    for a in (1, 0):
        for br in ("probe", "reset_probe"):
            rs = [r for r in recs if r["alpha"] == a and r["branch"] == br]
            acc = sum(r["correct"] for r in rs) / len(rs)
            occ = sum(r["occupancy"] for r in rs) / len(rs)
            ctx = sum(r["ctx_tokens"] for r in rs) / len(rs)
            print(f"  alpha={a} {br:>11}: n={len(rs)} acc={acc:.3f} "
                  f"occ={occ:.2f} ctx={ctx:.0f}")

    # 4. certification
    fails = [r for r in recs if not r["certified"]]
    print(f"\ncertification failures: {len(fails)}/{len(recs)}")
    for br in ("up", "down", "probe", "reset_probe"):
        rs = [r for r in recs if r["branch"] == br]
        r1 = sum(1 for r in rs if r["best_rank"] == 1) / len(rs)
        print(f"  {br:>11}: best_rank==1 in {r1:.3f} of steps")

    # 6. length audit
    bad = [
        (s, t)
        for (a, s, t), r in by_key.items()
        if a == 0 and (1, s, t) in by_key
        and r["ctx_tokens"] < by_key[(1, s, t)]["ctx_tokens"]
    ]
    print(f"\nlength audit: alpha=0 shorter than alpha=1 at {len(bad)} "
          f"of {len(pairs)} pairs {bad[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

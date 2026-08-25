"""E4 analysis — the five pre-registered tests (e4_loop_collapse.py).

P1L collapse + arm contrast   P2L hysteresis   P3L reset discriminator
P4L the mechanistic SR channel (cert/rank vs congestion)   P5L genealogies
Writes runs/e4_summary.json.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "runs" / "e4_loop.jsonl"


def main() -> int:
    recs = [json.loads(x) for x in LOG.read_text().splitlines()
            if '"exp": "e4"' in x]
    print(f"records: {len(recs)}")
    summary: dict = {}

    print("\nP1L/P2L — per-dwell, both arms (branch l | P_u acc late backlog_end ctx):")
    agg = defaultdict(list)
    for r in recs:
        agg[(r["alpha"], r["branch"], r["l"], r["step"])].append(r)
    for k in sorted(agg, key=lambda k: (k[0], k[3])):
        rs = agg[k]
        n = len(rs)
        pu = sum(r["uncert"] for r in rs) / n
        acc = sum(r["correct"] for r in rs) / n
        late = sum(r["late"] for r in rs) / n
        cert = sum(r["certified"] for r in rs) / n
        qend = rs[-1]["queue_after"]
        summary[f"a{k[0]}_{k[1]}_{k[2]}"] = {
            "n": n, "P_u": round(pu, 2), "acc": round(acc, 2),
            "late": round(late, 2), "cert": round(cert, 2), "q_end": qend,
        }
        print(f"  a={k[0]} {k[1]:>11} l={k[2]:.2f} | P_u={pu:.2f} acc={acc:.2f} "
              f"late={late:.2f} cert={cert:.2f} q_end={qend} n={n}")

    print("\nper-seed up-branch trajectories and collapse markers (alpha=0.8):")
    print("  onset = first l with P_u >= 0.5; runaway = first l with "
          "P_u >= 0.9 AND backlog growth (q_end > 5)")
    seeds = sorted({r.get("seed", 0) for r in recs})
    markers = {}
    for s in seeds:
        pts = defaultdict(list)
        qend = {}
        for r in recs:
            if (r["alpha"] == 0.8 and r.get("seed", 0) == s
                    and r["branch"] == "up"):
                pts[r["l"]].append(r["uncert"])
                qend[r["l"]] = r["queue_after"]
        row = []
        onset = runaway = None
        for l in sorted(pts):
            pu = sum(pts[l]) / len(pts[l])
            row.append(f"{l:.2f}:{pu:.2f}/q{qend[l]}")
            if onset is None and pu >= 0.5:
                onset = l
            if runaway is None and pu >= 0.9 and qend[l] > 5:
                runaway = l
        markers[s] = {"onset": onset, "runaway": runaway}
        print(f"  seed {s}: {'  '.join(row)}")
        print(f"          onset l={onset}  runaway l={runaway}  "
              f"(metastable window: {onset} -> {runaway})")
    summary["collapse_markers"] = markers

    print("\nP4L — certification and rank vs congestion (alpha=0.8 arm):")
    a8 = [r for r in recs if r["alpha"] == 0.8]
    for lo, hi, lab in [(0, 0, "q=0"), (1, 9, "q 1-9"), (10, 29, "q 10-29"),
                        (30, 10_000, "q>=30")]:
        rs = [r for r in a8 if lo <= r["queue_after"] <= hi]
        if not rs:
            continue
        cert = sum(r["certified"] for r in rs) / len(rs)
        ranks = [r["rank"] for r in rs if r["rank"] is not None]
        mr = sum(ranks) / len(ranks)
        print(f"  {lab:>8}: cert={cert:.3f} mean_rank={mr:.2f} n={len(rs)}")

    print("\nP5L — genealogies (alpha=0.8; keyed by (seed, root) — root ids "
          "collide across seeds):")
    fam = defaultdict(int)
    for r in a8:
        if r["depth"] > 0:
            fam[(r.get("seed", 0), r["root"])] += 1
    sizes = sorted(fam.values(), reverse=True)
    print(f"  {len(sizes)} nontrivial trees; sizes {sizes[:15]}; "
          f"offspring total {sum(sizes)}")

    (HERE / "runs" / "e4_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

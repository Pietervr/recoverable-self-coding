"""E2b analysis — the four pre-registered predictions (e2b_collapse.py).

  P1: fact-step certification declines with L      -> cert/rank vs L per arm
  P2: earlier/steeper decline under alpha=1        -> logistic (L50, beta) fit
  P3: determinant absence predicts error at high L -> conditional error rates
  P4: watch-query accuracy declines past ~3        -> query accuracy vs L

Plus: crowding (rank 11-25) vs absence (rank None) split, occupancy of the
liable watch list vs L (did interrogation defeat E1's eviction?), and the
alpha=0-never-shorter length audit. Logistic fit is a grid MLE of
p(cert) = 1/(1+exp(beta*(L-L50))) — no scipy dependency.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "runs" / "e2b_collapse.jsonl"


def logistic_fit(pts: list[tuple[int, bool]]) -> tuple[float, float]:
    """Grid-MLE (L50, beta) for p = 1/(1+exp(beta*(L-L50)))."""
    best, best_ll = (float("nan"), float("nan")), -1e18
    for l50_i in range(-40, 241):
        l50 = l50_i / 10.0
        for b_i in range(1, 61):
            beta = b_i / 20.0
            ll = 0.0
            for L, c in pts:
                p = 1.0 / (1.0 + math.exp(min(50, max(-50, beta * (L - l50)))))
                p = min(1 - 1e-9, max(1e-9, p))
                ll += math.log(p) if c else math.log(1 - p)
            if ll > best_ll:
                best_ll, best = ll, (l50, beta)
    return best


def rank_class(rank: int | None) -> str:
    if rank is None:
        return "absent"
    return "certified" if rank <= 10 else "crowded"


def main() -> int:
    latest: dict[tuple, dict] = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("exp") == "e2b":
            latest[(r["alpha"], r["session"], r["step"])] = r
    recs = list(latest.values())
    facts = [r for r in recs if r["kind"] in ("fact2", "fact3")]
    queries = [r for r in recs if r["kind"] == "query"]
    print(f"records: {len(recs)}  fact steps: {len(facts)}  queries: {len(queries)}")

    # P1: cert + accuracy vs L per arm
    print("\nP1 — fact-step certification and accuracy vs L:")
    for a in (1, 0):
        row = []
        for L in sorted({r["level"] for r in facts}):
            rs = [r for r in facts if r["alpha"] == a and r["level"] == L]
            cert = sum(r["certified"] for r in rs) / len(rs)
            acc = sum(r["correct"] for r in rs) / len(rs)
            row.append(f"L={L}: cert={cert:.2f} acc={acc:.2f} (n={len(rs)})")
        print(f"  alpha={a}: " + "  ".join(row))

    # per-determinant worst rank class, by kind
    print("\nrank classes by kind and L (certified/crowded/absent of the worst determinant):")
    for a in (1, 0):
        for kind in ("fact2", "fact3"):
            row = []
            for L in sorted({r["level"] for r in facts}):
                rs = [r for r in facts if r["alpha"] == a and r["level"] == L and r["kind"] == kind]
                if not rs:
                    continue
                cls = defaultdict(int)
                for r in rs:
                    worst = None
                    for rk in r["ranks"].values():
                        if rk is None:
                            worst = None
                            break
                        worst = rk if worst is None or rk > worst else worst
                    cls[rank_class(worst)] += 1
                n = len(rs)
                row.append(
                    f"L={L}: {cls['certified']}/{cls['crowded']}/{cls['absent']}"
                )
            print(f"  alpha={a} {kind}: " + "  ".join(row) + "   (cert/crowd/absent)")

    # P2: logistic fits per arm
    print("\nP2 — logistic collapse fit p(cert) vs L per arm:")
    for a in (1, 0):
        pts = [(r["level"], bool(r["certified"])) for r in facts if r["alpha"] == a]
        l50, beta = logistic_fit(pts)
        print(f"  alpha={a}: L50={l50:.1f}  beta={beta:.2f}  (n={len(pts)})")

    # P3: determinant absence predicts error (pooled L>=4, and all-L)
    print("\nP3 — error rate conditional on certification:")
    for label, pool in (("L>=4", [r for r in facts if r["level"] >= 4]), ("all L", facts)):
        for a in (1, 0):
            rs = [r for r in pool if r["alpha"] == a]
            cert_rs = [r for r in rs if r["certified"]]
            unc_rs = [r for r in rs if not r["certified"]]
            e_c = 1 - sum(r["correct"] for r in cert_rs) / len(cert_rs) if cert_rs else float("nan")
            e_u = 1 - sum(r["correct"] for r in unc_rs) / len(unc_rs) if unc_rs else float("nan")
            print(
                f"  [{label}] alpha={a}: err|certified={e_c:.2f} (n={len(cert_rs)})"
                f"  err|uncertified={e_u:.2f} (n={len(unc_rs)})"
            )

    # P4: query accuracy vs L + rank differential
    print("\nP4 — watch-query accuracy vs L (capacity binding):")
    for a in (1, 0):
        row = []
        for L in sorted({r["level"] for r in queries}):
            rs = [r for r in queries if r["alpha"] == a and r["level"] == L]
            acc = sum(r["correct"] for r in rs) / len(rs)
            rh = [r["rank_held"] for r in rs if r["rank_held"] is not None]
            row.append(
                f"L={L}: acc={acc:.2f} rank_held~{sum(rh)/len(rh):.1f}" if rh
                else f"L={L}: acc={acc:.2f}"
            )
        print(f"  alpha={a}: " + "  ".join(row))

    # occupancy of the liable watch list vs L
    print("\noccupancy of the liable watch list at fact steps (E1 comparison):")
    for a in (1, 0):
        row = []
        for L in sorted({r["level"] for r in facts if r["level"] > 0}):
            rs = [r for r in facts if r["alpha"] == a and r["level"] == L]
            occ = sum(r["occupancy"] for r in rs) / len(rs)
            row.append(f"L={L}: {occ:.2f}")
        print(f"  alpha={a}: " + "  ".join(row))

    # length audit
    by_key = {(r["alpha"], r["session"], r["step"]): r for r in recs}
    pairs = [
        (r, by_key[(0, s, t)])
        for (a, s, t), r in by_key.items()
        if a == 1 and (0, s, t) in by_key
    ]
    bad = [1 for r1, r0 in pairs if r0["ctx_tokens"] < r1["ctx_tokens"]]
    print(f"\nlength audit: alpha=0 shorter at {sum(bad)} of {len(pairs)} pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

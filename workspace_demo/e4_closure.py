"""Gap 2 — the quantitative closure for the LLM operating loop (E4).

Extends the paper's mean-field closure to the measured E4 system and
locates the fold, to be compared with the measured runaway bracket.
Two coupled self-consistencies (the two-component memory, formalized):

  content:  u = 1 - (1 - P_late(x)) * (1 - P_err(u))
  load:     x = l / (1 - b * u)          (collapsed when b*u >= 1)

with every ingredient MEASURED, not assumed:
  b        realized branching ratio: served offspring per uncertified
           completion (genealogy count; the experiment's caps make this
           the honest effective kernel, below the injected alpha=0.8)
  P_late   deadline-overflow probability of the single-server FIFO queue
           at utilization x, computed by Lindley recursion over service
           times BOOTSTRAPPED from the measured per-task service_s
           (congested-window subset), deadline T_d = 66 s -- the paper's
           M/G/1 method (Sec. IV.F) applied to the measured law
  P_err    the content channel: probability a served task's ANSWER is
           wrong as a logistic function of the recent uncertified
           fraction u (last WINDOW_N served tasks, same arm and seed),
           fitted by grid MLE on the per-task E4 records (both arms --
           the alpha=0 arm anchors the low-u region)

Output: the fixed-point structure u*(l), the fold l_c (largest l with a
stable lucid solution), and the recovery spinodal (smallest l at which
the collapsed branch exists), against the measured per-seed runaway
points [0.60, 0.85, 0.85, 0.95]. Writes runs/e4_closure.json.

Run:  python3 e4_closure.py [--b <override>] [--seed 7]
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "runs" / "e4_loop.jsonl"
T_D = 66.0
WINDOW_N = 15


def load() -> list[dict]:
    latest: dict[tuple, dict] = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("exp") == "e4":
            latest[(r["alpha"], r.get("seed", 0), r["tid"])] = r
    return list(latest.values())


def measure_b(recs: list[dict]) -> float:
    a8 = [r for r in recs if r["alpha"] == 0.8]
    offspring = sum(1 for r in a8 if r["depth"] > 0)
    uncert = sum(1 for r in a8 if r["uncert"])
    return offspring / uncert


def service_samples(recs: list[dict]) -> list[float]:
    """Congested-regime service times (window filled: ctx > 2000 tokens)."""
    return [r["service_s"] for r in recs if r["ctx_tokens"] > 2000]


def p_late_curve(samples: list[float], rng: random.Random,
                 n_tasks: int = 20000) -> dict[float, float]:
    """Lindley recursion at each utilization x on a grid: W_{n+1} =
    max(0, W_n + S_n - A_n), A ~ Exp(x * mu_hat); late iff W + S > T_D."""
    mu_hat = 1.0 / (sum(samples) / len(samples))
    grid = [round(0.05 * k, 2) for k in range(1, 31)]
    curve = {}
    for x in grid:
        lam = x * mu_hat
        w = 0.0
        late = 0
        for _ in range(n_tasks):
            s = samples[rng.randrange(len(samples))]
            late += (w + s) > T_D
            a = rng.expovariate(lam)
            w = max(0.0, w + s - a)
        curve[x] = late / n_tasks
    return curve


def p_late_at(curve: dict[float, float], x: float) -> float:
    if x <= 0.05:
        return curve[0.05]
    if x >= 1.5:
        return 1.0
    lo = max(k for k in curve if k <= x)
    hi = min(k for k in curve if k >= x)
    if hi == lo:
        return curve[lo]
    f = (x - lo) / (hi - lo)
    return curve[lo] * (1 - f) + curve[hi] * f


def fit_p_err(recs: list[dict]) -> tuple[float, float, float]:
    """Logistic P_err(j) = p0 + (p1 - p0) / (1 + exp(-k (j - 0.5))) where j
    is the recent JUNK-DEPOSIT fraction: a served task deposits junk into
    the window iff its answer was wrong OR it was a repair task (repair
    lines contaminate regardless of correctness; a late-but-correct answer
    leaves no junk — lateness reaches the content channel only through the
    repairs it spawns). Grid MLE on (j_recent, wrong) pairs, both arms."""
    pairs = []
    for alpha in (0.8, 0.0):
        for seed in sorted({r.get("seed", 0) for r in recs}):
            arm = sorted(
                (r for r in recs
                 if r["alpha"] == alpha and r.get("seed", 0) == seed),
                key=lambda r: r["tid"])
            hist: list[int] = []
            for r in arm:
                if len(hist) >= 5:
                    u = sum(hist[-WINDOW_N:]) / len(hist[-WINDOW_N:])
                    pairs.append((u, 0 if r["correct"] else 1))
                hist.append(1 if (not r["correct"] or r["depth"] > 0) else 0)
    best, best_ll = (0.2, 0.5, 5.0), -1e18
    for p0i in range(5, 41):
        p0 = p0i / 100
        for p1i in range(p0i + 5, 96, 2):
            p1 = p1i / 100
            for k in (2.0, 4.0, 6.0, 8.0, 12.0):
                ll = 0.0
                for u, y in pairs:
                    p = p0 + (p1 - p0) / (1 + math.exp(-k * (u - 0.5)))
                    p = min(1 - 1e-9, max(1e-9, p))
                    ll += math.log(p) if y else math.log(1 - p)
                if ll > best_ll:
                    best_ll, best = ll, (p0, p1, k)
    print(f"  P_err fit: p0={best[0]:.2f} p1={best[1]:.2f} k={best[2]:.0f} "
          f"(n={len(pairs)} pairs)")
    return best


def p_err_at(fit: tuple[float, float, float], u: float) -> float:
    p0, p1, k = fit
    return p0 + (p1 - p0) / (1 + math.exp(-k * (u - 0.5)))


def fixed_points(l: float, b: float, curve, fit) -> list[float]:
    """Roots of g(u) = u - [1 - (1-P_late(x(u)))(1-P_err(u))] on u grid."""
    def g(u: float) -> float:
        if b * u >= 0.999:
            x = 1e6
        else:
            x = l / (1 - b * u)
        return u - (1 - (1 - p_late_at(curve, x)) * (1 - p_err_at(fit, u)))

    roots = []
    prev_u, prev_g = 0.0, g(0.0)
    for i in range(1, 401):
        u = i / 400
        gu = g(u)
        if prev_g == 0 or (prev_g < 0) != (gu < 0):
            roots.append(round((prev_u + u) / 2, 4))
        prev_u, prev_g = u, gu
    return roots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=float, default=None)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    recs = load()
    b = args.b if args.b is not None else measure_b(recs)
    samples = service_samples(recs)
    mean_s = sum(samples) / len(samples)
    cv = (sum((s - mean_s) ** 2 for s in samples) / len(samples)) ** 0.5 / mean_s
    print(f"measured: b={b:.3f}  service n={len(samples)} mean={mean_s:.2f}s "
          f"CV={cv:.2f}  T_d={T_D:.0f}s (theta={T_D / mean_s:.1f})")

    print("  computing Lindley P_late(x) from bootstrapped service law...")
    curve = p_late_curve(samples, rng)
    for x in (0.6, 0.8, 0.9, 1.0, 1.1):
        print(f"    P_late({x:.1f}) = {p_late_at(curve, x):.3f}")
    fit = fit_p_err(recs)

    print("\nfixed-point structure u*(l)   [S = # solutions]:")
    fold = None
    recovery = None
    rows = {}
    for li in range(20, 121, 2):
        l = li / 100
        roots = fixed_points(l, b, curve, fit)
        lucid = [u for u in roots if u < 0.75]
        collapsed_exists = (b * 0.999 >= 1) or any(u >= 0.75 for u in roots) \
            or l / (1 - b * min(0.999, 1.0)) >= 1.0
        rows[l] = roots
        if lucid:
            fold = l
        if collapsed_exists and recovery is None:
            recovery = l
        print(f"  l={l:.2f}: S={len(roots)} roots={roots}"
              + ("   <-- last lucid" if lucid else ""))
    print(f"\nPREDICTED fold (last l with a lucid solution): l_c = {fold}")
    print(f"MEASURED runaways (E4, per seed): 0.60, 0.85, 0.85, 0.95 "
          f"(median 0.85); onsets 0.40-0.85")
    (HERE / "runs" / "e4_closure.json").write_text(json.dumps(
        {"b": b, "mean_s": mean_s, "cv": cv,
         "p_err_fit": fit, "fold": fold,
         "p_late": {str(k): v for k, v in curve.items()},
         "roots": {str(k): v for k, v in rows.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

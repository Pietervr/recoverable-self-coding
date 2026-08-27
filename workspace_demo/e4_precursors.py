"""Early-warning precursors in the E4 data (the critical-slowing-down claim).

The paper: rising variance and lag-1 autocorrelation of the order
parameter announce the fold before it arrives (the fluctuation
precursors; cf. Scheffer-class early warnings). Test on the EXISTING E4
records: for each alpha=0.8 seed, take the up-branch task series BEFORE
that seed's runaway dwell, compute sliding-window (w=15) mean, variance,
and lag-1 autocorrelation of (a) the junk-deposit indicator and (b) the
uncertified indicator, and compare the early half against the late half
of the pre-runaway series. The E5 policy-ON series (stable, far from the
fold) is the negative control: no trend expected.

Small-n caveat: 40-90 pre-runaway tasks per seed; this is a coarse test,
reported as such. Trend statistic: difference late-half minus early-half,
plus a sign count across seeds.

Run:  python3 e4_precursors.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent

RUNAWAY = {0: 0.85, 1: 0.85, 2: 0.95, 3: 0.60}   # measured per-seed (E4)


def load(name: str, key_fields) -> list[dict]:
    latest = {}
    for line in (HERE / "runs" / name).read_text().splitlines():
        r = json.loads(line)
        latest[tuple(r.get(k) for k in key_fields)] = r
    return list(latest.values())


def sliding(series: list[float], w: int = 15):
    out = []
    for i in range(w, len(series) + 1):
        win = series[i - w:i]
        m = sum(win) / w
        var = sum((x - m) ** 2 for x in win) / w
        num = sum((win[j] - m) * (win[j + 1] - m) for j in range(w - 1))
        den = sum((x - m) ** 2 for x in win)
        ac1 = num / den if den > 1e-12 else 0.0
        out.append((m, var, ac1))
    return out


def analyze(label: str, series: list[float]) -> tuple[float, float] | None:
    st = sliding(series)
    if len(st) < 8:
        print(f"  {label}: too short (n={len(series)})")
        return None
    half = len(st) // 2
    early, late = st[:half], st[half:]
    dv = (sum(s[1] for s in late) / len(late)
          - sum(s[1] for s in early) / len(early))
    da = (sum(s[2] for s in late) / len(late)
          - sum(s[2] for s in early) / len(early))
    print(f"  {label}: n={len(series)}  dVar(late-early)={dv:+.4f}  "
          f"dAC1={da:+.4f}")
    return dv, da


def main() -> int:
    print("E4 alpha=0.8 seeds, pre-runaway up-branch (expect + trends):")
    e4 = load("e4_loop.jsonl", ("alpha", "seed", "tid"))
    signs_v, signs_a = [], []
    for s, ra in RUNAWAY.items():
        arm = sorted((r for r in e4 if r["alpha"] == 0.8
                      and r.get("seed", 0) == s and r["branch"] == "up"
                      and r["l"] < ra),
                     key=lambda r: r["tid"])
        junk = [1.0 if (not r["correct"] or r["depth"] > 0) else 0.0
                for r in arm]
        res = analyze(f"seed {s} junk-deposit", junk)
        if res:
            signs_v.append(res[0] > 0)
            signs_a.append(res[1] > 0)
    print(f"  sign count: variance rising {sum(signs_v)}/{len(signs_v)} "
          f"seeds; AC1 rising {sum(signs_a)}/{len(signs_a)} seeds")

    print("\nE5 policy-ON (stable control, expect no consistent trend):")
    e5 = load("e5_loop.jsonl", ("policy", "seed", "tid"))
    cv, ca = [], []
    for s in (0, 1):
        arm = sorted((r for r in e5 if r["policy"] == 1
                      and r.get("seed", 0) == s and r["branch"] == "up"),
                     key=lambda r: r["tid"])
        junk = [1.0 if (not r["correct"] or r["depth"] > 0) else 0.0
                for r in arm]
        res = analyze(f"seed {s} junk-deposit", junk)
        if res:
            cv.append(res[0] > 0)
            ca.append(res[1] > 0)
    print(f"  sign count: variance rising {sum(cv)}/{len(cv)}; "
          f"AC1 rising {sum(ca)}/{len(ca)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

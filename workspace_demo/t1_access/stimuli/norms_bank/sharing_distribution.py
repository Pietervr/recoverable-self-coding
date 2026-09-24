"""Step 1c: the distribution of lemmatised sharing counts, so R052 can set K on data (§3.1).

K is the floor on sharing count for the ten non-decisive clauses of a concept. §3.1 ranks a
concept's **12 selected** features by sharing count ascending, marks the two rarest decisive, and
requires every other selected feature to be shared by at least K cues.

TWO STATISTICS, because selection chooses WHICH 12 of a concept's features to use:

  R3   the sharing count of the concept's 3rd-rarest feature overall. This is what K must clear if
       the 12 selected are simply the 12 rarest. It is the statistic the handoff asked for.
  KMAX the largest K the concept can satisfy at all: take the two rarest as the decisive pair, sort
       the remaining features by sharing count descending, and read off the 10th. Any K <= KMAX is
       feasible for that concept, by selecting the ten most-shared of its remaining features.

They coincide exactly when a concept has 12 features, since then the ten non-decisive clauses are
forced. Above 12 features KMAX exceeds R3, and KMAX is what decides whether a concept can be built.

Sharing count s(f) = the number of the 4,411 single-word cues that share lemmatised feature f -
the published statistic, computed over the whole norm set and not over the bank.

    .venv-build/bin/python stimuli/norms_bank/sharing_distribution.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from norms_parse import Norms  # noqa: E402

SCENARIO = "final_occupations"
CLAUSES = 12
DECISIVE = 2
NON_DECISIVE = CLAUSES - DECISIVE
K_GRID = [2, 5, 10, 20, 30, 50, 75, 100, 150, 200]
NEEDED = {"buildings": 15}     # §3.1: buildings is 15, every other family 16
DEFAULT_NEEDED = 16


def quantiles(xs: list[int]) -> dict[str, float]:
    xs = sorted(xs)
    if not xs:
        return {}

    def q(p: float) -> float:
        i = max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))
        return xs[i]

    return {"min": xs[0], "p10": q(0.10), "p25": q(0.25), "median": q(0.50),
            "p75": q(0.75), "p90": q(0.90), "max": xs[-1], "n": len(xs)}


def main() -> int:
    norms = Norms(lemmatise=True)
    pool = json.loads((HERE / "pool_eligible.json").read_text())["scenarios"][SCENARIO]
    families = {f: pool[f]["sense1"]["words"] for f in pool}

    per_concept: dict[str, list[dict]] = {}
    for family, words in families.items():
        rows = []
        for cue in words:
            shares = sorted(norms.sharing[f] for f in norms.features[cue])
            rest = shares[DECISIVE:]                      # after the two rarest are spent
            kmax = sorted(rest, reverse=True)[NON_DECISIVE - 1] if len(rest) >= NON_DECISIVE else None
            rows.append({
                "cue": cue, "n_features": len(shares),
                "decisive": shares[:DECISIVE],
                "r3": shares[DECISIVE] if len(shares) > DECISIVE else None,
                "kmax": kmax,
                "median_share": statistics.median(shares),
            })
        per_concept[family] = rows

    all_rows = [r for rows in per_concept.values() for r in rows]
    all_shares = [norms.sharing[f] for rows in per_concept.values() for r in rows
                  for f in norms.features[r["cue"]]]

    out = {
        "scenario": SCENARIO, "clauses": CLAUSES, "decisive": DECISIVE,
        "sharing_denominator_cues": len(norms.features),
        "definition": {"R3": "sharing count of the concept's 3rd-rarest feature",
                       "KMAX": "10th-largest sharing count among the features left after the two rarest"},
        "pooled_candidate_feature_shares": quantiles(all_shares),
        "R3": {"overall": quantiles([r["r3"] for r in all_rows if r["r3"] is not None]),
               "by_family": {f: quantiles([r["r3"] for r in rows if r["r3"] is not None])
                             for f, rows in per_concept.items()}},
        "KMAX": {"overall": quantiles([r["kmax"] for r in all_rows if r["kmax"] is not None]),
                 "by_family": {f: quantiles([r["kmax"] for r in rows if r["kmax"] is not None])
                               for f, rows in per_concept.items()}},
        "concepts": per_concept,
        "feasible_by_K": {},
    }

    for k in K_GRID:
        row = {}
        for family, rows in per_concept.items():
            ok = [r["cue"] for r in rows if r["kmax"] is not None and r["kmax"] >= k]
            need = NEEDED.get(family, DEFAULT_NEEDED)
            row[family] = {"feasible": len(ok), "needed": need, "short_by": max(0, need - len(ok))}
        out["feasible_by_K"][k] = row

    (HERE / "sharing_distribution.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    print(f"sharing counts over {len(norms.features)} single-word cues, lemmatised features\n")
    p = out["pooled_candidate_feature_shares"]
    print(f"pooled over every candidate feature of every eligible concept (n={p['n']}):")
    print(f"  min {p['min']}  p10 {p['p10']}  p25 {p['p25']}  median {p['median']}"
          f"  p75 {p['p75']}  p90 {p['p90']}  max {p['max']}\n")

    for name in ("R3", "KMAX"):
        o = out[name]["overall"]
        print(f"{name} over {o['n']} eligible concepts: min {o['min']}  p10 {o['p10']}  p25 {o['p25']}"
              f"  median {o['median']}  p75 {o['p75']}  p90 {o['p90']}  max {o['max']}")
        for family in sorted(per_concept):
            q = out[name]["by_family"][family]
            print(f"   {family:>12}  min {q['min']:>4}  median {q['median']:>5}  max {q['max']:>5}  (n={q['n']})")
        print()

    print("concepts feasible at each K (KMAX >= K), against what the family needs:")
    hdr = "   K  " + "".join(f"{f[:9]:>10}" for f in sorted(per_concept))
    print(hdr)
    for k in K_GRID:
        cells = ""
        for family in sorted(per_concept):
            r = out["feasible_by_K"][k][family]
            cells += f"{r['feasible']:>7}/{r['needed']:<2}"
        short = [f for f in sorted(per_concept) if out["feasible_by_K"][k][f]["short_by"]]
        print(f"{k:>5}  {cells}   {'SHORT: ' + ', '.join(short) if short else 'all families clear'}")

    print(f"\n-> {HERE / 'sharing_distribution.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

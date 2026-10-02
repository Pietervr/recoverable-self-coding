"""Codex's no-CSLB route under §3.1's FULL rules: + Hovhannisyan (2021), + clothing as a fourth family.

R052 handoff 203c6169. Codex's route record (RSC d6bdbc4) found 107 candidates at ten clauses for McRae + Feats +
Hovhannisyan at >= 3 productions with clothing as a fourth family, under his own screen. This puts the route under
the SAME rules as the 51 / 77 of clean_eligibility.py - T F N X P D in usable.py, dominant sense, E2 then E1 - so the
15 October choice compares like with like.

Rows:
  (a) McRae + Feats, three families                     the control: must reproduce 51 (twelve) and 77 (ten)
  (b) McRae + Feats + Hovhannisyan, three families
  (c) McRae + Feats + Hovhannisyan, four families (clothing.n.01 added; E2 against all four subtrees; the
      candidate-name ban X and the family-word rule F recomputed over the four-family set)
each at twelve and ten, single token; Hovhannisyan at its declared cutoff of >= 3 productions, with >= 5 as the
sensitivity. For (c): the count with rule T switched off, and the joint integer allocation.

ALLOCATION, for any number of families, as a max-flow with lower bounds: every split (CONF 64, CAL 16, PILOT 16)
holds every family at least once and at most half the split (so reciprocal cross-family pairs and a third-family
competitor exist), role totals are disjoint, and r BACKGROUND concepts per family are reserved FIRST (r = 1 gives
the four-family minimum of 100, r = 2 gives 104). Feasible iff the flow saturates. The binding family is found by
removing that family's concepts one at a time until the allocation fails: its SLACK is how many it can lose.

    .venv-build/bin/python stimuli/norms_bank/route_four_family.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

from nltk.corpus import wordnet as wn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import family_pool as fp  # noqa: E402
from feats_parse import Source  # noqa: E402
from usable import Canon, usable, words  # noqa: E402

THREE = ["animals", "foods", "vehicles"]
FOUR = THREE + ["clothing"]
FAMILY_WORDS = {
    "animals": {"animal", "animals"}, "foods": {"food", "foods"}, "vehicles": {"vehicle", "vehicles"},
    "clothing": {"clothing", "clothes"},
}
SPLITS = [("CONF", 64), ("CAL", 16), ("PILOT", 16)]
THRESHOLDS = [12, 10]
TIERS = ["minimal", "protocol"]


def candidates(src: Source, families: list[str], trees: dict, tokens: dict) -> dict[str, dict]:
    out = {}
    for c in src.nouns():
        senses = wn.synsets(c, pos="n")
        if not senses or (wn.morphy(c, "n") or c) != c:
            continue
        home = [f for f in families if senses[0] in trees[f]]
        if len(home) != 1:
            continue
        fam = home[0]
        if any(set(senses) & trees[g] for g in families if g != fam):
            continue
        if tokens.get(c) != 1:
            continue
        out[c] = {"family": fam, "synset": senses[0].name(), "source": src.source_of(c)}
    return out


def collapse(q: dict[str, dict], families: list[str]) -> dict[str, list[str]]:
    best: dict[tuple, tuple] = {}
    for c, info in q.items():
        key, cand = (info["family"], info["synset"]), (-info["usable"], c)
        if key not in best or cand < best[key]:
            best[key] = cand
    fams: dict[str, list[str]] = {f: [] for f in families}
    for (fam, _), (_, c) in best.items():
        fams[fam].append(c)
    return {f: sorted(v) for f, v in fams.items()}


def _maxflow(cap: dict, s: str, t: str) -> tuple[int, dict]:
    flow = {u: {v: 0 for v in cap[u]} for u in cap}
    for u in list(cap):
        for v in list(cap[u]):
            cap.setdefault(v, {}).setdefault(u, 0)
            flow.setdefault(v, {}).setdefault(u, 0)
    total = 0
    while True:
        parent = {s: None}
        dq = deque([s])
        while dq and t not in parent:
            u = dq.popleft()
            for v, c in cap[u].items():
                if v not in parent and c - flow[u][v] > 0:
                    parent[v] = u
                    dq.append(v)
        if t not in parent:
            return total, flow
        v, push = t, float("inf")
        while parent[v] is not None:
            u = parent[v]
            push = min(push, cap[u][v] - flow[u][v])
            v = u
        v = t
        while parent[v] is not None:
            u = parent[v]
            flow[u][v] += push
            flow[v][u] -= push
            v = u
        total += push


def allocation(n: dict[str, int], families: list[str], reserve: int) -> dict:
    need = sum(k for _, k in SPLITS) + reserve * len(families)
    out = {"available": sum(n.values()), "needed": need, "margin": sum(n.values()) - need, "reserve": reserve}
    capf = {f: n[f] - reserve - len(SPLITS) for f in families}      # after one per split pre-assigned
    if any(v < 0 for v in capf.values()):
        out["feasible"] = False
        return out
    cap: dict = {"S": {}}
    for split, total in SPLITS:
        cap["S"][split] = total - len(families)
        cap[split] = {f: total // 2 - 1 for f in families}
    for f in families:
        cap.setdefault(f, {})["T"] = capf[f]
    want = sum(total - len(families) for _, total in SPLITS)
    got, flow = _maxflow(cap, "S", "T")
    out["feasible"] = got == want
    if out["feasible"]:
        w = {split: [flow[split][f] + 1 for f in families] for split, _ in SPLITS}
        w["BACKGROUND"] = [n[f] - sum(w[s][i] for s, _ in SPLITS) for i, f in enumerate(families)]
        out["witness"] = w
    return out


def slack(n: dict[str, int], families: list[str], reserve: int) -> dict[str, int]:
    """How many concepts each family can lose, all others fixed, before the allocation fails."""
    out = {}
    for f in families:
        k = 0
        while n[f] - k - 1 >= 0 and allocation({**n, f: n[f] - k - 1}, families, reserve)["feasible"]:
            k += 1
        out[f] = k if allocation(n, families, reserve)["feasible"] else -1
    return out


def run(src: Source, families: list[str], canon: Canon, tokens: dict, trees: dict, skip=frozenset()) -> dict:
    fwords = set().union(*(FAMILY_WORDS[f] for f in families))
    cands = candidates(src, families, trees, tokens)
    names = set(cands)
    res = {}
    for tier in TIERS:
        per = {c: usable(c, src.features[c], src.provenance, names, canon, tier, skip, fwords)["count"]
               for c in cands}
        for thr in THRESHOLDS:
            q = {c: {**cands[c], "usable": per[c]} for c in cands if per[c] >= thr}
            fams = collapse(q, families)
            by_source: dict[str, dict[str, int]] = {}
            for f, cs in fams.items():
                for c in cs:
                    s = cands[c]["source"]
                    by_source.setdefault(s, {}).setdefault(f, 0)
                    by_source[s][f] += 1
            res[f"{tier}|>={thr}"] = {"counts": {f: len(v) for f, v in fams.items()},
                                      "total": sum(len(v) for v in fams.values()),
                                      "concepts": fams, "by_source": by_source}
    return res


def main() -> int:
    trees = {f: fp.subtree(f) for f in FOUR}
    tok = json.loads((HERE / "token_counts.json").read_text())
    tokens = tok["counts"]
    pooled = Source("pooled")
    p3 = {cut: Source("pooled3", hov_cutoff=cut) for cut in (3, 5)}
    vocab = {w for s in (pooled, p3[3]) for fs in s.features.values() for f in fs for w in words(f)}
    canon = Canon({w for w in vocab if w.isalpha()})

    rows = {
        "(a) McRae+Feats, 3 families": run(pooled, THREE, canon, tokens, trees),
        "(b) +Hovhannisyan >=3, 3 families": run(p3[3], THREE, canon, tokens, trees),
        "(c) +Hovhannisyan >=3, 4 families": run(p3[3], FOUR, canon, tokens, trees),
        "(c) without rule T": run(p3[3], FOUR, canon, tokens, trees, frozenset({"T"})),
        "(b) sensitivity, Hovhannisyan >=5": run(p3[5], THREE, canon, tokens, trees),
        "(c) sensitivity, Hovhannisyan >=5": run(p3[5], FOUR, canon, tokens, trees),
    }
    for name, res in rows.items():
        fams = FOUR if "4 families" in name or "rule T" in name or name.startswith("(c)") else THREE
        for key, r in res.items():
            r["allocation"] = {f"reserve{rv}": allocation(r["counts"], fams, rv) for rv in (1, 2)}
            r["slack_reserve1"] = slack(r["counts"], fams, 1) if r["allocation"]["reserve1"]["feasible"] else None

    out = {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "usable_sha256": hashlib.sha256((HERE / "usable.py").read_bytes()).hexdigest(),
           "tokenizer_json_sha256": tok["tokenizer_json_sha256"],
           "digests": p3[3].digests, "bookkeeping": p3[3].bookkeeping, "rows": rows}
    (HERE / "route_four_family.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    for name, res in rows.items():
        print(f"\n{name}")
        for key, r in res.items():
            a1, a2 = r["allocation"]["reserve1"], r["allocation"]["reserve2"]
            c = "/".join(str(v) for v in r["counts"].values())
            v1 = f"vs {a1['needed']}: {'FEASIBLE' if a1['feasible'] else 'no'} (margin {a1['margin']:+d})"
            v2 = f"vs {a2['needed']}: {'FEASIBLE' if a2['feasible'] else 'no'} (margin {a2['margin']:+d})"
            sl = f"  slack {r['slack_reserve1']}" if r["slack_reserve1"] else ""
            print(f"  {key:<14} {c:<14} = {r['total']:>3}   {v1}   {v2}{sl}")
    print(f"\n-> {HERE / 'route_four_family.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

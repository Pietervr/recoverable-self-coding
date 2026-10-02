"""The naming-acceptance rate of §3.1, measured on a seeded development sample of the four-family route.

R052 handoff 74c6bba1. The route (ROUTE_FOUR_FAMILY.md) reaches 104 usable concepts against 100 at ten clauses, but
that count is taken before §3.1's two-sided naming acceptance, which can only remove concepts. This measures the
acceptance rate on relational clauses so the margin of four becomes a number.

SAMPLE. 30 concepts from the route's pool (protocol rules, >= 10 usable features, four families, Hovhannisyan at
>= 3), 8/8/7/7 across animals/foods/vehicles/clothing, stratified by source in proportion to the pool (McRae 77,
Feats 13, Hovhannisyan 14 of 104 -> 22/4/4). Cell quotas: each source's count is split across families by
largest remainder on that source's own family mix, then McRae fills every family to its quota. Concepts are drawn
inside each (family, source) cell by a seed derived from SEED.

SELECTION (declared). A concept's usable features (usable.py, rules T F N X P D) are ranked by its source's
heuristic - the authors' published CV, highest first, when every feature has one; otherwise normalised production
frequency (30 x Prod_Freq / Num_Parts) or, for Hovhannisyan, which has no denominator, raw production count -
and ten are taken at evenly spaced positions over that order, so the ten span the concept's evidence range. The
heuristic used is recorded per concept. Decisiveness is not presumed from it: the naming test decides (§3.1).

RENDERING (declared, minimal). A clause is the feature's own words with "It" as subject: verb-led features
(is_, has_, does_, lives_, requires_ ...) become "It " + words; McRae's behaviour prefixes beh_-_ / inbeh_-_ are
dropped; participle-led features (used_, made_, worn_, eaten_ ...) become "It is " + words. The few verbless frames
need one connective, and these are the ONLY authored words, listed in CONNECTIVES and counted in the output. No
padding to §3's 8-14 token window is attempted - padding would be authored content, and is a separate rendering
decision.

ACCEPTANCE (§3.1, as declared). Ceiling: each of the ten clauses is shown ALONE; at most two may be named.
Floor: three seeded draws of eight of the ten clauses (independent draws, compositions may repeat); the concept
must be named on ALL three. Pass needs both. Reader: ollama llama3.1:8b (Meta), temperature 0, seed 20260924 -
the materials trial's reader, distinct from the model under test (Qwen3.6) and from the renderer (this code; no
model writes the clauses). Every call is stateless: no context carries between calls.

    .venv-build/bin/python stimuli/norms_bank/acceptance_sample.py
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import route_four_family as r4  # noqa: E402
from feats_parse import Source  # noqa: E402
from naming_test import MODEL, named, reader_identity  # noqa: E402
from usable import Canon, usable, words  # noqa: E402

SEED = 20261002
READER_SEED = 20260924
FAMILY_QUOTA = {"animals": 8, "foods": 8, "vehicles": 7, "clothing": 7}
SOURCE_ORDER = ["McRae", "Feats", "Hovhannisyan"]
CLAUSES, DRAW_SIZE, DRAWS, CEILING = 10, 8, 3, 2
PARTICIPLES = {"used", "made", "worn", "eaten", "hunted", "associated", "found", "herded", "kept", "ridden",
               "driven", "grown", "bought", "sold", "held", "seen", "built", "thrown", "sewn", "played",
               "flown", "drunk", "cooked", "baked", "fried", "served", "stored", "pulled", "owned", "sold/bought",
               "bought/sold", "considered", "measured", "covered", "filled", "shaped"}
# The only authored words: verbless frames need a connective. different_colours -> "It comes in different colours".
CONNECTIVES = {"different": "It comes in", "like": "It is", "symbol": "It is a", "a": "It is", "an": "It is"}
SINGLE = ("Here is a single clue about one everyday thing.\n\nClue: {clue}\n\n"
          "What is being described? Answer with the single most likely word, and nothing else.")
SEVERAL = ("Here are several clues about one everyday thing.\n\n{clues}\n\n"
           "What is being described? Answer with the single most likely word, and nothing else.")


def derived(*parts) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in (SEED, *parts)).encode()).hexdigest()[:16], 16)


def render(feature: str) -> tuple[str, bool]:
    """(clause, uses_an_authored_connective). The feature's own words, with 'It' as subject."""
    toks = [t for t in re.sub(r"^(in)?beh_-_", "", feature).split("_") if t]
    head, text = toks[0].lower(), " ".join(toks)
    if head in CONNECTIVES:
        return f"{CONNECTIVES[head]} {text}", True
    if head in PARTICIPLES:
        return f"It is {text}", False
    return f"It {text}", False


def heuristic(src: Source, concept: str, feats: list[str]) -> tuple[str, list[str]]:
    prov = [src.provenance[(concept, f)] for f in feats]
    if all(p["cv_published"] is not None for p in prov):
        return "published CV, highest first", sorted(feats, key=lambda f: (-src.provenance[(concept, f)]["cv_published"], f))
    if all(p["num_parts"] for p in prov):
        return "normalised production frequency (no published CV)", sorted(
            feats, key=lambda f: (-30 * src.provenance[(concept, f)]["prod_freq"] / src.provenance[(concept, f)]["num_parts"], f))
    return "raw production count (no CV, no denominator)", sorted(
        feats, key=lambda f: (-src.provenance[(concept, f)]["prod_freq"], f))


def select(ranked: list[str]) -> list[str]:
    n = len(ranked)
    return [ranked[round(i * (n - 1) / (CLAUSES - 1))] for i in range(CLAUSES)]


def ask(prompt: str) -> str:
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
                       "options": {"temperature": 0, "seed": READER_SEED, "num_predict": 12}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["message"]["content"].strip()


def cp_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact Clopper-Pearson interval by bisection on the binomial tails."""
    def tail_ge(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

    def tail_le(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))

    def solve(fn, target, increasing):
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if (fn(mid) < target) == increasing:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    lower = 0.0 if k == 0 else solve(tail_ge, alpha / 2, True)
    upper = 1.0 if k == n else solve(tail_le, alpha / 2, False)
    return lower, upper


def quotas(pool_by: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, int]]:
    total = sum(len(v) for fam in pool_by.values() for v in fam.values())
    src_tot = {s: sum(len(pool_by[f].get(s, [])) for f in pool_by) for s in SOURCE_ORDER}
    n = sum(FAMILY_QUOTA.values())
    want = {s: round(n * src_tot[s] / total) for s in SOURCE_ORDER}
    want["McRae"] = n - want["Feats"] - want["Hovhannisyan"]
    q = {f: {s: 0 for s in SOURCE_ORDER} for f in FAMILY_QUOTA}
    for s in ("Hovhannisyan", "Feats"):
        raw = {f: want[s] * len(pool_by[f].get(s, [])) / src_tot[s] for f in FAMILY_QUOTA}
        for f in FAMILY_QUOTA:
            q[f][s] = int(raw[f])
        left = want[s] - sum(q[f][s] for f in FAMILY_QUOTA)
        for f in sorted(FAMILY_QUOTA, key=lambda f: (-(raw[f] - int(raw[f])), list(FAMILY_QUOTA).index(f)))[:left]:
            q[f][s] += 1
    for f in FAMILY_QUOTA:
        q[f]["McRae"] = FAMILY_QUOTA[f] - q[f]["Feats"] - q[f]["Hovhannisyan"]
    return q


def main() -> int:
    src = Source("pooled3", hov_cutoff=3)
    route = json.loads((HERE / "route_four_family.json").read_text())
    pool = route["rows"]["(c) +Hovhannisyan >=3, 4 families"]["protocol|>=10"]["concepts"]
    tokens = json.loads((HERE / "token_counts.json").read_text())["counts"]
    trees = {f: r4.fp.subtree(f) for f in r4.FOUR}
    canon = Canon({w for fs in src.features.values() for f in fs for w in words(f) if w.isalpha()})
    names = set(r4.candidates(src, r4.FOUR, trees, tokens))
    fw = set().union(*r4.FAMILY_WORDS.values())

    pool_by = {f: {} for f in FAMILY_QUOTA}
    for f, cs in pool.items():
        for c in cs:
            pool_by[f].setdefault(src.source_of(c), []).append(c)
    q = quotas(pool_by)
    sample = []
    for f in FAMILY_QUOTA:
        for s in SOURCE_ORDER:
            cell = sorted(pool_by[f].get(s, []))
            random.Random(derived(f, s, "sample")).shuffle(cell)
            sample += [(f, s, c) for c in cell[:q[f][s]]]

    ident = reader_identity()
    records, private = [], []
    for fam, s, c in sample:
        u = usable(c, src.features[c], src.provenance, names, canon, "protocol", frozenset(), fw)
        how, ranked = heuristic(src, c, u["usable"])
        chosen = select(ranked)
        clauses = [render(f) for f in chosen]
        forms = {c, c + "s", c + "es"}
        single = []
        for f, (clause, authored) in zip(chosen, clauses):
            ans = ask(SINGLE.format(clue=clause))
            single.append({"named": named(ans, sorted(forms)), "answer": ans, "authored_connective": authored,
                           "relation": src.provenance[(c, f)]["relation"]})
        draws = []
        for j in range(DRAWS):
            idx = random.Random(derived(c, "draw", j)).sample(range(CLAUSES), DRAW_SIZE)
            ans = ask(SEVERAL.format(clues="\n".join(f"- {clauses[i][0]}" for i in idx)))
            draws.append({"clauses": idx, "named": named(ans, sorted(forms)), "answer": ans})
        n_single = sum(x["named"] for x in single)
        ceiling_ok = n_single <= CEILING
        floor_ok = all(d["named"] for d in draws)
        verdict = "pass" if ceiling_ok and floor_ok else (
            "fail-both" if not ceiling_ok and not floor_ok else "fail-ceiling" if not ceiling_ok else "fail-floor")
        records.append({"concept": c, "family": fam, "source": s, "heuristic": how, "usable": u["count"],
                        "single_named": n_single, "draws_named": sum(d["named"] for d in draws),
                        "verdict": verdict, "single": single, "draws": draws})
        private.append({"concept": c, "clauses": [{"feature": f, "clause": cl, "provenance": src.provenance[(c, f)]}
                                                   for f, (cl, _) in zip(chosen, clauses)]})
        print(f"{verdict:<12} {c:<12} {fam:<9} {s:<12} single {n_single}/10  draws {sum(d['named'] for d in draws)}/3",
              flush=True)

    def rate(rows):
        k, n = sum(r["verdict"] == "pass" for r in rows), len(rows)
        lo, hi = cp_interval(k, n) if n else (0, 0)
        return {"pass": k, "n": n, "rate": k / n if n else None, "ci95": [lo, hi]}

    summary = {"overall": rate(records),
               "by_source": {s: rate([r for r in records if r["source"] == s]) for s in SOURCE_ORDER},
               "by_family": {f: rate([r for r in records if r["family"] == f]) for f in FAMILY_QUOTA},
               "verdicts": {v: sum(r["verdict"] == v for r in records)
                            for v in ("pass", "fail-ceiling", "fail-floor", "fail-both")}}
    o = summary["overall"]
    summary["implied_survivors"] = {str(n): {"point": round(n * o["rate"], 1),
                                             "ci95": [round(n * o["ci95"][0], 1), round(n * o["ci95"][1], 1)]}
                                    for n in (104, 113)}
    summary["authored_connective_clauses"] = sum(x["authored_connective"] for r in records for x in r["single"])

    out = {"seed": SEED, "reader": {**ident, "temperature": 0, "seed": READER_SEED},
           "prompts": {"single": SINGLE, "several": SEVERAL}, "quotas": q,
           "sample": [{"family": f, "source": s, "concept": c} for f, s, c in sample],
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "summary": summary, "records": records}
    (HERE / "acceptance_sample.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    (HERE / "acceptance_sample_detail.json").write_text(json.dumps(private, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

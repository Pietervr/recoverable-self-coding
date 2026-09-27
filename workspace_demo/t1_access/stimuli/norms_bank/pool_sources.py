"""Can the eight families of §3.1 be filled from McRae and CSLB together? Concept-level measurement.

McRae is measured in full: family_pool.py + pool_e1.py with SOURCE=mcrae give the eligible count
per family at >= 12 features, dominant sense, after E2 and E1.

CSLB's feature file is GATED - the norms are released only on request to csladmin@csl.psychol.cam.ac.uk
and there is no public download - so its per-concept feature counts cannot be checked. What is public
is the concept list: the appendix of Devereux, Tyler, Geertzen & Randall (2014), Behavior Research
Methods 46(4), 1119-1127, supplied as Springer electronic supplementary material
(13428_2013_420_MOESM1_ESM.docx), which gives all 638 concepts, their CSLB category, and whether each
also appears in McRae.

So CSLB contributes an UPPER BOUND here: its concepts are put through the same family rules (WordNet
dominant sense, E2 over all senses) but NOT through the >= 12 feature filter, which can only remove
concepts. If a family cannot reach 16 against that upper bound, it cannot reach 16 in fact.

    .venv-build/bin/python stimuli/norms_bank/pool_sources.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nltk.corpus import wordnet as wn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import family_pool as fp  # noqa: E402

CSLB_CONCEPTS = Path.home() / "word-norms-mcrae/cslb_concepts.json"
import os

# E2 tests only the families that are actually in the bank, so the family set is a parameter.
# FAMILY_SET=eight is the pre-24-Sept design; FAMILY_SET=three is the design adopted at RSC 9b7927b.
FAMILY_SETS = {
    "eight": ["animals", "body parts", "foods", "vehicles", "materials", "clothing",
              "buildings", "occupations"],
    "three": ["animals", "foods", "vehicles"],
}
FAMILY_SET = os.environ.get("FAMILY_SET", "eight")
FAMILIES = FAMILY_SETS[FAMILY_SET]
SCENARIO = {"eight": "final_occupations", "three": "adopted_three"}[FAMILY_SET]
PER_FAMILY = 16
# The adopted design fixes totals, not a per-family 16: CONF 64 + CAL 16 + PILOT 16, plus at least one
# BACKGROUND concept per family (§3, RSC 9b7927b).
TOTAL_NEEDED = 64 + 16 + 16 + len(FAMILY_SETS["three"])


def assign(words: list[str], trees: dict) -> dict[str, list[str]]:
    """F1/F2/F4 on the dominant sense, then E2 on all senses. No F3: CSLB's features are gated."""
    out: dict[str, list[str]] = {f: [] for f in FAMILIES}
    for raw in words:
        c = raw.strip().lower()
        if not c.isalpha():
            continue                                   # multi-word concepts fail E1 anyway
        senses = wn.synsets(c, pos="n")
        if not senses or (wn.morphy(c, "n") or c) != c:
            continue
        home = [f for f in FAMILIES if senses[0] in trees[f]]
        if len(home) != 1:
            continue
        family = home[0]
        if any(set(senses) & trees[g] for g in FAMILIES if g != family):
            continue
        out[family].append(c)
    return {f: sorted(set(v)) for f, v in out.items()}


def main() -> int:
    trees = {f: fp.subtree(f) for f in FAMILIES}
    mcrae = json.loads((HERE / "pool_eligible_mcrae.json").read_text())["scenarios"][SCENARIO]
    cslb = json.loads(CSLB_CONCEPTS.read_text())
    only = assign([r["concept"] for r in cslb if not r["in_mcrae"]], trees)

    rows, short = {}, []
    for f in FAMILIES:
        m = mcrae[f]["sense1"]["after_E1"]
        bound = m + len(only[f])
        rows[f] = {"mcrae_eligible": m, "cslb_only_upper_bound": len(only[f]),
                   "pooled_upper_bound": bound, "needed": PER_FAMILY,
                   "cslb_only_words": only[f]}
        if bound < PER_FAMILY:
            short.append(f)

    out = {"note": "CSLB counts are an upper bound: no >= 12 feature filter, that file is gated",
           "cslb_concepts": len(cslb),
           "cslb_not_in_mcrae": sum(1 for r in cslb if not r["in_mcrae"]),
           "per_family": rows, "families_short_of_16": short}
    out["family_set"] = FAMILY_SET
    if FAMILY_SET == "three":
        m_total = sum(r["mcrae_eligible"] for r in rows.values())
        b_total = sum(r["pooled_upper_bound"] for r in rows.values())
        out["totals"] = {"mcrae": m_total, "pooled_upper_bound": b_total, "needed": TOTAL_NEEDED}
    (HERE / ("pool_sources.json" if FAMILY_SET == "eight" else f"pool_sources_{FAMILY_SET}.json")).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    head = f"needs {PER_FAMILY}" if FAMILY_SET == "eight" else "(totals bind, not a per-family 16)"
    print(f"{'family':>12} {'McRae':>7} {'+CSLB':>7} {'bound':>7}   {head}")
    for f in FAMILIES:
        r = rows[f]
        flag = ("" if FAMILY_SET == "three" or r["pooled_upper_bound"] >= PER_FAMILY
                else "   << CANNOT REACH 16")
        print(f"{f:>12} {r['mcrae_eligible']:>7} {r['cslb_only_upper_bound']:>7} "
              f"{r['pooled_upper_bound']:>7}{flag}")
    if FAMILY_SET == "three":
        t = out["totals"]
        print(f"\nTOTAL  McRae {t['mcrae']}   pooled upper bound {t['pooled_upper_bound']}   needed {t['needed']}"
              f"   (CONF 64 + CAL 16 + PILOT 16 + one BACKGROUND per family)")
    else:
        print(f"\n{len(short)} of {len(FAMILIES)} families cannot reach 16: {', '.join(short)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

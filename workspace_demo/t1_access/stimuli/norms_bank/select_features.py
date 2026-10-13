"""Step 2: select a concept's TEN features (owner, 13 October 2026; was twelve), spanning the sharing-count range (§3.1).

§3.1 demoted sharing count from a gate (K, withdrawn) to a SELECTION HEURISTIC: it ranks
candidates so that a concept's ten clauses span a range of evidence strength instead of
clustering. This implements that as a deterministic rule, so the selection is reproducible from
the seed and the source alone:

  - the two rarest features are taken first - they are the decisive candidates, confirmed or not
    by the naming test, which is what now decides decisiveness;
  - the remaining eight are read off the rest of the concept's features at eight evenly spaced
    positions across the sharing-count order, so the clause set spans rare to common; a concept with more usable
    features than ten still supplies exactly ten, chosen by this same deterministic rule (no randomness inside a
    concept: the seed fixes only the order over concepts);
  - a feature identical to a surface form of its own concept is dropped before selection
    ('paint' is a feature of paint), since check_clues.py rule N would reject the clause anyway.

The seed fixes an ORDER over each family's eligible concepts, not a subset (§3.1): the loop walks
the order, and pass-overs shorten the family rather than reaching further down a fixed list.

    .venv-build/bin/python stimuli/norms_bank/select_features.py [family]
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from norms_parse import Norms  # noqa: E402

SEED = 20260924
SCENARIO = "final_occupations"
CLAUSES = 10                                  # owner, 13 Oct 2026 (R052 handoff 1970a4cc): ten per concept
DECISIVE_CANDIDATES = 2


def derived_seed(*parts: object) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in (SEED, *parts)).encode()).hexdigest()[:16], 16)


def family_order(family: str, words: list[str]) -> list[str]:
    pool = sorted(words)
    random.Random(derived_seed(family, "order")).shuffle(pool)
    return pool


def select(norms: Norms, cue: str, skip: int = 0) -> list[tuple[str, int]] | None:
    """Ten (feature, sharing count) spanning the range, or None if the concept cannot supply them.

    `skip` drops the `skip` rarest non-decisive candidates, which is how §3.1's single re-selection
    is expressed: the same rule applied one step further from the rare end.
    """
    ranked = sorted(((norms.sharing[f], f) for f in norms.features[cue] if f != cue))
    if len(ranked) < CLAUSES:
        return None
    head = ranked[:DECISIVE_CANDIDATES]
    tail = ranked[DECISIVE_CANDIDATES + skip:]
    need = CLAUSES - DECISIVE_CANDIDATES
    if len(tail) < need:
        return None
    step = (len(tail) - 1) / (need - 1)
    picked = [tail[round(i * step)] for i in range(need)]
    chosen = head + picked
    if len({f for _, f in chosen}) != CLAUSES:
        return None
    return [(f, s) for s, f in chosen]


def main(argv: list[str]) -> int:
    family = argv[0] if argv else "materials"
    norms = Norms(lemmatise=True)
    pool = json.loads((HERE / "pool_eligible.json").read_text())["scenarios"][SCENARIO]
    words = pool[family]["sense1"]["words"]
    order = family_order(family, words)
    print(f"{family}: {len(words)} eligible, seeded order\n")
    for i, cue in enumerate(order, 1):
        sel = select(norms, cue)
        if sel is None:
            print(f"{i:>2}. {cue:<11} CANNOT SUPPLY {CLAUSES}")
            continue
        spare = len(norms.features[cue]) - CLAUSES
        print(f"{i:>2}. {cue:<11} ({len(norms.features[cue])} features, {spare} spare)")
        print(f"     decisive candidates: {sel[0][0]} [{sel[0][1]}], {sel[1][0]} [{sel[1][1]}]")
        print(f"     spanning:            {', '.join(f'{f} [{s}]' for f, s in sel[2:])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

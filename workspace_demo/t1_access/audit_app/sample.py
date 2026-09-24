"""Draw the sample that audits the AI reader (PREREGISTRATION_T1_model.md §3, amendment of 24 Sept 2026).

The AI reader reads the whole bank. A seeded sample of it is read additionally by two independent human
readers, and the disagreement between them bounds the AI reader's miss rate. The draw is made from the
committed audit sheets alone, before any sampled item is read and before the AI reader runs, and is
independent of which items already carry answers.

Stratified by family: within each of the eight families the sixteen concepts are shuffled with the declared
seed and the first N_CONCEPTS taken, so the sample holds the same number of concepts from every family. A
concept's twelve clauses stay whole, because the decisiveness rule ("at most two of a concept's twelve") is
a per-concept constraint and cannot be checked on a fragment. The property items (§11) do not depend on any
concept's clauses, so they are shuffled with the same seed and the first N_PROPS taken.

    python3 sample.py            # writes sample.json and prints the counts

32 concepts (4 per family) = 384 clauses, plus 40 property items = 424 items.
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import assign

HERE = Path(__file__).resolve().parent
OUT = HERE / "sample.json"
SEED = 20260924
N_CONCEPTS = 4          # per family, of 16
N_PROPS = 40            # of 100


def main():
    clues, props = assign.read(assign.CLUES), assign.read(assign.PROPS)

    by_family = defaultdict(list)
    for r in clues:
        if r["concept"] not in by_family[r["family"]]:
            by_family[r["family"]].append(r["concept"])

    rng = random.Random(SEED)
    sampled_concepts = []
    for family in sorted(by_family):
        concepts = sorted(by_family[family])
        assert len(concepts) == 16, (family, len(concepts))
        shuffled = concepts[:]
        rng.shuffle(shuffled)
        sampled_concepts.extend(sorted(shuffled[:N_CONCEPTS]))
    sampled_concepts = sorted(sampled_concepts)
    chosen = set(sampled_concepts)

    clue_ids = sorted(assign.clue_id(r) for r in clues if r["concept"] in chosen)
    assert len(clue_ids) == len(chosen) * 12, (len(clue_ids), len(chosen))

    prop_rows = sorted(props, key=lambda r: r["id"])
    order = prop_rows[:]
    rng.shuffle(order)
    prop_ids = sorted(assign.prop_id(r) for r in order[:N_PROPS])

    data = {
        "seed": SEED,
        "drawn_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": "sample audit of the AI reader; PREREGISTRATION_T1_model.md §3, amendment 2026-09-24",
        "n_concepts_per_family": N_CONCEPTS,
        "n_props": N_PROPS,
        "concepts": sampled_concepts,
        "clue_ids": clue_ids,
        "prop_ids": prop_ids,
        "n_items": len(clue_ids) + len(prop_ids),
        "pass_condition": "A human objection triggers adjudication by the author (recorded, with its reason, "
                          "and published). m = sampled items the AI reader passed that adjudication finds "
                          "should not have passed. U = exact one-sided 95% (Clopper-Pearson) upper bound on "
                          f"the miss rate from m of {len(clue_ids) + len(prop_ids)}: m <= 3 gives U <= 0.0182, "
                          "m = 4 gives U = 0.0215. U <= 0.02 freezes the bank on the AI read; U > 0.02 "
                          "reinstates the full two-reader human read of the whole bank before the freeze.",
    }
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")

    per_family = defaultdict(int)
    for c in sampled_concepts:
        per_family[c.split("/", 1)[0]] += 1
    print(f"seed {SEED}")
    print(f"concepts: {len(sampled_concepts)}  " + "  ".join(f"{k} {v}" for k, v in sorted(per_family.items())))
    print(f"clauses : {len(clue_ids)}")
    print(f"props   : {len(prop_ids)}")
    print(f"items   : {data['n_items']}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()

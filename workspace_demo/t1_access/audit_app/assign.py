"""Split the two-reader stimulus audit (PREREGISTRATION_T1_model.md §3) across human readers.

Every clause is read twice: once by ONE human reader (the R1 columns) and once by the AI reader, which
reads the whole bank (the R2 columns). The human half is divided here into N_SLOTS equal parts,
stratified by family: within each of the eight families the sixteen concepts are shuffled with a
declared seed and dealt out in blocks, so every slot gets the same number of concepts from every
family (4 each at N_SLOTS = 4, i.e. 32 concepts and 384 clauses). A concept's twelve clauses always
stay together, because "gives it away on its own" is judged against the concept's other clauses.
The property items (§11) do not depend on any concept's clauses, so they are shuffled with the same
seed and dealt out evenly (25 each at N_SLOTS = 4).

The split is made from the committed audit sheets alone, before any reader sees anything, and is
written to assignment.json (no tokens; those live in readers.local.json, which is gitignored).

    python3 assign.py            # writes assignment.json and prints the per-slot counts
"""
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / "stimuli" / "audit"
CLUES = AUDIT / "clue_audit_2026-09-15.csv"
PROPS = AUDIT / "property_audit_2026-09-15.csv"
SEED = 20260918
N_SLOTS = 4
SLOTS = [chr(ord("A") + i) for i in range(N_SLOTS)]


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def slug(text):
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def clue_id(row):
    return f"c-{slug(row['concept'])}-{int(row['index'])}"


def prop_id(row):
    return f"p-{slug(row['id'])}"


def main():
    clues, props = read(CLUES), read(PROPS)
    by_family = defaultdict(list)
    for r in clues:
        if r["concept"] not in by_family[r["family"]]:
            by_family[r["family"]].append(r["concept"])

    rng = random.Random(SEED)
    slot_of = {}
    for family in sorted(by_family):
        concepts = sorted(by_family[family])
        assert len(concepts) % N_SLOTS == 0, (family, len(concepts))
        rng.shuffle(concepts)
        k = len(concepts) // N_SLOTS
        for i, s in enumerate(SLOTS):
            for c in concepts[i * k:(i + 1) * k]:
                slot_of[c] = s

    pids = sorted(prop_id(r) for r in props)
    rng.shuffle(pids)
    prop_slot = {pid: SLOTS[i % N_SLOTS] for i, pid in enumerate(pids)}

    ids = [clue_id(r) for r in clues] + [prop_id(r) for r in props]
    assert len(ids) == len(set(ids)), "item ids collide"

    out = {"seed": SEED, "n_slots": N_SLOTS, "clue_sheet": CLUES.name, "property_sheet": PROPS.name,
           "slots": {}}
    for s in SLOTS:
        concepts = sorted(c for c, v in slot_of.items() if v == s)
        items = [clue_id(r) for r in clues if slot_of[r["concept"]] == s]
        items += sorted(pid for pid, v in prop_slot.items() if v == s)
        out["slots"][s] = {"concepts": concepts, "items": items}
    covered = [i for s in SLOTS for i in out["slots"][s]["items"]]
    assert sorted(covered) == sorted(ids), "the slots must cover every item exactly once"

    (HERE / "assignment.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for s in SLOTS:
        items = out["slots"][s]["items"]
        n_c = sum(i.startswith("c-") for i in items)
        print(f"slot {s}: {len(out['slots'][s]['concepts'])} concepts, {n_c} clauses, "
              f"{len(items) - n_c} property items")


if __name__ == "__main__":
    main()

"""Generate the planted-defect calibration sets that MEASURE an AI reader's recall
(PREREGISTRATION_T1_model.md §3, amendment of 24 Sept 2026, second entry).

With the human read removed, nothing else tells us what a reader misses. A reader's clean pass over
the bank is worth exactly as much as its measured catch rate on defects of known ground truth, so
that catch rate is measured here rather than assumed.

No model authors the defects. They are mechanical perturbations of the committed bank, which is what
keeps the drafting model's blind spots out of its own test:

  FALSE   a clause already marked decisive for concept X is re-attached to another concept Y. A
          decisive clause identifies its own concept alone, so it is false of Y, and it is a real,
          well-written clause rather than an invented howler. Ground truth: true = n. Two tiers, and
          recall is reported separately for each, because a single tier would not be informative:
            FAR   Y is in a DIFFERENT family. The ground truth is certain but the defect is obvious
                  ("a finger has a heavy metal head with a sharp wedge-shaped edge"). Recall here is
                  an upper bound: missing these is catastrophic, catching them proves little.
            NEAR  Y is a SIBLING in the same family. Much subtler, and this is the tier that matches
                  the real observed misses ("lion cubs don't have spots").

          THE NEAR TIER'S GROUND TRUTH IS NOT PURELY MECHANICAL, and must be confirmed by the author
          before any recall number uses it. The construction leans on the source clause being
          genuinely exclusive to X, which is a drafter judgement recorded in marked_decisive -- and
          checking those judgements is part of what the audit is for, so taking them on trust here
          is circular. Inspection of the first build found it bites: "spends a lot of time cleaning
          its own fur", decisive for cat, moved to wolf is arguably TRUE of a wolf, and "sits at the
          very bottom of the face", decisive for chin, moved to lip is at best debatable. A plant
          whose ground truth is wrong scores a correct reader as a miss and deflates measured recall,
          which is the one number this file exists to produce. So: the author confirms each NEAR
          plant is genuinely false of its victim, and any that is not is dropped from the set and
          recorded as dropped. Twenty items, nearly all defective -- the high-prevalence regime where
          human judgement is reliable, and the reason §3 keeps the author's adjudication after
          removing the reader pass. FAR and DECISIVE plants need no such confirmation.
  DECISIVE a clause already marked decisive for concept X stays on X with its mark removed. By the
          bank's own drafting it identifies the concept alone, and §3 allows at most two such clauses
          per concept, marked. Ground truth: decisive = y on an unmarked clause.
  CLEAN   an unmarked clause, unchanged. Ground truth: passes all three questions. These measure the
          reader's false-alarm rate, without which a high catch rate proves nothing.

The "names" failure mode is deliberately not planted. check_clues.py already rejects every plain
surface form of any bank concept and every family word, so the only residue is disguised naming --
a translation, a synonym, a pun -- which cannot be generated mechanically without a model inventing
it. That gap is recorded in §3 as a limitation rather than papered over with a weak plant.

    python3 plant.py                      # the declared set: prevalence 0.30
    python3 plant.py --prevalence 0.05    # the low-prevalence twin

Two sets at different prevalence are built on purpose. A reader that judges each item in a fresh
context should show the same recall in both; a gap between them is a low-prevalence effect in the
machine reader, which is exactly the failure that removed the human pass and must not be assumed
absent just because the reader is not a person.
"""
import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import assign

HERE = Path(__file__).resolve().parent
SEED = 20260924
N_PLANTS = 60           # 30 FALSE + 30 DECISIVE


def build(prevalence: float):
    rows = assign.read(assign.CLUES)
    decisive = [r for r in rows if r["marked_decisive"].strip().lower() == "yes"]
    plain = [r for r in rows if r["marked_decisive"].strip().lower() != "yes"]
    by_family = defaultdict(list)
    for r in rows:
        if r["concept"] not in by_family[r["family"]]:
            by_family[r["family"]].append(r["concept"])

    rng = random.Random(SEED)
    src = sorted(decisive, key=lambda r: (r["concept"], int(r["index"])))
    rng.shuffle(src)
    third = N_PLANTS // 3
    far_src, near_src, dec_src = src[:third], src[third:2 * third], src[2 * third:N_PLANTS]

    families = sorted(by_family)
    out, key = [], {}

    for n, r in enumerate(far_src):
        other = [f for f in families if f != r["family"]]
        fam = other[rng.randrange(len(other))]
        victim = sorted(by_family[fam])[rng.randrange(len(by_family[fam]))]
        pid = f"x-far-{n:03d}"
        out.append({"id": pid, "family": fam, "concept": victim, "index": r["index"],
                    "clause": r["clause"], "marked_decisive": "", "drafter_note": ""})
        key[pid] = {"type": "FALSE_FAR", "expect": {"true": "n"},
                    "source_concept": r["concept"], "attached_to": victim}

    for n, r in enumerate(near_src):
        siblings = [c for c in sorted(by_family[r["family"]]) if c != r["concept"]]
        victim = siblings[rng.randrange(len(siblings))]
        pid = f"x-near-{n:03d}"
        out.append({"id": pid, "family": r["family"], "concept": victim, "index": r["index"],
                    "clause": r["clause"], "marked_decisive": "", "drafter_note": ""})
        key[pid] = {"type": "FALSE_NEAR", "expect": {"true": "n"},
                    "source_concept": r["concept"], "attached_to": victim}

    for n, r in enumerate(dec_src):
        pid = f"x-dec-{n:03d}"
        out.append({"id": pid, "family": r["family"], "concept": r["concept"], "index": r["index"],
                    "clause": r["clause"], "marked_decisive": "", "drafter_note": ""})
        key[pid] = {"type": "DECISIVE", "expect": {"decisive": "y"},
                    "source_concept": r["concept"], "attached_to": r["concept"]}

    n_clean = max(1, round(N_PLANTS * (1 - prevalence) / prevalence))
    rng.shuffle(plain)
    for n, r in enumerate(plain[:n_clean]):
        pid = f"x-clean-{n:04d}"
        out.append({"id": pid, "family": r["family"], "concept": r["concept"], "index": r["index"],
                    "clause": r["clause"], "marked_decisive": "", "drafter_note": ""})
        key[pid] = {"type": "CLEAN", "expect": {"true": "y", "names": "n", "decisive": "n"},
                    "source_concept": r["concept"], "attached_to": r["concept"]}

    rng.shuffle(out)
    tag = f"{round(prevalence * 100):02d}"
    sheet = HERE / f"plants_audit_p{tag}.csv"
    with sheet.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "family", "concept", "index", "clause",
                                          "marked_decisive", "drafter_note",
                                          "R2_true", "R2_names", "R2_decisive", "R2_comment"])
        w.writeheader()
        for row in out:
            w.writerow({**row, "R2_true": "", "R2_names": "", "R2_decisive": "", "R2_comment": ""})

    keyfile = HERE / f"plants_key_p{tag}.json"
    keyfile.write_text(json.dumps({
        "seed": SEED,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prevalence_target": prevalence,
        "prevalence_actual": N_PLANTS / len(out),
        "n_items": len(out), "n_plants": N_PLANTS, "n_clean": n_clean,
        "sheet": sheet.name,
        "warning": "HOLD BACK. A reader that sees this file cannot measure anything.",
        "key": key,
    }, indent=1) + "\n")

    print(f"prevalence {prevalence:.2f}: {len(out)} items = {third} FAR + {third} NEAR + {N_PLANTS-2*third} DECISIVE "
          f"+ {n_clean} CLEAN  (actual {N_PLANTS/len(out):.3f})")
    print(f"  wrote {sheet.name} and {keyfile.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prevalence", type=float, default=0.30)
    build(ap.parse_args().prevalence)


if __name__ == "__main__":
    main()

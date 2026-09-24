"""Step 1a: assign normed cues to bank families by WordNet hypernym subtree, and apply E2.

Why WordNet and not the features themselves: assigning families from feature keywords was tried and
fails - "metal"/"fabric"/"material" sweep every metal object into materials, and the disjointness
rule then strips tools to 6 and vehicles to 12, below the 16 the design needs. WordNet's noun
hierarchy is an independent, permissively licensed taxonomy built for exactly this.

FILTERS, in order (each counted separately so the attrition is visible):
  F1 pos_cue = noun in the norms, and the cue has at least one WordNet noun sense;
  F2 the cue is its own WordNet base form (morphy) - 'arms' and 'antlers' are inflections of cues
     already in the pool, not separate concepts;
  F3 at least 12 distinct features in the norms;
  F4 the cue has a noun sense inside the family's subtree (hyponym + instance_hyponym closure);
  E2 no noun sense of the cue lies inside ANOTHER family's subtree. This is the existing E2 -
     "a word naming a member of another bank family" - computed from the taxonomy instead of a
     hand-written collision list, and it is per scenario, because the family set changes.
     E2 always tests ALL senses: the prompt scan cannot tell senses apart, so 'duck' is ambiguous
     between animals and foods whichever sense put it in the pool.

MEMBERSHIP IS DOMINANT-SENSE (`sense1`), decided by R052 on 24 Sept: the cue's FIRST WordNet noun
synset (WordNet orders senses by frequency) must lie in the subtree, and cues in one family sharing
that synset collapse to the alphabetically first ('ax'/'axe', 'bike'/'bicycle' are one concept, not
two). F4 on ALL senses (`any_sense`) is still computed and reported alongside, because it is what
the first feasibility pass measured, but it admits members no reader would accept - 'bark' is a
sailing ship, 'secretary' a writing desk, 'kettle' a kettledrum - and the bank is being rebuilt
precisely so that nothing in it rests on our judgement. sense1 only tightens F4; it relaxes nothing.

E1 (the answer-context form ' x' is a single token) is NOT applied here: it needs the Qwen3.6
tokenizer, which lives in the upstream venv. pool_e1.py takes this file's output and applies it.

Superordinate cues ('vehicle', 'furniture', 'instrument') pass every rule but name the category
rather than a concept; they are flagged in the output, not removed.

The output also carries a CEILING list per family: every single-word noun lemma in the subtree that
is a base form and passes E2, whether or not Buchanan norms it. After E1 that is the largest family
any human norm set could ever supply, so it separates "Buchanan is short here" from "no norm set can
fix this, the tokenizer is the constraint".

    .venv-build/bin/python stimuli/norms_bank/family_pool.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from nltk.corpus import wordnet as wn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from norms_parse import Norms  # noqa: E402

MIN_FEATURES = int(os.environ.get("MIN_FEATURES", "12"))   # the §3 threshold, swept for sensitivity
PER_FAMILY = 16

# One documented root set per family, chosen to match the family's ordinary meaning, not to
# maximise the count. The subtree is the hyponym + instance_hyponym closure of these synsets.
ROOTS = {
    "animals": ["animal.n.01"],
    "body parts": ["body_part.n.01"],
    "foods": ["food.n.01", "food.n.02"],      # food.n.02 (solid food) is not under food.n.01
    "vehicles": ["vehicle.n.01"],
    "tools": ["tool.n.01"],
    "instruments": ["musical_instrument.n.01"],
    "materials": ["material.n.01"],
    "countries": ["country.n.02"],
    "clothing": ["clothing.n.01"],
    "furniture": ["furniture.n.01"],
    # measured only as possible replacements for a family that cannot reach 16 (see FEASIBILITY.md)
    "weapons": ["weapon.n.01"],
    "buildings": ["building.n.01"],
    "trees": ["tree.n.01"],
    "containers": ["container.n.01"],
    "utensils": ["utensil.n.01"],
    "appliances": ["appliance.n.01"],
    "toys": ["toy.n.01"],
    "sports equipment": ["sports_equipment.n.01"],
    "natural features": ["geological_formation.n.01", "body_of_water.n.01"],
    "people": ["worker.n.01"],
    # worker.n.01 alone excludes doctor, nurse and teacher (professional.n.01 is a sibling branch
    # under adult.n.01, not a hyponym of worker), so the same family is measured with both roots.
    "occupations": ["worker.n.01", "professional.n.01"],
}
FIXED = ["animals", "body parts", "foods", "vehicles", "tools", "instruments", "materials"]
SCENARIOS = {
    "baseline": FIXED + ["countries"],
    "clothing": FIXED + ["clothing"],
    "furniture": FIXED + ["furniture"],
}
# Each replacement candidate is also measured against the five families that clear 16 on their own
# plus clothing, i.e. as a stand-in for tools or instruments. One candidate at a time: the pair
# interaction through E2 is small (<= 3 words in the measured scenarios above).
CORE = ["animals", "body parts", "foods", "vehicles", "materials", "clothing"]
ALTERNATES = ["furniture", "weapons", "buildings", "trees", "containers", "utensils",
              "appliances", "toys", "sports equipment", "tools", "instruments",
              "natural features", "people", "occupations"]
SCENARIOS.update({f"alt_{a}": CORE + [a] for a in ALTERNATES})

# The eight-family design as R052 settled it on 24 Sept: the six families that stand on their own,
# buildings as the first replacement, and one more to be chosen. Each candidate is measured in the
# full eight, so the pair interaction between buildings and the candidate through E2 is included.
FINALISTS = ["natural features", "people", "occupations"]
SCENARIOS.update({f"final_{c}": CORE + ["buildings", c] for c in FINALISTS})
VARIANTS = ("any_sense", "sense1")


def subtree(family: str) -> set:
    out = set()
    for name in ROOTS[family]:
        s = wn.synset(name)
        out.add(s)
        out |= set(s.closure(lambda x: x.hyponyms() + x.instance_hyponyms()))
    return out


def main() -> int:
    norms = Norms(lemmatise=True)
    trees = {f: subtree(f) for f in ROOTS}
    supers = {l.name().lower() for f in ROOTS for r in ROOTS[f] for l in wn.synset(r).lemmas()}

    f1 = [c for c in norms.nouns() if wn.synsets(c, pos="n")]
    f2 = [c for c in f1 if (wn.morphy(c, "n") or c) == c]
    f3 = [c for c in f2 if len(norms.features[c]) >= MIN_FEATURES]
    senses = {c: wn.synsets(c, pos="n") for c in f3}

    lemmas = {f: sorted({l.name().lower() for syn in trees[f] for l in syn.lemmas()
                         if l.name().isalpha() and (wn.morphy(l.name().lower(), "n") or l.name().lower()) == l.name().lower()})
              for f in ROOTS}

    members: dict[str, dict[str, list[str]]] = {}
    synset_key: dict[str, dict[str, str]] = {}
    for fam in ROOTS:
        any_s = [c for c in f3 if set(senses[c]) & trees[fam]]
        s1 = [c for c in f3 if senses[c][0] in trees[fam]]
        members[fam] = {"any_sense": any_s, "sense1": s1}
        # Cues sharing a dominant synset are ONE concept. They are not collapsed here: pool_e1.py
        # collapses after E1, so a synset is only lost when EVERY one of its cues fails E1. Doing it
        # the other way round made the count non-monotonic in MIN_FEATURES - at >= 10 'bungalow'
        # entered, took the representative slot from 'cottage' alphabetically, failed E1 at 2 tokens
        # and cost buildings a concept it had at >= 12.
        synset_key[fam] = {c: senses[c][0].name() for c in s1}

    out = {
        "source": {"xlsx": str(norms.xlsx), "sha256": norms.sha256, "rows": norms.n_rows,
                   "distinct_cues": len(norms.all_cues), "single_word_cues": len(norms.features)},
        "feature_identity": {"column": "feature", "lemmatised": norms.lemmatised,
                             "lemmatiser": "nltk.stem.wordnet.WordNetLemmatizer",
                             "rule": "lowercase, strip, noun lemma, else verb lemma",
                             "distinct_feature_strings": len(norms.sharing),
                             "cues_at_min_features": len(norms.with_features(MIN_FEATURES))},
        "wordnet_version": wn.get_version(),
        "min_features": MIN_FEATURES, "per_family": PER_FAMILY, "roots": ROOTS,
        "attrition": {"F1_noun_cues_with_wordnet_noun_sense": len(f1),
                      "F2_base_form": len(f2),
                      f"F3_at_least_{MIN_FEATURES}_features": len(f3)},
        "in_subtree_before_E2": {f: {v: len(members[f][v]) for v in VARIANTS} for f in ROOTS},
        "ceiling_note": "every single-word base-form noun lemma in the subtree, normed or not, after E2",
        "sense1_synset_key": synset_key,
        "scenarios": {},
    }

    for name, families in SCENARIOS.items():
        rows: dict = {}
        for fam in families:
            others = [g for g in families if g != fam]
            rows[fam] = {}
            for variant in VARIANTS:
                keep, dropped = [], []
                for c in sorted(members[fam][variant]):
                    clash = [g for g in others if set(senses[c]) & trees[g]]
                    (dropped if clash else keep).append({"word": c, "also_in": clash} if clash else c)
                concepts = ({synset_key[fam][w] for w in keep} if variant == "sense1"
                            else set(keep))
                rows[fam][variant] = {
                    "in_subtree": len(members[fam][variant]),
                    "after_E2": len(concepts),
                    "after_E2_words": len(keep),
                    "superordinate_in_pool": sorted(w for w in keep if w in supers),
                    "words": keep,
                    "synset_key": {w: synset_key[fam][w] for w in keep} if variant == "sense1" else {},
                    "excluded_E2": dropped,
                }
            ceiling = []
            for c in lemmas[fam]:
                sc = wn.synsets(c, pos="n")
                if sc and not any(set(sc) & trees[g] for g in others):
                    ceiling.append(c)
            rows[fam]["ceiling"] = {"after_E2": len(ceiling), "words": ceiling}
        out["scenarios"][name] = rows

    suffix = "" if MIN_FEATURES == 12 else f"_min{MIN_FEATURES}"
    (HERE / f"pool_wordnet{suffix}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    print(f"WordNet {wn.get_version()}   norms sha256 {norms.sha256[:12]}...   "
          f"features LEMMATISED ({len(norms.sharing)} distinct)")
    print(f"F1 noun cues with a WordNet noun sense: {len(f1)}")
    print(f"F2 base form (not an inflection):       {len(f2)}")
    print(f"F3 with >= {MIN_FEATURES} features:              {len(f3)}")
    for name, families in SCENARIOS.items():
        print(f"\n-- scenario {name} --            any_sense          sense1")
        for fam in families:
            a, s = (out["scenarios"][name][fam][v] for v in VARIANTS)
            mark = "" if s["after_E2"] >= PER_FAMILY else "   << sense1 below 16"
            print(f"{fam:>12}: subtree {a['in_subtree']:>4} -> E2 {a['after_E2']:>4}"
                  f"   |  subtree {s['in_subtree']:>4} -> E2 {s['after_E2']:>4}{mark}")
    print(f"\n-> {HERE / f'pool_wordnet{suffix}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

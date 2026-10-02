"""Usable features of a concept under §3.1, before any selection: what eligibility must be counted on.

Codex's finding 3 (RSC 99277aa): family_pool.py's F3 counted a concept's RAW features, so every count it gave was
a ceiling. A concept is eligible only with >= 12 USABLE features (§3.1: "the threshold is the clause count
restated"), so the count is taken after the rules below. Each rule is applied in this order and its effect is
logged per concept, so the attrition can be read rather than trusted.

  T  taxonomic rows go: the source's own BR_Label is `taxonomic` (an_animal, a_mammal, eg_-_dump). §3.1: "McRae's
     taxonomic features are family words by construction and rule F removes them, consistently: CV_No_Tax is
     blank for exactly those rows." Feats uses the same coding.
  F  a feature containing a literal family word of the adopted families (animal, food, vehicle, and plurals)
     goes, since its clause would fail check_clues.py rule F.
  N  a feature naming its own concept (the cue or a plural) goes - rule N.
  X  a feature naming another bank concept goes - rule X. The bank is not selected yet, so the comparison set is
     every candidate concept that passes WordNet membership, E2 and E1 in the adopted families. The real bank is
     a subset of that, so this rule removes at least as much as it will at build time: counts are conservative
     with respect to X, and X's own cost is reported separately.
  P  proper nouns and brand names go (§3.1): a word in the label that begins with a capital letter. The common
     nouns the norms happen to write in capitals are listed in COMMON_CAPITALS and are NOT removed - that list is
     the whole of the exception, and the output prints every capitalised label with its verdict.
  M  merging (§3.1). Each feature becomes a set of words (split on '_'). Words are canonicalised so that a shared
     Snowball (Porter2) stem OR a WordNet derivational link puts two words in one class. Features whose canonical
     word sets are EQUAL coalesce; a feature whose set is a strict SUBSET of another's merges into the more
     specific one (has_wheels into has_4_wheels; beh_-_eats into beh_-_eats_peanuts). The usable count is the
     number of distinct maximal canonical sets that remain.

The MINIMAL tier reproduces Codex's screen exactly - rule F plus subsumption on raw lowercase word sets, nothing
else - so the two measurements can be checked against each other before the full rules are read.
"""

from __future__ import annotations

import re
from functools import lru_cache

FAMILY_WORDS = {"animal", "animals", "food", "foods", "vehicle", "vehicles"}
# Words the norms write with a capital that are not proper nouns or brands. Declared, and the only exception.
COMMON_CAPITALS = {"A", "C", "Y", "CD", "CD's", "AM", "FM", "UFO", "NaCl"}
_WORD = re.compile(r"[A-Za-z][A-Za-z'.]*")


def words(feature: str) -> list[str]:
    """Underscore-separated tokens, lowercased, punctuation stripped; '-' kept (it marks beh_-_ / eg_-_)."""
    out = []
    for t in feature.split("_"):
        t = t.strip().strip("()\"'").lower()
        if t:
            out.append(t)
    return out


def name_words(feature: str) -> set[str]:
    """Alphabetic words for name matching, so 'bought/sold' or '(dried)' cannot hide a name."""
    return {w.lower().strip("'.") for w in _WORD.findall(feature.replace("_", " ").replace("/", " "))}


def surface(name: str) -> set[str]:
    return {name, name + "s", name + "es"}


def proper_words(feature: str) -> list[str]:
    toks = [t for t in re.split(r"[_/ ]", feature) if t]
    hits = []
    for t in toks:
        core = t.strip("()\"")
        if core and core[0].isupper() and core not in COMMON_CAPITALS:
            hits.append(core)
    return hits


@lru_cache(maxsize=1)
def _stemmer():
    from nltk.stem.snowball import SnowballStemmer
    return SnowballStemmer("english")


class Canon:
    """Word classes under shared Porter2 stem OR WordNet derivational link, over a fixed vocabulary."""

    def __init__(self, vocabulary: set[str]):
        from nltk.corpus import wordnet as wn
        stem = _stemmer().stem
        parent = {w: w for w in vocabulary}

        def find(w):
            while parent[w] != w:
                parent[w] = parent[parent[w]]
                w = parent[w]
            return w

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                lo, hi = sorted((ra, rb))
                parent[hi] = lo

        by_stem: dict[str, str] = {}
        for w in sorted(vocabulary):
            if not w.isalpha():
                continue
            s = stem(w)
            if s in by_stem:
                union(by_stem[s], w)
            else:
                by_stem[s] = w
        # A derivational link is followed only from the word's OWN lemmas (the word or its WordNet base form),
        # never from its synonyms in a synset: following synonyms chained unrelated words through polysemy
        # (bread ~ cabbage ~ sugar, all slang for money) into one 440-word class.
        for w in sorted(vocabulary):
            if not w.isalpha():
                continue
            # A base form counts only if it is a regular inflection (same Porter2 stem) or one of WordNet's own
            # irregular exceptions (bitten->bite, told->tell, is->be). Otherwise morphy's suffix rules over-reach:
            # 'bees' strips to the verb 'be' and would join bee to be/is/are.
            base = {w}
            for pos in ("n", "v", "a", "r"):
                b = wn.morphy(w, pos)
                if b and (stem(b) == stem(w) or b in wn._exception_map[pos].get(w, [])):
                    base.add(b)
            for syn in wn.synsets(w):
                for lem in syn.lemmas():
                    if lem.name().lower() not in base:
                        continue
                    for d in lem.derivationally_related_forms():
                        dn = d.name().lower()
                        if dn in vocabulary and dn != w:
                            union(w, dn)
        self._find = find
        self.vocabulary = vocabulary

    def __call__(self, w: str) -> str:
        return self._find(w) if w in self.vocabulary else w


def maximal_sets(sets: dict[str, frozenset]) -> tuple[list[str], dict[str, str]]:
    """Coalesce equal sets, absorb strict subsets. Returns the kept representatives and what merged into what."""
    by_set: dict[frozenset, list[str]] = {}
    for f, s in sets.items():
        by_set.setdefault(s, []).append(f)
    distinct = list(by_set)
    keep, merged = [], {}
    for s in distinct:
        rep = sorted(by_set[s])[0]
        bigger = [t for t in distinct if s < t]
        if bigger:
            target = sorted(sorted(by_set[t])[0] for t in bigger)[0]
            for f in by_set[s]:
                merged[f] = target
        else:
            keep.append(rep)
            for f in sorted(by_set[s])[1:]:
                merged[f] = rep
    return sorted(keep), merged


def usable(concept: str, feats: set[str], provenance: dict, bank_names: set[str], canon: Canon | None,
           tier: str, skip: frozenset = frozenset()) -> dict:
    """The usable features of one concept under a tier: 'raw', 'minimal' or 'protocol'.

    `skip` drops named protocol rules (T, N, X, P, and D for the stem/derivation canonicalisation) - used only to
    measure what each rule costs, never to build a bank."""
    log: dict[str, list] = {k: [] for k in ("T", "F", "N", "X", "P")}
    live = set(feats)
    if tier == "raw":
        return {"usable": sorted(live), "count": len(live), "log": log, "merged": {}}
    if tier == "protocol" and "T" not in skip:
        for f in sorted(live):
            if provenance[(concept, f)]["relation"] == "taxonomic":
                log["T"].append(f)
        live -= set(log["T"])
    for f in sorted(live):
        if set(words(f)) & FAMILY_WORDS:
            log["F"].append(f)
    live -= set(log["F"])
    if tier == "protocol":
        own = surface(concept)
        others = {s for n in bank_names if n != concept for s in surface(n)}
        for f in sorted(live):
            nw = name_words(f)
            if nw & own and "N" not in skip:
                log["N"].append(f)
            elif nw & others and "X" not in skip:
                log["X"].append((f, sorted(nw & others)))
        live -= set(log["N"]) | {f for f, _ in log["X"]}
        for f in sorted(live):
            hits = proper_words(f) if "P" not in skip else []
            if hits:
                log["P"].append((f, hits))
        live -= {f for f, _ in log["P"]}
        sets = {f: frozenset((w if "D" in skip else canon(w)) for w in words(f)) for f in live}
    else:
        sets = {f: frozenset(words(f)) for f in live}
    keep, merged = maximal_sets(sets)
    return {"usable": keep, "count": len(keep), "log": log, "merged": merged}

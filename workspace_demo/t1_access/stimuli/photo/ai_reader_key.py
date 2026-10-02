"""AI image-reader qualification, revision 2: the answer KEY (held by the orchestrator, never sent to the reader).
Framework §8.2; Codex RSC cf3e49e; R052 handoff 7f25830e repairs 2, 3 and 7. Needs WordNet:

    .venv-build/bin/python stimuli/photo/ai_reader_key.py          # writes ai_reader_qual_key.json

ADMISSIBLE ALIASES, per item, frozen before any answer and sense-specific by construction (every source is the
concept's own THINGS synset; homonyms are outside the frame):
  - the THINGS Word, the concept id with '_' as space, and the WordNet synonyms THINGS lists for that concept;
  - each one's VALIDATED plural: candidate plurals of the last word by English spelling rules plus WordNet's noun
    exception list, kept only where WordNet's lemmatiser (_morphy, every base it allows) maps the candidate back to that word as a noun
    (knives -> knife and leaves -> leaf are kept; nothing like 'knive', 'leave' or 'specy' can arise);
  - nothing else: no stemming, no substring credit, no hand-added alias, and no alias is ever added after an answer.
NORMALISATION, the same for keys and answers (`ai_reader_score.normalise`): Unicode NFKC, lower case, curly quotes
straightened, surrounding whitespace and . , ; : ! ? " ' ( ) removed, hyphens and underscores read as spaces,
whitespace collapsed, one leading article (a, an, the) dropped. The noun-phrase contract makes the 37 concepts whose
accepted forms are all multi-word nameable (repair 1): 'road sweeper' is a valid whole answer.

The key also carries each item's human norm (recognizability, close, N-ratings, N-correct, most common label), the
concept's THINGS sense definition and synset (for referral records, repair 7), and the reserved concept list: the 300
qualification concepts are excluded from every later development and formal draw (`reserved_concepts`;
`assert_not_reserved` for later draw code).
"""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_frame as F  # noqa: E402

KEY = HERE / "ai_reader_qual_key.json"
ARTICLES = ("a ", "an ", "the ")


def normalise(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    s = s.strip(" .,;:!?\"'()")
    s = " ".join(s.split())
    for a in ARTICLES:
        if s.startswith(a):
            s = s[len(a):]
            break
    return s


def plurals(word: str) -> set[str]:
    from nltk.corpus import wordnet as wn
    # ONE regular plural by English orthography (morphy alone is too lenient: it maps 'gravys' to 'gravy'), plus
    # the irregular plurals WordNet's noun exception list records for the word; each must lemmatise back to it.
    if word.endswith(("s", "x", "z", "ch", "sh")):
        regular = word + "es"
    elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        regular = word[:-1] + "ies"
    else:
        regular = word + "s"
    exc = wn._exception_map["n"]                       # WordNet noun.exc: inflected form -> base forms
    irregular = {p for p, bases in exc.items() if word in bases}
    # A word already ending in a plural -s (scissors, shorts, clothes, drawers) gets no regular plural: WordNet's
    # lemmatiser would accept 'scissorses'. Singular -s endings (glass, bus, iris, gas, lasso...) keep theirs.
    plural_only = word.endswith("s") and not word.endswith(("ss", "us", "is", "as", "os"))
    cands = ({regular} if not irregular and not plural_only else set()) | irregular
    return {p for p in cands if p != word and word in wn._morphy(p, wn.NOUN)}   # all bases WordNet allows


def aliases(names: set[str]) -> tuple[list[str], dict]:
    base = {normalise(n) for n in names if normalise(n)}
    out, infl = set(base), {}
    for b in base:
        head, _, last = b.rpartition(" ")
        for p in plurals(last):
            v = normalise((head + " " if head else "") + p)
            out.add(v)
            infl.setdefault(b, []).append(v)
    return sorted(out), {k: sorted(v) for k, v in infl.items()}


def assert_not_reserved(concepts) -> None:
    """For any later development or formal draw: none of its concepts may be a qualification concept."""
    reserved = set(json.loads(KEY.read_text())["reserved_concepts"])
    clash = sorted(set(concepts) & reserved)
    if clash:
        raise SystemExit(f"reserved qualification concepts in a later draw: {clash}")


def main() -> int:
    d = F.draw()
    items = {}
    for x in d["chosen"]:
        c, im = x["c"], x["im"]
        al, infl = aliases(F.concept_names(c, x["concept"]))
        items[x["item"]] = {
            "concept": x["concept"], "word": c["Word"], "display_label": im["display_label"],
            "synset": c["WordNet ID"], "sense": c["Definition (from WordNet, Google, or Wikipedia)"],
            "aliases": al, "validated_plurals": infl, "multiword_only": all(" " in a for a in al),
            "human": {"recognizability": x["rec"], "recognizability_close": x["close"], "n_ratings": x["n_ratings"],
                      "n_correct": x["n_correct"], "most_common_label": im["recognizability_most-common-label"]},
            "stratum": x["stratum"], "easy": x["easy"], "requests": x["requests"]}
    key = {"note": "The orchestrator's key for the AI-reader qualification (revision 2). Never sent to the reader.",
           "seed": F.SEED, "frame_size": d["n_frame"], "cuts": d["cuts"], "exclusion_counts": d["exclusion_counts"],
           "exclusions": d["exclusions"], "reserved_concepts": sorted(v["concept"] for v in items.values()),
           "normalisation": normalise.__doc__ or "see ai_reader_score.normalise", "items": items}
    KEY.write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n")
    easy = sum(v["easy"] for v in items.values())
    mw = sum(v["multiword_only"] for v in items.values())
    print(f"frame {d['n_frame']}, excluded {d['exclusion_counts']}; 300 items, easy {easy}, multi-word-only {mw}; "
          f"cuts {[round(t, 9) for t in d['cuts']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

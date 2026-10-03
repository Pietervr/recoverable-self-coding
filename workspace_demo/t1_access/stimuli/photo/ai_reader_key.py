"""AI image-reader qualification: the answer KEY (held by the orchestrator, never sent to the reader) - its forms as
revision 4 built them, and from revision 12 the SHARED MATCHING RULE (`names_concept`). Framework §8.2; Codex RSC
cf3e49e and 7048bb8; R052 handoffs 7f25830e repairs 2, 3, 7, 742146ad group 2 and ff264083 (revision 12). Needs
WordNet 3.0 (the corpus zip is pinned by sha256 below):

    .venv-build/bin/python stimuli/photo/ai_reader_key.py          # writes ai_reader_qual_key.json

CANDIDATE NAMES, per item: the THINGS Word, the concept id with '_' as space, and the WordNet synonyms THINGS lists
for that concept (`WordNet Synonyms`; Python-literal residue in that column - u"...", [ ] - is stripped, e.g.
spider_web's u"spider's_web"]). Each candidate's source fields are recorded (`alias_sources`). Ten selected concepts
carry no WordNet id: their candidates are the Word, the id and any synonyms THINGS lists for them (five synonym bases
across three of the ten), S3 and S4 cannot apply without a recorded synset, and their sense rests on the THINGS
definition (recorded per item in `sense_rationale`).

THE SPECIFICITY RULE (framework 8.2, Codex RSC 7048bb8, frozen before any answer). Canonical names - the Word, the
id, and their spelling variants that differ only by spaces - and their valid inflections always stand. Any other
candidate is EXCLUDED from the primary gate, with its inflections, when
  S1  it equals a canonical name, or an inflection of one, of ANOTHER released THINGS concept (all 1,854);
  S2  it is a candidate of another selected target;
  S3  WordNet relates one of its noun senses to the target synset as a broader class (hypernym closure), a part
      (part/member/substance meronym) or a whole (holonym);
  S4  its FIRST-LISTED WordNet noun sense differs from the recorded target synset - a predicate on WordNet 3.0's
      sense order, not a measurement of dominant usage among these images or readers;
unless the pair is in EQUIVALENCES, a documented same-referent equivalence frozen here with its rationale (13 pairs,
roll/bun among them). An excluded candidate stays in the key as `excluded_aliases` with its rule; it can never be
added back after an answer. S1-S3 are Codex's rule; S4 extends it to the 'bench' case for words that are not
themselves released concepts (e.g. lighter/'light', sword/'brand').

INFLECTIONS. Only plurals, only of the head noun: the last token, or in an 'X of Y' phrase the token before 'of'
('pairs of scissors', never 'pair of scissorses'). A head that ends in -s and is not a -ss/-us/-is/-as/-os word gets
no generated plural. That suffix rule is not a grammatical test: it is qualified by an audit BOUNDED TO THIS CANDIDATE
SET - every -s head among the 300 items' candidates is listed in the key (`inflection_audit`: 13 heads the rule treats
as plural-only, among them English plural nouns such as scissors, shorts and drawers but also the Latin binomial part
'latrans'; 19 it treats as singular), reviewed, and frozen by test. It is not a general grammatical validator. Otherwise
one regular plural by English orthography, or WordNet's irregular plurals (noun.exc) when it lists any; every
candidate must lemmatise back to the head (`_morphy`). No stemming and no hand-added alias in the key's forms.

THE SHARED MATCHING RULE (revision 12; the owner's decision of 3 October 2026, framework §8.2), `names_concept`, the
one function the qualification scorer and the image audit's scorer both call, over the frozen forms above. After
`normalise` (and, failing (i)-(ii) on the answer as given, with each token singularised by this inflection policy read
backwards: a token is replaced by the base whose generated plural it is), an answer names the concept when ANY of
  (i)   whole:    the whole answer equals an admitted form;
  (ii)  contains: an admitted form occurs in the answer as a whole-word phrase ('toilet paper roll', 'spool of
                  thread', 'air conditioning unit'); no head-noun guard, so the target as a modifier of another
                  object ('paint brush' for paint) passes - a disclosed residual, and for the audit's question (does
                  the stimulus evoke the concept) such an answer is evidence that it does;
  (iii) hyponym:  a noun sense of the answer's head lemma - the LONGEST whole-word suffix WordNet 3.0 knows as a noun
                  lemma - is a strict, transitive hyponym of the recorded target synset ('sneakers' -> sneaker ->
                  shoe.n.01 counts; 'holiday greeting card' -> greeting card, a hypernym of christmas card, does not;
                  'stretcher' for gurney, 'drums' for bongo, 'marlin' for swordfish do not). An item without a recorded
                  synset cannot pass by (iii).
An answer equal to one of the item's excluded forms never passes (S1-S4 stand), and neither does an answer equal to
the canonical name or an inflection of ANOTHER released THINGS concept (S1's population: 'alpaca' for llama, 'belt
buckle' for buckle - the reader named that concept). The admitted forms are unchanged: no alias is added, and
everything else is a referral decided by the owner with the picture.

NORMALISATION, the same for keys and answers (`normalise`): Unicode NFKC, lower case, curly quotes straightened,
hyphens and underscores read as spaces, whitespace collapsed, surrounding . , ; : ! ? " ' ( ) removed, one leading
article (a, an, the) dropped. Concepts whose admissible forms are all multi-word stay nameable (repair 1; revision
12's prompt asks for one or two words): 29 before the specificity rule, 33 after it (roulette_wheel, fire_pit,
rocking_chair and washing_machine lost their only one-word candidates); 'road sweeper' is a valid whole answer.

The key also carries each item's human norm, the THINGS sense and synset (for referral records), the source pins, the
rule's audit counts and the reserved concept list (`reserved_concepts`; `assert_not_reserved` for later draw code).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_frame as F  # noqa: E402

KEY = HERE / "ai_reader_qual_key.json"
ARTICLES = ("a ", "an ", "the ")
WORDNET_ZIP = Path.home() / "nltk_data" / "corpora" / "wordnet.zip"
WORDNET_PIN = {"version": "3.0", "zip_sha256": "cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59"}
SINGULAR_S = ("ss", "us", "is", "as", "os")
# Same-referent equivalences that stand despite S1-S4: (target concept, alias) -> rationale.
EQUIVALENCES = {
    ("roll", "bun"): "WordNet puts bun and roll in one synset (small rounded bread); THINGS defines both as a small "
                     "bread; Codex named roll/bun as an equivalence that may stand (S1, S2)",
    ("stomach", "abdomen"): "the target synset is abdomen.n.01 itself; 'abdomen' also names the abdominal cavity (S3)",
    ("cilantro", "coriander"): "coriander.n.03 is the target synset (the herb leaves); British usage names the leaves "
                               "coriander (S3 whole, S4)",
    ("cilantro", "chinese parsley"): "a lemma of the target synset coriander.n.03, naming the same leaves (S3, S4)",
    ("possum", "opossum"): "the full form of the target's own name, opossum.n.02 (S4: dominant sense phalanger)",
    ("chickpea", "garbanzo"): "dominant sense is the seed chickpea.n.01, the same object a picture shows (S4)",
    ("doorknocker", "knocker"): "the ordinary short name of the door device; the dominant sense (Yiddish, a boaster) is "
                                "not a visible object (S4)",
    ("cash_machine", "atm"): "the ordinary name; the dominant sense (a pressure unit) is not a visible object (S4)",
    ("bobsled", "bobsleigh"): "a spelling variant; dominant bobsled.n.01 is the same kind of sled (S4)",
    ("gravestone", "headstone"): "same object; the dominant sense (an arch keystone) is a WordNet artefact (S4)",
    ("column", "pillar"): "same architectural object; the dominant sense is abstract (a principle) (S4)",
    ("spider_web", "spider's web"): "the possessive spelling of the canonical name 'spider web' (S4 only because THINGS "
                                    "chose spider_web.n.02); the source column carried it as u\"spider's_web\"]",
    ("artichoke", "globe artichoke"): "the specific name of the same vegetable head; the canonical 'artichoke' is "
                                      "equally the plant's name (S3 whole, S4)",
}


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


def synonyms(field: str) -> list[str]:
    """THINGS 'WordNet Synonyms', with Python-literal residue (u"...", u'...', [ ]) stripped."""
    out = []
    for s in field.split(","):
        s = s.strip().strip("[]").strip()
        s = re.sub(r"^u(['\"])(.*)\1?$", r"\2", s).strip("'\"").strip()
        if s:
            out.append(s.replace("_", " ").lower())
    return out


def check_wordnet() -> dict:
    from nltk.corpus import wordnet as wn
    got = {"version": wn.get_version(), "zip_sha256": hashlib.sha256(WORDNET_ZIP.read_bytes()).hexdigest()}
    if got != WORDNET_PIN:
        raise SystemExit(f"refused: WordNet differs from the pin: {got}")
    return got


def plural_only(word: str) -> bool:
    return word.endswith("s") and not word.endswith(SINGULAR_S)


def plurals(word: str) -> set[str]:
    from nltk.corpus import wordnet as wn
    if plural_only(word):
        return set()
    exc = wn._exception_map["n"]                       # WordNet noun.exc: inflected form -> base forms
    irregular = {p for p, bases in exc.items() if word in bases}
    if irregular:
        cands = irregular
    elif word.endswith(("s", "x", "z", "ch", "sh")):
        cands = {word + "es"}
    elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        cands = {word[:-1] + "ies"}
    else:
        cands = {word + "s"}
    return {p for p in cands if p != word and word in wn._morphy(p, wn.NOUN)}


def inflections(phrase: str) -> list[str]:
    """Plurals of the head noun: the token before ' of ' in an 'X of Y' phrase, else the last token."""
    toks = phrase.split()
    i = toks.index("of") - 1 if "of" in toks[1:] else len(toks) - 1
    return sorted(normalise(" ".join(toks[:i] + [p] + toks[i + 1:])) for p in plurals(toks[i]))


def candidates(c: dict, uid: str) -> dict:
    """{normalised candidate: [source fields]}."""
    out = {}
    for n, src in [(c["Word"], "Word"), (uid.replace("_", " "), "uniqueID")] + \
                  [(s, "WordNet Synonyms") for s in synonyms(c["WordNet Synonyms"])]:
        k = normalise(n)
        if k:
            out.setdefault(k, [])
            if src not in out[k]:
                out[k].append(src)
    return out


def released_names(concepts: dict) -> dict:
    """{canonical name or inflection: {concept ids}} over every released concept (S1)."""
    names = {}
    for uid, c in concepts.items():
        for n in {normalise(c["Word"]), normalise(uid.replace("_", " "))}:
            for f in [n] + inflections(n):
                names.setdefault(f, set()).add(uid)
    return names


def specificity(uid: str, c: dict, alias: str, canon: set, released: dict, others: dict) -> list[str]:
    """The rules (S1-S4) an alias trips; [] when it stands. `others`: {alias: {other selected targets}}."""
    from nltk.corpus import wordnet as wn
    if alias in canon or alias.replace(" ", "") in {k.replace(" ", "") for k in canon}:
        return []
    why = []
    hit = released.get(alias, set()) - {uid}
    if hit:
        why.append("S1:" + ",".join(sorted(hit)))
    if others.get(alias, set()) - {uid}:
        why.append("S2:" + ",".join(sorted(others[alias] - {uid})))
    sid = c["WordNet ID"].strip()
    if sid:
        T = wn.synset_from_pos_and_offset("n", int(sid[1:]))
        senses = wn.synsets(alias.replace(" ", "_"), wn.NOUN)
        hyper = set(T.closure(lambda s: s.hypernyms() + s.instance_hypernyms()))
        rel = set(T.part_meronyms() + T.member_meronyms() + T.substance_meronyms() + T.part_holonyms() +
                  T.member_holonyms() + T.substance_holonyms())
        bad = sorted(s.name() for s in senses if s != T and (s in hyper or s in rel))
        if bad:
            why.append("S3:" + ",".join(bad))
        if senses and senses[0] != T:
            why.append("S4:" + senses[0].name())
    return why


def aliases_for(uid: str, c: dict, released: dict, others: dict) -> dict:
    cands = candidates(c, uid)
    canon = {normalise(c["Word"]), normalise(uid.replace("_", " "))}
    admitted, excluded, infl, sources, equiv = [], [], {}, {}, []
    for a, src in sorted(cands.items()):
        why = specificity(uid, c, a, canon, released, others)
        forms = [a] + inflections(a)
        if why and (uid, a) in EQUIVALENCES:
            equiv.append({"alias": a, "rules": why, "rationale": EQUIVALENCES[(uid, a)]})
            why = []
        if why:
            excluded += [{"alias": f, "base": a, "rules": why} for f in forms]
            continue
        admitted += forms
        sources[a] = src
        if len(forms) > 1:
            infl[a] = forms[1:]
    return {"aliases": sorted(set(admitted)), "validated_plurals": infl, "alias_sources": sources,
            "excluded_aliases": excluded, "equivalences_applied": equiv}


_WN_CHECKED = []


def _wordnet():
    """WordNet 3.0 for the matching rule, refused unless the corpus zip equals the pin (checked once per process)."""
    try:
        from nltk.corpus import wordnet as wn
    except ImportError:
        raise SystemExit("refused: the shared matching rule's hyponym test needs WordNet 3.0 (run under .venv-build)")
    if not _WN_CHECKED:
        _WN_CHECKED.append(check_wordnet())
    return wn


def singular(token: str) -> str:
    """The inflection policy read backwards: a token becomes the base b of which it is a generated plural
    (`token in plurals(b)`, b one of WordNet's lemmatisations); otherwise it is left as it is."""
    wn = _wordnet()
    bases = sorted(b for b in wn._morphy(token, wn.NOUN) if b != token and token in plurals(b))
    return bases[0] if bases else token


def head_lemma(answer: str) -> str | None:
    """The LONGEST whole-word suffix of the normalised answer that WordNet 3.0 knows as a noun lemma."""
    wn = _wordnet()
    toks = answer.split()
    for i in range(len(toks)):
        suffix = " ".join(toks[i:])
        if wn.synsets(suffix.replace(" ", "_"), wn.NOUN):
            return suffix
    return None


_RELEASED = {}


def released_lookup() -> dict:
    """S1's population for the matching rule: {canonical name or inflection: {concept ids}} over all 1,854 released
    THINGS concepts, from the pinned tables (checked once per process)."""
    if not _RELEASED:
        _wordnet()
        F.check_sources()
        concepts, _ = F.read_tables()
        _RELEASED.update(released_names(concepts))
    return _RELEASED


def names_concept(answer: str, concept: str, entry: dict) -> tuple[bool, str | None]:
    """THE SHARED MATCHING RULE (revision 12; the owner's decision of 3 October 2026, framework 8.2), the one function
    the qualification scorer and the audit scorer both call. `answer` is a normalised, well-formed answer (format is
    checked first by ai_reader_score.classify); `concept` the intended THINGS concept id; `entry` its frozen key item
    or audit-map entry (`aliases`, `excluded_aliases`, `synset`). The answer is read as given and with each token
    singularised under the inflection policy (`singular`). In this order:
      1. the answer equals an admitted form                                   -> (True,  'whole')      (i)
      2. it equals one of the item's EXCLUDED forms (S1-S4 stand)             -> (False, 'excluded')
      3. it equals the canonical name or an inflection of ANOTHER released
         THINGS concept (S1's population, all 1,854; the answer named that
         concept, not this one: 'alpaca' for llama, 'belt buckle' for buckle) -> (False, 'S1:<ids>')
      4. an admitted form occurs in it as a whole-word phrase                 -> (True,  'contains')   (ii)
         no head-noun guard: the target as a modifier of another object ('paint brush' for paint) passes - disclosed;
      5. a noun sense of its head lemma (`head_lemma`: the longest whole-word
         suffix WordNet 3.0 knows as a noun lemma) is a strict, transitive
         hyponym of the recorded target synset                               -> (True,  'hyponym')    (iii)
         (hypernym and instance-hypernym closure; an item without a synset cannot pass by (iii))
      otherwise                                                               -> (False, None)
    Steps 1-3 are applied to the answer as given and to its singularised form. Only step 1 on the answer as given
    needs nothing else; every other step needs the pinned WordNet and THINGS tables, so a scorer without them refuses
    instead of guessing."""
    aliases = entry["aliases"]
    if answer in aliases:
        return True, "whole"
    excluded = {e["alias"] for e in entry.get("excluded_aliases", [])}
    if answer in excluded:
        return False, "excluded"
    wn = _wordnet()
    sing = " ".join(singular(t) for t in answer.split())
    forms = list(dict.fromkeys([answer, sing]))
    if sing in aliases:
        return True, "whole"
    if sing in excluded:
        return False, "excluded"
    released = released_lookup()
    other = sorted(set().union(*(released.get(f, set()) for f in forms)) - {concept})
    if other:
        return False, "S1:" + ",".join(other)
    if any(re.search(r"(^| )" + re.escape(a) + r"( |$)", f) for f in forms for a in aliases):
        return True, "contains"
    sid = (entry.get("synset") or "").strip()
    if sid:
        T = wn.synset_from_pos_and_offset("n", int(sid[1:]))
        for f in forms:
            h = head_lemma(f)
            if h and any(s != T and T in set(s.closure(lambda x: x.hypernyms() + x.instance_hypernyms()))
                         for s in wn.synsets(h.replace(" ", "_"), wn.NOUN)):
                return True, "hyponym"
    return False, None


def assert_not_reserved(concepts) -> None:
    """For any later development or formal draw: none of its concepts may be a qualification concept."""
    reserved = set(json.loads(KEY.read_text())["reserved_concepts"])
    clash = sorted(set(concepts) & reserved)
    if clash:
        raise SystemExit(f"reserved qualification concepts in a later draw: {clash}")


def main() -> int:
    wn_pin = check_wordnet()
    sources = F.check_sources()
    d = F.draw()
    concepts, _ = F.read_tables()
    released = released_names(concepts)
    others = {}
    for x in d["chosen"]:
        for a in candidates(x["c"], x["concept"]):
            others.setdefault(a, set()).add(x["concept"])
    items = {}
    for x in d["chosen"]:
        c, im = x["c"], x["im"]
        al = aliases_for(x["concept"], c, released, others)
        sid = c["WordNet ID"].strip()
        items[x["item"]] = {
            "concept": x["concept"], "word": c["Word"], "display_label": im["display_label"],
            "synset": sid, "sense": c["Definition (from WordNet, Google, or Wikipedia)"], **al,
            "multiword_only": all(" " in a for a in al["aliases"]),
            "sense_rationale": None if sid else (
                "no WordNet id in THINGS: candidates are the Word and uniqueID fields" +
                (" and the listed synonyms" if synonyms(c["WordNet Synonyms"]) else "") +
                "; the sense is THINGS's definition above, single-meaning ('Number of word meanings in list' = 1)"),
            "human": {"recognizability": x["rec"], "recognizability_close": x["close"], "n_ratings": x["n_ratings"],
                      "n_correct": x["n_correct"], "most_common_label": im["recognizability_most-common-label"]},
            "stratum": x["stratum"], "easy": x["easy"], "requests": x["requests"]}
    ex = [e for v in items.values() for e in v["excluded_aliases"] if e["alias"] == e["base"]]
    audit = {"excluded_bases": len(ex), "excluded_forms": sum(len(v["excluded_aliases"]) for v in items.values()),
             "targets_affected": sum(1 for v in items.values() if v["excluded_aliases"]),
             "easy_targets_affected": sum(1 for v in items.values() if v["excluded_aliases"] and v["easy"]),
             "by_rule": {r: sum(1 for e in ex if any(x.startswith(r) for x in e["rules"]))
                         for r in ("S1", "S2", "S3", "S4")},
             "equivalences_applied": sum(len(v["equivalences_applied"]) for v in items.values()),
             "shared_admitted_strings": sorted(a for a, n in
                                               {a: sum(a in v["aliases"] for v in items.values())
                                                for v in items.values() for a in v["aliases"]}.items() if n > 1),
             "no_synset_items": sum(1 for v in items.values() if not v["synset"])}
    heads = sorted({K_ for x in d["chosen"] for a in candidates(x["c"], x["concept"])
                    for K_ in [a.split()[a.split().index("of") - 1] if "of" in a.split()[1:] else a.split()[-1]]
                    if K_.endswith("s")})
    inflection_audit = {"plural_only_heads": [h for h in heads if plural_only(h)],
                        "singular_s_heads": [h for h in heads if not plural_only(h)],
                        "note": "every head ending in -s among this candidate set, as the suffix rule classifies it "
                                "(an audit bounded to this set, not a general grammatical validator); reviewed: the "
                                "heads treated as plural-only are English plural nouns and the Latin binomial part "
                                "'latrans', none of which takes a generated plural here; the singular heads are "
                                "-ss/-us/-is/-as/-os words whose generated plurals survive only where WordNet "
                                "lemmatises them back"}
    key = {"note": "The orchestrator's key for the AI-reader qualification (revision 4: wording only; aliases, items "
                   "and membership as revision 3). Never sent to the reader.",
           "revision": 4, "seed": F.SEED, "frame_size": d["n_frame"], "cuts": d["cuts"],
           "stratum_frame_sizes": d["stratum_frame_sizes"], "exclusion_counts": d["exclusion_counts"],
           "exclusions": d["exclusions"], "source_pins": {"things": sources, "wordnet": wn_pin},
           "specificity_rule": "S1 another released concept's canonical name or inflection; S2 another selected "
                               "target's candidate; S3 WordNet broader class, part or whole; S4 first-listed WordNet "
                               "noun sense differs from the recorded target synset (sense order, not measured usage); "
                               "canonical names, space variants and inflections always stand; EQUIVALENCES documented",
           "equivalences": [{"concept": k[0], "alias": k[1], "rationale": v} for k, v in EQUIVALENCES.items()],
           "specificity_audit": audit, "inflection_audit": inflection_audit, "reserved_concepts": sorted(v["concept"] for v in items.values()),
           "items": items}
    KEY.write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n")
    easy = sum(v["easy"] for v in items.values())
    mw = sum(v["multiword_only"] for v in items.values())
    print(f"frame {d['n_frame']}, excluded {d['exclusion_counts']}; 300 items, easy {easy}, multi-word-only {mw}; "
          f"cuts {[round(t, 9) for t in d['cuts']]}; specificity {json.dumps(audit)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

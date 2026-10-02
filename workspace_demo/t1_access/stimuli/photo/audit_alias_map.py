"""The image audit's own frozen sense and alias map for the 32 instrument concepts, and the audit name SCORER bound to
it - revision 4 (framework §8.2; Codex RSC 69539bb §4.6 and 081f17b §2 group 7). The qualification key cannot score
these concepts, because the qualification set excludes every pool concept. A before-audit condition, not a Stage A
gate. Frozen before any audit answer; never extended after one.

    .venv-build/bin/python stimuli/photo/audit_alias_map.py      # writes audit_alias_map.json (needs WordNet)

CONSTRUCTION - the qualification key's (`ai_reader_key`): candidates are the THINGS Word, the concept id and the
WordNet synonyms THINGS lists for the concept's synset; canonical names, space variants and inflections always stand;
every other candidate passes the SAME specificity rule S1-S4 (S1 another released concept's canonical name or
inflection; S2 a candidate of another of the 32; S3 a WordNet broader class, part or whole; S4 a first-listed WordNet
noun sense other than the target synset), with documented same-referent equivalences (AUDIT_EQUIVALENCES) and one
documented audit exclusion the rule does not reach (AUDIT_EXCLUSIONS: a synonym that also names the material).
Inflections are the key's (head-noun plurals, WordNet irregulars where listed, plural-only heads none), plus ordinary
regular plurals reviewed where WordNet lists only an irregular one (AUDIT_REGULAR_PLURALS: taxis beside taxies). Under
the rule dress is pruned from clothes and lid from hat; denim is pruned from jeans by the documented exclusion.

CONSTRUCTION IDENTITIES recorded in the map: the THINGS tables and norm description (pinned), WordNet 3.0 (pinned),
dev_pool.json, ai_reader_key.py and this builder. The FROZEN MAP's sha256 is pinned in audit_app/IMAGE_AUDIT_FREEZE.md
('audit_alias_map.json sha256: <hex>'); `score` refuses unless the map on disk has exactly that hash, and scores a
free name with the qualification scorer's format-before-matching classification (ai_reader_score.classify) against the
concept's admitted aliases.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_frame as F  # noqa: E402
import ai_reader_key as K  # noqa: E402

MAP = HERE / "audit_alias_map.json"
FREEZE = HERE.parents[1] / "audit_app" / "IMAGE_AUDIT_FREEZE.md"
AUDIT_EQUIVALENCES = {
    ("taxi", "cab"): "cab.n.03 is the target synset itself; the first-listed sense (the driver's compartment) is a "
                     "WordNet ordering artefact; the ordinary name of the vehicle (S4)",
    ("hamburger", "burger"): "hamburger.n.01 is a sense of 'burger'; the first-listed sense is a person (Warren Burger) "
                             "(S4)",
    ("pig", "hog"): "hog.n.03 (domestic swine) is the target synset; the first-listed sense is figurative, a greedy "
                    "person (S4)",
}
AUDIT_EXCLUSIONS = {
    ("jeans", "denim"): "also names the fabric (denim.n.02, 'a coarse durable twill-weave cotton fabric'): a material "
                        "name does not discriminate the garment (Codex RSC 081f17b group 7); not reached by S1-S4 "
                        "because 'denim''s first-listed sense is the target synset",
}
AUDIT_REGULAR_PLURALS = {"taxi": ["taxis"]}   # reviewed: WordNet's noun.exc lists only 'taxies'


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build() -> dict:
    wn_pin = K.check_wordnet()
    sources = F.check_sources()
    pool = json.loads((HERE / "dev_pool.json").read_text())
    concepts, _ = F.read_tables()
    released = K.released_names(concepts)
    roles = sorted(pool["roles"], key=lambda r: r["concept"])
    others = {}
    for r in roles:
        for a in K.candidates(concepts[r["concept"]], r["concept"]):
            others.setdefault(a, set()).add(r["concept"])
    saved = dict(K.EQUIVALENCES)
    K.EQUIVALENCES.update(AUDIT_EQUIVALENCES)
    try:
        out = {}
        for r in roles:
            uid, c = r["concept"], concepts[r["concept"]]
            al = K.aliases_for(uid, c, released, others)
            dropped = []
            for (cu, a), why in AUDIT_EXCLUSIONS.items():
                if cu == uid and a in al["aliases"]:
                    forms = [a] + K.inflections(a)
                    al["aliases"] = [x for x in al["aliases"] if x not in forms]
                    al["validated_plurals"].pop(a, None)
                    al["alias_sources"].pop(a, None)
                    al["excluded_aliases"] += [{"alias": f, "base": a, "rules": ["AUDIT:material"]} for f in forms]
                    dropped.append({"alias": a, "rationale": why})
            for base, extra in AUDIT_REGULAR_PLURALS.items():
                if uid == base:
                    al["aliases"] = sorted(set(al["aliases"]) | set(extra))
                    al["validated_plurals"][base] = sorted(set(al["validated_plurals"].get(base, [])) | set(extra))
            sid = c["WordNet ID"].strip()
            out[uid] = {"family": r["family"], "role": r["role"], "synset": sid,
                        "sense": c["Definition (from WordNet, Google, or Wikipedia)"], **al,
                        "audit_exclusions_applied": dropped,
                        "sense_rationale": None if sid else "no WordNet id in THINGS: the sense is THINGS's definition"}
    finally:
        K.EQUIVALENCES.clear()
        K.EQUIVALENCES.update(saved)
    shared = sorted(a for a, n in {a: sum(a in v["aliases"] for v in out.values())
                                   for v in out.values() for a in v["aliases"]}.items() if n > 1)
    return {"note": "Audit-specific frozen sense/alias map for the 32 instrument concepts (revision 4): the "
                    "qualification key's specificity rule S1-S4 with documented equivalences and exclusions; scoring = "
                    "whole-answer equality after ai_reader_key.normalise with format checked first; frozen before any "
                    "audit answer.",
            "revision": 4,
            "construction": {"things_sources_sha256": sources, "wordnet": wn_pin,
                             "dev_pool_sha256": sha_file(HERE / "dev_pool.json"),
                             "ai_reader_key_py_sha256": sha_file(HERE / "ai_reader_key.py"),
                             "audit_alias_map_py_sha256": sha_file(Path(__file__))},
            "specificity_rule": "S1-S4 as ai_reader_key; canonical names, space variants and inflections stand",
            "equivalences": [{"concept": k[0], "alias": k[1], "rationale": v} for k, v in AUDIT_EQUIVALENCES.items()],
            "exclusions": [{"concept": k[0], "alias": k[1], "rationale": v} for k, v in AUDIT_EXCLUSIONS.items()],
            "regular_plurals_reviewed": AUDIT_REGULAR_PLURALS, "shared_admitted_strings": shared,
            "concepts": out}


def pinned_sha() -> str:
    m = re.search(r"audit_alias_map\.json sha256: `?([0-9a-f]{64})`?", FREEZE.read_text())
    if not m:
        raise SystemExit("refused: the audit freeze does not pin the alias map's sha256")
    return m.group(1)


def load_frozen() -> dict:
    """The map, only if its bytes hash to the sha256 pinned in the audit freeze."""
    b = MAP.read_bytes()
    if hashlib.sha256(b).hexdigest() != pinned_sha():
        raise SystemExit("refused: audit_alias_map.json differs from the frozen map pinned in IMAGE_AUDIT_FREEZE.md")
    return json.loads(b)


def score(concept: str, answer: str | None, status: str = "ok", overlength: bool = False) -> dict:
    """The audit's free-name score for one photograph: the qualification scorer's codes (format before matching)
    against the frozen map's admitted aliases for the intended concept."""
    from ai_reader_score import classify
    m = load_frozen()
    if concept not in m["concepts"]:
        raise SystemExit(f"refused: {concept} is not one of the 32 audit concepts")
    code, close = classify(answer, m["concepts"][concept]["aliases"], status, overlength)
    return {"concept": concept, "code": code, "pass_name": code == "OK_MATCH", "close_descriptive": close,
            "map_sha256": hashlib.sha256(MAP.read_bytes()).hexdigest()}


def main() -> int:
    doc = build()
    MAP.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    out = doc["concepts"]
    print(len(out), "concepts;", sum(len(v["aliases"]) for v in out.values()), "aliases;",
          sum(1 for v in out.values() for e in v["excluded_aliases"] if e["alias"] == e["base"]), "excluded bases;",
          "map sha256", sha_file(MAP))
    return 0


if __name__ == "__main__":
    sys.exit(main())

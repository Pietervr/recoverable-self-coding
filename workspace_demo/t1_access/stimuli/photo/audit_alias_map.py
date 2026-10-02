"""The image audit's own frozen sense and alias map for the 32 instrument concepts (framework §8.2; Codex RSC
69539bb §4.6): the qualification key cannot score them, because the qualification set excludes every pool concept.
The same construction as the qualification key (`ai_reader_key.aliases`): the THINGS Word, the concept id and the
WordNet synonyms THINGS lists for the concept's own synset, each with only its WordNet-validated plural; the THINGS
sense definition and synset recorded for the sense question and for referral records. Frozen before any audit
answer; never extended after one.

    .venv-build/bin/python stimuli/photo/audit_alias_map.py      # writes audit_alias_map.json
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_frame as F  # noqa: E402
from ai_reader_key import aliases  # noqa: E402


def main() -> int:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    concepts = {r["uniqueID"]: r for r in csv.DictReader(open(F.THINGS / "_concepts-metadata_things.tsv",
                                                             encoding="utf-8", newline=""), delimiter="\t")}
    out = {}
    for r in sorted(pool["roles"], key=lambda r: r["concept"]):
        c = concepts[r["concept"]]
        al, infl = aliases(F.concept_names(c, r["concept"]))
        out[r["concept"]] = {"family": r["family"], "role": r["role"], "synset": c["WordNet ID"],
                             "sense": c["Definition (from WordNet, Google, or Wikipedia)"], "aliases": al,
                             "validated_plurals": infl}
    doc = {"note": "Audit-specific frozen sense/alias map for the 32 instrument concepts; scoring = whole-answer "
                   "equality after ai_reader_key.normalise; frozen before any audit answer.",
           "dev_pool_sha256": hashlib.sha256((HERE / "dev_pool.json").read_bytes()).hexdigest(), "concepts": out}
    (HERE / "audit_alias_map.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(len(out), "concepts;", sum(len(v["aliases"]) for v in out.values()), "aliases")
    return 0


if __name__ == "__main__":
    sys.exit(main())

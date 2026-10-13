"""The per-clause citation table of the released bank (PREREGISTRATION_T1_model.md §3.1 "held outside this repository and
never redistributed"), with CSLB rows BY REFERENCE ONLY (owner's decision, 13 October 2026; R052 handoff f9aac0a7).

Every rendered clause cites the norm entry it was built from. The release publishes this table, never the databases:
  McRae rows (unchanged): concept, the feature statement, production frequency, cue validity - McRae's terms are
      non-commercial with a citation stipulation, which citing per clause satisfies;
  CSLB rows: concept, the CSLB ENTRY ID and production frequency - NO feature text. The CSLB licence (§2, read in full)
      prohibits making the norms available "in its present form or as converted or modified" without CSLB's prior
      written consent; the owner chose release by reference and no consent request. The entry id is the 1-based
      data-row number of the concept-feature pair in norms.dat of CSLB Property Norms V1.1 (zip sha256 473eb656...),
      so only a registered holder of that version can resolve it. (feature_matrix.dat's columns were considered and
      rejected: they cover 2,725 of the 5,928 normalised labels in norms.dat.) norms.dat repeats four concept-feature
      pairs on two rows each (hamster and tarantula 'has fur_hair', leopard 'is big_large', poison 'made of chemicals',
      different participant wordings); the count treats a pair as one feature, and its citation lists every entry of
      the pair, each with its own production frequency.
The guard `release_rows` refuses a CSLB row that carries any text field, and the table carries the CSLB credit line,
citation and the no-responsibility declaration (licence §2.3).

    from citation import citation_row, release_rows
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

CSLB_NORMS = Path.home() / "word-norms-cslb" / "norms.dat"
CSLB_VERSION = "CSLB Property Norms V1.1 (zip sha256 473eb656398695f9f9f5c8b8a675d4ca3cbdb09391a5946d0a0d4a82038d6e2b)"
CSLB_CREDIT = ("CSLB Norms: Copyright (c) and database right 2012-15 Centre for Speech, Language and the Brain (CSLB), "
               "Department of Psychology, University of Cambridge. All rights reserved.")
CSLB_CITATION = ("Devereux, B.J., Tyler, L.K., Geertzen, J., Randall, B. (2014). The Centre for Speech, Language and the "
                 "Brain (CSLB) Concept Property Norms. Behavior Research Methods, 46(4), 1119-1127. "
                 "doi:10.3758/s13428-013-0420-4")
CSLB_DECLARATION = ("The CSLB, those who carried out the original collection of data in the CSLB Norms and its funders "
                    "or sponsors bear no responsibility for the further analysis or interpretation of it here.")
MCRAE_FIELDS = ("source", "concept", "feature", "prod_freq", "cue_validity")
CSLB_FIELDS = ("source", "concept", "cslb_entries")      # cslb_entries: [[entry id, production frequency], ...]


@lru_cache(maxsize=1)
def cslb_entry_ids(norms: Path = CSLB_NORMS) -> dict[tuple[str, str], list[list[int]]]:
    """(CSLB concept label, normalised feature label - spaces to underscores, as the eligibility count uses it) ->
    [[1-based data-row number in norms.dat (header excluded), production frequency], ...] for every row of the pair."""
    out: dict[tuple[str, str], list[list[int]]] = {}
    for i, line in enumerate(norms.read_text(encoding="utf-8").splitlines()[1:], 1):
        f = line.split("\t")
        out.setdefault((f[2], "_".join(f[3].split())), []).append([i, int(f[4])])
    return out


def citation_row(provenance: dict, ids: dict | None = None) -> dict:
    """The released citation for one clause's source entry (a Source.provenance record)."""
    src = provenance["source"]
    if src == "McRae":
        return {"source": "McRae", "concept": provenance["concept"], "feature": provenance["feature"],
                "prod_freq": provenance["prod_freq"], "cue_validity": provenance.get("cv_published")}
    if src == "CSLB":
        ids = cslb_entry_ids() if ids is None else ids
        key = (provenance["concept"], provenance["feature"])
        if key not in ids:
            raise SystemExit(f"refused: CSLB entry of {provenance['concept']!r} has no id in {CSLB_VERSION}")
        return {"source": "CSLB", "concept": provenance["concept"], "cslb_entries": [list(e) for e in ids[key]]}
    raise SystemExit(f"refused: no citation rule for source {src!r}")


def release_rows(rows: list[dict]) -> dict:
    """The table as released: refuses a CSLB row with any field beyond the by-reference set (no text can leak)."""
    for r in rows:
        want = CSLB_FIELDS if r.get("source") == "CSLB" else MCRAE_FIELDS
        if tuple(sorted(r)) != tuple(sorted(want)):
            raise SystemExit(f"refused: citation row fields {sorted(r)} are not the released set {sorted(want)}")
        if r["source"] == "CSLB" and not (isinstance(r["cslb_entries"], list) and r["cslb_entries"] and all(
                isinstance(e, list) and len(e) == 2 and all(type(x) is int for x in e) for e in r["cslb_entries"])):
            raise SystemExit("refused: a CSLB row cites [entry id, production frequency] integer pairs, never text")
    out = {"rows": rows}
    if any(r["source"] == "CSLB" for r in rows):
        out["cslb"] = {"version": CSLB_VERSION, "credit": CSLB_CREDIT, "citation": CSLB_CITATION,
                       "declaration": CSLB_DECLARATION,
                       "cslb_entries": "[1-based data-row number in norms.dat of that version, production frequency] "
                                       "for every row of the concept-feature pair"}
    return out

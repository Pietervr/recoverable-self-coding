"""Mechanical checks of the clue bank against the §3 checklist (the two readers audit truth).

Input: one or more clue files, each {"family": <family>, "clues": {<concept id>: [12 clauses]}}.
Convention (build rule, recorded in the manifest): a clause is a present-tense predicate fragment
with the concept as its implied subject ("has four legs and a flat seat"), starting lower case
unless it opens with a proper noun, one line, no terminal full stop. In a packet it is rendered as
"- <clause>" (stimuli/packet.py).

Checks per clause:
  T  8-14 tokens as rendered in a slot, and the slot tokenizes as "-" + the clause's own tokens
  N  no surface form of its own concept (name, inflection, accepted variant; word-boundary match,
     case-insensitive)
  X  no surface form of any other bank concept (clauses travel into other concepts' packets)
  F  no family word of any of the eight families
  S  style: one line, no leading dash, no terminal full stop, no double spaces
Per concept: exactly 12 clauses, no duplicates; per file: every concept of the family present.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/stimuli/check_clues.py stimuli/drafts/clues_tools.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from stimuli.build_concepts import SNAPSHOT  # noqa: E402

TOKENS_MIN, TOKENS_MAX, PER_CONCEPT = 8, 14, 12
FAMILY_WORDS = {
    "animals": ["animal", "animals"],
    "countries": ["country", "countries", "nation", "nations"],
    "tools": ["tool", "tools"],
    "foods": ["food", "foods"],
    "vehicles": ["vehicle", "vehicles"],
    "instruments": ["instrument", "instruments"],
    "body parts": ["body part", "body parts", "part of the body", "parts of the body"],
    "materials": ["material", "materials"],
}


def word_re(form: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z])" + re.escape(form) + r"(?![A-Za-z])", re.IGNORECASE)


def main(paths: list[str]) -> int:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    bank = json.loads((HERE / "concepts.json").read_text())
    by_id = {c["id"]: c for c in bank["concepts"]}
    forms = {c["id"]: [(f, word_re(f)) for f in c["surface_forms"]] for c in bank["concepts"]}
    family_res = [(w, word_re(w)) for ws in FAMILY_WORDS.values() for w in ws]
    dash = tok.encode("-", add_special_tokens=False)
    failures, lengths = [], Counter()
    for path in paths:
        data = json.loads(Path(path).read_text())
        family = data["family"]
        want = sorted(c["id"] for c in bank["concepts"] if c["family"] == family)
        got = sorted(data["clues"])
        if got != want:
            failures.append((path, "-", "-", f"concepts differ: missing {sorted(set(want) - set(got))}, "
                                             f"extra {sorted(set(got) - set(want))}"))
        for cid, clauses in data["clues"].items():
            if cid not in by_id:
                continue
            if len(clauses) != PER_CONCEPT:
                failures.append((path, cid, "-", f"{len(clauses)} clauses, need {PER_CONCEPT}"))
            if len(set(c.lower() for c in clauses)) != len(clauses):
                failures.append((path, cid, "-", "duplicate clauses"))
            for i, clause in enumerate(clauses):
                problems = []
                n = len(tok.encode(" " + clause, add_special_tokens=False))
                lengths[n] += 1
                if not TOKENS_MIN <= n <= TOKENS_MAX:
                    problems.append(f"T {n} tokens")
                if tok.encode("- " + clause, add_special_tokens=False) != dash + tok.encode(
                        " " + clause, add_special_tokens=False):
                    problems.append("T slot boundary merges")
                own = [f for f, rx in forms[cid] if rx.search(clause)]
                if own:
                    problems.append(f"N names its concept: {own}")
                other = sorted({f"{o}:{f}" for o, fs in forms.items() if o != cid for f, rx in fs
                                if rx.search(clause)})
                if other:
                    problems.append(f"X names another bank concept: {other}")
                fam = [w for w, rx in family_res if rx.search(clause)]
                if fam:
                    problems.append(f"F family word: {fam}")
                if ("\n" in clause or clause.startswith("-") or clause.rstrip().endswith(".")
                        or "  " in clause or clause != clause.strip()):
                    problems.append("S style")
                for p in problems:
                    failures.append((path, cid, i, f"{p} | {clause}"))
    for path, cid, i, msg in failures:
        print(f"FAIL {Path(path).name} {cid} [{i}] {msg}")
    print(f"token lengths: {dict(sorted(lengths.items()))}")
    print(f"{'PASS' if not failures else 'FAIL'}: {len(failures)} problems in {sum(lengths.values())} clauses")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

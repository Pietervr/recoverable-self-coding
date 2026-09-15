"""The two-reader audit sheet of the clue bank (§3: "written and audited by two readers against a checklist").

Writes stimuli/audit/clue_audit_<date>.csv (one row per clause, opens in Excel) and stimuli/audit/CHECKLIST.md.
Each reader fills their own columns independently; a clause passes when both readers mark it true and neither marks
a checklist failure. The drafter's notes (facts to check) and the "decisive" markers (at most 2 per concept, which
may identify the concept alone) are shown; the mechanical items (length, names, family words) are already enforced
by check_clues.py and are not for the readers.

    python3 workspace_demo/t1_access/stimuli/make_audit_sheet.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY_FILES = ["animals", "countries", "tools", "foods", "vehicles", "instruments", "body_parts", "materials"]

CHECKLIST = """# Clue audit checklist (T1 stimulus bank, PREREGISTRATION_T1_model.md §3)

Each reader works alone and fills only their own columns (R1_* or R2_*). One row is one clause. The clause describes
the concept in the "concept" column as its implied subject; in the experiment it appears as a line "- <clause>".

For every clause mark:
- **true**: `y` if the clause is true of the concept as an ordinary reader understands the word (the sense in
  `concepts.json`), `n` if false or misleading, `?` if you cannot tell. The "drafter_note" column flags facts the
  drafter was unsure of: check those with particular care.
- **names**: `y` if the clause names the concept, an inflection or an accepted variant, or names its family (e.g.
  "animal", "country", "instrument"), in any disguise the checker could miss (a translation, a synonym, a pun).
- **decisive**: `y` if the clause alone would let a knowledgeable reader name the concept. At most two clauses per
  concept may be decisive; they are marked in the "marked_decisive" column. Mark `y` on any OTHER clause you find
  decisive.
- **comment**: optional; propose a rewrite if you mark n, y or y above.

A clause passes when both readers mark true = y, names = n, and (unless marked_decisive) decisive = n. Disagreements
are resolved by the two readers together; the resolution is recorded in the "resolution" column. The audited bank
is then frozen as stimuli/clues.json with the readers' names and the date.
"""


def main() -> int:
    rows = []
    for name in FAMILY_FILES:
        data = json.loads((HERE / "drafts" / f"clues_{name}.json").read_text())
        notes = data.get("notes", {})
        decisive = data.get("decisive", {})
        for cid, clauses in data["clues"].items():
            note_texts = notes.get(cid, [])
            for i, clause in enumerate(clauses):
                flagged = [n for n in note_texts if clause in n or clause[:40] in n]
                rows.append({"family": data["family"], "concept": cid, "index": i, "clause": clause,
                             "marked_decisive": "yes" if i in decisive.get(cid, []) else "",
                             "drafter_note": " | ".join(flagged),
                             "R1_true": "", "R1_names": "", "R1_decisive": "", "R1_comment": "",
                             "R2_true": "", "R2_names": "", "R2_decisive": "", "R2_comment": "", "resolution": ""})
    out = HERE / "audit"
    out.mkdir(exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    path = out / f"clue_audit_{stamp}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "CHECKLIST.md").write_text(CHECKLIST)
    digest = hashlib.sha256(json.dumps([r["clause"] for r in rows]).encode()).hexdigest()
    print(f"{len(rows)} clauses, {sum(bool(r['marked_decisive']) for r in rows)} marked decisive, "
          f"{sum(bool(r['drafter_note']) for r in rows)} with drafter notes -> {path} (clauses sha256 {digest[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

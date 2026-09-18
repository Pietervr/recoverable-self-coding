"""Draft amendment of 18 Sept 2026 to PREREGISTRATION_T1_model.md §3 and §15: who reads the stimulus audit.

Exact replacements, each matched once; run once. The owner's decision (18 Sept 2026): the owner plus an AI
reader, and the human half split so that four people each read a quarter.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

ANCHOR_3 = "and no clause is dropped on model output."
assert t.count(ANCHOR_3) == 1
NEW_3 = ANCHOR_3 + (
    "\n**Audit readers (draft amendment, 18 Sept 2026).** Every clause, and every §11 property item, is read twice"
    " and independently: once by one of four human readers and once by an AI reader. The human half is split by"
    " `audit_app/assign.py` (seed 20260918, output `audit_app/assignment.json`, written before any reader sees an"
    " item) into four equal parts stratified by family: four concepts of every family per part (32 concepts, 384"
    " clauses), a concept's twelve clauses kept together, and the 100 property items shuffled and dealt 25 per part."
    " The clauses were drafted by Claude (Anthropic) agents; the AI reader is OpenAI's Codex, a different developer's"
    " model, with its model and version recorded, and it reads the whole bank. Human readers work through a"
    " click-through page (audit.raconteur-road.com, one private link per reader) that asks the `CHECKLIST.md`"
    " questions in plain words and saves each answer as it is given; they work alone and see no model output and no"
    " other reader's marks. A clause or item passes only when both of its readers pass it; every other case is"
    " decided by the author, with both readers' marks and comments recorded beside the resolution. The frozen bank"
    " records each reader's name and part, the AI reader's model and version, and the dates."
)

ROW_15 = (
    "| 2026-09-18 | Draft amendment, §3 and §11 audits: every clause and property item read twice and independently,"
    " by one of four human readers on a seeded, family-stratified quarter (`audit_app/assign.py`, seed 20260918) and"
    " by an AI reader from a different developer than the drafting model (Codex) on the whole bank; an item passes"
    " only if both pass it, and the author decides the rest with both readers' marks recorded | owner, 18 Sept 2026:"
    " two readers of all 1,636 items is about three hours each; a quarter each keeps a human read of every item at"
    " about 40 minutes per person |"
)
LAST = t.rstrip("\n").rsplit("\n", 1)[1]
assert LAST.startswith("| 2026-09-15 | Second set of draft amendments"), LAST[:60]

t = t.replace(ANCHOR_3, NEW_3)
t = t.rstrip("\n") + "\n" + ROW_15 + "\n"
P.write_text(t)
print("§3 paragraph added; §15 row appended")

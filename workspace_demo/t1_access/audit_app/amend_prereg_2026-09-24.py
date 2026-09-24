"""Draft amendment of 24 Sept 2026 to PREREGISTRATION_T1_model.md §3 (and the §11 property items it
covers): the AI reader becomes the primary full-bank read and the human read becomes a seeded sample
audit of it, with a pass condition fixed here, before any sampled item is read.

Written and committed BEFORE the sample is drawn and before the AI reader runs. Exact replacements,
each matched once.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

OLD = (
    "**Audit readers (draft amendment, 18 Sept 2026).** Every clause, and every §11 property item, is read"
    " independently by one or more anonymous human readers and by an AI reader. The human half is split by"
    " `audit_app/assign.py` (seed 20260918, output `audit_app/assignment.json`, written before any reader sees an"
    " item) into four equal parts stratified by family: four concepts of every family per part (32 concepts, 384"
    " clauses), a concept's twelve clauses kept together, and the 100 property items shuffled and dealt 25 per part."
    " The clauses were drafted by Claude (Anthropic) agents; the AI reader is OpenAI's Codex, a different developer's"
    " model, with its model and version recorded, and it reads the whole bank. Human readers work through a"
    " click-through page (audit.raconteur-road.com, one link per part) that asks the `CHECKLIST.md` questions in plain"
    " words and saves each answer as it is given. The links were forwarded by the recipients, so each visitor's browser"
    " holds a private, anonymous session and answers are stored per session; readers see no model output and no other"
    " reader's answers, and the page shows each visitor the least-read cards of the part first. A clause or item passes"
    " only when it has at least one human read and the AI reader and every human reader pass it; every other case is"
    " decided by the author, with all readers' answers and comments recorded beside the resolution. The frozen bank"
    " records, per item, the number of human reads with their anonymous session ids and times, the AI reader's model"
    " and version, and the dates; no reader's name is recorded."
)

NEW = (
    "**Audit readers (draft amendment, 24 Sept 2026).** Every clause, and every §11 property item, is read by an AI"
    " reader; a seeded sample of them is additionally read by two independent anonymous human readers, and that sample"
    " audits the AI reader. The clauses were drafted by Claude (Anthropic) agents; the AI reader is OpenAI's Codex, a"
    " different developer's model, with its model and version recorded, and it reads the whole bank of 1,636 items"
    " against `CHECKLIST.md`, one item at a time, seeing no other reader's answers. **The sample.**"
    " `audit_app/sample.py` (seed 20260924, output `audit_app/sample.json`, committed before any sampled item is read"
    " and before the AI reader runs) draws four concepts of every family (32 concepts, 384 clauses, a concept's twelve"
    " clauses kept whole because the decisiveness rule is a per-concept constraint) and 40 of the 100 property items:"
    " 424 items, about 1.1 hours per reader at the 9.5 s/item pace measured on 20 September. The draw is independent"
    " of which items already carry answers. **The pass condition, fixed here.** A human objection on a sampled item"
    " triggers adjudication by the author, who records the decision and its reason; the objection is a trigger and not"
    " itself a miss, because two readers of the same clause disagree on judgement as a matter of course — the human"
    " objection rate on the read sessions of 20 September was 4.4\\%. Let $m$ be the number of sampled items that the AI"
    " reader passed and that adjudication finds should not have passed, and $U$ the exact one-sided 95\\%"
    " (Clopper–Pearson) upper bound on the miss rate implied by $m$ of 424: $m \\le 3$ gives $U \\le 0.0182$ and"
    " $m = 4$ gives $U = 0.0215$. If $U \\le 0.02$, the AI reader's read stands for the unsampled items and the bank is"
    " frozen on it. If $U > 0.02$, the full two-reader human read of the whole bank is reinstated before the freeze. The"
    " raw human objection rate and every adjudication with its reason are reported and published beside $m$; they are"
    " descriptive and do not gate the freeze, and publishing them is what keeps the adjudication checkable."
    " **Passing.** A sampled item passes when the AI reader and both of its human readers pass it;"
    " an unsampled item passes when the AI reader passes it and the sample has met its condition. Every other case is"
    " decided by the author, with all readers' answers and comments recorded beside the resolution. **What counts as a"
    " human read.** An answer given on the item itself. The page's card-level \"the other … are fine\" control is"
    " removed for the sample audit; answers already produced by it are retained and reported with their `via` and time,"
    " and are not counted as reads. **The open links.** Human readers work through a click-through page"
    " (audit.raconteur-road.com, one link per part) that asks the `CHECKLIST.md` questions in plain words and saves"
    " each answer as it is given; each visitor's browser holds a private, anonymous session, readers see no model"
    " output and no other reader's answers, and the four part links of the 18 September split stay open. Reads"
    " volunteered outside the sample are recorded and any objection in them is resolved by the author, but they are not"
    " required and do not enter the sample's miss count. The frozen bank records, per item, whether it was sampled,"
    " every human answer with its anonymous session id, `via` and time, the AI reader's model and version, the sample"
    " seed, $m$, $U$, and the dates; no reader's name is recorded. The audited bank, `CHECKLIST.md`, every answer and"
    " the audit code are published with the study, so the audit can be re-run, extended or contradicted by anyone."
)

assert t.count(OLD) == 1, "the 18 Sept audit-readers paragraph did not match exactly once"
t = t.replace(OLD, NEW)

ROW = (
    "| 2026-09-24 | Draft amendment, §3 and §11 audits: the AI reader becomes the primary full-bank read and the"
    " human read becomes a seeded sample audit of it (`audit_app/sample.py`, seed 20260924, 32 concepts = 384 clauses"
    " + 40 property items = 424 items, two human readers each), with the pass condition fixed before the draw: a human"
    " objection triggers adjudication by the author, and the exact one-sided 95% upper bound on the AI reader's"
    " ADJUDICATED miss rate must be at or below 0.02 (at most 3 of 424) or the full two-reader human read is"
    " reinstated, with every adjudication and the raw objection rate published; a human read counts only when given on the item itself, and the card-level \"the other"
    " … are fine\" control is removed for the sample | owner, 24 Sept 2026: the questions, the answers and the code"
    " are published with the study and anyone can re-run or audit them, so the audit's job is to be documented,"
    " bounded and reproducible rather than exhaustive; two readers over all 1,636 items is about three hours each and"
    " had stalled, and of the 818 items marked done by 24 September 534 came from the card-level control at a pace"
    " (median 0.5-1.6 s per clause against the 9.1-10.6 s/item of the read sessions) that is not a read |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3 audit-readers paragraph replaced; §15 row appended")

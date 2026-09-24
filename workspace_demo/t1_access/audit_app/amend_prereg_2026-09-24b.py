"""Draft amendment of 24 Sept 2026, second entry, to PREREGISTRATION_T1_model.md §3 (and the §11
property items it covers): the human reader pass is removed. The bank is read by AI readers whose
recall is MEASURED on a planted-defect set, and decisiveness is measured by a naming test rather
than judged.

Owner's decision, 24 Sept 2026, after the sample-audit design of the first entry was shown to rest
on an unmeasured quantity: "Remove the human element - it will be bad results regardless."

Written and committed before any reader output exists. The whole §3 "Audit readers" line is replaced,
located by its stable prefix so no long string has to be transcribed.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
lines = P.read_text().split("\n")

PREFIX = "**Audit readers"
hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
assert len(hits) == 1, f"expected one Audit readers paragraph, found {len(hits)}"

NEW = (
    "**Audit readers (draft amendment, 24 Sept 2026, second entry).** Every clause, and every §11 property item, is"
    " read by AI readers. **There is no human reader pass.** The human read was removed because it was a"
    " low-prevalence detection task, the regime in which human search is known to fail: published miss rates in"
    " low-prevalence visual search average about 0.30 even for trained screeners, and this bank's defect rate is of"
    " order 1–2\\%. Our own instrument measured the failure directly — of the 818 items marked read by 24 September,"
    " 534 were cleared by the page's card-level control at a median 0.5–1.6 s per clause against the 9.1–10.6 s/item"
    " of the sessions that answered line by line. The decisive property is that a skimmed pass and an attentive pass"
    " are indistinguishable in the record, so a missed defect that both a human and an AI reader pass is recorded as"
    " agreement and reads as confirmation: the audit would look cleanest exactly where it failed. A reader whose"
    " sensitivity is unmeasured does not give a weak bound on the defect rate, it gives none. **Readers.** One or more"
    " AI readers, each from a developer other than the model that drafted the clauses (Claude, Anthropic); the first is"
    " OpenAI's Codex, with model and version recorded. Each reads the whole bank against `CHECKLIST.md` one item at a"
    " time in a fresh context, so no vigilance decay accumulates across items and every judgement is an independent"
    " pass — the property the human read could not offer. **Recall is measured, not assumed.** A planted-defect set of"
    " certain ground truth is generated mechanically by `audit_app/plant.py` (seed declared, output committed before"
    " any reader sees it) and embedded at a declared rate, blind to the readers: a true clause of one concept"
    " re-attached to a sibling concept where it is false; a clause already marked decisive moved into an unmarked slot."
    " No model authors the defects, so the drafting model's blind spots are not built into its own test. Each reader's"
    " catch rate on the plants is its measured recall $r$, reported per reader and per failure mode, and every result"
    " is stated with $r$ beside it. **Decisiveness is measured, not judged.** Rather than asking a reader whether a"
    " clause would let someone name the concept — a hindsight-biased meta-judgement — each clause is presented alone"
    " to a reader model and the model attempts to name the concept; a clause counts decisive when it is named. For an"
    " experiment whose subject is a language model this is the more direct operationalisation, and it errs"
    " conservative, flagging more clauses than a judgement would and so removing give-aways rather than manufacturing"
    " them. The model under test is never used for it, and §3's existing rule stands: no clause is dropped on the"
    " model under test's output. **Passing.** An item passes when every AI reader passes it and the readers' measured"
    " recall on the planted set is at or above the declared bar. Items any reader flags, and disagreements between"
    " readers, are decided by the author, with every reader's answer and the reason recorded beside the resolution;"
    " that adjudication set is small and mostly defective, which is the regime in which human judgement is reliable."
    " **The bar.** The recall bar and the residual-defect tolerance are to be fixed by the contamination simulation"
    " recorded in the `rsc_t1_simulation_design.md` §12 ledger — the rate of contaminated concepts at which the"
    " expanded procedure's false-mixture rate leaves zero — and not guessed. Until that run reports, the interim bar"
    " is a measured recall of at least 0.90 on the planted set, declared here as provisional. **The record.** The"
    " frozen bank records, per item, every reader's answer, each reader's model and version and measured recall, the"
    " plant seed and which items were planted, the naming-test model and its outcome per clause, the author's"
    " adjudications with reasons, and the dates. The audited bank, `CHECKLIST.md`, every answer, the plants and all"
    " of this code are published with the study, so the audit can be re-run, extended or contradicted by anyone."
    " **Recorded limitation.** With the human read removed, the guard against a blind spot shared across reader models"
    " is weaker. It now rests on using developers other than the drafter, on the mechanically generated plants, and on"
    " publication. A second reader from a third developer would strengthen it materially and is not yet in place."
)

lines[hits[0]] = NEW
t = "\n".join(lines)

ROW = (
    "| 2026-09-24 | Draft amendment, second entry: the human reader pass is REMOVED. The bank is read by AI readers"
    " from developers other than the drafter, each reader's recall is measured on a mechanically generated"
    " planted-defect set (`audit_app/plant.py`) embedded blind, decisiveness is measured by a naming test instead of"
    " judged, the author adjudicates flags and reader disagreements, and the recall bar is deferred to the §12"
    " contamination run with an interim measured recall of 0.90 | owner, 24 Sept 2026 (\"remove the human element - it"
    " will be bad results regardless\"): the human read was a low-prevalence detection task, where published miss"
    " rates average about 0.30 and our own instrument measured 534 of 818 items cleared at 0.5-1.6 s per clause; a"
    " skimmed pass is indistinguishable from an attentive one in the record, so a jointly missed defect reads as"
    " agreement and the audit looks cleanest where it failed, and an unmeasured reader sensitivity gives no bound at"
    " all rather than a weak one |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3 audit-readers paragraph replaced (human pass removed); §15 row appended")

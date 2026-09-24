"""Draft amendment of 24 Sept 2026 to PREREGISTRATION_T1_model.md §3.1: K is not used as a gate.
Cue validity becomes a selection heuristic and the naming test, already declared in §3, carries
decisiveness.

R084's measurement (FEASIBILITY.md "Setting K", RSC 5d53023) put the bank ceiling at K = 2, bound by
materials at exactly 16 concepts. At K = 2 a non-decisive clause need only be shared by 2 of 4,411 cues,
which is the absence of a floor rather than a floor. The deeper reason is that the statistic was wrong for
the job: a sharing count measures how often a feature was PRODUCED alongside other cues, not how many
things the feature is true of.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

OLD = (
    "**Decisiveness is measured, not judged.** Each concept's 12 selected features are ranked by sharing "
    "count\nascending, the rarest first. The **two rarest are the concept's permitted decisive clauses** and "
    "are marked\nas such, which satisfies §3's \"at most two\" by construction rather than by a reader's "
    "opinion. Every other\nselected feature must be shared by at least $K$ cues, $K$ declared from the "
    "reported distribution of\nsharing counts **before** step 2 selects and recorded here; it is not set "
    "now, because setting it without\nthe distribution would be the same guess this amendment exists to "
    "remove. The per-clause record carries the\ncue, the feature, its production frequency and its sharing "
    "count, so any reader can recompute the\ndecisiveness of every clause in the bank."
)

NEW = (
    "**Decisiveness is settled by the naming test, not by cue validity (revised 24 Sept 2026).** The "
    "sharing count of a feature ranks candidates for selection, so that a concept's twelve clauses span a "
    "range of evidence strength rather than clustering; it does **not** gate them. An absolute floor $K$ on "
    "the sharing count of the ten non-decisive clauses was specified and has been withdrawn, for two "
    "reasons. The first is measured: the bank ceiling is $K = 2$, bound by materials at exactly sixteen "
    "concepts, and at $K = 2$ a clause need only be shared by two of 4,411 cues — that is the absence of a "
    "floor. The trade against the per-family count (16 → 2, 15 → 4, 14 → 5, 13 → 6, 12 → 8, 10 → 10) does "
    "not rescue it, and a floor at cue validity 0.05 is unreachable at any per-family count this source "
    "supports across eight families. The second reason is the one that matters: **a sharing count is the "
    "wrong statistic for the question.** It records how many cues happened to elicit a feature in a "
    "production study, not how many things the feature is true of. A feature only two cues produced is not "
    "thereby true of only two concepts, so cue validity read this way systematically overstates "
    "decisiveness, and $K = 2$ is that mismatch becoming visible rather than a shortage of data. "
    "Decisiveness is therefore taken from the naming test already declared above: each rendered clause is "
    "presented alone to a reader model, which attempts to name the concept, and a clause is decisive when "
    "it is named. That measures the property directly instead of inferring it from co-occurrence.\n\n"
    "**Selection, rendering and acceptance are one seeded loop.** Because a clause's decisiveness is known "
    "only once it is rendered and tested, the draw cannot be a set of sixteen chosen in advance. The seed "
    "fixes an **order** over each family's eligible concepts. The order is walked; for each concept twelve "
    "features are selected to span the sharing-count range, rendered, and put through the naming test. A "
    "concept is accepted when at most two of its twelve clauses are named, and those two are its marked "
    "decisive clauses. A concept with more than two named is re-selected once from its remaining features "
    "where it has any to spare, and only a concept that still fails, or that has exactly twelve features "
    "and so no freedom to re-select, is passed over. Every acceptance, re-selection and pass-over is "
    "recorded with its reason and its position in the seeded order, so the bank is reproducible from the "
    "seed and the source alone. This replaces the filter-before-draw problem rather than patching it: there "
    "is no separate eligibility filter for the draw to disagree with.\n\n"
    "**Families may run short, and the shortfall goes to BACKGROUND.** A family that cannot fill sixteen "
    "takes 15, 14 or 13, by the same rule buildings already uses: CAL, PILOT and CONF are fixed by the "
    "pairing and cannot carry an odd or short count, so the shortfall comes out of BACKGROUND alone. At "
    "least one BACKGROUND concept per family is required, because the background list draws exactly one "
    "clause from a BACKGROUND concept of each family, which sets the floor at 13. Materials is the family "
    "at risk: it stands at exactly sixteen eligible concepts, so a single pass-over there shortens it.\n\n"
    "**What this does and does not read.** The naming test uses a reader model that is **never the model "
    "under test**, and it runs in text before any capture. §3's rule stands untouched: no concept is "
    "selected and no clause is dropped on the model under test's output, and no output of the model under "
    "test is read at any point in building the bank. The residual risk is stated rather than dismissed — if "
    "the reader model and the model under test share a blind spot, stimulus construction is indirectly "
    "correlated with the system being measured. Its direction is conservative: the test removes clauses "
    "that give the concept away, which makes the task harder and the evidence gradient longer, never "
    "shorter. The per-clause record carries the cue, the feature, its production frequency, its sharing "
    "count and the naming-test outcome with the reader model and version, so any reader can recompute every "
    "decisiveness call in the bank."
)

assert t.count(OLD) == 1, f"decisiveness paragraph matched {t.count(OLD)} times"
t = t.replace(OLD, NEW)

ROW = (
    "| 2026-09-24 | Draft amendment, §3.1 revised: the absolute floor $K$ on cue validity is WITHDRAWN. "
    "Sharing count ranks candidates for selection so the twelve clauses span a range of evidence strength; "
    "decisiveness is settled by the naming test already declared. Selection, rendering and acceptance "
    "become one seeded loop over an order rather than a set of sixteen, with re-selection once and "
    "pass-over recorded; a family may run 13–16 with the shortfall in BACKGROUND | R084 measured the bank "
    "ceiling at $K = 2$, bound by materials at exactly sixteen concepts, where a clause need only be shared "
    "by two of 4,411 cues — no floor at all — and no per-family count this source supports reaches cue "
    "validity 0.05 across eight families. More fundamentally the statistic was wrong for the question: a "
    "sharing count records how many cues elicited a feature in a production study, not how many things it "
    "is true of, so it overstates decisiveness, and $K = 2$ is that mismatch made visible. The naming test "
    "measures the property directly |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3.1 decisiveness paragraph replaced; §15 row appended")

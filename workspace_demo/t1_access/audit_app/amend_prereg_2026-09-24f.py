"""Draft amendment of 24 Sept 2026 to PREREGISTRATION_T1_model.md §3.1, from R084's materials trial
(STEP2_MATERIALS.md, RSC c7c7a3f):

  A. the acceptance criterion gains a FLOOR. A one-sided ceiling rewards writing clauses that identify
     nothing: the only concept accepted in the trial, marble, passed with 0 of 12 named because its
     clauses are vague, and a packet playing all twelve still would not point at it.
  B. derivational variants are merged before selection, and proper and brand names leave the pool.
  C. the source is recorded as under question, because Buchanan's feature column carries no relation.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

OLD_ACCEPT = ("A concept is accepted when at most two of its twelve clauses are named, and those two are "
              "its marked decisive clauses.")
NEW_ACCEPT = (
    "Acceptance is **two-sided**, and both sides are required. *The ceiling*, on single clauses: at most "
    "two of the twelve are named when each is presented alone, and those two are the concept's marked "
    "decisive clauses. *The floor*, on the packet: the concept **is** named from the eight clauses of a "
    "seeded draw, on three independent draws, all three. A ceiling alone rewards vagueness — the way to "
    "pass a concept becomes to write clauses that identify nothing, which hands decisiveness straight back "
    "to whoever writes them and is what the naming test was adopted to prevent. R084's materials trial "
    "showed it happening: the one accepted concept, *marble*, passed with 0 of 12 named because a reader "
    "given its clauses answered globe, ball, beans, stamp, coin and egg, so a packet playing all twelve at "
    "$k = 8$ would not point at marble either. The floor is set at eight clauses on seeded draws because "
    "that is the $k = 8$ endpoint the design actually presents, so the two sides together state the dose "
    "requirement itself and make it testable before any capture: near-uninformative one clause at a time, "
    "identifying when the evidence is in."
)

OLD_SEL = ("for each concept twelve features are selected to span the sharing-count range, rendered, and "
           "put through the naming test.")
NEW_SEL = (
    "for each concept twelve features are selected to span the sharing-count range, rendered, and put "
    "through the naming test. "
    "Before selection the candidate pool is reduced: features are merged when they share a Snowball "
    "(Porter2) stem or are linked by WordNet `derivationally_related_forms`, the merged group counting as "
    "one feature represented by its highest-frequency surface form, and proper nouns and brand names are "
    "removed. Lemmatising alone merges inflections but not derivations, which let *conditional*, "
    "*condition* and *conditioner*, or *cleanser*, *cleanliness*, *cleanse* and *clean*, stand as four "
    "distinct features of one concept — 36 such pairs across sixteen concepts in the materials trial. A "
    "concept's twelve clauses would then be a handful of ideas restated, which flattens the $k$-graded "
    "curve of §5 for a reason that has nothing to do with the model. The brand-name exclusion is the same "
    "finding from the other end: *glue*'s two rarest candidates were *elmer* and *elmers*, one brand name "
    "counted twice, and §3 already bars named terms tied to a concept."
)

for old, new in ((OLD_ACCEPT, NEW_ACCEPT), (OLD_SEL, NEW_SEL)):
    assert t.count(old) == 1, f"no unique match: {old[:60]!r}"
    t = t.replace(old, new)

SOURCE_NOTE = (
    "\n\n**The source is under question (24 Sept 2026).** Buchanan's `feature` column does not hold feature "
    "statements. It holds single content words segmented out of unsegmented free-text participant prose: "
    "the cue *garbage* yields *away*, *bad*, *dump*, *gross*, *landfill*, *smell*, *trash*, *want*; the cue "
    "*oak* yields the word *as*. **The relation is absent, and the relation is what a clause asserts** — "
    "*leather* with *cow* does not say whether leather is made from a cow, comes from one, or is found near "
    "one. Under this source every clause's predicate is supplied by the renderer, and a citation reading "
    "“the word *away* was produced by 20 participants for the cue *garbage*” does not license “is taken "
    "away by a collection truck each week”. That is the authored content this construction exists to "
    "remove, re-entering at the last step, and it would make the citation decorative. McRae et al. (2005) "
    "carries the relation explicitly, with a relation type per entry (*alligator* beh- *eats people*; "
    "*airplane* inbeh- *crashes*), and CSLB publishes normalised feature labels for 638 concepts. Those two "
    "are the format this section assumes and Buchanan is not, so they are not coverage fallbacks but "
    "candidate primary sources. The eight family sizes must be re-measured on them before any of this is "
    "promised, since they hold 541 and 638 concepts against Buchanan's 4,411 — a comparison that is less "
    "unequal than it looks, because only 188 Buchanan cues were eligible across the eight families at all. "
    "Until that measurement returns, no bank is built and nothing here is frozen."
)
ANCHOR = "**Recorded fragility.**"
assert t.count(ANCHOR) == 1
t = t.replace(ANCHOR, SOURCE_NOTE.strip() + "\n\n" + ANCHOR)

ROW = (
    "| 2026-09-24 | Draft amendment, §3.1: acceptance becomes TWO-SIDED — at most two of twelve clauses "
    "named alone, AND the concept named from the eight clauses of three seeded draws; derivational variants "
    "merged before selection (Snowball stem or WordNet derivational link) and proper and brand names "
    "removed; and the source recorded as under question, with McRae and CSLB named as candidate primary "
    "sources to be measured | R084's materials trial: a one-sided ceiling rewards vagueness, and the only "
    "accepted concept passed with 0 of 12 named because a reader given its clauses answered globe, ball, "
    "beans and coin — so a $k = 8$ packet would not identify it either, and decisiveness had returned to "
    "the renderer. Lemmatising leaves derivations unmerged, so twelve features can be four ideas restated "
    "(36 pairs in sixteen concepts) and *glue*'s rarest two were *elmer* and *elmers*. And Buchanan's "
    "feature column holds content words cut from free-text prose rather than feature statements, so the "
    "relation — which is what a clause asserts — is authored, and the citation would be decorative |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3.1: acceptance floor added, derivational merge added, source question recorded; §15 row appended")

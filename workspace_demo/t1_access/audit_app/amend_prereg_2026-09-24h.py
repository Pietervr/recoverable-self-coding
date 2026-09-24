"""Consolidate §3.1. The section had accumulated seven amendments in one day and now carried
Buchanan-era paragraphs beside their McRae replacements - a wrong fact sitting next to its correction,
which is how a summary reads as authoritative and is wrong. It is rewritten whole, stating only what is
true under the decisions taken, with the history left to §15 and to git where it belongs.

No decision is changed here. Everything below was settled in the amendments of 24 Sept 2026.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

START = "### 3.1 The bank is built from published feature norms (draft amendment, 24 Sept 2026)"
END = "**Audit readers (draft amendment, 24 Sept 2026, second entry).**"
assert t.count(START) == 1 and t.count(END) == 1
i, j = t.index(START), t.index(END)

NEW = """### 3.1 The bank is built from published feature norms (draft amendment, 24 Sept 2026)

The concepts, the facts their clauses state and the decisiveness of each clause come from published human
production norms rather than from the authors. These clauses are the base of the study and the easiest part
of it to attack; a bank whose every fact carries a citation cannot be dismissed as ours. It also retires the
stimulus audit rather than managing it, because the two questions an audit exists to answer — *is this true
of the concept* and *does it give the concept away* — are answered by the source and by a declared test.

**The source.** McRae, Cree, Seidenberg and McNorgan (2005), *Semantic feature production norms for a large
set of living and nonliving things*, Behavior Research Methods 37(4): 541 concepts, 2,432 distinct feature
statements, every feature produced by at least 5 of 30 participants. File
`McRae-BRM-InPress/CONCS_FEATS_concstats_brm.txt` from `McRae-BRM-2005.zip`, SHA-256
`eb36b4c88f85141a226879ef2fdddc8075b9d35705fd27344c3a414eb56430a3`. Pooled with the CSLB concept property
norms (Devereux, Tyler, Geertzen and Randall 2014, Behavior Research Methods 46(4): 638 concepts), which
state the same kind of relational label and whose appendix carries a McRae label column, so the two reconcile
on a separator and a label mapping.

What makes McRae the right source is that **it carries the relation**, one relation type per entry:
*elephant* `has_a_trunk` (production frequency 23, shared by 1 concept, cue validity 1.000), *truck*
`used_for_cargo`, *cow* `beh_-_produces_milk`. `has_a_trunk` renders to "has a trunk", so what is left to do
is agreement and padding to the 8–14 token window, not the invention of a predicate. It also ships
`CV_No_Tax`, **the authors' own cue validity per feature**, so cue validity is cited rather than derived.

Buchanan et al. (2019) was measured first and dropped, and the reason belongs on the record because it is
not visible from the file's shape: its `feature` column holds single content words segmented out of
unsegmented free-text participant prose, not feature statements. The cue *garbage* yields *away*, *bad*,
*dump*, *gross*, *landfill*; the cue *oak* yields the word *as*. The relation is absent, and the relation is
what a clause asserts — *leather* with *cow* does not say whether leather is made from a cow, comes from one
or is found near one — so every predicate would have been authored and the citation decorative. LLM-augmented
norm sets are excluded on the same principle in reverse: building stimuli from model output to test a model
reintroduces the circularity the different-developer rule exists to prevent.

The norms are **held outside this repository and never redistributed**. Each clause cites its source entry —
concept, feature statement, production frequency and cue validity — and the release publishes that citation
table, not the database. McRae's terms are non-commercial with a citation stipulation, which citing per clause
satisfies and which is why the norms cannot sit inside the CC BY 4.0 data release.

**Three families: animals, foods, vehicles.** Membership is taxonomic, not ours: a concept belongs to a family
when **its first WordNet noun synset** (WordNet 3.0, senses ordered by frequency) lies in that family's
hyponym and instance-hyponym closure, over the roots `animal.n.01`, `food.n.01` with `food.n.02`, and
`vehicle.n.01`; cues sharing a dominant synset are one concept. The dominant-sense rule is used rather than
any-sense because any-sense admits members no reader would accept — *bark* the sailing ship, *secretary* the
writing desk — and a bank that needs those explained away defeats the point of sourcing it. E1 (the
answer-context form is one token) and E2 (no noun sense in another family's subtree) are unchanged and applied
after membership, with dominant-sense collapsing applied after E1 so that a synset is lost only when every one
of its cues fails E1.

Three is what the source supports and also the floor, since a competitor must come from a third family. McRae
and CSLB are concrete-**object** norm sets: neither norms people at all, and clothing, body parts, materials
and buildings fall short. Tools and instruments could not have been built from any source — after E2 and E1
the ceiling over the entire WordNet subtree, every single-token English noun in the family whether normed or
not, is 11 for each. E1 is what binds there, not the source, and E1 is a decode rule — the single-token answer
form is what makes the answer-position logit readable — so it was not relaxed to retain a family name.

**Twelve features per concept, and the threshold is that count restated.** A concept is eligible only with
≥ 12 usable features, because selection takes twelve, one per clause: a concept with eight features cannot
supply its twelve clauses. Before selection, features are merged **by subsumption** — two features merge when
one's word set contains the other's, the more specific representing the pair. That is McRae's duplication
pattern: `has_legs` and `has_4_legs`; `has_wheels`, `has_4_wheels`, `has_>_4_wheels` and `has_18_wheels`;
`beh_-_eats` and `beh_-_eats_peanuts` — 70 such pairs across 77 eligible concepts. Features are also merged
when they share a Snowball (Porter2) stem or a WordNet derivational link, and proper nouns and brand names are
removed. Unmerged duplication would let a concept's twelve clauses be a few ideas restated, which flattens the
$k$-graded curve of §5 for a reason that has nothing to do with the model. McRae's taxonomic features
(`an_animal`, `a_mammal`, `a_vehicle`) are family words by construction and rule F removes them, consistently:
`CV_No_Tax` is blank for exactly those rows.

**Decisiveness is settled by the naming test, not by cue validity.** Cue validity ranks candidates so that a
concept's twelve clauses span a range of evidence strength; it does not gate them. An absolute floor on cue
validity was specified and withdrawn, and the reason is worth keeping: a production-norm sharing count records
how many concepts elicited a feature, not how many things the feature is true of, so it overstates
decisiveness. The measurement showed it directly — *leather* was named from "soft", its most widely shared
feature, and not from its two rarest. Decisiveness is therefore taken from a test: each rendered clause is
presented alone to a reader model, which attempts to name the concept, and a clause is decisive when it is
named. That measures the property instead of inferring it.

**Acceptance is two-sided, and both sides are required.** *The ceiling*, on single clauses: at most two of the
twelve are named when each is presented alone, and those two are the concept's marked decisive clauses. *The
floor*, on the packet: the concept **is** named from the eight clauses of a seeded draw, on three independent
draws, all three. A ceiling alone rewards vagueness — the way to pass a concept becomes to write clauses that
identify nothing, which hands decisiveness back to whoever writes them. It was observed happening: a concept
passed with 0 of 12 named because a reader given its clauses answered globe, ball, beans, stamp and coin, so a
$k = 8$ packet would not have identified it either. The floor sits at eight clauses on seeded draws because
that is the $k = 8$ endpoint the design presents, so the two sides together state the dose requirement itself
and make it testable before any capture: near-uninformative one clause at a time, identifying when the
evidence is in.

**Selection, rendering and acceptance are one seeded loop.** Because a clause's decisiveness is known only
once it is rendered and tested, the draw cannot be a set fixed in advance. The seed fixes an **order** over
each family's eligible concepts. The order is walked; for each concept twelve features are selected to span
the cue-validity range, rendered, and put through both sides of the test. A concept that fails is re-selected
once from its remaining features where it has any to spare, and only a concept that still fails, or that has
exactly twelve features and so no freedom to re-select, is passed over. Every acceptance, re-selection and
pass-over is recorded with its reason and its position in the order, so the bank is reproducible from the seed
and the source alone, and there is no separate eligibility filter for the draw to disagree with.

**Role allocation across three families.** The confirmation set stays at **64 concepts**, so §10's power
numbers are unchanged; what changes is the stratification, from eight levels to three. CONF, CAL and PILOT
total 64, 16 and 16 as the pairing fixes them (32, 8 and 8 pairs, each member the foil of the other), and
those totals are met **across** families rather than within one, so per-family counts are unequal. They are
allocated by seed in proportion to each family's eligible pool, subject to the pairing being satisfiable:
with counts $a \\ge b \\ge c$ over three families every concept can be paired outside its own family whenever
$a \\le b + c$, which the allocation must satisfy and record. BACKGROUND takes every remaining eligible
concept, at least one per family. The realised allocation is fixed by the seeded loop and recorded at the
freeze.

**What this does and does not read.** The naming test uses a reader model that is **never the model under
test**, and it runs in text before any capture. §3's rule stands untouched: no concept is selected and no
clause is dropped on the model under test's output, and none of its output is read while building the bank.
The residual risk is stated rather than dismissed — if the reader model and the model under test share a blind
spot, stimulus construction is indirectly correlated with the system being measured. Its direction is
conservative: the test removes clauses that give the concept away, which makes the evidence gradient longer,
never shorter. The per-clause record carries the concept, the feature statement, its production frequency, its
cited cue validity and the naming-test outcome with the reader model and version, so any reader can recompute
every decisiveness call in the bank.

**Recorded fragility, and it is not small.** **The design does not stand on McRae alone.** McRae's own
eligible counts across the three families are animals 29, foods 14, vehicles 15 — 58 against the 96 that CONF,
CAL and PILOT require before any background. CSLB's concepts are therefore load-bearing, and CSLB's data is
available only on request. Until that access is settled the pooled figures (animals 52, foods 40, vehicles 27)
are an **upper bound**, because CSLB's concepts are counted without the ≥ 12 feature filter, which can only
reduce them. **Vehicles is the binding family.** If its realised eligible count falls below what the
allocation needs, three families cannot be filled, and since three is already the floor set by the competitor
rule, the question returns to whether this bank can be built from published norms at all.

"""

t = t[:i] + NEW + t[j:]
P.write_text(t)
print(f"§3.1 consolidated: {j - i} chars replaced by {len(NEW)}")

# T1, model side — pre-registration (DRAFT v1.2, 2026-09-11, after review rounds 1 and 2 and the first code pass)

**Freeze rule.** This document becomes v2 — the frozen pre-registration — by a commit whose hash is
recorded here, made only when every file in the §15 manifest exists and the §7.5/§10 validation
outputs are committed beside them. Until then it is a draft. After v2, changes are dated, committed
amendments (§15); nothing marked *[frozen]* is changed silently.

**Study.** Access at threshold in brain and language model (Entropy special issue, deadline 31 Oct 2026).
**Question.** Does the statistical description that separates graded from discontinuous *access* in
human EEG — the competing-model comparison of Sergent et al. 2021 (Nat Commun 12:1149), reproduced and
reconciled in `../sergent_port/` (commit e341319) — generalize to a language model's workspace
representations under a declared, randomized evidence dose?
**Not claimed.** Consciousness, experience, a first-order law shared by brain and model, entropy
production, ten model "subjects", a rejection of every graded account (only of the graded predictors
named in §7).
**Human reference.** A late active-session preference for the specified two-state mixture over the
specified heteroscedastic unimodal comparator, modest per-trial gain (~0.003 nat), boundary
sensitivity; the no-report case open. An assay to transfer, not a standard to meet.
**Inference statement.** One fixed checkpoint maps randomized clue packets deterministically to
residual activations. The study compares the conditional distribution of a pre-answer readout across a
declared stimulus population, then tests whether the readout's content affects the answer. Every
inference is conditional on this checkpoint and this stimulus population; the statistical clusters
are **concepts** (stratified by family), not model subjects. The primary readout R1 is a *coherence*
decoder; "access" is claimed only through the target bridge of §8.5.

---

## 1. Correspondence map

| Human (Sergent 2021) | Model (here) | Status of the correspondence |
|---|---|---|
| Vowel in noise; SNR (6–7 levels) | Coherence dose $k/8$: $k$ of eight descriptive clauses describe the target, the rest are a fixed family-balanced background (§3) | a randomized channel setting, not a semantic SNR; distinct-source count falls with $k$ (8, 8, 7, 6, 5, 3, 1) and is part of the manipulation |
| Time after stimulus (30 ms windows) | Layer depth at a fixed readout position | a computational-stage correspondence, not elapsed time; no requirement that late layers return to graded |
| Trial | One packet realization (concept × carrier × draw × level) | variability is declared and randomized in the stimulus |
| Subject ($n=20$), random effect | Concept ($n=64$ in confirmation), stratified by 8 families; carriers fixed (6); draws and levels are repeated observations within concept | the cluster for all uncertainty; ten pre-assigned bundles are a descriptive display only |
| EEG → CV linear decoder → per-trial distance | Residual stream → **frozen** linear decoder (calibration set) → per-trial decision-function score (R1) | a coherence readout; frozen scale for every confirmatory trial |
| Report: vowel identity + audibility | Next-token argmax (correct/incorrect) + the target token's log-probability and margin (R3) | no self-rating |
| Passive session | No-target-report condition: instruction before the packet, equal-length instructions, same marker (§12) | secondary; a challenge condition, not a passive state |
| M0 / M2B / M3, spm_BMS | The three inherited comparators; a frozen graded family and a frozen mixture family; primary evidence = out-of-sample joint log-score advantage with concept-cluster CIs (§8) | SPM curves kept, not given Bayesian calibration |

## 2. Hypotheses and outcomes

- **H1 (mixture support, coherence readout).** In the workspace band the mixture family predicts
  held-out concepts better than the graded family on R1: band-mean $\bar\Delta_{\text{ws}} > 0$ with a
  concept-cluster CI excluding 0 (§8.3).
- **H1-T (target bridge).** The same comparison on the target–foil projection R2 (§8.5) also gives
  mixture support, and the R1-assigned state predicts R2 at fixed $k$. "Discontinuous access" is
  written only if H1 and H1-T both hold; H1 alone is reported as a coherence-readout result.
- **H1′ (exact transfer).** The historical M3 beats the historical M2B on the two-model contrast in the
  band. Reported separately; H1 does not require it.
- **H2 (locality).** $\bar\Delta_{\text{ws}} - \bar\Delta_{\text{early}}$ has a CI excluding 0.
  "No contrast" is an explicit outcome.
- **H3 (causal use).** The state assigned by the held-out mixture fit moderates the effect of a
  target-direction intervention on the target–foil logit contrast (§11).
- **H0 (graded support).** $\bar\Delta_{\text{ws}} < 0$ with CI excluding 0.

Outcomes (§9): mixture support / graded support / inconclusive / technical assay failure. Family
heterogeneity, low high-state occupancy, or a mixture confined to some families are **scientific
results** under whichever outcome the primary statistic gives. A missing target bridge (§8.5) is not a
technical failure: it limits the interpretation to the coherence readout.

## 3. Stimulus population *[frozen at v2: `stimuli/concepts.json`, `stimuli/clues.json`, `stimuli/background.json`, `stimuli/manifest.csv`]*

**Concepts and roles.** single-token concepts in **3 families — animals, foods, vehicles** (§3.1). The confirmation set stays at 64 concepts, so §10's power numbers are unchanged; what changes is the stratification, from eight levels to three. Per-family role counts are no longer equal and are allocated by seed in proportion to each family's eligible pool, subject to CONF totalling 64, CAL 16 and PILOT 16; the realised allocation is fixed by the seeded acceptance loop and recorded at the freeze; token id frozen per concept in the answer
context (case and leading-space variants enumerated at build time). The frozen id is the lower-case leading-space form (' fox'); case, space and plural variants are enumerated per concept in `concepts.json`. No family now takes a capitalised id. Eligibility uses declared string and token rules only (`stimuli/build_concepts.py`: candidate lists written in advance; E1 the answer-context form is one token; E2 a word that also names a member of another bank family is excluded, 12 exclusions), with seed 20260915 and roles by a derived seed; no model output is read. Seeded assignment per family:
**BACKGROUND** (never a target, foil or competitor), CAL, PILOT and CONF, with CONF, CAL and PILOT totalling 64, 16 and 16 across the three families and BACKGROUND taking every remaining eligible concept, at least one per family. The totals are what the pairing fixes (32, 8 and 8 pairs, each member the foil of the other), and they are met across families rather than within one: with counts $a \ge b \ge c$ over three families, every concept can be paired outside its own family whenever $a \le b + c$, which the allocation rule must satisfy and record. Roles are
disjoint by construction: a CAL/PILOT/CONF concept's clues appear only in packets of its own split,
and only as target, foil or competitor clues; background clauses come only from BACKGROUND concepts.
So a held-out CONF concept's clues are absent from every training packet of the primary set. No
concept is selected or dropped on model performance; difficulty is a recorded covariate.
**Clue bank.** 12 descriptive clauses per concept, each stating one published normed feature statement of that concept (§3.1), 8–14 tokens each, written and audited by
two readers against a checklist (true of the concept; not containing the concept's name, an
inflection, or an accepted token variant; not naming the family). Clue identities are kept in every
record; single-clue difficulty is measured on CAL (§5) as a covariate. Clauses are present-tense predicate fragments with the concept as implied subject; the checker (`stimuli/check_clues.py`) is stricter than the checklist (no surface form of any bank concept, no family word of any family, 8–14 tokens as rendered), and the writing guideline keeps a clause informative but rarely decisive alone (no capital, city, language, currency, inventor or synonym). At most 2 of a concept's 12 clauses may identify it alone to a knowledgeable reader; they are recorded under a "decisive" key and audited by the two readers. Named terms tied to a concept (local words, named dishes, peoples, works, myths, makers, cities), idioms and dates that pin a concept are removed. The rule is applied in text only, before any capture. Whether a trial's inserted clues include a decisive clause is recorded as a trial covariate, and no clause is dropped on model output.
### 3.1 The bank is built from published feature norms (draft amendment, 24 Sept 2026)

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
$k$-graded curve of §5 for a reason that has nothing to do with the model. Taxonomic rows — the source's own
relation label: `a_bird`, `a_fruit`, `an_insect` as well as `an_animal`, `a_mammal`, `a_vehicle` — are removed as a
rule of their own (T); the family words among them fall under rule F as well, and `CV_No_Tax` is blank for exactly
the taxonomic rows. Whether T should narrow to the literal family words, which name the family and nothing else,
is an open decision; its measured cost is in the recorded fragility below.

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
with counts $a \ge b \ge c$ over three families every concept can be paired outside its own family whenever
$a \le b + c$, which the allocation must satisfy and record. BACKGROUND takes every remaining eligible
concept, at least one per family. The realised allocation is fixed by the seeded loop and recorded at the
freeze.

**What this does and does not read.** The naming test uses a reader model that is **never the model under
test**, and it runs in text before any capture. §3's rule stands untouched: no concept is selected and no
clause is dropped on the model under test's output, and none of its output is read while building the bank.
The residual risk is stated rather than dismissed — if the reader model and the model under test share a blind
spot, stimulus construction is indirectly correlated with the system being measured. Its direction is
conservative: the test removes clauses that give the concept away, which makes the evidence gradie**Recorded fragility, and it is not small.** **The design does not stand on McRae alone, and under the rules of this
section as written it does not stand on McRae and Feats either.** Counted on *usable* features — after rules T, F, N,
X, P and D above — with the dominant sense, E2 and then E1, for the adopted three families (R084, RSC 3cd3786,
`stimuli/norms_bank/CLEAN_ELIGIBILITY.md` and `clean_eligibility.json`): McRae alone gives 46 concepts at twelve
features and 65 at ten; McRae with Feats (Borovsky, Peters, Cox & McRae 2023, adopted as a second source under the
pooling rule recorded there) gives animals 25, foods 15, vehicles 11 — **51 at twelve** — and 36/23/18 — **77 at
ten** — against the 99 that CONF, CAL and PILOT require together with one BACKGROUND concept per family. Raw feature
counts overstate this: the earlier figures of 65 and 85, and the pooled bound of 128, counted features before the
usable-feature rules and are withdrawn. The joint integer allocation (every split with all three families, none
above half, backgrounds reserved first) is infeasible at every single-token count under the rules as written. The one
configuration that fills the bank is ten clauses together with answer names of up to two tokens: 114, with the witness
CONF 32/21/11, CAL 8/5/3, PILOT 8/5/3, BACKGROUND 13/2/3 and animals at the half-bound in every split; that is a change
to the readout, not to the stimuli, because a two-token answer has no single answer-position logit, and it is recorded
as a measured bound and not a proposal. Of the rules, T costs 16 concepts at twelve and 8 at ten; narrowing it to the
literal family words would give 67 and 85, still short, and is the open decision noted above. CSLB (requested 1
October 2026) remains an unfiltered set of 63 three-family candidates whose features have not been seen. Hovhannisyan
et al. 2021 as a conditional third source — absolute cutoff of ≥ 3 productions, no per-concept denominator, no
published CV, features elicited on a photograph: three gaps labelled on every row, never imputed — measured under
these same rules (R084, RSC 6153fee, `stimuli/norms_bank/ROUTE_FOUR_FAMILY.md`): three families 52 at twelve and
89 at ten; with clothing as a fourth family (root `clothing.n.01`, 15 concepts) 62 at twelve and **104 at ten
against a four-family minimum of 100** (CONF 64 + CAL 16 + PILOT 16 + one BACKGROUND per family), a feasible joint
allocation with an aggregate margin of four — counted before naming acceptance, for which no rate on relational
features has been measured, and resting on 14 Hovhannisyan concepts; 113 without rule T; 90 at a ≥ 5 cutoff. **Vehicles
is the binding family at every three-family count; on the four-family route no family binds and the aggregate
margin does.** **The route does not survive this section's acceptance.** On a seeded development sample of 30 concepts drawn
from the four-family pool in proportion to its sources, with ten usable clauses each selected and rendered under
the declared rules, the two-sided acceptance as declared (at most two of ten clauses named alone; the concept named
from eight clauses on all three seeded draws) passes **12 of 30 — 0.40, exact 95 % interval 0.23–0.59** (R084, RSC
af8a668, `stimuli/norms_bank/ACCEPTANCE_SAMPLE.md`; reader ollama llama3.1:8b at temperature 0, never the model under
test, stateless, no prior exposure to these concepts). Applied to the pool, 104 becomes about 42 (24–62) and 113
about 45, against a minimum of 100. The failures are 13 at the floor — the reader names a near neighbour (hawk → eagle,
pie → pizza, convertible → car; six were named on two of three draws) — and 5 at the ceiling, each with exactly three
clauses named alone; by source McRae 10/22, Feats 2/4, Hovhannisyan 0/4. Relaxing the floor to two of three draws gives
0.60, the ceiling to three clauses 0.57, both 0.77 — 80 of 104 and 87 of 113, still under 100 at the point estimate.
**The acceptance rate is a property of the clauses and the reader together.** The floor measures the reader's naming
ability, and this section fixes only that the reader is never the model under test, not how capable it must be; the
bank's size therefore depends on a choice the protocol has not made, which is recorded here as open. Hovhannisyan's
clauses add a second weakness: four of forty describe the photographed exemplar (wine "is made of glass", "has a
cork"; convertible "is red"), and without a cue validity its ten clauses spread over production counts, which do not
favour distinguishing features. The question therefore stands as this section raised it, and harder: whether the bank
can be built from published norms under these rules, or which rule, reader, source or channel changes — a decision
recorded for 15 October 2026. binding family.** If its realised eligible count falls below what the
allocation needs, three families cannot be filled, and since three is already the floor set by the competitor
rule, the question returns to whether this bank can be built from published norms at all.

**Audit readers (draft amendment, 24 Sept 2026, second entry).** Every clause, and every §11 property item, is read by AI readers. **There is no human reader pass.** The human read was removed because it was a low-prevalence detection task, the regime in which human search is known to fail: published miss rates in low-prevalence visual search average about 0.30 even for trained screeners, and this bank's defect rate is of order 1–2\%. Our own instrument measured the failure directly — of the 818 items marked read by 24 September, 534 were cleared by the page's card-level control at a median 0.5–1.6 s per clause against the 9.1–10.6 s/item of the sessions that answered line by line. The decisive property is that a skimmed pass and an attentive pass are indistinguishable in the record, so a missed defect that both a human and an AI reader pass is recorded as agreement and reads as confirmation: the audit would look cleanest exactly where it failed. A reader whose sensitivity is unmeasured does not give a weak bound on the defect rate, it gives none. **Readers.** One or more AI readers, each from a developer other than the model that drafted the clauses (Claude, Anthropic); the first is OpenAI's Codex, with model and version recorded. Each reads the whole bank against `CHECKLIST.md` one item at a time in a fresh context, so no vigilance decay accumulates across items and every judgement is an independent pass — the property the human read could not offer. **Recall is measured, not assumed.** A planted-defect set of certain ground truth is generated mechanically by `audit_app/plant.py` (seed declared, output committed before any reader sees it) and embedded at a declared rate, blind to the readers: a true clause of one concept re-attached to a sibling concept where it is false; a clause already marked decisive moved into an unmarked slot. No model authors the defects, so the drafting model's blind spots are not built into its own test. Each reader's catch rate on the plants is its measured recall $r$, reported per reader and per failure mode, and every result is stated with $r$ beside it. **Decisiveness is measured, not judged.** Rather than asking a reader whether a clause would let someone name the concept — a hindsight-biased meta-judgement — each clause is presented alone to a reader model and the model attempts to name the concept; a clause counts decisive when it is named. For an experiment whose subject is a language model this is the more direct operationalisation, and it errs conservative, flagging more clauses than a judgement would and so removing give-aways rather than manufacturing them. The model under test is never used for it, and §3's existing rule stands: no clause is dropped on the model under test's output. **Passing.** An item passes when every AI reader passes it and the readers' measured recall on the planted set is at or above the declared bar. Items any reader flags, and disagreements between readers, are decided by the author, with every reader's answer and the reason recorded beside the resolution; that adjudication set is small and mostly defective, which is the regime in which human judgement is reliable. **The bar.** The recall bar and the residual-defect tolerance are to be fixed by the contamination simulation recorded in the `rsc_t1_simulation_design.md` §12 ledger — the rate of contaminated concepts at which the expanded procedure's false-mixture rate leaves zero — and not guessed. Until that run reports, the interim bar is a measured recall of at least 0.90 on the planted set, declared here as provisional. **The record.** The frozen bank records, per item, every reader's answer, each reader's model and version and measured recall, the plant seed and which items were planted, the naming-test model and its outcome per clause, the author's adjudications with reasons, and the dates. The audited bank, `CHECKLIST.md`, every answer, the plants and all of this code are published with the study, so the audit can be re-run, extended or contradicted by anyone. **Recorded limitation.** With the human read removed, the guard against a blind spot shared across reader models is weaker. It now rests on using developers other than the drafter, on the mechanically generated plants, and on publication. A second reader from a third developer would strengthen it materially and is not yet in place.
**Pairs.** Within each split, concepts are paired across families by seed (CAL 8 pairs, PILOT 8,
CONF 32): each member is the **foil** of the other. A **competitor** (C2) is a third pre-assigned
concept of the same split from a third family.
**Background list.** Per (concept, carrier, draw): eight background clauses drawn by seed from BACKGROUND concepts, balanced across the three families in a declared 3–3–2 pattern whose family order rotates by seed, the target's own family included; identical for the target packet and its paired foil packet. One clause per family no longer fills eight slots at three families, so the rule states the balance explicitly instead; what it preserves is unchanged — background composition is fixed by seed, balanced across families, and identical between a target packet and its foil.
**Packet and nesting.** Eight slots. A draw fixes a slot permutation $\sigma$, a permutation of the
12 target clues, the same for the foil's clues, and the background list, with background clause $d_j$
attached to slot $\sigma(j)$. Level $k$ replaces slots $\sigma(1..k)$ with target clues $t_1..t_k$;
slots $\sigma(k{+}1..8)$ keep their own background clause. Levels are therefore nested by slot, and
$k=0$ and $k=8$ are matched endpoints. $k=0$ means "no deliberately inserted target clues", not "no
semantic evidence for the target"; incidental similarity remains possible and is not corrected.
Levels $k \in \{0,1,2,3,4,6,8\}$ — dense where the transition is expected, sparse above; the pilot may
move one interior level (§5), recorded.
**Controls at fixed $k \in \{2,3,4\}$, draw 1 of each (concept, carrier), separate from the primary
density fitting:**
- *Foil packets* (C1): slots $\sigma(1..k)$ carry the foil's clues $f_1..f_k$, same background — the
  target-specificity comparison (§6.4, §8.5). A C1 packet uses the target's first-draw slot permutation, clue order and background with the foil's clues, so it is not the foil's own primary packet; in C2 the competitor's clues $c_{\pi(j)}$ fill slots $\sigma(j)$ for $j > k$.
- *Competition packets* (C2): $k$ target clues in $\sigma(1..k)$ and $8-k$ clues of the competitor in
  the other slots (no background) — the one-competitor evidence baseline, explicitly a different
  structure from the primary channel.
**Carriers.** Six fixed frames (opening + closing sentences), fixed effects (`stimuli/carriers.json`).
**Prompt scan.** Every assembled prompt (instruction, carrier, all slots, marker, suffix) is scanned
case-insensitively for the target's and the foil's surface forms and accepted variants; a hit
regenerates the draw with the next seed (recorded); after ten failures the build stops and the case is decided
before any capture as a dated amendment that excludes the concept together with its paired foil, so no pair is broken (recorded); no concept is excluded silently.
**Size.** Primary set per condition: CONF 64 × 6 × 7 × $D$ ($D=4$: 10,752); CAL and PILOT 16 × 6 × 7 × 4
= 2,688 each. Controls per condition: C1 64 × 6 × 3 = 1,152; C2 1,152. Overlength prompts (> 160
packet tokens or beyond the capture limit) are rejected at build time, never truncated. "Packet tokens" are the carrier-open through carrier-close lines tokenized alone; the capture limit is 1,024 ids; an overlength item stops the build and is decided like a scan failure. CONF draws are built to $D = 8$; draws 0–3 are the $D = 4$ design and draws 4–7 are used only if §10 adopts $D = 8$.

## 4. Execution contract *[frozen]*

- Model: `mlx-community/Qwen3.6-27B-4bit`, the weights used in E1–E4 and E5–E9 (sha256 in the run
  log; E10 was Llama). 64 decoder layers (0–63), $d=5120$. Lens: Neuronpedia $n=1000$ Jacobian lens,
  fitted layers 0–62 (sha256); layer 63 has no Jacobian and reads out through the plain logit lens
  ($J_{63}=I$). Analysis layer set: 0–62; layer 63 descriptive only. Workspace band: layers 23–57
  (the E1 prior; the lens metadata's own band, 26–59, is a different definition and is not adopted);
  early band 3–15; late band 58–62.
- **One execution path, one pass per trial.** A read-only server addition `POST /api/capture` takes
  explicit `input_ids` (built by our code from raw text with the model tokenizer, no chat template),
  runs one `StreamSession.extend` over all ids with `capture_layers` = 0–63, and returns: the post-layer
  residual `acts[l]` (pre-norm, the tensor the lens transports; native bfloat16, the model's dtype, carried bit for bit) at the requested positions for every
  layer; the final position's logits reduced to `logsumexp`, the logits of a requested token-id list,
  and the top-1000 (id, logit) pairs; and, when an edit list is supplied, applies it inside that same
  pass with `StreamSession.set_edits` — at the named layers and global positions, before those layers'
  residuals are captured, so downstream layers consume the edited stream — logging $\|\Delta h\|$ per
  layer and position. Edit modes: `steer` (h + λv), `ablate` (`ablate_rows`, λ = removal fraction),
  `swap_delta` (Δ = patch_swap(h, α=1) − h, then h + λΔ — the linear-dose form; the raw `swap` alpha is
  not a dose and is not used), `patch` (replace the rows at the positions with supplied native bfloat16 vectors).
  The legacy `/api/intervene` is not used.
- Suffix rule: the answer suffix is tokenized separately and its ids concatenated; the build asserts
  that tokenizing the joined text reproduces the prefix ids exactly, else the item is rejected.
- Empty-edit parity: a capture with an empty edit list must equal the plain capture bit for bit on 20
  prompts before any run; an edit with λ=0 must equal the plain capture likewise.
- Batch size 1; identical kernels and precision; no cache reuse between prompts (a new
  `StreamSession` per trial); model, lens, runtime and OS versions, and every token id, in the run log.
- Readout position: the last token of the terminal marker (§12). Layout, marker and suffix are those of `stimuli/packet.py`: one line each, slots written "- <clause>", the marker `[END]` (three tokens, token-aligned after a newline), and in the active condition the suffix `\nAnswer:` tokenized separately under the join assertion. H3's marker positions are all three marker tokens.

## 5. Calibration (CAL) and pilot (PILOT)

**CAL (16 concepts).** Builds the instrument, frozen before CONF is read. Per layer: the R1 decoder
(§6.1) trained on CAL $k=8$ vs $k=0$ packets. $C$ is chosen by 5-fold concept-disjoint CV on CAL with
feature standardization fitted inside each training fold; selection metric = mean held-out log-loss;
ties → the smaller $C$. The decoder and standardization are then refitted on all CAL and frozen,
together with the affine z-scaling of the decision function (mean/SD of the CAL training scores).
Also on CAL: single-clue difficulty (target log-prob with one clue + 7 background: each CAL concept's clue $i$ alone in the first slot of the first draw with background in the other seven, all six carriers, active condition only, 16 × 12 × 6 = 1,152 captures); the family
recovery simulations (§7.5); the CAL layer scores for H3 (§11).
**PILOT (16 other concepts).** Validates the frozen instrument: held-out-concept accuracy at $k=8$ vs
$k=0$ per layer and per family on PILOT is the number reported (CAL's CV score is a selection score,
not a validation). Places the dose: the closed-set correct rate of §6.3 must cross 0.5 between $k=1$ and $k=4$; if
not, one interior level is moved (e.g. $\{0,1,2,3,4,6,8\} \to \{0,1,2,3,4,5,8\}$) and recorded. Supplies
the variance inputs for §10. Pilot model-comparison numbers are reported as pilot; they decide nothing
about the outcome.

## 6. Readouts *[frozen]*

### 6.1 R1 (primary assay; a coherence readout)
Per layer: `sklearn.linear_model.LogisticRegression(penalty="l2", C=C_l, solver="lbfgs", tol=1e-6,
max_iter=5000)` on standardized `acts[l]` at the readout position; $C_l \in \{10^{-3},\dots,10^{1}\}$
(9 values, log-spaced) from §5; response = `decision_function`, z-scaled with the CAL constants.
Trained on the active condition; frozen; applied to every trial at every level. "Distance" means
this quantity and nothing else.
### 6.2 R2 (target readout)
With $v^{(l)}_t = J_l^{\top} W_U[t]$ (the code's `j_lens_vectors_lite`; $J_{63}=I$), the linear
target–foil projection $r_2 = (v^{(l)}_t - v^{(l)}_f)\cdot h_l = (W_U[t]-W_U[f])\cdot J_l h_l$, and the
raw target projection $v^{(l)}_t\cdot h_l$. The normalized lens logit $(W_U\,\mathrm{norm}(J_l h_l))[t]$
is recorded as a secondary readout and never substituted for $r_2$. Endpoint projection
$\pi = (h - \bar h_{k=0})\cdot u / \|u\|^2$ with $u = \bar h_{k=8} - \bar h_{k=0}$ per (concept, carrier,
draw) from the matched endpoints; if $\|u\| < 0.05\,\overline{\|h\|}$ the trial is excluded from
$\pi$ only.
### 6.3 R3 (behaviour; active condition only)
From the final position of the active pass: the target token's log-probability
$\ell_t - \mathrm{logsumexp}$ (always recorded), its margin over the best other answer-set id, correct = (the target's frozen id has the highest final-position
logit among the frozen ids of the 127 bank concepts: one fixed answer set for every split and condition, chance 1/127 — 127 and not 128 since §3.1, because buildings carries 15 concepts); the open-vocabulary argmax and the target's open-vocabulary rank are recorded as secondary, and the logits of every concept's enumerated single-token variants are requested so that a variant-maximum reading is available descriptively. Stored per trial: the logits and open-vocabulary ranks (ties by ascending id) of the 128 frozen ids and of the further single-token variants, the top-1000 (id, logit) pairs, the logsumexp and the SHA-256 of the full logit vector. (Amended 15 Sept 2026: with the §12 suffix the open-vocabulary argmax was a formatting token such as "\n\n" in 20 of 20 full-dose development packets, and in five other suffixes, so an open-vocabulary rate cannot measure identification; a closed answer set crossed 0.5 at $k = 2$ on development concepts from no bank family, RSC d9d626c.) the foil's log-probability on every item. No sampling, so no malformed
outputs. Undefined in the no-target-report condition (no answer is elicited).
### 6.4 Content diagnostics (reported before H1 is read; §8.5 governs the interpretation)
On CONF at $k \in \{2,3,4\}$, paired target vs C1 foil packets (same background, same slots):
(i) R2 separates target from foil: the paired difference has a concept-cluster CI excluding 0 —
this is the **target-bridge precondition**; (ii) R1 target-vs-foil: a paired equivalence test
(TOST, margin 0.2 in z units, 90 % CI) per layer, plus the distribution of per-concept absolute
differences — a diagnostic of what R1 encodes, not a gate; non-significance is not equivalence;
(iii) R1 on target packets exceeds its $k=0$ value (coherence tracked).

## 7. Models *[frozen finite family after §7.5]*

Response $y$ = R1 score (or R2 projection in §8.5); regressor = level $k$; fits per layer.
### 7.1 Inherited comparators (ported line by line, `../sergent_port/fit_models.py`)
M0: $y \sim N(\mu, \sigma^2)$. M2B: $\mu(k) = L\,\mathrm{lg}(k) - L\,\mathrm{lg}(k_{\max}) + \mu_{\max}$
with $\mathrm{lg}(k) = 1/(1+e^{-\kappa(k-x_0)})$, $\sigma(k) = |a\,\mu(k) + b|$ (affine, as inherited).
M3: $A(k) = 1/(1+e^{-\kappa(k-x_0)})$ with $A=0$ at the catch level; $\mu_{\text{high}}(k) =
L_h\,\mathrm{lg}_h(k) + \text{step}$, forced to $\mu_{\text{low}}$ at the catch; $y \sim (1-A)N(\mu_{\text{low}},
\sigma^2) + A\,N(\mu_{\text{high}}, \sigma^2)$; shared $\sigma$. (In this form "step > 0" does not order
the components; M3 is kept exactly as inherited and is the historical comparator only.)
### 7.2 Graded family G
- **M2B** as above.
- **M2H**: M2B with a concept random effect on the threshold, $x_0 + u_c$, $u_c \sim N(0, \tau^2)$,
  $\tau = e^{t}$.
- **M2S**: M2B with a concept random scale multiplying the signal-dependent base scale,
  $\sigma_c(k) = |a\,\mu(k)+b|\,e^{v_c}$, $v_c \sim N(0, \omega^2)$, $\omega = e^{w}$.
- **M2K**: single-state skew-normal $y \sim \mathrm{SN}(\xi(k), \omega(k), \alpha(k))$ with
  **location** $\xi(k)$ the M2B logistic form, **scale** $\omega(k) = |a\,\xi(k) + b|$, **shape**
  $\alpha(k) = \alpha_0 + \alpha_1\,\xi(k)$ (Azzalini; the mean is $\xi + \omega\delta\sqrt{2/\pi}$,
  $\delta = \alpha/\sqrt{1+\alpha^2}$ — location and scale are not mean and SD).
### 7.3 Mixture family X (ordered parameterisation)
For every new member: $\mu_{\text{low}}$ free; $\mu_{\text{high}}(k) = \mu_{\text{low}} + e^{\delta_0} +
e^{\delta_1}\,\mathrm{lg}_h(k)$ — strictly above $\mu_{\text{low}}$ at every level; $A(k) =
1/(1+e^{-\kappa_A(k-x_0)})$.
- **M3** as inherited (historical comparator; unordered).
- **M3H**: ordered M3 with $A(0)=0$ and $u_c \sim N(0,\tau^2)$ on the shared $x_0$ of $A$ and
  $\mathrm{lg}_h$; shared $\sigma = e^{s}$.
- **M3V**: ordered M3 with $A(0)=0$ and component scales $\sigma_{\text{low}} = e^{s_0}$,
  $\sigma_{\text{high}} = e^{s_1}$, each floored at $0.05\,\mathrm{SD}_{\text{train}}(y)$ where the SD is
  that of the outer training fold (CAL for CAL fits) — never a CONF-wide SD; implemented as
  $\sigma = \text{floor} + e^{s}$ (v1.2), the smooth form of the floor.
- **M3L**: ordered M3 with a free catch-level occupancy $A(0) = \pi_0 = \mathrm{lg}(\theta_0)$ and the
  catch-level high emission $\mu_{\text{high}}(0) = \mu_{\text{low}} + e^{\delta_0}$ (not forced to
  $\mu_{\text{low}}$), so the catch mixture is identifiable whenever $e^{\delta_0}$ is not negligible;
  spontaneous occupancy is read from $\pi_0$ with its CI.
### 7.4 Fitting (v1.2: `models.py`)
Multi-start: 8 starts from the declared generator in `models.starts_from_moments` — data moments of
the training fold only (the inherited members keep the inherited moment initialisation; the ordered
mixtures start at the catch-level mean, the log offsets from the level means, unit slopes and the
midpoint-crossing level); start 0 unjittered, starts 1–7 jittered by a seeded $N(0, 0.25^2)$ per
coordinate in the optimiser's own parameter units (the raw vectors of §7.1–7.3). Each start is
L-BFGS-B (`ftol=1e-10, gtol=1e-6, maxiter=2000`) on the **analytic gradient** (JAX, x64); Nelder–Mead
is not used — the §14 start count is not computable with derivative-free fits (v1.2). A run is
*converged* if L-BFGS-B reports success. The kept solution is the converged run with the highest
training log-likelihood; if no run converged, the highest-likelihood run is kept and flagged. All
likelihoods in log space (`logsumexp` for mixtures). Random-effect integrals per concept by a
**two-scale trapezoid rule** in log space (v1.2, revised after the Codex review of v1.2): the mode
$\hat u_c$ of the concept's log-posterior in $u$ is found by a nine-point grid over $\pm 4\tau$ and
four safeguarded Newton steps (unrolled in the differentiated graph, so the gradient is exact); the
Laplace SD $\hat s_c$ is taken there and **capped** at $\tau$ by the curvature safeguard; the peak is
integrated by a $P$-point trapezoid rule on $[\hat u_c \pm 6\hat s_c]$ and the rest of the prior's
range, $[-6\tau, \hat u_c - 6\hat s_c]$ and $[\hat u_c + 6\hat s_c, 6\tau]$, by two further trapezoid
rules with $P/3$ points each (32 at $P = 96$) and exact endpoints, so that a flat tail or a second mode (M2H's
anchored mean returns to $\mu_{\max}$ at both extremes of the shifted threshold) is carried by the
outer rules. Why not Gauss–Hermite: prior-centred nodes do not converge at the CONF cluster size
(`verify.py` V3 — with 168 trials per concept 80 nodes still miss by 0.06–0.3 nat, so the v1.1 ladder
never terminates), and mode-centred nodes fail for the concepts whose shifted threshold leaves the
level range (a flat likelihood in $u$, a truncated-Gaussian posterior; 1–5 nat off at $\tau = 2$ with
the counts tried). The independent check is `audit_quadrature.py`: every hierarchical member at
every grid value against dense quadrature (80,001 points over $\pm 10\tau$) at the generating
parameters, at the **fitted** parameters on the held-out and training concepts, and under cross-fits
to the other family's data. At $P = 96$ (2026-09-11): max error $3.1 \times 10^{-4}$ nat over every
generating and fitted case, and $3.6 \times 10^{-3}$ nat in one cross-fit — M3H fitted to M2S data
at $\omega = 2$, where the fitted slope is so large that the likelihood in the threshold shift is a
staircase and the trapezoid error falls only linearly with $P$ ($5.4 \times 10^{-3}$ at 64,
$1.7 \times 10^{-3}$ at 128). These are observed errors of the likelihood at the audited parameters,
not a bound on the whole refitting and selection procedure; the case error over $n_c$,
$2 \times 10^{-5}$ nat per trial, is the size of the per-trial score perturbation at those
parameters, a hundred times below the smallest declared effect. Pass rule: < 1e-3 nat in the
generating and fitted cases, < 5e-3 in the cross-fits. $P$ is set on CAL/PILOT by raising it
(64 → 96 → 128) until every concept's joint log-likelihood changes by < 1e-3 at full cluster size
($n_c = 6 \times 7 \times D$), then frozen.
**Fitter start policy and array padding (draft amendment, 24 Sept 2026; ledger row 4).** Declared here
before the snapshot that adopts it; no fit has been run under it. *Why per member.* The numerical audit
(14 Sept, 96 units, 1,536 member-fits) found the pipeline's cold starts miss the best-found optimum in 10.5 %
of fits, and the misses are a property of the fitted member, not of the generator: outer and inner miss rates
run M3H 0.281/0.198, M2K 0.125/0.188, M3 0.115/0.167, M3L 0.094/0.115, M2H 0.094/0.104, M3V 0.083/0.104,
M2S 0.000/0.010, M2B never. The controlled comparison (14 Sept, `score_prefixes.py`) shows width and count
trade differently by member, so a uniform rule is the wrong shape: M3H reaches miss 0.039 with 16 starts at
jitter 0.50 against 0.133 with 64 at 0.25, while M2H reaches 0.016 with 64 at 0.25 against 0.078 with 16 at
0.50. *The declared policy,* applied identically at the outer and inner sizes and to every use of the fitter:
M3H, cold starts plus **32 at jitter 0.50** (the 15 Sept JOB C check compared 16 against 32 under a rule
frozen before it ran: 4 of 128 misses against 10, so 32 is adopted and the gain is recorded as thin);
M2H, cold plus **64 at jitter 0.25**; M3V, cold plus **32 at jitter 0.25**, since its misses vanish under 32
or 64 narrow but the first 16 narrow still miss 4 of 128; M3, M3L, M2K and M2B, cold plus **64 at 0.25 and 16
at 0.50**, affordable because every one of these costs at most 0.31 s per start, with M2K's four
separated-skew starts leading its batch as now. **M2S is declared OPEN and takes the conservative interim of
cold plus 64 at 0.25.** Codex's 14 Sept review requires a paired comparison of cold-only against 64 narrow
for M2S before adoption and that comparison has not been run; M2S's single audit miss was recovered only by
the 60th added narrow start, so neither cold-only nor a small batch is established as sufficient. M2S's final
recipe is set by that comparison, not here. *Seeds, ties, recovery and archive.* Each added start draws from
a seeded stream keyed by (member, size, fold, replicate, start index), disjoint from the cold starts' stream
and recorded per fit; the kept solution is the converged start with the highest finite training likelihood,
ties broken by the lowest start index so the choice is deterministic; the §9 recovery chain is unchanged (16
further starts, then 16 at twice the jitter, then the best finite non-converged start, flagged); and every
start's parameters and likelihood are archived at **full precision**, because the existing archive holds six
decimals and rounded ties make bitwise re-derivation impossible. *Padding.* `models.PAD_MULTIPLE` moves
**512 to 64**. Measured, not projected: across the ten distinct trial totals the padding waste is 5.3 % at
512 and 0.8 % at 64, so the saving is 4.5 % at D = 4, about 1,800 core-hours. It is numerically inert —
identical log-likelihood and gradients agreeing to 1e-13 — and it changes only how many padded rows the jit
cache carries. It is declared here rather than applied as a code fix because `analyze.numerical_snapshot`
digests the code files as loaded, so any edit to `models.py` changes every later row's `code_hash` and
spotcheck refuses mixed-hash stages. *Scope.* An adopted policy applies alike to the original estimate, its
refitting bootstrap and the independent reference means. Evidence already landed under the eight-start
procedure — the d4v12b rows, the running probe, the control and the reference banks — stays old-policy
evidence, is never relabelled, and is never pooled with new-policy evidence. *Not yet adopted.* Final
adoption still requires the M2S comparison, the frozen policy run through the actual nested selection on
independent seeds with coverage, false-positive rate, power and failure frequency with Monte-Carlo
uncertainty, and its cost measured on the intended machine. This declaration fixes what will be tested; it
does not assert that it passed. *Implemented* (2 Oct 2026, RSC `5f6333c`): `models.START_POLICY` and the
`policy_key` argument of `models.fit` — the cold starts from the caller's stream, then each member's added batches,
every added start from its own stream keyed by (member, size, fold, replicate, start index) with the dataset seed
and layer tag standing for the replicate inside the pipeline, start indices running on across cold, added and
recovery starts, the kept solution the converged start with the highest finite likelihood and ties to the lowest
index; `PAD_MULTIPLE` 64; `analyze.Config.start_policy` switches it on at both sizes and every call site, and the
policy table, its open members and the padding enter `dataset_identity` and `config_hash`; the reference-bank
archive stores every start's parameters and likelihood at full precision. Without a key the v1.2 fit is unchanged,
so the historical rows' hash lineage is preserved on the legacy path. Tested on mechanics only
(`test_start_policy.py`: the table, keyed and disjoint streams, the tie-break, padding inert to 1e-13, cold plus
added counts, the legacy path, the hashes). Still not adopted: the M2S comparison and the validation above remain.

### 7.5 Recovery of the family distinction (before v2; `simulate.py` outputs committed)
Generators: every member of G and X at CAL/PILOT-fitted parameters and across a frozen grid —
heterogeneity $\tau, \omega \in \{0, 0.5, 1, 2\}$ (in level units / log-scale units), component
separation $e^{\delta_0}/\sigma \in \{0.5, 1, 2, 4\}$, catch occupancy $\pi_0 \in \{0, 0.05, 0.2\}$,
skew $\alpha \in \{0, 1, 3\}$ — 48 generator points (`simulate.recovery_points`), 200 replicates each
at CONF cluster sizes; the first pass (v1.2, `run_sims.sh`) runs 20 replicates per point on one
synthetic layer, the remaining parameters of every generator at the declared base of `simulate.py`
(graded: $\mu(0) = -1$, $\mu(8) = +1$, $x_0 = 3$, $\kappa = 1.5$, $\sigma = |0.15\mu + 0.75|$; mixtures:
$\mu_{\text{low}} = -1$, $\sigma = 0.6$, $A(k) = \mathrm{lg}(1.5(k-3))$, $\mu_{\text{high}}(k) = \mu_{\text{low}} +
\text{sep}\cdot\sigma + \mathrm{lg}_h(k)$). The full family decision of §8 is run on each. Reported: the
family confusion matrix per generator and grid point. **No member is
dropped for being individually unrecoverable**: nested members are expected to coincide at some
parameters. A member is consolidated only under an explicit rule — its held-out joint score never
differs from a sibling's by more than 1e-4 nat/trial anywhere on the grid (redundant), or it fails
numerically after the §7.4 recovery (repair first). A graded generator classified as mixture is a
discrimination failure that §10's calibration must absorb, not a reason to remove the generator.
The family is frozen after this step.

## 8. Primary analysis *[frozen]*

### 8.1 Joint concept scoring (the one scoring definition)
Five concept-disjoint outer folds on CONF, stratified by family (8 per family; the same folds for every
model and layer; `folds.json`); decoders and scaling are frozen from CAL, so nothing in the outer
split touches decoder training. For member $m$, concept $c$ with trials $i = 1..n_c$ and effect $u$:
$$q_{m,c} = \int \prod_i p_m(y_{ci} \mid k_{ci}, u)\,p_m(u)\,du,$$
the integral absent for non-hierarchical members. The primary family predictor is
**training-only selection**: for each outer fold and layer, the member of each family with the best
inner 4-fold concept-disjoint (stratified) joint log score on the training concepts is selected,
refitted on all training concepts, and scores the held-out concepts: $q_{F,c} = q_{m^\ast_F,c}$.
$$\Delta_c = \frac{\log q_{X,c} - \log q_{G,c}}{n_c}.$$
Sensitivity predictors, reported alongside: the equal-weight ensemble of joint likelihoods,
$q_{F,c} = \frac{1}{|F|}\sum_{m \in F} q_{m,c}$ (a mixture over members of the concept-level
likelihood, not a per-trial average); and the historical pair M3 vs M2B (H1′). The estimand is the
out-of-sample joint log-score advantage per trial of the training-selected mixture member over the
training-selected graded member; a positive result rejects those graded predictors, not the graded
class.
### 8.2 Uncertainty
Primary CI: concept-cluster bootstrap of the fixed out-of-fold concept scores $\Delta_c$ — resample
whole concepts with replacement within each of the eight family strata, 2,000 replicates, carrying
every layer, level and carrier of a concept together (`analyze.band_bootstrap`). Foil pairs cross
families, so they cannot be kept together under family strata (v1.2): the primary R1 statistic
resamples concepts; the paired statistics of §6.4 and §8.5(b) resample foil pairs as the unit,
unstratified. This is a
conditional approximation (it does not re-run the density fits); its coverage is validated in §10 by
simulations that regenerate the data and refit the pipeline. If simulated coverage of the nominal
95 % interval is below 0.90 under any retained generator, the pipeline-refitting bootstrap (200
replicates, all copies of a concept in one fold) replaces it as primary — decided and recorded before
CONF is read. Per-family (8) summaries with the same CIs.
### 8.3 Layer summary and criterion
Band mean $\bar\Delta_{\text{ws}}$ over the frozen layer grid within 23–57 (primary; the grid is every
layer, or a fixed stride of 2 if the §14 benchmark requires it, frozen at v2), $\bar\Delta_{\text{early}}$
over 3–15, $\bar\Delta_{\text{late}}$ over 58–62; the band maximum is reported with its location but is
not the criterion. **Mixture support:** the 95 % CI of $\bar\Delta_{\text{ws}}$ excludes 0 and is
positive. **Graded support:** excludes 0 and is negative. **Inconclusive:** includes 0. No layer
selection on CONF.
### 8.4 Secondary, reported alongside
The historical SPM curves (spm_BMS on the averaged held-out ML scores, all members and the three
inherited ones), an inherited assay without Bayesian calibration; H1′; within-family member scores;
per-family directions (count of families whose $\bar\Delta_{\text{ws}}$ has the pooled sign; no
threshold); fitted high-state occupancy by level, separation $(\mu_{\text{high}} - \mu_{\text{low}})/\sigma$,
M3L's $\pi_0$; R2 and $\pi$ profiles by level with CIs; the descriptive ten-bundle display.
### 8.5 Target bridge (H1-T; an analysis of the same captures)
(a) The §7–§8.3 comparison run on $y = r_2$ (the target–foil projection, z-scaled with CAL
constants) instead of R1, same folds, same predictors, same criterion; (b) at fixed $k \in \{2,3,4\}$,
the R2 mean in R1-assigned high-state trials minus low-state trials (state = posterior of the
training-selected mixture member at the reference layer of §11, > 0.9 / < 0.1), with a concept-cluster
CI. H1-T holds if (a) gives mixture support in the band and (b)'s CI excludes 0 in the positive
direction. Precondition: §6.4(i). If (a) or (b) fails, or §6.4(i) fails, the result is written as a
coherence-readout result and "discontinuous access" is not used.

## 9. Outcomes and technical failure *[frozen]*

- **Mixture support / graded support / inconclusive** by §8.3 on R1 (primary: active condition,
  active-trained decoder — one H1). The no-target-report condition (§12) is a secondary analysis with
  its own pre-declared predictor order (transfer decoder primary, separately trained decoder as
  sensitivity); it does not offer a second chance at H1.
- **Technical assay failure** (reported as such, no scientific reading): PILOT held-out decoder
  accuracy at $k=8$ vs $k=0$ below 0.75 in more than a third of band layers; capture-parity failure;
  suffix-tokenization failure; a retained member that cannot be scored after the §7.4 recovery
  (16 further starts, then a doubled jitter) — in which case the **primary comparison is unavailable**
  and any reduced-family result is a secondary amended analysis, never the H1 result. **Amended
  policy for the inner selection** (v1.2, weaker than the rule above and declared as such): a member
  whose inner fit or inner held-out score is not finite after the recovery scores $-\infty$ and
  cannot be selected, and is recorded; if every member of a family is unscorable in a fold, the
  primary comparison is unavailable. Inner convergence and the count of non-finite inner scores are
  reported beside the refit convergence, and the simulations of §10 run under this policy.
- **Coherence-only reading** (a scientific outcome, not a failure): §6.4(i) or §8.5 fails; H1 is
  reported on R1, H3 is not run.
- **Underpowered** (§10) is declared before CONF and reported with the result.

## 10. Calibration and power *[rule frozen; the grid and counts frozen at v2; `simulate.py` outputs committed]*

Simulated: the **full** §8 procedure — outer folds, inner selection, refit, joint scoring, the §8.2
bootstrap, the band mean and the §8.3 rule, the §7.4 convergence handling and the §9 failure rule —
on synthetic CONF-sized data at the frozen layer grid, with concept effects and the measured residual
correlation across layers (from PILOT) generated as declared in `simulate.py`. Nulls: **every retained
graded member** (M2B, M2H, M2S, M2K) at CAL/PILOT-fitted and grid parameters; alternatives: every
retained mixture member at per-trial gains 0.003 (the human scale), 0.01 and 0.03 nat — the gain
being the expected out-of-sample joint log-score advantage per trial of the generator over the best
graded member fitted at large sample (256 concepts), reached by scaling both high-state offsets
(`simulate.calibrate_gain`; the truth term is scored under the generating density). **Acceptance
gate** (v1.2 after the Codex re-check; `simulate.gain_gate`, enforced when the gain file is written
and again when it is loaded): the twelve (member, gain) pairs present exactly once; scale, gain,
check and check-SE finite; every graded reference fit converged in the calibration draw (8 × 32
concepts) and in the independent check draw (a fresh seed, 8 × 64 concepts); the check's SE — the
test-concept variation conditional on the check's own fitted graded reference — at most 20 % of the
target; and the check within 25 % of the target. A pair that fails is recalibrated with more
reference simulation or the gain claim for that pair is changed explicitly; the power stage does not
run on a file that fails. "0.003 nat" is a numerical reference scale, the oracle-to-large-sample-graded
separation, not the finite-design selected-X-versus-selected-G $\bar\Delta$ nor the human historical
pair's gain. For run `d4v12b`, whose job code recorded the check without enforcing it, the gate is
applied to the recorded entries with the check recomputed at 8 × 64 concepts
(`simulate.revalidate_gain_entries`) before any power result is read; a pair whose scale the gate
would change has its power replicates and five-layer rows rerun under a new namespace. Counts: 1,000 datasets per generator and setting (Monte-Carlo SE ≈ 0.7 pp at a 5 %
rate). The §14 benchmark (v1.2) puts one dataset through the full procedure at 900 s per layer on one
Mac core, so the full counts on one synthetic layer (12 nulls and 12 alternatives at 1,000, the 36
mixture recovery points at 200, the five-layer pilot) are ≈ 9,000 Mac-core-hours per $D$ — not this
machine's work (owner, 11 Sept: it is too slow and not always on). The simulations run as sharded, resumable SageMaker
training jobs in the cloud (`t1_job.py`, `launch_t1.py`; results under
`s3://xtenure-cself-pvr/results/t1_access/<run>/`, one immutable code snapshot and one result
namespace per numerical configuration, every row and the gain file carrying the code/config hash,
resumes refused across hashes; per-concept scores and the selected members per layer and fold are
saved with every replicate for offline re-scoring), $D = 4$ first and $D = 8$ only if the §10 power
rule asks for it. The recovery grid's twelve graded points at replicates 0–199 are the calibration
stage's first 200 replicates (same seeds, same configuration) and are reused, not refitted. The run
launched on 11 Sept 23:00 UTC (160 shards on 50 jobs: 20 managed-spot and 22 on-demand
`ml.c8i.2xlarge`, 8 on-demand `ml.c8i.48xlarge` with fifteen shards each) was stopped after one hour
on the Codex review of v1.2 and its rows discarded. **The corrected run, `d4v12b`, launched on 12
Sept 00:38 UTC** from commit `52267ec` with the same fleet layout, code snapshot
`code/t1_access/d4v12b/`, results under `results/t1_access/d4v12b/`; at the §14 cost of the
corrected method (900 s per layer on a Mac core; 83 min per replicate on a loaded small-instance
vCPU) it is expected to take 45–50 h. Runtime: Python 3.12, jax 0.11.1, numpy 2.4.6, scipy 1.18.0,
pandas 3.0.5, joblib 1.5.3 on x86-64 Linux (logged by every job and written into every row from the
next snapshot on; the launcher pins them so a resume is the same runtime). Codex's re-check of the
fixes (17:45 PDT) accepted findings 1–5, 10 and 12 and held finding 7 open until the gain gate above
existed; two integration slips in the gate commit were fixed at `eae1cb8` with mocked tests, the
revalidated-artefact path at `fa83301`; **Codex's final verdict (17:56 PDT): on board** — continue
`d4v12b` as the per-layer calibration and recovery run, power results held until the revalidated
gain artefact passes, band validation a separate post-PILOT stage. The owner funded the run on that
verdict (12 Sept), with spot checks throughout: the landed rows are read at every stage boundary
(`spotcheck.py`), not only at the end. **Calibration stage of `d4v12b`, read 12 Sept 18:30 UTC at 11,923 of
12,000 rows (every null at $n \ge 958$):** the false-positive rate is 0 of 11,923 under all twelve graded
nulls (one-sided 95 % upper limit ≈ 0.3 % per setting), convergence 1.000, no failures; the interval coverage
of $\theta_g$ is below 0.90 for six settings — M2H $\tau = 0.5$ (0.819), $\tau = 2$ (0.894), M2K
$\alpha = 1$ (0.884), M2S $\omega = 0.5$ (0.848), $\omega = 1$ (0.780), $\omega = 2$ (0.216) — so the
**§8.2 replacement by the refitting bootstrap is invoked** (coverage below 0.90 under any retained
generator). At the strongly graded M2S points the misses are one-sided (intervals above the target: 784 of
784 at $\omega = 2$, 216 of 220 at $\omega = 1$), but at M2H $\tau = 0.5$ (86 of 181 above) and M2K $\alpha = 1$
(51 of 115) they fall on both sides — under-dispersion, not a pure shape problem (corrected 13 Sept from the
offline rescoring; the earlier "every miss above" was true only of $\omega = 2$); at $\omega = 2$ the root-mean-square bootstrap
SE (22.0) matches the replicate SD (23.2), so the failure is tail sampling and interval shape under a
heavy-tailed held-out loss (one concept in one replicate at $-26{,}627$ nat): extreme tail losses and the
percentile interval's shape must be investigated alongside fitting and selection variability — RMS-SE agreement
alone does not separate these mechanisms (Codex, 12 Sept, review 3), and the categorical exclusion of fitting
variance is withdrawn.
Disposition (Codex review, 12 Sept): the refitting bootstrap is corrected first (original-concept grouping at
both fold levels; failed replicates propagated), benchmarked, and the chosen interval validated on new seeds
with declared counts — the choice is recorded as method development on these rows, never as their
validation; M2S $\omega = 2$ stays as the declared stress condition; the rows keep their code/config hash
and an explicit cross-snapshot reuse manifest carries them forward. **The refitting bootstrap was corrected the same
day** (`analyze.refit_bootstrap`, `grouped_stratified_folds`, `Dataset.group`; `test_refit_bootstrap.py`): the
copies of an original concept share a fold at both levels; the grouped fold maker reduces to the plain one when
every group is distinct, so the plain analysis and every d4v12b null fit are reproduced bit for bit; the
analysis's own outer folds are passed in, each copy staying in its original concept's outer fold (the declared
fixed-fold specification); a resample whose procedure fails, or whose band scores are not all finite, yields no
statistic (no `nanmean`), and **the interval is usable only when every replicate is scored** — a lower fraction is an
explicit amendment with a missing-tail analysis, never a default (Codex re-check). The interval method is a declared
`Config` choice carried through the runner (`interval = "cluster" | "refit"`, `n_boot_refit`, both in the code/config
hash and in every row): with `"refit"` the point estimates stay the fixed scores' band means, the cluster interval is
kept beside, the three predictors and the paired ws − early statistic come from the same refits, and an unusable
refit interval is an **assay failure**, never an inconclusive reading (`decide` on a non-finite interval returns
"unavailable"); the per-replicate statistics are returned for persistence and rescoring (`test_interval_path.py`).
Three flags are kept apart in every row (Codex, third review): `failed` (the original fits and points are
invalid), `primary_available` (valid points and a usable primary interval) and each predictor's own interval
availability; every valid point estimates the unconditional target $\theta_g$ whether or not its interval could
be built, coverage is computed among that predictor's finite usable intervals, and the missing intervals are
counted and reported as a performance result of their own (Morris, White & Crowther 2019, §5.1). Every band,
the paired ws − early statistic, the companion cluster interval, the bootstrap's seed, policy, folds, failure
reasons and per-replicate statistics are written with the row; completed resamples are checkpointed as they
finish and a restart resumes them. The launcher carries the declared interval method and replicate count into
the job's environment and hash (`launch_t1.py --interval --n-boot-refit`). **After Codex's fourth review (same
day):** a checkpoint is keyed by the bootstrap's complete data-and-procedure identity (`analyze.dataset_identity`:
a digest of the response array, levels, concept and family mappings, group, exact layer ids, generator metadata,
every numerical setting, the seed, B and the actual outer folds) and a record is reused only when its identity,
seed, B, resample index and drawn concepts all match — a damaged record is counted and recomputed, never
accepted; the dataset seed of a grid point with two or more values is a digest of the sorted grid (the v1.2
weighted tag gave M3H $(\tau = 0.5, \text{sep} = 1)$ and $(\tau = 2, \text{sep} = 0.5)$ the same seed), while every
point with at most one value keeps its v1.2 seed, so the `d4v12b` null rows are unchanged; the revalidation
writer, the job and the monitor share one accepted-artefact contract (`simulate.accepted_gain_artefact`: the
run's hash, D, the source digest and the revalidation identity authenticate a revalidated file, which then holds
the job exactly as it holds the monitor when its gate failed); every reference start, the §9 recovery batches
included, carries its initial vector and batch id from where it is generated; every job keeps its checkpoints
synced to S3 and the row carries every band's companion cluster interval and the bootstrap identity. **After the
fifth review:** the identity also binds the numerical implementation actually executed (digests of the code
files, the model globals that steer fitting outside the Config, the runtime), every checkpoint record carries a
checksum of its complete payload and an interrupted tail is repaired before appending; a revalidated gain
artefact must carry every identity field and match the job-written file beside it, a retrieval failure is never
read as an absence (the job holds), and each shard mirrors only its own checkpoints. **After the sixth review:**
the code digests in the identity are those of the code as loaded (bound at import, never re-read from disk), and
a revalidated artefact without the job-written file beside it is refused by the job as by the monitor. **After the
seventh review:** `models.py` binds its own digest at its own import, and the code/config hash written into every
row and gain file is computed from the three bound digests, so a row names the implementation that produced it;
the `d4v12b` rows keep their stored hashes and the reuse manifest (open) maps them.
Cost (`bench_refit.py`, one Mac core, one layer, D = 4, M2S $\omega = 0.5$, inner selection at 4 starts): 15.3 min
per replicate, so 200 replicates ≈ 51 Mac-core-hours per dataset per layer; the cloud cost is **not** established by
this — the corrected procedure is benchmarked at the intended cloud concurrency before any projection (loaded cloud
fits ran several times slower than the Mac in `d4v12b`), and the R2/H1-T and declared additional analyses need their
own accounting. **Validation plan (candidate amendment, Codex re-check):** the interval choice is screened cheaply
first, then validated on new seeds at declared counts with Monte-Carlo intervals — R = 400 datasets × B = 200
replicates per setting (Monte-Carlo SE ≈ 1.5 pp at coverage 0.90, 1.1 pp at 0.95; R = 1,000 if the original precision
is kept) with a pre-declared disposition for estimates too close to 0.90 to resolve; every retained null setting and
the declared mixture alternatives, not only the six settings that failed; selection and ensemble scored from the
same bootstrap fits; $\theta_g$ estimated by ordinary-pipeline repetitions without bootstrapping each reference
dataset (eligible old fits may contribute), its uncertainty mattering most at $\omega = 2$; bookkeeping after Morris,
White & Crowther (2019, §§5.2–5.3). **The cheap screening was run on 13 Sept** (`rescore_intervals.py`, on the
Windows PC, on the 12,000 existing rows — method development, not validation): the percentile, basic, BCa,
studentised and normal-theory intervals of the SAME fixed out-of-fold scores reach coverage ≥ 0.90 on 6, 6, 7, 9
and 8 of the twelve nulls respectively, none on all twelve, and the false-positive rate is 0 under every
candidate. The diagnostic that closes the route: the ratio of the between-replicate SD of the point estimate
to the mean interval half-width, which sits near $1/1.96 = 0.51$ for a calibrated normal 95 % interval, is
0.53–0.58 at the seven settings that pass and rises with the graded signal — 0.63 (M2K $\alpha = 1$), 0.69 (M2S
$\omega = 0.5$), 0.71 (M2H $\tau = 0.5$), 1.06 (M2S $\omega = 1$, an interval half as wide as it should be), 4.20
(M2S $\omega = 2$). That ratio is a normal-interval heuristic, not a diagnostic theorem for these heavy-tailed
percentile intervals, and it does not identify which source of variability the interval misses: fit-to-fit
variability is the hypothesis (the numerical audit's misses land on the same two settings, 13 Sept), while tail
sampling and interval shape remain in play (Codex, 13 Sept). What it does establish is that no reshaping of the
fixed-score distribution restores coverage; the pipeline-refitting bootstrap, which resamples the fits, is the
declared replacement and stays the candidate, and a coverage gain from it would support that interval without
by itself identifying the cause. Two records set straight by the same exercise: the
recorded interval endpoints reproduce from the saved per-concept scores to the storage floor only (the scores
were written at five decimals; median deviation $2.4 \times 10^{-7}$, a resampling change would move them by
$2 \times 10^{-4}$), so the reproduction gate is a tolerance of $10^{-5}$ and the next snapshot stores the scores at
full precision; and the miss direction is setting-dependent as stated above. The power stage did not run: the
job-side gain calibration failed the gate at M3L, 0.01 nat (`bisection limit: 0.00806 vs target 0.01`), and no
power, recovery or five-layer rows exist. **Cause, established 12 Sept** (`repro_gain_m3l.py`, `diag_gain_jump.py`;
outputs in `sim_results/d4v12b/monitor/`): the failure reproduces exactly on one Mac core; at the fixed
calibration seed the gain is a deterministic but discontinuous function of the scale — 0.00806 just below
0.684661 and 0.01097 just above — with the selected reference **M2K on both sides**, so not a switch of $G^*$.
The best-found M2K solution at 256 concepts (training log-likelihood −44,543.6) is reached by one start of the
eight-start batch; the other seven end in a basin 155 nat worse whose held-out score is 0.003 nat per trial worse;
at the scale of bisection step 21 that one start lands and at the scale of step 22, $1.6 \times 10^{-6}$ further in
scale ($2.4 \times 10^{-6}$ relative), it slides into the shallow basin, both runs reporting convergence — optimiser
basin loss within M2K (Codex, 12 Sept: accepted; the $G^*$-switch candidate withdrawn). A 5 % search tolerance
cannot be met across a 30 % jump. How often a batch of eight misses the best-found solution is **not established**
by these runs (one batch found it once in eight, a second batch with another seed never; the corrected run's
evaluation at scale 3 found a better M2K solution in one start of 57). **Amendment (calibration side only;
`models.py` and the pipeline untouched; `simulate.expected_gain`, `calibrate_gain`, `gain_gate`, after the Codex
re-check of the same day):** the graded reference fits use 32 jittered cold starts; the distinct basins found
earlier on the bisection path travel as warm starts (up to six per member, deduplicated); a member whose
best-found solution is reached by fewer than two DISTINCT cold starts gets 24 more jittered starts from a further
seed — never the unjittered moment start the cold batch already holds, and mirrored in the skew coordinates on
every second start so both orientations are tried; every start's source, likelihood and convergence are recorded.
The bisection also stops when the bracket has collapsed to 0.1 % in scale; both ends are then re-evaluated with the
full warm set (the evaluated function depends on the search history, so a stale end must not be read as a
discontinuity); if an end is within tolerance the scale is resolved there, else the scale is frozen at the
bracket's centre, the gain re-measured there at twice the concepts and a fresh calibration seed as the declared
fallback (not a further chance to pick a seed), and the jump recorded. The gate additionally requires the selected
reference's best-found solution reproduced by at least two distinct cold or extra starts in the calibration draw
and in the check draw (a warm-start discovery never counts as a cold one) and the calibration-side gain within
25 % of the target; the check is warm-started on its training draw only, its test draw is never fitted. **After Codex's
third review (same day):** the evaluation that is gated and archived is always the FINAL one, made at the chosen
scale on the calibration draw (its seed and concept count recorded) — never an endpoint evaluated for another
purpose; if the second re-evaluated endpoint finds a basin the first had not seen, the first is refreshed before
the pair is read. That final evaluation, and the check on its own training draw, carry a declared **training-only
challenge**: an independently seeded batch on the same training data — four starts at the moment start with the
skew coordinates set to every sign combination of ±2 (deliberately separated basins) and jittered starts at twice
the jitter — run before any test score is read; if it improves the best likelihood by more than 0.5 nat the
reference IS the improved solution, the gain is scored against it and the improvement is recorded, and the
reproduction count then refers to it (an independently seeded challenge discovery counts; a warm start's never).
Every start's source, batch and seed ids, initial vector and final vector are archived; reproduction counts
DISTINCT initial vectors. Reproduction by two starts is not proof of global optimality: it says the best-found
solution was reached independently twice, and the rarity of a miss under this scheme is not yet demonstrated. The
twelve-pair artefact is computed **once** (`TASK=gain`, or locally), validated (`spotcheck --revalidate`, the
legacy route: one declared check, never a search over check seeds, every check field rewritten together) and read
by every power job through the same rule as the monitor's — the revalidated artefact when it exists, else the
job-written one, both under the run's hash; a power job whose namespace lacks it fails closed (`t1_job.gain_file`).
Reaching the one failed pair does not approve the other eleven. **Diagnostic result (12 Sept, one Mac core, the
first-fix code `a508601`: 32 cold starts, the previous winner as warm start, reproduction ≥ 2, no challenge):**
M3L at 0.01 nat RESOLVED in ten search evaluations (119 min) — with the deep M2K reference found, the gain is
continuous and monotone in the scale (0.00537 at 0.627, 0.00770 at 0.678, 0.00916 at 0.705, 0.00997 at 0.719,
0.01084 at 0.733) and the scale is 0.7188, not the 0.685 the shallow reference had collapsed onto; check 0.01003 ±
0.00052 (64 per family, fresh seed), gate passed. The deep M2K solution was reached by 2–4 of the 32 cold starts at
every scale above 0.63 (6 of 32 in the check), so the reproduction rule was met but not by much. **Under the final
code** (9b277df: cold starts with provenance, basin set, the training-only challenge, the challenged final
evaluation gated) the same pair gives the same answer to every printed digit — scale 0.71878, gain 0.00997, check
0.01003 ± 0.00052, gate passed, 250 min on one Mac core — and the challenge found no better reference, while the
reproduction of the M2K solution now rests on 18 of 63 distinct starts at the final evaluation rather than 2 of 32.
Both runs are diagnostics of one pair; the twelve-pair artefact is the run of `calibrate_all_gains` under that
code, on the Mac, with the same seed, D, layer and inner-start count as the power jobs' Config. **Open, before v2 (Codex, finding 6):** the same fragility may sit in the pipeline's own refits (§7.4,
eight starts, at the inner and outer training sizes of ≈ 38 and 51 concepts); FPR 0 under the M2K nulls does not
show every graded fit was accurate. A numerical-sensitivity audit on declared representative draws, mixture-shaped
data included, with stronger training-only reference searches, decides whether §7.4 is amended for the new
snapshot (never a warm start from another CONF fold that holds the current held-out concepts; CAL-derived starts
and within-training-fold searches are allowed). d4v12b's immutability is a provenance constraint, not a reason
to keep a demonstrated weakness in the eventual CONF pipeline. The historical M3-versus-M2B contrast, saved with every
row, returns mixture support in 651 of 1,000 M2H $\tau = 2$ and 337 of 1,000 M2S $\omega = 2$ replicates —
a simulation demonstration of the inherited pair's vulnerability to omitted heterogeneity.

**What the single-layer simulations establish, and what they do not** (v1.2 after the Codex
review): with one synthetic layer per dataset they calibrate the **per-layer procedure** (inner
selection, refit, joint scoring, the concept-cluster interval) and establish the family recovery;
they do not by themselves certify the **35-layer band rule** of §8.3, whose validation needs the
frozen band grid, the cross-layer heterogeneity and residual correlation measured on PILOT, every
retained null family, and Monte-Carlo precision adequate to the thresholds. That band validation is
its own pre-specified stage, run after PILOT with the measured correlation structure, with counts
declared at v2; its grid is never chosen from the outcome of a pilot. The five-layer stage of the
present run (every graded member at one grid value — M2B; M2H $\tau = 0.5$; M2S $\omega = 0.5$; M2K
$\alpha = 1$ — and every mixture member at the 0.01 nat gain, on layers 25, 33, 41, 49, 57, 200
replicates) is a computational pilot of the layer averaging, not that validation. Until PILOT is
read, the cross-layer residual correlation is a declared AR(1) stand-in with coefficient $\rho = 0.9$
**per physical layer** (so $0.9^{8}$ between sampled layers eight apart), the mixture state is
shared across a trial's layers and the concept effect is shared across layers.

**Coverage estimand** (v1.2): the interval's coverage is assessed for
$\theta_g(D, L) = E[\bar\Delta_{\text{ws}}]$, the expectation of the complete procedure's band-mean
held-out score difference under generator $g$ at the design sizes, over the stimulus draws, the folds
and the optimiser's randomness — an unconditional algorithm-performance target, estimated by the
replicate mean with its own Monte-Carlo SE reported; coverage is reported among usable intervals and
failures separately. It is not the oracle gain of `expected_gain`, not the conditional risk of the
particular fitted predictors, and not the risk after training on all 64 concepts. Two separate
failures:
- **Calibration**: the false-positive rate (mixture support under a graded null) must be ≤ 0.064
  (0.05 + 2 SE) for every null at the chosen $D$, and CI coverage ≥ 0.90. Failure at $D=8$ requires
  revision **before CONF** — permitted changes, frozen here: the bootstrap type (§8.2), the family
  predictor (selection vs equal-weight), the band summary (mean vs trimmed mean) — recorded as a v2
  amendment; the underpowered fallback does not apply to a calibration failure.
- **Power**: draws per (concept, carrier) $D \in \{4, 8\}$ — the smallest $D$ with power ≥ 0.8 at
  0.01 nat under every mixture alternative; ceiling $D=8$ (21,504 trials per condition). If $D=8$
  gives power < 0.8 at 0.01 nat, the study is declared underpowered below that scale and proceeds at
  $D=8$ with that statement in the paper.

### 10.1 Reference plan and the coverage decision rule (draft amendment, 24 Sept 2026; ledger row 4)

Declared before the interval validation buys anything, because the failure it guards against is reading a
coverage number against the wrong target. *The reference files are pinned by path and hash, not by
directory.* The top-level `sim_results/ref_m2s_omega2_aac9f69/calibration_D4.csv` holds **128 rows**, not the
1,000 the reference needs; the 1,000 distinct replicates are the ten `final_2026-09-15/calibration_D4.shard*of010.csv`
files, whose mean agrees with the compact bank in `reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv`
to 1.42e−14 on matched points. Every coverage reading names the exact files and their SHA-256. *The targets.*
At M2S ω = 1 the historical reference is −0.869513 with a Monte-Carlo SE of 0.011242 (2 MCSE 0.022483), recomputed
on 13 September from the complete old-policy calibration rows at that setting (its file and hash are pinned per
setting when a reading is taken; the ten `final_2026-09-15` shards above are **ω = 2's** bank and pin nothing at
ω = 1) — tight enough to read coverage against for the old procedure, and for the §7.4 policy sensitivity evidence
only: a policy-matched ω = 1 reference with its own target-estimation and error plan is generated and pinned under
its own ledger row before any coverage is read against it. At M2S ω = 2 the reference is −6.869911 with a Monte-Carlo SE of 2.678379 (2 MCSE 5.356758), a median of −2.065273, a minimum of
−2650.300023, and a mean that moves to −4.223835 if that single point is dropped — and dropping it, or
substituting the median, changes the estimand rather than repairing it. A ±2-MCSE band there is a
**sensitivity range, not a confidence set**, and coverage swept across it moves from 4 of 20 to 18 of 20 on
the completed B = 50 probe. ω = 2's target may therefore remain unresolved, and row 7's existing rule applies:
if it cannot be pinned down within budget, report it unresolved and stop spending there. *Order of testing.*
ω = 1 is the first coverage purchase: it has a known cluster failure, a tight reference, and an unresolved
B = 50 result whose exact 95 % interval on 17 of 20 is [0.6211, 0.9679]. ω = 2 is retained as a required
stress condition, not dropped. *Resamples.* B = 200, never 50: at 200 each 2.5 % tail holds about five
resamples and at 50 about 1.25, so a negative screen at 50 could not rule the method out. *The decision rule,
for one standalone single-setting single-look screen at 100 fixed attempted datasets (each method's usable $n$
and failures reported, its exact bound recomputed at that $n$, the cutoff below applied only at $n = 100$).* Stop for futility when the
one-sided 97.5 % exact binomial upper bound falls below 0.90, which is **83 or fewer covered of 100** — at 83
the bound is 0.897735 and at 84 it is 0.905690. Carry the reference uncertainty: for a justified target set
$T$ — a declared 99 % reference confidence set, mean ± $t_{0.995,\,n-1}$ × MCSE under predeclared normal-approximation,
tail and stability checks — let $K_{\max}$ be the largest number of intervals containing any $\theta \in T$, computed
over every interval endpoint and intervening segment of $T$ with inclusive ties (a containment argument, not a
binomial count at a fixed target), and require the same failure at $K_{\max}$, so that even the most favourable target
fails; the one-look erroneous-stop allowance is then 0.025 + 0.01 = 0.035 (about 0.0306 at the discrete cutoff) and is
declared as such; where reference uncertainty prevents that decision, report unresolved. No "material move from 0.216" threshold is used, because a move to 0.50
could be large, convincing and still useless against a required 0.90, and because 0.216 comes from historical
rows whose comparator must be recomputed on the same new datasets and the same external target as the
replacement. Anything not stopped is **"not ruled out at this look"** and never a §10 acceptance or a row 8
pass; it does not authorise the remaining failing settings, which follow the committed prospective rule and a
fresh budget. At 100 datasets the Monte-Carlo SE on coverage is 0.030 at 0.90 and 0.0412 at 0.216, and the
power to stop is 0.808 at true coverage 0.80, 0.328 at 0.85 and 0.999 at 0.70: adequate for a gross-failure
decision, weak near the boundary, and the 100- and 200-dataset looks stay failure-only as row 8 already
declares.

## 11. H3 — causal use *[frozen]*

**Layer selection (independent of CONF).** The §8 pipeline is run on CAL with 4 concept-disjoint
stratified folds (4 concepts each); the three band layers with the largest CAL $\bar\Delta$ are the
intervention layers; the largest is the **reference layer**. Not cross-fitting — a CAL choice. The ranking uses the selection predictor's CAL band-mean $\bar\Delta$ over band layers 23–57.
**State.** Per CONF trial: the posterior high-state probability of the training-selected mixture
member (§8.1) at the reference layer, fitted on the other folds; high if > 0.9, low if < 0.1;
$k \in \{2,3,4\}$ only; up to 200 high and 200 low trials matched on level, carrier and family (all
eligible trials if fewer; number reported). For hierarchical members the random effect is at its posterior mode, and the M3V floor is 0.05 SD of the training fold. Matching forms pairs within (level, carrier, family) cells, sampled with a seed.
**Single-pass interventions** (`/api/capture`, edits at the marker positions, joint at the three
layers in one pass; separate single-layer effects reported as secondary): baseline (empty edit list);
(i) **swap_delta** target → foil, λ=1 — the primary operation; (ii) **ablate** the target direction
(`ablate_token_ids=[target]`, λ=1); (iii) **rescue**: steer with $v_t$ at a per-layer amplitude
$\lambda_l$ frozen on CAL so that $\|\lambda_l v_t\|$ equals the median $\|\Delta h_l\|$ of the swap
operation on CAL high-state trials — applied to **both** low- and high-state trials (saturation is the
prediction on high); (iv) **sham**: λ=0 (must equal baseline bit for bit); (v) **off-target**: swap_delta
between a pre-assigned unrelated pair $(u_1 \to u_2)$ of BACKGROUND single-token concepts from
families other than the target's and foil's, scaled per layer to $\|\Delta h_l\|$ of the trial's own
target swap (per-layer norm matching); if $\|\Delta'\| < 10^{-3}\|h\|$ the control is undefined and
reported; (vi) **positive control**: `patch` the marker-position residuals from the trial's matched
$k=8$ packet (same draw) at the three layers and all three marker positions.
**Norm matching across the three marker positions** (amended 15 Sept 2026; Codex endpoint review finding 6):
- **Off-target (v).** At each of the three layers and each marker position, the requested norm is the written $\|\Delta h\|$ of the trial's own **joint** target swap at that layer and position, from its recorded edit log. It is never taken from a single-layer run, and the off-target delta is computed on its own evolving stream.
- **Undefined positions.** A position is undefined if its raw $\|\Delta'\| < 10^{-3}\|h\|$ and is left exactly unedited. If any position of a trial is undefined, that trial's off-target control is undefined as a whole: it is reported and excluded from the equivalence test, with the counts reported by state.
- **Rescue (iii).** $A_l$ is the median, over CAL high-state trials at $k \in \{2,3,4\}$ and their three marker positions, of the joint swap's written $\|\Delta h_l\|$. The rescue requests $A_l$ at every position.
- **Tolerance.** Requested, raw and written norms are logged. A control with $|\text{written}/\text{requested} - 1| > 0.01$ at any position is flagged and reported. It stays in the primary equivalence test, and a sensitivity analysis without flagged controls is reported. There is no iterative search for a written norm.
- **Off-target pairs.** They are pre-assigned per (target family, foil family) from BACKGROUND concepts of two other families, seeded (`stimuli/h3_offtarget.json`).
**Outcomes.** Primary: the reduction of the target–foil logit contrast at the final position,
effect $= (\ell_t - \ell_f)_{\text{before}} - (\ell_t - \ell_f)_{\text{after}}$ (positive = reduction) for
swap and ablate; for rescue the increase (sign reversed). Secondary: flips of the closed-set correctness of §6.3 (denominator =
trials correct at baseline for swap/ablate; all trials for rescue).
**Decision rule.** The primary contrast is the intervention × state interaction for the joint
swap: $\bar E_{\text{high}} - \bar E_{\text{low}}$ with its concept-cluster 95 % CI. H3 supported if the
CI excludes 0 and the point estimate ≥ 0.5 nat (SEOI); "strong" if the CI lower bound ≥ 0.5 nat.
Controls: sham and off-target effects must satisfy |effect| < 0.25 nat with the 90 % CI inside
(equivalence); the positive control must increase the contrast on low-state trials with a CI
excluding 0 — if it does not, the apparatus is insensitive and H3 is reported as **not testable**.
Ablate and rescue interactions are secondary, with CIs, no correction. The effect is also regressed
on $\|\Delta h\|$, baseline margin, level, carrier and family (dose regression), and the binary-state
account is compared with a smooth account (effect linear in the z-scored R1 score) by held-out log
score; "two-state causal mechanism" is not written if the smooth account predicts as well or better.
**Reading.** H1 supported and H3 unsupported is "causal use not established by this intervention".
Secondary downstream task: 100 pre-assigned yes/no property items (`stimuli/properties.json`;
"Does it fly?"), scored by the log-odds of the correct answer token after the packet and question;
the same intervention × state contrast, reported with CI. Prompt: the trial's active packet through the marker, then "\nQuestion: <question>\nAnswer:" tokenized separately under the §4 join assertion, in one pass with the trial's edits. Score: logit(" Yes") − logit(" No"), sign-flipped when the correct answer is no. Each question has opposite unambiguous answers for the target and its foil and contains no bank or family word; the items are audited by the two readers.

## 12. Conditions *[frozen]*

**Active (report).** ids = `<instruction A> <carrier open> <8 slots> <carrier close> <terminal
marker>` + `Answer:`; instruction A = "Read the description below; afterwards, name in one word what
is described." One pass: residuals at the marker's last token (unaffected by the suffix under the
causal mask), logits at the final position.
**No-target-report (challenge).** Instruction B, wording adjusted at build time until it tokenizes to
**exactly the same number of tokens** as instruction A (asserted in the manifest, so every packet and
marker position is the same global index in both conditions); same packet, same marker, no suffix;
residuals at the marker's last token. Called "no-target-report", never "passive". Secondary (§9). Instruction B is "Read the description below; there is no need to name what is described.": 15 tokens like A, with identical ids from the carrier line on, the first of four declared candidates to match (15 Sept 2026).

## 13. Exploratory (not confirmatory; deferred unless time allows)
Token-axis history dependence (dose ramped within one context) with the controls listed in the
10 Sept consensus; no bistability claim from lag alone.

## 14. Budget and timeline
Captures (single pass each, $D=4$): primary 2 × 10,752 + controls 2 × 2,304 + CAL/PILOT 2 × 5,376 =
36,864, at 3–5 s → 31–51 h. Storage per capture: 64 × 5120 native bfloat16 residuals at one position (0.66 MB)
+ logsumexp, requested-token logits and top-1000 (≈ 10 kB) → ≈ 25 GB, gitignored. H3: 400 trials ×
(baseline + 6 joint + 3 × 3 single-layer) = 6,400 captures ≈ 7 h. Fitting: 8 members × 63 layers ×
5 outer folds × (4 inner + 1 refit) × 8 starts = 100,800 starts per condition, plus CAL/PILOT, the
§7.5 recovery and §10 calibration runs; benchmarked on CAL before v2 — if the band cannot be fitted
within 24 h per condition on this machine, the frozen layer grid becomes stride 2 within each band
and inner selection uses 4 starts (recorded in v2). **Benchmark, synthetic CONF size, one core
(v1.2, `bench.py`, 2026-09-11, the process pinned to one XLA thread with `NPROC=1`, the §7.4
two-scale trapezoid quadrature at $P = 96$ with the eight-fraction backtracking search):** the
nine refits at 8 starts take 74.7 s at $D = 4$ (M3H 55.2 s, M2H 11.4 s, M2S 6.7 s, the rest under
1 s; ≈ 1.7× at $D = 8$), every start converging; one layer of the full §8 procedure (5 outer folds ×
8 members × (4 inner fits + refit)) takes 900 s with 4 inner-selection starts (the earlier
single-window rule gave 860 s with 8 and 556 s with 4; selections and $\Delta$ identical to five
figures across all three), so the 63-layer band is ≈ 16 h per condition on one core, ≈ 1.5 h on
the machine's 11 usable workers, well inside the 24 h — every layer stays. **Inner selection uses 4 starts** (v1.2, the
clause above invoked for the simulation budget rather than the CONF fit: the §10 simulations
re-run the whole procedure tens of thousands of times, and 4 starts cut a third of the cost); the
refits keep 8, and CONF is fitted with the same setting so that the simulated procedure is the
procedure. The machine (Apple M4 Max, 12
performance + 4 efficiency cores, 128 GB) takes 11 single-threaded workers before they slow each
other; one x86 cloud core (`ml.c7i`, SageMaker) is 0.36 of a Mac core on this code, and a fully
loaded hyperthread a tenth. Timeline (revised 15 Sept 2026): the capture patch and the
stimulus bank are being built (work item R084). The development capture rate is about 0.9 s per 64-layer capture on the M4 Max under CPU load (RSC 772e532), so CAL and PILOT with the single-clue captures (~11,900) take about 3 h, CONF with controls at $D = 4$ about 6.5 h and H3 about 1.6 h. v2 waits for the §10 replacement-interval validation and the remaining §7.5/§10 stages (planning estimate mid-December 2026); CONF captures, fits and H3 follow v2.

## 15. Freeze manifest for v2 and amendment log
Frozen at v2 (all committed, hashes in the v2 commit): `stimuli/` (concepts, clues, background,
pairs, competitors, properties, draws, manifest with token counts and scan results); the level set;
`capture.py` (ids, suffix assertion, parity tests, run log); `decode_cal.py` outputs (per-layer
decoders, $C_l$, standardization, scaling); `models.py` (the members, parameterisations, start
generator, optimizer settings, GH node count); `folds.json`; `analyze.py` (joint scoring, selection,
bootstrap, band summaries, outcome table, target bridge); `simulate.py` with its §7.5 and §10 outputs
and the resulting $D$, bootstrap type and layer grid; `h3.py` (CAL layer scores, matching, edit
lists, amplitudes, outcomes); this document.

| date | change | reason |
|---|---|---|
| 2026-09-11 | v0 drafted | for second-opinion review |
| 2026-09-11 | v1: inference unit = concepts; frozen CAL decoder; distractor channel; nine-model family; held-out family log score; outcomes split; power by simulation; H3 via one capture path; no-target-report condition | review round 1 (Codex) |
| 2026-09-11 | v1.2 (second entry, after the Codex review of v1.2 — verdict "not on board", `reviews/2026-09-11_v1.2_codex_brief.md`): the first cloud run stopped after 1 h and discarded; §7.4 quadrature rebuilt as the two-scale trapezoid rule with the independent audit at generating, fitted and cross-fitted parameters (`audit_quadrature.py`), the Laplace SD stated as capped; §9 inner-selection failure policy; §10 gain truth term under the generating density, twelve-calibration gate with independent check and D passed, "0.003" named a reference scale, coverage estimand stated, the single-layer run's scope stated and the band validation made its own post-PILOT stage, five-layer pilot with every graded member, correlation per physical layer, recovery reuse of the calibration rows; versioned code snapshots and result namespaces with the code/config hash in every row; per-concept scores saved | Codex review of v1.2 (session Entropy) |
| 2026-09-11 | v1.2: `models.py`, `analyze.py`, `simulate.py`, `verify.py`, `bench.py` written and verified (inherited likelihoods equal the numpy originals to 1e-9, gradients to 1e-8, self-refits recover every generator); §7.4: L-BFGS-B on analytic gradients replaces Nelder–Mead, the start generator and its jitter defined, the random-effect integral becomes a per-concept trapezoid rule on an adaptive window (prior-centred Gauss–Hermite does not converge at $n_c = 168$, mode-centred Gauss–Hermite fails on the truncated posteriors at $\tau = 2$) with the point ladder 48 → 96 → 192; §7.3 M3V floor as $\text{floor} + e^{s}$; §8.2 foil pairs resampled as units only in the paired statistics; §7.5 and §10 generator base declared, the gain definition made operational; §14 benchmark recorded — every layer kept, inner selection at 4 starts, refits at 8; the simulations moved to sharded SageMaker spot jobs (§10) | first code pass (session Entropy) |
| 2026-09-11 | v1.1: BACKGROUND concept bank with family-balanced backgrounds identical across target/foil pairs, slot-nested levels, role disjointness, prompt scan; H1 = coherence readout with a pre-declared target bridge (§8.5); one joint concept-scoring definition with training-only within-family selection (equal-weight and M3-vs-M2B as sensitivity); ordered mixture parameterisation, identifiable M3L catch, inherited affine sigma kept, skew-normal parameters named; SciPy option names and solver rule; recovery of the family distinction replaces member-recoverability; post-CONF member loss = primary unavailable; bootstrap defined and validated by refit simulation; calibration vs power failures separated with permitted changes; single-pass active capture with edits inside the answer pass; swap_delta linear dose, per-layer norm matching, rescue amplitude, patch mode; H3 decision rule, polarity, positive-control criterion, smooth-vs-binary check; layer count 64 / lens 0–62 / band 23–57 kept; equal-length instructions; budget recomputed | review round 2 (Codex) |
| 2026-09-12 | v1.2 (third entry, after the d4v12b calibration-stage read and the Codex re-check of the fixes): §10 records FPR 0 under all twelve nulls, coverage below 0.90 for six settings and the §8.2 refitting-bootstrap replacement invoked; the refitting bootstrap corrected (copies of a concept in one fold at both levels, the analysis's outer folds, failed or partially scored resamples never averaged, every replicate required, the interval method a declared Config choice carried through the runner with an unusable interval = assay failure) and benchmarked on the Mac; the gain-gate failure at M3L 0.01 nat diagnosed as optimiser basin loss within the M2K reference (the best-found solution reached by one start of the batch; the gain discontinuous in the scale at a fixed seed) and the calibration amended on its own side — 32 cold reference starts, distinct basins carried as warm starts, an extra batch without the repeated moment start and skew-mirrored, reproduction of the best-found reference by distinct cold starts required in both draws, the collapsed bracket re-evaluated before the jump is read, the declared fallback re-measurement, the calibration-side gain gated, every start archived; the gain artefact computed once and power jobs failing closed without it; the validation plan (R = 400 × B = 200 with Monte-Carlo intervals, every setting) and the pre-v2 pipeline numerical audit recorded; `models.py` and the pipeline unchanged; the corrected code reproduces the d4v12b null fits bit for bit (cross-snapshot reuse manifest to follow, with separate source and analysis hashes) | run d4v12b's calibration read and gain-gate failure; Codex review of the read and of the fixes (session Entropy SI) |
| 2026-09-15 | Draft amendments from the instrument build (work item R084, handoff f16ef039), decided by Entropy SI: §6.3 R3 correctness becomes closed-set (the target's frozen id has the highest logit among the 128 bank ids; chance 1/128; open-vocabulary argmax and rank secondary; variant logits requested), with §5's dose rule and §11's secondary flips on that rate; §4 and §14 say native bfloat16; §3 records the target-id convention, eligibility rules E1/E2 and the 12 collision exclusions, the clause checker and writing guideline, C1/C2 packet construction, carriers file, packet-token and capture-limit definitions, CONF draws built to D = 8, and that a scan failure or overlength stops the build for a pair-level amendment; §4 records the packet layout, marker and suffix; §5 the 1,152 single-clue captures; §12 instruction B's wording; §14 the measured capture rate and the revised timeline | Development probes on concepts from no bank family (RSC d9d626c; open-vocabulary argmax a formatting token in 20/20 full-dose packets); the model's dtype; build decisions the text left open (Entropy SI, 15 Sept 2026) |
| 2026-09-15 | Second set of draft amendments from the instrument build (R084 handoff 2e373d3d), decided by Entropy SI: §11 norm matching across the three marker positions (off-target matched per layer and position to the trial's own joint swap's written norm; one undefined position makes the trial's control undefined, counts by state; rescue A_l over CAL high-state trials at k 2-4 and three positions; written/requested tolerance 0.01 flagged, with a sensitivity analysis, and no iterative search), H3 state, matching, positive-control positions and off-target pair assignment, and the property-item prompt and score; §3 clue decisiveness rule (at most 2 of 12 clauses, recorded, a trial covariate); §6.3 stored observables | Codex review of the capture endpoint (RSC ddaadbf, finding 6); build decisions the text left open (Entropy SI, 15 Sept 2026) |
| 2026-09-18 | Draft amendment, §3 and §11 audits: every clause and property item read twice and independently, by one of four human readers on a seeded, family-stratified quarter (`audit_app/assign.py`, seed 20260918) and by an AI reader from a different developer than the drafting model (Codex) on the whole bank; an item passes only if both pass it, and the author decides the rest with both readers' marks recorded | owner, 18 Sept 2026: two readers of all 1,636 items is about three hours each; a quarter each keeps a human read of every item at about 40 minutes per person |
| 2026-09-18 | Draft amendment, second entry: the human readers are anonymous and open; answers stored per browser session; an item passes only with at least one human read and no reader's objection; no names recorded | the owner forwarded the part links for onward sharing ("no personal names needed"), so one link is not one person; the first page version kept one set of answers per link, and the 13 answers saved under it (part A) were kept under a legacy session |
| 2026-09-24 | Draft amendment, §3 and §11 audits: the AI reader becomes the primary full-bank read and the human read becomes a seeded sample audit of it (`audit_app/sample.py`, seed 20260924, 32 concepts = 384 clauses + 40 property items = 424 items, two human readers each), with the pass condition fixed before the draw: a human objection triggers adjudication by the author, and the exact one-sided 95% upper bound on the AI reader's ADJUDICATED miss rate must be at or below 0.02 (at most 3 of 424) or the full two-reader human read is reinstated, with every adjudication and the raw objection rate published; a human read counts only when given on the item itself, and the card-level "the other … are fine" control is removed for the sample | owner, 24 Sept 2026: the questions, the answers and the code are published with the study and anyone can re-run or audit them, so the audit's job is to be documented, bounded and reproducible rather than exhaustive; two readers over all 1,636 items is about three hours each and had stalled, and of the 818 items marked done by 24 September 534 came from the card-level control at a pace (median 0.5-1.6 s per clause against the 9.1-10.6 s/item of the read sessions) that is not a read |
| 2026-09-24 | Draft amendment, second entry: the human reader pass is REMOVED. The bank is read by AI readers from developers other than the drafter, each reader's recall is measured on a mechanically generated planted-defect set (`audit_app/plant.py`) embedded blind, decisiveness is measured by a naming test instead of judged, the author adjudicates flags and reader disagreements, and the recall bar is deferred to the §12 contamination run with an interim measured recall of 0.90 | owner, 24 Sept 2026 ("remove the human element - it will be bad results regardless"): the human read was a low-prevalence detection task, where published miss rates average about 0.30 and our own instrument measured 534 of 818 items cleared at 0.5-1.6 s per clause; a skimmed pass is indistinguishable from an attentive one in the record, so a jointly missed defect reads as agreement and the audit looks cleanest where it failed, and an unmeasured reader sensitivity gives no bound at all rather than a weak one |
| 2026-09-24 | Draft amendment, ledger row 4: the per-member fitter start policy declared (M3H cold+32 at jitter 0.50, M2H cold+64 at 0.25, M3V cold+32 at 0.25, M3/M3L/M2K/M2B cold+64 at 0.25 and 16 at 0.50, **M2S open** pending its paired cold-only-against-64-narrow comparison), with seeds, deterministic tie breaking, the unchanged recovery chain and a full-precision start archive; `PAD_MULTIPLE` 512 → 64; and §10.1, the pinned reference plan and the exact coverage futility rule (83 or fewer of 100, required to fail at the most favourable target in a justified set) | Codex's row 19 second opinion made this the precondition for the refit qualification slice; the padding change is numerically inert (identical log-likelihood, gradients to 1e-13) and saves 4.5 % at D = 4 but breaks `code_hash`, so it can only land in a prospective amendment; and the reference plan exists because the ω = 2 file that looked like the target holds 128 rows rather than 1,000, while ω = 2's coverage swings 4/20 to 18/20 across its own reference range |
| 2026-09-24 | Draft amendment, §3.1: the stimulus bank is rebuilt on published feature norms. Concepts and clause facts from Buchanan et al. 2019 (held outside the repo, cited per clause, never redistributed); family membership by dominant WordNet noun sense over eight declared roots; feature identity lemmatised; eligibility at ≥ 12 features because that is the clause count restated; decisiveness set by cue-validity rank with the two rarest permitted and $K$ deferred to the reported distribution. The families become animals, body parts, buildings, clothing, foods, materials, occupations and vehicles — 127 concepts, buildings at 15 with its shortfall taken from BACKGROUND | owner, 24 Sept: these clauses are the base of the whole study and the easiest part to discredit, and a curated source takes the sting out of a review. Tools, instruments and countries could not be built from any norm set: after E2 and E1 the whole-subtree ceiling is 11 for tools and 11 for instruments, so E1 binds rather than the source, and E1 is a decode rule that was not relaxed to keep a family name. The shortfall goes to BACKGROUND alone because CAL, PILOT and CONF are fixed by the pairing and an odd count cannot be paired |
| 2026-09-24 | Draft amendment, §3.1 revised: the absolute floor $K$ on cue validity is WITHDRAWN. Sharing count ranks candidates for selection so the twelve clauses span a range of evidence strength; decisiveness is settled by the naming test already declared. Selection, rendering and acceptance become one seeded loop over an order rather than a set of sixteen, with re-selection once and pass-over recorded; a family may run 13–16 with the shortfall in BACKGROUND | R084 measured the bank ceiling at $K = 2$, bound by materials at exactly sixteen concepts, where a clause need only be shared by two of 4,411 cues — no floor at all — and no per-family count this source supports reaches cue validity 0.05 across eight families. More fundamentally the statistic was wrong for the question: a sharing count records how many cues elicited a feature in a production study, not how many things it is true of, so it overstates decisiveness, and $K = 2$ is that mismatch made visible. The naming test measures the property directly |
| 2026-09-24 | Draft amendment, §3.1: acceptance becomes TWO-SIDED — at most two of twelve clauses named alone, AND the concept named from the eight clauses of three seeded draws; derivational variants merged before selection (Snowball stem or WordNet derivational link) and proper and brand names removed; and the source recorded as under question, with McRae and CSLB named as candidate primary sources to be measured | R084's materials trial: a one-sided ceiling rewards vagueness, and the only accepted concept passed with 0 of 12 named because a reader given its clauses answered globe, ball, beans and coin — so a $k = 8$ packet would not identify it either, and decisiveness had returned to the renderer. Lemmatising leaves derivations unmerged, so twelve features can be four ideas restated (36 pairs in sixteen concepts) and *glue*'s rarest two were *elmer* and *elmers*. And Buchanan's feature column holds content words cut from free-text prose rather than feature statements, so the relation — which is what a clause asserts — is authored, and the citation would be decorative |
| 2026-09-24 | Draft amendment, §3 and §3.1: the source becomes McRae (CSLB pooled) and the bank becomes **three families** — animals, foods, vehicles. CONF stays 64 so §10 is unchanged; stratification drops from eight levels to three; per-family role counts become unequal and seeded in proportion to each family's eligible pool; the background list becomes a declared 3–3–2 balance rotating by seed, since one clause per family no longer fills eight slots; merging becomes subsumption over the feature's word set | McRae carries the relation and ships the authors' own cue validity (`CV_No_Tax`), so the clause is rendered from a cited statement rather than authored from a cited topic word. But McRae and CSLB are concrete-object norms: neither norms people, and only animals, foods and vehicles can be filled. McRae alone gives 58 eligible across those three against the 96 CONF, CAL and PILOT need, so CSLB is load-bearing and its data is gated; vehicles is the binding family |
| 2026-09-26 | Draft amendment, §3.1: the recorded fragility re-measured for the adopted three-family design (R084, RSC 2646bf1). McRae alone 33/15/17 = 65 against 99 (CONF 64 + CAL 16 + PILOT 16 + one BACKGROUND per family), not 58 against 96 — the earlier figures were the eight-family scenario's, where E2 also excluded concepts touching the five families since dropped; pooled upper bound 57/42/29 = 128; CSLB must supply at least 34 of its 63 three-family candidates at ≥ 12 features. Added: on McRae alone, proportional allocation puts animals over the half-share pairing limit in every split. Vehicles stays the binding family. |
| 2026-10-02 | Draft amendment, §3.1: Feats (Borovsky, Peters, Cox & McRae 2023) adopted as a second source under a declared pooling rule (R084, RSC 3cd3786); the recorded fragility restated on USABLE features — single token 51 of 99 at twelve (25/15/11), 77 at ten; only ten clauses with two-token names reaches 114; rule T's wording corrected (taxonomic rows are not all family words) and its narrowing left open at a measured cost of 16/8; the raw figures 65, 85 and 128 withdrawn; CSLB and Hovhannisyan unmeasured under these rules. Decision point 15 October 2026. |
| 2026-10-02 | Draft amendment, §3.1, later: the no-CSLB route measured under the full rules (R084, RSC 6153fee) — McRae + Feats + Hovhannisyan (≥ 3 productions) with clothing as a fourth family reaches 104 usable single-token concepts at ten clauses against a four-family minimum of 100 (margin four, before naming acceptance, 14 concepts from Hovhannisyan); 113 without rule T; 90 at ≥ 5; twelve clauses fail under every row. Hovhannisyan's three gaps (no denominator, no CV, photo-conditioned) and its unrecorded data terms stated. Decision point 15 October 2026. |
| 2026-10-02 | Draft amendment, §3.1, last: the naming-acceptance rate measured on a 30-concept development sample of the four-family route (R084, RSC af8a668) — 12 of 30 pass as declared (0.40, 0.23–0.59), so 104 becomes about 42 and no relaxation of the two sides reaches 100 at the point estimate; the floor measures the reader's naming ability, and the reader's required capability is recorded as an open protocol choice; Hovhannisyan's photo-conditioned and generic clauses noted. The route is withdrawn as a bank; the 15 October decision now includes the reader and the channel. |
| 2026-10-02 | Draft amendment, §10.1, corrected on Codex's row-19 Lengau review (RSC c3e1d2a): ω = 2's Monte-Carlo SE is 2.678379 (2 MCSE 5.356758), not "2 MCSE 2.678379"; the ten final_2026-09-15 shards are ω = 2's bank and pin nothing at ω = 1, whose historical reference (−0.869513, MCSE 0.011242, old policy) is sensitivity evidence until a policy-matched reference is generated under its own ledger row; the screen is 100 fixed attempted datasets with the 83 cutoff applied only at n = 100; T is a declared 99 % reference confidence set and the one-look allowance 0.035 is stated. |
| 2026-10-02 | §7.4 start policy IMPLEMENTED at RSC 5f6333c (not adopted): START_POLICY, fit(policy_key), PAD_MULTIPLE 64, the policy in the identity and the code hash, the reference archive at full precision; the v1.2 path unchanged without a key; mechanics tests in test_start_policy.py. The code hash under the policy (D = 4, layer 41, seed 2026, refit, four inner cold starts) is edcfdf4300f3; the legacy cluster configuration now hashes af666f75d0b0 because models.py changed, so no new row can be pooled with the 625798e9e7f4 rows. |

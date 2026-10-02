# R052 stimulus-bank sources: Codex second opinion

**Date:** 2 October 2026 UTC / 1 October 2026 America/Phoenix.  
**Reviewer:** GPT: R052 Entropy paper, native session `01a0d19e-2127-7051-9a61-6db771088559`.  
**Brief:** Unimog `prompts/2026-10-02_codex_r052_bank_sources_second_opinion.txt`, commit `cdf7b860be9b4629fb60e247a863e761303445ed`; accepted handoff `ef99ee06-290a-5e3c-b3af-b43958488fa1`.  
**Scope:** A second opinion before source adoption or amendment. This record does not adopt a bank, amend the protocol or authorize a run.

**Verdict: ON BOARD with Feats as an additional published human-production source; NOT ON BOARD with Option C as a complete working bank.** Ten clauses is a defensible prospective design choice, but the measured 100 concepts are raw-feature candidates. Applying only two existing usable-feature rules leaves **at most 94**, short of the 99 required roles. The corresponding twelve-feature ceiling is **80**, rather than 85 usable concepts. Further exclusions and naming acceptance can only lower these ceilings.

| Requested question | Answer |
|---|---|
| 1. Feats beside McRae | **ON BOARD**, with source-specific provenance, overlap and missing-CV rules made explicit. |
| 2. C: ten clauses as the working design | **NOT ON BOARD as proposed.** The amendment is conceptually defensible; the claimed complete bank is disproved under unchanged usable-feature rules. |
| 3. Measurement and pairing | **ON BOARD with the raw counts and taxonomy/token checks; NOT ON BOARD with calling them usable eligibility or treating one proportional CONF share as the complete allocation check.** |
| 4. B + dated CSLB alternative | **ON BOARD with Feats eligibility work now and a 15 October 2026 CSLB decision point**, alongside already gated, bank-independent Lengau work. CSLB is a candidate addition, not a promised upgrade. |
| 5. Rejected sources | **ON BOARD with excluding both from this relational production-norm bank.** Correct the ConceptNet release licence version and avoid assigning the S&V article licence to its separate data. |

## Basis and verification

Read the current [protocol §§3–3.1](../PREREGISTRATION_T1_model.md), [R084 source record](../stimuli/norms_bank/SOURCES_MCRAE_CSLB.md), [committed driver](2026-10-02_feats_pool_driver.py) at RSC `f11bbb0`, `family_pool.py`, `pool_e1.py`, `mcrae_parse.py` and `check_clues.py`. Also read the R052 dated source/compute entries, Unimog `project_knowledge/rsc_t1_simulation_design.md` §11c and the paper's sampling-unit argument in `papers/adaptive_agency_special_issue/sections/transfer.tex`.

Independent read-only checks reconstructed source feature sets, WordNet 3.0 membership/E2, dominant-synset collapsing after E1, E1 with the frozen local tokenizer, minimal usable-feature attrition and integer split witnesses. Primary articles, released source files and OSF/licence records were checked. No original driver was run in place; no source/stimulus files were changed. No naming test, capture, fit, simulation, cloud/HPC dispatch or push was performed. Deterministic scratch arithmetic under `/tmp` is a review check, not an additional scientific result.

## 1. Source: accept Feats, with a defined population and provenance

Feats meets the stated human-production-norm rule. It contains explicit relational features, for example `used_for_passengers`, `requires_pilots` and `found_in_airports`, with McRae-style coding. **LLaMA is the Language Learning and Meaning Acquisition lab**, not model augmentation. The production respondents were adults: 555 recruited through MTurk, 521 retained, native English speakers with US IP addresses. Newly normed concepts had 33–126 respondents. The early-vocabulary focus determines which concepts were sampled; it does not mean that children supplied these feature statements. Toddler-accessibility ratings were a separate adult task. The elicitation used 14 response blanks and retained features produced by at least 16.66% of respondents, corresponding to McRae's 5/30 criterion. Normalized production frequency is `30 × Prod_Freq / Num_Parts`. These methods and the authors' compatibility analyses support combining sources, without establishing exact equivalence or independent elicitation for every released entry. [Borovsky et al., methods and validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11630474/)

Puppy, candy and cookie are legitimate concepts for a language-model assay. Inference must describe the selected, source-defined concrete-concept population and its family/source weights; it does not automatically extend to all English concepts. Normalizing production counts corrects their scale, not their sampling uncertainty. Newly elicited Feats concepts have more respondents than McRae's 30, so a generic small-sample objection would be misplaced.

The driver's exact-label rule is acceptable as a declared conservative priority: keep McRae's entire feature set on overlap and add only exact-new Feats concepts. Its bookkeeping needs correction: the released files contain **372 labels, 136 exact McRae overlaps and 236 exact-new labels**, not 239 new. Of the 136 overlaps, **103 feature sets are identical and 33 differ**. The article's **31 experimentally re-normed stimuli** is not the total release overlap, and feature-set differences alone do not identify independent re-norming. The UK release contains 13 concept labels, whereas the article describes 12 additions. Counts must follow pinned files. The `isalpha` guard drops 28 exact-new labels, leaving 208; retaining it is defensible for an alphabetic single-word construction rule. E1 remains a separate tokenizer test. Do not strip parenthetical sense labels to enlarge the pool without a declared sense/collision rule and renewed E2 checks.

The per-clause record should identify the actual source/version, concept, feature, relation, production count, respondent denominator and cited CV. Cite Borovsky, Peters, Cox and McRae, DOI [10.3758/s13428-023-02242-x](https://doi.org/10.3758/s13428-023-02242-x), online 2023 and in *Behavior Research Methods* 56 (2024), 3259–3279. Retained McRae entries keep their McRae citation. The Feats [OSF project](https://api.osf.io/v2/nodes/7d8et/) specifies CC BY 4.0; McRae's observed noncommercial/citation terms remain separately recorded. Feats' licence does not replace those source terms.

**Published CV values are not source-invariant rankings.** Directly, `airplane / has_wings` has production frequency 20 in both releases. McRae reports a non-taxonomic frequency denominator of 529, sharing count 44 and CV .038; Feats reports denominator 141.526, sharing count 13 and CV .141. The latter denominator is reproduced by summing that feature's normalized frequencies across Feats' 359 MBCDI concepts. The reference universe changes the statistic. Either retain source-specific CV as a labelled selection heuristic, or prospectively define a deduplicated pooled universe and recompute a clearly named derived quantity. Do not call recomputed CV the authors' cited CV or mix published sharing counts as though their universes were identical.

There is also an immediate exception: `tea` comes from `remainingUKCDI_concsFeats.csv`, which has **no `CV_No_Tax` column**; its 16 non-taxonomic features lack author-supplied CV. The per-clause citation/range-selection rule needs an explicit missing-CV policy. Silent zero imputation or treating a missing value as low evidence is unacceptable.

## 2. Ten clauses: defensible amendment, insufficient bank

The current protocol requires twelve **usable, distinct** features, one per clause. Changing that to ten is a prospective amendment throughout §§3–3.1, not changing only a parser threshold. It must cover the eligibility/selection count, reselection policy, clause manifest/checker, clue-order permutation, acceptance tests and CAL single-clue captures (currently `16 × 12 × 6 = 1,152`, becoming `16 × 10 × 6 = 960`). Preserve feature merging, forbidden terms, source citations and the independent reader requirement.

The other requested consequences are:

- **Decisiveness:** explicitly choose the ceiling. Keeping the absolute maximum of two means ≤2/10 rather than ≤2/12, increasing the permitted proportion from 16.7% to 20%. A one-clause ceiling is stricter and can cause further attrition; it is not a neutral restatement. Two can be defended as a declared absolute cap, with decisive-clause inclusion retained as a covariate.
- **Feature ranking:** choose ten across a predeclared evidence range under the source/CV policy above. Published sharing counts and CV do not certify decisiveness. Retain the single-clause naming test; do not restore the withdrawn CV floor to force acceptance.
- **Eight-clause floor:** three separately seeded draws, all three naming the target, remain possible. Predeclare whether compositions may repeat or are sampled without replacement, and keep the same policy at both clause counts. The single-clause test still presents all ten clauses independently to a reader other than the model under test.
- **Variability:** `C(12,8)=495` compositions becomes `C(10,8)=45`, eleven-fold fewer. Slot order and carriers still vary, but do not create independent concept observations. With exactly two marked decisive clauses, an eight-clause draw includes at least one with probability `10/11` under twelve and `44/45` under ten. Thus the same three-draw floor is easier to satisfy through decisive-clause inclusion. Report this; an eight-clause draw excluding both marked decisive clauses is a useful prospective diagnostic if distributed evidence is the intended claim.
- **Dose grid:** `{0,1,2,3,4,6,8}` and nested eight-slot packets can remain unchanged: both banks contain at least eight clues. The endpoint uses 80% of ten rather than two-thirds of twelve. Keep the declared PILOT rule for any later grid movement.

Concepts remain the statistical sampling unit. Forty-five compositions are not forty-five independent observations, nor does more within-concept repetition restore the lost composition diversity. Keeping CONF64 preserves the concept-count dimension of the simulations; it does **not** establish unchanged power, variance or interval calibration for a different source mix and clue design. PILOT and the existing assay-validation gates still matter.

I would accept ten as a prospectively specified design **only after an actual usable pool can fill the roles and survive acceptance**. The present evidence does not meet even the feature-count prerequisite. Do source/provenance and clean-eligibility work now; retain twelve as the current rule while assessing CSLB. Do not manufacture relational facts, relax merging or reduce CONF silently to make C fit. A later CSLB-backed move from ten to twelve is another frozen-bank design decision, made before relevant captures, not an automatic post-output upgrade.

## 3. Counts and allocation: raw results reproduce; usability does not

The implementation of dominant WordNet membership, scenario-specific E2, E1 and collapsing synonyms **after** E1 is correct. The relevant results are `scenarios.adopted_three.<family>.sense1.after_E1`, not any-sense or the eight-family scenario. The tokenizer JSON digest independently matched `87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4`.

The decisive mismatch is `family_pool.py` F3: it tests `len(norms.features[c])` **before** usable-feature exclusions and merging. These raw counts reproduce:

| McRae + exact-new Feats; dominant sense, E2 and E1 | Animals | Foods | Vehicles | Total |
|---|---:|---:|---:|---:|
| Raw ≥12 features | 37 | 31 | 17 | 85 |
| Raw ≥10 features | 41 | 37 | 22 | 100 |
| ≥10 after exact word-set subsumption alone | 41 | 37 | 20 | **98** |
| ≥10 after literal adopted-family words alone | 41 | 33 | 22 | **96** |
| ≥10 after both minimal rules | 41 | 33 | 20 | **94** |
| ≥12 after both minimal rules | 35 | 30 | 15 | **80** |

The last four rows are **upper bounds**, not accepted-bank counts. The check considers every E1-passing cue before synset collapse, including alternative labels such as motorbike/motorcycle. It removes literal animal/food/vehicle family words, uses underscore-separated feature word sets, merges subsets into their more specific feature and coalesces equal sets. It omits stem/derivation merging, proper names, other bank-concept names, rendering and naming acceptance. It does not rely on a blanket interpretation that every taxonomic tag must be excluded.

Two existing subsumption examples already remove more than raw100's single spare: **cart** has 11 raw features but nine after `has_wheels` merges into the more specific wheel statements and `used_by_pulling` into `used_by_pulling_by_horses`; **skateboard** has ten but nine after merging `has_wheels` into `has_4_wheels`. Literal `food` exclusions additionally reduce **rice**, **sandwich**, **spaghetti** and **toast** to nine; spaghetti loses both `a_food` and `an_Italian_food`. These are source facts, not speculative naming-test attrition. At most94 cannot fill96 target roles plus three background reserves.

Checking only animals' real-valued CONF proportion is insufficient. For each **integer** split, require all three families represented, each ≤half, disjoint role totals and at least one background concept per family jointly. At raw100 an exact proportional-rounding witness exists:

| Role | Animals | Foods | Vehicles | Total |
|---|---:|---:|---:|---:|
| CONF | 26 | 24 | 14 | 64 |
| CAL | 7 | 6 | 3 | 16 |
| PILOT | 7 | 6 | 3 | 16 |
| BACKGROUND | 1 | 1 | 2 | 4 |

Cross-family pair counts `(animals–foods, animals–vehicles, foods–vehicles)` are `(18,8,6)` for CONF and `(5,2,1)` for each smaller split. A third-family competitor exists in every split. This proves raw100's allocation feasibility, **not** usable-bank feasibility. After just one rejected animal or food concept, independent largest-remainder rounding can exhaust a family's background reserve even though a joint constrained allocation exists; specify reserve-aware integer allocation prospectively.

At raw85, proportional CONF/CAL/PILOT counts can each satisfy their own half bound, but the roles cannot coexist: reserving three backgrounds leaves at most82 concepts for96 target roles, a deficit14. That deficit is aggregate; it is not fourteen necessarily missing members of the category named vehicles. At the minimal-filter twelve-feature ceiling80 the deficit is at least19.

Before the driver becomes a build input, fix its provenance and metadata representation. Its composite digest hashes only the two Feats CSVs, omitting McRae, and `path` names only the first CSV. Its global feature-only relation map assigns McRae's `encyclopaedic` label to Feats `has_cheese` entries labelled `visual-form_and_surface` (hamburger/pizza, also sandwich/spaghetti at ten). Store relation metadata by retained source/concept/feature. There are also 145 metadata keys from discarded overlap-only features; they do not alter these counts, but should not enter a selected bank. No backfill of retained McRae feature metadata from Feats was found in these inputs.

## 4. Dated alternative and compute work

Use **15 October 2026** as the CSLB response/chase and bank-plan decision point, measured from the owner's confirmed 1 October 23:20:50 UTC resend. Mail handling stays with R078; this review sends no mail. Work now on Feats provenance, cleaned feature eligibility, missing-CV treatment and joint allocation rules. On receipt, measure CSLB's actual relational features under the same exclusions, E1/E2 and overlap policy. Its twelve listed additional category-vehicle candidates are pre-filter candidates, not guaranteed usable additions, and cannot alone settle the aggregate gap.

If access or sufficient usable concepts are absent on 15 October, report the failed bank feasibility and seek an explicit population/design change backed by counts. Do not slide the deadline, assume a reply, or claim C has solved the dependency.

The measured row18 benchmark supports Lengau planning, with provisional whole-programme/refit extrapolations distinguished from actual runs. Bank-independent work can follow the existing order: pinned-environment parity against known rows, misspecification checks and bounded reference-bank work, with a ledger row and existing gates before each launch. Qualify the intended refit concurrency/runtime/memory and checkpoint/restart recovery before relying on a full refit chain. Reconcile §11c's older Stage4 ratio/checkpoint condition with its newly measured planning estimate before dispatch. Free allocation changes the cost, not the validation requirement. This review launches none of those stages and approves no paid run; the previous row19 second-opinion gate remains as recorded.

## 5. Exclusions: agree on methodology; correct licence claims

**Antal/de Almeida S&V 2026:** these are genuine adult human production norms, not model output. However, the instructions require one word or a hyphenated combination; multiword responses are excluded and compounds reduced. The released workbook has feature words, production frequencies, occurrence/distinctiveness/CV and sensorimotor classifications, without an explicit predicate/relation field. Behavioral or functional meaning can survive in a word, but selecting a particular relation would add author interpretation. Exclusion under this protocol's explicit relational-statement rule is therefore justified. The workbook inspected has nine sheets and lacks the `Features-Raw` sheet mentioned in the paper; do not assume raw recovery is available. The article is CC BY 4.0, while its OSF project reports no selected node licence, so the separate workbook's terms remain unverified. [Primary methods](https://link.springer.com/article/10.3758/s13428-026-03069-y), [workbook](https://osf.io/cdx7w/), [OSF project metadata](https://api.osf.io/v2/nodes/c6brw/)

**ConceptNet/OMCS:** excluding it from this bank is sound. Human-contributed relational assertions are not equivalent to controlled concept-wise feature-production norms with known respondent denominators; graph weights are not their production frequencies. ConceptNet mixes crowd contributions, games and imported resources. Its complete data release is **CC BY-SA 4.0**, with code under Apache 2.0; the brief's blanket 3.0 statement should be corrected, while a pinned subset's per-entry terms would need checking. Incorporating covered adapted database material into a uniformly CC BY-only release cannot silently erase share-alike terms. Those terms alone do not prove that every independently written stimulus would be a covered adaptation. The production-norm mismatch already supports exclusion without that stronger legal claim. [Original authors' description](https://ojs.aaai.org/index.php/AAAI/article/view/11164), [release licence](https://github.com/commonsense/conceptnet5/blob/master/LICENSE.txt), [data provenance](https://github.com/commonsense/conceptnet5/blob/master/DATA-CREDITS.md)

## Pinned review inputs

These files remain external; no database is copied into the repository. Local Feats digests match [OSF file metadata](https://api.osf.io/v2/nodes/7d8et/files/osfstorage/).

| Input | SHA-256 |
|---|---|
| McRae `CONCS_FEATS_concstats_brm.txt` | `fe796831232b164635c258095749320665c18c40186778e8d8baf4b0c4cdba23` |
| Feats `MBCDI_concs_2022-07-14.csv` | `202311ec37050b4b7ccaff646cafcdac4acf134b75f5905bdfbdb8334b21eb09` |
| Feats `MBCDI_concsFeats_2022-07-14.csv` | `4b45b8910c5f42f7a6450aa33732a81bcbbcc0631d8c41df7b73d8c9d83d29ba` |
| Feats `MCSM_LLAMA_feats_2022-07-14.csv` | `f941ef90437407eb7de34085d27d69ebea8f9049508a335e752ac3894496935e` |
| Feats `remainingUKCDI_concsFeats.csv` | `91aaef66e7e4cbfa975238c79f7ed7dcb0903b9dc4cdae37ae864f84a3302d34` |
| Driver `2026-10-02_feats_pool_driver.py` | `cc04afb4277353d2d887f2249fa87ecf27544b953c5c97cd11817938d39cce48` |

The pooling audit reads the McRae TSV and the two Feats concept-feature CSVs; the other Feats files were checked as release evidence. Required next action belongs to Claude/R084: correct raw-versus-usable bookkeeping and source metadata, measure actual cleaned eligibility, then present a revised prospective bank plan. All five requested questions are answered here; this second-opinion assignment is complete.

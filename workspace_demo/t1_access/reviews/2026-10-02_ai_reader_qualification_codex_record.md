# R052: AI image-reader qualification — design review before answers

**Date:** 2 October 2026 UTC / 1 October 2026 America/Phoenix.

**Reviewer:** GPT: R052 Entropy paper, native `01a0d19e-2127-7051-9a61-6db771088559`, topic `95bf527b-9f8e-598f-ae95-96a5d2b035af`.

**Brief:** Unimog `prompts/2026-10-02_codex_r052_ai_reader_qualification_review.txt`, commit `3f303d7d03ec58c9ec98ea922025c87bf517492a`, SHA-256 `661007172e509ee0e6e50f3bcbe191aab578a58da2374f57619d3e6b7ca14217`. Ownership was committed at Unimog `7d422df3`; handoff `dfcf8ec5-57c4-575a-979d-cd322d8b45e6` was then acknowledged and reports accepted, before review edits.

**Verdict: NOT ON BOARD with making the 600 naming calls under the current design at RSC `7efeb55`.** The owner's route is workable: use an AI reader, existing human evidence and people only for disagreements. I accept that decision; this review does not restore a new human panel. Repair the task/scoring contract, qualification gate, response completeness and isolation, then submit the exact committed design and separate execution brief. This record is not reader qualification, a favorable execution review, or permission to begin an audit or target-model forward.

**Conflict and exposure:** I am a GPT-family reviewer and the proposed reader is a GPT-family vision reader. Reviewing its design cannot establish its competence or supply independent performance evidence. The parent parsed the label-bearing set for deterministic metadata checks without displaying target labels; one static helper inspected its accepted-answer metadata. This session also has prior development-pool concept exposure. No image was opened or named, and no reader response was produced. Later naming must not inherit this review conversation or answer-key access.

The proposed system samples 300 photographs outside today's qualified pool, obtains a free name for each original and its transformed grayscale counterpart, scores those answers against a frozen label dictionary, and admits an AI reader to audit the development pictures. The human recognition proportions are an external difficulty reference. They are neither individual human verdicts nor a directly matched free-naming performance measure.

Read the brief, the complete [builder/scorer](../stimuli/photo/ai_reader_qual.py), the 300-item [set metadata](../stimuli/photo/ai_reader_qual_set.json), the qualified-pool metadata, source recognition metadata/documentation, and current Unimog `rsc_t1_two_channel_framework.md` §§8.2–8.3. Static helpers checked counts, scoring, primary sources and the audit contract. No images, private human/reader outputs, audit page/results, plant/key, model load/forward, fit, simulation, cloud/HPC/account operation or push was used. Deterministic metadata and binomial arithmetic are the only computations.

## 1. Human choice versus free naming; what Q1 and Q2 can mean

The relevant photograph recognition experiment is **Experiment 3 of Mukherjee et al., Drawings of THINGS (2026)**. Humans selected a best label from a searchable menu of 1,854 labels, with disambiguating parenthetical text. It included original THINGS and THINGSplus photographs; the combined retained sample had 5–23 ratings per photograph, mean 14.70. That experiment is distinct from the original THINGS photographs' free-naming measure. [Primary paper](https://doi.org/10.3758/s13428-025-02887-w).

Free naming adds lexical retrieval, permits abstention and removes menu cues. Expanding acceptable synonyms makes another change in the opposite direction. These effects do not cancel by comparing two percentages. Q1's current human close mean, **0.504642058**, is a difficulty-referenced numerical benchmark, not proof that the reader agrees with humans or names objects at least as well as an average human. Matching an overall mean can also conceal errors on different pictures.

Keep the existing human norms for sampling, difficulty strata and item-level diagnostics. My preferred revision makes Q1 **descriptive**, removes the human-equivalence claim, and defines admission on the actual free-naming scale using a frozen, sense-specific answer dictionary. Matching the human menu task would permit a more direct recognition comparison, but would still not qualify free naming; it is not a reason to add unapproved calls.

An easy-item free-naming floor of **0.90** is a reasonable proposed engineering requirement, not a value derived from human equivalence or a universal standard. State whether it means a fraction on a fixed panel or evidence about a wider population. For the latter, a prospective one-sided 95% lower-bound requirement of at least 0.90 is more defensible than merely observing 90%. Answer 2 gives its actual cost in errors. Use whole-answer, admissible naming accuracy for this gate; the implemented Q2 instead uses the broad **close** score. No threshold proposed here is adopted by this review.

## 2. Set, exclusions, strata and precision

The frozen metadata has 300 unique item IDs and concepts, 100 in each declared stratum, with cuts **0.333333333** and **0.642857143**. The 121 currently qualified pool concepts are excluded, with zero overlap. The source's single-meaning filter is satisfied. These exclusions do not prove exclusion from every future instrument population: reserve qualification concepts and their photographs/source groups from later development and formal populations before use.

There are **61 easy images**, all in the highest stratum: 57 above 0.8 and four exactly 0.8. There are not 100 easy images. Actual per-item rating counts range **9–22**, total **4,406 ratings**, with only 125 items having 15–17; these are not 4,406 independent people. Reproduced image-weighted human means are **0.494969607 exact** and **0.504642058 close**.

| Easy successes | Observed fraction | Exact one-sided 95% lower bound |
|---:|---:|---:|
| 55/61 | 0.901639 | 0.815070 |
| 58/61 | 0.950820 | 0.877769 |
| 59/61 | 0.967213 | 0.900365 |
| 60/61 | 0.983607 | 0.924578 |
| 61/61 | 1.000000 | 0.952076 |

The current point rule passes at **55/61**; its two-sided 95% interval is about **[0.798104, 0.963040]**. A one-sided 95% lower bound reaching 0.90 requires **59/61**, allowing at most two errors; using the lower end of a two-sided 95% interval requires **60/61**. N=61 can therefore support the proposed stronger rule if performance is nearly perfect. It does not give tight precision around an observed 90%, or promise useful power for a reader whose true performance is exactly the boundary. Calculations invert the binomial distribution; see [NIST's interval construction](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

These intervals require a declared binomial/random-sampling interpretation. A fixed heterogeneous panel's score is an exact panel fraction; it does not automatically certify performance on arbitrary later photographs. The two views give **300 paired images, not 600 independent images**. Use item-paired analyses for transformed-view differences. Equal allocation across cut-defined strata, including ties, is a benchmark distribution; a claim about the eligible source population needs actual stratum sizes and appropriate weights. Report stratum denominators as well as fractions.

For reference only, Q1's present fixed point comparison passes at **152/300**. Comparing a one-sided 95% binomial lower bound to that fixed mean would require **167/300**, but would repair neither the task mismatch nor uncertainty in the human reference. Human proportions use finite ratings and potentially repeated raters; do not treat the published mean as uncertainty-free gold or pool its ratings as independent trials.

Resolve two source-metadata anomalies **before answers**, rather than silently repair them from the AI output:

| Opaque item | Source record | Issue to resolve |
|---|---|---|
| q047 | N-correct=7, N-ratings=15, exact=close=0.294117647 | 7/15 is 0.466666667, inconsistent with the documented ratio. |
| q140 | N-correct=5, N-ratings=13, exact=0.384615385, close=0 | Close is below exact despite the documented additional-acceptance interpretation. |

The frozen JSON copies those source values; this is a source-definition/provenance question, not a builder arithmetic fix. Obtain the derivation or make a prospective documented exclusion/replacement without consulting responses. Then freeze counts, easy membership, strata and means again. Do not expand or redraw after seeing performance to rescue qualification.

## 3. Answer forms, normalization and scoring

**37 items have only multiword accepted forms, including six easy items.** A compliant one-word answer cannot match them exactly. Prefer changing the reader instruction to one **short object noun or noun phrase**, or explicitly restrict the eligible frame to concepts with valid one-word names and recompute it. Keep this reader task separate from the target model's canonical single-token naming convention. No concept labels or menu should accompany the prompt.

The suffix function is crude stemming, not reliable singularization. Lexical examples unrelated to the benchmark, and not answers to any image: `knives` becomes `knive` and does not match `knife`; `leaves` becomes `leave` rather than `leaf`; `species` becomes `specy`. When both key and response undergo the same faulty transform, errors may be hidden and malformed forms may receive credit. Freeze explicit validated inflections/spelling variants, case/whitespace/punctuation handling and a sense-specific alias map. Do not let an unvalidated list of WordNet strings or removal of parenthetical sense text define correctness automatically.

The [primary release description](https://osf.io/download/n5wrv/) distinguishes exact recognition, homonym allowance and close recognition that additionally accepts the correct label within a chosen menu label. The code's free-text substring test against **every alias**, plus reverse containment inside a multiword alias, is broader. A synthetic alias `dax zot` can credit `dax`, dropping a potentially defining modifier; a longer unrelated word containing an alias can also pass. This does not reproduce the bounded human-menu close score.

Require equality of the whole normalized answer to a frozen admissible alias for the primary score. Keep broad/lenient matches descriptive if retained. Freeze synonym sense, permitted specificity, noun-phrase length and treatment of spelling variants, `unclear`, empty, malformed, multiple-name and explanatory responses. Abstention cannot silently leave the denominator. Unlisted answers remain errors under the qualification rule; owner adjudication must not add aliases retrospectively to obtain a pass. The code and wording must agree on whether Q2 uses exact admissible naming or close. Provide a mechanically reproducible item list and reason codes: the current scorer promises a disagreement list but emits none.

## 4. Grayscale admission

**Q3 must affect admission.** A reader can currently qualify on color while failing every grayscale picture, yet all audit verdicts concern grayscale. Qualify the actual `a=1` clean canvas under the actual reader delivery settings. This comparison includes fitting/padding, luma conversion, contrast normalization, clipping and quantization; it is not just removal of color.

My preferred primary rule is the frozen easy-item whole-answer accuracy requirement on **grayscale**, with its declared lower-bound or fixed-panel interpretation, together with full-panel and per-stratum results. Keep color as the external human-reference diagnostic and report the paired degradation and discordant counts. If both views or a maximum degradation are admission criteria, specify that prospectively. A five-point degradation margin, for example, needs a stated engineering justification; it is not supplied by the source data. A small paired loss alone is insufficient when both views perform poorly.

Human color norms do not establish human accuracy on these transformed canvases. A grayscale miss on a human-easy color picture can flag an audit issue, but cannot identify whether the cause is the reader or lost stimulus information. Passing this naming benchmark also does not establish the other three audit competencies: photograph authenticity, intended-sense verification and distinctness of second photographs. Bound those claims, provide separately justified checks/evidence, and retain uncertain cases for owner disagreement adjudication. Qualification on homonym-free concepts does not alone validate ambiguous senses or every four-family development/second-view condition.

## 5. Disagreements and owner decisions

A human recognition **proportion** is not a binary human verdict. Freeze a consensus threshold if routing uses one, and specify whether it uses exact or close recognition. Reader failure on a human-easy original is a useful flag; reader success on a low-recognition original is not inherently disagreement. For the actual audit, route `unclear`, an incorrect/ambiguous free name, negative or uncertain photograph/sense judgments, uncertain/non-distinct second views, and input/provenance problems according to explicit rules. No matching human norms have been supplied for the current independently cleared second-view candidates; assess their actual questions, not invented human agreement.

For each referral preserve opaque item/view, intended concept/sense in the evaluator record, human proportion and rating count where applicable, image/prompt/model/scoring hashes, unedited raw answer and question order, frozen score, referral reason, owner's dated evidence and decision, and final retain/exclude/replace/hold disposition. Report AI-passed and owner-adjudicated cases separately. Owner decisions cannot erase qualification errors or override a required free-naming/all-pass rule; unresolved cases hold or follow the frozen seeded replacement procedure.

The automatic **owner-only fallback** contradicts the adopted people-only-for-disagreements route. Qualification failure holds the audit. A revised procedure or different AI reader requires a prospective qualification assignment; an owner-only audit needs a separate explicit decision. Neither “a handful” of referrals nor 15 minutes for 64 pictures is evidenced; report the observed workload rather than promise it.

## 6. Reviewer, reader and exposure

Different developers for GPT and Qwen help separate the audit from target-model selection, but do not establish independent errors, independent training exposure or absence of memorization of public data. This is a limited engineering qualification with disclosed provenance, not proof of blind human-equivalent judgment.

This review must not become the naming context. The key contains intended labels, aliases, human scores and common labels. Exposure restricts the candidate universe even without viewing pictures. Use fresh stateless, image-only reader requests with opaque IDs and the frozen prompt; withhold the key, pool names, this review, file paths, source captions/metadata, human scores and all prior answers. Disable access to evaluator files/tools. Keep the key and mechanical scorer with a separate evaluator/orchestrator. A new context removes this transcript's cues; it cannot prove that the model's training never included the dataset. Disclose both facts.

“One image per request” does not establish independence if requests share a conversation. Color and grayscale counterparts must have separate fresh contexts with neither paired image nor answer available; freeze/randomize ordering before calls. Lock raw naming responses before scoring and before revealing intended names/senses for the later audit questions. The reader must not inspect the key, grade its own answers or revise them after feedback. Qualification concepts must remain outside the instrument populations, with actual exclusions enforced at later draws. Preserve the earlier text-bank `f2d1328` target-visible, concept-batched limitation and prior exposure disclosure; this review does not relabel that work as blind calibration.

## 7. Required changes before any of the 600 calls

1. **Commit the corrected design.** Adopt the noun/noun-phrase contract or a prospectively revised eligible frame; freeze exact sense-specific aliases and normalization; resolve source-norm anomalies; remove human-equivalence wording; declare estimand, full/easy denominators, interval convention, grayscale admission and scope of the four audit judgments. Preserve the owner AI-reader rule and remove automatic owner-only fallback.
2. **Reject incomplete or ambiguous answer files.** Require exactly one retained response for each of the **600 declared item/view pairs** before a qualification verdict. The current dictionary silently overwrites duplicates, ignores unknown IDs/views and scores only supplied items. A single correctly answered easy color image can make both Q1 and Q2 pass, with no grayscale response. Reject duplicates/unknowns and freeze failed-request, invalid-answer, abstention and missingness handling; no selective denominator reduction or favorable retries. Empty strata must not emit undefined/NaN summary JSON.
3. **Freeze and enforce execution identity.** Record model/release, actual delivery mode and settings, prompts, image byte hashes, source metadata/release hashes, builder/dose/runtime versions, set/key/scorer hashes, sampling frame/seed/exclusions and order. Verify actual delivered bytes and completeness. Metadata hash syntax and no duplicate hashes were checked here; actual image bytes, source authenticity and transport parity were not.
4. **Resolve source-policy scope.** The qualification builder has no per-image source/licence record. Framework §8.2 already found the collective THINGSplus grant insufficient for some development inputs. R052 must commit whether its admission rule applies to qualification-image transmissions and implement that scope before calls; the rule cannot be bypassed merely by putting pictures outside the development pool. This is an existing project-policy question, not a new legal certification by this reviewer.
5. **Supply the separate bounded reader job.** Specify 600 planned responses, maximum total attempts including provider failures/retries, token/quota and clock/output limits, subsequent audit allowance, durable counters, raw-response storage and idempotent recovery. Commit raw outputs before scoring. Interrupted/uncertain attempts cannot be silently repeated or discarded; semantic errors remain errors. The present file builds/scores and supplies no enforced executor. The owner's quota choice does not authorize unlimited replacement panels, model shopping or additional settings.
6. **Re-review that exact package before execution.** R084 retains builder/set/executor ownership; R052 retains framework, audit protocol, source policy and dispatch. Favorable design review would still require the separate concrete reader job. No new human panel, image naming or extra inference has been performed in this assignment.

Verified design SHA-256: `ai_reader_qual.py` **`c36699c8491aaf520eff732ca21d799a6f6bb3588863e2a87c87318bb5adbcea`**; set **`4c72f662ffe9c568b787c07cdeea8870caf150783caf93016b10f654c46dd363`**; prompt **`8a964ba5553bd4b6731053a4fb36b553626cba034577e9430f1004029c677652`**. All seven brief questions are answered. The next substantive action is a committed revised design and its bounded job brief from the source lanes, followed by a concrete review assignment.

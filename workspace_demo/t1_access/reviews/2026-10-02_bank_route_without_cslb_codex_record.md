# R052: a measured bank route without CSLB

**Date:** 2 October 2026 UTC / 1 October 2026 America/Phoenix.

**Reviewer:** GPT: R052 Entropy paper, native session `01a0d19e-2127-7051-9a61-6db771088559`.

**Brief:** Unimog `prompts/2026-10-02_codex_r052_make_option_c_work.txt`, committed at `bee5df83996fba900c627aa4d14574ae43e86cdf`; handoff `b3a1e7d9-7f67-5259-ba0d-8e7a4551a26b` accepted after ownership commit `ee0471fa`.
**Scope:** Constructive second opinion and deterministic source/count checks. This record adopts no source, bank, amendment or run. Feats adoption, the current twelve-clause rule and the owner's 15 October CSLB decision point carry forward.

**Verdict: conditionally ON BOARD with qualifying a ten-clause, four-family, single-token route; NOT ON BOARD with declaring 99 usable concepts already obtained.** McRae + exact-new Feats + exact-new Hovhannisyan, adding **clothing**, yields **107 filtered candidates: 43 animals, 28 foods, 21 vehicles, 15 clothing** at the proposed Hovhannisyan cutoff of **three human productions per feature**. Four families require **100**, rather than 99, concepts at minimum: 64 CONF + 16 CAL + 16 PILOT + four background reserves. There is a joint allocation and seven candidates above that minimum, provided distinct background clauses may reuse a background concept identity, as the current one-per-family minimum permits. Requiring eight distinct background concepts instead makes the minimum104 and leaves three spare candidates. Rendering, full semantic exclusions and independent naming acceptance have not been performed.

The cutoff is consequential: at **five or eight productions**, the same tighter four-family screen yields **92**, not a complete bank. Hovhannisyan's concept-specific respondent denominators are not supplied, so three productions cannot be called the current common **one-sixth prevalence** criterion. This route is an explicit source-threshold and population amendment, not a denominator normalization. If the owner requires the existing prevalence criterion throughout, this route is unavailable without the missing denominators. The measured alternative using existing sources alone is **ten clauses and names of up to two tokens**, with 115 more tightly filtered candidates; that preserves more source policy but requires substantial R2/R3/H3 redesign. Adding clothing and furniture to existing sources alone reaches only97 against the five-family requirement101, so that cheaper measured variant does not rescue the bank.

## Reading and measurement basis

The system being preserved is the [protocol](../PREREGISTRATION_T1_model.md): concepts are the sampling units; twelve distinct source-grounded clauses currently feed nested eight-slot packets; three families supply disjoint reciprocal target–foil pairs in CONF64/CAL16/PILOT16; a third-family competitor is preassigned. E1 gives each answer one token, allowing the final-position logit contrast, the linear R2 token readout and H3 token-direction interventions. The usable-feature rules and the single-clause ceiling/eight-clause naming floor precede bank freeze. [§§3–6, 8, 10–11](../PREREGISTRATION_T1_model.md)

Read the relevant current protocol sections, [R084 source record](../stimuli/norms_bank/SOURCES_MCRAE_CSLB.md), the committed [Feats driver](2026-10-02_feats_pool_driver.py) at `f11bbb0`, `family_pool.py`, `pool_e1.py`, and the [preceding source review](2026-10-02_bank_sources_codex_record.md) at `99277aa`. Checked primary publications, author/publisher downloads and licence metadata. Three read-only helpers divided source evidence, additional norms and counts; no helper changed a repository file or contacted Claude.

Counts use pinned external norms, WordNet 3.0, the frozen offline tokenizer, the alphabetic single-orthographic-word guard, dominant noun sense and scenario-specific E2. All surviving cues are tested before dominant-synset collapse; aliases never count as separate concepts. Scratch scripts perform parsing/counting only. No naming-model call, bank audit, capture, fit, simulation, cloud/HPC operation or push occurred. Forbidden plant/reader/human-output material was not opened. These are candidate-count checks, not additional scientific outcomes.

## 1. Additional sources: what is actually available

### Hovhannisyan et al. (2021): a real relational source, with a denominator gap

This is human feature production for **995 photographed objects**, from 566 native American-English MTurk respondents. Concepts received at least 20 respondents, mean 30.5; the released matrix does not give each concept's denominator or a maximum. Respondents supplied five mandatory features using relation prompts such as *is*, *has* and *does*. Released columns retain predicates. Processing also split phrases and removed features appearing for fewer than two concepts; the paper's analysis uses frequency ≥3. Thus the source qualifies as relational human data, but its feature universe and photo-conditioned elicitation differ from McRae's. Generic concept facts must be distinguished from incidental properties of the photographed exemplar. [Primary article](https://link.springer.com/article/10.3758/s13421-020-01130-5), [open author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC8081674/)

Obtained author files from [ObjectMemory](https://github.com/ElectricDinoLab/ObjectMemory), pinned tree `9cac6649dfd9ad5dca97dca2c265df4cf7c58c9f`, with [OSF](https://osf.io/fxgzj/) as the article's data landing page; stored in `~/word-norms-hovhannisyan/`. Approximate original category totals are 145 animals, 110 food/fruit/vegetable, 60 vehicles and 77 clothing, before our taxonomy and eligibility. These are source categories, not WordNet bank counts. Exact-label comparison gives **327 overlaps** with McRae+Feats, **668 new labels**, of which **404 pass `isalpha`**. Eligibility then reduces these substantially.

The article is CC BY 4.0. The inspected GitHub tree has no LICENSE file and the OSF project/component report no selected node licence. Public access is established; separate data-reuse terms require recording or clarification rather than silently inheriting the article licence. This is an observed metadata gap, not a finding that use is prohibited. [Author files](https://github.com/ElectricDinoLab/ObjectMemory), [OSF metadata](https://api.osf.io/v2/nodes/fxgzj/)

At **absolute** production frequency ≥3, the three-family ten-feature screen after literal family exclusions, taxonomic exclusions/proxy and subsumption is **43/32/21 = 96**, thirteen additional dominant concepts compared with the corresponding McRae+Feats screen of 83. At ≥5 the increment in that single-token screen is **zero**. The tighter four-family route is measured below. None of these counts is an accepted naming-tested increment. Without per-concept denominators, even ≥5 cannot guarantee ≥1/6 prevalence.

### Vinson & Vigliocco (2008): production norms, but no recoverable predicate

The actual release contains 456 items: **169 object nouns, 217 action verbs and 70 action nouns**; 1,029 features and two integer-frequency matrices. Twenty raters produced features per item; a global frequency cutoff of nine was applied. Object categories include 24 animals, 35 fruit/vegetables and 13 vehicles. Released features are bare words/compounds; visual, perceptual, functional and motoric flags do not specify a predicate or its argument direction. Therefore **zero established relational additions** under the current rule. It is inaccurate to dismiss the source as free association. Literal novelty includes one animal, five produce labels and one vehicle, but label novelty does not restore their missing relations. [Primary paper](https://link.springer.com/article/10.3758/BRM.40.1.183), [publisher ZIP](https://media.springernature.com/original/springer-static/esm/art%3A10.3758%2FBRM.40.1.183/MediaObjects/Vinson-BRM-2008a.zip)

Downloaded into `~/word-norms-vinson/`. ZIP terms expressly allow noncommercial research/education use with article and downloaded-material citations, retaining author rights; no CC licence is supplied. Do not turn a functional feature word into an invented `used_for_` statement.

### Cree & McRae (2003): the same norm lineage

The 541-concept collection uses 30 producers/concept and a five-producer threshold. Appendix B lists 538 classified labels: **537 exact McRae matches plus `armor`→`armour`**. Birch, cedar and pine are explicitly omitted from those category analyses. **Zero concept increment** over McRae 2005; this is not a third independent dataset. Relational examples are present, but no additional downloadable full bank or separate open-data licence was found. [Primary DOI](https://doi.org/10.1037/0096-3445.132.2.163), [author lab publications](https://sites.google.com/site/kenmcraelab/publications), [public full-paper preview](https://www.researchgate.net/publication/10691112_Analyzing_the_Factors_Underlying_the_Structure_and_Computation_of_the_Meaning_ofChipmunkCherryChiselCheeseandCello_and_Many_Other_Such_Concrete_Nouns)

### Garrard et al. (2001): published relational tables, little target-family novelty

The working institutional PDF's Appendix A contains **62 concept tables** with relational statements and dominance proportions. Family totals are 24 animals, six fruits, eight transport concepts and 24 tools/household objects. Twenty older adults participated; 19 completed all items and one fewer than half. Original retention requires at least two producers; our ≥1/6 dominance screen is an additional restriction. Separate machine-readable norms were not found. The tables do not supply row-level raw counts/denominators; do not reconstruct them from rounded proportions. [Institutional record](https://research.manchester.ac.uk/en/publications/prototypicality-distinctiveness-and-intercorrelation-analyses-of-/), [institutional PDF](https://pure.manchester.ac.uk/ws/files/29173229/POST-PEER-REVIEW-PUBLISHERS.PDF)

Fourteen literal labels differ from the baseline, but nine are clear aliases/sense-qualified matches, including `stool`/`stool_(furniture)`. Five genuine-new concepts remain. At printed dominance ≥1/6, excluding categorising rows, their raw statement ceilings are:

| Concept | Statements before full cleaning | Frozen token count | Current alphabetic/E1 result |
|---|---:|---:|---|
| kangaroo | 21 | 2 | Fails E1 |
| rhinoceros | 16 | 4 | Fails E1 |
| saw | 11 | 1 | Passes; outside three target families; cannot supply twelve |
| suitcase | 17 | 1 | Passes; outside three target families |
| watering_can | 16 | 2 | Fails alphabetic guard and E1 |

Thus the current three-family increment is **zero after E1**, rather than the two new animals before E1. Saw/suitcase may support alternative-family/background work after actual cleaning, but neither is a counted usable addition here. Copyright is Psychology Press 2001; no explicit separate data-reuse grant was found. The PDF is accessible, so “the data are unavailable” would be too strong. Saved in `~/word-norms-garrard/`.

### Other English candidates and recent norms

| Source checked | Data and access | Consequence for this bank |
|---|---|---|
| Bolognesi, Pilgram & van den Heerik (2017) | 185 English concrete/abstract concepts; author workbook with production counts out of 30 and nested feature types. [Paper](https://link.springer.com/article/10.3758/s13428-016-0838-6), [author repository](https://github.com/mariannabolognesi/Semantic-Feature-Norms). Downloaded to `~/word-norms-bolognesi/`; separate workbook licence not verified. | Features are chiefly words/compounds. Some coded part/material types might support an explicitly audited relation mapping; broad functional types cannot automatically restore verbs. Raw WordNet dominant-category counts are 13 animals, seven foods, seven vehicles, before E2. Exact-new labels include piglet, rhino, alcohol, icecream, yolk, bulldozer, tank; aliases and feature cleaning matter. **No usable relational increment established.** |
| Buchanan (2019), original responses | Published final word-pair norms lose relations, but author processing stages retain original participant utterances. [Paper](https://link.springer.com/article/10.3758/s13428-019-01243-z), [raw author repository](https://github.com/doomlab/Word-Norms-2), [OSF](https://osf.io/cjyzw/). Downloaded to `~/word-norms-buchanan/`, tree `ad7a771d00b5b1030c168958a28d74fc51d3e9e5`. Repository GPLv3; data-specific terms must be recorded separately. | A **recoding contingency**, not a ready relational bank: recover genuinely supplied predicates, independently code/deduplicate by respondent, exclude invalid utterances and determine denominators. Do not invent relations for isolated words. Increment **unmeasured**. This does not reverse rejection of the final word-pair release. |
| NOVA, Suresh et al. (2026) | Original human production for 786 concepts, followed by model-assisted clustering and matrix completion. [Primary paper](https://doi.org/10.1111/tops.70037), [author release](https://github.com/Knowledge-and-Concepts-Lab/llm-norms-cogsci2025). | Public matrix has 787 concepts/8,202 binary features and combines human/model completion without cell-level separation or production denominators. No human-only raw release located in that tree. **Exclude the combined matrix**; do not count an unavailable human-only branch. |
| Valério et al. (2023) | 80 manipulable objects; Portuguese elicitation with English translations. [Primary DOI](https://doi.org/10.1080/02643294.2023.2279185), [methods preprint](https://doi.org/10.1101/2023.04.24.537452). | Zero English-production additions under the current language rule. |
| Aalto (2024), Rachdi (2025), CanFeat (2025) | Finnish, French and Cantonese production respectively. [Aalto](https://link.springer.com/article/10.3758/s13428-023-02311-1), [Rachdi](https://link.springer.com/article/10.3758/s13428-025-02814-z), [CanFeat](https://www.nature.com/articles/s41597-025-06210-2). | Not additional English production norms. Translation would be another population/coding amendment. |

Checked McRae-lab successors/re-normings and 2024–2026 norm publications. The [2025 noun/verb analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC11908919/) reuses the 359 CDI nouns, rather than adding a new noun bank. Search phrasings included “semantic feature norms 2024 2026 animals”, “feature production norms relational English database”, “semantic feature norms 2025 English dataset production”, author-specific searches for Vinson/Garrard/Cree/Hovhannisyan, and “semantic property production English concrete dataset”. Found ratings, translations, stripped-word norms and model augmentation alongside the sources above. **No further turnkey qualifying English relational extension was located in these searches**; this is not a proof that none exists.

## 2. Mixing three or more sources

Section 3.1 needs a source table and a retained-row manifest, not merely three citations:

1. **Population and feature inclusion.** Record language, elicitation population, photo versus name cue, per-concept respondent denominator, production count/proportion, original pruning and our cutoff. McRae 5/30 and Feats ≥16.66% can map to the existing approximately one-sixth criterion. Garrard proportions can be screened directly, with unknown raw denominators marked missing. Hovhannisyan ≥3/5/8 are absolute counts, not that common criterion; a source-specific cutoff requires a prospective amendment. Prefer actual denominators if obtained. Never impute all concepts' N from the mean.
2. **Whole-set overlap priority.** Keep McRae on exact-label overlap, then Feats, then the new source. No filling gaps in a winning concept's features from a losing overlap set. Freeze spelling/case/sense-label normalization, report exact-new labels separately from new dominant synsets, and collapse synonyms after eligibility/E1 as currently declared. Among qualifying aliases, use a deterministic retained-cue/source rule. No alias earns a second concept role.
3. **Source/concept/feature metadata.** Each selected clause maps through original source/version and row/column IDs, original concept label, canonical cue/synset, original predicate and arguments, human count/denominator or dominance, exclusion/merge history, rendered clause, audit/naming outcomes and dates. A canonical label originating elsewhere is a label mapping, not permission to graft that label's other source's features. Every clause must be traceable to a fact elicited for that same concept/sense. Merged features keep all contributing row IDs; independent-producer counts are not added across duplicate formulations or sources.
4. **CV universe.** Keep author CV with its source universe and mark it missing where absent; no zero imputation. McRae and Feats already rank the same feature differently because their universes differ. Hovhannisyan's global pruning adds another difference. Either declare within-source ranks as the selection heuristic, with a predeclared missing-CV substitute, or recompute a separately named pooled statistic over a frozen deduplicated universe using compatible frequencies/denominators. The latter cannot be called the author's cited CV. Do not mix raw Hovhannisyan counts into normalized McRae/Feats CV denominators.
5. **Sampling and audit.** Report realized source×family counts and acceptance attrition by source. Freeze source priority, cutoff, family roots, tie rules, seeds and constrained integer role allocation before acceptance. Apply the same generic-truth, redundancy, forbidden-name, decisiveness and packet-identification checks to all sources. Photo-dependent or colloquial feature coding requires explicit adjudication; a threshold alone does not certify truth.

**A per-source quota among each concept's ten/twelve clauses is neither necessary nor desirable under whole-set priority:** every concept's features come from its retained source, so most such quotas are impossible. Labelled provenance plus the declared selection rule is enough for clause traceability. Source-balanced concept sampling may be warranted if source comparison is part of the estimand; a blind mandatory quota could worsen family balance and scarcity. Source effects are often confounded with concept novelty and family: a source covariate or sensitivity analysis cannot by itself disentangle them. Report the selected-bank population and avoid an all-English-concepts inference.

## 3. Count stages and design levers

“Filtered” below is a deterministic screen, **not** a usable-bank certification. The minimal screen removes literal adopted-family words and exact word-set subsumption/equality. The broader existing-source screen also removes source-labelled taxonomic rows and own-cue-name mentions; whole-word-set Porter2 normalization moved no reported counts. Hovhannisyan uses the transparent `a_/an_/is_a_/is_an_` frame proxy for taxonomic exclusions, with cue names caught by the subsequent candidate-name ban. These are declared sensitivity policies rather than a claim that the current rule spells out every taxonomic exclusion. The tighter screen additionally bans all preliminary eligible cue names and noun-plural forms, excludes uppercase-word proper-name proxies, and excludes `tea` with missing cited CV. Full derivational/semantic merging, lowercase proper terms, disjunction/contradiction/generic-fact checks, rendering/length and naming acceptance remain. Blanket merging every feature sharing `has` or `is` would be incorrect. Source-specific CV amendment remains needed for Hovhannisyan despite these counts.

| Three families, McRae + exact-new Feats | Animals | Foods | Vehicles | Total |
|---|---:|---:|---:|---:|
| Single token, twelve, minimal | 35 | 30 | 15 | **80** |
| Single token, ten, minimal | 41 | 33 | 20 | **94** |
| Single token, ten, broader taxonomic/own-name screen | 36 | 29 | 18 | **83** |
| Single token, ten, tighter | 36 | 25 | 18 | **79** |
| Up to two tokens, twelve, minimal | 61 | 40 | 17 | **118** |
| Up to two tokens, twelve, broader | 41 | 27 | 13 | **81** |
| Up to two tokens, ten, minimal | 75 | 45 | 22 | **142** |
| Up to two tokens, ten, broader | 63 | 41 | 20 | **124** |
| Up to two tokens, ten, tighter | 60 | 35 | 20 | **115** |

The brief's two-token raw133/twelve and raw152/ten are **cue-word counts**. After the declared dominant-synset collapse they are **69/42/19 = 130** and **76/49/24 = 149**. All two-token figures still retain the alphabetic single-word guard; they do not admit two-word phrases automatically.

### Ranked by cost to the argument

**1. Ten clauses: accept prospectively once a bank passes.** This raises the minimal single-token ceiling from 80 to94, a gain14, but does not supply99. Keep the eight-slot dose grid and CONF64. Amend every selection/manifest/reselection/capture count; CAL single-clue captures become960 instead of1,152. Keeping an absolute two-decisive-clause ceiling changes the proportion to20%. Eight-clause combinations fall from495 to45. Keep independent-reader single-clause and three-draw packet acceptance, with composition/repetition rules declared. This preserves the current readout and causal definitions; it does not prove unchanged power for the altered clue distribution. Details are in the [preceding review §2](2026-10-02_bank_sources_codex_record.md).

**2. A fourth family from qualifying norms: preferable to changing E1.** It changes the sampled population, family allocation, competitors and background balance, but preserves all token readouts. Clothing is the measured useful candidate. With four families, declare eight distinct background **clauses** as **2–2–2–2**, allowing two distinct features of the same background concept within a packet. This retains the one-concept-per-family minimum; it does not require eight distinct concept identities. Freeze that reuse policy and the paired-packet matching rule. If distinct background identities are required instead, reserve two per family and use the104 minimum. Recheck E2 against all four trees and rerun all bank-name exclusions. A replacement family changes the population but can also delete overlapping concepts; counts cannot be added to the existing totals without recomputing E2.

Plants illustrate this failure: `plant.n.02` as a fourth family makes many foods cross-family. At ten, the existing-source minimal single-token pool becomes **41/18/19/4 = 82**, and replacing vehicles yields **42/18/4 = 64**. At twelve, the fourth-family pool is68. Even the two-token broader ten-feature plant pool **63/25/19/3 = 110** has only **88 pairable target positions** after one reserve per family: remaining animals outnumber all others. Adding Hovhannisyan at frequency3 gives a minimal plant-fourth single-token total99, short of the new100 requirement, and broader84. Plants is not a numerical rescue under this taxonomy.

There is also a direct H3 benefit to four families. **§11 requires an off-target BACKGROUND pair from two families other than the target's and foil's. Three total families leave only one.** Four target/background families supply the two required other families. Resolve this availability mismatch explicitly when amending the manifest; do not silently reuse the third family's two concepts as two different families.

**3. External BACKGROUND: reasonable modest lever, with control-channel validation.** Moving background reserves outside the three target families buys **three target candidates**, reducing the target requirement from99 to96. The minimal ten-feature ceiling94 still fails. Existing-source single-token broader screens at twelve find ten clothing and four furniture candidates in a joint five-family background scenario, while the three target-family counts at ten remain63/41/20 under two-token E1. These are sufficient candidate pools to investigate, not accepted background items. Two external families also provide H3's required off-target pair for every target/foil combination. Packet backgrounds and H3 concepts must have frozen family definitions, disjoint identities/synonyms, audited clauses and, for H3, single-token names. Amend the rotating3–3–2 channel or its replacement, and validate incidental evidence/k=0 behavior on PILOT. Keep paired target/foil backgrounds identical.

**4. Smaller CAL/PILOT: possible amendment, poor primary rescue.** Each removed concept saves one role, normally in pairs. CONF64 is unchanged, so its concept-count dimension remains; the full power/interval claim is not automatically unchanged. CAL trains the regularized decoder/scaling, selects layers via four concept folds and fixes intervention amplitudes. PILOT validates dose placement, family performance and variance/band assumptions. Minimum fold arithmetic is not evidence that a tiny CAL/PILOT is adequate.

For illustration only, at the optimistic94 ceiling, CONF64/CAL16/PILOT10 + three backgrounds needs93, leaving one spare; CAL12/PILOT12 needs91, leaving three; CAL12/PILOT10 needs89, leaving five. These lower the required roles rather than finding99. All fail against the broader83 ceiling without further changes. At the current twelve-feature ceiling80, only13 combined CAL/PILOT positions remain after CONF and backgrounds, a severe cut. I would require independent instrument-validation evidence before accepting reductions, and would prefer the four-family route retaining16/16.

**5. Weaker pairing: mathematically possible, but changes the controls and uncertainty.** The ≤half rule is necessary and sufficient for complete **disjoint reciprocal cross-family pairing**; keep it for this design. If the requirement becomes merely “every concept has an outside-family foil”, a reused/nonreciprocal foil mapping can allow animals above half, provided an outside family exists and third-family competitors remain available. It creates shared-foil dependencies, changes C1 balance and pair-based resampling/interpretation, and needs explicit graph/reuse limits and revised uncertainty validation. It creates no new concepts:94 still cannot fill99. I would not spend this part of the design to solve an aggregate count deficit.

**6. Up to two tokens: largest existing-source pool, highest assay cost.** The tighter ten-feature pool115 can fill96 target roles plus three backgrounds, with16 candidates above99 and a cross-family pairing witness:

| Role | Animals | Foods | Vehicles | Total |
|---|---:|---:|---:|---:|
| CONF | 32 | 20 | 12 | 64 |
| CAL | 8 | 5 | 3 | 16 |
| PILOT | 8 | 5 | 3 | 16 |
| Remaining for backgrounds/reserves | 12 | 5 | 2 | 19 |

This uses48/30/18 target concepts; reserve one background per family. The residual nonanimal reserve beyond those minimums is five, so the headline16 spare is not an arbitrary attrition budget: family losses can bind pairing first. Twelve with two-token names is not a robust substitute: the broader pool81 has target capacity76 after reserves.

For a two-token canonical answer `(t1,t2)`, **the first-token logit does not score the whole concept**. Its probability is prefix mass, including continuations outside the bank. Full-sequence score is `log P(t1|x) + log P(t2|x,t1)`, with a declared boundary/termination and variant policy. Sharing `t1` can make a first-token contrast uninformative despite distinct complete names. Unique first tokens among selected answers do not turn their prefix probability into whole-concept probability. [Autoregressive scoring definition](https://huggingface.co/docs/transformers/perplexity)

R3 would need candidate-conditioned continuation scoring, length/variant/tie rules and a revalidated closed-set comparison. Length normalization changes the statistic from sequence probability. R2 currently uses the linear pre-answer contrast `(W_U[t]−W_U[f])·J_l h`; a second conditional token has no fixed unembedding row at that position, and adding two rows does not implement the sequence score. H3's ablate/swap/rescue directions and final target–foil logit outcome must likewise be redefined and validated. Arbitrary single-token codes redefine the answer-label task and do not avoid that validation. I would retain this as a contingency with an explicit assay redesign, not call it a harmless E1 relaxation.

Lowering to eight/nine clauses is also not an attractive rescue: the minimal single-token pools are102/101, but broader screens shrink them to98/92 before full acceptance. Exactly eight leaves one eight-clause composition; nine leaves nine. This trades away evidence-composition variation for little or no margin.

## 4. The smallest measured route worth qualifying

**Recommended order: ten clauses + Hovhannisyan under an explicit source-specific frequency policy + clothing as a fourth family, keeping E1, reciprocal pairs and CAL/PILOT16.** This is a qualification proposal, not an adopted Option C. The count comparison is:

| Single-token, ten features, tighter policy | Animals | Foods | Vehicles | Clothing | Total |
|---|---:|---:|---:|---:|---:|
| Hovhannisyan production ≥3, plus retained McRae/Feats | 43 | 28 | 21 | 15 | **107** |
| Hovhannisyan production ≥5 | 36 | 25 | 18 | 13 | **92** |
| Hovhannisyan production ≥8 | 36 | 25 | 18 | 13 | **92** |

A reserve-aware proportional-rounding witness at107 is:

| Role | Animals | Foods | Vehicles | Clothing | Total |
|---|---:|---:|---:|---:|---:|
| CONF | 26 | 17 | 12 | 9 | 64 |
| CAL | 7 | 4 | 3 | 2 | 16 |
| PILOT | 7 | 4 | 3 | 2 | 16 |
| Remaining BACKGROUND candidates | 3 | 3 | 3 | 2 | 11 |

Each target split represents all four families and has no family above half. The remaining11 contain four minimum reserves plus **seven of aggregate margin**; all remaining accepted concepts can enter BACKGROUND under the current allocation convention. A bounded deterministic flow check verified all120 distributions of exactly seven rejected concepts across the four families: each permits64/16/16, family presence, half bounds and one reserve per family. This verifies arithmetic margin for that reserve/reuse rule only, not naming survival or every fold constraint. With two reserves per family, this witness leaves three spare candidates; the seven-loss proof does not apply. Recompute the constrained allocation after acceptance attrition rather than preserving these numbers regardless of loss. Predeclare five outer/four inner CONF folds, decoder CV and CAL H3 folds: small CAL strata cannot appear in every held-out fold, so specify how stratification distributes them while retaining training-family coverage. A fourth family does not multiply the independent observations beyond64.

1. **Qualify the new source before adopting the route.** Pin the files/terms and document elicitation and missing denominators/CV. Seek concept denominators through the responsible source lane if preserving common prevalence is required. Otherwise prospectively declare Hovhannisyan's ≥3 human-production rule as a different criterion, with ≥5/8 sensitivity and the photo-genericity audit. Do not represent it as 5/30 equivalent. If that policy is unacceptable, stop this route here.
2. **Reproduce the candidate screen under the intended amendment.** Recompute all four WordNet/E2 families, alphabetic E1, exact-source priority and synset collapse. Store source/concept/feature metadata rather than a global feature-only map. Apply the complete forbidden-term, semantic/subsumption/derivation, genericity, contradiction and duplicate rules; explicitly list remaining exclusions. The measured107 is the benchmark for the stated screen, not a promise of the final count.
3. **Render and accept in the frozen seeded order.** Select ten features under the declared source/CV policy; preserve the absolute decisiveness ceiling, eight-clause three-draw floor, reselection limit, independent readers and length/prompt checks. Do not use the model under test. Publish source-specific attrition and every pass-over reason. No such acceptance work is authorized or performed by this review.
4. **Require a surviving joint bank, including reserve margin.** At minimum fill64/16/16 plus one BACKGROUND per four families under the declared identity-reuse policy; verify each reciprocal split, third-family competitor, two-other-family H3 controls, fold construction and eight distinct background clauses in packet2–2–2–2 balance. Report actual spare count and its family distribution. Seven candidate spares may disappear during acceptance; if the final bank has no adequate margin, report that rather than lowering a rule retrospectively.
5. **Freeze the amendment and validate the changed instrument.** Holder updates the protocol, source manifest, builders, owning Methods/design records and audit contract before relevant captures. Retain CONF64 and the existing dose grid, but qualify the altered clue/source/family distribution through CAL/PILOT and the existing statistical/causal gates. This review grants no launch permission.

**15 October decision:** there is **no demonstrated bank meeting the current twelve-clause, three-family, single-token rules without CSLB**. A measured amended candidate route exists, with explicit costs and limited margin. If its source policy or acceptance fails, compare (a) measured CSLB eligibility, (b) Buchanan original-response recoding with newly measured counts, and (c) the115-candidate two-token/ten-clause route with a budgeted R2/R3/H3 redesign. Smaller CAL/PILOT or external backgrounds alone do not solve the current deficit. Do not assume that adding available datasets automatically adds usable concepts.

## Pinned inputs and reproducibility

Existing McRae/Feats input hashes, tokenizer digest and driver provenance remain in the [preceding record](2026-10-02_bank_sources_codex_record.md). Tokenizer JSON SHA-256 is `87a7830d63fcf43bf241c3c5242e96e62dd3fdc29224ca26fed8ea333db72de4`, snapshot `c000ac2c2057d94be3fa931000c31723aac53282`. New checked downloads:

| External input | SHA-256 |
|---|---|
| Hovhannisyan `featurematrix.csv` | `152eb2cc1729514781f4087d7fd6bbf2f34ff05089af02636f1e11df57b80e33` |
| Hovhannisyan `conceptFeatureLabelList.xlsx` | `570aa322dd7af158f5d893a3c9f7ed47000a753607c63fbd81dd6bd53eb3dc3b` |
| Hovhannisyan `pics.csv` | `ce2688a42010e928d64f662cc6136a8a01f15e82a36b575d219179c2f1269d2a` |
| Vinson publisher ZIP | `3bb37252d5b6fadc13bfa93b971846b5005df5cd0e894e22b55dbf33f5b927c5` |
| Garrard institutional PDF | `88079b99323bb128aef07501e769dd43195fc06d529310ba60de4a12eb59369f` |
| Bolognesi `Norms COGVIM for release 185 conc.xlsx` | `20150ff6ea0613648c3219c2902ccd036fa898922491423a418a1046865d2712` |

Scratch checks: `/tmp/r052_design_levers.py` (existing-source family/token/cleaning scenarios), `/tmp/r052_hov_increment.py` (source priority, absolute-cutoff sensitivity and four-family tight screen), `/tmp/r052_token_lengths.py` (offline tokenization), `/tmp/r052_final_arithmetic.py` (joint witnesses and rejection-margin flow checks; output `/tmp/r052_final_arithmetic.txt`), and source inspection scripts under `/tmp`. They read external norm files and the existing taxonomy definitions; no stimulus file is written. For Hovhannisyan, first column supplies the concept, columns after the first three give relational features and integer productions. Apply the chosen threshold only to exact-new Hovhannisyan labels; McRae/Feats retain their published inclusion. Build WordNet hyponym/instance closures for the declared scenario, require dominant-sense membership and no other-family membership across any noun sense, apply E1 and the stated feature screen, then count unique dominant synsets. The tighter candidate-name ban is computed over the preliminary eligible cue set and applied once, conservatively including names later rejected; it is not an iterative mechanism for increasing counts.

Script SHA-256: main lever check `9865b846ea1fa2cd04bf148d7d5af51bc488ade01114af705cac2dfdf6822900`; Hovhannisyan check `e7b4c671ebce6ef480d18c6ca6af53724734bc6a18d266a16ed296e7caee8a8a`; tokenizer helper `f570ec2ec53c34aa671b52e31c1a1643f1308ccd801fb6c3dd0857cab7089912`. Scratch files are not committed deliverables; the pinned inputs, algorithm and count/witness tables above carry the review evidence.

Scientific/protocol implementation, author frontmatter, dispatch and the CSLB correspondence stay with their existing owners. Only this record and the R052 review/lifecycle log are owned here. The earlier source review, row19 paid-run review and full-bank R2 completion reports remain complete and are not resent or reopened.

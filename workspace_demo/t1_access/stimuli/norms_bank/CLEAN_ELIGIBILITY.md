# Cleaned eligibility: McRae and McRae + Feats under every usable-feature rule of §3.1

R084, 1 October 2026 (MDT), answering R052's handoff 1485a585 and Codex's record RSC 99277aa. Nothing is selected,
rendered or frozen. The scripts are `feats_parse.py`, `usable.py`, `token_counts.py` and `clean_eligibility.py`;
the counts are in `clean_eligibility.json`.

## The answer

Under §3.1 **as written** — twelve clauses, three families, single-token answers — the pool is **51 of 99**:
McRae + Feats gives animals 25, foods 15, vehicles 11. At ten clauses it is **77**. Neither fills the bank.

| | twelve | ten |
|---|---:|---:|
| McRae alone, single token | 46 | 65 |
| **McRae + Feats, single token** | **51** | **77** |
| McRae + Feats, up to two tokens (upper bound) | 72 | **114** |
| needed: CONF 64 + CAL 16 + PILOT 16 + one BACKGROUND per family | 99 | 99 |

**The only configuration that fills 99 is ten clauses together with two-token answers**, 114 with a feasible
joint allocation. Every other cell is short.

Codex's 80 (twelve) and 94 (ten) were upper bounds by his own statement: they apply only the family-word rule and
subsumption. The rest of §3.1 costs a further 29 concepts at twelve and 17 at ten, and almost all of that is one
rule (below).

## Feats is in the pipeline, with its bookkeeping asserted

`feats_parse.py` replaces R052's review driver. A concept present in McRae keeps McRae's whole feature set; a Feats
label absent from McRae adds its own; the alphabetic guard applies to both; parenthesised sense labels are not
stripped. The loader **asserts** the pinned figures and refuses to run if any file changes: 372 Feats labels, 13 in
the UK file, 136 exact overlaps (103 with identical feature sets, 33 differing), 236 exact-new, 208 after the
alphabetic guard. All five source files match the SHA-256 values in Codex's record, as does the tokenizer.

**Provenance is kept per row**, not per feature label: source and file version, that source's own relation label,
production count, respondent denominator and the published CV. McRae's file has no `Num_Parts`; its denominator is
recorded as 30 by the study's design. The composite digest covers McRae and both Feats feature files.

**CV policy.** The authors' `CV_No_Tax` is reported as published, labelled with its source, and used only as a
selection heuristic inside one concept. Because each concept takes all its features from a single source, no
concept's ranking ever mixes the two reference universes, so the non-invariance Codex found (airplane / has_wings:
.038 in McRae, .141 in Feats) never enters a comparison. Nothing is recomputed under the authors' name.

**Missing-CV policy.** The UK file has no `CV_No_Tax` column. Nine exact-new concepts have no published CV on any
feature (elbow, neck, raincoat, road, seaside, smell, stairgate, tea, woman). Their features are ranked by
normalised production frequency, 30 × Prod_Freq / Num_Parts, labelled as such; nothing is imputed. Only *tea* is a
candidate in an adopted family (foods, 14 usable features at twelve), so the policy touches one concept.

## The usable-feature rules, and what each one costs

Applied in this order (`usable.py`): **T** taxonomic rows go (the source's own relation label; §3.1 says rule F
removes them); **F** literal family words go; **N** a feature naming its own concept goes; **X** a feature naming
another candidate concept goes; **P** proper nouns and brand names go; **D** words sharing a Porter2 stem or a
WordNet derivational link merge, then equal word sets coalesce and a subset merges into the more specific feature.

The protocol count with **one** rule switched off, McRae + Feats, single token:

| | all rules | without T | without N | without X | without P | without D |
|---|---:|---:|---:|---:|---:|---:|
| twelve | 51 | **67** | 52 | 56 | 53 | 51 |
| ten | 77 | **85** | 77 | 83 | 77 | 77 |

**Rule T is the cost: 16 concepts at twelve, 8 at ten.** It removes `a_bird` from robin, `a_fruit` from apple,
`an_insect` from bee, `a_dessert` and `a_snack` from cookie, and example-of rows such as `eg_-_dump` from truck.
§3.1 justifies it as "McRae's taxonomic features are family words by construction". That holds for `an_animal`,
`a_food` and `a_vehicle`, which rule F removes anyway. It does not hold for `a_bird` or `a_fruit`, which name no
adopted family. **Narrowing T to literal family words is R052's call, not mine**, and the "without T" column
shows what it would buy: 67 at twelve and 85 at ten — still short of 99 in both.

**Rule X is second: 5 at twelve, 6 at ten.** It is literal, like `check_clues.py`: *ambulance* loses `is_orange`
because "orange" names a foods concept, and *butter* loses `comes_from_cows`. The comparison set is every
candidate, which the real bank is a subset of, so X removes at least as much here as it will at build time.

**Rule D costs nothing.** That agrees with Codex's finding that Porter2 normalisation moved no count. It needed one
fix first, below.

**Rule P** strips 69 of the 78 capitalised labels. The other nine are on a declared list of common nouns the norms
happen to capitalise (A, C, Y, CD, CD's, AM, FM, UFO, NaCl). Every label and its verdict is in the gitignored
detail file.

### A defect I found and fixed in my own derivation rule

The first version followed WordNet derivational links from **every lemma of every synset** of a word, synonyms
included. Union-find then chained unrelated words through polysemy into a 440-word class: *bread* joined
*cabbage* and *sugar*, which are all slang for money in one WordNet synset, and *bite* joined *tin* and *fire*.
That version reported 44 at twelve. Links are now followed only from the word's own lemmas. A base form counts
only if it shares the word's Porter2 stem or is in WordNet's own irregular-exception list (bitten→bite, told→tell,
is→be). Otherwise morphy turns "bees" into the verb *be*. The largest class is now six words
(play/player/playful…), and D costs nothing.

## Codex's figures, reproduced before going further

Every raw and minimal figure in Codex's records reproduces exactly from my committed code. Single token: raw 85
and 100; minimal 35/30/15 = **80** and 41/33/20 = **94**. Two tokens: raw 130 and 149; minimal 118 and 142. His
named cases also reproduce: cart 11→9, skateboard 10→9, rice, sandwich, spaghetti and toast →9. Under the full
rules they fall further — sandwich and spaghetti to 5 — mostly through T and X.

## Allocation

`clean_eligibility.py` checks a **joint integer** allocation per count triple. One BACKGROUND per family is reserved
first. Every split must contain all three families with each at no more than half, so cross-family reciprocal
pairs and a third-family competitor exist, and role totals are disjoint. The check is exhaustive over CONF and
CAL, with PILOT in closed form, and it also reports a reserve-aware largest-remainder witness.

- Raw 100 (single token, ten) is feasible. My proportional witness is CONF 26/24/14 and CAL 7/6/3 — Codex's
  exactly — then PILOT 6/6/4 and BACKGROUND 2/1/1, an equally valid split of his PILOT 7/6/3, BACKGROUND 1/1/2.
- **114 (two tokens, ten, all rules) is feasible:** proportional CONF 32/21/11, CAL 8/5/3, PILOT 8/5/3,
  BACKGROUND 13/2/3. Animals sit at the half-bound in every split, so the margin is in animals only.
- Every single-token configuration under the full rules is short, by 48 at twelve and 22 at ten.

## The two-token bound, and what it costs the decode

Relaxing E1 to two tokens and keeping every other rule gives **72 at twelve, short by 27, and 114 at ten, feasible
with 15 above 99**. Of the 114, **38 are two-token answers**. **None shares its first token with another
answer**, so no two bank concepts would be indistinguishable on the first token. That collision risk does not
materialise in this pool.

The cost that remains is the one E1 exists to prevent. The study reads each answer from **one** answer-position
logit: the R3 closed-set argmax over frozen token ids, the linear token readout, and the H3 token-direction
interventions. A two-token answer has no such logit. Its first token is prefix mass, shared with every word that
begins the same way. It has to be scored as log P(t1|x) + log P(t2|x, t1), which needs a second, teacher-forced
position per answer and a declared termination rule. It also leaves 38 concepts read differently from the other
76 within one bank. That is a redesign of the readout, not a stimulus rule, and it is the owner's to weigh beside
the CSLB answer on 15 October. **This is the number, not a proposal.**

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/feats_parse.py          # asserts the bookkeeping
upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/token_counts.py   # E1 input, pinned tokenizer
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/clean_eligibility.py    # every table above
```

The norms stay outside the repo (`~/word-norms-mcrae/`, `~/word-norms-feats/`). `clean_eligibility.json` holds
counts, cue words, allocations and digests only. The per-concept record of what each rule removed is
`clean_eligibility_detail.json`; it holds feature labels, so it is gitignored. R052's untracked driver outputs in
this folder (`pool_eligible_feats*.json`, `pool_eligible_mcrae_min*.json`) were deleted as instructed.
`family_pool.py` now states in its docstring that its F3 is a raw ceiling.

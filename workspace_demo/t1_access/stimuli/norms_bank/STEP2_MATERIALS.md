# Step 2/3 trial on materials: the loop runs, and it shows the source cannot carry the clauses

R084, 24 September 2026, answering R052's handoff fdb701dc against §3.1 as revised at RSC 742619c.
Materials only, as instructed. **The reader model was available and the loop ran end to end.**

The instruction was to take materials because it is the family most likely to tell us the
construction does not work. It did, and at two separate places.

## The reader model

`llama3.1:8b` through ollama on 127.0.0.1 — Meta Llama 3.1 8B Instruct, Q4_K_M, digest
`46e0c10c039e`, temperature 0, seed 20260924. It is distinct from the model under test
(Qwen3.6-27B, Alibaba) and from the model that renders the clauses (Claude, Anthropic), which is
what §3.1 requires. No judgement was substituted for it anywhere.

## Finding 1 — Buchanan's "features" are words, not feature statements

This is the one that matters, and it was not visible until rendering was attempted.

§3.1 says rendering "must PRESERVE the cited feature and add nothing", on the model of a feature
tag like `has_trunk`. **Buchanan's file contains no such tags.** Its `feature` column holds single
content words extracted from free-text participant descriptions, with the production frequency of
each word. The raw responses in the source repository (`0.5 raw words/garbage.txt`) are unsegmented
prose:

> *"trash thrown away something you don't want broken food scraps landfills trash trucks stinky
> gross"*
> *"smells rotten attracts flies attracts other animals draws bugs can start to decompose…"*

What survives into the analysis file for `garbage` is: away, bad, dump, dumpster, gross, landfill,
long, longer, smell, smells, smelly, take, trash, want, unwanted, waste. `oak` yields `as`. The
relation is gone. **`leather` + `cow` does not say whether leather is made from a cow, comes from a
cow, or is found near one** — and the relation is precisely what a clause asserts.

So every clause is authored: the source fixes the topic word, and the renderer supplies the
predicate. "is the cured hide of a large grazing beast" cites `hide`; the other nine words are
mine. That is the self-authored content the rebuild exists to remove, reintroduced at the last
step. A per-clause citation reading *the word "away" was produced by 20 participants for the cue
garbage* does not license the sentence *is taken away by a collection truck each week*.

**McRae (2005) does carry the relation**, which is why it is the structurally correct source: its
entries are relational statements with an explicit relation type — *alligator beh- eats people*,
*airplane inbeh- crashes*, *inbeh- lives in* (Migrating Psycholinguistic Semantic Feature Norms
into Linked Data, ACL W13-5511, quoting the database). CSLB (638 concepts, 30 participants each)
likewise publishes normalised feature labels. The handoff named both as coverage fallbacks; they
are not fallbacks, they are the format §3.1 assumes.

## Finding 2 — two materials concepts cannot supply twelve clauses at all

Mechanical, before any rendering or naming test. The existing writing rules N (never name its own
concept), F (no family word) and X (no other bank concept's surface form) remove features from the
candidate pool, and two concepts fall below twelve:

| concept | features | usable | blocked |
|---|---:|---:|---|
| **cotton** | 13 | **11** | shirt (clothing), clothe (clothing) |
| **waste** | 13 | **11** | trash (materials), garbage (materials) |
| trash | 18 | 14 | waste, garbage, dirt (materials), food (family word) |
| starch | 17 | 14 | potato (foods), clothe (clothing), food (family word) |
| leather | 25 | 19 | pant, clothe (clothing), cow, animal, material, car |
| paint | 34 | 30 | coat (clothing), paint (its own name), arm (body parts), house (buildings) |

`waste` is the family's binding concept and it is blocked by `trash` and `garbage` — which are
themselves materials concepts. The family contains four near-synonyms (garbage, trash, waste, dirt)
that appear in each other's feature lists, so rule X turns them into mutual exclusions.

**Materials therefore runs 14, not 16, before the naming test has said anything.** That is within
§3.1's floor of 13, and it is reported loudly as instructed rather than worked around.

## Finding 3 — the naming test measures the rendering, not the source

Four concepts were selected, rendered and tested — 48 clauses. Selection used the §3.1 spanning
heuristic (`select_features.py`); all clauses pass T, N, F, X and S mechanically.

| concept | clauses named | verdict | named at sharing counts |
|---|---:|---|---|
| leather | 3 | re-select / pass over | belt 7, hide 25, **soft 107** |
| shampoo | 4 | re-select / pass over | conditioner 1, condition 6, soap 15, shower 6 |
| card | 6 | re-select / pass over | greet 4, credit 6, birthday 7, deck 7, game 50, plastic 74 |
| **marble** | **0** | **accept** | — |

**Decisiveness has no relationship to sharing count.** Leather's most-shared selected feature,
`soft` at 107 cues, produced a clause the reader named; its two rarest, `smoothest` at 1 and
`tough` at 2, did not. Card was named across the entire range, from 4 to 74. This is direct
evidence for R052's reason for withdrawing K: the statistic does not measure the construct.

**But the accepted concept is the problem, not the reassurance.** Marble passed with 0 of 12 named
because its clauses are vague. The reader answered: globe, ball, beans, stamp, ball, coin, glitter,
hoop, pencil, ice, tie, egg. A packet that plays all twelve at k = 8 still does not point at
marble. Card failed because its features (credit, birthday, deck) are near-definitional.

So acceptance is driven by how specific the renderer chose to be, and the criterion **rewards
vagueness**: the way to pass a concept is to write clauses that identify nothing. Since the
renderer is Claude, decisiveness is back in the author's hands, which is what §3.1's naming test
was adopted to prevent.

## Sample, to read rather than trust

`leather` — cited word in brackets, everything else authored:

```
      [smoothest/1]  is among the smoothest surfaces a hand can run across   -> reader: Glass
      [tough/2]      stays tough enough to survive many years of daily use   -> reader: Spoon
NAMED [belt/7]       is commonly formed into a belt worn around the waist    -> reader: Leather
      [purse/4]      is moulded into a purse carried over one shoulder       -> reader: Shoulder bag
      [furniture/21] covers the furniture in many formal sitting rooms       -> reader: Carpets
      [brown/91]     is most often a deep brown shade rather than a bright one -> reader: Coffee
NAMED [soft/107]     grows softer and more supple the longer it is handled   -> reader: Leather
NAMED [hide/25]      is the cured hide of a large grazing beast              -> reader: Leather
```

`shampoo` — five of its twelve selected features are the same idea:

```
      [cleanser/6]    works as a cleanser that lifts away oil and grease     -> reader: Soap
      [cleanliness/9] is bought for cleanliness rather than for any other reason -> reader: Soap
      [cleanse/14]    cleanses without stripping away everything it touches  -> reader: Soap
      [clean/76]      is used to clean what grows on top of the head         -> reader: Hairbrush
NAMED [condition/6]   is meant to condition as much as it is meant to wash   -> reader: Shampoo
```

## Finding 4 — lemmatising does not merge the variants that matter

36 near-duplicate pairs across the 16 concepts' selected twelves. `shampoo` has 11: conditional /
condition / conditioner, cleanser / cleanliness / cleanse / clean, soapy / soap, smelly / smell.
`dirt` has 7, `starch` 4 (stiff / stiffen / stiffener, thicker / thickener), `glue` 4 (elmer /
elmers, pasty / paste, crafty / craft, sticky / stick).

WordNet's lemmatiser only merges inflections, not derivations, so a concept's "twelve distinct
features" can be four ideas restated. That matters for the dose design specifically: if clauses
5 through 9 restate clause 3, adding them adds no evidence, and the k-graded curve §5 depends on
flattens for a reason that has nothing to do with the model.

`glue`'s two decisive candidates are `elmer` and `elmers` — one brand name, counted twice.

## What I did not do

I did not render the remaining twelve materials concepts. Findings 1 and 2 are not fixed by more
rendering, and 168 further authored clauses would embed the problem rather than measure it. The
selection for all sixteen is committed (`select_features.py` prints it) and rendering resumes the
moment the source question is settled.

## What this needs from R052

1. **The source format.** Buchanan cannot carry the rendering rule as written. Either the rule
   changes to acknowledge that the predicate is authored from a cited topic word — which weakens
   the citation claim the rebuild exists for — or the bank moves to McRae or CSLB, whose entries
   are relational statements. McRae is 541 concepts and CSLB 638, against Buchanan's 4,411, so
   family sizes must be re-measured against the eight roots before anything is promised.
2. **Materials at 14**, from rule X alone, driven by four near-synonymous concepts in one family.
3. **The acceptance criterion rewards vagueness.** A concept passes by saying nothing identifying.
   If the naming test stays, it needs a floor as well as a ceiling — some minimum of clauses the
   reader can use — or the bank fills with concepts nobody could ever name.
4. **Derivational variants** should be merged before selection, or a concept's twelve clauses can
   be four facts.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/select_features.py materials
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/naming_test.py \
    t1_access/stimuli/norms_bank/trial_clauses_materials.json
```

`trial_clauses_materials.json` is the four-concept trial, **not a bank**, and
`trial_naming_results.json` is every reader answer behind the table above.

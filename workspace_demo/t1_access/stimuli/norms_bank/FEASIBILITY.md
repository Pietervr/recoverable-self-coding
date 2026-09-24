# Rebuilding the T1 clue bank on published feature norms: what the norms can supply

R084, 23 September 2026. Measurement for R052, who owns `PREREGISTRATION_T1_model.md` §3 and
amends it from these numbers. Answers handoffs d310454e and 7d4428c1. Step 1 only: nothing is
selected, rendered or frozen, and no existing bank file is touched.

## Where this stands

**Settled by R052 on 24 September, and applied throughout below.**

- The eight-family structure stays. §3's background list is "eight background clauses, exactly one
  from a BACKGROUND concept of each family", so the packet's eight slots *are* the eight families;
  six families cannot fill a packet without redesigning the nesting and every §10 power number.
  16 per family is exactly 4 BACKGROUND + 2 CAL + 2 PILOT + 8 CONF, so a smaller per-family count
  comes straight out of the 64 CONF concepts.
- **Membership is dominant-sense.** A cue belongs to a family when its *first* WordNet noun synset
  lies in that family's subtree. One citable sentence, and it only tightens the all-senses rule.
- **Countries is replaced by clothing.**
- **Tools and instruments are replaced.** Buildings is adopted as one replacement.
- **E1 and E2 are unchanged.** E1 is a decode rule — the single-token answer form is what makes the
  answer-position logit readable — so it was not relaxed.
- **The feature identity is the raw `feature` string, lemmatised.**

**Open, and the reason this document is still being read:** at the decided threshold of ≥ 12
features, **buildings yields 15, one short of 16**, and neither candidate measured for the eighth
slot clears it as specified. See "The eighth family" below.

## Source, and that it is the right file

| | |
|---|---|
| Buchanan, Valentine & Maxwell (2019), *Behavior Research Methods* 51(4), 1849–1863 | 4,436 concepts |
| `github.com/doomlab/Word-Norms-2`, `4 analysis/final words 2017.xlsx` | 7,173,768 bytes |
| sha256 | `6e1fc087986d5657684e190c2c04bd5a2c40f1d39b78eebb0ead8bb5e2225337` |
| held at | `~/word-norms-2/` — outside the repo, not redistributed |

Parsed with `zipfile` + `re` (an `.xlsx` is a zip of XML), no pandas and no openpyxl: 69,284 data
rows, 4,436 distinct cues, of which 4,411 are single words — the other 25 are sense-disambiguated
(`bat_animal`, `bat_baseball`). On the raw feature column, 2,585 single-word cues carry ≥ 12
features and 1,405 carry ≥ 16. **Those four counts reproduce R052's measurements exactly**, which
is the check that this is the same file read the same way.

## Feature identity: lemmatised

The `feature` column, lowercased, stripped, lemmatised as a noun, and if that is a no-op lemmatised
as a verb. Lemmatiser: `nltk.stem.wordnet.WordNetLemmatizer`, nltk 3.10.3, WordNet 3.0.

Not the raw string: inflections as separate strings fragment the sharing counts, and because cue
validity is approximated by 1 / (cues sharing the feature), fragmentation makes every feature look
rarer than it is and so systematically **overstates** decisiveness. Not `translated` either: it
collapses on meaning, a judgement we would be importing, and leaves only 878 cues at ≥ 12 features.

**This is what reconciles the elephant example.** On raw strings elephant's rarest features are
`trunks` shared by 1 cue and `tusk` by 2. Lemmatised, they are `trunk` shared by 3 and `tusk` by 3
— exactly the figures in R052's original brief. The discrepancy was the fragmentation, and
lemmatising removes it.

It does not collapse every irregular: `teeth` and `men` are themselves WordNet noun lemmas, so they
stay separate from `tooth` and `man`. That is a handful of cases and it errs toward residual
fragmentation, so it is left as specified.

**Cost of lemmatising, measured:** distinct feature strings fall from 11,424 to 7,534, and cues at
≥ 12 features from 2,585 to 1,474. This is a large contraction and it is why the threshold now
binds (see the sweep below).

## The rules as implemented

Applied in order, each counted so the attrition is visible (at ≥ 12 lemmatised features):

- **F1** `pos_cue = noun` in the norms *and* the cue has a WordNet noun sense → 3,072 cues.
  `pos_cue` is unanimous per cue, so this is the norms' own judgement: `rake` is normed 65/65 rows
  as a verb, so its features describe the action and it is correctly out of tools.
- **F2** the cue is its own WordNet base form → 2,957. Drops `arms`, `beans`: inflections of cues
  already in the pool.
- **F3** ≥ 12 distinct lemmatised features → 1,131.
- **F4** the cue's **first** noun synset lies in the family's hyponym + instance-hyponym closure.
- **E2** no noun sense of the cue lies in **another** family's subtree — the existing rule computed
  from the taxonomy instead of the hand-written `COLLISIONS` list, recomputed per scenario. E2
  tests *all* senses, because the prompt scan cannot tell senses apart.
- **E1** the answer-context form `' x'` is a single token under the frozen Qwen3.6 tokenizer
  (snapshot `c000ac2c…`). Unchanged.

A dominant-sense concept is a **synset**, not a word: `ax`/`axe` and `bike`/`bicycle` are one
concept. Cues sharing a dominant synset are collapsed **after** E1, so a concept is lost only when
every one of its cues fails E1.

One documented root synset set per family, chosen to match the family's ordinary meaning and not to
maximise a count: `animal.n.01`, `body_part.n.01`, `food.n.01`+`food.n.02`, `vehicle.n.01`,
`material.n.01`, `clothing.n.01`, `building.n.01`, and for the candidates
`geological_formation.n.01`+`body_of_water.n.01` and `worker.n.01`(+`professional.n.01`).

The all-senses reading (`any_sense`) is still computed and reported in `pool_eligible.json`, but it
is not the rule: it admits `bark` the sailing ship, `secretary` the writing desk and `kettle` the
kettledrum.

## Eligible per family, dominant-sense, and the threshold sweep

Concepts, not words. Scenario: the six families that stand on their own, plus buildings, plus
occupations. **≥ 12 is the decided threshold**; the other two columns are the sensitivity R052
asked to see before §3 fixes it.

| family | ≥ 12 | ≥ 10 | ≥ 8 |
|---|---:|---:|---:|
| foods | 40 | 52 | 63 |
| animals | 36 | 41 | 45 |
| body parts | 25 | 28 | 33 |
| vehicles | 19 | 23 | 24 |
| clothing | 19 | 20 | 23 |
| occupations | 18 | 25 | 30 |
| **materials** | **16** | 26 | 36 |
| **buildings** | **15** | **15** | 18 |
| *natural features* | *11* | *11* | *17* |

Needed: 16. **Materials sits exactly on 16 with no margin; buildings is one short at ≥ 12 and at
≥ 10, and only clears at ≥ 8.** Every family clears at ≥ 8.

**Lowering the threshold is not actually available.** Step 2 selects 12 features per concept, one
per clause, so a concept with 8 normed features cannot supply its 12 clauses. The ≥ 12 threshold is
not a tuning knob — it is 12 clauses per concept restated. The ≥ 10 and ≥ 8 columns show where the
headroom would be if the clauses-per-concept count itself changed, which is a §3 decision with its
own cost, and nothing below ≥ 12 is usable as the design stands.

## The eighth family

Both candidates were measured in the full eight-family scenario, so the pair interaction with
buildings through E2 is included.

**A. Natural features** (`geological_formation.n.01` + `body_of_water.n.01`) — **11. Does not
clear.** Members: ascent, bank, cave, cliff, coast, mountain, reef, river, sea, shore, slope.
It fails on the **feature threshold**, not on taxonomy or tokenizer — its ceiling is 128, so the
words exist and are single tokens. Of R052's twenty expected words: mountain (21 features), river
(13), cliff (23) and cave (12) are in; `lake` is lost to E2 (also a pigment, so it sits in
materials); valley, glacier, creek and ridge are **not normed at all**; and island (11), swamp (10),
canyon (9), hill (9), volcano (9), ocean (9), bay (8), pond (8), desert (7), beach (7) and stream
(7) are normed but **below 12 features**. Natural features attract fewer distinct feature responses
than artifacts do. At ≥ 8 it reaches 17.

**B. People by occupation** — the root matters, and `worker.n.01` alone is the wrong one.

- `worker.n.01` as specified → **13. Does not clear.** It excludes doctor, nurse and teacher, which
  sit under `professional.n.01` → `adult.n.01`, a sibling branch, not under worker; and farmer,
  which sits under `creator.n.02`. This is a root artifact, not a shortage of normed occupations.
- `worker.n.01` + `professional.n.01` → **18. Clears.** Members: captain, chef, commander, cook,
  cowboy, doctor, editor, helper, lawyer, maid, nurse, officer, plumber, professor, rebel, teacher,
  veteran, washer. Ceiling 241.

R052's flagged concern about `person.n.01` ancestry dragging in body-part collisions did not
materialise: E2 costs occupations only `sailor` (also a collar) and `worker` (also an insect caste).
The pair interaction is small but not nil — adopting occupations costs **materials** one concept,
`clay`, which is also a person in WordNet, and that is what leaves materials sitting exactly on 16.
No other family moves by more than 1 against the natural-features scenario.

E1 removes beautician, cowgirl, electrician, mailman and stewardess at 2 tokens.

## What R052 has to decide

1. **Buildings is 15, not the 16 measured before.** The lemmatised identity cost it one concept —
   17 words survive E2; `castle` and `palace` are the same synset (`palace.n.01`) and so one
   concept, giving 16; `skyscraper` then fails E1 at 2 tokens, giving 15. Separately, cabin, church,
   court and school fail the dominant-sense rule — church sense 1 is the body of Christians, school
   sense 1 the educational institution, court sense 1 the judicial assembly, cabin sense 1 a room on
   a ship — and monastery has only 8 features. The threshold cannot rescue it: buildings is 15 at ≥ 10 too,
   and ≥ 8 is not usable while each concept needs 12 clauses. So the options are: accept 15 in that
   family and carry the §3 arithmetic change, replace buildings with another family, or reduce
   clauses per concept — which would free the threshold but is a protocol change.
2. **The eighth family.** Neither candidate clears as specified. Occupations with
   `worker.n.01` + `professional.n.01` clears at 18 and is the same family concept R052 named,
   with the root that actually contains occupations. R052 said to report and stop rather than hunt
   a third candidate, so that is what this does.
3. **Materials has zero margin at 16.** Any later tightening removes a concept from a family that
   has none to give, and it is the family most exposed to E2 — it already loses alligator, beaver,
   cherry, fur, leopard, lime, mink, raccoon, salt and sponge to animals, foods or clothing.
4. **Nothing is frozen** until §3 is amended. Step 2 runs on the amendment.

## Licence

Unchanged, and it gates publication rather than this build. The norms are held outside the repo,
are not redistributed, and nothing derived from them is published beyond our own prose and a
per-clause citation table. `pool_eligible.json` contains cue *words* and counts, no feature
strings. R052 is confirming reuse terms with the authors or the library.

NOVA (arXiv 2505.10718) was not used: LLM-augmented norms would reintroduce the circularity.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/norms_parse.py --lemmatise
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/family_pool.py
upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/pool_e1.py
MIN_FEATURES=8 t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/family_pool.py   # the sweep
MIN_FEATURES=8 upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/pool_e1.py
```

`.venv-build` is a separate venv holding nltk 3.10.3 and WordNet 3.0. Neither nltk nor WordNet went
into `t1_access/.venv`, which stays version-pinned for parity. `pool_wordnet*.json` and the
`*_min8` / `*_min10` sweep outputs are regenerable and gitignored; `pool_eligible.json` is the
committed measurement record at the decided threshold.

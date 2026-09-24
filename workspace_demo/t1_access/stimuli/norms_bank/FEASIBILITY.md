# Rebuilding the T1 clue bank on published feature norms: what the norms can supply

R084, 23 September 2026. Measurement for R052, who owns `PREREGISTRATION_T1_model.md` §3 and
amends it from these numbers. Answers handoffs d310454e, 7d4428c1 and b0a1f386. Step 1 only:
nothing is selected, rendered or frozen, and no existing bank file is touched.

## Where this stands

**Settled by R052 on 24 September in §3.1 of the preregistration (RSC 0ed1365), and applied
throughout below.**

- The eight-family structure stays. §3's background list is "eight background clauses, exactly one
  from a BACKGROUND concept of each family", so the packet's eight slots *are* the eight families;
  six families cannot fill a packet without redesigning the nesting and every §10 power number.
  16 per family is exactly 4 BACKGROUND + 2 CAL + 2 PILOT + 8 CONF, so a smaller per-family count
  comes straight out of the 64 CONF concepts.
- **Membership is dominant-sense.** A cue belongs to a family when its *first* WordNet noun synset
  lies in that family's subtree. One citable sentence, and it only tightens the all-senses rule.
- **Countries is replaced by clothing.**
- **Tools and instruments are replaced**, by **buildings** and **occupations**
  (`worker.n.01` with `professional.n.01`). They could not be kept: after E2 and E1 the ceiling
  over their entire WordNet subtrees is 11 concepts each.
- **The bank is 127, not 128.** Buildings supplies 15 and the shortfall comes out of BACKGROUND,
  which is the only split it can come from: CAL, PILOT and CONF are fixed by the pairing at 8, 8
  and 32 pairs, so an odd count in any of them cannot be paired, while BACKGROUND concepts are
  never a target, foil or competitor. Buildings takes 3 BACKGROUND instead of 4; CONF stays 64.
- **Materials stands at exactly 16 with no margin**, recorded in §3.1 rather than engineered away.
- **E1 and E2 are unchanged.** E1 is a decode rule — the single-token answer form is what makes the
  answer-position logit readable — so it was not relaxed.
- **The feature identity is the raw `feature` string, lemmatised.**

**Open, and the reason this document is still being read:** *K*, the floor on sharing count for
the ten non-decisive clauses, is not set, and the measured distribution says **no useful value of
it exists at 16 concepts per family** — the ceiling is K = 2, which is cue validity 0.5. See
"Setting K" below. Selection cannot run until R052 settles it.

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

## How the eighth family was chosen

Both candidates R052 named were measured in the full eight-family scenario, so the pair interaction
with buildings through E2 is included. **Occupations was adopted**, at 18 concepts.

- **Natural features** (`geological_formation.n.01` + `body_of_water.n.01`) — 11, short. It fails on
  the **feature threshold**, not on taxonomy or tokenizer: its ceiling is 128, so the words exist
  and are single tokens. Of the twenty expected, mountain (21 features), river (13), cliff (23) and
  cave (12) are in; `lake` goes to E2 (also a pigment, so it sits in materials); valley, glacier,
  creek and ridge are **not normed at all**; island (11), swamp (10), canyon (9), hill (9),
  volcano (9), ocean (9), bay (8), pond (8), desert (7), beach (7) and stream (7) are normed but
  below 12 features. Natural features attract fewer distinct feature responses than artifacts do.
- **People by occupation** — the root decides it. `worker.n.01` alone gives 13, because it excludes
  doctor, nurse and teacher, which sit under `professional.n.01` → `adult.n.01`, a sibling branch,
  and farmer, which sits under `creator.n.02`. With `worker.n.01` + `professional.n.01` the same
  family gives **18**: captain, chef, commander, cook, cowboy, doctor, editor, helper, lawyer, maid,
  nurse, officer, plumber, professor, rebel, teacher, veteran, washer. Ceiling 241. E1 removes
  beautician, cowgirl, electrician, mailman and stewardess at 2 tokens; E2 costs only `sailor`
  (also a collar) and `worker` (also an insect caste).

Adopting occupations costs **materials** one concept — `clay`, which is also a person in WordNet —
and that is what leaves materials sitting exactly on 16. No other family moves by more than 1.

## Why buildings supplies 15

17 words survive E2; `castle` and `palace` are the same synset (`palace.n.01`) and so one concept,
giving 16; `skyscraper` then fails E1 at 2 tokens, giving 15. Separately cabin, church, court and
school fail the dominant-sense rule — church sense 1 is the body of Christians, school sense 1 the
educational institution, court sense 1 the judicial assembly, cabin sense 1 a room on a ship — and
monastery has only 8 features. The threshold cannot rescue it: buildings is 15 at ≥ 10 as well, and
≥ 8 is not usable while each concept needs 12 clauses.

## Setting K: the distribution, and why no useful K exists at 16 per family

§3.1 ranks a concept's 12 **selected** features by sharing count, marks the two rarest decisive, and
requires every other selected feature to be shared by at least *K* cues. K is not yet set.

Because selection chooses *which* 12 of a concept's features to use, two statistics matter and they
are not the same:

- **R3** — the sharing count of the concept's 3rd-rarest feature overall. This is the number K must
  clear if the 12 selected are simply the 12 rarest.
- **KMAX** — the largest K the concept can satisfy at all: spend the two rarest on the decisive
  pair, sort the rest by sharing count descending, and read off the 10th. Any K ≤ KMAX is feasible,
  by selecting the ten most-shared of the remaining features.

They coincide exactly when a concept has 12 features, since then the ten non-decisive clauses are
forced. Above 12 features KMAX exceeds R3, and **KMAX is what decides whether a concept can be
built.** Sharing counts are over the 4,411 single-word cues, so a feature shared by *s* cues has
cue validity ≈ 1/*s*.

**Pooled, over every candidate feature of every eligible concept** (n = 4,209): min 1, p10 4,
p25 12, median 35, p75 84, p90 196, max 537.

| statistic | min | p10 | p25 | median | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| R3, over 188 eligible concepts | 1 | 2 | 2 | 5 | 10 | 14 | 78 |
| KMAX, over 188 eligible concepts | 1 | 5 | 12 | 35 | 73 | 89 | 147 |

Per family, KMAX (min / median / max): animals 4 / 44 / 105 · body parts 1 / 64 / 147 · buildings
5 / 17 / 55 · clothing 2 / 75 / 98 · foods 1 / 28 / 106 · materials 2 / 20 / 93 · occupations
1 / 12 / 71 · vehicles 1 / 37 / 93.

### The ceiling is K = 2

A family keeps K only if it still has enough concepts clearing it. The family ceiling is therefore
its *n*-th largest KMAX, and the bank's ceiling is the smallest of those:

| family | needs | has | slack | K ceiling | weakest concepts (KMAX) |
|---|---:|---:|---:|---:|---|
| **materials** | 16 | 16 | **0** | **2** | waste 2, starch 4, cigarette 6, dirt 6 |
| **occupations** | 16 | 18 | 2 | **3** | editor 1, professor 2, plumber 3, helper 4 |
| **buildings** | 15 | 15 | **0** | **5** | restaurant 5, convent 6, chapel 7, cathedral 9 |
| vehicles | 16 | 19 | 3 | 19 | aircraft 1, yacht 9, missile 17 |
| clothing | 16 | 19 | 3 | 23 | lingerie 2, gown 10, tie 13 |
| foods | 16 | 40 | 24 | 37 | seafood 1, barbecue 2, vodka 2 |
| animals | 16 | 36 | 20 | 44 | bee 4, worm 7, ant 8 |
| body parts | 16 | 25 | 9 | 61 | forehead 1, nerve 2, colon 6 |

**The bank ceiling is K = 2, bound by materials**, which has exactly 16 concepts and so cannot drop
`waste`. At K = 2 a non-decisive clause need only be shared by 2 of 4,411 cues — **cue validity
0.5**. That is not a floor; it is the absence of one, and it does not achieve what K is for.

Concepts that cannot clear a given K: 4 of 188 at K = 2, 10 at K = 3, 18 at K = 5, 37 at K = 10,
73 at K = 20.

The reason is visible in the binding concepts' own profiles — these are concepts whose features are
nearly all rare, so almost every clue gives them away:

```
editor      15 features, shares [1,1,1,1,1,1,1,1,1,4,11,15,18,80,497]
seafood     13 features, shares [1,1,1,1,2,2,22,39,52,55,132,245,253]
aircraft    12 features, shares [1,1,1,3,10,17,20,33,41,46,79,85]
waste       13 features, shares [1,1,2,2,2,4,7,11,12,37,42,62,67]
```

### The trade, if the per-family count were to move

| concepts per family | bank K ceiling | binding family |
|---:|---:|---|
| 16 | 2 | materials |
| 15 | 4 | materials, occupations |
| 14 | 5 | occupations |
| 13 | 6 | materials, occupations |
| 12 | 8 | materials |
| 10 | 10 | materials |

K = 10 is cue validity 0.1 and needs 10 concepts per family; K = 20 (validity 0.05) is not reachable
at any per-family count this source supports across eight families. **No setting of K makes the ten
non-decisive clauses genuinely non-decisive while the bank is 16 per family.** That is a property of
the source, and it is reported rather than engineered around.

### One rule detail this exposes

§3's selection draws 16 per family **by seed from the eligible list**, and the eligible list is not
filtered by K. Wherever a family has slack, a seeded draw can pick a concept whose KMAX is below K
even though the family as a whole clears it. The eligible list must be filtered to K-feasible
concepts *before* the seeded draw, or the draw can fail for a reason the seed does not record.
At K = 2 this is a no-op for materials and buildings, which have no slack, but it is not a no-op
for foods, animals or body parts.

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
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/sharing_distribution.py        # K
```

`.venv-build` is a separate venv holding nltk 3.10.3 and WordNet 3.0. Neither nltk nor WordNet went
into `t1_access/.venv`, which stays version-pinned for parity. `pool_wordnet*.json` and the
`*_min8` / `*_min10` sweep outputs are regenerable and gitignored; `pool_eligible.json` is the
committed measurement record at the decided threshold, beside `sharing_distribution.json`.

# Step 1 feasibility: can the T1 clue bank be rebuilt on published feature norms?

R084, 23 September 2026, answering the handoff
`prompts/2026-09-24_t1_bank_rebuild_on_published_norms.txt` (R052, handoff d310454e).
Step 1 only. Nothing is selected, rendered or frozen here, and no existing bank file is touched.

## The answer in three lines

1. **Five of the seven retained families clear 16 comfortably** from Buchanan alone: animals, body
   parts, foods, vehicles, materials.
2. **Clothing is the replacement for countries**, decisively over furniture: 34 eligible against 17
   on the permissive reading, 23 against 9 on the conservative one.
3. **Tools (13) and instruments (11) cannot reach 16 — and no other human norm set can fix them.**
   The binding constraint is E1, not the norms: across the whole of WordNet only 11 single-token
   nouns have a tool as their dominant sense, and only 11 have a musical instrument. This is a
   design question for R052, not a sourcing one.

## Source, and that it is the right file

| | |
|---|---|
| Buchanan, Valentine & Maxwell (2019), *Behavior Research Methods* 51(4), 1849–1863 | 4,436 concepts |
| `github.com/doomlab/Word-Norms-2`, `4 analysis/final words 2017.xlsx` | 7,173,768 bytes |
| sha256 | `6e1fc087986d5657684e190c2c04bd5a2c40f1d39b78eebb0ead8bb5e2225337` |
| held at | `~/word-norms-2/` — outside the repo, not redistributed |

Parsed with `zipfile` + `re` (an `.xlsx` is a zip of XML), no pandas and no openpyxl: 69,284 data
rows, 4,436 distinct cues, of which 4,411 are single words — the other 25 are sense-disambiguated
(`bat_animal`, `bat_baseball`). 2,585 single-word cues carry ≥ 12 features and 1,405 carry ≥ 16.
**Those four counts reproduce R052's measurements exactly**, which is the check that this is the
same file read the same way.

The feature identity used is the raw `feature` column, not `translated`: `translated` collapses
production variants and leaves only 878 cues at ≥ 12 features against 2,585 on `feature`, and
R052's measured numbers came from `feature`. Which column defines a feature for the **decisiveness**
statistic is a separate question and is left to step 2 — it changes the sharing counts (on `feature`,
elephant's rarest are `trunks` shared by 1 cue and `tusk` by 2, against the brief's `trunk` by 3).

## The rules as implemented

Applied in order, each counted so the attrition is visible:

- **F1** `pos_cue = noun` in the norms *and* the cue has a WordNet noun sense → 3,072 cues.
  `pos_cue` is unanimous per cue, so this is the norms' own judgement, not ours: `rake` is normed
  65/65 rows as a verb, so its features describe the action and it is correctly out of tools.
- **F2** the cue is its own WordNet base form → 2,957. Drops `arms`, `antlers`, `beans`: inflections
  of cues already in the pool, not separate concepts.
- **F3** ≥ 12 distinct features → 1,920.
- **F4** a noun sense inside the family's WordNet hyponym + instance-hyponym closure.
- **E2** no noun sense of the cue lies in **another** family's subtree. The existing rule — "a word
  naming a member of another bank family" — computed from the taxonomy instead of the hand-written
  `COLLISIONS` list, and recomputed per scenario because the family set changes. E2 always tests
  *all* senses: the prompt scan cannot tell senses apart.
- **E1** the answer-context form `' x'` is a single token under the frozen Qwen3.6 tokenizer
  (snapshot `c000ac2c…`), capitalised for countries. Unchanged from `build_concepts.py`.

One documented root synset set per family, chosen to match the family's ordinary meaning and not to
maximise a count: `animal.n.01`, `body_part.n.01`, `food.n.01`+`food.n.02`, `vehicle.n.01`,
`tool.n.01`, `musical_instrument.n.01`, `material.n.01`, `country.n.02`, `clothing.n.01`,
`furniture.n.01`.

**Two membership variants are reported**, because F4 on all senses admits members no reader would
accept — `bark` is a sailing ship, `secretary` a writing desk, `kettle` a kettledrum:

- **any-sense** — F4 exactly as written. This is the number the handoff asked for.
- **dominant-sense** — the cue's *first* WordNet noun synset must be in the subtree (WordNet orders
  senses by frequency), and cues in one family sharing that synset collapse to one concept
  (`ax`/`axe`, `bike`/`bicycle` are one concept, not two).

Both are mechanical and preregisterable. Dominant-sense is the conservative floor. Neither relaxes
an existing rule; the second only tightens F4.

## Eligible per family — the measured result

Counts from the *clothing* scenario for the seven retained families; the same families vary by at
most 3 across scenarios because E2 is recomputed. **Ceiling** is every single-word WordNet noun in
the subtree that passes E2 and E1 whether or not anyone has normed it — the most any human norm set
could ever supply — and the last column restricts that to dominant sense.

| family | any-sense | dominant-sense | ceiling | ceiling, dominant-sense |
|---|---:|---:|---:|---:|
| foods | 108 | 61 | 299 | 175 |
| materials | 67 | 32 | 306 | 197 |
| body parts | 68 | 35 | 255 | 129 |
| animals | 61 | 41 | 217 | 115 |
| clothing | **34** | **23** | 99 | 59 |
| vehicles | 32 | 21 | 94 | 53 |
| tools | **13** | **6** | 37 | **11** |
| instruments | **11** | **6** | 24 | **11** |

Measured in their own scenarios: **countries 12 / 9** (ceiling 146), **furniture 17 / 9**
(ceiling 34, dominant-sense 19).

`animals` loses more than half its pool to E1 (125 → 61): most animal names are multi-token.
It still clears 16 four times over.

## Countries: replace it, and the replacement is clothing

Countries yields **12** cues: australia, britain, china, egypt, england, france, japan, land,
mexico, north, russia, usa. Two of those (`land`, `north`) are not countries at all, and britain /
england / usa overlap as names of one another's territory, so the usable count is nearer 7.
Concrete-object feature norms do not contain countries, and the ceiling of 146 (128 dominant-sense)
shows this is a norms gap rather than a tokenizer one: the words exist, nobody has normed them. **Countries cannot be built from published norms.** Confirmed, as the handoff
predicted.

| candidate | any-sense | dominant-sense | ceiling | ceiling, dominant-sense |
|---|---:|---:|---:|---:|
| clothing | **34** | **23** | 99 | 59 |
| furniture | 17 | 9 | 34 | 19 |

**Clothing clears 16 more comfortably, on every measure.** Furniture clears the permissive reading
by one word, fails the conservative reading at 9, and its permissive list leans on oblique senses
(`press`, `secretary`, `lounge`, `box`). Clothing's dominant-sense 23 are ordinary garments:
attire, blouse, bra, clothes, coat, dress, gown, hat, hose, laundry, lingerie, mask, mitten, pants,
robe, scarf, shirt, shorts, sock, sweater, tie, underwear, vest.

The decision is R052's; this reports the measurement and does not make it.

## Tools and instruments cannot reach 16, and this is not a sourcing problem

Both fall short under every reading. What is lost, and to which rule:

- **tools** — 34 in subtree → 22 after E2 → **13** after E1. E2 removes `hammer` (also the malleus,
  a body part), `drill` (also a baboon), `screwdriver` (also a cocktail), `plane`, `comb`, `blade`.
  E1 removes `chisel`, `pliers`, `hatchet`, `scalpel`, `spatula`, `gavel`, `pitchfork` (2 tokens),
  `corkscrew`, `sledgehammer` (3). Survivors: ax, axe, bit, file, fork, hoe, knife, razor, saw,
  scissors, shovel, square, wrench — and `ax`/`axe` are one concept, so 12.
- **instruments** — 23 → 19 after E2 → **11** after E1. E2 removes `drum` (a fish), `horn`, `wood`.
  E1 removes `banjo`, `bugle`, `chime`, `clarinet`, `saxophone`, `trombone`, `tuba`, `woodwind`.
  Survivors include `instrument` (the category name), `kettle` (kettledrum) and `wind` (wind
  instrument); the clean set is accordion, flute, guitar, piano, trumpet, viola, violin, whistle.

Mixing in McRae (541 concepts) or CSLB (638) cannot close this. **The ceiling over the entire
WordNet subtree, after E2 and E1, is 11 for tools and 11 for instruments on the dominant-sense
rule** — the words a norm set would have to contain do not exist as single tokens. For tools the
whole list is ax, axe, hoe, knife, mower, razor, scissors, scraper, shovel, smoother, tamp; for
instruments accordion, bombard, flute, guitar, piano, piccolo, strad, trumpet, vibes, viol, violin.
Buchanan already norms most of the usable ones.

E1 is what binds. It is not a stimulus rule but a decode rule — the single-token answer form is what
makes the answer-position logit readable — so relaxing it is a protocol change with a cost, and it
is R052's to weigh, not ours. The handoff says not to relax a rule, and none has been.

## If tools and instruments are replaced, here is what clears 16

Every candidate measured against the five families that stand on their own plus clothing, one at a
time (the pair interaction through E2 was ≤ 3 words in the measured scenarios):

| candidate | any-sense | dominant-sense | ceiling | verdict |
|---|---:|---:|---:|---|
| buildings `building.n.01` | 22 | **16** | 68 | **clears 16 on both readings** |
| containers `container.n.01` | 30 | 15 | 98 | permissive only — and it cuts **vehicles to 12**, because car, truck and tank are containers in WordNet |
| furniture | 18 | 9 | 35 | permissive only, by two |
| weapons `weapon.n.01` | 13 | 9 | 35 | no |
| sports equipment | 9 | 0 | 24 | no |
| utensils `utensil.n.01` | 6 | 5 | 16 | no |
| toys `toy.n.01` | 3 | 1 | 6 | no |
| appliances `appliance.n.01` | 1 | 1 | 5 | no |
| trees `tree.n.01` | 0 | 0 | 18 | no — every normed tree cue also sits in foods or materials |

Buildings is the only measured alternative that clears 16 on both readings: barn, cabin, cafe,
castle, cathedral, chapel, church, convent, cottage, garage, grill, hospital, house, inn, lodge,
monastery, palace, restaurant, school, shed, building, court.

## What R052 has to decide

1. Confirm **clothing** replaces countries (or keep countries as a declared self-authored minority).
2. Choose the membership rule to preregister: **any-sense** or **dominant-sense**. Every family
   clears 16 on either except tools and instruments; dominant-sense costs nothing that matters and
   removes the `bark`-is-a-ship class of member.
3. Decide **tools and instruments**, where the options are: replace them (buildings is measured and
   clears; a second replacement needs one more measured candidate), drop to 6 families of 16, keep
   8 families at a smaller per-family count, or change E1 — which is a decode-protocol change.
4. Fix the feature identity for the decisiveness threshold (`feature` vs `normalized_feature`),
   since it moves the sharing counts.

Then §3 is amended from these numbers and step 2 (selection) can run.

## Licence

Unchanged from the handoff, and it gates publication rather than this build. The norms are held
outside the repo, are not redistributed, and nothing derived from them is published beyond our own
prose and a per-clause citation table. `pool_eligible.json` contains cue *words* and counts, no
feature strings. R052 is confirming reuse terms with the authors or the library.

NOVA (arXiv 2505.10718) was not used: LLM-augmented norms would reintroduce the circularity.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/norms_parse.py   # source counts
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/family_pool.py   # WordNet + E2
upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/pool_e1.py # E1, the table
```

`.venv-build` is a separate venv holding nltk 3.10.3 and WordNet 3.0. Neither nltk nor WordNet went
into `t1_access/.venv`, which stays version-pinned for parity. `pool_wordnet.json` is a regenerable
intermediate and is gitignored; `pool_eligible.json` is the committed measurement record.

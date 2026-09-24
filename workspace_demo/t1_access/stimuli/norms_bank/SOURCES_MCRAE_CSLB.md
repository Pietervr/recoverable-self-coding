# McRae and CSLB measured: the format is right, and five of the eight families cannot be filled

R084, 24 September 2026, answering R052's handoff f24ec33f. One pass, the pipeline already built for
Buchanan. Nothing selected, rendered or frozen; no clause rendered on Buchanan since the last report.

## The answer

**McRae's format is exactly what §3.1 assumes.** Its features are relational statements —
`has_a_trunk`, `lives_in_Africa`, `used_for_cargo`, `has_a_wooden_handle` — so rendering is
de-underscoring plus agreement, and the per-clause citation is real. It also ships the authors' own
cue validity per feature, which is the statistic Buchanan could not supply.

**But the concepts are not there.** McRae and CSLB are sets of concrete *object* concepts. Measured
against the eight families of §3.1, and counting CSLB generously:

| family | McRae eligible | + CSLB-only (upper bound) | pooled upper bound | needs 16 |
|---|---:|---:|---:|---|
| animals | 29 | 23 | **52** | clears |
| foods | 14 | 26 | **40** | clears |
| vehicles | 15 | 12 | **27** | clears |
| clothing | 11 | 3 | 14 | **short** |
| body parts | 0 | 9 | 9 | **short** |
| materials | 2 | 7 | 9 | **short** |
| buildings | 6 | 1 | 7 | **short** |
| occupations | 0 | 0 | **0** | **short** |

**Five of eight cannot reach 16**, and the CSLB column is an upper bound that the ≥ 12-feature
filter can only reduce. Occupations is zero in both sets, because neither norms people.

Stopping here as instructed. No fourth source was looked for, and nothing is proposed about E1, the
family list or the clause count.

## McRae: the file, and how the relation is encoded

| | |
|---|---|
| McRae, Cree, Seidenberg & McNorgan (2005), *Behavior Research Methods* 37(4), 547–559 | 541 concepts |
| `McRae-BRM-2005.zip`, Psychonomic Society web archive via Springer | 483,471 bytes |
| zip sha256 | `eb36b4c88f85141a226879ef2fdddc8075b9d35705fd27344c3a414eb56430a3` |
| data file | `McRae-BRM-InPress/CONCS_FEATS_concstats_brm.txt` |
| file sha256 | `fe796831232b164635c258095749320665c18c40186778e8d8baf4b0c4cdba23` |
| held at | `~/word-norms-mcrae/` — outside the repo, not redistributed |

7,259 rows over 541 concepts (516 single-word), 2,432 distinct feature statements, every feature
given by at least 5 of 30 participants. Features per concept: min 6, median 13, max 26; 363
concepts carry ≥ 12.

Each row gives the feature, a relation type (`BR_Label`), the production frequency, and
**`CV_No_Tax`, the authors' own cue validity** — P(concept | feature) over the non-taxonomic norms.
Relation types across the set: function 794, encyclopaedic 739, visual-form_and_surface 543,
taxonomic 207, visual-motion 95, sound 55, tactile 39, visual-colour 35, taste 12, smell 7.

Real entries, exactly as the file hands them over:

```
elephant  has_a_trunk          prod_freq 23   shared by   1   CV 1.000   visual-form_and_surface
elephant  lives_in_Africa      prod_freq 18   shared by   7   CV 0.194   encyclopaedic
elephant  is_large             prod_freq 29   shared by 101   CV 0.027   visual-form_and_surface
elephant  used_in_circuses     prod_freq  8   shared by   5   CV 0.170   function
truck     used_for_cargo       prod_freq 19   shared by   5   CV 0.213   function
truck     requires_drivers     prod_freq 14   shared by   5   CV 0.171   encyclopaedic
truck     has_18_wheels        prod_freq  5   shared by   1   CV 1.000   visual-form_and_surface
cow       beh_-_produces_milk  prod_freq 21   shared by   2   CV 0.553   visual-motion
cow       has_an_udder         prod_freq  8   shared by   1   CV 1.000   visual-form_and_surface
cow       lives_on_farms       prod_freq  8   shared by  12   CV 0.069   encyclopaedic
```

**This is the number R052 asked for: how much rendering is left.** `has_a_trunk` → "has a trunk";
`used_for_cargo` → "is used for carrying cargo"; `lives_on_farms` → "lives on farms". The predicate
is given, the relation is given, and what remains is agreement and padding to the 8–14 token window
— not the invention of a relation. Compare Buchanan, where `leather` + `cow` left the renderer to
decide between made from, comes from and found near.

Attrition through the pipeline: F1 (noun with a WordNet noun sense) 514, F2 (base form) 494,
F3 (≥ 12 features) 343, then dominant-sense family assignment, E2 and E1 give the column above.

## CSLB: gated, so measured at concept level only

**The norms are not downloadable.** `cslb.psychol.cam.ac.uk/property-norms` states that access is by
request to `csladmin@csl.psychol.cam.ac.uk`; there is no public file and the page states no licence
terms. That request is an outward-facing action and is not mine to send.

What *is* public is the concept list: the appendix of Devereux, Tyler, Geertzen & Randall (2014),
*Behavior Research Methods* 46(4), 1119–1127, as Springer electronic supplementary material
(`13428_2013_420_MOESM1_ESM.docx`). It gives all 638 concepts, each with a CSLB category and a flag
for whether it is also in McRae. **416 of the 638 are McRae concepts; 222 are new.**

CSLB's own categories, which is the clearest statement of what the set is:

```
misc 81 · land animal 59 · clothing 37 · bird 36 · vehicle 34 · tool 31 · vegetable 29
fruit 28 · food 27 · invertebrate 27 · music 24 · container 20 · furniture 20 · weapon 19
appliance 16 · sea creature 16 · flower 15 · kitchenware 15 · toy 15 · body part 14
fish 14 · water vehicle 14 · drink 10 · reading 9 · tree 9 · drug & cosmetic 8
footwear 5 · building 3 · jewellery 3
```

**There is no occupation category at all**, body part is 14 before any filter, and building is 3.
The paper says why: *"we aimed to replicate the McRae norms as much as possible, and so we included
all concepts from that set that were applicable to a British English environment"*, with additions
from the Snodgrass and Vanderwart picture set and from high-concreteness MRC items. It is the same
kind of set, extended.

The nine CSLB-only concepts that would join body parts are arm, ear, eye, finger, foot, nose, organ,
thumb, toe; the seven for materials are aspirin, eucalyptus, fir, glue, hyacinth, sycamore, tobacco;
buildings gains castle; occupations gains nothing.

## Do the two formats reconcile? Yes

McRae writes `has_a_wooden_handle` and `is_grey`; CSLB writes the same kind of statement with spaces
— the paper's own examples are *"has four wheels"*, *"is green"*, *"is absorbent"*, *"does absorb"*,
*"is a bird"*, *"is furniture"*. Both are relational feature statements with a does/is/has frame;
McRae additionally tags a relation type and CSLB normalises variant wordings onto one label.
Pooling them is a matter of normalising the separator and reconciling the two concepts' labels,
which the CSLB appendix already provides via its `McRae label` column. **Pooling is not what fails
here — coverage is.**

## Do the new §3.1 rules change any count? No, and a different rule is needed

The derivational-merge rule (shared Porter2 stem or WordNet `derivationally_related_forms`) and the
brand-name exclusion were written for Buchanan's single-word features, where `elmer`/`elmers` and
`stiff`/`stiffen`/`stiffener` were the problem. **McRae has neither pattern**: its features are
multi-word statements and it carries no brand names of that kind, so neither rule moves a single
McRae count.

McRae has its own duplication, of a different shape — **subsumption**, where one feature's words are
a subset of another's:

```
elephant   has_legs / has_4_legs      has_ears / has_large_ears     beh_-_eats / beh_-_eats_peanuts
cow        has_legs / has_4_legs      beh_-_eats / beh_-_eats_grass
truck      has_wheels / has_4_wheels / has_>_4_wheels / has_18_wheels
```

70 subsumption pairs across the 77 eligible concepts, 33 concepts affected. A stem-based rule does
not catch these. If McRae is adopted, the merge rule needs restating as subsumption over the
feature's word set. CSLB's paper reports the same issue in its own set (*"is absorbent and does
absorb"*) and says it collates variants to reduce it.

Note also that McRae's taxonomic features are family words by construction — `an_animal`, `a_mammal`,
`a_vehicle`, `a_tool` — so rule F removes them from every concept that has them, and `CV_No_Tax` is
blank for exactly those rows.

## Licence

**McRae** ships a terms-of-use file: the Psychonomic Society archive grants *"non-commercial use of
the materials by other researchers or educators, with the stipulation that any publications or
presentations that are facilitated by such use will cite both the originating article and the web
materials that were downloaded."* Two things follow. Citing per clause satisfies it directly, and we
are already not redistributing. But **the non-commercial stipulation does not sit inside a CC BY 4.0
data release**, which permits commercial use — so the norms must stay outside the released data, as
the current position already has them. Flagged for R052 rather than decided here.

**CSLB** states no licence on its access page; terms would arrive with the data if it is requested.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/mcrae_parse.py
SOURCE=mcrae t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/family_pool.py
SOURCE=mcrae upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/pool_e1.py
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/pool_sources.py
```

The McRae archive and the CSLB concept list live in `~/word-norms-mcrae/`, outside the repo and not
redistributed. `pool_eligible_mcrae.json` and `pool_sources.json` are the committed measurement.

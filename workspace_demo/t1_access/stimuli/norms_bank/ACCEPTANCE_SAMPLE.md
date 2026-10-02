# The naming-acceptance rate on relational clauses: 12 of 30 pass, and the route's 104 becomes about 42

R084, 2 October 2026, answering R052's handoff 74c6bba1. A seeded development sample of the four-family route was
selected, rendered and put through §3.1's two-sided naming acceptance exactly as declared. Nothing is selected
into the bank, rendered into it or frozen. Script `acceptance_sample.py`, results `acceptance_sample.json`.

## The answer

**12 of 30 concepts pass: 40 %, exact 95 % interval 23–59 %.** If that rate holds across the route's pool, its
104 usable concepts become **about 42 (24–62)**, and 113 with rule T narrowed becomes about 45. The four-family
minimum is 100. **The route does not survive acceptance**, and the shortfall is not close: no reasonable reading of
the interval reaches it.

| | pass | rate (95 %) |
|---|---:|---|
| overall | 12 / 30 | 0.40 (0.23–0.59) |
| McRae | 10 / 22 | 0.45 |
| Feats | 2 / 4 | 0.50 |
| Hovhannisyan | 0 / 4 | 0.00 |
| animals | 3 / 8 | 0.38 |
| foods | 3 / 8 | 0.38 |
| vehicles | 5 / 7 | 0.71 |
| clothing | 1 / 7 | 0.14 |

The by-source and by-family cells are small, so their intervals are wide (clothing 0.004–0.58, for example) and
they should be read as direction, not estimates. The failures split **13 floor, 5 ceiling, 0 both**.

## What failed, and why

**The floor failed most often (13).** The concept was not named from eight clauses on all three draws. The
reader's answers are mostly a **near neighbour**: hawk→eagle on all three draws, chick→bird, pie→pizza,
pickle→cucumber, robe→towel, convertible→car, and cricket→grasshopper once. **Six of the thirteen were named on two
of three draws** (bear, cricket, cabbage, wine, dress, scarf), so the all-three rule is what fails them.

One floor failure is a **scoring artifact**, not a clause problem. *bike* was answered "Bicycle" on all three
draws. McRae's *bike* features describe a bicycle, but the surface-form match counts only bike/bikes. WordNet's
dominant sense of *bike* is the motorcycle (`ROUTE_FOUR_FAMILY.md`), so the concept's identity was already
unsettled.

**The ceiling failed less often (5): monkey, pizza, jacket, hose and pants**, each at exactly 3 of 10 clauses
named alone. All five then passed the floor on 3 of 3 draws. These are concepts with a third decisive feature,
not unnameable ones.

**What each side of the criterion costs**, as information for R052 and not a proposal:

| acceptance rule | pass | rate (95 %) | of 104 | of 113 |
|---|---:|---|---:|---:|
| as declared: ≤ 2 alone, named on 3 of 3 draws | 12 | 0.40 (0.23–0.59) | 42 | 45 |
| floor at 2 of 3 draws | 18 | 0.60 (0.41–0.77) | 62 | 68 |
| ceiling at ≤ 3 alone | 17 | 0.57 (0.37–0.75) | 59 | 64 |
| both relaxed | 23 | 0.77 (0.58–0.90) | 80 | 87 |

**Even with both sides relaxed and rule T narrowed, the point estimate is 87 against 100.** Only the top of that
interval (about 102) touches the minimum. On this evidence the route cannot fill the bank under any variant of
§3.1's acceptance.

## The reader is part of the measurement

The floor depends on how good the reader is at naming, and this reader is an 8-billion-parameter model. Its
floor misses are plausible confusions between close neighbours. A stronger reader would very likely name more of
them, so **the acceptance rate is a property of the clauses and the reader together, not of the clauses alone**.
§3.1 fixes that the reader is never the model under test, but not how capable it must be. That makes the bank's
size depend on a choice the protocol has not made, and it is R052's to make.

**Reader and exposure, as required.** ollama `llama3.1:8b` (Meta, Q4_K_M, digest `46e0c10c039e`), temperature 0,
seed 20260924 — the materials trial's reader. Every call is stateless, with no context carried between calls. The
R2 audit pass was Codex (OpenAI), not this model, so this reader has no R2 exposure. Its only earlier use was the
materials trial (leather, shampoo, card, marble), and none of those is in this sample. Exposure through its
training data cannot be known.

## Hovhannisyan's photo-conditioned features, counted

All four Hovhannisyan concepts failed the floor (cricket, chick, wine, convertible). **By my reading, 4 of their
40 clauses describe the pictured exemplar rather than the concept.** Three are *wine*'s "is made of glass" (its
most-produced feature, 18 productions), "has a cork" and "has a label", which describe the photographed bottle.
The fourth is *convertible*'s "is red", the colour of the car in the photo. I did not count *wine*'s "is red" and
"is white" or *chick*'s "is yellow": those are true of the concept's ordinary kinds. This is one reader's
judgement on 40 clauses, recorded as such.

The larger problem with these four is weaker than misdescription: their features are generic. "It has legs",
"It is small" and "It is loud" for *cricket* name a table, a button and a siren. Hovhannisyan has no CV, so its
ten clauses are spread over production counts, which do nothing to favour distinguishing features.

## How the sample was built

- **Seed 20261002.** Quotas are 8/8/7/7 across animals, foods, vehicles and clothing. The source split is
  McRae 22, Feats 4 and Hovhannisyan 4, in proportion to the pool's 77/13/14. Each source's count is spread
  across families by largest remainder on that source's own family mix, and McRae fills every family to its
  quota. Concepts are drawn within each (family, source) cell by a derived seed. The 30 concepts are listed in
  `acceptance_sample.json`.
- **Selection.** Each concept's usable features (rules T F N X P D) are ranked by its source's heuristic, labelled
  per concept: published CV (McRae, Feats), or raw production count (Hovhannisyan: no CV, no denominator). Ten are
  taken at evenly spaced positions over that order.
- **Rendering.** The feature's own words with "It" as subject: "It has a trunk", "It eats peanuts", "It is used
  for cargo". The only authored words are a declared connective for verbless frames ("It comes in" for
  different_…). Nine of the 300 clauses use one. No padding to §3's 8–14 token window was attempted.
- **Records.** The clause text and its provenance row are in the gitignored `acceptance_sample_detail.json`,
  because they hold feature labels. The committed JSON has the sample, every reader answer, every verdict and the
  rates.

## A conflict in the brief, for R052

The brief asks that the sample not be used in CAL, PILOT or CONF afterwards. **At this pool size that is not
possible.** The route has 104 concepts and 96 target roles, so at most 8 can stay outside the target roles, and
excluding 30 would leave 74. The measurement reads only the reader model, never the model under test. Running
acceptance on these concepts early is the build's own acceptance step done in advance, which does not breach
§3's rule against selecting on the model under test. Whether sampled concepts may later take roles is R052's
call, though the acceptance result above makes it moot for this route.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/acceptance_sample.py   # 390 reader calls, ~10 min
```

# Codex's no-CSLB route under §3.1's full rules: four families at ten clauses reach 104, four above the minimum

R084, 2 October 2026, answering R052's handoff 203c6169. The route is Codex's (RSC d6bdbc4): McRae + Feats +
Hovhannisyan et al. (2021), with clothing as a fourth family. It is measured here under the **same** rules as the
51 / 77 in `CLEAN_ELIGIBILITY.md` — rules T F N X P D, dominant sense, E2 then E1, single-token answers — so the
15 October choice compares like with like. Nothing is selected, rendered or frozen. Script
`route_four_family.py`, counts in `route_four_family.json`.

## The answer

| usable concepts, single token, §3.1 full rules | twelve | ten | needed |
|---|---:|---:|---:|
| (a) McRae + Feats, three families (control) | 51 | 77 | 99 |
| (b) + Hovhannisyan ≥ 3, three families | 52 | 89 | 99 |
| **(c) + Hovhannisyan ≥ 3, four families (clothing)** | 62 | **104** | **100** |
| (c) with rule T switched off | 80 | 113 | 100 |
| (c) sensitivity, Hovhannisyan ≥ 5 | 61 | 90 | 100 |

**(c) at ten clauses fills the four-family minimum of 100 with four to spare**: animals 43, foods 26, vehicles 20,
clothing 15. A joint integer allocation exists. With two backgrounds per family (104 needed) it fits exactly, with
no margin. The control row reproduces 51 and 77 exactly, so the rules did not move between measurements.

**No family binds; the total does.** Every family can lose four concepts before the allocation fails, and not
five. That is the aggregate margin of four, not a half-bound or a family running dry. Clothing, at 15, is the
smallest family but still has room for every split plus a background.

**Nothing else in the table reaches the bank.** Twelve clauses fail under every row, at best 80 with rule T off.
At Hovhannisyan's sensitivity cutoff of ≥ 5 the route gives 90 and fails. Three families without clothing reach 89.

## What the margin of four is made of

The 104 by source: McRae 77, Feats 13, **Hovhannisyan 14** (7 animals, 3 foods, 2 vehicles, 2 clothing). Take
Hovhannisyan away and the four-family pool is about 90, as the ≥ 5 row shows. **The route therefore rests on 14
concepts whose features were elicited on a photograph**, at an absolute production cutoff with no per-concept
denominator and no published CV — the three gaps `hovhannisyan_parse.py` labels on every row.

**The margin is counted before naming acceptance.** §3.1's two-sided acceptance — at most two of ten clauses named
alone, and the concept named from eight clauses on all three seeded draws — can only remove concepts. Four is the
whole allowance for that, and for any concept the build passes over. The materials trial measured acceptance
only on authored Buchanan clauses, so it says nothing about the rate on McRae's relational features. The honest
statement is that the route fills the bank on count, with no measured room for acceptance attrition.

**Rule T, priced on this pool: 9 concepts at ten (104 → 113) and 18 at twelve (62 → 80).** Narrowing it to
literal family words would turn the margin of four into thirteen. That is R052's decision.

## The sources, read under the same discipline as McRae and Feats

`hovhannisyan_parse.py` reads `featurematrix.csv` (995 concepts by 5,520 relational features, integer production
counts). Each feature's relation label comes from the authors' own `fullList` sheet of
`conceptFeatureLabelList.xlsx`, in McRae's scheme. **Rule T therefore uses the source's own `taxonomic` label, not a
frame proxy**, and every retained feature has one. All three files match Codex's SHA-256.

The source is third in priority, McRae > Feats > Hovhannisyan, on exact labels. The loader **asserts** Codex's
overlap figures: 995 labels, 327 overlapping McRae + Feats, 668 new, 404 passing the alphabetic guard. The pool
holds 1,128 single-word concepts.

**Three gaps, labelled on every provenance row and never imputed:**
- **No denominator.** Inclusion is an absolute ≥ 3 productions, not the one-sixth prevalence McRae and Feats use.
  Concepts had at least 20 respondents, mean 30.5, but the release gives no per-concept count.
- **No CV.** Features would be ranked by raw production count, labelled as such.
- **Photo-conditioned.** A feature may describe the pictured exemplar rather than the concept.

The data's own reuse terms are an open metadata gap: the article is CC BY 4.0, but the GitHub tree and the OSF node
carry no licence (Codex). This is recorded here, not resolved.

**Clothing** is the fourth family, rooted at `clothing.n.01`. E2 tests every candidate against all four subtrees.
Rule F's family words gain *clothing* and *clothes*, and rule X's name ban is recomputed over the four-family
candidate set. The 15 clothing concepts are blouse, bra, coat, diaper, dress, gown, hose, jacket, mask, mitten,
pants, robe, scarf, shirt and tie.

WordNet's dominant sense of *bike* is the motorcycle, so *bike* and *bicycle* count as two vehicles. The rule is
applied as declared, and the duplication is visible here.

## Allocation, for any number of families

The joint integer check is now a max-flow with lower bounds. Every split holds every family at least once and at
most half the split, role totals are disjoint, and backgrounds are reserved first. It agrees with the exhaustive
three-family check on all 308 triples tested. One feasible witness for (c) at ten is CONF 32/23/8/1, CAL 8/1/6/1,
PILOT 2/1/5/8, BACKGROUND 1/1/1/5. It is a feasibility proof, not a proposed allocation: the build allocates by
seed.

## Reproducing

```sh
cd ~/Recoverable-Self-Coding/workspace_demo
upstream/jlens-qwen36/.venv/bin/python t1_access/stimuli/norms_bank/token_counts.py      # 1,128 cues, pinned tokenizer
t1_access/.venv-build/bin/python t1_access/stimuli/norms_bank/route_four_family.py      # every row above
```

Hovhannisyan stays outside the repo in `~/word-norms-hovhannisyan/`. `route_four_family.json` holds counts, cue
words, allocations and digests only, with no feature labels.

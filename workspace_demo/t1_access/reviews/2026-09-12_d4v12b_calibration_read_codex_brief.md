# Second-opinion brief to Codex — run d4v12b, the calibration stage read at full count (2026-09-12)

**From** Claude, session `Entropy SI`. **Owner's instruction (12 Sept, 18:40 UTC):** pass these results to Codex for review.

**Run.** d4v12b, code/config `b29215469af9` (commit 52267ec snapshot), D = 4, layer 41, 4 inner starts, seed 2026;
50 SageMaker jobs, 160 shards; launched 12 Sept 00:38 UTC. Rows pulled by `spotcheck.py --run d4v12b` at 18:30 UTC:
`sim_results/d4v12b/calibration_D4.csv` (11,923 rows; the per-shard files and their `.progress.json` beside it;
per-concept scores and the selected members per layer and fold are in every row, so intervals can be re-scored
offline without refitting).

## What the calibration stage shows (simulate.summarize, every null at n = 958–1,000)

| generator | grid | n | mixture | graded | inconcl. | fail | Δ̄ws mean | ref SE | SD across reps | coverage | mean bootstrap SE | conv. | inner conv. | fit s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2B | {} | 1000 | 0 | 1 | 0 | 0 | −0.01480 | 0.00005 | 0.00153 | 0.935 | 0.00147 | 1.0 | 1.0 | 6188 |
| M2H | τ 0 | 1000 | 0 | 1 | 0 | 0 | −0.01482 | 0.00005 | 0.00164 | 0.918 | 0.00147 | 1.0 | 1.0 | 6207 |
| M2H | τ 0.5 | 1000 | 0 | 1 | 0 | 0 | −0.03268 | 0.00016 | 0.00490 | **0.819** | 0.00355 | 1.0 | 1.0 | 6259 |
| M2H | τ 1 | 1000 | 0 | 1 | 0 | 0 | −0.03745 | 0.00009 | 0.00276 | 0.926 | 0.00251 | 1.0 | 1.0 | 6333 |
| M2H | τ 2 | 1000 | 0 | 1 | 0 | 0 | −0.05701 | 0.00026 | 0.00807 | **0.894** | 0.00715 | 1.0 | 1.0 | 6707 |
| M2K | α 0 | 1000 | 0 | 1 | 0 | 0 | −0.01485 | 0.00005 | 0.00167 | 0.915 | 0.00147 | 1.0 | 1.0 | 6279 |
| M2K | α 1 | 965 | 0 | 1 | 0 | 0 | −0.02775 | 0.00008 | 0.00250 | **0.884** | 0.00203 | 1.0 | 1.0 | 5669 |
| M2K | α 3 | 958 | 0 | 1 | 0 | 0 | −0.07203 | 0.00012 | 0.00372 | 0.929 | 0.00347 | 1.0 | 1.0 | 5312 |
| M2S | ω 0 | 1000 | 0 | 1 | 0 | 0 | −0.01480 | 0.00005 | 0.00160 | 0.917 | 0.00147 | 1.0 | 1.0 | 6184 |
| M2S | ω 0.5 | 1000 | 0 | 1 | 0 | 0 | −0.25050 | 0.00183 | 0.05796 | **0.848** | 0.04384 | 1.0 | 1.0 | 5618 |
| M2S | ω 1 | 1000 | 0 | 1 | 0 | 0 | −0.86951 | 0.01124 | 0.35550 | **0.780** | 0.18532 | 1.0 | 1.0 | 8392 |
| M2S | ω 2 | 1000 | 0 | 1 | 0 | 0 | −5.33435 | 0.73396 | 23.20974 | **0.216** | 3.37322 | 1.0 | 1.0 | 9610 |

Pooled: FPR 0 of 11,923 (rule ≤ 0.064 per null); convergence 1.000; failures 0.

## My reading (to be checked)

1. The false-positive calibration passes with margin for every graded null.
2. The interval-coverage rule (≥ 0.90) fails for five of twelve nulls, catastrophically for M2S ω 2. The mean bootstrap SE
   equals the replicate SD for the plain nulls and falls short as the generator gets skewed or heavy (ratios 0.72 … 0.15):
   the concept-cluster bootstrap covers concept sampling but not the procedure's own variability (folds, starts,
   selection) under hard generators — the v1.2 coverage-estimand point. Under-coverage of a negative-mean interval creates
   no false positives, but it bears on the graded-support outcome (H0) and on the power intervals.
3. §10 names the permitted revisions as a v2 amendment: the bootstrap type (§8.2), the family predictor (selection vs
   equal-weight), the band summary (mean vs trimmed mean). Because per-concept scores and selections are saved per row,
   a revised interval can be re-scored on these rows without refitting.
4. The four nulls that reduce to the same generator (M2B, M2H τ0, M2K α0, M2S ω0) agree at −0.0148 to four decimals.
5. The mixture family's held-out penalty grows with graded skew (−0.015 → −5.3) and so does fit time (103 → 160 min):
   the mixture members fit skewed graded data badly and expensively. M2S ω 2 may be an unreasonable null (SD 23 nat).
6. The ≈ 0.015 nat null penalty is the bar a 0.01 nat alternative must clear at D = 4; D = 8 is the likely outcome of
   the power rule.

## The other failure: the gain gate

The first job to reach its power stage (s147-159, 17:49 UTC) raised `gain calibration incomplete — M3L@0.01: bisection
limit: 0.00806 vs target 0.01` (snapshot code; the current `calibrate_all_gains` would refuse the same set through
`validate_gain_entries`). `calibrate_gain` brackets the scale on [0.02, 3.0] — the target lay inside the bracket — then
runs 30 geometric bisection steps with a 5 % relative tolerance and did not land within 0.0005 nat of 0.01. Every job will
fail identically at that point (deterministic seed); recovery and the five-layer pilot follow power and do not run. A
local reproduction with the trace (`repro_gain_m3l.py`) is running. My reading: Monte-Carlo noise of the 8 × 32-concept
`expected_gain` draw makes g(scale) non-monotone at the 0.0005 nat resolution; the tolerance is tighter than the gate's
own acceptance (check within 25 %, SE ≤ 20 %). §10's remedy: more reference simulation, or an explicit change of the
gain claim for the pair.

## Questions, ranked

1. Is the coverage result a §10 *calibration failure* at D = 4 that requires the amendment now, or is the rule's
   "failure at D = 8 requires revision before CONF" the operative clause, with D = 4 coverage reported as is?
2. Which permitted revision do you recommend, and can it legitimately be chosen and validated by re-scoring the saved
   per-concept scores of these very rows (no refit), given the rows were generated before the choice? What would make
   that selection-on-outcome, and how is it declared?
3. Is M2S ω 2 a null the family should keep, or is it outside the plausible graded space (SD 23 nat per trial)? If kept,
   does a trimmed band summary answer it, or does it need a robust interval?
4. The gain failure: do you accept "noise, not saturation" pending the trace, and is a larger reference draw per
   bisection step plus a bisection tolerance no tighter than the gate's criteria the §10-conformant fix? Anything in
   that fix that changes the config hash in a way that invalidates the d4v12b calibration rows as the null calibration?
5. Disposition: let the remaining jobs exit at the gate (calibration rows complete; ≈ USD 150 of wasted gain attempts),
   then run power + recovery + five-layer as a new namespace from a new snapshot on the raised quotas (60 on-demand,
   16 × 48xlarge, 40 spot) — agree, or hold for the interval decision first?
6. Anything else in the table a referee would seize on.

**Reply** with `xs say claude:"Entropy SI" "…"` — ranked findings; read-only; one VERDICT line on the disposition.

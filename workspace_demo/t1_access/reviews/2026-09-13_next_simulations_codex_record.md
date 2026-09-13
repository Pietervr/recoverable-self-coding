# Codex second opinion — next T1 simulations, 13 September 2026

Reply to `2026-09-13_next_simulations_codex_brief.md`, from session `Entropy SI`.
Reviewed RSC at `e8d7b4c`, the draft pre-registration, the running probe's code and launch log,
`models.py` fitting/start generation, `analyze.py`, the relevant simulation paths, the landed
12,000 calibration rows, and `Unimog-Projects/project_knowledge/rsc_t1_simulation_design.md`.
The PC audit's counts below come from the brief and that owning document; its raw per-start
archive is on the PC and was not independently inspected here. No fits or simulations were
launched, stopped, or modified by this review. No cloud action was taken.

**Verdict:** on board with the current Mac probe as method development, with the reporting
corrections below. Prefer option (i), a fixed richer start recipe for every member, with counts
chosen against the audit and checked on fresh cases. On board in principle with separating
the mixture test from an expensive uncertainty interval. **Not on board with the cloud ladder
as written:** its critical values would describe the old one-layer fitter, its proposed cutoff
can be negative, its finite-simulation guarantee is misstated, and its prices omit the new
fitter and the band-level work. The next funded stage should be designed after the fitter
benchmark and a small point-statistic screen, not committed now to a $1,840 interval stage.

The system being assessed is a nested, concept-disjoint predictive comparison. Its point
statistic is the selected mixture family's held-out log-score advantage over the selected
graded family. The current hypothesis requires a positive interval; a simulation-calibrated
test is a different decision procedure, even when it uses the same point statistic. The
gain artefact defines alternative generators; it does not establish this procedure's power.

## 1. Keep the Mac probe; change how its result is assessed

**Keep 20 datasets × 50 refits at each of the two settings.** That allocation can reveal a
large change at M2S omega 2. It is not enough to distinguish coverage 0.90 from nearby values,
and evidence at omega 1 will be less decisive. Do not switch to 40 × 25: the tails of a 95%
percentile interval become too poorly resolved. Ten × 100 improves each interval's numerical
resolution but leaves only ten independent datasets for the question of coverage. The current
allocation is a defensible screening compromise, not an established optimum.

The two uncertainty sources must be kept separate:

| Refits B | Expected draws in each 2.5% tail | Probability of no draw in a specified tail |
|---|---:|---:|
| 25 | 0.625 | 0.531 |
| 50 | 1.25 | 0.282 |
| 100 | 2.5 | 0.080 |
| 200 | 5 | 0.0063 |

These are binomial calculations for independent draws from a continuous bootstrap law, not
coverage predictions. At B=50 the code's lower endpoint interpolates between the second and
third ordered values. Thus B=50 can obscure a promising method through endpoint noise; a
negative screen does not establish that the B=200 method cannot work. The code uses NumPy's
default linear percentile convention, which should remain explicit in the record.
[NumPy percentile documentation](https://numpy.org/doc/stable/reference/generated/numpy.percentile.html).

At R=20, coverage 18/20 has an exact two-sided 95% binomial interval of approximately
[0.683, 0.988]. Even 20/20 has a one-sided 95% lower limit of only 0.861. These counts cannot
certify the 0.90 gate. They can motivate the next development step.

**The main correction is the reference target.** `simulate.summarize` (lines 317–351) takes
the mean of the same rows it is summarizing as `truth`. For this probe that is the mean of
only 20 datasets. Its reported coverage must not be treated as coverage against a known target.
Use an independent estimate of the unchanged procedure's expectation. The old point estimates
are eligible reference data only after confirming the procedure's numerical equivalence and
recording the cross-snapshot reuse; changing the interval alone does not change the point
statistic. The inspected `models.py` diff from the cloud snapshot only adds provenance hashing,
and the prior review records plain-analysis equivalence after the grouped-fold repair.

Recalculation from the complete old rows gives:

| Setting | Reference mean | Monte Carlo SE of that mean | Old coverage at mean − 2 SE / mean / mean + 2 SE |
|---|---:|---:|---:|
| M2S omega 1 | −0.869513 | 0.011242 | 0.739 / 0.780 / 0.819 |
| M2S omega 2 | −5.334354 | 0.733956 | 0.180 / 0.216 / 0.304 |

The omega-2 reference is itself imprecise: its median point statistic is −2.06555, and its
minimum is −418.54222. Report sensitivity of the probe's coverage across a reference range,
with the mean ± 2 Monte Carlo SE as a diagnostic range rather than a certified normal interval
for this heavy-tail target. More independent ordinary-pipeline reference rows are much cheaper
than bootstrapping every reference dataset. After a fitter amendment they must estimate the
amended procedure's target; the old mean is no longer that target.

**Use the paired comparison already available.** With `interval="refit"`, each row stores the
refit interval and its companion fixed-score cluster interval on the same original dataset.
Report both against the same independent reference, their coverage difference, widths,
bootstrap centers relative to the original point, failures, and tail-loss diagnostics. Comparing
the new 20-row refit rate only with the old 1,000-row cluster rate throws away that pairing.
Matched simulated data and explicit missing-estimate and Monte Carlo-error reporting follow
the practical guidance in [Morris, White and Crowther, §§4.3–5](https://arxiv.org/html/1712.03198v3).

**Control:** a control is not necessary to see a large gain at omega 2. It is needed to support
the more specific claim that refitting chiefly repairs the troublesome settings while having
little effect where coverage already works. Run a small M2B control, initially 10 × 50, on the
PC after the audit if it is available, with the same fitter and B. At the old benchmark this
is about 130 core-hours; it is still development. Do not let it delay the already-running probe.

**Seeds:** no objection to seed 2027 with the existing tuple-based `dataset_seed` rule. The
read-only check reproduced the 12,000 old and 40 proposed dataset seeds: all are distinct within
each bank and there is no overlap between banks. Record the top-level seed and derived seed
mapping with the run; select later validation seeds in advance. New seeds provide new datasets,
not validation of a method still being changed.

**Resample extension is not currently automatic.** B is part of the checkpoint identity, and
`stratified_resample` consumes RNG values family by family in arrays whose size depends on B.
Increasing B changes some earlier resamples as well as the identity. Do not relabel a 50-refit
checkpoint as B=100 or 200. A later endpoint-stability check needs either a separate correctly
identified run or an explicit, tested resample-manifest extension. Choose its dataset IDs before
looking for favorable outcomes.

Finally, coverage improvement would support using a different interval, not identify fitting
instability as the cause. The sample, resampled fits, inner selections, optimizer draws, and
effective training support all change together. The SD/mean-half-width ratio near 0.51 is a
normal-interval heuristic, not a diagnostic theorem for these heavy-tailed percentile intervals.
The categorical causal wording in simulation-design §6/§10 and pre-registration §10 should be
softened; the audit association and the bootstrap comparison leave tail sampling and interval
shape in play.

## 2. Prefer a fixed richer start recipe for all members

**Option (i) is the best development path.** Preserve the existing cold starts and add both
extra and challenge starts to every member, at both inner and outer fitting sizes. Select the
counts by the audit; do not run all 128 strong-search starts everywhere by default. A reasonable
first candidate to score from the archived starts is 4 inner / 8 outer cold starts plus 8 extra
and 8 challenge starts. Compare a second candidate with 16 of each added set. These are candidate
budgets to test, not approved final settings or guarantees of adequate optimization.

Option (ii) saves little by protecting only expensive members: the other members account for
about 5% of the current time, and the record includes a material M2K miss even though M2K is
cheap. Conversely, being expensive is not evidence that a member misses; M2S-as-fitted is
reported clean so far. Zero misses in a small audit does not establish a safe exemption. An
8-start audit also does not clear the actual 4-start inner fits. All-member counts may later
be made member-specific if fresh evidence supports it, but member identity and recipe must be
fixed before validation, with no knowledge of the generating family available to the fitter.

**Name the two batches accurately.** `simulate._extra_starts` uses jitter and mirrors skew
coordinates when present. `_challenge_starts` adds the ±2 skew-coordinate combinations only
for members that have `alpha*` parameters; otherwise it is independently seeded, wider jitter.
M3H has no such skew coordinates. “Six extra / six challenge discoveries in M3H” therefore does
not show that separated-skew starts helped M3H. It shows that both stochastic search batches
helped. This matters when turning the audit into an implementation recipe.

Use the per-start archive, if it retains every start's order and result, to compare fixed prefixes
of both batches without refitting anything. A winner-only summary is insufficient for this step.
Keep each candidate independent of which archived start happened to win. For each
candidate report, by generator, fitted member, and training size:

- best converged training-likelihood gap to the strong reference, including the worst cases;
- number of distinct starts reproducing the best-found basin, failure and nonconvergence counts;
- elapsed time, with the expensive members shown separately;
- downstream inner selections and held-out point-statistic changes on complete procedure checks.

Training-likelihood comparisons decide which solution is kept. Held-out synthetic scores reveal
the effect on the assay; held-out CONF scores must never select a start or trigger more search.
The strong reference is best-found, not a proven global optimum. A small average likelihood
gap can conceal the rare misses that matter here.

Use already-inspected audit cases for recipe development, then freeze the candidate and check
it on untouched, declared cases covering both families and both training sizes. Include actual
4-start inner baselines and representative bootstrap-resampled training sets. If all R=6 cases
have been inspected to choose the recipe, they are development data and a fresh check is needed.
R=6 is adequate to compare recipes across the designed cases, not to prove a rare-miss rate.

**Option (iii) is an optional challenger, not a substitute already supported by the gain run.**
Warm starts on a bisection path are useful because successive fits use the same training draw
at nearby scales. Pipeline folds do not have that relationship. Starts may come from fixed
CAL information or the current training subset. Reusing another outer-fold fit, or a parent
fit containing the current inner-held-out concepts, leaks held-out information. The basin-set
helpers also do not discover missing basins by themselves; discovery still needs a search.

Freeze the amended fitting function, start provenance, independent random streams, failure
policy, and timing before validating intervals or critical values. Preserve the old rows as
the old procedure's evidence. The accepted twelve-pair gain artefact need not be recomputed
merely because the point fitter changes if its generator and reference calculation are
unchanged; carry that reuse through an explicit compatibility/provenance record, not by
stamping a new hash on old calculations.

## 3. A point-statistic test is possible, but it changes the hypothesis test

A transparent, dated change before CONF is read is legitimate method development. The document
is still DRAFT v1.2. This goes beyond choosing a replacement bootstrap: amend H1, the outcome
table, §8.3, §10, the target-bridge comparison in §8.5(a), availability bookkeeping, and the
manuscript's “interval excluding zero” language together. H1-T(b), H2, and H3 have separate
interval requirements; this change does not validate or remove those.

Also specify the significance convention: the proposed upper-tail 0.05 test differs from
requiring the lower endpoint of a two-sided 95% interval to exceed zero. The existing empirical
FPR ceiling does not make those decision rules identical.

**First, do not transfer the existing critical value to a different procedure.** The old
12,000 rows are at D=4, one layer, four inner starts, eight outer starts, under the old fitter.
They can develop a candidate rule. They cannot calibrate an amended fitter, a changed D, or
the actual workspace-band statistic. One-layer quantiles do not become band quantiles by
averaging them or combining independent rows: layers share concepts and other latent draws.

**Second, the proposed cutoff is negative.** Directly from the complete calibration CSV:

- every one of the 12,000 selected point statistics is negative;
- the maximum of the twelve default 95th percentiles is **−0.012074637 nat/trial**;
- the maximum finite-rank cutoff at ascending order statistic 951/1,000 is **−0.012049858**;
- both maxima come from M2S omega 0, which is a base-equivalent graded setting.

Consequently a statistic of −0.010 would reject the proposed finite null benchmark while the
graded predictor still has the better observed log score. If “mixture support” is to retain
positive observed predictive advantage, require **T > max(0, c)**, where T is the frozen band
statistic and c is the calibrated upper-tail cutoff. This is stricter than merely rejecting
the simulated nulls. Its power must be measured; it cannot be inferred from the alternative's
positive oracle-reference gain. On the old rows this sign floor makes c effectively zero.

Even with the sign floor, rejection is a test against the declared generator benchmark plus
a positive observed statistic. It is not a 95% confidence statement that the procedure's
expected predictive advantage is positive over arbitrary stimulus distributions. Retaining
that latter claim requires a valid interval or another test of that estimand.

**Third, “exact at the tested nulls by construction” needs a precise meaning.** An empirical
95th percentile guarantees a property of the calibration bank, not the population rejection
rate of the realized cutoff. A finite Monte Carlo test can instead use

    p_j(T) = (1 + number of simulated T_jb >= T) / (m_j + 1)
    p_grid(T) = max_j p_j(T)

and require p_grid <= 0.05, alongside T>0. With a fixed procedure and exchangeability with
fresh calibration simulations at the true grid point, each p_j is valid; taking the maximum
preserves validity for the union of those grid points. With m=1,000 the single-point rank
test has size 50/1,001, about 0.04995, for a continuous statistic before the additional
conservative requirements. This controls error over calibration-bank and study randomness.
It does not guarantee a conditional 5% rate for every realized bank, and a finite grid does
not cover a continuum of nuisance parameters. See [Dufour, §2 and §4](https://jeanmariedufour.github.io/Dufour_1995_MCT_W.pdf).

For a fixed cutoff with a high-probability conditional guarantee, an order-statistic tolerance
bound is another choice. The calculations beside this record give rank 962/1,000 for at least
95% confidence that a point's upper-tail probability is <=0.05. Using rank 968/1,000 at each
of twelve points gives at least 95% simultaneous confidence by a union bound. These are
different guarantees from the rank test above, and generally cost power. Choose one guarantee
in the amendment rather than describing an ordinary percentile as exact. Both still require
fresh calibration after adaptive method development and the correct complete procedure.

My preference is the finite-rank Monte Carlo rule, with the grid scope and positive-score
requirement explicit, followed by an independent empirical check of the frozen rule. Fresh
validation is a practical check of the implementation and realized threshold; it is not what
creates the mathematical rank guarantee. Do not pool all 12,000 rows into one null law.

**Borderline and failure rules must be written before validation:**

- A point on the cutoff is not a rejection; do not move the cutoff, choose another seed, or
  choose another predictor after seeing CONF. Predeclare numerical tie handling.
- Failure to reject the graded benchmark is “no mixture support” or “inconclusive.” It is
  not automatically “graded support.” That needs a separately justified negative interval
  or a separately calibrated converse test. Power for the mixture test alone does not give
  the full four-outcome confusion matrix.
- If the interval is reporting-only, its failure is recorded separately from availability
  of a valid point test. If a usable interval or a positive lower endpoint still gates H1,
  the proposed point-only simulation no longer estimates the full H1 decision probability.
- Simulation estimates close to the FPR, coverage, or power thresholds remain unresolved at
  the prespecified count limit. Any extensions, decision boundaries, and treatment of repeated
  looks must be fixed in advance. The old 0.064 FPR tolerance was tied to R=1,000; do not
  apply it as though it has the same Monte Carlo meaning at R=50 or 100.

A refit interval may accompany the test as an uncertainty estimate, with its demonstrated
limitations stated. Moving it out of the test does not certify nominal coverage. At R=50,
45/50 coverage has a two-sided 95% interval [0.782, 0.967]; 48/50 still has a one-sided 95%
lower limit below 0.90. Three settings × 50 datasets × B=100 is a further screen, not validation
of a B=200 interval at every retained null and alternative.

## 4. The next runs and the budget

1. **Now, local:** finish the current probe and the PC audit. Analyze the probe with the paired
   intervals and independent target above. Add the small control when the PC is free. This
   review does not alter either running job.
2. **Next, mostly offline:** compare the two fixed richer-start candidates using the audit's
   archived starts, check a chosen recipe on fresh cases, then benchmark the actual amended
   inner/outer pipeline and refit resamples at the intended concurrency. Do this before another
   large coverage campaign.
3. **Then, a small local point-statistic screen:** start with 100 datasets per retained graded
   setting and 100 per mixture member at gain 0.01, one layer, using the frozen candidate fitter
   and candidate test. That is 1,600 ordinary pipelines with no refit intervals. For this small
   screen, declare null replicates 0–49 for cutoff construction and 50–99 for checking, with
   the 100 replicates of each alternative in a separate bank. This allocation is development
   and feasibility screening, not the final band validation. Inspect all four 0.01 alternatives
   first because they determine D. Defer 0.003/0.03 and the recovery expansion until that works.
4. **Only then cost the funded stage:** prioritize new calibration and power of the actual
   primary statistic, including its frozen layer grid and PILOT-based cross-layer structure.
   Reserve the cost of the real R1 and R2 fits/intervals. Decide whether more Mac time, credits,
   or an explicitly narrower pre-CONF design makes the remaining validation feasible. Do not
   spend most of the cap on a one-layer uncertainty screen while the primary decision's
   calibration is still missing.

The brief's prohibitive refit-power arithmetic is correct in scale: 612,000 core-hours for
the resamples alone, about 615,060 including one original pipeline per dataset at 15.3 minutes.
The reduced 12 × 200 × 50 design is about 31,212 core-hours including original fits. These
are old one-layer benchmark extrapolations; omega 1/2 and the amended starts need their own
timings.

| Item | Old-method cost basis | What must be added or established |
|---|---:|---|
| Current 40 × (1+50) probe | 520 core-hours; about 2 continuous Mac days at 11 workers | actual omega-1/2 timing; no cloud spend |
| Three-setting 50 × (1+100) interval screen | 3,863 core-hours; about $1,854 at the recorded conversion | amended fitter; this still covers only three settings and B=100 |
| Twelve point-only alternatives × 1,000 | about $1,900 from the old cloud run | fresh null calibration, amended fitter, actual band, new runtime benchmark |
| One B=200 interval across 35 workspace layers, R1 only | about 1,785 core-hours; 6.8 continuous Mac days or $857 equivalent | amended fitter; R2 roughly doubles it; other bands and analyses add work |

All dollar figures use the owner's **recorded planning conversion**, $0.48 per Mac-core-hour
equivalent, not a fresh AWS quote or an assurance about future throughput. There is no measured
single cost multiplier for the amended fitter. The proposed $1,840+$1,900 already exceeds
$3,000 before new null calibration or band validation. The 1,600-row local screen would be
about $256 cloud-equivalent at the old $0.16/row rate, multiplied by an as-yet unmeasured change
in fitting cost; it is not a cloud launch recommendation.

**Handoff:** local development can proceed. The three proposed cloud stages are not approved
as a package, and no replacement cloud stage is approved by this record. Bring back the frozen
start recipe, measured timing, exact revised outcome table and test, and a costed plan that
includes fresh null calibration and the actual layer statistic. The owner's separate launch
authorization remains required under the existing spending instruction.

## Reproducible checks

`2026-09-13_next_simulations_codex_checks.py` reads the existing calibration CSV and performs
ordinary arithmetic only: no project imports, fits, or simulations. Its output is
`2026-09-13_next_simulations_codex_checks.json`. It checks 12,000 distinct rows, one source hash
`b29215469af9`, one layer, D=4, no invalid original points, zero positive selected statistics,
the critical quantiles, independent-reference uncertainty diagnostics, binomial count limits,
bootstrap tail resolution, order-statistic ranks, seed overlap, and the cost arithmetic.
The CSV did not change while read; SHA-256:
`7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb`.

The running probe's log identifies 40 planned datasets, code/config `fab869c34eb6`, seed 2027,
B=50, four inner starts, layer 41, eleven workers. No completed dataset row was in its log at
the review's read; no coverage finding is claimed here.

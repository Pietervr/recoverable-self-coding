# Codex second opinion — proposed per-member fitter starts

14 September 2026. Requested by Claude Entropy SI at 11:20 PDT; brief
`2026-09-14_fitter_start_recipe_codex_brief.md`, initially RSC `f6a4c93`, with its
accepted cost correction at `6518219`.

**In progress: primary PC files requested, source verification still owed.** The
protocol and design assessment below is recorded now; the numerical tables have
not yet been independently reproduced. Codex owns this review and supporting
evidence. Claude retains production, protocol, execution, manuscript and R052
front matter. No fits, simulations, cloud actions or production edits were run.

Read the complete brief and its correction, the complete T1 pre-registration,
`rsc_t1_simulation_design.md`, `analyze.py`, and the relevant scoring, moment-start,
selection and recovery functions in `models.py`. Read both original epc II messages
from the Entropy SI transcript, at 18:04:53Z and 18:09:17Z, rather than relying on
the later summaries. They report PC commits `d0d194a` and `eeebaa9`; their scripts,
CSVs and per-start records are not present on this Mac at this checkpoint.
Claude requested their transfer into `reviews/pc_audit_2026-09-14/` after Codex's
11:23 PDT evidence request. Receipt, provenance and verification remain to check.
The resumed Codex session verified its wrap receipt on 14 September. Claude's
11:32 PDT transcript reports the package staged on the PC's iCloud Drive, with
Mac sync/checksum/move assigned to Claude; the destination is still absent at
the resumed check. No duplicate request or transfer watcher was started. The
reported package omits the per-start archive and distinguishes fitting source
`72c21a6` from reporting source `d0d194a`; their actual files and hashes remain
unverified here. The review remains open and no final verdict has been sent.

The procedure compares two families through nested concept cross-validation.
Every member is fitted in every inner fold; inner held-out scores choose each
family's member. Outer refits then supply independent concept scores, and a
concept bootstrap supplies the interval. Improving the optimizer changes this
whole statistical procedure, including its expectation and resampling behaviour.

## 1. What the prefix evidence can establish

Prefix scoring is an appropriate inexpensive way to compare *candidate search
recipes on the archived simulated datasets*. Match `models._pick`: prefer the
best finite converged training likelihood; if none converges, retain the best
finite run after the declared recovery chain and flag it. If none is finite,
record the failure. Held-out scores evaluate that training-selected solution.
Choosing the start by its held-out score would answer a different question.

Including a candidate's own starts in the reference union is legitimate for
measuring regret relative to that finite archive. It guarantees that a nested
larger training search cannot have a worse best converged training likelihood
when the smaller search has a converged solution. It does not establish the
global optimum, a future miss probability, or better held-out prediction. A
zero gap for the full union is construction, not validation.

The reported M3H and M2H results justify considering different recipes. They do
not justify saying the seed control proves that width does all the work. There
are two narrow draws and one wide draw, with different random streams. Equal
aggregate miss rates in the two narrow draws need not mean the same individual
fits missed. The comparison addresses one alternative seed draw; it does not
separate width from arbitrary seed variation or a width-by-seed interaction.
Likewise, 16 wide and 64 narrow have similar pooled miss frequencies, but their
reported mean training gaps and held-out losses differ. They have not been
shown equivalent in those losses, runtime or scientific performance.

The 896 fits per recipe are seven members at two sizes on 64 simulated units,
not 896 independent datasets. A per-member pooled rate has only 128 fits and
mixes inner and outer sizes. Report paired differences on the same units,
separately by size and generator, retaining the pairing and dataset clustering
in uncertainty estimates. Four replicates per setting are exploratory evidence.
Morris, White and Crowther's simulation guidance supports declaring the estimand,
methods and performance measures and reporting Monte Carlo uncertainty
([2019, Table 1 and §§3–5](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)).

## 2. Member-specific pre-registration

**Acceptable in principle.** Different parameterizations can require different
search effort to approximate the same training-likelihood objective. An equal
start count is not a statistical fairness requirement. Specify the policy before
confirmatory outcomes, develop it on simulations, then validate the frozen
procedure on independent seeds.

M3H +16 wide and M2H +64 narrow are defensible candidates on the reported
evidence, not yet a validated final prescription. The cheap-member union is a
reasonable training-search default where individual recipes remain unresolved,
including M3 and M3L. Calling it conservative refers only to the training search:
it does not guarantee conservative false-positive rates or better prediction.
M3V on M2S omega 2 deserves explicit reporting because the rare losses are large.
The report establishes zero misses for certain added batches, not for every
possible extra draw.

Specify the complete policy: counts by member and fit size; the training-only
moment base; jitter in raw coordinates; exact M2K skew vectors and whether they
replace four wide starts or add four more; independent seed derivation; finite
convergence, likelihood ties and failure recovery; initial/final vectors and batch
identities; effective configuration and source/runtime hashes. Repeated unjittered
moment starts must not masquerade as independent additional starts. This is an
amendment for a new numerical snapshot; existing rows retain their identity.

## 3. Inner fits and the bootstrap

**Include the inner fits.** A better outer refit cannot repair selection of the
wrong member caused by an inadequate inner search. The reported inner M2K miss
rate makes an outer-only amendment particularly hard to defend. Applying the
same *added batches* at both sizes is a clear initial candidate. A cheaper
size-specific policy is possible only if declared and evaluated as such.

The totals implied by this proposal are:

| Member | Inner total, including four cold | Outer total, including eight cold |
|---|---:|---:|
| M3H | 20 | 24 |
| M2H | 68 | 72 |
| Cheap-member union, excluding any extra skew starts | 84 | 88 |

`analyze.layer_pipeline` makes four inner fits and one outer refit for each
member in each of five outer folds. All outer members are fitted, including
those needed for the ensemble sensitivity. `refit_bootstrap` calls this same
pipeline with the same Config on each resample, with original-concept copies
kept together. The full cost is dominated by those repeated inner fits as well
as the outer fits; the outer-pair multiplier is not the bootstrap multiplier.

## 4. Additional development before adoption

The targeted M3H 16-versus-32-wide check is warranted before treating 16 as a
settled count. Score both fit sizes, keep the first 16 as an exact prefix, and
freeze the extra batch and the reporting rule before running it. It is a search
curve check, not proof of saturation. It can use the balanced existing units for
development, while independent datasets remain necessary for later validation.

Use the existing archive first for the unresolved member-by-size tables, paired
miss transitions, gap tails, held-out gains and losses, exact union candidate,
M2H prefix curve and separate M2K challenge. If the claim is specifically a width
effect, a bounded comparison using the same standardized perturbations at both
widths across more than one independent batch is cleaner than another unmatched
seed. The M3H check alone does not establish the other members or the full assay.

Before final adoption, check the chosen policy through the actual nested
selection path, including near-boundary mixture alternatives, and benchmark that
path on the intended machine. The reported zero sign changes use an outer-size
proxy, not all inner selections, interval endpoints or the four-way outcome rule.
It cannot establish that the confirmatory decision is unaffected. None of these
new fits is authorized or launched by this review.

## 5. Cost and which analyses must use the amendment

The original brief's prices count additional starts only. Claude accepted the
correction at `6518219`; the source reports still need their timing definition
checked. Arithmetic on the reported outer-size rates is:

| Member | Seconds per start | Current eight | Added batch | Proposed total |
|---|---:|---:|---:|---:|
| M3H | 39.7 | 317.6 | 635.2 | 952.8 |
| M2H | 15.1 | 120.8 | 966.4 | 1,087.2 |
| Pair | — | 438.4 | 1,601.6 | 2,040.0 |

The ratio to today is 4.6533. Cold plus 64 narrow on both costs 3,945.6 seconds,
so the candidate costs 51.7% of that comparator, a 48.3% saving. These are linear
calculations from reported rates, not measured complete-recipe runtimes. Start
iterations can depend on member, width, sample size, generator and convergence;
the PC rates do not turn the old 15.3-minute Mac bootstrap benchmark into a new
forecast. Include all inner fits, cheap members, compilation, recoveries, layers,
readouts and the original analysis when re-costing.

**An adopted amendment must apply to confirmation and to validation of its
refitting interval.** Let A name the start policy. The declared target is
theta(g,A) = E[Delta produced by the complete procedure using A]. Changing A can
change the target as well as the interval. New-policy original estimates,
bootstrap resamples and independent reference means must use the same declared
policy. An old-policy point with new-policy bootstrap fits is a different hybrid
method, not a cheap validation of the amended one.

The running old-policy probe, M2B control and omega-2 bank remain useful method
development for that policy. Keep them and their identities. They do not become
new-policy coverage evidence through relabeling or pooling. A limited paired
comparison can use the same underlying synthetic datasets, but the amended
scores require the amended fits; old scores are not such a comparison.

Zero proxy sign changes is insufficient reason to skip interval validation:
coverage concerns a quantitative target, and the reported magnitude changes can
matter even with an unchanged sign. Conversely, 10.5% training misses alone does
not establish that this more expensive recipe fixes the undercoverage. Cost a
bounded development and validation plan under the standing USD 3,000 cap before
new spending; the existing owner and launch approvals are unchanged.

## 6. Primary evidence checks still open

Before the numerical findings can be signed off, read the actual PC scripts and
tables and verify their provenance. Specifically reconcile the brief's 32-cold
description, the companion's 32 separated-skew wording, the report's 64+16 added
batches and 88 archived starts with the actual inner four/outer eight policy.
Check the reference candidate set, miss tolerance, convergence preference,
failures and denominators; exact balanced-block selection; candidate starts and
seed overlap; training-derived floor and scoring settings; stored parameter
precision; per-member/per-size paired results; and whether the seconds-per-start
figures include the cold batch. No primary table has been independently
recomputed at this checkpoint.

The development direction is reasonable. The outstanding evidence, bounded
search check and matched-procedure validation separate that judgment from final
adoption. This review does not reopen Melcon review 5, authorize EEG or a freeze,
or change the completed publication receipts.

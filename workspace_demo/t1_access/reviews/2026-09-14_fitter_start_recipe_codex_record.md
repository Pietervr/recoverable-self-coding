# Codex second opinion — proposed per-member fitter starts

14 September 2026. Requested by Claude Entropy SI at 11:20 PDT; brief
`2026-09-14_fitter_start_recipe_codex_brief.md`, initially RSC `f6a4c93`, with its
accepted cost correction at `6518219`.

**In progress: primary CSV and archive selection checks completed; integration
and final six-question response still owed.** The numerical evidence checkpoint
below updates the provisional design assessment. Codex owns this review and supporting
evidence. Claude retains production, protocol, execution, manuscript and R052
front matter. No fits, simulations, cloud actions or production edits were run.

Read the complete brief and its correction, the complete T1 pre-registration,
`rsc_t1_simulation_design.md`, `analyze.py`, and the relevant scoring, moment-start,
selection and recovery functions in `models.py`. Read both original epc II messages
from the Entropy SI transcript, at 18:04:53Z and 18:09:17Z, rather than relying on
the later summaries. PC scripts, CSVs and the subsequently requested per-start
archive are now present in `pc_audit_2026-09-14/`, delivered through Claude via
Dropbox. All package and archive checksums pass. Independent stdlib verification
is saved in `2026-09-14_fitter_evidence_checks.py` and its JSON output; it imports
no numerical model and runs no fitting. It reconstructs every archived prefix
selection and aggregates both CSVs. Held-out evaluations have not been re-run.
No final review reply has been sent. The draft must be integrated with §6 before
being marked complete.

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
reasonable training-search default for M2B, M2K, M3, M3V and M3L. M2S requires a
separate budget and decision: it is not cheap (about 7.93 seconds per added outer
start). Calling the union conservative refers only to the training search:
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

The primary source times the cold batch separately; `seconds_strong` measures
only the 80 added starts. Using the full audit's 96 units per member/size, the
proposed total is mean cold time plus added-count times mean added time / 80:

| Member | Current outer cold (s) | Added seconds/start | Proposed total (s) |
|---|---:|---:|---:|
| M3H, +16 wide | 309.026 | 38.9505 | 932.234 |
| M2H, +64 narrow | 116.325 | 15.0145 | 1,077.250 |
| Pair | 425.351 | — | 2,009.484 |

The independently reproduced ratio is 4.7243; cold+64 narrow on both is
3,879.106 s. The prefix report's per-start rates average the 70 archived units,
which explains its slightly different basis. These are linear extrapolations
from pooled added-batch timings, not timings of separately executed recipes.
The cheaper-width batch can have different iteration costs; a literal fourfold
total-recipe saving is not established.

M2S alone adds 634.169 s under the proposed 80-added union, reaching 695.632 s
per outer fit. Including all eight members, that original proposal is 2,803.364 s
against 495.907 s of cold fits at outer size. Applying four inner fits plus one
outer fit in each of five folds gives 47,796 s versus 5,766 s on this PC timing
basis, about 8.29 times; this is an extrapolation across sizes/folds, not a new
pipeline benchmark. It cannot be applied to the 15.3-minute Mac resample figure.
The M2S correction is accepted in the brief at `382e7bb`; a final M2S recipe is
not yet established. Re-cost all members, inner fits, compilation, recovery,
layers, readouts and the original analysis on the intended machine.

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

## 6. Primary evidence checkpoint — 14 September, before the 81% wrap

The verifier independently confirms 1,536 unique fits, 96 units, 161 misses at
training gap > 0.5 nat, no nonfinite fit scores and a converged cold winner in
every fit. The strong search is 8/4 cold + 64 narrow + 16 challenge: totals 88/84.
M2K's challenge contains four fixed alpha-sign combinations (+2,+2), (+2,-2),
(-2,+2), (-2,-2), followed by 12 wide jitter draws; the four do not add to 16.
No 32-cold batch exists in this source. The audit bypasses `fit` recovery, which
has no effect on these rows because every cold batch converged. Its start RNG
tags differ from `analyze.layer_pipeline`; it studies that count/width policy on
fold 0, not the exact random starts of a full pipeline execution. Its outer
training floor is also used at inner size, matching the existing analysis code.

All seven original package hashes, three archive hashes and 96 member-file
hashes pass. Removing the 34-line reporting addition from `audit_fits.py` yields
exact Git blob `025f4ec859cef9f83ace65d7033cf4cbfe0f2e21`, independently verifying
the reported producer/reporting-code relationship, not merely accepting the
provenance prose. The checkpoint schema was introduced mid-run: only 70 units
carry per-start data (rep 1: six; reps 2–5: 16 each), with 26 earlier units
unarchived. The files do not themselves supply a per-unit loaded-code digest.

All 96,320 stored starts were checked: 609 nonconverged, zero nonfinite
log-likelihoods. All 12,320 prefix choices, likelihoods, counts and miss flags
were reproduced directly from the archive with the convergence preference and
first-in-order tie rule. The balanced block is 64 units / 896 non-skew fits per
recipe; all member/size/setting tables and paired transitions are saved in JSON.
Six common seed values are reused across settings, and some zero-parameter null
settings share draws, so neither 96 units nor 896 fits are independent replicates.

Selected balanced-block miss counts (each cell has 64 fits):

| Member/size | Cold | +16 narrow | +16 wide | +64 narrow |
|---|---:|---:|---:|---:|
| M3H outer | 15 | 13 | 3 | 10 |
| M3H inner | 12 | 11 | 2 | 7 |
| M2H outer | 6 | 5 | 3 | 2 |
| M2H inner | 7 | 6 | 7 | 0 |
| M2K outer | 6 | 3 | 0 | 2 |
| M2K inner | 12 | 2 | 2 | 0 |
| M2S outer / inner | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

M2K's wide label means the mixed skew/wide batch above. M3H's two narrow
16-start draws each miss 24/128, but six fits change miss status: outer 1 rescued
and 2 newly missed, inner 2 rescued and 1 newly missed. Thus equal aggregate
misses do not establish seed irrelevance. M3V still misses 4/128 with the first
16 narrow starts; the zero applies to the second 16 narrow, 16 wide and 32/64
narrow candidates, not to every extra draw. M2S's one full-audit miss lies
outside the balanced block and must be examined before calling no extra starts
a validated prescription.

Zero outer-oracle proxy sign changes reproduces for all 96 audit units and for
all eleven prefixes on the 64 balanced units. The proxy explicitly chooses the
best member on the outer held-out data; it does not implement inner selection.
Ten audit changes exceed 0.001 nat/trial; mean absolute change 0.0384197,
maximum 0.9578855. The report's per-setting Delta columns accidentally retain
only the last replicate (`eff_by` overwrites earlier keys). For M2S omega 1/2,
the actual mean changes are +0.228504/+0.242861, not the near-zero last-row
values in that table. Its trigger uses setting-mean outer heterogeneity for
every fit, not each fit's pre-fit statistic; the quoted 70/161 is not a
within-fold trigger validation. The prose saying omega 0.5 has no misses also
disagrees with its own table (one miss).

Precision is a real limit: log-likelihoods and final vectors have six decimals,
initial vectors five. Rounded likelihood ties change the selected final vector
relative to the raw fit winner in 790/1,120 reference sets and 484/1,120 cold
sets. The prefix/raw-audit held-out differences reach 1.30e-5 nat/trial for cold
and 8.53e-5 for references. These differences combine rounding and changed tie
selection; they are not a demonstrated pure theta-rounding bound. Held-out
evaluation itself has not yet been independently re-executed. Retain full
precision and deterministic ties in the amended archive. Finish assessing
these limits and integrating §§1–6 before delivering the final review.

The development direction is reasonable. The outstanding evidence, bounded
search check and matched-procedure validation separate that judgment from final
adoption. This review does not reopen Melcon review 5, authorize EEG or a freeze,
or change the completed publication receipts.

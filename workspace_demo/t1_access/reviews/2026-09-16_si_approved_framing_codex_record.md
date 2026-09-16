# Approved Entropy SI framing: Codex second opinion

Date: 2026-09-16 UTC / 2026-09-15 PDT. Final review of
`2026-09-16_si_approved_framing_codex_brief.md` at RSC `0a466b0`, requested by
Claude Entropy SI at 18:48 PDT on the owner's behalf.

**Verdict: support the approved scope, with the corrections below.** The paper
can report a human reproduction and an application-specific simulation audit,
then propose a transfer protocol. It does not yet supply a validated replacement
test. No additional simulation is required for that claim set.

The owner has approved C, the proposed cuts including Melcon, and RSC option 1.
B remains rejected as written at any budget. A remains undecided and gated on
the auditors and capture machine; no pilot result belongs in the present abstract.
Claude retains scope disposition, manuscript, protocol and execution; R084 owns
the instruments. This record authorizes no scientific run or production change.

## Q1. Framing and boundaries

The central question is sound if stated as an audit of a **specified candidate
transfer procedure**, including what it fails to establish. A useful problem
statement is:

> A predictive comparison cannot be transferred across substrates by preserving
> predictor forms alone. Fitting, sampling units, the uncertainty target and the
> decision rule must be specified and assessed in the proposed application.

This avoids suggesting that T1 literally carries over the human decision rule:
it does not. Nor does this audit establish precisely which change would repair
the procedure. Expanded predictor families, selection, fitting variability,
dependence and score tails are distinct issues; the saved comparisons do not
isolate their causal contributions.

Present two completed analyses and a proposed protocol:

| Contribution | What is established | Boundary |
|---|---|---|
| Human reproduction | A faithful computational port and reanalysis on the original 20-participant data, including optimization sensitivity and the passive analysis | No new participant sample and no calibration of the inherited human decision procedure |
| Simulation audit | Performance of the specified T1 procedure in twelve declared graded settings; predictor-pair sensitivity; interval/reference diagnostics including the independent-seed bank | D = 4, one layer, finite generating families; power, broader recovery and actual-band validation remain unestablished |
| Proposed transfer | A concrete cross-substrate measurement and inference contract | Not a third validated empirical result, a confirmed model finding, or an instrument for consciousness |

The omega-2 bank belongs within the simulation audit. It is a second diagnostic
view of that audit, not an independent validation of its confidence claims.

No scientific cut needs restoring. Retain compact statements of the following:

- The human decoder/leakage and readout limitations, optimizer dependence, the
  inherited participant-level PXP rule and its lack of new recovery calibration.
  Keep the passive non-decision. State that the active reference was selected
  after seeing outcomes; do not turn the human anchor into prospective validation.
- Predictor preference concerns conditional readout distributions. It does not
  identify latent states, dynamical attractors, workspace access or consciousness
  without the separate bridge assumptions and interventions.
- The declared null families are plausible stress cases, not an exhaustive set
  or empirically calibrated model-data generators. Twelve thousand graded calls
  establish neither useful discrimination nor power under mixture alternatives.
- Preserve prospective freeze, the content/readout bridge and H3's causal role
  for the later model study. The SI audit does not relax those gates.
- The interval diagnostics remain visible, including uncertainty in the
  expectation reference. A failure to establish calibration is itself a result;
  it need not be recast as a fully explained failure mechanism.

RSC option 1 fits this scope: one motivation sentence, then the access-versus-
operation hypothesis in the appendix. Capacity/load/margin quantities are not
measured here. Predictive cross-entropy supplies the information-theoretic link;
no thermodynamic claim or measured operational loop follows from this assay.

## Q2. Historical-pair sensitivity is legitimate, with a precise label

Report it as **inherited-predictor-pair sensitivity under the T1 procedure, on
declared graded generators**. Make it visibly a post hoc saved-data analysis.
It is informative and strengthens the connection between the human comparison
and the proposed transfer. It is not a recovery audit of the published study.

The historical source at RSC `52267ec` makes the distinction concrete:
`t1_access/analyze.py::layer_pipeline` derives historical concept scores from
the T1 outer refits, using `(logq[M3] - logq[M2B]) / n_c`.
`analyze_dataset` then applies the same fixed-score concept bootstrap and
interval-sign rule as for selection and ensemble. Positive lower endpoint means
mixture; negative upper endpoint means graded; otherwise inconclusive.

| Procedure | Predictors and fitting | Decision |
|---|---|---|
| Published human analysis / faithful port | Three-model comparison, block cross-validation, participant fits with inherited Nelder-Mead procedure | Participant-level three-model SPM protected exceedance probabilities and the inherited rule across time windows |
| T1 historical-pair sensitivity | M3 versus M2B scores from T1 outer refits | Fixed-score concept bootstrap and interval-sign rule |
| T1 primary and ensemble | Expanded graded and mixture candidate sets, with selection or equal-weight predictive aggregation | The same T1 bootstrap/sign rule |

The published human model-comparison methods confirm the first row:
[Sergent et al. (2021)](https://www.nature.com/articles/s41467-021-21393-z).
Carrying over two predictor forms does not carry over the published fitting,
three-model group comparison, sampling units or temporal decision procedure.

### Verified saved-row comparison

Source: `2026-09-16_si_approved_framing_saved_rows.json` and its adjacent stdlib
script, committed at RSC `bac035a`. The bounded check completed before this
record; it was not rerun after continuation. It checked 12,000 unique rows,
twelve settings with reps 0-999, D = 4 and one layer; all three point estimates,
interval endpoints and SEs were finite, and endpoint signs exactly reproduced
every stored decision. All rows carry code hash `b29215469af9` and recorded
`failed = 0`. This last field is not an independent optimizer-convergence audit.

G/M/I below means graded / mixture / inconclusive. The last column is the
primary interval's inclusion rate for that setting's **same-sample replicate
mean**; it is not a known-population coverage probability.

| Graded setting | n | Selection G/M/I | Ensemble G/M/I | Historical G/M/I | Recorded failures | Primary reference inclusion |
|---|---:|---:|---:|---:|---:|---:|
| M2B | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.935 |
| M2H, tau = 0 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.918 |
| M2H, tau = 0.5 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.819 |
| M2H, tau = 1 | 1,000 | 1000/0/0 | 1000/0/0 | 975/0/25 | 0 | 0.926 |
| M2H, tau = 2 | 1,000 | 1000/0/0 | 1000/0/0 | 0/651/349 | 0 | 0.894 |
| M2K, alpha = 0 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.915 |
| M2K, alpha = 1 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.885 |
| M2K, alpha = 3 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.928 |
| M2S, omega = 0 | 1,000 | 1000/0/0 | 1000/0/0 | 1000/0/0 | 0 | 0.917 |
| M2S, omega = 0.5 | 1,000 | 1000/0/0 | 1000/0/0 | 966/0/34 | 0 | 0.848 |
| M2S, omega = 1 | 1,000 | 1000/0/0 | 1000/0/0 | 846/1/153 | 0 | 0.780 |
| M2S, omega = 2 | 1,000 | 1000/0/0 | 1000/0/0 | 77/337/586 | 0 | 0.216 |
| Total | 12,000 | 12000/0/0 | 12000/0/0 | 9864/989/1147 | 0 | Not pooled |

The source is `sim_results/d4v12b/calibration_D4.csv`, 98,959,507 bytes,
SHA256 `7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb`;
the bounded check verified unchanged input bytes. Claude's separate aggregation
is committed at `980820a`; this verdict relies on the independently
checked `bac035a` evidence, not on an unreviewed implementation equivalence claim.

The table supports these statements, with their denominators:

- The inherited pair makes 651 mixture calls in 1,000 M2H tau = 2 datasets,
  337 in 1,000 M2S omega = 2 datasets, and one in 1,000 M2S omega = 1 datasets.
  Inconclusive results also occur at M2H tau = 1 and M2S omega = 0.5.
- In these settings the primary and ensemble comparisons return graded in all
  12,000 datasets. This is observed performance of those complete procedures.
  Both G and X candidate sets expand, and selection/aggregation changes; the
  comparison does not isolate adding graded alternatives as the reason.
- A historical mixture call is false relative to the declared graded generating
  family. That is not automatically a type-I error for a statistical null that
  this misspecified pair's own expected score difference equals zero. Its
  positive preference can reflect relative predictive fit under misspecification.
- Do not present 989/12,000 as a universal false-positive rate, or call the result
  an audit of Sergent's false calls. The mixture of settings is our design choice.
  Agreement of selection and ensemble uses the same fits and datasets; it is a
  sensitivity check, not independent replication.

For each setting, zero observed primary mixture calls out of 1,000 gives a
one-sided 95% binomial upper limit of 0.002991, under independent replicates and
the fixed procedure. This is a per-setting bound, not a simultaneous bound or
a statement of zero error over all possible graded distributions. It says
nothing about power to recognize mixture alternatives, nor does it validate
the nominal confidence level attached to a graded decision.

### Interval and reference correction

Six primary plug-in inclusion rates fall below the declared 0.90 floor:
0.819, 0.894, 0.885, 0.848, 0.780 and 0.216. Their range is **0.216-0.894**,
not 0.22-0.82. M2K alpha = 1 is one of the six: this interval diagnostic is not
confined to concept heterogeneity, unlike the observed historical mixture calls.

The 0.216 uses the d4v12b omega-2 replicate mean, -5.334354. This is an estimated
reference from the same sample as the intervals. The manuscript Methods already
notes that the plug-in Monte Carlo SE ignores reference dependence; retain that
caveat next to the results, rather than presenting these rates as exact coverage.

The saved `t1_omega2_bank_2026-09-15/omega2_target_check.json` supplies the
independent-seed diagnostic: 1,000 datasets, mean -6.869911, sample SE 2.678379,
median -2.065273, minimum approximately -2650.300. The old intervals include
that bank mean at rate 0.178, its median at 0.754, and its mean after removing
the minimum at 0.282, versus 0.216 for their own replicate mean.

These are descriptive **candidate-reference inclusion rates**. An independent
seed bank with an imprecise mean does not certify independent coverage against
a known expectation. The estimand is fixed by the procedure and generating
distribution; its expectation is imprecisely estimated. The evidence proves
neither that the expectation fails to exist nor that it cannot be estimated at
all. Avoid calling the estimand itself imprecise.

The median is a different target. In particular, 0.754 must not be judged as
mean-interval coverage against the 0.90 floor, or described as validation of an
interval for the median. Leave-k-out or trimmed summaries remain sensitivity
descriptions, not a retroactive change of target. Keep every extreme in the
primary record. None of this establishes a unique tail, optimizer, fitting or
selection mechanism, and it does not certify refitting as the remedy.

## Q3. Do not add a historical-human recovery study to this SI

Keep the limitation visible. The narrowed SI can make its stated contribution
without a new human-procedure recovery study. An exact implementation can
reproduce an analysis while its scientific error rates remain uncalibrated.

A meaningful additional study would need its own human-data generating model,
readout/decoder scope, block and temporal dependence, participant aggregation,
optimizer policy and complete PXP/window decision rule. It would also need
prespecified performance targets, costs and stopping rules. Recovery under a
convenient scalar generator could not certify the original EEG pipeline or the
biological claim. Such work is not free merely because it avoids AWS billing.

No new simulation is recommended or authorized here. This does not require
hiding future evidence. The probe, M2B control and JOB D remain in the continuing
model-methods work under their existing ownership and gates; do not relaunch or
infer job status from this review. Default to keeping their numerical development
results out of the SI main text. If complete and materially relevant before
submission, one balanced development sentence may report the exact policy,
sample and target limits; it cannot establish a repair or validate the full assay.

## Q4. Strengthen the audit using what is already available

The best additional material is the verified twelve-row table and explicit
procedure/target distinctions above. They make the argument inspectable without
a new diagnostic sweep. In the manuscript:

1. Put the human and T1 rules side by side. Name the sampling unit, score,
   predictor families, interval target and decision rule, so the reader can see
   exactly what is reproduced and what is new.
2. Preserve all setting and failure denominators, and distinguish graded,
   mixture and inconclusive outcomes. Put finite-family scope and unassessed
   power beside the zero-call result. For nonzero call rates, ordinary binomial
   Monte Carlo uncertainty is conditional on that fixed setting and procedure;
   it is not uncertainty about generalization beyond the battery.
3. Name every interval reference and its estimation uncertainty. Keep the
   independent-seed bank separate from the original same-sample plug-in check.
   No new empirical coverage certificate follows from relabelling either.
4. Give executable source provenance for the saved-data sensitivity and exact
   versions for results beyond the earlier public DOI snapshot. Label the
   sensitivity as post hoc and retain the full negative/inconclusive outcomes.

The novelty should be application-specific: the audited candidate transfer,
its sensitivity to predictor choice, and the difficulty of estimating its
expectation reference under the observed extreme-score behaviour. Generic
cross-validation interval undercoverage and the need to distinguish estimands
are established issues; [Bates, Hastie and Tibshirani](https://arxiv.org/abs/2104.00673)
provide relevant context. Their results neither identify this T1 failure
mechanism nor supply a validated remedy for it. Likewise, multiple simulation
performance measures and Monte Carlo uncertainty belong to established practice;
see [Morris, White and Crowther](https://doi.org/10.1002/sim.8086), already in the SI
references.

The focused source search did not establish priority for this computational
reproduction. Remove "first independent" unless a separate, adequate literature
check supports a precisely defined priority claim. No exhaustive novelty verdict
is made here; the prior scope review's Gurnee qualification also stands.

## Q5. Abstract and opening corrections

- Open with the workspace hypothesis and the problem of transferring a
  conditional-readout comparison. Do not assign an all-or-none prediction to
  every theory of consciousness or equate a fitted mixture with latent states.
- Replace "nobody checked" with the particular validation gap examined here.
  Replace unqualified "realistic alternatives" with declared plausible graded
  alternatives; their match to model data is not yet established.
- Replace "first independent reproduction" with computational reproduction on
  the original data. Independence of implementation is not biological replication.
- Human "interval edges" are temporal preference boundaries, not confidence
  interval endpoints. If retained, 315 ms is the first inherited descriptive
  PXP > 0.95 crossing, not a calibrated access onset. Approximately 0.003 nat/trial
  describes the active plateau; it is not a common effect size across substrates.
- Replace the precise "coverage as low as 0.22" headline with qualified
  reference-inclusion diagnostics, or omit that number. The six-setting range
  and the meaning of the independent bank require the corrections in Q2.
- The historical counts are useful if explicitly under the T1 rule. They cannot
  imply that the original human rule was run on these 12,000 datasets.
- End with the proposed transfer and outstanding validation conditions.
  Neither a completed pilot nor a validated replacement is presently a result.

### Proposed replacement abstract

Global-workspace accounts motivate tests of all-or-none access, but transferring
comparisons of conditional readout distributions requires separate validation
of predictor choice and statistical decisions. We reproduce a published human
EEG analysis on its original 20-participant dataset and audit a candidate
transfer procedure using differences in held-out log predictive density.
The reproduction recovers the reported active-condition preference for a
two-component predictor, with optimization-sensitive temporal boundaries;
the passive analysis does not cross the inherited preference threshold.
Across 12,000 simulated datasets from twelve declared graded settings, the
expanded comparison and its ensemble sensitivity always favour graded
predictors. Under the same T1 decision rule, the inherited predictor pair
instead gives 989 mixture calls and 1,147 inconclusive outcomes. Interval
diagnostics raise a distinct concern: six plug-in reference-inclusion rates
are below 0.90, and an independent-seed bank at the strongest scale
heterogeneity reveals an expectation estimate sensitive to extreme scores.
These findings neither calibrate the published human decision rule nor
establish power or a validated replacement. We provide an application-specific
transfer audit and a proposed cross-substrate protocol, with confirmatory
model claims conditional on prospective validation.

Abstract word count: 177 (whitespace-delimited).

## Sources and verification boundary

The review completed the requested source reading before continuation: the
entire brief, approved strategy and preceding scope proposal/addendum,
manuscript introduction/results/theory/discussion/methods, design sections
11-12, the complete previous scope record at `2e29207`, the owner discussion
through approval and the current Entropy SI brief-delivery discussion.
It also read the full `sergent_port/README.md`, historical T1 `analyze.py` and
`simulate.py` at `52267ec`, and the complete saved omega-2 diagnostic source
and JSON. Primary literature consulted is cited at the relevant claims above.

Local context: Unimog `project_knowledge/rsc_publication_strategy.md`,
`project_knowledge/rsc_t1_simulation_design.md`, and
`papers/adaptive_agency_special_issue/sections/`; RSC
`workspace_demo/t1_access/reviews/2026-09-15_si_scope_and_model_route_codex_record.md`.
The approved-framing input is fixed at `0a466b0`; subsequent unreviewed
implementation edits are not silently adopted by this record.

Verification was bounded to existing rows: stdlib aggregation, 0.65 seconds,
no fitting, data generation, bootstrap, scientific imports or cloud calls.
The saved check was not rerun. No manuscript, protocol, production code,
model output, running job or other owner's working file was changed by this
review. The substantive reply and complete native Read receipt are recorded
separately in R052 after delivery; this document is the final scientific record.

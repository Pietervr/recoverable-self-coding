# Codex second opinion — Melcon v6 stage C failure and revision directions

15 September 2026. Requested by Claude Entropy SI at 03:37 PDT; brief
`2026-09-15_melcon_v6_stage_c_codex_brief.md` at RSC `a9a8573`, diagnostic
outputs at `66e4b16`.

**FINAL.** The v6 battery fails its declared X1-strong criterion in both drift
conditions. Accept the saved execution/results as the failed development record;
do not freeze the secondary analysis. The diagnosis warrants investigating
predictive stability and dose support before changing the decision rule. It does
not yet identify a unique cause or justify choosing revisions by whether v6 passes.

Codex owns this review, its evidence and the R052 log. Claude
retains protocol, implementation, manuscript, execution, front matter and
monitors. No revised protocol, fit, generated recording, EEG, freeze, cloud
action or production change has been made in this review. The prior calibration
acceptance and full-record receipt at `e1845a9` / Unimog `2d2ae627` are complete.
This is the new post-outcome failure review, not a reopening of that opinion.

## System and reading

The v6 decoder is trained on one two-block half. In the other half, likelihoods
train on one block and score the other, in both directions; the halves swap.
Evidence is the mean of four block log-score sums. Delta is the two-state minus
graded sum divided by all scored trials. The group rule compares null, graded
and two-state, requiring three adjacent windows with family PXP at least 0.95.
The null run is reported and does not independently veto a family call.

Read the full new brief, all four diagnostic scripts and their text outputs,
`likelihood.py`, `recording.py`, `group.py`, and shared `sergent_port/bms.py`.
The full PREREG, README, battery, decoder and synthetic files were read for the
preceding calibration review; the new audit refreshed their hashes and the
executing configuration. Fresh logs/status in both repositories, latest R052
entries and Entropy SI's 15 September 03:00 PDT onward transcript were inspected.
The complete primary `sergent_port/README.md`, `RESULTS_sergent.md`,
`fit_models.py`, and `model_comparison.py` have now been read. Its reproduction
uses a separate historical likelihood and validation design; its existing
limitations remain material. The actual submitted article's driver and all nine
section files have now been read from the ZIP with `unzip -p`, without extraction,
building or editing. The publication strategy reading continued from line 701 to
the end; the release record/manifest were read in the preceding continuation.

## Q1. Which parts of the diagnosis hold?

**The numerical description holds; the causal wording needs qualification.**
All saved decisions, diagnostics and severe-loss counts reproduce in the audit
below. The formal failure is X1 strong: zero two-state calls among six replicates,
three in each drift condition. G1–G3 meet their declared criteria through 35
inconclusive outcomes and one two-state outcome. No graded call is an important
additional limitation of the instrument, not a retrospective failure rule. All
34 recordings and ten main windows are eligible throughout; missingness or an
availability gate does not explain these outcomes.

The null's dominance at weak strength and in X2, the small positive median Delta
even under graded generators, and the disproportionate graded losses are real.
The trimmed positive means are useful descriptions of the remaining tilt; the
trimmed sample is not an alternative inferential dataset. A graded data-generating
process need not favor this fitted graded predictor at this training size and
readout. Approximation, parameter estimation, dose support and numerical fitting
all enter the comparison. Decoder AUC calibration measures signal availability;
it does not guarantee separation of graded and two-state conditional laws.

The fold examples demonstrate extreme held-out penalties with boundary parameter
values. They are ranks **1, 3 and 5** in the printed extreme list. The script
prints saved/rerun Delta to three decimals and has no full-precision equality
assertion. Its output omits full theta, conditional predictions, per-start
objectives and training-optimum checks. Do not describe it as an exact
full-precision reproduction of the literal three largest entries.

In `likelihood.py`, graded mean is `a0 + a1 L + beta h` and SD is
`exp(s0 + r L)`, with `L` the fitted logistic. An `a1` of 6.9–10 S is an
asymptotic amplitude, not the predicted shift on every observed trial;
`r = -ln(10)` permits tenfold contraction as L moves from zero to one. The combined
bounds permit an SD as low as 0.005 S, versus the two-state shared SD floor
0.05 S. That is a permitted limit, not a measured SD in the examples: their
printed `exp(s0)` is roughly S, and actual contraction depends on the missing
logistic parameters and doses. Small conditional SD can magnify mean error into
enormous Gaussian log loss. The events-only extrapolation evidence below makes
that mechanism plausible, but does not prove it is the sole cause or explain
the prevalence of all 1,898 severe graded losses.

Finally, arithmetic Delta and group PXP are different summaries. In the shared
`bms.py`, each recording contributes normalized responsibilities `g` in [0,1]
to the Dirichlet counts. Increasing an already decisive loss cannot increase
that recording's count without bound. Thus the tail demonstrably inflates mean
Delta; its numerical contribution to the PXP pattern has not been isolated.
This distinction follows the RFX derivation and outlier discussion in
[Stephan et al. (2009), equations 11–14 and Discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC2703732/).
PXP also depends on the model set and Bayesian omnibus risk, as in
[Rigoux et al. (2014), equations 6–7](https://www.tnu.ethz.ch/fileadmin/user_upload/documents/Publications/2014/2014_Rigoux_Stephan_Friston_Daunizeau.pdf)
(DOI `10.1016/j.neuroimage.2013.08.065`). Here its inputs are cross-validated
predictive scores, not integrated model evidences, so PXP is the inherited,
empirically assessed decision convention; 0.95 is not a demonstrated 5% error
rate. No defect in the shared BMS implementation was found in this review.

## Q2. Which revisions are justified, and what must stay fixed?

**Use v6 for declared method development, then evaluate one locked candidate
independently.** Post-outcome learning is legitimate when labeled and retained.
It becomes biased validation when the same outcomes choose and certify the
procedure. Selection must be included in the procedure being evaluated; see
[Cawley and Talbot (2010), Introduction](https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf).
The concrete recommendations below are this review's application of that
principle, not prescriptions from that paper.

1. **First diagnose the fitted predictions and the training search.** For a
   bounded development panel covering each generator/strength/drift, both severe
   and ordinary folds, retain every start's theta, objective, convergence state
   and chosen solution. Retain full-precision fold scores and conditional
   means/SDs over actual training and test doses. Log scaling, side, counts and
   dose-support ranges. Compare best training objectives and predictions across
   starts, including near-ties. Fit/start selection must use training data only;
   the known v6 test scores may diagnose the procedure as development evidence.
   A better maximum-likelihood optimum can generalize worse. More starts alone
   is not a remedy for unstable extrapolation or density misspecification.
2. **Develop a prediction-stable density, with a scientific rationale.** A
   positive effective-SD floor and regularization of asymptotes/slope are
   defensible candidates if specified in training units, with a declared scope
   and tested fairly for both families. Equal numeric parameter bounds do not
   imply equal predictive flexibility. A shared-SD graded model or narrower r
   is a restricted comparator and could weaken it under G3; it needs a recovery
   and misspecification check. G2 is skewed, while the graded likelihood is
   Gaussian; G3's latent SD plus additive sensor noise need not follow the
   fitted exponential-logistic SD. Diagnose these approximation issues too.
   A training-observed-range cap on a1 is not an automatic solution: a limited
   dose range need not identify the asymptote. No numeric replacement bound is
   established by the present evidence.
3. **Do not reject every boundary fit or delete difficult trials.** Graded
   `a1 = 0, r = 0` is a valid null-like submodel, and a boundary can be a valid
   constrained optimum. Any future availability rule must distinguish a
   numerical failure from a valid fit and retain failed attempts in reporting.
   Loss trimming, omitting extrapolated test doses, or choosing a start by
   held-out performance would change the target or contaminate evaluation.
4. **More density-training data is a design option, not yet a specified fix.**
   Every scored trial must be absent from both its decoder's and its density
   predictor's training. With four blocks, a possible allocation is two decoder
   blocks, one density-training block and one test block; simply pooling the
   other two blocks and scoring them leaks density-training information.
   Obtaining more density-training data therefore requires an explicit new
   allocation or additional data, with dependencies and scoring units documented.
   A redesigned decoder allocation changes its strength calibration too.
5. **Keep the current primary comparison and X1 test as the baseline.** A
   two-model BMS can be a clearly conditional sensitivity: which family is
   preferred given those two candidates. It cannot show that either predicts
   adequately, and removing the third model does not mechanically guarantee
   a larger PXP. The null run already supplies no separate veto in `group.py`.
   Do not lower PXP/run thresholds, remove null, boost X1 or relax its required
   recovery merely to turn this failed battery into a pass. Additional stronger
   X1 levels could map power as a new, explicitly labeled extension; retain the
   failed calibrated level and its result. A materially new primary group rule
   requires an independently evaluated registered revision.

Preserve the v6 data, code/runtime identity, seeds, ten calibrated amplitudes,
strength-resolution flags, X2 inversion and all original verdicts. Preserve
cohort, generator laws, dose definition, windows and decision criteria as the
comparison baseline. If a later approved revision changes any of these, name
the change explicitly and re-establish the affected calibration; never relabel
the existing result. The G1–G3 pass rule controls a limited false-two-state
behavior, not demonstrated positive recovery of graded laws. If graded recovery
becomes a requirement for the revised instrument, declare it prospectively.

## Q3. What must precede a rerun, and what should it contain?

Recommended sequence, subject to the owner's decision on Claude's concrete
revision proposal; this review authorizes no revised run:

1. **Preserve and specify.** The full saved-data audit is complete; do not repeat
   it. Write the revision and its estimand, folds, density/optimizer choices,
   selection rule, availability handling, success criteria and seed roles.
   v6 is the development sample. Commit the development plan before additional
   diagnostic fits. Keep all attempted candidates and their outcomes.
2. **Bounded development checks.** On synthetic development data, test the
   density/gradient and null-like special cases, finite conditional predictions,
   training-only scaling/selection, and decoder/density/test disjointness. Then
   examine the archived per-start and per-fold evidence described in Q2, with
   both ordinary and failing examples. Use an explicit limit on candidate
   revisions; fresh seeds used to choose a candidate are also development data.
   Add a cheap idealized density-level recovery check to separate a density
   problem from decoder/noise effects; it cannot replace the complete pipeline
   battery. No such computation was run for this opinion.
3. **Lock one candidate, benchmark, then validate.** Seal code, runtime,
   configuration, source/input hashes and the complete seed schedule before
   independent validation outcomes are opened. Use a new version/identity
   namespace and new independent recording seeds, with explicit separate tags
   for generation, decoder/folds, optimizer starts and group sampling as
   applicable. Run the whole retained battery: five generators × two strengths
   × two drift conditions × three replicates × 34 templates = 60 group
   replicates / 2,040 recordings, all main windows. Do not rerun only X1 or only
   the cells that failed. With three group replicates per cell, these are the
   declared development acceptance checks, not a precise power or error-rate
   estimate. A precision-driven expansion would itself need a declared plan.
4. **Calibration lineage.** A density-, optimizer- or group-only revision can
   retain the fixed calibrated amplitudes if the generator, decoder, strength
   statistic, templates/cohort and calibration settings remain identical.
   Record the exact parent v6 calibration hashes and applicability in the new
   manifest; do not claim that copied calibration was freshly run or rewrite a
   v6 seal to satisfy the new identity. Reusing v6 predictions to select a group
   rule remains development, not independent validation. A change to decoder,
   its training allocation, generator, dose/strength statistic or cohort requires
   new calibration with independent check seeds before the complete battery.
   Fresh calibration stages must keep separate search/check/validation seeds.
   Unresolved strengths and the original X2 amplitude inversion remain reported.
5. **Cost and stopping.** Original stage C ran 05:56:43Z–10:25:19Z, exactly
   4 h 28 min 36 s. Multiplying elapsed time by two workers gives 8.9533
   worker elapsed-hours, or 15.8 s per recording; it is not measured CPU time.
   The preceding benchmark was 11.242 worker-hours including generation.
   Neither measures a revised density, richer start schedule or different
   decoder allocation. Benchmark generation, decoding, fitting and summary
   separately under the intended concurrency after implementation, and cost
   optional recalibration and development separately. Claude retains scheduling,
   launch checks, thread limits, keep-awake and monitors. Retain failures; a
   failed independent validation returns the procedure to development and
   requires another untouched validation sample after any further selection.

The existing local authorization for v6 is not authorization for this new
post-outcome revision. No cloud spend, EEG readout, freeze or production action
is implied. The USD 3,000 cap, omega-1 hold and separate owner decision for the
PC nested-validation work remain unchanged.

## Q4. Implications for Sergent and the submitted arXiv v1

**No reported Sergent result or submitted numerical claim is shown to be wrong
by this Melcon battery. The broader methodological concerns remain relevant.**

The human reproduction uses the separate inherited `sergent_port/fit_models.py`
likelihoods: the graded scale is the absolute affine function of its mean;
optimization is the historical, unconstrained, capped Nelder–Mead path, not
Melcon's bounded exponential-logistic graded density. Its five likelihood folds,
ten decoder folds, trial population and scoring conventions also differ. Its
graded/two-state starting values use all trials, decoder and likelihood CV are not nested, and
known optimizer sensitivity limits the interval edges. It is a reproduction of
that historical procedure, not a newly validated, leakage-free assay. There is
no Melcon-to-Sergent import of the fitted density. The shared component is BMS.

The adjacent `2026-09-15_melcon_v6_stage_c_lineage_checks.py/.json` verifies all
11 tracked Sergent source/document files against producer
`e341319f5c6e0ce27fdeeb83ca6124009b7e0996`; every file is byte-identical, and
`git diff e341319 -- workspace_demo/sergent_port` is empty. Shared BMS SHA-256
`6d48a893977e6c71380223f19e70d5fcd95f076eccfa0b8332aada1db1717611`
matches the completed Melcon audit. This establishes source continuity, not
fresh numerical reproduction or proof that historical limitations are harmless.
No new Sergent fit, analysis or raw EEG read occurred. Do not transfer the
Melcon severe-loss rate or proposed bounds into claims about Sergent.

For the actual submitted text, the archive is
`Unimog-Projects/papers/adaptive_agency_special_issue/release/local/arxiv-submitted-v1/arxiv_v1_source_candidate.zip`,
SHA-256 `af47b85b2a9fd24222dfb73ba6781feb287d702169fa4463ebf3ec9d313f4818`.
The lineage check verifies that SHA and hashes all 14 members. The driver and
all section text were read directly from that archive, not inferred from live
manuscript files or the old candidate-status manifest wording.

- `arxiv_v1.tex` abstract and `sections/introduction.tex` status box identify
  the completed Sergent reproduction and separate model-side simulation audit.
  Melcon is under development; the dated snapshot is 13 September 2026.
- `sections/methods.tex`, human subsection, already states historical starts
  from all trials, nonnested decoder/likelihood CV, block overlap, capped fits,
  absolute-scale convention and descriptive PXP use.
- `sections/results.tex`, human subsection, already reports the modest active
  predictive advantage, optimizer-sensitive boundaries and two-model sensitivity.
  It says recovery for that historical family has not been run and limits the
  passive interpretation. The Melcon battery supplies no missing Sergent
  recovery validation.
- `sections/discussion.tex`, limits subsection, calls the visual dataset a
  planned secondary extension with a draft protocol and no outcome decoded.
  `sections/availability.tex` likewise says its loader was checked but no
  outcome decoding performed. Synthetic events-template development is
  consistent with those statements; it is not an EEG outcome.

Therefore this new failure does not require a correction to a claimed Melcon
result in submitted v1: no such result is claimed. In the next scientific
revision, report the failed development battery and the subsequent amendment/
independent-validation lineage before adding any secondary EEG conclusion.
Keep the human reference described as a bounded historical reproduction and
avoid implying that its two-state/graded discrimination has now been validated.
The primary/model-side fitter and interval work remains its own record; this
opinion does not transfer JOB B/C, certify those revisions or reopen R080.

The owning release/strategy record reports arXiv `submit/8075441` submitted and
Zenodo `22741885` published. No assigned arXiv identifier or changed portal
status was verified in this review. No manuscript, archive or publication was
modified. Claude retains manuscript and publication ownership.

## Completed independent audit — 15 September 10:51:28Z

Evidence: `2026-09-15_melcon_v6_stage_c_checks.py` and the adjacent `.json`.
Run once under RSC `.venv/bin/python`, nice 10, all five numerical thread
variables set to 1 before imports. The script guards against generation,
decoder execution, fitting, and production writes. Elapsed time: 74.11 seconds.
It recomputed all 60 `G.decide` results, including the common-cohort comparison,
with the original seed and 1,000,000 BMS draws. No numerical audit remains to be
repeated merely because this review crosses a session boundary.

- Actual namespace/runtime identity reproduced before and after:
  `ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021`.
  Source hashes, events-table hash, and effective one-thread OpenMP are saved.
- All 2,040 expected payloads and their sidecars passed `BT.load_verified`
  against freshly constructed manifests, including seed tags, calibration
  seals, amplitudes and template identities. All have status `ok`; all ten
  main windows have all models available and finite AUC/evidence. No extra
  payload, missing sidecar or temporary file was found.
- Every saved Delta equals `4 * (evidence_two_state - evidence_graded) / n`
  exactly (maximum absolute error 0). Every trial count matches its template.
  Fold-level sums cannot be independently checked: the payloads omit folds.
- All 60 outcomes and all 20 verdicts match the saved summaries; every numeric
  replicate diagnostic also matches. All 34 recordings enter every main-window
  comparison, so common-cohort runs are identical. Every entry of Claude's
  `stage_c_diag.json` reproduces, including rounded PXPs and run lengths.
- Outcomes: 59 inconclusive/mixed, one two-state, zero graded; verdicts:
  12 pass, two fail (X1 strong), six reported. Catastrophe counts:
  1,898/20,400 graded versus 8/20,400 two-state. Per-cell median-of-recording
  Delta spans +0.0063346 to +0.0290589 nat/trial; descriptive trimmed means
  span +0.0187006 to +0.0709378. Neither trimming nor rejection changed a call.
- All six v5 files, all 4,095 v6 files and all audited sources are byte-identical
  before and after. Aggregate fingerprints are in the evidence. Audited HEAD
  was `0daeb78`; this identifies the input state, not the later evidence commit.

### New structural finding: held-out dose extrapolation

The events templates alone (no readout or EEG) show substantial dose-support
shift in the three selected examples. Counts below use **all present trials**
and the complete training block's observed log-contrast range:

| Template and density fold | Training / test present trials | Test below / above training range |
|---|---:|---:|
| sub-30, block 3 → 4 (X2 strong example) | 86 / 90 | 0 / 60 |
| sub-30, block 1 → 2 (G1 strong example) | 93 / 91 | 3 / 30 |
| sub-18, block 1 → 2 (G3 strong example) | 90 / 93 | 0 / 62 |

Across 34 templates × four directed folds, 117/136 have at least one present
test dose outside the training range. This is structural covariate information,
not 136 independent evidence units or a demonstrated catastrophe rate. The
JSON also records side-specific ranges; those descriptive standardized values
use side-specific scaling and must not be mistaken for the model's pooled
training scaling. For the all-present rows above, maximum test dose under the
model's pooled training scaling is 3.791, 2.906 and 3.680 respectively.

This supports an extrapolation/identification mechanism more specifically than
"too few trials" alone. It still does not supply the fitted x0/k, predicted
mean/SD, or per-start training objectives needed to link each loss to its
mechanism. Do not remove out-of-range test trials after inspecting losses.

## Delivery

The scientific opinion and source/archive checks are complete. The numerical
audit above was run once in the predecessor and was not repeated. One requested
substantive reply to Claude Entropy SI follows the local commits. Exact native
receipt of the complete FINAL record will be recorded in R052; until verified,
Codex retains that delivery responsibility.

# SI interval-repair text — Codex round 3

27 October 2026, R052. Bounded text review of Unimog-Projects commit `ce2d9c7c4f99d8c6d612a949e8587efbc583f991`. The manuscript files read locally match that commit. `paper:` below means `/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/`; other paths are relative to `workspace_demo/t1_access/`. Line numbers identify source lines, which often contain several sentences.

## Blocking findings

### B1. The 0.03 bound is assigned to the wrong generator set; state the actual decision rule

**Location:** `paper:sections/methods.tex:131`, “For generators in the catalogue, the construction gives an inclusion rate of at least 0.95 and a mixture-call rate of at most 0.03.”

The inclusion construction concerns every catalogue setting. The mixture-call bound concerns **graded settings only**. The proposed catalogue also contains mixture alternatives whose detection probability is supposed to exceed 0.80. Moreover, these are mathematical bounds over a new calibration bank and a new study under a frozen algorithm, not measured performance of the intended-design procedure. The source gives a common calibration event of probability at least 0.99, conditional inclusion at least 0.96, and conditional graded-call probability at most 0.02. Its unconditional bounds are therefore 0.9504 and 0.0298.

**Exact replacement sentences:**

> The probability calculation assumes independent, finite runs of the frozen complete procedure. It gives median inclusion of at least 0.9504 over a new calibration bank and a new study. For each declared graded generator, it gives a mixture-call probability of at most 0.0298. These bounds use the calibration-error allocations in the method-repair record and apply within the frozen catalogue. The intended-design calibration and independent validation still have to run.

The same paragraph mentions a critical value but never says that it is an **additional** requirement beyond a positive interval. The historical rule elsewhere would omit it and would label a negative interval “graded support.” After the sentence about the order-statistic brackets, insert these exact sentences:

> The study statistic is the mean of the bounded contrasts across the 64 confirmation concepts. Mixture preference requires both a positive lower interval endpoint and a statistic above the calibrated graded critical value. A negative upper endpoint reports a negative bounded contrast. Other available results are inconclusive, and a failed fit or unavailable score is reported as unavailable.

Also replace “The complete point procedure is run on independent synthetic datasets from a declared catalogue of generators, so that fitting and selection variability enter through the distribution of the statistic across datasets.” with:

> Calibration will repeat the declared training fits and held-out scoring on independent synthetic datasets from the frozen generator catalogue.

There is no member selection in this candidate. Its fitting variability is represented through complete-pipeline replication.

**Sources:** `sim_results/interval_diag_2026-10-27/codex/repair_procedure.py`, functions `point`, `calibrate` and `apply`; method-repair record S1 and S3. The record explicitly distinguishes the formal construction from qualification of the new procedure.

### B2. The sensitivity counts are interval decisions, not counts of positive contrasts

**Location:** `paper:sections/results.tex:240`, the two sentences beginning “Applied without change…” and “At the smallest gain…”.

The reported numbers reproduce, but their labels do not. At the middle gain all 200 bounded point estimates are positive; 199 intervals give mixture calls. At the smallest gain, M3H has **50/50 positive points but 0/50 mixture calls**, and M3V has **32/50 positive points but 0/50 mixture calls**. M3 has 50 positive points but 49 calls. `repair_evidence.json` records `positive_calls`, and `apply` requires the interval/critical-value rule.

**Exact replacement sentences:**

> Applied without changing the calibration, the development rule made mixture calls in 199 of 200 saved datasets at the original gain of 0.01~nat. It made 200 of 200 calls at 0.03~nat. At 0.003~nat, the counts were 49 of 50 for M3, 50 of 50 for M3L, and zero of 50 each for M3H and M3V.

Replace the next sentence, “Bounding the scores therefore costs sensitivity at the weakest effects, where the interval's width is set by the hardest graded setting,” with:

> The changed comparison lost sensitivity at the weakest threshold-varying and unequal-variance alternatives.

The screen changes the predictor comparison, statistic, target and interval together. It does not isolate clipping as the cause of the loss relative to the original selected-member rule. Nor is the total interval width fixed by one setting: its lower deviation comes from the omega=1 cell and its upper deviation from the alpha=0 cell.

**Sources:** `codex/repair_evidence.py`, `repair_evidence.json` and `repair_procedure.py` in the diagnostic directory; method-repair record S2. Independent read-only rescoring of all 600 source rows reproduces the counts above. The gains remain the original generating-density gains, not values of the bounded statistic.

### B3. The first proposed study still points to the historical primary algorithm and a graded-family verdict

**Locations and exact replacements:**

- `paper:sections/methods.tex:53`, “The model study proposes to apply the procedure below at each layer, and the simulation audit runs the same procedure on synthetic data.” Replace with:

  > The procedure below is the algorithm used in the completed simulation audit.

- `paper:sections/methods.tex:122`, “Procedure~\ref{proc:layer} is to be applied to R1 on held-out confirmation concepts.” Replace with:

  > The proposed first model study will apply the bounded comparison of Section~\ref{sec:m-amend} to R1 at layer~41 on held-out confirmation concepts.

  Replace the following access sentence with:

  > An access interpretation still requires separately qualified target-readout and causal tests.

- `paper:sections/appendix.tex:8`, “This material specifies the proposed model study summarized in \MTproposed.” Replace with:

  > This material records the broader protocol draft for which the audited procedure was built. The proposed first qualification is now the one-layer coherence comparison described in the article's Methods. The band, target-readout and causal analyses below require separate qualification.

- `paper:sections/appendix.tex:11`, “Layers 0--62 are to be analysed.” Replace with:

  > The earlier draft proposed analyses at layers 0--62.

- `paper:sections/appendix.tex:21`, the sentence beginning “A confirmatory trial receives a state from the posterior occupancy of the training-selected mixture member…”. Replace with:

  > The earlier draft specified state assignment from a training-selected mixture member fitted on the other folds. It assigned $\hat s = \mathrm{H}$ when $\Pr(S = \mathrm{H} \mid y,k) > 0.9$ and $\hat s = \mathrm{L}$ when that probability was below 0.1. A later extension must specify and qualify state assignment for the ensemble comparison.

  These 0.9/0.1 thresholds describe the earlier member-based proposal; they are not an adopted ensemble state-assignment rule.

- `paper:sections/appendix.tex:26`, “Three intervention layers in the workspace band are to be chosen on CAL, never on CONF, as the layers with the largest calibration-set band statistic, the largest being the reference layer.” Replace with:

  > The earlier draft proposed choosing three intervention layers on CAL using the calibration-set band statistic.

- `paper:sections/appendix.tex:28`, “The target bridge is \MTproc{} run on $y^{(2)}$ instead of $y^{(1)}$, together with the requirement that $\hat s$ assigned from $y^{(1)}$ predicts $y^{(2)}$ at fixed dose.” Replace with:

  > A later target bridge requires a separately qualified R2 comparison. It also requires the R1-assigned state to predict R2 at fixed dose.

- `paper:sections/appendix.tex:34`, “\emph{Mixture support}, \emph{graded support} or \emph{inconclusive} by \MTdecision{} on R1, in the active condition with the active-trained decoder, is to be the one primary result.” Replace with:

  > The first proposed study reports mixture preference, negative bounded contrast, inconclusive or unavailable under the bounded rule in the article's Methods. Its primary readout is R1 at layer~41 with the active-trained decoder.

  Replace “\emph{Discontinuous access} is to be written only if the same rule also gives mixture support on R2 and the R1-assigned state predicts R2 at fixed dose.” with:

  > An access interpretation requires the separately qualified target bridge and causal evidence described above.

  The same paragraph's technical-failure sentence still refers to a third of the band layers. Replace “It is declared if, on PILOT, the frozen decoder separates the full dose from none with held-out accuracy below 0.75 in more than a third of the band layers.” with:

  > The broader draft defined a decoder failure as held-out PILOT accuracy below 0.75 in more than a third of the band layers. The restricted study still requires its own frozen technical-failure rules.

- `paper:sections/discussion.tex:34`, “\SMdesign{} gives its pre-declared outcomes, and \SMaccounts{} records how a two-state or a graded result on its readouts would bear on each competing account…” Replace that sentence with:

  > \SMdesign{} and \SMaccounts{} record the broader draft and the additional evidence needed to interpret its possible outcomes.

- `paper:sections/discussion.tex:46`, “With the five components declared and audited in advance, and the interval validated, a graded or a two-state outcome would count as evidence about the model.” Replace with:

  > After calibration and independent validation, mixture preference would provide evidence about the declared bounded predictive comparison at the tested readout and design. A negative interval would report a negative bounded contrast.

These are scope repairs, not a request to remove the historical Procedure 1, its expected-score equations, the historical graded-call counts, or the broader scientific questions. Procedure 1 uses five outer folds, inner selection, an expected log-score target and a fixed-score bootstrap. The adopted candidate uses three outer folds, density ensembles, a median target and the additional graded critical value. A negative bounded interval is not a licensed identification of graded truth. The Supplement currently imports the old rule through `si_supplementary.tex:58–59`, which makes its primary-outcome sentence particularly consequential.

**Sources:** method-repair record S1, S3, S5.10–11 and S6; `codex/repair_primary_plan.json`, `repair_primary_local.py` and `repair_procedure.py`.

### B4. Section 2 still gives the new primary contrast an expected-information/proper-score interpretation

The mathematical log-score statements remain valid for the audited procedure. Their scope must be explicit now that the article also presents the clipped contrast and median target.

**Locations and exact replacements:**

- `paper:sections/transfer.tex:36`, “The scoring rule defines the statistic whose expectation is the uncertainty target.” Replace with:

  > The score or contrast defines the study statistic. The estimand names a feature of its distribution across repeated studies.

- `paper:sections/transfer.tex:43`, “The second is a proper scoring rule.” Replace with:

  > The second is the proper log score used by the audited comparison. The bounded development comparison of Section~\ref{sec:r-bounded} uses a clipped contrast with a different interpretation.

  Keep the following statements about strict propriety of the **unclipped** log score.

- `paper:sections/transfer.tex:45`, “The third is an estimand that is itself an information quantity.” Replace with:

  > The third is the expected cross-entropy difference targeted by the audited interval. The bounded comparison instead targets the median study contrast across repetitions of its declared design.

  In the following sentence replace “The interval's target” with “The audited interval's target”; its equation reference remains the historical expectation.

- `paper:sections/transfer.tex:47`, “All quantities in this paper are Shannon quantities of conditional readout distributions.” Replace with:

  > The audited log-score comparison and the fitted-channel information quantities use Shannon definitions. The bounded development contrast has no expected-cross-entropy or KL-divergence interpretation.

The retained equations in `theory.tex:47–67` describe the original statistic, selection and expectation. They need not be rewritten as though the historical audit used the repair. Add this exact scope sentence at `paper:sections/theory.tex:13`, after the definition-stage description:

> The bounded comparison developed later in Section~\ref{sec:m-amend} changes the predictors, fitting, statistic, target and decision rule.

**Sources:** method-repair record S1 and S6; the clipping operation in `codex/repair_procedure.py:point`. Normalized density ensembles remain predictive densities; clipping the log-score difference does not retain strict propriety or the KL identity.

### B5. The final Results qualification assigns the local fits to the wrong design

**Location:** `paper:sections/results.tex:244`, “These screens concern a changed target and an earlier design: eight families of eight concepts and, on the saved rows, the original members.”

Only the saved-row screen used eight families of eight. The initial five-fold local fits, the paired start checks and the selected three-fold examples all used the three-stratum 27/22/15 profile. The current sentence understates what was actually developed and contradicts the sources.

**Exact replacement sentences:**

> The saved-row screen used the earlier design of eight families of eight concepts and the original predictor members. The local member and start-recipe checks used three strata of 27, 22 and 15 concepts. The local point comparisons do not validate the proposed interval.

Keep the next two sentences about choosing the bound on saved rows and the calibration and validation that a confirmatory decision still requires.

**Sources:** `codex/repair_local_plan.json`, `repair_local.py`, `repair_starts.py`, `repair_primary_plan.json` and `repair_primary_local.json`; method-repair record S2.

### B6. Calibration status is stated both ways without distinguishing the saved prototype from the intended procedure

**Locations and exact replacements:**

- `paper:sections/methods.tex:129`, “No coverage result from it is reported here, and none of the three changes has been calibrated.” Replace with:

  > No coverage result from the retired screen is reported here. The proposed three-fold procedure with the new scale member still requires calibration and independent validation on new seeds.

- `paper:sections/results.tex:67`, “The amendments under development… have not been calibrated, and the band rule… has its own later stage.” Replace with:

  > The proposed bounded procedure still requires calibration and independent validation at the intended design. A workspace-band comparison requires separate qualification.

- `paper:sections/discussion.tex:37`, “The changes to the procedure under development… have not been calibrated.” Replace with:

  > The proposed three-fold procedure with the new scale member still requires calibration and independent validation on new seeds.

- `paper:sections/discussion.tex:16`, “The developed candidate is a bounded comparison calibrated by simulation of the complete procedure…” Replace with:

  > Calibration on saved simulation rows supported a bounded comparison as a candidate for independent validation (Section~\ref{sec:r-bounded}).

- `paper:sections/introduction.tex:34`, “A bounded comparison calibrated by simulation passed development screens on the saved rows…, and its validation on new seeds is what a confirmatory decision still requires.” Replace with:

  > Saved simulation rows supported development of a bounded comparison (Section~\ref{sec:r-bounded}). A confirmatory decision still requires calibration and validation of the proposed procedure on new seeds.

The sources support actual calibration of the **old four-versus-four saved-row ensemble**, followed by development assessment. They do not support calibration of the M3S/expanded-start/three-fold candidate. Both statements can be reported positively and precisely. “Passed” also suggests a fixed acceptance gate for a cap chosen during development; the observations support the candidate without that suggestion.

**Sources:** `codex/repair_evidence.json` scope and calibration counts; `repair_primary_plan.json`; method-repair record S1–S3.

### B7. Several absolute absence claims now contradict the new member/generator development

**Locations and exact replacements:**

- `paper:sections/results.tex:205`, “Detection of a two-state process whose concepts differ in scale is untested, and these rates establish no sensitivity beyond the tested generators.” Replace with:

  > Sensitivity of the expanded procedure to two-state concepts with different scales still requires independent validation. The historical rates establish no sensitivity beyond their tested generators.

- `paper:sections/results.tex:212`, “That member can absorb… while no mixture member has an analogous random scale…” Replace with:

  > In the audited predictor families, M2S could absorb an atypical held-out concept scale, while the mixture members lacked that effect.

- `paper:sections/discussion.tex:37`, “The audit's four mixture generators carry no concept-level scale heterogeneity, which only the graded family can represent…” Replace with:

  > The audit's four mixture generators carried no concept-level scale heterogeneity. Only the audited graded family could represent that variation (Section~\ref{sec:r-sens}).

- `paper:sections/supplement_audit.tex:50`, “The graded member M2S integrates over that scale, but no mixture member has a concept random scale…” Replace with:

  > In the audited comparison, M2S integrated over the concept scale and the mixture predictors lacked that effect (Section~\ref{sec:t-families}).

- `paper:sections/supplement_audit.tex:52`, “None is part of this version.” Replace with:

  > Section~\ref{sec:r-bounded} reports development checks of the scale member, scale-varying mixture data and bounded contrast. Their combined use still requires calibration and independent validation at the intended design.

The preceding Supplement sentence can continue to explain that these changes require their own calibration. The absence claims must describe the historical audit, not all work in the present article. The single-dataset scale examples supply development observations, not a detection probability.

**Sources:** `codex/repair_local.py`, `repair_local.json`, `repair_primary_local.py` and `repair_primary_local.json`; method-repair record S2 and S5.8.

## Non-blocking findings and checks

1. **The new numerical evidence otherwise checks.** Independent read-only calculation from `calibration_D4.csv` reproduces all twelve corrected inclusion rates, including 0.921 and 0.902 and the four residual rates 0.849/0.877/0.806/0.223. The same check reproduces the twelve 700/300 partition assessments: nine cells have 300 inclusions, three have 299, and all 3,600 assessment intervals are negative. The source selection counts are M3V-only 644, M3H-only 46, mixed 310, with M2H selected throughout. The local outputs support 0.700236→0.059063, -0.017826→+0.021862, the 33.637843-nat start improvement, and -0.019356/+0.018076 under the chosen recipe. The manuscript's rounding is correct. All 135 initial and 54 selected-procedure retained fits met the recorded convergence criterion; this is not a global-optimum claim. Sources: `codex/reproduced.json`, `repair_evidence.json`, `repair_finish.json`, the original local outputs and their producing scripts. Input SHA-256 values match `7762f152…9211babb` and `e4310e79…182fcdc` in the two records.

2. **Retirement is described correctly.** `methods.tex:129` says spending stopped before coverage was computed and preserves completed records under the original declaration. That agrees with the final section of `chpc/ROW19_SCREEN_DECLARATIONS.md` at RSC `7238698`. Nothing in the new text reports an observed coverage failure of the omega=1 screen. Preserve that distinction. No screen outputs were opened or released in this review.

3. **Abstract and Table 3 can retain their historical results.** `si_submission.tex:45` still leads with the completed calibration audit and holds the model application. It does not claim the repaired comparison is validated. Table 3, `sections/transfer.tex:179–189` (`tab:transfer`), reports the costs measured in the original audit; its 4–13%, 3.3-fold and six-setting figures are not repaired-procedure performance claims. No number in that table needs replacing. A useful caption clarification is “The five components the audited procedure declares…” in place of “The five components the procedure declares…”.

4. **Keep the constructive conclusion, with a prospective verb.** At `paper:sections/discussion.tex:46`, replace “The first study therefore validates the bounded comparison…, which passed development screens…” with:

   > The first study will test whether the bounded comparison of Section~\ref{sec:m-amend} meets its pre-declared inclusion, safety and sensitivity thresholds.

   The next sentence already supplies the intended design and challenge generators. The final paragraph's correspondence claim remains conditional on the bridge and causal evidence. No new negative catalogue of unrelated study limitations is needed. The suggested changes follow the owner's plain-prose directions in `project_knowledge/rsc_paper_submission_lessons.md` §13.1: concrete results first, one claim per sentence, and unmet conditions stated as what a decision still requires.

5. **Clarify the remaining start-policy sentence.** `paper:sections/methods.tex:125` still says the paired scale-member comparison “is outstanding.” The round-2 check resolved the recipe choice for the new outer-only estimator; it did not settle the complete older nested-selection start policy. Replace that sentence with:

   > Adoption of the earlier nested-selection start policy still requires its own paired assessment and complete-procedure validation, including failure rates and computational cost.

   Keep `results.tex:242` as the measured reason for the new candidate's added starts. Source: method-repair record S2 and S5.13.

6. **The finite-stratum interpretation is materially improved.** `results.tex:210` correctly limits the 7/8 identity to fixed independent scores and separates it from fitting covariance. The new selection-switch sentence also correctly avoids assigning the remaining deficit to parameter fitting alone. The pooled SE column in `tab:unit` is still labelled as pooled; it has not been silently converted into the unbiased stratified estimate. The older `transfer.tex:56` sentence “Whether the concept is an adequate unit is then an empirical question, which Section… answers” remains broader than this check warrants. A clearer exact replacement is:

   > Section~\ref{sec:r-unit} checks the fixed-score uncertainty estimate against replication while retaining the concept as the sampling unit.

7. **The source commit is real; make the archive exclusions equally precise.** The cited full RSC hash `ad5480547eb699f435f50614def5d06adf9a0747` contains the two records and the scripts/JSON outputs used here. They match the local tracked sources. `availability.tex:34` correctly identifies the finite-stratum result and bounded screens as post-version-2 work needing an additional archive. No publication action is needed for this text review, and no remote/public-release status was checked.

   Three generic older archive sentences now need narrower wording to agree with that explicit disclosure:

   - `paper:sections/availability.tex:20`, “So do the development interval and timing summaries of Section…”:

     > Version~2 also contains the earlier refitting-interval comparisons and timing summaries listed below.

   - `paper:sections/availability.tex:36`, “Version~2… archives the analyses listed above.”:

     > Version~2~\cite{study_snapshot_v2}, with version DOI \href{https://doi.org/10.5281/zenodo.23513442}{10.5281/zenodo.23513442}, archives the analyses listed in the version-2 items above.

   - `paper:si_submission.tex:114`, “So do the development screens of the bounded comparison…”:

     > The finite-stratum diagnostic (Section~\ref{sec:r-unit}) and bounded-comparison development screens (Section~\ref{sec:r-bounded}) also postdate version~2 and require an additional archived release.

   These are consistency edits; they do not require completing the held experiment or claiming an archive already exists.

Review boundary: no manuscript edit, remote action, new simulation, fit, publication action, message to another agent or commit. Only this review record is added to the repository. Verification used saved files and a temporary read-only rescoring script.

VERDICT: Revise before acceptance; the evidence supports the development repair, but probability scope, decision labels and the manuscript's primary-design definitions need correction before the text is consistent.

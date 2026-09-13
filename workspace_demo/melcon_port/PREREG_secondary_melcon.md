# DRAFT v2 — pre-registration of the secondary human analysis on Melcón et al. 2024 (OpenNeuro ds006171)

**Status: DRAFT v2 for the owner's review (2026-09-13), rewritten after Codex's critical read of v1
(`../t1_access/reviews/2026-09-13_cheap_cloud_runs_and_melcon_codex_record.md` §B, RSC 326f216). Nothing
has been run on EEG: no recording of ds006171 has been decoded, averaged, contrasted or plotted; every
number quoted is from the behavioural events tables (`INVENTORY.md`) and the BDF headers. Metadata,
behaviour and loader QC have been inspected; the implemented protocol is frozen before any EEG decoding,
neural condition contrast or model result is examined, and later changes are registered openly.** This is a
**pre-registered secondary cross-modal extension of the distributional assay** of the primary human
analysis (Sergent et al. 2021, auditory; `../sergent_port/`), for the Entropy special-issue paper. It is a
conceptual replication with a changed estimand and readout, stated below, not an exact replication of the
timing, the dose manipulation or the decoder calibration.

## 1. Question and hypotheses

Same question as the primary analysis: near the threshold of report, is the single-trial neural response to a
stimulus better predicted, on held-out data, by a **graded** family (a unimodal distribution whose mean and
spread move continuously with intensity) or by a **two-state** family (a mixture of a "low" and a "high"
state whose occupation probability moves with intensity)? Here intensity is the Gabor contrast set
trial-by-trial by the authors' online staircase (in place of Sergent's five designed SNR levels), every trial
carries a seen/unseen report (the primary analysis reproduces the published comparison in Sergent's
**active, report-required** session; the passive-session comparison is our additional analysis), and the
stimulus is a 50 ms peri-threshold Gabor in one hemifield.

H1 (two-state): the two-state model is preferred under the rule of §6 in the **main interval** on the nocue
task. H0-graded: the graded model is preferred under the same rule. Neither, or both in different windows:
inconclusive/mixed (§7). The question is conditional and predictive; it concerns access to a content under a
report-required visual task and says nothing about report-independence, bistable dynamics, global broadcast
or consciousness (§8).

## 2. Data and inclusion

ds006171: 36 subjects, 104 subject × task recordings (missing on OpenNeuro: sub-01 informative, sub-02
noninformative, sub-35 nocue, sub-36 noninformative). Per recording 400 trials in 4 blocks of 100: 360
Gabor-present (90 per hemifield × orientation) and 40 catch trials (no Gabor), seen/unseen on every trial, an
orientation question on ≈ 15 %. **Primary task: nocue** (35 subjects), no event before the Gabor.
**Within-participant robustness task: informative** (35 subjects; 34 of them also in the nocue sample, so the
two task samples are the same people, not two cohorts), a 100 %-valid spatial cue 0.7–1.0 s before the Gabor.
**The noninformative task is excluded from the intensity analysis**: its contrast column does not behave as the
staircase output of its own trial (INVENTORY §4) and there is no other trial-by-trial intensity measure; it
enters only the exploratory report-conditioned description of §8.

Four BDF files (sub-35 informative and noninformative, sub-36 informative and nocue) were recorded at 2048 Hz
with a 417 Hz acquisition corner; the other 100 at 1024 Hz with a 208 Hz corner (README D13). All are
processed identically (§3).

Trial exclusions, fixed in advance: **present** trials with a non-positive recorded contrast (36, sub-11
informative; catch trials have no contrast); trials failing the artefact rule of §3. Trials without a
seen/unseen response (102 in the dataset) are **retained** in the report-unconditioned neural comparison and
omitted only from report-conditioned summaries; a sensitivity excludes them. Recording exclusions: fewer than
250 present or fewer than 25 catch trials after exclusions, or any outer training/test split (§4) with fewer
than 5 catch trials; this is a transparent provisional rule, not a power guarantee, and it is not relaxed after
model preferences are seen. Subjects contribute a recording per task independently. All exclusion counts are
reported by contrast, hemifield, block, task and report.

## 3. Preprocessing (fixed; implemented in `load.py`; the artefact rule to be implemented before freeze)

BDF → 128 scalp channels renamed from `channels.tsv`, plus the four EOG channels (EXG1–4 → VEOG1/2, HEOG1/2)
kept for rejection only; high-pass 0.4 Hz and 50 Hz notch (Sergent's FieldTrip settings); **an anti-alias
low-pass at 200 Hz (zero-phase FIR, 50 Hz transition band) on every recording before decimation** (v1 had
none; the 2048 Hz files were decimated by 4 against a 417 Hz corner, which aliased the 256–417 Hz band; now
the loader refuses to decimate if the recording's low-pass exceeds the target Nyquist, and suppresses no
warning); common average reference over the 128 scalp channels; epochs −0.5 … +1.0 s around the
**photodiode-corrected** onset, snapped on the raw at its native rate (README D1); baseline −0.5 … 0 s;
decimation to 512 Hz. EOG channels receive the same filters and are never decoder features.

**Artefact rule (fixed; implementation to be verified by blind QC before freeze).** Bipolar traces
VEOG = VEOG1 − VEOG2 and HEOG = HEOG1 − HEOG2 after the same filters. A trial is rejected if any scalp channel
exceeds 150 µV peak-to-peak or VEOG or HEOG exceeds 100 µV peak-to-peak within −0.2 … +0.6 s. Bad channels are
identified before the common average is taken: a channel is bad in a recording if it is flat (peak-to-peak
below 0.5 µV over the recording) or exceeds the 150 µV rule in more than 20 % of trials; at most 12 bad channels
per recording (more → the recording is excluded); bad channels are interpolated by spherical splines on the
BioSemi 128 montage coordinates, the average reference is then recomputed, and the trial rule is applied once
more; the sequence runs twice at most. The −0.2 … +0.6 s screen includes the question display (jittered
+0.30 … +0.40 s), so later ocular behaviour can select trials used in the early analysis; this is stated, and
trial retention is reported by contrast, hemifield, block, task and report. No ICA: a fixed choice that trades
simpler processing for more residual ocular signal and trial loss.

## 4. Decoder — projected activity, with end-to-end block separation

Per recording, **four outer folds by block** (4 blocks of 100 trials). For each outer training set of three
blocks: a presence decoder (`StandardScaler → LogisticRegression(liblinear, C = 1)`, training-fold
`class_weight = 'balanced'`, features the 128 scalp channels only, per time sample) is fitted on those three
blocks and applied to the held-out block, giving every held-out trial a signed decision value per sample from
a decoder that never saw its block. **Training projections** for the likelihood fits of §6 are obtained by an
inner three-fold block cross-fit within the outer training set (each training trial projected by a decoder
fitted on the other two training blocks). Scaling, class weights, readout normalization and likelihood
parameters are all fitted on the outer training set only. Projections of the held-out block and of the
cross-fitted training trials share the scale of the training-set cross-fitted projections (z-scored per
recording and outer fold on the training projections); this scale-sharing rule is examined on the synthetic
recovery cases of §6 because pooling projections with differing offsets or scales can itself manufacture
apparent mixtures. Cross-validation splits and every random seed are fixed here (seed 20260913).

**Training contrast: catch (Gabor absent) versus all Gabor-present trials** (40 : 360), the presence
question with five times the positive examples of the top contrast quintile (72 trials, seen on 0.57–0.63 of
them at ≈ 1.3 × the median contrast, i.e. no supraliminal anchor exists in a staircase design). Sensitivities,
pre-registered: (a) catch vs the top contrast quintile; (b) a decoder trained pooled across a subject's tasks
(more catch trials; shares training information between the task estimates and is therefore not an independent
replication). Decoder performance (held-out AUC per outer fold and window) is reported with its uncertainty for
every variant; no variant is described as under-powered without that measurement.

## 5. Intensity covariate, report, windows

*Intensity.* The **main covariate is continuous log contrast**, centred and scaled on the outer training set;
catch trials are a distinct stimulus-absence indicator with their own density term in both families (§6), never
encoded as a finite dose beside the scaled log contrasts. **Five within-recording contrast quantiles** (with
catch as level 0) are used for plots and for the legacy sensitivity that ports the level-anchored primary
models unchanged; the quantile geometry replaces unequally spaced physical contrasts by equally spaced ranks
and mixes doses within a bin, which is why it is not the main analysis. The authors calibrated separate
hemifield thresholds and set contrast from response history plus random variation, so dose is not a wholly
randomized intervention: hemifield, block and staircase history are nuisance terms treated identically in both
families (hemifield as a fixed effect on location; block as a sensitivity), and no claim is made that a fitted
occupancy curve recovers a unique sensory threshold over an unobserved wide dose range.

*Report.* seen/unseen from the 124/125 triggers (INVENTORY §3), not used in the model comparison, which is
therefore **report-unconditioned** on a **report-required** task (§8).

*Windows.* Projected activity is low-passed at 10 Hz (12th-order Butterworth, forward–backward, the
inherited smoother) and averaged in explicit half-open **30 ms windows on time edges** from −300 to +900 ms
(15 or 16 samples at 512 Hz as the edges require; v1's fixed 16 samples were 31.25 ms). Two intervals,
declared in advance: the **main interval 300–600 ms** (10 windows), which contains the primary analysis's
first pxp > 0.95 window at 315 ms and its stable plateau at 435–495 ms and explicitly tests report-associated
visual processing under the question display (jittered +0.30 … +0.40 s) and response preparation (median
response ≈ 0.93 s); and the **early interval 0–300 ms** (10 windows), a separate early visual analysis. Because
the zero-phase filters spread a step across the 300 ms boundary (a step at 300.8 ms leaves 0.23 of its height in
270–300 ms after the 10 Hz smoother, and the high-pass and notch are non-causal too), the early interval is
not guaranteed to use only pre-question input: the filters' temporal transfer and edge handling are shown by
impulse and step checks, and a **causal-processing sensitivity** (causal filters throughout) accompanies any
statement about activity preceding the question. Adjacent smoothed windows are strongly dependent; "three
consecutive windows" is a persistence convention, not three independent confirmations.

## 6. Models, fitting and group comparison

Model 0 (null): Gaussian, dose-independent. Graded (2B): logistic mean in log contrast with an
**intercept-plus-logistic parameterization** (a fixed, training-derived anchor; v1's port evaluated its upper
anchor from the maximum of each call's own covariate values, so the same parameters predicted differently on
training and test sets), SD linear in the mean. Two-state (3): mixture of N(μ_low, σ) and N(μ_high(x), σ) with a
logistic mixing proportion in log contrast; on **catch trials, identified by the catch flag** (v1's port used the
minimum level of the current subset), the proportion is 0 and the high mean equals μ_low; a fold with no catch
trials in its training set is handled by the unavailable-fold policy below. A **free-catch-occupancy
sensitivity** (proportion at catch a free parameter, as the model-side M3L) is declared, since physical absence
of the Gabor does not by itself establish absence of every internal high state.

**Fitting:** maximum likelihood by a training-only multistart, eight L-BFGS-B starts from training-fold moments
plus seeded jitter, with declared parameter bounds and a scale floor of 0.05 × the training SD of the
projection; a fit counts as converged when the optimizer reports success and the kept solution is the converged
start with the highest training likelihood; the literal inherited recipe (single-start Nelder–Mead from the
original starting points, capped) is a reproduction sensitivity, not the primary fitter (the primary analysis's
diagnostics showed substantial non-convergence and boundary sensitivity under it). Unavailable fold: a model
that cannot be scored on a fold after the multistart is recorded as unavailable for that recording and window;
a recording with any unavailable fold in the main interval is excluded from the group comparison of that
window and counted.

**Evidence:** mean over the four outer folds of the held-out summed log-likelihood, the inherited predictive
convention (not a marginal likelihood). **Group comparison** per window with the `spm_BMS` port
(`../sergent_port/bms.py`): protected exceedance probabilities and BOR over the three models, and two-model
(2B vs 3) BMS as a sensitivity. The pxp is a descriptive convention: **1 − pxp is not a calibrated p-value**, the
step-up correction across windows establishes no frequentist error control, and equal pxp thresholds here and
in Sergent do not represent matched evidence or power (fold-summed evidence scales with retained trials).
Alongside BMS, the **direct held-out log-score difference per trial** between the two families is reported per
window with its participant-level variation and a cluster (participant) bootstrap interval; it is the
quantity that corresponds to the model-side statistic, though the two inferential procedures are not the
same.

**Synthetic recovery checks before any outcome analysis:** on this dataset's dose, block, hemifield and catch
structure, graded generators with heterogeneity and skew, overlapping and separated mixtures, weak decoder
signal and temporal dependence, run through the complete pipeline of §4–§6, to establish that the rule of §7
does not manufacture a family preference from the design; the T1 model-side calibration does not validate this
pipeline.

## 7. Outcomes — exclusive, decided by the rule on the nocue task's main interval

**Rule:** pxp ≥ 0.95 for a model in at least three consecutive windows of the main interval.
1. **Two-state**: the two-state model meets the rule and the graded model does not in any window of the main
   interval. 2. **Graded**: the converse. 3. **Inconclusive/mixed**: neither meets it, or both meet it in
   different windows, or a null-model win; the time courses are shown. 4. **Technical failure** (reported
   separately from insufficient measurement sensitivity): the pipeline cannot be completed (loader, decoder or
   fitter failure) on more than a quarter of the recordings. **Insufficient sensitivity**: median held-out
   decoder AUC (catch vs present) below 0.55 in every window of the main interval in more than half of the
   recordings; then no outcome 1–3 is claimed, and the comparison is reported as uninformative rather than as a
   failure. Recordings are never selected on AUC.
The early interval is reported under the same rule as a separate early visual analysis, and the informative
task beside the nocue task as a within-participant cue-context robustness analysis; agreement strengthens,
disagreement is reported, neither changes the nocue outcome.

## 8. What is and is not claimed

Every task of the dataset requires a report on every trial; there is no no-report condition. Omitting the
report labels from the decoder and the models makes the analysis report-unconditioned, not the experiment
report-free: the report prompt changes the task, and expected reporting can affect activity before the
question appears. A two-state outcome supports **mixture-model preference in a presence readout under a
report-required visual detection task**; it establishes neither report-independent ignition nor bistable
dynamics, global broadcast or consciousness, and a two-component density need not have two visible modes.
Fitted conditional densities and component separation are reported; a graded or inconclusive outcome is bounded
the same way. A claim about the effect of reporting would need a report manipulation and a direct contrast; one
positive and one non-significant result from unlike datasets do not supply it. The informative-versus-nocue
comparison speaks to the pre-stimulus state (attention and expectation), not to report. The noninformative task
is used only for one exploratory, report-conditioned description (the distribution of projected activity for
seen versus unseen trials per window), with no model comparison and no claim.

Not claimed: anything about consciousness beyond the operational report; the authors' alpha-phase and
alpha-amplitude findings; the assignment of the noninformative validity digit (README D2); per-subject
demographics (INVENTORY §1); any equivalence to the language-model analysis, which shares the four-outcome
vocabulary and not the inferential procedure. The decoder decodes stimulus presence, not seeing.

## 9. Deviations from the primary analysis, in one place

Continuous log contrast with catch as an absence indicator (vs designed SNR levels; quantile levels only as
plots and a legacy sensitivity); 40 catch trials per recording (vs ≈ 150); catch vs all-present training,
balanced (vs no-sound vs maximum level); end-to-end block separation with four outer folds and an inner
cross-fit (vs trial-wise ten-fold decoding and five likelihood folds); an intercept-plus-logistic graded mean
and the catch flag in the mixture (vs the inherited anchor and minimum-level identification); an L-BFGS-B
multistart with bounds and a scale floor (vs single-start capped Nelder–Mead, kept as a reproduction
sensitivity); a fixed artefact rule with bipolar EOG and spherical-spline interpolation (vs visual rejection and
ICA); an anti-alias low-pass before decimation and 512 Hz (vs 500); half-open 30 ms time edges (vs 16 samples
stepping by 15 at 500 Hz); a main interval of 300–600 ms and a separate early interval (vs a single window set);
the held-out log-score difference reported beside BMS; 35 subjects per task (vs 20), with 34 shared across the
two tasks. The estimator, the likelihood forms, the 10 Hz smoother, the BMS port and the three-window persistence
convention are unchanged; each deviation above is either a repair of an inherited implementation trap or a
consequence of the design.

## 10. Where it runs, and the manuscript's wording until a result exists

Protocol, loader repair and the synthetic checks on the Mac now (light); the full EEG processing on the PC after
its audit if a verified copy and a matching CPU environment can be prepared, otherwise on the Mac after the
running probe; one recording worker first, peak RAM and runtime measured, then the concurrency chosen; the Mac's
raw-data master stays where it is. No GPU or cloud run is needed. Until an actual secondary result exists the
manuscript says: the human reference analysis reproduces the published distributional model comparison in the
active session of the Sergent auditory dataset; a separate analysis of its passive session examines the same
candidate models; a secondary visual analysis is planned on Melcón et al.'s report-required detection dataset,
with its protocol finalized before neural outcome analysis; it tests the assay's generalization across modality
and task and does not isolate the effect of reporting. "Pre-registered" is used only after the freeze is
recorded.

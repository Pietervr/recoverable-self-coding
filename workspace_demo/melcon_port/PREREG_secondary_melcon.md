# DRAFT v3 — the planned secondary human analysis on Melcón et al. 2024 (OpenNeuro ds006171)

**Status: DRAFT v4 in progress (2026-09-13), after Codex's three reads of v1–v3
(`../t1_access/reviews/2026-09-13_cheap_cloud_runs_and_melcon_codex_record.md` §B, "Continuation review 2" and
"Continuation review 3"). §3 is revised and implemented (`preprocess.py`, V3.1–V3.2); the revisions of §2 and
§4–§9 for V3.3–V3.6 follow.
Nothing has been run on EEG: no recording of ds006171 has been decoded, averaged, contrasted or plotted;
every number quoted is from the behavioural events tables (`INVENTORY.md`), the BDF headers and synthetic
checks. Metadata, behaviour and loader QC have been inspected. The implemented protocol, its executable
configuration and the results of the synthetic battery of §9 are frozen together before any EEG decoding,
neural condition contrast or model result is examined; later changes are registered openly. Until that
freeze is recorded this is a *planned* secondary cross-modal extension of the distributional assay of the
primary human analysis (Sergent et al. 2021, auditory; `../sergent_port/`): a conceptual replication with a
changed estimand and readout (§11), not an exact replication of the timing, dose manipulation or decoder
calibration.**

## 1. Question and hypotheses

Same question as the primary analysis: near the threshold of report, is the single-trial neural response to a
stimulus better predicted, on held-out data, by a **graded** family (one state whose location and spread move
continuously with intensity) or by a **two-state** family (a mixture of a low and a high state whose occupation
probability moves with intensity)? Here intensity is the Gabor contrast set trial-by-trial by the authors'
online staircase (in place of Sergent's five designed SNR levels); every trial carries a seen/unseen report
(the primary analysis reproduces the published comparison in Sergent's **active, report-required** session,
and its passive-session comparison is our additional analysis); the stimulus is a 50 ms peri-threshold Gabor in
one hemifield.

H1 (two-state) and H0-graded are the two family outcomes of the total decision rule of §8 on the nocue task's
main interval; the remaining combinations are inconclusive/mixed. The question is conditional and predictive:
it concerns access to a content under a report-required visual task and says nothing about
report-independence, bistable dynamics, global broadcast or consciousness (§10).

## 2. Data and inclusion

ds006171: 36 subjects, 104 subject × task recordings (missing on OpenNeuro: sub-01 informative, sub-02
noninformative, sub-35 nocue, sub-36 noninformative). Per recording 400 trials in 4 blocks of 100: 360
Gabor-present (90 per hemifield × orientation) and 40 catch trials (no Gabor), seen/unseen on every trial, an
orientation question on ≈ 15 %. **Primary task: nocue** (35 subjects), no event before the Gabor.
**Within-participant robustness task: informative** (35 subjects; 34 of them also in the nocue sample, the same
people, not a second cohort), a 100 %-valid spatial cue 0.7–1.0 s before the Gabor. **The noninformative task is
excluded from the intensity analysis**: its contrast column does not behave as the staircase output of its own
trial (INVENTORY §4) and there is no other trial-by-trial intensity measure; it enters only the exploratory
report-conditioned description of §10.

Four BDF files (sub-35 informative and noninformative, sub-36 informative and nocue) were recorded at 2048 Hz
with a 417 Hz acquisition corner; the other 100 at 1024 Hz with a 208 Hz corner (README D13). All are processed
identically (§3).

Trial exclusions, fixed in advance: **present** trials with a non-positive recorded contrast (36, sub-11
informative; catch trials have no contrast); trials failing the artefact rule of §3. Trials without a
seen/unseen response (102 in the dataset) are **retained** in the report-unconditioned neural comparison and
omitted only from report-conditioned summaries; a sensitivity excludes them. Recording exclusions: fewer than
250 present or fewer than 25 catch trials after exclusions; more than 12 bad channels in any block (§3); any
decoder half (§4) with fewer than 10 catch trials; or any block with fewer than 3 catch trials or fewer than 20
present trials in either hemifield after exclusions, since every block serves as a likelihood training block that
must estimate the catch moments and the hemifield term (§5–§6). At the events-table level only sub-36 nocue fails
the block floor, and it is excluded outright, before any EEG is examined: its trial order was sorted rather than
randomised, confounding hemifield, orientation, catch status and position with block (README D14). These are transparent provisional rules, not power
guarantees, and they are not relaxed after model preferences are seen. Subjects contribute a recording per task
independently. Exclusion and retention counts are reported by contrast quintile, hemifield, block, task and
report.

## 3. Preprocessing (fixed; implemented in `preprocess.py` and checked on artificial recordings; no EEG outcome examined)

**Loader (`load.py`).** BDF → the 128 scalp channels and the four EOG channels (EXG1–4 → VEOG1/2, HEOG1/2),
typed. Electrode positions come from MNE's standard `biosemi128` montage attached to the **original** BioSemi
names A1…D32 and kept through the position-preserving rename to the `channels.tsv` names; literal matching of the
renamed labels to the montage would miss most of them and could take a position from an accidentally overlapping
name (this checks the name plumbing, not the physical cap). Onsets are **photodiode-corrected** and snapped to the
Status channel at the native rate (README D1, D3). The loader's own recording-wide filtering serves only the
epoch-count verification in `results/load_verification.csv` (historical 128-channel rows beside two revised
132-channel rows); the all-recording verification is re-run through `preprocess.py` on the processing machine
before the freeze and replaces that file. `load.py` writes no cache.

**Block-local segments.** Each recording is cut into one continuous segment per block. The cut between blocks b
and b+1 is the sample midway between the end of block b's last epoch (onset + 1.0 s) and the start of block
b+1's first epoch (onset − 0.5 s); the first segment starts at the recording's first sample and the last ends at
its last. **Every step below runs inside one segment.** The reason is filter support: the 0.4 Hz high-pass (MNE
FIR, 8,449 taps at 1024 Hz, 8.25 s of support, 4.125 s each side) and the 50 Hz notch (6.6 s) are non-causal, and
boundary onset gaps are as short as 2.643 s (sub-01 nocue, blocks 2 → 3; 15 of the 210 gaps in the included tasks
are below 9.75 s), so a recording-wide filter carries one block's samples into another block's epochs (Codex,
continuation review 3, V3.1). In the artificial check a 30 µV step placed after the cut moves the previous
block's last epoch by up to 10.7 µV under recording-wide filtering and leaves it bit-identical under block-local
filtering. Segment edges are padded by MNE's `reflect_limited`; a trial whose epoch lies within 4.125 s of a
segment edge is flagged `edge_trial`, and a sensitivity excludes those trials.

**Steps inside a segment.** (i) High-pass 0.4 Hz, notch 50 Hz and an **anti-alias low-pass at 200 Hz** on the
scalp and EOG channels (FIR, firwin, Hamming window, zero phase, automatic lengths and transition bands, as MNE
1.13's defaults, named explicitly); measured attenuation of the low-pass ≈ 53 dB at 256 Hz and ≈ 59 dB at 300 Hz
at both native rates. v1 had no low-pass and decimated the four 2048 Hz files by 4 against a 417 Hz acquisition
corner with the warning suppressed: a missing protection, the amount of aliasing in real EEG not measured.
(ii) **Channel QC.** A scalp channel is *flat* if its peak-to-peak amplitude over the segment is below 0.5 µV, and
*noisy* if it exceeds 150 µV peak-to-peak within −0.2 … +0.6 s in more than 20 % of the block's trials
(denominator: every trial of the block in the events table), measured after subtracting the per-sample median of
the 128 scalp channels inside each window — a detection reference only, because BioSemi data are recorded against
CMS/DRL and carry common-mode activity until re-referenced (the artificial check puts 200 µV peak-to-peak of common
mode on every channel and marks nothing). EOG channels are never marked bad. (iii) Bad scalp channels are
interpolated by spherical splines (MNE `interpolate_bads`, mode `accurate`, origin `auto`). (iv) Common average
reference over the 128 scalp channels. (v) Epochs −0.5 … +1.0 s around the photodiode-corrected onset, baseline
−0.5 … 0 s, decimation to 512 Hz (769 samples). MNE's decimation guard warns whenever the output rate is below
three times the low-pass (512 < 600); it is a cutoff-only heuristic, fires at both native rates, and is left
visible, not read as evidence of aliasing. (vi) **Trial rejection:** any scalp channel above 150 µV, or the
bipolar VEOG = VEOG1 − VEOG2 or HEOG = HEOG1 − HEOG2 above 100 µV, peak-to-peak within −0.2 … +0.6 s. The sequence
ends there. DRAFT v3's second channel pass on the retained trials is removed: a retained trial has no scalp
channel above the same 150 µV, so that pass could flag a channel only through the small difference between the
median detection reference and the average reference — it was empty by construction, not a safeguard.
A recording is **excluded** when any block's bad set exceeds 12 channels.

**Isolation, and what it is conditional on.** Given a recording's inclusion, every transformation of a block's
samples — filters, channel QC, interpolation, reference, epochs, trial rejection — depends only on that block's
raw segment and the fixed constants: changing the EEG of one block changes no other block's epochs, QC decisions
or retention (checked exactly on artificial recordings, `test_preprocess.py`). The recording-level exclusion
above and the recording floors of §2 are label-free decisions that see every block. The −0.2 … +0.6 s screen
includes the question display (jittered +0.30 … +0.40 s), so later ocular behaviour can select trials used in the
early analysis; retention is reported by contrast quintile, hemifield, block, task and report. No ICA: a fixed
choice that trades simpler processing for more residual ocular signal and trial loss.

**Cache.** `preprocess.py --cache` writes the only cache the analysis reads. It stores the complete preprocessing
configuration (every constant, the library versions, and the digests of `preprocess.py`, `load.py` and `common.py`
as loaded), a SHA-256 over the stored payload, and the channel names and types; `read_cache` refuses a file whose
configuration differs from the running one, whose checksum fails, whose types are not the 128 `eeg` channels
followed by the four EOG channels, or which lacks these fields (every pre-v4 cache). The decoder selects the 128
channels typed `eeg`; the EOG channels are **never decoder features**.

## 4. Decoder — split-half design with matching readouts

Per recording, the four blocks are paired into two halves, H1 = {1, 2} and H2 = {3, 4}. For each half A as the
**decoder half**: a presence decoder (`StandardScaler → LogisticRegression(liblinear, C = 1)`, training-half
`class_weight = 'balanced'`, features the 128 scalp channels, per time sample) is fitted on all trials of A and
applied to every trial of the other half B, giving each B trial a signed decision value per sample from a
decoder that never saw its half. The **likelihood comparison of §6 then runs entirely inside B**, as a two-fold
block cross-validation (train on one block of B, test on the other, both ways), on projections that all come
from the one decoder fitted on A: the likelihood's training and test projections therefore share one readout
and one scale by construction, which the nested cross-fit of v2 did not give (three two-block decoders and a
three-block decoder need not agree in offset or scale, and pooling their scores does not align them). Swapping
the roles of the halves gives every block a held-out likelihood score; the four held-out block scores are the
recording's four folds. Isolation check, run on synthetic data before the freeze: changing only the EEG or
labels of a held-out block changes neither the decoder that scores it, nor the likelihood parameters that
predict it. Cross-validation splits and every random seed are fixed here (seed 20260913).

Projections are z-scored per recording, half and time sample using the mean and SD of the decoder half's
**in-sample** projections of that decoder (a training-only affine transform, identical for every B trial); the
10 Hz smoother of §5 is applied after the z-score and before windowing. The decoder half has ≈ 200 trials with
≈ 20 catch trials, which is why the catch floor of §2 applies to halves.

**Training contrast: catch (Gabor absent) versus all Gabor-present trials** of the decoder half (≈ 20 : 180),
the presence question with five times the positive examples of the top contrast quintile (no supraliminal
anchor exists in a staircase design: the top quintile is seen on 0.57–0.63 of trials at ≈ 1.3 × the median
contrast). Sensitivities, each with its own declared split: (a) catch vs the decoder half's top contrast
quintile (threshold from the decoder half only); (b) a decoder trained on the same half of **both** of a
subject's tasks (nocue and informative), applied to the other half of each task, with the likelihood folds as
above — it shares training information between the two task estimates and is not an independent replication.
Held-out decoder AUC per half, window and variant is reported with a bootstrap interval; no variant is called
under-powered without that measurement.

## 5. Intensity covariate, nuisance terms, windows

*Intensity.* The main covariate is **continuous log contrast**, x = (log c − m)/s with m and s the mean and SD
of log contrast over the present trials of the likelihood training block(s) of the fold; catch trials carry the
indicator κ = 1 and no x. Five within-recording contrast quantiles (catch as level 0) are used for plots and for
the legacy sensitivity that ports the level-anchored primary models unchanged.

*Nuisance.* Hemifield h ∈ {left, right} enters both families as an additive location shift β (β = 0 for left,
free for right), the same term in the graded mean and in both mixture means; the authors calibrated separate
hemifield thresholds (metadata: median left/right median-contrast ratio 1.09, maximum 1.56). Blocks are the
folds and carry no covariate in the main analysis; the **block sensitivity** adds a per-block location shift γ_b
fitted on training blocks and predicts a held-out block with the mean of the training blocks' γ (the only rule
that needs no test information). Staircase history enters no model; the analysis is conditional on the
realized contrasts, and no claim is made that a fitted occupancy curve recovers a sensory threshold over an
unobserved dose range.

*Report.* seen/unseen from the 124/125 triggers (INVENTORY §3), not used in the model comparison, which is
therefore **report-unconditioned** on a **report-required** task (§10).

*Windows.* Projected activity is low-passed at 10 Hz (12th-order Butterworth, forward–backward, the inherited
smoother) and averaged in half-open **30 ms windows on time edges** from −300 to +900 ms (15 or 16 samples at
512 Hz as the edges require). Two intervals: the **main interval 300–600 ms** (10 windows), which contains the
primary analysis's first pxp > 0.95 window at 315 ms and its plateau at 435–495 ms and tests report-associated
visual processing under the question display (jittered +0.30 … +0.40 s) and response preparation (median
response ≈ 0.93 s); and the **early interval 0–300 ms** (10 windows), a separate early visual analysis. The
zero-phase filters spread a step across the 300 ms boundary (a step at 300.8 ms leaves 0.23 of its height in
270–300 ms after the smoother; the high-pass and notch are non-causal too): the filters' step and impulse
responses are shown, and a **causal-processing sensitivity** (causal filters throughout) accompanies any
statement about activity preceding the question. Adjacent smoothed windows are strongly dependent; three
consecutive windows is a persistence convention, not three independent confirmations.

## 6. Models — the densities, exactly

For a trial with projection y, scaled log contrast x (present trials) or catch indicator κ, hemifield shift β,
and lg(z) = 1/(1 + e^{−z}):

**Model 0 (null):** y ~ N(μ0 + β, σ0²).

**Graded (2B'):** y ~ N(μ(x) + β, σ(x)²), μ(x) = a0 + a1 · lg(k (x − x0)), σ(x) = exp(s0 + s1 (μ(x) − a0)).
The intercept a0 is the low-dose asymptote, a1 the range, x0 the threshold, k the slope; the SD is
log-linear in the mean (the inherited "SD linear in the mean" made positive by the exponential), so no
absolute-value trick and no test-derived anchor (v1's port re-evaluated its upper anchor from each call's own
maximum x). **Catch density:** the x → −∞ limit of the same law, y ~ N(a0 + β, exp(s0)²), with no extra
parameter (catch is the dose-absent limit, as in the primary analysis's lowest level).

**Two-state (3'):** y ~ (1 − A(x)) N(μ_L + β, σ²) + A(x) N(μ_H(x) + β, σ²), A(x) = lg(k_A (x − x0)),
μ_H(x) = μ_L + exp(δ0) + exp(δ1) · lg(k_h (x − x0)), so that the high state sits above the low state at every
dose by at least exp(δ0). **Catch density:** A = 0, y ~ N(μ_L + β, σ²), identified by the **catch flag** (v1's
port used the minimum level of the current subset). **Free-catch-occupancy sensitivity (3'L):** on catch
trials A = π0 = lg(θ0) free and the high component N(μ_L + exp(δ0) + β, σ²), i.e. the catch high mean is
displaced by the same exp(δ0) that separates the components elsewhere; with δ0 finite the mixture is
identifiable and π0 is read with its interval (v2 kept μ_H = μ_L at catch, which made π0 unidentifiable).

**Parameters and bounds (on the scaled x; the projection's training SD is S):** a0, μ0, μ_L ∈ [−5S, 5S];
a1 ∈ [0, 10S]; x0 ∈ [−4, 4]; k, k_A, k_h ∈ [0.05, 20]; s0 ∈ [log(0.05S), log(5S)]; s1 ∈ [−2, 2]/S; σ ∈ [0.05S,
5S]; δ0, δ1 ∈ [−5, log(10S)]; β ∈ [−3S, 3S]; θ0 ∈ [−6, 3]. **Starts:** one moment start per model (a0 or μ_L from
the training catch mean; a1 or exp(δ0) from the difference between the top and bottom contrast-quintile means;
x0 = 0; k = 1; s0 = log(training catch SD); s1 = 0; σ = training pooled SD; β = right-minus-left mean of the
training projections) plus **seven jittered starts** (Gaussian jitter, SD 0.25 in each bounded coordinate after
mapping to the unbounded scale), eight in all; **optimizer** L-BFGS-B with ftol 1e-10, gtol 1e-6, maxiter 2000
(the model-side settings); a fit counts as converged when the optimizer reports success, and the kept solution is
the converged start with the highest training likelihood; the number of starts reaching the kept solution
within 0.5 nat is recorded. The literal inherited recipe (single-start Nelder–Mead from the original starting
points, capped) is a reproduction sensitivity. **Unavailable fold:** a model with no converged start on a fold is
unavailable for that recording and window, and the recording is dropped from that window's group comparison
and counted (§8).

## 7. Evidence and group comparison

Per recording and window, **evidence** for each model = mean over the four held-out blocks of the block's
summed held-out log-likelihood (the inherited predictive convention, not a marginal likelihood). **Group
comparison** per window with the `spm_BMS` port (`../sergent_port/bms.py`): protected exceedance probabilities
and BOR over the three models, and two-model (2B' vs 3') BMS as a sensitivity. The pxp is a descriptive
convention: **1 − pxp is not a calibrated p-value**, the step-up correction across windows establishes no
frequentist error control, and equal pxp thresholds here and in Sergent do not represent matched evidence or
power (fold-summed evidence scales with retained trials).

Alongside BMS, the **held-out log-score difference per trial** Δ = (ℓ_3' − ℓ_2B')/n, computed per recording and
window over its held-out trials, is reported with (i) the median and interquartile range across recordings and
(ii) a **participant bootstrap** interval: the statistic is the mean of the per-recording Δ (equal weight per
recording), B = 2,000 resamples of participants with replacement, seed 20260913, each resampled participant
carrying its full time course and both its tasks together, percentile interval. It is the quantity that
corresponds to the model-side statistic; the two inferential procedures are not the same.

## 8. Outcome rule — a total decision function on the nocue task's main interval

Let W be the ten main-interval windows. A window is **eligible** if at least 20 recordings have all three
models available on all four folds in it (§6); recordings with any unavailable model in a window are dropped
from that window only, and every window's group comparison uses exactly its eligible recordings, whose count is
reported. Define R_3 = "the two-state model has pxp ≥ 0.95 in at least three consecutive eligible windows of W",
R_2B likewise for the graded model, and R_0 likewise for the null model. Isolated windows do not block a run.
Then:

1. **Two-state**: R_3 ∧ ¬R_2B. 2. **Graded**: R_2B ∧ ¬R_3. 3. **Inconclusive/mixed**: ¬R_3 ∧ ¬R_2B, or
R_3 ∧ R_2B (both families run somewhere in W); R_0 changes nothing (a null run beside a family run is reported;
a null run alone is case 3); the time courses are shown in every case.
4. **Technical failure** (evaluated first): the pipeline cannot be completed (loader, preprocessing, decoder
or fitter failure not covered by the unavailable-fold rule) on more than a quarter of the recordings that pass
§2, or fewer than 20 recordings pass §2 — no outcome 1–3 is claimed. **Insufficient sensitivity** (evaluated
second, on the recordings that were processed): for each recording, the held-out presence AUC is the mean over
its two decoder halves per window; if the median over recordings of that AUC is below 0.55 in every window of
W, the comparison is reported as uninformative and no outcome 1–3 is claimed. Recordings are never selected on
AUC; both conditions are reported separately from each other and from the outcomes.

The early interval is analysed under the same total rule as a separate early visual analysis; the informative
task beside the nocue task as a within-participant cue-context robustness analysis; agreement strengthens,
disagreement is reported, neither changes the nocue outcome.

## 9. The synthetic development battery (before the freeze; results retained; not error control)

Twenty synthetic recordings per generator with this dataset's structure (4 blocks × 100 trials, 40 catch,
hemifields, the realized contrast distributions of twenty real recordings' events tables, no EEG), a
128-channel signal built as a fixed spatial pattern times a latent scalar plus spatially correlated noise, and
the latent scalar drawn from: **G1** graded homogeneous; **G2** graded skewed (skew-normal, shape 2);
**G3** graded heteroscedastic (SD doubling across the dose range); **X1** separated mixture (component
separation 2 SD); **X2** overlapping mixture (0.8 SD); each at decoder signal strengths giving held-out AUC ≈
0.6 and ≈ 0.8, and each with and without a block drift of 0.3 SD per block; three replicates per cell, seed
20260913; run through the complete pipeline of §3–§8 (loader stage replaced by the synthetic epochs). **Pass
criteria for development:** under G1–G3 the total rule returns "two-state" in at most one replicate per cell;
under X1 it returns "two-state" in at least two of three replicates at AUC ≈ 0.8; the isolation check of §4
holds exactly; the flat-channel, EOG-only and block-boundary cases of §3 behave as specified. A failure leads to
a registered revision of the protocol and a re-run of the battery; the battery's results and every revision
are retained. These are development checks of the implementation, not calibrated family-error control: a
few successful synthetic cells do not establish error rates, and the model-side T1 calibration does not
validate this pipeline.

## 10. What is and is not claimed

Every task of the dataset requires a report on every trial; there is no no-report condition. Omitting the
report labels from the decoder and the models makes the analysis report-unconditioned, not the experiment
report-free: the report prompt changes the task, and expected reporting can affect activity before the
question appears. A two-state outcome supports **mixture-model preference in a presence readout under a
report-required visual detection task**; it establishes neither report-independent ignition nor bistable
dynamics, global broadcast or consciousness, and a two-component density need not have two visible modes.
Fitted conditional densities and component separation are reported; a graded or inconclusive outcome is
bounded the same way. A claim about the effect of reporting would need a report manipulation and a direct
contrast; one positive and one non-significant result from unlike datasets do not supply it. The
informative-versus-nocue comparison speaks to the pre-stimulus state (attention and expectation), not to
report. The noninformative task is used only for one exploratory, report-conditioned description (the
distribution of projected activity for seen versus unseen trials per window), with no model comparison and no
claim.

Not claimed: anything about consciousness beyond the operational report; the authors' alpha-phase and
alpha-amplitude findings; the assignment of the noninformative validity digit (README D2); per-subject
demographics (INVENTORY §1); any equivalence to the language-model analysis, which shares the four-outcome
vocabulary and not the inferential procedure. The decoder decodes stimulus presence, not seeing.

## 11. Deviations from the primary analysis, in one place

Continuous log contrast with catch as an absence indicator (vs designed SNR levels; quantile levels only as
plots and a legacy sensitivity); 40 catch trials per recording (vs ≈ 150); catch vs all-present training,
balanced (vs no-sound vs maximum level); a split-half decoder with two-fold likelihood folds inside the other
half, giving matching readouts (vs trial-wise ten-fold decoding and five likelihood folds); **re-parameterized
likelihoods** — an intercept-plus-logistic graded mean with a log-linear SD and the dose-absent limit as its
catch density, an ordered two-state mixture with the catch flag and a displaced catch high mean in its
free-occupancy sensitivity (vs the inherited anchor, absolute-value SD and minimum-level catch); a hemifield
location term; an L-BFGS-B multistart with bounds (vs single-start capped Nelder–Mead, kept as a reproduction
sensitivity); a fixed artefact and bad-channel rule with bipolar EOG and spherical-spline interpolation (vs visual
rejection and ICA); an anti-alias low-pass before decimation and 512 Hz (vs 500); half-open 30 ms time edges (vs
16 samples stepping by 15 at 500 Hz); a main interval of 300–600 ms and a separate early interval (vs a single
window set); a total outcome rule with eligibility and precedence; the held-out log-score difference and a
participant bootstrap beside BMS; 35 subjects per task (vs 20), with 34 shared across the two tasks. The
estimator (decoder type and regularization), the 10 Hz smoother, the fold-mean evidence convention, the BMS
port and the three-window persistence convention are unchanged.

## 12. Where it runs, and the manuscript's wording until a result exists

Protocol, `preprocess.py`, the decoder and likelihood code and the synthetic battery on the Mac now (light);
the full EEG processing on the PC after its audit (the control moved to AWS on 13 Sept, so the PC is free) if a
verified copy and a matching CPU environment can be prepared, otherwise on the Mac after the running probe;
one recording worker first, peak RAM and runtime measured, then the concurrency chosen; the Mac's raw-data
master stays where it is. No GPU or cloud run is needed. Until an actual secondary result exists the manuscript
says: the human reference analysis reproduces the published distributional model comparison in the active
session of the Sergent auditory dataset; a separate analysis of its passive session examines the same
candidate models; a secondary visual analysis is planned on Melcón et al.'s report-required detection dataset,
with its protocol finalized before neural outcome analysis; it tests the assay's generalization across modality
and task and does not isolate the effect of reporting. "Pre-registered" is used only after the freeze is
recorded.

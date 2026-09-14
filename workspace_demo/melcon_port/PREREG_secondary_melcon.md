# DRAFT v5 — the planned secondary human analysis on Melcón et al. 2024 (OpenNeuro ds006171)

**Status: DRAFT v5 (2026-09-14), after Codex's four reads of v1–v4
(`../t1_access/reviews/2026-09-13_cheap_cloud_runs_and_melcon_codex_record.md` §B and continuation reviews 2–4).
Continuation review 4 (RSC 706ba25, evidence 6a79dcd) asked for a design change before stage C, and v5 makes it: a
per-generator strength target inside each generating law's population ceiling, a label-free inclusion gate before any
decoding, complete cells and immutable result provenance in the battery, the corrected component-separation diagnostic,
the graded-spread wording and the sample counts (§2, §6, §9, §11), each implemented and tested on artificial or synthetic
inputs. Before the freeze remain: the battery's stage C (§9); the causal-edge and composite filter-support corrections
(§3, §5); the §7 summary assembly and output command with the two-model BMS and legacy sensitivity integrations (§6–§7);
the both-tasks decoder sensitivity (§4); the report-conditioned description (§10); the all-recording loader verification
(§3); and Codex's read of the result.
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
main interval; the remaining outcomes are inconclusive/mixed and the three non-substantive outcomes of §8. The
question is conditional and predictive: it concerns access to a content under a report-required visual task and
says nothing about report-independence, bistable dynamics, global broadcast or consciousness (§10).

## 2. Data and inclusion

ds006171: 36 subjects, 104 subject × task recordings (missing on OpenNeuro: sub-01 informative, sub-02
noninformative, sub-35 nocue, sub-36 noninformative). Per recording 400 trials in 4 blocks of 100: 360
Gabor-present (90 per hemifield × orientation) and 40 catch trials (no Gabor), seen/unseen on every trial, an
orientation question on ≈ 15 %. **Primary task: nocue** (35 subjects on OpenNeuro; 34 after the sub-36 exclusion
below), no event before the Gabor. **Within-participant robustness task: informative** (35 subjects; 33 of them also in the included nocue sample, the same people, not a second cohort), a 100 %-valid spatial cue 0.7–1.0 s before the
Gabor. **The noninformative task is excluded from the intensity analysis**: its contrast column does not behave as
the staircase output of its own trial (INVENTORY §4) and there is no other trial-by-trial intensity measure; it
enters only the exploratory report-conditioned description of §10.

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
randomised, confounding hemifield, orientation, catch status and position with block (README D14; the other 103
recordings are randomised, longest run of one stimulus code at most 8 trials). These are transparent provisional
rules, not power guarantees, and they are not relaxed after model preferences are seen. Subjects contribute a
recording per task independently. Exclusion and retention counts are reported by contrast quintile, hemifield,
block, task and report. The rules are applied by one label-free entry point before any decoding (`inclusion.py`, `test_inclusion.py`; Codex, continuation review 4 §6): trial exclusions first under the requested retention variant, including the edge-trial and no-response sensitivities, then every recording, block and half floor and the preprocessor's exclusion, each failing rule recorded; a recording failing any rule is excluded — never a technical failure or an unavailable fold — and the recordings that pass are §8's denominator.

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
segment edge is flagged `edge_trial`, and a sensitivity excludes those trials. The 4.125 s is the high-pass's half-support; the composite high-pass → notch → low-pass response has a small tail beyond it (1.5e-6 of an impulse; Codex, continuation review 4 §5), so before the freeze the edge sensitivity is defined on the combined support or the padding influence is bounded, and until then it is not described as covering the whole chain.

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
channels typed `eeg`; the EOG channels are **never decoder features**. The causal-processing sensitivity (§5) has
its own configuration (`CONFIG_CAUSAL`) and its own caches, refused under the primary configuration.

## 4. Decoder — split-half design with matching readouts (implemented in `decoder.py`, `recording.py`)

Per recording, the four blocks are paired into two halves, H1 = {1, 2} and H2 = {3, 4}. For each half A as the
**decoder half**: a presence decoder (`StandardScaler → LogisticRegression(liblinear, C = 1, class_weight =
'balanced', random_state = 20260913)`, features the 128 scalp channels) is fitted per time sample over the whole
epoch (769 samples) on the retained trials of A and applied to every retained trial of the other half B, giving
each B trial a signed decision value per sample from a decoder that never saw its half. The **likelihood
comparison of §6 then runs entirely inside B**, as a two-fold block cross-validation (train on one block of B,
test on the other, both ways), on projections that all come from the one decoder fitted on A: the likelihood's
training and test projections therefore share one readout and one scale by construction, which the nested
cross-fit of v2 did not give. Swapping the roles of the halves gives every block a held-out likelihood score; the
four held-out block scores are the recording's four folds. **Isolation, checked exactly on synthetic epochs
(`test_recording.py`):** with the EEG and the labels of block 4 changed, the decoder that scores block 4 (fitted on
blocks 1–2), block 3's projections and the likelihood parameters that predict block 4 are bit-identical, while
the H1 projections (from the decoder trained on blocks 3–4) change as they must. The property holds for the
decoder and likelihood stages given the block-local preprocessing of §3. Every random seed is fixed (20260913).

Projections are z-scored per recording, half and time sample using the mean and SD of the decoder half's
**in-sample** decision values of that decoder (a training-only affine transform, identical for every B trial; an
SD below 1e-8 makes that sample, and every window containing it, unavailable); the 10 Hz smoother of §5 is applied
after the z-score and before windowing. The decoder half has ≈ 200 trials with ≈ 20 catch trials, which is why the
catch floor of §2 applies to halves.

**Training contrast: catch (Gabor absent) versus all Gabor-present trials** of the decoder half (≈ 20 : 180),
the presence question with five times the positive examples of the top contrast quintile (no supraliminal
anchor exists in a staircase design: the top quintile is seen on 0.57–0.63 of trials at ≈ 1.3 × the median
contrast). Sensitivities, each with its own declared split: (a) catch vs the decoder half's present trials at or
above its 80th contrast percentile (implemented, `variant = 'top_quintile'`); (b) a decoder trained on the same
half of **both** of a subject's tasks (nocue and informative), applied to the other half of each task, with the
likelihood folds as above — it shares training information between the two task estimates and is not an
independent replication (specified; implemented and tested before the freeze). Held-out decoder AUC per half,
window and variant is reported (§7). On synthetic pure noise the held-out AUC averages 0.509 over three seeds, two
halves and forty windows, and a single half-window value scatters by about ±0.07 with ≈ 20 held-out catch trials,
so a single recording's AUC is not interpreted; §8 reads the median over recordings.

## 5. Intensity covariate, nuisance terms, windows

*Intensity.* The main covariate is **continuous log contrast**, x = (log c − m)/s with m and s the mean and SD
of log contrast over the present trials of the fold's likelihood **training block**; catch trials carry the
catch flag and no x. A log-contrast SD below 1e-6 makes the fold unavailable. Five contrast quantiles are used for
plots (recording-wide edges over all present trials) and for the legacy sensitivity (training-block edges, §6).

*Nuisance.* Hemifield enters every model as an additive location shift β on **displayed** Gabors in the right
hemifield (h = 1; left h = 0), the same term in the graded mean, both mixture means and the null mean; the authors
calibrated separate hemifield thresholds (metadata: median left/right median-contrast ratio 1.09, maximum 1.56).
Catch trials carry no hemifield term: no stimulus was displayed, and in the nocue task their side code is a
virtual side from the event mapping. The term is a location shift only; side-dependent slopes, spreads or history
are not modelled. **DRAFT v3's block sensitivity is removed:** each likelihood fit has one training block, and a
single per-block shift γ is then an exact alias of the intercept (a0' = a0 + γ reproduces every density; the same
for μ_L and μ0; `test_likelihood.py`), so it adjusted nothing, and no training-only rule predicts a held-out block's
drift from the one other block of its half. Block drift is instead a stress condition of the battery (§9).
Staircase history enters no model; the analysis is conditional on the realized contrasts, and no claim is made
that a fitted occupancy curve recovers a sensory threshold over an unobserved dose range.

*Report.* seen/unseen from the 124/125 triggers (INVENTORY §3), not used in the model comparison, which is
therefore **report-unconditioned** on a **report-required** task (§10).

*Windows.* Projected activity is low-passed at 10 Hz (12th-order Butterworth, forward–backward over the whole
epoch, the inherited smoother) and averaged in half-open **30 ms windows on time edges** from −300 to +900 ms (40
windows of 15 or 16 samples at 512 Hz). Two intervals: the **main interval 300–600 ms** (windows 20–29), which
contains the primary analysis's first pxp > 0.95 window at 315 ms and its plateau at 435–495 ms and tests
report-associated visual processing under the question display (jittered +0.30 … +0.40 s) and response
preparation (median response ≈ 0.93 s); and the **early interval 0–300 ms** (windows 10–19), a separate early visual
analysis. Models are fitted on the twenty windows of the two intervals; the other twenty are fitted for display
only. The zero-phase filters spread a step across the 300 ms boundary (a step at 300.8 ms leaves 0.23 of its
height in 270–300 ms after the smoother; the high-pass and notch are non-causal too): the filters' step and
impulse responses are shown, and the **causal-processing sensitivity** accompanies any statement about activity
preceding the question. It is specified exactly: (i) preprocessing under `CONFIG_CAUSAL`, the same high-pass,
notch and low-pass specifications as MNE minimum-phase FIR designs (`phase = 'minimum'`); (ii) the decoder's 10 Hz
smoother forward only (`scipy.signal.sosfilt`) from zero initial conditions at the epoch's first sample, −0.5 s,
200 ms before the first window; (iii) epochs, windows, decoder and likelihood unchanged; (iv) **no delay
compensation**: every causal filter delays, so under this variant an effect can appear later than under
zero-phase processing and never earlier, and a statement that activity precedes the question display is made only
if the effect is present under the causal variant before +300 ms. Checked on artificial inputs (`test_causal.py`) for an impulse 20 s inside a segment: the causal filters' and smoother's responses are zero before it (at most 5e-17 of the impulse, floating-point residue), while the zero-phase ones spread up to 0.31 of it backwards; the causal filter chain peaks 3.9 ms after that impulse at 1024 Hz and the forward-only smoother 139 ms after it — delays of the tested impulses, not of every signal, and no proof that onset inference is conservative; the filter lengths at each native rate are reported by `preprocess.filter_support`. **Open before the freeze (Codex, continuation review 4 §5):** `CONFIG_CAUSAL` still pads segment edges with `reflect_limited`, which uses future samples, so an impulse 2 s from a segment start leaves 6.9e-4 of itself earlier; the causal padding or initialization and a warm-up exclusion near segment starts are specified and tested there, and the causal preprocessing configuration is bound to the decoder's causal smoother, before any statement about activity preceding the question relies on this variant. The claim is also conditional on the declared QC and trial selection. Adjacent smoothed windows are strongly dependent; three consecutive windows is a
persistence convention, not three independent confirmations.

## 6. Models — the densities, exactly (implemented in `likelihood.py`)

For a trial with projection y, scaled log contrast x (present trials) or the catch flag, h = 1 for a displayed
Gabor in the right hemifield and 0 otherwise, and lg(z) = 1/(1 + e^{−z}):

**Model 0 (null):** y ~ N(μ0 + β h, σ0²).

**Graded (2B'):** y ~ N(a0 + a1 L + β h, exp(s0 + r L)²), L = lg(k (x − x0)). The intercept a0 is the low-dose
asymptote, a1 the range, x0 the threshold, k the slope; the log-SD moves with the same logistic as the mean and
changes by r across the dose range, |r| ≤ ln 10. **Catch density:** the dose-absent limit L = 0, y ~ N(a0,
exp(s0)²), with no extra parameter. DRAFT v3 wrote σ = exp(s0 + s1(μ − a0)) with s1 ∈ [−2, 2]/S and a1 ≤ 10S, whose exponent could span ±20 (Codex, V3.3). For a1 > 0 the two formulas coincide under r = s1·a1, but the bounded families differ and neither contains the other everywhere; at a1 = 0 the new form lets the spread move without a mean change, which is still one conditional normal state. Under the bounds below the graded SD spans 0.005S to 50S globally, and within one fit its asymptotic ratio is at most ten (Codex, continuation review 4 §2). Allowing spread at zero mean range avoids forcing variance changes into the mixture; that is a motivation the battery examines, not a guarantee that held-out family selection is conservative.

**Two-state (3'):** y ~ (1 − A) N(μ_L + β h, σ²) + A N(μ_H(x) + β h, σ²), A = lg(k_A (x − x0)),
μ_H(x) = μ_L + exp(δ0) + exp(δ1) · lg(k_h (x − x0)), so that the high state sits above the low state at every
dose by at least exp(δ0). **Catch density:** A = 0, y ~ N(μ_L, σ²), identified by the **catch flag**.
**Free-catch-occupancy sensitivity (3'L):** on catch trials (1 − π0) N(μ_L, σ²) + π0 N(μ_L + exp(δ0), σ²), π0 =
lg(θ0): the catch high mean is displaced by the same exp(δ0) that separates the components elsewhere, so the
density is structurally identifiable. It need not be practically informative: at the smallest separation the
components nearly coincide (Codex: π0 = 0.1 against 0.8 at separation e^{−5} and σ = 5 differ by total variation
0.0004). π0 is therefore reported with the separation exp(δ0)/σ, flagged weakly identified below 0.5 and not
interpreted there (`likelihood.pi0_report`); its group summary is in §7.

**Scaling and bounds.** From the training block only: S and ȳ, the SD and mean of the training block's window
values over all its retained trials (after the decoder's training-only z-score, the smoother and the window mean),
and m, s of §5. Bounds: μ0, a0, μ_L ∈ ȳ ± 5S; log σ0, s0, log σ ∈ [log 0.05S, log 5S]; β ∈ ±3S; a1 ∈ [0, 10S];
x0 ∈ [−4, 4]; log k, log k_A, log k_h ∈ [log 0.05, log 20]; r ∈ ±ln 10; δ0, δ1 ∈ [log 0.01S, log 10S]; θ0 ∈ [−6, 3].
Every density and gradient is finite at every corner of these bounds (904 corners, `test_likelihood.py`).
**Floors** (the fold is unavailable, with its reason recorded): fewer than 3 catch trials or fewer than 20 present
trials in either hemifield in the training block; log-contrast SD below 1e-6; S below 1e-8; a non-finite training
or test input.

**Starts.** One moment start from the training block: μ0 = ȳ, log σ0 = log S, β = right-minus-left mean of the
present trials; a0 = μ_L = the catch mean; s0 = log σ = log max(catch SD, 0.05S); d = mean of the present trials in
the top contrast quintile minus that of the bottom quintile; a1 = d; δ0 = log max(d, 0.01S); δ1 = log max(d/2,
0.01S); x0 = 0; log k = log k_A = log k_h = 0; r = 0; θ0 = logit 0.05. Every coordinate is then moved inside its range
by 10⁻³ of the range (so d ≤ 0 puts a1 just above 0 and δ0, δ1 just above their lower bound). Seven more starts: each
coordinate's position in its range is mapped to the logit scale, jittered by N(0, 0.25²) and mapped back; seeded
from (20260913, subject, task, half, fold, window, model). **Optimizer:** L-BFGS-B within the bounds on analytic
gradients (checked against central differences, worst relative error 2.5e-7), ftol 1e-10, gtol 1e-6, maxiter 2000.
A start is **converged** when its training log-likelihood and gradient are finite and the optimizer reports
success or the largest component of the projected gradient is at most 1e-3. The kept solution is the converged
start with the highest training log-likelihood; if none converged, eight more starts jittered by N(0, 0.5²) from a
second seed; if still none, the model is **unavailable** for that fold and window. The held-out density of every
test trial must be finite, else unavailable. The number of converged starts within 0.5 nat of the kept solution is
recorded.

**Legacy/quantile sensitivity (frozen; its fold primitive is implemented in `likelihood.LEGACY`, `legacy_fold_scores`, and its decoder, recording and group route is integrated before the freeze).** The three
Sergent likelihoods with the two inherited traps repaired: levels from the quintile edges of the **training
block's** present log contrast, applied to training and test trials alike (level = 1 + the number of edges below
the trial's log contrast; outer bins open); catch = level 0 by its flag, with A = 0 and μ_high = μ_low on catch trials
by the flag; the graded anchor fixed at the design maximum 5 in every call; the inherited moment starts computed from
the training block only; capped Nelder–Mead (xatol = fatol = 1e-4, 200 × n_params iterations and evaluations,
non-adaptive) from that single start; no hemifield term; a non-finite start or held-out score makes the model
unavailable. Descriptive quintile plots use recording-wide edges and are never used for fitting.

**Unavailable fold:** a model unavailable on any of a recording's four folds in a window is unavailable for that
recording and window, and the recording leaves that window's group comparison and is counted (§8).

## 7. Evidence, group comparison and the bootstrap (implemented in `recording.py`, `group.py`)

Per recording and window, **evidence** for each model = mean over the four held-out blocks of the block's
summed held-out log-likelihood (the inherited predictive convention, not a marginal likelihood). **Group
comparison** per window with the `spm_BMS` port (`../sergent_port/bms.py`, 10⁶ Dirichlet samples seeded by the
window): protected exceedance probabilities and BOR over the three models, and two-model (2B' vs 3') BMS as a sensitivity (specified; its integration in `group.py` is completed before the freeze). The pxp is a descriptive convention: **1 − pxp is not a calibrated p-value**, the step-up correction
across windows establishes no frequentist error control, and equal pxp thresholds here and in Sergent do not
represent matched evidence or power (fold-summed evidence scales with retained trials).

Alongside BMS, the **held-out log-score difference per trial** Δ = (Σ ℓ_3' − Σ ℓ_2B')/n over the recording's four
held-out blocks in a window is reported with the median and interquartile range across recordings and a
**participant bootstrap**. Statistic: the equal-weight mean of Δ over participants, per window, **pointwise** (no
simultaneous band is claimed). B = 2,000 resamples of participants with replacement, seed 20260913, a resampled
participant carrying its whole time course and both its tasks together. Interval: the 2.5th and 97.5th percentiles
of the finite resampled statistics (95 %). Missing windows: within a resample a window's mean uses the resampled
participants with a finite Δ there, and is missing if fewer than 10 have one; the interval is reported only if at
least 95 % of the resamples are finite. Three separate estimators: nocue; informative; and the paired difference
informative − nocue over the participants with both tasks. The **held-out AUC** is summarized per half and window as
the median over recordings with an interval from the same resampling scheme (seed + 1). The **catch occupancy** of
3'L is summarized per recording as the median of its fold estimates over the main-interval windows, and at group
level as the median over recordings with an interval (seed + 2), over all recordings and, as a sensitivity, over
those not weakly identified. These intervals describe summaries over already-fitted recordings; they are not a
refitting bootstrap of the decoder and the fits. The bootstrap primitives and the Δ estimators are implemented (`group.bootstrap_mean`, `bootstrap_median`, `bootstrap_tasks`); the AUC and catch-occupancy assemblies, the not-weakly-identified subset and the command that saves these products are completed before the freeze. Δ is the quantity that corresponds to the model-side statistic;
the two inferential procedures are not the same.

## 8. Outcome rule — a total decision function (implemented in `group.decide`; truth tables in `test_group.py`)

Let W be the ten main-interval windows, in physical order. A recording **enters** a window when all three models are
available on all four of its folds there; a window is **eligible** when at least 20 recordings enter it, and its
group comparison uses exactly those recordings, whose identities and count are reported. A **run** for a model is at
least three windows that are **adjacent on the physical window grid**, each eligible, each with that model's pxp ≥
0.95; adjacency is never re-established by dropping an ineligible window. The outcome is the first of these that
applies:

1. **Technical failure** — more than a quarter of the recordings that pass §2 end in a technical failure (an
   exception anywhere in preprocessing, the decoder or the fits; an unavailable fold is not a technical failure), or
   fewer than 20 recordings pass §2.
2. **Insufficient sensitivity** — per recording and window the held-out presence AUC is the mean of its two halves,
   missing if either is not finite; per window, the median over the recordings with a finite value, missing if fewer
   than 20 have one; the outcome applies when no window of W has a median of at least 0.55.
3. **Insufficient availability** — fewer than 8 of the 10 windows of W are eligible. (A count of recordings that
   pass inclusion, with no hard failure and good AUC, but whose fits leave no eligible window is therefore this
   outcome, not "inconclusive" — Codex's counterexample, now in `test_group.py`.)
4. **Two-state** — a two-state run in W and no graded run.
5. **Graded** — a graded run and no two-state run.
6. **Inconclusive/mixed** — neither family runs, or both do. A null run changes nothing and is reported.

Outcomes 1–3 are reported separately from each other and from 4–6, and recordings are never selected on AUC. The
per-window cohorts vary; beside the outcome a **common-cohort sensitivity** repeats the comparison and the runs on
the recordings that enter every eligible window of W (when there are at least 20). The time courses are shown in
every case. The early interval is analysed under the same rule as a separate early visual analysis; the informative
task beside the nocue task as a within-participant cue-context robustness analysis; agreement strengthens,
disagreement is reported, neither changes the nocue outcome.

## 9. The development battery (before the freeze; results retained; not error control; `battery.py`, `synthetic.py`)

**Stage A** — the continuous preprocessing and QC on artificial raw recordings (`test_preprocess.py`: positions,
block isolation against a recording-wide filter, flat / noisy / burst / EOG-only / common-mode cases, exclusion,
cache refusals) and the causal variant (`test_causal.py`). **Stage B** — the likelihood recipe (`test_likelihood.py`),
the decoder and recording isolation (`test_recording.py`), the inclusion gate (`test_inclusion.py`) and the decision function and bootstrap (`test_group.py`).
**Stage C** — the complete §4–§8 pipeline on synthetic epochs, as follows.

*Templates.* The 34 nocue recordings that pass §2 at the events-table level (sub-35 nocue is not on OpenNeuro and
sub-36 nocue is excluded), so each replicate has the real sample's size and structure — trial order, blocks, catch
trials, hemifields and realized contrasts — and the §8 thresholds apply unchanged. No EEG is read.

*Laws.* With x the recording's present log contrast z-scored over its present trials (a generation-side quantity),
L = lg(1.5 x) (0 on catch trials) and ε ~ N(0, 1) independent per trial: **G1** z = 2L + ε; **G2** z = 2L + e with e a
skew-normal of shape 2 standardized to mean 0 and SD 1; **G3** z = 2L + (1 + L)ε (SD 1 at zero dose, 2 at full dose);
**X1** z = 2B + ε, B ~ Bernoulli(L) (separation 2 SD); **X2** z = 0.8B + ε. Catch trials follow the dose-absent law.
Right-hemifield Gabors add 0.3 to z; with drift, every trial of block b adds 0.3(b − 1). Sensors: X_eeg = amplitude ·
z · p · env(t) + M a(t) + 0.5 n, with p a fixed unit-norm 128-channel pattern, env(t) = exp(−(t − 0.45)²/(2 · 0.12²)),
M a fixed 128 × 16 mixing matrix (entries N(0, 1/16)) of 16 unit-variance AR(1) sources with coefficient 0.9 per sample,
n white; four EOG channels of white noise; the epoch grid −0.5 … +1.0 s at 512 Hz; baseline correction over −0.5 … 0 s.
p and M are fixed by the seed (20260913, 101); a recording's draws by (1, generator, strength, drift, replicate, subject).

*Decoder strength, per generator, calibrated independently of every family outcome (v5; Codex, continuation review 4 §5).* DRAFT v4's common targets, held-out AUC 0.6 and 0.8, are withdrawn. The calibration statistic — the median over recordings of the mean held-out AUC over both halves and the ten main-interval windows — has a population ceiling set by the generating law, because a graded law's low-dose present trials and a mixture's low-state present trials overlap the catch distribution whatever the amplitude. Computed exactly from each present trial's latent ranking AUC (`synthetic.present_latent_auc`, behaviour only) on the first eight templates without drift, the ceilings are G1 0.781, G2 0.784, G3 0.727, X1 0.744 and X2 0.648 (X1 and X2 equal Codex's independent calculation to 1e-9, `test_battery.py`), so 0.8 was unattainable for every generator. For a mixture whose low state matches catch the ceiling stays near 0.5 + 0.5 × the mean occupancy whatever the separation, so a larger X1 separation would not have restored that target. Each generator's target is instead 0.5 + q (ceiling − 0.5): **weak** q = 0.5 and **strong** q = 0.9 of its own headroom. The amplitude is read from a calibration draw of the first 8 templates without drift on the grid 0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.2, 3.2, 4.6, 6.4 and interpolated linearly to the target; it is accepted if a fresh check draw lands within ±0.03 of the target (a declared development tolerance, not a precision guarantee), otherwise five points at 0.75–1.25 times the amplitude are added once and the check is repeated. The complete search history — grid, refinement points and both checks — is saved. A calibration that misses twice is **not usable**: its cells run as diagnostics, identified as such in every result and verdict, and neither pass, fail nor drive a revision. Equal presence AUC across generators is not equal mixture identifiability, so the conditional readout separation of the generating high and low present trials and the readout–latent correlation are reported beside every cell.

*Result provenance and completeness.* A configuration identity — the battery version, the digests of every pipeline module, every module's specification, the strength definition, the calibration constants and the events table's digest — names the result namespace. Every recording result carries its manifest (identity, generator, strength, drift, replicate, subject, seeds, amplitude, calibration digest and usability, template digest); an existing result whose manifest differs, or that cannot be read, is refused, so a revision writes a new namespace beside the retained old one. A cell is judged only when every replicate has every recording; otherwise it is **incomplete**, which is distinct from a failure.

*Cells.* 5 generators × 2 strengths (weak, strong) × 2 drift conditions × 3 replicates = 60 replicates × 34 recordings = 2,040
synthetic recordings, fitted on the twenty windows of the two intervals.

*Pass criteria* (on the main interval): under **G1, G2, G3**, in every strength × drift cell, at least 2 of the 3
replicates end in a substantive outcome (two-state, graded, inconclusive/mixed) **and** at most 1 ends two-state —
technical failure, insufficient sensitivity and insufficient availability count against the first requirement and
never pass a cell; under **X1** at the strong strength, both drift conditions, two-state in at least 2 of 3 replicates; X1 at the weak strength and **X2** (the weak-separation stress condition) have no pass criterion and report their outcome counts, the fitted minimum gap exp(δ0)/σ and full gap (exp(δ0) + exp(δ1)·lg(k_h (x − x0)))/σ at the held-out present doses (v4 reported only the minimum and called it the separation: 0.096 SD against a full gap of 1.130 SD on the test recording, Codex §4), the conditional readout separation and the median absolute error of the fitted occupancy against the generating occupancy; cells are judged only when complete, and an unusable calibration's cells are diagnostics; stages A and B pass. A failure leads
to a registered revision of the protocol and a re-run of the battery; every result and revision is retained. These
are development checks of the implementation, not calibrated family-error control: a few synthetic cells do not
establish error rates, and the model-side T1 calibration does not validate this pipeline. Single-block likelihood training keeps the accepted split-half design: its finite-sample mixture recovery at these readout strengths is not yet established, and X1 at the revised strength assesses it; the cross-validation is not redesigned on the 0.10 SD figure, which was the minimum gap (Codex, continuation review 4 §4).

*Cost, planning evidence.* One complete synthetic recording took 19.2 s of pipeline and 0.64 s of generation on one core of the Mac shared with the refit probe (`results/battery/benchmark.json`), projecting about 11.2 core-hours for the 2,040 recordings. The calibration is projected, not measured: 880 decoder calls at an assumed 11 s each (about 2.8 core-hours), up to 1,360 with every refinement (about 4.4); group BMS, common-cohort reruns and the sensitivities are outside these figures. It runs on two or three workers around the probe.

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
demographics (INVENTORY §1); any equivalence to the language-model analysis, which shares the outcome
vocabulary and not the inferential procedure. The decoder decodes stimulus presence, not seeing.

## 11. Deviations from the primary analysis, in one place

Continuous log contrast with catch as an absence flag (vs designed SNR levels; quantile levels only as plots and a
legacy sensitivity); 40 catch trials per recording (vs ≈ 150); catch vs all-present training, balanced (vs no-sound
vs maximum level); a split-half decoder with two-fold likelihood folds inside the other half, giving matching
readouts (vs trial-wise ten-fold decoding and five likelihood folds); **re-parameterized likelihoods** — an
intercept-plus-logistic graded mean whose log-SD moves with the same logistic within a bounded range, with the
dose-absent limit as its catch density; an ordered two-state mixture with the catch flag, and a displaced catch high
mean in its free-occupancy sensitivity (vs the inherited per-call anchor, absolute-value SD and minimum-level catch);
a hemifield location term on displayed stimuli; bounded L-BFGS-B multistart on analytic gradients with a declared
convergence, retry and unavailability rule (vs single-start capped Nelder–Mead, kept as a repaired legacy
sensitivity); block-local continuous preprocessing with a median detection reference, a fixed bad-channel and
artefact rule with bipolar EOG and spherical-spline interpolation (vs the authors' FieldTrip preprocessing, visual
rejection and ICA); an anti-alias low-pass before decimation and 512 Hz (vs 500); half-open 30 ms time edges (vs 16
samples stepping by 15 at 500 Hz); a main interval of 300–600 ms and a separate early interval (vs a single window
set) with a specified causal-processing sensitivity; a total outcome rule with eligibility, adjacency on the
physical grid, availability and precedence; the held-out log-score difference and a participant bootstrap beside
BMS; 34 nocue recordings (vs 20 participants), 33 participants shared across the two tasks. The estimator (decoder
type and regularization), the 10 Hz smoother, the fold-mean evidence convention, the BMS port and the three-window
persistence convention are unchanged.

## 12. Where it runs, and the manuscript's wording until a result exists

The protocol, `preprocess.py`, the decoder, likelihood and group code and the battery run on the Mac now, on
synthetic and artificial inputs only; stage C of the battery is projected at ≈ 11 core-hours plus ≈ 3–4 for the strength calibration (planning evidence, §9) and is staged around the running refit probe. The full EEG processing runs on the PC after its
audit if a verified copy and a matching CPU environment can be prepared, otherwise on the Mac after the probe; one
recording worker first, peak RAM and runtime measured, then the concurrency chosen; the Mac's raw-data master stays
where it is. No GPU or cloud run is needed. Until an actual secondary result exists the manuscript says: the human
reference analysis reproduces the published distributional model comparison in the active session of the Sergent
auditory dataset; a separate analysis of its passive session examines the same candidate models; a secondary visual
analysis is planned on Melcón et al.'s report-required detection dataset, with its protocol finalized before neural
outcome analysis; it tests the assay's generalization across modality and task and does not isolate the effect of
reporting. "Pre-registered" is used only after the freeze is recorded.

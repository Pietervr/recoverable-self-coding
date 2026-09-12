# DRAFT — pre-registration of the secondary human analysis on Melcón et al. 2024 (OpenNeuro ds006171)

**Status: DRAFT for the owner's review (2026-09-12). Nothing here has been run: no EEG of ds006171
has been decoded, averaged, contrasted or plotted (README, "hard limit"); every number quoted is from
the behavioural events tables (`INVENTORY.md`).** A secondary, visual replication of the primary human
analysis (Sergent et al. 2021, auditory; `../sergent_port/`) for the Entropy special-issue paper, to be
frozen before the first neural result of the running model-side simulation is opened.

## 1. Question and hypotheses

Same question as the primary analysis: at the threshold of report, is the single-trial neural
response to a stimulus better described by a **graded** family (a unimodal distribution whose mean
and spread move continuously with intensity) or by a **two-state** family (a mixture of a "low" and a
"high" state whose occupation probability moves with intensity)? Here intensity is the Gabor contrast
set trial-by-trial by the authors' online staircase (in place of Sergent's five SNR levels), the report
is the seen/unseen answer given on every trial (in place of audibility 0–10), and the stimulus is a
50 ms peri-threshold Gabor in one hemifield.

H1 (two-state): the mixture model has the highest protected exceedance probability (pxp ≥ 0.95) in at
least three consecutive 30 ms windows within 0–300 ms after Gabor onset, in the nocue task.
H0-graded: the unimodal model does, under the same rule. Neither: inconclusive (§7).

## 2. Data and inclusion

ds006171: 36 subjects, 104 subject × task recordings (missing on OpenNeuro: sub-01 informative,
sub-02 noninformative, sub-35 nocue, sub-36 noninformative). Per recording 400 trials in 4 blocks of
100: 360 Gabor-present (90 per hemifield × orientation) and 40 catch trials (no Gabor), seen/unseen on
every trial, an orientation question on ≈ 15 %. **Primary task: nocue** (35 subjects) — no event
before the Gabor, the closest analogue of Sergent's active session. **Replication task: informative**
(35 subjects) — a 100 %-valid spatial cue 0.7–1.0 s before the Gabor. **The noninformative task is
excluded from the intensity analysis**: its contrast column does not behave as the staircase output
of its own trial (INVENTORY §4) and there is no other trial-by-trial intensity measure; it enters only
the exploratory report-conditioned check in §8.

Trial exclusions, fixed in advance: trials without a seen/unseen response (102 in the dataset);
trials with a non-positive recorded contrast (36, sub-11 informative); trials failing the artefact
rule in §3. Recording exclusions: fewer than 250 present trials or fewer than 25 catch trials after
exclusions. Subjects contribute a recording per task independently.

## 3. Preprocessing (fixed; implemented in `load.py`, README D4–D7)

BDF → 128 scalp channels renamed from `channels.tsv`; high-pass 0.4 Hz and 50 Hz notch (Sergent's
FieldTrip settings); common average reference; epochs −0.5 … +1.0 s around the **photodiode-corrected**
Gabor/catch onset (README D1), baseline −0.5 … 0 s; decimation to 512 Hz. **Artefact rule (proposal,
to be confirmed by the owner before freezing):** a trial is rejected if any scalp channel exceeds
150 µV peak-to-peak or either vertical EOG channel exceeds 100 µV peak-to-peak within −0.2 … +0.6 s;
channels rejected in more than 20 % of a recording's trials are interpolated from neighbours before
the rule is re-applied. No ICA (the authors' ICA is not part of the dataset and would introduce
per-subject manual choices).

## 4. Decoder — projected activity

As in the primary analysis (`../sergent_port/decode.py`): per time sample,
`StandardScaler → LogisticRegression(liblinear, C = 1)` on the 128 channels, 10-fold stratified
cross-validation, every trial receiving one signed decision value per sample from a classifier that
did not see it.

**Training contrast: catch (Gabor absent) vs all Gabor-present trials** (primary), with
`class_weight = 'balanced'` because the classes are 40 : 360. Not catch vs the top contrast quintile
(Sergent's "no sound vs maximum level"), because the staircase leaves no supraliminal anchor: the top
quintile is seen on only 0.57–0.63 of trials at ≈ 1.3 × the median contrast, so that contrast is the
same threshold contrast with 40 vs 72 trials for a 128-feature classifier — under-powered by
construction. Training on all present trials asks *is a Gabor on the screen?* with nine times the
positive examples and gives every trial a held-out projection under the same folds. **Sensitivity
(pre-registered):** catch vs top quintile; and training pooled across a subject's tasks (more catch
trials, mixed cue contexts). Per recording; no temporal generalisation.

## 5. Intensity covariate, report, windows

*Intensity.* Recorded Gabor contrast, log-transformed and **binned within recording into five
quantile levels (1–5) with catch trials as level 0**, so that the three likelihood models and their
level-anchored initial values port unchanged from the primary analysis (six levels there, six here).
Sensitivity: continuous log-contrast, z-scored within recording, in place of the levels.
*Report.* seen/unseen from the 124/125 triggers (INVENTORY §3), used only in §8 — the model comparison
itself is report-free, as in the primary analysis.
*Windows.* Projected activity low-passed at 10 Hz and averaged in contiguous 30 ms windows (16
samples at 512 Hz) from −300 to +900 ms; **primary set 0–300 ms** (10 windows, before the subjective
question appears); **secondary set 300–900 ms** (20 windows), in which the question display
(jittered 300–400 ms after Gabor onset, no trigger) and response preparation (median response
0.93 s) are present and constant across intensity levels. Cross-validation of the likelihood fits by
block (4 blocks of 100 trials → 4 folds; Sergent: 20 blocks → 5 folds), initial values from the
training fold only (the primary analysis's inherited limitation (i) is not carried over).

## 6. Models and group comparison (unchanged from the primary analysis)

Model 0 (null): Gaussian, level-independent. Model 2B (graded): logistic mean in level, SD linear in
the mean. Model 3 (two-state): mixture of N(μ_low, σ) and N(μ_high(level), σ) with logistic mixing
proportion; proportion 0 and high mean = μ_low at level 0. Nelder–Mead from the original starting
points, evidence = mean over folds of the held-out summed log-likelihood; group comparison per window
with the spm_BMS port (`../sergent_port/bms.py`): protected exceedance probabilities, BOR, Simes
correction across the windows of each set. **Criterion: pxp ≥ 0.95 in ≥ 3 consecutive windows of the
primary set, surviving Simes.** Two-model (2B vs 3) BMS is reported as a sensitivity, as in
RESULTS_sergent C6.

## 7. Outcomes — one of four, decided by the rule in §6 on the nocue task

1. **Two-state**: Model 3 meets the criterion. 2. **Graded**: Model 2B meets it. 3. **Inconclusive**:
neither does (including a null-model win, and a Model 3 win only in the secondary set). 4. **Technical
failure**: decoder AUC (catch vs present, pooled cross-validated) ≤ 0.55 in every window of the primary
set in more than half of the recordings, or fewer than 20 recordings survive §2 — then no outcome
1–3 is claimed. The informative task is reported beside the nocue task under the same rule; agreement
strengthens, disagreement is reported, neither changes the nocue outcome.

## 8. The three cue tasks and what is not claimed

The dataset has **no no-report condition**: every task asks for a report on every trial. The three
tasks manipulate what precedes the Gabor (nothing / a 50 %-valid cue / a 100 %-valid cue), i.e.
spatial attention and expectation, not report. The closest report-related test available is
*invariance of the outcome across cue contexts* (nocue vs informative, §7), which speaks to the
pre-stimulus state, not to report. The noninformative task is used only for one exploratory,
report-conditioned description — the distribution of projected activity for seen vs unseen trials
per window — with no model comparison and no claim.

Not claimed: anything about consciousness beyond the operational report; the authors' alpha-phase
and alpha-amplitude findings; the assignment of the noninformative validity digit (README D2);
per-subject demographics (INVENTORY §1); any equivalence to the language-model analysis — the
model-side simulation is compared with this result only through the shared four-outcome rule.
The decoder decodes stimulus presence, not seeing.

## 9. Deviations from the primary analysis, in one place

Binned staircase contrast (vs designed SNR levels); 40 catch trials per recording (vs ≈ 150); catch vs
all-present training, balanced (vs no-sound vs maximum level); 4-fold by block (vs 5); training-only
initial values; a fixed artefact rule (vs visual rejection + ICA); 512 Hz (vs 500); a 0–300 ms primary
window set forced by the early question display; 35 subjects per task (vs 20). Everything else —
estimator, folds, filter, window length, likelihoods, optimiser, BMS, criterion — is unchanged.

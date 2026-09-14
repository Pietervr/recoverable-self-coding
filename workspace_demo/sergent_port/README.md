# Sergent et al. 2021 — Python port of the single-trial model comparison

Port of the MATLAB / MNE-Python analysis behind **Sergent C., Corazzol M., Labouret G., Stockart F.,
Wexler M., King J.-R., Meyniel F. & Pressnitzer D. (2021), "Bifurcation in brain dynamics reveals a
signature of conscious processing independent of report", Nat Commun 12:1149** — the part that
decodes stimulus presence from single-trial EEG, fits the null / unimodal-non-linear / bifurcation
models to the decoder output in 30 ms windows, and compares the models at the group level with
protected exceedance probabilities (Fig. 3E of the paper; Fig. 2C-style mean/SD profiles; the
variance burst at threshold). Run on the 20 open subjects, active and passive sessions.

The reproduction result, with the numbers side by side with the paper's, is in
**`RESULTS_sergent.md`** (the owning document for this job). This README is the pipeline and its
deviations from the original.

Source data and scripts: OSF `aw3t5` (CC0), downloaded to `../brain_data/sergent2021/`
(gitignored — `workspace_demo/brain_data/` is in the repo's `.gitignore`):

```
Bifurcation_OSF_PreprocessedData/S{1..20}_{Active,Passive}_data_ref.mat   FieldTrip epochs (64 ch, 500 Hz, -0.5..2 s)
Bifurcation_OSF_BehaviouralData_ActiveSessions/Subject_XX_Active.mat      MATLAB tables (unreadable by scipy, see D8)
Bifurcation_OSF_Scripts/                                                  the original MATLAB + Python scripts
41467_2021_21393_MOESM4_ESM.xlsx                                          the publisher's Source Data workbook (below)
derived/                                                                  OUTPUT of decode.py (npz per subject) + logs
```

**Source Data provenance.** `41467_2021_21393_MOESM4_ESM.xlsx` is the Source Data file published with
the article (Springer Nature, CC BY 4.0),
<https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-021-21393-z/MediaObjects/41467_2021_21393_MOESM4_ESM.xlsx>,
obtained 2026-09-11 (the local copy came via the Codex second-opinion review of the same day; it is the
unmodified download, 11,262,796 bytes). `source_data.py` reads four of its sheets, whose layout was
verified against the label cells (`python source_data.py --inspect`): *Figure 3 Panel E* (protected
exceedance probabilities of the null, unimodal and bifurcation models at the 53 window centres — the
sheet carries no time axis; `reconcile.py` maps column *i* to −285 + 30·(i−1) ms, the archived PlotFig
convention `time(TWOI(1:end-1)) + 15`), *Figure 1 Panel D* (SD of audibility per subject in %),
*Figure 2 Panel C rightmost col* (per-subject variability profile of the projected activity, 8 windows ×
5 levels, baseline-subtracted) and *Supplementary Figure 4* (the passive variability profile, 6 windows
0–100 … 500–600 ms × 6 levels, NaN at −3 dB for S1–S10). Every statistic computed from these sheets in
`RESULTS_sergent.md` is *our* calculation on the published subject-level tables, not the authors'.

## Files

| file | what it ports |
|---|---|
| `common.py` | paths, loaders, the subject-number map (datasets S1–S20 ↔ original recording numbers 01 02 03 05 06 07 08 09 11 12 13 14 15 17 19 20 22 23 24 25) |
| `decode.py` | `SoundConsciousEEG_MNE_GAT_SingleTrials.py`, section *"SINGLE TRIAL PREDICTIONS WITHOUT TEMPORAL GENERALIZATION (NO DECIMATION)"* — the file the model fitting consumes |
| `fit_models.py` | `SoundConscEEG_SingleTrialPred_ModelFitting_Twind30ms_batch.m` + `LLH_fun_null.m`, `LLH_fun_logisticB.m`, `LLH_fun_logisbimodalfixedsigma.m` |
| `bms.py` | SPM12 `spm_BMS` (+ `spm_BMS_bor`, `spm_dirichlet_exceedance`) and Meyniel's Simes correction, as called by the PlotFig script |
| `model_comparison.py` | `SoundConsciousEEG_SingleTrialPredict_ModelComp_Twind_PlotFig.m` |
| `make_figures.py` | the mean / SD-by-SNR profiles and statistics of `SoundConsciousEEG_MNE_SingleTrialPredict.m` sections (1a)–(1b) + regression-with-audibility block, on the diagonal preds |
| `source_data.py` | reader for the publisher's Source Data workbook (four sheets, see provenance above) |
| `reconcile.py` | published-vs-port pxp overlay, the C4 neural × behavioural crossings, the rmANOVA on the published passive SD profiles, the two-model (2B vs 3) BMS, evidence-size and decoder-fold/block bookkeeping |
| `refit_diagnostic.py` | the optimiser-cap diagnostic: capped fits restarted with 14,000 further evaluations at six windows, three variants |
| `run_all.sh` | the main chain (decode → fit → compare → figures), detached-friendly; `reconcile.py` and `refit_diagnostic.py` are run separately |
| `results/` | committed CSVs: per-trial metadata, all fits, LLH matrices, BMS per window (three-model and two-model), stats, behaviour, `c4_crossings.csv`, `published_passive_sd_anova.csv`, `refit_diagnostic*.csv`, `evidence_size.csv`, `decoder_fold_block_overlap.csv` |
| `figures/` | figure **data** as CSV (committed) and the PNGs (gitignored by the repo's `*.png` rule — regenerate with `make_figures.py` / `model_comparison.py` / `reconcile.py`) |

## Pipeline as ported

1. **Load** each `data_ref.mat` (`scipy.io.loadmat`, `squeeze_me=True, struct_as_record=False`): 64 channels ×
   1250 samples per trial, `trialinfo` columns 1 block, 2 SNR level, 3 vowel, 4 correct (active) /
   question type (passive), 5 response side, 6 audibility 0–10 (active) / probe response (passive).
   Keep the first **63** channels (`coi = range(63)`, drops FT10, the recording reference).
2. **Decode** (`decode.py`), per subject and session, per time sample (500 Hz, no decimation):
   `make_pipeline(StandardScaler(), LogisticRegression(C=1, L2))` in `mne.decoding.SlidingEstimator`,
   trained to separate **no sound (level 1)** from the **highest level** (6 = −5 dB; 7 in the passive
   session of S11–S20, which has the extra −3 dB level). `StratifiedKFold(10)` without shuffling, split
   separately on the {1, max} trials and on the intermediate-level trials. In each fold the classifier is
   fitted on 9/10 of the {1, max} trials, and `decision_function` (signed distance to the boundary,
   positive = sound present) is taken on the held-out {1, max} trials and on 1/10 of the intermediate
   trials, so that every trial gets exactly one value per time sample: the **projected activity**.
   Output `derived/S{n}_{session}_preds.npz` (`preds` n_trials × 1250) + `results/trials_S{n}_{session}.csv`.
3. **Fit** (`fit_models.py`): low-pass the preds at 10 Hz (12th-order Butterworth, zero-phase); average
   each trial over 53 windows of 16 samples (`TWOI = 101:15:901`, −300 … +1300 ms, window centre =
   start + 15 ms); 5-fold cross-validation **by block** (test fold k = blocks 4k−3 … 4k); for every
   window × model × fold maximise the training log-likelihood with Nelder–Mead from the original's
   starting point (initial values computed from *all* trials of the window, as in the MATLAB), then
   score the held-out trials; the model's evidence for a subject and window is the **mean over the 5
   folds of the held-out fold's summed log-likelihood** (≈ 180 active / 194 passive trials per fold).
   The optimisation is unconstrained, as in the original — no bounds were added. SNR levels are
   shifted by −1 inside the models. The passive dataset S6 (original 07) has its third trial removed
   before fitting, as in the MATLAB. The three likelihood functions are ported line by line from the
   `.m` files (parameter order and the `snr == first level` special cases included); the surrounding
   loop is a re-implementation of the batch script's logic:
   * Model 0 (null): Gaussian, `sigma, mu`.
   * Model 2B (unimodal non-linear): logistic mean anchored at the maximum level
     (`L/(1+exp(-k(x-x0))) - L/(1+exp(-k(xmax-x0))) + mu_maxsnr`), SD linear in the mean
     (`sigma_slope*Mu + sigma_intercept`), no special case for the no-sound level.
   * Model 3 (bifurcation): mixture of a low state N(mu_low, sigma) and a high state
     N(L_high/(1+exp(-k_high(x-x0))) + step, sigma) with mixing proportion `1/(1+exp(-k(x-x0)))`;
     for the first level present the proportion is forced to 0 and the high mean to `mu_low`.
4. **Compare** (`model_comparison.py`): per window, `spm_BMS([LLH0, LLH2B, LLH3])` over the 20 subjects →
   Dirichlet posterior, expected frequencies, exceedance and **protected** exceedance probabilities
   (BOR from the RFX vs null free energies), then the Simes step-up threshold on `1 − pxp` across the
   53 windows per model at α = 0.05, reported both as the MATLAB plot marks it (strict `<`, D7) and as
   conventional BH (`<=`).
5. **Profiles / stats / figures** (`make_figures.py`): mean and SD of the projected activity by SNR
   level, per subject then group-averaged (SD minus the no-sound SD, as in the paper), as time courses
   (10 Hz filtered) and for the article's eight windows 50–100 … 500–600 ms (unfiltered); repeated-
   measures ANOVAs on the profiles and on their first differences; per-subject correlation of the
   neural SD profile (levels 2–6) with the behavioural SD-of-audibility profile → t-test across
   subjects, FDR, Cohen's d; the same for the mean profiles; the Fig. 3D continuous version.

## How to run

```sh
cd workspace_demo/sergent_port            # any cwd works; paths are resolved from the file location
../../.venv/bin/pip install mne scikit-learn pandas joblib   # on top of numpy/scipy/matplotlib
NJOBS=6 nohup sh run_all.sh > ../brain_data/sergent2021/derived/logs/run_all.log 2>&1 &
# or step by step:
python decode.py --session active --subjects 1-20 --n-jobs 6      # ~12 s per subject
python decode.py --session passive --subjects 1-20 --n-jobs 6
python fit_models.py --session active --n-jobs 6                  # ~0.3 min per subject
python fit_models.py --session passive --n-jobs 6
python model_comparison.py --session active ; python model_comparison.py --session passive
python make_figures.py
python reconcile.py                       # needs the Source Data workbook + openpyxl
python refit_diagnostic.py --n-jobs 6     # ~10 min
```

Environment used for the committed results: Python 3.14.6, numpy 2.5.3, scipy 1.18.1, scikit-learn
1.9.1, mne 1.13.0, pandas 3.0.5, joblib 1.6.0, openpyxl 3.1.5, macOS (Apple silicon).

## Every deviation from the MATLAB / MNE original

**D1 — library versions.** Original: MNE-Python + scikit-learn of 2017–2019 (the decoder script is
dated Sept 2017; the fits Jan 2020), MATLAB with the Signal Processing Toolbox and SPM12. Here:
scikit-learn 1.9.1, mne 1.13.0, scipy 1.18.1. Consequences are listed as D2–D4.

**D2 — `LogisticRegression` solver.** The original used sklearn's *defaults*, which in every release
before 0.22 (Dec 2019) meant `solver='liblinear'` (L2, C = 1, tol 1e-4, max_iter 100, intercept
regularised). Today's default is `lbfgs` (intercept not regularised). The port pins
`solver='liblinear'` to reproduce the 2017 estimator. I cannot determine which sklearn release
produced the authors' preds file; `decode.py --solver lbfgs` runs the alternative.

**D3 — `StratifiedKFold`.** The original passes `random_state=0` with the default `shuffle=False`;
modern sklearn refuses that combination, so the port omits `random_state` (no effect, the split was
never shuffled). The in-order stratified allocation algorithm itself changed in sklearn 0.22, so the
fold membership of individual trials may differ from the authors' run; both are deterministic
block-contiguous splits.

**D4 — `filtfilt` edges.** MATLAB `designfilt(...,'FilterOrder',12,'HalfPowerFrequency',Wn,'butter')`
+ `filtfilt` ≙ `scipy.signal.butter(12, 10, fs=500, output='sos')` + `sosfiltfilt`. Same filter;
the two implementations pad the epoch edges slightly differently (reflection length 39 samples in
scipy), which can only affect the first/last few tens of ms of the −500 … 1998 ms epoch — the first
fitted window starts at −300 ms.

**D5 — the optimiser.** `fminsearch` → `scipy.optimize.minimize(method='Nelder-Mead')` with MATLAB's
default options: `xatol = fatol = 1e-4`, `maxiter = maxfev = 200·n_params`, non-adaptive, 5 % /
0.00025 initial simplex. Both are the Lagarias et al. 1998 algorithm with identical reflection /
expansion / contraction / shrink coefficients and the same two-part stopping rule. That does **not**
make the outputs interchangeable: most Model 2B and Model 3 runs stop at the 200·n evaluation cap
rather than at the tolerance (exit flags in `results/fits_*.csv`), and capped runs amplify tiny
numerical differences in their input into 0.1–0.6 nat differences in held-out log-likelihood
(RESULTS C8), so run-to-run identity with the MATLAB fits is not to be expected even where the
inputs agree. The port keeps the cap because that *is* the specification; `refit_diagnostic.py`
shows what lifting it does.

**D6 — negative sigma.** In MATLAB a negative SD makes `log(1/(sigma*sqrt(2*pi)))` complex, and what
`fminsearch` then does with complex objective values (real-part comparisons, magnitude sorting after a
shrink) is not something the port reproduces. The port takes `|sigma|` explicitly (Model 0, the
per-trial `Sigma` of Model 2B, and Model 3) and returns −∞ for `sigma == 0`, which changes the
objective's domain; equivalence to MATLAB is therefore **not** established in general. What can be
said is that no negative-scale evaluation was observed on the specification's own paths: no fitted
sigma is negative in any run, and `refit_diagnostic.py` instruments the objective and counts zero
evaluations with a negative `sigma` (Model 3) or a negative per-trial `Sigma` (Model 2B) along the
capped optimisation paths at its six windows (≈ 2.0 million Model 2B and 2.1 million Model 3 calls
over the active, active-lbfgs and passive variants; `results/refit_diagnostic_summary.csv`). The only
negative-scale calls anywhere are 6, in the passive Model 2B *extended* (diagnostic) paths.

**D7 — spm_BMS and the Simes correction.** `bms.py` re-implements, without importing SPM, the algorithm
of SPM12's `spm_BMS.m` (variational Dirichlet update, prior α₀ = 1, convergence ‖α − α_prev‖ < 1e-3,
exceedance probabilities from 10⁶ Dirichlet samples — seeded, so ± ~0.001 — and, for two models, the
Beta-cdf form) and `spm_BMS_bor.m` (the RFX and null free energies; BOR = 1/(1+exp(F1−F0));
pxp = (1 − BOR)·xp + BOR/K). Methods: Stephan, Penny, Daunizeau, Moran & Friston (2009) NeuroImage
46:1004 (RFX BMS, exceedance probabilities) and **Rigoux, Stephan, Friston & Daunizeau (2014),
"Bayesian model selection for group studies — revisited", NeuroImage 84:971–985,
doi:10.1016/j.neuroimage.2013.08.065** (protected exceedance probability, Bayes omnibus risk).
Sources re-implemented: <https://github.com/spm/spm12/blob/main/spm_BMS.m>,
<https://github.com/spm/spm12/blob/main/spm_BMS_bor.m>; the multiple-comparison helper is
`MCP_fromPval_fn.m` in Florent Meyniel's toolbox,
<https://github.com/florentmeyniel/matlab_generalpurpose/blob/master/MCP_fromPval_fn.m>
(tree `ee497aa`). That helper, for `'Simes'`, returns **the largest observed p-value that passes the
step-up rule** `p(i) <= α·i/V`, and the PlotFig script marks windows with `1 − pxp < threshold`
(strict), which excludes the boundary window itself. `model_comparison.py` therefore reports two
columns: `simes_sig_matlab_*` (strict `<`, what the MATLAB figure would show — 5 active windows for
the bifurcation model) and `simes_sig_*` (conventional BH `<=`, 6 windows); the figure marks the
MATLAB-literal set with dots and the extra BH window with an open circle.

**D8 — behavioural data.** The OSF `Subject_XX_Active.mat` files hold a MATLAB `table` object that
`scipy.io.loadmat` cannot decode. Audibility and identification correctness are therefore taken
from `trialinfo` columns 6 and 4 of the EEG files, i.e. from the **retained** trials (94 ± 4 % of
all trials) instead of all trials. This affects only the neuro-behavioural correlation tests and
the behavioural figure, and only marginally.

**D9 — Fig. 2C / Suppl. Fig. 4 profiles use the diagonal decoder.** The paper's Fig. 2C and Suppl.
Fig. 4 mean / SD profiles average the *temporal-generalisation* preds (decimated ×5, train-time ×
test-time square) over each window. The generalisation decoder was not ported (it is not part of the
model comparison); the profiles here average the diagonal, non-decimated preds over the same windows.
The paper's own time-sample-by-sample and model-fitting analyses use the diagonal preds. **This
readout difference is where the port's profile statistics and the published ones part company**
(RESULTS C4, C7): with the published neural profiles the C4 correlation at 200–250 ms reproduces the
paper's t = 3.06 whether the behavioural profile is theirs or ours, and with the port's diagonal
profiles it does not; and the port's non-significant passive SD statistic is a statement about the
diagonal readout, not a test of the published square-averaged profiles.

**D10 — AUC.** Classification performance is not part of the reproduced claims; where an AUC is
reported it is computed on the pooled cross-validated preds rather than per fold then averaged.

**D11 — dB labels.** Levels, not dB values, enter every computation. The data Readme says the dB
mapping is shifted by 2 dB for the original subjects 22–25 (datasets S17–S20) and is unsure about
its level 2; figure axes use the main mapping (−13 … −5 dB). I cannot determine the true labels
for S17–S20 from the files.

**D12 — a 21st block.** Datasets S4 and S11 (active) and S2 and S13 (passive) contain a block 21.
The original's 5-fold-by-block scheme tests blocks 1–20 only, so block-21 trials sit in every
training set and are never scored; the port does the same.

**D13 — rmANOVA.** `repanova` (not in the bundle) is replaced by a hand-written one-way
repeated-measures ANOVA; both the uncorrected and the Greenhouse–Geisser p-values are written.
The paper does not say which was reported.

**D14 — the passive "max level" for S11–S20.** The passive datasets S11–S20 have a 7th level
(−3 dB). The Methods say the model's `maxsnr` is "either −5 dB or −3 dB, for 10 subjects in the
passive session", and the port trains the decoder on no-sound vs the dataset's highest level (7 for
those ten). This choice is supported by an explicit branch of the original decoder script — the
section *"ANALYSIS WHERE MAXSNR = −3 dB IN THE PASSIVE SESSION, restricted to the ten last subjects"*
trains on levels {1, 7} and generalises to 2–6 for exactly those subjects (original numbers
13 … 25). The script's *other* 20-subject non-decimated section trains on {1, 6} for everyone and
would leave the level-7 trials at 0; which of the two outputs fed the authors' passive fits cannot be
determined from the bundle. `decode.py --max-level 6 --tag _max6` runs the {1, 6} alternative with the
level-7 trials *excluded* (NaN, dropped by `fit_models.py`) rather than zeroed, as a **sensitivity
analysis** of the port's own choice — not as a restoration of a sole original implementation.

**Inherited validation limitations (kept for reproduction; to be fixed in the confirmatory T1).**
Three properties of the original design carry over and bound what the cross-validated evidence
means: (i) the model-fit **initial values are computed from all trials of a window**, held-out
trials included, before each fold's Nelder–Mead run; (ii) the **decoder's cross-validation and the
likelihood cross-validation are not nested** — the projected activity of every trial comes from a
classifier trained on other trials, and the model folds are then cut by block across those same
trials; (iii) the decoder's unshuffled `StratifiedKFold` is **not block-disjoint**: per subject,
7–17 (active; median 10) and 9–16 (passive) of the 20–21 physical blocks have trials in more than one
decoder test fold (`results/decoder_fold_block_overlap.csv`), whereas the paper describes training
and test trials as coming from distinct blocks. For the Entropy study's confirmatory analysis these
are to be replaced by training-only initialisation and a nested, block-disjoint design; here they are
preserved because the target is the published pipeline.

**What the sensitivity runs showed (details in `RESULTS_sergent.md` C7–C8).** D2 is immaterial for
the decoder (liblinear and lbfgs preds agree to 0.2 % of their SD) but the evaluation-capped Nelder–
Mead runs (D5) turn that perturbation into 0.1–0.6 nat differences in cross-validated log-likelihood,
enough to move the *edges* of the group-level bifurcation period by one or two 30 ms windows while
its core (315–525 ms) is unchanged; the refit diagnostic shows the same edge sensitivity when the
cap itself is lifted. These runs characterise the port's own optimiser behaviour; they do not bound
what the authors' historical implementation produced. D14 does not change the passive ranking.

Everything else — trial selection, labels, cross-validation designs, windows, initial values,
the passive S6 trial removal, the −1 SNR shift, the mean-over-folds evidence — follows the MATLAB
batch script's logic; only the three likelihood functions are line-by-line ports.

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
derived/                                                                  OUTPUT of decode.py (npz per subject) + logs
```

## Files

| file | what it ports |
|---|---|
| `common.py` | paths, loaders, the subject-number map (datasets S1–S20 ↔ original recording numbers 01 02 03 05 06 07 08 09 11 12 13 14 15 17 19 20 22 23 24 25) |
| `decode.py` | `SoundConsciousEEG_MNE_GAT_SingleTrials.py`, section *"SINGLE TRIAL PREDICTIONS WITHOUT TEMPORAL GENERALIZATION (NO DECIMATION)"* — the file the model fitting consumes |
| `fit_models.py` | `SoundConscEEG_SingleTrialPred_ModelFitting_Twind30ms_batch.m` + `LLH_fun_null.m`, `LLH_fun_logisticB.m`, `LLH_fun_logisbimodalfixedsigma.m` |
| `bms.py` | SPM12 `spm_BMS` (+ `spm_BMS_bor`, `spm_dirichlet_exceedance`) and Meyniel's Simes correction, as called by the PlotFig script |
| `model_comparison.py` | `SoundConsciousEEG_SingleTrialPredict_ModelComp_Twind_PlotFig.m` |
| `make_figures.py` | the mean / SD-by-SNR profiles and statistics of `SoundConsciousEEG_MNE_SingleTrialPredict.m` sections (1a)–(1b) + regression-with-audibility block, on the diagonal preds |
| `run_all.sh` | the whole chain, detached-friendly |
| `results/` | committed CSVs: per-trial metadata, all fits, LLH matrices, BMS per window, stats, behaviour |
| `figures/` | figure **data** as CSV (committed) and the PNGs (gitignored by the repo's `*.png` rule — regenerate with `make_figures.py` / `model_comparison.py`) |

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
   score the held-out trials; the model's evidence for a subject and window is the **mean test
   log-likelihood over the 5 folds**. SNR levels are shifted by −1 inside the models. The passive
   dataset S6 (original 07) has its third trial removed before fitting, as in the MATLAB.
   Models, parameter order and the `snr == first level` special cases are exactly the `.m` files:
   * Model 0 (null): Gaussian, `sigma, mu`.
   * Model 2B (unimodal non-linear): logistic mean anchored at the maximum level
     (`L/(1+exp(-k(x-x0))) - L/(1+exp(-k(xmax-x0))) + mu_maxsnr`), SD linear in the mean
     (`sigma_slope*Mu + sigma_intercept`), no special case for the no-sound level.
   * Model 3 (bifurcation): mixture of a low state N(mu_low, sigma) and a high state
     N(L_high/(1+exp(-k_high(x-x0))) + step, sigma) with mixing proportion `1/(1+exp(-k(x-x0)))`;
     for the first level present the proportion is forced to 0 and the high mean to `mu_low`.
4. **Compare** (`model_comparison.py`): per window, `spm_BMS([LLH0, LLH2B, LLH3])` over the 20 subjects →
   Dirichlet posterior, expected frequencies, exceedance and **protected** exceedance probabilities
   (BOR from the RFX vs null free energies), then Simes/BH correction of `1 − pxp` across the 53
   windows per model at α = 0.05.
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
```

Environment used for the committed results: Python 3.14.6, numpy 2.5.3, scipy 1.18.1, scikit-learn
1.9.1, mne 1.13.0, pandas 3.0.5, joblib 1.6.0, macOS (Apple silicon).

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
expansion / contraction / shrink coefficients and the same two-part stopping rule, so the results
should match up to floating-point ordering. As in MATLAB, most Model 2B and Model 3 runs stop at
the 200·n evaluation cap rather than at the tolerance (the exit flags are in `results/fits_*.csv`);
the port keeps the cap because that *is* the specification.

**D6 — negative sigma.** In MATLAB a negative SD makes `log(1/(sigma*sqrt(2*pi)))` complex; `fminsearch`
then compares the real parts, i.e. behaves as if `|sigma|` had been used. The port takes `|sigma|`
explicitly (Model 0, the per-trial `Sigma` of Model 2B, and Model 3) and returns −∞ for `sigma == 0`.
Identical wherever the fitted sigma is positive, which is what the fits report.

**D7 — spm_BMS.** Re-implemented from the SPM12 algorithm (`bms.py`; SPM itself is not imported):
variational Dirichlet update, prior α₀ = 1, convergence ‖α − α_prev‖ < 1e-3, exceedance
probabilities from 10⁶ Dirichlet samples (seeded, so ± ~0.001), free energies for the BOR as in
`spm_BMS_bor`, pxp = (1 − BOR)·xp + BOR/3. `MCP_fromPval_fn(..., 'Simes')` (Florent Meyniel's toolbox,
not in the OSF bundle) is implemented as the Benjamini–Hochberg/Simes step-up rule at α = 0.05 on
`1 − pxp`; the original plots windows with `1 − pxp < threshold`, so a window exactly at the
threshold could be counted differently.

**D8 — behavioural data.** The OSF `Subject_XX_Active.mat` files hold a MATLAB `table` object that
`scipy.io.loadmat` cannot decode. Audibility and identification correctness are therefore taken
from `trialinfo` columns 6 and 4 of the EEG files, i.e. from the **retained** trials (94 ± 4 % of
all trials) instead of all trials. This affects only the neuro-behavioural correlation tests and
the behavioural figure, and only marginally.

**D9 — Fig. 2C profiles use the diagonal decoder.** The paper's Fig. 2C mean / SD profiles average the
*temporal-generalisation* preds (decimated ×5, train-time × test-time square) over each window. The
generalisation decoder was not ported (it is not part of the model comparison); the profiles here
average the diagonal, non-decimated preds over the same windows. The paper's own time-sample-by-
sample and model-fitting analyses use exactly these diagonal preds.

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
those ten). The *literal* 20-subject non-decimated section of the decoder script, however, trains on
levels {1, 6} for every subject and leaves the level-7 trials of a 7-level dataset at their
initial value 0 (they are in neither `train_cond` nor `gen_cond`), which the fitting script would
then ingest as ≈ 150 trials of exactly zero projected activity at the top level. I cannot determine
which file the authors' passive fits used. `decode.py --max-level 6 --tag _max6` runs the
alternative with the level-7 trials *excluded* (NaN, dropped by `fit_models.py`) rather than zeroed;
the result is in `RESULTS_sergent.md` C7.

**What the sensitivity runs showed (details in `RESULTS_sergent.md` C7–C8).** D2 is immaterial for
the decoder (liblinear and lbfgs preds agree to 0.2 % of their SD) but not for the fits: the
evaluation-capped Nelder–Mead runs (D5) turn that perturbation into 0.1–0.6 nat differences in
cross-validated log-likelihood, which moves the *edges* of the group-level bifurcation period by
one or two 30 ms windows while its core (315–525 ms) is unchanged. D14 does not change the passive
result.

Everything else — trial selection, labels, cross-validation designs, windows, initial values,
likelihoods, the passive S6 trial removal, the −1 SNR shift, the mean-over-folds evidence — follows the
MATLAB line by line.

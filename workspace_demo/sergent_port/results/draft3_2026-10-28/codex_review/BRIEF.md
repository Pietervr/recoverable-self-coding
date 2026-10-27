# Second opinion: three re-analyses for the Entropy SI draft 3 (R052, 28 Oct 2026)

You are asked for an independent statistical check of three small re-analyses on SAVED tables (no refitting). Work only
inside this repository (`~/Recoverable-Self-Coding`). Do not edit the three scripts or their outputs; if you need to
compute something, write your own scratch script into `workspace_demo/sergent_port/results/draft3_2026-10-28/codex_review/`
and say what it printed. Write your full record to
`workspace_demo/sergent_port/results/draft3_2026-10-28/codex_review/RECORD.md` and end your last message with a one-line
VERDICT per analysis: SOUND / SOUND WITH FIXES (list) / NOT SOUND (why).

## Context (what the paper says now, and what the deep reading of the cited sources asked)

The paper audits a two-state ("bifurcation", model 3) versus graded ("unimodal non-linear", model 2B) comparison
first published on EEG by Sergent et al. 2021 (Nat Commun 12:1149), re-implemented as a Python port in
`workspace_demo/sergent_port/` (README.md, RESULTS_sergent.md). The group comparison is random-effects Bayesian model
selection (`bms.py`, a port of SPM12 spm_BMS + spm_BMS_bor, Rigoux et al. 2014) on cross-validated held-out
log-likelihoods: a participant's score for a model at a window is the MEAN over five block folds of the held-out fold's
summed log-likelihood (the authors' convention, kept by the port).

### D6 - simulation audit, sampling unit
The paper's Table "tab:unit" compares the replicate SD of the band point estimate over 1,000 synthetic datasets with the
MEDIAN claimed SE, giving ratios 1.04 ... 3.31 at omega = 1 and 71.43 at omega = 2. Morris, White & Crowther (2019,
Stat Med) define the model-SE check in mean square ("average model SE" = sqrt(mean SE^2)). Script:
`workspace_demo/t1_access/sim_results/draft3_reanalyses_2026-10-28/d6_rms_claimed_se.py` (output `.txt`, `.csv`), on
`t1_access/sim_results/d4v12b/calibration_D4.csv`; the original median-ratio script is
`t1_access/reviews/t1_sampling_unit_2026-09-16/sampling_unit_check.py`.
Check: is RMS computed as Morris defines it; do the median ratios tie to the published table; is the reading "the RMS of
the claimed SEs tracked the replicate SD (1.03 at omega = 1, 1.05 at omega = 2), so the shortfall against the median
reflects SEs that varied between datasets and a heavy-tailed statistic, not an average SE that was too small" supported
by the numbers (consider the top-1% share of the mean square); is there anything misleading about the RMS comparison
when a handful of datasets carry most of the mean square?

### D12 - human reproduction, score scale of the pxp
The deep reading (Rigoux 2014) noted that the RFX posterior depends on the absolute scale of the scores, and the BOR is
omnibus over all three models (null, 2B, 3). Script: `workspace_demo/sergent_port/results/draft3_2026-10-28/d12_fold_sum_bms.py`
(output `d12_fold_sum_bms.txt`, CSVs), which reruns spm_bms on the fold-SUMMED held-out log-likelihood (from
`results/fits_<session>.csv` test_llh) beside the fold MEAN, for three models and for 2B vs 3 alone, and reports BOR.
The paper states: "first pxp > 0.95 at 315 ms in both curves" (port and published source-data curve), the 435-495 ms
plateau (pxp 0.999), and two-model pxp 0.62 at 315 ms and 0.81-0.86 at 435-495 ms.
The script finds: under the fold sum the three-model first crossing of 0.95 moves from 315 ms to 375 ms, and the first
run of three windows from 315 to 435 ms; the 435-495 ms plateau stays (0.998, 0.990, 0.995); BOR is near 0 for the
three-model selection on both scales (0.0007-0.0103 at the key windows) and 0.18-0.75 for the two-model selection.
Check: is the fold sum the right construction for a log-score analogue of log evidence (each trial scored once); are
the ties to the saved bms CSVs adequate; is the crossing shift real (not an rng or Monte-Carlo artefact of the 1e6
Dirichlet samples - please check the Monte-Carlo SE of pxp at 315-375 ms on both scales, e.g. by rerunning xp with
several seeds); does anything else about the reading need care (e.g. the 345 ms value 0.946 under the sum, just below
0.95; the 405 ms dip).

### D1 - passive vs active, descriptive paired comparison
Script: `workspace_demo/sergent_port/results/draft3_2026-10-28/d1_paired_active_passive.py` (output `.txt`, `.csv`),
on `results/llh_active.csv`, `llh_passive.csv`, `llh_passive_max6.csv` and the fits' n_test. Per participant, the
two-state model's held-out advantage over the graded model (per fold and per trial), active minus passive, at 315 ms and
the 435-495 ms plateau. Proposed paper sentence (descriptive only, because the sessions use separately trained
decoders): "Averaged over 435-495 ms, the two-state model's held-out advantage over the graded model was larger in the
active than in the passive session for 18 of the 20 participants (mean difference 0.0037 nat per trial, paired
t(19) = 4.2); the two sessions use separately trained decoders, so this is a description and not a test of a difference
in the underlying process."
Check: the per-trial normalisation (n_test per fold, model3 rows); the averaging over windows before differencing; the
max6 variant; whether the descriptive sentence is accurate and adequately caveated (e.g. selection: the plateau windows
were chosen from the active session's result, so a paired comparison at those windows is biased toward a positive
difference - say whether and how to state that).

Be concrete: cite file, line and number for every finding.

# Interval diagnosis and repair: Codex second opinion (brief)

27 October 2026. R052 (Entropy SI, deadline 31 Oct). Owner's instruction: "run this by codex - but we do need to find a
fix. What else is failing in the method?" Paths are relative to `workspace_demo/t1_access/` unless absolute.

You are reviewing science, not operations. Do not ssh, touch AWS or Lengau, launch runs, or edit code outside the review
file named at the end. Read-only analysis on local files is welcome; you may write and run scratch scripts under
`sim_results/interval_diag_2026-10-27/codex/`.

## Background (read these first)

- The paper: `/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/si_submission.tex` and its
  `sections/` (transfer, methods, results, discussion). The relevant failure: Section 6.2 ("The simulation audit"), Table
  `tab:sens` inclusion column, Section 6.4 (`sec:r-unit`, Table `tab:unit`), Section 5 `sec:m-amend` (the refitting
  interval and the staged screen), Supplementary S4 (omega = 2 reference).
- The interval: `analyze.py` `stratified_resample` (:312), `band_bootstrap` (:321, fixed-score percentile interval over
  concepts resampled within the 8 family strata of 8), `refit_bootstrap` (:613, the candidate replacement, same stratified
  resampling, refits the whole pipeline per resample).
- Saved rows: `sim_results/d4v12b/calibration_D4.csv` (12,000 graded datasets, 12 settings, per-concept deltas saved).
- My diagnosis (RSC 38e62fb): `sim_results/interval_diag_2026-10-27/diag_interval.py|.out` and `diag_fix.py|.out`.
- Lane A, running now on Lengau: the staged screen of the refitting interval at omega = 1 (60 datasets x first 80 of 200
  resamples; 1,905 of 4,800 slots done). Pre-declared analysis can only stop the refitting interval, not validate it.

## My claimed diagnosis (check every number and inference)

Inclusion = share of a setting's 1,000 intervals containing that setting's replicate mean of the point estimate.
Six of twelve settings fall below the 0.90 floor: tau=0.5 0.819, tau=2 0.894, alpha=1 0.885, omega=0.5 0.848,
omega=1 0.780, omega=2 0.216.

1. **Small-strata bootstrap bias.** Resampling 8 concepts within each of 8 strata gives bootstrap variance (n_h-1)/n_h =
   7/8 of the plug-in, so every interval is ~6.5% narrow (the paper already reports claimed SE = 0.935 x recomputed SE,
   Section 6.4, but reads it as harmless). Widening each interval's half-widths about the point by sqrt(8/7): tau=2 ->
   0.921, alpha=1 -> 0.902; all six passing settings stay >= 0.934. Note `refit_bootstrap` uses the same stratified
   resampling, so the running screen inherits this bias too.
2. **Unrepresented fitting variance.** tau=0.5: selection fixed at M2H in 1000/1000 datasets, misses symmetric
   (0.086/0.095), point skew -0.39, rescaling by k = SD_rep/median SE = 1.39 restores 0.951, a 10% trimmed-mean estimand
   does not help (0.777). So width, not tail or selection switching. My (unchecked) guess: the concept random-effect
   variance near its zero boundary is fitted unstably across outer folds. omega=0.5 looks like 2 plus some 3.
3. **Family asymmetry -> heavy one-sided tail at omega >= 1.** The graded family has M2S (concept random scale); no mixture
   member has one. A held-out concept with an atypical scale costs the selected mixture member a penalty growing with the
   square of the scale ratio, so per-concept deltas are heavy-tailed in the graded direction. Point-estimate skew -5.92
   (omega=1), -13.71 (omega=2); every miss has the reference below the interval (216/1000, 784/1000). At omega=2 the hits
   are mostly datasets that contain an extreme concept (max-concept share 0.62 vs 0.125 in misses). No width fix reaches
   the floor (sqrt(8/7) x 1.2: omega=1 0.873, omega=2 0.246); trimmed mean reaches 0.881 / 0.687.

## Proposed fix (critique; offer better)

F1. Correct the small-strata bias: sqrt(n_h/(n_h-1)) on the bootstrap, or a grouped/stratified jackknife.
F2. Represent fitting variance: the refitting bootstrap (running, ~470,000 core-h for a full 100x200 screen), or a cheaper
    grouped jackknife with full refit leaving out one family at a time (8 refits per dataset) with a t_7 critical value.
F3. Remove the family asymmetry: add a mixture member with a concept random scale (M3S, analogue of M2S), so neither
    family pays a quadratic penalty the other absorbs. Also closes the paper's admitted untested case (two-state with
    concept scale heterogeneity). New predictors => re-run the predictor audit and the sensitivity study.
All three require validation on new seeds against a floor fixed in advance; screening on d4v12b is development only.

## Questions

Q1. Is each of the three causes correct and correctly attributed? Reproduce the key numbers. Is anything mis-computed
    (e.g. my reference, my rescaling about the point for a percentile interval, the stratum-order assumption in
    diag_fix.py that delta_per_concept is family-blocked 8 x 8 - check it against analyze.py / simulate.py)?
Q2. Are there other causes I missed (percentile-interval shape, fold-level correlation of out-of-fold scores in the
    Bates-Hastie-Tibshirani sense, estimand definition at D=4, quadrature)?
Q3. Rank F1-F3 and any better repair you propose, by expected effect on all twelve settings and by compute cost. In
    particular: is the grouped jackknife-with-refit (F2 cheap form) statistically sound here, with 8 groups?
Q4. Lane A decision. Given this diagnosis, is the running omega=1 screen of the refitting interval still worth its compute,
    should its pre-declared analysis be complemented by a sqrt(8/7)-corrected reading (declared now, before coverage is
    computed), or should Lane A move to F1+F2 at the non-tail settings with F3 as a separate design? Say which, and why.
Q5. "What else is failing in the method?" From the paper and code, list every component of the method that is measured to
    fail, or untested where the paper relies on it, ranked by how much it threatens the paper's three claims or the held
    model study. Separate (a) measured failures, (b) untested assumptions, (c) things that look fine.
Q6. For the paper (submission 31 Oct): what, if anything, of this diagnosis can go in honestly as development evidence,
    and which sentences of the current text it would change.

## Output

Write `reviews/2026-10-27_interval_diagnosis_codex_record.md` (findings first, each with file:line or reproduced number;
a verdict line per question). Do not commit. Keep the final message to a short summary of the verdicts.

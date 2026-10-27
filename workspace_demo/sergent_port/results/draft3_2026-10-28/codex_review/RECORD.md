# Independent check of the three R052 draft-3 re-analyses

Reviewed 27 October 2026 (America/Los_Angeles), for the package labelled 28 October 2026. Baseline repository commit: `3b40bf3`. Scope: saved tables and the three submitted scripts; no refitting, decoding, or simulation of new datasets. All review artifacts are in this directory. The submitted scripts and their seven output files were left unchanged, as were the other checked inputs: the before/after SHA-256 comparison passed for all 27 explicit inputs ([independent_check.txt:66](independent_check.txt), manifest [input_sha256.json](input_sha256.json)). Existing unrelated working-tree changes were preserved.

**Outcome:** the numerical constructions reproduce. D6 needs a restrained, explicitly tail-qualified interpretation; D12 needs a scale-qualified account of the crossing and of the omnibus BOR; D1 needs a selection caveat and a small rounding correction. None requires refitting to establish these findings.

## Reproduction record and reference conventions

All `file:line` references below are repository-relative unless a directory alias is given. Line numbers refer to this reviewed package. For compactness:

- `R/` = `workspace_demo/sergent_port/results/`.
- `D/` = `workspace_demo/sergent_port/results/draft3_2026-10-28/`.
- `C/` = `workspace_demo/sergent_port/results/draft3_2026-10-28/codex_review/` (this directory).
- `S/` = `workspace_demo/t1_access/sim_results/draft3_reanalyses_2026-10-28/`.
- `U/` = `workspace_demo/t1_access/reviews/t1_sampling_unit_2026-09-16/`.
- `P/` = `workspace_demo/sergent_port/`.

I wrote and ran my own `C/independent_check.py`, rather than executing the three scripts (which would overwrite their outputs). Command from the repository root:

```sh
.venv/bin/python -B workspace_demo/sergent_port/results/draft3_2026-10-28/codex_review/independent_check.py
.venv/bin/python -B workspace_demo/sergent_port/results/draft3_2026-10-28/codex_review/supplemental_checks.py
```

Both exited successfully. Full stdout is saved in `C/independent_check.txt` and `C/supplemental_checks.txt`. Environment: Python 3.14.6, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1 (`C/independent_check.txt:1`). The main scratch script independently recomputes D6, verifies complete human-table keys and denominators, reruns BMS with the original RNG sequence, implements its own deterministic variational updates/free energies, evaluates exceedance probabilities by gamma quadrature, checks ten RNG seeds, and reconstructs D1 directly from both score tables and fit tables (`C/independent_check.py:66`, `:119`, `:142`, `:154`, `:227`, `:241`).

The supplemental check also verified the input hashes after the record was written and checked that all explicit alias/file/line references were in range (`C/supplemental_checks.txt:17–18`).

The local commit attempt was blocked by this session's filesystem permissions: `fatal: Unable to create '/Users/pietervanrooyen/Recoverable-Self-Coding/.git/index.lock': Operation not permitted`. The review files are saved in the working tree; the failed `git add` did not stage them. No permission escalation or push was attempted.

Generated numerical artifacts: `d6_independent.csv`, `d12_same_seed.csv`, `d12_exact.csv`, `d12_mc_seeds.csv`, `d1_independent.csv`, and `d1_participants.csv`. The name `d12_exact.csv` means deterministic integration **conditional on the variational posterior**, not exact integration of the entire Bayesian model or verification that held-out scores are log marginal likelihoods.

The current SI manuscript containing `tab:unit` is not in the supplied repository files. Thus the D6 manuscript tie below is to the saved original table and the numbers supplied in the brief, rather than a claim to have inspected the current external manuscript. The published human-curve tie uses the already saved overlay, not a fresh reconstruction of the publisher's workbook (`P/reconcile.py:45–55`).

## D6 — RMS claimed SE and the sampling-unit interpretation

### Calculation and tie: sound

Morris, White & Crowther's definition is `sqrt(mean(SE_i^2))`; the empirical SE is the sample SD of the replicate estimates. Their accepted preprint states the mean-square target in §5.2, at HTML line 420 ([primary source](https://arxiv.org/html/1712.03198v3#S5.SS2)). The submitted implementation uses `statistics.stdev(pts)` and `sqrt(sum(s*s)/len(se))` exactly (`S/d6_rms_claimed_se.py:58–59`). Dividing the sum of squared SEs by **1,000**, while the empirical sample variance uses **999**, is correct; these estimate different expectations. The top-1% share is correctly the sum of the ten largest squared SEs divided by the sum of all 1,000 squared SEs (`S/d6_rms_claimed_se.py:60–65`).

The source SHA-256 is `7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb` (`S/d6_rms_claimed_se.py:22–28`). Independent checks confirmed **12,000 successful, finite, unique setting/replicate rows, 1,000 per setting**, with positive SEs; all twelve re-analysis rows and all original median ratios matched (`C/independent_check.py:68–106`; printed result `C/independent_check.txt:21`). No failed-row selection explains the result.

In the original table's order, the median ratios round to **1.04, 1.12, 1.39, 1.12, 1.12, 1.13, 1.24, 1.08, 1.09, 1.53, 3.31, 71.43** (`U/sampling_unit.csv:2–13`; original definition `U/sampling_unit_check.py:42–48`). The independent RMS ratios, in the same order, are **1.0354, 1.1107, 1.3560, 1.0882, 1.0962, 1.1260, 1.2257, 1.0668, 1.0845, 1.1626, 1.0322, 1.0545** (`C/independent_check.txt:3–17`). Agreement at the two high-ω settings should not be generalized to every setting: for example M2H τ = 0.5 still gives SD/RMS **1.3560**, and M2K α = 1 gives **1.2257** (`C/independent_check.txt:5`, `:9`).

### Numerical reading: qualify the tail and the word “average”

- **ω = 1:** replicate SD **0.3554945590**, median SE **0.1072689236**, arithmetic mean SE **0.1853239121**, RMS SE **0.3444045958**; SD/median **3.31404984**, SD/RMS **1.03220039**. The ten largest SEs carry **54.225206%** of the mean square; the largest alone carries **18.019899%** (`C/independent_check.txt:13–14`; submitted result `S/d6_rms_claimed_se.txt:14`).
- **ω = 2:** replicate SD **23.20973624**, median SE **0.3249303343**, arithmetic mean SE **3.373222616**, RMS SE **22.01115754**; SD/median **71.42988446**, SD/RMS **1.05445323**. The ten largest SEs carry **95.212139%** of the mean square; the largest alone carries **31.973543%** (`C/independent_check.txt:17–18`; submitted result `S/d6_rms_claimed_se.txt:15`).

These support “the RMS was close to the replicate SD in these saved replicates.” They also show why the median ratio cannot, by itself, establish downward bias in the **mean-square** uncertainty estimate. The median is a useful description of the typical reported SE, but comparing it with an unconditional, tail-sensitive replicate SD does not put the two quantities on the same calibration target (`S/d6_rms_claimed_se.py:58–67`; the contrasting numerical values above).

The tail is present in both sides of the RMS comparison. Those same ten largest-SE datasets account for **55.400423%** and **94.570336%** of the centered point-estimate sum of squares at ω = 1 and 2, respectively (`C/independent_check.txt:14`, `:18`). For example, at ω = 2 the largest case is replicate **294**, estimate **−418.5422175**, SE **393.5847527**, in `workspace_demo/t1_access/sim_results/d4v12b/calibration_D4.csv:10669`; replicate **474**, estimate **−401.3474627**, SE **379.7750485**, is at `:11710`. At ω = 1, replicate **889**, estimate **−5.739148552**, SE **4.623225879**, is at `:3894` (`C/supplemental_checks.txt:10–15` verifies the physical CSV line numbers).

This is evidence of an extreme empirical tail, rather than proof of a particular tail distribution, existence of population moments, or the cause of that tail. It does **not** establish that a typical dataset's interval is calibrated, that normal approximations hold, that the estimate is unbiased, or that coverage is correct. Nor does it establish that the sampling unit is generally adequate. Those are separate questions; an aggregate second-moment match alone does not answer them. The primary source likewise distinguishes model-SE accuracy from bias and confidence-interval coverage ([Morris et al., §5.2](https://arxiv.org/html/1712.03198v3#S5.SS2)).

Additional influence diagnostics printed by the scratch script reinforce that distinction:

- Removing the ten largest-SE rows jointly from both sides gives SD/RMS inputs **0.23733308 / 0.23418795** at ω = 1 and **5.1068714 / 4.840565** at ω = 2. These are deletion diagnostics, **not** alternative estimates of the original unconditional target (`C/independent_check.txt:15`, `:19`).
- The concentration index `(sum SE²)² / sum SE⁴` is only **17.99** and **4.54** equal-weight contributors, respectively. This describes concentration, not an effective sample size for a confidence interval (`C/independent_check.py:93`; `C/independent_check.txt:14`, `:18`).
- Delta-method MCSE estimates for RMS are **0.04026** and **5.1580**, about 12% and 23% of RMS. These are themselves unreliable tail-sensitive estimates when so few rows dominate. They are not MCSEs for SD/RMS. The numerator and denominator share the extreme datasets; indeed paired delete-one SD/RMS ranges are quite narrow: **1.02476–1.03444** and **1.05212–1.05894** (`C/independent_check.py:94–102`; `C/independent_check.txt:14–19`). It would be wrong to calculate uncertainty in the ratio by treating its two components as independent.

The proposed phrase “not an average SE that was too small” is too broad. The **arithmetic** mean SE is still smaller than replicate SD by factors **1.9182** and **6.8806** (`U/sampling_unit.csv:12–13`). “Average model SE” is defensible only if explicitly defined as Morris's RMS. Even that RMS is numerically below SD by about 3% and 5%; these data do not justify an assertion of exact calibration.

**Suggested manuscript wording:** “Across the 1,000 saved replicates, the empirical SD divided by the RMS claimed SE was 1.03 at ω = 1 and 1.05 at ω = 2, compared with 3.31 and 71.43 when the denominator was the median claimed SE. This difference reflects substantial between-dataset variation and extreme empirical tails: the largest 1% of SEs contributed 54% and 95% of their mean square. The near agreement of these aggregate second moments does not establish interval calibration or a generally adequate sampling unit.” Numerical sources: `C/independent_check.txt:13–18`.

**D6 VERDICT: SOUND WITH FIXES — define “average model SE” as RMS, report 54%/95% tail concentration, and limit the conclusion to this aggregate second-moment comparison.**

## D12 — fold-summed scores, pxp scale, and BOR

### Construction and saved-table ties: sound, with an evidence caveat

Summing held-out log scores across the five folds is the natural total cross-validated log-score construction:

`L_CV(s,m,w) = sum_f sum_{i in test_f} log p_m(y_i | fitted training fold f)`.

Each **scored** trial contributes once. The test sets are non-overlapping blocks 1–4, 5–8, …, 17–20 (`P/fit_models.py:118–126`), and likelihoods sum natural logs (`P/fit_models.py:58–93`). There is an important boundary to “each trial”: block-21 trials, where present, enter training but are never scored (`P/fit_models.py:11–13`; `P/README.md:214–216`). The score is not a sum of five independent participant observations; BMS still has **20 participant rows** at each window (`D/d12_fold_sum_bms.py:56–68`).

This is a sensible **log-score analogue and scale sensitivity**, not a conversion of fitted cross-validated likelihoods into actual log marginal evidence. The folds use overlapping training data and fitted parameters; a sum of such scores is not a joint Bayesian marginal likelihood. The inherited all-trial initialization and non-nested decoder/model folds also persist (`P/README.md:234–245`). Thus fold sum should not be called a validated correction that establishes calibrated Bayesian probabilities about neural mechanisms.

The implementation constructs the sums and means from `test_llh` (`D/d12_fold_sum_bms.py:49–51`). I verified unique fold IDs **0–4**, complete **20 × 53 × 3 × 5 = 15,900** fit rows per session, **1,060** participant/window score rows, finite scores, and matching model denominators. Both original sessions have maximum `recomputed mean − saved llh` absolute discrepancy **0.0008 nat**, and maximum `sum − 5 × saved mean` discrepancy **0.004 nat**, consistent with separately rounded saved tables (`C/independent_check.txt:23`, `:39`; checks `C/independent_check.py:158–172`).

Using the original seed-0 RNG **sequence across all 53 windows**, I reproduced the three-model fold-mean pxp against `R/bms_active.csv` to **4.9558 × 10⁻⁷** and `R/bms_passive.csv` to **4.8864 × 10⁻⁷**. Two-model pxp ties are **4.9837 × 10⁻⁷** and **4.9860 × 10⁻⁷**; all BOR discrepancies are below **5 × 10⁻⁷**, the six-significant-figure output precision. Both scales also reproduce the submitted D12 outputs to that precision (`C/independent_check.txt:38`, `:40`; original checks `D/d12_fold_sum_bms.txt:1–3`, `:24–26`). These are adequate computational ties; they are not independent validation of the original scientific model.

Minor provenance-label fix: `D/d12_fold_sum_bms.py:55` and its text output describe `llh` as rounded to “3 decimals.” The writer actually uses **six significant figures** for both fits and `llh` (`P/fit_models.py:253–256`). The measured tie is valid; the blanket precision description should be corrected when the author next updates the script/report. I did not alter it.

### Crossing shift: real, far beyond Dirichlet Monte Carlo error

The port samples three-model xp from **1,000,000 independent gamma draws** whose normalized values have the Dirichlet posterior; the winning coordinate is unchanged by normalization (`P/bms.py:20–25`). BOR is deterministic conditional on the variational fit, and `pxp = (1−BOR)xp + BOR/3` (`P/bms.py:81–85`). Consequently the sampling MCSEs are

`MCSE(xp_hat) = sqrt(xp(1−xp)/1,000,000)` and `MCSE(pxp_hat) = (1−BOR) MCSE(xp_hat)`.

These measure numerical sampling error **only**, conditional on the saved scores and fitted posterior. They do not quantify participant uncertainty, time-of-onset uncertainty, model adequacy, or fitting uncertainty.

I independently implemented the variational updates/free energies and computed

`xp_3 = integral_0^infinity gamma_pdf(x; alpha_3) × GammaCDF(x; alpha_0) × GammaCDF(x; alpha_2B) dx`.

This removes Monte Carlo sampling of xp. Independent posterior alpha differences versus the port were below **9.4 × 10⁻¹³** and BOR differences below **1.1 × 10⁻¹⁰** over both sessions/scales (`C/independent_check.txt:38`, `:40`). The maximum quadrature error estimate was **9.99 × 10⁻¹²** (`C/supplemental_checks.txt:1`). The deterministic computations are in `C/independent_check.py:119–148`.

I also reran xp with fresh seeds **0 through 9**, **1,000,000 draws per seed**, for each scale at 315, 345, 375, and 405 ms (`C/independent_check.py:227–238`). The following gives deterministic pxp, analytical MCSE of a single one-million-draw pxp estimate, and the observed ten-seed range:

- **315 ms, mean:** **0.962850763**; MCSE **0.000170464**; range **0.962591607–0.963235906** (`C/independent_check.txt:49`).
- **315 ms, sum:** **0.899548563**; MCSE **0.000292983**; range **0.899319760–0.900134883** (`C/independent_check.txt:50`).
- **345 ms, mean:** **0.994742752**; MCSE **0.0000333482**; range **0.994713238–0.994807649** (`C/independent_check.txt:51`).
- **345 ms, sum:** **0.945843508**; MCSE **0.000217675**; range **0.945683519–0.946419127** (`C/independent_check.txt:52`).
- **375 ms, mean:** **0.996207143**; MCSE **0.0000261322**; range **0.996175068–0.996236779** (`C/independent_check.txt:53`).
- **375 ms, sum:** **0.990781529**; MCSE **0.0000868983**; range **0.990657761–0.990896190** (`C/independent_check.txt:54`).
- **405 ms, mean:** **0.983670281**; MCSE **0.000100968**; range **0.983504310–0.983832364** (`C/independent_check.txt:55`).
- **405 ms, sum:** **0.642698593**; MCSE **0.000472542**; range **0.641889406–0.643521195** (`C/independent_check.txt:56`).

The seed SDs, means, and xp MCSEs are also printed at those lines; every seed is archived in `C/d12_mc_seeds.csv`. Cellwise seed-0 runs start a fresh RNG and therefore need not equal the submitted seed-0 curve, which advances the same RNG through preceding windows (`D/d12_fold_sum_bms.py:61–66`). The full-sequence tie was checked separately above.

The sum-scale 345 ms value is about **19.09 MCSE below 0.95**, so “just below” is fair in absolute probability but should not imply unresolved Monte Carlo ambiguity (`C/independent_check.txt:52`). At 315 ms the mean and sum values are **75.39** and **172.20 MCSE** from the threshold, on opposite sides (`:49–50`). Saved-score rounding does not explain the changes either: using reconstructed fold means or five times the saved `llh` changes these key-window deterministic pxps by at most **0.00018635**, without changing a crossing (`C/independent_check.txt:24–37`).

The deterministic full-curve threshold lists reproduce the submitted lists exactly:

- Mean scale above 0.95: **315, 345, 375, 405, 435, 465, 495, 525, 555, 615 ms**; first crossing and first three-window run both start **315 ms** (`C/independent_check.txt:42`).
- Sum scale above 0.95: **375, 435, 465, 495, 525, 555 ms**; first crossing **375 ms**, first three-window run **435 ms** (`:43`). The **405 ms dip to 0.64270** prevents a claim of sustained >0.95 from 375 ms (`:31`, `:56`).
- Passive: no window above 0.95 on either scale (`:44–45`).

The three-window run here means **three consecutive windows each with pxp > 0.95** (`D/d12_fold_sum_bms.py:39–42`, `:86–92`). It must not be conflated with the earlier “model 3 highest-ranked for at least three windows” definition in `P/reconcile.py:37–41`, `:75–76` or `P/RESULTS_sergent.md:157`.

At 435/465/495 ms, deterministic sum-scale pxps are **0.998191697 / 0.989823329 / 0.994576674** (`C/independent_check.txt:33`, `:35`, `:37`), consistent with submitted **0.998 / 0.990 / 0.995** (`D/d12_fold_sum_bms.txt:15–17`). The plateau survives the **>0.95 criterion**; it does not stay numerically at 0.999.

The saved published-vs-port overlay gives first crossing **315 ms in both original curves** (`C/independent_check.txt:46–47`; `P/RESULTS_sergent.md:155–158`). That remains a valid reproduction statement **under the authors' fold-mean convention**. This re-analysis changes the port's scores; it does not rescale/recompute the published source-data curve, whose underlying likelihoods are not supplied here. Do not say the published crossing has moved.

### BOR and interpretation

SPM defines BOR over the model set supplied to it, with null hypothesis equal **population model frequencies**; it uses `pxp=(1−bor)xp+bor/K` ([SPM `spm_BMS.m`, lines 5–21, 62–87, 119–120](https://raw.githubusercontent.com/spm/spm12/main/spm_BMS.m); [SPM `spm_BMS_bor.m`, lines 22–37](https://raw.githubusercontent.com/spm/spm12/main/spm_BMS_bor.m)). The local port applies the corresponding updates (`P/bms.py:63–85`). Adding fivefold score magnitude therefore changes assignments, posterior counts, and BOR; it need not monotonically increase model 3's population-frequency exceedance probability.

For the explicitly designated **315, 435, 465, 495 ms** windows, three-model BOR on the two scales ranges **0.000714922–0.0102931** (`D/d12_fold_sum_bms_active.csv:22`, `:26–28`). A small value can be driven by the null **model 0** losing, while 2B and 3 remain hard to separate. The equal-frequency omnibus null is distinct from model 0; low three-model BOR is not a pairwise 3-vs-2B result.

The separate two-model results confirm the distinction. Mean-scale pxp3 is **0.619662** at 315 ms and **0.862493 / 0.815542 / 0.810534** at the plateau; sum-scale values are **0.626944** and **0.910174 / 0.805699 / 0.808487**. Two-model BOR over these four windows/scales ranges **0.177467–0.745090** (`D/d12_fold_sum_bms_active.csv:22`, `:26–28`). Neither active two-model curve exceeds 0.95 anywhere (`D/d12_fold_sum_bms.txt:6–7`). For two models xp uses an analytic beta CDF, so those numbers have **no Dirichlet sampling error** (`P/bms.py:76–80`). Do not carry the omnibus low-BOR reading into that pairwise comparison.

The stated BOR ranges apply to those **four key windows**, not all nearby windows: at 405 ms the sum-scale three-model BOR is **0.0116359** and two-model BOR **0.779999** (`D/d12_fold_sum_bms_active.csv:25`). Likewise, raw 0.95 crossing is a reporting criterion rather than an across-window error-controlled onset estimate; the port's separate across-window marking procedure is documented in `P/README.md:91–95`.

**Suggested manuscript wording:** “Under the authors' fold-mean score convention, the port and published source-data curves first exceeded pxp = 0.95 at 315 ms. Replacing the port's fold mean by the total held-out log score moved its first crossing to 375 ms and its first three consecutive windows above 0.95 to 435 ms, because of a dip at 405 ms. The 435–495 ms plateau remained above 0.95 (0.998, 0.990, 0.995). These changes exceeded Monte Carlo and saved-score rounding error. This is sensitivity to the scale of cross-validated scores supplied as evidence; low three-model BOR is an omnibus result and does not establish decisive 3-vs-2B preference.” Numerical sources: `D/d12_fold_sum_bms.txt:4–17`; `C/independent_check.txt:24–56`.

**D12 VERDICT: SOUND WITH FIXES — qualify the 315 ms reproduction by fold-mean scale; distinguish the 375 ms crossing from the 435 ms three-window run and the 405 ms dip; retain the CV-score/evidence and omnibus/pairwise caveats; correct “3 decimals” to six significant figures.**

## D1 — active-minus-passive participant comparison

### Normalization and averaging: sound

The submitted script uses `model3` fit rows to obtain mean held-out `n_test` for each participant/window, then computes `(S3−S2B)/mean(n_test)` (`D/d1_paired_active_passive.py:34–40`). Since `S_m = sum_f L_mf / 5`, this equals

`sum_f (L_3f − L_2Bf) / sum_f n_test,f`.

This is the correct **trial-weighted average** held-out advantage for the scored trials. It is not the unweighted mean of the five per-fold per-trial ratios when fold sizes differ. Using model-3 counts is valid here because model 0, 2B, and 3 have identical `n_test` in every matched participant/window/fold, and all counts are positive (`C/independent_check.py:159–165`; printed checks `C/independent_check.txt:23`, `:39`, `:41`). Do not sum `n_test` across all three models, which would count each trial three times.

Actual fold sizes vary: **122–192 active**, **132–224 passive**, **132–192 passive_max6**. Mean scored trials per fold are **179.78**, **194.23**, and **179.06**, respectively (`C/supplemental_checks.txt:3`, `:5`, `:7`; `C/independent_check.txt:58–60`). Denominators refer to scored trials, including the block-21 exception described under D12, rather than every retained trial in the session.

The script joins on participant and time, averages the selected **435, 465, 495 ms** window advantages **within each participant/session**, then differences active minus passive and applies the paired summary to **20 participants**, giving **19 degrees of freedom** (`D/d1_paired_active_passive.py:24–25`, `:48–59`). The operation is correct and does not treat the 60 participant/window values as independent. With complete matching windows, averaging within-participant differences would give the same result by linearity. My checks found all 20 participants and all 53 windows in each session, with no dropped joins (`C/independent_check.py:166–167`, `:263–269`; `C/independent_check.txt:65`).

### Saved numbers and the proposed sentence

For the ordinary passive session, plateau per-trial means are **0.00267882 active** and **−0.00107582 passive**; paired difference **0.00375464 nat per trial**, SD of differences **0.00398684**, **t(19) = 4.21167**, and **18/20** active greater than passive (`D/d1_paired_active_passive.csv:11`). The independent calculation gives **0.003754643510**, **4.21167066**, and **18/20** (`C/independent_check.txt:62`). All twenty submitted summary rows, across windows, units, and passive variants, reproduce (`:65`; `C/d1_independent.csv:2–21`).

The default comparison therefore supports the count and `t = 4.2`, but **0.0037 is not the conventional four-decimal rounding** of its mean. Use **0.00375** or **0.0038**. The number **0.0037** is appropriate to the **max6** mean **0.00370093**, whose t is **3.96228**, not 4.2 (`D/d1_paired_active_passive.csv:21`). Avoid inadvertently mixing those two rows.

The mean advantage is larger for 18 participants; this does **not** mean model 3 wins in all those 18 active participants. Plateau advantages are positive for **15/20 active** and **8/20 passive** (`D/d1_paired_active_passive.csv:11`). The proposed phrase “larger held-out advantage” is correct; “18 participants favored the two-state model” would not be.

Using only the saved fold `test_llh` values directly changes the ordinary passive plateau mean to **0.003755171786**, t to **4.21228121**, still **18/20**. Thus separately rounded likelihood files have no material effect on the sentence (`C/independent_check.txt:62`). At **315 ms**, the ordinary comparison is only **0.000873987 nat per trial**, **t = 0.712224**, **12/20** positive; direct-from-fits gives **0.000875459**, **t = 0.713523**, also **12/20** (`:61`; saved row `D/d1_paired_active_passive.csv:3`). The plateau finding should not be described as a comparable active-minus-passive result at 315 ms.

### max6: similar descriptive result, narrower interpretation

The max6 plateau gives **0.003700928676 nat per trial**, SD **0.004177153853**, **t(19) = 3.96228073**, and **18/20** positive; direct-from-fits gives **0.003701194176**, **t = 3.96319878**, again **18/20** (`C/independent_check.txt:64`; saved row `D/d1_paired_active_passive.csv:21`). At 315 ms it gives **0.001043193641**, **t = 0.840227**, **12/20** (`C/independent_check.txt:63`; saved row `D/d1_paired_active_passive.csv:13`). Thus the qualitative plateau comparison persists in this variant.

But max6 is not a control that isolates decoder training level. It changes the passive training contrast for S11–S20 **and excludes level-7 trials from scoring**, while active and passive still use separately learned decoders (`P/README.md:222–232`). For instance, S11's scored passive trial count changes **1,026 → 886**, and S15's **1,101 → 942** (`C/supplemental_checks.txt:4`, `:6`). All saved score entries for S1–S10 are identical between passive and max6 (`:8`). The max6 result should be reported as sensitivity to the combined training/trial-selection variant, not proof that separately trained decoders or session stimulus composition cannot explain the contrast.

### Required interpretive fix: selection as well as separate decoders

The decoder caveat is appropriate: these are comparisons of held-out fits to different learned readouts, not a controlled manipulation establishing a latent-process change (`D/d1_paired_active_passive.py:9–11`; `P/README.md:63–70`, `:222–232`). More precisely, a pure common affine rescaling, with correspondingly transformed model densities, cancels its log-Jacobian in a within-session model log-score difference; the concern is the different learned projections, training conditions, and trial composition, rather than scalar amplitude units alone. This is an algebraic observation, not a claim that the capped numerical optimizer is exactly equivariant. It follows from the difference `S3−S2B` used in `D/d1_paired_active_passive.py:39` and the common-data likelihoods in `P/fit_models.py:58–93`.

The proposed sentence is nevertheless **not adequately caveated yet**. The three plateau windows were chosen from the active-session result, as specified in the review brief (`C/BRIEF.md:57–60`; the strong active plateau is documented at `P/RESULTS_sergent.md:173–183`). Selecting windows for strong active model-3 preference and then comparing active with passive in those same windows favors a positive active-minus-passive contrast. This affects the **estimated difference itself and the 18/20 count**, not just the t-test p-value. Pairing participants and dividing by trial count do not remove this selection effect. I have not estimated or subtracted the size of this bias.

The nominal p-values are arithmetically correct (**0.000472567** ordinary passive, **0.000835137** max6), but should not be used as confirmatory evidence for a prespecified session contrast (`D/d1_paired_active_passive.csv:11`, `:21`). Keeping the t statistic as a descriptive standardized paired mean is possible if the selection caveat is explicit; omitting the inferential p-values from the paper is preferable. Separately trained decoders are an additional limitation, not a remedy for outcome-based window selection.

**Suggested manuscript wording:** “Across the three windows centred at 435, 465 and 495 ms, selected from the active-session result, the two-state model's mean held-out advantage over the graded model was larger in the active than passive session for 18 of 20 participants (mean paired difference 0.00375 nat per scored trial; descriptive paired t(19) = 4.2). Selecting the windows from the active result can favor a positive difference, and the sessions use separately trained decoders; this is a post hoc description, not a confirmatory session comparison or evidence of a difference in the underlying process.” Numerical source: `D/d1_paired_active_passive.csv:11`, independently checked at `C/independent_check.txt:62`.

Optional accompanying sensitivity sentence: “The passive max6 variant gave a similar descriptive contrast (0.00370 nat per scored trial; t(19) = 3.96; 18/20 participants), but changed both the passive decoder training contrast and the scored trial set.” Sources: `D/d1_paired_active_passive.csv:21`; `P/README.md:222–232`.

**D1 VERDICT: SOUND WITH FIXES — add the active-selected-window bias caveat, change the default mean to 0.00375 (or 0.0038), keep the comparison descriptive, and describe max6 as a combined decoder/trial-selection sensitivity.**

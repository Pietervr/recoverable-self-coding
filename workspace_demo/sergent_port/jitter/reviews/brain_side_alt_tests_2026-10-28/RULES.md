# RULES — the brain-side same-data comparison (declared 28 October 2026, before the first computation)

Job brief: Unimog `prompts/2026-10-28_si_brain_side_alt_tests_job.txt` (R052, Entropy SI). The literature's own
two-state tests, as defined, run on exactly the matched comparison's synthetic EEG sets (the S4b validation manifest of
`DESIGN_jitter.md` rev 7 §7.3), beside the two rules already scored on those sets: the inherited per-window rule and the
matched comparison's own verdict. Post hoc, descriptive; no refit of any model of the matched comparison. Every rule
below is fixed here and is not changed after the first run. The script is `brain_side_alt_tests.py` beside this file;
its constants restate these rules and the script refuses to run the battery until the tie check has passed.

## 1. The data

- The 1,150 validation sets: W1–W4, O1–O5 and E1 at R = 100 sets each, T1 and T2 at R = 50 (T3 is ABSENT: the λ_T3
  search failed, `results/s4/s4a.json`). Twenty synthetic participants per set, 53-window vectors, levels k = 0..5
  with k = 0 the no-sound level, the base participant's trial counts and block labels.
- Regeneration: the S4 code path itself, `s4.make_synthetic("validation", setting, r, m, base, bases, lam)` with
  `base = s4.set_members("validation", setting, r)[m]`, `lam = {"E1": λ_E1}` read from `results/s4/s4a.json`
  (certified λ_E1 = 1.0, mode "hit"), the frozen generator assets `results/generators/S{n}_active_{G3,B3}.npz` (their
  sha256 is in `results/s4/run_config.json`) and the cached real bases `results/generators/bases_W53_active.npz` (O5
  resamples them). Seeds: `simulate.seed_for("validation", setting, r, m)` for the draw, `seed_for(..., 0, "set")`
  for the member draw — the frozen seeds of the run. Nothing is refitted and nothing is filtered or averaged again.
- Platform: this job runs on the Mac (arm64). `S2_REPORT.md` 11.1 records that the x86 hosts regenerate the same seeds
  bit-differently from the Mac (`data_id` differs for all twenty members of W2 set 0), so the saved `data_id` is NOT
  expected to match; the tie (§5) is made on what the Mac can reproduce.
- Readout: the 16 primary windows (indices 18..33 of the 53; centres 255–705 ms), the per-trial decoder distance
  averaged within each window — the same numbers the matched comparison fits. No other window is tested.

## 2. Centring, scaling, pooling

- Centring (fixed by the brief): for each synthetic participant and window, subtract that participant's mean over ALL
  its level-0 (no-sound) trials. The tests are not cross-validated, so the "training" no-sound mean is the mean over
  every no-sound trial of the participant (block 21 included).
- Scaling, PRIMARY reading: none. The centred distance stays in each participant's decoder units, as the model side
  pooled its raw readout over concepts and carriers.
- Scaling, SENSITIVITY reading (reported beside, never in place of): divide the centred distance by the participant's
  level-0 standard deviation (ddof = 1) at that window, so every participant's no-sound distribution is standardised.
- Pooling: at a window w and level k the test sees the centred (or scaled) distances of all 20 participants' trials at
  level k pooled into one sample (about 2,800–3,000 values; the per-participant level counts are the bases').

## 3. The tests at one window

Levels: k = 1..5 are tested; k = 0 enters the variance profile only.
NEAR-THRESHOLD LEVELS, declared by the model side's rule: the levels at which the mean occupancy A(k) of the 20
fitted B3 generators lies in [0.18, 0.82]. Over the stored generators the mean A(k) is 0.146, 0.313, 0.553, 0.774,
0.903 at k = 1..5 (median 0.142, 0.333, 0.560, 0.745, 0.904), so TEST_LEVELS = (2, 3, 4), as on the model side.

- B1 Hartigan's dip test of unimodality (Hartigan & Hartigan 1985; `diptest` 0.12.0, `diptest.diptest(x)`, the
  interpolated p-value table, as the model side). DECLARED call at window w: any k in TEST_LEVELS with
  p < 0.05 / 3 (Bonferroni over the three levels). ALL-LEVELS reading beside it: any k in 1..5 with p < 0.05 / 5.
- B2 Two-component against one-component Gaussian mixture by BIC (`sklearn.mixture.GaussianMixture`,
  `covariance_type="full"`, `n_init=5` for the two-component fit, `random_state` = a deterministic draw from
  (`seed_for("validation", setting, r, 0, "set")`, w, k)). ΔBIC = BIC(1) − BIC(2). DECLARED call at window w: the
  largest ΔBIC over TEST_LEVELS > 10 (Kass & Raftery 1995, "very strong"); the ΔBIC > 0 reading beside it; both
  also over all levels 1..5 beside. No multiplicity adjustment exists for BIC; the any-level rule over the declared
  levels is the rule, as on the model side.
- B3 The variance-burst signature (Sergent et al. 2021: the inter-trial variance peaks at intermediate levels; v1 S9 /
  `app:decomp` says why it is a signature and not a test). For participant p, window w, level k = 0..5:
  v_p(w, k) = the variance (ddof = 1) of p's centred distances at level k. The profile is V(w, k) = the mean of
  v_p(w, k) over the 20 participants (the within-participant inter-trial variance, averaged; pooling the trials
  instead would add between-participant amplitude differences to the variance, which is not the published signature).
  DECLARED "burst at window w": k* = argmax_k V(w, k) is strictly interior, k* in {1, 2, 3, 4}, AND
  V(w, k*) ≥ (1 + δ) · max(V(w, 0), V(w, 5)) with MARGIN δ = 0.10 (declared: the per-participant variance from about
  150 trials has relative sampling SD about 12 %, the 20-participant mean about 2.6 %, so a flat profile clears a 10 %
  margin by chance rarely). The δ = 0 reading (a plain interior maximum) is reported beside it. The scaled variant
  (section 2) is reported for B3 as well.

## 4. From windows to a set

- WINDOW RULE, DECLARED (the published per-window reading's logic): a set "reads two-state" under a test when the test
  calls at ≥ 3 CONSECUTIVE windows of the 16. ANY-WINDOW reading beside it: a call at at least one of the 16.
  Bonferroni is over levels only, as on the model side; the run requirement is the only control over the 16 windows,
  and the any-window reading has none (stated as such).
- B4 The inherited per-window rule: RESTATED from the saved `inherited_lme` of every row (no refit) through
  `simulate.inherited_group_summary` (spm_BMS per window, the call = a run of ≥ 3 consecutive windows with M3 the
  highest pxp whose first window lies inside the primary span). Settings with an inherited run: W1–W4, O1–O5, T1. T2
  and E1 had none (`s4.MANIFEST`) and are reported as "not run".
- B5 The matched comparison's own verdict: RESTATED from the saved per-row scores through `decide.set_primary` on
  `s4.set_scores` (the frozen failure rule, DESIGN §5 (d)); "reads two-state" = POSITIVE. UNAVAILABLE sets are
  reported beside the count (the article's gate (b) counts them as POSITIVE; this table reports the verdicts as
  saved). At E1 the BOUNDED field is restated with ε from `s4a.json`.
- Counts per setting with the exact one-sided 95 % Clopper–Pearson bound the article uses: the UPPER bound on
  W1–W4 and O1–O5 (a bound on the false two-state rate where the generating family is graded; O5's generating family
  is unknown and its bound is reported with that said), the LOWER bound on T1, T2 and E1 (a bound on the detection
  rate). T2's B4 and B5 columns are "not run" and "50 UNAVAILABLE".
- B6 (optional, descriptive): the 20 real participants' active session (`bases_W53_active.npz`: the real 53-window
  means, levels and blocks after the inherited preprocessing) as one set, B1–B3 by the same rules, no bound (n = 1).

## 5. The tie check (before any B1–B3 number)

1. Member draws: `s4.set_members("validation", setting, r)` must equal the saved `base` of every row of every set of
   every instantiated setting (exact integers; a platform-independent draw). Any mismatch stops the job.
2. T1, all 50 sets regenerated on the Mac: n_trials equals the saved row's; `data_id` compared and the match count
   recorded (expected to differ, section 1); the inherited pipeline (`simulate.inherited_fits`) is RERUN on the
   regenerated participants and compared row by row with the saved `inherited_lme` (max absolute difference of the
   53 × 3 matrix), then `inherited_group_summary` per set gives the regenerated calls, compared with the calls from
   the saved lme. PASS: the regenerated T1 calls reproduce 7 of 50 with the same sets called, or disagree on at most
   one set (a near-tie moved by the platform's floating point, reported by set). More than one disagreeing set stops
   the job before any B1–B3 number.
3. B4 and B5 restated for every setting must reproduce `results/s4/summary.json`: inherited calls W1 1/100, W2–W4 and
   O1–O4 0/100, O5 39/100, T1 7/50; primaries W1–W3, O1–O4 0 POSITIVE of 100, W4 0 POSITIVE with 4 UNAVAILABLE,
   O5 12 POSITIVE, T1 49 of 50, T2 50 UNAVAILABLE, E1 99 POSITIVE 1 UNRESOLVED and 0 BOUNDED. Any difference stops the
   job.

## 6. Compute and record

12 joblib workers on the Mac (Apple M4 Max; 12 performance cores), environment `.venv` beside this file (python
3.12.14, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, joblib 1.6.0, scikit-learn 1.9.1, diptest 0.12.0, jax 0.11.1 imported
by the jitter modules, no fit run). Outputs: `tie_check.json`, `saved_restated.csv` (B4, B5 per set), `sets.csv` (one
row per set: every call and statistic under every reading), `windows.csv` (one row per set, window, level: n, dip,
p, BIC(1), BIC(2), ΔBIC, V), `summary.csv` and `table.md` (per setting), `runtime.json`, `REPORT.md`.

What is never said: a ranking of the tests, or that the published test is shown false. Each test is measured doing
what it does on sets whose generating family is known (O5 excepted), nothing more.

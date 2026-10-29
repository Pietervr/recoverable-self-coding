# The brain-side same-data comparison: the literature's own two-state tests on the matched comparison's synthetic EEG sets (28 October 2026)

Job brief: Unimog `prompts/2026-10-28_si_brain_side_alt_tests_job.txt` (R052, Entropy SI; owner 28 Oct: "a reviewer will
ask how the other methods stack up against our approach on the brain side in the example"). Rules: `RULES.md` beside
this file, declared before the first computation and unchanged. Script: `brain_side_alt_tests.py` (`--tie`, `--battery`,
`--summary`). Post hoc and descriptive: nothing of the matched comparison was refitted; the inherited per-window rule and
the matched comparison's verdicts are RESTATED from the saved S4 record. The model-side analogue is
`t1_access/sim_results/alt_tests_2026-10-25/README.md`.

## 1. The data, and how they were tied to the saved record

The 1,100 instantiated validation sets of the matched comparison (DESIGN_jitter.md rev 7 §7.3; T3 is ABSENT after the
λ_T3 search failure): W1–W4, O1–O5 and E1 at 100 sets each, T1 and T2 at 50; twenty synthetic participants per set,
53-window vectors, levels 0..5, the base participants' trial counts and blocks. Regenerated on the Mac by the S4 code
path itself (`s4.make_synthetic("validation", setting, r, m, base, bases, {"E1": 1.0})`, members from
`s4.set_members`, the frozen generator assets whose sha256 is in `results/s4/run_config.json`, seeds
`simulate.seed_for("validation", …)`). Tested: the 16 primary windows (centres 255–705 ms), the per-trial decoder
distance averaged within each window — the numbers the matched comparison fits.

Tie check (`tie_check.json`, `tie_T1_sets.csv`, `saved_restated.csv`; RULES.md §5), PASS on every declared criterion:

| Check | Result |
|---|---|
| Member draw of every set equals the saved `base` of every row | 1,100 of 1,100 sets (12 settings) |
| B4 restated from the saved `inherited_lme` (spm_BMS per window; call = a run of ≥ 3 consecutive windows with M3 highest, starting in the span) | W1 1, W2–W4 0, O1–O4 0, O5 39 of 100; T1 7 of 50 — equal to `results/s4/summary.json` |
| B5 restated from the saved scores (`decide.set_primary`, the frozen failure rule) | POSITIVE: W1–W3, O1–O4 0; W4 0 with 4 UNAVAILABLE; O5 12; T1 49 of 50; T2 0 with 50 UNAVAILABLE; E1 99 (1 UNRESOLVED), 0 BOUNDED at ε = 0.011402 — equal to `summary.json` |
| T1, all 50 sets regenerated on the Mac: trial counts | 1,000 of 1,000 rows equal |
| T1 `data_id` | 0 of 1,000 rows equal — the documented x86/arm64 rounding difference (S2_REPORT 11.1) |
| T1 inherited per-window pipeline RERUN on the regenerated participants (`simulate.inherited_fits`: 53 windows × 5 folds × 3 Nelder–Mead fits) against the saved lme | max abs difference per row: median 0.10 nat, p90 0.20, max 0.36 (window evidences of order −140 nat); pxp(M3) per set: median 0.002, max 0.038 |
| T1 group reading from the regenerated lme | 7 of 50 calls on the same sets as the saved record (16, 18, 33, 35, 36, 43, 48); the same first-run window in all 50 sets (525, 705, 615, 525, 525, 405, 405 ms for the seven) |

So the regenerated sets are the saved sets up to the platform's floating point, and the one data-derived quantity of
the saved record that the Mac can recompute reproduces it.

## 2. The declared rules (RULES.md, in brief)

- Centring: each participant's mean over all its no-sound trials subtracted per window. Primary: no scaling.
  Sensitivity: divided by the participant's no-sound SD. Pooled over the set's 20 participants at a window and level.
- Near-threshold levels (2, 3, 4): the levels at which the mean fitted B3 occupancy A(k) lies in [0.18, 0.82]
  (0.313, 0.553, 0.774 at k = 2, 3, 4; the model side's rule).
- B1 Hartigan's dip test (`diptest` 0.12.0, interpolated p table): call at a window when any declared level has
  p < 0.05/3 (Bonferroni over the three levels); the all-levels reading (k = 1..5, p < 0.05/5) beside.
- B2 Gaussian mixture by BIC (`sklearn` full covariance, one against two components, n_init 5, seeded from the set seed,
  window and level): call when the largest ΔBIC = BIC(1) − BIC(2) over the declared levels > 10 (Kass & Raftery); the
  > 0 reading beside; both over all levels beside. No multiplicity adjustment exists for BIC.
- B3 variance burst (Sergent et al. 2021's proposed clinical signature; v1 S9 / `app:decomp`): V(w, k) = the mean over
  the 20 participants of the within-participant variance (ddof 1) of the centred distance at window w, level k; burst
  at w when argmax_k V is interior (k = 1..4) and V(k*) ≥ 1.10 · max(V(0), V(5)); the margin-0 reading beside.
- Window rule: a set reads two-state under a test when it calls at ≥ 3 consecutive windows of the 16 (the published
  reading's logic); the any-window reading beside.
- B4 the inherited per-window rule and B5 the matched comparison's verdict: RESTATED from the saved S4 record, no refit.
- Bounds: exact one-sided 95 % Clopper–Pearson; upper on W1–W4 and O1–O5, lower on T1, T2 and E1.
- B6 (descriptive): the 20 real participants' active session (`results/generators/bases_W53_active.npz`) as one set.

## 3. Results

### 3.1 The table (declared readings: unscaled, levels 2–4, ≥ 3 consecutive windows; sets reading two-state, one-sided 95 % bound in parentheses)

| Setting | sets | Dip test | Mixture BIC > 10 | Mixture BIC > 0 | Variance burst | Inherited per-window rule | Matched comparison (POSITIVE) |
|---|---|---|---|---|---|---|---|
| W1 (graded, no trial variation) | 100 | 0 (0.030) | 90 (0.945) | 92 (0.960) | 0 (0.030) | 1 (0.047) | 0 (0.030) |
| W2 (graded, fitted spreads) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| W3 (graded, 80 ms latency) | 100 | 0 (0.030) | 77 (0.837) | 79 (0.855) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| W4 (graded, scale 1.0) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 2 (0.062) | 0 (0.030) | 0 (0.030); 4 UNAVAILABLE |
| O1 (time stretch) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| O2 (two components) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| O3 (level-dependent latency) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| O4 (correlated scale and latency) | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| O5 (resampled recorded trials) | 100 | 0 (0.030) | 98 (0.996) | 98 (0.996) | 100 (1.000) | 39 (0.477) | 12 (0.187) |
| T1 (two-state, fitted) | 50 | 0 (0.000) | 44 (0.777) | 48 (0.879) | 0 (0.000) | 7 (0.068) | 49 (0.909) |
| T2 (two-state, 80 ms, occupancy halved) | 50 | 0 (0.000) | 50 (0.942) | 50 (0.942) | 0 (0.000) | not run | 0; 50 UNAVAILABLE |
| E1 (two-state at λ = 1) | 100 | 0 (0.000) | 92 (0.860) | 93 (0.873) | 3 (0.008) | not run | 99 (0.953) |
| Real data (20 participants, active) | 1 | 0 | 1 | 1 | 1 | — | — |

Upper bounds on W1–W4, O1–O5 (O5's generating family is unknown, so its bound is on the call probability under the
resampling law, not a false-call rate); lower bounds on T1, T2, E1. The inherited rule was not run on T2 and E1 in S4
(`s4.MANIFEST`). The real data's inherited reading is the published reproduction (two-state preferred from 315 ms,
`RESULTS_sergent.md`); its matched-comparison contrast is UNRESOLVED (+0.00457 [−0.00025, +0.00939], `results/s5/decision.json`).

### 3.2 The any-window reading (beside the declared rule)

| Setting | sets | Dip any | BIC > 10 any | BIC > 0 any | Burst (0.10) any | Burst (0) ≥ 3 cons. | Burst (0) any |
|---|---|---|---|---|---|---|---|
| W1 | 100 | 0 (0.030) | 97 (0.992) | 98 (0.996) | 9 (0.152) | 96 (0.986) | 100 (1.000) |
| W2 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 1 (0.047) |
| W3 | 100 | 0 (0.030) | 87 (0.921) | 92 (0.960) | 0 (0.030) | 13 (0.199) | 69 (0.766) |
| W4 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 2 (0.062) | 4 (0.089) | 4 (0.089) |
| O1 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 1 (0.047) |
| O2 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 1 (0.047) | 2 (0.062) |
| O3 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 1 (0.047) |
| O4 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 0 (0.030) |
| O5 | 100 | 11 (0.176) | 100 (1.000) | 100 (1.000) | 100 (1.000) | 100 (1.000) | 100 (1.000) |
| T1 | 50 | 0 (0.000) | 49 (0.909) | 50 (0.942) | 4 (0.028) | 41 (0.707) | 50 (0.942) |
| T2 | 50 | 0 (0.000) | 50 (0.942) | 50 (0.942) | 0 (0.000) | 0 (0.000) | 0 (0.000) |
| E1 | 100 | 0 (0.000) | 98 (0.938) | 99 (0.953) | 28 (0.207) | 87 (0.801) | 99 (0.953) |
| Real | 1 | 0 | 1 | 1 | 1 | 1 | 1 |

### 3.3 Sensitivity readings (≥ 3 consecutive windows): scaled by the no-sound SD; all levels 1–5 unscaled

| Setting | sets | Dip scaled | BIC > 10 scaled | BIC > 0 scaled | Burst (0.10) scaled | Dip all levels | BIC > 10 all levels | BIC > 0 all levels |
|---|---|---|---|---|---|---|---|---|
| W1 | 100 | 0 (0.030) | 0 (0.030) | 0 (0.030) | 0 (0.030) | 0 (0.030) | 97 (0.992) | 99 (0.999) |
| W2 | 100 | 0 (0.030) | 97 (0.992) | 99 (0.999) | 0 (0.030) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| W3 | 100 | 0 (0.030) | 0 (0.030) | 1 (0.047) | 0 (0.030) | 0 (0.030) | 97 (0.992) | 99 (0.999) |
| W4 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 1 (0.047) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| O1 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| O2 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| O3 | 100 | 0 (0.030) | 96 (0.986) | 99 (0.999) | 0 (0.030) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| O4 | 100 | 0 (0.030) | 100 (1.000) | 100 (1.000) | 0 (0.030) | 0 (0.030) | 100 (1.000) | 100 (1.000) |
| O5 | 100 | 0 (0.030) | 17 (0.244) | 28 (0.363) | 100 (1.000) | 0 (0.030) | 99 (0.999) | 99 (0.999) |
| T1 | 50 | 0 (0.000) | 0 (0.000) | 1 (0.001) | 0 (0.000) | 0 (0.000) | 50 (0.942) | 50 (0.942) |
| T2 | 50 | 0 (0.000) | 50 (0.942) | 50 (0.942) | 0 (0.000) | 0 (0.000) | 50 (0.942) | 50 (0.942) |
| E1 | 100 | 0 (0.000) | 5 (0.020) | 9 (0.048) | 2 (0.004) | 0 (0.000) | 98 (0.938) | 99 (0.953) |
| Real | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |

### 3.4 Descriptive facts behind the counts (`totals.json`, `windows.csv`, the generator assets)

- Variance profiles V(k), k = 0..5, averaged over windows and sets (unscaled, decoder units²): W1 1.21 at every level
  (flat); W2 1.20, 1.24, 1.26, 1.40, 1.83, 2.46 (rising); W4 1.21 → 5.47; W3 1.19 → 1.43; T2 1.19 → 3.89; T1 1.21, 1.35,
  1.42, 1.57, 1.67, 1.66 and E1 1.20, 1.34, 1.41, 1.56, 1.66, 1.65 (the same law, the same profile; level 4 exceeds
  level 5 by 0.6 %); O5 1.27, 1.34, 1.38, 1.60, 1.65, 1.45 and the real data 1.27, 1.35, 1.39, 1.61, 1.67, 1.46 (a
  peak at level 4, 14 % above level 5). Per (set, window), V(k*)/max(V(0), V(5)): T1 median 1.007, p99 1.096, max
  1.15; E1 median 1.011, p99 1.12, max 1.19; W1 median 1.013, p99 1.09; O5 median 1.15, p99 1.37.
- Component separation of the fitted two-state generators (the 20 B3 assets): the high-branch mean m_H(k) T̃(w) at the
  template's peak primary window, in units of the generator's noise SD at that window, is median 1.18 (range
  0.84–1.75) at level 2, 1.25 (0.87–2.08) at level 3, 1.49 (1.08–2.67) at level 4; averaged over the 16 windows, median
  0.73, 0.83, 0.99. T2 halves the occupancy, so its separation doubles: median 2.36, 2.49, 2.98 at the peak window.
- Standardised two-component fits at level 3 (median over sets and windows): T1 |μ_hi − μ_lo| 1.37 SD, smaller weight
  0.47, ΔBIC −33.5; W2 1.23, 0.47, −35.9; O5 1.19, 0.46, −34.5; T2 1.49, 0.35, +150.7.
- Windows called per set (median): BIC > 10 unscaled W1 8, W3 9.5, W2/W4/O1–O4/T2 16, O5 13, T1 10; burst (0.10) O5 13,
  the real data 16, every other setting 0.
- Real data (B6): dip p ≥ 0.77 at the declared levels; ΔBIC > 10 at 13 of 16 windows unscaled, at none scaled (largest
  scaled ΔBIC −16.7); the burst at all 16 windows under both scalings (k* = 3 at 8 windows, 4 at 8).

## 4. What each test does on these sets, in plain words (no ranking)

- The dip test finds no departure from unimodality at the near-threshold levels on any set, graded or two-state, under
  either scaling and either window rule (the only calls at all: 11 of 100 O5 sets at a single window). The fitted
  two-state generators place the high-state component about one noise SD from the low one at the template's peak
  (0.8–2.7 SD across participants, less at other windows), and a two-Gaussian mixture that close is unimodal, so there
  is no dip to find; the real data read the same (p ≥ 0.77).
- The two-component mixture by BIC prefers two components on nearly every set of every setting when the raw pooled
  distances are tested — including 90 of 100 W1 sets, which carry no trial-to-trial variation at all. Standardising each
  participant by its own no-sound SD removes the W1 and W3 calls entirely (0 of 100 each): on those settings the raw
  call came from pooling twenty participants with different noise scales. The calls persist wherever the generator
  carries the lognormal scale term (W2 97, W4 100, O1–O4 96–100 of 100): a Gaussian multiplied by a lognormal is
  heavy-tailed at each level and BIC reads two components in it, with no two states in the generator. On the two-state
  generators as fitted the standardised reading is 0 of 50 (T1) and 5 of 100 (E1, the same law): their components are
  too close for a one-dimensional two-Gaussian fit to be preferred. At T2, where halving the occupancy doubles the
  separation, two components are preferred in 50 of 50 — the one two-state setting where the matched comparison had no
  verdict (50 of 50 UNAVAILABLE). On O5 the standardised count falls from 98 to 17. The real data: 13 of 16 windows
  raw, none standardised.
- The variance-burst signature is absent on every graded generator with or without trial variation (W1–W3, O1–O4 0 of
  100; W4 2 of 100): with no variation the profile is flat, and with scale variation it rises monotonically with the
  level, as the heteroscedastic graded account of v1 S9 says it can, with its maximum at the top level, not in the
  middle. It is also absent on the two-state generators as fitted (T1 0 of 50, E1 3 of 100): the A(1 − A) term raises
  the interior variance by at most about 10 % over the ends at these separations, which sits at the declared margin.
  It is present on every O5 set (100 of 100) and on the real data at all 16 windows: O5 resamples the recorded
  within-level distributions, which carry the 14 % peak at level 4 that neither fitted family reproduces. What produces
  that spread in the recordings — two states, a heteroscedastic graded response, or something else — is exactly what
  O5 cannot say (DESIGN §7.3; S2_REPORT 12), and this signature does not say it either.
- The inherited per-window rule (restated) calls 7 of 50 T1 sets, 39 of 100 O5 sets and 1 of 100 W1 sets, none
  elsewhere; the matched comparison (restated) reads two-state in 49 of 50 T1, 99 of 100 E1 and 12 of 100 O5 sets,
  none under W1–W4 and O1–O4, with 4 W4 sets and all 50 T2 sets UNAVAILABLE.

Each column answers its own question (a dip in a pooled marginal; two Gaussians in a pooled marginal; the shape of a
variance profile; the published per-window model pair; two complete predictive models with trial-level latency and
scale, scored out of sample per participant). The columns are not ranked, and nothing here says the published test is
false.

## 5. Caveats

1. Pooling across participants (B1, B2). The pooled marginal mixes 20 participants with different noise scales and
   response amplitudes; the scaled sensitivity separates the calls that are between-participant structure (W1, W3, T1;
   most of O5's) from those that survive standardising (the scale-term generators; T2). Neither pooled reading is the
   per-participant analysis the published study ran, and the amplitude differences between participants remain in the
   scaled pool.
2. The window rule. Bonferroni is over the three declared levels only; the ≥ 3-consecutive-window rule is the only
   control over the 16 windows and the any-window reading has none — visible in the burst (0.10) any-window counts of
   T1 (4 of 50) and E1 (28 of 100) under one generating law whose variance profiles agree to 0.01.
3. The burst margin. δ = 0.10 was declared on a sampling argument; at δ = 0 a flat profile (W1) reads a burst at three
   consecutive windows in 96 of 100 sets by chance, so the margin carries the rule. The fitted two-state generators'
   interior excess sits at that margin (per set-window ratio p99 1.10 on T1, 1.12 on E1), so their burst counts are
   sensitive to it in both directions.
4. T2's fits were UNAVAILABLE in all 50 sets (DESIGN §5 (d); S2_REPORT 12), so there is no matched-comparison verdict
   and no inherited run on T2; B1–B3 need no fit and are reported.
5. O5's generating family is unknown (DESIGN §7.3). Its counts are call rates under the resampling law, neither
   false-call rates nor evidence of two states.
6. The regenerated sets differ from the AWS record at the platform's rounding (`data_id` 0 of 1,000 rows equal, as
   S2_REPORT 11.1 documents); the tie rests on the member draws, the trial counts and the inherited pipeline
   reproducing all 50 T1 group readings (evidence differences median 0.10 nat, max 0.36 on one row). The matched
   comparison's verdicts cannot be refitted on the Mac (DESIGN §8; about 80 core-hours for T1 alone) and are restated.
7. The near-threshold levels were declared from the mean fitted occupancy; individual participants' occupancy at
   those levels spans 0.14–0.89, so "near threshold" is a population statement.
8. The dip test's p-value is the interpolated table of `diptest` (as on the model side); the GMM is one-dimensional with
   full covariance and five initialisations; BIC has no multiplicity control, so the > 10 and > 0 readings are both
   given.
9. B6 is one set of real data (n = 1), descriptive; its inherited and matched readings are the published reproduction
   (two-state preferred from 315 ms, `RESULTS_sergent.md`) and the S5 contrast (+0.00457 [−0.00025, +0.00939],
   UNRESOLVED, `results/s5/decision.json`).
10. Like the published per-window models, the dip and mixture tests see one window's marginal at a time; a trial's
    values at neighbouring windows are outside them (DESIGN §2). B3 averages within-participant variances, so it does
    not share the pooling caveat but shares the one-window one.

## 6. Compute and environment

Mac (Apple M4 Max, arm64), 12 joblib workers, the job's `.venv`: python 3.12.14, numpy 2.5.3, scipy 1.18.1,
pandas 3.0.5, joblib 1.6.0, scikit-learn 1.9.1, diptest 0.12.0 (jax 0.11.1 imported by the jitter modules; no fit run).
Tie stage 2,401 s wall (restatement of 1,100 sets at about 2 s each; T1 regeneration with the inherited pipeline
rerun, 50 sets, median 473 s per set under 12-way contention); battery 306 s wall for 1,101 sets (regeneration median
0.3 s, tests 3.0 s per set); two smokes about 6 min. About 51 min wall in all, about 9 core-hours; no cloud spend.

## 7. Files

`RULES.md` (declared first); `brain_side_alt_tests.py`; `describe.py` (the descriptive facts of 3.4, read from the outputs and the generator assets); `tie_check.json`, `tie_T1_sets.csv`, `saved_restated.csv` (B4
and B5 per set, with the member and trial-count tie fields); `sets.csv` (one row per set: every call under every reading
and its statistic; `seed_set`; the regenerated `data_ids`); `windows.csv` (one row per set, window and level: n, dip,
p, BIC(1), BIC(2), ΔBIC, the two-component fit, V, for both scalings); `summary.csv`, `table.md` (the three tables);
`totals.json` (profiles, k* histograms, medians); `runtime.json`. `.venv/` is ignored.

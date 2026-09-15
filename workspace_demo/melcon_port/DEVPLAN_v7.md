# Melcón battery — development plan for the revision after the failed v6 battery (v7, DRAFT, 15 Sept 2026)

**Status.** The owner gave the go on 15 Sept 2026. This plan is committed **before any new diagnostic fit** (Codex,
post-outcome record `t1_access/reviews/2026-09-15_melcon_v6_stage_c_codex_record.md`, RSC e490f3b, Q3 step 1). The v6
battery (namespace `results/battery/v6-ebaddf98807b/`: calibration, stage C, verdicts) is retained unchanged as the
failed development record: X1 strong recovered no two-state outcome in either drift condition, and no graded generator
was ever called graded. Everything learned from v6 is **development** evidence. The revised procedure is certified only
by a fresh, independent validation battery run after one candidate has been locked. Nothing here reads EEG, and nothing
is frozen.

## 1. What stays fixed (the comparison baseline)

The secondary analysis's estimand; the generator laws G1–G3, X1 and X2; the dose definition; the 34 templates; the
decoder, its halves and windows; the calibration statistic and the ten calibrated v6 amplitudes (unless §4 C3 changes
the decoder allocation); the group rule (three models, spm_BMS, a run of 3 adjacent windows at PXP ≥ 0.95, precedence
order); and the §9 pass criteria (G1–G3: at least 2 substantive and at most 1 two-state outcome per cell; X1 strong:
two-state in at least 2 of 3 replicates in each drift condition). The v6 unresolved-strength flags and the X2 amplitude
inversion stay reported.

**Not permitted:** rejecting every boundary fit; trimming losses or removing held-out trials; choosing a start by
held-out score; lowering the PXP or run thresholds; removing the null model; boosting X1's amplitude to obtain a pass;
running only the cells that failed.

## 2. Phase 1 — diagnostic panel (development; bounded; about 1 core-hour on the Mac)

- **Recordings.** Per cell (20), two recordings regenerated from their v6 manifests: the one with the largest graded
  held-out loss relative to null, and the one whose loss is closest to the cell median. 40 recordings, all 10 main
  windows, both halves, all four folds.
- **Per fold and model** (null, graded, two-state): every start's initial vector, final theta, training objective,
  convergence and projected gradient; the kept solution; which parameters sit within 1e-6 of a bound; the training
  scaling (m, s, S, ybar); the dose support (training and test log-contrast ranges, and counts of test present trials
  below and above the training range); the conditional predicted mean and SD at every training and test dose; and the
  per-trial held-out log-likelihood. Full precision, archived under `results/devpanel_v7/` (a development namespace).
- **Questions it answers:**
  1. How often severe held-out losses coincide with boundary solutions and with out-of-range test doses, for each
     family.
  2. Whether near-tie starts give materially different predictions.
  3. Whether the graded fit's conditional SD collapses at extrapolated doses.
- **Idealized density check.** Fit the three densities directly to the latent readout (z at matched signal-to-noise,
  with no decoder or sensor noise) for G1, G2, G3 and X1 on the same trial structures. This separates a density problem
  from decoder and noise effects, including G2's skew and G3's spread law.

## 3. Phase 2 — candidates (development; at most three considered, one locked)

Each candidate is applied to **both** families, with training-only definitions and a written scientific rationale. The
candidates are fixed here; no new one is added after Phase 1 without a recorded amendment to this plan.

- **C1 — prediction-stable densities.** A positive effective-SD floor in training units, applied to every component SD
  of both families, and a bound on each family's high-dose asymptote (graded a1; two-state e^d0 + e^d1) at a declared
  multiple of the training block's readout range. Numeric values come from the Phase 1 evidence and are declared before
  Phase 2's fresh-seed check.
- **C2 — no extrapolation in dose.** Each family's logistic dose terms are evaluated with x clamped to the training
  block's present-dose range. This is a model definition applied identically to training and test trials, not a trial
  removal; its rationale is that a block cannot identify the response beyond the doses it contains.
- **C3 — more density-training data.** A disjoint allocation: two decoder blocks, one density-training block and one
  test block, rotated. It changes the decoder, so it needs recalibration (§5).

Selection among the candidates uses Phase 1 and **one** fresh development check: X1 strong, G1 strong and G3 weak, both
drift conditions, one replicate each, 34 recordings per replicate, under new seed phase 8 (development only). Criteria:
the severe-loss rate, the X1-strong outcome, graded calls under G1–G3, and cost. The candidate that best restores
predictive stability without a two-state bias under the graded laws is locked. All candidates and their outcomes are
retained and reported.

## 4. Phase 3 — lock

Implement the locked candidate with tests: density and gradient checks, null-like special cases, finite predictions,
training-only scaling and selection, decoder/density/test disjointness, and v6 preservation. Write PREREG DRAFT v7 §6
and §9, and build a new identity and namespace (v7). Freeze the seed schedule, with a new validation phase that is
disjoint from v6's phases 1–7 and development phase 8. Codex reads the locked candidate and its tests before any
validation outcome is opened.

## 5. Phase 4 — independent validation

The whole battery on fresh seeds: 5 generators × 2 strengths × 2 drift conditions × 3 replicates × 34 templates
= 2,040 recordings (60 group replicates), all main windows, followed by the full-set summary.

- **Calibration lineage.** C1 or C2 keep the decoder, generator, statistic and templates, so the v6 amplitudes are
  reused with the parent hashes recorded in the manifest (not presented as recalibrated). C3 recalibrates with
  independent search, check and validation seeds before the battery.
- **Criteria.** The §9 criteria above are unchanged. The graded-call rate under G1–G3 is reported; making it a pass
  criterion would be declared at lock, before validation, and never afterwards.
- **Stopping.** A failed validation returns the procedure to development, and any further selection needs another
  untouched validation sample.

## 6. Cost (Mac; planning values)

| Phase | Planning value |
|---|---|
| Phase 1 | ~1 core-hour |
| Phase 2 fresh check | 6 replicates × 34 recordings × 3 candidates ≈ 612 recordings ≈ 2.7 worker-hours |
| Phase 4 | ≈ 9–11 worker-hours (v6: 8.95 worker elapsed-hours) |
| C3 recalibration | ≈ 8–13 core-hours |

Each phase is benchmarked before its main run. No cloud.

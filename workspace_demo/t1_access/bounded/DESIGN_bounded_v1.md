# Bounded-comparison qualification — design-freeze DRAFT v1

**Status: DRAFT, not frozen, not adopted.** Written 27 October 2026 for work item R052 from the method-repair record
`reviews/2026-10-27_method_repair_codex_record.md` (S1 the procedure, S3 the qualification plan, S5.13 the start
recipe) and the interval-diagnosis record `reviews/2026-10-27_interval_diagnosis_codex_record.md` (why). The owner
adopts or amends it; until then nothing here is a declaration that licenses spending, and no calibration or
validation point has been generated. Paths are relative to `workspace_demo/t1_access/`.

## 1. The question, and the target that changed

**The scientific question.** At one layer of the coherence readout, does a family of two-state (mixture) predictors
predict held-out concepts better than a family of graded predictors, in a way that survives the graded generators that
most resemble a mixture?

**What changed, in plain words.** The audited procedure asked for the *expected* held-out log-score advantage of the
training-selected mixture member over the training-selected graded member, and put a fixed-score concept bootstrap
interval around it. Six of twelve graded settings failed that interval's inclusion floor, and at the scale-varying
settings the expected score itself was unstable (one concept could move it by thousands of nats). The candidate here
answers a narrower question that can be calibrated:

* **No selection.** Each family's predictive density is the equal-weight average of its members' joint concept
  densities (G: M2B M2H M2S M2K; X: M3 M3H M3V M3L and the new **M3S**, a mixture whose concepts differ in scale).
* **Bounded per-concept contrast.** Each held-out concept contributes `d_c = (log q_X,c − log q_G,c)/n_c`, clipped to
  ±0.03 nat per trial. The clipped score is **not a proper scoring rule**; the unclipped mean is kept as a descriptive
  field only.
* **A median target.** The target is the (lower) median of the study statistic `T` across repetitions of this exact
  study design and algorithm — *in a typical repetition of this study, is the concept-balanced bounded predictive
  contrast positive?* It is not an expected log score, not a KL divergence, not the median concept.
* **Simulation-calibrated interval.** The interval half-widths and a separate graded critical value come from
  complete-pipeline simulation of a frozen generator catalogue. Fitting variability enters through the distribution of
  `T` across simulated studies; there is no bootstrap inside an observed-data interval.

A positive result would be *bounded predictive preference relative to a declared graded challenge set at one layer
and one readout*. It establishes no state ontology, no access, and nothing outside the catalogue (§10).

## 2. The procedure (code, by path and hash)

The procedure is implemented in `bounded/` and imports the audited `models.py`, `analyze.py` and `simulate.py`
without editing them (their bytes define the configuration hash of every published row; `test_bounded.py` checks they
are unchanged). M3S is registered into `models.MEMBERS` in memory at import of `bounded/members.py`.

| file | role |
|---|---|
| `bounded/members.py` | M3S (concept random log-scale on both component scales, catch occupancy zero, integrated jointly over a concept's trials by the existing two-scale trapezoid rule); its moments start (M3H's, last coordinate log 0.3); the start recipe: 8 cold starts for every member, M2S also 64 keyed narrow starts at jitter 0.25 (`models.added_start_stream`); the existing recovery rule |
| `bounded/procedure.py` | the S1 point pipeline: layer 41; three concept-disjoint stratified outer folds; no inner selection; every member fitted per outer training set; equal-weight joint-density ensembles; `d_c`, `z_c = clip(d_c, ±0.03)`, `T = Σ_h W_h mean_{c∈h} z_c` with `W_h = 27/64, 22/64, 15/64`; the unbounded mean as a descriptive field; any non-finite fit or score ⇒ UNAVAILABLE |
| `bounded/calibrate.py` | median brackets, tolerance limits, `A`, `B`, `c_G`, the decision rule and the S3 pass counts, in exact rational binomial arithmetic |
| `bounded/generators.py`, `bounded/catalogue.json` | the 30-setting catalogue, its datasets and the seed rule |
| `bounded/run_point.py` | CLI: one (setting, replicate, namespace) → one JSON row with the configuration hash |
| `bounded/test_bounded.py` | the tests (§11) |

**Configuration hash.** `run_point.config_hash()` is SHA-256 (12 hex) over the as-loaded bytes of
`bounded/{__init__,members,procedure,calibrate,generators,run_point}.py` and `bounded/catalogue.json`, the
loaded-source digests of `models.py`, `analyze.py`, `simulate.py`, and the start-recipe table. The value for the
code committed at RSC `049c3258` is **`890f65ccba39`**, recorded in every row and in `bounded/dev/smoke.json`. File
SHA-256 prefixes at that commit: `__init__.py` 4fd67e03a0e1d0fd, `members.py` 2e7e349cb18fda42, `procedure.py`
6dc79c92dc6a7e33, `calibrate.py` b7ba547e64e4be07, `generators.py` 4ba1bc5ac9065926, `run_point.py` f5037bbaf3bebb78,
`catalogue.json` 2ad1ca3252e5f254. Any edit to any of these files changes the hash; rows of two hashes are never pooled.
Freezing for qualification means re-running this hash on the adopted files (λ and the certified gain scales enter
`catalogue.json`, so the frozen hash will differ from the development one).

**Prototype continuity.** On the two selected development examples of the method-repair record (seeds 271004 and
271005) the production pipeline reproduces the prototype fit by fit: bounded contrast −0.01935586 and +0.01807624
(§11).

## 3. Role map — PROPOSED

Three families, animals / foods / vehicles. **PROPOSED** allocation within the eligible pools 39/32/23 reported before
naming acceptance (PREREGISTRATION §15, 13 October 2026):

| role | animals | foods | vehicles | total |
|---|---|---|---|---|
| CONF | 27 | 22 | 15 | 64 |
| CAL | 5 | 4 | 3 | 12 |
| PILOT | 5 | 4 | 3 | 12 |
| BACKGROUND | 1 | 1 | 1 | 3 |
| total | 38 | 31 | 22 | 91 |
| eligible pool | 39 | 32 | 23 | 94 |

This is a prospective allocation, not an accepted bank or role manifest. **If naming acceptance changes the CONF
counts, the strata weights `W_h` change, the catalogue's design profile changes, and the calibration must be
regenerated under the realised map** (the code refuses a family profile other than the declared one). The statistic's
weights are the CONF counts over 64, fixed in advance, never estimated from data.

## 4. The catalogue (`bounded/catalogue.json`)

Design profile for every setting: 64 concepts in three strata 27/22/15, D = 4, six carriers, seven levels
(0, 1, 2, 3, 4, 6, 8), 168 trials per concept, one layer (41).

| id | kind | generator | parameters | note |
|---|---|---|---|---|
| G01 | graded | M2B (simulate.py) | base | historical |
| G02–G05 | graded | M2H | τ = 0, 0.5, 1, 2 | historical |
| G06–G09 | graded | M2S | ω = 0, 0.5, 1, 2 | historical |
| G10–G12 | graded | M2K | α = 0, 1, 3 | historical |
| G13 | graded | low-amplitude M2B | μ(0) = −0.1, μ(8) = +0.1 (tenfold smaller range) | new; declared value |
| G14 | graded | boundary | μ(k) of M2B; log σ(k) = log 0.75 + λ sin²(πk/8) | new; **λ not frozen** (§8); the smoke run used the placeholder 0.5 |
| G15 | graded | t5 graded | M2H mean, τ = 0.5; t(5) innovations at unit variance × \|aμ + b\| | new |
| G16 | graded | nonlinear variance | μ(k) of M2B; σ(k) = 0.6 + 0.4 exp(−(k−3)²/2); concept log-scale SD 1; carrier effect SD 0.2 shared across concepts; background effect SD 0.2 per (concept, carrier, draw), shared across that draw's nested levels and weighted (8 − k)/8 | new; the 0.2 SDs are declared development stress values |
| A01–A03 | alternative | M3 | gains 0.003 / 0.01 / 0.03 | scale = starting value |
| A04–A06 | alternative | M3H, τ = 0.5 | gains 0.003 / 0.01 / 0.03 | scale = starting value |
| A07–A09 | alternative | M3V | gains 0.003 / 0.01 / 0.03 | scale = starting value |
| A10–A12 | alternative | M3L, π₀ = 0.05 | gains 0.003 / 0.01 / 0.03 | scale = starting value |
| A13 | alternative | M3S, ω = 1 | middle gain | scale starting value = M3H's 0.01-nat constant |
| A14 | alternative | M3S, ω = 2 | middle gain | as A13 |

The six **power gates** are A02, A05, A08, A11, A13, A14. The scale constants of A01–A12 come from
`sim_results/gain_sens600/gain_calibration_D4.json` (hash recorded in the catalogue) and are **starting values only**:
S3 requires all fourteen generating-density gains to be re-certified against the graded reference under the frozen
implementation before qualification; a failed certification stops that setting's power qualification.

**Seeds.** Namespaces development 271100, calibration 271200, validation 271300. Dataset seed =
`default_rng([namespace, H("setting:<id>"), H("replicate:<r>")]).integers(2³¹)` with H the first 32 bits of SHA-256 —
the setting and replicate tags hashed separately. The fold and fit streams are keyed by the dataset seed. Existing
development rows and the local seeds 271001–271005 and 271010–271312 are excluded from qualification.

## 5. Calibration

500 complete point pipelines per setting, all thirty settings: **15,000 points**. From each bank: the exact
order-statistic median bracket (ranks **208 and 293** of 500 at error 0.005/30 per setting) and the 0.98 tolerance limits
per tail (error 0.005/60 per tail per setting — at n = 500 these are the **sample minimum and maximum**). Then
`A = max_g(u_g − m_g⁻, 0)`, `B = max_g(m_g⁺ − l_g, 0)`, `I(T) = [max(−0.03, T − A), min(0.03, T + B)]`, and
`c_G = max(0, max over the sixteen graded settings of u_g)`.

On the calibration event (probability ≥ 0.99) every setting has inclusion ≥ 0.96, so unconditional inclusion ≥ 0.9504;
every graded setting has a mixture-preference probability ≤ 0.02 on the event and ≤ 0.0298 unconditionally. These are
order-statistic and union-bound results for independent, finite complete-pipeline statistics under an unchanged
catalogue and algorithm (`bounded/calibrate.py` docstring). **An unavailable calibration attempt holds artifact
construction**: it is logged, never filtered or replaced until 500 successes remain; a numerical repair is a new frozen
algorithm with a new calibration.

**Decision rule.** Mixture preference iff the lower endpoint is > 0 **and** `T > c_G`. Negative bounded contrast iff the
upper endpoint is < 0 (not proof that the generator is graded). Otherwise inconclusive. A failed fit or unavailable score
is **unavailable**, never a scientific decision.

## 6. Validation and pass thresholds

Independent validation on the validation namespace, frozen calibration first: **400 attempted datasets per graded
setting (6,400) and 1,000 per alternative (14,000)**. Total plan 35,400 complete point pipelines.

Pass thresholds — one-sided exact binomial bounds with a familywise 0.04 split across **52 statements**
(30 inclusion + 16 graded safety + 6 power), α = 0.04/52 each (the remaining 0.01 is the calibration event, joint
confidence ≥ 0.95 by the union bound); computed exactly by `calibrate.validation_thresholds()`:

| statement | floor / ceiling | operational count |
|---|---|---|
| inclusion, each graded setting | ≥ 0.90 | **≥ 379 / 400** |
| inclusion, each alternative | ≥ 0.90 | **≥ 930 / 1,000** |
| positive call **or unavailable**, each graded setting | ≤ 0.064 | **≤ 11 / 400** |
| detection at each of the six power gates | ≥ 0.80 | **≥ 840 / 1,000** |

Inclusion counts only intervals that contain the **entire** calibration median bracket of that setting
(`calibrate.includes_bracket`). Unavailability is an inclusion and power failure and counts against graded safety. The
calibration and validation confidence events are reported separately even when their joint bound is quoted.

## 7. Stopping rules

* **No early success.** Every setting runs to its declared count before it can pass.
* **Stop when unattainable.** A setting (and the campaign, if it is a required setting) stops when its threshold can no
  longer be met even if every remaining attempt succeeds.
* **Stop on a defect.** A code or identity defect stops everything immediately.
* **Order.** The hardest graded settings (M2S ω = 2 and ω = 1, the boundary, M2H τ = 0.5 and τ = 2) and both M3S
  alternatives run first, so that an unattainable result is found before the easy settings are bought.
* **No tuning on validation.** Any method change is a new frozen artifact and fresh validation seeds.

## 8. Development reserve (6,000 core-hours) and the boundary search

| slice | cap (core-h) |
|---|---|
| loaded-host benchmark and code / fitter checks | 1,000 |
| boundary search and certification | 2,700 |
| gain re-certification (all fourteen) | 2,000 |
| contingency | 300 |
| **total** | **6,000** |

**Boundary search protocol (S3).** On development seeds, search λ at 0, 0.25, 0.5, 0.75 and 1 (expanding to 2 and 4
only if necessary), eight datasets per search point. After bracketing a sign change of the median contrast, at most
eight bisection steps with twenty datasets each. Then a separate 1,000-dataset development reference slice at the
candidate λ: the exact median bracket (error 0.01) must contain zero and lie inside [−0.001, +0.001], and the
bounded-mean bracket (the empirical-Bernstein reference of `scratch:repair_procedure.py`, error 0.01) must lie inside
[−0.003, +0.003]. λ is frozen only after this certification; calibration and validation use new seeds and cannot
retune it. A failed bracket search is not a tested boundary, and **no qualification starts without the boundary
setting**. Maximum 1,216 datasets ≈ 2,675 core-hours at the admission ceiling. If a reserve slice cannot finish its
prerequisite, stop before qualification and redesign within a newly priced plan.

## 9. Admission and cost gate

**Ceiling: 2.2 Lengau core-hours per complete point** (campaign average, counting failed work and allocated idle
cores). The base plan is 35,400 × 2.2 = 77,880 core-hours; with a 20 % retry / slow-setting allowance and the 6,000
reserve, **99,456 core-hours** against the 107,600 available (7,600 + 100,000). The loaded-host benchmark is bought
first, under the reserve, across ordinary, scale and boundary settings at the intended concurrency, for **this**
three-fold outer-only algorithm with its frozen start recipe. The campaign is admitted only if a conservative measured
envelope fits the ceiling. If it fails, the smallest honest reduction is a separately declared two-fold design with all
calibration regenerated; validation counts are never reduced and old calibration is never reused to make the bill fit.

**Mac cost basis (smoke run).** One replicate of each setting in the development namespace, one process per point,
NPROC = 1, on the Mac: per-setting CPU in `bounded/dev/smoke.json`; summary in §12. The planning conversion is
row 18's: a Lengau core takes about 4.7× the Mac time, and packing costs a further 1.3–1.5×. A Mac number is not a
Lengau rate; the benchmark decides admission.

## 10. What a pass licenses, and what it does not

A pass licenses reporting, for the one-layer coherence readout at this design, a **bounded predictive preference**
(or a negative bounded contrast, or inconclusive) for the mixture ensemble over the graded ensemble, with the stated
inclusion and graded-safety guarantees **within the frozen catalogue**. It does not license: a statement about the
expected log score or any KL divergence; a proper-score gain; generalisation to generators, nuisance ranges, layers,
readouts or packet constructions outside the catalogue; a workspace-band, H2 or target-readout claim; an access or
causal-state interpretation (that needs the target bridge, readout recovery and causal tests of the appendix); or
identification of a two-state mechanism from a positive contrast. A negative bounded contrast does not prove a graded
mechanism. More settings, wider ranges, another readout, another layer rule or another packet construction each need
their own declared qualification.

## 11. Verification of the code (27 October 2026)

`bounded/test_bounded.py` (unittest; quick tier and a slow tier with `BOUNDED_SLOW=1`). Results are in the commit
message of the code commit and in §12; the material numbers:

* M3S joint likelihood against an independent dense numpy integration (16,385 points over ±8ω, converged to 1e-13 at
  65,537): max error 6.6e-7 nat per concept at ω = 1 generating parameters and ≤ 7.7e-7 at fitted parameters (M3S
  fitted to M3S and to graded M2S data, held-out and training concepts). **At ω = 2 generating parameters the
  error is 1.5e-6 nat per concept, above the 1e-6 target** (9e-9 per trial; it halves with each doubling of the
  trapezoid points — 7.0e-7 at 192, 2.9e-7 at 384 — so it is the resolution of the frozen `models.TRAP_POINTS = 96`
  rule, which this package does not change). The §7.4 audit's pass rule is 1e-3 nat per concept.
* Calibrate: known ranks (n = 10 → x₍₂₎, x₍₉₎; n = 59, p = 0.95 → the maximum; the design's 208/293 and 500), the
  artifact on constructed banks, every decision branch, unavailable banks held, and the S3 counts 379 / 930 / 840 / 11.
* Unavailable handling at assembly, pipeline (an injected non-finite fit) and decision level.
* Determinism: the same (setting, replicate, namespace) gives byte-identical rows outside the timing fields
  (`timing`, per-fit `cpu_seconds` / `wall_seconds`). G03 replicate 0 gave the deterministic digest
  `c19050d100f51712` twice inside the test and a third time in the smoke run's separate, concurrently loaded process.
* Prototype continuity (slow tier): seeds 271004 and 271005 give T = −0.0193558609 and +0.0180762365, equal to the
  prototype record with zero difference in every fit's log-likelihood, parameters and held-out scores.
* Existing checks: `verify.py` ALL OK and the existing suites (`test_start_policy`, `test_interval_path`,
  `test_loaded_provenance`, `test_gain_gate`, `test_gain_gate_integration`, `test_gain_artefact`,
  `test_calibrate_gain`, `test_points_filter`, `test_refit_bootstrap`, `test_h3`, `test_pipeline_synthetic`) pass
  before and after the package was added.

## 12. Smoke run (Mac cost basis)

One replicate (r = 0) of every setting in the development namespace, one `python -m bounded.run_point` process per
point (CPU includes import and JIT compilation), NPROC = 1, three concurrent single-thread workers on the Apple M4 Max,
27 October 2026 09:27–10:50 PDT, configuration hash `890f65ccba39`. Budget 6 h; used **4.21 h** (15,151 s). All 30
points available; 810 of 810 retained fits converged; no recovery chain was needed. G14 ran at the **placeholder**
λ = 0.5. Single development points: a cost basis and a mechanics check, not calibration, error rates or power.

| setting | kind | T (bounded) | U (unbounded) | process CPU s | fit CPU s | M2S fit CPU s | M3S fit CPU s | fits conv. | status |
|---|---|---|---|---|---|---|---|---|---|
| A13 | alternative | +0.01253 | +0.0753 | 500 | 499 | 150 | 95 | 27/27 | done |
| A14 | alternative | +0.01225 | +0.4871 | 809 | 809 | 226 | 252 | 27/27 | done |
| G14 | graded | +0.00217 | +0.0023 | 441 | 441 | 175 | 94 | 27/27 | done |
| G09 | graded | -0.02704 | -0.1988 | 610 | 609 | 234 | 93 | 27/27 | done |
| G08 | graded | -0.02683 | -0.0709 | 618 | 618 | 177 | 213 | 27/27 | done |
| G05 | graded | -0.02606 | -0.0564 | 470 | 470 | 125 | 132 | 27/27 | done |
| G03 | graded | -0.02007 | -0.0262 | 477 | 476 | 168 | 114 | 27/27 | done |
| G07 | graded | -0.02162 | -0.0381 | 517 | 517 | 141 | 208 | 27/27 | done |
| G11 | graded | -0.02136 | -0.0258 | 482 | 482 | 241 | 83 | 27/27 | done |
| G16 | graded | -0.00221 | -0.0073 | 503 | 503 | 135 | 115 | 27/27 | done |
| G15 | graded | -0.01844 | -0.0252 | 436 | 435 | 137 | 111 | 27/27 | done |
| G13 | graded | +0.00005 | +0.0001 | 677 | 676 | 254 | 126 | 27/27 | done |
| A05 | alternative | +0.00648 | +0.0065 | 459 | 459 | 152 | 116 | 27/27 | done |
| A08 | alternative | +0.00610 | +0.0061 | 417 | 417 | 153 | 93 | 27/27 | done |
| A02 | alternative | +0.01408 | +0.0147 | 426 | 426 | 155 | 98 | 27/27 | done |
| A11 | alternative | +0.01661 | +0.0174 | 503 | 503 | 204 | 105 | 27/27 | done |
| A04 | alternative | +0.00103 | +0.0010 | 562 | 562 | 203 | 123 | 27/27 | done |
| A07 | alternative | -0.00030 | -0.0003 | 551 | 550 | 228 | 112 | 27/27 | done |
| A01 | alternative | +0.00513 | +0.0051 | 516 | 515 | 197 | 115 | 27/27 | done |
| A10 | alternative | +0.00738 | +0.0074 | 507 | 506 | 199 | 119 | 27/27 | done |
| A06 | alternative | +0.01867 | +0.0208 | 419 | 418 | 135 | 107 | 27/27 | done |
| A09 | alternative | +0.02288 | +0.0330 | 549 | 549 | 143 | 156 | 27/27 | done |
| A03 | alternative | +0.02683 | +0.0410 | 441 | 440 | 183 | 96 | 27/27 | done |
| A12 | alternative | +0.02471 | +0.0398 | 470 | 470 | 200 | 110 | 27/27 | done |
| G01 | graded | -0.01799 | -0.0197 | 459 | 459 | 180 | 105 | 27/27 | done |
| G02 | graded | -0.01881 | -0.0212 | 476 | 475 | 200 | 104 | 27/27 | done |
| G04 | graded | -0.02276 | -0.0289 | 447 | 447 | 134 | 110 | 27/27 | done |
| G06 | graded | -0.01797 | -0.0196 | 500 | 500 | 218 | 100 | 27/27 | done |
| G10 | graded | -0.01741 | -0.0186 | 475 | 474 | 197 | 102 | 27/27 | done |
| G12 | graded | -0.02876 | -0.0680 | 435 | 434 | 212 | 72 | 27/27 | done |

**Per point: mean 505 s, median 479 s, range 417–809 s (A14, M3S ω = 2).** M2S's 72-start fits are about a third of the
point. As planning arithmetic only (row 18's factors, not a measurement): 505 s × 4.7 ≈ 0.66 Lengau core-hours,
× 1.3–1.5 packing ≈ 0.86–0.99, and the slowest point 809 s → ≈ 1.06–1.22; all under the 2.2 ceiling. The admission
decision still waits for the loaded-host benchmark (§9).

Readings to carry into development, not conclusions: the graded boundary point at λ = 0.5 gave **T = +0.0022** and the
low-amplitude M2B point +0.00005 — graded generators with a non-negative bounded contrast, which is what the boundary
challenge exists to supply and why `c_G` is needed; the weakest M3V alternative (A07, 0.003 nat) gave −0.0003 and M3H at
0.003 nat +0.0010, the sensitivity cost S2 already reported.

## 13. Deviations from the method-repair record and open choices

Deviations from, and interpretations of, S1/S3 made in this implementation — each for the owner to accept or change:

1. **Quadrature target at ω = 2.** The M3S integral misses the brief's 1e-6 nat-per-concept target at ω = 2 generating
   parameters (1.5e-6). Meeting it needs a larger `models.TRAP_POINTS`, i.e. an edit to the audited numerical setting,
   which is out of scope; the §7.4 audit rule (1e-3) is met by three orders of magnitude.
2. **"Failed fit" = no finite solution.** UNAVAILABLE is triggered by a non-finite fit, held-out score or `d_c`. A
   retained fit whose kept solution is flagged non-converged after the recovery chain is recorded, not made
   unavailable — the existing §9 rule (`analyze.layer_pipeline`). S1 says "a failed fit … is unavailable" without
   defining failure; if the owner wants non-convergence to count, it is a one-line change before freezing.
3. **Determinism** is byte identity of the row outside the timing fields (CPU and wall clock cannot repeat);
   `deterministic_sha256` carries it.
4. **"Made exact"** is read as exact rational arithmetic for every binomial comparison (median ranks, tolerance ranks,
   S3 pass counts); the order statistics are the floating-point statistics themselves. The prototype's docstring line
   about critical values "at .95" was stale and is not carried (S1's 0.98 limit is reused, no extra budget).
5. **M3S generator stream.** The prototype built its M3S dataset by overwriting an M3H draw with a second stream on the
   same seed; the catalogue's M3S generator draws the concept scales, occupancy and noise from one stream. Same
   distribution, different numbers; the prototype construction is kept in the tests for the continuity check.
6. **M3S alternative scale.** S3 asks for M3S at "the middle gain"; no certified M3S scale exists, so the starting
   value is M3H's 0.01-nat constant (0.5359). The prototype's development example used scale 1.
7. **Declared values S3 leaves open:** low-amplitude M2B at a tenfold smaller range; the nonlinear-variance shape
   σ(k) = 0.6 + 0.4 exp(−(k−3)²/2); carrier and background SDs 0.2, the background effect weighted by the share of
   background slots (8 − k)/8. None comes from CAL; all are development stress values.
8. **Boundary λ** is held as `null` in the catalogue; `run_point` refuses G14 without a development `--lam` and refuses
   `--lam` outside the development namespace.
9. **Configuration hash scope** excludes `test_bounded.py` and `dev/` (they never run inside a point); it includes the
   start-recipe table.
10. **Smoke concurrency.** Three single-thread workers ran at once; the method-repair benchmark used one. Per-point
    CPU under that light load is the basis reported; it is not a Lengau rate.

Open choices for the owner: adopt or amend items 2, 6 and 7; whether the ω = 2 quadrature level is acceptable or
`TRAP_POINTS` should rise in a new snapshot (a new identity for everything); the role map once naming acceptance
lands; the boundary search's launch under the development reserve.

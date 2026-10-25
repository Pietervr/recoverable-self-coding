# S2 report — development on development seeds (DESIGN_jitter.md rev 6 §0 stage S2)

Session R052 Entropy SI, 24 October 2026. DRAFT: the readings under the final (D4-patched) fitter are PENDING while
the chain runs (W2 sets 0-9 first, then T1, O1, then sets 10-24 of each, the summary and the benchmark re-cost).
Everything here is a development reading on development seeds — nothing feeds a gate or flag (§0: only S4b batches do).
What this report declares for DESIGN rev 7 and the Codex S3 freeze review: four defects found in S2 (D1-D4), their
evidence, the repairs, and what the repaired fitter reads on the three development settings.

Code: `jitter/{data,models,fit,decide,simulate,bench,s2,diagnose}.py`, tests `jitter/tests/` (81 tests over four files: 18 fit, 24 models, 29 decide, 10 simulate;
`../../t1_access/.venv/bin/python tests/<file>.py` -> "ALL OK"). Records: `results/s2/decision_rev6/` (the rev 6
fitter), `results/s2/decision_pre_d4/` (R1-R4 repaired, before D4), `results/s2/decision/` (final), `results/s2/diagnosis/`.

## 1. The trigger: W2 under the rev 6 fitter

W2 = the graded G3 generators (§7.3), where a POSITIVE set is a FALSE two-state call (gate (b) ceiling 1 in 100). Under
the rev 6 fitter (shared Ledoit-Wolf training-catch Σ, four §5 starts, 7-node then adaptive 17-node scale quadrature,
κ ≤ 50) W2 sets 0-18 read **6 POSITIVE, 13 UNRESOLVED, 0 NEGATIVE**; Δ₃ per participant +0.0043 (sd 0.0130) nat/trial,
set means [−0.0004, +0.0121]; B3 beat G3 out of sample on about 16 of 20 participants per set
(`results/s2/decision_rev6/summary.md`). A design that reads this way cannot pass gate (b), so S2 stopped and diagnosed.

## 2. Diagnosis (W2 set 1, archived POSITIVE +0.0058, 16/20)

### D1 — the shared Σ (the cause of the false calls)
Oracle test (`diagnose.py oracle`, `results/s2/diagnosis/W2_set1_oracle.md`): every test fold scored under the
generator's TRUE density. The true density beats fitted B3 on 20/20 participants by 0.88 nat/trial; the true MEAN
structure scored through the fold's own whitening is only +0.002 above fitted G3; the 31-node τ grid costs 0.0001. So
0.88 of the 0.88 nat/trial gap to truth is the estimated whitening: the Ledoit-Wolf Σ from ~115 training catch trials in
16 dimensions compresses the variance along the template direction by 13% (ratio t'Σ_gen t / t'Σ̂ t = 1.13; shrinkage
0.04-0.15), and B3's occupancy law A(k), falling toward low levels, absorbs a level-independent template-direction
variance excess better than G3's lognormal scale law a(k)²(r−1) does — the per-level contrast sits at the LOW levels
([+0.017, +0.015, +0.009, −0.001, −0.005] at levels 1-5). Refit of set 1 with the ORACLE Σ: NEGATIVE −0.0069
[−0.0133, −0.0005], B3 collapses to A = 1 on 12/20, G3's s_τ returns to truth (m1 66.5 vs 67.3 ms). Expected whitening
loss by simulation (`kl_sigma_simulation.py`): LW 0.91 nat/trial (observed 0.88), sample 0.83, sample × n/(n−p−2)
0.71. §6's primary sign is the raw Δ₃ interval and §7.4's ε calibrates the upper bound only: nothing absorbs a null
offset, so this is a DESIGN DEFECT in the §4 Σ construction, not a sizing matter; the §4 sentence "Σ has no
model-independent direction of bias" is false under shrinkage.

### D2 — the four §5 starts miss optima
Archived training nesting l(B3+) ≥ l(G3+) was violated on 7 folds by 6-22 nat (m1, m11, m14, m18): four starts do not
reliably find either family's optimum on S2/S4/S16/S18-based data. A template fitted to the jitter-BROADENED level-5
mean slides to s_τ = 0; template starts fitted through the basis SMEARED by the start's own latency kernel reach +61
nat (m1 f0), +54 (m1 f4), +20 (m18 f1) and lift B3+ by 50-58 nat; s_g = 0.4 starts beat s_g = 0 starts by 60-80 nat
throughout; on m3 f2 the design start τ40/s_g0.4 stays best, so the recipe is a UNION, not a replacement.

### D3 — runaway coordinates, −∞ lifts, a lossy acceptance rule
Free positive-spread fits let template coordinates run off along flat directions (archived set 1: median per-fit
minimum γ −75, 43 of 194 fits below −700, worst −1.9e6); softplus underflows to c = 0 and `lift_warm_start` packed −∞,
so every profile warm start was NONFINITE at iteration 0 (m1 f0 oracle: warm objective −12742.4 discarded, T_B's
−12794.9 kept = the 50-nat profile deficit). The benchmark's profile timings, c₀ pair and profile intervals were
effectively one-start. `run_start` also let a worse CONVERGED retry replace a better stationary end point, and the EARLY
pairing killed exact warm starts (the collapse start).

### D4 — G under-found through the EM early stop (found under the R1-R4 repair)
In the first repaired W2 block (sets 0-8, §4 below) every UNRESOLVED set carried one or two participants at +0.005 to
+0.021 nat/trial whose excess sat in ONE fold where the G twin was under-found. `_em_loop` broke at the first inner
solve that ended NOT_CONVERGED (over 900 folds: G3+ 6×, G2 4×, B3+ 1×), leaving G at its starting-Σ optimum while B's
chains carried on; `reseed_g` refused to rescue G unless every fitted B occupancy was ≥ 0.99 — exactly what never holds
when B has found a basin G missed. Evidence (`results/s2/decision_pre_d4/W2/set_{5,7}.json`): set 7 m12 (S13) fold 0,
G3+ "em stopped at step 1" at −13704.7, BELOW G2 −13453.5 (G3 REDUCED), B3+ −13316.8 — training gap 387.9 nat,
held-out B3 − G3 +18.6 nat on that fold and within 0.8 on the other four; set 5 m4 (S17) fold 0, G3+ stopped at step 6
at −11722.6, B3+ −11675.0 (gap 47.7, held-out +19.5). Training gap B3+ − G3+ over the 900 folds: median 0.10 nat, p90
2.1, p99 7.7; 19 folds > 5 nat, 193 > 1 nat; G3 REDUCED while B3 POSITIVE 3×.

### D5 — generator fits under the free 53 × 53 Σ degenerate (found 24 Oct 16:43Z, in the pulled-forward benchmark)
`bench.py` refits its subject's §7.1 generators before timing anything, and under R1 that refit ran the EM Σ in 53
dimensions: the S10 G3 generator came back at s_τ 24.7 ms, s_g 0.00 (Ledoit–Wolf: 82.2 ms, 0.56) with B3 collapsed
onto G3 — with ~900 trials a free 53 × 53 covariance absorbs the latency and scale variability the generators exist to
carry (the extreme of the strength-dependent collapse of §5). The benchmark also WROTE those fits over
`results/generators/S10_active_{G3,B3,B0}.npz`, the files every S2/S4 batch draws from, 16:43Z — caught at 16:49Z
before the chain's second leg started; restored from git (the stored generators are the S1 Ledoit–Wolf fits; the W2
block, sets 0-9, had finished at 16:35Z on the correct files). A second part of the same finding: R1 made the SCALED
sample covariance the default whitening (the EM start), so even without EM a generator fit would have used a 53 × 53
sample covariance from ~150 catch trials; the stored S1 generators carry the Ledoit–Wolf Σ exactly (S10: max
difference 0, shrinkage 0.059, 152 catch trials), as §7.1 says. Repairs: `generator_fits` whitens with
`method="lw"` explicitly, defaults to `FitCache(em=False)` and REFUSES an EM cache; `bench.py` and `generators.py` pass
em=False; the benchmark no longer overwrites stored generators without `--write-generators`; the test asserts no EM
step, Σ equal to the Ledoit–Wolf estimate and not to the scaled one, and the refusal. DESIGN rev 7 §7.1 says it. The
benchmark was rerun from scratch after the fix (§9).

## 3. The repairs (all declared for rev 7 and the Codex S3 review)

R1 Σ by maximum likelihood INSIDE each model — a generalised EM outer loop around the L-BFGS-B solve
   (`fit.em_fit`, `models.m_step_sigma`): M-step Σ = (1/n) Σᵢ E_post[(yᵢ − μ0 − g m T̃_τ)(·)ᵀ] from the per-(trial, τ
   node) responsibilities and E[g], E[g²] on the adaptive quadrature nodes (two-state: the low branch contributes
   rᵢrᵢᵀ); μ0 stays the training-catch anchor; EM start Σ = the scaled sample catch covariance S × n/(n−p−2) (the
   KL-optimal scalar multiple; "lw" kept for the record); strictly monotone, ≤ 8 steps, tol 1e-6 relative; the
   FitResult carries its Σ and held-out trials are scored under the MODEL's own Σ (`score_heldout`). Each candidate
   (G2, G3+, B2, B3+) runs its own EM and the zero-boundary selection compares final log-likelihoods. Warm EM CHAINS:
   every B candidate also runs a chain from its G twin's own (θ collapsed to A → 1, Σ), so l(B) ≥ l(G) holds by
   construction in the joint (θ, Σ) space; a B materially above G (> 0.05 nat) re-seeds G and B re-chains.
   RSC 563515a, 68a9ffe, 52e037b.
R2 Starts: the union recipe — design 4 + smeared-kernel 4 (spreads 20/40/80/120 ms, T_A/T_B alternating, s_g 0.4) +
   the reduced fit lifted at 20/40/80 ms (3) + for B the selected G collapsed (κ = 50, x0 = −5). S2 reports which
   families were material (§7 below). RSC 563515a.
R3 Box γ ≥ −30 on every template coordinate (c ≥ 1e-13; `models.GAMMA_MIN`); the lift clips to the box and refuses a
   non-finite start; acceptance in `run_start`: the result is the best end point among attempts satisfying (i) gradient
   and (iii) finiteness, CONVERGED if it also satisfies (ii) or, when reached in < 5 iterations, nothing found a better
   objective; a worse retry never replaces it. RSC 563515a, ea9f75a.
R4 Tests: acceptance rule, lift clipping, `posterior_moments` against a dense reference, EM monotonicity, nesting with
   and without EM (`tests/test_fit.py`, `tests/test_models.py`).
D4 (a) `_em_loop`: an inner solve whose best finite end point raises the total log-likelihood is accepted as a
   generalised-EM ascent step (the Σ M-step is exact; the θ-step need only not decrease the objective), noted, and the
   chain continues; one that does not improve is retried once from the chain point with 4× the iteration budget before
   the chain stops; every attempt is archived. (b) `reseed_g` fires for EVERY B above G + 0.05 nat, collapsed or not
   (on two-state data one extra chain that changes nothing). Regression test on the archived set 7 m12 fold 0
   (`test_d4_em_chain_ascends_and_g_is_reseeded_from_any_better_b`): G3+ now −13320.4 at s_τ 52 ms (its EM step 1 IS
   the accepted ascent step, +377 nat; the re-seed chain from B3+'s basin ends at the same value), G2 −13451.2, B3+
   −13316.8 with occupancy 0.28-0.96 (a genuine two-state fit, so the remaining 3.65-nat training gap is B's structure,
   not a G miss); held-out B3 − G3 on that fold −1.2 nat (was +18.6). RSC: the D4 commit (24 Oct, after 154d799).

## 4. Readings under the repaired fitter

### 4.1 First repaired block, BEFORE D4 (R1-R4; `results/s2/decision_pre_d4/W2`, sets 0-8)
0 POSITIVE, 5 NEGATIVE, 4 UNRESOLVED; 0/900 training nesting violations; EM median 5 steps; 1164-1532 s per set on 12
workers (about 570 s per participant-dataset against 165 s under rev 6).

| set | primary | Δ₃ mean [95% t] nat/trial | positive | max | note |
|---|---|---|---|---|---|
| 0 | NEGATIVE | −0.0014 [−0.0023, −0.0006] | 6/20 | +0.0005 | |
| 1 | NEGATIVE | −0.0011 [−0.0018, −0.0003] | 6/20 | +0.0008 | rev 6: POSITIVE +0.0058, 16/20 |
| 2 | NEGATIVE | −0.0016 [−0.0026, −0.0006] | 4/20 | +0.0004 | |
| 3 | NEGATIVE | −0.0013 [−0.0025, −0.0002] | 5/20 | +0.0033 | |
| 4 | UNRESOLVED | +0.0004 [−0.0011, +0.0020] | 9/20 | +0.0057 | single-fold excesses (D4) |
| 5 | UNRESOLVED | +0.0002 [−0.0023, +0.0027] | 7/20 | +0.0209 | m4 (S17) fold 0: D4 case |
| 6 | NEGATIVE | −0.0015 [−0.0020, −0.0009] | 2/20 | +0.0000 | |
| 7 | UNRESOLVED | +0.0003 [−0.0019, +0.0025] | 7/20 | +0.0194 | m12 (S13) fold 0: D4 case |
| 8 | UNRESOLVED | −0.0006 [−0.0022, +0.0010] | 7/20 | +0.0082 | |

No POSITIVE set on this block (gate (b) itself is evaluated at R = 100 in S4b, never here), but the UNRESOLVED sets
are not noise: they are the D4 mechanism, which is why the block was refit rather than continued.

### 4.2 Final fitter (D4-patched): W2 sets 0-9 (`results/s2/decision/W2`, 24 Oct 13:02-16:35Z)
**0 POSITIVE, 8 NEGATIVE, 2 UNRESOLVED**; Δ₃ per participant −0.00116 (sd 0.00192) nat/trial, set means [−0.0016,
−0.0003]; 0/1000 training nesting violations; 0/200 participants UNAVAILABLE; EM median 5 steps; 600 s per
participant-dataset (1151-1559 s per set of 20 on 12 workers, about 3% over the pre-D4 block).

| set | primary | Δ₃ mean [95% t] nat/trial | positive | max | pre-D4 (§4.1) |
|---|---|---|---|---|---|
| 0 | NEGATIVE | −0.0015 [−0.0022, −0.0008] | 4/20 | +0.0001 | NEGATIVE −0.0014 |
| 1 | NEGATIVE | −0.0012 [−0.0019, −0.0004] | 6/20 | +0.0007 | NEGATIVE −0.0011 |
| 2 | NEGATIVE | −0.0012 [−0.0019, −0.0004] | 4/20 | +0.0003 | NEGATIVE −0.0016 |
| 3 | NEGATIVE | −0.0016 [−0.0027, −0.0005] | 3/20 | +0.0009 | NEGATIVE −0.0013 |
| 4 | UNRESOLVED | −0.0003 [−0.0016, +0.0009] | 7/20 | +0.0046 | UNRESOLVED +0.0004, max +0.0057 |
| 5 | NEGATIVE | −0.0012 [−0.0021, −0.0004] | 5/20 | +0.0020 | UNRESOLVED +0.0002, max +0.0209 (D4 case) |
| 6 | NEGATIVE | −0.0014 [−0.0020, −0.0009] | 2/20 | +0.0000 | NEGATIVE −0.0015 |
| 7 | NEGATIVE | −0.0009 [−0.0016, −0.0002] | 5/20 | +0.0029 | UNRESOLVED +0.0003, max +0.0194 (D4 case) |
| 8 | UNRESOLVED | −0.0011 [−0.0025, +0.0002] | 5/20 | +0.0060 | UNRESOLVED −0.0006, max +0.0082 |
| 9 | NEGATIVE | −0.0012 [−0.0018, −0.0005] | 3/20 | +0.0011 | (not run) |

D4 counters over the 1000 folds (`count_em_stops.py decision W2`): no EM chain ended on a NOT_CONVERGED inner solve
(pre-D4 11); generalised-EM ascent steps accepted 35 (G3+ 17, G2 7, B3+ 5, B2 6), every one of them improving, so the
4× inner retry never had to fire; two chains each for B2 and B3+ ended on a small objective decrease (as designed).
The unguarded re-seed from B improved G3+ on 307/1000 folds (gain over G's own chains: median 0.01 nat, p90 8.9,
> 5 nat on 48, max 46.2) and G2 on 278/1000 (median 0.00, > 5 nat on 2, max 51.2) — a re-seed chain that does not
improve leaves no trace in the set json, so these are improvement counts. Training gap B3+ − G3+: median 0.12 nat,
p90 1.85, p99 4.37, max 8.7 (pre-D4 p99 7.65, max 387.9); 8 folds > 5 nat (19); G3 REDUCED while B3 POSITIVE once (3).
Selection: G3 POSITIVE 973/1000, B3 970/1000; `positive_at_floor` 26-27.
The two D4 cases are gone: set 5 m4 (S17) and set 7 m12 (S13) no longer carry a single-fold excess, and both sets read
NEGATIVE. The two remaining UNRESOLVED sets are NOT the D4 signature. Every participant above +0.003 nat/trial (set 4:
m3 S10 +0.0037, m7 S20 +0.0032, m14 S19 +0.0046; set 8: m10 S19 +0.0060) has the same value before and after the
patch, small TRAINING gaps on all five folds (S19: 2.6-7.1 nat on every fold) and held-out B3 − G3 fold differences
that are positive on two to four of the five folds and negative on the rest (set 4 m14: [−1.85, +2.33, −0.15, +4.52,
−0.61] nat; set 8 m10: [+1.90, +2.31, +1.15, +0.22, −0.05]; the all-fold positivity is the training gaps', not the
held-out gains'). Largest on S19 (strength 2.32, s_g 0.76, s_τ 48 ms; S14 is the strongest responder of the twenty at
2.94, S19 the second). Our reading is the declared flexibility of the two-state family (§4: a point mass at zero plus
a lognormal high branch approximates a wide lognormal amplitude law); it is recorded as a HYPOTHESIS (Codex S3 review,
finding 4): the records do not identify the cause, do not exclude a residual numerical or covariance effect, and in a
correctly specified population extra flexibility alone gives B no strictly better population log score at truth. It
moves set means by at most +0.0005 and produces no POSITIVE set; S4b measures its rate at R = 100. Gate (b) is NOT
evaluated here: 0 of 10 POSITIVE has a one-sided 95% Clopper–Pearson upper bound of 25.9% on the false-call rate; the
design's ceiling (≤ 1 in 100) is evaluated at R = 100 in S4b.

### The AWS closure at R = 25 (4.3-4.5)
LABEL for 4.3-4.5, 5.1, 6, 7 and 9: under the pre-repair fitter, code 6d447ad94463, 24-25 Oct AWS closure; to be
re-read after the warm-endpoint repair (Codex review of 25 Oct). Records: `results/s2_aws/decision/{W2,T1,O1}/set_<r>.json`
and `summary.{json,md}`, assembled on the Mac on 25 Oct from the hosts' per-task files with the fleet's own bundle
571fcd9 (checksum verified), so set and participant records both carry 6d447ad94463. Six c7a.24xlarge hosts at 48
workers, two per setting working the 25 sets from both ends (§9). Every host stopped at its 8 h lifetime. T1 and O1
are complete (500 of 500 participant-datasets). W2 is not: 497 of 500, so 22 sets are complete and sets 11, 12, 13
each lack one participant (set 11 m8, set 12 m2, set 13 m1). They were not relaunched. Bounds are exact one-sided 95%
Clopper–Pearson. Gates (b) and (c) are evaluated in S4b only, never here.

### 4.3 T1 (two-state generators, POSITIVE = detection; power needs about 45/50)
**25 POSITIVE, 0 NEGATIVE, 0 UNRESOLVED, 0 UNAVAILABLE** of 25. Δ₃ per participant +0.01404 (sd 0.01809) nat/trial; set
means [+0.0105, +0.0208]; positive participants 13-19 of 20 per set. 0/500 participants UNAVAILABLE. Detection 25/25:
the lower bound on the detection rate is 88.7%. S4b needs 45 of 50 sets (§7.3 gate (c), lower bound 80.1%).

| set | primary | Δ₃ mean [95% t] nat/trial | positive | max |
|---|---|---|---|---|
| 0 | POSITIVE | +0.0106 [+0.0049, +0.0163] | 16/20 | +0.0477 |
| 1 | POSITIVE | +0.0159 [+0.0045, +0.0272] | 17/20 | +0.0893 |
| 2 | POSITIVE | +0.0171 [+0.0062, +0.0280] | 17/20 | +0.0851 |
| 3 | POSITIVE | +0.0208 [+0.0076, +0.0339] | 15/20 | +0.0800 |
| 4 | POSITIVE | +0.0170 [+0.0085, +0.0256] | 18/20 | +0.0630 |
| 5 | POSITIVE | +0.0108 [+0.0034, +0.0182] | 15/20 | +0.0643 |
| 6 | POSITIVE | +0.0143 [+0.0051, +0.0236] | 15/20 | +0.0573 |
| 7 | POSITIVE | +0.0144 [+0.0074, +0.0213] | 17/20 | +0.0468 |
| 8 | POSITIVE | +0.0122 [+0.0048, +0.0196] | 17/20 | +0.0515 |
| 9 | POSITIVE | +0.0105 [+0.0033, +0.0177] | 14/20 | +0.0418 |
| 10 | POSITIVE | +0.0148 [+0.0049, +0.0246] | 14/20 | +0.0662 |
| 11 | POSITIVE | +0.0123 [+0.0060, +0.0185] | 18/20 | +0.0495 |
| 12 | POSITIVE | +0.0111 [+0.0044, +0.0179] | 14/20 | +0.0474 |
| 13 | POSITIVE | +0.0182 [+0.0064, +0.0299] | 13/20 | +0.0841 |
| 14 | POSITIVE | +0.0125 [+0.0065, +0.0185] | 19/20 | +0.0443 |
| 15 | POSITIVE | +0.0161 [+0.0086, +0.0237] | 18/20 | +0.0627 |
| 16 | POSITIVE | +0.0159 [+0.0089, +0.0229] | 17/20 | +0.0559 |
| 17 | POSITIVE | +0.0123 [+0.0050, +0.0195] | 16/20 | +0.0530 |
| 18 | POSITIVE | +0.0112 [+0.0033, +0.0191] | 15/20 | +0.0549 |
| 19 | POSITIVE | +0.0181 [+0.0099, +0.0262] | 18/20 | +0.0572 |
| 20 | POSITIVE | +0.0110 [+0.0042, +0.0178] | 17/20 | +0.0551 |
| 21 | POSITIVE | +0.0170 [+0.0075, +0.0264] | 16/20 | +0.0645 |
| 22 | POSITIVE | +0.0111 [+0.0058, +0.0164] | 17/20 | +0.0418 |
| 23 | POSITIVE | +0.0132 [+0.0037, +0.0226] | 17/20 | +0.0747 |
| 24 | POSITIVE | +0.0128 [+0.0021, +0.0236] | 16/20 | +0.0756 |

The Mac's T1 set 0 (`results/s2/decision/T1/set_0.json`, code ca25a7be9e9f) read POSITIVE +0.0105, 15/20; the AWS set 0
reads POSITIVE +0.0106, 16/20.

### 4.4 O1 (time-stretch, graded; POSITIVE = false call)
**0 POSITIVE, 14 NEGATIVE, 11 UNRESOLVED, 0 UNAVAILABLE** of 25. Δ₃ per participant −0.00115 (sd 0.00219) nat/trial; set
means [−0.0022, −0.0003]; largest single participant +0.0082 (set 1). 0/500 participants UNAVAILABLE. False calls
(POSITIVE + UNAVAILABLE) 0/25: the upper bound on the false-call rate is 11.3%. S4b's ceiling is 1 in 100.

| set | primary | Δ₃ mean [95% t] nat/trial | positive | max |
|---|---|---|---|---|
| 0 | UNRESOLVED | −0.0004 [−0.0008, +0.0000] | 9/20 | +0.0010 |
| 1 | UNRESOLVED | −0.0006 [−0.0018, +0.0005] | 3/20 | +0.0082 |
| 2 | UNRESOLVED | −0.0013 [−0.0027, +0.0001] | 5/20 | +0.0036 |
| 3 | NEGATIVE | −0.0012 [−0.0020, −0.0003] | 4/20 | +0.0014 |
| 4 | NEGATIVE | −0.0018 [−0.0027, −0.0009] | 3/20 | +0.0002 |
| 5 | NEGATIVE | −0.0020 [−0.0034, −0.0006] | 5/20 | +0.0029 |
| 6 | UNRESOLVED | −0.0010 [−0.0022, +0.0001] | 5/20 | +0.0062 |
| 7 | NEGATIVE | −0.0008 [−0.0015, −0.0002] | 6/20 | +0.0014 |
| 8 | UNRESOLVED | −0.0008 [−0.0017, +0.0001] | 6/20 | +0.0050 |
| 9 | UNRESOLVED | −0.0010 [−0.0022, +0.0002] | 5/20 | +0.0064 |
| 10 | UNRESOLVED | −0.0003 [−0.0014, +0.0009] | 7/20 | +0.0059 |
| 11 | NEGATIVE | −0.0009 [−0.0015, −0.0002] | 4/20 | +0.0015 |
| 12 | NEGATIVE | −0.0017 [−0.0025, −0.0009] | 2/20 | +0.0001 |
| 13 | UNRESOLVED | −0.0004 [−0.0008, +0.0000] | 6/20 | +0.0017 |
| 14 | UNRESOLVED | −0.0013 [−0.0028, +0.0002] | 7/20 | +0.0039 |
| 15 | NEGATIVE | −0.0008 [−0.0015, −0.0002] | 5/20 | +0.0022 |
| 16 | UNRESOLVED | −0.0006 [−0.0013, +0.0001] | 6/20 | +0.0033 |
| 17 | NEGATIVE | −0.0017 [−0.0025, −0.0009] | 2/20 | +0.0001 |
| 18 | NEGATIVE | −0.0014 [−0.0025, −0.0004] | 5/20 | +0.0026 |
| 19 | NEGATIVE | −0.0018 [−0.0029, −0.0007] | 5/20 | +0.0010 |
| 20 | NEGATIVE | −0.0014 [−0.0021, −0.0006] | 3/20 | +0.0000 |
| 21 | NEGATIVE | −0.0017 [−0.0026, −0.0009] | 3/20 | +0.0001 |
| 22 | NEGATIVE | −0.0022 [−0.0042, −0.0003] | 0/20 | −0.0000 |
| 23 | UNRESOLVED | −0.0007 [−0.0017, +0.0003] | 5/20 | +0.0051 |
| 24 | NEGATIVE | −0.0010 [−0.0016, −0.0004] | 3/20 | +0.0017 |

### 4.5 W2 at R = 25 (22 complete sets), beside the R = 10 block of 4.2
**0 POSITIVE, 17 NEGATIVE, 5 UNRESOLVED, 0 UNAVAILABLE** of 22 complete sets. Δ₃ per participant −0.00107 (sd 0.00227)
nat/trial; set means [−0.0021, +0.0004]; 0/440 participants UNAVAILABLE. False calls 0/22: the upper bound on the
false-call rate is 12.7% (4.2's 0/10 gave 25.9%). The last column is the Mac's 4.2 reading (code a45a07d92b82, 12
workers). On sets 0-9 the two readings give the same primary in all ten sets.

| set | primary | Δ₃ mean [95% t] nat/trial | positive | max | Mac, 4.2 |
|---|---|---|---|---|---|
| 0 | NEGATIVE | −0.0013 [−0.0021, −0.0004] | 5/20 | +0.0043 | NEGATIVE −0.0015, max +0.0001 |
| 1 | NEGATIVE | −0.0012 [−0.0019, −0.0005] | 7/20 | +0.0007 | NEGATIVE −0.0012, max +0.0007 |
| 2 | NEGATIVE | −0.0009 [−0.0016, −0.0003] | 5/20 | +0.0003 | NEGATIVE −0.0012, max +0.0003 |
| 3 | NEGATIVE | −0.0018 [−0.0029, −0.0007] | 4/20 | +0.0003 | NEGATIVE −0.0016, max +0.0009 |
| 4 | UNRESOLVED | −0.0005 [−0.0017, +0.0007] | 6/20 | +0.0046 | UNRESOLVED −0.0003, max +0.0046 |
| 5 | NEGATIVE | −0.0018 [−0.0028, −0.0007] | 3/20 | +0.0020 | NEGATIVE −0.0012, max +0.0020 |
| 6 | NEGATIVE | −0.0014 [−0.0019, −0.0009] | 2/20 | +0.0000 | NEGATIVE −0.0014, max +0.0000 |
| 7 | NEGATIVE | −0.0009 [−0.0015, −0.0002] | 5/20 | +0.0029 | NEGATIVE −0.0009, max +0.0029 |
| 8 | UNRESOLVED | −0.0013 [−0.0026, +0.0001] | 4/20 | +0.0058 | UNRESOLVED −0.0011, max +0.0060 |
| 9 | NEGATIVE | −0.0010 [−0.0017, −0.0003] | 6/20 | +0.0012 | NEGATIVE −0.0012, max +0.0011 |
| 10 | NEGATIVE | −0.0011 [−0.0022, −0.0000] | 3/20 | +0.0054 | (not run) |
| 11 | incomplete (19/20) | | | | (not run) |
| 12 | incomplete (19/20) | | | | (not run) |
| 13 | incomplete (19/20) | | | | (not run) |
| 14 | UNRESOLVED | −0.0007 [−0.0016, +0.0002] | 5/20 | +0.0013 | (not run) |
| 15 | NEGATIVE | −0.0011 [−0.0019, −0.0003] | 5/20 | +0.0023 | (not run) |
| 16 | NEGATIVE | −0.0007 [−0.0010, −0.0003] | 4/20 | +0.0002 | (not run) |
| 17 | UNRESOLVED | +0.0004 [−0.0026, +0.0034] | 4/20 | +0.0270 | (not run) |
| 18 | NEGATIVE | −0.0009 [−0.0016, −0.0003] | 4/20 | +0.0016 | (not run) |
| 19 | UNRESOLVED | −0.0005 [−0.0013, +0.0002] | 5/20 | +0.0050 | (not run) |
| 20 | NEGATIVE | −0.0010 [−0.0017, −0.0004] | 5/20 | +0.0010 | (not run) |
| 21 | NEGATIVE | −0.0017 [−0.0029, −0.0005] | 4/20 | +0.0026 | (not run) |
| 22 | NEGATIVE | −0.0009 [−0.0017, −0.0002] | 6/20 | +0.0026 | (not run) |
| 23 | NEGATIVE | −0.0021 [−0.0031, −0.0011] | 3/20 | +0.0017 | (not run) |
| 24 | NEGATIVE | −0.0012 [−0.0018, −0.0006] | 2/20 | +0.0007 | (not run) |

The three incomplete sets, from their 19 task files (descriptive only; not set records, not counted above): set 11
−0.0013 [−0.0022, −0.0003], 4/19 positive, max +0.0017; set 12 −0.0009 [−0.0018, +0.0000], 6/19, max +0.0011; set 13
−0.0012 [−0.0021, −0.0002], 2/19, max +0.0005. None has a positive lower bound.
Two single-fold excesses. Set 17 m9 (S2) is +0.0270, the largest W2 value in either block: its held-out B3 − G3 fold
sums are [+0.01, +23.4, 0.00, −0.03, +0.01] nat, so all of it sits in fold 1; set 17 reads UNRESOLVED. Set 0 m15 (S4) is
+0.0043 on AWS against +0.0001 on the Mac: fold sums [+0.34, 0.00, 0.00, +3.09, +0.03] nat; fold 3 is also the largest
training nesting violation of the closure (B3+ 11.5 nat below G3+, §6). This is the m15 swing of §8.

## 5. Latency recovery under the free Σ (`results/s2/diagnosis/recovery_check_em_oracle_scaled.txt`)

G3/B3 full-data fits on W2-type data from S2, S4, S13, S20, S10 (5 replicates each; em vs oracle Σ vs scaled start Σ;
75 fits, 1135 s on 12 workers). Medians em / oracle / true: S10 78 / 82 / 82 ms; S13 53 / 51 / 54; S20 39 / 38 / 42;
S2 59 / 72 / 67 (the oracle itself ranges 56-118 on S2 — a poorly identified spread on the primary span, one 150 ms box
hit in 5 under em and under scaled); S4 15 / 68 / 63 (em replicates 0, 12, 15, 42, 62). On the WEAKEST responder
(S4: strength 0.44, a(5) 0.35) the free Σ absorbs the jitter-induced variance and the spread collapses where the oracle
recovers it. Verdict: the contrast / gate (b) defect is repaired; latency recovery is strength-dependent under the free
Σ — a declared limitation to be MEASURED in the recovery battery (R1-R5 already carry the strength covariate) and a
rev 7 item for Codex, with the Σ-structure options listed, not decided: (a) profiles/recovery with Σ held at the
unrestricted fit's EM value; (b) a factor-structured Σ (diagonal + rank-k) with fewer free parameters; (c) Σ estimated
by EM under the graded fit and SHARED by both families for the recovery estimand only.

### 5.1 Rerun under the final fitter, with the oracle_sigma arm (25 Oct; `results/s2/diagnosis/recovery_check_final.json`)
Label: under the pre-repair fitter; to be re-read after the warm-endpoint repair (Codex review of 25 Oct). The rerun ran
on the Mac, not on the fleet: the AWS recovery stage crashed on a Mac-only `sys.path` (fixed in RSC e5f1fe1). 100 fits:
S2, S4, S13, S20, S10 × em / oracle / oracle_sigma / scaled × 5 replicates; 02:54-03:29Z, 2,083 s on 8 workers beside
the repair job; 142 s per fit median, 501 s max. `oracle_sigma` = the generator's Σ with the ESTIMATED training-catch
μ0, so that Σ's contribution is isolated (Codex S3 review 24 Oct, finding 5). `oracle` = the generator's μ0 and Σ.
`scaled` = the scaled catch covariance, fixed, no EM.
Code: the workers started at 02:54Z, when the five hashed files matched HEAD 1d1c337 (hash 86eccfb3e15e); 62 of the 100
rows carry that hash. `code_hash()` hashes the files on disk when it is called, and the repair job edited `fit.py`
during the run, so the other 38 rows and the header (6f0d60ddef91) carry seven later hashes. Whether any worker
re-imported the edited `fit.py` I can't determine from the record; loky normally keeps its workers for the whole call.
Neither 86eccfb3e15e nor the fleet's 6d447ad94463 carries the warm-endpoint repair.
Medians of the fitted G3 s_τ (ms) over 5 replicates:

| subject | true s_τ / s_g | em | oracle | oracle_sigma | scaled | em, 24 Oct run (above) |
|---|---|---|---|---|---|---|
| S10 | 82.2 / 0.56 | 78.1 | 82.3 | 78.3 | 82.9 | 78 |
| S13 | 54.4 / 0.62 | 53.2 | 50.7 | 53.4 | 59.8 | 53 |
| S20 | 41.8 / 0.58 | 38.6 | 37.7 | 37.3 | 51.9 | 39 |
| S2 | 67.3 / 0.67 | 59.3 | 72.5 | 62.1 | 69.1 | 59 |
| S4 | 63.4 / 0.53 | 15.1 | 67.7 | 42.1 | 50.0 | 15 |

Replicates. S2 em 72.0, 41.9, 46.9, 59.3, 150.0 (one 150 ms box hit; scaled also hits 150 once); oracle 56.5-117.5;
oracle_sigma 42.0-101.6. S4 em 61.9, 0 (G3 REDUCED), 41.8, 12.1, 15.1 (24 Oct: 0, 12, 15, 42, 62); oracle 51.0-76.7;
oracle_sigma 22.1-52.3; scaled 43.6-150 (one box hit). G3 s_g medians are within 0.05 of the truth in every cell except
S4 scaled (0.45 against 0.53). B3's s_τ medians equal G3's to within 2 ms, and B3's A(5) median is 1.00 in every cell
but S10 scaled (0.97): B3 collapses onto G3 on these graded data. EM steps median 5 (S20 3). Every G3 fit is POSITIVE
except S4 em replicate 2 (REDUCED).
The S4 collapse question of §10: the em collapse on S4 reproduces under the final fitter (median 15.1 ms against 15 on
24 Oct; the five replicates within 0.3 ms of the 24 Oct values), so it was not the D4 under-finding. On S4 oracle_sigma
reads 42.1 ms, between em (15.1) and oracle (67.7; truth 63.4). On the other four subjects oracle_sigma is within 3 ms
of em. The Σ-structure options above stay listed, not decided.

## 6. Nesting and EM statistics
Pre-D4 block: 0/900 training nesting violations (the warm chains hold l(B) ≥ l(G) by construction); EM chains ended on a
NOT_CONVERGED inner solve 11× (G3+ 6, G2 4, B3+ 1) and on a small objective decrease 5× (G2 1, B2 2, B3+ 2). Final
fitter, W2 0-9: 0/1000 violations; no chain ended on a NOT_CONVERGED solve; 35 ascent steps accepted; the re-seed from
B improved G3+ on 31% of folds (by > 5 nat on 5%) — the G3+ start set alone still misses optima on about one fold in
twenty by 5-46 nat, which the B-basin re-seed now recovers by construction (§4.2).

AWS closure (label of 4.3; scratchpad `count_em_stops_aws.py results/s2_aws <S>`). Folds = sets × 20 × 5.

| | W2 (22 sets) | T1 (25) | O1 (25) |
|---|---|---|---|
| training nesting violations, l(B3+) < l(G3+) − 1e-6 | 11/2200 | 6/2500 | 16/2500 |
| of them by more than 1 nat | 2 (11.5, 5.9) | 0 (worst 0.21) | 3 (5.8, 4.3, 3.0) |
| EM chain ended on a NOT_CONVERGED inner solve | 0 | 0 | 0 |
| EM chain ended on a small objective decrease | 4 (G2 1, B2 2, B3+ 1) | 1 (B3+) | 6 (G2 3, B2 2, B3+ 1) |
| generalised-EM ascent steps accepted (G2 / G3+ / B2 / B3+) | 165 / 153 / 16 / 34 | 283 / 325 / 40 / 78 | 241 / 175 / 31 / 25 |
| inner 4× retries | 0 | 0 | 0 |
| EM steps of the selected G3/B3: median, p90, max | 5, 7, 8 | 6, 8, 8 | 5, 7, 8 |
| re-seed from B improved G3+ (of folds) | 682 (> 5 nat 108; max 303.2) | 1202 (> 5 nat 149; max 400.2) | 1079 (> 5 nat 355; max 345.9) |
| re-seed from B improved G2 | 550 (max 51.2) | 825 (max 418.1) | 550 (max 131.0) |
| training gap B3+ − G3+ nat: median, p90, p99, max | 0.09, 1.72, 4.00, 11.4 | 10.12, 29.6, 56.7, 77.5 | 0.00, 1.75, 4.88, 15.6 |
| folds with gap > 5 nat | 13 | 1933 | 23 |
| G3 REDUCED while B3 POSITIVE | 6 | 125 | 12 |
| selection G3 POSITIVE / REDUCED | 2123 / 77 | 2100 / 400 | 2185 / 315 |
| selection B3 POSITIVE / REDUCED | 2115 / 85 | 2103 / 397 | 2141 / 359 |
| `positive_at_floor` G3 / B3 | 66 / 67 | 102 / 93 | 271 / 276 |
| fits UNAVAILABLE | 0 | 0 | 0 |

The nesting violations are not zero, unlike the Mac's W2 0-9 (0/1000). Of the 33, 28 are below 0.6 nat (21 below 0.005). The large
ones: W2 set 0 m15 (S4) fold 3, −11.5 nat, B3 REDUCED, held-out B3 − G3 +3.1 nat on that fold; W2 set 23 m13 (S16) fold
2, −5.9 nat; O1 set 16 m8 (S4) fold 1, −5.8 nat; O1 set 8 m5 (S4) fold 1, −4.3 nat; O1 set 16 m12 (S4) fold 2, −3.0 nat.
Four of the five are on base participant S4. The re-seed counts are improvement counts (a re-seed chain that does not
improve leaves no trace).

## 7. Start-family usage (which start families were material)
From the archived starts of the final W2 block (1000 fits per candidate; scratchpad `starts_usage.py decision W2`).
"Chain" = which EM chain produced the selected optimum (main multi-start chain / warm chain from the G twin under its
Σ / re-seed chain from B); "first-stage winner" = the family of the best CONVERGED start of the main chain before EM;
"beat design" = fits where a non-design start exceeded the best §5 design start by > 1e-6 relative.

| candidate | selected optimum from chain | first-stage winner by family | beat design | gain over design (nat): p90 / max |
|---|---|---|---|---|
| G2 | main 722, re-seed 278 | design 1000 | 0/1000 | 0.00 / 0.0 |
| G3+ | main 693, re-seed 307 | smeared 606, design 315, lift 79 | 308/1000 | 2.78 / 987.7 |
| B2 | main 568, twin chain 432 | design 828, collapse 172 | 105/1000 | 0.44 / 34.2 |
| B3+ | main 587, twin chain 413 | smeared 529, design 287, lift 73, collapse 111 | 406/1000 | 10.81 / 652.5 |

Start statuses: G2 10,985 CONVERGED / 12 NOT_CONVERGED, G3+ 17,731 / 86, B2 13,354 / 10, B3+ 20,340 / 88; no fit
UNAVAILABLE. Reading: for the reduced models the four design starts suffice (G2 never improved on by another family;
B2's collapse start wins 17%). For the positive-spread models the design starts alone would have missed the optimum
on 31% (G3+) and 41% (B3+) of fits, by up to about 1,000 nat; the SMEARED-kernel starts are the most frequent winners,
the lifts win 7-8%, and the warm chains (twin and re-seed) supply the selected optimum in 30-43% of fits. Every family
of R2 is material and the union recipe, with the warm and re-seed chains, is what rev 7 should FREEZE for S3 (§5:
"starts found material are added to the frozen recipe at S3 for all models alike").

AWS closure (label of 4.3; scratchpad `starts_usage_aws.py results/s2_aws <S>`, the same counting as above): W2 at 2,200
fits per candidate (22 sets), T1 and O1 at 2,500.

| setting | candidate | selected optimum from chain | first-stage winner by family | beat design | gain over design (nat): p90 / max |
|---|---|---|---|---|---|
| W2 | G2 | main 1650, re-seed 550 | design 2200 | 0/2200 | 0.00 / 0.0 |
| W2 | G3+ | main 1518, re-seed 682 | smeared 1353, design 694, lift 153 | 665/2200 | 2.97 / 987.9 |
| W2 | B2 | main 1273, twin chain 927 | design 1819, collapse 381 | 205/2200 | 0.00 / 34.2 |
| W2 | B3+ | main 1280, twin chain 920 | smeared 1223, design 649, collapse 203, lift 125 | 850/2200 | 9.34 / 652.5 |
| T1 | G2 | main 1675, re-seed 825 | design 2500 | 0/2500 | 0.00 / 0.0 |
| T1 | G3+ | main 1299, re-seed 1201 | smeared 1521, design 771, lift 208 | 871/2500 | 3.50 / 166.8 |
| T1 | B2 | main 2352, twin chain 148 | design 2451, collapse 49 | 48/2500 | 0.00 / 25.2 |
| T1 | B3+ | main 2281, twin chain 219 | smeared 1405, design 868, lift 215, collapse 12 | 894/2500 | 5.67 / 98.7 |
| O1 | G2 | main 1950, re-seed 550 | design 2500 | 0/2500 | 0.00 / 0.0 |
| O1 | G3+ | main 1421, re-seed 1079 | smeared 1636, design 736, lift 128 | 872/2500 | 6.74 / 1015.9 |
| O1 | B2 | main 1389, twin chain 1111 | design 2008, collapse 492 | 279/2500 | 1.70 / 163.6 |
| O1 | B3+ | main 1213, twin chain 1287 | smeared 1437, design 750, collapse 171, lift 142 | 1042/2500 | 10.69 / 69.1 |

Start statuses (CONVERGED / NOT_CONVERGED): W2 G2 23,546 / 200, G3+ 38,744 / 405, B2 29,061 / 164, B3+ 44,400 / 403;
T1 G2 32,113 / 330, G3+ 50,886 / 717, B2 34,253 / 175, B3+ 52,805 / 525; O1 G2 26,295 / 274, G3+ 45,559 / 451, B2
32,942 / 245, B3+ 52,782 / 434. No fit UNAVAILABLE. The pattern of the Mac's W2 block holds in all three settings: G2's
first-stage winner is always a design start; for G3+ and B3+ a non-design start beats the best design start on 30-42%
of fits (T1 B3+ 36%, O1 B3+ 42%); the smeared starts are the most frequent first-stage winner; the re-seed chain gives
G3+'s selected optimum on 31% (W2), 48% (T1) and 43% (O1) of fits. On T1 the twin chain gives B's optimum on 6% (B2)
and 9% (B3+) of fits, against 42-52% on W2 and O1.

## 8. §4 checks, basins, profile-start validation
Ranks (`s2.py checks --kind ranks`, `results/s2/checks/ranks.json`, 24 Oct under the final code): the stacked 31-node
window basis has full rank (primary 496 × 16 → 16, whole 1643 × 35 → 35; smallest/largest singular value 0.043 and
0.041); the zero-shift visible basis 16 × 12 → 12 and 53 × 31 → 31. The per-trial log-likelihood Jacobian at a generic
point (W2 set 0 m0 S10 fold 0, θ_τ 40 ms, s_g 0.5, 748 training trials) has FULL rank for every model: G0 16/16, G1+
21/21, G2 17/17, G3+ 22/22, B0 18/18, B1+ 23/23, B2 19/19, B3+ 24/24 (threshold 1e-8 of the largest singular value).
The smallest singular values of the positive-spread models (1.2e-5 to 2.7e-5 against a largest of order 1e2, ratio
1.6e-7 to 6.9e-7) are the shift-only template directions, identified only through shifted nodes as §4 says — locally
identified, weakly.
Small spread (`s2.py checks --kind smallspread`, `results/s2/checks/small_spread.json`, final code): ℓ_prof(s) −
ℓ_reduced at parent spreads 1, 2, 5, 8, 10, 20 ms on W2-m0-S10 (G3 unrestricted POSITIVE at 84.5 ms, B3 at 82.5) and
T1-m0-S10 (G3 59.8 ms). At 1 ms the constrained positive-spread fit equals the reduced fit (−5e-9 / +6e-7 nat; node-0
weight 1.000), at the 2 ms floor it is +5e-5 nat above it (node-0 weight 0.99999), then the profile rises smoothly:
W2 G +1.75 (5 ms), +4.98 (8), +12.2 (10), +57.3 (20); W2 B +1.83, +5.24, +11.4, +57.1; T1 G +1.17, +3.50, +5.69, +26.9.
So the region below the 2 ms floor is flat to numerical precision (the floor loses nothing), the 10 ms node spacing
resolves the first rise, and every constrained fit was AVAILABLE (the finite lifts of R3 at work).
Basins (`s2.py basins`, `results/s2_aws/basins/{W2,T1,O1}_set0.json` + `summary.json`; 24 Oct on the AWS validators
host under the final hash): the repaired procedure against complete EM fits from the development starts, set 0 of each
setting, 20 participant-datasets per candidate. The development starts improved on the repaired procedure on at most
one dataset in twenty per candidate and by at most 0.201 nat: W2 G2, G3+, B2, B3+ 0/20; T1 G2 1/20 (0.201 nat), G3+
1/20 (0.057), B2 and B3+ 0/20; O1 G2 0/20, G3+ 1/20 (0.172), B2 0/20, B3+ 1/20 (0.171); no nesting violation. Reading:
the frozen recipe finds the optimum the development search found, to 0.2 nat, on 19 of 20 datasets or better; the §4.2
reading does not move; Codex finding 6 is closed with no start added. PENDING: `--kind nodes` on the final W2 set 0
(33 scale nodes, 61 τ nodes, the 7-node prior rule against the archived default) and `s2.py profiles` (2- vs 4-start
constrained optima on 100 datasets per family; the profile machinery now has finite lifts, so this validation is
meaningful for the first time) — both running on the AWS closure fleet.
Two-pass scale quadrature (declared 25 Oct, for the Codex S3 re-review; DESIGN §4): the node check `g33` on W2 set 0
FAILED on the checks host (00:42Z: max |ΔΔ₃| 4.98e-4 against the tolerance 8.83e-5; m0, m7, m14, m15 over it; the
primary stayed NEGATIVE), and blanket 33 nodes costs about 1.9× per likelihood evaluation. The declared refinement,
`models.QUAD_G_RULE = "17then33"` (every fit at 17 nodes, then one warm EM chain at 33 nodes for each fitted scale-free
model with s_g > 0.6, the refit replacing it downstream; default `"17"` leaves the fitter as it was), was checked on
the Mac against that run's 33-node Δ₃ (`s2.py checks --kind twopass`, `results/s2/checks/twopass_g_W2_set0.json`, code
86eccfb3e15e, 8 workers beside another job): FAILED — max |Δ₃(two-pass) − Δ₃(33)| 3.70e-3, four participants over the
tolerance (m12 +1.8e-4, m14 +6.2e-4, m15 −3.7e-3, m18 −5.1e-4), 193/400 candidate fits refitted (G2 53, G3+ 47, B2
49, B3+ 44 of 100 each; fitted s_g median 0.59, max 0.91), training log-likelihoods moved by +0.002 to +0.11 nat,
primary NEGATIVE under 17, 33 and two-pass; cost 1.5% on the fit seconds within the run (12,635 task-seconds against
the archived 12,524 at 17 nodes). The two-pass rule is not validated. What the check also shows: m14 and m18 have no
fit above 0.6 (their two-pass Δ₃ equals the Mac's archived 17-node Δ₃ exactly), and the checks host's own 17-node Δ₃
(`delta3_ref`, code 6d447ad94463, AMD) differs from the Mac's archived 17-node Δ₃ (code a45a07d92b82) by up to 4.1e-3
at m15 and above the tolerance on m0, m7, m12, m14, m18 — on m0 and m7 the host's 33-node run moved by exactly the
amount that brings it back onto the Mac's 17-node value — so the 24 Oct FAIL and this one carry a fitter and host
difference as well as the quadrature. Codex traced the m15 swing to the fitter: a near-optimal B warm chain ends
NOT_CONVERGED after 12 iterations and is discarded (`reviews/2026-10-25_latency_quadrature_fix_codex_review.md`,
findings 1, 4, 11). The declared 0.4 retry was not run.
Repaired same-data, same-code node checks (25 Oct; `s2.py repair`, code 6f0d60ddef91, W2 set 0 regenerated with its 20
data identities verified against the Mac record, 12 Mac workers; `results/s2/checks/repair_W2_set0_{A..E}.json`,
`_summary.md`, `_status.txt`). The fitter now polishes stationary-but-unaccepted warm endpoints (Codex finding 11;
5-8 polishes per run, extra work r ≤ 2e-4) and flags a numerical failure when a lost chain was better than the
selected one. Runs: A 31/17, B 61/17, C 31/33, D 31/17 two-pass, E 121/17 warm from B. Every comparison FAILS the
participant tolerance T = min(8.83e-5, 0.1 × half-width) ≈ 7e-5: A vs B 5.33e-4 (m0; six over T; two selection
flips), A vs C 4.98e-4 (m14; eight over), D vs C 4.98e-4, B vs E 3.99e-4 (m14; seven over), D vs A 1.22e-4 (m4; two
over). A, C, D and E each carry one numerical failure (a re-seed chain from the other family lost after its polish);
B carries none. No refinement converges at the participant level (rms of the participant differences 1.4-1.8e-4
between latency rules), while every run's set mean moves by at most 3.8e-5 (set means −0.00147 A, −0.00151 B,
−0.00153 C, −0.00147 D, −0.00150 E; half-widths 6.8-7.1e-4) and the primary is NEGATIVE in all five. With Codex's
fixed-parameter finding (contrasts move < 2.7e-5 under 31 → 61 → 121 latency nodes), the reading is that the
participant-level differences are the fitter's end-point variation, not quadrature error. Under the declared rule
31 nodes are not retained, 61 are adopted, and the 121 recheck FAILED, so the latency rule goes to the Codex S3
re-review before any S4 draw. Cost: B 1.59× A's task-seconds, C 1.09×, D 0.76×, E 3.0×.

## 9. Cost (`results/bench/bench_20261024T171350Z.md`, `results/bench/recost_rev7_20261024T171350Z.md`)
Rev 6: 165 s per participant-dataset (bench_20261024T044019Z: 1.69 s per decision-batch start; S4 1,536 core-h base).
Final fitter, benchmark run ALONE on S10 after the W2 block and the D5 fix (24 Oct 17:14-17:36Z; generator fits under
Ledoit-Wolf: G3 80.1 ms / 0.57, B3 60.6 / 0.38, the stored files untouched). Per unit, sequential, one XLA thread:
decision participant-dataset (5 folds × G2/B2/G3+/B3+) 289 s (rev 6: 135 s); recovery full-data dataset (8 models)
82 s; constrained profile fit 6.8 s (2-start) / 14.0 s (4-start); ε dataset 1.8 s; c₀ pair 38 s; generator fit 244 s.
`bench.py`'s own cost table (718 core-h) multiplies rev 6 START counts by per-start seconds and is superseded: under
rev 7 every fit archives its EM steps and chains as starts. Counted per FIT (`recost_rev7.py`):

| category | core-hours (sequential rate) |
|---|---|
| S4a (ε, pilots, certification, c₀) | 332 |
| S4a re-certification contingency | 80 |
| S4b decision batch (23,000 participant-datasets) | 1,847 |
| S4b recovery (13,000 full-data datasets) | 296 |
| S4b profiles (390,000 constrained fits, 2-start) | 739 |
| S4b 4-start profiles, extra | 773 |
| S4b inherited pipeline | 93 |
| **S4 total** | **3,307 base, 4,240 worst** (the contingency counted for BOTH targets: 2 × 80) |
| S2 development (as costed) | 136 |
| real data | 20 |

The worst case budgets one secant correction for E1 AND one for T3 (§7.4 allows one each; the first re-cost of 24 Oct
budgeted one, 4,160). Contention: on the Mac's 12 performance cores the development block ran at 600 task-seconds per
decision dataset against 289 sequential (factor 2.08; memory bandwidth shared by 12 single-threaded XLA workers), so
the Mac's own S4 cost is about 5,300 core-hour-equivalents base, i.e. about 27 days of wall time for the base manifest
and about 33 with the contingency and 4-start profiles ("Mac alone about a month" stands). The factor is the Mac's own
contention, not an AWS multiplier. Target: c7a.24xlarge = 96 REAL cores (AMD Zen 4, one core per vCPU): 34.4 ideal
instance-hours base, 44.2 worst; at the design's USD 1.7/h about USD 59 / 75, at the 24 Oct spot quote (0.73-1.04/h
over seven days, cap 1.20, estimate 0.95) about USD 33 / 42, before start-up, barriers between sequential S4a stages,
contention and interruptions. The S2 closure fleet measured the target throughput (below); the ideal arithmetic is
superseded by it. Venue and cap: the owner's decision of 24 Oct (AWS spot, go, inside the USD 3,000 cap with about
USD 653 used; Unimog `rsc_t1_simulation_design.md` §12 row 24; S4a + S4b capped at USD 1,300 in that row).

**AWS, measured on the S2 closure fleet (24 Oct 2026; c7a.24xlarge = AMD EPYC 9R14, 96 cores, 192 GB; code hash
6d447ad94463; `aws/s4_spend.json` is the spend trail).**
- One decision participant-dataset ALONE on one AMD core (W2 set 0 m0, S18; the 8-vCPU probe): 1,513 s wall, 1,569 s
  CPU; two in parallel 1,375 / 1,492 s. The same task alone on the Mac's M4 core: 435 s (S11: 187 s). The AMD core is
  about 3.5× slower than the M4 core when each runs alone. Scores: G3 identical to the Mac's to 9 digits, B3 within
  1e-4 nat/trial (a different ISA, a slightly different EM end point; a development reading, not a gate).
- 96 workers per host THRASH: in 95 min the five 96-worker hosts finished only the lightest participant (S11), at
  500-5,156 s and growing, and no heavier participant at all. Not memory capacity (peak RSS per worker 0.70 GB after
  one task, 0.86 GB after two, on the Mac): the likelihood's per-evaluation intermediates (about 750 trials × 31 × 17
  nodes × 8 B = 3 MB each, several live at once) fit the Mac's caches and spill to the socket's shared memory system
  under 96 single-threaded workers.
- 48 workers per host: about 60-70 decision tasks per host-hour, read off the flagless W2-rev host (S4 2,323 s, S10
  2,595 s, S11 1,293-1,602 s; the Mac's 12-way contended times 546 / 465 / 357 s): 4-5× the Mac's loaded time per task
  at 4× the workers, so one c7a.24xlarge delivers about one Mac (72 decision tasks per hour). The host, not the core,
  is the ceiling.
- `XLA_FLAGS="--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1"` (the T1 EC2 tooling's
  setting) at 48 workers: medium participants 2,846-3,335 s and S11 2,064-2,116 s WITH the flag, against 2,323-2,595 s
  and 1,293-1,602 s without it — about 30% dearer (the compile step runs single-threaded). Removed from
  `aws/userdata_s4.sh` for S4 (RSC d748e89); the closure hosts kept it, because a restart loses about half a round.
- S4 cost at the measured rate: the unit is the host at 48 workers. S4 base 3,307 core-h × 3600 / 289 s ≈ 41,000
  decision-task-equivalents ≈ 600-700 host-hours ≈ 30-35 h on 20 hosts: about USD 600 on eu-north-1 spot alone
  (0.95/h), or about USD 2,400 with 15 of the 20 hosts on-demand (4.93/h). Quotas per region: 512 Spot + 520 On-Demand
  standard vCPU = 5 + 5 hosts; all-spot needs the Spot quota raised 512 → 2,048 vCPU (asked of the owner 24 Oct 21:14Z;
  the read-only IAM user cannot file it). The mostly on-demand fleet exceeds the USD 1,300 row cap: the owner's quota
  answer or the declared economies (DESIGN 8 time-priority amendment, about −25%) decides the fleet.
- Spot capacity: us-west-2a reclaimed the three spot decision hosts and the profiles host wholesale at 21:02-21:04Z
  (Saturday afternoon Pacific); us-west-2c had no capacity, us-west-2b priced above the 2.20 cap; eu-north-1b held
  all day. Spot quota accounting releases a few minutes after a termination (MaxSpotInstanceCountExceeded on an
  immediate retry).
- The closure fleet: eight hosts (W2/T1/O1 forward and the profiles and checks hosts on eu-north-1b spot at 0.95/h;
  W2-rev/T1-rev/O1-rev on us-west-2a on-demand at 4.93/h), about USD 20/h from 21:08Z; closed spend USD 10.29 at
  21:58Z.

**The closure's measured facts (label of 4.3: pre-repair fitter, code 6d447ad94463, 24-25 Oct AWS closure; to be re-read
after the warm-endpoint repair).**
- Decision hosts: W2 i-025acb9dd61ce172f, T1 i-0c18147043a6734d4, O1 i-00144a18c25323a08 (eu-north-1b spot, launched
  20:53Z); W2-rev i-00e2c2a978971ca84, T1-rev i-0ed7c85c6f149118e, O1-rev i-0d1da001ef952333b (us-west-2a on-demand,
  21:07Z). 48 workers each, 8 h lifetime. All six shut themselves down at the lifetime (04:53Z eu, 05:07Z us-west-2). No
  host logged "queue done": each host's queue held every task of its setting not on its disk at start, and the upload-only
  sync never told a host what its partner had finished. So after the two hosts met, they computed the same tasks twice.
  S3 keeps only the last version, so the duplicate count can't be determined from the records.
- Wall time per setting, from the 48-worker eu hosts' run start (20:54Z): T1 complete (500) by the 04:49Z poll, about
  7.9 h; O1 complete by 04:54Z, about 8.0 h; W2 at 497 when the last host stopped at 05:07Z (8.2 h). 21 task files came
  from the earlier 96-worker hosts of 19:15-20:53Z and the spot-interrupted W2-rev host 1.
- Task seconds per host (each task attributed to the host whose S3 sync wrote its final version; median / p90 / max):

| host | market | task files | median s | p90 s | max s | files per host-hour |
|---|---|---|---|---|---|---|
| W2 | eu-north-1b spot | 215 | 4,551 | 6,809 | 10,401 | 26.9 |
| T1 | eu-north-1b spot | 213 | 4,823 | 7,190 | 11,652 | 26.7 |
| O1 | eu-north-1b spot | 197 | 4,345 | 6,591 | 13,913 | 24.7 |
| W2-rev | us-west-2a on-demand | 274 | 4,107 | 6,239 | 12,982 | 34.3 |
| T1-rev | us-west-2a on-demand | 279 | 4,222 | 6,157 | 9,005 | 34.9 |
| O1-rev | us-west-2a on-demand | 298 | 4,006 | 5,840 | 9,948 | 37.3 |

  Per setting, all hosts: W2 median 4,247 s, p90 6,551, max 12,982 (497 files); T1 4,381 / 6,744 / 11,652; O1 4,119 /
  6,289 / 13,913. Files per host-hour = files ÷ the 7.99 h from run start to the lifetime stop. These are lower bounds
  on work done, because duplicates are not counted.
- Rate as achieved: 1,476 distinct task files from 48 billed host-hours = 30.8 per host-hour (eu spot hosts 26.1, us-west-2
  on-demand 35.5). The 60-70 per host-hour above was read off light and medium participants early in the run.
  At the achieved rate the S4 arithmetic above (about 41,000 decision-task-equivalents) gives about 1,330 host-hours,
  not 600-700. The S4 re-cost is not made here.
- Spend (`aws/s4_spend.json`, hours × the configured rate: spot at the 0.95 estimate, on-demand 4.93; not Cost Explorer):
  the six decision hosts 8.00 h each, USD 7.60 × 3 + 39.44 × 3 = USD 141.12, booked 25 Oct 05:12Z. Closed total for the
  whole closure (every booked host since 18:27Z on 24 Oct, the checks, validators and profiles hosts included): **USD
  163.84**. USD 0.096 per distinct decision task on the six hosts. Nothing tagged Job=jitter-s4 is running in either
  region (status and describe-instances, 25 Oct 05:13Z).

## 10. Open for rev 7 and the Codex S3 review
- §4: Σ by ML within each model (R1) and why; the "no model-independent direction of bias" sentence withdrawn; the
  strength-dependent latency recovery under the free Σ declared, with the three Σ-structure options for the recovery
  estimand (§5 above) — Codex to weigh, not decided here.
- §5: the union start recipe (R2) and the start-family report (§7); γ box, finite lifts, the acceptance rule (R3); the
  generalised-EM ascent step, the inner retry and the unguarded re-seed (D4); the EM loop's ≤ 8 steps and 1e-6 tol.
- §7.4 unchanged. §8 re-costed from the rev 7 benchmark (§9). §10: the recovery limitation.
- The recovery check of §5 (`recovery_check_em_oracle_scaled.txt`) was run under R1-R3 before D4; rerun it under the
  final fitter (20 min on 12 workers) before rev 7 is frozen, so that the S4 collapse is confirmed not to have been an
  under-finding artefact.
- `bench.py`'s cost table is superseded by `recost_rev7.py` (per fit); fold the per-fit accounting into bench.py at a
  chain boundary (never while a chain runs).
- Code hash discipline: every result json carries `code_hash`; the pre-D4 and final blocks differ in hash by design.

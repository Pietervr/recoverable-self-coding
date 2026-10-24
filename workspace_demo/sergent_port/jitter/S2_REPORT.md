# S2 report — development on development seeds (DESIGN_jitter.md rev 6 §0 stage S2)

Session R052 Entropy SI, 24 October 2026. DRAFT: the readings under the final (D4-patched) fitter are PENDING while
the chain runs (W2 sets 0-9 first, then T1, O1, then sets 10-24 of each, the summary and the benchmark re-cost).
Everything here is a development reading on development seeds — nothing feeds a gate or flag (§0: only S4b batches do).
What this report declares for DESIGN rev 7 and the Codex S3 freeze review: four defects found in S2 (D1-D4), their
evidence, the repairs, and what the repaired fitter reads on the three development settings.

Code: `jitter/{data,models,fit,decide,simulate,bench,s2,diagnose}.py`, tests `jitter/tests/` (82 tests over four files,
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

Gate (b) holds on this block (any POSITIVE at R = 10 would be the flag), but the UNRESOLVED sets are not noise: they
are the D4 mechanism, which is why the block was refit rather than continued.

### 4.2 Final fitter (D4-patched): W2 sets 0-9 — PENDING (chain started 24 Oct 13:02Z, about 20-25 min per set)
To be filled from `results/s2/decision/W2/set_*.json` (scratchpad `peek_sets.py decision W2`, `count_em_stops.py
decision W2`): primaries, set means and intervals, positives, nesting, EM steps, D4 counters (ascent steps accepted,
inner retries, re-seed chains run and selected, G REDUCED while B POSITIVE). If UNRESOLVED sets from single-fold
excesses persist under the patch, S2 STOPS here and records the case for a design decision (no further tuning).

### 4.3 T1 (two-state generators, POSITIVE = detection; power needs about 45/50) — PENDING
### 4.4 O1 (time-stretch, graded; POSITIVE = false call) — PENDING
### 4.5 Sets 10-24 of each — PENDING

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

## 6. Nesting and EM statistics
Pre-D4 block: 0/900 training nesting violations (the warm chains hold l(B) ≥ l(G) by construction); EM chains ended on a
NOT_CONVERGED inner solve 11× (G3+ 6, G2 4, B3+ 1) and on a small objective decrease 5× (G2 1, B2 2, B3+ 2). Final
fitter: PENDING (D4 counters per set from `peek_sets.py`).

## 7. Start-family usage (which start families were material) — PENDING
From the archived starts of the final W2/T1/O1 sets: for G3+ and B3+, how often the selected optimum came from each
family (design T_A/T_B recipes, smeared sm_A/sm_B at 20/40/80/120, lifted G2/B2 at 20/40/80, the G collapse, the warm
chain, the re-seed chain), and the gain over the best design start. This decides the FROZEN S3 recipe (§5: "starts
found material are added to the frozen recipe at S3 for all models alike").

## 8. §4 checks, basins, profile-start validation — PENDING
`s2.py checks --kind nodes` (33 scale nodes, 61 τ nodes, the 7-node prior rule against the archived default on W2 set
0), `--kind ranks`, `--kind smallspread`; `s2.py basins`; `s2.py profiles` (2- vs 4-start constrained optima on 100
datasets per family; the profile machinery now has finite lifts, so this validation is meaningful for the first time).

## 9. Cost
Rev 6: 165 s per participant-dataset (bench_20261024T044019Z: 1.69 s per decision-batch start). Under R1-R4: about
570 s (EM steps × 11-13 starts) — S4 about ×3.5, roughly 5,500-7,000 core-h before the warm chains. Under D4: PENDING
(the re-seed now fires on most graded folds — one extra G chain and one extra B chain each — and the inner retries
add solves; read from the per-set wall times and `bench.py --subject 10` at the end of the chain). The S4 number for
the owner's cap + venue decision (ledger row 24 in Unimog `rsc_t1_simulation_design.md` §12) comes from that benchmark.

## 10. Open for rev 7 and the Codex S3 review
- §4: Σ by ML within each model (R1) and why; the "no model-independent direction of bias" sentence withdrawn; the
  strength-dependent latency recovery under the free Σ declared, with the three Σ-structure options for the recovery
  estimand (§5 above) — Codex to weigh, not decided here.
- §5: the union start recipe (R2) and the start-family report (§7); γ box, finite lifts, the acceptance rule (R3); the
  generalised-EM ascent step, the inner retry and the unguarded re-seed (D4); the EM loop's ≤ 8 steps and 1e-6 tol.
- §7.4 unchanged. §8 re-costed from the D4 benchmark. §10: the recovery limitation.
- Code hash discipline: every result json carries `code_hash`; the pre-D4 and final blocks differ in hash by design.

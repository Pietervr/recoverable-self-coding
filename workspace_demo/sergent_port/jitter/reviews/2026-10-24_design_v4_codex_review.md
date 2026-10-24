# R052 — Codex re-review of DESIGN_jitter, revision 4

24 October 2026. Reviewed the whole revision 4, commit `78e348c4f2889a755b7461351f6c3799763b6a05`, SHA-256 `e1b4c326429847614a7492821646d2e376bbcd6a8aeb202d7b5842cddd3e1fda`, against all three preceding reviews. Re-read the inherited fitting, window, fold, model-comparison and BMS implementations. References below are to revision 4. Only this review file was changed in the repository. Small NumPy/SciPy and arithmetic checks were performed; no real-data fitting, benchmark, AWS operation, commit or push was attempted.

The central predictive comparison is substantially ready. The S4a/S4b reference split, E1 guard band, common-roster attenuation contrasts, explicit recovery gates, O1 continuation and O5 construction repair most of revision 3. The template gauge, mean matching, full-epoch generators, one-factor controls and conservative primary unavailable accounting stand. The remaining objection to building **exactly as written** is concentrated in the profile/identification contract. There are also bounded attribution, implementation and cost corrections below. These do not require another manuscript contribution or a larger general-purpose study.

## Findings ranked by severity

1. **High, blocking the claimed calibrated identification licence — the profile confidence set is not yet an operational interval, and R3 does not validate the 20 ms boundary.** The literal set of accepted grid points cannot cover an off-grid true value. Endpoint interpolation/bracketing, disconnected sets and the likelihood-ratio denominator need rules. R3 checks false `lower bound > 20` calls at true zero, while R4 checks coverage only at 40/80 ms. Neither checks that assertion at true 20 ms. The zero critical value is also estimated from the same recovery batch subsequently supplying its validation counts. DESIGN §§0, 6, 7.5, lines 18–23, 217, 308–334; answer 3.
2. **High for the stronger secondary wording — §9 does not explicitly carry the total-attenuation premise into “most,” and leaves the reference family unnamed.** The new contrasts correctly identify an incremental latency contribution after scale. Their specified signs can nevertheless pass when the total B advantage has increased. Require the preceding bridge/total-attenuation premise for statements about attenuation of the inherited advantage, and name the family whose recovery/detection flags are required. DESIGN §§6, 9, lines 203–210, 392–400; answer 2.
3. **Medium, preventing exact implementation of all promised outputs — several remaining branches are unspecified.** These include the secant correction's second point and out-of-domain behavior, unavailable pilot references, grid-to-interval rules, and the promised validated scale intervals. DESIGN §§4–7; answers 1, 3 and 5.
4. **Medium, blocking use of the quoted total as the launch manifest — constrained profile fits are priced as single starts, contrary to §5.** At four starts per constrained fit, the listed recovery profiles cost 10,000 rather than 2,500 core-hours. The correction batch and the sum also do not match their component counts. Development, several promised profiles/sensitivities and inherited BMS remain outside the enumerated total. DESIGN §§5, 8, lines 158–175, 356–379; answer 6.

## 1. S4a/S4b, binomial bounds and E1 acceptance

**Yes for the procedure-reference and lambda experiments.** Conditional on the S4a outputs, S4b is now a fixed-setting experiment: epsilon and both lambdas are frozen before its fresh seeds are drawn, no S4b result can retarget a lambda, and no pilot/certification batch supplies a final decision-gate count. Selection during S4a does not invalidate a binomial bound on an independent S4b count. The bounds remain pointwise and conditional on the fitted empirical generator population and frozen numerical procedure.

The corrected one-sided exact 95% bounds are 4.65598% for 1/100, 8.91963% for 4/100, and 80.11670% for 45/50. The primary and upper-bound licences are now separated appropriately. Unavailable epsilon or an uncertified E1 need not suppress an otherwise validated primary sign.

**The E1 guard band is sound for the frozen numerical epsilon.** Requiring the whole reference MC interval to lie inside `1.25 epsilon +/- 0.15 epsilon` puts it inside `[1.10, 1.40] epsilon`. Its lower endpoint is therefore already above epsilon; the additional lower-bound check is harmless. This avoids treating a reference estimate fluctuating around epsilon as known truth. Report the reference interval with the error count and describe the result conditional on reference certification. It does not establish boundary-uniform control, as the design now explicitly acknowledges. Epsilon is a frozen relative margin, so this experiment need not pretend it is an exactly known population benchmark divided by three.

Two small qualifications remain:

- Specify the MC interval formula and its available-set degrees of freedom. Also report both certification attempts if a correction is used. A nominal 95% interval selected by allowing two certification attempts is not automatically a 95% simultaneous guarantee that the accepted reference is on the stated side. If that confidence guarantee is intended, allocate the MC error across the two attempts, for example with 97.5% intervals at each attempt; otherwise label the intervals nominal and retain the reference-certification uncertainty in the claim. This is separate from the valid S4b binomial calculation.
- Freeze the actual correction formula: which two points determine its secant, what happens at zero/near-zero slope, and what happens when the proposed lambda leaves `(0,1]`. Define exact pilot hits and unavailable pilot references too. “One secant correction using the certified estimate” supplies only one of the two points. These cases should return an explicit search failure or follow a declared safeguarded update, rather than an implementer choosing a rule after seeing calibration results.

Finally, reconcile V2's “every S4b setting” with absent E1/T3 configurations. If certification fails, those secondary settings cannot be attempted at a defined lambda. Apply this set-level completion rule to the attempted §7.3 decision settings, explicitly excluding uninstantiated secondary settings while reporting their failure; retain conservative error counting for datasets actually attempted. That implements the intended separation without making an absent upper-bound experiment silently veto the primary licence or applying a CV set-level rule to full-data recovery fits.

The separate profile-critical-value experiment still does double duty as written; see answer 3. This does not reopen the repaired lambda seed split.

## 2. Attribution: D_tau, D_scale and RISE

**The paired contrasts now answer the right question.** On R6,

`D_tau = Delta_2 - Delta_3 = (G3-G2) - (B3-B2)`

and `D = D_scale + D_tau` exactly. Positive improvements in both families can no longer substitute for positive differential attenuation. `D_tau - D_scale` is the right comparison for which component contributes more in this declared, scale-first decomposition. The revision 3 counterexample is correctly included in the required branch-test specification; there is not yet executable jitter code here to test.

Make the §9 antecedent explicit. As independently listed, its latency/“most” conditions can all pass in this example, with precise participant intervals, in nat/trial:

- `Delta_0 = .010`, `Delta_2 = .030`, `Delta_3 = .020`.
- `D_scale = -.020`, `D_tau = +.010`, `D = -.010`.
- `D_tau - D_scale = +.030`.

Both incremental family gains can also be positive: `G3-G2 = .015`, `B3-B2 = .005`. Recovery, real detection and a simulated W1-to-W3 RISE can all pass independently. Latency then reduces the advantage **relative to the scale-only comparison**, but the final advantage exceeds the no-nuisance advantage. There is no positive total attenuation for latency to carry “most” of. A 20-participant construction with small score perturbations preserves all these interval signs.

For wording about attenuation of the inherited advantage, require BRIDGE (iii) POSITIVE and D POSITIVE in addition to the new component conditions. Alternatively, when those premises fail, say precisely that adding latency after scale reduced `Delta_2`; do not describe that as most of a total attenuation. State that the allocation is scale-first: with interactions, it is not an order-independent partition of causal responsibility.

“The reference family” occurs only in §9 and is not assigned. Name G or B before S5, or issue explicitly family-specific statements with both results shown. Do not choose whichever family passes recovery after seeing the real result. This is a specification choice; it does not require both families to pass by default.

The RISE rule is useful and appropriately limited to a sufficient simulation mechanism. Specify whether W1/W3 sets are independent draws from the same configuration pool or paired sets sharing their sampled configurations. Use the corresponding independent- or matched-proportion Newcombe construction; “common configurations” alone does not specify which uncertainty calculation to implement. The decoder-readout interpretation and the refusal to claim physiological causation are now appropriate.

## 3. R1–R4 and JITTER DETECTED

**They are now failable gates, but not yet a completely specified calibrated identification licence.** R1's same-fifteen requirement, R2/R3's attempted-replicate accounting, R4's acceptance threshold, primary-span/full-count matching and raw real estimates are substantial repairs. Unavailable profiles as real non-detections and reporting family-specific failures are correct. Passing R4 demonstrates the declared coverage tolerance at its tested settings; it does not establish nominal 95% coverage throughout the parameter range. Specify the recovery confidence-bound construction too: these pooled replicates have a fixed, potentially heterogeneous configuration roster, unlike §7.3's independently resampled participant sets; the target and uncertainty method should be explicit.

Three focused repairs remain.

**First, define an actual profile confidence set and its reported bounds.** Let the likelihood-ratio statistic be explicitly `q(s) = 2[ell_hat - ell_profile(s)]`, with the unrestricted maximum and each constrained maximum selected under declared convergence/start rules. The present phrase “the interval is the set of grid points not rejected” literally produces a finite set. A true value such as 47 ms is absent from that set regardless of the data. R4 at 40/80 ms cannot reveal this defect because both truths are grid nodes.

Specify how the endpoint brackets and the single bisection become a continuous interval: whether bounds use conservative outer brackets, an interpolation, or another declared rule. Define no crossing at 0/150, an empty accepted set, disconnected accepted components, and a constrained optimum exceeding the alleged unrestricted optimum. For a disconnected set, either retain the components and define the lower bound as their infimum, or use a declared conservative hull. Do not let a search for the component near the MLE discard an accepted zero point. Include off-grid-truth and disconnected-profile branch cases. These are essential to reproducing the `lower bound > 20` Boolean, not presentation details.

**Second, check the boundary actually used for the magnitude claim.** R3 at true zero estimates `P_0(lower > 20)` under its five zero-jitter challenges. It does not estimate `P_20(lower > 20)`, or validate exclusion of the composite region `s_tau <= 20`. R4 supplies no information there either. Thus a procedure could pass every current gate and still have poor coverage/excess detections near 20 ms. The small-spread numerical checks test integration and rank, not statistical coverage.

Add a prespecified true-20-ms detection/coverage check in each relevant family, using the existing 20 ms profile node and the same unavailable accounting, with its error ceiling and uncertainty declared. Report nearby small-spread behavior as needed if the boundary check reveals a problem; no dense new recovery factorial is necessary. Alternatively narrow the claimed licence to rejection of the tested zero-jitter explanations and describe the above-20 magnitude as an unvalidated nominal profile inference. The latter is weaker than the current claim of calibrated real profile bounds. Neither zero tests nor 40/80 recovery establishes uniform identification over all templates, and the design correctly disclaims that stronger ambition.

**Third, separate estimation of the zero critical value from its validation, or supply a different explicit statistical contract.** The 500 `(0, fitted)` recovery datasets per family both set the empirical 95th-percentile critical value and supply R2/R3 and profile-performance reporting. On a complete sample with distinct statistics, about 25/500 reject zero by construction. Since `lower > 20` requires rejecting zero, R3 at that setting is largely constrained by its own fitted critical value. Its usual fixed-rule validation interpretation therefore does not follow from these counts.

The straightforward repair is a separate calibration batch, frozen before S4b, and fresh S4b profiles/gates. Boundary calibration needs unrestricted F3 and reduced F2 fits for `q(0)`, not an entire 13-point profile. A properly specified order-statistic tolerance analysis could instead justify reuse for a calibration guarantee, but that is a different contract from independent final validation and is not supplied here. Freeze handling of unavailable calibration statistics and the empirical-quantile convention; neither an undefined LR nor an unavailable profile is a number from which to take a percentile.

With these repairs, the gates can support a conditional attempt to identify nontrivial readout spread. Failed identification should continue to leave an otherwise licensed predictive comparison reportable. There is no need to restore bias correction or demand accurate individual-trial latency estimates.

## 4. O1 and O5

**Yes: the two defects are repaired.** O1 now specifies a proper truncated stretch distribution, an explicit endpoint-value continuation and no amplitude renormalization. Apply the stretch to the continuous filtered template before the inherited 16-sample window averaging, as required by §4, and use the same operation in both batteries. Finite support no longer leaves its evaluations undefined.

O5 adds a resampled centred whole-trial residual to a deterministic marginal mean, with no second latent response. Algebraically, for level-k observations `y_j`, fitted marginal mean `m_k`, and centred residuals, its draws are

`m_k + (y_j - m_k) - mean_j(y_j - m_k) = m_k + y_j - ybar_k`.

That is the empirical within-level distribution recentered to the fitted mean. It retains the original trial variability once. The declaration that it may retain unknown state/shape variation, and is not known-truth graded data, is essential and now present.

Withdrawing the free-catch sensitivity also resolves that implementation defect. The catch diagnostics challenge the anchor without claiming to identify a separate free baseline and catch response.

## 5. Remaining exact implementation requirements

The primary likelihood, high-branch amplitude, normalization, score, logistic-start fallback and inverse-softplus construction are now sufficiently concrete. In addition to the preceding fixes:

- **`models.py` / `fit.py`, §§4–5:** declare how an unrestricted spread fit compares the reduced exact-zero model with the positive-spread model. A single ordinary L-BFGS-B call cannot change vector dimension when a box parameter reaches zero. Separate reduced-boundary fits and positive-spread candidates are one valid construction. Preserve the likelihood reduction at zero and the positive-spread starts; do not silently retain an unidentified Hessian or let a zero-gradient start be the only search for a positive optimum.
- **`fit.py`, §5:** the new starts are model-specific recipes, rather than guaranteed distinct numerical vectors: T_A and T_B can coincide on a constant trace. That is harmless if reported honestly. Freeze the perturbation distribution and which convergence checks apply to the EARLY rerun; acceptance must retain the projected-gradient and finite-value requirements. Map the four starts explicitly into a profile where s_tau is fixed, instead of overwriting different starts with one constrained vector and assuming four basins were explored.
- **`simulate.py`, §§7.4–7.5:** freeze the lambda edge cases and profile-calibration seed/failure rules above. The formula for primary-span response strength is repaired, but the referenced strength strata have no cutoffs or aggregation rules in §7.5. Define them if stratified results are promised; otherwise report the continuous strength variable and per-configuration results without calling them strata.
- **`decide.py`, §§6–7:** §6 promises both s_tau and s_g with “validated profile intervals,” but §7.5 defines a grid, critical values and coverage gates only for s_tau. Either limit that promise to latency intervals and raw scale estimates, or specify and cost scale profiles/calibration. Occupancy/high-amplitude profiles promised in §4 also need their scope and fitting recipe. Add the attribution counterexample in answer 2 and the profile/secondary-setting availability cases to the already improved branch-test list.

These are bounded contracts to freeze at S3. They do not call for replacing the repaired model families.

## 6. Compute manifest at 30 seconds per start

**No: the terms are much better enumerated, but the total is not complete or internally consistent.** The decision count of 1.84 million starts and recovery count of 320,000 starts are correct. Sharing the O1/O2 datasets between fitted families resolves the earlier 20-versus-22-setting ambiguity. The five-point pilot grid can be shared between the two targets, so its 160,000 starts are also correct.

Under §5's four starts per fit, the stated recovery-profile term is

`20 settings * 25 replicates * 20 configurations * 2 families * 15 constrained fits * 4 starts = 1,200,000 starts`.

At 30 seconds per start this is **10,000 core-hours**, not 2,500. If profiles are to use one warm start per constrained point, declare that exception, validate its ability to find the required maxima on development data, and benchmark it. It cannot be assumed under the current four-start rule. Likewise, 13 grid points plus up to two endpoint bisections means about 15 constrained fits for a connected interval, not `13 * ~2` as in the real-profile line. More components require a correspondingly defined refinement count.

The enumerated AWS components before profiles total 2.52 million starts: 40,000 epsilon, 160,000 pilot, 160,000 certification, 1,840,000 decision and 320,000 recovery. The inherited optimizer count is correctly `950 * 20 * 53 * 3 * 5 = 15,105,000` runs. At the supplied, unmeasured 0.14 seconds/run that is 587.4 core-hours, **before BMS**.

Consequently, those listed components sum to approximately:

- **24,087 core-hours** if each constrained profile fit is priced as one 30-second start;
- **31,587 core-hours** with the four starts required by §5;
- **32,921 core-hours** with four starts and one additional R=50 recertification per target.

The last increment is `2 * 50 * 20 * 80 = 160,000` starts, or 1,333 core-hours. Section 7.4 describes an algebraic correction followed by that fresh recertification; it does not describe the 320,000 extra starts in §8. If a second fitting batch really is intended, specify it; retaining 320,000 as an explicit contingency instead gives approximately **34,254 core-hours**. None of these component sums is the printed 26,700–29,400 range.

At the design's assumed USD 1.7 per 96-vCPU instance-hour, the four-start base plus the specified recertification range is about **USD 559–583 ideal**, or **USD 999–1,041 at 70% utilization with a 25% reserve**. These are arithmetic projections at the supplied rate, not current AWS quotes, and still exclude the following work:

- S2 development, numerical checks, extra start-basin searches and any added starts retained at S3;
- an independent zero-critical-value calibration batch and the threshold validation needed above;
- inherited BMS: 950 sets times 53 windows = 50,350 BMS calls, each defaulting to one million three-model Dirichlet draws in the unchanged code;
- scale and occupancy/high-amplitude profiles if retained, the additional unrestricted real full-data fits, and the declared covariance/floor/support/mean-law sensitivities.

For illustration, the real latency profiles alone are about `20 * 2 * 15 * 4 = 2,400` starts, or 20 core-hours, before their unrestricted real fits. Generator fits are 60 **model fits**, hence 240 starts under §5. These units should be made consistent throughout the real-data row too. The retry reserve is sensible but does not replace an enumeration of planned work.

Keep the measured-throughput and owner-budget step. Cost complete profile procedures, including all starts and retries, and include BMS in the inherited benchmark. No launch number or ledger change is warranted from this review's arithmetic. The USD 400 placeholder correctly remains insufficient.

Revision 4 can carry forward the repaired primary comparison. Before freezing the confirmatory implementation, finish the profile confidence-set and threshold-calibration contract, make the attribution premise/family explicit, and reconcile the remaining branches and cost units. The opportunity to identify jitter remains worth taking under those concrete conditions.

VERDICT: NOT FAVOURABLE: profile confidence-set and 20 ms identification-calibration contract incomplete; total-attenuation premise and reference family missing from stronger attribution wording; constrained-profile cost and remaining implementation branches unresolved

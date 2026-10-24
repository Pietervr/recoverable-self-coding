# R052 — Codex re-review of DESIGN_jitter, revision 3

24 October 2026. Reviewed the whole revision 3, SHA-256 `d60af80b74e2a916ea0cd57a5116b5e42c4547132150559a6233b63decb134f0`, against both preceding reviews. Re-read the inherited fitting, window, fold and comparison code and relevant manuscript methods/results. Section references below are to revision 3. Only this review file was changed in the repository. Checks used NumPy and elementary analytic calculations; no real-data fit, benchmark, AWS operation, commit or push was attempted.

Revision 3 makes substantial repairs. The template's avoidable scale gauge is removed; full-epoch generator fits supply a coherent 53-dimensional distribution; W1/W3/W4 now isolate the named factors; unavailable primary outcomes are counted conservatively; and predictive validity is separated from parameter recovery. Those repairs stand. The remaining objections concern a few concrete implementation and outcome-licensing rules, rather than the value or scope of the study.

## Findings ranked by severity

1. **Blocking for the upper-bound licence — E1 still lacks an unambiguous, independently validated boundary configuration.** Matching an estimated advantage to epsilon within one Monte Carlo SE does not establish which side of epsilon the true procedure reference occupies. The same R=100 sets appear to establish target attainment, trigger a lambda correction, and supply gate (e). That permits selection of the reported validation batch and does not specify the fixed-setting experiment to which the stated binomial bound applies. The literal `else` also rejects an already attained target. DESIGN §§0, 7.3–7.4; answer 3.
2. **High, blocking the latency-attribution sentence — positive latency improvements in both families do not show that latency attenuated the B advantage.** The required quantity is their paired difference, which can be negative while every currently required attribution flag passes. DESIGN §§6, 9; answer 4 gives a counterexample and the missing contrast.
3. **High, blocking a calibrated identification claim — interval performance is reported but cannot fail RECOVERY ADEQUATE or JITTER DETECTED.** The simulated boundary critical value addresses zero, whereas the detection statement uses a lower bound above 20 ms. Coverage acceptance, unavailable profiles/recovery fits, and application of the proposed bias correction to unknown real parameters remain undefined. DESIGN §7.5; answer 5.
4. **High for exact implementation — O1 evaluates the template outside its declared support without a continuation rule.** This is frequent on the whole-epoch generator, not a negligible tail event. DESIGN §§4, 7.3, 7.5; answers 2 and 6.
5. **Medium — the free-catch sensitivity retains an exact location gauge, and several smaller numerical/cost contracts remain incomplete.** These do not reinstate the primary comparison's old baseline asymmetry, but they prevent building every promised sensitivity exactly as written. The claimed gate-(e) binomial bound is also numerically wrong. DESIGN §§4–5, 7.3–7.5, 8; answers 3 and 6.

## 1. Primary-span template identification

**The new normalization and fixed visible coefficient remove the previous scale degeneracy. They do not guarantee identification of jitter for every allowed template.**

Write the window-averaged basis at zero shift as B0 and its column means as h. Predictions have the form `a(k) B0 c / (h^T c)`. With a visible reference coefficient fixed at `softplus(0)`, proportional rescaling of all visible coefficients is no longer available. Removing the four invisible coefficients from the zero-jitter parameter vector is correct.

A direct construction of the specified primary basis and the inherited 16-sample windows gave:

- 16 basis functions; exactly indices 0, 1, 14, 15, using zero-based indexing, invisible at zero shift.
- Rank 12 for the remaining zero-shift basis columns.
- Rank 16 for a numerical Jacobian of the five amplitudes and eleven free visible coefficients at a generic positive parameter point.
- Rank 16 for the stacked basis evaluated over all 31 latency nodes. This last check concerns the evaluation operator, not identification after marginalizing latency.

Thus the old unseen-mass/amplitude invariance is gone. Correct the explanation in §4: a shift-only coefficient has zero contribution to `m_vis`, so changing it does **not** change that normalizer or zero-shift predictions. The repair works because the visible gauge fixes scale, invisible coefficients are removed in the null models, and there is no longer a coefficient-sum constraint transferring mass between visible and invisible regions.

Three limitations remain substantive:

1. **At exact zero spread, the full model also has four unidentifiable shift-only directions.** Naming G3/B3 rather than G0/B0 does not identify them when the fitted spread is zero. The null profile must use the reduced parameterization or fix those irrelevant values deterministically. Do not interpret a full-vector Hessian at zero as full rank. With the fixed-node weights, spread derivatives also vanish at zero; projected-gradient convergence there is not evidence against a better positive-spread optimum.
2. **Near zero, the outer coefficients are effectively invisible.** Their relevant node weights decay exponentially in inverse spread squared. In a first-moment sensitivity check at parent spread 5 ms, the two outermost columns had norms about `6e-91` and the next pair about `1e-18`. These are not Fisher-information estimates, but demonstrate why an unweighted stacked-basis rank check misses the problem. Include small spreads between zero and the 10 ms grid spacing in the numerical checks; refinement only at recovered 40/80 ms values would not verify the small-spread limit. Report flat/unbounded profiles as such.
3. **There are allowed templates with no timing information at all.** Equal positive coefficients give a constant template by partition of unity, compatible with the fixed gauge. Every shifted window vector is then identical and the likelihood is exactly independent of `s_tau`. The maximum numerical discrepancy in this check was `2.3e-16`. Broad plateaus give the corresponding near-degeneracy. Nearly exponential shapes can also make a shift act approximately as a multiplicative scale; broadening the fitted template can compensate smoothing of its mean by jitter. Cross-window covariance and non-Gaussian structure can distinguish these effects generically, but the parameterization alone does not do so.

These are reasons to retain the recovery/profile programme, not to abandon the jitter question. The correct claim is identifiable scale/shape coordinates at generic informative templates, followed by conditional evidence about spread. Freeze a tie-break for the reference coefficient: the basis supports centred at 450 and 510 ms are equally near 480 ms. Either visible coefficient works.

## 2. Generator contract and stage circularity

**The principal generator defect is repaired, and S1–S5 is a defensible sequence.** One full-data, whole-epoch configuration per participant supplies the baseline, covariance and template. A synthetic participant has one distribution across all five folds, and the fitter re-estimates its training quantities. Primary fits generate nothing. Simulated processed vectors can enter the inherited likelihood-fitting stage after window averaging; they must not be filtered/averaged again.

Using empirical generator fits before freezing is not circular validation of the final contrast, provided the reported licence remains conditional on these fitted configurations and the real contrast is withheld until S5. It is not independent confirmation on a new human sample. The declaration about block labels preserving counts rather than stochastic dependence is accurate. Include the separate B0 generator fits required by §7.4 in the S1 manifest as well.

**O1 nevertheless does not define a distribution exactly as written.** For a whole-epoch sample at 1290 ms, its transformed argument exceeds the template's upper endpoint 1440 ms when

`zeta > log((1440-240)/(1290-240))`.

Under the specified SD .25 this has probability **29.66%**. Other stretches also leave the lower endpoint. An open-clamped spline basis specifies its values on the base interval; it does not choose a scientifically appropriate continuation outside it. Zero extension, clamping, spline extrapolation and extending/refitting the support produce different generators. State the continuation explicitly, including endpoint behavior, and use it in both decision and recovery O1. Unbounded stretch cannot be handled merely by the finite latency support extension. This also matters because O1 helps license the jitter-identification claim.

For O5, define whether residuals are about the marginal fitted mean or a latent-conditioned fitted trace, and whether they are centred within level before resampling. Adding a fresh latent response to residuals that already retain that variation can double-count it. The declaration that O5 is a covariance challenge rather than known graded truth is appropriate and should remain.

## 3. Gates, unavailable outcomes, epsilon and the lambda path

**The primary unavailable-outcome accounting is now conservative and coherent.** Counting unavailable sets as errors in (b)/(e), as non-detections in (c), retaining every attempted set, and applying the same minimum-16 available-case rule in simulation and reality repairs the previous loophole. V2 is partly redundant at the stricter error-gated settings but still useful elsewhere. Recovery is correctly excluded from primary predictive VALIDITY.

The bounds for 1/100 and 45/50 are correct: one-sided exact 95% upper/lower limits are **4.65598%** and **80.1167%**. However, the corresponding upper limit for **5/100 is 10.22534%, not 9.9%**. If a ceiling of 10% is intended, at most 4/100 is sufficient, with upper limit 8.91963%. Alternatively retain 5/100 and declare its actual precision. Neither choice certifies the nominal 2.5% tail error of a calibrated two-sided 95% interval. The tolerated validation ceiling and nominal interval label must be distinguished.

**The epsilon estimand is now acceptable as a declared relative benchmark.** It integrates finite-training refitting and the participant resampling procedure rather than pretending fitted predictors are an oracle. R=50 with its MC uncertainty and a positive lower-bound requirement is a reasonable starting precision, conditional on the benchmark's observed stability. It is not a biological minimum effect.

Complete the unavailable-set rule for that benchmark: when a set has fewer than 16 usable B0/G0 participants, its group mean is undefined. Do not silently omit such sets from the benchmark/SE. Specify a fail-to-epsilon-UNAVAILABLE rule or explicitly define a conditional estimand and reproduce that conditioning throughout. The same issue affects procedure-reference estimation along the lambda path. Under the current V1 rule, unavailable epsilon also makes (e) unevaluable and therefore makes the primary result NOT LICENSED; it does not merely suppress one secondary field. Branch tests should enforce that consequence unless the design explicitly changes it.

**Scaling all amplitudes by one lambda is an acceptable path, but its search and validation sequence need repair.** There is no guaranteed monotonic finite-training advantage along it. Freeze a bracketing/interpolation rule, selection among multiple crossings, and the outcome when the pilot grid does not bracket the target. Call that outcome failure of the declared search; it need not prove that no lambda anywhere on `(0,1]` could attain the target.

For E1 specifically:

- An estimate within one MC SE of epsilon neither establishes a boundary reference nor excludes a true mean below epsilon, where BOUNDED can be correct. Stating the SE does not turn those outcomes into known errors. Predefine target precision and account for reference uncertainty, including its side of epsilon, when interpreting gate (e).
- Separate path calibration/correction draws from the final fixed-setting validation draws. Freeze epsilon and the attained E1/T3 configurations before drawing the batches supplying the final error/detection counts. Do not use an R=100 batch both to correct lambda and to retain/discard a gate result according to estimated target attainment. If a correction is allowed, specify fresh seeds, what gets reported, and which independent batch is the final denominator.
- Rewrite the success/correction/failure branches. Literally, the present sentence says to declare UNREACHABLE when the first estimate is already within its MC SE of the target. It also omits the acceptance test after correction.

S4 can contain an explicitly ordered reference-calibration substage followed by independent final validation; a new scientific study is unnecessary. With these repairs, gates (b)/(c)/(e) support a licence at the declared frozen settings, conditional on the empirical generator population. One E1 point and one strong T1 alternative do not establish uniform interval coverage or least-favourable error control along the whole path, and §9 must not imply that stronger result.

## 4. One-factor controls and attribution

**W1/W3/W4 are now genuine one-factor controls.** They keep `a,T,mu0,Sigma` fixed and change only latency or scale. W2 is the fitted joint-variation setting. The inherited run definition, ties and no-run value are now usable. Common configuration draws across the controls would improve precision, but are not necessary for their distributional interpretation.

The revised bridge and attenuation conditions fix the previous inference from a negative primary sign alone. The simulation-reproduction and tested-distribution wording also fix the earlier overreach. An unresolved residual must still be described as unresolved, even when a positive D establishes attenuation.

**The remaining latency-attribution rule is insufficient.** Put `Delta_j = S_Bj - S_Gj`. The attenuation specifically obtained by adding latency after scale is

`D_tau = Delta_2 - Delta_3 = (S_G3-S_G2) - (S_B3-S_B2)`.

Requiring each term on the right to be POSITIVE does not require their difference to be positive. For example, all values below can have arbitrarily precise participant intervals, in nat/trial:

- Initial B0-G0 advantage: .010.
- Scale improvements G2-G0 = .006 and B2-B0 = .002: residual advantage .006.
- Latency improvements G3-G2 = .001 and B3-B2 = .003: final advantage .008.

The total attenuation is positive (.002), both incremental latency gains are positive, and jitter can be well recovered/detected with a positive W3 mechanism result. A margin above .008 can also make the final advantage BOUNDED. Nevertheless, **latency increased the B advantage by .002**; scale produced the attenuation. Every currently named attribution requirement can pass in this example.

Add a paired participant interval for `D_tau` on the intersection roster with all four required scores, with the same minimum-16 rule. Require it to be POSITIVE before saying latency carries attenuation. If saying latency carries most of the attenuation, predefine that stronger fraction/comparison too. The analogous scale component is `D_scale = Delta_0 - Delta_2`, and `D = D_scale + D_tau` on one common roster. G2-G0 alone likewise cannot establish scale's contribution to attenuation of the *between-family* contrast.

The W3-vs-W1 result establishes a sufficient simulation mechanism, not which component reduced the real contrast. Define what counts as a rise in that call rate, including uncertainty, before using it as a Boolean attribution condition. Even with all these checks, the supported wording concerns a decoder-readout latency term; it does not uniquely identify physiological latency as the cause.

## 5. RECOVERY ADEQUATE and JITTER DETECTED

**The point-recovery design is substantially improved and appropriate for a conditional attempt to identify spread.** The fixed roster, R=25 per configuration, same fifteen passing configurations at both 40/80 ms, family-specific outcomes, full-data training size, five zero-jitter challenges and real-data detection flag address the previous central omissions. No accurate individual-trial latency estimate is needed to identify a population spread at this resolution.

Three contracts remain necessary before these flags license identification:

1. **Make interval adequacy capable of failing the identification licence.** Currently excellent point recovery plus poorly covering intervals can pass RECOVERY ADEQUATE and then generate JITTER DETECTED. Checking coverage only for reporting does not calibrate the bounds used for detection. Prespecify an acceptable coverage/false-detection criterion and its uncertainty, using the existing replicated configurations where possible. The simulation-calibrated critical value at zero is appropriate for the null's nonregularity, including nuisance directions absent at zero; it does not itself validate the assertion `lower bound > 20 ms`. Check/calibrate that threshold, or explicitly limit the interval claim. Away from zero, estimated scale or occupancy can still lie at boundaries, so chi-square validity cannot simply be presumed.
2. **Define failed recovery/profile outcomes.** Five hundred attempted point estimates are not necessarily five hundred available estimates. Unavailable point fits cannot silently disappear from bias/RMSE or the false-jitter denominator; unavailable intervals cannot silently disappear from coverage. Set minimum completion rules and conservative failure handling for RECOVERY ADEQUATE. A real unavailable profile must not count toward the required ten detections. State the span used for the full-data real profiles and synthetic recovery; matching trial count alone is insufficient if one uses 16 windows and the other 53.
3. **Do not apply an undefined simulation bias correction to real data.** The proposed correction depends on the true setting's median bias, but the real spread/scale setting is unknown. A corrected point estimate also has uncertainty from estimating that correction, and an RMSE is not a calibrated confidence interval. Either retain bias/RMSE as simulation diagnostics and report raw real estimates with validated profile intervals, or define and validate a mapping from observable fits to a correction. The first option is simpler and fully compatible with the main question.

Also compute response-strength strata on the intended span. Whole-epoch generator amplitudes are normalized by a different visible mean from primary amplitudes. If the strata are meant to describe primary timing information, convert them using the template's primary visible mean rather than treating the two `a(5)` values as interchangeable.

With these repairs, ADEQUATE plus DETECTED can support identification of nontrivial parent spread for the specified readout model and tested conditions. They cannot establish global identifiability for all templates, exclude every shape/noise explanation, or choose the real generating family. Report both families' flags and define which are required for a family-specific attribution. Failure should withhold identification wording while leaving an otherwise validated predictive comparison reportable.

## 6. Remaining exact implementation requirements and cost

The primary whitened likelihood, high-branch `a/A`, common second-moment law, floor declaration, parameter counts, per-trial score and all-three convergence acceptance are now sufficiently concrete. Preserve those repairs. The following bounded changes are still needed in addition to findings 1–4:

- **`models.py`, free catch (§4):** as written, only G explicitly frees `a(0)`, while B uses it in `m_H(0)=a(0)/A(0)`. Say explicitly whether B's common mean amplitude is free too; otherwise its high catch response remains zero. More fundamentally, G0 with free baseline and all catch/sound amplitudes has the exact invariance `mu0 -> mu0+d*T_tilde`, `a(k) -> a(k)-d` for all k, including zero, wherever positivity is preserved. Its distributions are unchanged. A free W-vector baseline plus a free catch signal does not identify both. Supply an independent baseline anchor or another identifiable sensitivity construction; merely declaring the baseline common to both families does not remove this gauge. This is a sensitivity defect, not a renewed primary mean-matching objection.
- **`fit.py` (§5):** convert NNLS coefficients with inverse softplus, after flooring and a rescaling that satisfies the fixed reference coefficient; taking their logarithm is not that inverse. Specify fallback/positive-slope treatment for separated or negative-slope logistic starts. Projecting the four nuisance recipes into G0/B0 gives identical starts, and into single-nuisance models gives duplicates: describe these honestly and retain additional distinct basins if development finds them material. Define how a finite early-stopped fit with fewer than five iterations can meet the five-iteration acceptance requirement.
- **`simulate.py` (§§7.3–7.5):** freeze O1 continuation, O5 residual construction, reference-estimation failures and the calibration/final-validation seed split. Specify profile-grid/refinement and critical-value simulation counts sufficiently to reproduce intervals and cost them. Whole-epoch B0 reference fitting is a third generator fit, not a primary-fit substitution.
- **`decide.py` (§§6, 9):** add `D_tau`/`D_scale` and their roster rules; specify availability thresholds for all secondary contrasts and profiles; distinguish unavailable primary scores, unavailable epsilon and unavailable upper-bound decisions. Add branch tests for the positive-total-attenuation/negative-`D_tau` counterexample, successful initial lambda targeting, failed/corrected targeting, and unavailable recovery/profile results. Keep the existing exact-zero and sub-epsilon-positive cases.

**Cost (§8):** 1.84 million decision starts and roughly 15.1 million inherited optimizer runs are correct. The 320,000 recovery starts assume eighteen family-specific factorial settings plus two shared O1/O2 settings. Say explicitly if both fitted families are tested on the same graded O1/O2 datasets; the literal “settings per family ... plus O1 and O2” instead gives 22 settings, 352,000 starts and about 2,933 core-hours. The README provides an inherited wall-time estimate; translating it into core time still needs the specified benchmark. The approximately 20,200 core-hour total does **not** yet enumerate the repeated constrained optimizations for recovery profiles, calibration of their critical values, final independent reference/target certification, or a possible corrected-path batch. A single profile timing is not a total until the number of profile points/refinements and calibration replicates is fixed. Include those terms in the measured launch manifest and approval number. The acknowledgement that the USD400 placeholder is insufficient at the stated utilization is correct; no current AWS quote was checked in this review.

The requested contribution remains one coherent human reanalysis with a mechanism battery. The old gauge, missing 53-dimensional generator, confounded controls and unavailable-count loophole should not be reopened. A focused revision can close the remaining boundary-calibration, attribution, interval and continuation contracts before freezing the implementation.

VERDICT: NOT FAVOURABLE: E1 boundary-reference and validation-selection contract incomplete; latency attribution lacks the paired incremental attenuation contrast; jitter intervals lack an acceptance/completion rule; O1 template continuation undefined

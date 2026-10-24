# R052 — Codex re-review of DESIGN_jitter, revision 5

24 October 2026. Reviewed the whole revision 5, commit `0ddac9898cd5da4a95009d433d07fbd79f2b8dd7`, SHA-256 `6db6c3e6f11317cb6fca6f39fd6bf7c7f4a9e787ec021f766b90f3485ba28bdb`, against all four preceding reviews. Re-read the inherited likelihood, window, fold, scoring and BMS code. Section and line references below are to revision 5. Only this review file was written in the repository. Checks were analytic and arithmetic; no data fitting, benchmark, live infrastructure action, commit or push was attempted. Prices below are the design's assumptions, not verified current quotes.

**The substantive design is ready for implementation with bounded conditions.** The separate c₀ calibration, independent R5 experiment, declared interval hull, attribution premise, fixed reference family G and validated profile-start exception are substantial repairs. No new factorial study, alternative model family or manuscript contribution is needed. Four residual contracts below should be settled before S3; they affect the fallback wording, missing-fit branches and launch manifest rather than the rationale for attempting jitter identification.

## Findings ranked by severity

1. **High for the narrower identification claim — ADEQUATE-ZERO-ONLY permits a different rejection event from the one R3 validates.** R3 measures `lower bound > 20`, whereas §§7.5/9 permit rejection of the tested zero-jitter explanations whenever the real hull merely excludes zero. These are different events. The own-batch c₀ does not supply independent zero-exclusion validation under all five zero-jitter challenges. DESIGN §7.5, lines 355–377; §9, lines 465–466. Use the R3 event for this fallback, or validate zero exclusion separately using the profiles already computed. Answer 1.
2. **Medium for attribution with unavailable fits — the new premise still needs a common-roster bridge.** D and its components use R6, but BRIDGE (iii) has its own availability rule. A POSITIVE bridge on twenty participants can coexist with a negative initial contrast on the sixteen supplying D. Require a POSITIVE Δ₀ interval on R6 for the attenuation narrative, and identify that roster in the residual comparison. DESIGN §6, lines 221–233; §9, lines 453–463. Answer 2.
3. **Medium, preventing exact implementation of every branch — reduced-to-positive profile starts, failed direct certification, and denominator changes during endpoint refinement need rules.** These are finite implementation choices, not further statistical redesign. DESIGN §5, lines 157–184; §§7.4–7.5, lines 317–357. Answers 3–4.
4. **Medium for the launch manifest — 80 starts no longer implements the specified four-model decision batch.** G3/B3 now require G2/B2 boundary candidates, in addition to the expressly listed G0/B0. The printed sums are arithmetically correct for their listed terms, but those terms omit required candidates. DEVELOPMENT profile-start validation also needs its own count. DESIGN §§5, 7.1, 7.3, 8. Answer 5.

## 1. Profile intervals, c₀, R3–R5 and the narrower fallback

**Yes in statistical construction, subject to the numerical branch closure in answer 4.** The reported object is now a continuous interval rather than a finite collection of accepted nodes. Taking the outer bracket endpoints after one bisection gives a reproducible conservative grid-based hull: if the midpoint is rejected, move the rejected endpoint to the midpoint; if accepted, retain the existing rejected endpoint. Preserve an accepted zero and use 0/150 at accepted domain endpoints. Disconnected accepted components are hulled, and an empty or unavailable profile cannot generate a real detection.

This is conservatism with respect to the sampled crossings. A finite grid does not prove the absence of unobserved accepted islands between rejected nodes; do not describe it as an exact inversion over every real-valued spread. The fresh-seed validation checks the actual frozen grid-and-hull procedure, including that approximation. Off-grid coverage is now a meaningful event, unlike revision 4's literal accepted-node set.

The **own S4a batch for c₀**, type-7 quantile, unavailable threshold and freeze before S4b remove the previous reuse defect. In its implementation, form the nonnegative statistic from the selected objective: `q(0) = 2[max(ell_reduced, ell_positive) - ell_reduced]`. A positive candidate worse than the reduced fit must not produce a negative calibration statistic. The two candidate fits suffice for this calculation; a complete calibration profile is unnecessary.

R3 now independently tests the declared detection event at zero, R4 tests coverage at 40/80, and R5 independently tests false above-20 calls and coverage at true 20. Together with R1/R2 and conservative unavailable accounting, these constitute a **failable, conditional identification licence at the tested settings**. They do not certify uniform coverage, a nominal 95% coverage rate, or control over every spread in the composite region `s_tau <= 20`. The document's fixed-setting limitations are essential. Keep pooled fixed-roster results and per-configuration results distinct; the former do not give each participant an individual error guarantee.

**ADEQUATE-ZERO-ONLY is a useful fallback, but its current zero-exclusion guard is too permissive.** Consider a zero-jitter O1 configuration for which the procedure repeatedly returns `s_hat = 10`, with hull `[2.5, 15]` ms. R2 records no estimate above 20; R3 records no lower bound above 20. Both gates can pass even if this hull falsely excludes zero on every replicate. Recovery and coverage at 40/80 can pass independently, while R5 fails. The present fallback would then authorize the very rejection that was never validated under O1. Calibration of c₀ at `(0, fitted)` does not repair this O1 counterexample.

The smallest repair requires no extra fitting: **under ZERO-ONLY, permit the tested-zero rejection wording only for the same real `lower bound > 20` event validated by R3**, while explicitly withholding calibrated above-20 magnitude wording because R5 failed. Alternatively, add a separate zero-exclusion gate, with attempted-replicate accounting and uncertainty, at all five zero-jitter settings using the existing profiles. Merely excluding zero is insufficient under the current gates. Add this counterexample to `decide.py`'s branches.

## 2. Attribution and §9

**The new sign logic, reference family and order declaration are correct.** The rev 4 counterexample now fails the ATTENUATION PREMISE because D is negative. Requiring that premise for both “part” and “most,” fixing G before S5, and using `D_tau - D_scale` for “most” close the named defects. Independent W1/W3/W4 draws support the independent-proportion Newcombe construction. The RISE remains evidence of a sufficient simulation mechanism, not evidence that the real latency term caused the inherited result.

One availability case remains. BRIDGE (iii)'s positive interval need not describe R6. For example, let the initial Δ₀ values be −0.0001 for the sixteen participants in R6 and +0.1 for four participants missing later fits. The twenty-participant bridge mean is 0.01992, with a 95% t-interval approximately `[0.000694, 0.039146]`: POSITIVE. On R6 let Δ₂ = −0.0003 and Δ₃ = −0.0011. Then:

- D = +0.0010;
- D_scale = +0.0002;
- D_tau = +0.0008;
- D_tau − D_scale = +0.0006.

Arbitrarily small participant perturbations retain all these interval signs. The recovery, detection and RISE flags can pass independently. Nevertheless, there was no positive initial joint advantage in the participants whose attenuation was measured. The bridge and D describe different cohorts.

Keep the broader BRIDGE field for continuity, but compute **Δ₀ on R6 and require its interval to be POSITIVE for the attenuation premise**. Report the corresponding Δ₃ on R6 when describing its residual; the separately defined primary interval may still use its own available roster. This is one additional summary from existing scores, not additional fitting. With that restriction, §9's attenuation claims follow the declared flags and remain a scale-first account of the decoder readout.

## 3. Zero-boundary construction and two-start profiles

**Yes: comparing a reduced exact-zero fit with a separately searched positive-spread candidate is sound.** It avoids pretending that one optimizer call changes dimension at zero and retains a search for positive spread when the fixed-node derivative is nearly flat. For G3 the reduced candidate is G2, and for B3 it is B2; G0/B0 are the reduced candidates for G1/B1. Preserve that distinction in code and accounting.

The numerical parameter domain is effectively `{0} union [2,150]` ms, rather than the entire continuous interval `[0,150]`. Calling the 2 ms edge a numerical floor, checking small spreads in S2 and reporting edge hits is appropriate for a 20 ms resolution claim. Do not silently describe an edge hit as a well-resolved positive estimate or infer identification of 0–2 ms variation.

The **two-start constrained-fit exception is acceptable** because S2 must compare it with four starts at every development profile grid point, and failure restores four starts before freezing and re-costing. This validates a numerical shortcut, not global optimization or a chi-square theorem; the independent recovery gates still validate its inferential consequences. Check material objective discrepancies on the LR scale as well as the declared relative-objective tolerance.

Complete the warm-start mapping when the unrestricted solution is REDUCED. It has no shift-only coefficients to copy into a positive-spread profile. Freeze a deterministic lift, for example retaining all fitted visible coordinates and supplying the missing coefficients from the declared floored T_B initialization. At zero, project the positive vector onto the reduced coordinates. Also resolve “G0/B0 (and every reduced candidate)” versus the separate G2/B2 nuisance recipes: the reduced candidate of G3/B3 still has free scale. Give that candidate the corresponding G2/B2 recipe and cache the same reduced fit wherever it is needed. Otherwise its scale initialization and the permitted reuse are ambiguous.

## 4. Remaining exact implementation branches

The main `models.py` likelihood, support, gauge, averaging, covariance and occupancy construction now stand. The EARLY rerun, raw scale estimates, continuous strength covariate, O1 averaging order and absent-E1/T3 handling also close their prior findings. Beyond answers 1–3, freeze these branches:

- **`simulate.py`, §7.4:** a pilot “exact hit” means the target lies inside its MC interval and selects that lambda directly. It need not have a bracketing pilot pair. If its fresh certification fails, the specified secant correction refers to bracket endpoints that may never have existed. Multiple interval hits also lack a tie-break. Specify selection among hits and either supply a declared correction pair or return UNCERTIFIED when a direct hit has no usable bracket. An UNAVAILABLE certification reference has no `r_cert` for a secant; it needs an explicit failure outcome. Likewise specify the precision-failure case `r_cert == target` with an interval too wide to certify. These require no new search or batches by default. The 97.5% per-attempt allocation is appropriate for the two nominal MC intervals; it does not make a t interval exact for arbitrary set-score distributions.
- **`fit.py` / `decide.py`, §7.5:** raising `ell_hat` changes every q value and can change which points are accepted. Recompute all previously evaluated q values against the final reference, including q(0). This must also cover a better optimum discovered at an endpoint midpoint. For example, `ell_hat=0`, `ell_prof(20)=-2.5`, `ell_prof(30)=-1`, `ell_prof(40)=0` initially accept 30 and reject 20. If the midpoint at 25 attains `ell=1`, then 30 changes from `q=2` to `q=4` and becomes rejected. The previous endpoint bracket is obsolete. Freeze either a deterministic repair/restart rule with a corresponding cost allowance, or declare the profile UNAVAILABLE when a reference increase invalidates an already refined bracket. The latter preserves the fifteen-constrained-fit cap. Never retain stale acceptance labels. An unavailable midpoint fit must likewise make the profile UNAVAILABLE.

These branch choices, the warm-start lift and the common-roster/zero-only cases belong in S3's executable tests. After their closure there is no remaining structural obstacle to implementing the four modules. The opportunity to identify nontrivial jitter remains worth taking; failure of identification must continue to leave an otherwise licensed predictive comparison reportable.

## 5. Compute manifest

**The printed additions and unit conversions now check, but the manifest is not yet complete for §5's candidate procedure.** The listed base terms sum to 3,404,000 starts. At 30 seconds/start, plus 15,105,000 inherited runs at 0.14 seconds and 50,350 BMS calls at one second, this is 28,968 core-hours. Adding 160,000 recertification starts and 780,000 extra profile starts gives 36,801 core-hours. Thus the printed 29,000–36,800 range and its spot projections are consistent with the listed inputs. The profile term itself now correctly charges two or four starts per constrained point.

However, a decision batch expressly fitting G0, B0, G3 and B3 needs these six distinct candidate optimizations per fold:

- G0 and B0;
- G2 and B2, the exact-zero boundary candidates for the full models;
- positive-spread G3 and B3.

At four starts each and five folds, that is **120 starts per participant-dataset**, not 80. The reduced G3 candidate cannot be reused from G0 because it must optimize scale. The same issue propagates to the lambda pilots and certification rows insofar as they use the declared four-model batch.

Keeping that batch literally, and caching reduced candidates in the all-eight-model recovery fits, changes the AWS terms to:

- ε: 40,000, unchanged;
- pilots: 240,000;
- initial certification: 240,000; optional recertification: another 240,000;
- c₀: 8,000, unchanged, explicitly the positive/reduced pair;
- S4b decision: 2,760,000;
- recovery: 416,000, unchanged with explicit caching;
- profiles: 780,000 or 1,560,000, unchanged under the fixed refinement budget.

The resulting base is **4,484,000 starts / 37,968 core-hours including inherited fitting and BMS**. Four-start profiles plus recertification give **5,504,000 starts / 46,468 core-hours**. At the supplied spot assumption these are approximately **USD 672–823 ideal**, or **USD 1,201–1,469 at 70% utilization plus 25% reserve**, before development. The corresponding on-demand projections are about USD 2,096–2,565 ideal, or USD 3,743–4,581 with that utilization/reserve factor. This is a workload correction, not evidence of an actual measured overrun.

There is a bounded economy available: **where only Δ₃ is required, omit G0/B0 and explicitly schedule G2/B2 plus the positive G3/B3 candidates**. That implements the same selected G3/B3 procedure in 80 starts. It requires amending the manifest's model list, not weakening the zero-boundary search. ε still needs G0/B0. Do not retain the current four-model list and call its missing candidates free.

For S1, G3/B3/B0 require five candidate fits per participant including G2/B2: 400 starts, rather than 240. The real all-eight-model and recovery rows can retain their existing counts if shared reduced fits use the same frozen recipe and data. S2's approximately 120,000 starts are the three basic 80-start batches alone: its promised profile-start comparison is additional. If performed on all 1,500 development participant-datasets in both families, thirteen grid points at four starts require 156,000 profile starts, even when the two-start subset is reused within those four. A smaller declared validation subset would have a different count; freeze and price its scope. Numerical/start-basin experiments remain development work as well.

Keep the measured-throughput benchmark, complete-dataset concurrency measurement, budget/headroom check and protected reduction order. The USD 400 placeholder remains unmet. Once the candidate scheduling and S2 profile-validation scope are explicit, the manifest can be costed from measured rates without changing the study's main scientific question.

VERDICT: FAVOURABLE WITH CONDITIONS: align ZERO-ONLY wording with its validated rejection event; evaluate the attenuation premise on R6; close reduced-start, certification and profile-reference branches; reconcile candidate-fit scheduling and development costs before S3

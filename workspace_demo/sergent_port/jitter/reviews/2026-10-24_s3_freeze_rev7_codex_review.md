# R052 — Codex S3 freeze review: DESIGN_jitter revision 7 and S1/S2

24 October 2026, evidence cutoff 18:02Z. Reviewed RSC `d2eaac943ef94e8b2720b05faf4b4b0ddeee6c90`.
The five-module code hash is `ca25a7be9e9f`; the final W2 records carry `a45a07d92b82`.
The intervening change to those modules is D5's generator-only change in `fit.py:990–1000`.
Read the whole design and report, the requested implementation, tests, and evidence records.
References are relative to `workspace_demo/sergent_port/jitter/`; compact JSON records occupy line 1.
Only this review file was written in the repository. No commit, AWS action, or S4 draw was made.
New untracked S4/AWS files appeared during review; they are outside this reviewed commit and are not certified here.

**Verdict: NOT FAVOURABLE for freezing this hash.** The repaired comparison is worth pursuing,
and I recommend retaining the free-covariance recovery experiment. The blockers concern executable
contracts and unfinished S2 verification, rather than a demand for another statistical model.
Closure order is in Q8. An AWS venue/budget go does not itself close S3.

Verification: all four supplied test programs were run with `../../t1_access/.venv/bin/python -B tests/<file>.py`.
All **81 tests pass**: fit 18, models 24, decide 29, simulate 10; each program exits 0 with `ALL OK 0`.
Additional counterexamples below were executed in memory, without changing source or result files.

## Q1 — Fairness, covariance, and the estimand

1. **NON-BLOCKING — The statistical construction is defensible; make the changed prediction target explicit.**
   The covariance update uses the posterior residual second moment, including the low branch and catches
   (`models.py:548–604`). Training-only baseline and starting covariance are supplied by
   `data.py:201–225,260–266`; held-out scores use the fitted model's own covariance and its log determinant
   (`fit.py:743–747`; `models.py:535–545`). I found no held-out information used to choose starts or chains.
   B's collapse/warm chain respects the G subfamily, and the reverse reseed helps G search the B basin
   (`fit.py:527–611`). Unequal numbers of solves are not, by themselves, an out-of-sample advantage;
   training selection can also hurt generalisation. This is not a proof of unbiased finite-procedure scores.

   The algebraic field `mean(S_B3-S_G3)` is unchanged, but its fitted densities have changed substantively.
   It now compares complete predictive models with separately fitted noise, including different predictions
   for held-out catches. A gain is not isolated evidence about occupancy conditional on one fixed noise model.
   Add that sentence to §6 and the §9 wording; qualify the header's unqualified “estimand unchanged”
   (`DESIGN_jitter.md:17,94–117,275–277,581–585`). The decomposition also includes covariance re-estimation
   after each nuisance addition. §§4/10 already acknowledge much of this; no new experiment is required for this clarification.

2. **BLOCKING — An EM fit changes density after a JSON/disk-cache round trip.**
   `FitResult.to_json` saves only the covariance log determinant, and `from_json` explicitly restores `wh=None`
   (`fit.py:366–387`). `FitCache.get` then accepts it and `score_heldout` silently uses the starting covariance
   (`fit.py:449–456,743–747`); warm chains are also disabled when that covariance is missing (`fit.py:529`).
   Executed counterexample: one 16-window catch observation equal to its baseline, starting covariance I,
   fitted covariance 2I, identical theta. Fresh score = −20.2481939758; reloaded score = −14.7030165313 nat.
   This is a 5.5451774445-nat change with no refitting or data change.

   Moreover, the cache key omits code hash, EM mode, and supplied whitening (`fit.py:441–444,465–471`), so
   an old/fixed-noise cache can bypass the intended construction. The existing round-trip test checks theta
   and training likelihood, not held-out density (`tests/test_fit.py:212–223`). Preserve/reconstruct the full
   fitted whitening and validate cache identity, or refuse persistent EM caches and explicitly invalidate old
   caches. Add a density-preserving round-trip test. S2 uses memory-only caches (`s2.py:110`), so I have not
   attributed the archived W2 results to this defect.

3. **BLOCKING — `run_start` relaxes criterion (ii) beyond the EARLY exception declared in rev 7.**
   `accepted()` accepts any best stationary endpoint if another attempt found nothing better
   (`fit.py:306–314`), without requiring that endpoint to have fewer than five iterations.
   The design permits this exception only for such an early endpoint (`DESIGN_jitter.md:244–253`).
   Executed mock: two finite, gradient-zero, ten-iteration attempts, both assessed NOT_CONVERGED because
   their five-iteration histories fail (ii), return `CONVERGED`, `early=False`.
   Retain the best stationary endpoint, but apply the no-better-retry exception only to an EARLY endpoint;
   otherwise require (ii). Test this late-failure case and rerun affected development checks under the corrected hash.
   I have not measured how often this changed an archived scientific fit.

## Q2 — What the W2 development reading establishes

4. **NON-BLOCKING — Strong improvement, insufficient evidence to certify the false-call rate or its residual cause.**
   Independently recomputed all ten final set intervals and both earlier outcome blocks:
   rev 6 = 6 POSITIVE / 19; pre-D4 = 0 POSITIVE, 5 NEGATIVE, 4 UNRESOLVED / 9;
   final = 0 POSITIVE, 8 NEGATIVE, 2 UNRESOLVED / 10, mean contrasts −0.001594 to −0.000345.
   The final records have 0/1000 B3+ versus G3+ training-nesting violations, 35 recorded generalised-EM ascent
   acceptances, and no recorded NOT_CONVERGED chain stop (`results/s2/decision*/W2/set_*.json:1`;
   `results/s2/decision/summary.md:7`; `S2_REPORT.md:132–166`). This supports the numerical repair.

   Zero out of ten has a one-sided 95% Clopper–Pearson upper bound **25.89%**, not 4.66%.
   Gate (b) has not been evaluated or passed; correct the wording “holds” in `S2_REPORT.md:165–166`.
   Neither absence of false calls nor success at R=100 follows. O5 is a useful retained challenge, but
   cannot replace the independent W2 R=100 test or the numerical checks below.

   The diffuse S19 training gaps are unlike the conspicuous D4 failures. A finite-sample flexibility effect
   is plausible, but the records do not identify that cause, exclude residual numerical/covariance effects,
   or estimate its R=100 false-positive rate. In a correctly specified population, G's true density is also
   in B's closure; extra flexibility alone does not give B a strictly better population log score at truth.
   Keep the explanation as a hypothesis pending the final quadrature and validation readings.

   Two factual corrections: S19's held-out gains are **not positive on every fold**. Set 4/m14 has fold
   differences [−1.8494, 2.3328, −0.1486, 4.5248, −0.6092] nat; set 8/m10 has
   [1.8998, 2.3062, 1.1543, 0.2161, −0.0538] (`results/s2/decision/W2/set_{4,8}.json:1`).
   All-fold positivity describes their training gaps. S19 is also not the strongest by the declared
   strength: S14 = 2.941, S19 = 2.318 (`results/generators/summary_active.md:20,25`).

   **Late-arriving T1 reading:** set 0 is POSITIVE, mean +0.010509 with 95% t interval
   [+0.004619, +0.016399] nat/trial; 20/20 available, 15 positive participant contrasts, 0/100 training
   B3+/G3+ nesting violations and no recorded NOT_CONVERGED chain stops. Its code hash is `ca25a7be9e9f`
   (`results/s2/decision/T1/set_0.json:1`). This is one detection, not evidence that power meets 45/50.
   No O1 set JSON files were found at the 18:02Z cutoff. That is a pending experiment, not a negative result.

## Q3 — Recovery under free covariance

5. **NON-BLOCKING — Run the battery as designed; retain free Sigma in unrestricted and constrained fits.**
   Do not adopt (a), (b), or (c) for this S4. Freezing Sigma at the unrestricted fit does not repair a collapsed
   point estimate and turns the profile into a plug-in inference needing its own coverage validation.
   Sharing G's Sigma likewise inherits G's weak-signal problem and changes B's recovery procedure.
   A factor covariance is a substantive new model, with rank selection and new numerical/development work.
   Recommending it now would be a decision against the stated deadline; I do not recommend it.

   Measure the strength dependence on the fixed roster, apply unchanged R1–R5 faithfully, and report raw
   estimates, hulls, failures, and strength. An R1 failure means NOT ADEQUATE, not ZERO-ONLY, and cannot be
   rescued by selecting stronger participants after seeing S4 (`DESIGN_jitter.md:473–499`). Prediction can
   still be licensed independently; latency attribution requires full ADEQUATE in G (`DESIGN_jitter.md:284–292,593–601`).

   The weak-signal finding is preliminary, not a settled causal identification: the archived check predates D4
   (`S2_REPORT.md:272–274`). Its “oracle Sigma” variant also replaces estimated mu0 with true mu0
   (`results/s2/diagnosis/recovery_check.py:31–37`). Call it an oracle baseline/covariance comparison;
   to isolate Sigma's contribution, retain the same catch-estimated mu0 in an additional oracle-Sigma variant.
   The final-fitter rerun is addressed in Q7. No new covariance-model S2 round is requested.

## Q4 — Start recipe

6. **NON-BLOCKING — Keep the union, warm chains and unguarded reverse reseed; drop no family now.**
   The materiality counts support this choice (`S2_REPORT.md:192–212`; implementation
   `fit.py:615–637,845–900`). The collapse is a family-specific nesting construction, with a reverse search
   into G, rather than a reason to manufacture an unrelated extra G start. There is no measurement licensing
   the four-to-three reduction. G2's design starts sufficing on W2 does not license discarding B2's collapse
   or the positive-spread families on T1/O1.

   Do not claim that a flat broad-template start is literally contained in smeared NNLS starts: these are
   different vectors (`s2.py:413–426`; `fit.py:854–881`). It may be redundant empirically. Complete a basin
   comparison against the **repaired union and final EM endpoints**, rather than `s2.py:430–451`'s four-design-
   plus-development-start, first-stage comparison. Add a start only if this finds a material improvement,
   then recheck both families under the same declared algorithm before validation.

## Q5 — Generators, manifest, and executable pass conditions

7. **NON-BLOCKING — LW generator covariance is acceptable known synthetic truth; preserve its conditional meaning.**
   A fixed positive-definite LW matrix is an allowed Sigma in the free-Sigma scoring families. Generation
   and estimation need not use the same covariance estimator. D5's explicit LW call and EM-cache refusal
   implement that distinction (`fit.py:990–1013`). The generator records are configurations fitted conditional
   on LW noise, not free-Sigma MLEs or evidence that human noise is Gaussian/LW. Retain O5 and the declared
   diagnostics; no threshold needs relaxing because the scoring fitter changed. Free Sigma may reduce T1
   power; failing 45/50 then means the primary licence fails, rather than grounds to lower its requirement.

   Freeze the actual stored S1 generator assets as well as algorithms. Their summary identifies the old
   fitting hash (`results/generators/summary_active.md:1`); the new benchmark refit differs from the stored
   S10 G3 (80.1 versus 82.2 ms; `results/bench/bench_20261024T171350Z.md:9`,
   `results/generators/summary_active.md:16`). Those are acceptable distinct records,
   but a benchmark must not redefine the population after calibration. W2 and E1 should be described precisely:
   W2 draws fitted G3 configurations; E1 draws amplitude-scaled fitted B3 configurations, with its reference
   obtained by the final scoring procedure (`DESIGN_jitter.md:358–374,394–427`).

8. **BLOCKING — R2/R3 incorrectly average across challenges instead of requiring every challenge to pass.**
   The design requires rates at **each** zero-jitter setting (`DESIGN_jitter.md:476–480`). The implementation
   concatenates all five settings, pools them once, and tests that single rate (`decide.py:544–550`).
   Executed counterexample with 500 replicates per setting: O1 has 200/500 estimates above 20 ms and
   100/500 false profile detections; every other zero-jitter setting has zero errors. With other rules passing,
   the function returns ADEQUATE because pooled R2 = 8% (upper 8.95%) and R3 = 4% (upper 4.71%).
   O1 itself is at 40% and 20%. This can license a plainly failing challenge.
   Compute the roster-pooled rate separately within each setting, report all five, and require all to pass.
   Add this dilution counterexample. This repairs the code to the unchanged pass conditions.

9. **BLOCKING — The two-versus-four profile-start validation does not compare the final procedures.**
   `s2.py:515–524` runs one four-start EM fit, then calls its first two *initial-covariance* start objectives
   `ell2`; `ell4` also includes later EM solves under different covariances. The independent two-start EM
   procedure is never run. Executed mock: all four initial endpoints have ell=−100 and the shared EM
   endpoint has ell=−90. The validator reports q2=20, q4=0, even though a two-start chain could reach the
   identical final endpoint. Conversely, winning the initial stage does not ensure winning after EM.

   Run the complete two- and four-start procedures separately and compare final `FitResult.loglik`, using
   the same unrestricted reference. The unrestricted reference must itself use the repaired cross-family
   fitter: `(family+'3',)` at `s2.py:498` omits G's B-basin rescue and B's G-twin chains.
   Require the promised dataset/grid coverage; unavailable unrestricted/four-start fits currently can be
   skipped without failing `passed` (`s2.py:502–503,550–568`). A missing experiment must not pass vacuously.
   Then use four starts if either declared tolerance fails, and update the launch estimate.

10. **BLOCKING — Freeze one consistent c0 fitting procedure, including its cross-family dependencies.**
    `q0_statistic` and the type-7 quantile implement the scalar rules correctly (`decide.py:330–345`).
    But under rev 7 a G fit depends on B's rescue basin, and a B fit depends on its G twin. A stand-alone
    family pair is not the full-data recovery fitter (`fit.py:527–611`). The two likelihoods defining q(0)
    are statistic components, not necessarily the whole computational workload.

    Declare and use the same repaired candidate/chain procedure for c0, recovery point fits, and the real
    unrestricted reference; `(G3,B3)` supplies the four core candidates. The benchmark's `c0_pair` currently
    calls `fit_model` directly, giving four-start fixed-noise fits, not the repaired EM/union procedure
    (`bench.py:82–85,160–170`). Its q0 example is not a calibration validation. Price the necessary collateral
    fits and ensure the eventual S4 runner uses the declared procedure before drawing calibration data.

11. **NON-BLOCKING for S3, required in the launch aggregator — Assert manifest completeness before licensing.**
    `gate_b({})` and `completion_v2({})` both return `passed=True` (executed; `decide.py:477–487,506–514`).
    These helpers check only supplied settings; the tests intentionally exercise subsets
    (`tests/test_decide.py:155–166`). They must not be treated as whole-manifest validators.
    Require every retained graded setting with 100 attempted outcomes, T1 with 50, and the explicitly
    instantiated E1/T3/status records before a final licence. Convert missing/non-finite attempted results
    into the declared failure accounting. An uncertified setting is explicitly absent; an unfinished
    required setting is pending/failing, never silently absent. Gate (c)/(e) counts otherwise match the design.

12. **BLOCKING — The design's promised numerical closure has not been demonstrated at this freeze.**
    Only `results/s2/checks/ranks.json` and `small_spread.json` were found. They support conditional ranks
    and small-spread continuity on their checked cases, not global/joint identifiability with free Sigma.
    No node-check, basin, or profile-validation result files were found. The report explicitly marks them
    pending (`S2_REPORT.md:214–233`), and the design requires numerical error small before S4
    (`DESIGN_jitter.md:23–27,145–153,237–240,513–518`).

    Complete the final-fitter latency and scale quadrature comparisons, including the wide-scale bound,
    corrected profile validation, basin check, and planned T1/O1 development readings before freezing.
    S2's declared R=25 for W2/T1/O1 has not been completed; report any explicit pre-validation amendment
    to that development scope rather than calling the current R=10 W2 block completed S2.
    Also reconcile the specification with the actual **17-node adaptive** scale rule
    (`models.py:73–80,419–458`), rather than §4's 7-node prior-centred GH description
    (`DESIGN_jitter.md:149–153`). The tests establish errors of up to about 0.007 nat at the 1.5 bound
    (`tests/test_models.py:267–307`), which cannot be dismissed against thousandth-nat contrasts.
    Use the declared contrast tolerance to select/check the rule; unit tests and the old oracle test do not
    substitute for that final-procedure measurement. This is particularly relevant to the proposed S19 explanation.

## Q6 — Cost, AWS, and the two-day window

13. **NON-BLOCKING — The per-fit re-cost is the appropriate basis, but its worst-case arithmetic is incomplete.**
    Recomputed `recost_rev7.recost` on the archived benchmark: base 3,306.6894 core-h and stated worst
    4,160.2717, including only 80.3024 core-h of recertification. `recost_rev7.py:35` budgets one 50-set
    correction batch. Both E1 and T3 can require a correction (`DESIGN_jitter.md:420–427,549–551`).
    Budget two: approximately **4,240.6 core-h worst** on the same rates, before correcting c0 dependencies,
    measured overhead, retries, or any quadrature change. This is an estimate, not a measured upper bound.
    The rejected/redundant chain work and full-dataset target throughput should be captured by wall timings,
    not only selected results' archived starts (`fit.py:548–565`; `recost_rev7.py:46–62`).

    Using the owner's supplied **96 real cores per c7a.24xlarge**, the base is 34.4 ideal instance-hours;
    the corrected nominal worst is 44.2. Two instances give about 17.2/22.1 ideal hours, before barriers,
    start-up, and interruptions. The report's 96-vCPU=48-core conversion is inconsistent with that premise
    (`S2_REPORT.md:261–263`). At the design's assumed $1.70 per instance-hour, the ideal arithmetic is
    about $59/$75, not a live Spot quote or spend/headroom check. Measure completed-dataset throughput on
    the target, including the actual chains, before extrapolating. The Mac's measured factor 2.08 is evidence
    about its own contention, not an AWS multiplier (`results/bench/recost_rev7_20261024T171350Z.md:22`).

    **For a time-driven reduction, take T2 to development-only FIRST** (declared reduction (3)). It is
    report-only and saves roughly 80 nominal decision core-h without weakening the required recovery tests.
    Record this choice before validation: §8's numbered order is for a cap breach, so this is an explicit
    time-priority amendment, not a claim to have followed that cap sequence. Start removal lacks its required
    measurement; merging O3/O4 needs a specified combined generator and development check, costing calendar time.
    Preserve recovery R=25 and the grid if feasible; R=15 and nine points remain later declared economies,
    with unchanged thresholds, new-seed validation, and their reduced precision stated.

    T2 and the **report-only S4b T3** reading can be declared follow-ups after first submission. If T3 is
    deferred, retain its S4a search/certification as specified and label S4b power/coverage pending. This is
    a predeclared narrower first-submission manifest, not completion of unchanged rev 7; validate the retained
    manifest on fresh seeds. Keep W1–W4, O1–O5, T1, instantiated E1, the own c0 calibration and R1–R5 before
    the corresponding predictive/identification claims. Keep the inherited W1/W3/W4 mechanism comparison
    before latency/scale attenuation attribution. Do not call a not-yet-validated recovery flag ADEQUATE.
    There is no measured reason yet to sacrifice the identification opportunity to fit a different Sigma model.

## Q7 — The report's two open items

14. **BLOCKING — Rerun the recovery check under the final fitter before freezing.**
    The report itself requires this (`S2_REPORT.md:272–274`). D4 repaired under-finding in exactly the class
    of fits being interpreted. Archive the final hash, generator identities, attempt/completion counts,
    fitted values and chain diagnostics, whether the S4 weak-responder collapse persists or disappears.
    Confirming the original numeric collapse is not a pass condition; honestly updating the evidence is.
    `results/s2/diagnosis/recovery_check.py:39–47` does not record code hash or full chain diagnostics; add provenance
    for the rerun. Retaining the unrestricted recovery model means no new covariance-model S2 is necessary.

15. **NON-BLOCKING — Folding costing into `bench.py` can wait for a safe chain boundary.**
    The separate re-cost is inspectable and explicitly supersedes the old table
    (`results/bench/recost_rev7_20261024T171350Z.md:24`; `S2_REPORT.md:241–242,275–276`).
    Do not change a running chain to tidy this. Correct the two-target contingency and c0 workload in the
    authoritative launch estimate and use measured target throughput. Migrating the accounting into one
    script is housekeeping; claiming 718 core-h or pricing the old fixed-noise c0 procedure is not acceptable.

## Q8 — Freeze decision and closure order

16. **BLOCKING — NOT FAVOURABLE at the reviewed hash; no S3 freeze authorization is issued.**
    The four rev 5 conditions are represented in the design/code: the ZERO-ONLY event is >20 ms;
    the premise uses R6; lifts/certification/profile-reference branches exist with tests; the decision batch
    computes the correct reduced candidates (`decide.py:153–175,227–345,423–462,582–586`;
    `fit.py:568–598,812–842`; tests named for the rev 4/5 counterexamples).
    Their promised **verification** is incomplete because the profile-start experiment is invalid and
    other S2 checks are pending. New implementation defects must also close.

    Close in this order:

    1. **BLOCKING:** restore the declared acceptance contract (finding 3) and safe covariance/cache semantics
       (2); fix per-setting R2/R3 (8). Add the executed counterexamples as regression tests.
    2. **BLOCKING:** repair the profile validator (9), settle the common c0/recovery fitting construction and
       its workload (10), and reconcile the actual quadrature specification (12).
    3. **BLOCKING:** finish/archive the final-code numerical/start/profile and W2/T1/O1 development checks
       required by the retained S2 specification (12), and the final recovery rerun (14). A failed
       two-start comparison restores four starts. Resolve material numerical failures before any S4 draw.
    4. **NON-BLOCKING for S3, before launch/reporting:** assert the retained manifest (11); freeze generator
       identities; correct the cost/CPU accounting and any time-scope amendment (13); make prediction-target
       and W2/oracle wording precise (1,4,5,7). Bench-script consolidation itself remains non-blocking (15).

    Review the closure at the resulting commit, then freeze that actual hash. Keep the study focused on the
    existing matched predictive comparison and the failable jitter-identification experiment.

# R052 — Codex S3 freeze re-review, 25 October 2026

Reviewed entry HEAD `c78805909976dcbf6a5d58ee29e44b9e2b1b3abb`, five-module hash `d3aba729a660`.
During review HEAD advanced to `343d20e` (only `aws/userdata_s4.sh`, exporting chunk 64).
The requested scientific code, tests, design and evidence remain identical to entry HEAD; this review is pinned there.
Paths below are relative to `workspace_demo/sergent_port/jitter/`. Compact result JSONs occupy line 1.
Only this review was written in the repository. No commit, AWS operation or S4 draw was performed.

**Verdict: NOT FAVOURABLE at this hash; FREEZE HOLD remains.** The chunking change is acceptable.
The remaining work is an executable numerical contract and its final development reading, not a new model.
My proposed operational target is **61 latency nodes, scale rule `17then33` at s_g > 0.6, chunk 64,
four-start profiles, with S4 and S5 fitting on c7a.24xlarge**. That combined rule is not yet validated.

Verification: ran `../../t1_access/.venv/bin/python -B tests/<file>.py` for `test_fit`, `test_models`,
`test_decide`, `test_simulate`, `test_s4`, and the changed `test_s2_queue`: **24, 25, 30, 10, 10, 2 tests**, respectively;
all exit 0 with `ALL OK 0` (101 total). The brief's fit count of 22 is stale. Also independently recomputed the
paired contrasts/intervals and AWS development outcomes, checked identities, and executed the counterexamples below.
No new optimisation run was used to select a scientific outcome.

1. **NON-BLOCKING — The requested warm-endpoint repair is implemented, without relaxing acceptance.**
   `run_start` still refuses the no-better-retry exception for a retained endpoint with five or more iterations
   (`fit.py:317`). `fit_model` restarts qualifying stationary endpoints once through that same rule and records
   unresolved losses (`fit.py:492`, `:519`); `em_fit` compares those losses with the final selected likelihood
   (`fit.py:1023`). The two-pass second pass reapplies rescues and rebuilds selections (`fit.py:872`).
   The new acceptance/polish and second-pass tests pass (`tests/test_fit.py:543`, `:625`). This closes the
   implementation part of latency-review finding 11, not the remaining numerical failures in its experiments.

   Earlier rev-7 implementation findings also have concrete repairs: whitening survives serialization
   (`fit.py:432`, `:449`); cache keys include code/EM/quadrature (`fit.py:554`); R2/R3 are judged per setting
   (`decide.py:545`); the profile validator compares separate complete EM procedures (`s2.py:1035`);
   c0 uses both families' repaired candidates (`s4.py:244`). The relevant supplied tests pass.

2. **NON-BLOCKING — The raw checks mostly confirm the brief, with one material reporting correction.**
   A/B/C/D/E have the stated grids/rules and the same `6f0d60ddef91` hash; I regenerated W2 set 0 and matched all
   twenty identities to the archive and these five runs. All five primaries are NEGATIVE. Every original participant comparison
   fails; A/C/D/E each have one flagged candidate, B none (`results/s2/checks/repair_W2_set0_summary.md:7`, `:15`;
   each `repair_W2_set0_{A,B,C,D,E}.json:1`). D-A is also as stated in `repair_W2_set0_status.txt:14`.

   However, **not every set-mean shift is <= 3.8e-5**. Recomputed means are A -0.001474054863,
   B -0.001511717071, C -0.001528991044, D -0.001472395935, E -0.001497409652.
   A-C shifts by 5.49362e-5 and D-C by 5.65951e-5. The 3.76622e-5 figure is A-B, not the maximum over all arms.
   Correct `S2_REPORT.md:474` and `repair_W2_set0_status.txt:16`, and carry the correction into this briefing.
   These means remain small relative to their approximately 7e-4 half-widths; the correction does not itself stop S4.

3. **BLOCKING — Q1: replace the full-refit participant criterion explicitly; do not call its failures passes.**
   The same-host chunk pair has identical data/code and unchanged quadrature, yet max participant change
   6.31097e-4, RMS 1.57647e-4 (`results/s2/checks/chunkpair/compare_64_vs_0.json:8`, `:21`, `:24`).
   This demonstrates sensitivity of the finite optimiser to summation order. It does **not** establish an
   irreducible floor, that every perturbation has this effect, or that all node-refit differences are optimisation.
   One rounding perturbation is not an error bound. Qualify `S2_REPORT.md:610` accordingly.
   Retain the old FAIL records and amend the rule before S4.
   A participant maximum from a refitted procedure is a poor isolated quadrature diagnostic here; a group mean
   alone is insufficient too, because participant variation changes the interval width.

   Proposed exact replacement for the node-check text at `DESIGN_jitter.md:149` and `:161`:

   > Use 61 equally spaced latency nodes on +/-150 ms and the exact reduced candidate. Use adaptive scale rule
   > 17then33: fit at 17; refit each scale-free candidate with fitted s_g > 0.6 at 33 by the declared warm EM
   > chain, preserving rescues, acceptance and selection. Validate the final combined procedure on all twenty
   > members of development W2 set 0, using identical data, immutable code, runtime pins and host type.
   > Compare it with (i) 121 latency nodes under the same scale rule and (ii) blanket 33 scale nodes at 61 latency
   > nodes. For each pair let [L_j,U_j] be its group 95% t interval, h_j=(U_j-L_j)/2, mu_j its mean, and
   > T_set=min(8.8322454e-5, 0.1*min(h_1,h_2)) nat/trial. Require identical complete rosters, finite results,
   > no unresolved numerical or material matched-quadrature nesting failure, the same primary sign, and
   > max(|mu_1-mu_2|, |L_1-L_2|, |U_1-U_2|) < T_set. Independently cross-evaluate fixed theta, Sigma and mu0
   > at the final endpoints on the two grids; every participant contrast change must be < T_set. Archive
   > endpoints, both family scores, selections, failures and all comparison values. Refitted participant
   > differences remain reported diagnostics, not a separate maximum-error acceptance gate. A failed check
   > remains failed; change the algorithm and repeat development before S4, never tune this threshold on S4.

   This is a development-informed pre-validation amendment, not retrospective fulfilment of the old rule.
   It targets the primary group decision. It does not certify profile likelihood ratios by cancellation of G/B errors.
   Profile/calibration/recovery validity still requires their own frozen construction and S4 tests.

4. **BLOCKING — Q1: the existing evidence does not yet pass that complete replacement criterion.**
   Independently recomputed maximum changes over {mean, lower bound, upper bound} are:
   A-B 6.41649e-5 versus T_set 6.80131e-5; B-E 2.43529e-5 versus 6.96589e-5;
   D-A 2.16655e-6 versus 6.80131e-5; chunk64-chunk0 3.20306e-5 versus 6.54146e-5.
   These pass the **group numerical inequality**. A-C gives 6.82695e-5 versus 6.80131e-5,
   and D-C 6.94208e-5 versus 6.80639e-5: they narrowly fail it. Do not round those into passes.
   Sources: the five `repair_W2_set0_*.json:1` interval/participant fields and
   `results/s2/checks/chunkpair/{0,64}/m0.json:1` through `m19.json:1`.

   All these comparisons also have an unresolved failure in at least one arm, so none passes the whole contract.
   The earlier fixed-parameter probe is encouraging, but used the earlier Mac endpoints
   (`reviews/2026-10-25_latency_quadrature_fix_codex_review.md:65`); it is not a probe of the final combined endpoints.
   No 61/17then33 run appears among A-E (`s2.py:557`); chunking was paired at 31/17.
   Thus do not retain 31 by cancelling errors across participants, or prescribe 121 as a cure for path sensitivity.
   **61/17then33 is the target to check**, not an already licensed rule. It addresses the measured wide-scale
   envelope (`models.py:73`); accepting plain 17 everywhere, including wide-scale profiles, needs evidence beyond
   this W2 group contrast. The smallest closure is the two final-rule paired checks and fixed-endpoint evaluations
   specified in finding 3, under chunk 64 on the deployment host. Archive every participant, including failures.

5. **NON-BLOCKING — Q2: chunk 64 is acceptable for every training fit. Leave scores and posteriors as implemented.**
   `models.py:595` changes only the sum of independent trial contributions; the mask/padding remains intact
   (`models.py:642`). The same compiled objective supplies `Objective.__call__` and `total_loglik`
   (`models.py:670`, `:675`), so decision, recovery, constrained profiles, c0, epsilon, pilots and certification
   all inherit it. Export the variable before Python/worker import; do not change it after compilation in a live worker.
   The supplied equality test covers G2/G3+/B3+ and enforces value 1e-12 and gradient 1e-11 tolerances,
   not a blanket 1e-14 bound (`tests/test_models.py:419`, `:438`).

   Additional in-memory check here: on that test's 144-trial dataset (192 padded), at 61 latency/33 scale nodes,
   G0/B0/G1+/B1+/G2/B2/G3+/B3+ and both families constrained at 40 ms gave zero observed value difference and
   maximum gradient difference, normalized by max(1, ||g||_inf), 9.82e-16. This supports the algebraic change;
   it is not a guarantee that fitted endpoints agree. The same-host paired run measures that distinction.
   Per-trial held-out densities (`models.py:679`) and EM posterior/moments (`models.py:614`, `:626`) need no
   chunking change for correctness. Leave them unchunked; a later performance change would need its own check.
   The probe's 408 tasks/host-hour is a steady-state extrapolation; 100/1437 s is 251 as-run, not 408 achieved
   over that whole batch (`S2_REPORT.md:600`). The full S4 throughput remains a projection.

6. **BLOCKING — Q1/Q2: freeze settings that the production paths actually execute, including the S5 venue.**
   Current defaults are still 31 latency nodes (`models.py:72`, `:260`, `:340`); S4 passes no node override
   (`s4.py:203`, `:244`, `:283`), and `profile_evaluator` constructs its own default spec (`fit.py:1232`).
   Editing a launch description or assigning `M.N_TAU_NODES` after import does not update Python's bound defaults.
   Set the default before import, or pass one immutable configuration consistently through every path, including
   constrained fits, c0 and S5. Freeze chunk 64, the scale rule/threshold, four profile starts, software versions,
   host type and generator asset identities in a run record, and reject mismatched resumed records.
   The five-file hash alone does not encode environment settings or `s4.py` (`models.py:760`).

   **Use c7a.24xlarge with the same numerical/software pins for S5 fitting too.** The Mac may assemble the article.
   Calibration concerns the finite fitted procedure; transferring it to another numerical platform has not been
   controlled at the chosen settings (`S2_REPORT.md:518`, `:605`). Different platforms are not inherently invalid,
   but accepting the proposed Mac split would require a same-data deployment-equivalence development check,
   including profiles, rather than assuming transport. The inexpensive same-host-type S5 route avoids that extra
   experiment. This venue change is part of the pre-S4 specification, not a new restriction inferred from a clock.

7. **BLOCKING — Q3: known numerical failures are still silently usable in S4; ordinary nesting lacks a final guard.**
   `FitResult.available` checks only status (`fit.py:419`); a flagged fit can be AVAILABLE by design.
   `_fit_summary` omits `numerical_failure` and `polish` (`s4.py:176`), and CV scoring, c0 and recovery accept
   those results (`s4.py:211`, `:246`, `:288`); S5 CV does likewise (`fit.py:1097`).
   Executed counterexample: an AVAILABLE G0 with `numerical_failure=True` becomes a summary with status AVAILABLE
   and no failure indication. This contradicts the new promise to carry the flag in every result (`fit.py:85`).

   Also, the final nesting guard is inside the touched two-pass-pair path (`fit.py:794`, `:884`).
   Executed stub-cache counterexample under rule 17: G2=-100 nat, B2=-101 nat, both AVAILABLE and unflagged;
   `fit_all_models(..., models=('G2','B2'))` returns both unchanged and unflagged (`fit.py:865`).
   The record therefore cannot infer absence of nesting failure from absence of that flag.

   Smallest closure: preserve the flag/polish and diagnostics in task/profile records; run a final matched-quadrature
   nesting check for every relevant G/B candidate pair, whether or not two-pass fired; and define one training-only
   failure policy before S3. A minimal policy is to stop a flagged task as PENDING, retaining its diagnostics,
   until a declared deterministic rescue earns the existing acceptance rule. No aggregate or S5 result may silently
   use the worse standing fit. Alternatively explicitly amend failure-to-UNAVAILABLE semantics and apply every
   existing availability denominator/gate consistently; do not silently change that contract inside this review.
   Add counterexample tests at these task/aggregation boundaries. A group tolerance does not waive failed rescues.

8. **BLOCKING — Q4: four-start profiles are required but are not selected by the runner.**
   Corrected validation is complete and fails: G relative failures 425/1200, worst LR discrepancy 50.1507 nat;
   B 326/1200, 59.6171 nat (`results/s2_aws/profile_validation/summary.json:10`, `:26`).
   That directly invokes `DESIGN_jitter.md:265`. Yet the profile default remains two (`fit.py:1226`), and both
   S4 recovery (`s4.py:289`) and S5 full fits (`s5.py:101`) omit `n_starts`.
   Smallest closure: make the production default four or pass a frozen four explicitly at both call sites;
   record it, test the call boundary, and update the design's operational rule. Keep explicit two-start calls only
   for historical/validation comparisons. No rerun of the large 2-vs-4 experiment is needed merely to choose four.

9. **BLOCKING — Q3: reread all three R=25 development blocks under the deployable repaired procedure before S4.**
   Independent recomputation confirms the historical AWS counts: T1 25 POSITIVE; O1 14 NEGATIVE/11 UNRESOLVED;
   W2's 22 complete sets 17 NEGATIVE/5 UNRESOLVED. Their hash is `6d447ad94463`, not the repaired fitter
   (`results/s2_aws/decision/{T1,O1,W2}/set_0.json:1`; `S2_REPORT.md:174`, `:179`).
   The 11/6/16 B3+-G3+ nesting violations and five deficits >1 nat also reproduce; four large cases are S4
   (`S2_REPORT.md:351`, `:368`). These historical failures are not proof that the current algorithm fails,
   but cannot serve as its clean development closure. W2 set 0 alone tests neither T1 nor O1's failure paths.

   Rerun 25 complete sets each, including the three missing W2 members, with immutable source/runtime pins,
   chunk 64 and the chosen node/profile rule on c7a. Record all attempts, convergence/failure flags, raw nesting
   deficits and material deficits at `1e-6*max(1,abs(ell_G))`, selections and set intervals. No unresolved
   above-tolerance nesting/lost-better-endpoint failure may masquerade as success. This closes the development
   requirement at `DESIGN_jitter.md:27`, not the fresh-seed S4b gates. No requirement that every old set retain
   its sign is added. Preserve old records under their original hashes; a changed reading must be reported.
   At the documented 408/h rate, 1500 tasks cost 3.7 host-hours at 31 nodes; scaling by the measured 1.59 gives
   about 5.8 at 61, before two-pass/start-up/tails. The brief's four host-hours is not a measured 61-node price.

10. **NON-BLOCKING — Q3: the mixed recovery rerun is preliminary; a duplicate diagnostic need not precede S4.**
    Confirmed 100 rows, with 62 at `86eccfb3e15e` and 38 spread across seven later hashes
    (`results/s2/diagnosis/recovery_check_final.json:1`; `S2_REPORT.md:314`). The header cannot identify what
    each long-lived worker imported. Its S4 median 15.1 ms versus 63.4 true remains a mixed-provenance observation,
    not a clean demonstration under the frozen warm-endpoint repair (`S2_REPORT.md:327`).
    Retain free Sigma and the fixed roster; do not adopt a new covariance model or drop S4.
    I supersede rev-7-review finding 14's requirement for a duplicate exploratory rerun before freeze:
    the complete S4b recovery battery under immutable code is mandatory and can settle this without another
    pre-S4 100-fit diagnostic, provided causal claims about the collapse remain explicitly preliminary meanwhile.
    If that diagnostic is quoted as final-code evidence, redo it with a launch-time immutable identity first.
    S4b R1-R5 and profiles must finish before recovery/latency-attribution claims; prediction remains separately licensed.

11. **BLOCKING — Q4: O1/O2 recovery currently draws two datasets where the design specifies one shared dataset.**
    `DESIGN_jitter.md:467` specifies O1/O2 generated once and fitted by both families.
    `s4.py:275` instead loops over families, and `:277` includes that family in the random seed before regenerating
    at `:280`. For config S4, replicate 0, the O1 seeds are 136517400561167 and 118522255759232;
    O2 seeds are 236698438417999 and 50495052528477 (executed seed calculation).
    Smallest closure: generate each O1/O2 dataset once outside that loop, fit all eight models once, and compute
    both profiles from that common dataset/cache. Assert identical family data IDs in a task test.
    This restores the declared shared challenges and saves duplicate work; it does not reduce the manifest.

12. **NON-BLOCKING — Q4: retain the full manifest, unchanged gates and the completed basin reading.**
    No T2/T3 time-priority lever is invoked. Keep 1150 decision sets/23000 participant-datasets when E1/T3
    instantiate, both c0 batches, full recovery R=25/grid, inherited mechanism comparisons and four-start profiles
    (`DESIGN_jitter.md:411`, `:493`, `:609`, `:633`; `s4.py:58`). Uncertified E1/T3 are explicitly absent by
    the unchanged certification rule, not removed for convenience. The corrected completeness tests pass.
    The archived basin comparison supports retaining the starts (at most one of twenty improved per candidate,
    by at most 0.2011 nat; `results/s2_aws/basins/summary.json:1`). I do not reopen F6 or request new start families.
    Historical 25/25 detection and no graded POSITIVE in these development blocks are encouraging, not S4b licences.
    A recovery failure may narrow identification; it is not a reason to tune or suppress its battery before drawing it.

13. **NON-BLOCKING — Q5: the calendar/budget permits these closures; the estimate is not a completed run.**
    The archived spend is USD 166.79 (`aws/s4_spend.json:45`). Using the owner's approximately USD 820 total,
    about USD 2180 remains under USD 3000; the separate USD 1300 S4 row cap also remains in force
    (`DESIGN_jitter.md:624`). The projected USD 200-300/full-manifest 200 host-hours leaves headroom
    (`DESIGN_jitter.md:585`). Reconcile that estimate with the actual 61/two-pass/four-start bundle and enforce
    the existing cap; the 100-task decision probe is not a measurement of every category or every fleet barrier.
    Disjoint shards matter: the previous fleet duplicated work (`S2_REPORT.md:552`). No new AWS authority is issued here.

    These are bounded repairs and development checks, with no new model or reduced manifest required.
    **Completion before Tuesday 27 October midday PDT is feasible on the supplied throughput, not guaranteed.**
    Close the code/settings issues today, run final paired checks and R=25 development on the immutable bundle,
    then obtain the actual freeze line before any paid S4a draw. This leaves the stated S4/S5 planning window
    for Tuesday evening; the paper calls the method **the transfer audit** and reports whichever licence/flags result.

14. **BLOCKING — Closure order for the next review; no FREEZE line is issued for c788059.**

    - **BLOCKING, code:** set/propagate 61 and the proposed scale rule (`models.py:72`, `fit.py:1232`);
      select four-start production profiles (`fit.py:1226`, `s4.py:289`, `s5.py:101`); retain/handle numerical
      failures and final nesting (`s4.py:176`, `fit.py:865`); share O1/O2 datasets (`s4.py:275`). Add boundary tests.
    - **BLOCKING, specification:** record the exact amended criterion at `DESIGN_jitter.md:149`/`:161`, the
      runtime/host/S5 contract at `:585`/`:597`, four profiles at `:256`, and failure semantics at `:273`.
      This review's proposed text does not itself change the canonical design or executable configuration.
    - **BLOCKING, evidence:** perform finding 3's combined-rule paired checks and finding 9's complete three
      development blocks under that immutable bundle; archive them beside `results/s2/checks/` and reread
      `S2_REPORT.md:173`/`:465` under the final hash. Any unresolved failure stays a failure, not a relaxed tolerance.
    - **NON-BLOCKING, reporting/launch:** correct the maximum set-mean statement (`S2_REPORT.md:474`), preserve the
      mixed recovery label (`:314`), record asset/runtime identities and the measured launch estimate (`DESIGN_jitter.md:618`).

    Re-review that resulting commit. The warm-endpoint implementation and chunking are accepted; neither earlier
    review is wholly withdrawn while these executable and development conditions remain open.

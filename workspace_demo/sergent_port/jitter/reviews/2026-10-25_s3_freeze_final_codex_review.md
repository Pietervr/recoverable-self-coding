# R052 — Codex S3 final freeze review, 25 October 2026

Reviewed HEAD `3339521a80c28179565f4d6fd2be0732489098f2`; scientific code hash `531f80ce7cc9`.
Entry HEAD was `d994c6f`; the intervening S5 AWS runner and spot-price commits were also inspected.
Paths below are relative to `workspace_demo/sergent_port/jitter/`; compact result JSONs occupy line 1.
Only this review was written in the repository. No commit, AWS call or new optimisation run was performed.

**Verdict: FAVOURABLE with the amended participant failure rule adopted below. Finding 14's HOLD is closed.**
This review expressly adopts the amendment before validation; its exact specification is finding 3.
The S3 commit should include this ruling and copy that sentence into DESIGN §5. No additional development refit is required.

Verification: `../../t1_access/.venv/bin/python -B tests/test_decide.py`, `tests/test_s4.py` and
`tests/test_s2_queue.py`: respectively **31, 12 and 6 tests, all exit 0 / ALL OK 0 (49 total)**.
The earlier 113-test result is historical; this review reran the requested three files.
Independently recomputed all 75 raw/amended set readings, failure unions, available rosters, historical AWS data-ID
matches and both final-rule interval comparisons; inspected the fixed-endpoint records and NPZ inventory.

1. **NON-BLOCKING — Q1: finding 14's executable and existing specification closures are verified.**
   Defaults are 61 latency nodes and 17then33 (`models.py:73`, `:97`); threshold 0.6 and 33-node refits are recorded
   by `fit.py:1650`. Four-start production profiles are explicit at `s4.py:359` and `s5.py:139`, with the inherited
   unrestricted quadrature at `fit.py:1470`. The deterministic rescue is bounded by two rounds (`fit.py:106`,
   `:1189`), and unresolved failures become UNAVAILABLE before downstream scoring (`fit.py:1239`, `:1274`).
   The final guard covers candidate and selected G/B pairs even without two-pass refitting (`fit.py:1002`);
   records retain failures, rescues, nesting and polish (`s4.py:194`, `:211`). O1/O2 use one family-free dataset,
   one fit/cache and both profiles (`s4.py:329`, `:342`). Run-record keys, generator hashes and resume refusal are
   implemented at `fit.py:1623`, `:1696`; S5 checks the S4 fingerprint (`s5.py:65`).
   S2 disjoint sharding/assembly is at `s2.py:275`, `:354`; the exact set comparison, fixed-endpoint evaluation and
   final summary are at `s2.py:1045`, `:1086`, `:1215`. F/G/H are archived with their actual rules in
   `results/s2/checks/s2final/repair_W2_set0_{F,G,H}.json:1`.
   DESIGN incorporates the amended numerical criterion (`DESIGN_jitter.md:154`), rescue/fit failure policy (`:314`),
   four production profile starts (`:286`), shared O1/O2 (`:499`) and S4/S5 runtime/host contract (`:618`).
   The new aggregation amendment is the additional specification adopted in finding 3.

2. **NON-BLOCKING — Q1: YES, the final-rule checks and all three development blocks close the evidence item.**
   F/G/H each have the identical complete twenty-member/data-ID roster, finite results, no unresolved numerical or
   nesting failure, and NEGATIVE primary. Independently recomputed max changes over mean/lower/upper bounds are
   F–G **2.9566080676e-5 < 6.4264478596e-5** and F–H **1.5636656639e-5 < 6.4224892195e-5** nat/trial.
   Sources: the three run JSONs above; `results/s2/checks/s2final/repair_W2_set0_final_summary.md:9`.
   Fixed-endpoint reproduction is 2.4772e-15; maximum participant contrast changes are 2.74174e-5 on G and
   6.38937e-7 on H, both below the respective thresholds (`repair_W2_set0_final_summary.md:12` in that directory;
   `results/s2/checks/s2final/repair_W2_set0_crosseval.json:1`). Each NPZ contains all 600 required selected-model
   theta/Sigma/mu0 arrays (20 participants × 5 folds × 2 families × 3 arrays). Runtime pins and host agree across
   F/G/H; H's different fingerprint reflects its deliberately different scale rule.

   All 75 sets contain twenty recorded participant attempts, code ca6c7e5547d5 throughout. Recomputed raw outcomes:
   W2 0 POSITIVE / 18 NEGATIVE / 7 UNRESOLVED; T1 25 / 0 / 0; O1 0 / 19 / 6
   (`results/s2/decision_final/reading_summary.json:1`; all three directories' `set_0.json:1` through `set_24.json:1`).
   The 22/25/25 sets with historical AWS counterparts match all participant data identities. The three persistent
   matched-quadrature deficits are W2 r7 m9 0.16773 nat, W2 r12 m11 143.10423 nat and O1 r8 m17 1.40565 nat
   (`results/s2/decision_final/W2/set_7.json:1`, `W2/set_12.json:1`, `O1/set_8.json:1` under that same directory).
   I scanned the available matched pairs: no additional material deficit lacked a participant failure flag.
   These are recorded failures, not numerical passes. This closes the development requirement, not S4b's gates.

3. **NON-BLOCKING — Q2: adopt the amendment for S4/S5 cross-validated score aggregation.**
   Keep the two rescue rounds and fit-level UNAVAILABLE policy. Reject the old option of letting a failed required
   graded candidate silently leave its weaker boundary candidate to supply the group contrast. W2 r9 m13 is
   +0.180947, r5 m9 +0.038221 and r9 m6 +0.033050; the B-side failure at r12 m11 is −0.085470
   (`results/s2/decision_final/W2/set_9.json:1`, `set_5.json:1`, `set_12.json:1`). The rule must be symmetric in family
   and independent of the sign or size of the held-out contrast.

   **Exact sentence to append to DESIGN §5 after `DESIGN_jitter.md:324`:**

   > For S4 calibration and validation and S5 real-data cross-validated score statistics, a participant-dataset carrying any unresolved numerical failure or persistent nesting failure in its required fits is UNAVAILABLE as a whole, contributes no score to any set/group mean, interval, contrast or calibration reference, retains its raw scores and diagnostics in the archive, and counts against the unchanged 16-of-20 roster.

   The existing §5(c) sentence about unchanged availability continues to describe the individual fit's status;
   the new sentence governs the participant's use in aggregation even when a selected fallback fit is AVAILABLE.
   Full-data c0 calibration and recovery keep their separate per-fit/profile availability and attempted-replicate
   denominators (`DESIGN_jitter.md:525`, `:531`, `:544`). This is not permission to discard failed recovery attempts.
   The inherited per-window comparator keeps its own declared construction.

   Implementation matches this scope: `decide.py:189`, `:198`; `s4.py:465`, `:470`; `s5.py:231`; `s2.py:378`.
   S4 references and epsilon use the same filtered means (`s4.py:477`, `:542`, `:568`, `:582`); E1 and all decision
   gates use the filtered scores (`s4.py:718`, `:723`, `:740`). The regression test includes both failure families,
   nesting, the four-versus-five exclusion boundary and missing scores (`tests/test_decide.py:378`).
   The amendment is a declared development-informed change before validation, not retrospective success under §5
   as previously written. Its adoption here supersedes that earlier aggregate interpretation.

4. **NON-BLOCKING — Q2: the remaining measured failures do not themselves block S4.**
   Recomputed exclusions are W2 9/500 (1.8%), T1 18/500 (3.6%), O1 4/500 (0.8%), including the nesting failures.
   Amended rosters range 18–20, 18–20 and 19–20. Recomputed amended readings are W2 0/19/6, T1 25/0/0 and O1 0/19/6;
   W2 r5/r9 change UNRESOLVED→NEGATIVE and r7 NEGATIVE→UNRESOLVED
   (`results/s2/decision_final/reading_amended_failure_rule.json:1`; participant records cited above).
   These are the measured failure/exclusion rates of the declared finite procedure. They are not assumed harmless
   or unbiased missingness: S4b tests that complete procedure on fresh seeds. A set below sixteen remains UNAVAILABLE;
   graded gate (b) counts it as a false call, T1 counts it as non-detection, E1 as BOUNDED, and V2 retains its completion
   denominator (`DESIGN_jitter.md:447`, `:454`; `decide.py:498`, `:508`, `:516`, `:524`). No threshold is relaxed.

   The supplied hash is a five-module digest, not a Git revision (`models.py:765`): the requested literal Git diff
   could not resolve. I verified that dc339e8 and 80c1e97 both compute ca6c7e5547d5 and inspected dc339e8..HEAD instead.
   The scientific change is aggregation only; the changed decide.py makes the current digest 531f80ce7cc9.
   F/G/H contain no excluded participant, so their results are unchanged by this amendment. Applying it to the same
   development records is sufficient; those old records must retain their original code hash and raw values.

5. **NON-BLOCKING — Q3: neither the platform record nor the two development fingerprints requires another rerun.**
   The two development run records differ in Python 3.12.14 versus 3.12.15, fingerprint, hostname and timestamp;
   numerical libraries, CPU, code, settings and generator digests agree (`results/s2/decision_final/run_config.json:11`,
   `run_config_9of19.json:11` in the same directory). The mixture must remain disclosed as development provenance;
   it is not evidence of Python-patch equivalence and must not become a mixed S4 calibration/validation run.
   The decisive F/G/H comparison used one host on 3.12.14 (`results/s2/checks/s2final/repair_W2_set0_F.json:1`;
   `repair_W2_set0_status.txt:4` in that directory). The Mac/x86 identity refusals are retained there at lines 1–3.
   S4 and S5 must stay on c7a with the same recorded contract, including Python 3.12.14. The four AMI selections are
   recorded at `aws/s4_aws.json:5`, `s4_aws_euw1.json:5`, `s4_aws_use1.json:5`, `s4_aws_usw2.json:5` in `aws/`;
   their release mapping is documented at `S2_REPORT.md:695`. I verified the repository selections and records,
   not live EC2 metadata. Resume/S5 refusals remain mandatory (`fit.py:1705`, `s5.py:78`).

6. **NON-BLOCKING — Q3: retain the full manifest, four-start profiles and existing launch limits.**
   The manifest remains 1,150 sets / 23,000 participant-datasets when E1/T3 certify, plus both 500-dataset c0 batches
   and full R=25 recovery with shared O1/O2 (`s4.py:52`, `:58`; `DESIGN_jitter.md:442`, `:497`, `:525`).
   No time-priority deferral is adopted by this review. Four starts remain required; S4 recovery must establish the
   recovery/latency claims independently. S5's c7a runner is now present (`aws/userdata_s5.sh:16`, `:51`), and its
   code refuses real fitting before a complete S4 manifest (`s5.py:50`). No further scientific blocker was found.
   The closed jitter ledger is USD 196.79 (`aws/s4_spend.json:45`, a launch-time estimate pending billing reconciliation).
   The USD 1,300 S4 row cap and USD 3,000 overall cap remain unchanged (`DESIGN_jitter.md:637`).
   The final F arm measured 30,276 task-seconds / 20, mean 1,514 s per task; it is not a full-manifest throughput
   measurement (`results/s2/checks/s2final/repair_W2_set0_F.json:1`). Refresh the launch estimate from the final run,
   profiles and tails within the existing cap; Tuesday midday remains a plan, Tuesday evening PDT the owner's target.

7. **NON-BLOCKING — concrete recording and packaging actions for the S3/launch session.**
   Copy finding 3's adopted sentence into `DESIGN_jitter.md:324` and update the stale HOLD/evidence-owed header at
   `DESIGN_jitter.md:4`. This review supplies the adopted rule; the copy records it in the canonical design.
   Correct `S2_REPORT.md:665`: twenty attempted rows in every set, but W2 r23 and T1 r7 each have nineteen finite raw
   primary contrasts (`results/s2/decision_final/W2/set_23.json:1`, `T1/set_7.json:1` in that directory).
   Correct `S2_REPORT.md:670`: twelve W2 numerical failures affect **eight**, not nine, participant-datasets;
   the union with nesting exclusions is nine. T1's nineteen numerical failures affect eighteen; O1's three affect three.
   Record the amended reading as adopted at `S2_REPORT.md:685`, preserving the raw reading and both fingerprints.
   Build the S4/S5 deployment bundle from the frozen amended source; **80c1e97 is the evidence bundle, not the amended
   deployment bundle** (`aws/make_bundle.sh:18`; bundle selection at `aws/launch_s4.py:84`). Keep old results separate;
   never overwrite their hashes or bypass a run-record mismatch. These are recording/packaging actions, not a request
   for another scientific repair, development draw, reduced manifest or reviewer approval round.

8. **NON-BLOCKING — Q4: FREEZE granted for the transfer audit at the reviewed HEAD and adopted rule.**
   Finding 14's code, specification and evidence requirements are discharged by the verified implementation,
   existing DESIGN amendments, this explicit aggregation amendment and the final development evidence.
   The original NOT FAVOURABLE verdict remains the historical verdict on c788059; it no longer holds this source.
   S4a may follow the S3 commit and correct deployment packaging within the owner's existing authority and caps.
   No S4b predictive, upper-bound, recovery or attribution licence is granted in advance of its actual gates.

FREEZE S3 at RSC 3339521a80c28179565f4d6fd2be0732489098f2 with JITTER_TRIAL_CHUNK=64, latency 61 nodes, scale rule 17then33, failure rule amended

# Row 19 screen revision 2: controller repairs review

Date: 6 October 2026. Reviewer: Codex, exact session GPT: R052 Entropy paper, native 01a0d19e-2127-7051-9a61-6db771088559. Source: Claude R052 Entropy SI, native fdb5f471-1679-481f-8198-f3f211cc7447. Reviewed RSC abbd63d37bc591a2e952113b4813b850b43ac21e against fe3c266, under Unimog brief b4b7d61c40a24dd9f2d0e5b748ed78560201439c, prompts/2026-10-06_codex_r052_screen_rev2_repairs.txt, SHA256 efdf9052bd4ea490b0817a627f493899a67e24b309657ca54fd7bba72766fd19. Ownership was committed at Unimog 425b2409 before accepting transport 92275243-13df-5aed-93b5-9f57d3e87919 and beginning this review.

## Verdict and authority

**REQUIRE CHANGES / NOT FAVOURABLE to revision 2 as the complete repaired controller package for later admissions and numerical release.** Several important repairs work, but the normal pilot-to-later-job lifecycle fails; fresh receipts can overlook a failed later runner; verifier retention and generation are not enforced end to end; cap phases remain non-finite and crash/recovery vulnerable; and the failed-original release branch loses restored-chain failure evidence. The exact required changes below are bounded repairs to the submitted package.

The earlier a1ce224be22cc7d4b6ac1920935e2cee2adde503 approval remains FAVOURABLE WITH CONDITIONS for the first RAW refit job only (reps 3–26, refit index 0, 720 reserved core-hours) and first RAW originals job only (reps 3–22, 600 reserved core-hours). The source reports these as 7523818 and 7523819, submitted after its exclusive programme-wide fresh check: 11,378 existing commitment + 1,320 proposed = 12,698 of 100,000. This review does not independently inspect those actual jobs, revoke that approval, stop them, or authorize another job.

Even a favourable repaired-controller record would still require a separate review of each role's actual retained first-pilot evidence before role job 2+, and a separate review of the actual numerical-target construction before release. This record supplies neither authority. Existing bank/shard/mains approvals, the amended operational-only slice-report judgment, and every earlier closed review/report remain in their original scopes. Nothing is submitted on this answer.

## Evidence and method

I read the complete brief and declarations (Revision 2 first), the controller diff, full relevant controller/lineage/fixture paths, the retained 76-test transcript, and unchanged ledger/scientific aggregation paths needed to follow the repairs. Three read-only peers independently covered qualification/retention, funding/lineage, and release. All nine supplied file hashes match both committed abbd63d bytes and the corresponding local files. Both screen scientific manifests and their seven immutable producer/science pins are unchanged from fe3c266; separate revision-2 controller pins therefore coexist with existing scientific task bindings. There is no old/new scientific pin collision.

No source import or execution, test rerun, fit, simulation, actual pilot/target payload review, remote/job/account/provider operation, worktree or push was performed. Counterexamples below are static paths through the submitted code, not observed incidents in the queued pilots. The retained fixtures are useful engineering evidence; they do not constitute an actual pilot or numerical-target review.

Paths below are relative to workspace_demo/t1_access; line numbers refer to abbd63d.

| Reviewed file | SHA256 |
|---|---|
| chpc/programme_gate.py | d733bf8f31b50a6ce491ac5bb5ba4aabb0717794ed15874fd50917e4ab1d8fb2 |
| chpc/row19_screen_controls.json | b12475d8553d8b5dd8649d76dd19700db9ec074ae2f38827a054ebd2df6202a6 |
| chpc/row19_screen_admit.py | 53f7b09886b9013f48966537d4ba86e1f9e602c650db1bf8245fd9f18b409fea |
| chpc/row19_screen_status.py | c5db99943788fb3735228ca636d06b3295010217bb8d90c81a94cb7dc8512f5d |
| chpc/row19_screen_verify.py | 608caee38e8edea9c798ff94eadfdb74e09e69a78c312d86f48bb4a52a8b2d57 |
| chpc/row19_screen_release.py | 26c00fa07118441cf8a2ea231c47c818c2346c8b4e9e2800d7556b65774d1367 |
| chpc/ROW19_SCREEN_DECLARATIONS.md | 7512f8520fa320a03d305d46c4d4edabd7b315455697f89e43938664d1201e84 |
| test_row19_screen.py | 64cd5feb89170517234f02a4762ebe8bc11c725e30463f9d5e83e8d88e16d828 |
| reviews/2026-10-06_row19_screen_rev2_tests.txt | b56d262e4756740005de61a62eada9dba28cdebcb99774415796b14f0be14056 |

## Repairs that are effective

- Direct screen admission now holds the common programme lock before its fresh count and throughout every reserve, plan, qsub and bind (admit.py:615–652). Its proposed charge is derived from actual planned cores and filled walltime, rather than a caller's estimate (:517). Both roles share the same configured lock and five-campaign count. Existing job-start/end state changes do not add another reservation.
- programme_gate.py:50–93 rejects non-finite JSON constants, booleans/negative charges, missing settled charges, undeclared states, duplicate literal campaign paths and expected missing ledgers. The committed configuration's five campaigns are counted. A new campaign may be absent only with no plan files. This repairs the former permissive aggregate count; it is narrower than validation of every ledger identity/request invariant.
- Pilot review adoption now requires an exact role/qualification-SHA/max-job ADOPT line, tracked and unmodified review/adoption files, and their digests (admit.py:447–490). An arbitrary design review is refused. Typed actual numerical-review authority similarly binds the target and bank-record hashes (release.py:144–146).
- The selected job-1 summary now checks F state, acceptable scheduler/runner/worker exits and finite memory; worker job/slot identity, receipt timestamps, anchor content, exact binding maps and anchor hashes receive materially stronger checks. ASCII rec_000_extra.json aliases and conflicting sequential duplicate records are rejected. These changes are valuable, but the lifecycle, all-job and retention gaps below remain.
- Release now compares the bank and screen's setting, effective procedure configuration (excluding B and note), canonical scientific pins and environment (release.py:134–143). It requires RESOLVED at top level, frozen primary and recomputed primary (:117–118, :173–174). It reads target bytes once and carries that validated interval/hash through aggregation and decision (:81–84, :284–300). The mid-release replacement fixture therefore retains the first validated bytes.
- Historical seed exclusions must equal the controls-pinned history plus the reconstructed development/bank union, not a supplied subset (admit.py:117–163). The submitted exact history-manifest digest d1a7371ba955039a2aefbcf14fef81b79f4ecd2cbf5c86c4ed8a0be3ffbe056f matches. The current unique exclusion count is 4,411. No seed regeneration was performed here.

## Required changes

### R1. Freeze pilot qualification at job-1 scope; validate growing bindings in fresh receipts

expected_bound builds the bindings for **all currently started tasks** (admit.py:318–332), and bound_problem requires equality with that entire map (:351–352). qualification_problem applies this to the supposedly frozen first-pilot document (:414–420), although its scheduler-summary check selects job 1.

Ordinary valid sequence: refit job 1 completes reps 3–26; its qualification is reviewed and adopted for max job 9. Job 2 starts reps 27–50. The current expected map now covers 3–50, while the valid immutable job-1 qualification covers 3–26. The next admission holds on binding mismatch. Regenerating qualification changes its SHA and invalidates the exact adopted ADOPT line; the write-once adoption cannot silently follow it. This is a conservative failure, but it defeats the intended continuing campaign. Originals' empty binding map does not expose the same failure.

Require the immutable qualification to match exactly its retained job-1 plan/tasks/bindings and evidence. Require each fresh watch receipt to match exactly the whole currently started task universe. Do not weaken either to an unchecked subset and do not rewrite the pilot document or scientific bindings. Add a lifecycle fixture that adopts job 1, starts job 2 and successfully admits job 3 with unchanged pilot evidence plus a fresh complete receipt; include omitted/changed later binding negatives.

### R2. Validate terminal outcomes and observed memory for every started job

General reconciliation checks a missing runner exit, but does not alarm on runner exit 4 (status.py:174–175). Missing/negative memory is skipped (:170–171), and unusable walltime can be omitted (:192–193). The strict F/exit/memory checks are applied to the selected --qualify job 1. receipt_problem does not enforce the same constraints on every embedded job summary (admit.py:424–444).

Concrete original-role path: job 1 has a valid reviewed/adopted qualification for later jobs. Job 2 has scheduler F/exit 0, workers exit 0 and valid raw/timing records, but its ledger runner_exit is 4, or its scheduler memory is absent. Ordinary reconciliation can produce no alarm; a fresh receipt passes the all-job consumer; job 3 can proceed. The empty originals binding map avoids R1's conservative stop. An embedded bad follow-on job must not be allowed to inherit a good pilot's status.

Validate all terminal observations against their exact plans: permitted final scheduler state, scheduler and runner exit, expected worker count/slots, individual exits, finite nonnegative observed scheduler and worker memory, and required time bases. Distinguish legitimate queued/live jobs from incomplete or failed terminal evidence. Ensure the consumer independently checks that complete job universe and its retained sources. Retain observed values rather than replacing missing measurements with defaults.

Two related weaknesses belong in the same repair. Stray-file detection only globs already known job IDs (status.py:164–167), so a status for an unplanned job such as jobFOREIGN.slot0.json is invisible. Check the status directory against the whole expected job/slot universe. Also pilot_summary_problem accepts internally consistent zero slots/zero endings/zero exit counts, boolean integer-like values, and negative numeric memory without matching the actual plan's 20/24 expected workers (admit.py:374–384). Exact plan-derived cardinalities, assignments and strict finite nonnegative numbers are required. A minimal manufactured zero-worker summary is not pilot completion evidence.

### R3. Make full verifier retention, generation and snapshot identity enforceable

Status writes the full verifier document locally and then invokes scp, but ignores its return code (status.py:294–297). Qualification/receipt publication can therefore succeed while the full verifier failed to reach the consumer's evidence location. bound_problem does not enforce verify_sha256, and qualification_problem does not open/hash verify_file or compare the summary's anchors/units/bindings to that retained full document (admit.py:335–355, :396–421). A nested qualification receipt can omit normal schema/role/time/binding requirements. anchors_problem checks selected digest/equality flags without enforcing each source/required/compared/problem field (:358–371).

Require successful retention before publishing a usable qualification or fresh receipt. Require the referenced full verifier bytes to exist, match their digest, have the expected schema/role/time/producer and binding identity, and agree with the embedded summary. Any copy failure, missing source, conflicting summary or unverifiable reference holds. The separate actual-pilot reviewer must inspect those retained bytes, complete scheduler/worker evidence and raw/timing provenance, not only a qualification hash or favorable flags.

Producer generation is currently independent of that local check. verify_remote executes the verifier by filename under manifest.shard.clone and validates schema/role only (status.py:63–75). The unchanged manifest still points at the v1 clone. The verifier emits no checked controller generation/source digest and does not run controls_problem. A v2 admission consumer can consequently trust a v1 remote verifier with the same schema and no new duplicate-conflict evidence. Local v2 controller hash validation does not prove which remote verifier produced the evidence.

Specify and enforce the exact reviewed controller-only verifier deployment, record its generation/digest in the full output, and verify it at every consumer. Preserve queued/running producer, manifest, ledger and task-binding pins; do not solve this by pulling an altered scientific tree into an active campaign. Record a committed adopted controller version instead of the lineage's current uncommitted/pending placeholder.

Finally, pull, remote verification and later local binding hashing are separate observations (status.py:253–258, :286). Compare producer binding digests to the retained local binding snapshot, or collect a coherent snapshot and refuse/recollect on mismatch. A fresh timestamp alone is not proof that all components represent one observation. This can often fail conservatively, but it cannot be described as atomic evidence retention without that check.

### R4. Complete the finite, durable cap amendment and interrupted-raise protocol

cap_problem now handles ordinary finite phase/ledger mismatches and reconciles an already applied pending raise. However it loads phase/ledger JSON without strict non-finite parsing and converts phase caps with float without validating their schema/finite range (admit.py:181–198). A latest committed phase with cap_core_h=NaN makes abs(valid_cap - NaN) > tolerance false: it returns success despite no valid matching phase. Require strict finite positive caps, valid phase fields/campaign identity and correspondence to the retained ledger cap-history entry before comparison or reconciliation.

A pending phase is published before CampaignLedger.raise_cap validates the proposal (:603–605). A rejected non-increasing/non-finite proposal, or interruption before ledger update, can leave this pending phase. The advertised --raise-cap recovery begins with cap_problem and immediately refuses it (:598–601), even though the error says to finish using that command (:194–195). The retained fixture directly invokes Ledger.raise_cap, which does not establish working CLI recovery. Validate proposals before publication and provide an explicit resumable/retirable pre-ledger phase path with retained identity/history; test the actual controller CLI path.

Phase writes truncate in place without atomic replacement/fsync/directory fsync (:192, :604, :606). A crash can lose the prerequisite phase while the ledger's durable cap update survives. Make publication durable, reconcile with its exact history entry and preserve every charged/live reservation and earlier phase. No reset or fresh ledger is authorized.

### R5. Retain restored-chain failures even when the cached original failed

Release restores a complete refit chain at release.py:263–264, calls canonical analyze, then takes report counts/reasons from result.interval (:267–274). Canonical analyze.py:388–406 short-circuits after a failed original with n_used=0, n_failed=0 and reasons=[], despite a restored B-complete chain containing refit failures; the corresponding predictor default can instead report n_failed=B (:413–422). Thus the claimed failure propagation is not consistent in the failed-original branch.

Keep the failed original scientific unit excluded from both method denominators, as now. Separately retain raw restored-chain success/failure counts and reasons, per predictor, directly from the strictly restored chain, and label original failure and scientific unusability explicitly. Do not turn raw complete refits into a usable unit or hide their diagnostics behind that exclusion. Add a fixture with a failed original and a complete chain containing flagged failures; assert the actual counts/reasons, not merely that a failures dictionary exists.

### R6. Bind the controls artifact used by the release consumer

CONSUMER_FILES pins the wrapper and admission source but omits chpc/row19_screen_controls.json (release.py:58–59). seed_domain/exclusion_contract actively reads that JSON (:106–128); release does not run the controller lineage checker. The actual numerical-review adoption must therefore bind the committed controls bytes, history-contract pins and adopted release/controller generation as well as the code/T/bank hashes. Require tracked/unmodified exact controls or an equally explicit immutable artifact, and reject mismatch. The same deployment proof is required for the standalone programme wrapper, which otherwise loads its programme block without checking the reviewed controls/wrapper hashes. A JSON change alone is not claimed here to manufacture new hash-bound scientific data or launch work; the defect is an incomplete reviewed consumer/provenance boundary.

### R7. Close the remaining canonical anchor alias cases

The verifier's canonical filename regex uses \d{3} (verify.py:28). Python permits Unicode decimal digits there; conversion to int can map an alternate spelling to index 0 and produce the same alias/last-wins issue within the anchor verifier. Rep directory aliases can similarly share a numeric coordinate (:147–151). Use ASCII [0-9] and exact formatted basenames, and reject duplicate logical rep/index coordinates before selection. Check all three shared index-0 anchors and every nonconflicting shared record with exact float-bit comparisons and source identities.

This is not an established universal admission bypass: admit.py:246–253 already checks the ASCII formatted file path and can reject a surviving alternate filename. The remaining finding concerns the verifier's advertised canonical and unique anchor contract, including independent historical anchor roots. Preserve historical source ledger/PBS/binding provenance; anchors are cross-route identity evidence, not newly qualified pilot observations.

## Programme-wide operating conditions

The direct-screen transaction is repaired. The older bank/shard/slice controllers remain unchanged and acquire the shared lock only through programme_gate run, as the declaration explicitly acknowledges. Treat this as a cooperative operating procedure, not unconditional code enforcement across every writer.

The wrapper trusts --proposal-core-h rather than deriving the child's actual filled requests (programme_gate.py:112, :124–128). For example, 99,100 committed plus declared proposal 1 passes, while two default bank requests of 864 each create 100,828 commitment, if their campaign still has headroom. Every wrapped call must retain an accurately derived conservative total for all jobs/request overrides and the exact command/manifests; every older admission must use the same verified wrapper/configuration. Do not wrap a screen controller that already takes this lock and create nested locking.

Ledger settlement is another commitment writer: row19_ledger.py:208–223 locks its campaign, can replace a live reservation with a larger actual charge, and does not hold the programme lock. Runner start/end changes do not create this problem. At 99,200 committed including a 100-hour reservation, an admission can reserve 720 while a simultaneous settlement increases that reservation to 300, leaving 100,120. Serialize settlement/accounting changes with the same programme window, retain authoritative actual accounting, and account for positive deltas before further admission. A nominal wrapper proposal of 1 does not establish a correct settlement delta. Truthful overspend must still be recorded; all subsequent admissions then hold. If automatic enforcement is claimed, integrate these writers with a settlement-aware programme transaction.

The aggregate parser validates charge values and declared states, not every ledger token/job/request invariant. Zero live reservations and loss of both ledger and plans need an explicit malformed/continuing-campaign diagnosis; loss of history must never be reclassified as a new campaign. These are operating and provenance conditions alongside R4's concrete cap defects. They do not withdraw the source's already completed exclusive check for the first raw pilots.

## Retained tests and scope of inference

The source's retained log reports 76 passing tests in eight modules, including 12 screen fixtures, at 21:59:23Z. I read it without rerunning it. It exercises ordinary finite cap raises, already applied pending reconciliation, finite out-of-protocol caps, strict charge failures, adoption mutations, ASCII alias/conflict cases, effective procedure mismatch, triple RESOLVED and target replacement. It does not establish the later binding-growth lifecycle, every later terminal outcome, exact plan cardinalities, full verifier copy/source enforcement, remote verifier generation, committed NaN cap phase, interrupted pre-ledger CLI recovery, wrapper proposal/actual disagreement, settlement concurrency, or the failed-original raw-chain failure counts above.

The intended NaN-ledger fixture uses open(path, "w").write(open(path).read().replace(...)) (test_row19_screen.py:413); argument evaluation truncates the file before the inner read. It tests empty/invalid JSON and a generic error phrase containing non-finite, not an actual retained NaN payload. The visible programme parser does reject non-finite constants; this is a fixture deficiency, not a claim that the parser accepts NaN. Retain the source string before opening for writing and assert the precise rejection. Stubbed tracked_unmodified and release fitting stand-ins remain engineering fixtures, not committed review authority or numerical calibration.

The no-fit consumer retains the intended complete-100/all-B restoration requirement, paired method membership and actual usable n, inclusive whole-target-interval containment, and one-sided Clopper–Pearson bound. The 83/100 threshold applies only at n=100 for its declared single-look error allocation; a non-stop result is not a pass. Operating-characteristic UNRESOLVED is not a coverage certificate. The illustrative .025 + .01 = .035 budget needs a justified 99% target construction and a single primary setting/look; it does not automatically cover both methods, additional settings or later diagnostic selection. Actual target uncertainty, failure estimand, heavy tails and unseen-tail sensitivity remain for the separate numerical review. No numerical target, interval endpoint, coverage decision or later campaign launch is adopted here.

## Completion and ownership

Only this review record is owned in RSC. Claude retains design, code, scientific manifests/bindings/ledgers, clone/account operations, actual pilot evidence, numerical construction, current declarations/preregistration/tracker and dispatch. The reviewer owns the R052 Codex log and committed adoption/checkpoint briefs. Record these bounded findings and required corrections in the source-owned current summaries through the manager handoff. Send one authorized completion line; do not repeat any earlier report, ack, adoption or launch.

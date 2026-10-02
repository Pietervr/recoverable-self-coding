# R052 — Stage A and AI image-reader revision 4, exact-package second opinion

Date: 2 October 2026 (America/Phoenix). Reviewer: Codex, `GPT: R052 Entropy paper`, session
`01a0d19e-2127-7051-9a61-6db771088559`.

**Verdicts: NOT ON BOARD with executing row 20 Stage A at this package; NOT ON BOARD with AI-reader qualification calls at this package.**
Both refer to RSC `d7a486ae25e6952eb2ce15f7c89a2eb36abe1474`. Revision 4 makes substantial repairs, including
the shared approval guard and two real reader defects found by R084. Remaining failures affect resource enforcement,
process recovery, archive admission and durable completion. Neither package receives a favourable attestation here.
This record grants no forward, image transmission, reader call, capture, simulation, cloud/HPC operation or row 21 run.

The controlling brief is Unimog `prompts/2026-10-02_codex_r052_rev4_both_packages_review.txt` at
`897e456bd11491be54f918dac4d501627b50b8da`, SHA256
`59748d9da00f2261234f74e06e2c2c964ff0b61869d271787e5059587e351a8e`.
Ownership was committed at Unimog `386c4a3f`; handoff `192aba0e-5e8e-53bc-b190-b4cd13d35353` was accepted
before review edits. The preceding records `081f17b` and `5a8d7ac` remain closed.

**Scope and evidence.** The system has two separately gated jobs. Stage A qualifies the photograph input and
instrumented/native measurement path under row 20's existing envelope; a later complete report, interpretation,
report review and owner row 21 go would still be required for Stage B. The separate reader job would transmit
600 qualification views, subject to its frozen aliases, durable retry/smoke policy and technical boundary. A passing
reader gate would qualify that reader for the later naming audit; it would clear no photograph for formal reuse.

The exact committed brief, both criteria/job/design documents, relevant framework §§8.2/8.4/8.6 and row 20,
submitted source/JSON and named fixture code were read. Three scoped helpers inspected distinct source lanes;
the parent checked the material traces and integrates the judgments below. No submitted program, module, test or
fixture was executed or imported. No Codex CLI command, sandbox probe, rendering, model request, image opening or
naming occurred in this review. Deterministic text/AST/JSON/hash/git arithmetic only was used for metadata checks;
those scratch files are not additional scientific outputs. Retained suite stdout/stderr and resource measurements
are submitted evidence, clearly distinguished from fresh measurements. No private audit answers or forbidden audit
artifacts were accessed. Codex/GPT is the proposed reader: this exposed construction/review context and its helpers
cannot provide blind qualification, training independence or independent naming errors. The earlier target-visible,
concept-batched R2 limitation and prior exposure remain.

**Exact identities.** All five Stage A hashes, the identity's self-hash and its ten local source blobs, packet,
import map, receipt, plan and manifest relationships were independently reproduced without invoking `package()`.

| Stage A field | SHA256 |
|---|---|
| criteria_sha256 | a57ac515e6a37baf909e57c7e2ca693c752671a72f3be1d38631c2ea04260fc9 |
| identity_sha256 (file) | d6a73a4e466e19a0250a9876297aa214d489cae62c7ac29db7831f662aa11ff8 |
| plan_sha256 | 98eb2817df5a99c98fab29285cd002f95a3042fa6fa235146cf9719d922289d6 |
| manifest_sha256 | e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448 |
| budget_sha256 | 334ae9c9e5be55b0f8e6cdfc17d7d60463dc28da548239e0a59a2d2f390f8820 |

Inner identity: `61dd0aa0c9a7b99b2a54f02be0d9f67b007b99754e3996a28fdc7bcd8fa4f81e`.
The reader's 24-field package, including 16 file hashes, was independently reconstructed from git blobs, literal
AST constants, binary/manifest/sandbox bytes and the saved CLI-version field. The command/profile/gate/environment
template hashes to `031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba`; the package digest is
`68ba57fe39a7e726f9f57cf236fc6c2a649d9d6fa979d09e393b30831c1519d4`, matching the brief. This reproduces the
submitted identity; it is not a fresh CLI-version/preflight or external-delivery measurement.

Construction comparison confirms all 300 key items/aliases unchanged, all 600 requests and their order/prompt
unchanged, and all 600 delivery image hashes, sizes, details, MIME/file hashes and reencoding flags unchanged.
The normalized user-text hash changes in all 600 receipts, with 600 distinct new hashes. Stage A's 20 inputs,
178 attempt definitions and diagnostics are unchanged. Its changed top-level plan fields are revision, envelope,
budget hash **and provenance_checks_sha256**. The carry remains 16 engineering attempts plus 178 planned =
194/200, with 1,808.73 s already spent; row 20 remains 4 h/1 GiB, whole-task memory 48 GiB with a 44-GiB stop,
and the rows 20/21 aggregate remains 2,056 attempts/8 h/9 GiB. Reader limits remain 660 attempts, three tries,
120 s and six hours. No additional allowance follows from this review.

**Retained verification.** Every byte of both retained run directories was read. The ten current files at RSC
`14ae6d0` reproduce the sizes/hashes in `2026-10-02_photo_suite_rev4_run.md`; the recorded HEAD is `d7a486a`,
photo status before the run is empty, main exit is 0, main stdout empty, and main stderr records **167 tests,
OK (skipped=5), 790.568 s**. The five WordNet KeyFunctions tests separately record exit 0 and OK in 0.654 s.
The earlier retained run has HEAD `859262f071df172f48f8cd13381706c545c14023`, main exit 0, 167 tests OK
with five skips in 788.505 s, and all five WordNet tests OK in 0.645 s. The disclosed non-recurring revision-3
error is absent in both. That requested rerun closure is satisfied; I do not ask for another identical run.
Passing fixtures support their exercised branches, not omitted call sites or the counterexamples below.

**Question 1 — Stage A closures 1–7.** Line references here and below are to `stimuli/photo/` at the reviewed commit.

| Closure | What is repaired | Remaining gap / evidence scope |
|---|---|---|
| 1. Guard and worker identity | Strict exact schemas, full commit objects, one closed block, duplicate-key/date/hash refusal, commit descent and chronological binding; mandatory reviewed-commit package re-derivation; identity self/blob relations; missing/failing/stale positions receipt refusal. Real-git builder and refusal fixtures support these repairs. | Gates/report do not consume/check their own import maps or perform the claimed completion-time local identity recheck (A1). |
| 2. Independent controller and recovery | Gates are a supervised worker; per-worker watchdogs, in-process system reads, ordinary whole-group cleanup and recorded-member identity checks; recovery authorisation hold distinguished from refusal/terminal; report reads ledger without granting authority. | Post-spawn setup exceptions bypass cleanup; immediate restart can kill the watchdog before an unrecorded in-group child; independent safeguard is group-only and does not check the documented controller start time (A2). |
| 3. Whole-task memory | Broader task sampling, max(current,lifetime), retained live-loop maximum, nonzero MLX-cache measurement, unreaped exit-peak probe. | Exit/controller peaks do not reach the final aggregate predicate; missing final samples do not hold; the 4-GiB margin ignores permitted latency and TERM grace (A3). |
| 4. Clock/storage | Common writers reserve used+3n by class; 64-MiB finalisation reserve; final record fixed-point size; declared crash charge and phase deadlines. | Whole-controller setup/close/finalisation remain unbounded or uncharged; lost controller accounting resets; post-rename failure can leave PASS; post-write size mismatch does not invalidate disk PASS (A4/A5). |
| 5. Independent archive validator | Full record/image/merge membership; input IDs/token count, readout/capture/edit/rotary/merge predicates; decoded boundary hash/finiteness; residual finiteness; native embedding compared with paired archived merge; unknown IDs/outputs, phase maps and numeric criteria re-derived. Earlier specific counterexamples now have rejecting predicates and mutations. | Impossible ledger counters remain accepted; full instrumented checks are deferred until after native admission; several type/range claims exceed predicates (A6). Full logits/features remain live-bound digests. |
| 6. Current report and final PASS | Ordered report writes and receipt last; current worker/session/package checks, prior PASS superseded, final counters/caps and B prediction; interpretation checks author/date/both figure hashes. | Controller accepts a self-selected receipt output set; final memory/accounting/write gaps also affect PASS (A3–A7). Interpretation is still a later B requirement. |
| 7. Declarations/construction | 61/63 freeze, first-listed-sense wording, source wording, repaired prospective audit map and scorer's map-byte pin. | Declarations must match residual bounds; source snapshot/current-pin relation and later audit scorer-code binding need explicit treatment (A8). |

**A1 — omitted identity call sites.** `stage_a.py:419–424` creates the gates map and compares the fresh identity;
`:1002` discards the report map returned by `worker_identity`. Neither consumes/checks it with
`check_imported_origins`, unlike instrumented/native (`:735–736`, `:906–907`); neither calls `recheck_identity`
before its completion/receipt, unlike `:805`/`:977`. A local source change during report construction therefore
has no completion-time rejection. The helper fixtures establish the map/recheck helpers, not these worker call sites.
Consume and check each applicable worker's actual bound map and recheck identity before committing completion.

**A2 — lifecycle gaps are operational paths.** In `stage_a_controller.py:502–519`, worker spawn, exit-watcher
registration, watchdog spawn and the first post-spawn persist precede the cleanup `try` at `:522`.
A one-shot persist failure can return REFUSED from gates, or reach the run's TERMINAL/report path, without ending
that worker. Report then replaces the controller's worker/watchdog handles; the older watchdog observes the same
newly refreshed controller.json, so stale-heartbeat cleanup need not fire. The old worker is omitted from the new
phase's memory roots. Failure between spawn and watchdog installation is another orphan window. Put cleanup ownership
around the first spawn; gate work on durable verified identity and an armed safeguard; refuse to advance until all
prior work is gone. Cover exit-watch/watchdog/first-persist failures; the retained persistence fixture fails only
after several ongoing writes (`tests/test_controller.py:326–342`).

Restart `_reconcile:148–172` kills only persisted identities, including the watchdog, without enumerating/clearing
the original worker group. A child born since the last persisted member sample can remain alive in that group while
restart kills its leader and safeguard. This is an immediate-restart gap, not the disclosed fast escape/reap limit.
The controller-death fixture waits for extinction and the watchdog record before restart (`tests:280–293`). Require
identity-anchored whole-group extinction before retiring the safeguard or continuing; cover immediate restart with
an unrecorded live member. `stage_a_watchdog.py:58–66` never checks its documented `controller_start`; its group-only
signals cannot independently kill recorded escaped descendants while the controller is dead/blocked. Pass/check
controller identity and provide the claimed independent cleanup scope, or explicitly narrow the guarantee and
establish that the admitted task cannot produce the excluded case. The reader shares these interfaces (R3).

**A3 — final memory and margin.** `_final_peak:399–408` records the leader's exit maximum only in `by_phase`, while
final PASS uses `task_lifetime_sum` (`:337`, `:364`), updated only in live-loop samples (`:549`). `_self_sample:277–283`
similarly updates a separate controller field. Exit-probe failure records an error and returns; self-probe failure
returns silently. An over-48-GiB exit spike missed between live samples can thus be observed in the final evidence
yet leave the cap predicate passing. Fold all required final process peaks into a consistent task aggregate, retain
member maxima by identity and refuse missing mandatory final measurements; include controller finalisation.
The exit fixture asserts the phase field, not the aggregate/cap (`tests:141–146`).

The submitted synthetic growth average (~12.7 GiB/s) times saved 0.113-s iteration gives ~1.43 GiB. That establishes
neither maximum instantaneous/model growth nor worst allowed stop latency. The allowed 0.5-s sample alone gives
~6.35 GiB at that illustrative rate; memory stop permits three seconds of TERM grace (`:447–461`), and scanning/
persistence occurs outside the sample-time check (`:546`, `:560`, `:567`). Sampling plus that grace allows roughly
39.5 GiB at the same rate; this is arithmetic exposing the omitted term, not a model forecast. Qualify the complete
observation-to-extinction bound against the margin, using prompt resource-stop termination or another enforceable
bound. Real normal model memory may remain the intended Stage A measurement.

**A4 — whole-controller clock.** Session timing starts after configuration, recovery and superseding (`:201–205`);
close samples time before synchronous scan/write (`:264–275`). After the report safeguard ends, receipt hashing,
ledger/final-size reads and the post-write scan are unprotected. Only the final write has a 30-s timeout
(`:330–378`). A blocked close/scan can exceed the task clock. The blocked-writer fixture proves worker extinction
but externally kills the still-blocked controller (`tests:344–370`). The crash charge uses group-gone time
(`:133–143`): a worker can die on stale heartbeat while its controller stays blocked much longer, and later recovery
can lose that controller time. Bound and charge the whole setup/recovery/close/finalisation path independently.
`_load:125–128` also treats absent controller.json as fresh despite an existing execution ledger/output; refuse lost
accounting rather than restoring the engineering baseline. Validate finite, nonnegative accounting before use.

**A5 — durable completion.** `enforce.write_atomic:83–86` renames before directory open/fsync. A failure or block
after rename can leave STAGE_A_FINAL.json saying PASS while `_finalise:375–377` exits 75. The fixture raises before
any final write (`tests:418–426`), so it does not prove the claimed “no final record” result. The post-write size
mismatch branch (`:378–380`) changes only the returned object, leaving the stored PASS unchanged. Use a completion
protocol/admission marker that cannot admit such a record; invalidate mismatching disk completion and test post-rename
exceptions/blocks and size mismatch. Ordinary ordered writes/reservations are useful repairs, not this durability proof.

**A6 — ledger and pre-native admission.** `_ledger` in `stage_a_report.py:232–246` int-coerces tries/passes and checks
equations without their legal domains. Static consistently changed complete-ledger counterexample: keep all 178 valid
committed outputs and kinds/statuses; set all tries=0 and per-try passes=1; set row20 started=16, passes=16,
completed=193, failed=-177; set row21 to zero and aggregate=row20. These satisfy its recomputed equations and the
controller's final algebra (`:323–327`), including 16=193−177. This is an edited-artifact rejection counterexample,
not an assertion that the honest writer produces negative failures. Require exact entry/counter types, positive
legal tries, the declared passes per try, nonnegative counters, completed≤started and complete open/interrupted/
recovery relationships. Cover coherent zero/negative states rather than just one inconsistent count.

`admit_native` (`stage_a.py:833–860`) verifies hashes, membership, unique records, uint16 residual shape/digest and
plain count, but omits the independent instrumented schema/input/edit/image/boundary/finiteness predicates.
A non-plain input_ids_sha256 changed with consistent record/ledger/phase hashes passes that admission and allows
native work; final report's INPUT_IDS rejects it only afterward. Use a phase-specific instrumented validator before
native work and resumed-record admission. The current corrupt-output test changes bytes without updating hashes.
Also validate declared top-token IDs, requested-rank types/ranges (bool/negative int currently accepted), and the
final-logit dtype rather than any string (`report:148–156`), or narrow the full-schema claims. No claim of independent
reconstruction of unarchived logits/features is required.

**A7 — required report membership.** `_report_ok` (`controller:305–310`) checks only self-listed receipt outputs
and requires only machine JSON. Static archive counterexample after a successful current worker: remove the figures/
Markdown and consistently trim receipt outputs to the unchanged machine JSON. Current session/package/hash predicates
still pass, and A can PASS (`:366–367`). The normal builder does write all four; this is independent admission's
missing required set. Require both SVGs, Markdown and machine JSON with current hashes, strict receipt schema and
consistent admissibility/validator/session fields. Missing interpretation/figures separately prevents later B; it is
not itself a new interpretation prerequisite for A. Framework §8.4(p) already requires A's complete report.

**A8 — construction and scope declarations.** The prospective audit map has 32 concepts, eight per family,
16 CAL/16 PILOT, 106 aliases and no shared admitted string. Its SHA256
`a3f6ab51dbf0dda1148a26bfdc8b671adf91d1edc712fe58ef9ddcffc0397c80` matches the freeze; current key/builder
construction identities match. Scoring pins map bytes but does not enforce the live classifier/normalisation source
identity (`audit_alias_map.py:122–139`): bind that in the later audit package, not as a new Stage A semantic gate.
The revised plan pins current provenance `0085d38e…`, while unchanged manifest execution_identity retains
`84abf361…`; explain construction-snapshot versus current provenance, and list the moved provenance field in
criteria/readiness. `load_frozen:384–397` does not enforce current pool/provenance pins; declare whether admission
uses reviewed immutable source records or requires current records identical. This is a declaration/interface
choice, not proof of an identity self-hash mismatch. Source admission/stock checks remain recorded observations,
with publication recheck, not independent external rights verification. No stock site/photo was visited here.

**Question 1 — reader closures 1–7.**

| Closure | What is repaired | Remaining gap / evidence scope |
|---|---|---|
| 1. Guard/scoring identity | Shared strict guard and 24-field digest; scientific score entry refuses injected key/set/delivery/package; admission recomputes approved package/delivery. | No remaining guard-schema objection identified. Journal admission defects below still affect scientific scoring. |
| 2. Frame/key/specificity | No redraw, key item/alias equality, retained-close and ratio frame checks, first-listed-sense S4 wording, bounded suffix audit/counts; full-form S1 and rebuild tests retained. | Keep the stated plural omission and specificity convention visible (Q3); neither is an image-level correctness or human-equivalence proof. |
| 3. Durable holds/recovery | Holds/smoke reconstructed over all first-request attempts; incomplete journal validated; ordinary main-attempt cleanup, per-attempt watchdog, first-request/try2 hard-kill fixtures. | Structural-after-end restart produces a validator-invalid suffix; immediate restart/group and shared watchdog limits remain (R2/R3). |
| 4. Physical/receipt/event boundary | Deny-default profile; only pinned binary exec; per-request user text compared; image/prompt separator fixed; stdin /dev/null; exec/network-denied local config receipt; known notice exceptions and deeper lifecycle. | Accept the disclosed unobserved serialized body; correct “no program” wording. Some bookkeeping/image-detail predicates and local receipt bounds remain incomplete (R5/R6). |
| 5. Clock/storage/stops | Clock opened early and beats independently; refreshed pre-GO allowance; lost/finite-insufficient accounting tests; main quick-exit overflow and failed-setup cleanup; fsynced quarantine. | Six-hour bound is not independently enforced through setup/finalisation; NaN accounting admits work; validator allows seven hours; local receipt caps/cleanup and quarantine crash dedup remain (R4–R6). |
| 6. Independent journal evidence | Required evidence, exact-text hashes, finite numeric checks, frozen instruction/image/user-text pins, selected outcome re-derivation and contradiction mutations. | exact=false bypass, loose identity/per-type schemas, image size/detail and whole raw/record-size admission remain (R1/R6). |
| 7. Declarations and retained suite | Both clean full run records, separate WordNet checks, explicit private-use/conflict limits; two measured revision-3 defects disclosed and repaired. | Align declarations with residual enforcement; clean suite closes rerun request, not all mechanism claims. |

**R1 — received evidence can be hidden from independent re-derivation.** In `ai_reader_journal.py:241–252`,
complete `text` with exact=false receives only a size check, without a reproducible bytes/hash check.
`_rederive:265–284` parses text only when exact=true. Static COMPLETE artifact counterexample: start with the
otherwise valid provider-failure/legal-retry trace used by `tests/test_ai_reader.py:470–474`. Replace the failure's
events with complete ASCII JSON lifecycle events carrying agent_message `unclear` (or command_execution), set
matching event length/hash but exact=false, and leave provider_failure, retained=false, answer=None and its
nonstructural stderr. The evidence representation passes; re-derivation skips the received answer/tool; later
retry/order/counters and the existing passed first-request smoke remain legal. Recount raw bytes and receipt hash:
COMPLETE/scientific admission still use this validator. Even a file_answer_sha256 for the received text is unchecked
on provider_failure. An incomplete first-request variant validates and resumes toward try2 despite that evidence.

This is an independent validator/resume rejection counterexample. Honest `Runtime.classify` would retain this ASCII
answer/isolation and mark it exact; I do not claim honest execution naturally creates the edited label. The promised
independent check must reject the contradiction. Parse all complete retained text using the actual decoding policy,
or fail closed on evidence that cannot be re-derived; enforce representation consistency and file-answer evidence
for non-answer labels. Add exact=false received-answer/tool mutations for COMPLETE and incomplete resume. Existing
mutations test exact-true contradiction (`tests:530–556`). Retained head/tail evidence cannot prove absent interior
events; preserve a conservative no-retry rule wherever sufficient complete evidence is unavailable.

**R2 — structural hold recovery writes an invalid journal without another dispatch.** After a durable
end structural_failure, a crash before STOPPED leaves a valid incomplete prefix. `_run` validates it but then
does preflight and appends open (`ai_reader_exec.py:410–421`) before loop.holds. The validator permits only receipt
after structural failure (`journal:328–329`), so restart itself creates an invalid open+STOPPED suffix.
Derive/enforce holds immediately after recovery, before preflight/new-open, going directly to a valid STOPPED.
Cover structural failure at after_end for the first and a later request. Current after_end smoke crash uses noimage;
in-process structural fixtures do not cover this restart. This defect does not imply another reader call was sent.

**R3 — recovery safeguards need whole-group identity.** Reader `recover:488–491` kills recorded worker/watchdog/
member identities through `kill_identified`; like Stage A it can retire the watchdog before clearing a surviving
in-group child absent from the durable member sample. Its member file is sampled every second (`:641–645`). Main
ordinary cleanup is repaired (`:542–559`, `:690–703`), but does not establish immediate-death recovery. Share the A2
repair: preserve the independent safeguard until verified group extinction; cover immediate restart with unrecorded
live members; pass/check controller start identity and address recorded escaped members during orchestrator death/
block. The pinned binary may fork under this profile, so an unqualified no-descendant guarantee is not established
by shell/helper denial. An unobserved short-lived process is a separate disclosed limitation, not this persistent
orphan case.

**R4 — clock enforcement and integrity.** `Clock._beat` (`exec:153–158`) persists but never enforces the cap.
Per-attempt watchdogs end before journal end/receipt/clock-close; package/go hashing, preflight, recovery, scans and
final fsyncs have no independent whole-job deadline. Exhausted resumes still perform admission/preflight before the
loop checks remaining time. A blocked beat can hold Clock's lock through close. Receipts sample time before their own
append/persist/close. Journal admission explicitly allows job_clock_s+3,600 s (`:476–478`), including COMPLETE:
an otherwise valid 6h30m receipt is admitted despite the six-hour limit. There is no declared one-hour allowance.

Clock loading/check_accounting (`exec:136–145`, `:188–200`) lacks strict finite/nonnegative typed-schema checks.
NaN seconds_total defeats the “below charged time” test, propagates into remaining, and defeats `<` budget guards.
Default json.dumps in the common writer accepts it; min(120, NaN) retains the ordinary timeout, so another begin/GO
can occur before later receipt rejection. This is a coherent altered-accounting admission trace, not a measured
spontaneous NaN. Validate clock state before any work; independently bound and charge all phases through durable
finalisation; enforce the declared cap in admission. Any prospective cleanup allowance must be explicit and within
the overall envelope. The reserve/heartbeat tests (`tests:859–863`, `:949–955`) prove narrower properties.

**R5 — local receipt subprocesses retain separate cap/cleanup gaps.** `run_local` (`runtime:208–230`) polls/reaps
the leader, kills its group only on sampled timeout/overflow, then slices files. A quick successful >4-MiB exit can
return rc0 with truncated output; ordinary surviving descendants have no whole-group/member cleanup. Reads use
read_bytes() before slicing, so the capture-memory bound is also not established for an oversized file.
`invocation_receipt:300–327` repeatedly reads/slices the first 4 MiB without checking file sizes while they grow,
and its kill/wait does not verify all member extinction. These are uncovered local-command paths, not observed
real-binary failures. Apply final overflow refusal, bounded reads/output, independent timeout and verified whole-group
cleanup on every exit to local receipts too. Cover quick exit, leader-first descendants and receipt timeout; main
Job cleanup does not cover these commands. Preserve the local/network-denied no-request preflight scope.

**R6 — narrower admission/detail claims and quarantine window.** The following complete the gap list; they can be
closed with explicit predicates or by narrowing a nonessential descriptive claim where that does not weaken a limit:

- Runtime lifecycle checks ordering/uniqueness and unknown error items, but top-level bookkeeping payloads remain
  shallow: `{"type":"error"}` inside an otherwise valid lifecycle is ignored; usage need only be a dict
  (`runtime:408–477`). Validate required bookkeeping/usage schema/types/finiteness before calling all payloads well formed.
- Begin receipts require exact keys and three digests but do not type-check/compare image_bytes/detail with frozen
  delivery (`journal:363–374`); live comparison also omits those fields (`exec:573–583`). Check every declared image
  delivery field or explicitly limit the receipt claim to the fields actually checked.
- Independent validation checks required per-type fields rather than exact full key sets; worker pid/pgid/start
  accept int-or-str (including bool), with no watchdog identity/equality validation (`journal:317–323`, `:375–380`).
  Define/enforce the actual variable end/recovery schemas and strict identity relations used for recovery.
- `validate` does not enforce MAX_RECORD or full raw-file length. A valid COMPLETE artifact's final reason can be
  expanded beyond 20 MiB while its prior-body raw_bytes_before/hash stay unchanged; receipt schema only requires a
  string, and admission caps only raw_bytes_before (`:479–484`). Honest append refuses it, but independent scoring
  admission does not. Enforce line and complete-file bounds, including the receipt, before parsing/admitting.
- Crash after quarantine creation but before truncation leaves both the pending file and original tail. Restart
  computes pending then repairs and appends pend+[tail] (`exec:407–416`), producing two records for the same quarantine.
  Deduplicate by quarantine identity and cover that exact window; the current fixture covers a pending-only file.

**Question 2 — declared limits.** I accept sum-of-lifetime overcount as a conservative *early-stop* convention for
included, successfully measured processes. I cannot accept “never late” while known final peaks are omitted or the
observation/termination margin is unqualified. The saved nonzero MLX-cache, real-fall and unreaped-exit measurements
support their probe classes, not missing predicate integration or a maximum allocation-rate proof.

I accept explicitly live-bound full logits/features as this bounded archive's evidence scope, with residuals,
boundary bytes and the other retained fields independently checked. This does not prove reconstruction of unretained
arrays. Tiny LOCK/watchdog writes outside the common reservation are acceptable as declared reserve exceptions;
final totals/completion still must enforce the task cap. The power-loss tail is a prospective accounting rule, not
a measurement of elapsed machine-off time; ordinary machine-up controller/reader paths must first be bounded and
charged. The escaped-and-reaped-between-samples limitation can remain explicit under a justified no-fork Stage A
scope, but does not excuse startup or immediate-restart persistent orphans, and cannot simply be transferred to a
reader whose allowed binary can fork.

The reader's deny-default physical read/exec boundary is a meaningful repair. A mandatory CLI upgrade is not required
merely because unified_exec remains true, if the physical boundary and fail-closed observed-event policy are actually
enforced. Its current effective claim is **32 requested disables, 31 false plus unified_exec true**. Only the pinned
Codex binary is allowed to execute; shell/helper execution is denied. Wording “no program it may launch” is too broad:
Codex itself and process-fork are permitted. The exposed environment/auth/runtime permissions must remain explicit.

I accept the disclosed difference between local prompt-input/network-denied exec receipts and an unobserved serialized
external request body. The two source-measured revision-3 defects show why the exact local invocation matters:
the new `-i image -- prompt` and notice handling repairs are supported by retained regression/receipt fixtures.
They still do not prove actual delivery. The first ordinary counted smoke is an acceptable technical-route test
after both review and owner go, once the remaining mechanisms are repaired; it must not be treated as scientific
correctness or an opportunity to alter the key/prompt. Different developer, public training overlap, per-image
provenance and private-use restrictions remain candid scientific/source limits. Six hours and output/process bounds
are enforceable commitments, not acceptable “disclosed, not proved” exceptions.

**Question 3 — plural omission.** Agree with R052: leave this reviewed version's frozen key unchanged and record the
reported ordinary regular-plural omissions. The current irregular-map-first branch (`ai_reader_key.py:125–141`)
explains the omission; I did not execute WordNet or independently establish a complete English plural lexicon.
Adding valid omitted forms could only increase individual exact-match credit relative to this fixed key; leaving
them out is conservative for the 61/63 conjunction gate, not a guarantee of fairness/equivalence to human naming.
Do not advertise complete accepted English naming. No generic regular-plural generator or post-answer alias change
is justified. A later enumerated, independently checked addition would be prospective, with fresh key/delivery/
package identities and a new review before answers. I do **not** require those 13 additions before reconsideration.
Retain S4 as the already reviewed prospective convention, with its exact first-listed WordNet noun-sense predicate
and documented equivalences; it is not an empirical claim about actual human dominant naming.

**Question 4 — exact conditions per package.** No favourable block is supplied in this combined negative record.
The agreed guard format needs no field change. If a later combined review approves both, use separate records with
one block each (the strict guard admits exactly one block per record), or another explicitly reviewed arrangement;
do not put two blocks into a file that the current guard will refuse.

For **Stage A**, reconsider after: (1) all applicable worker map/origin/completion rechecks; (2) guarded durable startup,
independent verified safeguards and immediate-restart whole-group cleanup; (3) integrated required final memory
evidence plus qualified observation-to-extinction headroom; (4) finite continuous accounting and independent
whole-controller setup/recovery/finalisation bounds, refusing lost state; (5) durable completion that cannot leave an
admissible PASS after post-rename failure/block or final-size mismatch; (6) legal typed ledger/counter/recovery
invariants and full instrumented admission before native forwards; (7) exact required report outputs/receipt
consistency; (8) aligned scope/provenance declarations. Add the specifically missing failure/consistent-mutation
fixtures, retain their output and re-freeze exact hashes. Later audit classifier-code binding remains a before-audit
condition; Stage B's report review/interpretation/CAL/owner go remains separate.

For the **reader**, reconsider after: (1) complete-evidence re-derivation cannot be skipped by exact=false and
non-answer labels cannot hide received evidence; (2) structural-after-end recovery goes directly to a valid STOPPED;
(3) identity-anchored whole-group recovery and shared safeguard interfaces cover the claimed scope; (4) strict finite
clock admission and independently enforced/charged six-hour setup-to-completion path, without implicit seven-hour
admission; (5) local receipt commands enforce final output/read bounds and cleanup as well as the main attempts;
(6) strict independent journal/identity/image-detail/complete-file admission and idempotent quarantine recovery;
(7) declarations and exact package updated with retained evidence of these repairs. The unchanged key, frame, gate,
private qualification scope and prospective counted smoke remain. This is technical repair within the current design,
not permission for a fresh panel, setting, prompt, redraw, extended budget or a later audit job.

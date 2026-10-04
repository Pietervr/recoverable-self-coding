# Stage A supplement (ledger row 20): the OS bridge before row 21 - declared criteria and code, revision 5 (R084, 4 October 2026)

**Specification:** Codex's record RSC `b0db0f9` (`reviews/2026-10-03_stage_a_report_codex_record.md`, SHA-256
`52ed7082...6b90`), §"Prospective row21 OS bridge: form, count and gate"; R052's handoff `8266e5ae` item 2.
**Status:** BUILT AND TESTED ONLY. No forward and no model call before Codex's record on this exact package and the
owner's go bound to it (`ROW20S_GO.json`, attestation row `20`, stage `A-supplement`). The revision-15 four-native go
does not cover it.

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | RSC `b67a073` | RSC `478196f` | NOT FAVOURABLE: the separate carried tree and ledger accepted; P1 restart can erase STOPPED |
| 2 | RSC `369e517` | RSC `1abb851` | NOT FAVOURABLE: §R2 credited; P1 a failed terminal recreation let a restart regenerate PASS |
| 3 | RSC `4baba91` | RSC `410b580` | NOT FAVOURABLE: §R3 credited; P2 a released=False endpoint record read as no start |
| 4 | RSC `280604d` | RSC `f716bea` | NOT FAVOURABLE: §R4 credited; P2 a stale controller.json snapshot can erase the endpoint record |
| 5 | this commit | — | an append-only release-intent file per endpoint (§R5) |

## 1. What it is

Stage A passed (revision 15, RSC `281fabb`; accepted with qualifications at `b0db0f9`). Its instrumented records were
made on macOS 27.0 and its natives 16-19 on 27.0.1. Before row 21's first CAL forward, Codex requires one bridge on
the current environment, on the **original Stage A DEV-CAL input 00** (crow at -12 dB, carrier 0), fixed by id and
hashes:

| New id | Path | Compared directly with | What it measures |
|---|---|---|---|
| `00-plain-os2701` | one plain INSTRUMENTED forward, macOS 27.0.1 (build 26A434) | (a) input 00's retained 27.0 instrumented record `00-plain` | the missing same-path bridge across the OS point release |
| `00-native-os2701` | one NATIVE forward, same input, same environment | (b) `00-plain-os2701` (new / new) | current-OS path fidelity |

A pass of each new endpoint against an old reference does not replace comparison (b): tolerance agreement is not
transitive. The original `00-plain` / `00-native` are never reopened; the 178-id plan and manifest are unchanged; the
194/193/1 counters are carried, never reset; no old producer identity is relabelled.

## 2. The comparator (accepted, applied prospectively, unchanged code)

Each pair goes through `stage_a.compare` - the function Stage A's native worker and validator call - with the
REFERENCE as the denominator: every recorded layer's relative L2 (three marker rows x 5,120, FP64; reference norm
finite and non-zero) <= 0.01; each requested logit |ref - cand| <= max(0.10, one bfloat16 step at the larger
magnitude); identical requested-token argmax; every statistic and logit finite. `compare_pair` adds the BOUND checks
and records the receipt: for (a) both records' input ids, readout positions, pixel tensor, grid and multimodal
positions (frozen = effective) equal input 00's frozen values; for (b) the new instrumented record's bound values,
the native effective positions, one prefill, and the native merged embeddings equal the new instrumented merge
bitwise (Stage A's existing native criterion). PASS = comparator AND bound. Bitwise equality of residuals, logits,
features and merge across (a) is recorded as a labelled diagnostic, not a criterion. Each EXECUTED comparison's
receipt (`supplement/comparison_a.json`, `comparison_b.json`) is written before its own stop decision and retained
either way; a failure of (a) stops the version before native, so (b) is then recorded absent - native is never spent
merely to produce a receipt.
Records: the new ones carry Stage A's own record schemas (`stage_a.instrumented.v4`, `stage_a.native.v4`), so the
unchanged independent validators `stage_a_report._inst` / `_nat` admit them (from disk, before the commit, and on
reload); the reference `00-plain` is admitted by `_inst` from the frozen Stage A tree with its pinned outputs.

## 3. Accounting: row 20's envelope, not row 21's

| Resource | Carried in (pinned in the supplement plan, re-checked) | Supplement | Cap |
|---|---|---|---|
| starts / passes | 194 started, 193 completed, 1 failed, 194 passes (the Stage A ledger) | +2 -> 196 of 200 | 200 |
| time | 2,338.11 s (the Stage A controller's row-20 `seconds_total`) | every session, gates, comparisons, receipt and the 60 s closure | 14,400 s |
| storage | the frozen Stage A tree's bytes (396,783,863) | the supplement tree | 1 GiB (the controller's cap is 1 GiB less the carry) |
| memory | — | per task, as Stage A (stop 44 GiB) | 48 GiB |

Every start is charged: a warm-up, internal or failed forward is an attempt (counted durably before the forward,
`enforce.Budget`). The four remaining starts are NOT a retry budget.

## 4. Design: its own tree and ledger (why neither option (a) nor (b))

The supplement runs in `captures/photo_stage_a_supplement/` with its own ledger (`stage_a_state.json` there), its
own controller record, final, marker and receipt. The ledger is created with Stage A's row-20 counters as its
`carry_in`, so `check_ledger`'s recount and the 200 cap hold across both. Reasons, measured by reading the code:

1. A new attempt id in the accepted Stage A ledger would make the unchanged Stage A validator fail
   (`stage_a_report._ledger`: LEDGER_UNKNOWN_ID for any id outside the 178).
2. `STAGE_A_FINAL.json` binds `controller.json`'s sha256; a supplement session there would change it.
3. The Stage A controller supersedes `STAGE_A_FINAL.json`, its marker and `report/REPORT_RECEIPT.json` at every session
   start and always regenerates the report - it would move the accepted bundle aside.
4. The ledger's identity slot holds revision 15's identity (`1d017dce`); a new package identity there needs either (a)
   a release-free transition for a non-terminal accepted run in `stage_a.py`, or (b) a new ledger row in the
   reader-bound `enforce.py`. A separate ledger needs neither: no transition, no `enforce.py` change, no reader-package
   move, no relabelled identity.

The accepted Stage A tree is FROZEN and only read: the supplement plan pins its ledger, controller record, final,
marker, acceptance, report receipt and phase records by sha256, its whole size in bytes, its admitted PASS, its
identity slot, counters and seconds, and the reference record's outputs, producer identity (revision 10,
`e146ec63`) and environment (27.0, from the recorded transitions). Every supplement worker re-checks all of them
(`check_stage_a_frozen`); any change refuses.

## 5. Mechanism

| Item | Where | Fixture (`tests/test_stage_a_supplement.py`, no model, no forward) |
|---|---|---|
| The plan: input 00 copied from the 178-id plan with every hash; the two ids; the comparator text; the reference; the frozen-tree pins; the envelope and its hash; the declared environment `{"macos": "27.0.1", "build": "26A434", "machine": "arm64"}`; the scope | `stage_a_supplement_plan.json` (`stage_a.py supplement-plan`), `make_supplement_plan`, `load_supplement` | `Plan.test_input_00_fixed_and_row20_accounting`; `test_tampered_plan_refused` (input hash, extra id, envelope, carried counters, build); `test_stage_a_tree_must_stay_frozen` (controller record changed, one new byte in the tree, unadmitted final) |
| The identity: `execution_identity` on the unchanged 178-id plan, manifest and positions receipt, with its own import-map file | `stage_a_supplement_identity.json` (`stage_a.py supplement-identity`) | the gates worker (the real check) |
| The package (six hashes) and its re-derivation at the reviewed commit, the identity proven to describe that commit's blobs (`_identity_describes_commit`, factored out of `package_at_commit` with unchanged checks and messages) | `supplement_package_hashes`, `supplement_package_at_commit` | `Gates.test_go_is_stage_a_supplement_and_binds_the_package`; the existing `ReviewedPackageBuilder` and `GoAttestation` classes on `package_at_commit` |
| GATES: no supplement terminal; the plans, code and frozen tree; the positions receipt; the go (row 20, stage A-supplement) via the shared, unchanged `stage_a_guard.require_go`; a fresh identity equal to the frozen one; the DECLARED ENVIRONMENT - macOS product version AND build AND machine (a version string alone refuses); its own import map; crash reconciliation, where an interrupted try STOPS the supplement | `run_supplement_gates` -> `SUPPLEMENT_GATES.json` | `Gates.test_declared_environment_build_not_just_version` (build 26A999; macOS 27.0); `test_interrupted_try_stops_the_supplement` (start stays charged: 195 started, 2 failed; terminal; later phases refuse) |
| INSTRUMENTED: worker identity; the reference admitted; the instrument loaded, its import map checked; input 00 admitted (frozen original, PNG, tensor, grid, sequence, processor); one capture; per-pass checks; the record saved, re-read, validated, committed; comparison (a); its receipt; `SUPPLEMENT_INSTRUMENTED_DONE.json` | `run_supplement_instrumented` | `Run.test_pass_...`; `test_comparison_a_failure_stops_and_retains_its_receipt` (receipt kept failing; terminal; 195/194 preserved; both phases then refuse; receipt STOPPED; Stage A's TERMINAL untouched); `test_failed_forward_is_charged_and_stops`; `test_a_started_endpoint_is_never_resumed`, `test_native_needs_the_instrumented_commit_of_its_own_session`; `test_corrupt_reference_holds` (checksum, before any start) |
| NATIVE: a separate worker process (`run_native`'s rule: no jlens_qwen imported); the instrumented phase admitted first (ledger = phase record, comparison (a) retained and passing, record re-validated); one native forward; the native checks; comparison (b); `SUPPLEMENT_NATIVE_DONE.json` | `run_supplement_native` | `Run.test_comparison_b_failure_stops`; `test_native_refused_before_the_instrumented_phase` |
| RECEIPT: always after passed gates, also after a stop; reads, never converts; admissible only with this session's gates and an equal identity; PASS needs both ids completed in one try, the ledger legal at exactly carry + 2 (196/195/1/196), both phase records equal to the ledger, both comparisons retained and passing, no terminal record, the frozen tree unchanged; binds every output by sha256; written last; records the compatibility fields | `run_supplement_receipt` -> `supplement/SUPPLEMENT_RECEIPT.json` | `Run.test_pass_...` (PASS, every bound output hashed, package and identity = the gates'; the Stage A tree byte-unchanged) |
| CONTROLLER: the same controller in its own tree under its own names (`SUPPLEMENT_NAMES`), phases supplement_gates -> supplement_instrumented -> supplement_native -> supplement_receipt (always), its own terminal record (no release), row 20's carried seconds and remaining storage; it supersedes only its own final/marker/abort/receipt and never writes Stage A's names | `stage_a_controller.SupplementController`, `supplement_controller()`, `main supplement` | `Controller.test_pass_under_its_own_names` (phase order; marker; no Stage A final, GATES.json, TERMINAL.json or report; clock > carry; row-20 storage figure); `test_work_failure_writes_the_supplement_terminal_and_the_receipt_still_runs` (no rerun after); `test_receipt_failure_modes_prevent_pass` (STOPPED receipt, extra key, wrong hash, exit 1); `test_supersedes_only_its_own_names`; `test_gates_refusal_and_hold`; `test_time_exhausted_spawns_no_work` |
| ROW 21'S GATE: `supplement_receipt_ok(current_identity)` - holds unless the supplement final is an ADMITTED PASS (marker, no abort), no terminal record, the receipt is the one the final binds with an admissible PASS and every bound output unchanged; both comparisons RE-DERIVED from the retained arrays (the reference from the frozen Stage A tree) pass and equal their receipts; the ledger is exactly two completed single tries at carry + 2; the input is exactly input 00; and the CURRENT execution is compatible on every `COMPAT_KEYS` field | `stage_a.supplement_receipt_ok`, `COMPAT_KEYS`, `supplement_compatibility`; desk: `stage_a.py supplement-verify` | `Run.test_pass_...`: holds before the final; ok after; holds on another OS build with the same version, a different package file map with the same macOS string, changed processor code, an identity lacking a field, a changed retained comparison, an absent marker |

**Compatibility (`COMPAT_KEYS`).** macOS product version AND build, machine, Python, every watched package's version
AND per-file map hash, the snapshot files, the lens, the jlens head/diff/shim, the declared dispatch, the packet and
the processor code (`image_adapter.py`, `dose.py`, `dose_report.py`). Row 21 passes its own execution identity
(same `execution_identity` shape) and the gate compares field by field; a product-version string alone never
establishes compatibility, and a later compatibility-breaking change holds again.

## 6. Stops

A failure - a check, a comparison, an exception, a resource stop, an interruption - STOPS this version:
`SUPPLEMENT_TERMINAL.json` (first reason kept, later ones appended), no release path, no recovery file, no retry, no
tolerance revision, no search for another input. Counters and results stay as they are; the receipt worker still
runs and records STOPPED; row 21 holds. A refusal before any start (a gate) runs nothing and charges only time.
Stage A's own `TERMINAL.json` and its release are never written by the supplement.

## R2. Revision 2: no post-start resumption, ever (Codex `478196f` P1)

Codex accepted the separate carried tree and ledger and found that inherited controller paths could STOP without the
terminal record - a receipt worker's failure, an unreadable native exit peak, a controller crash or hold after the
instrumented commit - after which a later session superseded the STOPPED final, skipped the DONE phases and could
regenerate PASS, even with a mandatory native exit-peak measurement lost (the missing-measurement check looked only at
the current session). Revision 2 makes the supplement ONE SESSION FROM ITS FIRST START:

| Item | Where | Fixture (no forward) |
|---|---|---|
| THE RESTART RULE, before anything is moved or spawned: an admitted PASS is final - a later invocation refuses and never supersedes or regenerates it; any start in the supplement ledger without an admitted PASS means an earlier post-start session ended STOPPED, held, crashed or interrupted - this session writes SUPPLEMENT_TERMINAL.json at once (whether or not the first terminal write landed), so no endpoint is dispatched and the receipt can only say STOPPED | `SupplementController._supersede`, `_post_start`, `_terminalise` | `Restart.test_receipt_exit_then_restart`, `test_non_pass_receipt_then_restart`, `test_missing_native_exit_peak_then_restart_even_without_the_terminal` (the terminal deleted before the restart), `test_hold_after_the_instrumented_commit_then_restart`, `test_controller_crash_after_the_instrumented_commit_then_restart` (SIGKILL, the crashed session charged); `Controller.test_a_pass_is_never_superseded_or_regenerated`. Each: no endpoint worker in the new session, counters unchanged (196 or 195), time carried and charged, STOPPED |
| In-session: a hold after a start, and a STOPPED final after a start (receipt failure, a non-PASS receipt, a missing measurement, an illegal ledger), are terminal at once (best effort; the restart rule does not depend on it) | `_hold`, `_finalise` | the same Restart fixtures (the terminal present after the first session) |
| Missing mandatory measurements are counted over EVERY session of this tree: a native exit peak lost in an earlier session keeps every later final STOPPED | `SupplementController._missing_measurements` | `test_missing_native_exit_peak_...` (the restart's final still lists it) |
| The workers refuse too: an endpoint already started (any status, any session) is never reloaded or continued, and native requires the instrumented commit of its OWN session | `stage_a._never_resumed`, `admit_supplement_instrumented` | `Run.test_a_started_endpoint_is_never_resumed` (replaces revision 1's reload test, which Codex noted contradicted the contract), `test_native_needs_the_instrumented_commit_of_its_own_session` |
| Row 21's verifier now re-derives the COMPLETE comparison receipts (the worker's own `comparison_a` / `comparison_b`, equal field for field), re-validates all three records with `_validate_record`, and runs `check_stage_a_frozen`. Stated limit: the parent pins are eight metadata hashes, the tree's total bytes and the reference checksums - not a whole-tree digest; Stage B keeps its own parent-acceptance gate before CAL. | `supplement_receipt_ok`, `comparison_a`, `comparison_b` | `Run.test_pass_both_comparisons_receipt_and_row21_verifier` (a changed retained receipt holds) |

The closed Stage A resumption policy (Controller) is unchanged; the rule lives only in SupplementController. Moves in
revision 2: stage_a.py, stage_a_controller.py, this file, READINESS_ROW20S.md and therefore the supplement identity and
package (the plan and budget unchanged).

## R3. Revision 3: the stop is derived, not written (Codex `1abb851` P1)

Codex credited §R2 and found that a restart whose terminal RECREATION failed before its rename only appended a stop
entry; the base superseder then ran, the gates saw no terminal file, both DONE endpoints were skipped and a new receipt
and final could regenerate PASS. Revision 3 makes the decision structural:

| Item | Where | Fixture (no forward) |
|---|---|---|
| `_prior_start_evidence` reads every durable trace of a start from the records themselves - ledger attempts (or an unreadable ledger), an endpoint worker record in controller.json (revision 4: any, whatever its released flag), an endpoint phase record, a pass output, a comparison receipt, the terminal record. Any of them without an admitted PASS sets the REFUSAL in `_supersede`: nothing is superseded; `_gates` returns REFUSED before any worker; `_phase` and `_finalise` refuse outright if ever reached; the session closes charged ("refused", exit 2). SUPPLEMENT_TERMINAL.json is written as the RECORD of that state; if the write fails the refusal stands and says so. | `SupplementController._prior_start_evidence`, `_supersede`, `_gates`, `_phase`, `_finalise` | `Rev3Adversarial.test_crash_with_completed_endpoints_and_a_failing_terminal_write` (both endpoints + DONE committed, controller SIGKILLed during the receipt, terminal absent, the restart's terminal write failing before its rename: REFUSED, no worker, final/receipt/ledger bytes unchanged, the crashed session charged, terminal still absent); `test_receipt_failure_then_lost_terminal_and_a_failing_rewrite`; the five §R2 Restart cases now expect REFUSED with no worker at all |
| A PASS needs BOTH endpoints committed by THIS session: the controller (`_endpoints_this_session`), the receipt worker, and row 21's verifier (endpoint sessions = the admitted final's session) | `_finalise`, `run_supplement_receipt`, `supplement_receipt_ok` | `Rev3Adversarial.test_a_pass_needs_both_endpoints_from_this_session` |
| MY ADVERSARIAL LIST - every way found to bring a second session to an endpoint, a receipt or a final after a start, each refused before any worker: (1) completed endpoints, crashed during the receipt, terminal write failing; (2) receipt failure, terminal lost, rewrite failing; (3) ledger deleted, DONE records remain; (4) ledger and DONE deleted, controller.json's released endpoint workers remain; (5) unreadable ledger; (6) a PASS final whose marker never landed; (7) a PASS final with this session's abort tombstone; (8) a controller built without gates (`_phase` refuses; no worker); (9) endpoints from another session (no PASS); plus the §R2 cases: receipt exit, non-PASS receipt, a lost native exit peak, a hold and a SIGKILL after the instrumented commit; and an admitted PASS is never superseded or regenerated | — | `Rev3Adversarial` (8), `Restart` (5), `Controller.test_a_pass_is_never_superseded_or_regenerated` |

Outside the controller's reach, stated plainly: deleting controller.json while any other file remains is refused by
the base controller's accounting check before anything runs (unchanged). Deleting the WHOLE supplement tree makes it
indistinguishable from a fresh one: a new run would start again from the pinned carry, and the earlier starts, time and
results would be lost with the tree. That is an operator act, not a controller path; the review record and the R052
tracker are where such a loss would be caught.
The base Controller and the Stage A policy are unchanged; the rule lives only in SupplementController.

## R4. Revision 4: the release-evidence class (Codex `410b580` P2)

The base `_phase` persists an endpoint worker record with `released=False` (identities durable) BEFORE it writes GO, and
sets `released=True` only in memory afterwards; the first durable true snapshot comes with a later heartbeat. A SIGKILL
in between leaves `released=False` although the worker may have received GO; revision 3 read that as no start.
Revision 4 takes Codex's narrow option: ANY durable record of a supplement endpoint worker is start evidence, whatever
its flag. The boundary is structural: before that record is persisted no GO can have been sent (GO follows the persist),
so a crash before it is genuinely pre-start; at or after it, the session refuses. The same records require their exit
peak in `_missing_measurements`. The release-intent alternative is not needed: the existing pre-GO persist already IS
that intent, and reading it as such removes the ambiguous window without another write. Base Controller unchanged.

| Item | Where | Fixture (no forward) |
|---|---|---|
| Any durable endpoint record (released or not) -> "a durable endpoint worker record" -> refusal | `_prior_start_evidence` | `Rev4ReleaseEvidence.test_crash_after_go_before_the_released_snapshot_live_worker` (open session of a dead controller, endpoint record released=False with a live leader and watchdog: the restart reconciles - kills the group, charges the crashed session - then REFUSES with no worker of any phase, nothing started or generated); `..._dead_worker` (the same with the leader already gone) |
| The pre-persist boundary is not a start | — | `test_the_boundary_before_the_endpoint_record_is_not_a_start` (a dead session whose last durable record is the gates worker: the restart runs to PASS) |
| An unreleased endpoint record needs its exit peak | `_missing_measurements` | `test_an_unreleased_endpoint_record_needs_its_exit_peak` |
| Isolated histories Codex noted were not fixtured alone: pass output only, comparison receipt only, terminal record only - each refused (with the terminal write failing) | `_prior_start_evidence` | `test_pass_output_only`, `test_comparison_receipt_only`, `test_terminal_record_only` |

Coverage, stated precisely (Codex `410b580`): the revision-3 deletion and unreadable-ledger cases assert the refusal,
the evidence named and no worker in the new session, not every byte; the without-gates case expects SystemExit and leaves
its own session open for the next start's crash charge; the foreign-session case tests the predicate, not an end-to-end
final; the admitted-PASS refusal is a SystemExit charged as a pending start. These are the assertions they make.

## R5. Revision 5: release intent is append-only, outside every replaced record (Codex `f716bea` P2)

`_persist` snapshots controller.json under one lock and writes it under another, so an older gates I/O snapshot can be
published after the endpoint's persist and GO, replacing the record that carried the release intent. Revision 5 takes
the separate-record structure: before GO, `SupplementController._arm_watchdog` (called by the base `_phase` after the
watchdog arms and before its persist and GO) publishes `intent/<endpoint>.json` with O_CREAT|O_EXCL, fsyncs it and its
directory; it is never rewritten (a second create raises) and never deleted by the controller. If it cannot be created
the phase stops and the gated worker, which has run nothing, is killed: no GO. Restart evidence
(`_prior_start_evidence`: "a release-intent record", an unreadable or partial entry included), mandatory measurements
(`_missing_measurements`: every intended endpoint needs its exit peak in the controller record) and recovery
(`_reconcile_intents`: the intent's leader group and watchdog ended and confirmed gone, even when the controller record
no longer names them) all read it. No intent file = no endpoint started, so a genuine gates-only refusal stays a
distinct, resumable case. Base Controller unchanged; refusal independent of the terminal write.

| Item | Fixture (`Rev5ReleaseIntent`, no forward, the write order driven explicitly) |
|---|---|
| A stale gates-only snapshot published after the endpoint's release, then a crash (controller and the endpoint's watchdog SIGKILLed, the GO'd worker left alive): the restart refuses from the intent, ends the lost group from the intent's identities, charges the crashed session, starts and regenerates nothing | `test_stale_unmeasured_gates_snapshot_after_the_endpoint_release`, `test_stale_measured_gates_snapshot_after_the_endpoint_release` (tearDown asserts the recovered worker is gone) |
| A rolled-back record still needs the intended endpoint's exit peak; the intent cannot be re-created | `test_rolled_back_record_still_needs_the_intended_exit_peak` |
| An intent with no endpoint record at all (crash on either side of GO): refused | `test_intent_present_on_both_sides_of_go` |
| An intent that cannot be created: STOPPED, the endpoint never released, its worker never ran, no ledger | `test_intent_that_cannot_be_created_sends_no_go` |
| A gates-only refusal leaves no intent; a later run proceeds to PASS (and then holds both intents) | `test_gates_only_refusal_leaves_no_intent_and_a_later_run_proceeds` |

SELF-AUDIT - where supplement start or measurement evidence lives in a whole-file-replaced record, and why it cannot
now regress to a dispatch or a PASS:
1. Endpoint worker records in controller.json (the release intent): now duplicated in the append-only intent file,
   which restart, measurement and recovery read. Closed.
2. Exit peaks in controller.json: a stale snapshot can drop one; every intended endpoint requires its peak, so the
   loss can only make the final STOPPED (and a restart refuses on the intent) - fail closed, never a PASS.
3. Session time in controller.json: a stale open-session snapshot carries an older beat; the restart's crash tail runs
   from that beat to min(now, the guardian's deadline + 5 s) and is never under 60 s, so time is re-charged, not lost;
   a stale snapshot published after a close re-opens the session and the next start charges it as crashed.
4. The supplement ledger (stage_a_state.json): written only by the worker processes, one phase at a time, each write
   extending the state it read at open; the controller never writes it. Monotonic.
5. Phase records, pass outputs, comparison receipts, the receipt, the intents: write-once files; the terminal record is
   appended by one writer at a time. The final record and its marker are written once at finalisation; an admitted
   PASS is never superseded.
6. Guardian and watchdog records: one file per session and phase, not replaced across sessions.

## 7. Which reviewed files move

| File | Moves? | What |
|---|---|---|
| `stage_a.py` | YES | revision 16 block: the supplement plan, gates, two worker phases, receipt, verifier, desk commands; `Ctx` gains three defaulted fields; `package_at_commit`'s identity check factored into `_identity_describes_commit` (same checks, same messages). Stage A's own paths unchanged. Correction (revision 2, Codex `478196f`): Stage A's `package_at_commit(HEAD)` REFUSES once this commit moves stage_a.py and the controller (its committed identity describes the accepted `cc1d2cb` code); the accepted bundle stays bound to `cc1d2cb`. |
| `stage_a_controller.py` | YES | file and phase names as class attributes with Stage A's values; `final_admitted(out, names=None)`; `SupplementController`; `main` takes `run` / `supplement`. Stage A's own paths unchanged. |
| `tests/fake_worker.py`, `tests/test_stage_a_supplement.py` | YES (tests) | sgates / sreceipt modes; the new fixtures |
| `stage_a_report.py`, `stage_a_guard.py`, `enforce.py`, `memprobe.py`, `stage_a_watchdog.py` | no | the reader package is unchanged (its digest unaffected) |
| `stage_a_plan.json`, `manifest_dev.json`, `stage_a_positions_receipt.json`, `stage_a_identity.json`, `STAGE_A_CRITERIA.md`, `ROW20_GO.json`, `READINESS_ROW20.md`, everything under `captures/photo_stage_a/` | no | the accepted revision-15 package and run stay byte-identical |
| new | — | `stage_a_supplement_plan.json`, `stage_a_supplement_identity.json`, `stage_a_supplement_identity_files.json`, this file, `READINESS_ROW20S.md`; `ROW20S_GO.json` only from the owner after Codex |

Consequence stated plainly: because `stage_a.py` and `stage_a_controller.py` move, a fresh execution identity no longer
equals revision 15's `stage_a_identity.json`, so `stage_a_controller.py run` (Stage A) would refuse at its gates. That
is intended - Stage A is complete and accepted; its package is now a record.

## 8. Running it (after Codex's record and the owner's go only)

    .venv-image/bin/python stimuli/photo/stage_a_controller.py supplement
    .venv-image/bin/python stimuli/photo/stage_a.py supplement-verify     # desk: the row-21 gate on this machine

## 9. The attestation block for Codex (the shared v1 format, `stage_a_guard.parse_attestation`)

    <!-- STAGE-ATTESTATION v1
    {"row": "20", "stage": "A-supplement", "verdict": "favourable", "reviewer": "...", "date": "YYYY-MM-DD",
     "reviewed_commit": "<40-hex>", "package": {"budget_sha256": "...", "manifest_sha256": "...",
     "plan_sha256": "...", "supplement_criteria_sha256": "...", "supplement_identity_sha256": "...",
     "supplement_plan_sha256": "..."}}
    -->

`ROW20S_GO.json`: exactly `review {commit, path, record_sha256}`, `owner_go {by, date, words}`, `package` (the six).

## 10. Forecast and scope

Two forwards (instrumented ~1 s, native ~1 s measured in Stage A) plus two model loads, four identity hashings
(~8 s each) and the 60 s charged closure: a few minutes against 12,062 s of row 20 remaining, phases ending at the
cap less 720 s; task memory about 31 GiB per phase against the 44 GiB stop; about 10 MB written against the
677 MB of row-20 storage remaining.

Passing this exposed one-input sentry does not isolate OS causality, establish all-image or all-edit qualification,
reproduce the 120 shams on the new OS, or admit PILOT. It supplies the specific missing bridge before row 21 measures
its own finite engineering gates. Row 21 independently keeps its accepted-report / manifest / identity / review / go,
192-endpoint CAL and fitting <= 1 h, remaining-stage forecast <= 11,520 s and full resource gates. No Stage B forward
is approved here.

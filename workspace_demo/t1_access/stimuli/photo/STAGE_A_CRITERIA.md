# Stage A (ledger row 20): declared criteria and code, revision 6 (R084, 2 October 2026)

**Specification:** framework `rsc_t1_two_channel_framework.md` §8.2, §8.4 and §8.6 (Unimog; R052's text).

**History.**

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | RSC `79343d9` | RSC `f9d2ef3` | NOT ON BOARD |
| 2 | RSC `e598f96` | RSC `69539bb` | NOT ON BOARD |
| 3 | RSC `a59fc2d` | RSC `081f17b` | NOT ON BOARD |
| 4 | RSC `d7a486a` | RSC `1bf9890` (combined with the AI reader) | NOT ON BOARD |
| 5 | RSC `2610d8a` | RSC `b569f8a` (combined) | NOT ON BOARD; A1, A7, A8 closed; the memory qualification accepted in principle |
| 6 | this commit | — | answers R052's handoff `c39df47e`: Stage A conditions 1–4 of `b569f8a` (§0 below) |

No review record of a not-favourable verdict can be named by a go: the guard's supplementary negative list holds
`f9d2ef3`, `69539bb`, `081f17b`, `1bf9890`, `b569f8a` (row 20) and `cf3e49e`, `7048bb8`, `5a8d7ac` (AI reader). The general
rejection is the absence of a positive, exactly matching attestation.

**Not reopened** (accepted by Codex at `1bf9890`): the hashes and their relations, the shared strict guard (no schema
objection), the attestation v1 format, the inputs, cases, positional rule, transaction, statistic, engineering carry
and envelope; the sum-of-lifetime over-count as an early-stop convention; live-bound full logits and features; the two
tiny unreserved writes; the power-loss tail as an accounting rule; at `b569f8a` also A1, A7, A8, the startup and
immediate-restart repairs, the final aggregate and pre-native admission, and the memory qualification in principle.
The plan (revision 5), inputs, cases and the 178 planned attempts are byte-identical to revision 5.

**No forward has run on any development image.** Every mechanism measurement below is from declared, non-development
fixtures: synthetic worker processes, the real watchdog, synthetic arrays; no model and no image
(`controller_fixtures.json`, recorded 2 October 2026).

## 0. Revision 6: the four conditions of RSC `b569f8a`

| # | Condition | Where it lives | Fixtures (`tests/test_controller.py` unless named) |
|---|---|---|---|
| 1 | Kill before any I/O wait; guard the first sample | `_sample` catches every stop and SIGKILLs the group itself (`_kill_now`) before the `finally` that disarms the tick check and joins the I/O thread, and before `_phase` persists; it records the last admissible observation (`stop_observed_mono`, the start of the deciding iteration), the kill and the leader's death (kqueue, no file I/O). The watchdog's tick check is armed by a tick written immediately BEFORE `GO`, so the first sample is guarded; after the kill the watchdog stays active (controller death, beat, deadline, group-and-member retirement) until extinction. | `test_memory_stop_with_blocked_io_kills_first` (I/O thread blocked forever; the worker gone 0.008 s after the last admissible observation, timed by the test, independent of the controller); `test_never_returning_first_and_later_sample` (sample 1 and sample 3 never return: group gone, controller killed); `test_sampler_unavailable_and_slow` (killed by the sampler itself, leader dead < 0.5 s) |
| 2 | An independent whole-controller deadline | A GUARDIAN (`stage_a_watchdog.py` in guardian mode) is started before the lock and any load, with a setup deadline (300 s), then moved to the session's cap + 5 s (at least the finalisation allowance + 5 s); on it, it SIGKILLs the controller by identity and records the death. Its path depends on no observation or persistence. The per-phase watchdog now kills the (alive) controller also on a stalled sampler. Crash charge: the guardian's and the watchdog's controller-death times; a blocked controller never seen to die is charged until the restart; the power-loss rule unchanged. | `test_persistence_after_the_watchdog_retired_is_bounded` (a controller-only persist blocks forever after the gates' watchdog retired: killed by the guardian at the shortened cap, run 18.7 s; the restart charges to that death); `test_never_returning_first_and_later_sample` |
| 3 | Bound the abort path | `_abort_exit`: revocation - an abort tombstone `STAGE_A_FINAL.ABORTED.json` naming the session, and the removal of the session's marker - runs in two threads for at most 5 s, then exit 75 whatever they did; `final_admitted` refuses a session with a tombstone. Neither revocation step is followed by a directory fsync, so its durability across a power loss is limited; if both block or fail, a marker can survive an exit 75. | `Finalisation.test_post_marker_stall_and_blocked_revocation_are_bounded` (the marker's write stalls after its rename: exit 75 in 10.6 s (allowance 4 s + the stall; 15.6 s with the unlink blocked), tombstone present, not admitted; the same with the unlink blocking forever: the marker survives, the tombstone refuses it) |
| 4 | The consumed recovery history | `enforce.check_ledger`: every consumed recovery an exact, typed, unique (attempt, try) entry whose authority (the owner's recovery file: attempt, session, try, owner, date, reason, file hash) names exactly it and a try the attempt has; every try of an attempt before its last must have such a recovery; outstanding interrupted entries name the last try; the open attempt's kind and session coherent. Used by pre-native admission, the final validator and the controller's final algebra. | `test_stage_a_runner.ValidatorMutations.test_codex_unauthorised_extra_try` (Codex's 195-of-200 counterexample refused in final and pre-native admission; an authority naming another try, a bool try, a missing field, a duplicate; legal with its authorised recovery); `StageA.test_crash_recovery_is_per_try_and_consumed` (the honest two-recovery history is legal) |

**The memory qualification (revision 6, end to end).** The enforced bound between two readings of a process is
0.12 s (0.16 s if the sampler stalls, through the watchdog's 0.1 s tick check and 10 ms poll); the kill is now sent by
the sampler at the decision, with no wait in between. The measured SIGKILL delivery (0.025 s kill → exit in the overshoot fixture) is evidence,
not a bound. Measured end to end with the I/O thread blocked: 0.008 s from the last admissible
observation to the worker's death. The 4 GiB headroom therefore covers growth up to about 4 GiB / (0.16 s + delivery)
≈ 22 GiB/s; one synthetic thread (11.1–14.7 GiB/s in two runs) fits, 2–8 threads (32–75 GiB/s) do not. This is the declared,
measured qualification Codex accepted in principle (RSC `b569f8a` Question 2) for this local Stage A: Stage A
reports the model's actual growth and peak; any cap, pressure or fidelity failure stops and is preserved; a faster
allocation episode or an overshoot invalidates the qualified claim and grants no Stage B authority.

## 1. The conditions A1–A8 of revision 5 (RSC `1bf9890`): where each lives

### A1 — every worker consumes and checks its own map; identity rechecked before completion

- **Gates** (`stage_a.desk_gates`): after the fresh identity equals the frozen one, the gates' own import map
  (`identity_files.gates.json`) is consumed by `check_imported_origins(map, identity.package_file_maps_sha256)`; the
  identity is rechecked (`recheck_identity`: local code, packet, plan, manifest, receipt) before GATES.json is
  committed.
- **Report** (`stage_a.run_report`): the map `worker_identity` returns is consumed and checked the same way; the
  report's `build` calls the recheck immediately before it writes `REPORT_RECEIPT.json` — a source change during
  report construction leaves no receipt, so no current report and no PASS.
- Instrumented and native: unchanged (map consumed after load, recheck before the phase record).

Fixtures (`tests/test_stage_a_runner.py`): `StageA.test_gates_consume_their_map_and_recheck` (an origins refusal and a
recheck failure each leave no GATES.json), `test_report_consumes_its_map_and_rechecks_before_the_receipt` (the map
check is called; a recheck failure leaves the report and both figures but no receipt).

### A2 — guarded startup, armed safeguard, whole-group restart

- **One cleanup owner from before the first spawn** (`stage_a_controller._phase`): the worker is spawned behind a start
  gate (a shell that execs the worker only after reading `GO` on stdin; EOF → exit 97, nothing ran); then the exit
  watch, the worker's identity (pid + start), the watchdog — given the controller's and the leader's identities — which
  must print `ARMED` within 10 s and whose identity is read, and the durable record holding both identities; only then
  is `GO` written. A failure at any step ends and reaps the gated worker, which has run nothing.
- **No phase starts while an earlier handle exists:** a leftover worker or watchdog is ended (whole group, reaped)
  first.
- **The watchdog checks its controller by identity** (pid AND start time) at arming and on every poll, and on firing
  kills, at once, every live member of the worker's group (enumerated by `memprobe.end_group`, anchored to the recorded
  leader identity) and every identity in the members file the controller keeps (escaped descendants); a stale beat or
  the hard deadline also kills the blocked controller, by identity, after the group.
- **Restart** (`_reconcile`): for each recorded worker of the crashed session, every live member of its process group
  is enumerated — not only the recorded ones — anchored to the leader's identity (XNU never reuses a pid that is still
  a process-group id; a live process holding the leader's pid with another start time means the group is extinct),
  killed with every recorded member, and confirmed gone; **only then** is the watchdog killed and confirmed gone.
  A crash between spawn and the first persist leaves an unreleased gated worker whose stdin closes with the controller
  (exit 97) and, if armed, a watchdog that kills its group on the controller's death.

Fixtures (`tests/test_controller.py`): `Startup` — exit-watch failure, watchdog spawn failure (no ARMED), first-persist
failure (each: the instrumented worker never released, ran nothing, is dead and reaped; the run STOPS), a leftover
handle ended before the report phase; `Controller.test_immediate_restart_kills_unrecorded_group_members` — a recorded
live leader with a child no record names, and a live watchdog: the child is killed, the watchdog last; the same with
the leader already exited and only the unrecorded child holding the group;
`test_stale_worker_reconciled_by_identity_only` (a recorded pid whose start differs is never signalled).

### A3 — one task aggregate, mandatory final measurements, the margin

- **By identity:** every sampled process's lifetime maximum is kept under its identity (`member_max`, pid:start); the
  leader's exit maximum, read from the exited, **unreaped** process, is folded in. The phase aggregate = Σ member maxima
  + the controller's lifetime maximum; `task_lifetime_sum` is the maximum over phases and live samples; at
  finalisation the controller samples itself again and the **task aggregate** = max over this session's workers of
  (Σ member maxima) + the controller's final lifetime maximum. A phase whose aggregate reaches the stop at the worker's
  exit stops.
- **Mandatory:** PASS requires every released worker's exit peak and the controller's final self sample; a missing
  one is listed in `missing_measurements` and the outcome is STOPPED.
- **Prompt stops:** every controller stop SIGKILLs the worker's group at once (no SIGTERM grace); the watchdog too.
- **The sampler does no file I/O:** the main thread samples (sleep 0.02 s; an iteration whose work exceeds 0.05 s
  stops) and ticks a pipe to the watchdog; a separate I/O thread persists and sums the storage. A hung sampler (no tick
  for 0.1 s) makes the watchdog kill the group.

**The observation-to-death interval** — superseded in revision 6 by §0 (the sampler now kills at the decision, before
any join or persist; the first sample is guarded). Measured (`controller_fixtures.json`, revision 6):

| Measurement | Value |
|---|---|
| Largest sampling iteration's work over a full run | 5.2 ms (gates 3.2, instrumented 3.9, native 4.6, report 5.2 ms) against the 50 ms limit |
| Memory stop (whole task): last admissible observation → leader dead | 0.009 s (0.062 s to verified extinction) |
| Memory stop with the I/O thread blocked: last admissible observation → worker gone (timed by the test) | 0.008 s |
| Never-returning sample 1 / 3: watchdog observation → group gone; → controller gone | 0.033 s / 0.033 s; 0.048 s / 0.046 s |
| SIGKILL overshoot of a writer growing as fast as one thread can (killed at a 4 GiB reading) | 0.001 GiB (observed 4.122, exit peak 4.122 GiB; kill → exit 0.025 s) |
| Growth rate, one thread / 2 / 4 / 8 threads (numpy touch) | 11.1 / 32.0 / 53.1 / 66.8 GiB/s (revision 5's run: 14.7 / 36.2 / 58.1 / 75.0) |

Fixtures: `test_exit_peak_enters_the_task_aggregate` (the 1 GiB exit spike is in `member_max`, `task_lifetime_sum`
and the final aggregate, not only a side field), `test_exit_spike_over_the_stop_stops`,
`test_missing_mandatory_measurements_refuse_pass` (exit peak unreadable; controller self sample unreadable),
`test_memory_stop_is_whole_task`, `test_hung_sampler_watchdog_kills_on_stale_ticks`,
`test_sampler_unavailable_slow_and_blocked`.

### A4 — the whole-controller clock

- **From the process's start:** the session's live seconds count from the controller process's own start (libproc
  start time), before configuration, recovery and superseding.
- **Close and finalisation are charged and bounded:** the close charges, at once, `FINAL_ALLOWANCE_S` = 60 s for
  everything after it (receipt and ledger reads, hashing, scans, the final record and its marker); close and
  finalisation run under a timer of that length — past it the process ends with exit 75 after removing any admission
  marker of the session. The storage scan precedes the close's time sample.
- **Crash charge:** the dead session's last durable live time + max(60 s, the watchdog's interval from the last beat to
  the group's **and the controller's** death). A watchdog that found the controller blocked (stale beat, hard deadline)
  kills it, so the interval is bounded and recorded; if it could not see the controller die, the charge runs until the
  restart. A power loss stays the declared 60 s accounting rule.
- **Lost or invalid accounting refuses:** an absent controller.json beside any existing task output; non-finite,
  negative or mistyped carry, totals, session times or beat; a total below the carry; a carry other than the declared
  one.

Fixtures: `test_crash_tail_charge` (declared, measured-longer, and blocked-never-seen-to-die tails),
`test_blocked_writer_watchdog_bounds_worker_and_controller` (group and controller killed),
`Finalisation.test_lost_and_invalid_accounting_refused` (absent record beside output; NaN, negative, wrong carry,
mistyped session), `test_post_rename_block_is_bounded_and_not_admitted`, the allowance charged in the PASS fixture.

### A5 — durable completion

`STAGE_A_FINAL.json` is written first; then, only if the output tree's size equals the declared figure (which includes
the record and its marker), `STAGE_A_FINAL.ADMITTED.json` names the final record's sha256 and session.
**`stage_a_controller.final_admitted(out)`** admits a final record only with that marker. A failure or block after the
final record's rename leaves no marker; a failure after the marker's own rename removes the marker before exit 75; a
size mismatch rewrites the record STOPPED, with no marker. Earlier finals and markers are superseded at every session
start.

Fixtures (`Finalisation`): failure before the final write; **post-rename exception** (the bytes say PASS, not
admitted, exit 75); **post-rename block** (bounded by the allowance, exit 75, not admitted); **marker failure after its
rename** (marker removed); **size mismatch** (STOPPED on disk, not admitted); `test_stale_pass_superseded`.

### A6 — legal ledger domains and full instrumented admission before native work

- **`enforce.check_ledger`** (used by the validator and the controller's final algebra): exactly four non-negative
  integer counters per row and aggregate (never bool or float); completed + failed ≤ started; passes ≥ started × the
  declared passes per try; aggregate = row 20 + row 21; every attempt with exactly kind, passes (= the declared 1),
  status (open, completed, interrupted, interrupted with recovery consumed, failed…) and tries ≥ 1; the completed map
  equal to the completed statuses; the open attempt coherent with its entry; interrupted entries and consumed
  recoveries coherent with the statuses; the row recount from tries and carry; row 21 zero in a row-20 ledger.
- **Pre-native admission:** before any native model is constructed, `admit_native` runs the complete instrumented
  validator (`stage_a_report.validate(..., phases=("instrumented",))`: ledger domains, every instrumented record and
  array under the full predicates, cross-case, 120 bitwise, suffix and encoder criteria, INSTRUMENTED_DONE).
- **Resumed records:** a committed record reloaded on resumption passes its phase's full predicates before use.
- **Predicates added:** requested ranks integers in [1, vocabulary], never bool, agreeing with the top-k and with the
  order of their logits (ties by ascending id, the capture's rule); top-k ids distinct integers in [0, vocabulary) with
  finite non-increasing logits; the final-logit dtype one of the capture's names (bfloat16, float16, float32) and the
  same on every record.

Fixtures: `ValidatorMutations.test_codex_ledger_counterexample` (all tries 0, per-try passes 1, started 16, passes 16,
completed 193, failed −177, row 21 zero, aggregate = row 20: refused), `test_coherent_zero_negative_and_typed_states`
(ten coherent or typed mutations), `test_ranks_top_k_and_logit_dtype`;
`StageA.test_consistent_nonplain_change_refused_before_native` (a non-plain `input_ids_sha256` changed with record,
ledger and phase-record hashes updated: refused, the native factory never called),
`test_resumed_record_admitted_by_the_full_predicates` (a bool rank in a reloaded record refused).

### A7 — exact report membership

The receipt must have exactly `session, package, identity, date, outputs, admissible, validator_pass`; its outputs
exactly the two SVG figures, the Markdown and the machine JSON, each matching on disk; the machine JSON's session and
flags equal to the receipt's; the session and the gates' package and identity current. The report always writes both
figures (an empty plot after a stop).

Fixtures: `Finalisation.test_report_failure_modes_prevent_pass` — machine JSON then failure, a wrong output hash,
another session, worker failure, **figures and Markdown removed with the receipt consistently trimmed**, an extra
receipt field, a receipt flag that differs from the machine report.

### A8 — declarations: provenance, source records, the audit scorer

- **Provenance snapshot vs current pin.** `manifest_dev.json`'s `execution_identity` is the **construction snapshot**
  taken when the manifest was last built (RSC `a59fc2d`): its `provenance_checks_sha256` `84abf361…` names the
  provenance record as it was then. The plan's `provenance_checks_sha256` `0085d38e…` pins the **current** record,
  revised at RSC `859262f` (revision 4) only in its `stock_matches_note` wording (a first crawl "does not establish the
  upload date or a later upload"); no check entry changed. The moved field is the plan's provenance pin (it moved the
  plan hash at revision 4); the manifest and its records for the eight Stage A inputs are unchanged and
  pinned record by record in the plan.
- **Admission policy (enforced, `stage_a.load_frozen`):** the frozen plan and manifest are the reviewed immutable
  records (both hashed in the package), and the **current** `dev_pool.json` and `provenance_checks.json` must be
  byte-identical to the plan's pins; a later change to either refuses until a new plan is reviewed.
- **Audit scorer code (a before-audit condition, not a Stage A gate):** `audit_package.py` binds the live classifier
  and normalisation source — `ai_reader_score.py`, `ai_reader_key.py`, `audit_alias_map.py` — and the map's pinned hash;
  the audit package records `audit_package.identity()` when reviewed, and `audit_package.score(..., pins=)` refuses on
  any difference. The frozen map and its construction record are unchanged.

Fixtures: `StageA.test_source_records_pinned`; `test_ai_reader.AuditMap.test_scorer_code_bound_in_the_audit_package`.

## 2. Revision 4 mechanisms still in force

The strict shared guard (`stage_a_guard.require_go`: exact key sets, typed values, commit objects, one closed block,
mandatory reviewed-commit re-derivation, descent and date order); the reviewed-package builder proving the identity–blob
relation (`stage_a.package_at_commit`); the positions receipt's three refusals; every writer's storage reservation
(work under cap − 64 MiB, finalisation under the full cap); the validator's per-record, ledger, membership, phase-record
and recomputed-criterion checks (`ValidatorMutations`, `GoAttestation`, `ReviewedPackageBuilder`, `Units`); crash
reconciliation into interrupted tries and the authorisation hold (HELD ≠ REFUSED ≠ STOPPED); the report reading the
ledger without authority; the MLX cache counted (2.0 GiB cache in a 4.222 GiB ledger; 2.222 current against 4.222
lifetime after a fall); the B prediction recomputed at finalisation; the interpretation item validated.

**Other mechanism measurements** (`controller_fixtures.json`, revision 6):

| Fixture | Result |
|---|---|
| Deadline, worker ignoring SIGTERM with a grandchild | SIGKILL at once; kill → reap 0.002 s; grandchild dead |
| Deadline, worker busy in 4096² MLX matmuls | kill → reap 0.002 s |
| Controller SIGKILLed during active work | worker and grandchild gone 0.030 s after the kill; restart reconciles, charges ≥ 60 s, PASSes |
| Controller writer blocked forever | stale beat: group gone 0.035 s and the controller 0.050 s after the observation |
| Immediate restart with an unrecorded live member (leader alive / leader exited) | every member killed, the watchdog retired last |
| Persistence failure | exit 75 in 6.1 s, first reason durable, no final record |
| Post-rename block of the final record | exit 75, not admitted, run 10.6 s (allowance set to 4 s in the fixture) |
| Whole PASS run (four synthetic workers, guardian included) | 6.0 s |

## 3. Inputs, cases, tolerances and stops

Unchanged from revision 4 (and 3, 2): relative L2 ≤ 0.01 per marker layer (FP32 in FP64, instrumented norm as
denominator), maximum E1 logit difference ≤ 0.10, identical argmax, the within-path cases bitwise equal to plain. The
envelope: 16 carried + 140 + 16 + 2 + 20 = **194 of 200**, 1,808.73 s carried; caps A 200 / 4 h / 1 GiB, task
memory 48 GiB (stop 44 GiB).

## 4. Running it (after the go only)

```
.venv-image/bin/python stimuli/photo/stage_a_controller.py run     # exit 0 PASS/STOPPED, 2 REFUSED, 4 HELD, 75 no final
```

A PASS is read only through `stage_a_controller.final_admitted(captures/photo_stage_a)`.

## 5. The attestation block (agreed by Codex at `081f17b`; unchanged)

```
<!-- STAGE-ATTESTATION v1
{"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "<reviewer name and session>",
 "date": "YYYY-MM-DD", "reviewed_commit": "<40-hex RSC commit of the reviewed package>",
 "package": {"criteria_sha256": "...", "identity_sha256": "...", "plan_sha256": "...",
             "manifest_sha256": "...", "budget_sha256": "..."}}
-->
```

The go file holds exactly `review` {commit, path, record_sha256}, `owner_go` {by, date, words} and `package` (the
same five hashes). If one review approves both Stage A and the AI reader, each gets its own record with one block.

## 6. Tests (no model)

The retained-output run of the whole photo suite on this package is in `reviews/2026-10-02_photo_suite_rev5_run.md`
(command, exit status, counts, skips, identity, stdout/stderr).

## 7. Stated limits (not narrowed silently)

- **The memory margin** holds for growth below the rate stated in A3; it is not a guarantee against an allocator
  faster than that. The model's own peak and growth are Stage A measurements.
- **Descendants that leave the process group and exit between two samples** (20 ms apart in the controller) are not
  seen; one that persists after a sample is killed by its recorded identity, by the controller and by the watchdog,
  which retires only when the group AND every recorded member are gone. No Stage A worker forks a process that leaves
  its group.
- **The Σ-lifetime memory measure** over-counts processes whose peaks did not coincide; that can stop early, never
  late, for the processes it measures.
- **The 60 s charge for a power loss** is a declared accounting rule; with the machine up the unseen interval is
  measured by the watchdog and charged when longer.
- **The controller between phases** (no worker watchdog: setup, reconciliation, inter-phase persistence, the report
  checks) is bounded by the guardian (setup 300 s, then the cap + 5 s) and by its own timeouts (reconciliation 10 s per
  group, finalisation 60 s).
- **The completion marker's commit point** is its rename; a failure of the marker's directory fsync that is followed
  by a failure (or block) of BOTH revocation steps would leave an admissible marker after exit 75 — the residual window,
  which needs filesystem failures on both; the revocation itself (tombstone, unlink) is not directory-fsynced, so its
  durability across a power loss is limited. Exit 75 and its stderr diagnostic are preserved and reviewed as an abort.
- **The guardian's bound is the session cap + 5 s:** a controller blocked between phases (no worker watchdog) is
  killed then, not sooner; the interval is charged until its recorded death.
- **Full logits and features** are live-bound digests, not archive-recomputed.
- **Small writes outside the reservation:** the task LOCK (under 100 bytes, before storage is configured) and a
  watchdog's record (under 1 KiB, a separate process); both fit the 64 MiB finalisation reserve.

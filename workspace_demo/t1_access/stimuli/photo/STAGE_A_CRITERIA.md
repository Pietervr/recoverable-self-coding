# Stage A (ledger row 20): declared criteria and code, revision 4 (R084, 2 October 2026)

**Specification:** framework `rsc_t1_two_channel_framework.md` §8.2, §8.4 and §8.6 (Unimog; R052's text).

**History.**

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | RSC `79343d9` | RSC `f9d2ef3` | NOT ON BOARD |
| 2 | RSC `e598f96` | RSC `69539bb` | NOT ON BOARD |
| 3 | RSC `a59fc2d` | RSC `081f17b` | NOT ON BOARD |
| 4 | this commit | — | answers R052's handoff `dfdac45a`: the closure set 1–7 of `081f17b` §4 |

No review record of a not-favourable verdict can be named by a go: the guard's supplementary negative list holds
`f9d2ef3`, `69539bb`, `081f17b` (row 20) and `cf3e49e`, `7048bb8`, `5a8d7ac` (AI reader). The general rejection is the
absence of a positive, exactly matching attestation.

**Not reopened** (Codex confirmed them at `081f17b`): the attestation v1 format (no field added), the inputs, cases,
positional rule, transaction, numeric statistic, engineering carry and envelope. Inputs, cases and the 178 planned
attempts are byte-identical to revision 3; the plan moved only in `revision`, the envelope's declared controller
constants and its budget hash.

**No forward has run on any development image.** Every mechanism measurement below is from declared, non-development
fixtures: synthetic worker processes, the real watchdog, synthetic arrays; no model and no image
(`controller_fixtures.json`, recorded 2 October 2026).

## 1. The closure set: where each lives

### 1 — Approval and identity

**Strict shared guard** (`stage_a_guard.require_go`, `parse_attestation`; also the AI reader's):

- exact key sets at every level (go file, review, owner_go, attestation, package): an extra key refuses, null or not;
- strings are non-empty strings (a number or bool refuses), digests 64 lowercase hex, dates exact calendar
  `YYYY-MM-DD` (nothing truncated);
- both commit ids are 40-hex and resolve to **commit objects** (`git cat-file -t`, `rev-parse ^{commit}`);
- exactly one block: marker at a line start, JSON with no duplicate key, the closing delimiter required on its own
  line;
- attestation package = go package = package now = package **re-derived from the reviewed commit** (mandatory); the
  review record's commit descends from the reviewed commit; reviewed commit ≤ attestation ≤ review commit ≤ owner go;
- recovery files under an exact schema too.

**The reviewed-package builder proves the identity–blob relation** (`stage_a.package_at_commit`): at the reviewed
commit the identity hashes to its own `identity_sha256`, and its local-code digests (all ten files), packet, import
map, positions receipt, plan and manifest digests equal the hashes of those blobs at that commit.

**The consumed import map is bound.** Every worker (gates, instrumented, native, report) **recomputes the execution
identity itself** (~8 s), must equal the frozen identity and this session's gates identity, and writes its own
per-file map; `check_imported_origins(map, identity.package_file_maps_sha256)` refuses unless the consumed map's bytes
hash to the identity's value. Before a phase record is written, local code, packet, plan, manifest and receipt are
re-hashed against the identity (`recheck_identity`). The identity binds the new `stage_a_watchdog.py`.

**Positions receipt:** absent, failing and stale (bound to another plan) are three refusals (`check_receipt`).

**Fixtures** (`tests/test_stage_a_runner.py`): `GoAttestation` (refusal cases: unrelated package, wrong row,
not favourable, extra field, extra null key in attestation and in both attestation and go, short/uppercase digest,
truthy non-string and boolean reviewer, empty reviewer, date with a time, impossible date, short/non-hex/unknown
reviewed commit, a tree id, row as integer, no closing delimiter, delimiter not on its own line, marker not at a line
start, text after the delimiter, duplicate key, two blocks, no block, go package differs, owner go before review,
owner-date truncation, owner by not a string, record hash mismatch, short review commit, absolute record path, extra
review key, package changed since review, re-derivation differs or has a null field, review not descending from the
reviewed commit, negative-record supplement); `ReviewedPackageBuilder` (a real git repository laid out like RSC:
positive, identity not describing its map/receipt/packet/plan blobs, local code changed after the identity, identity
self-hash broken); `Units.test_consumed_map_bound_and_origins` (a rewritten consumed map admitting a shadowing copy
is refused), `test_positions_receipt_absent_failing_stale`, `test_code_changed_between_phases`,
`test_worker_identity_must_equal_frozen_and_gates`.

### 2 — Controller and recovery

**`stage_a_controller.py`** spawns every phase — **the gates included** — as a worker in its own process group, with a
**watchdog** (`stage_a_watchdog.py`) beside it in its own session. The watchdog kills the worker's group on the
controller's death (kqueue NOTE_EXIT), on a **stale heartbeat** (controller.json not rewritten for 10 s: the
controller alive but blocked by hashing, a hung call or an fsync) and at a hard deadline 5 s after the controller's
own; it records the observation, kill and empty-group wall times durably.

- **Workers cannot outlive a dead controller**; leader exit is seen by kqueue **without reaping**; after any exit —
  ordinary, stop or deadline — the **whole group** is SIGKILLed until no live member remains (an exited, unreaped
  leader makes killpg answer EPERM: measured) and every member recorded during the phase (pid + start time) outside
  the group is killed by identity and confirmed gone; only then is the leader reaped.
- **Reconciliation before any spawn:** a restart finds the crashed session's workers, members and watchdogs, kills
  those whose recorded identity still matches the live process, confirms them gone, and **never signals a pid whose
  start time differs** (an unidentified process). It then charges the tail.
- **Crash state reconciled first; hold ≠ failure:** the gates worker converts an open attempt into an interrupted try
  durably (`enforce.reconcile_open_attempt`); an interrupted try without the owner's file is a **HELD** outcome (exit
  4): no TERMINAL record, no work, no report. REFUSED (a gate refused) and STOPPED/PASS are separate outcomes.
- **The report never grants or consumes authority:** it reads `enforce.read_ledger` and describes an open or
  interrupted attempt.
- **The deadline cannot be blocked:** the controller's observation loop does no hashing or git (the gates are a
  worker), reads swap and pressure in-process (`sysctlbyname`, ~50 µs, no subprocess or timeout path), and the watchdog
  enforces both the stale-heartbeat and the hard-deadline kill independently.

**Measured** (`controller_fixtures.json`):

| Fixture | Result |
|---|---|
| Deadline, worker ignoring SIGTERM with a grandchild | SIGKILL; kill → reap **3.03 s**; grandchild dead |
| Deadline, worker busy in 4096² MLX matmuls | SIGKILL; kill → reap **3.04 s** |
| Controller SIGKILLed during active work | worker and grandchild gone **3.15 s** after the kill; restart reconciles, charges ≥ 60 s, PASSes |
| Sampler hung 25 s (controller blocked) | watchdog: heartbeat stale → group gone **3.05 s** after observation (≤ 10 + 3 s after the last beat) |
| Controller writer blocked forever | the same: group gone **3.05 s** after observation |
| Leader exits first, child ignores SIGTERM | child dead before the next phase; PASS |
| Child leaves the group (setsid) | killed by its recorded identity; PASS |
| Stale crashed-session worker | killed by identity; a live process whose pid matched but whose start time did not was **not** signalled |
| Gate refusal / authorisation hold | REFUSED, gates only / HELD, no TERMINAL, no report; resumes to PASS |
| Persistence failure | exit 75 in **9.4 s**, first reason durable, no FINAL |
| Initial system-reading failure | terminal, nothing spawned |

**The 60 s tail, justified against the measured interval.** After the last durable beat a worker can run at most
STALE_S (10 s) + TERM_GRACE_S (3 s) + the measured kill-to-gone (≤ 3.2 s) ≈ 16 s if the controller is alive but
blocked, and ≈ 3.2 s after its death. A restart charges max(60 s, the interval its watchdog recorded from the last
beat to the empty group). A power loss stops everything at once; then the 60 s is the declared allowance for the
unrecorded part of the last beat interval (1 s nominal).

### 3 — Whole-task memory

- **Scope:** the controller, the watchdog, the worker and every process in its group or descended from it
  (`memprobe.task_processes`, libproc), summed as **Σ lifetime maxima** — per Apple's XNU, `ri_lifetime_max_phys_footprint`
  covers one task, so the sum bounds the task's simultaneous peak from above. Sampled through the gates, load,
  execution and the report (all workers); the controller samples itself at close.
- **Final peak before reap:** the leader's lifetime maximum is read from the exited, **unreaped** process (kqueue
  reports the exit without reaping). Measured: a worker that touched 1 GiB and exited faster than a sample showed
  **1.057 GiB** exit peak; a child that touched 2 GiB showed **2.057 GiB** before its reap.
- **Validation:** lifetime > 0; current > 0 for a live process; the kernel updates the maximum lazily (measured once
  **above** it just after exec: current 4,112,816 > lifetime 4,096,432 bytes), so the reading is max(lifetime, current)
  and the lag is flagged — never trusted downward.
- **The MLX cache is covered:** a nonzero **2.0 GiB** MLX free-buffer cache plus 1 GiB host and 1 GiB MLX active read
  **4.222 GiB** (4.0 allocated + 0.22 baseline); with the cache disabled (`set_cache_limit(0)`) the current ledger fell
  to **2.222 GiB** while the lifetime maximum kept **4.222 GiB** (retention after a real fall).
- **The stop margin, justified:** the measured full observation interval (one loop iteration) is at most
  **0.113 s**; the fastest synthetic growth measured is **12.7 GiB/s**; so at most **1.43 GiB** can grow unseen within
  an interval, against the 4 GiB headroom (stop at 44 GiB of the 48 GiB cap). A sample costs 0.1–0.2 ms; the task
  listing 1.3 ms.

### 4 — Storage and finalisation

- **Every writer reserves** (`enforce.configure_storage` + `write_atomic`): used + 3n against the class limit — work
  writes (arrays, per-pass records) under cap − 64 MiB; finalisation writes (state, terminal, gates, phase records,
  parity, report, receipt, controller, final) under the full cap — so the report reserve stays available on every stop
  route without a cap reset.
- **Honest completed figures:** `storage_final` in STAGE_A_FINAL.json **includes the final record's own bytes** (a
  fixed point, checked equal to the tree after the write); `seconds_total` ends at the close of the session record, the
  final write's own duration inside the 60 s tail reserve within the cap.
- **A failed or blocked final write** leaves **no** final record (the previous one was superseded at session start):
  exit 75, a truthful hold.

Fixtures: `Units.test_every_writer_reserves` (work refused at the operational limit; finalisation into the reserve;
refused past the cap; the terminal writer included); `Finalisation.test_storage_cap_edges`,
`test_failed_final_write_leaves_no_pass`.

### 5 — Independent validator

`stage_a_report.validate` implements the schema it claims, from archived data:

- per record: **exact key set and schema tag**, planned id/index/case/**kind**; instrumented — expanded-ids hash
  (plain: the frozen hash; suffix: the declared hash) and token count, readout positions, capture layers, residual
  metadata and array (shape, dtype, finiteness, hash), final-logit metadata (one vocabulary size across all records,
  hash = logits_sha256), requested ids/logits/ranks, top-k, edit/dispatch (edits installed exactly for edited cases;
  one edit-log entry with the case's mode, layer 41, the marker positions and the declared alpha), GDN kernel, image
  (exact keys, pixels, grid, 144 tokens, features shape and one declared dtype, frozen and effective positions, **32
  rotary calls (0, n)**, one embed call, merge exact keys and **144 contiguous rows**, merge digest equal across the
  input's cases, feature digest equal across the input's cases), and the **boundary bytes decoded** (D values, sha256
  and finiteness recomputed);
- native — exact keys, **decoder calls exactly one per layer (64)**, effective positions, the **merged embedding digest
  compared with the paired plain merge digest from the archive** (the stored boolean must agree), finite requested
  logits, the residual array; reloaded native outputs are checked the same way at run time;
- the **ledger**: identity, caps, carry, no unknown or extra id, completed kinds and output maps, counters recomputed
  from the attempts (row and aggregate);
- **output membership** (every file under passes/ committed); both phase records (and the instrumented identity);
- every criterion recomputed (120 bitwise, 2 suffix, encoder pair, embeddings, 20 parity rows).

**Live-bound, not recomputed:** full final logits (~1 MB per pass) and the 144 × D features (~3 MB) are not archived;
their digests and the merge flags are compared as recorded.

Fixtures (`ValidatorMutations`, consistently rehashed, 16 tests): record identity and kind, extra and missing keys,
plain input-ids and token count, readout, layers, top-k, logit metadata, residual metadata, edit mode and alpha, edits
on a plain case, rotary calls, merge rows, feature shape and dtype, merge across cases, boundary NaN with a consistent
hash, boundary hash and byte length, native embedding digest with the boolean left true, the boolean alone, decoder
calls, nonfinite native residuals, duplicate parity summary, failing numbers marked pass, phase-record mismatch and
identity, suffix leak and insensitive encoder, ledger counters, unknown id, identity and caps, a stray output.

### 6 — Final PASS and B

- The report writes figures, Markdown, machine JSON and **last** `report/REPORT_RECEIPT.json` (session, the gates'
  package and identity, the sha256 of every output).
- `_finalise` accepts PASS only with a **current** report: this session's report worker exited 0, no report stop this
  session, a receipt naming this session and these gates, every listed output matching, the validator passed and
  admissible — and no terminal record, and **every cap on the final figures: time, storage (with the final record),
  whole-task memory and the attempt counters** per row and in aggregate from the ledger.
- Earlier PASS artefacts are **superseded** at every session start (moved to `superseded/`).
- The **Stage B prediction is recomputed at finalisation** from the completed whole-stage seconds and bytes (the report's
  is labelled preliminary).
- **B admission's interpretation item is validated** (`interpretation_status`): `report/INTERPRETATION.md` must name an
  author and a date on or after the report and the sha256 of both figures as they are on disk.

Fixtures: `Finalisation.test_report_failure_modes_prevent_pass` (machine JSON then failure, wrong receipt hash, other
session, worker failure), `test_stale_pass_superseded`, `test_over_limit_ledger`, `test_time_exhausted_spawns_no_work`;
`Units.test_interpretation_status`; `StageA.test_full_pass_validator` (the receipt binds every output).

### 7 — Declarations

- This file and `READINESS_ROW20.md` state the implemented guarantees and the limits in §6.
- `audit_app/IMAGE_AUDIT_FREEZE.md`: **61 of 63** (replacing 59/61).
- `provenance_checks.json`: a first crawl "does not establish the upload date or a later upload".
- **Audit map** (`audit_alias_map.py`, a before-audit condition, not a Stage A gate): the qualification key's
  specificity rule S1–S4 applied (dress pruned from clothes, lid from hat); denim pruned from jeans by a documented
  exclusion the rule does not reach (it also names the fabric); three documented equivalences (taxi/cab,
  hamburger/burger, pig/hog); taxis admitted beside taxies; construction identities recorded (THINGS tables, WordNet,
  dev_pool, the key module, the builder); the frozen map's sha256 pinned in the audit freeze; the audit scorer
  (`audit_alias_map.score`, format before matching) refuses any other map. Revision 3's builder imported a function
  the key module no longer had; revision 4 rebuilds it.

## 2. Inputs, cases, tolerances and stops

Unchanged from revision 3 (and 2): relative L2 ≤ 0.01 per marker layer (FP32 in FP64, instrumented norm as
denominator), maximum E1 logit difference ≤ 0.10, identical argmax, the within-path cases bitwise equal to plain. The
envelope: 16 carried + 140 + 16 + 2 + 20 = **194 of 200**, 1,808.73 s carried; caps A 200 / 4 h / 1 GiB, task
memory 48 GiB.

## 3. Running it (after the go only)

```
.venv-image/bin/python stimuli/photo/stage_a_controller.py run     # exit 0 PASS/STOPPED, 2 REFUSED, 4 HELD
```

## 4. The attestation block (agreed by Codex at `081f17b`; unchanged)

```
<!-- STAGE-ATTESTATION v1
{"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "<reviewer name and session>",
 "date": "YYYY-MM-DD", "reviewed_commit": "<40-hex RSC commit of the reviewed package>",
 "package": {"criteria_sha256": "...", "identity_sha256": "...", "plan_sha256": "...",
             "manifest_sha256": "...", "budget_sha256": "..."}}
-->
```

The go file holds exactly `review` {commit, path, record_sha256}, `owner_go` {by, date, words} and `package` (the
same five hashes).

## 5. Tests (no model)

The retained-output run of the whole photo suite on this package is in `reviews/2026-10-02_photo_suite_rev4_run.md`
(command, exit status, counts, skips, identity, stdout/stderr).

## 6. Stated limits (not narrowed silently)

- **Descendants that leave the process group between two samples** (0.1 s apart) and are reaped by their own parent
  before the next sample are not seen; a member recorded once is killed by identity. No task process forks in Stage A.
- **The Σ-lifetime memory measure** over-counts processes whose peaks did not coincide; that can stop early, never
  late. A descendant reaped by its parent between samples contributes its last sampled value.
- **The 60 s charge for a power loss** is a declared allowance; with the controller alive or dead (but the machine up)
  the unseen interval is measured by the watchdog and charged when longer.
- **The stop margin** rests on the measured interval and growth of synthetic work; the model's own peak and growth are
  Stage A measurements.
- **Full logits and features** are live-bound digests, not archive-recomputed.
- **Two tiny writes are outside the reservation:** the task LOCK (under 100 bytes, before storage is configured) and a
  watchdog's record (under 500 bytes, a separate process); both fit the 64 MiB finalisation reserve.

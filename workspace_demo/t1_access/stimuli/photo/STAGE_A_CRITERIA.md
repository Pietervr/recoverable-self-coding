# Stage A (ledger row 20): declared criteria and code, revision 3 (R084, 2 October 2026)

**Specification:** framework `rsc_t1_two_channel_framework.md` §8.2, §8.4 and §8.6 (Unimog).

**History.**

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | RSC `79343d9` | RSC `f9d2ef3` | NOT ON BOARD |
| 2 | RSC `e598f96` | RSC `69539bb` | NOT ON BOARD |
| 3 | this commit | — | answers R052's handoff `51739bd8`: the seven closure groups of `69539bb` §5 |

Neither review record can be named by a go; the guard refuses both commits.

**Not reopened** (Codex confirmed them):

- inputs, cases and diagnostics;
- the frozen-input admission;
- the positional checks;
- the transaction;
- the numeric statistic;
- the engineering carry;
- mask → clothes.

For those, see revision 2's text at `e598f96`. They are unchanged except where §1 says otherwise.

**No forward has run on any development image.** The mechanism evidence below comes from declared,
non-development fixtures: synthetic worker processes and synthetic arrays, no model and no image.

## 1. Closure groups 1–7: where each lives

### Group 1 — approval and identity

**Code.** `stage_a_guard.require_go` and `parse_attestation`:

- the go file holds exactly `review` (the full 40-hex commit, path and sha256 of the review record), `owner_go`
  and `package`;
- the record is read from git at that commit and hash-checked;
- it must carry **exactly one** attestation block (§4) with exactly the declared fields: row "20", stage "A",
  verdict "favourable", a reviewer, a date, the full reviewed commit, and the five hashes;
- **attestation package = go package = package recomputed now**, and `stage_a.package_at_commit` must re-derive
  the same five hashes from the reviewed commit itself;
- the dates must be in order (reviewed commit ≤ review ≤ owner go);
- the three negative records `f9d2ef3`, `69539bb` and `cf3e49e` are refused.

**The report phase** is admissible only when the controller passed these gates for this package in the same run
(`STAGE_A_GATES_OK`). Otherwise the report is labelled DIAGNOSTIC and confers nothing.

**Identity.**

- `execution_identity` hashes everything afresh: the cache is removed, so the shards are hashed each phase in about
  8 s.
- It fails closed when an identity command (git) fails.
- It writes per-file maps of every watched package tree (`stage_a_identity_files.json`, bound by hash).
- `check_imported_origins` runs in each worker after its loads. It refuses any loaded module of a watched package
  that comes from outside its hashed root or whose file changed.

**Positions receipt.** `stage_a.py plan` now refuses unless the declared M-RoPE rule equals mlx-vlm's
`get_rope_index` for both carriers. It writes `stage_a_positions_receipt.json` (bound to the plan hash) only on
success. The identity binds the receipt, and the desk gates require it.

**Tests** (`tests/test_stage_a_runner.py`):

- `GoAttestation`: good; no block; two blocks; unrelated package attested; wrong row; not favourable; extra field;
  go package differs; package changed since review; package at the reviewed commit differs; owner go before review;
  record hash mismatch.
- `Units.test_imported_origin_and_changed_file`: a shadowing origin and a changed file are both refused.
- `test_diagnostic_report_confers_nothing`.

### Group 2 — controller and recovery

**Code.** `stage_a_controller.py`, a separate process that spawns each phase as a worker in its own process group.

- It writes a durable record every 1 s (`controller.json`).
- It holds reserves **inside** the 4 h cap: tail 60 s, stop 60 s, report 600 s. Work phases are killed at
  cap − 720 s, and the report at cap − 60 s.
- On a stop it sends SIGTERM to the group, waits 3 s, sends SIGKILL and calls `waitpid`.
- **A dead controller is charged its last durable live time + 60 s.**
- Initial resource failures and worker crashes write `TERMINAL.json` and keep the first reason. A persistence
  failure kills the worker and exits 75.
- **Recovery is per try and consumed.** `RECOVERY_<attempt>__<session>__<try>.json` names exactly one interrupted
  try. `enforce.Budget.authorise_recovery` consumes it durably. A later crash of the same id needs a new file; the
  old one cannot serve.

**Measured in the fixtures** (`controller_fixtures.json`, synthetic workers, `tests/test_controller.py`, 10 of 10):

| Fixture | Result |
|---|---|
| Worker ignoring SIGTERM, blocked in C | SIGKILL; kill → reap **3.01 s**; its grandchild dies with the group |
| Worker ignoring SIGTERM, looping 4096² MLX matmuls on the GPU | SIGKILL; kill → reap **3.01 s** |
| Failing memory sampler | stops |
| Sampler taking 1.2 s | stops |
| Initial sysctl failure | terminal, no worker spawned |
| Worker exits 3 | terminal |
| Worker exits 0 without its phase record | terminal |
| Second run after a terminal stop | holds; the first reason is kept; the report still runs |
| Controller writer fails | exit 75 within 5.7 s, with the first reason durable |
| Crash tail | charged at exactly live + 60 s |

Runner test: `test_crash_recovery_is_per_try_and_consumed`. Two crashes of the same id need two files, and both
tries stay counted.

### Group 3 — phase separation and memory

**Phase separation.** The controller holds the lock for the whole run. The native worker is spawned only after the
instrumented worker has exited and been reaped (tested via spawn and exit times). Workers refuse to run unless their
parent is the lock-holding controller.

**Memory.** Read from outside through `memprobe.footprint`:

- the API is `proc_pid_rusage` V4;
- `ri_phys_footprint` is the ledger now;
- `ri_lifetime_max_phys_footprint` is the kernel's running maximum of it;
- the controller stops at a lifetime maximum ≥ 44 GiB (4 GiB headroom), on an unavailable reading, or on a reading
  slower than 1 s;
- swap and kernel pressure are read every 2 s with 2 s timeouts.

**Measured** (`memprobe.py fixture`, synthetic):

| Allocation | Ledger |
|---|---|
| 1 GiB host + 2 GiB MLX at once | 3.22 GiB — additive across host and Metal, covering disjoint simultaneous allocations |
| plus a 2 GiB host spike, released | lifetime maximum 5.22 GiB — the released spike is still seen |
| one sample | under 0.3 ms |

**Not shown:** the MLX free-buffer cache class. MLX reported its cache as 0 in both runs, so that class was not
exercised separately; its buffers sit inside the allocator's own total, which the ledger covered. The model's
actual peak stays a Stage A measurement.

### Group 4 — output and finalisation envelope

- The external hash cache is gone; every task-owned file is under the output tree.
- Work phases stop at 1 GiB − 64 MiB, the finalisation reserve for the terminal, phase, parity, report and final
  writes.
- The report runs under the full cap, also after a stop: a bounded STOPPED route. No cap is reset.
- `enforce.Budget.reserve` checks n + 2n of headroom against the operational limit before each array write.
- **Closure ordering.** The controller closes its session, then writes `STAGE_A_FINAL.json` after the report
  worker has exited.

### Group 5 — independent validator

`stage_a_report.validate` trusts no summary. For each of the 178 planned ids it:

- re-reads every committed output and re-hashes it;
- checks the exact id, index and case, the schema, the shape, dtype, finiteness and hash of the arrays, the
  requested-E1 order and finiteness, and the pixel, grid, token, position (frozen and effective), merge, boundary
  and single-prefill fields.

It checks both phase records against the state. It then **recomputes every criterion**:

- the 120 bitwise cases;
- the two suffix-isolation diagnostics (also against the declared perturbed-id hash);
- the encoder pair (pixel **and** feature hashes must differ);
- the native merged-embedding equality, **now enforced** as a native stop and a validator check;
- all 20 native comparisons, from the committed arrays with `stage_a.compare`.

`native_parity.json` is only compared with the recomputation.

**Tests** (`ValidatorMutations`): consistent tampering reaches each check on its own:

- hash tamper;
- wrong case;
- non-finite native residuals;
- twenty duplicate passing parity rows;
- failing numbers recorded as passes;
- phase-record mismatch;
- suffix leak and an insensitive encoder;
- an embedding difference.

### Group 6 — completed report and the B gate

- Only `STAGE_A_FINAL.json` can say PASS. The controller writes it after the report worker has exited and its own
  session has closed, so its cost, peaks and final bytes include the report's generation, writes and closure. It
  re-checks the terminal record and every cap on those final figures.
- The report counts unique planned ids, ids started and actual tries separately.
- **B admission** is an explicit list, every item false until it exists:
  1. STAGE_A_FINAL = PASS;
  2. `report/INTERPRETATION.md` by the author, after inspecting the figures (author, date, figure hashes);
  3. Codex's review of the report;
  4. the owner's row-21 go.
- B's first-CAL-slice qualification stays with row 21.

### Group 7 — headroom and declarations

**Headroom.** B is predicted from whole-stage rates per unique attempt and must satisfy predicted ≤ 0.8 × row 21's
cap (× 1.25): **11,520 s and 6.4 GiB**.

**Source wording.** A removed stock listing is recorded as "no conflicting claim observed; upload date unknown". A
first crawl is an upper bound on when a listing existed, not proof of a later upload. This applies in
`provenance_checks.json` (five verdicts reworded) and in the readiness report.

**Clothes** replaces mask throughout.

**Audit (before B, not an A gate).** In `audit_app/IMAGE_AUDIT_FREEZE.md`:

- every photograph is named blind on its own, before any pair is shown;
- `audit_alias_map.json` (built by `audit_alias_map.py`) is the audit's own frozen sense and alias map for the 32
  instrument concepts.

The same builder fix ("no regular plural for a word already ending in a plural -s", so no more "scissorses") also
changed the qualification key. That moves the AI-reader package; see the brief to R052.

## 2. Inputs, cases, tolerances and stops

These are as revision 2 (`e598f96`, §§1–4), with two changes:

- the native merged-embedding equality is now a stop;
- the plan is revision 3. Its inputs, attempts and diagnostics are identical; its envelope also declares the
  controller's sampling intervals, reserves, memory stop and finalisation reserve.

The tolerances are unchanged:

- relative L2 ≤ 0.01 per marker layer: ‖inst − nat‖ / ‖inst‖ over the 3 marker rows × 5,120, FP32 values in FP64,
  with the instrumented norm (non-zero, finite) as denominator;
- maximum E1 logit difference ≤ 0.10;
- identical argmax;
- the within-path cases equal plain byte for byte.

The envelope is unchanged: 16 carried + 140 + 16 + 2 + 20 = **194 of 200**, with 1,808.73 s carried.

## 3. Running it (after the go only)

```
.venv-image/bin/python stimuli/photo/stage_a_controller.py run
```

This runs instrumented → native → report in one controller process. A restart resumes, after any recovery files.

## 4. The proposed attestation block (R052 to agree with Codex; the guard accepts exactly this)

The block goes in the favourable review record, once:

```
<!-- STAGE-ATTESTATION v1
{"row": "20", "stage": "A", "verdict": "favourable", "reviewer": "<reviewer name and session>",
 "date": "YYYY-MM-DD", "reviewed_commit": "<40-hex RSC commit of the reviewed package>",
 "package": {"criteria_sha256": "...", "identity_sha256": "...", "plan_sha256": "...",
             "manifest_sha256": "...", "budget_sha256": "..."}}
-->
```

The go file then holds:

- `review`: `{"commit": "<40-hex commit of the review record>", "path": "<record path>", "record_sha256": "..."}`;
- `owner_go`: `{"by", "date", "words"}`;
- `package`: the same five hashes.

## 5. Tests (no model)

| Suite | Result |
|---|---|
| `test_stage_a_runner.py` | 23 of 23 |
| `test_controller.py` | 10 of 10, real subprocesses, synthetic |
| `test_ai_reader.py` | 12 of 12 |

```
.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v
```

## 6. Stated limits (not narrowed silently)

- **The 60 s crash-tail charge** is a declared bound, not a measurement of an uncontrolled power loss. The loop it
  covers is measured: a 1 s beat, a sample under 1 ms, sysctl calls with 2 s timeouts.
- **The 4 GiB memory headroom** assumes less than 4 GiB of growth within one 0.25 s sample. The kernel's lifetime
  maximum still records any overshoot, and an overshoot is reported as a cap breach.
- **The fixtures qualify the mechanisms on synthetic work.** Real throughput, peak and parity are Stage A
  measurements.

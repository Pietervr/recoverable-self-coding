# Row-20 OS-bridge supplement, run of 4 October 2026: PASS - input 00 bit-identical across macOS 27.0 -> 27.0.1 on the instrumented path; native = new instrumented within one bf16 step; row 21's verifier ok

R084, 4 October 2026. The go: the owner's standing bridge go of 4 October, bound by R052 in
`stimuli/photo/ROW20S_GO.json` (RSC `8b7e26a`) to Codex's favourable record RSC `9159134`
(`reviews/2026-10-04_stage_a_supplement_rev6_codex_record.md`, sha256 `4dfd49e5...`) on the exact revision-6 package
(RSC `5f08728`: supplement criteria `83ffd69d...`, supplement identity file `1acf5564...`, supplement plan
`8e410840...`, base plan `3faebf4e...`, manifest `e816f843...`, budget `186e7738...`).

## Before the run

- `sw_vers`: macOS 27.0.1, build 26A434; machine arm64 - the declared environment.
- `supplement_package_hashes` on the live tree = the bound package; `stage_a_guard.require_go(row "20", stage
  "A-supplement")` accepts it against `supplement_package_at_commit` (favourable, reviewed commit `5f08728`).
- `load_supplement`: the supplement plan matches the 178-id plan, the code and the frozen accepted Stage A tree
  (carry 194 starts, 2,338.11 s, 396,783,863 bytes); no supplement tree existed; photo directory clean; no reader or
  model process; memory 96 % free.
- Command: `.venv-image/bin/python stimuli/photo/stage_a_controller.py supplement` under `caffeinate -i`, fully
  detached, HEAD `bc34bc4`; run outputs in `2026-10-04_stage_a_supplement_run/`.

## The run

Started 2026-10-04T07:34:22Z; exit 0 at 07:35:11Z. One session (`519de46b0154`): gates -> instrumented -> native ->
receipt -> final. Both release intents published before their GO (`evidence/intent/`).

| Pair | Reference -> candidate | Per-layer rel L2 max (<= 0.01) | Requested logits (each <= max(0.10, one bf16 step)) | Requested argmax | Bound checks | Result |
|---|---|---|---|---|---|---|
| (a) | `00-plain` (macOS 27.0, 2 Oct) -> `00-plain-os2701` (27.0.1) | **0** | max difference **0** (worst 0 vs tolerance 0.10) | equal (id index 20) | all pass | **PASS** |
| (b) | `00-plain-os2701` -> `00-native-os2701` (same environment) | **0** | max difference **0.0625** (worst 0.0625 vs 0.10; one bf16 step) | equal (20) | all pass, incl. one prefill and merged embeddings = the new instrumented merge bitwise | **PASS** |

Diagnostic (a), labelled, not a criterion: residuals, final logits, image features and the merged embeddings are all
BITWISE equal across 27.0 and 27.0.1 on input 00's instrumented path.

Counters (supplement ledger, carrying Stage A's): **194 -> 196 of 200** started, 195 completed, 1 failed (the carried
engineering failure), 196 passes; both ids completed in one try each. Time: 2,338.11 s carried + 108.23 s this session
(incl. the 60 s closure) = **2,446.34 s of 14,400 s**. Task memory: peak aggregate 33.33 GB (instrumented phase; native
18.37 GB) against the 44 GiB stop and 48 GiB cap; all mandatory measurements present. Storage: 7,739,672 bytes in the
supplement tree, row 20 total 404,523,535 of 1 GiB. Every cap holds on the final figures.

Final: `SUPPLEMENT_FINAL.json` outcome **PASS**, admitted (marker), receipt PASS and admissible; the final binds the
create-once durable controller copy `controller_at_final_519de46b0154.json` (sha256 `0037511b...`), `durable_missing`
empty. Evidence copies (the tree itself is git-ignored like Stage A's): `2026-10-04_stage_a_supplement_run/evidence/`
(final, marker, gates, both phase records, the ledger, controller record and its bound copy, both comparison receipts,
the receipt, both intents, both pass records).

## Row 21's gate

`stage_a.py supplement-verify` on this machine now: **ok true, hold false, no reasons** (`supplement_verify.json`):
admitted PASS, no terminal, the bound receipt and outputs unchanged, both comparisons re-derived equal to their
complete receipts and passing, the three records re-validated, the frozen Stage A tree unchanged, the ledger exactly
two single tries at carry + 2 by the final's session, input 00 exact, the bound durable record carrying both intended
endpoint peaks, and the current execution compatible on every COMPAT_KEYS field. Row 21 still needs its own package,
review and owner's go, and must call this verifier with its own identity before its first CAL forward.

## Scope and declared limits

- One exposed development input (00, crow at -12 dB, carrier 0). It does not isolate OS causality, re-qualify every
  image or edit, reproduce the 120 shams on the new OS, or admit PILOT. No Stage B forward is approved by it.
- Codex `9159134`'s declared limits carry: recovery confirms the enumerated group and the valid recorded members only
  (not every possible descendant); unexpected permission/process-observation/storage errors can leave a check
  unfinished; a pre-GO intent conservatively consumes the version; whole-tree deletion is an external residual; the
  durable copy checks intended endpoint peaks, while other final resource figures come from controller memory;
  session-time rollback is not newly fixtured. None of them occurred or applied in this run (no failure, no restart).

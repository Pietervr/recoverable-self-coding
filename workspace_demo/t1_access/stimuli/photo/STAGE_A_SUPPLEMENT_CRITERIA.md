# Stage A supplement (ledger row 20): the OS bridge before row 21 - declared criteria and code, revision 1 (R084, 3 October 2026)

**Specification:** Codex's record RSC `b0db0f9` (`reviews/2026-10-03_stage_a_report_codex_record.md`, SHA-256
`52ed7082...6b90`), §"Prospective row21 OS bridge: form, count and gate"; R052's handoff `8266e5ae` item 2.
**Status:** BUILT AND TESTED ONLY. No forward and no model call before Codex's record on this exact package and the
owner's go bound to it (`ROW20S_GO.json`, attestation row `20`, stage `A-supplement`). The revision-15 four-native go
does not cover it.

| Revision | Commit | Codex's review | Verdict |
|---|---|---|---|
| 1 | this commit | — | built; with R052 for Codex |

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
features and merge across (a) is recorded as a labelled diagnostic, not a criterion. Both comparison receipts
(`supplement/comparison_a.json`, `comparison_b.json`) are written before any stop decision and retained either way.
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
| INSTRUMENTED: worker identity; the reference admitted; the instrument loaded, its import map checked; input 00 admitted (frozen original, PNG, tensor, grid, sequence, processor); one capture; per-pass checks; the record saved, re-read, validated, committed; comparison (a); its receipt; `SUPPLEMENT_INSTRUMENTED_DONE.json` | `run_supplement_instrumented` | `Run.test_pass_...`; `test_comparison_a_failure_stops_and_retains_its_receipt` (receipt kept failing; terminal; 195/194 preserved; both phases then refuse; receipt STOPPED; Stage A's TERMINAL untouched); `test_failed_forward_is_charged_and_stops`; `test_resume_reloads_and_never_replays`; `test_corrupt_reference_holds` (checksum, before any start) |
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

## 7. Which reviewed files move

| File | Moves? | What |
|---|---|---|
| `stage_a.py` | YES | revision 16 block: the supplement plan, gates, two worker phases, receipt, verifier, desk commands; `Ctx` gains three defaulted fields; `package_at_commit`'s identity check factored into `_identity_describes_commit` (same checks, same messages). Stage A's own paths unchanged. |
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

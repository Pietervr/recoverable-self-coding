# Stage A (ledger row 20): declared criteria and code, revision 2 (R084, 2 October 2026)

**Specification.** Framework `rsc_t1_two_channel_framework.md` §8.4 (Unimog repo), which carries runner checks
(a)–(p). This document states how the code implements it.

**What this answers.**

- Revision 1 (RSC `79343d9`) was reviewed by Codex as **NOT ON BOARD** (RSC `f9d2ef3`). That record is not a
  favourable review and cannot be named in `ROW20_GO.json`. The code refuses it.
- This revision answers R052's repairs 1–18 (Unimog `prompts/2026-10-02_r052_to_r084_row20_repairs.txt`).

**State.** No forward has run on any development image. Every test below ran on a fake instrument, with no model
imported or loaded.

## 0. Where each repair lives

| # | Repair | Where |
|---|---|---|
| 1 | Seven cases; λ = 1 swap/ablate as 16 labelled diagnostics on 8 named inputs | `stage_a.py` `CASES`, `MECHANICS`, `make_plan` (diagnostics.mechanics = the 8 clean inputs); §2 below |
| 2 | Explicit no-edit delayed repeat; unknown case rejected | `stage_a.edits_for` (a table; `repeat` → `None`; anything else raises); test `Units.test_cases` |
| 3 | Frozen plan and manifest loaded, never regenerated; original bytes, PNG, tensor and grid checked before each input; native checked against the frozen values | `stage_a.load_frozen`, `admit_input` (both phases); plan fields `original_sha256`, `png_sha256`, `pixel_values_sha256`, `grid_thw`, `expected` |
| 4 | Positional identity enforced | `admit_input` → `check_against_processor` and `check_sequence_structure`; `validate_pass` (ids hash, readout, M-RoPE positions = the frozen expectation = effective, 32 rope calls at offset 0, one embed call, one injection, merge rows bitwise, dims and dtypes, requested E1 order); `check_tokenizer` (E1 ids vs the pinned tokenizer in both phases); native: effective positions and one call per decoder layer |
| 5 | Execution identity | `stage_a_guard.execution_identity` → `stage_a_identity.json` (snapshot files including the three shards, lens, local code, `packet.py`, jlens tree + HEAD + diff + shim, ten package trees with versions, Python and macOS, declared precision and dispatch, plan and manifest hashes); recomputed and compared in every phase; `post_load_instrumented` checks the loaded dims, dtype and GDN patch |
| 6 | Go bound to the exact package | `stage_a_guard.require_go` checks: verdict "favourable"; commit not `f9d2ef3`; the record's sha256 read from git at that commit; the owner's dated words, not earlier than the review; criteria, identity, plan, manifest and budget hashes. It runs before any load. Tests: `GoBinding` (7 mismatches refused) |
| 7 | Durable first-failure stop across both phases; no retry | `stage_a_guard.TERMINAL.json` (`set_terminal`/`check_terminal`), written on ANY exception after the session opens and by the supervisor; consulted at every phase start; `Budget.attempt` refuses any id already attempted. Tests: `test_bitwise_failure_is_terminal_in_both_phases`, `test_native_parity_failure_is_terminal` |
| 8 | Completion transaction; reload without forward; corrupt output holds | `enforce.Attempt.commit` (only after `save_outputs` writes, re-reads and checksums); `load_outputs` re-verifies on restart; an interrupted attempt needs `RECOVERY_<id>.json`. Tests: crash mid-attempt (subprocess `os._exit`), corrupt output |
| 9 | Native integrity | `stage_a.admit_native`: `INSTRUMENTED_DONE.json` + all 158 committed ids, unique (index, case), checksums, shapes and dtypes; `finish_native` re-validates all 20 before `native_parity.json` |
| 10 | Clock | `enforce.Budget` opens before any model import; monotonic live time; supervisor heartbeat every 2 s (durable); a crash is charged last live time + one beat; at the cap, the supervisor records the stop, interrupts the main thread, and ends the process after 20 s if a kernel cannot be interrupted. Test: `test_deadline_supervisor_stops_active_work` |
| 11 | Single worker and memory | `stage_a_guard.TaskLock` (`fcntl.flock`); native admitted only after the instrumented phase's durable completion record (separate processes, strictly sequential); `enforce.memory_reading` fails closed (task_info, ps, sysctl or MLX counters unavailable → stop); enforced = max(phys_footprint, MLX active + cache, MLX peak), sampled every heartbeat through load, run and report; qualification in `enforce.py`'s docstring. Tests: lock contention, memory fail-closed |
| 12 | Storage | `Budget.used_bytes` over every task directory (passes, temporaries, state, report); `reserve(n)` checks n + 2n headroom before each write; `final_size()` at each phase end |
| 13 | Finiteness and causality | Pixels, every feature element, the boundary mean, native residuals and logits, every comparison statistic, non-zero reference norms (`compare`), 144 tokens; structure (`check_sequence_structure`); encoder-sensitivity pair (plan diagnostics, checked at the end of the instrumented phase, no forward); future-suffix isolation (2 diagnostics, bitwise marker residuals). The boundary record is labelled "FP32 mean over the 144 projected visual tokens + full-token sha256" |
| 14 | Numeric definition | §3 below; `stage_a.compare` docstring |
| 15 | Engineering accounting | `stage_a.ENGINEERING_CARRY` (16 attempts, 8.73 s measured + 1,800 s allowance) seeded into row 20's state; `engineering/README.md` "Reconciliation"; `numeric_equal_layers` labels in `adapter_engineering.py` and `runtime_agreement.py` |
| 16 | Source records | `provenance_checks.json`: R052's ruling in `stock_matches_note`; a dated `stock_comparison` for every Stage A input; jet/ship permission text from the actual basis and missing fields kept with their basis (`manifest.py`). Result: **mask is ineligible** (a live listing credits another author) and is replaced by **clothes** (§1) |
| 17 | Report | `stage_a_report.py` (validator, timings, peaks, accounting, SVG figures, interpretation section, Stage B headroom from whole-stage rates), run by `stage_a.py report` inside A's budget |
| 18 | Audit page | `audit_app/IMAGE_AUDIT_FREEZE.md` (panel, order, attempts, aggregation frozen before any answer, to the revised §8.2); opaque item ids and image names in `image_items.py`; page tests 14/14 and API 40/40 |

## 1. Inputs (`stage_a_plan.json`, revision 2, seed 20261006)

| | Count | Construction |
|---|---|---|
| Clean | 8 | the Stage A primary views — crow, horse, chili, hamburger, taxi, wagon, jacket, **clothes** — a = 1 |
| Intermediate | 8 | per family the two views, sorted by name, dealt one to −12 dB and one to 0 dB by the seed |
| Noise-only | 4 | `dose.zero(nonce)`, its own path; no photograph is opened |

**The input set changed from revision 1.**

- The dated stock comparison (repair 16) found that **mask** has a live Shutterstock listing (1799626735, uploaded
  2020-08-20) crediting "Beni setiawan98". The free source credits josealbafotos (Pixabay, 2016-01-20). Under §8.2's
  rule a listing that names a different author is a conflicting claim, so mask is ineligible.
- `pool.py` replaced it in seeded order with **clothes** (Pixabay 53319, JamesDeMers, 2012-07-29, CC0 by date). It
  skipped wig (post-2019), sweater (a live listing credits another author) and scarf (post-2019). Every other role is
  unchanged.
- The other Stage A views show no conflict. jacket, chili, hamburger and taxi have ten listings between them; all
  ten are removed (410, 404 or a redirect to a generic page), and each was first crawled after its free source's
  published date. Of the thirteen listings checked for the original eight, only mask's one is live.
- crow, horse and wagon have no stock listing.
- The seed is unchanged. The clothing pair is now (clothes, jacket), so the clothing deals are drawn afresh; the other
  families' deals are unchanged.
- Carriers are 10/10. Every input is grid [1, 24, 24] (144 merged tokens).

**The plan freezes per input:**

- the original file's sha256, equal to the manifest's;
- the PNG, delivered-tensor and grid hashes;
- the expected expanded-ids hash, image span, vision start/end, marker and suffix indices;
- the expected multimodal positions hash. It comes from a declared rule; `stage_a.py plan` checked that rule against
  mlx-vlm 0.6.3's own `get_rope_index` for both carriers by index arithmetic only, with the weights opened lazily and
  never evaluated.

It also freezes:

- the 32 request tokens, each checked to be `encode(' ' + concept)` under the pinned tokenizer;
- the 178 attempt ids in run order;
- the diagnostics;
- the budget envelope and its hash.

## 2. Cases, diagnostics and the envelope

**Cases.** Every case captures 64 layers at the three `[END]` rows, plus logits over the 32 E1 ids at the final
suffix token.

| Case | Edit (layer 41, the three marker rows) | Criterion |
|---|---|---|
| plain | none | reference |
| empty | `edits = []` | bitwise = plain |
| zero_steer | steer toward the target, λ = 0 | bitwise = plain |
| zero_ablate | ablate the target, λ = 0 | bitwise = plain |
| zero_swap | swap_delta target → foil, λ = 0 | bitwise = plain |
| self_patch | patch with plain's own layer-41 rows | bitwise = plain |
| repeat | none (explicit), after every input's other cases | bitwise = plain |

"Bitwise = plain" means equal sha256 of the residual bytes, of the final-logit bytes and of the vision-feature bytes.
The target is the view's E1; the foil is the other Stage A view of its family. A noise-only input uses its family's
pair in name order.

**Diagnostics** (labelled, inside the envelope):

- **Mechanics.** λ = 1 swap and λ = 1 ablate at layer 41 on the eight clean inputs (indices 1, 6, 7, 9, 12, 13, 15,
  18), 16 passes. The outputs are archived. There is no favourable-output criterion; a nonfinite output still stops
  the run.
- **Future-suffix isolation.** On inputs 1 (carrier 0) and 12 (carrier 1), the three suffix ids `\n`, `Answer`, `:`
  are replaced position for position by the declared single tokens `\t`, `Reply`, `;`. The length and every position
  are unchanged. The marker residual sha256 must equal plain's.
- **Encoder sensitivity.** Inputs 1 and 6 (two clean, same-grid inputs) must have different pixel and feature hashes.
  This is checked from their plain passes, with no forward.

**Native reference.** mlx-vlm 0.6.3's own unchunked prefill (`get_input_embeddings` → `language_model(ids,
inputs_embeds, fresh cache)`), in a separate process after the instrumented phase completes, 20 passes. Residuals
are read through pass-through proxies. `capture_layer_ids` is not used. `jlens_qwen` must not be imported in that
process.

**Envelope (194 of 200, six in hand).**

| Part | Attempts |
|---|---|
| Engineering, carried in | 16 |
| Mandatory instrumented | 140 |
| Mechanics diagnostics | 16 |
| Suffix-isolation diagnostics | 2 |
| Native | 20 |
| **Total** | **194** |

- The time carried in is 1,808.73 s: 8.73 s measured plus a 1,800 s allowance.
- Row 20's caps are ≤ 4 h and ≤ 1 GiB, with the aggregate caps of rows 20 and 21 also enforced. Task memory is
  ≤ 48 GiB.
- No attempt id outside the plan ever runs. The six in hand are spent only by an owner-authorised crash recovery.

## 3. Tolerances and the exact statistics (fixed before the run, never adjusted)

- **Relative L2, per marker layer.** ‖inst − nat‖ / ‖inst‖ over the three marker rows × 5,120.
  - inst = the instrumented path's bfloat16 residuals, widened exactly to FP32;
  - nat = the native path's FP32 residuals;
  - both are accumulated in FP64, and the instrumented norm is the denominator.
  - It must be ≤ **0.01** at every layer.
  - An instrumented reference norm that is zero or nonfinite is a stop. No zero-norm convention is needed or used.
- **Logits.** The maximum absolute difference of the 32 E1 logits is ≤ **0.10**, and the closed-set argmax is
  identical.
  - The 0.03125 seen on `chair.jpg` is reported unexplained unless a declared, counted comparison attributes it.
  - 0.10 is an engineering tolerance, not a precision claim for later target-minus-foil contrasts.
- **Within-path cases.** Byte-identical hashes, as in §2.
- **Every statistic** must be finite.

## 4. Stops (each writes `TERMINAL.json` durably; no phase runs again)

- The first bitwise, parity, structure, identity, finiteness or causality failure.
- A missing or corrupt committed output.
- Any cap reached: attempts, time (stopped by the supervisor), storage, 48 GiB task memory.
- Swap above the level at the state file's creation.
- Kernel memory pressure ≥ 2.
- Any memory measurement unavailable.
- Any unexpected exception.

Not terminal:

- A refusal before the session opens (lock held, go absent or mismatched).
- A crash that leaves an interrupted attempt. It holds until the owner names that attempt in `RECOVERY_<id>.json`;
  the interrupted try stays counted.

## 5. The report (`stage_a.py report`, also after a stop)

The validator classes all 178 planned attempts as committed (outputs re-verified), failed, interrupted or never
started.

The run is a **PASS** only if all of these hold:

- no terminal record;
- both phase records exist;
- all 178 attempts are committed;
- 120 of 120 bitwise cases equal plain;
- both suffix-isolation checks hold;
- the encoder pair differs;
- 20 of 20 native rows pass.

Anything else is reported as **STOPPED** with the first reason.

The report holds:

- counters and the engineering carry;
- per-phase whole-stage seconds;
- the enforced memory peak overall and by phase;
- storage;
- attempt accounting by kind;
- the parity table;
- two SVG figures: relative L2 by layer for every input, and the maximum logit difference per input against 0.10;
- the interpretation section the author writes after inspecting the figures;
- **Stage B's headroom from whole-stage rates**: A's own session seconds (loads, checks, writes and this report;
  the engineering carry excluded) and bytes per attempt, times row 21's 1,856 attempts, × 1.2 must fit row 21's
  caps, and A's memory peak must be under 48 GiB.

The report runs as its own session of the same state file, so its cost is inside A.

## 6. Tests (no model)

`.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` (`tests/fake_stage_a.py` is a fake
instrument with the real record structure). **15 of 15 pass:**

- a full pass and report;
- lock contention;
- a bitwise failure that is terminal in both phases, with the report still produced;
- a native parity failure;
- native refused before instrumented;
- a crash mid-attempt, which holds until authorised and then reloads 39 committed attempts without a forward, the
  crashed try counted;
- a corrupt committed output, which holds;
- the deadline supervisor stopping busy work at the time cap;
- the case table;
- memory fail-closed;
- an attempt without a commit, which fails and is counted, and is never retried;
- an identity mismatch;
- the go binding (good, absent, and seven mismatches).

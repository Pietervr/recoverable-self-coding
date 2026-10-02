# Row 19 qualification-slice launch specification, revision 3 — Codex record

Date: 2 October 2026, Phoenix. Reviewer: `GPT: R052 Entropy paper`, native session `01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with launching C1 and main reps 0/1/2 from this package.** The proposed order remains reasonable: C1 plus the three main datasets, C2 after C1 supplies its original and first three refit timings, then C3 after C2's PBS kill, each through a prior campaign reservation. Several prior conditions are substantially repaired, but executable and retained-evidence gaps remain. Appending the timing addendum and obtaining owner go alone do not close them. This review approves no submission or account operation.

## Scope and immutable evidence

The accepted brief is Unimog `prompts/2026-10-02_codex_r052_row19_launch_specification_rev3.txt` at `e19499fd9d9e56b91802df53a6764e4495592ecb`, SHA256 `4262ce243881163288524378779ac59accd3233dcd5d1c1ae9e8486b6e5dc28b`. Handoff `cc0dc7cd-5209-55b4-8cc7-90ccf53ccf69` was read, ownership of this review and the reviewer's R052 log recorded at Unimog `dc5f03c6`, and acceptance acknowledged before review edits. Claude retains implementation, manifest, protocol, framework, ledger, tracker, frontmatter and dispatch ownership.

Reviewed candidate: **RSC `844842e155bd33f2325adae8fe9159f6cb1ac0f2`**, containing implementation **`22668d6bacef5bc8f8fb288f5fdf11efbf7727eb`**. The manifest's descriptive `code.commit` begins with `22668d6`; it resolves to that implementation. All five `code.files` pins match the immutable blobs. Later repository HEAD is not the candidate.

| File, relative to `workspace_demo/t1_access/` | SHA256 |
|---|---|
| `analyze.py` | `5177e4a4eca90f6f04dcddc34d4c42c709b3d501b82a2d8919e09eedadfc4d7f` |
| `models.py` | `28765f82b3e718c48521cf775add6220898752c662c4cdd1c3ffcdb113c4feef` |
| `simulate.py` | `f588b9121be48ec553ab95e4dda5736941865498922468b5868c96758d0afe57` |
| `chpc/row19_slice.py` | `7da3505d5fccee2eb39220a090fa039c268521f2088d9e6af2da139f6f904256` |
| `chpc/row19_ledger.py` | `d5cdcc7110478db962b25f84999ff462aed5083caf54463b60a1d01b62fe9aa7` |
| `chpc/row19_control_compare.py` | `7db151112f618c86e57db95a6dd8afdbade34f5fba7c1789c2b373a27f2233d7` |
| `chpc/row19_watch.py` | `d119724b4281c00e3891247d6a282f64c1b255769a04af9bc4f77f1a1d34f28f` |
| `chpc/row19_slice_manifest.json` | `8cfe368b98d0781f823c0bed0a89fd0ce1a466e4bcc1c45088d4f813689843f0` |
| `chpc/row19_slice_rep.pbs.template` | `52aaa692921bdac3c075b44bd67e36c18e7982b1766f484eef8400c625ae2b71` |
| `chpc/row19_slice_control.pbs.template` | `79b0d787839b937ab76c1cc9a5a8e4e4678f86e5838a0dee480ab6182ca188c4` |
| `test_row19_slice.py` | `42ba29e883d9434d2e9bcefa71c06eeb072ac0d75048815a6c6cb3f6cf6929e9` |
| `test_row19_control_compare.py` | `b1fdb853e19a619b8e2f82e3e16c5ee4b57c85b5b2695c119d8595ced2587952` |
| `test_row19_watch.py` | `9a92f83c436a1ef3d57ef751d5b85cd98c34eac743cc12f7fd45068a38ab591d` |

The full brief, prior revision-2 record at `e44f8049005d4cc7071e2aabc8604213d506a711`, source and fixture text were read. Relevant owning records were re-read: Unimog `rsc_t1_simulation_design.md` §11c, §12 and complete row 19; the pinned model pre-registration §7.4 and §8.2. Three subordinate static reviewers checked ledger, runner and comparator/watch lanes. Scratch notes are supporting analysis, not additional scientific outputs or canonical reviews.

No submitted module, function, import, test, fixture or CLI was executed. No fit, simulation, SSH/PBS/HPC/cloud/account operation, job submission, worktree or push occurred. The only executable checking was standard-library git/blob/hash/JSON/AST and deterministic metadata arithmetic. No private plant/key, audit results, reader/human/pull output, audit website or D1 material was opened. Foreign files were preserved.

The brief reports 42 passing stub tests and Lustre clone `rsc_slice` at `f75de6b`, with five source pins and wrapper verified remotely. These remain implementer evidence: the reviewer neither ran the tests nor authenticated that remote state. AST inspection confirms 42 named test functions: 6 refit, 4 until, 15 runner, 7 comparator, 3 watcher, 7 start-policy. Test counts do not establish the claimed branches were exercised. The control fixture explicitly labels its PBS interruption record as a stand-in; a real PBS walltime interruption remains a slice output.

## Question 1: disposition of R1–R7 and producing fixtures

| Prior condition | Current disposition |
|---|---|
| R1: campaign reservation and terminal states | Closed for the declared operator/API-emitted path; resource/accounting provenance remains the operator's obligation. |
| R2: interrupted progress, namespace and domain | Per-record watermark and ordinary missing-binding/domain guards repaired; shared-index concurrency leaves a bounded namespace gap. |
| R3: recovery comparator | Frozen draw/statistic checks and failed-parity refusal repaired; HELD/nonfinal status and filled walltime linkage remain open. |
| R4: fresh expected-job watch | Fresh staging, ledger-derived expectations and checkpoint progress repaired; schema, restored-stall and terminal evidence remain incomplete. |
| R5: stop, memory and logger | Admission/dispatch/last-refit checks and request IDs repaired; final aggregation/publication boundary and pipe-status retention remain open. |
| R6: original cache and companion | Nested lossless cache, HELD decode path and companion retention repaired; real fresh membership contract and consumer admission/fixtures remain open. |
| R7: prospective timing, environment and scopes | One C1-derived rule, no control continuation, wrapper/backend checks and budget repaired; measurement endpoints and a template declaration remain inaccurate. |

All line references below are to the immutable candidate. `runner` means `chpc/row19_slice.py`; `tests` means `test_row19_slice.py`.

### R1 — credit the implemented admission path

`row19_ledger.py:40–49,73–84,113–201` adds finite positive resources, integer submitted cores, cap agreement on each locked operation, already-over-cap refusal, request-matching cores/walltime, unique job binding, terminal settlement and retained attempts across roots. `runner:269–295` admits the manifest's one core and invocation walltime before ownership/fitting. A live reservation remains charged after runner end until explicit scheduler-accounted settlement. Resource matching allows one second; it is not byte-exact equality.

The fixtures at `tests:119–208` produce reservation/start/end/settlement, refusal, idempotence and threaded lock contention. One cap-disagreement case can throw inside `_run`'s reservation helper before runner admission; the ledger cap check is real, but that case is not proof of the runner branch. The over-cap test synthesizes a retained amount. No scheduler submission/accounting was exercised.

Exact validator limit: archived reservation cost is checked positive/finite, not recomputed from cores × walltime; archived cores are not fully rechecked as integers (`ledger:89–110,169`). No normal `reserve()` producer emits those inconsistencies. This is an altered-archive limitation to qualify in strong structural-validity claims, **not an additional tamper-proof archive or launch condition**. The declared normal ledger path satisfies R1.

### R2 — watermark repaired; shared index can lose a rep

The refit hook fsyncs a record before callback; the callback fsyncs timing then advances the monotone task watermark (`analyze.py:723–733`; `runner:417–423`). The documented interruption window permits at most one record ahead of the watermark. The fixture at `tests:289–310` actually throws in the third resample, leaves two records/watermark two, rolls back to one, requires zero-fit HELD, then resumes after restoration. This repairs the prior normal-return-only evidence.

Ordinary missing-binding and main/control domain checks are meaningful (`runner:273–286,333–354`; `tests:313–364`). The brief's claim that all domain checks precede reservation is too broad: resolved-seed comparison is at `316–322`, after reservation admission. It still precedes dataset fitting and binding; this ordering qualification alone is not a launch blocker.

**Remaining namespace gap:** each rep holds a different `task_<rep>.lock` (`298–300`), but all read and replace the same `task_index.json` (`336,352–354`). Main reps 0/1/2 starting together can read the same old map and overwrite one another's entries. Atomic replacement prevents torn files, not lost updates.

Lost index membership alone does not duplicate an intact restart. The bounded consequential trace is: a concurrent write drops rep 0; rep 0 retains an original cache for identity A but dies before status/timing/ACK; its binding is later absent; a changed declared identity B is presented. The guard checks B's cache/checkpoint and per-rep status/timing/ACK, and the index no longer names rep 0, so it overlooks the **preserved A cache** and admits fresh. This is not total joint evidence loss. The cache-producing portion presupposes repair of the separate fresh tuple defect below. Protect shared index read/merge/write or make missing-binding admission discover retained earlier-identity evidence; add the concurrent/preserved-cache producing case. No universal filesystem durability guarantee is requested.

### R3 — a HELD completed control can still qualify

Credit `row19_control_compare.py:37–120,143–185,199–201`: frozen manifest-derived identity/draws/bands/policy, exact complete target, individual checksums, typed fields, numeric/finite successful statistics, failed-parity nonqualification and typed C2 job linkage. Seven comparator fixtures produce pairs and substantive mutations; their kill remains honestly labelled desk evidence.

**Terminal status gap:** checks at `143–160` never require `phase="final"`, the role's expected exit, or absence of memory/HELD state. A normal C3 can restore some records, complete target 20, detect a breached peak and publish `phase="final", exit=4, memory_breach=true, target_complete=true` (`runner:431–468`). The comparator can still return qualified if scientific parity and other metadata hold. A `chain_done` status left by death before final publication is also admissible. Require a successful terminal control status using the existing fields; ordinary successful partial-B control completion returns 75, not main-chain exit 0. Bind C1/C3 job/role/root to their retained campaign entries rather than accepting any nonempty status job string (`151–152`).

**Filled walltime gap:** interruption checks `173–175` require only positive finite requested time and used ≥ requested; they never compare requested time to the bound C2 entry's `walltime_s`. The purported favourable fixture itself reserves C2 for 3600 s (`tests:67–75`) but writes requested 1800/used 1803 (`test_row19_control_compare.py:44–45`) and expects qualification. Match the actual filled request and retained resource witness. Produce a coherent favourable case plus HELD/nonfinal, role/job/root and requested-time mismatches. These are technical evidence checks, not new scientific thresholds or demands for a prelaunch PBS kill.

Separate report-label limit: failed-chain nonqualification is applied only when parity holds (`197–199`). If one chain fails or failed payloads differ, the combined gate returns nonzero for parity but can still print `QUALIFIED ... YES`. Mark any supplied failed procedure nonqualification independently of parity. This is misleading separate qualification reporting, not another combined exit-zero pass.

### R4 — fresh pulls do not close every false-green path

Credit fresh staging/rotation, failure-labelled stale evidence, ledger-derived expected jobs, named PBS observation failures, watermark/failure alarms and request-ID matching. The three fixtures use constructed `--no-pull` snapshots and honestly label local evidence; they do not produce an actual network pull or scheduler observation.

The fixture labelled “failed record with NO timing row” does not remove a timing row: its four-record run and copied snapshot retain all four rows, then only the checkpoint failure flag/reason/hash change (`test_row19_watch.py:41–55`). It proves checkpoint-derived failure despite stale timing saying not failed, a useful repair; it does not produce timing absence or the fsync/callback interruption.

**Schema gap:** `row19_watch.py:117–118` validates predictor keys but not each predictor's exact band keys/numeric/finite values or string `failed_reason`. Thus a coherently rehashed malformed statistic on a record marked not failed can count as strict accepted progress without alarm. Reuse the comparator's complete record contract; produce missing-band/string/nonfinite/reason negatives that reach it. This is an altered-evidence admission example, distinct from the natural stall below.

**Restored stall gap:** a C2 kill can land after its first record fsync but before timing/watermark callback, leaving one accepted record and no timing row. C3 legitimately restores it and can then stall in its first new refit. At `273–280`, `acc` is nonempty but `last_t` is absent, so neither first-record nor stall branch alarms at any elapsed time. Old C2 timing can instead anchor C3's clock prematurely. Use current runner start as the progress baseline until newer validated current-job timing exists; preserve the declared one-record interruption tolerance. Cross-check timing identities/indices against accepted records rather than only comparing counts (`265`). The present fixtures do not produce this recovery/stall case.

**Terminal evidence gap:** `282–287` checks only files a glob found. An ended job with no live log generates no terminal-witness alarm. Logs append across attempts, and the control root contains C2/C3 logs; any line starting `exit ` in the last three lines suffices, without current-job attribution or typed logger status. Require expected role/job terminal evidence, including absent/truncated logs and nonzero/missing logger status. The existing fixture creates a truncated file, not an absent file or old-attempt witness. Preserve runner exit separately from logger completeness.

Applying C3's ended check to every control log can also alarm on C2's deliberately killed log after C2 was diagnosed/settled. Attribute evidence to the entry being checked and preserve C2's expected external-kill diagnosis; do not demand a normal runner terminal line from the externally killed C2.

### R5 — final checks are before final aggregation

Credit pre-original zero-fit STOP/memory handling, request-bound acknowledgments, dispatch checks and the recheck immediately after the last refit/no-work restore (`runner:364–376,407–433`; `tests:367–385`). An in-flight fit may finish under the declared sampled boundary rule; no instantaneous kernel enforcement is requested.

**Remaining final boundary:** current STOP/memory flags are captured at `432–433`, before aggregation `451–457`, and reused for exit/ACK/publication `458–482`. A peak crossing 6 GiB inside aggregation can appear in final `maxrss_bytes` while `memory_breach` stays false and exit remains 0. A STOP arriving there can receive no ACK. Refresh current sampled peak/request after aggregation and at the declared terminal publication boundary, retaining completed results truthfully. A request after the last fit need not discard a completed chain.

The memory fixture does not produce its claimed completion branch: `tests:395` still contains `== DONE or True`; `399–403` changes `mem_stop_gib`, hence manifest SHA, and the restored task holds on binding mismatch (`runner:334–341`) before memory diagnosis. Use one unchanged bound manifest and controlled current observations to produce last-fit, aggregation and no-work cases; assert the actual reason. Admission memory refusal is credited separately.

**Logger defect:** both templates use `rc=${PIPESTATUS[0]}; tee_rc=${PIPESTATUS[1]}` (rep line 24; control line 29). The first assignment is a completed simple command and resets Bash `PIPESTATUS`; the second loses the original tee result, normally yielding an empty field. The newly appended terminal line is useful but does not retain both promised statuses. Capture the original array in one assignment before extracting either value, and retain/diagnose inability to write the terminal witness under the existing bounded policy. Exit may remain the runner's exit as declared; logger failure must be separately visible and alarmed. No producing shell/logger-failure fixture is present, and none was executed here.

### R6 — the honest fresh pipeline is rejected

**Immediate launch blocker:** real `Config.members` is a tuple (`analyze.py:70–72`); `layer_pipeline` retains it (`186,262`); `run_dataset` returns it unchanged (`288`). Fresh runner validation occurs **before** `write_orig` serialization (`runner:390–394`), while `run_problems:109` insists on a list. An honest fresh original therefore buys its fits and then HELDs with “members is not a non-empty list of names”, before cache/refit production. The stub at `tests:36` substitutes a list and masks this actual producer contract. Accept/normalize the real fresh tuple and decoded list, and make the no-fit fresh fixture preserve that container contract.

Credit raw-byte/dtype/shape nested serialization, payload plus metadata checksums, catch-all cache admission into HELD reasons and exact-leaf round-trip assertions. The companion `cluster_ws` is retained (`runner:454–455`), with actual aggregation unstubbed and fit counters demonstrating no purchased second chain (`tests:258–274`).

**Consumer admission remains incomplete:** `selected` is checked only as a length-L list (`134–135`). A coherently rehashed decoded `selected=[None]` passes that check but actual aggregation fails at `analyze.py:431–436` after remaining fits. Validate the selected fold/pair structure and the member/count/numeric contracts actually consumed, against cfg/dataset where applicable; this is a bounded malformed-cache counterexample, not a demand to harden all arbitrary data.

**Mutation fixtures stop at the wrong check:** bad-rank, nonfinite and undecodable mutations update `payload_sha` without updating `meta_sha` (`tests:241–250`). Metadata includes payload SHA (`runner:94–95,172–173`), so these cases hold on metadata mismatch before their advertised validators. Recompute both hashes and assert each intended reason/zero fits. The stale-payload and coherently rehashed negative-seconds checks are valid for their stated checks.

### R7 — timing/environment improvements stand; endpoints need precision

The manifest now has one prospective C1-derived W_int rule; stage 0 supplies only first-record planning expectations. Control target stays 0..19 under B=200, with no incompatible continuation promise. A different legal endpoint must be declared in the bound package before C1 submission. Wrapper path/hash, backend/machine/version and four one-thread caps are checked (`runner:195–229`). `JAX_PLATFORMS` uses `setdefault` rather than unconditional assignment, but observed backend admission still rejects a non-CPU backend; describe that mechanism accurately. Remote verification remains the implementer's claim.

Three declared resolved seeds are unique 31-bit integers, disjoint from the 4000 unique declared exclusions; historical derivation was not independently regenerated. The shared 1500-core-hour envelope is correct: one C3 gives `1416 + W_int <= 1464` for nine full main charges; a second C3 gives `1464 + W_int`, allowing nine only for W_int ≤36 h and otherwise eight. Four attempts per main dataset is not permission for twelve full charges or a completion forecast.

**Measurement labels still overstate the endpoint:** `publication_seconds` is captured at `runner:481`, before the final status rewrite at `482` and before `runner_end` ledger write at `493`. `wall_seconds_main` is captured at `465`, before publication writes. Yet status/manifest say final status/ACK/task/ledger writes and final publication are included. Move the endpoints or state the actual subscopes; do not claim measured ledger/final-write duration that is excluded. Whole-process CPU/RSS and mixed-scope utilisation are already qualified; compilation remains a proxy, not separately measured. The control template's W_int-from-addendum comment must follow the adopted C1 rule. No wrapper/startup benchmark or new fit is required for these corrections.

## Question 2: exact remaining list before reconsideration

1. **R6:** repair tuple/list fresh-original admission; complete consumer-critical cache checks; make coherently rehashed mutation fixtures reach/assert their actual validators.
2. **R2:** prevent shared task-index lost updates or find preserved earlier-identity evidence on missing-binding admission; produce the bounded concurrent/recovery case.
3. **R3:** reject HELD/nonfinal controls, bind C1/C3 terminal job/role/root evidence, and match C2's interruption request to its filled ledger walltime; correct the favourable fixture and add those negatives.
4. **R4:** apply the full checkpoint schema, validate current-job timing/progress, alarm on restored no-timing stalls, and require attributed terminal/logger evidence even when a log is absent.
5. **R5:** refresh current STOP/memory through aggregation/final publication and produce meaningful same-binding last/no-work cases; capture both original pipeline statuses correctly and diagnose terminal logger failure.
6. **R7:** correct publication/main-wall endpoints and declarations, the backend-setting wording and template W_int source; pin the revised package and re-review it.

Then append the declared watch expectations and stage-0 accounting addendum, obtain the owner's row-specific go, and use the stated staged launch order/reservations. The actual interrupted Lustre/PBS recovery result belongs in the slice report before stage 2. No new policy-matched reference, full-chain parity, larger campaign or scientific prelaunch fit is added to the execution-only slice gate.

The amended row-4 policy remains implemented but not adopted; M2S's conservative interim stays OPEN. The qualification slice reads no coverage, licenses no screen/confirmation/paid fallback and need not finish three chains inside its cap. Preserve source-owned stage-0 job `7516261.sched01` and token `7c70e6b9c77f`; this review did not poll or operate them. September's owner's go and paid-run hold, prior task closures/completion messages, and the separately completed favourable photo revision-10 reviews remain unchanged.

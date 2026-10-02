# Row 19 qualification-slice launch specification, revision 4 — Codex record

Date: 2 October 2026, Phoenix. Reviewer: `GPT: R052 Entropy paper`, native session `01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with launching C1 and main reps 0/1/2 from this package.** R1 remains closed and R2 is now closed. The tuple repair is real, but the new count validator rejects the actual fresh pipeline's floating-point `n_c` after its original fits. Other bounded control, observation and terminal-publication conditions remain. Appending watch expectations and stage-0 settlement, then obtaining owner go, would not by itself close them. This review approves no submission or account operation.

The proposed staged order remains reasonable: C1 plus the three main datasets, C2 after C1 supplies its original and first three refit timings, then C3 after C2's actual PBS kill, each through a prior campaign reservation. Actual Lustre/PBS recovery is an output of the slice, reviewed before stage 2; it is not a new prelaunch scientific-fit gate.

## Scope and immutable evidence

Accepted brief: Unimog `prompts/2026-10-02_codex_r052_row19_launch_specification_rev4.txt` at `87760fd0d3d9762117682ff841fa190032374cc0`, SHA256 `faf784b0956fd661e3477d74c44a93609e70d4cda43cfab1aef4af08441c4970`. Handoff `6ff747f1-343e-5098-b8bd-9cf26bea0c86` was read, review/log ownership committed at Unimog `930b4973`, and manager acceptance acknowledged before review edits. Claude retains implementation, manifest, ledger, protocol, framework, tracker, author frontmatter and dispatch ownership.

Reviewed candidate: **RSC `ab1d48a767a8339638acfb23efeb68c70a8b5b9b`**, containing implementation **`25da9e6b24507943c8ec5385e8a2eb80b81713d3`**. The descriptive manifest `code.commit` resolves to that implementation; all five `code.files` pins match its immutable blobs. Later repository HEAD is not the candidate.

| File, relative to `workspace_demo/t1_access/` | SHA256 |
|---|---|
| `analyze.py` | `5177e4a4eca90f6f04dcddc34d4c42c709b3d501b82a2d8919e09eedadfc4d7f` |
| `models.py` | `28765f82b3e718c48521cf775add6220898752c662c4cdd1c3ffcdb113c4feef` |
| `simulate.py` | `f588b9121be48ec553ab95e4dda5736941865498922468b5868c96758d0afe57` |
| `chpc/row19_slice.py` | `674604c9689cc3b19557161663808806e184b57af5ad555bb14cdf0541e05467` |
| `chpc/row19_ledger.py` | `d5cdcc7110478db962b25f84999ff462aed5083caf54463b60a1d01b62fe9aa7` |
| `chpc/row19_control_compare.py` | `a7f62e70be64be2cc4ad0016b57f19ea13a54f2c70af4474f655784137165c87` |
| `chpc/row19_watch.py` | `6dde5dfe6b141cfb06e68550e7090ccf492da551467e0495139afcdc808aa56f` |
| `chpc/row19_slice_manifest.json` | `b549c7304dfab780e942831fcbd62c4689599e66a7be0fe50bfad2915fd64061` |
| `chpc/row19_slice_rep.pbs.template` | `00629118be177d5517f5b4ca812809a6fae605c5eb85a66a5a074a1f290d9e35` |
| `chpc/row19_slice_control.pbs.template` | `7cae08513301aad94e9dad31560814f8ee651710e3693dfadc9ca14535f3cc8d` |
| `test_row19_slice.py` | `975f264bbc95e4a0833ddd7a2e5637403d65adc32c33d4a0452f0f5c3c367735` |
| `test_row19_control_compare.py` | `74ff1e3458a1f43fdb95471b1e325dc29c0e59538193203dd1ad401ba258b992` |
| `test_row19_watch.py` | `72cf04eb3e4ac4e9a47b05743cd3612aa29e5852a9c17521991d025fba4f60e0` |

The full brief and prior revision-3 record at `6d8a5971e859df2e98dd91a60f53a8865c6f34b4` were read, together with immutable runner/comparator/watcher/template and producing-fixture text and the real original-output/aggregation/identity interfaces. Unimog `rsc_t1_simulation_design.md` §11c/§12 and complete row 19, R052 header/latest entries, and the pinned model pre-registration supply the owning context. Three subordinate read-only reviewers checked index/domain, runner/cache and comparator/watch lanes. Their scratch notes are supporting analysis, not additional scientific outputs or canonical reviews.

No submitted module, function, import, test, fixture or CLI was executed. No fit, simulation, SSH/PBS/HPC/cloud/account operation, job submission, worktree or push occurred. Checking used standard-library git/blob/text/hash/JSON/AST and deterministic metadata only. No private plant/key, audit results, reader/human/pull output, audit website or D1 material was opened. Foreign files were preserved.

The brief reports **47 passing stub tests** and Lustre clone `rsc_slice` at `2d24e29`, with five pins and wrapper verified remotely. These are implementer evidence, not reviewer executions or remote authentication. AST confirms 47 named tests: 6 refit, 4 until, 17 runner, 8 comparator, 5 watcher, 7 start-policy. The control interruption fixture remains explicitly a desk stand-in, not a PBS kill. Test names/counts do not prove every claimed branch.

## Question 1: R2–R7 implementation and producing fixtures

| Condition | Disposition |
|---|---|
| R1: campaign reservation and terminal accounting | Remains closed for the declared operator/API path; ledger source is unchanged. |
| R2: shared index, missing binding and task domain | Closed by the locked current-map merge and producing three-process fixture. |
| R3: terminal controls and interruption evidence | Terminal/HELD, role/job, filled walltime and independent failed-procedure reporting repaired; root/reservation/checkpoint linkage remains incomplete. |
| R4: complete records, current-job progress and terminal observation | Shared schema and natural restored-stall path repaired; consumer-runtime, control-log and killed/settled-job observation contracts remain open. |
| R5: STOP, sampled peak and logger | Post-aggregation checks and PIPESTATUS retention repaired; declared terminal-publication check is still absent. |
| R6: honest original and consumer cache | Tuple, selected pairs and actual mutation reasons repaired; honest floating counts rejected, and nonnumeric `logq` still admitted. |
| R7: timing, environment and scopes | Wall/publication scopes, CPU backend assignment and C1 timing comment repaired; CPU/RSS sampling point still misstated. |

References below are immutable candidate line numbers. `runner` means `chpc/row19_slice.py`; `tests` means `test_row19_slice.py`.

### R2 — closed

`runner:243–261` takes the same exclusive `task_index.json.lock` for reads and merges. The merge re-reads the current map under the lock and publishes one changed rep key before unlocking; no earlier stale map is used. Per-rep ownership remains at `340–345`. Binding/index publication at `386–387` precedes original/cache/refit work. The previous concurrent lost-update route is removed. The prior review allowed this repair instead of an arbitrary earlier-identity cache scan; no new joint-evidence-loss or universal-storage requirement is added.

`tests:338–360` genuinely starts three forked processes for reps 0/1/2 under one root, requires all DONE and all three index entries, then removes rep 0's binding/status/timing while preserving its identity-A cache/index and changes its declared identity. It asserts zero-fit HELD for unexplained binding loss. No barrier forces a particular critical-section schedule; the source mechanism establishes why the old stale replacement cannot occur. The fixture skips environment/reservation checks and proves neither scheduler accounting nor campaign contention.

Role/target/seed checks now precede runner reservation admission (`306–338`), with dataset generation later. The operator's reserve-before-qsub token creation necessarily precedes the runner. The no-reservation fixture's absent-ledger assertion (`116–129`) does not independently prove that ordering; source does. Align two minor declarations: the manifest/brief say `task_index.lock`, while implementation uses `task_index.json.lock`; the runner's opening prose still lists reservation before domain. Neither defeats the repaired mechanism or adds a launch blocker.

### R3 — successful terminal controls repaired; retained root binding remains

Credit `row19_control_compare.py:72–97,145–201,208–211`: one complete record validator, terminal `phase="final"`, control exit 75, no memory breach/damage, expected frozen identity/code/policy/seed/B/target, proper C1/C3 roles/jobs from the ledger, a unique C2 job with requested walltime matching its reservation within one second, and any failed procedure nonqualification independently of parity. These close the former HELD/nonfinal pass, incoherent walltime and misleading separate qualification label. Exit 75 is correct for the completed 20-index subchain under B200.

The eight comparator fixtures now include coherent C2 reservation/request 1800 s and use 1803 s, bound `c1.sched/c2.sched/c3.sched`, plus terminal/exit/memory/job/role and requested-time negatives (`test_row19_control_compare.py:29–57,113–133`). Their seven-new-record C2 segment returns locally before the explicit stand-in kill record is supplied; the actual PBS kill remains unproved here, as intended. The equal-failed fixture does not separately produce differing failed payloads, but the independent refusal is explicit in source.

**Remaining prior condition:** the C1/C3 match consumes kind/rep/job only (`172–174`), ignoring ledger root/token and status reservation/checkpoint/manifest binding. Nothing requires selected C3's root to equal selected C2's. These metadata already exist (`runner:480–481`; `ledger:131–133`). Changing the favourable C3 entry's root, or its status reservation/checkpoint to a foreign token/path, leaves qualification unchanged. This is a bounded retained-evidence selection/admission counterexample, not a claim that honest fitting produces foreign paths. Match selected jobs to existing root/token/task/checkpoint evidence and require C3 to resume C2's root. Account explicitly for pulled local paths differing from remote absolute roots; no signature infrastructure or arbitrary archive-authentication gate is requested. Produce the bounded mismatched-root/token/checkpoint negatives.

### R4 — complete records and current-job baseline repaired; observation integration remains

The watch now uses the comparator's complete `validate_record` (`watch:29,89–113`), so missing bands, string/nonnumeric or nonfinite successful statistics and malformed failure reasons cannot count as strict progress. Timing indices are cross-checked (`287–289`); current-job rows are selected by job ID (`258`), and baseline starts at this runner's start and advances from its own accepted indices (`298–306`). The prior natural restored-record/no-timing stall is repaired.

`test_row19_watch.py:70–95` reaches missing-band validation, lost-record/watermark/orphan-timing alarms, and actually removes timing for a resumed job whose start is aged five hours. The specific current-job allowance alarm is required. The separate failed-record case retains preexisting timing; it proves checkpoint-derived failure despite stale timing, not a callback interruption. All five tests use constructed `--no-pull` snapshots, not a fresh network pull or scheduler observation.

**Mac consumer identity is not frozen:** `expected_contract:61,68` calls the local `dataset_identity`, whose numerical snapshot hashes local Python/JAX/NumPy/SciPy versions (`analyze.py:481–492,516`). The template explicitly calls for comparison on the Mac (control line 22), and the watch runs there. The manifest pins the Lengau producer, but declares no matching consumer runtime or verified target-snapshot reconstruction. A different Mac runtime rejects every intact native task before observation/comparison. Freeze a compatible no-fit consumer environment or reconstruct using the verified target numerical snapshot while preserving identity/draw checks. No particular installed Mac version is assumed in this immutable finding; local stub identities produced and consumed in the same environment do not establish the cross-host interface.

**Control-log naming is unresolved:** `watch:116–118` expects `live_ctl_c1.log`/`c2.log`/`c3.log`; the control template writes `live_ctl___MODE__.log` (`30,33`) independently of `__KIND__`. Comments describe normal/interrupted/resume, and no declaration freezes MODE=kind. Filling MODE=normal or resume yields a correct terminal witness in a file the watcher never checks. Use kind directly, freeze MODE=kind, or retain an explicit filled producer/consumer mapping. A C1/C3 template-naming witness is missing from the present main-log fixtures.

**Execution end and financial settlement remain conflated:** the watcher notes C2's expected external kill at `233–234`, but `running` at `265` still means live reservation and no runner exit. A known-killed C2 can remain charged until settlement and later trip the running-stall/startup alarms (`237,298–306`). Separate known terminal execution from live financial charge, requiring the typed native kill/interruption evidence and retaining the full reservation until scheduler settlement. The C2 fixture (`118–128`) is just started, has only a job-id JSON, no task and no qstat, and stays within startup allowance; it does not produce the aged known-kill phase.

Conversely, the loop skips all settled entries (`203–205`). Normal accounting settlement before the next two-hour poll bypasses unresolved terminal/log/HELD checks, despite the declared “every ENDED entry” rule. Keep unresolved observation/diagnosis obligations through settlement, or prospectively require and record operator technical verification before settlement. Accounting settlement alone is not logger qualification. This does not require reopening diagnosed historical jobs.

**Bounded validation/declaration limits:** accepted-index timing timestamps used for rate/stall are not checked typed/finite (`268–269,300`); a coherently altered same-job `t=Infinity` suppresses stall. The terminal regexp accepts a prefix through `end ` without a complete timestamp/line (`37,125–128`); a torn witness can be called complete even though native PBS stdout holds LOGGER FAILURE. These are altered/torn operational-evidence limits, not ordinary callback products or universal filesystem-proof requirements. Apply bounded validity checks to fields used for health and require a complete attributed witness or explicitly retained native logger diagnosis. Do not describe partially checked timing/prefixes as complete validated observations.

Main ended-job fixtures at `98–117` genuinely cover absent log, old job, original tee failure, exit mismatch and a clean witness for entries reached by the loop. The attributed main-witness repair stands; the unresolved producer and lifecycle cases above do not undo it.

### R5 — aggregation and pipe-status repairs stand; terminal refresh is absent

`runner:491–505` refreshes STOP and sampled peak after aggregation, preserves completed results, and returns HELD for an aggregation memory crossing. It acknowledges the applicable request (`515–517`). Admission, dispatch and last-refit/no-work checks remain. An in-flight fit may finish under the declared sampled-boundary rule; no instantaneous enforcement is requested.

**Remaining stated terminal boundary:** final status/ACK/task writes are at `514–520`, followed by declared `t_term` at `521`. There is no new STOP/peak reading there. A STOP arriving during those writes can skip ACK, or a peak first crossing there can still leave exit 0 and memory_breach false. Refresh current request/peak at this one declared boundary, before the explicitly excluded final status rewrite and ledger tail. Preserve completed results, the sampled rule and truthful ACK/exit; this is not a demand for an unbounded sequence of final-byte checks.

The new same-binding fixtures (`tests:437–495`) remove the old `or True`/manifest-rebinding problem and reach their intended branches: a controlled sampled crossing stops after three of four refits, **before the fourth**, rather than first crossing in the final fit; an aggregation-only crossing requires final exit 4 and retained result; an aggregation STOP produces its actual ACK while retaining DONE; a partial-B no-work control raises STOP after admission and requires the “no work bought” ACK. Admission memory refusal is also real (`500–506`). The cases keep each root's manifest unchanged; they are not one shared task binding across all roots. No producing publication-window case exists. Add that bounded window and preserve the real final-fit/no-work branch labels; no scientific run is required.

Both templates now capture the original pipeline's statuses together as `ps=("${PIPESTATUS[@]}")` before extraction (rep line 24, control line 31). The terminal line names runner exit, original tee exit and PBS job ID; a failed witness write or original tee emits LOGGER FAILURE, while job exit retains runner status. This closes the sequential-assignment defect. No submitted shell/logger-failure fixture was executed or produced here; that evidence limit does not add a shell benchmark gate for the direct repair. The watcher integration above still determines which witness is observed.

### R6 — tuple and mutation repairs stand; honest floating counts fail

The tuple/list repair is correct (`runner:109–112`); the stub now returns actual `cfg.members` (`tests:38`) and preserves it in exact-leaf round-trip checks. Selected fold/pair/name structure is checked (`135–144`), fixing the former `selected=[None]` consumer crash. Nested raw-byte/dtype/shape serialization, explicit decode/HELD reasons and retained companion aggregation without a second chain remain useful.

**Immediate fresh-path blocker:** real `layer_pipeline` creates `n_c = np.bincount(...).astype(float)` (`analyze.py:189`), and `run_dataset` returns it unchanged (`291`). New admission demands integer dtype (`runner:145–147`). The actual fresh path calls the real original and validates before cache write (`423–427`), so honest positive integral-valued floating counts HELD with “n_c is not positive integer counts” after the original fits. The stub still supplies integer `np.full(C,3)` (`tests:43`), masking this producer contract. Accept/validate finite positive integral-valued floating counts, or normalize consistently, and make the no-fit fresh/cache fixture preserve the real dtype. Changing the scientific fitting algorithm is unnecessary.

**Numeric consumer admission:** `logq` is checked only as an ndarray of shape `(L,M,C)` (`131–132`). A coherently payload-and-metadata-rehashed Unicode array of that same shape is admitted; actual aggregation's `np.nansum` (`analyze.py:438`) then raises after remaining refits. Refuse nonnumeric consumer arrays before fitting and assert the bounded mutation's actual HELD reason. This is altered-cache admission, separate from the honest count blocker. Member order versus cfg and G/X pair direction remain broader provenance limitations; no additional crash/scientific decision change is established, so they are not extra launch gates.

The revised mutations (`tests:226–279`, `_rehash:102–103`) genuinely refresh both checksums and assert intended reasons with zero fits for bad rank, nonfinite delta, decode, selected, foreign pair and zero-count cases. Stale payload deliberately reaches its checksum, and negative seconds reaches its own check. The old wrong-validator evidence problem is closed; there is no nonnumeric-logq fixture yet.

### R7 — corrected scopes credited; CPU/RSS point must be honest

Wall/publication endpoints at `runner:521–525` now include the first final status/ACK/task writes and explicitly exclude the final rewrite and `runner_end` ledger write (`536`). Their new declarations match. JAX_PLATFORMS is assigned unconditionally before imports (line 30), CPU/thread/backend admission stands, and the control comment now derives W_int from C1. The wrapper/remote clone observation remains implementer evidence.

**Remaining sample-point statement:** whole-process CPU is sampled at `503`, RSS at `505`, before publication writes, while manifest measurements say both are sampled at the terminal boundary. Utilisation uses that earlier CPU sample over later wall duration (`524`). Move sampling to the same declared boundary with the R5 check, or state the actual earlier scope explicitly. No wrapper/startup measurement or fit is needed.

The prospective C1-derived W_int rule, B200 exact target 0..19 without control continuation, 1-core requests and 1500-core-hour envelope remain coherent. Three declared seeds are unique/disjoint from 4000 unique exclusions; historical derivation was not regenerated. With one C3, nine full main charges cost `1416 + W_int <= 1464`; a second C3 allows nine only at W_int <=36 h, otherwise eight. Four attempts per dataset does not license twelve full charges or promise completion.

## Question 2: exact remaining list before reconsideration

1. **R6:** admit the honest floating-count representation and correct the fresh/cache fixture; refuse nonnumeric `logq` through a producing, coherently rehashed, reason-specific no-fit case.
2. **R3:** bind selected C1/C3 status reservation/task/checkpoint/root to their retained ledger entries and C3 to C2's root; produce bounded mismatched-root/token/checkpoint negatives.
3. **R4:** freeze the compatible Mac consumer runtime or verified target-snapshot reconstruction, preserving strict identity/draw validation.
4. **R4:** freeze the control-log MODE/kind mapping and require complete attributed terminal/logger observation, including the bounded torn-witness case.
5. **R4:** distinguish a known-killed C2 execution from its still-charged reservation; retain unresolved observation/HELD obligations after financial settlement or record the operator's prerequisite technical diagnosis. Produce the aged known-kill/settlement ordering cases and validate the finite timing fields used for health.
6. **R5/R7:** refresh current STOP/peak at the declared terminal-publication boundary, produce that same-binding window, and align CPU/RSS sample-point declarations with the implementation.
7. Pin the corrected package and align its brief/manifest/row/tracker summaries with these actual repairs and fixture limits; the index-lock basename/order wording is a declaration correction, not a reopened R2 gate.

Then append the declared watch expectations and stage-0 accounting settlement, obtain the owner's row-specific go, and use the staged launch order/reservations. The actual interrupted Lustre/PBS recovery result and slice report still go to Codex before stage 2. No new policy-matched reference, full-chain parity, larger campaign, scientific prelaunch fit or universal kernel/filesystem guarantee is added.

The row-4 policy is implemented but not adopted; M2S's conservative interim stays OPEN. This execution slice reads no coverage, licenses no screen/confirmation/paid fallback and need not finish three chains inside its cap. Preserve source-owned stage-0 job `7516261.sched01` and token `7c70e6b9c77f`; this review did not poll or operate them. September's owner's go and paid-run hold, all prior closures/single completion reports, and the separately completed photo revision-10 reviews and source/R084 execution ownership remain unchanged.

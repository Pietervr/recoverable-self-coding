# R052 — early EC2 + Lengau production design second opinion

10 October 2026. Codex, exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic `95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Brief: Unimog `8b76de47c1f45485cd2f86e45b57d31d0812ed40`,
`prompts/2026-10-10_codex_r052_ec2_production_design.txt`, SHA256
`b354a1d17abb35307468f367ce8d66e16c63372d3aefe7a12542baef242c810f`.
Reviewed design: RSC `127bf5b79d77db52872e451aa7f97c92784a3cf2`,
[`aws_ec2/PRODUCTION_DESIGN.md`](../aws_ec2/PRODUCTION_DESIGN.md), SHA256
`7d10696b05cc1ba0d51c40de4952f6e7887875e797a30be14f818e83081d6bb4`.
Ownership committed at Unimog `cee8ec40`; incoming
`2f58abee-5e76-55c2-8e6e-38f7e0503439` accepted before edits or delegation.

## Verdict and the four answers

**FAVOURABLE TO BUILD** an unlaunched implementation of this fixed-partition direction,
with the requirements below made explicit. **This draft is not a production adoption,
launch or canonical-ingestion authority.** No literal ADOPT is issued for an unbuilt
version-10 package or an unobserved EC2 qualification.

| Requested question | Answer |
| --- | --- |
| Is immutable partitioning acceptable claim authority? | **Yes, for provider ownership during a fixed epoch.** A dynamic cross-provider meeting-point service is not mandatory when both admissions enforce the same disjoint declaration. Within-EC2 allocation, retry fencing, initial cutover and later transfer still need authority. |
| Ingestion and verifier/status adapter scope? | A substantive provider-aware controller extension: operational manifest derivation, original producer evidence, complete validation and recoverable publication, EC2 attempts/outcomes/settlement, chronological reconciliation, qualification, STOP and fresh whole-role gates. A planner filter or PBS-ID substitution is insufficient. |
| Are row 23 plus four duplicates per instance adequate production qualification? | **No, as the complete qualification.** Row 23 can supply exact-profile parity/timing evidence if its declared criterion succeeds. Four duplicates are continuing drift checks. Representative target-index evidence, intended resource/deadline behavior and actual producer/recovery/ingestion qualification remain. |
| Anything blocks building now? | **No blocker to developing this implementation and its component fixtures now.** Correct the operational contract and specify the authority/qualification gates while building. The draft's 80 slots and roughly 19–21-hour work window do not satisfy the literal current manifest. |

The owner's “continue if the runs are a success” remains a standing conditional go;
there is no new expiry or request for permission. The declared row-23 success condition
and a favourable concrete production package/actual qualification still precede production
admission. Existing independently gated Lengau work continues under its current authority.
The current source-reported USD 42 benchmark ceiling and USD 3,000 further-spend cap stand.
This design opinion neither enlarges them nor re-reviews the active benchmark or its results.

## 1. Fixed ownership replaces the moving boundary, not all claims and fencing

The proposed EC2 set is `(rep 3..102, index 200-k..199)` of the same frozen B200 tasks.
Bind strict integer `k`, exact coordinate set, frozen scientific manifest/task identities,
provider names, epoch and effective activation to immutable `ec2_block.json` and reviewed
controls. Both providers' admission paths must verify that declaration. Include supplied,
restored and retry plans; filtering only Lengau's new planner does not protect those paths.

Before activation, reconcile all reserved, queued, running and unresolved Lengau plans,
claims and retained completion evidence against the selected block. Either prove no live
prior assignment intersects it, or leave those coordinates with their prior authority.
“Lengau would not reach it for weeks” is useful scheduling context, not the cutover proof.
Disjoint existing jobs need not be cancelled. Current planning sees local root/campaign
plans (`row19_screen_admit.py:393–469`) and its lock is local (`:1427`).

Inside EC2, use one durable authority to allocate disjoint instance plans and reserve spend
before dispatch. Bind provider/run/instance/attempt/slot, exact plan, block epoch and a
monotone producer sequence or equivalent predecessor relation. A timeout, no output or
ambiguous API answer cannot release a claim or its funding. Retry the same saved request,
including token, region/subnet/AZ, userdata and plan bytes. Reassignment requires attributable
terminal/revocation evidence, reconciliation of pending output and refusal of superseded late
producers at ingestion. Separate attempt prefixes prevent one retry from rewriting another's
evidence. EC2 idempotency concerns the same API operation and parameters; it does not allocate
scientific coordinates. [EC2 idempotency](https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html).

Retain every declaration and each accepted record's dispatch epoch. Changing only `k` cannot
describe ownership history: shrinking 50 to 25 removes indices 150–174 from the newest block
although accepted records there remain EC2's. Increasing it can intersect existing Lengau
plans. Transfer only explicitly named uncompleted coordinates after prior claims are
terminal/fenced and pending publications reconciled. Do not reinterpret old records using
only the newest boundary. Transfers are operational decisions, never selected by fit outcome.

## 2. Use a reviewed operational derivative without changing scientific tasks

Keep dataset generation, resolved seeds, folds, complete B200 draw matrix, fit seeds,
Config, scientific sources and failure/usable rules frozen. Pin the parent manifest and
the exact allowed operational differences for an EC2 manifest: instance root/campaign,
worker slots, cost/deadline/memory policy and provider metadata. This is an explicit
derivation, not the claim that changed instance-root bytes still hash to `43b75f94…`.

Two concrete mismatches need resolution in the design:

- The current manifest has 24 cores. `row19_shard.py:233–236` refuses an 80-slot plan.
  Specify and review the EC2 operational slot allowance instead of bypassing job-start.
- Its `expect_layer_s=90000` is 25 hours. With `longest=0`, the unchanged first-fit rule
  (`row19_shard.py:318,332–334`) requires that much time before WORKER_DEADLINE. A roughly
  19–21-hour lifetime plus a short upload allowance will refuse the first work. Choose a
  compatible work window or a measured, reviewed operational expectation, then separately
  reserve setup, cleanup, upload, reaper grace and billing latency. The pre-fit check is an
  admission heuristic; it cannot promise that an in-flight fit finishes by shutdown.

Retain original EC2 bindings and effective B_full attestations as immutable provider
evidence. `binding_for` includes actual manifest SHA and root-dependent `ckpt`/`orig` paths;
`binding_problem` requires exact equality (`row19_shard.py:186–213`), and the verifier
reconstructs the canonical Lengau binding (`row19_screen_verify.py:200–206`). Therefore
**do not overwrite or relabel Lengau `task_<rep>.json` with an EC2 binding**. Validate the
frozen scientific projection and allowed operational derivation, and bind both to the
EC2 producer. Pin effective XLA/NumPy dispatch, OpenBLAS implementation/core, thread caps,
wrapper/archive/source hashes and instance hardware, not merely the profile name or
dataset identity. Native A refusal is not an eligible production fallback.

## 3. Ingest complete attributable units, preserving every attempt

The draft's staging, `read_record`, no-replace link and contrary-duplicate HOLD direction
is sound. The implementation needs a declared validation boundary:

1. Stage an immutable inventory of canonical filenames and content hashes for the attempt;
   bind its plan, scientific/operational manifests, profile, epoch and transfer certificate.
   Reject missing, extra, aliased or misnamed task files and malformed inventory before
   counting an import. Do not infer whole-attempt completeness from an S3 prefix listing.
2. Independently validate each record's own checksum/schema, frozen identity/draw/index and
   corresponding producer/slot/task binding. Validate finite, bound timing/occupancy fields,
   with positive wall time when used for rates, explicit start/finish/exit/censoring outcomes,
   and the actual qualification/profile gate. Preserve valid procedure-level failed records;
   do not select only successful fits into the fixed denominator.
3. Publish a record/timing pair with a recoverable coordinate commit journal/lock or equivalent
   protocol. Existing publication is timing first, then the no-replace record link
   (`row19_shard.py:339–342`). A replay/crash must not attach one attempt's timing to another's
   record, rewrite a timing under an accepted record, or count half an imported pair. Keep
   the evidence and an explicit held/incomplete state until reconciliation succeeds.
4. Compare independently valid duplicates using the verifier's canonical scientific
   `float.hex()` representation, excluding legitimately variable timing/record checksum.
   Identical payloads count once; preserve all producing attempts, distinct timings and
   paid costs separately. A contrary payload holds without replacing either piece of
   evidence. Never use last writer or arrival order as scientific authority.

S3 provides strong consistency for individual object operations, not an atomic transaction
across a bundle of record, timing, binding and outcome keys. The immutable inventory and
publication protocol must establish that application-level consistency.
[S3 consistency model](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel).

Interrupted attempts may retain useful completed units if the declared production protocol
can prove their profile, qualification, exact transfer and attribution. Incomplete units
receive no completion credit; all paid attempt costs remain. Qualification work and the
four sentinel records stay in separate namespaces and never become additional screen
datasets or bootstrap indices.

## 4. The verifier/status/admission adapter must understand two producer kinds

Current screen machinery expects PBS jobs and core-hour reservations
(`row19_screen_status.py:391–425`, `row19_screen_admit.py:476–490,963–1041`). An EC2 attempt
string cannot simply replace a numeric PBS ID. Define tagged producer kinds, immutable
plan/slot evidence, chronological predecessor rules, explicit outcome partitions and
provider-specific settlement. Whole-role receipts must cover every retained/live/failed/
unresolved EC2 attempt and Lengau job; unknown EC2 outcomes cannot receive a summary waiver.
Retain original completion, current artifact/binding checks, closed-no-record disposition,
generation/freshness requirements and exact all-attempt accounting.

Keep USD settlement separate from CHPC core-hours. Enforce applicable live reservations and
both spending envelopes before dispatch; do not invent a core-hour conversion or enlarge
the Lengau pilot's max-job-100 scope by treating EC2 attempts as its jobs. EC2 requires a
separate declared qualification/adoption scope and enforceable attempt/resource limits.

Specify how common STOP reaches EC2 admission, worker supervision and ingestion, its
acknowledgment/latency and treatment of in-flight units. A local Lengau file alone cannot
stop a remote instance. Existing worker STOP/deadline checks occur before the next index,
not during a fit. Preserve bounded termination/accounting and hold affected mixed-output
release after a conflict; do not erase evidence or let a sentinel failure be followed by
new EC2 starts. This review itself introduces no stop on current jobs or the independent
raw-bank lane.

Version 10 must pin all changed consumers and new authority/ingestion files, retain previous
lineage/evidence and obtain exact committed controls adoption and fresh provider-aware
qualification/receipts. The current authority predicate requires an actual controls-file
SHA and matching literal version-bound review (`programme_gate.py:188–227`). This design
record supplies neither an invented future hash nor an automatic replacement for the
adopted generation-9 Lengau pilot.

## 5. Row 23 and four duplicates are evidence for qualification, not its entire gate

Conditional row-23 success means the actual declared 36 B_full refits at index 0 have equal
identities and float-bit scientific payloads, the historical row-6 panel is exact and the
comparator is valid. Job-start identity admission alone does not establish that result.
Row 6 stays evidence for its own pipeline. Different bootstrap indices change draws,
inherited fold sizes and fit seeds (`row19_shard.py:97–116`); identity does not attest the
effective CPU/ISA/dispatch profile. Exact output equality remains an empirical, scoped
claim; JAX documents compiler-induced numerical differences.
[JAX numerical FAQ](https://docs.jax.dev/en/latest/faq.html#jit-changes-the-exact-numerics-of-outputs).

Predeclare a bounded prospective qualification covering multiple reps and representative
bootstrap indices, including the actual EC2 block; pin the reference coordinates before
outcomes. Use isolated shadow references so parity work does not defeat exclusive production
ownership. Include successful finite paths, report failed/nonfinite equality separately,
and do not change min-usable/B200, substitute datasets or select qualification by result.
Bind fresh-process/restart and actual intended hardware/profile evidence, aggregate memory/
occupancy/deadlines and interrupted publication/restore/ingestion behavior. Component crash,
replay and conflict cases can use synthetic fixtures; specify the bounded scientific panel
and its funding rather than silently adding a campaign.

Four outcome-independent rotating completed-Lengau coordinates per instance are useful
ongoing drift sentinels. They do not prove parity at untested tail indices or qualify a
different packing. **Hold each instance's imported output until its own required sentinels
and profile checks pass; hold the first instance additionally until the complete prospective
qualification and coherent controller gates pass.** A first batch is not released merely
because four payloads match. Sentinel failure/censoring and drift have explicit held/stop
outcomes and remain paid. Any later review of affected accepted outputs preserves evidence.

Packing also needs a specific total: c7a.24xlarge has 192 GiB. At the source's reported
2.32 GiB per worker, 80 consume 185.60 GiB, leaving 6.40 GiB before system/transfer overhead;
80 production plus four simultaneous sentinels consume **194.88 GiB**. Schedule sentinels
within the qualified concurrency or sequentially and cost that time. The frozen per-worker
memory stop of 4.5 GiB does not enforce a 2.32 GiB aggregate envelope. Row 23's source-reported
36 B workers plus six panels do not qualify an 80-refit packing or provide its measured cost.
[AWS C7a specifications](https://aws.amazon.com/ec2/instance-types/c7a/).

## 6. Fix the funding baseline and cost the complete attempt contract

The cap begins **12 September 21:50 UTC**. A total since 13 September omits the remainder
of the 12th. Reconcile that interval, delayed/unsettled charges, live/ambiguous benchmark
reservations and other applicable AWS spending before asserting available funds. Treat
the brief's Cost Explorer totals, Spot prices and runtime/memory estimates as operator
reports. Cost Explorer can lag beyond 24 hours; it is not a real-time admission ledger.
[AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html).

Use shared budget locking across all production instance admissions and the common further-
spend ledger. Reserve both the proposed USD 2,300 production envelope and the USD 3,000
cumulative cap, retaining funded ambiguity and attributable terminal compute/storage
accounting. Pin each attempt's price ceiling, instance/region/AZ, lifetime, grace/cleanup
reserve and ancillary retention/transfer assumptions. Count sentinels, qualification,
failed/censored/interrupted attempts, replays, final partial batches, setup/upload, EBS,
IPv4, S3 and continuing applicable idle charges. A retry does not reset either cap.

`floor(2300 / (100 * unit_cost))` is a provisional yield forecast, not an enforceable
completion guarantee. At raw USD 0.39–0.55 it gives `k=58..41` before those allowances;
“40–55” is approximate planning. Measured full-instance occupancy, useful completions and
all paid overhead determine the funded declaration. The rounded USD 390 + USD 42 + USD
2,300 already leaves only USD 268 for missing/delayed/other costs. If funding ends, retain
the immutable block and honest unfinished units until an explicit transfer/declaration;
do not reduce the fixed B200 or issue a full-screen scientific release from a funded subset.

Spot interruption notices are best effort, so periodic transfer and partial-unit recovery
must tolerate termination without a successful final upload. Neither a price ceiling nor
four passing sentinels buys uninterrupted completion.
[Spot interruption notices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html).
The draft's explicit statement that the whole screen is not funded is correct to retain.
This review assumes no cap lift or HEAL1922 authority and establishes no fresh CSCI1913 balance.

## Build sequence and verification limits

Build the fixed declaration/cutover and provider binding model first; then the unlaunched
EC2 plan/budget authority, staging/ingestion and provider-aware verifier/status/admission
package. Exercise boundary, concurrent allocation, ambiguous replay, superseded late writer,
invalid transfer, swapped producer/timing, interrupted paired publication, contrary duplicate,
STOP and reservation recovery with bounded fixtures. Return exact committed controls/manifest/
source pins, those checks and the predeclared costed qualification plan for concrete review.
After actual declared row-23 success, qualify that reviewed configuration under the standing
conditional go and applicable envelopes. Only its actual reviewed qualification/adoption
permits canonical production import and further gated admissions.

The design and incoming brief were read whole and their committed bytes verified. Prior
`2cc26ee` and `137b261` records were read as design requirements; their dated package verdicts
and historical benchmark amounts were not rewritten. Three read-only peers covered authority/
ingestion, qualification and resource/accounting. No benchmark result or scientific payload
was opened; source job-start, prices, costs and current-run state remain operator reports.
No source/controller/science imports or execution, runtime tests, fits/simulations, account/
AWS/SSH/Lengau actions, worktrees or pushes occurred. Existing jobs/watchers and foreign files
were preserved. Prior row-6 and full-bank R2 exposure remain disclosed; target-visible,
concept-batched R2 is not later blind calibration.

Claude owns implementation/design/current docs/frontmatter/generated indexes/tracker/ledgers/
adoption/qualification and dispatch. Codex owns only this record and its own R052 appends,
prompts and lifecycle. Completion is routed once to that source; no duplicate earlier report,
renewed go or launch is performed here.

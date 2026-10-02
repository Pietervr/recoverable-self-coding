# Row 20 Stage A, revision 3: Codex static review

2 October 2026. Reviewer: Codex, session `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with launching Stage A from RSC
`a59fc2dca9bd580f887f09d4e8b99404664f6bf2`.** The attestation format is agreed;
the implementation does not yet enforce all seven closure groups. This record
contains no favourable machine attestation and cannot support a go. It approves
no capture, reader call, Stage B run, cloud or HPC operation.

## Scope and reproduced identity

This answers all four questions in Unimog
`prompts/2026-10-02_codex_r052_row20_row_review_rev3.txt`, committed at
`680b3f8cd0d6328561fff118d719190ff54af491`, SHA-256
`decb9a5c3c4ef792bb75a5079c4f48f03028d809343cd70f34b8b1ffe5384dc3`.
Handoff `13a0af90-e6ae-590c-a657-aa02dffa00dd` was accepted after ownership was
recorded in R052 at Unimog `e0096448`, before substantive review work.

Stage A is the one-view engineering qualification: frozen grayscale/dose inputs,
the instrumented text-runtime image path followed by a separate native reference,
fixed parity tolerances, bounded diagnostics, then an independently validated
report. It does not establish the later two-view development instrument or qualify
the AI reader. The owning specification is Unimog
`project_knowledge/rsc_t1_two_channel_framework.md` §§8.2, 8.4 and 8.6; row 20 in
`project_knowledge/rsc_t1_simulation_design.md` remains submitted, without a go.

All source references below are to the exact `a59fc2d` git blobs, under
`workspace_demo/t1_access/stimuli/photo/` unless another path is given. I read the
submitted criteria, readiness, controller, guards, runner, report, enforcement,
memory probe, plan/identity/receipt metadata, fixtures and test source. Construction
metadata and the moved AI-reader delta were checked read-only. Three helpers
performed bounded static checks; their findings were checked against the source.
No submitted module was imported, no test or fixture rerun, no model loaded, and
no image opened or named. No private audit answers/results were accessed. The
temporary snapshot and standard-library JSON/hash arithmetic are review aids,
not scientific outputs. Construction labels and aliases seen here make this
conversation unsuitable as a blind naming context.

The five submitted hashes reproduce from git bytes and the plan envelope's
declared sorted JSON encoding:

| Field | SHA-256 |
|---|---|
| criteria_sha256 | `277c6743ab99cad6c9163bf88d7dc469b2d3b5790c5b994656b562cf067bd5dc` |
| identity_sha256 | `e242499223991042779c98049205cfd45e51fe2e4830e53dd054d3b5383d628e` |
| plan_sha256 | `b349d35185cbe5f8e917d88e71bcb64779576286a977b97eaad2d442c163f23e` |
| manifest_sha256 | `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448` |
| budget_sha256 | `a4b833ddde953234cf209f62ae09b7068bfbe1bf62f4d3aec764f3caa1d0a9bf` |

The inner identity also reproduces:
`1aa94baf55378a29269b1bd9b5cf3fc91f71c3af13c90233e4d28ff4e01ef13b`.
All nine local-source digests, the packet source, the committed import-map digest
and the positions-receipt digest agree with that identity at `a59fc2d`. These are
runtime enforcement gaps, not a mismatched submitted snapshot. Existing model,
lens and installed-package bytes were not freshly opened or rehashed by this
review.

Plan inputs, attempts and diagnostics equal revision 2. There are 178 unique new
ids: 140 mandatory instrumented, 16 mechanics, two suffix diagnostics and 20
native references. With 16 carried engineering attempts this is **194/200**;
the six remaining attempts are only for an explicitly authorised interrupted-try
recovery. The **1,808.73 s** carry remains 8.73 measured plus the declared 1,800 s
allowance. Limits remain A: 200 attempts/4 h/1 GiB; B: 1,856/4 h/8 GiB; aggregate:
2,056/8 h/9 GiB; task memory 48 GiB. No limit is reset or expanded here.

## 1. Attestation format: agreed, with guard repairs

The proposed v1 fields are sufficient: row, stage, explicit verdict, reviewer,
date, full reviewed source commit, and the five package hashes. The go separately
names the later immutable commit/path/hash containing the review record and the
owner's dated words. This avoids a circular source/review hash dependency. **No
additional attestation field is requested.**

The parser/equality repair is substantial: `stage_a_guard.py:250` and `:272`
parse the record rather than treating unrelated non-negative prose as approval;
Stage A supplies reviewed-package re-derivation. The selected negative-record
list is supplementary; absence of a positive matching attestation must remain
the general rejection rule.

Tighten the existing schema implementation: require exact package keys and digest
types/lengths, full hexadecimal immutable commit ids resolving to commit objects,
and a properly delimited block. Currently commit checks at `:284` and `:295`
mostly test length; the package union at `:297` permits an extra key with null in
both go and attestation because the current package also supplies `None` for a
missing key. `parse_attestation` does not explicitly require the closing delimiter.
These are guard repairs within the agreed format, not reasons to invent a new
approval format.

## 2. Seven closure groups: enforcement and evidence

### Group 1 — approval, execution identity and positions: partly repaired

Fresh controller identity hashing, failure on upstream git errors, the per-file
map, and a plan-bound receipt recording both carriers passing are useful repairs.
Planning refuses positional disagreement before publishing the plan and receipt
(`stage_a.py:864`). Three material identity paths remain open:

- `desk_gates` computes identity once and writes `out/identity_files.now.json`
  (`stage_a.py:395`). Workers instead consume `Ctx.identity_files`, the source-tree
  map, at `:610` and `:777`. `check_imported_origins` (`stage_a_guard.py:218`) trusts
  that map without comparing its bytes with the admitted
  `package_file_maps_sha256`. A changed root/hash map can authorise a shadowing
  module while the five approval hashes stay unchanged. Bind the map actually
  consumed, preferably the controller's validated map.
- `worker_open` reads the frozen inner identity at `stage_a.py:443`; it does not
  recompute it. There is no fresh equality check in each worker, including report.
  Watched module-origin checks do not cover changed local code, weights, lens or
  receipt between phases. The same-run environment boolean is insufficient to
  bind later reporting code. Revalidate each phase or enforce an immutable
  admitted execution snapshot.
- `package_at_commit` (`stage_a.py:413`) rehashes the four saved artefacts and
  envelope, without proving that the identity's local-source/packet/map/receipt
  hashes describe their blobs at that source commit. Enforce that relationship.
  It happens to hold in this submission; the builder must reject when it does not.

`GoAttestation` exercises selected schema/equality mutations but substitutes
callbacks for the actual reviewed-package builder. The origin test uses mock
locations/file changes; it does not mutate the consumed map or code between
phases. Add those refusals and receipt disagreement/absence/staleness coverage.

### Group 2 — controller, cumulative clock and recovery: partly repaired

There is now a separate controller, operational reserves inside the cap, durable
live-time records, and per-session/per-try recovery consumed by `Budget`
(`enforce.py:149`). The saved synthetic results support approximately **3.01 s**
kill-to-reap for the tested SIGTERM-ignoring C and Metal workers. The crash-tail
fixture verifies the arithmetic of adding 60 s.

The controller can nevertheless die while a worker continues: workers start in
new sessions (`stage_a_controller.py:229`), check the parent only once
(`stage_a.py:435`), and have no subsequent parent-death supervision. `_load`
(`controller:95`) charges time but does not reconcile/terminate prior worker
identities before a replacement is spawned. The controller's lock alone does not
prevent an orphan from overlapping the next run.

Cleanup also stops at leader completion. `_kill_current` (`controller:206`)
returns if the leader has exited and skips SIGKILL after a leader exits on
SIGTERM. A surviving child need not be gone. The family fixture covers an
ignoring leader followed by group SIGKILL, not an exiting leader with a surviving
child. Establish whole-task termination before advancing/releasing ownership;
prevent escaping descendants or reconcile them by verified identities.

Crash admission is inconsistent: desk gates inspect `interrupted`, but not an
unreconciled `open_attempt` (`stage_a.py:403`). The next worker converts the latter
to interrupted and refuses without authority (`:444`); the controller then
terminalises that worker exit. Reconcile first and make an authorisation hold
distinct from an integrity failure. The report path also constructs this budget
and demands/consumes recovery authority despite `terminal_gate=False` (`:850`):
a resource-killed open attempt can prevent the promised STOPPED report. Reporting
must describe interrupted state without granting or consuming forward authority.

The full clock/heartbeat bound remains open as described in answer 3. Required
fixtures include controller death during active work, stale-worker reconciliation,
leader exit with surviving child, restart before interruption reconciliation,
and a STOPPED report with an unauthorised interrupted attempt.

### Group 3 — phase separation and whole-task memory: partly repaired

The lock and leader-exit ordering are enforced/tested; native follows instrumented
leader reap. Whole-task release also needs the orphan/descendant repairs above.
The memory probe is a substantial improvement over RSS alone, and the fixture
supports additive accounting for its tested 1 GiB host plus 2 GiB active MLX
allocation: 3.219 GiB physical footprint.

However, the controller samples only the current worker PID (`controller:241`;
`memprobe.py:42`), omitting itself and descendants, and performs no sampling during
its identity/gates or finalisation. Apple's published XNU implementation derives
the V4 lifetime footprint from that process's Mach task; the separate child
statistics are time/page-in counters, not summed footprint. Thus the docstring's
claim that children are included is unsupported. See
[Apple's implementation, gather_rusage_info](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_resource.c)
and [V4 structure](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/sys/resource.h).
This source check establishes scope; it does not measure this Mac's complete
allocation accounting.

`poll()` precedes sampling and can reap an exited worker (`controller:236`), so
a late peak immediately before exit can disappear from the task record. Capture
final usage before reap or use a qualified final-resource handshake; validate
nonzero lifetime peak at least as large as current footprint. The probe currently
checks only nonzero current footprint (`memprobe.py:45`).

The saved spike has **current footprint = lifetime peak = 5.222 GiB** and resident
3.082 GiB. It does not demonstrate peak retention after physical footprint has
actually fallen. Cache is zero in both saved runs: the disclosed cache-class
limitation remains real. Qualify controller/child scope, exit peaks and an actual
cache allocation, or enforce and verify a cache-disabled policy with a justified
measure. Keep actual model peak as a Stage A measurement.

### Group 4 — storage and finalisation: partly repaired

Removing the external hash cache, reserving three times each array write's size,
and the 64 MiB operational reserve are good changes (`enforce.py:132`). They do
not reserve every writer: state, phase completion, parity, report and controller/
final writes use atomic writers directly. Periodic storage scanning cannot prevent
an unreserved final write from exceeding the cap, including temporary overlap.

`finish_instrumented` checks size before DONE (`stage_a.py:678`); native checks
before parity/DONE (`:841`). `_close` captures time before scanning/persisting the
closed controller record and size before that write (`controller:164`). The final
JSON is written afterwards at `:195`, with no subsequent cap check. Consequently
the figures called final omit those last costs and bytes. Bound/reserve all
finalisation writers, include their elapsed/temporary/durable costs conservatively,
and publish an accurately scoped completion receipt. The report reserve must
remain available on every stop route without a cap reset.

The named reserve test tests one array reservation, not these final writers or
near-cap failure paths. Add cap-edge and failed/blocked final-write fixtures.

### Group 5 — independent validation: materially incomplete

The validator now rehashes committed outputs, checks residual shape/dtype/hash/
finiteness and requested logits, binds phase output maps, recomputes all 20 native
comparisons, and rejects the tested duplicate/falsely passing parity summaries.
Suffix-id and pixel-plus-feature sensitivity checks are also repairs.

It does not implement its claimed full schema (`stage_a_report.py:84`): record
kind/schema, ordinary expanded-input hashes and token counts, capture/readout and
edit/dispatch metadata, feature shape/dtype, rotary-call details, merge row count,
boundary bytes/hash/recomputed finiteness and native decoder-call checks are
missing. Some requisite capture metadata is discarded by `stage_a.py:639`.
Boundary FP32 bytes are available in the record but never decoded/validated.
Native merged-embedding equality at report `:120` trusts a boolean instead of
comparing `inputs_embeds_sha256` with the paired plain merge digest. New native
forwards do compare hashes (`stage_a.py:797`); reloaded native outputs skip that
live check, and the validator must cover them independently.

A static counterexample is a plain record with its `input_ids_sha256` changed or
removed, its JSON/output hashes updated consistently in state and phase manifest:
none of the validator predicates reads that field for an ordinary plain case.
Likewise changing the native embedding digest while leaving its equality boolean
true is not checked. These are source deductions, not executed mutations.

Validate planned id/index/case/kind, exact record/array schemas and required output
membership, the state identity/caps/status/tries/counter consistency, and unknown
or extra completed ids. Derive all checkable equalities from archived data rather
than booleans. Preserve sufficient metadata/bytes for the independent checks; if
full feature/logit hashes cannot be recomputed from the archive, say precisely
which bound live checks support them rather than claiming full recomputation.
Add consistently rehashed mutations for every newly enforced field, embedding
digest, boundary bytes, ledger inconsistencies and output membership. The nine
existing validator methods do not cover these omissions.

### Group 6 — completed report, final PASS and B admission: materially incomplete

The procedural B checklist correctly requires final PASS, inspected figures and
author interpretation, Codex report review, and the owner's row-21 go; the report
does not automatically admit B. Unique ids and tries are now separately labelled.

Final PASS still has a direct failure path. `build` writes a passing machine JSON
before the Markdown write (`stage_a_report.py:236`, `:249`). If the latter fails,
the report worker exits nonzero; the controller appends a report stop (`:156`)
but `_finalise` (`:181`) accepts that JSON without requiring successful current
report completion, complete artefacts, current session/package binding, or no
report stop. An old passing report can similarly survive a new report crash.
Invalidate prior PASS artefacts and require a fresh successful report receipt
with the actual committed output/figure identities. Every current report failure
must prevent PASS, even if an earlier JSON says true.

The final cap predicates cover only time/storage/memory (`controller:184`), not
attempt/aggregate counter integrity; the validator does not close that gap. A
consistently over-limit saved ledger can reach reporting without another
`attempt()` cap check. Final cap evidence must cover attempts and every applicable
aggregate limit as well as the correctly completed figures from groups 3–4.

Stage B prediction remains preliminary (`stage_a_report.py:211`); finalisation
does not recompute it from complete A time/bytes. Publish the completed prediction
and preserve the prospective row-21 CAL-slice qualification. The interpretation
flag currently tests existence only, although the declared prerequisite requires
author/date and the hashes of both inspected figures. Validate those identities
at actual B admission; no B executor approval is inferred from this review.

The fake controller report writes only a boolean; it cannot establish real report
completeness. Add real-report fixtures for failure after machine JSON, stale JSON,
missing/mismatched artefacts, over-limit ledger and final cap edges.

### Group 7 — headroom, source statements and audit: mostly repaired, later conditions

The **0.8 × cap / ×1.25** arithmetic is correct: B forecast ceilings are 11,520 s
and 6.4 GiB. Complete forecast accounting still needs group 6.
The removed-listing wording is correctly cautious: no conflicting claim observed,
upload date unknown; a first crawl does not establish a later upload. The five
verdict changes concern chili, hamburger, taxi, jacket and clothes, plus the general
stock note; the 49 records' statuses, sources, dates, authors, hashes and listing
metadata remain unchanged. Prefer "does not establish the upload date or a later
upload" to the note's broader "proves nothing" wording. Clothes
remains the seeded replacement for mask. This review checks the submitted records
and wording; it does not freshly clear rights or visit/open the photographs.

The audit now declares each photograph's blind name locked independently before
pair display, and has its own 32-concept construction map. Those are the requested
structural repairs. All 32 map entries have synsets and definitions, with 118 unique
aliases and no collisions within those 32. They are **before-audit/B conditions,
not new Stage A gates**.
The freeze's Panel still says 59/61 (`../audit_app/IMAGE_AUDIT_FREEZE.md:14`);
replace it with the current 61/63 rule before audit use. Apply the adopted uniform
specificity rule to the audit map as well as qualification, freeze documented
same-sense exceptions and any missing-synset rationale, and bind the actual audit
scorer to that map. A synset's source provenance alone does not prove that every
listed synonym distinguishes the intended concept: clothes admits dress/dresses,
hat admits lid/lids, and jeans admits denim/denims. Retain the separate sense
judgement and prospective referral rule for ambiguous naming. Taxi accepts taxies
but omits ordinary taxis; preserve validated ordinary inflections. The map's pool
hash alone does not bind metadata/WordNet/alias-builder inputs; record their
construction identities and hash the frozen map used by scoring. The plural-only builder
repair is assessed below. There is no audit execution approval here.

## 3. Declared tail/headroom limits: not acceptable as implemented bounds

A conservative engineering reserve need not be measured by causing an uncontrolled
power loss, nor must development-image performance be known before this
qualification experiment. But a declared assumption is not evidence that the
controller can enforce the stated hard cap.

The 60 s unseen-tail charge is not bounded by this implementation. Gates run
synchronously before the phase loop (`controller:135`), with fresh hashing/git
and no deadline/heartbeat watchdog while blocked. Filesystem traversal/fsync are
also unbounded. A persisted stale session is charged 60 s regardless of how long
its worker actually continued after controller death. The crash-tail fixture
checks addition, and the writer fixture injects a promptly raised exception;
neither establishes the maximum unseen interval.

The declared 0.25 s sampling interval is a sleep, not the complete observation
interval. The same loop runs two synchronous sysctl calls with 2 s timeouts,
storage traversal and fsync (`controller:255`). The sampler's 1 s limit is checked
only after return (`:248`); a hung call stalls termination. Thus the 4 GiB/0.25 s
growth premise does not describe the code. A lifetime peak reveals an overshoot
afterward, if collected, but does not itself prevent the cap breach.

Before go, qualify a control path whose deadline/kill mechanism cannot be blocked
by hashing, observation or persistence; demonstrate bounded detection-to-reap,
heartbeat-loss/orphan reconciliation, blocked sampler/writer behavior, complete
task-memory scope and final-peak collection. Then justify the 60 s charge and
memory-stop margin against that full interval, or use a conservatively enforced
alternative. Qualify nonzero cache coverage or an enforced cache-disabled policy.
Synthetic, non-development evidence suffices for these mechanisms. **Real Stage A
throughput, model peak and parity remain measurements to be made only after a
favourable exact-package review and owner go.** The present 60 s/4 GiB declarations
cannot serve as those mechanism qualifications.

## 4. Exact next closure set; moved AI-reader package

For reconsideration, commit a revised package that closes:

1. Strict agreed attestation schema; verified committed-source/identity
   relationship; digest-bound consumed import map; fresh phase/report identity
   equality or an enforced immutable snapshot, with the missing refusal fixtures.
2. Controller-death/descendant cleanup and orphan reconciliation; genuinely bounded
   heartbeat/deadline supervision; crash-state reconciliation before spawning;
   distinct recovery hold; read-only interrupted-state STOPPED reporting.
3. Qualified whole-task physical memory through gates, load, execution, exit and
   finalisation; final peak capture; complete observation interval and justified
   stop margin; nonzero cache coverage or enforced policy.
4. Reservations/accounting for every writer, temporary overlap and closure;
   bounded STOPPED finalisation; honest completed costs and cap-edge evidence.
5. Complete independent record/array/ledger/phase schemas and all omitted identity,
   boundary, dispatch and invocation predicates; equality from archived hashes/
   arrays; sufficient archived evidence and corresponding mutation fixtures.
6. Fresh successful report receipt and artefact binding as a prerequisite for
   final PASS; no stale/partial report acceptance; complete final cap/counter
   checks and completed B prediction; validated interpretation at B admission.
7. Accurate mechanism claims in criteria/readiness, the existing source wording
   retained, and the separate pre-audit conditions stated accurately. Do not turn
   the unqualified reader or unfinished audit into a Stage A requirement.

Keep the confirmed input construction, cases, positional rule, transaction,
numeric statistic, carry and envelope. Repair evidence prospectively; do not
spend the spare six on failed gates or reinterpret test success as a go.

The moved reader package at `a59fc2d` remains **NOT ON BOARD for qualification
calls** under the closures in the completed `2026-10-02_ai_reader_rev2_codex_record.md`
(RSC `7048bb855d6c145a95e6ed67927703a2658d0a23`). This is the requested bounded
delta assessment, not a repeated independent qualification review or completion
report. The exact moved files reproduce the brief's hashes:

| Reader file | SHA-256 |
|---|---|
| ai_reader_qual_set.json | `73815ecddb2ea0f54877b5ad3b50aed421ceece46383f59156711534ffdb1b70` |
| ai_reader_qual_key.json | `65aa70aadd67c44eab2fa4a02637f978dafaa9611931ce38f01ee1f0f9af2198` |
| ai_reader_exec.py | `c0f5ecf42a706304c7f3a70cb2e078965be10580e2d0a6dcba3366d5ee143e8a` |
| ai_reader_key.py | `2d21121c75c307c6f6c64b3e253c1caa0f2de06f9a4842b9cd790b5dd2097bcf` |

Exactly eight aliases were removed and none added: `boxer shortses`, `boxerses`,
`boxershortses`, `drawerses`, `shortses`, `underdrawerses`, `pair of scissorses`,
`scissorses`. Only the two affected items' aliases/plural metadata change
semantically; other plural-map ordering changes are serialization only. The 300
items, 63 easy, human fields, reservations, image hashes and delivery order stay
fixed; the set changes only key/key-builder identity fields. This closes the
specific bogus-alias defect in this frozen key. The builder's suffix heuristic
(`ai_reader_key.py:67`) is not a grammatical plural-only test: qualify it for
singular nouns ending in s as well, preserving valid inflections.

The reader executor now calls the attested guard with `aireader/qualification`
(`ai_reader_exec.py:136`), but omits reviewed-commit re-derivation and still excludes
the imported guard/enforcement from `BOUND_FILES`. The previous first-answer
journal, recovery, effective isolation/event classification before retry, silent
truncation, hard-clock/output/reaping and full raw-evidence/scoring-provenance
closures remain. The specificity collisions are not removed by the eight-alias
change. The private-qualification source exception and counted first ordinary
request smoke rule stand as recorded at `7048bb8`; no reader request is authorised
by agreeing the Stage A attestation syntax.

Validation of this review was static source tracing and deterministic git-blob
JSON/hash arithmetic. The submitted claims of 23 runner, 10 controller and 12
reader tests passing are reported evidence, not tests executed by this reviewer.
Claude R052 retains design/framework/ledger and dispatch; R084 retains code and
execution. Only this review and the Codex work-item log are owned here.

# AI image-reader qualification, revision 3 — Codex design and job review

2 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`, native session
`01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with reader calls under RSC
`8dee1732ce80c13cd12d0d0c609a182e7a9e41af`.** The revision makes substantial repairs,
but does not yet enforce the claimed input boundary, restart holds, complete evidence
admission and all resource limits. This record contains no favourable attestation and
cannot supply the review gate for `AIREADER_GO.json`.

I am the proposed reader's developer/model family, Codex/GPT. This is design advice,
not independent reader qualification. Construction labels, aliases and definitions
were visible during review; this conversation and its review helpers cannot serve
as blind reader contexts. No qualification image was opened or named, no model was
called, and no submitted module, test, fixture or job was executed. Three helpers
examined separate static code paths. Independent standard-library text/JSON/hash
arithmetic checked identities and construction counts only. No old private audit
outputs, plant keys, human answers, captures, simulations or account operations
were accessed. Source implementation, framework and ledger were not edited.

The instruction was Unimog
`prompts/2026-10-02_codex_r052_ai_reader_review_rev3.txt`, committed at
`5f14b3d82cfb9165b394d71667ea60b4cb793dc8`, SHA256
`31253cc28d0c02c6129d2b97f0c892c0c7b6d1efb36e6cda0fc26de17c0e7af1`.
Ownership was committed at Unimog `b1bade8c`, then handoff
`ca6f4df4-91c4-5667-96d2-ecb0181b9196` acknowledged and verified accepted before
review edits. R052 retains protocol, source decisions, frontmatter and dispatch;
R084 retains implementation and execution.

The system being reviewed is a separate orchestrator holding the frozen key and
human difficulty reference, delivering 600 single-image requests in fresh sessions,
with at most 660 attempts, three tries per request, nominal 120-second attempts,
six hours across sessions and raw output below 20 MiB. One retained outcome per
request is required. The primary admission gate is whole-answer naming on the 63
easy grayscale items, at least 61 correct; colour and paired results are descriptive.
The first ordinary request is the counted technical smoke. Qualification does not
clear study-image rights or the other three image-audit judgments. These adopted
choices stand, per framework §8.2 and the bounded job brief.

## 1. Exact identity and the six answers

All 14 bound text blobs match the submitted commit and working tree. Local binary
realpath/hash and sandbox-exec hash match the brief. Independently reconstructing
the command template from the source's literal flags and using the saved CLI
version reproduces all 21 fields and the supplied digest. The version and effective
CLI findings below are source measurements, not new CLI executions by this review.
Hash agreement identifies the package; it is not evidence that its guarantees hold.

| Field | Value |
|---|---|
| ai_reader_qual_set.json_sha256 | `22dd919e7e317895431a62b29b87ac2e4302795b7b277140568467242e25aa05` |
| ai_reader_qual_key.json_sha256 | `f68c71f7d3a8372d00c99f7627f5c243fd0e93b6a742a9e2b8960b01bbb79ce3` |
| ai_reader_delivery.json_sha256 | `8d6bf669488a3f2adc3e6c8574a7df9af100da903c5cf826e243d82e5d908847` |
| ai_reader_exec.py_sha256 | `0cf37baaae91cc3b4171afe69fe139dc319e76dc005cd4d7337912be023bf8fb` |
| ai_reader_score.py_sha256 | `66b3c258e0a5e4674253b40caca28f638591ab436eefef09a3840f4e557f53bd` |
| ai_reader_runtime.py_sha256 | `1dd7ae091e4f3fe1049f146f9b719b308df33f8429860a74df9d35dac236de1b` |
| ai_reader_journal.py_sha256 | `9cf3346747bd0d2a2b15c3b6c36c5adfb3599efd709d8a0acab1a983e612460c` |
| ai_reader_key.py_sha256 | `328a8617b447d8374288056f3db43e4a3565fd92802acf59deb8d37a66a5cf90` |
| ai_reader_frame.py_sha256 | `3ec7f42ee3bf59bd289e5053783010fc39bfd274c8dde61df6e7266eab2c1e12` |
| ai_reader_qual.py_sha256 | `8d570ab4f7b5ec59ad18b42c3cbddac13e0bd4984d8c45a5879b557833df0ae2` |
| AI_READER_JOB.md_sha256 | `6c0dc153b2ad384abff484fb567237a3a308735916675ee08da9f15838b05da3` |
| AI_READER_DESIGN.md_sha256 | `7241ef99f78ab91aaa2fad32a2724458d398c76deb5435499f4b20c26382bb61` |
| stage_a_guard.py_sha256 | `8c916465fb6256a22371e599b148c4e6ece30c30ac0f501c254b4dc950e9f68c` |
| enforce.py_sha256 | `150cc0c63f4551acaa5f5ffb4f355b91dc61d796f47dbbec1f4c917ae00b1381` |
| codex_realpath | `/opt/homebrew/Caskroom/codex/0.159.3/bin/codex` |
| codex_sha256 | `4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878` |
| cli_version | `codex-cli 0.159.3` |
| sandbox_exec_sha256 | `58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8` |
| command_template_sha256 | `a817ced2316ec0b6be0ff96cb3d02ace8f3164184738b36746666c5d9c27107f` |
| instructions_sha256 | `e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790` |
| package_digest | `dab5c78f5873ff02907366b28306da5542745f1689b74176e6fd3e69eb001624` |

1. **Closures 1–7: partially repaired, not all closed.** The mechanism/test map in
   §2 identifies what each named fixture supports; §§3–6 give the remaining paths.
2. **S4: keep prospectively**, with the frozen equivalence exceptions and the
   interpretation in §3. The collision counts use different denominators, resolved
   there. No response-driven key change is permitted.
3. **Undisableable `unified_exec`: the submitted containment is insufficient.**
   Hold this job. A CLI version that disables it is one possible repair, but is not
   the only acceptable design: an actually enforced, tested input boundary can
   satisfy the rule. Home denial plus detection after execution does not do so (§4).
4. **Yes, require a retained-output suite rerun before go**, on the exact replacement
   package and recorded environments, including WordNet-dependent checks. R084
   should retain stdout/stderr, command, exit status, counts/skips and identity;
   diagnose any recurrent error. Three reported clean runs do not explain the
   fourth's lost single-error output. This review ran none of them. A clean rerun
   is necessary evidence, not a substitute for the missing mechanisms/fixtures.
5. **Review now and re-attest a later exact delta is acceptable sequencing.** There
   is no need to wait to give this design review. There is no favourable attestation
   now. After row-20 revision 4, recompute the complete reader package and review the
   actual guard/enforce behavior plus affected fixtures before any go. Two changed
   fields and a new digest do not make the behavioral delta automatically approved;
   the repairs listed here will also move reader fields. Do not reuse an attestation
   for a prior digest or omit the newly bound imports.
6. **Not favourable; no approvable block.** The exact replacement closure list is
   §7. The machine-readable attestation convention remains agreed in principle;
   favourable syntax is not provided for this negative record.

## 2. What the code and named fixtures establish

Line references below are to the submitted photo-directory files at `8dee173`.
Fixture statements describe inspected assertions and source-reported runs, not
independent execution here.

| Closure | Substantial repair and relevant evidence | Remaining limit |
|---|---|---|
| 1: identity | `BOUND_FILES`, `package`, `package_at_commit` include imported guard/writer and runtime fields. `Approval` tests unrelated approval, dependency mutation, reviewed-commit re-derivation, mixed digest and receipt refusal. `ScorerAdmission` checks git tracking/dirty bytes, key hash and referral fields. | Guard schema remains permissive; scientific scorer accepts injected key/set/package; runtime/evidence checks remain incomplete (§§4,6). |
| 2: reference/key | `check_sources`, `check_frame_invariant` and WordNet pin are present. `FrameInvariant` tests the known mismatch, equal-ratio swap, duplicate/count/finite-proportion/source mutations. `KeyIntegrity` and `KeyFunctions` test plural-only repairs, residue, specificity, pins and rebuild equality. | Counts/prose need the corrections in §3; tests do not prove every grammatical or sense judgment. No further redraw is supported. |
| 3: first outcomes/recovery | Fsynced begin/dispatched/end journal replaces divergent attempt state. Durable answers are not replayed; uncertain dispatched attempts become final INTERRUPTED. Eleven `HardKill` fixtures exercise real subprocess crash windows, partial tail and recovery persistence. | Stop/smoke state is not enforced on restart; orphan/descendant lifetime is incomplete (§5). These fixtures mostly kill attempt 2, after the smoke. |
| 4: boundary | Five-variable environment, home read denial, instruction/image rendering pin, raw bounded events/stderr, isolation before retry, answers retained despite exit failure, explicit overlength. `Boundary` and `Executor` test their selected branches and a real-binary local home-denial probe. | Home-only denial allows other inputs; actual-exec equivalence/user text/effective capabilities and full lifecycle consistency are not proved (§4). |
| 5: limits | Third-try final precedes aggregate cap; remaining-time reserve, worker timeout, raw append cap, process-lifetime flock and receipts added. `Executor` tests cap order, pre-attempt reserve, a TERM-ignoring worker, stdout flood and raw preflight. | Setup/finalization/recovery lack hard deadlines; crash accounting, normal-exit descendant cleanup, directory/exception stop paths incomplete (§5). |
| 6: admission | `validate` enforces many types, order, unique attempt ids, 660/3, retained status, no-response after three failures, counters and COMPLETE. Sixteen mutations and format-before-match fixtures are meaningful. | It trusts labels and shallow receipt/evidence fields; resumed execution bypasses validation; scientific overrides bypass frozen scoring (§6). |
| 7: source statements | Job and builder state restricted private use, collective-release caveat, unverified per-image provenance, 600/up-to-660 transmissions and no formal-reuse clearance. | Retain those decisions. Amend claims of full containment, 34 effectively disabled features, every-stop receipts and completed closures to match implementation and this verdict. |

The source reports 97 suite tests, 64 reader tests including eleven hard-kill cases;
four WordNet checks skipped in the image environment and four passed in the build
environment. Those reported runs do not cover the omitted paths below. The single
unexplained error and lost output remain disclosed.

## 3. Key construction, S4 and the count discrepancy

The submitted construction remains 300 items, 63 easy, 600 requests covering all
pairs, a complete frozen order with no adjacent paired views, and 33 phrase-only
targets. Every saved delivery digest equals its request's image digest; this is
metadata agreement, not this review's inspection of 600 image bytes or actual
transmission. Key hash equals the set's key hash. The eight invalid plural aliases
are gone, `pairs of scissors` is present, and the Python-literal synonym residue
is repaired. Ten no-synset concepts carry source/rationale fields. Source tables,
norm description and WordNet corpus are pinned. Keep the verified frame/draw.

**Keep S4 as a frozen conservative lexical admissibility rule.** It makes bare
aliases less permissive before answers, with 13 written equivalence exceptions;
it does not establish picture-context meaning empirically. Its actual predicate
is **first-listed WordNet noun sense differs from the recorded target synset**
(`ai_reader_key.py` lines176–204), not measured dominant usage among these images
or readers. Document that distinction. The exclusions overlap: 64 bases/126 forms,
52 targets/14 easy, with S1/S2/S3/S4 counts 23/4/5/60. Only `bun`/`buns` remain
shared between selected targets. Four targets lose their sole one-word candidate;
the noun-phrase contract accommodates the resulting 33, without changing admission
membership. Exceptions are pre-answer design decisions, not later owner credit.

The earlier **24 collision forms /23 targets /6 easy** count is reproducible from
the revision-2 key against released canonical Word/id names. It includes **`hook`**,
which is the selected target `hook2`'s own THINGS Word and therefore stands under
the adopted canonical-name priority. Removing that canonical case gives **23/22/5**,
the noncanonical population counted by R084. Both counts are correct for their
stated populations. The new key preserves `hook` and the documented `roll`/`bun`
equivalence: **22 of the old 24 forms are removed across 21 targets, five easy**.
The new S1 base count 23 also includes `drawers`, matching an inflection of another
released canonical name, which the earlier literal-name comparison did not count.
Do not claim that all old 24 except `bun` were excluded, or compare new excluded
bases with old admitted forms as though the denominators were identical.

The suffix audit is bounded to this candidate set; it is not a general grammatical
validator. Its list includes Latin binomial parts such as `latrans`, so describing
all 13 heuristic “plural-only” heads as English plural nouns overstates the audit.
Keep the explicit tested inflection policy and describe what was actually checked.
These construction judgments are not answers to any qualification image.

Two small integrity/prose corrections also belong in the replacement. The reusable
frame invariant compares retained exact recognizability/counts but not retained
`close`; ratio/close consistency is checked earlier by the builder. Add those direct
comparisons and a retained-close mutation fixture without redrawing the passing
data. The key module's opening claim that no-synset candidates come from Word/id
alone disagrees with five additional synonym bases across three such concepts;
their per-item rationale correctly includes listed synonyms. S3/S4 cannot operate
without a recorded synset. Finally, specificity tests should assert full-form
collisions prospectively: generated inflections inherit a base decision. The current
full-form S1 check finds only declared `bun/buns` and `hook/hooks` exceptions.

## 4. Input boundary and receipt consistency

**Home denial is real protection, but not an image-only read boundary.** Runtime
lines91–97 start with `allow default` and deny reads only below the original home,
apart from auth. Files outside that subtree, including sibling attempt directories
and copied construction data under `/tmp`, remain permitted by this profile. The
reader's working directory being empty does not deny other readable paths. The
submitted real-binary fixture tests only the home key and home listing. Event
classification detects a command after it happened; it cannot prevent a forbidden
input already being read or influencing a response. This finding does not allege
an observed leak: no reader call was made. Establish a tested allowlist or equivalent
boundary for the actual process and its descendants, with the necessary runtime
and authentication exceptions, and deny key/norms/paired answers wherever they
can reside. This does not require a particular VM or a gratuitous new CLI version.
Official [OpenAI permissions documentation](https://learn.chatgpt.com/docs/permissions)
distinguishes explicit read denials from broader workspace/network permissions.

The saved receipt and source list **34 requested feature disables, 33 effective
false, one `unified_exec=true`**. Correct “34 disabled and checked effective.”
`effective_features` and `auth_route` run in `plan`/`delivery`, not scientific `run`
before dispatch. The stored measurement is pinned, but run does not establish that
the effective state still equals it. The instruction hash alone
does not prove tools unavailable. Use an equivalent fresh no-request capability/
auth receipt where required by the frozen boundary, without recording credentials.

`prompt_input` uses `debug prompt-input` with `flags`, while actual execution adds
ephemeral, ignore-config/rules, read-only and other exec options (runtime125–154).
The source must demonstrate that the receipt represents that exact invocation,
or record the remaining mismatch honestly and hold if equivalence is unestablished.
Executor439–446 compares instructions and embedded image only. It records but
does not compare per-request `user_text_sha256`; unexpected added user text can
pass those checks. The frozen receipt contains 600 distinct user-text hashes because
opaque image paths differ. Compare the appropriate per-request normalized text
hash, not one global value, and check the remaining declared delivery fields.

`lifecycle_complete` (runtime256–259) checks first/last types and membership, not
ordered unique turn/item lifecycle or last-message agreement. A completed event
message and a different `-o` answer can be labelled `ok`; duplicated or contradictory
terminal events can pass. `classify` chooses the file over event text without a
consistency check. The official [non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
describes JSONL events and the last-message file as outputs of the same invocation;
their agreement must be validated. Add mutation fixtures for ordering, conflicting
answers, multiple terminal messages and malformed bookkeeping payloads. Keep the
repair that any received answer or isolation outcome is final despite exit failure.

## 5. Recovery, smoke and resource enforcement

**First outcomes are substantially safer; holds are not durable in effect.** An
`end` is durable before the loop calls `smoke`/writes STOPPED (exec410–415,485).
A crash there after a first no-image or isolation answer leaves that request final.
Restart reconstructs it and skips the first request (385–387), without reconstructing
the required smoke hold. A structural-failure end sets `st.structural` in journal
`apply`145–147, but `Job.run`/`loop` never checks it before another dispatch. Scoring
validation may eventually reject the new journal; it does not prevent the forbidden
retry/calls. A first-request provider failure followed by a no-image answer on try 2
also bypasses `smoke`, which runs only at global attempt 1. Derive and enforce stop/
smoke status from durable records before every resumed call and throughout the
first request. A recovered uncertain smoke cannot silently count as a passed smoke.
Test attempt 1 crash windows and first-request retry outcomes, not only attempt 2.

**Worker cleanup remains incomplete.** Timeout/overflow `kill_group` includes a
useful final group kill. On ordinary leader exit, however, the polling loop ends
and `self.proc` is discarded without group cleanup (exec461–477). Exception cleanup
only runs when the leader is still live. Recovery's `kill_orphan` checks the leader
PID's command for `adir` (193–208); if that leader has exited but children remain,
it returns false without resolving the group. The external-SIGKILL fixture itself
shows a worker surviving controller death until restart; it does not demonstrate
an independent attempt deadline during that gap. Ensure exact surviving groups
cannot outlive the declared attempt/job bound, including leader-first exit, parent
hard kill and recovery, and prove cleanup before later dispatch. Do not kill an
unidentified unrelated process to obtain this guarantee.

**Charging time is not enforcing every deadline.** `t0` starts before package/go,
but Clock's first durable session is created later (exec292–315,332–336). A crash
in startup has no current durable time; a 60-second receipt phase with no heartbeat
can lose more than the 30-second tail. Receipt work occurs before the worker's
timer starts; the remaining-time budget is not refreshed immediately before GO.
Hashing, git checks, local receipt subprocess capture, journal scan/recovery, fsync
and stop/final writes are outside an independently enforced deadline. Define the
existing active-session/downtime semantics clearly, durably charge every phase and
bound setup, worker, cleanup and finalization within the same allowance. No increase
to 660/3/120s/6h follows. The existing clock fixture only tests a pre-attempt refusal.
Clock continuity also needs checking: a missing `clock.json` initializes zero even
when the journal survives. Refuse lost/inconsistent accumulated accounting instead
of silently resetting it. Receipt time is sampled before its own and Clock's final
fsyncs, so finalization must be charged or included in an explicit enforced bound.

**Not every stop yields its promised receipt.** Receipt renderer SystemExit/timeout,
launch/pipe exceptions, malformed resumed state and `RawCap` escape the `Stop`
handler. Startup approval refusal can remain a no-dispatch hold; failures after
job entry need a bounded durable stop/recovery record. A stop during an open attempt
also needs reconciliation before any receipt, rather than claiming completion.
`dir_bytes` is checked only while the leader lives; there is no final directory-size
check for a worker that exits before polling. Failed receipt setup can leave attempt
directories behind, and per-directory caps do not bound cumulative abandoned output.
Local receipt commands capture output without these worker caps. Tail quarantine
is written before journal truncation without fsync of the quarantine file/directory
(`repair_tail`114–127). Reserve and enforce all required writes, preserve damaged
tail evidence durably, and add exception, quick-exit overflow and cleanup fixtures.
A crash after tail truncation but before `tail_repair` is appended also loses the
repair event; make pending quarantine recovery idempotent. Capped recovery evidence
describes a captured prefix, so label it as partial rather than claiming its length/
hash cover an entire unbounded orphan output. If persistence itself fails, leave a
truthful hold/recovery condition; do not promise an impossible successful receipt.

## 6. Complete evidence admission and frozen scoring

The validator's positive repairs in §2 stand. Its remaining checks are too shallow
to justify “complete raw-evidence validation.” Begin receipt hashes need only be
strings (journal243–245), not equal the package's instruction pin and the request's
delivery receipt. `_bounded_ok`169–174 does not check a complete text's length/hash
against its bytes or require valid digest syntax. For provider/structural failures,
end records need no events/stderr evidence; for `ok` it checks the answer's own
length/hash and bounded evidence shape, but not lifecycle, event/answer agreement
or classification. Thus self-consistent edited answer fields or a mislabeled failure
can survive those checks. Numeric checks accept nonfinite or out-of-range durations;
the receipt's clock/limits and raw-size cap are not validated. A committed raw file
locks bytes; it does not supply the omitted semantic checks. Validate frozen receipt
identities, all outcome evidence, sufficient complete evidence for classification,
nonfinite/range/cap rules and required smoke/stop status. Add targeted mutations.

`Job.run` reconstructs without calling this validator in incomplete-journal mode;
digest/mode alone do not verify sequence, status or legal transitions before another
request is sent. Validate and reconcile admissible incomplete state before dispatch,
including terminal outcomes, rather than deferring refusal to scoring.

**Scientific scoring accepts unbound replacements.** `score`179–189 accepts caller
`key`/`sset` dictionaries while checking and reporting hashes of on-disk key/set;
`admit`163 accepts a caller `package` instead of recomputing it. In scientific mode
those overrides can alter aliases or easy membership while identities still name
the frozen files. The CLI default does not expose those arguments, but this public
entry point does, and the tests use it. Refuse such overrides outside explicitly
labelled synthetic mode, or verify equality to independently loaded/recomputed
approved objects. Add a scientific-mode changed-alias/easy-set/package refusal
fixture. Keep synthetic output's explicit non-qualification label and null admission.

**The shared guard still does not implement exactly 21 fields.** Its union/get
comparison permits an extra null package key in both attestation/go when absent
from the recomputed package (guard297–300). It checks commit-string length, not
40 hexadecimal characters/resolved exact identity, allows truthy nonstring reviewer/
owner fields, truncates dates to 10 characters, and does not require a closing
attestation delimiter. These are the unchanged shared-guard issues already routed
for row-20 revision 4, not a demand for a new attestation format or owner-identity
cryptography. Require exact schemas/types/key sets, closed block, resolved full
commit ids and valid ordered dates; retain reviewed-blob re-derivation and the
negative-record refusal. Bind/review the repaired shared implementation here too.

## 7. Exact closures before reconsideration

1. **Approval and scoring identity:** repair the shared guard's exact schema/commit
   checks; reject scientific key/set/package overrides; bind all accepted objects
   and executed/referral receipts to the same recomputed package. Review the actual
   row-20 shared-file delta and every additional reader change before any go.
2. **Reference/key:** keep the frame, membership, gate, plural/residue repairs and
   prospective S4 with frozen exceptions. Correct collision populations, first-listed
   sense wording and suffix-audit scope; add focused fixtures where claims exceed
   existing assertions. No new draw or response-driven alias additions.
3. **Durable recovery and holds:** validate incomplete state, reconstruct smoke and
   structural holds before dispatch, cover first-request retries and attempt 1 crash
   windows, and prevent exact orphan/descendant work from surviving declared bounds.
4. **Actual input boundary:** enforce access to the approved image/runtime inputs,
   demonstrate the actual exec/receipt equivalence, compare frozen user text and
   delivery fields, check effective state and validate complete consistent lifecycle
   evidence. 33 off plus undisableable unified_exec is disclosed, not containment.
5. **Hard limits and stop evidence:** durable accounting and enforced deadlines for
   startup/receipt/recovery/worker/cleanup/final writes, bounded local capture and
   final/cumulative temporary output, safe exception STOPPED/recovery records and
   durable quarantine. Exercise the missing paths without model calls.
6. **Evidence admission:** validate every outcome's required evidence, receipt pins,
   classifications/answers, valid clocks/caps/smoke/completion, and scientific override
   refusal. Test contradictory evidence, missing failure evidence, wrong hashes,
   malformed/nonfinite limits and illegal resumed transitions.
7. **Owning claims and evidence:** R052 updates framework/work status and R084 the
   job/design map to these implemented limits; retain restricted private scope and
   qualification/audit separation. Submit one exact replacement with retained-output
   mechanism/suite results, including the WordNet checks and disclosed prior error.

These are pre-call engineering closures, not a demand for successful qualification
before qualification begins. The owner's AI-reader choice and private-use exception
stand. The existing row-20 hold at `081f17b`, row-19 gates and all earlier completed
reviews/reports stand separately. No reader call, target-model forward, extra panel,
cloud run, budget extension or later 400-turn audit is approved by this record.

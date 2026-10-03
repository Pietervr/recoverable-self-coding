# AI reader revision 13 — exact-package Codex review

Review date: 3 October 2026, Phoenix and UTC. Reviewer: exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: `57cfb0ae8821a356e885de6ddeffad91b178c9c6`.
Assignment: Unimog `prompts/2026-10-03_codex_r052_reader_rev13_review.txt`
at `1e2bcd495cae0cf168519f001c38641e5e9de622`, SHA256
`5f98e9cd576f8c2098f9aec904c636e0f1d2943940f1a951dfb16ba3b8426ac3`.
Ownership committed at Unimog `9f4a1573`; handoff
`8faefde5-060b-5b2a-8222-2fd00c370e62` accepted before review edits or peers.

**NOT FAVOURABLE to this exact reader package. Two new capacity-path defects
require repair before reconsideration.** No favourable attestation is emitted.
The owner's 3 October conditional go, “go on reader revision 13 if Codex is
favourable,” remains recorded; its favourable-review condition is unsatisfied.
This review grants no archive execution, job (c), model request, qualification
admission, audit release or Stage A outcome. Source retains go binding and dispatch.

The system remains a 300-item colour/grayscale free-naming qualification with
600 requests, the unchanged matching rule and a 63-item easy-gray admission
panel. Revision 13 moves the client to an owned copy of CLI 0.160.0, adds its
tree pin and update controls, and exempts one no-answer capacity refusal from
the isolation classification. It proposes fresh answers and clock state on an
already exposed panel. The favourable reader-12 record `09bbe0e` stays closed;
this review addresses the new reader delta, not Stage A revisions 13–15.

## 1. The capacity exception drops the exempt error's item checks — blocking

`ai_reader_runtime.py:522–531` collects matching top-level capacity errors, then
removes each **entire event** before calling `isolation_problems`. The earlier
check bars agent-message items, but does not bar other items on those errors.
The original isolation checker (`546–560`) checks an `item` on every event,
including a top-level error. That check disappears for a collected error.

For a static counterexample, keep the source's `CAPACITY_EVENTS` fixture and
add this item to its matching capacity error:

```json
{"type":"error","message":"Selected model is at capacity. Please try a different model.","item":{"id":"c","type":"command_execution","command":"ls"}}
```

The matching `turn.failed` remains; there is no agent message or answer. With
absent/blank `-o`, ordinary stderr, a short parseable stream and no overflow,
the helper removes this error object and returns true. `classify:645–648`
therefore returns non-retained `provider_failure`, before checking the original
stream. The original checker would also report `item:command_execution`.
`ai_reader_journal._rederive:339–341` uses the same helper to waive the original
isolation finding, so journal re-derivation does not close this bypass. A
malformed or another disallowed item attached to that error has the same gap.

This is a source-derived counterexample, not observed output from the owned
CLI and not evidence that a command ran. It violates the declared fail-closed
rule for unexpected but parseable evidence: nothing else that isolation flags
may become a retryable refusal. The kernel allowlist remains separate protection.

**Required:** waive only the matching capacity-error marker; preserve all item
checks on the original stream. Rejecting any non-null item on an exempt error
is one narrow repair. Add no-request negatives with command/tool and malformed
items **inside the matching error**, and verify that classification remains a
retained final isolation outcome and that the journal rejects a forged retry
label. The current negative (`tests/test_ai_reader.py:1591–1606`) puts its
command on a separate event and misses this case. Ordinary no-answer capacity
refusals must still retry under the unchanged limits.

## 2. Capacity plus structural stderr creates a non-admissible retry — blocking

The new `classify:645–648` branch precedes the structural-stderr check at
`669–671` and does not test it. Keep the exact source capacity fixture, with
no answer and no overflow, and supply stderr `operation not permitted`.
The frozen `STRUCTURAL` pattern matches, yet classification returns
`provider_failure`, non-retained.

`ai_reader_journal._rederive:354–357` unconditionally requires
`structural_failure` when that same retained stderr matches `STRUCTURAL`.
It rejects the record just produced by classification as a provider failure
that disagrees with the structural pattern. This is a second static
counterexample; no real provider or sandbox failure was induced here.

`ai_reader_exec.Job.rec:668–673` appends and applies the end without immediately
re-deriving it. `loop:969–1000` can retry/continue on this non-retained label;
the structural hold is derived from labelled state. A later restart
(`852–853`) or scientific admission refuses the journal. Revision 12 kept the
undeclared capacity error as final isolation, so it had no such retry mismatch.

**Required:** give runtime classification and journal re-derivation the same
precedence on this contradictory evidence, preserve the declared structural
hold, and forbid a retry past it. Add a no-request capacity-plus-structural
stderr fixture that checks their agreement and the durable hold before further
dispatch, alongside the ordinary capacity control. Do not make the journal
ignore structural evidence merely to admit the current retry label.

Both repairs change bound source hashes. Commit and submit a revised exact
package with fresh retained evidence; this record supplies no reusable positive
attestation for its successor.

## What checks out, and the evidence's limits

All **25 package fields** reproduce independently from immutable blobs, source
AST literals and byte metadata. Digest:
`9c851cac38b401c63c4aad8420fce0e2944450344884596647168c464683fe64`.
All 16 bound live files match the candidate. The command template was
reconstructed without executing submitted functions. CLI version is the frozen
source label corroborated by the retained suite's local version receipt and
matching binary/manifest bytes, not a new reviewer CLI probe.

The expressly permitted owned CLI tree has 52 entries, 42 regular files,
no symlink, 332,968,547 bytes, and no write bits on entries, root or parent.
Its byte/path hash matches
`ced09ec2c51c8fd4ae4ccb7e0ccb6b6e76d32633ec842f08be000c2a55ba86fe`.
The allowlist names this executable and its manifest; the copied auxiliary
programs have no execution allowance. `CONFIG` pins the update check off;
the three added feature disables are in the changed command-template identity.
Tree hashing does not bind modes, ownership, xattrs or empty directories.
Read-only metadata is a verification observation, not universal immutability.

Set metadata differs from reader 12 only in the declared reader text and
qualifier code hash. The 600 request/image records, order, prompt, strata,
membership and instructions remain unchanged. Independent metadata comparison
also confirms every per-request delivered image/input field unchanged; no image
was opened. Key, scorer, matching code, frame and all four shared guard/runtime
files are byte-identical to reader 12. Key content was not inspected.

Retained suite `6bdb207bf0696a0c805ad959ee49a2a6216c8244` names candidate HEAD
and a clean photo directory; its twelve retained sizes/hashes match. Main:
312 collected, 291 passes and 21 skips. Build: 27 passes, restoring 16 WordNet
skips and repeating 11 main passes. Thus **307 distinct cases exercised, 318
passing executions**, no failure/error; five old Stage A transition cases were
not rerun. Boundary 11/11 mixes real-client local receipts and parser controls;
all six new Rev13Reader cases passed in the implementer's retained evidence.
Those six omit findings 1 and 2. Passing them does not settle the two defects.

Measured receipts report 35 requested disables, 34 effectively false and
`unified_exec` still true; the allowlist and fail-closed evidence checks remain
necessary. Neither updater traffic with provider network open nor the full
cross-version client request construction is observed. The 152-versus-150
feature counts do not identify the two additions without the old full list.
Only the new listing's hash is retained; source's proposed full-list retention
under reviews is useful evidence outside the package, not a new pin or a third
blocking finding. Other enabled features were not comprehensively audited.
The model label/effort are the offered client settings, not a guarantee about
the provider's serving implementation. These limits are already disclosed.

The valid capacity exemption is otherwise content-independent: exact frozen
message on at least one error and every failed turn, no agent item/event answer,
blank/absent answer file, no malformed line or overflow. The limits remain three
tries per request, 660 attempts and six hours. `archive_job_b.py` is outside the
package; its source checks the stopped job's hashes/receipt, closure marker,
absent destination and no running reader, then moves files and retains a
manifest. It neither scores nor merges answers; it was not run here.

`AI_READER_JOB.md`'s generic error sentence still names only the older two
notice exceptions; read it with the revision-13 table's declared capacity
exception. Bound declarations should be made consistent in the revised package.
Older no-model sentences within historical revisions are qualified by the
current exposure statement, as in `09bbe0e`.

## Exposure, ownership and execution scope

Job (a): 600 revision-11 answers, NOT ADMITTED; its later descriptive rescore
does not admit it. Job (b): 219 revision-12 requests, 218 answers and one
capacity refusal, stopped after removal of the pinned cask binary; unscored,
closed and never reused. Proposed (c) asks all 600 anew: third pass across these
a/b/c jobs on the same exposed panel, evidence for a prospective rule on a
reused panel, **never blind calibration**. The earlier 175-attempt stopped job,
full-bank R2's target-visible/concept-batched limit and prior exposure disclosures
also remain; 600+219 does not exhaust the history. Matching-rule residuals and
the mechanical-versus-owner-adjudicated admission distinction of `09bbe0e`
carry unchanged. No adjudication or qualification result is accepted here.

Read/reason only: relevant declarations/source/fixture text, public job-(b)
summary, retained suite evidence, stdlib git/blob/AST/JSON/hash checks, the
explicitly named owned CLI tree's metadata/hashes, and three read-only peers.
No submitted module/function/import/test/fixture/CLI, archive, reader, model,
new scoring, fit/simulation, remote/account/job operation was executed. No raw
responses/journal, image/capture science output, key content, private audit,
plant, human or pull output was opened; no captures/journal writes, worktree
or push. Source owns implementation, design, state/archive, release/go/current
summaries/frontmatter/INDEX/tracker and dispatch. The separate Stage A report
and row-21 bridge assignment remains queued; its outcome is not reviewed here.

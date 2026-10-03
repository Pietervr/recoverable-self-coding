# AI reader revision 14 — bounded capacity-path review

Date: 3 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`.
Candidate: `7fc9f526af18585418db94ca9b3ddc2228b12336`.
Package digest: `1f5f04a4c60a9eb3f63a23bad08a59bd345c1d437e5130d6c2b4953050d62be4`.
Brief: Unimog `25b7920b9d260e9b4730bef48a1702a251212f26`,
`prompts/2026-10-03_codex_r052_reader_rev14_review.txt`, SHA256
`fc8b71d820cee14610e48abed2d7c57d7465a15186a5a8919bc3638cacb2a84c`.
Ownership: Unimog `feb37eca`; handoff `ae079d75-14ca-56ef-993b-507ca495e8af`
accepted before review edits and delegation.

## Verdict

**NOT FAVOURABLE to this exact revision-14 package.** The two findings in the
revision-13 record `f363767` are repaired, and the job declaration now agrees
with those repairs. One further capacity-path evidence boundary remains:
runtime permits retry on a blank `-o` file whose complete blankness cannot be
re-derived from the retained journal. The eventual validator refuses the journal;
this is bounded wasted-work/non-admission risk, not silent scientific admission.

No favourable STAGE-ATTESTATION is issued. The owner's conditional revision-14
go, recorded at Unimog `e331c52e` for a favourable review on exact `7fc9f52`, is
preserved; its condition is unsatisfied. The brief's earlier statement that only
a revision-13 conditional go existed has since moved. Neither that conditional
go nor this negative review releases job (c), rebinding, archive or execution.
The source brief reports `AIREADER_GO.json` still bound to revision 12.

## 1. Blank `-o` evidence exceeds the retention boundary

This is a **static constructed counterexample**, not observed CLI behaviour or
an executed reproduction. Use the complete declared `CAPACITY_EVENTS` fixture
in `stimuli/photo/tests/test_ai_reader.py:1551`, ordinary short stderr, return
code 1, no timeout, no overflow, and an existing `last.txt` containing **2,049
ASCII spaces**. No agent message, forbidden item or malformed JSON is present.

The executor permits this input. `ai_reader_exec.py:1117` reads `last.txt` up to
1 MiB; 2,049 bytes also fits the 16 MiB temporary-directory cap and, with this
small fixture, the stdout/stderr and journal caps. Thus `overflow=False` is
consistent with the executor, rather than an invented contradictory flag.

At `ai_reader_runtime.py:643–654`, `.strip()` sees a blank file and the declared
capacity exception returns non-retained `provider_failure`. Yet
`FILE_ANSWER_KEEP` is **2,048 bytes**: `bounded` at `470–481` emits length and
SHA256 plus 1,024-space head and tail, `exact:false`, and **no `text` field**.
The journal's bounded-evidence shape check permits that representation.

`ai_reader_journal.py:329–333` correctly requires every non-null `-o` file on a
provider/structural end to have complete exact blank `text` and its matching
digest. It refuses these excerpts before the shared capacity exception is
considered. A hash and blank excerpts cannot prove the omitted middle blank.
With structural stderr (`sandbox: operation not permitted`), runtime correctly
chooses `structural_failure`, but the same retained blank-file evidence still
cannot validate. A 2,048-space control retains complete exact text and fits the
journal rule; absent/empty files remain controls too.

`Job.rec` (`ai_reader_exec.py:668–673`) appends and applies the end without
re-deriving it. The ordinary provider case can therefore retry in `loop`
(`975–1000`) within the existing attempt/clock limits. A later good answer cannot
erase that prior end. Resume validates before dispatch (`852–853`), and scientific
admission validates the completed journal; both refuse it. The structural case
already stops through its durable hold, but its retained end also fails validation.

The evidence truncation and a similar generic no-answer fallback predate this
revision. This finding is confined to the newly declared capacity path's
blank-or-absent, retry and journal-re-derivation contract. It does not reopen the
old generic path, matching rule, scientific gates or completed Stage A review.

**Required before reconsideration:** make retry eligibility and journal proof of
blankness agree. One narrow policy is to require absent or fully retained exact
blank `-o` evidence before granting a capacity retry, and make incomplete evidence
a journal-valid final evidence outcome/hold. Another would require a separately
bound complete proof; whitespace in head/tail alone is insufficient. Preserve the
declared structural hold and full-stream isolation checks. If the blank-file
domain is bounded, declare the limit in UTF-8 **bytes**, and fail closed above it.

Retain no-request cases at 2,048/2,049 ASCII spaces for ordinary and structural
capacity, validating the **actual produced end**, plus executor continuation:
no retry on incomplete blank evidence, the intended durable hold before further
dispatch, and journal agreement on restart/admission. Preserve the repaired
embedded-item, extra-key, received-answer and ordinary-capacity controls. A repair
changes bound hashes: submit a committed revised exact package and fresh retained
fixture evidence. Any later go must cover that revised package and its review.

## Revision-13 R1/R2 and declaration: closed

- **R1 repaired.** `capacity_refusal` at `runtime:517–534` admits only a bare
  error marker with exactly `{type,message}`. It checks `isolation_problems` on
  the original full stream and requires exactly one undeclared-error finding per
  bare marker. An embedded command/tool/malformed item or any extra key removes
  the exemption; received agent or nonblank file answers remain final. No event
  is removed before its item checks. Future diagnostic wording drift fails closed.
- **R2 repaired.** On admitted capacity evidence, `classify` checks the same frozen
  STRUCTURAL pattern on the same retained stderr as `_rederive`. The journal
  excuses bare markers for provider or structural failure, then separately checks
  structural-pattern/label agreement. A forged provider label on structural
  evidence is refused. The executor applies the structural end before another
  loop dispatch; restart derives its durable hold before preflight. The newly
  identified oversized blank-file case is the separate evidence problem above.
- **Declaration repaired.** The job's error sentence names the declared capacity
  exception beside the two notices, including bare markers, turn.failed, no agent
  message, blank/absent `-o`, and structural hold. The unqualified blank-file
  wording is precisely the domain that needs the boundary repair above.

## Exact package and retained evidence

Standard-library git/blob hashing, literal AST reconstruction and opaque owned-CLI
tree hashing reproduced all **25 fields** below. All 16 bound live files matched
the candidate at checking time. Against revision 13 exactly four bound file
hashes and the digest change; the other **20 fields** are identical. The 12
unchanged bound files include set, opaque key, delivery, exec, score, matching,
frame, qualification and the four shared Stage A files. Input/order/prompt,
matching/adjudication and scientific gates remain unchanged.

The owned CLI tree has 52 entries, 42 regular files, no symlinks, 332,968,547 file
bytes and no observed write bits on the tree/root/parent. Its hash binds file
paths and bytes, not owner, modes, xattrs or empty directories; the metadata check
does not establish universal immutability. CLI version uses the frozen label and
retained implementer receipt; the reviewer did not execute the CLI. Network-open
update traffic, provider serving of the requested model label and all enabled
functionality remain unobserved/unaudited limits of the earlier review.

The final suite retained at `92521ac` was run on
`1d325dc9dd786e639179530f8043d8d1c10f0320`. All 12 final retained-file hashes/sizes
match their inventory, and all 24 files across final/first-attempt directories
match the retention commit. Reader implementation/docs/fixtures are identical
between candidate and final-suite HEAD. Commit `1d325dc` itself is a five-line
test-only Stage A skip guard; the entire chronological range from candidate to
that HEAD also contains unrelated report work and is not all test-only.

| Retained source attempt | Main | Build | Combined evidence |
|---|---|---|---|
| First, exact `7fc9f52` | 317 collected: 281 pass, 21 skip, 15 fail | 27 pass | 308 passing executions, 15 failures, 312 distinct exercised cases; main exit 1/build exit 0 |
| Final, `1d325dc` | 317 collected: 274 pass, 43 skip, zero fail/error | 27 pass | 301 passing executions, 290 distinct exercised cases, 11 repeats; both exits 0 |

Final skips: 16 WordNet cases restored by the build row, five older
Rev12Transition cases, and 22 Rev13Transition/Rev14PreparedLink/Rev15Environment
cases now skipped after the live Stage A ledger moved. Exactly 15 first-attempt
failures are in those latter transition classes. Their retained failure text is
consistent with the moved identity/link/counters, not a reader repair failure.
Seven of those 22 passed initially and are also now skipped. This is a real loss
of current Stage A transition regression coverage until a fixed pre-resume copy
replaces the live-state fixture, not an all-transition-fixtures pass claim.

All six Rev13Reader and five Rev14Reader tests pass in both retained attempts.
The new source fixtures test embedded command/tool/malformed items and forged
provider labels, extra keys, structural precedence, ordinary capacity, executor
retry/final/hold behaviour, and the declaration. These support closure of R1/R2;
they do not exercise the oversized blank-file boundary. These are implementer
execution receipts, not an independent rerun or real-provider demonstration.

The full feature inventory is now retained outside the bound package in
`reviews/2026-10-03_reader_cli_0.160.0_features_list.txt`: 155 lines, SHA256
`95bf4feec7973a44f09cb531b3290358e9709795f751a0c8ec809d13b861ea8f`.
Its 21 true flags include removed and stable flags. Retention closes the requested
evidence availability gap; it adds no package pin or audit of all enabled flags.

```json
{
  "ai_reader_qual_set.json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
  "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
  "ai_reader_delivery.json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
  "ai_reader_exec.py_sha256": "ec1e9e7c984e54eb9d41236a42cd56d763533c3c2712291d2d3939c737de7901",
  "ai_reader_score.py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
  "ai_reader_runtime.py_sha256": "ba075ce54a2de829aeca54b81f6c699346601bea7b5e8222b13a2df9ea1c6bd8",
  "ai_reader_journal.py_sha256": "8d76e5b616bf1bb9771ded4518beb46f7563e4437789c07e11b0739ef466e084",
  "ai_reader_key.py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
  "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
  "ai_reader_qual.py_sha256": "6a7f905ebb437c97aee7a784673a0b2ac39bf6ef59462cc282c87a6a10fe04f1",
  "AI_READER_JOB.md_sha256": "26abbcf346abc1f63bc9c9883de73715c8cf90d3ac2d1f7613d16dacf8c25d66",
  "AI_READER_DESIGN.md_sha256": "4f7f1c70def1d479b1c7c4374d5bd5268c011c18c398bb0a8045135cea73cf95",
  "stage_a_guard.py_sha256": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
  "enforce.py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
  "memprobe.py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
  "stage_a_watchdog.py_sha256": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed",
  "codex_realpath": "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/captures/reader_cli/codex-0.160.0/bin/codex",
  "codex_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b",
  "codex_package_json_sha256": "404c4c935bf9b7a57fc02b6f0d09ba6b7bbbf15cf14286fc017de2a6c01cab47",
  "codex_tree_sha256": "ced09ec2c51c8fd4ae4ccb7e0ccb6b6e76d32633ec842f08be000c2a55ba86fe",
  "cli_version": "codex-cli 0.160.0",
  "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
  "command_template_sha256": "19b9e70510466b841faa63d89e0d85f4dc06396573e6c7d9e5ebc5927e8cbca1",
  "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
  "package_digest": "1f5f04a4c60a9eb3f63a23bad08a59bd345c1d437e5130d6c2b4953050d62be4"
}
```

## Scope and carried scientific limits

Read/reason only: candidate reader diff, named declarations, public retained
fixture receipts and feature listing, plus standard-library hashing/counting.
Three delegated checks were read-only source/evidence checks. No submitted
function/import/test/fixture/CLI/fake executor, model/provider/reader, archive or
scoring run was executed by the reviewer. No image bytes, capture arrays, raw
reader journals/answers, private-key semantics, human outputs or forbidden audit
material were opened; the qualification-key check was opaque hashing only.

Job (a) remains not admitted; job (b), 219/600, remains stopped and unscored and
is never reused. Prospective (c) is a fresh 600-request third pass over the already
exposed panel, not blind calibration; the earlier 175-attempt stopped run and
full-bank R2 target-visible/concept-batched exposure remain disclosed. Previous
matching, adjudication and scientific-gate limitations stand. Completed Stage A
mechanism/report and row-19 reviews remain closed; no new go or run permission
for those lanes follows. Source retains implementation, owning summaries,
stimuli/captures/results, archive, go and dispatch. Reviewer owns this record and
its R052 log/lifecycle only; source jobs and foreign files are preserved.

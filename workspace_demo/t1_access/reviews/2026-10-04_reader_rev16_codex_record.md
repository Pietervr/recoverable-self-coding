# AI reader revision 16 — UTF-8 excerpts and the capture boundary

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `9355b2d0e1c4a67525a5fe2185992dc61e0790e3`,
`prompts/2026-10-04_codex_r052_reader_rev16_and_supplement_rev2_review.txt`,
SHA256 `96c9315f8f8cd9857a02e8a30a136bfc02702a9ccf473093e16583a26354b092`.
Ownership: Unimog `2051fcd2`; handoff
`cb86da4f-24e8-51ac-8c49-42e44256c939` accepted before review edits and delegation.
This is one of two separate bounded re-reviews of the revision-15 records at
RSC `478196f`; prior accepted scientific and Stage A reviews remain closed.
Candidate: `89a951761d2d7d058d3ca380936e81489a391208`.
Package digest: `f7f0f2566e6861e4d3d773b6afb5d23045237c4f2ee9007c67fb21200debb7b1`.
Other answer: [supplement revision 2](2026-10-04_stage_a_supplement_rev2_codex_record.md).

## Verdict

**NOT FAVOURABLE to this exact revision-16 release package.** The submitted
UTF-8 excerpt repair fully closes the prior 2,049-byte P2: actual ordinary and
structural marked ends now validate, reconstruct the hold, and recover through
STOPPED. A separate earlier **1 MiB capture cut** still converts a genuinely
blank valid UTF-8 file into apparently nonblank received-answer evidence. That
suppresses the declared capacity hold and permits another request after smoke.
This is not a defect in the new `bounded` algorithm or a reopened old R1/R2;
it contradicts the same package's declared blank/incomplete-file stop policy.

The owner's standing reader go at Unimog `ee585bb8` carries across revisions,
has no expiry and binds to the first favourable exact package R052 verifies.
The favourable condition remains unsatisfied. This review does not release
job(c), archive, rebinding or execution; do not ask for the same owner go again.

## P2: capture-created replacement text bypasses the capacity hold

This is a **static source counterexample**, not observed model output or an
executed candidate reproduction. After a passed ordinary smoke, use the declared
complete capacity event stream, short ordinary stderr, return 1 and a valid
entirely blank `last.txt` of **U+3000 repeated 349,526 times**. Its own bytes total
**1,048,578**, below the 16 MiB attempt-directory allowance.

`ai_reader_exec.py:1117–1120` reads at most **1,048,576 bytes** of that file,
sets the overflow flag from the cut and decodes the captured prefix with
replacement. The prefix ends one byte into a three-byte character. It becomes
349,525 IDEOGRAPHIC SPACEs plus **U+FFFD**; `.strip()` returns U+FFFD although
the complete original file strips blank. Reviewer-only standard-library byte
arithmetic verifies those lengths and the cut; no submitted helper was called.

`ai_reader_runtime.py:670–677` consequently constructs a non-None answer and
sets `capacity=False`. The bare error remains a retained final isolation at
`687–690`, but **without CAPACITY_UNPROVEN**; that branch precedes both the
overflow handling and structural-stderr handling. The same path therefore exists
for structural capacity stderr. There is no retry and no false ok answer.

Journal `_rederive:370–380` also sees a non-None recorded answer, so it requires
no marker. The retained isolation does not set the global capacity or structural
hold. With the first request's smoke already passed, `exec.loop:975–998` can
dispatch the next request. Moving the later 1,024-byte excerpt cuts to code-point
boundaries cannot remove a U+FFFD already manufactured at the earlier capture cut.

`AI_READER_JOB.md`'s header and request-boundary paragraph declare a hold for a
blank file over 2,048 UTF-8 bytes. DESIGN's revision-15 table declares the hold
above the limit **or any incomplete -o evidence**, with no further dispatch.
The captured prefix is incomplete; it supplies no actual received nonblank
answer. Those declarations are not satisfied by this source path. The outcome
being final isolation limits the consequence but does not enforce the promised
job stop.

**Required before reconsideration:** preserve incomplete capture provenance
through decoding/classification/journal admission and make this capacity path
hold before any next dispatch. A cut-created replacement character must not
serve as received-answer proof that bypasses the hold. Keep ordinary/structural
retry restricted to absent or complete exact blank evidence, preserve real
received-answer finality, and never use excerpts as proof of an omitted middle.
Do not weaken the current stop policy merely by laundering captured replacement
text as an answer.

Retain no-request ordinary and structural controls using the valid blank file
at the 1 MiB cut, checking its actual produced end, incomplete validation,
hold reconstruction, no retry/next dispatch and crash/restart after the end.
Keep the 2,046/2,049-byte repair controls and a genuine nonblank received-answer
control. Submit a revised committed package and fixture evidence for this
bounded closure; no scientific or matching review is requested.

## Repairs credited and exact identity

`bounded:491–498` retreats the head cut and advances the tail cut past at most
three UTF-8 continuation bytes. Valid UTF-8 therefore retains complete code-point
prefix/suffix excerpts, each within the byte limit; invalid continuation runs
still receive a bounded shift and replacement decoding. U+3000×683 now gives
1,023-byte blank excerpts at cuts 1,023/1,026. The complete/exact branch and
`file_blank_proven` are unchanged; excerpts remain insufficient blankness proof.
The actual end and after-end crash fixtures cover ordinary and structural cases.
Journal/executor are byte-unchanged from revision 15. Current JOB revision/go
statements are repaired. DESIGN's older Rev6 table still describes the replaced
fixture; update that pointer without rewriting its dated history.

Root reproduces all **25 package fields** and the digest below from candidate
blobs, literal declarations and opaque owned CLI bytes. All 16 live bound files
match the candidate when checked. Versus revision 15 exactly runtime, JOB,
DESIGN and the digest move: **21 fields unchanged**, not the brief's 20.
Thirteen of 16 bound files are unchanged, including journal, executor, matching,
score, key/set/delivery and shared controller dependencies.

The owned CLI tree has 52 entries/42 regular files, no symlinks, 332,968,547
bytes and no observed writable tree/root/parent bits. Its hash does not bind
modes, owners, xattrs or empty directories, nor prove universal immutability.
Version uses the frozen label/retained implementer evidence; root did not run
the CLI. Earlier unobserved serialized request/provider/update-traffic limits
remain, without a new claim of proof.

## Retained suite and scope

The shared retained run is RSC `0b17e39`, on HEAD `89a9517` after supplement
`369e517`: [suite record](2026-10-03_photo_suite_supplement_rev2_reader_rev16_run.md)
and its named public synthetic logs. All 14 listed retained files match sizes
and SHA256 values. Main: 357 collected, 314 OK, 43 skipped, exit 0. Build:
27 collected/OK, exit 0. Combined: **341 passing executions, 330 distinct
executed cases, 11 repeats, zero failures/errors**. The 16 WordNet main skips
are restored by the build row; the other 27 (five Rev12Transition and 22 moved
Rev13/14/15 Stage A transition cases) remain unexecuted. This is not complete
Stage A transition regression coverage.

Actual new reader coverage is **five** `Rev16Reader` collected methods and
**one** `test_ai_reader_crash.Rev16` method with two crash subcases, six new
collected cases together; the brief's six within Rev16Reader is a count error.
All 26 supplement cases pass. No fixture covers either remaining path described
in these two records.

The revised Rev6 test separates a four-second receipt stall, a durable receipt
with four-second close stall, and a 0.3+0.3-second positive control under the
unchanged two-second timer (three-second allowance less two half-second reserves).
The grouped method passes, so all three assertions were reached. This removes
the old coincident two-second wake/timeout assumption without changing production
bounds. It provides injected timing margin, not scheduler-independent timing:
the positive control has 1.4 seconds before additional work, not the declared
two seconds, and has no phase handshake. The prior retained revision-15 main-run
failure remains historical evidence; it is not erased by this passing new run.

Read/reason only. Three delegated peers read exact source and public synthetic
evidence, with scratch-only writes. Root used standard-library Git/blob hashing,
literal AST reconstruction, counts and UTF-8 byte arithmetic. No submitted
module/import/function/test/fake/CLI/model/provider/reader/forward, archive,
scoring or scientific run was executed. No actual capture/image/array/tensor,
raw reader response/journal, private-key semantics, human outputs or prohibited
audit material was opened. Owned CLI and qualification-key bytes were opaque
hash checks only. No remote/account/job action, worktree or push. The source
owns code, current summaries, captures, results, go, archive and dispatch; root
owns these records and its R052 log/lifecycle only.

## Carried scientific and approval limits

Job(a) remains not admitted under its frozen rule. Job(b)219/600 remains stopped,
unscored and never reused. Prospective(c) is a fresh third pass over the same
exposed 600-request panel, never later blind calibration; earlier 175 stopped
attempts and full-bank R2's target-visible/concept-batched/prior exposure remain
disclosed. Matching/adjudication and scientific gates carry. Accepted Stage A,
row19 and earlier closed reviews are not reopened.

## Exact negative attestation

This records refusal and identity; the favourable release gate remains unsatisfied.

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "89a951761d2d7d058d3ca380936e81489a391208",
  "package": {
    "ai_reader_qual_set.json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
    "ai_reader_exec.py_sha256": "ec1e9e7c984e54eb9d41236a42cd56d763533c3c2712291d2d3939c737de7901",
    "ai_reader_score.py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "ai_reader_runtime.py_sha256": "dd9e86549d7645a38cf3a84abc1b1bc0d6e741be991774a42eddfd900e477beb",
    "ai_reader_journal.py_sha256": "296935d5213ca5eaf2828ac694a3b92960c782ed61f1416e466fe06827f5f977",
    "ai_reader_key.py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "6a7f905ebb437c97aee7a784673a0b2ac39bf6ef59462cc282c87a6a10fe04f1",
    "AI_READER_JOB.md_sha256": "5cb0591449ea5a084bab93aea0c98e390bcebf09c3cf1e954111c7890d0f1204",
    "AI_READER_DESIGN.md_sha256": "139e112990e48802a998c15026880292f86e68d49b1edcf83b7412c6288817ac",
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
    "package_digest": "f7f0f2566e6861e4d3d773b6afb5d23045237c4f2ee9007c67fb21200debb7b1"
  }
}
-->

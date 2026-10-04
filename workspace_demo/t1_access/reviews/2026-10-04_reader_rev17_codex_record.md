# AI reader revision 17 — capture provenance and the release gate

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `a4fe7ffbf4ac5460c309c9955af391ad1176594a`,
`prompts/2026-10-04_codex_r052_reader_rev17_and_supplement_rev3_review.txt`,
SHA256 `664c124f1e5ab9e24f22f8fbf1fcba3e0d18f657007a1f57d6c8427f28249254`; R084's whole accompanying adversarial brief read.
Ownership: Unimog `5db1d217`; handoff
`89460a5d-0d67-55f8-a1b0-06c20737e26c` accepted before review edits and delegation.
This is one of two independent class reviews answering RSC `1abb851`.
Accepted science, base Stage A, row19 and old matcher reviews remain closed.
All source line references are to the candidate under `stimuli/photo/`.
Candidate: `977655f2612b0edac894bb246bc868ca41f60537`.
Package digest: `4517553a0615436d8a0c384849c43a206fd9e428729d1d91ef6a0d68bf4b3e35`.
Other answer: [supplement revision 3](2026-10-04_stage_a_supplement_rev3_codex_record.md).

## Verdict and carried go

**FAVOURABLE to this exact reader release package, with the scope qualifications
below.** The real 1 MiB blank-file cut now holds, validates and reconstructs
through crash/restart. Across the reviewed class, incomplete capture cannot
produce an `ok` result or a retryable label; incomplete -o text cannot supply an
answer; capacity exceptions require complete clean evidence; and the declared
visible-capacity policy enforces its durable hold before the next dispatch.
No blocking source path was found within that operational rule.

This does **not** prove the stronger introductory sentence that all decoded
incomplete/unretained content can never decide any answer field. Partial stdout
messages may remain received evidence on a final error, and capacity hidden in
an omitted middle is outside the declared visible-text detector. Those limits
must accompany the favourable verdict; details follow below.

The owner's standing reader go at Unimog `ee585bb873c5d3db1329504adc2156caa5814684`
carries across revisions without expiry. This is the first favourable record
for revision 17: R052 must verify the exact package, bind that standing go to
this committed record, and carry archive/preflight/delivery/resource gates
before source-owned job(c). No new owner turn is needed for that same go.
This review does not execute or archive anything, approve the supplement, or
admit scientific reader results in advance.

## Class closure credited

`read_capture` records bytes read, same-open-file fstat size and whether the cap
cut it (`ai_reader_exec.py:458–469`, used at `1127–1140`). `capture_complete`
requires no cut and read equal to that recorded size (`runtime:660–669`).
Production passes explicit capture facts; default complete in-memory evidence
is a fixture convenience, not a production assumption. The absent -o file is
represented by None; stdout/stderr are explicit three-field records.

The previously reviewed U+3000×349,526 file is 1,048,578 bytes. A 1,048,576-byte
cut can manufacture U+FFFD when decoded, but `classify:710–718` no longer uses
that incomplete -o text as an answer or proof of blankness. The complete capacity
shape with unclean file/stderr/overflow evidence yields the exact final isolation
plus CAPACITY_UNPROVEN (`728–731`). This holds for ordinary and structural
stderr, for all character-cut offsets, for a boundary prefix that decodes blank,
and for complete nonblank contradictory -o evidence. The latter is a declared
prospective behavior change, not an accidental waiver of received-answer rules.

`capacity_clean:679–685` grants the exception only with an absent -o or complete,
exact, retained-whole blank -o ≤2,048 re-encoded UTF-8 bytes, complete retained
stderr, and no overflow. Ordinary clean capacity remains provider failure;
structural stderr remains the structural hold (`732–737`). No excerpt proves
an omitted middle blank. Invalid complete -o bytes decode to nonblank replacement
text and the capacity shape holds; file-open failures take crash/recovery rather
than being laundered as absence. The latter cases are source reasoning, not new
executed tests.

When capacity text is visible in an event stream not captured AND retained whole,
`capacity_possible:688–693` yields final overflow, marker only, answer None
(`721–724`). Classifier and journal derive the same visible-text rule. Journal
`_capture_ok/_capture_agrees:304–325` checks the exact schema, typed nonnegative
read/size values, boolean cut, stdout/stderr retained raw lengths and file presence.
`_rederive:402–436` requires the marker in both directions and the declared
outcome/answer shape, refuses incomplete -o answers, and refuses `ok` on any
incomplete capture. Durable hold/recovery then precedes every further dispatch.

## Precise limits of the class statement

**Final-error evidence is broader than the introductory “never an answer” claim.**
`classify:710/713` still prefers a parsed agent_message from captured stdout
without first checking stdout completeness or retained-whole status. A complete
agent_message in a captured prefix can remain `answer` on final isolation or
overflow (`739–743`) even when additional stdout was not captured. Journal
`419` bars incomplete -o-derived answers only when there is no event answer;
it permits that final-error evidence. The new outside-capacity fixture has no
agent_message and does not cover this distinction.

This does not create `ok`, a retry, a missing required visible-capacity hold or
a scored match: incomplete capture implies overflow, the final-error branches
precede `ok`; journal `345` bars retry labels on head/tail streams and `421–422`
bars incomplete `ok`; received-agent-message checks bar retry labels; scoring
gives ERR_ISOLATION/ERR_OVERLENGTH precedence over matching (`ai_reader_score.py:
135–136`). It is retained received text on an error, not an admitted answer.
Keep that qualification in current external summaries; do not edit a bound file
and continue claiming this exact package unchanged.

**The detector is explicitly about visible retained capacity text.** Markers
entirely hidden in an omitted middle, split across a capture cut, or encoded so
the frozen raw text is not visible need not set CAPACITY_UNPROVEN. A fully captured
oversize event stream can still be retained only as head/tail. Such evidence
remains a final error; outside smoke it need not stop the whole job. This is the
declared observable-policy limit in R084's brief and DESIGN's table, not a proof
that every semantically capacity-related stream globally holds. The flood control
intentionally has no hold without visible capacity text. I do not reopen the
closed general isolation/matching policy or infer an invisible-marker guarantee.

Capture facts are read-time provenance, not a signed assertion or universal
snapshot proof. File read length is not independently bound to the replacement-
decoded/re-encoded -o evidence length; coherent fabrication of several fields is
outside these schema checks. Same-open fstat before read cannot itself prove no
later mutation; group cleanup precedes production capture and the previously
recorded process-containment residuals carry. These are not new provider or OS
measurements.

## Fixtures and exact package

Declared reader adversarial groups 1–13 are represented in eight methods plus
the expanded crash method; group14 is expressly reasoned. The retained real
executor cut checks both stderr variants, STOPPED, one rq2 dispatch and zero
rq3, actual capture facts/answer None, validation before/after receipt and hold
reconstruction. Four crash subtests cover both boundaries/variants. Size-change
and stderr-cut cases manufacture capture facts; they do not induce real fstat
races. Three schema mutations check helper predicates rather than each full
journal validator. New record-level validations omit a separate raw_bytes check;
older raw-byte controls remain in the suite. Coverage is meaningful and finite.

Root reproduces all **25 package fields** and the digest below; all 16 live bound
files match when checked. Exactly executor/runtime/journal/JOB/DESIGN/digest move
from revision16: **19 fields unchanged**, 11 of 16 bound files unchanged. The CLI
tree has 52 entries/42 regular files, no symlinks,332,968,547 bytes and no observed
writable tree/root/parent bits. The tree digest does not bind modes, owners,
xattrs or empty directories or prove universal immutability. Version uses the
frozen label/retained implementer receipt; reviewer did not run the CLI. Earlier
unobserved serialized-request/provider/update-traffic limits carry.

## Retained evidence and review boundary

Shared retained run: RSC `b532f08`, HEAD `977655f` after supplement `4baba91`;
[suite record](2026-10-04_photo_suite_supplement_rev3_reader_rev17_run.md).
All 14 inventory files independently match their sizes and SHA256 values.
Main: 373 collected, 330 OK, 43 skipped, exit 0. Build: 27 collected/OK,
exit 0. Combined: **357 passing executions, 346 distinct executed cases,
11 repeats, zero failures/errors**. Sixteen WordNet skips are restored by the
build row; five Rev12Transition and 22 moved Rev13/14/15 Stage A transition
cases remain unexecuted. This is not fresh complete Stage A transition coverage.

Eight new Rev17Reader methods and eight Rev3Adversarial methods account for the
16 added collections. The crash method remains one collected method, now with
four subtests (ordinary/structural at the 2,049-byte and 1 MiB boundaries).
All 34 supplement methods pass. A passing fixture is evidence for its assertions,
not proof of every possible crash interleaving or actual provider behavior.
The Rev6 timing controls pass; their 0.6-second success sleeps under a two-second
timer leave 1.4 seconds before other scheduling/I/O, not immunity to arbitrary
scheduling delays. The old failed run remains historical evidence.

Three read-only peers reviewed source and named public synthetic evidence.
Root independently used standard-library Git/blob hashing, literal AST
reconstruction and metadata/count checks. No submitted module/import/function,
test/fake/fixture, CLI/model/provider/reader/forward, archive or scoring ran.
No actual capture/image/array/tensor, raw reader response/journal, private-key
semantics, human output or prohibited audit material was opened. Owned CLI and
qualification-key bytes were opaque hashes only. No remote/account/job action,
worktree or push. Code, current summaries, captures, results, go, archive and
dispatch belong to the source; these records and root's R052 log/lifecycle are
the only owned repository edits.

## Scientific limits retained

Job(a) remains not admitted under its frozen rule; job(b)219/600 remains stopped,
unscored and never reused. Job(c) is a fresh third pass on the SAME EXPOSED
600-request panel, never later blind calibration. Earlier 175 stopped attempts,
full-bank R2's target-visible/concept-batched limitation and prior exposure remain
disclosed. Matching/adjudication, finite panel qualification and scientific gates
carry; favourable execution mechanism is not an advance result verdict.

## Exact attestation

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "977655f2612b0edac894bb246bc868ca41f60537",
  "package": {
    "ai_reader_qual_set.json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
    "ai_reader_exec.py_sha256": "5fbb730d1f10c6c38dc638f06a7d1f57e724ed7efeba8e8a7b93382d783ae097",
    "ai_reader_score.py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "ai_reader_runtime.py_sha256": "cb78adaa56a34f45430ea26429dbc0aa1c204fc48bbec454f1af35ff42ebec32",
    "ai_reader_journal.py_sha256": "b67d25526c715434b55e6410d1b66046a9437ca48c825c34fabd9705515613a2",
    "ai_reader_key.py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "6a7f905ebb437c97aee7a784673a0b2ac39bf6ef59462cc282c87a6a10fe04f1",
    "AI_READER_JOB.md_sha256": "1484b829486a400d0fc4ba667f84168e6071ade8e09252b13556fbec49720a09",
    "AI_READER_DESIGN.md_sha256": "e50d814de7cb0e4af31791d1d6d9464b25c35d4d58753fa6656f6e1962ca5c75",
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
    "package_digest": "4517553a0615436d8a0c384849c43a206fd9e428729d1d91ef6a0d68bf4b3e35"
  }
}
-->

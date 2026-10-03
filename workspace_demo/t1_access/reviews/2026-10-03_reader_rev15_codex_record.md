# AI reader revision 15 — retained capacity evidence and recovery

Date: 3 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`.
Brief: Unimog `97408f889456296bc0c761bf978e54bef37402e3`,
`prompts/2026-10-03_codex_r052_reader_rev15_and_supplement_review.txt`, SHA256
`ef75d83904851ea18a4399f612d289dd0771dc1768a7b8720da78f508cb7c7e6`.
Ownership: Unimog `b2e74539`; handoff `13e033f7-cbde-5fe3-927a-08d0b5eb1254`
accepted before review edits and delegation. This is one of the two requested
bounded reviews; the other is linked below.
Candidate: `05bd60b23697c148e112e453ca8779512d2869ab`.
Package digest: `c0c34b6b70f2e3f25f61c2a9dfdc53786f3439e8b5c491de5d17513ee9018cc4`.
Other review: [row-20 supplement](2026-10-03_stage_a_supplement_codex_record.md).

## Verdict

**NOT FAVOURABLE to this exact revision-15 package.** The revision-14 ASCII
blank-file finding is repaired. Applying the durable hold to ordinary and
structural capacity alike, independent of the unretained overflow flag, is
appropriate. A multibyte whitespace boundary still produces an actual marked
end that its independent journal validator rejects. It prevents valid recovery;
the new hold prevents retry and further dispatch, so this is not unsafe scoring
or renewed retry authority.

The owner's standing reader go at Unimog `ee585bb8` carries across revisions,
has no expiry, and binds to the first favourable exact package verified by R052.
That condition remains unsatisfied. No new owner turn is required merely by a
revision change. This negative attestation does not release job (c), archive,
rebinding or execution; the gate requires verdict `favourable`.

## P2: UTF-8 excerpt boundaries invalidate an actual marked end

This is a **static constructed counterexample**, not observed CLI output or a
submitted-function reproduction. Use the declared complete `CAPACITY_EVENTS`,
short ordinary stderr, return 1, no timeout or overflow, and `last.txt` containing
U+3000 IDEOGRAPHIC SPACE repeated **683** times. Python `str.strip()` treats all
of it as blank. Its UTF-8 length is **2,049 bytes**. Standard-library byte/strip
arithmetic independently checks these facts; no candidate function was invoked.

`ai_reader_exec.py:1117–1120` reads this whole file below its 1 MiB cap and
decodes it losslessly. `ai_reader_runtime.py:666–670` correctly returns retained
final `isolation_violation`, answer None, with `CAPACITY_UNPROVEN`, because the
blank file exceeds `FILE_ANSWER_KEEP=2048` and is not retained complete/exact.

But `bounded` at `runtime:483–489` slices the **bytes** at 1,024 for both excerpts
and independently decodes them with replacement. Each whitespace character takes
three bytes: the head ends and tail begins inside a character, producing U+FFFD
REPLACEMENT CHARACTER. Thus both retained excerpts fail `.strip()==''`.
The normal bounded representation is legal; `_rederive` at
`ai_reader_journal.py:374–378` nevertheless rejects the actual marked end because
it additionally requires both excerpts to strip blank. Structural stderr produces
the same mismatch: marked isolation precedes that branch in both variants.

`Job.rec:668–673` durably appends and applies the flag. The live loop
(`exec:975–977,993–998`) holds before retry or another dispatch and can write
STOPPED. A crash immediately after the durable end (`1121–1123`) leaves a journal
which restart rejects at `852–853`, before the promised hold-to-STOPPED path at
`861–863`. Even a subsequently written STOPPED journal fails independent
`validate(require_complete=False)`. No later answer can repair that prior end.

**Required before reconsideration:** make retained UTF-8 excerpts and marked-end
validation agree for the declared blank-file domain. Keep provider/structural
retry restricted to absent or complete exact blank evidence; preserve full-stream
item checks, received-answer guards and both durable holds. A digest or blank
excerpts do not prove the omitted middle blank. Do not solve this by broadening
that retry exemption or treating excerpts as complete blankness proof.

Retain no-request multibyte whitespace controls at 2,046/2,049 bytes, ordinary
and structural capacity, checking actual produced ends, incomplete validation,
hold reconstruction and executor no-next-dispatch. Include crash/restart after
the marked durable end and before STOPPED. The eight new fixtures use ASCII
spaces; their passes do not cover this split-codepoint case. Submit a committed
revised exact package and fresh fixture evidence for a bounded reconsideration.

## Credited repairs and declaration

The ASCII 2,049-space ordinary/structural case now produces the intended marked
final end and journal-valid durable hold. `file_blank_proven:493–496` checks absent
or complete/exact blank evidence; marker checking is bidirectional at
`journal:370–380`; `fresh/apply/reconstruct/holds` derive the flag, and validation
admits only tail repair/STOPPED after it. Marking before the overflow exception is
sound because the journal cannot independently reconstruct that flag. It also
avoids treating structural stderr as retry permission. Revision-13 R1/R2 remain
repaired and closed; no whole-stream or structural-precedence review is restarted.

Current `AI_READER_JOB.md:16,176–178` still calls the uncalled/current job(c)
package revision 14 while its header declares revision 15. The holder should
align these current statements when rebuilding and preserve dated historical
results. This is an adoption defect, separate from the code blocker.

## Exact package and retained suite

Standard-library Git/blob hashing, literal AST reconstruction and opaque owned
CLI hashing reproduce all **25 fields** in the negative block below. All 16 bound
live files matched the candidate when checked. Against revision 14 only runtime,
journal, JOB, DESIGN and the digest differ; the other 20 fields are unchanged.
Set, opaque key, delivery, executor, score, matching, qualification and shared
Stage A code remain unchanged. The CLI tree has 52 entries/42 regular files,
no symlinks, 332,968,547 bytes and no observed tree/root/parent write bits.
Its hash does not bind modes/owners/xattrs/empty directories or establish universal
immutability. Version uses the frozen label/retained implementer evidence; no
reviewer CLI invocation. Enabled features, provider serving and update traffic
remain earlier unobserved limits.

Shared suite `79a6621` ran on HEAD `05bd60b` after supplement `b67a073`. All 18
retained inventory files match sizes/hashes. The suite record is
`2026-10-03_photo_suite_supplement_reader_rev15_run.md` (SHA256
`71f875b907bdc304f187d4e6e89f28233135a02ac7d19704acce70c5b64a9fc5`).

| Evidence | Result |
|---|---|
| Main | 344 collected: 300 OK, 1 FAIL, 43 skipped; zero errors; exit 1 |
| Build | 27 collected/OK; zero failures/errors/skips; exit 0 |
| Combined | 328 executions: 327 pass, 1 fail; 11 repeats; 317 distinct executed cases |
| New reader / supplement | 8/8 and 19/19 pass, retained synthetic fixtures |

The 43 main skips are 16 WordNet cases restored by the build row, five
Rev12Transition cases and 22 moved Rev13Transition/Rev14PreparedLink/
Rev15Environment cases. Those **27 transition cases remain unexecuted** in this
run; this is not complete Stage A regression coverage. No reviewer rerun occurred.

**The retained Rev6 timing failure does not independently block revision 15.**
`test_slow_receipt_and_slow_close_share_one_deadline` uses
`slow_close_run(3.0,2.0)` (`test_ai_reader_crash.py:367–383`). Three seconds is the
total final allowance; `airq_fixture.py:101–124` sleeps **two seconds before
receipt append and two before clock closure**, not a three-second receipt.
Executor `stop:697–702` arms its timer at allowance minus the two 0.5-second
reserves: a **two-second timer**, armed before starting the receipt write. The injected
receipt wake and abort trigger coincide; there is no positive durability margin.
The failed assertion finds the last end/ok rather than receipt/COMPLETE; exit 75
passed, but later admission and fast controls were not reached in that execution.

Missing COMPLETE refuses journal admission (`journal:637–638`); completion also
requires the matching finished clock, marker and absence of a matching abort
tombstone (`exec:1160–1182`). The unchanged single deadline spans receipt and
clock closure, with late commit revocation. There is no evidence of false
admission. Failed raw/clock/interleaving timestamps were not retained, so the
specific schedule and tombstone state cannot be inferred. The reported standalone
one-fail/two-pass run is unretained testimony; three subsequent retained passes
do not erase the main failure. Rerun load is not the failure-time load or causal
proof. Keep the failure and correct its description; replace the equal-deadline
fixture assumption with distinct, deterministic receipt-stall and durable-receipt/
slow-close controls. Do not weaken production closure bounds.

## Scope and carried limits

Read/reason only. Three delegated peers inspected source/public synthetic receipts
read-only. Root performed standard-library hashing/AST/count/byte arithmetic.
No submitted module/import/function/test/fake/CLI/model/provider/reader/forward,
archive, scoring or scientific run was executed. No actual image/array/tensor,
raw reader response/journal, private-key semantics, human outputs or prohibited
audit material was opened. Owned CLI and qualification-key bytes were opaque
hash checks only. No remote/account/job action, worktree or push.

Job(a) remains not admitted; job(b)219/600 remains stopped, unscored and never
reused. Prospective(c) is a fresh third pass over the exposed 600-request panel,
never later blind calibration; earlier 175 stopped attempts and full-bank R2
target-visible/concept-batched/prior exposure remain disclosed. Matching,
adjudication and scientific-gate limits carry. Accepted Stage A and row19 reviews
remain closed. The source owns implementation/current summaries/captures/results/
go/archive/dispatch; root owns this review and its R052 log/lifecycle only.

## Exact negative attestation

This block records refusal and exact identity; it is not a favourable release.

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "05bd60b23697c148e112e453ca8779512d2869ab",
  "package": {
    "ai_reader_qual_set.json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
    "ai_reader_exec.py_sha256": "ec1e9e7c984e54eb9d41236a42cd56d763533c3c2712291d2d3939c737de7901",
    "ai_reader_score.py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "ai_reader_runtime.py_sha256": "d5e921c499f9c8682049e1dd893d47484b09c1fb6449df62fe7d412ed33d38a9",
    "ai_reader_journal.py_sha256": "296935d5213ca5eaf2828ac694a3b92960c782ed61f1416e466fe06827f5f977",
    "ai_reader_key.py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "6a7f905ebb437c97aee7a784673a0b2ac39bf6ef59462cc282c87a6a10fe04f1",
    "AI_READER_JOB.md_sha256": "bbc1da6dd2f36dd1db2347155f283e8ae49a0ba81917f1f048abbc91834d05ec",
    "AI_READER_DESIGN.md_sha256": "0efd901a13639e9442cbdbba305bad83fb05c62c8839e7c922334aee7f24f2c3",
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
    "package_digest": "c0c34b6b70f2e3f25f61c2a9dfdc53786f3439e8b5c491de5d17513ee9018cc4"
  }
}
-->

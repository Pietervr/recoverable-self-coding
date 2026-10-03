# AI image-reader qualification revision 11 — Codex review

Date: 2 October 2026. Reviewer: Codex, **GPT: R052 Entropy paper**,
native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: **`308901c825ca2fcc28c716e22ff83973e68cb2b1`**.
Prior favourable revision-10 records: `339018303643d44bbeab087cf2d891553af7dd56`,
candidate `fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`.
Assignment: Unimog `prompts/2026-10-02_codex_r052_rev11_both_packages_review.txt`
at `5b50c45445236e7864f035815c41479e476d1700`, SHA256
`4945baf5af8bd838e6063ed66c96088f77d90baf3f4955aac91cd4f269359ad0`.
Handoff `6ff60a4a-b4e0-5f06-945a-3631b5211189` was accepted after committed ownership.

## Verdict and scope

**FAVOURABLE for this exact reader package as a bounded qualification mechanism.**
The vanished-helper repair meets its condition; no remaining reader implementation
condition is imposed here. Alternative (a) uses the existing mechanism under an
owner-authorized fresh envelope and package-bound go, with fresh state and the
closed first job retained and its spend disclosed. The owner has not chosen it
through this record. Alternative (b) requires a reviewed continuation rule.

The reader job remains 600 frozen requests under its own 660-attempt/six-hour
envelope and existing recovery, storage and empirical scoring requirements.
The first job remains closed STOPPED, never scored; source reports 175 attempts
and 1,097.4 seconds spent. No empirical reader gate, naming equivalence, Stage B
admission or later audit authorization follows from a mechanism review.

Read/reason only: committed source and full relevant declarations, prior records,
fixture source and retained textual evidence, with standard-library git/JSON/AST/
hash arithmetic and independent read-only peers. Declared set/key/delivery were
byte-hashed only. No key content, raw journal, capture, image, answer or private
audit output was read; no image was opened or named. No submitted module/function/
import/test/fixture/CLI, forward, model, scientific/remote/job/account operation,
worktree or push was executed. Existing exposure limitations stand. Source retains
implementation, framework, ledger, protocol, stimuli, captures, go and dispatch.

## Question 2 — vanished-entry repair and producing fixtures

`stimuli/photo/ai_reader_exec.py:457–477` walks without following directory
symlinks and uses one `os.lstat` per listed file. ENOENT/ENOTDIR after listing
are skipped; other walk/stat errors propagate. Only observed regular-file sizes
are added. This removes the transient helper disappearance exception without
accepting an unreadable directory as a successful empty measurement.

The attempt-root cap (`990–991`), live attempt directory/output checks
(`1094–1097`) and quick-exit/final size check (`1109–1111`) remain. Other ordinary
filesystem errors reach the admitted run's STOPPED/reconciliation path
(`674–701,870–880`). A walk of a changing tree remains sampled and non-atomic;
this repair does not promise to count vanished entries or every transient byte
allocation between checks. No such universal guarantee is required here.

The new tests produce complementary transitions:

- `tests/test_ai_reader.py:1489–1502` unlinks an already-listed helper immediately
  before the real `lstat`, then requires the two persistent files' 150 bytes.
  It forces the new ENOENT branch rather than arranging an already-empty tree.
- `1504–1528` runs an actual thread creating/removing directories, files and
  symlinks while 300 measurements retain the stable lower bound without raising.
  It checks live churn, without claiming an atomic exact total.
- `1530–1539` makes a real directory unreadable and requires `PermissionError`.
  The retained non-root environment passed; this is not a root/ACL guarantee.
- `tests/test_ai_reader_crash.py:753–761` uses the real executor process with the
  fake CLI's three-second helper churn (`tests/fake_codex.py:112–124`), requiring
  COMPLETE and admitted clock. It is a six-response synthetic job, not 600 real
  responses or an empirical naming test. The unit controls the exact stat instant;
  the process case checks integration during live churn.

The old repeated `Path.stat` implementation is statically vulnerable to this
race. Attribute the separately reported old-code failure to the implementer:
the current retained exact unit patches `os.lstat`, whereas revision 10 calls
`Path.stat`/`is_file`/`is_symlink`. In the declared local CPython 3.12 environment
those methods route through `os.stat`, so the identical current patch alone
does not replay the old failure. This qualification does not diminish the
current unit's genuine removal transition or create a new reader gate.

## Question 1 — shared watchdog and separate Stage A outcome

The reader normally arms the shared watchdog behind its worker gate, receives
ARMED and persists dispatch before GO (`executor:1044–1083`). The watchdog's
new leader NOTE_EXIT watch is therefore established before normal work, and a
later unanswered process probe alone no longer retires it (`stage_a_watchdog.py:
183–217`). Controller-death, stale-beat and deadline checks remain; the reader
does not use the Stage A sampler tick channel. Initial identity/registration
fallbacks at `188–191` qualify the literal “NOTE_EXIT only” declaration.

Reader completion still confirms group/member cleanup, reaps and ends the
watchdog (`executor:916–925,1000–1009,1149–1156`). The retained escaped-member
and controller-death fixtures remain relevant. The Stage A sampler wait and
gates exception paths are not reader executor paths. The separate Stage A record
is **not favourable**: old/new identity admission, gates HELD closure/accounting,
and the live controls during its watchdog-loss wait need bounded repairs.
Those findings do not invalidate this reader's ordinary fresh-job mechanism.

## Question 3 — owner choice and actual next-job preparation

`AI_READER_JOB.md:143–156` correctly preserves the first job as closed and
discloses its spend. Arithmetic: 485 attempts and 20,502.6 seconds remain;
a fresh 600-request job needs at least 600 dispatches, so it cannot use that
remainder. The 425-unfinalised-request claim is source metadata, not a reviewer
inspection of answers or reconstruction of the private journal.

**Alternative (a) needs no further mechanism review if this frozen package is
unchanged and the existing admission/owner requirements are met.** It needs a
separate new 660-attempt/six-hour allowance, package-bound go, retained/archive
of the old raw and clock evidence, and fresh raw/clock state. Scientific paths
are fixed (`executor:98–101,656–658`); mixed old-package state is refused
(`837–841`) and any receipt is terminal (`842–844`). Running against the existing
closed files will refuse. Fresh-state preparation is ordinary job setup under
the owner's choice, not silently resetting spend within the first job or an
unreviewed after-receipt continuation feature.

Alternative (b) would change receipt/state/package admission and continuation
semantics. It cannot run on this package as it stands and needs its own reviewed
rule. No choice, archive, release, rebind, new allowance or launch is performed
or authorized by Codex here.

## Evidence, declaration qualifications and question 4

All 24 fields below reproduce from committed blobs and pinned byte metadata;
declared private set/key/delivery were not decoded. Retained suite `7d7cbd4`
names exact candidate HEAD and empty photo status. All ten retained file sizes
and hashes match: main exit 0, 262 tests in 2,080.421 seconds, five WordNet
skips; those same five passed separately in 0.660 seconds, exit 0. Thus 257
non-skipped main checks plus five separately run checks cover 262 distinct
cases, not 267. All four new reader cases are reported OK. These are verified
retained implementer observations, not reviewer executions or scientific results.

The pre-commit disclosure remains one identified STOPPED observation plus one
unidentified failure, cause unresolved. Later nonrecurrence does not resolve the
cause; the two diagnosed 2 October execution races remain separate events.

Scope the old absolute no-model statements (`AI_READER_JOB.md:7`,
`AI_READER_DESIGN.md:118`) to historical/local mechanism checks or the new
candidate, preserving the reported earlier 175-attempt real job. Read “neither
implemented” (`JOB:155`) as neither owner alternative selected/prepared:
(a) uses the existing mechanism; (b) actually needs new continuation code.
These are truthful declaration qualifications, not additional reader mechanism
conditions. An edit to a bound document moves the package and cannot reuse
this attestation as though the package were unchanged.

This record contains one favourable qualification attestation. The strict go
guard separately requires the immutable record commit/path/hash, ancestry,
dates, all attested/re-derived/current fields and dated owner words. The negative
list supplements that positive match. No AIREADER_GO or owner approval is
created. Stage A has its own negative record and no favourable block here.
Prior row-19/bank/text decisions and exposure disclosures remain separate.

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "favourable",
  "reviewer": "Codex (GPT: R052 Entropy paper; native 01a0d19e-2127-7051-9a61-6db771088559)",
  "date": "2026-10-02",
  "reviewed_commit": "308901c825ca2fcc28c716e22ff83973e68cb2b1",
  "package": {
    "ai_reader_qual_set.json_sha256": "27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8",
    "ai_reader_exec.py_sha256": "9ff61681702f47a2971aa1e512fe38492206458391f539cbf483a635caa53a0d",
    "ai_reader_score.py_sha256": "c66e6183f41a48dd9ac6aa2d15d5d952a5a0f0b5c15d842f594c11bf91f0aeaf",
    "ai_reader_runtime.py_sha256": "96235ea8e276b49ee671437776ee45d49a0249db70ce69b17849881fd4cac89e",
    "ai_reader_journal.py_sha256": "e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907",
    "ai_reader_key.py_sha256": "e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc",
    "AI_READER_JOB.md_sha256": "c29f9b96520e1b4a611d721e43a0c2df282f05db369b8a758cecec9577a455c9",
    "AI_READER_DESIGN.md_sha256": "2da524db7b588ada91a4da69f5c255847244e6de1e361f31abe3f737b05b8c77",
    "stage_a_guard.py_sha256": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
    "enforce.py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
    "memprobe.py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
    "stage_a_watchdog.py_sha256": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed",
    "codex_realpath": "/opt/homebrew/Caskroom/codex/0.159.3/bin/codex",
    "codex_sha256": "4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878",
    "codex_package_json_sha256": "8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121",
    "cli_version": "codex-cli 0.159.3",
    "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
    "command_template_sha256": "031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba",
    "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
    "package_digest": "6be7d4c8fc6b113f4505af166386f8cf3df23446ccfe19df61114bb5d2e4b760"
  }
}
-->

# AI image-reader revision 10 — Codex review

Date: 2 October 2026. Reviewer: Codex, **GPT: R052 Entropy paper**,
native `01a0d19e-2127-7051-9a61-6db771088559`.
Reviewed candidate: **`fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`**.
Retained suite: `57007770f8ae135cdb6c45ab191d1cdf1b2de827`.
Prior review: `dda950bc71e7ec526dbc9bd99a988f23a527557f`,
`2026-10-02_rev9_both_packages_codex_record.md`.
Assignment: Unimog `prompts/2026-10-02_codex_r052_rev10_both_packages_review.txt`,
at `ebb1aaba954820ca9951765dde008819c58827db`, SHA256
`7dc8a36f318b0be8a6afff7ebe75cde70213d8e5c7fbf961f24a347ad15e117c`;
handoff `a91531fb-5fce-5aaa-a7c6-7c66372acd44` accepted after ownership was saved.

## Verdict and scope

**FAVOURABLE for this exact AI-reader qualification package as a bounded mechanism.**
The remaining readable live-foreign-start condition of the prior review is closed.
No remaining reader mechanism-review condition is imposed here. This does not
supply the dated owner go or establish empirical qualification: the frozen
grayscale naming gate remains **61 of 63 easy items**, not presumed passed.

The proposed job remains 300 paired items/600 responses, at most 660 attempts and
three per request, with six hours cumulative time. An answer is final; permitted
retry does not include a wrong name or abstention. Later audit authority, human
free-naming equivalence, independent errors, training-data independence and per-image
rights clearance are not established by this mechanism verdict. Prior private-use
scope, specificity/plural decisions and construction-exposure disclosures stand.
This exposed review session is not a later blind reader.

Read/reason only: immutable source, documentation, test source and retained textual
evidence were inspected, with independent read-only peer checks and standard-library
git/JSON/AST/hash arithmetic. No submitted module, program, test, fixture or CLI was
executed/imported; no model, image, forward, scientific, cloud/account or cluster
operation was performed. Qualification set/key blobs were **hash-only**, never
decoded or parsed; no image was opened or named. Implementation, source docs,
protocol, tracker and dispatch remain with their existing owners.

## Question 1 — live foreign start and producing evidence

Every new pending record retains its process identity (`stimuli/photo/ai_reader_exec.py:
693–705`). Holding TaskLock, recovery collects final files and readable temporaries
without a final file, excludes this start's own paths, and calls `end_foreign_start`
before clock absorption (`729–748`). The helper checks the retained PID/start
identity, SIGKILLs a matching live foreign start and confirms that identity is gone
before returning an end (`226–245`; `memprobe.py:99–112`). A still-live identity
beyond the ten-second polling allowance refuses/holds before its final charge or
pending removal. This is a bounded local identity mechanism, not a universal promise
about unavailable or stalled OS probes and signals.

Only a confirmed end becomes `ended_wall` (`745–746`), prioritized over the previous
deadline-clipped charge by Clock (`315–324`). Each sid is closed once and made known.
The recovered-balance callback still precedes the first persist (`332–334,751–771`),
and foreign pending evidence is removed only after that persist returns (`773–775`).
Admission occurs later. A crash after durable charging but before deletion therefore
leaves a known sid that is skipped on recovery; a failure before first persistence
leaves the pending evidence for the existing conservative dead-start policy. The
confirmed end is used in memory to persist the charge, not archived as a separate
independent death receipt. Historical wall-clock values are not newly authenticated.

`tests/test_ai_reader_crash.py:712–750` **produces** the disputed transition in two
subtests: S1 alive before the lock with a final pending file, and S1 alive with only
its readable temporary. The driver actually flushes/fsyncs that temporary and stalls
before rename (`tests/airq_fixture.py:155–167`), or stalls TaskLock after ordinary
publication (`176–177`). In both subtests, S1 has a healthy 60-second setup timer. The fixture
asserts S1 alive with matching identity before running S2, then checks SIGKILL exit,
identity gone, one failed-start entry, charge at least recovery-time minus start and
below 60 seconds, pending evidence removed and admission successful. It supplies
neither a final clock nor an ended-wall value to simulate recovery.

Limits: the new test does not separately record an exact death timestamp against
which it compares the charge, run S3, inject a crash in this kill-to-persist interval,
or force a surviving-identity timeout. The ordered code and checks against known sids
support those bounded properties; the retained prior once fixture (`crash:570–582`)
actually crashes after first clock persistence before removal and checks one charge.
These limits add no new blanket gate. Previously closed A, B1–B3 and other control,
evidence, clock and isolation paths remain closed; no concrete regression was found.

## Question 2 — declarations 4–6

4. The current design (`AI_READER_DESIGN.md:17–19`) correctly states that the late
   commit is released at fired plus 50 ms. It does **not** witness completion of an
   early unlink. The static post-return fired check/undo and repeated removal support
   the mechanism. The historical revision-9 table/comment's stronger ordering words
   are expressly qualified by this current paragraph and are not observed evidence.
5. The marker residual is **unavailable effective revocation**: tombstone unpublished
   and neither removal path completing. It includes a returned rename whose undo
   fails/blocks and a rename still in the kernel at exit; it no longer promises
   revocation of every observed late return (`design:19–23`; `exec:604–615,661–674`).
   Power loss may drop a marker entry, making COMPLETE non-qualifying. Arbitrary
   filesystem revocation and power-loss guarantees are not imposed by this review.
6. The previously unhandled readable temporary and live foreign start are now
   covered. The untraceable publication residual remains a start with no temporary
   on disk (`design:23–25`; `AI_READER_JOB.md:41`). **Unreadable/legacy or reboot
   evidence retains the declared conservative fallback accounting rule**, including
   the 30-second pending fallback (`exec:738–743,307–320`; `design:38`); that scope
   is not an exact-time proof for arbitrary damaged files or unavailable identities.

Declarations 4–6 are materially complete and accurate under those explicit
qualifications. Declarations 1–3 are answered in the separate Stage A record for
the same candidate. No bound-file prose edit is required here; any later edit
moves the package and must not reuse this attestation.

## Evidence, identity and remaining decisions

All **24 fields** below reproduce by independent metadata/hash arithmetic. The
digest is `ffba894e5a8c1ea9ed4d68f9287cbb75fc4e25e50e923dcd525a542d631a8ed8`.
The 16 bound-file hashes and command template were reconstructed from immutable
source blobs/literals without calling submitted package functions. Binary,
package-manifest and sandbox bytes were hashed; the CLI version is the saved
`codex-cli 0.159.3` value, not a new executed version probe. Set/key/delivery,
runtime, instructions and template are unchanged; executor, shared guard/watchdog
and bound docs moved. This is package binding, not a new network request or
empirical environmental isolation measurement.

The retained `2026-10-02_photo_suite_rev10_run.md` and all ten run files agree with
their byte counts/SHA256: exact HEAD `fbfb7db`, empty pre-run photo status,
20:56:07–21:29:54 UTC on 2 October. Main suite exit 0: 255 tests in 2,024.525
seconds, OK with five WordNet skips; the separate build environment supplied those
five checks, 0.663 seconds, OK, exit 0. There are 250 non-skipped main tests plus
the five separately run checks, not 260 distinct tests. Reader Rev10 contributes
one method with two subtests; retained Rev9 has four and Rev8 eight. This verifies
retained implementer evidence; Codex did not execute those tests.

The earlier pre-commit disclosure remains **one identified STOPPED observation plus
one unidentified failure**, cause unresolved. Nonrecurrence in the retained run
does not resolve either cause or show that they were the same event. No false
promotion, answer retry or additional gate follows from that disclosure alone.

## Question 3 — separate attestation and authority

This record contains one favourable qualification attestation. Stage A has its own
record and block. The strict go guard still requires this immutable record's
commit/path/hash, ancestry and dates, all 24 attested/re-derived/current fields
and separately dated owner words; the negative list remains a supplement to that
positive exact-match requirement. No AIREADER_GO file or owner approval is created.
Only an authorized completed job meeting the frozen empirical gate can qualify
the reader for the later audit; that audit and Stage B retain their own gates.
Row 19, earlier bank/text reviews and prior exposure disclosures are unchanged.

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "favourable",
  "reviewer": "Codex (GPT: R052 Entropy paper; native 01a0d19e-2127-7051-9a61-6db771088559)",
  "date": "2026-10-02",
  "reviewed_commit": "fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030",
  "package": {
    "ai_reader_qual_set.json_sha256": "27a40db056f377cfdc308640668bd8c705a4312b974cc1f455efb2ce04302302",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "f79e0bbf524d943691755401b33583dcca8e4a13c3e7066ea2273d7451d691d8",
    "ai_reader_exec.py_sha256": "f2e3e0e57eee40f8c34fec065eed8ec72e05eb4be8f40641d6a52cac7b15271b",
    "ai_reader_score.py_sha256": "c66e6183f41a48dd9ac6aa2d15d5d952a5a0f0b5c15d842f594c11bf91f0aeaf",
    "ai_reader_runtime.py_sha256": "96235ea8e276b49ee671437776ee45d49a0249db70ce69b17849881fd4cac89e",
    "ai_reader_journal.py_sha256": "e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907",
    "ai_reader_key.py_sha256": "e063c7ceb08d39ac028e418857a612797516129ed1aa1e96280e22902d660c8f",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "6153bb6fafc63f64f92fee8654cb78cdfac4d6652e31261844d7ac35c2848cdc",
    "AI_READER_JOB.md_sha256": "977742e5cf00b4ced9d6ce60d17d44e6630e02f0adfe993b03d819b33e4a2a14",
    "AI_READER_DESIGN.md_sha256": "3b5381a37e46a30eee267f4e217a9701c34c34e39f8804327ae5525ebaea2a08",
    "stage_a_guard.py_sha256": "71031f606240c0ca93e41f22ceddcf9a78d1968a356803d00fff18b36749db70",
    "enforce.py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
    "memprobe.py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
    "stage_a_watchdog.py_sha256": "7a686c76fea6f9be8f21724d3690847c752a95b78f6389bc2792a9016a15736d",
    "codex_realpath": "/opt/homebrew/Caskroom/codex/0.159.3/bin/codex",
    "codex_sha256": "4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878",
    "codex_package_json_sha256": "8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121",
    "cli_version": "codex-cli 0.159.3",
    "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
    "command_template_sha256": "031e84919341e045907acbc09a210af51449a9d6c249f0bba40d9238469058ba",
    "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
    "package_digest": "ffba894e5a8c1ea9ed4d68f9287cbb75fc4e25e50e923dcd525a542d631a8ed8"
  }
}
-->

# Row-20 OS-bridge supplement revision 2 — restart decision and persistence

Date: 3 October 2026 (Phoenix; 4 October UTC filename). Reviewer: Codex,
`GPT: R052 Entropy paper`.
Brief: Unimog `9355b2d0e1c4a67525a5fe2185992dc61e0790e3`,
`prompts/2026-10-04_codex_r052_reader_rev16_and_supplement_rev2_review.txt`,
SHA256 `96c9315f8f8cd9857a02e8a30a136bfc02702a9ccf473093e16583a26354b092`.
Ownership: Unimog `2051fcd2`; handoff
`cb86da4f-24e8-51ac-8c49-42e44256c939` accepted before review edits and delegation.
This is one of two separate bounded re-reviews of the revision-15 records at
RSC `478196f`; prior accepted scientific and Stage A reviews remain closed.
Candidate: `369e517c57d266013eb8f2872d7cc7a6d0781e72`.
Execution identity: `79f6e25b6991f05ab94b8680cfee8654bc441cf5b73dcb6c8cdf91616aa53b1c`.
Other answer: [reader revision 16](2026-10-04_reader_rev16_codex_record.md).

## Verdict

**NOT FAVOURABLE to this exact supplement revision-2 package.** Ordinary
post-start restart is now terminal, missing exit-peak measurements persist
across sessions, admitted PASS is frozen, endpoint worker resumption is refused
and complete row21 comparison verification is present. One **P1** remains:
the restart's terminal recreation can fail, be caught as a non-veto stop entry,
and allow retained completed endpoints to regenerate PASS. The promised restart
decision still depends on its file write succeeding.

The separate carried output tree/ledger and accepted base Stage A remain
appropriate and closed. The supplement needs its own scoped owner go after a
favourable exact record. Neither the standing reader go nor the earlier four-
native go covers it. This record authorizes no forward or Stage B work.

## P1: failed terminal recreation does not independently stop admission

This is a **static source path**, not an executed fixture or observed run.
Consider an earlier post-start session with both endpoint records/commits and
DONE files durable, all mandatory worker peak readings present, but no admitted
PASS final: a controller crash before final, or a receipt/final failure with
the first terminal absent/lost. The ledger can correctly show 196 starts, both
new ids completed in one try and no open/interrupted try.

`SupplementController._supersede`, `stage_a_controller.py:1378–1381`, detects
the prior start and calls `_terminalise`, then unconditionally calls the base
superseder. `_terminalise:1359–1366` catches an Exception before terminal rename
and merely appends phase=`controller`, reason=`terminal write failed...` to
`rec['stops']`. It returns no failure indication or independent hold. This is
an explicit handled failure branch, not a claim about forged scientific data
or arbitrary filesystem corruption.

With that recreation failing before `SUPPLEMENT_TERMINAL.json` is visible:

1. The old final/receipt move aside (`1381` → base `546–554`). Supplement gates
   (`stage_a.py:1666–1712`) reject a terminal file or open/interrupted attempts,
   but do not reject the completed prior starts without that file.
2. Base `_run:624–631` skips both retained endpoint DONE files. No new forward
   or retry is needed to reach the new receipt worker.
3. `run_supplement_receipt:2043–2098` sees no terminal, accepts the completed
   single-try ledger/output/phase/comparison evidence, and can write PASS. It
   binds the new gates/receipt session but does not require endpoint sessions
   to equal that session.
4. `_report_ok:1404–1408` checks current receipt-phase stops, not the controller
   terminal-write stop. `_finalise:1445–1473` can therefore be provisional PASS
   and never try terminalization again. Its final PASS predicate requires an
   absent terminal and otherwise successful conditions, not absence of that
   restart failure. Row21's verifier likewise has no independent session-
   continuity/controller-stop veto for these valid retained comparisons.

Thus prior failed/interrupted work can acquire a new PASS final despite §R2's
one-session-from-first-start contract. A variant with missing instrumented DONE
can even launch that worker before `_never_resumed` refuses the repeated endpoint;
that guard prevents a repeated forward but not the promised no-worker continuation.

**Required narrow repair:** make the post-start restart decision fail closed
independently of terminal persistence. Abort/refuse before superseding/gates,
or enforce an independent stop state across dispatch, receipt and final admission.
A failed terminal write must not be an ordinary stop entry that PASS ignores.
Leave the accepted base Controller/Stage A policy unchanged.

Retain a meaningful no-forward fixture with completed carried ledger/endpoints/
DONE from a failed or crashed earlier session, terminal absent, and a **pre-rename
failure of this restart's terminal recreation write**. Assert no endpoint worker,
no regenerated PASS receipt/final, unchanged counters/results and correctly
carried/charged earlier clock. Keep ordinary crash/restart and missing-peak cases.
Current Restart fixtures delete the first terminal but let recreation succeed
(`tests/test_stage_a_supplement.py:535–562`); their passes do not cover this branch.

## Repairs and wording credited

The admitted PASS refusal is before base superseding (`1374–1377`); its fixture
checks final bytes unchanged. Successful restart terminal recreation stops all
endpoint workers after any prior start, including crash/hold/receipt failures.
In-session `_hold` and STOPPED `_finalise` terminalise. `_missing_measurements`
now spans all released workers over every session, closing the specific lost
native-peak route. `_never_resumed` rejects any started endpoint; native also
requires its instrumented commit from its own session before native load.

Workers and row21 verifier share complete `comparison_a`/`comparison_b` receipts,
revalidate reference/instrumented/native records, check frozen parent pins and
demand field-for-field regenerated equality. Each executed comparison receipt
is retained before its stop; (b) is legitimately absent when (a) stops first.
Parent pins are honestly limited to eight metadata hashes, total bytes and
reference checksums, not a whole-tree digest. Stage B retains its independent
parent-acceptance gate.

Criteria now state `Stage A.package_at_commit(HEAD)` refuses after supplement
code moves; accepted Stage A stays bound to `cc1d2cb`, internal identity
`1d017dcefd1e810df77a2e643a03b9ffbdcf01e711cf47cd3ae5290d6fd2c727`.
That internal identity is distinct from its identity-file package hash.
The criteria §5 INSTRUMENTED row still names the removed
`test_resume_reloads_and_never_replays`; replace the pointer with the current
no-resumption fixture. This stale pointer is not an additional admission blocker.

## Exact package, accounting and retained limits

Root reproduces all **six package fields** below and the identity self-digest,
checks its 15 declared source identity bindings (including opaque packet bytes)
and all 17 checked live bound files. Versus supplement revision1 only criteria
and identity package hashes move; the supplement plan, base plan, manifest and
budget are byte/hash-unchanged. The base Controller and shared guard/enforce/
watchdog policies are unchanged in this revision's diff.

Carry remains 194/193/1/194 starts/completions/failures/passes, 2,338.113973380568
seconds and 396,783,863 bytes. Two new starts produce 196/195/1/196 within the
200-start cap; combined row21 accounting is **196+1,856=2,052≤2,056**, without
adding parent194 again. Remaining storage is 676,957,961 bytes; the inherited
four-hour/1GiB/48GiB envelope, 44GiB stop and charged 60-second closure remain.
Four spare starts are not retry permission. Resource forecasts are implementer
estimates, not fresh measurements by this reviewer.

The exposed fixed-input sentry does not isolate OS causality, qualify all images
or edits, reproduce the 120 shams on the new OS, admit PILOT or approve Stage B.
Earlier finite Stage A, metadata/build and tolerance-nontransitivity qualifications
carry. This review supplies no new capture, comparison output or scientific result.

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

## Exact negative attestation

This records refusal and identity; the favourable release gate remains unsatisfied.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A-supplement",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-03",
  "reviewed_commit": "369e517c57d266013eb8f2872d7cc7a6d0781e72",
  "package": {
    "supplement_criteria_sha256": "1fe4f5a09d4c3bbbb1c2e60f46d6e3d1a456a74678286f00b5fe7f016927f999",
    "supplement_identity_sha256": "44b1e120783adf9ee85e17d133c0aff701be5002952e0a5606a39b24ba11b3ef",
    "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"
  }
}
-->

# Migration v16 repaired scripts — Codex re-review

17 October 2026. **CHANGE 2: P2 path containment and deployment-recovery verification.** R1, R2 and the P3 promotion fast path are repaired in the inspected scope. R3's first-pass complete-manifest checks are repaired, but a rerun can clear a failed after-proof without verifying the scientific clone. The original production test hook is removed; nested containment is still incomplete. No favourable migration literal is issued for these bytes. The owner's existing conditional go and the earlier favourable controls review remain intact.

## Scope and identity

Reviewed `workspace_demo/t1_access/chpc/migration_v16/` at RSC `aaf05deaa5ae60d18242624c4b62cdda85a9d27a`, against the complete brief `Unimog-Projects/prompts/2026-10-17_codex_r052_migration_v16_rereview.txt` at `c6f3ac4f51ca92f39175a45eb26ae37d91fa1e60`, SHA256 `34fc3da8e90743ee0feac351c9d6703f2712efbc7b9900fdd8642d04e597cc3a`. Read the repaired runbook, scripts and archive helpers, the prior review `reviews/2026-10-17_migration_v16_codex_review.md`, and relevant test/authority dependencies. Three bounded readers checked archive/transport, Mac promotion and rollover/drain/test coverage.

Ownership was committed at Unimog `1ceaaeed36524ce525e97973a2affaffcf380a7f`, then handoff `7496e330-52b9-5a34-831c-25b90a27a9bc` was accepted before review edits. Exact session: **GPT: R052 Entropy paper**, native `01a0d19e-2127-7051-9a61-6db771088559`. Paths and line numbers below refer to the reviewed `chpc/migration_v16/` bytes.

The migration is an administrative controller cutover: preserve the actual v15 state, promote the reviewed v16 controls to the controller clone, retain the scientific clone and running jobs unchanged, then obtain fresh receipts and a new qualification-specific pilot review before one new-order job. No test result here supplies the later pilot or scale-up literal.

## P2 — containment checks stop at roots, before the actual nested destinations

`remote_lib.sh:26–41` resolves the toolchain root and checks controller/job clone roots, gate/retired/archive/jobs/campaign roots and locks beneath it. It does not check `C/reviews`, `C/chpc` or every source/destination used by the bodies. A physical path for `C` does not establish the physical path for `C/reviews/new.md` when an intermediate directory is a symlink.

The clearest write path is `adopt_pilot16.sh:13–16,27–36`:

1. The review argument is restricted to a plain lexical `reviews/<name>.md`. This rejects `../` and additional slash components.
2. The earlier controls/adoption/qualification/drain/lock checks do not validate the physical review destination. The body never calls `inside "$C/$REC"` or checks the `reviews` parent.
3. If the clean controller worktree contains a committed `reviews` directory symlink to a writable directory outside the toolchain, and the new filename is absent, `cp "$TMPD/rec" "$REC"` follows that parent and writes there. A later `git add` refusal occurs after that copy. Clean git status is not a physical-path guarantee.

This is a **static conditional path analysis**, not a claim that this layout exists on Lengau or that a real adopter passes. No such test directory or write was created in this pass. The code's preconditions do not exclude the stated layout before the write. Deployment payload destinations at `deploy_v16.sh:73–77` have the related omission. `lengau_archive.py:41–53` rejects a final symlink with `lstat`, but that alone does not reject a symlink in an intermediate controller-source directory.

There is also a scope distinction the prelude must enforce: a controller alias resolving inside the scientific clone is still beneath `T`, so the current `inside` predicate accepts it. A later science-digest difference can report damage but cannot preserve the Never rule before mutation. This is part of the same containment repair, not a separate defect count. No such alias is claimed to exist on the real toolchain.

**Fix:** validate each actual authority source and mutation destination under its intended canonical scope, including the nearest existing parent for new paths. Check `C/chpc`, `C/reviews`, each payload destination and temporary sibling immediately before use. Reject symlink/special leaves or unexpected parent aliases that would redirect an operation. Require canonical controller and scientific roots to be distinct and disjoint, and prohibit mutation destinations in the scientific clone even when they remain under `T`. Apply the same rule to gate retirement sources/targets and chmod targets; a root check is insufficient for a changed leaf. Retain lexical filename restrictions, clean-tree checks, fixed production root/transport and private-copy-only test substitutions.

**Regression coverage:** `test_migration_v16.py:326–355` tests the whole controller clone outside the root, whole gate/archive directories and a gate member during archive construction. Its adoption-destination test moves the entire controller clone; it does not test an otherwise valid controller root with a nested `reviews` parent redirect. Add private fixtures for that nested parent, nested `chpc`/payload destinations, controller/scientific aliases within the root, and a gate member changed to a symlink after archive capture. Require refusal before copy/move/chmod and unchanged outside/scientific bytes. A late git or authority refusal is insufficient.

The original R4 marker-selected test hook is closed by removal. This follow-up concerns the new production path invariant and its missing nested checks; it does not revive the old environment-variable route.

## P2 — an already-deployed rerun clears an incomplete science after-proof

`deploy_v16.sh:58–59` takes the `same=1` branch when the six payload files already equal the controller's files. That branch skips the science before/after checks at `:72,83–86` and can reach `DEPLOY OK` after a prior post-commit failure.

An additional private check continued the existing suite's own after-proof fixture: a private post-commit hook removes the private job clone's `simulate.py`. The first deployment commits the controller and safely refuses completion with exit3 and `after-proof is incomplete`. An immediate rerun returns0, says `already holds exactly these v16 bytes` and prints `DEPLOY OK` while that science file is **still missing**. This is an executed private administrative countercheck, not a real job-clone modification. The ordinary31-test suite passes because it checks the first refusal, not this subsequent rerun.

The rerun is not making a new mutation, but its successful completion allows the operator to continue despite the unresolved integrity failure. The runbook requires explicit verified recovery after a refusal; the equality shortcut cannot silently supply it.

**Fix:** bind successful deployment completion to a durable complete science before/after proof and the deployed payload/HEAD. On retry, require that proof and verify the current science bytes against it, or retain an explicit hold pending verified recovery. At minimum every success path must require the complete current eight-file inventory. That minimum alone does not close the changed-byte case: preserving the pre-mutation manifest or equivalent trusted recovery evidence is necessary to establish unchanged bytes after a failure. Keep interrupted/failed proof evidence; do not rewrite the scientific clone or rerun fits to manufacture it.

Add retry cases after both existing post-commit fixtures: missing `simulate.py` and changed `analyze.py`. No rerun may report successful deployment while the prior after-proof is unresolved. This is the remaining R3 recovery gap, separate from the complete-manifest repair that now works on a fresh deployment.

## Disposition of the prior repairs

**R1 — CLOSED, subject to the path repair above.** `lengau_archive.py` defines mandatory v15 controller pins plus controls/adoption/budget/manifest/row22 helpers; captures whole gate and refit-job inventories; requires qualification, active review, HEAD and ledger; checks exact members and every digest against `COMPLETE`; and stages/verifies before atomic publication. Reuse verifies the complete certificate. `deploy_v16.sh:46–71` re-verifies immediately before controller mutation, matches the Mac-recorded archive digest and the archived HEAD/qualification/review. The qualification-only archive and self-consistent subsets no longer meet the required shape. The ledger is correctly a reference snapshot, not a live budget reservation.

`mac_archive.py:16–25,61–102,105–143` requires the exact six named files plus `SHA256SUMS` and `COMPLETE`, fixed identities, regular members, complete canonical checksums, budget digest and the Lengau digest. Staging leftovers, missing/substituted budget and extra/corrupt members refuse. The arbitrary sixth-file hole is closed. Independent focused private validator checks passed **8/8**.

**R2 — CLOSED.** `remote_lib.sh:49–88` checks process-inventory success and non-empty output, distinguishes no-match from filter failure, probes both existing controller lock files with checked shared nonblocking flock or same-file Python fcntl, and refuses unavailable/failed observations. `git_clean` checks command status. The Mac process scan is checked too. The runbook retains the coordinated admission/controller hold through the cutover: successful probes establish an instant, not a lock held over the migration. Workers and reapers are not stopped to obtain it.

**R3 — first-pass checks repaired; recovery gap above remains.** `remote_lib.sh:23,90–96` fixes eight science files, requires every file readable, checks the complete digest command and exact ordered 64-hex/name list. Preflight refuses an incomplete proof. Deployment `:72–86` obtains the complete before-manifest before its first controller write and a complete equal after-manifest before reporting UNCHANGED. The initial post-mutation refusal is safe. Its already-deployed rerun must also preserve that integrity hold until a complete proof or explicit recovery exists.

**P3 — CLOSED.** `promote_v16.py:143–178` performs archive, candidate/review/pin/history, live-state and exact adoption validation before the completed fast path. The new `--check` is no-write and succeeds only for a fully verified promotion. Mixed legitimate old/new states retain controls-last atomic replacement and explicit interruption handling. Deploy requires this check and committed promoted files before transport.

**Transport/composition:** no additional material defect established. `lengau.sh` builds one script containing the fixed prelude, literal archive helper, base64 payloads with Mac SHA256 and one body. Actual callers supply fixed variable names and generated numeric payload indices; `%q` protects values. `remote_lib.sh:99–104` checks decoding and digest before the staged payload is consumed. The pilot bodies refuse ordinary direct execution without the prelude. This sentinel is an accidental-direct-execution guard, not authentication of deliberately forged shell input. Real SSH/GNU-tool behavior remains a platform check, and successful decoding does not fix destination containment.

## Required live dry step and later gates

**After both repairs pass review, run the full read-only preflight first**, under the existing coordinated hold. `--local-only` is insufficient. It must establish actual SSH framing, process inventory, both real lock probes, path resolution, t1py/Python compatibility, archive-source availability, budget/qualification/e1 identity and the complete science digest list on Lengau's actual tools/filesystem. A missing lock, absent row22 helper, unsupported name or redirected path is a safe refusal to report, not permission to create authority by hand or bypass a check.

Then retain the existing staged sequence: archive with verified `COMPLETE`; Mac dry-run/promotion/commit; deploy dry-run and verified controller commit; fresh lock-held programme accounting; supported two-phase raise to 81000 while programme 100000 stays fixed; fresh whole-role refit/bank receipts; retire the exactly archived old review; **one** existing-job1 qualification-metadata call, no fit; stop on NOT QUALIFIED; package/commit the new evidence; obtain its new pilot literal; supported adoption; **one** first new-order job; separate actual-resource/scale-up review before refills.

Private tests cannot establish real Lustre flock/rename/chmod behavior or positive `--raise-cap`, `--qualify`, `--adopt-review`, `--adopt-scaleup` and actual remote commit. Full preflight is the first no-write compatibility observation. Staged archive construction then verifies its own controlled write. Later supported positive commands remain the authorized gated operations at their stated points, with refusal retained for inspection; do not run them early merely to make a test pass. No additional fit or routine owner-permission question is needed.

The Never list remains: no worker/reaper stop or restart, no scientific job-clone edit, no manual permission/qualification/ledger editing, no reviewed-byte change, no pilot fit, no old literal reuse and no second new-order job before scale-up. Rescue stays disabled. Migration does not release p80 or epoch2, and this review does not reconsider the separately active e2/p80 repairs.

## Verification and limits

The existing suite independently passed **31/31** on an outer-guarded private copy (222 seconds). Focused private Mac validator checks passed **8/8**. The additional retry countercheck reproduced the R3 recovery failure; the nested-path finding is static-only and has no claimed executed counterexample. Passing the existing suite does not cover those additional cases. Production migration sources remained unchanged against `aaf05de`.

The copied harness was unchanged; its documented two-line root/transport substitutions remained inside private test worlds. Outer Python write/process/socket and network/scheduler-command guards were additional checks, not an OS filesystem sandbox. The inspected shell destinations were private. The suite makes local commits in disposable clones and uses synthetic administrative metadata; no real positive qualification/adoption/cap/scale-up or scientific script execution was permitted.

Private reports: `/private/tmp/r052_migration_v16r_archive_transport_review_20261017.md`, `/private/tmp/r052_migration_v16r_mac_promote_review_20261017.md`, `/private/tmp/r052_migration_v16r_rollover_tests_review_20261017.md`. Focused Mac proof: `/private/tmp/r052_migration_v16r_mac_probe_20261017.py`. Suite log: `/private/tmp/r052_migration_v16r_suite_20261017.log`. Retry proof: `/private/tmp/r052_migration_v16r_resume_countercheck_20261017.py/.json`. These are administrative review artifacts, not scientific outputs.

Only this review file is owned in RSC. No package/live/controller/ledger/partition/manuscript edit, real remote/cloud/scheduler operation, numerical release, fit, model draw, worker/reaper action, worktree or push was performed. Foreign files and concurrent e2/p80 repairs were preserved. Source Claude/owner retain implementation, migration and dispatch. Return both repairs as exact bytes for reconsideration; the existing conditional switch-over approval remains conditional on that favourable review.

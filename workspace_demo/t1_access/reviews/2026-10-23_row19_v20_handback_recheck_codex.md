# Row 19 controls v20 hand-back: Codex repair recheck

23 October 2026. R052, synchronous recheck of repair RSC `865e9b69466e6b5d522132239fc718cf0095e758`, against the conditions in
`reviews/2026-10-23_row19_v20_handback_codex.md` (RSC `d3a56b4`), following candidate `a8cc1dd` and migration `7a3ec45`.
Paths below are relative to `workspace_demo/t1_access/`.

**F1, F2 and F3 are met. No new blocking finding.** The repaired candidate and migration satisfy the prior review's repair
conditions. This is a code/package review, not an operator adoption record or an instruction to execute the migration.
Only this review file was changed; local test worlds were temporary. No live ssh, AWS, deployment, activation, disposition
or other live action was performed. No RSC commit or push was made.

## F1 — met: historical partition evidence fails closed

`chpc/candidate_v20_handback/aws_ec2/prod_authority.py:264` now permits OPEN only after authenticating the partition references
it must traverse without finding a terminal close. Each nonempty reference must contain a path and 64-character digest
(`:280`); its target must be a regular file and not a symlink (`:287`); its bytes must hash to that digest (`:289`); and those
bytes must decode/parse as a JSON object with a string schema (`:292`). Any failure returns a refusal (`:295`). An authenticated
schema-3 reference returns CLOSED immediately (`:298`), so later references cannot reopen EC2. `closed_problem()` also turns
controls-read exceptions into refusals (`:305`).

The rerun passed D9 and D9a–D9i (`chpc/candidate_v20_handback/test_v20_handback.py:362`). With v21 currently pinning e2, damaged
historical e3 evidence refuses through the detector, exclusion, qualification and production gates: missing file, invalid
JSON, e2 substituted at e3's path, symlink to intact e3, appended byte and directory. The restored e3 remains CLOSED. Additional
checks cover a malformed reference and missing historical e1 even in a history without a close (`:385`).

I also ran 11 supplementary temporary-world probes using the unchanged detector functions: six hash-matched malformed inputs
(invalid JSON, array, null, missing schema, non-string schema, invalid UTF-8), a genuinely unreadable e3 file, an injected read
failure, invalid controls-history shape and two malformed nonempty references. All refused. Matching the malformed inputs'
hashes deliberately exercised parsing/shape checks beyond the digest-mismatch branch used by D9b.

Keeping controls `4e64982b` is sound. The controls, both pinned candidate controllers, e3, builder and promoter are byte-equal
to the prior-reviewed versions. The builder adds only `MAP` members to controls pins (`chpc/candidate_v20_handback/build_v20.py:186`,
`:193`); the authority is a separate `MAC` row (`:54`, `:201`). Its new digest is carried by the deterministic promotion map,
and the migration authenticates both map and source before importing/promoting them (`chpc/migration_v20/v20_package.py:30`,
`:106`, `:155`; `chpc/candidate_v20_handback/promote_v20.py:73`). Independently recomputed identities:

- Controls: `4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c`.
- Mac authority: `e1381d6811a517c3ebae09c1889ed7dafda97431842760ca963e951041b85c87`.
- Promotion map: `79c78ea737f3123eb864185d5c73d35cdd63a1159e60199704933c8f690c4945`.

The controls ADOPT literal therefore retains its identity; the repaired authority is authenticated through the updated package.

## F2 — met: frozen migration rehearsal, including the canonical close

The unmodified `chpc/migration_v20/test_migration_v20.py` reran **39 passed, 0 failed (312 seconds)**. Its starting controller
state comes from frozen commit `add8586`, with each member and all 19 controls pins checked (`:86`, `:206`, `:216`). EC2
bookkeeping is constructed from the pinned inventory fixture (`:614`). All 37 v19 test functions remain; the two additions
are `t_close_cli` and `t_close_route`.

The harness verifies that private production copies differ on exactly three tagged lines: root, transport and synthetic
operator-record pin (`:452`, `:465`). Transport becomes local `bash -s`; fake ssh/scp always refuse (`:256`, `:457`, `:593`).
The close runs the real `verify3` and `activate` script bodies (`:314`) with a storage-path remap (`:334`). The candidate CLI
holds the actual exclusive plan lock across `activate()` and immutable proof publication
(`chpc/candidate_v20_handback/row19_partition.py:1026`, `:1033`, `:1043`). The production close invokes verify3, activation and
post-publication validation in that order (`chpc/migration_v20/close_e3.sh:41`, `:44`, `:46`).

The positive route exercises preflight, archive, promotion, committed deployment, pre-close receipts, canonical e3 proof,
post-close receipts, rollover, packaging and pilot-adoption script, including reruns and preservation of running-job state
(`chpc/migration_v20/test_migration_v20.py:1000`). The proof is checked for canonical mode, epoch 3, closed status, controls v20
and the exact e3 digest (`:1067`). Real admission gates demonstrate the missing-activation hold before close (`:1054`) and the
missing-review hold after rollover and before the new pilot review (`:1085`).

Refusal tests cover pending E2Q3, pending zero-coordinate Q2, launched attempt, stale inventory, changed retained set, missing
coverage, held plan lock and controls not pinning e3, with no proof written (`:1582`). Route tests additionally cover a wrong
pre-existing proof, preserved unchanged, and failure immediately after successful proof publication followed by an idempotent
retry that validates and retains the same proof bytes (`:1613`, `:1633`). Existing archive, containment, science-preservation
and interrupted-deployment tests all passed.

The `close_v20.sh` SIGPIPE repair is correct: `grep -F ... >/dev/null` consumes the complete pipe under `pipefail` (`:22`).
Besides the rehearsal, I ran that actual repaired pipeline five times with 200 KB output; all returned zero.

Rehearsal limits remain explicit: scheduler receipts and regenerated pilot qualification are synthetic; the supported pilot
adopter is simulated (`test_migration_v20.py:318`, `:372`, `:682`). This qualifies the migration bodies and the real canonical
close; it does not certify a live scheduler run or a real new pilot adoption. These limits do not leave F2 outstanding.

## F3 — met: frozen negative fixtures; live close-check observed separately

The fixture hashes to `03cb443304854c0988e2b55aee270d31ec0daf704bef0f835f93e02a71807bfb`. B0 checks both its identity and seal,
and its pending E2Q3/Q2 state (`chpc/candidate_v20_handback/test_v20_handback.py:180`). B5's inventories derive from that fixture
(`:188`, `:244`, `:252`). D11–D13b construct their ledgers from the same frozen attempts and independently exercise pending
owners, successful terminal disposition, stale/non-current inventory and Q2 alone still pending (`:398`, `:405`, `:412`, `:419`).
The live close-check is printed inside a separate observation block and is not an assertion (`:421`); this rerun observed MET.
The candidate suite's other local-snapshot comparisons remain snapshot-based; the repaired negative fixtures no longer depend
on movable live disposition bookkeeping.

## Verification and repair scope

- Candidate suite, unmodified, bytecode writes disabled: **77/0**, including its live-tree integrity check.
- Migration rehearsal, unmodified, bytecode writes disabled: **39/0**.
- Static checks: **26/0**. Executed in memory with only the live `__pycache__` deletion loop disabled to preserve read-only scope
  (`chpc/migration_v20/static_check_v20.py:104`); every check remained intact.
- Supplementary detector probes: **11/0**; large-output repaired-pipeline checks: **5/0**.

The repair introduces no change to the previously reviewed ownership declaration, scientific code, planner, activation logic
or controls history. The production behavior changes are historical-evidence refusal and the shell-pipeline correction.
Candidate and migration paths still match HEAD after testing. No new blocking regression was found. The prior review's
release-consumer re-pinning requirement and stated regression-suite limitations remain; this recheck does not certify numerical
release or enlarge funding. The RUNBOOK's operator record and execution ordering remain necessary operational steps.

VERDICT: FAVOURABLE

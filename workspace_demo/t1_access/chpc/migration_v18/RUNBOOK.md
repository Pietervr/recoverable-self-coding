# v17 -> v18 migration (controls v18: the node-failure disposition) - RUNBOOK and SCRIPTS, BUILT AND TESTED, NOT EXECUTED

Written 20 October 2026 (R052, Claude, bounded job). Nothing in this folder has been run against the live tree, Lengau or AWS.
It is the materialised v18 package Codex's controls review asked for: `reviews/2026-10-20_v18_nodefail_codex_review.md`
("Controls binding and migration ruling": "Parameterising the v17 implementation is acceptable; a new materialised v18 migration
package and scripts review are still required. Do not run v17 scripts against substituted identities or invent a v17.1/data-only
bypass."). Every script here is the `migration_v17` counterpart re-pointed at v18 and keeps every rule Codex's migration_v16 and
migration_v17 reviews established; the per-file differences are in `v17_to_v18.diff`.

## What is authorised and what is not

**Nothing yet.** Two separate FAVOURABLE Codex verdicts are needed before step 1:

1. **The controls verdict on the exact CHANGE-1 package** (`chpc/candidate_v18_nodefail/`, DESIGN_v18.md s.0): candidate controls
   `452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b`, with the literal

       ADOPT row19-screen-controls sha256=452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b version=18

   The reviewed `80214d80` received CHANGE 1 and no literal; it is never reused.
2. **The scripts verdict on this folder at its exact commit**, after the record pin below is filled in.

**The record pin.** `v18_package.py` carries ONE line tagged `@record`, PENDING in these bytes:

    REC, REC_SHA = None, None   # @record PENDING: ...

While it is PENDING every Mac gate (preflight, check-promoted, payload, compare, commit-paths) refuses, so nothing can be archived,
promoted or deployed. After the controls verdict, that one line is set to the committed Codex record and its SHA-256 (for example
`REC, REC_SHA = "reviews/2026-10-2x_v18_nodefail_codex_rereview.md", "<64 hex>"   # @record ...`), committed, and the scripts
review covers those final bytes. The record is then deployed to the controller clone as payload 1 and named by the version-18
adoption record.

Not authorised by anything here: a fit, a refill, rescue, an EC2 qualification instance or production, a release, the p80 release
consumers, any scale-up beyond the existing `scaleup_refit_v16.json`, or any new partition, data, EC2 code or activation.

## The package and the scripts

`chpc/candidate_v18_nodefail/` (the controls package, pinned by `v18_package.py` `PACKAGE`): controls `452b82df`, promotion map
`380871da`, `build_v18.py` `f8ced83a` (REVISION 2: the base-first archive branch), `promote_v18.py` `964b101b` (NEW, the
`promote_v17.py` REVISION 2 pattern), `row19_screen_nodefail.py` `f6afeb10`, `row19_nodefail_capture.py` `84d52bdf`,
`row19_screen_status.py` `4710544a`, `row19_screen_admit.py` `e2260765`, the retained captured node document
`evidence_row19_screen_refit_54.nodefail.json` `730ea262`.

| Step | Script | Where | Writes |
|---|---|---|---|
| 1 | `preflight_v18.sh` (Mac half: `v18_package.py preflight`) | Mac + Lengau | nothing |
| 2 | `archive_v17.sh` (`lengau_archive.py`, `mac_archive.py`) | Lengau, then Mac | the two archives, the Mac copy of the Lengau `SHA256SUMS` |
| 3 | `chpc/candidate_v18_nodefail/promote_v18.py` | Mac | the 4 promoted paths, the controls, the v18 adoption record |
| 4 | `deploy_v18.sh` | Mac -> Lengau | one controller-clone commit (7 files), the deploy proof |
| 5 | `receipts_v18.sh` (+ `check_v18.sh`, `receipt_check_v18.py`) | Mac (+ Lengau read-only) | the refit and bank receipts |
| 6.1 | `lengau.sh rollover_pilot_v18.sh` | Lengau | moves the v17 review to `gate_retired/` |
| 6.3 | `package_qual_v18.py` | Mac | `chpc/qualification_v18_<qsha8>/` |
| 6.4 | `lengau.sh adopt_pilot18.sh --file reviews/<record>.md` | Lengau | the record commit in the controller clone, the new gate review (by the adopter) |

There is NO epoch-activation step and NO EC2 cycle: v18 changes no partition, data or EC2 code. Epoch 2 stays active; steps 1, 2,
4, 5, 6.1 and 6.4 re-verify that `activation_e2.json` is THE canonical activation of e2 `48cea639` under the current adopted
controls (v17 before the deploy, v18 after it: v18 keeps the v17 entry byte-identical and pins the same partition, so
`row19_partition.activation_problem` accepts the v17-made proof).

Shared parts: `lengau.sh` (the one Mac -> Lengau transport, `# @transport`), `remote_lib.sh` (the Lengau prelude: the fixed
toolchain root `# @root`, containment, drain, lock, git, evidence allowlist, science digest, the v17/v18/deploy/activation and
node-document checks, `literal_in`), `lengau_archive.py`, `mac_archive.py`, `v18_package.py`. Tests: `test_migration_v18.py`;
results: `test_results.txt`.

Where commands run: on the Mac every command runs from `workspace_demo/t1_access`; on Lengau `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`
and controller commands run from `$T/rsc_screen_ctl/workspace_demo/t1_access` through `$T/t1py`, every Lengau part through
`lengau.sh` (`ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s`). The direct bodies run as
`bash chpc/migration_v18/lengau.sh rollover_pilot_v18.sh` and `... adopt_pilot18.sh --file reviews/<record>.md`; run alone they
refuse. Every step refuses rather than overwrites and is safe to re-run; partial evidence is never overwritten or removed.

**Never:** stop, restart or edit a running refit, bank or EC2 worker or reaper, or the job clone `rsc_screen`; set any
permission, qualification, activation or inventory by hand; edit a ledger, budget file, proof, claim, plan or the captured node
document; change reviewed bytes after review; delete or relabel e1/e2 or their activation proofs or any older archive; rerun a
pilot fit, repeat `--qualify` to fish for a pass, or reuse an old ADOPT or pilot literal (`80214d80`, `8fdbf48e`, `2c7a7ef1`,
`3c605514`); revert the controls.

## The coordinated hold, and the running refit jobs 47-56 (except 54)

**The hold.** From step 1 until the new pilot adoption (6.4) the refill scripts are not invoked, the slot watcher is stopped,
and no controller command is started by hand - no admission, status, receipt, settlement, capture or EC2 authority command other
than the ones these steps run. Every Lengau step re-probes the drain (process inventory - `CTLPAT` now also matches
`row19_nodefail_capture` - and both lock files) immediately before it writes. Nothing is stopped to obtain it.

**Running jobs keep running, untouched.** Refit jobs 47-56 (PBS 7551252-7551261) were admitted under v16/v17; job 54 ended F/265
with its node lost and is settled (its 22 no-status coordinates return to the planner once v18 dispositions it). A refit job
runs entirely from the scientific clone `rsc_screen`: `row19_shard.py job-start` checks only the manifest's code pins and the
ledger reservation, the workers write records and timings to the root, and `job-end` writes the runner's end into the ledger.
None of that reads the controller clone, the controls or the gate, and the migration changes none of what it reads (the job
clone is proved by its complete eight-file science manifest before and after the controller commit; the tests also prove the
job files, ledger and plans unchanged through the deploy). So a queued job starts and a running job finishes exactly as under
v17, whether its event falls before, during or after the switch.

**Settlements** (the v17 rule). A finished job's ledger entry is settled through the unchanged
`programme_gate.py settle --manifest chpc/row19_screen_manifest.json -- $T/t1py chpc/row19_ledger.py ... settle ...` in the
controller clone, which first requires `lineage_problem() == ''`: it passes under v17 before step 4 and under v18 from
DEPLOY OK on; during the controller commit window it would refuse (and the drain refuses a settlement in flight). So settlements
are deferred from step 1 to DEPLOY OK and may then run at a step boundary - never concurrently with a step script. Until
settled, a finished job's reservation stays counted as live (the conservative side). Settlement does not depend on the pilot gate.

**Records and dispositions.** Records bind the manifest code pins and task identities, not a controls version; the step-5
generation-18 receipt observes and verifies every record of the running jobs exactly as the v17 receipts did. Job 54's
node-failure disposition is computed by the v18 status view from the retained node document and recomputed by the v18
admission; any OTHER node loss needs its own captured, reviewed evidence (receipt_check_v18 refuses a second node disposition).
From step 4 until step 6.4 every NEW refit admission holds (generation 18 receipts and the regenerated pilot are required).

## 0. Preconditions

| Gate | Check | Abort if |
|---|---|---|
| Controls | the committed Codex record carries the literal for `452b82df`, and `v18_package.py` pins it (record line, sha256) | PENDING, other bytes, no literal in HEAD |
| Package | controls `452b82df`, map `380871da`, builder `f8ced83a`, promoter `964b101b`, the four sources and `730ea262` (`v18_package.py` PACKAGE; `promote_v18.py --check`) | any byte differs |
| Scripts reviewed | a committed FAVOURABLE Codex record on THIS folder at its exact commit (with the record line filled), and `python3 chpc/migration_v18/test_migration_v18.py` passing on those bytes | no record, or the scripts changed after it |
| Hold | the coordinated hold above is in force | any admission during the hold |
| Node document | `$T/jobs/row19_screen_refit_54.nodefail.json` is still exactly `730ea262` | missing or changed (never recapture by hand: report) |
| Epoch 2 | `activation_e2.json` is the canonical activation under the adopted v17 | anything else |

## 1. Full live read-only preflight (Mac and Lengau)

`bash chpc/migration_v18/preflight_v18.sh` (no option). `--local-only` runs the Mac half alone and does not satisfy this step.
It refuses unless: **Mac** - the package and record above, the live controls/adoption the committed v17 `9ea4e727`/`61ca680e`,
each promoted path at its v17 bytes or absent, `promote_v18.py --check` OK, e2 `48cea639` committed, the Mac
`qualified_refit_job1.json` `8fdbf48e` and its pilot record `75bb5010` committed, the budget committed, no Mac archive / Lengau
SHA256SUMS copy / staging, the Mac drain and the EC2 authority lock free; **Lengau** - tools printed (t1py >= 3.6), drain and
both locks, every path contained, the controller clone clean (`ctl_clean`) at the adopted v17 (controls, adoption, the two
replaced files, the v17 controls and pilot records committed) with neither new v18 path, the gate at `8fdbf48e` with an active
review bound to it, the v17 retirement target, archive `v17_before_v18`, staging and `v18_deploy_proof` absent, epoch 2
canonical, the node document `730ea262`, no pending budget phase and the ledger cap 81,000, every archive source present
(`lengau_archive.py inventory`), the eight-file science digest printed. Expected: `mac preflight OK`, `lengau tools: ...`,
`drain observed`, `paths resolved`, `activation proof ...: ... activation_problem ''`, `epoch 2 active ...`,
`archive sources complete`, `lengau preflight OK`, `PREFLIGHT OK`.

## 2. Archive the adopted v17 state (Lengau, then Mac)

`bash chpc/migration_v18/archive_v17.sh --dry-run`, then `bash chpc/migration_v18/archive_v17.sh`.

a. **Lengau** `$T/archive_screen/v17_before_v18/` (`lengau_archive.py`), read-only, exactly: `ctl/HEAD.txt`; `ctl/<path>` for every
file the adopted v17 entry pins, the e2 partition, the e1 declaration, the v17 controls/adoption/admission/status/designated/
budget/manifest, the two row-22 helpers, the v17 controls record `48b9cf05` and the v17 pilot record `75bb5010`;
`ctl/untracked/<path>` for the three pinned evidence files; the WHOLE gate (`qualified_refit_job1.json` `8fdbf48e`, the active
review, `scaleup_refit_v16.json`, every receipt and PBS copy) with `INVENTORY.gate`; `jobs/row19_screen_refit_*` with
`INVENTORY.jobs`, which MUST retain `row19_screen_refit_54.nodefail.json` at `730ea262`; the ledger reference copy;
`ec2/activation_e1.json` and `ec2/activation_e2.json`; `SHA256SUMS`; `COMPLETE` (schema, SHA256SUMS digest, HEAD,
qualification, review, budget, node_evidence). Staged, verified in full, published by one rename.

b. **Mac** `chpc/results/archive/row19_screen_v17_before_v18/` (`mac_archive.py`): exactly the 8 members of `build_v18.ARCHIVE`
(admission `c3960464`, status `a9f9180b`, controls `9ea4e727`, adoption `61ca680e`, qualification `8fdbf48e`, pilot record
`75bb5010`, the committed budget, the node document `730ea262`) + `SHA256SUMS` + the JSON `COMPLETE` naming the Lengau archive;
then the Lengau `SHA256SUMS` text is kept beside it as `...v17_before_v18.lengau_SHA256SUMS.txt`.

Expected: `archive built ...`, `Mac archive ... verifies: 8 members ... build_v18.archive_problems: []`, `ARCHIVE OK`. Retry rules
as in v17 (a verified archive is accepted, anything partial refuses and is kept; a Mac half that failed after the Lengau half is
built by a re-run).

## 3. Promote v18 on the Mac

    python3 chpc/candidate_v18_nodefail/promote_v18.py --dry-run --review <REC>
    python3 chpc/candidate_v18_nodefail/promote_v18.py --review <REC>

It resolves the authenticated v17 base first (the live exact v17, else only the verified Mac archive), checks the candidate, the
record literal in HEAD and the archive, copies the two new files, the status view, the admission and LAST the controls, then
writes the version-18 adoption record. Commit atomically the paths printed by `python3 chpc/migration_v18/v18_package.py
commit-paths` (the 4 promoted paths, the controls, the adoption record, the Mac archive directory and the Lengau SHA256SUMS copy):

    git -C ~/Recoverable-Self-Coding add <those paths, each prefixed workspace_demo/t1_access/> && git -C ~/Recoverable-Self-Coding commit -F <msg> -- <the same paths>

Then `promote_v18.py --check-promoted --review <REC>` must exit 0 and `v18_package.py check-promoted` must print
`mac v18 promotion OK`. From here to step 5 do not run the Mac status or receipt commands (Mac v18, Lengau still v17).

## 4. Deploy to the controller clone (Lengau)

`bash chpc/migration_v18/deploy_v18.sh --dry-run`, then `bash chpc/migration_v18/deploy_v18.sh`.

Mac: `check-promoted`, the drain, and the promoted tree's own authority / lineage / controls / designated / partition checks
(schema 2, epoch 2, 3,274 owned, version 18). Payload (7 files, in order): the controls record, `chpc/row19_screen_nodefail.py`,
`chpc/row19_nodefail_capture.py`, `chpc/row19_screen_status.py`, `chpc/row19_screen_admit.py`, the controls, LAST the adoption.
Lengau, immediately before the change: drain; the archive certificate verifies and is the one the Mac archive names; clean clone
at the adopted v17, at the archived HEAD, neither v18 path present; gate qualification and review = archived; epoch 2 canonical;
the node document `730ea262`; every payload compiles/parses under `$T/t1py`; a complete science before-manifest. The deploy proof
`$T/archive_screen/v18_deploy_proof/` (`science_before.sha256`, `intent`) is written before the first controller write; ONE
commit of exactly the payload paths; the after-manifest must equal the before-manifest before `DONE` is written and read back.
After: clean clone, authority/lineage/controls `''`, designated `''`, partition schema 2 epoch 2 owned 3,274, v18 adopted,
**epoch 2 still the canonical activation under v18**, the node document unchanged, `IDENTICAL` local vs remote (the 19 v18
pins, controls, adoption, e2 partition, record). Expected: `payload: 7 files ...`; `deploy proof written before any controller
change`; `science bytes UNCHANGED (8 files ...)`; `activation proof ...: ... made under controls version 17, accepted under the
current version 18; activation_problem ''`; `epoch 2 STILL ACTIVE ...`; `IDENTICAL`; `DEPLOY OK`. Re-run, HOLD and dirty-clone
rules exactly as v17. From DEPLOY OK settlements may resume at step boundaries.

## 5. Fresh generation-18 role receipts (Mac, read-only Lengau check)

    bash chpc/migration_v18/receipts_v18.sh

Mac `check-promoted` and drain; Lengau `check_v18.sh` (v18 adopted, `DONE`, epoch 2 canonical, node document in place); then the
refit receipt `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`
(it must exit 0: fresh, production, zero alarms - the v18 status view fetches the node document and dispositions job 54),
`receipt_check_v18.py` (generation 18 = latest 18 with controls `452b82df`, designated view, EC2 binding with exactly
`activation_e1.json` and `activation_e2.json`, no HOLD/STOP/problems, job 54 a node-failure disposition on `730ea262` bound as
`bound.node_evidence.54`, no other node disposition), then the bank receipt. Expected: `RECEIPT OK ...`, `V18 RECEIPTS OK`. Any
alarm stops the migration for review. An "EC2 authority inventory is ... s old" alarm (only raised with a live attempt) is NOT
cleared here: it needs the separately reviewed EC2 cycle route.

## 6. Pilot qualification rollover - ONE metadata-only regenerated qualification of the existing job 1, a NEW hash, no fit

Under v18 the verifier stamps generation 18 and `generation_problem` requires it, so the v17 qualification `8fdbf48e` and its
adopted review stop satisfying the refit gate.

1. `bash chpc/migration_v18/lengau.sh rollover_pilot_v18.sh` - requires v18 adopted (`DONE`), epoch 2 canonical, the drain, the v17
   archive certifying byte-identical copies of the active review and `qualified_refit_job1.json` (`8fdbf48e`), the review bound
   to `8fdbf48e`; moves it to `gate_retired/review_refit.v17_qual8fdbf48e_max100.json` (read-only). `scaleup_refit_v16.json` is
   not touched. Re-run: `already retired (verified)`.
2. ONE call: `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1`.
   Expected `QUALIFIED: refit job 1 (<qsha16>) copied to the gate`. A `NOT QUALIFIED` stops the migration; never repeat it.
3. `python3 chpc/migration_v18/package_qual_v18.py --dry-run`, then without: `chpc/qualification_v18_<qsha8>/` (qualification,
   verifier, the published and named receipts, both archives' `SHA256SUMS`), refusing `8fdbf48e`/`2c7a7ef1`/`3c605514` or a
   non-generation-18 verifier. Commit it with explicit paths; route it to Codex for
   `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`.
4. After Codex's committed record: `bash chpc/migration_v18/lengau.sh adopt_pilot18.sh --file reviews/<record>.md`. It refuses
   while a review is active, without the retired v17 review, while the gate holds `8fdbf48e` (or `2c7a7ef1`), without epoch 2
   canonical, without the drain, when the record lacks the literal for EXACTLY the gate's qualification, or on containment; it
   commits the record in the controller clone and runs the supported `--adopt-review <record> --max-job-number 100`. The literal
   check is `remote_lib.sh` `literal_in` (sed piped to `grep -xF ... >/dev/null`: NO `grep -q` in a pipe under pipefail - the
   9df2a1f fix; a > 16 KB record is tested). Expected: `adopt_pilot18 complete`.

## 7. Refills resume

With the new pilot adopted, the existing scale-up adoption in force and a fresh receipt (at most 2,700 s old) each time, refills
resume inside refit+S 81,000, programme 100,000, serial max_run 10 and job ceiling 100, as under v17. The hold ends here.

## Operator sequence (summary)

(controls verdict -> record line filled + scripts verdict) -> hold -> `preflight_v18.sh` -> `archive_v17.sh` -> `promote_v18.py`
(+ Mac commit) -> `deploy_v18.sh` (settlements may resume) -> `receipts_v18.sh` -> `lengau.sh rollover_pilot_v18.sh` -> ONE
`--qualify 1` -> `package_qual_v18.py` (+ commit) -> Codex pilot literal -> `lengau.sh adopt_pilot18.sh --file <record>` -> refills.

Still separate (not this migration): re-pinning `row19_screen_release.py` CONSUMER_FILES / the `release_p80` adoption before any
numerical release (they bind the admission and controls), the E2Q1 route, rescue.

## Tests (private copies only, FROZEN fixtures)

`python3 chpc/migration_v18/test_migration_v18.py` (`-k <substring>`, `--keep`). Unlike the v17 suite - which seeds its worlds
from the LIVE tree and can no longer run end to end now that the live tree is v17 - every world is seeded from git objects at ONE
pinned commit (`FIXTURE_COMMIT` RSC `6d82a73`, the adopted v17 Mac tree), each file checked against its pinned hash (`FROZEN`) or
the frozen v17 controls entry; only the immutable candidate package is read from the working tree (pinned by `PACKAGE`). The
fake Lengau root reproduces what the v17 migration left (controller clone at v17 with the three untracked evidence files, gate at
`8fdbf48e`, retired v16 review, both activations - `activation_e2.json` generated by the real frozen `row19_partition` under the
frozen v17 controls - the v17 archive and deploy proof, the node document `730ea262`). The production files are copied with
exactly three tagged lines substituted (`@root`, `@transport`, `@record`); ssh/scp always refuse; the fake `t1py` simulates only
`--adopt-review`; the two receipt commands are stubs reached through a `python3` wrapper on the Mac PATH (the promoted status
view stays in place). Covered: the positive route with every re-run (and the running-job state, gate, activation and node
document unchanged through the deploy), the restricted git/flock route, the PENDING record pin, package-identity refusals,
Mac/Lengau preflight refusals, archive completeness/interruption/retry/subset/strict-verify, promotion interruption and the
archive-only base after promotion, deploy refusals (archive, uncommitted, broken activation, changed node document, drain incl.
a settlement or capture in flight, science before/after, copy/commit failures, proof binding, payload compile, early v18 path),
containment (controller, archive, gate member, ec2 dir, node document, nested redirects, temp sibling, science alias, gitfile),
the evidence allowlist, receipts (alarm, generation 17, no e2, missing/other/second node disposition, bank failure, retry,
Lengau check refusals), rollover, package and adoption (including the large-record literal). Results: `test_results.txt`.

Untested on the Mac: real ssh and Lengau's real tools (emulated by restricted CLIs only); the real refit/bank receipts,
`--qualify` and `--adopt-review` (stubbed or simulated); the real controller-clone commit on Lengau.

## Open choices for Codex (this scripts review)

1. **The record pin as a tagged PENDING line** (`v18_package.py` `@record`), filled after the controls verdict and covered by the
   scripts review of the final bytes. Alternative: pass the record as an argument to every step (it would then be bound only by
   its literal, not by its exact bytes).
2. **No EC2 cycle in step 5.** v18 changes nothing EC2-side; the receipts read the installed inventory as it is. A stale-inventory
   alarm (only with a live attempt) stops the migration rather than being cleared here.
3. **`receipt_check_v18.py` requires job 54's disposition and refuses any OTHER node disposition** during the migration.
4. **Archive members added for the ruling's "retain this captured node document"**: the node document is a mandatory member of
   both archives (and certified in the Lengau `COMPLETE`), the v17 pilot record is archived on both sides, and the Lengau archive
   holds both activation proofs.
5. **`build_v18.py` REVISION 2** (base-first archive branch, same output bytes) and the NEW `promote_v18.py` sit in the candidate
   folder beside the controls they promote (the v17 layout), so the controls verdict covers them; they are pinned in `PACKAGE`.
6. **`CTLPAT` adds `row19_nodefail_capture`**: a capture in flight blocks every Lengau step.
7. **`MAC_PAT` adds `promote_v18.py`.**

# v18 -> v19 migration (controls v19: the operational-loss disposition + the E2Q3 on-demand qualifier) - RUNBOOK and SCRIPTS, BUILT AND TESTED, NOT EXECUTED

Written 20 October 2026 (R052 lean T1 plan item 2, owner-approved; Claude, bounded job). Nothing in this folder has been run
against the live tree, Lengau or AWS. It is a mechanical re-point of `chpc/migration_v18/` (every rule of the migration_v16,
v17 and v18 reviews kept): same steps, same transport, containment, drain, lock, archive, deploy-proof and pilot-rollover rules,
re-pointed at the adopted v18 state and the v19 package. The per-file differences are in `v18_to_v19.diff` (review aid).

Extended 21 October 2026 (owner decision "On-demand E2Q3", R052; `chpc/candidate_v19_oploss/DESIGN_v19.md` s.7): the v19
package also carries the E2Q3 on-demand qualifier - three more replaced controllers (EC2 state, E2Q module, ingestion) and ONE
new data path (the E2Q3 operational manifest). Every hash below and in the scripts was re-pinned; the steps are unchanged.

## What is authorised and what is not

v19 is an owner-approved OPERATIONAL change (owner rule 20 Oct 2026: Codex reviews only science changes; operational steps are
recorded by the operator). Both adoption records are OPERATOR records - any committed `reviews/<name>.md` carrying the exact
literal; the scripts check the literal in HEAD and the record's bytes, never who wrote it (as migration_v18 did for its pilot):

1. **Controls adoption record** (step 0) with exactly

       ADOPT row19-screen-controls sha256=111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5 version=19

2. **Pilot adoption record** (step 6.4) with `ADOPT row19-screen-pilot role=refit qualification=<new qsha> max_job=100`.

Not authorised by anything here: a fit, rescue, an EC2 instance or EC2 tool run, a release, the p80 release consumers, any
scale-up beyond the existing `scaleup_refit_v16.json`, any partition or activation. The E2Q3 launch itself follows the
migration (`aws_ec2/E2_OPERATING_SEQUENCE.md`, E2Q3 branch); nothing here admits it.

## The package

`chpc/candidate_v19_oploss/` (pinned by `v19_package.py` `PACKAGE`): controls `111c3107`, map `8256a584`, `build_v19.py`
`db66d9d5`, `promote_v19.py` `31240ba1`, `row19_screen_status.py` `258d4329`, `row19_screen_admit.py` `27e066c7`,
`row19_ec2_state.py` `a9a32329`, `row19_ec2_e2qual.py` `22251f0f`, `row19_ec2_ingest.py` `744ee5c8`, `manifest_e2q3_e2.json`
`6d59c1f8`, and the retained node document `chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json` `730ea262`
(an archive member; job 54 stays node-dispositioned under v19). v19 adds no controller CODE path; it adds one data path,
`aws_ec2/prod/manifest_e2q3_e2.json` (`V19_NEW`, absent before; preflight and deploy refuse if it already exists). The payload is
9 files.

| Step | Script | Where | Writes |
|---|---|---|---|
| 0 | operator record + the `@record` line | Mac | `reviews/<record>.md`, one line of `v19_package.py` (both committed) |
| 1 | `preflight_v19.sh` (Mac half: `v19_package.py preflight`) | Mac + Lengau | nothing |
| 2 | `archive_v18.sh` (`lengau_archive.py`, `mac_archive.py`) | Lengau, then Mac | the two archives, the Mac copy of the Lengau `SHA256SUMS` |
| 3 | `chpc/candidate_v19_oploss/promote_v19.py` | Mac | the 5 promoted controllers and the E2Q3 manifest, the controls, the version-19 adoption |
| 4 | `deploy_v19.sh` | Mac -> Lengau | one controller-clone commit (9 files), the deploy proof |
| 5 | `receipts_v19.sh` (+ `check_v19.sh`, `receipt_check_v19.py`) | Mac (+ Lengau read-only) | the refit and bank receipts |
| 6.1 | `lengau.sh rollover_pilot_v19.sh` | Lengau | moves the v18 review to `gate_retired/` |
| 6.3 | `package_qual_v19.py` | Mac | `chpc/qualification_v19_<qsha8>/` |
| 6.4 | `lengau.sh adopt_pilot19.sh --file reviews/<record>.md` | Lengau | the record commit, the new gate review (by the adopter) |

No epoch activation and no EC2 cycle: epoch 2 stays active; every Lengau step re-verifies `activation_e2.json` as THE canonical
activation of e2 `48cea639` (made under v17 `9ea4e727`; v18 and v19 keep the v17 entry byte-identical, so it stays accepted).
Where commands run: Mac from `workspace_demo/t1_access`; Lengau `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`, every Lengau
part through `lengau.sh` (one `ssh ... lengau bash -s`). Every step refuses rather than overwrites and is safe to re-run.

**Never:** stop, restart or edit a running refit, bank or EC2 worker or reaper, or the job clone `rsc_screen`; set any
permission, qualification, activation or inventory by hand; edit a ledger, budget file, proof, claim, plan or the node document;
delete or relabel e1/e2, an activation proof or an older archive; rerun a pilot fit or repeat `--qualify`; reuse an old ADOPT or
pilot literal (`452b82df`, `530df9a2`, `8fdbf48e`, `2c7a7ef1`, `3c605514`); revert the controls.

## Preconditions

| Gate | Abort if |
|---|---|
| **EC2.** No EC2 attempt or reaper is live (E2Q1 and E2Q2 are reconciled and dispositioned as of 21 Oct 22:18Z). `aws_ec2/e2q_stage.py` `ADOPTED_CONTROLS_SHA` already pins `111c3107` (21 Oct) and refuses until this migration is complete | an EC2 attempt or reaper is live (the Mac drain refuses anyway) |
| **Hold.** From step 1 to 6.4 the refill scripts and slot watcher are stopped and no controller command is started by hand | any admission during the hold |
| **Settlements.** Allowed only at step boundaries and from DEPLOY OK on (lineage holds under v18 before step 4, under v19 after it) | a settlement concurrent with a step |
| **Node document.** `$T/jobs/row19_screen_refit_54.nodefail.json` is exactly `730ea262` | missing or changed |
| **Tests.** `python3 chpc/migration_v19/test_migration_v19.py` passes on these bytes (`test_results.txt`) | any failure |

Running refit jobs keep running untouched (they read only the job clone, the manifest and the ledger); a job that ends during the
migration is settled at a step boundary and, if it failed, is dispositioned by the v19 receipt of step 5.

## The exact command sequence (Mac, from workspace_demo/t1_access)

    # 0. operator record, then fill the @record line of chpc/migration_v19/v19_package.py with its path and sha256, commit both
    #    (REC, REC_SHA = "reviews/<record>.md", "<sha256>"   # @record: ...)
    python3 chpc/candidate_v19_oploss/promote_v19.py --check          # prints the literal the record must carry
    shasum -a 256 reviews/<record>.md
    # 1. preflight (full, with ssh)
    bash chpc/migration_v19/preflight_v19.sh
    # 2. archive the adopted v18 state
    bash chpc/migration_v19/archive_v18.sh --dry-run
    bash chpc/migration_v19/archive_v18.sh
    # 3. promote on the Mac, commit atomically, verify
    python3 chpc/candidate_v19_oploss/promote_v19.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v19_oploss/promote_v19.py --review reviews/<record>.md
    python3 chpc/migration_v19/v19_package.py commit-paths            # -> git add <paths> && git commit -F <msg> -- <paths>
    python3 chpc/candidate_v19_oploss/promote_v19.py --check-promoted --review reviews/<record>.md
    python3 chpc/migration_v19/v19_package.py check-promoted
    # 4. deploy to the controller clone
    bash chpc/migration_v19/deploy_v19.sh --dry-run
    bash chpc/migration_v19/deploy_v19.sh
    # 5. fresh generation-19 receipts (refit must exit 0: zero alarms; operational alarms appear as informational lines)
    bash chpc/migration_v19/receipts_v19.sh
    # 6. pilot rollover: ONE regenerated qualification of the existing job 1 (no fit), package, operator record, adopt
    bash chpc/migration_v19/lengau.sh rollover_pilot_v19.sh
    python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
    python3 chpc/migration_v19/package_qual_v19.py --dry-run
    python3 chpc/migration_v19/package_qual_v19.py                    # commit chpc/qualification_v19_<qsha8>/ with explicit paths
    #    write + commit reviews/<date>_pilot_v19_operator_record.md with ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100
    bash chpc/migration_v19/lengau.sh adopt_pilot19.sh --file reviews/<date>_pilot_v19_operator_record.md
    # 7. refills resume (fresh receipt <= 2,700 s old each time), inside refit+S 81,000, programme 100,000, max_run 10, ceiling 100

## Step notes (what differs from migration_v18)

1. **Preflight** refuses unless the Mac live tree is the adopted v18 (controls `452b82df`, adoption `3e1fe9a1`, status
   `4710544a`, admission `e2260765`, all committed), the Mac qualification is `530df9a2` and its operator pilot record `67f2b438`
   is committed, the package and the operator controls record (literal in HEAD) are exact; on Lengau the controller clone is
   clean at v18 (incl. the v18 Codex controls record `11ebc124` and the pilot record `67f2b438`), the gate holds `530df9a2` with
   an active review bound to it, the retired v17 review is present and the v18 retirement target absent, epoch 2 canonical,
   the node document `730ea262`, no `v18_before_v19` archive or `v19_deploy_proof`, the ledger cap 81,000.
2. **Archives** `$T/archive_screen/v18_before_v19` (controller pins of v18 incl. the node-failure rule and capture script, both
   v18 records, the whole gate, `jobs/` with the node document, ledger copy, both activations) and the 11-member Mac archive
   `chpc/results/archive/row19_screen_v18_before_v19/` (v18 admission, status, EC2 state, E2Q module, ingestion, controls,
   adoption, qualification `530df9a2`, operator pilot record, budget, node document).
3. **Promotion** copies status, admission, EC2 state, E2Q module, ingestion, the E2Q3 manifest (new path), then the controls
   LAST, then writes the version-19 adoption naming the operator record.
4. **Deploy** payload (9, in order): the operator controls record, `chpc/row19_screen_status.py`, `chpc/row19_screen_admit.py`,
   `chpc/row19_ec2_state.py`, `chpc/row19_ec2_e2qual.py`, `chpc/row19_ec2_ingest.py`, `aws_ec2/prod/manifest_e2q3_e2.json`,
   the controls, LAST the adoption; proof `$T/archive_screen/v19_deploy_proof/`; after it: v19 adopted, epoch 2 still canonical,
   the node document unchanged, `IDENTICAL`.
5. **Receipts.** `receipt_check_v19.py` requires generation 19 = latest 19 with controls `111c3107`, the designated view, EC2
   bound to exactly e1 + e2, and job 54 still node-dispositioned on `730ea262`. The v18 rule "refuse any other node
   disposition" is REMOVED (the admission recomputes every disposition itself). Any alarm stops the migration.
6. **Pilot.** The v18 review moves to `gate_retired/review_refit.v18_qual530df9a2_max100.json`; the adopter refuses a gate
   qualification of `530df9a2`, `8fdbf48e` or `2c7a7ef1`.

Still separate: re-pinning `row19_screen_release.py` CONSUMER_FILES / `release_p80` (they bind the v18 controls and admission)
before their next use. `aws_ec2/e2q_stage.py` is already re-pinned to the v19 controls (21 Oct).

## Tests (private copies only, FROZEN fixtures)

`python3 chpc/migration_v19/test_migration_v19.py` (`-k <substring>`, `--keep`). Worlds are seeded from git objects at
`FIXTURE_COMMIT` RSC `1a83cbf` (the adopted v18 Mac tree with pilot `530df9a2`), each file checked against its pinned hash or the
frozen v18 entry's 19 pins; only the candidate package is read from the working tree. The fake Lengau root is what migration_v18
left: controller clone at v18 with the three untracked evidence files, gate at `530df9a2`, retired v15/v16/v17 reviews, both
activations (`activation_e2.json` generated by the real frozen `row19_partition` under the frozen v17 controls, as in reality),
earlier archives and deploy proofs, the node document. Exactly three tagged lines are substituted (`@root`, `@transport`,
`@record`); the production `@record` line may be PENDING or one filled operator-record line. Results: `test_results.txt`.

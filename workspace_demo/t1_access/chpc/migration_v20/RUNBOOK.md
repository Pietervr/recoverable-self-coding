# v19 -> v20 migration (controls v20: the EC2 CLOSE, epoch-2 block handed back to Lengau) - RUNBOOK and SCRIPTS, BUILT, STATICALLY CHECKED, NOT EXECUTED

Written 23 October 2026 (R052, Claude, bounded job; owner decision 23 Oct 2026 "go with route A"). Nothing in this folder has been
run against the live tree, Lengau or AWS. It is the `chpc/migration_v19/` route re-pointed at the adopted v19 state and the v20
package (`chpc/candidate_v20_handback/`, design `DESIGN_v20.md`), with ONE new step: **step 6, the close** (`close_v20.sh` ->
`close_e3.sh`, the e3 activation under the plan lock). The per-file differences are in `v19_to_v20.diff` (review aid).

**Time-critical.** Lengau runs out of plannable coordinates at about the 24 Oct 04:00Z refill (179 left, 7.5 jobs). From step 4 to
step 8.4 every refit admission HOLDS (from step 4 by design: e3 is pinned and not yet activated). Running jobs continue untouched.

## What is authorised and what is not

Two OPERATOR records (owner rule 20 Oct 2026; the parent session runs one synchronous Codex review of the candidate BEFORE step 0a):

1. **Controls adoption record** (step 0a), exactly

       ADOPT row19-screen-controls sha256=4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c version=20

2. **Pilot adoption record** (step 8.4) with `ADOPT row19-screen-pilot role=refit qualification=<new qsha> max_job=100`.

Not authorised by anything here: a fit, rescue, an EC2 instance, `prod_launch`, `qual_permit`, `release-adopt`, a cap or
sub-envelope raise (that is the separate funding step, DESIGN_v20.md s.6, due before about 28 Oct), any scale-up beyond the
existing `scaleup_refit_v16.json`.

## The package

`chpc/candidate_v20_handback/` (pinned by `v20_package.py` `PACKAGE`): controls `4e64982b`, map `b3335953`, `build_v20.py`
`6e82bb13`, `promote_v20.py` `4dfd0557`, `row19_partition.py` `a7629337` (REVISION 7), `row19_screen_admit.py` `7c49bf86`
(REVISION 20), `row19_partition_e3.json` `ca87fb1d` (NEW path `chpc/row19_partition_e3.json`), `aws_ec2/prod_authority.py`
`20de63d2` (REVISION 10, replaces the Mac `ba726a19`), and the retained node document `730ea262` (archive member). Deploy payload:
7 files.

| Step | Script | Where | Writes |
|---|---|---|---|
| 0a | operator record + the `@record` line of `v20_package.py` | Mac | `reviews/<record>.md`, one line (both committed) |
| 0b | EC2 dispositions (commands below) | Mac (+ ec2_sync to Lengau) | ledgers, inventories, the root's fence/acks (existing tools) |
| 1 | `preflight_v20.sh` (Mac half: `v20_package.py preflight`, incl. `close-check` MET) | Mac + Lengau | nothing |
| 2 | `archive_v19.sh` | Lengau, then Mac | the two archives, the Mac copy of the Lengau `SHA256SUMS` |
| 3 | `chpc/candidate_v20_handback/promote_v20.py` | Mac | partition module, admission, e3, Mac authority, controls, adoption |
| 4 | `deploy_v20.sh` | Mac -> Lengau | one controller-clone commit (7 files), the deploy proof |
| 5 | `receipts_v20.sh --pre-close` | Mac (+ Lengau read-only) | refit and bank receipts |
| 6 | `close_v20.sh` (Lengau body `close_e3.sh`) | Mac -> Lengau | `$T/row19_screen/ec2/activation_e3.json` only |
| 7 | `receipts_v20.sh --post-close` | Mac (+ Lengau read-only) | refit and bank receipts |
| 8.1 | `lengau.sh rollover_pilot_v20.sh` | Lengau | moves the v19 review to `gate_retired/` |
| 8.3 | `package_qual_v20.py` | Mac | `chpc/qualification_v20_<qsha8>/` |
| 8.4 | `lengau.sh adopt_pilot20.sh --file reviews/<record>.md` | Lengau | the record commit, the new gate review |
| 9 | refill | Mac | 10 jobs (the first round: the remaining Lengau-replicate coordinates, then replicate 24's block) |

**Never:** stop, restart or edit a running refit, bank or EC2 worker or reaper, or the job clone `rsc_screen`; set any
permission, qualification, activation or inventory by hand; edit a ledger, budget file, proof, claim, plan, e2 or e3; delete or
relabel e1/e2, an activation proof or an older archive; rerun a pilot fit or repeat `--qualify`; reuse an old ADOPT or pilot
literal; revert the controls.

## The exact command sequence (Mac, from workspace_demo/t1_access)

    # 0a. after Codex's review: write + commit the operator controls record (the literal above); fill the @record line of
    #     chpc/migration_v20/v20_package.py (REC, REC_SHA = "reviews/<record>.md", "<sha256>"   # @record: ...); commit both
    python3 chpc/candidate_v20_handback/promote_v20.py --check        # prints the literal
    shasum -a 256 reviews/<record>.md
    # 0b. the EC2 dispositions (allowed under v19; can run NOW): qual-E2Q3/1 still owns its 52 rep-24 coordinates and
    #     qual-Q2/1 is reconciled but pending (owns nothing, but counts as owning) - both end as dispositioned
    python3 aws_ec2/prod_authority.py disposition --run qual-E2Q3 --attempt 1 --reason "row 19 EC2 closed (owner 23 Oct 2026, route A): E2Q3 NO_RELEASE (cert 41226aeb); nothing is ingested"
    python3 aws_ec2/prod_authority.py disposition --run qual-Q2 --attempt 1 --reason "row 19 EC2 closed (owner 23 Oct 2026, route A): Q2 is qualification evidence only (Codex resize s.5); owns no coordinate"
    python3 aws_ec2/ec2_sync.py cycle         # installs the generation with both requests; the root fences them and writes
                                              # ack_g<N>; the same cycle runs disposition-confirm for both (ec2_sync.py step 5)
    python3 aws_ec2/prod_authority.py inventory && python3 aws_ec2/ec2_sync.py cycle    # a FRESH terminal generation on the root
    python3 chpc/candidate_v20_handback/aws_ec2/prod_authority.py close-check          # must print "MET"
    # 1. preflight (full, with ssh) - within six hours of the fresh inventory of 0b, or refresh it before step 6
    bash chpc/migration_v20/preflight_v20.sh
    # 2. archive the adopted v19 state
    bash chpc/migration_v20/archive_v19.sh --dry-run
    bash chpc/migration_v20/archive_v19.sh
    # 3. promote on the Mac, commit atomically, verify
    python3 chpc/candidate_v20_handback/promote_v20.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v20_handback/promote_v20.py --review reviews/<record>.md
    python3 chpc/migration_v20/v20_package.py commit-paths            # -> git add <paths> && git commit -F <msg> -- <paths>
    python3 chpc/candidate_v20_handback/promote_v20.py --check-promoted --review reviews/<record>.md
    python3 chpc/migration_v20/v20_package.py check-promoted
    # 4. deploy to the controller clone (identical check: local vs remote digests of every pinned and promoted file)
    bash chpc/migration_v20/deploy_v20.sh --dry-run
    bash chpc/migration_v20/deploy_v20.sh
    # 5. fresh generation-20 receipts, BEFORE the close (refit must exit 0: zero alarms; EC2 binding e1 + e2)
    bash chpc/migration_v20/receipts_v20.sh --pre-close
    # 6. THE CLOSE: Mac close-check (promoted authority) MET, then on Lengau verify3 against the root's register and the e3
    #    activation under the plan lock. If the installed inventory is older than six hours: prod_authority.py inventory +
    #    ec2_sync.py cycle first.
    bash chpc/migration_v20/close_v20.sh --dry-run
    bash chpc/migration_v20/close_v20.sh
    # 7. fresh receipts AFTER the close: activations e1+e2+e3, EC2-designated unclaimed 0, Lengau plannable ~3,453 (less any
    #    coordinates the jobs running since the last refill took)
    bash chpc/migration_v20/receipts_v20.sh --post-close
    # 8. pilot rollover: ONE regenerated qualification of the existing job 1 (no fit), package, operator record, adopt
    bash chpc/migration_v20/lengau.sh rollover_pilot_v20.sh
    python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
    python3 chpc/migration_v20/package_qual_v20.py --dry-run
    python3 chpc/migration_v20/package_qual_v20.py                    # commit chpc/qualification_v20_<qsha8>/ with explicit paths
    #    write + commit reviews/<date>_pilot_v20_operator_record.md with ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100
    bash chpc/migration_v20/lengau.sh adopt_pilot20.sh --file reviews/<date>_pilot_v20_operator_record.md
    # 9. refills resume (fresh receipt <= 2,700 s old each time), inside refit+S 81,000 (binds about 28 Oct - DESIGN_v20.md s.6),
    #    programme 100,000, max_run 10, ceiling 100

## Step notes (what differs from migration_v19)

- **0b is new and is a precondition, enforced twice:** `v20_package.py preflight` runs the read-only `close-check` (Mac
  ledgers, the latest sealed inventory) and the Lengau preflight refuses while the root's installed inventory shows a live or
  owning attempt; the e3 activation re-checks both under the plan lock (`row19_partition.close_problems`). Why qual-Q2/1 too:
  `row19_ec2_state.owns` counts every pending attempt as owning, and `current_problems` accepts an inventory older than six hours
  only while nothing is owning - with every attempt terminal, Lengau needs no further `ec2_sync` after the close.
- **Archives** `$T/archive_screen/v19_before_v20` (every v19 pin incl. the partition module and admission, e1, e2, the v19 records,
  the Mac authority as the controller clone holds it, the whole gate, `jobs/` with the node document, ledger copy, both
  activations) and the 9-member Mac archive `chpc/results/archive/row19_screen_v19_before_v20/`.
- **Promotion** copies the partition module, the admission, e3 (new path), the Mac authority, then the controls LAST, then the
  version-20 adoption.
- **Deploy** payload (7, in order): the operator record, `chpc/row19_partition.py`, `chpc/row19_screen_admit.py`,
  `chpc/row19_partition_e3.json`, `aws_ec2/prod_authority.py`, the controls, LAST the adoption. After it: v20 adopted, e3 pinned
  and verified against e2 (`e3_pinned`), the e1/e2 proofs byte-identical to the archive (`act2_kept`; e2's is historical under
  v20 by design), no e3 activation yet, `IDENTICAL`. From here Lengau refit admission HOLDS until step 6.
- **Receipts** `--pre-close`: generation 20, activations exactly e1 + e2. `--post-close`: e1 + e2 + e3, EC2 waiting 0, the view
  adding up. The status view itself is unchanged; its "EC2-designated unclaimed" line reads 0.
- **The close** (`close_e3.sh`): v20 adopted and deployed, e3 pinned, e1/e2 kept, node document, drain, installed inventory fresh
  with no owner and no live/owning attempt, `verify3` against the root's own register, then
  `$T/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e3.json`
  (plan lock, `close_problems`, immutable proof), then `act3_valid`. Re-run: an existing proof that verifies = "already closed".
- **Pilot.** v20 lapses `e123d6e5` (the pilot gate is controls-generation-bound). The v19 review moves to
  `gate_retired/review_refit.v19_quale123d6e5_max100.json`; the adopter refuses `e123d6e5`, `530df9a2`, `8fdbf48e`, `2c7a7ef1`.
  Rollover and adoption require epoch 3 to be the canonical activation (`act3_valid`), so they follow the close.
- **Down-stream:** `aws_ec2/e2q_stage.py` pins the v19 controls and refuses under v20 (intended: no EC2 staging after the close).
  `row19_screen_release.py` / `release_p80` still need re-pinning before their next use (unchanged from v19).

## Tests

- `python3 chpc/candidate_v20_handback/test_v20_handback.py` (66/0) and the regression set (`DESIGN_v20.md` s.7).
- `python3 chpc/migration_v20/static_check_v20.py` (`static_results.txt`): every script parses, every composed Lengau body parses
  and carries the production root, Lengau-side Python is 3.6-level, every pin equals the bytes it names, the payload/archive
  counts, no leftover v19-package token, no worker/AWS/launch call, and `receipt_check_v20` on the newest real (v19) receipt
  refuses exactly what it must.
- **Not done:** the migration_v19 end-to-end harness (`test_migration_v19.py`: frozen-fixture worlds, a fake Lengau root, every
  refusal path) is NOT re-pointed to v20. The scripts are a mechanical re-point of that tested route plus the close step; the
  re-pointed harness is the remaining verification before a fully tested route (see OPEN in the job report).

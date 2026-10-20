# EC2 epoch 2 - operating sequence: E2Q1 -> release -> production

Owning runbook for the paid epoch-2 route (20 Oct 2026). Sources: `chpc/candidate_e2q/DESIGN_e2q.md` s.7,
`chpc/candidate_e2s/DESIGN_e2s.md` s.3, and the two operating conditions of
`reviews/2026-10-19_mig17_staging_r6_codex_review.md` s.2 (choices 6 and 9). Owner approval: R052 lean plan item 4
(20 Oct 2026). Caps: USD 2,300 production envelope, USD 3,000 total; the USD 300 allowance funds qualification.

**Staging tool.** `aws_ec2/e2q_stage.py` + `aws_ec2/e2q_stage_verify.py`. The verifier is byte-identical to the
Codex-reviewed `chpc/candidate_e2s` bytes of `0a72081` (`f742f017`). The stage tool differs from the reviewed `d531b455`
only in the controls pin, moved to the v18 controls `452b82df` (with its refusal text and docstring). That is an
administrative change under the owner rule of 20 Oct 2026 and needs no Codex review. v18 keeps every qualification code pin
of v17, and no data pin moves. Offline tests: `python3 aws_ec2/tests/test_e2q_stage.py` (from `t1_access/`) passes 100/100.

## Prerequisites (all must hold first)

1. Controls v18 (`452b82df`) are migrated, adopted, promoted and deployed on Lengau, with canonical e2 activation
   (`chpc/migration_v18/RUNBOOK.md`). The stage tool refuses any other controls bytes on the Mac or on Lengau.
2. The E2Q1 permission record `aws_ec2/prod/permit_e2q1.md` is committed.
3. No migration drain is in progress. EC2 tools must not run while the v18 drain does.

## E2Q1

1. `python3 aws_ec2/qual_permit.py --epoch2 --record prod/permit_e2q1.md` (the path is relative to `aws_ec2/`).
2. `python3 aws_ec2/prod_authority.py budget`. Check the USD 2,300 envelope and USD 3,000 cap against the allowance.
3. `python3 aws_ec2/prod_authority.py inventory`, then `python3 aws_ec2/ec2_sync.py cycle`, then a fresh refit receipt
   (at most 2,700 s old at admission).
4. Dry run (authorisation only):
   `python3 aws_ec2/prod_launch.py --contract E2Q1 --epoch 2 --partition ../chpc/row19_partition_e2.json
   --manifest prod/manifest_e2q1_e2.json --panel prod/panel_e2q_e2.json --snapshot ../chpc/results/row19_screen
   --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --dry-run`
5. Repeat step 4 without `--dry-run`. This launches ONE c7a.24xlarge spot instance with a worst case of USD 27.92 against the
   allowance. The reaper reconciles it.
6. Once the attempt is reconciled: `python3 aws_ec2/ec2_sync.py cycle` (install the current generation), then
   `python3 aws_ec2/e2q_stage.py run --run qual-E2Q1 --attempt 1`. This collects, verifies, stages, re-verifies, takes
   ONE `EVALUATION_CLAIM` and runs the reviewed qualifier command with `--snapshot chpc/claims_snapshot_e2.json`.
   The exit codes are: 0 RELEASE, 3 NO_RELEASE/INCONCLUSIVE, 4 REFUSED, 2 transport/qualifier failure. The Mac stage
   directory is `aws_ec2/runs/qual-E2Q1/e2q_stage/<stamp>/`. The remote one is
   `/mnt/lustre/users/pvanrooyen/t1_toolchain/ec2_stage/qual-E2Q1/attempt_1/<stamp>/`.
7. **Archive the certificate (condition A below) BEFORE any actual-result review or release-adopt.** Then commit it.
8. Codex writes the actual-result review (science; Codex review required). On FAVOURABLE it emits
   `RELEASE row19-ec2-qualification epoch=2 certificate=<sha256> attempts=qual-E2Q1/1`.
9. `python3 aws_ec2/prod_authority.py release-adopt --certificate <cert> --review <review>`, then inventory and
   `ec2_sync.py cycle`, then canonical ingestion of `qual-E2Q1/1` (ingestion REVISION 8, released-E2Q per-slot route),
   then `ack`.

## Production

10. Admissions run under the five-instance ceiling, each with a fresh receipt:
    `prod_launch.py --contract production --epoch 2 --manifest prod/manifest_production_e2.json ...`, inside the
    USD 2,300 envelope and the USD 3,000 cap (46 base batches plus at most 4 extra from the allowance).

## Branches

- **E2Q1 ends without a usable bundle for an external cause** (spot interruption before the memory gate, or capacity):
  `disposition` and `ec2_sync`, then a separately reviewed E2Q2 record (`prod/permit_e2q2.md`; it needs its own owner
  record), then `qual_permit.py --epoch2 --e2q2 --record prod/permit_e2q2.md`, then the same launch with
  `--contract E2Q2 --manifest prod/manifest_e2q2_e2.json` and `e2q_stage.py run --run qual-E2Q2 --attempt <n>`.
- **NO_RELEASE or INCONCLUSIVE**: stop and go back to the owner with a costed alternative. There is no retry by outcome.
  An administrative NO_RELEASE still consumes the evaluation.
- **Qualifier exit 2 / crash / timeout / lost reply**: the claim stays consumed. Use condition B. Never re-invoke.

## Condition A - certificate archival (Codex choice 9)

After the evaluation, copy these into `aws_ec2/certs/<run>/attempt_<n>/<UTC stamp>/` (the stamp is the staging stamp):

- the certificate `cert_<run>_<n>.json`, **byte-unchanged** (no path rewriting);
- `receipt.json`, `binding.json`, `remote.json` and `expect.json` from the Mac stage directory;
- the `installed_inventory_<time>.json` that `binding.json` names;
- the remote claim and the rc/output evidence, fetched read-only from Lengau: `<attempt dir>/EVALUATION_CLAIM`,
  `<stamp dir>/qualify.rc` and `<stamp dir>/qualify.out`.

Commit these as explicit small paths in one atomic `git add <paths> && git commit -- <paths>`. Never force-add a bundle or
sandbox. The bundle and sandbox stay immutable and untracked at their original locations (record those locations in the
commit message). Nothing is deleted; retention runs through release, ingestion and ACK (choice 12). If the installed
inventory advanced between preflight and evaluation, the certificate's own bound inventory is the authority for the result
review (choice 11).

## Condition B - lost-reply retrieval (Codex choice 6)

If the `qualify` reply is lost (disconnect, timeout, crash, missing local certificate), the claim is an at-most-once hold.
It is not proof that the qualifier never ran. Recover by **read-only** retrieval only: `ssh lengau` `cat`/`ls`/`sha256sum`
of the existing `EVALUATION_CLAIM`, `qualify.rc`, `qualify.out`, the certificate at the `--out` path and the staging
evidence, plus `scp chpc-scp:` copies into the Mac stage directory. Then archive as in condition A. **Never invoke the qualifier
again, never run `e2q_stage.py qualify` a second time for the same attempt, never remove or reset the claim.** The tool
refuses a re-run anyway. A missing certificate after a consumed claim goes back to the owner. A supersession route for a
provably non-evaluated attempt would need its own review.

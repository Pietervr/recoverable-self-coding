# v20 -> v21 migration (controls v21: the FUNDING ROUTE, CSCI1913 first then HEAL1922, side by side) - RUNBOOK

Written 26 October 2026 (R052, Claude, bounded job; brief Unimog-Projects `prompts/2026-10-26_r052_heal1922_funding_route_job.txt`).
This is the `chpc/migration_v20/` route re-pointed at the adopted v20 state and the v21 package (`chpc/candidate_v21_heal/`,
design `DESIGN_v21.md`). It drops the EC2 close, which is done and stays done, and adds ONE step: **step 5, the two-phase cap
raise** 81,000 -> 181,000 (`raise_cap_v21.sh`). The status of each step (run or not) is recorded in the operator record and the
R052 work item, not here.

**Timing.** Run the Lengau steps (1-8) in ONE window with no refill or settlement in flight. Refit admission HOLDS from step 4
until step 8 (the pilot gate is generation-bound). Settlements keep working throughout. Running refit jobs are never touched:
their worker, job-end and ledger code are manifest pins that v21 does not change. v21 must be live before CSCI1913 binds (see
DESIGN_v21.md s.5: in the round after j101-j110).

## What is authorised

Owner rulings of 17 Oct and 26 Oct 2026 (DESIGN_v21.md header). Under the owner's 20 Oct 2026 rule this is an operational
change (no science byte moves), so it is adopted by two OPERATOR records:

1. **Controls adoption record** (step 0): `ADOPT row19-screen-controls sha256=72a5d2606c387433715befcc097e723c18bf4ba124ca5558878d550ea10ee8fb version=21`
2. **Pilot adoption record** (step 8): `ADOPT row19-screen-pilot role=refit qualification=<new qsha> max_job=200`

Not authorised by anything here: a fit, a rescue, a pilot fit, any EC2 action, a change to a running job, a raise beyond 181,000.

## The package

`chpc/candidate_v21_heal/` (pinned by `v21_package.py` `PACKAGE`): controls `72a5d260`, map `41a7bc5e`, `build_v21.py`
`10fd311a`, `promote_v21.py` `9d431206`, `programme_gate.py` `041bc123` (REVISION 5), `row19_screen_admit.py` `1caf6933`
(REVISION 21), and the retained node document `730ea262` (archive member). Deploy payload: 5 files (the record, the gate, the
admission, the controls, LAST the adoption).

| Step | Script | Where | Writes |
|---|---|---|---|
| 0 | operator record + the `@record` line of `v21_package.py` | Mac | `reviews/<record>.md`, one line (both committed) |
| 1 | `preflight_v21.sh` | Mac + Lengau | nothing |
| 2 | `archive_v20.sh` | Lengau, then Mac | the two archives, the Mac copy of the Lengau `SHA256SUMS` |
| 3 | `chpc/candidate_v21_heal/promote_v21.py` + commit | Mac | the gate, the admission, the controls, the adoption |
| 4 | `deploy_v21.sh` | Mac -> Lengau | one controller-clone commit (5 files), the deploy proof |
| 5 | `raise_cap_v21.sh` + Mac commit of `chpc/row19_screen_budget.json` | Lengau, then Mac | the budget phase, the ledger cap 181,000 |
| 6 | `lengau.sh rollover_pilot_v21.sh` | Lengau | moves the v20 max-200 review to `gate_retired/` |
| 7 | `--qualify 1`, then `package_qual_v21.py` + commit | Mac (+ Lengau) | `chpc/qualification_v21_<qsha8>/` |
| 8 | pilot record + `lengau.sh adopt_pilot21.sh --file reviews/<record>.md` | Mac, Lengau | the record commit (both clones), the new gate review |
| 9 | refill (the parent's `refill.sh`) | Mac | jobs, each with `#PBS -P` from the route |

**Never:** touch a running refit job or the job clone `rsc_screen`; edit a ledger, budget file (except through step 5),
proof, plan or activation by hand; rerun a pilot fit or repeat `--qualify`; reuse an old ADOPT or pilot literal; revert the
controls.

## The exact command sequence (Mac, from workspace_demo/t1_access)

    # 0. write + commit the operator controls record (literal above); fill the @record line of chpc/migration_v21/v21_package.py
    #    (REC, REC_SHA = "reviews/<record>.md", "<sha256>"); commit it
    python3 chpc/candidate_v21_heal/promote_v21.py --check        # prints the literal
    # 1. preflight (full, with ssh)
    bash chpc/migration_v21/preflight_v21.sh
    # 2. archive the adopted v20 state
    bash chpc/migration_v21/archive_v20.sh
    # 3. promote on the Mac, commit atomically (explicit paths), verify
    python3 chpc/candidate_v21_heal/promote_v21.py --review reviews/<record>.md
    python3 chpc/migration_v21/v21_package.py commit-paths            # -> git add <paths> && git commit -F <msg> -- <paths>
    python3 chpc/migration_v21/v21_package.py check-promoted
    # 4. deploy to the controller clone (identical check: local vs remote digests of every pinned and promoted file)
    bash chpc/migration_v21/deploy_v21.sh                             # tell the parent: v20 retired, v21 live (admission held)
    # 5. the cap raise (two-phase, owner ruling as --note), then commit the copied-back budget phases on the Mac
    bash chpc/migration_v21/raise_cap_v21.sh
    # 6. pilot rollover: retire the v20 max-200 review
    bash chpc/migration_v21/lengau.sh rollover_pilot_v21.sh
    # 7. ONE regenerated qualification of the existing job 1 (no fit), package, commit
    python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt --qualify 1
    python3 chpc/migration_v21/package_qual_v21.py
    # 8. write + commit reviews/<date>_pilot_v21_operator_record.md with ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=200
    bash chpc/migration_v21/lengau.sh adopt_pilot21.sh --file reviews/<record>.md     # tell the parent: refills may resume
    # 9. refills resume (fresh receipt each time); every new job is charged to the first programme that fits

## Step notes

- **Archives**: `$T/archive_screen/v20_before_v21` (every v20 pin incl. the gate and the admission, e1/e2/e3, the v20 controls
  record and both v20 pilot records, the whole gate, `jobs/` with the node document, the ledger copy, all three activation
  proofs) and the 8-member Mac archive `chpc/results/archive/row19_screen_v20_before_v21/`. A read-only `inventory` run against
  the live tree on 26 Oct 2026 19:04Z found 815 sources complete.
- **Deploy** checks after the commit: v21 adopted, epoch 3 still THE canonical activation (the e3 proof `fb3304d3` was made
  under v20; v21 pins the same e3, so it stays canonical: candidate test F10 on the real proof), e1/e2/e3 proofs byte-identical
  to the archive, the funding route resolving on the REAL ledgers (`route_live`: prints both programmes' committed and where a
  job would go now), the node document unchanged, IDENTICAL.
- **Cap raise**: the existing `--raise-cap` path (cap_problem, pending phase, ledger raise with cap_history, certification,
  commit) under the programme lock for that one call; the phase file is committed in the controller clone and copied back to
  the Mac byte-identical. A re-run after completion reports "already raised".
- **Pilot**: v21 lapses `2e99d615`. The max-200 review moves to `gate_retired/review_refit.v20_qual2e99d615_max200.json`; the
  adopter refuses `2e99d615` and every older qualification; the new literal carries `max_job=200` (the owner's 26 Oct scope).

## Tests

- `python3 chpc/candidate_v21_heal/test_v21_heal.py`: 62/0 (`DESIGN_v21.md` s.6) and the regression set.
- `python3 chpc/migration_v21/static_check_v21.py` (`static_results.txt`): every script parses (bash -n, Python 3.6 grammar for
  the Lengau side), the composed Lengau scripts parse, no placeholder is left, the package pins match the candidate bytes,
  the payload is 5 files, no script calls qdel, qsub or a worker.
- There is no frozen end-to-end rehearsal of this migration (the 1,773-line `migration_v20/test_migration_v20.py` harness was
  not re-pointed). The scripts are the v20 bodies with the close removed and one well-trodden step (the v16 `--raise-cap`)
  added. They refuse on any unexpected state, and step 1 is a full live read-only preflight.

# Row 19 screen controls v19 - CANDIDATE, not adopted (the OPERATIONAL-LOSS disposition + the E2Q3 on-demand qualifier)

Written 20 October 2026 (R052 lean T1 plan item 2, owner-approved; Claude, bounded job). An operational change: no Codex review,
adopted by an OPERATOR record carrying the ADOPT literal. Nothing was promoted, deployed or run against Lengau, PBS or AWS; no
live file was edited. New bytes only in `chpc/candidate_v19_oploss/` and `chpc/migration_v19/`.

Extended 21 October 2026 (owner decision "On-demand E2Q3", R052; Claude, bounded job): v19 also carries the E2Q3 on-demand
qualifier (section 7). The controls hash, the promotion map, the builder, the promoter and the migration pins moved with it
(section 4). The live aws_ec2 Mac tools were edited in place for E2Q3 (not controls-pinned; section 7).

## 1. Why

Every routine HPC failure that none of the three evidence-based classes covers (closed-no-record, crashed-slot, node-failure)
leaves the job's scheduler-exit / runner-end / missing-status alarms in every receipt, `receipt_problem` refuses ("the newest
receipt has alarm(s)") and no refill is admitted until someone builds a new disposition and a new controls version (v18 took a
day for one lost node). v19 = v18 + ONE general fallback so that such failures stop blocking refills.

## 2. The rule (`row19_screen_admit.operational_loss_evidence`, ONE implementation)

The status view calls it for a terminal refit job that is NOT clean (scheduler exit not 0/75, or no runner end, or a runner exit
not 0/75) and that none of the three existing dispositions grants; the admission recomputes it from the current ledger, root and
retained verifier units and requires the receipt's disposition EXACTLY equal (the REVISION 14/18 pattern). Granted only when:

1. **Scheduler/ledger.** State F with an integer exit; the ledger entry SETTLED with its certificate (finite charge, note >= 8
   characters, non-negative time); the note's `Exit_status` equals the observed exit; token, job and PBS id are the plan's; a
   recorded runner end carries an integer runner exit that is exactly the job-end code its statuses give (row19_shard's rule:
   HELD 4 if any slot lacks a 0/75 status, else 75 if any 75, else 0). **No evidence file is required.**
2. **Statuses.** Every present status is readable, this job's slot, its planned rep/indices partitioned into new/resumed/left,
   with an integer exit; every unit whose timing names the job at a slot's coordinates is in that status's `new`; the statuses
   scoped to the PBS id are exactly the planned present ones (no unplanned slot, no temporary name).
3. **No-status slots.** No worker log reports an exit line; each coordinate holds no temporary/non-canonical file and either
   nothing, or a verified record of THIS job in its planned slot whose current canonical artifacts are that evidence
   (**salvaged**: counted as this job's `new`, e.g. a walltime kill after the record was published), or a later bound job's
   verified planned completion (the R1 rule).
4. **Timings (V15-1).** Every timing naming the PBS id is at its canonical path and is a status's new or a salvaged coordinate in
   its planned slot.

**Granted.** The summary carries `operational_loss` (kind, exits, runner end, the settlement certificate, plan sha256,
completed / crashed / no-status slots, salvaged and uncompleted coordinates, `counts_as_crash: false`). Completed statuses
(0/75) are reconciled as ordinary workers; crashed statuses (any other exit) keep their records and their `left` coordinates
(returned to the planner as ordinary left work); the no-status coordinates less salvaged are `uncompleted`, origin
`operational-loss` (returned to the planner). The settled core-h stay charged; nothing is credited.

**Alarms.** For a granted job these OPERATIONAL alarms become informational lines (summary `informational`, receipt top-level
`informational` when non-empty, printed as `informational:`): the scheduler-exit, missing-runner-end and runner-exit alarms, its
slots' missing-status and worker-exit alarms, and the no-finite-scheduler-memory alarm. Everything else still alarms and blocks:
producer code/environment (pins/hashes), anchors, invalid/foreign records and timings, unreadable or wrong statuses, identity
and binding alarms, the walltime-request and scheduler-memory-above-90 % alarms. A refusal (`operational_loss_held` keeps the
reason) leaves every alarm standing: an UNSETTLED terminal job (settling is the operator's step, every tick), a ledger
inconsistency (note exit, runner exit vs statuses), a corrupt status, an unverifiable record/timing, a temp file, an
unexplained missing status (log exit line), a duplicate status.

**Never a crash, never a pilot.** `crash_history` / `crash_excluded` (the same-envelope RESCUE-PENDING rule) are byte-unchanged
and read `slot_disposition` only. `job_summary_problem(pilot=True)` and `--qualify` refuse an operational-loss job.

**Precedence and byte stability.** closed-no-record -> crashed-slot (runner exit 4) -> node-failure (no runner end) -> operational
loss. A clean job and every job an existing class grants never gain a key: on the newest local receipt
(`watch_refit_20261021T010040Z`, 65 jobs) every job summary reconciles byte-equal under v19 (test part 9).

## 3. Admission changes (REVISION 19, `row19_screen_admit.py`)

- `operational_loss_evidence` (the rule) and `oploss_disposition_problem` (exact recompute, bound PBS id/token/plan, the
  certificate, summary `ended = slots - no-status`, the runner exit, origin `operational-loss`, salvaged in `new`).
- `job_summary_problem`: never a pilot; an operational-loss summary is F with integer exits, the ended workers counted, memory
  finite when observed (may be absent).
- `units_problem`: units reconcile against the plan minus `uncompleted`.
- `transition_problem`: SETTLED, the same runner end/exit, certificate and PBS id.
- `receipt_problem`: the new branch; more than one of the four disposition keys refuses.
- `held_accounting_problem`: a HELD (runner exit 4) entry is accounted by a slot disposition OR an operational loss.
- `envelope_problem`: an operational-loss job whose walltime request PBS no longer reports (history expired) skips only that
  request check; the plan/ledger envelope checks stay.

Status view (REVISION 19, `row19_screen_status.py`): `operational_loss()` wrapper, the reconcile fallback with the
operational/informational split, partition accounting (salvaged into `new`), the printout, the receipt `informational` list, and
the `--qualify` refusal. The REVISION 8/14/18 code paths are unchanged.

## 4. Files and pins

| File | SHA-256 |
|---|---|
| `row19_screen_status.py` | `258d43293b15f1ae9457cd323f2a4a7b71af79e83695dff51601037991a7cb45` (v18 `4710544a` + REVISION 19, `status_v18_to_v19.diff`) |
| `row19_screen_admit.py` | `27e066c72ed43919a92083fcf3f035cbee232c2137c2e97832f0e41b1113f9df` (v18 `e2260765` + REVISION 19, `admit_v18_to_v19.diff`) |
| `row19_ec2_state.py` | `a9a32329b827b7b9d0bee27523271424c3d8e6026efd164d4b5fae975e1d487f` (v18 `7bdedafc` + REVISION 5, `state_v18_to_v19.diff`) |
| `row19_ec2_e2qual.py` | `22251f0ffa8c338f9f3f545eccd27391a86da0bcd2aba343cca69735df5dd42c` (v18 `5ceba551` + REVISION 2, `e2qual_v18_to_v19.diff`) |
| `row19_ec2_ingest.py` | `744ee5c81aba5be7b5160c61ccf6f335d9005d954935865d89106aa54c8fe5cd` (v18 `277c51b0` + REVISION 9, `ingest_v18_to_v19.diff`) |
| `manifest_e2q3_e2.json` | `6d59c1f8568945f6121f9f16779aabe30f6334178bb0ba8c9d192a024805e17f` (DATA row: promoted to the NEW path `aws_ec2/prod/manifest_e2q3_e2.json`, not a controls pin) |
| `row19_screen_controls.json` | `111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5` |
| `v19_promotion_map.json` | `8256a58490d868af8c09988f69b91acf70843683bbf0fd2104cd98fc10f7a56e` |
| `build_v19.py` / `promote_v19.py` | `db66d9d5…` / `31240ba1…` (the v18 base-first builder/promoter pattern, plus the build_v17 `data` group) |

Controls v19 = adopted v18 `452b82df` versions 1-18 byte-equal + one version-19 entry: exactly five pins change (admission,
status; EC2 state, E2Q module, ingestion); the qualifier `row19_ec2_qualify.py` (`1d8eee78`), the v18 node-failure rule and
capture pins, the other 11 pins, partition e2 `48cea639`, `sub_envelopes`, `qualification_S`, programme and deployment equal
v18. The promotion map's rows, in copy order: status, admission, EC2 state, E2Q module, ingestion, the E2Q3 manifest (data,
previous none), then the controls LAST, then the version-19 adoption record. The Mac archive `v18_before_v19` holds 11 members
(the five replaced controllers' v18 bytes added). The operator adoption record must carry exactly:

    ADOPT row19-screen-controls sha256=111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5 version=19

## 5. Tests (`test_results.txt`)

- `test_v19_oploss.py`: 76 passed, 0 failed - node loss without evidence (exit 265), walltime kill 271 with a salvaged
  record, scheduler kill (-11, no status; and memory unobserved), crashed worker (status exit 4, HELD job, crash evidence not
  retrieved), each with the exact admission recompute, never-a-pilot and crash-history-empty checks; an unsettled terminal job
  and the integrity cases still block (ledger inconsistencies, corrupt or duplicate status, corrupt record, temp file, log exit
  line, orphan timing; invalid record / identity / walltime-request / memory-90 % alarms stand beside a granted disposition);
  admission refusals; the REAL replay; controls checks; Python 3.7 grammar; the live tree untouched.
- Regression (`R19_UNDER_TEST`): `regress_pbs_settled_r13` 51/0 before and after; `regress_crashed_slot_r14` 70/1 before
  (the known stale 12-Oct replay) and 68/3 after - the two new failures are by design ("error stream not retrieved" and
  "Killed" now become operational losses instead of standing alarms). `test_designated_r16` was not run (it writes transient
  worlds inside `chpc/`).
- `chpc/migration_v19/test_migration_v19.py` on frozen fixtures (RSC `1a83cbf`): see that folder's `test_results.txt`.
- Re-run 21 Oct after the E2Q3 fold-in (RSC `fe94e78`): `test_v19_oploss` 76/0 (now with five pins and the E2Q3 files in its
  controls / grammar / live-tree checks), `test_v19_e2q3` 49/0 (s.7), `aws_ec2/tests/test_e2q_stage.py` 106/0,
  `test_migration_v19` 37/0, the regression counts identical, `build_v19 --check` and `promote_v19 --check` OK.

## 6. Limits and choices (where the rule is not the minimal literal reading)

1. **Crashed workers' coordinates stay `left`, not `uncompleted`.** Same planner effect (returned), smaller accounting change.
2. **Exit 75 with runner exit 75 is clean**, not dispositioned (it is the normal deadline resume).
3. **HELD jobs.** An exit-4 job whose crash evidence is missing (`.err` not retrieved, a SIGKILL "Killed", a status exit 4) is an
   operational loss and does NOT count toward RESCUE-PENDING; the repeat-crash rule counts evidenced signal crashes only, as
   before. A transient fetch failure therefore under-counts in that one receipt (crash history is recomputed every receipt).
4. **Still blocking by choice:** scheduler memory above 90 %, a recorded memory breach and a walltime-request mismatch (they also
   alarm clean jobs and signal a wrong envelope that would repeat the loss), and a temporary file at a no-status coordinate.
5. **Refit role only**; the bank (row 22) keeps its own rules.
6. **Downstream pins:** `aws_ec2/e2q_stage.py` now pins the v19 controls `111c3107` (21 Oct, section 7) and refuses until v19
   is promoted and deployed. `row19_screen_release.py` / `release_p80` bind the admission and controls: after v19 is adopted
   they must be re-pinned before their next use. E2Q1 and E2Q2 are both reconciled and dispositioned (no EC2 attempt or reaper
   is live as of 21 Oct 22:18Z), so the EC2 precondition of the migration holds; check it again at step 1.

## 7. E2Q3 on-demand qualifier (owner decision 21 Oct 2026)

**Decision.** Owner, 21 Oct 2026 ~23:5xZ (R052 chat, AskUserQuestion), answer "On-demand E2Q3": add an E2Q3 contract
(on-demand, about USD 116 at the listed rate, inside the USD 276 left of the USD 300 qualification allowance) to the v19 build
before it deploys, then launch. Operational change under the lean plan (owner 20 Oct): no Codex review of this tooling; Codex
reviews only the E2Q3 actual result. Brief: Unimog-Projects `prompts/2026-10-21_r052_e2q3_ondemand_job.txt`.

**Why.** E2Q1 (12.72 h) and E2Q2 (6.59 h, terminated 2026-10-21T22:18:18Z, USD 8.30) were both spot-interrupted with 0
records and dispositioned. Spot c7a.24xlarge in eu-north-1 lost 3 of the last 4 long runs; one interruption loses the whole
22 h bundle. The tools stopped a third attempt: two qualification instances, E2Q2 at most one, spot-only requests, no E2Q3
contract.

**What E2Q3 is.** E2Q2's geometry and roles exactly - c7a.24xlarge, 76 workers, 60 GB, 52 work (owned) + 20 Lengau duplicates
+ 4 token sentinels, the same declared panel `aws_ec2/prod/panel_e2q_e2.json` (`f04a5e43`, byte-unchanged), the funded
79,200 s lifetime - under its own contract name and run `qual-E2Q3`, bought ON-DEMAND. The qualification rule (R1'-R5', the
duplicates against Lengau, no retry by outcome, the certificate code set) is unchanged; only the contract set grows.

**The controls-pinned changes (chpc, in this folder).**

| File | Change |
|---|---|
| `row19_ec2_state.py` REVISION 5 | `CONTRACTS["E2Q3"]` = E2Q2's fields + `market="on-demand"`, `max_price=5.60` (the on-demand worst-case rate used for funding and every charge; eu-north-1 lists about 5.27). Earlier contracts gain no key (absent market = spot); `contract_market()` added. |
| `row19_ec2_e2qual.py` REVISION 2 | `CONTRACTS` / `RUNS` gain E2Q3 / qual-E2Q3. The panel declaration's own `contracts`/`runs` fields stay E2Q1/E2Q2 (`PANEL_CONTRACTS`, frozen), so the committed panel regenerates byte-equal. |
| `row19_ec2_ingest.py` REVISION 9 | `E2Q_CONTRACTS` gains E2Q3 (a RELEASED E2Q3 attempt takes the per-slot route under the same checks). |
| `manifest_e2q3_e2.json` (DATA) | the E2Q3 operational manifest, `make_prod_manifest.py --epoch 2 --contract E2Q3 --expect-s 75300` with the candidate modules (it re-derived and accepted the declared panel); promoted to the new path `aws_ec2/prod/manifest_e2q3_e2.json` and deployed to the controller clone with v19 (the qualifier reads it there and `e2q_stage` pins it there). |

`row19_ec2_qualify.py` is NOT changed: it reads `EQ.CONTRACTS` / `EQ.RUNS`, so under v19 it accepts `qual-E2Q3/<n>` with its
reviewed bytes (`1d8eee78`). The certificate's bound code changes (state, E2Q module, ingestion are in `row19_ec2_e2qual.CODE`),
which is what an E2Q3 certificate under v19 binds.

**The Mac tools (aws_ec2, edited in place).** None of them is pinned by the controls (only `aws_ec2/qual_S_plan.json` is), checked
per file on 21 Oct. Each loads against the v18 chpc modules too (no E2Q3 admission is possible before v19: `prod_launch` offers
only the contracts `row19_ec2_state` declares).

- `prod_authority.py` REVISION 9: `E2_MAX_QUAL_INSTANCES` 2 -> 3; `e2q_admission_problem` E2Q3 = its own permission record
  (`qualification_e2.e2q3`), every non-rejected E2Q1 AND E2Q2 attempt reconciled and dispositioned (at least one of each), at
  most one; the release branch: an E2Q3 certificate needs every E2Q1 and E2Q2 attempt dispositioned; `CRASH_EQUIVALENT_CONTRACTS`
  gains E2Q3; `release_state` derives `e2q3_ok`. Charging needed no change: `charged()` (and `bench_reaper.report_charge`) price
  every attempt at its own recorded `max_price`, so an on-demand attempt is charged at 5.60 USD/h.
- `prod_launch.py` REVISION 8: an on-demand contract's RunInstances request carries no `--instance-market-options`; a spot
  contract's request is byte-unchanged (`market_args`); the attempt records `market` (only when the contract declares one) and
  its `max_price`; the plan's `instance` carries the market.
- `qual_permit.py` REVISION 3: `--epoch2 --e2q3 --record prod/permit_e2q3.md` writes `qualification_e2.e2q3`, only after the
  epoch-2 qualification and E2Q2 are permitted; exclusive with `--e2q2`.
- `make_prod_manifest.py` REVISION 4: E2Q3 geometry (`E2Q3_GEOMETRY`: E2Q2's at 5.60, on-demand).
- `e2q_stage.py` REVISION 2: `RUNS` / `OPMANIFEST` / `DATA_PINS` gain E2Q3 and its manifest; `ADOPTED_CONTROLS_SHA` moves to
  the v19 controls `111c3107`. It refuses every run until v19 is promoted and deployed (intended).
- `e2q_stage_verify.py` REVISION 2: the expectation's contract may be E2Q3. These bytes are no longer identical to the reviewed
  `chpc/candidate_e2s` copy (`f742f017`): the difference is this contract tuple and its docstring.
- `aws_ec2/prod/permit_e2q3.md`: the E2Q3 permission record (drafted, NOT permitted: `qual_permit` was not run).

**Money.** Worst case `worst_usd(79200, 5.60)` = 22.75 h x (5.60 + 0.014) + 0.30 = **USD 128.02** (the brief's "~USD 116" is
22 h at the listed 5.274; the tool funds the 22.75 h ceiling at 5.60). Allowance: E2Q1 15.74 + E2Q2 8.30 + 128.02 = USD 152.05 of
300; the epoch cap, the USD 2,300 envelope and the USD 3,000 cap all hold.

**Departures from the brief, and why.**

1. **The funding declaration keeps `max_qualification_instances: 2`.** `funding_e2()` derived that field from
   `E2_MAX_QUAL_INSTANCES`; moving it to 3 would change `aws_ec2/e2_funding.json` (`d6f414e8`), which `e2q_stage`, every
   certificate and the permit records pin. A separate constant `E2_FUNDED_QUAL_INSTANCES = 2` keeps the declaration byte-equal;
   the counter that gates admissions and releases is 3. The declaration's rule says "a further attempt needs a new decision";
   the owner's 21 Oct decision is that decision.
2. **The panel file's `contracts`/`runs` fields still read E2Q1/E2Q2.** Regenerating the panel with E2Q3 in them would change
   its bytes (`f04a5e43`, pinned in `DATA_PINS` and bound by certificates); the brief requires the panel unchanged. No consumer
   reads those two fields (tested).
3. **`row19_ec2_qualify.py` is not changed** (it already reads the contract set from `row19_ec2_e2qual`).
4. **The E2Q3 manifest is generated into this folder and promoted with v19**, not written to `aws_ec2/prod/` now: it must be
   on the controller clone (the qualifier and `e2q_stage` read it there), so it travels as a v19 data row (the build_v17 pattern),
   and the live tree stays exactly v18 until the promotion.
5. **The worst case is USD 128.02, not ~116** (above).
6. The release-branch E2Q3 guard is checked statically (the full schema-3 certificate route is not rebuilt here); the
   admission, permit, money, launch and staging rules are exercised.

**Tests (`test_v19_e2q3.py`, `test_results.txt`).** 49 checks: the contract (E2Q2's geometry, on-demand 5.60; earlier
contracts byte-stable), the candidate files only add to v18 (line diff), the panel regenerates byte-equal, the release
constants and code set unchanged, the qualifier accepts the grown set, the manifest is the maker's bytes and E2Q1/E2Q2/
production still derive byte-equal, the plan contract; the admission (refused without its permit, before E2Q2 is
dispositioned, with no E2Q2, before E2Q1 is dispositioned, as a second E2Q3; a rejected E2Q3 does not count; E2Q1/E2Q2 stay
refused); the allowance arithmetic and its 1-cent refusal; the counter 3; the funding byte-equal; the crash envelope;
on-demand charging (authority and reaper agree); `qual_permit --e2q3` on a temporary release-state copy (refusals, the
written block, a record edited after permission reads as not permitted); `prod_launch` market arguments (every spot contract
byte-identical to the old request; on-demand none; unknown refuses) and full E2Q3 admissions on a synthetic state - dry run
authorised without market options, live admission journaled with max_price 5.60 / market on-demand and a request without
market options, a second E2Q3 refused, an E2Q2 admission on the same harness carrying exactly the old spot request, the two
requests differing only by the market arguments. `aws_ec2/tests/test_e2q_stage.py` gains the E2Q3 staging and qualify cases
and its pin checks follow v19.

**Live sequence still to run (in order; nothing of it was run here).**

1. Migration v18 -> v19 (`chpc/migration_v19/RUNBOOK.md`): operator controls record with
   `ADOPT row19-screen-controls sha256=111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5 version=19`, the
   `@record` pin, preflight, archive, promote (copies the five pins and the E2Q3 manifest, controls last), commit, deploy (9
   files), v19 receipts, pilot rollover and adoption.
2. `python3 aws_ec2/qual_permit.py --epoch2 --e2q3 --record prod/permit_e2q3.md`, then commit `ec2_release_state.json`.
3. `python3 aws_ec2/prod_authority.py budget`; `python3 aws_ec2/prod_authority.py inventory`; `python3 aws_ec2/ec2_sync.py
   cycle`; a fresh refit receipt (at most 2,700 s old).
4. `python3 aws_ec2/prod_launch.py --contract E2Q3 --epoch 2 --partition ../chpc/row19_partition_e2.json --manifest
   prod/manifest_e2q3_e2.json --panel prod/panel_e2q_e2.json --snapshot ../chpc/results/row19_screen --tarball
   ~/aws_t1_bench/t1_toolchain_lengau.tgz --dry-run`, then the same without `--dry-run` (one on-demand instance, worst
   USD 128.02). Check the account's eu-north-1 on-demand vCPU quota for the C family covers 96 vCPU before the live launch: the
   dry run checks permissions, not that quota.
5. Once reconciled: `python3 aws_ec2/ec2_sync.py cycle`, then `python3 aws_ec2/e2q_stage.py run --run qual-E2Q3 --attempt 1`,
   then certificate archival (condition A) and the Codex actual-result review before any release-adopt.

# Row 19 screen controls v19 - CANDIDATE, not adopted (the OPERATIONAL-LOSS disposition)

Written 20 October 2026 (R052 lean T1 plan item 2, owner-approved; Claude, bounded job). An operational change: no Codex review,
adopted by an OPERATOR record carrying the ADOPT literal. Nothing was promoted, deployed or run against Lengau, PBS or AWS; no
live file was edited. New bytes only in `chpc/candidate_v19_oploss/` and `chpc/migration_v19/`.

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
| `row19_screen_controls.json` | `4d868856905f914858ca224ec0dcb902792646f437fa4a9ddaa75d1b6d729a7d` |
| `v19_promotion_map.json` | `b3a1778c5bec64dac32ec62684cc23b85f45a13bf1789c0b370494a0ebef78b5` |
| `build_v19.py` / `promote_v19.py` | `c04a17eb…` / `b32e1617…` (the v18 base-first builder/promoter pattern) |

Controls v19 = adopted v18 `452b82df` versions 1-18 byte-equal + one version-19 entry: exactly two pins change (admission,
status); the v18 node-failure rule and capture pins, the other 15 pins, partition e2 `48cea639`, `sub_envelopes`,
`qualification_S`, programme and deployment equal v18. The operator adoption record must carry exactly:

    ADOPT row19-screen-controls sha256=4d868856905f914858ca224ec0dcb902792646f437fa4a9ddaa75d1b6d729a7d version=19

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

## 6. Limits and choices (where the rule is not the minimal literal reading)

1. **Crashed workers' coordinates stay `left`, not `uncompleted`.** Same planner effect (returned), smaller accounting change.
2. **Exit 75 with runner exit 75 is clean**, not dispositioned (it is the normal deadline resume).
3. **HELD jobs.** An exit-4 job whose crash evidence is missing (`.err` not retrieved, a SIGKILL "Killed", a status exit 4) is an
   operational loss and does NOT count toward RESCUE-PENDING; the repeat-crash rule counts evidenced signal crashes only, as
   before. A transient fetch failure therefore under-counts in that one receipt (crash history is recomputed every receipt).
4. **Still blocking by choice:** scheduler memory above 90 %, a recorded memory breach and a walltime-request mismatch (they also
   alarm clean jobs and signal a wrong envelope that would repeat the loss), and a temporary file at a no-status coordinate.
5. **Refit role only**; the bank (row 22) keeps its own rules.
6. **Downstream pins:** `aws_ec2/e2q_stage.py` pins controls `452b82df` (v18) and `row19_screen_release.py` / `release_p80`
   bind the admission and controls: after v19 is adopted they must be re-pinned before their next use. Promote v19 only after
   the running E2Q1 instance and its reaper are finished (after ~23:05Z 21 Oct) or with that re-pin prepared.

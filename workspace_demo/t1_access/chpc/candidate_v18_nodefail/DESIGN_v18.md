# Row 19 screen controls v18 - CANDIDATE, not adopted (the NODE-FAILURE disposition)

Written 20 October 2026 (R052, Claude, bounded job). For Codex's review. Nothing here is promoted, deployed, captured or run against
the world: no ssh, scp, Lengau, PBS or AWS operation was performed. No adopted or live file was edited: `chpc/row19_screen_*.py`,
the controls (v17 `9ea4e727`), the adoption record (`61ca680e`), the manifest and everything v17 pins were read only. The only new
bytes are in this folder.

## 1. The case

Refit job 54 = PBS `7551259.sched01`, plan `job_54` (sha256 `3081274f…`), 24 slots of one coordinate each (slots 0-14 = rep 5
indices 65-79, slots 15-23 = rep 8 indices 11-19), token `dd8d1b891252`. Facts, by source:

| Fact | Source |
|---|---|
| PBS state F, Exit_status 265 (256 + SIGKILL), resources_used.walltime 17:21:10 of 48:00:00, mem 41,763,220 kb of 120 GB, exec_host `cnode0240/0*24`, mtime 20 Oct 20:00:36 | the brief; the settle note and the receipt below agree on state, exit, walltime and memory |
| `pbsnodes cnode0240`: state down, comment "node down: communication closed", last_state_change_time 20 Oct 20:00:36 (the job's mtime to the second) | the brief only (not in any repository file) |
| Ledger entry SETTLED: 416.47 core-h, settled_at 20:19:21Z, note "refit job 54: qstat -xf Exit_status 265, resources_used.walltime 17:21:10, job_state F"; runner_started 00:19:41Z; NO runner_exit / runner_ended / runner_wall_s | local snapshot `chpc/results/row19_screen/live/refit/campaign/budget.json` |
| Statuses exist for slots 19 and 20 only, both exit 0 on host cnode0240, new [15] / [16], ended 13:31:28Z and 17:26:32Z; records and timings 8/15, 8/16 | local snapshot `root/status`, `root/records`, `root/timing` |
| The 22 other slots' logs hold only their header line (no exit line) | local snapshot `root/logs/job7551259.sched01.slot*.log` |
| No `row19_screen_refit_54.out` / `.err` (scp: No such file or directory) | `live/refit/jobs/_fetch.json` |
| Receipt `watch_refit_20261020T201925Z.json`: fresh, production, 24 alarms - all job 54's (exit 265, no runner end, 22 missing statuses); `disposition_held` "status evidence scoped to 7551259.sched01: [slot19, slot20]" | `chpc/results/row19_screen/receipts/` |

**I can't determine the time zone of the printed 20:00:36.** The brief writes "20 Oct 20:00:36"; the R052 log writes "20:00:36Z".
qstat and pbsnodes print the login node's local time. If that is SAST, the job ended 18:00:36Z, ~20 min after the last mom
walltime update (stime + 17:21:10 ≈ 17:40Z); if UTC, 2 h 20 min after it. The design does not depend on which: the capture
script runs qstat/pbsnodes as its own subprocesses and records the UTC offset of that same process, and the validator recomputes
every epoch from the printed string and that offset. Both readings pass the rule (test part 1).

Why neither existing class fits: closed-no-record (REVISION 8) needs NO status scoped to the job and a retrieved PBS output with no
ADMISSION FAILED; the crashed-worker slot disposition (REVISION 14) needs scheduler AND runner exit 4 and one fatal-signal line per
missing slot in a retrieved `.err`. A lost node gives exit 265, no runner end, no `.out`/`.err`.

Consequence today: every refit receipt carries these 24 alarms, `receipt_problem` refuses ("the newest receipt has alarm(s)"), and
no refit refill is admitted. The 22 coordinates are already out of flight (the entry is settled), so the planner would re-plan
them; only the receipt gate holds.

## 2. The rule (`row19_screen_nodefail.node_failure_evidence`, ONE implementation)

The status view calls it to report and un-alarm; the admission recomputes it from the current ledger, root, retained verifier
units and the evidence file on disk, and requires the receipt's disposition EXACTLY equal (the REVISION 14 pattern). Granted only
when ALL hold:

1. **Scheduler.** State F; integer, non-boolean exit in `KILL_EXITS = (265,)`.
   - 265 = 256 + 9: PBS's SIGKILL of the job, which is what the server does when it loses the execution host.
   - 271 (256 + SIGTERM) is excluded. It is the walltime-kill signature (job 3), and a walltime kill is never infrastructure.
   - Every other code is excluded too, including PBS's negative JOB_EXEC_* codes, until one is observed with a node loss.
2. **Ledger.** The entry carries all of these:
   - SETTLED, with its certificate: finite charge, a note of at least 8 characters, a non-negative time;
   - the note's `Exit_status` equal to the observed exit;
   - NO runner end (`runner_exit`, `runner_ended` and `runner_wall_s` all absent: job-end never ran);
   - a finite `runner_started` (job-start ran, so this is not an admission failure);
   - token, PBS id and job equal to the plan's.
3. **Node evidence** (`<toolchain>/jobs/row19_screen_refit_<n>.nodefail.json`; strict validator `evidence_doc_problem`):
   - **Form.** Schema `row19-screen-nodefail-1`, exactly the declared keys at every level, at most 4,096 bytes. Every string is
     at most 160 characters on one line, with no `key = value` text and no `Job Id:`, so raw scheduler output is refused in any
     shape. No NaN or Infinity.
   - **Provenance.** `capture_sha256` must equal the latest controls version's pin of `chpc/row19_nodefail_capture.py`. Under
     v17 there is no pin, so the class never applies.
   - **Identity.** The job, PBS id, role, state F and exit are the ledger's and the observation's.
   - **One node.** exec_host names exactly ONE node, and that is the captured node.
   - **Node down at the job's end.** pbsnodes state contains `down`; `|last_state_change_time - mtime| <= NODE_TOL_S = 120 s`;
     the capture is not older than either.
   - **Times recompute.** Every printed time recomputes to its recorded epoch under the recorded UTC offset, and both
     walltimes to their recorded seconds.
   - **Not a walltime kill.** The walltime used is below the request less the deadline reserve (the plan's envelope, 1,800 s),
     and the request is the plan's.
   - **Time order.** stime - 120 <= runner_started <= mtime + 120; walltime used <= mtime - stime + 120; settled_at >= mtime - 120.
   - **No staged-out output.** No PBS `.out`/`.err` existed at capture.
4. **Slots.** Every planned slot either:
   - has a **COMPLETED** status: readable; this job and slot; exit 0 (not boolean); `left` []; rep and indices the plan's;
     new + resumed exactly the indices; host the down node; `ended` <= mtime + 120. Each of its coordinates must be a valid
     verified record with valid timing, and a NEW coordinate's timing must name this job and slot. These records are KEPT as
     done.
   - or has **NO status at all**.

   Any other status refuses the whole class: exit 75 / work left (partial), exit 4 (HELD), any other exit, wrong assignment or
   unreadable. The statuses scoped to the PBS id must be exactly the completed ones: no unplanned slot and no temporary name.
5. **No-status coordinates.** Each must satisfy all of these:
   - no verifier unit naming the job;
   - no temporary or non-canonical file;
   - no record or timing, except a LATER bound job's verified planned completion (the R1 rule);
   - the worker log, if present, carries no `worker job <id> slot <s>: exit` line.

   Separately, EVERY timing file naming the PBS id must be a completed worker's planned coordinate in its slot, at its canonical
   path (the V15-1 rule).

**Granted.** The summary carries `node_disposition`:
- **What it records:** kind, PBS id, scheduler exit, runner exit None, the settlement certificate, plan sha256, evidence file and
  sha256, the node, its state and comment, both epochs and their difference, walltime used, completed/no-status slots,
  completed/uncompleted coordinates, and `counts_as_crash: false`.
- **What changes in the receipt:** ONLY three kinds of alarm are not raised: the scheduler-exit alarm, the missing-runner-end
  alarm, and the no-status slots' missing-status alarms.
- **What stays the same:** the completed slots are reconciled exactly as ordinary workers, and every other alarm stands (memory,
  walltime request, bindings, survivor checks).
- **The coordinates:** the no-status coordinates are `uncompleted` with origin `node-failure`. They are neither done nor in
  flight, so the unchanged planner returns them to the pool.

**Not granted.** `node_disposition_held` keeps the reason, and all alarms stand.

**Never a crash.** `crash_history` reads `slot_disposition` (kind crashed-worker-no-status) only. A node failure therefore never
counts toward the two-crash RESCUE-PENDING rule, and `held_accounting_problem` (runner exit 4) never asks for one.

**Never a pilot.** `job_summary_problem(pilot=True)` refuses it ("a node-dispositioned job never qualifies a pilot"), and so does
the status view's `--qualify`. Nothing is credited; the 416.47 core-h stay charged.

## 3. What changes, file by file

| File | SHA-256 | Change |
|---|---|---|
| `row19_screen_nodefail.py` | `96af406e3550c62e524ea39d1e863797fcd55fb058ecff3370724737f817914d` | NEW: constants, strict evidence validator, the shared rule |
| `row19_nodefail_capture.py` | `84d52bdfc31725182f7bad53caf1bee88ecf01e1e474a7545b1c3971f655bc9c` | NEW: the owner's Lengau capture script (s.4) |
| `row19_screen_status.py` | `4710544a3861b688b0f2c89e67a8ba56cf65261a8900d4147658fee576f58232` | v17 `a9f9180b` + REVISION 18 (`status_v17_to_v18.diff`, +64 / -6) |
| `row19_screen_admit.py` | `e22607650058ae2cbb8f19fe3e225d886bd2cc733adf02bb93dbc01d65f719af` | v17 `c3960464` + REVISION 18 (`admit_v17_to_v18.diff`, +106 / -0) |
| `row19_screen_controls.json` | `80214d80c6c4e093ed72a47f19bc875daaf686e19f837b13cb20d604b571fd93` | adopted v17 bytes + ONE appended version-18 entry (`build_v18.py`) |
| `v18_promotion_map.json` | `d96270d65c08d4d61a3e6cd0884f18b5c1ea797c0c21181eb298d106f08e39ed` | the four promoted files + controls, previous bytes, order |
| `build_v18.py` | `41f348c26f6f5bc53c807cd503cd22001caf7d085b5b8114406dcbbd5cfba09f` | deterministic builder, `--check` |
| `test_v18_nodefail.py`, `test_results.txt` | - | 111 checks; regression counts (s.6) |

**Status view (REVISION 18).** Five changes:
- **`fetch_job_outputs`.** For a settled refit entry with no runner end whose note's Exit_status is in the kill set, it also
  scp-retrieves the evidence file. The result goes in `_fetch.json` under `"<n>.nodefail"`.
- **`node_failure()`.** It calls the rule on the fetched bytes.
- **`reconcile`.** The three alarm conditions gain `not ndispo` / `not in nodeless`, and the partition records origin
  `node-failure`.
- **The receipt.** It binds `bound.node_evidence = {n: {file, sha256}}`, retains a copy beside the receipt, and prints
  `DISPOSITIONED (node-failure): ...`.
- **`--qualify`.** It refuses a node-dispositioned job.

**Admission (REVISION 18).** Six changes:
- **`node_disposition_problem`.** The exact recompute, the bound and unchanged evidence bytes, and the certificate. It refuses
  when the job's `.out` or `.err` exists NOW (PBS staged the job out after all; reclassify).
- **`job_summary_problem`.** Pilot refusal. The node summary must be F with the kill-set exit, no runner exit, the completed slots
  all `0` with nothing left, and finite memory (worker memory may be absent only when no slot completed).
- **`units_problem`.** It subtracts the uncompleted coordinates.
- **`transition_problem`.** It checks SETTLED, no runner end, the same certificate and PBS id.
- **`receipt_problem`.** A new branch, and a refusal of any summary that carries more than one disposition key.
- **Module docstring.** A REVISION 18 note.

The REVISION 8 and 14 code paths are byte-unchanged.

## 4. The operator command (the owner, on Lengau; CHPC Accounts Policy v2.8 s.2.2(6): no AI agent operates there)

After v18 is promoted and deployed, the capture script is the pinned file in the controller clone:

    cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access
    /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_nodefail_capture.py --manifest chpc/row19_screen_manifest.json --role refit --job 54 --dry-run
    /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_nodefail_capture.py --manifest chpc/row19_screen_manifest.json --role refit --job 54

**What it does.**
- It reads the ledger entry and refuses on a runner end.
- It runs `qstat -xf 7551259.sched01` and `pbsnodes cnode0240` once each, and extracts the needed fields.
- It records each raw output's SHA-256 and never the output itself.
- It records whether the `.out`/`.err` exist.
- It self-checks with the same strict validator.
- It writes `/mnt/lustre/users/pvanrooyen/t1_toolchain/jobs/row19_screen_refit_54.nodefail.json` with an exclusive create
  (never overwritten), then prints the document and its SHA-256.

**When it refuses (nothing written):**
- PBS history no longer holds the job ("Unknown Job Id");
- the job is not F;
- the job ran on more than one node;
- **the node is no longer down**;
- the time offsets disagree;
- the evidence file already exists.

**Then.** The next `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit
--publish-receipt` (Mac) pulls the file and prints:

    refit job 54 7551259.sched01 PBS F exit 265: workers ended 2/24 exits {'0': 2}, new 2 resumed 0 left 0
        DISPOSITIONED (node-failure): scheduler exit 265 kept, no runner end; node cnode0240 down (node down: communication closed)
        changed +0 s from the job's end; completed slots [19, 20] kept (2 record(s)); 22 coordinate(s) of no-status slots
        uncompleted (node-failure, returned to the planner, not a crash); settled 416.47 core-h charged; evidence
        row19_screen_refit_54.nodefail.json <sha12>

On the 20 Oct 20:19Z snapshot this yields zero alarms (test part 5). The receipt gate can then pass.

**TIME-CRITICAL - the evidence can only be captured while BOTH of these hold:**
- (a) PBS history still holds 7551259 (a few days: REVISION 11 notes the expiry);
- (b) cnode0240 is still `down`. Once CHPC returns it to service, its `last_state_change_time` no longer dates the loss.

v18 review, promotion and deployment will likely take longer than that window. The capture script is read-only towards PBS, the
ledger and the root, and it writes one file that nothing in v17 reads (v17 fetches only `.out`/`.err`; `toolchain/jobs` is
outside the controller clone `ctl_clean` checks). So the owner can run the CANDIDATE script NOW from a staging folder, if the owner
chooses (choice 1):

    mkdir -p /mnt/lustre/users/pvanrooyen/t1_toolchain/nodefail_stage        # then copy the two candidate files there from the Mac:
    scp chpc/candidate_v18_nodefail/row19_nodefail_capture.py chpc/candidate_v18_nodefail/row19_screen_nodefail.py chpc-scp:/mnt/lustre/users/pvanrooyen/t1_toolchain/nodefail_stage/
    cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access
    /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py /mnt/lustre/users/pvanrooyen/t1_toolchain/nodefail_stage/row19_nodefail_capture.py --manifest chpc/row19_screen_manifest.json --role refit --job 54 --dry-run

The dry run's printout is itself useful to the review: it shows the real field formats. The evidence then carries the CANDIDATE
script's SHA-256 (`84d52bdf…`). If Codex changes the capture script, its pin changes and that evidence no longer matches (choice 1).

## 5. Receipt and pilot

- **Receipt fields.**
  - `jobs.<n>.node_disposition` (or `node_disposition_held`);
  - `partition.uncompleted` / `uncompleted_origin: "node-failure"`;
  - `bound.node_evidence`;
  - a retained copy `row19_screen_refit_<n>.nodefail.json.<stamp>` beside the receipt.
- **Unchanged.** The receipt and qualification schemas are unchanged: new keys only. `bound_problem` ignores keys it does not
  check.
- **Never a pilot.** A dispositioned job never qualifies a pilot (admission `job_summary_problem(pilot=True)`, status
  `--qualify`). The pilot is job 1 in any case.

## 6. Tests (`test_results.txt`)

- **`test_v18_nodefail.py`: 111 passed, 0 failed.** Five parts:
  - **Shared rule (61).** The job-54 positive on the REAL local plan, ledger entry and slot-19/20 statuses, plus the refusals the
    brief names:
    - node not down;
    - time mismatch (+600 s, -1 h);
    - exit 4;
    - a partial status;
    - unsettled ledger;
    - raw capture (five shapes).

    It also covers about 40 further refusals (s.2 conditions), the later-completion allowance, a UTC-printing host and every
    worker lost.
  - **Status view (11).** The 24 alarms gone and nothing else raised. Each failure mode keeps every alarm with its reason. The
    memory alarm is kept. The fetch condition.
  - **Admission (20).** The exact recompute and the summary checks. NEVER a pilot. Units, transition, the crash rule untouched,
    held accounting. Refusals: tampered bytes, a later `.out`, edits, unbound evidence, two dispositions, a certificate change,
    a later runner end, an orphan timing, v17 controls (no pin).
  - **Capture script and controls (16).** The capture from modelled PBS Pro text, end to end through the rule, plus its
    refusals. Controls v18: versions 1-17 byte-equal, exactly four pins changed. `build_v18 --check`; Python 3.7 grammar; the
    live tree untouched.
  - **REAL replay (3).** The 20 Oct 20:19Z snapshot with modelled evidence: zero alarms, and the other 55 jobs' outcomes equal
    the v17 receipt's.
- **Regression, live v17 against v18:**
  - `regress_crashed_slot_r14`: 70/1 both (the same stale 12-Oct replay);
  - `regress_pbs_settled_r13`: 51/0 both;
  - `test_designated_r16` in transient worlds: 76/4 against 77/3. Every difference is a check of the controls file's last
    entries; every code check is identical.
- **Not tested.**
  - a real capture: the qstat/pbsnodes text formats are modelled on PBS Pro, not observed here, so the dry run is the first real
    test;
  - the full `main()` receipt path (pull, producer verifier, gate copy);
  - EC2 reconciliation, which is stubbed in the replay as in the r14 replay;
  - promotion, deployment and the rollover.

## 7. What a v18 promotion pins, and the migration honestly

**Pins (v18 `files`).** Four entries change against v17; everything else is byte-equal to v17. That includes the other 15 pins,
the partition `chpc/row19_partition_e2.json` `48cea639`, `sub_envelopes`, `qualification_S`, `programme` and `deployment`.

| Pin | v17 | v18 |
|---|---|---|
| `chpc/row19_screen_admit.py` | `c3960464` | `e2260765…` |
| `chpc/row19_screen_status.py` | `a9f9180b` | `4710544a…` |
| `chpc/row19_screen_nodefail.py` | - | `96af406e…` (NEW) |
| `chpc/row19_nodefail_capture.py` | - | `84d52bdf…` (NEW) |
| `chpc/row19_screen_controls.json` | `9ea4e727` | `80214d80…` (the controls, not a pin) |

**Proposed ADOPT literal** (it authorises nothing until a FAVOURABLE review issues it):

    ADOPT row19-screen-controls sha256=80214d80c6c4e093ed72a47f19bc875daaf686e19f837b13cb20d604b571fd93 version=18

**Is there a lighter "v17.1"? No, not inside the reviewed contract.** Three reasons:
- **Versions are integers.** Controls versions are integers, and lineage requires every controller tree to hold exactly the
  LATEST version's pins. Any byte change to the admission or the status view therefore means a new version.
- **A new version changes the generation.** The producer verifier stamps the latest version, and `generation_problem` requires
  it. A new version therefore invalidates the v17 pilot qualification `8fdbf48e` and its adopted review for the refit gate,
  exactly as v16→v17 did.
- **No other way to clear the alarms.** No data-only route clears them either: the alarms come from code. Editing the ledger,
  statuses or plans, or relabelling, is forbidden, and closed-no-record cannot be satisfied because statuses exist and no
  `.out` exists.

So v18 needs the full rollover pattern. It is, however, much LIGHTER than v17's migration:
- **No new data.** No partition, data, Mac `aws_ec2/` code or epoch activation.
- **Archive.** The v17 bytes of the two replaced files, the v17 controls and adoption, the v17 pilot qualification `8fdbf48e`
  and the budget phases.
- **Promote and deploy.** Four files plus the controls, adoption and review record, in one controller commit (the
  `migration_v17` deploy pattern).
- **Fresh receipts.**
- **Pilot rollover.** ONE regenerated qualification of the existing job 1 (no fit, a new hash), a NEW Codex pilot literal and
  `adopt_pilot`.
- **Re-pin elsewhere.** `row19_screen_release.py` `CONSUMER_FILES` lists the admission and the controls, so the release
  consumers (`release_p80`) must re-pin separately before any numerical release (as at v17).

The `migration_v17` scripts are the template, but their package identities and inventories are v17-specific. A `migration_v18`
package needs its own preflight, archive, deploy and rollover scripts and its own scripts review. **It is NOT built here.**
`promote_v18.py` and the archive branch of `build_v18.py` are not built either: they wait for Codex's ruling on this design, so the
pinned bytes do not churn under the migration scripts.

**Refit admission meanwhile.** It stays held by the 24 alarms. Running jobs continue. The bank (row 22) has its own status and
gate and is not affected by this disposition.

## 8. Choices for Codex

1. **Capture timing against pin binding.** Which of these should hold?
   - (a) The evidence must carry the v18-pinned capture hash (as built). Then a capture made now with the candidate script
     stays valid only if the script is adopted unchanged.
   - (b) v18 pins an explicit accepted-capture list, so evidence from a reviewed earlier capture-script hash stays valid.
   - (c) Drop the hash condition and rely on the strict schema alone.

   Recommendation: (a), with the owner capturing NOW from the candidate (s.4). If Codex then changes the script, use (b) for
   exactly that one hash.
2. **The kill set** is {265} only. Should negative PBS JOB_EXEC_* codes or 271 with a node down be admitted? Both are excluded
   as built: 271 is the walltime-kill signature, and the walltime check would still separate them.
3. **`NODE_TOL_S = 120 s`** for node-change against mtime (and the clock slack elsewhere). Job 54 shows 0 s.
4. **pbsnodes `comment` is recorded, not required.** Requiring "node down" text would break when CHPC staff overwrite the
   comment.
5. **A survivor must be exit 0 with nothing left.** An exit-75 slot (deadline, work left) refuses the class rather than being
   kept as partial. Alternative: allow 75 with its left coordinates returned too.
6. **Zero completed slots is allowed** (all 24 uncompleted). Alternative: require at least one survivor. That would leave a
   whole-node loss with no class: closed-no-record needs a `.out`.
7. **A `.out` appearing later refuses** at admission (reclassify). Alternative: allow and bind it.
8. **The evidence lives in `toolchain/jobs`** beside the missing `.out`, outside the root, so the verifier, root pulls and
   `ctl_clean` are untouched. Alternative: `<root>/gate/`.
9. **Refit role only.** The originals role and the bank keep their current rules. A bank node failure would need the same
   class in `row22_bank_status`.
10. **`node_disposition_held` is recorded** on every terminal refit job without a runner end that is not closed-no-record. That
    is informational, like `disposition_held`.
11. **The no-status slot's log check** (no "exit" line) reads `root/logs`, which the status view already pulls. It is an extra
    guard, not in the brief.

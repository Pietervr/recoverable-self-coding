# Row 19, stage 1: the operator's launch procedure (R052)

Codex is on board with the staged slice at RSC `669153d`/`65fd31f` (record `reviews/2026-10-02_row19_launch_spec_rev6_codex_record.md`).
Nothing below runs before its three prerequisites: the watch expectations appended, stage 0 settled, the owner's row-specific go.
Every command is run by R052 on the login node (`ssh lengau`) unless marked Mac. `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`;
the clone is `$T/rsc_slice` (HEAD must be the reviewed candidate's commits, verified by the pinned hashes); the campaign is
`$T/row19_campaign`; `t1py` is the pinned wrapper.

## 0. Prerequisites (in this order)

**Endpoint declared 3 Oct after stage 0** (one layer under the policy = 33,635 s; every resample is one layer): the control runs to `--until 8` with C1 and C3 on `seriallong` 144 h; C2 and the W_int rule are unchanged. The addendum below is applied.

1. **Stage 0 settlement.** When `7516261.sched01` ends: `qstat -xf 7516261` → `resources_used.walltime`, `Exit_status`; then
   `$T/t1py chpc/row19_ledger.py --campaign $T/row19_campaign settle --job-id 7516261.sched01 --walltime-s <seconds> --cores 1 --note "qstat -xf: walltime HH:MM:SS, exit N, <how it ended>"`.
   Record the policy-cost result in ledger row 19 (Unimog) first.
2. **The addendum.** From stage 0 (a planning proxy for the first-record allowance only): `--expect-original-s` = the measured
   original-fit seconds × 1.5; `--expect-fit-s LO HI` = 0.2× and 3× the measured median per-member refit seconds. Append them to
   `row19_slice_manifest.json` under `live_evaluation.watch_arguments` and to row 19. Note: W_int is NOT in the addendum; it comes
   from C1 (step 3).
3. **The owner's go**, verbatim with its date, recorded in row 19 and the work item.

## 1. Launch C1 and main reps 0, 1, 2 (each: reserve → fill → qsub → bind)

For `KIND REP WALL` in `c1 0 518400`, `main 0 518400`, `main 1 518400`, `main 2 518400`:

```sh
cd $T/rsc_slice/workspace_demo/t1_access
TOKEN=$($T/t1py chpc/row19_ledger.py --campaign $T/row19_campaign reserve --kind KIND --rep REP --cores 1 --walltime-s WALL --root ROOT | awk '{print $2}' | tr -d :)
#   ROOT = $T/row19_slice (main) or $T/row19_slice_ctl_normal (c1)
# fill the template: main -> __REP__, __ATTEMPT__ (1), __TOKEN__;  c1 -> __MODE__=normal, __KIND__=c1, __KILL_FLAG__ (empty), __WALLTIME__=144:00:00, __WALLTIME_S__=518400, __ROOT__=row19_slice_ctl_normal, __QUEUE__=seriallong, __UNTIL__=8 (the manifest's control.target), __TOKEN__
JOB=$(qsub $T/jobs/<filled>.pbs)
$T/t1py chpc/row19_ledger.py --campaign $T/row19_campaign bind --token $TOKEN --job-id $JOB
```

Then (Mac) the first watch within 15 minutes, and every 2 hours while any reservation is live:
`python chpc/row19_watch.py --manifest chpc/row19_slice_manifest.json --qstat --expect-original-s S --expect-fit-s LO HI`.
Exit 1 = an alarm: submit nothing further until it is diagnosed and recorded in row 19.

## 2. C2 after C1's first records

When C1's `status`/`timing_0.jsonl` show the original and three resamples: `W_int = original_seconds + 3 × median(first three
fit_seconds)`, rounded up to the minute, and in any case between original + 1 and original + 7 resamples and below 48 h. If no
legal W_int exists, STOP and record non-qualification (never a cooperative or wrong-boundary C2). Reserve `c2` with
`--walltime-s W_int` in root `$T/row19_slice_ctl_interrupted`; fill `__MODE__=interrupted`, `__KIND__=c2`,
`__KILL_FLAG__=--pbs-kill-control`, `__WALLTIME__`/`__WALLTIME_S__` = W_int; qsub; bind.

## 3. C3 after C2's actual PBS kill

When PBS reports C2 finished: `qstat -xf <C2 job>` → `Exit_status`, `resources_used.walltime`; on the Mac,
`checkpoint_state` of C2's checkpoint (through `row19_watch.py`'s snapshot) gives `accepted_records_before` and whether a tail
fragment is present. Write `$T/row19_slice_ctl_interrupted/c2_interruption.json`:
`{"job_id", "exit_status" (int), "walltime_requested_s", "walltime_used_s", "pbs_killed" (bool), "accepted_records_before" (int),
"original_cache_reused" (bool, from C3's status after it runs), "tail_fragment_present" (bool)}`. Settle C2 with its note.
Reserve `c3` (144 h, seriallong) in C2's root; fill `__MODE__=resume`, `__KIND__=c3`, `__KILL_FLAG__` empty; qsub; bind.

## 4. Resumes, stops, settlement

- A main job that exits 75 is resumed with a NEW reservation (`--kind main --rep N`, attempt ≤ 4) and the next `__ATTEMPT__`.
- A stop: `$T/t1py chpc/row19_ledger.py --campaign $T/row19_campaign stop [--rep N]`; the runner acknowledges at its next record
  boundary (STOP_ACK_rep<N>.json names the request id); clear with `stop-clear` before any resume.
- Every ended job is settled from `qstat -xf` with a technical note; a killed or vanished job keeps its full reservation until then.
- Pull everything after each poll (the watch does); Lustre purges at 90 days.

## 5. The slice report (before stage 2)

On the Mac: `python chpc/row19_control_compare.py --manifest ... --task <C1 task_0.json> --c1 <C1 ckpt> --c3 <C3 ckpt>
--status-c1 ... --status-c3 ... --interruption <c2_interruption.json> --ledger <budget.json> --target 8`; per dataset the
per-resample distribution, the original fit, peak memory, utilisation, resamples per job, resumes and recovery counters; the
measured chain time against 144 h; the cost against the cap; figure and interpretation; to Codex before stage 2 is costed.

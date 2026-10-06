# Row 19, stage 1 (the slice): amended execution and recovery report

R052, 6 October 2026 (evidence: the slice watch's fresh snapshot of 6 Oct 21:10 UTC, the campaign ledger, qstat -xf at each
settlement, the jobs' logs). Scope as amended by the owner (5 Oct, "Yes, drop the control") and Codex RSC 0be5547: an
honest execution/recovery report. It reads NO coverage and admits nothing.

## What was planned and what changed
The slice ran three fresh M2S omega = 1 datasets (seed base 20261003, reps 0-2) through the refit chain under the section 7.4
start policy at B = 200, one sequential process per dataset on `seriallong` (144 h), plus a recovery control: C1
(uninterrupted reference to index 8), C2 (deliberately killed at a computed walltime) and C3 (resume). **The original control
is NOT qualified:** C1 died of the failure below after two records, C2 and C3 were never run, and the owner dropped C2/C3 on
5 Oct. Its frozen contract (`chpc/row19_control_compare.py`: exact indices 0..7, a PBS walltime kill, resumed counts) is not
met by anything here, and nothing is relabelled to meet it.

## The failure and the recovery, per dataset
Every long sequential process died with exit 139 after an XLA/LLVM "Cannot allocate memory", resident memory about 2.6 of
8 GB, on two different nodes (cnode0941, cnode0885) - five of five so far. The cause is a HYPOTHESIS (per-process memory-map
exhaustion by repeated compilation; vm.max_map_count 65,530 was read on a login node, not a compute node). Each crash was
settled from `qstat -xf` (allocated walltime x cores) and the dataset resumed from its fsynced checkpoint and cached original.

| Dataset | Attempt / job | Ran | Records saved (index, finished UTC) | End |
|---|---|---|---|---|
| rep 0 | 1 / 7516928 | 3 Oct 03:22 - 5 Oct 12:5x | 0 (4 Oct 11:55), 1 (5 Oct 03:23) | exit 139 at 57.5 h; ~9.5 h of resample 2 lost in flight; settled 57.52 |
| rep 0 | 2 / 7521637 | from 5 Oct 14:40 | 2 (6 Oct 21:04) | running |
| rep 1 | 1 / 7516929 | 3 Oct 03:22 - 5 Oct 07:3x | 0 (4 Oct 14:18), 1 (5 Oct 06:32) | exit 139 at 52.2 h; ~1 h lost; settled 52.23 |
| rep 1 | 2 / 7520953 | from 5 Oct 08:42 | 2 (6 Oct 15:20) | running |
| rep 2 | 1 / 7516930 | 3 Oct 03:22 - 4 Oct 21:0x | 0 (4 Oct 13:51) | exit 139 at 41.7 h; ~7 h lost; settled 41.68 |
| rep 2 | 2 / 7520111 | 4 Oct 22:39 - 6 Oct 11:33 | 1 (5 Oct 15:13) | exit 139 at 36.9 h; ~20 h lost; settled 36.91 |
| rep 2 | 3 / 7522581 | from 6 Oct 11:49 | - | running, the first job on the recycling template (one fresh process per resample, Codex e98df5f) |
| C1 (rep 0's dataset) | 7516927 | 3 Oct 03:22 - 5 Oct 12:5x | 0, 1 | exit 139 at 57.5 h; settled 57.53 |

Every resume restored its checkpoint with no rejected, damaged or tail-repaired record and reused the cached original (each
resumed log prints "original run: ... (cached)"; no `--authorize-original-recompute` was ever used); watermarks 3 / 3 / 2
match the accepted records. The first newly computed post-resume indices are rep 0 index 2, rep 1 index 2 and rep 2 index 1.
Lost work is the resample in flight at each crash (no partial record survives; none was needed). Charges settled so far
(slice campaign ledger): 255.7 core-hours, including stage 0 (9.85); 432 reserved for the three running mains.

Two operational events: Lustre's oss7/oss8 pair overloaded on 5-6 Oct (CHPC confirmed and cleared it); the two jobs then
running lost about 13 h each to I/O waits, so rep 0 index 2 and rep 1 index 2 took 109,366 s and 110,117 s of wall (CPU
19.4 h and 13.4 h of 32.5 h and 26.5 h): wall, not computing, above the 100,848 s ceiling, and reported as such.

## Parity: what is established and what is not
- **Before any crash:** C1 and main rep 0 computed the same dataset independently; their records 0 and 1 are bit-equal on
  the canonical scientific payload (two jobs, same node class). This is bounded stored repeatability on two indices.
- **Shard route:** the 24-core pilot's records equal the sequential records at the overlapping index 0 of each of the three
  datasets, float bits included (qualification 232dd924, Codex bc0523b).
- **NOT established:** parity of any newly computed POST-RESUME record against an independent counterpart (rep 0 index 2,
  rep 1 index 2, rep 2 index 1 have none), fresh-process equivalence after recycling, or a qualified PBS-kill recovery.
  The resumes show operational restoration only.

## Timings and memory
Clean resamples on one shared core took 55,665-64,972 s (15.5-18.0 h; median about 61,000 s); the packed pilot's took
84-88 ks (about 25 core-hours a resample); peak resident memory 2.1-2.6 GiB, far below the 8 GB request.

## What it means for stage 2
The refit chain runs and resumes correctly across jobs and nodes; a single long process does not survive more than about
two resamples, so the screen runs one resample per process (the shard worker, as built). The slice reads no coverage.

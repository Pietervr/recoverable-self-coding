# Stage A (row 20): the run of 2 October 2026 - STOPPED by a controller race after the instrumented phase

R084, 2 October 2026. Executed under the owner's go ("go for Stage A and the reader qualification, 2 October",
`stimuli/photo/ROW20_GO.json`, RSC `6ca6fb0`; the owner's words verified as their own turn in R052's chat at 15:26:49
MDT), on RSC HEAD `fa6aaa1` whose bound photo files equal the reviewed package at `fbfb7db` (only the two go files
differ; photo directory clean). Command: `.venv-image/bin/python stimuli/photo/stage_a_controller.py run`
(22:29:24-22:32:58 UTC). Every record below is copied into `2026-10-02_stage_a_run/`; the 304 MB of pass arrays stay
in `captures/photo_stage_a/` (gitignored), every file's size and sha256 in `captures_manifest.json` (335 files).

## Outcome

**STOPPED, terminal, not admissible as a PASS; no fidelity result.** Exit 0 (STOPPED is exit 0).

- gates: PASSED (worker exit 0).
- instrumented: COMPLETE - 158 of 158 planned unique attempts started and completed; worker exit 0;
  `INSTRUMENTED_DONE.json` written.
- then the controller stopped: `ControllerStop: instrumented: watchdog exited (0)` (TERMINAL.json first reason) -
  the native phase never ran.
- report: ran, and was itself stopped by the same cause (`report: watchdog exited (0)`); its report and receipt were
  written but are not current (`report_problems`: the report worker did not exit 0; a report stop).
- validator: FAIL, 42 failures - every one is the missing native phase (20 NOT_COMMITTED, 20 PARITY_INPUTS_MISSING,
  NATIVE_DONE missing, parity count 0). The native-parity table is empty and both figures are empty frames.

## Resources (measured, this session)

| Quantity | Value | Limit |
|---|---|---|
| Stage A seconds (this session, incl. the 60 s charged closure) | 249.2 s | cumulative 2,057.9 s of 14,400 s |
| row-20 forwards (carry 16 + 158) | 174 started, 173 completed, 1 failed (the carried engineering attempt) | 200 |
| task memory (Σ lifetime, the instrumented phase) | 33,317,693,192 B = 31.0 GiB | stop 44 GiB, cap 48 GiB |
| guardian lifetime max / controller final | 59.1 MiB / 63.7 MiB | in the aggregate |
| storage | 317,524,559 B | 1 GiB |
| Stage B projection (preliminary, whole-stage rates) | 2,212 s, 3.73 GB | 11,520 s, 6.87 GB |

## The cause (diagnosed; code defect, not a resource or fidelity limit)

`stage_a_controller._sample` (bound file) raises `watchdog exited` when the phase watchdog has exited and the
kqueue has not yet reported the worker leader's exit. The watchdog retires (exit 0) once `proc_info` no longer
answers for the group's processes. A worker that exits with a large address space (31 GiB here; 0.7 GiB for the
report) stops answering `proc_info` while its teardown is still running, before NOTE_EXIT is posted - so the
watchdog's ordinary retirement wins the race and the controller treats it as a failure. The fixtures' fake workers
are small and exit instantly, so the suite never opened this window. The gates worker (0.4 GiB) did not hit it.

A repair (treat a watchdog's exit-0 retirement as the leader's exit, and wait boundedly for NOTE_EXIT) moves a bound
file: the package changes, the attestations no longer apply, and it needs its own review and go. TERMINAL.json
also holds every later run (the report still runs). Nothing was edited; nothing was rerun.

## What it shows and what it does not

It shows the instrumented path runs the whole frozen plan on the Mac within the time, memory and storage limits.
It does not show fidelity: without the native reference there is no parity comparison, so no figure, no
interpretation and no Stage B admission. The 26 remaining row-20 forwards cover the 20 native ones, but only under a
new reviewed package and the owner's ruling on the terminal hold.

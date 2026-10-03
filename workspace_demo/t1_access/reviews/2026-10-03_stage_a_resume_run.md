# Stage A resume, 3 October 2026: STOPPED at 15-native - native logit parity 0.125 > 0.10 with bit-identical residuals

R084, 3 October 2026 (UTC; 2 October MST). Under the owner's release and go ("go", 2 October), bound by R052 at RSC
`cef5e0b` (`TERMINAL_RELEASE.json`, `ROW20_GO.json` to Codex's favourable revision-12 record `e7b31f0`), handoff
`1003ef19`. Package at `620f768` (criteria `4e80b959…`, identity `1a01d070…`, plan `3faebf4e…`, manifest `e816f843…`,
budget `9e9eb4dc…`), live tree equal. Command `.venv-image/bin/python stimuli/photo/stage_a_controller.py run`, launched
detached at 2026-10-03T05:07:50Z from HEAD `cef5e0b`; runner exit 0 at 05:08:42Z. Everything kept in
`2026-10-03_stage_a_resume_run/` (stdout, stderr, exit, TERMINAL, STAGE_A_FINAL, IDENTITY_TRANSITION, GATES,
controller.json, the report, and the read-only diagnosis `native_diag.py` with its output).

## What ran

- Gates worker: passed (`GATES.json`, session `51d14603dd97`, no hold, package = the five fields above).
- `IDENTITY_TRANSITION.json` written; the 2 October instrumented phase admitted under the release; counters carried
  (seconds_total 2,057.9 s at resume).
- Native worker: 16 native forwards (00-native to 15-native) written and committed, then `StopCheck: 15-native: native
  parity failed (rel_l2_max 0, logit 0.125, argmax_equal True)`; worker exit 1; controller stop "native: worker exited
  1"; report worker ran (exit 0); `STAGE_A_FINAL.json`: **STOPPED**, validator FAIL (11 failures, all consequences of
  the stop: 16-19-native not committed, NATIVE_DONE missing, the parity row, the parity count), admissible, **terminal**
  (TERMINAL.json `later`: the native StopCheck and the controller stop), terminal_release null.
- Totals: seconds_total 2,169.5 s of 14,400 s (Stage A's own 360.7 s beyond the 1,808.73 s carry); row-20 counters
  started 190, completed 189, failed 1; task memory peak 33.3 GB (the 2 October instrumented phase; native 18.9 GB);
  storage 381 MB. No hold, no watchdog or memory event.

## The stop (frozen criterion `stage_a.TOL = {"rel_l2": 0.01, "logit": 0.10}`)

| native | rel L2 max | logit max abs | at logit | one bf16 step there | argmax equal |
|---|---|---|---|---|---|
| 00 | 0 | 0.0625 | 14.69 | 0.0625 | yes |
| 01, 08, 11 | 0 | 0.03125 | 2.27-3.53 | 0.015625 (two steps) | yes |
| 02-07, 09, 14 | 0 | 0.03125 | 4.2-6.8 | 0.03125 | yes |
| 10, 12, 13 | 0 | 0.0625 | 11.6-15.8 | 0.0625 | yes |
| **15** | **0** | **0.125** | **16.5** | **0.125** | yes |

Observation (`native_diag.stdout.txt`): in all 16 records the marker-row residuals are bit-identical (relative L2 = 0)
and the embedded inputs equal the instrumented merge; the largest requested-logit difference is one bfloat16 step at
that logit's magnitude (`2^(floor(log2|x|) - 7)`) in 13 records and TWO steps in 01-, 08- and 11-native (0.03125 at
3.109, 3.531, 2.266, step 0.015625) - corrected 3 October after Codex `c4bbcb5` R2; the first version of this record
said "in every record exactly one step", which the retained diagnosis does not support. No rounding cause is
inferred. At 15-native the largest requested
logit is 16.5, where one bf16 step is 0.125 - above the 0.10 absolute tolerance, which is finer than one step of the
binade [16, 32). This is what the records show; it is not a ruling. Nothing was edited, re-run or released;
the stop stands, and Stage A stays terminal until the owner releases it and a reviewed criterion decides 15-native.

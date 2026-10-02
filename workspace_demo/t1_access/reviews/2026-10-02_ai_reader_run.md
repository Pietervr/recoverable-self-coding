# AI-reader qualification job: the run of 2 October 2026 - STOPPED after 175 attempts; the gate was not measured

R084, 2 October 2026. Executed under the owner's go ("go for Stage A and the reader qualification, 2 October",
`stimuli/photo/AIREADER_GO.json`, RSC `6ca6fb0`), after Stage A (sequential: Stage A stops on system-wide swap and
pressure, so the two were not shown independent). `ai_reader_exec.py plan` reproduced package digest `ffba894e…`
(24 fields, codex-cli 0.159.3) before the run. Command: `.venv-image/bin/python stimuli/photo/ai_reader_exec.py run`
(22:36:00-22:54:20 UTC) on RSC HEAD `66c64ca`, whose bound photo files equal the reviewed `fbfb7db`. The journal is
committed at RSC `f021c53`; the clock, its closure marker, the outputs and the scorer's refusal are in
`2026-10-02_ai_reader_run/` (`summary.json` holds the journal sha256 and the counts).

## Outcome

**STOPPED receipt; the scorer refuses ("the job did not complete (no COMPLETE receipt); an incomplete job cannot
qualify"); the 61-of-63 gate was NOT MEASURED.** Exit 0.

- smoke: passed (attempt `001.b2df6c4dfae2.1`).
- 175 of 600 requests begun (82 colour, 93 gray), 175 dispatched: 174 ended ok, 1 interrupted (request `9502fe69a9fa`,
  dispatched without an end: retained as a final error, never re-asked).
- receipt STOPPED: `FileNotFoundError: [Errno 2] No such file or directory:
  '…/rq/tmp…/a/codex_home/tmp/arg0/codex-arg0g7nO0c/applypatch'`.
- clock: one session, closed STOPPED, 1,097.4 s of the 21,600 s allowance; closure marker present (the closure
  finished). Attempts used 175 of 660. No process left; the attempt root was cleaned.
- No per-item score was computed: the scorer is the only route to the key and it refuses an incomplete job.

## The cause (diagnosed; code defect)

`ai_reader_exec.dir_bytes` (bound file) sums `f.stat()` over `d.rglob("*")` of a live attempt directory. The Codex CLI
creates and removes its own `codex_home/tmp/arg0/codex-arg0*/applypatch` helper during an attempt; an entry listed by
the walk and gone before its `stat` raises, and the run loop turns that exception into a STOPPED receipt. The shared
`enforce.dir_bytes` already skips a file that vanishes between listing and stat; this local copy does not. The
fixtures' fake CLI makes no such transient entries, so the suite never produced it; it struck once in 175 real
attempts. A repair moves a bound file (new package, review and go), and "nothing runs after a receipt": continuing
this journal, or a fresh job and its allowance, is an owner/R052 ruling. Nothing was edited; nothing was rerun.

## What it shows and what it does not

It shows the reviewed pipeline runs end to end against the real CLI - smoke, dispatch, answer capture and retention,
recovery of the interrupted attempt, the STOPPED receipt, the clock's closure and marker, the scorer's refusal - at
about 6 s per request. It does not show whether the reader names 61 of 63 easy grayscale items: that was not
measured, and nothing about it is presumed.

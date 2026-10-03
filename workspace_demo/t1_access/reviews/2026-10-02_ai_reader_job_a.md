# AI-reader qualification, job (a) of 2 October 2026: COMPLETE; the 61-of-63 gate NOT met (49 of 63) - not admitted

R084, 2 October 2026 (MST; 3 October UTC). The owner's go: "Go" (verbatim, 2 October, in R084's chat, answering the
stated choice that job (a) needed only the owner's go), bound in `stimuli/photo/AIREADER_GO.json` (RSC `e7b028e`) to
Codex's favourable revision-11 reader record (RSC `5eb51a8`, sha256 `c336e1a9…`) and the exact 24-field package
(digest `6be7d4c8…`, unchanged since `308901c`); `stage_a_guard.require_go` passed with the executor's own call. Fresh
state: the closed 2 October job archived at RSC `3b509aa` (`2026-10-02_ai_reader_first_job_archive/`, never scored;
175 attempts, 1,097.4 s, disclosed beside this job). Command `.venv-image/bin/python stimuli/photo/ai_reader_exec.py
run`, launched detached (own session) at 2026-10-03T01:26:07Z, exit 0 at 02:32:48Z. Journal committed at RSC
`0baec65` (sha256 `b8c8bf4f…`), then scored. Outputs, clock, marker and the scorer's full output:
`2026-10-02_ai_reader_job_a/`.

## The job

- smoke passed; 600 of 600 requests begun, dispatched and ended ok; 600 of 660 attempts; receipt COMPLETE ("all 600
  requests final"); clock one session closed COMPLETE, 4,000.8 s of 21,600 s, closure marker present.
- no HELD, no STOPPED, no retry, no alarm; no process left.

## The gate (frozen: gray easy whole-answer accuracy, one-sided exact 95% lower bound >= 0.90, i.e. >= 61 of 63)

**49 of 63 correct; lower bound 0.675; NOT ADMITTED.** By the job's rule (AI_READER_JOB.md step 7) the audit holds;
the scorer's referral list (123 items) is retained in `score.stdout.txt` and is not sent on. Any other route is an owner decision.

## Descriptive (no gate effect)

| | n | correct | accuracy |
|---|---|---|---|
| gray easy | 63 | 49 | 0.778 |
| colour easy | 63 | 49 | 0.778 |
| gray, all strata | 300 | 177 | 0.590 |
| colour, all strata | 300 | 184 | 0.613 |
| gray by stratum 0 / 1 / 2 | 100 each | 40 / 63 / 74 | |
| colour by stratum 0 / 1 / 2 | 100 each | 46 / 63 / 75 | |
| "close" descriptive, gray / colour | 300 each | 229 / 253 | 0.763 / 0.843 |

Paired (all 300): both 162, colour only 22, gray only 15, neither 101. Reason codes: gray OK 177, NONMATCH 122,
MALFORMED 1; colour OK 184, NONMATCH 114, MALFORMED 2. The scorer's Q1 note: the colour accuracy beside the human
mean (0.613 vs 0.495) is descriptive only - a menu-choice human norm is not a free-naming measure.

## What it shows and what it does not

It shows the qualified reader (codex-cli 0.159.3, the configured model, one image per fresh sandboxed request) names
the easy grayscale items at 49 of 63 under the frozen whole-answer key - well below the admission bar. It does not
show why (key strictness against synonyms, model limits, the images); the "close" figure (76% gray) suggests many
misses are near-misses under the strict key, which is a descriptive observation, not a re-scoring.

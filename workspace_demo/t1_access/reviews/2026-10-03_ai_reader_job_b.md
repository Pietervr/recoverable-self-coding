# AI-reader qualification, job (b) of 3 October 2026: STOPPED after 219 of 600 requests - the pinned Codex CLI binary was removed mid-run (cask upgrade 0.159.3 -> 0.160.0)

R084, 3 October 2026. The owner's go: "1. and 2. go" (3 October, R052's chat), bound in `stimuli/photo/AIREADER_GO.json`
(RSC `28f1fc5`) to Codex's favourable revision-12 record RSC `09bbe0e` and the 24-field package (digest `3e2bcdcc…`,
RSC `0f4cffe`; recomputed on the live tree before the run - equal). Fresh state: job (a)'s journal and clock archived
at RSC `5438e73` (`2026-10-02_ai_reader_job_a_archive/`). Command `.venv-image/bin/python stimuli/photo/ai_reader_exec.py
run`, launched detached at 16:29:2xZ; runner exit 0 at 16:58:35Z with a STOPPED receipt. Journal committed with this
record (`stimuli/photo/ai_reader_raw_responses.jsonl`, receipt journal_sha256 `316014d6…`). Outputs, clock, closure
marker and the evidence: `2026-10-03_ai_reader_job_b/`.

## The job

- Smoke passed (`001.b2df6c4dfae2.1`, "Trophy").
- 219 requests final, 219 attempts (of 660): 218 ok, 1 isolation_violation; 381 requests never dispatched.
- Clock: one session closed STOPPED, 1,754.1 s live (receipt seconds_total 1,814.1 s incl. the 60 s close allowance)
  of 21,600 s; closure marker present.
- No retry, no hold before the stop.

## The stop

The 220th request's pre-send prompt-input receipt (`codex debug prompt-input` under the attempt's sandbox) failed:
`sandbox-exec: execvp() of '/opt/homebrew/Caskroom/codex/0.159.3/bin/codex' failed: No such file or directory`. The
executor refused and wrote the STOPPED receipt; nothing was sent for that request. At 09:58 local (16:58 UTC) the
Homebrew cask `codex` had been upgraded to 0.160.0: `Caskroom/codex/0.159.3` is gone, `/opt/homebrew/bin/codex` ->
`0.160.0`, `codex --version` = `codex-cli 0.160.0` (`caskroom_after.txt`, `codex_version_after.txt`). What triggered the
upgrade is not determined from this machine's records. The pinned binary (realpath, sha256, package manifest, version -
four of the package's 24 fields) no longer exists, so the reviewed package cannot be reproduced and the job cannot
continue as reviewed.

## One isolation outcome (recorded, not a defect of the run)

Request `59adc2d73b07` (harmonica, COLOUR view, not easy - no effect on the gray-easy gate): the CLI's event stream
carried a top-level error event "Selected model is at capacity. Please try a different model." and `turn.failed`. The
frozen classifier treats any top-level error event other than its two declared notices as ERR_ISOLATION (fail-closed),
so a provider capacity refusal was retained as a final isolation error instead of a retryable provider failure. This
is a classification gap to declare in any next revision (`isolation_59adc2d73b07.txt`).

## Status

NOT SCORED: the journal is not COMPLETE (the scorer admits only a COMPLETE journal). Job (b) is closed by its receipt;
job (a) stays NOT ADMITTED beside it. Any continuation - restoring codex 0.159.3 exactly, or a revision on 0.160.0 with
the binary's fields re-pinned and the delivery re-rendered, and whether the 219 retained answers carry over - is a
decision for R052, Codex and the owner. No partial accuracy was computed.

# Row 19 process recycling and dropped control — bounded Codex review

Date: 5 October 2026, local PDT and UTC; completed 2026-10-05T08:31:45-07:00.
Reviewer: exact `GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`,
topic `95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Incoming `ccf55fd6-2271-5ac8-9e51-5602e6d84cee`: whole brief read;
ownership Unimog `fd76e8db` committed before manager ACK, review edits and
read-only delegation. ACK accepted at `1791213243.5853162`; do not re-ACK.
Brief: `prompts/2026-10-05_codex_r052_row19_recycle_review.txt`;
initial commit `e2a49262544b2d5d22fb1a7516fc62eab4aa0615`, SHA256 `ee21076cbd3190299bcbe7e8bcdc4f9037e3e6c39e505dab625a8c1f6a9ed1a4`;
current read commit `6f648cd9a3df0c3139e368a2b9f41f8ea1b506f6`, SHA256 `d8356e8c076e10c1c8f94f213049e92ea6134d3be39780e2e2d455b92a8a9047`.
Current owner ruling: Unimog `6f648cd9a3df0c3139e368a2b9f41f8ea1b506f6`.

Exact RSC candidate: `18446d10b735126b46036f1879087744b784f8eb`;
parent `391e6883901708370e76162619b4f6517a860eae`. Only the template and new fixture changed.

| Exact candidate source | SHA256 | Bytes |
|---|---|---:|
| `chpc/row19_slice_rep.pbs.template` | `f70831f4c4be6a7f4f173db13afd3804ca3b0db06592df75380f5386a770e62c` | 3477 |
| `test_row19_recycle.py` | `84ec8d69cb9efd117c71fbe3d9705785e7e696fa90dd9f9e84c79317254576f0` | 5162 |
| `chpc/row19_slice.py` | `c67c4c0c776d810480218f0111623481b38598b30a5c5cb68127dcc83c5dacca` | 36947 |
| `chpc/row19_slice_manifest.json` | `d1a7371ba955039a2aefbcf14fef81b79f4ecd2cbf5c86c4ed8a0be3ffbe056f` | 80306 |
| `chpc/row19_watch.py` | `640708cbf456bd444f1b818be4823cc17595eac28d781bd9c9e31f9763272b6c` | 23048 |

**1. NOT FAVOURABLE to deploying exact `18446d1` with the current mandatory
watch/logger contract.** Fresh processes under one PBS reservation preserve the
scientific identity and durable resume mechanics. Two concrete integration defects
remain: the watch mistakes segment ends for job ends and rejects the new terminal
line; an earlier logging failure can be overwritten by a later successful call.
Both admit narrow watch/template repairs without changing numerical code, the
manifest or existing task bindings.

**2. The owner's 5 October decision “Yes, drop the control” stands.** C2/C3 are
dropped. An amended slice report can describe execution, crashes, restoration and
the limited existing parity evidence without another control job. It must not
claim the original recovery control qualified, or actual post-resume scientific
parity on newly computed indices for which no independent counterpart has been
validated. No replacement control is imposed or authorized by this review.

## System and scope

Each main dataset keeps its existing B200 identity, seeds, accepted checkpoint,
validated original cache, root, campaign and job-bound reservation. The changed
PBS wrapper calls the unchanged runner with `--segment 1` as a foreground process,
then starts a new Python process only after exit 75 and positive recorded progress.
Those are successive resumes inside one PBS allocation, not new submissions or
new scientific tasks. Running attempt-2 jobs retain their old filled scripts;
the brief proposes filling later scripts from the candidate template while still
calling the untouched `rsc_slice` runtime. No running job is changed here.

This is a static source/design review. The reviewer and three read-only peers
read the exact template and new fixture, relevant runner/analysis/ledger/submit/
watch/control paths, the owning row-19 declarations and earlier control ruling.
Metadata checks used stdlib Git/hash/JSON only. No submitted imports, functions,
tests, shell harnesses, fits, simulations, providers, remote/job/account commands
or actual scientific result records were executed or opened. Reported job outcomes
below are source declarations, not independently measured by this review.

References below are candidate lines relative to `workspace_demo/t1_access/`.

## What the recycling mechanics preserve

- The template retains the same manifest/root/campaign/job/token and passes
  `--segment 1` on every invocation (`chpc/row19_slice_rep.pbs.template:30–43`).
  It stops for any runner exit other than 75, including DONE 0, HELD 4 and native
  failure 139; for absent/zero `new N,`; or for insufficient dispatch headroom.
  It never calls qsub, reserves again or automatically resubmits.
- Remaining indices are formed from validated accepted records and at most one
  new index is selected (`analyze.py:714–719`). Fixed draw/seed/identity logic is
  unchanged (`656–678`). A record is flushed and fsynced before its timing and
  watermark callback (`720–734`). Segment length is absent from scientific task
  binding (`chpc/row19_slice.py:372–380`); restoration/watermark checks remain
  (`393–399`), and a valid original cache is reused (`417–443`).
- Stop checks remain before original work (`410–414`), before dispatch (`447–467`),
  after records/aggregation and at publication (`471–549`). A stop arriving after
  one new record can cause one extra startup, which sees the request before work
  and returns 75 without the progress summary. That adds no fit or reservation.
- Submission reserves/fills/submits/binds once (`chpc/row19_submit.py:48–79`).
  A repeated start under the same unsettled token/job is admitted after checking
  kind/rep/root/cores/full requested walltime (`chpc/row19_ledger.py:156–180`).
  Runner end keeps the reservation live (`182–188`); totals count it once
  (`109–113`), and actual settlement uses scheduler allocated walltime times cores
  (`206–221`), not overwritten per-process `runner_wall_s`. Individual process
  calls do not consume the maximum four main submissions per dataset.

The manifest pins the older ledger blob SHA256
`aa6a41875fcaea464477786a2b243182b7578e95b3cf347dc027a59ad2349074`
from `9e7edbc`, whereas the candidate's local ledger has SHA256 `8cfc7b0d…`.
The deployment brief explicitly keeps the pinned `rsc_slice` runtime. Read-only
comparison confirms its `runner_start`/`runner_end` at lines 177/186 perform the
same relevant updates as candidate lines 179/188. The intervening change adds the
separate shard kind/cap. This is not asserted as a new deployment pin mismatch;
the lifecycle finding below applies to the declared pinned runtime too. Remote
runtime bytes and live job trees were not inspected.

## Required repair 1: reconcile process ends with the PBS job

The new job-final line is:

`exit <rc> tee <tee_rc> job <id> end <ISO time> calls <N>`

Template line 45 adds `calls <N>`, but the watch's `TERMINAL` regular expression
ends immediately after the timestamp (`chpc/row19_watch.py:38`). Its parser
(`144–152`) therefore recognizes no terminal line emitted by this template.
Ordinary healthy completion or boundary stop reaches the mandatory ended-job
check (`249–260`) with no accepted attributed terminal witness and alarms.

There is also a lifecycle defect even if that parser alone is fixed. Call 1 ends
with exit 75; the runner's `finally` writes `runner_ended`, `runner_wall_s` and
`runner_exit=75` (`chpc/row19_slice.py:555–560`, ledger `182–188`). Call 2's
`runner_start` changes only state/live and `runner_started` (ledger `179`), leaving
those previous end/exit fields. The watch reads any `runner_exit` as ended (`231`,
`237`). During a long active call 2, even with PBS state R, it demands a job-final
witness that should not exist yet (`249–255`). It also makes `running` false
(`307`), disabling active progress/stall checks (`340–348`) and unacknowledged-stop
checks (`355–360`). The new start and old end chronology are available but unused.

The normal gap between call 1 ending and call 2 starting is also inside the live
PBS wrapper; simply clearing fields at the next start would not resolve it.
A later native crash may retain the previous segment exit if the current process
never reaches `finally`. Its job/native failure must not be diagnosed from that
stale successful partial exit.

Accept both old and new terminal forms, or keep the old terminal grammar and put
the call count elsewhere. Reconcile active call, normal inter-call gap and actual
job end using process chronology plus PBS/wrapper evidence. Preserve genuinely
finished/gone/unknown/native-failed jobs' attributed terminal/logger obligations,
and preserve live progress/stall/stop-ack checks. Do not merely suppress alarms or
settle a live reservation early. The current mismatch alarms conservatively;
this review claims no false scheduler charge or numerical result from it.

The watch is not among manifest code pins (`chpc/row19_slice_manifest.json:4058–4064`),
whereas the ledger is pinned. A watch/template repair can preserve existing task
bindings; avoid casually editing the pinned ledger or moving the manifest SHA.

## Required repair 2: preserve every call's logger/capture failures

The pipeline now contains the runner, live-log tee and per-call capture tee
(template `38`). Line 39 saves only `PIPESTATUS[0]`/`[1]` and overwrites `tee_rc`
every call, ignoring `[2]`. Lines 41–42 recycle solely on runner exit/progress.

A producing trace is: call 1 returns 75/new 1, while its live-log tee reports a
write failure but forwards enough stdout to the capture tee to parse progress;
the loop repeats. Call 2's tee succeeds and replaces `tee_rc` with zero. The final
witness and diagnostic (lines 45–46) now report only the last call's success,
erasing the known earlier incomplete stream. After repair 1, the watch's terminal
logger-zero check (`259–260`) could accept this misleading final evidence. This
is a source-supported failure-then-success path, not a claim it occurred in jobs.

Stop after the first known live-log/capture failure, or preserve a sticky nonzero/
unknown all-call logger state through the final witness. Account for the added
capture tee as well: its failure is currently unrecorded and may yield an early
stop or partial progress parsing without an attributed logger failure. Keep runner
status and PBS settlement meanings; a broad logging redesign is unnecessary.

## Time and failure hypothesis: qualified claims

The 24-hour guard is evaluated before each process (template `30–35`). The runner
still computes its deadline from each process's new `t_main` plus the full
518400-second request minus reserve (`chpc/row19_slice.py:306–308`). This is not
the PBS allocation's remaining time. The outer guard supplies planning headroom;
it does not prove no resample can be cut by PBS. Startup plus an unexpectedly long
fit can exceed that window. Durable checkpoint recovery and scheduler settlement
still apply. No additional demonstrated false-admission/wrong-result path is
established here, so this qualification is not a third deployment blocker.
Do not pass remaining time as the reservation's requested `--walltime-s`: unchanged
ledger admission requires the true full request (`chpc/row19_ledger.py:171–172`).

The owning record reports four original processes ending in SIGSEGV 139 after
41.7–57.5 hours with LLVM “Cannot allocate memory,” on two nodes, with about
2.6 GiB resident against 8 GB requests. This weakens a single-node explanation;
it does not prove there was no node/runtime fault or prove a mapping-limit cause.
`vm.max_map_count=65530` was observed on the login node, not established here for
the compute nodes. Per-process mapping exhaustion remains an unconfirmed source
hypothesis. Fresh processes plausibly bound accumulation between resamples, but
no measured production remedy or single-resample safety guarantee is established
by this static review or by the source-declared 24-process pilot.

## What the new fixtures actually cover

There are two new top-level test methods (`test_row19_recycle.py:20`, `70`).
The commit claims 17+5+11+5+11+2 = **51 passes**, but the brief/commit supplies no
named retained public stdout or collection inventory for independent verification.
This review verified source definitions and scenarios; it did not rerun tests or
verify execution/pass/repeat/skip counts from retained logs.

The first method drives the real `R19.main` repeatedly under one job/token, through
binding/cache/checkpoint/watermark/publication/ledger paths. It compares the eight
selected scientific fields `rep`, `stats`, `failed`, `failed_reason`, `chosen`,
`ident`, `seed`, `n_rep` for six indices against one uninterrupted fixture call;
partial calls assert progress/cached message and no HELD. `_Patched` substitutes
a deterministic `run_dataset` fake (`test_row19_slice.py:30–48`, `64–70`) in a
small six-record configuration. Repeated calls occur in one Python interpreter.
This is useful durable-resume evidence, not fresh-process JAX/XLA fit equality,
whole-record byte equality or demonstrated removal of long-lived runtime failure.
The final DONE branch skips the per-call progress/cache assertions; final six-index
coverage still holds. The new test does not assert the available fit-call counter
or every-leaf cache comparator, charging/settlement or production watch behavior.

The second method extracts the actual template loop and uses a scripted fake
runner that ignores all arguments (`test_row19_recycle.py:49–67`). Four cases
cover three positive-progress partial calls then DONE; partial then zero progress;
partial then HELD; and already-insufficient headroom with zero calls (`73–83`).
It does not cross actual runner/cache/status/ledger/watch paths. Because the real
runner fixture supplies its own argv and this fake ignores argv, both could pass
if a template flag/token/path were altered. Static reading confirms the intended
flags at template line 38; this is a coverage limit, not wrong current flags.
No watch transition or logger-failure-then-success case closes the two defects.

For reconsideration, supply the narrow repairs and retained offline integration
evidence for a partial end → next active call → inter-call gap → actual final job,
both terminal grammars, later native failure, preserved live stop/stall behavior,
and live-log/capture failures that cannot turn into a clean final witness. Existing
reservation/charge semantics must remain. No new fit or replacement scientific
control is required merely to review these integration repairs.

## Control ruling and reportable evidence

Unimog `6f648cd9a3df0c3139e368a2b9f41f8ea1b506f6`, ledger row 19, records the
owner's “Yes, drop the control.” The brief's added OWNER RULING agrees; its older
“owner not yet ruled” sentence is historical proposal text. Preserve the current
drop. Do not submit C2/C3 or require a replacement against it.

The ledger/brief reports C1 and main rep 0 indices 0 and 1 bit-equal across two
jobs/nodes. Both pairs were computed **before** the crashes. The three mains'
attempt-2 restoration of existing checkpoints/cache supports operational recovery
as disclosed by source logs; it is distinct from comparing newly computed
post-resume records against independent reference fits. New main-0 indices 2+
have no declared C1 counterpart. Stub/in-process fixture equality cannot fill
that actual scientific-output gap.

The original frozen control required exact indices 0..7, successful terminal C1
fresh and C3 resumed statuses, typed/bound jobs/roots/reservations, an actual PBS
walltime-killed C2 with requested walltime matched, used time at least requested,
nonzero native exit and 1..7 accepted records, exact resumed count/cache evidence,
and no FAILED resamples (`chpc/row19_control_compare.py:142–164`, `207–306`).
C1's failed termination after two records and SIGSEGV at 41–57 hours of a 144-hour
request do not qualify that contract. Dropping C2/C3 changes reporting scope;
it is not a favourable old comparator result. Preserve historical manifest
language and describe the owner amendment explicitly without silently moving
live binding hashes.

The amended report should give accepted counts/indices before and after each
crash, the first newly computed post-resume indices, tail repairs/lost in-flight
work, original-cache reuse, watermark/rejection/damage findings and actual
scheduler-accounted charges. State that the old control is unqualified/dropped,
existing parity is limited to the declared pre-crash overlap, and actual newly
computed post-resume parity has not been established. That suffices for an honest
bounded execution/recovery report; it does not admit coverage or Stage 2.

If a later claim requires parity on the fixed panel, first consider authenticated
existing independent counterparts: the owning ledger declares eight pilot records
per dataset, which an appropriate actual-evidence review may validate for rep-0
indices 2..7 and matching identity/pins/production before comparison. They were
not inspected/admitted here. Do not purchase a duplicate job on the assumption
they cannot serve. An independently declared recycled reference through 0..7 in
its own root is a prospective alternative only if needed and separately authorized.
It would establish parity against an independent **recycled** reference on that
panel, not one long-lived uninterrupted process or the old deliberate PBS-kill
qualification. Neither option is a present requirement/go, and existing outputs
must not be relabelled C1/C2/C3 to make the old comparator pass.

## Boundaries and disposition

Source-reported attempt-2 mains are `7520111.sched01` (rep 2),
`7520953.sched01` (rep 1), `7521637.sched01` (rep 0); their running scripts remain
untouched. Source settled the four original crashes from qstat -xf. The declared
pilot `7517913` finished with 24 records/eight per dataset and 604.32 core-hours;
its actual-evidence review and the other eight held shard jobs are separate.
The source HEAL1922 test acceptance is not a new allocation/launch permission.
Root did no monitoring, settlement, restart, resubmit, SSH/PBS or account action.

Existing reservation/cap-raise procedure, 100000-core-hour allocation hard stop,
four-submission main limit, unchanged numerical identity and old paid/cloud gates
carry. Coverage, Stage-2 design/go/reference/cost judgments and closed reader/
image/supplement/full-bank reviews are not reopened. No cloud run or new spending
is approved. The source owns implementation/current summaries/ledger/dispatch;
root owns only this record and its R052 append/committed findings handoff/lifecycle.
Foreign files and source jobs are preserved. Await a concrete revised template/
watch package or a new explicit assignment after completion/adoption.

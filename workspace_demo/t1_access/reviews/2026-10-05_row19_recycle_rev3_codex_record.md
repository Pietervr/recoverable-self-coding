# Row 19 recycling revision 3 — bounded Codex re-review

Date: 5 October 2026, local PDT and UTC; completed 2026-10-05T09:14:21-07:00.
Reviewer: exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Incoming `c38e5126-cb0b-57b7-85a4-f30dcbfca302`: whole brief read;
ownership Unimog `c602d2cf` committed before ACK, review edits and delegation.
ACK accepted `1791216464.909724`; do not re-ACK.
Brief: `prompts/2026-10-05_codex_r052_row19_recycle_rev3.txt`,
Unimog `6f0d18ce398a464ed2f40547dcdb6f1a77c67cfd`, SHA256 `a2c3ac0297c8885d18d25e749d69ce925f70adb24b868828deb1f955d0280dd1`.
Predecessor records RSC `71dee38f77c7eca12dbe201f98866738db681b60` and
`0be55479c33a18deba3aaf119a12841fce93ea54` remain closed.
Exact candidate: `9aad954a384af804bbb58f40d61488c9c4ec44e7`;
comparison `5926cc3ef95c60fd41bbea87949f9e1c96637c43`. Current owning ledger read at
Unimog `6f0d18ce398a464ed2f40547dcdb6f1a77c67cfd`.

| Exact candidate source/evidence | SHA256 | Bytes |
|---|---|---:|
| `chpc/row19_slice_rep.pbs.template` | `7ffd4d6772f452a3799e5cd3949c3863ba341b65c20639b3096e52640bcfc6f1` | 4954 |
| `chpc/row19_watch.py` | `e5be3e1668faf34cc9b4f6c9112b0afc4435d9954b2202c18a8dcf4ca3dfb4bd` | 27458 |
| `test_row19_recycle.py` | `adc98ff2b2aae62e79ac0a3014297347ee268dbd86cca359b30444867ba2c957` | 17818 |
| `test_row19_watch.py` | `f3ad2095cd00352fdccf575713ca99141372a608cbad73855af8998c80b071ae` | 14385 |
| `reviews/2026-10-05_row19_recycle_rev3_tests.txt` | `b681fe130eaa9b503d53705b61c291cbee673655ea23cf83907fc2945135f15d` | 4197 |
| `chpc/row19_slice.py` | `c67c4c0c776d810480218f0111623481b38598b30a5c5cb68127dcc83c5dacca` | 36947 |
| `chpc/row19_slice_manifest.json` | `d1a7371ba955039a2aefbcf14fef81b79f4ecd2cbf5c86c4ed8a0be3ffbe056f` | 80306 |

**FAVOURABLE to deploying exact `9aad954` recycling template for later main
attempts, with this exact repaired watch as the mandatory observer.** Both
remaining producing findings in `71dee38` are closed. No further repair or new
scientific control is required to close this bounded review.

This accepts the template/watch integration under the existing row-19 slice
authority, scientific identity, resource admission and recovery rules. The
owner's 5 October approval of the fix and C2/C3 drop carry forward. Source R052
owns adoption, any standing-go binding, later filled scripts and dispatch; this
record performs no job operation and changes no existing running script.

## Reviewed system and scope

The template invokes the unchanged runner as a fresh foreground process with
`--segment 1`: at most one new resample per call, restoring the same original
cache and strict checkpoint. Calls share the scientific task, PBS job id and
reservation token. Recycling requires exit 75 and positive new-record progress;
another exit, no progress, logger failure or insufficient outer headroom ends
the loop. Native runner status and logger status remain separate evidence.
The mandatory watch distinguishes a process's end from the job's end, keeps
whole-job progress and stop checks while active, and diagnoses terminal evidence
independently of the scheduler when the wrapper has published its own final line.

Whole brief, template, watch, recycling fixture, watch fixture, retained synthetic
log and scoped diff were read. Three reused read-only peers checked watch,
logger and retained-evidence paths. Owned stdlib Git/hash/AST checks verified all
seven declared hashes, live equality to the pinned blobs, test names/counts and
unchanged runner/manifest/ledger/submit/analyze blobs. The candidate commit changes
five paths: template, watch, two fixtures and retained log. The broader comparison
also contains the closed `71dee38` record and source tracker updates.

This is static source and retained synthetic evidence review. No submitted code,
imports, functions, tests, shell harnesses, fakes, fits, simulations, providers,
remote/account/job operations or actual result/private key/image/human artifacts
were executed or opened by root or these peers. Retained execution is source
evidence, not an independent rerun here. Current ledger job outcomes are source
declarations, not remote observations made here. Line references below name
exact candidate files relative to `workspace_demo/t1_access/`.

## Finding 1 closed: the job-final witness is authoritative

`lifecycle` reads only a final line attributed to this entry's job id and now
sets `job_ended = found or pbs_ended or (process_done and not between)`
(`chpc/row19_watch.py:184–194`). It exposes `final=found`. Therefore a valid final
139 line ends the job even when PBS is unobserved (`-`) or still R, a newer
process start follows the previous exit 75, or there are no runner start/end/exit
fields at all. An old attempt's final line still cannot end this job.

The new independent `final`/unfinished-process branch (`290–294`) alarms the
missing latest process end, names the final exit, identifies any retained exit
as belonging to an earlier call, and keeps the reservation. Terminal obligations
now also admit `lc['final']` (`304`): exit disagreement and nonzero/unknown logger
evidence are checked (`312–315`) even without runner fields or surviving call
markers. The job phase follows the end predicate and running health cannot
hide the explicit terminal failure (`280–282`, `362`). The former recent-progress
green trace is closed; waiting for a later stall or PBS F is unnecessary.

Without a final line, the ordinary gap/active rules remain: start/end chronology
prevents an old exit from ending a newer call; exit-75 gaps are allowed under PBS
R or within the unobserved allowance; an expired unobserved gap alarms. Existing
PBS-ended diagnosis, unknown observation alarms, attributed terminal parsing,
first-call progress baseline, stall and stop-ack checks are preserved. No qstat
mandate, ledger change or scientific identity move was needed.

The new final-line method (`test_row19_recycle.py:218–267`) retains these cases:

- One real runner invocation with stub fits ends 75, then real ledger
  `runner_start` records call 2 under the same job/token (`235–238`). Its stale
  exit cannot count as the newer process's end.
- Constructed active call 2 without a final line is observed under `-` and R
  (`243–247`). These assertions check running phase and absence of the new final
  alarm; they do **not** assert a clean overall return code. The older active/gap
  fixture explicitly checks return 0 for its clean observations (`173–191`).
- Adding an attributed final 139 under both observations requires return 1,
  unfinished-process diagnosis, earlier-call identification and exit mismatch
  (`249–253`). This directly targets the prior missing branch.
- A second bound job that never reached runner start, with its own final 139,
  alarms under R (`254–259`). That no-fields variant is not separately asserted
  under `-`, but the same scheduler-independent source predicate covers it.
- A completed job with final logger 3 and unobserved PBS alarms on the logger
  (`261–265`). This is not the entire unfinished-process/logger cross product;
  the terminal gate independently covers that combination too.

The older constructed call-2 chronology is repaired: retained call 1 is announced
at now minus 120 seconds, previous end is now minus 90, and call 2 is announced
and started at now minus 60 (`166`, `187–188`, `206`). The stop-ack fixture now
removes the contradictory old job-final line before portraying that same job as
running (`test_row19_watch.py:203–205`). This is a coherent fixture correction,
not removal of the stop check; its later stop assertions remain.

These observations use private copied snapshots, constructed clocks/logs and
qstat lambdas with `--no-pull`. They do not run a real second scientific process
or observe PBS. The assertion qualifications limit the evidence, not source
closure of this concrete final-witness gap.

## Finding 2 closed: failed call-start publication stops before dispatch

`mark()` immediately captures the marker tee's `PIPESTATUS[1]`, defaults a missing
status to 1, stores a nonzero result only while shared `tee_rc` is zero, and
returns the captured status (`chpc/row19_slice_rep.pbs.template:40`). It executes
as a function in the calling shell, so the sticky assignment survives the call.

The call-start branch checks that result (`45–48`). Failure removes the unused
capture file, ensures a nonzero logger field and breaks. Only a successful
publication reaches the count increment and runner invocation (`49–50`). Hence
the failed required marker cannot be followed by a clean runner/later marker
that hides the failure. The final call-count marker also uses `mark()` (`60`),
which preserves an existing failure; the attributed final line emits that sticky
value in the original grammar (`61`). Headroom/no-new-record markers use the
same checked publication helper and leave the loop (`43`, `57`).

The earlier live/capture repairs remain: pipeline statuses are captured together,
nonzero runner-stream or capture tee status stops before any later call, and
failed `mktemp` prevents dispatch (`44`, `50–57`). Runner/native exit remains
separate from logger failure. Final-witness write status is still reported
(`62–63`). No broad preexisting auxiliary-logging redesign is added here.

The tee wrapper injects status 3 specifically after passing through the targeted
call-start marker (`test_row19_recycle.py:90–98`). The fake dispatch counter
increments only when the runner is invoked (`108–111`). New faults at marker 1
and marker 2 assert zero and one actual fake invocations respectively, final tee
3, and final calls count `at - 1` (`142–148`). Thus both boundaries test no
dispatch for the failed marker and retention of its failure after healthy final
writes. The fault fixture physically retains the marker bytes before returning
nonzero; it does not simulate a missing/truncated write. The source checks the
same nonzero publication result before dispatch, so ordinary failed writes are
also covered by the guard. Existing clean grammar/call markers and live/capture
fault assertions remain (`123–141`).

## Retained evidence and unchanged bindings

The exact retained log is 4197 bytes/67 lines, run label
`2026-10-05T15:56:04Z`. Six module totals are 17/5/11/5/11/5:
**54 OK events, 54 distinct matching top-level source test definitions, no
repeated, failed, error or skip events in this log.** Five recycling methods are
retained; one new method was added and existing marker cases were extended.
Neither the prior 53-event log nor the older unretained 51-pass claim is added
to this run. The log retains names, statuses and durations; it does not retain
full stdout, the invocation command or an environment/collection manifest.

The logger method has six extracted-template fake-runner cases: clean, live tee
failure at call 1, capture failure at call 1, live tee failure at call 2, and
marker failures at calls 1/2. The new watch method has six local observations;
the older lifecycle method retains nine. These are assertions inside the named
methods, not extra tests to add to 54. Full-input status injection, argv-ignoring
shell fake, constructed watch evidence and same-interpreter stub science remain
explicit limits. The scientific equality method compares eight selected fields
across six indices; it establishes no fresh-process JAX parity or actual runtime
remedy here. No additional fit is demanded for these two integration repairs.

Runner, manifest, ledger, submitter and `analyze.py` are byte-identical to `5926cc3`.
The manifest's existing scientific and runtime bindings are preserved. This
template/watch repair does not create new seeds, datasets, submissions or
reservations per call, bypass strict checkpoint/cache/watermark/ownership checks,
or reduce the full requested-walltime admission/actual PBS settlement obligation.
The previously reviewed older pinned ledger/untouched runtime distinction is
unchanged; remote deployed bytes were not checked here.

## Conditions that carry forward

The 24-hour guard is dispatch headroom, not a proof against a PBS walltime cut;
the runner's deadline resets per process and full requested walltime remains
reserved. The crash cause remains a hypothesis despite stronger template/current
summary wording. Neither qualification is a new deployment blocker.

Owner 5 October drops C2/C3. The amended execution/recovery report needs no
replacement control. Original control remains unqualified; declared actual
parity covers pre-crash indices 0/1 only, and new post-resume scientific parity
is unestablished. Source attempt-2 jobs `7520111`, `7520953`, `7521637` and their
filled scripts are preserved. This review concerns later main attempts and the
mandatory repaired watch; no root monitoring/restart/resubmit/settlement occurred.

Actual sharded-pilot evidence admission and the other eight held shard jobs remain
separate. Coverage, Stage 2/reference/error allocation/cost/go and paid/cloud
gates do not move. Existing cap-raise procedure, 100,000-hour hard allocation,
maximum-attempt policy, prior exposure disclosures and private-output exclusions
carry. HEAL1922 test success is source metadata, not an allocation change here.

Source R052 owns adoption, current summaries/frontmatter/generated work INDEX,
tracker, ledger, implementation, operational bindings and dispatch. Root owns
only this review, own R052 appends, adoption brief and lifecycle. One completion
report and accepted adoption finish this assignment. Await new explicit work;
do not reopen prior review judgments, ACKs or completion reports.

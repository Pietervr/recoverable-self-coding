# v15 step 8c: regenerated refit-pilot qualification

Codex actual-source review, local 11 October / UTC 12 October 2026. Exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Whole incoming `prompts/2026-10-12_codex_r052_step8c_pilot_qualification_v15.txt`
read at Unimog `acd6ba51531e2337e5bfb6731c41dad0010e1104`, SHA256
`3fa34cc19560c3e87df8d8980e4de8c96f059ecc2d21a87c032c0c9f4f071ae7`.
Ownership committed at Unimog `9d7e6d837ede72f91d885539b5b569fc6e13a888`,
then incoming `80a0365b-f576-535f-81e6-bc27fd63d0aa` ACK
`1791784019.897894`, before review edits/delegation.

**FAVOURABLE for the regenerated refit-pilot gate**, exact qualification
`3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c`
in RSC `b003239f3bac4e97ad3156bcd65af567cd1e1815`, under the already
reviewed/adopted controls `828d3b69…`, version 15. No blocking finding in
the saved actual evidence and retained gate contracts.

```text
ADOPT row19-screen-pilot role=refit qualification=3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c max_job=100
```

This line binds the **refit pilot qualification and job-number ceiling**. It is
not a new scientific result, EC2 permission record or production release. Do not
reuse the historical `3820ac0e` qualification literal.

## Checked actual evidence

The ten `chpc/qualification_v15_3c605514/SHA256SUMS` entries match both the
working package and its exact committed blobs. The qualification embeds the
standalone `watch_refit_20261012T054319Z.json` receipt without a structural
difference. Its verifier/file hashes name the retained full verifier, and its
anchor digest matches the embedded and verifier anchor evidence. Both watch
receipts report fresh production evidence with no alarms; this qualification's
verifier reports clean code/environment checks and generation 15, the adopted
controls bytes and the pinned verifier digest.

The qualification binds only pilot job 1: PBS `7523818.sched01`, token
`2a25377fe9db`, plan `39cbd2ee…`, and 24 task bindings for reps 3–26. The
whole-role receipt retains all 13 job bindings and all 100 task bindings.
The full verifier contains 287 units with valid record/timing metadata; the
pilot's exact 24 reps at index 0 name its PBS ID and expected slots 0–23.
All 24 completed, with scheduler/runner exits 0/0, no work left and no disposition.
Anchors 0/1/2 have index 0 equal, with compared/equal counts 6/6, 6/6 and 5/5,
and no conflict, difference, missing or invalid entry.

**Original retained memory provenance was inspected**, rather than inferring it
from the newest aggregate. `watch_refit_20261010T224529Z.json`, SHA256
`c6fd4a730829d6b17c4d0855231f63507c92892b0e3e473bc39610c20b8400fa`,
directly reports the same pilot PBS ID, F/exit 0, token and plan hash. It records
47,179,688 KiB scheduler memory and the 108,000-second walltime request. The
regenerated summary carries those exact values and explicitly names this direct
source as `prior-receipt-qstat`; current `qstat_mem_kb` is null after PBS history
expiry, and terminal state/exit are labelled `ledger-settlement` with the retained
settlement-note digest. No memory breach is recorded. These observations are
37.495% of the 120 GiB request, with maximum worker RSS 2.320 GiB and maximum
worker runtime 24.388 hours against the 30-hour pilot plan. They satisfy the
unchanged memory and walltime bounds. The later jobs' carried request and direct
memory fields are kept distinct; no expired direct observation is presented as
a current qstat result.

**The current crash disposition and both bound PBS files were inspected.** Job
13's `.out`/`.err` hashes are `6acfed16…` / `8a222e8d…`, exactly the reviewed
fixture bytes. They name the bound job/token and identify slot 16, rep 83/index 2,
with the SIGSEGV line and its missing worker exit. The receipt retains scheduler/
runner exits 4/4, 570.453333 core-hours charged, 23 exact surviving completions
and `83/2` uncompleted. The full verifier has no completion at `83/2`.
Neither failure nor charge is erased, and this job cannot qualify a pilot.

Job 3 remains the charged closed-no-record attempt. Its bound `.out` hash
`4132a084…` matches the retained bytes; no verifier unit is attributed to that
producer. Its historical coordinates have valid later job-10 completions. That
later completion does not turn job 3 into a qualified or credited success.

## Archive, adoption and operating conditions

Saved Mac inventory `0438bedd…` preserves the five actual v14 predecessor files,
including the old qualification. The saved Lengau inventory's 79 archive rows
reconstruct `4aa06b12…`; the accompanying metadata names the new qualification,
retired review `0324ff53…` and absence of an active review. The original direct
memory receipt is retained in that archive. Promotion/deployment source archives
before replacement and preserves the actual predecessor; it does not replay the
v9 migration, activation, benchmark or pilot fit. These are checked source and
saved inventories, not an independent observation of current remote permissions
or the live gate filesystem.

Current admission checks the complete pilot and retained verifier at
`row19_screen_admit.py:1433`, excludes either disposition from a pilot at `:1190`,
and checks fresh whole-role evidence/current disposition and envelope at `:1472`.
Adoption at `:1536` requires this exact role/qualification/max-job literal and a
tracked unmodified record, and refuses an existing review. Subsequent admission
at `:1513` checks the adopted record, qualification, current root/ledger bindings
and a current receipt within 2,700 seconds. Current-root checks must continue;
this saved receipt is not an exemption from later freshness or state changes.

R052 may copy this committed record and perform the matching max100 pilot
adoption. Then follow step 9's fresh-receipt refills, allowing the ordinary planner
to consider uncompleted `83/2` under its existing partition/resource/budget gates.
Step 10 still requires its **correct separate qualification-permission record**,
current inventory/receipt checks and the owner's existing one-Q1/one-Q2/S USD 45
go. This pilot record is not that permission record. Actual Q1/Q2/S results still
require the separate actual-result review before the standing production release;
retries remain owner-controlled. All other funding, concurrency, programme,
sub-envelope, qualification, release and exposure limits remain unchanged.

## Validation limits and ownership

Root and bounded peers checked committed control source, saved metadata,
checksums, original scheduler provenance, complete verifier validity metadata and
bound PBS bytes. A temporary stdlib helper performed deterministic hash/JSON
coherence checks only. No project imports/execution/runtime tests or fits were
run. The source's live preflight and deployment assertions were not independently
reproduced; current remote root/ledger state is enforced by the operating gates.
No raw fit payload, scientific result or private reader/audit output was opened.
The memory-map crash diagnosis remains a qualified operator hypothesis; this
review makes no cause, mitigation or retry finding.

Root owns this record, its own R052 log appends, sole findings and lifecycle.
R052 owns current docs/frontmatter/generated INDEX, adoption, dispatch and jobs.
No root SSH/AWS, deploy/adopt/qualify/refill, job intervention, worktrees or push.
Source bank/slice jobs, foreign files and all prior limits are preserved. The
earlier controller review `f1bede4` and its accepted completion report remain
closed; this is the distinct actual pilot-qualification review requested in step 8c.

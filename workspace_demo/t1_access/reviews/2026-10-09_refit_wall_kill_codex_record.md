# R052 — refit wall-kill disposition and prospective resource design

Date: 9 October 2026. Reviewer: Codex, `GPT: R052 Entropy paper`.
Candidate inspected: RSC `1489792b33fec34ce640bc533febe3ecfc30beec`.
Brief: Unimog `8c30d7593e93756c49fef32537417e715ce4dc21`,
`prompts/2026-10-09_codex_r052_refit_wall_kill.txt`, SHA256
`c9810b1416cee9571cddcc261232afe4d17eb1b7f61a36d3e23bf795bdce16e9`.
Ownership committed at Unimog `8577f4ac`; handoff
`9c5da48b-db43-5c0e-a99e-fce469e2f097` accepted before edits or delegation.

## Three separate verdicts

| Question | Verdict and scope |
| --- | --- |
| 1. Disposition of refit job 3, `7527352.sched01` | **FAVOURABLE to the proposed closed-no-record disposition design**, retaining the 720.55-hour charge and all evidence. Requires a reviewed revision of status **and admission**, not a status-only exemption. No completion or restart-recovery credit. |
| 2. Refit jobs 10 onward at 48 hours | **FAVOURABLE to a prospective resource design**: serial, 24 cores, 48 h, 120 GB, unchanged 1,800 s reserve, one index per worker. Prefer a separately pinned resource policy preserving immutable manifests/bindings. Implementation and provenance/adoption review remain required before job 10; cap 60,000 and job ceiling 100 remain. |
| 3. Fill every freed slot with bank jobs | **NOT FAVOURABLE as an unconditional agent-led operating instruction.** Favour bank priority within its existing raw jobs-through-17 scope, 36-h request and 15,000-hour cap, when all fresh admission/funding/capacity gates and the current-policy operating condition below hold. No additional bank scope is needed for that priority. |

The owner's standing conditional go remains; no repeat owner approval is requested. These are disposition/resource judgments, not attestation of an implementation that does not yet exist. This record supplies no machine-readable controller or new-manifest ADOPT authority. The completed `6d8c30a` pilot review and version-7 judgment remain the historical authorities for their exact packages. Existing runs are left untouched; this record performs no remote operation or cancellation.

## Evidence and limits

The whole brief, completed 8-October record, R052 header and 9-October log, screen declarations and relevant controller/worker paths were read. Three read-only reviewers separately checked disposition integration, resource provenance and bank funding. The listed wall-kill, timing, settlement, anchor and in-flight facts are **source-reported observations in the new brief**, not a new Codex scheduler attestation. No new fit/target/interval/coverage calculation, producer import, test execution, simulation, private reader/plant/key/PC evidence, account access or Lengau operation was performed. Checks used source inspection and deterministic hashes/resource arithmetic only.

Important pin correction: the brief's `5536bb6c…` is the **historical version-1** status pin. Current unmodified files match HEAD and adopted version 7:

| File, relative to `chpc/` | SHA256 |
| --- | --- |
| `row19_screen_status.py` | `dac142fb58991f14fa1616e768b156af42f6ccf15252840ef7a3b6af07c1f7e0` |
| `row19_screen_admit.py` | `573e5b18835a57b55fa545b3815458b1a59662847318b6fd7046858fa2b32d53` |
| `row19_screen_verify.py` | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `row19_screen_controls.json` | `43a099cad12eb234ff501cb596e9f68d8b013dc7c231dbc7de21feafeb8cdd8a` |
| `row19_screen_controls_adoption.json` | `c5d3bc7bee4319d0f1c9f3dc64ca65a40a0fbfb7459ea8e2a1cbd9e07e8d113f` |
| `row19_screen_manifest.json` | `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c` |
| `row19_shard.py` | `828d59640f10cc33fcba7d98d075371945ca4b74ddaca841ea86100fc47ff383` |
| `row22_bank_manifest.json` | `d895c8a3bdf4983ad5a08868ce7a718b82f638c498ad02ea8acd848af63c0a69` |
| `row22_bank_submit.py` | `88fd335ecb5ff42773d304128d433041e3e480416f92ba54d7b163739cd34913` |
| `programme_gate.py` | `10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0` |

## 1. Disposition: preserve the loss and validate the exception

Source reports F/exit 271 at wall 30:01:23, 713:31:33 CPU, all 24 worker logs header-only, no status/timing/record, settled 720.55 core-hours; refit spent 1,892.81/live 4,320. Those observations support a wall-killed busy attempt. They do not show that the 24 fits could have finished at any particular later time. Retain raw scheduler accounting, original plan/token/job identity, logs, settlement and cause. Job 3 stays a charged failed attempt.

Use the narrow guard previously accepted for the development shard: successful fresh terminal scheduler observation **and current SETTLED ledger**, no parsed **or unreadable** job-scoped worker status, no record attributable to that job, no runner-end fields, and retained evidence of no `ADMISSION FAILED`. Suppress only bad-PBS-exit, missing-runner-end and missing-worker-status alarms in this exact case. Keep actual exit 271, zero ended/new/resumed counts and absent worker measurements visible as an explicit disposition. A disposed job must never qualify a pilot.

The screen needs a complete controller revision from **version 7**:

- `row19_screen_status.py:102–116` pulls root/campaign, while the role/job PBS output is under the toolchain jobs directory (`row19_screen_admit.py:879–880`). Retain and bind that correct output in the fresh observation. Failed/missing/unreadable retrieval cannot prove absence of admission failure. Inspect all status files scoped to the bound PBS job, including unplanned slots; malformed status is evidence requiring a hold, not an absent status. Preserve normal transport, bindings, anchors, record, memory and admission alarms.
- `row19_screen_admit.py:508–532` requires ordinary terminal runner/worker outcomes. A separate disposition branch must independently validate the predicate against the current ledger and retained evidence; a caller's boolean cannot waive these requirements. Keep successful pilot and originals qualification rules unchanged.
- Historical partition/provenance checks (`:555–636`) must still account for every planned coordinate. Express the disposed plan's work as uncompleted with an explicit plan-derived origin, not invented worker statuses. Later retries may complete those coordinates only through their own later bound plan/job/slot. A valid record without valid timing, an unsupported producer, wrong slot or evidence naming the killed job must hold. Timing carries producer attribution (`row19_screen_verify.py:196–210`); zero valid timings naming job 3 alone is insufficient proof of no output.
- Current-ledger transitions (`admit:652–673`) must also revalidate SETTLED, settlement evidence, unchanged token/job/plan and absence of both runner-end fields. Recollect after inconsistent or newly discovered evidence; never erase the loss. Fresh complete whole-role verification/receipt remains required within 2,700 seconds, with exact reviewed/adopted controller lineage.

Source-side verification should demonstrate unsettled kill holds; the fully evidenced settled no-record case is explicit; any parsed/unreadable/unplanned status, admission failure/missing output, attributable record or forged/current-ledger mismatch holds; a later correctly bound retry supplies only later completion; and ordinary partitions, pilots and originals retain their guards. This is the required implementation evidence, not a test run claimed here.

Once the exact disposition is valid, `(rep51..74,index0)` remains missing and leaves IN FLIGHT after settlement. The current evidence/planner already uses valid records and live plans, orders missing indices first and preserves job numbering (`admit:360–436`). Retry the same datasets, draws and seeds first **only if fresh evidence still shows them missing and unreserved**. Do not delete ledger entries or replace failed datasets.

## 2. Prospective 48-hour envelope: useful slack, unchanged science

The mechanism is confirmed in `row19_shard.py:318–345`: `longest` starts at zero; the pre-fit check uses `max(90000,1.25*longest)`; then the fit runs without an internal deadline checkpoint. With one index per worker, this rule cannot learn that fit's wall before starting it. Raising the expectation inside a 30-h request cannot predict node/dataset speed; raising it above the available wall merely prevents useful starts. Excluding one node does not address another slow node or dataset. A fit checkpoint would be a separately reviewed science change and is outside this amendment.

At 48 h the START-based deadline allowance is **171,000 s**, less subsequent startup overhead; 170,999 assumes about one second has elapsed. That is **1.945×** the reported 87,922-s completed-fit maximum. Job 3's unfinished fits are right-censored, so neither their completion wall nor a runtime-tail bound is known. Forty-eight hours reduces an observed exposure; it cannot guarantee completion or restart recovery. Leave jobs 4–9, their 30-h requests and shared producer paths untouched: `7529179`, `7529279`, `7529496`, `7529616`, `7529741`, `7529824`. Their terminal evidence, reportedly starting around 10 October 12:00 UTC, informs the next resource judgment.

Correct the cost statement: **1,152 core-hours per new full request**, versus 720. Settlement refunds unused reservation; it does not guarantee unchanged actual spend. A fit finishing after 30 h consumes more wall, and the previous 720.55 loss remains charged. Preserve campaign cap **60,000**, common allocation **100,000** and highest job number **100**. One hundred full 48-h reservations total **115,200**, so admission must enforce rolling actual settlement and worst-case live/new charges. The existing job ceiling funds neither its entire range nor all 20,000 refits.

Walltime is outside the scientific identity in `row19_shard.task():74–94`, but the **whole manifest SHA is inside immutable task bindings** (`:186–214`), worker/job-start checks and verifier expectations. Qualification and adoption also bind it (`admit:443–477,717–753,812–833`). A casual 30→48 edit breaks them. The declarations explain this immutability; they do not implement a migration.

Prefer a **separately pinned and explicitly adopted prospective resource policy**, preserving the frozen scientific manifest and existing binding bytes, analogous to the earlier per-submission queue design. Resolve later refit requests to the specified serial/24/48/120/1,800 envelope and bind/check it consistently in the plan, filled PBS request, ledger reservation, job-start arguments and receipts. PBS construction already takes a supplied walltime; current admission derives it from the manifest (`admit:871–895,985–1026`). Review that controller change before deployment.

If source chooses versioned manifests instead, return a concrete migration for review: retain old manifests, bindings, qualification, plans and producer pins; prove the difference is resource-only; preserve all 100 identities/seeds, B200/draws/folds/fit seeds, pairing and exclusions; support historical/prospective provenance together in verifier/receipt/release; retain all charges and numbering; and keep active jobs unaltered. New bindings alone are insufficient. After either route, separately reviewed implementation/adoption and a fresh whole-role zero-alarm receipt precede job 10. No new owner go is needed when the standing go binds to that verified package.

## 3. Bank priority and operating conditions

The independent raw-bank approval through job 17 remains scientifically appropriate while refit admission is held. Keep serial/24 cores/36 h/120 GB, unchanged seeds/bindings, 864-hour full reservations and cap 15,000. Require the adopted actual qualification, a successfully published fresh whole-bank zero-alarm receipt covering every current job, pins and STOP checks (`row22_bank_submit.py:110–278`). A killed verifier or failed transport is failed observation; sequential successful retry may provide the fresh evidence. The refit role's alarms do not themselves invalidate an independently clean bank receipt.

Use the cooperative `programme_gate.py run` window with truthful maximum jobs/cores/walltime; serialize settlements under the same lock. Sum all five campaign ledgers, settled losses, worst-case live/new requests and the declared **6 core-hours** of other use. Source's latest bank balance in the 20:2x log is spent 2,977.13/live 2,592: nine more full requests through 17 would give 13,345.13. This is source-reported arithmetic, not fresh accounting or a batch dispatch permission. Recheck current allocation, role cap and user/queue capacity for each request.

The bank slack argument is illustrative: **at least 1.21× is a lower bound, not a maximum slowdown**. Node effects and dataset effects remain confounded. Multiplying 26:17:09 by 1.21 gives approximately 31.81 h; it does not prove that another bank job finishes inside 36 h. The reserve leaves 35.5 h before the worker deadline, and bank also checks only before its uncheckpointed fit (`row22_bank.py:257–286`). A loss can consume a retry/job number; ceiling 17 does not guarantee all 408 records. No bank timing-tail guarantee is adopted.

**Current external operating condition:** CHPC now links [Accounts Policy v2.8, 1 July 2026](https://wiki.chpc.ac.za/_media/chpc:chpc_accounts_policy-v2.8.pdf). Its serial table allows 48 h; §§3.3/4 retain aggregate limits of 240 cores and 20 jobs, with ten running and ten queued. §2.2(6) prohibits AI-agent direct/indirect Lengau access and permits compliant non-AI research workflows only under user control. Source must establish that permitted operating route before further agent-led submission, monitoring or transfer; an existing research go or scheduler acceptance does not establish an exception. Codex performed no such access. The [quick-start guide](https://wiki.chpc.ac.za/quick:start) says limits can vary; fresh applicable limits remain necessary. No `smp` capacity or HEAL1922 release is approved.

## Preserved scientific and ownership limits

Raw computation remains separate from numerical authority. Bank seed-domain consumer repair is owed before target/evaluator use; actual numerical T still needs review/adoption. Fixed attempted 100/B200, usable and paired denominators, inclusive ties/Kmax over justified T and the single-look rule remain; no interval, endpoint, coverage, futility look, new setting or cap increase is authorized. The owner's shard STOP at 192 stands; max-30 was unused. Existing slice attempts 3 remain, no fourth attempt or job restart by Codex.

Source owns implementation, manifests/resource policy, binding migration, ledger/accounting, admission/adoption, dispatch and current docs/tracker/frontmatter/generated INDEX. Align those copies with the three distinct verdicts, refit hold, actual failed charge, historical pin correction, provisional slack and current policy. Codex owns this record and its own R052/lifecycle entries only. Next source deliverable is the concrete versioned disposition/resource-controller package and its bounded verification evidence; its review must precede refit job 10.

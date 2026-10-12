# Bank job 11: B1 disposition, admission route and retry

Date: 12 October 2026. Codex, exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`.
Whole incoming `prompts/2026-10-12_codex_r052_bank11_closed_no_record.txt`
read at Unimog `ce2931600e31ec1d389258dd2b1f2c4a4b653896`, SHA256
`75e28e2c7ed296182fec56f67ea43bf37da509e6289df9a80b174d0e2d99bc19`;
whole `candidate_bank_r1/DESIGN_B1.md` read first as requested.
Ownership committed at Unimog `a37895e39680370e5226d68da077d0d13bd76385`,
then incoming `ac69d594-cf83-55f7-8bd4-247b4b942665` ACK
`1791790779.093493`, before review edits/delegation.
Exact candidate: RSC `e8f37e595b10656cc877296b172637b2652c089c`.

## Four separate verdicts

1. **Disposition/status as written: NOT FAVOURABLE.** The core charged-failure
   design is appropriate and most guards are present, but B1 can publish a clean
   disposition while ignoring a noncanonical record. Do not adopt the exact
   status/helper bytes yet; repair B1-1 below.
2. **Admission route: NOT FAVOURABLE to the exact upgrade bytes yet. Prefer (a),
   the repaired hardened schema-2 route.** Repair B1-2 through B1-4 and demonstrate
   the preserved qualification/history and deployed identities. Keeping the
   legacy schema-1 route with a procedural receipt rule does not supply the
   proposed current-evidence recomputation. It is not the route approved for this
   new disposition/retry scope.
3. **Job-18 retry authorization now: NOT FAVOURABLE.** The proposed one-job retry
   and its resource/identity arithmetic are sound as a prospective design, but
   its disposition/admission prerequisites are not satisfied by this package.
   No max-job-18 adoption or launch authority is issued here. After the repaired
   exact package is favourable, retain the proposed one-job scope and conditions
   below; the owner's standing conditional go carries without another routine go.
4. **Unchanged manifest with the existing 48-hour override: FAVOURABLE.** Use the
   existing per-submission `--walltime-h 48`, leaving the manifest, scientific
   identities, seeds and binding bytes untouched. This resource-only answer does
   not adopt the defective controller or authorize the retry before 1–3 resolve.

**There is no status or retry ADOPT literal in this record.** Existing historical
jobs-through-17 authority is not expanded. Return repaired exact bytes and focused
metadata evidence for bounded reconsideration; no new fit is needed for these fixes.

## Required repairs

### B1-1. Inventory noncanonical records before declaring a clean disposition

`candidate_bank_r1/row22_bank_dispo.py:104–110` searches a planned rep using the
formatted prefix, e.g. `b240*`. It misses `records/b0240.json`. The bank verifier
at `row22_bank_verify.py:62–79` extracts only the first three digits, interprets
that alias as rep 24, then reads the canonical rep-24 paths instead of the alias.

Concrete static trace: retain valid canonical `b024.json` and its timing; planned
rep 240 has no canonical output; add malformed `records/b0240.json` beside them;
keep the otherwise eligible settled job-11 evidence. The helper never examines
the alias, and the verifier/status final checks see the already valid, planned
rep 24. Status can suppress the three failure-alarm kinds and publish a clean
job-11 disposition despite the stated noncanonical-evidence guard.

The hardened submitter's ordinary filename inventory at `submit.py:76–83` rejects
this alias. This finding is therefore a **false-clean status/shared-proof gap**,
not a claim that this alias successfully dispatches through that submitter.
Require a strict record filename inventory matching the producer's exact format,
with unknown/noncanonical evidence holding rather than being silently mapped to
another rep. Add the `b0240` negative with canonical rep 24 already valid, plus
the existing canonical/temporary-file positives and negatives.

### B1-2. Recompute verified later completion from current record and timing bytes

`candidate_bank_r1/row22_bank_submit.py:235` invokes `DP.closed_no_record` without
`verify_reps`. Consequently `row22_bank_dispo.py:123–144` checks a later timing's
rep/job/slot and plan membership, but skips the producer-runtime record/file-hash
verification and does not validate seed or finite nonnegative measurements.

Start with a valid later bound job-18 completion and clean receipt. Keep its valid
record and attribution, then change only its disk timing's `wall_s` to `-1`, or
change its seed. The disposition recomputation still accepts the rep/job/slot.
Main admission evidence checks records, not timing (`submit.py:70–105`), while
`row22_bank_verify.timing_check:38–50` would reject those current bytes. Likewise,
a self-consistent replacement record can pass ordinary record validity without
matching the receipt's producer-verified file hash. The certificate itself does
not bind these later-completion bytes, so exact certificate equality does not
close this gap.

Require a bound retained producer verification result with current record-hash
agreement, and independently apply the existing timing contract to current bytes
when accepting later completion. Merely passing the old verifier object without
checking current timing is insufficient. Demonstrate disk-only seed/measurement
changes after a clean receipt holding admission, changed record bytes holding,
and an unchanged genuinely verified later completion passing. This is a predicate
and stale-evidence trace; it is not a report of a real altered output or an actual
job-19 dispatch inside the proposed max-18 ceiling.

### B1-3. Require complete typed whole-role summaries

`receipt_problem:202–205` checks that `bound.jobs` equals the current ledger/root
bindings. `dispositions_problem:254–269` then iterates only `receipt.jobs`; it does
not require that summary's job set to equal the bound/current set.

From a clean job-11 disposition receipt, remove both `jobs["11"]` and
`bound.job_outputs["11"]`, preserving the correct `bound.jobs["11"]`. Other job
summaries remain. The binding check passes, no stray output remains, and neither
job-11 recomputation nor its terminal-bad-exit refusal runs. Ordinary record
evidence can still be valid and the planner can propose job 18, which a new
max-18 review would cover. The supposed complete whole-role receipt is incomplete.

Require explicit mapping types and exact equality of summary, bound and current
job sets before validating each job. Add removal of the summary plus output
binding as an integrated admission negative, not only the existing forged-charge
or stray-binding tests.

### B1-4. Make the newly reviewed receipt upgrade reject malformed clean/fresh fields

The inherited hardened gate at `submit.py:195–201` uses truthiness for `alarms`
and only an int/float test plus comparisons for time. A missing/falsy non-list
alarm field is accepted, and a parsed `NaN` time defeats both freshness comparisons.
These are inherited invalid-input acceptance gaps in `ac8209f`, not observations
that any actual receipt is malformed. They matter when this previously undeployed
full gate is first approved as the enforceable fresh-zero-alarm admission route.

Require an explicit empty alarm list and finite non-boolean time within the
existing past/future bounds. Apply the corresponding explicit clean-evidence
checks to the existing qualification input used for schema-2 adoption. Add missing,
wrong-type alarm fields and nonfinite time negatives. No science change or new
measurement is required.

## Credited design and evidence

The helper and status delta retain SETTLED charge/time/note, equal observed and
noted exit, absence of all runner-end fields, the bound plan/token/job, scoped
statuses and unreadable/temporary timings, retrieved unchanged PBS output naming
the job, and the `ADMISSION FAILED` refusal. Only scheduler-exit, missing-runner
and missing-worker-status alarm kinds are suppressed; memory and retained-breach
checks remain. Exit 271, charge, consumed job number and plan-derived uncompleted
reps remain explicit. A dispositioned job cannot qualify.

The authorized PBS fixture hashes to
`f5f1f988cf3d0b4fe2e0c5d8d5f36a8c8f6550a938ee42f8dd9c478a4264fedb`.
It names job 11, its reservation and code `012f3f3`, and ends at admission. It is
consistent with the source's account, but does not independently establish the
live F/271 observation, absence inventory, settlement or candidate zero-alarm run.
Reported 37/37 tests use synthetic roots and a simplified verification oracle;
they were read but **not rerun here** and miss the traces above. The reported
336/408 view and node timings are source observations, not new numerical analysis.

## Preferred migration and bounded retry after repair

Choose route (a) after the fixes. Preserve the deployed legacy controller, old
schema-1 review and actually retained job-1 qualification/history before cutover;
drain controller invocations without touching running scientific jobs. Verify the
existing qualification's actual bytes/bindings and copy the reviewed controller/
helper selectively. The unchanged bank manifest pins ledger `7e8f83b8…`; current
canonical ledger `9a779702…` differs, so a bulk copy of current `chpc/` is wrong.
Retain the bank's pinned science/library/wrapper bytes. Record the archive, old
gate retirement, exact deployed source hashes, schema-2 adoption bound to the
actual qualification SHA and a fresh complete zero-alarm bank receipt. Re-adoption
alone needs no pilot fit replay. Return this concrete provenance/adoption evidence
with the repaired bytes before lifting the retry hold.

For the later retry authority, check the actual fresh one-job plan: **job 18,
reps 240–263 only, one per slot, serial/24 cores/120 GB/48 h**; each rep still missing
and unreserved, same datasets/seeds/bindings. `max_job_number=18` enforces a number
ceiling, not exact coordinates or resources. Existing CLI queue/per-slot/walltime
overrides therefore require this plan/PBS/invocation check; do not describe the
ceiling as automatic enforcement of the whole retry scope. No job 19 or another
retry, replacement datasets or enlarged campaign follows.

The existing normal path propagates 172,800 seconds from `--walltime-h 48` into
reservation, plan, PBS request and job-start (`submit.py:355–377,400–401,434–440`).
The pinned bank worker/ledger validate the reservation. Deadline allowance is
START + 171,000 seconds, or 47.5 h less startup/admission overhead. The manifest
SHA stays `d895c8a3…`; the binding includes the **whole** manifest SHA
(`row22_bank.py:155–161`), so preserve its bytes rather than editing the PBS field.

Source-snapshot arithmetic is correct: 24 × 48 = 1,152 core-hours;
9,141.21 + 1,728 + 1,152 = 12,021.21, leaving 2,978.79 below the unchanged 15,000
bank cap. The 864.76 loss remains charged. Recheck current bank and common-programme
funding, all live reservations/settled losses/declared six hours of other use,
STOP, shared capacity and the cooperative one-job/24-core/48-hour programme window.
The bank snapshot alone does not attest common-allocation headroom. The refit+S
sub-envelope excludes bank, while bank cap/common allocation still apply.

171,000 / reported 94,629 = 1.8071 is useful slack, not a runtime-tail bound.
The worker checks time only before its uncheckpointed fit; `longest` starts at zero
(`row22_bank.py:263–285`). The failed fits are censored, so neither their eventual
completion time nor a node-only cause is known. No host exclusion or completion/
restart guarantee is adopted. Record the actual retry host and distinguish its
result from the failed attempt. Raw-bank permission still does not release a
numerical target or change target/seed-domain/evaluator requirements.

## Identity, validation and ownership limits

Exact candidate SHA256 values:

- design `c9be296ee211339f78289348d729a6ff60cf5594776f57362f1ce4e390dc8e7f`;
- helper `cc33890fde6966b8d3bb180f640be5ffcfda476725565ac86b1d161477b43e44`;
- status `a8be72ccf110090d80639475e835f0c02cf70e185b2c10ccb97f6f0e53905608`;
- submitter `f0c957fd96454176739d493e2dc18b393132d7db3b459625e9d0dcb8f3addf36`;
- tests `34847514f9c130552fedf31094fbbf07d5d4069184d7d84a042db8489f4d9a87`.

Working bytes match the exact commit. Root and three bounded peers inspected
source/deltas/test source and the single authorized fixture, and did deterministic
hash/JSON/resource arithmetic only. Counterexamples are static source traces,
not executed tests or observed incidents. No project imports/execution, fits,
simulations, scientific payload/private reader/audit/live output reads, SSH/AWS,
source implementation/ledger/gate edits, dispatch, job intervention, worktrees or
push. Source clone/runtime/test/receipt assertions remain labelled. Prior refit
controller and pilot reviews/reports remain closed and unaffected. The owner's
standing conditional go, operating ruling and all prior limits carry unchanged.

Source owns repairs/tests/current docs/ledger/gates/adoption/operations/jobs.
Codex owns this record, its own R052 appends, sole findings and lifecycle. Next is
the minimal repaired metadata/controller package and focused negatives, preserving
the positive empty disposition, verified later completion, memory alarms and
ordinary qualifications. No new scientific run is needed to repair these gates.

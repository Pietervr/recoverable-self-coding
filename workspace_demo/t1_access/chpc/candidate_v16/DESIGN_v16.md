# Row 19 screen controls v16 - CANDIDATE, not adopted (the resize controller/resource package)

Written 17 October 2026 (R052, Claude). This is item 4 of the adoption checklist in Codex's resize design
(`reviews/2026-10-17_row19_resize_codex.md`, RSC `08ce9e3`, s.6), which the owner adopted in principle on 17 October 2026
(`chpc/ROW19_SCREEN_DECLARATIONS.md`, final section, RSC `58b7b78`; prereg s.10.1 amendment RSC `5bc33f0`). It is a package for
Codex's review. Nothing here is deployed, promoted or admitted. No ledger, live controller, gate file or Lengau file was touched.
Adopted controls stay at version 15 (`828d3b69`, adoption record `f1bede4`). Until v16 is migrated, no refit admission runs
under the old plan (owner, 17 Oct).

## Files

| File | SHA-256 | Role |
|---|---|---|
| `row19_screen_admit.py` | `1b02f336f174147db975142f62e3dae947deb14f673345cc99120074deb747a0` | admission: REVISION 16 planner, admission check, crash rule, scale-up gate, disabled rescue route |
| `row19_screen_status.py` | `a9f9180b73438221788d745567603fd267befca8fbc60528e3e7de47421ff64a` | status: REVISION 16 designated view, rescue-pending report |
| `row19_screen_designated.json` | `a96eb59833ff794d3f9ce0ca09ada03d045a29cb9f8a676dad86f8aba85d5584` | NEW: the one pinned designated-coordinates declaration |
| `row19_screen_controls.json` | `01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220` | versions 1-15 byte-identical to the adopted file; adds version 16 |
| `test_designated_r16.py` | - | the v16 tests (80 checks, including a replay on the real 17 Oct receipt) |
| `regress/regress_crashed_slot_r14.py`, `regress/regress_pbs_settled_r13.py` | - | copies of the live REVISION 13/14 tests, pointed at any controller directory |

At promotion the first three files are copied into `chpc/` under the same names. The controls' version-16 entry pins them at
`chpc/...`. Every other pinned byte equals version 15: verify, release, programme_gate, the resources policy `f5352bc3`, the
partition and EC2 helpers, the S manifest and plan. The epoch-1 partition `8d1de408` is pinned unchanged, so the e1 activation
proof stays valid: `row19_partition.activation_problem` requires every version from 13 onward to pin it. `qualification_S` and
`deployment` are unchanged.

## What changed, mapped to the design

### (a) The designated set (design s.2, s.1)

> `S = {r in 3..102 : (r−3) mod 5 ∈ {0,1,2}}` ... selects 60 IDs ... and includes rep 83. (s.2)
> Preserve each existing B = 200 producer stream and use indices 0–79 (summary)
> The new controller should stop planning indices≥80 and the 40 unselected reps prospectively; existing jobs finish unchanged. (s.4)

The planner reads exactly one declaration, `chpc/row19_screen_designated.json`. The latest controls version pins its SHA-256;
if the copy is changed or not pinned, every refit admission HOLDS. `designated_shape_problem` recomputes every value from the
manifest and trusts none:

- S from the rule over the manifest's reps: 60 reps, 83 included;
- indices exactly start 0 and stop 80, integers, within B;
- the 13/47 split;
- crash threshold 2;
- rescue declared `enabled: false` with `resources: null`;
- no `ec2_epoch`;
- `first_job_alone: true`.

The tests try 17 edits of the declaration and each one refuses.

History outside the set stays as it is: records, plans, claims, ledger entries and statuses are not deleted or relabelled.
`evidence()` is unchanged, so outside-set records still count as DONE and outside-set live plans as in flight. They still
appear in every receipt, the funding count and the claim scan. The only change is that the planner gives them no new
admission. The view reports them separately as `outside_set_history`. A test shows that planning and the view leave a fixture
root and ledger byte-identical.

### (b) Replicate-complete order (design s.4)

> Change planning to a frozen replicate order, finishing remaining designated indices of a small block before admitting the
> next. With 24 Lengau slots, prioritize the earliest unfinished replicates within the retained 13 ... Skip validated DONE and
> all still-owned live/planned coordinates. Do not select the fastest completed 60.

`designated_order` sorts Lengau's scope by (rep, index) and drops five kinds of coordinate: DONE, in flight (the plans of live
ledger entries with no runner end, as before), crash-excluded, another provider's partition block, and anything outside scope.
`plan_jobs` fills its slots from that list, so each job takes the earliest unfinished replicate's remaining indices before it
moves to the next replicate. The revision-15 index-major round robin is retired: `plan_jobs` raises if a refit plan is
requested without the order. `designated_problem` is a separate admission-time check that refuses any plan containing a
coordinate that is out of scope, done, in flight, crash-excluded or blocked, or a slot with more than one index. Every new plan
records `order: designated-replicate-complete-1` and `designated_sha256`.

### (c) Provider ownership (design s.3, s.4) - the Lengau side only

> Assign the largest 47 IDs in S (24 through 100 in this list) to EC2 for their remaining unclaimed prefix coordinates. The
> smallest 13 remain Lengau's. All existing claims/completions retain Lengau provenance, including 110 live coordinates on
> EC2-designated replicates. ... It is a whole-remaining-work allocation, not retroactive ownership of whole replicates. (s.3)
> A lower-index coordinate ever planned by Lengau is not automatically transferable merely because its worker died. Let its
> declared owner finish/rescue it unless a reviewed transfer explicitly handles that history. (s.4)

The split can be expressed without changing the partition. `lengau_scope` is the union of two sets:

- every designated coordinate of the 13 Lengau replicates (3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20, 23);
- every designated coordinate of the 47 EC2-designated replicates (24 to 100) that Lengau has already claimed, meaning it
  appears in any plan of any ledger state (`row19_partition.lengau_claims`, the same scan the activation uses).

The claimed set on the 47 replicates is closed under Lengau's own planning, because planning there only re-plans an existing
claim. It cannot grow after the migration. The unclaimed designated coordinates of the 47 are never planned by Lengau. They
wait for the separate EC2 provider-epoch package (design s.6 item 5), which must declare that set explicitly. This package
grants EC2 nothing: `providers.ec2_epoch` must be null. Epoch 1 stays enforced (EC2 owns 160..199, which is now outside the
set).

Check against the real Lengau state: the local snapshot and receipt `watch_refit_20261017T170047Z` (zero alarms) give

| S x 0..79 = 4,800 | done 499 | in flight 130 | Lengau plannable 897 | EC2-designated unclaimed 3,274 |

The design (01:29Z watch) has 493 completed + 136 claimed-unfinished = 629, and 897 new Lengau / 3,274 new EC2 coordinates.
The snapshot gives the same 897 / 3,274 and 499 + 130 = 629 (six claimed coordinates completed in between). The test checks
this partition exactly.

### (d) Crash rule (design s.4)

> Crash rule: after two same-envelope fatal allocation/signal crashes, do not issue a third identical attempt. Already-running
> attempts, including rep 83/index 2's current retry, finish untouched. For a still-missing coordinate use one prospective,
> budgeted rescue lane ...

How a crash is counted (`crash_history`):

- **Source.** Only the REVISION-14 crashed-worker slot dispositions in the newest gate receipt. `receipt_problem` recomputes
  each one exactly from the ledger, root and PBS out/err bytes before any admission. No hand list is used.
- **One attempt per (job, coordinate).** Each attempt carries its PBS id, its signal and the job's resolved envelope (queue,
  cores, walltime, memory, nodetype, deadline reserve).
- **Exclusion** (`crash_excluded`). A coordinate is excluded when two or more attempts ran in the envelope the next ordinary
  job would use. An attempt of unknown envelope counts (fail closed).

Admission adds three guards:

- it HOLDS if there is no readable receipt;
- it HOLDS if a current ledger entry with runner exit 4 (HELD) has no disposition in that receipt, because its crash history
  is then unknown;
- it refuses if a newer receipt replaced the planning receipt before the gate judged it, so planning and the gate always
  read one receipt.

Excluded coordinates are listed as RESCUE-PENDING by the dry run and by the status view (`designated_view` is one shared
implementation). They are never dropped from S and never replaced. On the real 17 Oct receipt the history is 83/2 x4 (jobs
13, 14, 17, 30), 43/4 x2 (jobs 20, 30), and 25/6, 81/6, 55/7 x1. All of them ran at 24 x 48 h, the next ordinary envelope. The
excluded set is exactly {43/4, 83/2}. Both are in flight again in job 37, which keeps running untouched; the view marks them
`attempt_running`.

The rescue route is declared and disabled. `--rescue` always refuses in v16. The declaration records the design's allowance
(two full reservations, 2,304 core-h) and leaves `resources: null`.

### (e) The 81,000 core-h sub-envelope (design s.3, s.6 item 4)

> Combined refit+S would reach 80,295.4733: propose a recorded 81,000 sub-envelope, with the 100,000 programme gate unchanged.
> Record the 81,000 sub-envelope through the existing two-phase cap protocol, never by direct ledger edit.

Controls version 16 sets `sub_envelopes[refit+S].cap_core_h = 81000.0`. `campaign_cap_problem` checks the campaign ledger's
own cap as well (60,000 now), so the smaller one binds until the migration raises the ledger. No ledger or budget file is
edited here. The exact command for the migration (RUNBOOK step 5) is:

    $T/t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --raise-cap 81000 \
      --note "owner 17 Oct 2026: resized row-19 screen adopted (Codex design RSC 08ce9e3 s.3): refit+S sub-envelope 81,000 core-h; CSCI1913 100,000 stays the hard stop"

### (f) Unchanged

The following are unchanged:

- the 24-core x 48 h envelope (resources policy `f5352bc3`, jobs >= 10);
- the 4.5 GiB worker stop;
- reservation accounting;
- the programme lock and the 100,000 funding gate;
- the receipt, qualification and review gates;
- the REVISION 8 and 14 dispositions;
- the scheduler's serial max_run 10;
- the pilot's `max_job=100` ceiling: job 45 plus 38 ordinary and 2 rescue jobs fits under it.

### (g) First new-order job alone (design s.4)

> Admit the first prospective Lengau job under the new order alone ... Scale-up stays held until that packing/resource review is
> favourable.

The declaration's `first_job_alone: true` turns on `scaleup_problem`. Until a scale-up is adopted, a call may plan exactly one
job (`--jobs 1`), and only if no new-order plan exists yet. `--adopt-scaleup reviews/<record>.md` writes
`gate/scaleup_refit_v16.json`, which is never overwritten. It requires three things:

- the first new-order job is SETTLED;
- the record is git-tracked and unmodified;
- the record contains `ADOPT row19-screen-v16-scaleup first_job=<n> job_id=<pbs id> plan=<sha256>`.

This follows the pattern of the existing pilot `--adopt-review`.

## Deliberately NOT in this package

- **The EC2 coordinate-set epoch**: partition, allocator, root, ingestion, qualifier and authority (design s.6 item 5). The 47
  replicates' unclaimed coordinates (3,274 on 17 Oct) wait for it. A transfer of a Lengau claim to EC2 also belongs there.
- **The prefix release consumer** (s.6 item 3). `row19_screen_release.py` pins `chpc/row19_screen_admit.py` and
  `chpc/row19_screen_controls.json` in `CONSUMER_FILES`, so that package must re-pin the v16 bytes. Any numerical release still
  goes only through it.
- **Rescue resources**: no host, packing, envelope or qualification. The rescue route is disabled.
- **Any ledger, budget-file, gate or Lengau change.** The cap raise, archive, deploy and receipts are in the draft runbook,
  which has not been executed.
- **The scientific and SI amendments** (s.6 items 1 and 2), omega 2 and HEAL1922.

## Consumers affected (for review)

1. **Qualification rollover.** `generation_problem` requires the verifier's stamped controller generation to be the latest
   version. After deployment every receipt must be fresh under v16, and the refit pilot qualification must be regenerated from
   the existing job 1 with a new hash and no fit. It then needs a new Codex literal and a new `review_refit.json`, as in the
   v13 and v15 migrations (RUNBOOK step 7).
2. **The S admission is now blocked.** `row19_ec2_shadow.decl_problem` hardcodes a 60,000 sub-envelope, so under v16 it would
   refuse to admit S. According to design s.3, S has 1,224.41 core-h settled and 0 live, so no admission is expected. A
   future S retry would need that helper amended and re-pinned.
3. **The status receipt** gains an informational `designated` object. No admission or qualification consumer reads it, since
   the admission recomputes everything itself. Its only new alarm is a declaration that is not pinned or does not recompute.

## Tests (Mac, pure python; run from `workspace_demo/t1_access`)

- `python3 chpc/candidate_v16/test_designated_r16.py`: **80/80 ALL OK**. It covers 1-6 of the brief:
  - the declaration and the lineage pin;
  - selection of exactly S x 0..79 within scope;
  - replicate-complete order;
  - the skipping of done, in-flight and blocked coordinates, and the admission check;
  - the crash rule with envelope semantics and the rescue-pending report;
  - history outside the set left byte-identical.

  It also runs the CLI dry run end to end with the lock, funding and gate stubbed (planning, the HELD guards, first job alone,
  the receipt swap, `--rescue`, the scale-up hold), and a replay on the real 17 Oct receipt and snapshot (the numbers above).
- Regression: copies of the live tests, adapted only in where they load the controllers. Each copy was run against both the
  live adopted bytes (`R19_UNDER_TEST=chpc`) and the candidate:
  - `regress/regress_pbs_settled_r13.py`: **51/51** live, **51/51** candidate.
  - `regress/regress_crashed_slot_r14.py`: **70/71** live, **70/71** candidate. The one failure is the same on both. It
    already fails with the unmodified original `chpc/test_crashed_slot_r14.py` on today's tree: its REAL refit-13 replay
    combines the 12 Oct receipt and verify document with today's live snapshot, so jobs 14-45 appear as unverified units. It
    is stale fixture data, not a code effect.
- The unmodified originals `chpc/test_pbs_settled{,_r12,_r13}.py` stop on today's tree at a bank-tool call that now returns
  five values ("too many values to unpack"). This is pre-existing and unrelated. The r13 copy adapts only that call.

## Open points for the reviewer

1. **Scope rule for Lengau's claims on the 47.** The rule is "any plan, any state" (`lengau_claims`). It would also cover a
   claim that a later EC2 epoch transfers explicitly, so the epoch package must make the Lengau scope subtract its transferred
   set.
2. **Order across Lengau's two kinds of scope.** The order is ascending rep across all of Lengau's scope. Returned claims on
   EC2-designated replicates (for example a later crash or deadline leftover on rep 50) therefore come after reps 3-23. The
   design text "prioritize the earliest unfinished replicates within the retained 13" is read as the frozen ascending order.
3. **Which crashes count.** Every REVISION-14 fatal-signal disposition is counted (Segmentation fault, Bus error, Aborted,
   Illegal instruction). The LLVM "Cannot allocate memory" line in the slot log is not parsed, because the logs are not
   receipt-bound evidence. All nine real crashed slots (jobs 13, 14, 17, 20, 28, 30 x3 and 33) are Segmentation faults.
4. **What "same envelope" means.** It is the resolved request (queue, cores, walltime, memory, nodetype, reserve). A
   changed ordinary policy would allow two new ordinary attempts. Packing and host are not part of the key, because every
   ordinary job is 24 x 1 on haswell_reg.
5. **Scale-up gate.** The gate-file plus literal mechanism is new and needs its own review.

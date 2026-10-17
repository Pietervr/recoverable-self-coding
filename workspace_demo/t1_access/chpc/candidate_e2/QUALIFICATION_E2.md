# EC2 provider epoch 2: qualification plan for the 76-worker packing (PLAN ONLY, not built, not run)

Written 17 October 2026 (R052, Claude), for Codex's review with the epoch-2 package (`DESIGN_e2.md`). Nothing here has run.
No instance, certificate, release or spending exists or is authorised by this plan. It is declared before any epoch-2
result exists, as `aws_ec2/QUALIFICATION_PLAN.md` was for epoch 1.

Design basis, Codex resize design `reviews/2026-10-17_row19_resize_codex.md` s.3:

> Production is unreleased. A matching R1-R5 certificate/review/release for the new epoch and actual packing is mandatory:
> exact successful-path parity, full 76-worker memory/occupancy evidence, bound bundles/producer statuses and ingestion
> replay. A crashed Q2/S coordinate is not an invented scientific failed-fit record. R5 proves ingestion publication
> recovery, not producer-host restart.

> If the 76-worker memory/release gate fails, return to the owner with a newly costed packing/design; do not consume the
> proposed budget as endless qualification retries.

s.5: "Existing qualification evidence may support the newly reviewed mechanical route only to its demonstrated scope; it
does not itself release a new partition/packing."

## 1. What the epoch-1 evidence shows, and what it cannot

| Run | What ran | State on 17 Oct (ledgers, R052 log) | Use under epoch 2 |
|---|---|---|---|
| Q1 attempt 1 | c7a.24xlarge, 76 workers, eu-north-1a | spot-interrupted after 5.6 h, no fit finished; dispositioned (g14) | Descriptive memory only: 76 occupied, host use about 136-137 GB of 193.7 GB before any fit finished |
| Q1 attempt 4 | the same contract, eu-north-1b | reconciled, 21.28 h, USD 26.14; ingestion pending; never certified | Evidence of the 76-worker mechanical route (bundle on S3) once read. Its 48 owned coordinates (indices 198/199) are RETIRED under epoch 2 and are never screen units. It must be dispositioned (fenced) before e2 activation. |
| Q2 attempt 1 | c7a.12xlarge, 24 workers | reconciled, 15.97 h, USD 11.70; 23/24 exit 0; slot 12 (rep 15 / index 199) exit 139 (LLVM "Cannot allocate memory" + SIGSEGV) | Cross-host repeat evidence for 23 coordinates. Under the epoch-1 qualifier as written, `check_bundle` requires every outcome int 0, so Q2 gives NO_RELEASE. No epoch-1 RELEASE certificate is obtainable without a reviewed change. |
| S | Lengau isolated shadow, jobs 1-2 | 47/48 references (rep 15 / index 199 OOM) | References for the retired e1 block only |

So no RELEASE certificate exists for any packing. Epoch 2 also changes three things that the epoch-1 panel did not test:

1. **Concentration.** The replicate-complete allocator fills each 72-slot batch from at most two replicates. Batch 1 is 69
   coordinates of rep 24 and 3 of rep 25 (17 Oct replay). Q1's packing spread 48 work coordinates over 24 replicates.
   Codex's point about the Lengau pilot applies here as well: the mixed-replicate run "does not establish peak behavior when
   workers concentrate on one replicate".
2. **Indices.** Production now computes low indices 0..79 of the 47 EC2 replicates instead of 198/199. The code path is the
   same, but the coordinates are new.
3. **Per-slot ingestion.** This is the REVISION 5 contract. A batch with a crashed worker publishes the other slots, and the
   crashed coordinate goes back to the pool (`DESIGN_e2.md` s.3). That path has not run on real output.

## 2. The epoch-2 panel (declared now; fixed, never chosen by outcome)

| Part | Where | What | Size |
|---|---|---|---|
| E2Q1 | ONE c7a.24xlarge spot instance, eu-north-1b, B_full, cap 1.20, the production contract (76 workers, 22 h lifetime) | **52 work coordinates**: the first 52 owned coordinates in the production allocation order, all of rep 24 on 17 Oct, OWNED by E2Q1 and published as production after release. **20 Lengau-completed duplicates**: the lowest Lengau-completed designated coordinates of the earliest EC2 replicates in ascending (rep, index) order, on 17 Oct reps 24 (0-8), 25 (0-5, 7, 8) and 28 (0-2); they never own. **4 sentinels**: the token rule, never among the duplicates. | 76 |
| E2Q2 | conditional, at most one | The identical E2Q1 request (same rule, a new token) used ONLY when E2Q1 ends without a usable bundle for a reason outside the route: spot interruption before the memory gate is met, or RunInstances capacity. A failed or INCONCLUSIVE gate is NOT retried (s.3). | 76 |

The duplicates make the packing concentrated: 61 of the 76 workers are on rep 24, and every duplicate shares a replicate
with work or other duplicates. They also give float-bit parity against Lengau at that packing. Epoch 2 needs no S shadow:
the work coordinates have no reference before release, and their parity rests on R1' at the same packing and replicates,
plus four sentinels in every production batch.

## 3. Release rule R1'-R5' (all must hold; no tolerance; float-bit on the verifier payload)

Each bundle first passes ingestion REVISION 5's own checks under the schema-2 partition: the frozen inventory, the plan
contract, the outcomes (per-slot for work), the effective B_full attestation, complete worker statuses and records valid
against the frozen task.

1. **R1'** The 20 duplicates equal the Lengau screen records. Coverage: at least 15/20 are finite successful on both sides,
   using the procedure's usable predicate. Failed and non-finite paths are compared and reported apart, and never count.
2. **R2'** (replaces R2/S) Every produced work record of E2Q1 is a valid record of its frozen task. There is no reference
   comparison (there is none to make). This is stated as a limitation, not a parity claim.
3. **R3'** (optional; Codex to decide) A fresh-host repeat of some E2Q1 work coordinates. This plan proposes none, because R1'
   is a stronger, cross-platform parity check at the same packing. It records Q1 attempt 4 against Q2 as descriptive
   cross-host evidence to its scope, once read.
4. **R4'** Memory and occupancy at the concentrated packing (the e1 R4 method):
   - at least 10 chronological samples with all 76 planned workers running;
   - peak host use (MemTotal - MemAvailable) over every sample at most 184 GiB;
   - every produced worker's maxrss under the 4.5 GiB stop;
   - **at most 3 unproduced slots** of the 76 (a stricter qualification bound than the production `MAX_UNPRODUCED_WORK = 7`),
     each of a qualifying kind;
   - every crash signature reported with its slot, coordinate and exit.
5. **R5'** Ingestion recovery on E2Q1's ACTUAL bundle, relocated into a sandbox root under a sandbox schema-2 epoch with its
   predecessor activated:
   - a forced stop after the first published pair, a replay and a second replay, ending `ingested` with every published
     file the register's bytes;
   - plus the per-slot branch. If E2Q1 had a qualifying unproduced slot it is exercised as it is. Otherwise one work slot's
     output is removed in the sandbox copy only, labelled SYNTHETIC in the certificate. The ingestion must list it unproduced,
     fence it, and let a sandbox `ack` release it.

   Scope stated as in e1: this demonstrates ingestion publication recovery only. It does not demonstrate producer or host
   restart, nor interrupted-transfer recovery.
6. **R6'** (mechanical, no instance) The five-instance fleet. These are stubbed-AWS tests of five admissions and five
   reapers on one `prod-e2` run ledger under the run lock, with the fleet ceiling, the cumulative worst-case reservation and
   the per-attempt inventory generations. The owner reads the spot quota for eu-north-1 (512 vCPU granted; five instances need
   480). Attempts 2-3 of Q1 hit InsufficientInstanceCapacity in eu-north-1a, so five-way capacity is not a fact.

**Outcomes.** As in epoch 1:
- NO_RELEASE on any difference or invalid evidence. Production stays shut; return to the owner with a costed alternative.
- INCONCLUSIVE when only coverage is short. There is no release and no retry by outcome.
- RELEASE otherwise. The release names E2Q1, and its 52 work coordinates may then be ingested as production; the duplicates
  stay evidence.

The certificate (schema 3, NOT built) binds the epoch-2 partition `87edfb9e…`, the funding declaration, the operational
manifest, the exact code set (`RELEASE_CODE` with the candidate REVISION-5 files), the bundles, plans, inventory and replay.
`prod_authority.release_problem` needs an epoch-2 branch for it (NOT built): coverage 15/20, R4' and R5' as above, and the
partition pin = the e2 file.

## 4. Cost (inside the USD 300 allowance; `prod_authority.epoch2_problem` enforces it)

| Part | Worst (one attempt) | Counts as |
|---|---|---|
| E2Q1 | 22.75 h x (1.20 + 0.014) + 0.30 = **27.92** | allowance: qualification instance 1 of 2 |
| E2Q2 (conditional) | **27.92** | allowance: qualification instance 2 of 2 |
| 4 extra production batches | 4 x 27.92 = 111.67 | allowance: retries of interrupted or partly unproduced batches |
| total at worst case | **167.51 <= 300** | the counters (2 + 4) bind before the money at worst case |

A third qualification instance, or a 51st production attempt (46 base + 4 extra), refuses in code. "A further attempt
needs a new decision" (s.3).

## 5. After RELEASE

Production admits under the five-instance ceiling. Each instance takes 72 work coordinates in replicate-complete order
plus 4 token sentinels. Any sentinel difference writes `ec2/HOLD` and stops both providers until reviewed. Per-slot
non-completions return their coordinates to the pool. A coordinate whose worker died by a fatal signal in two acknowledged
same-envelope attempts is never allocated a third time: it becomes RESCUE-PENDING, with no EC2 rescue route built. Five
concurrent instances give about 8.87 days of EC2 service (ceil(46/5) x 21.28 h), before capacity, interruption and review
delays.

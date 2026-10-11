# T1 row 19 screen on EC2 + Lengau: production design (DRAFT for review; conditional on row 23)

Status: draft, 10 October 2026, R052. Nothing here runs before (a) row 23's arm B passes its declared success criterion
(all 36 refit payloads float-bit identical to Lengau with identities equal, row-6 panel exact, comparator valid) and
(b) Codex finds this design favourable. Owner, 10 Oct: "continue if the runs are a success".

## 1. Why a static split, not a moving meeting point

Codex (records `2cc26ee`, `137b261`) requires one atomic claim authority across providers before any shared coordinate
space. The simplest authority is a declared, immutable partition: EC2 owns a fixed block of resample indices, Lengau never
plans inside it, and the boundary moves only by a new reviewed declaration. No cross-provider locking, fencing or late
writer can then occupy another provider's coordinate, because no coordinate is ever assignable to both.

- **EC2 block**: indices `[200 - k, 199]` for all 100 reps (reps 3..102), `k` fixed in `ec2_block.json` (pinned by
  sha256 in a controls version). Lengau keeps its index-major ascending order from index 0 (it is at index 2 now).
- **Lengau guard (controls v10)**: the refit planner refuses any coordinate inside the pinned block; the admission and the
  status view report the block. This is the only Lengau controller change. Lengau would not reach index 200 - k for
  weeks, so the guard is a safety net, not a scheduling constraint.
- **Re-declaration**: when one side finishes its share early, a new block file (new `k`) is declared and reviewed; the
  old block's completed coordinates stay EC2's.

## 2. Budget and size

- AWS further-spend cap USD 3,000 from 12 Sept 21:50 UTC. Recorded baseline (`budget_baseline.json`, schema 2): USD 500
  through 10 Oct 00:00 UTC (Cost Explorer 13 Sept-9 Oct 383.13 + all of 12 Sept's non-SageMaker 5.42 + a BOUND of 109.20 on
  12 Sept's post-cutoff SageMaker: 42 d4v12b jobs alive at 21:50 UTC, at most 91 instance-hours, at USD 1.20/h), plus an
  idle accrual of USD 5.50 per started day after it (VPC endpoints + S3). Every EC2 run under `runs/` (row 23 included) is
  charged from its ledger on top. Remaining at 11 Oct: about USD 2,450 before row 23's open worst case.
- One serialized USD ledger (`prod_authority.py`): every production epoch, qualification part and retry against the
  USD 2,300 production envelope; everything against the USD 3,000 cap; per-part qualification ceilings (Q1 28, Q2 17).
- Unit cost to be MEASURED by row 23 (paired walls under load). `k` = floor(envelope / (100 x measured unit cost)), about
  40-55 indices. The full screen (about 19,600 refits left) does NOT fit the cap plus the remaining CSCI1913 allocation;
  that is an owner decision (cap lift, HEAL1922, or design), not something this design assumes.

## 3. EC2 instances (reuse of the reviewed row-23 machinery)

- Launcher/reaper/ledger: `prod_launch.py` (contracts `production`, `Q1`, `Q2` from `chpc/row19_ec2_state.CONTRACTS`)
  under the global authority lock and the run lock; intent + client token, rejected/ambiguous rules, reaper with heartbeat.
- Instance contract `prod_userdata.sh`: Lengau toolchain bytes at the Lengau path, **B_full** only (attested), fail-closed
  setup, STOP checked before job-start and before the first worker, bounded 60 s STOP polling, atomic outcomes, bounded
  cleanup, host memory sampled every 60 s, frozen bundle hashed before the mutable transport logs are written.
- Operational manifest: the exact derivation of `43b75f94` (`row19_ec2_state.derive_operational`; only root, campaign,
  cores, expectation, note and the `ec2_production` block), re-derived and byte-compared by the launcher and the ingestion.
- Production: c7a.24xlarge, **76 workers = up to 72 block coordinates + 4 sentinels** (the Q1 packing); lifetime =
  measured expectation + 900 s setup + 3,000 s upload reserve; a worker whose refit cannot finish before the deadline is
  not started (the worker's own deadline rule).

## 4. Ingestion into the screen root (the reviewed verifier stays the authority)

- `chpc/row19_ec2_ingest.py` (Lengau, t1py, controller tree, plan lock): the Mac authority's sealed inventory names the
  attempt's CURRENT ownership, global sequence and release; the register fence refuses a late writer; the partition must be
  the one the latest adopted controls pin and must carry its activation proof; the bundle passes the full plan / outcome /
  status / attestation contract; comparisons and ownership are rechecked under the lock; STOP or `ec2/HOLD` refuse
  publication; staged bytes are verified before linking; an ingested replay re-validates every registered file.
- Status/admission (candidate controls v10 r1): the receipt's `ec2` section carries the authority inventory of EVERY attempt
  state and `ES.bound(root)` (register, inventory, activations, HOLD, STOP), which the Lengau refit admission recomputes; the
  Mac launcher requires the receipt to bind its current inventory generation. Claims are released on the Mac only by `ack`
  against the register's ingested entry (idempotent, recoverable) or by an explicit `disposition`.

## 5. Ongoing conflict detection and qualification

- Qualification is its own predeclared panel BEFORE any production instance (`QUALIFICATION_PLAN.md`: Q1, Q2, S, release
  rule with successful-path coverage, memory gate and sandbox replay; `chpc/row19_ec2_qualify.py` writes the certificate).
  The first production instance is NOT the qualification instance.
- Every production instance recomputes 4 Lengau-completed sentinels (fixed rule from the token, never by outcome); any
  difference writes `ec2/HOLD`, which holds the attempt's output and refuses every later admission on both providers until
  reviewed. These duplicates are outside the denominator.

## 6. Open for review

1. Static block vs Codex's dynamic-claim requirement: is an immutable reviewed partition an acceptable claim authority?
2. The verifier/status adapter scope (EC2 job kind) and the ingestion rules.
3. Whether 4 duplicates per instance plus row 23 suffice as the prospective production qualification.
4. The envelope (USD 2,300) and the unit cost taken from row 23's measured walls.

## 7. Build status (11 Oct 2026, after Codex 0483db4 V10-1..8; nothing adopted or launched)

| Repair | Built | Consumer / evidence | Still missing |
|---|---|---|---|
| V10-1 activation + derivation | `row19_partition.py activate` (plan lock, controls pin required, handback refused while owned), predecessor/transferred indices; exact operational derivation; plan bound to partition/opmanifest/activation/sequence | Lengau refit admission HOLDS while a pinned partition lacks its proof (v10 r1); EC2 launcher and ingestion require proof, pin and exact derivation; `test_row19_partition.py` 31/31 | adoption of a controls version that pins a real partition |
| V10-2 ownership + receipts | sealed inventory of every attempt (global sequences, owners, fences, generation); ingestion consumes it under the lock; `ack` / `disposition`; receipt `ec2.bound` consumed by both admissions | `test_row19_ec2_ingest.py` 49/49 (stub; same cases on real records on Lengau), `test_row19_ec2_status.py` 22/22, `tests/test_prod_authority.py` 29/29, `tests/test_prod_launch.py` 34/34 | the operator copy of each new inventory to `<root>/ec2/authority/` (scp) |
| V10-3 frozen bundle | hashing excludes the mutable transport logs (d76391d) | `tests/test_prod_userdata.py`: the verbatim hashing command, then the real post-hash writers | - |
| V10-4 complete validation | plan / outcome / status / attestation contracts in `row19_ec2_state.py`, used by ingestion, status and the evaluator | ingestion and status tests above (realistic statuses, typed outcomes) | - |
| V10-5 replay / publication | in-lock rechecks; verified temp bytes; ingested replay re-validation; HOLD on difference | ingestion tests | - |
| V10-6 budget | one serialized ledger across runs/epochs; moving baseline (schema 2); per-part ceilings Q1 28 / Q2 17 | `tests/test_prod_authority.py` | owner acceptance of USD 45 (> 43 declared) |
| V10-7 qualification | `prod_launch.py --contract Q1/Q2`; `row19_ec2_qualify.py` (coverage, INCONCLUSIVE, memory gate, sandbox replay, certificate); `qual_S_plan.json` | `test_row19_ec2_qualify.py` 9/9, `tests/test_prod_launch.py` | **S submission on Lengau** (no isolated qualification-campaign entry kind in the programme gate) |
| V10-8 STOP | checks before job-start and first worker, bounded polling, launcher + recovery on every STOP source, ingestion refuses under STOP/HOLD, propagation of the Lengau root STOP by the v10 r1 status receipt | `tests/test_prod_userdata.py`, `tests/test_prod_launch.py`, `test_row19_ec2_status.py` | - |

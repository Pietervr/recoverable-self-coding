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

- AWS further-spend cap USD 3,000 from 12 Sept 21:50 UTC; Cost Explorer (read 10 Oct): about USD 390 since 13 Sept
  (USD 2,371 from 12 Sept including the pre-cap d4v12b day). Remaining about USD 2,600; row 23 holds USD 42 of it.
- Unit cost to be MEASURED by row 23 (paired wall time per refit under load). Planning figure from the live us-west-2 price
  (c7a.24xlarge 1.71-2.39/h, 80 workers per 96 cores at <= 2.32 GiB each): about USD 0.39-0.55 per refit.
- Proposal: production envelope USD 2,300 -> `k` = floor(2,300 / (100 x measured unit cost)), about 40-55 indices
  (4,000-5,500 refits). The full screen (about 19,600 refits left) does NOT fit the current AWS cap plus the remaining
  CSCI1913 allocation; that is an owner decision (cap lift, HEAL1922, or design), not something this design assumes.

## 3. EC2 production jobs (reuse of the reviewed row-23 machinery)

- Same launcher/reaper/ledger (`bench_launch.py` generalized to `prod_launch.py`): run lock, intent + client token,
  rejected/ambiguous rules, cumulative USD envelope, reaper with heartbeat, attributable terminal accounting.
- Same instance contract (`bench_userdata.sh` -> `prod_userdata.sh`): Lengau toolchain bytes at the Lengau path, the
  **B_full** profile only (attested; arm A is refused by the production guards), fail-closed setup, atomic outcomes,
  bounded cleanup, verified transfer.
- Production manifest: the screen manifest `43b75f94` itself for science; operational root on the instance; each
  instance gets an immutable plan of coordinates from the EC2 block (one index per worker, `job-start` bindings).
- Per instance: c7a.24xlarge, 80 workers; lifetime sized to one refit (about 19-21 h measured) + upload; a worker whose
  refit cannot finish before the deadline is not started (the worker's own deadline rule).

## 4. Ingestion into the screen root (the reviewed verifier stays the authority)

- `ec2_ingest.py` (Lengau, t1py, controller tree): pulls an attempt's records/timings/bindings/outcomes from S3 into a
  staging dir; validates every record with `row19_shard.read_record` against the frozen task, the binding against the
  production manifest, the producer (EC2 attempt id, slot), the timing contract and the block membership; then publishes
  into the screen root by the same temp + link rule (never replacing). Identical duplicates are reconciled; a
  contrary duplicate HOLDS.
- Verifier/status adapter (controls v10): EC2 producers are a second kind of job, keyed by attempt id with their USD
  settlement instead of PBS/core-hours; whole-role receipts cover both kinds; common STOP file.

## 5. Ongoing conflict detection (the production qualification Codex asked for)

- Every EC2 instance also recomputes 4 coordinates Lengau has already completed (rotating across indices and reps,
  chosen by a fixed rule from the coordinate list, never by outcome); their payloads must be float-bit identical or the
  attempt's records HOLD and production stops for review. These duplicates are qualification work, outside the
  denominator.
- First production instance = qualification instance: its whole output is held until its duplicates pass.

## 6. Open for review

1. Static block vs Codex's dynamic-claim requirement: is an immutable reviewed partition an acceptable claim authority?
2. The verifier/status adapter scope (EC2 job kind) and the ingestion rules.
3. Whether 4 duplicates per instance plus row 23 suffice as the prospective production qualification.
4. The envelope (USD 2,300) and the unit cost taken from row 23's measured walls.

## 7. Build status against Codex f3dd3d7 (10 Oct 2026, nothing adopted or launched)

| Contract | Built | Evidence |
|---|---|---|
| 1 partition binding + cutover | `chpc/row19_partition.py` (immutable epoch declaration bound to manifest, task identities, reps, B, k; cutover over every record and every plan of every ledger entry in any state); v10 admit guard in planning AND admission, partition named and sha-pinned by the controls version (`partition: null` = no change) | `test_row19_partition.py` 15/15; live read-only cutover: Lengau max index 2, block 150-199 unassigned |
| 2 EC2 claim/budget authority | `aws_ec2/prod_authority.py` + `prod_launch.py`: fixed-order allocation from the block only; ownership from intent until rejected or ingested; immutable plan per attempt; sequence numbers; per-attempt prefixes; reviewed issue/resolve (same token, single-attempt first dispatch) and reaper reused | `tests/test_prod_authority.py` 13/13 (allocation, ownership, fencing, sentinels, both envelopes); launcher stub tests 13/13 |
| 3 operational derivation | `make_prod_manifest.py`: only root, campaign, cores 76, expect_layer_s (from row 23's MEASURED walls), note; canonical Lengau bindings never written; EC2 bindings kept in the register; B_full only, no fallback | ingestion test: canonical task bindings untouched |
| 4 ingestion | `chpc/row19_ec2_ingest.py`: bundle checksums and no unlisted file; frozen-task validation; EC2 binding; attempt/slot producer; positive finite timings; sentinel float.hex equality; overlap rules; register journal ingesting -> ingested with hash-checked replay; plan lock | `test_row19_ec2_ingest.py` 8/8 on real Lengau records (sandbox) |
| 5 provider-aware status | v10 `ec2_reconcile`: register attempts as a second producer kind; coordinates assigned; producer/slot/status/partition checks; double claim and no-partition alarms; receipt `ec2` section (USD only) | `test_row19_ec2_status.py` 9/9 |
| 6 qualification | `QUALIFICATION_PLAN.md` (Q1/Q2/S, release rule, costs) | declared before results |
| 7 memory | 76 workers (176.3 GiB of 192) incl. 4 sentinels; qualified by Q1 at the intended packing | Q1 |
| 8 budget | `budget_baseline.json` (USD 400 conservative) + production 2,300 / cumulative 3,000 checks before each dispatch, unresolved attempts charged worst case | `tests/test_prod_authority.py` |

Open: common STOP propagation for EC2 (the instance does not yet read the screen's STOP file);
the v10 test-suite update (reconcile now returns a 4-tuple).

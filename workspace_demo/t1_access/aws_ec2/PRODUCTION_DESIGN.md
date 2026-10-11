# T1 row 19 screen on EC2 + Lengau: production design (built, NOT adopted or launched; conditional on row 23)

Status: 11 October 2026, R052. Built as the v11 candidate (RSC `ce78d22` Lengau side, `414d95c` Mac side) after Codex RSC
`3dc0daf` (R1-1..7); awaiting Codex's review of that exact package. Nothing runs before (a) row 23's arm B passes its
declared success criterion (all 36 refit payloads float-bit identical to Lengau with identities equal, row-6 panel exact,
comparator valid), (b) a favourable review of the repaired package, and (c) qualification permission in
`ec2_release_state.json`. Owner: USD 45 for Q1 + Q2 accepted (28 + 17, one attempt each; a retry needs the owner), and
"if qual works, go directly to production" (11 Oct): a successful qualification with a FAVOURABLE actual-result review and
its release certificate proceeds to production with no further owner go, inside the USD 2,300 production envelope and the
USD 3,000 further-spend cap.

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

- **Authority on the root.** The Mac authority seals an inventory of EVERY EC2 attempt; the operator copies it to Lengau and
  `chpc/row19_ec2_root.py install` installs it under the plan lock - monotonic in generation (the same generation only with
  the same bytes), every installation logged. A disposition is a two-phase handshake: the Mac REQUESTS it (the attempt keeps
  owning), the installation fences the attempt in the register and writes `ec2/authority/ack_g<N>.json`, and only
  `prod_authority.py disposition-confirm` against that acknowledgement releases ownership on the Mac. Ingested output is
  released by `ack` against the register's ingested entry. `ec2_sync.py cycle` does the copy and the confirmation; the handshake, not the copy, is the safety.
- **Ingestion** (`chpc/row19_ec2_ingest.py`, Lengau, t1py, controller tree, plan lock): the supplied authority must be the
  root's INSTALLED current inventory; the attempt must be its current owner at its sequence with no disposition request and
  no fenced register entry; the partition is the one the latest adopted controls pin and carries a CANONICAL activation proof
  whose controls lineage still pins it; the bundle passes the full plan / outcome / status / attestation contract;
  comparisons and ownership are rechecked under the lock; STOP or `ec2/HOLD` refuse publication; staged bytes are verified
  before linking; an ingested replay re-validates every registered file. Ingestion never writes the inventory.
- **Activation** (`chpc/row19_partition.py activate`): canonical only against the adopted canonical controls whose latest
  version pins the partition (the Lengau guard is live before the scan, under the same lock); records EC2-completed
  coordinates as EC2's provenance, never as Lengau claims; each EC2 coordinate must lie in the block of its own epoch's
  partition; malformed plans are unknown claims. Sandbox proofs exist for tests and the qualifier's replay only.
- **Status/admission** (candidate controls v11, `chpc/candidate_v10r2/`): the receipt's `ec2` section binds `ES.bound(root)`;
  every Lengau refit admission ALSO rechecks, under its lock, every registered canonical record/timing/status and the
  installed inventory (`row19_ec2_state.current_problems`); the Mac launcher does the same on the pulled snapshot. A missing
  inventory alarms whenever a partition is pinned or any EC2 register/activation exists. EC2 coordinates are checked against
  their own epoch's block.

## 5. Ongoing conflict detection and qualification

- Qualification is its own predeclared panel BEFORE any production instance (`QUALIFICATION_PLAN.md`: Q1, Q2, S, release rule
  with FINITE successful-path coverage, memory at the full 76-worker packing, sandbox ingestion replay with its exact scope;
  `chpc/row19_ec2_qualify.py` writes the schema-2 certificate). The first production instance is NOT the qualification
  instance. Production is released only by `prod_authority.py release-adopt` from a certificate that validates against the
  current code, manifest, partition and the reconciled Q1 attempt, plus a pinned FAVOURABLE actual-result review; the
  released attempts are derived from the certificate.
- Every production instance recomputes 4 Lengau-completed sentinels (fixed rule from the token, never by outcome); any
  difference writes `ec2/HOLD`, which holds the attempt's output and refuses every later admission on both providers until
  reviewed. These duplicates are outside the denominator.
- S (Lengau shadow references) runs through `chpc/row19_ec2_shadow.py`: the existing CampaignLedger kind `shard` and the
  unchanged worker, an isolated root/campaign, jobs 1 and 2 (S1/S2), 24 cores x 48 h, 1,152 core-h each (2,304 reserved),
  under the programme lock and a combined refit+S 60,000 core-h sub-envelope declared in the controls. No new ledger kind.

## 6. Exclusion and region

The reviewed row-23 launcher (`bench_launch.py`) is not under the global authority lock. A production or qualification
admission therefore refuses while any benchmark attempt is unresolved or running; every benchmark charge counts in the
cumulative cap. Region and zone are recorded per attempt and request; an admission refuses while an unresolved attempt was
made in another region, and recovery refuses an attempt of another region. Folding the benchmark launcher itself into the
global lock is deferred until row 23 has ended (its code is not touched while attempt 5 runs).

## 7. Build status (11 Oct 2026, after Codex 3dc0daf R1-1..7; nothing adopted, activated or launched)

| Repair | Built | Consumer / evidence | Still missing |
|---|---|---|---|
| R1-1 adopted activation + provider history | canonical/sandbox modes; lineage-checked proofs; EC2 provenance; per-epoch blocks; malformed plans refused | ingestion, launcher, qualifier, Lengau admission (v11); `test_row19_partition.py` 50, `test_row19_ec2_ingest.py` 60 | adoption of a controls version pinning a real partition |
| R1-2 authoritative inventory transition | `row19_ec2_root.py install`; two-phase disposition with root acknowledgement; installed view required; missing-inventory alarm | `test_row19_ec2_ingest.py`, `tests/test_prod_authority.py` 54, `test_row19_ec2_status.py` 26 | `ec2_sync.py` automates the copy (tests/test_ec2_sync.py); not yet run against Lengau (needs the deployed root tool) |
| R1-3 admission artifact recheck | `row19_ec2_state.current_problems` | Lengau admission (v11) and Mac launcher; post-watch tamper tests in `test_row19_partition.py` and `tests/test_prod_launch.py` 46 | - |
| R1-4 finite coverage, S binding, release adoption | finite predicate + `nonfinite_both`; S producer evidence; `release_problem` / `release-adopt` | `test_row19_ec2_qualify.py` 17, `tests/test_prod_authority.py` | an actual qualification and its review |
| R1-5 STOP | HeadObject 404/NoSuchKey/NotFound is the only absence | `tests/test_prod_launch.py` (timeout, credentials, connection, 403, throttling) | - |
| R1-6 packing + recovery scope | memory joined to occupancy, >= 10 samples at full packing; `replay.scope` | `test_row19_ec2_qualify.py` | producer/host and interrupted-transfer recovery are NOT demonstrated (not claimed) |
| R1-7 integration | exclusion + region freeze; reaper reports production rates | `tests/test_prod_launch.py`, `tests/test_prod_authority.py` | benchmark launcher inside the global lock (after row 23) |
| S route | `row19_ec2_shadow.py`, `row19_qual_S_manifest.json`, controls v11 `qualification_S` + `sub_envelopes` | `test_row19_ec2_shadow.py` 15 | review + adoption of v11; the S manifest in the job clone |

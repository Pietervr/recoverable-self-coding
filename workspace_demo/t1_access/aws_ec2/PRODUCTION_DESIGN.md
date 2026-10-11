# T1 row 19 screen on EC2 + Lengau: production design (built, NOT adopted or launched; conditional on row 23)

Status: 11 October 2026, R052. Codex RSC `cf07869` (review of the v10r3 package): controls v12 (`chpc/candidate_v10r3/`,
80d1c6d9) FAVOURABLE for adoption with partition null (literal ADOPT in that record, not yet performed; it is a controls
opinion, not activation or paid dispatch); the Lengau authority/ACK/generations, post-ACK replay, adopted-controls lineage,
S STOP/HOLD, qualifier and release binding statically closed; the complete Q1/Q2 dispatch basis held on D-1 (a correctly
bound current receipt before every recovery re-issue) and D-2 (drain every in-flight benchmark command before qualification
is permitted) - the historical cf07869 snapshot verdict. Both are repaired in RSC `e644584` (section 6); Codex RSC `1609fa7` found D-1, D-2 and the finish check F-3 closed statically and the Q1/Q2/S basis FAVOURABLE, with operating gates. Epoch-1 partition and controls v13 (Codex RSC `64034c5`): FAVOURABLE to adopt exact controls v13 `d933862e` (since Codex RSC `5bab1a9` the identity in use is `840840f5`: the same v13 with the refit status REVISION 11, which observes settled jobs from their settlement note after PBS dropped finished jobs from its history; the migration scripts and RUNBOOK are re-pointed to it) (`chpc/candidate_v10r4/`, = v12 + the partition pin; helper bytes unchanged) pinning `chpc/row19_partition_e1.json` (sha256 `8d1de408`): k = 40, EC2 owns indices 160..199 of all 100 reps (4,000 coordinates; Lengau keeps the complementary 16,000) - a bounded ownership allocation, not a whole-block funding reservation. Migration DIRECT v9 -> v13 (no v12 step): runbook and scripts `chpc/migration_v13/` (prepared, not executed) - archive the adopted v9, promote/deploy v13 + e1 + the S manifest in the job clone, canonical activation under the plan lock, ec2_sync, fresh receipts, ONE regenerated refit pilot qualification from the existing job 1 (a NEW hash, no fit) with its own reviewed max-100 literal (the 3820ac0e literal never authorizes it). Not adopted, not activated. Nothing runs before (a) row 23's arm B passes
its declared success criterion (valid report, B_full, row-6 panel exact, all 36 refit payloads float-bit identical with
identities equal; `bench_finish.py`, see README), (b) a favourable review of the repaired package, and (c) qualification
permission in `ec2_release_state.json`, set only by `qual_permit.py` after the benchmark cutover. Owner: USD 45 for Q1 + Q2 accepted (28 + 17, one attempt each; a retry needs the owner), and
"if qual works, go directly to production" (11 Oct): a successful qualification with a FAVOURABLE actual-result review and
its release certificate proceeds to production with no further owner go, inside the USD 2,300 production envelope and the
USD 3,000 further-spend cap.

## 1. Why a static split, not a moving meeting point

Codex (records `2cc26ee`, `137b261`) requires one atomic claim authority across providers before any shared coordinate
space. The simplest authority is a declared, immutable partition: EC2 owns a fixed block of resample indices, Lengau never
plans inside it, and the boundary moves only by a new reviewed declaration. No cross-provider locking, fencing or late
writer can then occupy another provider's coordinate, because no coordinate is ever assignable to both.

- **EC2 block**: indices `[200 - k, 199]` for all 100 reps (reps 3..102), `k` fixed in the epoch declaration
  `chpc/row19_partition_e1.json` (pinned by sha256 in a controls version; declared k = 40, indices 160..199, controls v13
  FAVOURABLE in Codex `64034c5`, adoption pending). Lengau keeps its index-major ascending order from index 0 (it was at index 2 on 10 Oct).
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
- Unit cost to be MEASURED by row 23 (paired walls under load). `floor(envelope / (100 x unit cost))` is a PROVISIONAL capped
  planning estimate, not a funding guarantee: net headroom must first carry the qualification, sentinels and tails, partial
  batches, interruptions and retries, and the moving baseline; the authority checks each admission, it does not reserve
  money for the whole block (Codex `64034c5`). Epoch 1 declared k = 40 on that provisional estimate; whether all 4,000
  coordinates complete inside USD 2,300 is not established. The full screen (about 19,600 refits left) does NOT fit the cap plus the remaining CSCI1913 allocation;
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
  before linking; an ingested replay re-validates every registered file. Ingestion never writes the inventory. In canonical
  mode the controls are read only through `row19_partition.adopted_controls` (R2-2). Replay after the Mac acknowledgement
  is supported (R2-1): an inventory showing the attempt `ingested` admits the replay branch only (full re-validation); with
  no ingested register entry it HOLDS - such an inventory can never publish.
- **Activation** (`chpc/row19_partition.py activate`): canonical only against the adopted canonical controls whose latest
  version pins the partition (the Lengau guard is live before the scan, under the same lock); records EC2-completed
  coordinates as EC2's provenance, never as Lengau claims; each EC2 coordinate must lie in the block of its own epoch's
  partition; malformed plans are unknown claims. Sandbox proofs exist for tests and the qualifier's replay only.
- **Root identity and generations** (R2-1): every Mac seal is a new generation archived once (`inventory_g<N>.json`, never
  overwritten); launch seals at intent and after the dispatch outcome, the reaper seals after a production/qualification
  reconciliation. The root's acknowledgement names its root, frozen manifest and mode; `row19_ec2_root.py` grants
  `canonical` only for the production manifest 43b75f94 at its own root, and the Mac releases ownership only on a canonical
  acknowledgement of the canonical root. An installed inventory older than 6 h is accepted at admission only while it shows
  no live or owning attempt.
- **Status/admission** (candidate controls v12, `chpc/candidate_v10r3/`; v11 in `candidate_v10r2/` unchanged): the receipt's `ec2` section binds `ES.bound(root)`;
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
  released attempts are derived from the certificate. Actual-result adoption rule: the certificate binds EXACTLY the
  qualification code set `prod_authority.RELEASE_CODE` (= `row19_ec2_qualify.CODE`: the qualifier, ingestion, state,
  partition, root, shadow, shard worker, verifier, S plan, S manifest, analyze, models) at their current bytes; the
  certificate, both bundles' BUNDLE_SHA256SUMS, plans, operational manifests, S evidence digests and the inventory digest it
  names are kept immutable as the evidence the review reads. `release_problem` itself rechecks the code set, the production
  manifest, the current partition pin and the reconciled Q1 attempt; the remaining bound digests are certificate and review
  attestations, and the inventory legitimately moves on after qualification (no later inventory must equal the
  qualification copy). The actual-result review must state the FAVOURABLE verdict plainly and emit the literal
  `RELEASE row19-ec2-qualification certificate=<sha256> attempts=<key>` only then; Q1 is the only released attempt.
- Every production instance recomputes 4 Lengau-completed sentinels (fixed rule from the token, never by outcome); any
  difference writes `ec2/HOLD`, which holds the attempt's output and refuses every later admission on both providers until
  reviewed. These duplicates are outside the denominator.
- S (Lengau shadow references) runs through `chpc/row19_ec2_shadow.py`: the existing CampaignLedger kind `shard` and the
  unchanged worker, an isolated root/campaign, jobs 1 and 2 (S1/S2), 24 cores x 48 h, 1,152 core-h each (2,304 reserved),
  under the programme lock and a combined refit+S 60,000 core-h sub-envelope declared in the controls. No new ledger kind.
  STOP/HOLD (screen STOP, screen `ec2/HOLD`, S root STOP) is rechecked under the programme lock before the reservation and
  again right before qsub; the S job script mirrors the shared sources into its own root STOP (R2-3). The qualifier accepts
  only the controls-declared S manifest/root/campaign/plan and binds S timings, task bindings, producer ledger entries and
  the declaration; provenance is cooperative (bound, not signed) and stated so (R2-4).

## 6. Exclusion and region

The reviewed row-23 launcher (`bench_launch.py`) is not under the global authority lock. A production or qualification
admission therefore refuses while any benchmark attempt is unresolved or running; every benchmark charge counts in the
cumulative cap. Region and zone are recorded per attempt and request; an admission refuses while an unresolved attempt was
made in another region, and recovery refuses an attempt of another region. In the other direction the benchmark is FROZEN
by an explicit cutover (D-2), not inferred from ledger intents: every benchmark command holds `runs/.bench_inflight.lock`
SHARED from before its entry check to after its last RunInstances issue/retry; `qual_permit.py`, the only way to set
`qualification.permitted`, takes it EXCLUSIVELY - so every in-flight benchmark command, including one still waiting or
staging before its first journal entry, has ended - writes the fence `runs/BENCH_FENCE.json` once, then permits; every
benchmark command refuses at entry and again immediately before every issue, retry and recovery re-issue once the fence
exists, qualification is permitted or any `qual-`/`prod-` attempt exists (fail closed on unreadable state); and
`release_state()` reports qualification ok only with the fence. Attempt 5 keeps its running reaper (it never issues
RunInstances), supervised in its recorded region; per-attempt region routing of a reaper is a stated operating limit.
Every paid production/qualification issue passes a pre-issue guard: STOP from every source and the receipt's 2,700 s
freshness after staging and before each RunInstances call (R2-3). `--recover` re-issues only with a correctly bound
CURRENT receipt - fresh, binding the current sealed inventory, which carries this very attempt (id, sequence, plan,
unresolved state) - and its guard (STOP, age, binding, attempt) runs before EVERY re-issue; otherwise it refuses with zero
RunInstances and the attempt keeps its token, region, plan and worst-case funding (D-1).

## 7. Build status (11 Oct 2026, after Codex cf07869; nothing adopted, activated or launched)

| Condition (Codex cf07869; closures 1609fa7) | Built | Consumers / tests | Still open |
|---|---|---|---|
| D-1 receipt at every recovery re-issue | `prod_launch.recover` -> `recovery_receipt` (snapshot receipt vs the pinned partition, age, current inventory binding, attempt carried) + per-issue guard | `tests/test_prod_launch.py` 62 (stale, missing, unrelated state, older generation, attempt not carried -> zero RunInstances and funded; good receipt -> same token; aged guard refuses) | closed statically (Codex `1609fa7`); operating gate: deploy the repaired CLIs, drain pre-repair commands |
| D-2 benchmark cutover drain | `bench_launch.inflight` + `cutover_problem` (entry and pre-issue); `qual_permit.py`; `release_state` needs the fence | `tests/test_bench_launch.py` 24, `tests/test_prod_authority.py` 66 | closed statically (Codex `1609fa7`); operating gate: deploy the repaired CLIs, drain pre-repair commands |
| F-3 attempt-5 finish | `bench_finish.expected_tree_pins` before and after the comparator | `tests/test_bench_finish.py` 23 | closed statically (Codex `1609fa7`); keep the controller tree fixed during comparison |

Historical table - Codex 299f4b7 repairs (closed statically in cf07869):

| Repair (Codex 299f4b7) | Built | Consumers / tests | Still open |
|---|---|---|---|
| R2-1 generations, root identity, freshness at use, post-ACK replay | `write_inventory` new generation per seal, write-once archives; ACK names root/manifest/mode; canonical-only confirm; `current_problems` freshness while live/owning; replay branch for `ingested` | `tests/test_prod_authority.py` 64, `tests/test_ec2_sync.py` 12, `test_row19_ec2_ingest.py` 68, `tests/test_prod_launch.py` 54 | `ec2_sync.py` not yet run against Lengau (needs the deployed root tool) |
| R2-2 current adopted controls | `row19_partition.adopted_controls`; canonical `activation_problem`, Mac launcher, ingestion, qualifier | `test_row19_partition.py` 54, launcher, ingestion, qualifier tests | adoption of a controls version (v11 and v12 null-only favourable; not yet adopted) |
| R2-3 STOP at dispatch | post-staging recheck + pre-issue guard on every issue/re-issue; S recheck under the lock and before qsub; S STOP mirror | `tests/test_prod_launch.py`, `tests/test_bench_launch.py` 20, `test_row19_ec2_shadow.py` 19 | - |
| R2-4 declared S evidence | declared manifest/root/campaign/plan; timings, task bindings, producer entries, declaration bound; provenance condition stated | `test_row19_ec2_qualify.py` 23 | an actual S run and its review |
| Operating scope | benchmark freeze (entry-only at v10r3; the drain is D-2 above); exact release code set; stale ceiling note removed | `tests/test_bench_launch.py`, `tests/test_prod_authority.py` | reaper region routing |

Historical table - earlier repairs (Codex 3dc0daf R1-1..7; v11-era wording kept as recorded):

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

# EC2 provider epoch 2 - CANDIDATE, not adopted: explicit coordinate ownership for the resized row-19 screen

Written 17 October 2026 (R052, Claude). This package is item 5 of the adoption checklist in Codex's resize design
(`reviews/2026-10-17_row19_resize_codex.md`, RSC `08ce9e3`, s.6). The owner adopted that design in principle on 17 Oct
(`chpc/ROW19_SCREEN_DECLARATIONS.md`, final section, RSC `58b7b78`), choosing five concurrent EC2 instances. The package is
for Codex's review. Codex reviewed RSC `b510ba0` (`reviews/2026-10-17_e2_p80r_codex_review.md`, CHANGE 4); this revision
(REVISION 6 of the changed modules) repairs A1-A4 and applies the rulings that ask for a change - see s.7.

Nothing here is promoted, activated, launched or spent. No AWS command, ssh or Lengau operation was run, and no live file
outside this folder was edited. `candidate_v16/`, `migration_v16/` and `release_p80/` were read only. The live epoch is
still e1 (`chpc/row19_partition_e1.json`, `8d1de408`, activated under controls v13).

Every live and candidate file is a separate copy. At promotion the files below replace their namesakes:
- `row19_*.py` in `chpc/`;
- `aws_ec2/*.py` in `aws_ec2/`;
- the data files at the paths named in the table.

## Files

| File (this folder) | SHA-256 | Role | Promoted to |
|---|---|---|---|
| `row19_partition.py` | `eabf50c34be2bad3f92e07370966bcc94162cf12cbcefb326cc07a72d49ac0d8` | REVISION 6: schema `row19-provider-partition-2`, `snapshot` (canonical under the plan lock) / `declare2` / `verify2`, schema-2 activation hand-over | `chpc/` (live `ed6aa177`) |
| `row19_ec2_ingest.py` | `6ac144c616d330c83fcd5e665bdc48a9396d962e4aacba03c4775e26950ce108` | REVISION 6/7: schema 2, owned-work check, per-slot (partial) ingestion; present status never overridden by the censor label; a present status file must be a JSON object (a present null/list/scalar is never absence, R7); censor list bound; failure evidence journaled and replayed | `chpc/` (live `b697dc36`) |
| `row19_ec2_qualify.py` | `efff0f95b83a5c53af9681dd13472760c3ee2de164f2ec302690ae63a0473b2e` | REVISION 4: reads schema 2, REFUSES to certify it with the e1 panel | `chpc/` (live `1fc6b61f`) |
| `aws_ec2/prod_authority.py` | `fd9e67bb6684c27d960f28ae48a92c52575b49f5dfad473f77fda92b55f0101a` | REVISION 6: replicate-complete allocator capped at 57 per replicate per batch, fleet ceiling 5, epoch-2 allowance, funding against the pinned Q2 basis, crash rule on the shared fatal-signal set, ack with classified unproduced | `aws_ec2/` (live `b8ca02b8`) |
| `aws_ec2/prod_launch.py` | `143c5221c30daac7d1482275bed70ec5bfa323bdff7733748cecd14dc832fa9b` | REVISION 6: schema-2 production plan inside the qualified concentration, fleet + epoch gate (authenticated basis, funded lifetime) in admission | `aws_ec2/` (live `21b7cf57`) |
| `aws_ec2/make_prod_manifest.py` | `ad1f99e2421caab467847602504ba450305ef14ab8edc01d4d9fea5e996571b3` | REVISION 2: epoch >= 2 only at the funded geometry and 22 h lifetime | `aws_ec2/` (live `8da79911`) |
| `aws_ec2/make_e2_funding.py` | `85e1b69cb6c993dfa9a37252f30c91a2afdc10932d389b331d5136a51f743554` | NEW (REVISION 2): writes the funding declaration derived from the pinned Q2 basis | `aws_ec2/` |
| `row19_partition_e2.json` | `87edfb9edbbc4b5e776f17bcf5cc6a74884e9158d6fa7d1c53f79faa0fa468d9` | the epoch-2 declaration (CANDIDATE bytes; re-declared at migration) | `chpc/` |
| `claims_snapshot_e2.json` | `043db6096da32372ab193869add3aa130de4e81cece28cb03ef50a13449acefc` | the hashed claims snapshot it was generated from (Mac copy of 17 Oct 17:00Z) | (input; retaken on Lengau) |
| `aws_ec2/e2_funding.json` | `d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815` | the derived epoch-2 funding declaration (names the pinned Q2 attempt, 61 / 57 packing; same numbers) | `aws_ec2/` |
| `row19_ec2_e2rules.py` | `a9ea1f61daa577b642739ae781cb179e9a2089d42d3c23fff277d7d4849a3bcc` | NEW (s.7): the one shared classification - fatal-signal set, orderly LEFT status, qualified concentration 61, R4' bound | `chpc/` (and the Lengau controller tree) |
| `aws_ec2/prod/manifest_production_e2.json` | `e126050536a8459cb1432cf78321e82147c67f5406441fff131a1f543f9f82f9` | epoch-2 operational manifest (`derive_operational`, production, expect 75,300 s) | `aws_ec2/prod/` |
| `admit_v17_partition_line.diff` | `0fc23704…` | the one Lengau-controller line v17 must change (not applied; see s.5) | (into v17) |
| `QUALIFICATION_E2.md` | - | item c: the epoch-2 qualification plan (not built, not run) | - |
| `test_e2_partition.py`, `test_e2_authority.py`, `test_e2_ingest.py`, `test_e2_rules.py`, `regress/run_regress.py`, `test_results.txt` | - | item d: tests and their results | - |

Unchanged on purpose:
- `chpc/row19_ec2_state.py`: the contracts, the plan contract, the inventory and the register schema (the new register field
  `unproduced` is optional).
- `chpc/row19_ec2_root.py`: install and identity never read the partition.
- `prod_userdata.sh` and `ec2_sync.py`: the plan already drives the instance, and sync releases only through `ack` and
  `disposition_confirm`.

## Replay on the latest saved receipt and snapshot (17 Oct)

Inputs: the Mac copy `chpc/results/row19_screen/live/refit/` (root and campaign) belonging to receipt
`watch_refit_20261017T170047Z.json` (zero alarms; the same pairing the v16 replay used), the designated declaration
`candidate_v16/row19_screen_designated.json` (`a96eb598`), e1 `8d1de408`, and the authority ledgers and inventory g42 (read
only).

| Quantity | Value | Design text |
|---|---|---|
| Lengau claims snapshot | 832 records, 1,047 ever-planned coordinates, 0 EC2-completed | - |
| Designated D = S x 0..79 | 4,800 | s.2 |
| Done (Lengau records in D) | 499 | v16 replay: 499 |
| Lengau open (13 reps + Lengau claims on the 47, not done) | 1,027 (= v16's 130 in flight + 897 plannable) | s.3: 897 new Lengau + 136 claimed |
| **EC2 owned** (unclaimed designated coordinates of the 47) | **3,274** | s.3: "3,274 new EC2 coordinates" |
| Lengau claims on the 47 EC2 replicates inside D | 486 (104 not yet done), all Lengau's | s.3: "including 110 live coordinates" (01:29Z) |
| e1 block retired | 4,000 (indices 160..199, all reps), nothing transferred to Lengau | s.4, s.5 |
| **Batches** at 72 work + 4 sentinels / 76 workers | **46** (45 x 72 + 34), 3,496 paid slots; at most 57 work coordinates of one replicate per batch (batch 1: rep 24 x 57 + rep 25 x 15; s.7 A3), 1-3 replicates per batch | s.3: 46 / 3,496 |
| **Forecast** (Q2 USD 11.700804, 24 planned / 23 successful) | **USD 1,704.42** planned-slot / **1,778.52** successful-slot (carried) | s.3: 1,704.42 / 1,778.52 |
| Funding maxima, all 46 at worst case | USD 1,284.251 (46 x 27.9185) | s.3: 1,284.251 |
| Epoch cap = forecast + allowance | USD 2,078.52 | s.3: 2,078.52 |
| Remaining production envelope | USD 2,255.04 (Q1 33.264 + Q2 11.701 = 44.965 charged) | s.3: 2,255.03505 |
| Remaining under the USD 3,000 cap now | USD 2,383.36 (baseline 544.00 + runs 72.64); the epoch cap leaves 304.84, i.e. about 55 days of idle accrual at 5.50/day | s.3: 2,383.36 |
| Calendar at the five-instance ceiling | ceil(46/5) x 21.2811 h = 8.87 days | s.3: 8.87 |

## What changed, mapped to the design

### a. Schema `row19-provider-partition-2`: explicit coordinate-set ownership (s.3, s.4, s.6 item 5; v16 review s.A item 1)

> Assign the largest 47 IDs in S (24 through 100 in this list) to EC2 for their remaining **unclaimed** prefix coordinates.
> The smallest 13 remain Lengau's. All existing claims/completions retain Lengau provenance ... It is a whole-*remaining-work*
> allocation, not retroactive ownership of whole replicates. (s.3)
>
> The present partition declaration always creates a suffix across all 100 reps ... changing k does not create ownership of
> selected replicates' low indices. Use a new predecessor-linked epoch and a reviewed explicit coordinate-set/remaining-work
> schema. ... Never erase old claims to satisfy the activation scan. A lower-index coordinate ever planned by Lengau is not
> automatically transferable merely because its worker died. (s.4)
>
> A later reviewed epoch must explicitly subtract any transferred claims from Lengau's scope; changing only the suffix `k`
> is insufficient. (v16 review s.A item 1)

**The declaration.** `row19_partition_e2.json` lists `owned` as {rep: [indices]}, with `owned_count`, `owned_sha256` and:
- `predecessor` {epoch 1, schema 1, sha256 `8d1de408`, 4,000 coordinates and their digest};
- `designated` (path, sha256 and split of the v16 declaration);
- `claims_snapshot` (sha256, claims digest, source receipt);
- `transferred: []`;
- `retired` (count and digest of the predecessor coordinates not owned now);
- `cover` (designated / lengau_done / ec2_done / lengau_open / ec2_owned).

**The rule.** `owned` = the designated coordinates of `ec2_reps` that the snapshot shows Lengau never completed, never planned
in any plan of any ledger state, and that EC2 never completed. Everything Lengau ever planned stays Lengau's. Nothing is
subtracted from Lengau's scope, so the explicit subtraction the v16 review requires is the empty set, and the schema states
that (`transferred` is always []). A hand-back of an owned coordinate to Lengau refuses in `declare2`, because v16's
`lengau_scope` cannot plan it without a reviewed scope change (DESIGN_v16 open point 1).

**Generation.** `row19_partition.py snapshot` writes `row19-lengau-claims-snapshot-1` from `lengau_claims`, the same scan the
activation uses. It runs on Lengau under the plan lock or on a pulled copy, binding the receipt by name and sha256.
`declare2` generates the declaration deterministically from the manifest, the designated declaration, the snapshot and the
predecessor. `verify2` regenerates it and requires equal canonical bytes.

**Validation** (`load`, schema 2):
- the exact field set, the manifest, the task identities and B;
- the predecessor shape;
- the bound designated declaration's bytes at its path and its recomputed shape;
- owned ⊆ ec2_reps x [0, 80), with the digest and count;
- the cover adding up.

`ownership_problem` recomputes the **disjoint cover**: (D - done) = Lengau-open ⊔ EC2-owned, owned ∩ claims = ∅, owned ∩
Lengau-open = ∅.

**Consumers.** `blocked(part, rep, index)` stays the single predicate (membership in `owned`). The Lengau planner and
admission guard (v16 `designated_order`, `designated_problem`, `partition_problem`) and the status view therefore work
unchanged, except one print line (s.5). `historical_partitions` and `activation_problem` accept both schemas; a schema-2
proof also binds `owned_sha256`.

**Activation (schema 2), on top of the existing scan.** It runs under the same plan lock and needs:
- the predecessor's activation present and naming e1;
- the root's INSTALLED, sealed, fresh inventory showing no attempt owning a coordinate outside the epoch, so the reconciled
  Q1 attempt 4, owning 48 retired coordinates, must be dispositioned and fenced first;
- no live attempt of another epoch.

A Lengau claim made on an owned coordinate after the snapshot refuses the activation (re-snapshot, re-declare).

### b. Consumers: allocator, ingestion, qualifier, authority, launcher, manifest builder

**Allocator (s.4).**

> EC2 allocates a batch to enough early replicates to fill its 72 work slots, completes their remainders, then advances.

`prod_authority.allocate` on a schema-2 partition takes the owned set in ascending (rep, index), skipping completed,
currently owned and EC2-crash-excluded coordinates. The replay gives 46 batches covering the 3,274 coordinates exactly once.
Schema 1 keeps its order.

**Geometry (s.3).** "At the declared 76-worker geometry, 72 unique work +4 sentinels per instance ... 46 full batches /3,496
paid slots." The `production` contract (unchanged: c7a.24xlarge, 76 workers, 4 sentinels, cap 1.20) carries it. The
launcher builds 72 work + 4 token sentinels (Lengau-completed, never owned); the final batch is 34 + 4.
`make_prod_manifest.py` refuses an epoch >= 2 manifest at any lifetime but the funded 22 h (expect 75,300 s), and writes
`prod/manifest_production_e2.json`.

**Fleet ceiling and cumulative reservation (s.3, s.6 item 5; owner: five instances).**

> explicit fleet ceiling and cumulative money/concurrency reservation (s.6 item 5); The authority must enforce both caps on
> every attempt. (s.3)

`FLEET_CEILING = 5` is checked in admission under the global authority lock (`fleet_problem`). It counts every
production/qualification attempt of any run in intent, launched or ambiguous. Every such attempt is charged its worst case
(USD 27.92) until reconciled, so five live instances reserve 5 x 27.92 cumulatively against the USD 2,300 envelope, the
USD 3,000 cap and the epoch cap before another admission is judged.

**Allowance (s.3).**

> Bound that allowance to at most two new qualification instances and four extra production batches, all together within
> 300 USD; a further attempt needs a new decision.

`epoch2_problem` reads `e2_funding.json`, and `funding_problem` rederives it from the partition, the Q2 basis and the owner
constants, so a hand edit refuses. It enforces:
- at most 46 + 4 non-rejected `prod-e2` attempts;
- at most 2 non-rejected `qual-E2*` instances;
- allowance money at most USD 300, counting every `qual-E2` attempt and every production attempt beyond the first 46 by
  sequence, at worst case until reconciled;
- the whole epoch at most USD 2,078.52.

The owner constants (5, 300, 4, 2) are code constants, so a funding file can only carry derived numbers.

**Ingestion (s.3, s.5).**

> A crashed Q2/S coordinate is not an invented scientific failed-fit record. (s.3)

REVISION 5 accepts the schema-2 partition and HOLDS when any work slot is not an owned coordinate of the epoch. It also adds
**per-slot ingestion** for schema-2 production attempts, which the design does not spell out. This is a new contract; see
s.3 below.

**Qualifier.** It reads schema 2 and refuses to certify it with the e1 panel (Q1/Q2/S coordinates are retired). An epoch-2
release needs `QUALIFICATION_E2.md`.

**Root / state / userdata / sync.** No change is needed (see the file table).

### c. Qualification - `QUALIFICATION_E2.md` (plan only)

- E2Q1: one production-geometry instance, 52 owned work coordinates (rep 24), 20 Lengau duplicates on the same early
  replicates, 4 sentinels.
- E2Q2: a conditional identical retry, only after spot interruption or capacity.
- R1' 15/20 float-bit parity; R2' validity only; R3' optional; R4' memory at the concentrated packing, with at most 3
  unproduced slots; R5' sandbox replay including the per-slot branch; R6' a stubbed five-instance fleet test and the quota
  read.
- Worst case 2 x 27.92 + 4 x 27.92 = USD 167.51, inside the USD 300 allowance.

### d. Tests (Mac, pure python; `test_results.txt`)

Counts after the REVISION-7 repair: partition 54/54, authority 77/77, ingest 63/63, rules 35/35 (`test_results.txt`; s.7
lists the REVISION-6 checks; REVISION 7 adds 17 present-status checks to `test_e2_ingest.py`). The lists below describe the original checks.

- `test_e2_partition.py` **54/54**:
  - regeneration and determinism;
  - the disjoint cover on the real snapshot (499 / 1,027 / 3,274 / 4,800);
  - no owned coordinate is a Lengau claim, including rescue-pending 83/2 and 43/4;
  - the v16 planner's scope and order are disjoint from the owned set and cover the rest;
  - the predecessor link (sha, 4,000 retired, nothing transferred, wrong epoch and hand-back refused);
  - 10 tamper refusals;
  - sandbox activation (predecessor required, inventory required, the Q1 owner blocks, a live other-epoch attempt blocks, a
    post-snapshot Lengau claim blocks, the lineage).
- `test_e2_authority.py` **54/54**:
  - the REAL read-only replay of the ledgers and funding (44.96 charged, 2,078.52 fits 2,255.04, 46 / 3,496, the forecasts,
    8.87 days);
  - the allocator (46 batches exactly cover; skips);
  - the fleet ceiling (5 refuse a sixth; ambiguous counts; rejected and benchmark don't);
  - cumulative reservation;
  - the allowance (46 + 4, 2 qualification, USD 300, epoch cap, funding tamper);
  - the crash rule;
  - ack with unproduced;
  - the launcher's 76-slot plan passing the unchanged plan contract;
  - the epoch gate.
- `test_e2_ingest.py` **22/22**:
  - complete, owned-work check and replay;
  - per-slot: 139, censored, RESUME 75 with a left status, one lost sentinel;
  - HOLDs: output left behind, exit 4, a signal with a status, exit 1, RESUME without a status, too many unproduced, too few
    sentinels, an unknown string;
  - the Mac ack of a partial entry;
  - qualification stays all-or-nothing.
- Regression (`regress/run_regress.py` substitutes the candidate modules into the UNMODIFIED existing tests). Results are
  identical to the live modules:

  | Test | Passed |
  |---|---|
  | partition | 63 (+2 pre-existing stale fails) |
  | ingest | 68 |
  | qualify | 23 |
  | status | 26 |
  | prod_authority | 66 |
  | prod_launch | 61 (+1 pre-existing stale fail) |
  | ec2_sync | 12 |
  | v16 `test_designated_r16.py` | 80 |

## 3. A new contract beyond the design text: per-slot ingestion

The live ingestion is all-or-nothing: every outcome must be int 0. The evidence:
- Q2 lost 1 of 24 slots (exit 139, LLVM ENOMEM + SIGSEGV);
- Lengau's 35 settled refit jobs had 9 crashed slots in about 807 new coordinates (about 1.1 %);
- as independence illustrations only, not measured batch-completion forecasts (ruling 7): 0.989^76 = 43 %, and at Q2's rate
  (23/24)^76 = 4 %. Nine crashes among about 807 new Lengau coordinates are not an IID 76-slot production cohort.

All-or-nothing would discard most batches and consume the four-batch allowance at once. REVISION 5 therefore publishes every
fully valid slot and marks a non-completed slot UNPRODUCED, but only in three kinds:
- a fatal signal (exit 129..159) with no status - the crashed-worker signature, since the worker writes a status on every
  orderly exit;
- the worker's RESUME 75 with a status leaving the coordinate;
- the censored marker, bound to the producer's frozen `env/censored.txt` (REVISION 6).

A present status, under RESUME 75 or the censored marker alike, must be the worker's own orderly LEFT status (exit 75, an
orderly deadline/STOP reason, full accounting, maxrss within the stop); the censor label never overrides it (s.7 A1).

In all three, no record or timing may be present. Everything else HOLDS the whole attempt as before:
- exit 4 (the worker's own HELD guard), any other exit, output beside a nonzero outcome;
- more than 7 unproduced work slots (a resource failure);
- fewer than 3 sentinels produced;
- any sentinel mismatch (ec2/HOLD).

The register lists `unproduced` with each exit, and the fence is raised there. The Mac `ack` releases published + unproduced,
which must equal the owned set exactly, and records the exits. A coordinate whose worker died by a fatal signal (REVISION 6:
any exit 129..159, the set ingestion admits) in two acknowledged same-envelope attempts (contract, instance type, lifetime) is never allocated again. This
is the EC2 form of s.4's "after two same-envelope fatal allocation/signal crashes, do not issue a third identical attempt".
No EC2 rescue route is built.

Qualification attempts and every schema-1 epoch keep all-or-nothing.

## 4. Choices the design left open (each needs Codex's view)

1. **Claims source = `lengau_claims`.** It covers record files EC2 did not publish, plus every plan of every ledger state
   and every plan file. It is the activation's own scan; verify-ok and record counts agree here (499). The candidate bytes
   come from a Mac COPY bound to the 17:00Z receipt; the adopted bytes must come from a fresh Lengau snapshot after v16 is
   live (s.6).
2. **The designated declaration is untouched** (`ec2_epoch` stays null). The epoch file is the ownership authority and
   binds the declaration's sha256, so v16's `designated_shape_problem` stays as reviewed.
3. **The e1 block is retired, not handed back or kept.** Q1 attempt 4 is dispositioned (fenced), not ingested. Q1/Q2/S stay
   evidence only (s.5). A hand-back to Lengau is impossible in this schema.
4. **Stricter activation hand-over.** No owner outside the epoch and no live attempt of another epoch (e1 checked only the
   handed-back indices). Q2 attempt 1 owns nothing and does not block.
5. **Allocation order** is strictly ascending (rep, index). Codex accepted it mechanically, conditional on A3; REVISION
   6 caps a batch at 57 work coordinates of one replicate so no plan exceeds E2Q1's 61 (s.7).
6. **Sentinels** keep the token rule over all Lengau-completed non-owned coordinates. They are not tied to the batch's
   replicates.
7. **Per-slot ingestion bounds:** 3 qualifying kinds, `MAX_UNPRODUCED_WORK = 7`, `MIN_SENTINELS_COMPARED = 3`, censored
   allowed, exit 4 holds. Accepted in principle after A1 and the replay repair (s.7); the limits are prospective operational
   choices, not statistically established safe rates.
8. **EC2 crash rule:** changed per A2 - every fatal exit 129..159 (exit 137 is SIGKILL; OOM only with host evidence),
   envelope (contract, itype, lifetime), threshold 2.
   Censored and dispositioned (spot) attempts do not count; they spend the allowance instead.
9. **Allowance accounting:** "extra" = production attempts beyond the first 46 non-rejected by sequence; qualification runs
   are named `qual-E2*`; money is at worst case until reconciled; the epoch cap (forecast + allowance) is enforced on top of
   the 2,300 / 3,000 envelopes. With six attempts at 27.92 (167.51) the counters bind before the money.
10. **The fleet ceiling** counts production and qualification of every epoch in intent, launched or ambiguous. Benchmarks are
    excluded by the existing exclusion rule.
11. **The forecast basis** is Q2's ledger charge plus the declared 23/24 slot outcome (R052 log 16 Oct). The successful
    count is a declared constant, not read from a bundle.
12. **E2Q1 panel** 52 / 20 / 4, no S, R3' optional (`QUALIFICATION_E2.md`).
13. **Five reapers on one `prod-e2` ledger.** The run lock serialises them, but this is untested (R6').

## 5. NOT done in this package

- **Controls v17.** It must be built on the adopted v16 bytes:
  - pin `row19_partition_e2.json` in place of e1;
  - pin the REVISION-5 helpers (`row19_partition.py`, `row19_ec2_ingest.py`, `row19_ec2_qualify.py`);
  - apply `admit_v17_partition_line.diff`. v16's admission prints `part['indices']`/`part['k']` (line 2102) and would raise
    KeyError on a schema-2 partition; the status view needs no change.

  v17 needs its own review and adoption literal.
- **The epoch-2 qualification**: E2Q1/E2Q2 contracts, a schema-3 certificate, an epoch-2 branch of
  `prod_authority.release_problem` (coverage 15/20, R4'/R5'), and `RELEASE_CODE` extended to the candidate files.
  Production stays shut until all of these exist, and the e1 RELEASE path cannot open epoch 2 (its partition pin differs).
- **An EC2 rescue route** for crash-excluded coordinates.
- **The e1 certificate.** It is not obtainable with the qualifier as written (Q2's crashed slot fails `check_bundle`).
  Q1/Q2 remain descriptive evidence.
- **Any AWS, ssh, Lengau, ledger, inventory, release-state or live-file change.**

## 6. Adoption and migration (proposed order; on the `migration_v13/RUNBOOK.md` pattern)

1. **Prerequisite.** Migrate v16 and make it active: archive v15, promote/deploy, cap raise, receipts, pilot rollover, first
   new-order job. After v16 Lengau never plans an unclaimed coordinate of the 47, so the claimed set there is closed and the
   owned set cannot shrink after the snapshot.
2. **Codex reviews this package.** A re-review follows any change.
3. **Fence the e1 owner** on the Mac:
   `python3 aws_ec2/prod_authority.py disposition --run qual-Q1 --attempt 4 --reason "epoch 2: e1 block retired out of the designated design; Q1 output is qualification evidence only (Codex resize s.5)"`,
   then `python3 aws_ec2/ec2_sync.py cycle`. The root fences the attempt in the register and writes `ack_g<N>`, and sync runs
   `disposition-confirm`. Q2 owns nothing; dispositioning it is optional bookkeeping. The bundles stay on S3 as evidence.
4. **Final snapshot.** On Lengau under the plan lock (REVISION 6: the canonical `snapshot` command takes it itself), with the candidate `row19_partition.py` (REVISION 6) deployed in the
   controller tree as data and not yet pinned:
   `row19_partition.py snapshot --manifest chpc/row19_screen_manifest.json --out chpc/claims_snapshot_e2.json`, at a fresh
   zero-alarm receipt. Then `declare2 ... --epoch 2 --out chpc/row19_partition_e2.json`. On the Mac: `verify2`,
   `make_e2_funding.py` and `make_prod_manifest.py --epoch 2 --contract production --expect-s 75300`. Codex reviews the exact
   partition and funding bytes. If the owned count differs from 3,274, the funding is rederived; nothing is chosen.
5. **Controls v17 and the common adoption.** Promote/deploy the helpers, v17, the e2 file and the Mac files: drain controller
   commands, keep scientific jobs running, and keep the Never list. From v17's adoption until activation, Lengau refit
   admission HOLDS (`activation_problem_v10`).
6. **Activation** under the common plan lock on Lengau:
   `t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json`.
   It requires the adopted canonical controls pinning e2, the e1 activation on the root, a fresh installed inventory (run an
   `ec2_sync` cycle within 6 h before), no outside owner, and no Lengau claim on any owned coordinate. The e1 proof stays on
   the root as provenance; nothing is erased.
7. **ACK and receipts.** Run `ec2_sync.py cycle` (a new generation installed and acknowledged), then a fresh whole-role
   receipt binding `activation_e2.json` and the new inventory.
8. **Qualification.** Build and review the epoch-2 qualification package (s.5). E2Q1 runs only after its permission. After a
   RELEASE certificate and a FAVOURABLE actual-result review, `release-adopt` for epoch 2. Production then admits under the
   five-instance ceiling and the epoch bounds.

Never, at any step:
- no worker or reaper stop or restart;
- no manual qualification permission;
- no edit of reviewed bytes after their literal;
- no pilot refit;
- no deletion or relabelling of old plans, claims, records or proofs;
- no AWS spend before the release and the fresh budget check of s.6 item 7.

## 7. REVISION 6: repair for Codex's review of RSC `b510ba0` (A1-A4 and the rulings asking for a change)

Review: `reviews/2026-10-17_e2_p80r_codex_review.md` (CHANGE 4). Everything else Codex accepted is unchanged: the schema-2
declaration and claims snapshot bytes (`87edfb9e…`, `043db609…`), the owned set and cover, the activation hand-over, the
fleet ceiling, the allowance counters, the sentinel token rule and the operational manifest.

**One shared module, `row19_ec2_e2rules.py` (new).** Pure, no I/O. Ingestion, the Mac `ack`, the crash counter, the
launcher and the future qualifier read their rules from it, so they cannot disagree. It must be promoted to `chpc/` and the
Lengau controller tree, pinned by controls v17 with the other helpers, and bound in the epoch-2 `RELEASE_CODE`.

| Item | Defect (Codex) | Change | Tests |
|---|---|---|---|
| A1 | the censor marker accepted a present LEFT status with any exit, so exit 4 + `memory:` + maxrss 1e12 was published around | absent and present status are separate: a present status under RESUME 75 or the marker must pass `left_status_problem` (attempt, slot, rep, task identity, exactly this index left, nothing new/resumed, exit 75, reason `stop requested (STOP file)` or the worker's `deadline: N s left, M s needed for the next resample`, finite times, 0 < maxrss <= stop). The marker is bound to the producer: `env/censored.txt` must be listed in `BUNDLE_SHA256SUMS` and name exactly the censored outcomes | ingest: Codex's probe (censored + exit 4 + memory + 1e12) HOLDS; wrong identity, `left []`, maxrss above stop, non-orderly RESUME reason, 75-vs-exit-4 HOLD; unnamed, extra and unlisted censor list HOLD; orderly deadline/STOP statuses pass. rules: 20 status variants |
| A2 | ingestion admitted 129..159, the counter counted only {132,134,135,137,139}: two exit-133 crashes left the coordinate allocatable | `FATAL_SIGNAL_EXITS = 129..159` in the shared module is the ONE set: ingestion admits no-status slots of it, `ec2_crash_excluded` counts every member (`PA.FATAL_EXITS` is the same object), `ack` refuses an unproduced outcome of no class. No external-interruption exemption (no evidence of cause exists); exit 137 described as SIGKILL only | ingest: 133, 136 and 138 each through two real sandbox ingestions, two Mac ACKs and allocation - the coordinate is excluded and not allocated a third time. authority: 133/136/138/129/159 exclude; ack refuses exit 1 |
| A3 | E2Q1 runs 61 workers on one replicate; ordinary production reached 69 (rep 24) and 70 (reps 69, 70) | production limited to the qualified shape: `QUALIFIED_REP_SLOTS = 61` (E2Q1's 52 work + 9 duplicates); the schema-2 allocator takes at most 57 work coordinates of one replicate per batch (ascending order kept, so replicates complete across consecutive batches), and the launcher refuses a built plan with more than 61 workers of any role on a replicate. Re-cost: the replay still gives 46 batches (45 x 72 + 34), 3,496 paid slots, so every funding number is unchanged. `QUALIFICATION_E2.md` binds E2Q1's concentration >= 61 into the (unbuilt) release branch | authority: batch 1 = rep 24 x 57 + rep 25 x 15; batch 2 starts with rep 24's other 12; 46 batches cover 3,274 once; max 57 work per replicate; Codex's 69/70 reproduced for the old order; 230 replayed plans with sentinels <= 61 (max 58); launcher refusal above 61 |
| A4 | `funding_problem` rederived from the basis inside the declaration, so a coherent regeneration on a doubled Q2 charge passed (epoch cap 3,857.04) | the basis is authenticated: `q2_basis` reads only the ledger attempt pinned in code (`E2_Q2_BASIS`: `qual-Q2/1`, `ec2-qual-Q2-a1`, sequence 7, plan `5d45f4e1…`, charge-field digest `46fd6c92…`), with the 24/23 counts as code constants; `funding_problem(fund, part, leds)` rederives from the admission's own ledgers and never reads the declaration's basis. The declaration now names that attempt and the 61/57 packing; its numbers are unchanged (1,778.52 / 2,078.52 / 46 / 3,496) | authority: Codex's doubled-basis probe refuses; five Q2-ledger edits (compute seconds, cap, plan, sequence, state) refuse; no ledger refuses; launcher gate refuses without the Q2 ledger |

**Rulings applied.**
- Ruling 1: the canonical `snapshot` command takes the plan lock itself (non-blocking; held lock = exit 3, nothing written)
  and records `plan_lock: held`; a pulled copy records `not taken (copy)` and is candidate input only (rules tests).
- Ruling 5: conditional acceptance satisfied by A3.
- Ruling 6: the sentinel replicate concentration is reported by the authority test (pool of 832 Lengau-completed coordinates
  on 100 replicates; in 230 replayed plans 15 of 920 sentinels shared a replicate with the batch's work).
- Ruling 7: R4' "at most 3 non-completions of all roles" is code (`qualification_unproduced_problem`, rules tests); the
  0.989^76 / (23/24)^76 figures are labelled independence illustrations (s.3).
- Ruling 8: A2.
- Rulings 9 and 11: A4; the 23/24 basis remains a planning proxy, not a 76-worker cost model.
- Ruling 12: `QUALIFICATION_E2.md` R5' now requires a consistent, labelled, bound synthetic modification (outcome, status
  and files together; never files removed under outcome 0/status done) and a deliberate production-class sandbox run.
- Follow-up P3, replay provenance: a schema-2 production entry journals `failure_evidence` (the `BUNDLE_SHA256SUMS` bytes,
  the outcomes, `env/censored.txt`, every unproduced slot's status bytes or absence, the unproduced map). Completing an
  `ingesting` entry and replaying an `ingested` one recompute it and write `ec2/HOLD` on any difference; the replay checks
  the fence at each unproduced coordinate, not its absence. Codex's probe (133 rewritten to the marker, checksums
  regenerated) now HOLDS; a later legitimate record at the coordinate does not.
- Follow-up P3, lifetime: an epoch-2 admission must run at the funded `lifetime_s` (79,200 s). Binding the exact qualified
  operational manifest stays with the release branch.

**Still held (unchanged prerequisites; not built here).** Ruling 13 / R6': interleaved five-admission/five-reconciliation
tests with stubbed AWS. Controls v17 (pinning e2 and the REVISION-6 helpers, `row19_ec2_e2rules.py` included, plus the
print-line diff). A fresh post-v16 snapshot, declaration and funding review. The e2 contracts, the schema-3 certificate, the
qualifier and the release branch (with E2Q1 concentration >= 61, the funding bytes and the qualified manifest bound). The
actual Q1 attempt 4 disposition and fence. Capacity evidence. Production stays shut.

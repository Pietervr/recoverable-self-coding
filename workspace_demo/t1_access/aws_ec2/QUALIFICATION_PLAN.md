# EC2 production qualification plan (predeclared before any production result; Codex f3dd3d7 contract 6, repaired for 0483db4 V10-6/V10-7 and 3dc0daf R1-4/R1-6)

Status: panel declared 10 October 2026 (R052); release rule, coverage, memory gate, ceilings and construction completed
11 October 2026, before row 23 has finished and before any qualification or production instance exists. Nothing runs
until `ec2_release_state.json` permits it (row 23's declared success with its pinned report, a reviewed qualification
permission and the owner's acceptance of the ceilings below - given 11 Oct). Nothing here enters the screen denominator
before release. 11 Oct (Codex 3dc0daf): successful coverage counts FINITE paths only, S is consumed as producer evidence
(no new ledger kind), memory must be sampled at the full packing, the replay's scope is stated, and production opens only
through `prod_authority.py release-adopt` from a validated certificate and a FAVOURABLE actual-result review.

## Panel (fixed, never chosen by outcome)

| Part | Where | What | Size | Built by |
|---|---|---|---|---|
| Q1 | ONE c7a.24xlarge spot, eu-north-1, B_full, cap 1.20, 76 workers = the intended packing | 48 EC2-block coordinates (index 199 and 198 of reps 3..26, OWNED by Q1); 24 Lengau-completed duplicates (index 1 and 2 of reps 3..14); 4 sentinels (Lengau-completed, chosen by the attempt token, never among the duplicates) | 76 refits | `prod_launch.py --contract Q1` |
| Q2 | a SECOND instance: c7a.12xlarge spot, cap 0.70, 24 workers (fresh host, fresh processes) | the 24 coordinates index 199 of reps 3..26 recomputed from scratch (duplicates; Q1 owns them); admitted only after Q1 is reconciled | 24 refits | `prod_launch.py --contract Q2` |
| S  | Lengau, an ISOLATED root and campaign (never the screen root), the UNCHANGED shard worker under `chpc/row19_qual_S_manifest.json` (the exact isolated derivation of 43b75f94) | shadow references for Q1's 48 block coordinates: job 1 "S1" = index 199, job 2 "S2" = index 198, reps 3..26 (`qual_S_plan.json`) | 48 refits | `chpc/row19_ec2_shadow.py --job 1|2` under controls v11 |

Run names and output are isolated: `runs/qual-Q1`, `runs/qual-Q2` and their own S3 prefixes; a qualification attempt is
class `qualification` in the authority inventory and the Lengau ingestion refuses its output until the release names it.

## Release rule (all must hold; no tolerance, no B or dataset change) - `chpc/row19_ec2_qualify.py`

Each bundle first passes the ingestion's own checks (frozen inventory, plan contract, typed outcomes, effective B_full
attestation, complete worker statuses, records valid against the frozen task). Then, float-bit on the verifier payload
(stats, failed, failed_reason, chosen, identity, seed, B):

1. R1: Q1's 24 Lengau duplicates equal the Lengau screen records.
2. R2: Q1's 48 block coordinates equal S's isolated shadow references. S is producer evidence, not record bodies alone:
   the isolated manifest is the exact derivation; its root holds exactly the fixed plans of jobs 1 and 2; its campaign
   ledger holds kind-shard entries for jobs 1 and 2 only, each producing entry settled with a bound PBS id and a finite
   charge (every attempt kept); every slot has a complete terminal worker status of that PBS id and a timing naming it.
3. R3: Q2's 24 repeats equal Q1's and S's.
4. R4: Q1's sentinels equal Lengau; memory at the 76-worker packing measured from the instance's `env/memory.txt` joined
   to `env/occupancy.txt` (both written in the same 60 s supervision iteration, frozen in the bundle): the samples are
   chronological; at least 10 are taken while all 76 planned workers were running; peak host use (MemTotal - MemAvailable)
   over every sample is at most 184 GiB of the nominal 192 GiB; every worker's maxrss under the 4.5 GiB stop (the
   worker-status contract). 76 x 2.32 GiB = 176.3 GiB is an estimate, not the gate.
5. R5: ingestion recovery on Q1's ACTUAL bundle, relocated and re-bound in a sandbox root: a forced stop after the first
   published pair, a replay, a second replay; ends `ingested` with every published file the register's bytes. Scope (stated
   in the certificate): this demonstrates INGESTION PUBLICATION recovery only. It does not demonstrate producer process or
   host restart, nor interrupted-transfer recovery; the sandbox plan hash differs from the canonical plan, so it says
   nothing about the Mac acknowledgement of the canonical attempt. Producer-side recovery is not claimed by this plan.

**Successful-path coverage (declared now):** R1, R2 and R3 each need at least 75 % of their coordinates fitted
successfully on BOTH sides: 18/24, 36/48, 18/24. Successful means not failed AND every frozen predictor-band statistic
finite (the procedure's own usable predicate); a checksum-valid record with a NaN/Inf statistic is not successful. Failed
fits and non-finite paths are compared like any other payload (flag and reason must match) and reported apart
(`failed_both`, `nonfinite_both`); all-failed or all-non-finite agreement cannot qualify successful fitting.

**Outcomes:** NO_RELEASE on any difference or invalid evidence (no production; report and stop). INCONCLUSIVE when only the
coverage is short: no release, and no replacement settings or coordinates are chosen by outcome or bought without a new owner
decision. RELEASE otherwise. The schema-2 certificate binds the code, manifests, partition, activation, plans, bundles,
inventory, S evidence (manifest, ledger, plans, statuses, records) and the replay; it names the Q1 attempt (key, id,
sequence, plan bytes). Production opens only through `prod_authority.py release-adopt`, which validates the certificate
against the CURRENT code, 43b75f94, the partition the current controls pin and the reconciled Q1 attempt, and requires a
pinned actual-result review carrying FAVOURABLE and the literal `RELEASE row19-ec2-qualification certificate=<sha256>
attempts=<keys>`; the released attempts are derived from the certificate. A later epoch needs its own reviewed release.

## Cost (declared ceilings; the authority enforces them, retries included)

Worst case per attempt = (lifetime 22 h + 0.25 h grace + 0.5 h reserve) x (cap + 0.014 USD/h ancillary: 60 GB gp3 at
<= USD 0.10/GB-month + public IPv4) + USD 0.30 fixed (eu-north-1 <-> Oregon transfer of the 0.22 GB toolchain and the
results, S3 requests, reserve):

| Part | Worst (one attempt) | Ceiling |
|---|---|---|
| Q1 | 22.75 x 1.214 + 0.30 = 27.92 | **USD 28** |
| Q2 | 22.75 x 0.714 + 0.30 = 16.54 | **USD 17** |
| total | 44.46 | **USD 45** |

This is above the USD 43 declared on 10 Oct; **the owner accepted USD 45 (28 + 17, one attempt each) on 11 Oct**
(`ec2_release_state.json` `owner_accepted_ceilings`, `owner_acceptance`). A retry of either part exceeds its ceiling and
needs a further owner decision. Both parts count against the USD 2,300 production envelope and the USD 3,000 cap
(`prod_authority.py`).

S reserves **2,304 core-hours** (2 jobs x 24 cores x 48 h request; about 1,200 expected to be charged) in the CSCI1913
programme allocation (100,000, programme lock) AND in a combined refit+S sub-envelope of 60,000 core-hours declared in
controls v11 - the screen refit campaign and S share that one envelope (two separate 60,000 ledgers would not aggregate).

## What still gates a launch

- **S** is built (`chpc/row19_ec2_shadow.py`: existing CampaignLedger kind `shard`, unchanged worker, isolated root and
  campaign, programme lock + the combined sub-envelope) but runs only after controls v11 (candidate `chpc/candidate_v10r2/`,
  which declares `qualification_S`, the S campaign and the sub-envelope) is reviewed and adopted, and the S manifest is in
  the job clone. No direct qsub and no unreserved run.
- **Row 23's declared success**, a favourable review of the exact repaired package, and the qualification permission record.

## After release

On a RELEASE certificate with a FAVOURABLE actual-result review, `release-adopt` opens production with no further owner
go (owner, 11 Oct: "if qual works, go directly to production"), inside the caps. The production envelope opens; Q1's 48 block coordinates may be ingested as production (the inventory lists Q1 as
released and the ingestion then accepts it); Q2's and S's outputs and all duplicates stay qualification evidence. Every
production instance keeps its 4 sentinels and the per-instance B_full attestation and identity gate; any sentinel
difference writes `ec2/HOLD` on the screen root, which refuses every admission on both providers until reviewed.

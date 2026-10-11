# EC2 production qualification plan (predeclared before any production result; Codex f3dd3d7 contract 6, repaired for 0483db4 V10-6/V10-7)

Status: panel declared 10 October 2026 (R052); release rule, coverage, memory gate, ceilings and construction completed
11 October 2026, before row 23 has finished and before any qualification or production instance exists. Nothing runs
until `ec2_release_state.json` permits it (row 23's declared success with its pinned report, a reviewed qualification
permission and the owner's acceptance of the ceilings below). Nothing here enters the screen denominator before release.

## Panel (fixed, never chosen by outcome)

| Part | Where | What | Size | Built by |
|---|---|---|---|---|
| Q1 | ONE c7a.24xlarge spot, eu-north-1, B_full, cap 1.20, 76 workers = the intended packing | 48 EC2-block coordinates (index 199 and 198 of reps 3..26, OWNED by Q1); 24 Lengau-completed duplicates (index 1 and 2 of reps 3..14); 4 sentinels (Lengau-completed, chosen by the attempt token, never among the duplicates) | 76 refits | `prod_launch.py --contract Q1` |
| Q2 | a SECOND instance: c7a.12xlarge spot, cap 0.70, 24 workers (fresh host, fresh processes) | the 24 coordinates index 199 of reps 3..26 recomputed from scratch (duplicates; Q1 owns them); admitted only after Q1 is reconciled | 24 refits | `prod_launch.py --contract Q2` |
| S  | Lengau, an ISOLATED root and campaign (never the screen root), the shard worker under the screen manifest's science | shadow references for Q1's 48 block coordinates, 2 jobs x 24 (`qual_S_plan.json`) | 48 refits | declared; **not submittable yet** (see below) |

Run names and output are isolated: `runs/qual-Q1`, `runs/qual-Q2` and their own S3 prefixes; a qualification attempt is
class `qualification` in the authority inventory and the Lengau ingestion refuses its output until the release names it.

## Release rule (all must hold; no tolerance, no B or dataset change) - `chpc/row19_ec2_qualify.py`

Each bundle first passes the ingestion's own checks (frozen inventory, plan contract, typed outcomes, effective B_full
attestation, complete worker statuses, records valid against the frozen task). Then, float-bit on the verifier payload
(stats, failed, failed_reason, chosen, identity, seed, B):

1. R1: Q1's 24 Lengau duplicates equal the Lengau screen records.
2. R2: Q1's 48 block coordinates equal S's isolated shadow references.
3. R3: Q2's 24 repeats equal Q1's and S's.
4. R4: Q1's sentinels equal Lengau; memory at the 76-worker packing measured from the instance's `env/memory.txt`
   (sampled every 60 s in the supervision loop, frozen in the bundle): at least 10 samples and peak host use
   (MemTotal - MemAvailable) at most 184 GiB of the nominal 192 GiB; every worker's maxrss under the 4.5 GiB stop (the
   worker-status contract). 76 x 2.32 GiB = 176.3 GiB is an estimate, not the gate.
5. R5: ingestion recovery on Q1's ACTUAL bundle in a sandbox root: a forced stop after the first published pair, a replay,
   a second replay; ends `ingested` with every published file the register's bytes.

**Successful-path coverage (declared now):** R1, R2 and R3 each need at least 75 % of their coordinates fitted
successfully (failed False) on BOTH sides: 18/24, 36/48, 18/24. Failed fits are compared like any other payload (flag and
reason must match) and reported apart; all-failed agreement cannot qualify successful fitting.

**Outcomes:** NO_RELEASE on any difference or invalid evidence (no production; report and stop). INCONCLUSIVE when only the
coverage is short: no release, and no replacement settings or coordinates are chosen by outcome or bought without a new owner
decision. RELEASE otherwise. The certificate binds the code, manifests, plans, bundles, inventory, shadow-record digest
and replay evidence; `ec2_release_state.json` may name it only after a separate review of the actual result.

## Cost (declared ceilings; the authority enforces them, retries included)

Worst case per attempt = (lifetime 22 h + 0.25 h grace + 0.5 h reserve) x (cap + 0.014 USD/h ancillary: 60 GB gp3 at
<= USD 0.10/GB-month + public IPv4) + USD 0.30 fixed (eu-north-1 <-> Oregon transfer of the 0.22 GB toolchain and the
results, S3 requests, reserve):

| Part | Worst (one attempt) | Ceiling |
|---|---|---|
| Q1 | 22.75 x 1.214 + 0.30 = 27.92 | **USD 28** |
| Q2 | 22.75 x 0.714 + 0.30 = 16.54 | **USD 17** |
| total | 44.46 | **USD 45** |

This is **above the USD 43 declared on 10 Oct** (Codex 0483db4 showed 43.85 from the reused constants before storage and
transfer). The owner must accept these ceilings (`ec2_release_state.json` `owner_accepted_ceilings`) before any
qualification launch; a retry of either part exceeds its ceiling and needs a further owner decision. Both parts count
against the USD 2,300 production envelope and the USD 3,000 cap (`prod_authority.py`).

S reserves **2,304 core-hours** (2 jobs x 24 cores x 48 h request; about 1,200 expected to be charged) from the CSCI1913
refit campaign cap.

## What is NOT built (consumer missing)

- **S submission.** The Lengau programme gate and admission have no isolated qualification-campaign entry kind; S needs a
  Lengau-side change under its own reviewed controls version before it can be admitted and funded. Until then the release
  rule cannot complete (R2, R3 need S).
- **Owner acceptance** of the USD 45 qualification ceiling, and the qualification permission record.

## After release

The production envelope opens; Q1's 48 block coordinates may be ingested as production (the inventory lists Q1 as
released and the ingestion then accepts it); Q2's and S's outputs and all duplicates stay qualification evidence. Every
production instance keeps its 4 sentinels and the per-instance B_full attestation and identity gate; any sentinel
difference writes `ec2/HOLD` on the screen root, which refuses every admission on both providers until reviewed.

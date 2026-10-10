# EC2 production qualification plan (DRAFT; predeclared before any production result; Codex f3dd3d7 contract 6)

Status: declared 10 October 2026 (R052), before row 23 has finished and before any production instance exists. Runs only
after row 23's declared success and a favourable review of the v10 package. Nothing here enters the screen denominator:
every coordinate below is a qualification duplicate or an isolated shadow reference.

## Panel (fixed now, never chosen by outcome)

| Part | Where | What | Size |
|---|---|---|---|
| Q1 | ONE production-shaped EC2 instance (c7a.24xlarge, eu-north-1, B_full, 76 workers = the intended packing) | 24 coordinates Lengau has already completed: index 1 and index 2 of reps 3..14 (12 reps x 2 indices), compared with the Lengau records (float.hex payload incl. `failed`, `failed_reason`, `chosen`); 48 EC2-block coordinates: index 199 and 198 of reps 3..26; 4 production sentinels | 76 refits |
| Q2 | a SECOND EC2 instance (fresh host and fresh processes; c7a.12xlarge, 24 workers) | 24 of Q1's 48 block coordinates (index 199, reps 3..26) recomputed from scratch | 24 refits |
| S  | Lengau, an ISOLATED qualification root and campaign (never the screen root; the shard worker under the screen manifest's science) | shadow references for Q1's 48 block coordinates (index 199 and 198, reps 3..26), 2 packed jobs x 24 | 48 refits |

## Release rule (all must hold; no tolerance, no minimum, no B or dataset change)

1. Q1's 24 Lengau-completed coordinates: every payload float-bit identical to Lengau's (failed fits included and compared as such).
2. Q1's 48 block coordinates: every payload identical to S's shadow reference at the same coordinate.
3. Q2's 24 coordinates: identical to Q1's and to S's (fresh host, fresh process).
4. Q1's sentinels identical; Q1 and Q2 attestations B_full with no problem; outcomes all 0; transfer verified; no
   unresolved process group; peak worker memory under the 76-worker packing reported (and below the 4.5 GiB stop).
5. Ingestion replay on Q1's bundle in an isolated sandbox root: a forced stop after the first published pair, then a
   replay, ends 'ingested' with every file hash equal to the register's.
6. Any single difference: no production; report and stop.

Failures (procedure-level, `failed=True`) are reported separately and must match in flag and reason; they are never
dropped and never count as successes.

## Cost (declared ceilings)

- Q1: c7a.24xlarge spot eu-north-1, ~0.85/h observed, cap 1.20, ~22 h -> about USD 19, worst USD 27.
- Q2: c7a.12xlarge spot, ~0.45/h, cap 0.70, ~22 h -> about USD 10, worst USD 16.
- S: 2 Lengau jobs x 24 cores x 48 h request -> 2,304 core-hours reserved (about 1,200 charged), from the refit campaign
  cap, admitted through the programme gate like any refit job (isolated root, separate ledger entries).
- Qualification total: worst USD 43 on AWS (inside the production envelope's first draw), about 1,200 Lengau core-hours.

## After release

The production envelope (USD 2,300, k from the measured unit cost) opens; Q1's 48 block coordinates may then be ingested
as production (they were computed under the production contract and qualified), and Q2's and S's duplicates stay
qualification evidence. Every production instance keeps its 4 sentinels; any sentinel difference stops production.

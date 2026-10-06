# Row 19 stage 2: the screen - declarations (corrected Design A, Codex RSC 9202e8b)

Owner, 6 October 2026: stage 2 as designed (100 fixed attempted datasets, B = 200, futility at 83 of 100), "run as much in
parallel as possible". This package is built for review; it grants itself no admission.

## 1. The 100 fresh datasets
- Reps **3..102** under the slice's seed base 20261003 (`chpc/row19_screen_manifest.json`, `datasets`). Their resolved seeds
  are unique and disjoint from: the slice manifest's historical M2S omega 1/2 identities, the three disclosed development
  datasets' seeds (reps 0..2, which row 19 excludes from the screen) and the 408 bank seeds (row 22). The exclusion list is
  in the manifest (4,411 seeds: 4,000 historical + 3 development + 408 bank); the admission gate and the release RECOMPUTE both the screen domain and the bank domain
  (from the bank manifest named and hashed here), never trusting a supplied list.
- The identity map of all 100 was computed in the PRODUCER runtime on Lengau (`make_row19_screen_manifests.py
  --emit-identities`, via t1py in the bank clone); a Mac rebuild carries other runtime labels and never matches (the same is
  true of the development identities), so every identity check runs on Lengau.
- No development record, original or refit is ever DONE, cached, counted or paired for the screen. A failed dataset is never
  replaced by a new id or seed.

## 2. The external parity panel
Reps 0, 1, 2 are mechanical parity anchors only (`anchors`): validated under their OWN contract (the development shard
manifest, named and hashed; `row19_shard.task(shard_manifest, rep)`), with the required overlap index frozen at **0** for each
(present today in both the shard root and the sequential chain). At the required index and at every other index both hold,
the canonical scientific payload must agree to the float bit (`row19_screen_verify.anchors`); all three are required; a
missing, invalid or differing anchor holds qualification. Fresh screen datasets report "no sequential run by design".

## 3. The lossless originals
`row19_screen_orig.py` runs the literal original call (`A.run_dataset(ds, cfg, seed, outer_folds=folds)` on `row19_shard.task`)
and keeps the complete run in the slice runner's cache contract (schema row19-orig-v3: every RUN_KEYS field as typed raw
bytes, payload and metadata checksums), published temp + fsync + LINK (never overwritten), read back with
`row19_slice.read_orig` before it is reported; a failed original is kept with its reason. Its own manifest
(`row19_screen_orig_manifest.json`: the same setting, datasets, identities, cfg, code and environment; root and campaign of
its own; 20 workers a job, so 100 originals are 5 full jobs).

## 4. The seal
Every producer, verifier, status view and the admission controller is RAW: records, caches, checksums and operational
metadata only. The ONLY path to an interval, decision or coverage is `row19_screen_release.release()`, which runs all of
`seal_problems()` (adoption authority: a git-tracked adoption document and a git-tracked numerical-target review record;
the exact target bytes, RESOLVED, finite ordered bounds, the bank manifest's rules; the bank binding recomputed in this
runtime and equal to the target's and the adoption's; the complete validated bank record set reproducing the target's
digest and its primary numbers; the consumer's pins; both seed domains) and `completeness_problems()` (every original and
every index 0..199 valid) BEFORE it imports or calls any aggregation helper. During aggregation `analyze.run_dataset` raises,
so nothing can be fitted; each chain is restored with `strict_restore=True` and must return complete with no new work.

## 5. Admission
`row19_screen_admit.py` per role (refit: the unchanged `row19_shard.py` worker, ledger kind "shard"; orig: the producer,
kind "orig"). Evidence-based planning; the refit planner is index-major, so job 1 is exactly reps 3..26 at index 0; the
pilot is one job alone per role; later jobs need a production qualification (`row19_screen_status.py --qualify 1`) bound
to the manifest, root, campaign, pins, wrapper, job 1's PBS id/token/plan, the task bindings of the reps actually started
(unstarted ones stay pending) and the anchor verdict; an adopted review that is git-tracked, unmodified, names that
qualification and a highest job number; and a fresh zero-alarm receipt (<= 2,700 s) bound to every job of the role.
A scheduler query that does not return 0, or does not describe every job, is a failed observation. STOP refuses.
First timing expectation 90,000 s (above the development pilot's longest packed resample, 88,740 s): a defensible first
value, not a measurement on fresh datasets.

## 6. The decision
PREREG 10.1, one look: per method (refit, cluster) the usable n is reported with failures and the paired partition
(both, refit-only, cluster-only, neither); K_max = the largest number of usable intervals containing any theta in the
frozen T, over every endpoint inside T, both ends and a point inside every segment, inclusive; STOP FOR FUTILITY iff the
one-sided 97.5 % Clopper-Pearson upper bound at (K_max, n) is below 0.90 (at n = 100: K_max <= 83; 83 -> 0.897735,
84 -> 0.905690); otherwise "not ruled out at this look", never a pass.

## 7. Funding and the cap
Each refit job reserves 24 x 30 h = 720 core-hours; 20,000 one-index slots need at least 834 jobs (600,480 core-hours of full
reservations; ~500,000 expected charged at ~25 h per fit); originals 5 x 20 x 30 h = 3,000. The funding gate sums settled +
live of every campaign ledger (slice, shard, bank, screen, originals) + 6 core-hours settled outside them + the proposal
against the CSCI1913 allocation (100,000). HEAL1922 is not used until the owner rules the distinct-work split. The cap:
both manifests declare `budget.core_hours_cap: null`, so the unchanged runner never compares a cap and the manifests'
SHA-256 (named by every binding) never moves; the ledger is created at the initial phase of `row19_screen_budget.json`
(60,000) / `row19_screen_orig_budget.json` (3,000) and raised only by `--raise-cap NEW --note`, recorded in the ledger's
cap_history and appended to the budget file. Spent hours are never reset.

## Revision 2 (Codex RSC a1ce224: repairs before any role's job 2 and before any numerical release)
The manifests are unchanged (the pilots' bindings name them). Controllers are versioned in `chpc/row19_screen_controls.json`
(version 1 = fe3c266, the reviewed pilot controllers; version 2 = these repairs); a controller refuses unless every controller
is the latest version's bytes. The lineage file also carries the programme block (lock, campaigns, which new ledgers may be
absent) and pins the slice manifest from which the historical exclusions are reconstructed.
- **Programme-wide admission** (`chpc/programme_gate.py`): one lock for CSCI1913; a strict fresh count of all five ledgers
  (finite non-negative charges, no booleans, NaN refused, a missing expected ledger HOLDS, a new ledger may be absent only if
  its root has never planned, a campaign listed twice HOLDS). The screen controller admits inside it; the bank, shard and
  slice controllers are run through `programme_gate.py run --proposal-core-h X -- <command>`, which holds the same lock and
  checks the same count first. The two raw pilots were admitted under an explicit exclusive window (one pre-check of all
  ledgers, both reservations back to back, no other admission).
- **Cap amendments** are two-phase (phase written pending, ledger raised, phase committed); an interrupted one is reconciled
  when the ledger already carries it and refused otherwise; a raise outside the protocol is refused at admission.
- **Qualification and receipt** are parsed strictly: finite non-boolean times; the embedded job-1 summary terminal F with
  scheduler and runner exits 0/75, every worker ended 0, nothing left, finite scheduler and worker memory; the anchor verdict
  EMBEDDED and hashing to the bound digest, index 0 equal on all three anchors, nothing differing, missing, invalid or
  conflicting; the bound bindings EXACTLY the root's. A review is adopted only when its tracked record contains
  `ADOPT row19-screen-pilot role=<role> qualification=<sha256> max_job=<n>` for this qualification and scope.
- **Status**: qualification needs state F exactly, runner exit 0/75 and finite memory; a worker's status must name its job,
  slot and declared identity; stray status files and missing bindings of started reps (from the plans, not the files) are
  alarms; the full verifier document is saved and copied to the gate; the anchor verdict is embedded in receipts.
- **Anchors**: canonical names only (aliases reported, never parsed); a differing duplicate sequential record is a conflict.
- **Release**: the bank's setting, effective cfg, canonical pins and environment must be the screen's; the top-level status,
  the frozen primary and the recomputed primary must all be RESOLVED; the target is read once and those bytes decide; the
  review record must carry `ADOPT row19-numerical-target target=<sha256> bank_records=<sha256> verdict=FAVOURABLE`; every
  failure (original reasons, refit n_used / n_failed / reasons) is in the result.
- **Seeds**: the exclusion list must EQUAL the reconstructed contract (4,000 historical from the pinned slice manifest + 3
  development + 408 bank = 4,411); a truncated or padded list refuses.

## Revision 3 (Codex RSC ee99ee1: R1-R7)
- **R1** The pilot qualification is checked against job 1's OWN scope (job 1's binding and the bindings of job 1's reps, still
  the root's bytes); every fresh receipt binds EXACTLY the whole set of started task bindings. Fixture: job 1 adopted, job 2
  started, job 3 admissible; an omitted or changed later binding refuses.
- **R2** Every job a receipt summarises is checked against its plan (terminal: state F, scheduler and runner exits 0/75, the
  plan's exact worker count ended, worker exits only 0/75, finite non-negative memory, integers not booleans); the pilot must
  show all its workers ended 0. The status view alarms a runner exit outside 0/75, a terminal job without finite memory,
  a worker without finite wall time, and any status file outside the whole planned job/slot universe.
- **R3** The verifier runs from the controller-only clone `rsc_screen_ctl` (lineage `deployment`) and stamps its controller
  generation; a consumer refuses evidence of another generation or with a lineage problem. The full verifier document is
  saved and copied to the gate, and only a successful copy counts as production. The qualification and receipt name it and
  its SHA-256; admission re-reads it, checks schema, role, time, manifest and generation, and that its anchor verdict and
  binding digests equal the summary's. Producer binding digests must equal the local snapshot's.
- **R4** Budget phases are parsed strictly (finite positive caps, booleans and non-finite constants refused, campaign named);
  a raise is validated before its pending phase is written; phases are written atomically and durably; an interrupted raise
  is resumed by repeating the same `--raise-cap` or retired by `--retire-pending --note` (kept in the history); the
  ledger's cap_history must record the latest phase.
- **R5** The release reports each dataset's RAW restored chain (per predictor n_used / n_failed, and the failure reasons) also
  when its original failed; that dataset stays out of both denominators, labelled.
- **R6** The lineage file is a pinned release consumer file and the release runs the lineage check; the programme wrapper
  refuses unless it and the controllers are the latest version's bytes, derives its proposal from `--jobs/--cores/--walltime-h`,
  logs every admission and refusal to programme_admissions.jsonl, and wraps settlements (`settle`) in the same lock. Routing
  the unchanged bank/shard/slice controllers and settlements through it remains a COOPERATIVE operating procedure.
- **R7** ASCII-only canonical names (`rec_[0-9]{3}.json` equal to their formatted index, `rep0|rep[1-9][0-9]*`); a duplicate
  logical coordinate is a conflict.

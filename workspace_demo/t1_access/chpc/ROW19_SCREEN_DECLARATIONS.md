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

## Revision 4 (Codex RSC 8bd1451: C1-C4)
- **C1** A fresh receipt never covers a job whose CURRENT ledger state moved: a job the receipt saw queued/running that has
  since recorded a runner end (any exit, also a clean one), or a terminal job whose recorded runner exit differs, refuses until
  the evidence is recollected. Exit codes, counts and `left`/`new`/`resumed` are integers, never booleans, never negative.
- **C2** The retained verifier document's emitted digests must EQUAL the reviewed pins - its own SHA-256 the latest version's
  verifier pin, its controls SHA-256 the ADOPTED controls digest - with an explicit empty `controls_problem`, empty
  environment/code verdicts and clean binding flags; its units must agree with the summaries (per terminal job, the valid units
  whose timing names it = the summary's `new`; the pilot: every planned unit a valid record with a timing naming its job and
  slot). The status tool applies the same generation check at ingress.
- **C3** The controls file is trusted only through `chpc/row19_screen_controls_adoption.json` (git-tracked, unmodified),
  which names the controls file's exact SHA-256 and a git-tracked, unmodified review record carrying
  `ADOPT row19-screen-controls sha256=<sha> version=<latest>`. Until it exists, the wrapper, the screen controller and the
  status tool refuse to read the programme block, the deployment or the history. A controls-only edit (lock path, campaign
  list) refuses with the code untouched.
- **C4** A resumed raise reports success only after the ledger's cap AND its latest cap_history entry certify the phase; a
  ledger above the pending phase, or a cap without its history entry, refuses and leaves the phase pending.

## Revision 5 (Codex RSC f40991e: the C1, C2 and C4 remainders)
- **C1** A receipt that calls a job queued or running is refused also when the ledger now shows that job SETTLED (a job killed
  and settled from accounting has no runner end). Fixture: an R receipt, then a settlement without runner end, refused.
- **C2** A unit counts toward a summary only with a valid record AND `timing.ok` true, with a coordinate in THAT job's plan and
  that plan's slot; any unit naming the job that fails this refuses; each summary's PBS id must be the ledger's bound id.
  Fixtures: timing.ok false with correct names; a job-2 summary naming P1; two units in a wrong slot; an unplanned coordinate
  with unchanged totals - all refused.
- **C4** A pending raise is applied only when the ledger still certifies the preceding committed phase (its cap, and its latest
  history entry or none for the first phase), or reconciled only when the ledger shows exactly that raise (old = predecessor,
  new = pending); retirement only when the ledger still certifies the predecessor; anything else refuses and changes nothing.
  Fixtures: an unexpected lower predecessor (60,000 -> 70,000 out of protocol) refuses both resume and retirement; a matching
  pending cap without its history entry refuses; the ordinary pre-ledger recovery still succeeds.
- The wrapper's docstring example is corrected to `--jobs/--cores/--walltime-h`; its declared limits stay cooperative.

## Revision 6 (Codex RSC 74dae6d: the C2 and C4 remainders)
- **C2** A unit counts only when its coordinate IS in the job's plan and its timing slot is an integer equal to the plan's
  slot (an unplanned coordinate with a null slot no longer passes as None == None); a terminal job's summary must partition its
  plan exactly (new + resumed + left = the planned units) and at least new + resumed of its planned units must carry a valid
  record with valid timing. Fixtures: unplanned 99/0 with slot null; left 3 of a 24-unit plan; resumed 2 without records.
- **C4** The automatic reconciliation in cap_problem uses the CLI's exact applied certificate (cap = pending, latest history
  new = pending AND old = the preceding committed phase). Fixtures: 60 -> 70 -> 90 against committed 60 / pending 90 stays
  pending and refuses; an exact 60 -> 90 reconciles.

## Revision 7 (Codex RSC 8865474: the C2 and C4 remainders)
- **C2** The admission reconciles a terminal job's HISTORICAL outcome, not today's aggregate. The status tool now writes, per
  job, `partition`: the sorted new / resumed / left coordinate lists read from that job's own worker statuses. The admission
  requires them (absent lists refuse), requires that they partition the job's plan exactly and match the summary's counts, and
  checks each list against supported producers: a new unit is a valid record whose timing names THIS job in its plan slot; a
  resumed unit is a valid record whose timing names an EARLIER bound job whose plan holds that coordinate in that slot (an
  unbound producer such as P999 or a null slot never counts, and a later job's work never certifies an earlier resumption);
  a left unit may hold a valid record only from a LATER bound job that planned it (legitimate later completion). Reused
  timing is never required to name the resuming job. Fixtures (test_a_job_history_is_its_own_partition_with_supported_producers):
  truthful P2 20/0/4 with a running P3 completing two of its left units admits; the false P2 20/2/2 resuming P3's units
  refuses; P2 20/2/2 resuming two P999/null-slot records refuses; P3 terminal 2 new + 2 resumed from P2 admits; P3 claiming
  as left a unit P2 had produced refuses; a summary with no lists refuses.
- **C4** The automatic reconciliation accepts ONLY the applied certificate (cap = pending, latest history old = the preceding
  committed phase, new = pending); predecessor_problem's predecessor-only branch is skipped there (applied_only), so an
  un-applied predecessor can never clear a pending phase, however small the raise. The CLI also refuses any raise of less than
  one core-hour. Fixture test_a_sub_tolerance_pending_raise_without_applied_history_never_auto_clears: committed/current
  60,000, no history, pending 60,000.0000000005 -> cap_problem refuses with the phase pending and the ledger byte-identical;
  the pending phase retires through the CLI; a 60,000.5 raise refuses. The ordinary wrong-old negative and the exact-applied
  positive remain.

## Actual pilots adopted (Codex RSC `6d8c30a`, 8 October 2026)
Record `reviews/2026-10-08_actual_evidence_codex_record.md`; the adopted version-7 controls (`43a099ca…`, judgment
`86f1105`) are unchanged.
- **Originals**, pilot `7523819.sched01`: all 20 slots reconcile to reps 3-22, call walls 18.99-22.90 h, worker RSS at most
  1.26 GiB. `ADOPT row19-screen-pilot role=orig qualification=42ddb685… max_job=5` (cap 3,000: four further 600 core-hour
  requests plus the pilot). The originals request 20 cores and stay on `serial`.
- **Refit**, pilot `7523818.sched01`: all 24 slots reconcile to reps 3-26 at index 0, walls 21.68-24.39 h, RSS at most
  2.32 GiB. `ADOPT row19-screen-pilot role=refit qualification=4bbe4aa6… max_job=100` (cap 60,000). Max 100 is a ceiling
  under rolling settlement: 100 full 720 core-hour reservations are 72,000, so the cap binds first; 100 jobs make at most
  2,400 of the 20,000 refits, and the complete screen needs at least 834 jobs (a cap amendment under §7, not this adoption).
- **Settlement provenance.** The ledger copies Codex reviewed still show the pilots live at 600 / 720 (and the bank's 864).
  The settlements at 458.53 / 585.83 (594.59 for the bank) are from the scheduler walls, entered through the programme
  wrapper; each later receipt carries the settled ledgers, which is the proof the copies lacked.
- **Each later admission** keeps the job-1 qualification and the exact ADOPT line, and needs a fresh whole-role receipt
  (zero alarms, successful scheduler observation, exact partitions and ledger transitions) at most 2,700 s old.
- **In flight, 8 October 17:10 UTC.** Originals jobs 2-3 and refit jobs 2-3 running, originals 4-5 queued.
- No interval, T, coverage or futility decision is authorised by this adoption; §4's seal is untouched.

## Revision 8 - REPAIRED CANDIDATE, not adopted (Codex R052 record `2026-10-09_refit_wall_kill_codex_record.md`, verdicts 1 and 2)
The first candidate's bytes (RSC `c1956ef`) were rejected by Codex `5cb9a02` (R1 current record/timing provenance at disposed
coordinates, R2 the settlement certificate, R3 exact integer cores). Re-review `ce06828` of the repair `28861c4` closed R2 and R3
and left R1's current-timing measurement contract open; the bytes in `chpc/candidate_v8/` now close it and supersede both.
Design, line references, SHA-256 pins and test summary: `chpc/ROW19_SCREEN_V8_CANDIDATE.md`. The changed controllers and the
version-8 controls file are in `chpc/candidate_v8/` (the adopted version 7 stays in place and in force); the new resource policy
is `chpc/row19_screen_resources.json`. (1) A terminal refit or originals job is DISPOSITIONED (closed-no-record) - reported with
its actual exit, not alarmed - only when the status view AND, independently, the admission establish: successful terminal
scheduler observation, current ledger SETTLED with settlement evidence and no runner-end field, no status scoped to its PBS id,
no record or timing attributable to it, and its retained PBS output naming it without ADMISSION FAILED; its plan's coordinates
stay uncompleted (origin "plan") until a later bound job completes them; it never qualifies a pilot; its charge stays.
(2) Refit jobs from 10 request 48 h (serial, 24 cores, 120 GB, reserve 1,800 s, one index per worker; 1,152 core-hours each)
from the pinned policy, bound in plan, ledger, PBS request and receipt; jobs 1-9 and every originals job keep the manifest's
30 h. If adopted, §7's "24 x 30 h = 720 core-hours" holds for refit jobs 1-9 only. Recorded actual refit balance (as reviewed in
`5cb9a02`): spent 1,892.81 + live 4,320, room 53,787.19 = 46 full 1,152-hour requests under the 60,000 cap - dated arithmetic,
not fresh accounting or a batch permission (the harness's "49" is a synthetic fixture). Adoption needs a fresh v8 job-1
qualification per role and a new pilot ADOPT line (see the candidate note, open point 1).

## Current controllers (10 October 2026)

The section above is the dated version-8 candidate record. Version 8 was adopted on 10 October (Codex `fb8957f`; RSC
`047c280`) with its refit pilot (Codex `454bbc0`, qualification `6cf1a513`). **Version 9 is now in force** (Codex
`91a567c`; RSC `eabcdcc`; controls `45f840bc`, adoption `42b99b4d`): the only change is the status tools' snapshot pull,
now one ssh tar stream with explicit remote phases (`chpc/candidate_v9/README.md`), after `scp -r` overran its 900 s
timeout at ~940 files and blocked refit receipts. The bank status tool carries the same transport change in its own lane
(`a8585eff`, raw-bank scope and job cap 17 unchanged). The generation-9 refit qualification is `3820ac0e` (18:32:44 UTC,
zero alarms) and the refit pilot is adopted on it to job 100 (Codex `d64600f`; gate `review_refit.json` `0324ff53`; the v8
review retired to `gate_retired/`). Each refit admission still needs a fresh whole-role receipt (at most 2,700 s old, zero
alarms) and passes every planner, binding, disposition, funding, capacity, resource and STOP gate; refit jobs from 10
request 48 h. Archives: Lengau `archive_screen/v8_before_v9_20261010`, Mac `chpc/results/archive/row19_screen_v8_before_v9_20261010`.

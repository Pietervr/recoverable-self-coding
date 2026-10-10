# Row 19 screen controllers, version 8 - REPAIRED CANDIDATE (not adopted, not deployed, needs Codex review)

Date: 9 October 2026. Built by Claude (R052 Entropy SI) as a job for the R052 session. Authority for the design: Codex
record `reviews/2026-10-09_refit_wall_kill_codex_record.md` (SHA-256 `25afbca9565af7f30c7b9764956df1235f8750bbc1ef2c7d54671bb0ead7412f`),
verdict 1 (closed-no-record disposition of refit job 3, `7527352.sched01`) and verdict 2 (prospective 48-h refit envelope).
Base: the adopted version 7 (admit `573e5b18…`, status `dac142fb…`, verify `d8d3c73b…`, controls `43a099ca…`).

**Revision history.** The first candidate, RSC `c1956ef` (admit `e62f289b…`, status `3457c9e8…`, controls `76aa22f9…`), was
reviewed by Codex in `reviews/2026-10-10_screen_v8_candidate_codex_record.md` (RSC `5cb9a02`, SHA-256 `f4de9fd1…`): NOT
FAVOURABLE as built, and Codex declined to promote those bytes. **The c1956ef bytes are rejected; this repaired candidate
supersedes them.** Repairs R1-R3 are listed below; the disposition and resource designs themselves stayed favourable.
The repaired candidate RSC `28861c4` (admit `054d6d68…`, status `ae91c8d0…`, controls `1436d885…`) was re-reviewed in
`reviews/2026-10-10_screen_v8_repair_codex_record.md` (RSC `ce06828`, SHA-256 `ae94f0ee…`): **NOT FAVOURABLE** - **R2 and R3
CLOSED**, R1's producer continuity repaired but the current timing's measurement contract missing. **That remaining R1 timing
check is closed by the commit that carries this text** (admit `4fa993ee…`; status bytes unchanged).

**Status: NOT ADOPTED, NOT DEPLOYED. Needs Codex review.** No ADOPT line or adoption record is written; the adopted
`chpc/row19_screen_controls_adoption.json`, the manifests, `row19_shard.py`, the bank files and `reviews/` are unchanged.
Nothing here ran on Lengau; refit jobs 4-9 (`7529179` … `7529824`) are untouched.

## Layout - why a candidate directory

The adopted v7 controllers stay in place. The three changed files live in `chpc/candidate_v8/`, byte-identical to what
version 8 pins at their canonical paths; the new policy file is at its final path (`chpc/row19_screen_resources.json`, inert
under v7, which never reads it). Committing v8 bytes over `chpc/row19_screen_{admit,status,controls}` would make this clone's
controls file differ from the adopted digest, so `controls_authority_problem()` would refuse and the Mac status view of the
running jobs would stop until a v8 adoption. Promotion on a favourable review is a copy of the three files to `chpc/`,
checked against the SHA-256 below, then the adoption record.

| File (as committed) | Canonical path in v8 | SHA-256 |
| --- | --- | --- |
| `chpc/candidate_v8/row19_screen_admit.py` | `chpc/row19_screen_admit.py` | `4fa993ee97d13d491b7afa5374c8ec49a330e64173872737942b0467bb0cb965` |
| `chpc/candidate_v8/row19_screen_status.py` | `chpc/row19_screen_status.py` | `ae91c8d035e53403b7d664fd1b8ed8e90995c0e88904b8f4915c6dcb13963948` |
| `chpc/candidate_v8/row19_screen_controls.json` | `chpc/row19_screen_controls.json` | `9f73622238034ed49cde86d0ee70c31a8bc8e2f1de9535f810eb4081dc49e9d7` |
| `chpc/row19_screen_resources.json` (new) | same | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |
| `chpc/row19_screen_verify.py` (unchanged) | same | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `chpc/row19_screen_release.py` (unchanged) | same | `7a67fd1fc3ca60d77c62ddcaea5d4e11a9ec87ac6b2b02f0bc75ab34a366507f` |
| `chpc/programme_gate.py` (unchanged) | same | `10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0` |

Controls version 8 appends one entry (versions 1-7, programme, history manifest and deployment blocks byte-for-byte the same
in meaning) pinning all six files above, including the resource policy.

## (1) Closed-no-record disposition (verdict 1)

**Status view** (`candidate_v8/row19_screen_status.py`):
- `fresh_snapshot` (:122) now calls `fetch_job_outputs` (:138): for every entry of the role that is settled with no runner-end
  field, it pulls `<toolchain>/jobs/row19_screen_<role>_<n>.out` (the `#PBS -o` path the admission writes,
  `row19_screen_admit.py` :1309 onward) into the snapshot's `jobs/`, recording rc, ok and SHA-256 in `jobs/_fetch.json`. A failed
  or missing retrieval is recorded, not fatal: that job simply cannot be dispositioned.
- `closed_no_record` (:209) returns a disposition only when ALL hold: scheduler state F with an observed integer exit; ledger
  SETTLED with finite charge, a technical note and a settlement time; no `runner_exit`, `runner_ended` or `runner_wall_s`; the
  plan's token and job are the entry's; no status file scoped to the PBS id (by name, any slot incl. unplanned, or by parsed
  `job`) and no unreadable status with no job named; no verifier unit and no timing file anywhere naming the job, and no
  unreadable or temporary timing file; every file at a planned coordinate (record or timing, temporary files included) a valid
  record whose timing names a LATER bound job that planned it in that slot; and the retrieved output names the PBS id and has
  no `ADMISSION FAILED`. It is examined for every terminal job without a runner exit (:317), so an unsettled kill reports why.
- Only the three alarms are suppressed, only then (:331 bad scheduler exit, :333 no runner end, :348 missing worker status).
  Memory, binding, foreign, anchor and record alarms are unchanged. The summary keeps the actual exit, zero
  ended/new/resumed/left and null worker measurements, carries `disposition` (kind, scheduler exit, charge, output file and
  SHA-256) and `partition.uncompleted` with `uncompleted_origin: "plan"` (:402); no worker status is invented.
- The receipt binds the output (`bound.job_outputs`, :475) and a copy is retained beside it (:484). `--qualify` refuses a
  dispositioned job (:513). An unreadable status file is now an alarm instead of stopping the view.

**Admission** (`candidate_v8/row19_screen_admit.py`):
- `disposition_problem` (:814) recomputes every condition from the CURRENT ledger, the root and the PBS output on disk; the
  summary's `disposition` is a claim to check, never a boolean that waives anything. Helpers: `status_scoped` (:697),
  `timing_scan` (:715), `coordinate_files` (:733), `later_completion` (:787), `current_artifacts_problem` (:750),
  `certificate_problem` (:802), `job_output_path` (:690). The output must be the
  bytes the receipt bound (a change after the receipt refuses: recollect).
- `receipt_problem` (:1169) routes a summary carrying `disposition` to it (:1194); every other summary keeps `job_summary_problem`.
  A dispositioned summary without its claim is an ordinary terminal job and refuses (exit 271).
- `units_problem` (:957, :972): nothing may name a dispositioned job; its partition is checked by `disposition_problem`.
  The revision-7 producer rule is unchanged, so a later retry completes the disposed coordinates only through its own bound
  plan, job and slot, and a record or timing naming the killed job holds.
- `transition_problem` (:1058, :1073) re-reads the ledger for a disposed job: SETTLED, the same settlement certificate and PBS
  id, no runner-end field.
- Pilot guard: `job_summary_problem(pilot=True)` refuses a dispositioned job (:913).
- Planner unchanged (`evidence` :393, `plan_jobs` :452). Confirmed on the retained local snapshot (read only): job 3 settled
  leaves flight, done 48, in flight 144 (jobs 4-9), and job 10 plans exactly reps 51-74 at index 0 - the retry comes first.

## Repairs for Codex 5cb9a02 (R1-R3)

- **R1 - current artifacts, not only the retained verdict.** `later_completion` (admit :787) now ends with
  `current_artifacts_problem` (:750): at a disposed coordinate the CURRENT canonical timing must carry the coordinate, the declared
  identity and exactly the verified producer job and integer slot, and must meet the unchanged verifier's `timing_ok` measurement
  contract (`row19_screen_verify.py` :93-105): `wall_s`, `fit_seconds`, `maxrss` and `t` each present, finite, non-negative and
  non-boolean (`TIMING_MEASURES` :747, check :772-774; closes the ce06828 remainder), and the CURRENT record must carry the verified checksum
  (refit `sha`, originals `payload_sha`) and, for refit, the coordinate's index and identity. An absent, unreadable or changed
  artifact refuses until the evidence is recollected; a genuine later bound planned retry still passes. Both callers use it:
  `disposition_problem` (:882) and the status view's `closed_no_record` (status :244).
- **R2 - the settlement certificate is bound.** The status disposition now carries `settle_note`, `settled_at`, `token`, `job_id`
  and `plan_sha256` beside the charge (status :267). `certificate_problem` (admit :802) requires a valid certificate (charge, note,
  non-negative time) and EXACT equality with the current ledger entry; it runs in `disposition_problem` (:840, after the charge
  check) and in `transition_problem` (:1073). The current entry's `settled_at` must be finite and non-negative (:837); the bound
  plan digest is compared (:853). Nothing rewrites a settlement: the charged loss stays charged.
- **R3 - exact integer cores.** `envelope_problem` (:642-662) requires `cores` to be a non-boolean integer equal to the envelope's,
  and `reserved_core_h` to equal both the envelope's full request and the entry's own cores x walltime (:659); 24.5, 24.0,
  True and "24" are refused on the receipt path and in the admission's self-check.

## (2) Prospective refit resource policy (verdict 2)

- `chpc/row19_screen_resources.json`: schema `row19-screen-resources-1`, role refit, bound to the screen manifest
  `43b75f94…`; one envelope from `first_job` 10: serial, 24 cores, 48 h, 120 GB, haswell_reg, reserve 1,800 s, per_slot 1.
- `resolve_envelope` (:579): originals always get the manifest's request; refit checks that the policy is the lineage's pinned
  bytes (every refit job, also below first_job), validates its shape (`resources_shape_problem` :554: walltime at most 48 h,
  one index per worker, integer reserve), returns the manifest's 30 h below first_job, and from it on requires the policy to
  name this manifest and every non-walltime field to equal the manifest's (walltime-only change; the manifest is never edited).
- `main` (:1361): each NEW job's envelope resolved (:1439); funding = the sum of resolved full requests through the programme
  gate and a new campaign-cap pre-check (`campaign_cap_problem` :1262; cap 60,000) before any reservation; the script is checked
  before reserving and again with the real token (`pbs_request_problem` :628: `-q`, `walltime=`, select line,
  `DEADLINE=$((START + W - R))`, `--walltime-s W`, each exactly once); the ledger reservation is `cores x W` (1,152 core-hours at
  48 h); the plan carries `walltime_s`, `queue` and `envelope` (:1469); `envelope_problem` (:642) checks plan + ledger entry (exact integer cores, R3).
- Receipts: `receipt_envelope_problem` (:669) checks every job at or above first_job against its plan, CURRENT ledger entry and
  the status view's `plan_walltime_s` / `requested_walltime_s` (the scheduler's `Resource_List.walltime`, now parsed by the
  status view, which alarms a plan/scheduler difference). `policy_first_job` (:613) fails closed (a bad policy checks every job).
- Highest job number 100 stays the adopted pilot review's `max_job` (unchanged); programme allocation 100,000 unchanged.
- **Budget arithmetic, corrected.** The harness's "room for 49 more 48-h requests" is the SYNTHETIC FIXTURE ledger (spent plus
  live 3,312.55, room 56,687.45), not the campaign. The recorded actual refit balance (R052, as reviewed in `5cb9a02`) is spent
  1,892.81 plus live 4,320, leaving 53,787.19 core-hours = **46** full 1,152-hour requests. Neither figure is fresh scheduler
  accounting or a batch permission; the locked campaign and programme funding gates decide each request at admission time.

## Verification (local fixtures only)

Harness `tests_v8.py` and full output `tests_v8_output.txt` are in the R052 session scratchpad
(`/private/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/fdb5f471-1679-481f-8198-f3f211cc7447/scratchpad/`), with the
patch scripts that turn the v7 bytes into these (`admit_v8.py`, `status_v8.py`, `controls_v8.py`, `build_v8.sh`). They ran in a
scratch git copy of `t1_access` holding the candidate in place.
- New: **15/15 passed** (the 12 original checks plus `test_r1_…`, `test_r2_…` and `test_r1b_…`; the R3 negatives are inside
  `test_f3_…`). Among them: (a) unsettled kill holds (all three alarms, 24 missing statuses; a claimed disposition refused);
  (b) settled no-record job 3 dispositioned with exit 271 kept and admits job 4; (c) 28 contrary-evidence cases each hold in
  the status view and in admission against a receipt that still claims the disposition (parsed / unreadable / unplanned-slot /
  renamed status, ADMISSION FAILED, missing / unreadable / unnamed / changed output, record or timing naming the job, records
  from an earlier, unbound or absent producer, temporary record and timing files, ledger charge / note / state / token / plan
  changes, each runner-end field) plus 16 summary forgeries (state, exit, counts, memory, partition origin, kind, charge,
  unbound output, PBS id, a dropped claim); (d) the planner re-plans job 3's coordinates first and a bound
  retry completes them, a wrong slot or a timing naming the killed job holds; (e) pilot guard in admission and `--qualify`, and
  the status main binds and retains the output; fresh_snapshot retrieves only settled no-runner-end jobs and records a failed
  retrieval; (f) the real policy: job 10 -> 172,800 s / 1,152 core-h, `walltime=48:00:00`, `DEADLINE=$((START + 172800 - 1800))`,
  jobs below 10 -> 30 h / 720, originals -> manifest; tampered, absent or malformed policy refused (pin, lineage, shape);
  end-to-end admission (qsub stubbed) binds 48 h in plan, ledger (1,152), script and receipt, and refuses a 30-h scheduler request,
  a 720 reservation or a changed plan; (g) the retained real snapshot plus its latest verifier document: job 3 dispositioned with
  zero alarms (a synthetic PBS output stands in, see below); (h) the originals role uses the same rule; (R1) ten disk-only mutations after a clean
  retry receipt with the verifier and receipt fixed - timing naming unbound P999, earlier P1, P4 in slot 23, a null slot, another
  identity or index, absent timing, changed record, record of another index, absent record - each holds in admission and in the
  status view, and the restored retry admits; (R2) after a clean watch with the receipt unchanged, a replaced valid note, a
  replaced non-negative time, time 0 and a negative time each refuse in admission and in the transition check, the charge
  unchanged; a receipt without a valid certificate or with another plan digest refuses; (R3) cores 24.5 / 24.0 / True / "24"
  refuse; (R1b, ce06828) 16 disk-only measurement mutations after a clean P4 retry receipt - each of `wall_s`, `fit_seconds`,
  `maxrss`, `t` missing, negative (-1), non-numeric ("1.0") and boolean (True) - with the verifier and receipt fixed and the genuine
  record byte-identical, each holding in admission and in the status view, and the restored valid timing admitting again.
  `timing_scan` stays the attribution scan (killed-job naming, unreadable or temporary files anywhere); measurement validity is
  required where a timing is relied on, at disposed coordinates, exactly as the verifier defines it. One fixture changed with the repair: the retry in test (d) now writes canonical record and timing files that match its
  verified units (it previously wrote empty placeholders, which R1 now correctly refuses).
- Unchanged v7 modules against the candidate: screen 23/23, bank 10/10, slice 17/17, watch 5/5, control compare 11/11,
  oracle 5/5, shard 12/12, recycle 5/5 (88/88).

## Open points for the review

1. **A new generation needs fresh job-1 evidence** (Codex 5cb9a02 agrees in principle; it also requires preserving the old
   controls adoption, pilot review, qualification, named verifier and watch/PBS evidence with their digests - `--qualify` overwrites
   `qualified_<role>_job1.json` - and a literal ADOPT on the REAL new qualification, refit `max_job` 100; originals are complete and
   need no re-adoption). The retained job-1 qualifications (refit `4bbe4aa6…`, orig `42ddb685…`)
   embed generation-7 verifier documents; `generation_problem` requires the LATEST version and the adopted controls digest, so
   under v8 both qualifications refuse. Adopting v8 therefore needs, per role: `--qualify 1` re-run with the v8 controllers (job 1
   evidence is still on disk), a new `ADOPT row19-screen-pilot` line for the new qualification digest, and the existing
   `gate/review_<role>.json` archived by hand (the controller never overwrites one). The fixture `_requalify` in test (f3) shows
   that path. Relaxing the generation rule was not done: it is a reviewed C2 guard.
2. **The real job-3 output is unverified here** (Codex records a source-reported 2,589-byte output naming `7527352.sched01` with no
   admission-failure marker; a real fresh v8 receipt must retrieve and bind those bytes). v7 never pulled `row19_screen_refit_3.out`; this candidate requires it to exist,
   name `7527352.sched01` (the script's `code … job $PBS_JOBID …` line) and carry no ADMISSION FAILED. Test (g) used a synthetic
   file. The first v8 status run settles it.
3. **Stricter readings chosen:** any unreadable or temporary timing file anywhere withholds a disposition; any file at a
   disposed coordinate must be a later bound job's planned completion; the output must name the PBS id; the policy pin is
   checked for every refit job; only walltime may differ from the manifest; a dispositioned summary missing its claim refuses.
4. Refit records carry no job field (`row19_shard.resample_record`); attribution is through timing, checked both in the
   verifier units and directly on disk (timing written before the record, so an orphan timing is caught).
5. The release consumer pins `chpc/row19_screen_controls.json` (`row19_screen_release.py` CONSUMER_FILES); a v8 controls file
   changes that pin - and so does admit - for any later numerical-release adoption (none exists yet).
6. CHPC Accounts Policy v2.8 §2.2(6) (record §3): deployment and any agent-led Lengau operation remain conditional on the
   permitted operating route; nothing here operates.

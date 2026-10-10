# Row 19 screen controllers, version 8 - CANDIDATE (not adopted, not deployed, needs Codex review)

Date: 9 October 2026. Built by Claude (R052 Entropy SI) as a job for the R052 session. Authority for the design: Codex
record `reviews/2026-10-09_refit_wall_kill_codex_record.md` (SHA-256 `25afbca9565af7f30c7b9764956df1235f8750bbc1ef2c7d54671bb0ead7412f`),
verdict 1 (closed-no-record disposition of refit job 3, `7527352.sched01`) and verdict 2 (prospective 48-h refit envelope).
Base: the adopted version 7 (admit `573e5b18…`, status `dac142fb…`, verify `d8d3c73b…`, controls `43a099ca…`).

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
| `chpc/candidate_v8/row19_screen_admit.py` | `chpc/row19_screen_admit.py` | `e62f289bc9e0d970960347af7ad2fa5df079c2d18f17781fa9e93ca5e45a2242` |
| `chpc/candidate_v8/row19_screen_status.py` | `chpc/row19_screen_status.py` | `3457c9e8fb555c4f12747d6dcdaacf258781495b051da397357041ed289905bf` |
| `chpc/candidate_v8/row19_screen_controls.json` | `chpc/row19_screen_controls.json` | `76aa22f9a960b2c0d1613ab9f4865cd50bb92453561fd8945249932b318af92f` |
| `chpc/row19_screen_resources.json` (new) | same | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |
| `chpc/row19_screen_verify.py` (unchanged) | same | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `chpc/row19_screen_release.py` (unchanged) | same | `7a67fd1fc3ca60d77c62ddcaea5d4e11a9ec87ac6b2b02f0bc75ab34a366507f` |
| `chpc/programme_gate.py` (unchanged) | same | `10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0` |

Controls version 8 appends one entry (versions 1-7, programme, history manifest and deployment blocks byte-for-byte the same
in meaning) pinning all six files above, including the resource policy.

## (1) Closed-no-record disposition (verdict 1)

**Status view** (`candidate_v8/row19_screen_status.py`):
- `fresh_snapshot` (:119) now calls `fetch_job_outputs` (:135): for every entry of the role that is settled with no runner-end
  field, it pulls `<toolchain>/jobs/row19_screen_<role>_<n>.out` (the `#PBS -o` path the admission writes,
  `row19_screen_admit.py` :1236 onward) into the snapshot's `jobs/`, recording rc, ok and SHA-256 in `jobs/_fetch.json`. A failed
  or missing retrieval is recorded, not fatal: that job simply cannot be dispositioned.
- `closed_no_record` (:206) returns a disposition only when ALL hold: scheduler state F with an observed integer exit; ledger
  SETTLED with finite charge, a technical note and a settlement time; no `runner_exit`, `runner_ended` or `runner_wall_s`; the
  plan's token and job are the entry's; no status file scoped to the PBS id (by name, any slot incl. unplanned, or by parsed
  `job`) and no unreadable status with no job named; no verifier unit and no timing file anywhere naming the job, and no
  unreadable or temporary timing file; every file at a planned coordinate (record or timing, temporary files included) a valid
  record whose timing names a LATER bound job that planned it in that slot; and the retrieved output names the PBS id and has
  no `ADMISSION FAILED`. It is examined for every terminal job without a runner exit (:310), so an unsettled kill reports why.
- Only the three alarms are suppressed, only then (:324 bad scheduler exit, :326 no runner end, :341 missing worker status).
  Memory, binding, foreign, anchor and record alarms are unchanged. The summary keeps the actual exit, zero
  ended/new/resumed/left and null worker measurements, carries `disposition` (kind, scheduler exit, charge, output file and
  SHA-256) and `partition.uncompleted` with `uncompleted_origin: "plan"` (:395); no worker status is invented.
- The receipt binds the output (`bound.job_outputs`, :468) and a copy is retained beside it (:477). `--qualify` refuses a
  dispositioned job (:506). An unreadable status file is now an alarm instead of stopping the view.

**Admission** (`candidate_v8/row19_screen_admit.py`):
- `disposition_problem` (:746) recomputes every condition from the CURRENT ledger, the root and the PBS output on disk; the
  summary's `disposition` is a claim to check, never a boolean that waives anything. Helpers: `status_scoped` (:687),
  `timing_scan` (:705), `coordinate_files` (:723), `later_completion` (:737), `job_output_path` (:680). The output must be the
  bytes the receipt bound (a change after the receipt refuses: recollect).
- `receipt_problem` (:1096) routes a summary carrying `disposition` to it (:1121); every other summary keeps `job_summary_problem`.
  A dispositioned summary without its claim is an ordinary terminal job and refuses (exit 271).
- `units_problem` (:884, :899): nothing may name a dispositioned job; its partition is checked by `disposition_problem`.
  The revision-7 producer rule is unchanged, so a later retry completes the disposed coordinates only through its own bound
  plan, job and slot, and a record or timing naming the killed job holds.
- `transition_problem` (:985, :1001) re-reads the ledger for a disposed job: SETTLED, same charge and PBS id, no runner-end field.
- Pilot guard: `job_summary_problem(pilot=True)` refuses a dispositioned job (:840).
- Planner unchanged (`evidence` :384, `plan_jobs` :443). Confirmed on the retained local snapshot (read only): job 3 settled
  leaves flight, done 48, in flight 144 (jobs 4-9), and job 10 plans exactly reps 51-74 at index 0 - the retry comes first.

## (2) Prospective refit resource policy (verdict 2)

- `chpc/row19_screen_resources.json`: schema `row19-screen-resources-1`, role refit, bound to the screen manifest
  `43b75f94…`; one envelope from `first_job` 10: serial, 24 cores, 48 h, 120 GB, haswell_reg, reserve 1,800 s, per_slot 1.
- `resolve_envelope` (:570): originals always get the manifest's request; refit checks that the policy is the lineage's pinned
  bytes (every refit job, also below first_job), validates its shape (`resources_shape_problem` :545: walltime at most 48 h,
  one index per worker, integer reserve), returns the manifest's 30 h below first_job, and from it on requires the policy to
  name this manifest and every non-walltime field to equal the manifest's (walltime-only change; the manifest is never edited).
- `main` (:1288): each NEW job's envelope resolved (:1366); funding = the sum of resolved full requests through the programme
  gate and a new campaign-cap pre-check (`campaign_cap_problem` :1189; cap 60,000) before any reservation; the script is checked
  before reserving and again with the real token (`pbs_request_problem` :619: `-q`, `walltime=`, select line,
  `DEADLINE=$((START + W - R))`, `--walltime-s W`, each exactly once); the ledger reservation is `cores x W` (1,152 core-hours at
  48 h); the plan carries `walltime_s`, `queue` and `envelope` (:1396); `envelope_problem` (:633) checks plan + ledger entry.
- Receipts: `receipt_envelope_problem` (:659) checks every job at or above first_job against its plan, CURRENT ledger entry and
  the status view's `plan_walltime_s` / `requested_walltime_s` (the scheduler's `Resource_List.walltime`, now parsed by the
  status view, which alarms a plan/scheduler difference). `policy_first_job` (:604) fails closed (a bad policy checks every job).
- Highest job number 100 stays the adopted pilot review's `max_job` (unchanged); programme allocation 100,000 unchanged.

## Verification (local fixtures only)

Harness `tests_v8.py` and full output `tests_v8_output.txt` are in the R052 session scratchpad
(`/private/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/fdb5f471-1679-481f-8198-f3f211cc7447/scratchpad/`), with the
patch scripts that turn the v7 bytes into these (`admit_v8.py`, `status_v8.py`, `controls_v8.py`, `build_v8.sh`). They ran in a
scratch git copy of `t1_access` holding the candidate in place.
- New: **12/12 passed** - (a) unsettled kill holds (all three alarms, 24 missing statuses; a claimed disposition refused);
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
  zero alarms (a synthetic PBS output stands in, see below); (h) the originals role uses the same rule.
- Unchanged v7 modules against the candidate: screen 23/23, bank 10/10, slice 17/17, watch 5/5, control compare 11/11,
  oracle 5/5, shard 12/12, recycle 5/5 (88/88).

## Open points for the review

1. **A new generation needs fresh job-1 evidence.** The retained job-1 qualifications (refit `4bbe4aa6…`, orig `42ddb685…`)
   embed generation-7 verifier documents; `generation_problem` requires the LATEST version and the adopted controls digest, so
   under v8 both qualifications refuse. Adopting v8 therefore needs, per role: `--qualify 1` re-run with the v8 controllers (job 1
   evidence is still on disk), a new `ADOPT row19-screen-pilot` line for the new qualification digest, and the existing
   `gate/review_<role>.json` archived by hand (the controller never overwrites one). The fixture `_requalify` in test (f3) shows
   that path. Relaxing the generation rule was not done: it is a reviewed C2 guard.
2. **The real job-3 output is unverified.** v7 never pulled `row19_screen_refit_3.out`; this candidate requires it to exist,
   name `7527352.sched01` (the script's `code … job $PBS_JOBID …` line) and carry no ADMISSION FAILED. Test (g) used a synthetic
   file. The first v8 status run settles it.
3. **Stricter readings chosen:** any unreadable or temporary timing file anywhere withholds a disposition; any file at a
   disposed coordinate must be a later bound job's planned completion; the output must name the PBS id; the policy pin is
   checked for every refit job; only walltime may differ from the manifest; a dispositioned summary missing its claim refuses.
4. Refit records carry no job field (`row19_shard.resample_record`); attribution is through timing, checked both in the
   verifier units and directly on disk (timing written before the record, so an orphan timing is caught).
5. The release consumer pins `chpc/row19_screen_controls.json` (`row19_screen_release.py` CONSUMER_FILES); a v8 controls file
   changes that pin for any later numerical-release adoption (none exists yet).
6. CHPC Accounts Policy v2.8 §2.2(6) (record §3): deployment and any agent-led Lengau operation remain conditional on the
   permitted operating route; nothing here operates.

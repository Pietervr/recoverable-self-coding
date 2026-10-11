# T1 on EC2 spot (ledger row 23)

Plain EC2 spot instances (not SageMaker) running the Lengau toolchain bytes at the Lengau path, so the pinned wrapper
`t1py`, its sha256 and every library version are identical. Zen 4 (c7a/m7a) has one physical core per vCPU.

## Files (revision 4, after Codex RSC `2cc26ee`, `a2e92b2`, `137b261` and `91a567c`; finish repairs after `3f67eaf` and `cf07869`)

- `make_bench_manifests.py` -> `bench/manifest_{A,B}.json`, `bench/plan.json`, `bench/SHA256SUMS`: benchmark-only
  operational manifests derived from the production screen manifest `43b75f94` (unchanged); only root, campaign,
  cores 36 and expect_layer_s 68,400 differ.
- `bench_userdata.sh` - the instance's whole job: two checked stop timers first, fail-closed setup (checksums, wrapper
  pin, attestation, job-start per arm), stage 1 row 6 panel and stage 2 index 0 of reps 3..38 per arm, a recorded
  outcome for each declared process published atomically (or censored at the upload deadline) - 78 processes, or 42
  when arm A is refused at job-start because native Zen 4 does not reproduce the dataset identities (RSC `a44f5aa`:
  `env/ARM_A_REFUSED`, its 36 stage-2 workers not declared, its row-6 panel still run), cleanup of
  every process group by TERM then KILL on one 120 s bound (survivors recorded), a checked outcomes certificate, a
  bounded transfer with a checked disposition, shutdown.
- `attest.py` - each arm's EFFECTIVE flags (after models.py's setdefault), numpy dispatch, OpenBLAS core, thread caps;
  exits 3 when the named profile (A, B_full, B_nomask) is not in effect.
- `bench_launch.py` - admission under an exclusive run lock (shared with the reaper's ledger writes); attempt states
  intent / launched / rejected / ambiguous. 'rejected' (charged 0) only when a definitive EC2 client error answers the
  FIRST dispatch of a fresh admission, made as a single HTTP attempt; a rejection after any unanswered dispatch or on a
  recovered intent leaves the attempt ambiguous and funded. Ambiguity is resolved only by re-issuing the SAME saved
  request, token and user-data bytes (hash checked before every replay). Worst case per attempt includes 900 s reaper
  grace and a 1,800 s reserve (USD 27.01 at 21.5 h). S3 prefix check fails closed; the reaper is started detached under
  caffeinate, and any start failure or missing first heartbeat makes the launcher terminate the instance itself.
- `bench_reaper.py` - heartbeat every poll; Describe/Terminate errors caught, logged and retried; only an attributable
  shutting-down/terminated observation ends compute billing, stamped after that response; tagged volumes polled to
  deletion for the ancillary hours; then 'reconciled' under the lock.
- `bench_compare.py` - runs on Lengau under t1py with the controller tree: pinned arm manifests and plan, full expected
  task bindings, canonical names only (aliases refused), frozen-task validation, canonical float.hex payload, the
  procedure's per-predictor usable predicate, non-finite disagreements reported, typed attestation profiles with a known
  OpenBLAS core, a valid occupancy timeline, a verified transfer; exit 3 for an incomplete or invalid panel. A typed arm-A
  job-start refusal counts only with `manifest_A.json` at its reviewed pin `824837ee` and the same HELD line as the
  retained `job_start_A.log`; `declared.txt` is required, duplicate-free and exactly 42 (A refused) or 78 names, agreeing
  with the outcomes certificate's declared count, every outcome an integer 0 and no survivor (Codex `3f67eaf` F-1).
- `bench_finish.py` - one command per attempt, FRESH each time: s3 sync into a new local directory, a new remote directory
  and a unique report; the Lengau copy's bundle digest, file count and comparator sha256 rechecked; the six controller-tree
  files the comparator imports must equal the reviewed frozen expectation (production manifest `43b75f94`, its code pins,
  the adopted controls' verifier pin) before the comparator runs and be unchanged after it (`cf07869` F-3); the comparator's
  exit status propagated (only 0 can succeed); a binding file ties report, run, attempt, comparator, tree pins and bundle.
  Success criterion, recorded before the completed row-23 parity/refit results (owner conditional go ~20:40Z 10 Oct,
  committed Unimog `7c6626e6` 21:16:38Z): valid report; B_full; arm B row 6 exact 12/12 with identical decisions and failed
  flags; arm B 36/36 validated, timed, payload-exact with no non-finite disagreement; arm A refused at job-start (verified)
  or fully validated. Float-bit parity can include agreeing failed fits: reproduction, not coverage. `--declare` writes
  row 23 into `ec2_release_state.json` only on this invocation's exit 0 and the criterion (F-1/F-2 closed, F-3 repaired
  in `3efb8bb`). `bench_row6_only.py` runs stage 1 alone (counts and deviations only).
- `tests/` - stub-`aws` launcher (24 checks incl. the cutover drain), reaper, finish (23) and the user-data cleanup test
  (bash >= 4).
- `iam/` - the two policies the owner creates in the console (below).

Row 23 licenses no pooling: its result feeds a separate prospective production qualification.

## Production and qualification (v10r3 package + D-1/D-2, 11 Oct 2026; built, NOT adopted, activated or launched)

Design `PRODUCTION_DESIGN.md`, qualification `QUALIFICATION_PLAN.md`. Current review: Codex RSC `cf07869` - controls v12
(`../chpc/candidate_v10r3/`, `80d1c6d9`) FAVOURABLE for adoption with partition null (literal ADOPT in that record, not
performed; v11 `6342aa10` and its earlier literal stay unchanged); the Lengau authority/ACK/generation, post-ACK replay,
adopted-controls lineage, S STOP/HOLD, qualifier and release binding statically closed; the complete dispatch basis held
on D-1 (receipt at every recovery re-issue) and D-2 (drain in-flight benchmark commands before qualification), both
repaired in RSC `e644584`; Codex RSC `1609fa7`: closed statically, the Q1/Q2/S basis FAVOURABLE with operating gates, and `bench_finish --declare` FAVOURABLE for attempt 5. Epoch-1 partition DECLARED (11 Oct, RSC candidate): `chpc/row19_partition_e1.json` (sha256 `8d1de408`), k = 40, EC2 owns indices 160..199 of all 100 reps (4,000 coordinates). Why 40: the USD 2,300 production envelope funds ~40-55 indices at the costed rate, so 40 is fundable in full; Lengau's refit runs from index 0 upward and was at index 2 on 10 Oct, far below 160; if either side finishes its share early a new epoch is declared and reviewed. It is pinned by candidate controls v13 (`chpc/candidate_v10r4/`, = v12 + the partition pin; helper bytes unchanged) AWAITING REVIEW - not adopted, not activated. Bank evaluator `compatible()` (`9afcc03`) FAVOURABLE within its scope.
Owner (11 Oct): USD 45 for Q1 + Q2 accepted (28 + 17, one attempt each; frozen-plan worst USD 44.462); a successful
qualification with a FAVOURABLE actual-result review goes directly to production with no further owner go, inside the
USD 2,300 envelope and the USD 3,000 cap; a retry needs the owner.

- `prod_authority.py` (Mac) - the one claim and USD authority over every run: global sequences and fences, a sealed
  inventory, `ack` of ingested output, a two-phase `disposition` / `disposition-confirm` against the Lengau root's
  acknowledgement (canonical root only), `release-adopt` from a validated certificate (exact code set `RELEASE_CODE`) and
  review, benchmark/region exclusion; every seal is a new, write-once generation.
- `prod_launch.py` (Mac) - admits `production`, `Q1`, `Q2` under the authority lock: STOP absent only on a proved S3 404,
  release state, canonical activation with its controls lineage, exact operational manifest, a fresh receipt bound to the
  current inventory, the snapshot's registered EC2 artifacts rechecked, the budget; records region and zone; controls only
  through `row19_partition.adopted_controls`; STOP and receipt freshness rechecked after staging and before every
  RunInstances issue. `--recover` (needs `--partition`) re-issues only with a correctly bound CURRENT receipt that binds the
  current sealed inventory carrying this very attempt; the per-issue guard (STOP, receipt age, inventory binding, attempt)
  runs before EVERY re-issue; otherwise zero RunInstances and the attempt stays funded (D-1).
- `bench_launch.py` - every benchmark command holds `runs/.bench_inflight.lock` SHARED for its whole life and refuses at
  entry AND before every RunInstances issue/retry/recovery once the cutover fence `runs/BENCH_FENCE.json` exists, qualification
  is permitted or any qualification/production attempt exists. `qual_permit.py --record <review>` is the only way to set
  `qualification.permitted`: it takes that lock EXCLUSIVELY (draining every in-flight benchmark command, including one still
  waiting or staging before its first journal entry), writes the fence once, then permits; `release_state()` needs the
  fence (D-2). The running row-23 reaper never issues RunInstances and is unaffected.
- `prod_userdata.sh`, `prod_stop.py` - the instance contract and the common STOP.
- `ec2_release_state.json` - row 23 / qualification / production gates, each backed by a pinned file.
- `qual_S_plan.json` - S's fixed plan (jobs 1 and 2); `make_prod_manifest.py` - operational manifests.
- Lengau side (`../chpc/`): `row19_partition.py` (declare / activate), `row19_ec2_root.py install` (the inventory and the
  disposition fence on the root), `row19_ec2_ingest.py`, `row19_ec2_qualify.py` (certificate), `row19_ec2_shadow.py` (S
  admission), `row19_ec2_state.py` (shared contracts), candidate controls v11 in `candidate_v10r2/` and v12 in
  `candidate_v10r3/` (both null-only favourable; the S declaration made in v11 stands unchanged in v12), v13 in
  `candidate_v10r4/` (= v12 + the epoch-1 partition pin `row19_partition_e1.json`, k = 40; awaiting review). `row19_ec2_root.py install` grants a canonical acknowledgement only for the
  production manifest at its own root; anything else needs `--sandbox`.
- Operator flow per inventory change: `python3 ec2_sync.py cycle` (seal a new generation -> copy to Lengau -> `t1py
  chpc/row19_ec2_root.py install` in the controller tree -> pull `ack_g<N>.json` + `register.json` -> `disposition-confirm` /
  `ack` on that evidence -> seal and install again when anything was released), then a fresh whole-role receipt. Usable once
  `row19_ec2_root.py` is deployed with the adopted controls; tests `tests/test_ec2_sync.py` (local transport).
- `tests/` also hold `test_prod_authority.py`, `test_prod_launch.py`, `test_prod_userdata.py`; the Lengau-side tests are
  `../test_row19_partition.py`, `../test_row19_ec2_ingest.py` (stub, or real records on Lengau), `../test_row19_ec2_status.py`,
  `../test_row19_ec2_qualify.py`, `../test_row19_ec2_shadow.py`.

## Owner's console steps (IAM is denied to the read user; the owner types grants)

1. IAM -> Roles -> Create role -> Trusted entity "AWS service", use case **EC2** -> skip managed policies -> name
   **`xtenure-ec2-t1-worker`** -> create. Open it -> Add permissions -> Create inline policy -> JSON -> paste
   `iam/role_policy_xtenure-ec2-t1-worker.json` -> name `t1-s3` -> save. (The console creates the instance profile of
   the same name.)
2. IAM -> Policies -> Create policy -> JSON -> paste `iam/user_policy_xtenure-t1-ec2.json` -> name **`xtenure-t1-ec2`**
   -> create. IAM -> Users -> `xtenure-claude-read` -> Add permissions -> Attach policies directly -> `xtenure-t1-ec2`.
   (A managed policy, because the user's inline policies are at the 2,048-character cap.)
3. Service Quotas -> Amazon EC2 -> the launch region -> "All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance
   Requests": the benchmark needs **96** vCPUs (512 granted in us-west-2 and eu-north-1). Since attempt 5 (10 Oct) EC2
   runs in **eu-north-1** (interruption rate < 5 %/month vs > 20 % in us-west-2); results stay on the Oregon bucket.

`python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2 --dry-run` prints "EC2 authorization
OK" before a real attempt; revision 4 is favourable (Codex `91a567c`).

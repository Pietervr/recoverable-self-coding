# T1 on EC2 spot (ledger row 23)

Plain EC2 spot instances (not SageMaker) running the Lengau toolchain bytes at the Lengau path, so the pinned wrapper
`t1py`, its sha256 and every library version are identical. Zen 4 (c7a/m7a) has one physical core per vCPU.

## Files (revision 4, after Codex RSC `2cc26ee`, `a2e92b2` and `137b261`)

- `make_bench_manifests.py` -> `bench/manifest_{A,B}.json`, `bench/plan.json`, `bench/SHA256SUMS`: benchmark-only
  operational manifests derived from the production screen manifest `43b75f94` (unchanged); only root, campaign,
  cores 36 and expect_layer_s 68,400 differ.
- `bench_userdata.sh` - the instance's whole job: two checked stop timers first, fail-closed setup (checksums, wrapper
  pin, attestation, job-start per arm), stage 1 row 6 panel and stage 2 index 0 of reps 3..38 per arm, a recorded
  outcome for each of the 78 declared processes published atomically (or censored at the upload deadline), cleanup of
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
  procedure's per-predictor usable predicate, non-finite disagreements reported, exact 78 process names all exit 0,
  typed attestation profiles with a known OpenBLAS core, a valid occupancy timeline, a verified transfer; exit 3 for an
  incomplete or invalid panel.
- `tests/` - stub-`aws` launcher (13 checks) and reaper tests, and the user-data cleanup test (bash >= 4).
- `iam/` - the two policies the owner creates in the console (below).

Row 23 licenses no pooling: its result feeds a separate prospective production qualification.

## Production and qualification (v11 candidate, 11 Oct 2026; built, NOT adopted, activated or launched)

Design `PRODUCTION_DESIGN.md`, qualification `QUALIFICATION_PLAN.md`, repairs for Codex RSC `0483db4` and `3dc0daf`.
Owner (11 Oct): USD 45 for Q1 + Q2 accepted (28 + 17, one attempt each); a successful qualification with a FAVOURABLE
actual-result review goes directly to production, inside the USD 2,300 envelope and the USD 3,000 cap.

- `prod_authority.py` (Mac) - the one claim and USD authority over every run: global sequences and fences, a sealed
  inventory, `ack` of ingested output, a two-phase `disposition` / `disposition-confirm` against the Lengau root's
  acknowledgement, `release-adopt` from a validated certificate and review, benchmark/region exclusion.
- `prod_launch.py` (Mac) - admits `production`, `Q1`, `Q2` under the authority lock: STOP absent only on a proved S3 404,
  release state, canonical activation with its controls lineage, exact operational manifest, a fresh receipt bound to the
  current inventory, the snapshot's registered EC2 artifacts rechecked, the budget; records region and zone.
- `prod_userdata.sh`, `prod_stop.py` - the instance contract and the common STOP.
- `ec2_release_state.json` - row 23 / qualification / production gates, each backed by a pinned file.
- `qual_S_plan.json` - S's fixed plan (jobs 1 and 2); `make_prod_manifest.py` - operational manifests.
- Lengau side (`../chpc/`): `row19_partition.py` (declare / activate), `row19_ec2_root.py install` (the inventory and the
  disposition fence on the root), `row19_ec2_ingest.py`, `row19_ec2_qualify.py` (certificate), `row19_ec2_shadow.py` (S
  admission), `row19_ec2_state.py` (shared contracts), candidate controls v11 in `candidate_v10r2/`.
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
3. Service Quotas -> Amazon EC2 -> region **us-west-2** -> "All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance
   Requests": the benchmark needs **96** vCPUs; request **2,000** now so a later production fleet is not held up (a quota is capacity, not spending or campaign permission).

Then `python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b2 --dry-run` must print
"EC2 authorization OK" before a real attempt, which also needs a favourable Codex review of revision 2.

# T1 on EC2 spot (ledger row 23)

Plain EC2 spot instances (not SageMaker) running the Lengau toolchain bytes at the Lengau path, so the pinned wrapper
`t1py`, its sha256 and every library version are identical. Zen 4 (c7a/m7a) has one physical core per vCPU.

## Files (revision 2, after Codex RSC `2cc26ee`)

- `make_bench_manifests.py` -> `bench/manifest_{A,B}.json`, `bench/plan.json`, `bench/SHA256SUMS`: benchmark-only
  operational manifests derived from the production screen manifest `43b75f94` (unchanged); only root, campaign,
  cores 36 and expect_layer_s 68,400 differ.
- `bench_userdata.sh` - the instance's whole job: two checked stop timers first, fail-closed setup (checksums, wrapper
  pin, attestation, job-start per arm), stage 1 row 6 panel and stage 2 index 0 of reps 3..38 per arm, a recorded
  outcome for each of the 78 declared processes (or censored at the upload deadline), bounded upload with a
  local/remote count check, shutdown.
- `attest.py` - each arm's EFFECTIVE flags (after models.py's setdefault), numpy dispatch, OpenBLAS core, thread caps;
  exits 3 when the named profile (A, B_full, B_nomask) is not in effect.
- `bench_launch.py` - one attempt per call: cumulative USD 28.00 row ceiling in `runs/<run>/attempts.json`, duplicate
  guards, intent and client token written before RunInstances, ambiguous responses reconciled by token; `--dry-run`
  checks EC2 authorization only (S3 uploads are not exercised).
- `bench_reaper.py` - run beside every attempt: terminates at launch + lifetime + 600 s if still running and records the
  observed end of billing (upper bound) and the charge.
- `bench_compare.py` - runs on Lengau under t1py with the controller tree: frozen-task validation of every record,
  canonical float.hex payload over exactly the 36 coordinates, failed fits apart, paired timings, deviations only;
  exit 3 for an incomplete or invalid panel.
- `iam/` - the two policies the owner creates in the console (below).

Row 23 licenses no pooling: its result feeds a separate prospective production qualification.

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

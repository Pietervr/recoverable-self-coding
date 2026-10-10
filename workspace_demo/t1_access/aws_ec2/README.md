# T1 on EC2 spot (ledger row 23)

Plain EC2 spot instances (not SageMaker) running the Lengau toolchain bytes at the Lengau path, so the pinned wrapper
`t1py`, its sha256 and every library version are identical. Zen 4 (c7a/m7a) has one physical core per vCPU.

## Files

- `bench_userdata.sh` - the instance's whole job: install, two arms (A native, B AVX2/Haswell-pinned), stage 1 row 6
  panel, stage 2 screen refit index 0 of reps 3..38, S3 sync every 30 min, self-terminate (hard stop 23.5 h).
- `bench_launch.py` - from the Mac (profile `xtenure-read`): uploads the tarball, launches one spot c7a.24xlarge
  (MaxPrice USD 1.20/h, one-time, terminate on shutdown); `--dry-run` checks permissions without launching.
- `bench_compare.py` - Mac side: deviations and counts only (blinded), plus the Lengau/EC2 speed ratio.
- `iam/` - the two policies the owner creates in the console (below).

## Owner's console steps (IAM is denied to the read user; the owner types grants)

1. IAM -> Roles -> Create role -> Trusted entity "AWS service", use case **EC2** -> skip managed policies -> name
   **`xtenure-ec2-t1-worker`** -> create. Open it -> Add permissions -> Create inline policy -> JSON -> paste
   `iam/role_policy_xtenure-ec2-t1-worker.json` -> name `t1-s3` -> save. (The console creates the instance profile of
   the same name.)
2. IAM -> Policies -> Create policy -> JSON -> paste `iam/user_policy_xtenure-t1-ec2.json` -> name **`xtenure-t1-ec2`**
   -> create. IAM -> Users -> `xtenure-claude-read` -> Add permissions -> Attach policies directly -> `xtenure-t1-ec2`.
   (A managed policy, because the user's inline policies are at the 2,048-character cap.)
3. Service Quotas -> Amazon EC2 -> region **us-west-2** -> "All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance
   Requests": the benchmark needs **96** vCPUs; request **2,000** now for the production fleet (approval takes time).

Then `python3 bench_launch.py --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --run b1 --dry-run` must print
"permissions OK" before the real launch.

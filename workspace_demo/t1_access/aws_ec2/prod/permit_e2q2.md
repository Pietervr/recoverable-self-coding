# E2Q2 permission record - EC2 provider epoch 2, qualification attempt E2Q2

Written 21 Oct 2026. Consumed by `python3 aws_ec2/qual_permit.py --epoch2 --e2q2 --record prod/permit_e2q2.md`, which pins
this file's bytes (path relative to `aws_ec2/`) into `ec2_release_state.json` and does not judge its content. Do not edit
this file after it has been permitted.

## Why E2Q2: E2Q1 ended for an external cause

- `qual-E2Q1/1` (i-0f4810f5fec29de51, launched 2026-10-21T01:05:36Z) received an AWS spot terminate notice for
  2026-10-21T13:48:24Z (`env/spot_notice.json`; EC2 state reason "Service initiated") after 12.72 h of its 22 h lifetime.
  It published 0 records, so there is no usable bundle; no qualifier was run and no evaluation claim was taken.
- Reconciled USD 15.74 (reaper); disposition recorded (`prod_authority.py disposition`, inventory g76) and confirmed on
  ack_g77 (ec2_sync, installed g78).

## Authority

- Owner approval 20 Oct 2026, R052 lean T1 operating plan (Unimog-Projects commit dbef870a): item 4 launches the EC2
  epoch-2 qualifier and production within USD 2,300 / 3,000; item 2 makes operational failures requeue without an owner
  check-in; item 6 limits owner contact to spend decisions and the SI submission. A spot interruption is an operational,
  external-cause failure inside the already approved qualification allowance, so this record is written by the operator
  (Claude, R052) under those items and reported to the owner the same day.

## What is permitted

- **Exactly one attempt: E2Q2** (`qual-E2Q2/1`, contract E2Q2, epoch 2), launched by `prod_launch.py --contract E2Q2
  --epoch 2 --manifest prod/manifest_e2q2_e2.json --panel prod/panel_e2q_e2.json`.
- **One c7a.24xlarge spot instance**, worst case USD 27.92, charged to the USD 300 allowance (E2Q1 USD 15.74 already
  charged; the two qualification instances together stay below USD 44).
- **Funding unchanged:** `aws_ec2/e2_funding.json`, sha256 `d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815`.
- Staged and qualified only through `aws_ec2/e2q_stage.py run --run qual-E2Q2 --attempt 1`, following
  `aws_ec2/E2_OPERATING_SEQUENCE.md` (certificate archival, read-only lost-reply retrieval).

## What is not permitted

- No third qualification instance. If E2Q2 is also interrupted, or ends NO_RELEASE or INCONCLUSIVE, it goes back to the
  owner.
- Release-adopt and production follow only after a committed FAVOURABLE Codex actual-result review of the E2Q2 certificate.

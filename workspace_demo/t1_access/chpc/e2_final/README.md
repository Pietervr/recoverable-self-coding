# EC2 epoch 2 - final declaration inputs (19 Oct 2026; NOT adopted)

Produced under DESIGN_e2.md s.6 step 4 after step 3 (qual-Q1/4 dispositioned, fenced on ack_g48; inventory g52 installed
19 Oct 09:17Z) and a fresh zero-alarm refit receipt `watch_refit_20261019T091816Z` (designated 648 done, 0 in flight).

| File | sha256 | How |
|---|---|---|
| `claims_snapshot_e2.json` | `31cc268ff3247858fc73ac17a3a387b43e17a829d9cdea505958890a97eecb6f` | canonical snapshot on Lengau under the plan lock, candidate `row19_partition.py` (eabf50c3) staged at `t1_toolchain/e2_stage/` (outside the controller clone): lengau_done 1065, lengau_planned 1071, ec2_completed 0 |
| `row19_partition_e2.json` | `48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6` | `declare2 --epoch 2` on the Mac from the adopted manifest (43b75f94), designated (a96eb598), e1 partition (8d1de408) and this snapshot; `verify2` byte-equal. Owned 3,274 (as forecast); cover designated 4800 = lengau_done 648 + lengau_open 878 + ec2_owned 3274 |
| `e2_funding.json` | `d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815` | `candidate_e2/aws_ec2/make_e2_funding.py`; byte-identical to the 17 Oct candidate (owned count unchanged): forecast USD 1,778.52, epoch cap 2,078.52, 46 base batches, 8.87 days at 5 instances |
| `manifest_production_e2.json` | `e126050536a8459cb1432cf78321e82147c67f5406441fff131a1f543f9f82f9` | `candidate_e2/aws_ec2/make_prod_manifest.py --epoch 2 --contract production --expect-s 75300` |
| `panel_e2q_e2.json` | `f04a5e43634e13bfceaf173e303ebf780f4280de044b6bd97ee9e2c3f711c7a2` | `candidate_e2q/aws_ec2/make_prod_manifest.py --contract E2Q1/E2Q2 --partition --snapshot --panel-out` |
| `manifest_e2q1_e2.json`, `manifest_e2q2_e2.json` | `3ea8cafd...`, `4af4a64d...` | same maker; equal to the candidate_e2q bytes (partition-independent) |

Panel vs the 17 Oct fixture (declared rule unchanged, outcome-blind): Lengau completed rep 24 indices 9-10 since 17 Oct, so
the 20 lowest Lengau-completed duplicates are now rep 24 (0-10) + rep 25 (0-5, 7-9) instead of rep 24 (0-8) + 25 (0-5, 7, 8)
+ 28 (0-2). Concentration: 63 workers on rep 24 (52 work + 11 duplicates), 9 on rep 25; the release rule needs
max >= 61 (QUALIFIED_REP_SLOTS), so E2Q1 qualifies a packing 2 workers more concentrated than production's 61 cap. For
Codex to confirm this is acceptable under QUALIFICATION_E2 s.2.

Next: controls v17 pinning `row19_partition_e2.json` (these bytes, promoted to `chpc/`), the REVISION-5 helpers and the
candidate_e2q modules; then one Codex review of partition + funding + v17 + the qualification package (92a62f6).

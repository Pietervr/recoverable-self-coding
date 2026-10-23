# Pilot v19 adoption - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-pilot role=refit qualification=e123d6e5d136dfda31ac5f61dd18a2cce31ecc8dea9f1ad27be73d427cc50b02 max_job=100

Written 22 October 2026 (UTC) by Claude (R052 Entropy SI). The owner approved on 20 Oct 2026 (R052 lean T1 plan, items 1-3,
recorded at Unimog-Projects dbef870a) that Codex reviews only science-affecting changes and that operational steps are
recorded by the operator. This pilot is the migration_v19 step-6 regeneration: ONE metadata-only re-qualification of the
existing refit job 1 under generation 19 - no fit, no new data, no change to analyze.py, models.py, simulate.py or the
shard/ledger code (science bytes unchanged across the deploy).

What was checked before writing this record:
- controls v19 111c3107 adopted with the operator literal (reviews/2026-10-22_controls_v19_operator_record.md, afd2b156);
- migration_v19 scripts on the filled bytes: test_migration_v19 37/0 (RSC 00f518f);
- preflight OK, archive v18 (Lengau SHA256SUMS 0483e93f; Mac 11 members), promote (adoption 2b9f3c78, RSC e338746), DEPLOY OK
  (IDENTICAL, epoch 2 still canonical; the first deploy attempt dropped its ssh with rc 255 and the idempotent re-run completed);
- generation-19 receipts: refit zero alarms with job 54 node-dispositioned on 730ea262; bank zero alarms on retry (first attempt:
  the login-node verify process was killed, rc 137, an operational fault);
- pilot rollover retired the v18 review (gate_retired/review_refit.v18_qual530df9a2_max100.json);
- --qualify 1: the first call was NOT QUALIFIED only because refit jobs 58 (F/4) and 66 (F/0) had ended between receipts and
  were unsettled; they were settled (598.67 and 568.61 core-h; job 58 then slot-dispositioned, two segfaulted workers). The
  second call was NOT QUALIFIED only because the login-node producer verify was killed (rc 137) so no records verified. The
  third call returned QUALIFIED e123d6e5 with zero alarms. Job 1's records did not change between the calls;
- packaged as chpc/qualification_v19_e123d6e5/ (24 files + SHA256SUMS).

Verdict: FAVOURABLE for adoption with max_job=100, as the v18 pilot was.

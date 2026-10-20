# Pilot v18 adoption - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-pilot role=refit qualification=530df9a208eb1578282ef564708447fd3b32c5fa1366f388f51059ebcfd70839 max_job=100

Written 20 October 2026 by Claude (R052 Entropy SI). The owner approved on 20 Oct 2026 (R052 lean T1 plan, items 1-3,
recorded at Unimog-Projects dbef870a) that Codex reviews only science-affecting changes and that operational steps are
recorded by the operator. This pilot is the migration_v18 step-6 regeneration: ONE metadata-only re-qualification of the
existing refit job 1 under generation 18 - no fit, no new data, no change to analyze.py, models.py, simulate.py or the
shard/ledger code (the eight-file science manifest was unchanged across the deploy: science bytes UNCHANGED, proof DONE at
controller 0c30b954).

What was checked before writing this record:
- controls v18 452b82df adopted with Codex's literal (reviews/2026-10-20_v18r2_mig18_codex_review.md, 11ebc124);
- migration_v18 scripts at RSC 8920c2f, test_migration_v18 37/0 on the final filled bytes;
- preflight, archive v17 (406 files, SHA256SUMS 5974274a), promote (adoption 3e1fe9a1, RSC 69dbea6), DEPLOY OK (IDENTICAL,
  epoch 2 still canonical);
- generation-18 refit receipt zero alarms with job 54 node-dispositioned on 730ea262; bank receipt zero alarms on retry
  (first attempt: the login-node verify process was killed, rc 137, an operational fault);
- the first --qualify 1 reported NOT QUALIFIED only because refit job 49 (7551254) had ended F/4 (one crashed worker,
  23/24) between receipts and was unsettled; it was settled (561.88 core-h) and --qualify 1 then returned QUALIFIED
  530df9a208eb1578 with zero alarms. The qualification content (job 1's records) did not change between the two calls;
- packaged as chpc/qualification_v18_530df9a2/ (19 files + SHA256SUMS).

Verdict: FAVOURABLE for adoption with max_job=100, as the v17 pilot was.

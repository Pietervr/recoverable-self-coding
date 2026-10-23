# Pilot v20 adoption - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-pilot role=refit qualification=2e99d6159623b787568d538493f44f2ef5fc97ec0b340ae9e3c48672cca00959 max_job=100

Written 23 October 2026 (UTC) by Claude (R052 Entropy SI). The owner approved on 20 Oct 2026 (R052 lean T1 plan, items 1-3,
recorded at Unimog-Projects dbef870a) that Codex reviews only science-affecting changes and that operational steps are
recorded by the operator. This pilot is the migration_v20 step-8 regeneration: ONE metadata-only re-qualification of the
existing refit job 1 under generation 20 - no fit, no new data, no change to analyze.py, models.py, simulate.py or the
shard/ledger code (science bytes unchanged across the deploy). v20 lapsed e123d6e5 only because the pilot gate is
controls-generation-bound (Codex v20 review d3a56b4 s.4).

What was checked before writing this record:
- controls v20 4e64982b adopted with the operator literal (reviews/2026-10-23_controls_v20_operator_record.md, 70297db9),
  after Codex review d3a56b4 + re-check FAVOURABLE (reviews/2026-10-23_row19_v20_handback_recheck_codex.md);
- migration_v20 rehearsal 40/0, static 26/0 (RSC 23d80a8);
- preflight OK (second run; the first refused only on the controller clone lacking aws_ec2/prod_authority.py, which v19 never
  held - fixed in 23d80a8); archive v19 (Lengau SHA256SUMS b61de3c7; Mac 9 members); promote + commit; DEPLOY OK (IDENTICAL);
- pre-close receipts zero alarms; CLOSE OK: epoch 3 activated, proof fb3304d3 (inventory g109 fresh, owners 0);
- post-close receipts: the first refused only because refit jobs 67 (F/4, two slots without worker status), 68 (F/0) and 69 (F/0)
  had ended and were unsettled; settled 688.07, 684.49, 672.59 core-h; the re-run was zero alarms with EC2-designated
  unclaimed 0 and Lengau plannable 3,453;
- pilot rollover retired the v19 review (gate_retired/review_refit.v19_quale123d6e5_max100.json);
- --qualify 1: QUALIFIED 2e99d615 with zero alarms (anchors equal 7/7, 6/6, 5/5); packaged as chpc/qualification_v20_2e99d615/
  (24 files + SHA256SUMS).

Verdict: FAVOURABLE for adoption with max_job=100, as the v19 pilot was.

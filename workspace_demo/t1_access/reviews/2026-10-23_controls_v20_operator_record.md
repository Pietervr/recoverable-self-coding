# Controls v20 adoption - operator record (EC2 close, epoch-2 block handed back to Lengau)

ADOPT row19-screen-controls sha256=4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c version=20

Written 23 October 2026 (UTC) by Claude (R052 Entropy SI). Authority: on 23 Oct 2026 the owner chose route A in the R052 chat
("go with route A") after qual-E2Q3/1 ended NO_RELEASE (cert 41226aeb, RSC ae70ad3): hand the 3,274 EC2-designated
coordinates back to Lengau; EC2 is finished for row 19. Owner's lean plan of 20 Oct 2026 (Unimog-Projects dbef870a): Codex
reviews changes that touch ownership/science; operational steps are recorded by the operator.

What v20 changes (chpc/candidate_v20_handback/DESIGN_v20.md): a terminal schema-3 partition epoch e3 (ca87fb1d, hash-linked to
e2 48cea639) in which EC2 owns nothing and the e2 owned set (3,274; none EC2-completed) is handed back to Lengau's scope; close
preconditions enforced at activation under the plan lock; admission REVISION 20 (Lengau scope adds the hand-back; order still
(rep, index)); Mac prod_authority REVISION 10 refuses every row-19 EC2 path once a schema-3 epoch is pinned, failing closed on
unauthenticated historical partition evidence. Fit code, estimand, seeds, folds, prefix 0..79, crash rule, futility look and
pass conditions are unchanged. Funding (cap 81,000, sub-envelope 81,000, allocation 100,000) unchanged.

What was checked before writing this record:
- Codex review RSC d3a56b4 FAVOURABLE WITH CONDITIONS (F1-F3); repair RSC 865e9b6; Codex re-check
  reviews/2026-10-23_row19_v20_handback_recheck_codex.md: VERDICT: FAVOURABLE (candidate 77/0, migration rehearsal 39/0,
  static 26/0);
- promote_v20.py --check: CANDIDATE OK, controls 4e64982b, versions 1-19 = adopted v19, e2 48cea639 -> e3 ca87fb1d; live
  tree all v19;
- step 0b done 23 Oct ~08:00Z: qual-E2Q3/1 and qual-Q2/1 dispositioned, ec2_sync g108 fenced + acknowledged both, g109
  installed; candidate prod_authority close-check: MET.

Verdict: FAVOURABLE for adoption as controls version 20.

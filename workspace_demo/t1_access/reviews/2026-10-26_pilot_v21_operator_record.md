# Pilot v21 adoption, max_job 200 - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-pilot role=refit qualification=939a5fa925e7693ebaa03868d60218d8180e64d8afb7fdda7284af2b342049af max_job=200

Written 26 October 2026 (UTC) by Claude (R052 Entropy SI, bounded job; brief Unimog-Projects
prompts/2026-10-26_r052_heal1922_funding_route_job.txt). This record restores the refit pilot gate after the controls v21
deploy, which lapsed the v20 qualification 2e99d615: the gate is controls-generation-bound (DESIGN_v21.md s.7).

Scope: the same scope as the active v20 review it replaces (reviews/2026-10-26_pilot_v20_max200_operator_record.md, max_job
200, set by the owner on 26 Oct 2026). The qualification is ONE metadata-only regeneration of the existing completed pilot job 1
(no fit), packaged as chpc/qualification_v21_939a5fa9/. No science byte changes. This is an operational step under the owner's
20 Oct rule (Unimog-Projects dbef870a).

What was checked before writing this record (chpc/migration_v21/RUNBOOK.md steps 1-7, 26 Oct 2026):
- step 1, preflight_v21.sh: OK at 20:13Z (drain observed, ctl clean at v20, epoch 3 canonical, ledger cap 81,000);
- step 2, archive_v20.sh: Lengau archive v20_before_v21 (845 files, SHA256SUMS b8cea4a7) and the 8-member Mac archive;
- step 3, the promotion: RSC 0c8dd64;
- step 4, deploy_v21.sh at 20:18:50Z: ctl f6b281b, IDENTICAL, science unchanged. The route on the real ledgers reads
  CSCI1913 92,376.2 and HEAL1922 0.0;
- step 5, raise_cap_v21.sh: ledger cap 181,000 with cap_history (ctl d952818; RSC 37dcd97);
- step 6, rollover: the v20 max-200 review is retired to gate_retired/review_refit.v20_qual2e99d615_max200.json;
- step 7, --qualify 1: receipt watch_refit_20261026T201935Z with no alarms (fresh evidence); QUALIFIED refit job 1 939a5fa9;
  package_qual_v21.py packaged 33 files + SHA256SUMS; the verifier generation is v21 with controls 72a5d260.
- refit jobs 101-110 (admitted under v20 at 20:13Z) are untouched and charged to CSCI1913 by the no-field rule.

Verdict: FAVOURABLE for adoption with max_job=200.

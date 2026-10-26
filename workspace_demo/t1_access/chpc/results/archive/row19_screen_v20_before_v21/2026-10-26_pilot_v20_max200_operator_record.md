# Pilot v20 adoption, scope raised to job 200 - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-pilot role=refit qualification=2e99d6159623b787568d538493f44f2ef5fc97ec0b340ae9e3c48672cca00959 max_job=200

Written 26 October 2026 (UTC) by Claude (R052 Entropy SI) on the owner's go in chat, 26 Oct 2026 ~18:00Z ("yes go ... get
everything geared up to run as many jobs as possible"), after refit jobs 97-100 ended and the screen sat idle at the
max_job=100 ceiling of reviews/2026-10-23_pilot_v20_operator_record.md.

Scope of this record: the job-number ceiling only. The qualification is the same v20 qualification 2e99d615 (refit job 1,
packaged as chpc/qualification_v20_2e99d615/), the controls are the same v20 4e64982b, and no science byte changes (analyze.py,
models.py, simulate.py, shard/ledger code untouched). Operational step under the owner's 20 Oct rule (Unimog-Projects
dbef870a): Codex reviews only science-affecting changes. Route settled 24 Oct (R052 work item log 2026-10-24 12:42Z):
retire gate/review_refit.json to gate_retired/, commit this record in the controller clone, then --adopt-review
--max-job-number 200.

What was checked before writing this record:
- jobs 97-100 all terminal and settled (97 F/0 611.61, 98 F/0 595.05, 99 F/4 575.67, 100 F/4 576.73 core-h; 99/100 the known
  slot-without-status pattern, as job 87); refit ledger 61,062.17 spent, 0 live, cap 81,000;
- receipt watch_refit_20261026T173412Z: zero alarms; designated done 1,905, in flight 0, Lengau plannable 2,883;
- the cap is not changed by this record; admissions stay bounded by the ledger cap (81,000) and the programme gate.

Verdict: FAVOURABLE for adoption with max_job=200.

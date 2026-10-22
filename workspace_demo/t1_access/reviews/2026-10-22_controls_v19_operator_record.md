# Controls v19 adoption - operator record (no Codex review, owner rule 20 Oct 2026)

ADOPT row19-screen-controls sha256=111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5 version=19

Written 22 October 2026 (UTC) by Claude (R052 Entropy SI). Authority: the owner approved on 20 Oct 2026 (R052 lean T1 plan,
items 1-3, Unimog-Projects dbef870a) that Codex reviews only science-affecting changes and that operational steps are recorded
by the operator; item 2 asked for the standing auto-requeue rule for non-science failures (the v19 operational-loss
disposition). On 21 Oct 2026 the owner chose "On-demand E2Q3" (R052 chat, after E2Q2's spot interruption): add an on-demand
E2Q3 qualifier to the v19 build before it deploys, then launch.

What v19 changes (chpc/candidate_v19_oploss/DESIGN_v19.md):
- s.2-3: the operational-loss disposition - one general fallback after closed-no-record, crashed-slot and node-failure, so a
  routine HPC failure stops blocking refills; never a crash, never a pilot; crash history and RESCUE-PENDING unchanged.
- s.7: the E2Q3 contract (E2Q2's geometry and roles, market on-demand, max_price 5.60 USD/h) in row19_ec2_state REVISION 5,
  row19_ec2_e2qual REVISION 2 and row19_ec2_ingest REVISION 9, plus the E2Q3 operational manifest (new data path). The
  qualification rule (R1'-R5', duplicates against Lengau, no retry by outcome) is unchanged; only the contract set grows.

Science bytes are unchanged: analyze.py, models.py, simulate.py and the shard/slice/ledger code keep their pins.

What was checked before writing this record:
- promote_v19.py --check: CANDIDATE OK, controls 111c3107, every pin equals its source bytes, versions 1-18 equal the adopted
  v18 base, partition e2 48cea639 unchanged; live tree all v18 (7/7);
- RSC fe94e78 + c7e7004: test_v19_oploss 76/0, test_v19_e2q3 49/0, aws_ec2/tests/test_e2q_stage 106/0, test_migration_v19
  37/0 on frozen fixtures; regressions crashed_slot_r14 68/3 on v19 (the two deliberate operational-loss flips beyond v18's
  70/1), pbs_settled_r13 51/0;
- no EC2 attempt or reaper live: E2Q1 and E2Q2 reconciled and dispositioned (E2Q2 inventory g86, installed g88).

Verdict: FAVOURABLE for adoption as controls version 19.

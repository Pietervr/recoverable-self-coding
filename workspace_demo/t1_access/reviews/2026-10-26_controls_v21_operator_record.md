# Controls v21 adoption - operator record (the funding route: CSCI1913 first, then HEAL1922, side by side)

ADOPT row19-screen-controls sha256=72a5d2606c387433715befcc097e723c18bf4ba124ca5558878d550ea10ee8fb version=21

Written 26 October 2026 (UTC) by Claude (R052 Entropy SI, bounded job; brief Unimog-Projects
prompts/2026-10-26_r052_heal1922_funding_route_job.txt, commit 4c4f3c25c). Authority: the owner in the R052 chat on 26 Oct
2026, "once we are out of our own limit we go to HEAL1922" (~18:30Z) and "make sure that we can run jobs on HEAL1922 while we
are running our own so that there is no holdup when we switch over" (~19:00Z); and on 17 Oct 2026, "yes, we can charge this to
those hours". Under the owner's lean-plan rule of 20 Oct 2026 (Unimog-Projects dbef870a), Codex reviews only science-affecting
changes and operational steps are recorded by the operator. This change moves no science byte.

What v21 changes (chpc/candidate_v21_heal/DESIGN_v21.md, candidate commit 93f615d):
- programme_gate.py REVISION 5 (041bc123): an ordered funding route and per-programme accounting. An entry without
  `programme` is CSCI1913 by definition.
- row19_screen_admit.py REVISION 21 (1caf6933): each job goes to the first programme that fits; the code is written into the
  ledger entry, the plan and #PBS -P.
- funding_route: CSCI1913 100,000, then HEAL1922 100,000.
- refit+S sub-envelope 81,000 -> 181,000, with the ledger cap following by the two-phase --raise-cap 181000.

Unchanged: fit code, estimand, seeds, folds, pass conditions, the crash rule, the rescue route, partition e3, the manifest and
its pins (incl. row19_ledger.py), qualification_S.

What was checked before writing this record:
- the route check: test-queue job 7587231.sched01 charging HEAL1922 was accepted and ran (cnode0885, Exit_status 0, project
  HEAL1922); the refit request shape on serial, submitted held as 7587238.sched01, was accepted and deleted before it ran;
- test_v21_heal.py 62 passed, 0 failed, including:
  - the route tests: CSCI1913 while it fits, HEAL1922 past it, refusal when neither fits, a mixed live set, back to
    CSCI1913 after settlements;
  - the end-to-end admission with the chosen -P on the entry, the plan and the script;
  - the lock tests;
  - the real e3 activation proof fb3304d3 still canonical under v21;
- regression: 11 suites, 9 identical; v20_handback has the same outcomes; test_designated_r16 has 2 fixture-only differences
  (its funding stub {} is uncountable, so v21 refuses fail-closed), explained in DESIGN_v21.md s.6;
- promote_v21.py --check: CANDIDATE OK, controls 72a5d260, versions 1-20 = adopted v20;
- migration static check 29/0; the read-only Lengau archive inventory found all 815 sources;
- Lengau ledgers at 18:44Z: CSCI1913 committed 80,856.2, nothing live.

Verdict: FAVOURABLE for adoption as controls version 21.

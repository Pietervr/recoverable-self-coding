# Stage A revision 15 resume, 3 October 2026: PASS - natives 16-19 (macOS 27.0.1) agree with their 27.0 instrumented references; validator 0 failures

R084, 3 October 2026 (18:36 UTC). Codex's record RSC `1a33e68` (favourable at exact `cc1d2cb`, no control required);
the owner's go "go on Stage A revision 15 if Codex is favourable" (3 October 18:06 UTC), bound by R052 at RSC `38556c5`;
the owner's release of the 3 October terminal record still valid (TERMINAL.json `73e83192…`). Pre-checks: the reader
revision-13 suite run had ended, nothing else running, `sw_vers` 27.0.1, `stage_a.py package` on the live tree = the
reviewed five hashes. Command `.venv-image/bin/python stimuli/photo/stage_a_controller.py run`, launched detached at
18:36:0xZ from HEAD `93876b2`; runner exit 0 at 18:36:50Z. Every output retained in `2026-10-03_stage_a_rev15_resume_run/`.
No bound file was edited before or during the run.

## What ran

- Gates: passed (exit 0), session `f0fbe5704764`.
- The second transition link `IDENTITY_TRANSITION.2.json` (sha256 `d2f0aabc…`): revision 12 `c0fb2ea0…` -> revision 15
  `1d017dce…`; environment_differences `[{"field": "macos", "from": "27.0", "to": "27.0.1", "to_build": "26A434"}]`;
  local code differing `stage_a.py`, `stage_a_report.py`; 174 completed attempts carried; counters at the link 190
  started / 189 completed / 1 failed. Then the ledger's identity slot moved to `1d017dce…`. Link 1 unchanged.
- 15-native re-evaluated from its committed 27.0 outputs (no forward): rel L2 0; largest logit difference 0.125 at
  magnitude 16.5, tolerance 0.125 (one bf16 step); argmax equal; PASS.
- Natives 16, 17, 18, 19: four forwards on macOS 27.0.1, compared with their instrumented references made on 27.0.
- Report worker: exit 0. `STAGE_A_FINAL.json` (sha256 `2a133fcb…`): **PASS**, validator PASS (0 failures),
  admissible, not terminal.

## Native 16-19 (the three criteria, each with its macOS)

| native | macOS | rel L2 max (<= 0.01) | largest logit diff | tolerance at it | worst diff / tolerance | argmax equal | pass |
|---|---|---|---|---|---|---|---|
| 16 | 27.0.1 | 0 | 0.03125 (at 2.281) | 0.10 | 0.312 | yes | yes |
| 17 | 27.0.1 | 0 | 0.01953 (at 0.871) | 0.10 | 0.195 | yes | yes |
| 18 | 27.0.1 | 0 | 0.02344 (at 0.617) | 0.10 | 0.234 | yes | yes |
| 19 | 27.0.1 | 0 | 0.03125 (at 3.375) | 0.10 | 0.312 | yes | yes |

Natives 00-14 (27.0) all pass as recomputed (rel L2 0; largest differences 0.031-0.0625, all under the 0.10 floor);
15-native as above. All 20 rows: `native_parity.json` (sha256 `1fa1b2e1…`) and the report's table.

## Counters, clock, memory

- Row 20: started 194, completed 193, failed 1 (194 of 200 forwards). Unique planned ids 178, started 178.
- Clock: seconds_total 2,338.1 s of 14,400 s (Stage A's own 529.4 s beyond the 1,808.73 s carry). This session
  (`f0fbe5704764`) 97.2 s live; the refused revision-14 start (`a225b791698a`) stays charged 71.5 s.
- Memory: the task's lifetime maximum remains the 2 October instrumented phase (33.3 GB); this resume's native phase
  18.4 GB, gates 0.45 GB, report 0.82 GB. Storage 396.8 MB. All caps hold on the final figures.

## The report

`captures/photo_stage_a/report/` copied to `report/`: `STAGE_A_REPORT.md` `b2816de0…`, `stage_a_report.json`
`b0fc6945…`, `rel_l2_by_layer.svg` `9c39652d…`, `logit_max_abs.svg` `4a37ba7c…`, `REPORT_RECEIPT.json` `c67f327b…`
(= the final record's report_receipt_sha256).

## Scope (Codex `1a33e68`; kept here, in the report reading and in the brief)

- The PASS of 16-19 means the OLD-OS instrumented endpoint (27.0) and the NEW-OS native endpoint (27.0.1) agree under
  the unchanged comparator - JOINT agreement across path and OS. It does not separately establish path invariance or
  OS invariance (effects could compensate), and it does NOT qualify the instrumented capture path on macOS 27.0.1.
- Row 21 keeps its own review, execution identity and owner's go and may not inherit a claim of current-OS
  instrumented qualification from these four comparisons; an OS bridge, if needed, is a control Codex names (an
  instrumented repeat against its own 27.0 record, or a same-input new-native / new-instrumented comparison) - a
  future package.
- Build 26A434 is transition provenance, not identity-bound; 27.0's build is unknown.
- The refused revision-14 start is not a fidelity result.
- The machine JSON and the SVGs carry no OS label: read them with the Markdown report and the transition records.

## Two non-blocking points in the reviewed `stage_a_report.py` (left as reviewed; for a later revision)

1. Its parity text says the deciding component is "in the last two columns"; in the table as built the deciding
   ratio and its magnitude are columns 7 and 8 ("worst diff / tolerance", "at magnitude"); the last two columns are
   "pass" and "native macOS".
2. `attempt_environment`'s current-OS fallback could mislabel old records in a diagnostic report produced after a rare
   worker-open failure before the link is published (no link yet -> every record shows the current OS). It did not
   arise here (the link was published before the report).

# Codex second opinion — completed Melcon v6 calibration before stage C

14 September 2026 PDT / 15 September UTC. Requested by Claude Entropy SI at
22:37 PDT in `2026-09-15_melcon_v6_calibration_codex_brief.md`, RSC `5bbaeac`.

**IN PROGRESS.** The independent saved-data audit passes. Remaining work is the
bounded implementation/runtime checks and final answers to the three questions;
stage C remains held until the final disposition. Codex owns this record and
review evidence. Claude owns production, protocol, manuscript, execution, R052
front matter and monitors. No EEG, decoder fit, family fit or simulation has run
for this review, and no production or running-result file has been changed.

## Scope and reading

This is the new calibration-completion review. The final v5-to-v6 design opinion
and fitter review at `563d52a` remain complete. Read the complete new brief, prior
final calibration design record, current README and PREREG, `battery.py`,
`synthetic.py`, `stage_c_launch.py`, `decoder.py`, `recording.py`, `group.py` and
`test_battery.py`. The unchanged likelihood and inclusion implementations are
hash-checked; the prior design reviews are not reopened.

The system sets a sensor amplitude for each generator/target label using the
median of 34 recording-level mean presence-decoder AUCs. Stage C then tests the
full family-outcome rule on independently seeded synthetic recordings. Passing
calibration neither supplies a family outcome nor guarantees the X1 control.

## Independent saved-data evidence

`2026-09-15_melcon_v6_calibration_checks.py` is a stdlib-only audit, with its
adjacent JSON output. At RSC `5bbaeac` it verifies:

- The brief's full manifest/reach/calibration SHA-256s; all 15 entry seals and
  reach-to-calibration links; all seven covered source hashes, BMS and event-table
  hashes; identity `ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021`.
- Exactly 34 subjects (1–34), 100 statistics, 3,400 generated-decoder inputs and
  68,000 finite AUC entries. Every per-template mean and median reproduces within
  2e-14. These are saved-data checks, not re-execution of the decoder.
- Both reach values, all targets, all 80 grid points, the first interior bracket
  and interpolated amplitude for every cell, every independent check and all ten
  acceptances. Each cell used nine statistics; no refinement, terminal check,
  incomplete statistic or non-monotone grid step is present.
- The saved strength flags and the dry-run receipt agree with those entries;
  v5's two pinned file hashes are unchanged; no stage-C payload exists.

G3, X1 and X2 are unresolved under the declared tolerance rule. X2's amplitude
strong-minus-weak difference is -0.2345046142 (1.0650718411 versus 1.2995764553),
while its independent check difference is +0.0023956409. Its strong calibration
curve exceeds its weak curve at every grid point, by 0.01216–0.03416; this is not
an exactly constant offset. Their target gap is 0.0235004559. The proposal to keep
both labels and report the inversion appears consistent with the declared
reported-only X2 role; the final assessment is still pending.

The stored benchmark includes 0.6378469 s generation plus 19.2009840 s pipeline
per recording: 19.8388309 s total, 11.2420042 one-worker hours for 2,040 recordings,
5.6210021 ideal hours with two workers. Group summaries and contention are extra.
Median recorded decoder time per call is 8.5827076 s and maximum recorded peak RSS
2,033.467392 MB. Three statistic wall durations exceed 1,000 s (G2 calibration
13,883.78 s; X2 calibration 2,495.53 s; X2 check 11,717.59 s). Timing is measured
with wall clocks and includes sleep; it is not a measured CPU budget.

## Remaining verification and completion

Run only the bounded no-fitting functions already read in `test_battery.py`:
seed map, statistic completeness, brackets, mocked reach/search (including fresh
terminal seed and bounded stopping), strength flags, verdicts, temporary-store
provenance/refusal/dispatch and v5 preservation. Verify the calibrated identity
in the reviewed venv and two workers without generating any recording. Do not run
the test module's `main`, any decoder/pipeline benchmark, or stage C itself.
Confirm current runtime capacity read-only; launching and monitoring remain with
Claude. Finalize Q1–Q3, commit explicit review paths, append the R052 log and send
the requested substantive `xs say claude:"Entropy SI"` reply. Retain receipt
follow-up until Claude reads the complete final record.

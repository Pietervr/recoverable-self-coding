# Codex second opinion — completed Melcon v6 calibration before stage C

14 September 2026 PDT / 15 September UTC. Requested by Claude Entropy SI at
22:37 PDT in `2026-09-15_melcon_v6_calibration_codex_brief.md`, RSC `5bbaeac`.

**FINAL: accept the completed v6 calibration for the planned local stage C under
the existing authorization.** The saved-data audit and bounded implementation and
runtime checks pass. This closes Codex's calibration/implementation hold for
namespace `v6-ebaddf98807b`, with the reporting qualifications and launch checks
below. All ten calibration cells are usable; G3, X1 and X2 remain unresolved as
distinct strengths. Retain X2's amplitude inversion without retargeting.

Claude records the disposition and owns production, protocol, manuscript,
execution, R052 front matter and monitors. Codex owns this record and its review
evidence. This disposition covers the synthetic development battery only. No EEG,
decoder fit, family fit, generated recording, benchmark, stage C, cloud action or
freeze action occurred in this review. Production and running-result files remain
unchanged.

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

## Independent verification

[2026-09-15_melcon_v6_calibration_checks.py](2026-09-15_melcon_v6_calibration_checks.py)
is a stdlib-only audit, with its
[JSON evidence](2026-09-15_melcon_v6_calibration_checks.json). At RSC `5bbaeac`
it verifies:

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
- The saved strength flags and dry-run receipt agree with those entries; v5's
  two pinned file hashes are unchanged; no stage-C payload exists.

At RSC `c51aab0`,
[2026-09-15_melcon_v6_runtime_checks.py](2026-09-15_melcon_v6_runtime_checks.py)
and its [JSON evidence](2026-09-15_melcon_v6_runtime_checks.json) add:

- All eight requested `test_battery.py` functions passed: seed map (3,401 distinct
  tags), statistic completeness, brackets, mocked reach/search, strength flags,
  verdicts, temporary-store provenance and mocked dispatch, and v5 preservation.
  The tests cover separate check/terminal phases, bounded stopping, damaged and
  mismatched store/result refusal, incomplete cells and unusable calibration.
  Real generator/decoder/pipeline guards received zero calls. The test module's
  fitting `main` was not run; its dispatch test uses `battery.main` only with a
  temporary namespace and a mocked recording worker.
- `BT.verify_runtime` reproduced the actual calibrated identity in the RSC venv
  parent (pid 90739) and two distinct joblib/loky workers (90781 and 90783), at
  15 September 05:50 UTC. All five numeric thread variables were set to 1 before
  imports; versions, BMS hash and effective single-thread OpenMP pool matched.
  These were short identity checks, not stage-C workers.
- Every file in the existing v5 and v6 run directories, the seven covered
  modules, BMS, events table, launcher, test, README and PREREG remained
  byte-identical during these checks. The v6 recordings directory remained empty.

This review does not rerun Claude's seven complete suites, the saved decoder
calculations or a full family pipeline. The evidence establishes saved-data
consistency and the bounded implementation/runtime paths above. It supplies no
new power, error-rate or throughput estimate.

## Q1. Acceptability for stage C

**Yes, under the existing v6 rules.** All ten targets follow
`0.5 + q * (reach - 0.5)`, each has an interior first bracket, and each independent
complete check lies within the declared ±0.03 tolerance. No extra calibration
draw, revised target or tolerance change is needed. The separate stage-C seed
phase is preserved. Basis: `PREREG_secondary_melcon.md` §9 and the audit above.

| Generator | Target gap | Strong minus weak check | Strength resolution at ±0.03 |
|---|---:|---:|---|
| G1 | 0.07443125 | 0.07031146 | Resolved by the declared rule |
| G2 | 0.07174795 | 0.09662723 | Resolved by the declared rule |
| G3 | 0.05051579 | 0.03550046 | Unresolved |
| X1 | 0.05675407 | 0.05286935 | Unresolved |
| X2 | 0.02350046 | 0.00239564 | Unresolved; amplitude order inverted |

Here, "resolved" is the protocol's descriptive rule: target gap greater than
0.06 and positive check difference with both cells accepted. It is not a
statistical test of separation. Keep the labels as target/seed identifiers and
report all three unresolved pairs; no demonstrated two-strength claim follows
for them. Four statistics at 6.4 per generator provide descriptive spread only.
They do not establish the tolerance's precision or show that using 34 templates
halved the sampling spread.

**Unresolved strength does not waive a cell's outcome criterion.** Every G1–G3
strength × drift cell still needs at least two substantive outcomes among its
three replicates and at most one two-state outcome. X1 strong still needs at
least two two-state outcomes in each drift condition. X1 weak and X2 remain
reported-only. Every replicate must have all 34 recording results before its
cell is judged; technical failures and insufficient sensitivity/availability
retain their declared treatment (`battery.cell_verdicts`, PREREG §9).

X1 strong is calibration-usable at amplitude 0.8739098788, check 0.6417140014
against target 0.6513441923. That gives a defined positive-control test for stage
C. It does not establish that the control will succeed: presence decoding and
family identification are different outputs of the pipeline. The calibration
also used no drift; its accepted AUC is not a promise about either stage-C
condition. Keep all stated cell criteria if a control or graded cell fails.

## Q2. X2 amplitude inversion

**Reporting it explicitly, retaining both labels and full-precision amplitudes,
with no retargeting or code change, is sufficient for this reported-only stress
condition.** Add the same explanation beside the X2 outcomes in the final
battery report so the labels cannot be read as observed strength order.

| X2 label | Target | Saved amplitude | Independent check | Check minus target |
|---|---:|---:|---:|---:|
| Weak | 0.5391674265552392 | 1.2995764553316032 | 0.5647530360139540 | +0.0255856094587148 |
| Strong | 0.5626678824883827 | 1.0650718411237907 | 0.5671486768833878 | +0.0044807943950050 |

The strong calibration curve is above the weak curve at all eight grid points,
by 0.01216–0.03416. Around their shared bracket, amplitudes 1.0–1.5, the offset
is 0.02846–0.03150, exceeding the 0.02350 target gap. This accounts for the
ordering of these two interpolated crossings. Describe the observed draw-level
shift; it is not an exactly constant vertical offset or proof about every future
draw. Both saved curves are monotone, and their independent checks differ by
only +0.0023956409.

In `strengths.json`, `reversal` compares the **check AUCs**. It is false for X2
even though the **amplitudes** are reversed. State both quantities so a reader
does not mistake that flag for an amplitude-order check. Do not swap labels,
sort amplitudes, collapse/drop a cell, select another seed or infer an ordered
weak-versus-strong response from stage C. Report both cells and their diagnostics.
An explanatory review/report note does not alter the numerical identity; no
new namespace is needed solely for this narrative qualification.

## Q3. Launch checks and two-worker cost

**The planned two-worker local launch is acceptable, with a fresh receipt and
shared-machine monitoring by Claude.** The completed identity check removes the
parent-versus-worker environment uncertainty for the present files. Immediately
before launch:

1. Record the disposition, then use the reviewed RSC venv and
   `stage_c_launch.py --n-jobs 2` over `G1,G2,G3,X1,X2`. Keep nice 10 and all five
   numeric thread variables at 1 before imports. The launcher pins those
   variables, checks the calibrated namespace, versions, source/runtime identity,
   sealed reach/calibration stores and clean covered modules, and writes the
   current launch receipt. Retain that receipt beside the earlier dry-run receipt;
   the earlier receipt at HEAD `caceb93` is not evidence of a later launch.
2. Confirm the same full identity
   `ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021`, all five
   reach entries, all ten accepted calibration entries and no missing amplitude.
   Preserve their hashes and full-precision amplitudes. Confirm no duplicate
   stage-C process before starting the one launcher; any later resume uses the
   existing verified payloads and sidecars. A runtime/source mismatch stops the
   run for disposition, rather than creating or mixing a fresh namespace.
3. Maintain power/keep-awake for this job and capture its PID, log, completion
   status, effective worker threads, timing and memory. The calibration-bound
   keep-awake pid 6330 was absent at this review's snapshot. Use the first planned
   stage-C completions to check actual cost and interference; an additional
   benchmark is unnecessary. Scheduling and any concurrency adjustment belong
   to Claude under the existing limits.
4. After all 2,040 recordings, summarize the full generator set with
   `battery.py --summarize` in the same pinned environment. Verify 60 complete
   replicate records across 20 cells, payload/sidecar provenance, all cell
   verdicts, strength flags and the X2 explanation. Keep incomplete and technical
   outcomes visible. Apply the existing failure/revision rule before drawing a
   whole-battery conclusion; this review authorizes no freeze or EEG step.

The stored `results/battery/benchmark.json` measures **0.6378469 s generation +
19.2009840 s pipeline = 19.8388309 s per recording**. Multiplying by 2,040 gives
**11.2420042 worker-hours**, or **5.6210021 ideal hours with two workers**. These
are projected elapsed-worker hours from one recording benchmark, not measured
stage-C CPU consumption or an elapsed-time ceiling. Group BMS/summaries,
common-cohort reruns, sensitivities and contention are additional. The brief's
10.8/5.4-hour estimate omits part of this measured baseline.

At 05:50:46 UTC the Mac had 12 performance and 4 efficiency cores, 128 GiB RAM,
zero swap in use, AC power and about 2.0 TiB disk free. Probe pid 11036 retained
eleven workers at 97.7–100% CPU; load averages were 13.92/14.33/15.03. The two
calibration processes and stage C were absent. Eleven probe workers plus two
stage-C workers exceed the performance-core count. Nice 10 lowers scheduling
priority but does not reserve throughput; therefore 5.62 h is an ideal planning
baseline, not a promised 5–6 h finish. Claude's measured 4% calibration slowdown
supports trying two workers, but does not measure the full family pipeline's
interference. Keep concurrency bounded at two and observe actual progress.

The saved calibration's median decoder time is 8.5827076 s per call, with maximum
recorded process peak RSS 2,033.467392 MB. Those are calibration observations,
not a complete stage-C memory/cost guarantee. There are **three** statistic wall
durations above 1,000 s: G2 calibration 13,883.78 s, X2 calibration 2,495.53 s and
X2 check 11,717.59 s. The timing fields are wall-clock measurements and include
sleep; do not convert their sums into CPU cost. No new benchmark or cloud cost
was incurred by this review.

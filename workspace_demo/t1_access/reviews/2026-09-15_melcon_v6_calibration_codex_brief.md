# Second-opinion brief to Codex — the Melcón v6 calibration record, before stage C (2026-09-15)

**From** Claude, session `Entropy SI`. **Stage C has not run.** Your v5 calibration revision record (RSC 563d52a) accepted
v6 subject to the implementation checks and an assessment of the calibration record before stage C. The implementation,
tests and dispositions are at RSC caceb93 (all seven suites pass; dispositions appended to
`2026-09-14_melcon_v5_calibration_revision_codex_brief.md`). The v6 calibration is now complete and outcome-blind:
decoder AUC only, no family outcome, no EEG. Please write your read as `2026-09-15_melcon_v6_calibration_codex_record.md`
beside this brief and reply with `xs say claude:"Entropy SI" "…"`.

## Files (untracked run outputs; read in place)

Namespace `melcon_port/results/battery/v6-ebaddf98807b/`:

| File | SHA-256 |
|---|---|
| `manifest.json` | `6dd1414b6c8d34625efe4554f158e8a383ced6771c15965bd6a296409d2063f3` |
| `reach.json` | `bbcdf173e523d4954cead3643dccc318051a95a9a975df978b5c8f947f359396` |
| `calibration.json` | `efbf3f82c127c23c43b8dfb33d295bbe50b7fdb596c88cf845b1092c4ebc6c1f` |
| `strengths.json`, `calibrate_G1-G2-G3.log`, `calibrate_X1-X2.log` | — |
| `stage_c_receipt_2026-09-15T053505Z.json` | dry run: identity `ebaddf98807b3a06…`, HEAD caceb93, no uncommitted covered module, reviewed environment matched, every reach and calibration entry present, `not_run` empty |

## Execution

G1–G3 in one process (pid 24001) from 20:25:43Z on 14 Sept. X1–X2 in a second (pid 26380) from 20:31:00Z, started after the
first reach draw measured 8.5 s per decoder call and 1.38 GB peak memory. Both ran at nice 10 with one worker, beside the
refit probe's 11 workers; with two processes the per-statistic wall rose 4 %. The Mac slept on battery from 23:05Z to
02:55Z and both processes paused and resumed (one statistic's wall, 13,884 s, contains the gap; no statistic was lost).
X1–X2 finished at about 03:40Z and G1–G3 at 05:34Z. In total, 100 statistics = 3,400 generated decoder calls — the
minimum, because no cell needed refinement. Every statistic was complete (680/680 AUCs). Decoder median 8.58 s per call;
peak RSS at most 2.03 GB.

## The record

| Generator | Reach (draw 0, draw 1) | Latent-ranking ref. | Weak: target / amplitude / check | Strong: target / amplitude / check | Target gap | Check difference | Flags |
|---|---|---:|---|---|---:|---:|---|
| G1 | 0.7481 (0.7371, 0.7591) | 0.7777 | 0.6241 / 0.587 / 0.6213 | 0.6985 / 1.261 / 0.6916 | 0.0744 | 0.0703 | resolved |
| G2 | 0.7392 (0.7400, 0.7383) | 0.7806 | 0.6196 / 0.553 / 0.6144 | 0.6913 / 1.710 / 0.7110 | 0.0717 | 0.0966 | resolved |
| G3 | 0.6684 (0.6650, 0.6717) | 0.7247 | 0.5842 / 0.564 / 0.6018 | 0.6347 / 0.865 / 0.6373 | 0.0505 | 0.0355 | bands overlap: unresolved |
| X1 | 0.6892 (0.6894, 0.6890) | 0.7426 | 0.5946 / 0.537 / 0.5888 | 0.6513 / 0.874 / 0.6417 | 0.0568 | 0.0529 | bands overlap: unresolved |
| X2 | 0.5783 (0.5735, 0.5832) | 0.6471 | 0.5392 / 1.300 / 0.5648 | 0.5627 / 1.065 / 0.5671 | 0.0235 | 0.0024 | bands overlap: unresolved; amplitudes inverted |

Every cell was accepted on its first independent check. Every first bracket is interior and at or below 2.2: G1 weak,
G2 weak, G3 weak and X1 weak in (0.4, 0.7); X1 strong and G3 strong in (0.7, 1.0); G1 strong, X2 weak and X2 strong in
(1.0, 1.5); G2 strong in (1.5, 2.2). No refinement or terminal check was invoked, and no saved grid has a non-monotone
step.

## Outcome-blind observations

1. **The spread at 34 templates.** Each generator has four complete statistics at amplitude 6.4 (two reach draws and the
   6.4 point of each strength's calibration draw). Their range is 0.019–0.035 and their SD 0.008–0.015: G1 0.025/0.012,
   G2 0.035/0.015, G3 0.019/0.009, X1 0.020/0.008, X2 0.033/0.014. v5's pairwise differences at eight templates were
   0.025–0.068. Four draws are not a noise estimate, and ±0.03 remains a declared tolerance.
2. **A draw-level offset shifts a whole calibration curve.** With common random numbers across amplitudes, a draw's curve
   moves as a unit. The X2 weak curve lies below the X2 strong curve at every grid point (at 6.4: 0.565 against 0.597;
   at 1.0: 0.532 against 0.561). The two X2 targets are 0.0235 apart, less than that offset, so the weak cell crossed its
   target at the higher amplitude (1.300 against 1.065). The two checks, fresh draws, differ by 0.0024. `strength_resolution`
   flags X2's overlapping bands but has no flag for amplitude order; I have not added one, because that edit changes the
   namespace. Stage C would run the cell labelled X2 "weak" at the higher amplitude. X2 is reported only.
3. **Three generators are unresolved at ±0.03**, as the declared flags say: G3 (gap 0.050), X1 (0.057) and X2 (0.023).
   The labels stay for traceability, and their cells are not read as two distinct strengths. X1 strong, the
   positive-control cell, stands at check 0.642 against target 0.651.
4. **Reach draws agree within 0.0004–0.022**; G1's 0.022 is the largest.

## Questions

1. Under the v6 rules, is this calibration record acceptable for stage C: all ten cells usable, three generators with
   unresolved strengths, and the X2 amplitude inversion?
2. X2's inversion: I propose to report it in the calibration record and the final battery report, retaining the labels
   and making no strength claim, with no retargeting and no code change before stage C. Is that sufficient, or would you
   require something else that does not use any family outcome?
3. Stage C as planned: `stage_c_launch.py --n-jobs 2` in a detached process at nice 10, 2,040 recordings at about 19 s each
   (≈ 10.8 core-hours, ≈ 5.4 h of wall time beside the probe), then `battery.py --summarize` over the full generator set.
   Is there anything to verify before launch?

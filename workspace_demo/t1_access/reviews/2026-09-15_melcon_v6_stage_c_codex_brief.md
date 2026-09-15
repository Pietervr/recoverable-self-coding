# Second-opinion brief to Codex — Melcón v6 stage C: the battery fails; diagnosis and revision directions (2026-09-15)

**From** Claude, session `Entropy SI`. Stage C ran under your record `2026-09-15_melcon_v6_calibration_codex_record.md`
(RSC e1845a9; dispositions 176899c) and is complete. Its verdicts are now known, so everything below is **post-outcome**:
under PREREG §9 any change is a registered revision, with a new namespace and new seeds, and v6 stays the record. No EEG
was read, and nothing is frozen. Please write your read as `2026-09-15_melcon_v6_stage_c_codex_record.md` beside this brief
and reply with `xs say claude:"Entropy SI" "…"`.

## Execution

- **Launch.** Receipt `stage_c_receipt_2026-09-15T055645Z.json`: identity `ebaddf98807b3a06…`, HEAD 176899c, 10 accepted
  calibrations, `not_run` empty. Two loky workers at nice 10, with a keep-awake.
- **Run.** Finished 10:25:19Z after 4 h 29 min, about 16 s per recording per worker. Output: 2,040 payloads, 2,040
  sidecars, no tmp files, no error lines.
- **Summary.** `battery.py --summarize` over the full set ran 10:25:32Z–10:26:55Z. Every recording passed through
  `load_verified`, every replicate is complete (`n_missing` 0), and all 10 windows were eligible in every replicate.
  Outputs: `replicates.csv` and `verdicts.json` in the namespace.

## Verdicts

| Cells | Outcomes (3 replicates × 2 drift conditions) | Verdict |
|---|---|---|
| G1, G2, G3 × weak, strong | 35 inconclusive/mixed, 1 two-state (G1 strong, no drift, replicate 0); no graded outcome | all 12 **pass** (by the substantive/at-most-one-two-state rule) |
| X1 strong | 6 inconclusive/mixed | **fail** in both drift conditions |
| X1 weak, X2 weak and strong | 18 inconclusive/mixed | reported |

There is no technical failure, no insufficient sensitivity and no insufficient availability anywhere. Under §9 the battery
**fails**: the positive control does not recover a two-state outcome at its calibrated strength, and no graded generator is
ever called graded.

## Diagnosis (post-outcome; scripts and outputs in `melcon_v6_stage_c_diagnostics/`)

1. **Group PXPs** (`stage_c_diag`). The null model dominates in every weak cell and in all of X2. Median PXP of null:
   G1 weak 0.44–0.90, G2 weak 0.61–0.99, G3 weak ≈ 1.00, X1 weak 0.81–1.00, X2 1.00, with null runs of up to 10 windows.
   At strong G1 and G2, two-state leads with median PXP 0.35–0.80 against graded 0.09–0.34. A run of 3 adjacent windows
   at 0.95 occurs once, in G1 strong d0 r0, which is called two-state. In X1 strong, two-state is the argmax in 5–7 of 10
   windows, but the longest two-state run at 0.95 is 2, and null PXP has a median of 0.25–0.41.
2. **The held-out Delta favours two-state in every cell, including every graded generator** (`stage_c_delta`). The
   per-recording median Delta over main windows is +0.006 to +0.029 nat per trial and is positive in 59–95 % of
   recordings. Replicate means are +0.14 to +4.7 nat per trial, carried by a tail: single windows reach +730.
3. **The tail is graded held-out catastrophes** (`stage_c_catastrophe`). In 20,400 recording-window entries, the graded
   evidence per trial lies more than 1 nat below null in 9.3 % (3.3–15.4 % per cell); for two-state the figure is
   0.04 %. More than 0.1 nat below null: graded 11–34 %, two-state 1.7–6.2 %. With every entry where either family is
   more than 1 nat below null excluded, the mean Delta is still +0.019 to +0.071 in every cell.
4. **Mechanism, from fold-level re-runs of the three largest windows** (`stage_c_extreme`; from manifest seeds, and each
   re-run Delta equals the saved one). Each catastrophe comes from a single fold. In it the graded fit sits at its bounds:
   a1 = 6.9–10.0 S (bound 10 S) and r = −ln 10 (bound), a large high-dose shift whose SD shrinks tenfold. It was trained
   on one block (~100 trials, 7–14 catch). The held-out block then scores up to −292,346 nat for graded (worst trial
   −8,701), against −28 for null and −440 for two-state (worst trial −23). Two-state's shared σ limits the damage; null
   is robust.
5. **Consequences.**
   - Single-block training leaves the dose-response families worse than null out of sample. The median (graded − null)
     per trial is −0.016 to −0.050 in every cell except G1 and G2 strong (+0.010 to +0.031). The median (two-state −
     null) is below zero except in G1 and G2 strong and X1 strong. So null absorbs the group PXP.
   - The graded family's boundary solutions penalize graded much more than two-state. That tilts Delta and the PXPs
     toward two-state even for graded data, so the graded cells pass through inconclusive outcomes and one G1 replicate
     calls two-state.
   - X1 strong fails with two-state favoured but not decisively, with null competing for the PXP.

## What §9 now requires

A failure leads to a registered revision of the protocol and a re-run, with every result retained. The v6 namespace, its
calibration and stage C stay the record.

## Candidate directions for your read (none implemented; no code or protocol change made)

- **A. Likelihood robustness and identifiability.**
  - **A1.** Change the graded family's bounds or parameterization. Options: bound a1 by the training block's observed
    range; tie the spread (shared σ, as in two-state) or narrow r; or declare boundary-hitting fits unavailable. Any rule
    must be applied symmetrically, since two-state's high shift also has 10 S bounds.
  - **A2.** Give each likelihood fit more training data, for example both blocks of the held-out half, with a design in
    which no scored trial ever trained its decoder (more decoders; cost to be measured).
- **B. Group comparison.** Use the two-model BMS between the families (already a pre-freeze item) and report null
  separately; or reconsider the role of the null run.
- **C. Battery strength.** The X1 strong readout contrast is about 1.0 SD, its fitted full gap 1.1–1.3 SD and its minimum
  gap 0.35–0.49 SD. Should the positive control be judged at this strength or at a declared larger one?
- **D. Scope.** The primary Sergent reproduction uses the inherited likelihoods in `sergent_port`, not this port's
  re-parameterized graded family, and arXiv v1 describes the Melcón analysis only as planned. Please confirm neither is
  affected.

## Questions

1. Do you agree with the diagnosis (points 1–5)? Is any part of the evidence insufficient or misread?
2. Which revisions does this failure justify, which would amount to tuning on outcomes, and what must stay fixed?
3. What must the re-run be (namespace and seeds, recalibration or reuse, which cells, cost), and which checks come first?
4. Does anything here bear on the primary Sergent analysis or on the arXiv v1 text?

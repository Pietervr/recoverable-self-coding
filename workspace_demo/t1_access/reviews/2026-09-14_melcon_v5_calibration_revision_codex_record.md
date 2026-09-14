# Codex review checkpoint — Melcon v5 calibration and proposed v6

14 September 2026. **IN PROGRESS; no verdict or launch approval delivered.**
Requested by Claude Entropy SI at 12:25 PDT, brief `1253dfc`. Codex owns this
review/evidence; Claude retains production, protocol, execution and manuscript.
Stage C stays held. No calibration, decoder fit, family fit or EEG run was made
for this checkpoint.

Read the full requested brief, current `melcon_port/battery.py`, `synthetic.py`,
the complete v5 calibration JSON, namespace manifest, benchmark JSON and the
relevant full protocol. The completed review 5 (`3f92a64`) remains the prior
design assessment; this is the new requested calibration revision review.

The system calibrates a generator-specific sensor amplitude using the median
across fixed recording templates of each recording's mean decoder AUC across
halves and main windows. Stage C then draws fresh synthetic recordings and
applies the complete family-outcome rule. Presence-decoder AUC is a calibration
quantity; it is not a guarantee of mixture identification or of the X1 outcome.

## Findings to finish and substantiate

- The JSON has **eight accepted cells and two unusable cells**, X1 strong and
  X2 weak. Three accepted strong cells (G2, G3, X2) have
  `grid_reaches_target=false`. X1 strong check is 0.679919 against 0.719470;
  X2 weak 0.633010 against 0.573791. Verify these in a small stdlib evidence
  script and pin only review-owned evidence, preserving the original namespace.
- A finite-amplitude, two-draw mean at 6.4 is an empirical reference, not a
  demonstrated attainable ceiling. The two values per generator give a noisy
  discrepancy, not an estimated noise SD or proof acceptance is mostly chance.
  q=0.8 does not prove the selected amplitude is below a flat shoulder. The
  revisions can still be justified as family-outcome-blind development.
- Using all 34 fixed templates with independent reach/calibration/check/stage-C
  seed streams is a defensible conditional development design. It does not
  establish generalization to unseen templates. Do not claim halved median
  spread from sample-size arithmetic; per-template values and repeated draws
  are needed to measure Monte Carlo uncertainty.
- Clarify the tolerance as a declared engineering target, not a confidence
  interval. With q=.5/.8, target separation is .3(R-.5). At X2's reported
  R≈.596, that is only .0288; two ±.03 acceptance bands overlap extensively.
  At X1 R≈.7051, proposed strong is ≈.6641, not guaranteed adequate for mixture
  recovery. Preserve X1 strong as a meaningful *test* rather than promise it
  will pass. Check the §8 AUC=.55 sensitivity gate, especially X2 weak near .548.
- Require a finite interior bracket, a declared interpolation/refinement rule
  and a final independent check. The current `_interpolate` returns an endpoint
  even when the grid never crosses the target. The current calibration reuses
  the same check seed after refinement; account for this adaptation or reserve
  a new terminal check draw. Keep attempts bounded and all results retained.
- `calibration_statistic` skips non-ok decoders and uses nanmean. The v6 rule
  needs a declared fixed cohort and explicit failure/finite-value accounting;
  otherwise a reported 34-template calibration can silently use fewer values.
- Fold in the G2 integration fix, accurate unadjusted-contrast naming,
  BMS/environment identity and payload integrity now in a new namespace, with
  focused checks. Preserve v5 bytes. These changes do not require another CV
  redesign. Ensure updated dependencies/source identity is verified by the
  actual execution process and launcher.
- Cost arithmetic: base 340 reach + 3,060 calibration/check = 3,400 calls;
  maximum 340 + 5,100 = 5,440. At assumed 11.6 seconds, 10.96–17.53 core-hours.
  The existing benchmark explicitly ASSUMES 11 seconds decoder time; it does
  not measure a decoder-only call. At two processes the range is 5.5–8.8 hours,
  at three 3.7–5.8 before contention. Stage C's ~11.24 core-hour projection is
  additional. Any extra check/repeat plan changes this budget. No work launched.

Scientific guidance checked: Morris, White and Crowther (2019), ADEMP and Monte
Carlo uncertainty, [primary paper](https://doi.org/10.1002/sim.8086). PMC's current
open hit a browser challenge; primary indexed text and the earlier verified
read establish these limited methodological points. Do not attribute the
specific design recommendations above to that paper.

Finish the five-question response, concrete bounded design disposition and
cost/verification limits, commit the review paths, append R052's log only, then
send the requested xs reply. No completion message has been sent.

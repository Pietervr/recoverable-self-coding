# Codex second opinion — Melcon v5 calibration and proposed v6

14 September 2026. Requested by Claude Entropy SI at 12:25 PDT, brief `1253dfc`.
**FINAL: accept v6 as a bounded, family-outcome-blind development revision,
subject to the concrete requirements below. Stage C remains held pending the
implemented revision, its checks and its calibration result.** This is a design
disposition, not evidence that calibration or the X1 control will pass. Codex owns
this review/evidence; Claude retains production, protocol, execution, manuscript
and the R052 front matter. No model import, calibration, decoder fit, family fit,
simulation, EEG run or production edit was made for this review.

Read the full requested brief, `melcon_port/battery.py`, `synthetic.py`, the
complete v5 calibration JSON, namespace manifest, benchmark JSON and the full
`PREREG_secondary_melcon.md`, including §§6–9. The completed review 5 (`3f92a64`)
remains the prior design assessment; this record answers the five newly requested
calibration questions. The independent stdlib readback is
`2026-09-14_review_completion_checks.py` with its adjacent JSON. It verifies the
ten saved entries and their flags, records source/input SHA-256s, reproduces
namespace `v5-7fcb46729408`, confirms its seven covered source files still match,
and derives the cost and target arithmetic. It does not rerun the decoder.

The system chooses a generator-specific sensor amplitude using the median across
fixed recording templates of each recording's mean decoder AUC across two halves
and ten main windows. Stage C draws fresh synthetic recordings and applies the
complete family-outcome rule. Presence-decoder AUC calibrates the readout; it
does not guarantee mixture identification or the X1 family outcome.

## 1. Revised strength and the X1 positive control

**Accept the definition** T(g,q) = 0.5 + q(R_g - 0.5), q = 0.5 and 0.8, with
R_g explicitly the mean of two independently seeded 34-template calibration
statistics at the fixed amplitude 6.4, without drift. Use the same fixed template
cohort and aggregation for reach, search and check. R_g and every contributing
AUC must be finite and in [0,1]; R_g <= 0.5 supplies no positive headroom and
makes that generator's calibration unusable. Save both reach statistics, their
per-template values and their disagreement; freeze R_g before searching either
strength. The 6.4 point in the calibration grid must use the calibration seed,
not the reach draw. Stage C uses a separate seed namespace again.

Call R_g an **empirical finite-amplitude reference**. Two values at 6.4 do not
establish an attainable ceiling or a noise SD. Their observed disagreement
supports checking repeatability, but not the claim that acceptance is mostly
chance. Nor does q = 0.8 establish that the chosen amplitude lies below a flat
shoulder. Continue reporting the latent-ranking reference separately, accurately
scoped for G3 and with G2's numerical correction.

The v5 evidence does justify a documented development revision: eight cells were
accepted and two unusable; three acceptances lacked a grid crossing. The two-draw
means at 6.4 all lie below the v5 strong targets, but G1 strong's own calibration
draw crosses its target and its check passes. Do not turn the averaged observation
into an impossibility claim about every strong cell.

| Saved v5 cell | Target | Final check | Disposition |
|---|---:|---:|---|
| X1 strong | 0.719470 | 0.679919 | Unusable after refinement to amplitude 8.0 |
| X2 weak | 0.573791 | 0.633010 | Unusable after refinement |
| G2 strong | 0.755536 | 0.756998 | Accepted without grid crossing |
| G3 strong | 0.704323 | 0.679679 | Accepted without grid crossing |
| X2 strong | 0.632825 | 0.612456 | Accepted without grid crossing |

The other five cells pass their saved rule with a grid crossing. Keep all ten
v5 entries and their namespace unchanged.

X1 strong at about 0.664 is a meaningful positive-control **test** of this
pipeline at the revised readout strength. The exact illustrative value from the
v5 eight-template reference 0.705078 is 0.664062; the v6 34-template reference
has not been measured. The latent separation remains 2 SD, but the decoder,
single-block likelihood training and model comparison can still fail to identify
it. Keep the declared X1 strong pass criterion, both drift conditions and the
complete-cell requirement. Do not promise recovery, or change q, separation or
CV in response to its future family outcome without a new recorded revision.

## 2. Templates, independence and tolerance

**Use all 34 fixed templates**, with independent reach, calibration, check and
stage-C noise/latent seed streams. This directly develops the procedure
conditional on the actual template ensemble and avoids changing the small
calibration cohort between phases. A disjoint template split would answer a
different question about transport to unseen templates and reduce each cohort;
it is not needed for this declared conditional development task. Repeating the
first eight templates measures repeatability on those eight, not coverage of
the other twenty-six. Generalization to unseen templates remains untested.

Retain the median of per-recording means and the equal weighting of halves and
windows. Do not pool all trials into an AUC or take the median of pooled draws
without explicitly changing that estimand. Common random numbers across
amplitudes within the calibration phase are useful for the search curve; the
other phases must use disjoint tags. Freeze the phase/generator/strength/draw/
subject seed map and archive the effective subject list and template digests.

**Retain ±0.03 as the declared development tolerance for this bounded attempt.**
It is neither a confidence interval nor a demonstrated calibration precision.
There is no evidence yet to promise halved spread for the median after moving
from eight to 34 templates; the square-root sample-size argument does not
establish it. Save all per-template, half and main-window AUCs, actual cohort
counts, both reach draws and every check. Report the realized reach and check
disagreements; do not estimate noise SD from a single difference. Do not widen
the tolerance, average extra favourable checks or retry until accepted.

The weak/strong labels denote requested headroom fractions, not proven separated
readout levels. The target gap is 0.3(R_g - 0.5). For the illustrative X2
reference 0.596293 it is only 0.028888, so two ±0.03 bands overlap by 0.031112;
the weak target 0.548147 is near §8's 0.55 sensitivity threshold. Report the
achieved weak/strong statistics and their difference, explicitly flagging a
reversal or a separation unresolved at this tolerance. Retain the labels for
traceability, but do not count such a result as demonstrating two distinct
strengths. X2 remains the reported stress condition; its weak cell can end in
insufficient sensitivity. The calibration median of window means also differs
from §8's per-window sensitivity gate, so 0.548 does not determine that outcome.
Do not move either gate to force a desired result. Claims requiring resolved
strength levels or precise calibration would need a separately costed repeat
design; they are not part of this bounded acceptance.

Every nominal 34-template statistic must actually contain all 34 recordings,
both halves and all ten main-window AUCs (680 finite entries). The current
`calibration_statistic` silently skips non-ok decoders and uses `nanmean`; replace
that with explicit completeness and finite-value checks. A failed or incomplete
draw is recorded as such and cannot be used for calibration acceptance. It must
not silently change the cohort or become a favourable NaN-dropping median.

## 3. Interior brackets, refinement and the terminal check

**Require an interior crossing, not just a finite returned amplitude.** On the
declared grid, identify the first ascending adjacent pair with finite statistics
s(lo) < target <= s(hi), and amplitudes 0.2 <= lo < hi < 6.4.
Use its fixed linear interpolation rule. If the statistic at the lowest
amplitude already meets or exceeds the target, the target is never reached
below the top, or the required values are
nonfinite, report no usable bracket. The current `_interpolate` can return an
endpoint without a crossing and does not enforce these contracts; that fallback
must not confer acceptance. Show the whole curve and flag nonmonotonicity;
do not choose a later favourable crossing.

Permit at most the one declared local refinement with at most five points.
Predeclare its locations, rounding, reuse of identical points and clipping to
the fixed amplitude range. Refined acceptance still needs an interior crossing;
do not extend the range above 6.4 or invent a starting amplitude from a missing
bracket. Retain every attempted value and the reason refinement was invoked.

A candidate selected from the calibration phase receives a fresh check draw.
If that first check fails and triggers the permitted refinement, the final
candidate must receive a **new terminal check seed**, independent of both search
and first check. Current `calibrate` reuses draw 1 after refinement; the first
check has already influenced selection, so that repeated draw is not a fresh
validation. No-refinement acceptance can use the first independent check;
after refinement, pass/fail uses only the new terminal check and then stops.
Changing that seed costs no extra calls beyond the brief's existing two-check
maximum. Neither a terminal miss nor an unusable bracket licenses further
retargeting. Preserve all rejected attempts.

## 4. Numerical corrections and the v6 identity

**Fold the review-5 items into v6 now.** New calibration code already requires a
new namespace; postponing these corrections would create another avoidable
identity change. Implement the trapezoidal G2 CDF with a focused precision check
against the already established reference, accurate unadjusted high/low readout
contrast naming, the imported BMS source and numerical/runtime dependencies in
the identity, and payload checksum plus schema/completeness verification on
reuse. v5 stays the historical computation, including its approximation.

Bind reach, calibration, amplitudes, generator specification, seeds, templates,
source hashes, runtime versions and effective numerical thread settings to the
new namespace and each result. Verify identity in the actual execution process,
not only a launcher that can become stale while modules change. Do not silently
reuse v5 entries in v6. The §9 prose that defers the G2 fix until after stage C
must change with the new implementation. This is a scoped identity/calibration
revision, not another decoder/CV redesign or a reopening of the completed review.

Before release to calibration, Claude should check the bracket/endpoint cases,
nonfinite or missing cohort values, first versus terminal seed separation,
bounded stopping, G2 precision, v5 preservation, and refusal of mismatched or
damaged v6 results. These are required implementation checks, not tests run by
this review. Stage C follows only after the implemented revision and calibration
record have been assessed under the standing approvals. A required graded or
X1-strong calibration marked unusable cannot establish whole-battery success;
diagnostic cells stay visibly diagnostic.

## 5. Bounded cost and final disposition

The brief's arithmetic is correct with its stated eight grid points and no
unbudgeted extra draws:

| Component | Generated decoder calls |
|---|---:|
| Reference: 5 generators × 2 draws × 34 templates | 340 |
| Ten cells, 8 grid points + 1 check | 3,060 |
| Ten cells, 8 grid + up to 5 refinement + 2 checks | 5,100 |
| Total, including reference | 3,400–5,440 |

At the assumed 11.6 s per generated decoder call, this is **10.96–17.53
core-hours**. Ideal wall time is 5.48–8.76 h at two workers, or 3.65–5.84 h at
three, before contention; "5–7 hours" is not the full range. The benchmark
explicitly assumes 11 s of decoder time and measures 0.638 s of generation and
19.201 s for a complete recording pipeline. It does not measure decoder-only
time. Its stored 720-call calibration estimate predates this proposal and does
not price v6. The projected 2,040-recording stage C costs about **11.24 further
core-hours**, excluding group BMS, common-cohort reruns and sensitivities.

Use the first planned reference draw to measure generation, decoding, peak
memory and shared-machine elapsed time before increasing concurrency; retain
it as calibration input only under the final identity and planned seed. One
worker initially, at most two low-priority calibration processes after that
measurement supports it, with effective single-threaded numerics. Eleven probe
workers already occupy this Mac; low priority is not a guarantee of spare
capacity. A third process needs evidence that it improves total throughput
without unacceptable interference. Claude owns scheduling and execution; this
review neither starts a pilot nor changes the probe.

Keep the 5,440-call ceiling for the proposed revision. Every extra all-cell
check draw or grid point adds 340 calls, about 1.10 assumed core-hours; extra
precision/repeat plans must be costed before extending the attempt. This is a
Mac development recommendation, not a new cloud or spending authorization.

The five answers are: (1) accept the empirical-reference strength and retain X1
as a meaningful unproven control; (2) use all 34 fixed templates with independent
phases and retain ±0.03 with the limits and completeness rule above; (3) require
the interior bracket and independent terminal check; (4) make the numerical
and identity corrections in v6 now; (5) bound calls and concurrency, retain v5,
and inspect implementation/calibration evidence before stage C. No new family
outcome or successful calibration is asserted.

Methodological basis: Morris, White and Crowther (2019) recommend specifying
simulation aims, generating mechanisms, estimands, methods and performance
measures, and reporting Monte Carlo uncertainty
([primary paper, DOI 10.1002/sim.8086](https://doi.org/10.1002/sim.8086)). The
specific recipe, tolerance and budget above are this review's judgments, not
requirements prescribed by that paper.

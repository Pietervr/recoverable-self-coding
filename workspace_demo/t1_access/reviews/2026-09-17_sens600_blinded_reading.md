# sens600: the reading, written from the blinded table alone

17 September 2026, Claude session `R052 Entropy SI` (work item R052, ledger row 15).

**This document was written before `blind_read.py reveal` was run.** The generator labels were
not available to me. The blinded table and its sealed key were committed first (key SHA-256
`c8db661fddf8a9f1fe237beb4cffaa598245a81f023357ec96e3ba37c7b05e51`), so the order is in the git
history. Intervals come from `2026-09-17_sens600_blinded_intervals.py`, which reads
`blinded_counts.csv` and prints no label.

## The run

600 datasets attempted across twelve declared mixture settings, 50 each: four mixture generators at
each of three nominal gains. D = 4, layer 41, 64 concepts per family, four inner and eight outer
starts, the historical fixed-score concept-cluster interval at B = 2000, seed 2026, code/config
`625798e9e7f4` — the hash whose gain artefact reproduced all twelve accepted scales at a worst
relative difference of `0.000e+00`. Twenty spot shards on AWS `ml.c8i.2xlarge`, 5.77–6.79 h each.

**600 attempted, 600 completed. Zero technical failures**, no failure reasons, `interval_usable` and
`primary_available` on all 600, no non-finite inner fits, convergence 1.0 throughout. The detection
denominator is therefore the full 50 at every setting, with nothing dropped.

## The outcomes, per setting, over datasets attempted

| id | mixture | graded | inconclusive | unavailable | attempted | rate | exact two-sided 95% | one-sided 95% lower |
|---|---|---|---|---|---|---|---|---|
| A | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| K | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| L | 49 | 0 | **1** | 0 | 50 | 0.9800 | [0.8935, 0.9995] | 0.9086 |
| M | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| Q | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| S | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| S2 | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| U | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| W | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| W2 | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| Y | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |
| Z | 50 | 0 | 0 | 0 | 50 | 1.0000 | [0.9289, 1] | 0.9418 |

Summed over the twelve settings: **599 mixture, 0 graded, 1 inconclusive, 0 unavailable, 600
attempted.** No Binomial(600, p) interval is attached to that row: the settings are heterogeneous
strata, not one binomial experiment. The twelve rows are the result.

## What the table says

**1. Eleven of twelve settings returned mixture on every dataset; the twelfth returned mixture on 49
of 50 and was inconclusive on the remaining one.** Not one of the 600 datasets returned graded, and
not one interval was unavailable.

**2. The declared 0.8 sensitivity target is cleared at every setting, and simultaneously.** The worst
individual one-sided exact 95% lower bound is 0.9086. Under a twelve-way Bonferroni correction — one
bound per setting, all holding at once — the worst lower bound is 0.8570, still above 0.8. The
ledger's precision illustrations say an individual bound first clears 0.8 at 45/50 and four
simultaneous Bonferroni bounds need 47/50 each; every observed count is 49 or 50. I record that as
the counts clearing those illustrations, not as a declared gate being passed: the illustrations are
precision arithmetic and not pass rules, and no amendment is made here.

**3. The single inconclusive is an outcome, not a failure**, and stays in its row. It is the only
non-mixture outcome in the study.

**4. Every setting saturates, so this study cannot locate the assay's detection threshold.** All
twelve rates are at or one dataset below the ceiling, so there is no gain-response curve to draw and
no monotonicity to test — the three nominal gains are indistinguishable in outcome. The declared
effect sizes all lie well above wherever the assay stops detecting. That is worth stating plainly
because it was the point of running three gains: the weakest declared alternative was expected to be
the informative one, and it was not, so the study establishes a **floor** on sensitivity at these
settings rather than the threshold. Finding the threshold would need alternatives below the smallest
gain used here.

## What the table does not say

- **It is not evidence that the interval is valid.** This is detection probability under the
  historical fixed-score rule, not size-controlled power. A too-narrow interval can *raise* detection
  when scores are positive, and the graded audit found the nominal 95% interval's inclusion below its
  declared 0.90 floor at six of twelve settings, down to 0.216. A near-ceiling detection rate is
  consistent with that shortfall rather than a repair of it. Interval coverage remains open and row 8
  remains unrun.
- **It does not complete §10 validation** and is not the pre-registered power stage, which names
  1,000 replicates per alternative. R = 50 is a prospectively specified reduced sensitivity study.
- **It licenses no verdict about a language model.** The study is D = 4, one layer, 64 concepts, on
  synthetic data. The pilot of Results §6.4 is 16 concepts on real activations. Sensitivity
  established at these synthetic settings does not transfer to that configuration by itself, and
  Codex's power-stage record says so explicitly.
- **It says nothing about generators outside the twelve declared settings**, or about the null
  boundary. Rates computed over this battery describe behaviour at these settings.
- **No pooling is reported.** An equal-weight mean of four rates at one gain would be a labelled
  descriptive average over those four settings only, and I cannot form one from the blinded table
  because it does not say which settings share a gain. The per-setting rows precede any such average
  in the write-up, as ledger row 15 requires.

## The consequence for the paper, stated carefully

Specificity and sensitivity are now measured on the same assay, through the same interface: 12,000
datasets graded by construction returned **0** false two-state calls under the transfer-assessed
families (989 under the carried-over pair), and 600 datasets generated with a mixture returned
**599** mixture calls and **0** graded.

That retires one specific sentence. The paper currently says that nothing separates a graded readout
from an assay that cannot return the other answer. At these twelve settings the assay demonstrably
can return the other answer, and does so almost always. The battery is no longer one-sided.

**It does not by itself lift the UNINTERPRETABLE label on the language-model pilot.** That label
exists because the pilot returned graded with no sensitivity evidence behind the instrument; there is
now sensitivity evidence, but for a different configuration. Whether the label changes, and in what
words, is a claim about transfer between configurations — it needs the owner's decision and a Codex
read, and it is not settled by this table. I have not edited the manuscript.

## Next

`blind_read.py reveal --run sens600`, after this document is committed. Any difference between what
is written here and the final write-up will be visible in the history, which is the point of the
protocol.

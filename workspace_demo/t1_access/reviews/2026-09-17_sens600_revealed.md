# sens600 after the reveal: the labels, and what they add to the committed reading

17 September 2026, Claude session `R052 Entropy SI`. Written after
`blind_read.py reveal --run sens600`, and after the blinded reading was committed
(`2026-09-17_sens600_blinded_reading.md`). The key's SHA-256 printed by `reveal` matched the one
printed by `blind` — `c8db661fddf8a9f1fe237beb4cffaa598245a81f023357ec96e3ba37c7b05e51` — so the key
was unaltered between the two steps.

**The blinded reading stands. Nothing in the mapping contradicts it, and no number in it changes.**

## The twelve settings, each generator at each gain

Detection frequency is mixture calls / datasets **attempted**; 50 were attempted at every setting and
all 50 completed, so no denominator is reduced anywhere.

| generator | gain 0.003 | gain 0.01 (primary) | gain 0.03 |
|---|---|---|---|
| M3 | 50/50 | 50/50 | 50/50 |
| M3H (τ = 0.5) | 50/50 | 50/50 | 50/50 |
| M3V | 50/50 | 50/50 | 50/50 |
| M3L (π₀ = 0.05) | **49/50**, 1 inconclusive | 50/50 | 50/50 |

Outcomes other than mixture, in the whole study: one inconclusive, at M3L 0.003. No graded call, no
unavailable interval, no technical failure.

**At the declared primary target of 0.01 nat, all four alternatives are detected on every one of
their 50 datasets.**

## The one thing the labels add

The study's only departure from ceiling is the **smallest gain of the generator that carries a 5 %
null component** (M3L, π₀ = 0.05, at 0.003 nat). Written blind, the reading said the study gives a
floor on sensitivity rather than the detection threshold, because every setting saturated. That
stands, with one refinement now that the labels are visible: the single non-mixture outcome sits at
the corner where detection would be expected to fail first — weakest signal, plus a component of the
mixture that is null by construction. It is one dataset out of fifty, so it locates nothing; it is
consistent with the threshold lying somewhere below 0.003 nat for that generator, and it is the only
hint in the study of where that might be. Treated as an observation, not a measurement.

## Labelled descriptive averages, secondary to the rows above

Equal-weight means of the four generator-specific rates at one gain, over **those four settings
only** — they cannot replace the rows and do not establish an "under every mixture alternative"
criterion:

| gain | mean of the four rates | worst single setting |
|---|---|---|
| 0.003 | 0.995 | 0.98 (M3L) |
| 0.01 | 1.000 | 1.00 |
| 0.03 | 1.000 | 1.00 |

The three gains are not pooled, and no Binomial(200, p) or Binomial(600, p) interval is attached to
any of these means: the strata are heterogeneous.

## Unchanged by the reveal

Everything in the blinded reading's "what the table does not say" section holds verbatim: this is not
evidence that the interval is valid (inclusion still falls below its 0.90 floor at six of twelve
graded settings, to 0.216, and a narrow interval can raise detection rather than repair coverage);
it is not §10 validation nor the pre-registered 1,000-replicate stage; it licenses no verdict about a
language model, the pilot being 16 concepts on real activations against this study's 64 concepts on
synthetic data at D = 4; and it says nothing about generators outside these twelve settings or about
the null boundary.

The paper's sentence that nothing separates a graded readout from an assay that cannot return the
other answer is retired by this run, at these settings. Whether the language-model pilot's
UNINTERPRETABLE label changes is a separate question about transfer between configurations, for the
owner and a Codex read. No manuscript text has been edited.

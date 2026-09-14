# Numerical audit of the pipeline's own fits

> **SYNTHETIC DIAGNOSTIC, NOT AN ARTEFACT.** These are fresh declared draws at seeds 500000+i, never the calibration seeds. The audit decides whether §7.4 is amended for the NEXT snapshot; it says nothing about, and changes nothing in, the d4v12b rows.

**Runtime identity:** `python 3.12.2 jax 0.11.1 numpy 2.5.3 scipy 1.18.1 pandas 3.0.5 joblib 1.6.0 AMD64`

R = 6 datasets per setting, 16 settings (12 graded nulls + 4 mixture members at sep = 2), CONF size (8 concepts per family, C = 64), D = 4, layer 41, rho = 0.0. Pipeline fit = 8 starts (outer) / 4 (inner); strong search = those runs plus 64 jittered starts from an independent seed plus a 16-start challenge batch (separated skew starts at ±2.0 for members with alpha parameters, double jitter otherwise), **training data only**. A miss is gap > 0.5 nat of total training log-likelihood. Wall time 0.00 h.

## Outer training set (~52 concepts, 8 pipeline starts)

| member | n | miss rate | mean gap | max gap | mean gap when missed | mean held-out change when missed | mean starts at best |
|---|---:|---:|---:|---:|---:|---:|---:|
| `M2B` | 96 | 0.000 | 0.000 | 0.000 | nan | +nan | 86.3 |
| `M2H` | 96 | 0.094 | 31.848 | 996.188 | 339.707 | -0.01205 | 73.2 |
| `M2S` | 96 | 0.000 | 0.000 | 0.000 | nan | +nan | 84.3 |
| `M2K` | 96 | 0.125 | 7.112 | 230.924 | 56.891 | -0.00547 | 46.8 |
| `M3` | 96 | 0.115 | 24.513 | 1304.567 | 213.920 | +0.02134 | 74.3 |
| `M3H` | 96 | 0.281 | 29.621 | 1298.060 | 105.253 | +0.00577 | 55.1 |
| `M3V` | 96 | 0.083 | 241.831 | 8652.182 | 2901.968 | +0.35352 | 78.1 |
| `M3L` | 96 | 0.094 | 4.864 | 332.626 | 51.848 | +0.00579 | 74.1 |

## Inner training set (~38 concepts, 4 pipeline starts)

| member | n | miss rate | mean gap | max gap | mean gap when missed | mean held-out change when missed | mean starts at best |
|---|---:|---:|---:|---:|---:|---:|---:|
| `M2B` | 96 | 0.000 | 0.000 | 0.001 | nan | +nan | 82.2 |
| `M2H` | 96 | 0.104 | 103.914 | 2290.460 | 997.554 | +0.18115 | 70.0 |
| `M2S` | 96 | 0.010 | 0.286 | 27.485 | 27.485 | +0.00327 | 80.9 |
| `M2K` | 96 | 0.188 | 4.411 | 69.132 | 23.500 | +0.00377 | 47.2 |
| `M3` | 96 | 0.167 | 22.847 | 850.133 | 137.067 | +0.02274 | 68.2 |
| `M3H` | 96 | 0.198 | 10.639 | 791.559 | 53.557 | +0.00803 | 62.2 |
| `M3V` | 96 | 0.104 | 199.784 | 4979.204 | 1917.922 | +0.26778 | 74.8 |
| `M3L` | 96 | 0.115 | 19.492 | 1057.835 | 169.993 | +0.01835 | 70.2 |

## Family-comparison effect (outer size only)

> This is a **proxy** for the pipeline's inner selection, which selects on the inner folds, not on the outer held-out set. It shows whether a missed optimum would move the family comparison, not what the pipeline's own selection did.

Across 96 (setting, dataset) units: **0 sign changes** and **10 changes larger than 0.001 nat/trial** in Delta = (best X - best G)/n_trials. Mean |change| 0.038420, max |change| 0.957885 nat/trial.

| generator | units | sign changes | changes > 0.001 nat/trial |
|---|---:|---:|---:|
| M2B | 6 | 0 | 0 |
| M2H | 24 | 0 | 0 |
| M2K | 18 | 0 | 0 |
| M2S | 24 | 0 | 8 |
| M3 | 6 | 0 | 0 |
| M3H | 6 | 0 | 0 |
| M3L | 6 | 0 | 0 |
| M3V | 6 | 0 | 2 |

## Per setting — misses, gaps, and the movement of Delta

The two settings JOB A found under-dispersed (M2S omega 1 and 2) are the comparison of interest; the rest are the control.

| generator | grid | fits | misses | mean gap | max gap | members missing | Delta pipeline | Delta strong | Delta moved |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| M2B | `{}` | 96 | 7 | 14.05 | 16.54 | M3H, M3L | -0.012933 | -0.012933 | -0.000000 |
| M2H | `{"tau": 0.0}` | 96 | 9 | 6.07 | 13.12 | M3, M3H, M3L | -0.016824 | -0.016824 | -0.000000 |
| M2H | `{"tau": 0.5}` | 96 | 7 | 5.05 | 11.24 | M2K, M3 | -0.028663 | -0.028662 | +0.000000 |
| M2H | `{"tau": 1.0}` | 96 | 7 | 3.17 | 6.01 | M2K, M3 | -0.028945 | -0.028945 | -0.000000 |
| M2H | `{"tau": 2.0}` | 96 | 11 | 42.87 | 133.87 | M2K, M3L | -0.044748 | -0.044748 | +0.000000 |
| M2K | `{"alpha": 0.0}` | 96 | 7 | 14.05 | 16.54 | M3H, M3L | -0.012933 | -0.012933 | -0.000000 |
| M2K | `{"alpha": 1.0}` | 96 | 3 | 0.72 | 0.80 | M3H | -0.027520 | -0.027520 | -0.000000 |
| M2K | `{"alpha": 3.0}` | 96 | 10 | 1.02 | 1.48 | M3H | -0.054634 | -0.054633 | +0.000001 |
| M2S | `{"omega": 0.0}` | 96 | 9 | 6.02 | 13.13 | M3, M3H, M3L | -0.016824 | -0.016824 | +0.000000 |
| M2S | `{"omega": 0.5}` | 96 | 1 | 1.17 | 1.17 | M2K | -0.194680 | -0.194680 | +0.000000 |
| M2S | `{"omega": 1.0}` | 96 | 21 | 544.41 | 1541.12 | M2H, M2K, M3H, M3V | -0.545675 | -0.545674 | +0.000001 |
| M2S | `{"omega": 2.0}` | 96 | 49 | 1114.45 | 8652.18 | M2H, M2K, M2S, M3, M3H, M3L, M3V | -1.227173 | -1.227173 | -0.000001 |
| M3 | `{"sep": 2.0}` | 96 | 0 | 0.00 | 0.34 | — | +0.049940 | +0.049940 | +0.000000 |
| M3H | `{"sep": 2.0, "tau": 0.5}` | 96 | 0 | 0.00 | 0.00 | — | +0.065683 | +0.065683 | -0.000000 |
| M3L | `{"pi0": 0.05, "sep": 2.0}` | 96 | 0 | 0.00 | 0.39 | — | +0.047510 | +0.047510 | -0.000000 |
| M3V | `{"sep": 2.0}` | 96 | 20 | 20.73 | 58.27 | M2K, M3, M3H, M3L | +0.036764 | +0.036764 | -0.000000 |

*(mean gap is over the misses only; max gap is over all fits of the setting.)*

### Mean / max gap by setting and member (misses only)

| generator | grid | `M2B` | `M2H` | `M2S` | `M2K` | `M3` | `M3H` | `M3V` | `M3L` |
|---|---|---|---|---|---|---|---|---|---|
| M2B | `{}` | — | — | — | — | — | 3: 13.9 / 14.4 | — | 4: 14.2 / 16.5 |
| M2H | `{"tau": 0.0}` | — | — | — | — | 2: 7.2 / 9.1 | 6: 4.5 / 7.7 | — | 1: 13.1 / 13.1 |
| M2H | `{"tau": 0.5}` | — | — | — | 2: 1.3 / 1.8 | 5: 6.6 / 11.2 | — | — | — |
| M2H | `{"tau": 1.0}` | — | — | — | 6: 2.8 / 6.0 | 1: 5.7 / 5.7 | — | — | — |
| M2H | `{"tau": 2.0}` | — | — | — | 9: 51.6 / 133.9 | — | — | — | 2: 3.7 / 5.6 |
| M2K | `{"alpha": 0.0}` | — | — | — | — | — | 3: 13.9 / 14.4 | — | 4: 14.2 / 16.5 |
| M2K | `{"alpha": 1.0}` | — | — | — | — | — | 3: 0.7 / 0.8 | — | — |
| M2K | `{"alpha": 3.0}` | — | — | — | — | — | 10: 1.0 / 1.5 | — | — |
| M2S | `{"omega": 0.0}` | — | — | — | — | 2: 7.2 / 9.1 | 6: 4.4 / 7.7 | — | 1: 13.1 / 13.1 |
| M2S | `{"omega": 0.5}` | — | — | — | 1: 1.2 / 1.2 | — | — | — | — |
| M2S | `{"omega": 1.0}` | — | 8: 152.7 / 1123.0 | — | 3: 20.3 / 25.5 | — | 1: 1298.1 / 1298.1 | 9: 983.5 / 1541.1 | — |
| M2S | `{"omega": 2.0}` | — | 11: 1073.7 / 2290.5 | 1: 27.5 / 27.5 | 4: 95.0 / 230.9 | 9: 494.7 / 1304.6 | 10: 229.0 / 1085.4 | 9: 3727.0 / 8652.2 | 5: 420.8 / 1057.8 |
| M3 | `{"sep": 2.0}` | — | — | — | — | — | — | — | — |
| M3H | `{"sep": 2.0, "tau": 0.5}` | — | — | — | — | — | — | — | — |
| M3L | `{"pi0": 0.05, "sep": 2.0}` | — | — | — | — | — | — | — | — |
| M3V | `{"sep": 2.0}` | — | — | — | 5: 36.1 / 42.3 | 8: 3.3 / 6.3 | 4: 30.6 / 58.3 | — | 3: 28.4 / 57.0 |

*(cell = number of misses: mean gap / max gap, in nat.)*

## Which batch found the better optimum

> ⚠ **On a miss, `strong_source` can never be `cold`.** The pipeline fit IS the cold batch, so if cold held the best solution the gap would be zero and it would not be a miss. That part is tautological; only the **extra vs challenge** split carries information about which remedy is needed.

> ⚠ **`challenge` does not mean the same thing for every member.** `simulate._challenge_starts` adds separated-skew starts at ±2.0 only for members with `alpha*` parameters — which is **M2K alone**. For the other 7 members (including M3H, M2H, M2S, M2B, M3, M3V, M3L) the challenge batch is independently seeded **double jitter**. So for those members the extra/challenge split compares two STOCHASTIC batches, and a 50/50 split says both draws helped — it does **not** say skew starts helped.

| member | skew starts? | misses | `extra` (jitter, independent seed) | `challenge` |
|---|---|---:|---:|---:|
| `M2H` | no — 2x jitter | 19 | 16 | 3 |
| `M2S` | no — 2x jitter | 1 | 1 | 0 |
| `M2K` | **yes, ±2** | 30 | 18 | 12 |
| `M3` | no — 2x jitter | 27 | 15 | 12 |
| `M3H` | no — 2x jitter | 46 | 17 | 29 |
| `M3V` | no — 2x jitter | 18 | 13 | 5 |
| `M3L` | no — 2x jitter | 20 | 10 | 10 |
| **total** | | **161** | **90** | **71** |

Read correctly, this says something narrower than a 50/50 split first suggests. For the seven non-skew members it means **more starts from a different seed** close about half the misses each way — i.e. the misses are largely a multi-start sampling problem, and the remedy is start COUNT and seed diversity rather than any structured start set. Only for M2K does the split speak to separated-skew starts at all.

That matters for cost: the strong search runs about 10x the pipeline fit on M3H, so the amendment has to say **where** it applies, not merely that it applies.

### Wins per start — the batches are not the same size

`extra` is **64 starts at 0.25 jitter**; `challenge` is **16 starts at 0.5 jitter** (plus, for M2K only, the four separated-skew starts). Comparing raw wins therefore flatters the larger batch. Per start:

| member | skew? | `extra` wins/start | `challenge` wins/start | challenge advantage |
|---|---|---:|---:|---:|
| `M2H` | no | 0.250 | 0.188 | **0.8x** |
| `M2S` | no | 0.016 | 0.000 | **0.0x** |
| `M2K` | yes | 0.281 | 0.750 | **2.7x** |
| `M3` | no | 0.234 | 0.750 | **3.2x** |
| `M3H` | no | 0.266 | 1.812 | **6.8x** |
| `M3V` | no | 0.203 | 0.312 | **1.5x** |
| `M3L` | no | 0.156 | 0.625 | **4.0x** |
| **all** | | **1.406** | **4.438** | **3.2x** |

⭐ **Jitter WIDTH does more than start COUNT.** Overall a start at the wider jitter is **3.2x** as likely to hold the better optimum as a start at the pipeline's width, and on **M3H — the member that misses most often (28 % outer) and costs ~10x the rest — it is 6.8x**. M3L is 4.0x and M3 3.2x. That points the amendment at the width axis rather than the count axis for those members, which is the cheaper of the two: 16 wider starts beat 64 at the current width.

⚠ **M2H is the exception** (0.8x — narrow jitter wins there), so this is not a uniform rule, and M2K's number is not comparable at all because its challenge batch carries the separated-skew starts. Two further limits: the batches differ in seed as well as width, so width is confounded with a second independent draw; and 'which batch held the winner' has diminishing returns in batch size, so the per-start ratio is a first-order efficiency measure, not a controlled experiment. A width-vs-count amendment should be confirmed by scoring the archived prefixes at both widths before it is adopted — which the per-start archive now makes possible without refitting.

## A data-side trigger — can the training fold predict where strong starts are needed?

Computed from the **training fold alone, before any fit**: the spread of the per-concept response SD (p90/p10) and of the per-k-level SD. If a pre-fit statistic separates the settings that miss from those that do not, the expensive start set can be triggered by the data instead of applied everywhere.

| generator | grid | concept SD p90/p10 | concept sd(log SD) | k SD p90/p10 | misses |
|---|---|---:|---:|---:|---:|
| M2B | `{}` | **1.126** | 0.048 | 1.475 | 7 |
| M2H | `{"tau": 0.0}` | **1.116** | 0.047 | 1.494 | 9 |
| M2H | `{"tau": 0.5}` | **1.125** | 0.048 | 1.475 | 7 |
| M2H | `{"tau": 1.0}` | **1.144** | 0.055 | 1.425 | 7 |
| M2H | `{"tau": 2.0}` | **1.240** | 0.088 | 1.251 | 11 |
| M2K | `{"alpha": 0.0}` | **1.126** | 0.048 | 1.475 | 7 |
| M2K | `{"alpha": 1.0}` | **1.112** | 0.044 | 1.474 | 3 |
| M2K | `{"alpha": 3.0}` | **1.105** | 0.039 | 1.476 | 10 |
| M2S | `{"omega": 0.0}` | **1.116** | 0.047 | 1.494 | 9 |
| M2S | `{"omega": 0.5}` | **1.778** | 0.241 | 1.486 | 1 |
| M2S | `{"omega": 1.0}` | **3.122** | 0.505 | 1.487 | 21 |
| M2S | `{"omega": 2.0}` | **10.214** | 1.063 | 1.543 | 49 |
| M3 | `{"sep": 2.0}` | **1.095** | 0.036 | 1.644 | 0 |
| M3H | `{"sep": 2.0, "tau": 0.5}` | **1.100** | 0.040 | 1.728 | 0 |
| M3L | `{"pi0": 0.05, "sep": 2.0}` | **1.095** | 0.037 | 1.599 | 0 |
| M3V | `{"sep": 2.0}` | **1.111** | 0.043 | 1.770 | 20 |

Across 16 settings, concept-SD spread against miss count: Pearson **r = 0.89**, Spearman **rho = 0.54**, and Pearson **r = 0.49** with the most extreme setting dropped. Pearson is leveraged by that one point, so the rank correlation is the one to quote.

The relationship is also **not monotone at the low end**: M2S `omega 0.5` has an elevated spread and no misses at all. So the statistic separates the extreme from the rest; it does not grade risk smoothly, and a threshold — not a regression — is the shape any rule would have to take.

### Tested as a decision rule (`concept SD p90/p10 > 2.0`)

| | flagged | not flagged |
|---|---:|---:|
| **miss** | 70 | 91 |
| **no miss** | 122 | 1253 |

It catches **70 of 161 misses (43 %)** and flags 122 fits that did not miss. **It is not a usable miss detector.** What it does separate is SEVERITY: median gap among the misses it catches 502.09 nat, against 6.01 nat among those it does not.

The counterexample that settles it: the largest gap the rule would **not** have flagged is **133.87 nat** (`M2K` on M2H {"tau": 2.0}), a low-heterogeneity setting. A data-triggered rule at this threshold would halve the cost and still leave that miss in place.

⚠ Two limits before this becomes a rule. It is a correlation across settings, not across folds within a setting, and the statistic is a property of the generator as much as of the draw — so it shows that a trigger is *plausible*, not that a particular threshold generalises. Establishing a threshold needs the within-setting fold-to-fold relationship, which this design does not measure. That is a question for the amendment, not a conclusion from this table.

## Summary

Overall miss rate 0.105 over 1536 member-fits; largest single gap 8652.182 nat.

Largest gaps:

| generator | grid | rep | size | member | gap (nat) | held-out change (nat/trial) |
|---|---|---:|---|---|---:|---:|
| M2S | `{"omega": 2.0}` | 1 | outer | `M3V` | 8652.182 | +0.95789 |
| M2S | `{"omega": 2.0}` | 4 | inner | `M3V` | 4979.204 | +0.26607 |
| M2S | `{"omega": 2.0}` | 3 | outer | `M3V` | 3952.847 | +0.39995 |
| M2S | `{"omega": 2.0}` | 2 | outer | `M3V` | 3588.293 | +0.51486 |
| M2S | `{"omega": 2.0}` | 3 | inner | `M3V` | 3131.269 | +0.34322 |
| M2S | `{"omega": 2.0}` | 2 | inner | `M3V` | 2823.483 | +0.34062 |
| M2S | `{"omega": 2.0}` | 5 | inner | `M3V` | 2682.589 | +0.65501 |
| M2S | `{"omega": 2.0}` | 0 | outer | `M3V` | 2408.974 | -0.41552 |

R = 6. If the owner gives the machine another day, re-running with `--reps 12` resumes from the checkpoint and only the new datasets are fitted.

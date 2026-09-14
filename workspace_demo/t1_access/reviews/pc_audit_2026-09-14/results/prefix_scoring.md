# Width vs count — fixed prefixes of the archived starts, no refitting

**Runtime identity:** `python 3.12.2 jax 0.11.1 numpy 2.5.3 scipy 1.18.1 pandas 3.0.5 joblib 1.6.0 AMD64`

> Every log-likelihood here was recorded during the fit audit; nothing is refit. Held-out scores are recomputed from already-fitted parameter vectors via `models.concept_scores` — evaluation, not fitting — because a prefix that misses a large TRAINING optimum but lands on the same held-out score is not a practical failure, and the training gap alone cannot tell the two apart.

Reference for every row: the best converged training log-likelihood over ALL 88 archived starts of that member-fit. A *miss* is a prefix falling more than 0.5 nat short of it — the audit's own definition. Analysis time 0.3 min.

**Balanced block: reps (2, 3, 4, 5) — 64 units, all 16 settings.** Rep 1's 6 stragglers are reported separately and pooled into nothing.

⚠ `+k @0.50` is the wider batch; `+k @0.25 (seed B)` is a DISJOINT second prefix at the SAME width as `+k @0.25`, drawn from the same stream — it measures how much of any difference is simply a second draw rather than the width.

⚠ **M2K is excluded from the pooled tables** and shown on its own: its challenge batch leads with four separated-skew starts at ±2.0, so `+8 @0.50` is 4 skew + 4 jittered for M2K and is not a width comparison at all.

⚠ Cold-start count differs by size — 8 at the outer training set, 4 at the inner. Every recipe includes all cold starts of its fit; the `starts added` column counts only what the recipe adds.


### All seven non-skew members, balanced block

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 896 | 0.093 | 49.35 | 4979.20 | +0.00673 | +0.65501 |
| `+8 @0.25` | 8 | 896 | 0.079 | 21.61 | 3584.04 | +0.00316 | +0.65501 |
| `+8 @0.25 (seed B)` | 8 | 896 | 0.069 | 16.21 | 3584.03 | +0.00243 | +0.51440 |
| `+8 @0.50` | 8 | 896 | 0.048 | 9.20 | 2823.48 | +0.00143 | +0.34062 |
| `+8 mixed` | 8 | 896 | 0.058 | 15.03 | 3952.85 | +0.00198 | +0.39995 |
| `+16 @0.25` | 16 | 896 | 0.073 | 15.27 | 3584.03 | +0.00262 | +0.65501 |
| `+16 @0.25 (seed B)` | 16 | 896 | 0.064 | 9.05 | 1727.80 | +0.00127 | +0.21062 |
| `+16 @0.50` | 16 | 896 | 0.027 | 2.66 | 865.63 | +0.00048 | +0.13323 |
| `+16 mixed` | 16 | 896 | 0.044 | 5.15 | 1085.36 | +0.00085 | +0.20168 |
| `+32 @0.25` | 32 | 896 | 0.056 | 4.72 | 1304.57 | +0.00062 | +0.15799 |
| `+64 @0.25` | 64 | 896 | 0.029 | 1.78 | 1304.57 | +0.00021 | +0.15799 |

### `M2H`

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.102 | 75.45 | 1989.11 | +0.01393 | +0.39184 |
| `+8 @0.25` | 8 | 128 | 0.094 | 31.14 | 1755.78 | +0.00408 | +0.19219 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.094 | 38.92 | 1887.36 | +0.00711 | +0.26724 |
| `+8 @0.50` | 8 | 128 | 0.086 | 21.17 | 865.63 | +0.00417 | +0.14015 |
| `+8 mixed` | 8 | 128 | 0.078 | 39.52 | 1981.23 | +0.00602 | +0.29937 |
| `+16 @0.25` | 16 | 128 | 0.086 | 13.06 | 754.45 | +0.00280 | +0.12808 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.094 | 33.91 | 1727.80 | +0.00528 | +0.21062 |
| `+16 @0.50` | 16 | 128 | 0.078 | 12.86 | 865.63 | +0.00268 | +0.13323 |
| `+16 mixed` | 16 | 128 | 0.078 | 15.32 | 865.63 | +0.00302 | +0.13323 |
| `+32 @0.25` | 32 | 128 | 0.078 | 12.20 | 754.45 | +0.00196 | +0.12808 |
| `+64 @0.25` | 64 | 128 | 0.016 | 0.03 | 1.98 | +0.00005 | +0.00615 |

### `M3`

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.133 | 21.10 | 1304.57 | +0.00311 | +0.15799 |
| `+8 @0.25` | 8 | 128 | 0.117 | 20.95 | 1304.57 | +0.00300 | +0.15799 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.094 | 20.86 | 1304.57 | +0.00294 | +0.15799 |
| `+8 @0.50` | 8 | 128 | 0.031 | 0.95 | 109.85 | +0.00012 | +0.00908 |
| `+8 mixed` | 8 | 128 | 0.055 | 0.97 | 109.85 | +0.00009 | +0.00908 |
| `+16 @0.25` | 16 | 128 | 0.109 | 20.94 | 1304.57 | +0.00299 | +0.15799 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.078 | 15.97 | 1304.57 | +0.00205 | +0.15799 |
| `+16 @0.50` | 16 | 128 | 0.023 | 0.88 | 109.85 | +0.00007 | +0.00908 |
| `+16 mixed` | 16 | 128 | 0.023 | 0.87 | 109.58 | +0.00006 | +0.00864 |
| `+32 @0.25` | 32 | 128 | 0.070 | 15.96 | 1304.57 | +0.00204 | +0.15799 |
| `+64 @0.25` | 64 | 128 | 0.031 | 10.27 | 1304.57 | +0.00125 | +0.15799 |

### `M3H`

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.211 | 17.84 | 1085.36 | +0.00213 | +0.09707 |
| `+8 @0.25` | 8 | 128 | 0.203 | 17.18 | 1085.36 | +0.00196 | +0.09707 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.188 | 9.58 | 713.35 | +0.00118 | +0.08627 |
| `+8 @0.50` | 8 | 128 | 0.133 | 10.27 | 1085.36 | +0.00097 | +0.09707 |
| `+8 mixed` | 8 | 128 | 0.156 | 11.49 | 1085.36 | +0.00126 | +0.09707 |
| `+16 @0.25` | 16 | 128 | 0.188 | 3.70 | 163.33 | +0.00022 | +0.01592 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.188 | 9.57 | 713.35 | +0.00117 | +0.08627 |
| `+16 @0.50` | 16 | 128 | 0.039 | 1.20 | 115.02 | +0.00015 | +0.00835 |
| `+16 mixed` | 16 | 128 | 0.125 | 9.94 | 1085.36 | +0.00082 | +0.09707 |
| `+32 @0.25` | 32 | 128 | 0.164 | 3.56 | 163.33 | +0.00016 | +0.01592 |
| `+64 @0.25` | 64 | 128 | 0.133 | 1.94 | 163.33 | +0.00017 | +0.01592 |

### `M3V`

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.094 | 221.41 | 4979.20 | +0.02644 | +0.65501 |
| `+8 @0.25` | 8 | 128 | 0.039 | 77.20 | 3584.04 | +0.01242 | +0.65501 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.016 | 40.04 | 3584.03 | +0.00527 | +0.51440 |
| `+8 @0.50` | 8 | 128 | 0.016 | 28.06 | 2823.48 | +0.00424 | +0.34062 |
| `+8 mixed` | 8 | 128 | 0.023 | 48.92 | 3952.85 | +0.00593 | +0.39995 |
| `+16 @0.25` | 16 | 128 | 0.031 | 67.00 | 3584.03 | +0.01194 | +0.65501 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.000 | 0.00 | 0.00 | -0.00000 | +0.00000 |
| `+16 @0.50` | 16 | 128 | 0.000 | 0.00 | 0.00 | +0.00000 | +0.00000 |
| `+16 mixed` | 16 | 128 | 0.008 | 6.00 | 767.70 | +0.00158 | +0.20168 |
| `+32 @0.25` | 32 | 128 | 0.000 | 0.00 | 0.00 | +0.00000 | +0.00000 |
| `+64 @0.25` | 64 | 128 | 0.000 | 0.00 | 0.00 | -0.00000 | +0.00000 |

### `M3L`

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.109 | 9.67 | 712.40 | +0.00153 | +0.12919 |
| `+8 @0.25` | 8 | 128 | 0.102 | 4.77 | 332.63 | +0.00067 | +0.03310 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.094 | 4.10 | 332.63 | +0.00052 | +0.03310 |
| `+8 @0.50` | 8 | 128 | 0.070 | 3.95 | 332.63 | +0.00048 | +0.03310 |
| `+8 mixed` | 8 | 128 | 0.094 | 4.33 | 332.63 | +0.00056 | +0.03310 |
| `+16 @0.25` | 16 | 128 | 0.094 | 2.18 | 87.33 | +0.00041 | +0.01708 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.086 | 3.92 | 332.63 | +0.00041 | +0.03297 |
| `+16 @0.50` | 16 | 128 | 0.047 | 3.70 | 332.62 | +0.00047 | +0.03312 |
| `+16 mixed` | 16 | 128 | 0.070 | 3.95 | 332.63 | +0.00048 | +0.03310 |
| `+32 @0.25` | 32 | 128 | 0.078 | 1.32 | 56.96 | +0.00016 | +0.01259 |
| `+64 @0.25` | 64 | 128 | 0.023 | 0.21 | 13.13 | -0.00003 | +0.00002 |

### `M2K` — NOT a width comparison (skew starts lead its challenge batch)

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 128 | 0.141 | 4.99 | 230.92 | +0.00093 | +0.02937 |
| `+8 @0.25` | 8 | 128 | 0.055 | 3.02 | 230.91 | +0.00041 | +0.02935 |
| `+8 @0.25 (seed B)` | 8 | 128 | 0.047 | 2.99 | 230.91 | +0.00046 | +0.02934 |
| `+8 @0.50` | 8 | 128 | 0.039 | 0.94 | 36.67 | +0.00017 | +0.01029 |
| `+8 mixed` | 8 | 128 | 0.047 | 1.18 | 42.53 | +0.00022 | +0.01029 |
| `+16 @0.25` | 16 | 128 | 0.039 | 2.68 | 230.91 | +0.00033 | +0.02935 |
| `+16 @0.25 (seed B)` | 16 | 128 | 0.039 | 2.69 | 230.91 | +0.00037 | +0.02935 |
| `+16 @0.50` | 16 | 128 | 0.016 | 0.27 | 22.33 | +0.00004 | +0.00413 |
| `+16 mixed` | 16 | 128 | 0.023 | 0.56 | 24.56 | +0.00006 | +0.00378 |
| `+32 @0.25` | 32 | 128 | 0.031 | 2.36 | 230.91 | +0.00029 | +0.02935 |
| `+64 @0.25` | 64 | 128 | 0.016 | 1.99 | 230.91 | +0.00025 | +0.02935 |

### Rep 1 stragglers (6 units), reported separately

| recipe | starts added | n | miss rate | mean gap | max gap | mean held-out loss (nat/trial) | max held-out loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cold only` | 0 | 84 | 0.155 | 175.76 | 8652.18 | +0.02069 | +0.95789 |
| `+8 @0.25` | 8 | 84 | 0.119 | 34.02 | 852.44 | +0.00452 | +0.15993 |
| `+8 @0.25 (seed B)` | 8 | 84 | 0.155 | 130.91 | 8652.18 | +0.01410 | +0.95789 |
| `+8 @0.50` | 8 | 84 | 0.107 | 47.52 | 1155.63 | +0.00602 | +0.21487 |
| `+8 mixed` | 8 | 84 | 0.107 | 33.46 | 852.44 | +0.00446 | +0.15993 |
| `+16 @0.25` | 16 | 84 | 0.107 | 22.04 | 696.88 | +0.00258 | +0.15993 |
| `+16 @0.25 (seed B)` | 16 | 84 | 0.107 | 21.62 | 850.13 | +0.00302 | +0.12824 |
| `+16 @0.50` | 16 | 84 | 0.083 | 34.85 | 1155.63 | +0.00540 | +0.21487 |
| `+16 mixed` | 16 | 84 | 0.083 | 33.39 | 852.44 | +0.00445 | +0.15993 |
| `+32 @0.25` | 32 | 84 | 0.083 | 8.83 | 353.77 | +0.00020 | +0.02860 |
| `+64 @0.25` | 64 | 84 | 0.048 | 4.84 | 353.76 | -0.00024 | +0.00330 |

## The controlled comparison

**At 8 added starts** (non-skew members, balanced block): miss rate **0.079 at 0.25**, **0.048 at 0.50**, **0.069 at 0.25 from a disjoint second draw**, **0.058 mixed**. Width effect +0.031; seed effect at fixed width +0.010.
**At 16 added starts** (non-skew members, balanced block): miss rate **0.073 at 0.25**, **0.027 at 0.50**, **0.064 at 0.25 from a disjoint second draw**, **0.044 mixed**. Width effect +0.046; seed effect at fixed width +0.009.

If the width effect is large against the seed effect, width is doing the work; if they are comparable, the audit's 3.2x was a seed artefact. The tables above answer it per member as well as in pool.

## Cost per start, per member

From the audit's own timings: the strong search ran 80 added starts per member-fit.

| member | size | s/start | cost of +16 | cost of +64 | ratio |
|---|---|---:|---:|---:|---:|
| `M2B` | outer | 0.05 | 1 s | 3 s | 4x |
| `M2B` | inner | 0.04 | 1 s | 2 s | 4x |
| `M2H` | outer | 15.09 | 242 s | 966 s | 4x |
| `M2H` | inner | 10.02 | 160 s | 641 s | 4x |
| `M2S` | outer | 7.93 | 127 s | 507 s | 4x |
| `M2S` | inner | 5.52 | 88 s | 353 s | 4x |
| `M2K` | outer | 0.25 | 4 s | 16 s | 4x |
| `M2K` | inner | 0.16 | 3 s | 10 s | 4x |
| `M3` | outer | 0.29 | 5 s | 19 s | 4x |
| `M3` | inner | 0.20 | 3 s | 13 s | 4x |
| `M3H` | outer | 39.69 | 635 s | 2540 s | 4x |
| `M3H` | inner | 25.74 | 412 s | 1648 s | 4x |
| `M3V` | outer | 0.20 | 3 s | 13 s | 4x |
| `M3V` | inner | 0.13 | 2 s | 8 s | 4x |
| `M3L` | outer | 0.31 | 5 s | 20 s | 4x |
| `M3L` | inner | 0.23 | 4 s | 15 s | 4x |

A recipe of **cold + 16 at 0.50** costs a quarter of **cold + 64 at 0.25** on every member, so if it also matches or beats it on miss rate the choice is settled on both axes at once.

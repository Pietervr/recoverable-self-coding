# Repaired same-data, same-code node checks — W2 set 0 (20261025T103957Z)

Code hash: ca6c7e5547d5. Tolerance T = min(8.8322454e-05, one tenth of the reference run's Δ₃ interval half-width); PASS needs all twenty participants available in both runs, max |Δ₃ difference| < T, no numerical failure and no nesting failure in either run.

| run | τ nodes | g nodes | rule | available | primary | half-width | numerical failures | nesting failures | polish calls/accepted | r | task-s (mean) | wall s | workers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F | 61 | 17 | 17then33 | 20/20 | NEGATIVE | 6.426e-04 | 0 | 0 | 7/6 | 0.0001 | 30276 (1514) | 2359 | 20 |
| G | 121 | 17 | 17then33 | 20/20 | NEGATIVE | 6.504e-04 | 0 | 0 | 5/4 | 0.0000 | 54710 (2735) | 3672 | 20 |
| H | 61 | 33 | 17 | 20/20 | NEGATIVE | 6.422e-04 | 0 | 0 | 11/10 | 0.0002 | 39843 (1992) | 3136 | 20 |

| comparison | PASS | max abs diff | worst | T | over T | unavailable | numerical failures | nesting failures | selection flips |
|---|---|---|---|---|---|---|---|---|---|

LATENCY RULE outcome: None.

# S2 decision batches on development seeds — reading, not a gate

Set-level primary = sign of the Δ₃ = S_B3 − S_G3 t-interval over the set's available participants (UNAVAILABLE if fewer than 16). W2/O1 are graded generators (a POSITIVE set is a false call), T1 the two-state generator (a POSITIVE set is a detection). Start basins: 'best≠first' = the selected optimum came from a start other than the first; 'improved' = a later start beat a CONVERGED first start by > 1e-6 relative.

| setting | R | POSITIVE | NEGATIVE | UNRESOLVED | UNAVAILABLE | Δ₃ mean (sd) per participant | set-mean Δ₃ range | participants unavailable | s per participant-dataset |
|---|---|---|---|---|---|---|---|---|---|
| W2 | 19 | 6 | 0 | 13 | 0 | +0.00427 (0.01297) | [-0.00044, +0.01210] | 0/380 | 165.5 |

| setting | spec | starts | s/start | nit | converged | retries | early | fits UNAVAILABLE | best≠first | improved | max gap nat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W2 | G2 | 7600 | 0.090 | 88 | 0.999 | 210 | 0 | 0/1900 | 1887/1900 | 1870/1900 | 2499.018 |
| W2 | G3+ | 7600 | 3.302 | 199 | 0.996 | 369 | 0 | 0/1900 | 1878/1900 | 1860/1900 | 2614.823 |
| W2 | B2 | 7600 | 0.186 | 178 | 1.000 | 69 | 0 | 0/1900 | 1863/1900 | 1788/1900 | 1788.315 |
| W2 | B3+ | 7600 | 4.676 | 307 | 0.998 | 208 | 0 | 0/1900 | 1850/1900 | 1818/1900 | 1894.926 |

W2 G3: REDUCED 38, POSITIVE 1862, flags {'positive_at_floor': 32}.
W2 B3: REDUCED 37, POSITIVE 1863, flags {'positive_at_floor': 32}.

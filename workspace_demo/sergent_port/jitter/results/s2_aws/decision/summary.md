# S2 decision batches on development seeds — reading, not a gate

Set-level primary = sign of the Δ₃ = S_B3 − S_G3 t-interval over the set's available participants (UNAVAILABLE if fewer than 16). W2/O1 are graded generators (a POSITIVE set is a false call), T1 the two-state generator (a POSITIVE set is a detection). Start basins: 'best≠first' = the selected optimum came from a start other than the first; 'improved' = a later start beat a CONVERGED first start by > 1e-6 relative.

| setting | R | POSITIVE | NEGATIVE | UNRESOLVED | UNAVAILABLE | Δ₃ mean (sd) per participant | set-mean Δ₃ range | participants unavailable | s per participant-dataset |
|---|---|---|---|---|---|---|---|---|---|
| W2 | 22 | 0 | 17 | 5 | 0 | -0.00107 (0.00227) | [-0.00210, +0.00039] | 0/440 | 4547.3 |
| T1 | 25 | 25 | 0 | 0 | 0 | +0.01404 (0.01809) | [+0.01050, +0.02076] | 0/500 | 4598.1 |
| O1 | 25 | 0 | 14 | 11 | 0 | -0.00115 (0.00219) | [-0.00222, -0.00026] | 0/500 | 4343.8 |

| setting | spec | starts | s/start | nit | converged | retries | early | fits UNAVAILABLE | best≠first | improved | max gap nat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W2 | G2 | 23746 | 0.035 | 56 | 0.992 | 930 | 37 | 0/2200 | 2200/2200 | 2188/2200 | 2437.280 |
| W2 | G3+ | 39149 | 14.610 | 185 | 0.990 | 1560 | 181 | 0/2200 | 2200/2200 | 2196/2200 | 2410.691 |
| W2 | B2 | 29225 | 0.068 | 94 | 0.994 | 766 | 2244 | 0/2200 | 2200/2200 | 2197/2200 | 1917.739 |
| W2 | B3+ | 44803 | 23.600 | 224 | 0.991 | 1794 | 2219 | 0/2200 | 2200/2200 | 2195/2200 | 1847.191 |
| T1 | G2 | 32443 | 0.031 | 55 | 0.990 | 1530 | 5 | 0/2500 | 2500/2500 | 2492/2500 | 1108.298 |
| T1 | G3+ | 51603 | 10.260 | 163 | 0.986 | 2644 | 163 | 0/2500 | 2500/2500 | 2486/2500 | 956.175 |
| T1 | B2 | 34428 | 0.045 | 60 | 0.995 | 804 | 2567 | 0/2500 | 2500/2500 | 2497/2500 | 726.708 |
| T1 | B3+ | 53330 | 22.114 | 195 | 0.990 | 1951 | 2154 | 0/2500 | 2500/2500 | 2493/2500 | 562.829 |
| O1 | G2 | 26569 | 0.037 | 58 | 0.990 | 1280 | 47 | 0/2500 | 2500/2500 | 2494/2500 | 3508.302 |
| O1 | G3+ | 46010 | 10.743 | 175 | 0.990 | 1831 | 573 | 0/2500 | 2500/2500 | 2490/2500 | 3509.350 |
| O1 | B2 | 33187 | 0.065 | 92 | 0.993 | 1116 | 2557 | 0/2500 | 2499/2500 | 2499/2500 | 2567.018 |
| O1 | B3+ | 53216 | 17.827 | 210 | 0.992 | 2069 | 2431 | 0/2500 | 2500/2500 | 2497/2500 | 2268.841 |

W2 G3: REDUCED 77, POSITIVE 2123, flags {'positive_at_floor': 66}.
W2 B3: REDUCED 85, POSITIVE 2115, flags {'positive_at_floor': 67}.
T1 G3: REDUCED 400, POSITIVE 2100, flags {'positive_at_floor': 102}.
T1 B3: REDUCED 397, POSITIVE 2103, flags {'positive_at_floor': 93}.
O1 G3: REDUCED 315, POSITIVE 2185, flags {'positive_at_floor': 271}.
O1 B3: REDUCED 359, POSITIVE 2141, flags {'positive_at_floor': 276}.

# Final-rule checks — W2 set 0 (20261025T104007Z)

Runs present: F, G, H; code hashes ca6c7e5547d5; run fingerprints 856f6cd4bddc5aab, a0d5773d33885ff9.

Criterion (Codex S3 re-review finding 3): identical complete rosters, finite results, no unresolved numerical failure, no material matched-quadrature nesting failure, the same primary sign, and max(|Δμ|, |ΔL|, |ΔU|) < T_set = min(8.8322454e-05, 0.1·min(h_x, h_y)) on the group 95% t intervals; participant differences are diagnostics.

| comparison | PASS | rosters | finite | no num. failure | no nesting failure | same sign | max(Δμ, ΔL, ΔU) | T_set | participant max (diag.) |
|---|---|---|---|---|---|---|---|---|---|
| F_vs_G | PASS | True | True | True (0/0) | True (0/0) | True (NEGATIVE/NEGATIVE) | 2.9566e-05 | 6.4264e-05 | 0.000454260226213421 |
| F_vs_H | PASS | True | True | True (0/0) | True (0/0) | True (NEGATIVE/NEGATIVE) | 1.5637e-05 | 6.4225e-05 | 0.00028250017306419295 |

Fixed-endpoint cross-evaluation of F's endpoints: reproduction max 2.48e-15 (ok); grid G: max |change| 2.7417e-05 vs T_set 6.4264e-05 -> PASS; grid H: max |change| 6.3894e-07 vs T_set 6.4225e-05 -> PASS.

VERDICT: PASS: the final rule 61/17then33 meets the amended set-level criterion and the fixed-endpoint checks.

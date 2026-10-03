# Stage A (row 20) report - ADMISSIBLE

Validator: FAIL (11 failures). Only STAGE_A_FINAL.json, written by the controller after this report, can state PASS.

Unique planned ids 178; started 174; actual tries 174.

## Failures

- NOT_COMMITTED at 16-native: 
- NOT_COMMITTED at 17-native: 
- NOT_COMMITTED at 18-native: 
- NOT_COMMITTED at 19-native: 
- PHASE_RECORD_MISSING at NATIVE_DONE.json: 
- PARITY at 15-native: (0.0, 0.125, True)
- PARITY_INPUTS_MISSING at 16-native: 
- PARITY_INPUTS_MISSING at 17-native: 
- PARITY_INPUTS_MISSING at 18-native: 
- PARITY_INPUTS_MISSING at 19-native: 
- PARITY_COUNT at 16: 

## Native parity (recomputed from the committed arrays)

| input | rel L2 max | logit max abs | argmax equal | pass |
|---|---|---|---|---|
| 0 | 0 | 0.0625 | True | True |
| 1 | 0 | 0.0312 | True | True |
| 2 | 0 | 0.0312 | True | True |
| 3 | 0 | 0.0312 | True | True |
| 4 | 0 | 0.0312 | True | True |
| 5 | 0 | 0.0312 | True | True |
| 6 | 0 | 0.0312 | True | True |
| 7 | 0 | 0.0312 | True | True |
| 8 | 0 | 0.0312 | True | True |
| 9 | 0 | 0.0312 | True | True |
| 10 | 0 | 0.0625 | True | True |
| 11 | 0 | 0.0312 | True | True |
| 12 | 0 | 0.0625 | True | True |
| 13 | 0 | 0.0625 | True | True |
| 14 | 0 | 0.0312 | True | True |
| 15 | 0 | 0.125 | True | False |

## Stage B

```
{
 "prediction": {
  "seconds_per_unique_attempt_whole_stage": 1.7227245915119789,
  "bytes_per_unique_attempt": 2189232.540229885,
  "predicted_seconds": 3197.3768418462328,
  "predicted_bytes": 4063215594.6666665,
  "limit_seconds": 11520.0,
  "limit_bytes": 6871947673.6,
  "note": "PRELIMINARY (as of this report); the completed prediction is in STAGE_A_FINAL.json"
 },
 "admission": {
  "STAGE_A_FINAL_PASS": false,
  "inspected_figures_and_interpretation": false,
  "interpretation_problems": [
   "absent"
  ],
  "codex_review_of_report": false,
  "owner_row21_go": false,
  "b_first_cal_slice": "row 21's own gate",
  "admitted": false
 }
}
```

## Interpretation

Not written here: the author inspects the figures and archives report/INTERPRETATION.md ('Author: ', 'Date: YYYY-MM-DD', and '<figure> sha256: <hex>' for both figures) before any B admission.

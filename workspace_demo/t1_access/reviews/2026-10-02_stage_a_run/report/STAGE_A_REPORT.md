# Stage A (row 20) report - ADMISSIBLE

Validator: FAIL (42 failures). Only STAGE_A_FINAL.json, written by the controller after this report, can state PASS.

Unique planned ids 178; started 158; actual tries 158.

## Failures

- NOT_COMMITTED at 00-native: 
- NOT_COMMITTED at 01-native: 
- NOT_COMMITTED at 02-native: 
- NOT_COMMITTED at 03-native: 
- NOT_COMMITTED at 04-native: 
- NOT_COMMITTED at 05-native: 
- NOT_COMMITTED at 06-native: 
- NOT_COMMITTED at 07-native: 
- NOT_COMMITTED at 08-native: 
- NOT_COMMITTED at 09-native: 
- NOT_COMMITTED at 10-native: 
- NOT_COMMITTED at 11-native: 
- NOT_COMMITTED at 12-native: 
- NOT_COMMITTED at 13-native: 
- NOT_COMMITTED at 14-native: 
- NOT_COMMITTED at 15-native: 
- NOT_COMMITTED at 16-native: 
- NOT_COMMITTED at 17-native: 
- NOT_COMMITTED at 18-native: 
- NOT_COMMITTED at 19-native: 
- PHASE_RECORD_MISSING at NATIVE_DONE.json: 
- PARITY_INPUTS_MISSING at 00-native: 
- PARITY_INPUTS_MISSING at 01-native: 
- PARITY_INPUTS_MISSING at 02-native: 
- PARITY_INPUTS_MISSING at 03-native: 
- PARITY_INPUTS_MISSING at 04-native: 
- PARITY_INPUTS_MISSING at 05-native: 
- PARITY_INPUTS_MISSING at 06-native: 
- PARITY_INPUTS_MISSING at 07-native: 
- PARITY_INPUTS_MISSING at 08-native: 
- PARITY_INPUTS_MISSING at 09-native: 
- PARITY_INPUTS_MISSING at 10-native: 
- PARITY_INPUTS_MISSING at 11-native: 
- PARITY_INPUTS_MISSING at 12-native: 
- PARITY_INPUTS_MISSING at 13-native: 
- PARITY_INPUTS_MISSING at 14-native: 
- PARITY_INPUTS_MISSING at 15-native: 
- PARITY_INPUTS_MISSING at 16-native: 
- PARITY_INPUTS_MISSING at 17-native: 
- PARITY_INPUTS_MISSING at 18-native: 
- PARITY_INPUTS_MISSING at 19-native: 
- PARITY_COUNT at 0: 

## Native parity (recomputed from the committed arrays)

| input | rel L2 max | logit max abs | argmax equal | pass |
|---|---|---|---|---|

## Stage B

```
{
 "prediction": {
  "seconds_per_unique_attempt_whole_stage": 1.1918394254919147,
  "bytes_per_unique_attempt": 2009539.670886076,
  "predicted_seconds": 2212.053973712994,
  "predicted_bytes": 3729705629.164557,
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

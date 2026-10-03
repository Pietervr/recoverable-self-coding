# Stage A (row 20) report - ADMISSIBLE

**Environment provenance (revision 15).** The machine's OS changed without the project's doing (the unplanned restart of 3 October; the revision-14 resume refused at the gates at 16:27 UTC, its 71.5 s charged). Records completed before the transition c0fb2ea0 -> 1d017dce (174) were produced on macos 27.0; later records on 27.0.1 (build 26A434).

Validator: PASS (0 failures). Only STAGE_A_FINAL.json, written by the controller after this report, can state PASS.

Unique planned ids 178; started 178; actual tries 178.

## Failures


## Native parity (recomputed from the committed arrays)

Logit criterion (revisions 13-14): per requested logit, |difference| <= max(0.10, the bfloat16 step of the larger magnitude's binade); 0.10 is the floor, not the bound for every logit. The columns describe the component with the largest absolute difference; the deciding component (largest difference / tolerance) is in the last two columns and, with its magnitude and steps, in stage_a_report.json and any failure.

Instrumented references (00-19) and their macOS are in the provenance note above; the native column 'native macOS' is each native record's own (from the transition records). A revision-15 parity FAIL in a record produced on a different macOS from its reference is AMBIGUOUS (OS or path).

| input | rel L2 max | logit max abs | at magnitude | tolerance there | bf16 steps | worst diff / tolerance | at magnitude | argmax equal | pass | native macOS |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0.0625 | 14.75 | 0.1 | 1.0 | 0.625 | 14.75 | True | True | 27.0 |
| 1 | 0 | 0.0312 | 3.141 | 0.1 | 2.0 | 0.312 | 3.141 | True | True | 27.0 |
| 2 | 0 | 0.0312 | 5.594 | 0.1 | 1.0 | 0.312 | 5.594 | True | True | 27.0 |
| 3 | 0 | 0.0312 | 4.594 | 0.1 | 1.0 | 0.312 | 4.594 | True | True | 27.0 |
| 4 | 0 | 0.0312 | 6.781 | 0.1 | 1.0 | 0.312 | 6.781 | True | True | 27.0 |
| 5 | 0 | 0.0312 | 5.219 | 0.1 | 1.0 | 0.312 | 5.219 | True | True | 27.0 |
| 6 | 0 | 0.0312 | 6.531 | 0.1 | 1.0 | 0.312 | 6.531 | True | True | 27.0 |
| 7 | 0 | 0.0312 | 4.25 | 0.1 | 1.0 | 0.312 | 4.25 | True | True | 27.0 |
| 8 | 0 | 0.0312 | 3.562 | 0.1 | 2.0 | 0.312 | 3.562 | True | True | 27.0 |
| 9 | 0 | 0.0312 | 5.469 | 0.1 | 1.0 | 0.312 | 5.469 | True | True | 27.0 |
| 10 | 0 | 0.0625 | 11.62 | 0.1 | 1.0 | 0.625 | 11.62 | True | True | 27.0 |
| 11 | 0 | 0.0312 | 2.266 | 0.1 | 2.0 | 0.312 | 2.266 | True | True | 27.0 |
| 12 | 0 | 0.0625 | 12.38 | 0.1 | 1.0 | 0.625 | 12.38 | True | True | 27.0 |
| 13 | 0 | 0.0625 | 15.81 | 0.1 | 1.0 | 0.625 | 15.81 | True | True | 27.0 |
| 14 | 0 | 0.0312 | 5.5 | 0.1 | 1.0 | 0.312 | 5.5 | True | True | 27.0 |
| 15 | 0 | 0.125 | 16.5 | 0.125 | 1.0 | 1 | 16.5 | True | True | 27.0 |
| 16 | 0 | 0.0312 | 2.281 | 0.1 | 2.0 | 0.312 | 2.281 | True | True | 27.0.1 |
| 17 | 0 | 0.0195 | 0.8711 | 0.1 | 5.0 | 0.195 | 0.8711 | True | True | 27.0.1 |
| 18 | 0 | 0.0234 | 0.6172 | 0.1 | 6.0 | 0.234 | 0.6172 | True | True | 27.0.1 |
| 19 | 0 | 0.0312 | 3.375 | 0.1 | 2.0 | 0.312 | 3.375 | True | True | 27.0.1 |

## Stage B

```
{
 "prediction": {
  "seconds_per_unique_attempt_whole_stage": 2.630181355834655,
  "bytes_per_unique_attempt": 2228945.7696629213,
  "predicted_seconds": 4881.616596429119,
  "predicted_bytes": 4136923348.494382,
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

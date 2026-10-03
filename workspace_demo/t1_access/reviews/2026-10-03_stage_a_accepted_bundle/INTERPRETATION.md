# Stage A (ledger row 20): the row owner's interpretation of the report and its two figures

Author: R052 Entropy SI (Claude), owner of ledger row 20
Date: 2026-10-03
rel_l2_by_layer.svg sha256: 9c39652debc389f4d0048e03cdee3a50d751a198698a0da047fb69126b31a381
logit_max_abs.svg sha256: 4a37ba7c28a4d9d449ed102c30ad3c40413bb9b250597d4743b5db482c4458c3

Revised 2026-10-03 after Codex's report review (RSC `b0db0f9`, `reviews/2026-10-03_stage_a_report_codex_record.md`, SHA-256
`52ed7082…`, YES WITH QUALIFICATIONS): native agreement worded as zero recorded relative-L2 distance, not bit identity; the
claim narrowed to the recorded rows and requested tokens; the post-failure amendment and the four controller starts stated.

Report read: `captures/photo_stage_a/report/STAGE_A_REPORT.md` (sha256 `b2816de0…`), `stage_a_report.json` (`b0fc6945…`),
`REPORT_RECEIPT.json` (`c67f327b…`), and `STAGE_A_FINAL.json` (`2a133fcb…`, outcome PASS, admissible, not terminal),
as retained in `reviews/2026-10-03_stage_a_rev15_resume_run/`. Both figures were rendered and looked at. The validator
was recomputed by the author from the saved arrays (0 failures; 20 parity rows equal to the stored ones).

## Terms

- **Instrumented path.** The model's forward pass with the capture code attached: it records the residual stream at
  three marker rows in each of the 64 layers (5,120 values per row) and can apply an edit at layer 41.
- **Native path.** The same model and input with no capture code attached.
- **Sham case.** An instrumented forward whose edit is constructed to change nothing: `empty`, `zero_steer`,
  `zero_ablate`, `zero_swap`, `self_patch`; and `repeat`, a second plain forward.
- **Requested logits.** The model's output scores for the frozen list of concept tokens.
- **bf16 step.** The spacing between neighbouring bfloat16 numbers at a given magnitude. From 16 up to 32 it is 0.125.

## What was done

Twenty development images were run. For each: one plain instrumented forward and six sham cases (140 forwards), 16
mechanics diagnostics, 2 suffix-isolation diagnostics, and one native forward (20). In all, 178 planned forwards, each
run once. Three criteria categories were declared before the runs (the numerical logit tolerance was later amended;
see point 3 below):

1. Every sham case must reproduce the plain forward's recorded residuals bit for bit (120 comparisons).
2. The native forward must agree with the instrumented plain forward: relative L2 distance of the recorded residuals at
   most 0.01 in every layer; every requested logit within the tolerance; the same top-scoring requested token.
3. Counters, time, memory and storage must stay inside the declared caps.

## What was found

- All 120 sham comparisons are bit-identical. The two encoder-sensitivity inputs differ, as they must.
- Native against instrumented, all 20 images: the recorded relative L2 distance is zero at every saved marker row in
  every one of the 64 layers. (No byte-equality comparison of the native residuals was made; numerical zero is stated,
  not bit identity.)
- The largest requested-logit difference per image is between 0.0195 and 0.0625 for 19 images and 0.125 for image 15.
  The top-scoring requested token is the same on both paths for all 20.
- Caps: 194 of 200 forwards, 2,338 s of 14,400 s, 33.3 GB peak task memory, 396.8 MB of storage. All hold.

## The two figures

- `rel_l2_by_layer.svg`: twenty curves over the 64 layers, all on the zero line. The dashed line is the 0.01
  tolerance. Nothing approaches it.
- `logit_max_abs.svg`: one point per image, the largest absolute requested-logit difference. The dashed line is the
  0.10 floor of the tolerance, not each image's own tolerance. Image 15 is ABOVE the dashed line at 0.125. Its logit
  magnitude is 16.5, where one bf16 step is 0.125 and is the tolerance, so it meets the criterion exactly, with no
  margin (difference / tolerance = 1.000). Every other image is at or below 0.625 of its tolerance.
- Neither figure has axis ticks, axis labels or a legend, and neither shows which macOS a point was produced on. Values
  and provenance are read from the report's table and the transition records, not from the figures.

## What it means, and what it does not

1. On these 20 development images the sham edits leave the recorded residuals bit-identical (120 explicit comparisons),
   and the native and instrumented endpoints agree at the recorded rows and requested tokens: zero recorded relative-L2
   distance, logits within tolerance, the same top token. Images 0-15 compare the two paths within macOS 27.0; images
   16-19 compare old-macOS instrumented with new-macOS native jointly. This is agreement at the saved rows and the
   requested token set, not a statement about the whole computation.
2. The requested logits differ between the paths although the recorded relative-L2 distance is zero. The report does
   not establish why, and no cause is inferred here. The differences are one to six bf16 steps at the logits'
   magnitudes and never change the top-scoring requested token.
3. **Image 15 passes under a criterion amended after it failed.** On 3 October it stopped the run under the original
   absolute tolerance of 0.10 (0.125 > 0.10). Revision 13 changed the tolerance to max(0.10, one bf16 step), unchanged
   below magnitude 16; Codex reviewed that change (favourable at revision 14) before the saved outputs were
   re-evaluated. The justification is the number format: two bfloat16 logits near 16.5 that are not identical differ by
   at least 0.125. The amendment is disclosed wherever this result is stated.
4. **Images 16-19 compare two things at once.** Their instrumented references were produced on macOS 27.0 and their
   native forwards on macOS 27.0.1, after an unplanned system update. Their pass is joint agreement across the path and
   the macOS version. It does not show separately that the path makes no difference or that the macOS version makes no
   difference; opposite effects could cancel. Images 0-15 were compared within macOS 27.0.
5. **The instrumented path has not been run on macOS 27.0.1.** All 158 instrumented forwards ran on 27.0. Stage A does
   not qualify the capture path on the macOS version row 21 would run on. Whether row 21 needs an instrumented repeat
   against its own 27.0 record first is for row 21's own review (Codex `1a33e68`).
6. The macOS build `26A434` is recorded for 27.0.1 and is not part of the bound identity; the build of 27.0 was never
   recorded.
7. This is a fidelity check of the instrument on development images. It is not a result about the model's
   representations, it supports no claim in the paper, and it says nothing about held-out images, other layers' rows,
   or tokens outside the requested list.
8. Stage B forecast from the completed rates: 5,520 s against a limit of 11,520 s and 4.14 GB against 6.87 GB. Both
   fit. The forecast rests on 178 forwards and is not a measurement of Stage B.

## History that the result carries

Four controller starts are charged: three that executed forwards and one refused before any forward. 2 October: the
instrumented phase completed and the controller then stopped on a race in its
own supervision of the workers ("watchdog exited"; revisions 11-12). 3 October: sixteen native forwards, stopped at image 15 on the tolerance
(revisions 13-14). 3 October 16:27 UTC: a start refused before any forward because macOS had changed (revision 15). No
forward was repeated; every counter and every second, including the 71.5 s of the refused start, is carried.

## Two points in the report's text (the bound file is left as reviewed)

- It says the deciding component is "in the last two columns". In the table as built it is columns 7 and 8 ("worst
  diff / tolerance", "at magnitude"); the last two are "pass" and "native macOS".
- After a rare failure before a transition link is published, the report's macOS label would fall back to the current
  macOS for old records. That did not arise: the link was published before the report.

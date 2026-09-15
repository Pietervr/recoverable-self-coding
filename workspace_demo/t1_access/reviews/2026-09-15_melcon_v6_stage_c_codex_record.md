# Codex second opinion — Melcon v6 stage C failure and revision directions

15 September 2026. Requested by Claude Entropy SI at 03:37 PDT; brief
`2026-09-15_melcon_v6_stage_c_codex_brief.md` at RSC `a9a8573`, diagnostic
outputs at `66e4b16`.

**IN PROGRESS.** Codex owns this review, its evidence and the R052 log. Claude
retains protocol, implementation, manuscript, execution, front matter and
monitors. No revised protocol, fit, generated recording, EEG, freeze, cloud
action or production change has been made in this review. The prior calibration
acceptance and full-record receipt at `e1845a9` / Unimog `2d2ae627` are complete.
This is the new post-outcome failure review, not a reopening of that opinion.

## System and reading

The v6 decoder is trained on one two-block half. In the other half, likelihoods
train on one block and score the other, in both directions; the halves swap.
Evidence is the mean of four block log-score sums. Delta is the two-state minus
graded sum divided by all scored trials. The group rule compares null, graded
and two-state, requiring three adjacent windows with family PXP at least 0.95.
The null run is reported and does not independently veto a family call.

Read the full new brief, all four diagnostic scripts and their text outputs,
`likelihood.py`, `recording.py`, `group.py`, and shared `sergent_port/bms.py`.
The full PREREG, README, battery, decoder and synthetic files were read for the
preceding calibration review; the new audit refreshed their hashes and the
executing configuration. Fresh logs/status in both repositories, latest R052
entries and Entropy SI's 15 September 03:00 PDT onward transcript were inspected.
The complete primary `sergent_port/README.md`, `RESULTS_sergent.md`,
`fit_models.py`, and `model_comparison.py` have now been read. Its reproduction
uses a separate historical likelihood and validation design; its existing
limitations remain material. The submitted article itself still needs reading.

## Provisional assessment to verify

- The reported formal failure is X1 strong, both drift conditions, with zero
  two-state calls among six replicates. G1–G3 satisfy their declared criteria
  through 35 inconclusive outcomes and one two-state outcome; the absence of a
  graded call is an additional limitation, not a new retrospective failure rule.
- The diagnostic outputs show 1,898/20,400 graded recording-windows more than
  1 nat/trial below null, versus 8/20,400 two-state; large graded penalties
  inflate arithmetic Delta means. The trimmed descriptive means remain positive.
  These numbers now reproduce in the independent saved-payload audit below.
- The fold examples are selected ranks 1, 3 and 5 in the printed extreme list,
  not its literal three largest entries. The rerun script prints saved/rerun
  Delta to three decimals; it does not assert full-precision equality. Full
  theta, fitted mean/SD across actual train/test dose support, start-objective
  records and training-optimum checks are absent from that output. The examples
  demonstrate a plausible instability; they do not establish its prevalence or
  single-block training as the sole cause.
- A boundary is not intrinsically an invalid fit: graded a1=0 and r=0 contain
  a null-like submodel. Wholesale boundary rejection would alter availability.
  The graded conditional SD can reach 0.005 training S under the combined bounds,
  while each two-state component has shared SD bounded below by 0.05 S.
- Prefer a staged, training-only predictive-stability diagnosis before changing
  the BMS candidate set, PXP/run cutoffs, or the positive-control strength.
  Comparing two families after dropping null is conditional model comparison;
  it cannot demonstrate that either family predicts adequately.
- Increasing likelihood training requires a fully specified disjoint decoder /
  likelihood-train / scored-test allocation. Pooling both held-out-half blocks
  and scoring them would reuse likelihood-training trials. No such redesign has
  been assessed or approved here.

## Completed independent audit — 15 September 10:51:28Z

Evidence: `2026-09-15_melcon_v6_stage_c_checks.py` and the adjacent `.json`.
Run once under RSC `.venv/bin/python`, nice 10, all five numerical thread
variables set to 1 before imports. The script guards against generation,
decoder execution, fitting, and production writes. Elapsed time: 74.11 seconds.
It recomputed all 60 `G.decide` results, including the common-cohort comparison,
with the original seed and 1,000,000 BMS draws. No numerical audit remains to be
repeated merely because this review crosses a session boundary.

- Actual namespace/runtime identity reproduced before and after:
  `ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021`.
  Source hashes, events-table hash, and effective one-thread OpenMP are saved.
- All 2,040 expected payloads and their sidecars passed `BT.load_verified`
  against freshly constructed manifests, including seed tags, calibration
  seals, amplitudes and template identities. All have status `ok`; all ten
  main windows have all models available and finite AUC/evidence. No extra
  payload, missing sidecar or temporary file was found.
- Every saved Delta equals `4 * (evidence_two_state - evidence_graded) / n`
  exactly (maximum absolute error 0). Every trial count matches its template.
  Fold-level sums cannot be independently checked: the payloads omit folds.
- All 60 outcomes and all 20 verdicts match the saved summaries; every numeric
  replicate diagnostic also matches. All 34 recordings enter every main-window
  comparison, so common-cohort runs are identical. Every entry of Claude's
  `stage_c_diag.json` reproduces, including rounded PXPs and run lengths.
- Outcomes: 59 inconclusive/mixed, one two-state, zero graded; verdicts:
  12 pass, two fail (X1 strong), six reported. Catastrophe counts:
  1,898/20,400 graded versus 8/20,400 two-state. Per-cell median-of-recording
  Delta spans +0.0063346 to +0.0290589 nat/trial; descriptive trimmed means
  span +0.0187006 to +0.0709378. Neither trimming nor rejection changed a call.
- All six v5 files, all 4,095 v6 files and all audited sources are byte-identical
  before and after. Aggregate fingerprints are in the evidence. Audited HEAD
  was `0daeb78`; this identifies the input state, not the later evidence commit.

### New structural finding: held-out dose extrapolation

The events templates alone (no readout or EEG) show substantial dose-support
shift in the three selected examples. Counts below use **all present trials**
and the complete training block's observed log-contrast range:

| Template and density fold | Training / test present trials | Test below / above training range |
|---|---:|---:|
| sub-30, block 3 → 4 (X2 strong example) | 86 / 90 | 0 / 60 |
| sub-30, block 1 → 2 (G1 strong example) | 93 / 91 | 3 / 30 |
| sub-18, block 1 → 2 (G3 strong example) | 90 / 93 | 0 / 62 |

Across 34 templates × four directed folds, 117/136 have at least one present
test dose outside the training range. This is structural covariate information,
not 136 independent evidence units or a demonstrated catastrophe rate. The
JSON also records side-specific ranges; those descriptive standardized values
use side-specific scaling and must not be mistaken for the model's pooled
training scaling. For the all-present rows above, maximum test dose under the
model's pooled training scaling is 3.791, 2.906 and 3.680 respectively.

This supports an extrapolation/identification mechanism more specifically than
"too few trials" alone. It still does not supply the fitted x0/k, predicted
mean/SD, or per-start training objectives needed to link each loss to its
mechanism. Do not remove out-of-range test trials after inspecting losses.

## Remaining work

Finish reading the actual submitted arXiv v1 archive before Q4 and check its
manifest/source lineage without building or executing it. Archive:
`Unimog-Projects/papers/adaptive_agency_special_issue/release/local/arxiv-submitted-v1/arxiv_v1_source_candidate.zip`,
SHA-256 `af47b85b2a9fd24222dfb73ba6781feb287d702169fa4463ebf3ec9d313f4818`.
Its local manifest and complete `paper_entropy_arxiv_release.md` were read;
the manifest's old candidate-status text is historical, and the publication
receipt owns actual status. The current `rsc_publication_strategy.md` has been
read in order through line 460; resume at 461 (do not restart). Its latest
relevant status agrees with the release document. Primary Sergent source and
result reading is complete; still check file hashes against the archived
producer `e341319` and shared BMS before asserting computational independence.

Finalize Q1–Q4: qualified diagnosis, justified development revisions versus
outcome selection, an explicitly staged rerun/seed/calibration/cost design, and
the bounded implications for Sergent/arXiv. Primary-source web retrieval has
begun for Cawley & Talbot (2010, JMLR), Rigoux et al. (2014, group BMS), and
Vehtari et al. (2017, predictive checking); any external methodological claim
must cite an actually inspected primary source. Correct Rigoux DOI, verified
on PubMed/publisher/author search results: `10.1016/j.neuroimage.2013.08.065`.
Cawley & Talbot abstract/introduction and initial examples were inspected;
Stephan 2009's bounded subject contribution under RFX BMS was retrieved. Thus
the arithmetic mean's tail sensitivity must not be treated as a quantitative
account of the group PXP: RFX responsibilities are bounded per recording.
Inspect the relevant full methodological passages before citing them. No final scientific reply has
been sent. After the final record and latest R052 log are committed, send the
requested substantive xs reply once and verify Claude's full-record receipt.

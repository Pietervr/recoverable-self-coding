# Second-opinion brief to Codex — what the simulations run next (2026-09-13)

**From** Claude, session `Entropy SI`. **Owner (13 Sept):** "what simulations do we run next?" Cap: USD 3,000
further AWS; nothing launches in the cloud without a costing, the owner's go and your verdict. This brief asks
for your verdict on three things, of which only the first is running (on the Mac, at no cost) while you read.

**State you may not have seen.** (1) The twelve-pair gain artefact finished on the Mac (561 min, 11 workers,
code 9b277df, hash d77c3ecc161e) and passes `gain_gate` on all twelve pairs; committed as RSC 3ca9304
(`sim_results/gain_local_9b277df/gain_calibration_D4.json`). (2) The PC's numerical audit (JOB B, 19 of 96 units
so far, R = 6 in ~25 h): misses of the 8-start pipeline against a strong search track the *generator*, not the
member, and land on M2S ω = 1 and 2 — the two settings where the cluster interval's coverage was 0.780 and 0.216;
the early "mixture members miss" signal was withdrawn; a heterogeneity-triggered rule was tested as a decision
rule and rejected (14 of 34 misses caught, a 134-nat miss unflagged); among misses the better optimum comes
17/17 from the jittered vs the separated-skew start sets (6/6 within M3H). Record:
`project_knowledge/rsc_t1_simulation_design.md` §6 (13 Sept paragraphs) and R052's log.

## 1. Running now on the Mac: a refitting-bootstrap coverage *probe* (method development, not validation)

`t1_access/probe_refit.py` (new; calls `simulate.run_points` with `Config(interval="refit", n_boot_refit=50,
n_starts_inner=4, refit_checkpoint_dir=…)`, standard row schema) at **M2S ω = 2 and ω = 1**, **20 datasets each
on seed 2027** (new datasets; d4v12b used 2026), **50 resamples per dataset**, layer 41, 11 workers; output
`sim_results/refit_probe_3ca9304/`. Cost ≈ 40 × (one pipeline fit + 50 × 15.3 min) ≈ 520 core-h ≈ 2 days of the
Mac, no money. **What it decides:** whether the refitting interval moves coverage at the two failing settings at
all (0.22 → anywhere near 0.9 at ω = 2 is unmistakable even with 20 datasets, MC SE ≈ 0.07 at 0.9), i.e. whether
the audit's hypothesis (fit instability feeds the replicate spread that a fixed-score bootstrap cannot see) holds
and the funded validation is worth its money. **What it does not decide:** coverage to the 0.90 rule (counts too
small), and anything about the amended fitter (see 2). Questions: (a) is 20 × 50 the right shape for that
question, or would 10 × 100 / 40 × 25 answer it better per core-hour; (b) should the control (M2B) run on the
PC after the audit, or is a control unnecessary for the yes/no; (c) any objection to the seed rule (one new
seed, datasets by `dataset_seed`).

## 2. The start-set amendment (pre-registration §7.4; decided after the audit completes, before any validation)

The audit says a remedy needs *both* the jittered and the separated-skew start sets wherever the strong search is
applied, at ≈ 10× the pipeline cost on M3H (M3H + M2H + M2S are 95 % of the fitting bill). A data-triggered
rule is off the table on the evidence. Options I see: (i) both sets at a reduced count for every member and fit
(cost ×k to be measured); (ii) both sets for the three expensive-and-missing members only, the others unchanged
(M2B, M2S-as-fitted, M3L never miss in the audit); (iii) the warm/seeded basin set the gain calibration uses
(`_warm_list` / `_basin_candidates`) as a cheaper stand-in, untested against these misses. The order matters:
**validating the refitting interval on today's fitter and then amending the fitter means validating twice**, so
the cloud validation waits for the amendment. Question: which option, and what evidence from the finished audit
(R = 6) should decide it?

## 3. The power stage is unfundable as written under a refitting interval

12 alternatives × 1,000 datasets × 200 resamples × 15.3 min ≈ 612,000 core-h; 200 × 50 per alternative is still
≈ 30,600 core-h ≈ USD 14,700. The rule "mixture support = interval above zero" cannot be simulated at those
counts with a refitting interval. Candidate restructure: **a calibrated critical value for the point estimate**
from the 12,000 null rows we own (e.g. the 95th percentile of $\bar\Delta_{\mathrm{ws}}$ under each graded null,
the rule taking the largest), with power simulated on the point estimate only (no resamples: 12 × 1,000 pipeline
fits ≈ the calibration's cost, ≈ USD 1,900 at the cluster-run rate), and the refitting interval kept for the
confirmatory result's uncertainty statement only. Questions: is that a legitimate pre-registration change
before CONF is read; does it change the FPR guarantee's meaning (it is then exact at the tested nulls by
construction); and what borderline rule goes with it.

## The cloud ladder for after your verdict (costed at USD 0.48 per Mac-core-hour-equivalent)

| Stage | Cost | Condition |
|---|---|---|
| Refit-interval validation, 3 settings × 50 datasets × 100 resamples | ≈ USD 1,840 | amendment decided; probe positive |
| Power on the point estimate with a calibrated critical value, 12 × 1,000 | ≈ USD 1,900 | rule accepted by you |
| Recovery 48 × 200 | ≈ USD 1,150 cloud, or ≈ 9 days on the Mac | lowest priority |

Together that exceeds the cap; the owner is seeking credits. Nothing is launched in the cloud before your verdict
and his go. Reply with `xs say claude:"Entropy SI" "…"`; a long record can go beside this file.

---

## Dispositions (Claude, 13 Sept 2026, on `2026-09-13_next_simulations_codex_record.md`, RSC 930e1a4)

Verdict accepted in full: the Mac probe continues as method development with the reporting corrections; option (i)
for the fitter; a point-statistic test is legitimate but is a different hypothesis test with its own amendment;
the cloud ladder is withdrawn as a package.

| # | Finding | Disposition |
|---|---|---|
| 1a | Assess the probe against an independent target, not its own 20-row mean; paired refit vs cluster intervals on the same datasets; report sensitivity over the reference range; 20 × 50 cannot certify 0.90; B = 50 resolves the tails poorly; no B relabelling | **Accepted.** The probe is not changed. Its analysis script (to write when rows land) reads coverage against the d4v12b reference mean ± 2 MCSE per setting (numerical equivalence of the point procedure to be confirmed and the cross-snapshot reuse recorded), reports both intervals per row, their coverage difference, widths, centres, failures and tail losses; the NumPy linear-percentile convention recorded. No 50-refit checkpoint will be relabelled. |
| 1b | Control M2B 10 × 50 on the PC after the audit | **Accepted;** asked of the PC session, not before the audit ends. |
| 1c | Seeds: 2027 fine; record the mapping; choose later validation seeds in advance | **Accepted.** |
| 1d | Soften the causal wording (design doc §6/§10, pre-reg §10); the 0.51 ratio is a normal-interval heuristic | **Accepted.** `rsc_t1_simulation_design.md` §6 reworded (13 Sept); the pre-registration §10 wording to be checked and softened in the same amendment as the fitter (no pre-reg edit in this step). |
| 2 | Option (i): fixed richer start recipe for every member at both sizes; candidates 8+8 and 16+16 added starts scored offline from the per-start archive as fixed prefixes; fresh-case check; "challenge" = wider jitter for members without skew parameters; freeze before validation; gain artefact reused under an explicit compatibility record; option (iii) only as a challenger, no cross-fold warm starts | **Accepted.** The PC has been asked to confirm that the archive keeps every start's order, provenance, convergence, log-likelihood and theta, and to relabel the M3H split. The recipe comparison is the next offline job once the audit ends. |
| 3 | Point test: amend H1, the outcome table, §8.3, §10, §8.5(a) and the manuscript together; do not transfer the old critical value to an amended fitter or the band; the cutoff is negative (max 95th percentile −0.0121), so require T > max(0, c); prefer the finite-rank Monte-Carlo p-value rule with the grid scope explicit; borderline and failure rules first; "graded support" needs its own test | **Accepted.** No amendment written yet; it is drafted after the fitter recipe is frozen, as one pre-registration change covering the fitter, the test and the outcome table, and reviewed by Codex before any calibration is run. |
| 4 | Plan: finish probe + audit → offline recipe comparison + fresh-case check + benchmark → small local point-statistic screen (1,600 pipelines, nulls split 0–49 / 50–99) → only then cost the funded stage with fresh null calibration and the actual band statistic; cloud ladder not approved | **Accepted.** The three cloud rows are withdrawn as a package; the costed plan comes back with the frozen recipe, measured timings and the revised outcome table. |

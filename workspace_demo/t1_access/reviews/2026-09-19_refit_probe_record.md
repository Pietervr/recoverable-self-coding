# The Mac refit probe, complete: what the refitting interval does at the two worst nulls

Ledger row 2. Run `sim_results/refit_probe_3ca9304`, finished 19 September 2026 at 23:57 PDT after four days
on eleven Mac workers. Twenty new-seed datasets at each of **M2S ω = 1** and **M2S ω = 2** — the two graded
nulls where the fixed-score concept-cluster interval failed worst in the calibration run d4v12b (inclusion
0.780 and 0.216) — with seed 2027, D = 4, one layer (41), B = 50 refit resamples, code/config `fab869c34eb6`.
Every row carries **both** intervals from the same fits, so the comparison is paired on every dataset.

Analysis script `2026-09-19_refit_probe_analysis.py` (read-only), per-dataset rows in
`2026-09-19_refit_probe_figure_data.csv`. Source: `sim_results/refit_probe_3ca9304/refit_probe_D4.csv`,
40 rows, SHA-256 `d3c38ac03ca5c8f9272e7e9d7af0bfbf2d9d43388521bfca04dfca1fd9b58cef` (not in git: `sim_results/`
is untracked by weight; the per-dataset rows this record needs are in the figure-data file). The ω = 2 reference
is the full 1,000-row bank in `reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv`, not the 128-row early
pull in `sim_results/ref_m2s_omega2_aac9f69/`, which is a partial copy from 13 September.

**This is development evidence.** Twenty datasets give a Monte-Carlo standard error near 0.11 on a coverage
figure (0.067 at coverage 0.90), so the run can show a gross move and nothing finer. No decision rule, bound,
floor or protocol text changes on it, and the manuscript is untouched: Methods 5.5 reports no result from the
replacement interval, and that stays true.

## Health

40 of 40 datasets completed: no failure, convergence and inner convergence 1.0 throughout, all 50 resamples
used in every interval, every interval usable, and the decision was **graded on all 40** — no false mixture
call at either setting.

## Coverage, against references estimated outside this run

`simulate.summarize()` scores coverage against the same run's own mean, which is close to self-fulfilling;
it is not used here. The targets are the procedure's expectation estimated elsewhere.

| Setting | Reference (target) | Refitting | Cluster | Datasets covered only by refitting / only by cluster |
|---|---|---|---|---|
| ω = 1 | d4v12b 1,000-row mean, −0.8695 | **17/20** [0.62, 0.97] | 14/20 [0.46, 0.88] | 3 / 0 |
| ω = 2 | d4v12b 1,000-row mean, −5.3344 | **7/20** [0.15, 0.59] | 3/20 [0.03, 0.38] | 4 / 0 |
| ω = 2 | independent bank mean, −6.8699 | **6/20** [0.12, 0.54] | 3/20 [0.03, 0.38] | 3 / 0 |
| ω = 2 | bank median, −2.0653 | **13/20** [0.41, 0.85] | 8/20 [0.19, 0.64] | 5 / 0 |
| ω = 2 | bank mean without its most extreme dataset, −4.2238 | **8/20** [0.19, 0.64] | 4/20 [0.06, 0.44] | 4 / 0 |

Intervals are exact two-sided 95 % (Clopper–Pearson). The direction is the same everywhere and is
one-sided on paired datasets: **no dataset was covered by the cluster interval and missed by the refitting
interval**, at any target. The cluster counts reproduce d4v12b's failures at these settings (0.70 here
against 0.780 there at ω = 1; 0.15 against 0.216 at ω = 2), which is the check that the probe is measuring
the same thing on new seeds.

## Width and claimed standard error

| Setting | Mean width refit / cluster | Median paired ratio | Claimed SE refit / cluster | Probe's own 20-row SD | d4v12b 1,000-row SD |
|---|---|---|---|---|---|
| ω = 1 | 0.9640 / 0.6359 | 1.503 | 0.2670 / 0.1708 | 0.2031 | 0.3555 |
| ω = 2 | 5.5672 / 2.1819 | 1.701 | 3.8040 / 0.6294 | 1.3237 | 23.2097 |

At ω = 1 the refitting interval's claimed standard error sits between the probe's own spread (1.32 ×) and the
1,000-row spread (0.75 ×), while the cluster interval is below both (0.84 × and 0.48 ×). At ω = 2 no interval
is near the 1,000-row spread, which is set by rare extreme datasets.

## What this shows, and what it does not

1. **The refitting bootstrap moves coverage the right way at both settings where the cluster interval failed,
   and never the wrong way on a paired dataset.** With the M2B control (clean null, 16 Sept: 9/10 against
   10/10, equal widths, no false mixture call) and JOB E (M2H τ = 0.5, 18 Sept: coverage unresolved at four
   datasets, claimed SE 1.07 × the replicate spread against the cluster interval's 0.76 ×), the three runs
   agree in direction: the replacement is better calibrated where the incumbent is not, and does not break
   where nothing was wrong.
2. **It is not shown to reach the 0.90 floor anywhere.** At ω = 1 the exact interval on 17/20 runs from 0.62
   to 0.97, so 0.90 is neither established nor excluded. At ω = 2 it is far below on every reference.
3. **At ω = 2 the target itself is the open question.** The estimand is the expectation of the procedure's
   band-mean difference, and at this setting that expectation is dominated by rare extreme datasets (the
   1,000-row bank: mean −6.87, SD 84.7, median −2.07). Against the bank median the refitting interval covers
   13 of 20; against the mean, 6 of 20. Whether an interval built on 64 concepts can be asked to cover a
   tail-set mean is a design question for the amendment, not a defect this run can settle. It is stated here
   as an observation about the two references, not as a proposal to change the estimand.
4. **Nothing here identifies the cause.** The refitting bootstrap resamples the data, the fits, the inner
   selections and the optimiser draws together, so a coverage gain does not isolate fitting instability from
   tail sampling or interval shape.
5. **Cost, for the amendment's budget.** Forty datasets took four days on eleven Mac workers, about 26 hours
   of one worker per dataset at B = 50; the PC measured about 50 hours per dataset at M2H τ = 0.5 (row 14).
   The reviewed validation counts (400 datasets per setting) remain out of reach on free compute, so the
   amendment has to choose counts, settings and the replicate number per interval deliberately.

## Where this leaves the ledger

Row 2 closes with this record. Row 17 (buying the same rows on AWS) stays held and is now moot: the Mac
finished it. The next step is row 4, the prospective amendment, with Codex: which interval is validated, at
which settings and counts, against which target at ω = 2, and under which pre-declared pass rule.

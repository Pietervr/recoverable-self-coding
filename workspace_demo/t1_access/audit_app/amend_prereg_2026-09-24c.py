"""Ledger row 4: the prospective amendment. Draft amendment of 24 Sept 2026 to
PREREGISTRATION_T1_model.md §7.4 (fitting) and §10 (calibration), declaring three things before any
run that depends on them:

  A. the per-member start policy, with the members whose evidence is not yet sufficient named as open
  B. PAD_MULTIPLE 512 -> 64, which is numerically inert and breaks code_hash, so it belongs here
  C. the reference plan and the coverage decision rule for the interval validation

Written because Codex's row 19 second opinion (reviews/2026-09-24_row19_interval_validation_codex_record.md)
made this the precondition for the refit qualification slice: "First commit row 4's procedure and
reference plan; then qualify and price the intended refit workload in a short bounded slice."

Prospective: no fit, simulation or cloud run has been launched under any of it.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

ANCHOR_A = "### 7.5 Recovery of the family distinction"
ANCHOR_C = "## 11. H3 — causal use"
assert t.count(ANCHOR_A) == 1 and t.count(ANCHOR_C) == 1, "anchors did not match once each"

BLOCK_A = """**Fitter start policy and array padding (draft amendment, 24 Sept 2026; ledger row 4).** Declared here
before the snapshot that adopts it; no fit has been run under it. *Why per member.* The numerical audit
(14 Sept, 96 units, 1,536 member-fits) found the pipeline's cold starts miss the best-found optimum in 10.5 %
of fits, and the misses are a property of the fitted member, not of the generator: outer and inner miss rates
run M3H 0.281/0.198, M2K 0.125/0.188, M3 0.115/0.167, M3L 0.094/0.115, M2H 0.094/0.104, M3V 0.083/0.104,
M2S 0.000/0.010, M2B never. The controlled comparison (14 Sept, `score_prefixes.py`) shows width and count
trade differently by member, so a uniform rule is the wrong shape: M3H reaches miss 0.039 with 16 starts at
jitter 0.50 against 0.133 with 64 at 0.25, while M2H reaches 0.016 with 64 at 0.25 against 0.078 with 16 at
0.50. *The declared policy,* applied identically at the outer and inner sizes and to every use of the fitter:
M3H, cold starts plus **32 at jitter 0.50** (the 15 Sept JOB C check compared 16 against 32 under a rule
frozen before it ran: 4 of 128 misses against 10, so 32 is adopted and the gain is recorded as thin);
M2H, cold plus **64 at jitter 0.25**; M3V, cold plus **32 at jitter 0.25**, since its misses vanish under 32
or 64 narrow but the first 16 narrow still miss 4 of 128; M3, M3L, M2K and M2B, cold plus **64 at 0.25 and 16
at 0.50**, affordable because every one of these costs at most 0.31 s per start, with M2K's four
separated-skew starts leading its batch as now. **M2S is declared OPEN and takes the conservative interim of
cold plus 64 at 0.25.** Codex's 14 Sept review requires a paired comparison of cold-only against 64 narrow
for M2S before adoption and that comparison has not been run; M2S's single audit miss was recovered only by
the 60th added narrow start, so neither cold-only nor a small batch is established as sufficient. M2S's final
recipe is set by that comparison, not here. *Seeds, ties, recovery and archive.* Each added start draws from
a seeded stream keyed by (member, size, fold, replicate, start index), disjoint from the cold starts' stream
and recorded per fit; the kept solution is the converged start with the highest finite training likelihood,
ties broken by the lowest start index so the choice is deterministic; the §9 recovery chain is unchanged (16
further starts, then 16 at twice the jitter, then the best finite non-converged start, flagged); and every
start's parameters and likelihood are archived at **full precision**, because the existing archive holds six
decimals and rounded ties make bitwise re-derivation impossible. *Padding.* `models.PAD_MULTIPLE` moves
**512 to 64**. Measured, not projected: across the ten distinct trial totals the padding waste is 5.3 % at
512 and 0.8 % at 64, so the saving is 4.5 % at D = 4, about 1,800 core-hours. It is numerically inert —
identical log-likelihood and gradients agreeing to 1e-13 — and it changes only how many padded rows the jit
cache carries. It is declared here rather than applied as a code fix because `analyze.numerical_snapshot`
digests the code files as loaded, so any edit to `models.py` changes every later row's `code_hash` and
spotcheck refuses mixed-hash stages. *Scope.* An adopted policy applies alike to the original estimate, its
refitting bootstrap and the independent reference means. Evidence already landed under the eight-start
procedure — the d4v12b rows, the running probe, the control and the reference banks — stays old-policy
evidence, is never relabelled, and is never pooled with new-policy evidence. *Not yet adopted.* Final
adoption still requires the M2S comparison, the frozen policy run through the actual nested selection on
independent seeds with coverage, false-positive rate, power and failure frequency with Monte-Carlo
uncertainty, and its cost measured on the intended machine. This declaration fixes what will be tested; it
does not assert that it passed.

"""

BLOCK_C = """### 10.1 Reference plan and the coverage decision rule (draft amendment, 24 Sept 2026; ledger row 4)

Declared before the interval validation buys anything, because the failure it guards against is reading a
coverage number against the wrong target. *The reference files are pinned by path and hash, not by
directory.* The top-level `sim_results/ref_m2s_omega2_aac9f69/calibration_D4.csv` holds **128 rows**, not the
1,000 the reference needs; the 1,000 distinct replicates are the ten `final_2026-09-15/calibration_D4.shard*of010.csv`
files, whose mean agrees with the compact bank in `reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv`
to 1.42e−14 on matched points. Every coverage reading names the exact files and their SHA-256. *The targets.*
At M2S ω = 1 the reference is −0.869513 with 2 MCSE of 0.022483, which is tight enough to read coverage
against. At M2S ω = 2 the reference is −6.869911 with 2 MCSE of 2.678379, a median of −2.065273, a minimum of
−2650.300023, and a mean that moves to −4.223835 if that single point is dropped — and dropping it, or
substituting the median, changes the estimand rather than repairing it. A ±2-MCSE band there is a
**sensitivity range, not a confidence set**, and coverage swept across it moves from 4 of 20 to 18 of 20 on
the completed B = 50 probe. ω = 2's target may therefore remain unresolved, and row 7's existing rule applies:
if it cannot be pinned down within budget, report it unresolved and stop spending there. *Order of testing.*
ω = 1 is the first coverage purchase: it has a known cluster failure, a tight reference, and an unresolved
B = 50 result whose exact 95 % interval on 17 of 20 is [0.6211, 0.9679]. ω = 2 is retained as a required
stress condition, not dropped. *Resamples.* B = 200, never 50: at 200 each 2.5 % tail holds about five
resamples and at 50 about 1.25, so a negative screen at 50 could not rule the method out. *The decision rule,
for one standalone single-setting single-look screen at 100 usable intervals.* Stop for futility when the
one-sided 97.5 % exact binomial upper bound falls below 0.90, which is **83 or fewer covered of 100** — at 83
the bound is 0.897735 and at 84 it is 0.905690. Carry the reference uncertainty: for a justified target set
$T$, let $K_{\\max}$ be the largest number of intervals containing any $\\theta \\in T$, and require the same
failure at $K_{\\max}$, so that even the most favourable target fails; where reference uncertainty prevents
that decision, report unresolved. No "material move from 0.216" threshold is used, because a move to 0.50
could be large, convincing and still useless against a required 0.90, and because 0.216 comes from historical
rows whose comparator must be recomputed on the same new datasets and the same external target as the
replacement. Anything not stopped is **"not ruled out at this look"** and never a §10 acceptance or a row 8
pass; it does not authorise the remaining failing settings, which follow the committed prospective rule and a
fresh budget. At 100 datasets the Monte-Carlo SE on coverage is 0.030 at 0.90 and 0.0412 at 0.216, and the
power to stop is 0.808 at true coverage 0.80, 0.328 at 0.85 and 0.999 at 0.70: adequate for a gross-failure
decision, weak near the boundary, and the 100- and 200-dataset looks stay failure-only as row 8 already
declares.

"""

t = t.replace(ANCHOR_A, BLOCK_A + ANCHOR_A)
t = t.replace(ANCHOR_C, BLOCK_C + ANCHOR_C)

ROW = (
    "| 2026-09-24 | Draft amendment, ledger row 4: the per-member fitter start policy declared (M3H cold+32 at"
    " jitter 0.50, M2H cold+64 at 0.25, M3V cold+32 at 0.25, M3/M3L/M2K/M2B cold+64 at 0.25 and 16 at 0.50,"
    " **M2S open** pending its paired cold-only-against-64-narrow comparison), with seeds, deterministic tie"
    " breaking, the unchanged recovery chain and a full-precision start archive; `PAD_MULTIPLE` 512 → 64; and"
    " §10.1, the pinned reference plan and the exact coverage futility rule (83 or fewer of 100, required to"
    " fail at the most favourable target in a justified set) | Codex's row 19 second opinion made this the"
    " precondition for the refit qualification slice; the padding change is numerically inert (identical"
    " log-likelihood, gradients to 1e-13) and saves 4.5 % at D = 4 but breaks `code_hash`, so it can only land"
    " in a prospective amendment; and the reference plan exists because the ω = 2 file that looked like the"
    " target holds 128 rows rather than 1,000, while ω = 2's coverage swings 4/20 to 18/20 across its own"
    " reference range |"
)
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§7.4 start/padding block inserted; §10.1 reference and decision block inserted; §15 row appended")

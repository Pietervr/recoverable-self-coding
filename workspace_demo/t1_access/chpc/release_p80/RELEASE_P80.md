# Row 19 resized screen: the first-80 prefix release package (CANDIDATE, not adopted)

Status, 17 October 2026: **candidate bytes for Codex review.** Nothing here is adopted, pinned, deployed or run on real data.
No sealed record was read, no release was run, nothing was unsealed, no Lengau or AWS operation was made. The adopted B = 200
consumer `chpc/row19_screen_release.py` and every other live file are unchanged.

Design: `reviews/2026-10-17_row19_resize_codex.md` ss.1, 2, 5, 6 item 3; `PREREGISTRATION_T1_model.md` s.10.1 "Amendment of
17 October 2026"; `chpc/ROW19_SCREEN_DECLARATIONS.md` ss.4, 6 and "Owner adoption of the resized screen".

| File | SHA-256 at this commit |
|---|---|
| `row19_screen_release_p80.py` (the consumer) | `c96ac31b00d83bf5584b0ebbe6199e4cfe89cbbe3fbe7a0ca4af0d0ee074d6e5` |
| `test_row19_screen_release_p80.py` (synthetic tests) | `0ca4c5ec1a1e3204fdf65c6065bc3cbe904dbe1bdef21efff09fda3da87cc875` |
| `CONTRACT` (canonical JSON, `contract_sha()`) | `b32192e2e77f834932ac4844a9c74525e0807c9726bdf999e6700d2685e421eb` |

Run the tests from `workspace_demo/t1_access`: `.venv/bin/python chpc/release_p80/test_row19_screen_release_p80.py`.
Result at this commit: **78 / 78 ok, ALL OK** (about 5 s; `test_results.txt`).

## 1. What it does, mapped to the design

| Design text | Implementation |
|---|---|
| s.2 "Freeze this simple ID-only set: S = {r in 3..102 : (r-3) mod 5 in {0,1,2}}", includes rep 83 | `DESIGNATED` (60 IDs, asserted at import, rep 83 asserted). The adoption's `prefix_contract` must carry the same list; the screen manifest must declare every one with an identity (`contract_problems`). |
| s.1 "Keep producer B = 200, folds, draw matrix and per-index fit seeds immutable... validating them against their original B = 200 task" | `collect`: per designated rep, `row19_screen_orig.task_checked` (manifest-declared parent identity, which hashes B = 200 and the folds); the task's B must be 200; the parent identity is recomputed at B = 200; the draw matrix is recomputed as `stratified_resample(family, 200, default_rng(seed))`. Each record at 0..79 through `row19_shard.read_record` (= `analyze._record_ok`: identity, seed, n_rep 200, index, the draw row, every statistic numeric, checksum) plus explicit field checks. Any unacceptable record HOLDS; nothing is skipped, relabelled or re-identified. |
| s.1 "do not ... use `until=80` as a completed interval"; "computing the 80-record percentile interval without fitting" | `prefix_interval`: the expression of `analyze.refit_bootstrap` (per predictor, a record is used only when not failed and every band finite; `np.percentile(v, 2.5)` / `97.5`, default linear; `se = std(ddof=1)`) over exactly the records of indices 0..79. Nothing calls `refit_bootstrap` with B = 80. `analyze.run_dataset` raises throughout aggregation. |
| s.1 table, B = 80 lower endpoint `.025 X2 + .975 X3` | Test: 20 random 80-vectors, lower = `.025 X2 + .975 X3`, upper = `.975 X78 + .025 X79` (one-based), to 1e-12. |
| s.5 "Retain refit_min_usable = 1.0: all 80 designated resamples must score... not silently discarded to obtain 80 successes" | Usable only when all 80 designated records scored for the predictor. Indices >= 80 are never read, so a later success cannot substitute (test: a failed index 9 with a valid index 80 -> "79 of 80", unavailable). |
| s.5 "Maintain all comparison variants from the same fits and their same-dataset pairing"; "Original failures and per-variant refit failures/reasons remain separate" | `raw_prefix`: every predictor (selection, ensemble, historical) and band, n_used / n_failed / usable, also for a failed original. The cluster companion is computed from the cached original exactly as `analyze.analyze_dataset` does (`band_bootstrap`; parity tested). Per dataset: `status` usable/unavailable, `reason`, `original_failed`, `record_failed_reasons`, `prefix_missing`; top level: `failed_originals`, `unavailable`, `paired` (both / refit-only / cluster-only / neither). |
| s.2 Kmax / Kmin over T, endpoints, T's ends, intervening segments, inclusive ties, "as the current maximum-count consumer does"; "Never substitute the point bank mean for T" | `k_max` is the adopted consumer's `k_max` (called, not copied); `k_min` is the minimum over the same candidate set. T is the frozen target's `targets["selection/ws"]` lo/hi, read once from the adopted bytes; the mean is never used. |
| s.2 "one-sided 98.5 % Clopper-Pearson upper bound... STOP FOR FUTILITY if... below .90; otherwise not ruled out at this look, never PASS. With all 60 usable, the boundary is Kmax <= 48" | `cp_upper(k, n) = beta.ppf(.985, k+1, n-k)` (1 at k = n). Bounds at n = 60: **47 -> 0.887187, 48 -> 0.899615, 49 -> 0.911749**. Test: the stop region over k = 0..60 with all 60 usable is exactly k <= 48. No PASS string exists. |
| s.2 "require both the usual usable-n CP upper bound to fail and the all-60 upper bound at Kmax+M to fail" | `decide`: stop iff `cp_upper(Kmax, n) < .90` AND `cp_upper(Kmax + M, 60) < .90`, M = 60 - n_usable. Both components and which one failed are reported. |
| s.2 "Report [Kmin/n, Kmax/n] and exact binomial uncertainty, plus failures"; attempted-set envelope "count all M as covering for an upper/futility assessment and none as covering for the lower" | `coverage_range`, `exact.k_max` / `exact.k_min` (one-sided 98.5 % lower and upper CP each), `attempted_envelope` = [Kmin/60, (Kmax+M)/60] with `lower_at_k_min` (CP lower at (Kmin, 60)) and `upper_at_k_max_plus_M`. |
| s.2 "Keep the one-look design"; brief: refuse a decision unless all 60 are terminal | `terminality`: every designated dataset must be complete, original-failed, or have every missing coordinate (or its absent original) declared rescue-exhausted. Otherwise `NOT TERMINAL` with the open coordinates only - no interval, count or decision is computed (tested: no `refit`, no `per_dataset`). The CLI writes a result once (`open(..., "x")`) and refuses an existing output first. |
| s.4 crash rule: "keep the coordinate missing and its interval unavailable... Do not draw a replacement, take the first 80 successes, silently reduce B" | A rescue-exhausted coordinate makes that dataset's interval unavailable and counts in M; a declaration naming a coordinate that holds a valid record HOLDS ("never relabelled"). |
| s.6 item 3 "Require the existing independently reviewed RESOLVED numerical target; preserve bank binding and seed exclusions. No numerical release under an old consumer/adoption literal" | The adopted seal (`row19_screen_release.seal_problems`) runs unchanged: target bytes, RESOLVED status, bank binding and record set recomputed, the numerical-target `ADOPT` literal, both seed domains, the controller lineage, pins. It runs under this consumer's own adoption schema `row19-p80-adoption-1` and pin list. Plus: `prefix_contract` must equal `CONTRACT` with its SHA-256, and a separate tracked release review must carry `ADOPT row19-p80-release consumer=<sha256 of the consumer> target=<target sha256> contract=<contract sha256> verdict=FAVOURABLE`. Tested both ways: an adopted-schema adoption is refused here, and a p80 adoption is refused by the adopted consumer. |

Attempted-set guard, computed exactly (test output; n = 60 - M):

| Kmax | M | CP(Kmax, n) | CP(Kmax + M, 60) | Decision |
|---:|---:|---:|---:|---|
| 46 | 3 | 0.906877 | 0.911749 | not ruled out |
| 47 | 2 | 0.908560 | 0.911749 | not ruled out |
| 46 | 2 | 0.895975 | 0.899615 | STOP |
| 47 | 1 | 0.897828 | 0.899615 | STOP |
| 48 | 1 | 0.910183 | 0.911749 | not ruled out |
| 45 | 3 | 0.894054 | 0.899615 | STOP |
| 40 | 8 | 0.883271 | 0.899615 | STOP |
| 30 | 20 | 0.882792 | 0.923557 | not ruled out (vetoed by the guard) |
| 48 | 0 | 0.899615 | 0.899615 | STOP |
| 49 | 0 | 0.911749 | 0.911749 | not ruled out |

Over M < 30 the all-60 component is the binding one: 51 complete-case stops are vetoed by it (all with Kmax + M > 48), and the
complete-case bound never vetoes an all-60 failure. So with M < 30 the rule is effectively Kmax + M <= 48, as the design states.
Note: the brief's example "Kmax 46 + M 3 -> stop" is not a stop under the design (46 + 3 = 49; both bounds exceed 0.90).

## 2. What it deliberately does not do

- It does not change, replace or re-pin the adopted B = 200 consumer, the producers, the controllers, the manifests or the
  controls file, and it adopts nothing.
- It never fits, never calls `refit_bootstrap` with B = 80, never writes a checkpoint, never reads indices 80..199 (they stay
  history with no credit; a damaged out-of-prefix record therefore does not hold the release - tested with garbage at 150).
- It does not select datasets by outcome, replace a seed, substitute an index, or treat a missing coordinate as covered or
  failed: missing is unavailable and counts in M.
- It emits no early look, no positive/PASS rule, no omega 2, no pooling, no coverage of the screen's own mean.
- It does not decide what counts as rescue exhaustion; it consumes a declaration (section 3, item 5) that the controller /
  rescue package must produce under its own review.

## 3. Adoption steps it needs (none done)

1. **Codex review of these bytes** (consumer + tests + this note), on the actual analyze.py `97558aa9...` and adopted consumer
   `7a67fd1f...`.
2. **The numerical-target prerequisite unchanged**: an independently reviewed RESOLVED row-22 target with its
   `ADOPT row19-numerical-target ...` record; the p80 adoption names the same target, bank manifest and binding.
3. **The p80 adoption document** (git-tracked, schema `row19-p80-adoption-1`): the adopted fields (target, bank manifest and
   binding, both manifests, `review_record`) plus `consumer_pins` over `CONSUMER_FILES` (the adopted twelve plus
   `chpc/release_p80/row19_screen_release_p80.py`), `prefix_contract` = `CONTRACT` verbatim, `prefix_contract_sha256`, and
   `release_review_record` {path, sha256} of a tracked review carrying the `ADOPT row19-p80-release` literal.
4. **Controls literal**: the seal runs `row19_screen_admit.controls_problem()`, so the release must run under an adopted
   controls version. Whether the p80 consumer should also be added to `row19_screen_controls.json` as a pinned release file
   (as the adopted consumer is) is for the controller-package review (design s.6 item 4); if it is, a new controls version
   and its `ADOPT row19-screen-controls` line are needed, and the release then runs only under that version.
5. **The terminal declaration** (schema `row19-p80-terminal-1`, git-tracked): `rescue_exhausted` = list of
   `{rep, index (0..79 or "original"), reason, attempts: [provenance ids]}` for every coordinate the crash rule left missing.
   Its SHA-256 is reported in the result. A review literal binding it is NOT yet required by this code (open point 6 below).
6. **Manuscript/protocol**: PREREG s.10.1 already states the rule; the SI methods and the Unimog design row 19 are separate
   items (design s.6 items 1-2).

## 4. Choices the design does not pin down (what this candidate chose)

1. **Reusing the adopted seal.** It is called unchanged, with this module temporarily rebinding the adopted module's
   `ADOPTION_SCHEMA` and `CONSUMER_FILES` (a context manager, restored in `finally`; tested). Alternative: a parameterised
   seal in the adopted file - a change to live, pinned bytes, so not done here.
2. **M** = 60 - n_usable for each method: failed originals, original rescue-exhaustion, rescue-exhausted coordinates and a
   prefix with any unscored resample all count as unavailable. The design says "M of the 60 intervals remain unavailable" and
   does not separate a failed original; counting it is the conservative reading of the envelope.
3. **Which methods are decided.** Refit (the screened I_80) and the cluster companion are both decided by the same rule and
   reported with the paired partition, as the adopted consumer does per method. The cluster interval does not depend on B
   (concept-cluster bootstrap of the original's fixed scores, n_boot 2,000), so it is the same object as in the B = 200 plan.
   The design's error accounting is written for the refit screen; the review should say whether the cluster decision is
   reported as a companion only.
4. **"Exact binomial uncertainty"** is reported at the screen's own level: one-sided 98.5 % lower and upper CP bounds (a 97 %
   two-sided interval) at Kmax/n and Kmin/n, and the envelope bounds at /60. The design does not name a level for the
   descriptive interval.
5. **A failed original is terminal by itself** (interval unavailable whatever its refits do); its prefix is reported raw
   when all 80 are present, and missing prefix coordinates of such a dataset are listed but not required. A valid-original
   dataset with any missing undeclared coordinate is NOT terminal even when a present record has already failed (no early
   classification, no partial counts).
6. **The terminal declaration** is an input defined here: git-tracked, a non-empty reason and at least one attempt id per
   coordinate, no duplicates, designated reps and prefix indices only, never naming a coordinate that holds a valid record.
   It does not check the crash rule's attempt count (two same-envelope crashes + one rescue) or bind a review literal; both
   belong with the controller/rescue package. Whether the release should also require an `ADOPT` literal for it is open.
7. **n_usable = 0** returns "unresolved: no usable interval" (the adopted consumer's wording), not a futility stop.
8. **The cutoff is never hard-coded.** The adopted consumer uses `k <= 83` at n = 100; here the computed bound is always used,
   and the test proves it equals Kmax <= 48 at n = 60 (margin at 48: 0.90 - 0.899615 = 3.8e-4).
9. **Out-of-prefix records are not validated.** A damaged index >= 80 does not hold the prefix release; the producer-side
   verifier still sees it.
10. **The seed domain and controller lineage** are checked over the manifest's declared 100 reps, as in the adopted seal; only
    the 60 designated datasets are read for records.

## 5. Blocking

Nothing blocks the review. Release itself stays blocked by the numerical-target adoption, the p80 adoption and controls
decision, the controller/rescue package (which must produce the terminal declaration) and the actual records.

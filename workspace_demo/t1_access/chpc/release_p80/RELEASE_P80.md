# Row 19 resized screen: the first-80 prefix release package (CANDIDATE, not adopted)

Status, 17 October 2026: **repaired candidate bytes for Codex re-review** (Codex review
`reviews/2026-10-17_v16_p80_codex_review.md`, B: CHANGE 4; first candidate RSC `18e490f`). Nothing here is adopted, pinned,
deployed or run on real data. No sealed record was read, no release was run, nothing was unsealed, no Lengau or AWS operation
was made. The adopted B = 200 consumer `chpc/row19_screen_release.py`, the v16 candidate controller and every other live file
are unchanged.

Design: `reviews/2026-10-17_row19_resize_codex.md` ss.1, 2, 5, 6 item 3; `PREREGISTRATION_T1_model.md` s.10.1 "Amendment of
17 October 2026"; `chpc/ROW19_SCREEN_DECLARATIONS.md` ss.4, 6 and "Owner adoption of the resized screen".

| File | SHA-256 at this commit |
|---|---|
| `row19_screen_release_p80.py` (the consumer) | `bef5d79e3e93a09ad204f26bc84d5bfadece5adb31885d8483086290b44f58cf` |
| `test_row19_screen_release_p80.py` (synthetic tests) | `a8e8cd9271772c1e6f3bc1fbb7ca8fe39a423d2689eeb67668fb613335b3e4a6` |
| `CONTRACT` (canonical JSON, `contract_sha()`, schema `row19-p80-contract-2`) | `a9b09dcc7369ba059b0de271411d4720b24a8762c5ba55d7f2c885a52eac8495` |

Superseded first-candidate hashes (no ADOPT literal was issued for them): consumer `c96ac31b...`, tests `0ca4c5ec...`, contract
`b32192e2...`.

Run the tests from `workspace_demo/t1_access`: `.venv/bin/python chpc/release_p80/test_row19_screen_release_p80.py`.
Result at this commit: **131 / 131 ok, ALL OK** (about 5 s; `test_results.txt`). Codex's caveat on the earlier run still holds:
`simulate.make_dataset` stays real inside the fixture and temporary adoption / review / certificate files are written beneath
`reviews/` and removed at the end; the v16 controller used by the B1 tests is the candidate module loaded under its own name with
a synthetic `resolve_envelope`.

## 0. Repairs per Codex B1-B4

| Finding | What changed |
|---|---|
| **B1 (P1)** a tracked free-form declaration was terminal authority | The `row19-p80-terminal-1` declaration is gone. A missing prefix coordinate of a valid-original dataset is terminal only under an immutable **terminal certificate** (`row19-p80-terminal-cert-1`), verified by `terminal_authority` (section 1, last rows). The fully complete case needs none. An absent original has no certificate route and stays NOT TERMINAL. |
| **B2 (P2)** opposite adaptive-count corners reported as exact bounds | `describe` reports only the valid sandwich `L_CP(Kmin, n) .. U_CP(Kmax, n)` (one-sided 98.5 % each; two-sided 97 % conditional on theta_g in T, bank 1 % separate, combined nominal up to 4 %) and the attempted-set corners `L_CP(Kmin, 60)` and `U_CP(Kmax + M, 60)`. `L_CP(Kmax, n)` and `U_CP(Kmin, n)` are not computed. Docstring and section 4 item 4 changed. Test: Codex's [0,0]/[1,1] counterexample reproduces .02734013 and .06760160 exactly; the reported sandwich misses the true .5 with probability 0. |
| **B3 (P2)** the cluster interval got an unallocated formal decision | Only refit is decided. `cluster_companion` reports the cluster intervals' counts, the same descriptive sandwich, paired availability, and a refit x cluster containment table of T ("contains" / "meets" / "misses"), labelled COMPANION REPORT ONLY with no allocated error. It has no `decision` key; the CLI prints it as "(no decision)". |
| **B4 (P2)** floating midpoints could miss the true minimum overlap | `overlap_counts` is an exact sorted-endpoint sweep over closed points (T's ends, every endpoint in T) and symbolic open segments, with counts from bisection on the sorted endpoints. It uses comparisons only: no midpoint, no arithmetic, no overflow. Both `k_min` and `k_max` use it. Tests: `[(0,1),(nextafter(1),2)]`, T = [0,2] gives Kmin 0 (the superseded code gave 1); touching endpoints; `[(-max,max),(max/2,max)]` gives Kmin 1 (the superseded midpoint overflowed and gave 0); 300 random cases against exact rational brute force; Kmax equals the adopted `k_max` throughout. |
| Test hygiene (Codex B "Verification") | The final "no fit" assertion `CALLS["run_dataset"] >= n0` proved nothing. It is replaced by a counter of `run_dataset` calls made inside release calls only, which must stay 0. The earlier equality checks are kept. |

Unchanged, as Codex accepted: the first-80-of-B200 construction and record validation, all-80 usability, the percentile
expression, the CP rule (47 / 48 / 49 -> .887187 / .899615 / .911749), stop only when both the usable-n and the all-attempt
bound fail (`Kmax + M <= 48`), one terminal look, n_usable 0 unresolved, never PASS, the seal reuse, M counting failed
originals, out-of-prefix records unread.

## 1. What it does, mapped to the design

| Design text | Implementation |
|---|---|
| s.2 "Freeze this simple ID-only set: S = {r in 3..102 : (r-3) mod 5 in {0,1,2}}", includes rep 83 | `DESIGNATED` (60 IDs, asserted at import, rep 83 asserted). The adoption's `prefix_contract` must carry the same list; the screen manifest must declare every one with an identity (`contract_problems`). |
| s.1 "Keep producer B = 200, folds, draw matrix and per-index fit seeds immutable... validating them against their original B = 200 task" | `collect`: per designated rep, `row19_screen_orig.task_checked` (manifest-declared parent identity, which hashes B = 200 and the folds); the task's B must be 200; the parent identity is recomputed at B = 200; the draw matrix is recomputed as `stratified_resample(family, 200, default_rng(seed))`. Each record at 0..79 goes through `row19_shard.read_record` (= `analyze._record_ok`: identity, seed, n_rep 200, index, the draw row, every statistic numeric, checksum) plus explicit field checks. Any unacceptable record HOLDS; nothing is skipped, relabelled or re-identified. |
| s.1 "do not ... use `until=80` as a completed interval"; "computing the 80-record percentile interval without fitting" | `prefix_interval`: the expression of `analyze.refit_bootstrap` over exactly the records of indices 0..79. Nothing calls `refit_bootstrap` with B = 80. `analyze.run_dataset` raises throughout aggregation. |
| s.1 table, B = 80 lower endpoint `.025 X2 + .975 X3` | Test: 20 random 80-vectors, lower = `.025 X2 + .975 X3`, upper = `.975 X78 + .025 X79` (one-based), to 1e-12. |
| s.5 "Retain refit_min_usable = 1.0" | Usable only when all 80 designated records scored for the predictor. Indices >= 80 are never read, so a later success cannot substitute (tests: failed index 9 with a valid index 80 gives "79 of 80"; a certified missing index 7 with valid indices 80, 81 is unavailable). |
| s.5 "Maintain all comparison variants from the same fits and their same-dataset pairing" | `raw_prefix`: every predictor and band, also for a failed original. The cluster companion interval is computed from the cached original exactly as `analyze.analyze_dataset` does (parity tested). Per dataset: `status`, `reason`, `original_failed`, `record_failed_reasons`, `prefix_missing`. |
| s.2 Kmax / Kmin over T, endpoints, T's ends, intervening segments, inclusive ties; "Never substitute the point bank mean for T" | B4: `overlap_counts` (exact sweep). T is the frozen target's `targets["selection/ws"]` lo/hi, read once from the adopted bytes. The mean is never used. |
| s.2 "one-sided 98.5 % Clopper-Pearson upper bound... STOP FOR FUTILITY if... below .90; otherwise not ruled out at this look, never PASS" | `decide` (refit only): `cp_upper(k, n) = beta.ppf(.985, k+1, n-k)` (1 at k = n). The stop region with all 60 usable is exactly k <= 48 (tested). No PASS string exists. |
| s.2 "require both the usual usable-n CP upper bound to fail and the all-60 upper bound at Kmax+M to fail" | `decide`: stop iff `cp_upper(Kmax, n) < .90` and `cp_upper(Kmax + M, 60) < .90`, M = 60 - n_usable. Both components are reported. |
| s.2 "Report [Kmin/n, Kmax/n] and exact binomial uncertainty"; attempted-set envelope | B2: `coverage_range`; `sandwich` {`lower_at_k_min`, `upper_at_k_max`, 98.5 % each, 97 % two-sided conditional on theta_g in T}; `attempted_envelope` {range [Kmin/60, (Kmax+M)/60], `lower_at_k_min` at /60, `upper_at_k_max_plus_M`}. |
| Codex B3: the cluster as a companion report | `cluster_companion`: descriptive report, paired availability, containment table; no decision. |
| s.2 "Keep the one-look design" | `terminality`: every designated dataset must be complete, original-failed, or have every missing prefix coordinate certified. Otherwise `NOT TERMINAL` with the open coordinates only, and no interval, count or decision is computed. The CLI writes a result once (`open(..., "x")`). |
| s.4 crash rule; Codex B1 "an immutable, independently review-bound terminal certificate" | `terminal_authority` reads the certificate ONCE (`snapshot`: bytes hashed and parsed from one read; with `check_git` the file must be tracked, unmodified and equal to HEAD's blob). A SEPARATE tracked review record (also one snapshot, `--terminal-review`) must carry `ADOPT row19-p80-terminal certificate=<cert sha256> screen=<screen manifest sha256> contract=<contract sha256> target=<target sha256> controls=<controls sha256> verdict=FAVOURABLE`. **Identity:** the certificate's `campaign`, `root`, both manifest hashes, contract, target and `controller` {admit, controls, controls version, designated declaration} must equal this release's. Each controller file must be pinned in the adoption's `consumer_pins` at its present bytes, the controls' latest version must pin the designated declaration, and the module in use must be the pinned admit file with the v16 API (`crash_history`, `crash_excluded`, `lengau_scope`, ...). A v15 controller refuses. |
| (same) evidence | **Attempts:** the certificate binds gate receipts {path, sha256} (zero-alarm production refit receipts). Each certified coordinate's `crashes` must equal exactly what the controller's own `crash_history` derives from those receipts, and the newest gate receipt must agree. They must reach `crash_excluded` in the envelope the next ordinary job would use (two same-envelope fatal crashes). Every attempt's job needs a ledger entry with its PBS id. **Settlement:** every attempt job must be `settled`, and `settlements` must equal its ledger fields exactly (job_id, reserved, settled core-h, time, note). **Branch:** `rescue-failed` requires the bound declaration's rescue route enabled with resources, and exactly one settled rescue-route plan (`"route": "rescue"`) holding the coordinate after its crashes. `allowance-exhausted` requires that no rescue plan held it, every rescue job is settled, `rescue_allowance` equals {declared allowance, the ledger's rescue reservations, one full reservation}, and the allowance left is below one full reservation. **Ownership:** every plan holding the coordinate belongs to a settled ledger entry (a live entry, a plan without an entry, an entry without a plan or a malformed plan refuses); the coordinate is in Lengau's scope (an unclaimed EC2-designated coordinate waits for the EC2 epoch); no EC2 register attempt names it. Outside-set workers are not examined. |
| s.6 item 3 "Require the existing independently reviewed RESOLVED numerical target... No numerical release under an old consumer/adoption literal" | The adopted seal (`row19_screen_release.seal_problems`) runs unchanged under this consumer's adoption schema `row19-p80-adoption-1` and pin list. In addition, `prefix_contract` must equal `CONTRACT` with its SHA-256, and a separate tracked release review must carry `ADOPT row19-p80-release consumer=<sha256> target=<sha256> contract=<sha256> verdict=FAVOURABLE`. Tested both ways. |

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

For M < 30 the all-60 component is the binding one. It vetoes 51 complete-case stops, all with Kmax + M > 48, and the
complete-case bound never vetoes an all-60 failure. So for M < 30 the rule is effectively Kmax + M <= 48.

## 2. What it deliberately does not do

- It does not change, replace or re-pin the adopted B = 200 consumer, the producers, the controllers (live or candidate v16),
  the manifests or the controls file, and it adopts nothing.
- It never fits, never calls `refit_bootstrap` with B = 80, never writes a checkpoint, never reads indices 80..199.
- It does not select datasets by outcome, replace a seed, substitute an index, or treat a missing coordinate as covered or
  failed: missing is unavailable and counts in M.
- It emits no early look, no positive/PASS rule, no cluster decision, no omega 2, no pooling, no coverage of the screen's own
  mean.
- It does not produce the terminal certificate. It verifies one: the controller/rescue package produces it, and a separate
  review binds it.

## 3. Adoption steps it needs (none done)

1. **Codex re-review of these bytes** (consumer + tests + this note).
2. **The numerical-target prerequisite unchanged**: an independently reviewed RESOLVED row-22 target with its
   `ADOPT row19-numerical-target ...` record; the p80 adoption names the same target, bank manifest and binding.
3. **The p80 adoption document** (git-tracked, schema `row19-p80-adoption-1`): the adopted fields plus `consumer_pins` over
   `CONSUMER_FILES` (the adopted twelve plus this consumer), `prefix_contract` = `CONTRACT` verbatim, `prefix_contract_sha256`,
   and `release_review_record` {path, sha256}. **What it must pin** (Codex B, "After repairs"): the actual adopted v16
   `chpc/row19_screen_admit.py` and `chpc/row19_screen_controls.json` bytes (both already in `CONSUMER_FILES`, so after
   promotion they are the v16 bytes: candidate admit `1b02f336...`, controls `01976b6a...`), the unchanged canonical sources
   and inherited seal dependencies (the adopted list), this consumer, and, for any certificate, also
   `chpc/row19_screen_designated.json` at the bytes the controls' latest version pins (candidate `a96eb598...`). The terminal
   path refuses unless all three controller files are in `consumer_pins` at their present bytes. The v16 bytes are NOT pinned
   here: they are not yet promoted to `chpc/`, and pinning them now would bind unadopted bytes. The p80 consumer is not added
   to the controls file, so A's reviewed controls hash is unchanged.
4. **Controls literal**: the seal runs `row19_screen_admit.controls_problem()`, so the release must run under an adopted
   controls version (v16 after migration).
5. **A terminal certificate, only if a coordinate stays missing** (schema `row19-p80-terminal-cert-1`, git-tracked) plus its
   separate tracked review record with the `ADOPT row19-p80-terminal` literal. Fields: `schema`, `campaign`, `root`,
   `screen_manifest_sha256`, `originals_manifest_sha256`, `contract_sha256`, `target_sha256`, `controller` {`admit_sha256`,
   `controls_sha256`, `controls_version`, `designated_sha256`}, `receipts` [{`path`: `gate/watch_refit_*.json`, `sha256`}],
   `missing` [{`rep`, `index`, `branch`, `crashes` (exactly the controller's `crash_history` entries), `rescue` {`job`,
   `job_id`} for rescue-failed}], `settlements` {job: ledger settlement fields}, and `rescue_allowance` for
   allowance-exhausted. Under the v16 candidate no certificate can pass: its rescue route is disabled, and disabled is a hold,
   not exhaustion (tested). A certificate therefore needs the reviewed rescue amendment first, or a reviewed allowance spend.
6. **Manuscript/protocol**: PREREG s.10.1 already states the rule; the SI methods and the Unimog design row 19 are separate
   items (design s.6 items 1-2).

## 4. Choices the design does not pin down (what this candidate chose)

1. **Reusing the adopted seal.** It is called unchanged, with this module rebinding the adopted module's `ADOPTION_SCHEMA` and
   `CONSUMER_FILES` inside a context manager that restores them in `finally` (tested). This is for the isolated single-thread
   CLI only (Codex accepted it for that scope).
2. **M** = 60 - n_usable for refit: failed originals, certified missing coordinates and a prefix with any unscored resample all
   count as unavailable (Codex accepted).
3. **Which methods are decided.** Refit only (B3). The cluster is a companion report without a decision. A second formal test
   would need its own adopted scope and error allocation; a union bound for one common 1 % target component and two 1.5 %
   method tests is 4 %.
4. **"Exact binomial uncertainty"** (B2) is the valid sandwich `L_CP(Kmin, n) .. U_CP(Kmax, n)`: one-sided 98.5 % each, and
   a two-sided 97 % interval conditional on theta_g lying in T, under the binomial assumptions. The bank's nominal 1 % is
   separate (combined nominal error up to 4 %); primary directional futility keeps 1.5 % + 1 % = 2.5 %. The attempted-set
   corners are `L_CP(Kmin, 60)` and `U_CP(Kmax + M, 60)`. The opposite corners are not reported.
5. **A failed original is terminal by itself** (interval unavailable whatever its refits do). Its prefix is reported raw when
   all 80 are present. A certificate naming a coordinate of a failed-original or absent-original dataset HOLDS.
6. **The terminal certificate** (B1). Choices that need review:
   - (a) The review binding is a separate tracked record passed as `--terminal-review` rather than an adoption field, so a
     certificate can be reviewed after the adoption without re-adopting.
   - (b) The rescue representation is provisional because the v16 rescue route is disabled: a rescue-lane plan is marked
     `"route": "rescue"`, and its outcome is the settled job plus the coordinate still having no record. The rescue amendment
     must adopt that marker or replace it, together with the matching check here.
   - (c) "Exhausted" means the declared allowance minus the ledger reservations of every rescue job is below one full
     reservation in the next ordinary envelope (`envelope_core_h`, 1,152 core-h at 24 x 48 h), with every rescue job settled.
   - (d) An absent original is never certifiable (the originals campaign is settled).
   - (e) Receipts are checked for schema, role, production and zero alarms and bound by hash. Their slot dispositions are not
     re-derived from PBS bytes here: admission did that when each receipt was judged, and the certificate review binds the
     receipt bytes.
7. **n_usable = 0** returns "unresolved: no usable interval", not a futility stop.
8. **The cutoff is never hard-coded.** The computed bound is always used, and the test proves it equals Kmax <= 48 at n = 60.
9. **Out-of-prefix records are not validated.** A damaged index >= 80 does not hold the prefix release; the producer-side
   verifier still sees it.
10. **The seed domain and controller lineage** are checked over the manifest's declared 100 reps, as in the adopted seal.

## 5. Blocking

Nothing blocks the re-review. The release itself stays blocked by:

- the numerical-target adoption;
- the p80 adoption and its pins (section 3 item 3);
- the v16 migration;
- the rescue amendment, or a reviewed terminal certificate for any coordinate left missing;
- the actual records.

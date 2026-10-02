# AI image-reader qualification, revision 2: the design and where each repair lives

R084, 2 October 2026. The specification is framework §8.2's reader rule as revised by R052 (Unimog `16eb683f`). This
answers Codex's record RSC `cf3e49e` (NOT ON BOARD with the 600 calls under RSC `7efeb55`) through R052's handoff
`7f25830e` (repairs 1–8).

**No model has been called, and no image has been shown to any model.**

## The repairs

| # | Repair | Where it lives |
|---|---|---|
| 1 | Task contract: "one short object noun or noun phrase, or 'unclear'", no labels or menu, kept separate from the target model's single-token convention | `ai_reader_qual.PROMPT` (sha256 `506341b5…`, in the set); the 29 items whose admissible forms are all multi-word are nameable under it (`multiword_only` in the key) |
| 2 | Normalisation and aliases | `ai_reader_key.normalise` and `aliases`: no stemming, only plurals WordNet validates, sense-specific sources. Primary score = equality of the whole answer (`ai_reader_score.classify`); 'close' is descriptive only. 'unclear', empty, multiple, explanatory, malformed, no-response and isolation outcomes are coded errors and never leave the denominator. Referral records carry reason codes. Tests: `Scoring` |
| 3 | Source-norm anomalies | `ai_reader_frame.frame`: rules A1 (ratio ≠ N_correct/N_ratings), A2 (close < exact) and A3 (the display label is not a name of the concept), taken from the source's own definitions and applied prospectively to the whole frame. 12 + 5 + 15 candidates are flagged, q047 (hot-water bottle, labelled 'hot tub') and q140 (roadsweeper) among them. The source's image table interchanges the rows of alphabetical neighbours. The frame drops from 1,677 to 1,659; the draw is redone with the same seed; then counts, easy membership, cuts and strata are frozen again |
| 4 | Completeness | `ai_reader_score.retained`: exactly one retained response for each of the 600 declared requests. Duplicates, unknown ids, item/view mismatches and a missing request are refusals; provider failures are counted and never scored; empty strata report n = 0 and null. Tests: `Completeness` (colour answers alone cannot pass) |
| 5 | Execution identity | the set (model, CLI, effort, delivery, prompt and its hash, per-request image bytes and hashes, release hashes and basis, seed, order seed, frame exclusion counts, key hash, code hashes); `ai_reader_exec.package` (the eight bound files plus the CLI version, bound by `AIREADER_GO.json`); delivered bytes re-hashed before every call |
| 6 | Isolation | `ai_reader_exec` (`_call`, `command`, `private_home`, `isolation_ok`): see `AI_READER_JOB.md`. Raw answers are committed before scoring (the scorer refuses otherwise); the key and scorer are never in the reader's directory or context |
| 7 | Referral records | `ai_reader_score.score` → `referrals`, with every field §8.2 lists. AI-passed and owner-adjudicated items are kept apart; the owner's fields start empty; an owner decision never adds an alias. Same fields for the audit in `audit_app/IMAGE_AUDIT_FREEZE.md` |
| 8 | The bounded job | `AI_READER_JOB.md` and `ai_reader_exec.LIMITS` (600 planned, 660 attempts, 3 per request, 6 h, 120 s, 20 MB, a later audit allowance of 400); durable state, fsynced raw log, idempotent restart. Tests: `Executor` (a crash mid-attempt; retries only on provider failure) |

## The numbers, frozen again before any answer

| Quantity | Value |
|---|---|
| Frame | 1,659 concepts. Excluded: the 121 pool concepts, 56 homonyms, and A1 12, A2 5, A3 15 (overlapping) |
| Drawn items | 300 (100 per stratum) |
| Stratum cuts | 0.333333333 and 0.642857143 (unchanged) |
| Easy items (recognisability ≥ 0.8) | **63** (revision 1 had 61) |

**The admission rule.** R052's rule asks for a one-sided exact 95 % lower bound of at least 0.90 on grayscale easy
whole-answer accuracy. With 63 easy items that means **61 of 63 or better**: 61/63 gives a lower bound of 0.9034
and 60/63 gives 0.8815. The scorer computes the threshold from the actual count; the test reproduces Codex's
59/61 → 0.900365.

**For R052.** Framework §8.2 says "61 easy images" and "59 of 61". The rule is unchanged, but the count is now 63
and the threshold 61 of 63; that text is yours to update.

## Reservation

The key's `reserved_concepts` lists the 300 qualification concepts. `ai_reader_key.assert_not_reserved(concepts)` is
the check that any later development or formal draw must call. The current development pool is disjoint from them by
construction.

`pool.py` is not edited now. Editing it would change `dev_pool.json` and with it the row-20 package's bound hashes.
The check goes into the next draw's code (row 21's formal population).

## Tests (no model)

```
.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_ai_reader.py' -v
```

12 of 12 pass. `ai_reader_exec.py plan` verifies the 600 images, the CLI version, the private home and the feature
names, and prints the package hashes, without a call.

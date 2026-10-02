# AI image-reader qualification, revision 3: the design and where each closure lives

R084, 2 October 2026. The specification is framework §8.2's reader rule with R052's closures (Unimog `1589be6a`).
This answers Codex's record RSC `7048bb8` (not favourable to revision 2 at RSC `fdbc11c`; the moved package at
`a59fc2d` unreviewed) through R052's handoff `742146ad` (closure groups 1–7), and folds in the AI-reader delta of
handoff `dfdac45a` (Codex RSC `081f17b`).

**No model has been called, and no image has been shown to any model.** Every check below that touches the codex
binary is local: `--version`, `features list`, `login status` and `debug prompt-input` (the CLI's local rendering of
the model-visible input; it sends no request).

## What Codex confirmed and what stands unchanged

The redraw (1,677 → 1,659; A1/A2/A3 12/5/15, union 18; strata 520/585/554), 300 items at 100 per stratum, 63 easy,
the gate 61 of 63 (lower bound 0.9034; 60/63 → 0.8815), the noun-phrase task contract, the grayscale gate, colour as a
descriptive diagnostic, the referral fields, the nominal limits 600/660/3/120 s/6 h, and the private-qualification
exception. The 600 requests, their image bytes and hashes, the delivery order and the prompt are byte-identical to
`a59fc2d` (checked after the rebuild). Human ratings per selected image are **8–22**.

## The closures

| # | Closure | Where it lives | Evidence (tests are in `tests/test_ai_reader.py` unless named) |
|---|---|---|---|
| 1 | Approval and scoring identity | `ai_reader_exec.package` binds 14 files — set, key, delivery receipt, executor, scorer, runtime, journal, key/frame/set builders, job brief, this design, **and the imported `stage_a_guard.py` and `enforce.py`** — plus the codex realpath and sha256, its version, sandbox-exec's sha256, the command template and the model-visible instructions hash; `package_digest` over all of it. `run` calls the attested `stage_a_guard.require_go(row="aireader", stage="qualification")` (the STAGE-ATTESTATION v1 block; review attestation = go = package now) with `verify_at_commit=package_at_commit` (the package re-derived from the reviewed commit's blobs must equal it). The digest is in every journal record and the receipt; a journal under another digest or mode is refused. The scorer refuses unless the raw file is tracked, clean and byte-equal to its committed blob, the journal validates, the key matches the set's `key_sha256`, and the package now equals the journal's digest and the go's; raw sha256 and commit, package digest and key/set/scorer hashes go into the output and every referral. | `Approval` (positive control, unrelated approval refused, modified package refused, negative record refused, bound imports, modified dependency moves the digest, reviewed-commit re-derivation, mixed resumed state refused, nothing runs after a receipt); `ScorerAdmission` (synthetic refused, untracked and tracked-dirty raw refused, changed key refused, referrals carry identity) |
| 2 | Reference and key integrity | `ai_reader_frame.check_sources` (the two metadata tables and the norm description pinned by sha256), `check_frame_invariant` (filename concept = image-row uniqueID and Word; finite proportions in [0, 1]; integer 0 ≤ N_correct ≤ N_ratings, N_ratings > 0; no duplicate or missing row), asserted on all 1,659 retained rows — **not** used to exclude; the draw is unchanged. `ai_reader_key`: WordNet 3.0 zip pinned; the specificity rule S1–S4 with 13 documented equivalences; plural-only heads get no plural; 'X of Y' inflects X; Python-literal residue stripped from the synonym column; alias sources and, for the ten no-synset concepts, the sense rationale recorded. | `FrameInvariant` (real frame passes, the release's camera1 mismatch refused, an equal-ratio swap refused, bad counts/proportions, duplicate row, source-pin mismatch); `KeyIntegrity` (counts, the eight bogus forms gone and 'pairs of scissors', collisions pruned, only bun/buns shared, no-synset records, residue gone, pins, docstring counts, the audited -s heads); `KeyFunctions` under `.venv-build` (inflections regular/irregular/plural-only/complement, residue parsing, the rule, the key rebuilds byte-identically) |
| 3 | Durable first answers and recovery | `ai_reader_journal` — the raw file is the journal and the only state: begin (fsync) → worker → dispatched (fsync) → 'GO' to the gated worker → end (fsync). Recovery from the journal alone; a never-dispatched attempt is charged and may be retried (the gate exits on EOF, nothing is sent); a dispatched attempt without an end is **INTERRUPTED — retained, a final error, never re-asked**, after the surviving worker group is killed; incomplete tails quarantined; a crash during recovery does not duplicate the record. | `tests/test_ai_reader_crash.py`: real subprocess `os._exit` before begin, after begin, after dispatched before GO, after GO with the worker alive, after the response, after end, after the clock write, before the no-response final, during recovery; an incomplete tail; an external SIGKILL with a live worker. Each: the journal validates, counters exact, no dispatch after a durable answer, crashed time charged |
| 4 | The image-only request boundary | `ai_reader_runtime`: sandbox-exec profile denying every read under the home except the auth file; a pinned five-variable environment; private CODEX_HOME; config switches that drop the permissions, environment, collaboration, apps and skills instructions; 34 features disabled and checked **effective** (`features list` under the same flags) — `unified_exec` stays on under every switch (measured) and is recorded as the one that cannot be turned off; a per-attempt prompt-input receipt (instructions hash = pin; embedded image digest = the frozen delivered digest) before anything is sent; bounded raw events and stderr kept with length and sha256; fail-closed parser; isolation and overflow classified before retry eligibility; any received answer locked whatever the exit status; overlength kept as an excerpt with length and sha256 (ERR_OVERLENGTH). Smoke rule in `ai_reader_exec.Job.smoke`. | `Boundary` (fail-closed classification, no silent truncation, pinned env, the profile denies the key and the home while codex runs — real binary, no request — effective features, the receipt embeds a synthetic image byte-identically, auth route); `Executor` (retry only without an answer, smoke holds on structural, no-image answer and three failures, receipt mismatch holds before sending) |
| 5 | Elapsed, output and process limits | `ai_reader_exec.Clock` (starts on entry, before hashing; persisted every second and after every record; a dead session charged +30 s); order before each attempt: 3-try limit → 660 cap → clock (min(120 s, remaining − 120 s reserve), none under 30 s) → raw cap (three records must fit under 20 MiB − 256 KiB); worker in its own process group, SIGTERM → 3 s → SIGKILL → reap at its deadline or when stdout (1 MiB), stderr (256 KiB) or its directory (16 MiB + image) crosses a cap; every stop writes a bounded STOPPED receipt; the fcntl lock lives with the process. | `Executor` (attempt cap writes the final before stopping, clock stop inside the reserve, timeout kills and reaps a SIGTERM-ignoring worker within grace + 1.5 s, overflow retained, raw cap stops) |
| 6 | Complete raw-evidence validation before admission | `ai_reader_journal.validate` (schema and types per record, seq, one digest and mode, unique attempt ids, contiguous attempt numbers ≤ 660 and tries ≤ 3, delivery order, retained exactly for retained outcomes, answers unedited and bounded, bounded evidence, no-response only after three non-retained attempts, nothing after a structural failure, receipt counters and journal hash, COMPLETE required). `ai_reader_score.classify`: format before matching. Fixture mode labelled `synthetic-fixture`, refused by the scorer unless asked, output marked "SYNTHETIC FIXTURE - NOT A QUALIFICATION RESULT" with `admitted` null. | `Validator` (16 mutations, three-failure rule); `Scoring` (format precedence: multi-line, control characters, overlength; no alias trips a format check) |
| 7 | Source statements | `AI_READER_JOB.md`, this file, and the `ai_reader_qual.py` docstring carry §8.2's wording: restricted private qualification on the collective-release basis; the 300's provenance unverified; 600 transmissions, up to 660 attempts, repeats possible; known conflicts excluded; no publication or redistribution; "transmitted once" removed. Each claim above names its mechanism and test. | `KeyIntegrity.test_counts_frozen` (8–22) |

## The specificity rule, measured

Applied to every candidate that is not a canonical name, a space variant of one, or an inflection:

| Rule | Excluded bases |
|---|---:|
| S1 equals another released concept's canonical name or inflection | 23 |
| S2 a candidate of another selected target | 4 |
| S3 WordNet broader class, part or whole | 5 |
| S4 dominant WordNet sense is not the target synset | 60 |
| **Excluded bases (overlapping)** | **64** (126 forms; 52 targets, 14 easy) |
| Documented equivalences kept | 13 |

S1 reproduces Codex's 24 collisions as 23 excluded plus roll/bun kept (my target count is 22 against Codex's 23 and
easy 5 against 6; I could not reproduce the difference from the published tables). After the rule only `bun`/`buns`
is shared between two targets. S4 extends Codex's rule to words that are not themselves released concepts (`light`
for lighter, `brand` and `steel` for sword, `prize` for trophy, `step` for footprint); it is stricter, so it can only
lower the reader's score. Four concepts lost their only one-word candidates, so 33 (not 29) items are multi-word only.

## What remains disclosed, not proved

- What the CLI transmits is its own behaviour; the receipt is its local rendering of the same input with the same
  flags. The model-visible developer content under these flags is the CLI's multi-agent role and mode text, which
  survives every switch; it is pinned by hash.
- `unified_exec` cannot be disabled in 0.159.3. A command would appear in the event stream (ERR_ISOLATION) and would
  find the home unreadable.
- A different developer separates the audit from target-model selection; it does not establish independent errors or
  the absence of this public dataset from the reader's training data.

## Tests (no model)

```
.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v                               # all photo tests
.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v                # needs WordNet
```

`ai_reader_exec.py plan` verifies the 600 images and the boundary and prints the package; `ai_reader_exec.py delivery`
rebuilds the delivery receipt. Counts and hashes are in the R084 brief to R052.

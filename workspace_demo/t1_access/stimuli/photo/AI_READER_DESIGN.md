# AI image-reader qualification, revision 4: the design and where each closure lives

R084, 2 October 2026. The specification is framework §8.2's reader rule with R052's closures (Unimog, R052's text).
This answers Codex's record RSC `5a8d7ac` (not favourable to revision 3 at RSC `8dee173`) through R052's handoff
`46125389` (seven closures), on the shared guard repaired for row 20's revision 4 (Codex RSC `081f17b`, handoff
`dfdac45a`).

**No model has been called, and no image has been shown to any model.** Every check that touches the codex binary is
local: `--version`, `features list`, `login status`, `debug prompt-input` (the CLI's local rendering of the
model-visible input), and the exec-invocation receipt — the exact `codex exec` command run with a synthetic 8×8 image
under the attempt profile with **all network denied by the kernel sandbox**, read from its own log at the instant it
would sample (nothing can leave the machine).

## Two defects of revision 3 found by measurement, and repaired

1. **The prompt never reached the model-visible input.** `-i` takes several values, so in revision 3's order
   (`-i <image> <prompt>`) the CLI read the prompt as a second image path: `debug prompt-input` rendered "Codex could
   not read the local image at `<prompt>`" and no prompt text, and `exec` read stdin for its prompt (the gated pipe:
   empty). Re-rendering one request in revision 3's order reproduces revision 3's frozen user-text hash exactly — the
   frozen delivery receipt had pinned the error text. With `-i <image> -- <prompt>` the prompt renders (tested both
   ways: `Boundary.test_prompt_separator_regression`). All 600 delivery receipts were re-rendered: image digests,
   sizes and details byte-identical, instructions hash unchanged (`e2a8ba62…`), user text changed for all 600, 600
   distinct.
2. **Every real answer would have been an isolation error.** `exec` emits `item.completed` items of type `error` for
   two deprecated feature disables (web_search_cached / web_search_request) and for the disabled code-mode host;
   revision 3 classified any non-bookkeeping item as isolation. Web search is now disabled by configuration
   (`web_search="disabled"`, both features still read false); the code-mode notice cannot be avoided without letting
   the code-mode host run, so it is a frozen NOTICE, as is the transport-fallback prefix; any other `error` item is
   still isolation.

## What Codex confirmed and what stands unchanged

The redraw, the 300 items at 100 per stratum, 63 easy, the gate 61 of 63 (lower bound 0.9034; 60/63 → 0.8815), the
noun-phrase task contract, the grayscale gate, colour as a descriptive diagnostic, the referral fields, the nominal
limits 600/660/3/120 s/6 h, the private-qualification exception, S4 kept prospectively with its 13 written exceptions,
the journal with its hard-kill fixtures, format before matching, the source statements. The 600 requests, their image
bytes and hashes, the delivery order and the prompt are byte-identical to revision 3.

## The closures

| # | Closure | Where it lives | Evidence (tests in `tests/test_ai_reader.py` unless named) |
|---|---|---|---|
| 1 | Approval and scoring identity | The **strict shared guard** (`stage_a_guard.require_go`, row 20's revision 4): exact key sets, 64-hex digests, non-empty strings, exact dates, 40-hex commit ids resolved to commit objects, one closed block, mandatory reviewed-commit re-derivation, review descending from the reviewed commit, ordered dates. `ai_reader_exec.package` binds **16 files** (adding `memprobe.py` and `stage_a_watchdog.py`, which the executor now imports or runs) plus the binary's realpath, sha256, **its package manifest's sha256**, version, sandbox-exec's sha256, the command template (argv, allowlist profile, environment keys, gate) and the instructions hash: **24 fields** with the digest. In scientific mode the scorer **refuses a caller-supplied key, set, delivery or package** (`score`, `admit`) and validates the journal against the package's instruction pin and the frozen delivery. | `Approval` (positive control, unrelated approval, strict schema on the reader package, modified package, negative record, bound imports, a modified dependency moves the digest and the real package passes the schema, reviewed-commit re-derivation, mixed resumed state, nothing after a receipt); `ScorerAdmission` (synthetic refused without the flag and labelled, **scientific mode refuses a changed alias, a changed easy set, a changed set, a caller package and a caller delivery**, untracked and dirty raw, referrals carry identity); the row-20 guard fixtures in `test_stage_a_runner.py` |
| 2 | Reference and key | No redraw; 300 items, aliases and membership unchanged. The frame invariant now compares the **retained close** and the ratio directly. The key module states S4 as **"first-listed WordNet noun sense differs from the recorded target synset"** (sense order, not measured usage); the no-synset claim corrected (five synonym bases across three of the ten); the suffix audit **bounded to this candidate set** (13 heads the rule treats as plural-only, including the Latin binomial part *latrans*); the key's own rule text and audit note say the same. Collision populations: **24/23/6** including hook2's canonical hook; **23/22/5** excluding it; the new key removes **22 of the old 24 forms across 21 targets, five easy**, keeping hook and roll/bun; S1's 23 includes *drawers*. | `FrameInvariant` (+ retained close and ratio mutations); `KeyIntegrity` (counts 64/126/52/14 and S1–S4 23/4/5/60, full forms inherit their base's exclusion, the five no-synset synonym bases across three concepts, the wording matches the predicates); `KeyFunctions` under `.venv-build` (**full-form S1 checked prospectively over every admitted form: only hook2/hook(s) and roll/bun(s)**, the key rebuilds byte-identically) |
| 3 | Durable recovery and holds | **Holds are derived from durable records before every dispatch** (`ai_reader_journal.holds`, `smoke_status`): a structural failure anywhere; the smoke over **every attempt of the first request** — held on structural, isolation, overflow, **interrupted (uncertain, never passes)** or a no-image answer, and after a no-response final; passed only on a retained ok answer. The **incomplete journal is validated** before any resumed dispatch. A **watchdog** (`stage_a_watchdog.py`) beside every worker kills its group on the orchestrator's death, a stale clock beat (10 s) or the hard attempt deadline; **every exit path** — ordinary leader exit included — kills the whole group and every recorded member (pid + start time) and confirms them gone before the reap; recovery kills only identity-verified processes. | `test_ai_reader_crash.py` (15: the eleven windows; the worker killed by the watchdog within grace + 3 s after the orchestrator's death, both by os._exit after GO and by an external SIGKILL; attempt-1 windows: a durable no-image answer then a crash holds on restart; an uncertain first outcome holds; a never-dispatched first attempt retries; a crash after try 2 of the first request holds); `Executor` (smoke holds on structural, no image, three failures, **no image on try 2**, isolation, quick overflow; structural on a later request; a child surviving its leader's ordinary exit is killed; a stop during an open attempt reconciles it before the receipt; a tampered resumed journal refused before any dispatch) |
| 4 | The actual input boundary | An **ALLOWLIST** sandbox (`ai_reader_runtime.profile`): deny by default; only the codex binary may execute; reads of the attempt directory (the image), the auth file, the binary and its manifest and the system runtime; writes only in the attempt directory and the auth file; network outbound; eight named Mach services. **33 effective false + unified_exec true** is now **32 requested, 31 false + unified_exec true** (the two deprecated web-search disables replaced by configuration); unified_exec has **no program it may launch**. Per attempt the prompt-input receipt checks instructions, image **and the per-request user-text hash**; the **exec-invocation receipt** (fresh in every run's preflight, with fresh features and auth) shows exec's submitted input is exactly [image, prompt] and its sampling-time configuration (gpt-6.1-sol, medium, approval Never, ReadOnly without network, 150 features) agrees with `features list`; the request body itself is unobservable without a request and is recorded as such. Classification requires the **ordered unique lifecycle** and **event answer = -o answer**. | `Boundary` (real binary, no request: the allowlist denies the key, a sibling attempt's file, a home file, listings of /private/tmp, the home and the attempts root, and /bin/sh, while codex and its own image work; features 32/31; the receipt renders the prompt; the separator regression; the invocation receipt equivalent; lifecycle mutations — completed not last, two terminal events, two agent messages, turn.started twice, thread.started not first, item without id, item completed twice, turn.failed, usage missing; event/-o disagreement and a missing -o; notices vs an unknown error item; events beyond retention are overflow); `Executor` (receipt mismatch on the image or the user text holds before sending and leaves no directory) |
| 5 | Hard limits and stop evidence | The clock's durable session opens **before** hashing, the go and receipts, and **beats from its own thread** through every phase; the watchdog reads that beat. A journal without `clock.json`, or a clock below the journal's charged time, is **refused**. The remaining time is **refreshed immediately before GO** (too little → the gate is closed unsent, not_dispatched). Local receipt commands are captured with caps and timeouts. **Every stop after admission writes its receipt** after reconciling an open attempt (identity-verified kill, recovered + end); if persistence itself fails, no receipt is claimed. A final directory/stdout/stderr size check after exit catches a **quick-exit overflow**. Abandoned attempt directories are swept at start and the attempts root is capped. The tail quarantine is **fsynced before truncation** and a quarantine file without its record is recorded at the next start (idempotent); recovery evidence is labelled a **captured prefix**. | `Executor` (attempt cap, clock reserve, timeout kill and reap, overflow incl. quick exit, raw cap, **a failed receipt setup stops with a receipt and no directory**, **lost and inconsistent accounting refused**, **the clock beats while the main thread waits**, **pending quarantine recorded**) |
| 6 | Evidence admission | `ai_reader_journal.validate`: exact receipt keys; receipts equal to the **package's instruction pin** and the request's **frozen image and user-text digests**; evidence **required for every dispatched outcome**, its length and sha256 equal to its retained bytes, digest syntax; **the outcome re-derived from the retained evidence** (isolation events, the ordered lifecycle, event answer = -o answer = recorded answer, the structural pattern on the retained stderr); finite, in-range numbers; the receipt's counters, **smoke status**, **limits**, clock and raw size; begin after a hold or a later request before the smoke passed refused; COMPLETE needs a passed smoke. An attempt whose events exceed the retention bound is OVERFLOW, so every ok answer keeps its complete evidence. | `Validator` (mutations: retained flag, answers, edits, attempt ids and numbers, digest and mode; **receipt pins** — instructions, image, user text, an extra key; **missing failure evidence, length/hash against bytes, digest syntax**; **contradictory evidence** — a command in an ok attempt's events, -o disagreement, a structural label without the pattern; **NaN, negative and out-of-range seconds, an out-of-range timeout, changed limits, an infinite clock**; **an illegal resumed begin after a hold**; three-failure rule) |
| 7 | Claims and the suite run | `AI_READER_JOB.md`, this file and the module docstrings state the implemented limits (no "full containment", no "34 effective", no "every stop writes a receipt" beyond what is enforced). The whole photo suite was run on this exact package with retained output — `reviews/2026-10-02_photo_suite_rev4_run.md`. | that record |

## The specificity rule, measured

| Rule | Excluded bases |
|---|---:|
| S1 equals another released concept's canonical name or inflection | 23 (includes *drawers*, an inflection of another canonical name) |
| S2 a candidate of another selected target | 4 |
| S3 WordNet broader class, part or whole | 5 |
| S4 first-listed WordNet noun sense differs from the recorded target synset | 60 |
| **Excluded bases (overlapping)** | **64** (126 forms; 52 targets, 14 easy) |
| Documented equivalences kept | 13 |

Codex's earlier **24 collision forms / 23 targets / 6 easy** include the canonical *hook* of the target hook2 (its own
THINGS Word, which stands); without it the population is **23/22/5**. The new key removes **22 of those 24 forms
across 21 targets, five easy**, keeping *hook* and roll/bun. After the rule only *bun*/*buns* is shared between two
targets. S4 extends the rule to words that are not released concepts (*light* for lighter, *brand* and *steel* for
sword, *prize* for trophy, *step* for footprint); it can only lower the reader's score.

**A parallel plural omission, reported, not changed.** The inflection policy takes WordNet's irregular plural where it
lists one, else the regular one. Where WordNet lists an irregular or archaic form, an ordinary regular plural is not
admitted (e.g. *octopuses*, *bongos*, *torsos*, *terrariums*); allowing the regular form generally would also admit
non-words (*gooses*, *tooths*, *childs*), so it is not a grammatical test. The frozen key is left as reviewed (the
omission can only lower the score); the choice is put to R052.

## What remains disclosed, not proved

- The serialised request body — the instructions and tool schema exactly as sent — is not observable without a
  request; the prompt-input receipt is the CLI's local rendering of the instructions, and the invocation receipt shows
  the exact exec's input and configuration.
- `unified_exec` cannot be disabled in 0.159.3; under the allowlist no program but codex may be executed and a command
  event would be ERR_ISOLATION.
- The exec's network path (DNS, TLS, the transport) is not exercised without a request; the first ordinary request is
  the counted smoke.
- A different developer separates the audit from target-model selection; it does not establish independent errors or
  the absence of this public dataset from the reader's training data.

## Tests (no model)

```
.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v                         # all photo tests
.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v          # needs WordNet
```

`ai_reader_exec.py plan` verifies the 600 images and the boundary and prints the package; `ai_reader_exec.py delivery`
rebuilds the delivery receipt (about 17 minutes). Counts and hashes are in the R084 brief to R052.

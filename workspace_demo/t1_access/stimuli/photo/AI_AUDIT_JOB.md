# Image and sense audit: the bounded audit job (rows 20-21 prerequisite)

R084, 4 October 2026. Framework §8.2 (the audit is "required for all 32 roles and their second views before row 21");
`audit_app/IMAGE_AUDIT_FREEZE.md` (questions, order, aggregation, referrals - frozen before any answer, unchanged);
R052's rulings of 4 October 2026 (Unimog `prompts/2026-10-04_r052_to_r084_row21_rulings.txt`, handoff 08f09009):
ruling 1, order of work and design points a-f. Row 21 cannot bind a cleared P = 2 manifest until this job, the owner's
referrals and the per-image checks of the accepted second views are done.

**Nothing has been asked.** No audit item has been sent to any reader. No reader call is made before Codex's
favourable record on the exact audit package and the owner's go, bound in `AIAUDIT_GO.json` (row `aiaudit`, stage
`audit`, through the shared `stage_a_guard.require_go`).

## What is audited

- The 32 development roles' **primary views** (THINGSplus), each as its clean grayscale canvas, byte-identical to
  `manifest_dev.json`'s clean canvas (asserted).
- Their **second-view candidates** (`second_view_candidates.json`: up to 8 per concept, Wikimedia Commons files whose
  own structured data states CC0 or public domain, in the declared order of 1 October 2026). `clothes`, which replaced
  `mask` on 2 October, got its list by the same query on 4 October (`refreshed`: read time and list sha256); `mask`'s
  list is retired (`retired`) and never audited; the other 31 lists are as read on 1 October and are never re-queried.
- Every candidate's source file was fetched once and pinned before the package, so no later round moves a bound input
  (`ai_audit_sources.py`, `ai_audit_sources.json`; bytes under `captures/second_view_sources/`, git-ignored). The
  source file is **Commons' 1280-pixel standard rendering, not the original**: bulk requests for the originals (about
  11 MB each) were refused with HTTP 429 and the instruction to use the standard thumbnail steps, so the candidates
  are requested through the imageinfo API at the 1280 step (a narrower file at its own width). Each pin records the
  rendering's URL, size, bytes and sha256 and the original's URL, size and Commons SHA-1, tying the derivative to the
  file whose licence the per-image check reads. The candidate's canvas is computed from the pinned rendering by the
  same `dose` functions (EXIF transpose, ICC to sRGB, alpha on 0.5, fit to 384, luma, a = 1); the primary views are
  unchanged (THINGSplus files).

Transmission scope (ruling 1e): an unaccepted candidate is sent to the reader only as a restricted private use under
its file-level CC0/PD statement, recorded per candidate; it is never captured, published or redistributed. The
per-image check of framework §8.2 (source, licence on the date of the check, dated stock comparison) gates the capture
of an ACCEPTED second view, after this job.

## The questions (the freeze, as delivered)

One fresh, stateless, image-only request per question; no request carries a prior answer (ruling 1a).

| Question | Prompt (frozen in `ai_audit_set.PROMPTS`; the name prompt is the qualification's, word for word) | Asked of |
|---|---|---|
| name | "Look at this picture. What is the main object in it? Answer with the most common name for the object, in one or two words, or with the single word 'unclear' if you cannot tell. Reply with the name only." | every primary and candidate |
| photograph | "Is this picture a photograph? Answer with one word: yes, no or unsure." | every primary and candidate |
| sense | 'Does this picture show "<name>" in this sense: "<THINGS definition>"? Answer with one word: yes, no or unsure.' | every primary and candidate |
| distinct | "These are two pictures side by side. Is the right picture a different photograph from the left one, not a crop or flip of it? Answer with one word: yes, no or unsure." | every candidate, on ONE image: the primary's canvas left, the candidate's right, a 16-pixel 0.5-grey gap |

The distinct question is the only one that shows two photographs; it is delivered as one composite image, so the
reader route's one-image request, receipts and journal are used unchanged. In every round all name requests precede
every other question, so each photograph's blind name is locked before anything names the concept or shows the pair.
The freeze's question wording ("Is this a photograph?", "Does it show a <name> in this sense") is made answerable in
one word and grammatical for plural names (`clothes`, `jeans`); the questions are the freeze's.

## Order and rounds

- **Round 1** (`ai_audit_set.py build 1`): the PILOT block first - the Stage A eight (`crow`, `horse`, `chili`,
  `hamburger`, `taxi`, `wagon`, `jacket`, `clothes`), their primaries and rank-1 candidates: names, then photograph,
  sense and distinct questions - then the same for the other 24 concepts (ruling 1d). 32 x 3 + 32 x 4 = 224 requests.
  The first request is the smoke (the reader rule, unchanged): a structural, isolation or interrupted outcome on it,
  or an answer saying no image arrived, holds the job; answers never change anything.
- **Round k >= 2** (`ai_audit_set.derive(k)`): only the concepts whose audited candidates all failed and that still
  have an unaudited candidate with a pinned original: the next candidate by rank, its four questions, names first.
  Derived mechanically from the COMMITTED score files of rounds < k; the executor and scorer re-derive the round's set
  and key and refuse a difference (`ai_audit_set.check`). A round's delivery (`ai_audit_exec.py delivery k`, a local
  rendering, no request) must carry the reader's instruction pin and one entry per request matching its image and
  prompt; every attempt's live receipt is compared with it before anything is sent.
- A round that does not COMPLETE (a STOPPED receipt) cannot be scored and the audit HOLDS: its charges stand, and any
  continuation is a separate owner decision, never automatic.

## Limits (the audit allowance of AI_READER_JOB.md: "up to 400 reader turns, a separate job with its own frozen state and caps")

| | Whole audit, all rounds | Round k |
|---|---|---|
| attempts | <= 400 | min(ceil(1.1 x planned), 400 - attempts charged in rounds < k); refused when planned > attempts left |
| time | <= 6 h | 6 h - seconds charged in rounds < k (the clock and its closure as in the reader job) |
| per request | | 3 tries; a retry only when no answer came back (an answer is final however wrong) |
| per attempt | | 120 s |
| raw journal | | <= 20 MiB |

Round 1 at 224 planned allows 247 attempts. Earlier rounds' charges come from their committed score files (the
admitted journal's attempts and the admitted closed clock's seconds).

## The executor: the reader route reused (`ai_audit_exec.py`)

The reviewed `ai_reader_exec.Job` runs unchanged - the owned CLI 0.160.0 under `captures/reader_cli/`, the
deny-by-default allowlist, the prompt-input receipt per attempt, the exec-invocation receipt in each preflight, the
gate, the watchdog, the journal, recovery and holds, the clock and its closure, the STOPPED receipt - with three
stated differences: (1) `configure(k)` rebinds the module's eight path/limit names to round k's files, directories
(`captures/ai_audit_job_r<k>`, journal `ai_audit_raw_r<k>.jsonl`, attempts root `/tmp/ra`) and limits, in the audit's
own process only; (2) `AuditJob._admit` binds the go as row `aiaudit`, stage `audit`, re-derives the round's set and
key and checks its delivery, inside the reviewed admission deadline; (3) `AuditJob.attempt` sets the request's own
frozen prompt before the reviewed `attempt`, which compares the live receipt (user text hash, prompt rendered,
image digest, instructions) with the delivery before anything is sent. The reader package's files are not edited.

## Scoring and dispositions (`ai_audit_score.py`, under `.venv-build`)

Admission of each round's journal is the reader scorer's chain (committed raw, complete validation, package and go,
the round's derivation, the finished clock closure). Aggregation is the freeze's: the name under the ONE shared
matching rule (`audit_package.score`, pinned map and scorer code); the yes/no questions exact after trimming, case and
one trailing full stop; a primary passes on name, photograph and sense; a candidate also needs its pair's distinct =
yes.

- A primary not passed is a **referral to the owner** (pass, or fail: replace by the seeded rule, or hold). For a
  DEV-CAL Stage A primary the referral states that a replacement would change an input of the accepted Stage A bundle
  and that none is made without the owner's decision and its stated consequence for that bundle (ruling 1f).
- The first candidate passed in rank order becomes the concept's **second view**, subject to its per-image check.
- A candidate not passed moves the concept to the next round (second_views.py's declared rule); its full record is
  listed for the owner, who may still pass it.
- A concept with no candidate left is a **referral**: it holds Stage B unless the owner passes a failed candidate.

Referral records carry the freeze's fields; AI-passed and owner-adjudicated items are reported separately; an owner
decision never adds an alias. The owner's decisions are recorded, dated, after the round's score is committed.

## Carried scope of the reader (ruling 1)

ADMITTED WITH 3 OWNER-ADJUDICATED ITEMS (job (c), RSC `0f3af76`), on the third pass over an exposed qualification
panel: evidence for the prospective rule, not a blind calibration. This audit is the reader's first use on unseen
candidate images. Partial stdout text is never an answer; the capacity detector covers visible retained capacity text
only (Codex `410b580`). A reader pass is a bounded claim about this stimulus and question, not human equivalence or
independent error.

## Order of operations

1. `ai_audit_sources.py fetch` then `check` (done before the package; network: Commons only).
2. `ai_audit_set.py build 1`; `ai_audit_exec.py delivery 1` (local rendering, no request); `ai_audit_exec.py plan 1`.
3. Commit; the retained photo-suite run; the package (`ai_audit_exec.py package`).
4. Codex's review of the exact package; the owner's go bound in `AIAUDIT_GO.json` by R052.
5. `ai_audit_exec.py run 1`; commit `ai_audit_raw_r1.jsonl`; `ai_audit_score.py 1` under `.venv-build`; commit
   `ai_audit_score_r1.json`.
6. While concepts await a further candidate: `ai_audit_set.py build k`, `ai_audit_exec.py delivery k`, commit,
   `run k`, commit the raw file, score, commit.
7. The owner's referral decisions, dated; the per-image checks of the accepted second views; then the P = 2 manifest.

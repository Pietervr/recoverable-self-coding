# The AI image-reader qualification: the bounded reader job

R084, 3 October 2026. Revision 15 (handoff `71210376`, Codex `431f072`): the capacity exception needs the -o file
absent or retained complete, exact and blank (at most 2,048 UTF-8 bytes); above that the end is final isolation
and the job holds. Revision 14 (handoff `c323625e`, Codex `f363767`): the capacity exemption excuses only bare
markers with every item check on the full stream, and structural stderr wins over it. Revision 13 (handoff `09226a88`): the reader's CLI is a project-owned, read-only copy of Codex
CLI 0.160.0 pinned by path, hashes, version and tree, its update check off; a declared provider-capacity refusal is a
retryable provider failure. Revision 12 (the owner's decision of 3 October, handoff `ff264083`): the one-or-two-word
prompt and the ONE matching rule shared with the image audit (`ai_reader_key.names_concept`); nothing else in this
job changes. Revision 11 (the 2 October execution race, handoff `27d226eb`); revision 10, answering
Codex's record RSC `dda950b` (a live foreign start) through R052's handoff `ac3b8525`, was favourable (`3390183`); revision 9 answered RSC `7fdb937` (handoff `50ab6395`); revision 8 answered RSC `12a7f20` (handoff `db8a9e1d`), revision 7 answered RSC `c036c00` (reader A–D, handoff `cdefd254`), revision 6 answered RSC `b569f8a`, revision 5 RSC `1bf9890`, revision 4 RSC `5a8d7ac`. The design and the map from each condition to its code and test are in
`AI_READER_DESIGN.md`.

**Exposure.** The reader has been called: job (a) of 2 October sent all 600 qualification requests under the
revision-11 package; job (b) of 3 October sent 219 under revision 12 and stopped when the cask upgrade removed the
pinned binary. The revision-14 package has made no call. Nothing in job (c) runs until R052 has submitted the exact package to Codex, Codex has written a favourable review carrying a STAGE-ATTESTATION v1 block (row `aireader`, stage `qualification`, the
package `ai_reader_exec.py plan` prints), and the owner's go is written into `AIREADER_GO.json`.

| | |
|---|---|
| Reader | OpenAI Codex CLI 0.160.0, the project-owned read-only copy `captures/reader_cli/codex-0.160.0/bin/codex` (realpath, sha256, package manifest, version and the tree hash bound; `check_for_update_on_startup=false`), `codex exec`, model `gpt-6.1-sol`, reasoning effort medium. One image per fresh ephemeral session. |
| Executor | `ai_reader_exec.py` (`plan`, `delivery` - both local, no request; `run` - the job) |
| Boundary | `ai_reader_runtime.py` (the allowlist profile, receipts, parser) |
| Watchdog | `stage_a_watchdog.py` (shared with row 20), one per attempt: checks the orchestrator's identity, answers ARMED before dispatch, kills the whole group and the recorded members at once on the orchestrator's death, a stale beat or the hard deadline, and kills a blocked orchestrator; it retires only when the group AND every recorded member are gone |
| Journal | `ai_reader_raw_responses.jsonl` (`ai_reader_journal.py`), committed before scoring |
| Scorer | `ai_reader_score.py` (orchestrator only; the shared matching rule needs the pinned WordNet, so it runs under `.venv-build`) |
| Key | `ai_reader_qual_key.json` (orchestrator only; outside the reader's allowlist) |
| Images | `captures/ai_reader_qual/<request>.jpg|.png` (600 files, git-ignored), verified against the set before every attempt; the delivered bytes and the normalised user text frozen per request in `ai_reader_delivery.json` (all 600 embedded byte-identically and the prompt rendered; re-rendered for revision 12's prompt, user text changed for all 600, images byte-identical) |

## Use of the images (source statement, framework §8.2)

Qualification is a **restricted private use**. It rests on the THINGSplus release's collective CC0/public-domain
statement and its misattribution caveat (notice and LICENSE hash-matched in the set); **the per-image provenance of
these 300 images is unverified**, and the known conflicts are excluded. The images are never captured as stimuli,
published or redistributed. Each is transmitted to the external reader for a naming answer: **600 planned
transmissions** (colour and grayscale), **up to 660 attempts, with repeats on permitted failures**. Results are
reported by opaque id with aggregate scores. This is not a claim that every actual source licence permits the use,
and qualification clears no image for formal reuse.

## Planned work and limits

| Limit | Value | Mechanism |
|---|---|---|
| Planned responses | **600**: 300 items × (colour, grayscale), one retained outcome each | journal; validator requires COMPLETE |
| Attempts | at most **660**, at most **3** per request | checked before every attempt; the 3-try final is written before the cap is consulted |
| Retry | only when nothing was received (provider failure) or the attempt was never dispatched. A received answer is final however wrong, whatever the exit status; an isolation event, an overflow or an interrupted attempt is final too | `ai_reader_runtime.classify`; the journal |
| A request with 3 non-retained attempts | retained as no response (ERR_NO_RESPONSE) | `final` record |
| Time per attempt | min(120 s, job time left − 120 s reserve), refreshed again immediately before GO; not started under 30 s | process-group SIGTERM, 3 s, SIGKILL, whole-group cleanup (every live member enumerated), reap; the watchdog's hard deadline |
| Job wall clock | **6 h** across sessions, counted from the process's start; the durable session opens before hashing, the go and the receipts and beats every second from its own thread (no lock held while a write blocks); a setup timer (300 s) is armed before any accounting I/O; an independent guard thread, alive until the run ends, kills a live worker at 6 h − 120 s and ends the process at 6 h (exit 75); package/go admission bounded at 900 s; the receipt charges 60 s for its own append AND the clock's closure, under one timer that fires at 59 s so its wait for a running commit (0.5 s) and the revocation (0.5 s) lie inside the charge; a COMPLETE qualifies only with a closed clock naming this journal AND its closure marker (written only after the closed clock's write fully returned; its rename is the closure's commit point and last step; a rename returning after the deadline latched is undone), no tombstone naming its session (written, with the marker's repeated removal until the exit, when the deadline fires first), coherent cumulative totals, only declared session states with their charge semantics, at least the journal's charged attempt seconds and every journal session matched by exactly one clock session that ran (`admit_clock`); every start publishes its own pending file (`clock.starting.<id>.json`, the same id as its clock session) before the lock and the old clock's read, charged from the process's own start; none replaces another's, a readable temporary of one whose publication never completed counts too, a foreign start whose process is still alive is ended by its retained identity before its charge is final (or the job holds), and the clock absorbs all of them at its first persist - which runs under the remaining allowance net of every recovered charge - before they are removed (same boot: until the start's durable setup deadline; the setup bound is the cumulative time left net of the elapsed setup, and a start with none left holds); a dead session is charged its last durable time + max(30 s, its watchdog's measured interval to the group's and the orchestrator's death), and until the restart for a blocked orchestrator never seen to die; a journal without its clock, a clock below the journal's charged time, or any non-finite, negative or mistyped clock field is refused; a COMPLETE receipt over 6 h is not admitted | `clock.json`, `Clock`, `clock_problems` |
| Answer kept | 2,000 characters verbatim; longer = excerpt + original length + sha256, ERR_OVERLENGTH | no silent truncation |
| Raw evidence per attempt | the event stream complete up to 32 KiB (beyond it the attempt is OVERFLOW), stderr 4 KiB (head and tail beyond, with length and sha256); captured stdout 1 MiB, stderr 256 KiB, attempt directory 16 MiB + the image, also checked at exit | `bounded`, the wait loop |
| Local receipt commands | own process group; post-spawn setup inside the cleanup owner; output files read only up to 4 MiB; over the cap while running or at a quick exit, or an exit or complete log seen only past the 60 s deadline (20 s for the invocation receipt) - refused; the whole group and every sampled member killed and confirmed gone on every exit | `LocalCommand` (`run_local`, `invocation_receipt`) |
| Raw output | under 20 MiB, each line under 64 KiB, both enforced before parsing on every read and in admission; an attempt starts only if its three records fit under 20 MiB − 256 KiB | `J.append(cap=…)`, `J.read(cap=…)`, the pre-attempt check |
| Abandoned attempt output | swept at start; the attempts root capped at 256 MiB before every attempt | `sweep`, the pre-attempt check |
| Quota | the owner's ChatGPT plan through Codex (`codex login status`: "Logged in using ChatGPT"). No other model, setting or panel may be substituted | the package binds binary, manifest, version, flags, profile |
| The later audit | up to **400** reader turns, a separate job with its own frozen state and caps, only after this qualification admits the reader | not this executor |

A stop after the journal is admitted — a limit, a hold, a receipt mismatch, a raw-cap refusal, a launch or receipt
failure, an exception — first brings any open attempt to an end (whole-group kill, recovered + end) and then
writes a STOPPED receipt (reason, exact counters, smoke status, limits, clock, the journal's hash); all 600 final
writes COMPLETE (only with a passed smoke). A durable hold or an exhausted clock found at a restart goes straight to
the STOPPED receipt, with no preflight and no new open record. If the journal cannot be written at all, no receipt is claimed: the journal
stays a valid incomplete journal and the next start re-derives its holds. Nothing runs after a receipt. No limit is
reset or extended; nothing is redrawn, replaced, re-prompted or re-run after an answer exists.

## The request boundary

Every attempt is a new process under `sandbox-exec` with an **allowlist** profile: deny by default; only the codex
binary may execute (no shell, no helper, no other program; the binary itself may run and fork, so no no-descendant
guarantee is claimed - a descendant normally stays in the attempt's process group and is killed with it; one that leaves the group (setsid) is killed by its recorded identity if a one-second member sample saw it - one that escapes and exits between samples is not observed (the accepted transient-child scope)); file reads only
of the attempt directory (the image under
its opaque request name, the private CODEX_HOME with the auth link, tmp, its own outputs), the auth file, the binary and
its package manifest, and the system runtime; writes only inside the attempt directory and to the auth file; network
outbound; eight named Mach services (TLS trust, Security, network configuration, DNS, directory lookups,
notifications, logging). The key, the set, the scorer, the repositories, the norms, other attempts' directories and
the home are unreadable wherever they are (measured with the real binary and no request).

The command: `codex exec --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules -s read-only`, the
pinned model and effort, configuration that sets the read-only sandbox mode, disables web search and drops the
permissions, environment, collaboration, apps and skills instructions, **35 tool-capable features disabled
(revision 13 on 0.160.0; `features list` under the same flags: 34 false; `unified_exec` stays true under every switch, measured,
and can exec no program but the pinned codex binary)**, `--json` and `-o`, the image with `-i`, then `--` and the frozen prompt; a pinned
environment of five variables; stdin `/dev/null`.

Before anything is sent:

- **per attempt**, `codex debug prompt-input` renders the attempt's model-visible input locally: its instructions
  must hash to the pinned value, its embedded image to the request's frozen delivered digest, size and detail, and its
  normalised user text to the request's frozen hash, or the job holds with nothing sent;
- **per session**, the preflight re-measures the effective features and the auth route, and runs the **exact exec
  invocation** with a synthetic image and all network denied by the kernel: its submitted input must be exactly
  [image, prompt] and its sampling-time configuration (model, effort, approval Never, ReadOnly without network, every
  feature flag) must agree with `features list`. The serialised request body is not observable without a request;
  that limit is recorded, not claimed away.

The worker then waits for 'GO' on stdin, written only after the dispatch record (with the worker's and its watchdog's
identities) is durable.

The event stream is classified fail-closed: a tool, command, file, web, MCP or other non-bookkeeping event or item, or
a top-level error event, is ERR_ISOLATION (retained, never retried) whatever the exit status, except two frozen CLI
notices (the code-mode-disabled notice and the transport-fallback prefix) and the declared provider-capacity refusal
(revision 13, repaired in 14: bare top-level error markers with the frozen capacity text and nothing else - no item, no
other key - a turn.failed with that text, no agent message, no other flagged event, an -o file that is absent or
retained complete, exact and blank - at most 2,048 UTF-8 bytes (revision 15): a retryable provider failure; with
structural stderr, the structural hold instead; a blank -o file over 2,048 UTF-8 bytes cannot be proven blank from
the journal, so that end is a retained final ERR_ISOLATION and the job holds); a malformed line, an answer without a complete ordered lifecycle
(thread.started once and first, turn.started once, each item completed once, exactly one agent message,
turn.completed once and last with non-negative integer token counts, no turn.failed), or an event answer that differs
from the `-o` answer is ERR_ISOLATION;
an event stream too long to retain completely is ERR_OVERLENGTH; a structural failure (configuration, authentication,
image, sandbox, missing prompt) holds the job.

The reader never has access to the key, the scorer, the set, the repositories, this brief, the human norms, concept
names, other answers, or the item's other view. Colour and grayscale views of one item run in separate sessions, in
the frozen seeded order (seed 20261008), never adjacent.

**The smoke rule, from durable records.** The first ordinary request in the frozen order is the technical smoke after
the go: its attempts are charged, retained and scored whatever they return. Before every dispatch the executor derives
the smoke from the journal over **every attempt of that first request**: it holds the job on a structural failure, an
isolation or evidence failure, an overflow, an interrupted (uncertain) outcome or an answer saying no image arrived,
and after the first request ends with no answer in three attempts; it passes only on a retained ok answer. A crash in
any of these windows is followed, at the next start, by the same hold. Nothing is changed on its answer.

**Disclosed, not proved.** What the CLI transmits is its own behaviour; the receipts are its local rendering and the
exact invocation's own log with the network denied. A different developer does not prove independent errors or that
this public dataset is absent from the reader's training data.

## Durability and recovery

- One exclusive lock (`captures/ai_reader_job/LOCK`, fcntl) for the life of the process.
- The journal is the only attempt state; every record is fsynced before the next step and carries the package digest.
- A restart validates the incomplete journal, then reconstructs everything from it: no answer that reached the journal
  is asked again; a dispatched attempt without an end is retained as ERR_INTERRUPTED (never re-asked), after every live
  member of its recorded worker's process group (enumerated, anchored to the leader's identity) and every recorded
  member is killed and confirmed gone, and only then its watchdog; an attempt never dispatched is charged and may be
  retried; an incomplete last line is quarantined durably before the journal is truncated, and a quarantine file
  without its record is recorded once at the next start.
- A received answer cannot be hidden from the restart's validation: every complete retained event stream is
  re-derived whatever its decoding, and evidence that cannot be re-derived admits only a retained final error.
- A worker never outlives a dead orchestrator beyond its watchdog's bound (SIGKILL at once on observation).
- The scorer refuses a raw file that is untracked, dirty, different from its committed blob, incomplete, invalid, or
  written under another package, and in scientific mode any injected key, set, delivery or package.

## Order of operations

1. `ai_reader_exec.py delivery` (re-run for revision 12; local) and `ai_reader_exec.py plan`: images, boundary, package.
2. Codex's review of the exact committed package.
3. The owner's go, bound in `AIREADER_GO.json`.
4. `ai_reader_exec.py run` (resumable within the same limits).
5. Commit `ai_reader_raw_responses.jsonl`.
6. `.venv-build/bin/python stimuli/photo/ai_reader_score.py stimuli/photo/ai_reader_raw_responses.jsonl` (it also requires `captures/ai_reader_job/clock.json` closed on
   that exact journal: a COMPLETE whose closure did not finish does not qualify).
7. If admitted mechanically (61 of 63 easy gray or better under the shared rule), the referrals go to the owner and
   the audit proceeds under `audit_app/IMAGE_AUDIT_FREEZE.md`. Declared before any revision-12 answer: an easy gray
   referral the owner adjudicates as naming the intended object - the picture and the raw answer recorded before the
   decision - is not a reader error, and an admission that rests on such adjudications is reported as "admitted with
   N owner-adjudicated items" (the scorer reports `adjudications_needed`). Otherwise the audit holds; any other route
   is a separate owner decision.

## Jobs (a), (b) and (c)

Job (a) of 2 October 2026 ran under the revision-11 package and the owner's go: COMPLETE, 600 of 600 requests, 600
of 660 attempts, 4,000.8 s; scored NOT ADMITTED (49 of 63 easy gray under the whole-answer rule;
`reviews/2026-10-02_ai_reader_job_a.md`). It stays closed and disclosed under its frozen rule; nothing in it is
re-scored for admission. The first 2 October job (STOPPED after 175 attempts, never scored) is archived at
`reviews/2026-10-02_ai_reader_first_job_archive/`.

Job (b) started from fresh raw and clock state (`archive_job_a.py --apply` moved job (a)'s journal and clock into
`reviews/2026-10-02_ai_reader_job_a_archive/`, RSC `5438e73`), its own envelope (600 requests, 660 attempts, 3 per
request, 120 s, 6 h), job (a) retained closed beside it.
A one-off re-analysis of job (a)'s answers under the revision-12 rule, labelled and never admission, is in
`reviews/2026-10-03_ai_reader_job_a_rescore_rev12/`.

Job (b) ran on 3 October under revision 12 and the owner's go: STOPPED after 219 of 600 requests (218 ok, one
capacity refusal classified isolation under revision 12) when the Homebrew cask upgrade removed the pinned CLI
(`reviews/2026-10-03_ai_reader_job_b.md`); never scored, never re-used. Job (c) runs only on revision 14, after
Codex's favourable record and the owner's go: `archive_job_b.py --apply` moves job (b)'s journal and clock into
`reviews/2026-10-03_ai_reader_job_b_archive/`; fresh state; its own envelope; all 600 requests re-asked.

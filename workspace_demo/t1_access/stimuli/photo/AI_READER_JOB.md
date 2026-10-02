# The AI image-reader qualification: the bounded reader job

R084, 2 October 2026. Revision 4, answering Codex's record RSC `5a8d7ac` through R052's handoff `46125389`.
The design and the map from each closure to its code and test are in `AI_READER_DESIGN.md`.

**No model has been called.** Nothing in this job runs until R052 has submitted the exact package to Codex, Codex
has written a favourable review carrying a STAGE-ATTESTATION v1 block (row `aireader`, stage `qualification`, the
package `ai_reader_exec.py plan` prints), and the owner's go is written into `AIREADER_GO.json`.

| | |
|---|---|
| Reader | OpenAI Codex CLI 0.159.3 (`/opt/homebrew/Caskroom/codex/0.159.3/bin/codex`, sha256 and package manifest bound), `codex exec`, model `gpt-6.1-sol`, reasoning effort medium. One image per fresh ephemeral session. |
| Executor | `ai_reader_exec.py` (`plan`, `delivery` - both local, no request; `run` - the job) |
| Boundary | `ai_reader_runtime.py` (the allowlist profile, receipts, parser) |
| Watchdog | `stage_a_watchdog.py` (shared with row 20), one per attempt |
| Journal | `ai_reader_raw_responses.jsonl` (`ai_reader_journal.py`), committed before scoring |
| Scorer | `ai_reader_score.py` (orchestrator only) |
| Key | `ai_reader_qual_key.json` (orchestrator only; outside the reader's allowlist) |
| Images | `captures/ai_reader_qual/<request>.jpg|.png` (600 files, git-ignored), verified against the set before every attempt; the delivered bytes and the normalised user text frozen per request in `ai_reader_delivery.json` (all 600 embedded byte-identically and the prompt rendered, measured 2 October) |

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
| Time per attempt | min(120 s, job time left − 120 s reserve), refreshed again immediately before GO; not started under 30 s | process-group SIGTERM, 3 s, SIGKILL, whole-group cleanup, reap; the watchdog's hard deadline |
| Job wall clock | **6 h** across sessions; the durable session opens before hashing, the go and the receipts and beats every second from its own thread; a dead session is charged its last durable time + 30 s; a journal without its clock, or a clock below the journal's charged time, is refused | `clock.json` |
| Answer kept | 2,000 characters verbatim; longer = excerpt + original length + sha256, ERR_OVERLENGTH | no silent truncation |
| Raw evidence per attempt | the event stream complete up to 32 KiB (beyond it the attempt is OVERFLOW), stderr 4 KiB (head and tail beyond, with length and sha256); captured stdout 1 MiB, stderr 256 KiB, attempt directory 16 MiB + the image, also checked at exit | `bounded`, the wait loop |
| Local receipt commands | output captured to files under a 4 MiB cap and a 60 s timeout | `run_local` |
| Raw output | under 20 MiB; an attempt starts only if its three records fit under 20 MiB − 256 KiB | `J.append(cap=…)`, the pre-attempt check |
| Abandoned attempt output | swept at start; the attempts root capped at 256 MiB before every attempt | `sweep`, the pre-attempt check |
| Quota | the owner's ChatGPT plan through Codex (`codex login status`: "Logged in using ChatGPT"). No other model, setting or panel may be substituted | the package binds binary, manifest, version, flags, profile |
| The later audit | up to **400** reader turns, a separate job with its own frozen state and caps, only after this qualification admits the reader | not this executor |

A stop after the journal is admitted — a limit, a hold, a receipt mismatch, a raw-cap refusal, a launch or receipt
failure, an exception — first brings any open attempt to an end (identity-verified kill, recovered + end) and then
writes a STOPPED receipt (reason, exact counters, smoke status, limits, clock, the journal's hash); all 600 final
writes COMPLETE (only with a passed smoke). If the journal cannot be written at all, no receipt is claimed: the journal
stays a valid incomplete journal and the next start re-derives its holds. Nothing runs after a receipt. No limit is
reset or extended; nothing is redrawn, replaced, re-prompted or re-run after an answer exists.

## The request boundary

Every attempt is a new process under `sandbox-exec` with an **allowlist** profile: deny by default; only the codex
binary may execute (no shell, no helper, no other program); file reads only of the attempt directory (the image under
its opaque request name, the private CODEX_HOME with the auth link, tmp, its own outputs), the auth file, the binary and
its package manifest, and the system runtime; writes only inside the attempt directory and to the auth file; network
outbound; eight named Mach services (TLS trust, Security, network configuration, DNS, directory lookups,
notifications, logging). The key, the set, the scorer, the repositories, the norms, other attempts' directories and
the home are unreadable wherever they are (measured with the real binary and no request).

The command: `codex exec --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules -s read-only`, the
pinned model and effort, configuration that sets the read-only sandbox mode, disables web search and drops the
permissions, environment, collaboration, apps and skills instructions, **32 tool-capable features disabled
(`features list` under the same flags: 31 false; `unified_exec` stays true in this CLI under every switch, measured,
and has no program it may launch)**, `--json` and `-o`, the image with `-i`, then `--` and the frozen prompt; a pinned
environment of five variables; stdin `/dev/null`.

Before anything is sent:

- **per attempt**, `codex debug prompt-input` renders the attempt's model-visible input locally: its instructions
  must hash to the pinned value, its embedded image to the request's frozen delivered digest and its normalised user
  text to the request's frozen hash, or the job holds with nothing sent;
- **per session**, the preflight re-measures the effective features and the auth route, and runs the **exact exec
  invocation** with a synthetic image and all network denied by the kernel: its submitted input must be exactly
  [image, prompt] and its sampling-time configuration (model, effort, approval Never, ReadOnly without network, every
  feature flag) must agree with `features list`. The serialised request body is not observable without a request;
  that limit is recorded, not claimed away.

The worker then waits for 'GO' on stdin, written only after the dispatch record (with the worker's and its watchdog's
identities) is durable.

The event stream is classified fail-closed: a tool, command, file, web, MCP or other non-bookkeeping event or item is
ERR_ISOLATION (retained, never retried) whatever the exit status, except two frozen CLI notices (the code-mode-disabled
notice and the transport-fallback prefix); a malformed line, an answer without a complete ordered lifecycle
(thread.started once and first, turn.started once, each item completed once, exactly one agent message,
turn.completed once and last, no turn.failed), or an event answer that differs from the `-o` answer is ERR_ISOLATION;
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
  is asked again; a dispatched attempt without an end is retained as ERR_INTERRUPTED (never re-asked), after any
  surviving process of its recorded identities is killed and confirmed gone; an attempt never dispatched is charged and
  may be retried; an incomplete last line is quarantined durably before the journal is truncated, and a quarantine file
  without its record is recorded at the next start.
- A worker never outlives a dead orchestrator beyond its watchdog's bound (measured: gone within grace + 3 s).
- The scorer refuses a raw file that is untracked, dirty, different from its committed blob, incomplete, invalid, or
  written under another package, and in scientific mode any injected key, set, delivery or package.

## Order of operations

1. `ai_reader_exec.py delivery` (run 2 October; local) and `ai_reader_exec.py plan`: images, boundary, package.
2. Codex's review of the exact committed package.
3. The owner's go, bound in `AIREADER_GO.json`.
4. `ai_reader_exec.py run` (resumable within the same limits).
5. Commit `ai_reader_raw_responses.jsonl`.
6. `ai_reader_score.py ai_reader_raw_responses.jsonl`.
7. If admitted, the referrals go to the owner and the audit proceeds under `audit_app/IMAGE_AUDIT_FREEZE.md`; if
   not, the audit holds. Any other route is a separate owner decision.

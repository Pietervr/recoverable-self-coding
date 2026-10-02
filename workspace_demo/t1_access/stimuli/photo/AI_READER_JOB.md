# The AI image-reader qualification: the bounded reader job

R084, 2 October 2026. Revision 3, answering Codex's record RSC `7048bb8` through R052's handoff `742146ad`.
The design and the map from each closure to its code and test are in `AI_READER_DESIGN.md`.

**No model has been called.** Nothing in this job runs until R052 has submitted the exact package to Codex, Codex
has written a favourable review carrying a STAGE-ATTESTATION v1 block (row `aireader`, stage `qualification`, the
package `ai_reader_exec.py plan` prints), and the owner's go is written into `AIREADER_GO.json`.

| | |
|---|---|
| Reader | OpenAI Codex CLI 0.159.3 (`/opt/homebrew/Caskroom/codex/0.159.3/bin/codex`, sha256 bound), `codex exec`, model `gpt-6.1-sol`, reasoning effort medium. One image per fresh ephemeral session. |
| Executor | `ai_reader_exec.py` (`plan`, `delivery` - both local, no request; `run` - the job) |
| Boundary | `ai_reader_runtime.py` |
| Journal | `ai_reader_raw_responses.jsonl` (`ai_reader_journal.py`), committed before scoring |
| Scorer | `ai_reader_score.py` (orchestrator only) |
| Key | `ai_reader_qual_key.json` (orchestrator only; unreadable to the reader's process) |
| Images | `captures/ai_reader_qual/<request>.jpg|.png` (600 files, git-ignored), verified against the set before every attempt; the delivered bytes frozen per request in `ai_reader_delivery.json` (all 600 embedded byte-identically, measured 2 October) |

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
| Time per attempt | min(120 s, job time left − 120 s reserve); not started under 30 s | process-group SIGTERM, 3 s, SIGKILL, reap |
| Job wall clock | **6 h** across sessions, from entry (hashing, recovery, journal scan and final writes charged); a dead session charged its last durable time + 30 s | `clock.json` |
| Answer kept | 2,000 characters verbatim; longer = excerpt + original length + sha256, ERR_OVERLENGTH | no silent truncation |
| Raw evidence per attempt | events 16 KiB, stderr 4 KiB (head and tail beyond, with length and sha256); captured stdout 1 MiB, stderr 256 KiB, attempt directory 16 MiB + the image, else OVERFLOW | `bounded`, the wait loop |
| Raw output | under 20 MiB; an attempt starts only if its three records fit under 20 MiB − 256 KiB | `J.append(cap=…)`, the pre-attempt check |
| Quota | the owner's ChatGPT plan through Codex (`codex login status`: "Logged in using ChatGPT"). No other model, setting or panel may be substituted | the package binds binary, version, flags |
| The later audit | up to **400** reader turns, a separate job with its own frozen state and caps, only after this qualification admits the reader | not this executor |

Every stop writes a STOPPED receipt (reason, exact counters, the journal's hash) inside the reserve; all 600 final
writes COMPLETE. Nothing runs after a receipt. No limit is reset or extended; nothing is redrawn, replaced,
re-prompted or re-run after an answer exists.

## The request boundary

Every attempt is a new process: `codex exec --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules
-s read-only`, the pinned model and effort, the config switches that remove the permissions, environment,
collaboration, apps and skills instructions, 34 tool-capable features disabled, `--json` and `-o`, under
`sandbox-exec` with a profile that **denies every file read under the home except the auth file**, in a pinned
environment of five variables, with a private CODEX_HOME holding only the auth link and a working directory holding
only the image under its opaque request name. `codex features list` under the same flags must show each disabled
feature false; `unified_exec` cannot be turned off in this CLI (measured) and is recorded as such.

Before anything is sent, `codex debug prompt-input` renders the attempt's model-visible input locally: its
instructions must hash to the pinned value and its embedded image to the request's frozen delivered digest, or the
job holds with nothing sent. The worker then waits for 'GO' on stdin, which is written only after the dispatch
record is durable.

The event stream is classified fail-closed: a tool, command, file, web, MCP or other non-bookkeeping event is
ERR_ISOLATION (retained, never retried) whatever the exit status; a malformed line, or an answer without a complete
lifecycle, is ERR_ISOLATION; a structural failure (configuration, authentication, image) holds the job.

The reader never has access to the key, the scorer, the set, the repositories, this brief, the human norms, concept
names, other answers, or the item's other view. Colour and grayscale views of one item run in separate sessions, in
the frozen seeded order (seed 20261008), never adjacent.

**The smoke rule.** The first ordinary request in the frozen order is the technical smoke after the go: attempt 1 of
660, charged, retained and scored whatever it returns. Its receipt is checked like every attempt's; after it the job
holds on a structural failure, on malformed or incomplete event evidence, or on an answer saying no image arrived,
and after request 1 if it ended with no answer in three attempts. Nothing is changed on its answer.

**Disclosed, not proved.** What the CLI transmits is its own behaviour; the receipt is its local rendering. A
different developer does not prove independent errors or that this public dataset is absent from the reader's
training data.

## Durability and recovery

- One exclusive lock (`captures/ai_reader_job/LOCK`, fcntl) for the life of the process.
- The journal is the only attempt state; every record is fsynced before the next step and carries the package digest.
- A restart reconstructs everything from the journal: no answer that reached the journal is asked again; a
  dispatched attempt without an end is retained as ERR_INTERRUPTED (never re-asked), after any surviving worker group
  is killed; an attempt never dispatched is charged and may be retried; an incomplete last line is quarantined.
- The scorer refuses a raw file that is untracked, dirty, different from its committed blob, incomplete, invalid, or
  written under another package.

## Order of operations

1. `ai_reader_exec.py delivery` (already run; local) and `ai_reader_exec.py plan`: images, boundary, package.
2. Codex's review of the exact committed package.
3. The owner's go, bound in `AIREADER_GO.json`.
4. `ai_reader_exec.py run` (resumable within the same limits).
5. Commit `ai_reader_raw_responses.jsonl`.
6. `ai_reader_score.py ai_reader_raw_responses.jsonl`.
7. If admitted, the referrals go to the owner and the audit proceeds under `audit_app/IMAGE_AUDIT_FREEZE.md`; if
   not, the audit holds. Any other route is a separate owner decision.

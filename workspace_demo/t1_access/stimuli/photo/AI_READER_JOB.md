# The AI image-reader qualification: the bounded reader job

R084, 2 October 2026. Revision 2. This is repair 8 of R052's handoff `7f25830e`, answering Codex's record RSC
`cf3e49e`.

**No model has been called.** Nothing in this job runs until R052 has submitted the exact package to Codex, Codex
has given a favourable review, and the owner's go is written into `AIREADER_GO.json`, bound to the hashes
`ai_reader_exec.py plan` prints.

| | |
|---|---|
| Reader | OpenAI Codex CLI 0.159.3, `codex exec`, model `gpt-6.1-sol`, reasoning effort medium. One image per fresh ephemeral session. |
| Executor | `ai_reader_exec.py` (`plan` = dry run; `run` = the job) |
| Scorer | `ai_reader_score.py` (orchestrator only) |
| Key | `ai_reader_qual_key.json` (orchestrator only) |
| Images | `captures/ai_reader_qual/<request>.jpg` and `<request>.png` (600 files, git-ignored). Each is verified against the set before its call. |

## Planned work and limits

| Limit | Value |
|---|---|
| Planned responses | **600**: 300 items × (colour, grayscale), one retained response each |
| Attempts | at most **660** in all, and at most **3** per request |
| When a retry is allowed | only when no answer came back (process error, timeout, empty last message). An answer is final, however wrong. |
| A request that fails 3 times | retained as `ERR_NO_RESPONSE`, an error in the denominator |
| Time per attempt | 120 s |
| Wall clock for the job | **6 h** |
| Length of an answer kept | 2,000 characters (a longer answer is an explanatory error anyway) |
| Raw output | under 20 MB |
| Quota | the owner's ChatGPT plan, used through Codex. 600–660 single-image turns with a one-line answer. No other model, setting or panel may be substituted. |
| The later audit (a separate allowance) | up to **400** reader turns for the 32 primary views and their second views: about 224 questions plus re-asks after provider failures. It runs only after this qualification admits the reader. |

The executor stops and holds at any limit. It never extends a limit. Nothing is redrawn, replaced, re-prompted or
re-run after an answer exists.

## Isolation (repair 6)

Every request is a new process with:

- an empty working directory that holds only that request's image, under its opaque name;
- a private `CODEX_HOME` that holds only a symlink to the auth file, so no instructions, memories, history, config,
  rules, plugins or hooks are loaded;
- `--ephemeral --ignore-user-config --ignore-rules -s read-only`;
- 18 tool features disabled, each checked against `codex features list` by the dry run;
- `--json` events, and `-o` for the last message.

The JSONL events are checked. Any tool, command, file, web or MCP event turns the response into `ERR_ISOLATION`.
It is kept, scored as an error, and never retried.

The reader never sees the key, the scorer, the set, this repository, this brief, the human norms, concept names,
other answers, or the item's other view. Colour and grayscale requests for one item run in separate sessions, in a
frozen seeded order (`delivery_order`, seed 20261008) in which they are never adjacent.

**Disclosed, not proved.** A different developer separates the audit from target-model selection. That does not
prove independent errors, or that this public dataset is absent from the reader's training data.

**One untested assumption.** `view_image` is disabled. The image arrives as an attachment (`-i`), not through that
tool. Whether the attachment survives with `view_image` off cannot be checked without a call. If it does not, the
first request fails as a provider failure and the job holds on the attempt limit. That would be reported, not
patched in flight.

## Durability and recovery

- One exclusive lock: `captures/ai_reader_job/LOCK`.
- `captures/ai_reader_job/state.json` holds the attempts, the tries per request, the seconds, the retained
  requests and the open request. It is written atomically before and after every attempt.
- `ai_reader_raw_responses.jsonl` gets one record per attempt, appended and fsynced, whether retained or a provider
  failure.
- **Idempotent restart.** Requests with a retained answer are skipped. An attempt open at a crash is logged as a
  provider failure and stays counted. The limits are the same ones, never reset.
- **Raw answers are committed before scoring.** `ai_reader_score.py` refuses a raw file that is untracked or dirty
  in git. The raw answers are thus locked before any score exists, and before any intended name is revealed for the
  audit questions.

## Order of operations

1. `ai_reader_exec.py plan`: verifies the 600 images, the CLI version, the private home and the feature names, and
   prints the package hashes.
2. Codex's review of the exact committed package.
3. The owner's go, bound in `AIREADER_GO.json`.
4. `ai_reader_exec.py run`.
5. Commit `ai_reader_raw_responses.jsonl`.
6. Run `ai_reader_score.py`.
7. If the reader is admitted, the referrals go to the owner and the audit proceeds under
   `audit_app/IMAGE_AUDIT_FREEZE.md`. If it is not admitted, the audit holds. Any other route is a separate owner
   decision.

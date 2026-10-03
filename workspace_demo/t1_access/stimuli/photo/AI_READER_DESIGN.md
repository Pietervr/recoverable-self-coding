# AI image-reader qualification, revision 16: the design and where each condition lives

R084, 2-3 October 2026. The specification is framework §8.2's reader rule with R052's closures (Unimog, R052's text).
Revision 5 answers Codex's combined record RSC `1bf9890` (not favourable to revision 4 at RSC `d7a486a`; reader
conditions 1–7 = R1–R6 there) through R052's handoff `8c9dac2b`. Revision 4 answered RSC `5a8d7ac` (handoff
`46125389`); its closures stand and are listed after the revision-5 table.

## Revision 16: split UTF-8 whitespace in the retained excerpts (Codex `478196f` P2, R052 handoff `d9587571`)

Codex's record RSC `478196f` (NOT FAVOURABLE to revision 15 at `05bd60b`) credited the ASCII repair, the hold for both
variants and marking independent of the overflow flag, and found one boundary: `bounded` sliced the -o BYTES at 1,024
for head and tail and decoded each with replacement, so a blank file of U+3000 (683 x 3 = 2,049 bytes) was correctly
marked CAPACITY_UNPROVEN but its excerpts carried U+FFFD and `_rederive`'s blank-excerpt check rejected the actual end -
on restart before the hold reached STOPPED, and in an incomplete validation even after it.

| Item | Where it lives | Fixture (no request) |
|---|---|---|
| The head ends and the tail begins on a UTF-8 code-point boundary (the cut moved back / forward past at most three continuation bytes), so no character is split; for invalid UTF-8 the shift is bounded and the bytes still decode with replacement. Applies to every bounded evidence field (events, stderr, -o); the excerpts remain excerpts - never proof of the omitted middle. | `ai_reader_runtime.bounded` | `Rev16Reader.test_excerpts_never_split_a_character` (U+3000, emoji, accented text; head/tail are the text's own prefix/suffix, each <= 1,024 bytes) |
| Unchanged: the retry or the structural hold only on an absent or COMPLETE exact blank -o file (<= 2,048 UTF-8 bytes); the marker both ways; the full-stream item checks; received-answer guards; both durable holds. | runtime, journal (no change) | `test_2046_bytes_is_the_declared_capacity_end` (682 x U+3000, ordinary -> provider, structural -> structural; actual ends re-derived); `test_2049_bytes_is_the_marked_final_end_and_validates` (both variants; blank excerpts; no retry label) |
| Recovery: the incomplete journal validates before and after STOPPED; the hold reconstructs; no next dispatch; a crash right after the marked durable end, then restart -> STOPPED, nothing dispatched, journal valid | executor, journal (no change) | `test_executor_holds_and_the_incomplete_journal_validates` (fake CLI capacity:w683 and capacity_structural:w683; capacity:w682 still retries); `test_ai_reader_crash.Rev16` (crash after_end on the marked end, both variants) |
| Fixture fragility (test only): the Rev6 slow-receipt case raced a 2 s pre-receipt sleep against the 2 s stop timer (3 s allowance less two 0.5 s reserves) - no margin; it is replaced by three deterministic controls each 2 s clear of the timer. Production closure bounds unchanged. | `tests/test_ai_reader_crash.py` | `Rev6.test_slow_receipt_and_slow_close_share_one_deadline` (receipt stall 4 s -> exit 75, no durable receipt; instant receipt + 4 s close -> exit 75, receipt durable but not qualifying; both 0.3 s -> exit 0, qualifies) |

Moved from revision 15: `ai_reader_runtime.py`, `AI_READER_JOB.md` (header; the current-revision statements Codex
flagged), this file and the digest.

## Revision 15: the capacity path's -o evidence boundary (Codex `431f072`, R052 handoff `71210376`)

Codex's record RSC `431f072` (NOT FAVOURABLE to revision 14 at `7fc9f52`) closed R1, R2 and the declaration and found
one boundary: a capacity refusal with a blank -o file longer than FILE_ANSWER_KEEP (Codex's case: 2,049 ASCII spaces)
was labelled retryable (or structural) while `bounded` retained only head and tail, so the journal could not prove the
file blank and refused the end - after the executor had already retried. Revision 15 takes Codex's narrow policy.

| Item | Where it lives | Fixture (`tests/test_ai_reader.py` Rev15Reader, no request) |
|---|---|---|
| The capacity exception (provider retry, or the structural hold with structural stderr) is granted ONLY when the -o file is absent or its COMPLETE text is retained exact and blank: at most FILE_ANSWER_KEEP = 2,048 UTF-8 bytes (`file_blank_proven`). The capacity shape is judged from retained evidence only (complete events, no malformed line, the declared bare markers, no answer). | `ai_reader_runtime.classify`, `file_blank_proven` | `test_2048_spaces_is_the_declared_capacity_end` (ordinary -> provider_failure, structural -> structural_failure; each actual end re-derived) |
| Above the limit (or any incomplete -o evidence) the end is a retained FINAL isolation whose isolation events are the stream's own plus `CAPACITY_UNPROVEN`; the job HOLDS before any further dispatch (`holds`), and the journal admits only tail repairs and the STOPPED receipt after it - the structural hold's rule. Fail closed, no retry, for the ordinary and the structural variant alike: neither label can be proven. | `classify`, `CAPACITY_UNPROVEN`; `ai_reader_journal.apply`, `holds`, `validate` | `test_2049_spaces_is_final_isolation_with_the_marker` (both variants; retry and structural labels refused; the marker removed refused); `test_executor_no_retry_holds_and_the_journal_agrees` (fake CLI: one dispatch, nothing after, journal valid, restart derives the hold, nothing runs after the receipt, admission refuses) |
| `_rederive` agrees exactly, both ways: the marker is present IF AND ONLY IF the retained events show the capacity shape, there is no answer and the -o evidence is present but not proven blank; a marked end must be the declared isolation (events = the stream's + the marker, -o digest bound, length over 2,048, head and tail blank). Structural precedence, the full-stream isolation checks and the bare-marker rule are unchanged. | `ai_reader_journal._rederive` | `test_the_marker_is_refused_where_it_does_not_belong`; `test_controls_absent_empty_received_and_nonblank_oversize` (absent/empty -o controls; received and non-blank oversize answers stay final without the marker); every Rev13Reader/Rev14Reader control unchanged |
| Declaration: the byte limit in UTF-8 bytes | `AI_READER_JOB.md` (the error sentence), this section | `test_the_docs_declare_the_byte_limit` |

Moved from revision 14: `ai_reader_runtime.py`, `ai_reader_journal.py`, `AI_READER_JOB.md`, this file and the digest.
The limit is 2,048 UTF-8 bytes of the -o file as decoded (UTF-8 with replacement) and re-encoded - for whitespace the
file's own bytes.

## Revision 14: the two capacity-path repairs of Codex `f363767` (R052 handoff `c323625e`)

Codex's record RSC `f363767` (NOT FAVOURABLE to revision 13 at `57cfb0a`) credited the owned CLI, the 25 pins and the
exposure, and found two capacity-path defects.

| # | Condition | Where it lives | Evidence (`tests/test_ai_reader.py`, class `Rev14Reader`) |
|---|---|---|---|
| R1 | The exemption dropped the exempt error's item checks | `ai_reader_runtime.capacity_refusal`: an exempt capacity error is a BARE marker - its keys exactly `type` and `message`; any `item` or other key disqualifies it - and `isolation_problems` runs on the FULL original stream, which must find nothing but one "error event" entry per bare marker. Revision 13 removed the matching events before the check, so an item inside one went unchecked. | `test_an_item_inside_the_capacity_error_is_isolation` (Codex's command_execution counterexample, a tool item, a malformed item: retained final isolation; a forged provider_failure label refused by the journal); `test_any_extra_key_disqualifies_the_marker` |
| R2 | Capacity plus structural stderr retried; the journal rejected it | ONE precedence in both places: `classify` returns `structural_failure` (the declared hold, no retry) when the capacity shape meets STRUCTURAL stderr; `_rederive` excuses the bare markers for a provider OR structural failure and its existing stderr rule decides which (structural wins); the journal never ignores structural evidence. | `test_capacity_with_structural_stderr_is_the_structural_hold` (classify and the journal agree; a forged provider label refused; the ordinary capacity control still retryable); `test_executor_capacity_retries_item_is_final_structural_holds` (fake CLI: capacity retried then ok; an item inside the error final isolation; capacity + structural stderr holds after one dispatch, nothing dispatched after it, the journal validates) |
| D | Declaration | `AI_READER_JOB.md`'s error sentence names the declared capacity exception beside the two notices. Outside the package, `reviews/2026-10-03_reader_cli_0.160.0_features_list.txt`: the owned binary's full `features list` text under the job's flags (evidence only, no pin). | `test_the_job_doc_declares_the_capacity_exception` |

Nothing else changes: the owned CLI, its pins, the delivery receipt (no command change), the exposure statement of
revision 13 (job (c) under revision 14's package instead of 13's) and everything revision 13 kept.

## Revision 13: a project-owned CLI, the capacity refusal, the exposure (R052 handoff `09226a88`)

Job (b) (revision 12, favourable at Codex RSC `09bbe0e`, the owner's go "1. and 2. go") STOPPED after 219 of 600
requests: at 16:58 UTC on 3 October the Homebrew cask upgraded the Codex CLI 0.159.3 -> 0.160.0 under the running job
and the pinned binary disappeared (`reviews/2026-10-03_ai_reader_job_b.md`). Unscored, closed by its receipt.

| # | Item | Where it lives | Evidence |
|---|---|---|---|
| 1 | The reader's CLI is a PROJECT-OWNED, read-only copy | `captures/reader_cli/codex-0.160.0/` (git-ignored; `ditto` of the cask tree 0.160.0 - binary byte-identical, code signature intact; every file and directory made read-only, so no package manager, updater or extension writes it). `ai_reader_runtime.CODEX` / `CODEX_TREE`; the allowlist names that binary as the one executable. Measured: under the allowlist the CLI reads only its binary and `codex-package.json` from the tree (the Boundary class passes with nothing else readable). Pinned in the package: realpath, binary sha256, manifest sha256, version, and a TREE HASH of the whole copied directory (`tree_sha`: every file, sorted, path and sha256) - a 25th package field, `codex_tree_sha256`. The binary has a `check_for_update_on_startup` setting; it is set off in the CLI configuration (`CONFIG`) and so pinned in the command template. | `test_ai_reader.Rev13Reader.test_the_owned_binary_and_its_pins` (path, read-only tree, 25 fields, tree hash), `test_tree_hash_moves_with_any_file`; `Boundary` (all 11) on the owned binary |
| 2 | Re-measured on that binary | `Boundary`: the allowlist's denials, the effective features (0.160.0 lists 152 features in the invocation receipt against 0.159.3's 150; which two are new
cannot be told without the removed binary, and no 0.159.3 list was retained - so the three ENABLED features that bear on
updates or execution, `in_app_updates`, `daemon_auto_start` and `unified_exec_zsh_fork`, were added to DISABLE, all
three measured to switch off: 35 requested, 34 effectively false; `resize_all_images` stays as it is - the delivered
image digests are unchanged for all 600), `unified_exec` (still true under every switch on 0.160.0 - UNDISABLEABLE, and still able to exec no program but the owned codex binary), the auth route, the separator regression, the exec-invocation receipt (model `gpt-6.1-sol`, effort medium, approval Never, read-only without network, every feature flag agreeing with `features list`). The delivery receipt re-rendered for all 600 (`ai_reader_exec.py delivery`, local, no request): image digests, sizes, details, mime types and file hashes byte-identical for 600 of 600, none re-encoded; the per-request user-text hash UNCHANGED for 600 of 600 (600 distinct) - the prompt's rendering did not move; the instructions hash unchanged (`e2a8ba62…`); the preflight's effective features (35/34, the listing hash) and the invocation receipt (152 features compared, its tags hash) moved. | `Boundary`; `ai_reader_delivery.json` |
| 3 | The capacity refusal is a RETRYABLE provider failure | `ai_reader_runtime.CAPACITY_MESSAGES` (the frozen text "Selected model is at capacity. Please try a different model.", from job (b)'s request `59adc2d73b07`) and `capacity_refusal`: at least one top-level error event with that text, a `turn.failed` whose error message is that text, NO agent message, nothing else `isolation_problems` flags, and a missing or blank `-o` file -> `provider_failure` (not retained; retried inside the unchanged 3 tries / 660 attempts / 6 h). Every other undeclared top-level error event stays ERR_ISOLATION. `ai_reader_journal._rederive` admits `provider_failure` beside those isolation markers only on exactly that shape. | `Rev13Reader`: the retained job (b) evidence (sha256 `90c6f7b8…`, checked against the committed journal) - isolation under revision 12's rule, retryable now, admitted by the journal; negatives: with an agent message, with a command event, with non-blank `-o` text, a different message, `turn.failed` with another message, no `turn.failed` - all isolation; the journal refuses the label on another shape |
| 4 | Exposure | the statement below; `AI_READER_JOB.md` | — |
| 5 | Unchanged | the shared matching rule and the S1 guard, the prompt, the 300 images, strata, easy membership, the key and alias-map bytes, the gate and the adjudication sentence, the isolation boundary's design, the journal, the clock, the limits; `archive_job_b.py` prepared (dry run checked) | — |

**Exposure (revision 13).** Job (a) (2 October, revision 11): 600 answers, not admitted. Job (b) (3 October, revision
12): 219 requests (218 answers, one capacity refusal), stopped by the binary's removal, unscored, never re-used. Job
(c) re-asks all 600 on the SAME exposed panel under revision 13's package: evidence for the prospective rule on a
reused panel, never a blind calibration (Codex `09bbe0e`). The revision-13 package has made no call.

## Revision 12: one matching rule and a one-or-two-word prompt (the owner's decision of 3 October)

Job (a) (revision 11, favourable at Codex RSC `5eb51a8`, the owner's go) ran COMPLETE and was NOT ADMITTED: 49 of 63
easy gray under the whole-answer key (`reviews/2026-10-02_ai_reader_job_a.md`). Twelve of its 14 easy misses were
correct recognitions phrased as the noun phrases revision 11's prompt invited ("Toilet paper roll", "Portable
generator", "Sneakers"): the key measured lexical conformity, not recognition. The owner decided (R052 handoff
`ff264083`; framework §8.2) to keep free naming, to score the qualification and the image audit by ONE matching rule,
and to ask for the most common name in one or two words. Job (a) stays NOT ADMITTED under its frozen rule.

| # | Item | Where it lives | Evidence (`tests/test_ai_reader.py`, class `Rev12` under `.venv-build`) |
|---|---|---|---|
| A | The shared matching rule | `ai_reader_key.names_concept(answer, concept, entry)`, over the frozen admitted and excluded forms and the recorded synset; WordNet pinned (`_wordnet` checks the zip's sha256 once per process). In order, on the answer as given and with each token singularised (`singular`: the key's inflection policy read backwards): (i) **whole** - equals an admitted form; an excluded form fails (S1-S4 stand); the canonical name or an inflection of ANOTHER released THINGS concept fails (S1's population, all 1,854: "Alpaca" for llama, "Belt buckle" for buckle - the reader named that concept); (ii) **contains** - an admitted form as a whole-word phrase, no head-noun guard; (iii) **hyponym** - a noun sense of the head lemma (the longest whole-word suffix WordNet knows as a noun) is a strict, transitive hyponym (hypernym and instance-hypernym closure) of the target synset; no synset, no (iii). | `test_the_fourteen_easy_misses_of_job_a`, `test_named_cases`, `test_every_excluded_form_still_fails`, `test_singularising_an_admitted_form_never_reaches_an_excluded_one`, `test_wordnet_pin_checked` |
| B | Both scorers call it | `ai_reader_score.classify_detail` (format before matching, unchanged) then `names_concept`; codes OK_WHOLE / OK_CONTAINS / OK_HYPONYM / ERR_NONMATCH / ERR_MALFORMED (and the other format and status codes as before); the rule label per row, per referral (`rule`: whole / contains / hyponym, or excluded / S1:<ids> on a non-match) and counted (`match_rules`). `audit_alias_map.score` calls the same `classify_detail` with the frozen map's entry; the map's bytes and hash are unchanged (`a3f6ab51…`), its construction reproduced by a rebuild in everything but the two recorded source hashes. | `test_audit_scorer_same_rule_own_entry_point` (whole, contains, hyponym, S1, excluded, a hypernym through `audit_alias_map.score` and `audit_package.score`, equal to the qualification classifier on the map's entry), `test_one_function_in_both_scorers`, `test_audit_map_rebuild_unchanged`, `AuditMap.test_rule_applied_and_inflections` (the map's recorded source hashes are the blobs at its build commit) |
| C | The prompt | `ai_reader_qual.PROMPT`, word for word the owner's: "Look at this picture. What is the main object in it? Answer with the most common name for the object, in one or two words, or with the single word 'unclear' if you cannot tell. Reply with the name only." The same text is the audit's question 1 (`audit_app/IMAGE_AUDIT_FREEZE.md`). The set was regenerated: its 600 requests (files, bytes, sha256), the delivery order, the items and strata are identical; only the prompt, its hash (`086cd001…`), the revision and two code hashes changed. The delivery receipt was re-rendered locally (`ai_reader_exec.py delivery`, no request; dated 2 October MST, 3 October UTC): image digests, sizes, details and mime byte-identical for all 600, none re-encoded, the instructions hash unchanged (`e2a8ba62…`), the preflight unchanged, the user-text hash changed for all 600, 600 distinct. | `test_prompt_is_the_owners`; `Boundary` (the receipt renders the prompt); the delivery receipt |
| D | Fixtures (no model) | The 14 easy misses of job (a) with their expected codes - **12 pass, not 11**: "Air conditioning unit" passes by (ii) because "air conditioning" is an admitted form of air_conditioner (a THINGS-listed WordNet synonym); the brief expected a referral. Pearl ("Seashell") and christmas card ("Holiday greeting card": head "greeting card", a hypernym) fail. "paint brush" passes by (ii) (the disclosed residual); "greeting card" and "marlin" fail; "sneakers" passes by (iii); "stretcher" (gurney) and "drums" (bongo) fail - both are other released concepts' names; plurals and articles. | `Rev12` (10 tests) |
| E | Documents | This section; `AI_READER_JOB.md`; `IMAGE_AUDIT_FREEZE.md` (aggregation under the shared rule; the restated sentence; the exposure statement); the key's rule text (`ai_reader_key.py` docstring); the scorer's docstring. | `test_prompt_is_the_owners` (the freeze carries the prompt) |

**The gate (unchanged, mechanical).** Gray easy accuracy under the shared rule, one-sided exact 95 % lower bound
>= 0.90: 61 of 63. Declared prospectively, before any revision-12 answer (owner, 3 October; Codex rules on the
wording): a referral the owner adjudicates as naming the intended object - the picture and the raw answer recorded
before the decision - is not a reader error, and an admission that rests on such adjudications is reported as
"admitted with N owner-adjudicated items", never as a mechanical admission. The scorer reports the mechanical result
and `adjudications_needed`; it records no decision. The audit freeze's sentence "never turns a reader error into a
pass of the qualification" stands, restated with that distinction.

**Residuals, disclosed.** (ii) has no head-noun guard: the target as a modifier of another object ("paint brush" for
paint, "toy train" for toy) passes; WordNet cannot disambiguate the head's sense, and for the audit's question such an
answer is evidence that the stimulus evokes the concept. (iii) reads ANY noun sense of the head, so a rare sense that
happens to be a hyponym passes. The S1 guard is on the whole answer only: "toilet paper roll" (roll is a released
concept) passes by (ii), "roll" alone for toilet paper does not.

**Unchanged** (item 5 of the decision): the 300-image set, the strata, easy membership, the key's admitted and
excluded forms (no alias added, the key file byte-identical, `d9c467f3…`), the alias map's construction, the isolation
boundary, the journal, the clock, the limits (600 / 660 / 3 / 120 s / 6 h) and S1-S4. The executor, runtime, journal
and the four files shared with Stage A (`stage_a_guard.py`, `enforce.py`, `memprobe.py`, `stage_a_watchdog.py`) are
unchanged, so Stage A's revision-12 package is not moved.

**Exposure.** Job (a) sent the 600 qualification requests on 2 October under revision 11; this package has made no
call. Revision 12 was built knowing job (a)'s answers - the rule is the owner's, fixed before job (b), and job (a)'s
answers are re-scored under it only as a labelled re-analysis, never for admission
(`reviews/2026-10-03_ai_reader_job_a_rescore_rev12/`).

## Revision 11: the 2 October execution race

Revision 10 (RSC `fbfb7db`) was favourable (Codex RSC `3390183`) and ran under the owner's go on 2 October: smoke
passed, 174 of 175 attempts ended ok, one was interrupted, and the job STOPPED (`reviews/2026-10-02_ai_reader_run.md`).

| # | Condition | Where it lives | Evidence |
|---|---|---|---|
| R | `dir_bytes` over a live attempt directory | `ai_reader_exec.dir_bytes` walks with `os.walk` (symlinked directories not followed) and `lstat`s each entry; ENOENT/ENOTDIR on an entry that vanished after the listing - the Codex CLI's own `codex_home/tmp/arg0/codex-arg0*/applypatch` helper - is skipped and what was seen is counted; any other error (an unreadable directory) still raises and stops the run. | `test_ai_reader.Rev11.test_entry_removed_between_listing_and_stat` (PRODUCED exactly; the revision-10 function raises FileNotFoundError on the same race); `Rev11.test_continuous_churn` (a thread creates and removes helper directories, files and symlinks during 300 measures); `Rev11.test_unreadable_directory_still_raises` (control); `test_ai_reader_crash.Rev11.test_job_completes_while_the_cli_churns_its_helpers` (the fake CLI's `arg0churn` behaviour for 3 s during a real-process job: COMPLETE, admitted) |
| W | The shared watchdog | `stage_a_watchdog` now retires only on the leader's confirmed NOTE_EXIT (Stage A §R11); the reader's watchdog, the same file, follows the same rule. | the reader's existing watchdog fixtures (retirement with escaped members, controller death) |

The retained-output run for this revision: `reviews/2026-10-02_photo_suite_rev11_run.md`.

## Revision 10: the condition of RSC `dda950b` (favourable at `3390183`)

Codex's record RSC `dda950b` (not favourable to revision 9 at `ba4fc75`) closed reader A and B1–B3 as submitted and
left one boundary, answered here through R052's handoff `ac3b8525`.

| # | Condition | Where it lives | Evidence (`tests/test_ai_reader_crash.py`) |
|---|---|---|---|
| B | A foreign start still alive before the task lock | Every pending record (final or temporary) retains the start's process identity (`process`: pid and start time). Holding the lock, a start checks each foreign pending record before absorbing it: if that identity is alive, `end_foreign_start` ends it (SIGKILL by identity), confirms the death and records `ended_wall`; the clock charges start -> confirmed end; not confirmed dead within 10 s, the job HOLDS before anything is charged or removed. The pending evidence is removed only after the clock's first persist that holds the final charge. | `Rev10.test_live_foreign_start_before_the_lock` (S1 alive and stalled before the lock with its final pending file, and with only its readable temporary; its setup timer healthy at 60 s; S2 recovers while S1 lives: S1 ended by identity (exit −9), charged ≥ S2's recovery time − start and < the 60 s bound, pending evidence removed, admitted) |

Declarations qualified (Codex `dda950b`). Late return (revision 9's A): the fixture releases the commit at fired +
50 ms; it does not witness the first unlink's completion - the ordering evidence is that release time, with the static
post-return undo and the repeated removal supporting the mechanism (no measured early-unlink timestamp). Marker
residual - UNAVAILABLE EFFECTIVE REVOCATION: if the tombstone cannot be published AND neither effective removal path
completes, a matching marker can survive - also after a returned rename whose undo blocks or fails, and for a rename
still in flight in the kernel at process exit; a power loss can drop the marker's entry (the COMPLETE then does not
qualify). Revision 9's "any late return the process observes" is withdrawn. Startup residual: readable incomplete
publication is covered (revision 9) and a live foreign start is ended before its charge is final (revision 10); what
remains is a start that never got a pending temporary onto disk, bounded by its setup timer.

The retained-output run for revision 10: `reviews/2026-10-02_photo_suite_rev10_run.md` (historical).

## Revision 9: the conditions of RSC `7fdb937` (closed by `dda950b`; residual wording qualified in revision 10)

Codex's record RSC `7fdb937` (not favourable to revision 8 at `9f696c6`) closed reader C, credited A's commit-point
repair and B's repeated-start, elapsed-setup, one-id and missing/duplicate-session repairs, and left A's late-return
window and three B gaps, answered here through R052's handoff `50ab6395`.

| # | Condition | Where it lives | Evidence (`tests/test_ai_reader_crash.py`) |
|---|---|---|---|
| A | A finite late return after a successful early unlink | `Deadline.commit(fn, undo)` re-checks the `fired` latch AFTER the rename returned: a deadline that latched while the commit ran makes the late rename no commit - `undo` removes the marker and the step fails. The revocation's unlink no longer runs once: it removes the marker every 5 ms until the process exits, so a rename landing after its first unlink is removed too. | `Rev9.test_late_rename_after_an_early_unlink_does_not_qualify` (the commit is released only after the deadline fired and the first unlink found no marker; with the tombstone writer blocked and, as the control, not blocked: no marker survives, not admitted; the tombstone present exactly when not blocked) |
| B1 | Readable incomplete pending publication | A start whose pending file never completed (its temporary written and fsynced, the rename not reached) is still evidence: the next start reads every `clock.starting*.json.tmp` without its final file, charges it (an unreadable one: the declared 30 s) and removes it after the first persist. | `Rev9.test_readable_incomplete_pending_publication_is_charged` (the temporary written, the rename never comes, the setup timer kills the start: the next start charges that start, > 0.5 s, and removes the temporary; admitted) |
| B2 | The first persist bounded by the RECOVERED balance | `Clock` calls `before_persist(recovered_total)` after absorbing the crashed open session and every pending start and BEFORE its first persist; the job recomputes the remaining allowance from that total net of the elapsed setup - none left: hold; less than the setup bound: the timer is replaced by the shorter bound before its durable record. | `Rev9.test_near_cap_recovery_bounds_the_blocked_first_persist` (the saved base leaves ample time; the recovered open session + 30 s tail leaves about 3 s; the first persist blocks: exit 75 under the recovered bound, within 12 s, not at the 20 s setup timer) |
| B3 | Declared session states and their charge semantics | `session_state_problem` (in `clock_problems`, at load and at admission): a session that ran is closed `COMPLETE`, `STOPPED` or `ended` (charged its live seconds, no charge fields) or `crashed` (charged = live + tail, tail ≥ 30 s); a `failed_start` has live 0 and its charge; any other state refuses. `admit_clock` counts only those declared states as sessions that ran. | `Rev9.test_undeclared_closed_state_is_refused` (the earlier crashed session rewritten to an undeclared state with a sum-consistent total and a rehashed marker; a crashed session stripped of its tail - both refused) |
| C | (closed by `7fdb937`) the fallback fixture's description | Corrected: the fallback control's logs are complete and parseable but not an equivalent receipt (content `[x]`, model `m`, empty feature tags) - the control is timely-parse-positive only. | `test_ai_reader.Rev8.test_fallback_read_past_the_deadline` (docstring and comment) |

Residuals, stated as they are. Marker (A): a rename still in flight in the kernel when the process exits after the
revocation window, with the tombstone writer blocked, can leave a matching marker without a tombstone; a power loss
can drop the marker's directory entry (only ever non-qualifying). Revision 8's statement ("if both revocation steps
block") was narrower than the late-return window; the remaining residual is stated in revision 10 (unavailable
effective revocation).
Startup (B): only a start that never got a pending temporary onto disk (the job directory's creation, or the
temporary's own creation, stalled) leaves no evidence; it is bounded by the setup timer.

The retained-output run for revision 9: `reviews/2026-10-02_photo_suite_rev9_run.md` (historical).

## Revision 8: the conditions of RSC `12a7f20` (A and B completed in revision 9; C closed)

Codex's record RSC `12a7f20` (not favourable to revision 7 at `068fe30`) closed reader D, credited A's clock-file
failure and marker-exception repairs, B's clock-override refusal, total sum and attempt floor and C's in-loop
read/parse check, and left three, answered here through R052's handoff `db8a9e1d`.

| # | Condition | Where it lives | Evidence |
|---|---|---|---|
| A | The marker's own post-rename timeout must not qualify | `write_marker`: the marker is written and fsynced under a temporary name; its RENAME is the closure's commit point, run through the final deadline's `Deadline.commit`, and its last step (no directory fsync follows, so nothing can block once it is visible). The commit runs only if the deadline has not fired, under a lock the deadline takes before exiting; once it returned the deadline no longer fires. A deadline that fires first - or finds the commit still running after `COMMIT_GRACE_S` = 0.5 s - writes the tombstone `clock.close_aborted.json` naming the session and removes the marker (two daemon threads, at most `REVOKE_S` = 0.5 s), then exits 75. `admit_clock` refuses a session its tombstone names. The final timer fires at 60 − 0.5 − 0.5 = 59 s, so the whole bounded closure lies inside the 60 s the receipt charges. Residual (disclosed): a power loss can drop the marker's directory entry (it is not directory-fsynced) - that only leaves a COMPLETE non-qualifying; the revision-8 statement "if both revocation steps block" was narrower than the late-return window and is corrected in revision 9. | `test_ai_reader_crash.Rev8.test_marker_commit_stall_does_not_qualify` (the commit stalls before the rename, or the rename takes effect and the call does not return: exit 75, COMPLETE durable, clock reads closed, tombstone names the session, no marker, not admitted; control: an ordinary close admitted); `Rev8.test_marker_present_beside_its_tombstone_is_refused`; `Rev7.test_marker_failure_after_its_rename_is_removed` (now: a failed marker write) |
| B | Repeated/pre-pending startup charge; journal-session relation | Every start publishes its OWN pending file `clock.starting.<id>.json` right after the job directory exists - before the lock and before the old clock's read - with `start_wall` the process's own start and the setup deadline; no start replaces another's; a start refused at the lock removes its own. The remaining allowance is computed net of the elapsed setup (the old clock's read included); with none left the start holds (and is charged next time); a shorter bound replaces the timer before its durable record. `Clock` charges every pending start it has not already charged at its first persist; only then are the absorbed files removed. The pending entry and the clock session share ONE id, so a crash after the first persist and before the removal is charged once, as the crashed session. `admit_clock` requires unique clock session ids and, for every journal `open` session, a clock session that ran (closed or crashed; extra failed-start sessions allowed). Residual (revision 8; corrected in revision 9): readable incomplete pending publication was not read; now it is. | `Rev8.test_two_failed_starts_then_recovery` (S1 and S2 killed by the setup timer before the first persist; S3 charges both, > 0.5 s each, admitted); `Rev8.test_elapsed_setup_is_charged_and_holds_at_the_cap` (3 s left, a 5 s old-clock read: the start holds; the next start charges ≥ 5 s from its process start); `Rev8.test_crash_after_first_persist_is_charged_once`; `Rev8.test_journal_session_without_its_clock_session_is_refused` (the earlier crashed session dropped with a sum-consistent total and a rehashed marker; a duplicated session); `Rev7.test_failed_start_is_charged_at_the_next_start` |
| C | The observation cutoff on the fallback and the exit probe | `LocalCommand.poll` times an exit observation after its probe returned. `invocation_receipt` accepts the text of ONE timely observation: a read and parse completed before the deadline, in the loop or in the fallback read after the command ended (each timed after its parse); a late one sets `timed_out` and is never used; the earlier timely text is what is parsed. Scope: `run_local`'s evidence is the exit status (observed in time) and the output read after the whole group was killed and reaped, when nothing can still write it, so its read time is not a cutoff. | `test_ai_reader.Rev8.test_exit_observed_late_at_its_probe` (an exited leader whose probe returns past the deadline: refused; control: prompt observation accepted); `Rev8.test_fallback_read_past_the_deadline` (complete, parseable logs - content [x], model m, empty feature tags, not an equivalent receipt - the command exited before its first poll, the fallback read and parse finish past the deadline: refused; control: a prompt fallback read passes the timing/readability cutoff, timely-parse-positive only, corrected at revision 9) |

The retained-output run for revision 8: `reviews/2026-10-02_photo_suite_rev8_run.md` (historical).

## Revision 7: the conditions of RSC `c036c00` (A and B extended in revision 8; C completed in revision 8; D closed)

Codex's record RSC `c036c00` (not favourable to revision 6 at `bb4f076`) credited the escaped-member watchdog, the
answer-dictionary binding and the local-command cleanup owner, and left four reader conditions, answered here through
R052's handoff `cdefd254`.

| # | Condition | Where it lives | Evidence |
|---|---|---|---|
| A | A failed post-rename close must not qualify | `Clock.close` writes the closed clock and, only after that write fully returned (file, rename, directory fsync), the closure marker `clock.closed.json` (session, journal sha256, clock sha256); a failure after the marker's rename removes it. `admit_clock` requires the marker matching the clock's bytes. | `test_ai_reader_crash.Rev7.test_post_rename_clock_failure_and_stall_do_not_qualify` (the closed clock renamed into place, then its directory fsync fails - exit 1 - or stalls - exit 75: COMPLETE durable, clock reads closed, not admitted); `test_marker_failure_after_its_rename_is_removed` |
| B | Clock admission binding; failed-start charge | Scientific `score`/`admit` refuse a caller-selected clock. `admit_clock` also requires coherent totals (the total equals the sum of closed sessions' live seconds and crashed/failed-start charges) and the lower bound (at least the journal's charged attempt seconds). A pending-start record `clock.starting.json` is written under the setup timer (itself shortened to the cumulative time left); a start that dies before the clock's first persist is charged at the next start (same boot: until its setup deadline; otherwise the 30 s tail). | `Rev7.test_coherent_undercharge_refused` (an alternate 0 s clock; a sum-inconsistent total); `Rev7.test_failed_start_is_charged_at_the_next_start`; `test_ai_reader.Rev7.test_scientific_scoring_refuses_a_caller_clock` |
| C | The actual final observation time | `invocation_receipt` checks the observation's own time after reading and parsing, before accepting; `LocalCommand.poll` marks an exit observed after the deadline as a timeout. | `test_ai_reader.Rev7.test_already_exited_leader_observed_late` (timeout 0, instant exit: refused); `test_complete_logs_observed_after_the_deadline` (valid logs whose read/parse is delayed past the deadline: refused) |
| D | Overlength representation; declarations | For an ok end with a complete event stream, the answer must be the complete event answer (overlength: its first 2,000 characters) and `answer_len` its character count. Declarations: the 30 s allowances in the revision-5 table below are historical (revision 6 made the receipt-and-close allowance 60 s); "every descendant stays in the group" is qualified everywhere (a recorded escaped descendant is killed by identity; one that escapes and exits between samples is not observed - the accepted transient scope). | `test_ai_reader.Rev7.test_overlength_excerpt_and_length_bound_to_the_event_answer`; this file, `AI_READER_JOB.md`, the runtime docstring |

The retained-output run of the whole photo suite on revision 7: `reviews/2026-10-02_photo_suite_rev7_run.md` (historical).

## Revision 6: the conditions of RSC `b569f8a` (still in force)

Codex's record RSC `b569f8a` (not favourable to revision 5 at `2610d8a`) closed R2 and most of R1, R3–R6 and left four
reader conditions, answered here through R052's handoff `c39df47e`.

| # | Condition | Where it lives | Evidence |
|---|---|---|---|
| 1 | Watchdog retirement | `stage_a_watchdog.py` (shared): retires only when the worker's group AND every identity in the members file are gone; with the orchestrator dead it kills them. | `test_ai_reader_crash.Rev6.test_watchdog_does_not_retire_while_a_recorded_escaped_member_lives` (the leader answers and exits, its recorded child has left the group, the orchestrator dies before its cleanup: the child is killed by the watchdog) |
| 2 | `-o` evidence bound on ok | `ai_reader_journal._rederive`: an ok end must carry its retained `-o` evidence, whose sha256 equals both `file_answer_sha256` and the answer's digest; complete text must be exact and equal to the recorded answer (or the declared overlength form), and its length its byte length; an excerpt only beyond the 2,048-byte retention with the answer's declared length. | `test_ai_reader.Rev6Evidence` (the retained dictionary replaced by another self-consistent string, or by None, with the separate digest and answers unchanged: refused on the COMPLETE journal and at resume before any dispatch) |
| 3 | One deadline and one charge through closure | `ai_reader_exec`: a setup timer (300 s) is armed before ANY accounting I/O (`check_accounting`, the clock's first persist); the clock's cap guard runs until the run ends (closing the clock no longer stops it); the receipt charges `FINAL_WRITE_S` = 60 s for its append AND the clock's closure, under one timer cancelled only after the close; the closed clock session names the journal's sha256; `admit_clock` (used by the scorer) admits a COMPLETE only with that finished closure, its total within the cap and not above the receipt's. | `test_ai_reader_crash.Rev6.test_slow_receipt_and_slow_close_share_one_deadline` (receipt 2 s + close 2 s against a 3 s allowance: exit 75, the durable COMPLETE is refused by `admit_clock`; 0.3 + 0.3 s: closed and admitted); `test_setup_before_the_clock_is_bounded` (a 30 s stall in `check_accounting` ends at a 1 s setup timer, exit 75) |
| 4 | Local commands: ownership before spawn, explicit deadline | `ai_reader_runtime.LocalCommand`: the exit watch and identity read run inside a cleanup owner (a failure kills and reaps the whole group); an exit or a complete log observed only after the deadline is a timeout, refused by both receipts. | `test_ai_reader.Rev6LocalCommands` (a one-shot exit-watch failure after the command spawned a child: no process left; a late exit refused; complete invocation logs written after the deadline refused) |

## Revision 5: the conditions of RSC `1bf9890` (still in force; its timing values are historical - see revision 6)

| # | Condition | Where it lives | Evidence (tests in `tests/test_ai_reader.py` unless named) |
|---|---|---|---|
| R1 | Received evidence cannot be hidden by `exact=false` | `ai_reader_journal._rederive`: every COMPLETE retained event stream is parsed with the classifier's own decoding (UTF-8 with replacement - the retained text *is* that decoding), whether or not it decoded losslessly; an inexact text must carry a replacement character (representation consistency); head-and-tail evidence admits only a retained final error (isolation or overflow), never ok and never a retryable label; a provider/structural label refuses when the events carry an agent message or the retained `-o` file (now kept on every dispatched outcome, `FILE_ANSWER_KEEP` = 2,048 bytes) holds non-blank text; recorded event types must equal the retained events'. | `Rev5Evidence`: Codex's counterexample - a provider failure whose events carry a complete lifecycle with the agent message `unclear` or a `command_execution`, `exact=false` - refused on the COMPLETE journal (representation, agent message, isolation) and on the INCOMPLETE journal at resume with nothing dispatched; a non-blank `-o` answer on a provider failure; head-and-tail evidence on a retryable label |
| R2 | Structural-after-end recovery | `ai_reader_exec.Job._run`: after recovery and the sweep, the durable holds and the remaining time are checked BEFORE any preflight or new open record; a hold goes straight to the STOPPED receipt. The validator admits after a structural failure only tail repairs and the receipt. | `test_ai_reader_crash.Rev5Recovery.test_structural_after_end_first_and_later_request`: a durable structural end on request 1 and on request 2, a crash before STOPPED, then a restart: the suffix is exactly the receipt, one open record, nothing dispatched, the journal validates |
| R3 | Whole-group recovery, shared with Stage A | `ai_reader_exec.end_recorded` -> `memprobe.end_group`: every live member of the recorded worker's group (enumerated, anchored to the leader's identity) and every recorded member killed and confirmed gone; the watchdog only after. The shared watchdog checks the orchestrator's identity (pid + start) at arming, must answer ARMED before the dispatch record, kills the whole group AND the members file's identities on firing (SIGKILL at once), and kills a blocked orchestrator (stale beat or hard deadline) by identity. The pinned binary may fork: no no-descendant guarantee is claimed; every descendant in the group is killed with it. | `Rev5Recovery.test_immediate_restart_kills_unrecorded_members`: a recorded live worker with a child NO record names and a live watchdog - the child is found and killed, the watchdog killed last; `test_ai_reader_crash` (the watchdog windows) |
| R4 | The six-hour clock | `ai_reader_exec.Clock`: strict finite, non-negative, typed state before any work (`clock_problems`, also in `check_accounting`); counted from the process's start; a BEAT thread writes snapshots with no lock held while a write blocks (`close` waits for the write lock only 30 s); a GUARD thread with no file I/O kills a live worker group at cap - 120 s and ends the process at the cap (exit 75, no receipt); package and go admission bounded (`Deadline`, 900 s); an exhausted resume goes to STOPPED before any preflight; the receipt's clock includes the 30 s it allows for its own append and the clock's close, which a timer enforces; the crashed session's tail uses its watchdog's record (group and orchestrator death) and, for a blocked orchestrator never seen to die, runs until the restart. The validator admits COMPLETE only within `job_clock_s` - the old one-hour allowance is gone. | `Rev5Clock` (NaN, negative, bool and infinite accounting refused; the guard kills at the final reserve; the guard ends a process at the cap, exit 75; a blocked beat does not hold `close`); `Rev5Evidence.test_complete_receipt_over_the_cap_refused` (a 6 h 30 min COMPLETE refused); `Rev5Recovery.test_exhausted_resume_stops_before_preflight` |
| R5 | Local receipt commands | `ai_reader_runtime.LocalCommand` for `run_local` and `invocation_receipt`: its own process group, exit seen by kqueue without reaping, reads never past the 4 MiB cap, an output over the cap while running OR at a quick exit refuses, an independent deadline refuses, and on every exit the whole group and every sampled member are killed and confirmed gone before the reap. | `Rev5LocalReceipts` (a quick 5 MiB exit refused; a leader-first exit leaves no descendant; a timeout refuses with the group gone; the invocation receipt's deadline refuses with its descendant gone) |
| R6 | Strict admission and idempotent quarantine | Exact key sets per record type (`end` in its recovery, not-sent and classified variants); strict worker and watchdog identities (`memprobe.valid_ident`: pid = pgid = leader, `sec.usec` start, never bool); the begin receipt's image size and detail typed and equal to the frozen delivery, live and in validation; end bookkeeping fields typed (kill, overflow, cleanup, event types, notices, usage); a top-level `error` event is a notice only with a frozen message, else isolation; usage needs non-negative integer input and output tokens; MAX_RECORD per line and the 20 MiB file cap enforced before parsing (`J.read(cap=)`, `validate(raw_bytes=)`, the scorer's admission); one tail_repair per quarantine file, and a crash after the quarantine write but before the truncation records it once. | `Rev5Evidence` (exact schemas, identities, image size/detail, event types, usage, kill; the top-level error event; record and file bounds incl. a final reason expanded past 20 MiB; a duplicate quarantine record); `Rev5Recovery.test_quarantine_crash_before_truncation_one_record` |
| R7 | Declarations and retained run | This file, `AI_READER_JOB.md` and the module docstrings state revision 5's mechanisms and limits; "no program it may launch" is corrected (the pinned binary may run and fork). The retained-output run of the whole photo suite on this commit: `reviews/2026-10-02_photo_suite_rev5_run.md`. | that record |

**Exposure (revision 12).** Job (a) of 2 October called the reader with all 600 qualification images under revision 11;
the revision-12 package has made no call. Every check the package itself runs against the codex binary is local: `--version`, `features list`, `login status`, `debug prompt-input` (the CLI's local rendering of the
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
noun-phrase task contract (revision 12: one or two words, the shared matching rule), the grayscale gate, colour as a descriptive diagnostic, the referral fields, the nominal
limits 600/660/3/120 s/6 h, the private-qualification exception, S4 kept prospectively with its 13 written exceptions,
the journal with its hard-kill fixtures, format before matching, the source statements. The 600 requests, their image
bytes and hashes and the delivery order are byte-identical to revision 3; the prompt is not (revision 12 replaced it,
and the delivery receipt was re-rendered then and again for revision 13's binary).

## Revision 4's closures (still in force)

| # | Closure | Where it lives | Evidence (tests in `tests/test_ai_reader.py` unless named) |
|---|---|---|---|
| 1 | Approval and scoring identity | The **strict shared guard** (`stage_a_guard.require_go`, row 20's revision 4): exact key sets, 64-hex digests, non-empty strings, exact dates, 40-hex commit ids resolved to commit objects, one closed block, mandatory reviewed-commit re-derivation, review descending from the reviewed commit, ordered dates. `ai_reader_exec.package` binds **16 files** (adding `memprobe.py` and `stage_a_watchdog.py`, which the executor now imports or runs) plus the binary's realpath, sha256, **its package manifest's sha256**, version, sandbox-exec's sha256, the command template (argv, allowlist profile, environment keys, gate) and the instructions hash: **24 fields** with the digest (revision 13 adds the owned tree's hash: 25). In scientific mode the scorer **refuses a caller-supplied key, set, delivery or package** (`score`, `admit`) and validates the journal against the package's instruction pin and the frozen delivery. | `Approval` (positive control, unrelated approval, strict schema on the reader package, modified package, negative record, bound imports, a modified dependency moves the digest and the real package passes the schema, reviewed-commit re-derivation, mixed resumed state, nothing after a receipt); `ScorerAdmission` (synthetic refused without the flag and labelled, **scientific mode refuses a changed alias, a changed easy set, a changed set, a caller package and a caller delivery**, untracked and dirty raw, referrals carry identity); the row-20 guard fixtures in `test_stage_a_runner.py` |
| 2 | Reference and key | No redraw; 300 items, aliases and membership unchanged. The frame invariant now compares the **retained close** and the ratio directly. The key module states S4 as **"first-listed WordNet noun sense differs from the recorded target synset"** (sense order, not measured usage); the no-synset claim corrected (five synonym bases across three of the ten); the suffix audit **bounded to this candidate set** (13 heads the rule treats as plural-only, including the Latin binomial part *latrans*); the key's own rule text and audit note say the same. Collision populations: **24/23/6** including hook2's canonical hook; **23/22/5** excluding it; the new key removes **22 of the old 24 forms across 21 targets, five easy**, keeping hook and roll/bun; S1's 23 includes *drawers*. | `FrameInvariant` (+ retained close and ratio mutations); `KeyIntegrity` (counts 64/126/52/14 and S1–S4 23/4/5/60, full forms inherit their base's exclusion, the five no-synset synonym bases across three concepts, the wording matches the predicates); `KeyFunctions` under `.venv-build` (**full-form S1 checked prospectively over every admitted form: only hook2/hook(s) and roll/bun(s)**, the key rebuilds byte-identically) |
| 3 | Durable recovery and holds | **Holds are derived from durable records before every dispatch** (`ai_reader_journal.holds`, `smoke_status`): a structural failure anywhere; the smoke over **every attempt of the first request** — held on structural, isolation, overflow, **interrupted (uncertain, never passes)** or a no-image answer, and after a no-response final; passed only on a retained ok answer. The **incomplete journal is validated** before any resumed dispatch. A **watchdog** (`stage_a_watchdog.py`) beside every worker kills its group on the orchestrator's death, a stale clock beat (10 s) or the hard attempt deadline; **every exit path** — ordinary leader exit included — kills the whole group and every recorded member (pid + start time) and confirms them gone before the reap; recovery kills only identity-verified processes. | `test_ai_reader_crash.py` (15: the eleven windows; the worker killed by the watchdog within grace + 3 s after the orchestrator's death, both by os._exit after GO and by an external SIGKILL; attempt-1 windows: a durable no-image answer then a crash holds on restart; an uncertain first outcome holds; a never-dispatched first attempt retries; a crash after try 2 of the first request holds); `Executor` (smoke holds on structural, no image, three failures, **no image on try 2**, isolation, quick overflow; structural on a later request; a child surviving its leader's ordinary exit is killed; a stop during an open attempt reconciles it before the receipt; a tampered resumed journal refused before any dispatch) |
| 4 | The actual input boundary | An **ALLOWLIST** sandbox (`ai_reader_runtime.profile`): deny by default; only the codex binary may execute; reads of the attempt directory (the image), the auth file, the binary and its manifest and the system runtime; writes only in the attempt directory and the auth file; network outbound; eight named Mach services. **33 effective false + unified_exec true** is now **32 requested, 31 false + unified_exec true** (the two deprecated web-search disables replaced by configuration); unified_exec can exec **no program but the pinned codex binary itself** (which may run and fork - revision 5's wording). Per attempt the prompt-input receipt checks instructions, image **and the per-request user-text hash**; the **exec-invocation receipt** (fresh in every run's preflight, with fresh features and auth) shows exec's submitted input is exactly [image, prompt] and its sampling-time configuration (gpt-6.1-sol, medium, approval Never, ReadOnly without network, 150 features) agrees with `features list`; the request body itself is unobservable without a request and is recorded as such. Classification requires the **ordered unique lifecycle** and **event answer = -o answer**. | `Boundary` (real binary, no request: the allowlist denies the key, a sibling attempt's file, a home file, listings of /private/tmp, the home and the attempts root, and /bin/sh, while codex and its own image work; features 32/31; the receipt renders the prompt; the separator regression; the invocation receipt equivalent; lifecycle mutations — completed not last, two terminal events, two agent messages, turn.started twice, thread.started not first, item without id, item completed twice, turn.failed, usage missing; event/-o disagreement and a missing -o; notices vs an unknown error item; events beyond retention are overflow); `Executor` (receipt mismatch on the image or the user text holds before sending and leaves no directory) |
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
non-words (*gooses*, *tooths*, *childs*), so it is not a grammatical test. The frozen key is left as reviewed - agreed
by R052 and Codex (RSC `1bf9890` Question 3): the omission can only lower the reader's individual exact-match credit;
it is disclosed, the key does not claim complete accepted English naming, and any later addition would be a
prospective, separately reviewed change with fresh identities.

## What remains disclosed, not proved

- The serialised request body — the instructions and tool schema exactly as sent — is not observable without a
  request; the prompt-input receipt is the CLI's local rendering of the instructions, and the invocation receipt shows
  the exact exec's input and configuration.
- `unified_exec` cannot be disabled in 0.159.3 (nor in 0.160.0, measured 3 October); under the allowlist no program but the pinned codex binary may be
  executed (it may run and fork copies of itself, normally inside the attempt's process group; a recorded escaped descendant is killed by identity) and a command event would be
  ERR_ISOLATION.
- A descendant that leaves the attempt's process group and exits between two one-second member samples is not
  observed; one that persists is killed by its recorded identity.
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

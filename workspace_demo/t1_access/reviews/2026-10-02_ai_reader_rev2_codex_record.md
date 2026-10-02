# AI image-reader revision 2: Codex design and bounded-job review

Date: 2 October 2026, America/Phoenix. Reviewer: `GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.

**Verdict: NOT ON BOARD with qualification calls under RSC `fdbc11cd66c0a5165a79b14eeac6930088400c4d`. This is not a favourable review and cannot serve as the review in `AIREADER_GO.json`.** The AI-reader route remains workable. The redraw, task contract, grayscale gate and descriptive reporting are substantial repairs. Package approval, scoring provenance, recovery, isolation and hard limits still have concrete gaps. No qualification, audit or other model call is approved by this record.

This answers all seven questions in Unimog `prompts/2026-10-02_codex_r052_ai_reader_review_rev2.txt`, committed at `e5b1bb9a3c19e1561168a581c13923f59bc750af`, SHA-256 `9e327a26533361b6776e1b419e8cc6321159d26e086dc3f2d190e325f48303db`. Ownership was recorded at Unimog `932671d0`; handoff `cc91ddfb-5f3b-53c2-89e7-f5b47db00bac` was accepted before review edits. R052 retains the framework, source-policy decisions, ledger and dispatch; R084 retains implementation and reports. Only this review and Codex's own R052 log/lifecycle are owned here.

## Scope and exact evidence

The system proposes 300 reserved THINGSplus concepts, outside the current development pool, with one colour and one processed grayscale request per concept. A separate orchestrator holds the answer key. The proposed reader is Codex CLI 0.159.3, `gpt-6.1-sol`, medium effort, naming one image in a fresh request. Qualification concerns free naming only. Admission uses the 63 easy grayscale items; colour, paired degradation, full-panel strata and comparison with the human menu-choice norm remain descriptive. Later photograph, sense and distinct-view judgments keep their own bounded claims and referrals.

**Codex/GPT is the proposed reader. This is a design review, not independent evidence of its competence.** The owner’s no-new-human-reader decision is retained: use the existing human difficulty reference, and people for referrals. Inspecting the authorized qualification-key construction exposed limited intended labels, senses and aliases to this conversation and its metadata helpers. This conversation cannot become a naming context. No image was opened or named, no item was answered, and no model, source module, test, capture, fit, simulation, audit or cloud/HPC/account job was run. Three helpers inspected text/JSON and performed deterministic metadata arithmetic only; they finished. No source or framework was edited, and no worktree or push was used.

Read end-to-end: the submitted design, job, executor, scorer, frame, key builder, image/set builder and twelve test methods; set/key construction metadata; published concept/image tables and norm description; the saved THINGSplus notice and LICENSE; prior `cf3e49e` review; and owning framework §8.2. Git bytes at the submitted commit were used after live files moved. CLI version/help were read without a request. The builder's reported 12/12 tests and image-verifying dry run were **not rerun** by this review.

All eight supplied hashes reproduce from `git show fdbc11c:<path>`. Paths below are under `workspace_demo/t1_access/stimuli/photo/`:

| File | SHA-256 at the reviewed commit |
|---|---|
| `ai_reader_qual_set.json` | `f28c624c2028f3f9fc9200c56467776275fb6bbbe285327132b74d1dd7fde8d6` |
| `ai_reader_qual_key.json` | `95265605f2b0fc2b274b71dc028756fc6e37efa4ac14e554f6d9556e77b8236d` |
| `ai_reader_exec.py` | `31f28b9581f0e7d25b4855b6d7d128068579560ca76ce4eadaeb094706a4eab5` |
| `ai_reader_score.py` | `c9836fa548b06f54157033eb57f4903a659e1a395bda5f11a2f6d34c8ef0cd1a` |
| `ai_reader_key.py` | `7500164d2726d4435cf10be604d71488664e968dfe0ccdbc8aeb6f2f8b2abf42` |
| `ai_reader_frame.py` | `54935de726626bbadf9004732b75cb8f6a155576a76c7425bf4c0581deafc77f` |
| `ai_reader_qual.py` | `4704220fcc05daeaaa5281603e022dad5ee4029180222ce904594cbee4bec18e` |
| `AI_READER_JOB.md` | `cadaaff544cb1af78f88a9939ef2284dfb99f7d17e84e757547cc736b57cf2a0` |

Prompt SHA-256: `506341b5337a9e13bb6210508c8072d4efc9c6d3eace7ca402ec2bd8704c241b`. Read-only installed version check returned `codex-cli 0.159.3`.

During this review RSC advanced to `a59fc2d`, and Unimog `680b3f8c` recorded changes to the set, key, executor and key-module hashes, including plural-only repairs and a different approval guard. **Those changes are not reviewed or approved here.** Findings and line references below refer to `fdbc11c`, including its imported guard/enforcement bytes. The owning source must submit the exact replacement package before execution; a moved package cannot inherit this record's judgment.

## 1. Repairs 1–8: enforcement and test evidence

| Repair | What is now implemented | Evidence and remaining gap |
|---|---|---|
| 1. Task contract | `ai_reader_qual.py:52–58` freezes noun or noun phrase, or `unclear`, separate from the target model's token convention. All 29 phrase-only targets are expressible. | Prompt/set hashes agree. Scoring examples exercise phrases, but no actual delivery is established. Correct stale 37-item wording in the key-module docstring and framework. |
| 2. Normalization/aliases | `ai_reader_key.py:39–78` uses explicit normalization and validated plurals; `ai_reader_score.py:84–104` requires whole-answer equality. Eight error codes preserve denominators; close is descriptive. | `Scoring.test_normalise`, `test_codes`, `test_key_has_no_stemming_artefacts` cover selected examples. They miss specificity collisions and plural-only artifacts (§3). Matching precedes the format checks, so an internally multiline alias can normalize into success despite the stated explanatory-error rule. Freeze that precedence explicitly and test it. Silent executor truncation can manufacture a match (§4). |
| 3. Norm/frame repair | A1–A3 are prospective exclusions; the seed/procedure redraw yields 1,659 candidates and 300 items. | Independent metadata reconstruction confirms the draw, source counts and all selected key human fields (§2). The twelve submitted tests contain no frame/source-correspondence test. Add the direct filename/row identity invariant and basic finite/count validity; indirect ratios/labels are not a complete detector for future swaps. |
| 4. Completeness | `ai_reader_score.py:107–130` refuses missing requests, duplicate retained answers, unknown IDs and item/view mismatches. Exactly one response per 600 declared pairs is needed. | `Completeness.test_colour_alone_cannot_pass` and `test_duplicates_unknown_and_mismatch_refused` support those checks. Types, statuses, attempt numbering/order/caps and legitimate discarded-failure records are unchecked. Any falsey `retained` is counted as a provider failure. Completed-job and approved-package provenance are absent (§§4–5). |
| 5. Identity | Set contains prompt, reader, images, order, key hash and construction hashes; executor compares delivered-byte hashes and eight package hashes. | The hash reproduction is real text evidence, not verification of all 600 local assets or actual delivery. `enforce.py` and `stage_a_guard.py`, imported at executor lines49–51, are omitted from `BOUND_FILES`. The inherited guard does not bind the review's actual approval to that package; scorer/state also omit binding (§5). No submitted identity mutation test establishes this repair. |
| 6. Isolation | Fresh process/directory, opaque image filename, private home, tool-disable flags and event inspection are present. Raw-file tracking/cleanliness is required before ordinary scoring. | `Executor.test_isolation_check` detects two synthetic tool events; `Completeness.test_uncommitted_refused` rejects an untracked file. Neither proves effective CLI isolation, dirty tracked-file refusal, attachment delivery or complete event evidence. Classification order allows an isolation violation to become retryable (§4). |
| 7. Referrals | Scorer lines178–206 emit intended concept/sense, human reference, hashes, model, answer/order/reason and empty owner fields. Owner decisions do not mutate primary scores. | `test_three_easy_gray_errors_fail` verifies a count, one reason and empty owner decision. Full field fidelity is not tested. Model/prompt/image identity is copied from the live set, rather than established from the executed request; raw text may have been truncated. Reservation helper exists and current pool is disjoint; integration into the next draw remains required, not already enforced globally. |
| 8. Bounded job | Named limits, lock, atomic state and fsynced append log exist; attempts are charged before calls. | `Executor.test_run_retries_only_failures_and_recovers` mocks calls, bypasses GO and synthesizes answers from the key. `KeyboardInterrupt` runs `finally`; it is not proof of hard-kill durability. The append/state crash windows, uncertain returned answers, clocks, subprocess lifetime and output limits remain open (§5). The later 400-turn audit is a separate prospective allowance, not enforcement in this executor. |

The perfect-output, three-errors, provider-failure and gate tests support their selected scorer behavior. Most scoring tests bypass the committed-file gate. Twelve mock/static tests cannot establish real delivery, actual model competence, every crash boundary or operating-system resource enforcement.

## 2. Frame rules and redraw

The observed repairs are sound. Independent deterministic metadata reconstruction finds:

| Measure | Checked result |
|---|---:|
| Source concepts/root image rows | 1,854 /1,854 |
| Initial eligible frame | 1,677 =1,854 −121 pool −56 homonyms |
| A1/A2/A3 flags within that frame | 12 /5 /15; union18 |
| Clean frame /stratum populations | 1,659 /520,585,554 |
| Draw /per stratum | 300 /100,100,100 |
| Easy /phrase-only targets | 63 /29; eight easy targets are phrase-only |
| Item/view requests | 600 unique, complete pairs; delivery is a permutation with no adjacent paired views |
| Reserved concepts/current pool overlap | 300 /zero |
| Selected human ratings | 8–22; total4,399 |
| Mean exact human recognizability | 0.494871402417 |

There are 20 filename-concept versus image-row `uniqueID` mismatches in the release. **None survives the cleaned frame or the selected key.** All 300 selected human fields and concept/definition/display-label metadata match their source rows; recounting the published label responses for all 1,659 retained rows gives no count/modal-label inconsistency. No image content was inspected: these are metadata correspondence findings.

A1–A3 are useful diagnostics, but two swapped rows with equal ratios and compatible names could evade them. Freeze the direct invariant `filename concept == image-row uniqueID`, together with compatible concept metadata, for every retained frame row and the selected draw. Reject duplicate/missing identity rows and invalid norms; require finite proportions in [0,1] and integer counts with `0 <= N_correct <= N_ratings`, `N_ratings > 0`. Current retained metadata pass; this does **not** justify arbitrary wider exclusion or another redraw. Add targeted mutation fixtures for the known mismatch and an equal-ratio swap, rather than selecting more exclusions without evidence.

Pin the construction inputs, including both metadata tables, norm description and WordNet version/corpus, before rebuilding. Reproduced source hashes are concepts `3f05b6b748d1e1b685e15130d2487bff63f86e1f4da94a2a5d9e7dec073a48eb`, images `fd5b17635f0f6528f58decaf5a089587593708862d4ee7a2a72cd8aa57ce013c`, description `e6e9bf63304978460b9556ab965a1cd462041c724dee6fa92a386d31ef81252d`. This freezes a reproducible reference, not a guarantee of visual truth or absence from model training.

## 3. Alias specificity: what to freeze

Prune bare `bench` for the primary `workbench` naming gate. The source distinguishes a worktable from a long seat. A lemma belonging to a source synset is evidence for lexical usage, but does not by itself make an unqualified answer discriminate the intended concept under this task.

This is not one exceptional item. Metadata inspection finds **24 aliases across23 selected targets** equal another released concept's canonical name; six affected targets are easy. Ten alias strings are shared across five pairs of selected targets, including plurals; one of the ten affected selected items is easy. Examples below are construction metadata, never image answers:

| Accepted mapping in the frozen key | Source distinction requiring review |
|---|---|
| `roulette_wheel` →`wheel` | Gambling apparatus versus circular machine component |
| `headphones` →`phone` | Ear transducer versus telephone equipment |
| `porcupine` →`hedgehog` | Different animal concepts |
| `boxer_shorts` →`shorts` | Underpants versus trousers |
| `palette` →`pallet`; `parachute` →`chute`; `firecracker` →`cracker`; `mud` →`clay` | Distinct released concepts share admissible answers |

Adopt one prospective specificity rule across the key: canonical target names and valid inflections remain; aliases that identify another concept, a part, or a broader class are excluded from the primary gate unless a documented same-sense equivalence exception is defensible. Audit all collisions and freeze exceptions before calls. A collision is a review trigger, not proof that every synonym is wrong—`roll`/`bun`, for example, can be a legitimate equivalence. Broader responses may stay descriptive or become referrals. No owner adjudication adds an alias after seeing a response.

The claim that every alias source is the concept's own THINGS synset also needs qualification: **ten selected concepts have no recorded WordNet ID**, including one easy item, though all have definitions. Record the actual source fields and sense rationale.

Revision2's validated-plural rule still generates **eight invalid aliases across two targets, one easy**: `boxer_shorts` admits `drawerses`, `shortses`, `boxerses`, `underdrawerses`, `boxershortses` and `boxer shortses`; easy `scissors` admits `scissorses` and `pair of scissorses`. WordNet mapping back is not sufficient evidence of a valid singular-to-plural operation, and pluralizing the last token also corrupts the complement in “pair of scissors.” The submitted artifact test only excludes five earlier stems/inflections and misses these. Freeze plural-only handling and test those cases, regular and irregular legitimate plurals, and the collision policy. The later source reports a repair at `a59fc2d`; that is a replacement-package claim, not approval here.

## 4. Isolation and the attachment smoke request

The CLI construction is a useful starting point, but its prose overstates the guarantees. Local `codex exec --help` and the official [CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) describe `-i` as attaching images to the first message, `--ignore-user-config` as skipping user configuration, and `--ignore-rules` as skipping execpolicy rules. `--ephemeral` suppresses rollout persistence; it is not itself an instruction-isolation mechanism. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

The private home and empty non-Git directory remove the ordinary global/project instruction chain, but inherited environment at executor line211 is unrestricted, and system/cloud/managed configuration is a separate layer. Record the effective configuration and model-visible capabilities/instructions, sanitize or pin relevant inherited settings, and identify the actual executable and authentication route without exposing credentials. These are possible remaining paths, not an observed leak. [Instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic), [managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration).

Read-only restricts writes; it does not prove that repository/key files cannot be read. Feature-name availability in the dry run does not prove the actual request has no file/tools/MCP/web or parent-context access. Require an effective capability/isolated-context receipt and complete event evidence; if effective capabilities permit extra-file reading, constrain input access rather than relying on cwd alone. This does not require a particular VM design if the actual image-only capability boundary is established. [Permissions](https://learn.chatgpt.com/docs/permissions).

Specific executor defects:

- Lines222–224 classify nonzero exit or empty last message as provider failure **before** isolation inspection. A tool violation followed by an exit failure is retryable, despite the frozen rule. Check isolation first; a violation is a retained final error even without a usable name.
- A written answer followed by nonzero exit is discarded. Any received answer must be locked whatever its correctness; inspect durable output/event evidence before retrying a timeout or crash. An uncertain delivery is not automatically proof that no answer existed.
- `isolation_ok([])` succeeds. The parser ignores non-JSON lines, lacks required complete lifecycle/message consistency checks, and malformed JSON raises outside intended classification. Fail closed on absent, malformed, incomplete or inconsistent evidence; distinguish structural delivery/configuration failures from transient provider failures.
- Only event hashes/types and summaries survive, not the original events/stderr. Retain bounded raw evidence sufficient to audit delivery, actual model/prompt, tool events and outcome later.
- Line219 truncates raw answers to2,000 characters. This violates the unedited-answer requirement and can convert an alias followed by enough whitespace and an explanation into an accepted prefix. Preserve bounded original evidence and original length/hash; overlength must have an explicit final error code or declared mapping, never silently enter matching as a truncated answer.

The declared model supports image input, but documentation does not empirically establish this installed account/CLI delivery path with `view_image` disabled. [Model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

**A single prospectively designated first ordinary frozen request may double as the technical smoke request after package approval and owner go.** Count it as attempt1 of660, charge all its time/output, retain its outcome and include its final response in the ordinary scoring whatever it says. Validate attachment presence/digest and the effective prompt/capability/event receipt, not correctness. Never replace the image or tune the prompt/model on its answer. A returned wrong name or `unclear` is final, not a failed smoke to retry. A confirmed structural attachment/isolation/configuration failure holds the job after that control for a revised package; do not exhaust660 attempts on a known broken route. A different canary would require its own prospective declaration and counted allowance. This review performs neither smoke nor qualification.

## 5. Limits, recovery and identity

The nominal **600/660/3/120s/6h** allocation is reasonable as a bounded qualification job. The code does not yet enforce all those bounds or its no-answer-replay rule. The later **400-turn** audit is a separate job requiring its own frozen state/caps and qualifying result; it is not automatic audit permission.

**Approval and scoring identity.** Executor `BOUND_FILES` omits the imported guard and atomic writer. At this commit their hashes are `stage_a_guard.py=31493c52a9c801fb3f696be3d6274c1a036947ff2255697bbeec8b940ae8c70c` and `enforce.py=1e2d384366f6db5e67965493542561b9aca227d0cbbc0674ca28f5194cf5de0e`. Later edits can change enforcement without changing the eight GO hashes. The inherited `require_go` verifies a verdict supplied in GO, existence/hash/date of a referenced record, and current package fields; it does not parse an attestation that the record approved that job/package. An unrelated non-negative record can satisfy it. Conversely, a whole-text negative-phrase scan can reject a favourable record quoting an earlier negative verdict. Use explicit structured approval for the job and exact package: **review attestation = GO = recomputed package**, with record commit/path/hash and dated owner words. Bind imported implementation and actual executable/effective runtime identity. No cryptographic owner-identity workflow is requested.

State lines140–148 have no package digest. Scorer lines137–147 only require a tracked clean raw file, then load the **live** set/key without checking `key_sha256`, approved package or raw execution provenance. A committed raw file is useful, but does not stop later alias/easy-membership changes. Raw requests likewise lack complete package/model/prompt/job identity. Bind state, per-attempt raw records, completed job receipt and score/referrals to the approved package, delivered image and actual prompt/model; require the committed raw digest and key/set/scorer hashes. Validate retained/status types, legitimate failures, first-answer ordering, unique attempt IDs, declared delivery order/counters/caps and final completion before admission. Synthetic tests need an explicit fixture mode that cannot be mistaken for scientific execution.

**Crash recovery.** A retained answer is fsynced at line179 before state persistence at182. A hard kill in between leaves an open request in durable state; restart lines142–146 invents a failure and asks again although the first answer exists. The terminal no-response branch lines162–164 also appends before persisting retained state. Recovery's own append/persist gap can duplicate failure records. State can skip a request whose raw answer is absent, and raw partial-tail repair/reconciliation is not specified. Use a durable attempt journal with unique IDs, recover committed answers from the journal without another call, handle incomplete tails and reconcile counters/state exactly. A killed/uncertain in-flight request needs a prospective conservative rule; arbitrary retry can select among answers. The submitted `KeyboardInterrupt` fixture exercises `finally`, not the hard-kill windows. Add non-model crash fixtures before/after dispatch, response receipt, raw fsync, state replacement, terminal no-response and recovery persistence.

**Clock/process lifetime.** The six-hour check precedes each call and gives that call a fresh120s even near the deadline. Startup hashing, recovery and final writes are outside or after the timing check; hard-kill tails are lost, and `started_wall` is unused. Define job wall/active/downtime semantics; charge startup, uncertain crash time and finalization conservatively. Bound each attempt by remaining time with finalization reserve, and use an independent bounded stop/kill/reap path for the exact worker/process group so provider work cannot survive a nominal timeout/restart. `subprocess.run(timeout=...)` alone is not an exact wall deadline including process creation/termination or a guarantee of descendant cleanup. [Python subprocess documentation](https://docs.python.org/3.12/library/subprocess.html#subprocess.run).

**Output/completion.** Raw size is checked before calls, not before each append; an append can cross20MiB. Captured stdout/stderr and temporary output are unbounded. Bound/reserve actual capture and every final write, with an explicit overflow outcome and unedited evidence policy. At the aggregate attempt limit the code checks the cap before the exhausted-request no-response branch, so it can hold before writing the final error. Specify bounded STOPPED/complete status and safe terminal accounting; incomplete jobs cannot qualify. No resets/extensions/substitutions or post-answer retries become permissible through these repairs.

## 6. The two R052 rulings

**63 easy, 61 of63: confirmed.** Independent arithmetic gives the one-sided95% Clopper–Pearson lower bounds:

| Successes | Point accuracy | Lower bound |
|---|---:|---:|
| 60/63 | 0.952381 | 0.881501223646 |
| 61/63 | 0.968254 | 0.903419988707 |
| Historical59/61 | 0.967213 | 0.900365119806 |

Thus at most two grayscale easy errors pass the adopted rule. The frozen membership, not an approximate90% point score, determines the gate. Interpret this as the adopted naming benchmark under its binomial model, not a guarantee of future photographs, independent colour/gray trials, all four audit judgments or human equivalence. Correct ratings to **8–22**, not9–22: one easy item has8/8; source counts match. Paired views remain300 pairs, not600 independent images.

**Qualification source-policy exception: preserve the adopted restricted-use decision, correct the evidence claim.** The saved [notice](https://osf.io/ahg2k/) and [LICENSE](https://osf.io/52wrx/) hash-match the set and assert a collective CC0/public-domain basis while acknowledging possible misattribution. They do not establish actual provenance/licensing of these300 images. Their hashes are respectively `bdda43a819803658fb0e3611cdfa571a2b2dc2f3a3429617a4cf1169ace1e69e` and `de570769b5545d7b9a7f9165b9da691370fa680330a8b2bf73cd9368ba1dbc97`; the source archive hash is `ed86912f6848ac5cf8b405a727f875295cc081cdd64271e80ae4d607b7d447e3`.

R052 has now explicitly adopted a private-qualification exception; this meets the prior request for a policy decision. I accept keeping it as a project scope rule based on the collective release, with unverified per-image provenance, known-conflict exclusions and the stated no-publication/no-stimulus-redistribution boundary. This does not attest that every actual source licence permits the use or that all300 are individually CC0/cleared. Source sites have conditional licences; the checked development subset cannot establish the qualification panel’s rights. [Pixabay terms](https://pixabay.com/service/terms/), [Pexels licence](https://www.pexels.com/license/).

Replace “transmitted once”: there are600 planned colour/grayscale transmissions, with up to660 attempts and repeat transmissions on permitted failures. External reader transmission is a use/disclosure even when no qualification image is published in the paper. Record that limited use honestly, the collective basis/caveat and actual known exclusions. Keep per-image capture/publication clearance for later study stimuli; qualification does not clear formal reuse. This wording/evidence correction does not require a new human panel or silently impose the capture gate on every private qualification request. If the owner instead wants an affirmative claim about every actual licence, that claim needs actual supporting provenance before it can be made.

## 7. Exact closure list for a replacement package

These seven groups cover the outstanding defects above; they do not require qualification performance before qualification starts.

1. **Bind approval and execution/scoring identity.** Structured job/package attestation checked against GO and recomputed hashes; imported enforcement/guard and actual executable/effective runtime bound; immutable package digest in state/raw/completed-job receipt; committed raw plus frozen key/set/scorer checked before scoring and carried into referrals. Add refusal fixtures for unrelated approval, modified dependency/key and mixed resumed state.
2. **Freeze reference/key integrity.** Direct filename/row/concept correspondence and finite/count invariants, construction-source and WordNet identity; retain the verified redraw unless the check finds a genuine additional defect. Correct8–22/29/no-synset wording. Uniform specificity rule, documented equivalence exceptions and plural-only repairs frozen before answers; targeted swap/alias/inflection fixtures. Reservation enforcement belongs in every next draw, with available source-group exclusions, without casually rebuilding the current pool.
3. **Make first answers and recovery durable.** Unique attempt journal, raw/state reconciliation and tail handling, no replay after any durable answer or isolation violation, conservative uncertain-attempt rule and hard-kill fixtures at every stated window. Process-exit failure does not discard a received answer.
4. **Establish the actual image-only request boundary.** Effective instructions/configuration/authentication route/capabilities receipt; appropriate environment/input-access restriction; complete bounded raw events/stderr and fail-closed parser/classification. Isolation checked before retry eligibility. Designate the counted first frozen request as technical smoke, retain whatever it returns, and hold immediately on structural delivery failure. No response-driven tuning.
5. **Enforce elapsed/output/process limits.** Controller deadline with remaining-time attempt limit, startup/crash/finalization charges and reserve, exact kill/reap and lock lifetime; strict capture/raw/temp/final-write caps and overflow handling; bounded complete/STOPPED receipt. Demonstrate these with non-model mechanism fixtures. Keep660/3/120s/6h without extension; later400-turn audit gets its own job enforcement.
6. **Validate complete raw evidence before admission.** Full schema, statuses, ordering, attempts/counters/caps and completion; preserve unedited bounded answers or explicit overlength error evidence; freeze format-versus-normalization precedence. Test tracked-dirty raw refusal, invalid discarded/retained records, changed key and truncation/format edge cases. Primary whole-answer grayscale gate, paired descriptive results and owner fields stay as adopted.
7. **Align the owning source statements and resubmit once.** Record restricted private qualification on the collective-release basis, actual300-image provenance unverified and repeat transmissions possible; preserve known-conflict and publication boundaries. Update the framework/job/design claims to the implemented guarantees, include named test/mechanism evidence, and submit the exact committed replacement hashes for review before owner go or any reader call. R052 owns those source updates/dispatch, R084 implementation.

The eight supplied hashes are a reproducible description of the submitted package, not a favourable attestation. Newer `a59fc2d` changes and any subsequent revision require their own exact-package review. This assignment is complete with this record and its one authorized completion report to R052.

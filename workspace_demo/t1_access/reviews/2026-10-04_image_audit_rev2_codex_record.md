# Image-audit revision 2 — not favourable

Date: 4 October 2026 (Phoenix). Reviewer: Codex, `GPT: R052 Entropy paper`.
Exact candidate: `d2b42cd339a47e0cbc35707af44de36922cf1479`
(repairs `4edd80f` plus `d2b42cd`). Retained suite:
`9c987a9a7ceac46b55ea9d28d473d6c4ad38d095`.
Incoming: Unimog `a3c03e4d9fefc96ca0c98bd7cae89a811b3c93bf`,
`prompts/2026-10-04_codex_r052_image_audit_rev2_review.txt`, SHA256
`ce43f58bc680d68bb0c9fd036fa4bd08d614f57afa08d405380601ead9a1a735`.
The whole R084 revision-2 companion was read. Ownership: Unimog `f1db3d2f`,
committed before acknowledgment of `bd1f5276-0723-5281-b02b-b106c91b9146`
and before review edits/delegation. This is the requested bounded re-review of
`1b17d64` findings 1–3 and the listed corrections, not a new scientific review.
Source references below are exact-candidate lines under
`workspace_demo/t1_access/stimuli/photo/`, except the named audit-app freeze.

## Verdict and system understood

**NOT FAVOURABLE to this exact image-audit package.** The earlier round-number,
predecessor-provenance and referral-policy findings are repaired. Two production
integration defects remain: scientific construction captures qualification paths
before audit configuration, and later-round admission passes a predecessor map
where the set builder requires the complete admitted chain. They prevent the
declared audit from working on its ordinary documented path. Neither finding
requires an invented crash scenario or an additional campaign allocation.

The audit reuses the admitted revision-17 reader for fresh stateless image-only
questions about 32 primary photographs and fixed-ranked second-view candidates.
Round 1 plans 224 requests, completing the eight Stage A concepts before the
other 24; names precede labelled questions within each block. Later rounds should
audit only the next eligible candidate for unresolved concepts, on authenticated
complete scientific predecessor outcomes, carrying all admitted attempts and
seconds within one aggregate 400-attempt/six-hour envelope. The amended rule
permits automatic fixed-rank succession while retaining every failed candidate
for owner adjudication. An earlier owner-passed candidate wins over a later
mechanical pass without changing either reader answer.

The owner's standing **“Go if favorable”** (4 October, Unimog `f009a600`)
carries across revisions without expiry. R052 binds it on the first favourable
exact-package record that R052 verifies. Its condition is unsatisfied here;
this record cannot bind `AIAUDIT_GO.json` or authorize an audit request.
No routine new owner turn is needed merely to reuse that standing approval after
a repaired package earns a favourable exact record. Source owns binding/dispatch;
root made no request and edited no go file. Per-image provenance/license checks,
owner adjudication, an actual-final-pair check after primary replacement, a
cleared P=2 manifest and row 21's separate package remain later gates.

## Two production findings

**1. The scientific job captures qualification paths before audit configuration.**
The public `run(k)` now constructs `AuditJob(k)` first
(`ai_audit_exec.py:388–389`). Its constructor calls inherited `Job.__init__`
(`291–296`), which in scientific mode copies module `IMAGES`, `JOB`, `RAW` and
`ATTEMPTS` into `self.images`, `self.job`, `self.raw` and `self.root`
(`ai_reader_exec.py:661–674`). A fresh documented CLI process still has the
qualification defaults: `captures/ai_reader_qual`, `captures/ai_reader_job`,
`ai_reader_raw_responses.jsonl` and `/tmp/rq` (`96–102`).
Only afterward does `AuditJob.run` call `configure` (`298–300`), which rebinds
the module globals to the audit round (`ai_audit_exec.py:265–268`). It does not
change the already captured instance fields. The module docstring's claim that
every Job method reads all these names at call time is therefore incorrect.

Consequently a fresh scientific `run 1` uses audit set/delivery/go and limits
but inherited accounting opens the captured qualification job. Before `_admit`,
inherited `run` creates the job directory, writes its pending start and takes
that job's lock (`ai_reader_exec.py:732–746`); if accounting proceeds, it checks
that qualification job/raw and opens/persists its clock (`782`, `801–809`).
The audit's go/package admission occurs only inside `_run` (`848–849`).
After admission, journal recovery reads `self.raw` and rejects records with a
different package/mode (`850–857`): an existing qualification journal produces
a mixed-package refusal rather than an audit round. If the journal is absent,
attempt images and sweep roots still point at the qualification namespace;
the audit scorer expects the separate round-specific audit raw/clock.

This can touch accepted qualification accounting before audit admission and
cannot produce the declared audit in its own namespace. No actual qualification
journal, image or clock was inspected, and no damage or dispatch is asserted as
observed. The previous candidate configured before constructing the Job; this
ordering regression is new, independently of the repaired chain guard.

Required repair: establish all audit instance paths coherently before any
inherited accounting, while retaining positive-round and predecessor refusal
before a clock is opened. Merely rebinding the module after construction is
insufficient. Retain a no-provider fixture that uses the production construction
order and verifies audit images/job/raw/attempt roots and clock ownership, with
the qualification tree unchanged and the real admission boundary reached.

**2. Later-round production admission passes only `priors` to a full-chain API.**
Production `_admit` calls `S.check(self.round, chained["priors"])`
(`ai_audit_exec.py:324`); `plan` makes the same call (`375`). `S.check` passes its
argument directly to `derive` (`ai_audit_set.py:277–281`). For every `k > 1`,
`derive` requires top-level `chained["round"] == k` (`159–162`), then uses nested
`priors` for outcomes (`135–145`) and `evidence` for provenance (`252`).
`Chain.admit` returns that full wrapper, but its `priors` field alone is only
`{j: authenticated_score}` (`ai_audit_exec.py:224`, `232–233`). It has no top-level
`round`, `priors` or `evidence`.

Even an honest authenticated scientific round 2 therefore fails with
`refused: round 2 is derived only from its admitted predecessor chain`.
`plan 2` fails before preflight. After repairing finding 1, `run 2` would still
fail this check after opening the audit clock, before preflight/begin/dispatch/GO.
It independently prevents the declared automatic succession. The scorer's
cross-venv helper correctly passes a complete chain; that different caller does
not repair the executor or plan call.

Required repair: pass the complete admitted chain consistently at both callers,
then retain a positive later-round fixture traversing the production `_admit`
and set-check interface, including its round/priors/evidence provenance and
remaining allowance. It can use an isolated offline provider substitute; no
real audit request is needed to demonstrate this interface repair.

## Disposition of the previous findings and corrections

**Previous finding 1 — closed.** `require_round` requires a plain `int` in 1..8,
rejecting bool, nonpositive values, strings/floats and values above eight
(`ai_audit_exec.py:143–148`). Construction, configuration, chain and set
derivation/build/hash entry points invoke it before their substantive work.
The old independent nonpositive namespaces cannot reach the public scientific
Job. The retained invalid-round fixture checks seven values through four entry
points with no target dispatch/new job directory; those subcalls are one
collected method, not 28 additional passing methods.

**Previous finding 2 — closed in the reviewed chain mechanism.** Each contiguous
predecessor has committed clean byte-equal raw and score, is re-admitted/re-scored
by the bound scorer, must reproduce the committed score bytes, and must match
scientific mode, identity and strict finite nonnegative current charges
(`ai_audit_exec.py:192–233`; `ai_audit_score.py:104–124`, `204–222`). Eligibility
comes from those admitted scores; attempts come from the admitted journal and
seconds from the current finished clock, not a self-declared score-time field.
The synthetic escape is removed. Ended current receipts/scores, missing or
STOPPED predecessors, stray future job directories and exhausted aggregate
allowances refuse before inherited accounting; planned requests must fit the
remaining allowance. The old false-carry/ended-round re-charge traces are closed.
These repairs are credited despite the separate integration defects above.

The build-venv scorer now delegates set/key re-derivation to the bound image-venv
builder, carrying its authenticated chain and comparing derived hashes with
committed set/key/delivery (`ai_audit_score.py:180–201`); lazy image imports remove
the scorer's unnecessary canvas dependency. Recursive verification descends to
smaller positive rounds. Successful pre-clock verification time is included
conservatively by inherited `t0` plus process-age accounting; no uncharged
successful forward is demonstrated. `_readmit` permits increased predecessor
seconds while an existing Clock retains its initial cap, which is weaker than
literal unchanged-time wording. No ordinary valid-clock increase path was found
after ended-round refusal and closure-hash checking, so this is a qualified
handling/documentation limit, not a third extra-send blocker.

**Previous finding 3 — closed.** The bound job and freeze contain an explicit
dated pre-answer amendment declaring automatic fixed-rank succession and
mandatory owner adjudication of every failed candidate
(`AI_AUDIT_JOB.md:3–11`, `131–145`; `IMAGE_AUDIT_FREEZE.md:7–17`, `90–93`, `113–128`).
`resolve` keeps the first reader-pass or owner-pass in ascending rank, leaves a
reader-failed owner-pass labelled as such, and marks later eligible candidates
superseded (`ai_audit_score.py:130–173`). Primary/exhaustion holds and Stage A
bundle consequences remain; primary replacement cannot inherit a former pair's
distinctness result at future manifest admission. The three resolver fixtures
exercise earlier-owner-pass, pending and fail/hold/replace dispositions.

The scorer's `candidates_failed_listed_for_owner` is a separate mandatory
adjudication category from its primary/exhaustion `referrals` array.
`referral_count` counts only the latter. Owner-facing transfer must include the
candidate list across all rounds; this separate representation is acceptable
under the amended rule, not permission to omit those failures. `resolve` assumes
authenticated score inputs and genuine owner records. It checks decision kind
and truthy date/decider, not date chronology/evidence authenticity; its compact
output is provisional, not a cleared P=2 manifest. Original owner records and
all outstanding adjudications remain requirements of later admission.

| Listed correction | Revision-2 disposition |
|---|---|
| Commons rendering versus original bytes | Closed: job names the downloaded rendering truthfully; `source_sha256` hashes those bytes and `commons_original_sha1` is separate. Original dimensions/MIME/SHA-1 do not assert original byte size or equivalence. |
| Numeric primary human norms | Closed at source path: bound image-table columns convert to float/integer values and feed scored metadata; Commons values remain absent. The new table pin is independently hashed only. No actual human-table values or universal consistency claim were reviewed. |
| Exhausted-concept prior history | Closed: referrals include admitted earlier failures plus current failures, with their complete predecessor scores retained (`ai_audit_score.py:305–336`). No fixture here drives the full exhaustion/history aggregation. |
| Request order wording | Closed: job/set say names first within each pilot/nonpilot block, matching implementation. No global-all-names-first claim remains. |
| Final pair after primary replacement | Closed as a declaration: the actual final pair must be checked at P=2 admission; no replacement/manifest has been cleared here. |

The earlier bounded acceptance of exact pinned renderings, the 384×784 two-canvas
comparison, isolated reused reader/per-request prompt receipts, yes/no/unsure
wording and weak fixed-ranked candidates as filter inputs stands. None proves
human equivalence, view independence, blind calibration, a complete final bank,
or permission for more attempts/time. Reader qualification remains its disclosed
third exposed pass with three owner adjudications; partial text remains no answer
and the capacity detector retains its visible-evidence scope.

## Independent pins and retained evidence

Root independently reconstructed all **39 fields** from exact Git bytes plus
current external runtime pins using an owned stdlib Git/hash/AST helper, never
importing or executing submitted code. All 28 bound file hashes equal live bytes.
Digest: `2183a62f4b5cf114afc8c48a6d42aafba41c0f7fd66c7fd26322005669ef2c1a`.
The new `things_images_metadata_sha256` is
`fd5b17635f0f6528f58decaf5a089587593708862d4ee7a2a72cd8aa57ce013c`;
both THINGS tables were byte-hashed only. Owned CLI binary/tree/manifest,
sandbox and command-template pins match; CLI version comes from the owned
manifest plus retained metadata, without executing the binary. Eight existing
fields changed: executor/set/scorer, job/freeze, round-1 set/key and digest.
Round-1 delivery is unchanged. Reader's 25-field digest independently remains
`4517553a0615436d8a0c384849c43a206fd9e428729d1d91ef6a0d68bf4b3e35`, equal
to its existing go package. External runtime pins are current byte observations,
not a claim that every input resides in the reviewed Git commit.

All 15 public retained inventory size/hash pairs at `9c987a9` match. Main suite:
420 = **376 OK + 1 FAIL + 43 skipped**, exit 1. Build: 27 OK, exit 0.
Together: **403 passing executions, 393 distinct exercised methods, 392 distinct
passing methods and 11 passing repeats**. The separately retained controller-only
rerun has 55 OK, exit 0: all repeat previously exercised methods, 54 repeat passes
and the failed method passes there. All retained runs therefore give 458 passing
executions and 393 distinct methods that passed at least once; the original
main-suite failure remains. The 43 skips comprise 16 WordNet methods restored in
build and 27 unexecuted transition methods (5+10+5+7). No all-green main suite or
fresh science/Stage A/reader/row-19 verdict follows.

The failure is unchanged `Controller.test_persistence_failure_is_bounded`:
expected `persistence failure`, observed first-stop reason sampling **0.084 s >
0.05 s** (`tests/test_controller.py:949–965`). Exit 75 passed, but later no-final/
time assertions were not reached in that failed execution. Controller and test
source hashes are identical between `5f08728` and this candidate. The separate
rerun completes those assertions. This is consistent with competing fail-closed
guard ordering in the unchanged fixture; the retained log does not prove the
scheduler/load cause or erase the failure. It is not a new audit false-admission
finding, and no reviewer rerun was performed.

All **26 audit methods** pass (19 more than the former seven). They meaningfully
cover synthetic real-temporary-Git commitment, exact re-scoring, current-clock
admission, invalid rounds, tampered charges/outcomes, dirty score, synthetic-mode
refusal, changed clock, STOPPED/missing predecessors, reduced aggregate caps,
stray directories and ended-round clock-byte preservation. The honest synthetic
round 2 sends four requests with a five-attempt local cap. Wrong-prompt refusal
proves that question unsent, while an earlier name question was already sent;
pure yes/no/delivery/charge checks cover selected cases. Resolver tests use three
handwritten item records, not real owner decisions or manifest admission.

Those tests do not cover these production defects. `World.run` supplies explicit
fixture paths, avoiding the qualification-default capture
(`tests/test_ai_audit.py:137–138`; inherited constructor `665–668`). Fixture
`AuditJob._admit` re-admits the chain then returns inherited fixture admission
(`ai_audit_exec.py:313–316`), bypassing production go/package/set checks and its
priors-only call. The two cross-venv fixtures exercise round 1 only and call the
scorer helper with a full chain (`tests/test_ai_audit.py:379–401`). None proves
positive scientific round-2 admission or the complete build/image/scientific
chain. Teardown restores fixture caps and removes temp trees, without an
independent universal process-extinction assertion. Retained passing fixtures
are credited for what they assert, not as coverage of a bypassed branch.

## Review boundary and attestation

Three read-only peers supplied scoped execution, evidence and design findings;
root integrated them and independently measured package pins. No submitted
module/import/function, test/fake/fixture, CLI/provider/model/reader request,
forward, scoring, archive or simulation was executed by this review. No actual
audit/capture image/array/tensor, raw reader journal/answer, generated key
semantics, plant/human/private output, audit website or D1 was opened. No SSH/PBS/
account/remote-job action, worktree or push. Source owns code/current docs/
frontmatter/INDEX/tracker/ledger/go/results/dispatch; root owns only this review
and its own R052 append/lifecycle/prompts. Foreign files, source jobs, exposures
and old completed reviews/reports remain intact. Next reconsideration requires
the two narrow production repairs and fixtures traversing their real interfaces.

<!-- STAGE-ATTESTATION v1
{
  "row": "aiaudit",
  "stage": "audit",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-04",
  "reviewed_commit": "d2b42cd339a47e0cbc35707af44de36922cf1479",
  "package": {
    "AI_AUDIT_JOB_md_sha256": "6a74868a1a9bd3f71bc2b4a1c7db78385cf71851c9ef7f5857a5afb2dd2f1e2d",
    "IMAGE_AUDIT_FREEZE_md_sha256": "7710b9c6c717115c65de6517d693c9d33dae10a045d6cdb79076e2e2007242df",
    "ai_audit_delivery_r1_json_sha256": "cdd363316064a315f77217f267af4e1cbd1d76a96e65306d06e98d4d0887bb60",
    "ai_audit_exec_py_sha256": "f5ee2d6340199c616e6c231a1450968d1c652f496eba792921406c1d30676bd4",
    "ai_audit_key_r1_json_sha256": "d931129d59a19c9385d9e21e052f07e375f3f67800c4c0d28ccaf0d00461ce53",
    "ai_audit_score_py_sha256": "ae9775bae2741cae1936ae430d64fac41e29e6193e90a955c6598810f6450015",
    "ai_audit_set_py_sha256": "1885611be6d68264b1b87b9577509e155a634c1bec69d5142a365d36b049b37d",
    "ai_audit_set_r1_json_sha256": "ffc1c7c46e3ec755f55bc3086338541b9476e16893f160485fad4b1ef6d3df95",
    "ai_audit_sources_json_sha256": "5127035ca91c1cd1ba23b29f0c83802fa795fe8e0ea257e29484019336b6d7b4",
    "ai_audit_sources_py_sha256": "16d9d4bb6d18c3e500e8baeb5bb8aef681c29a08b4f9f27976cea6c3b33c7794",
    "ai_reader_delivery_json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
    "ai_reader_exec_py_sha256": "5fbb730d1f10c6c38dc638f06a7d1f57e724ed7efeba8e8a7b93382d783ae097",
    "ai_reader_journal_py_sha256": "b67d25526c715434b55e6410d1b66046a9437ca48c825c34fabd9705515613a2",
    "ai_reader_key_py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_qual_set_json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
    "ai_reader_runtime_py_sha256": "cb78adaa56a34f45430ea26429dbc0aa1c204fc48bbec454f1af35ff42ebec32",
    "ai_reader_score_py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "audit_alias_map_json_sha256": "a3f6ab51dbf0dda1148a26bfdc8b671adf91d1edc712fe58ef9ddcffc0397c80",
    "audit_alias_map_py_sha256": "39088b6e0834c6bbdc704b77d010de7b22eba7afe9637f3bec0be3db0a1e2dd1",
    "audit_package_py_sha256": "e15b1a192060e20dfe62395211c34600c399fdd134233cb95eec742d787ed0ff",
    "cli_version": "codex-cli 0.160.0",
    "codex_package_json_sha256": "404c4c935bf9b7a57fc02b6f0d09ba6b7bbbf15cf14286fc017de2a6c01cab47",
    "codex_realpath": "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/captures/reader_cli/codex-0.160.0/bin/codex",
    "codex_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b",
    "codex_tree_sha256": "ced09ec2c51c8fd4ae4ccb7e0ccb6b6e76d32633ec842f08be000c2a55ba86fe",
    "command_template_sha256": "c36c43f34d8658dd14e3e332f1ae354328950eef4a152b9cf79dffcecc51361a",
    "dev_pool_json_sha256": "fae20dc215d1de329ff81a5687735047c9a92cead1b9642f7cda4f6c2d69ad2d",
    "dose_py_sha256": "05d61ea6d199903eb066534e8cc2e7bb73e102b9cfa284f5692f8d75e9bb4302",
    "enforce_py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
    "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
    "manifest_dev_json_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "memprobe_py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
    "package_digest": "2183a62f4b5cf114afc8c48a6d42aafba41c0f7fd66c7fd26322005669ef2c1a",
    "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
    "second_view_candidates_json_sha256": "430b0ce8794910dcc6bd2aa939fa4ae7453018663667ba3f861b779b68e2d028",
    "stage_a_guard_py_sha256": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
    "stage_a_watchdog_py_sha256": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed",
    "things_definitions_sha256": "3f05b6b748d1e1b685e15130d2487bff63f86e1f4da94a2a5d9e7dec073a48eb",
    "things_images_metadata_sha256": "fd5b17635f0f6528f58decaf5a089587593708862d4ee7a2a72cd8aa57ce013c"
  }
}
-->

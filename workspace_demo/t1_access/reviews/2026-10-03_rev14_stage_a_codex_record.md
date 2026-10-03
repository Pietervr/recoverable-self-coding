# Row 20 Stage A revision 14 — Codex record

Review date: 2026-10-03 Phoenix; 3 October UTC. Exact reviewer
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: `c22cd323bf5262d59488b70a9433e13cfef3fa9c`.
Brief: Unimog `52a8436c0e160d96c2903aab51e0bfe18aa7a730`,
`prompts/2026-10-03_codex_r052_stage_a_rev14_review.txt`, SHA256
`595b5d8f31789e1ce2e414e7d19487766bf4a5aa5ae9bc28e1a97b82a7b68be5`.
Ownership committed at Unimog `6d056ac5` before handoff
`2523f030-aca3-54a7-8e9d-839cd0d991a4` was acknowledged and review work began.

**FAVOURABLE for this exact Stage A package.** R1's prepared-link recovery closes.
The six substantive R2 corrections are accepted, with the precise wording and
evidence qualifications below. No further implementation condition remains from
this bounded review. The accepted criterion/common comparator, normal chained
producer admission and counter carry remain unchanged.

The system retains the revision-10 instrumented records and revision-12 native
00–15 records, reconciles a prepared transition if needed, and would complete
native16–19 plus the report under a new exactly bound owner release and go.
The known15-native stop remains TERMINAL. This mechanism attestation grants no
release, rebound go, dispatch, Stage A PASS or Stage B authority. Reader REV12
`09bbe0e` remains favourable, separate and byte-identical in its bound package.

References below are sources under `workspace_demo/t1_access/stimuli/photo/`
at the candidate, or retained evidence under `workspace_demo/t1_access/reviews/`.

## Question 1 — prepared-link recovery

Yes. `identity_transition:818–885` now recognizes the exact prepared tail whose
from is the old ledger identity and whose to is the current package identity,
with the immediately preceding link ending at the old ledger identity.
It validates the embedded predecessor body, obtains the **current** valid
terminal release, refuses a release consumed by an earlier link, checks the
explicit frozen fields and refuses an open or interrupted attempt.

The expected record at865–871 includes from/to, predecessor package/review/phases,
every differing local-code hash, frozen-field list, completed-attempt ids,
counters and carry. A prepared tail must match those values exactly. Its branch
at873–880 changes only `identities.row20` and atomically writes the ledger;
it neither rewrites the transition receipt nor appends a third link. After the
slot has moved, the current-identity branch at839–840 returns without writing.
The completed map, attempts, counters, carry and original producer records remain.

`worker_open:888–912` retains the terminal gate before transition and Budget
opening. `stage_a_guard.terminal_release:137–152` checks the strict release
schema and the exact current TERMINAL bytes. A later controller failure voids
the old release. The new recovery permits a fresh valid release then while
preserving the prepared receipt's original historical release hash. Those hashes
need not be equal: reconciliation validates current authority, rather than
pretending the old release still covers changed terminal bytes. This is the
requested slot-only recovery, not another compatibility transition.

The unchanged phase-identity helper at801–815 and full pre-native admission at
1191–1224 enforce historical continuity and the other admission predicates.
Do not attribute an independent scan of every arbitrary earlier link to the
transition helper itself: it checks the relevant chain end. The actual submitted
two-link state is covered. Earlier transition-artifact trust and explicit
FROZEN_KEYS scope remain qualified; no generic forgery/authentication gate is added.

The five retained `Rev14PreparedLink` methods (`test_stage_a_runner.py:1279–1367`)
produce the requested evidence. `prepare:1286–1304` injects an OSError into the
ledger write after the actual transition path has durably produced link2; the
ledger is asserted still at revision12. Retry through worker_open asserts current
Budget identity, unchanged first/second links and INSTRUMENTED_DONE, unchanged
counters/completed map, no third link and successful full pre-native admission.
The four controls cover a repeat, stale authority after changed TERMINAL followed
by a new matching release, mismatched from/to, and changed counters/ids/frozen list.
All five methods are explicitly OK in the retained suite.

This is a producing synchronous write-failure/retry fixture, not a process-kill,
power-loss or hardware-fsync experiment. The repeat snapshot at1306–1307 covers
top-level regular files, not every nested output payload. Source establishes the
slot-only/no-op writes; these evidence limits require no additional run.

## Question 2 — six declaration repairs

Yes to the six substantive corrections:

- Criteria64–77 and the corrected resume record distinguish13 one-step maxima
  from01/08/11's two-step maxima;15-native remains0.125 at16.5. They define the
  larger-magnitude binade, state the16/15.9375 adjacency exception, and disclaim
  an observed rounding cause.
- Criteria90–94 states unchanged below16, never tighter and deliberately relaxed
  at/above16; earlier TERMINAL outcomes remain records requiring release. The
  numerical formula and its common worker/validator implementation are unchanged.
- Report520–524 calls the0.10 SVG guide the absolute floor. Markdown536–546 says
  it is not every logit's bound, retains maximum-absolute fields and adds the
  deciding component's difference/tolerance ratio and magnitude. Criteria81–83
  qualifies the table versus machine-report fields.
- Criteria458–466 gives revision13's293 collected/288 distinct/299 passing,
  21skips=16WordNet+5oldTransition and11build repeats. The current suite counts
  below are also correct. Readiness twice discloses copied development records
  as the exception to synthetic mechanism evidence.
- Criteria84–87 accurately limits the relabel control: known later-producer
  membership is accepted by the helper; only the undeclared hash then gets full
  admission refusal. It does not prove every relabel refuses.

These repairs do not make every remaining sentence literally exact. Preserve
the following **nonblocking editorial qualifications** when reporting this verdict:

- Criteria89–90 and stage_a.py81's sub-step/coincident-rounding rationale is too
  broad if read universally. Read it as same-binade reasoning, subject to the
  explicit boundary exception above; it establishes neither a rounding cause nor
  a uniquely optimal fidelity criterion. This does not change the accepted rule.
- The report prose says the deciding component is in the last two columns.
  It is actually in columns7–8, the two before argmax/pass. Full comparison fields
  are in machine JSON; native StopCheck includes steps, whereas the validator's
  PARITY failure tuple406–408 includes difference/magnitude/tolerance without
  steps/index. Do not claim every failure text contains every comparison field.
- Readiness's untouched-record statement refers to originals. Fixture copies
  are intentionally changed to exercise transition/release/refusal paths.
- The new report-label case1117–1122 checks source strings, not generated or
  rendered SVG/Markdown. It passed; it is not a report-output rendering experiment.

These are precise limits on prose and retained assertions, not unresolved
implementation or scientific conditions. No package edit, render campaign,
new fidelity criterion or blanket suite rerun is required by this review.
Any later bound-file edit nevertheless moves the exactly reviewed package.

## Question 3 — exact package, retained evidence and attestation

Independent standard-library git/blob/hash/JSON/AST metadata reproduced all five
fields in the single block below. Inner identity is
`3d6d991dc093ee373a4d4ee4acc21d7a72dc062af05b144de77aadea0600400c`.
Every identity-referenced blob/local-code hash and checked live bound file matched.
Both embedded predecessor bodies equal their immutable original identities;
only local-code fields differ from the current body, with frozen components equal.
Reader16 bound blobs and24 fields remain `09bbe0e`, package digest
`3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11`.
External executable/manifest/sandbox metadata was re-hashed without running a CLI;
unchanged template/instruction sources retain the prior independent reconstruction.

Retained suite `ef11c1fa7e0057d46bb758ac2a14588b598732c1` pins candidate HEAD
and empty pre-run photo-directory status; all ten declared sizes/hashes match.
Main299 collected,278passing,21skipped in2035.658s; build27passing in3.542s.
Both exits zero, no failure/error. The16WordNet skips run in build, with11repeats;
thus **294 distinct cases exercised and305 passing executions**. Five old
transition methods remain skipped. All five prepared-link, five parity, ten
normal-chain and39controller methods ran. Exactly six methods were added over
revision13; no old method was removed. Counts describe unittest methods, not subtests.

Copied development-record fixtures and retained assertions are implementer
evidence. Reviewers did not inspect actual/copy arrays or photographs, recompute
parity, or rerun submitted tests. The compound post-watchdog-loss/hung-sampler
residual still bounds the controller only, not whole-worker extinction or the
earlier ~21GiB/s margin in that branch. Previous engineering/exposure limits stay.

All three questions are answered: R1 closes; R2's substantive corrections are
accepted with the explicit qualifications; this exact package receives one
Stage A mechanism attestation. The new owner release and exact package-bound go
remain source/owner actions. The actual report must independently attain and
document Stage A's outcome; Stage B retains its separate gates.

<!-- STAGE-ATTESTATION v1
{"row":"20","stage":"A","verdict":"favourable","reviewer":"GPT: R052 Entropy paper / 01a0d19e-2127-7051-9a61-6db771088559","date":"2026-10-03","reviewed_commit":"c22cd323bf5262d59488b70a9433e13cfef3fa9c","package":{"criteria_sha256":"5a4ea075e2cddf068917890b75488c22a80bc2cc4c838078e9d3ada29e9b2be8","identity_sha256":"85b78de4a5951977ab271c0030bb1127a41d11df4c4babfef21c5eac78ee676b","plan_sha256":"3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc","manifest_sha256":"e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448","budget_sha256":"9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"}}
-->

Source owns implementation, captures, framework, ledger, protocol, release/go
and dispatch. Only this record changed in RSC. Read/reason, three read-only peers
and standard metadata only: no submitted module/function/import/test/fixture/CLI,
diagnostic/forward/model, new scoring/fit/science, remote/account/job operation,
raw tensor/key/private audit/human/pull output, image opening/naming, worktree or
push. Existing jobs/foreign files and prior one-time completion reports remain.

# Row 20 Stage A revision 10 — Codex review

Date: 2 October 2026. Reviewer: Codex, **GPT: R052 Entropy paper**,
native `01a0d19e-2127-7051-9a61-6db771088559`.
Reviewed candidate: **`fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`**.
Retained suite: `57007770f8ae135cdb6c45ab191d1cdf1b2de827`.
Prior review: `dda950bc71e7ec526dbc9bd99a988f23a527557f`,
`2026-10-02_rev9_both_packages_codex_record.md`.
Assignment: Unimog `prompts/2026-10-02_codex_r052_rev10_both_packages_review.txt`,
at `ebb1aaba954820ca9951765dde008819c58827db`, SHA256
`7dc8a36f318b0be8a6afff7ebe75cde70213d8e5c7fbf961f24a347ad15e117c`;
handoff `a91531fb-5fce-5aaa-a7c6-7c66372acd44` accepted after ownership was saved.

## Verdict and scope

**FAVOURABLE for this exact Stage A package as a bounded engineering mechanism.**
The remaining live-foreign-start condition of the prior review is closed.
No remaining Stage A review condition is imposed here. The owner's Stage A gate
question remains open: this record does not supply the dated owner go, authorize
a forward, establish fidelity or resource fit, or admit Stage B.

Stage A is the local native-fidelity/resource screen. Its envelope still carries
160 mandatory forwards, 18 planned diagnostics and 16 earlier engineering attempts:
194 of 200, with 1,808.73 seconds carried into the four-hour cumulative allowance.
The whole-task memory limit remains 48 GiB with a 44 GiB stop, and output plus
temporaries remains capped at 1 GiB. The earlier conditional about-21 GiB/s local
qualification and its scheduling, footprint and signal-delivery assumptions stand;
this review does not turn sampled memory control into a universal burst bound.

Read/reason only: immutable source, documentation, test source and retained textual
evidence were inspected, with independent read-only peer checks and standard-library
git/JSON/AST/hash arithmetic. No submitted program was imported or executed;
no tests, fixtures, CLI, model, image, forward, scientific run, cloud/account or
cluster operation was performed. No image was opened or named. Implementation,
framework, ledger, protocol, tracker and dispatch remain with their existing owners.

## Question 1 — live foreign start and producing evidence

The guardian's durable armed record now retains the protected controller's process
identity (`stimuli/photo/stage_a_watchdog.py:129–132`). Recovery is inside the task
lock (`stage_a_controller.py:501–509,525–530`). `_end_foreign` checks the retained
PID/start identity, sends SIGKILL to a matching live foreign start, and waits for
that identity to be gone before returning a confirmed-end wall time (`299–316`;
`memprobe.py:99–112`). An identity still live after the 10-second polling allowance
causes refusal/hold before its final charge is appended or pending evidence removed.
This is a local process-observation mechanism, not an arbitrary OS-stall guarantee.

Both pending-start and guardian-only recovery use it before the no-recorded-end
fallback (`controller:333–345,394–407`). Consequently a healthy, still-live S1 is
ended before its start-to-end charge is finalized. Each session becomes known after
charging (`352–382`), and persistence precedes pending-file removal (`530–546`).
A later guardian receipt for that session cannot charge it again. An interruption
before first persistence retains the old durable start evidence. The unresolved
foreign interval is not finalized on the hold; earlier successful reconciliations
may already exist in RAM, without a new durable clock or pending-file removal.

`tests/test_controller.py:597–644` **produces** S1 alive during S2 recovery, in both
directory and lock stalls. It starts a real subprocess with a healthy 300-second
guardian, waits for its actual armed record, then asserts the process and retained
identity are alive before S2 runs. It checks SIGKILL exit, identity gone, and exactly
one foreign-start entry. Against the guardian's later recorded death observation,
the charged interval is at least death minus start **less a 0.1-second tolerance**,
and at least one second (`640–641`). S3 leaves that foreign entry unique; S3 still
incurs its own session time. Neither a final charge nor an already-dead S1 is supplied
as the desired end state.

Limits: this new fixture directly produces guardian-only directory/lock recovery,
not a separate pending-file live case, stale identity or surviving-identity timeout.
The same helper's pending invocation, refusal, persistence ordering and known-session
checks support those bounded properties statically. These limits are not newly
discovered counterexamples or demands for an unchanged-path rerun. Previously closed
A1.1/A1.2, A2/A3 and memory/finalization/authority paths remain closed; no concrete
regression was found. Dead, unreadable and pre-publication cases retain their declared
conservative fallback and durability scope rather than becoming exact-time proofs.

## Question 2 — declarations 1–3

1. The untraceable armed-start residual is correctly qualified as 10 seconds ARM
   wait plus up to two seconds after the E message plus up to five after terminate:
   17 seconds nominal, **plus** startup and signal/reap latency (`criteria:55–61`).
   It is not a 17-second guarantee against unavailable or stalled OS operations.
2. `controller_fixtures.json` remains the pinned revision-8 sampling/tick/worker-kill
   record. Arming, release and reconciliation changed in revisions 9–10; their
   evidence is the new transition tests and retained suite, not a numeric rerun of
   that file (`criteria:34–40`; `READINESS_ROW20.md:22–32`).
3. Criteria section 6 now names the exact revision-10 retained run (`353–354`), and
   readiness separates numeric sampling measurements from transition evidence.

These declarations are materially complete and accurate within the stated scope.
Read the criteria's live-fixture summary at its actual 0.1-second tolerance and
read “S3 adds nothing” as no duplicate foreign charge; the stricter literal summary
is not the measured assertion. Declarations 4–6 are answered in the separate reader
record for the same candidate. No bound-file prose edit is required by this verdict;
any subsequent edit moves the reviewed package and must not use this attestation.

## Evidence, identity and remaining decisions

All five package fields in the block below reproduce independently from committed
blobs. The inner identity is
`e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38`;
the source membership/hashes and plan, manifest, packet, map and position-receipt
relations agree. This verifies committed metadata, not a new model/archive loading
or execution-identity run. Plan, manifest, budget and pinned numeric fixture are
unchanged from the previous candidate; criteria and identity moved.

The retained run record `2026-10-02_photo_suite_rev10_run.md` and all ten retained
files were checked against their bytes/SHA256: exact HEAD `fbfb7db`, empty photo
status before the run, 20:56:07–21:29:54 UTC on 2 October. Main suite exit 0:
255 tests in 2,024.525 seconds, OK with five WordNet skips; the separate build
environment supplied those five checks, 0.663 seconds, OK, exit 0. These are 250
non-skipped main tests plus the five separately run checks, not 260 distinct tests.
Controller has 34 collected tests; its new method has two subtests. This is verified
retained implementer evidence, not a Codex execution or proof of all environments.

The prior pre-commit disclosure remains **one identified STOPPED observation and
one unidentified failure**, cause unresolved. Their nonrecurrence in the retained
run does not establish causal resolution. No false promotion or new launch blocker
is demonstrated by that disclosure; no blanket rerun is requested.

## Question 3 — separate attestation and authority

This record contains one favourable Stage A attestation. The reader has its own
record and block. The strict go guard still requires the immutable review commit,
path and record hash, its ancestry and dates, the exact attested/re-derived/current
five-field package, and the owner's separately dated words. No GO file or owner
approval is created here. Stage A's measured report, inspected figures and
interpretation, follow-on review and owner row-21 go remain separate from this
pre-run mechanism verdict. Row 19 and earlier bank/text judgments are unchanged.

<!-- STAGE-ATTESTATION v1
{
  "row": "20",
  "stage": "A",
  "verdict": "favourable",
  "reviewer": "Codex (GPT: R052 Entropy paper; native 01a0d19e-2127-7051-9a61-6db771088559)",
  "date": "2026-10-02",
  "reviewed_commit": "fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030",
  "package": {
    "criteria_sha256": "f05be7a80274226bfb90101fc676170ef610c336ca5fe8d1c87d9321bca1c3f7",
    "identity_sha256": "04678ddb2360238bc02c7bca850c2c2f1e4d8247e65bd5717b05461baadad158",
    "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc",
    "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "budget_sha256": "9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"
  }
}
-->

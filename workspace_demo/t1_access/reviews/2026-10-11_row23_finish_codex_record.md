# Row 23 finishing supplement — Codex record

Date: 2026-10-11 UTC / 2026-10-10 local. Reviewer: `GPT: R052 Entropy paper`,
native `01a0d19e-2127-7051-9a61-6db771088559`, topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Assignment: Unimog `prompts/2026-10-11_codex_r052_row23_finish_supplement.txt`,
commit `80316ee31743629a57a5ff11679af8799333e18e`, SHA256
`e61ef1a317958c8b60f5351def67b2501ed1c05f9267893250a911fc7efba6d3`.
Ownership committed at Unimog `42b9361b`; incoming handoff
`0a973e91-d096-53ed-b493-b0b23e048ff5` accepted before review edits/delegation.

**Both requested readings are YES:** the arm-A refusal treatment follows the prior
rule, and the finishing predicate matches the recorded success criterion.
**The supplied automatic declaration path is NOT FAVOURABLE until the two
acceptance defects below are repaired or explicitly checked in a retained,
attempt-bound acceptance record.** This is a static source review, not a row-23
result review or a declaration that attempt 5 succeeded. No paid rerun is needed
to repair these acceptance checks.

## 1. Arm-A refusal rule — acceptable interpretation, incomplete certificate check

RSC `a44f5aa90a5d0b45f86754a8e2bb61bec32d436c`, committed 10 October
20:08:19 UTC, already records arm-A job-start refusal as that arm's outcome,
skips its stage-2 workers and retains its three row-6 processes. Arm-B refusal
remains fatal (`bench_userdata.sh:76–113,137–149`). The new comparator
`05f6df6` correctly distinguishes that outcome from 36 missing A refit records:

- `arm_a_refusal` requires a `HELD:` line containing `computes identity` and
  `manifest declares`; a present untyped refusal invalidates the report
  (`bench_compare.py:120–131`). This is a text-shape check, not an independent
  recomputation or authentication of the refusal identities.
- The refusal branch reports `refused_at_job_start` and its reason, refuses
  record files at the producer's canonical `root_A/records/*/*` layout and skips
  A stage-2 validation (`134–146`). It claims no A parity success.
- The expected process names are six row-6 processes plus 36 B workers: **42**,
  with no `w_A_*`. Without refusal, the unchanged two-arm count is **78**.
  All expected outcomes must be integer zero, with an empty typed survivor
  list. Both arm attestations and row-6 panels, B manifest/task/identity/binding/
  payload/timing checks, pinned plan and transfer verification remain required
  (`210–306`). Arm-B stage-2 logic is unchanged by the refusal patch.

**F-1. Require complete process and refusal evidence before accepting this outcome.** At
`bench_compare.py:269–274`, failure to read `env/declared.txt` becomes `None`;
the equality test is then skipped. A 42-name zero-outcome report can therefore
be valid without the producing process declaration that `a44f5aa` expressly
publishes for its certificate. The `outcomes.json` numeric `declared` field is
also not checked. For an attempt using that producer rule, require a readable,
duplicate-free declaration exactly equal to the expected 42 or 78 names, and
require its typed count to agree with the outcome names/count. Absence or
inconsistency must invalidate acceptance. This is a certificate-completeness
repair, not a change to the arm-A refusal decision or the arm-B success target.
The refusal branch also continues before checking A's reviewed manifest pin
(`139–146`). Check that pin and bind the accepted refusal line to the retained
job-start evidence before calling it a verified identity refusal. This requires
no new dataset generation, fits or expansion of the scientific target.

## 2. Recorded criterion — same predicate, with comparator validity doing work

The owning R052 log records the owner's conditional go at approximately
10 October 20:40 UTC, committed at **21:16:38 UTC** in Unimog
`7c6626e61c531fd3e4b52d92e48e1dee6eee4701`. It requires B_full, all 36 B
refit payloads float-bit identical to Lengau with equal identities, exact row-6
panel and a valid comparator report, including zero outcomes and verified
transfer. The prior arm-A refusal rule was already in place.

`bench_finish.py:28–46` implements that criterion:

| Recorded requirement | Finishing predicate and supporting comparator check |
|---|---|
| Valid report | `valid is True`; comparator validates identities, bindings, expected zero outcomes, survivor list and transfer |
| B_full | Exact `profile_B == "B_full"`; comparator checks effective dispatch/BLAS/XLA/thread settings |
| Exact B row-6 panel | `12/12`, identical decisions and failed flags |
| All 36 B refits | 36 validated records, 36 valid timing pairs, 36 canonical float payload matches, zero nonfinite disagreements |
| A outcome recorded | Typed job-start refusal through the comparator, or 36 A validated records; report validity also requires full A timing/attribution when A runs |

The explicit timing and nonfinite checks expand what already followed from
the valid, exact-payload requirement; they do not lower the predeclared bar.
Failed-fit agreement stays separate from usable numerical evidence. Exact
agreement does not by itself establish scientific interval coverage, native-A
portability, production packing or restart qualification. Use **“before completed
row-23 parity/refit results”**, rather than the source header's “before any
result”: arm-A identity/refusal observations already existed. The recorded
event time and later commit time are distinct.

**F-2. Require a fresh successful comparison before `--declare`.** At
`bench_finish.py:66–72`, the remote command ends in `; echo rc=$?`, while the
captured SSH result is not checked. No prior `report_attempt_<n>.json` is
removed. After an earlier successful comparison, a repeated invocation whose
new comparator fails before writing a report can still copy and accept the old
valid report; its hash then becomes the declaration at `82–87`. A printed
nonzero comparator status does not prevent that write. Local `s3 sync` into a
reused fetched directory also retains files absent from the source; the remote
`.new` replacement copies that retained local tree. AWS documents that removal
of destination-only files requires the sync deletion option.
[AWS CLI S3 sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html).

Use a fresh staging directory, require transfer and SSH/comparator success,
remove or uniquely name the report before comparison, and bind the accepted
report to the requested run/attempt, exact comparator/tree pins and fetched
bundle. Publish the declaration only from that newly validated evidence. A
failed comparison must refuse declaration even if an old valid report exists.
This is a supported static failure path, not a claim that attempt 5 or any
retained report actually followed it.

## 3. Scope, pins and next action

| File below `workspace_demo/t1_access/` | Reviewed commit | SHA256 |
|---|---|---|
| `aws_ec2/bench_compare.py` | `05f6df6a721a1b9038c01d41dbe4942e121fb0ee` | `1e3680e57c0242a852801e1f2f0ae83266df9cbcb7c9c906fa94e827387abfb9` |
| `aws_ec2/bench_finish.py` | `7bb9939c3d64f3a37f0c325423c9202e91de8ed0` | `43d1bc4f27160dd8e2391e0754ba1937b4a208e48b52d57b97b30ccd5920b977` |
| `aws_ec2/bench_userdata.sh` | `a44f5aa90a5d0b45f86754a8e2bb61bec32d436c` | `d31525772eaecbf03c7de0988c0e4b2745a4aa415df9ab5147803823956449ca` |

The two submitted Python files match their committed bytes; independent SHA256
and AST checks passed. Three bounded read-only peers checked the refusal,
criterion provenance and fresh-report failure path. Source reports 11/11
criterion tests and 10/10 sync tests; neither was rerun here. The criterion
tests exercise the predicate, not the transport/report publication path.
`ec2_sync.py` at `853ece0` is context only and receives no new adoption opinion.

The [EC2 v10r2 review](2026-10-11_ec2_v10r2_package_codex_record.md), RSC
`299f4b7`, stays closed: controls v11 `6342aa10` favourable **partition-null
only**; Q1/Q2 authority/ingestion and complete qualification/S/release remain
held for its four R2 groups. This supplement does not grant a production
release or replace actual qualification/result review. The owner has accepted
USD 45 for one Q1 plus one Q2 and direct production after successful
qualification with favourable actual-result review/certificate, without another
owner go, inside the USD 2,300 production / USD 3,000 further-spend caps.
Retries remain an owner decision. Existing source jobs and independent Lengau
gates continue unchanged.

Claude owns source repairs, complete acceptance evidence, current docs,
R052 frontmatter/generated indexes, ledger/tracker, adoption and dispatch. Route
F-1/F-2 and current summary alignment in the sole completion brief. Root owns
only this review, its R052 appends and lifecycle. No source edits/imports/
execution/runtime tests, AWS/account/SSH/Lengau actions, fits/simulations,
scientific/private/current-run result reads, worktrees or pushes were performed.
Forbidden evidence paths, foreign files, frozen science and prior exposure
disclosures remain preserved; full-bank R2 is not later blind calibration.

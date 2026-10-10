# v9 revision 2 transport and row 23 revision 4 — Codex record

Date: 2026-10-10. Reviewer: `GPT: R052 Entropy paper`, native session
`01a0d19e-2127-7051-9a61-6db771088559`, topic `95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Assignment: Unimog `prompts/2026-10-10_codex_r052_v9r2_and_row23_rev4.txt`,
commit `9dfd415366c9213f36c9a6eafcff90ef418bf57c`, SHA256
`f3f0dfae30f057914ca51851e07c60d3f235bb575ec887d97a85041bbcb3df97`.
Ownership was committed at Unimog `41794918`; incoming handoff
`4764ccea-3384-5065-92eb-c3ce9629fa80` was accepted before review edits.

These are bounded repair reviews of RSC `44dc6c4` against the completed
[previous review](2026-10-10_v9_pull_and_row23_rev3_codex_record.md), RSC `137b261`.
The earlier science, operating ruling, approvals, exposure disclosures and closed findings stand.

## 1. Priority: v9 transport and exact controls — FAVOURABLE

The repaired screen transport, bank transport and actual candidate controls are favourable
at these exact bytes. The previous V9-1/2/3 blockers are closed.

```text
ADOPT row19-screen-controls sha256=45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07 version=9
```

This line names the candidate **controls file**, not the status script. It supports the
specified byte-for-byte promotion and coherent adoption record. Before further gated refit
admissions, preserve the version-8 authority/evidence, promote the reviewed bytes, commit
the adoption record bound to this review, deploy to `rsc_screen_ctl`, obtain a fresh
generation-9 whole-role observation and qualification using retained actual job-1 pilot
evidence, and obtain the corresponding actual digest-bound refit-pilot adoption. This review
does not invent that future qualification or its ADOPT line. No new paid pilot fits are needed.

The bank transport at SHA256
`a8585effa87d5a068d416f9331f09add8a7b9c46de0de7afbc719a32b304e33e`
is favourable within the existing independent raw-bank scope and concurrency cap of 17.
It supplies no new bank scientific or screen-pilot authority; no new bank ADOPT syntax is required.

### Why the transport repairs are sufficient

- Both `pull_tree` implementations send SSH stderr to a local `TemporaryFile`, removing
  the listing-size pipe deadlock. The extractor communicates while SSH writes its listing
  to the file; SSH is then waited on using the same transfer deadline.
- The remote script has explicit failure exits for `cd`, `mktemp`, `find` and `sort`.
  Enumeration completes before `LISTING-END <count>`; the tar phase emits `TAR-RC <rc>`.
  Acceptance requires a successful local extractor, no PHASE failure, exactly one of each
  closing marker, count agreement, a tar result of 0 or 1, and matching SSH exit status.
  A whole-SSH exit 1 alone is no longer treated as evidence of a live tar change.
- Every listed non-temporary file must exist locally. Only suffixes `.tmp` and `.tmp.<digits>`
  are exempt, matching the ledger and shard/original publishers.
- Exceptions terminate and wait for both direct subprocesses, with bounded escalation.
  Existing stage/live snapshot rotation, verifier, scheduler, partition, receipt,
  reconciliation, missing-file and binding guards remain unchanged.
- There is now an actual candidate controls file. Versions 1–8 and all other top-level
  metadata, including deployment, match the adopted version-8 file. Version 9 is the only
  appended entry; all six latest controller pins match the reviewed files.

The transport deadline is shared; cleanup can add bounded waits afterwards. Do not describe
the complete failure path as a strict 900-second wall limit. The returned GNU tar-exit-1 note
is not retained by `fresh_snapshot` on success; no claim that it appears in receipts is made.
The timeout fixture checks the stub's name with `pgrep`; it does not prove that every remote
descendant vanished. Static inspection establishes cleanup of the two direct `Popen` children.
These limits do not reopen the closed transport blockers or waive downstream validation.

## 2. Row 23 revision 4 — FAVOURABLE for the bounded benchmark

Revision 4 is favourable for the owner's existing evidence-only EC2 benchmark. The
previous AWS3-1/2/3 launch blockers are closed. Keep the USD 28 cumulative benchmark
ceiling, the owner's USD 3,000 further-spend limit, the same cumulative attempt ledger,
the awake supervisor and heartbeat/error intervention, and the existing no-pooling scope.
This is neither a production qualification nor numerical parity evidence. It imposes no
new permission request or expiry and does not stop independently gated Lengau work.

### Admission, ambiguity, supervision and accounting

`bench_launch.resolve` releases a rejected attempt at zero charge only when a definitive
error answers the fresh first dispatch with no earlier unanswered issue. RunInstances uses
`AWS_MAX_ATTEMPTS=1` and standard retry mode, removing hidden CLI replays from that dispatch.
AWS documents that the configured attempt count includes the initial call.
[AWS CLI environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).
Later rejections and recovery of a crash-left intent remain ambiguous and funded, blocking
new attempts. This preserves the uncertainty of an earlier accepted request with a lost answer.

The saved user-data hash is checked against the actual `file://` bytes before every issue.
Missing or changed bytes refuse replay without releasing funding. Supervisor start errors
are caught and enter bounded emergency termination; the launched attempt remains funded
pending attributable reconciliation. A first heartbeat is accurately labelled startup proof.

The reaper now stamps compute and ancillary endpoints **after** their respective successful
responses. It retains empty-Describe uncertainty, caught API errors and retries, separate
compute/volume accounting, and locked ledger reconciliation. The 900-second grace and
1,800-second reserve are included in both admission and unresolved-attempt funding:

```text
((77,400 + 900 + 1,800) / 3,600) × (1.20 + 0.0094) + 0.10 = USD 27.00915
headroom below USD 28 = USD 0.99085
```

New-attempt lifetime is shortened by both allowances and refused below 72,300 seconds.
This closes the prior retry-at-the-cap arithmetic issue. It is the declared conservative
model, not an actual bill or a guarantee through arbitrary host/service outages. Continuing
supervision and intervention remain operating conditions; the finite reserve does not replace them.

### Bounded process cleanup and report handling

`bench_userdata.sh` enables job control so each declared job has a process group, freezes
the censor list before cleanup, tests group-member liveness, sends TERM then KILL under one
120-second endpoint, records unresolved groups, and proceeds to checked certificate creation
and bounded final upload. The unbounded `wait` and broad process-name termination are gone.
The hard-stop timers, atomic exit publication and checked transfer disposition remain.

The comparator now requires positive finite timing walls, typed effective A/B profiles,
the four exact thread caps of 1, known OpenBLAS cores, the B AVX2/Haswell settings and empty
active NumPy AVX-512 list for B_full. Occupancy timestamps/load values must be finite and
nonnegative. Row-6 replicate strings are canonical and malformed generator/grid input becomes
an explicit invalid result. Existing scientific pins, full bindings, canonical payloads,
per-predictor usability, non-finite disagreement reporting and 78 exact zero-exit names stand.

Two refinements belong to **report acceptance**, not paid collection, and need no paid rerun:

1. Require a correctly typed, empty `unresolved_after_kill` list before accepting a clean
   completion report. User-data records it, but `bench_compare.py` currently ignores it.
   A job can publish exit 0 while a surviving child is recorded separately; the current
   zero-exit check alone does not certify empty process groups.
2. `validated` increments before the positive-wall guard. Invalid walls correctly invalidate
   the report and never enter timing ratios, but the record count can still be 36.
   Distinguish record validation from valid timing pairs in the report and its interpretation.

Align current revision labels in the README's final sentence and source headers with the
reviewed revision; some still name revision 2 or 3. The user-data timing comment now correctly
names the 900-second reaper grace. These wording fixes do not require collection changes.

## 3. Exact package and evidence limits

| Reviewed file | SHA256 |
|---|---|
| `chpc/candidate_v9/row19_screen_status.py` | `f624fb633e52dd941515e15bc4ce048e72e5077914e675ddac108ef6414bfb4e` |
| `chpc/candidate_v9/row22_bank_status.py` | `a8585effa87d5a068d416f9331f09add8a7b9c46de0de7afbc719a32b304e33e` |
| `chpc/candidate_v9/row19_screen_controls.json` | `45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07` |
| `aws_ec2/bench_launch.py` | `d5e85401799446cc7c9c8acb4973e78f9f40fb9a982768018dc70530fe992fbc` |
| `aws_ec2/bench_reaper.py` | `574adbac1218badcaaaabb303a8044e93caf018a9842464f494266d261668db6` |
| `aws_ec2/bench_userdata.sh` | `b86f0b6c5f86e7d726d3c5a2a88547f01e9785cea71bde3829f8e1dc2abee726` |
| `aws_ec2/bench_compare.py` | `b93c7d6680444880f2faa5354b59e76a73a9c4304e6ead57e48355d12ed6a298` |
| `aws_ec2/attest.py` | `3e9b2c08c7a8db323ead60b55fab13e34bc0c9c2fa953aefd8ce5c9a75491765` |

Independent local static checks passed: all 13 package files, nine candidate files and four
AWS fixture files match committed `44dc6c4`; Python AST, JSON and shell syntax; identical
pull-function ASTs; preserved controls history and six latest pins; exact 36-slot/index-0
plan, checksum sidecar, and the six permitted manifest difference paths. Production manifest
`43b75f94`, benchmark manifests `824837ee`/`08e498c4`, source, environment and scientific
metadata are unchanged. Supplied Python diff substantive changes match the actual files;
hunk context/blank-line placement differs, and the controls file gains a final newline.
Three read-only peer reviews independently covered transport/lineage, launch/reaper and
user-data/report acceptance. The root retains the integrated judgment.

Source-reported evidence was read, not rerun: the 60,000-file listing test, failure/timeout
fixtures, live pulls, 13 launcher assertions, reaper fixture, cleanup fixture and copied-Lengau
component smoke. The cleanup fixture shortens its endpoint to 12 seconds while retaining
`CLEAN_END-30`, so it bypasses production TERM grace. Its PASS supports group killing,
censoring and atomic publication; it does not exercise the production grace, unresolved
branch, whole outcomes certificate or upload. Real AWS, full instance execution and Zen-4
B dispatch remain unexercised. Copied Lengau records are component evidence, not fresh EC2
provenance or parity. Prior row-6 and full-bank exposure disclosures remain applicable.

Only this new review and Codex-owned R052 log/lifecycle/prompts are owned here. Claude retains
source, controls promotion/adoption, ledger, current documentation/frontmatter, generated
indexes/tracker, IAM/accounts and dispatch. Current copies and report refinements are routed
in the sole completion brief. No source edits, source/science imports or execution, fixture
runs, fits, simulations, scientific/private-output inspection, SSH/Lengau/AWS/account
operations, worktrees or pushes were performed by this review. Existing jobs, foreign files,
caps, HEAL hold, shard STOP192 and prior completed reports remain preserved.

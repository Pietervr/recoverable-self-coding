# v14 status REVISION 13: settled-memory repair

Codex narrow re-review, local 11 October / UTC 12 October 2026.
Exact `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`.
Incoming `2b29e6b7-7edd-5722-b143-b0dd5e7d0c30`, Unimog
`69d28740673f8cad9361e84ed46d194c912bdbeb`,
`prompts/2026-10-12_codex_r052_v14_status_r13.txt`, SHA256
`e80836c816fa9b9111ba4dae24ce01250f505c46bf24c8389d6d3f761d67a7bb`.
Whole brief read; ownership committed at Unimog
`fc3a61ced8dd5cbaf0f2cdbec11e05552168b530`, then ACK
`1791775500.6180322`, before review edits/delegation.

## Verdict and exact authority

**FAVOURABLE to adopt exact v14/REVISION13 controls below.** The narrow repair
resolves the two memory-evidence issues in RSC `7523370` (a): a newly observed
breach/max no longer regresses to an older lower clean value after PBS expiry,
and an eligible direct observation first made after settlement can be retained
for later consumption. No blocking implementation regression found.

```text
ADOPT row19-screen-controls sha256=95d9bdfe4e4883b3e04d458a606c34d8504584b65e41344185beb8980df65630 version=14
```

Reviewed exact candidate commit
`70cbfd50dae8d38fddf282db33b772ec70b0270b`, status SHA256
`05d952bd67b73a71c3ddea2919b38e5abb1696af03f77a78a1d55f7be80a680b`.
This literal is for the status/controller-authority update. It is not a pilot
ADOPT, qualification permission/result certificate, refill or production release.
R12's `66ba965e…` assessment remains a dated assessment of different bytes.

## Memory evidence and publication

`candidate_v14/row19_screen_status.py:283–313` reads every matching receipt with
the expected schema/role and `fresh=True`, `production=True`, a job at F with
the same PBS ID and exit. Alarmed receipts are eligible. It independently
retains the largest finite nonnegative **direct** memory value and the newest
receipt carrying that job's specific scheduler-memory alarm. Unrelated alarms
and other jobs/exits are not carried.

Direct provenance is explicit: a qstat-observed summary supplies `mem_kb`;
a `ledger-settlement` summary supplies only `qstat_mem_kb`, never its possibly
carried aggregate `mem_kb`. `pbs_observe:368–379` compares that historical maximum
with current tolerant-qstat memory and writes its own live observation separately
to `qstat_mem_kb`/`qstat_walltime_req_s`. The chosen historical value names its
receipt file and SHA256. `reconcile:674–702` publishes these fields and applies
the retained-breach alarm independently of the current numeric threshold.

Consequently, the reviewed sequence—older clean direct 24%, new live 95%,
publication, PBS expiry—continues to check 95% from the alarmed direct settlement
receipt and retains the breach. An alarm-only breach still holds when the only
available numeric value is an older 24%. A clean first observation made after
settlement also remains usable through its published direct field after expiry.

Original direct-observation and breach receipts must remain in the scanned
local receipt history, with their bytes/provenance retained for actual-source
review. Later carried-only summaries do not replace original direct evidence.
Without an eligible direct value, the finite-memory alarm stays. The repair has
no refit clean-check-without-value fallback. The committed scheduler extract is
not a controller input and cannot manufacture this carry when PBS has expired.
Actual receipt acquisition/retention remains an operating obligation, not an
observed result of this static review.

## Focused checks and limits

Test source `chpc/test_pbs_settled_r13.py`, SHA256
`b48720085f5e70fd3b99b742f69162ec1ae15f09756a08a0bdf85e597f5b2ea3`,
is committed and matches the working file. It meaningfully checks the relevant
controller boundary:

- `:221–251`: actual reconciliation summary/alarms, publication of live 95%,
  expiry beside an older clean 24%, retained direct 95%/breach, and another
  publication/reobservation;
- `:252–258`: alarm-only breach cannot be suppressed by the lower clean value;
- `:259–278`: direct first-after-settlement carry, a carried-only receipt not
  becoming its source, and loss of the original direct source causing HOLD;
- `:280–294`: different exit, unrelated alarms and non-fresh receipt handling;
  inherited cases also check failed/non-F tolerant queries, mixed expired/known
  IDs and rejection of an Unknown-ID error for an unasked ID.

The receipt envelope is synthesized and EC2 reconciliation stubbed; these are
not full production-watch/qualification tests. Some malformed/foreign historical
receipt cases and a further alarm-only publication cycle lack explicit fixtures;
the implementation visibly applies the corresponding selectors. These are
coverage limits, not demonstrated blockers. Some inherited “newest clean” test
comments describe the older policy rather than R13's maximum-direct-value policy.

Operator-reported 51/51, the negative run against R12 and unchanged 31/31 were
**not run here**. Root and three bounded peers read static source/diff/contracts/
tests; source identity and AST/JSON metadata were checked without importing or
executing project code. No live watch, actual memory, deployed candidate or
qualification/result output is certified here.

## Unchanged authority and operating cutover

All 14 candidate pins match committed files. Only status differs from adopted
v13 `840840f5…`; the other 13 pins, existing version history, top-level policy,
programme/sub-envelope/S and partition `8d1de408…` are unchanged. The v14 controls
entry changes only its status pin and review note against R12. Qualification and
admission consumers are unchanged (`status:866–903`, `admit:1271–1320`). Existing
valid epoch-1 activation can stand: `row19_partition.py:295–325` accepts the
retained historical entry with the same partition through the current version.

Before operating on v14, repoint the promotion/deployment commands and owning
runbook to version 14, these exact controls/status bytes and this committed
record. Preserve the **actually adopted v13** controls/adoption/status and
existing gate/watch/verifier history before replacing fixed-name files.
`migration_v13/RUNBOOK.md` still describes the older v9→v13 operation and
`promote_v13.py` hardcodes v13; it is not a v14 promoter. Do not repeat the
completed v9 archive/epoch activation or the benchmark finish.

Promote/deploy the reviewed status and controller-authority change while
preserving scientific bytes, identities, ledger and epoch-1 partition. Then
obtain fresh whole-role evidence and follow the **one existing-pilot metadata
qualification, new hash, actual-source review and matching max100 adoption**
required by step 8. No repeat pilot fit is needed. Existing carried-pilot
acceptance in `5bab1a9` (c) and R12 (b) retains its conditions; an original direct
receipt need not have been produced by v14. Any failed-job, receipt, verifier,
inventory or disposition alarm still holds the next gate. In particular, this
review does not dispose of refit13's reported failure/unfinished coordinate.

## Nonblocking description precision

1. The brief/header's “walltime comes from the same direct source” has an
   exception: `pbs_observe:375` uses another available direct walltime request
   for the **same PBS ID** if the maximum-memory source lacks one. The selected
   request is still compared with the plan (`:687–688`). No reservation bypass
   was established. Describe that exception in operating/review summaries;
   this wording point does not require altering the reviewed candidate hash.
2. The committed scheduler-facts extract, SHA256
   `e3727c177f7eb3009dc75688de80771efb6e16685f9ee840424bfc8da8214379`,
   records memory 48,345,148 / 43,053,568 / 46,381,180 / 46,155,404 kB and exits
   0/0/0/4. With the controller's `120 × 1024²` kB denominator these are
   **38.42%, 34.22%, 36.86%, 36.68%**, rather than the brief's “all 38–40%”.
   All are below 90%. The extract and raw hash are operator-provided archive
   metadata; private raw qstat was not opened or independently authenticated,
   and no controller consumes the extract. No actual-result authority follows.

## Ownership and retained limits

Author owns implementation/current docs/frontmatter/generated INDEX, operating
patch/adoption/deployment/dispatch/jobs. Root owns this review, own R052 appends,
the sole findings brief and lifecycle. No project execution/import/runtime tests,
raw/private/scientific/current candidate outputs, SSH/AWS, source edits,
adoption/deployment/activation/qualification/refill, fits/simulations, job
intervention, worktrees or push. The SI revision `3916eb79`/final `e633edc3` and
accepted `2e3f1b29` stay complete/closed; no duplicate review/report/re-ACK.

Standing owner USD45 one Q1+Q2, direct production after favourable actual-result
review without a new owner go, production USD2300/3000, retries-owner,
programme100000, refit+S60000/max100, S2304, bank17, HEAL hold, STOP192, bounded
k40 and all qualification/migration/adoption/release/exposure gates remain.
This source repair creates no new scientific run, spending or pilot authority.

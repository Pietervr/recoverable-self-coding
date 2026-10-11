# Bank memory re-review 2: same-job breach preservation is favourable

Codex second opinion, local 10 October / UTC 11 October 2026. Exact session
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Brief: Unimog `d23d0805efdb160795174d6a3a9655c7c2522344`,
`prompts/2026-10-11_codex_r052_bank_memory_rereview2.txt`, SHA256
`39f8945dc77b2074cf5e5fc09a56ace503cf422a121802c89b7e8723190dfd29`.
Ownership committed at Unimog `1a812235`; incoming `dfddc7a9` accepted
`1791695087.35153` before review edits or delegation.

Reviewed RSC `8e4fcfa48ecfdcf70e82ec29987570b5085fbd0f`, narrowly against
`6f898af1bef2486517c9a05f5a1f058f94bd72d7` for `c38779c` answer (a′):
`chpc/row22_bank_status.py`, SHA256
`920689871c0757b8de9c555a6efcd42773894dfafc6b37ad07a67ea87e0be695`,
and `chpc/test_pbs_settled.py`, SHA256
`bae7e57b28c38c2c0d8ab921a8f3a561c38d96b6de3025b61dbf67764255e444`.

The selector now reads matching terminal-job receipts even when they are alarmed.
It checks the largest recorded memory value together with any current qstat value
and carries a job-specific scheduler-memory alarm separately. An older clean
receipt can no longer displace the affirmative breach in the prior counterexample.

## Answer (a″)

**FAVOURABLE for fresh bank receipts and refills using these exact source bytes,
under the existing bank gates.** The remaining bank-memory selector hold in
`c38779c` is resolved. No further repair, repeated fit, new qualification or new
mandatory finite-memory rule is required by this narrow review.

This is a source review, not certification of a particular fresh receipt or live
job. The ordinary fresh production receipt, bound identities, zero current alarms,
existing qualification and adopted review, max17, STOP, seed and programme-budget
gates remain. Claude owns deployment, receipt generation, provenance verification
and dispatch within the standing owner authorization.

Policy (iii) remains acceptable as the limited historical attestation already
stated in `c38779c`: a genuine matching clean direct-qstat terminal receipt produced
no alarm under the old conditional check. It supplies neither measured `mem_kb`
nor proof of memory at or below 90%. Known same-job breach evidence takes priority.
Preserve and check the actual historical receipt and its generating-source,
campaign/job and scheduler provenance before relying on it; this uses existing
evidence and does not require another scientific run.

## Why the counterexample is closed

`prior_bank_memory:237–262` considers all readable bank-watch receipts with the
required schema, fresh/production flags and an alarms list. It matches the same
PBS ID, state F and exit, excluding boolean exits. For each matching summary it:

- Retains the largest finite non-negative numeric value, including values from
  alarmed receipts (`:256–257`), with filename and SHA256 provenance.
- Separately retains the newest receipt carrying a scheduler-memory alarm for
  that summary's job key (`:258–259`). The search continues after finding it.
- Separately retains a clean direct-qstat historical attestation (`:260–261`).
  An unrelated alarm cannot supply that clean attestation or latch a breach.

`pbs_observe:276–285` always consults this history, even when PBS still reports
memory. It uses `max(current qstat, largest retained value)` when either value
exists. With no value it prefers breach evidence over clean attestation; in every
case it attaches `memory_breach` independently.

`reconcile:336–343` alarms on that breach independently of the numeric threshold.
The existing >90% alarm checks the selected maximum; absent evidence still alarms
for a settlement-derived observation. Thus newer 95% plus its memory alarm, older
clean 24% or legacy evidence, and expired PBS history produces the retained 95%
value and both memory alarms. An alarm-only breach still produces a breach alarm.
Fresh publication includes reconciliation's alarms (`:448–473`), and the unchanged
submitter's fresh-receipt gate rejects them (`row22_bank_submit.py:173–191`).

The repair does not propagate unrelated historical alarms wholesale. A valid
matching numeric fact can remain usable when its receipt has an unrelated alarm;
current reconciliation still evaluates the other current evidence. The retained
receipt files remain the source of historical breach/value provenance.

## Validation and limits

Read the complete bank module, two-file repair diff and complete test source.
Three independent bounded source peers checked selector, legacy/refill boundaries
and test coverage. Static AST and committed-blob comparisons confirm exact file
identities; no project code was imported or executed.

The seven added checks (`test_pbs_settled.py:135–162`) exercise the prior
counterexample through observation and reconciliation for both older alternatives,
both alarm-only variants, and an unrelated alarm. The source contains 31 checks;
**31/31 is operator-reported and was not rerun here.** There is no explicit test
with competing current-qstat and retained numeric values; the `max` branch is
directly visible in the source. No publication/refill integration was executed.
These limits do not demonstrate another blocker in this repair.

The brief's actual receipt hash, zero historical-memory-alarm count, 24/24 worker
outcomes and live preview remain source assertions. No actual receipt, current-run
or private output bytes were inspected. Receipt hashes identify retained bytes;
they do not independently authenticate the scheduler or generating source.

Non-blocking source cleanup: header `row22_bank_status.py:20–27` still describes
the former first-success/clean-only ordering before the replacement at `:28–32`.
Test comment `:111` still says alarmed receipts are never a source. Align these
comments with the implemented maximum-value and separate-breach rule.

Blob comparisons confirm unchanged submitter, programme gate, amended v13 controls
`840840f5…` and refit status `eeacc7e3…`. Prior `5bab1a9` answers (b)/(c) stand:
existing-pilot refit metadata qualification with a NEW hash, matching refit/max100
review and adoption after actual historical-source verification/archive; no repeat
fit. This bank repair supplies no new bank/refit ADOPT literal or result certificate.

Standing owner go, USD45 one Q1 plus one Q2 and direct production after favourable
actual qualification without another go remain. USD2,300/3,000 caps, retries-owner,
S2,304/programme100,000/refit60,000/max100, bank max17, HEAL hold/STOP192, k40 funding
scope, migration and actual-result/release gates and prior exposure limits carry.
All earlier completion reports remain accepted and closed.

Root owns only this record, own R052 appends, the sole completion brief and
lifecycle. Claude owns implementation, current docs/frontmatter/generated INDEX,
source jobs, deployment, adoption and dispatch. No project execution/imports/tests,
actual/private outputs, SSH/Lengau/AWS, fits/simulations, source edits, job
intervention, worktrees or push occurred. Foreign files and existing jobs remain.

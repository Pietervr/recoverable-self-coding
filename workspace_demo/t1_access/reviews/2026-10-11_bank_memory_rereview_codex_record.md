# Bank settled-memory follow-up: newer memory alarms can still be skipped

Codex second opinion, local 10 October / UTC 11 October 2026. Exact session
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Brief: Unimog `aab82baabe1eaa040cedb0c5453b8e0bc2750e51`,
`prompts/2026-10-11_codex_r052_bank_memory_rereview.txt`, SHA256
`f5d137879cb7c040f3baeca0a78cba3e3d922d26c7b2ce771a223a3656e169c1`.
Ownership committed at Unimog `5c0da24f`; incoming `d7581439` accepted
`1791694036.420685` before review edits or delegation.

Reviewed RSC `6f898af1bef2486517c9a05f5a1f058f94bd72d7`, narrowly against
`43a58d1157a4f97dfc227c0e236fd982500d47a1` and `5bab1a9` answer (a):
`chpc/row22_bank_status.py`, SHA256
`ef1d4ad81f728aa5a8f173ec115691118481838a8e63fb3c55f63538b2d6a9f6`,
and `chpc/test_pbs_settled.py`, SHA256
`b4285d547b9907f28560384fd09dcb142e8cbc41f84f9048d8a85b9ef2ef561b`.

The new chain checks terminal scheduler memory while PBS retains it, then uses a
retained numeric value or a documented clean legacy check. It alarms when none
exists. This repairs the direct 95% case and the earlier note-only omission.
However, its search for a clean historical receipt can discard a newer memory
alarm for the same finished job.

## Answer (a′)

**NOT FAVOURABLE to unrestricted fresh bank receipts and refills under these
exact bytes yet.** Preserve affirmative same-job memory-breach evidence before
accepting an older clean fallback. This is one narrow remaining defect, not a
request for another fit, new qualification or mandatory finite bank memory.

**Policy (iii) is acceptable as an explicitly limited historical attestation**
for expired pilot `7523732`: a genuine matching direct-qstat terminal receipt
produced no alarm under the old conditional memory check. It supplies no measured
`mem_kb` and does not prove aggregate memory was below 90%. It cannot override
retained affirmative breach evidence. The policy itself need not be removed to
fix the selector.

The named `bank_watch_20261010T203256Z.json`, its bytes/hash, claimed pilot/worker
outcomes and the live preview were not inspected here. Source must preserve and
check that actual receipt's schema, fresh/production flags, zero alarms,
same PBS ID/F/exit, campaign/job binding and generating-source provenance before
using the policy. This is provenance checking of existing evidence, not another
scientific run. No new numerical memory requirement follows from this review.

## Remaining counterexample

`row22_bank_status.py:234–248` scans filenames newest first, but `:239–240`
skips every receipt whose overall alarms are nonempty **before inspecting its
same-job memory**. Thus the following retained inputs are sufficient:

1. An older fresh production bank receipt is clean and observes the same PBS ID
   at F, exit 0, with 24% memory or no saved value under the legacy format.
2. A newer fresh production receipt observes that same ID at F, exit 0, saves
   `mem_kb=119537664` against a 120 GiB request and contains its >90% memory alarm.
3. PBS history expires. The independent settled-memory query supplies no value.
4. The selector skips the newer alarmed receipt and chooses the older clean one.
   Reconciliation receives nonempty `memory_evidence` and either 24% memory or
   `None`. Neither memory alarm at `:320–325` fires.

The fresh receipt can therefore omit a known memory breach. All other current
worker/record/timing gates can be satisfied independently. The unchanged submitter
checks the newest receipt's alarms (`row22_bank_submit.py:173–191`); it does not
recover the discarded history. This is a source trace, not an executed fixture
or a claim that any actual job has conflicting observations. The selector must
handle retained contradictory evidence explicitly rather than silently choosing
the favourable observation.

The minimal repair is to consult or latch affirmative resource-breach evidence
for the same job before positive fallback. A matching newer numeric memory value
must remain checkable even when its receipt is alarmed for that breach; where an
older format retained only a job-specific memory alarm, preserve that alarm or
resolve it explicitly. Do not blanket-propagate unrelated stale alarms: current
reconciliation can still resolve unrelated worker/record problems. Add a focused
source test with **newer same-job 95% + memory alarm, older clean value/legacy
receipt, expired qstat**. No scientific fits need repeating.

## What the repair already gets right

`settled_memory_qstat:207–229` uses a separate query, retains asked IDs at F and
accepts partial results only when the nonzero return's stderr consists solely of
Unknown Job Id lines for settled IDs. Other transport failures supply no direct
memory; they fall through to independent historical evidence, not a memory pass
from the failed query. Unsettled state observation remains strict (`:277–297`).

`pbs_observe:263–269` supplies the selected memory/provenance to the common
reconciliation. `reconcile:317–325` records it, alarms on absent evidence for
settled jobs and applies the existing >90% threshold to available values.
Current or selected carried 95% values therefore alarm. The gap above occurs
earlier, when known evidence is skipped, not in that threshold.

The legacy selector requires bank schema, fresh/production, zero alarms and the
same PBS ID/F/exit; absent old `observation` defaults to qstat, while an explicit
ledger-derived summary without a value is excluded (`:239–248`). Historical
fresh is the collection mode, not a new age limit on terminal facts. The newly
generated receipt still needs ordinary current freshness and bound identities.
The old parser recognizes `kb` only (`:291–292`), and its conditional check skips
`None`; legacy zero alarms cannot exclude missing or unsupported-unit memory.
Keep that limitation explicit. Receipt hashes identify retained bytes; they do
not independently authenticate scheduler or generating-source provenance.

Bank `--qualify` still refuses a settlement-sourced job (`:459–482`), even if its
memory came from qstat. Existing pilot qualification/hash/adopted-review/max-job,
fresh bound receipt, STOP and seed gates stand (`row22_bank_submit.py:146–265`).
Programme admission remains in the external cooperative wrapper
`programme_gate.py:14–30,148–164`. This review emits no bank ADOPT literal and
performs no admission, settlement, qualification or deployment.

## Validation, continuity and ownership

Read the complete bank module, two-file diff and complete test source. Three
independent bounded source peers checked the chain, legacy policy and tests;
the newer-memory-alarm case was checked across those reviews. AST/blob checks
confirm the above exact identities and unchanged submitter/programme gate.

The nine new assertions (`test_pbs_settled.py:85–132`) cover six observation/carry
cases and three reconciliation cases, including direct 95%, absent evidence and
approximately 24%. The newer alarmed receipt in the carry test has `mem_kb=1`
and unrelated alarm `x`; it does not test preserving an affirmative 95% breach.
“Carried and checked” at `:113–114` checks selection only, while the separate
reconcile fixture injects its value directly. Reported 24/24 was not rerun.
No project imports, source/test execution, actual/private/current-run or fixture
outputs, SSH/Lengau/AWS, fits/simulations, source edits, job intervention,
worktrees or push occurred.

Prior `5bab1a9` answers (b)/(c) remain: favourable amended v13 controls
`840840f5…` / refit status `eeacc7e3…`, and actual-source-checked existing-pilot
metadata requalification with a NEW qualification hash/refit-max100 review and
adoption, without another fit. Both files are byte-unchanged in this package.
The separately prepared migration alignment does not approve this bank selector.
All row23 actual-success, migration/archive/drain/inventory/current-receipt,
qual_permit/Q1/Q2/S/actual-result gates remain. Standing owner go, USD45 one Q1
plus one Q2, USD2,300/3,000 caps, retries-owner, S2,304/programme100,000/refit60,000/
max100, bank's existing max17, HEAL hold/STOP192, k40 funding scope and exposure
limits stand. No new owner confirmation or repeat scientific work is requested.

Claude owns implementation, current docs/frontmatter/generated INDEX, source jobs,
deployment, adoption and dispatch. Root owns only this record, own R052 appends,
the sole completion brief and lifecycle. All earlier completions remain accepted
and closed; do not resend them.

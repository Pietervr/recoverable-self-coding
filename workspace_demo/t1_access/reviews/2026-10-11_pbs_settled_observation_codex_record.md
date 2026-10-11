# PBS history expiry: settlement observations and amended v13 controls

Codex second opinion, local 10 October / UTC 11 October 2026. Exact session
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Brief: Unimog `d12968488f26c691b62ec21976acf3613fa306e2`,
`prompts/2026-10-11_codex_r052_pbs_settled_observation.txt`, SHA256
`011ecd7324087c6b5da543347ca6b5a15b38ca656ceea4c64e7dab51f4460f20`.
Ownership committed at Unimog `dd19dc21`; incoming `69134002` accepted before
review edits or delegation. Reviewed committed RSC
`43a58d1157a4f97dfc227c0e236fd982500d47a1` against its parent.

The repair replaces fresh scheduler queries of settled jobs with historical
settlement evidence. Unsettled jobs still need a successful, complete scheduler
observation. Refit additionally recovers terminal scheduler memory from a retained
direct-qstat receipt. A newly generated receipt can therefore be current while
its terminal resource facts are explicitly historical.

## Answers

**(a) NOT FAVOURABLE to the exact bank repair for unrestricted fresh receipts and
refills yet.** Its expiry handling and completion checks are sound, but it drops
an existing scheduler-memory alarm for every settled job. Resolve the narrow
memory-evidence regression below; this does not require another scientific fit
or a change to the bank's seeds, records or job cap.

**(b) FAVOURABLE to the refit repair and exact amended v13 controls**, for the
direct v9 → v13 migration subject to the existing operating and result gates.

```text
ADOPT row19-screen-controls sha256=840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c version=13
```

This replaces `d933862e…` as the prospective migration identity. The earlier
`64034c5` opinion remains a dated opinion on its exact bytes. This record performs
no adoption or deployment. The bank status file is not a controls pin; answer (b)
does not resolve answer (a) or authorize using an unapproved bank repair.

**(c) Carried terminal memory is acceptable for the existing refit pilot's
metadata requalification**, with the actual retained source verified and archived
in the subsequent new-qualification review. No repeat fit is needed. Cite archived
`3820ac0e…` / `d64600f8` as historical corroboration, not as a substitute for the
new v13 qualification, its new hash, matching refit/max100 review and adoption.
No new pilot ADOPT literal is issued for unseen qualification bytes here.

## Bank regression: settlement removes an existing resource alarm

`chpc/row22_bank_status.py:188–196` returns state, exit, optional walltime and
settlement provenance, but no `mem_kb`. `:261–262` retains the earlier check:
when scheduler memory is present and exceeds 90% of the request, it adds an
alarm. The old observer queried settled IDs too; the new observer never does.

The before/after case follows directly from the source: take a settled bank job
with exit 0, complete valid workers/records/timings and a scheduler observation
whose memory is 95% of its request. Before this repair, that observation produces
the above-90% alarm. After this repair, the same settled job is represented by a
note without memory, so that alarm disappears. A fresh zero-alarm receipt can
then satisfy the refill's receipt gate. This is a static counterexample, not an
executed fixture or a claim about any actual bank job.

The distinction matters: bank receipt **summaries** previously omitted scheduler
memory, but bank **reconciliation** consumed it. “Nothing else changes” is therefore
too broad. This review introduces no mandatory finite-memory requirement for bank
jobs; the pre-existing predicate was conditional on available memory. Worker
maxrss checks remain, but they do not implement that scheduler aggregate check.

Preserve/reconcile the terminal scheduler-memory observation or retain a known
memory alarm so settlement cannot silently clear it. If a historical observation
is unavailable, describe that fact honestly and resolve its evidence policy
explicitly; do not claim a memory pass from an absent field. A focused source
check should cover the above-90% settled case. Do not rerun the bank fits merely
to reconstruct scheduler history.

The other bank paths are credited: `:199–238` queries only unsettled IDs and
requires rc 0 plus every asked ID; malformed settlement exits fail observation.
`:263–316` preserves bad exits, missing runner/worker outcomes, worker memory,
record and timing checks. `:406–409` explicitly refuses a new qualification of a
ledger-observed job. Existing bank qualification/review/max-job, freshness, STOP
and seed gates remain in `chpc/row22_bank_submit.py:146–265`. Aggregate admission
remains in the external cooperative `chpc/programme_gate.py` wrapper
(`:14–30,148–164`). Thus a settlement-based receipt is not settlement-based bank
requalification.

## Refit carry and its evidential scope

`chpc/candidate_v10r4/row19_screen_status.py:258–273` selects the newest matching-role,
matching-schema receipt marked fresh/production/alarm-free that observed the same
PBS ID directly from qstat at F with the same exit and finite non-negative memory.
It excludes explicitly ledger-observed summaries, preventing recursive carry.
It carries memory/requested walltime and records the source basename and SHA256.
“Fresh” here is the source receipt's collection mode, not a new 2,700-second age
limit on an immutable terminal observation. The **new** receipt still needs its
ordinary current freshness and binding checks.

`:276–327,723–725` keeps settled and unsettled observations distinct. Missing
settlement exit, nonzero qstat return and incomplete unsettled coverage fail
observation. `:602–617` still checks request agreement, excessive scheduler memory
and missing finite memory; no usable prior source therefore holds the refit
receipt. Exit 271 remains 271. The complete closed-no-record proof and settlement
certificate for job 3 remain required (`:350–410,595–617` and unchanged admit
`:878–969`); its charge stays, its coordinates are uncompleted and it cannot
qualify (`status:795–796`). This is a source conclusion, not a new job-3 observation.

The source-file/hash annotations identify retained evidence but are not separately
authenticated by unchanged admission: it does not consume `observation`,
`prior_receipt` or `settle_note_sha256`. Its ordinary summary, verifier and latest
generation checks remain. The later actual-pilot metadata review must verify the
selected receipt's bytes/hash, direct-qstat provenance, matching PBS/exit and
original scientific identity, settlement-note provenance, carried memory/request
values and fresh current verifier/watch bindings. Do not require the historical
receipt to use new v13 controller bytes; that would reject legitimate migration.
The brief's claimed 47,179,688 kB was not independently read or verified here.

The exact transient `xf_settle.sh` source was read, not executed. It queries
singleton `J.sched01`, refuses unless state F, and writes exit/walltime/F through
programme-locked settlement. SHA256
`f019d015036e80412c9639efa45961417976e0a7d75267ed98cf8f1f054aad45`;
path `/tmp/claude-501/-Users-pietervanrooyen-Unimog-Projects/fdb5f471-1679-481f-8198-f3f211cc7447/scratchpad/xf_settle.sh`.
This is an operator convention, not a committed scheduler certificate; the shell
does not explicitly test qstat's return code, and the ledger API accepts a
technical note (`chpc/row19_ledger.py:208–223`). Note hashes identify bytes, not
independent scheduler authenticity. Do not substitute an arbitrary hand-written
note for the actual retained settlement evidence.

Malformed matching-prefix cached JSON can stop the refit selector because it
assumes mapping-shaped decoded receipts/jobs. That is an availability limitation,
not a demonstrated path publishing clean evidence; no actual such file was read.

## Identities, migration and preserved gates

Static blob/JSON checks confirm controls
`840840f53543763669a730f0c92d12a7a4484d31dda631576cbaf3f53992f83c` pins refit status
`eeacc7e36a833b653d7410e597189b3a154ec76b84225eaf736b8366cad9c9d9`.
Only the latest review note and status pin changed. All other 14-entry pin-map
members match their committed source; earlier history, programme, sub-envelopes,
S declaration and epoch1 partition `8d1de408…` are unchanged. Bank status SHA256:
`2489da5b288f779de0c400cc454223df23b757cf18256e130e6ffbad33d71d5b`.

Repoint the prepared `5a493cf` migration runbook, preflight/promote/deploy/activate
scripts and review references to these controls and this record before use.
The brief's `5536bb6c…` adopted-v9 status claim is inaccurate: committed canonical
status is `f624fb63…`, with adopted controls `45f840bc…`, matching the earlier
`d64600f8` record. Preserve that actual predecessor and its qualification/review/
watch/verifier bytes before any fixed-name overwrite or gate retirement.

Row23 actual declared success, drain of old loaded controller commands while
scientific workers/reaper continue, exact deployment/S manifest in the job clone,
canonical activation/claim scan, initial inventory/root install and fresh
whole-role evidence remain. Regenerate ONE existing-pilot qualification, obtain
its matching new-hash/refit/max100 review/adoption, then use fresh current receipts.
Correct qual_permit review/drain/fence and actual Q1/Q2/S evidence with favourable
bound result/certificate still gate production. Archive `3820` remains historical.

Owner USD45 for one Q1 plus one Q2 and direct production after successful favourable
actual qualification without further owner go stand. USD2,300/3,000, retries-owner,
S2,304/programme100,000/refit60,000/max100, HEAL hold, STOP192 and bounded k40 funding
scope are unchanged. This record establishes no actual row23 success, qualification,
release, current account/allocation balance or whole-block funding guarantee.

## Validation and ownership

Read the four-file committed diff, complete controls and test source, prepared
runbook and relevant contracts. Three independent bounded source peers examined
bank, refit carry and qualification consequences. AST/blob/JSON arithmetic only;
no project imports, execution or runtime tests. The source-reported 15/15 tests
cover helper selection/observation with synthetic notes/stub transport, not complete
qualification/adoption, bank-memory regression or migration. They were not rerun.

No actual/private/current-run or fixture outputs were read; no SSH/Lengau/AWS,
deployment, scientific fits/simulations, source edits, job intervention, worktrees
or push. Claude owns implementation, current docs/frontmatter/generated INDEX,
deployment, adoption and dispatch; root owns only this review, own R052 appends,
completion brief and lifecycle. All prior reports remain closed; no resend.

# Actual generation-9 refit pilot — Codex adoption record

Date: 2026-10-10. Reviewer: `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`, topic `95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Brief: Unimog `prompts/2026-10-10_codex_r052_v9_refit_pilot_adopt.txt`, commit
`f72c8643df73df34c6d98cb241bab1a7cbbc0715`, SHA256
`c18ffbb61a92cf59be3f2bc37dd1728d044e2f5d4a15e3d52cc2e39b6cfe4c89`.
Ownership: Unimog `a8b34f3a`; incoming `a3923966-ef28-5719-8b83-0682797eac25`
accepted before review edits or delegation.

## Verdict

**FAVOURABLE** to adopting this actual generation-9 qualification as the refit pilot through
job 100, under the existing per-admission gates.

```text
ADOPT row19-screen-pilot role=refit qualification=3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678 max_job=100
```

This completes the separate actual-pilot review reserved by
[RSC 91a567c](2026-10-10_v9r2_and_row23_rev4_codex_record.md). It does not reopen transport,
science or row-23 review. Preserve the old generation-8 pilot review, move the active old
`review_refit.json` to `gate_retired/` after checking its archived hash, then adopt this
committed record against the exact qualification above. The adoption consumer refuses to
overwrite an existing review.

Before each further admission, obtain a fresh, successful whole-role generation-9 production
receipt with zero alarms and age at most **2,700 seconds**, and pass current binding,
disposition, funding, capacity, resource and STOP checks. The dated qualification does not
replace that next observation. Existing operating rulings and standing approvals carry
forward; no renewed owner go is requested. This is no batch-dispatch authority, runtime-tail
guarantee, numerical endpoint/coverage release or change to the fixed scientific procedure.
Codex performs no dispatch.

## Exact promotion and preservation

At RSC `eabcdcc939fd7878a06386cdbb35605e524d7619`, canonical screen status, bank status and
controls are byte-identical to their reviewed `44dc6c4` candidates. Controls metadata,
including its pending/review text, was not altered. All six latest controller pins match
disk. Controls/adoption/the bound review are tracked and unchanged; their local static
authority and lineage requirements are satisfied without executing the consumers.

| Path relative to `chpc/` | SHA256 |
|---|---|
| `row19_screen_controls.json` | `45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07` |
| `row19_screen_controls_adoption.json` | `42b99b4d4ceda4bf985d371d6740e87bc77596490cd2fbe4d07ac7c81d90e1f3` |
| `row19_screen_status.py` | `f624fb633e52dd941515e15bc4ce048e72e5077914e675ddac108ef6414bfb4e` |
| `row22_bank_status.py` | `a8585effa87d5a068d416f9331f09add8a7b9c46de0de7afbc719a32b304e33e` |

The controls adoption binds version 9, the actual controls digest, review `91a567c`/SHA256
`7f5431fa004d61eb7b7d4dde1665cba7cb0851e8a1e1f86a5e5f8194f1d532a5` and its exact controls
ADOPT line. It retains the previous version-8 controls/adoption digests and both archive
locations. Bank transport remains explicitly independent, within the existing raw-bank
scope and cap of 17.

The Mac archive `results/archive/row19_screen_v8_before_v9_20261010` contains six listed
controller/authority files. Its manifest SHA256 is
`19b5115ea1f5f82b0769ad1d9389f01f9679a162271109a7c5ed1e0c842950f1`;
all six file hashes pass and their write bits are clear. It preserves controls `9f736222…`,
adoption `ccddcf71…`, admit, verifier and both old status scripts. The separate Lengau archive
of 90 files, its manifest `3f348af5…`, gate/PBS preservation, ordering before replacement,
controller deployment `5131571`, clean remote authority checks and untouched jobs' clone
are operator-reported in the committed brief. No Codex remote archive or deployment check
was performed. The independently checked local promotion and actual verifier generation
corroborate the controller transition; the remote reporting limit does not block adoption.

## Actual qualification and whole-role evidence

The three submitted hashes match the actual Mac receipt bytes:

| File under `results/row19_screen/receipts/` | SHA256 |
|---|---|
| `qualified_refit_job1.json` | `3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678` |
| `watch_refit_20261010T183244Z.json` | `c7fb5b6f8572c1f270405d5cc64c9e89a2cc60b05badc5dea21d61140e314bd1` |
| `verify_refit_20261010T183244Z.json` | `e1e68c0c3baa2f7636ec8590899005c498dbbeaf5a0c3830fb09737f568bff83` |

Qualification is production refit **job 1 only**, PBS `7523818.sched01`, token `2a25377fe9db`,
plan `39cbd2eeb7501a24961fdf72ff9c021bad211d492a5bc349df9a4724d1867e94`. Its own 24 binding
hashes are exactly reps 3–26/index 0. All match the watch and verifier; the pilot partition
has 24 new units, zero resumed/left, every slot 0–23 attributed once, 24 worker exits 0 and
scheduler/runner exit 0. Embedded whole-role evidence does not broaden the pilot's own scope.

The qualification embeds the exact submitted watch object: 18:32:44 UTC, fresh, production,
zero alarms and all ten refit jobs. The verifier emits generation/latest 9, controls
`45f840bc…`, verifier pin `d8d3c73b…`, clean lineage/code/environment problems and unchanged
production manifest `43b75f94…`. All 156 retained unit summaries have valid record/timing
flags. For every job, attributed new-unit counts and coordinates match the watch partition;
all whole-role task-binding hashes match verifier bindings. Scientific source pins and
wrapper are unchanged. No scientific payloads were interpreted or recomputed.

Qualification/watch/verifier anchors agree; their reconstructed digest is
`493eb07152876db007b4bb69a41f21038ffa2ed6c9d7410262fa7f5e3c5443eb`. Development reps 0–2
each have five equal comparisons at indices 0, 1, 3, 5, 6, required index 0 and no invalid,
missing, differing or conflicting flags. Jobs 1, 2, 4 and 6 are F/0 with 24/24 worker exits 0;
jobs 5 and 7–10 remain running in this snapshot.

The source reports that these qualification/watch/verifier hashes also match the Lengau
gate and that the v9 whole command took 62 seconds without fits. Those are operator reports,
not Codex remote observations. The local pulled `live/refit/root/gate` still carries the
previous `6cf1a513…` qualification: it precedes the qualifier's later gate publication and
does not supply a readback of the new remote gate. Review authority is bound to the actual
new `receipts/` bytes; source adoption must use their exact hash in the gate.

## Preserved disposition, scope and next action

Job 3 stays F/271, `closed-no-record`, no runner end, no status or credited unit, 24
plan-derived uncompleted coordinates at reps 51–74/index 0. Its certificate retains
**720.5533333333333 core-hours charged**, token `8c07fbed7540`, job `7527352.sched01`, plan
`4bbbac0020f83b1cb1b40d0c887c7b1c3ed3740639d081ebb12a7615cf5a2e0e`, settlement time and
bound output hash `4132a084e81ff79d776ec3eb4f37b4fbdde6bd19072068d459a2c9ee7202a8e7`.
These agree within submitted qualification/watch/verifier metadata and with the prior
closed disposition. No raw PBS output was opened and no new output-production proof is
claimed. The failed attempt receives no refund, completion or restart credit.

After retiring the old review and adopting this record, publish a fresh clean receipt and
allow the current planner and all gates to decide the next single refill. The existing
walltime-only policy remains serial, 24 cores, 48 hours, 120 GB, `haswell_reg`, reserve
1,800/per-slot 1. Refit highest job 100, campaign cap 60,000 and common cap 100,000 remain;
dated metadata grants no batch reservation or current aggregate-funding claim. Bank scope,
original completion, fixed attempted 100/B200, seeds/draws/pairing, HEAL hold, shard STOP192,
three slice attempts and prior exposure disclosures remain unchanged. Row-23 report
refinements follow separately and are not judged here.

Claude owns adoption/deployment, qualification, ledgers, dispatch and current docs,
frontmatter, generated indexes and tracker. Codex owns only this record and its own R052
appends/lifecycle. Local metadata checks and two read-only peer reviews covered promotion,
archive, qualification and binding consistency. No source/controller imports or execution,
runtime tests, fits/simulations, scientific/private outputs, SSH/Lengau/AWS/account
operations, worktrees or pushes occurred. Existing jobs and foreign files were preserved.

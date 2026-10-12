# V15-1 repair re-review: exact `806cfe3`

Codex, local 11 October / UTC 12 October 2026. Exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Whole incoming `43a9d89e-b5e1-54ef-8663-4f6499170661` brief at Unimog
`9c46c6568c37de693c88a806a15e0adc7f089a4d`, SHA256
`18345d386da004202cd6c3c0b91894ca4ca3155ab4edc552536b7cd574847ec2`,
read. Ownership committed at Unimog `c12e87e4c914f03e8e494a363d1cf6d129095220`,
then ACK `1791782384.7492878`, before review edits/delegation.

**NOT FAVOURABLE to adopt exact repaired candidate `806cfe3` yet.**
No ADOPT literal for controls
`b597fe541c5c0f121ddd391495b42b533c59c31bd6d5b008d760a7ed2e903f7f`.
The original out-of-plan timing trace is fixed. One narrow canonical-path variant
of V15-1 remains; it needs a literal pathname check and focused negative test,
not a fit or simulation.

## Remaining V15-1 canonical-path variant

`candidate_v15/row19_screen_admit.py:1010` permits any digit sequence after
`rep`, including leading zeros. `:1091–1094` converts that sequence to an integer
and checks the numeric coordinate and survivor slot. It does not compare the
actual relative pathname with the formatted canonical pathname.

Concrete static trace, not an actual incident or executed test:

- A legitimate surviving planned worker is `67/2` in slot 0; its canonical
  record/timing and all other eligible crash evidence remain valid.
- Also retain `timing/rep067/t_002.json` naming the failed PBS ID with integer
  `rep=67`, `index=2`, `slot=0`. It may contain identity/measurements that differ
  from the legitimate canonical timing. There is no alias record directory.
- The regex matches; parsed pathname integers equal the embedded integers;
  `surv["67/2"] == 0`. The proof accepts the extra file.
- The producer verifier enumerates records and their canonical paired timings
  (`row19_screen_verify.py:175–199`), using `row19_shard.timing_path:127–128`,
  which formats `rep{int(rep)}`. It reads `rep67`, not this `rep067` alias, and
  emits no separate verifier unit for the alias. Downstream unit checks and
  shared-proof recomputation do not reject it.

Numeric coordinate attribution is now correct, so this is **not** the original
unplanned-coordinate bypass. The remaining issue is acceptance of an extra
noncanonical same-job artifact with unvalidated provenance while publishing or
consuming a clean crash disposition. A byte-identical duplicate would be harmless;
the code establishes neither identical bytes nor validity of the alias. It does
not earn completion credit, but fails the required canonical-path proof.

Require exact relative-path equality with the publisher's formatted path:

```text
timing/rep{rep}/t_{index:03d}.json
```

Use the already validated integer fields to format it. This also avoids permissive
path spelling/regex-end cases. Add a `rep067` negative beside a valid `rep67`
survivor, including contradictory alias provenance; shared proof and consumers
must refuse and retain the original crash hold. Keep legitimate canonical timings
and later-bound completions passing. Return the new exact candidate/controls.

## What the repair resolves

The strict field, numeric pathname/coordinate and exact survivor coordinate→slot
checks (`:1080–1095`) reject the original `rep999/777` orphan, missing/bool/string
fields, wrong survivor slot, unplanned index and the tested path/content mismatch.
The status negative checks the three original alarms, and admission checks a new
orphan written after the receipt and a current survivor timing changed to another
slot (`test_crashed_slot_r14.py:254–267`). Current-root recomputation is still
required. Another job's timing is correctly outside this proof's same-job scope;
other ordinary verifier rules remain in force.

The tightened signal regex fixes the PBS spool prefix and campaign log-root
path, and requires the screen-manifest basename under `chpc`. Its manifest path
prefix may still vary; no new material regression was found from this bounded
change. The operator-cause note now qualifies the inference, identifies the
unobserved process/node and uses 36.7%; it is not a cause certification.

The remaining consumers, status, pilot exclusion, retained 4/4 exits and charge,
survivor partition checks, later-bound completion, planner and gates are unchanged
from the previous review and retain their credited safeguards. Do not reopen the
whole scientific or previous controls review to make this small repair.

## Pins, tests and limits

Working and committed `806cfe30886a1f6869d3f0904654e4f6d5a6894d` hashes match:

- admission `13a742acef617a4a052382ba91f156ec225b3cab12608533d8a8195f51916eb0`;
- unchanged status `0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b`;
- test `eec06c1f233823689c75879cc8a82f5f662cc2183fed048a78c3b22c82f0d88f`.

Prior controls history, other 12 source pins, programme, partition, resources and
S contracts remain unchanged. The test source supports 67 checks when its
conditional real replay runs, 66 otherwise; this pathname variant is not covered.
The brief now properly discloses the cached replay/stubbed EC2 check, temporary
regression repointing and correction of the old 31/31 claim. Reported runtime
67/67, 51/51, 29/31 versus 29/31 and cached replay were **not run here**.
They do not certify fresh whole-role production evidence.

Three bounded peers and root performed static source/diff/test/contract/pin checks
only. No source execution/import/runtime tests, scientific fit/simulation,
raw/private/live outputs, SSH/AWS, source implementation edits, adoption,
deployment, activation, qualification, refill, job intervention, worktrees or push.
Author owns this minimal proof/test repair and current docs/frontmatter/INDEX/
operating changes/jobs; root owns this record, own R052 appends, sole findings and
lifecycle. Previous report `ec27287` and accepted `c0a594a9`/`5ea51fc5` stay closed.

After a repaired exact package is favourable: preserve adopted v14, promote/deploy
both reviewed controller files, get actual fresh whole-role evidence, and follow
step 8's one existing-pilot metadata qualification, new hash, actual-source review
and matching max100 adoption. No repeat fit or implicit pilot/refill/result
authority. All standing owner/resource/qualification/release/exposure limits,
source jobs and foreign files remain.

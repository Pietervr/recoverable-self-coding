# v17 pilot adopter — literal-check repair

20 October 2026 UTC. **FAVOURABLE for the exact one-line repair at `9df2a1f778ec81eae25af0d67526bba95170e44f`. No blocking finding.**

FAVOURABLE row19-screen-migration version=17 adopt_pilot17_fix=9df2a1f778ec81eae25af0d67526bba95170e44f

The favourable pilot opinion at `35767759fa5e0bcff40bbba82746fbb35de98cf4` remains unchanged, including qualification `8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa` and absolute `max_job=100`. This repair removes a false refusal in the wrapper; it supplies no new qualification, budget, packing, release or numerical authority. Actual supported adoption and the existing fresh admission gates still have to succeed before refills.

Read the complete brief `Unimog-Projects/prompts/2026-10-20_codex_r052_adopt17_fix_review.txt` at `9ac110fd2d4fe438ce166e1d25ac2d2dfdb084f1`, SHA256 `1e3f6cffef54a0df547248c2315d67a64e0dcd5ef4f144102b362705ba833a16`. Ownership was committed at Unimog `c4b2c28804cbe830788f3a404de45782d3ad6f2c`, then handoff `b22db805-b7b1-5eb8-98c1-677ed7074bb3` was accepted before review edits. Exact session remains `GPT: R052 Entropy paper`.

## Finding and repair

The original wrapper trims each record line, then pipes into `grep -qxF`. On a match, `grep -q` can exit while `sed` still has output to write. Under the retained `pipefail`, a resulting producer SIGPIPE makes the whole pipeline fail even though the exact literal was found. This is scheduling/buffering dependent; record size alone is not a deterministic threshold.

The changed line uses `grep -xF -- "$LIT" >/dev/null`. It retains fixed-string, whole-line matching after the same whitespace trimming and suppresses output while consuming the stream. Missing or altered literals still fail. Producer/read errors still propagate through `pipefail`. The script's other bytes are identical to the previously reviewed `5fbcf2c` version; the fix commit also adds only the diagnostic reproduction script.

Both current files match the fix commit. SHA256 identities are adopter `4f77547a7c0e0f71c381206063a878ab16922ff42df2be7c3b12e67682ce9859` and reproduction `e91aa2e843c4c37dc4b765ab92da2b591cdde084196ae13a63246d8a55fdfcc9`. The source was read in full. Exact qualification/literal/ceiling, deployed/adopted v17, canonical activation, retired review, drain/locks, containment, tracked unchanged record and no-overwrite checks remain intact. The literal check still precedes controller record copy/commit and supported gate adoption; temporary payload staging occurs earlier. The source's aborted live attempt is an operator record, not an action independently replayed here.

## Independent checks

The parent passed **7 exact binding/order checks**. A separate reader passed **20 bounded shell checks**, including the actual 9,544-byte committed pilot review; absent and altered qualification/role/ceiling/prefix/suffix refusals; whitespace/fence/EOF/CRLF acceptance; missing-file refusal; and a producer emitting the matching literal then exiting 7. That last case retained pipeline exit 7 with grep exit 0, correctly refusing rather than hiding the producer error.

The fully read source reproduction independently printed old 4/5, new 5/5 and absent 0/1. A separate approximately 2.1 MB synthetic early-match record reproduced old `sed=141, grep=0` in all five attempts. The old form on the actual owned review happened to pass 5/5 locally. This confirms the failure mechanism without claiming deterministic local reproduction of the operator's exact host/record failure. The source reproduction is a diagnostic counter script, not a self-enforcing passing test; the independent helper checks expected outcomes separately.

The full 37-case migration suite was **not rerun**. It seeds from a live Mac base whose qualification has already changed through migration, so it no longer supplies the old v16 starting world unchanged. That fixture limit is not a failure of this repair. This narrow pass does not recreate remote deployment or adoption, and does not retrospectively expand the original suite's coverage of large records.

Private evidence: `/private/tmp/r052_adopt17_fix_binding_20261020.{py,json}` and `/private/tmp/r052_adopt17_fix_checks_review_20261020.md`, with its linked helper/result receipt. Checks used explicit source/admin inputs and private fabricated records only. No project import, full migration harness, qualifier, adopter, planner/refill, SSH/cloud/PBS/authority/worker operation, fit/simulation/decoding, protected/raw scientific payload read, whole-tree copy/hash, worktree, push or publication occurred. Test children finished; no task-owned job/listener/poller remains. Source retains implementation, current records, ledger and dispatch; all standing approval, budget, exposure and foreign-file limits persist.

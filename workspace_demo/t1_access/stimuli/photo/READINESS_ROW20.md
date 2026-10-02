# Photograph arm, ledger row 20: readiness, revision 9

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 8 (RSC `9f696c6`) as NOT ON BOARD in a combined record with the AI
reader (RSC `7fdb937`): A2 and A3 closed, A1's timeout path credited, B, D, the 60 s closure and the ~21 GiB/s
qualification still credited; left: A1's healthy-guardian external death and receipt-publication window, plus five
summary alignments (handoff `50ab6395`). `STAGE_A_CRITERIA.md` §0000 maps the two transitions to code and fixtures;
§000, §00, §0 and §1 keep revisions 8, 7, 6 and 5; §7 states the limits. The owner's Stage A gate decision is open.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. Inputs, cases and the 178 planned attempts are byte-identical; revision 8 changes no plan constant (plan, manifest
and budget as in revision 7); the plan moved to revision 7 in the envelope's
controller constants (tick staleness 0.15 s, finalisation 50 s, revocation 5 s, exit margin 5 s, close charge 60 s,
guardian setup 300 s) and the budget hash.

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock (counted from its own process
start); the gates, each phase and the report run as gated workers released only after an armed, identity-checked
watchdog and a durable record of both identities; every stop SIGKILLs the whole group at once; the final record is
admitted only with its marker (`final_admitted`).

**Mechanism evidence.** All from synthetic, non-development fixtures; values in `controller_fixtures.json` (revision 8)
and `STAGE_A_CRITERIA.md` §000/§00: failed starts charged across a pre-pending stall, a long first persist with an
existing clock and two failures during reconciliation (§000), an external death before the pending entry and
recovery during the guardian's receipt publication (§0000); the complete observation interval with each path's own
baseline (§00): ordinary stop from its preceding successful reading to the kill, the leader's death and verified
extinction; the blocked-I/O stop from the deciding iteration; the first stalled sample from the pre-GO arming tick;
the third stalled sample from its preceding successful reading; the guardian
covering a stalled directory creation, a stalled final output and a post-close death; the closed session charging the
whole bounded closure; failed starts and missing death evidence charged on the same boot; the guardian in the task
memory aggregate; strict, witness-bound recovery authority and exact recovery sets in pre-native and final admission.

**The memory margin.** Configured interval 0.16 s from the previous successful reading (ordinary ≤ 0.12 s; stalled
0.15 s tick staleness from the reading's own time + 10 ms poll) plus the pinned fixture's SIGKILL delivery 0.0273 s →
about 21.4 GiB/s; on the latest measured endpoint (a stalled sample's controller gone 0.1948 s after its baseline)
20.5 GiB/s; stated as about 21 GiB/s and accepted by Codex at `12a7f20` as the declared, measured local qualification
under stated scheduling assumptions. One synthetic thread (13.63 GiB/s) fits; 2–8 threads (32.29–75.22 GiB/s) do not.

**Source records.** Admission requires the current `dev_pool.json` and `provenance_checks.json` byte-identical to the
plan's pins. The eight Stage A views (chili, clothes, crow, hamburger, horse, jacket, taxi, wagon) are unchanged; each
removed stock listing is recorded as "no conflicting claim observed, upload date unknown" and is rechecked at
publication.

**Before the audit (not Stage A gates).** The audit freeze states the 61-of-63 rule; the audit map applies the
specificity rule with its construction identities recorded; the audit scorer's code is bound by `audit_package.py`
to the pins the audit package will record.

**Forecast.** Unchanged (one out-of-pool image; it establishes nothing). Whole stage well under 30 min against 4 h
minus the 1,808.73 s carried and the 720 s of reserves, plus about 8 s of identity hashing per worker (four workers)
and the 60 s charged closure (finalisation allowance 50 s + revocation 5 s + exit/output 5 s); task memory about 31 GiB against the 44 GiB stop; storage about 0.4 GB against
1 GiB minus 64 MiB.

**Still needed.**

1. R052 submits this exact package to Codex, or the owner decides the alternative R052 has put to him (go now, Codex
   reviews the report).
2. Codex gives a favourable review that carries the attestation (in its own record), if that route is taken.
3. The owner gives a go bound to the package.

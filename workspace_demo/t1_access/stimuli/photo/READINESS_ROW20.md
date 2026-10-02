# Photograph arm, ledger row 20: readiness, revision 7

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 6 (RSC `bb4f076`) as NOT ON BOARD in a combined record with the AI
reader (RSC `c036c00`), crediting kill-first, the guardian, bounded revocation and the 195-count refusal, and keeping
the ~22 GiB/s memory qualification acceptable in principle. R052 sent four remaining Stage A conditions (handoff
`cdefd254`). `STAGE_A_CRITERIA.md` §00 maps them to code, fixture and measurement; §0 and §1 keep revisions 6 and 5;
§7 states the limits. The owner's Stage A gate decision (go with Codex reviewing the report) is pressed by R052 and
still open.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. Inputs, cases and the 178 planned attempts are byte-identical; the plan moved to revision 7 in the envelope's
controller constants (tick staleness 0.15 s, finalisation 50 s, revocation 5 s, exit margin 5 s, close charge 60 s,
guardian setup 300 s) and the budget hash.

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock (counted from its own process
start); the gates, each phase and the report run as gated workers released only after an armed, identity-checked
watchdog and a durable record of both identities; every stop SIGKILLs the whole group at once; the final record is
admitted only with its marker (`final_admitted`).

**Mechanism evidence.** All from synthetic, non-development fixtures; values in `controller_fixtures.json` (revision 7)
and `STAGE_A_CRITERIA.md` §00: the complete observation interval from the previous successful reading to the kill, the
leader's death and verified extinction (ordinary stop, blocked I/O, first and third stalled samples); the guardian
covering a stalled directory creation, a stalled final output and a post-close death; the closed session charging the
whole bounded closure; failed starts and missing death evidence charged on the same boot; the guardian in the task
memory aggregate; strict, witness-bound recovery authority and exact recovery sets in pre-native and final admission.

**The memory margin.** Stipulated interval 0.16 s from the previous successful reading (ordinary ≤ 0.12 s; stalled
0.15 s tick staleness from the reading's own time + 10 ms poll) plus the measured SIGKILL delivery → the 4 GiB headroom
covers growth up to about 21.5 GiB/s. One synthetic thread fits; 2–8 threads do not. Accepted in principle by Codex as
a declared, measured limit for this local Stage A, under stated scheduling assumptions.

**Source records.** Admission requires the current `dev_pool.json` and `provenance_checks.json` byte-identical to the
plan's pins. The eight Stage A views (chili, clothes, crow, hamburger, horse, jacket, taxi, wagon) are unchanged; each
removed stock listing is recorded as "no conflicting claim observed, upload date unknown" and is rechecked at
publication.

**Before the audit (not Stage A gates).** The audit freeze states the 61-of-63 rule; the audit map applies the
specificity rule with its construction identities recorded; the audit scorer's code is bound by `audit_package.py`
to the pins the audit package will record.

**Forecast.** Unchanged (one out-of-pool image; it establishes nothing). Whole stage well under 30 min against 4 h
minus the 1,808.73 s carried and the 720 s of reserves, plus about 8 s of identity hashing per worker (four workers)
and the 60 s finalisation allowance; task memory about 31 GiB against the 44 GiB stop; storage about 0.4 GB against
1 GiB minus 64 MiB.

**Still needed.**

1. R052 submits this exact package to Codex, or the owner decides the alternative R052 has put to him (go now, Codex
   reviews the report).
2. Codex gives a favourable review that carries the attestation (in its own record), if that route is taken.
3. The owner gives a go bound to the package.

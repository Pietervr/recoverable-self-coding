# Photograph arm, ledger row 20: readiness, revision 5

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 4 (RSC `d7a486a`) as NOT ON BOARD in a combined record with the AI
reader (RSC `1bf9890`). R052 sent the eight Stage A conditions A1–A8 (handoff `8c9dac2b`). `STAGE_A_CRITERIA.md` §1
maps each condition to its code, fixture and measurement; §7 states the limits. The owner is separately asked (by
R052) whether Stage A, once revision 5 closes these to its own fixtures, runs on his go with Codex reviewing the
report instead of a fifth package attestation.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. Inputs, cases and the 178 planned attempts are byte-identical to revision 4; the plan moved in `revision`, the
declared controller constants and the budget hash.

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock (counted from its own process
start); the gates, each phase and the report run as gated workers released only after an armed, identity-checked
watchdog and a durable record of both identities; every stop SIGKILLs the whole group at once; the final record is
admitted only with its marker (`final_admitted`).

**Mechanism evidence.** All from synthetic, non-development fixtures (`controller_fixtures.json`):

| Evidence | Measured |
|---|---|
| Deadline kill → reap of a SIGTERM-ignoring worker (blocked in C / busy in MLX) | 0.019 s / 0.029 s |
| Worker group gone after the controller was SIGKILLed | 0.022 s |
| Blocked controller writer | group gone 0.031 s, controller killed 0.059 s after the stale beat |
| Hung sampler (no tick for 0.1 s) | group gone 0.034 s after the observation |
| Startup failures (exit watch, watchdog not armed, first persist) | worker never released, ran nothing, dead and reaped |
| Immediate restart with an unrecorded live member | killed by group enumeration; the watchdog retired last |
| Exit peak in the task aggregate | 1 GiB exit spike in `member_max`, `task_lifetime_sum` and the final aggregate |
| Largest sampling iteration's work; SIGKILL overshoot; growth rates | 5.1 ms (limit 50 ms); 0.001 GiB; 14.7 GiB/s one thread, 36–75 GiB/s with 2–8 threads |
| Completion marker | post-rename failure or block, marker failure, size mismatch: none admitted |
| Ledger counterexample; consistent non-plain change before native | refused; refused before the native model exists |

**The memory margin, with the numbers.** Enforced observation-to-death ≤ 0.18 s, so the 4 GiB headroom covers
growth up to about 22 GiB/s. One synthetic thread (14.7 GiB/s) fits; 2–8 threads (36–75 GiB/s) do not. The margin is
qualified to 22 GiB/s and not claimed beyond it (STAGE_A_CRITERIA.md A3).

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

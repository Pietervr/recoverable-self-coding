# Photograph arm, ledger row 20: readiness, revision 6

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 5 (RSC `2610d8a`) as NOT ON BOARD in a combined record with the AI
reader (RSC `b569f8a`), closing A1, A7 and A8 and accepting the memory qualification in principle. R052 sent the four
remaining Stage A conditions (handoff `c39df47e`). `STAGE_A_CRITERIA.md` §0 maps them to code, fixture and
measurement; §1 keeps revision 5's map; §7 states the limits. The owner is separately asked (by
R052) whether Stage A, once revision 6 closes these to its own fixtures, runs on his go with Codex reviewing the
report instead of a fifth package attestation.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. The plan, inputs, cases and the 178 planned attempts are byte-identical to revision 5 (the envelope's constants
are unchanged).

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock (counted from its own process
start); the gates, each phase and the report run as gated workers released only after an armed, identity-checked
watchdog and a durable record of both identities; every stop SIGKILLs the whole group at once; the final record is
admitted only with its marker (`final_admitted`).

**Mechanism evidence.** All from synthetic, non-development fixtures (`controller_fixtures.json`, revision 6):

| Evidence | Measured |
|---|---|
| Memory stop: deciding observation → leader dead / verified extinction | 0.009 s / 0.062 s |
| Memory stop with the I/O thread blocked forever: observation → worker gone (timed by the test) | 0.008 s |
| Never-returning first / third sample (tick check armed before release) | group gone 0.033 s, controller killed 0.048 / 0.046 s after the watchdog's observation |
| Controller-only persist blocked after the watchdog retired | the guardian kills the controller at the shortened cap (run 18.7 s) |
| Marker write stalls after its rename; also with the unlink blocked | exit 75 in 10.6 s / 15.6 s; tombstone; not admitted |
| Deadline kill → reap (blocked in C / busy in MLX) | 0.002 s / 0.002 s |
| Worker group gone after the controller was SIGKILLed | 0.030 s |
| Blocked controller writer | group gone 0.035 s, controller killed 0.050 s after the stale beat |
| Startup failures; immediate restart with unrecorded members | worker never released / every member killed, watchdog last |
| Codex's unauthorised-extra-try ledger (195 of 200) | refused in final and pre-native admission |

**The memory margin.** Enforced reading-to-reading bound 0.16 s (with a stalled sampler) plus the measured SIGKILL
delivery (0.025 s, evidence, not a bound) → the 4 GiB headroom covers growth up to about 22 GiB/s. One synthetic
thread (11.1–14.7 GiB/s) fits; 2–8 threads (32–75 GiB/s) do not. Codex accepted this in principle as a declared,
measured limit for this local Stage A (RSC `b569f8a` Question 2); Stage A reports the model's actual growth and peak.

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

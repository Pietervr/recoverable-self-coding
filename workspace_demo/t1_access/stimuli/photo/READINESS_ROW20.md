# Photograph arm, ledger row 20: readiness, revision 4

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 3 (RSC `a59fc2d`) as NOT ON BOARD (RSC `081f17b`) and agreed the
attestation format. R052 sent the closure set 1–7 (handoff `dfdac45a`). `STAGE_A_CRITERIA.md` §1 maps each closure
to its code, fixture and measurement; §6 states the limits.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. Inputs, cases and the 178 planned attempts are byte-identical to revision 3; the plan moved in `revision`, the
declared controller constants and the budget hash.

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock; the gates, each phase and the
report run as workers it watches with an independent watchdog, cleans up as whole groups and reaps.

**Mechanism evidence.** All from synthetic, non-development fixtures (`controller_fixtures.json`):

| Evidence | Measured |
|---|---|
| Deadline kill → reap of a SIGTERM-ignoring worker (blocked in C / busy in MLX) | 3.03 s / 3.04 s |
| Worker group gone after the controller was SIGKILLed | 3.15 s |
| Watchdog on a stale heartbeat (blocked sampler; blocked writer) | group gone 3.05 s after the 10 s staleness |
| Leader-first exit with a surviving child; a child that left the group | both killed before the next phase |
| A recorded pid whose start time differs | not signalled |
| Exit peak read before reap | 1.057 GiB for a 1 GiB touch-and-exit |
| Nonzero MLX cache counted; retention after a fall | 2.0 GiB cache in a 4.222 GiB ledger; 2.222 current vs 4.222 lifetime |
| Full observation interval; fastest growth; unseen growth bound | 0.113 s; 12.7 GiB/s; ≤ 1.43 GiB vs 4 GiB headroom |
| Persistence failure | exit 75 in 9.4 s, no FINAL |
| Validator mutations, strict-guard refusals, reviewed-package builder | `tests/test_stage_a_runner.py` |

**Source records.**

- Stage A's eight are chili, clothes, crow, hamburger, horse, jacket, taxi and wagon. Clothes replaced mask on 2
  October, because mask has a live stock listing crediting another author.
- The other views' stock listings had all been removed when they were checked on 2 October. Each is recorded as "no
  conflicting claim observed, upload date unknown". A first crawl bounds when a listing existed from above; it does
  not establish the upload date or a later upload. Each is rechecked at publication.

**Before the audit (not Stage A gates).** The audit freeze states the 61-of-63 rule; the audit map applies the
specificity rule with its construction identities recorded, and the audit scorer is bound to the map's pinned hash.

**Forecast.** Unchanged from revision 2 (one out-of-pool image; it establishes nothing). Whole stage well under 30
min against 4 h minus the 1,808.73 s carried and the 720 s of reserves, plus about 8 s of identity hashing per worker
(four workers); task memory about 31 GiB against the 44 GiB stop; storage about 0.4 GB against 1 GiB minus 64 MiB.

**Still needed.**

1. R052 submits this exact package to Codex.
2. Codex gives a favourable review that carries the attestation.
3. The owner gives a go bound to the package.

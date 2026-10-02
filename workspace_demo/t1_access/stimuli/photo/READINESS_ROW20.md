# Photograph arm, ledger row 20: readiness, revision 3

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any development image.

**What this answers.** Codex reviewed revision 2 (RSC `e598f96`) as NOT ON BOARD (RSC `69539bb`). R052 sent the
seven closure groups (handoff `51739bd8`). This revision answers them; `STAGE_A_CRITERIA.md` §1 maps each group to
its code, test and measurement, and §6 states the limits.

**The package.** `stage_a.py package` prints the five hashes. The go must bind them through the attested review
(criteria §4). The brief to R052 carries the exact values for this commit.

**Run.** `stage_a_controller.py run`: one controller process that holds the lock and the clock, with each phase in
a worker it reaps.

**Mechanism evidence.** All from synthetic, non-development fixtures:

| Evidence | Source |
|---|---|
| Kill → reap of a worker ignoring SIGTERM: 3.01 s while blocked in C; 3.01 s while busy in MLX/Metal matmuls | `controller_fixtures.json` |
| Process group killed together | `controller_fixtures.json` |
| Additive host + Metal footprint, and a retained transient peak | `memprobe` fixture |
| A persistence failure ends in a bounded exit | `controller_fixtures.json` |
| Validator mutation tests | `tests/test_stage_a_runner.py` |

**Source records.**

- Stage A's eight are chili, clothes, crow, hamburger, horse, jacket, taxi and wagon. Clothes replaced mask on 2
  October, because mask has a live stock listing crediting another author.
- The other views' stock listings had all been removed when they were checked on 2 October. Each is recorded as "no
  conflicting claim observed, upload date unknown". A first crawl bounds when a listing existed from above; it does
  not show when it was uploaded. Each is rechecked at publication.

**Forecast.** Unchanged from revision 2 (one out-of-pool image; it establishes nothing). Whole stage well under 30
min against 4 h minus the 1,808.73 s carried and the 720 s of reserves; task memory about 31 GiB against the
controller's 44 GiB stop; storage about 0.4 GB against 1 GiB minus 64 MiB.

**Still needed.**

1. R052 agrees the attestation format with Codex and submits this exact package.
2. Codex gives a favourable review that carries the attestation.
3. The owner gives a go bound to the package.

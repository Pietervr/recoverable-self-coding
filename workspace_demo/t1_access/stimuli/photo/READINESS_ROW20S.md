# Photograph arm, ledger row 20 supplement (the OS bridge): readiness, revision 6

R084 (Claude), 3 October 2026. **The supplement has no go.** It is built and tested only; nothing ran: no forward,
no model load, no controller session, no `captures/photo_stage_a_supplement/` tree. The accepted Stage A tree
(`captures/photo_stage_a/`) and the revision-15 package files are byte-identical.

**Revision 2** (Codex `478196f` P1, handoff `d9587571`): the supplement is one session from its first start - a
restart after any start without an admitted PASS writes the terminal record and dispatches nothing; an admitted PASS is
never superseded or regenerated; missing measurements count over every session (`STAGE_A_SUPPLEMENT_CRITERIA.md` §R2).

**Revision 6** (Codex `7e1d1e0`, handoff `b34859b2`): lost-group cleanup through the base end_group with the
saved members (UNCONFIRMED otherwise, safeguard kept); complete, checked intent publication before GO; the final bound
to a create-once copy of the durable controller record checked for every intended endpoint's peak (§R6).

**Revision 5** (Codex `f716bea` P2, handoff `6d3504b2`): each endpoint's release intent is an append-only file
published before GO (`intent/<endpoint>.json`), read by restart, measurement and recovery - no whole-file replacement
of controller.json can erase a start (§R5).

**Revision 4** (Codex `410b580` P2, handoff `d0c368a3`): any durable endpoint worker record - released or not
- is start evidence, so a crash between GO and the released snapshot still refuses the next session (§R4).

**Revision 3** (Codex `1abb851` P1, handoff `02cfa037`): any record of a prior start without an admitted PASS
refuses the session before supersede, gates, any worker, receipt or final - derived from the ledger and records, not
from the terminal file (whose write failing still refuses); a PASS needs both endpoints from the same session (§R3).

**What it is.** Codex's record RSC `b0db0f9` requires, before row 21's first CAL forward, a row-20 supplement on the
original DEV-CAL input 00 on the current macOS 27.0.1: one plain instrumented forward (`00-plain-os2701`) compared
directly with input 00's retained 27.0 record (`00-plain`), and one native forward (`00-native-os2701`) compared
directly with the new instrumented output - the accepted comparator, each executed comparison receipt retained. Starts 194 -> 196 of
200; time, storage and memory charged to row 20. Specification, design and fixture map: `STAGE_A_SUPPLEMENT_CRITERIA.md`.

**The package** (`stage_a.py supplement-package`): `supplement_criteria_sha256`, `supplement_identity_sha256`,
`supplement_plan_sha256`, `plan_sha256` (the unchanged 178-id plan `3faebf4e...`), `manifest_sha256` (`e816f843...`),
`budget_sha256` (the supplement envelope). The brief to R052 carries the exact values for the commit.

**Run** (after Codex's record and the owner's go only): `stage_a_controller.py supplement` - the gates (declared
environment: macOS 27.0.1, build 26A434, arm64), the instrumented worker, the native worker (separate process), the
receipt; final `SUPPLEMENT_FINAL.json` with its marker. Row 21 calls `stage_a.supplement_receipt_ok(<its identity>)`
before its first CAL forward and holds on anything but an admitted PASS with a compatible execution.

**Mechanism evidence.** `tests/test_stage_a_supplement.py` (55, revision 6: the plan, the gates, the two phases and their
failures, no resumption after a start and the restart rule, the receipt, the row-21 verifier's holds, and the SupplementController with
synthetic workers and the real controller, watchdog and guardian) and the retained suite run recorded in `reviews/`.
No development forward; the Stage A record files are read from a fake run in a temporary tree, and the live tree only
by the desk plan and load checks.

**Still needed.**

1. R052 submits this exact package to Codex.
2. Codex's record on it, carrying a favourable attestation (row `20`, stage `A-supplement`) if favourable.
3. The owner's go bound to the package (`ROW20S_GO.json`).

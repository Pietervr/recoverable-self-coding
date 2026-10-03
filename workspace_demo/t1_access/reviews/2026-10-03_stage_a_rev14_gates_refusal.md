# Stage A revision 14 resume, 3 October 2026: REFUSED at the gates - the machine's macOS moved 27.0 -> 27.0.1

R084, 3 October 2026 (16:27 UTC). Under the owner's "1. and 2. go" (3 October), bound by R052 at RSC `28f1fc5`
(`ROW20_GO.json` to Codex's favourable revision-14 record `ac60eb8`; `TERMINAL_RELEASE.json` naming the 3 October
TERMINAL bytes `73e83192…`). Command `.venv-image/bin/python stimuli/photo/stage_a_controller.py run`, launched
detached at 16:27:1xZ from HEAD `28f1fc5`; runner exit **2** at 16:27:25Z. Outputs in `2026-10-03_stage_a_rev14_gates_refusal/`.

## What happened

The gates worker refused before any forward and before the native worker (so before any transition):
`refused: execution identity now 5aed48ef… differs from the frozen 3d6d991d…`. The controller's outcome:
`REFUSED, gates: worker exited 1`. Read-only diagnosis (`ident_diff.py`, its output retained): the ONLY differing field
of the execution identity is `macos`: frozen `27.0`, now `27.0.1` (`sw_vers.txt`: 27.0.1, build 26A434). The Mac
restarted on the morning of 3 October and took the macOS point update. Snapshot, packages and their file maps, the
lens, the local code, plan, manifest, positions receipt and the dispatch are unchanged.

## State after it (checked)

- `TERMINAL.json` byte-unchanged (`73e83192…`); the owner's release still valid (`terminal_release` OK, not active).
- The ledger's identity slot still revision 12 (`c0fb2ea0…`); no `IDENTITY_TRANSITION.2.json`; no record written,
  relabelled or recomputed; no forward.
- The controller charged this start: seconds_total 2,169.5 -> 2,240.9 s of 14,400 s.
- The earlier `STAGE_A_FINAL.json` was superseded by the controller's start, as designed.

## Why it cannot simply resume

`macos` is in the execution identity (so the package's `identity_sha256` no longer equals the reviewed one) and in
the transition's FROZEN_KEYS (so revision 12 -> current cannot be admitted while the predecessor body says 27.0). Any
route - regenerating the identity on 27.0.1, or narrowing what the identity or the transition freezes - changes the
reviewed package and needs R052's decision and Codex's record. Nothing was changed; Stage A waits.

The reader's package is unaffected (24 fields recomputed now = the go's `3e2bcdcc…`; its `sandbox-exec` hash is
unchanged).

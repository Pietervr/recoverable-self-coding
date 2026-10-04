# Photo test suite on image-audit revision 3: retained-output run

R084, 4 October 2026. The whole photo test suite on the committed audit revision 3 (RSC `babe835`), every byte of output kept in `2026-10-04_photo_suite_audit_rev3_run/`. No model or reader was called and no audit item was sent. New in this revision: `tests/test_ai_audit_cli.py`, 7 fresh-process fixtures through the public CLI (`ai_audit_exec.main`) in a temporary repository copy with a fake reader binary at the owned-CLI path (provider substitutions only: the fake, no sandbox-exec around it, a stub exec-invocation receipt), the real WordNet scorer under .venv-build and the real set derivation.

## Identity

- RSC HEAD `babe8357ebb2b8e03f9148301db2e91dbb2d0451`; photo directory status before the run: 0 lines.
- 2026-10-04T11:51:06Z to 12:47:47Z (UTC).
- Audit package digest `760f8f58aacc77787affb84076fa57f992ebe4b79e98f8d5ade3692bc6cbaa0f` (39 fields), equal to the package re-derived from babe835. The reader revision-17 package recomputes equal to `AIREADER_GO.json`; Stage A and the supplement are untouched.

## Counts

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | 427 | 43 | 0 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |

Against revision 2 (9c987a9: 420): + 7 CLI fixtures; the 26 in-process audit tests pass; the 43 skips have the same causes; the revision-2 load-sensitive controller ordering failure did not recur.

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `e887ee4daedbff6aefa5d4ac1adbf0d40e2bab5b72acb335e6df541997fe3e0b`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `ended.txt` 21 bytes `6b8749da9a0fde7b2d65ff4ec46eb2b151ab44d46415e556a7e41a209db34983`
- `head.txt` 41 bytes `d18c1f915e5150ce5e87dab8c47ab9817af96076f1d0834ad4cc539be2d16bdd`
- `main.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `main.stderr.txt` 69875 bytes `94a06ddc63eb72b7b9236ec5ec4ddab39a1f7d46036cbf0b757c7083a2dbc46f`
- `main.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `started.txt` 21 bytes `2522b86024e22e45b5063daaaaa3d80448b7b91035f7d11798fc0a8db0b166ed`
- `status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

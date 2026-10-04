# Photo test suite on the image-audit package (round 1): retained-output run

R084, 4 October 2026. The whole photo test suite on the committed audit package (RSC `b055a81`), every byte of output kept in `2026-10-04_photo_suite_audit_r1_run/`. No model or reader was called and no audit item was sent; the audit tests drive the reviewed reader `Job` through `ai_audit_exec.AuditJob` with the fake CLI on synthetic images; the codex binary (the owned copy, captures/reader_cli/codex-0.160.0) ran only its local subcommands and the exec-invocation receipt with all network denied and a synthetic 8x8 image.

## Identity

- RSC HEAD `b055a81e069483ea38c62dae9d87fb48e9e800c7`; photo directory status before the run: 0 lines.
- Started 2026-10-04T08:35:15Z, ended 2026-10-04T09:18:30Z (UTC).
- Audit package digest `2b8d8aa66fa83ba09fa022527fe69c34e8ec6c5bf4a012249f43e42f5a7c718c` (38 fields; `ai_audit_exec.py package`), equal to the package re-derived from b055a81. The reader revision-17 package recomputes equal to `AIREADER_GO.json` (unchanged); the Stage A and supplement packages are untouched.

## Counts

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | 401 | 43 | 0 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |

Against the supplement revision-6 run (RSC 98c8606: 394 + 27): the 7 new `test_ai_audit.py` cases, all passing; the 43 skips have the same causes (16 WordNet cases run in the build row, 5 + 22 moved-state Stage A transition fixtures).

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `570472ee7181bc2dbd9ea800a2fc2192487a358a912a9d1444489c9a5b49a88f`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `ended.txt` 21 bytes `b5c48e3e169adde2ec895294c4bb33bbcd886b4405abfa74e054bb7ff3b6f2bf`
- `head.txt` 41 bytes `e9f99a84a95c8e2b9df82629a28d8a49126a09f86d4abe8cfe490ca2998f35fa`
- `main.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `main.stderr.txt` 66630 bytes `183dab4d146d1c7b7483416b302aa063c50c866fb8c5c09c4d45fe1e948d8c7c`
- `main.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `started.txt` 21 bytes `de789134f7abd386546956da0963efe32816804018352d2a1593b76889a77010`
- `status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

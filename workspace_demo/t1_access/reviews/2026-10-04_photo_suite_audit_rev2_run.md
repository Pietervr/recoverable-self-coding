# Photo test suite on image-audit revision 2: retained-output run

R084, 4 October 2026. The whole photo test suite on the committed audit revision 2 (RSC `d2b42cd`), every byte of output kept in `2026-10-04_photo_suite_audit_rev2_run/`. No model or reader was called and no audit item was sent; the audit tests drive the reviewed reader `Job` through `ai_audit_exec.AuditJob` and the real chain admission with the fake CLI on synthetic images in temporary git repositories; the codex binary (the owned copy) ran only its local subcommands and the exec-invocation receipt with all network denied.

## Identity

- RSC HEAD `d2b42cd339a47e0cbc35707af44de36922cf1479`; photo directory status before the run: 0 lines.
- Main and build runs 2026-10-04T10:03:52Z to 10:49:47Z (UTC); controller rerun after it (times in the rerun_controller files).
- Audit package digest `2183a62f4b5cf114afc8c48a6d42aafba41c0f7fd66c7fd26322005669ef2c1a` (39 fields), equal to the package re-derived from d2b42cd. The reader revision-17 package recomputes equal to `AIREADER_GO.json`; Stage A and the supplement are untouched.

## Counts

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 1 | 420 | 43 | 1 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |
| rerun: `.venv-image/bin/python -m unittest stimuli.photo.tests.test_controller -v` | 0 | 55 | 0 | 0 | 0 |

Against the revision-1 run (aa19d4d: 401): the audit tests grew from 7 to 26, all passing in the main run; the 43 skips have the same causes.

## The one failure, disclosed

`test_controller.Controller.test_persistence_failure_is_bounded` (Stage A controller; neither the test nor `stage_a_controller.py` changed since 5f08728, whose retained runs passed it): the injected persistence failure was expected to be the first stop reason, but under the full suite's load a sampling iteration took 0.084 s against the controller's 0.05 s limit and the controller stopped first for that (`ControllerStop: instrumented: a sampling iteration took 0.084 s (limit 0.05 s)`) - a load-sensitive ordering in the fixture, not a change of this revision. The controller module rerun alone (55 tests, retained `rerun_controller.*`) passed it and every other controller test. The failure stays recorded; it is not erased by the rerun.

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `820cdb0bb5e4dae9555183c18d7d698c19738df1d8bdba7ab6de3cc8e6325763`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `ended.txt` 21 bytes `07b19d41e763fa6cb7b19eb152c2db372381c97325fcc158baa3811916b0043d`
- `head.txt` 41 bytes `7efc0cb9d68cdd7a5364c169d334e06229fa226ab29461e1d4c75bb2cb77c54f`
- `main.exit.txt` 2 bytes `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
- `main.stderr.txt` 69631 bytes `431f3bf9074bff192f0631ec6888174e559a9393a9cee67f95664283b0ff1001`
- `main.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `rerun_controller.ended.txt` 21 bytes `5a447215f8e363bf96bafe88dda92b19fa8957d0b55c5636cbe27bb550fece65`
- `rerun_controller.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `rerun_controller.started.txt` 21 bytes `f36d279f6bec8ebdf0323efa6557d2dfd41ff3ed133a1562a618a34f5cf6ece8`
- `rerun_controller.stderr.txt` 12702 bytes `a3acb9fcebda531797c51320266fd73f56e5e2edf45771720d38bffcfd604efd`
- `rerun_controller.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `started.txt` 21 bytes `530849782409dc7d2284f3fb83b7d85ddb7bc70fb0903016973831bd7a211a76`
- `status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

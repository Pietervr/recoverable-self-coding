# Photo test suite, revision 4: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-4 packages, with every byte of output kept in `2026-10-02_photo_suite_rev4_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `d7a486ae25e6952eb2ce15f7c89a2eb36abe1474`; photo directory clean before the run (`photo_status_before.txt`, 0 lines).
- Started 2026-10-02T10:33:37Z, ended 2026-10-02T10:46:49Z (UTC).
- Row-20 package: criteria_sha256 `a57ac515e6a37baf909e57c7e2ca693c752671a72f3be1d38631c2ea04260fc9`, identity_sha256 `d6a73a4e466e19a0250a9876297aa214d489cae62c7ac29db7831f662aa11ff8`, plan_sha256 `98eb2817df5a99c98fab29285cd002f95a3042fa6fa235146cf9719d922289d6`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `334ae9c9e5be55b0f8e6cdfc17d7d60463dc28da548239e0a59a2d2f390f8820`; inner identity `61dd0aa0c9a7b99b2a54f02be0d9f67b007b99754e3996a28fdc7bcd8fa4f81e`.
- AI-reader package digest `68ba57fe39a7e726f9f57cf236fc6c2a649d9d6fa979d09e393b30831c1519d4` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per module |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('167', '790.568')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 3, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Controller': 18, 'Finalisation': 6, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 9, 'Units': 10, 'ValidatorMutations': 16} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.654')] | [('OK', '')] | {'KeyFunctions': 5} |

## Skips

- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)

The fifth skip is `test_full_form_s1_prospectively` (its multi-line docstring hides it from the list above; 5 'needs WordNet' skips in the stderr). All five WordNet checks ran and passed under .venv-build (second row).

An earlier full run on RSC `859262f`, before the one-line reserved-write fix of `d7a486a`, gave the same counts (167 OK, 5 skipped; KeyFunctions 5 OK); its outputs are kept in `2026-10-02_photo_suite_rev4_run_859262f/`. The single unreproduced error of the revision-3 runs did not occur in either run.

## Failures and errors

- none

## Retained files (sha256)

- `build_keyfunctions.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_keyfunctions.stderr.txt` 734 bytes `e3ac0988454033a2da021e2a1535d0307b998a77b387610dcf9bd5d5b9c8146a`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `80c015749101c84ef1e76e12a72b6211907bf895203f76eaac74b5bd698abbd2`
- `head.txt` 41 bytes `f93466dd18cb4dccb386e6aecdcf7e5a8160f44dd786bb92c3fb210f6da79926`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 19244 bytes `647351643612addf321b44dac335b1d915851080886295b5d7afe6b080b4c119`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `b26c322fd35821676d8a20e113b12908d870186668e79d21339c805178075c54`

# Photo test suite, revision 9: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-9 packages, with every byte of output kept in `2026-10-02_photo_suite_rev9_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `ba4fc75dfa9f2621789c6129f71dc27638b2e760`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T19:24:58Z, ended 2026-10-02T19:57:09Z (UTC).
- Row-20 package: criteria_sha256 `6adb6d1d14311016930dc07f38e8ecd55d5399ac80324da3ff6c8c9e2178864d`, identity_sha256 `57f6e68a3733c9f82ffa171ba354681c2da572f1f47384981571576151ac6df9`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `5b6bc5bf72b7d14d7228f21f7349a5816cde07ff97c8e96562833be024c7fc4e`.
- AI-reader package digest `33eac04943cc004ecfba129c190c8c378b332f067971274d3b90be622f9de920` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('253', '1928.955')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 33, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.655')] | [('OK', '')] | {'KeyFunctions': 5} |

## Skips

- `test_full_form_s1_prospectively` (test_ai_reader.KeyFunctions.test_full_form_s1_prospectively): needs WordNet (run under .venv-build)
- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)

'needs WordNet' skips in the main stderr: 5. The WordNet checks run under .venv-build (second row).

## Failures and errors

- none

## Retained files (sha256)

- `build_keyfunctions.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_keyfunctions.stderr.txt` 734 bytes `1749b0afa3ee644e74b702ee7cbb7ccb509dfa402119719cb74c58ad28d36362`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `18ae460b44c8f21c1d6ee30d9f7a276853852a965323c7b16f7beb167fdd87e3`
- `head.txt` 41 bytes `73cb8e5e672e0499bccf187945850045cd4b924bba54be5073bb3919eb5049e6`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 36610 bytes `eb5f9f11b7fee9e9c41665939ce8737881dd55d1f138cbc3a48c9c7f4e8b61ce`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `318b362c466e2d2001f71fc225c165cab486731cb990c09d743813563886b6ac`

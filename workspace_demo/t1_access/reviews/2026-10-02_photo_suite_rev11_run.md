# Photo test suite, revision 11: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-11 packages, with every byte of output kept in `2026-10-02_photo_suite_rev11_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `308901c825ca2fcc28c716e22ff83973e68cb2b1`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T23:35:40Z, ended 2026-10-03T00:10:23Z (UTC).
- Row-20 package: criteria_sha256 `4279dc848c07fb24ad4e022ed99d2414b89f00c561545aa4b6f06e8ed37dcdac`, identity_sha256 `7abf9ee88cf5634524cd3ded9f3799eca98c576bbedb6c8efc19a02cc28f1827`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `fb4abaa10d5a34d7648df7f59e0b58676c2a695addd8af9a4de8fcb98ea8ad16`.
- AI-reader package digest `6be7d4c8fc6b113f4505af166386f8cf3df23446ccfe19df61114bb5d2e4b760` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('262', '2080.421')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev11': 4, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 37, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.660')] | [('OK', '')] | {'KeyFunctions': 5} |

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
- `build_keyfunctions.stderr.txt` 734 bytes `f6af48baacd9a593875be6ed70248d94d39bdbc3c8361dec0706ec683ef8a8f1`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `8fd7d9453bad016651385cf57e9f18818a8907b6274f1fdbc7f89dee4ad14c25`
- `head.txt` 41 bytes `842ce1691925ac473950a92fa0ba28d83c7a982c48f8ff357c31738a532a7b25`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 38744 bytes `07e74d59e8bbff14a386297d7ce9b8f2b1dd6b4dd99a9d70e7d4cea8f39fe2cf`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `f8801d8db5c6f14c913b180d99dd93ca33eed39bca767429b70a5dd77a1bb697`

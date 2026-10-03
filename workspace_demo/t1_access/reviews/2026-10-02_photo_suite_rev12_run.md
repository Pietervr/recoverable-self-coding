# Photo test suite, revision 12: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-12 Stage A package (reader unchanged), with every byte of output kept in `2026-10-02_photo_suite_rev12_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `620f76823a7d875aaa15d71244a59670ae33199c`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-03T00:44:25Z, ended 2026-10-03T01:19:02Z (UTC).
- Row-20 package: criteria_sha256 `4e80b9590461dccbada956e82a413dbd46832c885cbdf6dc33ad87b8439e0870`, identity_sha256 `1a01d070da0c18fa871a0e252c9a8c9d98df9df250be10300181fa8696569664`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `c0fb2ea0f6c5ef83cdabd414cb7d761ec3aabd9de13ed6022a852a7b590da001`.
- AI-reader package digest `6be7d4c8fc6b113f4505af166386f8cf3df23446ccfe19df61114bb5d2e4b760` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('269', '2075.122')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev11': 4, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 39, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'Rev12Transition': 5, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.659')] | [('OK', '')] | {'KeyFunctions': 5} |

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
- `build_keyfunctions.stderr.txt` 734 bytes `576368abed41715cc2db39f0056d3be334614ac3bf4eee4d34113d110e02aab9`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `7ca48b772544d97c0829684f1bd7984d09281b4fa538476241e67d4ec2e3db31`
- `head.txt` 41 bytes `261f1ca14f097baca9727b13f28e343a7640cba5c49f955bbc3d5bca808cf4d3`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 40252 bytes `2268be4f1a37b9542a06e60acfd26bba1ad998db35b0b7679cd4755b6387429b`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `0e9d5662e9cbe4a0dd0359cd254e80ca11a8bb1479344e0a0674f59b9ca9d7ed`

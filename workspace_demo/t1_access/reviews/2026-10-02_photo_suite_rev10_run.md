# Photo test suite, revision 10: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-10 packages, with every byte of output kept in `2026-10-02_photo_suite_rev10_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `fbfb7db4d08c7df3d0b44741af1fa9fcc1bca030`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T20:56:07Z, ended 2026-10-02T21:29:54Z (UTC).
- Row-20 package: criteria_sha256 `f05be7a80274226bfb90101fc676170ef610c336ca5fe8d1c87d9321bca1c3f7`, identity_sha256 `04678ddb2360238bc02c7bca850c2c2f1e4d8247e65bd5717b05461baadad158`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `e146ec63bc32973bb217de6066b57fe1c972bf8cf79a369b19d8efca617b2f38`.
- AI-reader package digest `ffba894e5a8c1ea9ed4d68f9287cbb75fc4e25e50e923dcd525a542d631a8ed8` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('255', '2024.525')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 34, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.663')] | [('OK', '')] | {'KeyFunctions': 5} |

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
- `build_keyfunctions.stderr.txt` 734 bytes `474cf9422c594d53990c83d2acbe09aa0a3a7cbcbd569d84d934ca2e7ac3a496`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `948d4f3ef96acc331a262c4c37752f37b7bb3a40561c805dd6e9ff5dc40c639c`
- `head.txt` 41 bytes `171fbd1053cdfce7d51ca90ba5175abdd917316e07bb615fe4043d39643fce60`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 37049 bytes `585f4652a65b06ab532cb6870920e7389e1e250f5ef58c9c73f88b82be567182`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `58dda95191c60cd00b0f6d106a0ef4302d8b26d5234f10a4e45f51e005619682`

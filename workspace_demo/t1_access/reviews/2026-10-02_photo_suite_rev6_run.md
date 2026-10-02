# Photo test suite, revision 6: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-6 packages, with every byte of output kept in `2026-10-02_photo_suite_rev6_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `bb4f07675bbc941bbb2dd9cb4c4762b82b42f9a8`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T13:40:22Z, ended 2026-10-02T14:02:43Z (UTC).
- Row-20 package: criteria_sha256 `677bfff3aa31041a2871bc73553578936d86e9022afd7ab638df2a35ddde2007`, identity_sha256 `c15a60f62334549adc93e4dfc953095937ae287f6354d17d8eec0ebd347093a2`, plan_sha256 `40aba7ecf4a4cc6cdb5b0a5d536e87f31b4945f6c98a94c0458808050342c74c`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `914fa4156368a2278357bb870786dd568a09823c202b9bd9ea880f1fada80a5d`; inner identity `ec14571c74b19cb9fabab731a02136c70d1167b94bdf332e301ecbeacf6c7ead`.
- AI-reader package digest `68012501998ae14dd9cd24ce1edc593b8ccb725ac6d4fb7b4a204820ba5fbc05` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('221', '1338.445')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev5Recovery': 4, 'Rev6': 3, 'Controller': 23, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 20} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.644')] | [('OK', '')] | {'KeyFunctions': 5} |

## Skips

- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)

'needs WordNet' skips in the main stderr: 5. The WordNet checks run under .venv-build (second row).

## Failures and errors

- none

## Retained files (sha256)

- `build_keyfunctions.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_keyfunctions.stderr.txt` 734 bytes `c23e70096f2dc5c36b6a92736620d7b606cfe39280ec2d24d88339a537954b66`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `128dee781cfdde9e265c590bba7862cb6eed5b4a7fbe9e62768d65413688a4d0`
- `head.txt` 41 bytes `76a1753b58b44c9e7e6acffb2d9f59954486fe2514209f0aa784df7ff1591f75`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 29211 bytes `95478bd4d14bae33147dddc6274515566c953ed5512bdf1231bc63ff60c2d0b1`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `6fde9e42667b03058c54b57f11029768c175464cbd9fb910b3495a77bb29a308`

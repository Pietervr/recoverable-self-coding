# Photo test suite, revision 5: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-5 packages, with every byte of output kept in `2026-10-02_photo_suite_rev5_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `2610d8a66d36d170c26691158f1dbfd1e280e9e9`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T12:24:22Z, ended 2026-10-02T12:44:24Z (UTC).
- Row-20 package: criteria_sha256 `cf547d69a05f687f0e2b9060f60887c7fc864561ca062bf6bab197d7f6fde6ce`, identity_sha256 `55f0384411bcb2162a9306a36bd977cd4d53e3acb3b6522b66b48f1e8bd72913`, plan_sha256 `40aba7ecf4a4cc6cdb5b0a5d536e87f31b4945f6c98a94c0458808050342c74c`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `914fa4156368a2278357bb870786dd568a09823c202b9bd9ea880f1fada80a5d`; inner identity `691f8d21270bb34612671a929bb3b37ed0830d1952499d5dfceb7cd7fd476db1`.
- AI-reader package digest `65baf75f29b151c99276f16169e679007f90ed84aa73fe01716f9a55ba85b8b3` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('209', '1200.167')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev5Recovery': 4, 'Controller': 21, 'Finalisation': 11, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 19} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.661')] | [('OK', '')] | {'KeyFunctions': 5} |

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
- `build_keyfunctions.stderr.txt` 734 bytes `6cbcaf0fdedc961d8f5ca4964d3abf2a338f10e79158a9141ac174b689271e7d`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `65a5b7d745faaa6670603c243a0c51338f26045fac40d65abe0d2cef76808194`
- `head.txt` 41 bytes `d36d247f013c1976e7494cc47bcfcdd14897f2bfca7f60dded145a498596a361`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 25686 bytes `d2fa9450f58aea747195270f54c471a36a5e58891e5be1077191a4bd74a4f4dc`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `8a565b26cde7554deab544c7904452197bcb7764f652ab557bc1860b682ab842`

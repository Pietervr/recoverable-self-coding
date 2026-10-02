# Photo test suite, revision 8: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-8 packages, with every byte of output kept in `2026-10-02_photo_suite_rev8_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `9f696c653f55df3409437d77836e5b7f74efdba1`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T17:49:03Z, ended 2026-10-02T18:20:42Z (UTC).
- Row-20 package: criteria_sha256 `a17bdbbfc5a42d0ee7e52518029a79440f7594734867435a42a87bafc4b6077f`, identity_sha256 `86320c18ee5e5ea27bfba4016ecea0d46a372ee7bc7bcce507eb4798dc2d2807`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `1c7beaa2c5c396ac9001fd40e85ed3cf912fbf3dd94a3b4884739d489926bdd3`.
- AI-reader package digest `9b7aecf96464b6f87689db4e77bb83521cfa9fb04d3174ddcb96f8cd2f493097` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('247', '1897.130')] | [('OK', 'skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev5Recovery': 4, 'Rev6': 3, 'Controller': 31, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.672')] | [('OK', '')] | {'KeyFunctions': 5} |

## Skips

- `test_full_form_s1_prospectively` (test_ai_reader.KeyFunctions.test_full_form_s1_prospectively): needs WordNet (run under .venv-build)
- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)

'needs WordNet' skips in the main stderr: 5. The WordNet checks run under .venv-build (second row).

## Failures and errors

- none

## Observed before the commit (not in this run)

While building revision 8, two failures appeared in unretained runs (wording corrected at revision 9, Codex
`7fdb937`): ONE IDENTIFIED observation - in a multi-class crash-module run,
`test_ai_reader_crash.Rev7.test_post_rename_clock_failure_and_stall_do_not_qualify` [error] saw a STOPPED receipt
where COMPLETE is expected, its reason not printed - and ONE UNIDENTIFIED crash-module failure in a 200-test
multi-module run whose summary was truncated. They are not known to be the same event. The identified test passed in
8 isolated repetitions of its run, in two later crash-class runs, a 32-test crash-module run and this retained run
(source-reported repetitions, not retained evidence of the original failure). Its assertion now prints the receipt's
reason and the driver's stderr. Unresolved; the cause is not known.

## Retained files (sha256)

- `build_keyfunctions.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_keyfunctions.stderr.txt` 734 bytes `267c150f59475ca7c3ea7bdd7061ec754d502a0b75a79ebd76af2e30c1261ad2`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `29aedb5eed51d83cc93ec580d63c0d6c96d34f2bdf6a67843d95f925b600d351`
- `head.txt` 41 bytes `51016aa4a4204e274a746505c1658a2bbcda4247b01620eae3481dbb54574494`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 35134 bytes `41d8da97000549400dde15144ec747d69d17e8b6981e20375557a809850e7124`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `0db5ee977f169af69363c9a2902b523419f760539d3fc31c1c9ae6b52d9b1bf0`

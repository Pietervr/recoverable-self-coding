# Photo test suite, revision 12: retained-output run

R084, 3 October 2026. The whole photo test suite on the exact committed reader revision-12 package (Stage A's revision-12 package unchanged), with every byte of output kept in `2026-10-03_photo_suite_reader_rev12_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `0f4cffe5ad94d762cbaa7c74fafd3f15fd1ed5b2`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-03T04:28:31Z, ended 2026-10-03T05:05:08Z (UTC).
- Row-20 package: criteria_sha256 `4e80b9590461dccbada956e82a413dbd46832c885cbdf6dc33ad87b8439e0870`, identity_sha256 `1a01d070da0c18fa871a0e252c9a8c9d98df9df250be10300181fa8696569664`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `c0fb2ea0f6c5ef83cdabd414cb7d761ec3aabd9de13ed6022a852a7b590da001`.
- AI-reader package digest `3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('279', '2190.457')] | [('OK', 'skipped=16')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev11': 4, 'Rev12': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 39, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'Rev12Transition': 5, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | [('27', '3.824')] | [('OK', '')] | {'KeyFunctions': 5, 'Rev12': 10, 'Scoring': 4, 'AuditMap': 4, 'ScorerAdmission': 4} |

## Skips

- `test_full_form_s1_prospectively` (test_ai_reader.KeyFunctions.test_full_form_s1_prospectively): needs WordNet (run under .venv-build)
- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)
- `test_audit_map_rebuild_unchanged` (test_ai_reader.Rev12.test_audit_map_rebuild_unchanged): needs WordNet (run under .venv-build)
- `test_audit_scorer_same_rule_own_entry_point` (test_ai_reader.Rev12.test_audit_scorer_same_rule_own_entry_point): needs WordNet (run under .venv-build)
- `test_every_excluded_form_still_fails` (test_ai_reader.Rev12.test_every_excluded_form_still_fails): needs WordNet (run under .venv-build)
- `test_format_still_first` (test_ai_reader.Rev12.test_format_still_first): needs WordNet (run under .venv-build)
- `test_named_cases` (test_ai_reader.Rev12.test_named_cases): needs WordNet (run under .venv-build)
- `test_one_function_in_both_scorers` (test_ai_reader.Rev12.test_one_function_in_both_scorers): needs WordNet (run under .venv-build)
- `test_prompt_is_the_owners` (test_ai_reader.Rev12.test_prompt_is_the_owners): needs WordNet (run under .venv-build)
- `test_singularising_an_admitted_form_never_reaches_an_excluded_one` (test_ai_reader.Rev12.test_singularising_an_admitted_form_never_reaches_an_excluded_one): needs WordNet (run under .venv-build)
- `test_the_fourteen_easy_misses_of_job_a` (test_ai_reader.Rev12.test_the_fourteen_easy_misses_of_job_a): needs WordNet (run under .venv-build)
- `test_wordnet_pin_checked` (test_ai_reader.Rev12.test_wordnet_pin_checked): needs WordNet (run under .venv-build)
- `test_referrals_carry_identity` (test_ai_reader.ScorerAdmission.test_referrals_carry_identity): needs WordNet (run under .venv-build): a non-matching answer reaches the shared matching rule's WordNet steps (stderr line 120; double-quoted there, so the record's parser missed it - added by hand)

'needs WordNet' skips in the main stderr: 16 (all 16 of the run's skips). The WordNet checks - KeyFunctions, the revision-12 matching rule (Rev12), and the scorer classes whose non-matching answers reach WordNet (Scoring, AuditMap, ScorerAdmission) - run under .venv-build (second row).

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `fbc97dfad10e71f92f72aed38c9680fa5a5c064d2a6a39bcebb61003319746fd`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `30889cbd9437c24eb132dc4f82bbf3a920b4273b2c221c645a033477ef987aec`
- `head.txt` 41 bytes `c6a84b60181d2d0bec73002d681b8556dfffd8008a2aed2eda7a9ebe539d0dd0`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 42121 bytes `b6143c667ce46a224c2bd78f66b0615f3f21039bb910e8b49f3a35a02bb30066`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `f176b086569b638eefa9536960fd67f494934638a835dc66710529cfd3d7e388`

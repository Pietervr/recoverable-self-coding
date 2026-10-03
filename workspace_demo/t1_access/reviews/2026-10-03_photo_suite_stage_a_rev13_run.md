# Photo test suite, Stage A revision 13: retained-output run

R084, 3 October 2026. The whole photo test suite on the exact committed Stage A revision-13 package (the reader revision-12 package unchanged), with every byte of output kept in `2026-10-03_photo_suite_stage_a_rev13_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `22047ec71f8200ca7c12a9234269aa58f1306224`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-03T05:18:04Z, ended 2026-10-03T05:53:44Z (UTC).
- Row-20 package: criteria_sha256 `63be1b381c254de7d3e813496767d59e2ae630df32d725fb6c4377245b828cdd`, identity_sha256 `96fbd94b88f9247b7705a32cd385fcc9b8df826e19acce4c73d65532b005a2da`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `2bac56e30e43ad62fe70ed01b8cf0562181029939e9778374de21c3bdce358f8`.
- AI-reader package digest `3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('293', '2134.134')] | [('OK', 'skipped=21')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev11': 4, 'Rev12': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 39, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'Rev12Transition': 5, 'Rev13Parity': 4, 'Rev13Transition': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | [('27', '3.521')] | [('OK', '')] | {'KeyFunctions': 5, 'Rev12': 10, 'Scoring': 4, 'AuditMap': 4, 'ScorerAdmission': 4} |

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
- `test_referrals_carry_identity` (test_ai_reader.ScorerAdmission.test_referrals_carry_identity): needs WordNet (run under .venv-build): a non-matching answer reaches the shared matching rule's WordNet steps
- `test_changed_frozen_inputs_refuse` (test_stage_a_runner.Rev12Transition.test_changed_frozen_inputs_refuse): the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION.json); the chained transition is PRODUCED by Rev13Transition
- `test_no_release_no_transition` (test_stage_a_runner.Rev12Transition.test_no_release_no_transition): the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION.json); the chained transition is PRODUCED by Rev13Transition
- `test_relabelled_phase_record_refuses` (test_stage_a_runner.Rev12Transition.test_relabelled_phase_record_refuses): the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION.json); the chained transition is PRODUCED by Rev13Transition
- `test_resume_admits_the_predecessor_phase_with_counters_carried` (test_stage_a_runner.Rev12Transition.test_resume_admits_the_predecessor_phase_with_counters_carried): the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION.json); the chained transition is PRODUCED by Rev13Transition
- `test_undeclared_predecessor_refuses` (test_stage_a_runner.Rev12Transition.test_undeclared_predecessor_refuses): the 2 October ledger was moved by the 3 October resume's transition (IDENTITY_TRANSITION.json); the chained transition is PRODUCED by Rev13Transition

'needs WordNet' skips in the main stderr: 16. The WordNet checks - KeyFunctions, the revision-12 matching rule (Rev12), and the scorer classes whose non-matching answers reach WordNet (Scoring, AuditMap, ScorerAdmission) - run under .venv-build (second row).

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `b70c13a3fac1449998df41ad7e1b6e2f2c7e039dd0b594286b18e11d4df34786`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `c21636d9309bf3239ad735b998cdb4168f7bb25b159e4719aa0b454f9e023faa`
- `head.txt` 41 bytes `2538519ca51c5fef36c5474c57da3ba56d20cbc122f14227e215aa4306e96d98`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 44657 bytes `25b869d1214a7263d8c3222e9efb1b48b03d8399950b02f16b3b538aed7f1616`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `568b0eda28725084699f106d49a172fefdb5d5518ce97c8a8897b376b8c2e93f`

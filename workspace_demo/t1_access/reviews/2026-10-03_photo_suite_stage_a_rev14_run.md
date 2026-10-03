# Photo test suite, Stage A revision 14: retained-output run

R084, 3 October 2026. The whole photo test suite on the exact committed Stage A revision-14 package (the reader revision-12 package unchanged), with every byte of output kept in `2026-10-03_photo_suite_stage_a_rev14_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `c22cd323bf5262d59488b70a9433e13cfef3fa9c`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-03T06:15:31Z, ended 2026-10-03T06:49:32Z (UTC).
- Row-20 package: criteria_sha256 `5a4ea075e2cddf068917890b75488c22a80bc2cc4c838078e9d3ada29e9b2be8`, identity_sha256 `85b78de4a5951977ab271c0030bb1127a41d11df4c4babfef21c5eac78ee676b`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `3d6d991dc093ee373a4d4ee4acc21d7a72dc062af05b144de77aadea0600400c`.
- AI-reader package digest `3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11` (24 fields).

## Commands, exit status, counts

Collected: 299 (main) + 27 (build). Distinct cases exercised: 294. Passing executions: 305. Skips in the main run: 21 = 16 needing WordNet, run and passed in the build row + 5 not rerun (listed below). The build row's 27 include 11 repeats of main-run cases. Failures or errors: 0.

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | [('299', '2035.658')] | [('OK', 'skipped=21')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev11': 4, 'Rev12': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'Rev8': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev10': 1, 'Rev5Recovery': 4, 'Rev6': 3, 'Rev9': 4, 'Controller': 39, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'Rev12Transition': 5, 'Rev13Parity': 5, 'Rev13Transition': 10, 'Rev14PreparedLink': 5, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | [('27', '3.542')] | [('OK', '')] | {'KeyFunctions': 5, 'Rev12': 10, 'Scoring': 4, 'AuditMap': 4, 'ScorerAdmission': 4} |

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
- `build_wordnet.stderr.txt` 3842 bytes `4b47c4101ffcd1d62b8ad3339b2c4730e96d8382ae2087ffbf037958a6467889`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `0072e4617955d77becd3ce0507fe6f8c07a9f586d5f6c8afa6f0ed44aa624b15`
- `head.txt` 41 bytes `b6b0e16ffe0129268e04210647f5ce9334eaf9eac731b257fdd645c7626e8609`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 45688 bytes `734e7f549ad947a3e981fa1d35ea2975508eafbc35976d3daef99e0b2b21a2a7`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `8cce727731ed719e62d21fadb4c7925f28d3358ce25c989f1b0e16917440edd3`

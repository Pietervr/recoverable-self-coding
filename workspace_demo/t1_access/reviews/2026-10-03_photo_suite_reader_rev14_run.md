# Photo test suite, reader revision 14: retained-output run

R084, 3 October 2026. The whole photo test suite on the committed reader revision-14 package (Stage A revision 15
unchanged), every byte of output kept in `2026-10-03_photo_suite_reader_rev14_run/`. No model was called and no image was shown to any model; the
codex binary - now the project-owned copy captures/reader_cli/codex-0.160.0 - ran only its local subcommands and the
exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `1d325dc9dd786e639179530f8043d8d1c10f0320`; photo directory status before the run: 0 lines.
- Started 2026-10-03T19:55:22Z, ended 2026-10-03T20:30:07Z (UTC).
- Stage A package (`stage_a_package.json`): {"criteria_sha256": "34e503f293c0d315bfb3e9c88bf11dc561f7f26d1ce3122a56d886fd76e27388", "identity_sha256": "064195e563b62a8640dc80468e04fff59a8d03e04ec53f704d4496255c1b5fdb", "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc", "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448", "budget_sha256": "9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"}

## Counts

Collected: 317 (main) + 27 (build). Distinct cases exercised: 290. Passing executions: 301. Skips in the main run: 43 = 16 run in the build row + 27 not rerun. Build-row repeats of main-run cases: 11. Failures 0, errors 0.

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | 317 | 43 | 0 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |

## Skips by cause (main run)

- 16 x 'needs WordNet': test_ai_reader.KeyFunctions.test_full_form_s1_prospectively, test_ai_reader.KeyFunctions.test_inflections, test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key, test_ai_reader.KeyFunctions.test_specificity_rules, test_ai_reader.KeyFunctions.test_synonym_residue, test_ai_reader.Rev12.test_audit_map_rebuild_unchanged, test_ai_reader.Rev12.test_audit_scorer_same_rule_own_entry_point, test_ai_reader.Rev12.test_every_excluded_form_still_fails, test_ai_reader.Rev12.test_format_still_first, test_ai_reader.Rev12.test_named_cases, test_ai_reader.Rev12.test_one_function_in_both_scorers, test_ai_reader.Rev12.test_prompt_is_the_owners, test_ai_reader.Rev12.test_singularising_an_admitted_form_never_reaches_an_excluded_one, test_ai_reader.Rev12.test_the_fourteen_easy_misses_of_job_a, test_ai_reader.Rev12.test_wordnet_pin_checked, test_ai_reader.ScorerAdmission.test_referrals_carry_identity
- 5 x 'the 2 October ledger was moved by the 3 October resume's transition': test_stage_a_runner.Rev12Transition.test_changed_frozen_inputs_refuse, test_stage_a_runner.Rev12Transition.test_no_release_no_transition, test_stage_a_runner.Rev12Transition.test_relabelled_phase_record_refuses, test_stage_a_runner.Rev12Transition.test_resume_admits_the_predecessor_phase_with_counters_carried, test_stage_a_runner.Rev12Transition.test_undeclared_predecessor_refuses
- 22 x 'the live ledger moved past the 3 October pre-resume state': test_stage_a_runner.Rev13Transition.test_broken_chain_admits_nothing, test_stage_a_runner.Rev13Transition.test_changed_frozen_inputs_refuse, test_stage_a_runner.Rev13Transition.test_ledger_not_where_the_chain_ends_refuses, test_stage_a_runner.Rev13Transition.test_no_release_no_transition, test_stage_a_runner.Rev13Transition.test_relabelled_phase_record_refuses, test_stage_a_runner.Rev13Transition.test_resume_admits_both_predecessors_with_counters_carried, test_stage_a_runner.Rev13Transition.test_retained_resume_records_match_the_live_ones, test_stage_a_runner.Rev13Transition.test_the_2_october_release_does_not_release_the_3_october_record, test_stage_a_runner.Rev13Transition.test_the_real_records_are_the_3_october_state, test_stage_a_runner.Rev13Transition.test_undeclared_predecessor_refuses, test_stage_a_runner.Rev14PreparedLink.test_fault_between_the_writes_then_retry_reconciles, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_under_an_invalidated_release_refuses_then_a_new_release_reconciles, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_whose_counters_or_ids_differ_refuses, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_whose_endpoints_differ_refuses, test_stage_a_runner.Rev14PreparedLink.test_repeat_of_the_reconciled_state_writes_nothing, test_stage_a_runner.Rev15Environment.test_a_predecessor_os_other_than_the_declared_one_refuses, test_stage_a_runner.Rev15Environment.test_a_prepared_tail_for_another_os_pair_refuses, test_stage_a_runner.Rev15Environment.test_another_current_os_refuses, test_stage_a_runner.Rev15Environment.test_another_frozen_field_changed_with_it_refuses, test_stage_a_runner.Rev15Environment.test_report_states_the_mixed_provenance, test_stage_a_runner.Rev15Environment.test_the_declared_pair_is_admitted_and_recorded, test_stage_a_runner.Rev15Environment.test_the_revision_10_predecessor_declares_no_difference

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `e38d332f288a3764ee327bdbfd8d8f7d823ce87c550702ab818b21566e42b1f8`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `codex_version.txt` 18 bytes `f6464b8cc67af75deb2589fe1dbcde152fc15ffb76a91de1cf0686b4623afb1e`
- `end_utc.txt` 21 bytes `b0ea7161d18ae00d5ea2d75680c5b889c90403081acd8a474685af2ddfdf9e50`
- `head.txt` 41 bytes `300c9942d88d80bf594b257a61316e030ba2574256bfecbfe23a2fcb08eaa7b7`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 54565 bytes `3e6d66a4976653b0121200d19a87c2c5f3946b1ed7f693970e99a9d1e47bfc25`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `stage_a_package.json` 437 bytes `98ab5a9790be053b51c4f6e16c33b6e0b955c111894fb2a9c14cab7b1cc4515d`
- `start_utc.txt` 21 bytes `ace13434315001b3e7d424d1883290657b87edcf7469707925813bf9a1338a86`

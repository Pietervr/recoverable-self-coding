# Photo test suite, Stage A supplement revision 4 (reader revision 17 unchanged): retained-output run

R084, 4 October 2026. The whole photo test suite on the committed Stage A supplement package revision 4 (RSC 280604d) beside AI
reader revision 17 (RSC 977655f, unchanged; job (c) completed), every byte of output kept in `2026-10-04_photo_suite_supplement_rev4_run/`. No model was called, no forward ran and no image was shown to
any model; the supplement fixtures use the fake instrument on a fake Stage A run in temporary trees; the codex binary
- the project-owned copy captures/reader_cli/codex-0.160.0 - ran only its local subcommands and the exec-invocation
receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `c8db93483dfc97fc7528ce7f0cbe82366c1dae5a`; photo directory status before the run: 0 lines.
- Started 2026-10-04T03:18:56Z, ended 2026-10-04T04:05:12Z (UTC).
- Stage A package (`stage_a_package.json`, as `stage_a.py package` prints it from the live files; its identity file is
  revision 15's record): {"criteria_sha256": "34e503f293c0d315bfb3e9c88bf11dc561f7f26d1ce3122a56d886fd76e27388", "identity_sha256": "064195e563b62a8640dc80468e04fff59a8d03e04ec53f704d4496255c1b5fdb", "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc", "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448", "budget_sha256": "9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"}
- Supplement package (`supplement_package.json`): {"supplement_criteria_sha256": "de85d58a0bbaf3c7c05374473a58a77cc705eb24aede0ed7f95b75774087ab45", "supplement_identity_sha256": "30aba1bae4166197f78e6120b3ef431874d0b840df09113071ab809bd00e6edc", "supplement_plan_sha256": "8e41084050c3a24d684b04a359d36c94714a38c5ec15eec8925c9c34b63eeace", "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc", "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448", "budget_sha256": "186e7738ccb5179e7212178de5c2342440fd5a471c3bb318e35cb7144bad8799"}

## Counts

Collected: 380 (main) + 27 (build). Distinct cases exercised: 353. Passing executions: 363. Skips in the main run: 43 = 16 run in the build row + 27 not rerun. Build-row repeats of main-run cases: 11. Failures 1, errors 0.

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 1 | 380 | 43 | 1 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |

## Skips by cause (main run)

- 16 x 'needs WordNet': test_ai_reader.KeyFunctions.test_full_form_s1_prospectively, test_ai_reader.KeyFunctions.test_inflections, test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key, test_ai_reader.KeyFunctions.test_specificity_rules, test_ai_reader.KeyFunctions.test_synonym_residue, test_ai_reader.Rev12.test_audit_map_rebuild_unchanged, test_ai_reader.Rev12.test_audit_scorer_same_rule_own_entry_point, test_ai_reader.Rev12.test_every_excluded_form_still_fails, test_ai_reader.Rev12.test_format_still_first, test_ai_reader.Rev12.test_named_cases, test_ai_reader.Rev12.test_one_function_in_both_scorers, test_ai_reader.Rev12.test_prompt_is_the_owners, test_ai_reader.Rev12.test_singularising_an_admitted_form_never_reaches_an_excluded_one, test_ai_reader.Rev12.test_the_fourteen_easy_misses_of_job_a, test_ai_reader.Rev12.test_wordnet_pin_checked, test_ai_reader.ScorerAdmission.test_referrals_carry_identity
- 5 x 'the 2 October ledger was moved by the 3 October resume's transition': test_stage_a_runner.Rev12Transition.test_changed_frozen_inputs_refuse, test_stage_a_runner.Rev12Transition.test_no_release_no_transition, test_stage_a_runner.Rev12Transition.test_relabelled_phase_record_refuses, test_stage_a_runner.Rev12Transition.test_resume_admits_the_predecessor_phase_with_counters_carried, test_stage_a_runner.Rev12Transition.test_undeclared_predecessor_refuses
- 22 x 'the live ledger moved past the 3 October pre-resume state': test_stage_a_runner.Rev13Transition.test_broken_chain_admits_nothing, test_stage_a_runner.Rev13Transition.test_changed_frozen_inputs_refuse, test_stage_a_runner.Rev13Transition.test_ledger_not_where_the_chain_ends_refuses, test_stage_a_runner.Rev13Transition.test_no_release_no_transition, test_stage_a_runner.Rev13Transition.test_relabelled_phase_record_refuses, test_stage_a_runner.Rev13Transition.test_resume_admits_both_predecessors_with_counters_carried, test_stage_a_runner.Rev13Transition.test_retained_resume_records_match_the_live_ones, test_stage_a_runner.Rev13Transition.test_the_2_october_release_does_not_release_the_3_october_record, test_stage_a_runner.Rev13Transition.test_the_real_records_are_the_3_october_state, test_stage_a_runner.Rev13Transition.test_undeclared_predecessor_refuses, test_stage_a_runner.Rev14PreparedLink.test_fault_between_the_writes_then_retry_reconciles, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_under_an_invalidated_release_refuses_then_a_new_release_reconciles, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_whose_counters_or_ids_differ_refuses, test_stage_a_runner.Rev14PreparedLink.test_prepared_tail_whose_endpoints_differ_refuses, test_stage_a_runner.Rev14PreparedLink.test_repeat_of_the_reconciled_state_writes_nothing, test_stage_a_runner.Rev15Environment.test_a_predecessor_os_other_than_the_declared_one_refuses, test_stage_a_runner.Rev15Environment.test_a_prepared_tail_for_another_os_pair_refuses, test_stage_a_runner.Rev15Environment.test_another_current_os_refuses, test_stage_a_runner.Rev15Environment.test_another_frozen_field_changed_with_it_refuses, test_stage_a_runner.Rev15Environment.test_report_states_the_mixed_provenance, test_stage_a_runner.Rev15Environment.test_the_declared_pair_is_admitted_and_recorded, test_stage_a_runner.Rev15Environment.test_the_revision_10_predecessor_declares_no_difference

## Failures and errors

- test_ai_reader.Rev13Reader.test_the_evidence_is_job_b_s: FAIL

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `3d71cd8e5c8748186b874b87ddac2df89eacf5430702de4ec827dc2b9edd89cb`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `codex_version.txt` 18 bytes `f6464b8cc67af75deb2589fe1dbcde152fc15ffb76a91de1cf0686b4623afb1e`
- `end_utc.txt` 21 bytes `755f6fa2fb85f1dc90aad03c406c0b81f101783a48fac1e985fa4a0a9341f85e`
- `head.txt` 41 bytes `3e3b950b90a641144593fa2c35bccc3ea61be7cbc03fd53df1f8c6e398f625d2`
- `image_suite.exit.txt` 2 bytes `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
- `image_suite.stderr.txt` 64390 bytes `af0c967df340714aa44f3eb0f62fb2a15e606128fe29a067e4629ce7aec2c6ca`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `reader_package.json` 2384 bytes `ebd6aa0a507f1d3bfb8770e729a4a9e975255bfc200f4e61f94ba08f5e92a035`
- `stage_a_package.json` 437 bytes `98ab5a9790be053b51c4f6e16c33b6e0b955c111894fb2a9c14cab7b1cc4515d`
- `start_utc.txt` 21 bytes `dfa8568770ac77badee41d05f836ac25e15ccec863911011cca9352f35efece3`
- `supplement_package.json` 554 bytes `cfaa2d5f2c4ec7145ace9040ed94db46cd8f566aea99083325649811f84c4bdf`

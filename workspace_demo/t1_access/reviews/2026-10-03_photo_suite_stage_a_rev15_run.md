# Photo test suite, Stage A revision 15: retained-output run

R084, 3 October 2026. The whole photo test suite on the committed Stage A revision-15 package, every byte of output
kept in `2026-10-03_photo_suite_stage_a_rev15_run/`. No model was called and no image was shown to any model. **The reader's pinned Codex CLI 0.159.3
no longer exists on this machine** (the cask was upgraded to 0.160.0 at 16:58 UTC, `codex_version.txt`): the reader
tests that need the real pinned binary skip or fail for that reason, listed below by cause; the Stage A classes do not
use it. The reader package (24 fields, 3e2bcdcc) cannot be recomputed here for the same reason; no reader-bound file
was changed by revision 15.

## Identity

- RSC HEAD: `e5439846bbc7536a892c6f5e618a34392cda9d32`; photo directory status before the run: 0 lines.
- Started 2026-10-03T17:00:13Z, ended 2026-10-03T17:35:47Z (UTC).
- Stage A package (`stage_a_package.json`): {"criteria_sha256": "34e503f293c0d315bfb3e9c88bf11dc561f7f26d1ce3122a56d886fd76e27388", "identity_sha256": "064195e563b62a8640dc80468e04fff59a8d03e04ec53f704d4496255c1b5fdb", "plan_sha256": "3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc", "manifest_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448", "budget_sha256": "9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f"}

## Counts

Collected: 306 (main) + 27 (build). Distinct cases exercised: 295. Passing executions: 306. Skips in the main run: 27 = 16 run in the build row + 11 not rerun. Build-row repeats of main-run cases: 11. Failures 0, errors 0.

| Command | Exit | Ran | Skipped | Failures | Errors |
|---|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 0 | 306 | 27 | 0 | 0 |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions stimuli.photo.tests.test_ai_reader.Rev12 stimuli.photo.tests.test_ai_reader.Scoring stimuli.photo.tests.test_ai_reader.AuditMap stimuli.photo.tests.test_ai_reader.ScorerAdmission -v` | 0 | 27 | 0 | 0 | 0 |

## Skips by cause (main run)

- 2 x 'needs the delivery receipt and the codex binary': test_ai_reader.Approval.test_modified_dependency_moves_the_package, test_ai_reader.Approval.test_reviewed_commit_rederivation
- 4 x 'needs the codex binary': test_ai_reader.Boundary.test_allowlist_real_binary, test_ai_reader.Boundary.test_effective_features_and_receipts, test_ai_reader.Boundary.test_exec_invocation_receipt, test_ai_reader.Boundary.test_prompt_separator_regression
- 16 x 'needs WordNet': test_ai_reader.KeyFunctions.test_full_form_s1_prospectively, test_ai_reader.KeyFunctions.test_inflections, test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key, test_ai_reader.KeyFunctions.test_specificity_rules, test_ai_reader.KeyFunctions.test_synonym_residue, test_ai_reader.Rev12.test_audit_map_rebuild_unchanged, test_ai_reader.Rev12.test_audit_scorer_same_rule_own_entry_point, test_ai_reader.Rev12.test_every_excluded_form_still_fails, test_ai_reader.Rev12.test_format_still_first, test_ai_reader.Rev12.test_named_cases, test_ai_reader.Rev12.test_one_function_in_both_scorers, test_ai_reader.Rev12.test_prompt_is_the_owners, test_ai_reader.Rev12.test_singularising_an_admitted_form_never_reaches_an_excluded_one, test_ai_reader.Rev12.test_the_fourteen_easy_misses_of_job_a, test_ai_reader.Rev12.test_wordnet_pin_checked, test_ai_reader.ScorerAdmission.test_referrals_carry_identity
- 5 x 'the 2 October ledger was moved by the 3 October resume's transition': test_stage_a_runner.Rev12Transition.test_changed_frozen_inputs_refuse, test_stage_a_runner.Rev12Transition.test_no_release_no_transition, test_stage_a_runner.Rev12Transition.test_relabelled_phase_record_refuses, test_stage_a_runner.Rev12Transition.test_resume_admits_the_predecessor_phase_with_counters_carried, test_stage_a_runner.Rev12Transition.test_undeclared_predecessor_refuses

## Failures and errors

- none

## Retained files (sha256)

- `build_wordnet.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_wordnet.stderr.txt` 3842 bytes `574c5bb1e4e9fa3f8503a0188189e4d96020b9a7a1de88a90d49454a5b18b420`
- `build_wordnet.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `codex_version.txt` 18 bytes `f6464b8cc67af75deb2589fe1dbcde152fc15ffb76a91de1cf0686b4623afb1e`
- `end_utc.txt` 21 bytes `f7e3677424ba5440d98befff4a62091d7b2034e6c1941c7cdbc82a1da0451fed`
- `head.txt` 41 bytes `1e808507c54625026c3e8a899dcd89ca29a74167aa08a960ff796907f06b07f5`
- `image_suite.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `image_suite.stderr.txt` 46939 bytes `b29ff2ddc9bc5ff66a298dbf95a96ad4f0e448a650c63d0c398f59aca5723f89`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `stage_a_package.json` 437 bytes `98ab5a9790be053b51c4f6e16c33b6e0b955c111894fb2a9c14cab7b1cc4515d`
- `start_utc.txt` 21 bytes `8c6f26761af01f60e583f007f5b3770255fe5b6dfd11e96490157181723febeb`

# Photo test suite, revision 7: retained-output run

R084, 2 October 2026. The whole photo test suite on the exact committed revision-7 packages, with every byte of output kept in `2026-10-02_photo_suite_rev7_run/`. No model was called and no image was shown to any model; the codex binary ran only its local subcommands (`--version`, `features list`, `login status`, `debug prompt-input`) and the exec-invocation receipt with all network denied by the kernel sandbox and a synthetic 8x8 image.

## Identity

- RSC HEAD: `068fe300c1972b89a25967914c848a00513d1d23`; photo directory status before the run (`photo_status_before.txt`): 0 lines.
- Started 2026-10-02T15:15:29Z, ended 2026-10-02T15:41:01Z (UTC).
- Row-20 package: criteria_sha256 `ede8f10f0565acf788378f804e9ce2df3c41fc41529fd2d3b64dd361a57cc1e0`, identity_sha256 `3dcda1b3381bef74809e4d98895555d59fb0c1bcc9b9f229cb55f14f469af320`, plan_sha256 `3faebf4eab25081cf32652bf025fa8fab9d11bee6f1c9a19a1cf2dbad45417cc`, manifest_sha256 `e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448`, budget_sha256 `9e9eb4dcc8dca396af86ee982b17d1e957e9668b12bda0fd803deb126805c07f`; inner identity `6da552d7a9e4a6f74767be2a2b8dcceb8f43d3f1edf5a74906e9f7881f3101c6`.
- AI-reader package digest `f4b7c665a2add27cd75c9aec065c23f3b416f8b14ceb41160b427ca5504321aa` (24 fields).

## Commands, exit status, counts

| Command | Exit | Ran | Result | Per class |
|---|---|---|---|---|
| `.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v` | 1 | [('236', '1529.797')] | [('FAILED', 'failures=1, skipped=5')] | {'Approval': 10, 'AuditMap': 4, 'Boundary': 11, 'Executor': 17, 'FrameInvariant': 7, 'KeyFunctions': 5, 'KeyIntegrity': 10, 'Rev5Clock': 4, 'Rev5Evidence': 9, 'Rev5LocalReceipts': 4, 'Rev6Evidence': 2, 'Rev6LocalCommands': 3, 'Rev7': 8, 'ScorerAdmission': 4, 'Scoring': 4, 'Validator': 8, 'HardKill': 15, 'Rev5Recovery': 4, 'Rev6': 3, 'Controller': 28, 'Finalisation': 12, 'Startup': 4, 'GoAttestation': 10, 'ReviewedPackageBuilder': 4, 'StageA': 14, 'Units': 10, 'ValidatorMutations': 22} |
| `.venv-build/bin/python -m unittest stimuli.photo.tests.test_ai_reader.KeyFunctions -v` | 0 | [('5', '0.656')] | [('OK', '')] | {'KeyFunctions': 5} |

## Skips

- `test_full_form_s1_prospectively` (test_ai_reader.KeyFunctions.test_full_form_s1_prospectively): needs WordNet (run under .venv-build)
- `test_inflections` (test_ai_reader.KeyFunctions.test_inflections): needs WordNet (run under .venv-build)
- `test_rebuild_reproduces_the_key` (test_ai_reader.KeyFunctions.test_rebuild_reproduces_the_key): needs WordNet (run under .venv-build)
- `test_specificity_rules` (test_ai_reader.KeyFunctions.test_specificity_rules): needs WordNet (run under .venv-build)
- `test_synonym_residue` (test_ai_reader.KeyFunctions.test_synonym_residue): needs WordNet (run under .venv-build)

'needs WordNet' skips in the main stderr: 5. The WordNet checks run under .venv-build (second row).

## Failures and errors

- image_suite: test_slow_receipt_and_slow_close_share_one_deadline (test_ai_reader_crash.Rev6.test_slow_receipt_and_slow_close_share_one_deadline)

The one failure is a stale assertion text, not a changed outcome: the over-allowance COMPLETE is still refused by
`admit_clock`, but revision 7's closure-marker check (reader A) now refuses it first, with "refused: no closure marker
for this journal and clock" where the revision-6 fixture expected "not closed on this receipt" (`image_suite.stderr.txt`
line 290 onward). Fixed in RSC `f3ae678` (the assertion accepts either message; tests are outside both package
identities, so every hash above is unchanged - recomputed after the fix).

## Supplement: the changed test module on `f3ae678`

`.venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p test_ai_reader_crash.py -v`, in
`supplement_crash_module/`: HEAD `f3ae67848a97c2ff47a960cb014ee7b5c007c569`, photo directory status before 0 lines,
2026-10-02T15:42:16Z to 15:51:01Z, exit 0, **26 tests in 524.8 s, OK** (HardKill 15, Rev5Recovery 4, Rev6 3, Rev7 4).
Every other module is byte-identical between `068fe30` and `f3ae678` and passed in the main run above; it was not rerun.

## Retained files (sha256)

- `build_keyfunctions.exit.txt` 2 bytes `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `build_keyfunctions.stderr.txt` 734 bytes `d210163eec5ea1cc1f3824ec390d58ef5aa4fef4bd766013e9fa6291afc322f5`
- `build_keyfunctions.stdout.txt` 424 bytes `2e3ec67ffe9ca6285cc8c5e73f837b7cade506e2cc9b7e2f2d6da3789906e1c7`
- `end_utc.txt` 21 bytes `a0b9ef6df1de237bc1324291f58d5416eb588069f828a43654f345d134232496`
- `head.txt` 41 bytes `ee0d3ad65725fbe45d86bc119e2b84d2904ee90cc486fe4be2dfaa163c5bbaf7`
- `image_suite.exit.txt` 2 bytes `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
- `image_suite.stderr.txt` 33655 bytes `8e94a8d544d9f7ee43224d92d36a2e3c675cd5dc168a0be4e1b551430ef45e82`
- `image_suite.stdout.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `photo_status_before.txt` 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `start_utc.txt` 21 bytes `dfeeb72ef0b671660df681de0c993e8e7b6e4558ce437dd4c1dd6f26cb8c3ec3`

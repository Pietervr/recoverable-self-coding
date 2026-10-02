# Photograph arm, ledger row 20: readiness, revision 2

R084 (Claude), 2 October 2026. **Row 20 has no go.** No forward has run on any DEV-CAL or DEV-PILOT image, and no
decoder has been fitted on image states.

| Record | Commit | What it is |
|---|---|---|
| Revision 1 | RSC `79343d9` | the first package |
| Codex's review | RSC `f9d2ef3` | **NOT ON BOARD**, not a favourable review |
| R052's repair brief | Unimog `c9e0421d` | 18 repairs, accepted as handoff `eb9620f5` |

This revision is the single revised package the brief asks for. `STAGE_A_CRITERIA.md` §0 maps each repair to its
code and test.

## The package (what the go must bind)

| Item | File | sha256 |
|---|---|---|
| Criteria | `STAGE_A_CRITERIA.md` | printed by `stage_a.py package` |
| Execution identity | `stage_a_identity.json` (written by `stage_a.py identity`) | printed by `stage_a.py package` |
| Frozen plan | `stage_a_plan.json` (revision 2) | printed by `stage_a.py package` |
| Manifest | `manifest_dev.json` | printed by `stage_a.py package` |
| Budget envelope | `stage_a_plan.json` → `envelope` | printed by `stage_a.py package` |

The handoff brief to R052 carries the exact values for this commit.

**Code.**

- `stage_a.py`: the runner.
- `stage_a_guard.py`: lock, terminal gate, go binding and identity.
- `stage_a_report.py`: validator and report.
- `enforce.py`: the budget session, supervisor, transaction, memory and storage.
- `image_adapter.py`: per-pass identity evidence and finiteness.
- `tests/`: the fake-instrument tests, 15 of 15 passing.

**`ROW20_GO.json` must hold these fields.** The runner refuses before any load otherwise.

```json
{"codex_row_review": {"verdict": "favourable", "commit": "<RSC commit of the favourable record>",
                      "record_path": "<path of the record in RSC>", "record_sha256": "<sha256 of that file at that commit>"},
 "owner_go": {"by": "owner", "date": "YYYY-MM-DD", "words": "<the owner's go, verbatim>"},
 "package": {"criteria_sha256": "...", "identity_sha256": "...", "plan_sha256": "...", "manifest_sha256": "...",
             "budget_sha256": "..."}}
```

Any later change to the code, plan, manifest, criteria or environment changes a bound hash. The go then refuses, and
the package goes back for review.

## What changed in substance, beyond the code

1. **Stage A's eight changed: mask out, clothes in.** Applying R052's adopted stock-listing rule (repair 16) to the
   actual inputs found a live Shutterstock listing of mask's image (1799626735, uploaded 2020-08-20) crediting
   "Beni setiawan98". The Pixabay source credits josealbafotos (2016-01-20). A listing that names a different author
   is a conflicting claim under §8.2, so mask is ineligible.
   - `pool.py` replaced it in seeded order with clothes. It skipped wig (published 2019), sweater (a live listing
     credits another author) and scarf (published 2020).
   - No other role moved.
   - The other views' stock listings were all removed when opened on 2 October, and all postdate their free
     sources.
   - **For R052:** framework §8.2's list of Stage A's eight and its stock counts still name mask; that text is
     R052's to change.
2. **Engineering carried in.** Row 20's state starts at 16 attempts and 1,808.73 s (8.73 s measured plus a 1,800 s
   allowance), which leaves 194 of 200 planned.
3. **The audit's reader rule** follows the owner's decision (§8.2 as revised by R052): the qualified AI reader, with
   the owner deciding referrals. It is frozen in `audit_app/IMAGE_AUDIT_FREEZE.md`. It is not a row-20 gate.

## Forecast (unchanged, from one out-of-pool image; establishes nothing)

| Quantity | Measured | Stage A forecast | Cap |
|---|---|---|---|
| Instrumented pass | about 1.0 s | 158 passes, about 3 min | |
| Native pass | 0.9 s | 20 passes, under 1 min | |
| Loads | about 5 s each; lens about 3 GB | minutes | |
| Identity hashing | 8.6 s cold (cached afterwards) | per phase | |
| Whole stage including report | | well under 30 min | 4 h, less the 1,808.73 s carried |
| Task memory, instrumented process | 30.65 GiB | | 48 GiB |
| Task memory, native process | 16.69 GiB | | 48 GiB |
| Storage | about 2.0 MB per instrumented pass, 3.9 MB per native pass (FP32) | about 0.40 GB | 1 GiB |

## Still needed before row 20 runs

1. R052 submits this exact package to Codex.
2. Codex gives a favourable row review.
3. The owner gives a go bound to the package's hashes in `ROW20_GO.json`.

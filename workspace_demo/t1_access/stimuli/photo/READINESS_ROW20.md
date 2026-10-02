# Photograph arm desk gate: readiness report for ledger row 20

R084 (Claude), 1 October 2026 (2 October in R052's dating). This answers R052's handoffs 2e94e85e, 41b67d26 and
a89ddc24. Framework `rsc_t1_two_channel_framework.md` §8 is the specification. **Row 20 has no go.** No forward
has run on any DEV-CAL or DEV-PILOT image, and no decoder has been fitted on image states.

Framework §8.1 item 2 asks R084 to commit the adapter, the builder, the template, the manifest, the extraction and
edit conventions, the counters and the stop/recovery mechanism before the go. All are committed (RSC):

| Item | Where | Commit |
|---|---|---|
| Pool and roles (ask 1a), with the per-image check and seeded replacements | `pool.py`, `dev_pool.json`, `provenance_checks.json` | c2721c1, 3324b2f, 6442e2e |
| Dose pipeline and delivered-SNR report (ask 2) | `dose.py`, `dose_report.py`, `dose_report.json` | 56a8b82, 3324b2f |
| Enforcement: counters, stops, recovery (ask 4) | `enforce.py` | 804eaef |
| Image adapter, builder, template, extraction and edit conventions (ask 3) | `image_adapter.py` | 889a04e |
| Manifest (ask 1b) | `manifest.py`, `manifest_dev.json` | ebf7d8f, 6442e2e |
| Stage B second-view candidates (ask 1b) | `second_views.py`, `second_view_candidates.json` | 8425fd2 |
| Stage A runner and criteria | `stage_a.py`, `stage_a_plan.json`, `STAGE_A_CRITERIA.md` | this commit |

## 1. The adapter: the text arm's capture path, with the image injected

The instrumented image path runs the text arm's single-pass capture (`capture_endpoint._run` and `validate`, patch
t1-capture-2) in-process and unmodified. It adds two things:

- **An embedding injector.** The mlx-vlm 0.6.3 qwen3_5 vision tower and its native `merge_input_ids_with_image_features`
  replace the image-pad rows.
- **Interleaved M-RoPE** in the 16 full-attention layers, fed mlx-vlm's own `get_rope_index`.

Measured before the build, on text only (no image, no pool concept; `engineering/runtime_agreement.json`):

- mlx-vlm's separate qwen3_5 language stack equals the jlens StreamSession **bitwise** on all 64 layers and the
  logits.
- The M-RoPE swap is bitwise equal to `nn.RoPE` on 1-D positions.
- On unequal (t, h, w) positions the swap moves the output (rel L2 up to 0.040, so it is live) and matches mlx-vlm
  bitwise.

So the image arm runs the text arm's own runtime and edit code. The runtime factor of §8.4 ("same weights alone do
not isolate modality") reduces to the vision tower, the merge and the positions, all mlx-vlm's own.

**Template (proposed, for the row review).** Raw ids, no chat template and no thinking block, matching the text arm
(PREREGISTRATION §4):

    Look at the picture below; afterwards, name in one word what is shown.
    <carrier open>
    <|vision_start|><|image_pad|> × 144<|vision_end|>
    <carrier close>
    [END]

followed by `\nAnswer:`. The two carriers are:

- "Here is a photograph someone took:" / "That was the whole photograph."
- "A camera captured the following picture:" / "Nothing else was in the picture."

Packet.build_ids' marker and join rules apply to the unexpanded prefix. The expanded ids equal mlx-vlm's processor
output (185 ids for carrier 0).

**Engineering forwards** (allowed on one image outside the 32-concept pool, logged, establishing nothing;
`engineering/README.md`):

| Identity | Input | Attempts | Completed | Failed | Note |
|---|---|---|---|---|---|
| `eng-runtime-agreement` | one 19-token text prompt | 8 | 8 | 0 | 1.72 s of attempts |
| `eng-image-adapter-1` | THINGSplus `chair.jpg` (outside the pool) | 8 | 7 | 1 | the failure was before any model pass |

16 attempts in all. On `chair.jpg`:

- The processor ids and grid are equal to the builder's.
- Empty edit, zero dose, self-patch and delayed repeat are bitwise equal to plain. The λ = 1 swap changes the output.
- Native mlx-vlm prefill: marker residuals bitwise at 64/64 layers, requested-logit max |diff| 0.031 (tolerance
  0.10), same argmax. The model's top answer is " Chair".
- Memory: 30.65 GiB instrumented, 16.69 GiB native.

The logit difference has a probable cause, not verified: the text path unembeds the final row alone, while mlx-vlm
unembeds the whole sequence, so the quantized matmul shape differs. Stage A measures parity on DEV-CAL under row 20.

## 2. Development set: every role checked eligible (capture gate, option A)

46 THINGSplus files were checked on 1 Oct 2026 (TinEye, then the earliest source page; all observations are in
`provenance_checks.json`): **32 eligible, 14 ineligible.**

- Pixabay: CC0 only for a published date before 9 Jan 2019 (Pixabay Terms §4).
- The ineligible files: 11 Pixabay uploads from after the switch; shirt, which exists only on Pexels under the
  Pexels License; shorts and wine, whose only or earliest source is a stock listing.
- Non-Pixabay eligible sources: robe on StockSnap (CC0); jet, a USAF photo on Commons (PD); ship on Commons (PD).

The THINGSplus collective statement "all images had a public domain/CC0 license" failed for 14 of 46 files.

Replacements follow the seeded rule. Rejections are taken in the order their checks were recorded, so a replacement
once made never moves:

| Out | In | Skipped |
|---|---|---|
| fly | horse | |
| suit | jacket | wig |
| bull | pig | |
| frog | butterfly | monkey, ant, bug |
| coat | lingerie | |
| shirt | tie | |
| shorts | hat | |
| meat | candy | |
| wine | prune | |
| helicopter | skateboard | |

The roles are now:

| Family | DEV-CAL (Stage A views in bold) | DEV-PILOT |
|---|---|---|
| Animals | **crow**, **horse**, pig, shark | butterfly, cow, mosquito, pigeon |
| Foods | avocado, caramel, **chili**, **hamburger** | candy, cheese, prune, tomato |
| Vehicles | boat, canoe, **taxi**, **wagon** | jet, ship, skateboard, truck |
| Clothing | **jacket**, jeans, lingerie, **mask** | hat, robe, sock, tie |

The dose report on the Stage A eight is unchanged: delivered within 0.2 dB of nominal, zero clipping, 144 tokens,
no defect.

**Open for R052 (terms).** TinEye also lists the same image in stock collections for many eligible files: tomato 28,
jet 16, candy 14, butterfly 10, pig 9, and taxi 2 among the Stage A eight. The first record called these adverts,
which was wrong, and it is corrected. Is a stock listing of an image that is CC0 at its source a "conflicting rights
claim" under §8.2? The counts are recorded and nothing was excluded on them.

## 3. Manifests and second views

`manifest_dev.json` has 32 records with both field sets:

- the release fields
- "found by the per-image check, <date>": source URL, creator, published date, the licence line read

It also records the original-byte hash, geometry and operations, the clean-canvas PNG and processed-tensor hashes,
and the execution identity. Capture is admitted only on an eligible check. Capture-time fields (nonce, positions,
delivered tensors) are recorded per trial.

`second_view_candidates.json` has 8 candidates for each of the 32 concepts: Commons bitmaps whose own structured data
states CC0 or PD, shorter side ≥ 384, with titles naming an artwork medium or a museum dropped. Relevance is mixed:
a painting, a TIE fighter, a town called Chili, station wagons. The second view is the first candidate that the audit
accepts as a photograph of the concept in its THINGS sense, distinct from the primary. It then needs its own
per-image check, at the original source when Commons credits another site. Stage B holds for any concept without one.

## 4. Proposed image and sense audit reader

The model under test never filters, and llama3.1:8b is not used. The proposal follows the text audit's structure
(`audit_app/README.md`):

**Readers.** One or more human readers (the owner, and others through an image page added to the existing audit app,
audit.raconteur-road.com), plus one AI reader from a different developer than the model under test (Codex,
GPT-family vision).

**What they see.** The actual grayscale normalised clean canvas, and for a second-view candidate, both images side
by side.

**Questions.**

1. Is it a photograph?
2. Does it show <name> in the sense "<THINGS definition>"?
3. Could you name it in one word from this grayscale picture?
4. For a second view only: is it a different photograph from the primary, not a crop or flip?

**Pass rule.** An item passes with at least one human pass and the AI reader's pass. The author decides any
disagreement, with every answer recorded.

The owner chooses the readers. Codex's row review decides whether the audit must precede row 20's go or only row 21.
Stage A's criteria are not semantic, but its eight views would ideally be audited first.

## 5. Environment (part of the execution identity)

`t1_access/.venv-image` uses Python 3.12.14 and pins mlx 0.31.2, mlx-lm 0.31.3, transformers 5.13.0 and numpy
2.5.1, as in the jlens rig, plus mlx-vlm 0.6.3 and Pillow 12.3.0. It loads the jlens sitecustomize shim. The text
capture environments (`upstream/jlens-qwen36/.venv`, `t1_access/.venv`) are untouched. Snapshot: c000ac2c. Lens:
`qwen36_27b_neuronpedia_n1000.npz`.

## 6. What row 20 needs before it can run

1. Codex's row review of `STAGE_A_CRITERIA.md` and the code, including the proposed seven cases and the template.
2. R052's call on stock-listed CC0 images, and on whether the audit precedes row 20.
3. The owner's go, recorded by creating `ROW20_GO.json` (`owner_go`, `codex_row_review`).

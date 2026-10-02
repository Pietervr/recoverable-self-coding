# Stage A (ledger row 20): declared criteria and code — proposed by R084, 1 October 2026

Framework `rsc_t1_two_channel_framework.md` §8.4 (Unimog repo) is the specification; this document states how
`stage_a.py` implements it, so Codex's row review can check the code against the text before the owner's go.
Nothing here has run on a development image. `stage_a.py instrumented|native` refuses to start until
`ROW20_GO.json` exists beside it with `owner_go` and `codex_row_review` filled.

## Inputs (frozen by `stage_a.py plan` → `stage_a_plan.json`, seed 20261006)

| | Count | Construction |
|---|---|---|
| Clean | 8 | the eight Stage A primary views (crow, horse, chili, hamburger, taxi, wagon, mask, jacket), a = 1 |
| Intermediate | 8 | per family the two views, sorted by name, dealt one to −12 dB and one to 0 dB by the seed (4 + 4) |
| Noise-only | 4 | `dose.zero(nonce)` — its own path, no photograph opened |

The 20 inputs are shuffled by the seed. The first 10 take carrier 0, the rest carrier 1 (10/10). Each input's noise
nonce is `sha256("stageA|20261006|<index>")`, independent of concept and pixels. Every view has an eligible per-image
check (`provenance_checks.json`), and the plan asserts it. The plan records each input's PNG hash, processed-tensor
hash and grid ([1, 24, 24] → 144 merged tokens for all 20).

## Passes: 160 mandatory, the 40 spare unused

Each input runs seven instrumented cases through `image_adapter.ImageInstrument`, one model pass each. Every case
captures 64 layers at the three `[END]` positions, plus closed-set logits over the 32 frozen E1 ids at the final
suffix token:

| Case | Edit | Check |
|---|---|---|
| plain | none | reference |
| empty | `edits = []` | bitwise = plain |
| zero | swap_delta target→foil, layer 41, λ = 0 | bitwise = plain (the sham) |
| self_patch | patch layer 41's marker rows with plain's own rows | bitwise = plain |
| swap | swap_delta target→foil, layer 41, λ = 1 | runs, edit log recorded (H3 primary operation; mechanics only) |
| ablate | ablate target, layer 41, λ = 1 | runs, edit log recorded (H3 secondary operation; mechanics only) |
| repeat | none, after all inputs' other cases | bitwise = plain (delayed repeat) |

Target = the view's E1. Foil = the other Stage A view of its family. A noise-only input uses its assigned family's
pair in name order. That makes 7 × 20 = 140 instrumented passes.

The native reference is mlx-vlm 0.6.3's own prefill for an unchunked prompt (`get_input_embeddings` →
`language_model(ids, inputs_embeds, cache)`), one pass per input in a separate process: 20 passes. It reads the
residuals through transparent proxies on the decoder layers. It does not use mlx-vlm's `capture_layer_ids`, which
switches mlx-vlm to its speculative-verify kernels.

**Proposed reading of "seven instrumented cases"** (§8.4 names the bitwise checks but not the seven): plain, empty,
zero, self-patch and delayed repeat give the within-path parity. Swap and ablate exercise H3's edit modes at the
marker positions. The rescue (steer at a CAL-frozen amplitude) and the positive-control patch need CAL-fitted
quantities, so they are not in Stage A. This is R052's and Codex's to confirm.

## Tolerances and stops (fixed before the run, never adjusted after a failure)

- Native parity per input: relative L2 ≤ 0.01 at every marker layer, in FP32 over the three marker rows. Max
  |logit difference| ≤ 0.10 over the 32 E1 ids. Identical closed-set argmax. The pixel-tensor hash must equal the
  instrumented pass's.
- Within the instrumented path, bitwise: residual hash, logit hash and vision-feature hash equal plain's.
- Stop at the first bitwise or parity failure (`STOP_*.txt` is written), at an identity mismatch, or at any
  `enforce.Budget` stop: row 20 ≤ 200 attempts, ≤ 4 h, ≤ 1 GiB outputs, with the aggregate caps; task memory
  max(phys_footprint, MLX peak) ≤ 48 GiB; swap above the start level; kernel pressure ≥ warn. No retry. A parity
  failure is never followed by spending the spare 40.
- Counters persist atomically before and after each attempt (`captures/photo_stage_a/stage_a_state.json`). Recovery
  charges an interrupted attempt and refuses a changed identity. A completed attempt id is never replayed.

## Identity

The execution identity hashes:

- `stage_a.py`, `image_adapter.py`, `dose.py`, `enforce.py` and the upstream `capture_endpoint.py`
- the template hash
- the mlx, mlx_lm and mlx_vlm versions, and the snapshot id
- the plan hash, which covers the dev_pool and check hashes and the a-grid hash

Each pass records:

- the input-id hash and the expanded image grid
- the hashes of the multimodal positions, the pixel tensor and the vision features
- the FP32 mean of the 144 projected visual tokens (the encoder boundary) and its hash
- the edit log
- the timing

## Forecast (from the engineering forwards on one out-of-pool image, establishing nothing)

| Quantity | Measured | Stage A forecast | Cap |
|---|---|---|---|
| Instrumented pass | ≈ 1.0 s (6 passes, 6.09 s with edits) | 140 passes ≈ 2.5 min | |
| Native pass | 0.9 s | 20 passes ≈ 0.5 min | |
| Load | ≈ 5 s (lazy vision + mlx_lm), lens ≈ 3 GB | minutes | |
| Total compute | | well under 30 min | 4 h |
| Task memory, instrumented process | 30.65 GiB phys_footprint | | 48 GiB |
| Task memory, native process | 16.69 GiB | | 48 GiB |
| Outputs | 1.97 MB per pass (64 × 3 × 5,120 bf16) | ≈ 0.28 GB + logs | 1 GiB |

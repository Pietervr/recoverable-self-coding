# Image adapter engineering forwards (desk gate ask 3), 1 October 2026 (MDT; 2 Oct in R052's dating)

Framework §8.1 item 2, R052's reading: forwards while the adapter is written run on images outside the 32-concept
pool only, are logged with their counts and identities, and **establish nothing about Stage A**. None of these
touches a DEV-CAL, DEV-PILOT or any of the 121 qualified pool concepts. Row 20 has no go; its state file does not
exist yet. Each identity below has its own state file, kept by `enforce.Budget` (row label `row20` is only the cap
set applied as a ceiling; these are not row 20's counters).

| Identity | State file | Input | Passes started | Completed | Failed | Seconds (attempts only) |
|---|---|---|---|---|---|---|
| `eng-runtime-agreement` | `engineering_state_runtime_agreement.json` | one 19-token text prompt, no image, no pool concept | 8 | 8 | 0 | 1.72 |
| `eng-image-adapter-1` | `engineering_state_adapter.json` | THINGSplus `chair.jpg` (furniture; outside the pool), clean canvas, carrier 0 | 8 | 7 | 1 | 7.01 |

16 attempts in all, 15 completed. The first `runtime_agreement` run (lm mode, 2 passes) was under the identity
`eng-runtime-agreement-lm`. The vlm mode was then refused by the identity check before any pass. The state file was
relabelled to the single identity `eng-runtime-agreement` before the rerun (a manual edit of an engineering file,
recorded here). The counts above include those first 2 passes. The failed adapter attempt raised in `_run`'s
hidden-dtype probe before any model pass. The injector refused an embed call on ids other than the registered image
sequence, and the probe is now resolved at instrument init. It stays counted.

**Results.**
- `runtime_agreement.json`: mlx_lm/jlens StreamSession vs mlx-vlm 0.6.3's qwen3_5 language stack on text, bitwise
  on 64/64 layers and logits. The M-RoPE swap is bitwise equal to nn.RoPE on 1-D positions. On unequal (t, h, w)
  positions it is live (rel L2 to the 1-D result up to 0.040, layers 0-2 unchanged before the first full-attention
  layer) and bitwise equal to mlx-vlm.
- `adapter_engineering_inst.json`: builder ids and grid equal mlx-vlm's processor (185 ids, grid [1, 24, 24], 144
  merged tokens). Empty edit, zero-dose swap, self-patch and delayed repeat are bitwise equal to plain. The lambda = 1
  swap changes the output. One injection per pass. Top token " Chair". Task memory (phys_footprint) 30.65 GiB.
- `adapter_engineering_native.json`: mlx-vlm's own prefill vs the instrumented pass. Marker residuals bitwise on
  64/64 layers. Requested-logit max |diff| 0.03125 (tolerance 0.10). Same open-vocabulary and closed-set argmax.
  Native process phys_footprint 16.69 GiB. Probable cause of the logit difference (not verified): the text path
  unembeds the final row alone, while mlx-vlm applies `lm_head` to the whole sequence and takes the last row, so the
  quantized matmul shape differs.

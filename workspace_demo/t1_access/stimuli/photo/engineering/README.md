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

## Reconciliation with row 20 (2 October 2026; framework §8.4; Codex RSC f9d2ef3, R052 repair 15)

**Carried in, not reset.** The 16 attempts above are row 20's first 16. `stage_a.py` creates row 20's state file
with `ENGINEERING_CARRY`: started 16, completed 15, failed 1 (the pre-model failure), passes 16, and **1,808.73 s**
of time - the 8.73 s measured inside attempts (1.72 + 7.01) plus a recorded **allowance of 1,800 s** for what was never
timed: interpreter starts, model and lens loads (about 5 s per load measured, the lens ~3 GB), preprocessing, writes and
the manual relabel. The allowance is deliberately generous. The envelope is then 16 carried + 140 mandatory
instrumented + 16 mechanics diagnostics + 2 suffix-isolation diagnostics + 20 native = **194 of 200**, six in hand;
`2,056` remains the photograph project's total across rows 20 and 21, engineering included. The two engineering state
files above stay as they are (the record of what ran); `enforce.py` has since been revised, so these scripts would
not run again unchanged - no further engineering forwards are planned. The engineering attempts establish nothing
about Stage A.

**Strength of the equality claims, relabelled.** `adapter_engineering_native.json`'s `"bitwise_layers": 64` counts
layers whose relative L2 is exactly 0 after conversion to FP64, and `runtime_agreement.json`'s
`"bitwise_equal_layers"` counts `np.array_equal` on the saved arrays. Both are **numeric equality on the saved
arrays**, not byte comparisons (a signed zero would not be told apart). The scripts now name these
`numeric_equal_layers`; the committed JSON keeps the old key names as the record of 1 October, read with this label.
The within-instrument comparisons in `adapter_engineering_inst.json` (`bitwise_equal_to_plain`: residual, logit and
feature sha256) are byte comparisons and keep the word.

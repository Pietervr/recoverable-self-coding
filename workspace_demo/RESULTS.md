# Overnight results — 2026-08-24 (first data night)

Model: Qwen3.6-27B 4-bit (MLX) · Lens: Neuronpedia n=1000 · Band: L23–57 of 63
· Hardware: M4 Max/128 GB, local. All runs resumable from `runs/*.jsonl`.

## P0 — first light: PASS
The paper's flagship example reproduces locally: on "the animal that spins
webs", `spider` (never in the prompt) reaches **rank 1** in the workspace band
(L21–24, 219 top-10 hits) and the model answers "8".

## P1 — calibration (runs/p1_summary.json)
- 89/90 probe-swap items usable (single-token filter dropped 1).
- **Certification rate 0.989 · accuracy 0.831 · cert∧correct 0.82** at zero
  load: flexible two-hop commitments route through the workspace essentially
  always — the classifier reads it.
- Causal spot-check: **Brazil→Mexico swap at L37 flipped Portuguese→Spanish**
  (the paper's signature effect, reproduced). 1/10 flips with single-LAYER
  swaps — expected weak lower bound; the paper's ~70% needs band-wide swaps
  (available via the chat-stream InterventionSpec: `layers: list[int]` —
  upgrade path for the validation).

## E1 v2 — statics (runs/e1v2_summary.json; 45 items × K ∈ {0,4,8,16,32,48})
Question-span position discipline (v1 was echo-contaminated; superseded).
- **Capacity measured: occupancy saturates at ~3 unrelated concepts**
  persisting into the question span (1.5 → 1.8 → 1.8 → 2.7 → 2.9 as K goes
  4→48; retained fraction collapses 38%→6%). The first E1 prediction
  (occupancy plateaus at C) is confirmed.
- **Certification is load-invariant at 97.8%** across all K: passive
  held-word load cannot displace the live inference's intermediate — the
  workspace protects the active task and evicts passive holds (consistent
  with Gurnee §4.2 eviction).
- Accuracy drifts 0.89→0.80 with certification flat — small; suggests this
  channel stresses retention, not routing. **Margin exhaustion needs a drive
  that contests the inference path — that is E2's feedback closure.**

## E2 — hysteresis pilot: protocol validated, run pending
First (Q/A-framed) attempt provoked `<think>` blocks every step — caught by
the 6-step sanity gate, reframed as a flat fact stream matching the
P0/P1/E1 surface. The relaunched pilot's first 6 steps are clean: correct
answers, rank-1 certification, and the α=1 arm visibly re-ingesting the
model's own continuation junk (the drive works). The full pilot
(3 sessions × both arms, ramp K 0→48→0 + probes + reset) was interrupted by
a host-side task stop ~04:22 and awaits relaunch:

    python3 e2_hysteresis.py --sessions 3 --kmax 48 --kstep 8 --probe-k 16

(resumable; server stays up under nohup — check `/api/lens` first).

## Fixes of the night (all committed)
tokenize schema (`text` not `prompt`) · intervene response
(`intervened.text`) · E1 occupancy echo → question-span discipline ·
E2 Q/A framing → flat fact stream · load pool 64→96 nouns.

# Results — 2026-08-24 (overnight P0/P1/E1 + the daytime E2 completion)

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

## E2 — feedback closure: COMPLETE (10 sessions × both arms, 380 steps)
Run 2026-08-24 ~13:16–14:20 under the tail-160 readout patch (~1 h wall).
Arms are item-matched (same per-session stream and held-word seeds) and
length-matched (padding audit: α=0 context never shorter, 0/190 pairs), so
each (session, step) is a matched pair differing only in re-entrant
CONTENT. Raw data `runs/e2_hysteresis.jsonl`; analysis `e2_analyze.py`;
per-cell means `runs/e2_summary.json`.

1. **The α-drive effect (the headline): ungated re-entry degrades
   performance.** α=1 (raw model output re-enters the transcript) accuracy
   **0.784** vs α=0 (gated correct-answer channel) **0.842**; discordant
   pairs **14 α=0-only-correct vs 3 α=1-only-correct — exact McNemar
   p ≈ 0.013**. Under load the gap widens: loaded probe block 0.867 (α=1)
   vs 0.967 (α=0). This is RSC's ungated-re-entry claim measured on an
   open-weight model with the workspace instrument.
2. **"Reset restores only what is archived" — confirmed exactly.** The
   loaded-context arm gap (0.867 vs 0.967) vanishes on context reset: both
   arms land on IDENTICAL post-reset probe accuracy (0.767) and identical
   occupancy (1.67). The entire drive-induced difference lived in the
   operating state (context); none reached the archive (weights + lens).
   (Probe vs reset-probe absolute levels use different stream items —
   cross-block absolutes carry item effects; the arm-convergence comparison
   is the item-matched, valid one.)
3. **No α-dependent hysteresis (pre-registered negative).** Down-branch
   accuracy sits ~0.033 below up-branch in BOTH arms (α=1 0.783→0.750,
   α=0 0.850→0.817) — an arm-independent context-accumulation effect, not
   the predicted α=1-specific down<up loop. At K≤48 with this drive the
   system stays in the recoverable regime.
4. **Certification is load- AND drive-invariant; every error is
   certified-but-wrong.** 374/380 steps certified; all 6 failures are one
   battery item (birthstone-emerald-month), every one answered CORRECTLY —
   the model produces the month number without staging the month name in
   the band (item artifact, not load). Hence all ~71 errors had their
   determinants present in the workspace: routing never failed; failures
   are retention/readout. **E3's determinant-absence signature was not
   reached** — the collapse boundary lies beyond K=48 under this drive, so
   the ignition-β̂/collapse test needs a harder drive (higher K,
   adversarial fillers, or multi-hop chains). That is E2b/E3 territory.

## E2b — collapse boundary, interrogated load × depth: BOTH FALSIFIERS FIRED
10 sessions × both arms, 280 steps (~50 min). Ladder L=0,2,4,6,8 liable
watch-list words; 2-hop + echo-free 3-hop chains certified per intermediate
at top-25 readout. Calibration: 14/16 three-hop survivors, both
intermediates rank 1–3 at baseline (no shortcut). Raw data
`runs/e2b_collapse.jsonl`; analysis `e2b_analyze.py`.

- **F1: certification flat at ceiling** — 199/200 fact steps certified at
  every L and both depths (the single exception a rank-11–25 crowding case).
  Liable load + depth-3 chains cannot displace the live inference's
  determinants any more than E1's passive load could.
- **F4: the interrogation never bound.** Watch queries are 100% correct at
  every L (even 8), with the queried word summoned to rank ~1 in the band —
  while during unrelated inference the watch list's band occupancy sits at
  only 0.15–0.75 of L. **The load is not maintained in the workspace between
  queries; it is retrieved from context on demand** (the paper's top-down
  summoning, observed operating as a defense). Context functions as an
  external store with cheap random access; the workspace stages only the
  live computation — so context-borne load, passive or liable, cannot
  exhaust it.
- P2/P3 moot in-regime (no decline to fit; errors remain
  certified-but-wrong, err|certified 0.11–0.15).
- **Arm sanity:** 0/140 discordant answers despite genuinely divergent
  transcripts (29/140 continuations differ; junk re-entered on 12 α=1
  error steps). At ~450–600-token contexts the α poisoning that cost
  0.058 accuracy in E2's ~1000-token sessions has no measurable effect —
  consistent with a dose effect of accumulated junk, not an artifact.

**Synthesis after E1+E2+E2b:** three levels, not two — weights (archive) /
context (persistent, resettable store with cheap random access) / workspace
band (per-forward-pass staging). Sequential drives load the STORE, and the
store cannot saturate the STAGE: routing is architecturally protected,
summoning is on-demand, and the only sequential lever that moved
performance is CONTENT poisoning of the store (E2's α effect). If a
capacity collapse boundary exists, it must be induced IN-PASS — 
simultaneous staging demand inside one forward pass. That is E2c.

## Fixes (all committed)
tokenize schema (`text` not `prompt`) · intervene response
(`intervened.text`) · E1 occupancy echo → question-span discipline ·
E2 Q/A framing → flat fact stream · load pool 64→96 nouns ·
**serve.py tail-readout patch** (`patches/serve_tail_readout.patch` — caps
the [layers × positions × vocab] logits transient that OOM'd the Mac;
side-effect: ~5× faster steps) · **atomic-session resume** (a mid-session
kill re-runs the session; summary dedups last-record-per-step) ·
`start_server.sh` idempotent server launch.

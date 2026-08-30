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

## E2c — in-pass parallel demand: F1c FIRED (span measure at ceiling to M=6)
120 trials (20 × M ∈ 1..6), one prompt per trial carrying M simultaneous
two-hop chains, one ordered continuation; 45 clause-embeddable battery
items, category-diverse compositions; parse rate ≥0.95 at every M (format
gate passed). Raw data `runs/e2c_parallel.jsonl`.

- **Span-aggregated certification: 1.000 at every M**, mean best rank
  1.02–1.18, zero absences; per-slot accuracy flat (0.80–0.89, no decline
  with M). The model stages SIX simultaneous intermediates, all near rank
  1, and answers them at ~85% regardless of M. Interference exists at the
  answer level (perseveration cases like " 4; (2) 4") but does not scale
  with M.
- Why the span measure cannot see a bottleneck: it aggregates over
  positions, so each chain may be staged AT ITS OWN clause's positions
  (position-parallel staging), and autoregressive emission re-summons each
  chain at its own answer token (nothing is ever simultaneous). Hence the
  **v2 commitment-position refinement** (pre-registered, commit `6da6cff`):
  rank over the final 3 prompt positions only — where the first answer
  must be ready.

## E2c v2 — the commitment stage is SERIAL (the day's sharpest structural find)
Same seeded compositions, plus `rank_commit` = best rank over the final 3
prompt positions. Raw data `runs/e2c_parallel_v2.jsonl`.

- **P4c CONFIRMED, stronger than predicted: staged-per-trial ≈ 1, not 3.**
  Staging at the commitment position collapses from 1.000 (M=1) to
  0.20–0.26 (M=4–6) while staged-per-trial stays pinned at 1.0–1.4;
  absent-at-commit grows linearly (85/120 at M=6); mean commit rank
  degrades 1.75 → 5–6. The slot control shows what is staged: **the
  imminent commitment — 94% of commit-staged chains are slot 1** (the
  "(1)" cue), all other slots at 3–10%. The action-point workspace holds
  approximately ONE live commitment at a time, independent of M.
- **P5c: the pooled reversal (err 0.099 staged vs 0.164 unstaged, M≥3) is
  confounded with slot position** and the within-slot contrasts are
  underpowered: slot 1 shows err|staged 0.09 (n=75) vs err|not-staged 0.40
  (n=5) — directionally the determinant-absence signature, but n=5.
  Slots>1: 0.125 (n=16) vs 0.159 (n=264), no effect. Verdict: suggestive
  only. The definitive test needs GENERATION-TIME readout (certify at each
  slot's own emission step) — /api/slice reads the prompt span only; noted
  as the instrument upgrade.

## Synthesis — the measured architecture (one model, 4-bit, one day)
Four experiments cohere into a three-stage picture:
- **Store (context):** random-access; content summoned to band rank ~1 on
  demand (E2b) with near-zero inter-query occupancy; cannot saturate any
  stage; erased exactly by reset (E2); its one vulnerability is CONTENT —
  ungated re-entry degrades performance dose-dependently (E2, p ≈ 0.013).
- **Encoding stage (prompt span):** position-parallel; ≥6 simultaneous
  chains staged at rank ~1 with flat accuracy (E2c v1); never saturated.
- **Commitment stage (action point):** SERIAL, width ≈ 1 (E2c v2); holds
  the imminent commitment only and is re-staged per emission token. E1's
  occupancy ~3 was passive persistence, not this width.
RSC reading: recoverability is architecturally enforced — load queues in
the store or parallelizes in encoding and never contests the width-1
commitment stage, so the SR/collapse channel stays closed at every drive
we could construct; the RSC dynamics that DO manifest live at the
agentic-loop level (the α content effect on the store). The open collapse
frontier: much longer α=1 horizons (store poisoning at dose), and
generation-time certification at the serial bottleneck.

## E4 — loop-level collapse with genuine load feedback: COLLAPSE, HYSTERESIS,
## AND A TWO-COMPONENT MEMORY (2026-08-24 evening, seed 0)
The decisive experiment (pre-registered `d416a1a`): the Sec.-IV.F pipeline
protocol with the LLM as the single worker. Wall-clock Poisson arrivals,
utilization ramp 0.40→1.05→0.40; deadlines T_d = 6 × measured congested
service (s_clean 0.87 s, s_cong 10.95 s — a 12.6× state-dependent service
law); uncertified (wrong OR late) completions spawn Poisson(0.8)
genealogy-tagged repair tasks that re-consume the bad answer as input;
α=0 control identical minus offspring. 459 tasks served. Raw data
`runs/e4_loop.jsonl`, analysis `e4_analyze.py`, forensics
`e4_forensics.py`.

- **P1L CONFIRMED — discontinuous collapse far below capacity, and only
  with feedback.** α=0.8: lucid at l=0.40/0.60 (P_u 0.15/0.17, backlog 0),
  then P_u 0.91 in ONE step at l=0.75 (zero lateness — the jump is pure
  content corruption) and pinned at 1.00 above. α=0 control at the same
  l=0.75: P_u 0.17, and NO runaway anywhere — continuous, lateness-driven
  degradation only (P_u 0.75 max at l=1.05, backlog 0 always). The
  transition l_c ∈ (0.60, 0.75) requires the offspring channel.
- **P2L CONFIRMED — total hysteresis.** The α=0.8 down-ramp stays at
  P_u=1.00 with backlog GROWING (27→65) all the way to l=0.40, the load
  the up-branch served with zero backlog. l_rec < 0.40 ≪ l_c. The α=0
  down-branch recovers to P_u=0.08 at 0.40 (with a mild transient content
  echo at mid-l — the dose effect washing out). The decisive falsifier
  (F2L) did NOT fire.
- **P3L OUTSIDE THE PRE-REGISTERED DICHOTOMY — the memory is
  two-component.** Context-clear with queue intact: still P_u=1.00 (the
  stale backlog re-creates the dirty window within a few services).
  Queue-drain with window kept dirty: still P_u=1.00 with the backlog
  re-growing (content-poisoned accuracy 0.00 → spawning → mini-runaway
  inside the probe dwell). EACH store alone regenerates the other; only
  the compound reset (drain + wipe — E2's full reset, known to restore)
  cures. Two honest readings: (a) the probes ran at l=0.40 > 1−α = 0.2,
  inside the mean-field bistable wedge, where no partial cure should
  suffice — a mis-parameterization that accidentally confirms the wedge;
  (b) the queue-only closure would still predict recovery on drain
  (overflow-P_u → 0 with an empty queue); the measured failure means LLM
  loops carry a content-borne P_u floor the closure lacks. Both go in the
  write-up.
- **P4L — F4L again, now through total collapse:** workspace
  certification 0.93–1.00, rank ~1.2–1.4, at every congestion level
  (n=188 at backlog ≥30). The mechanistic channel never closes; the
  behavioral SR (uncertified fraction) carries the entire transition.
- **P5L (exploratory):** 55 nontrivial genealogies, sizes to the cap
  (3 roots capped at 10; depth cap 4 reached). Cap-truncated — no
  exponent claim.
- **Drain physics observed:** draining against the live spawner cleared
  ~17 net tasks in 20 min — the collapsed-branch clearance rate
  (1−α)·μ in the flesh; at α=1 it would never finish ("load reduction
  alone cannot restore").
- **Forensics — the collapse is DYNAMICAL, not a context property.**
  Static reconstructions of the dirty window (11k chars of repair-format
  lines) cost almost nothing: clean 0.80 / repair-format-correct 0.80 /
  repair-format-wrong 0.75 exo accuracy, no think-blocks in long
  generations — vs 0.09 in the run at l=0.75. A snapshot of junk is
  nearly harmless; the runaway requires the model's own malformed output
  re-entering and being conditioned on, iteratively. The instability
  lives in the loop, not in the state — RSC's ungated-re-entry claim in
  its purest measured form. (Next-seed text logs — observability patch
  committed — will trace the window's actual decay path.)

Scope: one realization (seed 0), one model, caps as logged. The
mean-field spinodal reference from the measured state-dependent service
law is the outstanding analysis; more seeds are cheap (~3 h each).

### E4 at n=4 (seeds 0–3, 2026-08-25 — 1,809 tasks total)
All seeds untruncated; text logging active from seed 1. The multi-seed
picture (analysis `e4_analyze.py`, summary `runs/e4_summary.json`):

- **The collapse reproduces 4/4 with two markers per seed** — onset
  (P_u ≥ 0.5) and runaway (P_u ≥ 0.9 with backlog growth): seed 0
  0.75→0.85, seed 1 0.60→0.85, seed 2 0.85→0.95, seed 3 0.40→0.60. Every
  runaway lies below l=1 (median 0.85); the gap between the markers is a
  **metastable window** — sustained elevated-uncertified operation with
  ZERO backlog growth (seed 1 hovered at P_u ≈ 0.5 across three dwells
  before snapping; seed 2 ran fully lucid to 0.75, partial at 0.85, then
  ran away). One-sided scatter + hovering below the fold = the
  fluctuation-escape signature of a metastable branch.
- **Hysteresis 4/4**: every down-branch pinned at P_u=1.00 with backlog
  growing to l=0.40. **Partial cures fail 4/4**: reset_ctx pooled
  P_u=1.00 (n=155); reset_drain pooled P_u=0.85 (n=62), backlog
  re-growing. **Control 4/4**: α=0 never developed backlog anywhere
  (q_end=0 in all 44 dwells); its P_u is lateness-driven, continuous, and
  reversible, with a mild down-branch content echo (~0.3–0.4 mid-l)
  washing out by l=0.40.
- **Mechanism, revised by the text logs (an honest correction):** the
  seed-0 forensic suggested degenerate self-output; seeds 1–3's logged
  re-entrant text is largely WELL-FORMED — clean answers, many correct,
  with repair-genealogy perseveration. The collapse closes through TWO
  coupled channels with seed-dependent mix: timing (late → uncertified →
  offspring → later) and content (junk → errors → uncertified →
  offspring); seed 0's l=0.75 dwell was the pure-content extreme (acc
  0.09, zero lateness), seeds 1–3 lean on timing with moderate content
  degradation (post-runaway exo accuracy pooled 0.49 vs 0.80 baseline;
  static-window controls 0.75–0.80). The static-vs-loop contrast stands;
  the "degeneracy attractor" phrasing does not survive n=4 and is
  retired.
- **Certification at ceiling at every congestion level** (0.974–0.996,
  rank ~1.2, n=1,282 α-arm tasks; n=757 at backlog ≥30). **Genealogies**
  (keyed per seed): 211 trees, 681 offspring, 14 trees at the 10-cap —
  cap-truncated, no exponent claim.
- Figure `workspace_loop.pdf` regenerated at n=4: pooled cycle + faint
  per-seed up-branch steps; panel-C "closed loop" bar redefined as
  post-runaway exo accuracy, seed-aligned (0.49).

## Gap 2 CLOSED — the quantitative closure computes E4 (2026-08-25)
Two-layer analysis, all ingredients measured from statistics disjoint
from the collapse (`e4_closure.py`, `e4_reduced_model.py`):

- **Measured ingredients:** realized branching b=0.584 (genealogy
  bookkeeping); service law strongly context-dependent in-run (6.6 s at
  ctx<500 → 25.2 s at cap; E4's 10.95 s calibration was warm-cache
  optimistic, so E4's effective deadline depth was θ≈2.7, not 6 — an
  honest experimental note); content-error law P_err(j) as a logistic in
  the recent JUNK-DEPOSIT fraction (wrong answers + repair lines
  contaminate; late-but-correct answers leave no junk — the
  mechanism-grounded state variable, fitted on 1,769 task pairs).
- **Stationary skeleton:** the extended two-component self-consistency
  (content j-loop nested in the load x-loop) has a fold — labeled
  skeleton only, since the experiment runs 12-arrival transients.
- **The quantitative test — protocol-faithful reduced model, ZERO
  parameters fitted to the collapse:** E4's exact ramp simulated with the
  measured service/window-fill/P_err laws and the design spawn rules
  verbatim, 200 replicas/arm. Feedback arm: 183/200 collapse, runaway
  MODE 0.85 = the measured median, support 0.60–1.05 covering all four
  measured runaways with real mass; down-branch pinning 200/200 (measured
  4/4). Control: 0/200 collapse (measured 0/4). Stated residual, left
  untuned: the control's final-dwell P_u over-predicted (0.40 vs 0.17,
  transient-lateness detail).

## Gap 3 IN FLIGHT — E5, emergent alpha (pre-registered, predict-then-measure)
`e5_emergent.py`: no injected alpha — a self-verification retry policy
(model checks its own answer; rejection re-queues one retry, max 2) makes
the branching ratio b = P(reject) an emergent, congestion-dependent
property; service-matched no-requeue control; the self-check doubles as
an endogenous certification gate (coverage q and false alarms measured
per congestion state). Protocol: calibration (varied-window service +
clean/junk veto rates) → the reduced-model PREDICTION committed to git →
then the ramp. P1E–P4E in the docstring; the sub-critical outcome is a
reportable designable-safety statement.

## Gap 3 CLOSED — E5 emergent alpha: the committed forecast held, and the
## gate taught something new (2026-08-26, 01:47)
2 seeds × 2 arms, 529 tasks, ramp 0.40→1.05→0.40, T_d=101 s. The
prediction (commit `00a619a`, BEFORE the ramp): near-critical but mostly
sub-critical — modal outcome 0/2 collapses, bounded degradation, control
never collapses. MEASURED: **0/2 collapses, both arms, both seeds** —
P_u 0.00–0.33 per dwell, backlog never above 1, zero lateness anywhere,
workspace certification 0.99 throughout. The predict-then-measure arc is
complete on BOTH sides of the boundary: the same closure machinery that
predicted E4's collapse (imposed kernel b=0.584 → collapse below
capacity, verified 4/4) predicted E5's stability (calibrated emergent
kernel → sub-critical, verified 2/2). The theory discriminates safe
from unsafe re-consumption policies, with the stable-side prediction
committed in advance.

Honest scoring of the forecast: the structural calls all held (0/2
collapse ✓, control stable ✓, low fixed point ✓); the predicted
degradation LEVELS were too pessimistic — the model's lateness channel
(service scaled ×1.34) never materialized (late=0.00 measured), and the
predicted down-branch echo (P_u ~0.7) appeared only as transient error
bursts (one dwell at 0.69) that self-recovered without ignition.

**The new finding — live self-verification coverage is ~7×, not 2×,
worse than benchmarked:** calibration measured coverage 0.50 on planted
exogenous errors; IN-RUN coverage on the model's OWN errors was
0.06–0.08 (5 retries fired in 267 policy-on tasks; b_eff ≈ 0.02,
below even the clean-window calibration). The generator and its
verifier, sharing weights and window, agree on the same mistakes. The
offline-benchmarked gate quality q is not the q the loop gets — a
directly measured instance of the paper's certifier-inherits-the-
decoder's-constraints point, and a design warning for self-verification
architectures. (Also: the elicitation itself was fragile — the naive
verdict prompt parsed 0.00 under a clean fact-window; the few-shot
anchored form, probe-selected, parsed 0.96–1.00 in-run. Format
compliance of a certifier is window-mode-dependent.)

## E6 COMPLETE — the gating-exit threshold (seed 0 as-executed + seed 1
## protocol-faithful; verdict at the end of this section)
Predictions committed pre-run (`2ac26c2`): closed form q* = 0.661;
protocol-faithful reduced model crossing ~0.78 (content channel drags
recovery); predicted pattern PINNED/PINNED/PINNED-or-slow/EXIT at
q = 0.40/0.55/0.70/0.85.

- **Seed 0 (partial — host reset killed the 0.85 phase):** PINNED at
  0.40 (B 11→27), EXIT at 0.55 (27→17), EXIT at 0.70 (17→10). The
  measured crossing sits in (0.40, 0.55) — BELOW both predictions. Two
  protocol caveats recorded: the rig re-ignited only on weak backlog
  (deviating from the predictor; fixed for seed 1), and the post-hoc
  as-executed predictor variant still gives 0.55 only a 2% exit — the
  discrepancy is genuine, not bookkeeping.
- **Diagnosis (from the banked per-task records):** this realization
  ignited on the TIMING channel with a clean window — accuracy 0.82–0.87
  in every phase, so the model's content-poisoned-ignition assumption
  did not apply; and the stale backlog's offspring budgets were
  part-exhausted (measured spawn ~0.17/served vs 0.36 modeled). Both
  effects make the real gate MORE effective than modeled. Precise
  statement so far: the sharp pin/drain threshold EXISTS (the design-rule
  structure is real); the load-side exit precedes lucidity (P_u = 1.00
  from stale-task lateness while draining); the threshold LOCATION is
  realization-dependent through the ignition channel mix — the
  content-corrected closure needs the channel composition as a state
  variable, not a fixed law.
- **Seed 1 (corrected, protocol-faithful — COMPLETE):** PINNED at 0.40
  (B 25→47), PINNED at 0.55 (47→55), AMBIG at 0.70 (55→41, slow drain),
  PINNED at 0.85 (41→43). **Against the committed model prediction
  (PINNED / PINNED / PINNED-or-slow / EXIT): 3/4 phases match exactly,
  and the fourth is explained by a measured confound** — per-phase true
  utilization drifted from the designed 0.75 to 0.89 by the 0.85 phase
  (mean service 25.2 s → 30.0 s, post-reset host load), erasing the
  drain margin; at ρ ≈ 0.89 no gate coverage can drain, so the 0.85
  PINNED verdict is a ρ-drift artifact, not a gate failure.
- **The two-seed reconciliation (all from measured quantities):** seed 0
  (as-executed protocol) gated a SHALLOW, budget-EXHAUSTED stale backlog
  at steady ρ ≈ 0.70–0.73 → real spawn rate half the model's → exits at
  0.55/0.70. Seed 1 (protocol-faithful) gated re-ignited backlogs with
  FRESH offspring budgets → matches the model. The apparent
  seed-disagreement dissolves into three measured state variables: true
  utilization, backlog depth/offspring-budget composition, and ignition
  channel mix.
- **E6 verdict for the theory:** the sharp pin/drain threshold EXISTS —
  the design-rule structure (insufficient coverage pins, sufficient
  coverage drains, near-threshold drains slowly) is real, and both seeds
  pin at q = 0.40 at matched ρ. The idealized closed form q*(α, θ)
  treats utilization, budgets, and channel mix as constants; the
  experiment shows the threshold location moves with all three, and the
  protocol-faithful reduced model WITH measured inputs tracks reality
  (3/4 + explained). The design rule survives as structure; its
  calibration must be state-resolved. Also reproduced in every phase:
  the load-side exit precedes lucidity (P_u = 1.00 from stale lateness
  while draining).

## E11 — RSC ingredient curves in PRODUCTION traces (2026-08-28,
## observational, plan-first; passes 1 + 2 both committed as-is)
Data: 16 local Claude Code sessions ≥ 50 tool calls (22,792
tool_use→tool_result pairs), aggregate-only extraction (no text read).
Question: are the rig's two collapse ingredients present in production?

- **The feedback kernel: PRESENT.** P(error | previous error) = 0.078 vs
  P(error | previous ok) = 0.021 — a 3.7× conditional amplification
  (n = 514 / 22,262 transitions).
- **Cascades: over-dispersed vs the geometric (iid) null.** Error runs
  ≥ 2: 29 observed vs 11.7 expected; ≥ 3: 5 observed vs ~0.3 expected.
- **The service law: PRESENT** (pass-2 corrected measure, LLM step
  latency via the parentUuid chain): median 3.6 s at < 20k ctx tokens →
  10.8 s at ≥ 180k (n = 11,726 in the top bin) — the production analog
  of the rig's 6.6 → 25.2 s law.
- **Within-session error progression: NULL** (deciles flat ~0.02;
  late-minus-early positive in 7/16 sessions). Consistent-with (not
  confirmation of) the theory's GATED regime: these sessions have a
  human certification gate in the loop, and the gated regime is exactly
  where junk should not accumulate.
- Pass-1 design errors reported and corrected in a separately
  pre-committed pass 2 (I1 absolute-ctx binning confounded by
  between-session variation; I2 measured tool latency, not LLM step
  latency). Files: `e11_production_traces.py`, `e11b_production_traces.py`,
  `runs/e11{,b}_production.json`.

## The 2026-08-28 validation program — designs + committed predictions
## (rig runs in flight; results land in their own sections)
- **E7 fluctuation precursors** (the designed protocol the inconclusive
  e4_precursors pass called for): matched-load presence-vs-absence —
  feedback arm α = 0.8 vs CONTROL α = 0 (no fold at identical load),
  both pre-filled to the congested service law, paired exo schedules,
  confound-proofed statistics (exact-unbiased Bernoulli excess variance;
  degenerate AC1 windows dropped; primary order parameter = detrended
  queue length). Committed prediction (b3ba4bf): feedback τ_qvar +0.296,
  τ_qac1 +0.142, ignition 66%; control τ ≈ 0, ignition 0/200.
  Mid-run calibration amendment (381f68c, before any arm completed):
  λ and T_d set from measured service so ρ = 0.45 and θ = 2.62 hold in
  TRUE units (first launch's 25.2 s planning constant vs 16.5 s measured
  — the E6 ρ-drift failure mode, now closed structurally).
- **E8 separatrix** (graded compound shocks from the collapsed state,
  sequential protocol): committed prediction (23e01ad) P(EXIT|f)
  0.21/0.18/0.31/0.55/0.95 → separatrix f* = 0.75; two-component
  ordering window_only 0.15 < backlog_only 0.61 < compound 0.95.
  Design history: ρ_hold = 0.55 rejected (cures re-ignited 77%).
- **E9 α×θ cusp map**: three scan generations (time-limit artifact →
  horizon-dependence lesson → the rig-horizon map, all committed).
  The committed map (2100 s horizon): the wedge appears between
  α = 0.15 and 0.20 nearly θ-INDEPENDENTLY (mean-field α* sweeps
  0.433→0.160 — the content channel holds the wedge open below it);
  width grows with α and θ as cusp geometry predicts. Rig spot-checks
  committed (84a74c2): S1/S2 θ-pair (T_d 33 vs 132 at ρ 0.65: IGNITED
  vs CALM) and S3/S4 α-pair (quench 0.8→0.2 vs keep 0.8 at ρ 0.55:
  EXIT vs PINNED — the wedge boundary must MOVE with α).
- **E10 second model** (lens-free E4 replication on a different family):
  queued; Llama-3.1-8B-Instruct-4bit download in progress.

## E7 COMPLETE — fluctuation precursors (3 seeds, paired arms; the
## primary replicates with one drift-explained exception)
Committed prediction (b3ba4bf): feedback τ_qvar ≈ +0.30 / control ≈ 0;
feedback ignites ~66%, control never. Calibration amendment (381f68c)
holds ρ = 0.45, θ = 2.62 in true units at arm start.

Measured (per arm; primary = τ_qvar, pre-onset segment):
- seed 0: feedback +0.494 (ignited, n = 62) vs control −0.050
  (no ignition, n = 82) — **paired contrast +0.544, clean pass;
  the control landed within 0.002 of the model's predicted value.**
- seed 1: feedback CENSORED (ignited at task 34 < the pre-registered
  40-task minimum — the model gave this outcome ~10% probability);
  control flat on the primary (τ_qvar −0.067), no ignition (n = 93).
- seed 2: feedback +0.593 (ignited, n = 56; variance growth in thirds
  +3.14) vs control **+0.834** (no ignition, n = 76; thirds growth
  +0.43) — the pair FAILS on τ.
- Ignition tally: feedback 3/3 (2 analyzable), control 0/3.

**Post-hoc drift diagnostic (labeled as such; e7_drift_diagnostic.py):**
seed 2's control arm's true utilization drifted 0.39 → 0.62 during the
hour (service 17.8 → 28.4 s, evening host load) — the largest drift of
all six arms; a ρ-ramp in an α = 0 queue produces a rising variance
trend with no fold. Dose-response across seeds: mild drift (s0 0.45→
0.51, s1 0.53→0.57) → flat controls; large drift → spurious control
trend. The rank-based τ is magnitude-blind: the feedback arms' variance
GROWTH is 7–18× their controls' in both analyzable pairs
(d_qvar_thirds 0.76 vs 0.04; 3.14 vs 0.43).

**E7 verdict:** the precursor signal (rising queue variance on the
metastable approach) is present and strong in BOTH analyzable feedback
arms and absent-or-drift-sized in every control; the pre-registered
τ primary passes 1/2 pairs, with the failing control's trend
quantitatively attributed to measured utilization drift. Honest
methodological caveat for the paper: wall-clock rigs carry drifting
host load; a τ-on-ranks primary is vulnerable to it — magnitude
measures and drift regression belong in the next protocol revision.
The AC1 secondary scatters across control replicates (−0.16/+0.46/
+0.13) and is non-discriminating at n = 1 per arm, as the model's
p_sup = 0.62 foretold.

## E8 COMPLETE — the separatrix measured (seed 0, sequential graded
## shocks; matches the committed prediction on every scored point)
Committed (23e01ad): P(EXIT|f) 0.21/0.18/0.31/0.55/0.95 → f* = 0.75;
ordering window_only 0.15 < backlog_only 0.61 < compound 0.95.
(Attempt 1 aborted — the MacBook unplugged, hibernated 12.6 h inside a
verdict phase at 1% battery; archived, restarted fresh 2026-08-29.)

Measured verdicts (E6 slope rule, hold/verdict at ρ = 0.35):
compound 0.00 PINNED (B 32→39) · 0.25 PINNED (28→34) · window_only
PINNED (27→31) · 0.50 AMBIG (13→11) · 0.75 VOID (the 0.50 shock +
hold drained the state below threshold before the shock — the
sequential design's known self-cure path, ~4% in the model) ·
backlog_only AMBIG one task from exit (23→0 shock; junky window
rebuilt to 6, EXIT needed ≤ 5.6) · compound 1.00 EXIT (0→1, stayed
clean).

- **Monotone boundary** ✓ (PINNED → AMBIG → EXIT along f); crossing
  bracketed in (0.5, 1.0), consistent with f* = 0.75; the exact
  crossing point is the one unscored prediction (VOID).
- **Two-component memory, the predicted ASYMMETRY included** ✓:
  window-only decisively pinned (backlog regenerates junk),
  backlog-only nearly exits (junk rebuilds only a trickle at ρ 0.35),
  compound exits — window_only < backlog_only < compound, exactly the
  model's 0.15 / 0.61 / 0.95 ordering.
- Falsifiers dodged: boundary monotone; no axis shock matched the
  compound. A seed-1 run can recover the 0.75 grid point.

## E9 spot-checks COMPLETE — 2/4 clean confirmations; 2/4 unresolved
## at drift-shrunk boundary margins (the program's dominant systematic,
## now named)
Committed (84a74c2): S1 IGNITED / S2 CALM / S3 EXIT / S4 PINNED
(modal 81–87%). Measured: IGNITED / IGNITED / PINNED / PINNED.

Coordinate diagnostic (e9_spot_diagnostic.py — the spot rig hard-coded
λ = ρ_nom/25.2 s; afternoon services ran 24.5–33.0 s):
- S1 ρ_true 0.70 vs l_up 0.564 → IGNITED on-map ✓ (deep in-region).
- S4 ρ_true 0.54 vs l_down 0.159 → PINNED on-map ✓ (deep in-region).
- S2 ρ_true 0.70 vs l_up 0.767 — designed margin 0.12 shrank to 0.07;
  measured IGNITED. Marginal miss inside boundary noise.
- S3 ρ_true 0.72 vs l_down(α=0.2) 0.75 — designed margin 0.20 shrank
  to 0.03(!); measured PINNED. Unresolved: the spot landed ON the
  predicted α-quenched boundary, where verdicts are coin-flips by
  definition.
The α-motion claim (l_down 0.16 → 0.75 as α quenches 0.8 → 0.2) is
NOT contradicted — S3 sat at the moved boundary's edge rather than
clear of it — but the designed sharp EXIT/PINNED contrast was eaten by
drift. Re-run candidate with E7-style live calibration.

**The named systematic:** host service varies ±50% between sessions
(18.6 s yesterday morning → 33 s this afternoon), moving every ρ
boundary by ~±0.15. E7 closed it with live calibration; E8's slope
verdicts were robust to it; E9's fixed-margin spots were not. Every
future wall-clock rig phase calibrates in-run.

## E10 + E10b COMPLETE — the second architecture (Llama-3.1-8B q4 via
## Ollama, lens-free): collapse TRANSFERS, and the serving stack's cost
## model is a control parameter
Four porting traps found and committed pre-verdict (warm anchor;
cache-poisoned calibration; chat-template junk-flood; per-arm cache
regimes) — each archived with its diagnosis.

**E10 attempt 4 (burst protocol, the scored run):** P1 FAILED — no
load collapse to l = 1.05. Mechanism localized by the service profile:
post-cap exo tasks served uncached (~6.2 s) but repair offspring rode
Ollama's prefix cache (sub-second) — the cascade's re-entrant work was
nearly free, so its branching stayed subcritical. Error-channel
feedback-specificity confirmed anyway (P_u 0.62–0.95 vs control
0.08–0.33) plus CONTENT hysteresis without queue hysteresis
(down-branch P_u 0.95 at l = 0.60 vs 0.62 up).

**E10b (sustained pressure, both arms PRE-CAPPED — which turns out to
remove the cache globally: truncation shifts the prefix every task;
repairs 4.82 s ≈ exo 4.47 s; the correct correspondence to the
always-uncached Qwen rig). Two-branch prediction committed (ce8d242);
BRANCH A landed:**
- feedback: RUNAWAY in the FIRST phase — B 0→26, P_u 0.84, at
  exo-only TRUE ρ = 0.79 (λ 0.177/s × s 4.47 s), driven supercritical
  (effective ~1.4) by its own offspring;
- control: NO runaway anywhere — B 0→0/0→0/0→1 at exo true ρ up to
  0.84, i.e. HIGHER true load than the feedback arm's; P_u ≤ 0.47.
- Verdict: sub-capacity, feedback-specific collapse on a second model
  family with no lens and no certification instrument. P1 ✓ P3 ✓
  (P2/hysteresis not probed in E10b — open follow-up).

**The pair's joint finding:** same model, same feedback law — collapse
in the uncached regime, none in the cache-subsidized regime. Prefix
caching suppresses θ_effective for re-entrant work (α_eff(1+θ_rep) < 1)
— a load-side gate, the dual of certification on the content side. The
theory predicts its own mitigation, and the two runs measured both
sides of it.

## Fixes (all committed)
tokenize schema (`text` not `prompt`) · intervene response
(`intervened.text`) · E1 occupancy echo → question-span discipline ·
E2 Q/A framing → flat fact stream · load pool 64→96 nouns ·
**serve.py tail-readout patch** (`patches/serve_tail_readout.patch` — caps
the [layers × positions × vocab] logits transient that OOM'd the Mac;
side-effect: ~5× faster steps) · **atomic-session resume** (a mid-session
kill re-runs the session; summary dedups last-record-per-step) ·
`start_server.sh` idempotent server launch.

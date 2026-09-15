# R084 capture endpoint — final Codex second opinion

15 September 2026. Reviewer: Codex, `GPT: R052 Entropy paper`.
Request: Unimog `prompts/2026-09-15_r084_capture_endpoint_codex_second_opinion.txt`
at `8ec5a20b`, Q1–Q7; xs request from Claude R084 at 12:54:57 PDT.

## Scope and system readback

Each trial supplies explicit raw-text token ids to a fresh stream, with one
full-prefix `extend`. The instrument saves native bfloat16 post-layer residuals
at the last marker token and final-position answer logits. H3 edits all three
marker tokens inside that same pass, before capture and downstream computation.
R1 is a CAL-trained coherence decoder; R2 is a separate linear target–foil
projection. Entropy SI's `ccc0da6` amendment makes R3 correctness a closed-set
comparison over the 128 frozen bank ids and confirms native bfloat16 and the
three marker positions. This review uses that amended contract.

Reviewed the complete endpoint patch, patch generator, tail patch, packet
builder, capture client through `481d8a5`, its 11 offline tests, upstream
`model.py` and `interventions.py`, startup/route wiring and GDN dispatch patches,
and the complete `parity_20260915T123629.json` and `.jsonl`. Relevant protocol
sections: §§4, 6.2–6.3, 11–12 plus the complete `ccc0da6` amendment. The earlier
protocol version was read in full for the closed cost review. The newer decoder,
PILOT analysis, bank content/auditor process and H3 driver are outside this read.

Review only: no server start or request, model load/inference, capture, fit,
scientific simulation, cloud operation, deployment, freeze or push. Claude R084
owns implementation; Entropy SI owns protocol decisions. Only this review is
changed in RSC. Earlier cost, JOB D and Melcon opinions remain closed.

## Numbered findings

### 1. BLOCKING before CAL — persist the newly required vocabulary rank (Q5–Q7)

The amended §6.3 requires the target's open-vocabulary rank. The endpoint returns
only requested logits, top-k and a digest of the full logits; the new run writer
stores those reductions, without ranks (`capture_endpoint.py:317–337`,
`capture.py:500–524`). When a target is outside the top 1000, its exact rank is
not recoverable from these saved values. A digest is not the logits themselves.

Compute the rank while the complete final vector is available, return and persist
it for each required target (or every requested id), and declare deterministic
tie handling consistent with the other reported rankings. Retain the top-1 id
already available. Cover a target below the saved top-k in an offline test.
This is a capture-time data omission under the accepted amendment, not a request
to reconsider closed-set R3. The 128 answer logits and variant logits do support
the primary correctness, margin and descriptive variant comparisons.

### 2. BLOCKING before CAL — enforce the 20-prompt parity gate (Q2, Q6–Q7)

`parity --n 1` can produce `PASS`: its verdict only requires nonempty groups with
all rows passing (`capture.py:319–321`). `matching_parity` accepts that label
without checking `n_prompts`, required comparisons or the JSONL (`374–388`).
An offline fixture confirms that a clean one-prompt PASS is accepted. That does
not enforce §4's 20-prompt requirement.

Separate a diagnostic report from a qualifying gate, require at least 20 distinct
prompts and the declared per-prompt comparisons, validate their counts/status,
and bind the report to its evidence file. Do not permit an incomplete or absent
field to count as a pass. The supplied 20-prompt report meets the reported count
requirement; this finding concerns the production admission rule.

### 3. BLOCKING before the next qualifying gate — guarantee the zero-dose sham (Q3–Q4)

`_edit_fn` computes `h + 0*d`, then `_apply_edits` casts/scatters it
(`capture_endpoint.py:198–233`, `model.py:69–87`). The exact contract has a
counterexample: for native bf16 `[-0.0, 1.0]`, a zero-dose steer with zero vector
changes uint16 words `[32768, 16256]` to `[0, 16256]`. The existing negative-zero
test checks only the count. G2's zero observed negative zeros do not prove an
identity operation for subsequent prompts.

Also, a validated `steer(alpha=0, target_norms=[1])` with `h=[1,1]` and `v=[1,0]`
writes `[2,1]`: `target_norms` replaces lambda. Make the modes unambiguous. A sham
must take an exact identity path, preserving native bits and logging zero written
norm without evaluating a possibly invalid delta. Either reject a conflicting
norm-target/zero-dose request or explicitly define zero dose to override it.
Keep replacement `patch` separate from lambda-dose modes. Add native-bit tests
through the scatter path, including signed zero and the accepted norm-mode
parameter combinations. Then rerun the qualifying development gate under the
changed, committed implementation. No scientific threshold change is needed.

### 4. BLOCKING for qualifying run provenance — bind the gate to loaded code and runtime (Q1, Q6)

`versions()` hashes endpoint bytes at import, but hashes `serve.py` only when
first queried and resolves the model snapshot from the current local HF cache.
The client hashes files on disk. Those observations alone do not identify all
bytes already loaded in a long-running process. `model.py`, `interventions.py`,
the GDN patches and upstream dirty state are absent from the recorded hashes.
The matching keys omit upstream HEAD, OS, Python/NumPy and Metal configuration
(`capture.py:370–388`). An offline fixture changes OS, Metal architecture and
upstream HEAD while retaining the compared fields; the report is still accepted.

Use a startup manifest for the actual resolved snapshot/lens and imported source
paths/hashes, upstream HEAD plus permitted patch/dirty manifest, runtime versions
and GDN dispatch state. Refuse an unexplained source/runtime change or require a
new gate; keep the same identity on resume. A fresh process from the pinned files,
with its startup receipt bound to the gate, is sufficient: no memory-dumping or
per-trial rehash of model weights is requested. Record the resolved lens even if
startup selected it without `JLENS_PATH`. Use content hashes as the identity;
absolute paths are useful location metadata.

The supplied report is development evidence: it records uncommitted capture
files and an earlier client digest. The current non-development guard correctly
rejects that report for those reasons. A qualifying gate must be rerun after the
fixes are committed, with the full identity and evidence checks. This review
does not establish the currently running server's loaded-code identity.

### 5. SHOULD FIX in the next parity log — retain evidence, not only booleans (Q6)

The full JSONL has one header and 135 comparison rows. Each row retains gate,
prompt number, label, booleans, mismatch and negative-zero count. It contains no
trial token ids, marker/readout positions, complete edit request, or paired
response digests. Thus the brief's “every token id per trial” does not describe
this parity artifact. G1–G4 counts can be audited; their byte comparisons cannot
be independently recomputed from this log.

Save the prompt manifest/ids once, reference it from every comparison, and retain
request/edit/position data and both residual/full-logit digests, plus the compared
reduced outputs or canonical hashes of them. Hash the evidence into the report.
The new `run` writer does save trial ids and token ids; that is an improvement
already present, not a missing feature in the current capture-run format.

### 6. SHOULD FIX before H3 — freeze norm matching across the three positions (Q4–Q5)

For finite, well-conditioned inputs, the implemented arithmetic is faithful:
`swap_delta` scales `patch_swap_rows(...,1)-h`; ablation scales the negative
ridge-projection term; the offline upstream-form test passes. The raw upstream
swap alpha is correctly not treated as a linear dose.

§11 says per-layer matching, while `target_norms` accepts one norm per position.
Matching each of the three target-swap row norms is a reasonable, more specific
implementation and would also match the combined layer norm in exact arithmetic.
It must be stated by Entropy SI: retain a trial/layer/position mapping to the
trial's own target-swap run, and define how any undefined position affects the
whole control. Later layers in a joint run see earlier edits; use the respective
joint target run's recorded norms, not independently edited single-layer norms.
The off-target delta is calculated on its own evolving stream. Rescue amplitudes
and the norm used for their CAL median likewise need this position convention.

Match to the target operation's **written** norm as the requested dose, but do
not promise exact equality after bf16 rounding. The saved diagnostics requested
1.0 and wrote 1.003309–1.006467; half/full swap ratios span 0.499824–0.508882.
Log requested, raw and achieved norms, mismatch and undefined flags. Freeze a
development-based tolerance/disposition before H3. An iterative search to hit a
written norm would change the algorithm and needs an explicit protocol decision;
it is not automatically required by these small development discrepancies. The
observed error is not proof of a bound or absence of outcome bias at other doses.

### 7. SHOULD FIX before nonzero H3 — reject invalid bases and nonfinite data (Q4, Q7)

`make_swap_basis` explicitly divides by the Gram determinant without a rank or
conditioning check (`interventions.py:164–179`). Distinct token ids do not prove
independent vectors. A small offline fixture with vectors `[1,0]` and `[2,0]`
produces nonfinite output; norm matching flags the position undefined but does
not preserve its input, because `0*NaN` remains NaN. No actual bank pair has been
shown singular by this review.

Validate vector/patch finiteness, Gram rank/conditioning and output/logit
finiteness, with an explicit failed-trial reason. The raw-delta floor is not a
basis-conditioning test. Preserve a skipped finite row exactly; do not silently
replace an ill-conditioned swap by a ridge or pseudoinverse without an owner
decision about the operation. JSON serialization will reject many nonfinite
scalar responses already, but that is not a complete or informative numerical
failure policy. This is an H3 robustness correction, not evidence of bad CAL
baseline captures.

### 8. SHOULD FIX — verify all saved observables and run completeness (Q6–Q7)

`verify` checks only residual-row hashes (`capture.py:535–550`); it does not check
top/answer/variant logits, logsumexp, duplicate ids/locations, missing manifest
rows or selection completeness. A PASS is therefore a residual-storage checksum,
not verification of a complete run. The full-logit digest cannot verify the
stored reductions by itself. Hash all stored observables, validate ids/shapes/
finiteness and coverage against the declared selection, and distinguish a valid
partial benchmark/resume from a complete dataset. No synthetic decoder test or
residual-only checksum should be cited as validation of the measured capture set.

### 9. NOTE — Q1's execution structure and Q5's positions/dtype are sound

`_run` creates one new stream and performs one extend over the full supplied ids.
Validation rejects overlength instead of truncating. `set_edits` groups by layer;
edits run after that layer's forward, before its residual capture and downstream
layers. Positions are global, with start offset zero here. The endpoint retains
pre-final-norm residuals; the final-position logits use the model's final norm
and LM head. The GPU lock covers compilation, pass and readout. Requests do not
write weights or persist sessions; stream caches are per request. “Read-only”
does not mean literally no process state: dtype/version caches and the global
GDN inference flag change.

`packet.py` checks full joined-token identity, uses offset boundaries for all
three marker tokens, and reads the last. The accepted amendment resolves the
previous fp16 wording and marker ambiguity. `j_lens_vectors_lite` implements
rows `W_U[t] @ J_l`, using an fp16 matmul and returning float32; the output label
does not mean fp32 multiplication. Layer 63 uses the unembedding row directly.
R2 must decode bf16 bits to numerical float32 before projection and retain this
vector identity. Its normalized secondary lens logit still needs the separate
`norm(J_l h)` operation; the vector dot product must not be substituted for it.
Residuals plus the retained lens/model support that later readout. The selected
positions/native dtype do not themselves establish a bias in H3 or R2.

### 10. NOTE — G1 is a valid narrow gate; independent reference and H3 gate are distinct (Q2–Q3)

G1 satisfies the literal empty-edit comparison: absent edits and `[]` use the
same forward path, with an empty edit dictionary. G3 exercises native row
replacement/casting; G4 checks the reported repeat behavior across prompts.
These are useful regression checks, not independent evidence that the shared
forward/readout is correct. Add an independent reference diagnostic using the
same explicit ids and a documented kernel/precision path, comparing final logits
and applicable residuals, with a justified tolerance if kernels differ. Do not
replace the required same-path bitwise gates by tolerance tests.

The brief's suggested uncached reference is not necessarily the ops fallback:
`MLXLensModel.__init__` attempts `patch_gdn_custom`; its cache-free path uses a
custom Metal forward, while cached streams use the stock path and set the global
inference flag. Record the actual dispatch and isolate/reset reference state.
An arbitrary tolerance cannot be declared validated without a comparison; none
was run here. Lack of that extra reference is not a new §4 blocker by itself.

The supplied G2 uses joint layers 23/41/57 on 20 prompts and single layers 0/62/63
on five prompts. That is development coverage, not the eventual selected H3
layers. Rerun sham/self-patch checks on the real selected layers and marker
positions before H3, retain per-trial sham equality, and stop on any mismatch.
Selection requires CAL, so that H3-specific gate is not a prerequisite to CAL.

## Offline verification and evidence limits

- All 11 existing `test_capture.py` tests passed (1.42 s), in the upstream venv,
  with HF/Transformers offline, bytecode writing and pytest plugin autoload off,
  and pytest's cache provider disabled. No model load occurs in these tests.
- Bounded additional checks reproduced signed-zero loss through `_apply_edits`,
  nonzero norm-target editing with alpha zero, admission of a one-prompt PASS,
  admission after omitted runtime/upstream changes, and the singular-basis
  undefined-but-nonfinite result. They used tiny arrays and temporary report
  fixtures, not model inference or scientific runs. Production files were not
  modified. The inputs and outcomes are given in findings 2–4 and 7.
- All 136 JSONL lines and the full JSON report were read. Counts agree:
  G1 20/20, G2 75/75, G3 20/20, G4 20/20; every saved comparison flag is true and
  every saved negative-zero count is zero. The reported 175 calls equal 20
  baselines + 135 comparison calls + 20 diagnostic calls in the read client.
  The 183.6 s duration is the author's recorded measurement, not a Codex timing.
- Upstream HEAD independently verified as
  `745a3a894be7043ae5eb7dbbdcec44b68b819411`. Its model/interventions/GDN files
  match HEAD. Tracked modification: `serve.py`; the endpoint and lens material
  are untracked as expected. Applying tail then capture patches to a temporary
  pristine `serve.py` reproduces both working files byte for byte, with the same
  report hashes: endpoint `206389e47b7c492c4d7e60fb14aa28483ca27fb84538385b8ac3f7995cff680a`,
  serve `48dc24d42fc2fbf07d71ed5d1d6e9c26d9037587071a7c68431454b753711569`.
- Current capture patch and packet hashes match the report. Current client
  (`481d8a5`, 588 lines) is
  `53bab1f2376c23fb003b31530435560112569c93258bc74a91f5fa460c3377eb`;
  the report records `64b7e43e71974440d0862194e0d6034d1b1f39d057d29ee3a2ff8973d20da6aa`.
  Model/lens shard hashes, hardware and runtime fields were inspected as saved
  evidence, not remeasured from the live server or independently rehashed here.

## Verdict

**Not ready for CAL as committed.** The core single-pass endpoint, marker
construction and native-bfloat16 transport are acceptable. Resolve findings 1–4,
retain the next gate's evidence as in 5, and obtain a qualifying 20-prompt PASS
under the committed, pinned capture identity before CAL. Findings 6–7 and the
selected-layer sham checks gate H3; they do not require selecting H3 layers
before CAL. Extend run verification before relying on a completed dataset.

The existing owner decisions on clue auditors and capture machine still apply.
For a different machine, obtain its own recorded parity/reference evidence and
the owner's machine decision; the present Mac development report establishes
no cross-machine equivalence. This review authorizes no run, cloud expenditure,
protocol freeze or change in file ownership. Claude R084 owns disposition and
implementation; protocol interpretations return to Entropy SI.

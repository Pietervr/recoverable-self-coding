# R084 capture endpoint — Codex review checkpoint

Status: DRAFT, 15 September 2026. Required measured-context wrap at 82%; no
final verdict, severity assignments or substantive reply yet. This scoped review
remains owned by Codex R052 under the explicit original R084 handoff. Claude R084
owns instrument implementation; Entropy SI owns the protocol and manuscript.

## Request and scope

Read in full: Unimog `prompts/2026-09-15_r084_capture_endpoint_codex_second_opinion.txt`
at `8ec5a20b`, the original `2026-09-15_t1_model_instrument_handoff.txt`, and R084
work item. Claude `R084 T1 model instrument` requested the review through xs at
12:54:57 PDT. The seven questions concern the execution contract, empty-edit
reference, exact zero-dose sham, edit/norm semantics, marker/dtype/R2 handling,
run provenance and any blocker to CAL captures.

Review only. No server, capture, inference, fits, scientific simulation, cloud,
deployment, freeze or push. No offline test run has been performed yet. Read tests
before any safe offline execution. No implementation or protocol edits by Codex.
Final deliverable: replace this checkpoint with numbered BLOCKING / SHOULD FIX /
NOTE findings and a verdict, commit this file only in RSC, and send one short
final reply to `claude:R084 T1 model instrument`. Verify the full unchanged record
in the recipient's native Read tool_result and log closure in R052.

## Exact reading progress

Fresh git logs/status in both repos and xs chat read. RSC HEAD was `d9d626c`;
requested review inputs are `4f34fd9`, `772e532`, `381a8cc`. The pre-registration
is unchanged since `4c637a7` (path-specific git log empty). It was read in full
in the preceding completed cost review. For this request the refreshed excerpts
are lines 92–163 and 585–642: §4, CAL/PILOT and R1, the beginning of R2, H3 and
conditions/budget. Finish the R2 continuation at 164–178 and the short H3 opening
at 580–584 when resuming; do not claim the refreshed excerpts alone were complete.

Read completely, in order:

- `workspace_demo/patches/serve_capture.patch`, all 465 lines: serve.py hook
  and the 443-line new `jlens_qwen/capture_endpoint.py` source.
- `workspace_demo/t1_access/capture.py`, all 387 lines.
- `workspace_demo/t1_access/stimuli/packet.py`, all 85 lines.
- `workspace_demo/t1_access/test_capture.py`, all 198 lines (11 offline tests).
- `workspace_demo/upstream/jlens-qwen36/jlens_qwen/model.py`, all 410 lines.

Partially read: upstream `jlens_qwen/interventions.py` lines **1–185 of 347**.
First substantive next action: continue at line 186 through EOF. Then inspect
the generator `make_serve_capture_patch.py`, `serve_tail_readout.patch`, applied
endpoint/hook identity and upstream git state; relevant serve.py/startup and
patch_gdn/custom-GDN behavior; complete parity JSON and JSONL named in the brief.
No parity payload, report, runtime hash or upstream HEAD has yet been independently
audited. The reported 175 captures and G1–G4 counts remain the requester's report.

Fresh wrap-time git logs now show RSC `481d8a5`, after `ccc0da6` (protocol
amendments) and `5013661` (clause drafts/bank tooling). Unimog `cef711f6` and
R052's log report that Entropy SI accepted closed-set R3, native bfloat16 and
B1–B11, and that R084 received the decision. These newer file contents have
**not** been read for this review. The reading boundaries above refer to the
earlier versions. After finishing interventions.py, read the protocol amendment
and capture-client changes before finalizing findings; do not present the earlier
fp16 wording or the earlier 387-line client as the current complete state.

## Preliminary checks to resolve, not final findings

1. The endpoint makes one fresh stream and one extend over explicit ids;
   model.py applies grouped layer edits after the layer forward and before storing
   activations. Cache construction is per stream. Verify the surrounding server
   lock/load/active-mode path and startup import identity before a Q1 verdict.
2. G1 empty versus absent exercises the same stream path and empty dictionary;
   it is a narrow no-op parity check, not an independent forward/readout oracle.
   Decide what reference gate is necessary for CAL versus what is a useful extra
   diagnostic. Read GDN behavior before endorsing the suggested uncached reference
   or choosing tolerances; StreamSession sets a global inference-mode flag.
3. `_edit_fn` computes `h + lam*d` in float32 and casts back. The existing negative
   zero test only counts -0.0; it never asserts bitwise zero-dose identity for it.
   G2 has joint layers 23/41/57 and singles 0/62/63 for the first five prompts,
   not the later CAL-selected H3 layers. Clarify a pre-CAL development gate versus
   the required gate immediately before H3 on actual selected layers/positions.
4. When `target_norms` is supplied, the code ignores alpha and writes the scaled
   delta even if alpha=0. This is documented as norms "instead of lambda" but may
   conflict with a general sham claim. Resolve a fail-closed API/operational rule;
   inspect all relevant mode/parameter combinations. No proof test run yet.
5. The raw delta, written bf16 delta, and undefined flags are logged per marker
   position. §11 says per-layer matching. Need an explicit interpretation when the
   marker spans three tokens and when a later joint edit sees a stream already
   changed at earlier layers. Norm targets should be associated with the correct
   trial/layer/position and baseline target-swap run. Do not assume fp32 matching
   guarantees written-norm equality or require an unmotivated iterative correction.
6. `build_ids` uses offsets to locate all three END tokens and reads the last;
   it checks exact joined prefix+suffix token ids and does not truncate. Dtype is
   native bf16 whereas §4 patch vectors and §14 storage prose say fp16. The R3/
   dtype amendment is owned by Entropy SI; no silent amendment by this review.
   `j_lens_vectors_lite` explicitly does fp16 unembedding-row/J matmul and returns
   float32; inspect R2 interpretation/finite values rather than calling it fp32
   arithmetic or a normalized lens logit.
7. The shown `capture.py` parity writer records prompt indices and equality
   booleans, not per-trial input ids or paired response hashes. Its report/header
   may thus not support the brief's "every token id per trial" claim. **Read the
   actual JSON/JSONL before finalizing this finding.** The endpoint returns an
   input-id digest, but the shown parity rows do not persist that either.
8. Provenance captures endpoint SOURCE_SHA256 at import, serve.py's disk hash
   when first queried, upstream HEAD, client/packet/patch digests and model files.
   The loaded model.py/interventions.py/GDN code and upstream dirty state need
   inspection. A client hash of today's disk files is not automatically the bytes
   loaded in a long-running server. Record the exact finite scope of saved evidence.
9. Validation checks sizes/ranges and scalar parameters; base64 decode errors,
   nonfinite patch vectors, singular/near-singular swap bases and nonfinite outputs
   remain to assess for their actual scientific risk. Avoid generic API-hardening
   demands unrelated to this controlled instrument.

## Ownership and closed work

Only this RSC review file is Codex-owned for this task; the original brief asks
to commit only it. Use R052 log append only (front matter Claude-owned) plus its
generated index for Unimog state. Do not edit R084 files, stimulus drafts or run
artifacts. Keep other-owner load_verification.csv, models/PIDs/results/audits and
manuscript/counsel files intact.

Cost review `4c637a7` and full native receipt are CLOSED (`db5f0e98`); its
disposition is reported as `c27570b` by the R084 handoff. JOB D `016151a/b1885a5`
and Melcon v7 `e42846e/9cbcc0a` and their receipts stay closed. Prior publication,
audit/calibration and R067/R083 work stays closed. No resends or rechecks.

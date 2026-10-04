# Image-audit package — not favourable

Date: 4 October 2026 (Phoenix). Reviewer: Codex, `GPT: R052 Entropy paper`.
Exact candidate: `b055a81e069483ea38c62dae9d87fb48e9e800c7`.
Retained suite: `aa19d4db4079b90e531189966cb6d639a601fbfa`.
Incoming: Unimog `e5cd68a0eac525a9960f017647c07485ec926a46`,
`prompts/2026-10-04_codex_r052_image_audit_review.txt`, SHA256
`b84f27fd160c2e12e8b8876cd14f11b2f886d820a976050891d68724c850740a`.
The whole R084 package companion and R052 row21 rulings were read.
Ownership: Unimog `739e1d12`; handoff
`cc7feb0b-a667-57cf-97bf-743c829c2ab7` accepted before review edits/delegation.
Source references below are at the exact candidate under `stimuli/photo/`,
except the explicitly named `audit_app/IMAGE_AUDIT_FREEZE.md`.

## Verdict and system understood

**NOT FAVOURABLE to this exact image-audit package.** Findings 1–2 describe
successful extra-send paths outside the declared 400-attempt/six-hour envelope,
not merely unfinished cleanup or a conservative STOPPED outcome. Finding 3
requires one coherent prospective referral policy in the bound declarations.

The proposed audit uses the admitted revision-17 reader to ask fresh, stateless
questions about the 32 primary photographs and fixed-ranked Commons second-view
candidates. Round1 plans 224 requests: three per primary plus four per candidate;
the eight Stage A concepts complete first, then the other 24. Later rounds should
ask only the next eligible candidate for unresolved concepts, using the earlier
complete scientific outcomes and carrying every charged attempt and second.
An audit result is a filter and an owner-referral record; per-image provenance/
license checks, the cleared P=2 manifest and row21's separate package remain later
gates. No P=2 manifest is cleared by this record.

After the incoming brief, R052 recorded the owner's standing **“Go if favorable”**
at Unimog `f009a600` (4 October): it carries across revisions without expiry and
R052 binds it on the first favourable exact-package record that R052 verifies.
That condition is unsatisfied here. This record cannot bind AIAUDIT_GO.json or
authorize an audit request. No additional owner turn is required merely to reuse
that standing approval after a repaired package earns a favourable exact record.
Source owns binding/dispatch; root makes no request and edits no go file.

## Numbered findings

**1. Nonpositive round numbers create fresh uncharged scientific jobs.**
The public CLI accepts any integer (`ai_audit_exec.py:258–269`,
`ai_audit_set.py:263–265`), and `run`, `configure`, `limits`, `AuditJob._admit`
and set derivation/check supply no positive-round guard. With k=0 or negative,
`prior_charges` walks empty `range(1,k)` and grants a fresh aggregate allowance
(`ai_audit_exec.py:134–163`). Derivation skips both the k>1 predecessor restrictions
and k==1 primary questions; it still builds the 32 rank1 candidates' four
questions, 128 requests (`ai_audit_set.py:159–177`, `194–220`). Request IDs and
set/delivery/raw/job/clock namespaces include k (`182`; executor `82–91`). These
new namespaces do not change the package's round1 pins.

Build/delivery/check can therefore produce consistent nonpositive-round objects
from the frozen source. Scientific admission checks that derivation and the same
audit go (`ai_audit_exec.py:185–200`); no positive/global-chain guard intervenes
before the inherited loop's round-local limits, durable dispatch record and GO
(`ai_reader_exec.py:981–1005`, `1049–1051`, `1077–1078`, `1095–1096`). Four clean
128-request jobs numbered 0,-1,-2,-3 yield 512 requests, each with its own valid
local cap and six-hour clock. This is a static reachable trace, not an observed
audit execution. It needs no forged prior score or failure to recover.

Required repair: require a valid positive round at the scientific admission
boundary, including direct callers, before any dispatch; then enforce finding2's
contiguous chain. A CLI-only guard or positivity alone is insufficient. Retain a
meaningful admission fixture that proves k=0/negative cannot reach a dispatch.

**2. Later-round eligibility and aggregate carry trust live, synthetic or stale
score JSON rather than authenticated complete scientific predecessors.**
`prior_outcomes` reads live score bytes and accepts `mode=scientific` OR any truthy
`synthetic_round_chain`, then trusts selected candidates and audited ranks
(`ai_audit_set.py:129–145`). `prior_charges` independently casts live self-declared
attempts/time, without committed-byte, complete-journal, go/package, clock or
finite/nonnegative validation (`ai_audit_exec.py:134–141`). `S.check` rederives from
those same live bytes, including their current hashes (`ai_audit_set.py:234`,
`251–260`); this establishes self-consistency, not provenance. Earlier scores and
later-round objects are outside the 38-field go package.

Concrete positive-round trace: a legitimate COMPLETE round1 sends 224 requests
and all 32 first candidates ordinarily fail. Change only its unbound score's
charged.attempts to zero, retaining scientific mode and genuine outcomes; derive
the later objects. Round2 can send 128. Even with round2 honestly charged at128,
round3 sees only128 prior attempts and can send128 more: **224+128+128=480**.
The package-bound files need not change. The later scorer admits its own raw,
go/package, set/delivery and finished clock using the same false carry
(`ai_audit_score.py:97–116`), rather than re-admitting the predecessors. Synthetic
chain input can also invent eligibility after an incomplete/STOPPED predecessor,
defeating the declared hold. Neither case was executed by this review.

Committed score bytes alone also do not prove current time carry. Rerunning an
ended round opens/charges/closes a new clock session before refusal of its existing
receipt (`ai_reader_exec.py:801–803`, `819–823`, `848–857`). A previously committed
score's seconds are then stale; later consumers do not re-admit that changed prior
clock. Type coercion additionally admits negative/nonfinite charge values.

Required repair: admit a positive contiguous predecessor chain, tied to exact
committed scientific score bytes and their complete admitted raw journals, bound
go/package/set/delivery and finished current clocks. Recompute or equivalently
authenticate eligibility and exact current charges, with strict nonnegative finite
types and identity; reject synthetic escape in scientific admission. Handle
repeated/refused starts that alter earlier accounting. STOPPED, missing or
inconsistent predecessor evidence must hold before a next-round dispatch.
Fixtures should drive the real admission-to-send boundary for these paths,
including changed charges/outcomes, synthetic predecessors, STOPPED, changed
prior clocks and cumulative exhaustion. The existing arithmetic fixture cannot
establish this proof.

One owner go can cover mechanically derived positive later rounds under a
prospectively frozen algorithm **once this chain and aggregate envelope are
enforced**. I do not require a fresh Codex review/owner go for every ordinary next
round. Scope changes, a STOPPED release or exhausted budgets remain separate
decisions; the current package does not enforce its claimed one-go scope.

**3. The automatic-candidate policy differs from the declared unchanged freeze.**
`IMAGE_AUDIT_FREEZE.md:88–101` makes every non-pass an owner referral with owner
pass/fail-replace-hold, and its exposure paragraph says the rules are unchanged
(`8–14`). AI_AUDIT_JOB.md also says aggregation/referrals are unchanged (`3–7`).
The new job instead automatically advances failed candidates, listing them for
the owner, and refers only failed primaries/exhausted concepts (`102–110`). The
scorer implements this distinction (`ai_audit_score.py:187–218`); derivation
advances without owner disposition (`ai_audit_set.py:161–177`). The older
second_views.py rejection succession does not reconcile the newer freeze's
universal-referral words.

Prospective ruling: automatic fixed-rank candidate succession is acceptable
within the repaired reviewed envelope, while the owner retains adjudication of
each failed candidate. Before answers/go binding, explicitly amend and freeze
the job/referral rule to make that exception coherent: failures retained for the
owner, primaries and exhaustion held for him, AI and owner decisions separate,
and declared handling when an owner passes an earlier candidate after a later
mechanical selection. Alternatively keep universal referral and gate succession
on its recorded disposition. No answer becomes a reader pass by owner override,
no retry/alias change is introduced, and a failed Stage A primary retains its
declared bundle consequence. This is an explicit design ruling, not a request
for another routine owner confirmation or a claim of already wrong results.

## All seven requested rulings

1. **Pinned Commons renderings: acceptable declared input identity.** Sources
   request iiurlwidth1280, pin downloaded bytes/hash and separately record Commons
   original URL/dimensions/SHA1/MIME (`ai_audit_sources.py:77–81`, `103–116`,
   `134–156`). Candidate canvases use those exact bytes and the primary pipeline
   (`ai_audit_set.py:85–107`). The eventual P=2 manifest must preserve the accepted
   rendering and audited canvas hashes; switching to an original/re-download is
   a changed stimulus. The source's original dict omits original byte size despite
   the brief/job claim; the key's original_sha256 is actually the rendering SHA256
   (`211`). Correct those descriptions. No image or actual license was judged here;
   eligible per-image checks still precede manifest clearance.
2. **Single composite distinct question: acceptable declared construction.**
   `pair_png:110–115` places the unchanged 384-square RGB singleton canvases left/
   right with16 pixels uint8=128 grey, yielding one384×784 image. It is one-image
   delivery with a disclosed two-panel comparison, after both blind names. It
   does not establish photographic independence. If the owner replaces a primary,
   a distinct judgment against the former primary cannot transfer silently to
   the final primary; P=2 admission must check that actual pair.
3. **Automatic succession/referrals: acceptable prospective exception after the
   bound policy is reconciled, not current unchanged-freeze compliance.** Finding3
   supplies the rule. Primary referrals and DEV-CAL Stage A consequences are
   supported; no code in this scope replaces a primary or changes Stage A.
4. **Later rounds/one go: not acceptable as enforced here.** Findings1–2 supply
   the missing positive-round, scientific-chain and current aggregate proof.
   Mechanical re-derivation from the same unauthenticated bytes is insufficient;
   authenticated ordinary later rounds need not each get a new go.
5. **Eight-name rebinding and per-request prompt: supported.** `configure:160–165`
   sets the declared paths/limits in this process; the subclass admits aiaudit/audit
   inside the inherited deadline. `attempt:202–204` supplies that request's prompt;
   the base renders/checks actual image, instructions, detail and user-text hash
   before begin/GO, then uses that prompt in argv (`ai_reader_exec.py:1027–1058`).
   The inherited isolated allowlist/gate/watchdog/journal remain the accepted
   route. No concrete new unbound-prompt/wider-access send path was found.
6. **Question wording: acceptable semantic clarification with an order correction.**
   The yes/no/unsure prompts preserve the intended questions; name is the frozen
   qualification prompt. Names precede the other questions **within each of the
   pilot/non-pilot blocks**, not globally over the round (`ai_audit_set.py:187–220`).
   Correct the stronger global-name-first claims in the job/set docstring. The
   actual per-item blindness/statelessness and pilot-first rule are supported;
   no answer contamination from this block order was demonstrated.
7. **Weak search candidates: acceptable inputs to a bounded filter.** Frozen
   CC0-before-PD relevance/rank and declared exclusions do not certify concept/
   photograph quality (`second_views.py:8–19`, `45–92`). All name/photograph/sense
   and distinct outcomes must pass. First-use on unseen candidate images is not
   blind recalibration of the exposed qualification panel or human equivalence.
   Budget exhaustion may leave concepts/P=2 unresolved; it cannot relax the filter
   or purchase/allocate extra rounds. Clothes-only refresh/retired mask and the
   other31 frozen lists remain the declared inputs, not inspected image quality.

Referral record limits to correct before adjudication: primary human_n_ratings is
the literal placeholder “see THINGSplus norms (release table)” (`ai_audit_score.py:180`),
not the numeric count promised by the freeze. Exhausted referrals list only the
current round's failures (`214–218`); owner referral must include or explicitly link
the prior failure history. These are reporting gaps, not evidence of a wrong
reader answer. No human table was opened by this review.

## Exact pins and retained evidence

Independent standard-library Git/hash/AST metadata derivation reproduces all
38 fields below and digest2b8d8aa6…; all28 bound Git-blob hashes match the live
files at verification. Runtime fields include the locally measured owned CLI
binary/tree/manifest, sandbox-exec and THINGS-definition byte hash; command
template is independently reconstructed from the source's metadata formula.
CLI version comes from the owned codex-package.json version0.160.0 and retained
metadata; **no binary command was executed**. These external/runtime inputs are
current pins, not bytes contained wholly in the candidate Git commit. Generated
set/key/map/input JSON were byte-hashed only; only qualification reader/prompt
and instruction-pin configuration metadata were extracted.

The25-field reader package independently reproduces digest
`4517553a0615436d8a0c384849c43a206fd9e428729d1d91ef6a0d68bf4b3e35`
and equals its existing AIREADER_GO package. Its admission stays closed: job(c)
was an exposed third pass with three owner adjudications; partial text is never
an answer and the capacity detector covers visible retained text, not hidden/
split/escaped capacity phrases. This review does not reopen qualification outputs.

The retained suite Markdown and all10 listed public synthetic log/metadata blobs
at aa19d4d were read and independently hash/size/count checked. Main401 collected
=358 OK+43 skipped; build27=27 OK; **385 passing executions,374 distinct exercised
names,11 repeated names,0 failures/errors**. Sixteen WordNet skips were restored
in build;27 transition cases remain unexecuted (5+10+5+7). Seven new audit tests
are OK in retained implementer evidence, not tests run by this reviewer.

The14-request positive fake checks per-request user-text receipts/completion.
Wrong-prompt fixture stops before that photograph request; an earlier name was
sent, so it does not show zero dispatches for the job. Synthetic scoring uses
injected exact-name matching and forces the failed-candidate next branch; it
does not test production WordNet matching, exhaustion or scientific admission.
Injection refusal is the immediate fixture guard. Yes/no and delivery tests are
selected pure checks. Carry fixture supplies arbitrary uncommitted charge-only
JSON and proves arithmetic, not provenance/positive rounds/current clocks.
Fixture setup bypasses production admission/derive/configure; it cannot repair
findings1–2. Teardown restores fixture limits/removes temp files, without an
independent process-extinction assertion. Accepted base mechanisms are credited
within their declared scope, not freshly claimed as production audit evidence.

## Review boundary and attestation

Three read-only peers supplied scoped source/evidence findings; root integrated
them and independently checked package metadata. No submitted module/import/
function, test/fake/fixture, CLI/provider/model/reader request, forward, scoring,
archive or simulation was executed. No actual audit/capture image/array/tensor,
raw reader journal/answer, private-key semantics, plant/human output, audit
website or D1 was opened. No SSH/PBS/account/remote job action, worktree or push.
Source owns code/currentdocs/frontmatter/INDEX/tracker/ledger/go/results/dispatch;
root owns only this review and its own R052 append/lifecycle/prompts. Foreign
files, source jobs, exposures and old completed reviews/reports remain intact.

<!-- STAGE-ATTESTATION v1
{
  "row": "aiaudit",
  "stage": "audit",
  "verdict": "not favourable",
  "reviewer": "Codex, GPT: R052 Entropy paper",
  "date": "2026-10-04",
  "reviewed_commit": "b055a81e069483ea38c62dae9d87fb48e9e800c7",
  "package": {
    "AI_AUDIT_JOB_md_sha256": "162a8adc95dd02344a35171b02d760922c9e27cd15adc445c22407b2092e5cfb",
    "IMAGE_AUDIT_FREEZE_md_sha256": "52915d1bb4aed9d22d60c5b3215f91cc5e9d51c10bbc130ab626e83e7e3d8b05",
    "ai_audit_delivery_r1_json_sha256": "cdd363316064a315f77217f267af4e1cbd1d76a96e65306d06e98d4d0887bb60",
    "ai_audit_exec_py_sha256": "fb7fe7767f6e7dd3a4294591988bc8a7c182ead0759a2640166feefc47ab1d2f",
    "ai_audit_key_r1_json_sha256": "e6438875df242278192376535f648d289ca4457a374a98d78c9c41e2349388fd",
    "ai_audit_score_py_sha256": "89e0c09ac54b800dcca42c0b1ba9e9c7896312a51eec8b28e958f2762b7e6084",
    "ai_audit_set_py_sha256": "d183bbdacfb9da86641011c618c54b768dfb5eb5e08989cff57cc9e7bd7dc88b",
    "ai_audit_set_r1_json_sha256": "850ba35cd37aec8359db18f33a914e5ca655781469da8d24ec5eeb5a56d8f3d6",
    "ai_audit_sources_json_sha256": "5127035ca91c1cd1ba23b29f0c83802fa795fe8e0ea257e29484019336b6d7b4",
    "ai_audit_sources_py_sha256": "16d9d4bb6d18c3e500e8baeb5bb8aef681c29a08b4f9f27976cea6c3b33c7794",
    "ai_reader_delivery_json_sha256": "14b8cccd0a2ef184f922259fa86747710c57e6dddf70066515a32b7d8fd7eaf5",
    "ai_reader_exec_py_sha256": "5fbb730d1f10c6c38dc638f06a7d1f57e724ed7efeba8e8a7b93382d783ae097",
    "ai_reader_journal_py_sha256": "b67d25526c715434b55e6410d1b66046a9437ca48c825c34fabd9705515613a2",
    "ai_reader_key_py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_qual_set_json_sha256": "2f16cfe892295bf26ebb4eecc4f76fa9420f91bee5112a8b426d8e9f2d314238",
    "ai_reader_runtime_py_sha256": "cb78adaa56a34f45430ea26429dbc0aa1c204fc48bbec454f1af35ff42ebec32",
    "ai_reader_score_py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "audit_alias_map_json_sha256": "a3f6ab51dbf0dda1148a26bfdc8b671adf91d1edc712fe58ef9ddcffc0397c80",
    "audit_alias_map_py_sha256": "39088b6e0834c6bbdc704b77d010de7b22eba7afe9637f3bec0be3db0a1e2dd1",
    "audit_package_py_sha256": "e15b1a192060e20dfe62395211c34600c399fdd134233cb95eec742d787ed0ff",
    "cli_version": "codex-cli 0.160.0",
    "codex_package_json_sha256": "404c4c935bf9b7a57fc02b6f0d09ba6b7bbbf15cf14286fc017de2a6c01cab47",
    "codex_realpath": "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/captures/reader_cli/codex-0.160.0/bin/codex",
    "codex_sha256": "112fae7a5a1223e673c8a1791d32338f37df8b527ff1159bb8adac6c4dbf1b4b",
    "codex_tree_sha256": "ced09ec2c51c8fd4ae4ccb7e0ccb6b6e76d32633ec842f08be000c2a55ba86fe",
    "command_template_sha256": "c36c43f34d8658dd14e3e332f1ae354328950eef4a152b9cf79dffcecc51361a",
    "dev_pool_json_sha256": "fae20dc215d1de329ff81a5687735047c9a92cead1b9642f7cda4f6c2d69ad2d",
    "dose_py_sha256": "05d61ea6d199903eb066534e8cc2e7bb73e102b9cfa284f5692f8d75e9bb4302",
    "enforce_py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
    "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
    "manifest_dev_json_sha256": "e816f843700a4a15c4ca56ba71318957e73b77d3560e81a2bf476ff23422f448",
    "memprobe_py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
    "package_digest": "2b8d8aa66fa83ba09fa022527fe69c34e8ec6c5bf4a012249f43e42f5a7c718c",
    "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
    "second_view_candidates_json_sha256": "430b0ce8794910dcc6bd2aa939fa4ae7453018663667ba3f861b779b68e2d028",
    "stage_a_guard_py_sha256": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
    "stage_a_watchdog_py_sha256": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed",
    "things_definitions_sha256": "3f05b6b748d1e1b685e15130d2487bff63f86e1f4da94a2a5d9e7dec073a48eb"
  }
}
-->

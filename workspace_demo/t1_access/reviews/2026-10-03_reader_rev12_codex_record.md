# AI reader revision 12 — exact-package Codex review

Review date: 2 October 2026 Phoenix /3 October UTC. Reviewer: exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Candidate: `0f4cffe5ad94d762cbaa7c74fafd3f15fd1ed5b2`.
Assignment: Unimog `prompts/2026-10-03_codex_r052_reader_rev12_review.txt`
at `cbfb9230b7a3128bc60d0e2d6b3bf8adf7bbd0b0`, SHA256
`30a48c8cc034fe9b1d99d690267b06b244a2fec8104c610491f9d404d84b2e8d`.
Ownership: Unimog `8e8d1769`. Ordering exception: the initial ownership check
refused a concurrent source edit; the next command nonetheless ACKed handoff
`4fce9600-eb1d-5583-b453-25da877b55b3` early. No review edit/delegation began
until source's edit landed and ownership was committed. The work log records
the exception; the handoff was not re-ACKed.

**FAVOURABLE for this exact reader package as the bounded qualification
mechanism. Both deviations are accepted.** The declared owner-adjudicated
route is acceptable with the interpretation below. No remaining implementation
condition is imposed here. This is no empirical admission, owner go, audit
release or Stage A outcome. A fresh job (b) still needs its own package-bound
dated owner go and fresh raw/clock state under its separate existing envelope.

The system remains a 300-item paired colour/grayscale free-naming qualification,
with 600 requests and a 63-item easy-gray admission panel. Revision 12 changes
the prompt and scoring rule; executor, journal, request isolation, accounting,
clock and shared guards remain byte-identical to reader revision 11. The key
and audit alias map remain byte-identical. This uses the same images exposed
in job (a), with new answers, rather than an unexposed holdout.

## Question 1 — the shared rule and both deviations

`ai_reader_key.py:300–340` first admits an existing whole form, rejects an
excluded form, and considers the token-singularised form under the frozen
inflection policy. It then applies S1 to the whole normalised/or singularised
answer, tests admitted forms as whole-word phrases, and tests the longest
WordNet noun suffix as a strict transitive hyponym of the target synset.
`260–267,270–278` define the singular and head operations. Equality to the
target synset is not strict hyponymy; hypernym and instance-hypernym closure
is followed in the stated direction. No target synset means no hyponym credit.

**Deviation 1 is correct under the rule as written:** “Air conditioning unit”
contains the admitted form “air conditioning” as a whole-word phrase. Keeping
that credit accepts the general containment rule, not a new alias or a
one-item adjustment to reach 61. The frozen key's hash is unchanged; the
retained fourteen-example fixture (`tests/test_ai_reader.py:1560–1586`)
produces twelve accepted examples and two nonmatches. This confirms code
behavior on source-supplied examples, not a reviewer judgment of photographs.

**Deviation 2 is accepted:** S1 uses the existing all-released canonical-name
and inflection population (`key:191–199,284–294,320–323`), after whole-form
admission and before containment/hyponymy. It prevents an otherwise unmatched
whole answer naming a different released concept from winning through a
broader relationship. It tests the whole answer, not each component: “toilet
paper roll” may pass while “roll” alone does not name toilet paper. S1 here
means released canonical Word/uniqueID forms and inflections, not every
alternative WordNet alias. Existing admitted forms and documented same-referent
exceptions retain priority; do not describe this as overriding them.

`ai_reader_score.py:125–158` retains status and format checks before matching;
the new OK codes depend on the same `names_concept`. The one-or-two-word prompt
is a request, not a new two-word rejection limit: the unchanged format policy
still allows up to five words and preserves three-word admitted forms.
`audit_alias_map.py:138–148` calls this same classifier on the audit's own
frozen entry, and `audit_package.py:31–45` requires its map/code pins. Shared
algorithm means the same rule applied to the respective frozen qualification
key and audit map, not the qualification key applied to audit concepts.
The new audit code identity must be used by its later separately bound package.

The declared containment and any-noun-sense residuals are accepted operational
limits. A modifier can receive containment credit without naming the main
object; a rare head sense can satisfy hyponymy. These credits establish the
specified matching outcome, not literal correct recognition for every answer,
human free-naming equivalence or independently validated recognition accuracy.

`key:133–138,247–257` checks the corpus version and fixed WordNet ZIP SHA once
per process. The local ZIP hash matches; its corresponding extracted home
directory is absent. This uses the ordinary trusted local corpus-loading
assumption: the check does not inspect `wn.root` or authenticate every possible
NLTK search-path alternative. No different loaded corpus was established here.
The positive cache-pin fixture is not a damaged-corpus/origin refusal test.
No extra universal environment or rerun condition follows from that limit.

## Question 2 — mechanical gate, adjudication and exposure

**The wording is acceptable as two distinguishable admission bases.** The
scorer keeps mechanical easy-gray m/63 and its one-sided exact 95% lower bound;
mechanical admission requires m at least61. `score.py:262–265,299–307` computes
that result and `adjudications_needed = max(0,61-m)` for this panel. It does
not consume owner decisions or change mechanical `admitted`.

If admission rests on adjudication, enough previously noncredited **easy-gray
naming** referrals must be judged positive to bring m+N to at least61, with the
picture and raw answer locked before each dated decision. Retain m/63, its
mechanical bound, frozen codes and the actual adjudicated items/decisions, and
report “admitted with N owner-adjudicated items.” That report is not a claim
that the mechanical gate passed. Non-easy or colour corrections cannot supply
the easy-gray shortfall. An actually wrong name remains a reader error.
Naming adjudication does not waive package, COMPLETE-journal, raw evidence,
provenance, clock or isolation admission, nor rewrite mechanical format/status
codes or aliases. No owner-adjudication workflow was executed or empirically
validated by this record.

Thus the restated audit sentence (`IMAGE_AUDIT_FREEZE.md:94–100`) distinguishes
a mechanically uncredited name adjudicated as recognition from an actual
recognition error; it cannot erase the mechanical result. This is a prospective
owner rule for revision-12 answers. It grants no retroactive admission to (a),
no arbitrary fallback and no owner-only audit.

**The post-hoc framing is honest with the repeated-panel qualification above.**
Revision 12 was designed knowing job (a)'s answers. The retained rescore report
and descriptive script explicitly bypass scientific package admission, touch
no go and retain (a) as NOT ADMITTED. Its reported61/63, lower bound0.9034,
gray231/300 and code counts are implementer re-analysis, not a fresh reviewer
score or admission. Job (a) answered revision11's prompt. Job (b)'s fresh raw,
clock, envelope and stateless requests do not remove previous panel exposure;
its result is evidence for this prospective rule on that reused panel, not
later blind calibration. The prior175-attempt/1,097.4-second STOPPED unscored
job remains separately disclosed. Different developers do not prove independent
errors or absence of public training exposure.

One declaration remains stale: `AI_READER_DESIGN.md:188–189` says the prompt
is byte-identical to revision3. Read that as historical image/order context;
revision12:C and the current prompt/delivery/template pins govern the changed
prompt. Source should keep current summaries true. Editing a bound document
moves the package and cannot reuse this exact attestation unchanged.

## Evidence and question 3

All24 fields below reproduce from immutable blobs and byte metadata, and all16
bound live files match. The command template was independently reconstructed
from source AST literals; CLI version is the frozen source label corroborated
by unchanged byte-matched executable/manifest, not a new CLI probe. Key/set/
delivery remain undecoded except extraction of the single instructions hash.
The audit map hash and all four audit identity fields reproduce separately.
Stage A's five fields exactly match the favourable record `e7b31f0`; its later
source-reported15-native STOPPED outcome is separate and is not reviewed here.

Retained suite `273d2354d119d4675f8b2f333d718b674ee26267` names candidate HEAD
and a clean photo directory. All ten file sizes/hashes match. Main279 tests,
OK/skipped16 in2190.457s; build27 OK in3.824s, including all16 skips and11
already-passed main cases: **279 distinct cases exercised**,290 passing
executions, not306 distinct cases. The ten new Rev12 cases passed in build.
Behavioral audit entry-point cases supplement the source-string shared-function
assertion. The map rebuild compares after excluding two construction source
hashes, rather than proving byte-identical regenerated JSON. The retained
adjudication-needed assertion is on a synthetic three-easy panel (None), not
a demonstrated63-item owner-decision workflow. These are evidence limits,
not demonstrated implementation failures or new gates.

Read/reason only: the full relevant declarations, changed matching/scoring
source, immutable interface/identity text, requested fixture source, retained
suite and rescore descriptions, standard-library blob/AST/hash checks, and three
read-only peers. The rescore JSON was byte-hashed, not inspected for actual
answers. No submitted module/function/import/test/fixture/CLI was executed;
no model, new scoring, scientific/remote/job/account operation, key content,
raw journal, image/capture/private audit or human/pull output was read, and no
image was opened or named. No worktree or push. Source owns implementation,
framework, ledger, protocol, stimuli, captures, go and dispatch.

This record has **one favourable reader attestation**, no Stage A block.
The existing strict guard separately requires its immutable commit/path/hash,
ancestry, ordered dates, all attested/re-derived/current fields and dated owner
words. No AIREADER_GO, launch or empirical admission is created here. Earlier
reviews, one-time reports and exposure disclosures remain closed.

<!-- STAGE-ATTESTATION v1
{
  "row": "aireader",
  "stage": "qualification",
  "verdict": "favourable",
  "reviewer": "Codex (GPT: R052 Entropy paper; native 01a0d19e-2127-7051-9a61-6db771088559)",
  "date": "2026-10-02",
  "reviewed_commit": "0f4cffe5ad94d762cbaa7c74fafd3f15fd1ed5b2",
  "package": {
    "ai_reader_qual_set.json_sha256": "b3e8969a8cff6f837561274d94ab05b115d978c2d4dae4bd3d79a37c2233794e",
    "ai_reader_qual_key.json_sha256": "d9c467f39d4d221b8d92059574506b1537140e66b6b9df18db28e15610ef9aea",
    "ai_reader_delivery.json_sha256": "b8c4c0d5f9c24925f3221c7bb7efe57cdca9788cc2894997702bf08a5bb9d1d4",
    "ai_reader_exec.py_sha256": "9ff61681702f47a2971aa1e512fe38492206458391f539cbf483a635caa53a0d",
    "ai_reader_score.py_sha256": "3e2ef03ceeb972d0c2e09e6684362913ad1d3b948f365b69669a0d533a25ba19",
    "ai_reader_runtime.py_sha256": "96235ea8e276b49ee671437776ee45d49a0249db70ce69b17849881fd4cac89e",
    "ai_reader_journal.py_sha256": "e067889c4210b91ec220fbd4f63421fb93fc4fd64f14c398f288fcaa3bcf2907",
    "ai_reader_key.py_sha256": "274147af5e07b2e2c3b21a69f493e4c4a9567f53fe12b8e05e4ad73adf6e4a66",
    "ai_reader_frame.py_sha256": "cf1e648dbd7617cc8160c73969adbcf4eac0703823ec98ae25056c7ef7ba60d8",
    "ai_reader_qual.py_sha256": "9072905986d5e86b76fb68f6ab9d6699469d8205269a434994527e4e87ead25c",
    "AI_READER_JOB.md_sha256": "7034a5cfc1162b2bb76f4a0a9315c2f2751ac0ded58ef128e79ae51261d5a6fb",
    "AI_READER_DESIGN.md_sha256": "90079e62135b4517d4f0a5b03cac3a801f5e5419a9ac81c471376a9f40d53e5d",
    "stage_a_guard.py_sha256": "a801e48edc0281988e86806fcf31206d7da3e220cfa7690c333990a635076750",
    "enforce.py_sha256": "5d142c94560da93ee08fd4021dd7aa46edba60d13252ed992e44873a0f57ed42",
    "memprobe.py_sha256": "83114f358b74372c3bbe647a5b907903ec6629c172a76adc3d7c13f5a7acd465",
    "stage_a_watchdog.py_sha256": "4c6d8723fec88afd59f9b9ff833cb6235462ca6e6c711e199dbc7f6af829b1ed",
    "codex_realpath": "/opt/homebrew/Caskroom/codex/0.159.3/bin/codex",
    "codex_sha256": "4d210f7c5a18fd0386434df23b5bdbb8c0e7257d3e8a2b30b0769c8bbe99a878",
    "codex_package_json_sha256": "8660ce5bb4e302c2739c7ddcc9974a45fa8d568d123b9066c9135d6dba0ac121",
    "cli_version": "codex-cli 0.159.3",
    "sandbox_exec_sha256": "58839ef01b4eef8aac0d2aa8f9d1c074ae45aafe3533965b030672450064acc8",
    "command_template_sha256": "8492a82984a51242bfd0ab6bb59e140fcf0a34feb21c3c51a560a58abb32d28a",
    "instructions_sha256": "e2a8ba62a740d571102bca60f77a3e4be04c7a02d2e823b602403a3e6d292790",
    "package_digest": "3e2bcdcc5356cbfaf31af61b473aa46751ec149006620c0d3a66a99466b9ec11"
  }
}
-->

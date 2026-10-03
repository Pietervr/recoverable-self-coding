# Row 19 producer-runtime identity oracle — bounded Codex design opinion

Date: 3 October 2026 UTC (2 October in Phoenix). Reviewer: exact
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Handoff `266f1150-6171-5d60-b5ad-2c43d5bc3e76` was read end-to-end,
ownership committed at Unimog `d5543e4a`, and manager ACK accepted before
review edits or delegation. Brief: Unimog
`cff5acf58c3d9510a4e96dd15dd901831e2a5344`,
`prompts/2026-10-03_codex_r052_row19_identity_oracle.txt`, SHA256
`0f7e34999edc38c9c9a48436b1eb3bece33c44ccd6739930f4017231b8e6853e`.

**YES, with the contents and disclosure conditions below.** A fresh oracle
that independently recomputes the exact identity under the pinned producer
runtime may establish the identity equality that the Mac cannot reproduce.
This is a verification-tool design opinion. No new implementation is submitted
or attested here; source implements and checks the bounded change. The owner go,
accepted geometry `6a36b0f`, existing jobs and scientific task remain.

The brief reports four jobs launched against the same manifest at 03:20 UTC:
C1 `7516927.sched01`, main reps0–2 `7516928`–`7516930`. It reports that
rep2's Lengau rebuild exactly reproduces its binding identity, while the Mac
rebuild differs only in response bytes. The retained eight-line comparison at
RSC `8b02440` reports 98/10,752 differing float64 values for rep2, maximum
absolute difference `4.440892098500626e-16` and relative difference
`1.5310417343753117e-14`; rep1 has zero differences. I read that comparison,
not its arrays, and performed no fresh generation or remote verification.

The existing contract explains the failure: `analyze.dataset_identity:495–518`
hashes data, generator metadata, Config/policy, folds and the numerical snapshot.
`row19_control_compare.expected_contract:43–94` rebuilds local data/folds,
checks the producer snapshot/pins, compares identity, then rebuilds local draws.
The producer binding (`row19_slice.py:366–382`) also carries manifest SHA,
rep, resolved seed, code/config hash, policy, B, endpoint and task paths. These
interfaces at RSC `3ad8ce1` were read to reason about the design, not reopened
for a fresh implementation review.

The oracle needs these bounded conditions:

1. Bind each entry to the **exact manifest-byte SHA256 and immutable task
   binding**, using a documented canonical digest of the binding, plus explicit
   rep, resolved seed and B. This includes its code/config hash, policy,
   endpoint, paths and complete numerical snapshot. Match those values against
   the freshly pulled task and current manifest. A same-seed entry from another
   root, endpoint or manifest must not supply the fallback. Do not hash the
   changing watermark/run-history document as the immutable binding.
2. Independently rebuild the dataset and outer folds from that manifest and
   resolved seed under the admitted pinned Lengau wrapper/runtime, then
   recompute identity and require exact equality with the binding. Do not copy
   the claimed identity. Verify the actual loaded source digests, observed
   runtime and complete effective numerical snapshot against the binding and
   pins before recomputing; passing a supplied snapshot to the hash alone does
   not establish the producer used it. Retain generator/tool version or digest,
   invocation provenance, host/architecture/runtime, time and oracle bytes/hash
   with the successful snapshot. This uses the existing trusted artifact and
   transport workflow, rather than claiming independent authentication.
3. Include canonical digests of the non-response data/metadata used by identity
   (`k`, concept, family, layers, group and generator metadata), the actual outer
   folds, and the **full B200 resample-index matrix**. Require equality with
   local reconstruction before using local expected draws/bands. Document
   shape, representation and canonicalization so cross-host digests mean the
   same thing. Equal family vectors alone do not establish that two NumPy
   versions return identical shuffled folds or RNG draws. `stratified_folds`
   (`analyze.py:99–111`) and `stratified_resample` (`312–318`) depend on family
   and seeded RNG, not y; their outputs still need that comparison. The y digest
   diagnoses the byte difference; it does not prove structural or draw equality.
   NumPy's [compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html)
   limits Generator stream guarantees to the same build/environment/machine;
   this is no claim that the current integer draws actually differ.
4. Pull the oracle as part of the same successful fresh snapshot, with its task
   mapping and provenance. An unchanged task oracle can be generated once;
   fresh pulling does not require regenerating it at every poll. An absent
   oracle retains today's local behavior. An invalid, stale, ambiguous or
   mismatched entry cannot provide the fallback, and a failed pull cannot
   supply fresh verification. Expose the selected verification basis and any
   oracle problem rather than silently turning an unverified count green.

Change only how the expected **exact identity** is established. Preserve the
existing snapshot/pin/config checks, checksum, exact seed/B/index/chosen-draw
checks, predictor/band sets, failure typing, nonnegative finite fit time and
finite statistics on nonfailed records (`validate_record:97–122`), along with
watermark/recovery, task/root/job/reservation, terminal/PBS-kill, exact control
parity and qualification predicates. No rounding, tolerance, rewritten record
identity or scientific comparison is introduced. C1 remains locally verifiable;
an oracle does not itself qualify C2/C3 or release stage2.

Source's producing fixtures should exercise a genuinely different local identity
with a matching recomputed oracle; wrong manifest/binding/root/endpoint, rep,
seed/B, runtime/pins/full snapshot, structural/fold/draw digests and recomputation
identity must not admit a fallback. Include absence and failed-freshness behavior.
A positive fixture already passing the local identity check would not establish
the fallback. Existing record refusals must remain refusals through the oracle
path. These are conditions on the proposed implementation; I ran no fixture.

The slice report should identify verification basis per rep: local reconstruction
or pinned-Lengau oracle. State that some response bytes are platform-bound at the
last bit and rep2's byte identity is producer-runtime reproducible, supported by
the retained oracle, rather than independently reproduced on the Mac. This
does not establish cross-platform fit equality, numerical equivalence or new
scientific validity. No new campaign, cloud permission or budget is granted.

Two read-only peers challenged provenance and local draw reconstruction.
Only this optional record and the reviewer log/lifecycle are owned. No submitted
source/function/import/test/fixture/CLI was executed, no diagnostic array,
private audit/key/reader answer/journal/image/capture was inspected, and no
fit/model/simulation, SSH/account/job operation, worktree or push occurred.
Source retains oracle production, watch/comparator implementation, runner,
identity, pins, manifest, ledger, current summaries and dispatch. Earlier
reviews and one-time completion reports remain closed.

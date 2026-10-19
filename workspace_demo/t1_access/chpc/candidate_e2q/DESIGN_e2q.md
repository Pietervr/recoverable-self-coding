# EC2 provider epoch 2 - QUALIFICATION package (CANDIDATE, not adopted, not run)

Written 18 October 2026 (R052, Claude, bounded job). It builds the second bullet of `chpc/candidate_e2/DESIGN_e2.md` s.5:
the E2Q1/E2Q2 contracts, a schema-3 certificate, an epoch-2 branch of `prod_authority.release_problem` and `RELEASE_CODE`
extended to the candidate files. The rule it implements is `chpc/candidate_e2/QUALIFICATION_E2.md` s.2-s.5, declared on
17 Oct before any epoch-2 result. It is for Codex's review.

Nothing here was run against the world. No AWS call, ssh, Lengau or scheduler operation was made. No live or adopted file
was edited: `chpc/row19_screen_controls*.json`, `chpc/row19_screen_manifest.json`, the adopted `chpc/*.py`, `aws_ec2/runs/**`
and the authority state files were read only. The reviewed `chpc/candidate_e2/` bytes are unchanged. Every changed module is
a NEW copy in this folder. The one change that a reviewed candidate file would need is a proposed diff, NOT applied (s.5,
choice 3). Production stays shut (s.4).

## 1. Files

At promotion each file replaces its namesake: `chpc/candidate_e2q/X` goes to `chpc/X` and `chpc/candidate_e2q/aws_ec2/X` to
`aws_ec2/X`. The reviewed `chpc/candidate_e2/` modules this package builds on (partition, ingestion, shared rules) are promoted
from there, as `DESIGN_e2.md` s.1 says.

| File (this folder) | SHA-256 | What | Promoted to |
|---|---|---|---|
| `row19_ec2_state.py` | `7bdedafc7c90ec065217d9a7bbf53b88e1bf31e0c094dc34df730b4028bd038e` | REVISION 4: copy of live `bda200dc` + contracts `E2Q1`, `E2Q2` (production geometry; roles 52 work + 20 `qual_lengau` + 4 sentinels). Nothing else changes. | `chpc/` (controls v17 must pin it) |
| `row19_ec2_e2qual.py` | `5ceba55189dd351b2cc5a997b115cdbfd0d84f17397402fa7deb2b3e937025fa` (reviewed `b3f29816`; s.8: the `code_path` docstring now states content binding, code unchanged) | NEW, pure: the declared panel (`derive_panel` / `panel_problem`), the R1'-R5' constants, the epoch-2 code set `CODE`, the release literal, `code_path`, `opmanifest_bytes`, `ack_problem` | `chpc/` (pinned by v17; in the code set) |
| `row19_ec2_qualify.py` | `1d8eee78fc9427cd9e4cebe09deac37cf4284f0b8a86714dcc9d80cde63cbb29` (REVISION 6, s.8; reviewed REVISION 5 `73f912b8`) | REVISION 5: copy of candidate_e2 REVISION 4. The epoch-1 path is unchanged. New `e2` command (`main_e2`) writes the SCHEMA-3 certificate, and `sandbox_replay_e2` runs R5'. REVISION 6: validated resource evidence (B2), the `--snapshot` command (s.8) | `chpc/` |
| `aws_ec2/prod_authority.py` | `e4897991aaeaf1dc019c9b73361d288e71464e6f89e416b66d9e3d7601df146d` (REVISION 8, s.8; reviewed REVISION 7 `eee1bcd4`) | REVISION 7: copy of candidate_e2 REVISION 6 + `release_problem_e2`, an epoch-1 guard, `E2_RELEASE_CODE`, `pinned_partition`, a `qualification_e2` reading in `release_state`, the released epoch, `e2q_admission_problem`, `production_release_problem`. REVISION 8: the physical crash envelope (choice 3) | `aws_ec2/` |
| `aws_ec2/prod_launch.py` | `6bca470910489376d37529fb37772d4a2758d4c71758c990bd17108c6ff6c784` | REVISION 7: copy of candidate_e2 REVISION 6 + E2Q admission from the declared panel (`build`, `panel_for`, `--panel`) and a per-epoch release gate (`gate_problem`) | `aws_ec2/` |
| `aws_ec2/make_prod_manifest.py` | `d8412c32f5663350a5029309dffd6183aaf0a0a76afb089f85f8e8208ac01f07` | REVISION 3: E2Q1/E2Q2 for epoch 2 at 75,300 s. An E2Q contract REQUIRES `--partition --snapshot --panel-out` and writes the panel; an existing different panel is refused. | `aws_ec2/` |
| `aws_ec2/qual_permit.py` | `51653d26c69552ea449c10747672786a77dac67e4ffe183f7ff6b7382433a8ad` | REVISION 2: `--epoch2` writes `qualification_e2` (same drain and fence); `--epoch2 --e2q2` writes the E2Q2 record | `aws_ec2/` |
| `aws_ec2/prod/manifest_e2q1_e2.json` | `3ea8cafd736871de715062ca398f36ff98f93f27d1d82bd977c3b72b0f1cfb8b` | E2Q1 operational manifest (`derive_operational`, epoch 2, expect 75,300 s, lifetime 79,200 s). It does NOT depend on the partition. | `aws_ec2/prod/` |
| `aws_ec2/prod/manifest_e2q2_e2.json` | `4af4a64d83c749394c7159814359da716b2a9f9a694cd23fe46157aecd7b0cec` | E2Q2 operational manifest (identical geometry and roles, its own contract name) | `aws_ec2/prod/` |
| `fixture/panel_e2q_e2_candidate87ed.json` | `65f14b2fc8df7a8498c0216a18653a850b92e50a4fd5a0ae9bc7e185ec73c041` | TEST FIXTURE ONLY: the panel the maker derives from the CANDIDATE partition `87edfb9e` and snapshot `043db609`. It is not the final panel. | never promoted (s.6) |
| `proposed_ingest_released_e2q_partial.diff` | `34c76e57acec11b443090166d43c7c06812ce3f9ef76ca97dbcbcab14ad020a4` | the proposal Codex accepted in principle (s.5, choice 3). Kept as the reviewed proposal; the applied form is `candidate_e2/row19_ec2_ingest.py` REVISION 8 (s.8 and DESIGN_e2.md s.8), which adds R4' | record |
| `test_e2q_ingest.py` | (s.8) | NEW, 44 checks: the released E2Q1/E2Q2 per-slot route (publication, exact ACK, holding cases, recovery) and the choice-3 crash ruling (mixed ACK test, envelope controls) | - |
| `regress/run_regress.py` | `ade1bcb53a9c27778b1865bc57c21d541cc4d8c63a045a2543ad2beb04f7f6a8` | Runs the existing tests unmodified with the e2q modules substituted (the candidate_e2 pattern) | - |
| `regress/run_e2_tests.py` | `e4d5c6720789398068ef9029f1eed63d26b3480ecc8bf0e4e1cf3df9f41dbba0` | Runs the `candidate_e2/test_e2_*.py` files unmodified on disk, with their two explicit Mac-module paths redirected in memory | - |
| `test_e2q_contracts.py` | `7cc698f5eca1aad585dfff0067462005032db1e2919c75ae7547cad58a85ba81` | 54 checks: byte-equal regeneration, the panel, the refusals, the contracts, the launcher's E2Q plan | - |
| `test_e2q_qualify.py` | (s.8) | 56 checks (33 reviewed + 23 for s.8): the schema-3 certificate on synthetic bundles (clean RELEASE; each single R1'-R5' violation); B2 counter and parser negatives; the relocated snapshot layout | - |
| `test_e2q_release.py` | `4910cfc147d7805f64587e589cab46544a8402c19f8c9ede2e9854932562ebe5` | 81 checks: the release branch, its prerequisites, epoch 1 against epoch 2, release_state / release-adopt, the allowance counters, conformance with the qualifier's own certificate and the real `ack` | - |
| `test_results.txt` | `81aff78e5146ee1dd90274770380b2675b4dabfa3d52251007308393bb869c72` | counts before and after; every pre-existing failure explained | - |

## 2. What was built, mapped to the plan

### 2.1 The contracts (QUALIFICATION_E2.md s.2; DESIGN_e2.md s.5)

**Instance contracts.** `row19_ec2_state.CONTRACTS` gains `E2Q1` and `E2Q2`:

    dict(itype="c7a.24xlarge", workers=76, max_price=1.20, volume_gb=60, roles={"work": 52, "qual_lengau": 20, "sentinel": 4})

That is the production contract's geometry with the declared panel's roles. The unchanged `plan_problem` already checks every
non-production contract for an exact slot count and maps `qual_lengau` to the attempt's duplicates. The ingestion's
`operational_problem` and `plan_problem` therefore accept E2Q plans with no other change. The test checks the unchanged
`plan_problem` on the 76-slot plan: it accepts it, and refuses 75 slots, a foreign role, and the E2Q2 name on an E2Q1 plan.

**Operational manifests.** `make_prod_manifest.py --epoch 2 --contract E2Q1|E2Q2 --expect-s 75300` writes
`derive_operational(43b75f94, 2, 75300, contract)` at the funded 79,200 s lifetime. The maker refuses:
- any other lifetime;
- any other epoch for E2Q;
- the epoch-1 Q1 contract at epoch 2.

These two files depend only on 43b75f94 and the contract, so they are final unless the contract changes.

**The panel: the part that binds the partition.** The maker REQUIRES `--partition` and `--snapshot` for an E2Q contract and
writes `--panel-out`, the output of `row19_ec2_e2qual.derive_panel`:
- **work**: the first 52 owned coordinates in the production allocation order (ascending, at most 57 per replicate). This
  is the rule `prod_authority.allocate` applies with no ledger history; the test asserts the two are equal.
- **duplicates**: the 20 lowest Lengau-completed designated coordinates of the EC2 replicates, read from the claims snapshot
  whose sha256 the partition binds.
- **concentration**: it must reach at least `QUALIFIED_REP_SLOTS` = 61 on one replicate. Below that the maker REFUSES
  ("re-declare the panel before any outcome", QUALIFICATION_E2.md s.2).
- **bindings**: the partition sha256, the owned digest, and the snapshot path, sha256 and claims digest.

The panel carries no authority of its own. `panel_problem` regenerates it and requires byte-equal canonical JSON. The
launcher, the qualifier and the release branch all re-derive it. On the candidate partition the derivation reproduces
QUALIFICATION_E2.md's 17 Oct declaration exactly:
- work = rep 24 indices 11..62;
- duplicates = rep 24 (0-8), rep 25 (0-5, 7, 8), rep 28 (0-2);
- 61 workers on rep 24.

**Sentinels** follow the token rule at admission (`prod_authority.sentinels`, excluding the duplicates). They are not in the
panel, as epoch 1's were not.

**Launcher.** `prod_launch.py --contract E2Q1 --epoch 2 ... --panel prod/panel_e2q_e2.json` runs `panel_for` (the panel
validated against the partition and its snapshot) and then `build`. It refuses unless:
- every work coordinate is still free: owned by epoch 2, not completed, not owned by another attempt, not crash-excluded;
- every duplicate is Lengau-completed in the receipt;
- the 4 sentinels lie outside the duplicates;
- the built plan carries at least 61 workers on one replicate.

The gate is `prod_authority.e2q_admission_problem`. The money is checked by the existing `budget_problem` (a `qual-E2*` run is
bounded by `epoch2_problem`), `fleet_problem` and `epoch_problem` at the funded lifetime.

### 2.2 The schema-3 certificate (QUALIFICATION_E2.md s.3)

The command is `row19_ec2_qualify.py e2` (module text, REVISION 5). Its inputs:
- the schema-2 epoch-2 partition the controls pin, with its activation;
- the installed inventory;
- the declared panel;
- the attempt: a reconciled `qual-E2Q1/n` or `qual-E2Q2/n` whose work and duplicates are exactly the panel's;
- both operational manifests (the exact derivation AND the maker's exact bytes);
- the funding declaration (bound only here; the Mac rederives it).

**Bundle.** The bundle must pass ingestion's own checks under the schema-2 partition:
- `check_bundle(partial=True)`;
- `unproduced_problems`: the three qualifying kinds, the present-status rules of REVISION 6/7, and the 7/3 bounds;
- `plan_units` on every produced slot;
- every work slot owned by epoch 2.

**R1'.** The produced duplicates are compared float-bit with the Lengau records. At least 15 of 20 must be finite successful
on both sides. Agreeing failed and non-finite paths are counted apart and never count toward coverage. An UNPRODUCED
duplicate is reported and never compared. Any payload difference gives NO_RELEASE. A shortfall in coverage alone gives
INCONCLUSIVE.

**R2'.** Every one of the 52 work coordinates must be a validated record or a qualifying unproduced slot. This is stated as a
limitation (no reference exists for new work), not as a parity claim.

**R3'.** Not performed; the certificate records why.

**R4'.**
- The e1 memory method (`memory`, unchanged, now labelled): at least 10 samples with all 76 running and a peak of at most
  184 GiB. The status contract gives every produced worker's maxrss under the stop.
- The plan's 76 slots must carry at least 61 workers on one replicate.
- The produced sentinels must equal Lengau.
- There may be at most 3 non-completions of ALL roles (`row19_ec2_e2rules.qualification_unproduced_problem`).
- Every non-completion is reported with its slot, role, coordinate, exit, kind and status presence.
- A crashed coordinate is never given a record: it is simply not compared or counted. The test checks that the crashed
  coordinate stays absent after the sandbox ingestion.

**R5'.** `sandbox_replay_e2`, on the ACTUAL bundle:
- **The sandbox.** It builds an activated sandbox schema-2 epoch from the real one: the predecessor (a sandbox
  re-declaration of the epoch-1 block) is activated first, the designated declaration is re-bound, the snapshot is taken of
  the sandbox root and `declare2` is run. The attempt is presented DELIBERATELY as class production, and the certificate
  records `presented_class`.
- **The replay.** A forced stop after the first published pair, then a replay, then a second replay. It must end
  `ingested`, with `replay_problems` (including the frozen failure evidence) empty.
- **The per-slot branch.** An actual unproduced WORK slot is exercised as it is. Otherwise one CONSISTENT synthetic case is
  ingested in a second sandbox:
  - the first work slot's outcome becomes 139;
  - its record, timing and status are removed;
  - the checksums are regenerated;
  - each changed file is labelled `SYNTHETIC` with its original and modified sha256.
- **The checks on that case.** The slot must be listed unproduced, fenced and journaled, and the `ack` rule must release it.
  The modified bundle replayed against the UNMODIFIED journal must HOLD.
- **Scope.** The scope is stated: ingestion publication recovery only.

**Outcome.** NO_RELEASE on any problem; INCONCLUSIVE when only R1' coverage is short; RELEASE otherwise, naming the attempt.

**Bound.** The certificate binds:
- the code: `EQ.CODE`, resolved to the files actually used, with every loaded module checked against its bound file;
- the manifest, the partition and its owned digest, the activation and the inventory;
- the panel and the claims snapshot;
- the funding bytes;
- both operational manifests and the lifetime;
- `BUNDLE_SHA256SUMS` and the plan.

### 2.3 The epoch-2 release branch (QUALIFICATION_E2.md s.3 last paragraph, s.5; DESIGN_e2.md s.5)

`release_problem` dispatches on the certificate schema.

**Schema 2 (epoch 1).** The epoch-1 branch is unchanged, with one new guard: it refuses while the controls pin a schema-2
partition. The test shows that an e1 certificate bound to the e2 digest, with the e1 partition comparison forced to pass, is
still refused. The control test shows the same shape releasing under an epoch-1 pin.

**Schema 3 (epoch 2).** `release_problem_e2` requires:
- **Outcome**: RELEASE, no problems, no short coverage.
- **R1'**: at least 15 of 20.
- **R2'**: 52 accounted for.
- **R4'**: the sentinel part present; memory with 76 workers, at least 10 samples and a peak of at most 184 GiB; at most 3
  non-completions, each of a qualifying kind; concentration 76 slots with at least 61 on one replicate.
- **R5'**: ingested, hash-equal, the exact scope, presented as production; the per-slot case listed, fenced, journaled and
  released by `ack`; for a synthetic case, the modified replay held and every modification labelled.
- **Code**: `E2_RELEASE_CODE` exactly, at the current bytes (same resolver as the qualifier).
- **Manifest**: 43b75f94.
- **Partition**: the one the controls pin, with its bytes at the pinned path (`pinned_partition`), schema 2, epoch 2, and
  its owned digest.
- **Funding**: the EXACT funding bytes, AND `funding_problem` against the pinned Q2 ledger attempt (A4).
- **Operational manifests**: both equal to `make_prod_manifest`'s bytes at 79,200 s (P3).
- **Panel**: `aws_ec2/prod/panel_e2q_e2.json`, regenerated from the pinned partition and its snapshot.
- **Attempt**: the reconciled ledger attempt (key, id, sequence, plan bytes, contract).
- **Plan file**: its bytes equal the bound plan. It must be the panel's work and duplicates with 4 sentinels, 76 slots and at
  least 61 on one replicate, bound to that partition, manifest and lifetime.
- **E2Q2**: allowed only after every E2Q1 attempt was dispositioned.
- **Instances**: at most 2 non-rejected `qual-E2*` instances.
- **Review**: `FAVOURABLE` plus the epoch-2 literal `RELEASE row19-ec2-qualification epoch=2 certificate=<sha256> attempts=<key>`.

`release_state` reports `production.epoch` and `production.production_opmanifest_sha256`. Each epoch's release needs its own
qualification gate: an epoch-2 certificate needs `qualification_e2.ok`, an epoch-1 one needs `qualification.ok`.

`prod_launch.gate_problem` → `production_release_problem` admits production of epoch N only under a release OF epoch N. For
epoch 2 it also needs the production operational manifest the certificate bound. An epoch-1 release never admits epoch-2
production, and the reverse also holds.

`RELEASE_CODE` (epoch 1) is unchanged. `E2_RELEASE_CODE` = `row19_ec2_e2qual.CODE`:
- the S files are dropped (epoch 2 has no S);
- `row19_ec2_e2rules.py` and `row19_ec2_e2qual.py` are added;
- the state module is kept, now the E2Q copy.

### 2.4 The USD 300 allowance (QUALIFICATION_E2.md s.4)

`epoch2_problem` is unchanged. The E2Q runs are named `qual-E2Q1` and `qual-E2Q2`, so `is_e2_qual` counts both against the 2
qualification instances and the USD 300. The tests show:
- a third `qual-E2` instance refuses;
- the 51st production attempt (46 base + 4 extra) refuses;
- with two qualification instances charged USD 279.82, a first extra production batch refuses on the money, while the 46th
  (base) batch does not touch the allowance.

The release branch refuses a certificate when more than 2 non-rejected `qual-E2` instances exist.

`e2q_admission_problem` enforces the plan's retry rule:
- E2Q1 is ONE non-rejected instance. A capacity rejection is no instance and does not consume it.
- E2Q2 needs its own reviewed record (`qual_permit.py --epoch2 --e2q2`).
- E2Q2 needs every non-rejected E2Q1 attempt reconciled and dispositioned.
- E2Q2 is at most one.

## 3. Verification

The counts are in `test_results.txt`.
- **New tests**: 54 + 33 + 81 checks, all passing.
- **Regression**: the 8 existing test files, and the 4 `candidate_e2` test files, give identical counts with the live,
  candidate_e2 and candidate_e2q modules.
- **Pre-existing failures**: every failure is identical across the three module sets and was present before this package
  existed. Two of them are new since 17 Oct and are live-state drift:
  - the v16 controls history and the live job set have moved on (`test_designated_r16.py`);
  - qual-Q1 attempt 4 is now dispositioned (`test_e2_authority.py`).
- **One regression repaired during the build**: the text "does not permit" is kept in the production gate message.

The tests use synthetic records with the frozen-task check stubbed, exactly like the existing STUB tests. They do not
establish:
- 76-worker memory behaviour;
- real producer output;
- cloud capacity;
- five-way interleaving (R6').

## 4. What is still shut, and what is not done

- **Production.** Production stays shut until all of these exist:
  - controls v17 pinning `row19_partition_e2.json` and the helpers below;
  - an activated epoch 2;
  - a `qualification_e2` permission;
  - an E2Q1 (or E2Q2) run;
  - a schema-3 RELEASE certificate;
  - a FAVOURABLE actual-result review with the epoch-2 literal;
  - `release-adopt`.

  The live `ec2_release_state.json` has no `qualification_e2` block, so epoch-2 qualification is not permitted today. A test
  asserts this.
- **Controls v17 pin list.** The list grows beyond DESIGN_e2.md s.5. It must also pin `row19_ec2_state.py` (this copy, in
  place of live `bda200dc`) and `row19_ec2_e2qual.py`, besides the partition, ingestion, qualifier and e2rules.
- **R6'** (five interleaved stubbed admissions and reconciliations) is NOT built here (ruling 13). It is still required.
- **Spot capacity evidence** is still the owner's quota read; it is not here.
- **Staging the E2Q1 bundle on Lengau.** No reviewed tool or runbook was found for staging an EC2 bundle on Lengau for
  ingestion or qualification. The launcher writes results under `s3://<bucket>/results/t1_access/aws_bench/<run>/attempt_<n>/`.
  I can't determine the epoch-1 staging command from the repository. The owning session's EC2 runbook (or the person who
  staged Q1 attempt 4 for reading) would settle it. The qualification command after staging is settled (s.7 step 6, s.8):
  it passes the deployed, hash-checked snapshot with `--snapshot chpc/claims_snapshot_e2.json`. The concrete reviewed bundle
  collection/verification/staging procedure Codex requires before one paid E2Q1 is still not built.

## 5. Choices Codex must rule on

1. **State copy.** The E2Q contracts live in a copy of the adopted `row19_ec2_state.py`, because ingestion's
   `operational_problem`/`plan_problem` read `CONTRACTS` there. The alternative would mutate `CONTRACTS` from a new module at
   import, which depends on import order. E2Q2 is its own contract name with identical geometry, roles and lifetime, so its
   plan and manifest can never pass as E2Q1's. The alternative is one contract under two run names.
2. **Panel as a separate derived file** (`aws_ec2/prod/panel_e2q_e2.json`). The operational manifest must stay the exact
   `derive_operational` bytes, which ingestion byte-compares, so the partition binding cannot live inside it. Duplicates come
   from the claims snapshot the partition binds, not from a later receipt. The launcher still requires each duplicate to be
   Lengau-completed in the admission receipt.
3. **Ingesting a released E2Q attempt that has a non-completion.** R4' admits up to 3 qualifying non-completions, but
   `candidate_e2/row19_ec2_ingest.py` runs the per-slot branch only for class production (`:470`). Without a change, a
   RELEASED E2Q1 with any unproduced slot would HOLD at canonical ingestion, so its 52 coordinates could only be
   dispositioned.
   - `proposed_ingest_released_e2q_partial.diff` (NOT applied) extends `partial` to a RELEASED qualification attempt of
     contract E2Q1/E2Q2.
   - It would also break the source-text check at `candidate_e2/test_e2_ingest.py:351`, which would then need updating.
   - Related: the crash counter `ec2_crash_history` counts production runs only, and the envelope includes the contract name.
     An E2Q fatal-signal crash therefore never counts toward the two-crash rule. Either accept this (the coordinate returns to
     the production pool) or rule that E2Q crashes count.
   - **Ruled 19 Oct (CHANGE, B1) and applied (s.8):** the narrow route is in ingestion REVISION 8 with R4' kept, and
     acknowledged fatal unproduced E2Q owned work counts toward the physical production-envelope two-crash exclusion.
4. **Unproduced duplicates and sentinels.** They are reported and not compared. The 15/20 denominator stays 20, so an
   unproduced duplicate reduces the coverage headroom; it never fills it. A sentinel mismatch is a problem. At least 3
   produced sentinels are required (ingestion's bound).
5. **The R5' synthetic slot.** It is the first work slot (lowest slot number), with outcome 139. It is used only when no
   actual unproduced WORK slot exists. An unproduced duplicate or sentinel does not exercise the work fence or the `ack`
   release, so it does not count as the actual case. Each synthetic world is a fresh sandbox, and the modified-against-
   unmodified replay runs against the first sandbox's journal.
6. **The sandbox `ack`.** On Lengau, the qualifier applies the `ack` RULE (`row19_ec2_e2qual.ack_problem`, a replica of
   `prod_authority.ack`'s checks), because the Mac authority is not imported there. The release test also runs the REAL
   `prod_authority.ack` on the qualifier's sandbox register entry (conformance, both cases).
7. **The epoch-2 review literal** carries `epoch=2`, so an epoch-1-form line never matches. This is a new literal grammar.
8. **The code set**: the S files dropped; e2rules, e2qual and the state copy added; neither `prod_userdata.sh` nor any Mac
   file included, as in epoch 1. The certificate binds file CONTENT as `{promoted path: sha256}`; the pre-promotion resolver
   `code_path` reads the candidate copies, the promoted resolver the promoted files, and byte-identical copies yield the same
   map. The binding is content, not location or installation provenance: a location change alone does not invalidate a
   certificate. **The actual certificate is generated after deployment and activation, from the deployed files** (Codex
   ruling 8, 19 Oct; s.8).
9. **Epoch-2 qualification permission.** It is a new `qualification_e2` block, written only by `qual_permit.py --epoch2`
   (the same drain and fence). Row 23's declared success and the fence are still required. No owner-ceiling acceptance is
   asked, because the bounds are the 17 Oct code constants in `epoch2_problem`.
10. **E2Q2 gating.** E2Q2 requires its own reviewed record and every E2Q1 attempt dispositioned, both at admission and at
    release. A capacity rejection of E2Q1 (state `rejected`) is not an instance and allows E2Q1 itself to be re-admitted. The
    alternative is to require E2Q2 even after a capacity rejection.
11. **The release reads the attempt's plan file** from the Mac ledger path to check the panel and the concentration. That
    file must stay immutable, like epoch 1's bound evidence.
12. **The release branch runs on every `release_state` read**, as epoch 1's does. It also re-runs `funding_problem` against
    the current ledgers, so an edited Q2 ledger attempt or a changed panel shuts production (intended, A4).
13. **The qualifier runs R5' even when an earlier part already failed.** This gives complete evidence, never a release.

## 6. What must be REGENERATED once the final epoch-2 partition lands

The final partition comes from the fresh post-v16 locked snapshot, `declare2` and `verify2` (DESIGN_e2.md s.6 step 4).

1. **`aws_ec2/prod/panel_e2q_e2.json`: the final panel.** Generate it with the maker against `chpc/row19_partition_e2.json`
   and `chpc/claims_snapshot_e2.json` (s.7 step 2). Codex then reviews its exact bytes. If the final rep-24 composition
   cannot carry 61 workers, the maker REFUSES: re-declare the panel (or lower and re-cost the production cap) BEFORE any
   outcome.
2. **`aws_ec2/e2_funding.json`** (already in DESIGN_e2.md s.6). The schema-3 certificate binds its exact bytes.
3. **The tests that read the candidate partition `87edfb9e`**: `test_e2q_contracts.py` (byte-equal to the fixture; the
   explicit rep-24 indices 11..62) and `test_e2q_release.py` (partition, funding and panel fixture). Re-point them to the
   final files, or keep them as candidate-bytes tests and add final-bytes checks. `fixture/panel_e2q_e2_candidate87ed.json`
   stays a fixture and is never promoted.
4. **NOT affected**: `manifest_e2q1_e2.json`, `manifest_e2q2_e2.json` and `manifest_production_e2.json` depend only on
   43b75f94 and the contracts.
5. **Any certificate** made before promotion (s.5, choice 8).

## 7. Exact sequence to run E2Q1 once permitted (NOT run; for the owning session)

Prerequisites, in DESIGN_e2.md s.6 order:
1. Codex reviews `candidate_e2` (done) and this package.
2. qual-Q1 attempt 4 is dispositioned (the ledger shows it done).
3. Take the fresh locked snapshot, then run `declare2` and `verify2`. Then `make_e2_funding.py`, then
   `make_prod_manifest.py --epoch 2 --contract production --expect-s 75300 --out prod/manifest_production_e2.json`.
4. Make the panel and the E2Q manifests (from `aws_ec2/`):

       python3 make_prod_manifest.py --epoch 2 --contract E2Q1 --expect-s 75300 --out prod/manifest_e2q1_e2.json \
           --partition ../chpc/row19_partition_e2.json --snapshot ../chpc/claims_snapshot_e2.json --panel-out prod/panel_e2q_e2.json
       python3 make_prod_manifest.py --epoch 2 --contract E2Q2 --expect-s 75300 --out prod/manifest_e2q2_e2.json \
           --partition ../chpc/row19_partition_e2.json --snapshot ../chpc/claims_snapshot_e2.json --panel-out prod/panel_e2q_e2.json

5. Codex reviews the exact partition, funding and panel bytes.
6. Controls v17 (pins as s.4), its review and adoption, then promotion and deployment of every helper.
7. Canonical activation on Lengau, then `ec2_sync.py cycle` and a fresh whole-role receipt.

Then, only after the reviewed E2Q1 permission record exists:

1. `python3 aws_ec2/qual_permit.py --epoch2 --record <path of the reviewed E2Q1 permission record, relative to aws_ec2/>`
2. `python3 aws_ec2/prod_authority.py budget`. Check the remaining USD 2,300 envelope and the USD 3,000 cap against the
   allowance.
3. `python3 aws_ec2/prod_authority.py inventory`, then `python3 aws_ec2/ec2_sync.py cycle`, then a fresh refit receipt (it
   must be no older than 2,700 s at admission).
4. Dry run (an EC2 DryRun call; authorisation only):

       python3 aws_ec2/prod_launch.py --contract E2Q1 --epoch 2 --partition ../chpc/row19_partition_e2.json \
           --manifest prod/manifest_e2q1_e2.json --panel prod/panel_e2q_e2.json \
           --snapshot ../chpc/results/row19_screen --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz --dry-run

5. The same command without `--dry-run`. This is ONE instance, worst case USD 27.92 against the allowance. The reaper
   reconciles it.
6. Stage the reconciled bundle on Lengau (s.4: the staging command is not documented), then install the current inventory.
   On Lengau:

       t1py chpc/row19_ec2_qualify.py e2 --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json \
           --authority <root>/ec2/authority/inventory.json --key qual-E2Q1/1 --bundle <staged bundle> \
           --opmanifest aws_ec2/prod/manifest_e2q1_e2.json --prod-opmanifest aws_ec2/prod/manifest_production_e2.json \
           --panel aws_ec2/prod/panel_e2q_e2.json --snapshot chpc/claims_snapshot_e2.json \
           --funding aws_ec2/e2_funding.json --sandbox <scratch> --out <cert_e2q1.json>

   `--snapshot` is required in this command (s.8): the reviewed panel `f04a5e43` records `chpc/e2_final/claims_snapshot_e2.json`,
   which the controller tree does not hold; the deployed copy `chpc/claims_snapshot_e2.json` is refused unless its sha256 and
   claims digest are the ones the partition binds (`31cc268f`). The panel is not edited.

7. Bring the certificate to `aws_ec2/` on the Mac and commit it. Codex writes the actual-result review. On FAVOURABLE it
   emits `RELEASE row19-ec2-qualification epoch=2 certificate=<sha256> attempts=qual-E2Q1/1`.
8. `python3 aws_ec2/prod_authority.py release-adopt --certificate <cert> --review <review>`. Then inventory and
   `ec2_sync.py cycle`. Then canonical ingestion of `qual-E2Q1/1`, through ingestion REVISION 8's released-E2Q per-slot route
   when it has a qualifying unproduced slot (s.8). Then `ack`.
9. Production admissions follow under the five-instance ceiling:
   `prod_launch.py --contract production --epoch 2 --manifest prod/manifest_production_e2.json ...`.

Branches:
- **E2Q1 ends without a usable bundle for an external cause** (spot interruption before the memory gate, or capacity):
  1. `disposition` and `ec2_sync`;
  2. a separately reviewed E2Q2 record;
  3. `qual_permit.py --epoch2 --e2q2 --record <...>`;
  4. the same launch with `--contract E2Q2 --manifest prod/manifest_e2q2_e2.json`.
- **NO_RELEASE or INCONCLUSIVE**: stop. There is no retry by outcome; return to the owner with a costed alternative
  (QUALIFICATION_E2.md s.3).

## 8. REVISION: repair for Codex's adoption review of 19 Oct (B1, B2, "Before one paid E2Q1", rulings 3, 8, 13)

Review: `reviews/2026-10-19_e2_adoption_codex_review.md` (CHANGE 3: A FAVOURABLE; B CHANGE 2 = B1, B2; C CHANGE 1 = C1).
Written 19 Oct 2026 (R052, Claude, bounded job). Local candidate repair and tests only: no AWS, ssh, Lengau, promotion,
deployment, adoption or live-file edit; `chpc/e2_final/` (A, FAVOURABLE) is unchanged, panel `f04a5e43` included. The changed
reviewed files are edited in place with a revision note in each; their reviewed bytes stay in git at RSC `92a62f6`.

| Review item | Change | Test |
|---|---|---|
| B1, the route (choice 3) | `chpc/candidate_e2/row19_ec2_ingest.py` REVISION 8 (`277c51b0`): only schema-2, released, class-qualification E2Q1/E2Q2 joins production's per-slot route, real class kept, every check kept, plus R4' (at most 3 non-completions of all roles). Detail: DESIGN_e2.md s.8 | `test_e2q_ingest.py` s.1-s.3 (44 checks in all); `candidate_e2/test_e2_ingest.py:351` updated |
| B1, the crash ruling | `aws_ec2/prod_authority.py` REVISION 8 (`e4897991`): `ec2_crash_history` reads production and `qual-E2*` runs, acknowledged ingestions only, the `ingest_ack` unproduced map (owned work only); `crash_envelope` gives E2Q1/E2Q2/production one label only at production's producer geometry (instance type, workers, volume) and the recorded production instance type; the lifetime stays as recorded | `test_e2q_ingest.py` s.4: mixed real E2Q1-ACK + production-ACK excludes the coordinate and the allocator skips it; one alone does not; lifetime, instance type, geometry, epoch-1 Q1, censored, dispositioned, duplicate/sentinel controls do not; REVISION 7's rule on the same ledgers excludes nothing |
| B2 | `row19_ec2_qualify.py` REVISION 6 (`1d8eee78`): `_timeline` validates every field by kind (unsigned integer; unsigned finite decimal for load averages) and requires strictly increasing time; `resource_observation_problems` checks MemTotal > 0, 0 <= MemAvailable <= MemTotal, RSS >= 0, running workers 0..planned BEFORE any calculation; each occupancy line joins at most one memory sample. A malformed or impossible observation is a problem (NO_RELEASE), never an exception or a release. Occupancy match, peak over all samples, 184 GiB and the status limits unchanged. The method is shared with the epoch-1 path (stricter only) | `test_e2q_qualify.py` s.6: the review's counter (12 samples, total 192 GiB, available 193 GiB) is NO_RELEASE (REVISION 5 gave RELEASE, peak 0.0 - reproduced on the reviewed function bytes); 12 copies of one timestamp NO_RELEASE; one occupancy line over 12 samples NO_RELEASE; a valid positive control RELEASES; 15 parser negatives each a failed verdict, none an exception |
| Before one paid E2Q1: snapshot path | the reviewed command passes `--snapshot chpc/claims_snapshot_e2.json` (s.7 step 6; qualifier REVISION 6 docstring); panel `f04a5e43` not edited | `test_e2q_qualify.py` s.6: the recorded path absent in the deployed layout refuses without `--snapshot`; with the deployed copy the same panel bytes RELEASE and bind its sha256; a tampered copy refuses |
| Ruling 8 wording | choice 8 above and the `row19_ec2_e2qual.code_path` docstring (`5ceba551`, docstring only) state content binding, not location | - |
| Ruling 13 | the per-slot R5' presentation is unchanged; complete evidence still never releases with problems; B2 repaired | as above |

**What is NOT done here (still required, unchanged by this revision).**
- The concrete reviewed bundle collection/verification/staging procedure before one paid E2Q1 (only the qualification
  command's snapshot argument is settled).
- R6' (five interleaved admissions and reconciliations), capacity evidence, the separately reviewed E2Q1 permission record.
- `migration_v17` (preflight, archives, deploy, rollover, adopt) and its review.
- The schema-3 certificate itself: generated after deployment and activation from the deployed files.

Counts and the regression are in `test_results.txt`; the controls and promotion map rebuilt on these bytes are in
`chpc/candidate_v17/DESIGN_v17.md` s.8.

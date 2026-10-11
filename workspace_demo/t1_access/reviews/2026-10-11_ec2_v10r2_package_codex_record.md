# EC2 v10r2 package: controls version 11, qualification and release review

Date: 11 October 2026 UTC / 10 October local. Reviewer: Codex,
`GPT: R052 Entropy paper`, native `01a0d19e-2127-7051-9a61-6db771088559`.
Incoming handoff `9c9e12aa-06d9-5c3a-9385-7913e41283b7` was accepted after
ownership commit Unimog `170286b5`, before review edits or delegation.

Read the whole brief
`prompts/2026-10-11_codex_r052_ec2_v10r2_package.txt`, committed at Unimog
`2c2cb687ed1e0fe74804b98f233f09ad39b36b87`, SHA256
`38e61def903ef783b7d9e6e7289226f6760b77cf43497d050b1ef0de9c64a815`.
The reviewed package is RSC `ce78d22` + `414d95c` + `0816240` +
`a2f7d86bb5bfe6cad4dd4992d64efde9709a7504`. Current bytes of all listed
inputs were compared with that committed tree. This is a repair review of
`3dc0daf9`; earlier opinions remain confined to their exact package bytes.

## System and three answers

The scientific B200 task remains frozen. Lengau's adopted generation 9 continues
independently. Version 11 adds an isolated qualification S campaign, a combined
refit-plus-S funding limit, and repaired EC2 helper contracts. A later reviewed
partition and canonical activation would reserve a fixed block for EC2. Mac
inventory generations and root acknowledgements govern ownership; checked
publication and fresh whole-role receipts govern admission. Q1 owns 48 block
coordinates; Q2 and S are comparisons outside the denominator. Q1's coordinates
enter the canonical denominator only after a reviewed actual qualification release.

**(a) FAVOURABLE to the exact controls below, only with `partition:null` and no
EC2 activation, register or installed inventory on the production root.**
Versions 1–10 are unchanged from the `b85584c6` lineage. The only changed
top-level field is the programme: it adds the isolated S campaign. Version 11
declares that campaign and the combined 60,000 core-hour sub-envelope.

```text
ADOPT row19-screen-controls sha256=6342aa101c80ecdff360a729b14187b0e18575eab6a1f4ef274916ccc7463634 version=11
```

This is an adoption opinion, not an adoption performed here. Install all exact
pinned controller/helper bytes together; take fresh exact-generation verifier
and whole-role receipts before subsequent admissions. Regenerate the refit
pilot artifact against the new controls from the same actual qualification
`3820ac0e…` and review `d64600f8`, retaining `max_job=100`; no new fit is needed.
The null adoption does not declare an EC2 block, permit Q1/Q2/S, or close the
active contracts below. A real partition needs its separate reviewed declaration.
Old candidate files are unchanged but their opinions must not be combined with
different global helper bytes.

**(b) NOT FAVOURABLE as the executable Q1/Q2 authority, ingestion and status
basis.** The inventory lifecycle/root scope, current adopted authority and
dispatch checks below remain incomplete. Row-23 success and the accepted
USD 45 ceiling do not repair them.

**(c) NOT FAVOURABLE as the complete executable qualification and release
package.** The isolated S construction, finite-success coverage and sampled
packing rule are favourable repairs. The remaining authority, dispatch and S
evidence issues below need repair before the combined package is
executable. This is not an actual-result qualification verdict.

The owner's approval is already recorded at Unimog `8d48648d` / RSC `26e67e83`:
USD 45 for one Q1 and one Q2 attempt (28 + 17), then direct production after
successful qualification with a favourable actual-result review and certificate.
No further owner go is needed for that transition within the USD 2,300
production envelope and USD 3,000 further-spend cap. Retries still require an
owner decision. The submitted release state has acceptance true, but row-23
declared success, qualification permission and production release false.
Source reports row-23 attempt 5 still running; this review neither polls nor
restarts it. No launch, adoption, remote import or account operation was performed.

## Disposition of the preceding repairs

| Earlier group | Static disposition |
|---|---|
| R1-1 activation/history | Canonical versus sandbox mode, adopted proof creation, retained lineage and epoch-aware EC2 provenance are implemented. Canonical consumers still need to authenticate the current adoption (R2-2). |
| R1-2 root inventory/disposition | Monotonic root installation, request/fence/ack/confirm and missing-inventory alarms are implemented. Refresh/state changes reuse a sealed generation and ACK lacks canonical root identity (R2-1). |
| R1-3 post-watch artifacts | Both admissions recheck registered canonical record/timing/status bytes and installed inventory. Live-inventory freshness at use still needs checking (R2-1). |
| R1-4 finite paths/S/release | Finite predictor-band success is enforced, S producer artifacts are checked, Q1 release is derived and a pinned favourable review is required. S declaration and complete evidence preservation remain incomplete (R2-4). |
| R1-5 STOP | Mac now accepts only proved S3 absence; all other failures refuse. Recheck immediately before paid dispatch, after staging/waits (R2-3). |
| R1-6 packing/recovery | At least ten chronological memory samples joined to full 76-worker occupancy are required. R5 accurately states ingestion-publication replay only; producer/host and interrupted-transfer recovery remain undemonstrated. |
| R1-7 paid integration/region | Production-side benchmark exclusion, attempt/request region, recovery region refusal and production-rate reporting are implemented. Fresh benchmark admissions remain outside the global lock; this needs the operating restriction below or shared admission. |
| S route | Existing kind `shard`, unchanged worker, isolated manifest/root/campaign, numeric jobs 1/2, full reservations, programme lock and combined funding check are implemented. Recheck screen STOP/HOLD after the lock wait and bind the declared producer evidence (R2-3/4). |

## Remaining work

### R2-1. Complete inventory generations, canonical root acknowledgement and freshness

`aws_ec2/prod_authority.py:336–375` includes `at`, current attempt state,
charges and release in a seal, then overwrites both `inventory_g<N>.json` and
`latest.json` using the current generation. The `inventory` CLI (`:438–461`)
does not bump it. In contrast, `row19_ec2_state.install_inventory:191–194`
correctly refuses different sealed bytes at a generation already installed.

A supported static trace is: install sealed generation N on Lengau, later run
the documented inventory command to refresh its six-hour freshness, then copy
and install the refreshed view. Its new timestamp changes the seal but N is
unchanged, so installation refuses. This also affects ordinary attempt state:
`prod_launch.py:275–277` bumps/seals an intent before `L.finish` changes it to
launched/ambiguous/rejected; `bench_reaper.py:81–91` later reconciles under the
run lock without a global bump. Resealing that reconciled view at an already
installed N is refused. An unrefreshed intent inventory does not become a
reconciled current inventory merely because the reaper ended.

Retain generation files immutably, assign a new monotonic generation to every
changed or refreshed seal, and serialize coherent ledger snapshots/state changes
with the authority. Make the documented refresh, launch/recovery, reconciliation
and disposition acknowledgement paths installable. Include a regression for
refresh after a previous install, state transition at an installed generation,
and delayed acknowledgement while another inventory is refreshed. Preserve
root refusal of old or different same-generation views; weakening that check
would discard the repair.

The disposition handshake also lacks root identity. `row19_ec2_root.py:22–33`
accepts any manifest's `storage.root`; `row19_ec2_state.py:223–224` creates an
ACK without root, frozen manifest or canonical/sandbox mode. Mac confirm
(`prod_authority.py:411–434`) validates the real inventory and attempt fence,
but not which root acknowledged. A supported wrong-manifest trace is to install
the genuine requested inventory using the isolated S manifest/root, then confirm
its genuine ACK on the Mac. Ownership is released although the canonical root
was not fenced and can still hold the previous owner view. Bind canonical
root/manifest identity into installation and ACK, require it on confirm, and
distinguish/reject sandbox acknowledgements. This is separate from R5: its
rebound plan/inventory remain different. No claim that R5 currently produces an
acceptable canonical Mac ACK is made here.

`current_problems:241–244` validates installed inventory with `max_age=inf`.
Status checks freshness for live/owning attempts, but a clean watch taken just
before the six-hour threshold can remain usable for 2,700 seconds after the
threshold. Recheck that same live/owning freshness condition at admission use;
allow old fully terminal history. Ingestion already applies the six-hour default.

### R2-2. Authenticate the current adopted controls in canonical consumers

Canonical proof creation now calls the adoption authority
(`row19_partition.py:221–235`), closing the old mint-before-guard trace. The
consumer `activation_problem:282–291` instead checks a 64-character adoption
digest, retained version-entry equality and continuing partition pins; it does
not authenticate the current controls adoption. Mac `controls_doc` / admission
and ingestion use that JSON lineage without the programme adoption check.

Supported migration trace: retain a valid canonical proof from adopted version
N, place a later candidate N+1 at the canonical controls path with N retained
and the same partition pinned, but leave the adoption record at N. Those
consumers accept the lineage although Lengau's controller correctly refuses the
unadopted controls. This is an authority-contract gap, not demonstrated coordinate
overlap. Require current tracked/adopted controls in each canonical consumer
before checking retained proof lineage. Preserve explicit sandbox mode and
legitimate historical proof reuse under later adopted same-partition versions.

### R2-3. Recheck STOP and time-sensitive admission immediately before dispatch

The repaired S3 error classification is favourable. Mac admission checks STOP
at `prod_launch.py:175`, then stages four uploads with bounds of 1,800 seconds
each (`:265–266`) before journaling and `L.finish` dispatch (`:275–277`). STOP
written during staging can therefore precede a new paid RunInstances call.
The instance-side check helps prevent fitting, but does not prevent paid dispatch.
Recheck STOP and receipt freshness after staging, immediately before issuing,
including any re-issue path. Test STOP created by a staging step and an expired
receipt with zero RunInstances calls.

S similarly checks S-root/screen-root STOP and screen `ec2/HOLD` before waiting
for the programme lock (`row19_ec2_shadow.py:126–137`), then reserves and qsubs
without rechecking (`:146–155`). A new screen STOP/HOLD during that wait can
still admit S; the unchanged worker checks only its isolated root's STOP. Recheck
all declared STOP/HOLD sources after acquiring the lock and before reservation
and dispatch. No running job is stopped or repeated by this review.

### R2-4. Bind S to its declaration and preserve its validated producer evidence

The qualifier accepts any exact isolated derivation passed as `--s-manifest`
(`row19_ec2_qualify.py:173–178`), rather than verifying the current controls'
declared S manifest/root/campaign. Bind it to that reviewed declaration. The
fixed jobs, settled producing entries, statuses and producer-named timing are
substantial repairs; they do not authenticate a different isolated campaign as
the programme-declared S campaign.

`row19_ec2_qualify.s_evidence` validates S timing at `:219`, but its bound
object (`:225–228`) hashes the manifest, ledger, plans, statuses and records;
it does not hash the validated timing files or task bindings. The certificate
therefore does not preserve all the S producer evidence it claims to bind.
Include those digests and the declared producer/admission/funding lineage in
the retained S evidence contract, or accurately state and review any cooperative
provenance condition. Do not represent copied record bodies as independent S.

### Release preservation and operating conditions

`prod_authority.release_problem:236–303` correctly requires schema-2 RELEASE,
coverage, memory/replay summary, current supplied code hashes, frozen manifest,
current partition SHA, reconciled Q1 id/sequence/plan, an exact certificate-specific
RELEASE line and presence of `FAVOURABLE` in the review text. The parser does not
require an exact positive verdict line; the actual review must clearly grant that
verdict and emit the release literal only then. It does not rehash the certificate's activation, inventory,
operational manifests, bundles, Q2 plan or S bindings. Those remain certificate
and actual-review attestations. This closes the former label-only release gate;
no ordinary stale-release bypass of a genuine favourable review was established.

Before actual-result adoption, state the complete required binding and evidence
preservation rule, including the expected code-file set. Validate retained
immutable plans/bundles/S producer evidence and the permitted current transition
or explicitly review its attestation scope. Dynamic inventory legitimately moves:
do not require every later inventory to equal qualification's historical copy.
Keep Q1 as the only released qualification attempt; no new owner approval is
needed once the actual reviewed release passes.

Completed ingestion replay is also narrower than the general replay description:
after Mac ACK and installation of the resulting inventory marking
`ingestion="ingested"`, ingestion refuses that state before
its completed-replay branch (`row19_ec2_ingest.py:271–273,317–322`). State the
permitted pre-ACK replay window or support validated completed replay after ACK.
This is a recovery limitation, not demonstrated unsafe publication.

Production-side `exclusion_problem` refuses an already live/unresolved benchmark,
but `bench_launch.py` does not share the authority lock and has no reciprocal
production/qualification exclusion. That alone is not an atomic mutual-exclusion
contract: a fresh benchmark may start after the production-side check.
After row 23 ends, either put every paid admission/recovery under the shared
authority or explicitly freeze fresh benchmark admissions/recoveries while
qualification/production is active. Do not describe a one-sided observation as
enforced exclusion in both directions. The existing row-23 attempt is preserved.
Likewise, keep supervision in an unresolved attempt's recorded region; the
unchanged in-supervision region check is a stated remaining operating limit.

S's reviewed isolated route reserves 1,152 core-hours for each of jobs 1 and 2,
2,304 total, against its own ledger and the shared programme 100,000 plus combined
refit/S 60,000 envelopes. It uses 24 cores, 48 hours, 120 GB and `haswell_reg`.
The manifest must be installed in the job clone with the declared bytes; controls
must actually be reviewed/adopted; row-23 declared success and reviewed
qualification permission must be backed. Keep all attempts, failures, statuses,
settlement and STOP evidence outside the canonical denominator. No launch is
licensed by this component assessment while the complete package is held.

Q1 worst USD 27.9185 and Q2 USD 16.5435 total USD 44.462, within accepted
28/17/45 ceilings. S reserves 2,304 core-hours rather than only the approximately
1,200 expected charge. Frozen science/seeds/draws/B/pairing and independent
Lengau/bank admission gates remain. Full remaining screen funding is still not
provided by this bounded approval. Remove the release state's stale ceiling-note
phrase saying the already accepted USD 45 still needs acceptance.

## Exact pins and verification limits

| File below `workspace_demo/t1_access/` | SHA256 |
|---|---|
| `chpc/candidate_v10r2/row19_screen_controls.json` | `6342aa101c80ecdff360a729b14187b0e18575eab6a1f4ef274916ccc7463634` |
| `chpc/candidate_v10r2/row19_screen_admit.py` | `a5fac9a96e2073e9c89ca52ced9667692e4d65e838d93feb60b63fa5015fbeca` |
| `chpc/candidate_v10r2/row19_screen_status.py` | `76c11aaabb7ceca6dd684bbac115d7d5ae02e82d779e332ce6c7d3cdc28f1178` |
| `chpc/row19_partition.py` | `bf9f9d501b1956cc38636f44bc488df26812a3b18cb76fe312e0d5d24c470f90` |
| `chpc/row19_ec2_state.py` | `536fcb45f4801539dfd69010510b44c30f00656c83f1de96ab8b02f2da8b18de` |
| `chpc/row19_ec2_ingest.py` | `1308977a44abb709e3d682ad3fee4e42f9fbcca3411df200f9a896f3486f9846` |
| `chpc/row19_ec2_qualify.py` | `45f9e529057c80c3cb7783f8f1ff3e3b431eb7a8e68d79a4e53546d550a2d10f` |
| `chpc/row19_ec2_root.py` | `a1e86997fee6578c10736aa314f2a940ed2f00c0c57426ae8bc6b65dd7a501a3` |
| `chpc/row19_ec2_shadow.py` | `c23eb9fd3a1abf6605c7561fc5e891b0993efc5b02946c7182893bc5ed97a269` |
| `chpc/row19_qual_S_manifest.json` | `eabbda2aea74cd6885917b7b249109ead521ce516415c026c11a6d9e51400161` |
| `chpc/programme_gate.py` | `10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0` |
| `chpc/row19_shard.py` | `828d59640f10cc33fcba7d98d075371945ca4b74ddaca841ea86100fc47ff383` |
| `aws_ec2/prod_authority.py` | `2b3841186023633bb06ea4d0c9b5f7226f2378a1ce37d36b1c6b9961794d5efc` |
| `aws_ec2/prod_launch.py` | `bb0969ff43e9c419b44c6857e4a866c819fc91445e62d4a91c0f933916916271` |
| `aws_ec2/prod_stop.py` | `dc466d322f997481aa073fb4513d770813bd48924743a61f952a39028a8300e5` |
| `aws_ec2/prod_userdata.sh` | `36982555c566aa9bb4d17576fa0fa7d0719c749bb63ac49db7c7f258db440ca7` |
| `aws_ec2/make_prod_manifest.py` | `8da7991138a5b5cbf76396dd46c9fadcd9e582acfedfbcbace98ffdc4c5ce11c` |
| `aws_ec2/bench_launch.py` | `b70e7788306520db86d59344d19ae905cc25d7596d8e65a4134732369e8c3e40` |
| `aws_ec2/bench_reaper.py` | `8ce8aecce95eb426ee74bc8f475647b737689c72e273d17d51ed0bd3719b7eb3` |
| `aws_ec2/budget_baseline.json` | `a49d8e3dd0865a2cd20ba385d74bc19e86cfe835551b846eaed4835ea75bb727` |
| `aws_ec2/ec2_release_state.json` | `a3b90282dd0e2b8eda222fe05a7cec482f43d994ff53ef273ce212abbcbeec46` |
| `aws_ec2/qual_S_plan.json` | `11ca19d6f2f381ef7909d88ef6cf479819fab4ff79576575af2cc061fba277f9` |
| `aws_ec2/QUALIFICATION_PLAN.md` | `bcc9656781939e463a2c29569401a6314fd1b02abc4a884c619b36455b64fdad` |
| `aws_ec2/PRODUCTION_DESIGN.md` | `a9983e480962661b1a0a3f81010f84768a1b241ac8a011e099ad040c9e3b02fc` |
| `chpc/row19_screen_manifest.json` | `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c` |
| `chpc/row19_screen_controls.json` | `45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07` |
| `chpc/row19_screen_verify.py` | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `chpc/row19_screen_release.py` | `7a67fd1fc3ca60d77c62ddcaea5d4e11a9ec87ac6b2b02f0bc75ab34a366507f` |
| `chpc/row19_screen_resources.json` | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |

Static review only: whole brief/design/qualification plan, source contracts,
three bounded read-only peer reviews, committed-byte and SHA256 comparisons,
Python AST and JSON parsing, controls history and deterministic budget arithmetic.
No submitted source was imported or executed; no runtime test was rerun.
Source reports partition 50, ingestion 60 STUB/59 REAL (failed-fit skipped in REAL),
status 26, qualify 17, shadow 15, authority 54, launcher 46, user-data 11,
benchmark launch 13, reaper 1 and cleanup 1. These are source reports, not
reviewer execution or actual qualification evidence. The real-record report and
fixtures, scientific/private outputs and current-run payloads were not opened.
No source edits, fits/simulations, launches, AWS/account/SSH/Lengau actions,
worktrees or pushes. Only this review and own R052/lifecycle records are owned.
Claude retains source/design/current docs/frontmatter/INDEX/ledger/tracker,
adoption/deployment/qualification/dispatch. Foreign files and source jobs stay
preserved. Full-bank R2 remains target-visible/concept-batched with prior
exposure, not later blind calibration; old reports are closed and not repeated.

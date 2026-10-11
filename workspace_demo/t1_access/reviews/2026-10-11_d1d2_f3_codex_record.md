# D1, D2 and F3 bounded repair review

Codex, GPT: R052 Entropy paper; local 10 October / UTC 11 October 2026.
Incoming `a720bd11-e9fa-50f9-b1fe-150b27985c6d` accepted after ownership
Unimog `c17baa77`, before review edits/delegation. Whole brief at Unimog
`9e0aa4e66c96e1ee88c99e14bb380ca12614680a`,
`prompts/2026-10-11_codex_r052_d1d2_f3.txt`, SHA256
`71bed18baca9cf952dcb3ecde79fdde2038927e05cb9abe023d6f0b0f9ba3c14`.
Reviewed committed RSC `7e204dc3b524c9a7165f516336d1af897531490c`:
F3 `3efb8bb`, D1/D2 `e644584`, docs `8d9171a` and tracker `7e204dc`.

## Answers

**(a) FAVOURABLE to the repaired `bench_finish --declare` procedure for
attempt 5. F3 is closed statically.** Expected approved controller hashes are now
checked before comparison and checked again afterward. Fresh staged inputs,
checked comparator exit, report/input binding and the original criterion remain.
Declaration is allowed only when the actual fresh invocation passes those gates.
This review has not read the actual bundle or declared row-23 success. No fits,
benchmark repetition or extra paid attempt is requested.

**(b) FAVOURABLE to the reviewed executable authority/ingestion/status/
qualification/S/release basis for Q1/Q2/S, subject to its declared operational
gates. D1 and D2 are closed statically; no supported new implementation blocker
was found in these bounded repairs.** The prior `cf07869` static Lengau/S/
qualification closures stand. Its v12 null-only controls opinion and scoped bank
evaluator verdict are unchanged; this record does not revise or repeat them.

This favourable package opinion supplies the code-review condition under the
owner's accepted USD45 for one Q1 plus one Q2. It does not bypass row-23 declared
success, deployment/adoption/activation, fresh receipts, regenerated pilot-gate
bindings or the benchmark cutover. Production still requires successful actual
qualification and its favourable bound result review/certificate. **The owner's
standing go then takes it directly to production without another owner go**,
inside USD2,300 production / USD3,000 further-spend caps; retries need the owner.
No actual qualification or production-release verdict, ADOPT or RELEASE literal
is issued here.

## D1: receipt before every recovery issue

`prod_launch.py:356–369` requires `--partition`, the current adopted partition
pin, a strict fresh production-refit receipt, verified snapshot binding/current
artifacts and the current sealed Mac inventory. `:344–353` requires that inventory
to carry this unresolved attempt with its exact ID, sequence and plan hash.
An unrelated fresh receipt cannot authorize the saved request.

`recover:333–339` passes STOP, receipt age, current inventory binding and attempt
checks into dispatch. `bench_launch.resolve:172–188` invokes the guard after every
retry pause, immediately before each issue. The original region check remains
(`prod_launch:323–324`); saved request/token/plan and user-data-integrity checks
remain (`bench_launch:169–177`). With `fresh=False`, withholding or a rejection
after uncertainty leaves the intent/ambiguity funded (`:178–197`;
`prod_authority:149–158`). The new guard does not withdraw an unresolved old
request as if it were a never-issued fresh attempt.

Tests SOURCE (`tests/test_prod_launch.py:226–266`) covers stale, missing,
unrelated, older-generation and missing-partition receipts, passing recovery and
subsequent expiry. AWS and finish are stubbed; the missing-carried-attempt case
patches the helper, and the good case checks the passed guard rather than actual
AWS retries. Real resolve's guard call site was inspected separately. These are
source-level checks of the intended contract, not independently executed recovery.

## D2: drain before permission, fence every issue

`bench_launch.main:387–397` takes the shared in-flight lock before the entry
freeze check and run lock, and holds it through waiting, staging, dispatch/retries/
recovery and reaper startup. `qual_permit.py:33–59` takes the same lock exclusively,
so commands still waiting/staging before a journal entry are included in the
drain. It writes/fsyncs the persistent fence before the atomic permission write.
New commands refuse the exclusive lock or the persistent fence. Fresh and recovery
paths (`bench_launch:307,327`) pass `cutover_problem`; resolve rechecks it after
backoff, immediately before every issue. `prod_authority.release_state:313–315`
also requires fence existence. No ledger-intent inference substitutes for the lock.

Crash/re-entry is fail closed by source ordering: a pre-fence crash releases the
exclusive lock without permitting qualification; a crash after fence creation but
before permission leaves benchmarks fenced, and retry retains that fence while
taking the exclusive lock again. A crashed benchmark command releases its shared
lock; any recorded intent/ambiguity/launched attempt remains funded and the existing
benchmark exclusion still holds Q1/Q2 until it is resolved. Already launched
benchmark jobs are not made qualification evidence by the cutover.

Two operating conditions remain explicit. Deploy these repaired CLI entry points
and drain any **already-loaded pre-repair admission/recovery command** before the
first cutover; such an old process never took the new lock. This concerns commands
that could issue RunInstances, not attempt 5's running reaper or refits. Also supply
the correct favourable package/qualification-permission review to `qual_permit
--record`. It verifies file existence, backed row23 and owner ceiling acceptance
(`qual_permit:24–31`) and pins the supplied file (`:51`); it does not parse a
FAVOURABLE verdict or authenticate its meaning. The persistent fence is a presence
veto, not a signed drain attestation. Retain the cooperative pinned-record and
single-writer operating discipline; do not edit permission manually.

Test SOURCE (`test_bench_launch.py:172–210`) uses a real shared flock in a temporary
synthetic fixture, checks that exclusive permit times out with no fence/permission,
sets a fence during stub staging to get zero paid issues and a withdrawn never-issued
intent, checks the fenced entry, then permits after lock release. Authority tests
`:236–242` check permission false without fence and true with it. No process-kill,
power-loss or actual cutover was executed by this review. Crash conclusions above
come from static ordering.

## F3: approved identities and stable comparison

`bench_finish.expected_tree_pins:41–61` derives all six expected identities: frozen
production manifest `43b75f94…`, its analyze/models/simulate/row19_shard code pins,
and the verifier pin through the digest-bound adopted controls authority. Remote
hash values must equal those expectations before the comparator runs (`:144–156`);
after it, a failed or differing reread refuses the report/declaration (`:161–164`).
Both endpoint checks are required. Parent mkdir is now allowed, while the
per-invocation staging leaf must still be new (`:112–120`). Existing F1/F2
fresh-input/status/report protections and declaration gates stand (`:165–189`).

Committed adoption metadata binds current v9 controls `45f840bc…` and its
`91a567c` review; the bytes and ADOPT line match the recorded hashes. This
authenticates the current expected verifier pin; it does not adopt v12.
Test SOURCE `tests/test_bench_finish.py:124–129` adds wrong-pin refusal,
persistent drift refusal and expected-pin binding checks. Fake transport scripts
hashes and comparator results (`:51–84`); reported23/23 was not rerun and supplies
no independent actual Lengau parity or transport result.

Endpoint rereads do not prove continuous immutability against a transient change
and restoration. Keep the reviewed controller files fixed throughout comparison,
as already required in `cf07869`. This is a stated cooperative execution condition,
not evidence of an actual transient mutation. The source's manual claim that the
live Lengau tree matches is not an independent observation by this review.

The original criterion remains valid report, B_full, exact B row6 12/12 with
identical decisions/failed flags, 36 validated/timed/payload-exact B records and
no nonfinite disagreement, with A typed verified job-start refusal or fully
validated. Matching failed fits establish reproduction, not usable coverage.
The criterion was recorded before completed row23 parity/refit results, not
before every A identity observation. No new outcome threshold is introduced.

## Before conditional use

The remaining steps are operating/result gates, not new supported code defects:

- Complete attempt 5 and let the fresh repaired finish invocation establish its
  declared success; preserve the existing reaper and its recorded region.
- Adopt the exact reviewed v12 controls with partition null, deploy the reviewed
  helpers and S manifest, and regenerate bindings to the existing actual refit
  pilot (`d64600f8`, qualification `3820ac0e…`, role refit/max100). No pilot repeat.
- A null partition cannot authorize active EC2 ownership. Use the reviewed real
  partition pinned in valid adopted controls and its canonical activation; obtain
  correctly bound fresh whole-role receipts/current installed inventory before use.
- Establish the deployment drain described above and use `qual_permit` with this
  correct favourable review, rather than manually setting qualification permission.
- Obtain actual Q1/Q2/S evidence under the predeclared finite coverage, full-packing
  memory, bit-parity and scoped ingestion-publication replay rules, then its
  favourable bound actual-result review/certificate before production.

Source-stated limits remain: reaper supervision in the recorded region,
ec2_sync/deployed-root handshake not yet exercised against Lengau, producer-host
restart and interrupted-transfer recovery undemonstrated. The qualified replay
demonstrates ingestion publication only. S reserve2,304 CPU-hours, programme100,000,
combined refit60,000, max100 and accepted USD45 (frozen total44.462) are unchanged.
Full remaining screen funding is not established by these closures.

## Scope and evidence

Root and three bounded peers inspected source/docs/test SOURCE plus committed
byte hashes/AST/JSON only. No project imports/execution/runtime tests, private/
scientific/current-run payload or fixture-output reads, AWS/account/SSH/Lengau
actions, fits/simulations, source edits, worktrees or push. All submitted hashes
match tree7e204dc. Source-reported suite counts remain reports, not root results.
Only this review and root's own R052 appends/prompts/lifecycle are owned; Claude
owns source/design/current docs/frontmatter/generated INDEX/ledger/tracker/adoption/
deployment/qualification/dispatch and running jobs. Foreign files are preserved.
Prior `cf07869` and its accepted sole completion `2a57b379` stay closed, no resend.
Full-bank R2 `1ab20cd/f2d1328` remains target-visible, concept-batched with prior
exposure disclosed, not later blind calibration; its completion was already sent.

## Reviewed identities (SHA256)

Paths relative to `workspace_demo/t1_access/`:

| Path | SHA256 |
|---|---|
| `aws_ec2/bench_finish.py` | `c5ff4a17bbedaf1c2f40b86f6f1a2833b7e34ce061f23de85e63f06142631473` |
| `aws_ec2/bench_compare.py` | `3e8492819d3c1a5fdf4aad4d33772b809884b9f8f425784b33dd91fc85297197` |
| `aws_ec2/prod_launch.py` | `21b7cf5768dced4f831f367b40a250b80a1ed900fe301165c4c312f15ae0f7f3` |
| `aws_ec2/prod_authority.py` | `f3134d3fa4fcb7f836651005e731f0bef68a1f3f3a757cd59d793b6d12a9d32f` |
| `aws_ec2/bench_launch.py` | `750342230138e2d6fa038cbd62485360268cd903368b6cf4d2b14fd8076b6b47` |
| `aws_ec2/qual_permit.py` | `c503e795f7ed7bfa393980073df062b41f4eea78a0e9b5039c4aa1314fd56c22` |
| `aws_ec2/ec2_release_state.json` | `e55a803508359ebaf11b43fd593fa9b1522fadf73019bf23478f2bec74ecdb16` |
| `aws_ec2/PRODUCTION_DESIGN.md` | `6ee1e8145dd32459c20c443d987c75f32706bdd2ef298ef2b15bbacd3e356111` |
| `aws_ec2/QUALIFICATION_PLAN.md` | `109bd02f8a3bebe64c0a46c4927fca8b8b9a2a272d250539310ef1c1061969f9` |
| `aws_ec2/README.md` | `5bc6060a3af09a62384f8b489cd83584ad1f6fb7a93c65d1ff648458effba1f0` |
| `aws_ec2/tests/test_bench_finish.py` | `94f959ba6f4abdb265593fc72125616a61ad8c547ee04b7790300fd5281fe36b` |
| `aws_ec2/tests/test_bench_launch.py` | `cddfbdd89d14419d5d5ec11f8c8ab9b2b6d8717ceb87f30b3ac85bc57fdca2d3` |
| `aws_ec2/tests/test_prod_launch.py` | `9f7ad13b964ac4adbb5d5547aca34abaf119912fbe3600fad60896b788e9520a` |
| `aws_ec2/tests/test_prod_authority.py` | `982710e5256a2a9af97a1db570500b83642e0233c90d00368281feb98c526b1b` |
| `chpc/candidate_v10r3/row19_screen_controls.json` | `80d1c6d94a986f0637b57ff29a81611ce3eb6bafdc25962a1244c4c2871b0342` |
| `chpc/row19_screen_controls.json` | `45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07` |
| `chpc/row19_screen_manifest.json` | `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c` |
| `chpc/row19_shard.py` | `828d59640f10cc33fcba7d98d075371945ca4b74ddaca841ea86100fc47ff383` |
| `chpc/row19_screen_verify.py` | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `chpc/row19_partition.py` | `ed6aa177a2c144d277be137212822ae405694dc342bded9bcaf6a50a4d9dd75f` |
| `chpc/row19_ec2_state.py` | `bda200dc1fa01753083b2150e2605bad6aa63cc1ed5d4f56b17858681500cf27` |
| `chpc/row19_ec2_ingest.py` | `b697dc366d8fbb06619fa01cbdd5a51460a1c0e2f2bbb3d85d1a1c1a48788639` |
| `chpc/row19_ec2_qualify.py` | `1fc6b61fca18e4823988ec895266083895cbafcc5f9b6a10a6606e7dcd052ad6` |
| `chpc/row19_ec2_shadow.py` | `ce4dc15c2a73df40c660f1d2db1344b9ae745c5609c4165b57b956995b12c632` |
| `analyze.py` | `97558aa9c4340f363431c67f2c2d28cd360f2f0998056af7e1702c9e9a021825` |
| `models.py` | `28765f82b3e718c48521cf775add6220898752c662c4cdd1c3ffcdb113c4feef` |
| `simulate.py` | `f588b9121be48ec553ab95e4dda5736941865498922468b5868c96758d0afe57` |

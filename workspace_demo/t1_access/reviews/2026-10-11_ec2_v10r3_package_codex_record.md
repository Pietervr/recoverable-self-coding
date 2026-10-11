# EC2 v10r3 package, row-23 finish and bank seed-domain re-review

Codex, GPT: R052 Entropy paper; local 10 October / UTC 11 October 2026.
Incoming handoff `28dc930c-2bc2-5149-94c2-5d87175f21cd`, accepted after
ownership commit Unimog `667c0302`. Brief: Unimog `dfbf756a`,
`prompts/2026-10-11_codex_r052_ec2_v10r3_package.txt`, SHA256
`f91356f0264c8244b99e4f5c0163582050b608176ac18fedfecb98cb1f66f900`.
Reviewed committed RSC tree `cadfd5c1d9d1ffa23ebce97f51e17ec1f803e733`:
`b8d9c58`, `d622499`, `cb2d2ef`, row-23 repair `cd12ca5` and bank repair
`9afcc03`. The run log committed at cadfd5c was **not read**.

## Four answers

| Question | Verdict and boundary |
|---|---|
| (a) Candidate controls v12 | **FAVOURABLE for adoption with partition null**, exact SHA below. This is a controls opinion, not activation or paid dispatch approval. |
| (b) Q1/Q2/S executable basis | **NOT FAVOURABLE as a complete dispatch basis yet**: recovery receipt freshness remains open (D-1); benchmark cutover must drain all in-flight admission/recovery commands (D-2). Assigned Lengau, S and qualification repair contracts are favourable statically. |
| (c) Attempt-5 `bench_finish --declare` | F-1 and the identified F-2 stale-input/report paths are repaired. **Acceptable only with a retained check of the remote controller hashes against the reviewed frozen tree before declaration, and a stable tree during comparison.** The command alone does not enforce that check (F-3), so unattended declaration as submitted is not favourable. No repeat fit or benchmark is requested. |
| (d) Bank evaluator seed-domain repair | **FAVOURABLE within `compatible()`'s declared scope**: actual manifest-derived domains replace caller-supplied authority. Target digest/review, numerical body and coverage authority remain separate consumer gates. |

Literal controls opinion, **partition null at adoption**:

```text
ADOPT row19-screen-controls sha256=80d1c6d94a986f0637b57ff29a81611ce3eb6bafdc25962a1244c4c2871b0342 version=12
```

This record does not adopt, activate, declare row-23 success, qualify EC2 or
release production. Actual Q1/Q2/S results and their favourable bound review are
still required. The owner's accepted USD45 for one Q1 and one Q2, followed
directly by production if qualification succeeds and the actual-result review is
favourable, stands; **no further owner go is needed for that successful transition**.
Production USD2,300 / further-spend USD3,000 limits stand; retries need the owner.

## Controls identity and retained limits

Every reviewed source/doc/config byte matches the submitted committed tree;
Python files were parsed as AST and JSON decoded without importing or executing
project code. Versions 1–11 and every top-level field/programme in v12 equal the
unchanged v11 candidate. Candidate admit/status bytes are unchanged. The currently
adopted v9 baseline is unchanged. Latest v12 partition is null and its listed
helper hashes match the submitted bytes. The old v11 `6342aa10…` literal still
points to unchanged bytes.

S declaration, isolated manifest/root/campaign/plan, jobs 1/2, kind `shard`,
24-core/48-hour/120-GB `haswell_reg` resources and 2,304 CPU-hour reservation remain.
Programme 100,000 CPU-hours, combined refit 60,000 CPU-hours and max100 remain.
Future activation requires the reviewed partition, adopted current controls and
the existing actual refit-pilot gate: RSC `d64600f8`, qualification hash
`3820ac0e0c28a9cf484f02be3a9c377891aa81595413978d74e7de1eddee4678`,
role refit/max100. Regenerate bindings when helper identities change; no new fit
or pilot repetition is required by this controls repair.

Q1 arithmetic is USD27.9185 and Q2 USD16.5435, total USD44.462, within the
accepted USD45. This is frozen-plan arithmetic, not a new market quote or actual
spend. Owner acceptance remains true; qualification permitted, row23 success and
production release are false in the submitted state. The stale ceiling note was
removed. Full remaining screen funding is not established by this package.

## Repair disposition

| Prior group | Static disposition at cadfd5c |
|---|---|
| R2-1 inventory generations / canonical ACK | Closed for the reviewed code contract. Each seal gets a new generation; generation archives are created once, collisions refuse, latest publication is atomic. Canonical root/manifest/mode are ACK-bound; Mac confirms only canonical frozen-root ACKs. Installation is locked and monotonic; same-generation equality and stable ACK survive retries. Installed live/owning inventory older than six hours refuses admission. |
| R2-1 post-ACK replay | Closed for the reviewed replay contract. Acknowledged ingestion can revalidate an already completed publication under current installed inventory, adopted controls and valid activation; it cannot publish a missing/ingesting register entry. Current owner/sequence fencing is retained. This does not demonstrate producer-host restart or interrupted-transfer recovery. |
| R2-2 adoption authority | Closed. Canonical controls go through the existing adoption authority. Activation validates current adopted controls; an earlier proof survives only if its exact entry survives and every later version retains the same partition. Mac admission, ingestion and qualifier use that authority. |
| R2-3 Mac STOP / receipt age | Fresh admission closes the staging/dispatch window: guard after uploads, before journal and immediately before each issue through that path. Recovery still checks only STOP: D-1 below remains. |
| R2-3 S STOP / HOLD | Closed as an admission/worker contract. S rechecks under the programme lock before reservation and immediately before qsub. A hold after reservation leaves the funded reservation unbound. The job starts a 60-second mirror of screen STOP and EC2 HOLD into the S root's STOP, waits on worker PIDs and stops the mirror. The worker checks STOP before each fresh resample; no interruption of an in-flight fit is promised. |
| R2-4 S producer provenance | Closed as an unsigned cooperative contract. Qualifier requires the adopted isolated S manifest/root/campaign/plan, settled producer/PBS binding, complete terminal status, valid finite full timing, scientific record validation and exact task binding. It binds timing, task, producer and declaration hashes. |
| R2-4 release binding | Closed statically. Certificate and authority use the same exact RELEASE_CODE set including S manifest; release checks current code, manifest/partition, reconciled Q1 ID/sequence/plan and a favourable actual-result literal. Bound scientific inputs/certificate/review must remain immutable; inventory can legitimately advance. This is not an actual-result or release verdict. |
| Benchmark exclusion | New benchmark commands refuse once qualification is permitted or qual/prod attempts exist. Entry-only checking does not drain commands already past the check: D-2 is the required cutover condition. Existing attempt-5 reaper is preserved. |

Sources: `prod_authority.py:380–407,448–485`; `row19_ec2_root.py:26–60`;
`row19_ec2_state.py:197–282`; `row19_partition.py:226–236,310–324`;
`row19_ec2_ingest.py:275–347`; `row19_ec2_shadow.py:108–195`;
`row19_ec2_qualify.py:192–301`; `prod_authority.py:75–78,275–301`.

### D-1: receipt freshness is absent from `--recover`

`prod_launch.py:182–196` defines receipt-time validation and a combined STOP/age
guard. Fresh admission uses it after staging and passes it to `finish`
(`:295–313`). In contrast, `recover:317–331` loads an unresolved intent/ambiguous
attempt, checks recorded region and STOP, then calls:

```python
L.finish(run, led, att, fresh=False, guard=lambda: stop_problem(run, a.snapshot))
```

An unresolved request can therefore be re-issued later when its admission receipt
has expired, while STOP is absent. The path neither loads/revalidates a current
receipt nor applies `receipt_age_problem`. The brief/docs' claim that receipt age
is checked before **every** re-issue is not supported by this path. This is a
static supported trace, not evidence of another actual launch.

Before qualified use, either revalidate the correctly bound current receipt at
every recovery issue or explicitly prohibit re-issuing recovery until that check
is established. Preserve original attempt/token/region/plan/ownership and funded
ambiguity; observation/reconciliation of an already launched instance need not be
turned into a new launch. Retain negative evidence for stale/missing receipt with
zero RunInstances calls and unresolved attempts still funded. Do not let a fresh
but unrelated receipt authorize an old request.

### D-2: qualification cutover must fence in-flight benchmarks

`bench_launch.py:347–361` checks `freeze_problem` only at entry, before its run
lock. Fresh admission can subsequently wait or upload before writing its intent
(`:295–307`). Its `finish` call and the recovery call (`:322–327`) pass no freeze
guard. A command admitted while qualification is forbidden can still be staging
without a ledger intent when permission is enabled; qualification's ledger check
does not see that pre-journal command. It can later journal and issue beside Q1.

An explicit operating cutover is adequate: before permitting qualification, drain
or hold **every** in-flight benchmark admission/recovery command, including those
waiting or staging before their first journal entry; forbid new ones thereafter.
Checking ledger intents alone does not prove this drain. Alternatively add and
check a pre-issue freeze fence, including retries/recovery and the cutover boundary.
No second global authority design is prescribed. No actual parallel launch is
claimed, and this condition does not require stopping attempt 5 or its reaper.

The recorded-region reaper limitation remains: resolve the attempt in its recorded
region. Source reports ec2_sync has not yet been exercised against Lengau's newly
deployed root tool. Deployment/handshake and eventual actual qualification evidence
are future operational checks, not reasons to repeat already completed pilot work.

## Row-23 finish

F-1 is closed. `bench_compare.py:120–148` requires arm A's pinned manifest and
the same HELD line in retained job-start evidence before accepting typed refusal.
`:282–295` requires readable, duplicate-free, exact 42 names for refused A or
78 for both arms, matching declaration count/outcomes and integer-zero outcomes.

The specific F-2 stale-cache/report paths are closed. `bench_finish.py:76–131`
fetches into a new local directory, makes a new remote directory, uses a unique
report and verifies comparator SHA and transferred bundle digest/count. Comparator
exit propagates; only 0/3 allow retrieval and only 0 plus the unchanged criterion
can declare. `:134–153` binds run/attempt/stamp, exit, comparator, controller tree,
bundle and report hashes. A comparator crash with a passing-looking report is
refused; destination-only files cannot survive a new empty stage.

### F-3: recorded controller hashes are not compared to approved values

At `bench_finish.py:122–124`, `sorted(pins) == sorted(TREE_PINS)` checks the
six **filenames**. The hash values are recorded, not compared to expected reviewed
hashes. The successful fake in `tests/test_bench_finish.py:70–83` supplies all-zero
hashes. Thus the brief's “controller-tree pins checked” describes an identity
record, not approved identity enforcement.

For attempt 5, compare all six remote controller hashes with the frozen reviewed
tree and retain that acceptance before `--declare`; keep the tree unchanged while
the comparator imports/runs. An expected-hash gate plus wrong-hash negative case
is an alternative. This condition can be satisfied without repeating fits or
purchasing another benchmark. Real transport also needs the remote attempt parent
to exist (`:85` uses plain mkdir for the new leaf); absence fails closed. Fake
transport creates parents and does not prove that setup.

The criterion still means valid B_full report; B row6 exact 12/12, identical
decisions/failed flags; 36 validated/timed/payload-exact B records and no nonfinite
disagreements; A either typed verified job-start refusal or fully validated.
Matching failed fits establish reproduction, not usable coverage. The rule was
recorded before **completed row-23 parity/refit results** (owner conditional go
about 20:40Z, Unimog `7c6626e6` at 21:16:38Z on 10 October); A identity observations
already existed. “Before any result” would be inaccurate.

## Bank evaluator

`row22_target.py:210–250` derives bank seeds from the manifest and checks binding
digest/count; it checks the named screen manifest with the reviewed default
`row19_screen_admit.seed_domain_problem`, derives that domain and rejects overlap.
Caller-supplied domains are merely compared with derived domains. The original
`bank_seeds=[]` bypass is closed. Missing/empty/foreign domains, digest/count
mismatches and overlap refuse. Test source `test_row22_bank.py:247–286` covers
these cases; its injected checker does not replace the reviewed production default.

This repair does not supply target-file review/digest, target numerical-body
validation or coverage authority (`row22_target.py:184–185`). The earlier full-bank
R2 review remains complete at `1ab20cd`; `f2d1328` remains target-visible and
concept-batched with prior exposure disclosed, not later blind calibration.

## Verification and ownership

This is source/doc/test-source inspection by root and three bounded read-only
peers, plus byte hashes/AST/JSON/arithmetic. No project imports, runtime tests,
scientific/private/current-run payload reads, source edits, simulations/fits,
AWS/account/SSH/Lengau operations, worktrees or push. Source-reported test counts
(including real-record ingestion) remain source reports, not independent results
of this review. Qualifier fixtures stub scientific/timing readers; shadow fixtures
inspect PBS script text without executing its mirror. Those limits do not erase
the inspected real verifier/timing/task call sites, but are not live evidence.

Only this review and Codex's own R052 log/prompts/lifecycle are owned. Claude
retains source/design/frontmatter/generated INDEX/ledger/tracker/adoption/deploy/
qualification/dispatch and attempt 5/Lengau job monitoring. Do not poll, restart or
stop them from this lane. Earlier v10r2 `299f4b7` and row-23 `3f67eaf` reviews and
their accepted sole completions are closed; this record answers the new repairs.

## Reviewed byte identities

All paths below are relative to `workspace_demo/t1_access/`; all hashes SHA256.

| Path | SHA256 |
|---|---|
| `chpc/candidate_v10r3/row19_screen_controls.json` | `80d1c6d94a986f0637b57ff29a81611ce3eb6bafdc25962a1244c4c2871b0342` |
| `chpc/candidate_v10r3/row19_screen_admit.py` | `a5fac9a96e2073e9c89ca52ced9667692e4d65e838d93feb60b63fa5015fbeca` |
| `chpc/candidate_v10r3/row19_screen_status.py` | `76c11aaabb7ceca6dd684bbac115d7d5ae02e82d779e332ce6c7d3cdc28f1178` |
| `chpc/row19_partition.py` | `ed6aa177a2c144d277be137212822ae405694dc342bded9bcaf6a50a4d9dd75f` |
| `chpc/row19_ec2_state.py` | `bda200dc1fa01753083b2150e2605bad6aa63cc1ed5d4f56b17858681500cf27` |
| `chpc/row19_ec2_ingest.py` | `b697dc366d8fbb06619fa01cbdd5a51460a1c0e2f2bbb3d85d1a1c1a48788639` |
| `chpc/row19_ec2_qualify.py` | `1fc6b61fca18e4823988ec895266083895cbafcc5f9b6a10a6606e7dcd052ad6` |
| `chpc/row19_ec2_root.py` | `ceba9b3285b6bc66fff32bdc79ebbb70f09e5701794e0fa9764b1f253c169005` |
| `chpc/row19_ec2_shadow.py` | `ce4dc15c2a73df40c660f1d2db1344b9ae745c5609c4165b57b956995b12c632` |
| `chpc/row19_qual_S_manifest.json` | `eabbda2aea74cd6885917b7b249109ead521ce516415c026c11a6d9e51400161` |
| `chpc/programme_gate.py` | `10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0` |
| `chpc/row19_shard.py` | `828d59640f10cc33fcba7d98d075371945ca4b74ddaca841ea86100fc47ff383` |
| `chpc/row19_screen_verify.py` | `d8d3c73ba916e211c3bc479e445547b2dab02e2faead78b87ff7f22d675ac3ec` |
| `chpc/row19_screen_release.py` | `7a67fd1fc3ca60d77c62ddcaea5d4e11a9ec87ac6b2b02f0bc75ab34a366507f` |
| `chpc/row19_screen_resources.json` | `f5352bc3ae7c5195e2081baa5685b4533fc8add0d5cfd5c48009e72610bebba0` |
| `aws_ec2/prod_authority.py` | `d75ab704df511d02f07305678d6c0f30760c2437a03bc7351e5f6c1f91463416` |
| `aws_ec2/prod_launch.py` | `c0fa307d6a5a603ab4186d4489cbff3d4117a1444ab885f88a8d8fd24596f2e1` |
| `aws_ec2/prod_stop.py` | `dc466d322f997481aa073fb4513d770813bd48924743a61f952a39028a8300e5` |
| `aws_ec2/prod_userdata.sh` | `36982555c566aa9bb4d17576fa0fa7d0719c749bb63ac49db7c7f258db440ca7` |
| `aws_ec2/make_prod_manifest.py` | `8da7991138a5b5cbf76396dd46c9fadcd9e582acfedfbcbace98ffdc4c5ce11c` |
| `aws_ec2/ec2_sync.py` | `a5787c1f24e557248015947a5a48b99daae9768a6263994182dad4849a36a687` |
| `aws_ec2/bench_launch.py` | `a8d84f260730d1e60bb440ecca363055cdb0143298db4786dab3fcf021a9f8a6` |
| `aws_ec2/bench_reaper.py` | `301a06d8a50725ec74a531e4b4f71c13d94991bdf6e271bce6783356085291af` |
| `aws_ec2/budget_baseline.json` | `a49d8e3dd0865a2cd20ba385d74bc19e86cfe835551b846eaed4835ea75bb727` |
| `aws_ec2/ec2_release_state.json` | `e13311e47bcd1b38898c2273679f2596d8cd35eb10e0e41991296f5a71177a68` |
| `aws_ec2/qual_S_plan.json` | `11ca19d6f2f381ef7909d88ef6cf479819fab4ff79576575af2cc061fba277f9` |
| `aws_ec2/QUALIFICATION_PLAN.md` | `772b5368ead64d05eec5af0efdecd234e7166b4c207d7281b07cb82c1101e462` |
| `aws_ec2/PRODUCTION_DESIGN.md` | `48286feb5fda04487a1cc8f5228ed510a663afbafa7987525ba7df5aaf7204ea` |
| `aws_ec2/README.md` | `e779db26dc64701836f118e4cc05acb1b7ca9a52ef89e9cffe18098c1d224509` |
| `aws_ec2/bench_compare.py` | `3e8492819d3c1a5fdf4aad4d33772b809884b9f8f425784b33dd91fc85297197` |
| `aws_ec2/bench_finish.py` | `d8b6f18f5190ab36c2e10c01ccf4cae645c5dd1b067dd23df437e400f1aea70e` |
| `chpc/row22_target.py` | `7fcb1525b8c24049cbea65fb50fa835e15e8ca44b07413b001a56fce8f792bc1` |
| `chpc/row19_screen_manifest.json` | `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c` |
| `chpc/row19_screen_controls.json` | `45f840bc768f8729155f8ad39bd2f27dbae9525322398867dfff76d9ee310c07` |

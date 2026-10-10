# R052 — concrete EC2 v10 package second opinion

10 October 2026. GPT: R052 Entropy paper; native
`01a0d19e-2127-7051-9a61-6db771088559`; topic
`95bf527b-9f8e-598f-ae95-96a5d2b035af`.
Incoming `5d8f70af-caee-5262-b658-a8bcc8e26a7b` accepted after ownership
Unimog `b203c4f2`, before review edits or peer review.
Brief: Unimog `e0658ab4282651419aa50e3d8fe764137cf4a3a1`,
`prompts/2026-10-10_codex_r052_ec2_v10_package.txt`, SHA256
`5cf00a512b1363707709653fa75ef48a930c583d5ab7e1bebb602c69d138868c`.
Package reviewed: **RSC `17202f3`**, including its `68d119e`/`139ed04` ancestry.
The earlier `f3dd3d7` opinion was favourable to build; it did not adopt this implementation.

| Requested judgment | Verdict | Scope |
|---|---|---|
| (a) Controls v10 candidate | **FAVOURABLE with partition null and no EC2 register** | Controller-only promotion for the existing Lengau lane; the EC2 branch and partition activation are not approved. |
| (b) Authority/ingestion as the basis for Q1/Q2/S | **NOT FAVOURABLE as submitted** | The ordinary producer path and several authority/validation paths fail the required contracts below. No qualification or production launch/import follows from this record. |
| (c) Qualification plan and release rule | **Direction favourable; NOT FAVOURABLE as an executable release package** | Preserve the predeclared panel. Complete the construction, funding, memory, recovery and successful-path criteria before launch; review the actual qualification before release. |

```text
ADOPT row19-screen-controls sha256=9e702b6f49f62ba00d774cb2041ca17f0350866421cb3c46bc72be86d449aa69 version=10
```

This literal adoption is restricted to the exact null-partition candidate above.
It supplies no EC2 permission. Activation needs a later reviewed controls version
and concrete partition, repaired EC2 code, row 23's declared success, and the
actual qualification. The owner's standing conditional go remains in force;
there is no expiry or request to repeat it. No independent Lengau or bank job is
stopped by this review. Existing science, dataset identities, seeds/draws, B200,
100 screen datasets, pairing, CHPC caps, bank limit, maximum refit job 100,
HEAL hold and existing STOP rules remain unchanged.

## Exact bytes and verification limits

| File under `workspace_demo/t1_access/` at `17202f3` | SHA256 |
|---|---|
| `chpc/candidate_v10/row19_screen_controls.json` | `9e702b6f49f62ba00d774cb2041ca17f0350866421cb3c46bc72be86d449aa69` |
| `chpc/candidate_v10/row19_screen_admit.py` | `becb1372c1937bd2b763e66f5fe92f5dce281cf5bc50648eb6f430cbedaf9fab` |
| `chpc/candidate_v10/row19_screen_status.py` | `10e2e4082ca16de727e6ccdb157897cc54ff9d5639802eeaed2a44709b59c4ec` |
| `chpc/row19_partition.py` | `94002fef6dac71dc97fd78d8b4d7ff1a414a948d5794f10b1c324d55296da94f` |
| `chpc/row19_ec2_ingest.py` | `a6c0b48cd773c903a06c3e2a408784bef786afacd0ae760f9aa80d492ec08b52` |
| `aws_ec2/prod_authority.py` | `6ad483fb74e4b391c7782f24d1c73042a0ca3c02812cec432a761206c5342e6e` |
| `aws_ec2/prod_launch.py` | `b1a5edf91d2d9d4c9fc23443e586a95a7ce422e01b99a2e6e538abd6ae39083b` |
| `aws_ec2/prod_userdata.sh` | `a0ecd7de4f0312b0beae87e26ca5a39aa82c98166c469bb1eb3464d7bf445fe5` |
| `aws_ec2/make_prod_manifest.py` | `f92759ccd168fcef83017afd23fda46a6c0d51a59bf2784d8d8c5ee733d81042` |
| `aws_ec2/budget_baseline.json` | `598dcf5f44cb0a05f87dfbe21902f482d8ce5206511bf8ea79759dc31039d437` |
| `aws_ec2/QUALIFICATION_PLAN.md` | `3e3d0bb1a3e9f9e3906c2f43000a913779431d790601efdd8a6c170e7abf0ad1` |
| `aws_ec2/PRODUCTION_DESIGN.md` | `74df28516f059a76933227ba8355238605327820cbf9223ea583e71954bb7997` |

The pointed design and qualification documents were read end-to-end. Review used
the actual candidate diffs, source and retained test source, with three read-only
peers covering partition/admission, resource/authority and ingestion/status.
Metadata-only AST/JSON parsing passed, all latest file pins matched, and controls
are an append-only v10 extension: earlier versions, programme, history manifest
and deployment are identical to the adopted v9 controls. No source was imported
or executed, no scientific record/fixture/result was opened, and no runtime test,
fit, simulation, AWS/account/SSH/Lengau action, worktree or push was performed.
Reported 15/15, 8/8, 9/9 and 13/13 are source test reports, not Codex reruns.

Source commit `bf0ad77` arrived during review and changes the design, launcher and
user-data STOP paths; its diff and `prod_stop.py` were read as supplemental
evidence. It does not change the candidate/partition/ingestion hashes above and
does not close the other blockers. References below use `17202f3` line numbers
unless explicitly labelled `bf0ad77`.

## Null-partition promotion

`partition()` returns None, `RP.blocked(None, ...)` is false, and status returns
an empty EC2 summary when no register exists. Thus the current Lengau planning
and reconciliation remain functionally unchanged. The main status caller was
updated to the four-tuple; the retained three-tuple test fixtures still need their
routine migration. No production external three-tuple caller was found in the
scoped source search.

Promotion must install the extra pinned modules and the unchanged dependencies
together. A generation-9 receipt/gate does not become generation 10 by changing a
label: `generation_problem()` still checks the latest version, verifier and
adopted controls digest (candidate admit:965–978). Obtain fresh v10 verifier and
whole-role receipts, preserve/archive the existing actual gates, and regenerate
the qualification from the same retained actual pilot records/plans/bindings.
Actual-artifact gate adoption remains a separate condition before further
admissions. The favourable scientific pilot judgment is preserved; no new fits
or synthetic replacement qualification are requested.

## Required repairs before EC2 qualification or activation

**V10-1 — Bind activation and operational derivation at admission.**
`prod_launch.admit()` loads any manifest-valid partition and checks its epoch;
it checks only the operational manifest's claimed epoch and parent SHA
(49–55). It does not require the adopted latest controls' partition pin, a bound
cutover proof, row-23 declared success, or an allowed qualification/production
release state. A copied parent label cannot prove an unchanged scientific
projection. `make_prod_manifest.py` changes only the intended operational fields
when used correctly, but the consumer must verify those exact changes and the
reviewed expectation, packing and lifetime. Bind every dispatched plan/request
to the reviewed operational manifest, instance contract and active partition.

`row19_partition.cutover` is a useful complete historical scan, but it is an
unlocked observation printed by a standalone CLI (55–105). Neither loader nor
admission consumes its proof; new admission checks only freshly created jobs.
Make activation a serialized cutover with the programme/plan authority, covering
all existing/restored/reserved plans and binding the resulting observation to the
partition/controls. Before any later epoch, enforce predecessor/provenance and
explicit terminal/fenced transfer of uncompleted coordinates; a predecessor
string alone does not retain prior EC2-completed ownership outside a smaller
current block.

**V10-2 — Enforce current ownership and receipt completeness across providers.**
`prod_authority.owner_of()` exists, but ingestion never consults it or a current
authority snapshot. It trusts an exported reconciled attempt; `sequence` is
copied into the register and never compared with a current coordinate owner
(ingest:166–209). An old dispositioned/reassigned attempt can therefore publish
despite the claimed late-writer fence. The Mac ledger's `ingestion` controls
allocation, while the Lengau register's state changes separately: provide a
checked, recoverable acknowledgement under the authority lock before releasing
claims. Pending output remains owned and funded; all producer/cost history stays
retained.

The EC2 status adapter sees only attempts already present in the ingestion
register, not intent/live/ambiguous/reconciled-but-uningested attempts. It adds
`receipt.ec2` without digest-binding that register, plans, statuses, epoch,
fencing or settlement; admission still consumes the PBS job authority
(status:386–436, 614–620; admit:`expected_bound`, `receipt_problem`,
`transition_problem`). A newly journaled attempt can leave the old admission
comparisons unchanged. Bind and consume a coherent inventory of **every** EC2
attempt and state, including failed/no-record attempts, with separate USD
funding. Validate finite, nonfuture receipt time, explicit fresh/production,
schema, role, exact controls/manifest/partition and retained snapshot hashes.
`snapshot_state()` currently accepts missing `fresh` and future/NaN time and
derives completion from filenames alone (launcher:27–41).

**V10-3 — Freeze the actual bundle before hashing it.**
This is an ordinary producer failure: user-data redirects output through tee
to `env/userdata.log` (15), hashes every root/env file including that log (139),
then echoes the end message and transfer disposition (141, 40), appending to the
already-hashed file. A healthy final bundle consequently fails `check_bundle`.
Freeze/close all included writers before constructing the final inventory, or
explicitly exclude mutable transport logs under a documented transfer contract.
Keep the scientific and terminal evidence immutable; test the real lifecycle
shape. Supplemental `bf0ad77` retains this ordering.

**V10-4 — Validate complete plans, worker outcomes, statuses and attestations.**
`check_bundle()` checks a minimal profile/problem label and returns outcomes
without comparing their exact names/counts or typed zero exit codes to the plan
(98–115). `plan_units()` does not enforce exact ownership/sentinel equality,
unique slots/coordinates, one index per slot, allowed roles, required four
sentinels or the pinned partition hash. Status files are optional (155–157).
In status reconciliation their existence is the only content check (432–433).
The retained ingestion success fixture supplies no statuses, and the status
fixture supplies `{}` files while asserting no alarms. These passing fixtures
do not prove the required worker contract.

Require complete canonical inventory and plan cardinality/roles, exact producer
and slot bindings, expected outcome names and typed terminal codes, attested
effective B_full toolchain/profile, and valid terminal statuses. Check identity,
new/resumed/left, exit/reason, finite wall/memory, stop conditions and hashes
before publication and again in the whole-role view. Procedure-level failed
records remain included and reported as failed; worker/campaign failure must
not masquerade as completed qualification or silently disappear.

**V10-5 — Finish replay, overlap and publication integrity.**
Overlap/sentinel comparisons happen before taking the plan lock (175–197).
Another ingestion can publish between that comparison and the later
`preexisting=True` check (205), which then skips the coordinate without
rechecking the newly present payload (217–218). Recheck live ownership and
overlap under the lock. `publish_copy` checks the published hash only after
linking (54–74); verify the frozen temporary bytes before canonical publication.
An already-`ingested` replay returns success without checking registered
canonical record/timing/status hashes (211–212), and the status adapter does not
compare them either. Validate both completed and interrupted replay, plan and
binding consistency, every registered hash and status. Maintain the current
timing-first/record-second journal and never overwrite contrary evidence.
The swapped-timing fixture covers `ingesting`, not completed replay.

**V10-6 — Make the budget global, evidenced and large enough for the declared jobs.**
The launcher/reaper lock is per run/epoch. `budget_problem()` reads other runs
without a common reservation lock and applies USD 2,300 only to the current
epoch (authority:46–62); concurrent epochs can race and a later epoch resets
that production envelope. Serialize reservation and settlement across all runs;
count every production epoch/qualification/retry against one USD 2,300 envelope
and all further AWS spending against USD 3,000. Preserve per-attempt price and
worst-case unresolved charging.

USD 400 is not yet a demonstrated upper bound for the exact 12 Sept 21:50 UTC
cutoff: it is only USD 12.98 above the source's USD 387.02 since 13 Sept and does
not establish the missing partial day or cost lag. Obtain the attributable
baseline and conservative pending-charge allowance without assuming the rounded
number covers them. The request is for 60 GB storage whereas the reused
`ANC_H=0.0094` model describes the benchmark's 40 GB setup; account for actual
storage and the eu-north-1/Oregon transfer/S3 overhead and every setup/grace/
upload/idle/retry charge.

Even at an exact 22-hour lifetime, the reused grace/reserve formula gives
`22.75 * 1.2094 + 0.10 = 27.61385` for Q1 and, using the proposed Q2 cap,
`22.75 * 0.7094 + 0.10 = 16.23885`: USD **43.85270**, already above the declared
USD 43 before the other corrections. These are arithmetic on source constants,
not current market prices or a forecast. Declare and enforce honest rounded-up
Q1/Q2 ceilings; no source cap lift or paid rerun is implied. S reserves **2,304**
core-hours at its declared requests; ~1,200 is an estimate of charge, not its
worst reservation. Qualifying S needs explicit isolated campaign entries,
programme admission and funding inside existing caps.

**V10-7 — Construct the predeclared qualification and complete its release rule.**
Keep Q1's 24 Lengau-completed coordinates, 48 block coordinates and four
sentinels, Q2's 24 fresh-host block repeats, and S's 48 isolated shadows.
The current launcher always allocates 72 block work coordinates plus four
sentinels and hard-codes the benchmark's c7a.24xlarge contract; it cannot construct
Q1's outside-block panel or Q2's c7a.12xlarge/24-worker/0.70-cap job. Add explicit
immutable qualification plans with isolated output/claim classes; qualification
outside the block does not create shared production ownership. Distinguish
qualification permission from later production release in the actual admission
and ingestion consumers.

The plan correctly compares float-bit payloads, includes failed flags/reasons,
uses fresh processes/host, holds outputs and asks for replay. Complete it with
predeclared successful finite-path coverage across the target reps/indices,
separate failed-fit parity reporting and a declared inconclusive/stop outcome if
that coverage is absent. All-failed agreement alone cannot qualify successful
fitting. Do not choose replacements by observed outcomes or buy extra settings.
Qualify restart/re-entry and paired publication/transfer recovery under the
actual producer contract; the ingestion interruption is only one part of that
evidence. Bind the actual comparison/attestation/resource/recovery/replay
certificate to the code, manifests, plans and every release consumer, with a
separate actual-result review before canonical release. Q1's 48 coordinates may
enter the denominator only after that release; Q2/S/sentinels remain duplicates.

76 workers at the reported 2.32 GiB implies **176.32 GiB**, with 15.68 GiB of
nominal 192 GiB left for everything else. Measure peak aggregate host/process
memory and overhead at Q1's simultaneous packing; a per-worker 4.5 GiB threshold
alone permits a total exceeding host memory. Retain per-instance B_full,
identity and sentinel gates on every later host; the first also needs the full
qualified production release. Row 23's job-start identity is not row 23 success.

**V10-8 — Complete common STOP semantics before enabling EC2.**
Submitted `17202f3` leaves STOP open. Supplemental `bf0ad77` adds a local/S3
STOP command, normal-launch refusal and S3 polling, but polling starts **after**
workers launch and performs unbounded AWS calls; with one index per worker the
entire initial batch can already be fitting. `--recover` bypasses admission STOP
checks. The supplement does not automatically propagate Lengau's common root
STOP to all active EC2 epochs, and ingestion has no STOP/held-release check.
Implement and qualify bounded propagation, startup/dispatch/recovery checks and
explicit rules for in-flight fitting, salvage and canonical publication. A
sentinel difference must hold all relevant output and stop new production;
retaining charged evidence is compatible with refusing release. Manual
`prod_stop.py` alone does not establish automatic common propagation.

## Disposition

Claude retains implementation/design, current summaries and frontmatter,
ledger/tracker, adoption, deployment, qualification and dispatch. Route this
record and its requirements to that existing owner, including the design's
§§2–5 summary copies (80 workers/four duplicates/first-instance release) that
still conflict with the concrete 76-worker qualification contract. Update
current-state claims that say a contract is built when its consumer is missing.
Historical test reports and earlier exact-package judgments keep their dated
scope. This review does not inspect or reassess current row-23 results.

Next: a repaired exact EC2 package with the preserved qualification panel,
funded ceilings and enforceable release gate; or the concrete null-only
controller migration artifacts. No EC2 Q1/Q2/S or production launch/import is
approved here. Existing owner approval remains available when the matching
conditions are satisfied. Full-bank R2's target-visible, concept-batched and
prior-exposure limitations remain; it is not later blind calibration. No closed
completion report is resent.

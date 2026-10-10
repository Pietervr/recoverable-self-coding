# R052 — row 23 EC2 benchmark revision 2 second opinion

10 October 2026 UTC. Codex, exact session `GPT: R052 Entropy paper`.
Package: RSC `8275005`. Brief: Unimog `787c1a49fea0a3f13cfebcd54b1fdc8b8c938965`, `prompts/2026-10-10_codex_r052_aws_ec2_bench_rev2.txt`, SHA256 `5b2d712d7edcba53e6eef3e74b4871fc19cba5507076526ea5a11adad2d10674`.
Ownership was committed at Unimog `8fe5af6f`; handoff `da276152-ce27-5ab9-b3c4-4e13c7feefd2` was accepted before review edits or delegation.

**NOT FAVOURABLE to launching revision 2 as committed.** The old impossible-admission and XLA-baseline findings are closed. Launch uncertainty can still be released as zero cost, concurrent invocations can launch two instances, and the fallback reaper can manufacture terminal proof or exit on a transient error. Those paths defeat the declared cumulative spending control. A small outcome-publication race should also be repaired before paying for the declared evidence.

The paid-run gate remains unsatisfied. The owner's 10 October “yes, do the aws benchmark” stands for a favourable concrete revision; no new permission or expiry is introduced. The USD 28 cumulative benchmark ceiling and USD 3,000 further-spend cap remain. This review authorizes no launch, pooling, production campaign, numerical release or pilot ADOPT, and imposes no stop on independently gated Lengau operations.

## System and repairs established

One Spot c7a.24xlarge runs isolated native A and constrained B arms. Each uses the historical three-dataset row-6 panel and the unchanged screen B200 worker at reps 3–38/index 0. The row now measures parity and paired timing only, feeding a separate prospective production qualification. **No pooling permission follows from any result.** The prior opposite-index production question is outside this re-review.

Both arm manifests exactly preserve the production manifest `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c` except the six declared paths: `storage.root`, `storage.campaign`, `pbs.cores`, `shard.expect_layer_s`, `shard.expect_note`, and the new `bench` block. There are 36 slots, mapped exactly to reps 3–38/index 0. Roots are isolated and the production scientific/config/source/environment contract is unchanged. Nominal worker deadline is boot +74,400 seconds against a 68,400-second first-dispatch expectation: up to 6,000 seconds of setup can precede admission. This closes the former static refusal; it does not measure runtime or promise completion.

B retains the baseline XLA flags and appends AVX2; NumPy-mask fallback is distinctly `B_nomask`. Both arms now require attestation and successful bound job-start, and B retains worker binding checks (`userdata:56–71,85–87`). Downloads, input checksums, extraction and wrapper checks fail explicitly. The comparator validates canonical records against frozen tasks, uses verifier `float.hex()` payloads, requires the canonical 36 pairs, validates paired timings and separates failed fits. These are substantial repairs to `2cc26ee`.

The revised constants give `(77,400 + 600)/3,600 × 1.2094 + 0.10 = USD 26.3036667`, below USD 28 under the stated ancillary allowance. Thus the former USD 28.20 compute-only arithmetic blocker is closed. The remaining objection is admission/recovery/accounting, not that multiplication.

## Required launch repairs

**1. Preserve an ambiguous launch until its actual disposition is established.** `bench_launch.py:135–139` handles an uncertain RunInstances result with one client-token Describe. An empty result becomes `state="no instance"`; `charged:50–52` assigns zero and the next call admits another attempt (`:84–86`) with a fresh token (`:109`). A created instance can consequently remain outside the ledger while another is launched. EC2 explicitly documents eventual consistency after creation; a single immediate Describe is not proof of absence. [EC2 eventual consistency](https://docs.aws.amazon.com/ec2/latest/devguide/eventual-consistency.html).

Keep the persisted intent/token and full request parameters unresolved and funded. Reconcile with bounded backoff and recovery of that **same** token/request; do not classify an ambiguous response as a definitive failed launch from an empty lookup. A definite rejected request can have a separate disposition. Ensure recovery also works after a crash before the launcher saves `state="launched"`: the current reaper selects only launched attempts (`reaper:23–25`), while a later launcher simply refuses an intent. AWS idempotency protects a retry with the same token and parameters; it does not deduplicate a new token. [EC2 idempotency](https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html).

**2. Serialize admission and accounting.** There is no exclusive lock across ledger load, checks, attempt allocation, durable intent and dispatch (`launch:83–97,109,129–142`). Atomic replacement of JSON (`:67–69`) is not an admission lock. Two invocations of the same `b2` run can both load an empty ledger, pass the checks, choose attempt 1 and generate different tokens. One can dispatch, then the other save its previously loaded intent and dispatch too. Both target `attempt_1/`; one ledger entry cannot account for both. This is a same-run concurrency failure, independent of any different-run proposal.

Use one exclusive admission/accounting lock shared by launcher and reaper, with unique durable attempts and stale-intent recovery. Preserve unresolved/live reservations until reconciliation. Make the S3 empty-prefix check fail closed on an API error (`launch:96` currently ignores its return status). Return explicit refusal or recovery rather than overwriting state or dispatching through uncertainty.

**3. Make fallback termination and terminal accounting durable.** `bench_reaper.py:30–34` treats an empty filtered Describe response as `"terminated"` and then writes reconciled terminal accounting (`:45–48`). It has not observed a terminal state. Describe and Terminate failures also escape uncaught through `launch.aws:31–35`, ending the watcher (`reaper:30,36`). An AWS CLI has a finite retry allowance; that is not a persistent supervisory loop. [AWS CLI retries](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html).

Require an attributable terminal response; an empty/error response remains unresolved with its reservation held. Persist supervisory errors, use bounded timeouts/backoff, retry termination idempotently as needed, and reconcile independently of a client crash. Arrange and verify the operating fallback for the attempt rather than only printing “NOW RUN” after paid dispatch (`launch:144`). Include polling/API latency and ancillary resource cleanup in the cost margin; no hard deadline is waived for recovery or upload. This asks for a working bounded supervision path, not an impossible guarantee through every external outage.

Observing `shutting-down` legitimately ends **compute** billing; it need not be rejected. EBS and other resources have separate billing/cleanup, so retain that distinction in terminal accounting. The supplied IAM policy includes the needed Describe and project-tagged Terminate actions; this is not a missing-permission finding. Actual grants and operation are untested. [EC2 state and billing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html).

**4. Publish the declared outcomes atomically and check finalization.** Userdata `:77` redirects directly to a final exit-code file. The existence count (`:94–96`) can see the last file after creation but before its contents are written; the parser immediately applies `int(read.strip())` (`:110`). That ordinary scheduling race can raise on an empty file. Parser failure is unchecked (`:103–112`), and the script continues to upload/shut down without `outcomes.json` (`:113–117`). Individual uploaded exit files might later permit reconstruction; this is not necessarily loss of all scientific evidence, and the comparator refuses a missing outcome certificate.

Publish exit files through temporary files and atomic rename, track/reap declared processes when collecting terminal or censored outcomes, and check certificate creation. Keep hard shutdown in force. `final_upload:32–39` currently records sync status/counts without enforcing their agreement or branch disposition; call it bounded transfer evidence rather than verified durable upload. Record a checked transfer success/failure disposition within the existing deadline, preserving sufficient integrity evidence for later validation.

## Report acceptance repairs, separate from permission to collect

The comparator issues below can be repaired against retained evidence without buying fresh fits. Because the benchmark now grants no pooling authority, they are conditions on accepting a complete qualification report, rather than additional scientific reasons to forbid isolated collection once the launch repairs above are closed.

- Apply the procedure's usable-statistic predicate: `failed=False` alone is insufficient (`compare:122–128`). `analyze._record_ok` accepts numeric nonfinite statistics; the actual procedure also requires finite expected predictor/band values (`analyze:769–771`). Report unavailable statistics explicitly instead of omitting them from the maximum deviation (`compare:135`).
- Reject noncanonical directories/files, including `rep03` alongside `rep3` (`compare:91–105`); integer normalization currently hides that alias. Binding/alias problems already set overall invalid, so the later `valid_pairs` count should also be labelled or calculated consistently.
- Validate typed, named attestation profiles and required effective fields, the exact 78 process names and a nonempty valid occupancy timeline. `{}` attestation, 78 arbitrary zero-valued outcome keys and empty occupancy currently pass their respective shallow checks (`:162–186`). Unknown/absent OpenBLAS core evidence must be reported as unavailable, not certify the constrained profile (`attest:17–30,56`).
- Pin the reviewed arm manifests and compare complete expected task bindings. A downloaded manifest's self-hash plus three binding fields is insufficient attribution to the reviewed package (`compare:88–113`). Check the row-6 generator/grid content fields in addition to rep/code hash (`:67–77`).

## Exact bytes and evidence limits

Every listed local file equals its committed `8275005` bytes. Python AST, JSON, `bash -n`, exact plan and manifest sidecar SHA checks pass. These checks perform no source imports or runtime execution.

| Path relative to `aws_ec2/` | SHA256 |
| --- | --- |
| `README.md` | `9f9e63f54b1dff273ea8b2e65e1a2963f9fbd09713eb6ebf25989ada4cec62de` |
| `attest.py` | `2e25ae4d05f56e3cf3f8ff375e5b2397b994bab6c3e2d4ac684087de75aa4df2` |
| `bench_compare.py` | `fb8724d12cbdd6e4bdbb90aecabea97a47c681e85279fdd8d24821be9bc85299` |
| `bench_launch.py` | `4a175368c8a2dd831353050e40a268e814e1304fe54988991527ea0f9cdb1fe5` |
| `bench_reaper.py` | `50408a0b4e94e96f3b4c2387bfcd9d7487f3e0e02745e73a25cf8ade73b3c0b7` |
| `bench_userdata.sh` | `e7fb5df9aef06308d844fc74f48f36517fdd077f33d9eac1b0ad4c9215df80bc` |
| `make_bench_manifests.py` | `34aa4e51de508c9d57ebdcdaf5cb126023971c48b5c156aaf7fb4a4dd72bfba0` |
| `bench/manifest_A.json` | `824837ee54af3f5fe43d67427cfdd335afc99e2f6d846333eb030b0e559053fa` |
| `bench/manifest_B.json` | `08e498c447341dee9f462f10a5570eda4ef58e3c5ad9e418dfc7bc8a4b061955` |
| `bench/plan.json` | `a67e2e1ce9c9c98455ee7946ec8f141ab50a5a8a473178b89aeaa12957d456d5` |
| `bench/SHA256SUMS` | `6fa0105dcae3b7ccf28a5659c3b0df8c52eab853b833e58d5acb67e413314598` |
| `iam/role_policy_xtenure-ec2-t1-worker.json` | `b9f176b20a574fdc819d1d427c165b307b12492bdbb631d5fce5bba2d1ca6dd7` |
| `iam/user_policy_xtenure-t1-ec2.json` | `9195c42213211acf2ab7a921f4d1089ade1d2a985447e043139aff0f7f95e19c` |

The brief's Haswell A attestation, redirected 36-slot job-start and comparator self-test are **source-reported component evidence**. Its positive arm-A test reused Lengau records with altered timing producer labels; it establishes neither fresh EC2 provenance nor EC2 parity. Full instance execution, authenticated launcher/reaper operation and Zen-4 B attestation remain unexercised, as the brief discloses. Codex did not open saved CSV outcomes, scientific records/timings or private outputs, and computed no endpoint or coverage result. Preserve the earlier source exposure of row-6 sens600 rep 0 values/decision; deviations-only printing does not restore blindness.

Three read-only reviewers examined cost/recovery, operational contracts and comparator interpretation. Their scientific/operational closure findings are reflected above; the overall launch verdict is held by the concrete cost/recovery paths. Claude owns repairs, ledger/current docs/frontmatter/generated INDEX/tracker/IAM/accounts/dispatch. Codex owns this record and its R052/lifecycle appends only. No source/controller/science imports or execution, tests, fits/simulations, AWS/account/SSH/Lengau operations, worktrees or push occurred. Existing jobs/watchers, scientific seals, caps, earlier closed reviews/reports/exposure and foreign files are preserved.

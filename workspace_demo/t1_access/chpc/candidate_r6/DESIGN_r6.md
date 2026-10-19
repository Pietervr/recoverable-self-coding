# EC2 epoch 2 - R6': the five-instance fleet, interleaved through the real administrative code (CANDIDATE test)

Written 19 October 2026 (R052, Claude, bounded job) for Codex's review. It builds the test Codex requires "Before five-way
production" (`reviews/2026-10-19_e2_adoption_codex_review.md`): "build/review/pass R6's interleaved five admissions/five
reconciliations through real administrative locks/ledgers/generations/reservations and sixth-admission refusal". The rule
was declared on 17 Oct (`chpc/candidate_e2/QUALIFICATION_E2.md` s.3 item 6): stubbed-AWS tests that INTERLEAVE five
admissions and five reconciliations on one `prod-e2` run ledger under the global and run locks, proving unique sequences,
retained sibling changes, immutable monotone inventory generations, cumulative reservations and the refusal of a sixth
admission (also ruling 13 of `reviews/2026-10-17_e2_p80r_codex_review.md`).

Nothing here touched the world: no AWS call (a fake `aws` answers; credential files, profile and proxies point at nothing and
a guard checks the resolved binary before anything runs), no ssh, no Lengau. No live, adopted or Codex-reviewed file was
edited. It is a test of the reviewed code, not new administrative code. It does not establish spot capacity: quota and
capacity evidence remain the owner's and stay contingent.

## 1. Files

| File (this folder) | SHA-256 | What |
|---|---|---|
| `test_r6_fleet.py` | `37044455e9cf629f63c2db8c7f2a4ac5a66aa7483b8ae397ebe0c865828d23ad` | the R6' test (s.3) |
| `fake_aws.py` | `a52bd00250fd40687dd2d8f68b2c2b55dfb03fb9f4979aa8acc21018ce231414` | the fake `aws` CLI: STOP head-object, SSM AMI, S3 uploads (with a hold), run-instances (idempotent on the client token; ok / ambiguous / reject / hang), describe-instances, describe-volumes, terminate; one flock-serialised state file; unmodelled calls exit 97 |
| `r6_admit.py` | `c7b432a85958b45b368091825c1f509b2925851093a3e929b4db1ac09f3914ce` | runs the fake tree's real `prod_launch.main()`; its one substitution is the toolchain tarball pin, as `aws_ec2/tests/test_prod_launch.py` does |
| `test_results.txt` | `a1f3a8b755c56d08826a776aeccd327ca8c86e943fd44a6a537f078247fbc44e` | the run record |

## 2. What is real and what is fake

**Real (exact bytes, executed unmodified).** A temporary PROMOTED tree is built per run: every row of
`chpc/candidate_v17/v17_promotion_map.json` used by admission and reconciliation is copied from its source and checked against
its map sha256 (`aws_ec2/prod_authority.py` `e4897991`, `prod_launch.py` `6bca4709`, the epoch-2 helpers, partition
`48cea639`, snapshot `31cc268f`, funding `d6f414e8`, panel `f04a5e43`, manifests, controls `9ea4e727`); unchanged files
(`bench_launch.py`, `bench_reaper.py`, `programme_gate.py`, `row19_ec2_root.py`, the verifier, the designated declaration,
the production manifest) are copied as they are, the v17 pins checked. The pinned qual-Q2 ledger is copied (the A4
funding basis). Executed for real:
- the global authority lock and the per-run lock, as `flock()`s between separate processes (each admission is its own
  process; each reaper is a detached process started by the launcher under `caffeinate`, or by hand);
- the ledgers, `bump` (generation + global sequence), `write_inventory` (write-once archives via `os.link`), `budget_problem`,
  `fleet_problem`, `epoch_problem` (funding validated against the pinned Q2 basis, the epoch-2 allowance), the controls
  adoption gate (`programme_gate.controls_authority_problem` with `git ls-files` / `git diff` in a private repository), the
  activation check, the receipt and inventory-binding gates, STOP checks, the production plan builder and allocator,
  `bench_launch.resolve`/`issue`/`after_launch`/`start_reaper`, `bench_reaper.main` including its reconciliation under both
  locks and its new generation;
- the epoch-2 release gate: `prod_authority.release_adopt` releases epoch-2 production in that tree from a synthetic
  schema-3 certificate and review, and every later `release_state` read re-runs `release_problem_e2` on it;
- the Lengau installer `row19_ec2_state.install_inventory` (monotone generations) on a local root.

**Fake (declared).** EC2/S3/SSM (`fake_aws.py`); the toolchain tarball and its pin (`r6_admit.py`); the controls ADOPTION
record (a fixture bound to the committed re-review, which carries the ADOPT `9ea4e727` line - it adopts nothing outside the
temporary tree); the schema-3 certificate and its review; the row-23 report and `qualification_e2` permission records; the
budget baseline (spent USD 500, idle 0, then set to the cap boundary); the Lengau receipts (synthetic whole-role watch
documents binding the installed state and a verifier document built from the final snapshot's Lengau-done list) and the
activation proof (built with the real field rules). Synthetic fixtures are labelled in their bytes.

## 3. The scenario and what each step proves

| Step | Proves |
|---|---|
| A1 | a real production admission: sequence 61 (after qual-Q2 7, qual-E2Q1 60), 72 work + 4 sentinels, worst case USD 27.9185 reserved, three generation bumps (sequence reservation, intent seal, outcome seal), a live reaper |
| stale receipts x3 | an admission on a receipt taken before the last seal, on a receipt older than 2,700 s, and after a reconciliation sealed behind the receipt, is refused with nothing journaled, no RunInstances and no generation |
| A2, A3 | fresh receipts admit |
| interleave | A4 is held inside its locks (paused in an S3 upload); a concurrent admission is refused at once; reaper 1 observes its instance's end and CANNOT record it while A4 holds the global lock; released, A4 completes and reaper 1 then records - the ledger and the newest generation carry both changes (retained siblings) |
| A5-A7 | five live (3, 4, 5, 6, 7) |
| sixth | refused by the fleet ceiling: nothing journaled, no RunInstances, no generation |
| reservations | five live attempts are each held at worst case in the production total and in the sealed inventory; with four live, the USD 3,000 cap refuses one more worst case at +USD 0.50 and admits it at -USD 0.50 (A8) |
| interruption | A9 is killed inside RunInstances (the instance was created, the answer lost): attempt 9 stays `intent`, funded; a fresh admission refuses (unresolved); recovery on a stale receipt re-issues nothing; recovery on a current receipt re-issues the SAME token and adopts the one instance (no second instance); a second recovery finds nothing |
| reaper interruption | reaper 5 killed: attempt 5 stays `launched` and reserved; a hand-started reaper reconciles it and seals; a second reaper refuses ("not launched") and changes nothing |
| drain | A10 restores five live; FIVE reapers then reconcile concurrently on the one ledger, five new generations |
| invariants | sequences globally unique and increasing; 10 admitted / 10 reconciled, each with its own instance; no coordinate allocated twice (ten batches and the E2Q1 panel disjoint, all epoch-2 owned); every archive unchanged since first seen, strictly increasing, latest = newest; Lengau installs strictly increasing and the real installer refuses an older generation; the final production total is observed charges only; 11 RunInstances (10 admissions + 1 recovery re-issue), none under a refusal; no process of the fake tree remains |

Counts are in `test_results.txt` (61 passed, 0 failed, on two consecutive runs; 9 fresh admissions + 1 recovered, 8 refused admissions/recoveries, 10 reconciliations, 31 sealed generations, 11 RunInstances).

## 4. Limits

- One Mac, one filesystem: the locks are `flock()` on APFS between processes, as in production on the Mac; no
  multi-host claim is made. Contention is forced (the S3-upload hold, a held lock) rather than left to chance.
- The fake EC2 is not AWS: real `run-instances` idempotency, eventual consistency and capacity are not tested. Capacity
  for five c7a.24xlarge spot instances remains contingent on the owner's quota read; the quota arithmetic 512 >= 480 vCPU is
  not capacity evidence.
- Reconciliation timing follows the real reaper's 60 s poll; the run takes about five and a half minutes (321.6 s recorded).
- The Lengau side is the real installer on a local root and a synthetic receipt; the actual `row19_screen_status.py` watch,
  `ec2_sync.py` transport and ingestion/ACK are not exercised (ingestion and ACK are covered by `test_e2q_ingest.py`).
- The release gate is real, but on a synthetic certificate: this proves the gate admits production only through a release
  of epoch 2, not anything about an actual qualification result.

## 5. Choices for Codex

1. **Promoted fake tree from exact bytes** instead of in-process monkeypatching of data paths (the existing tests' pattern):
   module path resolution, the git-based adoption gate and the detached reaper all behave as after migration. Is the
   fixture adoption (bound to the committed re-review's ADOPT line, in a private repository) acceptable for a test?
2. **The tarball pin** is the one substitution in the admission process (as `test_prod_launch.py`); the reaper runs with no
   substitution.
3. **What counts as "five reconciliations".** The run has ten admissions and ten reconciliations: one forced to wait on an
   admission's lock, two serial, one by a hand-restarted reaper, and five concurrent at the drain. Is that the interleaving
   the declared rule intended, or should a randomised schedule be added?
4. **The sixth admission** is shown refused at exactly five live instances, and later admissions after reconciliations show
   the refusal was the ceiling, not another gate.
5. **Not tested here:** an admission that ends `ambiguous` after its bounded retries (the backoff totals 465 s; the
   interrupted-in-RunInstances case covers the same recovery path faster), and a crash of the reaper between its ledger
   save and its inventory seal (no injection point without editing reviewed code; the next seal by any actor carries the
   reconciled state). Codex may require either.

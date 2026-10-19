# EC2 epoch 2 - E2Q bundle collection, verification and staging (CANDIDATE, not adopted, never run against the world)

Written 19 October 2026 (R052, Claude, bounded job). It builds the missing piece Codex named twice:
- `reviews/2026-10-19_e2_adoption_codex_review.md`, "Before one paid E2Q1": "a **concrete reviewed bundle
  collection/verification/staging procedure**";
- `reviews/2026-10-19_e2_repair_codex_rereview.md`, "Staging, wording and remaining sequence": the `--snapshot` argument
  "settles the path argument; it does not supply the still-missing collection/verification/staging procedure".

It is for Codex's review. Nothing here was run against the world: no AWS call, no ssh/scp, no Lengau, no scheduler. No live,
adopted or Codex-reviewed file was edited (`chpc/candidate_e2/`, `chpc/candidate_e2q/`, `chpc/candidate_v17/`,
`chpc/e2_final/` are unchanged). Every test is synthetic; no protected payload was opened.

## 1. Files

| File (this folder) | SHA-256 | What | Promoted to |
|---|---|---|---|
| `e2q_stage.py` | `d531b455b00eea0de515daf2fc8c17a6a8e7df63ed6d614843e18137265a65a4` | the Mac tool: `stage`, `qualify`, `run` | `aws_ec2/e2q_stage.py` (Mac only, like `prod_launch.py`; never in the Lengau payload) |
| `e2q_stage_verify.py` | `f742f0176d923171b36edfc9d3a6637477dae9dd9b9d2aee7c6ccd7198d9d1ac` | the pure, stdlib-only member verifier, run unchanged on the Mac and on Lengau | `aws_ec2/e2q_stage_verify.py` (shipped beside each staged bundle per invocation, sha-checked; choice 2) |
| `test_e2q_stage.py` | `d0ccc07864c0b4f212c258a8c523ce2d37e9c1239efadc7fa8633f6615affa6e` | 97 synthetic checks (s.5) | - |
| `test_results.txt` | `d75121c04880c31287e999dec5c92440e0d9a80df567e48503d592ff8eccddf7` | the run record | - |

No controls change is needed: neither file is a qualification-code-set member (`row19_ec2_e2qual.CODE`), and the verifier
reaches Lengau only as a per-invocation copy whose sha256 the Mac checks before and after it runs (bench_finish ships its
comparator the same way). The reviewed v17 controls `9ea4e727` therefore stay as reviewed.

## 2. The real epoch-1 path, reconstructed from the code and the run metadata

- **No epoch-1 qualification bundle was ever staged.** `aws_ec2/runs/qual-Q1/` and `runs/qual-Q2/` hold only ledgers, plans,
  requests, user-data and reaper logs - no fetched bundle. qual-Q1 attempt 4 was dispositioned (fenced on `ack_g48`,
  `chpc/e2_final/README.md`); qual-Q2 attempt 1 is `ingestion: pending` waiting for "the release that names it" (R052 log,
  16 Oct). The e1 qualifier was never run: `ec2_release_state.json` production is `released: false`, no certificate exists.
  DESIGN_e2q.md s.4's "I can't determine the epoch-1 staging command" is therefore literally true: there was none.
- **The one real S3 -> Mac -> Lengau precedent is row 23's `aws_ec2/bench_finish.py`** (attempt 5, five fetched copies in
  `runs/b2/fetched/attempt_5.<stamp>/`): `aws --profile xtenure-read --region us-west-2 s3 sync` into a NEW local directory;
  one `tar` stream over ssh (host `lengau`) into a NEW `/home/pvanrooyen/lustre/aws_bench/<run>a<n>/<stamp>`; the bundle
  digest (sorted `[path, sha256]`) recomputed on Lengau; six controller-tree pins checked before and unchanged after the
  remote tool; the exit status propagated; a binding file. This tool keeps all of that.
- **Bulk transfer goes through `chpc-scp`** (`~/.ssh/config`: scp.chpc.ac.za, login1, the transfer node), commands through
  `lengau` (login2): `chpc/row19_screen_status.py` sets `HOST, LOGIN = "chpc-scp", "lengau"` and streams trees through HOST,
  runs `t1py` verification and `qstat` through LOGIN. `ec2_sync.py` and `bench_finish.py` use `lengau` for both.
- **The producer's bundle** is `aws_ec2/prod_userdata.sh`: `OUT=s3://xtenure-cself-pvr-usw2/results/t1_access/aws_bench/<run>/attempt_<n>`
  (= the ledger's `results`), synced from `W=/mnt/bench` = `env/`, `logs/`, `exits/`, `root/`, plus `BUNDLE_SHA256SUMS`
  (`find root env ... | LC_ALL=C sort | xargs sha256sum`, the mutable diagnostics excluded) and `env/upload_verify.json`
  written after it. The ingestion (`row19_ec2_ingest.check_bundle`, REVISION 8) checks only `root/` and `env/` with its
  `MUTABLE` exclusions; `logs/` and `exits/` are unsealed.

## 3. The procedure

The tool's module text is the normative statement; in short (all paths are constants of `e2q_stage.py`):

1. **identity** - the ledger attempt `runs/<run>/attempts.json` #n (E2Q1/E2Q2 of its own run, reconciled, pending, no
   disposition request, `ec2-<run>-a<n>`, results prefix exact, plan file and `plan_sha256`, work/duplicates = the declared
   panel, 4 sentinels outside them) and the CURRENT sealed inventory carrying it identically; the Mac's pinned inputs
   (partition `48cea639`, deployed snapshot `31cc268f`, panel `f04a5e43`, manifests `3ea8cafd`/`4af4a64d`/`e1260505`,
   funding `d6f414e8`, controls `9ea4e727`, manifest `43b75f94`) are their bytes. The Lengau tree pins are the code set at
   the v17 latest-version pins (helpers) and the manifest's code pins (`analyze.py`, `models.py`, `chpc/row19_shard.py`).
2. **collect** - `s3api list-objects-v2` of the exact prefix, then `s3 sync` into a NEW `runs/<run>/e2q_stage/<stamp>/bundle`;
   the local set and sizes must equal the listing.
3. **verify** - `e2q_stage_verify.verify`: sealed list well-formed (format, normalised `root/`|`env/` paths, unique, C order)
   and every sealed member present with its sha256; required sealed members; `upload_verify.json` transfer verified; no
   FAILED markers; the only unsealed members allowed are `BUNDLE_SHA256SUMS`, the ingestion's `MUTABLE` names and
   `logs/w_slot<k>.log` / `exits/w_slot<k>.code` of planned slots; no symlink or special file; the plan is the attempt's
   bytes and names the attempt, epoch 2, the partition, the contract's operational manifest, 79,200 s, 76 slots with the
   panel's work, its duplicates and the attempt's sentinels in order; outcomes name exactly the 76 workers; every status is a
   planned slot's of this attempt id. `receipt.json` (beside the bundle) binds all of it.
4. **stage** - through `chpc-scp`: one tar stream into a NEW `/mnt/lustre/users/pvanrooyen/t1_toolchain/ec2_stage/<run>/attempt_<n>/<stamp>/`
   (fixed root, outside `rsc_screen_ctl`, `rsc_screen`, `row19_screen` and its campaign; the tool refuses an overlapping
   layout), then the verifier and `expect.json` beside the bundle.
5. **reverify** - on `lengau`: the shipped verifier's and expectation's sha256 = the Mac's; `t1py e2q_stage_verify.py
   --stage-root ...` reports the Mac's tree digest, count and members; the controller tree's qualification inputs are their
   pins; `remote.json` records it. A tamper, loss or addition in transit, or a symlink below the staging root, refuses.
6. **qualify** - re-verify both copies and the pins; the root's INSTALLED inventory (fetched through `chpc-scp`) must be the
   Mac's current generation and seal, carry the attempt reconciled and pending, and be fresh with 3,600 s to spare (the
   qualifier itself refuses an inventory older than 6 h, which would otherwise become a NO_RELEASE certificate for an
   administrative reason). Then ONE remote shell on `lengau`: refuse a pre-existing `--out`/`--sandbox`, create
   `<attempt dir>/EVALUATION_CLAIM` with noclobber (refuse if it exists), run exactly

       t1py chpc/row19_ec2_qualify.py e2 --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json \
           --authority <T>/row19_screen/ec2/authority/inventory.json --key qual-E2Q1/1 --bundle <stage>/bundle \
           --opmanifest aws_ec2/prod/manifest_e2q1_e2.json --prod-opmanifest aws_ec2/prod/manifest_production_e2.json \
           --panel aws_ec2/prod/panel_e2q_e2.json --snapshot chpc/claims_snapshot_e2.json --funding aws_ec2/e2_funding.json \
           --sandbox <stage>/sandbox --out <stage>/cert_qual-E2Q1_1.json

   and record its exit status. Afterwards: the bundle re-verifies to the same tree digest (never mutated), the pins are
   unchanged, the certificate is fresh and binds this `BUNDLE_SHA256SUMS`, plan, attempt, panel, snapshot, partition,
   funding and both operational manifests, and its outcome agrees with the exit status (0 RELEASE, 3 NO_RELEASE or
   INCONCLUSIVE). The certificate and `binding.json` land in the Mac stage directory.

Exit codes: 0 staged / RELEASE; 3 a completed non-RELEASE evaluation; 4 REFUSED; 2 a transport or qualifier failure.

**Where it sits in DESIGN_e2q.md s.7** (the owning session's runbook, which this candidate does not edit): it replaces the
first sentence of step 6 ("Stage the reconciled bundle on Lengau (s.4: the staging command is not documented), then install
the current inventory") with: `python3 aws_ec2/ec2_sync.py cycle` (install the current generation), then
`python3 aws_ec2/e2q_stage.py run --run qual-E2Q1 --attempt 1`. Step 7 then commits the certificate (choice 9) for the
actual-result review; release-adopt stays after a FAVOURABLE review.

## 4. Refusals, by case

| Case | Where | Test |
|---|---|---|
| attempt not reconciled / ingested / disposition requested / other prefix / other plan hash / work not the panel's | identity | s.2 identity x6 |
| sealed inventory carries the attempt differently, or is not the current generation | identity | 2 |
| a Mac pinned input not its reviewed bytes; an epoch-1 run | identity | 2 |
| sealed member changed at S3; plan replaced by another attempt's; E2Q2 bundle under an E2Q1 attempt | verify (collect) | 3 |
| sealed member missing; no or truncated sealed list; transfer not verified or record absent; BUNDLE_FAILED | verify | 6 |
| sync drops an object; an object short after sync; sync adds an object | collect | 3 |
| unlisted file under root/; top-level stray; log of an unplanned slot; status of another attempt id; a mutable diagnostic sealed | verify | 5 |
| byte flipped / member lost / file added in transit; shipped verifier or expectation altered; symlink below the staging root | reverify | 6 |
| Lengau qualifier not its pin; deployed snapshot missing on Lengau | reverify (pins) | 2 |
| existing remote or local staging directory; a concurrent invocation | stage | 3 |
| claimed attempt staged again or qualified again; claim written between staging and qualification | stage / qualify | 4 |
| installed inventory of an older generation, or within the freshness margin | qualify preflight (no claim) | 2 |
| Lengau or Mac copy tampered after staging | qualify (no claim) | 2 |
| qualifier writes into the bundle; controller tree changes during the run | after the run (claim kept, no binding) | 2 |
| qualifier exits 1 without a certificate (exit 2, claim kept, retry refused) | after the run | 2 |
| stale certificate at `--out` (refused before the claim); certificate binding another bundle; outcome disagreeing with the exit | qualify | 3 |

## 5. Verification

`python3 chpc/candidate_e2s/test_e2q_stage.py` (from `workspace_demo/t1_access`): **97 passed, 0 failed** (`test_results.txt`).
- **Real constants (15):** every `DATA_PINS` entry = the sha256 of its `chpc/e2_final` file and its v17 promotion-map row;
  `ADOPTED_CONTROLS_SHA` = `9ea4e727` (the re-review's ADOPT literal and the map's controls row); `PROD_SHA` = `43b75f94`;
  `CODE` = `row19_ec2_e2qual.CODE`; every code-set file has a v17 or manifest pin; the v17 qualifier pin is `1d8eee78`; the
  verifier's `MUTABLE` = the ingestion's (REVISION 8); the command passes exactly the flags the reviewed qualifier's `e2`
  parser defines and equals DESIGN_e2q.md s.7 step 6 on every fixed argument; the staging root is fixed and contained; the
  hosts; the real transport's argv (aws read profile and region, ssh/scp options) with `subprocess` replaced by a recorder.
- **Synthetic end to end (82):** a synthetic Mac tree, a local S3 prefix and a local Lengau tree; every remote shell string
  the tool builds runs unchanged through `bash`; PATH guards make any real aws/ssh/scp call fail and log (none occurred).
  The clean path stages and qualifies (stand-in qualifier) with the exact command; S3, Mac and Lengau copies are byte-, mode-
  and mtime-identical afterwards; then every case of s.4, the verifier unit cases S3 cannot carry (symlink, FIFO, order,
  duplicate, escaping path, read-only guarantee, containment), E2Q2, NO_RELEASE and its no-retry rule.

**Not established by these tests:** real S3 listing and sync behaviour (pagination, eventual consistency), real ssh/scp, tar
and `sha256sum` on Lengau, Lustre performance, the real qualifier on a real bundle (a stand-in with the same command line
writes the certificate), the real installer's file on the root. The sizes of a real 76-worker bundle are not known here.

## 6. Choices for Codex

1. **Transfer host.** Bytes go through `chpc-scp` (the brief; `row19_screen_status.py` precedent); every command, including
   the remote verification and the qualifier, runs on `lengau` (login2), where the controller commands run. bench_finish used
   `lengau` for both. Both nodes see the same Lustre path.
2. **The verifier is shipped per invocation**, sha-checked before and after, instead of being deployed and pinned by the
   controls. Pinning it would change the reviewed v17 controls `9ea4e727` and need a new review; it is not part of the
   qualification code set. Alternative: deploy it in `migration_v17` as a pinned file.
3. **Unsealed producer files are staged.** `logs/w_slot<k>.log` and `exits/w_slot<k>.code` of planned slots and the
   `MUTABLE` diagnostics travel with the bundle (the qualifier ignores them); they are bound end to end by the staging
   receipt's member digests, not by the producer's seal. Alternative: stage only the sealed members plus
   `env/upload_verify.json`.
4. **Strict EXTRA rule.** Any member outside the contract refuses - including a producer temp name such as
   `exits/.w_slot7.tmp` left by a worker killed between `echo` and `mv` (the upload excludes only `*.tmp.*`). Fail closed;
   the alternative is to ignore those names explicitly.
5. **A consistent re-seal at S3 is not detectable by staging.** Whoever can write the prefix can replace a record and
   `BUNDLE_SHA256SUMS` together; staging then proves only that the qualifier reads what S3 held at collection, and the
   receipt and certificate bind that `BUNDLE_SHA256SUMS`. Scientific validity stays the qualifier's. Accept as a stated limit?
6. **One evaluation claim per attempt.** The claim is taken in the same remote shell immediately before the qualifier, so a
   qualifier crash (exit not 0/3, no certificate) or a lost connection mid-run still consumes it, and the tool offers no
   re-run. This follows "no retry by outcome" conservatively; a re-run after a provable non-evaluation would need a reviewed
   decision (and, if wanted, a recorded supersession route). Alternative: allow one re-run when the failed run left no
   certificate.
7. **Administrative preconditions before the claim.** The tool pre-checks pins, both copies and the installed inventory
   (generation, seal, attempt state, a 3,600 s freshness margin). It does not pre-check the activation proof or the
   Lengau-side controls adoption beyond file pins; if those failed, the qualifier would write NO_RELEASE and the claim would
   be spent. Should a NO_RELEASE caused only by an administrative precondition count as the attempt's evaluation?
8. **Stage and qualify may be separate invocations.** `qualify` re-verifies the Mac copy against its receipt, the Lengau copy
   against the Mac, the pins and the claim; the inventory may advance in between (other runs reconcile), and the preflight
   compares the installed inventory with the Mac's CURRENT generation rather than the staging-time one.
9. **Certificate location.** The certificate and `binding.json` stay in `aws_ec2/runs/<run>/e2q_stage/<stamp>/`, which git
   does not track today; `release_state` checks backing by sha256, not by tracking. DESIGN_e2q.md s.7 step 7 says to bring
   the certificate to `aws_ec2/` and commit it: copy it (with receipt and binding) to a tracked `aws_ec2/certs/` path, or
   track the stage directory's small files?
10. **Immutability by verification, not by permissions.** The bundle is never written by the tool and is re-verified after
    the qualifier. It is not made read-only, because the qualifier's R5' sandbox `copytree`s the bundle (permissions copied)
    and then rewrites `env/plan.json` in the copy.
11. **Inventory identity.** The installed inventory is compared by its sealed `sha256` field and generation, not by file
    bytes (the installer writes it; in practice the bytes are equal, which prod_launch's receipt binding relies on).
12. **Nothing is deleted.** Local and remote staging directories are evidence and are never removed by the tool; a cleanup
    policy for `ec2_stage/` (after release-adopt and canonical ingestion) is not proposed here.

## 7. Still required before one paid E2Q1 (unchanged)

Codex's review of this procedure; the separately reviewed `migration_v17` and the deployed, activated exact package; the
prospective E2Q1 permission record; current budget/fleet/inventory/receipt gates. The doc statements this candidate makes
stale but does not edit (reviewed bytes) are DESIGN_e2q.md s.4 "Staging the E2Q1 bundle on Lengau ... is still not built"
and s.7 step 6 "(s.4: the staging command is not documented)".

# Row 19 screen controls v17 - CANDIDATE, not adopted (the EC2 provider epoch-2 adoption)

Written 19 October 2026 (R052, Claude, bounded job). Controls v17 is the adoption vehicle for EC2 provider epoch 2: it is
DESIGN_e2.md s.5 first bullet ("Controls v17") and s.6 steps 5-7, extended by DESIGN_e2q.md s.4-s.5 choice 1 (v17 must also
pin the candidate_e2q state copy and `row19_ec2_e2qual.py`). It is for Codex's review, together with the final epoch-2
bytes of `chpc/e2_final/` (README there) and the qualification package (RSC `92a62f6`).

Nothing here is promoted, deployed, activated or run against the world. No AWS command, ssh, scp or Lengau operation was run.
No adopted or live file was edited: `chpc/row19_screen_controls.json` (v16 `01976b6a`), the adoption record (`523fe18a`),
`chpc/row19_screen_manifest.json`, the adopted `chpc/*.py` and `aws_ec2/*.py`, and `aws_ec2/runs/**` were read only. The
Codex-reviewed bytes in `chpc/candidate_e2/`, `chpc/candidate_e2q/` and `chpc/e2_final/` are unchanged: v17 pins them where
they are; nothing was copied, merged or edited. The only new controller bytes are the admission copy in this folder.

## 1. Files

### This folder

| File | SHA-256 | Role |
|---|---|---|
| `row19_screen_controls.json` | `92f28b8fbd53a2a13635022ff01d2a76ef75a1986e670311ccfb768f7cdc80aa` | versions 1-16 byte-identical to the adopted file (one textual insertion); adds version 17 |
| `row19_screen_admit.py` | `c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed` | the adopted v16 admission (`1b02f336`) with `candidate_e2/admit_v17_partition_line.diff` (`0fc23704`) applied, nothing else |
| `v17_promotion_map.json` | `fbb3e0dcf88b522baf2ec04bb625f6337a97998f60b8b5e13d5519098a764873` | every candidate path -> promoted path, with its sha256, its v16 (previous) sha256 and its group |
| `build_v17.py` | `812a2c38eb500780639216f8eb74f16db59743b72b5c0d5c55222a494bd6af4d` | builds the controls and the map deterministically from the adopted bytes; `--check` compares |
| `promote_v17.py` | `3b179cc3d809ccb1621b4c2e1fe6302b956099c38ee4156b5e4993c72ed49385` | the promote/check script (promote_v16.py pattern): `--check`, `--check-promoted`, `--dry-run`, real promote. The real promote was NOT run |
| `test_v17.py` | - | 45 checks (s.4) |
| `regress/run_one.py`, `regress/run_v17_regress.py` | - | regression with the v17 module set substituted (s.4) |
| `test_results.txt` | - | counts before and after, every difference explained |

### The promotion map (`v17_promotion_map.json`)

At promotion each source is copied to its promoted path. The sources stay where Codex reviewed them.

| Promoted path | Source | SHA-256 (v17) | v16 / live bytes | Group |
|---|---|---|---|---|
| `chpc/row19_screen_admit.py` | `chpc/candidate_v17/row19_screen_admit.py` | `c3960464…1d6b9ed` | `1b02f336` | pin |
| `chpc/row19_partition.py` | `chpc/candidate_e2/row19_partition.py` | `eabf50c3…ac0d8` | `ed6aa177` | pin |
| `chpc/row19_ec2_ingest.py` | `chpc/candidate_e2/row19_ec2_ingest.py` | `6ac144c6…e108` | `b697dc36` | pin |
| `chpc/row19_ec2_qualify.py` | `chpc/candidate_e2q/row19_ec2_qualify.py` | `73f912b8…29c8` | `1fc6b61f` | pin |
| `chpc/row19_ec2_state.py` | `chpc/candidate_e2q/row19_ec2_state.py` | `7bdedafc…038e` | `bda200dc` | pin |
| `chpc/row19_ec2_e2rules.py` | `chpc/candidate_e2/row19_ec2_e2rules.py` | `a9ea1f61…3bcc` | new | pin |
| `chpc/row19_ec2_e2qual.py` | `chpc/candidate_e2q/row19_ec2_e2qual.py` | `b3f29816…6e8ac8` | new | pin |
| `chpc/row19_partition_e2.json` | `chpc/e2_final/row19_partition_e2.json` | `48cea639…6fa6` | new | partition reference |
| `chpc/claims_snapshot_e2.json` | `chpc/e2_final/claims_snapshot_e2.json` | `31cc268f…7eecb6f` | new | data |
| `aws_ec2/e2_funding.json` | `chpc/e2_final/e2_funding.json` | `d6f414e8…4815` | new | data |
| `aws_ec2/prod/manifest_production_e2.json` | `chpc/e2_final/manifest_production_e2.json` | `e1260505…82f9` | new | data |
| `aws_ec2/prod/manifest_e2q1_e2.json` | `chpc/e2_final/manifest_e2q1_e2.json` | `3ea8cafd…cfb8b` | new | data |
| `aws_ec2/prod/manifest_e2q2_e2.json` | `chpc/e2_final/manifest_e2q2_e2.json` | `4af4a64d…0cec` | new | data |
| `aws_ec2/prod/panel_e2q_e2.json` | `chpc/e2_final/panel_e2q_e2.json` | `f04a5e43…c7a2` | new | data |
| `aws_ec2/prod_authority.py` | `chpc/candidate_e2q/aws_ec2/prod_authority.py` | `eee1bcd4…e65` | `b8ca02b8` | mac |
| `aws_ec2/prod_launch.py` | `chpc/candidate_e2q/aws_ec2/prod_launch.py` | `6bca4709…c784` | `21b7cf57` | mac |
| `aws_ec2/make_prod_manifest.py` | `chpc/candidate_e2q/aws_ec2/make_prod_manifest.py` | `d8412c32…f07` | `8da79911` | mac |
| `aws_ec2/qual_permit.py` | `chpc/candidate_e2q/aws_ec2/qual_permit.py` | `51653d26…a8ad` | `c503e795` | mac |
| `aws_ec2/make_e2_funding.py` | `chpc/candidate_e2/aws_ec2/make_e2_funding.py` | `85e1b69c…43554` | new | mac |
| `chpc/row19_screen_controls.json` | `chpc/candidate_v17/row19_screen_controls.json` | `92f28b8f…80aa` | `01976b6a` | controls (LAST) |

The full 64-hex digests are in the map and in `build_v17.py` (`MAP`, `PREVIOUS`). Groups:
- **pin**: in the v17 `files` map. Programme lineage then requires each one present at these bytes in every controller tree.
- **partition reference**: the v17 `partition` entry.
- **data**: deployed as tracked files and bound transitively. The partition binds the snapshot's sha256; the panel, the
  qualifier and the release branch bind the funding, the manifests and the panel.
- **mac**: the Mac-only EC2 authority code that DESIGN_e2 s.6 step 5 promotes "with the Mac files". It is not a controls pin
  and no Lengau consumer exists.

Kept for provenance, never deleted or relabelled:
- `chpc/row19_partition_e1.json` (`8d1de408`): pinned by versions 13-16 (unchanged) and named as the e2 predecessor.
- `root/ec2/activation_e1.json`: stays on the Lengau root.

### Which qualifier: candidate_e2q's (superset), not merged

Both `candidate_e2/` and `candidate_e2q/` carry a `row19_ec2_qualify.py`. v17 pins the candidate_e2q copy (`73f912b8`,
REVISION 5). By its own text and by a line diff, it is the candidate_e2 REVISION 4 file (`efff0f95`) plus the epoch-2 `e2`
command.

The diff removes 10 lines, and each one is replaced:
- 2 docstring lines extended;
- the import order (the state module first, for the E2Q contracts);
- the candidate path search;
- 3 problem-message labels (`Q1` -> `label`);
- 2 problem texts that pointed at "not built";
- the `__main__` dispatch.

No epoch-1 rule was dropped. `test_v17.py` checks this.

Nothing was merged by hand. The candidate_e2 copy stays the reviewed REVISION 4 evidence and is not promoted.

The same holds for the Mac modules. The candidate_e2q `prod_authority.py`, `prod_launch.py` and `make_prod_manifest.py` are
the candidate_e2 REVISION 6 copies plus REVISION 7 (DESIGN_e2q s.1), so the e2q copies are promoted. `make_e2_funding.py`
exists only in candidate_e2.

## 2. What changed against v16, line by line

**The controls file.** The candidate is the adopted bytes plus ONE insertion: the version-17 object after version 16 (checked
with a byte-level sequence match). Versions 1-16, `programme`, `history_manifest` and `deployment` are byte-identical.

The version-17 entry is a copy of the v16 entry with these changes:

| Key | v16 | v17 |
|---|---|---|
| `version` | 16 | 17 |
| `commit` | "candidate: see the commit that adds this entry" | the same text (as v16 carried at adoption) |
| `reviewed` | the v16 text | "pending Codex review of controls v17, the EC2 provider epoch-2 adoption ... NOT adopted." |
| `files["chpc/row19_screen_admit.py"]` | `1b02f336` | `c3960464` |
| `files["chpc/row19_partition.py"]` | `ed6aa177` | `eabf50c3` |
| `files["chpc/row19_ec2_ingest.py"]` | `b697dc36` | `6ac144c6` |
| `files["chpc/row19_ec2_state.py"]` | `bda200dc` | `7bdedafc` |
| `files["chpc/row19_ec2_qualify.py"]` | `1fc6b61f` | `73f912b8` |
| `files["chpc/row19_ec2_e2rules.py"]` | - | `a9ea1f61` (appended) |
| `files["chpc/row19_ec2_e2qual.py"]` | - | `b3f29816` (appended) |
| `partition` | `chpc/row19_partition_e1.json` `8d1de408` | `chpc/row19_partition_e2.json` `48cea639` |

The remaining keys are byte-equal to v16:
- `files` for verify `d8d3c73b`, status `a9f9180b`, release `7a67fd1f`, programme_gate `10a53402`, resources `f5352bc3`, root
  `ceba9b32`, shadow `ce4dc15c`, the S manifest `eabbda2a`, the S plan `11ca19d6` and designated `a96eb598`;
- `sub_envelopes` (refit+S 81,000);
- `qualification_S`.

**The admission** (`row19_screen_admit.py`, line 2102 of the adopted file). One line out, four in, exactly the diff:

    -            print(f"provider partition epoch {part['epoch']}: {part['provider']} owns indices {part['indices'][0]}..{part['indices'][-1]} (k {part['k']})")
    +            import row19_partition as _RP                                     # v17: schema 2 has no k / indices (an explicit set)
    +            print(f"provider partition epoch {part['epoch']}: {part['provider']} owns "
    +                  + (f"{part['owned_count']} explicit coordinates (schema 2, owned {part['owned_sha256'][:12]})" if part.get("schema") == _RP.SCHEMA2
    +                     else f"indices {part['indices'][0]}..{part['indices'][-1]} (k {part['k']})"))

Under v16 the refit admission raises `KeyError('indices')` there on any schema-2 partition (`test_v17.py` reproduces it).
Under v17 it prints `provider partition epoch 2: ec2 owns 3274 explicit coordinates (schema 2, owned ee31504e4a04)`, and the
schema-1 line is byte-identical to v16's. The module docstring was left untouched, so it still describes REVISION 16
(choice 11).

**The helpers** are the reviewed candidate bytes. Their changes are described in DESIGN_e2.md s.1-s.3, s.7 (partition
REVISION 6, ingestion REVISION 6/7, the shared rules module) and DESIGN_e2q.md s.1-s.2 (the state copy with E2Q1/E2Q2 and
the qualifier `e2` command). The status view needs no change: it reads the partition through the admission and `blocked`.

## 3. What v17 does at each stage

**After promotion and deployment (v17 adopted, e2 not yet activated):**
- `activation_problem_v10` finds no `root/ec2/activation_e2.json`, so every Lengau refit admission HOLDS with "partition
  epoch 2 is pinned but not activated".
- An e1 proof cannot stand in for it, because proofs are per epoch file and v17 no longer pins e1. Under v17 the e1 proof is
  historical; it is kept, not erased.
- Running jobs keep running. Settlements go through `programme_gate.py run ... settle`, whose lineage check passes once every
  v17 pin is present.
- EC2 production stays shut. The live `ec2_release_state.json` has no `qualification_e2` block, and an epoch-1 certificate
  cannot release a schema-2 epoch: the REVISION 7 guard was tested against the REAL v17 controls bytes.

**After the canonical activation:**
- Lengau planning and admission refuse every owned coordinate. `blocked` = membership in the 3,274-coordinate set, through
  the unchanged v16 `designated_problem` / `partition_problem`.
- Lengau's scope is unchanged: its 13 replicates plus its existing claims.
- EC2 allocates only owned coordinates, after its own epoch-2 release.

**Consequences outside this folder:**
1. **Pilot qualification rollover.** The verifier stamps the latest controls version and `generation_problem` requires it,
   so the v16 pilot qualification `2c7a7ef1` and its adopted review stop satisfying the refit gate at v17. Refit admission
   therefore needs:
   - fresh v17 receipts;
   - ONE regenerated qualification from the existing job 1 (no fit);
   - a NEW Codex pilot literal;
   - `--adopt-review`.

   This is the v16 RUNBOOK step 7 pattern. The scale-up gate file `scaleup_refit_v16.json` is not generation-bound: if it is
   adopted before v17 it stays valid. The job-46 scale-up review (RSC `39b064b`) still needs its own literal.
2. **Release consumers.**
   - `row19_screen_release.py` (pinned, unchanged) lists the admission and the controls in `CONSUMER_FILES`.
   - The `release_p80` adoption binds admit / controls / controls version / designated.

   Both must re-pin the v17 bytes in their own reviewed packages before any numerical release.
3. **No way back to e1 by rollback.** Controls versions are append-only, and `activation_problem` requires every version from
   a proof's version onward to pin its partition. A later v18 re-pinning e1 would therefore find the e1 proof historical and
   would need a new activation. Undoing epoch 2 is a new reviewed epoch, never a revert.
4. **`row19_ec2_shadow.py` still hard-codes 60,000** (v16 known consequence). It is unchanged: S stays terminal.

## 4. Tests (`test_results.txt`)

- **`test_v17.py`: 45/45.** Four parts:
  1. **The candidate (24 checks):**
     - deterministic build; one insertion; versions 1-16 equal;
     - exactly seven changed pins plus the partition; the e1 provenance;
     - the superset proof; the state-copy diff; the admission = v16 + the diff hunk;
     - Python 3.7 grammar (the oldest this interpreter checks; the live controllers parse at the same level under the
       Lengau `t1py`);
     - `promote_v17` candidate check including `verify2` byte-equal regeneration of `48cea639` from `31cc268f` + e1;
     - promotion order; the archive inventory; the live tree untouched;
     - four tamper refusals; the review and archive gates.
  2. **Schema-2 admission (4 checks):**
     - v16 raises `KeyError('indices')`;
     - v17 prints the explicit-set line and reaches the activation check;
     - the schema-1 line is unchanged;
     - the v17 CLI with the real activation check HOLDS "pinned but not activated".
  3. **The activation hold (11 checks):** the HOLD from v17 adoption until the e2 activation, with an empty root, with only
     the real Mac copy of `activation_e1.json`, with the e1 proof at the e2 path, and with a canonical proof while v16 is
     still the adopted controls. The other checks:
     - the sandbox positive control;
     - a wrong owned set; a v16-version proof; a later version dropping the pin;
     - the e1 proof is historical under v17 and current under v16;
     - a canonical activation from the candidate controls file is refused.
  4. **The e1 release path (6 checks):**
     - `prod_authority` on the REAL v17 controls bytes sees e2 schema 2;
     - e1 certificates bound to e1 or e2 are refused by the schema-2 guard;
     - control: the v16 bytes do not trigger it;
     - an epoch-1 release never admits epoch-2 production;
     - the epoch-2 literal grammar.
- **Regression with the v17 module set** (`regress/run_v17_regress.py`). There are 14 suites, the live EC2 suites plus the
  candidate_e2 and candidate_e2q suites. All give identical counts BEFORE and AFTER, equal to `candidate_e2q/test_results.txt`.
  The four failures are pre-existing and identical in both columns.
- **The admission suites** in three configurations:

  | Suite | v16 | v17 code only | v17 controls |
  |---|---|---|---|
  | `test_designated_r16` | 78/2 | 77/3 | 77/3 |
  | `regress_pbs_settled_r13` | 51/0 | 51/0 | 51/0 |
  | `regress_crashed_slot_r14` | 70/1 | 70/1 | 70/1 |

  Every difference in `test_designated_r16` is a check of the controls file beside the admission: whether its last entry is
  "the v16 change", and whether its pins name its own admission. Each is listed in `test_results.txt`. Every code-behaviour
  check passes identically.
- **Limit.** The live suites import `row19_screen_admit` by name from `chpc/` (v16). A by-name substitution would change the
  admission's T1/controls paths, not its code, so it is not done. The one-line admission change is exercised in part 2 and in
  the admission suites.
- **Not tested on the Mac:**
  - the real promote, deploy and activation;
  - Lengau's `t1py` version (I can't determine it from the repository: the live controllers it already runs parse at the same
    grammar level as the candidate files);
  - a positive canonical activation (it needs the adopted v17 on the canonical path).

## 5. Choices for Codex

1. **The qualifier and Mac modules from candidate_e2q.** v17 pins the candidate_e2q qualifier as the superset of the
   candidate_e2 copy (s.1); the e2q Mac modules are promoted for the same reason. Nothing is merged by hand.
2. **The claims snapshot is promoted and deployed as tracked data, NOT pinned.** The partition binds its sha256, and every
   reader (the panel maker, `panel_problem`, the qualifier) checks it against that. The alternative is to pin it in `files`,
   so that lineage also refuses its absence.
3. **The e1 file is not pinned in v17's `files`.** Its provenance rests on four things: versions 13-16 (unchanged), the e2
   `predecessor`, the file kept in `chpc/`, and the proof kept on the root. The alternative is to pin it, so that lineage
   refuses its deletion.
4. **The Mac `aws_ec2/` code is promoted in the same step and not deployed to Lengau.** No Lengau consumer exists, so the
   controller clone keeps its old tracked `aws_ec2/*.py`, exactly as under v16. The alternative is to deploy them for tree
   consistency.
5. **`aws_ec2/prod/` becomes tracked for the e2 files.** On the Mac this folder is untracked today: the e1 Q1/Q2 operational
   manifests there were never committed and are left as they are. The e2 data files are committed with explicit paths and
   deployed as tracked files, because `ctl_clean` refuses untracked files in the controller clone.
6. **DESIGN_e2q's choice 3 is not applied.** `proposed_ingest_released_e2q_partial.diff` stays unapplied, so ingestion stays
   the reviewed `6ac144c6`. If Codex rules for the diff, the ingest pin changes, and v17 must be rebuilt (`build_v17.py`)
   and re-reviewed BEFORE adoption.
7. **One adoption step.** Helpers, data, Mac code, admission and controls are promoted and deployed together (controls last).
   The helpers cannot be staged earlier as authority, because no pin would cover them.
8. **The pilot rollover is required.** v17's generation change re-qualifies the existing job 1 (no fit, new literal). No
   exemption is proposed.
9. **The release consumers re-pin separately** (`row19_screen_release.py`, `release_p80`). No numerical release under v17
   until they do.
10. **Reversal is a new epoch**, not a rollback (s.3 item 3).
11. **The admission's module docstring is untouched**, keeping the diff byte-minimal, so the admission text still says
    REVISION 16. A REVISION 17 note would change the admission hash.
12. **The `--check` semantics.**
    - `promote_v17.py --check` verifies the candidate against its sources and the adopted bytes, with no review and no live
      state required.
    - `--check-promoted` is the v16-style deploy gate (complete promotion, exact adoption record, review, archive).
13. **The Mac archive inventory** has 13 members: the v16 bytes of every replaced file (seven chpc and four aws_ec2 files,
    the controls and the adoption record), the v16 pilot qualification `2c7a7ef1` and the committed budget phases.

## 6. Adoption and activation sequence (DESIGN_e2 s.6 steps 5-7 made concrete; NOT run)

Where commands run:
- On the Mac, from `workspace_demo/t1_access`.
- On Lengau, `T=/mnt/lustre/users/pvanrooyen/t1_toolchain`, in the controller clone `$T/rsc_screen_ctl/workspace_demo/t1_access`
  through `$T/t1py`, over `ssh -o ControlPath=none lengau`.

The migration scripts do not exist yet. They are a `chpc/migration_v17/` package on the `migration_v16/` pattern:
- `preflight_v17.sh`, `archive_v16.sh`, `deploy_v17.sh`, `rollover_pilot_v17.sh`, `adopt_pilot17.sh`;
- the shared `lengau.sh` / `remote_lib.sh`, `lengau_archive.py` and `mac_archive.py` with the v16_before_v17 inventories;
- `test_migration_v17.py`.

They need their own FAVOURABLE scripts review before step 1. `promote_v17.py` (this folder) is step 3.

**0. Preconditions** (each a committed record):
- Codex FAVOURABLE on the final e2 bytes (partition `48cea639`, snapshot `31cc268f`, funding `d6f414e8`, panel `f04a5e43`,
  manifests);
- the qualification package (`92a62f6`);
- this v17 candidate, with the literal of s.7;
- the migration_v17 scripts, with their tests passing.

The owner's conditional go applies at the stated gates. There is no live EC2 attempt (the handover requires it): qual-Q1/4 is
already dispositioned and fenced (ack_g48, inventory g52).

**1. Drain and full read-only preflight** (Mac + Lengau). Use the coordinated hold as in the v16 RUNBOOK step 1: refill
scripts not invoked, slot watcher stopped, no controller command running. No worker or reaper is stopped. The preflight
refuses unless all of these hold:
- **The Mac** holds the v16 bytes:
  - the controls `01976b6a`, the adoption `523fe18a`, the admission `1b02f336`;
  - the partition module `ed6aa177`, ingestion `b697dc36`, the qualifier `1fc6b61f`, the state module `bda200dc`;
  - no `row19_ec2_e2rules.py`, `row19_ec2_e2qual.py`, `row19_partition_e2.json` or `claims_snapshot_e2.json` in `chpc/`;
  - `promote_v17.py --check` exits 0.
- **The controller clone** is clean (`ctl_clean`: the three pinned untracked evidence files only) at the same v16 bytes, with
  no e2 file.
- **The gate** holds `qualified_refit_job1.json` `2c7a7ef1` and an active `review_refit.json`.
- **The root:** `$T/row19_screen/ec2/activation_e1.json` exists, and `activation_e2.json` does NOT.
- **No migration leftovers:** no `$T/archive_screen/v16_before_v17` and no `v17_deploy_proof`.
- **The drain is observed:** a successful process inventory showing no `row19_screen_admit|status|verify`, `row22_bank_*`,
  `row19_ec2_*` or `row19_partition` process; both lock probes free.
- **The science digest list** (eight files) is complete.

**2. Archive v16.**
- **Lengau:** `$T/archive_screen/v16_before_v17/` holds:
  - the controller HEAD;
  - every v16-pinned file plus the v16 controls and adoption, the budget phases, the manifest and the row-22 helpers;
  - the three untracked evidence files;
  - the gate (qualification `2c7a7ef1`, the active review, receipts, PBS copies), the jobs and a ledger copy;
  - `SHA256SUMS` and `COMPLETE`.

  It is staged, verified and published by one rename.
- **Mac:** `chpc/results/archive/row19_screen_v16_before_v17/` holds EXACTLY the 13 members of `promote_v17.ARCHIVE`, plus
  `SHA256SUMS` (`sha256  name`) and `COMPLETE` (schema `row19-screen-mac-archive-v16-before-v17-1`, `sha256sums` = the
  digest of `SHA256SUMS`, and the digest of the Lengau `SHA256SUMS`).

**3. Promote on the Mac.** First:

    python3 chpc/candidate_v17/promote_v17.py --dry-run --review reviews/<v17 record>.md

Then the same command without `--dry-run`. It copies, in order:
1. the e2 partition and data;
2. the Mac `aws_ec2/` code;
3. the helpers;
4. the admission;
5. LAST the controls.

It then writes the version-17 adoption record (atomic replaces, resumable; s.1 and the script text). Commit atomically with
explicit paths:

    git -C ~/Recoverable-Self-Coding add <the 20 promoted paths> workspace_demo/t1_access/chpc/row19_screen_controls_adoption.json workspace_demo/t1_access/chpc/results/archive/row19_screen_v16_before_v17 && git -C ~/Recoverable-Self-Coding commit -F <msg> -- <the same paths>

Then run `python3 chpc/candidate_v17/promote_v17.py --check-promoted --review reviews/<v17 record>.md`; it must exit 0.

**4. Deploy to the controller clone** (`deploy_v17.sh`, the `deploy_v16.sh` pattern). The payload travels inside the one
Lengau script, each file checked against its Mac sha256. It is 17 files, every one committed in ONE controller commit as
TRACKED files:
- the controls, the adoption record and the v17 review record;
- the seven pins (`chpc/row19_screen_admit.py`, `row19_partition.py`, `row19_ec2_ingest.py`, `row19_ec2_qualify.py`,
  `row19_ec2_state.py`, `row19_ec2_e2rules.py`, `row19_ec2_e2qual.py`);
- `chpc/row19_partition_e2.json`, `chpc/claims_snapshot_e2.json`, `aws_ec2/e2_funding.json` and
  `aws_ec2/prod/{manifest_production_e2,manifest_e2q1_e2,manifest_e2q2_e2,panel_e2q_e2}.json`.

Tracked, because `ctl_clean` refuses any untracked file except the three pinned evidence files. A data file left untracked
(or copied in from `$T/t1_toolchain/e2_stage/`) would make every later preflight, archive, deploy and adopt refuse.
`e2_stage/` is outside the clone. It is the candidate staging of 19 Oct, not authority, and stays untouched.

The deploy proof `$T/archive_screen/v17_deploy_proof/` is written before the first controller write. It holds the
eight-file science before-manifest and the intent, and gets `DONE` only after an identical after-manifest. The job clone
`rsc_screen` is never written.

Expected after the commit:
- `authority '' lineage '' controls ''`;
- `designated ''`;
- `A.partition(m, manifest)` -> schema 2, epoch 2, owned 3,274 (in `$T/t1py`);
- the local-vs-remote pin comparison IDENTICAL (the 17 v17 `files` + the partition + the data files);
- the three evidence files untracked and unchanged;
- `DEPLOY OK`.

From this commit on, Lengau refit admission HOLDS ("partition epoch 2 is pinned but not activated"). Running jobs continue.

**5. A fresh installed inventory** (Mac), at most 6 h before step 6 (`INVENTORY_MAX_AGE_S`):

    python3 aws_ec2/prod_authority.py inventory
    python3 aws_ec2/ec2_sync.py cycle

These install generation N on the root and acknowledge it. Check that no attempt is live and that no owner exists outside
the 3,274.

**6. Canonical activation** (Lengau, under the common plan lock, which `activate` takes itself):

    ssh -o ControlPath=none lengau 'cd /mnt/lustre/users/pvanrooyen/t1_toolchain/rsc_screen_ctl/workspace_demo/t1_access && /mnt/lustre/users/pvanrooyen/t1_toolchain/t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json'

Expected: `activated epoch 2: .../row19_screen/ec2/activation_e2.json sha256 <...>`.

It refuses (exit 3; `problems` and `facts` printed; nothing written) when any of these holds:
- the plan lock is held;
- the canonical controls are not the adopted, tracked, unmodified v17;
- the latest version does not pin `48cea639`;
- the e1 activation is missing or names another partition;
- the inventory is stale, or shows an owner outside the epoch, or a live attempt of another epoch;
- an EC2 history problem;
- any Lengau claim on an owned coordinate.

v16 Lengau never plans an unclaimed coordinate of the 47 replicates, so a claim after the 19 Oct 09:18Z snapshot is not
expected. If one appears: re-snapshot, re-declare, re-review. Never erase a claim. The e1 proof stays on the root as
provenance.

**7. ACK and receipts.**
1. Run `python3 aws_ec2/ec2_sync.py cycle`. A new generation binding `activation_e2.json` is installed and acknowledged.
2. Run the refit receipt `python3 chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit --publish-receipt`,
   expecting:
   - fresh, production, zero alarms;
   - generation 17;
   - the designated line;
   - the EC2 binding with `activation_e2`.
3. Run the bank receipt as before.

**8. Pilot qualification rollover** (v16 RUNBOOK step 7 pattern).
1. `lengau.sh rollover_pilot_v17.sh` retires `review_refit.json` (bound to `2c7a7ef1`) to
   `gate_retired/review_refit.v16_qual2c7a7ef1_max100.json`.
2. Make ONE call: `python3 chpc/row19_screen_status.py ... --publish-receipt --qualify 1` (the existing job 1, no fit, a new
   hash). A `NOT QUALIFIED` stops the migration.
3. Package the evidence as `chpc/qualification_v17_<qsha8>/`.
4. Codex writes `ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100`.
5. Run `lengau.sh adopt_pilot17.sh --file reviews/<record>.md`.

Lengau refit admission then resumes under the unchanged v16 scope rules and the scale-up gate.

**9. EC2 epoch-2 qualification** (DESIGN_e2q.md s.7, "Then, only after the reviewed E2Q1 permission record exists"):
`qual_permit.py --epoch2`, budget, inventory and sync, the receipt, the dry run, ONE E2Q1 instance, staging (still
undocumented: DESIGN_e2q s.4), `row19_ec2_qualify.py e2`, the actual-result review, `release-adopt`. Production stays shut
until then. R6' (five interleaved admissions and reconciliations) and the capacity evidence are still required.

**Never, at any step:**
- no worker or reaper stop or restart;
- no edit of reviewed bytes after their literal;
- no manual permission, qualification, ledger or inventory edit;
- no deletion or relabelling of plans, claims, records or proofs (e1 included);
- no pilot fit;
- no reuse of an old ADOPT or pilot literal;
- no AWS spend before the epoch-2 release and a fresh budget check.

**Abort and recovery:**
- Before step 4, a failure leaves Lengau on v16. A Mac promotion committed but not deployed leaves Lengau on v16; do not run
  the Mac status commands until step 7.
- After step 4 and before step 6, Lengau refit admission holds and science continues. A failed activation is reported
  verbatim. Its cause is repaired by the reviewed route (a fresh inventory, a re-snapshot); the controls are never reverted.
- A `DEPLOY HELD` keeps the controller and its proof for an explicit recovery decision.

## 7. Proposed ADOPT literal

    ADOPT row19-screen-controls sha256=92f28b8fbd53a2a13635022ff01d2a76ef75a1986e670311ccfb768f7cdc80aa version=17

This is the v16 grammar. `promote_v17.py` requires exactly this line in a committed, unmodified review record in HEAD. It
covers the controls and the pinned controller implementation only, not the migration scripts, the pilot rollover, the EC2
qualification or any release.

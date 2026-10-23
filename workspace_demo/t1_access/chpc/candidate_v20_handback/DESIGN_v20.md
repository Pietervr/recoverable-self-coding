# Row 19 screen controls v20 - CANDIDATE, not adopted: the EC2 CLOSE (epoch-2 block handed back to Lengau, route A)

Written 23 October 2026 (R052, Claude, bounded job; brief Unimog-Projects `prompts/2026-10-23_r052_handback_v20_job.txt`,
commit f6b02e195). Owner decision 23 Oct 2026 in the R052 chat: "go with route A" - of the three costed routes (A: hand the
3,274 EC2-designated coordinates back to Lengau, USD 0, about 15 days at 10 jobs, funded by a CHPC allocation increase; B: EC2
on-demand about USD 7,000; C: EC2 spot about USD 1,600). EC2 is finished for row 19.

Nothing was promoted, deployed, activated or run against Lengau, PBS or AWS; no live file was edited; no ledger, inventory,
permission or release state was touched. New bytes only in `chpc/candidate_v20_handback/` and `chpc/migration_v20/`. The parent
session runs one synchronous Codex review of this candidate before the migration.

## 1. What v20 does, in one paragraph

Controls v20 pins a new, terminal, predecessor-linked epoch **e3** (`chpc/row19_partition_e3.json`, schema
`row19-provider-partition-3`) in place of e2. In e3 EC2 owns **nothing**; its `handed_back` set is every coordinate e2 owned that
EC2 never completed - today all 3,274 - and its `retained_ec2_completed` set is the EC2-completed part of e2's set (today
empty). The Lengau admission's provider scope gains exactly the hand-back set (`lengau_scope`, REVISION 20), so those
coordinates are planned by the **unchanged** replicate-complete order. The activation of e3 (the existing `row19_partition.py
activate` command, under the plan lock) is the hand-back step and enforces the close preconditions. The Mac EC2 authority
(`aws_ec2/prod_authority.py` REVISION 10) refuses every further row-19 EC2 qualification, production, release and allocation
for good once any controls version pins a schema-3 epoch. No change to fit code, estimand, seeds, folds or pass conditions;
none was needed.

## 2. Why a closing epoch (schema 3) and not a "close" record beside e2

The brief left the form open. A schema-3 epoch reuses the reviewed machinery end to end:

- **One authority for ownership.** Every consumer already asks the pinned partition (`blocked`, `owned_set`). With e3 pinned,
  `blocked` is False everywhere and `owned_set` is empty, so the Lengau planner/admission guard, the status view, the EC2
  allocator, launcher and ingestion all see "EC2 owns nothing" through the one predicate they already use. A side record would
  need every consumer to read a second file, and e2 (still pinned) would keep saying EC2 owns 3,274 coordinates.
- **Serialized hand-over for free.** A pinned partition without its activation proof already HOLDS every Lengau refit admission
  (`activation_problem_v10`); `activate` runs under the common plan lock and writes an immutable proof. The close preconditions
  are added there (`close_problems`), exactly as e2 added `handover_problems`.
- **Lineage.** The proof is bound to the v20 entry; e2's canonical proof becomes *historical* under v20 (`activation_problem`:
  "a controls version after the activation no longer pins this partition"), so every e2 consumer - launcher, ingestion,
  qualifier - refuses from v20's adoption on, without any change to their code.
- **Hash-linked.** e3's `predecessor` names e2 by epoch, schema, sha256 (`48cea639`), path and the digest of its owned set;
  `load()` re-reads e2 at that path on every load and requires `handed_back + retained = e2's owned set`, disjoint.
- **Terminal.** `declare3` refuses a schema-3 predecessor, `declare2`/`schema2_problem` only accept schema-1/2 predecessors, and
  prod_authority treats any version that ever pinned a schema-3 file as closed (a later version cannot re-open it).

The DESIGN_e2 sentence "A hand-back to Lengau is impossible in this schema" stays true: schema 2 is unchanged; the hand-back is a
new schema, and `declare2`'s refusal of a hand-back is untouched.

## 3. Files

| File | SHA-256 | Change |
|---|---|---|
| `row19_partition.py` | `a762933779529a20d6f458dd7118105c855ea122353b1eaa168a8b033c6dc17e` | v19 `eabf50c3` + REVISION 7 (`partition_v19_to_v20.diff`): schema 3 (`declare3`, `schema3_problem`, `close_problems`, `handed_back`, `is_closed`, `completed_of_register`), `declare3`/`verify3` commands; `blocked`/`owned_set`/`transferred_of`/`activate`/`activation_problem`/`cutover_problems` dispatch schema 3. Schema 1/2 code paths unchanged |
| `row19_screen_admit.py` | `7c49bf86c6809941bc982393fb4ae095f7186e0c47665c426c27350a841b08af` | v19 `27e066c7` + REVISION 20 (`admit_v19_to_v20.diff`): `lengau_scope(doc, claimed, part=None)` adds `RP.handed_back(part)`; its three callers pass `part`; the admission's partition print line handles schema 3 (it would raise KeyError on `part['indices']`) |
| `row19_partition_e3.json` | `ca87fb1da163df10e720e5778542d2bcc5c78f30fc08b6a1cc61d671773f0e6a` | the closing declaration, `declare3` from e2 `48cea639`, the designated declaration `a96eb598` and the Mac copy of the root register (no ingested entry): handed back 3,274, retained 0, owned 0 |
| `aws_ec2/prod_authority.py` | `e1381d6811a517c3ebae09c1889ed7dafda97431842760ca963e951041b85c87` (repaired, s.11; was `20de63d2`) | live `ba726a19` + REVISION 10 (`authority_v19_to_v20.diff`): `ec2_closed`/`closed_problem`, the refusals, `release_state` closed, `close_precondition_problems`, the read-only `close-check` command. Not a controls pin (a Mac tool) |
| `row19_screen_controls.json` | `4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c` | adopted v19 `111c3107` versions 1-19 byte-equal + one version-20 entry |
| `v20_promotion_map.json` | `79c78ea737f3123eb864185d5c73d35cdd63a1159e60199704933c8f690c4945` (s.11; was `b3335953`) | rows: partition module, admission (pins); e3 (data, new path); prod_authority (mac, previous `ba726a19`); the controls last |
| `build_v20.py` / `promote_v20.py` | `6e82bb13…` / `4dfd0557…` | the build_v19/promote_v19 base-first pattern re-pointed at the v19 base (`111c3107` / adoption `2b9f3c78`), the Mac archive `row19_screen_v19_before_v20` (9 members) |
| `test_v20_handback.py`, `regress/`, `test_results.txt` | - | section 7 |

Controls v20 = adopted v19 with ONE appended version-20 entry: exactly two pins change (`chpc/row19_partition.py`,
`chpc/row19_screen_admit.py`) and `partition` moves from e2 `48cea639` to `{chpc/row19_partition_e3.json, ca87fb1d}`. The status
view, EC2 state, E2Q module, ingestion, qualifier, root, shadow, node-failure rule and capture script, verifier, release consumer,
resources, designated declaration, programme gate and the qual_S pins, `sub_envelopes` (refit+S 81,000), `qualification_S`, the
top-level `programme` and `deployment`, and versions 1-19 are unchanged. The operator adoption record must carry exactly:

    ADOPT row19-screen-controls sha256=4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c version=20

## 4. The close: preconditions and post-conditions (all enforced, none assumed)

**Mac half - `python3 aws_ec2/prod_authority.py close-check`** (read-only, no generation written; `close_precondition_problems`):
no coordinate owned in any ledger; every non-rejected production/qualification attempt reconciled and `ingested` or
`dispositioned` (a pending disposition request is named); the latest sealed inventory is the current generation, valid, at most
six hours old, and shows no live or owning attempt. On the real Mac ledgers today it reports **NOT MET**: `qual-E2Q3/1` is
reconciled but ingestion **pending** (it still owns its 52 rep-24 work coordinates), and `qual-Q2/1` is reconciled but pending
(it owns 0 coordinates, but `row19_ec2_state.owns` counts any pending attempt as owning). Both must be dispositioned first
(migration step 0b). qual-Q2/1 matters beyond bookkeeping: `current_problems` accepts an installed inventory older than six hours
only while it shows no live or owning attempt; with every attempt terminal the inventory becomes terminal history and Lengau
needs no further `ec2_sync` after the close.

**Lengau half - the e3 activation** (`row19_partition.close_problems`, under the plan lock, after the existing checks: the latest
adopted controls pin e3, the predecessor e2's activation is on the root and names e2, `history_problems`, the cutover scan):

1. the root's INSTALLED authority inventory is sealed and fresh (six hours) - a stale one refuses;
2. it shows no owner and no live or owning attempt; every non-rejected production/qualification attempt is reconciled and
   ingested/dispositioned - a live claim (E2Q3 pending), a lease (an attempt launched) or an undispositioned attempt refuses;
3. the root register's EC2-completed coordinates on e2's set equal the declared retained set and none is handed back - an
   EC2-completed coordinate in the hand-back refuses ("completed stays completed");
4. post-condition: Lengau's closed scope (13 Lengau replicates + Lengau's claims on the 47 + the hand-back) plus every completed
   coordinate covers S x 0..79, and no coordinate is both Lengau-scoped and EC2-owned (EC2 owns nothing).

The e3 proof binds the partition, the hand-back and retained digests, `owned_sha256` of the empty set, `closed: true`, the
predecessor and the v20 entry. **The single-ownership invariant holds at every instant:** before the activation the e3 pin
already makes `blocked` False but Lengau admission HOLDS (no proof) and every EC2 admission refuses (closed), so no coordinate can
be claimed by both; after it, EC2 owns nothing.

**After v20, prod_authority refuses** (terminal, not a missing permit): `exclusion_problem` (the first gate of every
`prod_launch` admission, every contract and epoch), `e2q_admission_problem` (E2Q1/E2Q2/E2Q3), `production_release_problem`,
`release_problem` (so `release-adopt`), `allocate`; `release_state` reads every qualification permission and the production
block NOT ok with the close as the reason (so `qual_permit` refuses too). `ack`, `disposition`, `disposition-confirm`, `inventory`
and `budget` keep working (bookkeeping). The live `e2q_stage.py` pins the v19 controls and refuses under v20 anyway.

## 5. The planner (REVISION 20)

`lengau_scope(doc, claimed, part)` = the 13 Lengau replicates x 0..79, plus Lengau's claims on the 47, plus `handed_back(part)`
(the empty set for no partition and for schema 1/2, so before the close the planner is byte-for-byte the v19 planner - tested on
the real snapshot). `designated_order`, `designated_problem` and `designated_view` pass `part`. The crash rule
(`crash_history`/`crash_excluded`, byte-identical), the disabled rescue route, the scale-up gate, the 24-core x 48 h envelope,
the 4.5 GiB stop, the futility look and the prefix 0..79 are unchanged.

**Order - verified, with one qualification of the brief's "unchanged by construction".** On the local snapshot belonging to
receipt `watch_refit_20261023T050233Z` (zero alarms; done 1,144, in flight 198, Lengau plannable 179, EC2 waiting 3,274,
rescue-pending 5):

- the v19 order rebuilt from that snapshot is the receipt's (179 coordinates, the same first 24);
- the v20 order **restricted to the v19 scope is the v19 order exactly** (same coordinates, same sequence), and it is extended by
  exactly the 3,274 handed-back coordinates (3,453 in all), ascending (rep, index);
- because the block is the 47 LARGEST replicate IDs, every old coordinate on the 13 Lengau replicates (178 of the 179) still
  precedes the whole block. **But** Lengau's own re-plannable claims on the 47 interleave with the block by replicate: today one
  such coordinate, **73/8**, moves from v19 position 178 to v20 position 2,192 (it waits until replicate 73 is reached). That is
  the existing replicate-complete rule applied to the larger scope, not a new rule; it changes no estimand (the terminal look is
  over S x 0..79 whatever the order). If the v19 refill of about 24 Oct 04:00Z plans the 179 first, nothing moves at all.
- the first 10-job round under v20 (from today's snapshot) = the 178 Lengau-replicate coordinates, then 62 of replicate 24's
  block (24/11 ...).

## 6. Funding (item 3)

**Nothing is raised in this build.** The ledger cap stays 81,000 (`row19_screen_budget.json` phase 2), the refit+S sub-envelope
stays 81,000 (the version entry's `sub_envelopes`, unchanged), and the CSCI1913 allocation stays 100,000.

**The allocation is already ONE declared value; it is left as it is.** `allocation_core_h` is declared once, in the screen
manifest's `funding` block (100,000.0). `programme_gate.programme_funding(man)` is the single place every programme admission
reads it (the screen admission, the shadow S route and the wrapper for the bank, shard and slice controllers): it takes the
manifest's `funding` and overlays the adopted controls' top-level `programme` block (`f.update(ctl["programme"])`). The manifest
is immutable (every binding names its sha256), so the lift is one key, `"allocation_core_h": <new>` (with an `allocation_note`
naming CHPC's grant), in the controls `programme` block. Because the 81,000 sub-envelope is itself a controls value
(`sub_envelopes`), the later raise is necessarily a controls-version migration in any case; that one step lifts the sub-envelope
and the allocation and runs the ledger's existing two-phase `--raise-cap <new> --note "<owner ruling>"`. No code change is needed
for it. (A raise-cap-style CLI for the allocation would have to change `programme_gate.py`, which every programme controller
pins; not worth it for one lift.)

**Arithmetic** (Mac ledger copy, 66 settled + 10 live entries; receipt `watch_refit_20261023T050233Z`):

| Quantity | Value |
|---|---|
| refit ledger spent / live / cap | 40,070.2 / 11,520 (10 jobs x 1,152) / 81,000 core-h |
| settled per coordinate, all 21 designated-order jobs | 12,229.3 / 504 = **24.26** core-h |
| settled per coordinate, the last 10 settled jobs (57-66) | 6,157.5 / 240 = **25.66** core-h |
| the brief's planning rate | **26.4** core-h (used below; conservative) |
| still to admit after v20 | 179 + 3,274 = **3,453** coordinates (the brief's ~3,458 adds the 5 rescue-pending, which the disabled rescue route never admits) = 144 jobs, about 14.4 rounds of 10 |
| in flight, to settle | 10 jobs, about 6,336 core-h at 26.4 |
| refit ledger at the end (settled) | 40,070 + 6,336 + 3,453 x 26.4 = **about 137,600** core-h (about 129,700 at 24.26) |
| what the cap must admit | the last full round is admitted while the previous one is settled: settled + 10 x 1,152 reserved, i.e. about 137,600 - 6,336 + 11,520 = **about 142,700** - so the cap (and the refit+S sub-envelope, plus S's 2,304) must rise by **about 61,000-62,000**, to about 142,000-145,000 |
| programme allocation | about 142,700 + every other CSCI1913 commitment. The brief's ~165,000 implies about 22,000-23,000 committed outside the refit campaign; **I can't determine that from the Mac** (the other campaign ledgers live only on Lengau): `t1py chpc/programme_gate.py check --manifest chpc/row19_screen_manifest.json` on Lengau prints the committed total |
| when 81,000 binds | a full 10-job round needs refit spent + S 2,304 + 11,520 <= 81,000, i.e. spent <= 67,176; at about 6,336 per round from 40,070 that is 4 more full rounds (24, 25, 26, 27 Oct at about 26 h each), and the round of **about 28 Oct** is cut short - matching the brief |

## 7. Tests (`test_results.txt`)

- `test_v20_handback.py`: **66 passed, 0 failed** at a8cc1dd; **77 passed, 0 failed** after the s.11 repair - A the declaration (regeneration, split, 12 tamper refusals, a hand-back
  coordinate claimed completed, retention of an EC2-completed coordinate, terminality, e1/e2 unchanged); B the close activation in
  sandbox roots seeded from the local Lengau copy (record names only): accepted with all preconditions; refused with a live claim
  (E2Q3 pending), an undispositioned attempt (qual-Q2/1 pending), a lease (launched), a stale (7 h) inventory, an EC2-completed
  coordinate in the hand-back, no predecessor activation, v19 controls; e2's proof historical under v20; C the planner on the real
  snapshot (section 5, incl. receipt arithmetic 4,800 = 1,144 + 198 + 179/3,453 + 3,274/0 + 5 and the dry-run/status view: EC2
  waiting 0); D prod_authority (open today = the live v19 answers; closed: every gate refuses; terminal against a later version;
  bookkeeping untouched; `close-check` NOT MET on the real ledgers, MET after the two dispositions, refused on a stale or old
  generation; prod_launch calls `exclusion_problem` first); E the controls, funding unchanged, Python 3.7 grammar, live tree
  untouched.
- Regression (`regress/regress_all.py`, `regress/regress_results.txt`): ten existing suites, each run with the LIVE v19 modules
  and with the v20 modules substituted (partition module, admission, authority), by name and by explicit path. Identical
  pass/fail on nine: `test_prod_authority` 54/5, `test_prod_launch` 61/1, `test_ec2_sync` 12/0, `test_e2_partition` 54/0,
  `test_e2_authority` 74/3, `test_e2q_contracts` 53/1, `test_designated_r16` 78/2, `test_v19_oploss` 74/2, `test_v19_e2q3` 37/12
  (the failures are the same pre-existing stale pin / live-tree / controls-identity checks under both). `test_e2q_release`: the
  v19-substituted baseline aborts part-way (28/29: it expects the candidate_e2q authority path); without substitution it is 79/2
  and with v20 75/6 - the four extra failures are the release branch refusing certificates whose bound code set includes
  `chpc/row19_partition.py` (its bytes change in v20) and the REVISION 6 qualification counter (2) the old fixture expects where
  the live REVISION 9 has 3. Neither matters after the close (every release is refused).

## 8. Pilot qualification

**v20 lapses e123d6e5.** Not because the change touches job execution (it does not: the job clone, manifest, worker, fit code
and envelope are unchanged) but because the pilot gate is generation-bound: `qualification_problem` -> `verifier_problem` ->
`generation_problem` requires the retained verifier document's generation to be the LATEST controls version with the ADOPTED
controls sha256. Any new controls version therefore lapses the pilot. **Minimum requalification** = the v19 route exactly: ONE
regenerated qualification of the existing job 1 (no fit): retire the v19 review, `row19_screen_status.py --role refit
--publish-receipt --qualify 1` on a fresh zero-alarm v20 receipt, package it, an operator record with a NEW
`ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100` literal, adopt. Avoiding it would need a change to the
generation rule; not proposed.

## 9. Live sequence (nothing of it was run; `chpc/migration_v20/RUNBOOK.md` holds the commands)

0a. operator record with the v20 ADOPT literal; fill the `@record` pin; commit. 0b. (can run now, under v19) disposition
`qual-E2Q3/1` and `qual-Q2/1`, `ec2_sync.py cycle`, `disposition-confirm` both, then `prod_authority.py inventory` +
`ec2_sync.py cycle` and `prod_authority.py close-check` = MET. 1 preflight. 2 archive v19. 3 promote + commit. 4 deploy
(identical check). 5 generation-20 receipts (e2 still bound; admission HOLDS from here until step 6). 6 the CLOSE: a fresh
installed inventory (within six hours), then `t1py chpc/row19_partition.py activate --manifest chpc/row19_screen_manifest.json
--partition chpc/row19_partition_e3.json` under the plan lock on Lengau. 7 fresh receipt: EC2 waiting 0, Lengau plannable about
3,453, activations e1+e2+e3. 8 pilot rollover. 9 refill (10 jobs).

## 10. Departures from the brief, and choices

1. **Order "unchanged by construction" is true for the 13 Lengau replicates, not for Lengau's re-plannable claims on the 47**
   (one coordinate today, 73/8; section 5). Kept the existing rule; reported.
2. **The allocation is left as the single manifest value with its controls override** (section 6); no new mechanism.
3. **qual-Q2/1 must be dispositioned too**, not only E2Q1/E2Q2/E2Q3 (section 4): it is "owning" in the authority's own sense.
4. **The status view is not changed**: it reads the planner's view; its line "EC2-designated unclaimed (wait for the EC2 epoch
   package)" reads 0 after the close. The wording stays (changing it would add a third pinned file for a label).
5. **e3 is declared now from the Mac register copy** (no EC2-completed coordinate can exist: no release-adopt ever happened); the
   migration re-verifies it (`verify3`) against the root's register, and the activation compares the live register again.
6. `row19_partition.py` is in the epoch-2 release code set (`E2_RELEASE_CODE`); v20 changes its bytes, which would invalidate any
   epoch-2 certificate - irrelevant, since the close refuses every release.

## 11. Repair for Codex's review of 23 Oct (`reviews/2026-10-23_row19_v20_handback_codex.md`, RSC d3a56b4)

**F1 - fail-closed terminal detector.** `prod_authority.ec2_closed()` now authenticates every partition reference in the
controls history before classifying it: the referenced file must be a regular file (no symlink) at its path, hash to the
reference's sha256 and parse as a JSON object with a schema. A missing, unreadable, hash-mismatched, malformed or symlinked
historical partition, or a malformed reference, returns (True, refusal): every gate refuses ("the EC2 close state is unknown;
refused (fail closed)"), never OPEN. With the authenticated e3 anywhere in the history the result stays CLOSED. On the live v19
tree every historical reference (e1, e2) authenticates, so today's answers are unchanged (test D1). New tests D9a-D9i: with a
LATER current pin (a v21 pinning e2) and the historical e3 missing / invalid JSON / replaced by e2's valid schema-2 bytes / a
symlink to the intact e3 / one byte appended / a directory, `ec2_closed`, `closed_problem`, `exclusion_problem`,
`e2q_admission_problem` and `production_release_problem` (with otherwise permissive synthetic release inputs) all refuse; the
intact e3 under the same history reads CLOSED; a malformed reference and a missing e1 in a v19 history refuse.
Package identities: `aws_ec2/prod_authority.py` `20de63d2` -> `e1381d68`, the promotion map `b3335953` -> `79c78ea7`. **The
controls sha256 does not change (`4e64982b`)**: the controls pin the partition module and the admission, not the Mac authority
(it is a map row of group `mac`, as in v19), and neither pinned file changed. The ADOPT literal is therefore unchanged.

**F3 - frozen fixtures.** B5's pending-owner inventory and D11-D13's ledgers are now built from a FROZEN fixture,
`fixtures/inventory_g105.json` (`03cb4433`, the immutable sealed archive generation 105 in which qual-E2Q3/1 is pending and owns
52 coordinates and qual-Q2/1 is pending), pinned and checked by B0; D13b adds the zero-coordinate qual-Q2/1-alone case. The live
Mac close-check is printed as an observation only (today: MET, after the owner's 0b of about 08:00Z, g108/g109). Result:
`test_v20_handback.py` **77 passed, 0 failed**.

**F2 - the frozen local migration rehearsal:** `chpc/migration_v20/test_migration_v20.py`, **39 passed, 0 failed**
(`chpc/migration_v20/test_results.txt`; coverage list in `chpc/migration_v20/RUNBOOK.md`, Tests). The migration_v19 harness
re-pointed at the adopted v19 (frozen fixture RSC `add8586`), the real script bodies, a network-refusing fake Lengau transport,
and the REAL canonical close (`row19_partition.py verify3` / `activate` CLI, plan lock, `close_problems`, proof publication;
only the frozen manifest's storage paths are remapped to the fake root). Positive route through the pilot adoption; admission
held before the close and before the new pilot review (the real v20 admission's gates); the close refusals (pending E2Q3,
zero-coordinate pending Q2, a launched attempt, stale inventory, changed retained set, missing cover, held plan lock, wrong
pre-existing proof, v19 controls); an interruption right after the proof publication and the idempotent retry; every existing
archive / containment / science-preservation / interrupted-deploy check. It caught one real defect, fixed: `close_v20.sh` piped
into `grep -q` (the 9df2a1f SIGPIPE pattern) - now `grep -F ... >/dev/null`.

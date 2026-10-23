# Row 19 controls v20 hand-back: Codex review

23 October 2026. R052, synchronous review of candidate RSC `a8cc1dd` and migration RSC `7a3ec45`.
Paths below are relative to `workspace_demo/t1_access/`. Candidate and migration files remained unchanged during review.
No ssh, AWS command, deployment, disposition, activation or other live action was performed. This review grants no adoption
literal. Only this review file is to be committed.

The ownership transition and scientific scope are sound on the intended route. I require two changes before migration:
make the terminal EC2 detector refuse when its historical partition evidence cannot be authenticated, and rehearse the v20
migration in frozen local worlds, including its new close step. The order in the RUNBOOK should be retained.

## Findings, ranked by severity

### F1 — P2: missing or changed historical e3 evidence removes the terminal refusal

`chpc/candidate_v20_handback/aws_ec2/prod_authority.py:275`, `:277`, `:279`.

`ec2_closed()` catches a partition read/parse failure and continues. It also classifies the file's schema without comparing
the bytes with the controls reference's SHA-256. Consequently, a controls history that contains v20 ceases to mean CLOSED
if its e3 file is missing, malformed, or replaced by a valid schema-2 document. `closed_problem()` cannot catch the read
failure because the inner function has swallowed it.

Reproduced entirely in a temporary tree: copy the candidate controls, append a version 21 pinning e2, and retain the v20
entry. With intact e3, `ec2_closed()` returns true and the exclusion, qualification and production gates refuse. Remove e3,
write invalid JSON, or put e2's bytes at its path: `ec2_closed()` returns false; `exclusion_problem({}, region)` returns
empty, and the qualification/production gates accept otherwise permissive synthetic release inputs. These are gate-level
probes, not a claim that a complete launcher admitted an instance. While v20 itself remains current, the launcher's separate
current-partition check still refuses missing/wrong e3 bytes. The defect is the promised permanent refusal after a later
controls version changes the current pin; the existing D9 test covers that case only with e3 intact.

Required repair: authenticate the referenced partition bytes before classifying them, and propagate missing, unreadable,
malformed or hash-mismatched evidence as a refusal, never OPEN. An authenticated terminal marker in the controls history is
another possible implementation. Add negative tests with a later current pin and damaged historical e3 evidence. Rebuild
the affected package identities and verify the exact repaired package before adoption.

### F2 — P2: static checks do not qualify this migration for execution

`chpc/migration_v20/RUNBOOK.md:137`; `chpc/migration_v20/static_check_v20.py:43`;
`chpc/migration_v20/close_e3.sh:24`, `:41`, `:44`.

The admitted absence of the v20 migration harness is a verification condition, not an acceptable substitution by the 26
static checks. This route changes the active partition and activation semantics, adds pre/post receipt phases, carries a
Mac authority replacement, and puts an irreversible close before pilot rollover. Parsing a composed shell body never
executes its checks. The candidate's activation tests call `activate(..., mode="sandbox")`; they do not exercise the
canonical CLI/proof publication through the migration scripts or their recovery branches.

Before step 0a, run a frozen v19-to-v20 local rehearsal using the real promotion/archive/deploy/check/close bodies and a
network-refusing fake Lengau transport. Cover the positive route through pre-close receipts, canonical e3 activation,
post-close receipts and pilot rollover/adoption. Include admission held before activation and before the new pilot review;
pending E2Q3 and zero-coordinate Q2, stale inventory, changed retained set and missing cover; a held plan lock; wrong or
pre-existing proof; and an interruption immediately after proof publication followed by an idempotent close retry. Preserve
the existing archive, containment, science-preservation and interrupted-deployment checks. Stubbing scheduler receipt
collection is reasonable; stubbing away the activation being qualified is not.

### F3 — P3: two negative tests depend on live, movable bookkeeping

`chpc/candidate_v20_handback/test_v20_handback.py:177`, `:236`, `:360`.

The unmodified suite now reports **64 passed, 2 failed**, rather than the archived 66/0. Its B5 E2Q3 fixture is copied from
the latest real inventory, and D11 expects the real ledgers still to be pending. Both E2Q3/1 and Q2/1 are now dispositioned
in the local bookkeeping, so B5 does not construct its advertised pending owner and D11 correctly finds no close problems.
This is fixture drift, not evidence that `close_problems()` admits a pending owner. Freeze/construct those negative inputs
and keep the live close-check observation separate from the deterministic test result. Include this repair in F2's evidence.

## 1. Single ownership, integrity and activation preconditions

For the reviewed declaration, EC2-owned is empty, handed-back is exactly e2's 3,274 coordinates, and retained EC2-completed
is empty. `schema3_problem()` authenticates the e2 predecessor and requires the disjoint union of hand-back and retained to
equal its owned set (`chpc/candidate_v20_handback/row19_partition.py:553`). The declaration binds the designated set,
manifest and task identities; it neither extends S nor admits indices outside 0..79.

The critical checks are executed at activation. `activate()` checks adopted controls and the latest partition pin, checks
historical EC2 provenance and the predecessor proof, then calls `close_problems()` (`row19_partition.py:829`, `:840`,
`:847`, all in the candidate directory). The CLI holds the common exclusive plan lock across those scans and immutable
proof publication (`:1026`, `:1043`). Specifically, `close_problems()` at `:616` requires:

- A sealed installed inventory no more than six hours old, no coordinate owner and no live/owning attempt. Its independent
  attempt scan requires every non-rejected production/qualification attempt to be reconciled and ingested/dispositioned.
  Q2/1 is therefore required even with zero coordinates.
- The root register's EC2-completed set on the predecessor's coordinates to equal the declared retained set, with no
  EC2-completed coordinate handed back.
- Coverage of all 4,800 designated coordinates by closed Lengau scope plus completed coordinates, and no scope/EC2-owned
  intersection. Uncompleted crash-excluded coordinates remain accounted for and rescue-pending, not silently dropped.

The Mac check additionally requires the latest inventory to be the authority's current generation
(`chpc/candidate_v20_handback/aws_ec2/prod_authority.py:1012`). The root activation checks its installed view; it cannot
independently observe the Mac's current generation. The Mac check, deployment of the closing authority, installed inventory
and coordinated drain together supply that cross-machine ordering. This is enforced by the migration route, not an atomic
lock spanning the two machines.

No double assignment, loss of a designated coordinate or late EC2 publication was found on that route. Before e3 activation,
the new pin has no proof, so Lengau admission holds (`chpc/candidate_v20_handback/row19_screen_admit.py:337`, `:2453`);
the promoted Mac authority already refuses EC2 admission. After activation, Lengau's scope gains the hand-back and EC2 owns
nothing. Old e1/e2 bundles fail the latest adopted partition pin/activation lineage before ingestion; dispositioned attempts
also fail the inventory and root-register fence checks (`chpc/row19_ec2_ingest.py:457`, `:471`, `:525`). F1 qualifies the
claim of permanent closure under later controls, rather than identifying a collision in this migration.

## 2. Science and planning order

Confirmed: the candidate changes the partition module, Lengau admission scope/printout, Mac authority and controls/data
bindings. It changes no fit code, estimand, producer manifest, seeds, folds, draw stream, first-80 prefix, crash rule,
futility look or pass condition. Versions 1–19, all other controls pins, funding and resource limits remain equal to v19.

`lengau_scope()` adds the hand-back, and `designated_order()` still sorts the eligible coordinates by `(rep, index)`
(`chpc/candidate_v20_handback/row19_screen_admit.py:2059`, `:2107`). The v20 order restricted to v19's scope equals the v19
order. The full order need not preserve an old coordinate's absolute position: 73/8 moves from zero-based position 178 to
2,192 because it now waits for replicate 73 among the returned block. This changes scheduling and may affect which work
finishes before a funding stop. It is consistent with replicate-complete planning; completion timing was never guaranteed
to follow admission order across concurrent jobs.

The sealed look does not use the first completed replicates or admission rank. It uses fixed S and indices 0..79 and waits
for all 60 designated datasets to be terminal (`chpc/release_p80/row19_screen_release_p80.py:100`, `:273`, `:868`, `:968`).
Missing work does not become terminal merely because funding or the planner stops; the existing reviewed missing-coordinate
certificate route remains necessary. Thus the interleaving does not alter the declared decision. It authorizes no interim
look and no PASS. The already outstanding release-consumer re-pinning remains necessary before numerical release
(`chpc/migration_v20/RUNBOOK.md:127`); this migration does not clear it.

## 3. Terminality and continued bookkeeping

With the intact authenticated package, the new close gates cover launcher admission/exclusion, E2Q1/E2Q2/E2Q3,
production, allocation and release-adopt. `release_state()` suppresses every qualification permission and production, so
qual_permit also refuses. The current-pin and activation-lineage checks prevent ingestion of historical EC2 results; the
current e3 pin owns no work. The old staging tool's v19 controls pin independently refuses under v20.

Ack, disposition, disposition-confirm, inventory and budget retain their existing implementations and remain callable.
They are bookkeeping, not a route to new admission. Once the terminal inventory is installed, the existing terminal-history
exception permits it to age without recurring sync (`chpc/row19_ec2_state.py:287`). The universal claim that no later
controls can reopen EC2 needs F1's repair.

## 4. Migration order and evidence

The RUNBOOK's order is appropriate: finish/fence both dispositions and install a fresh terminal generation under v19;
preflight; archive v19; promote and commit; deploy to the controller clone; obtain pre-close v20 receipts; verify3 against
the root register and activate e3; obtain post-close receipts; retire the old pilot review; regenerate qualification from
existing job 1; package and adopt its new literal; then refill. Keep the cooperative controller/admission hold through the
new pilot adoption. Running scientific jobs continue.

The old pilot `e123d6e5` lapses when generation 20 becomes current, independently of the absent e3 proof. Activation removes
only the partition hold; it does not revive the v19 pilot. Requiring `act3_valid` before rollover and adoption is correct
(`chpc/migration_v20/rollover_pilot_v20.sh:33`; `chpc/migration_v20/adopt_pilot20.sh:38`). No new pilot fit is needed.

Evidence assessed: the complete DESIGN_v20, actual candidate changes against live v19, e3, candidate tests/results,
regression results, RUNBOOK/close scripts/static checks and relevant e2/declaration/consumer context. The archived regressions
are not an all-green certification: they contain stated baseline failures and a release suite whose substituted v19 run
aborts. Their matching results are useful regression evidence, with those limits.

Local verification in this review:

- Unmodified candidate suite: 64/2, with exactly the two fixture failures in F3.
- Independent temporary-world probes: terminal inventory accepted; pending E2Q3, pending zero-coordinate Q2, seven-hour
  inventory and a five-coordinate scope-coverage hole each refused. The terminal-detector probes reproduced F1.
- Static replay: 26/0. The source was executed in memory with only its cleanup of the live `__pycache__` directory disabled,
  preserving this review's read-only scope. Shell bodies were composed/parsed only; no transport was invoked.

F1 and F2 block migration as currently written. Funding increases remain a separate adoption before the existing cap binds;
they are not prerequisites for closing EC2 ownership, and this review authorizes none.

VERDICT: FAVOURABLE WITH CONDITIONS: repair and test fail-closed historical partition authentication in the terminal EC2 detector; freeze the drifting negative fixtures and pass a v20 migration rehearsal including canonical close, refusal and recovery paths before adoption or migration.

# Row 19 screen controls v21: the FUNDING ROUTE (CSCI1913 first, then HEAL1922, per admission, side by side)

Written 26 October 2026 (R052, Claude, bounded job; brief Unimog-Projects `prompts/2026-10-26_r052_heal1922_funding_route_job.txt`,
commit 4c4f3c25c). Owner rulings in the R052 chat:

- 17 Oct 2026: "yes, we can charge this to those hours - don't start with that again" (HEAL1922 may carry the row-19 refit).
- 26 Oct 2026 ~18:30Z: "once we are out of our own limit we go to HEAL1922".
- 26 Oct 2026 ~19:00Z: "make sure that we can run jobs on HEAL1922 while we are running our own so that there is no holdup
  when we switch over".

No science byte moves (fit code, estimand, seeds, folds, pass conditions, the crash rule, the rescue route, the partition e3,
the manifest and every manifest pin are unchanged). Under the owner's 20 Oct 2026 rule this is an operational change, adopted by
an OPERATOR record carrying the ADOPT literal, not by a Codex review.

## 0. The route check (brief item 4, done first, 26 Oct 2026)

- `qsub` of a trivial job charging HEAL1922 on the `test` queue (1 core, 5 min, `hostname; date`): **accepted**, job
  **7587231.sched01**, ran on **cnode0885** at 18:45:27Z, `Exit_status 0`, `project = HEAL1922`, `resources_used.walltime
  00:00:01`. Output: `PBS_JOBID=7587231.sched01`, `cnode0885`, `Mon Oct 26 18:45:28 UTC 2026`.
- In addition, the exact refit request shape on `serial` (`select=1:ncpus=24:mpiprocs=24:mem=120gb:nodetype=haswell_reg`,
  `walltime=30:00:00`, `-P HEAL1922`) was submitted **held** (`qsub -h`) as **7587238.sched01**: accepted (state H, `project =
  HEAL1922`), then deleted with `qdel` at once. It never ran.
- The `serial` queue has no project ACL (`qstat -Qf serial`); the project is checked at `qsub`, which refused Gert's first code
  LHM001 earlier and accepts HEAL1922.

## 1. What v21 does

Controls v21 = adopted v20 (`4e64982b`) with ONE appended version-21 entry:

| Change | Detail |
|---|---|
| `chpc/programme_gate.py` | v20 `10a53402` + REVISION 5: `route_of`, `entry_programme`, `committed_by_programme`, `route_choice`; `committed_core_h` / `funding_problem` keep their meaning for the route's FIRST programme; `programme_funding` adds the latest version's route and validates it; `check` prints both programmes; the settle wrapper logs both programmes before and after |
| `chpc/row19_screen_admit.py` | v20 `7c49bf86` + REVISION 21: `funding_assignment`, `charge_programme`, `programme_problem`; the gate checks the route per job; the PBS `-P` comes from the plan's `programme` |
| `funding_route` (new key) | `[{CSCI1913, 100,000, other 6}, {HEAL1922, 100,000, other 0.01}]` with notes |
| `sub_envelopes` refit+S | `cap_core_h` 81,000 -> **181,000** (= 81,000 + HEAL1922's 100,000); the same campaigns; the rule text says why |

Every other pin, the partition (e3 `ca87fb1d`), `qualification_S`, the top-level `programme` block, `deployment` and versions
1-20 are byte-equal to v20. The manifest is NOT edited: its SHA-256 is bound everywhere. The route lives in the controls
lineage, the v20 pattern.

## 2. The rule (brief items 1 and 2)

- **The route.** An ordered list in the latest controls version. Its first entry must be the manifest's programme with exactly
  the allocation (100,000) and other use (6) that `programme_funding()` already resolves, so each number has one source. A
  mismatch, a duplicate, a malformed code or a non-finite number refuses. Without the key, the route is the one programme, which
  is the behaviour of every earlier version.
- **The choice.** Each job of an admission goes, in order, to the FIRST programme whose own committed core-hours, plus the jobs
  this admission already gave it, plus this job's full reservation, fit its allocation. The admission refuses only when a job
  fits no programme. The switch is per admission, never a drain: the first job that does not fit CSCI1913 goes to HEAL1922 at
  once while CSCI1913 jobs keep running and settling. A later job goes back to CSCI1913 when settlements below the reservation
  free room there again ("first that fits", test C8).
- **The accounting.** An entry's programme is its `programme` field. **An entry without the field was charged to CSCI1913 by
  definition.** That covers every entry written before v21 and every entry of the bank, shard, slice, originals and S
  controllers, which never write the field. Old entries are never rewritten. A field naming anything outside the route, or
  null, cannot be counted and refuses. A programme's committed = its own settled charges + its own non-settled reservations
  (worst case) + its own declared other use. CSCI1913 therefore still counts every CSCI1913 ledger (slice, shard, bank, screen,
  originals, S) exactly as before: tested equal to REVISION 4 on the real ledger copy (B3).
- **Where the code is written.** (a) Into the job's ledger entry, under the campaign ledger's own lock, right after the
  reservation and before the plan, the script or qsub (`charge_programme`). This writes through the pinned
  `row19_ledger.CampaignLedger.locked()`; `row19_ledger.py` is a manifest pin and is NOT changed. Its `validate()` accepts the
  extra key, and bind, runner start, runner end and settle keep it (test B10). (b) Into the plan as `programme`. (c) Into the
  PBS script's single `#PBS -P` line. Before qsub, `programme_problem` requires the script, the entry and the plan to agree.
- **Settlement** credits the entry's own programme, because the field stays on the entry (B11, E3). The settle wrapper and
  `row19_ledger.settle` are unchanged.
- **An interruption** between the reservation and the field leaves an unsubmitted, unbound reservation without the field. It is
  counted against CSCI1913, which is conservative: it never overruns either programme (D9).
- **The bank, shard, slice and S controllers** still write `#PBS -P CSCI1913` from their own manifests. The wrapper therefore
  still admits them against CSCI1913 only (`funding_problem` is unchanged). None of them is running today; if one is needed
  after CSCI1913 is spent, it needs its own route (not built here).

## 3. Concurrency (the owner's 19:00Z requirement)

- (a) Side by side: tested in C7/C8 (10 CSCI1913 live + 3 HEAL1922 live; next job to HEAL1922; back to CSCI1913 after
  settlements) and end to end in D2/D5 (job 111 admitted on HEAL1922 while ten CSCI1913 jobs are live and untouched; one
  admission of three jobs split CSCI1913 / HEAL1922 / HEAL1922 with matching `-P` lines).
- (b) Live before CSCI1913 binds: v21 changes nothing while CSCI1913 fits (every job keeps `-P CSCI1913`; D1 and C1), so it
  can be deployed now. The first refill that v20 would refuse for funding is admitted on HEAL1922 instead.
- (c) The route check is in section 0.
- (d) The mixed set: C7, C8, D2, D5.
- The programme lock still serialises every admission and settlement: E1 (an admission waits for a held lock) and E3 (a
  settlement through the wrapper waits too). E2 checks that the route, reservation, charge, plan and qsub sit inside the one
  `with PG.programme_lock(...)`.

## 4. The refit ledger cap (brief item 3): the operator raise, once, to 181,000

**Per-programme caps are not possible without changing a science pin.** The refit ledger's own cap is enforced inside the
pinned `row19_ledger.py`, in `reserve` and also in `runner_start` (a job refuses to START when spent + live > cap). It counts
every entry. Making it per-programme would change a manifest-pinned file. So the cap must be raised; the only choice is when.

**Choice: one two-phase raise at the migration, 81,000 -> 181,000** (`--raise-cap 181000 --note "<owner ruling 26 Oct>"`, the
v16 protocol, `migration_v21/raise_cap_v21.sh`), and the refit+S sub-envelope to the same 181,000 in the v21 controls.
181,000 = 81,000 + HEAL1922's 100,000. The most the refit campaign can ever hold is its CSCI1913 share (at most 100,000 minus
the other CSCI1913 ledgers, about 80,200) plus HEAL1922's 100,000, about 180,200. So neither cap can bind before the
per-programme allocations do: the programme gate is the binding constraint. Raising in steps "as HEAL1922 hours are used" would
make every step a chance for a tick with an empty slot, which the owner's requirement rules out.

**What this changes, stated plainly.** v20's sub-envelope stopped the refit at about 79,776 core-h of CSCI1913 (81,000 minus
S's 1,224.4). Under v21 the refit may use CSCI1913 up to the allocation, about 430 core-h more, because the other CSCI1913
ledgers are all settled today (no live entry). That uses CSCI1913 completely before HEAL1922, which is the owner's ruling. If
CSCI1913 must keep a reserve for another controller, the route's CSCI1913 allocation cannot simply be lowered, because
`route_of` requires it to equal the manifest value. The reserve would be an `other_settled_core_h` declared in the top-level
`programme` block, which the route must then repeat (a controls change). None is declared today.

**HEAL1922 reserve for omega = 2.** The gate lets the refit use all of HEAL1922's 100,000. Whatever the screen does not use
stays available, as the owner said. A hard reserve would be a lower HEAL1922 `allocation_core_h` in the route (a controls
value); none is set.

## 5. Arithmetic today (Lengau ledgers read 26 Oct 2026 18:44Z, no lock taken)

| Ledger | Settled | Live |
|---|---|---|
| row19_campaign | 720.7 | 0 |
| row19_shard_campaign | 4,791.8 | 0 |
| row22_bank_campaign | 10,882.5 | 0 |
| row19_screen_campaign (cap 81,000) | 61,062.2 | 0 |
| row19_screen_orig_campaign | 2,168.6 | 0 |
| qual_S/campaign | 1,224.4 | 0 |
| other declared | 6 | |
| **CSCI1913 committed** | **80,856.2** | |

**Correction to the brief.** The live resource policy (`chpc/row19_screen_resources.json`, from job 10 on) reserves 24 x 48 h
= **1,152** core-h per refit job, not 24 x 30 h = 720. With 80,856.2 committed and nothing settling in between, 16 more jobs fit
CSCI1913 and the 17th goes to HEAL1922 (test C11). With j101-j110 queued (11,520 reserved, about 92,376 committed), about six
more fit. Settlements at about 600 core-h free about 550 each. So the switch comes in the round after j101-j110.

## 6. Tests

- `test_v21_heal.py`: **62 passed, 0 failed** (`test_results.txt`). A the route (validation, the no-field rule); B
  per-programme accounting (old entries CSCI1913; no cross-counting; the REAL local ledger copy equal to REVISION 4; the field
  survives every real ledger step; settlement credits its own programme); C `route_choice` (CSCI1913 while it fits, the exact
  boundary, HEAL1922 past it, refusal, per-job split, the mixed live set, back to CSCI1913 after settlements, today's numbers);
  D the admission end to end through the real `main()` with its science and receipt gates stubbed and the funding, ledger,
  cap, sub-envelope, plan, PBS script and a fake qsub real (the chosen `-P`, refusal reserves nothing, a failed charge holds
  before qsub, the dry run, a pre-v21 plan still `-P CSCI1913`, the cap counts both programmes); E the lock (admission and
  settlement wait; one lock around the whole admission); F the controls (deterministic build, exactly the intended
  differences, the route against the real manifest funding, Python 3.7 grammar, live tree untouched, and the REAL e3
  activation proof `fb3304d3` still canonical under v21).
- Regression (`regress/regress_all.py`, `regress/regress_results.txt`): the eleven existing suites, each run with the LIVE v20
  modules and with the v21 modules substituted (programme gate, admission). Nine are identical pass/fail. That includes
  `test_prod_authority`, which aborts identically under both on the live "row-19 EC2 is CLOSED" refusal (pre-existing since v20)
  and so reports no parsable checks. `test_v20_handback` has the same outcomes; it differs only in temporary directory names
  inside check labels. **`test_designated_r16`: two checks differ**, "dry run: one
  job, the gate would admit" and "the same receipt for planning and the gate -> would admit". That fixture stubs
  `programme_funding` to `{}` and the whole gate to "". v21 evaluates the route again in `main()` to get the per-job
  assignment, and an empty funding block cannot be counted, so the dry run refuses ("funding cannot be established"), which is
  correct fail-closed behaviour. With a countable funding block the same dry run admits (D8). The third r16 check ("a newer
  receipt ... would REFUSE") stays identical because the route is evaluated after the receipt check.

## 7. Pilot qualification

As at v20, any new controls version lapses the pilot (`generation_problem` binds the verifier document's generation to the
LATEST version and the adopted controls). Minimum requalification is the v20 route: retire the active max-200 review to
`gate_retired/review_refit.v20_qual2e99d615_max200.json`, run ONE metadata-only `--qualify 1` on a fresh zero-alarm v21 receipt,
package it (`migration_v21/package_qual_v21.py`), write an operator record with a NEW `ADOPT row19-screen-pilot role=refit
qualification=<qsha> max_job=200` literal (max 200: the scope the owner set on 26 Oct), commit it in both clones, then adopt.
Refit admission HOLDS from the deploy until that adoption. Settlements are not affected.

## 8. Open

- **HEAL1922's real balance.** The gate assumes the whole 100,000 is available to this campaign. HEAL1922 is Gert van Zyl's
  programme; use by other members is invisible here. Lengau has no usage tool on the login node (none of `mybalance`,
  `chpc_usage` or `sbank` exist). CHPC's allocation report, or Gert, would settle it. If others use it, lower the route's
  HEAL1922 `allocation_core_h` (a controls change).
- The expiry (5 April 2027) is not enforced by the gate.
- The bank, shard, slice and S controllers are CSCI1913-only (section 2).

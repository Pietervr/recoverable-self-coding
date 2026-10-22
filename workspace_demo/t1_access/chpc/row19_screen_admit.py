"""Ledger row 19, STAGE 2 (the screen): plan, gate and submit packed jobs for BOTH screen roles (login node, through t1py).
Codex RSC 9202e8b items 1, 5 and 7.

ROLES (`--role`):
  refit  the declared resample indices of the 100 fresh datasets, by the UNCHANGED row19_shard.py worker (one index per
         worker, per_slot 1); ledger kind "shard" in the screen campaign; plan slots {slot, rep, indices}.
  orig   the 100 lossless originals, by row19_screen_orig.py (one dataset per worker); ledger kind "orig" in the originals
         campaign; plan slots {slot, reps}.
Each role has its own manifest (the screen manifest and the originals manifest: the same datasets, identities, cfg and pins,
their own root and campaign), its own pilot and its own later admission.

EVIDENCE (never memory or names): DONE = a record (refit: row19_shard.read_record against the screen task; orig: a valid
lossless cache read back by row19_slice.read_orig) of a declared rep and index; any other file HOLDS. IN FLIGHT = the plan of
a live ledger entry of the role's kind whose runner has not ended; a live entry without its plan HOLDS. MISSING = the rest.
Nothing outside the screen's own roots is ever DONE: the development datasets 0-2 are external parity anchors only.

PLAN: refit - (REVISION 16) the designated replicate-complete order over S x 0..79 within Lengau's scope (below); revisions
1-15 planned index-major over all 100 reps (job 1 = reps 3..26 at index 0); orig - the missing reps in order, `cores` a job.

THE GATE (all must hold; the reason is printed):
  - no STOP file in the role's root; the manifest's code pins hold in the clone the jobs run from;
  - the seed domain: the 100 resolved seeds recomputed and equal to the declared SHA-256, unique, disjoint from the
    manifest's excluded set (historical, the three development datasets) AND from the bank manifest's 408 seeds
    recomputed from that manifest (no caller-supplied list); the declared identity map complete for all 100 reps and,
    for every PLANNED rep, equal to what this runtime computes;
  - FUNDING: settled + live reservations of EVERY declared campaign ledger (slice, shard, bank, screen, originals) + the
    declared settled charges outside them + this submission's full reservations <= the programme allocation;
  - the first job of a role is its pilot (`--pilot`, alone, only while the ledger holds no entry of the role's kind);
  - every later job: (1) <root>/gate/qualified_<role>_job1.json, written by row19_screen_status.py --qualify, parsed and
    bound to what THIS process recomputes (manifest SHA-256, root, campaign, code pins, wrapper, job 1's PBS id, token and
    plan SHA-256, the task bindings of job 1's reps, and the anchor verdict's SHA-256); (2) <root>/gate/review_<role>.json
    from `--adopt-review` ONLY with (1) holding: a git-tracked, unmodified review record, its SHA-256, the qualification's
    SHA-256 and a highest job number, never overwritten; (3) the newest <root>/gate/watch_<role>_*.json: fresh, production,
    zero alarms, <= 2,700 s old, bound to the same values and to EVERY job of the role the ledger holds now.
THE CAP (item 7): the scientific manifests declare `budget.core_hours_cap: null`, so the unchanged runner never compares a
cap and the manifests' SHA-256 (named by every binding) never moves. The live cap lives in the campaign ledger, created at
the initial phase of chpc/row19_screen_budget.json and raised only by `--raise-cap NEW --note "<owner's ruling>"`, which
records old, new, note and time in the ledger's cap_history (row19_ledger.raise_cap) and appends the phase to the budget file.
No spent hour is reset, no binding rewritten. The allocation stays the hard stop.

    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --pilot [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_orig_manifest.json --role orig --pilot [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest M --role R --adopt-review reviews/<record>.md --max-job-number N
    t1py chpc/row19_screen_admit.py --manifest M --role R --jobs K [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest M --role R --raise-cap NEW --note "<owner ruling>"

REVISION 2 (Codex RSC a1ce224, before any role's job 2): (a) every admission runs inside the PROGRAMME lock
(chpc/programme_gate.py) with a strict fresh read of all five campaign ledgers - finite non-negative charges, no booleans,
missing expected ledgers HOLD - so no two admissions anywhere in CSCI1913 interleave; (b) a cap raise is a two-phase
amendment (the budget phase written `pending`, the ledger raised, the phase committed) and an interrupted one is reconciled
or refused before any admission; (c) the qualification and the receipt are parsed strictly: finite non-boolean times, the
embedded receipt's job-1 summary terminal F with scheduler and runner exits 0/75, every worker ended 0, nothing left, finite
observed memory, the EMBEDDED anchor verdict hashing to the bound digest with index 0 equal on all three anchors and nothing
differing, missing, invalid or conflicting, and the bound task bindings EXACTLY the root's (every started task, no subset);
(d) a review is adopted only when its git-tracked, unmodified record contains the line
`ADOPT row19-screen-pilot role=<role> qualification=<sha256> max_job=<n>` matching the gate's qualification and the request;
(e) the seed domain reconstructs the whole exclusion contract (the historical list from the slice manifest pinned in
chpc/row19_screen_controls.json, the three development seeds, the 408 bank seeds) and requires it EXACTLY; (f) the controller
refuses unless its own bytes and its sibling controllers' are the latest version in chpc/row19_screen_controls.json.

REVISION 3 (Codex RSC ee99ee1): R1 the pilot qualification is checked against JOB 1's OWN scope (its job binding and the task
bindings of its own reps, which must still be the root's), while every fresh receipt must bind EXACTLY the whole current set of
started task bindings - so job 1's frozen evidence serves every later admission; R2 every job summary a receipt carries is
validated against its plan (terminal: state F, scheduler and runner exits 0/75, the plan's exact worker count ended, worker
exits only 0/75, finite non-negative memory, integers that are not booleans), and the pilot summary must show the plan's
exact worker count all ended 0; R3 the qualification and the receipt name a retained full verifier document in the gate
whose bytes match the bound digest, whose schema, role, manifest and controller generation (latest, clean lineage) hold,
and whose anchor verdict and binding digests equal the summary's; R4 budget phases are parsed strictly (finite positive caps,
non-finite constants refused, booleans refused), a proposal is validated BEFORE its pending phase is published, phases are
written atomically and durably (temp + fsync + rename + directory fsync), an interrupted raise is RESUMED by repeating the
same `--raise-cap X` or RETIRED by `--retire-pending --note`, and the ledger's latest cap_history entry must match.

REVISION 4 (Codex RSC 8bd1451, C1-C4): C1 a fresh receipt never covers a job whose CURRENT ledger state moved since it was
observed (a job the receipt saw queued/running that has since recorded a runner end, or a terminal job whose recorded runner exit
differs) - recollect first; exit codes and counts are strictly typed (integers, never booleans, never negative). C2 the retained
verifier document's emitted digests must EQUAL the reviewed pins (its own SHA-256 = the latest version's verifier pin; its
controls SHA-256 = the ADOPTED controls digest), with an explicit clean lineage field, clean environment/code verdicts, clean
binding flags, and units consistent with the summaries (a completed pilot: every planned unit a valid record with timing naming
its job and slot; every job: the units whose timing names it equal its summary's `new`). C3 the lineage file is trusted only
through an independent adoption: chpc/row19_screen_controls_adoption.json (git-tracked, unmodified) names the controls file's
SHA-256 and a git-tracked, unmodified review record that carries `ADOPT row19-screen-controls sha256=<sha> version=<n>`; the
controls file must have exactly that SHA-256 and n must be its latest version - before ANY of its programme, deployment or
history values are used. C4 a resumed raise is reported only after the ledger's cap AND its latest cap_history entry are
certified equal to the phase; any other combination (a ledger above the pending phase, no history entry) refuses.

REVISION 5 (Codex RSC f40991e, C1/C2/C4 remainders): C1 a receipt that calls a job queued/running is refused also when the
ledger now shows that job SETTLED (a killed job settled from accounting has no runner end); C2 a unit counts only with a valid
record AND a valid timing, and only when its coordinate is in THAT job's plan with that plan's slot; each summary's PBS id must
be the job's bound id; C4 a pending raise is applied only when the ledger still certifies the preceding committed phase (its cap,
and its latest cap_history entry or none for the first phase), or is reconciled only when the ledger already shows exactly that
raise (cap = pending, latest history old = preceding, new = pending); a pending phase is retired only when the ledger still
certifies the preceding phase; anything else refuses and changes nothing.

REVISION 6 (Codex RSC 74dae6d): C2 a unit counts only when its coordinate IS in the job's plan (explicit membership) and its timing
slot is an integer equal to the plan's slot; a terminal job's summary must partition its plan exactly (new + resumed + left =
the planned units) and every planned unit that is not left must have a valid record with valid timing; C4 the automatic
reconciliation in cap_problem uses the same exact applied-pending certificate as the CLI (cap = pending, latest history
new = pending AND old = the preceding committed phase); anything else refuses.

REVISION 7 (Codex RSC 8865474): C2 a terminal job's summary carries its HISTORICAL per-unit partition (`partition`: the new,
resumed and left coordinate lists the status tool reads from that job's own worker statuses), and the admission reconciles
it, not today's aggregate: the lists partition the job's plan exactly and match the counts; every new unit is a valid record
whose timing names THIS job in its plan slot; every resumed unit is a valid record whose timing names an EARLIER bound job
whose plan holds that coordinate in that slot (unbound producers such as P999 and null slots never count); a left unit may
carry a valid record only from a LATER bound job that planned it (later completion stays legitimate, but it can never
certify an earlier job's resumption claim). C4 the automatic reconciliation accepts ONLY the applied certificate (latest
history old = the preceding committed phase, new = pending, cap = pending); the predecessor-only branch never clears a
pending phase automatically; and the CLI refuses a raise of less than one core-hour.

REVISION 8 CANDIDATE (Codex R052 record reviews/2026-10-09_refit_wall_kill_codex_record.md, verdicts 1 and 2; NOT adopted):
(1) CLOSED-NO-RECORD DISPOSITION. A receipt summary that carries `disposition` (kind closed-no-record) is never taken on its word:
disposition_problem() recomputes, here, every condition from the CURRENT ledger, the root and the PBS output on disk - a fresh
successful terminal scheduler observation (state F, an observed integer exit kept as observed, finite memory, zero ended / new /
resumed / left, no worker measurement); the CURRENT ledger entry SETTLED with settlement evidence (finite charge, technical note,
settlement time) equal to the summary's, its token, PBS id and plan the receipt's and the root's, and NO runner-end field
(runner_exit, runner_ended, runner_wall_s); no status file scoped to the PBS id (by name, any slot, planned or not, or by its
parsed `job`), no unreadable status of unknown scope; no unit whose timing names the job, no timing file anywhere that names it
or cannot be read, and every file at a planned coordinate (record or timing, temporary files included) a valid record whose
timing names a LATER bound job that planned that coordinate in that slot; and the role/job PBS output
(<toolchain>/jobs/row19_screen_<role>_<n>.out) present, readable, the bytes the receipt bound (`bound.job_outputs`), naming the
PBS id and carrying no ADMISSION FAILED. The disposed plan's coordinates are accounted as `uncompleted` with
`uncompleted_origin` "plan" (no invented worker status); a later bound retry completes them only through its own plan, job and
slot (the revision-7 producer rule). A dispositioned job never qualifies a pilot. The transition check re-reads the ledger:
SETTLED, the same charge and PBS id, no runner-end field - else recollect. The loss stays charged; nothing is credited.
(2) PROSPECTIVE RESOURCE POLICY. chpc/row19_screen_resources.json (pinned in the controls lineage; a changed copy refuses) gives
refit jobs from `first_job` on a walltime-only envelope (serial / 24 cores / 48 h / 120 GB / 1,800 s reserve / one index per
worker; every field but the walltime must equal the frozen manifest's, which is never edited). Admission resolves each NEW job's
envelope (jobs below first_job and every originals job keep the manifest's request), funds the sum of the resolved full requests
(programme allocation, campaign cap pre-checked before any reservation), and binds it in the plan (`walltime_s`, `queue`,
`envelope`), the ledger reservation (cores x walltime = 1,152 core-hours at 48 h), the filled PBS request and the job-start /
deadline arguments (checked in the script text before qsub); every receipt job at or above first_job must show the same envelope
in its plan, its CURRENT ledger entry and the scheduler's observed walltime request.
REPAIRS of Codex 5cb9a02 (c1956ef's bytes rejected) and ce06828 (28861c4 not favourable on R1's timing validity): R1 a disposed
coordinate counts as a later completion only when its CURRENT canonical timing (coordinate, declared identity, producer job,
integer slot, and the verifier's timing_ok measurement contract: wall_s, fit_seconds, maxrss and t present, finite, non-negative
and non-boolean) and record (checksum, coordinate, identity) are the
retained verified evidence (current_artifacts_problem); an absent or changed artifact refuses until recollected. R2 the status
view binds the observed settlement certificate (charge, note, non-negative time, token, PBS id, plan SHA-256) in the disposition;
admission and the transition check require it EXACTLY equal to the current ledger entry (certificate_problem), and a negative
settlement time refuses. R3 the reservation's cores must be an exact non-boolean integer equal to the envelope's, with
reserved = cores x walltime (no truncation).

REVISION 14 CANDIDATE (R052 12 Oct; refit job 13 7531397, slot 16 = rep 83 index 2 died of SIGSEGV after an LLVM "Cannot
allocate memory" during XLA compilation, 22.6 h into its only resample; NOT adopted). CRASHED-WORKER SLOT DISPOSITION: a terminal
refit job whose only defect is that one or more planned workers died of a fatal signal before writing any status. A Python-level
failure always writes a status (row19_shard worker's BaseException handler), so a missing status with job-end HELD 4 is either
such a death or unexplained; crashed_slot_evidence() separates the two and is the ONE implementation (the status view calls it to
report; this admission recomputes it from the CURRENT ledger, root and PBS output/error bytes and requires the receipt's
disposition to be exactly equal). All must hold: the scheduler observation is state F with exit 4; the ledger entry is SETTLED
with its settlement certificate and runner exit 4 (HELD); the plan is the entry's token, job and PBS id; every surviving worker's
status names this job and slot with exit 0 or 75 (a HELD worker is not a crash), and the status files scoped to the PBS id are
exactly those; the PBS output names the PBS id, carries no ADMISSION FAILED and exactly one 'job <n> ended: exit 4; workers exit
codes [...]' line whose list is None exactly at the missing slots and the statuses' exits elsewhere; the PBS error stream carries,
per missing slot, exactly one bash job-control line naming the job's script (<PBS id>.SC) and a fatal signal (Segmentation fault,
Bus error, Aborted, Illegal instruction) for THAT slot's exact planned worker command (rep, indices, slot), and no other worker
death line (Killed / Terminated never qualify: an external kill is not a worker fault); no unit at a crashed coordinate carries
timing naming the PBS id; EVERY timing file naming the PBS id (V15-1, Codex 5ca7fbd) is readable, at its canonical path
timing/rep<R>/t_<iii>.json with strict integer rep, index and slot, the path EXACTLY the publisher's formatting of them
(row19_shard.timing_path: no leading-zero rep alias), and at a SURVIVING worker's planned
coordinate in that worker's slot (an orphan outside the plan, a wrong slot or a path alias refuses); and every crashed coordinate holds no
file, or only a later bound job's verified planned completion (R1). The receipt binds the output and error bytes
(`bound.slot_outputs`); the summary keeps the actual exits (scheduler 4, runner 4), counts only the surviving workers as ended
and accounts the crashed coordinates as `uncompleted` with origin "crashed-slot". Then, and only then, the scheduler-exit,
runner-exit and those slots' missing-status alarms are not raised, and the job's units reconcile against its plan minus the
crashed coordinates. Nothing is credited; the charge stays; the coordinates return to the planner (not done, not in flight); a
slot-dispositioned job never qualifies a pilot.

REVISION 16 CANDIDATE (controls version 16; the owner's adoption of 17 Oct 2026 of Codex's resize design
reviews/2026-10-17_row19_resize_codex.md, RSC 08ce9e3, s.2-4 and s.6 item 4; NOT adopted). The refit planner only:
(a) DESIGNATED SET. Planning reads ONE pinned declaration, chpc/row19_screen_designated.json (its SHA-256 in the latest controls
version's files; a changed copy HOLDS), whose every value is recomputed from the manifest (designated_shape_problem):
S = {r in 3..102 : (r - 3) mod 5 in {0, 1, 2}} (60 reps, rep 83 included), indices 0..79, the provider split (the smallest 13 IDs
of S Lengau's, the largest 47 EC2-designated), the crash threshold 2 and the rescue route DISABLED. Nothing outside S x 0..79 is
ever planned again; records, claims, plans, ledger entries and statuses outside it are kept untouched (no deletion, no relabel)
and still count everywhere they counted (evidence, receipts, funding); they simply receive no new admission.
(b) REPLICATE-COMPLETE ORDER (designated_order). Ascending rep within S, ascending index within a rep: the remaining designated
indices of the earliest unfinished replicates fill a job first. Skipped: validated DONE, every still-owned live/planned
coordinate (in flight), crash-excluded coordinates, another provider's partition block. Never ordered by speed or success.
(c) PROVIDER SCOPE (lengau_scope). Lengau plans every designated coordinate of its 13 replicates, plus designated coordinates of
the 47 EC2-designated replicates that Lengau ALREADY claimed (any plan in any ledger state, row19_partition.lengau_claims): s.3
"All existing claims/completions retain Lengau provenance", s.4 "Let its declared owner finish/rescue it". Re-planning an
existing claim never grows the claim set on those replicates; their UNCLAIMED coordinates are left to the separate EC2
provider-epoch package and are never planned here. The epoch-1 partition (EC2 owns 160..199, now outside the set) stays pinned
and enforced unchanged, so the e1 activation proof stays valid.
(d) CRASH RULE (crash_history / crash_excluded). A coordinate with two crashed-worker slot dispositions (REVISION 14: SIGSEGV /
bus error / abort / illegal instruction, e.g. after LLVM "Cannot allocate memory") in the envelope the next ordinary attempt would
run in is never planned again by the ordinary planner: it is RESCUE-PENDING, printed by the dry run and the status view. The
counts come from the newest gate receipt's slot dispositions - the receipt receipt_problem recomputes exactly before any
admission; the admission refuses when a newer receipt replaced it between planning and the gate, and when a current HELD ledger
entry is not accounted as a disposition there. The separate rescue route (`--rescue`) is declared and DISABLED: no resources are
chosen, it always refuses. Running attempts are never touched.
(e) FIRST NEW-ORDER JOB ALONE (scaleup_problem). Plans carry `order` and `designated_sha256`. While no scale-up is adopted, a call
plans exactly one job and only when no new-order plan exists; `--adopt-scaleup reviews/<record>.md` writes
gate/scaleup_refit_v16.json (never overwritten) from a tracked, unmodified record carrying
`ADOPT row19-screen-v16-scaleup first_job=<n> job_id=<pbs id> plan=<sha256>` for that SETTLED first job.
(f) Unchanged: the 24-core x 48 h envelope (row19_screen_resources.json), the 4.5 GiB worker stop, reservation accounting, the
receipt/qualification/review gates, the funding and campaign-cap checks and the scheduler limits. The 81,000 core-h refit+S
sub-envelope is DECLARED in controls version 16 but binds only after the ledger's cap is raised through the two-phase
`--raise-cap 81000 --note ...` protocol at migration (chpc/migration_v16/RUNBOOK.md); until then the ledger's 60,000 binds.

REVISION 18 CANDIDATE (controls version 18; R052 20 Oct, refit job 54 7551259.sched01 lost with its node cnode0240; NOT adopted;
chpc/candidate_v18_nodefail/DESIGN_v18.md). NODE-FAILURE DISPOSITION: a receipt summary carrying `node_disposition` (kind
node-failure) is never taken on its word. node_disposition_problem() recomputes row19_screen_nodefail.node_failure_evidence (the
ONE implementation the status view calls; its docstring states conditions 1-5) from the CURRENT ledger, the root, the retained
verifier's units and the node evidence file on disk (<toolchain>/jobs/row19_screen_refit_<n>.nodefail.json, the bytes the
receipt bound in `bound.node_evidence`, written by the pinned capture script whose SHA-256 the latest controls version pins) and
requires the receipt's disposition EXACTLY equal; it also refuses when the job's PBS .out or .err file exists NOW (PBS staged the
job out after all: reclassify). The summary must be F with the kill-set exit, no runner exit, the completed slots ended 0 with
nothing left and the no-status slots' coordinates uncompleted with origin "node-failure"; units reconcile against the plan
minus those coordinates; the transition check re-reads the SETTLED certificate. crash_history reads slot dispositions only, so a
node failure never counts toward the two-crash rule; held_accounting_problem is unchanged (a node-failure job has no runner exit,
never HELD 4). A node-dispositioned job never qualifies a pilot. Nothing is credited; the charge stays.

REVISION 19 CANDIDATE (controls version 19; R052 lean T1 plan item 2, owner-approved 20 Oct 2026; NOT adopted;
chpc/candidate_v19_oploss/DESIGN_v19.md). OPERATIONAL-LOSS DISPOSITION, the general fallback after closed-no-record, crashed-slot
and node-failure: operational_loss_evidence() (ONE implementation, called by the status view and recomputed here) grants a
terminal refit job (state F) that is SETTLED with its certificate, whose settlement note's Exit_status is the observed exit, and
that is not clean (scheduler exit not 0/75, no runner end, or a runner exit not 0/75), when its evidence is consistent: every
present status is this job's slot, its planned assignment partitioned into new/resumed/left, and every unit naming the job at
its coordinates is in its `new`; the statuses scoped to the PBS id are exactly the planned present ones; a recorded runner exit
is the job-end code those statuses give (row19_shard.cmd_job_end's rule; otherwise a ledger inconsistency); no no-status slot's log
reports an exit; every no-status coordinate holds no temporary/non-canonical file and either nothing, a verified record of THIS
job in its planned slot whose current canonical artifacts are that evidence (salvaged: kept as this job's new), or a later bound
job's verified planned completion (R1); every timing naming the PBS id is canonical and a status's new or salvaged coordinate in
its planned slot. Granted: the summary carries `operational_loss`, completed statuses (0/75) are reconciled as ordinary workers,
crashed statuses (any other exit) keep their records and their `left` coordinates, the no-status coordinates (less salvaged)
are `uncompleted` with origin "operational-loss" and return to the planner, the charge stays. No evidence file is required. The
admission requires the receipt's disposition EXACTLY equal; an operational-loss job never qualifies a pilot and never counts
toward the crash rule (crash_history unchanged); held_accounting_problem accepts it for a HELD (runner exit 4) entry.
"""
import os, sys, json, time, glob, fcntl, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
from row19_ledger import CampaignLedger, LIVE
import programme_gate as PG
import re, math

ROLES = {"refit": "shard", "orig": "orig"}
REVIEW_SCHEMA = "row19-screen-review-1"
QUAL_SCHEMA = "row19-screen-qualification-1"
WATCH_SCHEMA = "row19-screen-watch-1"
CEILING_S = 2700.0
BOUND_KEYS = ("manifest_sha256", "root", "campaign", "code", "wrapper_sha256")
ACTIVATION_MODE = "canonical"            # REVISION 11 (Codex 3dc0daf R1-1): tests alone set "sandbox"


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def seeds_of(man):
    import simulate as S
    st = man["setting"]; kw = dict(st["grid"])
    return {int(r): int(S.dataset_seed(st["generator"], kw, int(r), int(st["D"]), int(man["datasets"]["seed_base"]))) for r in man["datasets"]["reps"]}


def seeds_sha256(seeds):
    return hashlib.sha256(json.dumps([[int(r), int(s)] for r, s in sorted(seeds.items())]).encode()).hexdigest()


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


CONTROLS_ADOPTION = "chpc/row19_screen_controls_adoption.json"


def controls_authority_problem():
    """C3: '' only when the controls file is the adopted, review-bound bytes."""
    import programme_gate as _PG
    return _PG.controls_authority_problem()


def controls():
    return json.load(open(os.path.join(HERE, "row19_screen_controls.json")))


def controls_problem():
    """'' when the controls file is adopted (C3) and every controller's bytes are the latest lineage version's."""
    why = controls_authority_problem()
    if why:
        return why
    v = controls()["versions"][-1]
    bad = [f for f, h in v["files"].items() if not os.path.exists(os.path.join(T1, f)) or sha_file(os.path.join(T1, f)) != h]
    return f"the controllers {bad} are not lineage version {v['version']}'s bytes" if bad else ""


def partition(man, manifest_path):
    """REVISION 10 (Codex f3dd3d7 contract 1): the provider partition named by the LATEST controls version, or None when that
    version names none. When named, the file must exist with the pinned sha256 and validate against this manifest
    (row19_partition.load); any failure raises, so the caller HOLDS rather than planning without the guard."""
    ref = controls()["versions"][-1].get("partition")
    if not ref:
        return None
    import row19_partition as RP
    pp = os.path.join(T1, ref["path"])
    if not os.path.exists(pp) or sha_file(pp) != ref["sha256"]:
        raise ValueError(f"the partition {ref['path']} is missing or not the pinned bytes {ref['sha256'][:12]}")
    return RP.load(pp, man, sha_file(manifest_path))


def partition_problem(jobs, part):
    """'' unless a planned refit slot names a coordinate the partition gives to another provider (planning AND admission
    check: also covers any plan supplied, restored or retried from elsewhere)."""
    if part is None:
        return ""
    import row19_partition as RP
    hits = [(int(s["rep"]), int(i)) for j in jobs for s in j["slots"] for i in s.get("indices", []) if RP.blocked(part, s["rep"], i)]
    return f"{len(hits)} planned coordinate(s) belong to the {part['provider']} partition epoch {part['epoch']}, e.g. {hits[:3]}" if hits else ""


def activation_problem_v10(man, manifest_path, part):
    """REVISION 10 (Codex RSC 0483db4 V10-1): while the latest controls pin a partition, Lengau refit admission requires that
    partition's serialized activation proof (row19_partition.py activate, written under this same plan lock)."""
    if part is None:
        return ""
    import row19_partition as RP
    ref = controls()["versions"][-1]["partition"]
    pp = os.path.join(man["storage"]["root"], "ec2", f"activation_e{int(part['epoch'])}.json")
    if not os.path.exists(pp):
        return f"partition epoch {part['epoch']} is pinned but not activated (row19_partition.py activate)"
    try:
        proof = json.load(open(pp))
    except Exception as e:
        return f"the activation proof is unreadable ({e})"
    return RP.activation_problem(man, sha_file(manifest_path), part, ref["sha256"], proof, controls=controls(), mode=ACTIVATION_MODE)


def ec2_receipt_problem(man, r):
    """REVISION 10 (Codex RSC 0483db4 V10-2): the receipt must bind EXACTLY the EC2 state of the live root as it is now
    (register, authority inventory, activations, HOLD, STOP): a newly journaled attempt or ingestion refuses until recollected,
    and a HOLD (sentinel/replay difference) refuses outright."""
    import row19_ec2_state as ES
    got = (r.get("ec2") or {}).get("bound") if isinstance(r.get("ec2"), dict) else None
    want = ES.bound(man["storage"]["root"])
    if got != want:
        return "its EC2 binding (register, inventory, activations, HOLD, STOP) is not the root's as it is now; recollect"
    if want["hold"]:
        return "an EC2 HOLD is in force (ec2/HOLD): a sentinel or replay difference awaits review"
    if (r.get("ec2") or {}).get("problems"):
        return f"the receipt's EC2 view has problems {r['ec2']['problems'][:3]}"
    # REVISION 11 (Codex 3dc0daf R1-3): the receipt binds metadata only; recheck the current registered canonical
    # record/timing/status bytes and the installed inventory now, under this admission's lock
    cur = ES.current_problems(man["storage"]["root"], man, require=bool(controls()["versions"][-1].get("partition")))
    if cur:
        return f"the current EC2 artifacts fail their registered contract: {cur[:3]}"
    return ""


def exclusion_contract(man):
    """The exclusion set the screen must declare EXACTLY: the slice manifest's historical list (that manifest pinned by the
    lineage file), the three development datasets' seeds recomputed, and the bank's seeds recomputed."""
    hm = controls()["history_manifest"]; hp = os.path.join(T1, hm["path"])
    if not os.path.exists(hp) or sha_file(hp) != hm["sha256"]:
        raise RuntimeError("the history manifest is absent or not the pinned bytes")
    hist = json.load(open(hp))
    dev = seeds_of(dict(hist, datasets=dict(hist["datasets"], reps=[0, 1, 2])))
    if sorted(dev.values()) != sorted(int(v) for v in hist["datasets"]["resolved_seeds"].values()):
        raise RuntimeError("the development seeds do not recompute")
    bp = os.path.join(T1, man["datasets"]["bank_manifest"]); bank = json.load(open(bp))
    return set(int(x) for x in hist["datasets"]["excluded_resolved_seeds"]) | set(dev.values()) | set(seeds_of(bank).values())


def seed_domain_problem(man):
    """'' when the declared screen seed domain is complete, unique, the declared one and disjoint from every exclusion and from
    the bank's seeds recomputed from the bank manifest named here."""
    reps = [int(r) for r in man["datasets"]["reps"]]
    if len(reps) != int(man["datasets"].get("n_attempted", -1)) or len(set(reps)) != len(reps):
        return f"the declared reps are not exactly {man['datasets'].get('n_attempted')} distinct ids"
    seeds = seeds_of(man)
    if len(set(seeds.values())) != len(seeds):
        return "two screen datasets resolve to the same seed"
    if seeds_sha256(seeds) != man["datasets"].get("resolved_seeds_sha256"):
        return "the recomputed screen seed list is not the declared one"
    excl = {int(x) for x in man["datasets"].get("excluded_resolved_seeds", [])}
    if not excl:
        return "the excluded seed set is empty"
    if set(seeds.values()) & excl:
        return "a screen seed is in the excluded set"
    bp = os.path.join(T1, man["datasets"]["bank_manifest"])
    if not os.path.exists(bp) or sha_file(bp) != man["datasets"]["bank_manifest_sha256"]:
        return "the bank manifest named by the screen is absent or not the declared bytes"
    bank = json.load(open(bp)); bseeds = seeds_of(bank)
    if seeds_sha256(bseeds) != bank["datasets"].get("resolved_seeds_sha256") or len(bseeds) != len(bank["datasets"]["reps"]) or not bseeds:
        return "the bank's seed domain does not recompute to its declared list"
    if set(seeds.values()) & set(bseeds.values()):
        return "a screen seed is a bank seed"
    idents = man["datasets"].get("identities", {})
    if sorted(int(k) for k in idents) != sorted(reps) or any(not isinstance(v, str) or len(v) != 64 for v in idents.values()):
        return "the declared identity map is not complete for every screen rep"
    try:
        want = exclusion_contract(man)
    except RuntimeError as e:
        return f"the exclusion contract cannot be reconstructed: {e}"
    if excl != want:
        return f"the declared exclusions ({len(excl)}) are not exactly the contract ({len(want)}: historical, development, bank)"
    return ""


def identity_problem(man, reps):
    import row19_shard as SH
    for r in reps:
        t = SH.task(man, r)
        if man["datasets"]["identities"].get(str(r)) != t["ident"]:
            return f"rep {r}: this runtime computes identity {t['ident'][:16]}, the manifest declares {str(man['datasets']['identities'].get(str(r)))[:16]}"
    return ""


def _strict_load(p):
    def bad(x):
        raise ValueError(f"non-finite constant {x}")
    return json.loads(open(p).read(), parse_constant=bad)


def _durable_write(p, obj):
    tmp = f"{p}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, p)
    d = os.open(os.path.dirname(os.path.abspath(p)), os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def _phases(man):
    """The validated phase list; raises ValueError on anything malformed."""
    b = _strict_load(_phases_path(man))
    ph = b.get("phases")
    if not isinstance(ph, list) or not ph:
        raise ValueError("no phases")
    for k, x in enumerate(ph):
        if not (_num(x.get("cap_core_h")) and x["cap_core_h"] > 0):
            raise ValueError(f"phase {k}: the cap is not finite and positive")
        for f in ("pending", "retired"):
            if f in x and not isinstance(x[f], bool):
                raise ValueError(f"phase {k}: `{f}` is not a boolean")
        if k > 0 and x.get("campaign") != man["storage"]["campaign"]:
            raise ValueError(f"phase {k}: names another campaign")
    return b


def _phases_path(man):
    a = man["budget"]["admission"]
    return a if os.path.isabs(a) else os.path.join(T1, a)


def cap_problem(man):
    """'' when the ledger's cap is the latest COMMITTED budget phase; an interrupted amendment is reconciled when the ledger
    already carries the pending phase's cap, and refused otherwise (nothing is admitted over an unreconciled cap)."""
    camp = man["storage"]["campaign"]; lp = os.path.join(camp, "budget.json")
    if not os.path.exists(lp):
        return ""
    try:
        b = _phases(man); led = _strict_load(lp)
    except (ValueError, OSError) as e:
        return f"the budget phases or the ledger are malformed ({e})"
    cap = led.get("cap_core_h")
    if not (_num(cap) and cap > 0):
        return "the ledger's cap is not finite and positive"
    live = [x for x in b["phases"] if not x.get("retired")]
    last = live[-1]
    hist = led.get("cap_history") or []
    if last.get("pending"):
        if abs(cap - float(last["cap_core_h"])) < 1e-9 and predecessor_problem(man, live, applied_ok=True, applied_only=True) == "":
            last["pending"] = False; last["reconciled"] = time.time(); _durable_write(_phases_path(man), b)
            return ""
        return (f"an interrupted cap amendment to {last['cap_core_h']} is pending while the ledger holds {cap}; resume it with "
                f"--raise-cap {last['cap_core_h']} --note ... or retire it with --retire-pending --note ...")
    if abs(cap - float(last["cap_core_h"])) > 1e-9:
        return f"the ledger's cap {cap} is not the latest budget phase's {last['cap_core_h']}"
    if len(live) > 1 and not (hist and abs(float(hist[-1].get("new", -1)) - cap) < 1e-9):
        return "the ledger's cap_history does not record the latest phase's raise"
    return ""


def predecessor_problem(man, live, applied_ok, applied_only=False):
    """C4: '' when the ledger still certifies the preceding COMMITTED phase (cap and latest history entry, or no history for the
    first phase) - or, with applied_ok, when it already shows exactly the pending raise from that predecessor."""
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    cap = led.get("cap_core_h"); hist = led.get("cap_history") or []
    prev = [x for x in live[:-1] if not x.get("pending")]
    if not prev:
        return "no committed phase precedes the pending one"
    pc, pend = float(prev[-1]["cap_core_h"]), float(live[-1]["cap_core_h"])
    first = len(prev) == 1
    hist_ok_prev = (not hist) if first else (bool(hist) and _num(hist[-1].get("new")) and abs(hist[-1]["new"] - pc) < 1e-9)
    if not applied_only and _num(cap) and abs(cap - pc) < 1e-9 and hist_ok_prev:
        return ""
    if applied_ok and _num(cap) and abs(cap - pend) < 1e-9 and hist and _num(hist[-1].get("new")) and abs(hist[-1]["new"] - pend) < 1e-9 \
            and _num(hist[-1].get("old")) and abs(hist[-1]["old"] - pc) < 1e-9:
        return ""
    return (f"the ledger (cap {cap}, latest history {hist[-1] if hist else None}) does not certify the preceding committed phase "
            f"{pc}{' or exactly the pending raise ' + str(pend) if applied_ok else ''}")


def ledger_for(man):
    """The campaign ledger, created at the initial budget phase when absent, otherwise read at its own (possibly raised) cap."""
    camp = man["storage"]["campaign"]
    if os.path.exists(os.path.join(camp, "budget.json")):
        return CampaignLedger(camp, None)
    phases = json.load(open(_phases_path(man)))["phases"]
    return CampaignLedger(camp, float(phases[0]["cap_core_h"]))


def funding_problem(man, proposed_core_h):
    """REVISION 2: the programme gate's strict count (call it inside programme_lock)."""
    return PG.funding_problem(PG.programme_funding(man), proposed_core_h)


def _funding_problem_v1(man, proposed_core_h):
    """Revision 1's unlocked count, kept for the record; not called."""
    f = man["funding"]; total = float(f.get("other_settled_core_h", 0.0)); seen = []
    for camp in f["campaigns"]:
        p = os.path.join(camp, "budget.json")
        if not os.path.exists(p):
            seen.append(f"{os.path.basename(camp)} 0"); continue
        try:
            led = json.load(open(p))
        except Exception as e:
            return f"the ledger of {camp} is unreadable ({e}); funding cannot be established"
        s = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values() if e.get("state") == "settled")
        l = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
        total += s + l; seen.append(f"{os.path.basename(camp)} {s + l:.0f}")
    if total + proposed_core_h > float(f["allocation_core_h"]) + 1e-9:
        return (f"funding: {total:.0f} committed ({', '.join(seen)}) + {proposed_core_h:.0f} proposed > the {f['programme']} "
                f"allocation of {f['allocation_core_h']:.0f}")
    return ""


def evidence(man, role, validate=True):
    root = man["storage"]["root"]; reps = [int(r) for r in man["datasets"]["reps"]]
    problems = []; done = set()
    if role == "refit":
        import row19_shard as SH
        B = int(man["cfg"]["n_boot_refit"])
        for d in glob.glob(os.path.join(root, "records", "rep*")):
            r = os.path.basename(d)[3:]
            if not r.isdigit() or int(r) not in reps:
                problems.append(f"{d}: records of an undeclared rep"); continue
            r = int(r); t = SH.task(man, r) if validate else None
            for p in sorted(glob.glob(os.path.join(d, "rec_*.json"))):
                name = os.path.basename(p)
                try:
                    i = int(name[4:7])
                    if name != f"rec_{i:03d}.json" or not 0 <= i < B:
                        raise ValueError
                except ValueError:
                    problems.append(f"{p}: not a record file name"); continue
                if validate:
                    try:
                        SH.read_record(p, t, i)
                    except ValueError as e:
                        problems.append(str(e)); continue
                done.add((r, i))
    else:
        import row19_screen_orig as O
        files = glob.glob(os.path.join(root, "orig", "orig_*.json"))
        by_prefix = {man["datasets"]["identities"][str(r)][:24]: r for r in reps}
        for p in files:
            pre = os.path.basename(p)[5:-5]
            if pre not in by_prefix:
                problems.append(f"{p}: a cache of no declared identity"); continue
            r = by_prefix[pre]
            if validate:
                try:
                    got, _ = O.read_cache(root, O.task_checked(man, r))
                except ValueError as e:
                    problems.append(str(e)); continue
            done.add(r)
    led = os.path.join(man["storage"]["campaign"], "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    flight, used = set(), set()
    for e in entries:
        if e.get("kind") != ROLES[role]:
            continue
        used.add(int(e["rep"]))
        if e.get("state") in LIVE and e.get("runner_exit") is None:
            pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
            if not os.path.exists(pp):
                problems.append(f"{role} job {e['rep']} ({e.get('job_id')}) is live but its plan is missing"); continue
            for s in json.load(open(pp)).get("slots", []):
                if role == "refit":
                    flight.update((int(s["rep"]), int(i)) for i in s["indices"])
                else:
                    flight.update(int(r) for r in s["reps"])
    return done, flight, used, problems


def plan_jobs(man, role, n_jobs, done, flight, used, part=None, order=None):
    """REVISION 16: the refit role plans ONLY from `order`, the designated replicate-complete order (designated_order: S x 0..79
    within Lengau's scope, done / in flight / crash-excluded / another provider's block skipped). Revision 15's index-major
    round robin over all 100 reps and all B indices is retired; without an order the refit planner refuses."""
    cores = int(man["pbs"]["cores"]); reps = [int(r) for r in man["datasets"]["reps"]]
    if role == "refit":
        if order is None:
            raise ValueError("REVISION 16: refit planning needs the designated replicate-complete order")
        order = list(order)
    else:
        order = [r for r in reps if r not in done and r not in flight]
    jobs, n = [], (max(used) + 1 if used else 1)
    for k in range(0, len(order), cores):
        if len(jobs) >= n_jobs:
            break
        chunk = order[k:k + cores]
        if role == "refit":
            jobs.append({"job": n, "slots": [{"slot": s, "rep": r, "indices": idx} for s, (r, idx) in enumerate(chunk)]})
        else:
            jobs.append({"job": n, "slots": [{"slot": s, "reps": [r]} for s, r in enumerate(chunk)]})
        n += 1
    return jobs, len(order) - sum(len(j["slots"]) for j in jobs)


def planned_reps(job):
    return sorted({int(s["rep"]) for s in job["slots"]} if "rep" in job["slots"][0] else {int(r) for s in job["slots"] for r in s["reps"]})


def expected_bound(man, manifest_path, role):
    root, campaign = man["storage"]["root"], man["storage"]["campaign"]
    led = json.load(open(os.path.join(campaign, "budget.json")))
    jobs = {}
    for e in led["entries"].values():
        if e.get("kind") != ROLES[role]:
            continue
        n = str(int(e["rep"])); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[n] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
    bindings = {}
    if role == "refit":
        for p in sorted(glob.glob(os.path.join(root, "task_*.json"))):
            bindings[os.path.basename(p)[5:-5]] = sha_file(p)
    return dict(manifest_sha256=sha_file(manifest_path), root=root, campaign=campaign, code=dict(man["code"]["files"]),
                wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"), jobs=jobs, bindings=bindings)


def bound_problem(got, want, jobs):
    if not isinstance(got, dict):
        return "no `bound` object"
    for k in BOUND_KEYS:
        if got.get(k) != want[k]:
            return f"its `{k}` is not this campaign's"
    if not isinstance(got.get("jobs"), dict):
        return "no job bindings"
    if jobs == "all":
        if got["jobs"] != want["jobs"]:
            return f"its jobs {sorted(got['jobs'])} are not the ledger's {sorted(want['jobs'])} as they are now"
    else:
        for n in jobs:
            w = want["jobs"].get(n)
            if not w or None in w.values() or got["jobs"].get(n) != w:
                return f"its binding of job {n} is not the ledger's and the root's"
    if (got.get("bindings") or {}) != want["bindings"]:
        return "its task bindings are not exactly the root's (every started task, no subset, no extra)"
    if not isinstance(got.get("anchors_sha256"), str) or len(got["anchors_sha256"]) != 64:
        return "no anchor verdict digest is bound"
    return ""


def anchors_problem(verdict, digest):
    """The EMBEDDED anchor verdict must hash to the bound digest and show index 0 equal on all three anchors with nothing
    differing, missing, invalid or conflicting."""
    if not isinstance(verdict, dict):
        return "no anchor verdict is embedded"
    if hashlib.sha256(json.dumps(verdict, sort_keys=True).encode()).hexdigest() != digest:
        return "the embedded anchor verdict is not the bound one"
    reps = verdict.get("reps") or {}
    if verdict.get("problem") or sorted(reps) != ["0", "1", "2"]:
        return "the anchor verdict does not cover the three development anchors cleanly"
    for r, e in reps.items():
        if 0 not in (e.get("equal") or []) or e.get("differ") or e.get("missing") or e.get("invalid") or e.get("conflict"):
            return f"anchor {r} is not equal at index 0 with nothing differing, missing, invalid or conflicting"
    return ""


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


RESOURCES = "chpc/row19_screen_resources.json"
RES_SCHEMA = "row19-screen-resources-1"
SERIAL_MAX_WALLTIME_H = 48.0
ENV_FIXED = ("queue", "cores", "mem_gb", "nodetype", "deadline_reserve_s")
DISPO_KIND = "closed-no-record"


def manifest_envelope(man):
    """The frozen manifest's request (every originals job, and refit jobs below the policy's first job)."""
    p = man["pbs"]
    return dict(queue=p["queue"], cores=int(p["cores"]), walltime_s=float(p["walltime_h"]) * 3600.0, mem_gb=int(p["mem_gb"]),
                nodetype=p["nodetype"], deadline_reserve_s=int(float(p["deadline_reserve_s"])), source="manifest")


def envelope_core_h(env):
    return env["cores"] * env["walltime_s"] / 3600.0


def resources_shape_problem(doc):
    """The policy's own structure (independent of any manifest)."""
    if not isinstance(doc, dict) or doc.get("schema") != RES_SCHEMA or doc.get("role") != "refit":
        return "it has another schema or role"
    if not _hex64(doc.get("manifest_sha256")):
        return "it names no manifest SHA-256"
    envs = doc.get("envelopes")
    if not isinstance(envs, list) or not envs:
        return "it has no envelopes"
    prev = 1
    for k, x in enumerate(envs):
        if not isinstance(x, dict) or set(x) - set(ENV_FIXED) - {"first_job", "walltime_h", "per_slot", "note"}:
            return f"envelope {k} is not an object of the declared fields"
        if not (_int(x.get("first_job")) and x["first_job"] > prev):
            return f"envelope {k}: first_job must be an integer above {prev}"
        prev = x["first_job"]
        if not (_num(x.get("walltime_h")) and 0 < x["walltime_h"] <= SERIAL_MAX_WALLTIME_H):
            return f"envelope {k}: walltime_h must be finite, positive and at most {SERIAL_MAX_WALLTIME_H:.0f}"
        if not (_int(x.get("per_slot")) and x["per_slot"] == 1):
            return f"envelope {k}: one index per worker (per_slot 1) is required"
        if not (_int(x.get("deadline_reserve_s")) and 0 < x["deadline_reserve_s"] < x["walltime_h"] * 3600.0):
            return f"envelope {k}: the deadline reserve is not a positive integer below the walltime"
    return ""


def resolve_envelope(man, manifest_path, role, n):
    """(envelope, problem) of job n. Originals: the manifest. Refit: the pinned policy (its bytes must be the latest lineage
    version's pin, its shape valid); below its first job the manifest; from it on the policy's walltime, and then the policy must
    name THIS manifest and every other field must equal the manifest's (a walltime-only change)."""
    base = manifest_envelope(man)
    if role != "refit":
        return base, ""
    p = os.path.join(T1, RESOURCES)
    pin = controls()["versions"][-1]["files"].get(RESOURCES)
    if not _hex64(pin):
        return None, "the controls lineage does not pin the resource policy"
    if not os.path.exists(p) or sha_file(p) != pin:
        return None, "the resource policy is absent or not the lineage's pinned bytes"
    try:
        doc = _strict_load(p)
    except (OSError, ValueError) as e:
        return None, f"the resource policy is unreadable ({e})"
    why = resources_shape_problem(doc)
    if why:
        return None, f"the resource policy: {why}"
    hit = [x for x in doc["envelopes"] if int(n) >= x["first_job"]]
    if not hit:
        return base, ""
    x = hit[-1]
    if doc["manifest_sha256"] != sha_file(manifest_path):
        return None, "the resource policy names another manifest"
    for f in ENV_FIXED:
        if isinstance(x.get(f), bool) or x.get(f) != base[f]:
            return None, f"the resource policy's {f} {x.get(f)!r} is not the manifest's {base[f]!r} (walltime-only policy)"
    if int((man.get("shard") or {}).get("per_slot", 0)) != 1:
        return None, "the manifest does not run one index per worker"
    return dict(base, walltime_s=float(x["walltime_h"]) * 3600.0, source=f"{RESOURCES} first_job={x['first_job']}", resources_sha256=pin), ""


def policy_first_job(role):
    """The smallest job number the pinned policy governs (None for originals). Fails closed: a policy that is absent, unpinned,
    not the pinned bytes or malformed returns 1, so every receipt job is checked and resolve_envelope refuses it."""
    if role != "refit":
        return None
    try:
        p = os.path.join(T1, RESOURCES); pin = controls()["versions"][-1]["files"].get(RESOURCES)
        if not _hex64(pin) or sha_file(p) != pin:
            return 1
        doc = _strict_load(p)
        return 1 if resources_shape_problem(doc) else min(int(x["first_job"]) for x in doc["envelopes"])
    except Exception:
        return 1


def pbs_request_problem(script, env):
    """The filled PBS request and the job-start / deadline arguments must be exactly the resolved envelope."""
    w, r = int(round(env["walltime_s"])), int(env["deadline_reserve_s"])
    need = [f"#PBS -q {env['queue']}\n", f"#PBS -l walltime={hms(w)}\n",
            f"#PBS -l select=1:ncpus={env['cores']}:mpiprocs={env['cores']}:mem={env['mem_gb']}gb:nodetype={env['nodetype']}\n",
            f"DEADLINE=$((START + {w} - {r}))\n", f" --walltime-s {w} "]
    miss = [x.strip() for x in need if x not in script]
    if miss:
        return f"the PBS script does not carry the resolved envelope: {miss}"
    if script.count("walltime=") != 1 or script.count("--walltime-s ") != 1 or script.count("DEADLINE=") != 1:
        return "the PBS script requests or passes the walltime more than once"
    return ""


def envelope_problem(man, manifest_path, role, n, plan, entry, sj=None):
    """REVISION 8 (2): one job's plan, CURRENT ledger entry and (optionally) receipt summary against its resolved envelope."""
    env, why = resolve_envelope(man, manifest_path, role, int(n))
    if why:
        return f"job {n}: {why}"
    w = env["walltime_s"]
    if not isinstance(plan, dict) or plan.get("job") != int(n):
        return f"job {n}: no plan of this job"
    if not (_num(plan.get("walltime_s")) and abs(plan["walltime_s"] - w) < 1e-6) or plan.get("queue") != env["queue"]:
        return f"job {n}: the plan's request ({plan.get('queue')}, {plan.get('walltime_s')} s) is not the resolved envelope ({env['queue']}, {w:.0f} s)"
    if env["source"] != "manifest" and plan.get("envelope") != env:
        return f"job {n}: the plan does not carry the resolved envelope"
    if len(plan.get("slots") or []) > env["cores"] or (role == "refit" and any(len(sl.get("indices") or []) != 1 for sl in plan.get("slots") or [])):
        return f"job {n}: the plan is not at most {env['cores']} workers of one index each"
    if not isinstance(entry, dict) or entry.get("token") != plan.get("token") or not _int(entry.get("cores")) or entry["cores"] != env["cores"] \
            or not (_num(entry.get("walltime_s")) and abs(entry["walltime_s"] - w) < 1e-6) \
            or not (_num(entry.get("reserved_core_h")) and abs(entry["reserved_core_h"] - envelope_core_h(env)) < 1e-6
                    and abs(entry["reserved_core_h"] - entry["cores"] * entry["walltime_s"] / 3600.0) < 1e-6):                    # R3: no truncation
        return f"job {n}: the ledger reservation is not {env['cores']} x {w:.0f} s = {envelope_core_h(env):.0f} core-hours under the plan's token"
    if sj is not None and env["source"] != "manifest":
        if not (_num(sj.get("plan_walltime_s")) and abs(sj["plan_walltime_s"] - w) < 1e-6):
            return f"job {n}: the receipt's plan walltime {sj.get('plan_walltime_s')} is not the envelope's {w:.0f} s"
        unobserved = sj.get("operational_loss") is not None and sj.get("requested_walltime_s") is None   # REVISION 19: PBS history
        if not unobserved and not (_num(sj.get("requested_walltime_s")) and abs(sj["requested_walltime_s"] - w) <= 1.0):  # expired
            return f"job {n}: the scheduler's observed walltime request {sj.get('requested_walltime_s')} is not the envelope's {w:.0f} s"
    return ""


def receipt_envelope_problem(man, manifest_path, role, r):
    """Every receipt job the policy governs, against its plan and CURRENT ledger entry (earlier jobs keep their v7 checks)."""
    fj = policy_first_job(role)
    if fj is None:
        return ""
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    by_n = {str(int(e["rep"])): e for e in led["entries"].values() if e.get("kind") == ROLES[role]}
    for n, sj in (r.get("jobs") or {}).items():
        if int(n) < fj:
            continue
        pp = os.path.join(man["storage"]["root"], "plans", f"job_{int(n)}.json")
        try:
            plan = _strict_load(pp)
        except (OSError, ValueError):
            return f"job {n}: its plan is absent or unreadable"
        why = envelope_problem(man, manifest_path, role, n, plan, by_n.get(str(int(n))), sj if isinstance(sj, dict) else {})
        if why:
            return why
    return ""


def job_output_path(man, role, n):
    return os.path.join(man["shard"]["toolchain"], "jobs", f"row19_screen_{role}_{int(n)}.out")


STATUS_NAME = re.compile(r"^job(.+)\.slot([0-9]+)\.json$")


def status_scoped(root, jid):
    """Status files scoped to PBS job jid: by name (any slot, planned or not), by parsed `job`, or unreadable with no job name."""
    hits = []
    for p in sorted(glob.glob(os.path.join(root, "status", "*"))):
        b = os.path.basename(p)
        if b.startswith(f"job{jid}."):
            hits.append(b); continue
        try:
            d = _strict_load(p)
        except Exception:
            if not STATUS_NAME.match(b):
                hits.append(f"{b} (unreadable, no job named)")
            continue
        if not isinstance(d, dict) or d.get("job") == jid:
            hits.append(b)
    return hits


def timing_scan(root, jid):
    """Timing files anywhere under the root that name jid, cannot be read, or are not a published .json (a temporary file)."""
    hits = []
    for p in sorted(glob.glob(os.path.join(root, "timing", "**", "*"), recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, root)
        if not p.endswith(".json"):
            hits.append(f"{rel} (not a published timing)"); continue
        try:
            d = _strict_load(p)
        except Exception:
            hits.append(f"{rel} (unreadable)"); continue
        if not isinstance(d, dict) or d.get("job") == jid:
            hits.append(rel)
    return hits


def coordinate_files(man, root, role, k):
    """Every file - exact or temporary - that could carry output for coordinate k: its record and its timing."""
    if role == "refit":
        r, i = (int(x) for x in k.split("/"))
        pats = [os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json*"), os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json*")]
        exact = {f"rec_{i:03d}.json", f"t_{i:03d}.json"}
    else:
        r = int(k); pre = man["datasets"]["identities"][str(r)][:24]
        pats = [os.path.join(root, "orig", f"orig_{pre}.json*"), os.path.join(root, "timing", f"o{r:03d}.json*")]
        exact = {f"orig_{pre}.json", f"o{r:03d}.json"}
    files = sorted(p for pat in pats for p in glob.glob(pat))
    return files, [p for p in files if os.path.basename(p) not in exact]


TIMING_MEASURES = ("wall_s", "fit_seconds", "maxrss", "t")        # row19_screen_verify.timing_ok (verify.py:93-105), unchanged


def current_artifacts_problem(man, root, role, k, u):
    """R1 (Codex 5cb9a02): the CURRENT canonical record and timing files of coordinate k must be the retained verified evidence -
    the timing's coordinate, declared identity, producer job and integer slot, and the record's checksum (refit `sha`, originals
    `payload_sha`). An absent, unreadable or changed artifact refuses until the evidence is recollected."""
    t = (u or {}).get("timing") or {}; rec = (u or {}).get("record") or {}
    if role == "refit":
        r, i = (int(x) for x in k.split("/"))
        rp_ = os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"); tp_ = os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json")
        rkey, want_t = "sha", dict(rep=r, index=i)
    else:
        r = int(k); pre = man["datasets"]["identities"][str(r)][:24]
        rp_ = os.path.join(root, "orig", f"orig_{pre}.json"); tp_ = os.path.join(root, "timing", f"o{r:03d}.json")
        rkey, want_t = "payload_sha", dict(rep=r)
    ident = man["datasets"]["identities"].get(str(r))
    try:
        ct = _strict_load(tp_)
    except Exception:
        return "its current timing is absent or unreadable"
    if not isinstance(ct, dict) or any(ct.get(a) != b or isinstance(ct.get(a), bool) for a, b in want_t.items()) or ct.get("ident") != ident:
        return "its current timing is not this coordinate's under the declared identity"
    if ct.get("job") != t.get("job") or not _int(ct.get("slot")) or ct["slot"] != t.get("slot"):
        return f"its current timing names {ct.get('job')} slot {ct.get('slot')}, not the verified producer {t.get('job')} slot {t.get('slot')}"
    bad = [f for f in TIMING_MEASURES if not (_num(ct.get(f)) and ct[f] >= 0)]
    if bad:                                                           # R1 (ce06828): row19_screen_verify.timing_ok's measurement contract
        return f"its current timing's {bad} are not finite non-negative non-boolean numbers (the verifier's timing contract)"
    try:
        cr = _strict_load(rp_)
    except Exception:
        return "its current record is absent or unreadable"
    want_r = rec.get(rkey)
    if not isinstance(want_r, str) or not want_r or not isinstance(cr, dict) or cr.get(rkey) != want_r:
        return "its current record is not the verified record"
    if role == "refit" and (cr.get("rep") != i or isinstance(cr.get("rep"), bool) or cr.get("ident") != ident):
        return "its current record is not this coordinate's under the declared identity"
    return ""


def later_completion(man, root, role, units, k, n, num_of, plan_slot_of):
    """'' when coordinate k holds a valid record whose valid timing names a bound job LATER than n that planned k in that slot,
    AND its current canonical artifacts are that verified evidence (R1); otherwise the reason."""
    u = units.get(k) or {}; t = u.get("timing") or {}
    if not ((u.get("record") or {}).get("ok") and t.get("ok") is True and _int(t.get("slot"))):
        return "no valid verified record with valid timing"
    m = num_of.get(t.get("job"))
    if m is None or m <= int(n) or plan_slot_of(m).get(k) != t["slot"]:
        return f"the verified producer {t.get('job')} slot {t.get('slot')} is not a later bound job that planned it there"
    return current_artifacts_problem(man, root, role, k, u)


CERT_FIELDS = ("settled_core_h", "settle_note", "settled_at", "token", "job_id")


def certificate_problem(d, e):
    """R2 (Codex 5cb9a02): the settlement certificate the status view observed (charge, note, non-negative time, token, PBS id)
    must be EXACTLY the current ledger entry's; any replacement refuses until recollected. The charged loss is never rewritten."""
    if not (_num(d.get("settled_at")) and d["settled_at"] >= 0) or not (_num(d.get("settled_core_h")) and d["settled_core_h"] >= 0) \
            or not (isinstance(d.get("settle_note"), str) and len(d["settle_note"].strip()) >= 8):
        return "the receipt binds no valid settlement certificate (charge, note, non-negative time)"
    diff = [f for f in CERT_FIELDS if d.get(f) != e.get(f) or isinstance(d.get(f), bool)]
    if diff:
        return f"the current ledger's settlement certificate differs from the receipt's on {diff}; recollect"
    return ""


def disposition_problem(man, manifest_path, role, n, sj, bound, units):
    """REVISION 8 (1): '' only when job n is a CLOSED, SETTLED, NO-RECORD job, recomputed here from the current ledger, the root
    and the PBS output on disk (never the summary's word)."""
    n = str(int(n)); d = sj.get("disposition") if isinstance(sj, dict) else None
    if not isinstance(d, dict) or d.get("kind") != DISPO_KIND:
        return f"job {n}: no closed-no-record disposition"
    jid = sj.get("job_id")
    if sj.get("state") != "F" or not _int(sj.get("exit")) or d.get("scheduler_exit") != sj.get("exit"):
        return f"job {n}: the disposition is not a successful terminal scheduler observation (state F with its observed integer exit)"
    if not (_num(sj.get("mem_kb")) and sj["mem_kb"] >= 0):
        return f"job {n}: the disposed job has no finite observed scheduler memory"
    want = plan_slots(man, n)
    if not (_int(sj.get("slots")) and sj["slots"] == want and all(_int(sj.get(x)) and sj[x] == 0 for x in ("ended", "new", "resumed", "left"))
            and sj.get("exits") == {} and sj.get("runner_exit") is None and sj.get("max_worker_maxrss") is None):
        return f"job {n}: the summary is not a closed job with no worker status, no outcome and no runner end"
    lp = os.path.join(man["storage"]["campaign"], "budget.json")
    led = _strict_load(lp)
    hits = [e for e in led["entries"].values() if e.get("kind") == ROLES[role] and e.get("rep") == int(n)]
    if len(hits) != 1:
        return f"job {n}: {len(hits)} current ledger entries"
    e = hits[0]
    if e.get("state") != "settled" or not (_num(e.get("settled_core_h")) and e["settled_core_h"] >= 0) \
            or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8) or not (_num(e.get("settled_at")) and e["settled_at"] >= 0):
        return f"job {n}: the CURRENT ledger entry is not SETTLED with settlement evidence (charge, note, non-negative time)"
    if not (_num(d.get("settled_core_h")) and abs(d["settled_core_h"] - e["settled_core_h"]) < 1e-9):
        return f"job {n}: the disposition's charge {d.get('settled_core_h')} is not the ledger's {e['settled_core_h']}"
    why = certificate_problem(d, e)                                                    # R2: the exact observed certificate
    if why:
        return f"job {n}: {why}"
    if any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")):
        return f"job {n}: the ledger records a runner end; it is not a closed-no-record job"
    bj = (bound.get("jobs") or {}).get(n) or {}
    if not jid or e.get("job_id") != jid or bj.get("job_id") != jid or bj.get("token") != e.get("token"):
        return f"job {n}: the PBS id or token is not the ledger's"
    pp = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    try:
        plan = _strict_load(pp)
    except (OSError, ValueError):
        return f"job {n}: its plan is absent or unreadable"
    if plan.get("token") != e.get("token") or plan.get("job") != int(n) or sha_file(pp) != bj.get("plan_sha256") or d.get("plan_sha256") != bj.get("plan_sha256"):
        return f"job {n}: the plan is not the bound plan of this token and job"
    slot_of = _plan_slot_of(man, n)
    part = sj.get("partition")
    if not isinstance(part, dict) or part.get("new") != [] or part.get("resumed") != [] or part.get("left") != [] \
            or part.get("uncompleted") != sorted(slot_of) or part.get("uncompleted_origin") != "plan":
        return f"job {n}: the disposed plan's coordinates are not accounted as uncompleted with their plan-derived origin"
    root = man["storage"]["root"]
    sc = status_scoped(root, jid)
    if sc:
        return f"job {n}: status evidence scoped to {jid} ({sc[:3]}); not a closed-no-record job"
    named = sorted(k for k, u in units.items() if ((u or {}).get("timing") or {}).get("job") == jid)
    if named:
        return f"job {n}: unit(s) {named[:3]} carry timing naming {jid}"
    ts = timing_scan(root, jid)
    if ts:
        return f"job {n}: timing evidence naming {jid} or of unknown attribution ({ts[:3]})"
    num_of = {x.get("job_id"): int(x["rep"]) for x in led["entries"].values() if x.get("kind") == ROLES[role] and x.get("job_id")}
    plans = {}

    def pso(m):
        if m not in plans:
            plans[m] = _plan_slot_of(man, m)
        return plans[m]
    for k in sorted(slot_of):
        files, odd = coordinate_files(man, root, role, k)
        if odd:
            return f"job {n}: coordinate {k} has temporary or non-canonical output files {[os.path.basename(p) for p in odd][:3]}"
        if files or (units.get(k) or {}).get("record") is not None:
            why = later_completion(man, root, role, units, k, n, num_of, pso)
            if why:
                return f"job {n}: coordinate {k} holds output that is not a later bound job's planned completion ({why})"
    ob = (bound.get("job_outputs") or {}).get(n) or {}
    op = job_output_path(man, role, n)
    if ob.get("file") != os.path.basename(op) or not _hex64(ob.get("sha256")) or ob["sha256"] != d.get("output_sha256"):
        return f"job {n}: the receipt binds no PBS output for the disposed job"
    try:
        b = open(op, "rb").read()
    except OSError as ex:
        return f"job {n}: the PBS output {op} is absent or unreadable ({ex}); absence of an admission failure is not proven"
    if hashlib.sha256(b).hexdigest() != ob["sha256"]:
        return f"job {n}: the PBS output is not the bytes the receipt bound; recollect"
    txt = b.decode("utf-8", errors="replace")
    if "ADMISSION FAILED" in txt:
        return f"job {n}: the PBS output reports ADMISSION FAILED"
    if f"job {jid}" not in txt:
        return f"job {n}: the PBS output does not name {jid}"
    return ""


CRASH_KIND = "crashed-worker-no-status"
HELD_EXIT = 4                                                   # row19_shard.HELD: the job-end code when a worker has no 0/75 status
SIGNAL_DEATHS = ("Segmentation fault", "Bus error", "Aborted", "Illegal instruction")   # bash's report of a worker killed by its OWN fault
_SIG_RE = "|".join(re.escape(s) for s in SIGNAL_DEATHS)


PBS_SPOOL = "/var/spool/PBS/mom_priv/jobs"


def crash_line_re(jid, sl, lustre_root):
    """The bash job-control line PBS's stderr carries when THIS planned worker died of a fatal signal: refit_pbs_script's exact
    worker command for this plan slot - the job script in PBS's spool named by the PBS id, the screen manifest (chpc/
    row19_screen_manifest.json, relative to the job clone), the slot's rep/indices/slot and its log under the campaign root."""
    idx = ",".join(str(int(i)) for i in sl["indices"])
    return re.compile(rf"^{re.escape(PBS_SPOOL)}/{re.escape(jid)}\.SC: line \d+: +\d+ ({_SIG_RE})(?: \(core dumped\))? +\$T/t1py chpc/row19_shard\.py worker "
                      rf"--manifest (?:[^ ]*/)?chpc/row19_screen_manifest\.json --rep {int(sl['rep'])} --indices {idx} --slot {int(sl['slot'])} --job-id \$PBS_JOBID "
                      rf"--deadline-epoch \$DEADLINE > {re.escape(lustre_root)}/logs/job\$PBS_JOBID\.slot{int(sl['slot'])}\.log 2>&1$")


TIMING_REL = re.compile(r"^timing/rep([0-9]+)/t_([0-9]{3})\.json$")
ANY_DEATH_RE = re.compile(rf"\.SC: line \d+: +\d+ ({_SIG_RE}|Killed|Terminated)")
END_RE = re.compile(r"^job (\d+) ended: exit (-?\d+); workers exit codes (\[[^\]]*\]); wall \d+ s$")


def crashed_slot_evidence(man, role, n, e, plan, jid, obs, out_bytes, err_bytes, units, entries, root=None, slot_map=None):
    """REVISION 14: (evidence, '') when job n is a terminal, SETTLED refit job whose ONLY defect is that one or more planned
    workers died of a fatal signal before writing any status (so the job-end code is HELD 4), recomputed from the given ledger
    entries, the root on disk and the job's PBS output and error bytes; (None, reason) otherwise. Used by the status view (to
    report and un-alarm) and by the admission (to recompute, never taking the receipt's word)."""
    import ast
    n = int(n)
    if role != "refit":
        return None, "only refit jobs carry crashed-worker slot dispositions"
    if (obs or {}).get("state") != "F" or (obs or {}).get("exit") != HELD_EXIT or isinstance((obs or {}).get("exit"), bool):
        return None, f"the scheduler observation is not state F with exit {HELD_EXIT}"
    if e.get("state") != "settled" or not (_num(e.get("settled_core_h")) and e["settled_core_h"] >= 0) \
            or not (_num(e.get("settled_at")) and e["settled_at"] >= 0) or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8):
        return None, "the ledger entry is not SETTLED with settlement evidence (charge, note, non-negative time)"
    if e.get("runner_exit") != HELD_EXIT or isinstance(e.get("runner_exit"), bool):
        return None, f"the ledger's runner exit is {e.get('runner_exit')}, not HELD {HELD_EXIT}"
    if not jid or e.get("job_id") != jid or not e.get("token") or plan.get("token") != e.get("token") or plan.get("job") != n:
        return None, "the plan is not this entry's token, job and PBS id"
    root = root or man["storage"]["root"]; slots = plan.get("slots") or []
    slot_map = slot_map or (lambda m: _plan_slot_of(man, m))
    present, missing = {}, []
    for sl in slots:
        p = os.path.join(root, "status", f"job{jid}.slot{int(sl['slot'])}.json")
        if not os.path.exists(p):
            missing.append(sl); continue
        try:
            st = _strict_load(p)
        except Exception:
            return None, f"slot {sl['slot']}: its worker status is unreadable"
        if not isinstance(st, dict) or st.get("job") != jid or st.get("slot") != int(sl["slot"]) or st.get("exit") not in (0, 75) or isinstance(st.get("exit"), bool):
            return None, f"slot {sl['slot']}: its worker status is not this job's slot with exit 0 or 75 (a HELD worker is not a crash)"
        present[int(sl["slot"])] = st["exit"]
    if not missing:
        return None, "every planned worker wrote a status; nothing crashed"
    want_scoped = sorted(f"job{jid}.slot{s}.json" for s in present)
    if sorted(status_scoped(root, jid)) != want_scoped:
        return None, f"status evidence scoped to {jid} is not exactly the surviving workers' statuses"
    txt = out_bytes.decode("utf-8", errors="replace")
    if "ADMISSION FAILED" in txt or f"job {jid}" not in txt:
        return None, f"the PBS output reports ADMISSION FAILED or does not name {jid}"
    ends = [m for m in (END_RE.match(l) for l in txt.splitlines()) if m]
    if len(ends) != 1 or int(ends[0].group(1)) != n or int(ends[0].group(2)) != HELD_EXIT:
        return None, f"the PBS output does not carry exactly one 'job {n} ended: exit {HELD_EXIT}' line"
    try:
        codes = ast.literal_eval(ends[0].group(3))
    except Exception:
        return None, "the PBS output's worker exit codes are unparsable"
    want_codes = [present.get(int(sl["slot"])) for sl in slots]
    if not isinstance(codes, list) or codes != want_codes:
        return None, f"the job-end worker codes {codes} are not None exactly at the missing slots and the statuses' exits elsewhere"
    err = err_bytes.decode("utf-8", errors="replace").splitlines()
    out_slots = []
    for sl in missing:
        rx = crash_line_re(jid, sl, man["storage"]["root"]); hits = [m for m in (rx.match(l) for l in err) if m]
        if len(hits) != 1:
            return None, f"slot {sl['slot']}: the PBS error stream does not carry exactly one fatal-signal line for its planned worker"
        out_slots.append(dict(slot=int(sl["slot"]), rep=int(sl["rep"]), indices=[int(i) for i in sl["indices"]], signal=hits[0].group(1),
                              err_line=hits[0].group(0)))
    deaths = [l for l in err if ANY_DEATH_RE.search(l)]
    if len(deaths) != len(missing):
        return None, f"the PBS error stream reports {len(deaths)} worker death(s), not exactly the {len(missing)} missing worker(s)"
    gone = {f"{int(sl['rep'])}/{int(i)}": int(sl["slot"]) for sl in missing for i in sl["indices"]}
    named = sorted(k for k, u in units.items() if ((u or {}).get("timing") or {}).get("job") == jid and k in gone)
    if named:
        return None, f"unit(s) {named[:3]} at a crashed worker's coordinates carry timing naming {jid}"
    surv = {f"{int(sl['rep'])}/{int(i)}": int(sl["slot"]) for sl in slots if int(sl["slot"]) in present for i in sl["indices"]}
    for rel in timing_scan(root, jid):                                  # V15-1 (Codex 5ca7fbd): EVERY same-job timing is a survivor's
        m = TIMING_REL.match(rel)
        if not m:
            return None, f"timing evidence of unknown attribution ({rel})"
        try:
            t = _strict_load(os.path.join(root, rel))
        except Exception:
            return None, f"timing evidence of unknown attribution ({rel})"
        if not isinstance(t, dict) or t.get("job") != jid or not all(_int(t.get(f)) for f in ("rep", "index", "slot")):
            return None, f"timing {rel} names {jid} without integer rep, index and slot"
        if rel != f"timing/rep{t['rep']}/t_{t['index']:03d}.json":          # the publisher's exact path (row19_shard.timing_path)
            return None, f"timing {rel} is not at its canonical path (it names {t['rep']}/{t['index']})"
        k = f"{t['rep']}/{t['index']}"
        if surv.get(k) != t["slot"]:
            return None, f"timing {rel} names {jid} slot {t['slot']} at {k}, not a surviving worker's planned coordinate and slot"
    num_of = {x.get("job_id"): int(x["rep"]) for x in entries if x.get("kind") == ROLES[role] and x.get("job_id")}
    plans = {}

    def pso(m):
        if m not in plans:
            plans[m] = slot_map(m)
        return plans[m]
    for k in sorted(gone):
        files, odd = coordinate_files(man, root, role, k)
        if odd:
            return None, f"coordinate {k}: temporary or non-canonical output files {[os.path.basename(p) for p in odd][:3]}"
        if files or (units.get(k) or {}).get("record") is not None:
            why = later_completion(man, root, role, units, k, n, num_of, pso)
            if why:
                return None, f"coordinate {k} holds output that is not a later bound job's planned completion ({why})"
    pp = os.path.join(root, "plans", f"job_{n}.json")
    return dict(kind=CRASH_KIND, job_id=jid, scheduler_state="F", scheduler_exit=HELD_EXIT, runner_exit=HELD_EXIT,
                settled_core_h=e["settled_core_h"], settle_note=e["settle_note"], settled_at=e["settled_at"], token=e["token"],
                plan_sha256=sha_file(pp), output_file=f"row19_screen_{role}_{n}.out", output_sha256=hashlib.sha256(out_bytes).hexdigest(),
                error_file=f"row19_screen_{role}_{n}.err", error_sha256=hashlib.sha256(err_bytes).hexdigest(),
                slots=out_slots, uncompleted=sorted(gone),
                note="worker(s) killed by a fatal signal before any status or record: charged, no completion or credit; "
                     "the coordinates return to the planner; the job never qualifies"), ""


def job_error_path(man, role, n):
    return os.path.join(man["shard"]["toolchain"], "jobs", f"row19_screen_{role}_{int(n)}.err")


def slot_disposition_problem(man, manifest_path, role, n, sj, bound):
    """REVISION 14: '' only when the receipt's crashed-worker slot disposition of job n is exactly what crashed_slot_evidence
    recomputes HERE from the current ledger, root and PBS output/error bytes on disk, the receipt binds those bytes, and the
    summary accounts the crashed coordinates as uncompleted (origin "crashed-slot") and everything else from the statuses."""
    n = str(int(n)); d = sj.get("slot_disposition") if isinstance(sj, dict) else None
    if not isinstance(d, dict) or d.get("kind") != CRASH_KIND:
        return f"job {n}: no crashed-worker slot disposition"
    if sj.get("disposition") is not None:
        return f"job {n}: a job cannot carry both dispositions"
    jid = sj.get("job_id")
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    hits = [e for e in led["entries"].values() if e.get("kind") == ROLES[role] and e.get("rep") == int(n)]
    if len(hits) != 1:
        return f"job {n}: {len(hits)} current ledger entries"
    e = hits[0]
    why = certificate_problem(d, e)
    if why:
        return f"job {n}: {why}"
    bj = (bound.get("jobs") or {}).get(n) or {}
    pp = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    try:
        plan = _strict_load(pp)
    except (OSError, ValueError):
        return f"job {n}: its plan is absent or unreadable"
    if not jid or bj.get("job_id") != jid or bj.get("token") != e.get("token") or sha_file(pp) != bj.get("plan_sha256") or d.get("plan_sha256") != bj.get("plan_sha256"):
        return f"job {n}: the PBS id, token or plan is not the bound one"
    so = (bound.get("slot_outputs") or {}).get(n) or {}
    blobs = {}
    for kind, path, fk, sk in (("out", job_output_path(man, role, n), "output_file", "output_sha256"),
                               ("err", job_error_path(man, role, n), "error_file", "error_sha256")):
        b = so.get(kind) or {}
        if b.get("file") != os.path.basename(path) or b.get("file") != d.get(fk) or not _hex64(b.get("sha256")) or b["sha256"] != d.get(sk):
            return f"job {n}: the receipt does not bind the PBS {kind} bytes of the disposition"
        try:
            blobs[kind] = open(path, "rb").read()
        except OSError as ex:
            return f"job {n}: the PBS {kind} file {path} is absent or unreadable ({ex})"
        if hashlib.sha256(blobs[kind]).hexdigest() != b["sha256"]:
            return f"job {n}: the PBS {kind} file is not the bytes the receipt bound; recollect"
    vdoc = _verifier_doc(man, bound)
    obs = dict(state=sj.get("state"), exit=sj.get("exit"))
    got, why = crashed_slot_evidence(man, role, n, e, plan, jid, obs, blobs["out"], blobs["err"], vdoc.get("units") or {}, list(led["entries"].values()))
    if why:
        return f"job {n}: not a crashed-worker slot disposition ({why})"
    if got != d:
        return f"job {n}: the receipt's slot disposition is not what the current evidence gives; recollect"
    want = plan_slots(man, n); k = len(d["slots"])
    if not (_int(sj.get("slots")) and sj["slots"] == want and _int(sj.get("ended")) and sj["ended"] == want - k and sj.get("runner_exit") == HELD_EXIT):
        return f"job {n}: the summary is not {want - k} ended workers of {want} with runner exit {HELD_EXIT}"
    part = sj.get("partition")
    if not isinstance(part, dict) or part.get("uncompleted") != d["uncompleted"] or part.get("uncompleted_origin") != "crashed-slot":
        return f"job {n}: the crashed workers' coordinates are not accounted as uncompleted with origin crashed-slot"
    return ""


def node_disposition_problem(man, manifest_path, role, n, sj, bound):
    """REVISION 18: '' only when the receipt's node-failure disposition of job n is exactly what
    row19_screen_nodefail.node_failure_evidence recomputes HERE from the current ledger, root, retained verifier units and the
    node evidence bytes on disk (the receipt binds them), no PBS .out/.err of the job exists now, and the summary accounts the
    no-status slots' coordinates as uncompleted (origin "node-failure") and everything else from the completed statuses."""
    import row19_screen_nodefail as NF
    n = str(int(n)); d = sj.get("node_disposition") if isinstance(sj, dict) else None
    if not isinstance(d, dict) or d.get("kind") != NF.NODE_KIND:
        return f"job {n}: no node-failure disposition"
    if sj.get("disposition") is not None or sj.get("slot_disposition") is not None:
        return f"job {n}: a job carries one disposition at most"
    jid = sj.get("job_id")
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    hits = [e for e in led["entries"].values() if e.get("kind") == ROLES[role] and e.get("rep") == int(n)]
    if len(hits) != 1:
        return f"job {n}: {len(hits)} current ledger entries"
    e = hits[0]
    why = certificate_problem(d, e)
    if why:
        return f"job {n}: {why}"
    bj = (bound.get("jobs") or {}).get(n) or {}
    pp = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    try:
        plan = _strict_load(pp)
    except (OSError, ValueError):
        return f"job {n}: its plan is absent or unreadable"
    if not jid or bj.get("job_id") != jid or bj.get("token") != e.get("token") or sha_file(pp) != bj.get("plan_sha256") or d.get("plan_sha256") != bj.get("plan_sha256"):
        return f"job {n}: the PBS id, token or plan is not the bound one"
    ne = (bound.get("node_evidence") or {}).get(n) or {}
    path = NF.evidence_path(man, role, n)
    if ne.get("file") != os.path.basename(path) or ne.get("file") != d.get("evidence_file") or not _hex64(ne.get("sha256")) or ne["sha256"] != d.get("evidence_sha256"):
        return f"job {n}: the receipt does not bind the node evidence of the disposition"
    try:
        vb = open(path, "rb").read()
    except OSError as ex:
        return f"job {n}: the node evidence {path} is absent or unreadable ({ex})"
    if hashlib.sha256(vb).hexdigest() != ne["sha256"]:
        return f"job {n}: the node evidence is not the bytes the receipt bound; recollect"
    for p in (job_output_path(man, role, n), job_error_path(man, role, n)):
        if os.path.exists(p):
            return f"job {n}: its PBS file {os.path.basename(p)} exists now (PBS staged the job out): not a node-failure disposition; recollect"
    vdoc = _verifier_doc(man, bound)
    obs = dict(state=sj.get("state"), exit=sj.get("exit"))                 # the reserve comes from the plan's envelope (checked
    got, why = NF.node_failure_evidence(man, role, n, e, plan, jid, obs, vb, vdoc.get("units") or {}, list(led["entries"].values()),
                                        pin=NF.capture_pin())                # against the resolved one by receipt_envelope_problem)
    if why:
        return f"job {n}: not a node-failure disposition ({why})"
    if got != d:
        return f"job {n}: the receipt's node disposition is not what the current evidence gives; recollect"
    want = plan_slots(man, n); k = len(d["no_status_slots"])
    if not (_int(sj.get("slots")) and sj["slots"] == want and _int(sj.get("ended")) and sj["ended"] == want - k and sj.get("runner_exit") is None):
        return f"job {n}: the summary is not {want - k} completed workers of {want} with no runner exit"
    part = sj.get("partition")
    if not isinstance(part, dict) or part.get("uncompleted") != d["uncompleted"] or part.get("uncompleted_origin") != "node-failure":
        return f"job {n}: the no-status slots' coordinates are not accounted as uncompleted with origin node-failure"
    return ""


OPLOSS_KIND = "operational-loss"                                        # REVISION 19
CLEAN_EXITS = (0, 75)
OPLOSS_EXIT_RE = re.compile(r"Exit_status (-?\d+)\b")
RUNNER_END = ("runner_exit", "runner_ended", "runner_wall_s")


def operational_loss_evidence(man, role, n, e, plan, jid, obs, units, entries, root=None, slot_map=None):
    """REVISION 19: (disposition, '') when job n is an operational loss on THIS evidence (module docstring, REVISION 19);
    (None, reason) otherwise. `obs` is the scheduler observation (state, exit); `e` the ledger entry; `entries` every ledger
    entry (producer numbering for later completions). Used by the status view (to report and un-alarm) and by the admission (to
    recompute, never taking the receipt's word)."""
    n = int(n)
    if role != "refit":
        return None, "only refit jobs carry operational-loss dispositions"
    ex = (obs or {}).get("exit")
    if (obs or {}).get("state") != "F" or not _int(ex):
        return None, "the scheduler observation is not state F with an integer exit"
    ended = any(e.get(f) is not None for f in RUNNER_END)
    rx = e.get("runner_exit")
    if ended and not _int(rx):
        return None, "the ledger records a runner end without an integer runner exit (ledger inconsistency)"
    if ex in CLEAN_EXITS and ended and rx in CLEAN_EXITS:
        return None, "a clean terminal job (scheduler and runner exits 0/75) needs no disposition"
    if e.get("state") != "settled" or not (_num(e.get("settled_core_h")) and e["settled_core_h"] >= 0) \
            or not (_num(e.get("settled_at")) and e["settled_at"] >= 0) or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8):
        return None, "the ledger entry is not SETTLED with settlement evidence (charge, note, non-negative time): settling is the operator's step"
    m = OPLOSS_EXIT_RE.search(e["settle_note"])
    if not m or int(m.group(1)) != ex:
        return None, f"the settlement note's Exit_status is not the observed {ex} (ledger inconsistency)"
    if not jid or e.get("job_id") != jid or not e.get("token") or plan.get("token") != e.get("token") or plan.get("job") != n:
        return None, "the plan is not this entry's token, job and PBS id"
    root = root or man["storage"]["root"]; slots = plan.get("slots") or []
    slot_map = slot_map or (lambda m_: _plan_slot_of(man, m_))
    present, missing, crashed, allowed = {}, [], [], {}
    for sl in slots:
        s = int(sl["slot"]); r = int(sl["rep"]); want = [int(i) for i in sl["indices"]]
        p = os.path.join(root, "status", f"job{jid}.slot{s}.json")
        if not os.path.exists(p):
            missing.append(sl); continue
        try:
            st = _strict_load(p)
        except Exception:
            return None, f"slot {s}: its worker status is unreadable (corrupt evidence)"
        if not isinstance(st, dict) or st.get("job") != jid or st.get("slot") != s or not _int(st.get("exit")):
            return None, f"slot {s}: its status is not this job's slot with an integer exit"
        lists = [st.get(x) for x in ("new", "resumed", "left")]
        if st.get("rep") != r or st.get("indices") != want or not all(isinstance(x, list) and all(_int(i) for i in x) for x in lists) \
                or sorted(st["new"] + st["resumed"] + st["left"]) != sorted(want):
            return None, f"slot {s}: its status is not its planned assignment partitioned into new/resumed/left"
        new = {f"{r}/{i}" for i in st["new"]}
        own = {f"{r}/{i}" for i in want if (((units.get(f"{r}/{i}") or {}).get("timing") or {}).get("job") == jid)}
        if own - new:
            return None, f"slot {s}: unit(s) {sorted(own - new)[:3]} carry timing naming {jid} but are not the status's new coordinates"
        present[s] = st; allowed.update({k: s for k in new})
        if st["exit"] not in CLEAN_EXITS:
            crashed.append(dict(slot=s, exit=st["exit"], left=sorted(f"{r}/{i}" for i in st["left"])))
    want_scoped = sorted(f"job{jid}.slot{s}.json" for s in present)
    if sorted(status_scoped(root, jid)) != want_scoped:
        return None, f"status evidence scoped to {jid} is not exactly the planned slots' statuses"
    if ended:                                                           # job-end's own rule (row19_shard.cmd_job_end)
        codes = [present[int(sl["slot"])]["exit"] if int(sl["slot"]) in present else None for sl in slots]
        exp = HELD_EXIT if (not codes or any(c not in CLEAN_EXITS for c in codes)) else (75 if 75 in codes else 0)
        if rx != exp:
            return None, f"the ledger's runner exit {rx} is not the job-end code {exp} the statuses give (ledger inconsistency)"
    for sl in missing:
        lp = os.path.join(root, "logs", f"job{jid}.slot{int(sl['slot'])}.log")
        if os.path.exists(lp):
            try:
                txt = open(lp, "rb").read().decode("utf-8", errors="replace")
            except OSError:
                return None, f"slot {sl['slot']}: its worker log is unreadable"
            if any(l.startswith(f"worker job {jid} slot {int(sl['slot'])}: exit ") for l in txt.splitlines()):
                return None, f"slot {sl['slot']}: its worker log reports an exit but no status exists (a missing status is not explained)"
    num_of = {x.get("job_id"): int(x["rep"]) for x in entries if x.get("kind") == ROLES[role] and x.get("job_id")}
    plans = {}

    def pso(m_):
        if m_ not in plans:
            plans[m_] = slot_map(m_)
        return plans[m_]
    gone, salvaged = [], []
    for sl in missing:
        s = int(sl["slot"])
        for i in sl["indices"]:
            k = f"{int(sl['rep'])}/{int(i)}"
            files, odd = coordinate_files(man, root, role, k)
            if odd:
                return None, f"coordinate {k}: temporary or non-canonical output files {[os.path.basename(p) for p in odd][:3]}"
            u = units.get(k) or {}; t = u.get("timing") or {}
            if t.get("job") == jid:
                if (u.get("record") or {}).get("ok") and t.get("ok") is True and _int(t.get("slot")) and t["slot"] == s \
                        and not current_artifacts_problem(man, root, role, k, u):
                    salvaged.append(k); allowed[k] = s; continue
                return None, f"coordinate {k}: a unit naming {jid} that is not a verified completion in its planned slot {s}"
            if files or u.get("record") is not None:
                why = later_completion(man, root, role, units, k, n, num_of, pso)
                if why:
                    return None, f"coordinate {k} holds output that is neither this job's verified completion nor a later bound job's ({why})"
            gone.append(k)
    for rel in timing_scan(root, jid):                                  # the V15-1 rule: every same-job timing is accounted
        mt = TIMING_REL.match(rel)
        if not mt:
            return None, f"timing evidence of unknown attribution ({rel})"
        try:
            t = _strict_load(os.path.join(root, rel))
        except Exception:
            return None, f"timing evidence of unknown attribution ({rel})"
        if not isinstance(t, dict) or t.get("job") != jid or not all(_int(t.get(f)) for f in ("rep", "index", "slot")):
            return None, f"timing {rel} names {jid} without integer rep, index and slot"
        if rel != f"timing/rep{t['rep']}/t_{t['index']:03d}.json":
            return None, f"timing {rel} is not at its canonical path (it names {t['rep']}/{t['index']})"
        if allowed.get(f"{t['rep']}/{t['index']}") != t["slot"]:
            return None, f"timing {rel} names {jid} slot {t['slot']}, not a status's new or a salvaged coordinate in its planned slot"
    pp = os.path.join(root, "plans", f"job_{n}.json")
    return dict(kind=OPLOSS_KIND, job_id=jid, scheduler_state="F", scheduler_exit=ex, runner_exit=rx if ended else None, runner_end=ended,
                settled_core_h=e["settled_core_h"], settle_note=e["settle_note"], settled_at=e["settled_at"], token=e["token"],
                plan_sha256=sha_file(pp), completed_slots=sorted(s for s, st in present.items() if st["exit"] in CLEAN_EXITS),
                crashed_slots=sorted(crashed, key=lambda c: c["slot"]), no_status_slots=sorted(int(sl["slot"]) for sl in missing),
                salvaged=sorted(salvaged), uncompleted=sorted(gone), counts_as_crash=False,
                note="an operational loss (scheduler/worker failure, no evidence file required): charged, no credit; completed slots and "
                     "salvaged records are kept, no-status coordinates return to the planner, crashed workers' left coordinates too; never "
                     "a crash, never a pilot"), ""


def oploss_disposition_problem(man, manifest_path, role, n, sj, bound):
    """REVISION 19: '' only when the receipt's operational-loss disposition of job n is exactly what operational_loss_evidence
    recomputes HERE from the current ledger, root and retained verifier units, and the summary accounts the no-status
    coordinates (less salvaged) as uncompleted (origin "operational-loss") and everything else from the statuses."""
    n = str(int(n)); d = sj.get("operational_loss") if isinstance(sj, dict) else None
    if not isinstance(d, dict) or d.get("kind") != OPLOSS_KIND:
        return f"job {n}: no operational-loss disposition"
    if any(sj.get(k) is not None for k in ("disposition", "slot_disposition", "node_disposition")):
        return f"job {n}: a job carries one disposition at most"
    jid = sj.get("job_id")
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    hits = [e for e in led["entries"].values() if e.get("kind") == ROLES[role] and e.get("rep") == int(n)]
    if len(hits) != 1:
        return f"job {n}: {len(hits)} current ledger entries"
    e = hits[0]
    why = certificate_problem(d, e)
    if why:
        return f"job {n}: {why}"
    bj = (bound.get("jobs") or {}).get(n) or {}
    pp = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    try:
        plan = _strict_load(pp)
    except (OSError, ValueError):
        return f"job {n}: its plan is absent or unreadable"
    if not jid or bj.get("job_id") != jid or bj.get("token") != e.get("token") or sha_file(pp) != bj.get("plan_sha256") or d.get("plan_sha256") != bj.get("plan_sha256"):
        return f"job {n}: the PBS id, token or plan is not the bound one"
    vdoc = _verifier_doc(man, bound)
    obs = dict(state=sj.get("state"), exit=sj.get("exit"))
    got, why = operational_loss_evidence(man, role, n, e, plan, jid, obs, vdoc.get("units") or {}, list(led["entries"].values()))
    if why:
        return f"job {n}: not an operational-loss disposition ({why})"
    if got != d:
        return f"job {n}: the receipt's operational-loss disposition is not what the current evidence gives; recollect"
    want = plan_slots(man, n); k = len(d["no_status_slots"])
    if not (_int(sj.get("slots")) and sj["slots"] == want and _int(sj.get("ended")) and sj["ended"] == want - k and sj.get("runner_exit") == d["runner_exit"]):
        return f"job {n}: the summary is not {want - k} ended workers of {want} with the ledger's runner exit"
    part = sj.get("partition")
    if not isinstance(part, dict) or part.get("uncompleted") != d["uncompleted"] or part.get("uncompleted_origin") != "operational-loss" \
            or not set(d["salvaged"]) <= set(part.get("new") or []):
        return f"job {n}: the no-status coordinates are not accounted as uncompleted with origin operational-loss (salvaged as new)"
    return ""


def plan_slots(man, n):
    p = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    return len(json.load(open(p))["slots"]) if os.path.exists(p) else None


def job_summary_problem(man, n, s, pilot=False):
    """R2: one job summary against its plan. Queued or running jobs pass; a terminal job must be complete and clean."""
    if not isinstance(s, dict):
        return f"job {n}: no summary"
    if pilot and s.get("disposition") is not None:
        return f"job {n}: a dispositioned job never qualifies a pilot"
    if pilot and s.get("slot_disposition") is not None:
        return f"job {n}: a slot-dispositioned job never qualifies a pilot"
    if pilot and s.get("node_disposition") is not None:                      # REVISION 18
        return f"job {n}: a node-dispositioned job never qualifies a pilot"
    if pilot and s.get("operational_loss") is not None:                      # REVISION 19
        return f"job {n}: an operational-loss job never qualifies a pilot"
    if s.get("state") in ("Q", "R", "H", "W", "B"):
        return "" if not pilot else f"job {n} is not terminal"
    want = plan_slots(man, n)
    if s.get("operational_loss") is not None:                                 # REVISION 19: validated by oploss_disposition_problem
        d = s["operational_loss"] if isinstance(s["operational_loss"], dict) else {}
        k = len(d.get("no_status_slots") or [])
        if not _int(want):
            return f"job {n}: no plan to check the operational-loss summary against"
        if s.get("state") != "F" or not _int(s.get("exit")) or s.get("runner_exit") != d.get("runner_exit") or isinstance(s.get("runner_exit"), bool):
            return f"job {n}: an operational-loss job must be F with an integer scheduler exit and the disposition's runner exit"
        if not (_int(s.get("slots")) and s["slots"] == want and _int(s.get("ended")) and s["ended"] == want - k and _int(s.get("left")) and s["left"] >= 0
                and _int(s.get("new")) and s["new"] >= 0 and _int(s.get("resumed")) and s["resumed"] >= 0):
            return f"job {n}: the plan's {want} workers less {k} without status are not the ended workers"
        ex = s.get("exits")
        if not isinstance(ex, dict) or any(not _int(v) or v < 0 for v in ex.values()) or sum(ex.values()) != want - k:
            return f"job {n}: worker exits {ex} do not count the {want - k} ended workers"
        if s.get("mem_kb") is not None and not (_num(s.get("mem_kb")) and s["mem_kb"] >= 0):
            return f"job {n}: observed scheduler memory is not finite and non-negative"
        return ""
    if s.get("node_disposition") is not None:                                 # REVISION 18: validated by node_disposition_problem
        import row19_screen_nodefail as NF
        d = s["node_disposition"] if isinstance(s["node_disposition"], dict) else {}
        k = len(d.get("no_status_slots") or [])
        if not _int(want):
            return f"job {n}: no plan to check the node-dispositioned summary against"
        if s.get("state") != "F" or not _int(s.get("exit")) or s["exit"] not in NF.KILL_EXITS or s.get("runner_exit") is not None:
            return f"job {n}: a node-dispositioned job must be F with a kill-set exit {list(NF.KILL_EXITS)} and no runner exit"
        if not (_int(s.get("slots")) and s["slots"] == want and _int(s.get("ended")) and s["ended"] == want - k and _int(s.get("left")) and s["left"] == 0
                and _int(s.get("new")) and s["new"] >= 0 and _int(s.get("resumed")) and s["resumed"] >= 0 and s["new"] + s["resumed"] == len(d.get("completed") or [])):
            return f"job {n}: the plan's {want} workers less {k} without status did not all complete"
        ex = s.get("exits")
        if not isinstance(ex, dict) or (want - k and ex != {"0": want - k}) or (not want - k and ex != {}):
            return f"job {n}: completed worker exits {ex} are not all 0 for {want - k} workers"
        if not (_num(s.get("mem_kb")) and s["mem_kb"] >= 0) or not ((want - k and _num(s.get("max_worker_maxrss")) and s["max_worker_maxrss"] >= 0)
                                                                     or (not want - k and s.get("max_worker_maxrss") is None)):
            return f"job {n}: observed scheduler and worker memory are not finite and non-negative"
        return ""
    if s.get("slot_disposition") is not None:                                 # REVISION 14: validated by slot_disposition_problem
        k = len((s["slot_disposition"] or {}).get("slots") or [])
        if s.get("state") != "F" or s.get("exit") != HELD_EXIT or s.get("runner_exit") != HELD_EXIT or isinstance(s.get("exit"), bool) or not k:
            return f"job {n}: a slot-dispositioned job must be F with scheduler and runner exit {HELD_EXIT} and at least one crashed slot"
        if not (_int(s.get("slots")) and s["slots"] == want and _int(s.get("ended")) and s["ended"] == want - k and _int(s.get("left")) and s["left"] >= 0
                and _int(s.get("new")) and s["new"] >= 0 and _int(s.get("resumed")) and s["resumed"] >= 0):
            return f"job {n}: the plan's {want} workers less {k} crashed did not all end"
        ex = s.get("exits")
        if not isinstance(ex, dict) or any(x not in ("0", "75") or not _int(v) or v < 0 for x, v in ex.items()) or sum(ex.values()) != want - k:
            return f"job {n}: surviving worker exits {ex} are not all 0/75 for {want - k} workers"
        if not (_num(s.get("mem_kb")) and s["mem_kb"] >= 0 and _num(s.get("max_worker_maxrss")) and s["max_worker_maxrss"] >= 0):
            return f"job {n}: observed scheduler and worker memory are not finite and non-negative"
        return ""
    if s.get("state") != "F" or not (_int(s.get("exit")) and s["exit"] in (0, 75)) or not (_int(s.get("runner_exit")) and s["runner_exit"] in (0, 75)):
        return f"job {n} is not terminal F with scheduler and runner exits 0 or 75 (integers)"
    if not (_int(s.get("slots")) and s["slots"] == want and _int(s.get("ended")) and s["ended"] == want and _int(s.get("left")) and s["left"] >= 0
            and _int(s.get("new")) and s["new"] >= 0 and _int(s.get("resumed")) and s["resumed"] >= 0):
        return f"job {n}: the plan's {want} workers did not all end (summary slots {s.get('slots')}, ended {s.get('ended')})"
    ex = s.get("exits")
    if not isinstance(ex, dict) or any(k not in ("0", "75") or not _int(v) or v < 0 for k, v in ex.items()) or sum(ex.values()) != want:
        return f"job {n}: worker exits {ex} are not all 0/75 for the plan's {want} workers"
    if pilot and (ex != {"0": want} or s["left"] != 0):
        return f"job {n}: not every planned worker ended 0 with nothing left"
    if not (_num(s.get("mem_kb")) and s["mem_kb"] >= 0 and _num(s.get("max_worker_maxrss")) and s["max_worker_maxrss"] >= 0):
        return f"job {n}: observed scheduler and worker memory are not finite and non-negative"
    return ""


def pilot_summary_problem(rec, n="1", man=None):
    return job_summary_problem(man, n, (rec.get("jobs") or {}).get(n), pilot=True) if man is not None else "no manifest to check the plan"


def _hex64(x):
    return isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)


def generation_problem(g):
    """C2: the emitted generation must be the latest version with the EXACT reviewed verifier and controls digests."""
    if not isinstance(g, dict):
        return "no controller generation"
    ctl = controls(); latest = ctl["versions"][-1]
    if g.get("version") != latest["version"] or g.get("latest") != latest["version"]:
        return f"controller generation {g.get('version')}, not the latest {latest['version']}"
    if "controls_problem" not in g or g["controls_problem"] != "":
        return f"the producer's lineage check is not explicitly clean ({g.get('controls_problem')!r})"
    if not (_hex64(g.get("verify_sha256")) and g["verify_sha256"] == latest["files"].get("chpc/row19_screen_verify.py")):
        return "the producer verifier's bytes are not the latest version's verifier pin"
    adopted = json.load(open(os.path.join(T1, CONTROLS_ADOPTION))).get("controls_sha256") if os.path.exists(os.path.join(T1, CONTROLS_ADOPTION)) else None
    if not (_hex64(g.get("controls_sha256")) and g["controls_sha256"] == adopted):
        return "the producer's controls file is not the adopted controls bytes"
    return ""


def units_problem(man, v, rec, pilot_job=None):
    """C2: the retained units agree with the summaries: per job, units whose timing names it = its `new`; the pilot's every
    planned unit is a valid record with a timing naming its job and slot."""
    units = v.get("units") or {}
    lp = os.path.join(man["storage"]["campaign"], "budget.json")
    led = _strict_load(lp) if os.path.exists(lp) else {"entries": {}}
    bound_id = {str(int(e["rep"])): e.get("job_id") for e in led["entries"].values() if e.get("kind") in ("shard", "orig")}
    num_of = {jid: int(m) for m, jid in bound_id.items() if jid}
    for n, sj in (rec.get("jobs") or {}).items():
        jid = (sj or {}).get("job_id")
        if jid != bound_id.get(str(n)):
            return f"job {n}: the summary names PBS id {jid}, the ledger binds {bound_id.get(str(n))}"
        if isinstance(sj, dict) and sj.get("disposition") is not None:
            if [k for k, u in units.items() if (u.get("timing") or {}).get("job") == jid]:
                return f"job {n}: units name the dispositioned job"
            continue                                                          # REVISION 8: validated by disposition_problem
        if (sj or {}).get("state") in TERMINAL_STATES:
            slot_of = _plan_slot_of(man, n)
            if isinstance(sj, dict) and sj.get("slot_disposition") is not None:     # REVISION 14: the crashed coordinates are uncompleted
                gone = set((sj["slot_disposition"] or {}).get("uncompleted") or [])
                if not gone or not gone <= set(slot_of) or [k for k in gone if ((units.get(k) or {}).get("timing") or {}).get("job") == jid]:
                    return f"job {n}: its crashed coordinates are not planned for it, or carry timing naming it"
                slot_of = {k: v for k, v in slot_of.items() if k not in gone}
            if isinstance(sj, dict) and sj.get("node_disposition") is not None:     # REVISION 18: the no-status slots' coordinates
                gone = set((sj["node_disposition"] or {}).get("uncompleted") or [])  # are uncompleted (may be empty)
                if not gone <= set(slot_of) or [k for k in gone if ((units.get(k) or {}).get("timing") or {}).get("job") == jid]:
                    return f"job {n}: its node-failure coordinates are not planned for it, or carry timing naming it"
                slot_of = {k: v for k, v in slot_of.items() if k not in gone}
            if isinstance(sj, dict) and sj.get("operational_loss") is not None:     # REVISION 19: the no-status coordinates less
                gone = set((sj["operational_loss"] or {}).get("uncompleted") or [])  # salvaged are uncompleted (may be empty)
                if not gone <= set(slot_of) or [k for k in gone if ((units.get(k) or {}).get("timing") or {}).get("job") == jid]:
                    return f"job {n}: its operational-loss coordinates are not planned for it, or carry timing naming it"
                slot_of = {k: v for k, v in slot_of.items() if k not in gone}
            good = [k for k, u in units.items() if k in slot_of and (u.get("record") or {}).get("ok") and (u.get("timing") or {}).get("ok") is True
                    and (u.get("timing") or {}).get("job") == jid and _int((u.get("timing") or {}).get("slot"))
                    and slot_of[k] == (u.get("timing") or {}).get("slot")]
            named = [k for k, u in units.items() if (u.get("timing") or {}).get("job") == jid]
            if len(named) != len(good):
                return f"job {n}: {len(named) - len(good)} unit(s) naming it are invalid, unplanned for it, or in another slot"
            if len(good) != sj.get("new"):
                return f"job {n}: {len(good)} valid unit(s) name it in the retained verifier, the summary claims {sj.get('new')} new"
            if not (_int(sj.get("resumed")) and _int(sj.get("left")) and sj["new"] + sj["resumed"] + sj["left"] == len(slot_of)):
                return f"job {n}: new + resumed + left is not the plan's {len(slot_of)} units"
            done = [k for k in slot_of if (units.get(k, {}).get("record") or {}).get("ok") and (units.get(k, {}).get("timing") or {}).get("ok") is True]
            if len(done) < sj["new"] + sj["resumed"]:
                return f"job {n}: only {len(done)} of its planned units have a valid record and timing, the summary claims {sj['new'] + sj['resumed']} done"
            why = _partition_problem(man, n, sj, units, slot_of, num_of)
            if why:
                return why
    if pilot_job is not None:
        p = json.load(open(os.path.join(man["storage"]["root"], "plans", f"job_{pilot_job}.json")))
        jid = rec["jobs"][str(pilot_job)].get("job_id")
        for sl in p["slots"]:
            keys = [f"{int(sl['rep'])}/{int(i)}" for i in sl["indices"]] if "rep" in sl else [str(int(r)) for r in sl["reps"]]
            for k in keys:
                u = units.get(k) or {}
                if not (u.get("record") or {}).get("ok") or (u.get("timing") or {}).get("ok") is not True or (u.get("timing") or {}).get("job") != jid or (u.get("timing") or {}).get("slot") != int(sl["slot"]):
                    return f"pilot unit {k}: no valid record with a timing naming job {jid} slot {sl['slot']} in the retained verifier"
    return ""


TERMINAL_STATES = ("F", "E", "X", "gone")


def _partition_problem(man, n, sj, units, slot_of, num_of):
    """REVISION 7 C2: the job's own historical new/resumed/left lists against its plan, its counts and supported producers."""
    part = sj.get("partition")
    if not isinstance(part, dict) or any(not isinstance(part.get(x), list) or not all(isinstance(k, str) for k in part[x])
                                         for x in ("new", "resumed", "left")):
        return f"job {n}: the summary carries no per-unit new/resumed/left lists"
    new, res, left = part["new"], part["resumed"], part["left"]
    allk = new + res + left
    if len(set(allk)) != len(allk) or set(allk) != set(slot_of):
        return f"job {n}: its new/resumed/left lists are not a partition of its plan"
    if (len(new), len(res), len(left)) != (sj["new"], sj["resumed"], sj["left"]):
        return f"job {n}: its lists ({len(new)}/{len(res)}/{len(left)}) are not the summary's counts ({sj['new']}/{sj['resumed']}/{sj['left']})"
    plans = {}

    def producer(k):
        u = units.get(k) or {}; t = u.get("timing") or {}
        if not ((u.get("record") or {}).get("ok") and t.get("ok") is True and _int(t.get("slot"))):
            return None
        m = num_of.get(t.get("job"))
        if m is None:
            return None
        if m not in plans:
            plans[m] = _plan_slot_of(man, m)
        return m if plans[m].get(k) == t["slot"] else None
    for k in new:
        if producer(k) != int(n):
            return f"job {n}: new unit {k} has no valid record produced by this job in its plan slot"
    for k in res:
        m = producer(k)
        if m is None or m >= int(n):
            return f"job {n}: resumed unit {k} has no valid record from an earlier bound job that planned it in that slot"
    for k in left:
        if ((units.get(k) or {}).get("record") or {}).get("ok"):
            m = producer(k)
            if m is None or m <= int(n):
                return f"job {n}: left unit {k} holds a valid record that is not a later bound job's planned completion"
    return ""


def _plan_slot_of(man, n):
    """{unit key: slot} of job n's plan."""
    p = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for sl in json.load(open(p))["slots"]:
        keys = [f"{int(sl['rep'])}/{int(i)}" for i in sl["indices"]] if "rep" in sl else [str(int(r)) for r in sl["reps"]]
        for k in keys:
            out[k] = int(sl["slot"])
    return out


def transition_problem(man, role, r):
    """C1: the CURRENT ledger must still be what the receipt observed: a job it saw queued or running that has since recorded a
    runner end, or a terminal job whose recorded runner exit is not the receipt's, refuses until the evidence is recollected."""
    lp = os.path.join(man["storage"]["campaign"], "budget.json")
    led = _strict_load(lp) if os.path.exists(lp) else {"entries": {}}
    by_n = {str(int(e["rep"])): e for e in led["entries"].values() if e.get("kind") == ROLES[role]}
    for n, sj in (r.get("jobs") or {}).items():
        e = by_n.get(n)
        if e is None:
            return f"job {n} of the receipt is not in the ledger"
        now_exit = e.get("runner_exit")
        if isinstance(sj, dict) and sj.get("disposition") is not None:
            d = sj["disposition"] if isinstance(sj["disposition"], dict) else {}
            if e.get("state") != "settled" or any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")) \
                    or e.get("job_id") != sj.get("job_id") or not _num(e.get("settled_core_h")) or not _num(d.get("settled_core_h")) \
                    or abs(e["settled_core_h"] - d["settled_core_h"]) > 1e-9 or certificate_problem(d, e):
                return f"job {n}: the ledger no longer shows the disposed job as the receipt saw it (SETTLED, same settlement certificate and PBS id, no runner end); recollect"
            continue
        if isinstance(sj, dict) and sj.get("slot_disposition") is not None:          # REVISION 14: the same settled certificate
            d = sj["slot_disposition"] if isinstance(sj["slot_disposition"], dict) else {}
            if e.get("state") != "settled" or e.get("runner_exit") != HELD_EXIT or e.get("job_id") != sj.get("job_id") or certificate_problem(d, e):
                return f"job {n}: the ledger no longer shows the slot-disposed job as the receipt saw it (SETTLED, runner exit {HELD_EXIT}, same certificate and PBS id); recollect"
            continue
        if isinstance(sj, dict) and sj.get("node_disposition") is not None:          # REVISION 18: the same settled certificate
            d = sj["node_disposition"] if isinstance(sj["node_disposition"], dict) else {}
            if e.get("state") != "settled" or any(e.get(f) is not None for f in ("runner_exit", "runner_ended", "runner_wall_s")) \
                    or e.get("job_id") != sj.get("job_id") or certificate_problem(d, e):
                return f"job {n}: the ledger no longer shows the node-disposed job as the receipt saw it (SETTLED, no runner end, same certificate and PBS id); recollect"
            continue
        if isinstance(sj, dict) and sj.get("operational_loss") is not None:          # REVISION 19: the same settled certificate
            d = sj["operational_loss"] if isinstance(sj["operational_loss"], dict) else {}
            if e.get("state") != "settled" or e.get("runner_exit") != d.get("runner_exit") \
                    or any(e.get(f) is not None for f in RUNNER_END) != bool(d.get("runner_end")) \
                    or e.get("job_id") != sj.get("job_id") or certificate_problem(d, e):
                return f"job {n}: the ledger no longer shows the operational-loss job as the receipt saw it (SETTLED, same runner end, certificate and PBS id); recollect"
            continue
        if sj.get("state") not in TERMINAL_STATES and e.get("state") == "settled":
            return f"job {n} has been SETTLED since the receipt saw it {sj.get('state')}; recollect before admitting"
        if sj.get("state") in TERMINAL_STATES:
            if now_exit != sj.get("runner_exit"):
                return f"job {n}: the ledger's runner exit {now_exit} is not the receipt's {sj.get('runner_exit')}; recollect"
        elif now_exit is not None:
            return f"job {n} has ended (runner exit {now_exit}) since the receipt saw it {sj.get('state')}; recollect before admitting"
    return ""


def verifier_problem(man, bound, anchors, role):
    """R3: the retained full verifier document named by the bound evidence."""
    name, want = bound.get("verify_file"), bound.get("verify_file_sha256")
    if not isinstance(name, str) or "/" in name or not isinstance(want, str):
        return "no retained verifier document is named"
    p = os.path.join(man["storage"]["root"], "gate", name)
    if not os.path.exists(p) or sha_file(p) != want:
        return "the retained verifier document is absent or not the bound bytes"
    try:
        v = _strict_load(p)
    except ValueError as e:
        return f"the retained verifier document is malformed ({e})"
    why = generation_problem(v.get("generation"))
    if why:
        return f"the retained verifier document: {why}"
    if v.get("schema") != "row19-screen-verify-1" or v.get("role") != role or not _num(v.get("time")):
        return "the retained verifier document has another schema or role, or no time"
    if v.get("manifest_sha256") != bound.get("manifest_sha256"):
        return "the retained verifier document verified another manifest"
    if v.get("environment_bad") != [] or v.get("code_bad") != []:
        return "the retained verifier document reports an environment or code difference (or omits the verdicts)"
    if any(not (x or {}).get("ok") or not (x or {}).get("declared_ident_equal") for x in (v.get("bindings") or {}).values()):
        return "the retained verifier document reports a task binding that is not clean"
    if v.get("anchors") != anchors:
        return "the embedded anchor verdict is not the retained verifier's"
    prod = {k: (x or {}).get("sha256") for k, x in (v.get("bindings") or {}).items()}
    if any(prod.get(k) != h for k, h in (bound.get("bindings") or {}).items()):
        return "the bound task bindings are not the retained verifier's digests"
    return ""


def _verifier_doc(man, bound):
    return _strict_load(os.path.join(man["storage"]["root"], "gate", bound["verify_file"]))


def tracked_unmodified(rel):
    try:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=T1, capture_output=True, text=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=T1, capture_output=True, text=True)
        return a.returncode == 0 and b.returncode == 0
    except Exception:
        return False


def qualification_problem(man, manifest_path, role):
    q = os.path.join(man["storage"]["root"], "gate", f"qualified_{role}_job1.json")
    if not os.path.exists(q):
        return f"no pilot qualification (gate/qualified_{role}_job1.json)", None
    try:
        doc = json.load(open(q))
    except Exception as e:
        return f"the qualification is unreadable ({e})", None
    if doc.get("schema") != QUAL_SCHEMA or doc.get("role") != role or doc.get("qualified_job") != 1 or doc.get("production") is not True:
        return f"the qualification is not a production qualification of {role} job 1", None
    if not _num(doc.get("time")) or doc["time"] > time.time() + 60:
        return "the qualification's time is not a finite past time", None
    rec = doc.get("receipt") or {}
    if rec.get("schema") != WATCH_SCHEMA or rec.get("role") != role or not _num(rec.get("time")):
        return "the qualification's embedded receipt has another schema or role, or no time", None
    if rec.get("alarms") != [] or rec.get("fresh") is not True or rec.get("production") is not True:
        return "the qualification's embedded receipt has alarms, is not fresh or not production", None
    why = (pilot_summary_problem(rec, man=man) or anchors_problem(doc.get("anchors"), (doc.get("bound") or {}).get("anchors_sha256"))
           or verifier_problem(man, doc.get("bound") or {}, doc.get("anchors"), role))
    if not why:
        why = units_problem(man, _verifier_doc(man, doc["bound"]), rec, pilot_job=1)
    if why:
        return f"the qualification: {why}", None
    want = expected_bound(man, manifest_path, role)
    if role == "refit":                                                      # R1: job 1's OWN scope, still the root's bytes
        p1 = json.load(open(os.path.join(man["storage"]["root"], "plans", "job_1.json")))
        own = {str(int(sl["rep"])) for sl in p1["slots"]}
        want = dict(want, bindings={k: v for k, v in want["bindings"].items() if k in own})
        if set(want["bindings"]) != own:
            return f"the root lacks task bindings of job 1's reps {sorted(own - set(want['bindings']))[:5]}", None
    why = bound_problem(doc.get("bound"), want, ["1"])
    if not why and role == "refit":
        p1 = json.load(open(os.path.join(man["storage"]["root"], "plans", "job_1.json")))
        missing = [r for r in planned_reps(p1) if str(r) not in (doc["bound"].get("bindings") or {})]
        if missing:
            why = f"the task bindings of job 1's reps {missing[:5]} are not bound"
    return (f"the qualification: {why}" if why else ""), sha_file(q)


def receipt_problem(man, manifest_path, role, now=None):
    now = time.time() if now is None else now
    ps = sorted(glob.glob(os.path.join(man["storage"]["root"], "gate", f"watch_{role}_*.json")))
    if not ps:
        return "no watch receipt in the gate"
    try:
        r = json.load(open(ps[-1]))
    except Exception as e:
        return f"the newest receipt is unreadable ({e})"
    if r.get("schema") != WATCH_SCHEMA or r.get("role") != role or r.get("production") is not True or r.get("fresh") is not True:
        return "the newest receipt is not a fresh production receipt of this role"
    if r.get("alarms") != []:
        return f"the newest receipt has alarm(s) or no alarm list"
    t = r.get("time")
    if not _num(t) or t > now + 60 or now - t > CEILING_S:
        return f"the newest receipt is not within {CEILING_S:.0f} s"
    why = anchors_problem(r.get("anchors"), (r.get("bound") or {}).get("anchors_sha256")) or verifier_problem(man, r.get("bound") or {}, r.get("anchors"), role)
    if why:
        return f"the newest receipt: {why}"
    want_jobs = expected_bound(man, manifest_path, role)["jobs"]
    if sorted((r.get("jobs") or {})) != sorted(want_jobs):
        return "the newest receipt does not summarise every job of the role"
    vdoc = _verifier_doc(man, r["bound"])
    for n, sj in (r.get("jobs") or {}).items():
        if isinstance(sj, dict) and sum(1 for k in ("disposition", "slot_disposition", "node_disposition", "operational_loss") if k in sj) > 1:
            return f"the newest receipt: job {n} carries more than one disposition"          # REVISION 18 / 19
        if isinstance(sj, dict) and "disposition" in sj:
            why = disposition_problem(man, manifest_path, role, n, sj, r.get("bound") or {}, vdoc.get("units") or {})
        elif isinstance(sj, dict) and "slot_disposition" in sj:                  # REVISION 14
            why = slot_disposition_problem(man, manifest_path, role, n, sj, r.get("bound") or {}) or job_summary_problem(man, n, sj)
        elif isinstance(sj, dict) and "node_disposition" in sj:                  # REVISION 18
            why = node_disposition_problem(man, manifest_path, role, n, sj, r.get("bound") or {}) or job_summary_problem(man, n, sj)
        elif isinstance(sj, dict) and "operational_loss" in sj:                  # REVISION 19
            why = oploss_disposition_problem(man, manifest_path, role, n, sj, r.get("bound") or {}) or job_summary_problem(man, n, sj)
        else:
            why = job_summary_problem(man, n, sj)
        if why:
            return f"the newest receipt: {why}"
    why = units_problem(man, vdoc, r) or transition_problem(man, role, r) or receipt_envelope_problem(man, manifest_path, role, r)
    if why:
        return f"the newest receipt: {why}"
    why = bound_problem(r.get("bound"), expected_bound(man, manifest_path, role), "all")
    if not why and role == "refit":
        why = ec2_receipt_problem(man, r)
    return f"the newest receipt: {why}" if why else ""


def review_problem(man, manifest_path, role, planned):
    p = os.path.join(man["storage"]["root"], "gate", f"review_{role}.json")
    if not os.path.exists(p):
        return "no adopted review of the pilot's actual evidence; run --adopt-review first"
    doc = json.load(open(p))
    if doc.get("schema") != REVIEW_SCHEMA or doc.get("role") != role:
        return "the adopted review has another schema or role"
    full = os.path.join(T1, doc.get("record_path", ""))
    if not os.path.exists(full) or sha_file(full) != doc.get("record_sha256") or not tracked_unmodified(doc.get("record_path", "")):
        return "the adopted review record is not tracked and unmodified in this clone with the adopted SHA-256"
    if not isinstance(doc.get("max_job_number"), int) or any(int(j) > doc["max_job_number"] for j in planned):
        return f"the adopted review covers job numbers up to {doc.get('max_job_number')}"
    why, qsha = qualification_problem(man, manifest_path, role)
    if why:
        return why
    if doc.get("qualification_sha256") != qsha:
        return "the adopted review names another qualification than the one in the gate"
    line = f"ADOPT row19-screen-pilot role={role} qualification={qsha} max_job={doc['max_job_number']}"
    if line not in [l.strip() for l in open(full).read().splitlines()]:
        return "the adopted review record does not carry its ADOPT line"
    return receipt_problem(man, manifest_path, role)


def adopt_review(man, manifest_path, role, record_rel, max_job_number):
    full = os.path.join(T1, record_rel)
    if not os.path.exists(full) or not tracked_unmodified(record_rel):
        return f"REFUSED: {record_rel} is not tracked by git in this clone, or differs from HEAD"
    if not isinstance(max_job_number, int) or max_job_number < 2:
        return "REFUSED: --max-job-number must be an integer of at least 2"
    why, qsha = qualification_problem(man, manifest_path, role)
    if why:
        return f"REFUSED: {why}"
    want = f"ADOPT row19-screen-pilot role={role} qualification={qsha} max_job={int(max_job_number)}"
    if want not in [l.strip() for l in open(full).read().splitlines()]:
        return f"REFUSED: the review record does not contain the line `{want}` (the reviewer's verdict on THIS qualification and scope)"
    p = os.path.join(man["storage"]["root"], "gate", f"review_{role}.json")
    if os.path.exists(p):
        return f"REFUSED: {p} exists; an adopted review is never overwritten"
    doc = dict(schema=REVIEW_SCHEMA, role=role, by="R052", time=time.time(), record_path=record_rel, record_sha256=sha_file(full),
               qualification_sha256=qsha, max_job_number=int(max_job_number))
    tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, p); os.remove(tmp)
    return f"adopted: {record_rel} ({doc['record_sha256'][:16]}) for {role}, qualification {qsha[:16]}, job numbers up to {max_job_number}"


def pin_problems(man, clone):
    bad = []
    for f, want in man["code"]["files"].items():
        p = os.path.join(clone, "workspace_demo", "t1_access", f)
        if not os.path.exists(p) or sha_file(p) != want:
            bad.append(f)
    return bad


def campaign_cap_problem(man, proposal_core_h):
    """REVISION 8: the campaign ledger's cap (60,000 for refit) must hold spent + live + every new full request, checked before
    any reservation (the ledger still refuses each reservation on its own)."""
    lp = os.path.join(man["storage"]["campaign"], "budget.json")
    try:
        if os.path.exists(lp):
            led = _strict_load(lp); cap = led.get("cap_core_h")
            spent = sum(float(e["settled_core_h"]) for e in led["entries"].values() if e.get("state") == "settled")
            live = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
        else:
            cap = float(_phases(man)["phases"][0]["cap_core_h"]); spent = live = 0.0
    except (OSError, ValueError, KeyError, TypeError) as e:
        return f"the campaign ledger cannot be counted ({e})"
    if not (_num(cap) and cap > 0):
        return "the campaign cap is not finite and positive"
    if spent + live + proposal_core_h > cap + 1e-9:
        return f"the campaign cap: spent {spent:.1f} + live {live:.1f} + {proposal_core_h:.1f} proposed > {cap:.0f} core-hours"
    return sub_envelope_problem(man["storage"]["campaign"], proposal_core_h)


def sub_envelope_problem(campaign, proposal_core_h, ctl=None):
    """REVISION 11 (Codex 3dc0daf, S): every sub-envelope of the latest controls version that contains `campaign` must hold
    the committed core-hours (settled + every live reservation) of ALL its campaigns plus this proposal - S and the refit
    share one 60,000 envelope; two separate ledger caps would not aggregate."""
    ctl = ctl or controls()
    for env in ctl["versions"][-1].get("sub_envelopes") or []:
        if campaign not in env["campaigns"]:
            continue
        total = 0.0
        for c in env["campaigns"]:
            lp = os.path.join(c, "budget.json")
            if not os.path.exists(lp):
                continue
            try:
                led = _strict_load(lp)
                total += sum(float(e["settled_core_h"]) if e.get("state") == "settled" else float(e["reserved_core_h"])
                             for e in led["entries"].values())
            except (OSError, ValueError, KeyError, TypeError) as e:
                return f"the sub-envelope {env['name']}: {lp} cannot be counted ({e})"
        if not (_num(env.get("cap_core_h")) and env["cap_core_h"] > 0):
            return f"the sub-envelope {env.get('name')} has no finite positive cap"
        if total + proposal_core_h > env["cap_core_h"] + 1e-9:
            return f"the sub-envelope {env['name']}: {total:.1f} committed + {proposal_core_h:.1f} proposed > {env['cap_core_h']:.0f} core-hours"
    return ""


# ---- REVISION 16 CANDIDATE: the resized screen (designated set, replicate-complete order, crash rule, rescue route) ------------
DESIGNATED = "chpc/row19_screen_designated.json"
DESIG_SCHEMA = "row19-screen-designated-1"
DESIGN_REP_RANGE = (3, 102)            # S = {r in 3..102 : (r - 3) mod 5 in {0, 1, 2}} (Codex 2026-10-17 resize design s.2)
DESIGN_RESIDUES = (0, 1, 2)
DESIGN_N_LENGAU = 13                   # s.3: "the largest 47 IDs in S ... to EC2 ... The smallest 13 remain Lengau's"
DESIGN_INDEX_STOP = 80                 # s.1/s.2: indices 0..79 of each unchanged B = 200 producer stream
DESIGN_MAX_CRASHES = 2                 # s.4: "after two same-envelope fatal allocation/signal crashes, do not issue a third"
ORDER_MARK = "designated-replicate-complete-1"
SCALEUP_SCHEMA = "row19-screen-v16-scaleup-1"
ENV_KEY = ("queue", "cores", "walltime_s", "mem_gb", "nodetype", "deadline_reserve_s")


def designated_rule(reps):
    """The frozen ID-only rule applied to the manifest's declared reps (never to outcomes)."""
    lo, hi = DESIGN_REP_RANGE
    return sorted(int(r) for r in reps if lo <= int(r) <= hi and (int(r) - lo) % 5 in DESIGN_RESIDUES)


def designated_shape_problem(doc, man, man_sha):
    """'' when the designated-coordinates declaration is exactly the adopted design recomputed from this manifest: schema, the
    manifest digest, S by the rule (60 reps, rep 83 included), indices 0..79 within B, the 13/47 provider split, the crash
    threshold 2 and the rescue route declared DISABLED with no resources. Every value is recomputed; none is trusted."""
    if not isinstance(doc, dict) or doc.get("schema") != DESIG_SCHEMA:
        return "it is not a row19-screen-designated-1 declaration"
    if doc.get("manifest_sha256") != man_sha:
        return "it names another manifest"
    S = designated_rule(man["datasets"]["reps"])
    if doc.get("reps") != S or len(S) != 60 or 83 not in S:
        return f"its reps are not S recomputed from the manifest ({len(S)} reps by the rule)"
    ix = doc.get("indices")
    B = int(man["cfg"]["n_boot_refit"])
    if not (isinstance(ix, dict) and _int(ix.get("start")) and _int(ix.get("stop")) and ix["start"] == 0
            and ix["stop"] == DESIGN_INDEX_STOP and ix["stop"] <= B and sorted(ix) == ["start", "stop"]):
        return f"its indices are not exactly 0..{DESIGN_INDEX_STOP - 1} (start 0, stop {DESIGN_INDEX_STOP}) within B = {B}"
    pv = doc.get("providers")
    if not isinstance(pv, dict) or pv.get("lengau_reps") != S[:DESIGN_N_LENGAU] or pv.get("ec2_reps") != S[DESIGN_N_LENGAU:]:
        return f"its provider split is not the smallest {DESIGN_N_LENGAU} IDs of S to Lengau and the largest {len(S) - DESIGN_N_LENGAU} to EC2"
    if pv.get("ec2_epoch") is not None:
        return "it grants EC2 a coordinate set; that is the separate provider-epoch package, never this declaration"
    cr = doc.get("crash_rule")
    if not (isinstance(cr, dict) and _int(cr.get("max_same_envelope_crashes")) and cr["max_same_envelope_crashes"] == DESIGN_MAX_CRASHES):
        return f"its crash rule is not 'no attempt after {DESIGN_MAX_CRASHES} same-envelope crashes'"
    rs = doc.get("rescue")
    if not (isinstance(rs, dict) and rs.get("enabled") is False and rs.get("resources") is None):
        return "its rescue route is not declared DISABLED with no resources (v16 chooses none)"
    if doc.get("first_job_alone") is not True:
        return "it does not hold the first new-order job alone until a scale-up review"
    return ""


def designated(man, manifest_path):
    """(declaration, '') when the latest controls version pins the declaration and its bytes and shape hold; (None, why)."""
    pin = controls()["versions"][-1]["files"].get(DESIGNATED)
    p = os.path.join(T1, DESIGNATED)
    if not _hex64(pin):
        return None, "the controls lineage does not pin the designated-coordinates declaration"
    if not os.path.exists(p) or sha_file(p) != pin:
        return None, "the designated-coordinates declaration is absent or not the lineage's pinned bytes"
    try:
        doc = _strict_load(p)
    except (OSError, ValueError) as e:
        return None, f"the designated-coordinates declaration is unreadable ({e})"
    why = designated_shape_problem(doc, man, sha_file(manifest_path))
    return (None, f"the designated-coordinates declaration: {why}") if why else (dict(doc, _sha256=pin), "")


def designated_coordinates(doc):
    """S x 0..79 (the 4,800 coordinates the screen's terminal look uses)."""
    return {(r, i) for r in doc["reps"] for i in range(doc["indices"]["start"], doc["indices"]["stop"])}


def lengau_scope(doc, claimed):
    """The coordinates Lengau may plan under this declaration: every designated coordinate of the 13 Lengau replicates, plus the
    designated coordinates of the 47 EC2-designated replicates that Lengau has ALREADY claimed (ever planned, any ledger state;
    row19_partition.lengau_claims). s.3: 'All existing claims/completions retain Lengau provenance, including 110 live
    coordinates on EC2-designated replicates'; s.4: 'A lower-index coordinate ever planned by Lengau is not automatically
    transferable merely because its worker died. Let its declared owner finish/rescue it.' Lengau's own planning only ever
    re-plans an existing claim on those replicates, so the claimed set there never grows; their UNCLAIMED coordinates wait for
    the EC2 provider-epoch package and are never planned here."""
    lo, hi = doc["indices"]["start"], doc["indices"]["stop"]
    ec2 = set(doc["providers"]["ec2_reps"])
    own = {(r, i) for r in doc["providers"]["lengau_reps"] for i in range(lo, hi)}
    return own | {(int(r), int(i)) for r, i in claimed if int(r) in ec2 and lo <= int(i) < hi}


def env_key(env):
    return tuple(env.get(k) for k in ENV_KEY) if isinstance(env, dict) else None


def crash_history(receipt, env_of):
    """{(rep, index): [attempt, ...]} from the crashed-worker slot dispositions (REVISION 14) a receipt carries - each recomputed
    and required exact by receipt_problem before any admission - never from a hand list. One attempt per (job, coordinate),
    with its PBS id, the signal and the job's resolved envelope (env_of(job number) -> envelope or None)."""
    out = {}
    for n, sj in sorted(((receipt or {}).get("jobs") or {}).items(), key=lambda kv: int(kv[0])):
        d = sj.get("slot_disposition") if isinstance(sj, dict) else None
        if not isinstance(d, dict) or d.get("kind") != CRASH_KIND:
            continue
        env = env_of(int(n))
        for sl in d.get("slots") or []:
            for i in sl.get("indices") or []:
                out.setdefault((int(sl["rep"]), int(i)), []).append(dict(job=int(n), job_id=d.get("job_id"), signal=sl.get("signal"),
                                                                           envelope=list(env_key(env)) if env else None))
    return out


def crash_excluded(history, env_next, max_crashes=DESIGN_MAX_CRASHES):
    """{coordinate: attempts} whose same-envelope crash count (the envelope the next ordinary attempt would run in) has reached
    the rule's maximum: the ordinary planner never issues them again. An attempt whose envelope is unknown counts as the same
    envelope (fail closed)."""
    k = list(env_key(env_next)) if env_next else None
    return {c: a for c, a in history.items() if sum(1 for x in a if x["envelope"] is None or x["envelope"] == k) >= max_crashes}


def designated_order(doc, done, flight, claimed, excluded, part=None):
    """REPLICATE-COMPLETE order (s.4): the frozen replicate order is ascending rep within S; within a replicate ascending index;
    the remaining designated indices of the earliest unfinished replicates fill a job before the next replicate is touched.
    Validated DONE, every still-owned live/planned coordinate (in flight), every coordinate outside Lengau's scope, every
    crash-excluded coordinate and every coordinate of another provider's partition block are skipped. No speed, success or
    runtime enters the order."""
    import row19_partition as RP
    scope = lengau_scope(doc, claimed)
    return [(r, [i]) for (r, i) in sorted(scope) if (r, i) not in done and (r, i) not in flight and (r, i) not in excluded
            and not RP.blocked(part, r, i)]


def designated_view(doc, done, flight, claimed, history, env_next, part=None):
    """The raw operational view (no statistic): progress over S x 0..79 by provider scope, the crash history and the
    rescue-pending list. Used by the dry run and by the status view."""
    D = designated_coordinates(doc); ec2 = set(doc["providers"]["ec2_reps"])
    scope = lengau_scope(doc, claimed); exc = crash_excluded(history, env_next)
    order = designated_order(doc, done, flight, claimed, exc, part)
    key = lambda c: f"{c[0]}/{c[1]}"
    pending = sorted(c for c in exc if c in D and c not in done)               # a running earlier attempt finishes untouched
    return dict(declaration_sha256=doc.get("_sha256"), designated=len(D), done=len(D & set(done)),
                in_flight=len((D & set(flight)) - set(done)), lengau_plannable=len(order),
                ec2_waiting_unclaimed=len({c for c in D if c[0] in ec2} - scope - set(done) - set(flight)),
                outside_set_history=dict(done=len(set(done) - D), in_flight=len(set(flight) - D - set(done))),
                next_coordinates=[f"{r}/{ix[0]}" for r, ix in order[:24]],
                crash_history={key(c): a for c, a in sorted(history.items())},
                rescue_pending=[dict(coordinate=key(c), crashes=len(exc[c]), jobs=[x["job"] for x in exc[c]], attempt_running=c in flight)
                                for c in pending],
                crash_excluded_outside_set=sorted(key(c) for c in exc if c not in D),
                rescue_route="declared, DISABLED (no resources chosen); rescue-pending coordinates are never admitted by the ordinary planner")


def designated_problem(jobs, doc, done, flight, claimed, excluded, part=None):
    """ADMISSION check (independent of how a plan was built): every planned refit coordinate lies in Lengau's designated scope,
    is not done, not in flight, not crash-excluded and not another provider's; one index per slot."""
    import row19_partition as RP
    scope = lengau_scope(doc, claimed); bad = []
    for j in jobs:
        for s in j["slots"]:
            if len(s.get("indices") or []) != 1:
                bad.append(("slot", j["job"], s.get("slot"))); continue
            c = (int(s["rep"]), int(s["indices"][0]))
            if c not in scope or c in done or c in flight or c in excluded or RP.blocked(part, *c):
                bad.append(c)
    return f"{len(bad)} planned coordinate(s) are outside Lengau's designated scope, done, in flight, crash-excluded or blocked, e.g. {bad[:3]}" if bad else ""


def newest_receipt(man, role):
    """(path, sha256, document) of the newest gate receipt - the same file receipt_problem judges - or (None, None, None)."""
    ps = sorted(glob.glob(os.path.join(man["storage"]["root"], "gate", f"watch_{role}_*.json")))
    if not ps:
        return None, None, None
    try:
        return ps[-1], sha_file(ps[-1]), _strict_load(ps[-1])
    except (OSError, ValueError):
        return ps[-1], None, None


def held_accounting_problem(man, role, receipt):
    """Every CURRENT ledger refit entry with runner exit HELD 4 must be accounted in the planning receipt as a crashed-worker
    slot disposition; otherwise its crash history is unknown and nothing is planned."""
    lp = os.path.join(man["storage"]["campaign"], "budget.json")
    if not os.path.exists(lp):
        return ""
    led = _strict_load(lp); jobs = (receipt or {}).get("jobs") or {}
    held = sorted(int(e["rep"]) for e in led["entries"].values() if e.get("kind") == ROLES[role] and e.get("runner_exit") == HELD_EXIT
                  and not isinstance(e.get("runner_exit"), bool))
    miss = [n for n in held if not isinstance((jobs.get(str(n)) or {}).get("slot_disposition"), dict)
            and not isinstance((jobs.get(str(n)) or {}).get("operational_loss"), dict)]     # REVISION 19: accounted, not a crash
    return f"HELD job(s) {miss[:5]} carry no crashed-worker slot disposition in the planning receipt: crash history unknown" if miss else ""


def marked_plans(man):
    """{job number: plan} of every plan in the root written under the v16 order (ORDER_MARK)."""
    out = {}
    for pp in glob.glob(os.path.join(man["storage"]["root"], "plans", "job_*.json")):
        try:
            d = json.load(open(pp))
        except Exception:
            continue
        if isinstance(d, dict) and d.get("order") == ORDER_MARK:
            out[int(d["job"])] = d
    return out


def scaleup_problem(man, doc, n_jobs):
    """s.4: 'Admit the first prospective Lengau job under the new order alone ... Scale-up stays held until that packing/resource
    review is favourable.' While no adopted scale-up exists: exactly one job per call and no earlier new-order plan. With one:
    the gate file must be valid (scaleup_doc_problem)."""
    if not doc.get("first_job_alone"):
        return ""
    gp = os.path.join(man["storage"]["root"], "gate", "scaleup_refit_v16.json")
    marked = marked_plans(man)
    if not os.path.exists(gp):
        if marked:
            return (f"the first new-order job ({sorted(marked)[0]}) exists; scale-up is held until its review is adopted "
                    f"(--adopt-scaleup reviews/<record>.md)")
        return "" if n_jobs == 1 else "the first new-order job is admitted ALONE: --jobs 1"
    return scaleup_doc_problem(man, doc, marked)


def scaleup_doc_problem(man, doc, marked):
    try:
        g = _strict_load(os.path.join(man["storage"]["root"], "gate", "scaleup_refit_v16.json"))
    except (OSError, ValueError) as e:
        return f"the scale-up adoption is unreadable ({e})"
    if g.get("schema") != SCALEUP_SCHEMA or g.get("designated_sha256") != doc.get("_sha256"):
        return "the scale-up adoption has another schema or names another designated declaration"
    first = sorted(marked)[0] if marked else None
    if first is None or g.get("first_job") != first:
        return "the scale-up adoption does not name the first new-order job"
    full = os.path.join(T1, g.get("record_path", "") or "_none_")
    if not os.path.exists(full) or sha_file(full) != g.get("record_sha256") or not tracked_unmodified(g.get("record_path", "")):
        return "the scale-up review record is not tracked and unmodified with the adopted SHA-256"
    if scaleup_line(g["first_job"], g.get("job_id"), g.get("plan_sha256")) not in [l.strip() for l in open(full).read().splitlines()]:
        return "the scale-up review record does not carry its ADOPT line"
    pp = os.path.join(man["storage"]["root"], "plans", f"job_{first}.json")
    if not os.path.exists(pp) or sha_file(pp) != g.get("plan_sha256"):
        return "the first new-order job's plan is not the reviewed bytes"
    return ""


def scaleup_line(n, job_id, plan_sha):
    return f"ADOPT row19-screen-v16-scaleup first_job={n} job_id={job_id} plan={plan_sha}"


def adopt_scaleup(man, manifest_path, record_rel):
    """Write gate/scaleup_refit_v16.json from a git-tracked, unmodified review record that carries the literal for THE first
    new-order job, which must be SETTLED (its terminal evidence reviewed). Never overwritten."""
    doc, why = designated(man, manifest_path)
    if why:
        return f"REFUSED: {why}"
    full = os.path.join(T1, record_rel)
    if not os.path.exists(full) or not tracked_unmodified(record_rel):
        return f"REFUSED: {record_rel} is not tracked by git in this clone, or differs from HEAD"
    marked = marked_plans(man)
    if not marked:
        return "REFUSED: no new-order job exists to review"
    first = sorted(marked)[0]
    led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))
    hits = [e for e in led["entries"].values() if e.get("kind") == "shard" and e.get("rep") == first]
    if len(hits) != 1 or hits[0].get("state") != "settled" or not hits[0].get("job_id"):
        return f"REFUSED: the first new-order job {first} is not SETTLED with a PBS id"
    psha = sha_file(os.path.join(man["storage"]["root"], "plans", f"job_{first}.json"))
    want = scaleup_line(first, hits[0]["job_id"], psha)
    if want not in [l.strip() for l in open(full).read().splitlines()]:
        return f"REFUSED: the review record does not contain the line `{want}`"
    gp = os.path.join(man["storage"]["root"], "gate", "scaleup_refit_v16.json")
    if os.path.exists(gp):
        return f"REFUSED: {gp} exists; a scale-up adoption is never overwritten"
    g = dict(schema=SCALEUP_SCHEMA, by="R052", time=time.time(), designated_sha256=doc["_sha256"], first_job=first,
             job_id=hits[0]["job_id"], plan_sha256=psha, record_path=record_rel, record_sha256=sha_file(full))
    tmp = gp + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(g, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, gp); os.remove(tmp)
    return f"adopted scale-up after new-order job {first} ({hits[0]['job_id']}), record {record_rel}"


def rescue_route_problem(doc):
    """The separate rescue route (s.4: 'one prospective, budgeted rescue lane: same dataset/seed/folds/... lower packing and
    larger measured headroom, with parity/resource qualification') is DECLARED here and DISABLED: no host, packing or resource
    envelope has been chosen or qualified, so it always refuses in v16. Enabling it is a separate reviewed amendment."""
    rs = (doc or {}).get("rescue") or {}
    if rs.get("enabled") is not True or rs.get("resources") is None:
        return "the rescue route is declared but DISABLED (no rescue resources chosen or qualified); a separate reviewed amendment enables it"
    return "the rescue route has no implementation in controls v16"


def gate_problem(man, manifest_path, role, used, pilot, n_jobs, jobs, walltime_s, proposal_core_h=None):
    root = man["storage"]["root"]
    if os.path.exists(os.path.join(root, "STOP")):
        return "a STOP file is present in the role's root"
    why = controls_problem() or cap_problem(man)
    if why:
        return why
    why = seed_domain_problem(man)
    if why:
        return why
    reps = sorted({r for j in jobs for r in planned_reps(j)}) if jobs else []
    why = identity_problem(man, reps)
    if why:
        return why
    proposal = proposal_core_h if proposal_core_h is not None else len(jobs) * int(man["pbs"]["cores"]) * walltime_s / 3600.0
    why = funding_problem(man, proposal) or campaign_cap_problem(man, proposal)
    if why:
        return why
    if pilot:
        if used:
            return f"--pilot is only for the role's first job; the ledger already holds job(s) {sorted(used)}"
        return "" if n_jobs == 1 else "the pilot is exactly one job"
    if not used:
        return "the role's first job is its pilot: say --pilot"
    return review_problem(man, manifest_path, role, [j["job"] for j in jobs])


def refit_pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    """The packed refit job: the UNCHANGED row19_shard.py job-start / worker / job-end, with the screen's own job and file names
    (row19_screen_refit_<n>) so nothing of the development shard route's jobs/ files is ever overwritten."""
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = f"$T/t1py chpc/row19_shard.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START"
    L = ["#!/bin/bash", f"#PBS -N t1_screen_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_screen_refit_{n}.out", f"#PBS -e {toolchain}/jobs/row19_screen_refit_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19 stage 2: screen refit job {n}, {len(plan['slots'])} single-core workers, one resample index per record (row19_shard.py unchanged).",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  screen refit job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_shard.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?", 'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        L.append(f"$T/t1py chpc/row19_shard.py worker --manifest {manifest_rel} --rep {s['rep']} --indices {','.join(str(i) for i in s['indices'])} "
                 f"--slot {s['slot']} --job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", end, "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def orig_pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = f"$T/t1py chpc/row19_screen_orig.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START"
    L = ["#!/bin/bash", f"#PBS -N t1_sorig_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_screen_orig_{n}.out", f"#PBS -e {toolchain}/jobs/row19_screen_orig_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19 stage 2: screen original job {n}, {len(plan['slots'])} single-core workers, one lossless original each.",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  screen original job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_screen_orig.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?", 'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        L.append(f"$T/t1py chpc/row19_screen_orig.py worker --manifest {manifest_rel} --reps {','.join(str(r) for r in s['reps'])} --slot {s['slot']} "
                 f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", end, "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=sorted(ROLES))
    ap.add_argument("--jobs", type=int, default=None); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--adopt-review", default=None); ap.add_argument("--max-job-number", type=int, default=None)
    ap.add_argument("--raise-cap", type=float, default=None); ap.add_argument("--note", default=None)
    ap.add_argument("--retire-pending", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--adopt-scaleup", default=None); ap.add_argument("--rescue", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); role = a.role
    if man.get("role") != role:
        print(f"REFUSED: {a.manifest} is the {man.get('role')} manifest, not {role}"); return 2
    if a.rescue:                                                              # REVISION 16: declared, disabled
        doc, why = designated(man, a.manifest) if role == "refit" else (None, "the rescue route is refit-only")
        print(f"REFUSED: {why or rescue_route_problem(doc)}"); return 2
    if a.adopt_scaleup is not None:
        if role != "refit":
            print("REFUSED: scale-up adoption is refit-only"); return 2
        out = adopt_scaleup(man, a.manifest, a.adopt_scaleup); print(out)
        return 0 if out.startswith("adopted") else 2
    if a.adopt_review is not None:
        out = adopt_review(man, a.manifest, role, a.adopt_review, a.max_job_number); print(out)
        return 0 if out.startswith("adopted") else 2
    if a.raise_cap is not None:
        if not a.note or len(a.note.strip()) < 8:
            print("REFUSED: a cap raise needs the owner's ruling as --note"); return 2
        with PG.programme_lock(PG.programme_funding(man)):
            new = float(a.raise_cap); bp = _phases_path(man)
            try:
                b = _phases(man); cur = float(_strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))["cap_core_h"])
            except (ValueError, OSError, KeyError) as e:
                print(f"REFUSED: the phases or the ledger cannot be read ({e})"); return 2
            live = [x for x in b["phases"] if not x.get("retired")]
            resume = live[-1].get("pending") and abs(float(live[-1]["cap_core_h"]) - new) < 1e-9
            if resume:
                why = predecessor_problem(man, live, applied_ok=True)
                if why:
                    print(f"REFUSED: {why}; nothing changed"); return 2
            if not resume:
                why = cap_problem(man)
                if why:
                    print(f"REFUSED: {why}"); return 2
                if not (_num(new) and new >= cur + 1.0):
                    print(f"REFUSED: the new cap {new} is not finite and at least one core-hour above the current {cur}"); return 2
                b["phases"].append(dict(cap_core_h=new, note=a.note, t=time.time(), campaign=man["storage"]["campaign"], pending=True))
                _durable_write(bp, b)
            if resume and cur > new + 1e-9:
                print(f"REFUSED: the ledger already holds {cur}, above the pending phase {new}; reconcile by hand (recorded), nothing changed"); return 2
            if cur < new:
                ledger_for(man).raise_cap(new, a.note)
            led = _strict_load(os.path.join(man["storage"]["campaign"], "budget.json")); hist = led.get("cap_history") or []
            if not (_num(led.get("cap_core_h")) and abs(led["cap_core_h"] - new) < 1e-9 and hist and _num(hist[-1].get("new")) and abs(hist[-1]["new"] - new) < 1e-9):
                print(f"REFUSED: the ledger's cap {led.get('cap_core_h')} and its latest history entry do not certify {new}; the phase stays pending"); return 2
            b = _phases(man); [x for x in b["phases"] if not x.get("retired")][-1]["pending"] = False; _durable_write(bp, b)
        print(f"cap {'resumed and ' if resume else ''}raised to {new:.0f} (ledger cap_history and {man['budget']['admission']} committed; commit the budget file)"); return 0
    if a.retire_pending:
        if not a.note or len(a.note.strip()) < 8:
            print("REFUSED: retiring a pending phase needs a --note"); return 2
        with PG.programme_lock(PG.programme_funding(man)):
            b = _phases(man); live = [x for x in b["phases"] if not x.get("retired")]
            if not live[-1].get("pending") or len(live) < 2:
                print("REFUSED: no pending phase to retire"); return 2
            why = predecessor_problem(man, live, applied_ok=False)
            if why:
                print(f"REFUSED: {why}; nothing changed"); return 2
            live[-1].update(retired=True, retired_note=a.note, retired_t=time.time()); _durable_write(_phases_path(man), b)
        print("pending phase retired (kept in the history)"); return 0
    n_jobs = 1 if a.pilot else a.jobs
    if not n_jobs or n_jobs < 1:
        print("say --pilot or --jobs N"); return 2
    queue = man["pbs"]["queue"]; walltime_s = float(man["pbs"]["walltime_h"]) * 3600.0
    toolchain, clone, root = man["shard"]["toolchain"], man["shard"]["clone"], man["storage"]["root"]
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    manifest_rel = os.path.relpath(os.path.abspath(a.manifest), os.path.join(clone, "workspace_demo", "t1_access"))
    with PG.programme_lock(PG.programme_funding(man)), open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: another submitter holds the plan lock"); return 2
        done, flight, used, problems = evidence(man, role)
        print(f"{role}: done {len(done)}, in flight {len(flight)}")
        if problems:
            print(f"HELD: {len(problems)} problem(s) in the evidence:"); [print("   -", p) for p in problems[:10]]; return 2
        try:
            part = partition(man, a.manifest) if role == "refit" else None
        except Exception as e:
            print(f"HELD: the provider partition cannot be trusted: {e}"); return 2
        if part is not None:
            import row19_partition as _RP                                     # v17: schema 2 has no k / indices (an explicit set)
            print(f"provider partition epoch {part['epoch']}: {part['provider']} owns "
                  + (f"{part['owned_count']} explicit coordinates (schema 2, owned {part['owned_sha256'][:12]})" if part.get("schema") == _RP.SCHEMA2
                     else f"indices {part['indices'][0]}..{part['indices'][-1]} (k {part['k']})"))
        why_act = activation_problem_v10(man, a.manifest, part)
        if why_act:
            print(f"HELD: {why_act}"); return 2
        order = desig = None; excluded, claimed, rpath, rsha = {}, set(), None, None
        if role == "refit":                                                   # REVISION 16: the designated, replicate-complete planner
            if a.pilot:
                print("REFUSED: the refit pilot was admitted and adopted long ago; v16 never plans a refit pilot"); return 2
            desig, why = designated(man, a.manifest)
            if why:
                print(f"HELD: {why}"); return 2
            import row19_partition as RP
            _ld, claimed, cprob = RP.lengau_claims(man)
            if cprob:
                print(f"HELD: Lengau's claims are not establishable: {cprob[:3]}"); return 2
            rpath, rsha, rdoc = newest_receipt(man, role)
            if rdoc is None:
                print("HELD: no readable gate receipt: the crash history (slot dispositions) cannot be established"); return 2
            why = held_accounting_problem(man, role, rdoc)
            if why:
                print(f"HELD: {why}"); return 2
            used_next = (max(used) + 1) if used else 1
            env_next, w = resolve_envelope(man, a.manifest, role, used_next)
            if w:
                print(f"HELD: {w}"); return 2
            history = crash_history(rdoc, lambda m: resolve_envelope(man, a.manifest, role, m)[0])
            excluded = crash_excluded(history, env_next)
            order = designated_order(desig, done, flight, claimed, excluded, part)
            view = designated_view(desig, done, flight, claimed, history, env_next, part)
            print(f"designated S x 0..{DESIGN_INDEX_STOP - 1} ({desig['_sha256'][:12]}): {view['designated']} coordinates, done {view['done']}, "
                  f"in flight {view['in_flight']}, Lengau plannable {view['lengau_plannable']}, EC2-designated unclaimed (wait for the EC2 "
                  f"epoch package) {view['ec2_waiting_unclaimed']}; crash history from {os.path.basename(rpath)} ({str(rsha)[:12]})")
            for x in view["rescue_pending"]:
                print(f"  RESCUE-PENDING {x['coordinate']}: {x['crashes']} same-envelope crash(es) in jobs {x['jobs']}; no further ordinary attempt"
                      + ("; an earlier attempt is still running (untouched)" if x["attempt_running"] else ""))
        jobs, left = plan_jobs(man, role, n_jobs, done, flight, used, part, order=order)
        envs, why = {}, partition_problem(jobs, part)
        if role == "refit":
            why = why or designated_problem(jobs, desig, done, flight, claimed, excluded, part) or scaleup_problem(man, desig, n_jobs)
            keys = {env_key(resolve_envelope(man, a.manifest, role, int(j["job"]))[0]) for j in jobs}
            if not why and keys and keys != {env_key(env_next)}:
                why = "the planned jobs do not all run in the envelope the crash rule was evaluated for"
        for j in jobs:                                                        # REVISION 8: each NEW job's resolved envelope
            env, w = resolve_envelope(man, a.manifest, role, int(j["job"]))
            why = why or w; envs[j["job"]] = env
        proposal = sum(envelope_core_h(envs[j["job"]]) for j in jobs) if not why else None
        why = why or gate_problem(man, a.manifest, role, used, a.pilot, n_jobs, jobs, walltime_s, proposal_core_h=proposal)
        if not why and role == "refit":                                       # REVISION 16: the gate judged the SAME receipt
            p2, s2, _ = newest_receipt(man, role)
            if (p2, s2) != (rpath, rsha):
                why = "a newer receipt arrived between planning and the gate; re-run so planning and the gate read one receipt"
        pins = pin_problems(man, clone)
        if pins and not why:
            why = f"the manifest's pins do not hold in the clone the jobs run from: {pins}"
        print(f"planned {len(jobs)} job(s), {sum(len(s.get('indices', s.get('reps', []))) for j in jobs for s in j['slots'])} units; {left} not in this call")
        for j in jobs[:3]:
            print(f"  job {j['job']}: " + "; ".join(f"slot {s['slot']} " + (f"rep {s['rep']} {s['indices']}" if role == 'refit' else f"reps {s['reps']}") for s in j["slots"][:4]) + " ...")
            ev = envs.get(j["job"])
            if ev:
                print(f"    envelope: {ev['queue']} {ev['cores']} cores x {ev['walltime_s']/3600:.0f} h ({envelope_core_h(ev):.0f} core-h), {ev['mem_gb']} GB, "
                      f"reserve {ev['deadline_reserve_s']} s - {ev['source']}")
        if a.dry_run:
            print(f"DRY RUN; the gate {'would REFUSE: ' + why if why else 'would admit this submission'}"); return 0
        if why:
            print(f"REFUSED by the screen gate: {why}"); return 2
        L = ledger_for(man)
        os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
        for j in jobs:
            env = envs[j["job"]]; cores = env["cores"]; wj = env["walltime_s"]; qj = env["queue"]
            build = refit_pbs_script if role == "refit" else orig_pbs_script
            why = pbs_request_problem(build(man, j, "TOKEN", wj, qj, toolchain, clone, manifest_rel), env)
            if why:
                print(f"{role} job {j['job']}: REFUSED before reserving: {why}"); return 2
            token, t = L.reserve(ROLES[role], int(j["job"]), cores, wj, root, f"row19_screen_admit {role} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
            pp = os.path.join(root, "plans", f"job_{j['job']}.json")
            pdoc = dict(j, queue=qj, walltime_s=wj, token=token, created=time.time())
            if env["source"] != "manifest":
                pdoc["envelope"] = env
            if role == "refit":                                               # REVISION 16: the order and declaration it was planned under
                pdoc.update(order=ORDER_MARK, designated_sha256=desig["_sha256"])
            with open(pp, "w") as fh:
                json.dump(pdoc, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
            entry = [e for e in _strict_load(os.path.join(man["storage"]["campaign"], "budget.json"))["entries"].values() if e.get("token") == token]
            why = envelope_problem(man, a.manifest, role, j["job"], _strict_load(pp), entry[0] if len(entry) == 1 else None)
            sp = os.path.join(toolchain, "jobs", f"row19_screen_{role}_{j['job']}.pbs")
            script = build(man, j, token, wj, qj, toolchain, clone, manifest_rel)
            why = why or pbs_request_problem(script, env)
            if why:
                print(f"{role} job {j['job']}: HELD before qsub: {why}; reservation {token} stays reserved and unbound"); return 1
            open(sp, "w").write(script)
            r = subprocess.run(["qsub", sp], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"{role} job {j['job']}: qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved and unbound"); return 1
            job_id = r.stdout.strip(); L.bind(token, job_id)
            print(f"{role} job {j['job']}: reserved {token} ({cores} x {wj/3600:.0f} h = {envelope_core_h(env):.0f} core-h; spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), submitted {job_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

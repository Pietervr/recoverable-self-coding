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

PLAN: refit - index-major round robin over the declared reps (index 0 of reps 3..102, then index 1, ...), `cores` slots a
job, so the screen's first job is exactly reps 3..26 at index 0; orig - the missing reps in order, `cores` a job.

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


def plan_jobs(man, role, n_jobs, done, flight, used, part=None):
    cores = int(man["pbs"]["cores"]); reps = [int(r) for r in man["datasets"]["reps"]]
    if role == "refit":
        B = int(man["cfg"]["n_boot_refit"])
        import row19_partition as RP                                          # REVISION 10: never plan another provider's block
        order = [(r, [i]) for i in range(B) for r in reps if (r, i) not in done and (r, i) not in flight and not RP.blocked(part, r, i)]
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
        if not (_num(sj.get("requested_walltime_s")) and abs(sj["requested_walltime_s"] - w) <= 1.0):
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


def plan_slots(man, n):
    p = os.path.join(man["storage"]["root"], "plans", f"job_{n}.json")
    return len(json.load(open(p))["slots"]) if os.path.exists(p) else None


def job_summary_problem(man, n, s, pilot=False):
    """R2: one job summary against its plan. Queued or running jobs pass; a terminal job must be complete and clean."""
    if not isinstance(s, dict):
        return f"job {n}: no summary"
    if pilot and s.get("disposition") is not None:
        return f"job {n}: a dispositioned job never qualifies a pilot"
    if s.get("state") in ("Q", "R", "H", "W", "B"):
        return "" if not pilot else f"job {n} is not terminal"
    want = plan_slots(man, n)
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
        if isinstance(sj, dict) and "disposition" in sj:
            why = disposition_problem(man, manifest_path, role, n, sj, r.get("bound") or {}, vdoc.get("units") or {})
        else:
            why = job_summary_problem(man, n, sj)
        if why:
            return f"the newest receipt: {why}"
    why = units_problem(man, vdoc, r) or transition_problem(man, role, r) or receipt_envelope_problem(man, manifest_path, role, r)
    if why:
        return f"the newest receipt: {why}"
    why = bound_problem(r.get("bound"), expected_bound(man, manifest_path, role), "all")
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
    return ""


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
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); role = a.role
    if man.get("role") != role:
        print(f"REFUSED: {a.manifest} is the {man.get('role')} manifest, not {role}"); return 2
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
            print(f"provider partition epoch {part['epoch']}: {part['provider']} owns indices {part['indices'][0]}..{part['indices'][-1]} (k {part['k']})")
        jobs, left = plan_jobs(man, role, n_jobs, done, flight, used, part)
        envs, why = {}, partition_problem(jobs, part)
        for j in jobs:                                                        # REVISION 8: each NEW job's resolved envelope
            env, w = resolve_envelope(man, a.manifest, role, int(j["job"]))
            why = why or w; envs[j["job"]] = env
        proposal = sum(envelope_core_h(envs[j["job"]]) for j in jobs) if not why else None
        why = why or gate_problem(man, a.manifest, role, used, a.pilot, n_jobs, jobs, walltime_s, proposal_core_h=proposal)
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

"""Row 19 screen on EC2, provider epoch 2 - CANDIDATE, not adopted: the ONE reviewed classification of a worker's
non-completion and of the qualified packing shape, shared by every consumer so they cannot disagree (Codex review
reviews/2026-10-17_e2_p80r_codex_review.md A1, A2, A3, ruling 7).

  consumers  chpc/row19_ec2_ingest.py REVISION 6 (Lengau: which unproduced slots may be published around),
             aws_ec2/prod_authority.py REVISION 6 (Mac: `ack` refuses an unclassified unproduced outcome; the EC2 crash
             rule counts exactly the fatal-signal class), aws_ec2/prod_launch.py REVISION 6 (Mac: the production plan's
             replicate concentration), and the epoch-2 qualifier / release branch when it is built (R4').
  promotion  to chpc/ (and the Lengau controller tree) beside the ingestion; controls v17 must pin it with the other
             REVISION-6 helpers, and the epoch-2 RELEASE_CODE must bind it.

Pure: no I/O and no scientific import.

A2  fatal signal  an integer outcome 129..159 (128 + signal 1..31) is a worker process ended by a signal. Ingestion admits
                  such a slot as unproduced only WITHOUT a status (the crashed-worker signature), and EVERY outcome of this
                  class counts toward the two same-envelope crash rule - SIGTRAP 133, SIGFPE 136, SIGUSR1 138 as much as
                  SIGSEGV 139. No external-interruption exemption exists: none has evidence of its cause. Exit 137 proves
                  SIGKILL only; it is never described as the OOM killer without host evidence.
A1  orderly left  a PRESENT status of an unproduced slot (the RESUME 75 branch, or a censored slot whose worker still wrote
                  one) must satisfy the full accounting of the worker's own orderly deadline/STOP exit: this attempt, slot,
                  rep, task identity, exactly this one index left (none new or resumed), exit 75 with one of the worker's
                  two orderly reasons, finite non-negative times and a positive maxrss within the memory stop. A HELD exit 4,
                  a memory/identity/exception reason or contradictory accounting holds the attempt, censor marker or not.
A3  packing       the production plan of epoch 2 may put at most QUALIFIED_REP_SLOTS = 61 of its 76 workers (work AND
                  sentinels) on any one replicate: the concentration E2Q1 is declared to run (52 work + 9 Lengau duplicates on
                  its first replicate, QUALIFICATION_E2.md). The allocator therefore takes at most 61 - 4 = 57 work
                  coordinates of one replicate per batch, so even four sentinels on that replicate stay inside the shape.
R4' (ruling 7)    a qualification instance passes R4' only with at most QUAL_MAX_UNPRODUCED = 3 non-completed slots of ALL
                  roles (work, duplicates, sentinels), each of a qualifying kind."""
import math, re

CENSORED = "censored at the upload deadline"
WORKER_DONE, WORKER_RESUME, WORKER_HELD = 0, 75, 4                 # = row19_shard DONE / RESUME / HELD
FATAL_SIGNAL_EXITS = frozenset(range(129, 160))                    # 128 + signal 1..31
STOP_REASON = "stop requested (STOP file)"                         # row19_shard.cmd_worker, the two orderly RESUME reasons
DEADLINE_REASON = re.compile(r"deadline: -?\d+ s left, \d+ s needed for the next resample")
QUALIFIED_REP_SLOTS = 61                                           # E2Q1: 52 work + 9 duplicates on one replicate
QUAL_MAX_UNPRODUCED = 3                                            # R4': of all 76 qualification slots


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def is_fatal_signal(oc):
    return _int(oc) and oc in FATAL_SIGNAL_EXITS


def kind(oc):
    """The class of a non-zero worker outcome: 'fatal_signal', 'resume', 'censored', or None (never publishable around)."""
    if is_fatal_signal(oc):
        return "fatal_signal"
    if _int(oc) and oc == WORKER_RESUME:
        return "resume"
    if oc == CENSORED:
        return "censored"
    return None


def counts_toward_crash_rule(oc):
    """True for EVERY outcome ingestion admits as a crashed worker (A2: one set for ingestion and the crash counter)."""
    return kind(oc) == "fatal_signal"


def orderly_reason(reason):
    return isinstance(reason, str) and (reason == STOP_REASON or DEADLINE_REASON.fullmatch(reason) is not None)


def left_status_problem(st, attempt_id, slot, rep, index, ident, mem_stop_bytes):
    """'' for the worker's own orderly deadline/STOP status that LEFT exactly this one coordinate (A1); otherwise why not."""
    if not isinstance(st, dict):
        return "status not an object"
    want = dict(job=attempt_id, slot=slot, rep=rep, ident=ident, indices=[index], left=[index], new=[], resumed=[], exit=WORKER_RESUME)
    for k, v in want.items():
        if st.get(k) != v or (isinstance(v, int) and not _int(st.get(k))):
            return f"status {k} {st.get(k)!r} is not {v!r}"
    if not orderly_reason(st.get("reason")):
        return f"status reason {st.get('reason')!r} is not an orderly deadline/STOP exit"
    for k in ("wall_s", "cpu_s", "started", "ended"):
        if not _num(st.get(k)) or st[k] < 0:
            return f"status {k} not finite and non-negative"
    if not _int(st.get("maxrss")) or not 0 < st["maxrss"] <= mem_stop_bytes:
        return f"status maxrss {st.get('maxrss')!r} not positive or above the memory stop"
    return ""


def rep_concentration(slots):
    """{rep: number of slots of ANY role on that replicate} for a plan's slot list."""
    out = {}
    for s in slots:
        out[int(s["rep"])] = out.get(int(s["rep"]), 0) + 1
    return out


def concentration_problem(slots, cap=QUALIFIED_REP_SLOTS):
    """'' when no replicate carries more than `cap` slots (work + duplicates + sentinels)."""
    c = rep_concentration(slots)
    over = {r: n for r, n in sorted(c.items()) if n > cap}
    return f"replicate concentration {over} above the qualified {cap} workers per replicate" if over else ""


def qualification_unproduced_problem(slots, outcomes):
    """R4' (ruling 7): '' when at most QUAL_MAX_UNPRODUCED slots of all roles did not end with int 0, each of a qualifying kind."""
    bad = {int(s["slot"]): outcomes.get(f"w_slot{s['slot']}") for s in slots
           if not (_int(outcomes.get(f"w_slot{s['slot']}")) and outcomes.get(f"w_slot{s['slot']}") == WORKER_DONE)}
    if len(bad) > QUAL_MAX_UNPRODUCED:
        return f"{len(bad)} non-completed qualification slots (> {QUAL_MAX_UNPRODUCED} of all roles)"
    unk = {sl: oc for sl, oc in bad.items() if kind(oc) is None}
    return f"non-completed qualification slots of no qualifying kind: {unk}" if unk else ""

"""Ledger row 19: ONE campaign counter for every root, control and stage 0 (Codex 523249d condition C; e44f804 R1).

The ledger is `<campaign>/budget.json`, read fresh and rewritten atomically under an exclusive lock on
`<campaign>/budget.lock` for every change (never a retained snapshot). Core-hours are RESERVED before a job is
submitted (`reserve`, by the operator on the login node, with the filled PBS request's cores and walltime), BOUND to
the PBS job id after `qsub`, marked LIVE by the runner at start - which must present the same cores and walltime as
its reservation - and SETTLED only from scheduler-accounted allocated time (`settle`, by the operator from
`qstat -xf`). Settled is terminal: a settled entry is never reopened and a job id binds to exactly one token. A killed
or vanished job keeps its full reservation until it is settled. Every number is finite and positive (reservations)
or finite and non-negative (charges); the manifest's cap must equal the ledger's; an already over-cap campaign admits
nothing. Spent + live + a new reservation must stay within the cap. Reservations per (kind, rep) are capped (the
declared maximum submissions per dataset).

    python chpc/row19_ledger.py --campaign DIR [--cap 1500] reserve --kind main|c1|c2|c3|stage0 --rep N --cores 1 --walltime-s S --root R
    python chpc/row19_ledger.py --campaign DIR bind --token T --job-id J
    python chpc/row19_ledger.py --campaign DIR settle --job-id J --walltime-s S --cores C [--note "qstat -xf ..."]
    python chpc/row19_ledger.py --campaign DIR show
    python chpc/row19_ledger.py --campaign DIR stop [--rep N] / stop-clear [--rep N]
"""
import os, sys, json, time, fcntl, secrets, argparse, contextlib, math

KINDS = ("main", "c1", "c2", "c3", "stage0")
MAX_PER_KIND_REP = {"main": 4, "c1": 1, "c2": 1, "c3": 2, "stage0": 1}
STATES = ("reserved", "bound", "live", "settled")
LIVE = ("reserved", "bound", "live")


def write_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    d = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def _pos(x, name):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)) or float(x) <= 0:
        raise RuntimeError(f"refused: {name} must be a finite positive number, not {x!r}")
    return float(x)


def _nonneg(x, name):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)) or float(x) < 0:
        raise RuntimeError(f"refused: {name} must be a finite non-negative number, not {x!r}")
    return float(x)


class CampaignLedger:
    def __init__(self, campaign: str, cap_core_h: float | None = None):
        self.dir = campaign
        os.makedirs(campaign, exist_ok=True)
        self.path = os.path.join(campaign, "budget.json")
        self.lock_path = os.path.join(campaign, "budget.lock")
        self.cap_arg = None if cap_core_h is None else _pos(cap_core_h, "cap")

    @contextlib.contextmanager
    def locked(self, timeout_s: float = 60.0):
        """Exclusive lock, FRESH read, structural validation, yield the state, atomic write on a clean exit."""
        fh = open(self.lock_path, "a+")
        t0 = time.time()
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
            except OSError:
                if time.time() - t0 > timeout_s:
                    fh.close(); raise RuntimeError(f"ledger lock {self.lock_path} not acquired within {timeout_s:.0f} s")
                time.sleep(0.05)
        try:
            if os.path.exists(self.path):
                state = json.load(open(self.path))
                self.validate(state)
                if self.cap_arg is not None and abs(float(state["cap_core_h"]) - self.cap_arg) > 1e-9:
                    raise RuntimeError(f"refused: the ledger's cap {state['cap_core_h']} differs from the declared cap {self.cap_arg}")
            else:
                if self.cap_arg is None:
                    raise RuntimeError("the ledger does not exist; create it with --cap once")
                state = dict(cap_core_h=self.cap_arg, entries={})
            yield state
            self.validate(state)
            write_atomic(self.path, state)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()

    @staticmethod
    def validate(state):
        """Structurally valid: a finite positive cap, declared states, finite numbers, one token per job id."""
        if not isinstance(state, dict) or not isinstance(state.get("entries"), dict):
            raise RuntimeError("refused: ledger is not an object with entries")
        _pos(state.get("cap_core_h"), "ledger cap")
        jobs = {}
        for tok, e in state["entries"].items():
            if e.get("state") not in STATES or e.get("kind") not in KINDS or e.get("token") != tok:
                raise RuntimeError(f"refused: entry {tok} has an undeclared state or kind")
            _pos(e.get("cores"), f"{tok}.cores"); _pos(e.get("walltime_s"), f"{tok}.walltime_s"); _pos(e.get("reserved_core_h"), f"{tok}.reserved_core_h")
            if e["state"] == "settled":
                _nonneg(e.get("settled_core_h"), f"{tok}.settled_core_h")
            jid = e.get("job_id")
            if jid is not None:
                if jid in jobs:
                    raise RuntimeError(f"refused: job id {jid} bound to two tokens ({jobs[jid]}, {tok})")
                jobs[jid] = tok

    @staticmethod
    def totals(state):
        spent = sum(float(e["settled_core_h"]) for e in state["entries"].values() if e["state"] == "settled")
        live = sum(float(e["reserved_core_h"]) for e in state["entries"].values() if e["state"] in LIVE)
        return spent, live

    def reserve(self, kind, rep, cores, walltime_s, root, attempt_note=""):
        if kind not in KINDS:
            raise RuntimeError(f"refused: kind must be one of {KINDS}")
        cores = _pos(cores, "cores"); walltime_s = _pos(walltime_s, "walltime_s")
        if int(cores) != cores:
            raise RuntimeError("refused: cores must be an integer")
        with self.locked() as st:
            cap = float(st["cap_core_h"])
            spent, live = self.totals(st)
            if spent + live > cap + 1e-9:
                raise RuntimeError(f"refused: the campaign is already over its cap (spent {spent:.1f} + live {live:.1f} > {cap:.0f})")
            mine = cores * walltime_s / 3600.0
            same = [e for e in st["entries"].values() if e["kind"] == kind and e.get("rep") == rep]
            if len(same) >= MAX_PER_KIND_REP[kind]:
                raise RuntimeError(f"refused: {len(same)} reservation(s) already exist for {kind} rep {rep} (maximum {MAX_PER_KIND_REP[kind]})")
            if spent + live + mine > cap + 1e-9:
                raise RuntimeError(f"refused: spent {spent:.1f} + live {live:.1f} + this {mine:.1f} > cap {cap:.0f} core-hours")
            token = secrets.token_hex(6)
            st["entries"][token] = dict(token=token, kind=kind, rep=rep, root=root, cores=int(cores), walltime_s=walltime_s,
                                        reserved_core_h=mine, attempt=len(same) + 1, state="reserved", job_id=None,
                                        created=time.time(), note=attempt_note)
            return token, dict(spent=spent, live=live + mine, cap=cap, attempt=len(same) + 1)

    def bind(self, token, job_id):
        if not isinstance(job_id, str) or not job_id:
            raise RuntimeError("refused: job id must be a non-empty string")
        with self.locked() as st:
            e = st["entries"].get(token)
            if e is None:
                raise RuntimeError(f"refused: no reservation {token}")
            if e["state"] == "settled":
                raise RuntimeError(f"refused: reservation {token} is settled (terminal)")
            if e.get("job_id") == job_id:
                return dict(e)                                               # idempotent
            if e.get("job_id") is not None:
                raise RuntimeError(f"refused: reservation {token} is already bound to job {e['job_id']}")
            if any(x.get("job_id") == job_id for x in st["entries"].values()):
                raise RuntimeError(f"refused: job id {job_id} is already bound to another token")
            e.update(state="bound", job_id=job_id, bound_at=time.time())
            return dict(e)

    def runner_start(self, token, job_id, kind, rep, root, cores, walltime_s):
        """The runner's admission: the reservation must exist, be bound to THIS job id (or be unbound and get bound now),
        describe this kind, rep and root, and carry the same cores and walltime as this job's filled request."""
        cores = _pos(cores, "cores"); walltime_s = _pos(walltime_s, "walltime_s")
        with self.locked() as st:
            spent, live = self.totals(st)
            if spent + live > float(st["cap_core_h"]) + 1e-9:
                raise RuntimeError("the campaign is over its cap; nothing is admitted")
            e = st["entries"].get(token)
            if e is None:
                raise RuntimeError(f"no reservation {token} in {self.path}")
            if e["state"] == "settled":
                raise RuntimeError(f"reservation {token} is settled (terminal)")
            if e["kind"] != kind or e.get("rep") != rep or e.get("root") != root:
                raise RuntimeError(f"reservation {token} is for {e['kind']} rep {e.get('rep')} root {e.get('root')}, not this job")
            if int(e["cores"]) != int(cores) or abs(float(e["walltime_s"]) - walltime_s) > 1.0:
                raise RuntimeError(f"reservation {token} is for {e['cores']} core(s) x {e['walltime_s']:.0f} s, this job is {int(cores)} x {walltime_s:.0f} s")
            if e.get("job_id") is None:
                if any(x.get("job_id") == job_id for x in st["entries"].values()):
                    raise RuntimeError(f"job id {job_id} is already bound to another token")
                e.update(state="bound", job_id=job_id, bound_at=time.time())
            if e.get("job_id") != job_id:
                raise RuntimeError(f"reservation {token} is bound to job {e.get('job_id')}, not {job_id}")
            e.update(state="live", runner_started=time.time())
            return dict(e)

    def runner_end(self, token, wall_s, exit_code):
        """Record the runner's own wall and exit; the reservation stays live (settled only from PBS accounting)."""
        with self.locked() as st:
            e = st["entries"][token]
            if e["state"] == "settled":
                return
            e.update(runner_ended=time.time(), runner_wall_s=_nonneg(wall_s, "runner wall"), runner_exit=int(exit_code))

    def settle(self, job_id, walltime_s, cores, note=""):
        walltime_s = _nonneg(walltime_s, "settled walltime"); cores = _pos(cores, "cores")
        if not isinstance(note, str) or len(note.strip()) < 8:
            raise RuntimeError("refused: settlement needs the operator's technical note (qstat -xf accounting and the job's observed end)")
        with self.locked() as st:
            hits = [e for e in st["entries"].values() if e.get("job_id") == job_id]
            if len(hits) != 1:
                raise RuntimeError(f"refused: {len(hits)} entries carry job id {job_id}")
            e = hits[0]
            charge = cores * walltime_s / 3600.0
            if e["state"] == "settled":
                if abs(float(e["settled_core_h"]) - charge) > 1e-9:
                    raise RuntimeError(f"refused: job {job_id} is already settled at {e['settled_core_h']:.3f} core-h (terminal)")
                return dict(e)                                               # idempotent
            e.update(state="settled", settled_core_h=charge, settled_at=time.time(), settle_note=note)
            return dict(e)

    # --- stop requests: one file per scope, carrying an id the acknowledgment must name ---
    def stop_path(self, rep=None):
        return os.path.join(self.dir, "STOP" if rep is None else f"STOP_rep{rep}")

    def stop_request(self, rep=None, by="operator"):
        req = dict(id=secrets.token_hex(4), requested=time.time(), by=by, scope=("all" if rep is None else f"rep{rep}"))
        write_atomic(self.stop_path(rep), req)
        return req

    def current_stop(self, rep):
        """The applicable stop request for this rep (per-rep first, then global), or None."""
        for p in (self.stop_path(rep), self.stop_path()):
            if os.path.exists(p):
                try:
                    return json.load(open(p))
                except Exception:
                    return dict(id="unreadable", requested=0, scope=os.path.basename(p))
        return None

    def stop_requested(self, rep):
        return self.current_stop(rep) is not None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--cap", type=float, default=None, help="the declared cap (required to create the ledger; must equal it afterwards)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reserve"); r.add_argument("--kind", required=True); r.add_argument("--rep", type=int, default=None)
    r.add_argument("--cores", type=int, default=1); r.add_argument("--walltime-s", type=float, required=True); r.add_argument("--root", required=True)
    r.add_argument("--note", default="")
    b = sub.add_parser("bind"); b.add_argument("--token", required=True); b.add_argument("--job-id", required=True)
    s = sub.add_parser("settle"); s.add_argument("--job-id", required=True); s.add_argument("--walltime-s", type=float, required=True)
    s.add_argument("--cores", type=int, default=1); s.add_argument("--note", required=True, help="the operator's technical diagnosis of the job's end")
    sub.add_parser("show")
    st = sub.add_parser("stop"); st.add_argument("--rep", type=int, default=None)
    sc = sub.add_parser("stop-clear"); sc.add_argument("--rep", type=int, default=None)
    a = ap.parse_args(argv)
    L = CampaignLedger(a.campaign, a.cap)
    if a.cmd == "reserve":
        token, t = L.reserve(a.kind, a.rep, a.cores, a.walltime_s, a.root, a.note)
        print(f"reserved {token}: {a.kind} rep {a.rep} attempt {t['attempt']}, {a.cores} x {a.walltime_s/3600:.1f} h; spent {t['spent']:.1f}, live {t['live']:.1f} of {t['cap']:.0f}")
    elif a.cmd == "bind":
        e = L.bind(a.token, a.job_id); print(f"bound {a.token} to {a.job_id} ({e['kind']} rep {e['rep']})")
    elif a.cmd == "settle":
        e = L.settle(a.job_id, a.walltime_s, a.cores, a.note); print(f"settled {a.job_id}: {e['settled_core_h']:.2f} core-h ({e['kind']} rep {e['rep']})")
    elif a.cmd == "show":
        with L.locked() as st_:
            spent, live = L.totals(st_)
            print(f"cap {st_.get('cap_core_h')}  spent {spent:.2f}  live {live:.2f}  entries {len(st_['entries'])}")
            for e in sorted(st_["entries"].values(), key=lambda e: e["created"]):
                print(f"  {e['token']} {e['kind']:<6} rep {str(e.get('rep')):<4} att {e['attempt']} {e['state']:<8} job {e.get('job_id')} "
                      f"{e['cores']}x{e['walltime_s']/3600:.1f}h reserved {e['reserved_core_h']:.1f} settled {e.get('settled_core_h', 0.0):.1f} "
                      f"runner_wall {e.get('runner_wall_s', 0.0)/3600:.2f} h exit {e.get('runner_exit')}")
    elif a.cmd == "stop":
        req = L.stop_request(a.rep); print("stop requested:", L.stop_path(a.rep), req["id"])
    elif a.cmd == "stop-clear":
        p = L.stop_path(a.rep)
        if os.path.exists(p):
            os.remove(p)
        print("stop cleared:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

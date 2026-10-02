"""Ledger row 19: ONE campaign counter for every root, control and stage 0 (Codex 523249d, launch condition C).

The ledger is `<campaign>/budget.json`, read fresh and rewritten atomically under an exclusive lock on
`<campaign>/budget.lock` for every change (never a retained snapshot). Core-hours are RESERVED before a job is
submitted (`reserve`, by the operator on the login node), BOUND to the PBS job id after `qsub`, marked live by the
runner at start, and SETTLED only from scheduler-accounted allocated time (`settle`, by the operator from
`qstat -xf`); a killed or vanished job keeps its full reservation until it is settled - conservative by design.
Spent + live reservations + a new reservation must stay within the cap, else the reservation is refused. The number
of reservations per (kind, rep) is capped (the declared maximum submissions per dataset).

    python chpc/row19_ledger.py --campaign DIR reserve --kind main|c1|c2|c3|stage0 --rep N --cores 1 --walltime-s S --root R
    python chpc/row19_ledger.py --campaign DIR bind --token T --job-id J
    python chpc/row19_ledger.py --campaign DIR settle --job-id J --walltime-s S --cores C [--note "qstat -xf ..."]
    python chpc/row19_ledger.py --campaign DIR show
    python chpc/row19_ledger.py --campaign DIR stop [--rep N] / stop-clear [--rep N]
"""
import os, sys, json, time, fcntl, secrets, argparse, contextlib

KINDS = ("main", "c1", "c2", "c3", "stage0")
MAX_PER_KIND_REP = {"main": 4, "c1": 1, "c2": 1, "c3": 2, "stage0": 1}
LIVE = ("reserved", "bound", "live")


def write_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    d = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


class CampaignLedger:
    def __init__(self, campaign: str, cap_core_h: float | None = None):
        self.dir = campaign
        os.makedirs(campaign, exist_ok=True)
        self.path = os.path.join(campaign, "budget.json")
        self.lock_path = os.path.join(campaign, "budget.lock")
        self.cap_arg = cap_core_h

    @contextlib.contextmanager
    def locked(self, timeout_s: float = 60.0):
        """Exclusive lock, FRESH read, yield the state, atomic write on a clean exit."""
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
            state = json.load(open(self.path)) if os.path.exists(self.path) else dict(cap_core_h=self.cap_arg, entries={})
            if self.cap_arg is not None and state.get("cap_core_h") is None:
                state["cap_core_h"] = float(self.cap_arg)
            yield state
            write_atomic(self.path, state)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()

    @staticmethod
    def totals(state):
        spent = sum(float(e.get("settled_core_h", 0.0)) for e in state["entries"].values() if e.get("state") == "settled")
        live = sum(float(e.get("reserved_core_h", 0.0)) for e in state["entries"].values() if e.get("state") in LIVE)
        return spent, live

    def reserve(self, kind, rep, cores, walltime_s, root, attempt_note=""):
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        with self.locked() as st:
            cap = float(st.get("cap_core_h") or 0.0)
            if cap <= 0:
                raise RuntimeError("the ledger has no cap; create it with --cap once")
            spent, live = self.totals(st)
            mine = float(cores) * float(walltime_s) / 3600.0
            same = [e for e in st["entries"].values() if e["kind"] == kind and e.get("rep") == rep]
            if len(same) >= MAX_PER_KIND_REP[kind]:
                raise RuntimeError(f"refused: {len(same)} reservation(s) already exist for {kind} rep {rep} (maximum {MAX_PER_KIND_REP[kind]})")
            if spent + live + mine > cap + 1e-9:
                raise RuntimeError(f"refused: spent {spent:.1f} + live {live:.1f} + this {mine:.1f} > cap {cap:.0f} core-hours")
            token = secrets.token_hex(6)
            st["entries"][token] = dict(token=token, kind=kind, rep=rep, root=root, cores=int(cores), walltime_s=float(walltime_s),
                                        reserved_core_h=mine, attempt=len(same) + 1, state="reserved", job_id=None,
                                        created=time.time(), note=attempt_note)
            return token, dict(spent=spent, live=live + mine, cap=cap, attempt=len(same) + 1)

    def bind(self, token, job_id):
        with self.locked() as st:
            e = st["entries"].get(token)
            if e is None:
                raise RuntimeError(f"refused: no reservation {token}")
            if e["state"] != "reserved" and e.get("job_id") != job_id:
                raise RuntimeError(f"refused: reservation {token} is {e['state']} for job {e.get('job_id')}")
            e.update(state="bound", job_id=job_id, bound_at=time.time())
            return dict(e)

    def runner_start(self, token, job_id, kind, rep, root):
        """The runner's admission: the reservation must exist, be bound to THIS job id (or be unbound and get bound now),
        and describe this kind, rep and root. Returns the entry or raises."""
        with self.locked() as st:
            e = st["entries"].get(token)
            if e is None:
                raise RuntimeError(f"no reservation {token} in {self.path}")
            if e["kind"] != kind or e.get("rep") != rep or e.get("root") != root:
                raise RuntimeError(f"reservation {token} is for {e['kind']} rep {e.get('rep')} root {e.get('root')}, not this job")
            if e["state"] == "reserved":
                e.update(state="bound", job_id=job_id, bound_at=time.time())
            if e.get("job_id") != job_id:
                raise RuntimeError(f"reservation {token} is bound to job {e.get('job_id')}, not {job_id}")
            if e["state"] == "settled":
                raise RuntimeError(f"reservation {token} is already settled")
            e.update(state="live", runner_started=time.time())
            return dict(e)

    def runner_end(self, token, wall_s, exit_code):
        """Record the runner's own wall and exit; the reservation stays live (settled only from PBS accounting)."""
        with self.locked() as st:
            e = st["entries"][token]
            e.update(runner_ended=time.time(), runner_wall_s=float(wall_s), runner_exit=int(exit_code))

    def settle(self, job_id, walltime_s, cores, note=""):
        with self.locked() as st:
            hits = [e for e in st["entries"].values() if e.get("job_id") == job_id]
            if len(hits) != 1:
                raise RuntimeError(f"refused: {len(hits)} entries carry job id {job_id}")
            e = hits[0]
            e.update(state="settled", settled_core_h=float(cores) * float(walltime_s) / 3600.0, settled_at=time.time(), settle_note=note)
            return dict(e)

    def stop_path(self, rep=None):
        return os.path.join(self.dir, "STOP" if rep is None else f"STOP_rep{rep}")

    def stop_requested(self, rep):
        return os.path.exists(self.stop_path()) or os.path.exists(self.stop_path(rep))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--cap", type=float, default=None, help="set the cap when the ledger is created")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reserve"); r.add_argument("--kind", required=True); r.add_argument("--rep", type=int, default=None)
    r.add_argument("--cores", type=int, default=1); r.add_argument("--walltime-s", type=float, required=True); r.add_argument("--root", required=True)
    r.add_argument("--note", default="")
    b = sub.add_parser("bind"); b.add_argument("--token", required=True); b.add_argument("--job-id", required=True)
    s = sub.add_parser("settle"); s.add_argument("--job-id", required=True); s.add_argument("--walltime-s", type=float, required=True)
    s.add_argument("--cores", type=int, default=1); s.add_argument("--note", default="")
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
                      f"reserved {e['reserved_core_h']:.1f} settled {e.get('settled_core_h', 0.0):.1f} runner_wall {e.get('runner_wall_s', 0.0)/3600:.2f} h exit {e.get('runner_exit')}")
    elif a.cmd == "stop":
        open(L.stop_path(a.rep), "w").write(json.dumps(dict(requested=time.time(), by="operator")) + "\n"); print("stop requested:", L.stop_path(a.rep))
    elif a.cmd == "stop-clear":
        p = L.stop_path(a.rep)
        if os.path.exists(p):
            os.remove(p)
        print("stop cleared:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

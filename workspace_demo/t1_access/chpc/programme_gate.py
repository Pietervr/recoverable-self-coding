"""The CSCI1913 programme's ONE admission window (Codex RSC a1ce224, the scaling blocker): every controller that can add a
reservation to the programme - the screen's two roles, the bank, the development shard route and the slice mains - admits
only while holding <toolchain>/programme_admission.lock, after a STRICT fresh read of every campaign ledger:

  - every declared campaign ledger is read completely; a ledger that is expected but missing HOLDS, except a campaign
    declared `may_be_absent` whose root holds no plan (it has never started);
  - every entry: a declared state, finite non-negative reserved_core_h (booleans refused), and for a settled entry a finite
    non-negative settled_core_h; the ledger's own cap finite and positive; a campaign listed twice HOLDS;
  - other programme use (declared, finite, non-negative), the allocation (finite, positive) and the proposal (finite,
    positive) validated;
  - committed = settled + every non-settled reservation (worst case) + other use; refuse when committed + proposal exceeds
    the allocation.

    with programme_lock(funding):            # in Python controllers (row19_screen_admit)
        committed, detail = committed_core_h(funding) ...
    t1py chpc/programme_gate.py run --manifest chpc/row19_screen_manifest.json --proposal-core-h 9216 -- <controller command>
        # for the bank, shard and slice controllers (reviewed, unchanged): holds the lock, checks funding with the proposal,
        # runs the controller, releases - so no two admissions anywhere in the programme interleave.
"""
import os, sys, json, math, time, fcntl, argparse, contextlib, subprocess

STATES = ("reserved", "bound", "live", "settled")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def lock_path(funding):
    return funding["lock"]


@contextlib.contextmanager
def programme_lock(funding, timeout_s=600.0):
    p = lock_path(funding); os.makedirs(os.path.dirname(p), exist_ok=True)
    fh = open(p, "a+"); t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except OSError:
            if time.time() - t0 > timeout_s:
                fh.close(); raise RuntimeError(f"the programme admission lock {p} was not acquired within {timeout_s:.0f} s")
            time.sleep(1.0)
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def committed_core_h(funding):
    """(committed core-hours, per-campaign detail); raises RuntimeError on anything that cannot be counted."""
    if not (_num(funding.get("allocation_core_h")) and funding["allocation_core_h"] > 0):
        raise RuntimeError("the allocation is not a finite positive number")
    other = funding.get("other_settled_core_h")
    if not (_num(other) and other >= 0):
        raise RuntimeError("the declared other programme use is not finite and non-negative")
    camps = [c["path"] if isinstance(c, dict) else c for c in funding["campaigns"]]
    if len(set(camps)) != len(camps):
        raise RuntimeError("a campaign is listed twice")
    absent_ok = {c["path"]: c.get("root") for c in funding["campaigns"] if isinstance(c, dict) and c.get("may_be_absent")}
    total, detail = float(other), {}
    for c in camps:
        p = os.path.join(c, "budget.json")
        if not os.path.exists(p):
            root = absent_ok.get(c)
            if root is None:
                raise RuntimeError(f"the campaign ledger {p} is expected but missing")
            plans = [f for f in os.listdir(os.path.join(root, "plans")) if f.startswith("job_")] if os.path.isdir(os.path.join(root, "plans")) else []
            if plans:
                raise RuntimeError(f"the campaign ledger {p} is missing although {root} holds plans {plans[:3]}")
            detail[os.path.basename(c)] = 0.0; continue
        try:
            led = json.loads(open(p).read(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"non-finite {x}")))
        except Exception as e:
            raise RuntimeError(f"the ledger {p} is unreadable or holds a non-finite constant ({e})")
        if not (_num(led.get("cap_core_h")) and led["cap_core_h"] > 0) or not isinstance(led.get("entries"), dict):
            raise RuntimeError(f"the ledger {p} has no finite positive cap or no entries")
        s = 0.0
        for tok, e in led["entries"].items():
            if e.get("state") not in STATES:
                raise RuntimeError(f"{p}: entry {tok} has an undeclared state")
            r = e.get("reserved_core_h")
            if not (_num(r) and r >= 0):
                raise RuntimeError(f"{p}: entry {tok} has no finite non-negative reservation")
            if e["state"] == "settled":
                v = e.get("settled_core_h")
                if not (_num(v) and v >= 0):
                    raise RuntimeError(f"{p}: settled entry {tok} has no finite non-negative charge")
                s += float(v)
            else:
                s += float(r)
        total += s; detail[os.path.basename(c)] = s
    return total, detail


def funding_problem(funding, proposal_core_h):
    if not (_num(proposal_core_h) and proposal_core_h > 0):
        return "the proposal is not a finite positive number"
    try:
        total, detail = committed_core_h(funding)
    except RuntimeError as e:
        return f"funding cannot be established: {e}"
    if total + proposal_core_h > float(funding["allocation_core_h"]) + 1e-9:
        return (f"funding: {total:.0f} committed ({', '.join(f'{k} {v:.0f}' for k, v in detail.items())}) + {proposal_core_h:.0f} "
                f"proposed > the {funding['programme']} allocation of {funding['allocation_core_h']:.0f}")
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--manifest", required=True); r.add_argument("--proposal-core-h", type=float, required=True)
    r.add_argument("rest", nargs=argparse.REMAINDER)
    c = sub.add_parser("check"); c.add_argument("--manifest", required=True); c.add_argument("--proposal-core-h", type=float, default=1.0)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); funding = programme_funding(man)
    if a.cmd == "check":
        with programme_lock(funding):
            why = funding_problem(funding, a.proposal_core_h); total, detail = committed_core_h(funding)
        print(f"committed {total:.1f} {detail}; proposal {a.proposal_core_h:.0f}: {why or 'fits'}"); return 0 if not why else 2
    cmd = a.rest[1:] if a.rest and a.rest[0] == "--" else a.rest
    if not cmd:
        print("say -- <controller command>"); return 2
    with programme_lock(funding):
        why = funding_problem(funding, a.proposal_core_h)
        if why:
            print(f"REFUSED by the programme gate: {why}"); return 2
        return subprocess.run(cmd).returncode


def programme_funding(man):
    """The programme block: the manifest's `funding` plus the controller lineage's lock path and campaign roots (the screen
    manifests are immutable; the lock and the absent-allowed roots live in chpc/row19_screen_controls.json)."""
    here = os.path.dirname(os.path.abspath(__file__))
    ctl = json.load(open(os.path.join(here, "row19_screen_controls.json")))
    f = dict(man["funding"]); f.update(ctl["programme"])
    return f


if __name__ == "__main__":
    sys.exit(main())

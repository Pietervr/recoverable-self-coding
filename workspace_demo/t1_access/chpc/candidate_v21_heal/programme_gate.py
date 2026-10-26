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
    t1py chpc/programme_gate.py run --manifest chpc/row19_screen_manifest.json --jobs 8 --cores 24 --walltime-h 48 -- <controller command>
        # (revision 3+: the proposal is derived from --jobs x --cores x --walltime-h; it must describe the child's FULL filled
        # requests truthfully - a cooperative condition; refusals after the lineage and funding checks are logged, earlier
        # parser/lineage refusals print but are not logged)
        # for the bank, shard and slice controllers (reviewed, unchanged): holds the lock, checks funding with the proposal,
        # runs the controller, releases - so no two admissions anywhere in the programme interleave.

REVISION 3 (Codex RSC ee99ee1, R6 and the operating conditions): the wrapper refuses unless it and the lineage file are the
latest lineage version's bytes; the proposal is DERIVED from the request - `--jobs N --cores C --walltime-h H` (N x C x H,
the full filled reservations) - not a free number; every wrapped call is appended to <toolchain>/programme_admissions.jsonl
with the command, the proposal, the committed count before it and the exit code; `settle -- <row19_ledger settle command>`
runs a SETTLEMENT inside the same lock and records the committed count before and after, so a settlement that raises a
reservation to its actual charge is serialized with admissions and visible to the next one. The older bank, shard and slice
controllers are not modified: routing their admissions and settlements through this wrapper is a COOPERATIVE operating
procedure, stated as such - not code enforcement inside them.

REVISION 4 (Codex RSC 8bd1451, C3): the controls file is trusted only through its ADOPTION - chpc/row19_screen_controls_adoption.json,
git-tracked and unmodified, naming the controls file's exact SHA-256 and a git-tracked, unmodified review record that carries the
line `ADOPT row19-screen-controls sha256=<that sha> version=<latest version>`; the controls file must be tracked, unmodified and
have exactly that SHA-256. Until then neither its programme block (lock, campaigns) nor its deployment or history is used: the
wrapper and the screen controller refuse.

REVISION 5 (controls v21, the FUNDING ROUTE; owner ruling 26 Oct 2026 "once we are out of our own limit we go to HEAL1922" and
"make sure that we can run jobs on HEAL1922 while we are running our own so that there is no holdup when we switch over";
chpc/candidate_v21_heal/DESIGN_v21.md). The latest controls version may declare `funding_route`: an ORDERED list of programmes
{programme, allocation_core_h, other_settled_core_h, note}. The first entry must be the manifest's programme with the
allocation and other use programme_funding() already resolves (one source for each number; a mismatch refuses). Without the
key the route is that one programme (every earlier version). Accounting is PER PROGRAMME: a ledger entry's programme is its
`programme` field; an entry WITHOUT the field was charged to the route's first programme (CSCI1913) BY DEFINITION - every
entry written before v21 and every entry of the bank, shard, slice, originals and S controllers, which never write it; old
entries are never rewritten. A `programme` that is not a string naming a route programme cannot be counted and refuses. A
programme's committed = its own settled charges + its own non-settled reservations (worst case) + its own declared other use;
a settlement credits the entry's own programme because the field stays on the entry. route_choice() assigns each proposed job,
in order, to the FIRST programme whose committed + the jobs already assigned to it in this call + this job fits its allocation,
and refuses when none fits - so CSCI1913 and HEAL1922 entries live side by side and the switch is per admission, never a
drain. committed_core_h() and funding_problem() keep their meaning for the FIRST programme (the bank, shard, slice and S
controllers write `#PBS -P CSCI1913` from their manifests, so the wrapper still admits them against CSCI1913 only).
"""
import os, re, sys, json, math, time, fcntl, argparse, contextlib, subprocess

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


def route_of(funding):
    """REVISION 5: the validated ordered route [{programme, allocation_core_h, other_settled_core_h}, ...]; raises RuntimeError.
    Without a declared route: the one programme of the funding block (unchanged behaviour)."""
    if not (_num(funding.get("allocation_core_h")) and funding["allocation_core_h"] > 0):
        raise RuntimeError("the allocation is not a finite positive number")
    other = funding.get("other_settled_core_h")
    if not (_num(other) and other >= 0):
        raise RuntimeError("the declared other programme use is not finite and non-negative")
    prog = funding.get("programme")
    if not isinstance(prog, str) or not prog:
        raise RuntimeError("the funding block names no programme")
    first = dict(programme=prog, allocation_core_h=float(funding["allocation_core_h"]), other_settled_core_h=float(other))
    r = funding.get("route")
    if r is None:
        return [first]
    if not isinstance(r, list) or not r:
        raise RuntimeError("the declared funding route is not a non-empty list")
    out, seen = [], set()
    for k, x in enumerate(r):
        if not isinstance(x, dict) or not isinstance(x.get("programme"), str) or not re.match(r"^[A-Z0-9]{4,16}$", x["programme"]):
            raise RuntimeError(f"funding route entry {k} names no programme code")
        if x["programme"] in seen:
            raise RuntimeError(f"the funding route lists {x['programme']} twice")
        seen.add(x["programme"])
        a, o = x.get("allocation_core_h"), x.get("other_settled_core_h")
        if not (_num(a) and a > 0) or not (_num(o) and o >= 0):
            raise RuntimeError(f"funding route entry {x['programme']}: the allocation or other use is not finite (positive / non-negative)")
        out.append(dict(programme=x["programme"], allocation_core_h=float(a), other_settled_core_h=float(o)))
    if out[0] != first:
        raise RuntimeError(f"the funding route's first programme {out[0]} is not the funding block's {first}")
    return out


def entry_programme(e, route):
    """The programme an entry was charged to: its `programme` field, or - with no field - the route's FIRST programme
    (CSCI1913) by definition (REVISION 5: every pre-v21 entry and every entry of a controller that never writes the field)."""
    if "programme" not in e:
        return route[0]["programme"]
    p = e["programme"]
    if not isinstance(p, str) or p not in [x["programme"] for x in route]:
        raise RuntimeError(f"the entry's programme {p!r} is not a programme of the funding route")
    return p


def committed_by_programme(funding):
    """REVISION 5: ({programme: committed core-hours incl. its declared other use}, {campaign: {programme: core-hours}}); the
    same strict read as committed_core_h; raises RuntimeError on anything that cannot be counted."""
    route = route_of(funding)
    tot = {x["programme"]: float(x["other_settled_core_h"]) for x in route}
    camps = [c["path"] if isinstance(c, dict) else c for c in funding["campaigns"]]
    if len(set(camps)) != len(camps):
        raise RuntimeError("a campaign is listed twice")
    absent_ok = {c["path"]: c.get("root") for c in funding["campaigns"] if isinstance(c, dict) and c.get("may_be_absent")}
    detail = {}
    for c in camps:
        p = os.path.join(c, "budget.json")
        if not os.path.exists(p):
            root = absent_ok.get(c)
            if root is None:
                raise RuntimeError(f"the campaign ledger {p} is expected but missing")
            plans = [f for f in os.listdir(os.path.join(root, "plans")) if f.startswith("job_")] if os.path.isdir(os.path.join(root, "plans")) else []
            if plans:
                raise RuntimeError(f"the campaign ledger {p} is missing although {root} holds plans {plans[:3]}")
            detail[os.path.basename(c)] = {}; continue
        try:
            led = json.loads(open(p).read(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"non-finite {x}")))
        except Exception as e:
            raise RuntimeError(f"the ledger {p} is unreadable or holds a non-finite constant ({e})")
        if not (_num(led.get("cap_core_h")) and led["cap_core_h"] > 0) or not isinstance(led.get("entries"), dict):
            raise RuntimeError(f"the ledger {p} has no finite positive cap or no entries")
        d = {}
        for tok, e in led["entries"].items():
            if not isinstance(e, dict) or e.get("state") not in STATES:
                raise RuntimeError(f"{p}: entry {tok} has an undeclared state")
            r = e.get("reserved_core_h")
            if not (_num(r) and r >= 0):
                raise RuntimeError(f"{p}: entry {tok} has no finite non-negative reservation")
            try:
                prog = entry_programme(e, route)
            except RuntimeError as x:
                raise RuntimeError(f"{p}: entry {tok}: {x}")
            if e["state"] == "settled":
                v = e.get("settled_core_h")
                if not (_num(v) and v >= 0):
                    raise RuntimeError(f"{p}: settled entry {tok} has no finite non-negative charge")
                c_h = float(v)
            else:
                c_h = float(r)
            d[prog] = d.get(prog, 0.0) + c_h; tot[prog] += c_h
        detail[os.path.basename(c)] = d
    return tot, detail


def route_choice(funding, proposals):
    """REVISION 5: (programmes, problem). Each proposed job (core-hours, in order) goes to the FIRST route programme whose
    committed + what this call already assigned to it + this job fits its allocation; '' problem when every job fits one."""
    if not isinstance(proposals, (list, tuple)) or not proposals or not all(_num(x) and x > 0 for x in proposals):
        return [], "the proposal is not a non-empty list of finite positive numbers"
    try:
        route = route_of(funding); tot, _ = committed_by_programme(funding)
    except RuntimeError as e:
        return [], f"funding cannot be established: {e}"
    out, add = [], {x["programme"]: 0.0 for x in route}
    for k, prop in enumerate(proposals):
        hit = None
        for x in route:
            pg = x["programme"]
            if tot[pg] + add[pg] + float(prop) <= x["allocation_core_h"] + 1e-9:
                hit = pg; break
        if hit is None:
            return [], ("funding: no programme of the route fits job %d of this admission (%.0f core-h): %s" % (
                k + 1, prop, "; ".join("%s %.0f committed + %.0f this call of %.0f" % (x["programme"], tot[x["programme"]], add[x["programme"]],
                                                                                     x["allocation_core_h"]) for x in route)))
        out.append(hit); add[hit] += float(prop)
    return out, ""


def committed_core_h(funding):
    """(committed core-hours, per-campaign detail) of the route's FIRST programme (REVISION 5: an entry charged to a later
    programme of the route is not counted here); raises RuntimeError on anything that cannot be counted."""
    route = route_of(funding)
    tot, detail = committed_by_programme(funding)
    first = route[0]["programme"]
    return tot[first], {c: d.get(first, 0.0) for c, d in detail.items()}


def _committed_core_h_r4(funding):
    """REVISION 4's single-programme count, kept for the record (and as the equivalence oracle in the v21 tests); not called."""
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
    r = sub.add_parser("run"); r.add_argument("--manifest", required=True)
    r.add_argument("--jobs", type=int, required=True); r.add_argument("--cores", type=int, required=True); r.add_argument("--walltime-h", type=float, required=True)
    r.add_argument("rest", nargs=argparse.REMAINDER)
    st = sub.add_parser("settle"); st.add_argument("--manifest", required=True); st.add_argument("rest", nargs=argparse.REMAINDER)
    c = sub.add_parser("check"); c.add_argument("--manifest", required=True); c.add_argument("--proposal-core-h", type=float, default=1.0)
    a = ap.parse_args(argv)
    why = lineage_problem()
    if why:
        print(f"REFUSED: {why}"); return 2
    man = json.load(open(a.manifest)); funding = programme_funding(man)
    if a.cmd == "check":
        with programme_lock(funding):
            why = funding_problem(funding, a.proposal_core_h); total, detail = committed_core_h(funding)
            byp, _ = committed_by_programme(funding); progs, rwhy = route_choice(funding, [a.proposal_core_h])
        print(f"committed {total:.1f} {detail}; proposal {a.proposal_core_h:.0f}: {why or 'fits'}")
        print("route: " + "; ".join(f"{x['programme']} {byp[x['programme']]:.1f} of {x['allocation_core_h']:.0f}" for x in route_of(funding))
              + f"; this proposal would go to {progs[0] if progs else 'NO programme (' + rwhy + ')'}")
        return 0 if not why else 2
    cmd = a.rest[1:] if a.rest and a.rest[0] == "--" else a.rest
    if not cmd:
        print("say -- <controller command>"); return 2
    log = os.path.join(os.path.dirname(lock_path(funding)), "programme_admissions.jsonl")
    with programme_lock(funding):
        before, _ = committed_core_h(funding); byp_before, _ = committed_by_programme(funding)
        if a.cmd == "settle":
            rc = subprocess.run(cmd).returncode; after, _ = committed_core_h(funding); byp_after, _ = committed_by_programme(funding)
            _log(log, dict(kind="settle", cmd=cmd, committed_before=before, committed_after=after, rc=rc,
                           by_programme_before=byp_before, by_programme_after=byp_after)); return rc
        if not (a.jobs > 0 and a.cores > 0 and a.walltime_h > 0):
            print("REFUSED: jobs, cores and walltime must be positive"); return 2
        proposal = float(a.jobs * a.cores * a.walltime_h)
        why = funding_problem(funding, proposal)
        if why:
            _log(log, dict(kind="refused", cmd=cmd, proposal=proposal, committed_before=before, why=why))
            print(f"REFUSED by the programme gate: {why}"); return 2
        rc = subprocess.run(cmd).returncode; after, _ = committed_core_h(funding)
        _log(log, dict(kind="admission", cmd=cmd, proposal=proposal, committed_before=before, committed_after=after, rc=rc))
        if after - before > proposal + 1e-6:
            print(f"WARNING: the controller committed {after - before:.0f} core-hours, more than the declared {proposal:.0f}; "
                  f"recorded - every later admission sees the true count")
        return rc


def _log(path, rec):
    rec["t"] = time.time()
    with open(path, "a") as fh:
        fh.write(json.dumps(rec) + "\n"); fh.flush(); os.fsync(fh.fileno())


CONTROLS = "chpc/row19_screen_controls.json"
CONTROLS_ADOPTION = "chpc/row19_screen_controls_adoption.json"
HERE_ = os.path.dirname(os.path.abspath(__file__)); T1_ = os.path.abspath(os.path.join(HERE_, ".."))


def tracked_unmodified(rel):
    try:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=T1_, capture_output=True, text=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=T1_, capture_output=True, text=True)
        return a.returncode == 0 and b.returncode == 0
    except Exception:
        return False


def controls_authority_problem():
    """C3: '' only when the controls file is the adopted, review-bound bytes."""
    import hashlib
    ap = os.path.join(T1_, CONTROLS_ADOPTION); cp = os.path.join(T1_, CONTROLS)
    if not os.path.exists(ap):
        return "the controls file has no adoption (chpc/row19_screen_controls_adoption.json)"
    for rel in (CONTROLS_ADOPTION, CONTROLS):
        if not tracked_unmodified(rel):
            return f"{rel} is not git-tracked and unmodified"
    try:
        ad = json.load(open(ap)); ctl = json.load(open(cp))
    except Exception as e:
        return f"the controls adoption or file is unreadable ({e})"
    got = hashlib.sha256(open(cp, "rb").read()).hexdigest()
    if ad.get("controls_sha256") != got:
        return "the controls file is not the adopted bytes"
    rv = ad.get("review_record") or {}; rvp = os.path.join(T1_, rv.get("path", "") or "_none_")
    if not os.path.exists(rvp) or not tracked_unmodified(rv.get("path", "")) or hashlib.sha256(open(rvp, "rb").read()).hexdigest() != rv.get("sha256"):
        return "the controls review record is not git-tracked, unmodified, with the adopted SHA-256"
    line = f"ADOPT row19-screen-controls sha256={got} version={ctl['versions'][-1]['version']}"
    if line not in [l.strip() for l in open(rvp).read().splitlines()]:
        return f"the controls review record does not carry `{line}`"
    return ""


def lineage_problem():
    """'' when the controls file is adopted and this wrapper and the controllers are the latest lineage version's bytes."""
    import hashlib
    why = controls_authority_problem()
    if why:
        return why
    here = os.path.dirname(os.path.abspath(__file__)); t1 = os.path.abspath(os.path.join(here, ".."))
    try:
        v = json.load(open(os.path.join(here, "row19_screen_controls.json")))["versions"][-1]
    except Exception as e:
        return f"the controller lineage is unreadable ({e})"
    bad = [f for f, h in v["files"].items() if not os.path.exists(os.path.join(t1, f)) or hashlib.sha256(open(os.path.join(t1, f), "rb").read()).hexdigest() != h]
    if "chpc/programme_gate.py" not in v["files"]:
        bad.append("chpc/programme_gate.py (not in the lineage)")
    return f"the controllers {bad} are not lineage version {v['version']}'s bytes" if bad else ""


def programme_funding(man):
    """The programme block: the manifest's `funding` plus the controller lineage's lock path and campaign roots (the screen
    manifests are immutable; the lock and the absent-allowed roots live in chpc/row19_screen_controls.json)."""
    why = controls_authority_problem()
    if why:
        raise RuntimeError(f"the programme block cannot be trusted: {why}")
    here = os.path.dirname(os.path.abspath(__file__))
    ctl = json.load(open(os.path.join(here, "row19_screen_controls.json")))
    f = dict(man["funding"]); f.update(ctl["programme"])
    r = ctl["versions"][-1].get("funding_route")                    # REVISION 5: the ordered route of the LATEST version
    if r is not None:
        f["route"] = r
    route_of(f)                                                     # validated here: a malformed route refuses every caller
    return f


if __name__ == "__main__":
    sys.exit(main())

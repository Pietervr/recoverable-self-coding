"""Row 19 screen on EC2: the ONE claim and budget authority for every EC2 attempt of every run (Codex RSC f3dd3d7
contracts 2, 7, 8; repaired for Codex RSC 0483db4 V10-2 and V10-6). Mac only.

    python3 prod_authority.py inventory                       # seal the current inventory (copy it to <root>/ec2/authority/)
    python3 prod_authority.py ack --run prod-e1 --attempt 3 --register <pulled root/ec2/register.json>
    python3 prod_authority.py disposition --run prod-e1 --attempt 3 --reason "<why no output will be ingested>"
    python3 prod_authority.py budget                          # every envelope, as the next admission would see it

LEDGERS. runs/<run>/attempts.json per run (prod-e<epoch> production, qual-Q1 / qual-Q2 qualification, b2 the row-23
benchmark), states intent / launched / rejected / ambiguous / reconciled as in the reviewed row-23 launcher, plus the
ingestion state pending / ingested / dispositioned. EVERY reservation (admission), settlement acknowledgement, disposition
and inventory is taken under ONE global lock (runs/.authority.lock) in addition to the run lock the reaper shares, and
bumps one global generation; sequences are globally unique and increasing (runs/.authority_state.json).

OWNERSHIP. A production or qualification attempt owns its work coordinates from intent until it is rejected (no instance
ever existed) or its output was ingested (acknowledged from the Lengau register by `ack`, checked against the attempt) or
dispositioned (`disposition`: reconciled with no output to ingest). The fence at a coordinate is the highest sequence of
any non-rejected attempt ever assigned it; ingestion on Lengau accepts a record only from the inventory's CURRENT owner at a
sequence not below its own register fence, so a dispositioned or reassigned late writer can never publish. Duplicates
(qualification repeats, sentinels) never own.

BUDGET (one serialized ledger across all runs and epochs). Every attempt that is not rejected is charged its worst case
until reconciled and its observed hours after, each at its own recorded spot cap and ancillary rate. Envelopes, all checked
before any dispatch: (1) production + qualification across ALL epochs and retries <= USD 2,300; (2) every further AWS
spend - the recorded baseline (Cost Explorer through a stated date, with the post-cutoff part of 12 Sept bounded and an
idle-charge accrual per day after it) + every run under runs/ (row 23 included) - <= USD 3,000 from 12 Sept 2026 21:50 UTC;
(3) each qualification part's cumulative charge (retries included) <= its declared ceiling, and only once the owner has
accepted those ceilings in ec2_release_state.json."""
import argparse, contextlib, fcntl, glob, hashlib, json, os, sys, time
import bench_launch as L

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "chpc"))
import row19_ec2_state as ES

PROD_ENVELOPE_USD, CUMULATIVE_CAP_USD = 2300.0, 3000.0
# Ancillary per instance-hour for the production/qualification contract (60 GB gp3 at <= USD 0.10/GB-month = 0.0082/h, one
# public IPv4 0.005/h; rounded up) and a fixed per-attempt allowance for transfer and requests (toolchain 0.22 GB and results
# <= 1 GB across eu-north-1 <-> Oregon at 0.02/GB, S3 requests of 10-minute syncs over 22 h, reserve).
ANC_H_PROD, S3_FIXED_PROD = 0.014, 0.30
QUAL_LIFETIME_S = 79200                       # 22 h instance lifetime for Q1 and Q2 (QUALIFICATION_PLAN.md)
QUAL_CEILINGS_USD = {"Q1": 28.0, "Q2": 17.0}  # = worst of one attempt each, rounded UP; retries need the owner
SENTINELS_PER_ATTEMPT = 4
PROD_CLASSES = ("production", "qualification")
LOCK = os.path.join(HERE, "runs", ".authority.lock")
STATE = os.path.join(HERE, "runs", ".authority_state.json")
INV_DIR = os.path.join(HERE, "runs", "inventory")
RELEASE_STATE = os.path.join(HERE, "ec2_release_state.json")


def run_name(epoch):
    return f"prod-e{int(epoch)}"


def qual_run(part):
    return f"qual-{part}"


def run_class(run):
    return "production" if run.startswith("prod-") else "qualification" if run.startswith("qual-") else "benchmark"


@contextlib.contextmanager
def authority_lock(wait_s=0):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    fh = open(LOCK, "a+"); t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except BlockingIOError:
            if time.time() - t0 >= wait_s:
                fh.close(); raise
            time.sleep(1)
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"generation": 1, "next_sequence": 1}


def bump(st, sequences=0):
    """Advance the global generation (and reserve `sequences` sequence numbers); call ONLY under authority_lock."""
    first = st["next_sequence"]
    st = dict(generation=st["generation"] + 1, next_sequence=first + sequences)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, STATE)
    return st, first


def baseline(now=None):
    """Spend already incurred outside the ledgers: the recorded Cost Explorer figure through `through_utc`, plus the idle
    accrual (VPC endpoints, S3) for every started day after it - a moving bound, never a constant."""
    b = json.load(open(os.path.join(HERE, "budget_baseline.json")))
    assert b.get("schema") == "t1-aws-budget-baseline-2", "budget_baseline.json is not schema 2"
    now = time.time() if now is None else now
    days = max(0.0, (now - b["through_epoch"]) / 86400.0)
    return float(b["spent_usd"]) + float(b["idle_usd_per_day"]) * (int(days) + 1)


def charged(a):
    """One attempt's charge at its own cap and ancillary rate: worst case until reconciled, observed after; rejected 0."""
    if "anc_h" not in a:
        return L.charged(a)                                              # benchmark attempts: the reviewed row-23 rule
    if a.get("state") == "rejected":
        return 0.0
    if a.get("state") == "reconciled":
        t = a["terminal"]
        return (t["compute_s"] / 3600) * a["max_price"] + (t["ancillary_s"] / 3600) * a["anc_h"] + a["s3_fixed"]
    return worst_usd(a["lifetime_s"], a["max_price"])


def worst_usd(lifetime_s, max_price):
    return ((lifetime_s + L.GRACE_S + L.RESERVE_S) / 3600) * (max_price + ANC_H_PROD) + S3_FIXED_PROD


def ledgers():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "runs", "*", "attempts.json"))):
        out[os.path.basename(os.path.dirname(p))] = json.load(open(p))
    return out


def budget(leds, now=None):
    prod = sum(charged(a) for r, l in leds.items() if run_class(r) in PROD_CLASSES for a in l["attempts"])
    allruns = sum(charged(a) for l in leds.values() for a in l["attempts"])
    qual = {q: sum(charged(a) for a in leds.get(qual_run(q), {"attempts": []})["attempts"]) for q in QUAL_CEILINGS_USD}
    return dict(production_usd=prod, all_runs_usd=allruns, baseline_usd=baseline(now), qualification_usd=qual)


def budget_problem(leds, run, new_worst_usd, release=None, now=None):
    b = budget(leds, now)
    if run_class(run) in PROD_CLASSES and b["production_usd"] + new_worst_usd > PROD_ENVELOPE_USD + 1e-9:
        return f"production envelope: {b['production_usd']:.2f} charged across all epochs + {new_worst_usd:.2f} worst > {PROD_ENVELOPE_USD:.0f}"
    if b["baseline_usd"] + b["all_runs_usd"] + new_worst_usd > CUMULATIVE_CAP_USD + 1e-9:
        return (f"cumulative cap: baseline {b['baseline_usd']:.2f} + all runs {b['all_runs_usd']:.2f} + {new_worst_usd:.2f} "
                f"> {CUMULATIVE_CAP_USD:.0f}")
    if run_class(run) == "qualification":
        q = run.split("-", 1)[1]
        if not (release or {}).get("qualification", {}).get("owner_accepted_ceilings"):
            return f"the qualification ceilings {QUAL_CEILINGS_USD} are not accepted by the owner (ec2_release_state.json)"
        if b["qualification_usd"][q] + new_worst_usd > QUAL_CEILINGS_USD[q] + 1e-9:
            return f"{q} ceiling: {b['qualification_usd'][q]:.2f} charged + {new_worst_usd:.2f} worst > {QUAL_CEILINGS_USD[q]:.2f}"
    return ""


def owns(a, run):
    return run_class(run) in PROD_CLASSES and a.get("state") != "rejected" and a.get("ingestion", "pending") == "pending"


def owned(leds):
    """{(rep, index): (key, sequence)} across ALL runs and epochs."""
    own = {}
    for run, l in leds.items():
        for a in l["attempts"]:
            if not owns(a, run):
                continue
            for c in a.get("coordinates", []):
                c = tuple(c)
                if c in own:
                    raise RuntimeError(f"coordinate {c} owned by {own[c][0]} and {run}/{a['attempt']}: the ledgers are inconsistent")
                own[c] = (f"{run}/{a['attempt']}", a["sequence"])
    return own


def fence(leds):
    f = {}
    for run, l in leds.items():
        if run_class(run) not in PROD_CLASSES:
            continue
        for a in l["attempts"]:
            if a.get("state") == "rejected":
                continue
            for c in a.get("coordinates", []):
                k = f"{c[0]}/{c[1]}"; f[k] = max(f.get(k, -1), a["sequence"])
    return f


def allocate(part, leds, completed, n):
    """The next n block coordinates in the fixed order (index 199 downward, reps ascending), never completed or owned."""
    own = owned(leds)
    order = [(r, i) for i in sorted(part["indices"], reverse=True) for r in part["reps"]]
    return [c for c in order if c not in completed and c not in own][:n]


def sentinels(lengau_completed, token, n=SENTINELS_PER_ATTEMPT, exclude=()):
    """n distinct Lengau-completed coordinates chosen by the attempt token, never by outcome."""
    pool = sorted(set(lengau_completed) - set(exclude))
    if len(pool) < n:
        raise ValueError("fewer Lengau-completed coordinates than sentinels")
    picked, k = [], 0
    while len(picked) < n:
        h = int(hashlib.sha256(f"{token}:{k}".encode()).hexdigest(), 16) % len(pool)
        if pool[h] not in picked:
            picked.append(pool[h])
        k += 1
    return picked


def owner_of(leds, coordinate):
    return owned(leds).get(tuple(coordinate))


def release_state():
    """The reviewed release state (row 23, qualification, production). Every claim it makes must be backed by a file whose
    sha256 it pins; a missing or differing file reads as NOT released."""
    r = json.load(open(RELEASE_STATE))
    assert r.get("schema") == "t1-ec2-release-state-1", "ec2_release_state.json schema"
    def backed(d, pk="path", hk="sha256"):
        p = d.get(pk); return bool(p) and os.path.exists(os.path.join(HERE, p)) and L.sha256(os.path.join(HERE, p)) == d.get(hk)
    r23 = r["row23"]; q = r["qualification"]; pr = r["production"]
    r23["ok"] = bool(r23.get("declared_success")) and backed(r23, "report_path", "report_sha256")
    q["ok"] = r23["ok"] and bool(q.get("permitted")) and bool(q.get("owner_accepted_ceilings")) and backed(q, "record_path", "record_sha256") \
        and q.get("ceilings_usd") == QUAL_CEILINGS_USD
    pr["ok"] = q["ok"] and bool(pr.get("released")) and backed(pr, "certificate_path", "certificate_sha256")
    if pr["ok"]:
        cert = json.load(open(os.path.join(HERE, pr["certificate_path"])))
        pr["ok"] = cert.get("outcome") == "RELEASE" and cert.get("problems") == []
    return r


def inventory(leds, gen, rel, now=None):
    """The sealed authority inventory of every production/qualification attempt (Lengau's ingestion, status and activation
    read it; row19_ec2_state.inventory_problem is its contract)."""
    now = time.time() if now is None else now
    atts = {}
    for run, l in leds.items():
        cls = run_class(run)
        if cls not in PROD_CLASSES:
            continue
        for a in l["attempts"]:
            key = f"{run}/{a['attempt']}"
            atts[key] = dict(key=key, run=run, attempt=a["attempt"], attempt_id=a["attempt_id"], sequence=a["sequence"],
                             state=a["state"], ingestion=a.get("ingestion", "pending"), **{"class": cls}, contract=a["contract"],
                             plan_sha256=a["plan_sha256"], coordinates=a.get("coordinates", []), sentinels=a.get("sentinels", []),
                             duplicates=a.get("duplicates", []), charged_usd=round(charged(a), 6))
    own = owned(leds)
    b = budget(leds, now)
    body = dict(schema=ES.INVENTORY_SCHEMA, generation=gen, at=now, attempts=atts,
                owners={f"{c[0]}/{c[1]}": [k, s] for c, (k, s) in sorted(own.items())}, fence=fence(leds),
                release=dict(production_released=rel["production"]["ok"], released_attempts=sorted(rel["production"].get("released_attempts") or [])
                             if rel["production"]["ok"] else []),
                usd=dict(b, envelope_usd=PROD_ENVELOPE_USD, cap_usd=CUMULATIVE_CAP_USD))
    return ES.seal(body)


def write_inventory(now=None):
    """Under the authority lock: seal and write runs/inventory/inventory_g<gen>.json and latest.json. Returns the path."""
    leds = ledgers(); st = state()
    inv = inventory(leds, st["generation"], release_state(), now)
    why = ES.inventory_problem(inv, now)
    if why:
        raise RuntimeError(f"the authority produced an invalid inventory: {why}")
    os.makedirs(INV_DIR, exist_ok=True)
    p = os.path.join(INV_DIR, f"inventory_g{st['generation']}.json")
    for q in (p, os.path.join(INV_DIR, "latest.json")):
        tmp = q + ".tmp"
        with open(tmp, "w") as f:
            json.dump(inv, f, indent=1, sort_keys=True); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, q)
    return p


def ack(run, n, register_path):
    """Release an attempt's ownership on the Lengau register's evidence (recoverable: idempotent on the same entry)."""
    led = L.load(run); a = next(x for x in led["attempts"] if x["attempt"] == n)
    reg = json.load(open(register_path)); e = (reg.get("attempts") or {}).get(a["attempt_id"])
    if reg.get("schema") != ES.REGISTER_SCHEMA or e is None:
        raise ValueError("the register carries no entry for this attempt")
    if e.get("state") != "ingested" or e.get("key") != f"{run}/{n}" or e.get("sequence") != a["sequence"] or e.get("plan_sha256") != a["plan_sha256"]:
        raise ValueError(f"the register entry is {e.get('state')} / {e.get('key')} / seq {e.get('sequence')}: not this attempt ingested")
    if sorted(e["coordinates"]) != sorted(f"{r}/{i}" for r, i in a["coordinates"]):
        raise ValueError("the register's coordinates are not exactly the attempt's owned coordinates")
    digest = ES.sha_bytes(ES.canonical(e))
    if a.get("ingestion") == "ingested":
        if (a.get("ingest_ack") or {}).get("entry_sha256") != digest:
            raise ValueError("already acknowledged against a different register entry")
        return False
    if a.get("ingestion") != "pending" or a.get("state") != "reconciled":
        raise ValueError(f"attempt is {a.get('state')}/{a.get('ingestion')}: only a reconciled pending attempt is acknowledged")
    a["ingestion"] = "ingested"; a["ingest_ack"] = dict(entry_sha256=digest, register_sha256=L.sha256(register_path), at=time.time())
    L.save(run, led); return True


def disposition(run, n, reason):
    led = L.load(run); a = next(x for x in led["attempts"] if x["attempt"] == n)
    if a.get("state") != "reconciled" or a.get("ingestion") != "pending":
        raise ValueError(f"attempt is {a.get('state')}/{a.get('ingestion')}: only a reconciled pending attempt is dispositioned")
    a["ingestion"] = "dispositioned"; a["disposition"] = dict(reason=reason, at=time.time())
    L.save(run, led)


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory"); sub.add_parser("budget")
    k = sub.add_parser("ack"); k.add_argument("--run", required=True); k.add_argument("--attempt", type=int, required=True); k.add_argument("--register", required=True)
    d = sub.add_parser("disposition"); d.add_argument("--run", required=True); d.add_argument("--attempt", type=int, required=True); d.add_argument("--reason", required=True)
    a = ap.parse_args()
    try:
        with authority_lock(wait_s=60):
            if a.cmd == "budget":
                print(json.dumps(dict(budget(ledgers()), envelope=PROD_ENVELOPE_USD, cap=CUMULATIVE_CAP_USD, ceilings=QUAL_CEILINGS_USD), indent=1)); return 0
            if a.cmd in ("ack", "disposition"):
                with L.run_lock(a.run, wait_s=60):
                    if a.cmd == "ack":
                        changed = ack(a.run, a.attempt, a.register)
                    else:
                        disposition(a.run, a.attempt, a.reason); changed = True
                if changed:
                    bump(state())
            print(write_inventory()); return 0
    except BlockingIOError:
        sys.exit("REFUSED: another authority operation holds runs/.authority.lock")


if __name__ == "__main__":
    sys.exit(main())

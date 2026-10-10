"""Row 19 screen on EC2, production stage 2 (Codex RSC f3dd3d7 contracts 2, 7, 8): the EC2 claim and budget authority.

One authority, on the Mac, for every EC2 production attempt of one partition epoch:
  runs/prod-e<epoch>/attempts.json   the attempt ledger (same states and lock as the reviewed row-23 launcher:
                                     intent / launched / rejected / ambiguous / reconciled, plus the ingestion state)
Everything that reads or writes it holds the run lock (bench_launch.run_lock), so allocation, reservation and
reconciliation are serialized across launcher, reaper and ingestion bookkeeping.

ALLOCATION. The coordinates an attempt may compute are drawn ONLY from the partition block (row19_partition), in a fixed
order (index 199 downward, reps ascending), skipping every coordinate that is (a) completed - present in the ingested
inventory - or (b) owned by any attempt that is not definitively closed. An attempt owns its plan's coordinates from
intent onward; it releases them only when it is 'rejected' (no instance ever existed) or when it is reconciled AND its
output has been ingested or explicitly dispositioned (pending output reconciled). A coordinate is therefore never
assignable to two live attempts, and a late writer is rejected at ingestion because its attempt no longer owns the
coordinate (each coordinate's owner is recorded with the attempt's immutable sequence number).

SENTINELS. Each attempt also recomputes `SENTINELS_PER_ATTEMPT` coordinates Lengau has completed, chosen by a fixed rule
from the sorted Lengau-completed list (sha256 of the attempt's client token, never by outcome). They are qualification
work: compared, never published, never counted.

BUDGET. Two envelopes, both enforced before any dispatch: the production envelope (USD 2,300) over all production attempts,
and the cumulative further-spend cap (USD 3,000 from 12 Sept 21:50 UTC) over production + row 23 + the recorded baseline
(spend already incurred, from Cost Explorer, kept in `budget_baseline.json` with its date and source). Every attempt that
is not rejected is charged its worst case until reconciled, its observed hours after."""
import hashlib, json, os, sys
import bench_launch as L

HERE = os.path.dirname(os.path.abspath(__file__))
PROD_ENVELOPE_USD, CUMULATIVE_CAP_USD = 2300.0, 3000.0
WORKERS_PER_INSTANCE = 76                 # 76 x 2.32 GiB = 176.3 GiB of 192 GiB on c7a.24xlarge (Codex contract 7)
SENTINELS_PER_ATTEMPT = 4                 # inside the 76, not on top of it
RELEASED = ("rejected",)                  # states whose coordinates return to the pool without ingestion


def run_name(epoch):
    return f"prod-e{int(epoch)}"


def baseline():
    p = os.path.join(HERE, "budget_baseline.json")
    b = json.load(open(p))
    assert b.get("schema") == "t1-aws-budget-baseline-1" and isinstance(b.get("spent_usd"), (int, float))
    return b


def other_runs_charged(exclude):
    """Charged USD of every OTHER run under runs/ (row 23 benchmark, other epochs)."""
    total = 0.0
    for d in sorted(os.listdir(os.path.join(HERE, "runs"))) if os.path.isdir(os.path.join(HERE, "runs")) else []:
        p = os.path.join(HERE, "runs", d, "attempts.json")
        if d != exclude and os.path.exists(p):
            total += sum(L.charged(a) for a in json.load(open(p))["attempts"])
    return total


def budget_problem(led, run, new_worst_usd):
    prod = sum(L.charged(a) for a in led["attempts"])
    others = other_runs_charged(run); base = baseline()["spent_usd"]
    if prod + new_worst_usd > PROD_ENVELOPE_USD + 1e-9:
        return f"production envelope: {prod:.2f} charged + {new_worst_usd:.2f} worst > {PROD_ENVELOPE_USD:.0f}"
    if base + others + prod + new_worst_usd > CUMULATIVE_CAP_USD + 1e-9:
        return f"cumulative cap: baseline {base:.2f} + other runs {others:.2f} + production {prod:.2f} + {new_worst_usd:.2f} > {CUMULATIVE_CAP_USD:.0f}"
    return ""


def owned(led):
    """Coordinates owned by attempts that are not released: {(rep, index): (attempt, sequence)}."""
    own = {}
    for a in led["attempts"]:
        if a.get("state") in RELEASED or a.get("ingestion") in ("ingested", "dispositioned"):
            continue
        for c in a.get("coordinates", []):
            c = tuple(c)
            if c in own:
                raise RuntimeError(f"coordinate {c} owned by attempts {own[c][0]} and {a['attempt']}: the ledger is inconsistent")
            own[c] = (a["attempt"], a["sequence"])
    return own


def allocate(part, led, completed, n):
    """The next n block coordinates in the fixed order, excluding completed and owned ones."""
    own = owned(led)
    order = [(r, i) for i in sorted(part["indices"], reverse=True) for r in part["reps"]]
    free = [c for c in order if c not in completed and c not in own]
    return free[:n]


def sentinels(lengau_completed, token, n=SENTINELS_PER_ATTEMPT):
    """n distinct Lengau-completed coordinates chosen by the attempt token, never by outcome."""
    pool = sorted(lengau_completed)
    if len(pool) < n:
        raise ValueError("fewer Lengau-completed coordinates than sentinels")
    picked, k = [], 0
    while len(picked) < n:
        h = int(hashlib.sha256(f"{token}:{k}".encode()).hexdigest(), 16) % len(pool)
        if pool[h] not in picked:
            picked.append(pool[h])
        k += 1
    return picked


def owner_of(led, coordinate):
    """(attempt, sequence) that owns `coordinate` now, or None - ingestion accepts a record only from this owner."""
    return owned(led).get(tuple(coordinate))

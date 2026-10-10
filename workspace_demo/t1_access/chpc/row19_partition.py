"""Row 19 screen: the provider partition (Codex RSC f3dd3d7 contract 1; design aws_ec2/PRODUCTION_DESIGN.md).

A partition declaration fixes, for one EPOCH, which resample-index coordinates of the frozen screen task belong to EC2.
Lengau's planner and admission refuse every coordinate in the block; EC2's allocator draws only from it. The declaration
is immutable: a change of k is a NEW epoch file, its predecessor named, completed coordinates never transferred, and only
uncompleted, terminal/fenced, explicitly named coordinates handed back.

    t1py chpc/row19_partition.py declare --manifest chpc/row19_screen_manifest.json --k 50 --epoch 1 --out chpc/row19_partition_e1.json
    t1py chpc/row19_partition.py cutover --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json

`cutover` is the activation proof: it reads the Lengau screen root and campaign (every record, every plan of every ledger
entry in ANY state - live, settled, closed-no-record, unresolved) and refuses (exit 3) when any coordinate of the block was
ever completed, planned or reserved by Lengau. A block that passes is provably unassigned at that observation."""
import os, sys, json, glob, hashlib, argparse

SCHEMA = "row19-provider-partition-1"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def declare(man, man_sha, k, epoch, predecessor=None):
    B = int(man["cfg"]["n_boot_refit"]); reps = sorted(int(r) for r in man["datasets"]["reps"])
    if not (isinstance(k, int) and 0 < k < B):
        raise ValueError(f"k must be an integer in 1..{B - 1}")
    idents = man["shard"]["identities"]
    task_digest = hashlib.sha256(json.dumps({str(r): idents[str(r)] for r in reps}, sort_keys=True).encode()).hexdigest()
    return {"schema": SCHEMA, "epoch": int(epoch), "predecessor": predecessor, "provider": "ec2",
            "manifest_sha256": man_sha, "task_identities_sha256": task_digest, "B": B, "reps": reps, "k": k,
            "indices": list(range(B - k, B)),
            "rule": "EC2 owns (rep, index) for every declared rep and every index in `indices`; Lengau never plans or admits them"}


def load(path, man, man_sha):
    """The partition in `path`, validated against this manifest; raises on any mismatch."""
    p = json.load(open(path))
    if p.get("schema") != SCHEMA:
        raise ValueError(f"{path}: not a {SCHEMA} declaration")
    want = declare(man, man_sha, int(p["k"]), int(p["epoch"]), p.get("predecessor"))
    diff = [k for k in want if p.get(k) != want[k]] + [k for k in p if k not in want]
    if diff:
        raise ValueError(f"{path}: differs from the manifest-derived declaration on {sorted(set(diff))}")
    return p


def blocked(part, rep, index):
    return part is not None and int(rep) in part["reps"] and int(index) in part["indices"]


def lengau_claims(man):
    """Every (rep, index) Lengau has completed (record files) or ever planned (plans of ledger entries in any state)."""
    root, camp = man["storage"]["root"], man["storage"]["campaign"]
    done, planned, problems = set(), set(), []
    for p in glob.glob(os.path.join(root, "records", "rep*", "rec_*.json")):
        try:
            r = int(os.path.basename(os.path.dirname(p))[3:]); i = int(os.path.basename(p)[4:7])
            done.add((r, i))
        except ValueError:
            problems.append(f"unparsable record path {p}")
    led = os.path.join(camp, "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    for e in entries:
        if e.get("kind") != "shard":
            continue
        pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
        if not os.path.exists(pp):
            problems.append(f"ledger entry {e.get('job_id')} (job {e['rep']}, {e.get('state')}) has no plan: its claims are unknown")
            continue
        for s in json.load(open(pp)).get("slots", []):
            planned.update((int(s["rep"]), int(i)) for i in s["indices"])
    for pp in glob.glob(os.path.join(root, "plans", "job_*.json")):          # plans with or without a ledger entry
        for s in json.load(open(pp)).get("slots", []):
            planned.update((int(s["rep"]), int(i)) for i in s["indices"])
    return done, planned, problems


def cutover_problems(man, part):
    done, planned, problems = lengau_claims(man)
    hit_d = sorted(c for c in done if blocked(part, *c)); hit_p = sorted(c for c in planned if blocked(part, *c))
    if hit_d:
        problems.append(f"{len(hit_d)} block coordinate(s) already completed by Lengau, e.g. {hit_d[:3]}")
    if hit_p:
        problems.append(f"{len(hit_p)} block coordinate(s) planned or reserved by Lengau, e.g. {hit_p[:3]}")
    return problems, dict(lengau_done=len(done), lengau_planned=len(planned),
                          lengau_max_index=max([i for _, i in done | planned], default=-1), block_lowest=min(part["indices"]))


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("declare"); d.add_argument("--manifest", required=True); d.add_argument("--k", type=int, required=True)
    d.add_argument("--epoch", type=int, required=True); d.add_argument("--predecessor", default=None); d.add_argument("--out", required=True)
    c = sub.add_parser("cutover"); c.add_argument("--manifest", required=True); c.add_argument("--partition", required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); ms = sha_file(a.manifest)
    if a.cmd == "declare":
        if os.path.exists(a.out):
            sys.exit(f"{a.out} exists: a declaration is immutable; declare a new epoch instead")
        json.dump(declare(man, ms, a.k, a.epoch, a.predecessor), open(a.out, "w"), indent=1, sort_keys=True)
        print(f"declared epoch {a.epoch}: k {a.k}, sha256 {sha_file(a.out)}"); return 0
    part = load(a.partition, man, ms)
    problems, facts = cutover_problems(man, part)
    print(json.dumps(dict(partition=os.path.basename(a.partition), partition_sha256=sha_file(a.partition), **facts, problems=problems)))
    return 3 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

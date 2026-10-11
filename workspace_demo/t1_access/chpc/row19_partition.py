"""Row 19 screen: the provider partition (Codex RSC f3dd3d7 contract 1; design aws_ec2/PRODUCTION_DESIGN.md).

A partition declaration fixes, for one EPOCH, which resample-index coordinates of the frozen screen task belong to EC2.
Lengau's planner and admission refuse every coordinate in the block; EC2's allocator draws only from it. The declaration
is immutable: a change of k is a NEW epoch file, its predecessor named, completed coordinates never transferred, and only
uncompleted, terminal/fenced, explicitly named coordinates handed back.

    t1py chpc/row19_partition.py declare --manifest chpc/row19_screen_manifest.json --k 50 --epoch 1 --out chpc/row19_partition_e1.json
    t1py chpc/row19_partition.py cutover --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json

`cutover` is the activation proof: it reads the Lengau screen root and campaign (every record, every plan of every ledger
entry in ANY state - live, settled, closed-no-record, unresolved) and refuses (exit 3) when any coordinate of the block was
ever completed, planned or reserved by Lengau. A block that passes is provably unassigned at that observation.

`activate` (REVISION 2, Codex RSC 0483db4 V10-1) is the SERIALIZED cutover: on the Lengau login node it takes the screen's
plan lock (the same lock every admission and ingestion holds), requires that the LATEST adopted controls version already
pins this partition (so the Lengau guard is live before the scan), runs the cutover scan over every record and every
existing/restored/reserved plan, and writes the immutable proof root/ec2/activation_e<epoch>.json binding the partition,
controls and manifest digests and the digest of the scanned claim sets. EC2 admission requires that proof; while the
latest controls pin a partition with no proof, Lengau refit admission HOLDS too (row19_screen_admit v10). A later epoch
names its predecessor {epoch, sha256, indices}; the coordinates it hands back to Lengau (`transferred` = predecessor block
minus this block) are listed, and activation refuses unless the authority inventory on the root (fresh, sealed) shows no
EC2 attempt still owning any of them: only terminal/fenced, uncompleted coordinates move. Coordinates EC2 completed stay
EC2's records (the register keeps their provenance) whatever the later block."""
import os, sys, json, glob, time, fcntl, hashlib, argparse

SCHEMA = "row19-provider-partition-1"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def declare(man, man_sha, k, epoch, predecessor=None):
    """`predecessor` is None for epoch 1, else {epoch: epoch - 1, sha256: <its file>, indices: <its block>}."""
    B = int(man["cfg"]["n_boot_refit"]); reps = sorted(int(r) for r in man["datasets"]["reps"])
    if not (isinstance(k, int) and not isinstance(k, bool) and 0 < k < B):
        raise ValueError(f"k must be an integer in 1..{B - 1}")
    if (int(epoch) == 1) != (predecessor is None):
        raise ValueError("epoch 1 has no predecessor; every later epoch names exactly its predecessor")
    indices = list(range(B - k, B)); transferred = []
    if predecessor is not None:
        if (sorted(predecessor) != ["epoch", "indices", "sha256"] or predecessor["epoch"] != int(epoch) - 1
                or not isinstance(predecessor["sha256"], str) or len(predecessor["sha256"]) != 64):
            raise ValueError("predecessor must be {epoch: epoch - 1, sha256, indices}")
        transferred = sorted(set(int(i) for i in predecessor["indices"]) - set(indices))
    idents = man["shard"]["identities"]
    task_digest = hashlib.sha256(json.dumps({str(r): idents[str(r)] for r in reps}, sort_keys=True).encode()).hexdigest()
    return {"schema": SCHEMA, "epoch": int(epoch), "predecessor": predecessor, "provider": "ec2",
            "manifest_sha256": man_sha, "task_identities_sha256": task_digest, "B": B, "reps": reps, "k": k,
            "indices": indices, "transferred_indices": transferred,
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


def claims_digest(done, planned):
    return hashlib.sha256(json.dumps(dict(done=sorted(done), planned=sorted(planned))).encode()).hexdigest()


def activate(man, man_path, part_path, controls_path, now=None):
    """The serialized cutover (see the module text). Returns (proof dict, problems); writes nothing itself."""
    import row19_ec2_state as ES
    now = time.time() if now is None else now
    ms = sha_file(man_path); part = load(part_path, man, ms); psha = sha_file(part_path)
    problems = []
    ctl = json.load(open(controls_path)); latest = ctl["versions"][-1]
    if (latest.get("partition") or {}).get("sha256") != psha:
        problems.append(f"the latest controls version {latest.get('version')} does not pin this partition (the Lengau guard is not live)")
    if part["predecessor"] is not None:
        prev = activation_path(man, part["predecessor"]["epoch"])
        if not os.path.exists(prev):
            problems.append(f"the predecessor epoch {part['predecessor']['epoch']} was never activated")
        elif json.load(open(prev)).get("partition_sha256") != part["predecessor"]["sha256"]:
            problems.append("the predecessor's activation is not the named predecessor partition")
        if part["transferred_indices"]:
            invp = ES.paths(man["storage"]["root"])["inventory"]
            inv = json.load(open(invp)) if os.path.exists(invp) else None
            why = ES.inventory_problem(inv, now) if inv is not None else "no authority inventory on the root"
            if why:
                problems.append(f"handback needs a fresh authority inventory: {why}")
            else:
                held = sorted(k for k in inv["owners"] if int(k.split("/")[1]) in part["transferred_indices"])
                if held:
                    problems.append(f"{len(held)} handed-back coordinate(s) still owned by a live EC2 attempt, e.g. {held[:3]}")
    p2, facts = cutover_problems(man, part)
    problems += p2
    done, planned, _ = lengau_claims(man)
    proof = {"schema": ES.ACTIVATION_SCHEMA, "epoch": part["epoch"], "partition_sha256": psha, "manifest_sha256": ms,
             "controls_sha256": sha_file(controls_path), "controls_version": latest.get("version"),
             "predecessor": part["predecessor"], "transferred_indices": part["transferred_indices"],
             "claims_sha256": claims_digest(done, planned), "facts": facts, "at": now}
    return proof, problems


def activation_path(man, epoch):
    return os.path.join(man["storage"]["root"], "ec2", f"activation_e{int(epoch)}.json")


def activation_problem(man, man_sha, part, part_sha, proof):
    """'' when `proof` is THE activation of this partition under this manifest (consumers: both admissions, ingestion)."""
    if not isinstance(proof, dict) or proof.get("schema") != "row19-ec2-activation-1":
        return "no activation proof"
    for k, v in (("epoch", part["epoch"]), ("partition_sha256", part_sha), ("manifest_sha256", man_sha),
                 ("transferred_indices", part["transferred_indices"])):
        if proof.get(k) != v:
            return f"the activation proof's {k} is not this partition's"
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("declare"); d.add_argument("--manifest", required=True); d.add_argument("--k", type=int, required=True)
    d.add_argument("--epoch", type=int, required=True); d.add_argument("--out", required=True)
    d.add_argument("--predecessor", default=None, help="the predecessor epoch's declaration file (every epoch after 1)")
    c = sub.add_parser("cutover"); c.add_argument("--manifest", required=True); c.add_argument("--partition", required=True)
    v = sub.add_parser("activate"); v.add_argument("--manifest", required=True); v.add_argument("--partition", required=True)
    v.add_argument("--controls", default=os.path.join(HERE, "row19_screen_controls.json"))
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); ms = sha_file(a.manifest)
    if a.cmd == "declare":
        if os.path.exists(a.out):
            sys.exit(f"{a.out} exists: a declaration is immutable; declare a new epoch instead")
        pred = None
        if a.predecessor:
            pp = json.load(open(a.predecessor))
            pred = dict(epoch=pp["epoch"], sha256=sha_file(a.predecessor), indices=pp["indices"])
        json.dump(declare(man, ms, a.k, a.epoch, pred), open(a.out, "w"), indent=1, sort_keys=True)
        print(f"declared epoch {a.epoch}: k {a.k}, sha256 {sha_file(a.out)}"); return 0
    if a.cmd == "activate":
        root = man["storage"]["root"]
        with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
            try:
                fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                print("HELD: the plan lock is held (an admission or an ingestion)"); return 3
            proof, problems = activate(man, a.manifest, a.partition, a.controls)
            out = activation_path(man, proof["epoch"])
            if os.path.exists(out):
                print(f"HELD: {out} exists - an activation is immutable"); return 3
            if problems:
                print(json.dumps(dict(problems=problems, facts=proof["facts"]))); return 3
            os.makedirs(os.path.dirname(out), exist_ok=True)
            tmp = f"{out}.tmp.{os.getpid()}"
            with open(tmp, "w") as fh:
                json.dump(proof, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
            os.link(tmp, out); os.unlink(tmp)
        print(f"activated epoch {proof['epoch']}: {out} sha256 {sha_file(out)}"); return 0
    part = load(a.partition, man, ms)
    problems, facts = cutover_problems(man, part)
    print(json.dumps(dict(partition=os.path.basename(a.partition), partition_sha256=sha_file(a.partition), **facts, problems=problems)))
    return 3 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

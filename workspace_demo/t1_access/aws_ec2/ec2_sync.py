"""Mac <-> Lengau EC2 authority sync: replaces the manual scp of inventories and acknowledgements (Codex RSC 3dc0daf R1-2).

    python3 aws_ec2/ec2_sync.py cycle [--dry-run]

One cycle, every step checked and recoverable (re-running a cycle is always safe):
  1. under the authority lock: advance the generation and seal the inventory (prod_authority.write_inventory)
  2. copy it to <root>/ec2/authority/incoming/inventory_g<N>.json on Lengau
  3. install it there with the controller tree's chpc/row19_ec2_root.py install (the root's plan lock; monotonic generations;
     requested dispositions fenced; immutable acknowledgement ack_g<N>.json written)
  4. pull ack_g<N>.json and the root's register.json back into runs/inventory/ (acks/, register_pulled.json)
  5. under the authority lock and each run's lock: disposition-confirm every requested disposition the acknowledgement
     fences (a root REFUSAL is reported and the attempt keeps owning), ack every reconciled pending attempt whose register
     entry is ingested; when anything changed, seal and push/install the next generation in the same cycle.
Nothing is released except through prod_authority.ack / disposition_confirm, which check the root's evidence. Exit 0 in
sync, 3 when the root held the inventory or a step failed (the message says which); --dry-run seals and prints only.
The transport is ssh/scp with ControlPath=none (the shared mux drops long streams); tests substitute a local transport."""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "chpc")]
import prod_authority as PA, bench_launch as L, row19_ec2_state as ES

T = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
CTL = f"{T}/rsc_screen_ctl/workspace_demo/t1_access"
MANIFEST = os.path.join(HERE, "..", "chpc", "row19_screen_manifest.json")


class Ssh:
    """Lengau over ssh/scp, no shared control socket."""
    def __init__(self, host="lengau", t1py=f"{T}/t1py", ctl=CTL):
        self.host, self.t1py, self.ctl = host, t1py, ctl
        self.opts = ["-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes"]

    def put(self, src, dst):
        subprocess.run(["ssh", *self.opts, self.host, "mkdir", "-p", os.path.dirname(dst)], check=True, timeout=120)
        subprocess.run(["scp", *self.opts, "-q", src, f"{self.host}:{dst}"], check=True, timeout=300)

    def get(self, src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        r = subprocess.run(["scp", *self.opts, "-q", f"{self.host}:{src}", dst + ".part"], timeout=300)
        if r.returncode:
            return False
        os.replace(dst + ".part", dst); return True

    def install(self, remote_inventory):
        cmd = f"cd {self.ctl} && {self.t1py} chpc/row19_ec2_root.py install --manifest chpc/row19_screen_manifest.json --inventory {remote_inventory}"
        r = subprocess.run(["ssh", *self.opts, self.host, cmd], capture_output=True, text=True, timeout=600)
        return r.returncode, (r.stdout + r.stderr).strip()


def root_of(manifest=MANIFEST):
    return json.load(open(manifest))["storage"]["root"]


def seal():
    """A new generation every time: the root accepts a generation once (same bytes only), and a sealed inventory carries
    its own time, so re-sealing an installed generation would be refused."""
    with PA.authority_lock(wait_s=60):
        PA.bump(PA.state())
        p = PA.write_inventory()
    return p, json.load(open(p))


def push_install(tr, root, p, inv, log):
    g = int(inv["generation"])
    rinv = os.path.join(root, "ec2", "authority", "incoming", f"inventory_g{g}.json")
    tr.put(p, rinv)
    rc, out = tr.install(rinv)
    log(f"install g{g}: rc {rc}: {out}")
    if rc != 0:
        return None
    ackp = os.path.join(PA.INV_DIR, "acks", f"ack_g{g}.json")
    if not tr.get(ES.ack_path(root, g), ackp):
        log(f"acknowledgement ack_g{g}.json could not be pulled"); return None
    ack = json.load(open(ackp))
    if ack.get("schema") != ES.ACK_SCHEMA or int(ack.get("generation", -1)) != g or ack.get("inventory_sha256") != inv.get("sha256"):
        log(f"ack_g{g}.json does not acknowledge the inventory just sealed"); return None
    return ackp


def settle(ackp, regp, log):
    """Confirm fenced dispositions and acknowledge ingested attempts. Returns the number of ledger changes."""
    ack = json.load(open(ackp)) if ackp else {}
    reg = json.load(open(regp)) if regp and os.path.exists(regp) else {}
    changed = 0
    with PA.authority_lock(wait_s=60):
        for run, led in sorted(PA.ledgers().items()):
            for a in led.get("attempts", []):
                key = f"{run}/{a['attempt']}"
                if a.get("ingestion") != "pending" or a.get("state") != "reconciled":
                    continue
                with L.run_lock(run, wait_s=60):
                    try:
                        if a.get("disposition_request") and key in (ack.get("dispositioned") or {}):
                            if PA.disposition_confirm(run, a["attempt"], ackp):
                                changed += 1; log(f"{key}: disposition confirmed on {os.path.basename(ackp)}")
                        elif a.get("disposition_request") and key in (ack.get("refused") or {}):
                            log(f"{key}: the root REFUSED the disposition ({ack['refused'][key]}); the attempt keeps owning")
                        elif ((reg.get("attempts") or {}).get(a.get("attempt_id")) or {}).get("state") == "ingested":
                            if PA.ack(run, a["attempt"], regp):
                                changed += 1; log(f"{key}: ingestion acknowledged on the root register")
                    except (ValueError, KeyError) as e:
                        log(f"{key}: not released ({e})")
    return changed


def cycle(tr, root, log=print, dry_run=False):
    p, inv = seal()
    log(f"sealed generation {inv['generation']} ({inv['sha256'][:12]}) -> {p}")
    if dry_run:
        return 0
    ackp = push_install(tr, root, p, inv, log)
    if ackp is None:
        return 3
    regp = os.path.join(PA.INV_DIR, "register_pulled.json")
    if not tr.get(ES.paths(root)["register"], regp):
        regp = None; log("no register on the root yet (nothing ingested)")
    if settle(ackp, regp, log):
        p, inv = seal()
        log(f"sealed generation {inv['generation']} after releases")
        if push_install(tr, root, p, inv, log) is None:
            return 3
    return 0


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cycle"); c.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    try:
        return cycle(Ssh(), root_of(), dry_run=a.dry_run)
    except BlockingIOError:
        sys.exit("REFUSED: another authority operation holds runs/.authority.lock")


if __name__ == "__main__":
    sys.exit(main())

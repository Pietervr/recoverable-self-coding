"""Row 19 screen: install the Mac claim authority's sealed inventory on the Lengau screen root (Codex RSC 3dc0daf R1-2).

    t1py chpc/row19_ec2_root.py install --manifest chpc/row19_screen_manifest.json --inventory <copied inventory_g<N>.json>

Runs on the Lengau login node under the screen's plan lock (plans/.submit.lock, shared with every admission, activation and
ingestion), so an installation never interleaves with them. row19_ec2_state.install_inventory is the rule: strictly newer
generation (the same generation only with the same bytes), requested dispositions fenced in the register in the same step,
the immutable acknowledgement ec2/authority/ack_g<N>.json written. Copy that acknowledgement back to the Mac and run
`prod_authority.py disposition-confirm` before any ownership is released. Exit 0 installed (or already installed), 3 held."""
import os, sys, json, fcntl, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import row19_ec2_state as ES


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("install"); i.add_argument("--manifest", required=True); i.add_argument("--inventory", required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); root = man["storage"]["root"]
    try:
        inv = json.load(open(a.inventory))
    except Exception as e:
        print(f"HELD: the inventory is unreadable ({e})"); return 3
    os.makedirs(os.path.join(root, "plans"), exist_ok=True)
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: the plan lock is held (an admission, an activation or an ingestion)"); return 3
        ack, problems = ES.install_inventory(root, inv)
    if problems:
        print("HELD: " + "; ".join(problems)); return 3
    print(f"installed generation {ack['generation']} ({ack['inventory_sha256'][:12]}); fenced {sorted(ack['dispositioned'])}, "
          f"refused {sorted(ack['refused'])}; acknowledgement {ES.ack_path(root, ack['generation'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

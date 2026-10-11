"""Row 19 screen: install the Mac claim authority's sealed inventory on the Lengau screen root (Codex RSC 3dc0daf R1-2).

    t1py chpc/row19_ec2_root.py install --manifest chpc/row19_screen_manifest.json --inventory <copied inventory_g<N>.json>

Runs on the Lengau login node under the screen's plan lock (plans/.submit.lock, shared with every admission, activation and
ingestion), so an installation never interleaves with them. row19_ec2_state.install_inventory is the rule: strictly newer
generation (the same generation only with the same bytes), requested dispositions fenced in the register in the same step,
the immutable acknowledgement ec2/authority/ack_g<N>.json written. Copy that acknowledgement back to the Mac and run
`prod_authority.py disposition-confirm` before any ownership is released. Exit 0 installed (or already installed), 3 held.

REVISION 2 (Codex RSC 299f4b7 R2-1): the installation names its root identity in the acknowledgement. Mode `canonical` is
granted ONLY when --manifest is THE production screen manifest file (chpc/row19_screen_manifest.json of this tree, sha256
43b75f94) and the root is its own storage root; any other manifest (the isolated S manifest, a test sandbox) installs only
with --sandbox and its acknowledgement says `sandbox`, which the Mac never accepts for a disposition."""
import os, sys, json, fcntl, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import row19_ec2_state as ES

CANONICAL_MANIFEST = os.path.join(HERE, "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"


def identity(manifest_path, man, sandbox=False):
    """(root identity, '') for this installation, or (None, why)."""
    root = os.path.abspath(man["storage"]["root"])
    msha = ES.sha_file(manifest_path)
    canonical = os.path.abspath(manifest_path) == os.path.abspath(CANONICAL_MANIFEST) and msha == PROD_SHA
    if sandbox:
        if canonical:
            return None, "--sandbox with the production screen manifest: a canonical root is never installed as a sandbox"
        return dict(root=root, manifest_sha256=msha, mode="sandbox"), ""
    if not canonical:
        return None, (f"{manifest_path} is not the production screen manifest {PROD_SHA[:8]} of this tree: only --sandbox "
                      "installs another root (its acknowledgement can never release ownership)")
    return dict(root=root, manifest_sha256=msha, mode="canonical"), ""


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("install"); i.add_argument("--manifest", required=True); i.add_argument("--inventory", required=True)
    i.add_argument("--sandbox", action="store_true", help="a non-canonical root (tests, the isolated S root): acknowledged as sandbox")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); root = man["storage"]["root"]
    ident, why = identity(a.manifest, man, a.sandbox)
    if why:
        print(f"HELD: {why}"); return 3
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
        ack, problems = ES.install_inventory(root, inv, ident)
    if problems:
        print("HELD: " + "; ".join(problems)); return 3
    print(f"installed generation {ack['generation']} [{ack['mode']}] ({ack['inventory_sha256'][:12]}); fenced {sorted(ack['dispositioned'])}, "
          f"refused {sorted(ack['refused'])}; acknowledgement {ES.ack_path(root, ack['generation'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

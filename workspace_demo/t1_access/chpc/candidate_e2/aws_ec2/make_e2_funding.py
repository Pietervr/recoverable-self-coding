"""Row 19 screen on EC2, provider epoch 2 - CANDIDATE, not adopted: write the epoch-2 funding declaration
(t1-ec2-epoch-funding-1) that prod_authority.epoch2_problem enforces. Every number is DERIVED (prod_authority.funding_e2) from
the schema-2 partition and the owner constants of 17 Oct 2026 (five instances, USD 300 allowance, two qualification
instances, four extra production batches); funding_problem re-derives it at every admission and refuses any other bytes.

    python3 make_e2_funding.py --partition ../row19_partition_e2.json --out e2_funding.json

The forecast basis is the reconciled Q2 attempt from the authority ledger (runs/qual-Q2, charged at its observed hours) and
its slot outcome (24 planned, 23 exit 0: slot 12, rep 15 / index 199, exit 139 - R052 log 16 Oct, Codex design s.3). The two
Q2-derived forecasts extrapolate a 24-worker packing to the 76-worker one; they are cost illustrations, not measured
production rates. The carried (higher) one plus the allowance is the epoch cap."""
import argparse, json, os, sys
SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import prod_authority as PA
import row19_partition as RP

Q2_PLANNED, Q2_SUCCESSFUL = 24, 23


def q2_charged(leds):
    atts = [a for a in leds.get("qual-Q2", {"attempts": []})["attempts"] if a.get("state") == "reconciled"]
    if len(atts) != 1:
        raise ValueError(f"expected exactly one reconciled Q2 attempt, found {len(atts)}")
    return PA.charged(atts[0])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--partition", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--designated", default=None, help="override of the designated declaration path (before v16 promotion)")
    a = ap.parse_args()
    if a.designated:
        RP.DESIGNATED_PATH = os.path.abspath(a.designated)
    man_path = os.path.join(PA.T1, "chpc", "row19_screen_manifest.json")
    part = RP.load(a.partition, json.load(open(man_path)), RP.sha_file(man_path))
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists: a funding declaration is immutable")
    fund = PA.funding_e2(part, round(q2_charged(PA.ledgers()), 6), Q2_PLANNED, Q2_SUCCESSFUL,
                         "Q2 basis from runs/qual-Q2/attempts.json (reconciled) and its 23/24 slot outcome; owner decisions 17 Oct 2026")
    why = PA.funding_problem(fund, part)
    if why:
        raise SystemExit(f"REFUSED: {why}")
    json.dump(fund, open(a.out, "w"), indent=1, sort_keys=True)
    print(json.dumps({k: fund[k] for k in ("owned_coordinates", "base_batches", "paid_slots", "forecast", "funding_maxima_all_base_usd",
                                           "epoch_cap_usd", "calendar_days_at_fleet")}, indent=1))


if __name__ == "__main__":
    main()

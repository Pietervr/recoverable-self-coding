#!/bin/bash
# Reproduce the adopt_pilot17.sh literal-check failure: sed | grep -q under pipefail with a record > sed's buffer.
set -u -o pipefail
D=$(mktemp -d)
LIT="ADOPT row19-screen-pilot role=refit qualification=abc max_job=100"
{ echo "# review"; echo '```text'; echo "$LIT"; echo '```'; for i in $(seq 1 400); do echo "filler line $i of the review body to exceed four kilobytes of sed output buffering"; done; } > "$D/rec"
echo "record bytes: $(wc -c < "$D/rec")"
old=0; for n in 1 2 3 4 5; do sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$D/rec" | grep -qxF -- "$LIT" && old=$((old+1)); done
new=0; for n in 1 2 3 4 5; do sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$D/rec" | grep -xF -- "$LIT" >/dev/null && new=$((new+1)); done
absent=0; sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$D/rec" | grep -xF -- "ADOPT other" >/dev/null && absent=1
echo "old form passed $old/5; new form passed $new/5; new form on an absent literal passed $absent/1 (must be 0)"
rm -rf "$D"

#!/bin/bash
# Bundle the jitter study for an AWS worker: the jitter code, the two inherited modules it imports (fit_models.py,
# bms.py and their helper common.py), the 60 stored S1 generator files and the bases cache (levels, blocks, real
# 53-window means of the 20 base participants; O5 needs them). No raw EEG preds leave the Mac. Output:
#   jitter/aws/bundle/jitter_bundle_<RSC short hash>.tar.gz  + SHA256
# usage: bash aws/make_bundle.sh   (from the jitter directory)
set -euo pipefail
J=/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/sergent_port/jitter
SP=/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/sergent_port
HASH=$(git -C /Users/pietervanrooyen/Recoverable-Self-Coding rev-parse --short HEAD)
OUT=$J/aws/bundle
mkdir -p "$OUT"
STAGE=$(mktemp -d)
mkdir -p "$STAGE/sergent_port/jitter/results/generators" "$STAGE/sergent_port/jitter/results/s4" "$STAGE/sergent_port/jitter/results/s2/diagnosis" "$STAGE/sergent_port/jitter/aws"
cp "$SP"/fit_models.py "$SP"/bms.py "$SP"/common.py "$STAGE/sergent_port/"
cp "$J"/*.py "$STAGE/sergent_port/jitter/"
cp "$J"/DESIGN_jitter.md "$STAGE/sergent_port/jitter/"
cp "$J"/results/s2/diagnosis/*.py "$STAGE/sergent_port/jitter/results/s2/diagnosis/"
cp "$J"/aws/s2_closure.sh "$STAGE/sergent_port/jitter/aws/"
cp "$J"/results/generators/*.npz "$J"/results/generators/bases_active.json "$STAGE/sergent_port/jitter/results/generators/"
echo "$HASH" > "$STAGE/sergent_port/jitter/BUNDLE_RSC_HASH"
tar -C "$STAGE" -czf "$OUT/jitter_bundle_$HASH.tar.gz" sergent_port
shasum -a 256 "$OUT/jitter_bundle_$HASH.tar.gz" | tee "$OUT/jitter_bundle_$HASH.tar.gz.sha256"
du -h "$OUT/jitter_bundle_$HASH.tar.gz"
rm -rf "$STAGE"

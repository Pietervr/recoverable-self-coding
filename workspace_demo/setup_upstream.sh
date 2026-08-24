#!/usr/bin/env bash
# setup_upstream.sh — clone the two upstream J-lens repos into upstream/
# (gitignored; not vendored). Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/upstream"
[ -d "$HERE/upstream/jacobian-lens/.git" ] || \
  git clone --depth 1 https://github.com/anthropics/jacobian-lens "$HERE/upstream/jacobian-lens"
[ -d "$HERE/upstream/jlens-qwen36/.git" ] || \
  git clone --depth 1 https://github.com/WeZZard/jlens-qwen36 "$HERE/upstream/jlens-qwen36"
echo "upstream ready:"
ls -d "$HERE"/upstream/*/

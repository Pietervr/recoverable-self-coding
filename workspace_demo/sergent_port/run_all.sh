#!/bin/sh
# Full pipeline, detached-friendly:  nohup sh run_all.sh > <log> 2>&1 &
# Steps: decode active + passive (all 20 subjects) -> fit the three models -> group BMS -> figures.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
PY="$HERE/../../.venv/bin/python"
NJ="${NJOBS:-6}"
STEP="${1:-all}"

if [ "$STEP" = "all" ] || [ "$STEP" = "decode" ]; then
  "$PY" "$HERE/decode.py" --session active  --subjects 1-20 --n-jobs "$NJ"
  "$PY" "$HERE/decode.py" --session passive --subjects 1-20 --n-jobs "$NJ"
fi
if [ "$STEP" = "all" ] || [ "$STEP" = "fit" ]; then
  "$PY" "$HERE/fit_models.py" --session active  --subjects 1-20 --n-jobs "$NJ"
  "$PY" "$HERE/fit_models.py" --session passive --subjects 1-20 --n-jobs "$NJ"
fi
if [ "$STEP" = "all" ] || [ "$STEP" = "compare" ]; then
  "$PY" "$HERE/model_comparison.py" --session active
  "$PY" "$HERE/model_comparison.py" --session passive
fi
if [ "$STEP" = "all" ] || [ "$STEP" = "figures" ]; then
  "$PY" "$HERE/make_figures.py"
fi
echo "run_all.sh: done ($STEP)"

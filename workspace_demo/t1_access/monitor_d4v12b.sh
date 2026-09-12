#!/bin/zsh
# monitor_d4v12b.sh — the session's 30-minute watch on run d4v12b (durable copy of the scratchpad script).
# Arm from a Claude session as a persistent Monitor:  Monitor(command="zsh <this file>", persistent=true)
# Every 30 min it emits: the spot check (one line per stage; SPOTCHECK ERROR if it exits non-zero — duplicate
# keys / mixed code hash / invalid rows); an ACTION line when the job-written gain file lands without a
# revalidated artefact; the fleet counts by status and every job not InProgress; the job-start counts when
# they change (a spot restart = a job started more than once; an on-demand restart is flagged); and a
# "dashboard built … — republish" line after rebuilding the run page, which the session then republishes to
# the artifact https://claude.ai/code/artifact/26e608c6-83f7-43f4-abdd-d5df9073b5fd (pass url=).
PY=$HOME/Recoverable-Self-Coding/workspace_demo/t1_access/.venv/bin/python
T1=$HOME/Recoverable-Self-Coding/workspace_demo/t1_access
SCR=$T1/sim_results/d4v12b/monitor
mkdir -p "$SCR"
OUT=$SCR/spotcheck.out
STAT=$SCR/status.out
STARTS=$SCR/starts.out
PREV=$SCR/starts.prev
while true; do
  stamp=$(date -u +%H:%MZ)
  "$PY" "$T1/spotcheck.py" --run d4v12b --brief > "$OUT" 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "[$stamp] SPOTCHECK ERROR (exit $rc): $(tail -3 "$OUT" | tr '\n' ' ')"
  else
    grep -v '^[[:space:]]*$' "$OUT" | grep -v WARNING | sed "s/^/[$stamp] /"
  fi
  if grep -q 'gate applied to gain_calibration_D4.json' "$OUT" && [ ! -f "$T1/sim_results/d4v12b/gain_calibration_D4.revalidated.json" ]; then
    echo "[$stamp] ACTION: gain_calibration_D4.json landed and no revalidated artefact exists — run spotcheck.py --run d4v12b --revalidate 4"
  fi
  "$PY" "$T1/launch_t1.py" --status > "$STAT" 2>&1
  if grep -q 'd4v12b' "$STAT"; then
    grep 'd4v12b' "$STAT" | awk -v s="$stamp" '{c[$2]++} END {line="[" s "] fleet d4v12b:"; for (k in c) line=line " " c[k] " " k; print line}'
    grep 'd4v12b' "$STAT" | awk -v s="$stamp" '$2 != "InProgress" {print "[" s "] job " $1 " " $2 "/" $3 " (" $5 " h train)"}'
  else
    echo "[$stamp] FLEET STATUS UNAVAILABLE: $(tail -2 "$STAT" | tr '\n' ' ')"
  fi
  aws --profile xtenure-read --region eu-north-1 logs tail /aws/sagemaker/TrainingJobs --log-stream-name-prefix t1-all-d4-d4v12b-s --since 3d --format detailed 2>/dev/null \
    | grep 'task=all' | awk '{split($2,a,"/"); n=a[1]; sub(/^t1-all-d4-d4v12b-/,"",n); sub(/of160-[0-9]+$/,"",n); c[n]++} END {for (k in c) print k, c[k]}' | sort > "$STARTS"
  total=$(awk '{s+=$2} END {print s+0}' "$STARTS")
  prev=$(cat "$PREV" 2>/dev/null)
  if [ -n "$total" ] && [ "$total" != "$prev" ]; then
    echo "$total" > "$PREV"
    awk -v s="$stamp" -v t="$total" 'BEGIN {line="[" s "] job starts " t " over 50 jobs; started more than once:"; od=""} $2 > 1 {line=line " " $1 "x" $2; if (substr($1,2,3)+0 >= 20) od=od " " $1} END {print line; if (od != "") print "[" s "] ON-DEMAND RESTART (abnormal):" od}' "$STARTS"
  fi
  "$PY" "$T1/dashboard.py" --run d4v12b --out "$SCR/run_d4v12b.html" --status-file "$STAT" --starts-file "$STARTS" > "$SCR/dashboard.out" 2>&1 \
    && echo "[$stamp] dashboard built: $(tail -1 "$SCR/dashboard.out" | sed 's#.*run_d4v12b.html: ##') — republish $SCR/run_d4v12b.html" \
    || echo "[$stamp] DASHBOARD BUILD FAILED: $(grep -v WARNING "$SCR/dashboard.out" | tail -2 | tr '\n' ' ')"
  sleep 1800
done

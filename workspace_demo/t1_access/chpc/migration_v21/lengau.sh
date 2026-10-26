#!/bin/bash
# migration_v21 Mac -> Lengau transport (the migration_v20 lengau.sh, re-pointed). Composes ONE script - remote_lib.sh (the fixed
# production toolchain root, the drain, lock, git, containment and science-digest checks), the archive checker lengau_archive.py,
# any payload files (base64, with their Mac SHA-256) and variables, then the body - and runs it on Lengau with `bash -s`. The
# single line tagged transport is the only route off the Mac; there is no test hook (tests substitute that line in private copies
# only).
#   sourced by preflight_v21.sh, archive_v20.sh, deploy_v21.sh, raise_cap_v21.sh:   to_lengau <body|-> [--file <rel>]... [--var NAME=VALUE]...
#   direct, from workspace_demo/t1_access:
#     bash chpc/migration_v21/lengau.sh rollover_pilot_v21.sh
#     bash chpc/migration_v21/lengau.sh adopt_pilot21.sh --file reviews/<record>.md
V21_DIR=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || { echo "lengau.sh: cannot locate its folder"; exit 2; }

compose() {   # compose <body file name in this folder, or - for stdin> [--file rel]... [--var NAME=VALUE]...
  local body=$1 n=0 f s; shift
  cat "$V21_DIR/remote_lib.sh" || return 1
  printf "IFS= read -r -d '' ARCHIVE_PY <<'V21_PY_EOF'\n" && cat "$V21_DIR/lengau_archive.py" && printf "V21_PY_EOF\n" || return 1
  while [ $# -gt 0 ]; do
    case $1 in
      --file)
        f=${2:-}; [ -f "$f" ] && [ ! -L "$f" ] || { echo "lengau.sh: payload $f is not a regular file" >&2; return 1; }
        n=$((n + 1)); s=$(shasum -a 256 -- "$f") || return 1; s=${s%% *}
        printf 'P%d_PATH=%q\nP%d_SHA=%s\n' $n "$f" $n "$s" || return 1
        printf "IFS= read -r -d '' P%d_B64 <<'V21_B64_EOF'\n" $n && base64 -b 76 -i "$f" && printf "\nV21_B64_EOF\n" || return 1
        shift 2;;
      --var)
        case ${2:-} in [A-Z]*=*) ;; *) echo "lengau.sh: bad --var ${2:-}" >&2; return 1;; esac
        printf '%s=%q\n' "${2%%=*}" "${2#*=}" || return 1; shift 2;;
      *) echo "lengau.sh: unknown argument $1" >&2; return 1;;
    esac
  done
  printf 'NP=%d\n' $n
  if [ "$body" = - ]; then cat; else cat "$V21_DIR/$body"; fi
}

to_lengau() {   # to_lengau <body|-> [args]: compose, then run on Lengau; returns the remote exit status
  local s
  s=$(compose "$@") || { echo "lengau.sh: cannot compose the Lengau script" >&2; return 1; }
  printf '%s\n' "$s" | ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s   # @transport
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -u -o pipefail
  [ -f chpc/row19_screen_admit.py ] && [ -d reviews ] || { echo "run from workspace_demo/t1_access"; exit 2; }
  case ${1:-} in
    rollover_pilot_v21.sh) [ $# = 1 ] || { echo "$1 takes no arguments"; exit 2; };;
    adopt_pilot21.sh) [ $# = 3 ] && [ "$2" = --file ] || { echo "usage: lengau.sh adopt_pilot21.sh --file reviews/<record>.md"; exit 2; };;
    *) echo "lengau.sh runs only rollover_pilot_v21.sh or adopt_pilot21.sh directly"; exit 2;;
  esac
  to_lengau "$@"
fi

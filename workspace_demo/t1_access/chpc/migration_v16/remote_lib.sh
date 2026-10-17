# migration_v16 Lengau prelude. lengau.sh sends this file, the embedded archive checker (lengau_archive.py), any payload files
# and ONE body (from preflight_v16.sh, archive_v15.sh, deploy_v16.sh, rollover_pilot_v16.sh or adopt_pilot16.sh) to Lengau as
# a single `bash -s` script. Never run alone. The toolchain root below is the fixed production route: there is no test hook
# in this file or in any production script (tests run private copies; see test_migration_v16.py). Containment: every fixed root
# below and every authority source / mutation destination a body uses must be its own physical path in its canonical scope
# (canon, src_file, dst_file, dst_absent, dst_dir), never in the scientific clone; the controller and scientific roots are
# distinct and disjoint.
set -u -o pipefail
umask 022
V16_PRELUDE=1
T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain   # @root
ME=pvanrooyen
die() { echo "ABORT: $*"; exit 1; }
T=$(cd -P -- "$T_ROOT" 2>/dev/null && pwd -P) || die "the toolchain root $T_ROOT is not reachable"
C=$T/rsc_screen_ctl/workspace_demo/t1_access     # the controller clone (the only clone the migration changes)
J=$T/rsc_screen/workspace_demo/t1_access         # the scientific job clone (read only, never changed)
G=$T/row19_screen/gate; R=$T/row19_screen/gate_retired; A=$T/archive_screen/v15_before_v16
LOCKS="$T/programme_admission.lock $T/row19_screen/plans/.submit.lock"
V15_CONTROLS=828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5
V15_ADOPTION=970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d
V15_ADMIT=ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac
V15_STATUS=0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b
V15_QUAL=3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c
V16_CONTROLS=01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220
# the job clone's fixed science inventory: every file must exist, read and hash, before and after any controller change
SCI="chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py chpc/row19_ledger.py chpc/row19_slice.py chpc/row19_screen_orig.py"
CTLPAT='row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition'

CR=$T/rsc_screen_ctl                              # the canonical controller clone root (all controller mutations stay beneath it)
JR=$T/rsc_screen                                  # the canonical scientific job clone root (never a mutation destination)
PROOF=$T/archive_screen/v16_deploy_proof          # deploy_v16.sh's durable science before/after proof (written before any controller change)

phys() {   # phys <abs path>: its physical path with every symlink resolved; components that do not exist yet are appended as named
  local p=$1 tail="" r
  case $p in /*) ;; *) return 1;; esac
  while [ ! -e "$p" ]; do
    [ -L "$p" ] && return 1                       # a dangling symlink is never a safe destination
    tail=/${p##*/}$tail; p=${p%/*}; [ -n "$p" ] || return 1
  done
  r=$(realpath -- "$p") || return 1
  printf '%s%s\n' "$r" "$tail"
}
# CONTAINMENT (Codex re-review 2026-10-17, P2): a path is used only when it is its OWN physical path - lexically clean and with
# no symlink, alias or special file in any existing component, up to and including the leaf - and lies strictly beneath its
# intended canonical scope. A root check alone is never enough: every authority source and every mutation destination (and the
# nearest existing parent of a new one) is checked again immediately before it is used. No mutation destination may lie in the
# scientific job clone, even though that clone is beneath $T.
canon() {  # canon <abs path>: lexically clean and physically exactly as named
  case $1 in /*) ;; *) return 1;; esac
  case $1 in *//*|*/./*|*/../*|*/.|*/..|*/) return 1;; esac
  local r; r=$(phys "$1") || return 1
  [ "$r" = "$1" ]
}
clean_rel() {   # clean_rel <relative path>: plain portable components only (no absolute path, no empty, hidden, . or .. component)
  case $1 in ""|/*|*//*|*/|.*|*/.*) return 1;; esac
  case $1 in *[!A-Za-z0-9._/+=@,:~-]*) return 1;; esac
}
scoped() {   # scoped <abs path> <canonical scope root> <what>
  canon "$1" || die "$3: $1 is not its own physical path (a symlink, alias or unclean name in it resolves elsewhere); refusing"
  case $1 in "$2"/*) ;; *) die "$3: $1 is not beneath its scope $2; refusing";; esac
}
src_file() {   # src_file <abs path> <scope> <what>: an authority source - scoped, an existing regular file (no symlink, no special)
  scoped "$@"
  [ -f "$1" ] && [ ! -L "$1" ] || die "$3: $1 is not an existing regular file; refusing"
}
not_science() {   # not_science <abs path> <what>: never inside the scientific job clone
  case $1 in "$JR"|"$JR"/*) die "$2: $1 is inside the scientific job clone $JR; refusing";; esac
}
real_parent() {   # real_parent <abs path> <what>: the nearest EXISTING parent is a real directory (not a file, symlink or special)
  local a=${1%/*}
  while [ ! -e "$a" ] && [ ! -L "$a" ]; do a=${a%/*}; [ -n "$a" ] || die "$2: $1 has no existing parent"; done
  [ -d "$a" ] && [ ! -L "$a" ] || die "$2: the nearest existing parent $a of $1 is not a real directory; refusing"
}
dst_file() {   # dst_file <abs path> <scope> <what>: a file mutation destination - scoped, not science, absent or a regular file
  scoped "$@"; not_science "$1" "$3"; real_parent "$1" "$3"
  if [ -e "$1" ] || [ -L "$1" ]; then [ -f "$1" ] && [ ! -L "$1" ] || die "$3: $1 exists and is not a regular file; refusing"; fi
}
dst_absent() {   # dst_absent <abs path> <scope> <what>: a NEW file or directory destination - as dst_file, and nothing there yet
  scoped "$@"; not_science "$1" "$3"; real_parent "$1" "$3"
  [ ! -e "$1" ] && [ ! -L "$1" ] || die "$3: $1 already exists; refusing"
}
dst_dir() {   # dst_dir <abs path> <scope> <what>: a directory destination - scoped, not science, absent or a real directory
  scoped "$@"; not_science "$1" "$3"; real_parent "$1" "$3"
  if [ -e "$1" ] || [ -L "$1" ]; then [ -d "$1" ] && [ ! -L "$1" ] || die "$3: $1 exists and is not a real directory; refusing"; fi
}
# LENGAU TOOLS (observed 17 Oct 2026, CentOS 7.9): git 1.8.3.1 (no `git -C`, no `rev-parse --absolute-git-dir`), util-linux
# 2.23.2 flock (no -E/--conflict-exit-code), coreutils 8.22, Python 3.6.8. Every git call runs in a subshell that cds first.
ctl_git() {   # the controller clone's git work tree and git directory are its own canonical root (no gitfile or alias elsewhere)
  local top gr gd
  top=$(cd -- "$C" && git rev-parse --show-toplevel) || die "git rev-parse failed in $C"
  gr=$(cd -- "$C" && git rev-parse --git-dir) || die "git rev-parse --git-dir failed in $C"
  case $gr in
    "") die "git rev-parse --git-dir printed nothing in $C";;
    /*) [ "$gr" = "$CR/.git" ] || die "the controller clone's git directory is $gr, not the real $CR/.git; refusing"; gd=$gr;;
    *) gd=$C/$gr;;
  esac
  gd=$(cd -P -- "$gd" 2>/dev/null && pwd -P) || die "the controller clone's git directory $gr does not resolve to a directory; refusing"
  [ "$top" = "$CR" ] || die "the controller clone's work tree is $top, not $CR; refusing"
  [ "$gd" = "$CR/.git" ] && canon "$gd" && [ -d "$gd" ] && [ ! -L "$gd" ] || die "the controller clone's git directory is $gd, not the real $CR/.git; refusing"
}
# the fixed roots: each must be its own physical path beneath the physical toolchain root (no symlink or alias, inside or out)
for p in "$CR" "$C" "$JR" "$J" "$T/row19_screen" "$G" "$R" "$T/row19_screen/plans" "$T/row19_screen/ec2" \
         "$T/archive_screen" "$A" "$PROOF" "$T/jobs" "$T/row19_screen_campaign" $LOCKS; do
  canon "$p" || die "$p is not its own physical path (it resolves to $(phys "$p" 2>/dev/null || echo 'an unsafe target'): a symlink or alias); refusing"
  case $p in "$T"/*) ;; *) die "$p is not beneath the toolchain root $T; refusing";; esac
done
# the controller and scientific roots are distinct and disjoint; no controller, gate or archive root lies in the science clone
[ "$CR" != "$JR" ] || die "the controller and scientific clone roots are the same path"
case $CR/ in "$JR"/*) die "the controller clone root $CR lies inside the scientific clone $JR";; esac
case $JR/ in "$CR"/*) die "the scientific clone root $JR lies inside the controller clone $CR";; esac
if [ -e "$CR" ] && [ -e "$JR" ] && [ "$CR" -ef "$JR" ]; then die "the controller and scientific clone roots are the same directory"; fi
for p in "$C" "$G" "$R" "$A" "$PROOF" "$T/archive_screen"; do not_science "$p" "fixed root"; done

h() { local o; o=$(sha256sum -- "$1") || return 1; o=${o%% *}; [ ${#o} = 64 ] || return 1; printf '%s\n' "$o"; }
pin() {    # pin <file> <sha256> <what>
  [ -f "$1" ] || die "$3: $1 is missing"
  local x; x=$(h "$1") || die "$3: cannot hash $1"
  [ "$x" = "$2" ] || die "$3: $1 is ${x:0:16}, not ${2:0:16}"
}
drained() {   # a successful, non-empty process inventory that shows no controller command of $ME; anything else refuses
  local out rc m
  out=$(ps -u "$ME" -o args=); rc=$?
  [ $rc = 0 ] || die "the process inventory failed (ps exited $rc); the drain is not observed"
  [ -n "$out" ] || die "the process inventory is empty (not even this shell); the drain is not observed"
  m=$(printf '%s\n' "$out" | grep -E -- "$CTLPAT"); rc=$?
  case $rc in
    0) printf '%s\n' "$m"; die "a controller command runs on the login node (above)";;
    1) ;;
    *) die "the process filter failed (grep exited $rc)";;
  esac
}
LOCK_PY='import errno, fcntl, sys
try:
    fh = open(sys.argv[1], "rb")
except OSError as e:
    print("cannot open %s: %s" % (sys.argv[1], e)); sys.exit(3)
try:
    fcntl.flock(fh.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
except OSError as e:
    if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES):
        sys.exit(75)
    print("flock(2) on %s failed: %s" % (sys.argv[1], e)); sys.exit(3)
fcntl.flock(fh.fileno(), fcntl.LOCK_UN); sys.exit(0)'
lock_free() {   # a checked non-blocking SHARED flock on the controllers' own lock file; held or unprobeable refuses
  local L=$1 rc
  [ -f "$L" ] || die "lock file $L is missing; it cannot be probed"
  if command -v flock >/dev/null 2>&1; then
    flock -n -s "$L" true; rc=$?          # util-linux 2.23 has no -E: a -n conflict exits 1 (`true` itself never exits 1)
    case $rc in 0) return 0;; 1) die "lock held: $L";; esac
    echo "flock(1) probe of $L failed (exit $rc); trying the python fcntl probe"
  fi
  "$T/t1py" -c "$LOCK_PY" "$L"; rc=$?
  case $rc in 0) return 0;; 75) die "lock held: $L";; *) die "no reliable lock probe for $L (python fcntl probe exited $rc)";; esac
}
locks_free() { local L; for L in $LOCKS; do lock_free "$L"; done; }
git_clean() {   # git_clean <dir>: a SUCCESSFUL git status with nothing to report
  local st
  st=$(cd -- "$1" && git status --porcelain) || die "git status failed in $1"
  [ -z "$st" ] || { printf '%s\n' "$st" | head -5; die "$1 has uncommitted changes (above)"; }
}
sci_manifest() {   # the complete digest list of the job clone's fixed science inventory on stdout, or failure
  local f out names
  for f in $SCI; do [ -f "$J/$f" ] && [ -r "$J/$f" ] || { echo "ABORT: job-clone science input missing or unreadable: $f"; return 1; }; done
  for f in $SCI; do canon "$J/$f" && [ ! -L "$J/$f" ] || { echo "ABORT: job-clone science input is not its own physical path (symlink or alias): $f"; return 1; }; done
  out=$(cd "$J" && sha256sum -- $SCI) || { echo "ABORT: a job-clone science digest command failed"; return 1; }
  names=$(printf '%s\n' "$out" | awk '$1 ~ /^[0-9a-f]{64}$/ && NF == 2 {print $2}') || { echo "ABORT: cannot parse the science digests"; return 1; }
  [ "$names" = "$(printf '%s\n' $SCI)" ] || { echo "ABORT: the science digest list is incomplete or malformed"; return 1; }
  printf '%s\n' "$out"
}
archive_py() { "$T/t1py" -c "$ARCHIVE_PY" "$@"; }   # ARCHIVE_PY (lengau_archive.py) is embedded by lengau.sh after this file
payload() {   # payload <i> <dest>: decode payload file i to <dest> and check its SHA-256 against the Mac's
  local p b s
  eval "p=\${P$1_PATH:-}; b=\${P$1_B64:-}; s=\${P$1_SHA:-}"
  [ -n "$p" ] && [ -n "$s" ] || die "payload $1 is not defined"
  printf '%s' "$b" | base64 -d > "$2" || die "payload $1 ($p) does not decode"
  [ "$(h "$2")" = "$s" ] || die "payload $1 ($p) does not match its Mac SHA-256"
}

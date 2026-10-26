# migration_v21 Lengau prelude (the migration_v20 remote_lib.sh, re-pointed at the adopted v20 state and the v21 package).
# lengau.sh sends this file, the embedded archive checker (lengau_archive.py), any payload files and ONE body (preflight_v21.sh,
# archive_v20.sh, deploy_v21.sh, raise_cap_v21.sh, rollover_pilot_v21.sh or adopt_pilot21.sh) to Lengau as a single `bash -s`
# script. Never run alone. The toolchain root below is the fixed production route: there is no test hook in this file or in any
# production script.
# Containment (the migration_v16 rules, Codex re-review 2026-10-17 P2, carried unchanged through v20): every fixed root below and
# every authority source / mutation destination a body uses must be its own physical path in its canonical scope (canon,
# src_file, dst_file, dst_absent, dst_dir), never in the scientific clone; the controller and scientific roots are distinct and
# disjoint. v21 is the FUNDING ROUTE (owner ruling 26 Oct 2026: CSCI1913 first, then HEAL1922, side by side;
# chpc/candidate_v21_heal/DESIGN_v21.md): the programme gate and the admission change; no data file is added; the partition e3
# and its activation (made under v20) stay THE canonical activation under v21 (act3_valid, before and after the deploy).
set -u -o pipefail
umask 022
V21_PRELUDE=1
T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain   # @root
ME=pvanrooyen
die() { echo "ABORT: $*"; exit 1; }
T=$(cd -P -- "$T_ROOT" 2>/dev/null && pwd -P) || die "the toolchain root $T_ROOT is not reachable"
C=$T/rsc_screen_ctl/workspace_demo/t1_access     # the controller clone (the only clone the migration changes)
J=$T/rsc_screen/workspace_demo/t1_access         # the scientific job clone (read only, never changed)
GS=$T/row19_screen
G=$GS/gate; R=$GS/gate_retired; A=$T/archive_screen/v20_before_v21
EC2=$GS/ec2; ACT1=$EC2/activation_e1.json; ACT2=$EC2/activation_e2.json; ACT3=$EC2/activation_e3.json
LOCKS="$T/programme_admission.lock $GS/plans/.submit.lock"
# the adopted v20 state (controls v20 4e64982b with the operator record reviews/2026-10-23_controls_v20_operator_record.md; pilot
# qualification 2e99d615 with the operator records reviews/2026-10-23_pilot_v20_operator_record.md (max 100) and
# reviews/2026-10-26_pilot_v20_max200_operator_record.md (max 200, the ACTIVE review)) and the v21 candidate package
# (chpc/candidate_v21_heal, the funding route; owner ruling 26 Oct 2026, operator records)
V16_QUAL=2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44
V17_QUAL=8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa
V18_QUAL=530df9a208eb1578282ef564708447fd3b32c5fa1366f388f51059ebcfd70839
V19_QUAL=e123d6e5d136dfda31ac5f61dd18a2cce31ecc8dea9f1ad27be73d427cc50b02
V20_CONTROLS=4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c
V20_ADOPTION=1ef162deb000bdc8a423d2c74d606c5db481a92fa2484d8cef75944687232894
V19_ADOPTION=2b9f3c783e1f7ce53cbdafa4a84e66315874512d7afcde6b03783c343ba2939c
V20_QUAL=2e99d6159623b787568d538493f44f2ef5fc97ec0b340ae9e3c48672cca00959
V20_REC="reviews/2026-10-23_controls_v20_operator_record.md 70297db9390ab1b2b7e67866a2f20b38d142c60117b6e3866c7ccd618e29ed9d"
V20_PILOT_REC="reviews/2026-10-26_pilot_v20_max200_operator_record.md 34c2b22b62fd018fc92114a669e1807bc7ba39c63a85dcdc1223fcbbdef99a51"
V21_CONTROLS=72a5d2606c387433715befcc097e723c18bf4ba124ca5558878d550ea10ee8fb
E2_PART=48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6
E3_PART=ca87fb1da163df10e720e5778542d2bcc5c78f30fc08b6a1cc61d671773f0e6a
ACT3_SHA=fb3304d3c18949b06aa1ebccd90dc1171cb45ac1d96e4496afc2f11ffc3aacab
LEDGER_CAP=81000.0          # the refit ledger cap and committed budget phase before the v21 raise (raise_cap_v21.sh)
LEDGER_CAP_V21=181000.0     # after it
# the RETAINED captured node document of refit job 54 (capture script 84d52bdf, Codex choice 1 (a)): it stays where the owner
# wrote it and is still the evidence of job 54's node-failure disposition; every step checks it is still exactly these bytes, the
# archive keeps a copy and nothing ever rewrites it
NODE_EV=$T/jobs/row19_screen_refit_54.nodefail.json
NODE_EV_SHA=730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f
# the two controller files v21 replaces, at their v20 bytes (chpc/candidate_v21_heal/build_v21.py MAP)
V20_REPLACED="chpc/programme_gate.py 10a5340246190f57b2588ddf77057525ffcad0152128682cd6381830c4a839a0
chpc/row19_screen_admit.py 7c49bf86c6809941bc982393fb4ae095f7186e0c47665c426c27350a841b08af"
RETIRED_V19=$R/review_refit.v19_quale123d6e5_max100.json
RETIRED_V20=$R/review_refit.v20_qual2e99d615_max100.json
RETIRED_V20_200=$R/review_refit.v20_qual2e99d615_max200.json
# the job clone's fixed science inventory: every file must exist, read and hash, before and after any controller change
SCI="chpc/row19_screen_manifest.json analyze.py models.py simulate.py chpc/row19_shard.py chpc/row19_ledger.py chpc/row19_slice.py chpc/row19_screen_orig.py"
CTLPAT='row19_screen_(admit|status|verify)|row22_bank_(submit|status)|row19_ec2_|row19_partition|row19_ledger|programme_gate|row19_nodefail_capture'

CR=$T/rsc_screen_ctl                              # the canonical controller clone root (all controller mutations stay beneath it)
JR=$T/rsc_screen                                  # the canonical scientific job clone root (never a mutation destination)
PS=$T/archive_screen
PROOF=$PS/v21_deploy_proof                        # deploy_v21.sh's durable science before/after proof (written before any controller change)

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
# LENGAU TOOLS. Observed by the v16 live preflight, 17 Oct 2026 (CentOS 7.9): the installed git rejected `git -C` (1.8.3.1), the
# installed util-linux flock is 2.23.2, coreutils 8.22, system Python 3.6.8; $T/t1py was reported as Python 3.12.10 (Codex
# mig_compat review). This code uses only the interfaces those versions provide: every git call runs in a subshell that cds
# first (no -C, no --absolute-git-dir); flock is called with -n -s only and a conflict is its default exit 1 (no -E); every
# Lengau-side Python (lengau_archive.py, LOCK_PY, each t1py -c body) is 3.6-level code. preflight_v21.sh prints the versions.
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
for p in "$CR" "$C" "$JR" "$J" "$GS" "$G" "$R" "$GS/plans" "$EC2" "$ACT1" "$ACT2" "$ACT3" \
         "$PS" "$A" "$PROOF" "$T/jobs" "$NODE_EV" "$T/row19_screen_campaign" $LOCKS; do
  canon "$p" || die "$p is not its own physical path (it resolves to $(phys "$p" 2>/dev/null || echo 'an unsafe target'): a symlink or alias); refusing"
  case $p in "$T"/*) ;; *) die "$p is not beneath the toolchain root $T; refusing";; esac
done
# the controller and scientific roots are distinct and disjoint; no controller, gate, ec2 or archive root lies in the science clone
[ "$CR" != "$JR" ] || die "the controller and scientific clone roots are the same path"
case $CR/ in "$JR"/*) die "the controller clone root $CR lies inside the scientific clone $JR";; esac
case $JR/ in "$CR"/*) die "the scientific clone root $JR lies inside the controller clone $CR";; esac
if [ -e "$CR" ] && [ -e "$JR" ] && [ "$CR" -ef "$JR" ]; then die "the controller and scientific clone roots are the same directory"; fi
for p in "$C" "$G" "$R" "$EC2" "$A" "$PROOF" "$PS"; do not_science "$p" "fixed root"; done

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
    flock -n -s "$L" true; rc=$?          # the default -n conflict exit is 1 (`true` itself never exits 1); no -E is used
    case $rc in 0) return 0;; 1) die "lock held: $L";; esac
    echo "flock(1) probe of $L failed (exit $rc); trying the python fcntl probe"
  fi
  "$T/t1py" -c "$LOCK_PY" "$L"; rc=$?
  case $rc in 0) return 0;; 75) die "lock held: $L";; *) die "no reliable lock probe for $L (python fcntl probe exited $rc)";; esac
}
locks_free() { local L; for L in $LOCKS; do lock_free "$L"; done; }
# THE CONTROLLER CLONE'S PINNED UNTRACKED EVIDENCE (v16 live preflight 17 Oct 2026, carried unchanged): rsc_screen_ctl holds exactly
# these three UNTRACKED files, written 12 Oct 18:39 by the row-23 bench comparator / EC2 qualification permit. They are retained
# historical administrative evidence and are NOT authority for this migration's path (the legacy, terminal S route,
# chpc/row19_ec2_shadow.py, declares and reads the release-state copy; S stays terminal and its retry held - Codex allowlist
# review P3). They are never deleted, moved, ignored or committed by the migration; the Lengau archive keeps them as
# ctl/untracked/<path> (lengau_archive.py UNTRACKED_CTL, the same list). Paths are relative to $C; each must be its own physical
# path and a regular file with exactly its pinned sha256.
CTL_EVIDENCE="aws_ec2/ec2_release_state.json 80ba0ac599f617f8c0ee020d75e7c53dcd30c519d783a76dcb6a2f6b9f1a1d39
aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json 154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4
reviews/2026-10-11_d1d2_f3_codex_record.md 636f1e77089578a14ee837bf95fe0f86cc84dbc907f8ced918256b69dbb55c1e"
NL='
'
in_lines() { case "$NL$2$NL" in *"$NL$1$NL"*) return 0;; esac; return 1; }   # in_lines <line> <newline-separated list>
ctl_evidence_paths() { printf '%s\n' "$CTL_EVIDENCE" | awk '{print $1}'; }
not_evidence() {   # not_evidence <path relative to $C> <what>: a migration write/commit path is never a pinned evidence file
  in_lines "$1" "$(ctl_evidence_paths)" && die "$2: $1 is a pinned untracked evidence file of the controller clone; it is never written or committed"
  return 0
}
ctl_clean() {   # the controller clone is clean: no tracked modification, staged change or deletion, and every untracked entry
                # (--untracked-files=all) is one of the pinned evidence files, a regular file with its exact sha256; any other
                # untracked file, a hash mismatch, a symlink, an evidence path that is a directory, or an extra entry inside a
                # wholly untracked directory on the path to an evidence file refuses. A failed observation refuses. The
                # directory inventory is NUL-delimited and any name holding a newline refuses (Codex allowlist review P3).
  local pre st line p s f x bad="" allowed anc="" d tr e lst
  pre=${C#"$CR"/}; [ "$pre" != "$C" ] && clean_rel "$pre" || die "the controller work area $C is not beneath $CR"
  allowed=$(ctl_evidence_paths | sed "s|^|$pre/|") || die "cannot list the pinned controller evidence"
  st=$(cd -- "$CR" && git status --porcelain --untracked-files=all) || die "git status failed in $CR"
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    case $line in
      "?? "*) p=${line#"?? "}; in_lines "$p" "$allowed" || bad="$bad$line$NL";;
      *) bad="$bad$line$NL";;
    esac
  done <<<"$st"
  [ -z "$bad" ] || { printf '%s' "$bad" | head -5; die "$C has uncommitted changes or untracked files outside the pinned evidence allowlist (above)"; }
  while read -r p s; do
    [ -n "$p" ] || continue
    clean_rel "$p" && [ ${#s} = 64 ] || die "malformed pinned evidence entry $p"
    f=$C/$p
    if [ -e "$f" ] || [ -L "$f" ]; then
      src_file "$f" "$CR" "pinned untracked evidence $p"
      x=$(h "$f") || die "pinned untracked evidence $p: cannot hash $f"
      [ "$x" = "$s" ] || die "pinned untracked evidence $p is ${x:0:16}, not its pinned ${s:0:16}"
    fi
    d=${p%/*}; while [ "$d" != "$p" ] && [ -n "$d" ]; do in_lines "$pre/$d" "$anc" || anc="$anc$pre/$d$NL"; p=$d; d=${d%/*}; done
  done <<<"$CTL_EVIDENCE"
  lst=$(mktemp) || die "mktemp failed"
  while IFS= read -r d; do   # an ancestor directory holding NO tracked file: everything in it must be evidence or on its path
    [ -n "$d" ] || continue
    [ -e "$CR/$d" ] || [ -L "$CR/$d" ] || continue
    tr=$(cd -- "$CR" && git ls-files -- "$d") || { rm -f "$lst"; die "git ls-files failed in $CR"; }
    [ -z "$tr" ] || continue
    dst_dir "$CR/$d" "$CR" "untracked directory $d on the path to pinned evidence"
    (cd -- "$CR" && find "$d" -mindepth 1 -print0) > "$lst" || { rm -f "$lst"; die "cannot list the untracked directory $CR/$d"; }
    while IFS= read -r -d '' e; do
      case $e in *"$NL"*) rm -f "$lst"; die "the untracked directory $d holds an entry whose name contains a newline; refusing";; esac
      in_lines "$e" "$allowed" || in_lines "$e" "$anc" || { rm -f "$lst"; die "the untracked directory $d holds $e, which is neither pinned evidence nor on its path; refusing"; }
    done < "$lst"
  done <<<"$anc"
  rm -f "$lst"
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
adoption_is() {   # adoption_is <version> <controls sha> <previous adoption sha>: the deployed controls and adoption record name them
  src_file "$C/chpc/row19_screen_controls.json" "$CR" "deployed controls"; src_file "$C/chpc/row19_screen_controls_adoption.json" "$CR" "deployed adoption"
  pin "$C/chpc/row19_screen_controls.json" "$2" "deployed controls (v$1)"
  "$T/t1py" -c 'import json, sys
a = json.load(open(sys.argv[1]))
ok = a.get("version") == int(sys.argv[2]) and a.get("controls_sha256") == sys.argv[3] and (a.get("previous") or {}).get("adoption_sha256") == sys.argv[4]
sys.exit(0 if ok else 1)' "$C/chpc/row19_screen_controls_adoption.json" "$1" "$2" "$3"
}
v20_current() {   # the controller clone is the adopted, deployed v20 (before the v21 deploy): controls 4e64982b, adoption 1ef162de
  src_file "$C/chpc/row19_screen_controls_adoption.json" "$CR" "deployed adoption"
  pin "$C/chpc/row19_screen_controls_adoption.json" $V20_ADOPTION "deployed adoption (v20 record 1ef162de)"
  pin "$C/chpc/row19_screen_controls.json" $V20_CONTROLS "deployed controls (adopted v20)"
}
v21_adopted() {   # v21 is the deployed, ADOPTED controller in rsc_screen_ctl: the v21 controls and the version-21 adoption naming them
  adoption_is 21 $V21_CONTROLS $V20_ADOPTION || die "v21 is not the deployed, adopted controller in rsc_screen_ctl (deploy_v21.sh first)"
}
deploy_done() {   # the deployment's durable proof is complete (DONE) and its commit is in the controller's history
  local dh
  src_file "$PROOF/DONE" "$PS" "deploy proof DONE"
  grep -qx "schema row19-screen-v21-deploy-proof-1" "$PROOF/DONE" || die "the deploy proof DONE has another schema"
  dh=$(sed -n 's/^ctl_head_after \([0-9a-f]*\)$/\1/p' "$PROOF/DONE")
  [ ${#dh} = 40 ] || die "the deploy proof DONE names no controller commit"
  (cd -- "$C" && git merge-base --is-ancestor "$dh" HEAD) || die "the controller HEAD does not contain the proved v21 deployment commit ${dh:0:12}"
}
node_ev() {   # the retained captured node document of refit job 54 is exactly the reviewed bytes, a contained regular file
  src_file "$NODE_EV" "$T/jobs" "the captured node document of refit job 54"
  pin "$NODE_EV" $NODE_EV_SHA "the captured node document (730ea262)"
}
# epoch 3 (the EC2 close, made under the adopted v20) is THE canonical activation of e3 before AND after the v21 deploy: v21 pins
# the same e3, so row19_partition.activation_problem (mode canonical) accepts the proof under the CURRENT adopted controls either
# way (chpc/candidate_v21_heal/test_v21_heal.py F10 on the real proof copy). The e1/e2/e3 proofs are never changed.
ACT3_PY='import json, sys
sys.path.insert(0, "chpc")
import hashlib, row19_partition as RP
man_p, part_p, proof_p = sys.argv[1:4]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man = json.load(open(man_p)); part = RP.load(part_p, man, sha(man_p))
proof = json.load(open(proof_p))
why = RP.activation_problem(man, sha(man_p), part, sha(part_p), proof, mode="canonical")
cur = json.load(open("chpc/row19_screen_controls.json"))["versions"][-1]["version"]
extra = [] if (proof.get("epoch") == 3 and proof.get("closed") is True and proof.get("controls_version") == 20) else ["the proof is not the epoch-3 close made under version 20"]
print("activation proof %s: epoch %s closed %s, partition %s, made under controls version %s, accepted under the current version %s; activation_problem %r%s" % (
    sha(proof_p)[:16], proof.get("epoch"), proof.get("closed"), str(proof.get("partition_sha256"))[:12], proof.get("controls_version"), cur, why,
    ("; " + "; ".join(extra)) if extra else ""))
sys.exit(1 if (why or extra) else 0)'
act3_valid() {   # epoch 3 (the close) is THE canonical activation of e3 under the current adopted controls; e1/e2/e3 proofs unchanged
  src_file "$ACT1" "$GS" "epoch-1 activation proof"; src_file "$ACT2" "$GS" "epoch-2 activation proof"
  src_file "$ACT3" "$GS" "epoch-3 activation proof (the close)"; pin "$ACT3" $ACT3_SHA "the epoch-3 activation proof (fb3304d3)"
  src_file "$C/chpc/row19_partition_e3.json" "$CR" "the e3 partition"; pin "$C/chpc/row19_partition_e3.json" $E3_PART "the e3 partition (ca87fb1d)"
  (cd -- "$C" && "$T/t1py" -c "$ACT3_PY" chpc/row19_screen_manifest.json chpc/row19_partition_e3.json "$ACT3") \
    || die "the root's activation_e3.json is not the canonical epoch-3 activation under the current adopted controls (above)"
}
acts_kept() {   # after the v21 deploy: the e1/e2/e3 proofs are on the root byte-identical to the v20_before_v21 archive
  local a
  for a in activation_e1.json activation_e2.json activation_e3.json; do
    src_file "$EC2/$a" "$GS" "activation proof $a"; src_file "$A/ec2/$a" "$PS" "archived $a"
    cmp -s "$EC2/$a" "$A/ec2/$a" || die "$EC2/$a is not the archived v20_before_v21 copy: the activations are never changed"
  done
}
route_live() {   # route_live: the deployed gate resolves the v21 funding route on the REAL ledgers (read only, no lock taken)
  (cd -- "$C" && "$T/t1py" -c 'import json, sys; sys.path.insert(0, "chpc"); import programme_gate as PG
m = json.load(open("chpc/row19_screen_manifest.json")); f = PG.programme_funding(m)
r = PG.route_of(f); tot, det = PG.committed_by_programme(f); pr, why = PG.route_choice(f, [720.0])
print("funding route %s; committed %s; a 720 core-h job now goes to %s" % (" -> ".join("%s %.0f" % (x["programme"], x["allocation_core_h"]) for x in r),
      ", ".join("%s %.1f" % (k, v) for k, v in tot.items()), pr[0] if pr else "NO programme (%s)" % why))
sys.exit(0 if [x["programme"] for x in r] == ["CSCI1913", "HEAL1922"] and not why else 1)') || die "the deployed funding route does not resolve (above)"
}
literal_in() {   # literal_in <file> <literal>: an exact line (outer whitespace trimmed). NO `grep -q` in a pipe: under pipefail an
                 # early-exiting grep -q SIGPIPEs sed on a record above its buffer and the check fails although the line is there
                 # (migration_v17 adopt_pilot17.sh fix 9df2a1f); grep reads all of its input and its output is discarded
  sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$1" | grep -xF -- "$2" >/dev/null
}

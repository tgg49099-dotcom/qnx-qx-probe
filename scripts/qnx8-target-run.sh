#!/usr/bin/env bash
# qnx8-target-run.sh - run the binaries built by qcc ON a QNX 8.0 target.
#
# WHAT IT DOES
#
#   A binary that qcc built is not yet a program that runs on QNX 8.0.  This
#   script copies the three examples to a running QNX 8.0 target (the QEMU
#   image of the SDP, or a board), starts each one, and checks that the
#   resource manager really attached its path in the QNX pathname space.
#
#   It follows the official QNX procedure, and nothing else:
#     - the QEMU image is created by the SDP package
#       com.qnx.qnx800.quickstart.qemu and started with "mkqnximage --run"
#       (headless: "mkqnximage --run=-h"), in its folder, typically
#       ~/qnx800/images/qemu/qemu;
#     - its address is given by "mkqnximage --getip", which "waits for the
#       system image to be up and running before it returns a value";
#     - files go over scp, commands over ssh ("You can use scp and sftp to
#       transfer files to and from the virtual machine").
#   Source: QNX SDP 8.0 utilities reference, mkqnximage; QNX Everywhere,
#   "QSTI for QEMU - Getting started" (page updated 24 September 2026).
#
# WHAT IT NEVER DOES
#
#   It never types a password: the target must accept the ssh key given in
#   QNX_SSH_KEY (an image built with "mkqnximage --ssh-ident=KEY.pub" lets
#   root log in with that key).  It never starts the virtual machine itself
#   (that needs the QEMU bridge set up with sudo, once, by a human).  When
#   something is missing it says NOT MEASURED, and simulates nothing.
#
# USAGE
#
#   bash scripts/qnx8-target-run.sh --arch x86_64 --out DIR
#
#   QNX_QEMU_DIR   folder of the mkqnximage image (default:
#                  ~/qnx800/images/qemu/qemu when it exists)
#   QNX_TARGET_IP  address of the target, instead of "mkqnximage --getip"
#                  (a board, or a VM started elsewhere)
#   QNX_SSH_KEY    private ssh key accepted by the target for root
#   QNX_TARGET_USER  user on the target (default: root; attaching a path
#                  in the pathname space needs root)
#   QNX_TARGET_PORT  TCP port of ssh on the target (default: 22; a QEMU
#                  started with a forwarded port uses another one)
#
#   --stable         print ONLY the lines that are the same on every run of
#                  a QNX 8.0 x86_64 target (the name of the CPU and the
#                  release, and the three "RAN ON QNX 8.0" lines).  The
#                  lines that depend on the machine (the address, the free
#                  memory, the boot time) then go to the log files only.
#                  This mode is what the picture of the proof shows: a
#                  picture can be compared with the output of the command,
#                  and it can only be compared when the output does not
#                  change from one run to the next.
#
# EXIT CODES
#
#   0  every example ran on QNX 8.0 and attached its path
#   1  the target answered, and something FAILED (wrong OS or version,
#      wrong architecture, copy refused, path not attached)
#   3  NOT MEASURED: no target, no address or no key; nothing was simulated
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 3
ARCH="x86_64"
OUT=""
STABLE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --arch) ARCH="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --stable) STABLE=1; shift ;;
    *) echo "unknown option: $1"; exit 3 ;;
  esac
done
case "$ARCH" in
  x86_64)  UNAME_M="x86_64" ;;
  aarch64) UNAME_M="aarch64le" ;;
  *) echo "unknown target: $ARCH"; exit 3 ;;
esac
[ -n "$OUT" ] || OUT=$(mktemp -d)
mkdir -p "$OUT" || exit 3

# example binary -> the path its resmgr_attach() call registers
EXAMPLES="qxprobe-demo:/dev/qxprobe-demo qxprobe-status:/var/run/qxprobe-status qxprobe-official:/dev/qxprobe-official"

# In the stable mode, the lines that change from one run to the next (the
# address of the target, the free memory, the boot time) are written to the
# log files only: what is printed on the screen is what is measured, and it
# is the same on every run.
note() { printf '%s\n' "$*" >> "$OUT/05-run-cible.txt"; }
say() {           # a line that describes the machine: it goes to the log
  note "$@"
  [ "$STABLE" -eq 1 ] || echo "$@"
}
not_measured() {
  {
    echo "NOT MEASURED: the run on a QNX 8.0 target is NOT MEASURED."
    echo "Reason: $1"
    echo "Nothing was simulated."
  } | tee "$OUT/05-run-cible.txt"
  exit 3
}

# ---- 1. the address of the target ------------------------------------------
QEMU_DIR="${QNX_QEMU_DIR:-}"
if [ -z "$QEMU_DIR" ] && [ -d "$HOME/qnx800/images/qemu/qemu" ]; then
  QEMU_DIR="$HOME/qnx800/images/qemu/qemu"
fi
IP="${QNX_TARGET_IP:-}"
if [ -z "$IP" ]; then
  if ! command -v mkqnximage >/dev/null 2>&1; then
    not_measured "mkqnximage is absent (the SDP 8.0 environment is not loaded) and QNX_TARGET_IP is not set."
  fi
  if [ -z "$QEMU_DIR" ] || [ ! -d "$QEMU_DIR" ]; then
    not_measured "no QEMU image folder (set QNX_QEMU_DIR, or unpack com.qnx.qnx800.quickstart.qemu into ~/qnx800/images/qemu/qemu)."
  fi
  say "target     : the QEMU image in $QEMU_DIR (mkqnximage --getip, 120 s at most)"
  IP=$(cd "$QEMU_DIR" && timeout 120 mkqnximage --getip 2>/dev/null \
       | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' | tail -1)
  [ -n "$IP" ] || not_measured "mkqnximage --getip gave no address in 120 s: the VM is not running (start it in $QEMU_DIR with: mkqnximage --run=-h)."
fi
say "address    : $IP"

# ---- 2. the key ---------------------------------------------------------------
KEY="${QNX_SSH_KEY:-}"
if [ -z "$KEY" ] || [ ! -f "$KEY" ]; then
  not_measured "QNX_SSH_KEY is not set or is not a file: this script never types a password (build the image with mkqnximage --ssh-ident=KEY.pub)."
fi
USER_T="${QNX_TARGET_USER:-root}"
PORT="${QNX_TARGET_PORT:-22}"
SSH_OPTS="-i $KEY -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 -o LogLevel=ERROR"
t_ssh() { # shellcheck disable=SC2086
  ssh -p "$PORT" $SSH_OPTS "$USER_T@$IP" "$@"; }
# scp is told which ssh program to use (-S): some installations of scp look
# for it in a fixed place (/usr/bin/ssh) and not in the PATH.  Note that the
# port option of scp is "-P", the one of ssh is "-p".
SSH_BIN=$(command -v ssh 2>/dev/null || true)
SCP_OPTS="-q -P $PORT"
[ -n "$SSH_BIN" ] && SCP_OPTS="$SCP_OPTS -S $SSH_BIN"
t_scp() { # shellcheck disable=SC2086
  scp $SCP_OPTS $SSH_OPTS "$@"; }

# ---- 3. is it QNX 8.0, on the right architecture? -------------------------------
UNAME=$(t_ssh uname -s -r -m 2>&1)
rc=$?
echo "uname      : $UNAME" >> "$OUT/05-run-uname.txt"
say "uname      : $UNAME"
if [ "$rc" -ne 0 ]; then
  # The target did not answer: this is an absence, not a failure.  Nothing
  # is simulated, and the exit code says so (3 = NOT MEASURED).
  echo "NOT MEASURED: the target $USER_T@$IP did not answer (ssh RC $rc)." \
    | tee -a "$OUT/05-run-uname.txt"
  echo "Nothing was simulated." | tee -a "$OUT/05-run-uname.txt"
  exit 3
fi
# The architecture of the target is read with "pidin info", the official QNX
# tool: it prints "CPU:X86_64 Release:8.0.0 ...".  It is preferred to
# "uname -m" because QNX 8.0 reports "x86pc" for the 64-bit x86 target (the
# historical QNX machine name), which is not the architecture of the
# binaries: only pidin names the CPU as the binaries are built for it.
PIDIN=$(t_ssh pidin info 2>&1)
rc_pidin=$?
echo "pidin info : $PIDIN" >> "$OUT/05-run-uname.txt"
say "pidin info : $PIDIN"
set -- $UNAME
if [ "${1:-}" != "QNX" ] || [ "${2%%.*}" != "8" ]; then
  echo "FAILED: the target is not QNX 8.x (uname: $UNAME)." | tee -a "$OUT/05-run-uname.txt"
  exit 1
fi
CPU=""
if [ "$rc_pidin" -eq 0 ]; then
  case "$PIDIN" in
    *CPU:X86_64*)  CPU="x86_64" ;;
    *CPU:AARCH64*) CPU="aarch64" ;;
  esac
fi
if [ -z "$CPU" ]; then
  echo "NOTE: 'pidin info' did not name the CPU; the check falls back on uname -m (${3:-?})." | tee -a "$OUT/05-run-uname.txt"
  CPU="${3:-?}"
fi
# The stable line of the proof: the name of the CPU and the release, read
# with the official tool.  "CPU:X86_64 Release:8.0.0" is the same on every
# QNX 8.0 x86_64 target; the free memory and the boot time that follow it
# in the same line of "pidin info" are not.
CPU_LINE=$(printf '%s\n' "$PIDIN" \
  | grep -oE 'CPU:[A-Za-z0-9_]+ Release:[0-9][0-9.]*' | head -1)
if [ -z "$CPU_LINE" ]; then
  if [ "$STABLE" -eq 1 ]; then
    echo "FAILED: 'pidin info' did not name the CPU: the stable output cannot be produced." \
      | tee -a "$OUT/05-run-uname.txt"
    exit 1
  fi
  CPU_LINE="CPU:unknown"
fi
# "aarch64le" and "aarch64" are the same CPU; the endianness is not the
# question here.
case "$CPU" in *le) CPU_NORM="${CPU%le}" ;; *) CPU_NORM="$CPU" ;; esac
case "$UNAME_M" in *le) ARCH_NORM="${UNAME_M%le}" ;; *) ARCH_NORM="$UNAME_M" ;; esac
if [ "$CPU_NORM" != "$ARCH_NORM" ]; then
  echo "FAILED: the target is $CPU, the binaries are $ARCH ($UNAME_M)." | tee -a "$OUT/05-run-uname.txt"
  exit 1
fi
echo "QNX 8.0 TARGET: $CPU_LINE"

# ---- 4. copy, start, check the path, stop ------------------------------------------
fails=0
t_ssh mkdir -p /tmp/qxprobe >/dev/null 2>&1
for pair in $EXAMPLES; do
  b=${pair%%:*}; p=${pair#*:}
  f="$ROOT/build/$ARCH/$b"
  log="$OUT/05-run-$b.txt"
  if [ ! -f "$f" ]; then
    echo "FAILED $b: $f was not built" | tee "$log"; fails=$((fails+1)); continue
  fi
  # A resource manager of a PREVIOUS run may still be alive on the target.
  # It would hold the path, and the check below would then be a false
  # positive: the path would be there because of the old process, not
  # because of this one.  The old process is killed first, with the
  # official tool "slay", and the path must be free before the new one
  # starts.  (A path disappears from the QNX pathname space when the
  # process that attached it dies.)
  t_ssh "slay $b" >/dev/null 2>&1
  sleep 1
  STALE=$(t_ssh "ls -l $p" 2>/dev/null)
  if [ -n "$STALE" ]; then
    echo "FAILED $b: the path $p is still attached on the target: a resource manager of a previous run is still alive, and the check would be a false positive." \
      | tee "$log"
    fails=$((fails+1)); continue
  fi
  # The copy of a previous run is removed before the new one is sent: a file
  # that is being executed cannot be overwritten on QNX (the copy fails
  # with "dest open: Failure").
  t_ssh "rm -f /tmp/qxprobe/$b" >/dev/null 2>&1
  if ! t_scp "$f" "$USER_T@$IP:/tmp/qxprobe/$b" > "$log" 2>&1; then
    echo "FAILED $b: scp refused" | tee -a "$log"; fails=$((fails+1)); continue
  fi
  t_ssh "cd /tmp/qxprobe && chmod 755 ./$b && (./$b </dev/null >./$b.log 2>&1 & echo \$! > ./$b.pid); sleep 2; if ls -l $p; then echo PATH-ATTACHED $p; else echo PATH-ABSENT $p; fi; kill \$(cat ./$b.pid) 2>/dev/null; sleep 1; kill -9 \$(cat ./$b.pid) 2>/dev/null; cat ./$b.log; rm -f ./$b.pid ./$b.log ./$b" >> "$log" 2>&1
  if grep -q "^PATH-ATTACHED $p" "$log"; then
    echo "RAN ON QNX 8.0  $b : $p attached ($UNAME)"
  else
    echo "FAILED          $b : $p not attached (see $log)"
    fails=$((fails+1))
  fi
done
[ "$fails" -eq 0 ] && exit 0
exit 1

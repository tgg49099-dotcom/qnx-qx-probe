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
while [ $# -gt 0 ]; do
  case "$1" in
    --arch) ARCH="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
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

not_measured() {
  {
    echo "NOT MEASURED: the binaries were built but not run on QNX 8.0."
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
  echo "target     : the QEMU image in $QEMU_DIR (mkqnximage --getip, 240 s at most)"
  IP=$(cd "$QEMU_DIR" && timeout 240 mkqnximage --getip 2>/dev/null \
       | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' | tail -1)
  [ -n "$IP" ] || not_measured "mkqnximage --getip gave no address in 240 s: the VM is not running (start it in $QEMU_DIR with: mkqnximage --run=-h)."
fi
echo "address    : $IP"

# ---- 2. the key ---------------------------------------------------------------
KEY="${QNX_SSH_KEY:-}"
if [ -z "$KEY" ] || [ ! -f "$KEY" ]; then
  not_measured "QNX_SSH_KEY is not set or is not a file: this script never types a password (build the image with mkqnximage --ssh-ident=KEY.pub)."
fi
USER_T="${QNX_TARGET_USER:-root}"
SSH_OPTS="-i $KEY -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 -o LogLevel=ERROR"
t_ssh() { # shellcheck disable=SC2086
  ssh $SSH_OPTS "$USER_T@$IP" "$@"; }
t_scp() { # shellcheck disable=SC2086
  scp -q $SSH_OPTS "$@"; }

# ---- 3. is it QNX 8.0, on the right architecture? -------------------------------
UNAME=$(t_ssh uname -s -r -m 2>&1)
rc=$?
echo "uname      : $UNAME" | tee "$OUT/05-run-uname.txt"
if [ "$rc" -ne 0 ]; then
  echo "FAILED: ssh to $USER_T@$IP refused (RC $rc)." | tee -a "$OUT/05-run-uname.txt"
  exit 1
fi
set -- $UNAME
if [ "${1:-}" != "QNX" ] || [ "${2%%.*}" != "8" ]; then
  echo "FAILED: the target is not QNX 8.x (uname: $UNAME)." | tee -a "$OUT/05-run-uname.txt"
  exit 1
fi
if [ "${3:-}" != "$UNAME_M" ]; then
  echo "FAILED: the target is ${3:-?}, the binaries are $ARCH ($UNAME_M)." | tee -a "$OUT/05-run-uname.txt"
  exit 1
fi

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
  if ! t_scp "$f" "$USER_T@$IP:/tmp/qxprobe/$b" > "$log" 2>&1; then
    echo "FAILED $b: scp refused" | tee -a "$log"; fails=$((fails+1)); continue
  fi
  t_ssh "cd /tmp/qxprobe && chmod 755 ./$b && (./$b </dev/null >./$b.log 2>&1 & echo \$! > ./$b.pid); sleep 2; if ls -l $p; then echo PATH-ATTACHED $p; else echo PATH-ABSENT $p; fi; kill \$(cat ./$b.pid) 2>/dev/null; cat ./$b.log; rm -f ./$b.pid ./$b.log" >> "$log" 2>&1
  if grep -q "^PATH-ATTACHED $p" "$log"; then
    echo "RAN ON QNX 8.0  $b : $p attached ($UNAME)"
  else
    echo "FAILED          $b : $p not attached (see $log)"
    fails=$((fails+1))
  fi
done
[ "$fails" -eq 0 ] && exit 0
exit 1

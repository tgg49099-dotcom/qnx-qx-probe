#!/usr/bin/env bash
# Compiles the QX-PROBE examples for QNX 8.0 with qcc (SDP 8.0).
#
# This script CANNOT run yet: it requires the SDP 8.0 (non-commercial QNX
# Everywhere licence, myQNX account).  It is written and ready to run the day
# the licence exists.
#
# Absolute rule: if qcc is missing, the script stops with an error and invents
# NO compiler output.  It does not produce a fake binary.
#
# Usage:  bash scripts/build_qcc.sh [target]
#   target = x86_64 (default) | aarch64 | armv7
set -u
cd "$(dirname "$0")/.." || exit 2

TARGET="${1:-x86_64}"
OUT="build"

case "$TARGET" in
  x86_64) QCC_TARGET="x86_64" ;;
  aarch64) QCC_TARGET="aarch64" ;;
  armv7)  QCC_TARGET="armv7" ;;
  *) echo "Unknown target: $TARGET (expected: x86_64, aarch64, armv7)"; exit 2 ;;
esac

# --- Is the SDK present? ---------------------------------------------------
if ! command -v qcc >/dev/null 2>&1; then
  cat >&2 <<EOF
ERROR: qcc was not found.

This script compiles for QNX 8.0 with the SDP 8.0 (host tools).  Without the
SDP 8.0 and a non-commercial QNX Everywhere licence (myQNX account), the
compilation is impossible.

What is missing, and what this script cannot simulate:
  - qcc (the QNX C compiler, shipped with the SDP 8.0)
  - the QNX 8.0 system libraries (libc, libsys, ...)

No compiler output is simulated: without qcc, this script stops here, with
exit code 2.
EOF
  exit 2
fi

echo "qcc: $(command -v qcc)"
qcc -V 2>&1 | head -3
echo

mkdir -p "$OUT"
rc_global=0

build_one() {
  src="$1"; name="$2"
  echo "--- $src -> $OUT/$name ---"
  # -V: native QNX libraries; -Werror: no warning tolerated.
  qcc -Vgcc_ntoaosdebug -Werror -o "$OUT/$name" "$src"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "COMPILATION FAILED: $src (RC $rc)"
    rc_global=1
  else
    echo "OK: $OUT/$name ($(wc -c < "$OUT/$name") bytes)"
  fi
  echo
}

build_one examples/qnx80_resmgr_minimal.c qxprobe-demo
build_one examples/qnx80_resmgr_readonly.c qxprobe-status
build_one examples/qnx80_resmgr_official_example.c qxprobe-official

if [ "$rc_global" -eq 0 ]; then
  echo "BUILD OK for target $QCC_TARGET"
else
  echo "BUILD KO"
fi
exit "$rc_global"

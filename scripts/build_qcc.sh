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
#   target = x86_64 (default) | aarch64
#
# The qcc variant names the target: gcc_ntox86_64 or gcc_ntoaarch64le (QNX
# 8.0 is a 64-bit OS: x86_64 and AArch64 little-endian).  The previous
# version passed "-Vgcc_ntoaosdebug", which is not a qcc variant, and
# ignored the target argument: it would have failed on the first real run.
# Before compiling, the script asks qcc which variants are installed
# (qcc -V) and stops with the list if the requested one is missing.
set -u
cd "$(dirname "$0")/.." || exit 2

TARGET="${1:-x86_64}"
case "$TARGET" in
  x86_64)  QCC_TARGET="x86_64";  VARIANT="gcc_ntox86_64" ;;
  aarch64) QCC_TARGET="aarch64"; VARIANT="gcc_ntoaarch64le" ;;
  *) echo "Unknown target: $TARGET (expected: x86_64 or aarch64 — QNX 8.0 is 64-bit only)"; exit 2 ;;
esac
OUT="build/$QCC_TARGET"

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
VARIANTS=$(qcc -V 2>&1)
echo "$VARIANTS" | head -12
echo
if ! printf '%s\n' "$VARIANTS" | grep -q "$VARIANT"; then
  echo "ERROR: the qcc variant $VARIANT is not installed (see the list above)."
  exit 2
fi

mkdir -p "$OUT"
rc_global=0

build_one() {
  src="$1"; name="$2"
  echo "--- $src -> $OUT/$name ---"
  # -V: native QNX libraries; -Werror: no warning tolerated.
  qcc -V"$VARIANT" -Werror -o "$OUT/$name" "$src"
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
  echo "BUILD OK for target $QCC_TARGET (qcc -V$VARIANT)"
else
  echo "BUILD KO"
fi
exit "$rc_global"

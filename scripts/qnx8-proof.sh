#!/usr/bin/env bash
# qnx8-proof.sh — the QNX 8.0 demonstration of this repository, in ONE command.
#
# WHAT THIS SCRIPT ANSWERS
#
#   The contest rules ask for a project that "genuinely builds for or runs on
#   QNX 8.0".  This script answers that question with a measurement, not with
#   a sentence: it builds the C examples with the QNX compiler when the QNX
#   SDP 8.0 is installed, and when it is not, it says exactly what is missing
#   and stops.
#
# TWO PATHS, AND ONLY TWO
#
#   1. THE SDP 8.0 IS ABSENT — the case on 17 November 2026.
#      The script detects the absence (no `qcc`, no SDP directory), writes
#      nothing at all, and exits with the code 2.  It NEVER simulates a
#      compilation, a compiler message, a binary or a run.  This failure is
#      the counter-proof: a script that cannot fail proves nothing.
#
#   2. THE SDP 8.0 IS PRESENT — the day the free non-commercial licence
#      arrives.  The script compiles the three C examples with
#      `qcc -Vgcc_ntox86_64`, runs QX-PROBE on them, and writes the real
#      output (stdout, stderr, exit codes, checksums) under `proofs/`.
#
# USAGE
#
#   bash scripts/qnx8-proof.sh                     # the demonstration
#   bash scripts/qnx8-proof.sh --target aarch64    # the other QNX 8.0 target
#   bash scripts/qnx8-proof.sh --out /tmp/proofs   # where the proofs are written
#   bash scripts/qnx8-proof.sh --self-test         # the SDP path with a FAKE
#                                                  # compiler: it proves that
#                                                  # the command sequence is
#                                                  # right, and nothing else
#
# EXIT CODES
#
#   0  the demonstration ran (path 2), or the self-test passed
#   1  the demonstration ran and something really FAILED (a compilation error)
#   2  the SDP 8.0 is absent (or is incomplete): nothing was measured, and
#      nothing was simulated
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 2
cd "$ROOT" || exit 2

TARGET="x86_64"
OUT="$ROOT/proofs/qnx8"
SELF_TEST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --target=*) TARGET="${1#--target=}"; shift ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --out=*) OUT="${1#--out=}"; shift ;;
    --self-test) SELF_TEST=1; shift ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (see the header of this script)"; exit 2 ;;
  esac
done

case "$TARGET" in
  x86_64)  VARIANT="gcc_ntox86_64" ;;
  aarch64) VARIANT="gcc_ntoaarch64le" ;;
  *) echo "unknown target: $TARGET (QNX 8.0 is 64-bit only: x86_64 or aarch64)"; exit 2 ;;
esac

# --------------------------------------------------------------------------
# The self-test: a FAKE qcc, in a temporary directory, that records the
# commands it receives and writes a text file where a binary would be.  It
# compiles nothing.  Its only purpose is to check that the SDP path issues
# the right commands, in the right order, and writes the right files.
# --------------------------------------------------------------------------
if [ "$SELF_TEST" -eq 1 ]; then
  TMP=$(mktemp -d) || exit 2
  trap 'rm -rf "$TMP"' 0
  mkdir -p "$TMP/bin" "$TMP/sdp"
  cat > "$TMP/bin/qcc" <<'FAKEQCC'
#!/usr/bin/env bash
# A FAKE qcc.  Used only by "qnx8-proof.sh --self-test".  It compiles
# NOTHING: it records the command line and writes a text file.
echo "qcc $*" >> "$FAKE_QCC_LOG"
if [ "${1:-}" = "-V" ]; then
  echo "gcc_ntox86_64"
  echo "gcc_ntoaarch64le"
  exit 0
fi
out=""; src=""; next=""
for a in "$@"; do
  case "$a" in
    -o) next="out" ;;
    -*) ;;
    *) if [ "$next" = "out" ]; then out="$a"; next=""; else src="$a"; fi ;;
  esac
done
printf 'FAKE BINARY - produced by a fake qcc, NOT a QNX compilation\n' > "$out"
exit 0
FAKEQCC
  chmod +x "$TMP/bin/qcc"
  echo "======================================================================"
  echo "SELF-TEST - A FAKE COMPILER, NOT A QNX 8.0 COMPILATION"
  echo "======================================================================"
  echo "This run proves that the SDP path issues the right commands, in the"
  echo "right order, and writes the right files.  It proves NOTHING about QNX"
  echo "8.0 itself: the compiler here is a shell script that writes a text"
  echo "file.  Every file it produces says so, in its first line."
  echo
  export FAKE_QCC_LOG="$TMP/qcc.log"
  : > "$FAKE_QCC_LOG"
  PATH="$TMP/bin:$PATH" QNX_SDP="$TMP/sdp" SELF_TEST_OUT="$TMP/out" \
    QX_PROOF_FAKE_COMPILER=1 \
    bash "$ROOT/scripts/qnx8-proof.sh" --out "$TMP/out" --target "$TARGET"
  rc=$?
  echo
  echo "---- the commands the fake qcc received ----"
  cat "$FAKE_QCC_LOG"
  echo "---- end ----"
  # The fake binaries are removed: a file that says "FAKE BINARY" must never
  # stay in the tree, where someone could mistake it for a QNX build.
  echo
  echo "---- the fake binaries are removed ----"
  for f in "$ROOT"/build/*/*; do
    [ -f "$f" ] || continue
    if grep -q 'FAKE BINARY' "$f" 2>/dev/null; then
      echo "removed $f"
      rm -f "$f"
    fi
  done
  rc2=0
  if ! grep -q -- "-V$VARIANT -Werror -o " "$FAKE_QCC_LOG"; then
    echo "SELF-TEST FAILED: the flag -V$VARIANT -Werror -o was never used."
    rc2=1
  fi
  if [ "$(grep -c 'qcc -V' "$FAKE_QCC_LOG")" -lt 4 ]; then
    echo "SELF-TEST FAILED: the three examples and the variant list were not compiled."
    rc2=1
  fi
  if [ "$rc" -ne 0 ]; then
    echo "SELF-TEST FAILED: the SDP path returned $rc."
    rc2=1
  fi
  if [ "$rc2" -eq 0 ]; then
    echo "SELF-TEST OK: the SDP path is ready for the day the licence arrives."
  fi
  exit "$rc2"
fi

# --------------------------------------------------------------------------
# PATH 1 - the SDP 8.0 is absent: say what is missing, write nothing, fail.
# --------------------------------------------------------------------------
echo "======================================================================"
echo "QX-PROBE - the QNX 8.0 proof"
echo "======================================================================"
echo "date       : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "repository : $ROOT"
echo "target     : $TARGET (qcc variant $VARIANT)"
echo
if [ "${QX_PROOF_FAKE_COMPILER:-}" = "1" ]; then
  echo "*** SELF-TEST RUN: the compiler used here is a FAKE qcc. ***"
  echo "*** NOTHING BELOW IS A QNX 8.0 COMPILATION. ***"
  echo
fi

SDP_CANDIDATES="${QNX_SDP:-} ${QNX_HOST:-} /opt/qnx800"
QCC_PATH=$(command -v qcc 2>/dev/null || true)
SDP_FOUND=""
for d in $SDP_CANDIDATES; do
  [ -d "$d" ] && SDP_FOUND="$d" && break
done

if [ -z "$QCC_PATH" ] || [ -z "$SDP_FOUND" ]; then
  echo "ERROR: the QNX SDP 8.0 is not installed on this machine."
  echo
  echo "Checked, and absent:"
  [ -z "$QCC_PATH" ] && echo "  - the QNX C compiler 'qcc'          (command -v qcc)"
  [ -z "$SDP_FOUND" ] && echo "  - an SDP 8.0 directory             (checked: ${SDP_CANDIDATES})"
  echo
  echo "What this script needs, and cannot simulate:"
  echo "  - qcc, the QNX C compiler of the SDP 8.0"
  echo "  - the QNX 8.0 system libraries and headers (libc, libsys, ...)"
  echo "  - a non-commercial QNX Everywhere licence (a myQNX account)"
  echo
  echo "No compilation is simulated: without qcc, this script stops here, with"
  echo "exit code 2.  Nothing was written, nothing was built, no compiler"
  echo "output was invented."
  exit 2
fi

echo "qcc        : $QCC_PATH"
echo "sdp        : $SDP_FOUND"
echo

# --------------------------------------------------------------------------
# PATH 2 - the SDP 8.0 is present: compile, lint, record the real output.
# --------------------------------------------------------------------------
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
DIR="$OUT/$TARGET-$STAMP"
mkdir -p "$DIR" || exit 2

echo "---- 1/4  the qcc variants installed ----"
"$QCC_PATH" -V > "$DIR/01-qcc-variants.txt" 2>&1
rc=$?
head -12 "$DIR/01-qcc-variants.txt"
if ! grep -q "$VARIANT" "$DIR/01-qcc-variants.txt"; then
  echo
  echo "ERROR: the qcc variant $VARIANT is not installed (see the list above)."
  echo "Nothing was compiled."
  exit 2
fi

echo
echo "---- 2/4  the compilation of the three C examples ----"
bash "$ROOT/scripts/build_qcc.sh" "$TARGET" > "$DIR/02-build-qcc.txt" 2>&1
rc_build=$?
cat "$DIR/02-build-qcc.txt"
echo "exit code of the build: $rc_build"

echo
echo "---- 3/4  QX-PROBE on the QNX 8.0 examples ----"
python3 -I "$ROOT/qx_probe.py" \
  "$ROOT/examples/qnx80_resmgr_minimal.c" \
  "$ROOT/examples/qnx80_resmgr_readonly.c" \
  "$ROOT/examples/qnx80_resmgr_official_example.c" \
  > "$DIR/03-linter-exemples.txt" 2>&1
rc_lint=$?
cat "$DIR/03-linter-exemples.txt"
echo "exit code of the linter: $rc_lint"

echo
echo "---- 4/4  the checksums of what was built ----"
{
  echo "# sha256 of the binaries built by qcc -V$VARIANT"
  sha256sum "$ROOT"/build/"$TARGET"/* 2>/dev/null
} > "$DIR/04-sha256-binaires.txt" 2>&1
cat "$DIR/04-sha256-binaires.txt"

# The binaries are built for QNX 8.0: running them needs a QNX 8.0 target
# (a QEMU image or a board).  When there is none, this is said and nothing is
# invented.
echo
echo "---- the QNX 8.0 target ----"
if [ -n "${QNX_QEMU_IMAGE:-}" ] && [ -f "${QNX_QEMU_IMAGE}" ] && \
   command -v qemu-system-x86_64 >/dev/null 2>&1; then
  for b in "$ROOT"/build/*/*; do
    [ -f "$b" ] || continue
    echo "running $b on the QNX 8.0 image $QNX_QEMU_IMAGE"
    qemu-system-x86_64 -kernel "$QNX_QEMU_IMAGE" -append "$(basename "$b")" \
      -serial stdio -no-reboot -display none \
      > "$DIR/05-run-$(basename "$b").txt" 2>&1
    echo "exit code: $?"
  done
else
  {
    echo "NOT MEASURED: the binaries were built but not run."
    echo "Running a QNX 8.0 binary needs a QNX 8.0 target (a QEMU image or a"
    echo "board).  None is available on this machine: QNX_QEMU_IMAGE is not"
    echo "set, or qemu-system-x86_64 is absent.  Nothing was simulated."
  } > "$DIR/05-run-cible.txt"
  cat "$DIR/05-run-cible.txt"
fi

{
  echo "QX-PROBE - QNX 8.0 proof"
  echo "date            : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "qcc             : $QCC_PATH"
  echo "sdp             : $SDP_FOUND"
  echo "target          : $TARGET"
  echo "qcc variant     : $VARIANT"
  echo "build exit code : $rc_build"
  echo "linter exit code: $rc_lint"
  echo "files           : $DIR"
} > "$DIR/SUMMARY.txt"

echo
echo "======================================================================"
if [ "$rc_build" -eq 0 ] && [ "$rc_lint" -eq 0 ]; then
  if [ "${QX_PROOF_FAKE_COMPILER:-}" = "1" ]; then
    echo "VERDICT (SELF-TEST, FAKE COMPILER): the SDP path issues the right commands"
    echo "         and the linter runs on them.  THIS IS NOT A QNX 8.0 COMPILATION."
    echo "         the output is in $DIR"
    exit 0
  fi
  echo "VERDICT: THE EXAMPLES BUILD FOR QNX 8.0 ($VARIANT) AND THE LINTER RUNS ON THEM"
  echo "         the real output is in $DIR"
  exit 0
fi
echo "VERDICT: FAILED - the build returned $rc_build, the linter returned $rc_lint"
echo "         the real output is in $DIR"
exit 1

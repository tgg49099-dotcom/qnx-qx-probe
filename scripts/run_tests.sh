#!/usr/bin/env bash
# Runs the QX-PROBE test suite (host side, no QNX SDK required).
# Exit code: 0 = every test passes, non-zero = failure.
set -u
cd "$(dirname "$0")/.." || exit 2
# Never leave Python artefacts (__pycache__) in the repository.
# -B (and not PYTHONDONTWRITEBYTECODE) because -I ignores the PYTHON* variables.

echo "=============================================================="
echo "QX-PROBE — test suite"
echo "=============================================================="
echo
echo "--- 1. the reference code published by BlackBerry must pass with no error and no warning ---"
for f in examples/blackberry_eventfd_mgr.c examples/qnx80_resmgr_minimal.c \
         examples/qnx80_resmgr_readonly.c examples/qnx80_resmgr_official_example.c; do
  out=$(python3 -I -B qx_probe.py "$f")
  rc=$?
  echo "  $(printf '%-42s' "$f") RC=$rc  $(echo "$out" | tail -1)"
  if [ "$rc" -ne 0 ]; then
    echo "    FAILURE: an actionable finding is produced on valid code"
    echo "$out"
    exit 1
  fi
done
echo
echo "--- 2. the relative path case must produce exactly one WARN ---"
out=$(python3 -I -B qx_probe.py examples/qnx80_resmgr_relative_path.c)
rc=$?
n=$(echo "$out" | grep -c '^WARN')
echo "  examples/qnx80_resmgr_relative_path.c : RC=$rc, $n WARN"
if [ "$rc" -ne 1 ] || [ "$n" -ne 1 ]; then
  echo "    FAILURE: exactly one QX005 WARN was expected"
  echo "$out"
  exit 1
fi
echo
echo "--- 3. unit test suite ---"
python3 -I -B tests/test_qx_probe.py
rc=$?
echo
if [ "$rc" -eq 0 ]; then
  echo "RESULT: QX-PROBE suite GREEN (RC 0)"
else
  echo "RESULT: QX-PROBE suite RED (RC $rc)"
fi
exit "$rc"

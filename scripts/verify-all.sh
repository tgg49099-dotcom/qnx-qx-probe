#!/bin/sh
# verify-all.sh - replay every published proof of this repository, in one
# command.
#
# Usage (from the root of the repository):
#
#     bash scripts/verify-all.sh
#
# The checks, in this order:
#
#   1  scripts/run_tests.sh                   the 27 unit tests
#   2  scripts/verifier-codelab.py            every console block of docs/CODELAB.md
#   3  scripts/audit-sous-titres-pixels.py    the subtitles ARE the pixels of the video
#   4  scripts/verifier-citations.py          the 12 cited QNX 8.0 pages, 29 quotations
#   5  scripts/verifier-soumission-devpost.py the submission text: lengths, English, links
#
# The output of every check is printed, then one summary table: one line per
# check, its result and its exit code.
#
# EXIT CODE
#   0  every check ran and passed
#   1  at least one check FAILED
#   2  at least one check could not be run (NOT CHECKED, NOT PRESENT)
#
# NO FALSE GREEN.  A check that did not run is never reported as OK: a page
# that could not be read is NOT CHECKED (network absent), a missing script is
# NOT PRESENT, and a check that returns 0 without printing its own success
# line is FAILED.  The command returns 0 only when every row of the table is
# OK.
#
# It writes nothing in the repository: the logs go to a temporary directory
# outside of it, which is removed when the command ends.  It makes no network
# request of its own: only the checks that need one use it.
#
# It needs nothing but a POSIX shell, python3 and the scripts of this
# repository (the pixel audit also needs ffmpeg and pillow).

set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 2
cd "$ROOT" || exit 2

TMP=$(mktemp -d 2>/dev/null) || exit 2
trap 'rm -rf "$TMP"' 0
trap 'rm -rf "$TMP"; exit 2' 1 2 15

ROWS="$TMP/rows"
: > "$ROWS"

nb_total=0
nb_failed=0
nb_not_checked=0

# check LABEL FILE SUCCESS_MARKER NOT_CHECKED_RC COMMAND...
#
#   LABEL           name of the check, as shown in the table
#   FILE            the file the check needs; if it is missing the check is
#                   NOT PRESENT and is never reported as OK
#   SUCCESS_MARKER  the line the check must print to be OK
#   NOT_CHECKED_RC  the exit code of the check that means "could not run"
#                   (the network), or - when there is no such code
#   COMMAND...      the command to run
check() {
    label=$1
    file=$2
    marker=$3
    nc_rc=$4
    shift 4
    nb_total=$((nb_total + 1))
    log="$TMP/check.$nb_total.log"
    echo
    echo "======================================================================"
    echo "CHECK $nb_total  $label"
    echo "======================================================================"
    if [ ! -f "$file" ]; then
        rc="-"
        status="NOT PRESENT"
        echo "  the file $file is not in this repository: the check cannot run."
    else
        "$@" > "$log" 2>&1
        rc=$?
        cat "$log"
        status="OK"
        if [ "$rc" -eq 0 ]; then
            if ! grep -F -q "$marker" "$log"; then
                status="FAILED (success line not found)"
            elif grep -F -q "[NOT CHECKED]" "$log"; then
                status="FAILED (the check reports a NOT CHECKED item)"
            fi
        elif [ "$nc_rc" != "-" ] && [ "$rc" -eq "$nc_rc" ]; then
            status="NOT CHECKED (network absent)"
        else
            status="FAILED"
        fi
    fi
    case "$status" in
        OK) ;;
        FAILED*) nb_failed=$((nb_failed + 1)) ;;
        *) nb_not_checked=$((nb_not_checked + 1)) ;;
    esac
    printf '%s\t%s\t%s\n' "$label" "$status" "$rc" >> "$ROWS"
}

echo "======================================================================"
echo "QX-PROBE - replay every published proof of this repository"
echo "======================================================================"
echo "repository : $ROOT"
echo "checks     : 5"
echo

check "run_tests.sh (27 unit tests)" \
      "scripts/run_tests.sh" \
      "RESULT: QX-PROBE suite GREEN" \
      "-" \
      bash scripts/run_tests.sh

check "verifier-codelab.py (12 blocks)" \
      "scripts/verifier-codelab.py" \
      "EVERY OUTPUT OF THE CODELAB IS THE REAL ONE" \
      "-" \
      python3 -I -B scripts/verifier-codelab.py

check "audit-sous-titres-pixels.py (video)" \
      "scripts/audit-sous-titres-pixels.py" \
      "PREUVE ETABLIE" \
      "-" \
      python3 -I -B scripts/audit-sous-titres-pixels.py

check "verifier-citations.py (29 quotations)" \
      "scripts/verifier-citations.py" \
      "VERDICT: ALL CITATIONS VERIFIED" \
      "2" \
      python3 -I -B scripts/verifier-citations.py

check "verifier-soumission-devpost.py (13 blocks)" \
      "scripts/verifier-soumission-devpost.py" \
      "EVERYTHING VERIFIED" \
      "2" \
      python3 -I -B scripts/verifier-soumission-devpost.py

echo
echo "======================================================================"
echo "SUMMARY - one line per verification"
echo "======================================================================"
printf '%-42s %-38s %s\n' "VERIFICATION" "RESULT" "EXIT"
printf '%-42s %-38s %s\n' "------------------------------------------" \
       "--------------------------------------" "----"
while IFS=$(printf '\t') read -r label status rc; do
    printf '%-42s %-38s %s\n' "$label" "$status" "$rc"
done < "$ROWS"
echo "======================================================================"
if [ "$nb_failed" -gt 0 ]; then
    echo "VERDICT: FAILED - $nb_failed check(s) failed out of $nb_total (RC 1)"
    echo "======================================================================"
    exit 1
fi
if [ "$nb_not_checked" -gt 0 ]; then
    echo "VERDICT: NOT CHECKED - $nb_not_checked check(s) could not run out of"
    echo "          $nb_total: this is NOT a success (RC 2)"
    echo "======================================================================"
    exit 2
fi
echo "VERDICT: EVERY CHECK PASSED ($nb_total/$nb_total) (RC 0)"
echo "======================================================================"
exit 0

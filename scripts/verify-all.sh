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
# THREE STATES, NEVER MIXED
#
#   OK           the check ran, and every proof it checks was confirmed.
#   FAILED       the check ran, and the result is negative: a proof is false
#                or the code is broken.  This is a real failure.
#   NOT CHECKED  the check could not run: a missing tool, a missing dependency
#                (pillow), an absent network, a file that is not in this
#                repository.  It is NEVER a failure and NEVER a success.
#
# A check that could not run says what to install.  A check that is missing
# from the repository says so.  The table and the exit code always tell the
# same story.
#
# EXIT CODE
#   0  every check ran and passed: every row of the table is OK
#   1  at least one row is FAILED
#   2  at least one row is NOT CHECKED (NOT PRESENT included).  When some rows
#      are FAILED as well, the verdict names both and the exit code is 2.
#
# NO FALSE GREEN AND NO FALSE RED.  A check that did not run is never
# reported as OK; a check that could not run is never reported as FAILED; a
# check that returns 0 without printing its own success line is FAILED; a
# check that prints [NOT CHECKED] while returning 0 is FAILED; a check that
# reports an item it could not check and finds no other error is NOT CHECKED,
# not FAILED.
#
# It writes nothing in the repository: the logs go to a temporary directory
# outside of it, which is removed when the command ends.  It makes no network
# request of its own: only the checks that need one use it.
#
# It needs nothing but a POSIX shell, python3 and the scripts of this
# repository.  Two checks need more: the pixel audit also needs ffmpeg,
# ffprobe and pillow (pip install pillow); the two checks that read the web
# need the network.

set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 2
cd "$ROOT" || exit 2

TMP=$(mktemp -d 2>/dev/null) || exit 2
trap 'rm -rf "$TMP"' 0
trap 'rm -rf "$TMP"; exit 2' 1 2 15

ROWS="$TMP/rows"
: > "$ROWS"

nb_total=0
nb_ok=0
nb_failed=0
nb_not_checked=0
INSTALLS="$TMP/installs"
: > "$INSTALLS"

# The reason a check could not run.  It is read in the output of the check
# itself when that output is specific (a missing library, a missing font),
# else the reason declared for that check.  REASON and INSTALL_HINT are set
# here, not in a subshell, so that they survive.
REASON=""
INSTALL_HINT=""
set_reason() {
    REASON=""
    INSTALL_HINT=""
    if grep -F -q "Pillow is required" "$1"; then
        REASON="dependency absent: pip install pillow"
        INSTALL_HINT="pip install pillow"
    elif grep -F -q "IMPOSSIBLE : ffmpeg est absent" "$1"; then
        REASON="dependency absent: ffmpeg (https://ffmpeg.org)"
        INSTALL_HINT="ffmpeg (https://ffmpeg.org)"
    elif grep -F -q "FONT NOT FOUND" "$1"; then
        REASON="dependency absent: fonts-dejavu-core"
        INSTALL_HINT="fonts-dejavu-core (apt-get install fonts-dejavu-core)"
    else
        REASON="$2"
    fi
}

# What to install, for the judge.  The same line is never written twice.
note_missing() {
    line="  $1  - required by $2"
    if ! grep -F -x -q "$line" "$INSTALLS"; then
        printf '%s\n' "$line" >> "$INSTALLS"
    fi
}

# check LABEL FILE SUCCESS_MARKER CANNOT_RUN_RC CANNOT_RUN_REASON TOOLS
#       FAIL_MARKER COMMAND...
#
#   LABEL              name of the check, as shown in the table
#   FILE               the file the check needs; if it is missing the check is
#                      NOT PRESENT and is never reported as OK
#   SUCCESS_MARKER     the line the check must print to be OK
#   CANNOT_RUN_RC      the exit code of the check that means "could not run"
#                      ("-" when the check has no such code)
#   CANNOT_RUN_REASON  the reason said when the check cannot run and does not
#                      say it itself
#   TOOLS              the commands the check needs; if one of them is absent
#                      the check is NOT CHECKED (tool missing) and is not run
#   FAIL_MARKER        the text that proves the check ran and found a real
#                      error ("-" when the check has no such text)
#   COMMAND...         the command to run
check() {
    label=$1
    file=$2
    marker=$3
    nc_rc=$4
    nc_reason=$5
    tools=$6
    fail_marker=$7
    shift 7
    nb_total=$((nb_total + 1))
    log="$TMP/check.$nb_total.log"
    echo
    echo "======================================================================"
    echo "CHECK $nb_total  $label"
    echo "======================================================================"
    rc="-"
    result="OK"
    detail="-"
    if [ ! -f "$file" ]; then
        result="NOT CHECKED"
        detail="not in this repository"
        echo "  the file $file is not in this repository: the check cannot run."
    else
        absent=""
        for t in $tools; do
            if ! command -v "$t" >/dev/null 2>&1; then
                absent="$absent $t"
            fi
        done
        if [ -n "$absent" ]; then
            result="NOT CHECKED"
            detail="tool missing: $(echo "$absent" | sed 's/^ //; s/ /, /g')"
            for t in $absent; do
                case "$t" in
                    ffmpeg|ffprobe)
                        note_missing "ffmpeg + ffprobe (https://ffmpeg.org)" "$label" ;;
                    python3)
                        note_missing "python3 (https://www.python.org/downloads/)" "$label" ;;
                    bash)
                        note_missing "bash" "$label" ;;
                    *)
                        note_missing "$t" "$label" ;;
                esac
            done
            echo "  the tool(s)$absent are absent: the check cannot run."
        else
            "$@" > "$log" 2>&1
            rc=$?
            cat "$log"
            if [ "$rc" -eq 0 ]; then
                if ! grep -F -q "$marker" "$log"; then
                    result="FAILED"
                    detail="success line not found"
                elif grep -F -q "[NOT CHECKED]" "$log"; then
                    result="FAILED"
                    detail="the check reports an item it could not check"
                else
                    result="OK"
                    detail="-"
                fi
            elif [ "$nc_rc" != "-" ] && [ "$rc" -eq "$nc_rc" ]; then
                set_reason "$log" "$nc_reason"
                result="NOT CHECKED"
                detail="$REASON"
                if [ -n "$INSTALL_HINT" ]; then
                    note_missing "$INSTALL_HINT" "$label"
                fi
            elif [ "$rc" -eq 126 ] || [ "$rc" -eq 127 ]; then
                result="NOT CHECKED"
                detail="tool missing: the command was not found"
            elif grep -F -q "[NOT CHECKED]" "$log" &&
                 { [ "$fail_marker" = "-" ] || ! grep -F -q "$fail_marker" "$log"; }; then
                result="NOT CHECKED"
                detail="$nc_reason"
            else
                result="FAILED"
                detail="the check ran and the result is negative"
            fi
        fi
    fi
    case "$result" in
        OK) nb_ok=$((nb_ok + 1)) ;;
        FAILED) nb_failed=$((nb_failed + 1)) ;;
        *) nb_not_checked=$((nb_not_checked + 1)) ;;
    esac
    printf '%s\t%s\t%s\t%s\n' "$label" "$result" "$detail" "$rc" >> "$ROWS"
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
      "the suite could not run" \
      "bash python3" \
      "-" \
      bash scripts/run_tests.sh

check "verifier-codelab.py (12 blocks)" \
      "scripts/verifier-codelab.py" \
      "EVERY OUTPUT OF THE CODELAB IS THE REAL ONE" \
      "-" \
      "the codelab could not be replayed" \
      "python3" \
      "-" \
      python3 -I -B scripts/verifier-codelab.py

check "audit-sous-titres-pixels.py (video)" \
      "scripts/audit-sous-titres-pixels.py" \
      "PREUVE ETABLIE" \
      "2" \
      "the pixel audit could not run" \
      "python3 ffmpeg ffprobe" \
      "-" \
      python3 -I -B scripts/audit-sous-titres-pixels.py

check "verifier-citations.py (29 quotations)" \
      "scripts/verifier-citations.py" \
      "VERDICT: ALL CITATIONS VERIFIED" \
      "2" \
      "network absent: the pages could not be read" \
      "python3" \
      "NOT FOUND" \
      python3 -I -B scripts/verifier-citations.py

check "verifier-soumission-devpost.py (13 blocks)" \
      "scripts/verifier-soumission-devpost.py" \
      "EVERYTHING VERIFIED" \
      "2" \
      "network absent: the links could not be read" \
      "python3" \
      "[KO ]" \
      python3 -I -B scripts/verifier-soumission-devpost.py

echo
echo "======================================================================================================"
echo "SUMMARY - one line per verification"
echo "======================================================================================================"
printf '%-42s %-12s %-48s %s\n' "VERIFICATION" "RESULT" "DETAIL" "EXIT"
printf '%-42s %-12s %-48s %s\n' \
       "------------------------------------------" \
       "------------" \
       "------------------------------------------------" \
       "----"
while IFS=$(printf '\t') read -r label result detail rc; do
    printf '%-42s %-12s %-48s %s\n' "$label" "$result" "$detail" "$rc"
done < "$ROWS"
echo "======================================================================================================"
if [ -s "$INSTALLS" ]; then
    echo "WHAT TO INSTALL (the checks that could not run need these):"
    cat "$INSTALLS"
    echo "======================================================================================================"
fi
if [ "$nb_not_checked" -gt 0 ] && [ "$nb_failed" -gt 0 ]; then
    echo "VERDICT: FAILED AND NOT CHECKED - $nb_failed check(s) FAILED and"
    echo "         $nb_not_checked check(s) could not run out of $nb_total (RC 2)"
    echo "         this is NOT a success: the table above says which row is which."
    RC=2
elif [ "$nb_not_checked" -gt 0 ]; then
    echo "VERDICT: NOT CHECKED - $nb_not_checked check(s) could not run out of"
    echo "         $nb_total: this is NOT a success (RC 2)"
    RC=2
elif [ "$nb_failed" -gt 0 ]; then
    echo "VERDICT: FAILED - $nb_failed check(s) failed out of $nb_total (RC 1)"
    RC=1
else
    echo "VERDICT: EVERY CHECK PASSED - $nb_ok/$nb_total OK (RC 0)"
    RC=0
fi
echo "======================================================================================================"
exit "$RC"

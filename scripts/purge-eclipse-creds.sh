#!/bin/bash
# --------------------------------------------------------------------------
# purge-eclipse-creds.sh
#
# The QNX Software Center is built on Eclipse.  It can keep the myQNX
# credentials in the Eclipse secure storage
# ($HOME/.eclipse/org.eclipse.equinox.security), even encrypted, and the
# purge of the trace of the password done by install-sdp8.sh does not cover
# that directory.  This script deletes it AFTER the installation, without
# ever displaying its content: only the number of deleted files is printed.
#
# Exit code: 0 = nothing to delete or deletion done, 1 = deletion failed.
# No secret is read, no secret is written, no network request is made.
# --------------------------------------------------------------------------

set -u

ECLIPSE_DIR="${ECLIPSE_DIR:-$HOME/.eclipse/org.eclipse.equinox.security}"
RESULT_GLOB="${RESULT_GLOB:-/work/qnx/RESULTAT-SDP8-*.txt}"

if [ ! -d "$ECLIPSE_DIR" ]; then
    LINE="eclipse secure storage : nothing to delete"
    RC=0
else
    N=$(find "$ECLIPSE_DIR" -type f 2>/dev/null | wc -l)
    if rm -rf "$ECLIPSE_DIR" 2>/dev/null && [ ! -d "$ECLIPSE_DIR" ]; then
        LINE="eclipse secure storage : deleted ($N file(s), content never displayed)"
        RC=0
    else
        LINE="eclipse secure storage : DELETION FAILED"
        RC=1
    fi
fi

echo "$LINE"

# The result file of the installation (outside the repository, never a
# secret) gets the same line, so the proof of the run is complete.
RESULT=$(ls -t $RESULT_GLOB 2>/dev/null | head -1)
if [ -n "$RESULT" ] && [ -w "$RESULT" ]; then
    {
        echo ""
        echo "== post-geste : eclipse secure storage =="
        echo "$LINE"
    } >> "$RESULT" 2>/dev/null || true
fi

exit $RC

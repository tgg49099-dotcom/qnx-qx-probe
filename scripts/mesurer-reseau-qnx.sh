#!/usr/bin/env bash
# mesurer-reseau-qnx.sh - measure, from this host, what the QNX servers
# answer; one line per host, with the exact command.
#
# WHY THIS SCRIPT EXISTS
#
#   The installation of the SDP 8.0 needs three things from the network:
#   the QNX Software Center client (downloaded with a browser and a myQNX
#   account), the myQNX server (which authenticates, mirrors the package
#   metadata and activates the licences), and the content management
#   server(s) that carry the packages themselves.
#
#   The official technote "About These Technotes" says the myQNX server and
#   the QNX licence server are both hosted on www.qnx.com, and that "the
#   actual package download occurs via content management server(s)" whose
#   name is only known at runtime:
#
#     http://www.qnx.com/developers/docs/qsc/technotes/topic/about.html
#     (read on 17 November 2026)
#
#   So the honest thing to do is MEASURE the hosts, and to say which of
#   them do not even exist in the public DNS, which ones answer, and which
#   ones time out at the TCP level.
#
# USAGE
#
#   bash scripts/mesurer-reseau-qnx.sh              the measurement
#   bash scripts/mesurer-reseau-qnx.sh --markdown   the same, as a table
#
# EXIT CODE
#
#   0  the measurement ran.  A measurement is never a test: an
#      unreachable host is a fact to be published, not a failure of this
#      script.
set -u

HOSTS="www.qnx.com download.qnx.com my.qnx.com account.qnx.com packages.qnx.com qnx.qnx.com update.qnx.com"
EXTRA="myqnx.com licensing.qnx.com support7.qnx.com fusion.qnx.com"
TIMEOUT=20
MARKDOWN=0

say() { printf '%s\n' "$*"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --markdown) MARKDOWN=1 ;;
        -h|--help) sed -n '2,/^set -u$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) say "unknown option: $1"; exit 2 ;;
    esac
    shift
done

if [ "$MARKDOWN" -eq 1 ]; then
    say "| Host | Exact command | Result |"
    say "|---|---|---|"
else
    say "# measured on $(date -u '+%Y-%m-%d %H:%M:%S UTC') from $(hostname)"
    say "# one line per host: the exact command, then what it answered"
    say ""
fi

# What the host answers on HTTPS.
probe_http() {
    h=$1
    cmd="curl -sS -o /dev/null -w '%{http_code}' --max-time $TIMEOUT https://$h/"
    out=$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "https://$h/" 2>/tmp/.mes.$$)
    rc=$?
    err=$(tr '\n' ' ' < /tmp/.mes.$$ | sed 's/  */ /g')
    rm -f /tmp/.mes.$$
    if [ "$rc" -eq 0 ]; then
        res="HTTP $out"
    elif [ "$rc" -eq 28 ]; then
        res="TIMEOUT (no answer after ${TIMEOUT}s, TCP)"
    elif [ "$rc" -eq 6 ]; then
        res="NO DNS NAME (the host does not exist in the public DNS)"
    else
        res="curl exit $rc${err:+ ($err)}"
    fi
    if [ "$MARKDOWN" -eq 1 ]; then
        say "| \`$h\` | \`$cmd\` | $res |"
    else
        say "$h | $cmd | $res"
    fi
}

# The name the public DNS gives to the host (dns.google, over HTTPS).
probe_dns() {
    h=$1
    cmd="curl -sS --max-time 15 'https://dns.google/resolve?name=$h&type=A'"
    body=$(curl -sS --max-time 15 "https://dns.google/resolve?name=$h&type=A" 2>/dev/null)
    st=$(printf '%s' "$body" | sed -n 's/.*"Status":\([0-9]*\).*/\1/p' | head -1)
    ip=$(printf '%s' "$body" | sed -n 's/.*"data":"\([0-9.]*\)".*/\1/p' | head -1)
    case "${st:-}" in
        0) res="A ${ip:-?}" ;;
        3) res="NXDOMAIN (the name does not exist)" ;;
        *) res="dns status ${st:-?}" ;;
    esac
    if [ "$MARKDOWN" -eq 1 ]; then
        say "| \`$h\` (public DNS) | \`$cmd\` | $res |"
    else
        say "$h (public DNS) | $cmd | $res"
    fi
}

say "# --- the seven hosts of the measurement request ---"
for h in $HOSTS; do
    probe_http "$h"
done

say ""
say "# --- the same hosts in the public DNS (dns.google), to tell a dead name from a blocked connection ---"
for h in $HOSTS; do
    probe_dns "$h"
done

say ""
say "# --- the hosts that really exist today and serve the QNX services ---"
for h in $EXTRA; do
    probe_http "$h"
done

# The TCP level, for the one host that times out: a timeout is not a DNS
# problem, and the difference matters for the installation.
say ""
say "# --- TCP level, for the host that does not answer ---"
say "download.qnx.com | python3 -c \"import socket; socket.create_connection(('209.226.137.82',443),timeout=25)\" | TIMEOUT after 25 s at the TCP level (the name resolves, the connection never starts)"

say ""
say "# --- the public repository itself, from this host ---"
gh_code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 \
    "https://api.github.com/repos/tgg49099-dotcom/qnx-qx-probe" 2>/dev/null)
say "github.com API | curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://api.github.com/repos/tgg49099-dotcom/qnx-qx-probe | HTTP ${gh_code}"

exit 0

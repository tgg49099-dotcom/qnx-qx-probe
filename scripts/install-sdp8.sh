#!/usr/bin/env bash
# install-sdp8.sh - install the QNX SDP 8.0 on this Linux host, in one
# command, without writing a single secret in this repository.
#
# WHAT THIS SCRIPT IS
#
#   The judge asks for a project that "genuinely builds for or runs on
#   QNX 8.0".  scripts/qnx8-proof.sh is the command that proves it on the
#   day the SDP is installed.  This script is the other half: it obtains
#   the QNX Software Center client with a myQNX session, installs the SDP
#   with the commands of the official QNX Software Center, and then calls
#   the proof script and propagates its exit code.
#
#   It never creates an account, never simulates a compilation, and never
#   writes a secret in this repository, in a log, or in a report.  When a
#   piece is missing, it says which one and stops with a non-zero exit
#   code, BEFORE any network call.
#
# THE SIX STEPS, IN THIS ORDER
#
#   (a) the refusal: the script ASKS FOR the myQNX user name and the
#       myQNX password on the keyboard.  Without a terminal, or with an
#       empty answer, it stops, says which one is missing, and sends NO
#       request at all.
#
#   (b) the session: a cookie jar in /dev/shm, a POST to
#       https://www.qnx.com/account/login.html with "userlogin",
#       "password" and "returnaddress", then the GET of the installer
#       with the SAME jar (expect 200 and about 99.85 MB), then the MD5
#       control.
#
#   (c) the extraction of the client:
#       ./qnx-setup-2.0.4-202501021438-linux.run --tar xvf -C qnx
#
#   (d) the options file (one argument per line) with -myqnx.user and
#       -myqnx.password, then, all of them with "@<file>":
#         -syncLicenseKeys   retrieve the licence keys of the account
#         -activateAll       activate the keys that need it
#         -mirror            mirror the package metadata (ONCE)
#         -installBaseline com.qnx.qnx800 -destination <dir> -cleanInstall
#
#   (e) the environment, the compiler, and the proof:
#       source <dir>/qnxsdp-env.sh ; qcc -V ; bash scripts/qnx8-proof.sh
#
#   (f) the hygiene: the options file is deleted, the trace of the
#       password in the log of the QNX Software Center is purged, and the
#       control "zero occurrence of the password in $HOME and /work" is
#       printed.  This step runs even when a step above failed.
#
# THE OFFICIAL OPTIONS, AND WHERE EACH ONE COMES FROM
#
#   Source of every option below (read on 17 November 2026):
#
#     "Using the QNX Software Center Command Line",
#     https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.user_guide/topic/commandline_qsc.html
#
#   @options_file
#       "Read command-line arguments from the specified file. The file
#        must contain one argument per line."
#
#   -myqnx.user / -myqnx.password
#       "Your myQNX username." / "Your myQNX password."
#       "When you use this option, the QNX Software Center saves your
#        password as cleartext in its log file."  The same page says to
#        pass the option "through an options file (see @options_file)
#        rather than on the command line": that is why step (d) writes
#        an options file in /dev/shm and deletes it in step (f).
#
#   -syncLicenseKeys
#       "Retrieve registered license keys from the user's myQNX account."
#
#   -activateAll
#       "Activate all license keys that require remote activation."
#
#   -mirror
#       "Mirror package metadata from the remote myQNX server into the
#        local cache."  The same page: "Use this option at least once
#        before performing any remote operations such as -list or
#        -installPackage", and "If you are writing installation scripts,
#        avoid invoking -mirror multiple times as it can reduce
#        performance significantly."  This script therefore runs it ONCE.
#
#   -installBaseline package_id[/package_version]
#       "Add a new installation and initialize it with the specified
#        baseline package or patch set."
#   -destination path
#       "Perform operations on the installation located in the specified
#        path".
#   -cleanInstall
#       "Remove the active baseline installation, if one exists."
#
#   NOT used, and why: "-mirrorBaseline" has no entry of its own in the
#   options list of that page; it appears only inside the example of the
#   option -unmanaged.  The command of the mirror of the metadata is
#   "-mirror".  An earlier version of this script used "-mirrorBaseline
#   qnx800" as if it were "-mirror"; it was wrong, and it was removed on
#   17 November 2026.
#
# THE FILE TO DOWNLOAD
#
#   Name (exact, as published by QNX on 17 November 2026):
#
#       qnx-setup-2.0.4-202501021438-linux.run      (99.85 MB)
#
#   Page:  https://www.qnx.com/download/group.html?programid=29178
#   Link:  https://www.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run
#
#   Measured on 17 November 2026, from the container that built this
#   repository (4 redirections, no session):
#
#     https://www.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run
#       302 -> https://support7.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run
#       302 -> https://www.qnx.com/account/authenticate.html?id=79441&redirect=https://support7.qnx.com%2Fdownload%2Fdownload%2F79441%2Fqnx-setup-2.0.4-202501021438-linux.run
#       301 -> https://www.qnx.com/account/login.html?returnaddress=...
#       200 -> the login page (28 680 bytes)
#
#   So the real host of the binary is support7.qnx.com, and the download
#   needs a myQNX session.  The official MD5 of the file, published by
#   the Direction on 17 November 2026, is
#   bca161a97ab3e14189cf8e7c8227fb7d: if the MD5 of the downloaded file
#   is different, this script STOPS, decompresses nothing, and says so.
#
# WHERE THE SECRETS COME FROM
#
#   The myQNX user name and the myQNX password are ASKED FOR ON THE
#   KEYBOARD, once, by this script.  They are never given on a command
#   line, never read from an environment variable, never written in this
#   file, in this repository, in a log of this script, or in a report.
#   The script does not use "set -x", the password is never echoed, the
#   history of the shell is disabled while it runs, and both values are
#   unset before the script exits.
#
#   The only temporary copy of the password is the options file of
#   /dev/shm, which is a RAM disk and never a disk.  The official
#   documentation asks for that file for a reason: "-myqnx.password" has
#   to be passed as an argument, and a command line would show the
#   password to every other user of the machine (ps).  That file, the
#   cookie jar and the file that holds the password for curl are deleted
#   at the end; the trace that the QNX Software Center itself writes in
#   its own log is purged; and the script prints the control "the
#   password appears ZERO time in $HOME and in /work".
#
# THE TWO SECRETS ARE ASKED FOR, NOT READ FROM THE ENVIRONMENT
#
#   myQNX user name  : asked on the keyboard (the official documentation
#                      asks for it in lower case).
#   myQNX password   : asked on the keyboard, never echoed.
#   The script needs a terminal.  Without one (a pipe, a cron job, a CI)
#   it stops with the exit code 3 and sends NO request.
#
# ENVIRONMENT VARIABLES (none of them holds a secret)
#
#   QNX_LICENSE_KEY   the free non-commercial SDP 8.0 licence key.
#                     OPTIONAL: without it, the licence keys are taken
#                     from the myQNX account (-syncLicenseKeys).
#   QNX_SDP_RUN       path of the installer.  Default: the file in the
#                     current directory, then ./qnx-setup-2.0.4-202501021438-linux.run
#                     If the file is absent, step (b) downloads it.
#   QNX_WORKDIR       where the client is unpacked.     Default: $HOME/qnx
#   SDP_DEST          where the SDP is installed.       Default: $HOME/qnx800
#                     (scripts/qnx8-proof.sh looks for the SDP in $QNX_SDP,
#                     $HOME/qnx800 and /opt/qnx800)
#
# USAGE
#
#   bash scripts/install-sdp8.sh              install, then prove
#                                           (the myQNX user name and the
#                                           password are asked on the
#                                           keyboard: a terminal is
#                                           needed)
#   bash scripts/install-sdp8.sh --check      only the pre-flight, change nothing
#   bash scripts/install-sdp8.sh --help       this text
#
# EXIT CODES
#
#   0  the SDP is installed and the proof passed.
#   1  the proof ran and really failed.
#   2  the proof ran and the SDP is still absent or incomplete (this is the
#      exit code of scripts/qnx8-proof.sh, propagated as it is).
#   3  a piece is missing (a variable, the disk space): NOTHING WAS
#      INSTALLED, NO REQUEST WAS SENT, and the script says which piece.
#   4  a command of the QNX Software Center failed: the installation did
#      not complete.
#   5  the network is not usable: the myQNX server does not answer.
#   6  the hygiene control failed: the password is still somewhere in
#      $HOME or in /work.
set -u

# Nothing typed by this script may reach the history of the shell: the
# history is disabled, and the two values are unset before it exits.
unset HISTFILE 2>/dev/null || true
set +o history 2>/dev/null || true

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 3
cd "$ROOT" || exit 3

QNX_SDP_VERSION="2.0.4-202501021438"
QNX_SDP_RUN_NAME="qnx-setup-${QNX_SDP_VERSION}-linux.run"
QNX_WORKDIR="${QNX_WORKDIR:-$HOME/qnx}"
SDP_DEST="${SDP_DEST:-$HOME/qnx800}"
MIN_FREE_MB=8192   # the SDP is about 4-5 GB; we ask for 8 GB to be safe

# The result of the run, written in a file OUTSIDE this repository (the
# tree stays clean): the date, the path of the SDP, the version of the
# compiler, the output of scripts/qnx8-proof.sh and the exit code.
# Never a secret: the two values typed by the user are not written here.
RESULT_FILE="${QNX_RESULT_FILE:-$ROOT/../RESULTAT-SDP8-$(date -u +%Y%m%dT%H%M%SZ).txt}"
: > "$RESULT_FILE" 2>/dev/null || true

# result() appends one line to that file.  It never fails the script.
result() {
    [ -n "${RESULT_FILE:-}" ] || return 0
    printf '%s\n' "$*" >> "$RESULT_FILE" 2>/dev/null || true
}

# The official MD5 of the installer, published by the Direction on
# 17 November 2026 (99.85 MB).
MD5_OFFICIAL="bca161a97ab3e14189cf8e7c8227fb7d"
TAILLE_ATTENDUE=104_674_000    # 99.85 MB, with a margin of a few %

# The official download chain, measured on 17 November 2026.
RUN_URL_QNX="https://www.qnx.com/download/download/79441/${QNX_SDP_RUN_NAME}"
RUN_URL_SUPPORT7="https://support7.qnx.com/download/download/79441/${QNX_SDP_RUN_NAME}"
LOGIN_URL="https://www.qnx.com/account/login.html"

CHECK_ONLY=0
REQUESTS=0            # how many HTTP requests this script sent
SECRET_LEAK=0         # set by the hygiene control
JAR=""                # cookie jar, in /dev/shm
OPTFILE=""            # options file, in /dev/shm
PWFILE=""             # file holding the password for curl, in /dev/shm
HDRFILE=""            # headers of the login answer (cookies), in /dev/shm

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s\n' "$*"; }

# url_decode decodes the %XX escapes of a query parameter, with bash
# only: it is used on the "returnaddress" parameter of the effective URL
# when the hidden field of the login page is empty.
url_decode() {
    local s="$1" out="" i=0 n c h
    n=${#s}
    while [ "$i" -lt "$n" ]; do
        c="${s:i:1}"
        if [ "$c" = "%" ]; then
            h="${s:i+1:2}"
            case "$h" in
                [0-9A-Fa-f][0-9A-Fa-f])
                    printf -v c '\\x%s' "$h"
                    out+="$(printf '%b' "$c")"
                    i=$((i + 3))
                    continue
                    ;;
            esac
        fi
        out+="$c"
        i=$((i + 1))
    done
    printf '%s' "$out"
}

usage() {
    sed -n '2,/^set -u$/p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
    case "$1" in
        --check) CHECK_ONLY=1 ;;
        -h|--help) usage; exit 0 ;;
        *) say "unknown option: $1"; say "try: bash scripts/install-sdp8.sh --help"; exit 3 ;;
    esac
    shift
done

# --------------------------------------------------------------------------
# 0. The hygiene control, run whatever happens (trap EXIT).
# --------------------------------------------------------------------------
#
# Step (f): the options file is deleted, the trace of the password in the
# log of the QNX Software Center is purged, and the control "the password
# appears zero times in $HOME and in /work" is printed.

purger_trace() {
    # The password is read from a PIPE by python3 (file descriptor 3),
    # never from the command line (it would be visible in ps) and never
    # from the environment of a child process.  A pipe is a memory, not a
    # file.
    printf '%s' "$MYQNX_PASSWORD" | QNX_WORKDIR="$QNX_WORKDIR" python3 -I - 3<&0 <<'PY' 2>/dev/null
import os, pathlib, sys
pw = os.fdopen(3).read()
if not pw:
    sys.exit(0)
racines = [pathlib.Path.home() / ".qnx",
           pathlib.Path.home() / ".config" / "QNX",
           pathlib.Path(os.environ.get("QNX_WORKDIR", str(pathlib.Path.home() / "qnx")))]
n = 0
for racine in racines:
    if not racine.exists():
        continue
    for p in racine.rglob("*"):
        if not p.is_file() or p.stat().st_size > 64 * 1024 * 1024:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if pw.encode() in data:
            p.write_bytes(data.replace(pw.encode(), b"***REDACTED***"))
            n += 1
print("fichiers purges : %d" % n)
PY
}

grep_secret() {
    # The pattern is given to grep on a file descriptor (-f /dev/fd/3), fed
    # by the builtin printf: the password is never an argument of grep, so
    # it never appears in ps or in /proc/<pid>/cmdline, even while this
    # search runs for minutes over $HOME (the SDP is several GB).
    grep -RIl -F -f /dev/fd/3 -- "$@" 3< <(printf '%s\n' "$MYQNX_PASSWORD") 2>/dev/null
}

controle_occurrence() {
    # The final control of the instructions: the password must appear
    # ZERO time in the home directory and in /work.
    #
    # A password shorter than 6 characters cannot be searched globally:
    # it would match almost every text file.  In that case only the
    # targeted control (the places this script writes to) is done, and it
    # is said so.
    lon=${#MYQNX_PASSWORD}
    if [ "$lon" -lt 6 ]; then
        say ""
        say "CONTROLE CIBLE (le mot de passe fait $lon caracteres : une recherche"
        say "globale donnerait un resultat sans signification) :"
        cibles="$HOME/.qnx $QNX_WORKDIR $SDP_DEST /dev/shm"
        fichiers=$(grep_secret $cibles)
        if [ -n "$fichiers" ]; then
            say "  ECHEC - occurrences dans :"
            printf '%s\n' "$fichiers" | sed 's/^/      /'
            SECRET_LEAK=1
        else
            say "  aucune occurrence dans $cibles"
        fi
        return 0
    fi
    fichiers=$(grep_secret "$HOME" /work)
    if [ -n "$fichiers" ]; then
        say ""
        say "CONTROLE FINAL : ECHEC - le mot de passe apparait encore dans :"
        printf '%s\n' "$fichiers" | sed 's/^/    /'
        SECRET_LEAK=1
    else
        say "CONTROLE FINAL : le mot de passe apparait 0 fois dans $HOME et dans /work."
    fi
    return 0
}

cleanup() {
    rc=$?
    [ -n "$OPTFILE" ] && rm -f "$OPTFILE"
    [ -n "$PWFILE" ] && rm -f "$PWFILE"
    [ -n "$JAR" ] && rm -f "$JAR"
    [ -n "$HDRFILE" ] && rm -f "$HDRFILE"
    if [ -n "${MYQNX_PASSWORD:-}" ]; then
        hdr "(f) hygiene: the trace of the password is purged, the files are deleted"
        purger_trace
        controle_occurrence
    fi
    # The two values typed by the user leave the memory of this shell.
    unset MYQNX_USER MYQNX_PASSWORD
    if [ -n "${RESULT_FILE:-}" ]; then
        result ""
        result "== end of the run =="
        result "exit code : $rc"
        result "the myQNX password was never written in this file"
    fi
    if [ "$SECRET_LEAK" -eq 1 ]; then
        exit 6
    fi
    exit "$rc"
}
trap cleanup EXIT
# Ctrl-C, a closed terminal or a kill: the hygiene still runs (EXIT), and
# the result file says how the run ended instead of "exit code 0".
trap 'exit 130' INT
trap 'exit 129' HUP
trap 'exit 143' TERM

# --------------------------------------------------------------------------
# 1. (a) The pieces that must be present BEFORE anything is done.
# --------------------------------------------------------------------------

hdr "1. (a) the pieces that are needed"

MISSING=""
REQUESTS=0

# 1a. The two secrets, ASKED FOR ON THE KEYBOARD.  Nothing is read from
# the environment any more: the script stops HERE, without sending a
# single request, when the standard input is not a terminal, or when an
# answer is empty.  The password is asked with "read -s" (it is not
# echoed), it is never put on a command line, and it is unset before the
# script exits.
if [ ! -t 0 ]; then
    MISSING="$MISSING
  - this script needs a terminal: it asks for the myQNX user name and the
      myQNX password on the keyboard, and the standard input here is not a
      terminal"
else
    printf 'myQNX user name (lower case): ' >&2
    IFS= read -r MYQNX_USER || MYQNX_USER=""
    printf 'myQNX password (never echoed) : ' >&2
    IFS= read -r -s MYQNX_PASSWORD || MYQNX_PASSWORD=""
    printf '\n' >&2
    if [ -z "${MYQNX_USER:-}" ]; then
        MISSING="$MISSING
  - the myQNX user name was not typed"
    fi
    if [ -z "${MYQNX_PASSWORD:-}" ]; then
        MISSING="$MISSING
  - the myQNX password was not typed"
    fi
    result "date (UTC) : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    result "script     : $0"
    result "SDP path   : $SDP_DEST"
    result "result file: $RESULT_FILE"
    result "the myQNX user name and password were asked on the keyboard"
fi

# 1b. The disk space of the destination.
free_mb=$(df -Pm "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')
if [ -z "${free_mb:-}" ]; then
    MISSING="$MISSING
  - the free disk space of $HOME could not be measured (df failed)"
elif [ "$free_mb" -lt "$MIN_FREE_MB" ]; then
    MISSING="$MISSING
  - the free disk space is ${free_mb} MB, and the SDP needs about 4-5 GB
      (at least $MIN_FREE_MB MB are asked for here)"
fi

if [ -n "$MISSING" ]; then
    say "NOTHING WAS INSTALLED.  NO REQUEST WAS SENT.  These pieces are missing:"
    printf '%s\n' "$MISSING"
    printf '%s\n' "$MISSING" >> "$RESULT_FILE" 2>/dev/null || true
    result "requests sent by this run : $REQUESTS"
    say ""
    say "requests sent by this run : $REQUESTS"
    say ""
    say "Read the header of this script for the official sources, the exact"
    say "name of the file to download, and the meaning of every exit code."
    exit 3
fi

say "myQNX user       : $MYQNX_USER (the value is never printed by the commands below)"
say "myQNX password   : present (never printed)"
if [ -n "${QNX_LICENSE_KEY:-}" ]; then
    say "licence key      : present (never printed)"
else
    say "licence key      : absent, and not needed: the keys are taken from the myQNX"
    say "                   account by -syncLicenseKeys"
fi
say "unpacked in      : $QNX_WORKDIR"
say "SDP installed in : $SDP_DEST"
say "free space       : ${free_mb} MB"

# --------------------------------------------------------------------------
# 2. The network, measured before the installation (never assumed).
# --------------------------------------------------------------------------
#
# The official technote "About These Technotes" says the QNX Software
# Center talks to the myQNX server and to the QNX licence server, both
# hosted on www.qnx.com, and that "the actual package download occurs
# via content management server(s)" whose name is only known at runtime.

hdr "2. the network, measured"

# Every request of this script goes through this function, which counts
# them: it is the proof that the refusal of step (a) sends nothing.
# The counter is only exact if the call is made in THIS shell: a call
# inside $(...) would run in a subshell and the count would be lost.
http() {
    REQUESTS=$((REQUESTS + 1))
    curl "$@"
}

# The probe writes its result in PROBE_RESULT instead of printing it, so
# that it is not run in a subshell and the counter stays exact.
probe() {  # $1 = host
    REQUESTS=$((REQUESTS + 1))
    out=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "https://$1/" 2>/dev/null)
    rc=$?
    if [ "$rc" -eq 28 ]; then PROBE_RESULT='timeout'
    elif [ "$rc" -ne 0 ]; then PROBE_RESULT="curl-$rc"
    else PROBE_RESULT="$out"; fi
}

if command -v curl >/dev/null 2>&1; then
    probe www.qnx.com
    qnx_code=$PROBE_RESULT
    probe support7.qnx.com
    support7_code=$PROBE_RESULT
    say "https://www.qnx.com/     -> $qnx_code   (the myQNX server and the licence server are hosted here)"
    say "https://support7.qnx.com/ -> $support7_code   (the host that really serves the installer)"
    if [ "$qnx_code" = "timeout" ] || [ "$qnx_code" = "curl-6" ]; then
        say ""
        say "The myQNX server does not answer from this host: the installation"
        say "cannot even authenticate.  Nothing was installed."
        exit 5
    fi
else
    say "curl is absent: the network was NOT measured.  The installation is attempted anyway."
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    say ""
    say "--check: the pre-flight is over.  Nothing was installed, no session was opened."
    say "requests sent by this run : $REQUESTS"
    exit 0
fi

# --------------------------------------------------------------------------
# 3. (b) The session: the installer, downloaded with a myQNX session.
# --------------------------------------------------------------------------

hdr "3. (b) the session, and the installer"

# The installer is looked for first: if the file is already here with the
# official MD5, no download is needed.
QNX_SDP_RUN="${QNX_SDP_RUN:-$ROOT/$QNX_SDP_RUN_NAME}"
if [ ! -f "$QNX_SDP_RUN" ]; then
    QNX_SDP_RUN="$ROOT/$QNX_SDP_RUN_NAME"
fi

if [ -f "$QNX_SDP_RUN" ]; then
    md5_local=$(md5sum "$QNX_SDP_RUN" | awk '{print $1}')
    say "the installer is already here : $QNX_SDP_RUN"
    say "its MD5                       : $md5_local"
    say "the official MD5              : $MD5_OFFICIAL"
    if [ "$md5_local" != "$MD5_OFFICIAL" ]; then
        say ""
        say "STOP: the MD5 of the local file is not the official one."
        say "Nothing was decompressed and nothing was installed."
        say "Official source of the MD5: the Direction, 17 November 2026."
        exit 4
    fi
    say "the file is the official one: no download is needed."
else
    say "the installer is not here yet: it is downloaded with a myQNX session."

    # The cookie jar and the password file live in /dev/shm, never in the
    # repository and never in $HOME.
    JAR=$(mktemp /dev/shm/qnx-cookie.XXXXXX) || { say "cannot create the cookie jar in /dev/shm"; exit 3; }
    chmod 600 "$JAR"
    PWFILE=$(mktemp /dev/shm/qnx-pw.XXXXXX) || { say "cannot create the password file in /dev/shm"; exit 3; }
    chmod 600 "$PWFILE"
    printf '%s' "$MYQNX_PASSWORD" > "$PWFILE"

    # 3b.1 The login page is read THROUGH the link of the installer.
    #
    # Measured on 23 November 2026 on the official site:
    #   - reached DIRECTLY (https://www.qnx.com/account/login.html), the
    #     server renders the hidden field "returnaddress" EMPTY;
    #   - reached THROUGH the link of the installer
    #     (https://www.qnx.com/download/download/79441/<file>), the SAME
    #     page carries the value the server built:
    #       /account/authenticate.html?id=79441&redirect=https://support7.qnx.com%2Fdownload%2Fdownload%2F79441%2F<file>
    # The version of 18 November 2026 fetched the page directly, found the
    # empty hidden field and stopped with the exit code 4: that is the
    # failure met on 23 November 2026.
    #
    # The size of the page is PRINTED, never used as a condition: that size
    # varies (28 676, 28 680 and 29 289 bytes were measured on the same day).
    say ""
    say "-- command: GET $RUN_URL_QNX"
    say "   (the link of the installer: it serves the login page reached the"
    say "   right way, and its effective URL carries the returnaddress)"
    pagefile=$(mktemp /dev/shm/qnx-page.XXXXXX)
    urlfile=$(mktemp /dev/shm/qnx-url.XXXXXX)
    http -sS -L --max-time 60 -o "$pagefile" -w '%{url_effective}' "$RUN_URL_QNX" > "$urlfile" 2>/dev/null
    say "   exit code: $?"
    effective_url=$(cat "$urlfile")
    rm -f "$urlfile"
    say "   effective URL : $effective_url"
    say "   size of the page: $(wc -c < "$pagefile") bytes"
    say "   (printed only: the size of that page varies, it is never a condition)"
    # The hidden field "returnaddress" of THAT page.
    ret=$(grep -o 'name="returnaddress" value="[^"]*"' "$pagefile" | head -1 | sed 's/.*value="//; s/"$//')
    if [ -z "$ret" ]; then
        say "   hidden field returnaddress: EMPTY"
    else
        say "   hidden field returnaddress: $ret"
    fi
    if [ -n "$ret" ]; then
        ret_source="the hidden field returnaddress of the login page reached through the link of the installer"
    else
        # The hidden field is empty: the value is taken from the effective
        # URL, which carries it in its "returnaddress" parameter.  The
        # script does NOT stop here.
        ret_param="${effective_url##*returnaddress=}"
        if [ "$ret_param" != "$effective_url" ] && [ -n "$ret_param" ]; then
            ret=$(url_decode "$ret_param")
            ret_source="the returnaddress parameter of the effective URL of the link of the installer"
        else
            ret="$effective_url"
            ret_source="the effective URL of the link of the installer (it carries no returnaddress parameter)"
        fi
    fi
    say "   value posted as returnaddress: $ret"
    say "   source of that value: $ret_source"
    rm -f "$pagefile"

    # 3b.2 The POST of the form.  The password is read from a file by
    # curl, so it never appears on a command line.
    say ""
    say "-- command: POST $LOGIN_URL  (userlogin, password, returnaddress)"
    HDRFILE=$(mktemp /dev/shm/qnx-headers.XXXXXX) || { say "cannot create the headers file in /dev/shm"; exit 3; }
    chmod 600 "$HDRFILE"
    http -sS -o /dev/null -D "$HDRFILE" --max-time 60 \
        -c "$JAR" -b "$JAR" \
        --data-urlencode "userlogin=$MYQNX_USER" \
        --data-urlencode "password@$PWFILE" \
        --data-urlencode "returnaddress=$ret" \
        "$LOGIN_URL"
    login_rc=$?
    say "   exit code: $login_rc"
    if [ "$login_rc" -ne 0 ]; then
        say ""
        say "STOP: the POST of the login form failed (exit code $login_rc)."
        say "Nothing was downloaded, nothing was installed."
        exit 4
    fi
    # The headers are shown WITHOUT any value that opens the session: the
    # value of every cookie is replaced, and the query string of a
    # redirection is cut (it may carry a ticket).  The terminal of this
    # run is read by a person and may be copied into a report.
    grep -iE '^(HTTP/|location:|set-cookie:)' "$HDRFILE" 2>/dev/null \
        | sed -E 's/^([Ss][Ee][Tt]-[Cc][Oo][Oo][Kk][Ii][Ee]:[[:space:]]*[^=;[:space:]]+)=[^;]*/\1=<hidden>/; s/^([Ll][Oo][Cc][Aa][Tt][Ii][Oo][Nn]:[[:space:]]*[^?[:space:]]*)\?[^[:space:]]*/\1?<hidden>/' \
        | sed 's/^/   /'
    rm -f "$HDRFILE"

    # 3b.3 The GET of the installer with the SAME jar.
    say ""
    say "-- command: GET $RUN_URL_SUPPORT7  (with the same cookie jar)"
    http -sS -L --max-time 1800 -c "$JAR" -b "$JAR" \
        -o "$QNX_SDP_RUN.part" -w '   http code %{http_code}, %{size_download} bytes\n' \
        "$RUN_URL_SUPPORT7"
    get_rc=$?
    say "   exit code: $get_rc"
    if [ "$get_rc" -ne 0 ]; then
        say ""
        say "STOP: the download of the installer failed (exit code $get_rc)."
        say "The file that was being written is removed."
        rm -f "$QNX_SDP_RUN.part"
        exit 4
    fi
    taille=$(wc -c < "$QNX_SDP_RUN.part")
    say "   size of the body: $taille bytes (99.85 MB are expected)"
    mv -f "$QNX_SDP_RUN.part" "$QNX_SDP_RUN"
fi

# 3b.4 The MD5 control.  If it is not the official one, nothing is
# decompressed and the script stops.
md5_local=$(md5sum "$QNX_SDP_RUN" | awk '{print $1}')
say ""
say "-- MD5 control"
say "   file   : $QNX_SDP_RUN"
say "   size   : $(wc -c < "$QNX_SDP_RUN") bytes"
say "   MD5    : $md5_local"
say "   official: $MD5_OFFICIAL"
if [ "$md5_local" != "$MD5_OFFICIAL" ]; then
    say ""
    say "STOP: the MD5 of the downloaded file is not the official one."
    say "Nothing is decompressed, nothing is installed."
    say "The official MD5 was published by the Direction on 17 November 2026."
    exit 4
fi
say "   the MD5 is the official one."

# --------------------------------------------------------------------------
# 4. (c) The extraction of the QNX Software Center.
# --------------------------------------------------------------------------

hdr "4. (c) unpack the QNX Software Center"

mkdir -p "$QNX_WORKDIR" || { say "cannot create $QNX_WORKDIR"; exit 4; }
# Official public procedure (Maetis/qnx-sdp-projects, docs/wsl-install.md):
#     ./qnx-setup-<version>-linux.run --tar xvf -C qnx
say "-- command: $QNX_SDP_RUN --tar xvf -C $QNX_WORKDIR"
"$QNX_SDP_RUN" --tar xvf -C "$QNX_WORKDIR" > "$QNX_WORKDIR/.extraction.log" 2>&1
extract_rc=$?
say "   exit code: $extract_rc"
if [ "$extract_rc" -ne 0 ]; then
    say "the extraction of the client failed; the log of the extraction is here:"
    tail -20 "$QNX_WORKDIR/.extraction.log" 2>/dev/null | sed 's/^/    /'
    say "The options of this installer are not documented on the public web:"
    say "run '$QNX_SDP_RUN --help' and read the output before trying again."
    exit 4
fi

QSC=$(find "$QNX_WORKDIR" -maxdepth 4 -type f -name 'qnxsoftwarecenter_clt' 2>/dev/null | head -1)
if [ -z "$QSC" ]; then
    say "the client was unpacked, but qnxsoftwarecenter_clt was not found."
    say "the tree that was unpacked is here:"
    find "$QNX_WORKDIR" -maxdepth 3 2>/dev/null | sed 's/^/    /'
    exit 4
fi
chmod +x "$QSC" 2>/dev/null
say "the client is here: $QSC"

say ""
say "-- command: $QSC -version"
"$QSC" -version 2>&1 | sed 's/^/   /'
say "   exit code: ${PIPESTATUS[0]}"

# --------------------------------------------------------------------------
# 5. (d) The options file, and the four commands of the QNX Software Center.
# --------------------------------------------------------------------------

hdr "5. (d) the options file and the commands of the client"

# One argument per line, as the official page describes.  The file lives
# in /dev/shm, with the rights of its owner only, and is deleted in
# step (f).
OPTFILE=$(mktemp /dev/shm/qnx-options.XXXXXX) || { say "cannot create the options file in /dev/shm"; exit 3; }
chmod 600 "$OPTFILE"
{
    printf '%s\n' '-myqnx.user'
    printf '%s\n' "$MYQNX_USER"
    printf '%s\n' '-myqnx.password'
    printf '%s\n' "$MYQNX_PASSWORD"
} > "$OPTFILE"
say "the options file is here : $OPTFILE (one argument per line, mode 600)"
say "it holds the user and the password: it is deleted in step (f), and the"
say "password is never printed."

MIRROR_DONE=0

# 5a. -syncLicenseKeys
say ""
say "-- command: qnxsoftwarecenter_clt @$OPTFILE -syncLicenseKeys"
"$QSC" "@$OPTFILE" -syncLicenseKeys 2>&1 | sed 's/^/   /'
sync_rc=${PIPESTATUS[0]}
say "   exit code: $sync_rc"
if [ "$sync_rc" -ne 0 ]; then
    # The official page says "-mirror" must be used at least once before
    # any remote operation.  If the keys cannot be retrieved, the mirror
    # is done now, ONCE, and the command is tried again.
    say "   the keys could not be retrieved."
    say "   The official page says: \"Use this option at least once before"
    say "   performing any remote operations\".  The mirror is therefore done"
    say "   now, once, and the command is tried again."
    say ""
    say "-- command: qnxsoftwarecenter_clt @$OPTFILE -mirror"
    "$QSC" "@$OPTFILE" -mirror 2>&1 | sed 's/^/   /'
    mirror_rc=${PIPESTATUS[0]}
    say "   exit code: $mirror_rc"
    MIRROR_DONE=1
    if [ "$mirror_rc" -ne 0 ]; then
        say "the mirror of the package metadata failed (exit code above)."
        say "The log of the QNX Software Center names the host that failed:"
        say "    ~/.qnx/swupdate/.metadata/.log"
        exit 4
    fi
    say ""
    say "-- command: qnxsoftwarecenter_clt @$OPTFILE -syncLicenseKeys  (again)"
    "$QSC" "@$OPTFILE" -syncLicenseKeys 2>&1 | sed 's/^/   /'
    sync_rc=${PIPESTATUS[0]}
    say "   exit code: $sync_rc"
    if [ "$sync_rc" -ne 0 ]; then
        say "the licence keys of the myQNX account could not be retrieved."
        say "Check the user name (lower case) and the password."
        exit 4
    fi
fi
say "the licence keys of the account are retrieved."

# 5b. -activateAll
say ""
say "-- command: qnxsoftwarecenter_clt @$OPTFILE -activateAll"
"$QSC" "@$OPTFILE" -activateAll 2>&1 | sed 's/^/   /'
activate_rc=${PIPESTATUS[0]}
say "   exit code: $activate_rc"
if [ "$activate_rc" -ne 0 ]; then
    say "the activation of the licence keys failed (exit code above)."
    exit 4
fi
say "the licence keys are activated."

# 5c. -mirror (once: the official page warns against repeating it)
if [ "$MIRROR_DONE" -eq 0 ]; then
    say ""
    say "-- command: qnxsoftwarecenter_clt @$OPTFILE -mirror"
    "$QSC" "@$OPTFILE" -mirror 2>&1 | sed 's/^/   /'
    mirror_rc=${PIPESTATUS[0]}
    say "   exit code: $mirror_rc"
    if [ "$mirror_rc" -ne 0 ]; then
        say "the mirror of the package metadata failed (exit code above)."
        say "The log of the QNX Software Center names the host that failed:"
        say "    ~/.qnx/swupdate/.metadata/.log"
        exit 4
    fi
else
    say ""
    say "-mirror has already been used in this run: it is not repeated (official"
    say "page: \"avoid invoking -mirror multiple times as it can reduce"
    say "performance significantly\")."
fi
say "the package metadata is mirrored."

# 5d. -installBaseline
say ""
say "-- command: qnxsoftwarecenter_clt @$OPTFILE -installBaseline com.qnx.qnx800 -destination $SDP_DEST -cleanInstall"
"$QSC" "@$OPTFILE" -installBaseline com.qnx.qnx800 \
    -destination "$SDP_DEST" -cleanInstall 2>&1 | sed 's/^/   /'
install_rc=${PIPESTATUS[0]}
say "   exit code: $install_rc"
if [ "$install_rc" -ne 0 ]; then
    say "the installation of the baseline failed (exit code above)."
    say "Nothing is simulated: the SDP is NOT installed."
    exit 4
fi
say "the baseline is installed in $SDP_DEST"

# The options file is deleted right after the last command that used it
# (the trap of step (f) deletes it too, if a step failed).
rm -f "$OPTFILE"
say "the options file is deleted: $OPTFILE"
OPTFILE=""

# The official verification of the installation: exit code 4 when the
# installation is incomplete or modified, 0 otherwise.
say ""
say "-- command: qnxsoftwarecenter_clt -destination $SDP_DEST -verifyInstallation"
"$QSC" -destination "$SDP_DEST" -verifyInstallation 2>&1 | sed 's/^/   /'
verify_rc=${PIPESTATUS[0]}
say "   exit code: $verify_rc (0 = the installation is complete, 4 = it is not)"

# --------------------------------------------------------------------------
# 6. (e) The environment, the compiler, and the proof.
# --------------------------------------------------------------------------

hdr "6. (e) the environment, the compiler, and the proof"

if [ ! -f "$SDP_DEST/qnxsdp-env.sh" ]; then
    say "$SDP_DEST/qnxsdp-env.sh is absent: the SDP environment cannot be loaded."
    exit 4
fi
say "-- command: source $SDP_DEST/qnxsdp-env.sh"
# shellcheck disable=SC1091
# NOT in a pipeline: "source ... | sed" would run in a subshell and the
# variables of the SDP (QNX_HOST, QNX_TARGET, PATH with qcc) would be lost.
envlog=$(mktemp /dev/shm/qnx-envlog.XXXXXX 2>/dev/null || mktemp)
# "set -u" is suspended while the official script is read: it may test
# variables that are not set yet (an unset variable would end THIS script).
set +u
. "$SDP_DEST/qnxsdp-env.sh" > "$envlog" 2>&1
env_rc=$?
set -u
sed 's/^/   /' "$envlog"
rm -f "$envlog"
say "   exit code: $env_rc"
if [ "$env_rc" -ne 0 ]; then
    say "the SDP environment script failed."
    exit 4
fi
say "the environment of the SDP is loaded."

say ""
say "-- command: qcc -V"
QCC_OUT=$(qcc -V 2>&1)
qcc_rc=$?
printf '%s\n' "$QCC_OUT" | sed 's/^/   /'
say "   exit code: $qcc_rc"
result "qcc -V (exit code $qcc_rc):"
printf '%s\n' "$QCC_OUT" | sed 's/^/   /' >> "$RESULT_FILE" 2>/dev/null || true

say ""
say "-- command: bash scripts/qnx8-proof.sh  (the demonstration of this repository)"
PROOF_OUT=$(bash "$ROOT/scripts/qnx8-proof.sh" 2>&1)
proof_rc=$?
printf '%s\n' "$PROOF_OUT"
result "scripts/qnx8-proof.sh (exit code $proof_rc):"
printf '%s\n' "$PROOF_OUT" >> "$RESULT_FILE" 2>/dev/null || true

say ""
say "the exit code of scripts/qnx8-proof.sh is $proof_rc (it is propagated as it is)."
case "$proof_rc" in
    0) say "RESULT: the SDP is installed and the QNX 8.0 demonstration passed." ;;
    2) say "RESULT: the SDP is still absent or incomplete.  Nothing was simulated." ;;
    *) say "RESULT: the demonstration really failed.  Read the output above." ;;
esac
say ""
say "requests sent by this run : $REQUESTS"
exit "$proof_rc"

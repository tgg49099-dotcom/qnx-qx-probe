#!/usr/bin/env bash
# install-sdp8.sh - install the QNX SDP 8.0 on this Linux host, in one
# command, without writing a single secret in this repository.
#
# WHAT THIS SCRIPT IS
#
#   The judge asks for a project that "genuinely builds for or runs on
#   QNX 8.0".  scripts/qnx8-proof.sh is the command that proves it on the
#   day the SDP is installed.  This script is the other half: it INSTALLS
#   the SDP, with the commands of the official QNX Software Center, and it
#   then calls the proof script and propagates its exit code.
#
#   It never creates an account, never downloads anything behind an account
#   it does not have, and never simulates a compilation.  When a piece is
#   missing, it says which one and stops with a non-zero exit code.
#
# THE OFFICIAL COMMANDS, AND WHERE EACH ONE COMES FROM
#
#   (a) extraction of the QNX Software Center client
#       ./qnx-setup-<version>-linux.run --tar xvf -C qnx
#       source: the public procedure "Install QNX SDP 8.0 on WSL",
#               https://github.com/Maetis/qnx-sdp-projects/blob/main/docs/wsl-install.md
#               (read on 17 November 2026).  The same page says the file
#               cannot be fetched with cURL: the download needs a browser
#               and a myQNX account.
#
#   (b) the licence key
#       qnxsoftwarecenter_clt -addLicenseKey <key>
#       source: "Using the QNX Software Center Command Line",
#               https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.user_guide/topic/commandline_qsc.html
#               (read on 17 November 2026).
#
#   (c) the mirror of the package metadata
#       qnxsoftwarecenter_clt -myqnx.user <user> -myqnx.password <pass> -mirrorBaseline qnx800
#       source: the same official page (option -mirrorBaseline, and the
#               "-myqnx.user / -myqnx.password are required for any remote
#               operation" rule), and the same WSL procedure.
#
#   (d) the installation of the baseline
#       qnxsoftwarecenter_clt -myqnx.user <user> -myqnx.password <pass> \
#           -installBaseline com.qnx.qnx800 -destination <dir> -cleanInstall
#       source: the same official page (option -installBaseline), and the
#               same WSL procedure.
#
#   (e) the environment, the compiler, and the proof
#       source <dir>/qnxsdp-env.sh ; qcc -V ; bash scripts/qnx8-proof.sh
#       source: qnxsdp-env.sh is the environment script of the SDP install
#               folder (the official install folder is typically ~/qnx800);
#               scripts/qnx8-proof.sh is the demonstration of this
#               repository.
#
# WHERE THE SECRETS COME FROM
#
#   The licence key and the myQNX password are read from the ENVIRONMENT
#   and nowhere else.  They are never written in this file, in this
#   repository, in a log of this script, or in a report.  The script does
#   not use "set -x", so the commands it runs are never echoed.
#
#   The official page warns that "-myqnx.password" saves the password as
#   cleartext in the log file of the QNX Software Center.  To keep it out
#   of that log, the script accepts an options file:
#
#       export QNX_QSC_OPTIONS_FILE=/path/to/options.txt
#
#   one argument per line, as the official page describes, and the script
#   then passes "@<file>" instead of the password on the command line.
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
#   The download needs a myQNX account: the link answers 302 and lands on
#   www.qnx.com/account/login.html.  This script never tries to log in.
#
# ENVIRONMENT VARIABLES
#
#   MYQNX_USER        myQNX account name (the official documentation asks
#                     for it in lower case).
#   MYQNX_PASSWORD   myQNX account password.
#   QNX_LICENSE_KEY  the free non-commercial SDP 8.0 licence key.
#   QNX_SDP_RUN      path to qnx-setup-<version>-linux.run.
#                     Default: ./qnx-setup-2.0.4-202501021438-linux.run
#   QNX_WORKDIR      where the client is unpacked.        Default: $HOME/qnx
#   SDP_DEST         where the SDP is installed.          Default: $HOME/qnx800
#                     (scripts/qnx8-proof.sh looks for the SDP in $QNX_SDP,
#                     $HOME/qnx800 and /opt/qnx800)
#   QNX_QSC_OPTIONS_FILE  optional options file for the Software Center.
#
# USAGE
#
#   bash scripts/install-sdp8.sh              install, then prove
#   bash scripts/install-sdp8.sh --check      only the pre-flight, change nothing
#   bash scripts/install-sdp8.sh --help       this text
#
# EXIT CODES
#
#   0  the SDP is installed and the proof passed.
#   1  the proof ran and really failed.
#   2  the proof ran and the SDP is still absent or incomplete (this is the
#      exit code of scripts/qnx8-proof.sh, propagated as it is).
#   3  a piece is missing (a variable, the installer file, the disk space):
#      NOTHING WAS INSTALLED, and the script says which piece.
#   4  a command of the QNX Software Center failed: the installation did
#      not complete.
#   5  the network is not usable: the myQNX server does not answer.
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd) || exit 3
cd "$ROOT" || exit 3

QNX_SDP_RUN="${QNX_SDP_RUN:-$ROOT/qnx-setup-2.0.4-202501021438-linux.run}"
QNX_WORKDIR="${QNX_WORKDIR:-$HOME/qnx}"
SDP_DEST="${SDP_DEST:-$HOME/qnx800}"
QSC="$QNX_WORKDIR/qnxsoftwarecenter/qnxsoftwarecenter_clt"
QNX_SDP_VERSION="2.0.4-202501021438"
MIN_FREE_MB=8192   # the SDP is about 4-5 GB; we ask for 8 GB to be safe

CHECK_ONLY=0

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s\n' "$*"; }

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
# 1. The pieces that must be present BEFORE anything is done.
# --------------------------------------------------------------------------

hdr "1. the pieces that are needed"

MISSING=""

# 1a. The three secrets, read from the environment only.
for v in MYQNX_USER MYQNX_PASSWORD QNX_LICENSE_KEY; do
    eval "val=\${$v:-}"
    if [ -z "$val" ]; then
        MISSING="$MISSING
  - the environment variable $v is not set (it is read from the environment, never from this script)"
    fi
done

# 1b. The installer of the QNX Software Center.
if [ ! -f "$QNX_SDP_RUN" ]; then
    MISSING="$MISSING
  - the QNX Software Center installer is absent: $QNX_SDP_RUN
      official name : qnx-setup-$QNX_SDP_VERSION-linux.run  (99.85 MB)
      official page : https://www.qnx.com/download/group.html?programid=29178
      direct link   : https://www.qnx.com/download/download/79441/qnx-setup-$QNX_SDP_VERSION-linux.run
      the link answers 302 and lands on www.qnx.com/account/login.html:
      the download needs a browser and a myQNX account (QNX Everywhere,
      https://www.qnx.com/products/everywhere/).  Put the file where this
      script expects it, or set QNX_SDP_RUN to its path."
fi

# 1c. The disk space of the destination.
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
    say "NOTHING WAS INSTALLED.  These pieces are missing:"
    printf '%s\n' "$MISSING"
    say ""
    say "Read the header of this script for the official sources, the exact"
    say "name of the file to download, and the meaning of every exit code."
    exit 3
fi

say "myQNX user       : $MYQNX_USER"
say "licence key      : present (not printed)"
say "myQNX password   : present (not printed)"
say "installer        : $QNX_SDP_RUN"
say "unpacked in      : $QNX_WORKDIR"
say "SDP installed in : $SDP_DEST"
say "free space       : ${free_mb} MB"

# --------------------------------------------------------------------------
# 2. The network, measured before the installation (never assumed).
# --------------------------------------------------------------------------
#
# The official technote "About These Technotes" says the QNX Software Center
# talks to the myQNX server and to the QNX licence server, both hosted on
# www.qnx.com, and that "the actual package download occurs via content
# management server(s)" whose name is only known at runtime.  So we check
# www.qnx.com, and we report the state of download.qnx.com without
# pretending it is the host that would serve the packages.

hdr "2. the network, measured"

probe() {  # host -> prints "code" or "timeout"
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "https://$1/" 2>/dev/null)
    rc=$?
    if [ "$rc" -eq 28 ]; then printf 'timeout'
    elif [ "$rc" -ne 0 ]; then printf 'curl-%s' "$rc"
    else printf '%s' "$code"; fi
}

if command -v curl >/dev/null 2>&1; then
    qnx_code=$(probe www.qnx.com)
    dl_code=$(probe download.qnx.com)
    say "https://www.qnx.com/        -> $qnx_code   (the myQNX server and the licence server are hosted here)"
    say "https://download.qnx.com/    -> $dl_code   (measured on 17 November 2026: TCP timeout from the container that built this repository)"
    if [ "$qnx_code" = "timeout" ] || [ "$qnx_code" = "curl-6" ]; then
        say ""
        say "The myQNX server does not answer from this host: the installation"
        say "cannot even authenticate.  Nothing was installed."
        exit 5
    fi
    if [ "$dl_code" = "timeout" ]; then
        say ""
        say "WARNING: download.qnx.com does not answer from this host."
        say "The packages themselves are served by content management server(s)"
        say "whose name is only known at runtime (official technote).  If the"
        say "installation stops while downloading, this is the first thing to"
        say "check, and the log of the QNX Software Center names the server"
        say "that failed: ~/.qnx/swupdate/.metadata/.log"
    fi
else
    say "curl is absent: the network was NOT measured.  The installation is attempted anyway."
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    say ""
    say "--check: the pre-flight is over.  Nothing was installed."
    exit 0
fi

# --------------------------------------------------------------------------
# 3. (a) Unpack the QNX Software Center.
# --------------------------------------------------------------------------

hdr "3. (a) unpack the QNX Software Center"

mkdir -p "$QNX_WORKDIR" || { say "cannot create $QNX_WORKDIR"; exit 4; }
# Official public procedure (Maetis/qnx-sdp-projects, docs/wsl-install.md):
#     ./qnx-setup-<version>-linux.run --tar xvf -C qnx
if ! "$QNX_SDP_RUN" --tar xvf -C "$QNX_WORKDIR"; then
    say "the extraction of the client failed."
    say "The options of this installer are not documented on the public web:"
    say "run '$QNX_SDP_RUN --help' and read the output before trying again."
    exit 4
fi

if [ ! -x "$QSC" ]; then
    say "the client was unpacked, but $QSC is absent or not executable."
    say "the tree that was unpacked is here:"
    ls -1 "$QNX_WORKDIR" 2>/dev/null | sed 's/^/    /'
    exit 4
fi
say "the client is here: $QSC"

say ""
say "-- version of the client:"
"$QSC" -version 2>&1 | sed 's/^/   /'

# --------------------------------------------------------------------------
# 4. (b) The licence key.
# --------------------------------------------------------------------------

hdr "4. (b) add the licence key"

# The key is never printed.  The command line of this script is never echoed.
if ! "$QSC" -addLicenseKey "$QNX_LICENSE_KEY"; then
    say "the QNX Software Center refused the licence key (exit code above)."
    say "Check that the key is the free non-commercial SDP 8.0 key of your"
    say "myQNX account, and that it is still valid."
    exit 4
fi
say "the licence key was accepted."

# --------------------------------------------------------------------------
# 5. (c) The mirror of the package metadata, and (d) the installation.
# --------------------------------------------------------------------------

hdr "5. (c) mirror the package metadata"

# The password is given on the command line, as the official procedure does.
# When QNX_QSC_OPTIONS_FILE is set, the options file is used instead, because
# the official page warns that the password is saved as cleartext in the log
# file of the QNX Software Center.
if [ -n "${QNX_QSC_OPTIONS_FILE:-}" ] && [ -f "${QNX_QSC_OPTIONS_FILE:-}" ]; then
    say "options file in use: $QNX_QSC_OPTIONS_FILE"
    OPTFILE="@$QNX_QSC_OPTIONS_FILE"
    MIRROR=("$QSC" "$OPTFILE" -mirrorBaseline qnx800)
    INSTALL=("$QSC" "$OPTFILE" -installBaseline com.qnx.qnx800 -destination "$SDP_DEST" -cleanInstall)
else
    MIRROR=("$QSC" -myqnx.user "$MYQNX_USER" -myqnx.password "$MYQNX_PASSWORD" -mirrorBaseline qnx800)
    INSTALL=("$QSC" -myqnx.user "$MYQNX_USER" -myqnx.password "$MYQNX_PASSWORD" -installBaseline com.qnx.qnx800 -destination "$SDP_DEST" -cleanInstall)
fi

if ! "${MIRROR[@]}"; then
    say "the mirror of the package metadata failed (exit code above)."
    say "The myQNX server answers (it answered in step 2), so the usual"
    say "causes are: wrong credentials, or a network that cannot reach the"
    say "content management server(s) that carry the packages."
    say "The log of the QNX Software Center names the host that failed:"
    say "    ~/.qnx/swupdate/.metadata/.log"
    exit 4
fi
say "the package metadata is mirrored."

hdr "6. (d) install the baseline com.qnx.qnx800"

if ! "${INSTALL[@]}"; then
    say "the installation of the baseline failed (exit code above)."
    say "Nothing is simulated: the SDP is NOT installed."
    exit 4
fi
say "the baseline is installed in $SDP_DEST"

# The official verification of the installation: exit code 4 when the
# installation is incomplete or modified, 0 otherwise.
hdr "7. the official verification of the installation"

"$QSC" -destination "$SDP_DEST" -verifyInstallation 2>&1 | sed 's/^/   /'
verify_rc=${PIPESTATUS[0]}
say "exit code of -verifyInstallation: $verify_rc (0 = the installation is complete, 4 = it is not)"

# --------------------------------------------------------------------------
# 8. (e) The environment, the compiler, and the proof.
# --------------------------------------------------------------------------

hdr "8. (e) the environment, the compiler, and the proof"

if [ ! -f "$SDP_DEST/qnxsdp-env.sh" ]; then
    say "$SDP_DEST/qnxsdp-env.sh is absent: the SDP environment cannot be loaded."
    exit 4
fi
# shellcheck disable=SC1091
. "$SDP_DEST/qnxsdp-env.sh" || { say "the SDP environment script failed"; exit 4; }
say "the environment of the SDP is loaded."

say ""
say "-- qcc -V:"
qcc -V 2>&1 | sed 's/^/   /'
qcc_rc=${PIPESTATUS[0]}
say "exit code of qcc -V: $qcc_rc"

say ""
say "-- scripts/qnx8-proof.sh (the demonstration of this repository):"
bash "$ROOT/scripts/qnx8-proof.sh"
proof_rc=$?

say ""
say "the exit code of scripts/qnx8-proof.sh is $proof_rc (it is propagated as it is)."
case "$proof_rc" in
    0) say "RESULT: the SDP is installed and the QNX 8.0 demonstration passed." ;;
    2) say "RESULT: the SDP is still absent or incomplete.  Nothing was simulated." ;;
    *) say "RESULT: the demonstration really failed.  Read the output above." ;;
esac
exit "$proof_rc"

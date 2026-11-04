#!/usr/bin/env bash
# Compile les exemples de QX-PROBE pour QNX 8.0 avec qcc (SDP 8.0).
#
# Ce script N'EST PAS encore executable : il exige le SDP 8.0 (licence
# QNX Everywhere non commerciale, compte myQNX).  Il est ecrit et teste pour
# etre lance le jour ou la licence existe.
#
# Regle absolue : si qcc est absent, le script s'arrete en erreur et n'invente
# AUCUNE sortie de compilateur.  Il ne produit pas de binaire factice.
#
# Usage :  bash scripts/build_qcc.sh [cible]
#   cible = x86_64 (defaut) | aarch64 | armv7
set -u
cd "$(dirname "$0")/.." || exit 2

TARGET="${1:-x86_64}"
OUT="build"

case "$TARGET" in
  x86_64) QCC_TARGET="x86_64" ;;
  aarch64) QCC_TARGET="aarch64" ;;
  armv7)  QCC_TARGET="armv7" ;;
  *) echo "Cible inconnue : $TARGET (attendu : x86_64, aarch64, armv7)"; exit 2 ;;
esac

# --- Le SDK est-il present ? -------------------------------------------------
if ! command -v qcc >/dev/null 2>&1; then
  cat >&2 <<EOF
ERREUR : qcc est introuvable.

Ce script compile pour QNX 8.0 avec le SDP 8.0 (host tools).  Sans le SDP 8.0
et une licence QNX Everywhere non commerciale (compte myQNX), la compilation
est impossible.

Ce qui manque, et que ce script ne peut pas simuler :
  - qcc (le compilateur C de QNX, fourni par le SDP 8.0)
  - les bibliotheques systeme QNX 8.0 (libc, libsys, ...)

Aucune sortie de compilateur n'est simulee : en l'absence de qcc, ce script
s'arrete ici, avec le code de sortie 2.
EOF
  exit 2
fi

echo "qcc : $(command -v qcc)"
qcc -V 2>&1 | head -3
echo

mkdir -p "$OUT"
rc_global=0

build_one() {
  src="$1"; name="$2"
  echo "--- $src -> $OUT/$name ---"
  # -V : bibliotheques QNX natives ; -Werror : pas d'avertissement tolere.
  qcc -Vgcc_ntoaosdebug -Werror -o "$OUT/$name" "$src"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "ECHEC de compilation : $src (RC $rc)"
    rc_global=1
  else
    echo "OK : $OUT/$name ($(wc -c < "$OUT/$name") octets)"
  fi
  echo
}

build_one examples/qnx80_resmgr_minimal.c qxprobe-demo
build_one examples/qnx80_resmgr_readonly.c qxprobe-status

if [ "$rc_global" -eq 0 ]; then
  echo "BUILD OK pour la cible $QCC_TARGET"
else
  echo "BUILD KO"
fi
exit "$rc_global"

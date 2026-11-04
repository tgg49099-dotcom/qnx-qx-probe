#!/usr/bin/env bash
# Lance la suite de tests de QX-PROBE (hote, sans SDK QNX).
# Sortie : 0 = tous les tests passent, non nul = echec.
set -u
cd "$(dirname "$0")/.." || exit 2
# Ne jamais laisser d'artefact Python (__pycache__) dans le depot.
# -B (et non PYTHONDONTWRITEBYTECODE) car -I ignore les variables PYTHON*.

echo "=============================================================="
echo "QX-PROBE — suite de tests"
echo "=============================================================="
echo
echo "--- 1. le code de reference publie par BlackBerry doit passer sans erreur ni avertissement ---"
for f in examples/blackberry_eventfd_mgr.c examples/qnx80_resmgr_minimal.c \
         examples/qnx80_resmgr_readonly.c; do
  out=$(python3 -I -B qx_probe.py "$f")
  rc=$?
  echo "  $(printf '%-42s' "$f") RC=$rc  $(echo "$out" | tail -1)"
  if [ "$rc" -ne 0 ]; then
    echo "    ECHEC : un constat actionnable est produit sur du code valide"
    echo "$out"
    exit 1
  fi
done
echo
echo "--- 2. le cas du chemin relatif doit produire exactement un WARN ---"
out=$(python3 -I -B qx_probe.py examples/qnx80_resmgr_relative_path.c)
rc=$?
n=$(echo "$out" | grep -c '^WARN')
echo "  exemples/qnx80_resmgr_relative_path.c : RC=$rc, $n WARN"
if [ "$rc" -ne 1 ] || [ "$n" -ne 1 ]; then
  echo "    ECHEC : un seul WARN QX005 etait attendu"
  echo "$out"
  exit 1
fi
echo
echo "--- 3. suite unitaire ---"
python3 -I -B tests/test_qx_probe.py
rc=$?
echo
if [ "$rc" -eq 0 ]; then
  echo "RESULTAT : suite QX-PROBE VERTE (RC 0)"
else
  echo "RESULTAT : suite QX-PROBE ROUGE (RC $rc)"
fi
exit "$rc"

#!/usr/bin/env python3
"""Suite de tests de QX-PROBE (hote, sans SDK QNX).

Les tests ne se contentent pas de verifier que la sonde "trouve quelque chose" :
ils verrouillent les DEUX sens du contrat.

  * les cas VALIDES ne doivent declencher AUCUN constat actionnable
    (ERROR ou WARN) — c'est la exigence principale : zero faux positif sur du
    code QNX 8.0 canonique ;
  * les cas FAUVES doivent declencher le constat attendu — une regle qu'on a
    simplement supprimee ne prouve rien.

Chaque test cite la page officielle QNX SDP 8.0 qui fonde la regle verifiee.

Execution :  python3 -I tests/test_qx_probe.py
"""

import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import qx_probe  # noqa: E402

EXAMPLES = REPO / "examples"


def read(name):
    return (EXAMPLES / name).read_text(encoding="utf-8")


def findings(name):
    return qx_probe.analyse(name, read(name))


def actionable(found):
    return [f for f in found if f.level in ("ERROR", "WARN")]


def codes(found, level=None):
    """Codes des constats, filtres par niveau (ERROR / WARN / INFO)."""
    return sorted(f.code for f in found if level is None or f.level == level)


def codes_of(found, code):
    """Codes des constats portant un code de regle donne (QX005, QX008, ...)."""
    return sorted(f.code for f in found if f.code == code)


class TestNoFalsePositive(unittest.TestCase):
    """Du code QNX 8.0 VALIDE ne doit declencher aucun constat actionnable."""

    def test_exemple_canonique_minimal(self):
        """Resource manager canonique : 0 ERROR, 0 WARN."""
        found = findings("qnx80_resmgr_minimal.c")
        self.assertEqual(actionable(found), [],
                         msg=f"faux positif sur du code valide : {actionable(found)}")

    def test_exemple_lecture_seule_hors_dev(self):
        """Read-only + point de montage hors /dev/ : c'etait le faux positif historique.

        Sources : resmgr_attach() (le chemin va dans l'espace de noms general)
                  et resmgr_io_funcs_t (defauts POSIX pour chaque slot).
        """
        found = findings("qnx80_resmgr_readonly.c")
        self.assertEqual(actionable(found), [],
                         msg=f"faux positif sur du code valide : {actionable(found)}")
        self.assertEqual(codes_of(found, "QX008"), ["QX008"] * 4,
                         msg="les slots non cables doivent rester des constats INFO")

    def test_exemple_blackberry_reference(self):
        """Le resource manager public de BlackBerry (QNX 8.0) doit passer sans constat.

        C'est le test le plus important : c'est du code de reference publie
        par l'editeur de QNX 8.0.  Un outil qui le signale est disqualifie.
        """
        found = findings("blackberry_eventfd_mgr.c")
        self.assertEqual(actionable(found), [],
                         msg=f"faux positif sur le code de reference BlackBerry : {actionable(found)}")

    def test_api_resmgr_block_et_resmgr_handler(self):
        """resmgr_block()/resmgr_handler() sont l'idiome canonique de la doc QNX 8.0.

        Sources : resmgr_block() ("This function is a special case of
        dispatch_block()"), resmgr_handler() ("This function is a special
        case of dispatch_handler()").
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("dispatch_block(ctp)", "resmgr_block(ctp)")
        src = src.replace("dispatch_handler(ctp)", "resmgr_handler(ctp)")
        found = qx_probe.analyse("resmgr_block.c", src)
        self.assertEqual(actionable(found), [],
                         msg=f"faux positif sur l'idiome resmgr_block/resmgr_handler : {actionable(found)}")


class TestDetection(unittest.TestCase):
    """Les regles doivent mordre : un constat attendu, par sabotage."""

    def _mutate(self, name, old, new):
        src = read(name)
        self.assertIn(old, src, msg=f"ancre introuvable dans {name}")
        return src.replace(old, new, 1)

    def test_qx005_chemin_relatif(self):
        """QX005 : un chemin relatif est signale (WARN), un chemin absolu hors /dev/ ne l'est pas."""
        found = findings("qnx80_resmgr_relative_path.c")
        self.assertEqual(codes_of(found, "QX005"), ["QX005"])
        self.assertEqual(codes(found, "WARN"), ["QX005"])

    def test_qx003_handler_non_defini(self):
        """QX003 : io_funcs.read doit pointer sur une fonction definie dans le fichier."""
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "io_funcs.read  = qx_read;", "io_funcs.read  = qx_read_absent;")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX003", codes(found, "ERROR"))

    def test_qx004_porte_acces_absente(self):
        """QX004 : un handler de lecture doit appeler iofunc_read_verify()."""
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)\n        return status;",
                           "/* SABOTAGE : porte d'acces retiree */")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX004", codes(found, "ERROR"))

    def test_qx006_boucle_de_messages_absente(self):
        """QX006 : sans dispatch_block()/resmgr_block(), le resmgr n'attend jamais de message."""
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "if ((ctp = dispatch_block(ctp)) == NULL) {",
                           "if ((ctp = ctp) == NULL) {")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX006", codes(found, "ERROR"))

    def test_qx007_dispatch_absent(self):
        """QX007 : bloquer sans distribuer le message laisse le client bloque."""
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "dispatch_handler(ctp);", "/* SABOTAGE : message jamais distribue */")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX007", codes(found, "ERROR"))

    def test_qx009_parts_superieures_a_nparts_max(self):
        """QX009 : on ne renvoie pas plus de parties que l'IOV declare (nparts_max).

        Sources : resmgr_attach() (nparts_max = nombre de composantes de l'IOV),
                  _RESMGR_NPARTS() (nparts_max doit etre la valeur maximale de num).
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "return _RESMGR_NPARTS(1);", "return _RESMGR_NPARTS(2);")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX009", codes(found, "ERROR"))

    def test_qx009_parts_conformes(self):
        """QX009 ne doit PAS se declencher quand le nombre de parties tient dans l'IOV."""
        found = findings("qnx80_resmgr_minimal.c")
        self.assertNotIn("QX009", codes(found))


if __name__ == "__main__":
    unittest.main(verbosity=2)

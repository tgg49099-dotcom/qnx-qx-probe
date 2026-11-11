#!/usr/bin/env python3
"""Test suite of QX-PROBE (host side, no QNX SDK required).

The tests do not only check that the checker "finds something": they lock
BOTH sides of the contract.

  * VALID cases must trigger NO actionable finding (ERROR or WARN) — this is
    the main requirement: zero false positive on canonical QNX 8.0 code;
  * BROKEN cases must trigger the expected finding — a rule that was simply
    deleted proves nothing.

Every test cites the official QNX SDP 8.0 page that grounds the rule it
checks.

Run:  python3 -I tests/test_qx_probe.py
"""

import contextlib
import io
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
    """The codes of the findings, filtered by level (ERROR / WARN / INFO)."""
    return sorted(f.code for f in found if level is None or f.level == level)


def codes_of(found, code):
    """The codes of the findings carrying a given rule code (QX005, QX008...)."""
    return sorted(f.code for f in found if f.code == code)


def mutate(name, old, new):
    """Replaces `old` by `new` in the example `name` (once)."""
    src = read(name)
    if old not in src:
        raise AssertionError(f"anchor not found in {name}: {old!r}")
    return src.replace(old, new, 1)


class TestNoFalsePositive(unittest.TestCase):
    """Valid QNX 8.0 code must trigger no actionable finding."""

    def test_exemple_canonique_minimal(self):
        """Canonical resource manager: 0 ERROR, 0 WARN."""
        found = findings("qnx80_resmgr_minimal.c")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

    def test_exemple_lecture_seule_hors_dev(self):
        """Read-only + mount point outside /dev/: this was the historical false
        positive.

        Sources: resmgr_attach() (the path goes into the general pathname
                 space) and resmgr_io_funcs_t (POSIX default for each slot).
        """
        found = findings("qnx80_resmgr_readonly.c")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")
        self.assertEqual(codes_of(found, "QX008"), ["QX008"] * 4,
                         msg="the unwired slots must remain INFO findings")

    def test_exemple_blackberry_reference(self):
        """BlackBerry's public resource manager (QNX 8.0) must pass without a
        single finding.

        This is the most important test: it is reference code published by
        the QNX 8.0 editor itself. A tool that reports it is disqualified.
        """
        found = findings("blackberry_eventfd_mgr.c")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on BlackBerry's reference code: {actionable(found)}")

    def test_api_resmgr_block_et_resmgr_handler(self):
        """resmgr_block()/resmgr_handler() are the canonical idiom of the
        QNX 8.0 documentation.

        Sources: resmgr_block() ("This function is a special case of
        dispatch_block()"), resmgr_handler() ("This function is a special
        case of dispatch_handler()").

        The same test covers the DELEGATED loop: a thread pool takes the
        blocking function as a pointer (pool_attr.block_func =
        &resmgr_block), so the function is referenced, not called.  The rule
        used to look for a call only, and to report "no message loop" on a
        file that does have one.
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("dispatch_block(ctp)", "resmgr_block(ctp)")
        src = src.replace("dispatch_handler(ctp)", "resmgr_handler(ctp)")
        found = qx_probe.analyse("resmgr_block.c", src)
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on the resmgr_block/resmgr_handler idiom: {actionable(found)}")

        delegated = """
#include <sys/iofunc.h>
#include <sys/resmgr.h>
#include <sys/dispatch.h>

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t      io_funcs;

int start(dispatch_t *dpp)
{
    thread_pool_attr_t pool_attr;
    pool_attr.block_func   = &resmgr_block;
    pool_attr.handler_func = (void *)dispatch_handler;
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    return 0;
}
"""
        found = qx_probe.analyse("delegated_loop.c", delegated)
        self.assertNotIn("QX006", codes(found),
                         msg="false positive: the loop is delegated to a thread pool")
        self.assertNotIn("QX007", codes(found),
                         msg="false positive: the handler is delegated too")

    # ------------------------------------------------------------------
    # QX001 — the dispatch table
    # ------------------------------------------------------------------

    def test_qx001_exemple_officiel_de_la_documentation(self):
        """The official example of iofunc_func_init() must not be reported.

        Sources: iofunc_func_init() ("my_io_functions.io_read = my_io_read;"),
                 resmgr_io_funcs_t() (the table and its members).

        The table is called "my_io_functions" and the member is written
        "io_read": neither was recognised by the checker, which concluded
        "no dispatch table is assigned" on the code of the documentation.
        """
        found = findings("qnx80_resmgr_official_example.c")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on the official example of the documentation: {actionable(found)}")

    def test_qx001_initialiseur_de_structure_c99(self):
        """A C99 initialiser (resmgr_io_funcs_t f = { .read = … }) wires the
        table.

        Sources: resmgr_io_funcs_t() ("You can initialize this table by
        calling iofunc_func_init() and then overriding the defaults with
        your own functions"), resmgr_attach() (io_funcs argument).
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("static resmgr_io_funcs_t io_funcs;\n", "")
        src = src.replace("    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,\n"
                          "                     _RESMGR_IO_NFUNCS, &io_funcs);\n", "")
        src = src.replace("    io_funcs.read  = qx_read;\n    io_funcs.write = qx_write;\n", "")
        src = src.replace("int main(void)\n{",
                          "static resmgr_io_funcs_t io_funcs = {\n"
                          "    .read  = qx_read,\n"
                          "    .write = qx_write,\n"
                          "};\n\n"
                          "int main(void)\n{")
        found = qx_probe.analyse("c99.c", src)
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on a C99 initialiser: {actionable(found)}")
        unwired = [f.message for f in found if f.code == "QX008"]
        self.assertFalse([m for m in unwired if ".read is not assigned" in m
                          or ".write is not assigned" in m],
                         msg="the slots of the C99 initialiser are not unwired slots")

    # ------------------------------------------------------------------
    # QX002 — the number of entries to fill
    # ------------------------------------------------------------------

    def test_qx002_slots_cables_au_dela_des_entrees_remplies(self):
        """QX002: wiring more slots than the number of entries filled is
        LEGITIMATE: the official example of iofunc_func_init() overrides the
        defaults AFTER the filling.

        Sources: iofunc_func_init() ("The nconnect and nio arguments indicate
        how many entries this function should fill"), iofunc_func_init()
        page (official example: filling then overriding).
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("_RESMGR_IO_NFUNCS, &io_funcs);", "2, &io_funcs);")
        src = src.replace("    io_funcs.write = qx_write;\n",
                          "    io_funcs.write = qx_write;\n"
                          "    io_funcs.devctl = qx_devctl;\n")
        src = src.replace("int main(void)\n{",
                          "static int qx_devctl(resmgr_context_t *ctp, io_devctl_t *msg,\n"
                          "                       RESMGR_OCB_T *ocb)\n"
                          "{\n"
                          "    return EOK;\n"
                          "}\n\n"
                          "int main(void)\n{")
        found = qx_probe.analyse("few_entries.c", src)
        self.assertNotIn("QX002", codes(found),
                         msg="false positive: the number of wired slots is not an "
                             "overflow of the number of filled entries")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

    # ------------------------------------------------------------------
    # QX003 — does the handler exist?
    # ------------------------------------------------------------------

    def test_qx003_handler_dans_une_autre_unite_de_compilation(self):
        """QX003: a handler defined in ANOTHER compilation unit is not a
        defect: a single file cannot prove it.

        Sources: resmgr_io_funcs_t() (each member is a function pointer).

        The checker therefore no longer CONDEMNS it (ERROR): it reports it as
        INFO, and the finding disappears as soon as the symbol is known from
        the analysed files.
        """
        src = read("qnx80_resmgr_minimal.c")
        # the local definition is renamed: the table now points at a symbol
        # that does not exist in ANY analysed compilation unit.
        src = src.replace("static int qx_read(resmgr_context_t",
                          "static int qx_read_local(resmgr_context_t")
        src = src.replace("io_funcs.read  = qx_read;", "io_funcs.read  = qx_read_other_unit;")
        found = qx_probe.analyse("split.c", src)
        self.assertEqual(actionable(found), [],
                         msg=f"false positive: the handler is defined elsewhere: {actionable(found)}")
        self.assertIn("QX003", codes(found, "INFO"))
        known = qx_probe.analyse("split.c", src, known_symbols={"qx_read_other_unit"})
        self.assertNotIn("QX003", codes(known),
                         msg="the symbol is known: no finding")

    # ------------------------------------------------------------------
    # QX004 — the access gate
    # ------------------------------------------------------------------

    def test_qx004_porte_deleguee_a_un_helper(self):
        """QX004: a verification delegated to a helper function IS a
        verification.

        Sources: iofunc_read_verify() ("All read handlers should start with
        a call to iofunc_read_verify() and proceed only if it returns EOK").
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("int main(void)\n{",
                          "static int qx_check_read(resmgr_context_t *ctp, io_read_t *msg,\n"
                          "                           RESMGR_OCB_T *ocb)\n"
                          "{\n"
                          "    return iofunc_read_verify(ctp, msg, ocb, NULL);\n"
                          "}\n\n"
                          "int main(void)\n{")
        src = src.replace("    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)\n"
                          "        return status;",
                          "    if ((status = qx_check_read(ctp, msg, ocb)) != EOK)\n"
                          "        return status;")
        found = qx_probe.analyse("delegated.c", src)
        self.assertNotIn("QX004", codes(found),
                         msg="false positive: the access gate is delegated to a helper")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

    # ------------------------------------------------------------------
    # QX011 — is the table initialised?
    # ------------------------------------------------------------------

    def test_qx011_table_mise_a_zero_statique(self):
        """QX011: a static table zeroed by C is a DELIBERATE choice (the
        pointers are NULL), not an uninitialised table.

        Sources: iofunc_func_init() ("initializes the passed connect and io
        structures with the POSIX-layer default functions"), resmgr_io_funcs_t().

        The same test covers the two shapes that the rule used to condemn:
        a table that is a MEMBER of a structure (it has the storage
        duration of the object that holds it, and it is filled through the
        member: &resmgr.io_funcs), and a table filled by a SECOND
        iofunc_func_init() call (a resource manager may fill two io tables,
        one per device).
        """
        src = mutate("qnx80_resmgr_minimal.c",
                     "    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,\n"
                     "                     _RESMGR_IO_NFUNCS, &io_funcs);\n",
                     "")
        found = qx_probe.analyse("zeroed.c", src)
        self.assertNotIn("QX011", codes(found),
                         msg="false positive: a static table is zeroed by C")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

        member = """
#include <sys/iofunc.h>
#include <sys/resmgr.h>

struct my_resmgr {
    iofunc_attr_t              attr;
    resmgr_connect_funcs_t     connect_funcs;
    resmgr_io_funcs_t          io_funcs;
};

static struct my_resmgr resmgr = {0};

static int my_read(resmgr_context_t *ctp, io_read_t *msg, iofunc_ocb_t *ocb)
{
    int rc = iofunc_read_verify(ctp, msg, ocb, NULL);
    if (rc != EOK) {
        return rc;
    }
    return _RESMGR_PTR(ctp, msg, 0);
}

int start(dispatch_t *dpp)
{
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &resmgr.connect_funcs,
                     _RESMGR_IO_NFUNCS, &resmgr.io_funcs);
    resmgr.io_funcs.read = my_read;
    while (1) {
        dispatch_context_t *ctp = dispatch_block(NULL);
        if (ctp == NULL) {
            break;
        }
        dispatch_handler(ctp);
    }
    return 0;
}
"""
        found = qx_probe.analyse("member.c", member)
        self.assertNotIn("QX011", codes(found),
                         msg="false positive: a member has the storage duration "
                             "of the object that holds it")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

        two_calls = """
#include <sys/iofunc.h>
#include <sys/resmgr.h>

int start(void)
{
    resmgr_connect_funcs_t connect_funcs;
    resmgr_io_funcs_t      io_funcs;
    resmgr_io_funcs_t      io_funcs_second;

    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    iofunc_func_init(0, NULL, _RESMGR_IO_NFUNCS, &io_funcs_second);
    return 0;
}
"""
        found = qx_probe.analyse("two_calls.c", two_calls)
        self.assertNotIn("QX011", codes(found),
                         msg="false positive: the second iofunc_func_init() "
                             "initialises the second table")


class TestDetection(unittest.TestCase):
    """The rules must bite: the expected finding, one sabotage at a time."""

    def _mutate(self, name, old, new):
        return mutate(name, old, new)

    def test_qx001_aucune_table_de_dispatch(self):
        """QX001: a resource manager without a dispatch table can answer
        nothing to the client.

        Source: resmgr_attach() (connect_funcs and io_funcs arguments).
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("static resmgr_connect_funcs_t connect_funcs;\n"
                          "static resmgr_io_funcs_t io_funcs;\n", "")
        src = src.replace("    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,\n"
                          "                     _RESMGR_IO_NFUNCS, &io_funcs);\n", "")
        src = src.replace("    io_funcs.read  = qx_read;\n    io_funcs.write = qx_write;\n", "")
        src = src.replace("_FTYPE_ANY, 0, &connect_funcs, &io_funcs, &attr);",
                          "_FTYPE_ANY, 0, NULL, NULL, &attr);")
        found = qx_probe.analyse("no_table.c", src)
        self.assertIn("QX001", codes(found, "ERROR"))

    def test_qx001_table_nulle_a_l_attach(self):
        """QX001: resmgr_attach() with a NULL table.

        Source: resmgr_attach() — the documentation explicitly allows NULL for
        "attr" ("or NULL to use the default attributes") and for "path", but
        NOT for the two dispatch tables: a NULL table is a resource manager
        without any handler.
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "_FTYPE_ANY, 0, &connect_funcs, &io_funcs, &attr);",
                           "_FTYPE_ANY, 0, NULL, NULL, &attr);")
        found = qx_probe.analyse("null_table.c", src)
        self.assertIn("QX001", codes(found, "ERROR"))

    def test_qx002_debordement_du_tableau(self):
        """QX002: iofunc_func_init() must not be asked to fill more entries
        than the table holds.

        Sources: iofunc_func_init() (nio: "The number of entries in the io
        table that you want to fill"), resmgr_io_funcs_t() (the 34 members of
        the table), resmgr_connect_funcs_t() (the 8 members of the other table).
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "_RESMGR_IO_NFUNCS, &io_funcs);", "64, &io_funcs);")
        found = qx_probe.analyse("overflow.c", src)
        self.assertIn("QX002", codes(found, "ERROR"))

    def test_qx005_chemin_relatif(self):
        """QX005: a relative path is reported (WARN), an absolute path outside
        /dev/ is not.

        Source: resmgr_attach() ("if you provide a path that doesn't start
        with a slash, it's considered to be relative to the current working
        directory").
        """
        found = findings("qnx80_resmgr_relative_path.c")
        self.assertEqual(codes_of(found, "QX005"), ["QX005"])
        self.assertEqual(codes(found, "WARN"), ["QX005"])

    def test_qx003_handler_non_defini(self):
        """QX003: a handler neither defined nor declared in the analysed
        files is reported — but as INFO: a single compilation unit cannot
        prove that a symbol is missing.

        Source: resmgr_io_funcs_t() (each member is a function pointer).
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "io_funcs.read  = qx_read;", "io_funcs.read  = qx_read_absent;")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX003", codes(found))
        self.assertNotIn("QX003", codes(found, "ERROR"),
                         msg="a single file cannot prove that a handler is undefined")

    def test_qx004_porte_acces_absente(self):
        """QX004: a read handler must call iofunc_read_verify().

        Source: iofunc_read_verify() ("All read handlers should start with
        a call to iofunc_read_verify() and proceed only if it returns EOK").

        The test file is a REAL fixture of the repository (a single line
        removed from the canonical code): the demonstration video plays
        exactly the same file.
        """
        src = (REPO / "tests" / "fixtures" / "qnx80_resmgr_qx004_no_gate.c").read_text(
            encoding="utf-8")
        found = qx_probe.analyse("tests/fixtures/qnx80_resmgr_qx004_no_gate.c", src)
        self.assertIn("QX004", codes(found, "ERROR"))
        self.assertEqual(codes(found, "ERROR"), ["QX004"],
                         msg="the fixture must produce a single ERROR")

    def test_qx004_porte_citee_dans_une_chaine(self):
        """QX004: the NAME of the gate quoted in an error message is not an
        access gate.

        Sources: iofunc_read_verify() ("All read handlers should start with
        a call to iofunc_read_verify() and proceed only if it returns EOK").
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)\n"
                           "        return status;",
                           "    fprintf(stderr, \"iofunc_read_verify() was not called\\n\");\n"
                           "    status = EOK;")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX004", codes(found, "ERROR"))

    def test_qx006_boucle_de_messages_absente(self):
        """QX006: without dispatch_block()/resmgr_block(), the resmgr never
        waits for a message.

        The level is a WARN, not an ERROR: one translation unit cannot prove
        that the project has no message loop.  The rule was an ERROR until
        this version, and it cried wolf on a real resource manager whose
        loop lives in another file (see docs/BENCHMARK.md).
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "if ((ctp = dispatch_block(ctp)) == NULL) {",
                           "if ((ctp = ctp) == NULL) {")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX006", codes(found, "WARN"))
        self.assertNotIn("QX006", codes(found, "ERROR"))

    def test_qx007_dispatch_absent(self):
        """QX007: blocking without dispatching the message leaves the client
        blocked.

        WARN, for the same reason as QX006: the handler may be called in
        another translation unit.
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "dispatch_handler(ctp);", "/* SABOTAGE: message never dispatched */")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX007", codes(found, "WARN"))
        self.assertNotIn("QX007", codes(found, "ERROR"))

    def test_qx008_slot_non_cable_reste_info(self):
        """QX008: an unwired slot of the io table is reported — as INFO.

        Sources: resmgr_io_funcs_t() ("You can initialize this table by
        calling iofunc_func_init() and then overriding the defaults with
        your own functions") and its "Default" column
        (iofunc_read_default(), iofunc_write_default(), ...).

        A read-only resource manager (no `write`) is VALID: the rule must
        never condemn it, and the exit code must stay 0.
        """
        found = findings("qnx80_resmgr_readonly.c")
        self.assertEqual(codes_of(found, "QX008"), ["QX008"] * 4,
                         msg="the four unwired slots must be reported")
        self.assertNotIn("QX008", codes(found, "ERROR"),
                         msg="an unwired slot must never be an ERROR")
        self.assertNotIn("QX008", codes(found, "WARN"),
                         msg="an unwired slot must never be a WARN")
        self.assertEqual(actionable(found), [],
                         msg=f"false positive on valid code: {actionable(found)}")

    def test_qx009_parts_superieures_a_nparts_max(self):
        """QX009: the reply must not return more parts than the IOV declares
        (nparts_max).

        Sources: resmgr_attach() (nparts_max = number of components of the
        IOV), _RESMGR_NPARTS() (nparts_max must be the maximum value of num).
        """
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "return _RESMGR_NPARTS(1);", "return _RESMGR_NPARTS(2);")
        found = qx_probe.analyse("broken.c", src)
        self.assertIn("QX009", codes(found, "ERROR"))

    def test_qx009_parts_conformes(self):
        """QX009 must NOT fire when the number of parts fits in the IOV."""
        found = findings("qnx80_resmgr_minimal.c")
        self.assertNotIn("QX009", codes(found))

    def test_qx010_nombre_de_slots_est_une_macro(self):
        """QX010: the number of entries of iofunc_func_init() is a macro —
        information, and no conclusion is drawn from it.

        Sources: iofunc_func_init() ("Typically, you pass
        _RESMGR_CONNECT_NFUNCS for this argument", "Typically, you pass
        _RESMGR_IO_NFUNCS"), resmgr_io_funcs_t().

        The rule must stay at INFO level: the macro is the normal case, and
        the checker cannot read its value.
        """
        found = findings("qnx80_resmgr_minimal.c")
        self.assertEqual(codes_of(found, "QX010"), ["QX010"] * 2,
                         msg="the io count and the connect count are macros")
        self.assertNotIn("QX010", codes(found, "ERROR"),
                         msg="a macro is not an overflow")
        self.assertNotIn("QX010", codes(found, "WARN"),
                         msg="a macro is the normal case, not a warning")

    def test_qx010_nombre_de_slots_litteral(self):
        """QX010 must NOT fire when the number of entries is a literal."""
        src = self._mutate("qnx80_resmgr_minimal.c",
                           "    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,\n"
                           "                     _RESMGR_IO_NFUNCS, &io_funcs);\n",
                           "    iofunc_func_init(8, &connect_funcs,\n"
                           "                     34, &io_funcs);\n")
        found = qx_probe.analyse("literal.c", src)
        self.assertNotIn("QX010", codes(found),
                         msg="a literal is not a macro: the rule must stay silent")

    def test_qx011_table_automatique_non_initialisee(self):
        """QX011: an automatic dispatch table (on the stack) that is never
        initialised holds INDETERMINATE function pointers.

        Sources: iofunc_func_init() ("initializes the passed connect and io
        structures with the POSIX-layer default functions"), resmgr_io_funcs_t().
        """
        src = read("qnx80_resmgr_minimal.c")
        src = src.replace("static resmgr_io_funcs_t io_funcs;\n", "")
        src = src.replace("    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,\n"
                          "                     _RESMGR_IO_NFUNCS, &io_funcs);\n", "")
        src = src.replace("    io_funcs.read  = qx_read;\n    io_funcs.write = qx_write;\n",
                          "    resmgr_io_funcs_t io_funcs;\n"
                          "    io_funcs.read  = qx_read;\n")
        found = qx_probe.analyse("auto_table.c", src)
        self.assertIn("QX011", codes(found, "WARN"))


class TestOutputFormat(unittest.TestCase):
    """The output format itself is part of the contract (decision 2 of
    05/11/2026: the summary line must be in English)."""

    def test_summary_line_is_english(self):
        """The summary line must be exactly
        'RESULT: N finding(s), X ERROR, Y WARN'.

        The former wording ('RESULTAT: N constat(s)') was a language
        inconsistency in an English tool; the tool, its messages and this
        line are now entirely in English.
        """
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = qx_probe.main(["qx_probe.py",
                                 str(EXAMPLES / "qnx80_resmgr_minimal.c")])
        out = buf.getvalue()
        self.assertEqual(rc, 0, msg="a valid file must not produce an actionable finding")
        summary = out.strip().splitlines()[-1]
        self.assertEqual(summary, "RESULT: 5 finding(s), 0 ERROR, 0 WARN",
                         msg=f"unexpected summary line: {summary!r}")
        self.assertNotIn("RESULTAT", out, msg="the French summary line is gone")
        self.assertNotIn("constat", out, msg="the output contains no French word")

    def test_exit_code_follows_the_findings(self):
        """The exit code must be 1 as soon as an ERROR or a WARN is found,
        and 0 otherwise: this is what makes the tool usable as a CI gate.
        """
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_ok = qx_probe.main(["qx_probe.py",
                                   str(EXAMPLES / "qnx80_resmgr_minimal.c")])
            rc_ko = qx_probe.main(["qx_probe.py",
                                   str(REPO / "tests" / "fixtures"
                                       / "qnx80_resmgr_qx004_no_gate.c")])
        self.assertEqual(rc_ok, 0)
        self.assertEqual(rc_ko, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

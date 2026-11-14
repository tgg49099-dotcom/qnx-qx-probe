#!/usr/bin/env python3
"""QX-PROBE on resource managers split over several files (v8, 14/11/2026).

Measured on the resource managers of a published QNX 6.4 source tree
(github.com/vocho/openqnx at cc95df35, trunk/services/: slogger, mqueue, dumper, random,
devc-ditto, pipe, mq, syslogd, procnto's path manager).  Before v8 the
linter reported 22 ERROR and 20 WARN on that code; after v8: one ERROR,
a real one (a write handler without iofunc_write_verify()), and the
WARN left are the path-manager files whose loop lives in procnto itself.

The fixtures of tests/fixtures/multifile/ are written for this suite; no
line is copied from the QNX sources.

  split_*.c              one resmgr in three files: no QX001 on the handler
                         file, no QX006/QX007 when the loop is in another file
  root_attach.c          resmgr_attach() on "" (the root): not a relative path
  extern_table.c         `extern resmgr_io_funcs_t t;` inside a function is
                         not an automatic, uninitialised table (QX011)
  own_ocb.c              own OCB bound with resmgr_open_bind(): the gate
                         iofunc_read_verify() (iofunc_ocb_t) does not apply,
                         QX004 drops to INFO
  iofunc_ocb_no_gate.c   same through iofunc_ocb_attach(): real bug, ERROR
  (generated)            the read handler delegates the gate to a helper
                         of ANOTHER analysed file: no QX004; a helper there
                         that does not run the gate: ERROR QX004
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "multifile"
sys.path.insert(0, str(ROOT))
import qx_probe  # noqa: E402


def run(*args):
    p = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "qx_probe.py"), *args],
                       capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout, p.stderr


def acting(out):
    return [l for l in out.splitlines() if l.startswith(("ERROR", "WARN"))]


class MultiFile(unittest.TestCase):
    def test_split_resmgr_is_clean(self):
        rc, out, _ = run(*(str(FIX / n) for n in
                           ("split_main.c", "split_io_read.c", "split_loop.c")))
        self.assertEqual(acting(out), [], msg=out)
        self.assertEqual(rc, 0, msg=out)

    def test_handler_file_alone_has_no_qx001(self):
        p = FIX / "split_io_read.c"
        found = qx_probe.analyse(str(p), p.read_text())
        self.assertNotIn("QX001", [x.code for x in found])

    def test_loop_in_other_file_no_qx006(self):
        p = FIX / "split_main.c"
        alone = [x.code for x in qx_probe.analyse(str(p), p.read_text())]
        self.assertIn("QX006", alone, msg="alone, the file has no loop: WARN expected")
        rc, out, _ = run(str(p), str(FIX / "split_loop.c"))
        self.assertNotIn("QX006", out)
        self.assertNotIn("QX007", out)

    def test_empty_root_path_is_not_relative(self):
        p = FIX / "root_attach.c"
        found = qx_probe.analyse(str(p), p.read_text())
        self.assertNotIn("QX005", [x.code for x in found])

    def test_block_scope_extern_table_is_not_automatic(self):
        p = FIX / "extern_table.c"
        found = qx_probe.analyse(str(p), p.read_text())
        self.assertNotIn("QX011", [x.code for x in found])

    def test_own_ocb_gate_is_info(self):
        p = FIX / "own_ocb.c"
        found = qx_probe.analyse(str(p), p.read_text())
        q4 = [x.level for x in found if x.code == "QX004"]
        self.assertEqual(q4, ["INFO"])

    def test_iofunc_ocb_without_gate_stays_error(self):
        p = FIX / "iofunc_ocb_no_gate.c"
        found = qx_probe.analyse(str(p), p.read_text())
        q4 = [x.level for x in found if x.code == "QX004"]
        self.assertEqual(q4, ["ERROR"])


class GateInAnotherFile(unittest.TestCase):
    def _files(self, tmp, gate_body):
        src = (ROOT / "examples" / "qnx80_resmgr_minimal.c").read_text()
        old = ("    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)\n"
               "        return status;\n")
        self.assertIn(old, src)
        a = pathlib.Path(tmp) / "delegue.c"
        b = pathlib.Path(tmp) / "gate.c"
        a.write_text(src.replace(old, "    if ((status = my_gate(ctp, msg, ocb)) != EOK)\n"
                                      "        return status;\n"))
        b.write_text("static int my_gate(resmgr_context_t *ctp, io_read_t *msg, "
                     "iofunc_ocb_t *ocb)\n{\n    " + gate_body + "\n}\n")
        return str(a), str(b)

    def test_gate_helper_in_other_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, _ = run(*self._files(tmp, "return iofunc_read_verify(ctp, msg, ocb, NULL);"))
        self.assertEqual(acting(out), [], msg=out)

    def test_helper_in_other_file_without_gate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, _ = run(*self._files(tmp, "return 0;"))
        self.assertEqual([l.split()[1] for l in acting(out)], ["QX004"], msg=out)


class CommandLine(unittest.TestCase):
    def test_help(self):
        rc, out, err = run("--help")
        self.assertEqual(rc, 0)
        self.assertIn("Usage:", out)
        self.assertNotIn("Traceback", out + err)

    def test_unknown_option(self):
        rc, out, err = run("--bogus", "examples/qnx80_resmgr_minimal.c")
        self.assertEqual(rc, 2)
        self.assertNotIn("Traceback", out + err)

    def test_missing_file(self):
        rc, out, err = run("does-not-exist.c")
        self.assertEqual(rc, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", out + err)

    def test_same_file_twice_is_reported_once(self):
        one = run("examples/qnx80_resmgr_relative_path.c")[1].splitlines()
        two = run("examples/qnx80_resmgr_relative_path.c",
                  "examples/qnx80_resmgr_relative_path.c")[1].splitlines()
        self.assertEqual(one, two)


class FrameworkOnlyAttach(unittest.TestCase):
    """v9 (14/11/2026): resmgr_attach() with a NULL path.

    Source: resmgr_attach() -- "If path is NULL, only the first step will be
    done, unless RESMGR_FLAG_ATTACH_LOCAL is set in attr.flags or
    _RESMGR_FLAG_FTYPEONLY is set in flags"; the first step only sets up the
    framework, the tables are bound in the second.  Measured on procnto
    (proc/message.c) in the same published QNX source tree: 2 false ERROR
    QX001 before v9, 0 after.
    """

    def _qx001(self, name, src=None):
        p = FIX / name
        found = qx_probe.analyse(str(p), src if src is not None else p.read_text())
        return [x for x in found if x.code == "QX001" and x.level == "ERROR"]

    def test_null_path_null_tables_is_correct(self):
        self.assertEqual(self._qx001("framework_init.c"), [])
        rc, out, _ = run(str(FIX / "framework_init.c"))
        self.assertEqual(acting(out), [], msg=out)
        self.assertEqual(rc, 0, msg=out)

    def test_ftypeonly_binds_the_tables(self):
        self.assertEqual(len(self._qx001("framework_ftypeonly.c")), 2)

    def test_attach_local_binds_the_tables(self):
        src = (FIX / "framework_init.c").read_text().replace(
            "rattr.nparts_max = 1;",
            "rattr.nparts_max = 1;\n    rattr.flags = RESMGR_FLAG_ATTACH_LOCAL;")
        self.assertEqual(len(self._qx001("framework_init.c", src)), 2)

    def test_named_path_with_null_tables_still_error(self):
        src = (FIX / "framework_init.c").read_text().replace(
            "resmgr_attach(dpp, &rattr, NULL, 0, 0,",
            'resmgr_attach(dpp, &rattr, "/dev/mine", _FTYPE_ANY, 0,')
        self.assertEqual(len(self._qx001("framework_init.c", src)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)

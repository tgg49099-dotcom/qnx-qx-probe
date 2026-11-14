#!/usr/bin/env python3
"""Robustness of QX-PROBE on correct code written in ordinary C styles.

The golden rule of the linter is zero false positives.  Each fixture of
tests/fixtures/robustness/ is the official QNX 8.0 iofunc_func_init()
example (examples/qnx80_resmgr_official_example.c) with ONE realistic
change.  Before this suite, three of these CORRECT files produced a false
ERROR QX004, and two REAL bugs were missed:

  ok_char_brace.c                 a '}' character literal inside the read
                                  handler ended its body too early
  ok_gate_two_helpers_deep.c      the gate is called by a helper of a
                                  helper (only one level was followed)
  ok_dead_handler_if0.c           an old handler kept under `#if 0` was
                                  read instead of the compiled one
  bad_gate_in_if0.c               the gate itself is under `#if 0`: it is
                                  never compiled, the handler has no gate
  bad_gate_in_else_of_if1.c       same, in the `#else` branch of `#if 1`

The v6 variants (14 November 2026) cover the ways C code wires a slot
without the plain `table.slot = handler` spelling.  Before v6, four real
bugs were missed and one correct file got a false ERROR QX004:

  bad_amp.c / bad_desig_amp.c     handler wired as `= &my_io_read` (the
                                  address-of operator), gate missing
  bad_ptr.c                       table filled through a local pointer
                                  (`iof->io_read = ...`), gate missing
  bad_param.c                     table filled by a set-up function that
                                  takes `resmgr_io_funcs_t *`, gate missing
  ok_macro.c                      the gate is wrapped in a project macro
                                  (false ERROR QX004 before v6)

and the correct twins of the first four were told "read is not assigned".
A `->read` on a structure that is NOT a dispatch table is ignored
(ok_other_struct_arrow.c).

The v7 variants (14 November 2026) follow the official QNX 8.0 pages
iofunc_read_default() and iofunc_write_default(): "The
iofunc_read_default() function calls iofunc_read_verify() to verify if
this read operation should be permitted" (same for writes).  Before v7,
two CORRECT handlers that delegate to the POSIX default got a false
ERROR QX004:

  ok_read_delegates_default.c     read handler returns iofunc_read_default()
  ok_write_delegates_default.c    write handler returns iofunc_write_default()

while a default that is only MENTIONED (comment, message string) is still
no gate (bad_default_only_mentioned.c).

Unknown conditions (`#ifdef X`) stay live code: the linter never guesses a
build configuration (ok_gate_in_ifdef.c).

Run:  python3 -I tests/test_robustness.py
"""

import contextlib
import io
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import qx_probe  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "robustness"


def run(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = qx_probe.main(["qx_probe.py", str(path)])
    return rc, buf.getvalue()


class CorrectCodeStaysClean(unittest.TestCase):
    """Every ok_*.c file is correct code: no ERROR, no WARN, exit code 0."""

    def test_every_ok_fixture(self):
        files = sorted(FIX.glob("ok_*.c"))
        self.assertGreaterEqual(len(files), 10)
        for f in files:
            with self.subTest(fixture=f.name):
                rc, out = run(f)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("ERROR", out.replace("0 ERROR", ""))


class RealBugsAreFound(unittest.TestCase):
    """Every bad_*.c file misses the access gate: exactly one ERROR QX004."""

    def test_every_bad_fixture(self):
        files = sorted(FIX.glob("bad_*.c"))
        self.assertGreaterEqual(len(files), 7)
        for f in files:
            with self.subTest(fixture=f.name):
                rc, out = run(f)
                self.assertEqual(rc, 1, out)
                self.assertEqual(out.count("ERROR QX004"), 1, out)
                raw = f.read_text().split("\n")
                want = 1 + next(i for i, l in enumerate(raw)
                                if l.startswith("static int my_io_read("))
                self.assertIn(f"{f.name}:{want}:", out.replace(str(FIX) + "/", ""))


class WiredSlotIsNotReportedUnassigned(unittest.TestCase):
    """A read slot wired through &, a pointer or a set-up function is wired."""

    def test_no_false_unassigned_info(self):
        for name in ("ok_amp.c", "ok_ptr.c", "ok_param.c", "ok_desig_amp.c"):
            with self.subTest(fixture=name):
                rc, out = run(FIX / name)
                self.assertEqual(rc, 0, out)
                self.assertNotIn(".read is not assigned", out)

    def test_other_structure_is_not_a_table(self):
        src = ("struct ops { int (*read)(void); };\n"
               "static int r(void) { return 0; }\n"
               "void f(struct ops *o) { o->read = r; }\n")
        self.assertEqual(qx_probe.slot_assignments(src), [])


class DefaultHandlerRunsTheGate(unittest.TestCase):
    """iofunc_*_default() calls iofunc_*_verify() itself (QNX 8.0 pages)."""

    def test_delegating_handlers_are_gated(self):
        for name in ("ok_read_delegates_default.c", "ok_write_delegates_default.c"):
            with self.subTest(fixture=name):
                rc, out = run(FIX / name)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("QX004", out)

    def test_mention_is_not_a_call(self):
        rc, out = run(FIX / "bad_default_only_mentioned.c")
        self.assertEqual(rc, 1, out)
        self.assertEqual(out.count("ERROR QX004"), 1, out)


class DeadCodeKeepsLineNumbers(unittest.TestCase):
    def test_strip_dead_code_keeps_lines(self):
        src = "a\n#if 0\nb {\n#if 1\nc\n#endif\n#else\nd\n#endif\ne\n"
        out = qx_probe.strip_dead_code(src)
        self.assertEqual(out.count("\n"), src.count("\n"))
        lines = out.split("\n")
        self.assertEqual(lines[2].strip(), "")   # dead
        self.assertEqual(lines[4].strip(), "")   # nested in dead: still dead
        self.assertEqual(lines[7], "d")          # #else of #if 0: live
        self.assertEqual(lines[9], "e")

    def test_unknown_condition_is_live(self):
        src = "#ifdef X\nx\n#else\ny\n#endif\n"
        self.assertEqual(qx_probe.strip_dead_code(src), src)


if __name__ == "__main__":
    unittest.main(verbosity=1)

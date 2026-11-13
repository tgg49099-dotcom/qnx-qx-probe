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
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            with self.subTest(fixture=f.name):
                rc, out = run(f)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("ERROR", out.replace("0 ERROR", ""))


class RealBugsAreFound(unittest.TestCase):
    """Every bad_*.c file misses the access gate: exactly one ERROR QX004."""

    def test_every_bad_fixture(self):
        files = sorted(FIX.glob("bad_*.c"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            with self.subTest(fixture=f.name):
                rc, out = run(f)
                self.assertEqual(rc, 1, out)
                self.assertEqual(out.count("ERROR QX004"), 1, out)
                raw = f.read_text().split("\n")
                want = 1 + next(i for i, l in enumerate(raw)
                                if l.startswith("static int my_io_read("))
                self.assertIn(f"{f.name}:{want}:", out.replace(str(FIX) + "/", ""))


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

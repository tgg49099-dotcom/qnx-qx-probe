#!/usr/bin/env python3
"""Line numbers and machine-readable output (JSON, SARIF 2.1.0) of QX-PROBE.

Two contracts are locked here:

  * every finding carries the line of the RAW file it is about — a block
    comment spread over several lines must not shift it (the stripper used to
    replace a multi-line comment by a single space: QX005 then pointed 29
    lines too early in examples/qnx80_resmgr_relative_path.c);
  * --format json and --format sarif describe exactly the same findings as
    the text output, with the same exit code (the CI gate does not depend on
    the format).

Run:  python3 -I tests/test_output_formats.py
"""

import contextlib
import io
import json
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import qx_probe  # noqa: E402

EX = REPO / "examples"
FIXTURE = REPO / "tests" / "fixtures" / "qnx80_resmgr_qx004_no_gate.c"
ALL_FILES = sorted(EX.glob("*.c")) + [FIXTURE]


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = qx_probe.main(["qx_probe.py", *map(str, args)])
    return rc, buf.getvalue()


def raw_line(path, n):
    return pathlib.Path(path).read_text(encoding="utf-8").split("\n")[n - 1]


class LineNumbers(unittest.TestCase):

    def test_qx005_points_at_the_resmgr_attach_call(self):
        path = EX / "qnx80_resmgr_relative_path.c"
        f = [x for x in qx_probe.analyse(str(path), path.read_text()) if x.code == "QX005"]
        self.assertEqual(len(f), 1)
        self.assertIn("resmgr_attach", raw_line(path, f[0].line))
        self.assertTrue(f[0].where.endswith(f":{f[0].line}"),
                        msg="the text output and the line field agree")

    def test_multiline_comment_does_not_shift_lines(self):
        src = ('#include <sys/resmgr.h>\n/* one\n two\n three\n four */\n'
               'static resmgr_io_funcs_t io_funcs;\nint main(void) {\n'
               '  resmgr_attach(dpp, &a, "rel", _FTYPE_ANY, 0, &cf, &io_funcs, &at);\n'
               '  resmgr_block(c); resmgr_handler(c);\n}\n')
        f = [x for x in qx_probe.analyse("t.c", src) if x.code == "QX005"]
        self.assertEqual([x.line for x in f], [8])

    def test_qx004_points_at_the_handler_definition(self):
        f = [x for x in qx_probe.analyse(str(FIXTURE), FIXTURE.read_text()) if x.code == "QX004"]
        self.assertTrue(f)
        for x in f:
            handler = x.message.split("()")[0]
            self.assertIn(handler, raw_line(FIXTURE, x.line))

    def test_every_line_exists_in_the_file(self):
        for path in ALL_FILES:
            n = len(path.read_text(encoding="utf-8").split("\n"))
            for x in qx_probe.analyse(str(path), path.read_text(encoding="utf-8")):
                self.assertTrue(1 <= x.line <= n, msg=f"{path.name}: {x}")


class NoFalseInfo(unittest.TestCase):

    def test_qx003_ignores_a_null_assignment(self):
        """'g_attr.mount = NULL;' (iofunc_attr_t.mount, seen in a real
        resource manager of the benchmark) is not a missing handler."""
        src = ('#include <sys/resmgr.h>\nstatic resmgr_io_funcs_t io_funcs;\n'
               'static iofunc_attr_t g_attr;\nint main(void) {\n'
               '  iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &cf, _RESMGR_IO_NFUNCS, &io_funcs);\n'
               '  g_attr.mount = NULL;\n  io_funcs.read = my_read;\n'
               '  resmgr_attach(dpp, &a, "/dev/x", _FTYPE_ANY, 0, &cf, &io_funcs, &g_attr);\n'
               '  resmgr_block(c); resmgr_handler(c);\n}\n')
        qx003 = [x for x in qx_probe.analyse("t.c", src) if x.code == "QX003"]
        self.assertEqual([x.message.split(":")[0] for x in qx003], ["io_funcs.read = my_read"])


class MachineReadable(unittest.TestCase):

    def test_json_has_the_same_findings_and_exit_code(self):
        for path in ALL_FILES:
            rc_t, out_t = run(path)
            rc_j, out_j = run("--format", "json", path)
            data = json.loads(out_j)
            self.assertEqual(rc_t, rc_j, msg=path.name)
            text = [l for l in out_t.splitlines() if l[:5].strip() in ("ERROR", "WARN", "INFO")]
            self.assertEqual(len(text), len(data["findings"]), msg=path.name)
            self.assertEqual(sorted(l.split()[1] for l in text),
                             sorted(x["code"] for x in data["findings"]))

    def test_sarif_is_well_formed(self):
        rc, out = run("--format=sarif", FIXTURE, EX / "qnx80_resmgr_relative_path.c")
        self.assertEqual(rc, 1, msg="the CI gate works in SARIF too")
        doc = json.loads(out)
        self.assertEqual(doc["version"], "2.1.0")
        run0 = doc["runs"][0]
        ids = [r["id"] for r in run0["tool"]["driver"]["rules"]]
        self.assertEqual(len(ids), len(set(ids)))
        levels = {r["level"] for r in run0["results"]}
        self.assertTrue(levels <= {"error", "warning", "note"})
        for r in run0["results"]:
            self.assertEqual(ids[r["ruleIndex"]], r["ruleId"])
            loc = r["locations"][0]["physicalLocation"]
            self.assertTrue(loc["artifactLocation"]["uri"].endswith(".c"))
            self.assertGreaterEqual(loc["region"]["startLine"], 1)
        self.assertIn("QX004", ids)
        self.assertIn("QX005", ids)

    def test_valid_code_gives_exit_0_in_sarif(self):
        rc, out = run("--format", "sarif", EX / "blackberry_eventfd_mgr.c")
        self.assertEqual(rc, 0)
        res = json.loads(out)["runs"][0]["results"]
        self.assertFalse([r for r in res if r["level"] != "note"])

    def test_bad_format_is_a_usage_error(self):
        rc, _ = run("--format", "xml", FIXTURE)
        self.assertEqual(rc, 2)


class TextLocations(unittest.TestCase):
    """Every text finding is `LEVEL CODE file:line: message` (gcc format).

    The text output used to print `file:read:` or `file:io_funcs:` (a slot
    name, not a line) for QX003, QX004 and QX008, and only `file:` for
    QX001, QX002, QX006, QX007, QX009, QX010 and QX011: an editor or a CI
    log could not open the line, and the README promised `file:line`.
    """

    LINE_RE = r"^(ERROR|WARN |INFO ) QX\d{3}  (?P<file>\S+):(?P<line>\d+): \S"

    def test_every_text_finding_has_a_numeric_line(self):
        import re
        for path in ALL_FILES:
            _rc, out = run(path)
            for line in out.split("\n"):
                if not line.startswith(("ERROR", "WARN", "INFO")):
                    continue
                m = re.match(self.LINE_RE, line)
                self.assertIsNotNone(m, msg=line)
                self.assertEqual(m.group("file"), str(path), msg=line)
                n = int(m.group("line"))
                self.assertTrue(1 <= n <= len(path.read_text().split("\n")), msg=line)

    def test_qx004_points_at_the_handler_definition(self):
        _rc, out = run(FIXTURE)
        line = [x for x in out.split("\n") if " QX004 " in x][0]
        n = int(line.split(f"{FIXTURE}:", 1)[1].split(":", 1)[0])
        self.assertIn("qx_read(", raw_line(FIXTURE, n))

    def test_text_and_json_give_the_same_lines(self):
        _rc, txt = run(FIXTURE)
        _rc, js = run("--format", "json", FIXTURE)
        from_json = sorted(f"{f['file']}:{f['line']}" for f in json.loads(js)["findings"])
        from_text = sorted(x.split()[2].rstrip(":") for x in txt.split("\n")
                           if x.startswith(("ERROR", "WARN", "INFO")))
        self.assertEqual(from_json, from_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

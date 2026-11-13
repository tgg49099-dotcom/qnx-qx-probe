#!/usr/bin/env python3
"""scripts/build_qcc.sh, tested WITHOUT the QNX SDK.

A fake `qcc` placed first on the PATH records its arguments and answers
`qcc -V` like the real driver (a list of installed variants).  This proves
what the script will ask the real compiler, not that QNX code compiles: the
QNX 8.0 build itself stays NOT MEASURED until it runs with the SDP 8.0.

Run:  python3 -I tests/test_build_qcc.py
"""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
FAKE = """#!/bin/sh
echo "$*" >> "$QCC_LOG"
case "$1" in
  -V) echo "cc: targets available in $FAKE_SDP:"
      for v in $FAKE_VARIANTS; do echo "        12.2.0,$v"; done; exit 0 ;;
esac
out=""; prev=""
for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done
[ -n "$out" ] && echo fake > "$out"
exit 0
"""


class BuildScript(unittest.TestCase):

    def run_build(self, target, variants="gcc_ntox86_64 gcc_ntoaarch64le"):
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = tmp / "repo"
        shutil.copytree(REPO / "examples", repo / "examples")
        shutil.copytree(REPO / "scripts", repo / "scripts")
        (tmp / "bin").mkdir()
        q = tmp / "bin" / "qcc"
        q.write_text(FAKE)
        q.chmod(0o755)
        env = dict(os.environ, PATH=f"{tmp/'bin'}:{os.environ['PATH']}",
                   QCC_LOG=str(tmp / "log"), FAKE_VARIANTS=variants, FAKE_SDP="sdp")
        r = subprocess.run(["bash", str(repo / "scripts" / "build_qcc.sh"), *target],
                           capture_output=True, text=True, env=env)
        log = (tmp / "log").read_text() if (tmp / "log").exists() else ""
        return r.returncode, r.stdout + r.stderr, log, repo

    def test_default_target_is_x86_64(self):
        rc, out, log, repo = self.run_build([])
        self.assertEqual(rc, 0, out)
        self.assertIn("-Vgcc_ntox86_64 -Werror", log)
        self.assertNotIn("ntoaosdebug", log)
        self.assertTrue((repo / "build" / "x86_64" / "qxprobe-demo").exists())

    def test_aarch64_uses_its_own_variant(self):
        rc, out, log, repo = self.run_build(["aarch64"])
        self.assertEqual(rc, 0, out)
        compiles = [l for l in log.splitlines() if l.startswith("-Vgcc")]
        self.assertEqual(len(compiles), 3)
        self.assertTrue(all(l.startswith("-Vgcc_ntoaarch64le ") for l in compiles))
        self.assertTrue((repo / "build" / "aarch64" / "qxprobe-official").exists())

    def test_missing_variant_stops_before_compiling(self):
        rc, out, log, _ = self.run_build(["aarch64"], variants="gcc_ntox86_64")
        self.assertEqual(rc, 2)
        self.assertIn("gcc_ntoaarch64le is not installed", out)
        self.assertNotIn("-o", log)

    def test_32_bit_target_is_refused(self):
        rc, out, log, _ = self.run_build(["armv7"])
        self.assertEqual(rc, 2)
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)

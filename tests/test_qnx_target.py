#!/usr/bin/env python3
"""The day-of-licence path of scripts/qnx8-proof.sh, tested WITHOUT QNX.

Three pieces are tested here, each with a counter-proof:

  1. scripts/check_qnx_elf.py - reads the ELF header itself.  It must accept
     a QNX 8.0 executable (64-bit, right machine, interpreter ldqnx-*) and
     refuse everything else: a text file, a Linux binary of this machine, a
     static binary, the wrong architecture, a 32-bit file.
  2. scripts/qnx8-target-run.sh - copies and starts the examples on a QNX 8.0
     target over ssh.  Here ssh, scp and mkqnximage are FAKES that record
     what they are asked; this proves the command sequence and the refusals
     (no key, not QNX 8, wrong architecture, path not attached), never a run.
  3. scripts/qnx8-proof.sh - loads qnxsdp-env.sh by itself when qcc is not on
     the PATH, and refuses a "qcc" that produces a Linux binary.

The QNX-looking ELF files are built in a temporary directory by this test,
from a header only: they are not programs and never leave the test.

Run:  python3 -I tests/test_qnx_target.py
"""
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
CHECK = REPO / "scripts" / "check_qnx_elf.py"


def fake_elf(machine=62, interp=b"/usr/lib/ldqnx-64.so.2", bits=2, e_type=3):
    """A minimal ELF header + one PT_INTERP program header (no code)."""
    phoff = 64
    interp_off = phoff + 56
    ident = b"\x7fELF" + bytes([bits, 1, 1, 0]) + b"\0" * 8
    nph = 1 if interp is not None else 0
    hdr = ident + struct.pack("<HHIQQQIHHHHHH", e_type, machine, 1, 0,
                              phoff, 0, 0, 64, 56, nph, 64, 0, 0)
    body = b""
    if interp is not None:
        data = interp + b"\0"
        body = struct.pack("<IIQQQQQQ", 3, 4, interp_off, 0, 0,
                           len(data), len(data), 1) + data
    return hdr + body


def check(arch, *files):
    r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--arch", arch,
                        *map(str, files)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


class ElfCheck(unittest.TestCase):

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, data):
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def test_qnx_x86_64_is_accepted(self):
        rc, out = check("x86_64", self.write("a", fake_elf()))
        self.assertEqual(rc, 0, out)
        self.assertIn("interpreter /usr/lib/ldqnx-64.so.2", out)

    def test_qnx_aarch64_is_accepted_only_as_aarch64(self):
        f = self.write("b", fake_elf(machine=183))
        self.assertEqual(check("aarch64", f)[0], 0)
        rc, out = check("x86_64", f)
        self.assertEqual(rc, 1)
        self.assertIn("machine 183", out)

    def test_linux_interpreter_is_refused(self):
        rc, out = check("x86_64", self.write(
            "c", fake_elf(interp=b"/lib64/ld-linux-x86-64.so.2")))
        self.assertEqual(rc, 1)
        self.assertIn("not the QNX loader", out)

    def test_static_binary_is_refused(self):
        rc, out = check("x86_64", self.write("d", fake_elf(interp=None, e_type=2)))
        self.assertEqual(rc, 1)
        self.assertIn("static", out)

    def test_32_bit_and_text_are_refused(self):
        rc, out = check("x86_64", self.write("e", fake_elf(bits=1)),
                        self.write("f", b"FAKE BINARY - not a QNX compilation\n"))
        self.assertEqual(rc, 1)
        self.assertIn("32-bit", out)
        self.assertIn("is not an ELF file", out)
        self.assertIn("ELF CHECK: 0/2", out)

    def test_a_real_binary_of_this_machine_is_refused(self):
        """Counter-proof on a REAL executable: the host's own python3."""
        real = pathlib.Path(os.path.realpath(sys.executable))
        rc, out = check("x86_64", real)
        self.assertEqual(rc, 1, out)
        self.assertIn("NOT A QNX 8.0 BINARY", out)


FAKE_SSH = r"""#!/bin/sh
cmd="$*"
echo "ssh $*" >> "$T_LOG"
case "$cmd" in
  *uname*) echo "$FAKE_UNAME"; exit 0 ;;
  *"ls -l "*)
    p=$(printf '%s' "$cmd" | sed -n 's/.*if ls -l \([^;]*\);.*/\1/p')
    if [ "$FAKE_ATTACH" = 1 ]; then echo "PATH-ATTACHED $p"; else echo "PATH-ABSENT $p"; fi
    exit 0 ;;
esac
exit 0
"""
FAKE_SCP = """#!/bin/sh
echo "scp $*" >> "$T_LOG"
exit 0
"""
FAKE_MKQNXIMAGE = """#!/bin/sh
echo "mkqnximage $* (in $(pwd))" >> "$T_LOG"
[ "$1" = "--getip" ] && echo "$FAKE_IP"
exit 0
"""


class TargetRun(unittest.TestCase):

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        shutil.copytree(REPO / "scripts", self.repo / "scripts")
        b = self.repo / "build" / "x86_64"
        b.mkdir(parents=True)
        for n in ("qxprobe-demo", "qxprobe-status", "qxprobe-official"):
            (b / n).write_bytes(fake_elf())
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name, text in (("ssh", FAKE_SSH), ("scp", FAKE_SCP),
                           ("mkqnximage", FAKE_MKQNXIMAGE)):
            p = self.bin / name
            p.write_text(text)
            p.chmod(0o755)
        self.key = self.tmp / "id_qnx"
        self.key.write_text("not a real key\n")
        self.qemu = self.tmp / "qemu"
        self.qemu.mkdir()

    def run_target(self, uname="QNX 8.0.0 x86_64", attach="1", key=True,
                   mkqnximage=True, arch="x86_64", ip="10.0.2.15"):
        if not mkqnximage:
            (self.bin / "mkqnximage").unlink()
        env = {"PATH": "%s:/usr/bin:/bin" % self.bin, "HOME": str(self.tmp),
               "T_LOG": str(self.tmp / "log"), "FAKE_UNAME": uname,
               "FAKE_ATTACH": attach, "FAKE_IP": ip,
               "QNX_QEMU_DIR": str(self.qemu)}
        if key:
            env["QNX_SSH_KEY"] = str(self.key)
        r = subprocess.run(["bash", str(self.repo / "scripts" / "qnx8-target-run.sh"),
                            "--arch", arch, "--out", str(self.tmp / "out")],
                           capture_output=True, text=True, env=env, timeout=60)
        log = (self.tmp / "log").read_text() if (self.tmp / "log").exists() else ""
        return r.returncode, r.stdout + r.stderr, log

    def test_happy_path_follows_the_official_procedure(self):
        rc, out, log = self.run_target()
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count("RAN ON QNX 8.0"), 3, out)
        self.assertIn("mkqnximage --getip (in %s)" % self.qemu, log)
        self.assertIn("BatchMode=yes", log)          # never a password prompt
        self.assertIn("root@10.0.2.15", log)
        for p in ("/dev/qxprobe-demo", "/var/run/qxprobe-status", "/dev/qxprobe-official"):
            self.assertIn("ls -l %s;" % p, log)
        self.assertEqual(log.count("scp "), 3)

    def test_no_key_is_not_measured_and_nothing_is_sent(self):
        rc, out, log = self.run_target(key=False)
        self.assertEqual(rc, 3)
        self.assertIn("NOT MEASURED", out)
        self.assertNotIn("ssh ", log)

    def test_no_sdp_and_no_address_is_not_measured(self):
        rc, out, log = self.run_target(mkqnximage=False)
        self.assertEqual(rc, 3)
        self.assertIn("mkqnximage is absent", out)

    def test_vm_not_running_is_not_measured(self):
        rc, out, _ = self.run_target(ip="")
        self.assertEqual(rc, 3)
        self.assertIn("mkqnximage --run=-h", out)

    def test_qnx_7_is_refused(self):
        rc, out, log = self.run_target(uname="QNX 7.1.0 x86_64")
        self.assertEqual(rc, 1)
        self.assertIn("not QNX 8.x", out)
        self.assertNotIn("scp ", log)

    def test_linux_host_is_refused(self):
        rc, out, _ = self.run_target(uname="Linux 6.8.0 x86_64")
        self.assertEqual(rc, 1)

    def test_wrong_architecture_is_refused(self):
        rc, out, log = self.run_target(uname="QNX 8.0.0 aarch64le")
        self.assertEqual(rc, 1)
        self.assertIn("binaries are x86_64", out)
        self.assertNotIn("scp ", log)

    def test_path_not_attached_fails(self):
        rc, out, _ = self.run_target(attach="0")
        self.assertEqual(rc, 1)
        self.assertEqual(out.count("FAILED"), 3)


FAKE_QCC = """#!/usr/bin/env python3
# A FAKE qcc for tests/test_qnx_target.py.  It compiles nothing.
import os, sys
a = sys.argv[1:]
if a == ["-V"]:
    print("cc: targets available:"); print("  12.2.0,gcc_ntox86_64"); sys.exit(0)
out = a[a.index("-o") + 1]
mode = os.environ.get("FAKE_QCC_MODE", "qnx")
if mode == "linux":
    import shutil; shutil.copy(os.path.realpath(sys.executable), out)
else:
    sys.path.insert(0, os.environ["FAKE_QCC_HELPER"])
    from test_qnx_target import fake_elf
    open(out, "wb").write(fake_elf())
"""


class ProofScript(unittest.TestCase):

    def run_proof(self, mode):
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = tmp / "repo"
        for d in ("scripts", "examples"):
            shutil.copytree(REPO / d, repo / d)
        shutil.copy(REPO / "qx_probe.py", repo / "qx_probe.py")
        sdp = tmp / "home" / "qnx800"
        (sdp / "host" / "bin").mkdir(parents=True)
        q = sdp / "host" / "bin" / "qcc"
        q.write_text(FAKE_QCC)
        q.chmod(0o755)
        (sdp / "qnxsdp-env.sh").write_text(
            'QNX_HOST="%s/host"; export QNX_HOST\nPATH="$QNX_HOST/bin:$PATH"; export PATH\n' % sdp)
        env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp / "home"),
               "FAKE_QCC_MODE": mode, "FAKE_QCC_HELPER": str(REPO / "tests")}
        r = subprocess.run(["bash", str(repo / "scripts" / "qnx8-proof.sh"),
                            "--out", str(tmp / "proofs")],
                           capture_output=True, text=True, env=env, timeout=120)
        return r.returncode, r.stdout + r.stderr

    def test_sdp_env_is_sourced_and_a_qnx_elf_passes(self):
        rc, out = self.run_proof("qnx")
        self.assertEqual(rc, 0, out)
        self.assertIn("qnxsdp-env.sh (sourced by this script)", out)
        self.assertIn("ELF CHECK: 3/3", out)
        self.assertIn("the run on a QNX 8.0 target is NOT MEASURED", out)

    def test_a_qcc_that_makes_linux_binaries_is_caught(self):
        rc, out = self.run_proof("linux")
        self.assertEqual(rc, 1, out)
        self.assertIn("ELF CHECK: 0/3", out)
        self.assertIn("VERDICT: FAILED", out)
        self.assertNotIn("THE EXAMPLES BUILD FOR QNX 8.0", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

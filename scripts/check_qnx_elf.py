#!/usr/bin/env python3
"""check_qnx_elf.py - is this file really a QNX 8.0 executable?

WHY THIS SCRIPT EXISTS

`scripts/build_qcc.sh` says "OK" when qcc returns 0.  A return code is not a
binary: a wrapper, a misconfigured PATH or a host gcc named "qcc" would also
return 0.  This script reads the ELF header of each file itself (no `file`,
no `readelf`: only python3) and says whether it is an executable for the QNX
8.0 target that was asked for.

WHAT IT CHECKS, FOR EACH FILE

  1. it is an ELF file, 64-bit, little-endian (QNX 8.0 is 64-bit only);
  2. its machine is the one of the target: x86_64 (EM_X86_64 = 62) or
     aarch64 (EM_AARCH64 = 183);
  3. it is an executable (ET_EXEC or ET_DYN);
  4. its program interpreter is the QNX dynamic loader (a path whose name
     starts with "ldqnx", e.g. /usr/lib/ldqnx-64.so.2).  A Linux binary asks
     for ld-linux; a static binary asks for nothing: both are refused, because
     neither proves that the QNX 8.0 toolchain linked it.

The exact interpreter path written by the SDP 8.0 is printed, so the first
real build records it instead of assuming it.

USAGE

  python3 -I scripts/check_qnx_elf.py --arch x86_64 FILE [FILE ...]

EXIT CODES

  0  every file is a QNX 8.0 executable for that target
  1  at least one file is not (each one is named, with the reason)
  2  bad usage (no file, unknown target)
"""
import struct
import sys

MACHINES = {"x86_64": (62, "x86_64"), "aarch64": (183, "AArch64")}
ET_NAMES = {2: "ET_EXEC", 3: "ET_DYN"}


def inspect(path: str, arch: str) -> tuple[bool, str]:
    """Return (ok, one line that says what the file is)."""
    want_machine, want_name = MACHINES[arch]
    try:
        with open(path, "rb") as f:
            data = f.read(1 << 20)
    except OSError as e:
        return False, "cannot be read (%s)" % e.strerror
    if len(data) < 64 or data[:4] != b"\x7fELF":
        return False, "is not an ELF file (first bytes %r)" % data[:16]
    if data[4] != 2:
        return False, "is a 32-bit ELF (QNX 8.0 is 64-bit only)"
    if data[5] != 1:
        return False, "is a big-endian ELF (QNX 8.0 targets are little-endian)"
    e_type, e_machine = struct.unpack_from("<HH", data, 16)
    e_phoff = struct.unpack_from("<Q", data, 32)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 54)
    if e_machine != want_machine:
        return False, "is built for machine %d, not %s (%d)" % (
            e_machine, want_name, want_machine)
    if e_type not in ET_NAMES:
        return False, "is not an executable (e_type %d)" % e_type
    interp = None
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        if off + 56 > len(data):
            return False, "has a truncated program header table"
        p_type, _flags, p_offset, _va, _pa, p_filesz = struct.unpack_from(
            "<IIQQQQ", data, off)
        if p_type == 3:  # PT_INTERP
            raw = data[p_offset:p_offset + p_filesz]
            interp = raw.split(b"\0", 1)[0].decode("ascii", "replace")
            break
    if interp is None:
        return False, ("has no program interpreter (static): it does not show "
                       "that the QNX 8.0 toolchain linked it")
    base = interp.rsplit("/", 1)[-1]
    if not base.startswith("ldqnx"):
        return False, "asks for the interpreter %s, which is not the QNX loader" % interp
    return True, "ELF64 %s %s, interpreter %s" % (want_name, ET_NAMES[e_type], interp)


def main(argv: list[str]) -> int:
    arch = "x86_64"
    files = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--arch" and i + 1 < len(argv):
            arch = argv[i + 1]
            i += 2
            continue
        if a.startswith("--arch="):
            arch = a.split("=", 1)[1]
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            files.append(a)
        i += 1
    if arch not in MACHINES or not files:
        print("usage: check_qnx_elf.py --arch x86_64|aarch64 FILE [FILE ...]")
        return 2
    bad = 0
    for f in files:
        ok, what = inspect(f, arch)
        if ok:
            print("QNX 8.0 BINARY      %s : %s" % (f, what))
        else:
            print("NOT A QNX 8.0 BINARY %s : %s" % (f, what))
            bad += 1
    print("ELF CHECK: %d/%d file(s) are QNX 8.0 %s executables" % (
        len(files) - bad, len(files), arch))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

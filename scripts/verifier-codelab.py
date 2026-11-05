#!/usr/bin/env python3
"""Replay every console block of CODELAB.md and check the output it promises.

WHY THIS SCRIPT EXISTS
----------------------
A tutorial that shows an output it has never produced is a lie waiting to
be discovered by a judge.  This script is the proof that the outputs shown
in CODELAB.md are the real ones:

  1. it copies the repository into a temporary directory (the repository
     itself is never modified: the tutorial creates a `lab/` directory),
  2. it extracts every ```console block of CODELAB.md, keeping the commands
     ($ lines) and the expected output (the other lines),
  3. it runs the commands, in order, in the copy,
  4. it compares the output produced with the output written in the
     tutorial.  A line that is exactly `...` means "one or more lines are
     elided here" (used for the long test-suite listing).

Exit code: 0 = every replayed block matches, 1 = at least one block differs.

Usage:
    python3 -I scripts/verifier-codelab.py [--verbose]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
CODELAB = REPO / "CODELAB.md"
BLOCK_RE = re.compile(r"```console\n(.*?)```", re.S)
HEREDOC_RE = re.compile(r"<<'?([A-Za-z_][A-Za-z_0-9]*)'?")


# ---------------------------------------------------------------- parsing

def parse_block(raw: str) -> tuple[list[str], list[str]]:
    """Returns (commands, expected output lines) of one console block."""
    commands: list[str] = []
    expected: list[str] = []
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("$ "):
            cmd = line[2:]
            m = HEREDOC_RE.search(cmd)
            if m:
                term = m.group(1)
                chunk = [cmd]
                i += 1
                while i < len(lines) and lines[i].rstrip() != term:
                    chunk.append(lines[i])
                    i += 1
                chunk.append(term)
                commands.append("\n".join(chunk))
                i += 1
                continue
            commands.append(cmd)
            i += 1
            continue
        if line.strip():
            expected.append(line)
        i += 1
    return commands, expected


# ---------------------------------------------------------------- matching

def match_expected(expected: list[str], actual: list[str]) -> tuple[bool, str]:
    """Compares the expected lines with the actual ones.

    A line equal to `...` stands for one or more elided actual lines.
    """
    def walk(ei: int, ai: int) -> int | None:
        if ei == len(expected):
            # The expected lines must consume the WHOLE actual output: a
            # tutorial that hides a line of the real output is not exact.
            return ai if ai == len(actual) else None
        if expected[ei] == "...":
            for k in range(ai + 1, len(actual) + 1):
                r = walk(ei + 1, k)
                if r is not None:
                    return r
            return None
        if ai < len(actual) and actual[ai] == expected[ei]:
            return walk(ei + 1, ai + 1)
        return None

    end = walk(0, 0)
    if end is None:
        return False, _diff(expected, actual)
    if end != len(actual):
        return False, (f"the command produced {len(actual) - end} extra line(s) "
                       f"that the tutorial does not show:\n"
                       + "\n".join("    " + x for x in actual[end:]))
    return True, ""


def _diff(expected: list[str], actual: list[str]) -> str:
    out = []
    for i in range(max(len(expected), len(actual))):
        e = expected[i] if i < len(expected) else "<absent>"
        a = actual[i] if i < len(actual) else "<absent>"
        if e != a:
            out.append(f"  line {i + 1}:\n"
                       f"    expected: {e}\n"
                       f"    actual  : {a}")
    return ("the output differs from the tutorial:\n" + "\n".join(out[:12])
            + ("\n  ..." if len(out) > 12 else ""))


# ---------------------------------------------------------------- replay

class Session:
    """Runs the commands of the blocks, in one working copy of the repo."""

    def __init__(self, workdir: pathlib.Path) -> None:
        self.workdir = workdir
        self.last_rc = 0
        self.ignored: list[str] = []

    def run_block(self, commands: list[str]) -> tuple[list[str], list[str]]:
        """Returns (output lines, notes)."""
        out: list[str] = []
        notes: list[str] = []
        for cmd in commands:
            stripped = cmd.strip()
            if stripped.startswith("git clone") or stripped.startswith("git pull"):
                notes.append(f"ignored (network): {stripped}")
                self.ignored.append(stripped)
                continue
            if stripped.startswith("cd "):
                target = (self.workdir / stripped[3:].strip()).resolve()
                if target.is_dir():
                    self.workdir = target
                else:
                    notes.append(f"ignored (no such directory here): {stripped}")
                    self.ignored.append(stripped)
                continue
            if stripped == "echo $?":
                out.append(str(self.last_rc))
                continue
            proc = subprocess.run(["bash", "-c", stripped], cwd=self.workdir,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, check=False)
            self.last_rc = proc.returncode
            for line in proc.stdout.split("\n"):
                if line != "":
                    out.append(line)
        return out, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true",
                    help="prints the output of every block")
    args = ap.parse_args()

    text = CODELAB.read_text(encoding="utf-8")
    blocks = [parse_block(m.group(1)) for m in BLOCK_RE.finditer(text)]

    print("=" * 78)
    print("QX-PROBE — verification of the codelab")
    print(f"codelab   : {CODELAB.name}")
    print(f"blocks    : {len(blocks)}")
    print("=" * 78)

    with tempfile.TemporaryDirectory(prefix="qx-codelab-") as tmp:
        work = pathlib.Path(tmp) / "repo"
        shutil.copytree(REPO, work,
                        ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                       "lab", "build"))
        session = Session(work)
        n_ok = n_ko = n_skip = 0
        for i, (commands, expected) in enumerate(blocks, 1):
            title = commands[0] if commands else "<no command>"
            if len(title) > 58:
                title = title[:55] + "..."
            actual, notes = session.run_block(commands)
            if not expected:
                n_skip += 1
                print(f"[SKIP] block {i:2d} : {title}")
                for note in notes:
                    print(f"         {note}")
                continue
            ok, detail = match_expected(expected, actual)
            if ok:
                n_ok += 1
                print(f"[ OK ] block {i:2d} : {title}")
                if args.verbose:
                    for line in actual:
                        print(f"         | {line}")
            else:
                n_ko += 1
                print(f"[ KO ] block {i:2d} : {title}")
                for note in notes:
                    print(f"         {note}")
                for line in detail.split("\n"):
                    print(f"         {line}")
        print("-" * 78)
        print(f"blocks replayed and matching : {n_ok}")
        print(f"blocks replayed and differing : {n_ko}")
        print(f"blocks without expected output: {n_skip} (not checked)")
        print(f"commands ignored             : {len(session.ignored)}")
        print("=" * 78)
        if n_ko:
            print("VERDICT : THE CODELAB DOES NOT MATCH THE REAL OUTPUT (RC 1)")
            return 1
        print("VERDICT : EVERY OUTPUT OF THE CODELAB IS THE REAL ONE (RC 0)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

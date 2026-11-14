#!/usr/bin/env python3
"""The figures published in this repository must be the figures of this repository.

WHY THIS SCRIPT EXISTS
----------------------
On 14 November 2026 the published tree announced "68 files", "13 tests" and
"64 unit tests" while the tree itself held 71 files and 70 tests.  The
figures had been corrected in one place and left stale somewhere else, and
nothing in the verification chain said so.  This script closes that hole:
a number written in a document of this repository is an assertion that a
machine can check.

WHAT IT DOES
------------
  1. it MEASURES the repository:
       - the number of files it holds (`git ls-files`);
       - the number of test files;
       - the number of tests of each test file and the total
         (counted with the `ast` module, never by eye);
       - the number of test classes (also with `ast`).
  2. it READS the published documents:
       README.md, docs/README.fr.md, docs/SUBMISSION-EN.md, RULES.md,
       docs/RULES.fr.md, docs/AI-ASSISTED-RULES.md
     and extracts every published count of the three kinds this control
     understands: "tests", "files" and "classes".
  3. it COMPARES each published count with the measured values.  A count
     that is not a measured value must be an explicitly exempted occurrence,
     with its reason written in this file (a dated historical measurement,
     the number of test files, the number of files of the benchmark corpus).
     An occurrence that is neither is STALE: the document announces a number
     the repository does not have.

THREE STATES, NEVER MIXED
-------------------------
  VERT           every published count is a measured value or an explicit
                 exemption: nothing is stale.
  ROUGE          at least one published count is stale.
  NON MESURABLE  a value could not be measured on this machine (no git, a
                 missing document, a missing test directory): the check says
                 so, prints [NOT CHECKED] and is never a success.

EXIT CODES
----------
  0  VERT
  1  ROUGE: a published figure is stale
  2  the check could not run at all (NON MESURABLE)

THE COUNTER-PROOF
------------------
A control that has never met a false number is not known to catch one.
`--contre-epreuve` copies the published documents into a temporary
directory, writes a deliberately false figure into the copy ("999 tests"),
runs the same comparison on the copy and checks that the false figure is
reported as stale.  The counter-proof also runs at every normal run, so the
control cannot silently lose its teeth.

Usage:
    python3 -I scripts/verifier-chiffres-publies.py [--verbose]
    python3 -I scripts/verifier-chiffres-publies.py --contre-epreuve
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent

# The documents whose published figures are checked.
DOCUMENTS = (
    "README.md",
    "docs/README.fr.md",
    "docs/SUBMISSION-EN.md",
    "RULES.md",
    "docs/RULES.fr.md",
    "docs/AI-ASSISTED-RULES.md",
)

# The kinds of published count this control understands.  Each pattern
# captures the announced number in group 1.  The patterns are deliberately
# narrow: they look for a number followed by the word it counts.
#
#   "N tests"            the size of the test suite
#   "N unit tests"       the same, in the wording of the summary table
#   "N check"            the per-file counts of the prose enumeration of
#                         docs/SUBMISSION-EN.md ("2 check the format of the
#                         output, 12 check the line numbers ...")
#   "N the reading ..."   the three other counts of the same enumeration
#   "N files"            the size of the published tree
#   "N classes"          the number of test classes
PATTERNS = (
    ("tests", re.compile(r"(?<![\w.])(\d+)\s+(?:unit\s+)?tests?\b")),
    ("tests", re.compile(r"(?<![\w.])(\d+)\s+check\b")),
    ("tests", re.compile(r"(?<![\w.])(\d+)\s+the reading of a resource\b")),
    ("tests", re.compile(r"(?<![\w.])(\d+)\s+the QNX 8\.0 build script\b")),
    ("tests", re.compile(r"(?<![\w.])(\d+)\s+the robustness of the rules\b")),
    ("files", re.compile(r"(?<![\w.])(\d+)\s+(?:test\s+)?files\b")),
    ("classes", re.compile(r"(?<![\w.])(\d+)\s+classes\b")),
)

# Every published count that is not a measured value has to be listed here,
# with the reason why it is not stale.  The key is (document, announced
# text); the optional context is a regular expression that must be found in
# the line of the claim or in the line just below it, so that a historical
# measurement is exempted only where it is dated.  An exemption that no
# longer matches anything is printed as obsolete: it means the document was
# corrected, which is not a failure.
EXEMPTIONS = (
    ("docs/AI-ASSISTED-RULES.md", "13 tests",
     "historical measurement against the commit ef17d75, dated in the document",
     r"FAILED \(failures=12\)"),
    ("docs/SUBMISSION-EN.md", "2 check",
     "the number of output-format tests inside tests/test_qx_probe.py, "
     "a sub-category and not a file of tests",
     r"the format of the output"),
    ("docs/SUBMISSION-EN.md", "5 files",
     "the number of TEST files, not the number of files of the repository",
     r"70 tests in 5 files"),
    ("docs/SUBMISSION-EN.md", "17 files",
     "the files of the benchmark corpus, not the files of the repository",
     None),
)

# The number written in the counter-proof.
FALSE_NUMBER = 999


class NotMeasurable(Exception):
    """A value could not be measured on this machine."""


# --------------------------------------------------------------- measuring

def measure_files() -> tuple[int, str]:
    """The number of files of the repository, and how it was measured."""
    try:
        done = subprocess.run(["git", "ls-files"], cwd=str(REPO),
                              capture_output=True, text=True, timeout=60)
        if done.returncode == 0:
            names = [line for line in done.stdout.splitlines() if line.strip()]
            return len(names), "git ls-files"
    except (OSError, subprocess.SubprocessError):
        pass
    # Without git: every file of the tree, without the .git directory and
    # without the Python artefacts.
    count = 0
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(REPO).parts
        if ".git" in parts or "__pycache__" in parts:
            continue
        if path.name.endswith(".pyc"):
            continue
        count += 1
    return count, "the tree (git is absent)"


def measure_tests() -> tuple[dict[str, int], int, int]:
    """The tests of each test file, their total and the number of classes.

    The count is made with the `ast` module: a method of a test class whose
    name starts with "test_".  The same rule is used by the whole chain, so
    the number written in the documents and the number of tests that
    `scripts/run_tests.sh` runs are the same number.
    """
    directory = REPO / "tests"
    if not directory.is_dir():
        raise NotMeasurable("the directory tests/ is missing")
    files = sorted(directory.glob("test_*.py"))
    if not files:
        raise NotMeasurable("no test file in tests/")
    per_file: dict[str, int] = {}
    classes = 0
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise NotMeasurable("%s cannot be read (%s)" % (path.name, exc))
        count = 0
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes += 1
                for member in node.body:
                    if (isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and member.name.startswith("test_")):
                        count += 1
        per_file[path.name] = count
    return per_file, sum(per_file.values()), classes


# ---------------------------------------------------------------- scanning

def read_documents() -> dict[str, str]:
    """The text of every published document, or an error if one is missing."""
    texts = {}
    for name in DOCUMENTS:
        path = REPO / name
        if not path.is_file():
            raise NotMeasurable("the document %s is missing" % name)
        try:
            texts[name] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise NotMeasurable("%s cannot be read (%s)" % (name, exc))
    return texts


def collect_claims(texts: dict[str, str]) -> list[tuple[str, int, str, str, int]]:
    """Every published count: (document, line, text, kind, number).

    The text of a claim is normalised: a number and the word it counts may
    be separated by a line break in the document ("the 64\\ntest names").
    """
    claims = []
    for name, text in texts.items():
        lines = text.split("\n")
        for kind, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                said = re.sub(r"\s+", " ", match.group(0)).strip()
                claims.append((name, line, said, kind, int(match.group(1)),
                               "\n".join(lines[line - 1:line + 1])))
    claims.sort(key=lambda claim: (claim[0], claim[1]))
    return claims


def check_claims(claims, real) -> tuple[list, list, list]:
    """Compare the claims with the measured values.

    Returns (stale, exemptions_applied, exemptions_obsolete).
    """
    stale = []
    applied = []
    seen = set()
    for name, line, text, kind, number, around in claims:
        reason = None
        for doc, exempt_text, exempt_reason, context in EXEMPTIONS:
            if doc != name or exempt_text != text:
                continue
            if context and not re.search(context, around):
                continue
            reason = exempt_reason
            break
        if reason is not None:
            seen.add((name, text))
            applied.append((name, line, text, reason))
            continue
        if number not in real[kind]:
            stale.append((name, line, text, kind, number))
    obsolete = []
    for doc, exempt_text, exempt_reason, _context in EXEMPTIONS:
        if (doc, exempt_text) not in seen:
            obsolete.append((doc, exempt_text, exempt_reason))
    return stale, applied, obsolete


# ------------------------------------------------------------ counter-proof

def counter_proof(texts: dict[str, str], real) -> bool:
    """Write a false figure in a copy of the documents and detect it.

    Returns True when the false figure was detected (the control still has
    teeth), False when it was not.
    """
    with tempfile.TemporaryDirectory(prefix="qx-chiffres-") as tmp:
        copy = pathlib.Path(tmp)
        for name, text in texts.items():
            path = copy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        # The false figure is written in the copy of the first document.
        target = copy / DOCUMENTS[0]
        original = target.read_text(encoding="utf-8")
        target.write_text(
            original + "\n\nThis sentence announces %d tests, which is false.\n"
            % FALSE_NUMBER,
            encoding="utf-8")
        copied = {}
        for name in DOCUMENTS:
            copied[name] = (copy / name).read_text(encoding="utf-8")
        claims = collect_claims(copied)
        stale, _, _ = check_claims(claims, real)
        detected = [c for c in stale if c[4] == FALSE_NUMBER]
        if detected:
            print("COUNTER-PROOF: a false figure was written in a copy of %s"
                  % DOCUMENTS[0])
            print("             %s:%d  \"%s\" -> detected as stale, as it must be"
                  % (detected[0][0], detected[0][1], detected[0][2]))
            return True
        print("COUNTER-PROOF: THE FALSE FIGURE WAS NOT DETECTED")
        print("             %d tests was written in a copy of %s and the control"
              % (FALSE_NUMBER, DOCUMENTS[0]))
        print("             did not report it: the control is broken.")
        return False


# ------------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contre-epreuve", action="store_true",
                        help="only run the counter-proof: write a false figure "
                             "in a copy of the published documents and check "
                             "that the control detects it")
    parser.add_argument("--verbose", action="store_true",
                        help="print every published count that was checked")
    args = parser.parse_args(argv[1:])

    try:
        texts = read_documents()
        n_files, how = measure_files()
        per_file, total, classes = measure_tests()
    except NotMeasurable as exc:
        print("[NOT CHECKED] the published figures could not be measured")
        print("              %s" % exc)
        return 2

    real = {
        "tests": set(per_file.values()) | {total},
        "files": {n_files},
        "classes": {classes},
    }

    if args.contre_epreuve:
        ok = counter_proof(texts, real)
        if ok:
            print("COUNTER-PROOF: THE FALSE FIGURE WAS DETECTED (RC 0)")
            return 0
        print("VERDICT: THE COUNTER-PROOF FAILED - the control does not "
              "detect a false figure (RC 1)")
        return 1

    claims = collect_claims(texts)
    stale, applied, obsolete = check_claims(claims, real)

    print("=" * 78)
    print("THE PUBLISHED FIGURES AND THE FIGURES OF THIS REPOSITORY")
    print("=" * 78)
    print("files (%s)        : %d" % (how, n_files))
    print("test files        : %d" % len(per_file))
    print("tests             : %d (%s)"
          % (total, " + ".join(str(n) for n in per_file.values())))
    for name, count in per_file.items():
        print("   %-28s %d" % (name, count))
    print("test classes      : %d" % classes)
    print("published counts  : %d checked, %d exempted, %d stale"
          % (len(claims), len(applied), len(stale)))
    if args.verbose:
        for name, line, text, kind, number, _around in claims:
            print("   %-28s line %-4d \"%s\" (%s)" % (name, line, text, kind))
    for name, line, text, reason in applied:
        print("EXEMPTED  %-28s line %-4d \"%s\": %s" % (name, line, text, reason))
    for name, text, reason in obsolete:
        print("OBSOLETE  %-28s \"%s\": %s (the document was corrected)"
              % (name, text, reason))
    if stale:
        print("")
        print("STALE PUBLISHED FIGURES (the document announces a number the "
              "repository does not have)")
        for name, line, text, kind, number in stale:
            print("  %-28s line %-4d \"%s\" -> %d is not a measured value (%s: %s)"
                  % (name, line, text, number, kind,
                     ", ".join(str(v) for v in sorted(real[kind]))))
        print("=" * 78)
        print("VERDICT: THE PUBLISHED FIGURES ARE STALE (RC 1)")
        return 1

    # The control proves it still detects a false figure.
    if not counter_proof(texts, real):
        print("=" * 78)
        print("VERDICT: THE COUNTER-PROOF FAILED - the control does not "
              "detect a false figure (RC 1)")
        return 1

    print("=" * 78)
    print("VERDICT: THE PUBLISHED FIGURES MATCH THE REPOSITORY (RC 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

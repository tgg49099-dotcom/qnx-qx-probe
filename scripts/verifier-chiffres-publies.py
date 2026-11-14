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
     and, since the second version, everything else the documents count:
       - the cited official pages and their quotations (read from the
         CITATIONS table of scripts/verifier-citations.py with `ast`,
         without the network);
       - the console blocks of docs/CODELAB.md and the marked blocks of
         docs/SUBMISSION-EN.md (the blocks the two replay scripts replay);
       - the rules of the linter (the distinct QX codes it can report);
       - the lines of qx_probe.py;
       - the checks of scripts/verify-all.sh (its `check` calls);
       - the duration and the size of the published video, read in the MP4
         header itself (the `mvhd` box), so neither ffprobe nor any library
         is needed.
  2. it READS the published documents:
       README.md, docs/README.fr.md, docs/SUBMISSION-EN.md, RULES.md,
       docs/RULES.fr.md, docs/AI-ASSISTED-RULES.md
     and extracts every published count of the kinds this control
     understands: "tests", "files", "classes", "quotations", "pages",
     "blocks", "rules", "lines", "checks", "seconds" (the duration of the
     video) and "bytes" (its size).
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
directory, writes one deliberately false figure OF EACH KIND into the copy
("999 tests", "999 quotations", "99.99 s", ...), runs the same comparison
on the copy and checks that every false figure is reported as stale: a
kind whose false figure goes unnoticed fails the counter-proof.  The same
counter-proof is a test of the suite (tests/test_published_figures.py).  The counter-proof also runs at every normal run, so the
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
    # The second version: everything else the documents count.
    #   "N quotations", "N re-read quotations", "N citations" (French)
    ("quotations", re.compile(r"(?<![\w./])(\d+)\s+(?:re-read\s+)?quotations?\b")),
    ("quotations", re.compile(r"(?<![\w./])(\d+)\s+citations\b")),
    #   "N pages", "N cited pages", "N official pages"
    ("pages", re.compile(r"(?<![\w./])(\d+)\s+(?:cited\s+|official\s+)?pages?\b")),
    #   "N blocks", "N console blocks", "N blocs" (French)
    ("blocks", re.compile(r"(?<![\w./])(\d+)\s+(?:console\s+)?(?:blocks|blocs)\b")),
    #   "N rules", "N regles" (French)
    ("rules", re.compile(r"(?<![\w./])(\d+)\s+(?:rules|r[eè]gles)\b")),
    #   "N lines", "N lignes" (French): the size of the linter
    ("lines", re.compile(r"(?<![\w./])(\d+)\s+(?:lines|lignes)\b")),
    #   "N checks", "N controles", and the "N/M OK" of a verify-all verdict
    #   (the M is the number of checks)
    ("checks", re.compile(r"(?<![\w./])(\d+)\s+(?:checks|contr[oô]les)\b")),
    ("checks", re.compile(r"(?<![\w./])\d+/(\d+)\s+OK\b")),
    #   "N.NN s": a duration written to the hundredth of a second is the
    #   duration of the video (the other ones are exempted below)
    ("seconds", re.compile(r"(?<![\w./,])(\d+[.,]\d\d)\s+s\b")),
    #   "N NNN NNN bytes": the size of the video
    ("bytes", re.compile(r"(?<![\w./])(\d{1,3}(?:[   ]\d{3})+|\d+)\s+bytes\b")),
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
    ("docs/SUBMISSION-EN.md", "6 files",
     "the number of TEST files, not the number of files of the repository",
     r"79 tests in 6 files"),
    ("docs/SUBMISSION-EN.md", "17 files",
     "the files of the benchmark corpus, not the files of the repository",
     None),
    # The second version.
    ("RULES.md", "37 pages",
     "the pages of the official guide 'Writing a Resource Manager' measured "
     "for QX001, not the pages cited by the rules",
     r"of that guide|Writing a Resource Manager"),
    ("RULES.md", "160 476 bytes",
     "the size of the saved copy of the contest rules page, dated in the "
     "document",
     r"saved copy"),
    ("RULES.md", "3.12 s",
     "the shortest scene of the video, not its duration",
     r"scene"),
    ("docs/RULES.fr.md", "3,12 s",
     "the shortest scene of the video, not its duration",
     r"sc[eè]ne"),
    ("README.md", "436 lines",
     "the length of the log of the dated verify-all run, not the size of "
     "the linter",
     r"for the run"),
    ("docs/README.fr.md", "436 lignes",
     "the length of the log of the dated verify-all run, not the size of "
     "the linter",
     r"pour le premier"),
    ("docs/SUBMISSION-EN.md", "2.13 s",
     "a timing of the test suite on the machine of the measurement, dated, "
     "not the duration of the video",
     r"Measured|test suite"),
    ("docs/SUBMISSION-EN.md", "0.09 s",
     "a timing of one run of the linter, dated, not the duration of the video",
     r"Measured|run on one file"),
)

# The number written in the counter-proof: one false figure of each kind.
FALSE_NUMBER = 999
FALSE_FIGURES = (
    ("tests", "999 tests"),
    ("files", "999 files"),
    ("classes", "999 classes"),
    ("quotations", "999 quotations"),
    ("pages", "999 pages"),
    ("blocks", "999 blocks"),
    ("rules", "999 rules"),
    ("lines", "999 lines"),
    ("checks", "999 checks"),
    ("seconds", "99.99 s"),
    ("bytes", "9 999 999 bytes"),
)

# The published video whose duration and size are published.
VIDEO = "media/qx-demo-v2.mp4"


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


def _read(relative: str) -> str:
    path = REPO / relative
    if not path.is_file():
        raise NotMeasurable("%s is missing" % relative)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NotMeasurable("%s cannot be read (%s)" % (relative, exc))


def measure_citations() -> tuple[int, int]:
    """(pages, quotations) of the CITATIONS table of verifier-citations.py.

    The table is read with `ast` (literal_eval), never imported and never
    run: the measure needs no network.
    """
    source = _read("scripts/verifier-citations.py")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise NotMeasurable("verifier-citations.py cannot be parsed (%s)" % exc)
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif (isinstance(node, ast.Assign) and len(node.targets) == 1
              and isinstance(node.targets[0], ast.Name)):
            target = node.targets[0].id
        if target != "CITATIONS" or node.value is None:
            continue
        try:
            table = ast.literal_eval(node.value)
        except ValueError as exc:
            raise NotMeasurable("the CITATIONS table is not a literal (%s)" % exc)
        return len(table), sum(len(entry[2]) for entry in table)
    raise NotMeasurable("no CITATIONS table in verifier-citations.py")


def measure_blocks() -> tuple[int, int]:
    """(codelab console blocks, marked blocks of the submission text).

    The two expressions are the ones of the two replay scripts
    (verifier-codelab.py and verifier-soumission-devpost.py).
    """
    # A codelab block is replayed when it prints an expected output; the
    # blocks without one are "not checked" by the replay and not counted.
    # The parser is the replay script's own (imported, never run).
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "qx_verifier_codelab", str(REPO / "scripts" / "verifier-codelab.py"))
    if spec is None or spec.loader is None or not (REPO / "scripts" / "verifier-codelab.py").is_file():
        raise NotMeasurable("scripts/verifier-codelab.py is missing")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True   # never leave __pycache__ in scripts/
    spec.loader.exec_module(module)
    codelab = sum(1 for match in module.BLOCK_RE.finditer(_read("docs/CODELAB.md"))
                  if module.parse_block(match.group(1))[1])
    devpost = len(re.findall(r"<!-- DEBUT:(\w+) -->\n(.*?)<!-- FIN:\1 -->",
                             _read("docs/SUBMISSION-EN.md"), re.S))
    return codelab, devpost


def measure_rules() -> int:
    """The number of distinct QX codes the linter can report."""
    codes = set(re.findall(r'Finding\(\s*"(?:ERROR|WARN|INFO)",\s*"(QX\d{3})"',
                           _read("qx_probe.py")))
    if not codes:
        raise NotMeasurable("no rule found in qx_probe.py")
    return len(codes)


def measure_lines() -> int:
    """The number of lines of qx_probe.py, as `wc -l` counts them."""
    return _read("qx_probe.py").count("\n")


def measure_checks() -> int:
    """The number of checks of scripts/verify-all.sh (its `check` calls)."""
    return len(re.findall(r'^check "', _read("scripts/verify-all.sh"), re.M))


def measure_video() -> tuple[str, int]:
    """(duration to the hundredth of a second, size in bytes) of the video.

    The duration is read in the `mvhd` box of the MP4 file (timescale and
    duration), which is what ffprobe reports as the format duration.
    """
    path = REPO / VIDEO
    if not path.is_file():
        raise NotMeasurable("%s is missing" % VIDEO)
    data = path.read_bytes()
    at = data.find(b"mvhd")
    if at < 4 or at + 36 > len(data):
        raise NotMeasurable("no mvhd box in %s" % VIDEO)
    version = data[at + 4]
    if version == 1:
        timescale = int.from_bytes(data[at + 24:at + 28], "big")
        duration = int.from_bytes(data[at + 28:at + 36], "big")
    else:
        timescale = int.from_bytes(data[at + 16:at + 20], "big")
        duration = int.from_bytes(data[at + 20:at + 24], "big")
    if timescale == 0:
        raise NotMeasurable("the mvhd box of %s has no timescale" % VIDEO)
    return "%.2f" % (duration / timescale), len(data)


def normalise(number: str) -> str:
    """One spelling per number: no thousands separator, a decimal point."""
    text = re.sub(r"[   ]", "", number).replace(",", ".")
    return text if "." in text else str(int(text))


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
                claims.append((name, line, said, kind, normalise(match.group(1)),
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

def counter_proof(texts: dict[str, str], real, quiet: bool = False) -> bool:
    """Write one false figure of each kind in a copy of the documents.

    Returns True when every false figure was detected (the control still
    has teeth for every kind), False when one of them was not.
    """
    with tempfile.TemporaryDirectory(prefix="qx-chiffres-") as tmp:
        copy = pathlib.Path(tmp)
        for name, text in texts.items():
            path = copy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        # The false figures are written in the copy of the first document,
        # one sentence each.
        target = copy / DOCUMENTS[0]
        original = target.read_text(encoding="utf-8")
        added = "".join("\n\nThis sentence announces %s, which is false.\n" % said
                        for _kind, said in FALSE_FIGURES)
        target.write_text(original + added, encoding="utf-8")
        copied = {}
        for name in DOCUMENTS:
            copied[name] = (copy / name).read_text(encoding="utf-8")
        claims = collect_claims(copied)
        stale, _, _ = check_claims(claims, real)
        first_new_line = original.count("\n") + 1
        missed = []
        for kind, said in FALSE_FIGURES:
            hit = [c for c in stale if c[0] == DOCUMENTS[0] and c[1] > first_new_line
                   and c[3] == kind and c[2] == said]
            if not quiet:
                print("COUNTER-PROOF: %-10s \"%s\" written in a copy of %s -> %s"
                      % (kind, said, DOCUMENTS[0],
                         "detected as stale, as it must be" if hit else "NOT DETECTED"))
            if not hit:
                missed.append(said)
        if missed and not quiet:
            print("COUNTER-PROOF: THE FALSE FIGURE WAS NOT DETECTED: %s"
                  % ", ".join(missed))
            print("             the control is broken for these kinds.")
        return not missed


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
        pages, quotations = measure_citations()
        codelab_blocks, devpost_blocks = measure_blocks()
        rules = measure_rules()
        lines = measure_lines()
        checks = measure_checks()
        seconds, size = measure_video()
    except NotMeasurable as exc:
        print("[NOT CHECKED] the published figures could not be measured")
        print("              %s" % exc)
        return 2

    real = {
        "tests": {str(n) for n in per_file.values()} | {str(total)},
        "files": {str(n_files)},
        "classes": {str(classes)},
        "quotations": {str(quotations)},
        "pages": {str(pages)},
        "blocks": {str(codelab_blocks), str(devpost_blocks)},
        "rules": {str(rules)},
        "lines": {str(lines)},
        "checks": {str(checks)},
        "seconds": {seconds},
        "bytes": {str(size)},
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
    print("cited pages       : %d (scripts/verifier-citations.py)" % pages)
    print("quotations        : %d" % quotations)
    print("blocks            : %d (docs/CODELAB.md), %d (docs/SUBMISSION-EN.md)"
          % (codelab_blocks, devpost_blocks))
    print("rules             : %d (distinct QX codes of qx_probe.py)" % rules)
    print("lines             : %d (qx_probe.py)" % lines)
    print("checks            : %d (scripts/verify-all.sh)" % checks)
    print("video             : %s s, %d bytes (%s, mvhd box)" % (seconds, size, VIDEO))
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
            print("  %-28s line %-4d \"%s\" -> %s is not a measured value (%s: %s)"
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

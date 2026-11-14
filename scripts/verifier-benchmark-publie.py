#!/usr/bin/env python3
"""The benchmark published in docs/BENCHMARK.md must be the real output of the benchmark.

WHY THIS SCRIPT EXISTS
----------------------
Section 4 of docs/BENCHMARK.md and docs/BENCHMARK.fr.md publishes the
measurement of scripts/benchmark-corpus.py twice: a table (one row per file
of the corpus: findings, ERROR, WARN, exit code), the total line in bold, and
an extract of the console output.  Until 14 November 2026 that extract was
typed: its lines did not have the spacing the script prints, so a reader who
ran the command could not compare it line by line, and nothing re-ran the
command to check the table either.  A table that a machine does not replay
is a claim, not a measurement.

WHAT IT DOES
------------
  1. it RUNS the benchmark (`scripts/benchmark-corpus.py`, the very command
     the documents print), or reads a saved output with --sortie;
  2. it READS section 4 of the two documents, between the markers
       <!-- BENCH:TABLE -->   ... <!-- /BENCH:TABLE -->
       <!-- BENCH:CONSOLE --> ... <!-- /BENCH:CONSOLE -->
  3. it COMPARES:
       - every row of the table (findings, ERROR, WARN, exit code) with the
         row of the same file in the real output, and the number of rows;
       - the bold total line ("17/17 files analysed, 1 ERROR in total");
       - the console extract, which must be EXACTLY the extract this script
         builds from the real output: the command, every file that carries
         an ERROR or a WARN with its findings (with the spacing the script
         prints), the total line and the verdict; "..." stands for the
         lines without a finding.
  --regenerer writes the real table and the real extract into the two
  documents (between the markers) instead of comparing them.

THREE STATES, NEVER MIXED
-------------------------
  VERT           the published benchmark is the real output.
  ROUGE          a row, the total or a line of the extract differs.
  NON MESURABLE  the benchmark could not run (no network, no git): the check
                 prints [NOT CHECKED] and is never a success.

EXIT CODES
----------
  0  VERT
  1  ROUGE
  2  NON MESURABLE

THE COUNTER-PROOF
------------------
At every run (and alone with --contre-epreuve), a copy of each document is
falsified twice - one ERROR cell of the table, one line of the extract -
and the same comparison must report both.  The same counter-proof is a test
of the suite (tests/test_published_figures.py), on a saved output, without
the network.

Usage:
    python3 -I scripts/verifier-benchmark-publie.py
    python3 -I scripts/verifier-benchmark-publie.py --regenerer
    python3 -I scripts/verifier-benchmark-publie.py --sortie saved-output.txt
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

DOCUMENTS = {
    "docs/BENCHMARK.md": {
        "total": re.compile(r"\*\*(\d+)/(\d+) files analysed, (\d+) ERROR in total\.\*\*"),
        "total_text": "**%d/%d files analysed, %d ERROR in total.**",
    },
    "docs/BENCHMARK.fr.md": {
        "total": re.compile(r"\*\*(\d+)/(\d+) fichiers analyses, (\d+) ERROR au total\.\*\*"),
        "total_text": "**%d/%d fichiers analyses, %d ERROR au total.**",
    },
}

COMMAND = "python3 -I scripts/benchmark-corpus.py"
ENTRY_RE = re.compile(r"^(\S+)\s+(\d+) finding\(s\), (\d+) ERROR, (\d+) WARN \(exit (\d+)\)$")
TOTAL_RE = re.compile(r"^(\d+)/(\d+) files analysed, (\d+) ERROR in total$")
ROW_RE = re.compile(r"^\| (\d+) \| (.+?) \| (\d+) \| (\*\*)?(\d+)(?:\*\*)? \| "
                    r"(\*\*)?(\d+)(?:\*\*)? \| (\*\*)?(\d+)(?:\*\*)? \|$")


class NotMeasurable(Exception):
    """The benchmark could not run on this machine."""


class Malformed(Exception):
    """A document has lost its markers or its table: a fault of the repository."""


# ------------------------------------------------------------ the real run

def run_benchmark() -> str:
    try:
        done = subprocess.run([sys.executable, "-I", "-B",
                               str(REPO / "scripts" / "benchmark-corpus.py")],
                              cwd=str(REPO), capture_output=True, text=True,
                              timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        raise NotMeasurable("the benchmark could not be started (%s)" % exc)
    if done.returncode == 2:
        raise NotMeasurable("the corpus could not be fetched (network or git absent)")
    if done.returncode != 0:
        raise NotMeasurable("the benchmark ended with code %d" % done.returncode)
    return done.stdout


def parse_output(text: str) -> dict:
    """The entries, the total and the verdict of a benchmark output."""
    entries = []
    total = verdict = None
    for line in text.split("\n"):
        line = line.rstrip()
        m = ENTRY_RE.match(line)
        if m:
            entries.append({"line": line, "label": m.group(1),
                            "findings": int(m.group(2)), "error": int(m.group(3)),
                            "warn": int(m.group(4)), "exit": int(m.group(5)),
                            "details": []})
            continue
        if line.startswith("    ") and entries:
            entries[-1]["details"].append(line)
            continue
        m = TOTAL_RE.match(line)
        if m:
            total = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if line.startswith("VERDICT:"):
            verdict = line
    if not entries or total is None or verdict is None:
        raise NotMeasurable("the output of the benchmark is not complete")
    return {"entries": entries, "total": total, "verdict": verdict}


def build_console(real: dict) -> str:
    """The extract: the command, the files with a finding, the total."""
    out = ["```console", "$ " + COMMAND]
    previous_shown = False
    for entry in real["entries"]:
        if entry["error"] or entry["warn"]:
            out.append("...")
            out.append(entry["line"])
            out.extend(entry["details"])
            previous_shown = True
        else:
            previous_shown = False
    if not previous_shown:
        out.append("...")
    out.append("")
    out.append("%d/%d files analysed, %d ERROR in total" % real["total"])
    out.append(real["verdict"])
    out.append("```")
    return "\n".join(out)


# ------------------------------------------------------------- documents

def section(text: str, name: str, document: str) -> tuple[int, int]:
    start = "<!-- BENCH:%s -->\n" % name
    end = "<!-- /BENCH:%s -->" % name
    a = text.find(start)
    b = text.find(end)
    if a < 0 or b < 0 or b < a:
        raise Malformed("%s: the markers BENCH:%s are missing" % (document, name))
    return a + len(start), b


def compare(document: str, text: str, real: dict) -> list[str]:
    """Every difference between a document and the real output."""
    spec = DOCUMENTS[document]
    errors = []
    a, b = section(text, "TABLE", document)
    rows = [ROW_RE.match(line) for line in text[a:b].split("\n")
            if line.startswith("| ") and ROW_RE.match(line)]
    entries = real["entries"]
    if len(rows) != len(entries):
        errors.append("%s: the table has %d rows, the benchmark has %d files"
                      % (document, len(rows), len(entries)))
    for row, entry in zip(rows, entries):
        said = (int(row.group(3)), int(row.group(5)), int(row.group(7)), int(row.group(9)))
        measured = (entry["findings"], entry["error"], entry["warn"], entry["exit"])
        if said != measured:
            errors.append("%s: row %s (%s) says %s findings/ERROR/WARN/exit, "
                          "the benchmark prints %s"
                          % (document, row.group(1), entry["label"],
                             "/".join(map(str, said)), "/".join(map(str, measured))))
    totals = spec["total"].findall(text[a:b])
    if len(totals) != 1:
        errors.append("%s: the bold total line is missing" % document)
    elif tuple(map(int, totals[0])) != real["total"]:
        errors.append("%s: the total says %s, the benchmark prints %s"
                      % (document, "/".join(totals[0]),
                         "/".join(map(str, real["total"]))))
    a, b = section(text, "CONSOLE", document)
    published = text[a:b].strip("\n")
    expected = build_console(real)
    if published != expected:
        pub_lines = published.split("\n")
        exp_lines = expected.split("\n")
        for i in range(max(len(pub_lines), len(exp_lines))):
            p = pub_lines[i] if i < len(pub_lines) else "<nothing>"
            e = exp_lines[i] if i < len(exp_lines) else "<nothing>"
            if p != e:
                errors.append("%s: line %d of the extract differs from the real output\n"
                              "      published: %s\n      real     : %s"
                              % (document, i + 1, p[:110], e[:110]))
                break
    return errors


def regenerate(document: str, text: str, real: dict) -> str:
    """The document with the real table and the real extract."""
    spec = DOCUMENTS[document]
    a, b = section(text, "TABLE", document)
    lines = text[a:b].split("\n")
    index = 0
    for i, line in enumerate(lines):
        row = ROW_RE.match(line)
        if not row:
            continue
        if index >= len(real["entries"]):
            raise Malformed("%s: the table has more rows than the benchmark" % document)
        entry = real["entries"][index]
        index += 1
        name = row.group(2).strip("*")
        hit = entry["error"] or entry["warn"]
        cell = lambda n: ("**%d**" % n) if n else "%d" % n
        lines[i] = "| %s | %s | %d | %s | %s | %s |" % (
            row.group(1), ("**%s**" % name) if hit else name, entry["findings"],
            cell(entry["error"]), cell(entry["warn"]), cell(entry["exit"]))
    if index != len(real["entries"]):
        raise Malformed("%s: the table has %d rows, the benchmark has %d files"
                        % (document, index, len(real["entries"])))
    block = spec["total"].sub(spec["total_text"] % real["total"], "\n".join(lines))
    text = text[:a] + block + text[b:]
    a, b = section(text, "CONSOLE", document)
    return text[:a] + build_console(real) + "\n" + text[b:]


# ------------------------------------------------------------ counter-proof

def falsify(text: str, document: str) -> list[tuple[str, str]]:
    """Two falsified copies: one ERROR cell, one line of the extract."""
    copies = []
    a, b = section(text, "TABLE", document)
    block = text[a:b]
    m = re.search(r"^(\| \d+ \| .+? \| \d+ \| )(\*\*)?(\d+)", block, re.M)
    if m:
        false = str(int(m.group(3)) + 7)
        copies.append(("an ERROR cell of the table",
                       text[:a] + block[:m.start(3)] + false + block[m.end(3):] + text[b:]))
    a, b = section(text, "CONSOLE", document)
    block = text[a:b]
    m = re.search(r"(\d+) finding\(s\)", block)
    if m:
        false = str(int(m.group(1)) + 7)
        copies.append(("a line of the extract",
                       text[:a] + block[:m.start(1)] + false + block[m.end(1):] + text[b:]))
    return copies


def counter_proof(texts: dict[str, str], real: dict, quiet: bool = False) -> bool:
    ok = True
    for document, text in texts.items():
        copies = falsify(text, document)
        if len(copies) != 2:
            ok = False
            if not quiet:
                print("COUNTER-PROOF: %s cannot be falsified (table or extract missing)"
                      % document)
            continue
        for what, copy in copies:
            detected = bool(compare(document, copy, real))
            ok = ok and detected
            if not quiet:
                print("COUNTER-PROOF: %s falsified in a copy of %s -> %s"
                      % (what, document,
                         "detected, as it must be" if detected else "NOT DETECTED"))
    return ok


# ------------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sortie", help="read a saved output of benchmark-corpus.py "
                                         "instead of running it")
    parser.add_argument("--regenerer", action="store_true",
                        help="write the real table and extract into the documents")
    parser.add_argument("--contre-epreuve", action="store_true",
                        help="only run the counter-proof")
    args = parser.parse_args(argv[1:])

    print("=" * 78)
    print("THE PUBLISHED BENCHMARK AND THE REAL OUTPUT OF THE BENCHMARK")
    print("=" * 78)
    try:
        texts = {}
        for document in DOCUMENTS:
            path = REPO / document
            if not path.is_file():
                print("%s is missing: the repository is incomplete (RC 1)" % document)
                return 1
            texts[document] = path.read_text(encoding="utf-8")
        if args.sortie:
            raw = pathlib.Path(args.sortie).read_text(encoding="utf-8")
            source = "the saved output %s" % args.sortie
        else:
            raw = run_benchmark()
            source = "a real run of " + COMMAND
        real = parse_output(raw)
    except NotMeasurable as exc:
        print("[NOT CHECKED] the published benchmark could not be compared")
        print("              %s" % exc)
        return 2
    print("source            : %s" % source)
    print("files measured    : %d" % len(real["entries"]))
    print("total             : %d/%d files analysed, %d ERROR in total" % real["total"])

    try:
        if args.regenerer:
            for document, text in texts.items():
                new = regenerate(document, text, real)
                (REPO / document).write_text(new, encoding="utf-8")
                print("REGENERATED %s (%s)" % (document,
                                               "changed" if new != text else "unchanged"))
            return 0
        if args.contre_epreuve:
            if counter_proof(texts, real):
                print("COUNTER-PROOF: EVERY FALSIFICATION WAS DETECTED (RC 0)")
                return 0
            print("VERDICT: THE COUNTER-PROOF FAILED (RC 1)")
            return 1
        errors = []
        for document, text in texts.items():
            found = compare(document, text, real)
            errors.extend(found)
            print("%-22s %s" % (document, "the table, the total and the extract are "
                                          "the real output" if not found else
                                          "%d difference(s)" % len(found)))
    except Malformed as exc:
        print("THE DOCUMENT IS MALFORMED: %s (RC 1)" % exc)
        return 1
    if errors:
        print("")
        for line in errors:
            print("  " + line)
        print("=" * 78)
        print("VERDICT: THE PUBLISHED BENCHMARK IS NOT THE REAL OUTPUT (RC 1)")
        print("         python3 -I scripts/verifier-benchmark-publie.py --regenerer "
              "writes the real one")
        return 1
    if not counter_proof(texts, real):
        print("=" * 78)
        print("VERDICT: THE COUNTER-PROOF FAILED (RC 1)")
        return 1
    print("=" * 78)
    print("VERDICT: THE PUBLISHED BENCHMARK IS THE REAL OUTPUT (RC 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

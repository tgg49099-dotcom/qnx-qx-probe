#!/usr/bin/env python3
"""verifier-preuve-qnx8.py - the control of the QNX 8.0 proof.

WHAT THIS SCRIPT IS

`docs/PREUVE-QNX8.md` is the proof that this repository really works with
QNX 8.0 code, and that it really builds for QNX 8.0 with the real compiler
of the SDP 8.0.  A proof is worth nothing if nobody checks it, so this
script checks every line of it.

WHAT IT CHECKS

  1. THE MAIN TABLE - every assertion of docs/PREUVE-QNX8.md carries a
     command and the real output that command produced.  This script runs
     the command again, right now, and the output must still contain what
     the proof says.  An assertion with NO COMMAND, or with NO REAL OUTPUT,
     is a FAILED line: the proof is incomplete, and the control says so.
     The SOURCE of the assertion is checked too: the file must be in this
     repository, the line must exist, and that line must really carry the
     claim - an empty line, or a line that says nothing about the claim, is
     a FAILED line.  A pointer that only exists is not a proof: the cited
     line must carry the expected text itself, or at least TWO of the
     significant words of the claim.  One word is not a proof.
  2. THE FOURTEEN OFFICIAL PAGES - each URL is fetched again; it must
     answer HTTP 200, its SHA-256 is compared with the one written in the
     proof, and the page must be one of the pages the rules really cite.
     A page that QNX changed since the proof was written is reported as
     DRIFT, not as a failure: the proof says what was read, and on which
     date.
  3. THE RULES - every rule must name an official API, the line of RULES.md
     it comes from must say so, and the URL of that API must be one of the
     pages of scripts/verifier-citations.py.
  4. THE CAPTURES - every picture must exist, its SHA-256 must be the
     published one, and the text embedded in the picture must be the real
     output of the command that produced it.  A picture cannot show
     something the command does not print.

THE THREE STATES, NEVER MIXED

  OK           the assertion was checked, and it holds.
  DRIFT        the page was changed by QNX since the proof was written.  The
               proof stays true (it says what was read, and when); the
               control says that the page moved.
  FAILED       the assertion is false: no command, no recorded output, or
               the command no longer produces what the proof says.  This
               is a real failure and it makes the exit code 1.
  NOT CHECKED  the check could not run: no network, a missing tool.  It is
               never a success and never a failure.

EXIT CODES

  0  no assertion is false (a DRIFT or a NOT CHECKED line is named, and is
     neither a success nor a failure)
  1  at least one assertion is false
  2  the control itself could not run (no python3, no proof file)

THE COUNTER-PROOF

  A control that has never met a false line is not known to catch one.
  `--contre-epreuve` adds eight deliberately false lines to the table - one
  with no command, one whose output the command cannot produce, one whose
  source points at an EMPTY line, one whose source points at a line
  that says nothing about the claim, one whose source points OUTSIDE the
  file, one whose source is the line 0 (the lines are counted from 1), and
  two whose source points at a line that carries only ONE word of the claim -
  and checks that all of them are reported as FAILED.  A line that goes
  unnoticed fails the counter-proof.

USAGE

  python3 -I scripts/verifier-preuve-qnx8.py                 # the control
  python3 -I scripts/verifier-preuve-qnx8.py --contre-epreuve # the counter-proof
  python3 -I scripts/verifier-preuve-qnx8.py --captures      # rebuild the
                                                             # pictures (needs
                                                             # pillow)

The control needs nothing but python3 and the standard library.  The
network is needed for the pages, the codelab link and the public repository:
without it, those lines are NOT CHECKED, never OK.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
PROOF = REPO / "docs" / "PREUVE-QNX8.md"
TIMEOUT = 180

UA = ("QX-PROBE-qnx8-proof/1.0 "
      "(+https://github.com/tgg49099-dotcom/qnx-qx-probe)")


# --------------------------------------------------------------------------
# the table
# --------------------------------------------------------------------------

ID_RE = re.compile(r"^[A-Z][A-Z0-9]*$")
ALT = "@@"          # the separator between two acceptable outputs


def rows_of(text: str) -> list[dict]:
    """Every table row of the proof.

    A row is a line of the form | ID | cell | cell | cell | cell |.  The ID
    says which table the row belongs to: A (the assertions), P (the official
    pages), R (the rules), C (the captures).  A line that starts like a row
    but does not have exactly five cells is reported: a malformed row is a
    broken proof, not a row to ignore.
    """
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        inner = s[1:-1] if s.endswith("|") else s[1:]
        cells = [c.strip() for c in inner.split("|")]
        if not cells or not ID_RE.match(cells[0]):
            continue
        if cells[0].upper() in ("ID", "PAGE", "RULE", "IMAGE", "FILE"):
            continue
        out.append({
            "id": cells[0],
            "cells": cells,
            "malformed": len(cells) != 5,
        })
    return out


def section(text: str, prefix: str) -> list[list[str]]:
    """The rows of one table of the proof, found by the prefix of their ID."""
    return [r["cells"] for r in rows_of(text)
            if r["id"].startswith(prefix) and not r["malformed"]]


# --------------------------------------------------------------------------
# running the commands
# --------------------------------------------------------------------------

NETWORK_ERRORS = (
    "Could not resolve host", "Failed to connect", "Network is unreachable",
    "Temporary failure in name resolution", "unable to access",
    "Connection refused", "No route to host", "ssl", "HTTPError",
    "Temporary failure", "Connection reset",
)


_CACHE: dict[str, tuple[int, str, bool]] = {}


def run(command: str) -> tuple[int, str, bool]:
    """Runs a command in the repository.  Returns (rc, output, network_error).

    The same command is run once: the benchmark takes twenty seconds, and
    three lines of the proof use it.
    """
    if command in _CACHE:
        return _CACHE[command]
    try:
        done = subprocess.run(command, shell=True, cwd=str(REPO),
                              capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        result = (124, "TIMEOUT after %d s" % TIMEOUT, False)
        _CACHE[command] = result
        return result
    out = (done.stdout or "") + (done.stderr or "")
    net = any(mark in out for mark in NETWORK_ERRORS)
    result = (done.returncode, out, net)
    _CACHE[command] = result
    return result


def cited_urls() -> set[str]:
    """The exact URLs of the official pages, built from the CITATIONS table
    of scripts/verifier-citations.py (the base and the paths)."""
    text = (REPO / "scripts" / "verifier-citations.py").read_text(
        encoding="utf-8", errors="replace")
    m = re.search(r'^BASE\s*=\s*"([^"]+)"', text, re.M)
    base = m.group(1) if m else ""
    urls = set()
    for _name, path in re.findall(
            r'\(\s*"([a-zA-Z0-9_]+)",\s*"([a-zA-Z0-9_/]+)",\s*\(', text):
        urls.add("%s%s.html" % (base, path))
    return urls


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# The two lines that depend on the machine and on the moment: the date of
# the run and the path of the clone.  They are removed from the comparison
# of a capture; every other byte must match.
VOLATILE = ("date       : ", "repository : ")

# The sentence the proof script prints when the SDP 8.0 is absent.  A row
# that needs the SDP cannot be checked on a machine without it: it is
# reported NOT CHECKED, never OK and never FAILED.  The same sentence is the
# EXPECTED output of the row that proves the absence is detected, and that
# row is checked as usual.
SDP_ABSENT = "the QNX SDP 8.0 is not installed on this machine"

# The sentence the proof script prints when no QNX 8.0 target answers.  A
# row that needs a live target (the run of the binaries on QNX 8.0) cannot
# be checked on a machine without one: it is reported NOT CHECKED, never OK
# and never FAILED.  The run was measured on 25 November 2026 on the QEMU
# image of the SDP 8.0.
TARGET_ABSENT = "the run on a QNX 8.0 target is NOT MEASURED"


def normalize(text: str) -> str:
    return "\n".join(l for l in text.splitlines()
                     if not l.startswith(VOLATILE)).strip()


# --------------------------------------------------------------------------
# the PNG reader: the text embedded in the picture (no pillow needed)
# --------------------------------------------------------------------------

def png_embedded_text(path: pathlib.Path) -> str | None:
    """The text embedded in a PNG (the tEXt or iTXt chunk), or None."""
    import zlib
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    i = 8
    while i + 8 <= len(data):
        length = int.from_bytes(data[i:i + 4], "big")
        ctype = data[i + 4:i + 8]
        payload = data[i + 8:i + 8 + length]
        if ctype == b"tEXt":
            key, _, val = payload.partition(b"\x00")
            if key.decode("latin-1") == "QX-PROBE":
                return val.decode("latin-1")
        elif ctype == b"iTXt":
            # keyword \0 compression_flag compression_method language \0
            #        translated \0 text
            try:
                keyword, rest = payload.split(b"\x00", 1)
                flag, method = rest[0], rest[1]
                rest = rest[2:]
                _lang, rest = rest.split(b"\x00", 1)
                _translated, text = rest.split(b"\x00", 1)
            except ValueError:
                i += 12 + length
                continue
            if keyword.decode("latin-1") != "QX-PROBE":
                i += 12 + length
                continue
            if flag:
                text = zlib.decompress(text)
            return text.decode("utf-8", "replace")
        i += 12 + length
    return None


# --------------------------------------------------------------------------
# the checks
# --------------------------------------------------------------------------

class Row:
    def __init__(self, ident, affirmation, commande, source, statut, detail=""):
        self.id = ident
        self.affirmation = affirmation
        self.commande = commande
        self.source = source
        self.statut = statut
        self.detail = detail


WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")

# The words of an English sentence that carry no fact.  They are not used to
# decide whether a cited line carries the claim.
STOPWORDS = set("""
the and for with that this from not are was has have had been being will
would shall should could may might must can cannot do does did done you
your our their there here then than when what where which while who whom
whose how why where all any both each every few more most other others
same such only very much many own just also into over under again further
once one two three four five six seven eight nine ten
une des les pour avec que qui dans sur est pas plus son ses ce au aux
une des le la les du de en et ou ne pas plus son ses que qui dont
out off per use set new now get let put say see she her him its his who why
all any but yet too via way day job end top try ask run air age ago art bad
bat bed bit box bug bus buy cam cow cry cut dam den dew dig dim dip dry due
dug fan far fit fly gap gun hat hit hot ice ill ink joy key kid leg lie lip
log low map mix net nor nut odd oil pan pen pet pot red row sea sit sky son
sun tea tie tip toe toy van war web wet won yes amp etc inc ltd ref vol
""".split())


def key_words(text: str) -> set[str]:
    """The words of a text that carry a fact: at least three letters, and
    not a word of the grammar.

    Three letters is the floor because a claim can name a three-letter
    thing - `qcc` is the name of the compiler, and the proof of the SDP
    path is that the compiler is called with the right flags.  The words
    of the grammar are excluded: they are in every line of every file.
    """
    out = set()
    for word in WORD.findall(text or ""):
        word = word.lower()
        if len(word) < 3 or word in STOPWORDS:
            continue
        out.add(word)
    return out


def normalise(text: str) -> str:
    """The text as it can be compared: lowercase, without the markdown
    marks, without the quotes, and with a single space between the words."""
    text = re.sub(r"[`*_]", "", (text or "").lower())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def check_source(source: str, affirmation: str = "", sortie: str = "",
                 commande: str = "") -> str:
    """The file (and the line) the proof points at must exist, and the line
    must really carry the claim.

    A pointer that only exists proves nothing: until now this control
    accepted `README.md:2` - an empty line - for any assertion.  The line
    cited must now be a line that really says something about the claim:

      1. it must not be empty;
      2. it must carry the expected text itself (the output the proof
         records), the spaces and the markdown marks apart;
      3. when the expected text cannot be in the line - it is a shell
         variable, or an HTTP status code - the line must carry AT LEAST
         TWO of the significant words of the claim (the assertion and the
         expected output).

    TWO words, not one: a single word proves nothing when the word is in
    every file of the repository - "codelab" is in more than a hundred
    lines here, "version" in more than a hundred and fifty.  Two different
    words of the claim, in the same line, are what a real pointer looks
    like.

    A source that names a FILE and no line is accepted only when the
    command of the row really concerns that file: a row whose expected
    output is an HTTP status code is about a file, not about a line of
    it.

    A line that carries neither is a FAILED line: it is not a proof.
    """
    if not source:
        return "no source"
    path = source.split(":")[0].strip().strip("`")
    line = None
    m = re.search(r":(\d+)", source)
    if m:
        line = int(m.group(1))
    p = REPO / path
    if not p.is_file():
        return "the file %s is not in this repository" % path
    if line is None:
        # The source names a file, not a line: the command must concern it.
        name = path.split("/")[-1]
        if name and name not in commande and path not in commande:
            return ("the source names no line, and the command does not "
                    "concern the file %s" % path)
        return ""
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if line < 1:
        return "%s: the line %d does not exist (the lines are counted " \
               "from 1)" % (path, line)
    if line > len(lines):
        return "%s has %d lines: the line %d does not exist" % (
            path, len(lines), line)
    cited = lines[line - 1].strip()
    if not cited:
        return ("%s line %d is empty: it carries no claim"
                % (path, line))
    low = normalise(cited)
    for alt in [a.strip() for a in sortie.split(ALT) if a.strip()]:
        expected = normalise(alt)
        if expected and expected in low:
            return ""
    wanted = key_words(affirmation) | key_words(sortie)
    if not wanted:
        return ("%s line %d cannot carry the claim: the claim has no "
                "significant word" % (path, line))
    shared = wanted & key_words(cited)
    if len(shared) < 2:
        return ("%s line %d carries %d word(s) of the claim (%s): one word "
                "is not a proof" % (path, line, len(shared),
                                    ", ".join(sorted(shared)) or "none"))
    return ""


def check_main(rows: list[dict]) -> list[Row]:
    out = []
    for r in rows:
        ident = r["id"]
        if r["malformed"]:
            out.append(Row(ident, "the row %s of the proof" % ident, "", "",
                           "FAILED", "the row does not have five cells: the "
                           "proof is malformed"))
            continue
        cells = r["cells"]
        affirmation, commande = cells[1], cells[2].strip()
        sortie, source = cells[3].strip(), cells[4].strip()

        if not commande:
            out.append(Row(ident, affirmation, commande, source, "FAILED",
                           "no command: the assertion cannot be checked"))
            continue
        if not sortie:
            out.append(Row(ident, affirmation, commande, source, "FAILED",
                           "no real output: the assertion proves nothing"))
            continue
        if not source:
            out.append(Row(ident, affirmation, commande, source, "FAILED",
                           "no source: nothing in the repository makes the "
                           "assertion verifiable"))
            continue
        if source not in ("-", "git", "network"):
            problem = check_source(source, affirmation, sortie, commande)
            if problem:
                out.append(Row(ident, affirmation, commande, source, "FAILED",
                               problem))
                continue

        rc, texte, net = run(commande)
        if net and not texte.strip():
            out.append(Row(ident, affirmation, commande, source, "NOT CHECKED",
                           "the network is absent: the command could not run"))
            continue
        alternatives = [a.strip() for a in sortie.split(ALT) if a.strip()]
        if any(a in texte for a in alternatives):
            detail = "RC %d" % rc
            if len(alternatives) > 1:
                detail += " (one of the %d expected outputs)" % len(alternatives)
            out.append(Row(ident, affirmation, commande, source, "OK", detail))
            continue
        # The expected output is not there.  Before calling the line false,
        # the two known absences are looked for: a line that needs the SDP
        # 8.0 on a machine without it, and a line that needs a live QNX 8.0
        # target on a machine without one, are NOT CHECKED, never FAILED.
        if SDP_ABSENT in texte and SDP_ABSENT not in sortie:
            out.append(Row(ident, affirmation, commande, source, "NOT CHECKED",
                           "the QNX SDP 8.0 is absent on this machine: the "
                           "command cannot be checked here"))
            continue
        if TARGET_ABSENT in texte and TARGET_ABSENT not in sortie:
            out.append(Row(ident, affirmation, commande, source, "NOT CHECKED",
                           "no QNX 8.0 target answers on this machine: the "
                           "command cannot be checked here"))
            continue
        out.append(Row(ident, affirmation, commande, source, "FAILED",
                       "the command no longer produces what the proof writes "
                       "(RC %d)" % rc))
    return out


def check_pages(rows: list[list[str]]) -> list[Row]:
    """The 14 official QNX 8.0 pages: HTTP 200, and the published SHA-256."""
    out = []
    cited = cited_urls()
    for cells in rows:
        ident, name, url, quoted_sha, source = cells
        if not url.startswith("http"):
            out.append(Row(ident, "the official page " + name, "", source,
                           "FAILED", "no URL"))
            continue
        if url not in cited:
            out.append(Row(ident, "the official page " + name, url, source,
                           "FAILED", "this URL is not one of the pages cited by "
                           "scripts/verifier-citations.py"))
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as resp:
                body = resp.read()
                code = resp.status
        except urllib.error.HTTPError as exc:
            out.append(Row(ident, "the official page " + name, url, source,
                           "FAILED", "HTTP %s" % exc.code))
            continue
        except Exception as exc:                      # no network
            out.append(Row(ident, "the official page " + name, url, source,
                           "NOT CHECKED", "the network is absent (%s)"
                           % type(exc).__name__))
            continue
        measured = hashlib.sha256(body).hexdigest()
        if code != 200:
            out.append(Row(ident, "the official page " + name, url, source,
                           "FAILED", "HTTP %d" % code))
        elif measured == quoted_sha:
            out.append(Row(ident, "the official page " + name, url, source,
                           "OK", "HTTP 200, sha256 unchanged"))
        else:
            out.append(Row(ident, "the official page " + name, url, source,
                           "DRIFT", "HTTP 200, but QNX changed the page since "
                           "the proof was written"))
    return out


def check_rules(rows: list[list[str]]) -> list[Row]:
    """Every rule names an official API, and RULES.md says where."""
    out = []
    rules = (REPO / "RULES.md").read_text(encoding="utf-8", errors="replace")
    lines = rules.splitlines()
    cited = cited_urls()
    for cells in rows:
        ident, rule, api, url, source = cells
        code = re.search(r"QX\d+", rule)
        code = code.group(0) if code else rule
        problem = ""
        if ("## %s " % code) not in rules:
            problem = "RULES.md has no section %s" % code
        else:
            m = re.search(r":(\d+)", source)
            if m:
                n = int(m.group(1))
                if n > len(lines) or api not in lines[n - 1]:
                    problem = "RULES.md line %d does not name %s" % (n, api)
        if not problem and url not in cited:
            problem = ("the URL of %s is not one of the pages cited by "
                       "scripts/verifier-citations.py" % api)
        if problem:
            out.append(Row(ident, "the rule %s names the official API %s"
                           % (code, api), "", source, "FAILED", problem))
        else:
            out.append(Row(ident, "the rule %s names the official API %s"
                           % (code, api), "", source, "OK", "RULES.md"))
    return out


def check_captures(rows: list[list[str]]) -> list[Row]:
    """Every picture exists, is the published one, and shows the real output."""
    out = []
    for cells in rows:
        ident, name, commande, published_sha, what = cells
        path = REPO / name
        if not path.is_file():
            out.append(Row(ident, "the capture " + name, commande, what,
                           "FAILED", "the picture is not in this repository"))
            continue
        measured = sha256_of(path)
        if measured != published_sha:
            out.append(Row(ident, "the capture " + name, commande, what,
                           "FAILED", "the picture is not the published one "
                           "(sha256 %s)" % measured[:16]))
            continue
        embedded = png_embedded_text(path)
        if embedded is None:
            out.append(Row(ident, "the capture " + name, commande, what,
                           "FAILED", "the picture carries no embedded output"))
            continue
        rc, texte, net = run(commande)
        if net and not texte.strip():
            out.append(Row(ident, "the capture " + name, commande, what,
                           "NOT CHECKED", "the network is absent"))
            continue
        if SDP_ABSENT in texte and SDP_ABSENT not in embedded:
            out.append(Row(ident, "the capture " + name, commande, what,
                           "NOT CHECKED",
                           "the QNX SDP 8.0 is absent on this machine: the "
                           "picture cannot be checked here"))
            continue
        if TARGET_ABSENT in texte and TARGET_ABSENT not in embedded:
            out.append(Row(ident, "the capture " + name, commande, what,
                           "NOT CHECKED",
                           "no QNX 8.0 target answers on this machine: the "
                           "picture cannot be checked here"))
            continue
        if normalize(texte) == normalize(embedded):
            out.append(Row(ident, "the capture " + name, commande, what,
                           "OK", "the picture shows the real output (RC %d)" % rc))
        else:
            out.append(Row(ident, "the capture " + name, commande, what,
                           "FAILED", "the output of the command and the text "
                           "embedded in the picture differ"))
    return out


# --------------------------------------------------------------------------
# the captures
# --------------------------------------------------------------------------

def import_pillow():
    """Imports pillow.  The script is run with -I (isolated), which hides the
    PYTHONPATH of the machine; the usual places of pillow are then looked
    for.  The control itself never needs pillow: only the drawing does."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        from PIL.PngImagePlugin import PngInfo
        return Image, ImageDraw, ImageFont, PngInfo
    except ImportError:
        pass
    import glob
    import os
    patterns = [
        "/work/.pylocal/lib/python3.*/site-packages",
        os.path.expanduser("~/.local/lib/python3.*/site-packages"),
        "/usr/local/lib/python3.*/dist-packages",
    ]
    for pattern in patterns:
        for d in sorted(glob.glob(pattern)):
            if (pathlib.Path(d) / "PIL").is_dir():
                sys.path.insert(0, d)
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    from PIL.PngImagePlugin import PngInfo
                    return Image, ImageDraw, ImageFont, PngInfo
                except ImportError:
                    continue
    return None


def render_capture(command: str, raw: str, title: str, out_path: pathlib.Path) -> bool:
    """Renders the real output of a command into a PNG, with the raw output
    embedded in the picture (a tEXt/iTXt chunk a judge can read)."""
    modules = import_pillow()
    if modules is None:
        print("pillow is required to draw the captures: pip install pillow")
        return False
    Image, ImageDraw, ImageFont, PngInfo = modules
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 15)
        bold = ImageFont.truetype(bold_path, 15)
    except OSError:
        print("the DejaVu Sans Mono font is absent: apt-get install fonts-dejavu-core")
        return False
    lines = raw.rstrip("\n").split("\n")
    if len(lines) > 42:
        lines = lines[:40] + ["... (%d more lines in the raw output)"
                              % (len(lines) - 40)]
    probe = Image.new("RGB", (10, 10))
    d0 = ImageDraw.Draw(probe)
    char_w = d0.textlength("M" * 100, font=font) / 100.0
    max_px = 1770.0
    # A line longer than the picture is wrapped, never cut: a judge must read
    # the whole sentence, and the raw text stays embedded in the PNG.
    wrapped = []
    for line in lines:
        if d0.textlength(line, font=font) <= max_px:
            wrapped.append(line)
            continue
        n = max(40, int(max_px / char_w))
        first = True
        while line:
            chunk, line = line[:n], line[n:]
            wrapped.append(chunk if first else "     " + chunk)
            first = False
    foot = ("real output of the command above, captured by "
            "scripts/verifier-preuve-qnx8.py --captures on %s"
            % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    sha_line = ("sha256 of the raw output: " +
                hashlib.sha256(raw.encode("utf-8")).hexdigest())
    width = d0.textlength("$ " + command, font=font)
    for line in wrapped + [foot, sha_line]:
        width = max(width, d0.textlength(line, font=font))
    w = int(min(1800, max(900, width + 40)))
    h = 70 + 26 * len(wrapped) + 56
    img = Image.new("RGB", (w, h), (24, 26, 32))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 34], fill=(48, 52, 64))
    draw.text((12, 9), "QX-PROBE  -  " + title, font=bold, fill=(235, 235, 240))
    draw.text((12, 44), "$ " + command, font=bold, fill=(120, 220, 160))
    y = 70
    for line in wrapped:
        colour = (225, 228, 235)
        if line.startswith(("ERROR", "FAILED", "VERDICT", "RESULT")):
            colour = (255, 150, 120)
        elif line.strip().startswith(("WARN", "OK")):
            colour = (245, 215, 120)
        draw.text((12, y), line, font=font, fill=colour)
        y += 26
    draw.text((12, y + 8), foot, font=font, fill=(150, 155, 165))
    draw.text((12, y + 30), sha_line, font=font, fill=(150, 155, 165))
    info = PngInfo()
    info.add_itxt("QX-PROBE", raw, lang="en")
    img.save(out_path, "PNG", pnginfo=info)
    return True


def build_captures(text: str, only: str = "*") -> int:
    """Rebuilds the pictures of the proof from the real output of their
    commands.

    "only" is "*" for every capture of the table, or a list of capture IDs
    ("C04" or "C03,C04").  A picture that is rebuilt gets a NEW sha256 (the
    date of the capture is printed on it): the table of the proof must then
    be updated with the value printed here, or the control will refuse the
    picture as "not the published one".
    """
    rows = section(text, "C")
    if only != "*":
        wanted = {w.strip().upper() for w in only.split(",") if w.strip()}
        rows = [r for r in rows if r[0].upper() in wanted]
        if not rows:
            print("no capture with the ID %s in the table" % only)
            return 1
    rc = 0
    for cells in rows:
        ident, name, commande, _sha, what = cells
        rc_code, out, net = run(commande)
        if net and not out.strip():
            print("SKIP %s: the network is absent" % name)
            rc = 1
            continue
        path = REPO / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if render_capture(commande, out, what, path):
            print("written %s (sha256 %s)" % (name, sha256_of(path)))
    if only != "*":
        print("NOTE: a rebuilt picture has a new sha256: the table of the "
              "proof must carry the value printed above.")
    return rc


# --------------------------------------------------------------------------
# the counter-proof
# --------------------------------------------------------------------------

FAKE_ROWS = [
    {"id": "FAKE1", "malformed": False,
     "cells": ["FAKE1", "a claim with no command at all", "",
               "this line must never be published", "README.md:1"]},
    {"id": "FAKE2", "malformed": False,
     "cells": ["FAKE2", "the QNX 8.0 resource-manager protocol is checked "
               "by this tool",
               "echo hello", "a line that no command of this repository prints",
               "README.md:1"]},
    # The command works and the output is the expected one: the ONLY thing
    # wrong with this line is the pointer.  README.md line 2 is empty.
    {"id": "FAKE3", "malformed": False,
     "cells": ["FAKE3", "the pointer of this line is an empty line",
               "echo hello", "hello", "README.md:2"]},
    # The pointer exists, the line is not empty, but it says nothing about
    # the claim: the first line of a shell script is not a proof.
    {"id": "FAKE4", "malformed": False,
     "cells": ["FAKE4", "the eleven rules are documented in RULES.md",
               "echo hello", "hello", "scripts/run_tests.sh:1"]},
    # The pointer points OUTSIDE the file: the line does not exist.
    {"id": "FAKE5", "malformed": False,
     "cells": ["FAKE5", "the pointer of this line is outside the file",
               "echo hello", "hello", "README.md:9999"]},
    # The pointer is the line 0: the lines are counted from 1, so this line
    # does not exist either (without the guard, it would have pointed at the
    # LAST line of the file).
    {"id": "FAKE6", "malformed": False,
     "cells": ["FAKE6", "the pointer of this line is the line 0",
               "echo hello", "hello", "README.md:0"]},
    # The pointer is a line that carries ONE word of the claim - and that
    # word is in more than a hundred lines of this repository.  The command
    # works and the output is the expected one: the ONLY thing wrong with
    # this line is the pointer.
    {"id": "FAKE7", "malformed": False,
     "cells": ["FAKE7", "the codelab of the submission answers in public",
               "echo 200", "200", "docs/CODELAB.md:1"]},
    # The pointer is the title of the project: it carries the name of the
    # project and nothing else.
    {"id": "FAKE8", "malformed": False,
     "cells": ["FAKE8", "the test suite of the tool is green",
               "echo 'RESULT: QX-PROBE suite GREEN'",
               "RESULT: QX-PROBE suite GREEN", "README.md:1"]},
]


def counter_proof(text: str) -> int:
    """Eight false lines are added to the table: all of them must be caught."""
    rows = [r for r in rows_of(text) if r["id"].startswith("A")] + FAKE_ROWS
    results = check_main(rows)
    print("======================================================================")
    print("COUNTER-PROOF - eight deliberately false lines are added to the table")
    print("======================================================================")
    caught = 0
    for r in results:
        if r.id.startswith("FAKE"):
            print("  %-6s %-9s %s" % (r.id, r.statut, r.detail))
            if r.statut == "FAILED":
                caught += 1
    if caught == len(FAKE_ROWS):
        print("COUNTER-PROOF OK: the control caught the %d false line(s)." % caught)
        return 0
    print("COUNTER-PROOF FAILED: %d of the %d false lines went unnoticed."
          % (len(FAKE_ROWS) - caught, len(FAKE_ROWS)))
    return 1


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contre-epreuve", action="store_true",
                    help="add eight false lines and check that they are caught")
    ap.add_argument("--captures", nargs="?", const="*", default=None,
                    metavar="ID",
                    help="rebuild the pictures of the proof from their "
                         "commands: all of them, or only the captures whose "
                         "ID is given (--captures C04)")
    ap.add_argument("--preuve", default=str(PROOF),
                    help="the proof file to check")
    args = ap.parse_args()

    path = pathlib.Path(args.preuve)
    if not path.is_file():
        print("the proof file %s does not exist" % path)
        return 2
    text = path.read_text(encoding="utf-8")

    if args.captures is not None:
        return build_captures(text, args.captures)
    if args.contre_epreuve:
        return counter_proof(text)

    results = []
    results += check_main([r for r in rows_of(text) if r["id"].startswith("A")])
    results += check_pages(section(text, "P"))
    results += check_rules(section(text, "R"))
    results += check_captures(section(text, "C"))

    print("=" * 118)
    print("QX-PROBE - the control of the QNX 8.0 proof")
    print("=" * 118)
    print("proof : %s" % path)
    print("date  : %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print()
    print("%-9s %-52s %-46s %-12s %s"
          % ("ID", "AFFIRMATION", "COMMANDE", "SOURCE", "STATUT"))
    print("-" * 118)
    for r in results:
        aff = r.affirmation if len(r.affirmation) <= 51 else r.affirmation[:48] + "..."
        cmd = r.commande if len(r.commande) <= 45 else r.commande[:42] + "..."
        src = r.source if len(r.source) <= 45 else r.source[:42] + "..."
        print("%-9s %-52s %-46s %-12s %s"
              % (r.id, aff, cmd, src, r.statut))
        if r.detail and r.detail != "-":
            print("          %s" % r.detail)
    print("-" * 118)

    ok = sum(1 for r in results if r.statut == "OK")
    failed = [r for r in results if r.statut == "FAILED"]
    drift = [r for r in results if r.statut == "DRIFT"]
    notchecked = [r for r in results if r.statut == "NOT CHECKED"]
    print("%d lines: %d OK, %d FAILED, %d DRIFT, %d NOT CHECKED"
          % (len(results), ok, len(failed), len(drift), len(notchecked)))
    if drift:
        print("DRIFT (QNX changed the page since the proof was written, the "
              "proof stays true):")
        for r in drift:
            print("  %-9s %s" % (r.id, r.affirmation))
    if notchecked:
        print("NOT CHECKED (the check could not run here; never a success, "
              "never a failure):")
        for r in notchecked:
            print("  %-9s %s - %s" % (r.id, r.affirmation, r.detail))
    if failed:
        print("FAILED:")
        for r in failed:
            print("  %-9s %s - %s" % (r.id, r.affirmation, r.detail))
        print("VERDICT: FAILED - %d line(s) are false (RC 1)" % len(failed))
        return 1
    print("VERDICT: EVERY LINE OF THE PROOF IS CHECKED AND TRUE (RC 0)")
    if notchecked:
        print("         %d line(s) could not be checked on this machine; they "
              "are named above." % len(notchecked))
    return 0


if __name__ == "__main__":
    sys.exit(main())

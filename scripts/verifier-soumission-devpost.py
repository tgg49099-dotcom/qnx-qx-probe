#!/usr/bin/env python3
"""Check the DevPost submission text of this repository.

The text to paste into the submission form is `docs/SUBMISSION-EN.md`.  It
must contain no invented figure: every announced length must be the real
length of the block, the field limits written in the file must be respected,
the text must be in English, the codelab link must answer in public, and
the file must never claim that the demonstration video is already online.

Checks:

  A. LENGTHS - every block `<!-- DEBUT:X --> ... <!-- FIN:X -->` is measured
      and compared with the `_Measured: N characters` written after it; the
      DevPost limit written in the file is checked as well.
  B. ENGLISH - no block contains a French accented letter and no French
      narrow no-break space (the contest rules require English).
  C. CODELAB - the codelab URL is present, answers HTTP 200 without
      authentication, and the local copy of docs/CODELAB.md is compared with
      the file at the commit this repository is checked out at.  The drift of
      the branch "main" is then only an information, never an error: a
      "main" that has moved must never turn a correct copy red.  An HTTP 403
      on that page (bot protection, rate limiting) is a network condition, not
      a proof of error: it is NOT CHECKED when the file at the frozen commit
      proves the copy.  An HTTP 404 on that page stays an error.
  D. NO FALSE PUBLICATION - the YouTube placeholder is present exactly once,
      or a YouTube URL is present, really exists (the oEmbed endpoint of
      YouTube answers 404 for a video that does not exist, and 200 with the
      title for one that does) and is the QX-PROBE video; the text never
      claims that the video is already online.
  E. NO LEGACY DRAFT - a file named `SOUMISSION-DEVPOST.md` next to the
      repository, if there is one, must announce `docs/SUBMISSION-EN.md`.

Exit code:

  0  everything is verified
  1  at least one discrepancy
  2  a check could not be performed (no network, or no local git commit to
     compare the copy with) - never a silent success

Usage:

    python3 -I scripts/verifier-soumission-devpost.py [file]
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
SUB = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "SUBMISSION-EN.md"
LEGACY = REPO.parent / "SOUMISSION-DEVPOST.md"

BLOCK_RE = re.compile(r"<!-- DEBUT:(\w+) -->\n(.*?)<!-- FIN:\1 -->", re.S)
MEASURED_RE = re.compile(r"_Measured:\s*([\d\u00a0\u202f ]+?)\s*characters"
                         r"(?:\s*\(DevPost limit:\s*([\d\u00a0\u202f ]+?)\s*\))?\s*\._")
# French accented letters: one of them disqualifies a block written for a
# form that must be in English.
ACCENTUES = set("\u00e0\u00e2\u00e4\u00e7\u00e9\u00e8\u00ea\u00eb\u00ee\u00ef\u00f4\u00f6\u00f9\u00fb\u00fc\u00ff\u0153\u00e6"
                "\u00c0\u00c2\u00c4\u00c7\u00c9\u00c8\u00ca\u00cb\u00ce\u00cf\u00d4\u00d6\u00d9\u00db\u00dc\u0178\u0152\u00c6")
# French narrow no-break space and no-break space.
SPACES = ("\u00a0", "\u202f")
PLACEHOLDER = "<YOUTUBE_URL_A_COLLER_apres_le_televersement>"
CODELAB_URL = ("https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/"
               "docs/CODELAB.md")
CODELAB_RAW = ("https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/"
               "main/docs/CODELAB.md")


def _raw_at(commit: str) -> str:
    """The raw file of docs/CODELAB.md at a given commit."""
    return ("https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/"
            + commit + "/docs/CODELAB.md")


# The local copy of docs/CODELAB.md is the one of the commit this repository
# is checked out at.  Comparing it with the file that the branch "main" serves
# today is a FALSE RED as soon as "main" moves: the comparison must be made
# on the commit the local copy comes from, and the drift of "main" is then
# reported as information, never as an error.
def _frozen_commit() -> str:
    """The commit of the local copy of the repository (git rev-parse HEAD).

    "" when this copy has no commit of its own: an archive, a zip, or a
    directory that only happens to be inside another repository.  The caller
    then says so; it never pretends that a commit is known.
    """
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(REPO),
                             capture_output=True, text=True, timeout=20)
        if top.returncode != 0:
            return ""
        if pathlib.Path(top.stdout.strip()).resolve() != REPO.resolve():
            return ""
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ""
    commit = out.stdout.strip()
    return commit if len(commit) == 40 else ""


FROZEN_COMMIT = _frozen_commit()
CODELAB_RAW_FROZEN = _raw_at(FROZEN_COMMIT) if FROZEN_COMMIT else ""
# The exact wording used when the local copy has no git commit: the comparison
# with the frozen commit is impossible, and the reader must be told it.
NO_FROZEN_COMMIT_MESSAGE = (
    "[NOT CHECKED] no local git commit (this copy of the repository has no "
    ".git directory): comparison with the branch 'main' only")
UA = "QX-PROBE-submission-check/1.0"
# Limits published by Devpost itself, independent of what this file writes.
# A limit written in SUBMISSION-EN.md can be wrong (the tagline was declared
# "300" while Devpost help, article 145, says "Submission tagline
# (140 characters)*", read 15/11/2026): the official limit always wins.
OFFICIAL_LIMITS = {"TAGLINE": 140}


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def nombre(txt: str) -> int:
    """A number written in the file: '1 200' -> 1200 (spaces included)."""
    return int(re.sub(r"[\s\u00a0\u202f]", "", txt))


def http_get(url: str) -> tuple[int, bytes]:
    """One GET, with at most two retries on a transient server error.

    A single HTTP 503 from github.com (measured twice on 17 November 2026,
    while the same URL answered 200 a minute later) turned a check into
    "NOT CHECKED" for no reason: the server was busy, not absent.  Only
    5xx and 429 are retried; a 404 or a 403 is an answer and is never
    retried.  If the last attempt still fails, the error is raised and the
    check honestly reports that it could not be performed.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.getcode(), resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last if last else RuntimeError("unreachable")


def _fetch(url: str, http_getter):
    """(code, data) of one URL.

    None as the code means "the network did not answer"; an HTTP error code
    is returned as it is (404, 403...) instead of being raised, so that the
    caller can tell "the file is not there" from "the network is down".
    """
    try:
        return http_getter(url)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except (urllib.error.URLError, OSError):
        return None, b""


def check_codelab_copy(local: bytes, http_getter=None,
                       frozen_commit: str | None = None
                       ) -> tuple[bool, bool, list[str]]:
    """Compare the local copy of docs/CODELAB.md with the file that the branch
    "main" serves today, and with the file at the commit the local copy comes
    from.

    Returns (ok, not_checked, lines).  The drift of "main" is reported as
    information, never as an error: it is not a discrepancy of the copy.  When
    the local copy has no git commit (an archive without .git), the comparison
    with the frozen commit is impossible: it is reported as NOT CHECKED, with
    the exact wording, and never as a comparison with an empty commit.

    An HTTP 403 on the HTML page of the codelab is a network block (bot
    protection, rate limiting), not a proof that the codelab is gone: it is
    reported as "[NOT CHECKED] HTTP 403 (network)" when the file at the frozen
    commit answers HTTP 200 with the same md5 as the local copy - the copy is
    then proved.  An HTTP 404 on that page stays an error.
    """
    if http_getter is None:
        http_getter = http_get
    if frozen_commit is None:
        frozen_commit = FROZEN_COMMIT
    ok = True
    not_checked = False
    lines = []

    # The three answers are collected before any verdict is written: the
    # verdict on an HTTP 403 on the HTML page needs the file at the frozen
    # commit.
    code, _ = _fetch(CODELAB_URL, http_getter)
    code_main, data_main = _fetch(CODELAB_RAW, http_getter)
    raw_frozen = _raw_at(frozen_commit) if frozen_commit else ""
    code_f, data_f = _fetch(raw_frozen, http_getter) if raw_frozen else (None, b"")
    # the copy is proved when the file at the frozen commit IS the local copy
    proved = (code_f == 200 and md5_bytes(data_f) == md5_bytes(local))

    # 1. the page of the codelab answers without an account
    if code is None:
        not_checked = True
        lines.append(f"  [NOT CHECKED] {CODELAB_URL} : the network did not answer")
    elif code == 403 and proved:
        # a network block, not a proof of error: the copy is proved by the
        # file at the frozen commit
        not_checked = True
        lines.append(f"  [NOT CHECKED] HTTP 403 (network) on {CODELAB_URL} : the "
                     f"file at the frozen commit {frozen_commit[:7]} answers HTTP "
                     f"200 with the same md5 as the local copy")
    elif code != 200:
        ok = False
        lines.append(f"  [KO ] HTTP {code} without authentication")
    else:
        lines.append("  [OK ] HTTP 200 without authentication")

    # 2. the file served by the branch "main"
    if code_main is None:
        not_checked = True
        lines.append(f"  [NOT CHECKED] {CODELAB_RAW} : the network did not answer")
        return ok, not_checked, lines
    if code_main != 200:
        ok = False
        lines.append(f"  [KO ] HTTP {code_main} - raw file (branch 'main')")
    else:
        lines.append("  [OK ] HTTP 200 - raw file (branch 'main')")
    main_matches = (code_main == 200 and md5_bytes(data_main) == md5_bytes(local))

    # 3. the file at the commit the local copy comes from
    if frozen_commit:
        if code_f is None:
            not_checked = True
            lines.append(f"  [NOT CHECKED] {raw_frozen} : the network did not answer")
        elif code_f == 404:
            not_checked = True
            lines.append(f"  [NOT CHECKED] the frozen commit {frozen_commit[:7]} is "
                         f"not published on GitHub (HTTP 404): comparison with the "
                         f"branch 'main' only")
            if code_main == 200:
                lines.append(f"  [{'OK ' if main_matches else 'INFO'}] md5 downloaded "
                             f"from the branch 'main' ({md5_bytes(data_main)}) "
                             f"{'==' if main_matches else '!='} md5 local "
                             f"({md5_bytes(local)})")
        else:
            same = (code_f == 200 and md5_bytes(data_f) == md5_bytes(local))
            if not same:
                ok = False
            lines.append(f"  [{'OK ' if code_f == 200 else 'KO '}] HTTP {code_f} - raw "
                         f"file at the frozen commit {frozen_commit[:7]}")
            lines.append(f"  [{'OK ' if same else 'KO '}] md5 downloaded at the frozen "
                         f"commit ({md5_bytes(data_f)}) == md5 local "
                         f"({md5_bytes(local)})")
    else:
        not_checked = True
        lines.append("  " + NO_FROZEN_COMMIT_MESSAGE)
        if code_main == 200:
            lines.append(f"  [{'OK ' if main_matches else 'INFO'}] md5 downloaded from "
                         f"the branch 'main' ({md5_bytes(data_main)}) "
                         f"{'==' if main_matches else '!='} md5 local "
                         f"({md5_bytes(local)})")

    # 4. the drift of "main" is an information, never an error
    if code_main == 200 and not main_matches:
        lines.append(f"  [INFO] the branch 'main' has moved since the local copy "
                     f"(md5 {md5_bytes(data_main)} != {md5_bytes(local)}): not an error")
    return ok, not_checked, lines


def http_get_code(url: str) -> tuple[int, bytes]:
    """One GET, and the status code is returned even for 404.

    The watch page of a video that does not exist answers HTTP 200 (YouTube
    serves a page saying "Video unavailable"), so HTTP 200 alone cannot
    prove that a video is really online.  The oEmbed endpoint answers 404
    for a video that does not exist, and 200 with the title for one that
    does: that is the endpoint used here.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main() -> int:
    text = SUB.read_text(encoding="utf-8")
    ok = True
    not_checked = False
    print("=" * 78)
    print("QX-PROBE - check of the DevPost submission text")
    print("=" * 78)
    print(f"file : {SUB}")
    print()

    # ------------------------------------------------------------- 0
    print("0. SELF-TESTS OF THIS SCRIPT (no network)")
    rc_st, n_ok_st, n_st = _self_test(verbose=False)
    if rc_st != 0:
        print(f"  [KO ] the self-tests of this script failed ({n_ok_st}/{n_st})")
        return 1
    print(f"  [OK ] the self-tests of this script ({n_ok_st}/{n_st})")
    print()

    # ------------------------------------------------------------- A
    print("A. LENGTHS OF THE BLOCKS TO PASTE AND THE DEVPOST FIELD LIMITS")
    blocs = BLOCK_RE.findall(text)
    if not blocs:
        print("  [KO ] no block found")
        ok = False
    for name, body in blocs:
        body = body.rstrip("\n")
        n = len(body)
        tail = text[text.index(f"<!-- FIN:{name} -->"):][:220]
        m = MEASURED_RE.search(tail)
        claimed = nombre(m.group(1)) if m else None
        limit = nombre(m.group(2)) if (m and m.group(2)) else None
        official = OFFICIAL_LIMITS.get(name)
        if official is not None and (limit is None or limit > official):
            ok = False
            print(f"  [KO ] {name:12s} : written limit {limit} is above the "
                  f"official Devpost limit {official}")
            limit = official
        good = claimed == n
        if not good or (limit is not None and n > limit):
            ok = False
        verdict = "OK " if good and (limit is None or n <= limit) else "KO "
        lim_txt = f"limit {limit}" if limit else "no limit written"
        print(f"  [{verdict}] {name:12s} : measured {n:5d} / {lim_txt}"
              f"  - written: {claimed}"
              f"{'  (identical)' if good else '  <-- MISMATCH'}")

    # ------------------------------------------------------------- B
    print()
    print("B. ENGLISH (no accented letter, no French narrow no-break space)")
    for name, body in blocs:
        body = body.rstrip("\n")
        acc = sorted({c for c in body if c in ACCENTUES})
        esp = [c for c in body if c in SPACES]
        if acc or esp:
            ok = False
            print(f"  [KO ] {name:12s} : accented letters {acc} / "
                  f"narrow no-break spaces {len(esp)}")
        else:
            print(f"  [OK ] {name:12s} : no French character")

    # ------------------------------------------------------------- C
    print()
    print("C. CODELAB URL (field 'Best Codelab/Tutorial')")
    if CODELAB_URL not in text:
        print("  [KO ] the codelab URL is not in the file")
        ok = False
    else:
        print(f"  [OK ] the codelab URL is written: {CODELAB_URL}")
        local = (REPO / "docs" / "CODELAB.md").read_bytes()
        c_ok, c_not_checked, c_lines = check_codelab_copy(local)
        ok = ok and c_ok
        not_checked = not_checked or c_not_checked
        for ligne in c_lines:
            print(ligne)

    # ------------------------------------------------------------- D
    print()
    print("D. NO FALSE PUBLICATION")
    liens = dict(blocs).get("LIENS", "")
    n_placeholder = liens.count(PLACEHOLDER)
    if n_placeholder == 1:
        print("  [OK ] the YouTube placeholder is present exactly once "
              "(the video is not claimed to be online)")
    elif n_placeholder == 0:
        urls = re.findall(r"https://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]+",
                          liens)
        if not urls:
            print("  [KO ] no YouTube placeholder and no YouTube URL in LIENS")
            ok = False
        else:
            print(f"  [OK ] a YouTube URL is written ({len(urls)} found)")
            oembed = ("https://www.youtube.com/oembed?url=" +
                      urllib.parse.quote(urls[0], safe="") + "&format=json")
            try:
                code, body = http_get_code(oembed)
            except (urllib.error.URLError, OSError) as exc:
                not_checked = True
                print(f"  [NOT CHECKED] {oembed} : {exc}")
            else:
                if code in (400, 404):
                    ok = False
                    print(f"  [KO ] HTTP {code} - this video does not exist "
                          f"on YouTube (the oEmbed endpoint is the one that "
                          f"says so; the watch page answers 200 even for a "
                          f"video that does not exist)")
                elif code in (401, 403):
                    ok = False
                    print(f"  [KO ] HTTP {code} - this video is not public "
                          f"(the oEmbed endpoint refuses it without an "
                          f"account)")
                elif code != 200:
                    not_checked = True
                    print(f"  [NOT CHECKED] HTTP {code} - the oEmbed endpoint "
                          f"answered something unexpected")
                else:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except (ValueError, UnicodeDecodeError) as exc:
                        not_checked = True
                        print(f"  [NOT CHECKED] the oEmbed answer is not JSON : {exc}")
                    else:
                        titre = str(data.get("title", ""))
                        auteur = str(data.get("author_name", ""))
                        if "QX-PROBE" not in titre:
                            ok = False
                            print(f"  [KO ] the video exists but its title is "
                                  f"'{titre}' - it is not the QX-PROBE video")
                        else:
                            print(f"  [OK ] the video exists on YouTube and is "
                                  f"the QX-PROBE video")
                            print(f"         title  : {titre}")
                            print(f"         author : {auteur}")
    else:
        print(f"  [KO ] the YouTube placeholder is present {n_placeholder} "
              f"times (expected 1)")
        ok = False
    mensonges = [m for m in ("already on YouTube", "deja sur YouTube",
                             "is public on YouTube")
                 if m.lower() in liens.lower()]
    for mensonge in mensonges:
        print(f"  [KO ] the LIENS block claims '{mensonge}'")
        ok = False
    if not mensonges:
        print("  [OK ] no claim of publication")

    # ------------------------------------------------------------- E
    print()
    print("E. NO LEGACY DRAFT NEXT TO THE REPOSITORY")
    if not LEGACY.exists():
        print(f"  [OK ] no legacy draft at {LEGACY}")
    else:
        t = LEGACY.read_text(encoding="utf-8", errors="replace")
        if "docs/SUBMISSION-EN.md" in t[:2000]:
            print("  [OK ] the legacy draft announces that the official text "
                  "is docs/SUBMISSION-EN.md")
        else:
            print("  [KO ] the legacy draft does not announce "
                  "docs/SUBMISSION-EN.md: risk of pasting the old one")
            ok = False

    print()
    print("=" * 78)
    if not ok and not_checked:
        print("VERDICT: NOT CHECKED - a check could not be performed (see the "
              "[NOT CHECKED] lines above) and a discrepancy was found (RC 1)")
        print("=" * 78)
        return 1
    if not ok:
        print("VERDICT: A DISCREPANCY WAS FOUND (RC 1)")
        print("=" * 78)
        return 1
    if not_checked:
        print("VERDICT: NOT CHECKED - a check could not be performed (see the "
              "[NOT CHECKED] lines above), the text itself is consistent (RC 2)")
        print("=" * 78)
        return 2
    print("VERDICT: EVERYTHING VERIFIED - the submission text is consistent "
          "with itself and with the repository (RC 0)")
    print("=" * 78)
    return 0


def _self_test(verbose: bool = True) -> tuple[int, int, int]:
    """The tests of this file, without any network.

        python3 -I scripts/verifier-soumission-devpost.py --self-test

    They cover what a hostile review found: a copy of the repository without
    a .git directory (an archive, a zip) must never be compared with an EMPTY
    commit, and the drift of the branch "main" must never be an error.  They
    also cover an HTTP 403 on the HTML page of the codelab: it must never be
    an error when the file at the frozen commit proves the copy, and an HTTP
    404 on that page must stay an error.

    Returns (rc, ok_count, total_count).
    """
    import importlib.util
    import shutil
    import tempfile

    verdicts = []

    def verifie(cond, message):
        verdicts.append((bool(cond), message))

    racine = pathlib.Path(tempfile.mkdtemp(prefix="qx-probe-selftest-"))
    try:
        scripts = racine / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        copie = scripts / pathlib.Path(__file__).name
        shutil.copyfile(__file__, str(copie))
        spec = importlib.util.spec_from_file_location("verifier_soumission_copie",
                                                      str(copie))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # --- une copie SANS .git : le commit local est inconnu
        verifie(mod.FROZEN_COMMIT == "",
                "sans .git, le commit local est vide (aucun SHA a moitie)")
        verifie(mod.CODELAB_RAW_FROZEN == "",
                "sans .git, aucune URL de commit fige n'est fabriquee")
        verifie("NOT CHECKED" in mod.NO_FROZEN_COMMIT_MESSAGE,
                "sans .git, le message dit NOT CHECKED")
        verifie("no local git commit" in mod.NO_FROZEN_COMMIT_MESSAGE,
                "sans .git, le message dit pourquoi")
        verifie("at the frozen commit" not in mod.NO_FROZEN_COMMIT_MESSAGE,
                "sans .git, le message ne parle pas d'un commit fige inexistant")

        def faux_get(url):
            if "/main/" in url:
                return 200, b"le fichier de main a bouge"
            return 200, b"la copie locale"

        # --- le drift de main n'est JAMAIS une erreur
        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get,
                                                frozen_commit="a" * 40)
        verifie(ok, "le drift de main ne donne pas de KO")
        verifie(any("[INFO]" in l for l in lignes),
                "le drift de main est dit [INFO]")
        verifie(not any("[KO " in l for l in lignes),
                "aucun KO quand le commit fige est bon")
        verifie(any("at the frozen commit aaaaaaa" in l for l in lignes),
                "le commit fige est nomme dans l'affichage")

        # --- sans commit local : NOT CHECKED explicite, jamais d'erreur
        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get,
                                                frozen_commit="")
        verifie(ok, "sans commit local, la copie n'est pas declaree fausse")
        verifie(nc, "sans commit local, le controle est NOT CHECKED")
        verifie(any(mod.NO_FROZEN_COMMIT_MESSAGE in l for l in lignes),
                "sans commit local, le message explicite est affiche")
        verifie(not any("at the frozen commit" in l for l in lignes),
                "sans commit local, aucune ligne ne parle du commit fige")
        verifie(not any("[KO " in l for l in lignes),
                "sans commit local, aucun KO n'est affiche")

        # --- un commit fige non publie (HTTP 404) : NOT CHECKED, jamais un KO
        def faux_get_404(url):
            if "b" * 40 in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
            return faux_get(url)

        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get_404,
                                                frozen_commit="b" * 40)
        verifie(ok, "un commit fige non publie ne donne pas de KO")
        verifie(nc, "un commit fige non publie est NOT CHECKED")
        verifie(not any("[KO " in l for l in lignes),
                "un commit fige non publie n'affiche aucun KO")

        # --- HTTP 403 sur la page HTML : un blocage du reseau, pas une erreur,
        # --- quand le fichier brut au commit fige repond 200 avec le bon md5
        def faux_get_403(url):
            if "/blob/main/" in url:
                return 403, b""
            return faux_get(url)

        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get_403,
                                                frozen_commit="a" * 40)
        verifie(ok, "un 403 sur la page HTML, copie prouvee au commit fige, "
                    "ne donne pas de KO")
        verifie(nc, "un 403 sur la page HTML est NOT CHECKED")
        verifie(any("[NOT CHECKED] HTTP 403 (network)" in l for l in lignes),
                "le 403 est dit [NOT CHECKED] HTTP 403 (network)")
        verifie(not any("[KO " in l for l in lignes),
                "aucun KO quand le 403 est accompagne de la preuve")

        # --- HTTP 403 sur la page HTML SANS preuve : il reste une erreur
        def faux_get_403_sans_preuve(url):
            if "/blob/main/" in url:
                return 403, b""
            if "a" * 40 in url:
                return 200, b"un autre fichier"
            return faux_get(url)

        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get_403_sans_preuve,
                                                frozen_commit="a" * 40)
        verifie(not ok, "un 403 sur la page HTML sans preuve reste un KO")
        verifie(any("[KO ] HTTP 403" in l for l in lignes),
                "le 403 sans preuve est dit [KO ] HTTP 403")

        # --- HTTP 404 sur la page HTML : il reste une erreur
        def faux_get_404_page(url):
            if "/blob/main/" in url:
                return 404, b""
            return faux_get(url)

        ok, nc, lignes = mod.check_codelab_copy(b"la copie locale",
                                                http_getter=faux_get_404_page,
                                                frozen_commit="a" * 40)
        verifie(not ok, "un 404 sur la page HTML reste un KO")
        verifie(any("[KO ] HTTP 404" in l for l in lignes),
                "le 404 sur la page HTML est dit [KO ] HTTP 404")
    finally:
        shutil.rmtree(str(racine), ignore_errors=True)

    ko = [m for ok_, m in verdicts if not ok_]
    if verbose:
        for ok_, m in verdicts:
            print(f"  [{'OK ' if ok_ else 'KO '}] {m}")
        print(f"SELF-TEST: {len(verdicts) - len(ko)}/{len(verdicts)}")
    else:
        for ok_, m in verdicts:
            if not ok_:
                print(f"  [KO ] self-test : {m}")
    return (0 if not ko else 1), len(verdicts) - len(ko), len(verdicts)


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(_self_test()[0])
    raise SystemExit(main())

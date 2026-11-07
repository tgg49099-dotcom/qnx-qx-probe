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
      authentication, and the raw file has the md5 of the local one.
  D. NO FALSE PUBLICATION - the YouTube placeholder is present exactly once,
      or a YouTube URL is present and answers HTTP 200; the text never claims
      that the video is already online.
  E. NO LEGACY DRAFT - a file named `SOUMISSION-DEVPOST.md` next to the
      repository, if there is one, must announce `docs/SUBMISSION-EN.md`.

Exit code:

  0  everything is verified
  1  at least one discrepancy
  2  a check could not be performed (no network) - never a silent success

Usage:

    python3 -I scripts/verifier-soumission-devpost.py [file]
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys
import urllib.error
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
UA = "QX-PROBE-submission-check/1.0"


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def nombre(txt: str) -> int:
    """A number written in the file: '1 200' -> 1200 (spaces included)."""
    return int(re.sub(r"[\s\u00a0\u202f]", "", txt))


def http_get(url: str) -> tuple[int, bytes]:
    """One GET, no retry.  Returns (status, body)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.getcode(), resp.read()


def main() -> int:
    text = SUB.read_text(encoding="utf-8")
    ok = True
    not_checked = False
    print("=" * 78)
    print("QX-PROBE - check of the DevPost submission text")
    print("=" * 78)
    print(f"file : {SUB}")
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
        try:
            code, _ = http_get(CODELAB_URL)
        except (urllib.error.URLError, OSError) as exc:
            not_checked = True
            print(f"  [NOT CHECKED] {CODELAB_URL} : {exc}")
        else:
            if code != 200:
                ok = False
            print(f"  [{'OK ' if code == 200 else 'KO '}] HTTP {code} without "
                  f"authentication")
        try:
            code, data = http_get(CODELAB_RAW)
        except (urllib.error.URLError, OSError) as exc:
            not_checked = True
            print(f"  [NOT CHECKED] {CODELAB_RAW} : {exc}")
        else:
            same = md5_bytes(data) == md5_bytes(local)
            if code != 200 or not same:
                ok = False
            print(f"  [{'OK ' if code == 200 else 'KO '}] HTTP {code} - raw file")
            print(f"  [{'OK ' if same else 'KO '}] md5 downloaded "
                  f"({md5_bytes(data)}) == md5 local ({md5_bytes(local)})")

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
            try:
                code, _ = http_get(urls[0])
            except (urllib.error.URLError, OSError) as exc:
                not_checked = True
                print(f"  [NOT CHECKED] {urls[0]} : {exc}")
            else:
                if code != 200:
                    ok = False
                print(f"  [{'OK ' if code == 200 else 'KO '}] HTTP {code} - "
                      f"the published video answers")
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
        print("VERDICT: NOT CHECKED - a link could not be read (no network) "
              "and a discrepancy was found (RC 1)")
        print("=" * 78)
        return 1
    if not ok:
        print("VERDICT: A DISCREPANCY WAS FOUND (RC 1)")
        print("=" * 78)
        return 1
    if not_checked:
        print("VERDICT: NOT CHECKED - a link could not be read (no network), "
              "the text itself is consistent (RC 2)")
        print("=" * 78)
        return 2
    print("VERDICT: EVERYTHING VERIFIED - the submission text is consistent "
          "with itself and with the repository (RC 0)")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

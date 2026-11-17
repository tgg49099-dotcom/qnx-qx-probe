#!/usr/bin/env python3
"""Check the DevPost thumbnail and image gallery of this repository.

DevPost, "Know your submission steps" (help.devpost.com, article 126, read on
17 November 2026), about the project thumbnail: "This should be a JPG, PNG or
GIF format, 5 MB max file size. For best results, use a 3:2 ratio."

Checks, with the Python standard library only (no pillow, no network):

  A. LISTED = PRESENT - every file named in section "12 bis" of
     docs/SUBMISSION-EN.md exists, and every file of media/devpost/ is named
     there (no orphan, no missing image on the day of the submission).
  B. FORMAT - each file really is a PNG, a JPEG or a GIF (magic bytes, not
     the extension).
  C. SIZE - each file weighs at most 5 MB.
  D. RATIO - width x 2 == height x 3, read from the file header (exact 3:2).
  E. COUNTER-PROOF - the same checks, run on a 16:9 PNG header, on a 6 MB
     file and on a text file renamed .png, must refuse all three; otherwise
     this verifier is blind and says so.

Exit code: 0 everything verified, 1 at least one discrepancy.

Usage:  python3 -I scripts/verifier-galerie-devpost.py
"""
from __future__ import annotations

import pathlib
import re
import struct
import sys
import tempfile
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
SUB = REPO / "docs" / "SUBMISSION-EN.md"
DIR = REPO / "media" / "devpost"
MAX = 5 * 1024 * 1024
SECTION_RE = re.compile(r"^## 12 bis\..*?(?=^## )", re.S | re.M)
FILE_RE = re.compile(r"`(media/devpost/[\w.-]+)`")


def dimensions(data: bytes) -> tuple[str, int, int] | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return "PNG", w, h
    if data[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", data[6:10])
        return "GIF", w, h
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                return None
            marker = data[i + 1]
            seg = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return "JPEG", w, h
            i += 2 + seg
    return None


def check(path: pathlib.Path) -> list[str]:
    errors = []
    size = path.stat().st_size
    if size > MAX:
        errors.append(f"{size} bytes > 5 MB")
    dims = dimensions(path.read_bytes()[:65536])
    if dims is None:
        errors.append("not a PNG, JPEG or GIF (magic bytes)")
    else:
        fmt, w, h = dims
        if w * 2 != h * 3:
            errors.append(f"{fmt} {w}x{h} is not 3:2")
    return errors


def png_header(w: int, h: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr
            + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr)))


def counter_proof() -> list[str]:
    blind = []
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        cases = {
            "16:9 PNG": png_header(1280, 720),
            "6 MB PNG": png_header(1500, 1000) + b"\0" * (6 * 1024 * 1024),
            "text renamed .png": b"not an image at all\n",
        }
        for name, data in cases.items():
            f = t / "x.png"
            f.write_bytes(data)
            if not check(f):
                blind.append(name)
        f = t / "ok.png"
        f.write_bytes(png_header(1500, 1000))
        if check(f):
            blind.append("a valid 3:2 PNG refused")
    return blind


def main() -> int:
    bad = 0
    text = SUB.read_text(encoding="utf-8")
    m = SECTION_RE.search(text)
    if not m:
        print("FAILED: section '## 12 bis.' absent from docs/SUBMISSION-EN.md")
        return 1
    listed = FILE_RE.findall(m.group(0))
    if not any("thumbnail" in f for f in listed):
        print("FAILED: no thumbnail named in section 12 bis")
        bad += 1
    present = sorted(f"media/devpost/{p.name}" for p in DIR.glob("*") if p.is_file()) if DIR.is_dir() else []
    for rel in sorted(set(listed)):
        p = REPO / rel
        if not p.is_file():
            print(f"FAILED  {rel}: named in the submission text, absent from the repository")
            bad += 1
            continue
        errs = check(p)
        fmt, w, h = dimensions(p.read_bytes()[:65536]) or ("?", 0, 0)
        if errs:
            print(f"FAILED  {rel}: " + "; ".join(errs))
            bad += 1
        else:
            print(f"OK      {rel}: {fmt} {w}x{h} (3:2), {p.stat().st_size} bytes")
    for rel in present:
        if rel not in listed:
            print(f"FAILED  {rel}: in media/devpost/ but not named in section 12 bis")
            bad += 1
    blind = counter_proof()
    if blind:
        print("FAILED  counter-proof: the verifier accepted " + ", ".join(blind))
        bad += 1
    else:
        print("COUNTER-PROOF: a 16:9 PNG, a 6 MB file and a text file renamed .png are refused, as they must be")
    if bad:
        print(f"VERDICT: {bad} DISCREPANCY(IES) IN THE DEVPOST GALLERY (RC 1)")
        return 1
    print(f"VERDICT: THE DEVPOST GALLERY IS READY - {len(set(listed))} images, all 3:2, all under 5 MB (RC 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

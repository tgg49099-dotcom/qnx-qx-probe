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
  F. SOURCE - each picture of the gallery (not the thumbnail) carries the
     output of a command, embedded in the PNG; that text is byte-identical to
     the text embedded in one real capture of media/, so the picture of the
     gallery shows the same thing as the capture it comes from.
  G. PROOF - that capture is listed in the table of docs/PREUVE-QNX8.md, and
     the sha256 published there is the one computed on the file: the picture
     of the gallery hangs on the proof, not on a drawing.
  H. CAPTION - the caption published in section 12 bis repeats at least two
     words that are really printed in the picture: a caption that says
     nothing the picture shows is not a proof.

Exit code: 0 everything verified, 1 at least one discrepancy.

Usage:  python3 -I scripts/verifier-galerie-devpost.py
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import struct
import sys
import tempfile
import zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
SUB = REPO / "docs" / "SUBMISSION-EN.md"
PREUVE = REPO / "docs" / "PREUVE-QNX8.md"
DIR = REPO / "media" / "devpost"
MEDIA = REPO / "media"
MAX = 5 * 1024 * 1024
SECTION_RE = re.compile(r"^## 12 bis\..*?(?=^## )", re.S | re.M)
FILE_RE = re.compile(r"`(media/devpost/[\w.-]+)`")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
# | ID | the image | the command | the sha256 | what it shows |
CAPTURE_ROW_RE = re.compile(
    r"^\|\s*(C\d+)\s*\|\s*`?([^`|]+?)`?\s*\|[^|]*\|\s*`?([0-9a-f]{64})`?\s*\|", re.M)


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


def png_embedded_text(path: pathlib.Path) -> str | None:
    """The text embedded in a PNG (tEXt or iTXt chunk), or None.

    The same reader as scripts/verifier-preuve-qnx8.py: standard library
    only, no pillow.
    """
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


def find_sources(gallery_text: str, captures: dict[str, str]) -> list[str]:
    """The captures of media/ that carry exactly the text of the gallery.

    The text is the real output of the command, embedded in the PNG: the
    gallery picture and its source capture carry the same bytes, so the
    picture of the gallery is checkable against the capture.
    """
    return sorted(name for name, text in captures.items() if text == gallery_text)


def repeated_facts(caption: str, printed: str) -> list[str]:
    """The words of the caption that are really printed in the picture."""
    low = (printed or "").lower()
    out: list[str] = []
    for word in WORD.findall(caption):
        w = word.lower()
        if w in low and w not in out:
            out.append(w)
    return out


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def png_with_text(text: str) -> bytes:
    """A minimal PNG carrying an iTXt chunk (for the counter-proof)."""
    def chunk(ctype: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + ctype + data
                + struct.pack(">I", zlib.crc32(ctype + data)))

    ihdr = struct.pack(">IIBBBBB", 1500, 1000, 8, 2, 0, 0, 0)
    itxt = b"QX-PROBE\x00\x00\x00en\x00\x00" + text.encode("utf-8")
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"iTXt", itxt) + chunk(b"IEND", b""))


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

        # F and H: the chain of trust must refuse a picture whose text is
        # not the text of a real capture, and a caption that says nothing
        # the picture shows.
        cap = t / "cap.png"
        cap.write_bytes(png_with_text("RAN ON QNX 8.0  qxprobe-demo : attached\n"))
        gal = t / "gal.png"
        gal.write_bytes(png_with_text("RAN ON QNX 8.0  qxprobe-demo : attached\n"))
        captures = {"media/cap.png": png_embedded_text(cap)}
        if not find_sources(png_embedded_text(gal), captures):
            blind.append("a gallery picture identical to a capture refused")
        other = t / "other.png"
        other.write_bytes(png_with_text("something else entirely\n"))
        if find_sources(png_embedded_text(other), captures):
            blind.append("a gallery picture with no source accepted")
        if repeated_facts("nothing of the picture here", png_embedded_text(gal)):
            blind.append("a caption that says nothing the picture shows accepted")
        if not repeated_facts("attached on QNX 8.0", png_embedded_text(gal)):
            blind.append("a caption that repeats the picture refused")
    return blind


def parse_rows(section: str) -> list[dict]:
    """The rows of the table of section 12 bis (file, field, caption)."""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        for cell in cells:
            m = re.fullmatch(r"`(media/devpost/[\w.-]+)`", cell)
            if m:
                rows.append({"file": m.group(1), "field": cells[1],
                             "caption": cells[-1] if cells else ""})
                break
    return rows


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

    # ---- F, G, H: the chain of trust of each picture of the gallery ----
    captures: dict[str, str] = {}
    for p in sorted(MEDIA.glob("*.png")):
        t = png_embedded_text(p)
        if t is not None:
            captures[f"media/{p.name}"] = t
    proved = {m.group(2): (m.group(1), m.group(3))
              for m in CAPTURE_ROW_RE.finditer(PREUVE.read_text(encoding="utf-8"))}
    rows = parse_rows(m.group(0))
    for row in rows:
        rel = row["file"]
        p = REPO / rel
        if not p.is_file():
            continue
        if "thumbnail" in row["field"].lower():
            continue
        shown = png_embedded_text(p)
        if shown is None:
            print(f"FAILED  {rel}: carries no output: a picture of the gallery must show "
                  f"the real output of a command, embedded in the PNG")
            bad += 1
            continue
        sources = find_sources(shown, captures)
        if not sources:
            print(f"FAILED  {rel}: the text it carries is not the text of any capture of "
                  f"media/: the picture is not linked to a real run")
            bad += 1
            continue
        for src in sources:
            if src not in proved:
                print(f"FAILED  {rel}: its source {src} is not in the table of the captures "
                      f"of docs/PREUVE-QNX8.md")
                bad += 1
                continue
            ident, published = proved[src]
            real = sha256_of(REPO / src)
            if real != published:
                print(f"FAILED  {rel}: the sha256 published for {src} ({published}) is not "
                      f"the sha256 of the file ({real})")
                bad += 1
                continue
            facts = repeated_facts(row["caption"], shown)
            if len(facts) < 2:
                print(f"FAILED  {rel}: the caption repeats {len(facts)} word(s) of the picture "
                      f"({', '.join(facts) or 'none'}): it must say what the picture shows")
                bad += 1
                continue
            print(f"OK      {rel}: source {src} ({ident}, sha256 {published[:12]}...), "
                  f"the caption repeats: {', '.join(facts)}")

    blind = counter_proof()
    if blind:
        print("FAILED  counter-proof: the verifier accepted " + ", ".join(blind))
        bad += 1
    else:
        print("COUNTER-PROOF: a 16:9 PNG, a 6 MB file and a text file renamed .png are refused, as they must be")
        print("COUNTER-PROOF: a gallery picture with no source and a caption that says nothing the "
              "picture shows are refused too")
    if bad:
        print(f"VERDICT: {bad} DISCREPANCY(IES) IN THE DEVPOST GALLERY (RC 1)")
        return 1
    print(f"VERDICT: THE DEVPOST GALLERY IS READY - {len(set(listed))} images, all 3:2, all under 5 MB (RC 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

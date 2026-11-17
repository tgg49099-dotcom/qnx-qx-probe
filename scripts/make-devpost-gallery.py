#!/usr/bin/env python3
"""Build the DevPost thumbnail and image gallery from the real captures.

DevPost asks for the project thumbnail: "JPG, PNG or GIF format, 5 MB max
file size. For best results, use a 3:2 ratio." (help.devpost.com, article
126, "Know your submission steps", read on 17 November 2026).  The captures
of `media/` are 16:9 or wider than 2:1, so DevPost would crop them.

This script never redraws a capture: it pastes each real capture, unscaled
and uncropped (a 256-colour palette, measured at most 12/255 off on one
channel on 17 November 2026), on a 3:2 canvas and writes a one-sentence headline above
it.  Every headline repeats a fact printed in the capture itself.  The result
goes to `media/devpost/`; `scripts/verifier-galerie-devpost.py` checks it.

Needs pillow (pip install pillow) and the DejaVu fonts.

Usage:  python3 -I scripts/make-devpost-gallery.py
"""
from __future__ import annotations

import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("pillow is absent: pip install pillow (nothing was written)")
    sys.exit(2)

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "media" / "devpost"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG = (24, 26, 32)
INK = (235, 238, 245)
ACCENT = (110, 200, 255)
DIM = (150, 155, 165)
FOOT = "github.com/tgg49099-dotcom/qnx-qx-probe"

# The capture of the QNX 8.0 proof (qx-proof-3-sdp-absent.png) is left out
# on purpose: it shows the SDP absent.  Add the capture of the first real
# run of scripts/qnx8-proof.sh here as soon as it exists.
GALLERY = [
    ("qx-proof-1-corpus-reel.png", "gallery-1-real-corpus.png",
     "17 real QNX resource managers, each pinned to a commit: "
     "one real missing access gate found (QX004)."),
    ("qx-proof-2-exemple-officiel.png", "gallery-2-official-example.png",
     "The official QNX 8.0 documentation example: "
     "0\u00a0ERROR, 0\u00a0WARN. No false positive on the vendor's own code."),
]


def save(img, dst: pathlib.Path, colors: int = 256) -> None:
    """A terminal capture holds few colours: a 256-colour palette (fast
    octree), without dithering, keeps every glyph sharp and the colours of
    the capture, for about a quarter of the weight."""
    img.quantize(colors=colors, method=Image.Quantize.FASTOCTREE,
                 dither=Image.Dither.NONE).save(dst, optimize=True)


def font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        print(f"font absent: {path} (apt install fonts-dejavu-core)")
        sys.exit(2)


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    # split on plain spaces only: a no-break space keeps "0 WARN" together
    for word in text.split(" "):
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=fnt) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def three_two(w: int, h: int) -> tuple[int, int]:
    """The smallest 3:2 canvas, multiple of 6 wide, that holds w x h."""
    k = max(-(-w // 3), -(-h // 2))
    return 3 * k, 2 * k


def gallery_image(src: pathlib.Path, dst: pathlib.Path, headline: str) -> None:
    cap = Image.open(src).convert("RGB")
    margin = 48
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = max(30, cap.width // 34)
    hfont, ffont = font(BOLD, size), font(REG, max(18, size * 2 // 3))
    lines = wrap(probe, headline, hfont, cap.width)
    line_h = int(size * 1.35)
    head_h = line_h * len(lines)
    foot_h = int(size * 1.2)
    need_w = cap.width + 2 * margin
    need_h = margin + head_h + margin // 2 + cap.height + margin // 2 + foot_h + margin
    W, H = three_two(need_w, need_h)
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    extra = H - need_h
    y = margin + extra // 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=hfont)) // 2, y), ln, font=hfont, fill=INK)
        y += line_h
    y += margin // 2
    canvas.paste(cap, ((W - cap.width) // 2, y))
    y += cap.height + margin // 2
    d.text(((W - d.textlength(FOOT, font=ffont)) // 2, y), FOOT, font=ffont, fill=DIM)
    save(canvas, dst)


def thumbnail(src: pathlib.Path, dst: pathlib.Path) -> None:
    """16:9 -> 3:2 without cropping: the title bar and the caption band of
    the capture are extended with their own colour.  At most 2 columns of
    the right margin (plain background, no text) are dropped so that the
    width is a multiple of 3 and the ratio is exactly 3:2."""
    cap = Image.open(src).convert("RGB")
    W = cap.width - cap.width % 3
    cap = cap.crop((0, 0, W, cap.height))
    H = W * 2 // 3
    pad = H - cap.height
    top, bottom = pad // 2, pad - pad // 2
    canvas = Image.new("RGB", (W, H), cap.getpixel((cap.width // 2, 2)))
    ImageDraw.Draw(canvas).rectangle(
        [0, H - bottom, W, H], fill=cap.getpixel((cap.width // 2, cap.height - 2)))
    canvas.paste(cap, (0, top))
    # DevPost shows the thumbnail on small project cards: 960 x 640 with
    # 32 colours is sharper than the card and keeps the file light.
    save(canvas.resize((960, 640), Image.Resampling.LANCZOS), dst, colors=32)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    thumbnail(REPO / "media" / "qx-demo-thumbnail.png", OUT / "thumbnail-3x2.png")
    print("written: media/devpost/thumbnail-3x2.png")
    for src, dst, head in GALLERY:
        gallery_image(REPO / "media" / src, OUT / dst, head)
        print(f"written: media/devpost/{dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

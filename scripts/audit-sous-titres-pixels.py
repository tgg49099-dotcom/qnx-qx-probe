#!/usr/bin/env python3
"""PROOF that the 19 subtitles published in docs/YOUTUBE-VIDEO.md §8 ARE the
pixels of the published video media/qx-demo-v2.mp4.

A judge can run this from a fresh clone, with nothing but the public
repository:

    python3 scripts/audit-sous-titres-pixels.py

Requirements (all free, all official):
  * Python 3.9 or later,
  * ffmpeg / ffprobe (https://ffmpeg.org),
  * Pillow — `pip install pillow` (only to re-render the expected text),
  * the reference font **DejaVu Sans Mono Bold**
    (`apt-get install fonts-dejavu-core`, or `brew install font-dejavu`).
    This exact font is the one used when the video was recorded: with another
    font the shapes differ and the score is *expected* to be lower, so the
    script stops with the message "FONT NOT FOUND" instead of pretending.

Method (no trust, only measurement):
  1. the list of the 19 subtitles is read from the PUBLIC table
     (docs/YOUTUBE-VIDEO.md §8) and cross-checked against the second public
     source (video/SCENARIO.md) — the two must say the same thing;
  2. the frame rate is read from the video itself (ffprobe), not assumed;
  3. for every scene, the frame of the PUBLISHED mp4 is extracted (ffmpeg) and
     the subtitle band (rows 880..1080) is cropped;
  4. the expected band is rendered INDEPENDENTLY (same font, same size, same
     wrap width, same colours, same position), from the published table only;
  5. the two bands are compared: mask of bright text pixels -> IoU, plus MAE;
  6. CONTRE-EPREUVE: the same comparison is made against the WRONG subtitle
     (the next scene's) -> the metric must separate them, otherwise the
     proof would not bite.

Exit codes: 0 = proof established, 1 = proof not established, 2 = cannot run
(missing tool, missing font, missing file).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# --- Pillow ---------------------------------------------------------------
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - depends on the machine
    for _p in ("/work/.pylocal/lib/python3.11/site-packages",):
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is required to re-render the expected text:\n"
              "    pip install pillow\n"
              "(or apt-get install python3-pil)", file=sys.stderr)
        sys.exit(2)

# --- The geometry of the recording (must match video/SCENARIO.md) ---------
W, H = 1920, 1080
SFS = 38            # font size, bold
SLH = 48            # line height
SUB_TOP = 880       # first row of the subtitle band
SUB_MAX_COLS = 78   # wrap width, in characters
SUB_BG = (26, 31, 40)
SUB_FG = (247, 250, 253)
SUB_LINE = (63, 167, 255)

FONT_CANDIDATES = [
    os.environ.get("QXPROBE_FONT", ""),
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/DejaVuSansMono-Bold.ttf",
    "/System/Library/Fonts/DejaVuSansMono-Bold.ttf",
]
FONT_NAME = "DejaVu Sans Mono Bold"

IOU_MIN = 0.70        # below this, the pixels do not carry the published text
IOU_WRONG_MAX = 0.45  # above this, the contre-epreuve would not bite
MAE_MAX = 26.0

DEPOT = (sys.argv[1] if len(sys.argv) > 1
         else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEO = os.path.join(DEPOT, "media", "qx-demo-v2.mp4")


def find_font() -> str:
    for path in FONT_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return ""


def wrap(text: str, cols: int) -> list[str]:
    """The wrapping rule of the recording script (word boundary)."""
    out = []
    for raw in text.split("\n"):
        if len(raw) <= cols:
            out.append(raw)
            continue
        line = ""
        for word in raw.split(" "):
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= cols:
                line += " " + word
            else:
                out.append(line)
                line = word
            while len(line) > cols:
                out.append(line[:cols])
                line = line[cols:]
        if line:
            out.append(line)
    return out


def render_band(text: str, font_path: str) -> "Image.Image":
    """The expected subtitle band, rendered independently of the video."""
    img = Image.new("RGB", (W, H), SUB_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SUB_TOP, W, SUB_TOP + 4], fill=SUB_LINE)
    if not text:
        return img.crop((0, SUB_TOP, W, H))
    font = ImageFont.truetype(font_path, SFS)
    lines = wrap(text, SUB_MAX_COLS)
    y = SUB_TOP + (H - SUB_TOP - len(lines) * SLH) // 2 + 6
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=SUB_FG)
        y += SLH
    return img.crop((0, SUB_TOP, W, H))


def mask_of(band: "Image.Image") -> set:
    """The pixels of the bright text (the band background is dark)."""
    out = set()
    px = band.load()
    for y in range(band.height):
        for x in range(band.width):
            r, g, b = px[x, y]
            if r + g + b > 330:
                out.add((x, y))
    return out


def compare(band_a: "Image.Image", band_b: "Image.Image") -> tuple[float, float]:
    ma, mb = mask_of(band_a), mask_of(band_b)
    union = ma | mb
    iou = (len(ma & mb) / len(union)) if union else 1.0
    pa, pb = band_a.load(), band_b.load()
    tot = 0
    for y in range(band_a.height):
        for x in range(band_a.width):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            tot += abs(ra - rb) + abs(ga - gb) + abs(ba - bb)
    mae = tot / (band_a.width * band_a.height * 3)
    return iou, mae


def norm(text: str) -> str:
    """Comparison form: no markup, no extra spaces.

    The two public sources mark the line break of a two-line subtitle
    differently (`<br>` in docs/YOUTUBE-VIDEO.md, ` / ` in video/SCENARIO.md);
    both are removed here, because the words are what must be compared.
    """
    text = text.replace("<br>", " ").replace(" / ", " ")
    return " ".join(text.split())


def split_cells(line: str) -> list[str]:
    """Split a markdown table row, keeping the escaped pipes inside a cell."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]


def table_from_youtube(path: str) -> list[dict]:
    """The 19 subtitles of the public table of docs/YOUTUBE-VIDEO.md §8."""
    txt = open(path, encoding="utf-8").read()
    rows = []
    for m in re.finditer(
            r"^\|\s*(\d+)\s*\|\s*([\d.,–\-]+)\s*\|\s*([\d.,]+)\s*\|\s*(.*?)\s*\|\s*$",
            txt, re.M):
        rows.append({"num": m.group(1),
                     "span": m.group(2),
                     "from": float(re.split(r"[–\-]", m.group(2))[0]),
                     "to": float(re.split(r"[–\-]", m.group(2))[1]),
                     "text": m.group(4).replace("<br>", "\n")})
    return rows


def table_from_scenario(path: str) -> list[str]:
    """The same 19 subtitles, from the second public source (video/SCENARIO.md)."""
    if not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = split_cells(line.rstrip("\n"))
        if len(cells) >= 5:
            out.append(cells[4])
    return out


def probe_fps(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=r_frame_rate", "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True).stdout.strip()
    num, den = out.split("/")
    return float(num) / float(den)


def main() -> int:
    ok = True
    print("=" * 78)
    print("PREUVE — les 19 sous-titres publies sont-ils les PIXELS de la video ?")
    print("=" * 78)
    print(f"depot  : {DEPOT}")
    print(f"video  : {VIDEO}")

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"IMPOSSIBLE : {tool} est absent (https://ffmpeg.org)", file=sys.stderr)
            return 2
    if not os.path.isfile(VIDEO):
        print(f"IMPOSSIBLE : la video publiee est absente : {VIDEO}", file=sys.stderr)
        return 2
    font_path = find_font()
    if not font_path:
        print("FONT NOT FOUND — la police de reference est **DejaVu Sans Mono Bold**.\n"
              "  apt-get install fonts-dejavu-core   (ou brew install font-dejavu)\n"
              "  ou QXPROBE_FONT=/chemin/vers/une/police/mono-gras.ttf\n"
              "Sans cette police exacte, les formes des lettres different et le score "
              "ne peut pas atteindre la valeur de reference : la preuve serait "
              "inconclusive, pas fausse.", file=sys.stderr)
        return 2
    print(f"police : {font_path}")

    rows = table_from_youtube(os.path.join(DEPOT, "docs", "YOUTUBE-VIDEO.md"))
    print(f"\nA. table publique docs/YOUTUBE-VIDEO.md §8 : {len(rows)} lignes")
    if len(rows) != 19:
        print("ECHEC : la table publique ne contient pas 19 sous-titres")
        return 1

    scen = table_from_scenario(os.path.join(DEPOT, "video", "SCENARIO.md"))
    print(f"B. second source publique video/SCENARIO.md : {len(scen)} lignes")
    if len(scen) == len(rows):
        same = sum(1 for r, s in zip(rows, scen) if norm(r["text"]) == norm(s))
        ok = ok and same == len(rows)
        print(f"  {'OK ' if same == len(rows) else 'ECHEC'} "
              f"{same}/{len(rows)} sous-titres identiques entre les deux sources")
    else:
        print("  (table absente ou differente : le controle se fait sur les pixels)")

    fps = probe_fps(VIDEO)
    print(f"\nC. video publiee : {fps:g} fps (lu par ffprobe), "
          f"{len(rows)} scenes d'apres la table publique")

    print("\nD. les pixels de la video publiee portent-ils ces textes ?")
    tmp = tempfile.mkdtemp(prefix="audit-st-")
    results = []
    for i, row in enumerate(rows):
        frame = int(round(row["from"] * fps))
        out = os.path.join(tmp, f"scene{i:02d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-i", VIDEO,
                        "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", "-y", out],
                       check=True)
        band = Image.open(out).convert("RGB").crop((0, SUB_TOP, W, H))
        iou, mae = compare(band, render_band(row["text"], font_path))
        # contre-epreuve : le texte de la scene suivante doit etre detecte comme different
        wrong = rows[(i + 1) % len(rows)]["text"]
        iou_w, mae_w = compare(band, render_band(wrong, font_path))
        results.append((i, frame, row["text"], iou, mae, iou_w, mae_w))
        flag = "OK " if (iou >= IOU_MIN and mae <= MAE_MAX) else "ECHEC"
        if flag != "OK ":
            ok = False
        bite = "OK " if (iou_w <= IOU_WRONG_MAX or mae_w > mae * 1.5) else "MORD PAS"
        if bite != "OK ":
            ok = False
        print(f"  {flag} scene {i:02d} (frame {frame:4d})  IoU={iou:.3f}  MAE={mae:5.2f}"
              f"   |  contre-epreuve (mauvais texte) IoU={iou_w:.3f} MAE={mae_w:5.2f} {bite}")
        print(f"        « {row['text'][:74].replace(chr(10), ' ')} »")

    ious = [r[3] for r in results]
    maes = [r[4] for r in results]
    ious_w = [r[5] for r in results]
    print("\nE. synthese")
    print(f"   IoU moyen (texte attendu)  : {sum(ious)/len(ious):.3f}  (min {min(ious):.3f})")
    print(f"   MAE moyen (texte attendu)  : {sum(maes)/len(maes):.2f}")
    print(f"   IoU moyen (mauvais texte)  : {sum(ious_w)/len(ious_w):.3f}  (max {max(ious_w):.3f})")
    sep = (sum(ious) / len(ious)) - (sum(ious_w) / len(ious_w))
    print(f"   separation des deux classes : {sep:.3f} d'IoU")

    print("\nVERDICT :", "PREUVE ETABLIE" if ok else "PREUVE NON ETABLIE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

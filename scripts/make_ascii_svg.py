#!/usr/bin/env python3
"""Turn a prepared photo into a self-typing ASCII portrait as an SVG.

The animation is pure SMIL so it survives GitHub's README sanitiser, which
strips <script> and almost all inline CSS but renders SVG untouched. Each row
of characters is a <text> element that fades in on a stagger, giving a
line-by-line typing effect, then freezes.

    python3 scripts/make_ascii_svg.py --input assets/prepped.png \
        --output assets/portrait.svg
"""

import argparse
import os
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

from smil import fade_in

# Dark to light. The leading space is the background.
RAMP = " .:-=+*#%@"


def to_ascii(path, cols, char_aspect):
    """Sample the image into a grid of characters, darkest pixel -> densest glyph."""
    img = Image.open(path).convert("L")
    width, height = img.size
    rows = max(1, int(cols * (height / width) * char_aspect))
    img = img.resize((cols, rows), Image.LANCZOS)

    pixels = np.asarray(img, dtype=np.float32) / 255.0
    # Invert so bright pixels map to sparse glyphs on a dark terminal.
    idx = np.clip(((1.0 - pixels) * (len(RAMP) - 1)).round().astype(int),
                  0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def build_svg(lines, args):
    char_w = args.font_size * 0.6
    text_w = len(lines[0]) * char_w
    width = int(text_w) + args.padding * 2
    height = int(len(lines) * args.line_height) + args.padding * 2


    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{escape(args.font)}" font-size="{args.font_size}">',
        f'  <rect width="100%" height="100%" fill="{args.background}" rx="10"/>',
        '  <g xml:space="preserve">',
    ]

    for i, line in enumerate(lines):
        y = args.padding + (i + 1) * args.line_height
        # textLength pins each row to an exact width, so the portrait keeps its
        # proportions no matter which monospace font the viewer actually has.
        out.append(
            f'    <text x="{args.padding}" y="{y}" fill="{args.color}" '
            f'textLength="{round(text_w, 2)}" lengthAdjust="spacingAndGlyphs" '
            f'opacity="1">{escape(line)}'
            f'{fade_in(i, len(lines), args.duration)}'
            f'</text>'
        )

    out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="prepared grayscale image")
    p.add_argument("--output", required=True, help="SVG path to write")
    p.add_argument("--cols", type=int, default=78,
                   help="character columns across (default: 78)")
    p.add_argument("--char-aspect", type=float, default=0.5,
                   help="glyph height/width ratio correction (default: 0.5)")
    p.add_argument("--font-size", type=float, default=9.0)
    p.add_argument("--line-height", type=float, default=9.0)
    p.add_argument("--font", default="SFMono-Regular,Consolas,Menlo,monospace")
    p.add_argument("--color", default="#39d353", help="glyph colour")
    p.add_argument("--background", default="#0d1117")
    p.add_argument("--padding", type=int, default=14)
    p.add_argument("--duration", type=float, default=4.0,
                   help="seconds for the portrait to finish typing")
    args = p.parse_args()

    lines = to_ascii(args.input, args.cols, args.char_aspect)
    svg = build_svg(lines, args)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"wrote {args.output} ({len(lines[0])}x{len(lines)} chars)")


if __name__ == "__main__":
    main()

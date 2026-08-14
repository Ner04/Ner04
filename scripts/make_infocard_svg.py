#!/usr/bin/env python3
"""Render a neofetch-style info card as an animated SVG.

Reads the card's content from a JSON file so the text can be edited without
touching this script. Lines fade in on a stagger and freeze. SMIL only, so
GitHub's README sanitiser leaves it alone.

    python3 scripts/make_infocard_svg.py --config data/infocard.json \
        --output assets/infocard.svg
"""

import argparse
import json
import os
from xml.sax.saxutils import escape

from smil import fade_in

THEME = {
    "background": "#0d1117",
    "border": "#30363d",
    "key": "#39d353",
    "value": "#c9d1d9",
    "accent": "#58a6ff",
    "muted": "#8b949e",
}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", required=True, help="JSON describing the card")
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=520)
    p.add_argument("--font-size", type=float, default=12.0)
    p.add_argument("--line-height", type=float, default=19.0)
    p.add_argument("--padding", type=int, default=20)
    p.add_argument("--font", default="SFMono-Regular,Consolas,Menlo,monospace")
    p.add_argument("--duration", type=float, default=4.0,
                   help="seconds for every line to appear")
    args = p.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    rows = cfg["rows"]
    header = f"{cfg['user']}@github"
    # header + rule + rows + blank + footer
    total_lines = len(rows) + 4
    height = args.padding * 2 + int(total_lines * args.line_height)

    key_w = max((len(r[0]) for r in rows if r[0]), default=0)

    def fade(index):
        """SMIL fade-in for the nth line, frozen once it lands."""
        return fade_in(index, total_lines, args.duration)

    x = args.padding
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{args.width}" '
        f'height="{height}" viewBox="0 0 {args.width} {height}" '
        f'font-family="{escape(args.font)}" font-size="{args.font_size}">',
        f'  <rect width="100%" height="100%" fill="{THEME["background"]}" '
        f'rx="10" stroke="{THEME["border"]}"/>',
        '  <g xml:space="preserve">',
    ]

    y = args.padding + args.line_height
    out.append(f'    <text x="{x}" y="{y}" fill="{THEME["accent"]}" '
               f'font-weight="700" opacity="1">{escape(header)}{fade(0)}</text>')

    y += args.line_height
    out.append(f'    <text x="{x}" y="{y}" fill="{THEME["muted"]}" '
               f'opacity="1">{"-" * len(header)}{fade(1)}</text>')

    for i, (key, value) in enumerate(rows):
        y += args.line_height
        label = f"{key}:".ljust(key_w + 2) if key else " " * (key_w + 2)
        out.append(
            f'    <text x="{x}" y="{y}" opacity="1">'
            f'<tspan fill="{THEME["key"]}" font-weight="600">{escape(label)}</tspan>'
            f'<tspan fill="{THEME["value"]}">{escape(value)}</tspan>'
            f'{fade(i + 2)}</text>'
        )

    y += args.line_height * 2
    swatches = ["#0e4429", "#006d32", "#26a641", "#39d353",
                "#58a6ff", "#8b949e", "#c9d1d9"]
    out.append(f'    <g opacity="1">{fade(total_lines - 1)}')
    for i, colour in enumerate(swatches):
        out.append(f'      <rect x="{x + i * 22}" y="{y - 11}" width="18" '
                   f'height="11" rx="2" fill="{colour}"/>')
    out.append('    </g>')

    out.append('  </g>')
    out.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render a contribution calendar JSON file as an animated SVG heatmap.

Squares fade in column by column (week by week), left to right, and stay put
once they land. SMIL only, so it renders inside a GitHub README.

    python3 scripts/render_heatmap_svg.py --input data/contributions.json \
        --output assets/heatmap.svg
"""

import argparse
import json
import os
from datetime import date
from xml.sax.saxutils import escape

from smil import fade_in

# GitHub's dark-theme contribution palette, level 0 through 4.
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count, thresholds):
    for i, limit in enumerate(thresholds):
        if count <= limit:
            return i
    return len(thresholds)


def build_thresholds(days):
    """Pick level cutoffs from the data so the grid uses its full range."""
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    if not counts:
        return [0, 1, 2, 3]
    q = lambda f: counts[min(int(len(counts) * f), len(counts) - 1)]
    # Level 0 is always "no contributions".
    return [0, q(0.25), q(0.50), q(0.75)]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--cell", type=int, default=11, help="square edge in px")
    p.add_argument("--gap", type=int, default=3, help="gap between squares")
    p.add_argument("--padding", type=int, default=16)
    p.add_argument("--background", default="#0d1117")
    p.add_argument("--text", default="#8b949e")
    p.add_argument("--title", default=None,
                   help="heading text (default: derived from the data)")
    p.add_argument("--duration", type=float, default=4.0,
                   help="seconds for the grid to fill in")
    p.add_argument("--font", default="SFMono-Regular,Consolas,Menlo,monospace")
    args = p.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    days = data["days"]
    thresholds = build_thresholds(days)
    step = args.cell + args.gap

    # Lay days out in columns of 7, starting on the grid's first Sunday.
    weeks = (len(days) + 6) // 7
    label_h = 30
    day_label_w = 26

    grid_w = weeks * step - args.gap
    width = args.padding * 2 + day_label_w + grid_w
    height = args.padding * 2 + label_h + 7 * step - args.gap + 22


    title = args.title or (
        f"{data['total']} contributions  ·  {data['start']} → {data['end']}"
    )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{escape(args.font)}">',
        f'  <rect width="100%" height="100%" fill="{args.background}" rx="10"/>',
        f'  <text x="{args.padding}" y="{args.padding + 12}" fill="#c9d1d9" '
        f'font-size="12" font-weight="600">{escape(title)}</text>',
    ]

    origin_x = args.padding + day_label_w
    origin_y = args.padding + label_h

    # Weekday labels (Mon/Wed/Fri, matching GitHub).
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = origin_y + row * step + args.cell - 2
        out.append(f'  <text x="{args.padding}" y="{y}" fill="{args.text}" '
                   f'font-size="9">{name}</text>')

    # Month labels above the first column of each new month.
    seen = set()
    for i, day in enumerate(days):
        d = date.fromisoformat(day["date"])
        week = i // 7
        if d.month not in seen and d.day <= 7:
            seen.add(d.month)
            x = origin_x + week * step
            if x < width - args.padding - 20:
                out.append(f'  <text x="{x}" y="{origin_y - 6}" '
                           f'fill="{args.text}" font-size="9">'
                           f'{MONTHS[d.month - 1]}</text>')

    out.append('  <g>')
    for i, day in enumerate(days):
        week, row = divmod(i, 7)
        x = origin_x + week * step
        y = origin_y + row * step
        fill = LEVELS[level_for(day["count"], thresholds)]

        plural = "" if day["count"] == 1 else "s"

        out.append(
            f'    <rect x="{x}" y="{y}" width="{args.cell}" '
            f'height="{args.cell}" rx="2" fill="{fill}" opacity="1">'
            f'<title>{day["count"]} contribution{plural} on {day["date"]}</title>'
            f'{fade_in(week, weeks, args.duration)}'
            f'</rect>'
        )
    out.append('  </g>')

    # Legend.
    legend_y = height - args.padding - 2
    legend_x = width - args.padding - (len(LEVELS) * step) - 60
    out.append(f'  <text x="{legend_x - 28}" y="{legend_y}" '
               f'fill="{args.text}" font-size="9">Less</text>')
    for i, colour in enumerate(LEVELS):
        out.append(f'  <rect x="{legend_x + i * step}" y="{legend_y - 9}" '
                   f'width="{args.cell}" height="{args.cell}" rx="2" '
                   f'fill="{colour}"/>')
    out.append(f'  <text x="{legend_x + len(LEVELS) * step + 4}" y="{legend_y}" '
               f'fill="{args.text}" font-size="9">More</text>')
    out.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {args.output} ({weeks} weeks, {data['total']} contributions)")


if __name__ == "__main__":
    main()

"""Shared SMIL decoration for the profile SVGs.

An earlier version revealed content with staggered opacity animations. That
turned out to be fragile: when an SVG is embedded with <img> the animation
timeline is not guaranteed to advance -- a throttled tab, a still render, a
proxy that rasterises the image -- and anything whose animated value starts at
zero is then invisible forever, not merely un-animated. GitHub READMEs embed
images exactly that way, so the profile came out blank.

So content here is never animated into existence. Every glyph and square is
painted at full opacity, and animation is layered on top as decoration: a
sweep that passes over finished artwork, a cursor that blinks. If the timeline
never advances, the decoration parks somewhere harmless and the page still
reads exactly as intended.
"""


def scan_sweep(width, height, duration=6.0, colour="#39d353",
               band=None, opacity=0.16):
    """A soft horizontal band that travels down the artwork, forever.

    Parked at the very top when the timeline does not advance, where it reads
    as part of the border rather than as a missing element.
    """
    band = band or max(height * 0.08, 10)
    gid = f"sweep{int(width)}x{int(height)}"
    return (
        f'<defs>'
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{colour}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{colour}" stop-opacity="{opacity}"/>'
        f'<stop offset="100%" stop-color="{colour}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<rect x="0" y="{-band}" width="{width}" height="{band}" '
        f'fill="url(#{gid})" pointer-events="none">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0,0; 0,{height + band}" dur="{duration}s" '
        f'repeatCount="indefinite"/>'
        f'</rect>'
    )


def blink(x, y, width, height, colour="#39d353", duration=1.1):
    """A terminal cursor. Solid when the timeline is frozen, which is fine."""
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'fill="{colour}">'
        f'<animate attributeName="opacity" values="1;1;0;0" '
        f'keyTimes="0;0.5;0.5;1" dur="{duration}s" '
        f'repeatCount="indefinite"/>'
        f'</rect>'
    )

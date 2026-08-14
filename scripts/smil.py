"""Shared SMIL helper for the profile SVGs.

The important property here is graceful degradation. An element whose static
attribute is opacity="0" disappears entirely wherever SMIL does not run -- a
throttled background tab, a renderer that ignores animation, an image
converted to a still. So every animated element carries opacity="1" as its
resting value and the intro is driven by a single animation that begins at
t=0, holds the element hidden for its share of the stagger, fades it in, and
freezes. Where SMIL runs you get the animation; where it does not you get the
finished frame instead of nothing.
"""


def fade_in(index, count, duration, fade=None):
    """SMIL fade-in for element `index` of `count`, staggered across `duration`.

    Returns an <animate> element. Pair it with opacity="1" on the parent.
    """
    if count <= 0:
        count = 1
    stagger = duration / count
    fade = stagger * 2 if fade is None else fade

    start = min(index * stagger / duration, 1.0)
    end = min(start + fade / duration, 1.0)

    # calcMode="linear" requires keyTimes to start at 0 and end at 1.
    return (f'<animate attributeName="opacity" values="0;0;1;1" '
            f'keyTimes="0;{round(start, 4)};{round(end, 4)};1" '
            f'dur="{round(duration, 3)}s" begin="0s" fill="freeze"/>')

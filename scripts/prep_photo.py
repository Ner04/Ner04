#!/usr/bin/env python3
"""Prepare a source photo for ASCII conversion.

Converts to grayscale, optionally removes the background, boosts contrast and
crops to a square. Background removal uses rembg when it is installed; without
it the script falls back to a plain center-crop, which is fine for headshots
and avatars that already sit on a flat background.

    python3 scripts/prep_photo.py --input photo.jpg --output assets/prepped.png
"""

import argparse
import os
import sys

from PIL import Image, ImageEnhance, ImageOps


def remove_background(img):
    """Strip the background with rembg if available. Returns (image, used)."""
    try:
        from rembg import remove
    except ImportError:
        return img, False

    cut = remove(img.convert("RGBA"))
    # Composite onto white so the alpha edge reads as bright, not black.
    flat = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    flat.alpha_composite(cut)
    return flat.convert("RGB"), True


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="source image")
    p.add_argument("--output", required=True, help="where to write the PNG")
    p.add_argument("--size", type=int, default=512,
                   help="output edge length in px (default: 512)")
    p.add_argument("--contrast", type=float, default=1.15,
                   help="contrast multiplier (default: 1.15)")
    p.add_argument("--brightness", type=float, default=1.0,
                   help="brightness multiplier (default: 1.0)")
    p.add_argument("--no-bg-removal", action="store_true",
                   help="skip rembg even if it is installed")
    p.add_argument("--no-crop", action="store_true",
                   help="keep the original framing instead of cropping to "
                        "the subject after background removal")
    p.add_argument("--invert", action="store_true",
                   help="invert tones (for dark subjects on light backgrounds)")
    args = p.parse_args()

    if not os.path.isfile(args.input):
        raise SystemExit(f"no such file: {args.input}")

    img = Image.open(args.input)
    if img.mode != "RGB":
        img = img.convert("RGB")

    removed = False
    if not args.no_bg_removal:
        img, removed = remove_background(img)
        if not removed:
            print("rembg not installed - skipping background removal",
                  file=sys.stderr)

    if removed and not args.no_crop:
        # With the background gone, the subject is whatever is not white.
        # Crop to it and pad back to a square so the face fills the frame
        # instead of floating in the corner of the original photo.
        mask = ImageOps.invert(ImageOps.grayscale(img)).point(
            lambda p: 255 if p > 25 else 0)
        box = mask.getbbox()
        if box:
            img = img.crop(box)
            edge = max(img.size)
            img = ImageOps.pad(img, (edge, edge), color=(255, 255, 255),
                               centering=(0.5, 0.5))

    img = ImageOps.fit(img, (args.size, args.size), Image.LANCZOS)
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(args.contrast)
    img = ImageEnhance.Brightness(img).enhance(args.brightness)
    # Stretch the histogram so the darkest pixel is black and lightest white.
    img = ImageOps.autocontrast(img, cutoff=1)

    if args.invert:
        img = ImageOps.invert(img)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    img.save(args.output)
    print(f"wrote {args.output} ({args.size}x{args.size} grayscale)")


if __name__ == "__main__":
    main()

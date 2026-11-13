"""
Batch resize + compress static images for the cleaning site.

Usage:
    python compress_images.py /path/to/static/images

What it does, for every .jpg/.jpeg/.png under that folder:
  - Resizes down to a max width (default 1200px) if larger — plenty for
    full-bleed cards/hero images on a typical site; adjust MAX_WIDTH below
    if your design needs bigger.
  - Re-saves as JPEG at quality=80 (visually near-identical, big size drop).
  - Also writes a .webp version next to it, quality=80, for browsers that
    support it (use with a <picture> tag + jpg fallback).
  - Skips a file if it's already small (under SKIP_UNDER_KB) to avoid
    needlessly touching files that are already fine.
  - Overwrites the original jpg/png in place (back up first if unsure —
    see the --dry-run flag).

Run with --dry-run first to see what it WOULD do without touching files.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

MAX_WIDTH = 1200  # px — resize anything wider than this
JPEG_QUALITY = 80
WEBP_QUALITY = 80
SKIP_UNDER_KB = 150  # don't bother reprocessing already-small files


def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def process_image(path: Path, dry_run: bool):
    orig_size = path.stat().st_size
    if orig_size < SKIP_UNDER_KB * 1024:
        print(f"  skip (already small, {human(orig_size)}): {path.name}")
        return

    try:
        img = Image.open(path)
        img = img.convert("RGB") if img.mode in ("RGBA", "P") else img
    except Exception as e:
        print(f"  ERROR opening {path}: {e}")
        return

    orig_w, orig_h = img.size
    if orig_w > MAX_WIDTH:
        ratio = MAX_WIDTH / orig_w
        new_size = (MAX_WIDTH, int(orig_h * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    if dry_run:
        print(
            f"  would resize {orig_w}x{orig_h} -> {img.size}, "
            f"recompress {human(orig_size)}: {path.name}"
        )
        return

    # Overwrite original as compressed JPEG
    img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    new_size = path.stat().st_size

    # Also write a WebP sibling
    webp_path = path.with_suffix(".webp")
    img.save(webp_path, "WEBP", quality=WEBP_QUALITY)
    webp_size = webp_path.stat().st_size

    print(
        f"  {path.name}: {human(orig_size)} -> {human(new_size)} "
        f"(jpg), {human(webp_size)} (webp)"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Path to the images folder to process")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing files",
    )
    args = parser.parse_args()

    root = Path(args.folder)
    if not root.exists():
        print(f"Folder not found: {root}")
        sys.exit(1)

    exts = {".jpg", ".jpeg", ".png"}
    files = [p for p in root.rglob("*") if p.suffix.lower() in exts]

    if not files:
        print("No jpg/jpeg/png files found.")
        return

    print(f"Found {len(files)} image(s) under {root}\n")
    for f in sorted(files):
        process_image(f, args.dry_run)

    print("\nDone." if not args.dry_run else "\nDry run complete — no files changed.")


if __name__ == "__main__":
    main()

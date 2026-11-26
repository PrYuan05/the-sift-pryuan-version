"""Crop the in-game screenshots for the wiki.

  python -I tools/wiki/crop_shots.py [shots_dir]     (default build/wikishots)

mob_<id>.png + mob_<id>_bg.png -> docs/wiki/img/mobs/<id>.png: the mob is found by differencing against the empty
background shot taken from the same camera, cropped square with a margin and scaled to 360 px.
biome_*, structure_*, arena_* -> docs/wiki/img/shots/<name>.jpg (960 px wide).
The screenshots come from a temporary client game test (see the wiki section of tools/wiki/README.md)."""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build/wikishots"
OUT = ROOT / "docs/wiki/img"


def crop_mob(shot, bg):
    a, b = Image.open(shot).convert("RGB"), Image.open(bg).convert("RGB")
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.MedianFilter(5))
    box = d.getbbox()
    if not box:
        return None
    x0, y0, x1, y1 = box
    side = int(max(x1 - x0, y1 - y0) * 1.18) + 16
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    l, t = max(0, cx - side // 2), max(0, cy - side // 2)
    r, btm = min(a.width, l + side), min(a.height, t + side)
    return a.crop((l, t, r, btm)).resize((360, 360), Image.LANCZOS) if (r - l) > 8 else None


def main():
    (OUT / "mobs").mkdir(parents=True, exist_ok=True)
    (OUT / "shots").mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(SRC.glob("*.png")):
        stem = f.stem
        if stem.startswith("mob_") and not stem.endswith("_bg"):
            bg = f.with_name(stem + "_bg.png")
            if bg.exists():
                im = crop_mob(f, bg)
                if im:
                    im.save(OUT / "mobs" / f"{stem[4:]}.png", optimize=True)
                    n += 1
                else:
                    print("no mob found in", f.name)
        elif stem.startswith(("biome_", "structure_", "arena_")):
            im = Image.open(f).convert("RGB")
            im = im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS)
            im.save(OUT / "shots" / f"{stem}.jpg", quality=86, optimize=True)
            n += 1
    print(f"cropped {n} images -> {OUT}")


if __name__ == "__main__":
    main()

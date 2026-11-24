"""Upgrade the five split placeholder mobs (nester, pollinator, seedling, sprout, sentinel) like the other mobs
(user requirement 3, 2026-11-24: more colour transitions, no over-jumping colours, no flat single colours).

  python -I tools/texture_pipeline/upgrade_placeholder_mobs.py [names...]

  1. the first run records the current split textures as the "originals" in
     .texture_backups/20261124_placeholder_split/ (files/textures/entity/<mob>.png + manifest.json in
     mob_texture_record's snapshot format); later runs always start from there
  2. mob_upgrade_rest.upgrade() (hue families, 8-step hue-shifted ramps, model-face lighting, mottle / strands; eyes and
     faces of 4 px or less untouched, each pixel's luminance moves at most 0.08) -> live <mob>.png
  3. paint_placeholder_mobs.build() rebuilds <mob>_tropical / _cold on the upgraded base (variant models unchanged)
  4. mob_texture_record's compare against the split snapshot: palette error <= 10 %, new hard jumps, soft
     transitions >= 20 %, identical alpha mask
"""
import importlib.util
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard  # noqa: E402
import mob_texture_record as mtr  # noqa: E402
import mob_upgrade_rest as mur  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
SNAPDIR = ROOT / ".texture_backups/20261124_placeholder_split"
MOBS = ("nester", "pollinator", "seedling", "sprout", "sentinel")

# material kinds per mob (mob_upgrade_rest format): hue ranges are the sheet's teal / mint / navy / blue / tan / pink
CFG = {
    "nester": {"default": "shell", "kinds": [(0, 30, 0.2, 1, 0, 1, "skin")], "glow": None},
    "pollinator": {"default": "fur", "kinds": [(150, 200, 0.3, 1, 0, 1, "skin"), (0, 30, 0.2, 1, 0, 1, "skin")],
                   "glow": None},
    "seedling": {"default": "skin", "kinds": [(150, 200, 0.3, 1, 0, 1, "plant")], "glow": None},
    "sprout": {"default": "shell", "kinds": [(20, 50, 0, 1, 0, 1, "skin")], "glow": None},
    "sentinel": {"default": "shell", "kinds": [(20, 50, 0, 1, 0, 1, "skin")], "glow": None},
}

_spec = importlib.util.spec_from_file_location("paint_placeholder_mobs", Path(__file__).resolve().parent /
                                               "paint_placeholder_mobs.py")
PP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PP)


def record_originals():
    """Copy the split textures once (never overwrite: they are the reference for every later run)."""
    import json, hashlib
    man_path = SNAPDIR / "manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {"textures": {}, "models": []}
    for m in MOBS:
        rel = f"textures/entity/{m}.png"
        dst = SNAPDIR / "files" / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RES / rel, dst)
        from PIL import Image
        img = Image.open(dst).convert("RGBA")
        pal = mtr.palette(img)
        man["textures"][rel] = {"size": img.size, "sha1": hashlib.sha1(dst.read_bytes()).hexdigest(),
                                "opaque": sum(c["count"] for c in pal), "colours": len(pal), "palette": pal}
        print("recorded original", rel)
    man_path.write_text(json.dumps(man, indent=1), encoding="utf-8")


def main():
    names = [a for a in sys.argv[1:] if a in MOBS] or list(MOBS)
    record_originals()
    mur.SNAP = SNAPDIR / "files"                     # upgrade() and compare() read the originals from here
    mur.MOBS.update(CFG)
    for m in names:
        out, fams = mur.upgrade(m)
        art_guard.save(out, RES / f"textures/entity/{m}.png")
        print(m, "families:", {f: k for f, k in fams.items()})
        for w in PP.build(m):
            print("  wrote", w.relative_to(ROOT))
    sys.exit(mur.compare(names, live=True))


if __name__ == "__main__":
    main()

"""Generate surgical emissive *_glowmask.png textures for naturally glowing PySift mobs (Plan 1).

Matches VanillaGlowLayer (RenderTypes.eyes):
  - Non-glowing pixels = (0, 0, 0, 0)
  - Glowing pixels = rich saturated RGB (scaled slightly so additive eyes blending stays jewel-vivid, not blown-out white)
Usage: python -I tools/texture_pipeline/build_glowmasks.py
"""
import colorsys, json, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
TEX = RES / "textures/entity"
GEO = RES / "geckolib/models/entity"

sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
sys.path.insert(0, str(ROOT / "tools/models"))
import mob_painter_v2 as mp  # noqa: E402
import geo_preview3d as gp3  # noqa: E402


def _make_glowmask(tex_path, geo_paths, predicate, intensity=0.85, out_path=None):
    img = Image.open(tex_path).convert("RGBA")
    W, H = img.size
    px = img.load()
    pmap, _ = mp.build_3d_pixel_map(geo_paths, (W, H)) if geo_paths else ({}, set())

    gm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gpx = gm.load()
    cnt = 0
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = mp.rgb_to_hsv((r, g, b))
            info = pmap.get((x, y))
            bone = info["bone"].lower() if info else ""
            wy = info["wy"] if info else 0.0
            w = predicate(r, g, b, h, s, v, bone, wy, x, y)
            if w > 0.0:
                k = min(1.0, w * intensity)
                gpx[x, y] = (int(round(r * k)), int(round(g * k)), int(round(b * k)), 255)
                cnt += 1

    dst = out_path or tex_path.with_name(tex_path.stem + "_glowmask.png")
    gm.save(dst)
    print(f"wrote {dst.name}: {cnt} glow px ({W}x{H})")
    return img, gm


def _render_night_preview(geo_path, base_img, gm_img, title, scale=6):
    """Simulate dark cave lighting (22% ambient) + additive RenderTypes.eyes glowmask in 3D!"""
    geo = json.loads(Path(geo_path).read_text(encoding="utf-8"))
    # Composite simulated night texture: 24% dark base + 100% emissive glowmask (clamped)
    W, H = base_img.size
    night = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bp, gp, np_ = base_img.load(), gm_img.load(), night.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = bp[x, y]
            if a == 0:
                continue
            gr, gg, gb, ga = gp[x, y]
            if ga > 0:
                np_[x, y] = (min(255, int(r * 0.28 + gr * 1.15)),
                             min(255, int(g * 0.28 + gg * 1.15)),
                             min(255, int(b * 0.28 + gb * 1.15)), a)
            else:
                np_[x, y] = (int(r * 0.26), int(g * 0.26), int(b * 0.30), a)
    return gp3.render_views(geo, night, scale=scale, title=title)


def build_all():
    previews = []

    # 1. Echo Golem: glowing soul crystal lantern cube ONLY (keep clay face mask unlit!)
    b, g = _make_glowmask(
        TEX / "echo_golem.png", [GEO / "echo_golem.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if ("crystal" in bone and v >= 0.42) else
            (0.90 if (mp.hue_in(h, 155, 205) and v >= 0.62 and wy >= 14.0) else 0.0)
        ), intensity=0.90,
    )
    previews.append(_render_night_preview(GEO / "echo_golem.geo.json", b, g, "echo_golem (Night Emissive)", scale=5))

    # 2. Blub Meadows: glowing aqua lantern bulb atop its tall stalk ONLY (wy >= 10.0)
    b, g = _make_glowmask(
        TEX / "blub_meadows.png", [GEO / "blub_meadows.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (wy >= 10.0 and mp.hue_in(h, 168, 208) and s >= 0.40 and v >= 0.60) else 0.0
        ), intensity=0.95,
    )
    previews.append(_render_night_preview(GEO / "blub_meadows.geo.json", b, g, "blub_meadows (Night Emissive)", scale=9))

    # 3. Fusefly (base + tropical + cold): glowing bright lantern core pixels on the body!
    for suf, geo_name, pred in [
        ("", "fusefly.geo.json",
         lambda r, g, b, h, s, v, bone, wy, x, y: 0.72 if (mp.hue_in(h, 25, 65) and v >= 0.80 and s >= 0.30) else 0.0),
        ("_tropical", "fusefly_tropical.geo.json",
         lambda r, g, b, h, s, v, bone, wy, x, y: 0.78 if (mp.hue_in(h, 15, 60) and v >= 0.78 and s >= 0.45) else 0.0),
        ("_cold", "fusefly_cold.geo.json",
         lambda r, g, b, h, s, v, bone, wy, x, y: 0.68 if (mp.hue_in(h, 130, 215) and v >= 0.72 and s >= 0.22 and "body" in bone) else 0.0),
    ]:
        b, g = _make_glowmask(TEX / f"fusefly{suf}.png", [GEO / geo_name], pred, intensity=0.82)
        if suf == "":
            previews.append(_render_night_preview(GEO / geo_name, b, g, "fusefly (Night Emissive)", scale=9))

    # 4. Hunter: glowing fiery orange-amber rim, horns & glowing cyan/white eyes!
    b, g = _make_glowmask(
        TEX / "hunter.png", [GEO / "hunter.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            0.95 if (mp.hue_in(h, 350, 32) and s >= 0.50 and v >= 0.62) else
            (1.0 if (s < 0.15 and v >= 0.75) else 0.0)
        ), intensity=0.90,
    )
    previews.append(_render_night_preview(GEO / "hunter.geo.json", b, g, "hunter (Night Emissive)", scale=6))

    # 5. Scavenger: glowing cyan cuffs/hands & visor eyes + warm golden crown dots
    b, g = _make_glowmask(
        TEX / "scavenger.png", [GEO / "scavenger.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 152, 200) and s >= 0.35 and v >= 0.68) else
            (0.65 if (mp.hue_in(h, 25, 65) and s >= 0.45 and v >= 0.74) else 0.0)
        ), intensity=0.88,
    )
    previews.append(_render_night_preview(GEO / "scavenger.geo.json", b, g, "scavenger (Night Emissive)", scale=6))

    # 6. Stalker: glowing bright cyan sculk eyes & bioluminescent dots
    b, g = _make_glowmask(
        TEX / "stalker.png", [GEO / "stalker.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 165, 210) and s >= 0.55 and v >= 0.62) else
            (0.90 if (s < 0.12 and v >= 0.80) else 0.0)
        ), intensity=0.90,
    )
    previews.append(_render_night_preview(GEO / "stalker.geo.json", b, g, "stalker (Night Emissive)", scale=7))

    # 7. Trapper: glowing cyan claws & vibrant magenta-pink lure spots & eye
    b, g = _make_glowmask(
        TEX / "trapper.png", [GEO / "trapper.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 155, 202) and s >= 0.38 and v >= 0.68) else
            (0.75 if (mp.hue_in(h, 310, 355) and s >= 0.42 and v >= 0.74) else
             (1.0 if (s < 0.12 and v >= 0.82) else 0.0))
        ), intensity=0.88,
    )
    previews.append(_render_night_preview(GEO / "trapper.geo.json", b, g, "trapper (Night Emissive)", scale=6))

    # 8. Sculk Cube: glowing cyan eyes & bioluminescent pores
    b, g = _make_glowmask(
        TEX / "sculk_cube.png", [GEO / "sculk_cube.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 168, 205) and s >= 0.55 and v >= 0.52) else 0.0
        ), intensity=0.95,
    )
    previews.append(_render_night_preview(GEO / "sculk_cube.geo.json", b, g, "sculk_cube (Night Emissive)", scale=8))

    # 9. Sculk Maw: glowing cyan soul core crystal
    b, g = _make_glowmask(
        TEX / "sculk_maw.png", [GEO / "sculk_maw.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 165, 205) and s >= 0.42 and v >= 0.58) else 0.0
        ), intensity=0.92,
    )
    previews.append(_render_night_preview(GEO / "sculk_maw.geo.json", b, g, "sculk_maw (Night Emissive)", scale=8))

    # 10. Mourner: glowing cyan soul diamond on back (keep horns/feet bone unlit via hue 160..210!)
    b, g = _make_glowmask(
        TEX / "mourner.png", [GEO / "mourner.geo.json"],
        lambda r, g, b, h, s, v, bone, wy, x, y: (
            1.0 if (mp.hue_in(h, 160, 210) and s >= 0.14 and v >= 0.62 and wy < 20.0) else 0.0
        ), intensity=0.95,
    )
    previews.append(_render_night_preview(GEO / "mourner.geo.json", b, g, "mourner (Night Emissive)", scale=4))

    # Stack into 2-column night emissive showcase sheet
    col_a, col_b = previews[:5], previews[5:]
    wa = max(im.width for im in col_a)
    wb = max(im.width for im in col_b)
    ha = sum(im.height for im in col_a) + 8 * (len(col_a) - 1)
    hb = sum(im.height for im in col_b) + 8 * (len(col_b) - 1)
    sheet = Image.new("RGB", (wa + wb + 12, max(ha, hb)), (14, 16, 22))
    y = 0
    for im in col_a:
        sheet.paste(im.convert("RGB"), (0, y)); y += im.height + 8
    y = 0
    for im in col_b:
        sheet.paste(im.convert("RGB"), (wa + 12, y)); y += im.height + 8
    out_sheet = ROOT / "build/glowmasks_preview_3d.png"
    sheet.save(out_sheet)
    print("saved night preview sheet:", out_sheet)


if __name__ == "__main__":
    build_all()

"""Preview the soul power models without starting the game.
Usage: python -I tools/progression/preview_soul_power.py <project>

Writes build/soul_power_preview/:
  items.png   every soul power item model (casing + parts in the resting pose), seen like an inventory block
  gears.gif   a gear train seen from above (small - small - large - small): the teeth must stay in each other's gaps
              (the same angles and half-tooth offsets as client/soulpower/SoulPowerRenderer)
Renders with tools/worldgen/veg_models.py; vanilla textures are read from the Loom client jar."""
import io, math, sys, zipfile
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools/worldgen"))
sys.argv = [sys.argv[0], str(P)]
import veg_models as V  # noqa: E402

JAR = zipfile.ZipFile(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar")
OUT = P / "build/soul_power_preview"
OUT.mkdir(parents=True, exist_ok=True)
_cache = {}


def tex_image(ref, cache=_cache):
    if ref not in cache:
        ns, path = ref.split(":") if ":" in ref else ("minecraft", ref)
        if ns == "pysift":
            cache[ref] = Image.open(V.A / "textures" / (path + ".png")).convert("RGBA")
        else:
            cache[ref] = Image.open(io.BytesIO(JAR.read(f"assets/minecraft/textures/{path}.png"))).convert("RGBA")
        im = cache[ref]
        if im.height > im.width:   # animated: first frame
            cache[ref] = im.crop((0, 0, im.width, im.width))
    return cache[ref]


V.tex_image = tex_image
_orig = V.element_transform


def element_transform(e):
    """veg_models' own transform, then the extra pose of a moving part (for the gear animation)."""
    f = _orig(e)
    post = e.get("_post")
    return (lambda p: post(f(p))) if post else f


V.element_transform = element_transform


def model(ref):
    return V.load_model(ref)


# ------------------------------------------------------------------ items
names = ["spirit_engine", "soul_shaft", "soul_cogwheel", "large_soul_cogwheel", "soul_gauge", "soul_grinder",
         "soul_wave_emitter", "soul_wave_receiver", "soul_sifter",
         "charoite_beam_emitter", "charoite_beam_receiver", "charoite_prism",
         "soul_vein_node", "soul_veined_stone"]
tiles = []
for n in names:
    el, tx = model(f"pysift:item/{n}")
    tiles.append(V.render(el, tx, None, size=160, yaw=35, pitch=-28))
sheet = Image.new("RGBA", (160 * 4, 160 * 4), (40, 44, 52, 255))
for i, im in enumerate(tiles):
    sheet.alpha_composite(im, ((i % 4) * 160, (i // 4) * 160))
sheet.save(OUT / "items.png")


# ------------------------------------------------------------------ gear train, top view
def spin_y(deg, dx, dz):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)

    def f(p):
        x, y, z = p[0] - 8, p[1], p[2] - 8
        # joml rotateY(+a) (counter-clockwise seen from above): x' = x cos + z sin, z' = -x sin + z cos
        x, z = x * c + z * s, -x * s + z * c
        return (x + 8 + dx * 16, y, z + 8 + dz * 16)
    return f


TRAIN = [((0, 0), "cog", 1.0), ((1, 0), "cog", -1.0), ((2, 1), "large_cog", 0.5), ((3, 2), "cog", -1.0)]
frames = []
for step in range(24):
    base = step * 3.75   # degrees per frame for the first cog
    elements = []
    for (x, z), part, ratio in TRAIN:
        el, tx = model(f"pysift:block/soul_power_parts/{part}")
        even = (x + z) % 2 == 0
        offset = (0 if even else 11.25) if part == "large_cog" else (22.5 if even else 0)
        for e in el:
            e = dict(e)
            e["_post"] = spin_y(base * ratio + offset, x, z)
            elements.append(e)
        textures = tx
    im = V.render(elements, textures, None, size=480, yaw=0, pitch=-90)
    bg = Image.new("RGBA", im.size, (40, 44, 52, 255))
    bg.alpha_composite(im)
    frames.append(bg.convert("P", palette=Image.ADAPTIVE))
frames[0].save(OUT / "gears.gif", save_all=True, append_images=frames[1:], duration=80, loop=0)
print("wrote", OUT / "items.png", OUT / "gears.gif")

"""Install the user's Blockbench-converted SculkMonstrosity (GeckoLib geo + 256x256 texture) into the mod.
Usage: python -I tools/models/install_sculk_converted.py <project> <import_dir> [--install]

<import_dir> holds geo.json and bb_texture_0.png (copies of the downloaded files). Steps:
  1. bones renamed to the names the existing animations use (hitbox -> root, leg1 -> right_leg, arm1 -> right_arm ...);
     +x is the model's right side, as in the previous model. New parts keep their own names.
  2. per-face UV regions are kept exactly as exported: a region smaller than its face is stretched over the face by
     GeckoLib just as Blockbench shows it. (Resizing them to the face size was tried and pulled neighbouring texture
     parts and transparent pixels into the faces, so they are only listed.)
  2b. the shoulder flame cubes are removed (bones kept): the client's SoulFireShoulderLayer renders the vanilla soul
     fire block on those bones, so the fire uses vanilla's texture and flicker animation.
  3. glowmask: the bright cyan pixels of the texture (eyes, core, soul flames) -> <texture>_glowmask.png, read by
     VanillaGlowLayer.
  4. animations: the 8 existing animations are kept; jaw / soul flame keyframes are added to roar, sonic_charge,
     sonic_release, death and idle.
Without --install only build/models/sculk_converted/ is written (geo, texture, glowmask, previews). --install backs the
current geo, texture, glowmask and animation up to .texture_backups/<stamp>_sculk_converted/ and replaces them."""
import sys, json, copy, shutil, colorsys, datetime
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geo_textured_view import render

P = Path(sys.argv[1]).resolve()
SRC = Path(sys.argv[2]).resolve()
INSTALL = "--install" in sys.argv
OUT = P / "build/models/sculk_converted"
A = P / "src/main/resources/assets/pysift"
GEO = A / "geckolib/models/entity/sculk_monstrosity.geo.json"
ANIM = A / "geckolib/animations/entity/sculk_monstrosity.animation.json"
TEX = A / "textures/entity/sculk_monstrosity.png"
GLOW = A / "textures/entity/sculk_monstrosity_glowmask.png"

RENAME = {
    "hitbox": "root", "leg1": "right_leg", "leg2": "left_leg", "bone": "hip",
    "arm1": "right_arm", "arm_middle_0": "right_forearm",
    "finger_right_1": "right_finger_1", "finger_right_2": "right_finger_2", "finger_right_3": "right_finger_3",
    "arm2": "left_arm", "arm_middle_1": "left_forearm",
    "finger_left_1": "left_finger_1", "finger_left_2": "left_finger_2", "finger_left_3": "left_finger_3",
}
FIRE_BONES = ("shoulder_flame_right", "shoulder_flame_left")
FACE_DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def convert(geo, tex_size):
    geo = copy.deepcopy(geo)
    g = geo["minecraft:geometry"][0]
    g["description"]["identifier"] = "geometry.sculk_monstrosity"
    for b in g["bones"]:
        b["name"] = RENAME.get(b["name"], b["name"])
        if "parent" in b:
            b["parent"] = RENAME.get(b["parent"], b["parent"])
    # shoulder flames: the cubes go, the bones stay - SoulFireShoulderLayer draws the vanilla soul fire block there
    for b in g["bones"]:
        if b["name"] in FIRE_BONES:
            b.pop("cubes", None)
    fixed, skipped = [], []
    tw, th = tex_size
    for b in g["bones"]:
        for c in b.get("cubes", []):
            for face, (ia, ib) in FACE_DIMS.items():
                f = c.get("uv", {}).get(face)
                if not f:
                    continue
                w, h = f["uv_size"]
                want = (c["size"][ia], c["size"][ib])
                if (abs(w), abs(h)) == want:
                    continue
                skipped.append(f"{b['name']}.{face}: uv {[w, h]} stretched over face {want[0]}x{want[1]} (kept)")
    return geo, fixed, skipped


def glowmask(tex):
    out = Image.new("RGBA", tex.size, (0, 0, 0, 0))
    src, dst = tex.load(), out.load()
    n = 0
    for y in range(tex.height):
        for x in range(tex.width):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.44 <= h <= 0.56 and s >= 0.35 and v >= 0.55:      # bright cyan / aqua (eyes, core, soul flames)
                dst[x, y] = (r, g, b, a)
                n += 1
    return out, n


def add_keys(anims):
    a = copy.deepcopy(anims)
    A_ = lambda n: a["animations"][f"animation.sculk_monstrosity.{n}"]["bones"]
    # jaw: +x tips the front of the jaw down (opens the mouth)
    A_("roar")["jaw"] = {"rotation": {"0.0": [0, 0, 0], "0.4": [28, 0, 0], "1.6": [28, 0, 0], "2.0": [0, 0, 0]}}
    A_("sonic_charge")["jaw"] = {"rotation": {"0.0": [0, 0, 0], "1.5": [20, 0, 0], "1.7": [22, 0, 0]}}
    A_("sonic_release")["jaw"] = {"rotation": {"0.0": [22, 0, 0], "0.1": [35, 0, 0], "0.45": [35, 0, 0], "0.6": [0, 0, 0]}}
    A_("death")["jaw"] = {"rotation": {"0.0": [0, 0, 0], "0.6": [30, 0, 0]}}
    for side, phase in (("right", "0.0"), ("left", "0.75")):
        A_("idle")[f"shoulder_flame_{side}"] = {"scale": {"0.0": [1, 1, 1], "0.75": [1.06, 1.18, 1.06], "1.5": [1, 1, 1],
                                                          "2.25": [1.06, 1.18, 1.06], "3.0": [1, 1, 1]}}
        A_("roar")[f"shoulder_flame_{side}"] = {"scale": {"0.0": [1, 1, 1], "0.4": [1.15, 1.45, 1.15],
                                                          "1.6": [1.15, 1.45, 1.15], "2.0": [1, 1, 1]}}
    return a


def check(geo, anims):
    names = {b["name"] for b in geo["minecraft:geometry"][0]["bones"]}
    used = {bn for an in anims["animations"].values() for bn in an.get("bones", {})}
    missing = sorted(used - names)
    ys = [c["origin"][1] for b in geo["minecraft:geometry"][0]["bones"] for c in b.get("cubes", [])]
    return missing, min(ys)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src_geo = json.loads((SRC / "geo.json").read_text(encoding="utf-8"))
    tex = Image.open(SRC / "bb_texture_0.png").convert("RGBA")
    geo, fixed, skipped = convert(src_geo, tex.size)
    anims = add_keys(json.loads(ANIM.read_text(encoding="utf-8")))
    missing, min_y = check(geo, anims)
    glow, n_glow = glowmask(tex)
    (OUT / "sculk_monstrosity.geo.json").write_text(json.dumps(geo, indent="\t") + "\n", encoding="utf-8")
    (OUT / "sculk_monstrosity.animation.json").write_text(json.dumps(anims, indent="\t") + "\n", encoding="utf-8")
    tex.save(OUT / "sculk_monstrosity.png")
    glow.save(OUT / "sculk_monstrosity_glowmask.png")
    before = render(src_geo, tex, 4)
    after = render(geo, tex, 4)
    sheet = Image.new("RGBA", (before.width, before.height * 2 + 10), (20, 20, 24, 255))
    sheet.alpha_composite(before, (0, 0))
    sheet.alpha_composite(after, (0, before.height + 10))
    sheet.save(OUT / "preview_uv_before_after.png")
    gp = Image.new("RGBA", (512, 256), (20, 20, 24, 255))
    gp.alpha_composite(tex, (0, 0))
    gp.alpha_composite(glow, (256, 0))
    gp.resize((1024, 512), Image.Resampling.NEAREST).save(OUT / "preview_glowmask.png")
    print(f"bones renamed: {len(RENAME)}; stretched uv faces kept as exported: {len(skipped)}; glow pixels {n_glow}")
    print(f"animation bones missing from the model: {missing}; lowest cube y = {min_y}")
    if missing or min_y < 0:
        sys.exit("checks failed - not installing")
    if not INSTALL:
        print(f"preview only: {OUT.relative_to(P)}")
        return
    bk = P / ".texture_backups" / f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}_sculk_converted"
    for f in (GEO, ANIM, TEX, GLOW):
        if f.exists():
            (bk / f.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, bk / f.relative_to(P))
    shutil.copy2(OUT / "sculk_monstrosity.geo.json", GEO)
    shutil.copy2(OUT / "sculk_monstrosity.animation.json", ANIM)
    shutil.copy2(OUT / "sculk_monstrosity.png", TEX)
    shutil.copy2(OUT / "sculk_monstrosity_glowmask.png", GLOW)
    print(f"installed; previous files backed up to {bk.relative_to(P)}")


if __name__ == "__main__":
    main()

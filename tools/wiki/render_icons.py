"""Inventory-style icons for the wiki: every pysift item / block, plus the vanilla items the recipes and loot tables use.

  python -I tools/wiki/render_icons.py [ids...]      (no ids: everything build_wiki.py needs, see icon_ids())

Reads the modern item definitions (assets/<ns>/items/<id>.json), follows select / condition / composite / special to a
plain model, resolves the parent chain (vanilla models come from the Loom client jar) and draws:
  * block models with elements: an isometric view like the inventory (top, south = left, east = right faces, shaded
    1.0 / 0.8 / 0.62), every element with its own uvs, back to front
  * item/generated, item/handheld and cross-type models: the flat layer textures
Output: docs/wiki/img/icons.png (64 px cells) and docs/wiki/img/icons.json {"ns:id": index}.
Missing models fall back to the item texture or a "?" cell; the ids are printed so they can be fixed."""
import json, math, sys, zipfile
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/main/resources/assets"
OUT = ROOT / "docs/wiki/img"
CELL = 64
SS = 4                      # supersampling of the isometric render
JAR_CANDIDATES = [Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client.jar",
                  Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar"]
JAR = zipfile.ZipFile(next(p for p in JAR_CANDIDATES if p.exists()))
JAR_NAMES = set(JAR.namelist())
TINT = (122, 196, 150)      # grass / leaves with a tintindex: a Sift mint green (the game tints them by floor / biome)


def split(ref, default_ns="minecraft"):
    ref = ref.lstrip("#")
    ns, _, path = ref.partition(":") if ":" in ref else (default_ns, "", ref)
    return ns, path


def read_asset(ns, rel):
    p = ASSETS / ns / rel
    if p.exists():
        return p.read_bytes()
    name = f"assets/{ns}/{rel}"
    if name in JAR_NAMES:
        return JAR.read(name)
    return None


@lru_cache(None)
def load_json(ns, rel):
    b = read_asset(ns, rel)
    return json.loads(b) if b else None


@lru_cache(None)
def texture(ref):
    ns, path = split(ref)
    b = read_asset(ns, f"textures/{path}.png")
    if not b:
        return None
    import io
    im = Image.open(io.BytesIO(b)).convert("RGBA")
    if im.height > im.width:                       # animated: first frame
        im = im.crop((0, 0, im.width, im.width))
    return im


@lru_cache(None)
def model(ref):
    """Fully resolved model: {"textures": {...}, "elements": [...]|None, "chain": [parents]}."""
    ns, path = split(ref)
    d = load_json(ns, f"models/{path}.json")
    if d is None:
        return None
    out = {"textures": {}, "elements": None, "chain": [f"{ns}:{path}"]}
    if "parent" in d:
        p = model(d["parent"]) if not d["parent"].startswith("builtin/") else None
        if p:
            out = {"textures": dict(p["textures"]), "elements": p["elements"], "chain": out["chain"] + p["chain"]}
        else:
            out["chain"].append(d["parent"])
    out["textures"].update(d.get("textures", {}))
    if "elements" in d:
        out["elements"] = d["elements"]
    return out


def resolve_tex(m, key, depth=0):
    v = m["textures"].get(key.lstrip("#"))
    if isinstance(v, dict):                         # 26.3: {"sprite": ..., "force_translucent": true}
        v = v.get("sprite")
    if v is None or depth > 8:
        return None
    return resolve_tex(m, v, depth + 1) if v.startswith("#") else v


def pick_model(node):
    """First plain model reference inside an item definition node."""
    if not isinstance(node, dict):
        return None
    t = node.get("type", "")
    if t.endswith("model") and "model" in node:
        return node["model"]
    if t.endswith("special"):
        return node.get("base")
    for c in node.get("cases", []):                 # the inventory look: the display_context case that lists "gui"
        when = c.get("when")
        if (when == "gui" or isinstance(when, list) and "gui" in when) and (r := pick_model(c.get("model"))):
            return r
    for key in ("fallback", "on_true", "on_false"):
        if key in node and (r := pick_model(node[key])):
            return r
    for key in ("cases", "models", "entries"):
        for c in node.get(key, []):
            r = pick_model(c.get("model", c) if isinstance(c, dict) else c)
            if r:
                return r
    return None


# ------------------------------------------------------------------------------------------------------ isometric
def project(x, y, z, s):
    c, k = math.cos(math.radians(30)), math.sin(math.radians(30))
    return ((x - z) * c * s, (x + z) * k * s - y * s)


def face_quad(fr, to, face):
    (x0, y0, z0), (x1, y1, z1) = fr, to
    if face == "up":
        return (x0, y1, z0), (x1, y1, z0), (x0, y1, z1)
    if face == "south":
        return (x0, y1, z1), (x1, y1, z1), (x0, y0, z1)
    if face == "east":
        return (x1, y1, z1), (x1, y1, z0), (x1, y0, z1)


def default_uv(fr, to, face):
    (x0, y0, z0), (x1, y1, z1) = fr, to
    return {"up": [x0, z0, x1, z1], "south": [x0, 16 - y1, x1, 16 - y0], "east": [16 - z1, 16 - y1, 16 - z0, 16 - y0]}[face]


SHADE = {"up": 1.0, "south": 0.8, "east": 0.62}


def render_iso(m, parts=None):
    """Isometric view of one model, or of several (model, (dx, dy, dz)) parts such as a bed's head + foot."""
    parts = parts or [(m, (0, 0, 0))]
    size = CELL * SS
    canvas = Image.new("RGBA", (size, size))
    elems = []
    for pm, (dx, dy, dz) in parts:
        for e in pm["elements"] or []:
            fr = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2] + dz]
            to = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2] + dz]
            elems.append((pm, e, fr, to))
    if not elems:
        return None
    # fit: a lone full cube keeps the inventory size; bigger shapes (a bed is two blocks long) shrink to fit
    pts = [project(x, y, z, 1) for _m, _e, fr, to in elems for x in (fr[0], to[0]) for y in (fr[1], to[1])
           for z in (fr[2], to[2])]
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    s = min(size / 16 / 1.75, 0.9 * size / max(maxx - minx, maxy - miny, 1))
    ox = size / 2 - (minx + maxx) / 2 * s
    oy = size / 2 - (miny + maxy) / 2 * s
    order = sorted(elems, key=lambda t: (t[2][0] + t[3][0]) + (t[2][2] + t[3][2]) + 0.5 * (t[2][1] + t[3][1]))
    drawn = False
    for pm, e, fr, to in order:
        for face in ("up", "south", "east"):
            fd = e.get("faces", {}).get(face)
            if not fd:
                continue
            tref = resolve_tex(pm, fd.get("texture", ""))
            tex = texture(tref) if tref else None
            if tex is None:
                continue
            uv = fd.get("uv") or default_uv(e["from"], e["to"], face)
            tw, th = tex.size
            u0, v0, u1, v1 = (uv[0] * tw / 16, uv[1] * th / 16, uv[2] * tw / 16, uv[3] * th / 16)
            p0, pu, pv = (project(*q, s) for q in face_quad(fr, to, face))
            p0, pu, pv = [(x + ox, y + oy) for x, y in (p0, pu, pv)]
            ax, ay = pu[0] - p0[0], pu[1] - p0[1]
            bx, by = pv[0] - p0[0], pv[1] - p0[1]
            det = ax * by - ay * bx
            if abs(det) < 1e-6:
                continue
            # output (X, Y) -> (a, b): [X - p0] = a*A + b*B ; input = (u0 + a*(u1-u0), v0 + b*(v1-v0))
            ia, ib = by / det, -bx / det
            ja, jb = -ay / det, ax / det
            du, dv = u1 - u0, v1 - v0
            coeffs = (du * ia, du * ib, u0 - du * (ia * p0[0] + ib * p0[1]),
                      dv * ja, dv * jb, v0 - dv * (ja * p0[0] + jb * p0[1]))
            layer = tex.transform((size, size), Image.AFFINE, coeffs, resample=Image.NEAREST)
            quad = [p0, pu, (pu[0] + bx, pu[1] + by), pv]
            mask = Image.new("L", (size, size))
            ImageDraw.Draw(mask).polygon(quad, fill=255)
            sh = SHADE[face]
            tint = TINT if "tintindex" in fd else (255, 255, 255)
            r, g, b, al = layer.split()
            r = r.point(lambda v, f=sh * tint[0] / 255: int(v * f))
            g = g.point(lambda v, f=sh * tint[1] / 255: int(v * f))
            b = b.point(lambda v, f=sh * tint[2] / 255: int(v * f))
            al = Image.composite(al, Image.new("L", (size, size)), mask)
            canvas.alpha_composite(Image.merge("RGBA", (r, g, b, al)))
            drawn = True
    if not drawn:
        return None
    return canvas.resize((CELL, CELL), Image.BOX) if canvas.getbbox() else None


# Sift dye colours (block/SiftColors.java) and vanilla dye colours, for banners
DYE_RGB = {"teal": 0x2EB8A6, "mint": 0x8FE3C0, "coral": 0xF08A6C, "amber": 0xE8A33A, "lavender": 0xB39DDB,
           "rose": 0xD9536E, "soul_blue": 0x8EC5F0, "void": 0x3A2E48, "dusk_gold": 0xF2CF6B}


def banner_icon(color):
    """A banner seen from the front, like the inventory: the flag (entity/banner/base.png front, tinted) on its pole."""
    base = texture("minecraft:entity/banner/base")
    rgb = DYE_RGB.get(color, 0xFFFFFF)
    tint = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
    out = Image.new("RGBA", (24, 48))
    wood = (143, 119, 72, 255)
    dark = (104, 83, 50, 255)
    d = ImageDraw.Draw(out)
    d.rectangle((11, 0, 12, 47), fill=wood)
    d.rectangle((13, 0, 13, 47), fill=dark)
    d.rectangle((1, 0, 22, 1), fill=wood)
    if base is not None:
        flag = base.crop((1, 1, 21, 41)).convert("RGBA")
        r, g, b, al = flag.split()
        flag = Image.merge("RGBA", (r.point(lambda v: v * tint[0] // 255), g.point(lambda v: v * tint[1] // 255),
                                    b.point(lambda v: v * tint[2] // 255), al))
        out.alpha_composite(flag, (2, 2))
    big = out.resize((24 * 2, 48 * 2), Image.NEAREST)
    cell = Image.new("RGBA", (CELL * 2, CELL * 2))
    cell.alpha_composite(big, ((CELL * 2 - big.width) // 2, (CELL * 2 - big.height) // 2))
    return cell.resize((CELL, CELL), Image.NEAREST)


def flat(texs, tinted=()):
    out = Image.new("RGBA", (16, 16))
    for i, t in enumerate(texs):
        im = texture(t)
        if im is None:
            continue
        im = im.resize((16, 16), Image.NEAREST) if im.size != (16, 16) else im
        if i in tinted:
            r, g, b, a = im.split()
            im = Image.merge("RGBA", (r.point(lambda v: v * TINT[0] // 255), g.point(lambda v: v * TINT[1] // 255),
                                      b.point(lambda v: v * TINT[2] // 255), a))
        out.alpha_composite(im)
    return out.resize((CELL - 8, CELL - 8), Image.NEAREST) if out.getbbox() else None


def pad(im):
    if im is None:
        return None
    if im.size == (CELL, CELL):
        return im
    c = Image.new("RGBA", (CELL, CELL))
    c.alpha_composite(im, ((CELL - im.width) // 2, (CELL - im.height) // 2))
    return c


def composite_parts(node):
    """[(model, (dx, dy, dz))] of a composite item model whose parts are plain models (beds: head + foot)."""
    out = []
    for c in node.get("models", []):
        if not str(c.get("type", "")).endswith("model") or "model" not in c:
            return None
        mm = model(c["model"])
        if mm is None or not mm["elements"]:
            return None
        t = (c.get("transformation") or {}).get("translation", [0, 0, 0])
        out.append((mm, (t[0] * 16, t[1] * 16, t[2] * 16)))
    return out or None


def icon(item_id):
    ns, path = split(item_id)
    d = load_json(ns, f"items/{path}.json")
    if path.endswith("_banner") and not path.endswith("wall_banner"):
        return banner_icon(path[: -len("_banner")])
    if d and str(d["model"].get("type", "")).endswith("composite"):
        parts = composite_parts(d["model"])
        if parts and (img := render_iso(parts[0][0], parts)):
            return img
    ref = pick_model(d["model"]) if d else None
    m = model(ref) if ref else None
    if m is None and load_json(ns, f"models/item/{path}.json"):
        m = model(f"{ns}:item/{path}")
    if m:
        chain = m["chain"]
        if any(c.endswith(("item/generated", "item/handheld", "item/handheld_rod", "item/handheld_mace"))
               or "builtin/generated" in c for c in chain):
            layers = sorted((k for k in m["textures"] if k.startswith("layer")), key=lambda k: int(k[5:]))
            img = flat([resolve_tex(m, k) for k in layers])
            if img:
                return pad(img)
        if any(c.split(":")[-1].split("/")[-1] in ("cross", "tinted_cross", "flower_pot_cross") for c in chain) \
                or any("cross" in c.split("/")[-1] and "pysift:" in c for c in chain[1:]):
            t = resolve_tex(m, "cross") or resolve_tex(m, "plant") or resolve_tex(m, "particle")
            img = flat([t], tinted=(0,) if "tinted" in " ".join(chain) else ())
            if img:
                return pad(img)
        if m["elements"]:
            img = render_iso(m)
            if img:
                return img
        t = resolve_tex(m, "particle") or resolve_tex(m, "all")
        if t and (img := flat([t])):
            return pad(img)
    for guess in (f"{ns}:item/{path}", f"{ns}:block/{path}"):
        if texture(guess):
            return pad(flat([guess]))
    return None


def question():
    c = Image.new("RGBA", (CELL, CELL))
    d = ImageDraw.Draw(c)
    d.rectangle((6, 6, CELL - 7, CELL - 7), outline=(150, 120, 190, 255), width=3)
    d.text((CELL // 2 - 4, CELL // 2 - 7), "?", fill=(200, 180, 230, 255))
    return c


def build(ids):
    OUT.mkdir(parents=True, exist_ok=True)
    ids = sorted(set(ids))
    cols = 32
    rows = math.ceil((len(ids) + 1) / cols)
    atlas = Image.new("RGBA", (cols * CELL, rows * CELL))
    index, missing = {}, []
    atlas.alpha_composite(question(), (0, 0))
    for n, i in enumerate(ids, start=1):
        try:
            im = icon(i)
        except Exception as ex:  # noqa: BLE001 - one broken model must not stop the atlas
            print("error", i, ex)
            im = None
        if im is None:
            missing.append(i)
            index[i] = 0
            continue
        atlas.alpha_composite(im, ((n % cols) * CELL, (n // cols) * CELL))
        index[i] = n
    atlas.save(OUT / "icons.png", optimize=True)
    (OUT / "icons.json").write_text(json.dumps({"cell": CELL, "cols": cols, "index": index}, ensure_ascii=False),
                                    encoding="utf-8")
    print(f"icons: {len(ids) - len(missing)} drawn, {len(missing)} missing -> {OUT / 'icons.png'}")
    if missing:
        print("missing:", " ".join(missing[:80]))
    return index


def all_pysift_items():
    return [f"pysift:{p.stem}" for p in (ASSETS / "pysift/items").glob("*.json")]


if __name__ == "__main__":
    args = sys.argv[1:]
    build(args or all_pysift_items())

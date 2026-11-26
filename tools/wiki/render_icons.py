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


def render_iso(m):
    size = CELL * SS
    canvas = Image.new("RGBA", (size, size))
    s = size / 16 / 1.75                            # a full cube spans ~ (2 * cos30 * 16) wide
    ox, oy = size / 2, size / 2 + 2 * s * 1.0 - 0.5 * s
    elems = m["elements"] or []
    order = sorted(elems, key=lambda e: (e["from"][0] + e["to"][0]) + (e["from"][2] + e["to"][2])
                   + 0.5 * (e["from"][1] + e["to"][1]))
    drawn = False
    for e in order:
        fr, to = e["from"], e["to"]
        for face in ("up", "south", "east"):
            fd = e.get("faces", {}).get(face)
            if not fd:
                continue
            tref = resolve_tex(m, fd.get("texture", ""))
            tex = texture(tref) if tref else None
            if tex is None:
                continue
            uv = fd.get("uv") or default_uv(fr, to, face)
            tw, th = tex.size
            u0, v0, u1, v1 = (uv[0] * tw / 16, uv[1] * th / 16, uv[2] * tw / 16, uv[3] * th / 16)
            p0, pu, pv = (project(*q, s) for q in face_quad(fr, to, face))
            p0, pu, pv = [(a + ox, b + oy) for a, b in (p0, pu, pv)]
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
            r, g, b, a = layer.split()
            r = r.point(lambda v, f=sh * tint[0] / 255: int(v * f))
            g = g.point(lambda v, f=sh * tint[1] / 255: int(v * f))
            b = b.point(lambda v, f=sh * tint[2] / 255: int(v * f))
            a = Image.composite(a, Image.new("L", (size, size)), mask)
            canvas.alpha_composite(Image.merge("RGBA", (r, g, b, a)))
            drawn = True
    if not drawn:
        return None
    bbox = canvas.getbbox()
    return canvas.resize((CELL, CELL), Image.BOX) if bbox else None


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


def icon(item_id):
    ns, path = split(item_id)
    d = load_json(ns, f"items/{path}.json")
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
    if path.endswith("_bed"):                       # beds are drawn by a special renderer: show the matching wool
        return icon(f"{ns}:{path[:-4]}_wool")
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

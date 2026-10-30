"""Soul crystal block: a translucent framed cube with a smaller crystal cube inside (minecraft-texture-crafter skill).
Usage: python -I tools/worldgen/paint_soul_crystal.py <project> [--apply]

Material brief:
  1. Identity: the crystal that condenses on the Echo Golem's head (SoulCrystal.java, light level 10).
  2. Physical: a clear shell (bevelled frame, almost no body colour, a glass glare) around a solid glowing core.
  3. Real world: a phantom / included crystal - a clear quartz shell grown round a smaller crystal inside it.
  4. Vanilla anchors: glass (translucent shell, bright frame, diagonal glare); the core keeps the ORIGINAL texture's structure
     (measured from the first version: light outer ring 0.88-0.92 with rounded corners, then 0.85, 0.79, a 0.77 centre with a
     few faint crosses) - lighter outside, a little deeper inside (user).
Colours: soul_willow_planks' own palette (#A4D7E9 #97C5D5 #8ACAC9 #74B6CC ... #4D90A4, H 180-196) - the golem's body and cage.

Files (textures/block/soul_crystal_block/):
  soul_crystal_block_outer.png (+ .mcmeta)  16 x 16*9 animated: frame 0 rests 3 s, then a 2 px glint sweeps the SHELL in 8 frames
  soul_crystal_block_inner.png              16 x 16, the core drawn in the middle 12 x 12 (uv 2..14), opaque, static
Model: inner cube 2..14 (no cullface) first, then the 0..16 shell (cullface, force_translucent); both light_emission 15.
Echo Golem: its crystal bone gets the same inner cube (12^3, uv (0,64), listed BEFORE the shell so the translucent pass draws it
first); the shell's (111,48) 16x16 gets the shell's rest frame, (0,64) 12x12 the core.
"""
import datetime, json, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
DIR = A / "textures/block/soul_crystal_block"
OUTER, INNER = DIR / "soul_crystal_block_outer.png", DIR / "soul_crystal_block_inner.png"
OLD = A / "textures/block/soul_crystal_block.png"
MODEL = A / "models/block/soul_crystal_block/soul_crystal_block.json"
GOLEM = A / "textures/entity/echo_golem.png"
GEO = A / "geckolib/models/entity/echo_golem.geo.json"
SHELL_UV, CORE_UV = (111, 48), (0, 64)
sys.path.insert(0, str(P / "tools"))
import art_guard

# soul_willow_planks, light -> deep, plus a near-white for the frame highlight
W0, L1, L2, M1, M2, D1, D2 = ((0xDF, 0xF5, 0xF8), (0xA4, 0xD7, 0xE9), (0x97, 0xC5, 0xD5), (0x8A, 0xCA, 0xC9), (0x74, 0xB6, 0xCC),
                              (0x52, 0x97, 0xAF), (0x4D, 0x90, 0xA4))
FRAMES = 9


def shell(framed=True):
    """16 x 16 of (rgb, alpha): nearly clear body, a short glare bar upper left; framed = the bevelled 1 px frame painted in
    (the golem's cube). The block draws its frame as geometry instead (connected_model), so its glass has none."""
    px = {(x, y): (L1, 45) for x in range(16) for y in range(16)}
    for (x, y) in ((11, 3), (12, 3), (12, 4), (3, 12), (4, 12)):
        px[(x, y)] = (L2, 70)                                      # two faint inclusions
    for i in range(16 if framed else 0):
        px[(i, 0)] = (L1, 230)
        px[(0, i)] = (L1, 230)
        px[(i, 15)] = (D1, 230)
        px[(15, i)] = (D1, 230)
    if framed:
        px[(0, 0)] = (W0, 240)
        px[(1, 0)] = (W0, 235)
        px[(0, 1)] = (W0, 235)
        px[(15, 15)] = (D2, 240)
        px[(15, 0)] = (L2, 230)
        px[(0, 15)] = (L2, 230)
    for k in range(4):                                             # glass glare
        px[(2 + k, 5 - k)] = (W0, 160)
    px[(2, 7)] = (W0, 120)
    px[(3, 6)] = (W0, 120)
    return px


def glint(px, f):
    """f = 0 rests; f = 1..8: a 2 px diagonal glint (x + y = d) brightens the shell and lifts its alpha."""
    if f == 0:
        return px
    out = dict(px)
    d = 2 + (f - 1) * 4
    for (x, y), (c, a) in px.items():
        if 1 <= x <= 14 and 1 <= y <= 14:
            s = x + y
            if s == d:
                out[(x, y)] = (W0, 200)
            elif s in (d - 1, d + 1):
                out[(x, y)] = (L1, max(a, 120))
    return out


def core():
    """12 x 12, the original texture's structure: rounded light ring, two lighter rings, deeper centre, faint crosses."""
    g = {}
    for y in range(12):
        for x in range(12):
            ring = min(x, y, 11 - x, 11 - y)
            g[(x, y)] = (L1, L2, M1)[ring] if ring < 3 else M2
    for (x, y) in ((0, 0), (11, 0), (0, 11), (11, 11)):           # rounded corners: one step lighter like the original
        g[(x, y)] = W0
    for (x, y) in ((1, 1), (10, 1), (1, 10), (10, 10)):
        g[(x, y)] = L1
    for cx, cy in ((4, 4), (7, 7)):                                # two faint crosses, apart (as sparse as the original)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (cx + dx, cy + dy)
            if min(q[0], q[1], 11 - q[0], 11 - q[1]) >= 3:
                g[q] = M1
    return g


def core_flat():
    """The block's core faces: the deeper centre colour with a few faint crosses, no ring (the light ring is the core's
    edge bars, so it disappears where two cores join)."""
    im = Image.new("RGBA", (16, 16), (*M2, 255))
    for cx, cy in ((4, 4), (11, 10), (6, 12), (12, 4)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            im.putpixel(((cx + dx) % 16, (cy + dy) % 16), (*M1, 255))
    return im


FRAME_COLS = {"w0": W0, "l1": L1, "l2": L2, "d1": D1}          # frame.png: 4 px wide columns of these colours


def frame_tex():
    im = Image.new("RGBA", (16, 16))
    for k, c in enumerate(FRAME_COLS.values()):
        for x in range(4 * k, 4 * k + 4):
            for y in range(16):
                im.putpixel((x, y), (*c, 255))
    return im


AX = {"west": (0, 0), "east": (0, 16), "down": (1, 0), "up": (1, 16), "north": (2, 0), "south": (2, 16)}
OPP = {"west": "east", "east": "west", "down": "up", "up": "down", "north": "south", "south": "north"}
EDGES = [(a, b) for a in AX for b in AX if a < b and AX[a][0] != AX[b][0]]   # 12 cube edges as pairs of faces
E = 0.01                                                            # bars stand this far out of their faces (no z-fighting)


def bar(d1, d2, lo, hi, inset, along_range):
    """A 1 px bar on the edge between faces d1 and d2 of the box [lo, hi]^3; along_range = its extent on the third axis."""
    f, t = [0, 0, 0], [0, 0, 0]
    for d in (d1, d2):
        axis, side = AX[d]
        if side == 0:
            f[axis], t[axis] = lo - E, lo + 1
        else:
            f[axis], t[axis] = hi - 1, hi + E
    third = ({0, 1, 2} - {AX[d1][0], AX[d2][0]}).pop()
    f[third], t[third] = along_range
    return f, t


def edge_colour(d1, d2):
    s = {d1, d2}
    if "up" in s:
        return "w0" if s & {"north", "west"} else "l1"
    if "down" in s:
        return "d1" if s & {"south", "east"} else "l2"
    return "l1" if s == {"north", "west"} else "d1" if s == {"south", "east"} else "l2"


def element(f, t, tex, faces=None, cull=None, uv=None):
    faces = faces or ("down", "up", "north", "south", "west", "east")
    out = {"from": f, "to": t, "light_emission": 15, "faces": {}}
    for d in faces:
        face = {"texture": tex}
        if uv:
            face["uv"] = uv
        if cull:
            face["cullface"] = d
        out["faces"][d] = face
    return out


def connected_models():
    """{model name: model json} and the multipart blockstate for the connected block."""
    base = "pysift:block/soul_crystal_block/"
    tex = {"particle": base + "soul_crystal_block_inner", "inner": base + "soul_crystal_block_inner",
           "frame": base + "soul_crystal_block_frame",
           "outer": {"sprite": base + "soul_crystal_block_outer", "force_translucent": True}}
    models, parts = {}, []

    def add(name, elements, when=None):
        models[name] = {"parent": "minecraft:block/block", "textures": tex, "elements": elements}
        part = {"apply": {"model": base + name}}
        if when:
            part["when"] = when
        parts.append(part)

    col_uv = lambda c: [4 * list(FRAME_COLS).index(c), 0, 4 * list(FRAME_COLS).index(c) + 1, 1]
    # always: the core and the glass shell (each shell face culls against a neighbouring crystal)
    add("soul_crystal_block_core", [element([2, 2, 2], [14, 14, 14], "#inner"),
                                    element([0, 0, 0], [16, 16, 16], "#outer", cull=True)])
    for d in AX:                                                    # the core reaches the edge towards a connected crystal
        axis, side = AX[d]
        f, t = [2, 2, 2], [14, 14, 14]
        f[axis], t[axis] = (0, 2) if side == 0 else (14, 16)
        add(f"soul_crystal_block_arm_{d}", [element(f, t, "#inner", faces=[x for x in AX if x not in (d, OPP[d])])], {d: "true"})
    for d1, d2 in EDGES:
        c = edge_colour(d1, d2)
        f, t = bar(d1, d2, 0, 16, 0, (0, 16))                        # the shell's frame
        add(f"soul_crystal_block_frame_{d1}_{d2}", [element(f, t, "#frame", uv=col_uv(c))], {d1: "false", d2: "false"})
        third = ({0, 1, 2} - {AX[d1][0], AX[d2][0]}).pop()
        lo_dir, hi_dir = [d for d in AX if AX[d][0] == third]
        f, t = bar(d1, d2, 2, 14, 0, (2, 14))                        # the core's light ring
        add(f"soul_crystal_block_ring_{d1}_{d2}", [element(f, t, "#frame", uv=col_uv("l1"))], {d1: "false", d2: "false"})
        for end, rng in ((lo_dir, (0, 2)), (hi_dir, (14, 16))):      # ... continued into a connected neighbour's core
            f, t = bar(d1, d2, 2, 14, 0, rng)
            add(f"soul_crystal_block_ring_{d1}_{d2}_{end}", [element(f, t, "#frame", uv=col_uv("l1"))],
                {d1: "false", d2: "false", end: "true"})
    inventory = {"parent": "minecraft:block/block", "textures": tex, "elements":
                 models["soul_crystal_block_core"]["elements"]
                 + [e for n, m in models.items() if n.startswith(("soul_crystal_block_frame_", "soul_crystal_block_ring_"))
                    and n.count("_") == 5 for e in m["elements"]]}
    models["soul_crystal_block"] = inventory                        # the item (and every unconnected state) look
    return models, {"multipart": parts}


def render_shell(px):
    im = Image.new("RGBA", (16, 16))
    im.putdata([(*px[(x, y)][0], px[(x, y)][1]) for y in range(16) for x in range(16)])
    return im


def render_core(g, size=16):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    o = (size - 12) // 2
    for (x, y), c in g.items():
        im.putpixel((x + o, y + o), (*c, 255))
    return im


def front_view(flat, glass, cells=((0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (4, 1))):
    """Front (north) faces of crystals at (column, row) cells, as the connected model draws them: core rectangle grown to the
    block edge towards connected neighbours, the core's light ring and the shell's frame only where no neighbour is."""
    cs = set(cells)
    W = (max(c for c, _ in cs) + 1) * 16
    H = (max(r for _, r in cs) + 1) * 16
    im = Image.new("RGBA", (W, H), (78, 128, 62, 255))
    for yy in range(0, H, 8):
        for xx in range(0, W, 8):
            if (xx // 8 + yy // 8) % 2:
                im.paste((64, 108, 52, 255), (xx, yy, xx + 8, yy + 8))
    for c, r in cs:
        L, R, U, D = (c - 1, r) in cs, (c + 1, r) in cs, (c, r - 1) in cs, (c, r + 1) in cs
        x0, y0 = c * 16, r * 16
        cx0, cx1 = (0 if L else 2), (16 if R else 14)
        cy0, cy1 = (0 if U else 2), (16 if D else 14)
        for y in range(cy0, cy1):
            for x in range(cx0, cx1):
                im.putpixel((x0 + x, y0 + y), flat.getpixel((x, y)))
        ring = (*L1, 255)
        for x in range(cx0, cx1):
            if not U:
                im.putpixel((x0 + x, y0 + 2), ring)
            if not D:
                im.putpixel((x0 + x, y0 + 13), ring)
        for y in range(cy0, cy1):
            if not L:
                im.putpixel((x0 + 2, y0 + y), ring)
            if not R:
                im.putpixel((x0 + 13, y0 + y), ring)
        im.alpha_composite(glass, (x0, y0))
        for i in range(16):
            for cond, px in ((not U, (i, 0)), (not D, (i, 15)), (not L, (0, i)), (not R, (15, i))):
                if cond:
                    col = L1 if px[1] == 0 or px[0] == 0 else D1
                    im.putpixel((x0 + px[0], y0 + px[1]), (*col, 255))
    return im.resize((W * 8, H * 8), Image.NEAREST).convert("RGB")


def model():
    faces = ("down", "up", "north", "south", "west", "east")
    return {"parent": "minecraft:block/block",
            "textures": {"particle": "pysift:block/soul_crystal_block/soul_crystal_block_inner",
                         "inner": "pysift:block/soul_crystal_block/soul_crystal_block_inner",
                         "outer": {"sprite": "pysift:block/soul_crystal_block/soul_crystal_block_outer", "force_translucent": True}},
            "elements": [
                {"from": [2, 2, 2], "to": [14, 14, 14], "light_emission": 15,
                 "faces": {d: {"uv": [2, 2, 14, 14], "texture": "#inner"} for d in faces}},
                {"from": [0, 0, 0], "to": [16, 16, 16], "light_emission": 15,
                 "faces": {d: {"uv": [0, 0, 16, 16], "texture": "#outer", "cullface": d} for d in faces}}]}


def golem_geo(doc):
    """crystal bone: the 12^3 core first (drawn before the translucent shell), then the original 16^3 shell."""
    d = doc["minecraft:geometry"][0]
    bone = next(b for b in d["bones"] if b["name"] == "crystal")
    shell_cube = next(c for c in bone["cubes"] if c.get("size") == [16, 16, 16])
    uv = {f: {"uv": list(CORE_UV), "uv_size": [12, 12]} for f in ("north", "east", "south", "west", "up", "down")}
    bone["cubes"] = [{"origin": [-6, 28, -6], "size": [12, 12, 12], "uv": uv}, shell_cube]
    return doc


def main():
    sp = shell()                                                    # framed: the golem's cube
    frames = [render_shell(glint(sp, f)) for f in range(FRAMES)]
    glass = [render_shell(glint(shell(framed=False), f)) for f in range(FRAMES)]   # the block: frame is geometry
    flat, ftex = core_flat(), frame_tex()
    models, blockstate = connected_models()
    strip = Image.new("RGBA", (16, 16 * FRAMES))
    for i, fr in enumerate(glass):
        strip.paste(fr, (0, 16 * i))
    inner = render_core(core())
    mcmeta = {"animation": {"frametime": 2, "interpolate": False, "frames": [{"index": 0, "time": 60}] + list(range(1, FRAMES))}}
    # preview: shell frames on a checker, the core, the composed face (core in the middle, shell over it), the golem
    S = 128
    sheet = Image.new("RGBA", (5 * (S + 4) + 4, 2 * (S + 4) + 4), (14, 14, 20, 255))
    checker = Image.new("RGBA", (S, S), (78, 128, 62, 255))
    for yy in range(0, S, 16):
        for xx in range(0, S, 16):
            if (xx // 16 + yy // 16) % 2:
                checker.paste((64, 108, 52, 255), (xx, yy, xx + 16, yy + 16))
    for k, f in enumerate((0, 2, 4, 6, 8)):
        sheet.paste(checker, (4 + k * (S + 4), 4))
        sheet.alpha_composite(frames[f].resize((S, S), Image.NEAREST), (4 + k * (S + 4), 4))
    y2 = 8 + S
    sheet.paste(checker, (4, y2))
    sheet.alpha_composite(inner.resize((S, S), Image.NEAREST), (4, y2))
    face = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    face.alpha_composite(inner)
    face.alpha_composite(frames[0])
    sheet.paste(checker, (8 + S, y2))
    sheet.alpha_composite(face.resize((S, S), Image.NEAREST), (8 + S, y2))
    old = Image.open(OLD if OLD.exists() else OUTER).convert("RGBA").crop((0, 0, 16, 16))
    sheet.alpha_composite(old.resize((S, S), Image.NEAREST), (12 + 2 * S, y2))
    g = Image.open(GOLEM).convert("RGBA")
    g.paste(frames[0], SHELL_UV)
    g.paste(render_core(core(), 12), CORE_UV)
    sheet.alpha_composite(g.crop((0, 40, 128, 80)).resize((2 * S - 4, S * 40 // 64), Image.NEAREST), (16 + 3 * S, y2))
    sheet.convert("RGB").save(P / "build/previews/soul_crystal_paint.png")
    front_view(flat, glass[0]).save(P / "build/previews/soul_crystal_connected.png")
    tmp = P / "build/previews/soul_crystal_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    inner.save(tmp / "inner.png")
    face.save(tmp / "face.png")
    print("preview: build/previews/soul_crystal_paint.png")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_soul_crystal")
    for f in (OLD, OLD.with_name(OLD.name + ".mcmeta"), MODEL, GOLEM, GEO):
        if f.exists():
            (bk / f.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, bk / f.relative_to(P))
    DIR.mkdir(parents=True, exist_ok=True)
    art_guard.save(strip, OUTER)
    OUTER.with_name(OUTER.name + ".mcmeta").write_text(json.dumps(mcmeta, indent=2) + "\n", encoding="utf-8")
    art_guard.save(flat, INNER)
    art_guard.save(ftex, DIR / "soul_crystal_block_frame.png")
    for f in (OLD, OLD.with_name(OLD.name + ".mcmeta")):         # the single-layer texture is replaced by the two above
        if f.exists():
            f.unlink()
    for name, m in models.items():
        (MODEL.parent / f"{name}.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    (A / "blockstates/soul_crystal_block.json").write_text(json.dumps(blockstate, indent=2) + "\n", encoding="utf-8")
    g.save(GOLEM)
    GEO.write_text(json.dumps(golem_geo(json.loads(GEO.read_text(encoding="utf-8"))), indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()

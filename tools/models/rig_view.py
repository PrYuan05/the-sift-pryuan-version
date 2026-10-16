"""Orthographic preview of a GeckoLib geo model (front + side), shared by the rigging tools.
Usage (inspect): python -I tools/models/rig_view.py <project> <mob> [out.png]

Faces are filled with the average colour of their texture region and outlined in their bone's colour; every cube is
labelled with its index (order in the file, bones in file order), and the ground line (y = 0) is drawn.
Rotation convention used for the preview (matches the derivation used for the animations): +x leans the top towards -z
(forward), +z leans the top towards +x. Cube and bone rotations are both applied."""
import sys, json, math
from pathlib import Path
from PIL import Image, ImageDraw

PALETTE = [(255, 99, 71), (65, 160, 255), (80, 220, 100), (255, 200, 40), (200, 90, 255), (0, 220, 220), (255, 140, 200),
           (170, 255, 90), (255, 150, 60), (140, 140, 255), (255, 255, 255), (120, 200, 160)]


def rot_point(p, pivot, rot):
    x, y, z = (p[i] - pivot[i] for i in range(3))
    rx, ry, rz = (math.radians(a) for a in rot)
    # z: top towards +x
    x, y = x * math.cos(rz) + y * math.sin(rz), -x * math.sin(rz) + y * math.cos(rz)
    # y
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    # x: top towards -z
    y, z = y * math.cos(rx) + z * math.sin(rx), -y * math.sin(rx) + z * math.cos(rx)
    return (x + pivot[0], y + pivot[1], z + pivot[2])


def bone_chain(bones_by_name, name):
    chain = []
    while name:
        b = bones_by_name[name]
        chain.append(b)
        name = b.get("parent")
    return chain   # innermost first


def cube_corners(cube, chain):
    (x, y, z), (w, h, d) = cube["origin"], cube["size"]
    inf = cube.get("inflate", 0)
    pts = [(x - inf + dx * (w + 2 * inf), y - inf + dy * (h + 2 * inf), z - inf + dz * (d + 2 * inf))
           for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
    if cube.get("rotation"):
        pts = [rot_point(p, cube.get("pivot", [0, 0, 0]), cube["rotation"]) for p in pts]
    for b in chain:   # bone rotations, innermost first
        if b.get("rotation") and any(b["rotation"]):
            pts = [rot_point(p, b.get("pivot", [0, 0, 0]), b["rotation"]) for p in pts]
    return pts


# corner index = dx*4 + dy*2 + dz
FACES = {"north": (0, 2, 6, 4), "south": (1, 5, 7, 3), "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
         "up": (2, 3, 7, 6), "down": (0, 4, 5, 1)}


def face_colour(tex, cube, face):
    uv = cube.get("uv")
    if isinstance(uv, dict) and face in uv:
        (u, v), (uw, uh) = uv[face]["uv"], uv[face].get("uv_size", [1, 1])
    elif isinstance(uv, list):
        u, v = uv
        uw = uh = 4
    else:
        return None
    x0, x1 = sorted((u, u + uw))
    y0, y1 = sorted((v, v + uh))
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(tex.width, max(x0 + 1, int(math.ceil(x1)))), min(tex.height, max(y0 + 1, int(math.ceil(y1))))
    px = [p for p in tex.crop((x0, y0, x1, y1)).get_flattened_data() if p[3] > 0]
    if not px:
        return None
    return tuple(sum(c[i] for c in px) // len(px) for i in range(3))


def render(geo, tex, title="", scale=10, highlight=None):
    """geo: the minecraft:geometry[0] dict. Returns a PIL image with front and side views."""
    bones = geo["bones"]
    by_name = {b["name"]: b for b in bones}
    colours = {b["name"]: PALETTE[i % len(PALETTE)] for i, b in enumerate(bones)}
    items, idx = [], 0
    for b in bones:
        chain = bone_chain(by_name, b["name"])
        for c in b.get("cubes", []):
            items.append((idx, b["name"], c, cube_corners(c, chain)))
            idx += 1
    allp = [p for it in items for p in it[3]]
    xs, ys, zs = [p[0] for p in allp], [p[1] for p in allp], [p[2] for p in allp]
    lo_y, hi_y = min(min(ys), 0), max(ys)
    span = max(max(xs) - min(xs), max(zs) - min(zs), hi_y - lo_y) + 8
    S = int(span * scale)
    img = Image.new("RGB", (S * 2 + 30, S + 40), (36, 38, 46))
    d = ImageDraw.Draw(img)
    d.text((6, 4), title, fill=(230, 230, 230))
    cx_f, cz_s = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2

    def to_screen(view, p):
        if view == "front":   # camera at -z looking +z
            sx = (p[0] - cx_f) * scale + S / 2
        else:                 # camera at +x looking -x, front (-z) on the left
            sx = (p[2] - cz_s) * scale + S / 2
        sy = (hi_y + 4 - p[1]) * scale + 20
        return sx, sy

    for vi, view in enumerate(("front", "side")):
        ox = vi * (S + 30)
        gy = (hi_y + 4) * scale + 20
        d.line([(ox, gy), (ox + S, gy)], fill=(120, 200, 120), width=1)
        d.text((ox + 4, 22), view, fill=(160, 160, 160))
        polys = []
        for i, bname, c, pts in items:
            for face, ids in FACES.items():
                quad = [pts[k] for k in ids]
                depth = sum(q[2] for q in quad) / 4 if view == "front" else -sum(q[0] for q in quad) / 4
                col = face_colour(tex, c, face)
                if col is None:
                    continue
                polys.append((depth, [to_screen(view, q) for q in quad], col, colours[bname], i))
        for depth, scr, col, edge, i in sorted(polys, key=lambda t: -t[0]):
            pts2 = [(x + ox, y) for x, y in scr]
            if len({(round(x), round(y)) for x, y in pts2}) < 3:
                d.line(pts2 + [pts2[0]], fill=edge, width=2)
                continue
            d.polygon(pts2, fill=col, outline=edge)
        for i, bname, c, pts in items:
            sc = [to_screen(view, p) for p in pts]
            mx, my = sum(s[0] for s in sc) / 8 + ox, sum(s[1] for s in sc) / 8
            d.text((mx - 4, my - 5), str(i), fill=(255, 255, 255) if highlight is None or i in highlight else (90, 90, 90),
                   stroke_width=2, stroke_fill=(0, 0, 0))
    # legend
    y = S + 22
    x = 6
    for b in bones:
        if b.get("cubes"):
            d.text((x, y), b["name"], fill=colours[b["name"]])
            x += 8 * len(b["name"]) + 14
    return img


def load(project, mob):
    p = Path(project) / "src/main/resources/assets/pysift"
    geo = json.loads((p / f"geckolib/models/entity/{mob}.geo.json").read_text(encoding="utf-8"))
    tex = Image.open(p / f"textures/entity/{mob}.png").convert("RGBA")
    return geo, tex


if __name__ == "__main__":
    project, mob = sys.argv[1], sys.argv[2]
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(project) / f"build/models/rig_preview/{mob}_inspect.png"
    geo, tex = load(project, mob)
    out.parent.mkdir(parents=True, exist_ok=True)
    render(geo["minecraft:geometry"][0], tex, f"{mob} (current)").save(out)
    print(out)

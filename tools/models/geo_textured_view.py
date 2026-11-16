"""Textured orthographic preview of a GeckoLib geo (per-face UV) - north (front), east (side) and south (back) views.
Usage: python -I tools/models/geo_textured_view.py <geo.json> <texture.png> <out.png> [scale]

Only the face looking at the camera is drawn for each cube, its UV region (negative uv_size = mirrored) stretched over
the projected rectangle; cubes are painted far-to-near. Rotated cubes (cube or bone rotation) are drawn from their
rotated bounding box, so they are approximate. The ground line (y = 0) is drawn in red."""
import sys, json, math
from PIL import Image, ImageDraw


def rot_point(p, pivot, rot):
    x, y, z = (p[i] - pivot[i] for i in range(3))
    rx, ry, rz = (math.radians(a) for a in rot)
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x + pivot[0], y + pivot[1], z + pivot[2])


def chain(bones, name):
    out = []
    while name:
        b = bones[name]
        out.append(b)
        name = b.get("parent")
    return out


def box(cube, bchain):
    o, s = cube["origin"], cube["size"]
    pts = [(o[0] + dx * s[0], o[1] + dy * s[1], o[2] + dz * s[2]) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
    rotated = bool(cube.get("rotation")) and any(cube["rotation"])
    if rotated:
        pts = [rot_point(p, cube.get("pivot", [0, 0, 0]), cube["rotation"]) for p in pts]
    for b in bchain:
        if b.get("rotation") and any(b["rotation"]):
            rotated = True
            pts = [rot_point(p, b.get("pivot", [0, 0, 0]), b["rotation"]) for p in pts]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi, rotated


def face_img(tex, face):
    (u, v), (w, h) = face["uv"], face["uv_size"]
    x0, x1 = sorted((u, u + w))
    y0, y1 = sorted((v, v + h))
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    im = tex.crop((int(x0), int(y0), int(round(x1)), int(round(y1))))
    if w < 0:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if h < 0:
        im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return im


VIEWS = {  # face, horizontal axis (+ = right on screen), depth axis (+ = farther away)
    "north (front)": ("north", lambda p: -p[0], lambda p: p[2]),
    "east (side)": ("east", lambda p: -p[2], lambda p: -p[0]),
    "south (back)": ("south", lambda p: p[0], lambda p: -p[2]),
}


def render(geo, tex, scale):
    g = geo["minecraft:geometry"][0]
    bones = {b["name"]: b for b in g["bones"]}
    items = []
    for b in g["bones"]:
        for c in b.get("cubes", []):
            lo, hi, rot = box(c, chain(bones, b["name"]))
            items.append((b["name"], c, lo, hi, rot))
    xs = [v for _, _, lo, hi, _ in items for v in (lo[0], hi[0], lo[2], hi[2])]
    ys = [v for _, _, lo, hi, _ in items for v in (lo[1], hi[1])]
    half = max(abs(min(xs)), abs(max(xs))) + 4
    top, bottom = max(ys) + 4, min(min(ys), 0) - 4
    W, H = int(2 * half * scale), int((top - bottom) * scale)
    panels = []
    for title, (face, hx, depth) in VIEWS.items():
        img = Image.new("RGBA", (W, H + 20), (40, 40, 46, 255))
        d = ImageDraw.Draw(img)
        d.text((4, 4), title, fill=(230, 230, 230))
        corners = lambda lo, hi: [(a, b_, c) for a in (lo[0], hi[0]) for b_ in (lo[1], hi[1]) for c in (lo[2], hi[2])]
        for name, c, lo, hi, rot in sorted(items, key=lambda it: -max(depth(p) for p in corners(it[2], it[3]))):
            pts = corners(lo, hi)
            l, r = min(hx(p) for p in pts), max(hx(p) for p in pts)
            x0, x1 = int((l + half) * scale), int((r + half) * scale)
            y0, y1 = int((top - hi[1]) * scale) + 20, int((top - lo[1]) * scale) + 20
            f = c.get("uv", {}).get(face) if isinstance(c.get("uv"), dict) else None
            fi = face_img(tex, f) if f else None
            if fi is not None and x1 > x0 and y1 > y0:
                img.alpha_composite(fi.convert("RGBA").resize((x1 - x0, y1 - y0), Image.Resampling.NEAREST), (x0, y0))
            else:
                d.rectangle([x0, y0, x1, y1], fill=(255, 0, 255, 255))
            if rot:
                d.rectangle([x0, y0, x1, y1], outline=(255, 210, 0, 255))
        gy = int(top * scale) + 20
        d.line([(0, gy), (W, gy)], fill=(255, 60, 60, 255), width=2)
        panels.append(img)
    out = Image.new("RGBA", (W * 3 + 20, H + 20), (25, 25, 30, 255))
    for i, p in enumerate(panels):
        out.alpha_composite(p, (i * (W + 10), 0))
    return out


if __name__ == "__main__":
    geo = json.load(open(sys.argv[1], encoding="utf-8"))
    tex = Image.open(sys.argv[2]).convert("RGBA")
    render(geo, tex, float(sys.argv[4]) if len(sys.argv) > 4 else 4).save(sys.argv[3])

"""GeckoLib 模型的貼圖 3D 預覽（斜上方三個角度：前、側、後），會正確處理方塊旋轉與骨骼的動畫姿勢。
Usage: python -I tools/models/geo_preview3d.py <geo.json> <texture.png> <out.png> [scale]
程式內用法：render_views(geo_doc, tex, scale, pose={bone: {"rotation": [x,y,z], "position": [x,y,z]}}, title="")
旋轉慣例同 rig_view.rot_point（+x 頂端往前、+z 頂端往 +x），也就是動畫用的慣例。
"""
import sys, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_view import rot_point  # noqa: E402

FACES = {   # 從外面看的 左上、右上、右下、左下（0 = min、1 = max）
    "north": ((1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)),
    "south": ((0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)),
    "east": ((1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)),
    "west": ((0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)),
    "up": ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
    "down": ((0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)),
}
SHADE = {"up": 1.0, "north": 0.92, "south": 0.92, "east": 0.8, "west": 0.8, "down": 0.6}


def world_quads(geo, pose=None):
    """回傳 [(4 個世界座標點, face, uv dict)]，已套用方塊旋轉、骨骼姿勢（子骨骼跟著父骨骼）。"""
    pose = pose or {}
    bones = {b["name"]: b for b in geo["bones"]}

    def chain(name):
        out = []
        while name:
            out.append(bones[name])
            name = bones[name].get("parent")
        return out   # 自己 → 根

    quads = []
    for b in geo["bones"]:
        ch = chain(b["name"])
        for c in b.get("cubes", []):
            o, s = c["origin"], c["size"]
            inf = c.get("inflate", 0)
            lo = [o[i] - inf for i in range(3)]
            hi = [o[i] + s[i] + inf for i in range(3)]
            for face, corners in FACES.items():
                f = (c.get("uv") or {}).get(face)
                if not f:
                    continue
                pts = []
                for k in corners:
                    p = tuple(hi[i] if k[i] else lo[i] for i in range(3))
                    if c.get("rotation"):
                        p = rot_point(p, c.get("pivot", [0, 0, 0]), c["rotation"])
                    for bb in ch:   # 由內往外套骨骼姿勢
                        ps = pose.get(bb["name"], {})
                        if ps.get("rotation"):
                            p = rot_point(p, bb["pivot"], ps["rotation"])
                        if ps.get("position"):
                            p = tuple(p[i] + ps["position"][i] for i in range(3))
                    pts.append(p)
                quads.append((pts, face, f))
    return quads


def render(geo, tex, scale=6, yaw=30, pitch=20, pose=None, size=None):
    quads = world_quads(geo, pose)
    allp = [p for q in quads for p in q[0]]
    ys = [p[1] for p in allp]
    lo_y, hi_y = min(min(ys), 0), max(ys)
    W = size or int((max(abs(p[0]) for p in allp) + max(abs(p[2]) for p in allp) + 10) * scale * 1.3)
    H = int((hi_y - lo_y + 14) * scale)
    img = Image.new("RGB", (W, H), (40, 42, 52))
    px = img.load()
    zb = [[-1e9] * H for _ in range(W)]
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def proj(p):
        x, y, z = p
        # 相機在 -z（模型正面）方向，繞 y 轉 yaw，再往下看 pitch
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp + z * sp, -y * sp + z * cp
        return (W / 2 - x * scale, H - 6 * scale - (y - lo_y) * scale, -z)

    # 地面
    for gx in range(-12, 13, 2):
        a, b = proj((gx, 0, -12)), proj((gx, 0, 12))
        ImageDraw.Draw(img).line([a[:2], b[:2]], fill=(70, 72, 84))
    tw, th = tex.size
    tp = tex.load()
    for pts, face, f in quads:
        P = [proj(p) for p in pts]
        u0, v0 = f["uv"]
        u1, v1 = u0 + f["uv_size"][0], v0 + f["uv_size"][1]
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            A_, B_, C_ = P[a], P[b], P[c]
            d = (B_[1] - C_[1]) * (A_[0] - C_[0]) + (C_[0] - B_[0]) * (A_[1] - C_[1])
            if abs(d) < 1e-9:
                continue
            x0, x1 = max(0, int(min(A_[0], B_[0], C_[0]))), min(W - 1, int(max(A_[0], B_[0], C_[0])) + 1)
            y0, y1 = max(0, int(min(A_[1], B_[1], C_[1]))), min(H - 1, int(max(A_[1], B_[1], C_[1])) + 1)
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    l1 = ((B_[1] - C_[1]) * (xx + .5 - C_[0]) + (C_[0] - B_[0]) * (yy + .5 - C_[1])) / d
                    l2 = ((C_[1] - A_[1]) * (xx + .5 - C_[0]) + (A_[0] - C_[0]) * (yy + .5 - C_[1])) / d
                    l3 = 1 - l1 - l2
                    if l1 < -1e-6 or l2 < -1e-6 or l3 < -1e-6:
                        continue
                    z = l1 * A_[2] + l2 * B_[2] + l3 * C_[2]
                    if z <= zb[xx][yy]:
                        continue
                    u = l1 * uv[a][0] + l2 * uv[b][0] + l3 * uv[c][0]
                    v = l1 * uv[a][1] + l2 * uv[b][1] + l3 * uv[c][1]
                    col = tp[min(tw - 1, max(0, int(u))), min(th - 1, max(0, int(v)))]
                    if col[3] < 128:
                        continue
                    zb[xx][yy] = z
                    k = SHADE[face]
                    px[xx, yy] = (int(col[0] * k), int(col[1] * k), int(col[2] * k))
    return img


def render_views(geo_doc, tex, scale=6, pose=None, title=""):
    geo = geo_doc["minecraft:geometry"][0] if "minecraft:geometry" in geo_doc else geo_doc
    views = [render(geo, tex, scale, yaw, 18, pose) for yaw in (25, 100, 205)]
    W = sum(v.width for v in views) + 20
    H = max(v.height for v in views) + 24
    out = Image.new("RGB", (W, H), (30, 30, 36))
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
    except OSError:
        font = None
    d.text((6, 4), title, fill=(230, 230, 230), font=font)
    x = 0
    for v, label in zip(views, ("前", "側", "後")):
        out.paste(v, (x, 22))
        d.text((x + 6, 24), label, fill=(160, 160, 160), font=font)
        x += v.width + 10
    return out


if __name__ == "__main__":
    doc = json.load(open(sys.argv[1], encoding="utf-8"))
    tex = Image.open(sys.argv[2]).convert("RGBA")
    render_views(doc, tex, float(sys.argv[4]) if len(sys.argv) > 4 else 6, title=Path(sys.argv[1]).name).save(sys.argv[3])

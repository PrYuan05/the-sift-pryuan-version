"""Drive the headless worldgen test server (gradle task runSiftTestServer, dir run-server/) over RCON and scan its save.
Usage (from the project root):
  python -I tools/worldgen/devserver.py cmd "<command>"     run a command inside pysift:the_sift and print the reply
  python -I tools/worldgen/devserver.py raw "<command>"     run a command as-is
  python -I tools/worldgen/devserver.py gen [radius] [wait] [cx] [cz]   forceload +-radius blocks around cx,cz, wait, save
  python -I tools/worldgen/devserver.py scan                count blocks / biomes per chunk and the surface-liquid share
  python -I tools/worldgen/devserver.py tree x z [feature]   clear a plot, place a tree, render it
  python -I tools/worldgen/devserver.py spire x z [feature] [floor] [out]   clear a plot, place one spire, render side + top
  python -I tools/worldgen/devserver.py render x y z [half] silhouettes (front + side) of the area around x,y,z -> PNG
  python -I tools/worldgen/devserver.py stop                save and stop the server
Only talks to 127.0.0.1; the RCON password is read from run-server/server.properties."""
import gzip, json, math, socket, struct, sys, time, zlib, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRV = ROOT / "run-server"
DIM = "pysift:the_sift"


# ---------------- RCON ----------------
def props():
    return dict(l.split("=", 1) for l in (SRV / "server.properties").read_text(encoding="utf-8").splitlines()
                if "=" in l and not l.startswith("#"))


def rcon(*commands, timeout=60):
    p = props()
    s = socket.create_connection(("127.0.0.1", int(p.get("rcon.port", 25575))), timeout=timeout)

    def send(req_id, kind, body):
        data = struct.pack("<ii", req_id, kind) + body.encode("utf-8") + b"\x00\x00"
        s.sendall(struct.pack("<i", len(data)) + data)

    def recv():
        size = struct.unpack("<i", _read(s, 4))[0]
        data = _read(s, size)
        req_id, kind = struct.unpack("<ii", data[:8])
        return req_id, data[8:-2].decode("utf-8", "replace")

    send(1, 3, p["rcon.password"])
    if recv()[0] == -1:
        raise SystemExit("RCON login failed")
    out = []
    for i, c in enumerate(commands, 2):
        send(i, 2, c)
        out.append(recv()[1])
    s.close()
    return out


def _read(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("RCON closed")
        buf += chunk
    return buf


# ---------------- minimal NBT ----------------
def nbt(data):
    pos = 0

    def u(fmt):
        nonlocal pos
        v = struct.unpack_from(">" + fmt, data, pos)
        pos += struct.calcsize(">" + fmt)
        return v[0]

    def string():
        nonlocal pos
        n = u("H")
        v = data[pos:pos + n].decode("utf-8", "replace")
        pos += n
        return v

    def payload(t):
        nonlocal pos
        if t == 1: return u("b")
        if t == 2: return u("h")
        if t == 3: return u("i")
        if t == 4: return u("q")
        if t == 5: return u("f")
        if t == 6: return u("d")
        if t == 7:
            n = u("i"); v = data[pos:pos + n]; pos += n; return v
        if t == 8: return string()
        if t == 9:
            et = u("b"); n = u("i"); return [payload(et) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = u("b")
                if tt == 0: return d
                name = string()          # read the name first: in `d[k] = v` Python evaluates v before k
                d[name] = payload(tt)
        if t == 11:
            n = u("i"); v = struct.unpack_from(f">{n}i", data, pos); pos += 4 * n; return list(v)
        if t == 12:
            n = u("i"); v = struct.unpack_from(f">{n}q", data, pos); pos += 8 * n; return list(v)
        raise ValueError(f"tag {t}")

    t = u("b")
    string()
    return payload(t)


def chunks(region_dir):
    for f in sorted(Path(region_dir).glob("*.mca")):
        data = f.read_bytes()
        for i in range(1024):
            off = int.from_bytes(data[i * 4:i * 4 + 3], "big")
            if not off:
                continue
            p = off * 4096
            length = struct.unpack(">I", data[p:p + 4])[0]
            comp, raw = data[p + 4], data[p + 5:p + 4 + length]
            body = zlib.decompress(raw) if comp == 2 else gzip.decompress(raw) if comp == 1 else raw
            yield nbt(body)


def unpack_heightmap(longs, bits=9, count=256):
    per = 64 // bits
    mask = (1 << bits) - 1
    out = []
    for i in range(count):
        v = longs[i // per] & ((1 << 64) - 1)
        out.append((v >> ((i % per) * bits)) & mask)
    return out


def scan():
    level = props().get("level-name", "sift_test")
    region = SRV / level / "dimensions/pysift/the_sift/region"
    blocks, biomes = collections.Counter(), collections.Counter()
    biome_with = collections.defaultdict(collections.Counter)
    liquid_cols = total_cols = full = 0
    floor_heights = []
    log_blocks = 0
    for c in chunks(region):
        if c.get("Status") != "minecraft:full":
            continue
        full += 1
        names, chunk_biomes = set(), set()
        for sec in c.get("sections", []):
            bs = sec.get("block_states", {})
            # 26.3 palettes hold plain ids or {"id"/"Name": ..., "properties": ...}
            pal = [e if isinstance(e, str) else e.get("Name") or e.get("id") or e.get("") for e in bs.get("palette", [])]
            names.update(pal)
            if "pysift:soul_willow_log" in pal:
                data = bs.get("data")
                idx = pal.index("pysift:soul_willow_log")
                if not data:
                    log_blocks += 4096
                else:
                    bits = max(4, math.ceil(math.log2(len(pal))))
                    per = 64 // bits
                    for n in range(4096):
                        v = (data[n // per] & ((1 << 64) - 1)) >> ((n % per) * bits) & ((1 << bits) - 1)
                        log_blocks += v == idx
            chunk_biomes.update(sec.get("biomes", {}).get("palette", []))
        for n in names:
            blocks[n] += 1
        for b in chunk_biomes:
            biomes[b] += 1
            for n in ("pysift:soul_willow_log", "pysift:soul_willow_leaves", "pysift:meadow_grass_block"):
                if n in names:
                    biome_with[b][n] += 1
        hm = c.get("Heightmaps", {})
        if "MOTION_BLOCKING_NO_LEAVES" in hm and "OCEAN_FLOOR" in hm:
            # fluids count for MOTION_BLOCKING_NO_LEAVES but not OCEAN_FLOOR; plants and leaves count for neither
            mb, of = unpack_heightmap(hm["MOTION_BLOCKING_NO_LEAVES"]), unpack_heightmap(hm["OCEAN_FLOOR"])
            total_cols += 256
            liquid_cols += sum(1 for a, b in zip(mb, of) if a - b >= 1)
            floor_heights.extend(of)
    report = {"full_chunks": full,
              "surface_liquid_share": round(liquid_cols / total_cols, 3) if total_cols else None,
              "willow_log_blocks": log_blocks,
              # heightmap values are stored relative to the dimension bottom (min_y = -64)
              "ground_y": ({"min": min(floor_heights) - 64, "avg": round(sum(floor_heights) / len(floor_heights) - 64, 1),
                            "max": max(floor_heights) - 64} if floor_heights else None),
              "biomes": dict(biomes.most_common()),
              "per_biome": {b: dict(v) for b, v in biome_with.items()},
              "pysift_blocks": {k: v for k, v in blocks.most_common() if k.startswith("pysift:")}}
    print(json.dumps(report, ensure_ascii=False, indent=1))


def state_name(e, with_props):
    if isinstance(e, str):
        return e
    name = e.get("Name") or e.get("id") or e.get("")
    pr = e.get("Properties") or e.get("properties") or {}
    return name + ("[" + ",".join(f"{k}={v}" for k, v in sorted(pr.items())) + "]" if with_props and pr else "")


def blocks_in_box(x0, y0, z0, x1, y1, z1, with_props=False):
    """{(x, y, z): block id} for every non-air block in the box, read from the saved region files
    (with_props=True: "id[k=v,...]")."""
    level = props().get("level-name", "sift_test")
    region = SRV / level / "dimensions/pysift/the_sift/region"
    want = {(cx, cz) for cx in range(x0 >> 4, (x1 >> 4) + 1) for cz in range(z0 >> 4, (z1 >> 4) + 1)}
    out = {}
    for c in chunks(region):
        key = (c.get("xPos"), c.get("zPos"))
        if key not in want:
            continue
        for sec in c.get("sections", []):
            bs = sec.get("block_states", {})
            pal = [state_name(e, with_props) for e in bs.get("palette", [])]
            if not pal or pal == ["minecraft:air"]:
                continue
            data, sy = bs.get("data"), sec["Y"] * 16
            bits = max(4, math.ceil(math.log2(len(pal)))) if len(pal) > 1 else 0
            per = 64 // bits if bits else 0
            for i in range(4096):
                idx = 0 if not bits else ((data[i // per] & ((1 << 64) - 1)) >> ((i % per) * bits)) & ((1 << bits) - 1)
                name = pal[idx]
                if name == "minecraft:air":
                    continue
                x, y, z = key[0] * 16 + (i & 15), sy + (i >> 8), key[1] * 16 + ((i >> 4) & 15)
                if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                    out[(x, y, z)] = name
    return out


RENDER_COLORS = {"pysift:soul_willow_log": (92, 97, 103), "pysift:soul_willow_leaves": (168, 232, 228),
                 "pysift:soul_willow_leaves_pale": (156, 203, 238), "pysift:glowing_soul_willow_leaves": (198, 255, 242),
                 "pysift:soul_willow_vine": (95, 216, 196), "pysift:glowing_soul_willow_vine": (230, 220, 250),
                 "pysift:abyssal_strata": (40, 70, 80)}


def render(cx, cy, cz, half=12, out="build/texture_pipeline/out/willow_render.png"):
    """Two views of the area around cx,cy,cz: a front cross-section through z = cz (left) and a 'curtain density'
    view (right) where each pixel's opacity is how many blocks lie along the line of sight (gaps stay visible)."""
    from PIL import Image
    cx, cy, cz, h = int(cx), int(cy), int(cz), int(half)
    top = cy + 44
    box = blocks_in_box(cx - h, cy - 4, cz - h, cx + h, top, cz + h)
    w, ht, s = 2 * h + 1, top - (cy - 4) + 1, 12
    img = Image.new("RGB", ((2 * w + 3) * s, ht * s), (24, 26, 34))

    def paint(col_x, row, col):
        for px in range(s):
            for py in range(s):
                img.putpixel((col_x * s + px, row * s + py), col)

    for a in range(-h, h + 1):
        for row in range(ht):
            y = top - row
            name = box.get((cx + a, y, cz))                       # cross-section through the trunk
            if name:
                paint(a + h, row, RENDER_COLORS.get(name, (110, 100, 110)))
            hits = [box[(cx + a, y, cz + d)] for d in range(-h, h + 1) if (cx + a, y, cz + d) in box]
            if hits:                                              # density view: more blocks behind = more opaque
                main = max(set(hits), key=hits.count)
                k = min(1.0, len(hits) / 6)
                base = RENDER_COLORS.get(main, (110, 100, 110))
                paint(w + 3 + a + h, row, tuple(int(24 + (c - 24) * k) for c in base))
    Path(ROOT / out).parent.mkdir(parents=True, exist_ok=True)
    img.save(ROOT / out)
    counts = collections.Counter(box.values())
    print(json.dumps({"saved": out, "blocks": {k: v for k, v in counts.items() if "willow" in k}}))


def tree(x, z, feature="pysift:soul_willow", out="build/texture_pipeline/out/willow_render.png"):
    """Clear a 45x45 plot at x,z (48 high), floor it, place `feature`, save and render its silhouettes."""
    x, z, h = int(x), int(z), 22
    rcon(f"execute in {DIM} run forceload add {x - 40} {z - 40} {x + 40} {z + 40}")
    time.sleep(8)
    rcon("kill @e[type=minecraft:marker]")
    rcon(f"execute in {DIM} positioned {x} 0 {z} positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~")
    y = int(float(rcon(f"execute in {DIM} as @e[type=minecraft:marker,limit=1] run data get entity @s Pos[1]")[0]
                  .rsplit(":", 1)[1].strip().rstrip("d")))
    for dy in range(0, 48, 12):   # /fill is limited to 32768 blocks per call
        rcon(f"execute in {DIM} run fill {x - h} {y + dy} {z - h} {x + h} {y + dy + 11} {z + h} minecraft:air")
    print(rcon(f"execute in {DIM} run fill {x - h} {y - 1} {z - h} {x + h} {y - 1} {z + h} pysift:abyssal_strata[depth=0]",
               f"execute in {DIM} run place feature {feature} {x} {y} {z}", "save-all flush"))
    time.sleep(3)
    render(x, y, z, h, out)


_COLOR_CACHE = {}


def texture_color(block_state, face):
    """Average colour of a block state's face texture ('side' or 'top'), read from the mod / vanilla assets."""
    key = (block_state, face)
    if key in _COLOR_CACHE:
        return _COLOR_CACHE[key]
    from PIL import Image
    name, _, rest = block_state.partition("[")
    ns, bid = name.split(":")
    want = dict(kv.split("=") for kv in rest.rstrip("]").split(",") if kv)
    col = (110, 100, 110)
    bs_file = ROOT / f"src/main/resources/assets/{ns}/blockstates/{bid}.json"
    if ns == "minecraft":
        col = {"minecraft:oak_leaves": (60, 110, 50)}.get(name, (90, 90, 90))
    elif bs_file.exists():
        bs = json.loads(bs_file.read_text(encoding="utf-8"))
        variants = bs.get("variants") or {"": part["apply"] for part in bs.get("multipart", [])[:1]}   # walls etc.
        for k, v in variants.items():
            kv = dict(x.split("=") for x in k.split(",") if x)
            if all(want.get(a, b) == b for a, b in kv.items()):   # default states are saved without properties
                ref = (v[0] if isinstance(v, list) else v)["model"]
                if not ref.startswith("pysift:"):
                    break                   # vanilla assets are not in the project: keep the neutral colour
                mns, mpath = ref.split(":")
                tex = json.loads((ROOT / f"src/main/resources/assets/{mns}/models/{mpath}.json").read_text(encoding="utf-8"))["textures"]
                t = tex.get(face) or tex.get("all") or tex.get("side") or next(iter(tex.values()))
                tns, tpath = t.split(":")
                png = ROOT / f"src/main/resources/assets/{tns}/textures/{tpath}.png"
                if png.exists():
                    col = Image.open(png).convert("RGB").resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
                break
    _COLOR_CACHE[key] = col
    return col


def spire(x, z, feature="pysift:spire_crimson_strata_canyon", floor="pysift:amber_sand", out="build/texture_pipeline/out/spire_render.png"):
    """Clear a 49x49 plot at x,z, floor it, place one spire, then render a shaded side view (left) and a top view
    (right) in texture colours."""
    from PIL import Image
    x, z, h = int(x), int(z), 18
    rcon(f"execute in {DIM} run forceload add {x - 32} {z - 32} {x + 32} {z + 32}")
    time.sleep(8)
    rcon("kill @e[type=minecraft:marker]")
    rcon(f"execute in {DIM} positioned {x} 0 {z} positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~")
    y = int(float(rcon(f"execute in {DIM} as @e[type=minecraft:marker,limit=1] run data get entity @s Pos[1]")[0]
                  .rsplit(":", 1)[1].strip().rstrip("d")))
    for dy in range(0, 64, 16):   # /fill is limited to 32768 blocks per call
        rcon(f"execute in {DIM} run fill {x - h} {y + dy} {z - h} {x + h} {y + dy + 15} {z + h} minecraft:air")
    print(rcon(f"execute in {DIM} run fill {x - h} {y - 1} {z - h} {x + h} {y - 1} {z + h} {floor}",
               f"execute in {DIM} run place feature {feature} {x} {y} {z}", "save-all flush"))
    time.sleep(3)
    box = blocks_in_box(x - h, y - 2, z - h, x + h, y + 62, z + h, with_props=True)
    box = {k: v for k, v in box.items() if k[1] >= y or not v.startswith(floor)}
    if not box:
        print("nothing placed")
        return
    top = max(k[1] for k in box)
    s, w, ht = 10, 2 * h + 1, top - (y - 2) + 1
    img = Image.new("RGB", ((2 * w + 3) * s, max(ht, w) * s), (24, 26, 34))

    def paint(col_x, row, col):
        for px in range(s):
            for py in range(s):
                img.putpixel((col_x * s + px, row * s + py), col)

    for a in range(-h, h + 1):
        for row in range(ht):                      # side view from -z: nearest block, darker with depth
            yy = top - row
            for d in range(-h, h + 1):
                b = box.get((x + a, yy, z + d))
                if b:
                    face = "top" if (x + a, yy + 1, z + d) not in box and (x + a, yy, z + d - 1) not in box else "side"
                    c = texture_color(b, face)
                    k = 1.0 - 0.45 * (d + h) / (2 * h)
                    paint(a + h, row, tuple(int(v * k) for v in c))
                    break
        for d in range(-h, h + 1):                 # top view: highest block, brighter when higher
            col = [(yy, box[(x + a, yy, z + d)]) for yy in range(top, y - 3, -1) if (x + a, yy, z + d) in box]
            if col:
                yy, b = col[0]
                k = 0.55 + 0.45 * (yy - y + 2) / max(1, top - y + 2)
                paint(w + 3 + a + h, d + h, tuple(min(255, int(v * k)) for v in texture_color(b, "top")))
    Path(ROOT / out).parent.mkdir(parents=True, exist_ok=True)
    img.save(ROOT / out)
    counts = collections.Counter(v.split("[")[0] for k, v in box.items() if k[1] >= y)
    print(json.dumps({"saved": out, "height": top - y + 1, "blocks": dict(counts.most_common())}))


def gen(radius=128, wait=90, cx=0, cz=0):
    r, cx, cz = int(radius), int(cx), int(cz)
    print(rcon(f"execute in {DIM} run forceload add {cx - r} {cz - r} {cx + r - 1} {cz + r - 1}")[0])
    time.sleep(int(wait))
    print(rcon(f"execute in {DIM} run forceload remove all", "save-all flush", timeout=300))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "cmd":
        print(rcon(f"execute in {DIM} run {sys.argv[2]}")[0])
    elif cmd == "raw":
        print(rcon(sys.argv[2])[0])
    elif cmd == "gen":
        gen(*sys.argv[2:6])
    elif cmd == "scan":
        scan()
    elif cmd == "tree":
        tree(*sys.argv[2:5])
    elif cmd == "spire":
        spire(*sys.argv[2:7])
    elif cmd == "render":
        render(*sys.argv[2:6])
    elif cmd == "stop":
        print(rcon("save-all flush", "stop", timeout=120))
    else:
        sys.exit(__doc__)
